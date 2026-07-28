"""Market Breadth & Sector Correlation Analysis for Signal Validation"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


class MarketAnalyzer:
    """Analyzes market breadth, sector trends, and correlations"""
    
    # Major ETFs for market breadth
    MARKET_ETFS = {
        'SPY': 'S&P 500',
        'QQQ': 'Nasdaq 100',
        'IWM': 'Russell 2000',
        'DIA': 'Dow Jones',
        'VTI': 'Total Market'
    }
    
    # Sector ETFs
    SECTOR_ETFS = {
        'XLK': 'Technology',
        'XLF': 'Financials',
        'XLV': 'Healthcare',
        'XLE': 'Energy',
        'XLI': 'Industrials',
        'XLY': 'Consumer Discretionary',
        'XLP': 'Consumer Staples',
        'XLB': 'Materials',
        'XLU': 'Utilities',
        'XLRE': 'Real Estate',
        'XLC': 'Communication Services'
    }
    
    # Stock to sector mapping
    STOCK_SECTORS = {
        'AAPL': 'XLK', 'MSFT': 'XLK', 'NVDA': 'XLK', 'AMD': 'XLK', 'INTC': 'XLK',
        'GOOGL': 'XLC', 'META': 'XLC', 'NFLX': 'XLC',
        'AMZN': 'XLY', 'TSLA': 'XLY', 'HD': 'XLY', 'NKE': 'XLY',
        'JPM': 'XLF', 'BAC': 'XLF', 'WFC': 'XLF', 'GS': 'XLF', 'MS': 'XLF', 'C': 'XLF', 'V': 'XLF', 'MA': 'XLF',
        'JNJ': 'XLV', 'PFE': 'XLV', 'UNH': 'XLV', 'ABBV': 'XLV', 'MRK': 'XLV', 'TMO': 'XLV', 'ABT': 'XLV',
        'XOM': 'XLE', 'CVX': 'XLE', 'COP': 'XLE',
        'CAT': 'XLI', 'BA': 'XLI', 'GE': 'XLI', 'HON': 'XLI',
        'PG': 'XLP', 'KO': 'XLP', 'PEP': 'XLP', 'WMT': 'XLP', 'COST': 'XLP',
        'LIN': 'XLB', 'SHW': 'XLB',
        'NEE': 'XLU', 'SO': 'XLU',
        'PLD': 'XLRE', 'AMT': 'XLRE'
    }
    
    def __init__(self):
        self.market_data = {}
        self.sector_data = {}
        self.breadth_indicators = {}
    
    def fetch_market_data(self) -> Dict:
        """Fetch market breadth data"""
        results = {}
        
        def fetch_etf(symbol):
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period='1mo', auto_adjust=True)
                if not df.empty:
                    return symbol, {
                        'price': df['Close'].iloc[-1],
                        'change_1d': (df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100 if len(df) > 1 else 0,
                        'change_5d': (df['Close'].iloc[-1] / df['Close'].iloc[-6] - 1) * 100 if len(df) > 5 else 0,
                        'change_20d': (df['Close'].iloc[-1] / df['Close'].iloc[-21] - 1) * 100 if len(df) > 20 else 0,
                        'volume': df['Volume'].iloc[-1],
                        'sma_20': df['Close'].rolling(20).mean().iloc[-1],
                        'above_sma20': df['Close'].iloc[-1] > df['Close'].rolling(20).mean().iloc[-1],
                        'rsi': self._calc_rsi(df['Close']),
                        'trend': 'BULLISH' if df['Close'].iloc[-1] > df['Close'].rolling(20).mean().iloc[-1] else 'BEARISH'
                    }
            except:
                pass
            return symbol, None
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_etf, sym): sym for sym in self.MARKET_ETFS}
            for future in as_completed(futures):
                sym, data = future.result()
                if data:
                    results[sym] = data
        
        self.market_data = results
        return results
    
    def fetch_sector_data(self) -> Dict:
        """Fetch sector ETF data"""
        results = {}
        
        def fetch_sector(symbol):
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period='1mo', auto_adjust=True)
                if not df.empty:
                    return symbol, {
                        'price': df['Close'].iloc[-1],
                        'change_1d': (df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100 if len(df) > 1 else 0,
                        'change_5d': (df['Close'].iloc[-1] / df['Close'].iloc[-6] - 1) * 100 if len(df) > 5 else 0,
                        'change_20d': (df['Close'].iloc[-1] / df['Close'].iloc[-21] - 1) * 100 if len(df) > 20 else 0,
                        'volume': df['Volume'].iloc[-1],
                        'rsi': self._calc_rsi(df['Close']),
                        'trend': 'BULLISH' if df['Close'].iloc[-1] > df['Close'].rolling(20).mean().iloc[-1] else 'BEARISH',
                        'name': self.SECTOR_ETFS.get(symbol, symbol)
                    }
            except:
                pass
            return symbol, None
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(fetch_sector, sym): sym for sym in self.SECTOR_ETFS}
            for future in as_completed(futures):
                sym, data = future.result()
                if data:
                    results[sym] = data
        
        self.sector_data = results
        return results
    
    def calculate_market_breadth(self) -> Dict:
        """Calculate market breadth indicators"""
        if not self.market_data:
            self.fetch_market_data()
        
        if not self.sector_data:
            self.fetch_sector_data()
        
        # Count bullish vs bearish ETFs
        bullish_etfs = sum(1 for d in self.market_data.values() if d.get('trend') == 'BULLISH')
        bearish_etfs = sum(1 for d in self.market_data.values() if d.get('trend') == 'BEARISH')
        total_etfs = len(self.market_data)
        
        # Count bullish vs bearish sectors
        bullish_sectors = sum(1 for d in self.sector_data.values() if d.get('trend') == 'BULLISH')
        bearish_sectors = sum(1 for d in self.sector_data.values() if d.get('trend') == 'BEARISH')
        total_sectors = len(self.sector_data)
        
        # Advance/Decline ratio
        ad_ratio = bullish_etfs / bearish_etfs if bearish_etfs > 0 else bullish_etfs
        
        # Market breadth score (-100 to +100)
        breadth_score = ((bullish_etfs - bearish_etfs) / total_etfs * 100) if total_etfs > 0 else 0
        
        # Sector breadth score
        sector_breadth = ((bullish_sectors - bearish_sectors) / total_sectors * 100) if total_sectors > 0 else 0
        
        # Overall market health
        if breadth_score > 30:
            market_health = 'STRONG_BULLISH'
        elif breadth_score > 10:
            market_health = 'BULLISH'
        elif breadth_score > -10:
            market_health = 'NEUTRAL'
        elif breadth_score > -30:
            market_health = 'BEARISH'
        else:
            market_health = 'STRONG_BEARISH'
        
        # SPY specific metrics
        spy_data = self.market_data.get('SPY', {})
        
        self.breadth_indicators = {
            'market_health': market_health,
            'breadth_score': round(breadth_score, 1),
            'sector_breadth': round(sector_breadth, 1),
            'bullish_etfs': bullish_etfs,
            'bearish_etfs': bearish_etfs,
            'total_etfs': total_etfs,
            'bullish_sectors': bullish_sectors,
            'bearish_sectors': bearish_sectors,
            'total_sectors': total_sectors,
            'ad_ratio': round(ad_ratio, 2),
            'spy_change_5d': round(spy_data.get('change_5d', 0), 2),
            'spy_rsi': round(spy_data.get('rsi', 50), 1),
            'spy_trend': spy_data.get('trend', 'NEUTRAL')
        }
        return self.breadth_indicators
    
    def get_sector_correlation(self, symbol: str) -> Dict:
        """Get sector correlation for a stock"""
        sector_etf = self.STOCK_SECTORS.get(symbol)
        if not sector_etf:
            return {'sector': 'Unknown', 'sector_trend': 'NEUTRAL', 'correlation': 'N/A'}
        
        if not self.sector_data:
            self.fetch_sector_data()
        
        sector_info = self.sector_data.get(sector_etf, {})
        
        return {
            'symbol': symbol,
            'sector_etf': sector_etf,
            'sector_name': self.SECTOR_ETFS.get(sector_etf, 'Unknown'),
            'sector_trend': sector_info.get('trend', 'NEUTRAL'),
            'sector_change_5d': round(sector_info.get('change_5d', 0), 2),
            'sector_change_20d': round(sector_info.get('change_20d', 0), 2),
            'sector_rsi': round(sector_info.get('rsi', 50), 1),
            'aligned_with_sector': True  # Will be determined by signal direction
        }
    
    def validate_signal_with_market(self, signal: str, symbol: str) -> Dict:
        """Validate a trading signal against market conditions"""
        if not self.breadth_indicators:
            self.calculate_market_breadth()
        
        sector_info = self.get_sector_correlation(symbol)
        
        market_health = self.breadth_indicators.get('market_health', 'NEUTRAL')
        sector_trend = sector_info.get('sector_trend', 'NEUTRAL')
        
        # Validation logic
        validation_score = 0
        warnings = []
        confirmations = []
        
        # Market breadth validation
        if signal == 'BUY':
            if market_health in ['STRONG_BULLISH', 'BULLISH']:
                validation_score += 30
                confirmations.append(f"Strong market breadth ({market_health})")
            elif market_health == 'NEUTRAL':
                validation_score += 10
            else:
                validation_score -= 20
                warnings.append(f"Buying against bearish market ({market_health})")
        elif signal == 'SELL':
            if market_health in ['STRONG_BEARISH', 'BEARISH']:
                validation_score += 30
                confirmations.append(f"Bearish market supports selling ({market_health})")
            elif market_health == 'NEUTRAL':
                validation_score += 10
            else:
                validation_score -= 20
                warnings.append(f"Selling against bullish market ({market_health})")
        
        # Sector alignment
        if signal == 'BUY' and sector_trend == 'BULLISH':
            validation_score += 25
            confirmations.append(f"Sector {sector_info['sector_name']} is bullish")
        elif signal == 'SELL' and sector_trend == 'BEARISH':
            validation_score += 25
            confirmations.append(f"Sector {sector_info['sector_name']} is bearish")
        elif signal == 'BUY' and sector_trend == 'BEARISH':
            validation_score -= 15
            warnings.append(f"Buying against bearish sector ({sector_info['sector_name']})")
        elif signal == 'SELL' and sector_trend == 'BULLISH':
            validation_score -= 15
            warnings.append(f"Selling against bullish sector ({sector_info['sector_name']})")
        
        # SPY trend check
        spy_trend = self.breadth_indicators.get('spy_trend', 'NEUTRAL')
        if signal == 'BUY' and spy_trend == 'BULLISH':
            validation_score += 15
            confirmations.append("SPY trend is bullish")
        elif signal == 'SELL' and spy_trend == 'BEARISH':
            validation_score += 15
            confirmations.append("SPY trend is bearish")
        
        # Determine validation result
        if validation_score >= 30:
            validation = 'CONFIRMED'
        elif validation_score >= 0:
            validation = 'NEUTRAL'
        else:
            validation = 'WEAK'
        
        return {
            'validation': validation,
            'validation_score': validation_score,
            'market_health': market_health,
            'sector_trend': sector_trend,
            'sector_name': sector_info.get('sector_name', 'Unknown'),
            'confirmations': confirmations,
            'warnings': warnings,
            'breadth_score': self.breadth_indicators.get('breadth_score', 0),
            'sector_breadth': self.breadth_indicators.get('sector_breadth', 0),
            'ad_ratio': self.breadth_indicators.get('ad_ratio', 1.0)
        }
    
    def _calc_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.isna().all() else 50.0
