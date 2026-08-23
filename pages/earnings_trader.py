"""
Earnings Trader Page - Calendar, Pre-Earnings Watchlist, Post-Earnings Reaction Scanner
5-Layer Earnings Engine + visual dashboard
"""
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from analysis.earnings_engine import EarningsEngine

st.set_page_config(page_title="Earnings Trader", page_icon="📅", layout="wide")
st.title("📅 Earnings Trader - Calendar & Reaction Scanner")
st.caption("5-layer earnings engine: Beat Streak | Surprise % | Estimate Revisions | IV Crush | Window Risk")

# Default watchlist (mega-caps with frequent earnings)
DEFAULT_SYMBOLS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "NFLX",
    "CRM", "ORCL", "ADBE", "AVGO", "JPM", "BAC", "WFC", "GS",
    "XOM", "CVX", "COP", "SLB",
    "JNJ", "LLY", "PFE", "MRK", "ABBV", "UNH",
    "WMT", "COST", "HD", "NKE", "MCD", "SBUX",
    "AMD", "INTC", "QCOM", "TXN", "MU", "PLTR",
    "DIS", "T", "TMUS", "CMCSA",
    "BA", "CAT", "GE", "HON", "UPS",
    "SPGI", "BLK", "SCHW", "AXP", "V", "MA",
    "PANW", "SHOP", "SQ", "PYPL", "UBER",
    "ABNB", "ETSY", "RBLX", "SNAP", "PINS",
    "F", "GM", "RIVN", "LCID", "NIO",
    "PFE", "BMY", "GILD", "AMGN", "REGN",
]


# ---- Sidebar settings ----
with st.sidebar:
    st.header("📅 Earnings Settings")
    symbols_input = st.text_input(
        "Stock symbols (comma-separated)",
        ",".join(DEFAULT_SYMBOLS[:30]),
        key="earnings_symbols"
    )
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    max_symbols = st.slider("Max stocks to scan", 5, 100, 30, 5)
    scan_btn = st.button("🔍 Scan Earnings", type="primary", use_container_width=True)
    st.markdown("---")
    st.markdown("### 🎯 Window Filter")
    window_filter = st.selectbox(
        "Show only:",
        ["All stocks", "Pre-Earnings (1-7 days)", "Post-Earnings Drift (1-5 days ago)", "Day-of Earnings"],
    )
    st.markdown("---")
    st.caption("""
**Strategy Tips:**

🟢 **Pre-Earnings Avoid**: Stocks reporting in 1-3 days. Binary event risk.

📈 **Post-Earnings Drift**: Stocks that reported in last 5 days. Academic edge ~65-70%.

💎 **IV Crush Play**: High IV before earnings = opportunity for premium sellers (avoid option buys).

🎯 **Beat Streak**: 4+ consecutive beats = strong momentum signal.

💥 **Surprise Magnitude**: Avg surprise >5% = consistent underestimation.
""")


# ---- Main scanner function ----
def scan_earnings(symbols, _bust_cache=False):
    """Scan symbols for earnings data. Returns list of dicts."""
    results = []
    for sym in symbols:
        try:
            t = yf.Ticker(sym)
            cal = None
            next_earnings = None
            eps_avg = None
            rev_avg = None
            try:
                cal = t.calendar
                if cal and isinstance(cal, dict):
                    ed_list = cal.get('Earnings Date', [])
                    if ed_list and len(ed_list) > 0:
                        next_earnings = ed_list[0]
                    eps_avg = cal.get('Earnings Average')
                    rev_avg = cal.get('Revenue Average')
            except Exception:
                pass
            # Days until
            days_until = None
            if next_earnings is not None:
                if hasattr(next_earnings, 'date'):
                    ned = next_earnings.date()
                else:
                    ned = next_earnings
                days_until = (ned - datetime.now().date()).days
            # Get current price
            try:
                hist = t.history(period='5d', auto_adjust=True)
                price = float(hist['Close'].iloc[-1]) if not hist.empty else None
            except Exception:
                price = None
            # Run 5 earnings layers
            beat = EarningsEngine.beat_streak(sym)
            surprise = EarningsEngine.surprise_magnitude(sym)
            revisions = EarningsEngine.estimate_revisions(sym)
            iv = EarningsEngine.iv_crush_signal(sym)
            window = EarningsEngine.earnings_window_risk(sym)
            results.append({
                'Symbol': sym,
                'Price': price,
                'Next Earnings': next_earnings,
                'Days Until': days_until,
                'EPS Estimate': eps_avg,
                'Revenue Estimate': rev_avg,
                'Beat Streak': beat.get('streak', 0),
                'Beat Type': beat.get('streak_type', ''),
                'Beat Rate %': beat.get('beat_rate', 0),
                'Avg Surprise %': surprise.get('avg_surprise_pct', 0),
                'Estimate Revision %': revisions.get('revision_pct', 0),
                'IV Ratio': iv.get('iv_ratio', None),
                'IV Signal': iv.get('signal', ''),
                'Window': window.get('window', ''),
                'Days Until Earn': window.get('days_until_earnings', None),
                'Window Score': window.get('score', 5),
                'Total Score': (
                    beat.get('score', 5) + surprise.get('score', 5) +
                    revisions.get('score', 5) + iv.get('score', 5) +
                    window.get('score', 5)
                ),
                'Beat Signal': beat.get('signal', ''),
                'Surprise Signal': surprise.get('signal', ''),
                'Revision Signal': revisions.get('signal', ''),
            })
        except Exception as e:
            results.append({
                'Symbol': sym, 'Error': str(e), 'Total Score': 25,
                'Window': 'ERROR', 'Days Until Earn': None,
            })
    return results


# ---- Run scan when button is clicked or symbols change ----
# Cache buster ensures we don't return stale results
import time as _time
_scan_cache_buster = int(_time.time())
if scan_btn or 'earnings_results' not in st.session_state:
    with st.spinner("Scanning " + str(min(len(symbols), max_symbols)) + " stocks for earnings data... (may take 30-60 seconds)"):
        scanned = scan_earnings(symbols[:max_symbols], _bust_cache=_scan_cache_buster)
        st.session_state.earnings_results = scanned
        st.session_state.last_scanned_symbols = symbols[:max_symbols]
        st.session_state.last_scan_time = _time.strftime("%H:%M:%S")
        if not scanned:
            st.warning("Scan returned no results. Check that your symbols are valid US tickers.")

results = st.session_state.get('earnings_results', [])
if not results:
    st.info("Click 'Scan Earnings' to analyze your watchlist.")
    st.stop()

df = pd.DataFrame(results)

# Apply window filter
if window_filter == "Pre-Earnings (1-7 days)":
    df = df[df['Days Until Earn'].between(1, 7, inclusive="both")]
elif window_filter == "Post-Earnings Drift (1-5 days ago)":
    df = df[df['Days Until Earn'].between(-5, -1, inclusive="both")]
elif window_filter == "Day-of Earnings":
    df = df[df['Days Until Earn'] == 0]

if df.empty:
    st.info(f"No stocks match filter: {window_filter}")
    st.stop()

# ---- Summary metrics ----
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Stocks Scanned", len(results))
col2.metric("Pre-Earnings (1-3d)", int(((df['Days Until Earn'] >= 1) & (df['Days Until Earn'] <= 3)).sum()))
col3.metric("Post-Earnings Drift", int(((df['Days Until Earn'] >= -5) & (df['Days Until Earn'] <= -1)).sum()))
col4.metric("Day-of Earnings", int((df['Days Until Earn'] == 0).sum()))
col5.metric("Avg Total Score", f"{df['Total Score'].mean():.1f}/50")

st.markdown("---")


# ---- Section 1: Earnings Calendar ----
st.subheader("📅 Earnings Calendar")

cal_df = df[['Symbol', 'Next Earnings', 'Days Until Earn', 'EPS Estimate', 'Revenue Estimate', 'Window']].copy()
if not cal_df.empty:
    cal_df = cal_df.dropna(subset=['Next Earnings']).sort_values('Days Until Earn')
    # Format EPS / Revenue
    def fmt_money(v):
        if pd.isna(v) or v is None:
            return "-"
        if v >= 1e9:
            return f"${v/1e9:.1f}B"
        if v >= 1e6:
            return f"${v/1e6:.0f}M"
        return f"${v:.2f}"
    cal_df['EPS Estimate'] = cal_df['EPS Estimate'].apply(fmt_money)
    cal_df['Revenue Estimate'] = cal_df['Revenue Estimate'].apply(fmt_money)

    def window_badge(w):
        if 'PRE' in str(w):
            return '🚫 ' + str(w)
        if 'POST' in str(w):
            return '📈 ' + str(w)
        if 'DAY' in str(w):
            return '⚠️ ' + str(w)
        return str(w)
    cal_df['Window'] = cal_df['Window'].apply(window_badge)
    cal_df.columns = ['Symbol', 'Date', 'Days Until', 'EPS Est', 'Rev Est', 'Status']
    st.dataframe(cal_df, use_container_width=True, hide_index=True)
else:
    st.info("No earnings calendar data available")

st.markdown("---")

# ---- Section 2: 5-Layer Scoring Table ----
st.subheader("🎯 5-Layer Earnings Score Breakdown")

score_df = df[['Symbol', 'Price', 'Days Until Earn', 'Beat Streak', 'Beat Type',
               'Avg Surprise %', 'Estimate Revision %', 'IV Ratio',
               'Total Score', 'Window']].copy()
score_df = score_df.sort_values('Total Score', ascending=False).reset_index(drop=True)

# Format columns
score_df['Avg Surprise %'] = score_df['Avg Surprise %'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "-")
score_df['Estimate Revision %'] = score_df['Estimate Revision %'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "-")
score_df['IV Ratio'] = score_df['IV Ratio'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
score_df['Price'] = score_df['Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "-")
score_df['Beat Streak'] = score_df.apply(
    lambda r: f"{int(r['Beat Streak'])} ({r['Beat Type']})" if r['Beat Streak'] > 0 else "0",
    axis=1
)

# Add rank column
score_df.insert(0, 'Rank', range(1, len(score_df) + 1))
st.dataframe(score_df, use_container_width=True, hide_index=True)


# ---- Section 3: Pre-Earnings Watchlist (1-3 days) ----
st.markdown("---")
st.subheader("🚫 Pre-Earnings Blackout (1-3 days) - AVOID THESE")
pre_df = df[(df['Days Until Earn'] >= 1) & (df['Days Until Earn'] <= 3)].copy()
pre_df = pre_df.sort_values('Days Until Earn')
if not pre_df.empty:
    pre_display = pre_df[['Symbol', 'Next Earnings', 'Days Until Earn', 'Beat Streak', 'Avg Surprise %', 'IV Signal']].copy()
    pre_display['Avg Surprise %'] = pre_display['Avg Surprise %'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "-")
    pre_display['Next Earnings'] = pre_display['Next Earnings'].astype(str)
    st.dataframe(pre_display, use_container_width=True, hide_index=True)
    st.warning(f"⚠️ {len(pre_df)} stock(s) reporting in 1-3 days. Binary event risk — avoid directional trades.")
else:
    st.success("✅ No stocks reporting in next 3 days. Clear to trade normally.")

# ---- Section 4: Post-Earnings Drift Window ----
st.markdown("---")
st.subheader("📈 Post-Earnings Drift (1-5 days ago) - ACADEMIC EDGE")
post_df = df[(df['Days Until Earn'] >= -5) & (df['Days Until Earn'] <= -1)].copy()
post_df = post_df.sort_values('Days Until Earn', ascending=False)
if not post_df.empty:
    post_display = post_df[['Symbol', 'Next Earnings', 'Days Until Earn', 'Beat Streak', 'Beat Type',
                            'Avg Surprise %', 'Estimate Revision %', 'Total Score']].copy()
    post_display['Avg Surprise %'] = post_display['Avg Surprise %'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "-")
    post_display['Estimate Revision %'] = post_display['Estimate Revision %'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "-")
    post_display['Next Earnings'] = post_display['Next Earnings'].astype(str)
    post_display.columns = ['Symbol', 'Reported On', 'Days Since', 'Beat Streak', 'Beat Type',
                             'Surprise %', 'Rev %', 'Total']
    st.dataframe(post_display, use_container_width=True, hide_index=True)
    st.info(f"📊 {len(post_df)} stock(s) in drift window. Look for beat-streak ≥ 3 + surprise ≥ 5%.")
else:
    st.info("No stocks in post-earnings drift window right now.")

# ---- Section 5: Top Setups ----
st.markdown("---")
st.subheader("🏆 Top Earnings Setups (Total Score)")

top_df = df.sort_values('Total Score', ascending=False).head(10).copy()
top_display = top_df[['Symbol', 'Price', 'Days Until Earn', 'Beat Streak', 'Avg Surprise %',
                       'Estimate Revision %', 'IV Ratio', 'Total Score']].copy()
top_display['Price'] = top_display['Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "-")
top_display['Avg Surprise %'] = top_display['Avg Surprise %'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "-")
top_display['Estimate Revision %'] = top_display['Estimate Revision %'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "-")
top_display['IV Ratio'] = top_display['IV Ratio'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")

for _, row in top_display.iterrows():
    score = row['Total Score']
    if score >= 40:
        badge = "🏆 A++"
        color = "🟢"
    elif score >= 35:
        badge = "✅ A+"
        color = "🟢"
    elif score >= 28:
        badge = "🟡 B"
        color = "🟡"
    else:
        badge = "⚪ C"
        color = "⚪"
    days = row['Days Until Earn']
    if days is not None and days <= 3 and days >= 0:
        warning = " ⚠️ PRE-EARNINGS"
    elif days is not None and days == 0:
        warning = " ⚠️ DAY-OF"
    elif days is not None and days < 0 and days >= -5:
        warning = " 📈 POST-EARNINGS DRIFT"
    else:
        warning = ""
    with st.expander(f"{color} {row['Symbol']} — Score: {score}/50 {badge}{warning}", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Days Until Earn", days if days is not None else "N/A")
        c2.metric("Beat Streak", int(row['Beat Streak']))
        c3.metric("Avg Surprise", row['Avg Surprise %'])
        c4.metric("IV Ratio", row['IV Ratio'])

# CSV export
csv = df.to_csv(index=False)
st.download_button(
    label="📥 Download Full Earnings Report CSV",
    data=csv,
    file_name="earnings_scan.csv",
    mime="text/csv",
)
