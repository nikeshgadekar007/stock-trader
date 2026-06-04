"""Advanced Intraday Signal Engine"""
import yfinance as yf
import pandas as pd
from typing import Dict

class AdvancedSignalEngine:
    def get_multi_timeframe_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        data = {}
        for interval in ['1m', '5m', '15m', '1h', '1d']:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period="5d" if interval == '1d' else "2d", interval=interval)
                if not df.empty:
                    data[interval] = df
            except Exception:
                continue
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
        bullish_count = sum([momentum['rsi_14'] > 50, momentum['macd'] > momentum['macd_signal'], momentum['stoch_k'] > momentum['stoch_d'], momentum['williams_r'] > -50, momentum['cci'] > 0, momentum['aroon_up'] > momentum['aroon_down']])
        bearish_count = 6 - bullish_count
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
        confluence_score = confluence['confluence_pct'] * 0.25
        pattern_score = patterns['score'] * 0.25
        momentum_score = momentum.get('momentum_score', 0) * 0.25
        volume_score = volume.get('vol_ratio', 1) * 15 if volume.get('above_vwap', False) else -volume.get('vol_ratio', 1) * 15
        total_score = confluence_score + pattern_score + momentum_score + volume_score
        action = "BUY" if total_score > 30 else "SELL" if total_score < -30 else "HOLD"
        if action == "BUY":
            entry = current
            stop = current * 0.995
            target1 = current * 1.01
            target2 = current * 1.02
        elif action == "SELL":
            entry = current
            stop = current * 1.005
            target1 = current * 0.99
            target2 = current * 0.98
        else:
            entry = current
            stop = current
            target1 = current
            target2 = current
        return {'symbol': symbol, 'action': action, 'confidence': abs(total_score), 'score': total_score, 'entry': entry, 'stop': stop, 'target1': target1, 'target2': target2, 'current_price': current, 'confluence': confluence, 'patterns': patterns, 'momentum': momentum, 'volume': volume}

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
