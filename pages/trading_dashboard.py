"""
Unified Trading Dashboard -- simplified 8-composite-layer scoring system
Replaces 4 separate dashboards with one simple, clean interface.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from analysis.composite_scorer import score_symbol, COMPOSITE_NAMES
from analysis.intraday import get_market_session

st.set_page_config(page_title="Trading Dashboard", page_icon="🎯", layout="wide")
st.title("🎯 Trading Dashboard")
st.caption("Simplified 8-composite scoring (0-100). One number per stock.")

DEFAULT_SYMBOLS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "NFLX",
    "CRM", "ORCL", "ADBE", "AVGO", "JPM", "BAC", "WFC", "GS",
    "XOM", "CVX", "COP", "SLB", "JNJ", "LLY", "PFE", "MRK",
    "WMT", "COST", "HD", "NKE", "MCD", "SBUX",
    "AMD", "INTC", "QCOM", "MU", "PLTR", "DIS",
]


# ---- Sidebar ----
with st.sidebar:
    st.header("Settings")
    direction = st.radio("Direction", ["Long", "Short"], index=0)
    direction_key = "long" if direction == "Long" else "short"
    symbols_input = st.text_input(
        "Symbols (comma-separated)",
        ",".join(DEFAULT_SYMBOLS),
        key="td_symbols"
    )
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()][:30]
    max_stocks = st.slider("Max stocks", 5, 30, 15, 5)
    analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

# ---- Session banner ----
session = get_market_session()
session_emoji = {"PRE_MARKET": "[PM]", "REGULAR_MARKET": "[LIVE]", "AFTER_HOURS": "[AH]", "CLOSED": "[--]"}.get(session, "")
st.info(f"{session_emoji} {session}", icon="Time")



# ---- Analyze button ----
if analyze_btn or 'td_results' not in st.session_state:
    results = []
    progress = st.progress(0)
    status = st.empty()
    total = min(len(symbols), max_stocks)
    for i, sym in enumerate(symbols[:max_stocks]):
        status.text("Analyzing " + sym + " (" + str(i+1) + "/" + str(total) + ")...")
        try:
            r = score_symbol(sym, direction=direction_key)
            if 'error' not in r:
                results.append(r)
        except Exception as e:
            pass
        progress.progress((i + 1) / total)
    progress.empty()
    status.empty()
    st.session_state.td_results = results
    st.session_state.td_last_run = datetime.now().strftime("%H:%M:%S")

results = st.session_state.get('td_results', [])
if not results:
    st.info("Click **Analyze** to scan your watchlist.")
    st.stop()

# ---- Sort by composite score (descending) ----
results = sorted(results, key=lambda x: x.get('total', 0), reverse=True)

# ---- Top metrics ----
col1, col2, col3, col4, col5 = st.columns(5)
buy_count = sum(1 for r in results if r.get('signal') == 'BUY')
hold_count = sum(1 for r in results if r.get('signal') == 'HOLD')
sell_count = sum(1 for r in results if r.get('signal') == 'SELL')
a_plus = sum(1 for r in results if r.get('grade') == 'A+')
col1.metric("Stocks", len(results))
col2.metric("BUY", buy_count, delta_color="normal")
col3.metric("HOLD", hold_count, delta_color="off")
col4.metric("SELL", sell_count, delta_color="inverse")
col5.metric("A+ Setups", a_plus)
st.caption("Last scan: " + st.session_state.get('td_last_run', ''))
st.markdown("---")



# ---- Results table (8 columns: Symbol, Signal, Score, Grade, Entry, Target, Stop, Notes) ----
st.subheader("Results (sorted by composite score)")
table_data = []
for r in results:
    sig = r.get('signal', 'HOLD')
    sig_emoji = "[BUY]" if sig == 'BUY' else "[SELL]" if sig == 'SELL' else "[--]"
    score = r.get('total', 0)
    grade = r.get('grade', 'D')
    grade_emoji = "[A+]" if grade == 'A+' else "[A]" if grade == 'A' else "[B]" if grade == 'B' else "[C]" if grade == 'C' else "[D]"
    price = r.get('current_price')
    entry = r.get('entry')
    target = r.get('target')
    stop = r.get('stop_loss')
    rr = r.get('risk_reward', 0)
    table_data.append({
        'Symbol': r.get('symbol'),
        'Signal': sig_emoji + " " + sig,
        'Score': ('%.1f' % score) + '/100',
        'Grade': grade_emoji + " " + grade,
        'Price': ('$' + ('%.2f' % price)) if price else "-",
        'Entry': ('$' + ('%.2f' % entry)) if entry else "-",
        'Target': ('$' + ('%.2f' % target)) if target else "-",
        'Stop': ('$' + ('%.2f' % stop)) if stop else "-",
        'R:R': (('%.1f' % rr) + 'x') if rr else "-",
        'Notes': r.get('notes', '') or "-",
    })

df = pd.DataFrame(table_data)

def color_signal(val):
    if 'BUY' in str(val):
        return 'background-color: #d4edda; color: #155724; font-weight: bold'
    elif 'SELL' in str(val):
        return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
    return ''

def color_score(val):
    try:
        s = float(str(val).split('/')[0])
        if s >= 85:
            return 'background-color: #28a745; color: white; font-weight: bold'
        elif s >= 75:
            return 'background-color: #5cb85c; color: white; font-weight: bold'
        elif s >= 60:
            return 'background-color: #ffc107; color: black'
        elif s >= 40:
            return 'background-color: #fd7e14; color: white'
        else:
            return 'background-color: #dc3545; color: white'
    except Exception:
        return ''

styled = df.style.map(color_signal, subset=['Signal']).map(color_score, subset=['Score'])
st.dataframe(styled, use_container_width=True, hide_index=True, height=400)

# ---- CSV export ----
csv = df.to_csv(index=False)
st.download_button(
    label="Download Results CSV",
    data=csv,
    file_name="trading_dashboard.csv",
    mime="text/csv",
)



# ---- Top 5 stocks with composite breakdown ----
st.markdown("---")
st.subheader("Top 5 Setups -- Composite Breakdown")
top5 = results[:5]
cols = st.columns(min(5, len(top5)))
for i, r in enumerate(top5):
    if i >= 5:
        break
    with cols[i]:
        symbol = r.get('symbol', 'N/A')
        total = r.get('total', 0)
        grade = r.get('grade', 'D')
        sig = r.get('signal', 'HOLD')
        notes = r.get('notes', '-')
        st.markdown("### " + symbol)
        st.markdown("**" + sig + "** | " + grade)
        st.metric("Composite", ('%.1f' % total) + "/100")
        if notes:
            st.caption(notes)
        with st.expander("Composites", expanded=False):
            for cname, cdata in r.get('composites', {}).items():
                bar_len = int(cdata['pct'] / 10)
                bar = "#" * bar_len
                st.caption(COMPOSITE_NAMES.get(cname, cname) + ": " + ('%.1f' % cdata['score']) + "/15  " + bar)

# ---- Footer: link to advanced view ----
st.markdown("---")
st.caption("Advanced views: pages/swing_trading.py | pages/signal_dashboard.py | pages/opg_dashboard.py | pages/earnings_trader.py")
