"""
Pre-Market Institutional Engine -- 5 Live Pre-Market Layers
Gap, VWAP, Volume, Range Break, News Sentiment
Designed for 4:00-9:30 AM ET pre-market trading

Accuracy filters (Tier 1):
  A. Liquidity discount (volume < 10K -> scale toward 5, < 5K -> heavily discounted)
  B. Spread filter (>0.5% spread -> cap at 5, >1% -> mark TOO_ILLIQUID)
  C. Time-of-day multiplier (4-6AM x0.6, 6-8AM x0.85, 8-9:30AM x1.1)
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, time, timezone, timedelta
import warnings
warnings.filterwarnings('ignore')


class PreMarketEngine:
    """5-layer pre-market institutional signal engine with Tier 1 accuracy filters."""

    @staticmethod
    def _get_et_time():
        """Get current Eastern Time (handles DST)."""
        try:
            utc = datetime.now(timezone.utc)
            month = utc.month
            offset = timedelta(hours=-4) if 3 <= month <= 10 else timedelta(hours=-5)
            et = utc.astimezone(timezone(offset))
            return et.time()
        except Exception:
            return None

    @staticmethod
    def _time_of_day_multiplier():
        """Tier 1C: time-of-day confidence multiplier.
        4-6 AM: x0.6 (very low participation), 6-8 AM: x0.85 (building up),
        8-9:30 AM: x1.1 (approaching open, more reliable).
        """
        t = PreMarketEngine._get_et_time()
        if t is None:
            return 1.0
        if t < time(6, 0):
            return 0.6
        elif t < time(8, 0):
            return 0.85
        elif t <= time(9, 30):
            return 1.1
        return 0.85

    @staticmethod
    def _get_spread(symbol):
        """Tier 1B: get bid/ask spread for the symbol. Returns (spread_pct, too_wide, too_loose)."""
        try:
            t = yf.Ticker(symbol)
            info = t.info or {}
            bid = info.get('bid', 0)
            ask = info.get('ask', 0)
            if bid and ask and bid > 0:
                mid = (bid + ask) / 2
                spread_pct = ((ask - bid) / mid) * 100 if mid else 0
                return round(spread_pct, 3), spread_pct > 1.0, spread_pct > 0.5
            return 0.0, False, False
        except Exception:
            return 0.0, False, False
    @staticmethod
    def _get_premarket_bars(symbol, lookback_days=5):
        """Fetch today pre-market + previous regular bars."""
        try:
            t = yf.Ticker(symbol)
            df = t.history(period=f"{lookback_days}d", interval="5m",
                           prepost=True, auto_adjust=True)
            if df is None or df.empty:
                return None, None
            df = df.copy()
            df.index = pd.to_datetime(df.index)
            pm_mask = (df.index.hour >= 4) & (
                (df.index.hour < 9) |
                ((df.index.hour == 9) & (df.index.minute < 30))
            )
            pm = df[pm_mask]
            try:
                daily = t.history(period="5d", interval="1d", auto_adjust=True)
                if daily is None or daily.empty:
                    return pm, None
                idx = -2 if len(daily) >= 2 else -1
                prev_close = float(daily["Close"].iloc[idx])
                prev_high = float(daily["High"].iloc[idx])
                prev_low = float(daily["Low"].iloc[idx])
            except Exception:
                prev_close = prev_high = prev_low = None
            return pm, {"prev_close": prev_close, "prev_high": prev_high,
                        "prev_low": prev_low}
        except Exception:
            return None, None

    @staticmethod
    def gap(symbol):
        """Layer 26: Pre-Market Gap (10 pts)."""
        try:
            pm, ctx = PreMarketEngine._get_premarket_bars(symbol)
            if pm is None or pm.empty or ctx is None or ctx.get("prev_close") in (None, 0):
                return {"signal": "NO_DATA", "score": 5}
            pc = ctx["prev_close"]
            last_price = float(pm["Close"].iloc[-1])
            gap_pct = ((last_price - pc) / pc) * 100
            pm_vol = int(pm["Volume"].sum())
            if gap_pct >= 5: sig, sc = "EXTREME_GAP_UP", 8
            elif gap_pct >= 2: sig, sc = "STRONG_GAP_UP", 10
            elif gap_pct >= 0.5: sig, sc = "GAP_UP", 8
            elif gap_pct > -0.5: sig, sc = "FLAT", 5
            elif gap_pct > -2: sig, sc = "GAP_DOWN", 3
            elif gap_pct > -5: sig, sc = "STRONG_GAP_DOWN", 1
            else: sig, sc = "EXTREME_GAP_DOWN", 2
            return {"gap_pct": round(gap_pct, 2), "premarket_price": round(last_price, 2),
                    "premarket_volume": pm_vol, "signal": sig, "score": sc}
        except Exception:
            return {"signal": "ERROR", "score": 5}

    @staticmethod
    def vwap(symbol):
        """Layer 27: Pre-Market VWAP Position (10 pts)."""
        try:
            pm, ctx = PreMarketEngine._get_premarket_bars(symbol)
            if pm is None or pm.empty or len(pm) < 2:
                return {"signal": "NO_DATA", "score": 5}
            typical = (pm["High"] + pm["Low"] + pm["Close"]) / 3
            cum_tp_vol = (typical * pm["Volume"]).cumsum()
            cum_vol = pm["Volume"].cumsum()
            vwap_val = float((cum_tp_vol / cum_vol).iloc[-1])
            last_price = float(pm["Close"].iloc[-1])
            dist_pct = ((last_price - vwap_val) / vwap_val) * 100 if vwap_val else 0
            if dist_pct >= 1.5: sig, sc = "STRONG_ABOVE_VWAP", 10
            elif dist_pct >= 0.3: sig, sc = "ABOVE_VWAP", 8
            elif dist_pct > -0.3: sig, sc = "AT_VWAP", 5
            elif dist_pct > -1.5: sig, sc = "BELOW_VWAP", 3
            else: sig, sc = "STRONG_BELOW_VWAP", 1
            return {"vwap": round(vwap_val, 2), "premarket_price": round(last_price, 2),
                    "distance_pct": round(dist_pct, 2), "signal": sig, "score": sc}
        except Exception:
            return {"signal": "ERROR", "score": 5}
    @staticmethod
    def volume(symbol):
        """Layer 28: Pre-Market Volume Ratio (10 pts)."""
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="30d", interval="5m", prepost=True, auto_adjust=True)
            if df is None or df.empty or len(df) < 100:
                return {"signal": "NO_DATA", "score": 5}
            df = df.copy()
            df.index = pd.to_datetime(df.index)
            pm_mask = (df.index.hour >= 4) & (
                (df.index.hour < 9) |
                ((df.index.hour == 9) & (df.index.minute < 30))
            )
            pm = df[pm_mask]
            if pm.empty:
                return {"signal": "NO_DATA", "score": 5}
            daily_pm_vol = pm.groupby(pm.index.date)["Volume"].sum()
            if len(daily_pm_vol) < 2:
                return {"signal": "INSUFFICIENT_HISTORY", "score": 5}
            today_vol = int(daily_pm_vol.iloc[-1])
            avg_vol = float(daily_pm_vol.iloc[:-1].mean())
            if avg_vol == 0:
                return {"signal": "NO_HISTORY", "score": 5}
            ratio = today_vol / avg_vol
            if ratio >= 5: sig, sc = "EXTREME_VOLUME", 10
            elif ratio >= 3: sig, sc = "HIGH_VOLUME", 9
            elif ratio >= 1.5: sig, sc = "ELEVATED_VOLUME", 7
            elif ratio >= 0.7: sig, sc = "NORMAL_VOLUME", 5
            elif ratio >= 0.3: sig, sc = "LOW_VOLUME", 3
            else: sig, sc = "VERY_LOW_VOLUME", 1
            return {"today_volume": today_vol, "avg_volume": int(avg_vol),
                    "volume_ratio": round(ratio, 2), "signal": sig, "score": sc}
        except Exception:
            return {"signal": "ERROR", "score": 5}

    @staticmethod
    def range_break(symbol):
        """Layer 29: Pre-Market Range Break (10 pts)."""
        try:
            pm, ctx = PreMarketEngine._get_premarket_bars(symbol)
            if pm is None or pm.empty or ctx is None:
                return {"signal": "NO_DATA", "score": 5}
            if ctx.get("prev_high") is None or ctx.get("prev_low") is None:
                return {"signal": "NO_DATA", "score": 5}
            pm_high = float(pm["High"].max())
            pm_low = float(pm["Low"].min())
            pm_last = float(pm["Close"].iloc[-1])
            ph = ctx["prev_high"]
            pl = ctx["prev_low"]
            broke_high = pm_high > ph
            broke_low = pm_low < pl
            if broke_high and not broke_low: sig, sc = "BREAKED_HIGH", 10
            elif broke_low and not broke_high: sig, sc = "BREAKED_LOW", 1
            elif broke_high and broke_low:
                if pm_last > (ph + pl) / 2:
                    sig, sc = "BOTH_SIDES_BULLISH_CLOSE", 7
                else:
                    sig, sc = "BOTH_SIDES_BEARISH_CLOSE", 3
            elif pm_last > ph * 0.998: sig, sc = "TESTING_HIGH", 7
            elif pm_last < pl * 1.002: sig, sc = "TESTING_LOW", 4
            else: sig, sc = "INSIDE_RANGE", 5
            return {"premarket_high": round(pm_high, 2), "premarket_low": round(pm_low, 2),
                    "prev_high": round(ph, 2), "prev_low": round(pl, 2),
                    "broke_high": broke_high, "broke_low": broke_low,
                    "signal": sig, "score": sc}
        except Exception:
            return {"signal": "ERROR", "score": 5}

    @staticmethod
    def news(symbol):
        """Layer 30: Pre-Market News Sentiment (10 pts)."""
        try:
            t = yf.Ticker(symbol)
            news_list = []
            try:
                news_list = t.news or []
            except Exception:
                pass
            if not news_list:
                return {"signal": "NO_NEWS", "score": 5, "headlines": 0}
            now = pd.Timestamp.now(tz=None)
            pos_words = {"beat", "surge", "rally", "upgrade", "buy", "strong", "growth",
                         "profit", "win", "record", "high", "bullish", "optimistic", "gain"}
            neg_words = {"miss", "fall", "plunge", "downgrade", "sell", "weak", "loss",
                         "cut", "low", "bearish", "pessimistic", "decline", "warning", "concern"}
            total_weight = 0
            weighted_score = 0
            headlines_used = 0
            cutoff = now - pd.Timedelta(hours=24)
            for item in news_list[:10]:
                title = (item.get("title") or "").lower()
                pub = item.get("providerPublishTime")
                if not title:
                    continue
                try:
                    pub_time = pd.Timestamp.fromtimestamp(pub, tz=None) if pub else now
                except Exception:
                    pub_time = now
                if pub_time < cutoff:
                    continue
                age_hours = max(0, (now - pub_time).total_seconds() / 3600)
                weight = 2.0 if age_hours < 0.5 else 1.0 if age_hours < 4 else 0.5
                pos = sum(1 for w in pos_words if w in title)
                neg = sum(1 for w in neg_words if w in title)
                sentiment = (pos - neg) / max(pos + neg, 1)
                weighted_score += sentiment * weight
                total_weight += weight
                headlines_used += 1
            if total_weight == 0 or headlines_used == 0:
                return {"signal": "NO_RECENT_NEWS", "score": 5, "headlines": 0}
            avg = weighted_score / total_weight
            if avg >= 0.5: sig, sc = "VERY_BULLISH_NEWS", 10
            elif avg >= 0.2: sig, sc = "BULLISH_NEWS", 8
            elif avg > -0.2: sig, sc = "NEUTRAL_NEWS", 5
            elif avg > -0.5: sig, sc = "BEARISH_NEWS", 2
            else: sig, sc = "VERY_BEARISH_NEWS", 1
            return {"sentiment": round(avg, 2), "headlines": headlines_used,
                    "signal": sig, "score": sc}
        except Exception:
            return {"signal": "ERROR", "score": 5}
    @staticmethod
    def _apply_filters(layer_result, layer_name, total_premarket_volume=None,
                        spread_pct=0.0, spread_too_wide=False, time_mult=1.0):
        """Apply Tier 1 accuracy filters (A, B, C) to a single layer result.

        A. Liquidity discount: vol < 5K -> scale toward 5 by 70%, < 10K -> 40%, ==0 -> 5
        B. Spread filter:      > 0.5% -> cap at 5, > 1% -> mark TOO_ILLIQUID
        C. Time-of-day mult:   scale final score by time_mult (0.6/0.85/1.1)
        """
        if not isinstance(layer_result, dict):
            return layer_result
        if 'score' not in layer_result:
            return layer_result
        result = dict(layer_result)
        original_score = result.get('score', 5)
        new_score = original_score
        # Filter A: Liquidity discount
        if total_premarket_volume is not None:
            if total_premarket_volume == 0:
                new_score = 5
                result['liquidity_filter'] = 'NO_VOLUME_NEUTRAL'
            elif total_premarket_volume < 5000:
                new_score = int(round(original_score + (5 - original_score) * 0.7))
                result['liquidity_filter'] = f'VERY_LOW_VOL_{total_premarket_volume}'
            elif total_premarket_volume < 10000:
                new_score = int(round(original_score + (5 - original_score) * 0.4))
                result['liquidity_filter'] = f'LOW_VOL_{total_premarket_volume}'
        # Filter B: Spread filter
        if spread_too_wide:
            new_score = 5
            result['spread_filter'] = f'TOO_WIDE_{spread_pct:.2f}%_EXCLUDED'
            result['signal'] = 'TOO_ILLIQUID'
        elif spread_pct > 0.5:
            new_score = min(new_score, 5)
            result['spread_filter'] = f'WIDE_SPREAD_{spread_pct:.2f}%'
        # Filter C: Time-of-day multiplier
        if time_mult < 1.0:
            new_score = int(round(new_score + (5 - new_score) * (1 - time_mult)))
            result['time_filter'] = f'TOO_EARLY_x{time_mult}'
        elif time_mult > 1.0:
            if new_score > 5:
                new_score = int(round(5 + (new_score - 5) * time_mult))
            else:
                new_score = int(round(5 - (5 - new_score) * time_mult))
            result['time_filter'] = f'LATE_PREMARKET_x{time_mult}'
        new_score = max(0, min(10, new_score))
        result['score'] = new_score
        result['original_score'] = original_score
        result['filters_applied'] = True
        return result

    @staticmethod
    def get_filtered_premarket_data(symbol):
        """Master function: runs all 5 layers + applies Tier 1 filters.
        Returns dict with all 5 layer results + filter context (_meta).
        This is what `AdvancedSignalEngine.analyze()` should call.
        """
        try:
            spread_pct, spread_too_wide, _ = PreMarketEngine._get_spread(symbol)
            time_mult = PreMarketEngine._time_of_day_multiplier()
            et_time = PreMarketEngine._get_et_time()
            gap_r = PreMarketEngine.gap(symbol)
            vwap_r = PreMarketEngine.vwap(symbol)
            vol_r = PreMarketEngine.volume(symbol)
            range_r = PreMarketEngine.range_break(symbol)
            news_r = PreMarketEngine.news(symbol)
            total_pm_vol = None
            if isinstance(gap_r, dict):
                pmv = gap_r.get('premarket_volume')
                if pmv is not None:
                    total_pm_vol = pmv
            filtered = {
                'gap': PreMarketEngine._apply_filters(gap_r, 'gap', total_pm_vol, spread_pct, spread_too_wide, time_mult),
                'vwap': PreMarketEngine._apply_filters(vwap_r, 'vwap', total_pm_vol, spread_pct, spread_too_wide, time_mult),
                'volume': PreMarketEngine._apply_filters(vol_r, 'volume', total_pm_vol, spread_pct, spread_too_wide, time_mult),
                'range_break': PreMarketEngine._apply_filters(range_r, 'range', total_pm_vol, spread_pct, spread_too_wide, time_mult),
                'news': PreMarketEngine._apply_filters(news_r, 'news', total_pm_vol, spread_pct, spread_too_wide, time_mult),
            }
            filtered['_meta'] = {
                'spread_pct': spread_pct,
                'spread_too_wide': spread_too_wide,
                'time_multiplier': time_mult,
                'et_time': et_time.strftime('%H:%M:%S') if et_time else None,
                'total_premarket_volume': total_pm_vol,
                'filters_active': True,
            }
            return filtered
        except Exception as e:
            return {'error': str(e), '_meta': {'filters_active': False}}
