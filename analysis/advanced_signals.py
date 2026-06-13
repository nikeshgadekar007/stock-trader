"""Advanced Intraday Signal Engine"""
import yfinance as yf
import pandas as pd
from typing import Dict

class AdvancedSignalEngine:
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
        
        # If no data fetched, try a simpler approach
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
            current = df['Close'].iloc[-1]
            rsi = self._calculate_rsi(df)
            macd = self._calculate_macd(df)
            score = 0
            if current > ema_9 > ema_21:
                score += 33
            elif current < ema_9 < ema_21:
                score -= 33
            if rsi > 50:
                score += 33
            elif rsi < 50:
                score -= 33
            if macd > 0:
                score += 34
            elif macd < 0:
                score -= 34
            scores[timeframe] = score
        total_score = sum(scores.values())
        max_possible = len(scores) * 100 if scores else 1
        bullish_count = sum(1 for s in scores.values() if s > 0)
        bearish_count = sum(1 for s in scores.values() if s < 0)
        return {'total_score': total_score, 'confluence_pct': (total_score / max_possible * 100) if max_possible > 0 else 0, 'bullish_count': bullish_count, 'bearish_count': bearish_count, 'aligned': bullish_count == len(scores) or bearish_count == len(scores), 'scores': scores}

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
        momentum['supertrend_dir'] = supertrend['direction']
        
        bullish_count = sum([
            momentum['rsi_14'] > 50,
            momentum['macd'] > momentum['macd_signal'],
            momentum['stoch_k'] > momentum['stoch_d'],
            momentum['williams_r'] > -50,
            momentum['cci'] > 0,
            momentum['aroon_up'] > momentum['aroon_down'],
            momentum['mfi'] > 50,
            momentum['roc'] > 0,
            momentum['plus_di'] > momentum['minus_di'],
            momentum['supertrend_dir'] > 0
        ])
        bearish_count = 10 - bullish_count
        total = bullish_count + bearish_count
        momentum_score = ((bullish_count - bearish_count) / total * 100) if total > 0 else 0
        direction = 'BULLISH' if momentum_score > 20 else 'BEARISH' if momentum_score < -20 else 'NEUTRAL'
        return {'indicators': momentum, 'bullish_count': bullish_count, 'bearish_count': bearish_count, 'momentum_score': momentum_score, 'direction': direction}

    def analyze_volume(self, df: pd.DataFrame) -> Dict:
        if len(df) < 20:
            return {}
        volume = df['Volume']
        current_vol = volume.iloc[-1]
        avg_vol = volume.rolling(20).mean().iloc[-1]
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
        current = df['Close'].iloc[-1]
        vwap = self._calculate_vwap(df)
        return {'current_volume': current_vol, 'avg_volume': avg_vol, 'vol_ratio': vol_ratio, 'above_vwap': current > vwap, 'volume_surge': vol_ratio > 2}

    def generate_signal(self, symbol: str) -> Dict:
        data = self.get_multi_timeframe_data(symbol)
        if not data:
            return {'error': 'No data available'}
        df_5m = data.get('5m', data.get('15m', list(data.values())[0]))
        confluence = self.calculate_timeframe_confluence(data)
        patterns = self.detect_patterns(df_5m)
        momentum = self.calculate_momentum_matrix(df_5m)
        volume = self.analyze_volume(df_5m)
        current = df_5m['Close'].iloc[-1]
        
        # === IMPROVED CONFIDENCE CALCULATION ===
        
        # 1. Normalize each component to 0-100 scale
        confluence_norm = (confluence['confluence_pct'] + 100) / 2  # -100 to 100 -> 0 to 100
        
        # 2. Pattern strength (normalize pattern score)
        pattern_norm = min(100, max(0, patterns['score'] + 50))  # -50 to 100 -> 0 to 100
        
        # 3. Momentum score already normalized -100 to 100
        momentum_norm = (momentum.get('momentum_score', 0) + 100) / 2
        
        # 4. Volume confirmation score
        vol_ratio = volume.get('vol_ratio', 1)
        above_vwap = volume.get('above_vwap', False)
        vol_direction = 1 if above_vwap else -1
        vol_norm = min(100, vol_ratio * 30) * (0.5 + 0.5 * vol_direction)  # 0-100 with direction
        
        # 5. Calculate weighted components
        weights = {
            'confluence': 0.30,      # Increased - multi-timeframe alignment is key
            'patterns': 0.25,        # Pattern recognition is strong signal
            'momentum': 0.25,        # Momentum indicators
            'volume': 0.20           # Volume confirmation
        }
        
        # 6. Calculate raw weighted score
        raw_score = (
            confluence_norm * weights['confluence'] +
            pattern_norm * weights['patterns'] +
            momentum_norm * weights['momentum'] +
            vol_norm * weights['volume']
        )
        
        # 7. Apply volatility adjustment
        volatility = self._calculate_volatility(df_5m)
        vol_adjustment = 1.0 - (volatility * 0.1)  # Reduce confidence in high volatility
        
        # 8. Apply alignment bonus (all timeframes aligned)
        alignment_bonus = 1.15 if confluence.get('aligned', False) else 1.0
        
        # 9. Apply pattern count bonus
        pattern_count = len(patterns['patterns'])
        pattern_bonus = 1.0 + (pattern_count * 0.02)  # +2% per pattern detected
        
        # 10. Calculate final confidence
        final_score = raw_score * vol_adjustment * alignment_bonus * pattern_bonus
        confidence = min(100, max(0, final_score))
        
        # 11. Determine action with BALANCED thresholds
        # Relaxed: Require most timeframes aligned AND good confidence
        most_aligned = confluence.get('bullish_count', 0) >= 2  # At least 2 timeframes
        good_momentum = momentum.get('momentum_score', 0) > 10
        any_pattern = len(patterns['patterns']) >= 1
        
        if confidence > 60 and most_aligned and good_momentum and any_pattern and raw_score > 50:
            action = "BUY"
        elif confidence > 60 and most_aligned and momentum.get('momentum_score', 0) < -10 and any_pattern and raw_score < 50:
            action = "SELL"
        else:
            action = "HOLD"
        
        # 12. Calculate adaptive stop/target based on ATR (WIDER stops for safety)
        atr = self._calculate_atr(df_5m)
        if action == "BUY":
            entry = current
            stop = current - (atr * 2.0)  # 2.0 ATR stop (wider)
            target1 = current + (atr * 2.0)  # 2 ATR target (tighter)
            target2 = current + (atr * 3.0)  # 3 ATR target
        elif action == "SELL":
            entry = current
            stop = current + (atr * 2.0)
            target1 = current - (atr * 2.0)
            target2 = current - (atr * 3.0)
        else:
            entry = current
            stop = current
            target1 = current
            target2 = current
        
        return {
            'symbol': symbol, 
            'action': action, 
            'confidence': confidence,
            'raw_score': raw_score,
            'score': final_score,
            'entry': entry, 
            'stop': stop, 
            'target1': target1, 
            'target2': target2, 
            'current_price': current,
            'atr': atr,
            'volatility': volatility,
            'confluence': confluence, 
            'patterns': patterns, 
            'momentum': momentum, 
            'volume': volume,
            'component_scores': {
                'confluence': confluence_norm,
                'patterns': pattern_norm,
                'momentum': momentum_norm,
                'volume': vol_norm
            }
        }
    
    def _calculate_volatility(self, df: pd.DataFrame, period: int = 20) -> float:
        """Calculate historical volatility"""
        returns = df['Close'].pct_change().dropna()
        if len(returns) < period:
            return 0.02
        volatility = returns.tail(period).std()
        return volatility if not pd.isna(volatility) else 0.02
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else (close.iloc[-1] * 0.01)

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50

    def _calculate_macd(self, df: pd.DataFrame) -> float:
        ema_12 = df['Close'].ewm(span=12).mean()
        ema_26 = df['Close'].ewm(span=26).mean()
        return ema_12.iloc[-1] - ema_26.iloc[-1]

    def _calculate_macd_signal(self, df: pd.DataFrame) -> float:
        ema_12 = df['Close'].ewm(span=12).mean()
        ema_26 = df['Close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        return macd.ewm(span=9).mean().iloc[-1]

    def _calculate_bollinger(self, df: pd.DataFrame, period: int = 20) -> tuple:
        mid = df['Close'].rolling(period).mean().iloc[-1]
        std = df['Close'].rolling(period).std().iloc[-1]
        return mid + (std * 2), mid - (std * 2)

    def _calculate_vwap(self, df: pd.DataFrame) -> float:
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        cumulative_tp = (typical_price * df['Volume']).cumsum()
        cumulative_vol = df['Volume'].cumsum()
        return (cumulative_tp / cumulative_vol).iloc[-1] if cumulative_vol.iloc[-1] > 0 else df['Close'].iloc[-1]

    def _calculate_stochastic(self, df: pd.DataFrame, period: int = 14) -> dict:
        low_min = df['Low'].rolling(period).min().iloc[-1]
        high_max = df['High'].rolling(period).max().iloc[-1]
        k = 100 * (df['Close'].iloc[-1] - low_min) / (high_max - low_min) if high_max != low_min else 50
        return {'k': k, 'd': k}

    def _calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> float:
        high_max = df['High'].rolling(period).max().iloc[-1]
        low_min = df['Low'].rolling(period).min().iloc[-1]
        wr = -100 * (high_max - df['Close'].iloc[-1]) / (high_max - low_min) if high_max != low_min else -50
        return wr

    def _calculate_cci(self, df: pd.DataFrame, period: int = 20) -> float:
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        sma = typical_price.rolling(period).mean().iloc[-1]
        mean_dev = typical_price.rolling(period).apply(lambda x: abs(x - x.mean()).mean(), raw=True).iloc[-1]
        cci = (typical_price.iloc[-1] - sma) / (0.015 * mean_dev) if mean_dev != 0 else 0
        return cci

    def _calculate_aroon(self, df: pd.DataFrame, period: int = 25) -> dict:
        aroon_up = 100 * (period - (period - df['High'].rolling(period).apply(lambda x: period - x[::-1].argmax(), raw=True).iloc[-1])) / period
        aroon_down = 100 * (period - (period - df['Low'].rolling(period).apply(lambda x: period - x[::-1].argmin(), raw=True).iloc[-1])) / period
        return {'up': aroon_up, 'down': aroon_down}
    
    def _calculate_obv(self, df: pd.DataFrame) -> float:
        """On Balance Volume"""
        close_diff = df['Close'].diff()
        obv = (df['Volume'] * close_diff.apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)).cumsum()
        return obv.iloc[-1]
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> dict:
        """Average Directional Index"""
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(period).mean()
        
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return {'adx': adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0, 'plus_di': plus_di.iloc[-1], 'minus_di': minus_di.iloc[-1]}
    
    def _calculate_mfi(self, df: pd.DataFrame, period: int = 14) -> float:
        """Money Flow Index"""
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        money_flow = typical_price * df['Volume']
        
        positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(period).sum()
        negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(period).sum()
        
        mfi = 100 - (100 / (1 + (positive_flow / negative_flow)))
        return mfi.iloc[-1] if not pd.isna(mfi.iloc[-1]) else 50
    
    def _calculate_roc(self, df: pd.DataFrame, period: int = 12) -> float:
        """Rate of Change"""
        roc = ((df['Close'] - df['Close'].shift(period)) / df['Close'].shift(period)) * 100
        return roc.iloc[-1] if not pd.isna(roc.iloc[-1]) else 0
    
    def _calculate_supertrend(self, df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> dict:
        """SuperTrend Indicator"""
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        hl2 = (high + low) / 2
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        supertrend = [close.iloc[0]]
        direction = [1]
        
        for i in range(1, len(close)):
            if close.iloc[i] > upper_band.iloc[i]:
                direction.append(1)
            elif close.iloc[i] < lower_band.iloc[i]:
                direction.append(-1)
            else:
                direction.append(direction[-1])
            
            if direction[-1] == 1:
                supertrend.append(lower_band.iloc[i])
            else:
                supertrend.append(upper_band.iloc[i])
        
        return {'value': supertrend[-1], 'direction': direction[-1]}
    
    def _calculate_pivot_points(self, df: pd.DataFrame) -> dict:
        """Calculate Pivot Points and S/R levels"""
        high = df['High'].iloc[-1]
        low = df['Low'].iloc[-1]
        close = df['Close'].iloc[-1]
        
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)
        
        return {'pivot': pivot, 'r1': r1, 'r2': r2, 'r3': r3, 's1': s1, 's2': s2, 's3': s3}
    
    def _calculate_keltner_channels(self, df: pd.DataFrame, period: int = 20, multiplier: float = 2.0) -> dict:
        """Keltner Channels"""
        middle = df['Close'].ewm(span=period).mean()
        
        tr1 = df['High'] - df['Low']
        tr2 = abs(df['High'] - df['Close'].shift())
        tr3 = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        upper = middle + (multiplier * atr)
        lower = middle - (multiplier * atr)
        
        return {'upper': upper.iloc[-1], 'middle': middle.iloc[-1], 'lower': lower.iloc[-1]}
    
    def _calculate_parabolic_sar(self, df: pd.DataFrame, af: float = 0.02, max_af: float = 0.2) -> dict:
        """Parabolic SAR"""
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        sar = [low.iloc[0]]
        trend = [1]
        af_current = af
        ep = [high.iloc[0]]
        
        for i in range(1, len(close)):
            if trend[-1] == 1:
                sar.append(sar[-1] + af_current * (ep[-1] - sar[-1]))
                if low.iloc[i] < sar[-1]:
                    trend.append(-1)
                    sar.append(high.iloc[i])
                    ep.append(low.iloc[i])
                    af_current = af
                else:
                    if high.iloc[i] > ep[-1]:
                        ep.append(high.iloc[i])
                        af_current = min(af_current + af, max_af)
                    else:
                        ep.append(ep[-1])
            else:
                sar.append(sar[-1] - af_current * (sar[-1] - ep[-1]))
                if high.iloc[i] > sar[-1]:
                    trend.append(1)
                    sar.append(low.iloc[i])
                    ep.append(high.iloc[i])
                    af_current = af
                else:
                    if low.iloc[i] < ep[-1]:
                        ep.append(low.iloc[i])
                        af_current = min(af_current + af, max_af)
                    else:
                        ep.append(ep[-1])
        
        return {'value': sar[-1], 'direction': trend[-1]}
