"""
Interactive Brokers (IBKR) Integration
Connect your app to IBKR for real trading
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_ibkr_setup_instructions():
    """Get step-by-step IBKR setup instructions"""
    return """
# IBKR Trading Setup Guide

## Step 1: Enable API Access in IBKR
1. Log in to IBKR Trader Workstation (TWS)
2. Go to **Edit** → **Preferences** → **API**
3. Check **Enable ActiveX and Socket Clients**
4. Set **Socket port** to 7496 (paper) or 7497 (live)
5. Add your IP address or allow all (127.0.0.1)

## Step 2: Get IB Gateway or TWS Running
- Download IB Gateway from: https://interactivebrokers.com/api
- Or enable API in your TWS desktop app
- Make sure it's running before trading

## Step 3: Install IB API Library
```bash
pip install ib_insync
```

## Step 4: Connect and Trade
```python
from brokers.ibkr_trader import IBKRTrader

# Initialize
trader = IBKRTrader()

# Connect
trader.connect()

# Place a BUY order
trader.place_order(
    symbol='TSLA',
    action='BUY',
    quantity=10,
    order_type='LMT',
    price=245.50
)

# Place with stop loss
trader.place_bracket_order(
    symbol='TSLA',
    action='BUY',
    quantity=10,
    entry_price=245.50,
    stop_price=242.00,
    target_price=252.00
)
```

---

## Quick Reference for IBKR Mobile/TWS

### Manual Trade Entry:
1. **Symbol**: Enter stock symbol (e.g., TSLA)
2. **Action**: BUY or SELL
3. **Quantity**: Number of shares
4. **Order Type**: LMT (Limit) or MKT (Market)
5. **Price**: Your entry price
6. **Advanced**: Add stop loss and target

### For Stop Loss:
- Order Type: **STP**
- Price: Your stop price (e.g., $242.00)

### For Target:
- Order Type: **LMT**
- Price: Your target (e.g., $252.00)

---

## Important Settings:
- **Time in Force**: DAY or GTC (Good Till Cancelled)
- **Destination**: SMART (auto-route)
- **Paper Trading**: Use paper account for testing first
"""

def get_manual_trade_steps():
    """Get manual trade steps for IBKR"""
    return """
# How to Enter Trade in IBKR

## In TWS (Desktop):
1. Type symbol in search box
2. Click **BUY** or **SELL**
3. Select **Quantity**: Use the shares number from app
4. Select **Order Type**: LIMIT
5. **Price**: Enter the Entry price from app
6. Click **Advanced** → Add **Stop Loss** and **Take Profit**
7. Submit order

## In IBKR Mobile:
1. Tap **Trade** tab
2. Search symbol
3. Tap **BUY** or **SELL**
4. Set quantity from app
5. Tap **Price Type** → **Limit**
6. Enter price
7. Tap **More Options** → Add stop loss
8. Submit

## Stop Loss Setup:
- Tap **Stop Loss**
- Enter stop price from app (e.g., $242.00)

## Take Profit Setup:
- Tap **Take Profit**
- Enter target price from app (e.g., $252.00)
"""

# IBKR Order Types Reference
ORDER_TYPES = {
    'MARKET': 'MKT - Market order, executes immediately',
    'LIMIT': 'LMT - Limit order at specific price',
    'STOP': 'STP - Stop loss trigger',
    'STOP_LIMIT': 'STL - Stop with limit price',
    'BRACKET': 'Bracket - Entry + Stop + Target'
}

# Quick Trade Template
TRADE_TEMPLATE = """
## Trade Template for {symbol}

| Field | Value |
|-------|-------|
| Symbol | {symbol} |
| Action | {action} |
| Quantity | {shares} |
| Order Type | LIMIT |
| Limit Price | ${entry:.2f} |
| Stop Loss | ${stop:.2f} |
| Take Profit | ${target:.2f} |
| Risk | ${risk:.2f} |
| Reward | ${reward:.2f} |
| R:R Ratio | {rr_ratio:.1f}x |

### IBKR Steps:
1. Open IBKR → Trade tab
2. Enter symbol: {symbol}
3. Select: {action}
4. Quantity: {shares}
5. Order Type: LIMIT
6. Price: ${entry:.2f}
7. Advanced → Stop: ${stop:.2f}
8. Advanced → Target: ${target:.2f}
9. Review & Submit
"""