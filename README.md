# Stock Trading Analysis System

## Advanced Intraday Trading System with AI

A comprehensive stock trading analysis system that combines technical analysis, deep learning (CNN-LSTM), and backtesting to generate BUY/SELL recommendations for US stocks.

### Features

- **📊 Real-time Data**: Live stock data from Yahoo Finance
- **🔬 Technical Analysis**: RSI, MACD, Stochastic, Bollinger Bands
- **🧠 AI Model**: CNN-LSTM hybrid neural network (TensorFlow/Keras)
- **📈 Backtesting**: Walk-forward validation, Monte Carlo simulation
- **⚠️ Overfitting Prevention**: Cross-validation, parameter stability analysis
- **📱 Web Interface**: Streamlit dashboard (mobile-friendly)

### Quick Start

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the web app**:
```bash
streamlit run app.py
```

3. **Or run CLI analysis**:
```bash
python main.py
```

### Project Structure

```
stock_trader/
├── app.py              # Streamlit web app
├── main.py             # CLI entry point
├── config.py           # Configuration
├── data/              # Data fetching
├── analysis/          # Technical indicators
├── models/             # CNN-LSTM model
├── backtest/           # Backtesting engine
├── trading/            # Signal generation
└── requirements.txt    # Dependencies
```

### Deployment

Deploy to **Streamlit Cloud** (free):

1. Push to GitHub
2. Go to https://share.streamlit.io
3. Connect your GitHub repo
4. Deploy!

### Tech Stack

- **Python** - Core logic
- **Streamlit** - Web interface
- **TensorFlow/Keras** - CNN-LSTM deep learning
- **scikit-learn** - Parameter optimization
- **yfinance** - Stock data
- **plotly** - Charts

### Disclaimer

This is NOT financial advice. Always do your own research before trading. Past performance does not guarantee future results.