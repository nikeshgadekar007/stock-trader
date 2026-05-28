"""
Technical Analysis Engine
Calculates comprehensive technical indicators for stock analysis
"""

import pandas as pd
import numpy as np
from typing import Dict


class TechnicalAnalyzer:
    """Calculates technical indicators"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.indicators = {}
        
    def calculate_all(self) -> Dict:
        """Calculate all technical indicators"""
        results = {}
        results['sma'] = self.calculate_sma()
        results['ema'] = self.calculate_ema()
        results['macd'] = self.calculate_macd()
        results['rsi'] = self.calculate_rsi()
        results['stochastic'] = self.calculate_stochastic()
        results['bollinger_bands'] = self.calculate_bollinger_bands()
        results['atr'] = self.calculate_atr()
        results['volume'] = self.calculate_volume_indicators()
        results['signals'] = self.generate_signals()
        self.indicators = results
        return results
    
    def calculate_sma(self) -> Dict:
        periods = [5, 10, 20, 50, 100, 200]
        sma = {}
        for p in periods:
            if len(self.df) >= p:
                sma[f'sma_{p}'] = float(self.df['close'].rolling(window=p).mean().iloc[-1])
        return sma
    
    def calculate_ema(self) -> Dict:
        periods = [9, 12, 26]
        ema = {}
        for p in periods:
            if len(self.df) >= p:
                ema[f'ema_{p}'] = float(self.df['close'].ewm(span=p, adjust=False).mean().iloc[-1])
        return ema
    
    def calculate_macd(self) -> Dict:
        if len(self.df) < 26:
            return {}
        exp12 = self.df['close'].ewm(span=12, adjust=False).mean()
        exp26 = self.df['close'].ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return {
            'macd': float(macd.iloc[-1]),
            'signal': float(signal.iloc[-1]),
            'histogram': float(histogram.iloc[-1]),
            'trend': 'bullish' if histogram.iloc[-1] > 0 else 'bearish'
        }
    
    def calculate_rsi(self, period: int = 14) -> Dict:
        if len(self.df) < period + 1:
            return {}
        delta = self.df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        val = float(rsi.iloc[-1])
        return {
            'rsi': val,
            'signal': 'oversold' if val < 30 else 'overbought' if val > 70 else 'neutral'
        }
    
    def calculate_stochastic(self) -> Dict:
        if len(self.df) < 14:
            return {}
        low_min = self.df['low'].rolling(window=14).min()
        high_max = self.df['high'].rolling(window=14).max()
        k = 100 * (self.df['close'] - low_min) / (high_max - low_min)
        d = k.rolling(window=3).mean()
        return {
            'k': float(k.iloc[-1]),
            'd': float(d.iloc[-1]),
            'signal': 'oversold' if k.iloc[-1] < 20 else 'overbought' if k.iloc[-1] > 80 else 'neutral'
        }
    
    def calculate_bollinger_bands(self) -> Dict:
        if len(self.df) < 20:
            return {}
        sma20 = self.df['close'].rolling(window=20).mean()
        std20 = self.df['close'].rolling(window=20).std()
        upper = sma20 + (2 * std20)
        lower = sma20 - (2 * std20)
        current = float(self.df['close'].iloc[-1])
        return {
            'upper': float(upper.iloc[-1]),
            'middle': float(sma20.iloc[-1]),
            'lower': float(lower.iloc[-1]),
            'position': 'above_upper' if current > upper.iloc[-1] else 'below_lower' if current < lower.iloc[-1] else 'within_bands'
        }
    
    def calculate_atr(self, period: int = 14) -> Dict:
        if len(self.df) < period + 1:
            return {}
        high_low = self.df['high'] - self.df['low']
        high_close = np.abs(self.df['high'] - self.df['close'].shift())
        low_close = np.abs(self.df['low'] - self.df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return {'atr': float(atr.iloc[-1])}
    
    def calculate_volume_indicators(self) -> Dict:
        vol = {}
        vol['current'] = int(self.df['volume'].iloc[-1])
        vol['sma20'] = float(self.df['volume'].rolling(window=20).mean().iloc[-1])
        vol['ratio'] = float(vol['current'] / vol['sma20']) if vol['sma20'] > 0 else 0
        vol['spike'] = vol['ratio'] > 1.5
        return vol
    
    def generate_signals(self) -> Dict:
        signals = {'buy': [], 'sell': [], 'neutral': []}
        rsi = self.indicators.get('rsi', {})
        macd = self.indicators.get('macd', {})
        stoch = self.indicators.get('stochastic', {})
        
        if rsi.get('rsi', 50) < 30:
            signals['buy'].append('RSI Oversold')
        if rsi.get('rsi', 50) > 70:
            signals['sell'].append('RSI Overbought')
        if macd.get('trend') == 'bullish':
            signals['buy'].append('MACD Bullish Cross')
        if macd.get('trend') == 'bearish':
            signals['sell'].append('MACD Bearish Cross')
        if stoch.get('signal') == 'oversold':
            signals['buy'].append('Stochastic Oversold')
        if stoch.get('signal') == 'overbought':
            signals['sell'].append('Stochastic Overbought')
            
        return signals


def analyze_stock(df: pd.DataFrame) -> Dict:
    """Analyze stock data and return indicators"""
    if df is None or df.empty:
        return {}
    analyzer = TechnicalAnalyzer(df)
    return analyzer.calculate_all()