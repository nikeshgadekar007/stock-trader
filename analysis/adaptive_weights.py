"""
Adaptive Weights - Regime-based layer weight multipliers.

Core insight: Same indicator means different things in different regimes.
  - Breakouts work in BULL_TREND, fail in RANGE_BOUND (fakeouts)
  - Mean reversion works in RANGE_BOUND, fails in BULL_TREND
  - Liquidity sweeps work in BEAR_TREND (capitulation reversals)
  - Options wall is most informative in LOW_VOL_GRIND

Each layer gets a multiplier (0.0 - 1.5):
  0.0 = disable layer entirely
  0.5 = downweight
  1.0 = neutral
  1.5 = boost

Usage:
  from analysis.adaptive_weights import get_regime_weights, apply_regime_weights
  weights = get_regime_weights('BULL_TREND')
  adjusted_scores = apply_regime_weights(scores_dict, 'BULL_TREND')
"""
from typing import Dict


# Layer keys used in the 35-layer confluence system
LAYER_KEYS = [
    'trend', 'support_resistance', 'fibonacci', 'candlestick', 'momentum',
    'volume', 'sentiment', 'fundamentals', 'regime', 'ml', 'sector',
    'atr_risk', 'earnings', 'insider', 'breakout', 'trade_mgmt', 'liquidity',
    'short_interest', 'bearish_divergence', 'opg',
    'options_wall', 'vix_term', 'cross_asset', 'smart_money', 'liquidity_sweep',
    'premarket_gap', 'premarket_vwap', 'premarket_volume', 'premarket_range', 'premarket_news',
    'earnings_beat_streak', 'earnings_surprise', 'earnings_revisions', 'earnings_iv', 'earnings_window',
]


REGIME_WEIGHTS = {
    'BULL_TREND': {
        'trend': 1.4, 'momentum': 1.3, 'breakout': 1.5, 'volume': 1.2,
        'sector': 1.2, 'opg': 1.3, 'smart_money': 1.2,
        'support_resistance': 0.7, 'fibonacci': 0.8, 'candlestick': 0.8,
        'liquidity_sweep': 0.6, 'short_interest': 0.6, 'bearish_divergence': 0.5,
        'vix_term': 0.7, 'cross_asset': 0.9,
    },
    'BEAR_TREND': {
        'trend': 0.7, 'momentum': 0.7, 'breakout': 0.4, 'opg': 0.6,
        'support_resistance': 1.3, 'fibonacci': 1.2, 'candlestick': 1.1,
        'liquidity_sweep': 1.5, 'short_interest': 1.4, 'bearish_divergence': 1.3,
        'vix_term': 1.4, 'cross_asset': 1.2, 'sentiment': 1.2,
        'fundamentals': 1.1, 'insider': 1.2, 'atr_risk': 1.3,
        'premarket_news': 1.1, 'earnings_revisions': 1.1, 'options_wall': 1.2,
    },
    'RANGE_BOUND': {
        'trend': 0.5, 'momentum': 0.7, 'breakout': 0.3, 'volume': 0.8,
        'sector': 0.8, 'opg': 0.7, 'smart_money': 0.8,
        'support_resistance': 1.5, 'fibonacci': 1.4, 'candlestick': 1.3,
        'liquidity_sweep': 1.2, 'bearish_divergence': 1.2,
        'vix_term': 0.8, 'cross_asset': 0.8, 'sentiment': 0.9, 'fundamentals': 0.8,
        'insider': 0.9, 'premarket_gap': 0.9, 'premarket_volume': 0.9,
        'earnings_beat_streak': 0.9, 'earnings_revisions': 0.9, 'options_wall': 1.1,
    },
    'VOLATILE_SHOCK': {
        'trend': 0.5, 'momentum': 0.5, 'breakout': 0.3, 'volume': 0.7,
        'sector': 0.7, 'opg': 0.4, 'smart_money': 1.1,
        'support_resistance': 1.2, 'liquidity_sweep': 1.4,
        'short_interest': 1.2, 'bearish_divergence': 1.2,
        'vix_term': 1.5, 'cross_asset': 1.3, 'sentiment': 1.3,
        'fundamentals': 1.2, 'ml': 0.8, 'atr_risk': 1.5,
        'insider': 1.3, 'trade_mgmt': 1.3, 'liquidity': 1.3,
        'premarket_gap': 0.5, 'premarket_vwap': 0.7, 'premarket_volume': 1.2,
        'premarket_news': 1.2, 'options_wall': 1.3,
    },
    'LOW_VOL_GRIND': {
        'momentum': 0.8, 'volume': 0.8, 'sector': 1.1,
        'smart_money': 1.3, 'support_resistance': 1.1,
        'liquidity_sweep': 1.1, 'short_interest': 1.1,
        'bearish_divergence': 1.1, 'vix_term': 0.8,
        'sentiment': 1.1, 'fundamentals': 1.1, 'atr_risk': 0.9,
        'insider': 1.1, 'earnings_iv': 1.1, 'options_wall': 1.3,
    },
}


def get_regime_weights(regime: str) -> Dict[str, float]:
    """Get layer weight multipliers for a regime. Defaults to 1.0 for unspecified."""
    weights = {k: 1.0 for k in LAYER_KEYS}
    regime_w = REGIME_WEIGHTS.get(regime, {})
    weights.update(regime_w)
    return weights


def apply_regime_weights(scores: Dict[str, int], regime: str) -> Dict[str, float]:
    """Apply regime multipliers to layer scores. Returns adjusted scores."""
    weights = get_regime_weights(regime)
    adjusted = {}
    for layer, score in scores.items():
        mult = weights.get(layer, 1.0)
        adjusted[layer] = round(score * mult, 2)
    return adjusted


def get_adjusted_total(scores: Dict[str, int], regime: str) -> float:
    """Compute total score with regime-weighted adjustments."""
    weights = get_regime_weights(regime)
    total = 0.0
    for layer, score in scores.items():
        mult = weights.get(layer, 1.0)
        total += score * mult
    return round(total, 1)


if __name__ == '__main__':
    print('Regime weights:')
    for regime in REGIME_WEIGHTS:
        weights = get_regime_weights(regime)
        boosted = [k for k, v in weights.items() if v > 1.1]
        reduced = [k for k, v in weights.items() if v < 0.9]
        print("\n" + regime + ":")
        print("  BOOSTED: " + ', '.join(boosted))
        print("  REDUCED: " + ', '.join(reduced))