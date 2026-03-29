"""
Generates realistic demo data for the OMS.

This populates the database with fake but realistic-looking orders, positions,
and accounts so that when you open the app it looks like a real trading system.

Why seed data matters: When you show this to an employer, having realistic
data makes it look professional. Empty tables look like a school project.
"""

import random
from datetime import datetime, timedelta
from models import db, Account, Order, Execution, Position, ComplianceRule


def seed_all():
    """Main function that populates everything."""
    seed_accounts()
    seed_compliance_rules()
    seed_positions()
    seed_orders()
    db.session.commit()


def seed_accounts():
    accounts = [
        Account(
            account_code="USLSE-001",
            account_name="Apex US Long/Short Equity",
            fund_type="Long/Short Equity",
            base_currency="USD",
            nav=850_000_000
        ),
        Account(
            account_code="GLBMAC-002",
            account_name="Apex Global Macro Fund",
            fund_type="Global Macro",
            base_currency="USD",
            nav=1_200_000_000
        ),
        Account(
            account_code="FICRD-003",
            account_name="Apex Credit Opportunities",
            fund_type="Credit",
            base_currency="USD",
            nav=620_000_000
        ),
        Account(
            account_code="MLTSTR-004",
            account_name="Apex Multi-Strategy",
            fund_type="Multi-Strategy",
            base_currency="USD",
            nav=2_100_000_000
        ),
    ]
    db.session.add_all(accounts)
    db.session.flush()  # This assigns the IDs so we can use them below


def seed_compliance_rules():
    rules = [
        ComplianceRule(
            rule_name="Single Name Concentration",
            rule_type="concentration",
            parameter="symbol",
            threshold=8.0,
            description="No single equity position can exceed 8% of fund NAV"
        ),
        ComplianceRule(
            rule_name="Sector Concentration",
            rule_type="concentration",
            parameter="sector",
            threshold=25.0,
            description="No single sector can exceed 25% of fund NAV"
        ),
        ComplianceRule(
            rule_name="Max Order Size",
            rule_type="position_limit",
            parameter="order_value",
            threshold=50_000_000,
            description="Single order cannot exceed $50M notional"
        ),
        ComplianceRule(
            rule_name="Restricted List - EXAMPLE Corp",
            rule_type="restricted_list",
            parameter="EXMP",
            threshold=0,
            description="Trading restricted due to material non-public information"
        ),
    ]
    db.session.add_all(rules)


def seed_positions():
    """Create existing positions across all asset classes."""
    # Account 1 - US L/S Equity
    eq_positions = [
        ("AAPL", "Apple Inc.", 45000, 195.20, 218.50),
        ("MSFT", "Microsoft Corp", 22000, 390.10, 441.30),
        ("NVDA", "NVIDIA Corp", 15000, 110.50, 132.80),
        ("GOOGL", "Alphabet Inc.", 18000, 155.40, 176.20),
        ("AMZN", "Amazon.com Inc.", -12000, 188.90, 197.40),  # Short position (negative qty)
        ("META", "Meta Platforms", 8000, 480.20, 522.10),
        ("JPM", "JPMorgan Chase", -6000, 245.30, 252.80),
        ("TSLA", "Tesla Inc.", 10000, 242.10, 267.50),
    ]
    for sym, desc, qty, cost, mkt in eq_positions:
        mv = qty * mkt
        pnl = qty * (mkt - cost)
        db.session.add(Position(
            account_id=1, asset_class="Equity", symbol=sym, description=desc,
            quantity=qty, avg_cost=cost, market_price=mkt,
            market_value=mv, unrealized_pnl=pnl, currency="USD"
        ))

    # Account 2 - Global Macro (FX + Rates)
    fx_positions = [
        ("EUR/USD", "Euro vs US Dollar", 25_000_000, 1.0820, 1.0945),
        ("USD/JPY", "US Dollar vs Yen", -15_000_000, 152.30, 150.80),
        ("GBP/USD", "British Pound vs Dollar", 10_000_000, 1.2650, 1.2780),
    ]
    for sym, desc, qty, cost, mkt in fx_positions:
        pnl = qty * (mkt - cost)
        db.session.add(Position(
            account_id=2, asset_class="FX", symbol=sym, description=desc,
            quantity=qty, avg_cost=cost, market_price=mkt,
            market_value=qty * mkt, unrealized_pnl=pnl, currency="USD"
        ))

    # Account 3 - Credit (Fixed Income)
    fi_positions = [
        ("UST 10Y", "US Treasury 10Y 4.25% 2034", 50_000_000, 98.50, 97.20),
        ("UST 2Y", "US Treasury 2Y 4.75% 2026", 30_000_000, 99.80, 99.95),
        ("AAPL 3.5 30", "Apple 3.5% 2030", 10_000_000, 96.20, 97.10),
        ("JPM 4.25 29", "JPMorgan 4.25% 2029", 15_000_000, 101.30, 102.50),
        ("HYG ETF", "iShares High Yield Corp Bond", 200_000, 78.40, 79.20),
    ]
    for sym, desc, qty, cost, mkt in fi_positions:
        # For bonds, market value = face_value * price / 100
        if "ETF" in sym:
            mv = qty * mkt
            pnl = qty * (mkt - cost)
        else:
            mv = qty * mkt / 100
            pnl = qty * (mkt - cost) / 100
        db.session.add(Position(
            account_id=3, asset_class="Fixed Income", symbol=sym, description=desc,
            quantity=qty, avg_cost=cost, market_price=mkt,
            market_value=mv, unrealized_pnl=pnl, currency="USD"
        ))

    # Account 4 - Multi-Strat (mix of everything)
    deriv_positions = [
        ("SPX 5500C 0325", "S&P 500 5500 Call Mar 25", 500, 42.30, 48.70),
        ("SPX 5200P 0325", "S&P 500 5200 Put Mar 25", -300, 18.50, 15.20),
        ("AAPL 220C 0425", "Apple 220 Call Apr 25", 200, 8.40, 11.20),
        ("IRS 5Y USD", "5Y USD Interest Rate Swap", 100_000_000, 0, 0),
    ]
    for sym, desc, qty, cost, mkt in deriv_positions:
        if "IRS" in sym:
            mv = 100_000_000
            pnl = 340_000
        else:
            mv = qty * mkt * 100  # Options multiplier
            pnl = qty * (mkt - cost) * 100
        db.session.add(Position(
            account_id=4, asset_class="Derivative", symbol=sym, description=desc,
            quantity=qty, avg_cost=cost, market_price=mkt,
            market_value=mv, unrealized_pnl=pnl, currency="USD"
        ))


def seed_orders():
    """
    Create a mix of orders in various states to make the blotter look realistic.
    A real blotter on any given day would have filled orders, partially filled ones,
    some still working, and maybe a couple rejected.
    """
    now = datetime.utcnow().replace(hour=14, minute=30)
    order_counter = 40800

    # Helper to make order IDs look real
    def next_id():
        nonlocal order_counter
        order_counter += 1
        return f"ORD-{order_counter}"

    brokers = ["GS", "JPM", "MS", "BARC", "CITI", "UBS", "BofA", "CS"]
    
    # === EQUITY ORDERS ===
    equity_orders = [
        # Filled orders
        dict(symbol="AAPL", desc="Apple Inc.", side="BUY", qty=5000, otype="Limit",
             limit=218.50, status="Filled", filled=5000, avg=218.32, acct=1,
             comp="Passed", minutes_ago=300),
        dict(symbol="MSFT", desc="Microsoft Corp", side="SELL", qty=2500, otype="Market",
             limit=None, status="Filled", filled=2500, avg=441.18, acct=1,
             comp="Passed", minutes_ago=285),
        dict(symbol="META", desc="Meta Platforms", side="BUY", qty=3000, otype="VWAP",
             limit=None, status="Filled", filled=3000, avg=521.44, acct=1,
             comp="Passed", minutes_ago=240),
        dict(symbol="GOOGL", desc="Alphabet Inc.", side="BUY", qty=4000, otype="Limit",
             limit=176.00, status="Filled", filled=4000, avg=175.88, acct=4,
             comp="Passed", minutes_ago=220),
        
        # Partial fills
        dict(symbol="NVDA", desc="NVIDIA Corp", side="BUY", qty=8000, otype="Limit",
             limit=132.75, status="Partial", filled=5200, avg=132.60, acct=1,
             comp="Passed", minutes_ago=150),
        dict(symbol="TSLA", desc="Tesla Inc.", side="SELL", qty=6000, otype="TWAP",
             limit=None, status="Partial", filled=3800, avg=267.22, acct=4,
             comp="Passed", minutes_ago=90),
        
        # Working orders
        dict(symbol="AMZN", desc="Amazon.com Inc.", side="SELL", qty=3000, otype="Limit",
             limit=198.00, status="Working", filled=0, avg=None, acct=1,
             comp="Passed", minutes_ago=60),
        dict(symbol="JPM", desc="JPMorgan Chase", side="BUY", qty=4000, otype="VWAP",
             limit=None, status="Working", filled=1200, avg=252.44, acct=1,
             comp="Passed", minutes_ago=30),
        
        # Rejected
        dict(symbol="TSLA", desc="Tesla Inc.", side="BUY", qty=50000, otype="Limit",
             limit=265.00, status="Rejected", filled=0, avg=None, acct=1,
             comp="Failed", comp_note="Exceeds single-name concentration limit (8% of NAV)",
             minutes_ago=75),
    ]

    # === FIXED INCOME ORDERS ===
    fi_orders = [
        dict(symbol="UST 10Y", desc="US Treasury 10Y 4.25% 2034", side="BUY",
             qty=25_000_000, otype="Limit", limit=97.50, status="Filled",
             filled=25_000_000, avg=97.35, acct=3, comp="Passed", minutes_ago=260,
             ac="Fixed Income"),
        dict(symbol="MSFT 4.0 32", desc="Microsoft 4.0% 2032", side="BUY",
             qty=5_000_000, otype="Market", limit=None, status="Filled",
             filled=5_000_000, avg=103.25, acct=3, comp="Passed", minutes_ago=200,
             ac="Fixed Income"),
        dict(symbol="UST 5Y", desc="US Treasury 5Y 4.5% 2029", side="SELL",
             qty=15_000_000, otype="Limit", limit=99.20, status="Working",
             filled=0, avg=None, acct=3, comp="Passed", minutes_ago=45,
             ac="Fixed Income"),
    ]

    # === FX ORDERS ===
    fx_orders = [
        dict(symbol="EUR/USD", desc="Euro vs US Dollar", side="BUY",
             qty=10_000_000, otype="Limit", limit=1.0930, status="Filled",
             filled=10_000_000, avg=1.0928, acct=2, comp="Passed", minutes_ago=270,
             ac="FX", cpair="EUR/USD"),
        dict(symbol="USD/JPY", desc="US Dollar vs Yen", side="SELL",
             qty=8_000_000, otype="Market", limit=None, status="Filled",
             filled=8_000_000, avg=150.82, acct=2, comp="Passed", minutes_ago=180,
             ac="FX", cpair="USD/JPY"),
        dict(symbol="GBP/USD", desc="British Pound vs Dollar", side="BUY",
             qty=5_000_000, otype="Limit", limit=1.2800, status="Working",
             filled=0, avg=None, acct=2, comp="Passed", minutes_ago=20,
             ac="FX", cpair="GBP/USD"),
    ]

    # === DERIVATIVE ORDERS ===
    deriv_orders = [
        dict(symbol="SPX 5600C 0425", desc="S&P 500 5600 Call Apr 25", side="BUY",
             qty=200, otype="Limit", limit=35.50, status="Filled",
             filled=200, avg=35.20, acct=4, comp="Passed", minutes_ago=230,
             ac="Derivative"),
        dict(symbol="AAPL 225C 0425", desc="Apple 225 Call Apr 25", side="SELL",
             qty=150, otype="Limit", limit=6.80, status="Partial",
             filled=100, avg=6.85, acct=4, comp="Passed", minutes_ago=100,
             ac="Derivative"),
    ]

    all_orders = equity_orders + fi_orders + fx_orders + deriv_orders

    for o in all_orders:
        order = Order(
            order_id=next_id(),
            asset_class=o.get("ac", "Equity"),
            symbol=o["symbol"],
            description=o["desc"],
            side=o["side"],
            quantity=o["qty"],
            order_type=o["otype"],
            limit_price=o["limit"],
            status=o["status"],
            filled_qty=o["filled"],
            avg_price=o["avg"],
            broker=random.choice(brokers),
            account_id=o["acct"],
            compliance_status=o["comp"],
            compliance_note=o.get("comp_note", ""),
            created_at=now - timedelta(minutes=o["minutes_ago"]),
            tif="DAY",
            currency_pair=o.get("cpair"),
        )
        db.session.add(order)
        db.session.flush()  # Get the order.id assigned right away

        # Create execution records for filled/partial orders
        if o["filled"] > 0 and o["avg"] is not None:
            remaining = o["filled"]
            exec_count = 0
            while remaining > 0:
                exec_count += 1
                if remaining == o["filled"] and random.random() > 0.5:
                    fill = remaining
                else:
                    fill = min(remaining, max(1, int(remaining * random.uniform(0.3, 0.7))))
                
                variance = o["avg"] * 0.001 * random.uniform(-1, 1)
                fill_price = round(o["avg"] + variance, 4)
                
                exec_time = now - timedelta(
                    minutes=o["minutes_ago"] - random.randint(1, max(2, o["minutes_ago"] // 2))
                )
                
                db.session.add(Execution(
                    exec_id=f"EXE-{order_counter:05d}-{exec_count}",
                    order_id=order.id,
                    fill_qty=fill,
                    fill_price=fill_price,
                    venue=random.choice(["NYSE", "NASDAQ", "ARCA", "BATS", "IEX", "DARK"]),
                    exec_time=exec_time,
                    settle_status=random.choice(["Pending", "Matched", "Settled"]),
                    settle_date="T+2" if o.get("ac", "Equity") in ("Equity", "Fixed Income") else "T+1",
                ))
                remaining -= fill
