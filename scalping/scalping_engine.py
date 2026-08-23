"""
Intraday Scalping Suite - Advanced Trading Tools
Real-time 5-min charts, Level 2, Volume Spikes, Trade Execution
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

class ScalpingEngine:
    """Advanced intraday scalping engine with real-time data"""
    
    def __init__(self):
        self.cache = {}
        self.last_update = {}
        
    def get_realtime_quote(self, symbol: str) -> Dict:
        """Get real-time quote with bid/ask"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'bid': info.get('bid', 0),
                'ask': info.get('ask', 0),
                'bid_size': info.get('bidSize', 0),
                'ask_size': info.get('askSize', 0),
                'last': info.get('regularMarketPrice', 0),
                'volume': info.get('regularMarketVolume', 0),
                'change': info.get('regularMarketChange', 0),
                'change_pct': info.get('regularMarketChangePercent', 0),
                'high': info.get('regularMarketDayHigh', 0),
                'low': info.get('regularMarketDayLow', 0),
                'open': info.get('regularMarketOpen', 0),
                'prev_close': info.get('previousClose', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_5min_chart(self, symbol: str, bars: int = 100) -> pd.DataFrame:
        """Get 5-minute candlestick data"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get 5-minute data for today
            df = ticker.history(period="1d", interval="5m", prepost=True)
            
            if df.empty or len(df) < 10:
                # Fallback to 15-min compressed
                df = ticker.history(period="2d", interval="15m")
                if len(df) > 0:
                    # Resample to 5-min
                    df = df.resample('5T').agg({
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }).dropna()
            
            return df.tail(bars)
        except Exception as e:
            return pd.DataFrame()
    
    def calculate_scalping_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate indicators for scalping"""
        if df.empty:
            return {}
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # EMA 9 and 21
        ema9 = close.ewm(span=9).mean()
        ema21 = close.ewm(span=21).mean()
        
        # VWAP (Volume Weighted Average Price)
        typical_price = (high + low + close) / 3
        cumulative_tp_vol = (typical_price * volume).cumsum()
        cumulative_vol = volume.cumsum()
        vwap = cumulative_tp_vol / cumulative_vol
        
        # RSI (fast)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(7).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD (fast)
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        
        # Bollinger Bands (fast - 10 period)
        bb_mid = close.rolling(10).mean()
        bb_std = close.rolling(10).std()
        bb_upper = bb_mid + (bb_std * 2)
        bb_lower = bb_mid - (bb_std * 2)
        
        # Volume SMA
        vol_sma = volume.rolling(20).mean()
        vol_ratio = volume / vol_sma
        
        # Support/Resistance levels
        pivot = (high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3
        r1 = 2 * pivot - low.iloc[-1]
        s1 = 2 * pivot - high.iloc[-1]
        r2 = pivot + (high.iloc[-1] - low.iloc[-1])
        s2 = pivot - (high.iloc[-1] - low.iloc[-1])
        
        return {
            'ema9': ema9.iloc[-1] if len(ema9) > 0 else 0,
            'ema21': ema21.iloc[-1] if len(ema21) > 0 else 0,
            'vwap': vwap.iloc[-1] if len(vwap) > 0 else close.iloc[-1],
            'rsi': rsi.iloc[-1] if len(rsi) > 0 else 50,
            'macd': macd.iloc[-1] if len(macd) > 0 else 0,
            'macd_signal': signal.iloc[-1] if len(signal) > 0 else 0,
            'bb_upper': bb_upper.iloc[-1] if len(bb_upper) > 0 else 0,
            'bb_lower': bb_lower.iloc[-1] if len(bb_lower) > 0 else 0,
            'vol_ratio': vol_ratio.iloc[-1] if len(vol_ratio) > 0 else 1,
            'avg_volume': vol_sma.iloc[-1] if len(vol_sma) > 0 else 0,
            'pivot': pivot,
            'r1': r1, 'r2': r2,
            's1': s1, 's2': s2,
            'last_price': close.iloc[-1],
            'last_volume': volume.iloc[-1]
        }
    
    def generate_scalp_signal(self, quote: Dict, indicators: Dict) -> Dict:
        """Generate scalping buy/sell signal"""
        if not indicators:
            return {'action': 'HOLD', 'confidence': 0, 'reason': 'No data'}
        
        signals = []
        confidence = 0
        
        price = quote.get('last', indicators.get('last_price', 0))
        vwap = indicators.get('vwap', price)
        ema9 = indicators.get('ema9', price)
        ema21 = indicators.get('ema21', price)
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        vol_ratio = indicators.get('vol_ratio', 1)
        
        # Signal 1: EMA Crossover
        if ema9 > ema21:
            signals.append('BULLISH_EMA_CROSS')
            confidence += 20
        elif ema9 < ema21:
            signals.append('BEARISH_EMA_CROSS')
            confidence -= 20
        
        # Signal 2: Price vs VWAP
        if price > vwap:
            signals.append('ABOVE_VWAP')
            confidence += 15
        else:
            signals.append('BELOW_VWAP')
            confidence -= 15
        
        # Signal 3: RSI
        if rsi < 30:
            signals.append('RSI_OVERSOLD')
            confidence += 15
        elif rsi > 70:
            signals.append('RSI_OVERBOUGHT')
            confidence -= 15
        
        # Signal 4: MACD
        if macd > macd_signal:
            signals.append('MACD_BULLISH')
            confidence += 15
        else:
            signals.append('MACD_BEARISH')
            confidence -= 15
        
        # Signal 5: Volume spike
        if vol_ratio > 3:
            signals.append('VOLUME_SPIKE')
            confidence += 10 if confidence > 0 else -10
        
        # Signal 6: Bid/Ask spread
        bid = quote.get('bid', price)
        ask = quote.get('ask', price)
        spread = (ask - bid) / price * 100
        if spread < 0.05:
            signals.append('TIGHT_SPREAD')
            confidence += 10
        elif spread > 0.2:
            signals.append('WIDE_SPREAD')
            confidence -= 10
        
        # Determine action
        confidence = max(0, min(100, confidence + 50))
        
        if confidence >= 70:
            action = "BUY"
        elif confidence <= 30:
            action = "SELL"
        else:
            action = "HOLD"
        
        # Calculate entry, stop, target
        spread_pct = 0.001  # 0.1% spread
        
        if action == "BUY":
            entry = quote.get('ask', price)
            stop = entry * (1 - 0.005)  # 0.5% stop
            target = entry * (1 + 0.01)  # 1% target
        elif action == "SELL":
            entry = quote.get('bid', price)
            stop = entry * (1 + 0.005)  # 0.5% stop
            target = entry * (1 - 0.01)  # 1% target
        else:
            entry = price
            stop = price
            target = price
        
        return {
            'action': action,
            'confidence': confidence,
            'signals': signals,
            'entry': entry,
            'stop': stop,
            'target': target,
            'risk_reward': abs(target - entry) / abs(entry - stop) if entry != stop else 0,
            'reason': f"Based on {len(signals)} indicators"
        }
    
    def detect_volume_spike(self, df: pd.DataFrame) -> Dict:
        """Detect unusual volume activity"""
        if df.empty or len(df) < 20:
            return {'spike': False, 'ratio': 1}
        
        volume = df['Volume']
        avg_vol = volume.rolling(20).mean().iloc[-1]
        current_vol = volume.iloc[-1]
        
        ratio = current_vol / avg_vol if avg_vol > 0 else 1
        
        return {
            'spike': ratio > 3,
            'ratio': ratio,
            'current_volume': current_vol,
            'avg_volume': avg_vol,
            'alert': f"Volume {ratio:.1f}x average" if ratio > 2 else None
        }
    
    def get_level2_proxy(self, symbol: str) -> Dict:
        """Get Level 2 proxy data (simulated order book)"""
        quote = self.get_realtime_quote(symbol)
        if 'error' in quote:
            return {'error': quote['error']}
        
        price = quote.get('last', 0)
        bid = quote.get('bid', price)
        ask = quote.get('ask', price)
        
        # Simulate order book levels
        bid_levels = []
        ask_levels = []
        
        for i in range(10):
            offset = (i + 1) * 0.01 * price
            bid_levels.append({
                'price': round(bid - offset, 2),
                'size': int(np.random.uniform(100, 1000)),
                'orders': int(np.random.uniform(1, 10))
            })
            ask_levels.append({
                'price': round(ask + offset, 2),
                'size': int(np.random.uniform(100, 1000)),
                'orders': int(np.random.uniform(1, 10))
            })
        
        # Calculate market depth
        total_bid = sum(l['size'] for l in bid_levels)
        total_ask = sum(l['size'] for l in ask_levels)
        
        # Detect large orders (walls)
        walls = []
        for level in bid_levels + ask_levels:
            if level['size'] > 500:
                walls.append(level)
        
        return {
            'bid_levels': bid_levels,
            'ask_levels': ask_levels,
            'total_bid': total_bid,
            'total_ask': total_ask,
            'imbalance': (total_bid - total_ask) / (total_bid + total_ask) * 100 if total_bid + total_ask > 0 else 0,
            'walls': walls,
            'spread': round(ask - bid, 4),
            'spread_pct': round((ask - bid) / price * 100, 4) if price > 0 else 0
        }
    
    def analyze_momentum(self, df: pd.DataFrame) -> Dict:
        """Analyze momentum for scalping"""
        if df.empty or len(df) < 10:
            return {}
        
        close = df['Close']
        volume = df['Volume']
        
        # Recent price change
        price_change = close.iloc[-1] - close.iloc[-5]
        price_change_pct = (price_change / close.iloc[-5]) * 100 if len(close) >= 5 else 0
        
        # Volume trend
        vol_change = volume.iloc[-1] - volume.iloc[-5]
        vol_change_pct = (vol_change / volume.iloc[-5]) * 100 if len(volume) >= 5 and volume.iloc[-5] > 0 else 0
        
        # Momentum score
        momentum = 0
        if price_change_pct > 0.5:
            momentum += 30
        elif price_change_pct < -0.5:
            momentum -= 30
        
        if vol_change_pct > 50:
            momentum += 20 if price_change_pct > 0 else -20
        
        # Recent candle analysis
        candles = []
        for i in range(-5, 0):
            if len(df) > abs(i):
                candle = df.iloc[i]
                body = candle['Close'] - candle['Open']
                upper_wick = candle['High'] - max(candle['Open'], candle['Close'])
                lower_wick = min(candle['Open'], candle['Close']) - candle['Low']
                
                if body > 0:
                    candles.append('BULLISH')
                else:
                    candles.append('BEARISH')
        
        bullish_count = candles.count('BULLISH')
        bearish_count = candles.count('BEARISH')
        
        if bullish_count > bearish_count:
            momentum += 20
        elif bearish_count > bullish_count:
            momentum -= 20
        
        return {
            'momentum': momentum,
            'price_change_5min': round(price_change_pct, 3),
            'volume_change_5min': round(vol_change_pct, 1),
            'candles': candles,
            'direction': 'BULLISH' if momentum > 20 else 'BEARISH' if momentum < -20 else 'NEUTRAL'
        }


# Global instance
scalping_engine = ScalpingEngine()
