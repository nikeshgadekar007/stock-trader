"""
Regime Detector - Classifies current market regime from 4 macro inputs.

Regime classes:
  - BULL_TREND:      Uptrend with low/normal volatility, breakouts work
  - BEAR_TREND:      Downtrend with rising vol, mean reversion fails, sweeps work
  - RANGE_BOUND:     Sideways, breakouts fake out, mean reversion works
  - VOLATILE_SHOCK:  VIX spike / dislocation, only defensive setups work
  - LOW_VOL_GRIND:   VIX <15, slow drift, options cheap, mean reversion works

Inputs (4):
  1. VIX term structure (^VIX vs ^VIX3M)
  2. SPY 200-MA slope (rising/falling)
  3. Breadth: % of S&P 500 above 50-MA
  4. 3-month sector momentum (XLK vs XLE vs XLF etc.)

Output: regime name + confidence (0-1) + per-input contributions.
"""
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime
from typing import Dict


class RegimeDetector:
    """Detects market regime from macro inputs. Caches for 1 hour."""

    CACHE_TTL_MINUTES = 60

    def __init__(self):
        self.regime = 'UNKNOWN'
        self.confidence = 0.0
        self.inputs = {}
        self.timestamp = None

    def detect(self, use_cache=True):
        """Detect current regime. Returns dict with regime, confidence, inputs."""
        now = datetime.now()
        if use_cache and self.timestamp and (now - self.timestamp).total_seconds() < self.CACHE_TTL_MINUTES * 60:
            return self._result_dict()
        try:
            vix_term = self._vix_term_structure()
            spy_slope = self._spy_200ma_slope()
            breadth = self._market_breadth()
            sector_mom = self._sector_momentum()
            self.inputs = {'vix_term': vix_term, 'spy_slope': spy_slope,
                           'breadth': breadth, 'sector_momentum': sector_mom}
            regime_scores = self._score_regimes(vix_term, spy_slope, breadth, sector_mom)
            self.regime = max(regime_scores, key=regime_scores.get)
            sorted_scores = sorted(regime_scores.values(), reverse=True)
            total = sum(sorted_scores)
            self.confidence = round(sorted_scores[0] / total, 2) if total > 0 else 0.0
            self.timestamp = now
            return self._result_dict()
        except Exception as e:
            self.regime = 'UNKNOWN'
            self.confidence = 0.0
            self.inputs = {'error': str(e)}
            self.timestamp = now
            return self._result_dict()

    def _result_dict(self):
        return {'regime': self.regime, 'confidence': self.confidence,
                'inputs': self.inputs,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None,
                'description': self._regime_description(self.regime)}
    def _vix_term_structure(self):
        """VIX spot vs 3-month VIX. Contango = calm, backwardation = stressed."""
        try:
            vix = yf.Ticker('^VIX').history(period='5d', auto_adjust=True)
            vix3m = yf.Ticker('^VIX3M').history(period='5d', auto_adjust=True)
            if vix.empty or vix3m.empty:
                return {'slope': 0, 'vix_spot': 20, 'signal': 'NEUTRAL'}
            spot = float(vix['Close'].iloc[-1])
            fwd = float(vix3m['Close'].iloc[-1])
            slope = fwd - spot
            if spot > 30:
                sig = 'STRESS'
            elif spot > 22:
                sig = 'ELEVATED'
            elif spot < 13:
                sig = 'COMPLACENT'
            else:
                sig = 'NORMAL'
            return {'slope': round(slope, 2), 'vix_spot': round(spot, 2), 'signal': sig}
        except Exception:
            return {'slope': 0, 'vix_spot': 20, 'signal': 'NEUTRAL'}

    def _spy_200ma_slope(self):
        """Is SPY's 200-MA rising or falling?"""
        try:
            spy = yf.Ticker('SPY').history(period='1y', auto_adjust=True)
            if spy.empty or len(spy) < 200:
                return {'slope_pct': 0, 'price_vs_ma_pct': 0, 'signal': 'NEUTRAL'}
            ma200 = spy['Close'].rolling(200).mean()
            slope = (ma200.iloc[-1] - ma200.iloc[-20]) / ma200.iloc[-20] * 100
            price_vs_ma = (spy['Close'].iloc[-1] - ma200.iloc[-1]) / ma200.iloc[-1] * 100
            if slope > 1.5:
                sig = 'STRONG_UP'
            elif slope > 0.3:
                sig = 'UP'
            elif slope < -1.5:
                sig = 'STRONG_DOWN'
            elif slope < -0.3:
                sig = 'DOWN'
            else:
                sig = 'FLAT'
            return {'slope_pct': round(slope, 2), 'price_vs_ma_pct': round(price_vs_ma, 2), 'signal': sig}
        except Exception:
            return {'slope_pct': 0, 'price_vs_ma_pct': 0, 'signal': 'NEUTRAL'}

    def _market_breadth(self):
        """Approximate breadth: large sector ETFs above 50-MA."""
        try:
            etfs = ['SPY', 'QQQ', 'IWM', 'XLE', 'XLF', 'XLK', 'XLV', 'XLY', 'XLP', 'XLI']
            above = 0
            total = 0
            for etf in etfs:
                df = yf.Ticker(etf).history(period='6mo', auto_adjust=True)
                if df.empty or len(df) < 50:
                    continue
                total += 1
                ma50 = df['Close'].rolling(50).mean().iloc[-1]
                if df['Close'].iloc[-1] > ma50:
                    above += 1
            pct = above / total * 100 if total > 0 else 50
            if pct > 75:
                sig = 'BROAD'
            elif pct > 55:
                sig = 'HEALTHY'
            elif pct < 25:
                sig = 'NARROW_DECLINE'
            elif pct < 45:
                sig = 'WEAK'
            else:
                sig = 'MIXED'
            return {'pct_above_50ma': round(pct, 1), 'signal': sig}
        except Exception:
            return {'pct_above_50ma': 50, 'signal': 'MIXED'}

    def _sector_momentum(self):
        """3-month relative performance of key sectors."""
        try:
            sectors = {'Tech': 'XLK', 'Energy': 'XLE', 'Financials': 'XLF',
                        'Healthcare': 'XLV', 'Consumer': 'XLY', 'Staples': 'XLP',
                        'Industrials': 'XLI', 'Utilities': 'XLU'}
            perf = {}
            for name, etf in sectors.items():
                df = yf.Ticker(etf).history(period='6mo', auto_adjust=True)
                if df.empty or len(df) < 60:
                    continue
                ret = (df['Close'].iloc[-1] - df['Close'].iloc[-60]) / df['Close'].iloc[-60] * 100
                perf[name] = round(ret, 2)
            if not perf:
                return {'leaders': [], 'laggards': [], 'spread': 0}
            sorted_perf = sorted(perf.items(), key=lambda x: x[1], reverse=True)
            leaders = [s[0] for s in sorted_perf[:2]]
            laggards = [s[0] for s in sorted_perf[-2:]]
            spread = sorted_perf[0][1] - sorted_perf[-1][1]
            return {'leaders': leaders, 'laggards': laggards, 'spread': round(spread, 2), 'all': perf}
        except Exception:
            return {'leaders': [], 'laggards': [], 'spread': 0}
    def _score_regimes(self, vix_term, spy_slope, breadth, sector_mom):
        """Score each regime from 0 to 10+ based on input alignment."""
        scores = {'BULL_TREND': 0, 'BEAR_TREND': 0, 'RANGE_BOUND': 0,
                  'VOLATILE_SHOCK': 0, 'LOW_VOL_GRIND': 0}
        vix_spot = vix_term.get('vix_spot', 20)
        if vix_spot > 30:
            scores['VOLATILE_SHOCK'] += 4
            scores['BEAR_TREND'] += 2
        elif vix_spot > 22:
            scores['BEAR_TREND'] += 2
            scores['VOLATILE_SHOCK'] += 1
        elif vix_spot < 13:
            scores['LOW_VOL_GRIND'] += 4
            scores['BULL_TREND'] += 1
        else:
            scores['BULL_TREND'] += 1
            scores['RANGE_BOUND'] += 1

        slope_signal = spy_slope.get('signal', 'NEUTRAL')
        if slope_signal == 'STRONG_UP':
            scores['BULL_TREND'] += 4
            scores['LOW_VOL_GRIND'] += 1
        elif slope_signal == 'UP':
            scores['BULL_TREND'] += 3
        elif slope_signal == 'STRONG_DOWN':
            scores['BEAR_TREND'] += 4
            scores['VOLATILE_SHOCK'] += 2
        elif slope_signal == 'DOWN':
            scores['BEAR_TREND'] += 3
        else:
            scores['RANGE_BOUND'] += 2

        breadth_signal = breadth.get('signal', 'MIXED')
        if breadth_signal == 'BROAD':
            scores['BULL_TREND'] += 3
        elif breadth_signal == 'HEALTHY':
            scores['BULL_TREND'] += 2
        elif breadth_signal == 'NARROW_DECLINE':
            scores['BEAR_TREND'] += 3
        elif breadth_signal == 'WEAK':
            scores['BEAR_TREND'] += 2
        else:
            scores['RANGE_BOUND'] += 1

        spread = sector_mom.get('spread', 0)
        if spread > 15:
            scores['BULL_TREND'] += 1
            scores['VOLATILE_SHOCK'] += 1
        elif spread < 5:
            scores['LOW_VOL_GRIND'] += 2
            scores['RANGE_BOUND'] += 1
        return scores

    def _regime_description(self, regime):
        descriptions = {
            'BULL_TREND': 'Uptrend with healthy breadth. Favor breakouts, momentum, trend-following.',
            'BEAR_TREND': 'Downtrend with rising volatility. Favor defensive shorts, liquidity sweeps.',
            'RANGE_BOUND': 'Sideways market. Favor mean reversion, support/resistance bounces.',
            'VOLATILE_SHOCK': 'Elevated stress, VIX >30. Reduce size, favor low-beta defensive setups.',
            'LOW_VOL_GRIND': 'Low VIX complacent market. Favor mean reversion, options selling.',
            'UNKNOWN': 'Insufficient data to classify regime.',
        }
        return descriptions.get(regime, 'Unknown regime.')


_regime_instance = None


def get_current_regime(use_cache=True):
    """Convenience function - get current regime."""
    global _regime_instance
    if _regime_instance is None:
        _regime_instance = RegimeDetector()
    return _regime_instance.detect(use_cache=use_cache)


if __name__ == '__main__':
    print('Testing RegimeDetector...')
    rd = RegimeDetector()
    result = rd.detect(use_cache=False)
    print("\nRegime: " + result['regime'] + " (confidence: " + str(result['confidence']) + ")")
    print("Description: " + result['description'])
    print("\nInputs:")
    for k, v in result['inputs'].items():
        print("  " + str(k) + ": " + str(v))