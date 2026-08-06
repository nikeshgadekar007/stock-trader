"""
Backtest Dashboard — Validate Your 17-Layer Scoring System
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from analysis.backtest_engine import BacktestEngine
from analysis.confluence_scorer import ConfluenceScorer

st.set_page_config(page_title="Backtest", page_icon="🧪", layout="wide")
st.title("🧪 Strategy Backtester")
st.caption("Validate your 17-layer scoring system against historical data")

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "SPY",
                    "LLY", "AVGO", "JPM", "XOM", "UNH", "V", "PG", "MA", "COST"]

with st.sidebar:
    st.header("⚙️ Backtest Settings")
    symbol = st.text_input("Stock Symbol", "SPY", help="US stock tobacktest")
    period = st.selectbox("Data Period", ["1y", "2y", "3y", "5y"], index=1)
    min_score = st.slider("Minimum Score to Enter", 80, 180, 108, 2,
                          help="Only trades with score >= threshold")
    holding_days = st.select_slider("Holding Period (Days)", options=[3, 5, 7, 10, 15, 20, 30], value=10)
    max_positions = st.slider("Max Concurrent Positions", 1, 10, 3)
    st.markdown("---")
    st.markdown("### 📊 Score Guide")
    st.markdown("| Score | Grade |")
    st.markdown("|-------|-------|")
    st.markdown("| 162-180 | A+ |")
    st.markdown("| 144-161 | A |")
    st.markdown("| 126-143 | B |")
    st.markdown("| 108-125 | C |")
    run_btn = st.button("🚀 Run Backtest", type="primary", use_container_width=True)
    st.markdown("---")
    multistock = st.checkbox("🔬 Multi-Stock Scan")
    if multistock:
        symbols_input = st.text_input("Stocks (comma)", ",".join(DEFAULT_SYMBOLS[:10]))
        symbols_list = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

if run_btn:
    engine = BacktestEngine()
    if st.session_state.get('multistock', False):
        stocks = symbols_list
    else:
        stocks = [symbol]

    results = []
    progress = st.progress(0)
    status = st.empty()

    for i, sym in enumerate(stocks):
        status.text(f"🔍 Backtesting {sym}...")
        r = engine.run(sym, period=period, min_score=min_score,
                       holding_days=holding_days, max_positions=max_positions)
        results.append(r)
        progress.progress((i + 1) / len(stocks))

    status.text("✅ Done")
    progress.empty()

    for r in results:
        if 'error' in r:
            st.error(f"❌ {r.get('symbol', '?')}: {r['error']}")
            continue

        st.subheader(f"📈 {r['symbol']} ({r['period']})")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Total Trades", r['total_trades'])
        c2.metric("Win Rate", f"{r['win_rate']}%")
        c3.metric("Avg Win", f"+{r['avg_win_pct']}%")
        c4.metric("Avg Loss", f"-{r['avg_loss_pct']}%")
        c5.metric("Expectancy", f"{r['expectancy_pct']}%")
        c6.metric("Max Drawdown", f"-{r['max_drawdown_pct']}%")

        st.markdown(f"💰 **Total Return:** {r['total_return_pct']}%  |  📊 **Profit Factor:** {r['profit_factor']}")

        # Equity curve
        if r.get('equity'):
            eq_df = pd.DataFrame(r['equity'])
            eq_df['date'] = pd.to_datetime(eq_df['date'])
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Scatter(x=eq_df['date'], y=eq_df['equity'],
                                      name='Equity', line=dict(color='green', width=2)),
                          row=1, col=1)
            peak = eq_df['equity'].cummax()
            dd = (eq_df['equity'] - peak) / peak * 100
            fig.add_trace(go.Scatter(x=eq_df['date'], y=dd,
                                      fill='tozeroy', name='Drawdown %',
                                      line=dict(color='red', width=1)),
                          row=2, col=1)
            fig.update_layout(height=400, template='plotly_dark',
                              hovermode='x unified', margin=dict(l=0, r=0, t=10, b=0))
            fig.update_yaxes(title_text="Equity ($)", row=1, col=1)
            fig.update_yaxes(title_text="Drawdown %", row=2, col=1)
            st.plotly_chart(fig, use_container_width=True)

        # Trade log
        if r.get('trades'):
            with st.expander(f"📋 Trade Log ({len(r['trades'])} trades)"):
                trades_df = pd.DataFrame(r['trades'])
                trades_df['pnl_color'] = trades_df['pnl_pct'].apply(
                    lambda x: f"+{x}%" if x > 0 else f"−{abs(x)}%" if x < 0 else "0%"
                )
                st.dataframe(trades_df[['entry_date', 'exit_date', 'entry_price',
                                         'exit_price', 'pnl_color', 'score', 'days_held']],
                             use_container_width=True, hide_index=True)

        st.markdown("---")
