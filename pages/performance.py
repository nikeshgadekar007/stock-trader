"""
Performance Dashboard - Live signal outcome tracking.

Shows win rate by grade, sector, regime, and per-layer predictive power.
Outcomes are auto-updated each time you visit this page.
"""
import streamlit as st
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from analysis.signal_tracker import (
    init_db, update_outcomes,
    get_performance_stats, get_layer_performance
)

st.set_page_config(page_title="Performance", page_icon="[STAT]", layout="wide")
try:
    from components.theme import init_theme
    init_theme()
except Exception:
    pass

st.title("[STAT] Performance Dashboard")
st.caption("Live signal tracking - outcomes auto-update on each visit")

with st.sidebar:
    st.header("[CTRL] Controls")
    days_back = st.slider("Lookback (days)", 7, 365, 90, 7,
                           help="How far back to compute stats")
    if st.button("[UPD] Update Outcomes Now", type="primary"):
        with st.spinner("Fetching latest prices..."):
            n = update_outcomes(batch_size=200)
            st.success("Updated " + str(n) + " signals")

with st.spinner("Updating outcomes..."):
    n_updated = update_outcomes(batch_size=200)

st.caption("Auto-updated " + str(n_updated) + " signals on page load")

stats = get_performance_stats(days=days_back)

st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Tracked Signals", stats['total_tracked'])
with col2:
    st.metric("Win Rate (5d)", stats['win_rate_5d'],
               delta=str(stats['avg_return_5d_pct']) + "% avg return")
with col3:
    st.metric("Wins (5d)", stats['wins_5d'])
with col4:
    st.metric("Avg Return (5d)", str(stats['avg_return_5d_pct']) + "%")


def _color_wr(val):
    try:
        v = float(val)
        if v >= 70:
            return 'background-color: #28a745; color: white; font-weight: bold'
        if v >= 55:
            return 'background-color: #5cb85c; color: white'
        if v >= 45:
            return 'background-color: #ffc107; color: black'
        return 'background-color: #dc3545; color: white'
    except Exception:
        return ''


st.markdown("---")
st.subheader("[GRADE] Win Rate by Grade")
if stats['by_grade']:
    grade_data = []
    for grade, info in sorted(stats['by_grade'].items(),
                               key=lambda x: -x[1]['win_rate']):
        grade_data.append({
            'Grade': grade,
            'Trades': info['trades'],
            'Wins': info['wins'],
            'Win Rate': info['win_rate'],
            'Avg Return %': info['avg_return_pct']
        })
    df_grade = pd.DataFrame(grade_data)
    try:
        styled = df_grade.style.map(_color_wr, subset=['Win Rate'])
        st.dataframe(styled, use_container_width=True, hide_index=True)
    except Exception:
        st.dataframe(df_grade, use_container_width=True, hide_index=True)
else:
    st.info("No signals with resolved outcomes yet. Keep scanning for 5+ days.")

st.markdown("---")
st.subheader("[SECT] Win Rate by Sector")
if stats['by_sector']:
    sector_data = []
    for sector, info in sorted(stats['by_sector'].items(),
                                key=lambda x: -x[1]['win_rate']):
        sector_data.append({
            'Sector': sector,
            'Trades': info['trades'],
            'Wins': info['wins'],
            'Win Rate': info['win_rate'],
            'Avg Return %': info['avg_return_pct']
        })
    df_sector = pd.DataFrame(sector_data)
    try:
        st.dataframe(df_sector.style.map(_color_wr, subset=['Win Rate']),
                      use_container_width=True, hide_index=True)
    except Exception:
        st.dataframe(df_sector, use_container_width=True, hide_index=True)
else:
    st.info("No sector data yet.")

st.markdown("---")
st.subheader("[REG] Win Rate by Market Regime")
if stats['by_regime']:
    regime_data = []
    for regime, info in sorted(stats['by_regime'].items(),
                                key=lambda x: -x[1]['win_rate']):
        regime_data.append({
            'Regime': regime,
            'Trades': info['trades'],
            'Wins': info['wins'],
            'Win Rate': info['win_rate'],
            'Avg Return %': info['avg_return_pct']
        })
    df_regime = pd.DataFrame(regime_data)
    try:
        st.dataframe(df_regime.style.map(_color_wr, subset=['Win Rate']),
                      use_container_width=True, hide_index=True)
    except Exception:
        st.dataframe(df_regime, use_container_width=True, hide_index=True)
else:
    st.info("No regime data yet.")

st.markdown("---")
st.subheader("[LAYER] Layer Predictive Power")
st.caption("Predictive Power = high_score_win_rate - low_score_win_rate. "
            "Layers with high values are most useful.")

layer_perf = get_layer_performance(days=days_back)
if layer_perf:
    layer_data = []
    for layer, info in layer_perf.items():
        if info['high_score_trades'] >= 5 or info['low_score_trades'] >= 5:
            layer_data.append({
                'Layer': layer,
                'High Trades': info['high_score_trades'],
                'High WR': info['high_win_rate'] if info['high_win_rate'] is not None else '-',
                'Low Trades': info['low_score_trades'],
                'Low WR': info['low_win_rate'] if info['low_win_rate'] is not None else '-',
                'Predictive Power': info['predictive_power'] if info['predictive_power'] is not None else '-'
            })
    if layer_data:
        df_layer = pd.DataFrame(layer_data)
        df_layer = df_layer.sort_values('Predictive Power', ascending=False, na_position='last')
        st.dataframe(df_layer, use_container_width=True, hide_index=True)

        underperforming = [l for l, info in layer_perf.items()
                           if info['predictive_power'] is not None
                           and info['predictive_power'] < 5
                           and info['high_score_trades'] >= 10]
        if underperforming:
            st.warning("[WARN] Underperforming layers (low predictive power):")
            st.write(", ".join(underperforming))
            st.caption("Consider reducing weight or removing these layers.")
    else:
        st.info("Need more signals with resolved outcomes to compute layer stats.")
else:
    st.info("No layer data yet.")

st.markdown("---")
st.subheader("[RECENT] Recent Signals (with outcomes)")
if stats['recent_signals']:
    recent_data = []
    for s in stats['recent_signals']:
        recent_data.append({
            'Date': s['timestamp'][:10],
            'Symbol': s['symbol'],
            'Direction': s['direction'].upper(),
            'Grade': s['grade'],
            'Score': str(round(s['score'])) if s['score'] else '-',
            'Entry': '$' + ('%.2f' % s['entry_price']) if s['entry_price'] else '-',
            'Ret 5d': ('%+.2f' % s['return_5d']) + '%' if s['return_5d'] is not None else '-',
            'Ret 10d': ('%+.2f' % s['return_10d']) + '%' if s['return_10d'] is not None else '-',
            'Win 5d': '[WIN]' if s['win_5d'] else '[LOSS]' if s['win_5d'] is False else '-',
            'Regime': s['regime'] or '-',
            'Sector': s['sector'] or '-',
        })
    df_recent = pd.DataFrame(recent_data)
    st.dataframe(df_recent, use_container_width=True, hide_index=True)
else:
    st.info("No resolved signals yet. Wait 5+ days after scanning.")

st.markdown("---")
st.caption("[NOTE] Outcomes auto-update each page visit. "
            "DB at signal_outcomes.db. 5d/10d outcomes from yfinance prices.")