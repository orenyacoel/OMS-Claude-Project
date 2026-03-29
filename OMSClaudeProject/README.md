# Apex Capital OMS - Demo Order Management System

A buy-side Order Management System built with Python/Flask, designed to demonstrate trading operations workflows across multiple asset classes (Equities, Fixed Income, FX, Derivatives).

## What This Does

This is a functional demo OMS that mirrors the core features of systems like Charles River IMS, Bloomberg AIM, and SS&C Eze - the platforms used daily at hedge funds and asset managers.

### Features (Phase 1 - Core OMS)

- **Trade Blotter** - Real-time view of all orders with status tracking (New, Working, Partial, Filled, Rejected, Cancelled)
- **Order Entry** - Create new orders with full ticket details (side, symbol, quantity, order type, broker, account, TIF)
- **Pre-Trade Compliance** - Automated compliance checks including position concentration limits, max order size, and restricted lists
- **Multi-Asset Support** - Equities, Fixed Income, FX, and Derivatives with asset-class-specific fields
- **Positions View** - Current holdings with real-time P&L across 4 fund accounts
- **Executions View** - Fill-level detail with venue, settlement status, and timestamps
- **Compliance Dashboard** - Active rules and violation history

### Fund Accounts

| Account | Strategy | NAV |
|---------|----------|-----|
| USLSE-001 | US Long/Short Equity | $850M |
| GLBMAC-002 | Global Macro | $1.2B |
| FICRD-003 | Credit Opportunities | $620M |
| MLTSTR-004 | Multi-Strategy | $2.1B |

## Tech Stack

- **Backend**: Python / Flask
- **Database**: SQLite via SQLAlchemy ORM
- **Frontend**: HTML/CSS (dark terminal theme)
- **No JavaScript frameworks** - intentionally lightweight

## Getting Started

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/oms-demo.git
cd oms-demo

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Then open http://localhost:5000 in your browser.

The database auto-populates with demo data on first run. To reset, delete `instance/oms.db` and restart.

## Project Structure

```
oms-demo/
├── app.py              # Main Flask app - routes and API endpoints
├── models.py           # Database models (Account, Order, Execution, Position, ComplianceRule)
├── seed_data.py        # Generates realistic demo data
├── requirements.txt    # Python dependencies
├── static/
│   └── style.css       # Dark terminal-style UI
└── templates/
    ├── base.html       # Layout shell (sidebar nav)
    ├── blotter.html    # Trade blotter + order entry
    ├── positions.html  # Holdings view
    ├── executions.html # Trade fills
    └── compliance.html # Rules and violations
```

## Roadmap

- **Phase 2**: Trade break detection, reconciliation automation, P&L reporting
- **Phase 3**: Live deployment with shareable URL

## About

Built as a portfolio project to demonstrate understanding of buy-side trading operations workflows, the trade lifecycle, and operational automation.
