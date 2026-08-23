"""
Composite Scorer -- simplifies 35-layer ConfluenceScorer into 8 composite layers.
Each composite aggregates 2-5 individual layers and is scored 0-15.
Total max = 120, scaled to 100 for clean grade thresholds.
"""
from .confluence_scorer import ConfluenceScorer


COMPOSITE_GROUPS = {
    'trend':       (['trend', 'support_resistance', 'fibonacci', 'candlestick', 'breakout'], 75),
    'momentum':    (['momentum', 'volume', 'smart_money', 'liquidity_sweep'], 40),
    'context':     (['regime', 'vix_term', 'cross_asset', 'atr_risk'], 35),
    'fundamentals':(['fundamentals', 'sentiment', 'earnings_surprise'], 30),
    'smart_money': (['insider', 'short_interest', 'bearish_divergence'], 30),
    'risk':        (['trade_mgmt', 'liquidity', 'earnings_window'], 20),
    'premarket':   (['premarket_gap', 'premarket_vwap', 'premarket_volume', 'premarket_range', 'premarket_news'], 50),
    'earnings':    (['earnings_beat_streak', 'earnings_revisions', 'earnings_iv'], 30),
}

COMPOSITE_NAMES = {
    'trend':        'Trend & Direction',
    'momentum':     'Momentum',
    'context':      'Market Context',
    'fundamentals': 'Fundamentals',
    'smart_money':  'Smart Money',
    'risk':         'Risk Management',
    'premarket':    'Pre-Market Edge',
    'earnings':     'Earnings Edge',
}


def score_to_composite(scores: dict) -> dict:
    """Aggregate 35 individual layer scores into 8 composites (each 0-15)."""
    out = {}
    for cname, (layers, max_pts) in COMPOSITE_GROUPS.items():
        raw = 0
        present = 0
        for layer in layers:
            v = scores.get(layer)
            if v is None:
                continue
            present += 1
            raw += v
        scaled = (raw / max_pts) * 15 if max_pts else 0
        scaled = round(scaled, 2)
        out[cname] = {
            'score': scaled,
            'max': 15,
            'raw_total': raw,
            'raw_max': max_pts,
            'pct': round((raw / max_pts) * 100, 1) if max_pts else 0,
            'layers_present': present,
            'layers_total': len(layers),
        }
    return out


def get_total_score(scores: dict) -> dict:
    """Sum all composite scores. Total 0-100 (scaled from 0-120)."""
    composites = score_to_composite(scores)
    raw_total = sum(c['score'] for c in composites.values())
    pct_total = (raw_total / 120) * 100
    total = round(pct_total, 1)
    if total >= 85:
        grade = 'A+'
    elif total >= 75:
        grade = 'A'
    elif total >= 60:
        grade = 'B'
    elif total >= 40:
        grade = 'C'
    else:
        grade = 'D'
    return {
        'total': total,
        'max': 100,
        'composites': composites,
        'grade': grade,
        'raw_total': round(raw_total, 1),
        'raw_max': 120,
    }


def score_symbol(symbol: str, direction: str = 'long') -> dict:
    """Run ConfluenceScorer + AdvancedSignalEngine, return simplified composite.
    This is the ONE function callers should use for the simplified dashboard.
    """
    cs = ConfluenceScorer()
    raw = cs.score_all(symbol, direction=direction)
    if 'error' in raw:
        return raw
    scores = raw.get('scores', {})
    result = get_total_score(scores)
    result['symbol'] = raw.get('symbol')
    result['direction'] = raw.get('direction')
    result['current_price'] = raw.get('current_price')
    result['signal'] = raw.get('signal')
    # Notes from earnings window
    notes = []
    ew = raw.get('details', {}).get('earnings_window', {})
    days_until = ew.get('days_until_earnings')
    if days_until is not None:
        if 0 <= days_until <= 3:
            notes.append("Pre-earnings in " + str(days_until) + "d")
        elif -5 <= days_until < 0:
            notes.append("Post-drift day " + str(-days_until))
        elif days_until > 15:
            notes.append("Clear sky (" + str(days_until) + "d)")
    beat = raw.get('details', {}).get('earnings_beat_streak', {})
    streak = beat.get('streak', 0)
    if streak >= 3:
        notes.append("Beat streak " + str(streak))
    surprise = raw.get('details', {}).get('earnings_surprise', {})
    avg_sp = surprise.get('avg_surprise_pct', 0)
    if avg_sp >= 5:
        notes.append("Avg surprise " + ('%+.1f' % avg_sp) + '%')
    result['notes'] = ' | '.join(notes) if notes else ''
    result['earnings_window'] = ew.get('window', 'NEUTRAL')
    # Entry/target/stop from AdvancedSignalEngine
    try:
        from analysis.advanced_signals import AdvancedSignalEngine
        eng = AdvancedSignalEngine()
        sig = eng.generate_signal(symbol, include_premarket=False)
        if 'error' not in sig:
            result['entry'] = sig.get('entry')
            result['target'] = sig.get('target')
            result['stop_loss'] = sig.get('stop_loss')
            result['risk_reward'] = sig.get('risk_reward')
    except Exception:
        result['entry'] = None
        result['target'] = None
        result['stop_loss'] = None
    return result