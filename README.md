# Stock Trading Analysis System

## Advanced Intraday Trading System with AI

A comprehensive stock trading analysis system that combines technical analysis, deep learning (CNN-LSTM), and backtesting to generate BUY/SELL recommendations for US stocks.

### Features

- **Real-time Data**: Live stock data from Yahoo Finance
- **Technical Analysis**: RSI, MACD, Stochastic, Bollinger Bands
- **AI Model**: CNN-LSTM hybrid neural network (PyTorch)
- **News Sentiment**: Analyze news headlines for sentiment
- **Pattern Recognition**: Detect chart patterns (Double Top, Head & Shoulders, etc.)
- **Risk Management**: Position sizing, Kelly Criterion, Sharpe Ratio
- **Portfolio Tracking**: Track trades and P&L
- **Stock Watchlist**: Monitor multiple stocks with alerts
- **Backtesting**: Walk-forward validation, Monte Carlo simulation
- **Web Interface**: Streamlit dashboard (mobile-friendly)

### Quick Start

1. **Run the web app**:
```bash
streamlit run app.py
```

2. **Run daily scan**:
```bash
python daily_workflow.py --scan
```

3. **Analyze single stock**:
```bash
python daily_workflow.py AAPL
```

### Project Structure

```
stock_trader/
├── app.py                    # Streamlit web app
├── main.py                   # CLI entry point
├── daily_workflow.py         # Daily scanning script
├── train_pytorch.py          # AI training script
├── analysis/
│   ├── technical.py          # RSI, MACD, Stochastic
│   ├── sentiment.py          # News sentiment analysis
│   └── pattern_recognition.py # Chart patterns
├── models/
│   ├── cnn_lstm_pytorch.py   # PyTorch model
│   └── best_model.pth         # Trained weights
├── trading/
│   ├── signals.py            # BUY/SELL signals
│   ├── risk_management.py    # Position sizing
│   └── portfolio.py          # Portfolio tracker
├── scanner/
│   └── watchlist.py         # Stock watchlist
└── backtest/
    └── engine.py            # Backtesting engine
```

### Daily Workflow

Run this every day before trading:

```bash
python daily_workflow.py --scan
```

This will:
1. Scan 10 stocks from your watchlist
2. Calculate technical indicators
3. Analyze news sentiment
4. Generate BUY/SELL signals
5. Show top trading opportunities

### Risk Management

The system includes comprehensive risk management:

- **Position Sizing**: Calculate optimal shares based on risk
- **Kelly Criterion**: Optimal bet sizing
- **Risk-Reward Ratio**: Grade A+ to D
- **Value at Risk**: 95% confidence interval
- **Max Drawdown**: Track portfolio losses

### AI Model - ACTIVE

The CNN-LSTM model is trained and ready!

- **Training Data:** 4,207 samples from 18 stocks
- **Best Validation Accuracy:** 74.94%
- **Model Location:** `models/best_model.pth`

### Disclaimer

This is NOT financial advice. Always do your own research before trading. Past performance does not guarantee future results.
