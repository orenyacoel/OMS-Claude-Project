"""
Apex Capital OMS - Demo Order Management System

This is the main Flask app. Flask is a web framework - it listens for
HTTP requests (like when you visit a URL in your browser) and returns
HTML pages in response.

Each @app.route() function handles a different page of the OMS.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Account, Order, Execution, Position, ComplianceRule
from seed_data import seed_all
from datetime import datetime
import os

app = Flask(__name__)

# SQLite is a simple file-based database. Perfect for demos because
# there's nothing to install - the database is just a file.
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///oms.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.context_processor
def inject_now():
    """Make the current time available in all templates."""
    return {"now": datetime.utcnow()}


def init_db():
    """Create tables and load demo data if the database is empty."""
    db.create_all()
    if Account.query.first() is None:
        seed_all()


# ========== PAGE ROUTES ==========
# These are the URLs you visit in the browser.

@app.route("/")
def index():
    """Redirect to the blotter - that's the main page of any OMS."""
    return redirect(url_for("blotter"))


@app.route("/blotter")
def blotter():
    """
    The Trade Blotter - the heart of the OMS.
    
    Shows all orders for the day with their current status.
    In a real OMS, this updates in real-time via websockets.
    For our demo, it refreshes when you reload the page.
    """
    # Get filter parameters from the URL query string
    # e.g., /blotter?asset_class=Equity&status=Working
    asset_filter = request.args.get("asset_class", "All")
    status_filter = request.args.get("status", "All")
    account_filter = request.args.get("account", "All")

    query = Order.query

    if asset_filter != "All":
        query = query.filter(Order.asset_class == asset_filter)
    if status_filter != "All":
        query = query.filter(Order.status == status_filter)
    if account_filter != "All":
        query = query.filter(Order.account_id == int(account_filter))

    orders = query.order_by(Order.created_at.desc()).all()
    accounts = Account.query.all()

    # Calculate summary stats for the top bar
    all_orders = Order.query.all()
    stats = {
        "total": len(all_orders),
        "filled": sum(1 for o in all_orders if o.status == "Filled"),
        "working": sum(1 for o in all_orders if o.status in ("Working", "Partial")),
        "rejected": sum(1 for o in all_orders if o.status == "Rejected"),
    }

    return render_template(
        "blotter.html",
        orders=orders,
        accounts=accounts,
        stats=stats,
        asset_filter=asset_filter,
        status_filter=status_filter,
        account_filter=account_filter,
        active_page="blotter",
    )


@app.route("/positions")
def positions():
    """
    Positions view - shows what the fund currently holds.
    
    This is crucial for trading ops because you need to know current
    positions before you can figure out what trades to make, and to
    check that orders won't breach any limits.
    """
    account_filter = request.args.get("account", "All")
    asset_filter = request.args.get("asset_class", "All")

    query = Position.query
    if account_filter != "All":
        query = query.filter(Position.account_id == int(account_filter))
    if asset_filter != "All":
        query = query.filter(Position.asset_class == asset_filter)

    positions_list = query.all()
    accounts = Account.query.all()

    # Calculate totals
    total_mv = sum(p.market_value for p in positions_list)
    total_pnl = sum(p.unrealized_pnl for p in positions_list)

    return render_template(
        "positions.html",
        positions=positions_list,
        accounts=accounts,
        total_mv=total_mv,
        total_pnl=total_pnl,
        account_filter=account_filter,
        asset_filter=asset_filter,
        active_page="positions",
    )


@app.route("/executions")
def executions():
    """
    Executions view - shows all fills/trades that have happened.
    
    In trading ops, you'd use this to:
    - Verify that orders were executed correctly
    - Check execution quality (did we get a good price?)
    - Feed into the reconciliation process
    """
    execs = Execution.query.order_by(Execution.exec_time.desc()).all()
    return render_template(
        "executions.html",
        executions=execs,
        active_page="executions",
    )


@app.route("/compliance")
def compliance():
    """
    Compliance dashboard - shows rules and any violations.
    
    Pre-trade compliance is one of the biggest responsibilities in
    trading ops. Every order gets checked against a set of rules
    before it goes to the broker.
    """
    rules = ComplianceRule.query.all()
    # Get recent compliance failures
    failed_orders = Order.query.filter(Order.compliance_status == "Failed").all()
    
    return render_template(
        "compliance.html",
        rules=rules,
        failed_orders=failed_orders,
        active_page="compliance",
    )


# ========== API ROUTES ==========
# These handle form submissions and AJAX requests.
# They return JSON instead of HTML pages.

@app.route("/api/order", methods=["POST"])
def create_order():
    """
    Create a new order via the order entry form.
    
    This is what happens when someone fills out the order ticket
    and clicks Submit. The flow is:
    1. Receive the order details
    2. Run compliance checks
    3. If it passes, set status to "Working" (sent to broker)
    4. If it fails, set status to "Rejected"
    """
    data = request.form

    # Generate a new order ID
    last_order = Order.query.order_by(Order.id.desc()).first()
    if last_order:
        last_num = int(last_order.order_id.split("-")[1])
        new_id = f"ORD-{last_num + 1}"
    else:
        new_id = "ORD-40801"

    # Parse the limit price (might be empty for market orders)
    limit_price = None
    if data.get("limit_price"):
        try:
            limit_price = float(data["limit_price"])
        except ValueError:
            pass

    # Determine asset class from the symbol
    # In a real system this would come from a security master database
    asset_class = data.get("asset_class", "Equity")

    order = Order(
        order_id=new_id,
        asset_class=asset_class,
        symbol=data["symbol"].upper(),
        description=data.get("description", ""),
        side=data["side"],
        quantity=float(data["quantity"]),
        order_type=data["order_type"],
        limit_price=limit_price,
        broker=data.get("broker", ""),
        account_id=int(data["account_id"]),
        tif=data.get("tif", "DAY"),
        currency_pair=data.get("currency_pair", None),
        status="New",
        compliance_status="Pending",
    )

    # Run compliance checks
    compliance_result = run_compliance_checks(order)
    order.compliance_status = compliance_result["status"]
    order.compliance_note = compliance_result.get("note", "")

    if compliance_result["status"] == "Passed":
        order.status = "Working"
    else:
        order.status = "Rejected"

    db.session.add(order)
    db.session.commit()

    return redirect(url_for("blotter"))


def run_compliance_checks(order):
    """
    Check an order against all active compliance rules.
    
    This is a simplified version. A real system would check things like:
    - Position limits (would this order make us too big in one name?)
    - Sector/country concentration
    - Restricted securities list
    - Regulatory limits
    - Client mandate restrictions
    """
    rules = ComplianceRule.query.filter_by(is_active=True).all()

    for rule in rules:
        # Check restricted list
        if rule.rule_type == "restricted_list":
            if order.symbol == rule.parameter:
                return {
                    "status": "Failed",
                    "note": f"Symbol {order.symbol} is on the restricted list: {rule.description}"
                }

        # Check max order size
        if rule.rule_type == "position_limit" and rule.parameter == "order_value":
            # Rough notional value calculation
            price_estimate = order.limit_price or 100  # Default if no limit price
            notional = order.quantity * price_estimate
            if notional > rule.threshold:
                return {
                    "status": "Failed",
                    "note": f"Order notional ${notional:,.0f} exceeds max ${rule.threshold:,.0f}"
                }

        # Check concentration
        if rule.rule_type == "concentration" and rule.parameter == "symbol":
            account = Account.query.get(order.account_id)
            if account and account.nav > 0:
                existing = Position.query.filter_by(
                    account_id=order.account_id, symbol=order.symbol
                ).first()
                existing_value = existing.market_value if existing else 0
                price_estimate = order.limit_price or 100
                new_value = existing_value + (order.quantity * price_estimate)
                concentration = abs(new_value) / account.nav * 100
                if concentration > rule.threshold:
                    return {
                        "status": "Failed",
                        "note": f"Position would be {concentration:.1f}% of NAV (limit: {rule.threshold}%)"
                    }

    return {"status": "Passed", "note": "All compliance checks passed"}


@app.route("/api/order/<int:order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    """Cancel a working order."""
    order = Order.query.get_or_404(order_id)
    if order.status in ("Working", "Partial", "New"):
        order.status = "Cancelled"
        db.session.commit()
    return redirect(url_for("blotter"))


# ========== START THE APP ==========

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
