"""
OPG Dashboard — Opening Price Gap Scanner & Historical Backtest
"""
import streamlit as st
import pandas as pd
from analysis.opg_engine import OPGDetector, OPGDatabase
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="OPG Scanner", page_icon="📊", layout="wide")
st.title("📊 Opening Price Gap (OPG) Scanner")
st.caption("Detect market-opening gaps, classify signals, and backtest historical performance")

DEFAULT_SYMBOLS = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B",
                   "LLY","AVGO","JPM","XOM","UNH","V","PG","MA","COST","JNJ",
                   "HD","WMT","ABBV","NFLX","BAC","MRK","KO","PEP","CVX","AMD",
                   "TMUS","ADBE","WFC","MCD","DIS","CRM","CSCO","ACN","ABT"]

detector = OPGDetector()
db = OPGDatabase()

with st.sidebar:
    st.header("⚙️ OPG Settings")
    symbols_input = st.text_input("Stock Symbols (comma)", ",".join(DEFAULT_SYMBOLS[:20]),
                                   key="opg_symbols")
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    scan_btn = st.button("🔍 Scan Today's Gaps", type="primary", use_container_width=True)
    st.markdown("---")
    btest_sym = st.text_input("Backtest Symbol", "SPY")
    btest_btn = st.button("📊 Run OPG Backtest")
    st.markdown("---")
    stats = db.get_stats()
    if stats:
        st.metric("Total Gaps Recorded", stats.get('total', 0))
        st.metric("Gap Ups / Downs", f"{stats.get('gap_ups',0)} / {stats.get('gap_downs',0)}")
        st.metric("Fill Rate", f"{stats.get('fill_rate',0)}%")

if scan_btn and symbols:
    with st.spinner(f"Scanning {len(symbols)} stocks..."):
        results = detector.scan(symbols)
    if results:
        st.success(f"Found {len(results)} gaps today")
        df = pd.DataFrame(results)
        cols = ['symbol','gap_type','gap_pct','vol_ratio','signal','score']
        df_display = df[[c for c in cols if c in df.columns]]
        df_display.columns = [c.title() for c in df_display.columns]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        fig = go.Figure()
        gap_pos = [r for r in results if r['gap_pct'] > 0]
        gap_neg = [r for r in results if r['gap_pct'] < 0]
        if gap_pos:
            fig.add_trace(go.Bar(x=[r['symbol'] for r in gap_pos], y=[r['gap_pct'] for r in gap_pos],
                                name='Gap Up', marker_color='green'))
        if gap_neg:
            fig.add_trace(go.Bar(x=[r['symbol'] for r in gap_neg], y=[r['gap_pct'] for r in gap_neg],
                                name='Gap Down', marker_color='red'))
        fig.update_layout(title="Today's Gaps (%)", template='plotly_dark', height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No significant gaps detected today")

if btest_btn and btest_sym:
    with st.spinner(f"Backtesting {btest_sym}..."):
        bt = detector.backtest(btest_sym, period='1y')
    if 'error' in bt:
        st.error(bt['error'])
    else:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Trades", bt['total_trades'])
        c2.metric("Win Rate", f"{bt['win_rate']}%")
        c3.metric("Avg Win", f"+{bt['avg_win']}%")
        c4.metric("Avg Loss", f"-{bt['avg_loss']}%")
        if bt.get('trades'):
            tdf = pd.DataFrame(bt['trades'])
            st.dataframe(tdf, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("📋 Historical Gap Database")
history = db.get_history(limit=30)
if history:
    hdf = pd.DataFrame(history)
    cols = ['symbol','date','gap_pct','gap_type','signal','score']
    st.dataframe(hdf[[c for c in cols if c in hdf.columns]], use_container_width=True, hide_index=True)
else:
    st.info("No gap history yet. Run a scan to populate the database.")