"""
Yahoo Finance Data Fetcher
Fetches stock data, fundamentals, and real-time quotes
"""

import yfinance as yf
import pandas as pd
import numpy as np
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)


class StockDataFetcher:
    """Fetches stock data from Yahoo Finance with caching"""
    
    def __init__(self, rate_limit_pause: float = config.YFINANCE_RATE_LIMIT_PAUSE):
        self.rate_limit_pause = rate_limit_pause
        self.cache = {}
        self.cache_timestamps = {}
        
    def _is_cache_valid(self, symbol: str, cache_type: str, duration_minutes: int = 5) -> bool:
        key = f"{symbol}_{cache_type}"
        if key not in self.cache_timestamps:
            return False
        elapsed = (datetime.now() - self.cache_timestamps[key]).total_seconds() / 60
        return elapsed < duration_minutes
    
    def _update_cache(self, symbol: str, cache_type: str, data):
        key = f"{symbol}_{cache_type}"
        self.cache[key] = data
        self.cache_timestamps[key] = datetime.now()
    
    def _rate_limit(self):
        time.sleep(self.rate_limit_pause)
    
    def get_realtime_quote(self, symbol: str) -> Optional[Dict]:
        cache_key = f"{symbol}_realtime"
        
        if self._is_cache_valid(symbol, 'realtime', duration_minutes=1):
            return self.cache[cache_key]
        
        try:
            self._rate_limit()
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            quote = {
                'symbol': symbol,
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'previous_close': info.get('previousClose') or info.get('regularMarketPreviousClose'),
                'open': info.get('open') or info.get('regularMarketOpen'),
                'day_high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
                'day_low': info.get('dayLow') or info.get('regularMarketDayLow'),
                'volume': info.get('volume') or info.get('regularMarketVolume'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'eps': info.get('trailingEps'),
                'beta': info.get('beta'),
                '50_day_avg': info.get('fiftyDayAverage'),
                '200_day_avg': info.get('twoHundredDayAverage'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'avg_volume': info.get('averageVolume'),
                'timestamp': datetime.now().isoformat()
            }
            
            self._update_cache(symbol, 'realtime', quote)
            return quote
            
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = '1mo', interval: str = '5m') -> Optional[pd.DataFrame]:
        cache_key = f"{symbol}_{period}_{interval}"
        
        if self._is_cache_valid(symbol, cache_key, duration_minutes=5):
            return self.cache[cache_key]
        
        try:
            self._rate_limit()
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                return None
            
            df = df.reset_index()
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            self._update_cache(symbol, cache_key, df)
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def get_daily_data(self, symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
        try:
            self._rate_limit()
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if df.empty:
                return None
            
            df = df.reset_index()
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching daily data for {symbol}: {e}")
            return None
    
    def get_fundamentals(self, symbol: str) -> Optional[Dict]:
        cache_key = f"{symbol}_fundamentals"
        
        if self._is_cache_valid(symbol, 'fundamentals', duration_minutes=60):
            return self.cache[cache_key]
        
        try:
            self._rate_limit()
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            fundamentals = {
                'symbol': symbol,
                'company_name': info.get('shortName') or info.get('longName'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'eps': info.get('trailingEps'),
                'forward_eps': info.get('forwardEps'),
                'revenue': info.get('totalRevenue'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'profit_margin': info.get('profitMargins'),
                'operating_margin': info.get('operatingMargins'),
                'roe': info.get('returnOnEquity'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'dividend_yield': info.get('dividendYield'),
                'payout_ratio': info.get('payoutRatio'),
                'beta': info.get('beta'),
                'avg_volume': info.get('averageVolume'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'week_52_high': info.get('fiftyTwoWeekHigh'),
                'week_52_low': info.get('fiftyTwoWeekLow'),
                'analyst_target': info.get('targetMeanPrice'),
                'analyst_rating': info.get('recommendationKey'),
                'timestamp': datetime.now().isoformat()
            }
            
            self._update_cache(symbol, 'fundamentals', fundamentals)
            return fundamentals
            
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return None
    
    def get_batch_quotes(self, symbols: List[str]) -> List[Dict]:
        quotes = []
        for symbol in symbols:
            quote = self.get_realtime_quote(symbol)
            if quote:
                quotes.append(quote)
        return quotes
    
    def clear_cache(self):
        self.cache = {}
        self.cache_timestamps = {}


def fetch_stock_data(symbol: str) -> Dict:
    """Fetch all stock data (quote, history, fundamentals)"""
    fetcher = StockDataFetcher()
    
    data = {
        'symbol': symbol,
        'quote': fetcher.get_realtime_quote(symbol),
        'history_5min': fetcher.get_historical_data(symbol, period='5d', interval='5m'),
        'history_daily': fetcher.get_daily_data(symbol, days=365),
        'fundamentals': fetcher.get_fundamentals(symbol),
        'timestamp': datetime.now().isoformat()
    }
    
    return data


def fetch_multiple_stocks(symbols: List[str]) -> List[Dict]:
    """Fetch data for multiple stocks"""
    fetcher = StockDataFetcher()
    results = []
    
    for symbol in symbols:
        try:
            data = fetch_stock_data(symbol)
            if data['quote']:
                results.append(data)
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
    
    return results