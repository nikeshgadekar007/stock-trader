"""
Unified Trading Dashboard - simplified 8-composite scoring (0-100).
Hardened against runtime errors.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from analysis.composite_scorer import score_symbol, COMPOSITE_NAMES
from analysis.intraday import get_market_session

st.set_page_config(page_title="Trading Dashboard", page_icon="[TD]", layout="wide")

DEFAULT_SYMBOLS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "NFLX",
    "CRM", "ORCL", "ADBE", "AVGO", "JPM", "BAC", "WFC", "GS",
    "XOM", "CVX", "JNJ", "LLY", "WMT", "COST", "HD", "MCD",
    "AMD", "INTC", "QCOM", "MU", "DIS",
]

st.markdown("# Trading Dashboard")
st.caption("Simplified 8-composite scoring (0-100). One number per stock.")

with st.sidebar:
    st.header("Settings")
    direction = st.radio("Direction", ["Long", "Short"], index=0, key="td_dir")
    direction_key = "long" if direction == "Long" else "short"
    default_text = ",".join(DEFAULT_SYMBOLS)
    symbols_input = st.text_input("Symbols", default_text, key="td_sym")
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()][:30]
    max_stocks = st.slider("Max stocks", 5, 30, 15, 5, key="td_max")
    analyze_btn = st.button("Analyze", type="primary", use_container_width=True, key="td_btn")

try:
    session = get_market_session()
    s_emoji = {"PRE_MARKET": "[PM]", "REGULAR_MARKET": "[LIVE]", "AFTER_HOURS": "[AH]", "CLOSED": "[--]"}.get(session, "")
    st.info(s_emoji + " " + session)
except Exception:
    pass

if analyze_btn or ('td_results' not in st.session_state):
    results = []
    try:
        progress = st.progress(0)
        status = st.empty()
        total = min(len(symbols), max_stocks)
        for i, sym in enumerate(symbols[:max_stocks]):
            status.text("Analyzing " + sym + " (" + str(i+1) + "/" + str(total) + ")...")
            try:
                r = score_symbol(sym, direction=direction_key)
                if isinstance(r, dict) and 'error' not in r:
                    results.append(r)
            except Exception:
                pass
            progress.progress((i + 1) / max(total, 1))
        progress.empty()
        status.empty()
        st.session_state.td_results = results
        st.session_state.td_last_run = datetime.now().strftime("%H:%M:%S")
        if not results:
            st.warning("Scan returned no results. Check that your symbols are valid US tickers.")
    except Exception as e:
        st.error("Scan error: " + str(e))

results = st.session_state.get('td_results', [])

if not results:
    st.info("Click **Analyze** in the sidebar to scan your watchlist.")
else:
    results = sorted(results, key=lambda x: x.get('total', 0) or 0, reverse=True)

    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    b_count = sum(1 for r in results if r.get('signal') == 'BUY')
    h_count = sum(1 for r in results if r.get('signal') == 'HOLD')
    s_count = sum(1 for r in results if r.get('signal') == 'SELL')
    ap_count = sum(1 for r in results if r.get('grade') == 'A+')
    c1.metric("Stocks", len(results))
    c2.metric("BUY", b_count)
    c3.metric("HOLD", h_count)
    c4.metric("SELL", s_count)
    c5.metric("A+", ap_count)
    st.subheader("Results (sorted by composite score)")
    rows = []
    for r in results:
        try:
            sig = r.get('signal', 'HOLD')
            sig_e = '[BUY]' if sig == 'BUY' else '[SELL]' if sig == 'SELL' else '[--]'
            sc = r.get('total', 0)
            gr = r.get('grade', 'D')
            gr_e = '[A+]' if gr == 'A+' else '[A]' if gr == 'A' else '[B]' if gr == 'B' else '[C]' if gr == 'C' else '[D]'
            pr = r.get('current_price')
            en = r.get('entry')
            tg = r.get('target')
            stp = r.get('stop_loss')
            rr = r.get('risk_reward', 0)
            rows.append({
                'Symbol': str(r.get('symbol', '')),
                'Signal': sig_e + ' ' + sig,
                'Score': '%.1f' % sc + '/100',
                'Grade': gr_e + ' ' + gr,
                'Price': ('$' + '%.2f' % pr) if pr else '-',
                'Entry': ('$' + '%.2f' % en) if en else '-',
                'Target': ('$' + '%.2f' % tg) if tg else '-',
                'Stop': ('$' + '%.2f' % stp) if stp else '-',
                'R:R': ('%.1f' % rr + 'x') if rr else '-',
                'Notes': r.get('notes', '') or '-',
            })
        except Exception:
            continue

    if rows:
        df = pd.DataFrame(rows)
        try:
            def _csig(val):
                if 'BUY' in str(val):
                    return 'background-color: #d4edda; color: #155724; font-weight: bold'
                if 'SELL' in str(val):
                    return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
                return ''
            def _csc(val):
                try:
                    s = float(str(val).split('/')[0])
                    if s >= 85:
                        return 'background-color: #28a745; color: white; font-weight: bold'
                    if s >= 75:
                        return 'background-color: #5cb85c; color: white'
                    if s >= 60:
                        return 'background-color: #ffc107; color: black'
                    if s >= 40:
                        return 'background-color: #fd7e14; color: white'
                    return 'background-color: #dc3545; color: white'
                except Exception:
                    return ''
            styled = df.style.map(_csig, subset=['Signal']).map(_csc, subset=['Score'])
            st.dataframe(styled, use_container_width=True, hide_index=True, height=400)
        except Exception:
            st.dataframe(df, use_container_width=True, hide_index=True, height=400)
        try:
            st.download_button('Download CSV', df.to_csv(index=False), 'trading_dashboard.csv', 'text/csv', key='td_dl')
        except Exception:
            pass

    st.markdown('---')
    st.subheader('Top 5 Setups')
    top5 = results[:5]
    if top5:
        cols = st.columns(min(5, len(top5)))
        for i, r in enumerate(top5):
            try:
                with cols[i]:
                    st.markdown('### ' + str(r.get('symbol', '')))
                    st.markdown('**' + str(r.get('signal', '')) + '** | ' + str(r.get('grade', '')))
                    st.metric('Composite', '%.1f' % r.get('total', 0) + '/100')
                    notes = r.get('notes', '')
                    if notes:
                        st.caption(notes)
                    with st.expander('Composites'):
                        for cname, cd in r.get('composites', {}).items():
                            try:
                                pct = cd.get('pct', 0)
                                sc_v = cd.get('score', 0)
                                bar = '#' * max(0, min(10, int(pct / 10)))
                                st.caption(COMPOSITE_NAMES.get(cname, cname) + ': ' + '%.1f' % sc_v + '/15  ' + bar)
                            except Exception:
                                pass
            except Exception:
                continue

    st.markdown('---')
    st.caption('Advanced views: swing_trading | signal_dashboard | opg_dashboard | earnings_trader')