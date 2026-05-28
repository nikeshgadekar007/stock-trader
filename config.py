"""
Configuration for Intraday Trading System
Adjust these settings based on your capital and risk tolerance
"""

# =============================================================================
# TRADING PARAMETERS
# =============================================================================

# Your Trading Capital (USD)
CAPITAL = 1000

# Risk Management
MAX_RISK_PER_TRADE = 30  # $30 per trade (3% of $1,000)
MAX_DAILY_RISK = 90  # $90 total daily risk (9%)
MAX_CONCURRENT_TRADES = 3
MIN_RISK_REWARD_RATIO = 2.0  # Minimum 2:1 risk/reward

# Position Sizing
DEFAULT_STOP_LOSS_PCT = 0.03  # 3% stop loss
DEFAULT_TAKE_PROFIT_PCT = 0.05  # 5% take profit
TRAILING_STOP_ACTIVATION = 0.02  # Activate trailing stop after 2% gain
TRAILING_STOP_PCT = 0.015  # 1.5% trailing stop

# =============================================================================
# STOCK FILTERS (Micro-cap focused for $1,000 capital)
# =============================================================================

# Price Range
MIN_PRICE = 0.50
MAX_PRICE = 500.00  # Allow higher priced stocks

# Volume (Liquidity)
MIN_VOLUME = 100000  # Lower minimum volume for more stocks
AVG_VOLUME_PREFERENCE = 500000  # Prefer stocks with 500K+ average volume

# Market Cap
MIN_MARKET_CAP = 0  # No minimum
MAX_MARKET_CAP = 10_000_000_000  # $10B max for more stocks

# Price Movement - Relaxed for more opportunities
MIN_PRICE_CHANGE_PCT = 0.0  # No minimum - any stock
MAX_PRICE_CHANGE_PCT = 50.0  # Allow up to 50% movement

# =============================================================================
# TECHNICAL INDICATORS PARAMETERS
# =============================================================================

# Moving Averages
SMA_PERIODS = [5, 10, 20, 50, 100, 200]
EMA_PERIODS = [9, 12, 26]

# RSI
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
RSI_NEUTRAL_LOW = 40
RSI_NEUTRAL_HIGH = 60

# MACD
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands
BB_PERIOD = 20
BB_STD = 2

# Stochastic
STOCH_PERIOD = 14
STOCH_SMOOTH_K = 3
STOCH_SMOOTH_D = 3

# ATR (for stop loss)
ATR_PERIOD = 14
ATR_MULTIPLIER = 2  # Stop loss at ATR * 2

# Volume
VOLUME_SMA_PERIOD = 20
VOLUME_SPIKE_MULTIPLIER = 1.5  # Volume must be 1.5x average

# =============================================================================
# SCORING WEIGHTS
# =============================================================================

WEIGHT_TECHNICAL = 0.40
WEIGHT_MOMENTUM = 0.25
WEIGHT_FUNDAMENTAL = 0.20
WEIGHT_PATTERN = 0.15

# Minimum score to generate recommendation
MIN_RECOMMENDATION_SCORE = 60

# =============================================================================
# TRADING HOURS (EST - US Market)
# =============================================================================

# Market hours in EST
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0

# Pre-market and after-hours
PRE_MARKET_OPEN_HOUR = 4
AFTER_HOURS_CLOSE_HOUR = 20

# Timezone conversion to HKT (UTC+8)
# EST to HKT: EST + 13 hours
# So 9:30 AM EST = 10:30 PM HKT
TIMEZONE_OFFSET_HOURS = 13

# =============================================================================
# STOCK UNIVERSE
# =============================================================================

# Popular stocks suitable for micro-cap trading
DEFAULT_WATCHLIST = [
    # Tech
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'INTC', 'NFLX',
    # Finance
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'V', 'MA',
    # Healthcare
    'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'TMO', 'ABT',
    # Energy
    'XOM', 'CVX', 'COP', 'SLB', 'OXY',
    # Retail
    'WMT', 'TGT', 'COST', 'HD', 'LOW',
    # Industrial
    'BA', 'CAT', 'GE', 'MMM', 'HON',
    # Micro-cap (high risk/reward) - More volatile, better for BUY signals
    'SPCE', 'PLTR', 'SNAP', 'ROKU', 'SQ', 'HOOD', 'COIN', 'RIVN', 'LCID', 'NKLA',
    # ETFs for safety
    'SPY', 'QQQ', 'IWM', 'DIA', 'TQQQ', 'SQQQ', 'UVXY',
    # High volatility stocks - More likely to be oversold
    'NIO', 'LCID', 'RIVN', 'F', 'GM', 'W', 'PYPL', 'SQ', 'SHOP', 'ZM', 'DOCU', 'NET',
    'CRWD', 'DDOG', 'SNOW', 'U', 'ABNB', 'DASH', 'COIN', 'MARA', 'RIOT', 'SOFI',
    'OPEN', 'OUST', 'LAZR', 'VLTA', 'MAXR', 'LIDAR', 'INVZ', 'AEVA', 'JOBY', 'ACHR',
]

# Sectors to focus on
SECTORS = [
    'Technology',
    'Healthcare', 
    'Finance',
    'Energy',
    'Consumer Cyclical',
]

# =============================================================================
# DATA SOURCES
# =============================================================================

# Yahoo Finance intervals
INTERVAL_1MIN = '1m'
INTERVAL_5MIN = '5m'
INTERVAL_15MIN = '15m'
INTERVAL_1HOUR = '1h'
INTERVAL_1DAY = '1d'

# Data periods
PERIOD_1DAY = '1d'
PERIOD_5DAY = '5d'
PERIOD_1MONTH = '1mo'
PERIOD_3MONTH = '3mo'
PERIOD_6MONTH = '6mo'
PERIOD_1YEAR = '1y'
PERIOD_YTD = 'ytd'
PERIOD_2YEAR = '2y'
PERIOD_5YEAR = '5y'

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================

OUTPUT_DIR = 'output'
CACHE_DIR = 'cache'
CHARTS_DIR = f'{OUTPUT_DIR}/charts'

# Database
TRADES_DB = f'{OUTPUT_DIR}/trades.db'

# Output files
RECOMMENDATIONS_FILE = f'{OUTPUT_DIR}/recommendations.json'
ANALYSIS_REPORT_FILE = f'{OUTPUT_DIR}/analysis_report.html'
TRADES_LOG_FILE = f'{OUTPUT_DIR}/trades.log'

# =============================================================================
# API RATE LIMITS (Free tier)
# =============================================================================

YFINANCE_RATE_LIMIT_PAUSE = 0.5  # Seconds between requests
MAX_RETRIES = 3
CACHE_DURATION_MINUTES = 5  # Cache real-time data for 5 minutes

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'