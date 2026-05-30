"""
Configuration for Intraday Trading System
Adjust these settings based on your capital and risk tolerance
"""

# =============================================================================
# TRADING PARAMETERS
# =============================================================================

CAPITAL = 100000  # Alpaca paper trading account
MAX_RISK_PER_TRADE = 300  # $300 per trade (0.3% of $100k)
MAX_DAILY_RISK = 1500  # $1500 total daily risk (1.5%)
MAX_CONCURRENT_TRADES = 5
MIN_RISK_REWARD_RATIO = 2.0
DEFAULT_STOP_LOSS_PCT = 0.02  # 2% stop loss
DEFAULT_TAKE_PROFIT_PCT = 0.04  # 4% take profit

# =============================================================================
# STOCK FILTERS
# =============================================================================

MIN_PRICE = 0.50
MAX_PRICE = 500.00
MIN_VOLUME = 100000
MIN_PRICE_CHANGE_PCT = 0.0
MAX_PRICE_CHANGE_PCT = 50.0

# =============================================================================
# TECHNICAL INDICATORS
# =============================================================================

RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2
STOCH_PERIOD = 14
ATR_PERIOD = 14

# =============================================================================
# STOCK UNIVERSE
# =============================================================================

DEFAULT_WATCHLIST = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'INTC', 'NFLX',
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'V', 'MA',
    'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'TMO', 'ABT',
    'XOM', 'CVX', 'COP', 'SLB', 'OXY',
    'WMT', 'TGT', 'COST', 'HD', 'LOW',
    'BA', 'CAT', 'GE', 'MMM', 'HON',
    'SPCE', 'PLTR', 'SNAP', 'ROKU', 'SQ', 'HOOD', 'COIN', 'RIVN', 'LCID', 'NKLA',
    'SPY', 'QQQ', 'IWM', 'DIA', 'TQQQ', 'SQQQ', 'UVXY',
    'NIO', 'F', 'GM', 'W', 'PYPL', 'SHOP', 'ZM', 'DOCU', 'NET',
    'CRWD', 'DDOG', 'SNOW', 'U', 'ABNB', 'DASH', 'MARA', 'RIOT', 'SOFI',
]

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================

OUTPUT_DIR = 'output'
TRADES_DB = f'{OUTPUT_DIR}/trades.db'
RECOMMENDATIONS_FILE = f'{OUTPUT_DIR}/recommendations.json'
TRADES_LOG_FILE = f'{OUTPUT_DIR}/trades.log'

# =============================================================================
# AUTOMATED TRADING SETTINGS (HK Timezone)
# =============================================================================

TIMEZONE_NAME = 'Asia/Hong_Kong'
PRE_MARKET_START = "04:00"
MARKET_OPEN = "21:30"
MARKET_CLOSE = "04:00"
SCAN_INTERVAL_MINUTES = 15
REAL_TIME_CHECK_SECONDS = 300
AUTO_TRADE_ENABLED = False
PAPER_TRADING_ENABLED = True

# Notifications
NOTIFICATION_EMAIL = "nikeshgadekar07@gmail.com"
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
ENABLE_EMAIL_NOTIFICATIONS = True
ENABLE_TELEGRAM_NOTIFICATIONS = False
ENABLE_TOAST_NOTIFICATIONS = True

# Paper Trading API (Alpaca - Free)
ALPACA_API_KEY = "PKJASTI4PEYKMWGODCD7EQRVLH"
ALPACA_API_SECRET = "8vKgRyFSWuojpH28gfLisQjhmJB32yo3eCM9UL8QhZUx"
ALPACA_PAPER_URL = "https://paper-api.alpaca.markets"
ALPACA_LIVE_URL = "https://api.alpaca.markets"

# Data Fetcher Settings
YFINANCE_RATE_LIMIT_PAUSE = 0.5
MAX_RETRIES = 3
CACHE_DURATION_MINUTES = 5