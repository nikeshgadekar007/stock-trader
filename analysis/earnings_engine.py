"""
Earnings Engine -- 5 Institutional-Grade Earnings Layers
Beat Streak, Surprise Magnitude, Estimate Revisions, IV Crush, Window Risk
Designed for earnings-based trading (pre-earnings positioning, post-earnings drift,
IV crush plays, and earnings-window risk avoidance).
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class EarningsEngine:
    """5-layer earnings institutional signal engine.
    All methods are static for safe concurrent calls.
    Each returns dict with keys: score (0-10), signal (str), details (dict).
    Fallback score is 5 (neutral) on any error or no-data condition.
    """


    @staticmethod
    def beat_streak(symbol):
        """Layer 31: Beat Streak (10 pts).
        Track consecutive EPS beats from earnings_history.
        4+ consecutive beats = strong momentum signal.
        """
        try:
            t = yf.Ticker(symbol)
            eh = t.earnings_history
            if eh is None or eh.empty or 'epsActual' not in eh.columns or 'epsEstimate' not in eh.columns:
                return {'signal': 'NO_DATA', 'score': 5}
            # Calculate beat/miss for each quarter
            eh = eh.copy()
            eh['beat'] = eh['epsActual'] > eh['epsEstimate']
            streak = 0
            streak_type = None  # 'BEAT' or 'MISS'
            for beat in eh['beat']:
                if beat and streak_type in (None, 'BEAT'):
                    streak += 1
                    streak_type = 'BEAT'
                elif not beat and streak_type in (None, 'MISS'):
                    streak += 1
                    streak_type = 'MISS'
                else:
                    break
            total_beats = int(eh['beat'].sum())
            total_quarters = len(eh)
            if streak >= 4 and streak_type == 'BEAT':
                sig, sc = 'STRONG_BEAT_STREAK', 10
            elif streak >= 3 and streak_type == 'BEAT':
                sig, sc = 'BEAT_STREAK', 8
            elif streak >= 4 and streak_type == 'MISS':
                sig, sc = 'STRONG_MISS_STREAK', 1
            elif streak >= 3 and streak_type == 'MISS':
                sig, sc = 'MISS_STREAK', 2
            elif streak == 2 and streak_type == 'BEAT':
                sig, sc = 'TWO_BEATS', 7
            elif streak == 2 and streak_type == 'MISS':
                sig, sc = 'TWO_MISSES', 3
            else:
                sig, sc = 'MIXED_HISTORY', 5
            return {'streak': streak, 'streak_type': streak_type,
                    'total_beats': total_beats, 'total_quarters': total_quarters,
                    'beat_rate': round(total_beats / max(total_quarters, 1) * 100, 1),
                    'signal': sig, 'score': sc}
        except Exception:
            return {'signal': 'ERROR', 'score': 5}


    @staticmethod
    def surprise_magnitude(symbol):
        """Layer 32: Surprise Magnitude (10 pts).
        Average surprise % over last 4 quarters.
        Big beats (>5%) indicate consistent underestimation by analysts.
        """
        try:
            t = yf.Ticker(symbol)
            eh = t.earnings_history
            if eh is None or eh.empty or 'surprisePercent' not in eh.columns:
                return {'signal': 'NO_DATA', 'score': 5}
            eh = eh.copy()
            surprises = eh['surprisePercent'].dropna()
            if len(surprises) == 0:
                return {'signal': 'NO_DATA', 'score': 5}
            avg_surprise = float(surprises.mean())
            max_surprise = float(surprises.max())
            min_surprise = float(surprises.min())
            positive_surprises = int((surprises > 0).sum())
            if avg_surprise >= 10:
                sig, sc = 'HUGE_BEATS', 10
            elif avg_surprise >= 5:
                sig, sc = 'STRONG_BEATS', 9
            elif avg_surprise >= 2:
                sig, sc = 'MODERATE_BEATS', 7
            elif avg_surprise >= 0:
                sig, sc = 'MILD_BEATS', 6
            elif avg_surprise >= -2:
                sig, sc = 'MILD_MISSES', 4
            elif avg_surprise >= -5:
                sig, sc = 'MODERATE_MISSES', 3
            else:
                sig, sc = 'HUGE_MISSES', 1
            return {'avg_surprise_pct': round(avg_surprise, 2),
                    'max_surprise_pct': round(max_surprise, 2),
                    'min_surprise_pct': round(min_surprise, 2),
                    'positive_surprises': positive_surprises,
                    'total_reports': len(surprises),
                    'signal': sig, 'score': sc}
        except Exception:
            return {'signal': 'ERROR', 'score': 5}


    @staticmethod
    def estimate_revisions(symbol):
        """Layer 33: Estimate Revisions (10 pts).
        Compare 0q estimate vs +1q estimate from earnings_estimate.
        Rising estimates = analyst confidence = bullish.
        Falling estimates = analyst downgrading = bearish.
        """
        try:
            t = yf.Ticker(symbol)
            ee = t.earnings_estimate
            if ee is None or ee.empty:
                return {'signal': 'NO_DATA', 'score': 5}
            ee = ee.copy()
            current_q = ee.loc['0q'] if '0q' in ee.index else None
            next_q = ee.loc['+1q'] if '+1q' in ee.index else None
            current_y = ee.loc['0y'] if '0y' in ee.index else None
            next_y = ee.loc['+1y'] if '+1y' in ee.index else None
            if current_q is None or next_q is None:
                return {'signal': 'INSUFFICIENT_DATA', 'score': 5}
            # Try to extract avg estimate column
            avg_col = None
            for col in ['avg', 'average', 'meanAvg']:
                if col in ee.columns:
                    avg_col = col
                    break
            if avg_col is None:
                # Use first numeric column
                numeric_cols = ee.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    avg_col = numeric_cols[0]
            if avg_col is None:
                return {'signal': 'NO_DATA', 'score': 5}
            curr_q_val = float(current_q[avg_col])
            next_q_val = float(next_q[avg_col])
            if curr_q_val == 0:
                return {'signal': 'NO_DATA', 'score': 5}
            revision_pct = ((next_q_val - curr_q_val) / abs(curr_q_val)) * 100
            growth_col = None
            for col in ['growth', 'Growth']:
                if col in ee.columns:
                    growth_col = col
                    break
            current_growth = float(current_q[growth_col]) if growth_col and pd.notna(current_q.get(growth_col)) else None
            next_growth = float(next_q[growth_col]) if growth_col and pd.notna(next_q.get(growth_col)) else None
            if revision_pct >= 10:
                sig, sc = 'STRONG_UPWARD_REVISION', 10
            elif revision_pct >= 3:
                sig, sc = 'UPWARD_REVISION', 8
            elif revision_pct >= 0:
                sig, sc = 'STABLE_ESTIMATES', 6
            elif revision_pct >= -3:
                sig, sc = 'MILD_DOWNWARD', 4
            elif revision_pct >= -10:
                sig, sc = 'DOWNWARD_REVISION', 2
            else:
                sig, sc = 'STRONG_DOWNWARD', 1
            return {'current_q_estimate': round(curr_q_val, 3),
                    'next_q_estimate': round(next_q_val, 3),
                    'revision_pct': round(revision_pct, 2),
                    'current_growth': current_growth,
                    'next_growth': next_growth,
                    'signal': sig, 'score': sc}
        except Exception:
            return {'signal': 'ERROR', 'score': 5}


    @staticmethod
    def iv_crush_signal(symbol):
        """Layer 34: IV Crush Signal (10 pts).
        Calculate IV from ATM straddle (call+put price vs underlying).
        High IV rank before earnings = opportunity for premium sellers,
        DANGEROUS for option buyers (IV crushes after earnings).
        """
        try:
            t = yf.Ticker(symbol)
            if not t.options:
                return {'signal': 'NO_OPTIONS', 'score': 5}
            # Use the nearest expiration
            exp = t.options[0]
            chain = t.option_chain(exp)
            calls = chain.calls
            puts = chain.puts
            if calls.empty or puts.empty:
                return {'signal': 'NO_CHAIN_DATA', 'score': 5}
            # Get current price from underlying
            try:
                hist = t.history(period='1d', auto_adjust=True)
                if hist.empty:
                    return {'signal': 'NO_PRICE', 'score': 5}
                spot = float(hist['Close'].iloc[-1])
            except Exception:
                return {'signal': 'NO_PRICE', 'score': 5}
            # Find ATM strike (closest to spot)
            all_strikes = sorted(set(calls['strike'].tolist()) & set(puts['strike'].tolist()))
            if not all_strikes:
                return {'signal': 'NO_ATM_STRIKE', 'score': 5}
            atm_strike = min(all_strikes, key=lambda s: abs(s - spot))
            # Get ATM call and put mid-prices
            atm_call = calls[calls['strike'] == atm_strike]
            atm_put = puts[puts['strike'] == atm_strike]
            if atm_call.empty or atm_put.empty:
                return {'signal': 'NO_ATM_DATA', 'score': 5}
            call_mid = (float(atm_call['bid'].iloc[0]) + float(atm_call['ask'].iloc[0])) / 2
            put_mid = (float(atm_put['bid'].iloc[0]) + float(atm_put['ask'].iloc[0])) / 2
            straddle_price = call_mid + put_mid
            # Calculate historical volatility (30-day) for comparison
            hist_30 = t.history(period='3mo', auto_adjust=True)
            if hist_30.empty or len(hist_30) < 20:
                return {'straddle_price': round(straddle_price, 2),
                        'atm_strike': atm_strike, 'spot': round(spot, 2),
                        'implied_vol_pct': 'unknown', 'signal': 'NO_HIST', 'score': 5}
            hist_30 = hist_30.copy()
            hist_30['log_return'] = np.log(hist_30['Close'] / hist_30['Close'].shift(1))
            realized_vol = float(hist_30['log_return'].std() * np.sqrt(252) * 100)
            # Implied vol from straddle (rough): straddle ~= 0.4 * spot * sigma * sqrt(T)
            # For T < 30 days, approximate T = 7/365
            T = 7 / 365
            implied_vol_pct = (straddle_price / (0.4 * spot * np.sqrt(T))) * 100
            # IV rank proxy: ratio of implied to realized
            iv_ratio = implied_vol_pct / max(realized_vol, 1)
            if iv_ratio >= 2.5:
                sig, sc = 'EXTREME_IV_SELL_PREMIUM', 10
            elif iv_ratio >= 1.8:
                sig, sc = 'HIGH_IV_SELL_PREMIUM', 9
            elif iv_ratio >= 1.3:
                sig, sc = 'ELEVATED_IV', 7
            elif iv_ratio >= 0.8:
                sig, sc = 'NORMAL_IV', 5
            elif iv_ratio >= 0.5:
                sig, sc = 'LOW_IV', 3
            else:
                sig, sc = 'VERY_LOW_IV', 2
            return {'straddle_price': round(straddle_price, 2),
                    'atm_strike': atm_strike, 'spot': round(spot, 2),
                    'implied_vol_pct': round(implied_vol_pct, 1),
                    'realized_vol_pct': round(realized_vol, 1),
                    'iv_ratio': round(iv_ratio, 2),
                    'signal': sig, 'score': sc}
        except Exception:
            return {'signal': 'ERROR', 'score': 5}


    @staticmethod
    def earnings_window_risk(symbol):
        """Layer 35: Earnings Window Risk (10 pts).
        Days until next earnings date. Best trading windows:
          - 1-5 days AFTER earnings: post-earnings drift (academic edge)
          - 15+ days before earnings: clear sky, normal trading
        Worst windows:
          - 0-3 days BEFORE earnings: binary event risk, avoid
          - Day of earnings: gap risk, IV crush
        """
        try:
            t = yf.Ticker(symbol)
            cal = None
            next_earnings = None
            # Try calendar first
            try:
                cal = t.calendar
                if cal and isinstance(cal, dict) and 'Earnings Date' in cal:
                    ed_list = cal['Earnings Date']
                    if ed_list and len(ed_list) > 0:
                        next_earnings = ed_list[0]
            except Exception:
                pass
            # Fallback: earnings_dates
            if next_earnings is None:
                try:
                    ed_df = t.earnings_dates
                    if ed_df is not None and not ed_df.empty:
                        future = ed_df[ed_df.index > pd.Timestamp.now()]
                        if not future.empty:
                            next_earnings = future.index[0].date()
                except Exception:
                    pass
            if next_earnings is None:
                return {'signal': 'NO_DATA', 'score': 5}
            # Calculate days until
            if hasattr(next_earnings, 'date'):
                next_earnings_date = next_earnings if hasattr(next_earnings, 'strftime') else next_earnings.date()
            else:
                next_earnings_date = next_earnings
            today = datetime.now().date()
            if hasattr(next_earnings_date, 'date'):
                next_earnings_date = next_earnings_date.date()
            days_until = (next_earnings_date - today).days
            if days_until == 0:
                sig, sc = 'EARNINGS_DAY', 2
                window = 'EARNINGS_DAY'
            elif days_until == 1:
                sig, sc = 'PRE_EARNINGS_TOMORROW', 2
                window = 'PRE_EARNINGS_1D'
            elif 2 <= days_until <= 3:
                sig, sc = 'PRE_EARNINGS_2_3D', 3
                window = 'PRE_EARNINGS_BLACKOUT'
            elif 4 <= days_until <= 7:
                sig, sc = 'WATCHLIST_PRE_EARNINGS', 5
                window = 'WATCHLIST'
            elif -5 <= days_until < 0:
                # Post-earnings drift window
                days_since = abs(days_until)
                if days_since <= 2:
                    sig, sc = 'POST_EARNINGS_DRIFT_1_2D', 10
                elif days_since <= 3:
                    sig, sc = 'POST_EARNINGS_DRIFT_3D', 9
                else:
                    sig, sc = 'POST_EARNINGS_DRIFT_4_5D', 8
                window = 'POST_EARNINGS_DRIFT'
            elif -10 <= days_until < -5:
                sig, sc = 'POST_EARNINGS_OLD', 6
                window = 'POST_EARNINGS_FADING'
            elif days_until > 7:
                sig, sc = 'CLEAR_SKY', 7
                window = 'CLEAR_SKY'
            else:
                # days_until < -10
                sig, sc = 'NEUTRAL', 5
                window = 'NEUTRAL'
            return {'days_until_earnings': days_until,
                    'next_earnings_date': str(next_earnings_date),
                    'window': window,
                    'signal': sig, 'score': sc}
        except Exception:
            return {'signal': 'ERROR', 'score': 5}

