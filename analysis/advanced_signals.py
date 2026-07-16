"""Enhanced Advanced Intraday Signal Engine with Additional Indicators"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class AdvancedSignalEngine:
    def __init__(self):
        self.market_context = None
    
    def get_multi_timeframe_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        data = {}
        intervals_to_try = [
            ('5m', '5d'),
            ('15m', '5d'),
            ('30m', '5d'),
            ('1h', '5d'),
            ('1d', '1mo')
        ]
        
        for interval, period in intervals_to_try:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval, auto_adjust=True)
                if df is not None and not df.empty and len(df) > 20:
                    data[interval] = df
            except Exception as e:
                continue
        
        if not data:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period="5d", interval="5m", auto_adjust=True)
                if df is not None and not df.empty and len(df) > 20:
                    data['5m'] = df
            except:
                pass
        
        return data

    def calculate_timeframe_confluence(self, data: Dict[str, pd.DataFrame]) -> Dict:
        scores = {}
        for timeframe, df in data.items():
            if len(df) < 10:
                continue
            ema_9 = df['Close'].ewm(span=9).mean().iloc[-1]
            ema_21 = df['Close'].ewm(span=21).mean().iloc[-1]
            ema_40 = df['Close'].ewm(span=40).mean().iloc[-1]
            current = df['Close'].iloc[-1]
            rsi = self._calculate_rsi(df)
            macd = self._calculate_macd(df)
            score = 0
            if ema_9 > ema_21 > ema_40:
                score += 25
            elif ema_9 < ema_21 < ema_40:
                score -= 25
            if rsi > 50:
                score += 25
            elif rsi < 50:
                score -= 25
            if macd > 0:
                score += 25
            elif macd < 0:
                score -= 25
            if current > ema_9:
                score += 25
            elif current < ema_9:
                score -= 25
            scores[timeframe] = score
        total_score = sum(scores.values())
        max_possible = len(scores) * 100 if scores else 1
        bullish_count = sum(1 for s in scores.values() if s > 0)
        bearish_count = sum(1 for s in scores.values() if s < 0)
        return {
            'total_score': total_score,
            'confluence_pct': (total_score / max_possible * 100) if max_possible > 0 else 0,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'aligned': bullish_count == len(scores) or bearish_count == len(scores),
            'scores': scores
        }

    def detect_patterns(self, df: pd.DataFrame) -> Dict:
        patterns = []
        pattern_score = 0
        if len(df) < 30:
            return {'patterns': [], 'score': 0}
        current = df['Close'].iloc[-1]
        hh_count = sum(1 for i in range(-5, 0) if len(df) > abs(i) + 1 and df['High'].iloc[i] > df['High'].iloc[i-1])
        hl_count = sum(1 for i in range(-5, 0) if len(df) > abs(i) + 1 and df['Low'].iloc[i] > df['Low'].iloc[i-1])
        if hh_count >= 3 and hl_count >= 3:
            patterns.append('HIGHER_HIGHS_LOWS')
            pattern_score += 20
        lh_count = sum(1 for i in range(-5, 0) if len(df) > abs(i) + 1 and df['High'].iloc[i] < df['High'].iloc[i-1])
        ll_count = sum(1 for i in range(-5, 0) if len(df) > abs(i) + 1 and df['Low'].iloc[i] < df['Low'].iloc[i-1])
        if lh_count >= 3 and ll_count >= 3:
            patterns.append('LOWER_HIGHS_LOWS')
            pattern_score -= 20
        rsi = self._calculate_rsi(df)
        price_trend = df['Close'].iloc[-1] - df['Close'].iloc[-10]
        if rsi < 30 and price_trend < 0:
            patterns.append('BULLISH_RSI_DIVERGENCE')
            pattern_score += 25
        elif rsi > 70 and price_trend > 0:
            patterns.append('BEARISH_RSI_DIVERGENCE')
            pattern_score -= 25
        macd = self._calculate_macd(df)
        macd_prev = self._calculate_macd(df.iloc[:-1]) if len(df) > 1 else 0
        if macd > 0 and macd_prev < 0:
            patterns.append('MACD_BULLISH_CROSS')
            pattern_score += 20
        elif macd < 0 and macd_prev > 0:
            patterns.append('MACD_BEARISH_CROSS')
            pattern_score -= 20
        bb_upper, bb_lower = self._calculate_bollinger(df)
        bb_width = (bb_upper - bb_lower) / df['Close'].mean()
        if bb_width < 0.05:
            patterns.append('BB_SQUEEZE')
            pattern_score += 15
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
        vol_current = df['Volume'].iloc[-1]
        if vol_current > vol_avg * 2:
            patterns.append('VOLUME_SPIKE')
            pattern_score += 10 if pattern_score > 0 else -10
        vwap = self._calculate_vwap(df)
        if len(df) > 1:
            if current > vwap and df['Close'].iloc[-2] < vwap:
                patterns.append('VWAP_BULLISH_CROSS')
                pattern_score += 15
            elif current < vwap and df['Close'].iloc[-2] > vwap:
                patterns.append('VWAP_BEARISH_CROSS')
                pattern_score -= 15
        resistance = df['High'].rolling(20).max().iloc[-1]
        support = df['Low'].rolling(20).min().iloc[-1]
        if current > resistance * 0.99:
            patterns.append('RESISTANCE_BREAK')
            pattern_score += 25
        elif current < support * 1.01:
            patterns.append('SUPPORT_BREAK')
            pattern_score -= 25
        ichimoku = self._calculate_ichimoku(df)
        if ichimoku['bullish']:
            patterns.append('ICHIMOKU_BULLISH')
            pattern_score += 15
        elif ichimoku['bearish']:
            patterns.append('ICHIMOKU_BEARISH')
            pattern_score -= 15
        fib_levels = self._calculate_fibonacci(df)
        if fib_levels['near_support']:
            patterns.append('FIB_SUPPORT')
            pattern_score += 10
        if fib_levels['near_resistance']:
            patterns.append('FIB_RESISTANCE')
            pattern_score -= 10
        ema_triple = self._calculate_ema_triple(df)
        if ema_triple['alignment'] == 'BULLISH_STACK':
            patterns.append('EMA_TRIPLE_BULLISH')
            pattern_score += 25
        elif ema_triple['alignment'] == 'BEARISH_STACK':
            patterns.append('EMA_TRIPLE_BEARISH')
            pattern_score -= 25
        for crossover in ema_triple['crossovers']:
            patterns.append(crossover)
            if crossover == 'EMA9_21_BULLISH_CROSS':
                pattern_score += 20
            elif crossover == 'EMA9_21_BEARISH_CROSS':
                pattern_score -= 20
            elif crossover == 'EMA21_40_BULLISH_CROSS':
                pattern_score += 15
            elif crossover == 'EMA21_40_BEARISH_CROSS':
                pattern_score -= 15
        if ema_triple['price_above_ema9']:
            patterns.append('PRICE_ABOVE_EMA9')
            pattern_score += 10
        else:
            patterns.append('PRICE_BELOW_EMA9')
            pattern_score -= 10
        return {'patterns': patterns, 'score': pattern_score}

    def calculate_momentum_matrix(self, df: pd.DataFrame) -> Dict:
        if len(df) < 20:
            return {}
        momentum = {}
        momentum['rsi_14'] = self._calculate_rsi(df)
        momentum['macd'] = self._calculate_macd(df)
        momentum['macd_signal'] = self._calculate_macd_signal(df)
        stoch = self._calculate_stochastic(df)
        momentum['stoch_k'] = stoch['k']
        momentum['stoch_d'] = stoch['d']
        momentum['williams_r'] = self._calculate_williams_r(df)
        momentum['cci'] = self._calculate_cci(df)
        aroon = self._calculate_aroon(df)
        momentum['aroon_up'] = aroon['up']
        momentum['aroon_down'] = aroon['down']
        momentum['mfi'] = self._calculate_mfi(df)
        momentum['roc'] = self._calculate_roc(df)
        momentum['obv'] = self._calculate_obv(df)
        adx = self._calculate_adx(df)
        momentum['adx'] = adx['adx']
        momentum['plus_di'] = adx['plus_di']
        momentum['minus_di'] = adx['minus_di']
        supertrend = self._calculate_supertrend(df)
        momentum['supertrend'] = supertrend['value']
        momentum['supertrend_signal'] = supertrend['signal']
        return momentum

    def analyze(self, symbol: str) -> Dict:
        data = self.get_multi_timeframe_data(symbol)
        if not data:
            return {'error': 'No data available'}
        
        confluence = self.calculate_timeframe_confluence(data)
        primary_df = list(data.values())[0]
        patterns = self.detect_patterns(primary_df)
        momentum = self.calculate_momentum_matrix(primary_df)
        ema_strategy = self._calculate_ema_triple(primary_df)

        total_score = confluence['total_score'] + patterns['score']
        signal = 'HOLD'
        if total_score > 50:
            signal = 'BUY'
        elif total_score < -50:
            signal = 'SELL'
        
        # Calculate volume data
        volume = self._calculate_volume_data(primary_df)
        
        # Calculate market regime
        regime = self.detect_market_regime(primary_df)
        
        # Calculate signal confidence
        confidence = self.calculate_signal_confidence(momentum, patterns, confluence, volume, regime)
        
        return {
            'symbol': symbol,
            'signal': signal,
            'total_score': total_score,
            'confluence': confluence,
            'patterns': patterns,
            'momentum': momentum,
            'ema_strategy': ema_strategy,
            'current_price': primary_df['Close'].iloc[-1],
            'volume': volume,
            'regime': regime,
            'confidence': confidence
        }
    
    def generate_signal(self, symbol: str) -> Dict:
        result = self.analyze(symbol)
        if 'error' in result:
            return result
        
        current_price = result['current_price']
        signal = result['signal']
        
        atr = self._calculate_atr(list(self.get_multi_timeframe_data(symbol).values())[0])
        
        if signal == 'BUY':
            entry = current_price
            stop_loss = current_price - (atr * 1.5)
            target = current_price + (atr * 3)
        elif signal == 'SELL':
            entry = current_price
            stop_loss = current_price + (atr * 1.5)
            target = current_price - (atr * 3)
        else:
            entry = current_price
            stop_loss = current_price - (atr * 1)
            target = current_price + (atr * 2)
        
        result['entry'] = round(entry, 2)
        result['stop_loss'] = round(stop_loss, 2)
        result['target'] = round(target, 2)
        result['risk_reward'] = round(abs(target - entry) / abs(stop_loss - entry), 2) if stop_loss != entry else 0
        
        return result
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.isna().all() else 50.0
    
    def _calculate_macd(self, df: pd.DataFrame) -> float:
        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        return ema12.iloc[-1] - ema26.iloc[-1]
    
    def _calculate_macd_signal(self, df: pd.DataFrame) -> float:
        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        return signal.iloc[-1]
    
    def _calculate_bollinger(self, df: pd.DataFrame, period: int = 20) -> Tuple[float, float]:
        sma = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        return upper.iloc[-1], lower.iloc[-1]
    
    def _calculate_vwap(self, df: pd.DataFrame) -> float:
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        cumulative_tp_vol = (typical_price * df['Volume']).cumsum()
        cumulative_vol = df['Volume'].cumsum()
        return cumulative_tp_vol.iloc[-1] / cumulative_vol.iloc[-1] if cumulative_vol.iloc[-1] > 0 else df['Close'].iloc[-1]
    
    def _calculate_stochastic(self, df: pd.DataFrame, period: int = 14) -> Dict:
        low_min = df['Low'].rolling(window=period).min()
        high_max = df['High'].rolling(window=period).max()
        k = 100 * (df['Close'] - low_min) / (high_max - low_min)
        d = k.rolling(window=3).mean()
        return {'k': k.iloc[-1] if not k.isna().all() else 50.0, 'd': d.iloc[-1] if not d.isna().all() else 50.0}
    
    def _calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> float:
        high_max = df['High'].rolling(window=period).max()
        low_min = df['Low'].rolling(window=period).min()
        wr = -100 * (high_max - df['Close']) / (high_max - low_min)
        return wr.iloc[-1] if not wr.isna().all() else -50.0
    
    def _calculate_cci(self, df: pd.DataFrame, period: int = 20) -> float:
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        sma = typical_price.rolling(window=period).mean()
        mad = (typical_price - sma).abs().rolling(window=period).mean()
        cci = (typical_price - sma) / (0.015 * mad)
        return cci.iloc[-1] if not cci.isna().all() else 0.0
    
    def _calculate_aroon(self, df: pd.DataFrame, period: int = 25) -> Dict:
        """Calculate Aroon indicator - fixed version"""
        aroon_up = []
        aroon_down = []
        
        for i in range(period, len(df)):
            window_high = df['High'].iloc[i-period+1:i+1]
            window_low = df['Low'].iloc[i-period+1:i+1]
            
            # Find days since highest high and lowest low
            days_since_high = period - 1 - window_high.idxmax()
            days_since_low = period - 1 - window_low.idxmin()
            
            aroon_up.append((period - days_since_high) / period * 100)
            aroon_down.append((period - days_since_low) / period * 100)
        
        if len(aroon_up) > 0:
            return {'up': aroon_up[-1], 'down': aroon_down[-1]}
        return {'up': 50.0, 'down': 50.0}
    
    def _calculate_mfi(self, df: pd.DataFrame, period: int = 14) -> float:
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        raw_money_flow = typical_price * df['Volume']
        positive_flow = raw_money_flow.where(typical_price > typical_price.shift(1), 0).rolling(window=period).sum()
        negative_flow = raw_money_flow.where(typical_price < typical_price.shift(1), 0).rolling(window=period).sum()
        mfi = 100 - (100 / (1 + positive_flow / negative_flow.replace(0, np.inf)))
        return mfi.iloc[-1] if not mfi.isna().all() else 50.0
    
    def _calculate_roc(self, df: pd.DataFrame, period: int = 12) -> float:
        roc = (df['Close'] - df['Close'].shift(period)) / df['Close'].shift(period) * 100
        return roc.iloc[-1] if not roc.isna().all() else 0.0
    
    def _calculate_obv(self, df: pd.DataFrame) -> float:
        obv = (np.sign(df['Close'].diff()) * df['Volume']).cumsum()
        return obv.iloc[-1]
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> Dict:
        high_diff = df['High'].diff()
        low_diff = -df['Low'].diff()
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        atr = self._calculate_atr(df)
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.inf)
        adx = dx.rolling(window=period).mean()
        return {'adx': adx.iloc[-1] if not adx.isna().all() else 25.0, 'plus_di': plus_di.iloc[-1] if not plus_di.isna().all() else 25.0, 'minus_di': minus_di.iloc[-1] if not minus_di.isna().all() else 25.0}
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean().iloc[-1] if not tr.isna().all() else 1.0
    
    def _calculate_supertrend(self, df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> Dict:
        atr = self._calculate_atr(df, period)
        hl2 = (df['High'] + df['Low']) / 2
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        supertrend = pd.DataFrame(index=df.index)
        supertrend['close'] = df['Close']
        supertrend['upper'] = upper_band
        supertrend['lower'] = lower_band
        supertrend['trend'] = True
        for i in range(1, len(supertrend)):
            if supertrend['close'].iloc[i] > supertrend['upper'].iloc[i-1]:
                supertrend.loc[supertrend.index[i], 'trend'] = True
            elif supertrend['close'].iloc[i] < supertrend['lower'].iloc[i-1]:
                supertrend.loc[supertrend.index[i], 'trend'] = False
            else:
                supertrend.loc[supertrend.index[i], 'trend'] = supertrend['trend'].iloc[i-1]
        current_trend = supertrend['trend'].iloc[-1]
        return {'value': lower_band.iloc[-1] if current_trend else upper_band.iloc[-1], 'signal': 'BUY' if current_trend else 'SELL'}
    
    def _calculate_ichimoku(self, df: pd.DataFrame) -> Dict:
        nine_period_high = df['High'].rolling(window=9).max()
        nine_period_low = df['Low'].rolling(window=9).min()
        tenkan_sen = (nine_period_high + nine_period_low) / 2
        twenty_six_period_high = df['High'].rolling(window=26).max()
        twenty_six_period_low = df['Low'].rolling(window=26).min()
        kijun_sen = (twenty_six_period_high + twenty_six_period_low) / 2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        fifty_two_period_high = df['High'].rolling(window=52).max()
        fifty_two_period_low = df['Low'].rolling(window=52).min()
        senkou_span_b = ((fifty_two_period_high + fifty_two_period_low) / 2).shift(26)
        current_price = df['Close'].iloc[-1]
        cloud_top = max(senkou_span_a.iloc[-1] if not pd.isna(senkou_span_a.iloc[-1]) else 0, senkou_span_b.iloc[-1] if not pd.isna(senkou_span_b.iloc[-1]) else 0)
        cloud_bottom = min(senkou_span_a.iloc[-1] if not pd.isna(senkou_span_a.iloc[-1]) else current_price, senkou_span_b.iloc[-1] if not pd.isna(senkou_span_b.iloc[-1]) else current_price)
        bullish = current_price > cloud_top and tenkan_sen.iloc[-1] > kijun_sen.iloc[-1]
        bearish = current_price < cloud_bottom and tenkan_sen.iloc[-1] < kijun_sen.iloc[-1]
        return {'bullish': bullish, 'bearish': bearish}
    
    def _calculate_fibonacci(self, df: pd.DataFrame) -> Dict:
        if len(df) < 50:
            return {'near_support': False, 'near_resistance': False}
        high = df['High'].rolling(50).max().iloc[-1]
        low = df['Low'].rolling(50).min().iloc[-1]
        diff = high - low
        levels = {
            '0.236': low + diff * 0.236,
            '0.382': low + diff * 0.382,
            '0.5': low + diff * 0.5,
            '0.618': low + diff * 0.618,
            '0.786': low + diff * 0.786
        }
        current = df['Close'].iloc[-1]
        tolerance = diff * 0.02
        near_support = any(abs(current - levels[l]) < tolerance for l in ['0.236', '0.382', '0.618'])
        near_resistance = any(abs(current - levels[l]) < tolerance for l in ['0.786', '0.5'])
        return {'near_support': near_support, 'near_resistance': near_resistance}
    
    def _calculate_ema_triple(self, df: pd.DataFrame) -> Dict:
        if len(df) < 45:
            return {
                'ema_9': 0.0, 'ema_21': 0.0, 'ema_40': 0.0,
                'alignment': 'MIXED', 'crossovers': [],
                'price_above_ema9': False, 'trend_strength': 0.0
            }
        ema_9 = df['Close'].ewm(span=9).mean()
        ema_21 = df['Close'].ewm(span=21).mean()
        ema_40 = df['Close'].ewm(span=40).mean()
        ema_9_curr = ema_9.iloc[-1]
        ema_21_curr = ema_21.iloc[-1]
        ema_40_curr = ema_40.iloc[-1]
        current_price = df['Close'].iloc[-1]
        crossovers = []
        if ema_9_curr > ema_21_curr and ema_9.iloc[-2] <= ema_21.iloc[-2]:
            crossovers.append('EMA9_21_BULLISH_CROSS')
        elif ema_9_curr < ema_21_curr and ema_9.iloc[-2] >= ema_21.iloc[-2]:
            crossovers.append('EMA9_21_BEARISH_CROSS')
        if ema_21_curr > ema_40_curr and ema_21.iloc[-2] <= ema_40.iloc[-2]:
            crossovers.append('EMA21_40_BULLISH_CROSS')
        elif ema_21_curr < ema_40_curr and ema_21.iloc[-2] >= ema_40.iloc[-2]:
            crossovers.append('EMA21_40_BEARISH_CROSS')
        if ema_9_curr > ema_21_curr > ema_40_curr:
            alignment = 'BULLISH_STACK'
        elif ema_9_curr < ema_21_curr < ema_40_curr:
            alignment = 'BEARISH_STACK'
        else:
            alignment = 'MIXED'
        price_above_ema9 = current_price > ema_9_curr
        price_range = df['Close'].max() - df['Close'].min()
        ema_spread = abs(ema_9_curr - ema_40_curr)
        trend_strength = (ema_spread / price_range * 100) if price_range > 0 else 0.0
        return {
            'ema_9': ema_9_curr, 'ema_21': ema_21_curr, 'ema_40': ema_40_curr,
            'alignment': alignment, 'crossovers': crossovers,
            'price_above_ema9': price_above_ema9, 'trend_strength': trend_strength
        }
    
    def _calculate_volume_data(self, df: pd.DataFrame) -> Dict:
        """Calculate volume analysis data"""
        if len(df) < 20:
            return {}
        
        current_volume = df['Volume'].iloc[-1]
        avg_volume = df['Volume'].rolling(20).mean().iloc[-1]
        vol_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Volume surge detection
        volume_surge = current_volume > avg_volume * 1.5
        
        # VWAP for volume analysis
        vwap = self._calculate_vwap(df)
        current_price = df['Close'].iloc[-1]
        above_vwap = current_price > vwap
        
        # Volume trend (last 5 candles vs previous 5)
        vol_current_5 = df['Volume'].iloc[-5:].mean()
        vol_prev_5 = df['Volume'].iloc[-10:-5].mean() if len(df) >= 10 else avg_volume
        vol_trend = (vol_current_5 - vol_prev_5) / vol_prev_5 * 100 if vol_prev_5 > 0 else 0
        
        return {
            'current_volume': int(current_volume),
            'avg_volume': int(avg_volume),
            'vol_ratio': round(vol_ratio, 2),
            'volume_surge': volume_surge,
            'above_vwap': above_vwap,
            'vol_trend_pct': round(vol_trend, 1)
        }
    
    def detect_market_regime(self, df: pd.DataFrame) -> Dict:
        """Detect if market is trending or ranging"""
        if len(df) < 50:
            return {'regime': 'UNKNOWN', 'strength': 0}
        
        # Calculate ADX for trend strength
        adx_data = self._calculate_adx(df)
        adx = adx_data['adx']
        
        # Calculate Bollinger Band width for range detection
        bb_upper, bb_lower = self._calculate_bollinger(df)
        bb_width = (bb_upper - bb_lower) / df['Close'].rolling(20).mean().iloc[-1]
        
        # Determine regime
        if adx > 25:
            regime = 'TRENDING'
            strength = min(adx, 100)
        else:
            regime = 'RANGING'
            strength = 100 - adx
        
        # Check for strong trend
        ema_9 = df['Close'].ewm(span=9).mean()
        ema_21 = df['Close'].ewm(span=21).mean()
        ema_slope = (ema_9.iloc[-1] - ema_9.iloc[-20]) / ema_9.iloc[-20] * 100 if len(df) >= 20 else 0
        
        return {
            'regime': regime,
            'strength': strength,
            'adx': adx,
            'bb_width': bb_width,
            'trend_slope': ema_slope,
            'direction': 'BULLISH' if ema_slope > 0.5 else 'BEARISH' if ema_slope < -0.5 else 'NEUTRAL'
        }
    
    def calculate_signal_confidence(self, momentum: Dict, patterns: Dict, confluence: Dict, volume: Dict, regime: Dict) -> Dict:
        """Calculate confidence score for the signal"""
        confidence_factors = []
        
        # 1. RSI confirmation (not overbought/oversold for entries)
        rsi = momentum.get('rsi_14', 50)
        if 40 <= rsi <= 60:
            confidence_factors.append(1.0)  # Neutral zone - good entry
        elif rsi < 30:
            confidence_factors.append(0.8)  # Oversold - potential reversal
        elif rsi > 70:
            confidence_factors.append(0.8)  # Overbought - potential reversal
        else:
            confidence_factors.append(0.5)
        
        # 2. MACD confirmation
        macd = momentum.get('macd', 0)
        macd_signal = momentum.get('macd_signal', 0)
        if macd > macd_signal:
            confidence_factors.append(1.0)
        else:
            confidence_factors.append(0.5)
        
        # 3. Volume confirmation
        vol_ratio = volume.get('vol_ratio', 1.0)
        if vol_ratio > 1.2:
            confidence_factors.append(1.0)  # Good volume
        elif vol_ratio > 0.8:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.4)
        
        # 4. ADX trend strength
        adx = momentum.get('adx', 25)
        if adx > 25:
            confidence_factors.append(1.0)  # Strong trend
        else:
            confidence_factors.append(0.6)  # Weak trend
        
        # 5. Timeframe confluence
        confluence_pct = confluence.get('confluence_pct', 0)
        if confluence_pct > 75:
            confidence_factors.append(1.0)
        elif confluence_pct > 50:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.5)
        
        # 6. Pattern quality
        pattern_score = patterns.get('score', 0)
        if abs(pattern_score) > 50:
            confidence_factors.append(1.0)
        elif abs(pattern_score) > 25:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.5)
        
        # Calculate overall confidence
        avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        
        # Adjust for market regime
        if regime['regime'] == 'TRENDING' and regime['strength'] > 40:
            regime_multiplier = 1.2  # Better signals in trending markets
        elif regime['regime'] == 'RANGING':
            regime_multiplier = 0.8  # Lower confidence in ranging markets
        else:
            regime_multiplier = 1.0
        
        final_confidence = min(avg_confidence * regime_multiplier, 1.0)
        
        # Determine confidence level
        if final_confidence >= 0.8:
            level = 'HIGH'
        elif final_confidence >= 0.6:
            level = 'MEDIUM'
        else:
            level = 'LOW'
        
        return {
            'confidence': round(final_confidence * 100, 1),
            'level': level,
            'factors': {
                'rsi_zone': confidence_factors[0],
                'macd_confirmation': confidence_factors[1],
                'volume_confirmed': confidence_factors[2],
                'trend_strength': confidence_factors[3],
                'timeframe_confluence': confidence_factors[4],
                'pattern_quality': confidence_factors[5]
            },
            'regime_multiplier': regime_multiplier
        }
