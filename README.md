# Stock Trading Analysis System

Automated intraday trading system with AI-powered analysis for US markets.

## Features

- **Technical Analysis**: RSI, MACD, Stochastic, Bollinger Bands, VWAP
- **AI Model**: CNN-LSTM deep learning for price prediction (74.94% accuracy)
- **Intraday Trading**: Real-time VWAP analysis and momentum indicators
- **Automated Trading**: Continuous market monitoring with paper trading
- **Notifications**: Email, Telegram, and Windows Toast alerts
- **Paper Trading**: Simulated trading to validate strategies

## Quick Start

### 1. Run Web App
```bash
python -m streamlit run app.py
```
Open http://localhost:8501

### 2. Run CLI Scanner
```bash
# Full watchlist scan
python daily_workflow.py --scan

# Single stock analysis
python daily_workflow.py AAPL

# Intraday analysis
python daily_workflow.py --intraday AAPL
```

### 3. Automated Trading
```bash
# Single market scan
python auto_trader.py --scan

# Continuous monitoring
python auto_trader.py --continuous

# Check system status
python auto_trader.py --status
```

## Market Hours (HK Timezone)

| Session | HKT Time |
|---------|----------|
| Pre-Market | 04:00 - 21:30 |
| Regular Market | 21:30 - 04:00 |
| After Hours | 04:00 - 20:00 |

## Configuration

Edit `config.py` to customize:
- Trading capital and risk parameters
- Watchlist stocks
- Notification settings (Telegram/Email)
- Paper trading API keys (Alpaca)

## Setting Up Notifications

### Telegram (Recommended - Free)
1. Message @BotFather on Telegram
2. Create a new bot and get the token
3. Get your chat ID from @userinfobot
4. Add to config.py:
```python
TELEGRAM_BOT_TOKEN = "your_token"
TELEGRAM_CHAT_ID = "your_chat_id"
ENABLE_TELEGRAM_NOTIFICATIONS = True
```

### Email
Add your email to config.py:
```python
NOTIFICATION_EMAIL = "your_email@gmail.com"
ENABLE_EMAIL_NOTIFICATIONS = True
```

## Paper Trading Setup (Alpaca - Free)

1. Sign up at https://app.alpaca.markets
2. Get API keys from dashboard
3. Add to config.py:
```python
ALPACA_API_KEY = "your_key"
ALPACA_API_SECRET = "your_secret"
```

## Project Structure

```
stock_trader/
├── app.py              # Streamlit web app
├── auto_trader.py      # Automated trading system
├── daily_workflow.py   # CLI scanner
├── notifications.py    # Alert system
├── paper_trading.py    # Paper trading simulator
├── config.py           # Configuration
├── analysis/
│   ├── technical.py    # Technical indicators
│   ├── intraday.py     # Intraday analysis
│   └── sentiment.py    # News sentiment
├── data/
│   └── fetcher.py      # Stock data fetcher
├── trading/
│   ├── signals.py      # Trade signals
│   └── risk_management.py
├── models/
│   └── best_model.pth  # Trained AI model
└── output/
    └── paper_trades.json
```

## Disclaimer

This software is for educational purposes only. Stock trading involves risk. Past performance does not guarantee future results. Always do your own research before trading.