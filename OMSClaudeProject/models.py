"""
Database models for the OMS.

Each class here becomes a table in the SQLite database.
SQLAlchemy is an ORM (Object Relational Mapper) - it lets you work with
database rows as Python objects instead of writing raw SQL.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Account(db.Model):
    """
    Represents a fund/portfolio account.
    On the buy-side, you might manage multiple funds (e.g., a US equity fund,
    a global macro fund, etc.) and each has its own account.
    """
    id = db.Column(db.Integer, primary_key=True)
    account_code = db.Column(db.String(20), unique=True, nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    fund_type = db.Column(db.String(50))  # e.g., "Long/Short Equity", "Global Macro"
    base_currency = db.Column(db.String(3), default="USD")
    nav = db.Column(db.Float, default=0.0)  # Net Asset Value

    # This creates a relationship so you can do account.orders to get all orders
    orders = db.relationship("Order", backref="account", lazy=True)
    positions = db.relationship("Position", backref="account", lazy=True)


class Order(db.Model):
    """
    The core of the OMS - an order represents an instruction to buy or sell.
    
    The lifecycle of an order:
    New -> Compliance Check -> Sent to Broker -> Working -> Partially Filled -> Filled
    
    Or it can be: New -> Compliance Check -> Rejected (if it fails a rule)
    """
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable=False)
    
    # What are we trading?
    asset_class = db.Column(db.String(20), nullable=False)  # Equity, Fixed Income, FX, Derivative
    symbol = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(100))  # e.g., "Apple Inc." or "US 10Y Treasury"
    
    # Order details
    side = db.Column(db.String(4), nullable=False)  # BUY or SELL
    quantity = db.Column(db.Float, nullable=False)
    order_type = db.Column(db.String(20), nullable=False)  # Market, Limit, Stop, VWAP, TWAP
    limit_price = db.Column(db.Float, nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), default="New")  # New, Working, Partial, Filled, Rejected, Cancelled
    filled_qty = db.Column(db.Float, default=0.0)
    avg_price = db.Column(db.Float, nullable=True)
    
    # Routing info
    broker = db.Column(db.String(20))
    venue = db.Column(db.String(30))  # Exchange or dark pool
    
    # Account link
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    
    # Compliance
    compliance_status = db.Column(db.String(20), default="Pending")  # Pending, Passed, Failed
    compliance_note = db.Column(db.String(200))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Time in force
    tif = db.Column(db.String(10), default="DAY")  # DAY, GTC, IOC, FOK
    
    # FX-specific fields
    currency_pair = db.Column(db.String(10))  # e.g., "EUR/USD"
    settle_date = db.Column(db.String(10))  # T+1, T+2, etc.
    
    # Fixed Income specific
    coupon = db.Column(db.Float)
    maturity_date = db.Column(db.String(20))
    yield_value = db.Column(db.Float)

    executions = db.relationship("Execution", backref="order", lazy=True)


class Execution(db.Model):
    """
    Each time part of an order gets filled, that creates an execution record.
    One order can have many executions (partial fills).
    
    For example, if you want to buy 10,000 shares of AAPL, it might fill in 
    chunks: 3,000 at $218.50, then 4,000 at $218.55, then 3,000 at $218.48.
    Each of those is a separate execution.
    """
    id = db.Column(db.Integer, primary_key=True)
    exec_id = db.Column(db.String(20), unique=True, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    
    fill_qty = db.Column(db.Float, nullable=False)
    fill_price = db.Column(db.Float, nullable=False)
    venue = db.Column(db.String(30))
    exec_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Settlement info - this is key for trade ops
    settle_status = db.Column(db.String(20), default="Pending")  # Pending, Matched, Settled, Failed
    settle_date = db.Column(db.String(10))  # The actual date it should settle


class Position(db.Model):
    """
    Current holdings in each account.
    Positions get updated as orders fill.
    """
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    
    asset_class = db.Column(db.String(20), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(100))
    
    quantity = db.Column(db.Float, default=0.0)
    avg_cost = db.Column(db.Float, default=0.0)
    market_price = db.Column(db.Float, default=0.0)
    market_value = db.Column(db.Float, default=0.0)
    unrealized_pnl = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default="USD")


class ComplianceRule(db.Model):
    """
    Pre-trade compliance rules that get checked before an order goes out.
    Examples: max position size, sector concentration limits, restricted lists.
    """
    id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(100), nullable=False)
    rule_type = db.Column(db.String(50))  # position_limit, concentration, restricted_list
    parameter = db.Column(db.String(50))  # What it checks (e.g., symbol, sector, asset_class)
    threshold = db.Column(db.Float)  # The limit value
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
