"""
Swing Trading Dashboard - 17-Layer Confluence Scoring System
Only shows A+ setups (score >= 162/180) for maximum accuracy
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from analysis.confluence_scorer import ConfluenceScorer
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Swing Trading Signals", page_icon="🎯", layout="wide")

st.title("🎯 Swing Trading — A+ Setups Only")
st.caption("17-Layer Confluence Scoring System | Only trades with score ≥ 162/180 are shown")

# Auto-refresh
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
    st.session_state.refresh_interval = 120

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    trade_direction = st.radio("📈 Trade Direction", ["Long", "Short"], index=0,
                                help="Long=buy low sell high. Short=sell high buy low.")
    direction = "long" if trade_direction == "Long" else "short"
    max_score_label = 210 if direction == "short" else 190
    min_score = st.slider("Minimum Score Threshold", 60, max_score_label,
                          int(max_score_label * 0.9), 2,
                          help=f"A+ = {int(max_score_label*0.9)}+ (90% of max)")
    max_stocks = st.slider("Max Stocks to Scan", 5, 50, 20, 5)
    auto_refresh = st.checkbox("🔄 Auto-Refresh", value=st.session_state.auto_refresh,
                                help="Auto-refresh every 2 minutes")
    if auto_refresh:
        st.session_state.auto_refresh = True
        refresh_interval = st.select_slider("Interval", options=[30, 60, 120, 300], value=120)
        st.session_state.refresh_interval = refresh_interval
    else:
        st.session_state.auto_refresh = False
    
    st.markdown("---")
    st.markdown(f"### 📊 Score Guide (/{max_score_label})")
    if direction == "long":
        st.markdown("| 162-180 | A+ | STRONG BUY |\n| 144-161 | A | BUY |\n| 126-143 | B | MODERATE BUY |\n| 108-125 | C | WEAK BUY |\n| 72-107 | D | HOLD |")
    else:
        st.markdown("| 180-200 | A+ | STRONG SHORT |\n| 160-179 | A | SHORT |\n| 140-159 | B | MODERATE SHORT |\n| 120-139 | C | WEAK SHORT |\n| 80-119 | D | HOLD |")
    
    st.markdown("---")
    st.markdown("### 🎯 19 Layers")
    st.markdown("1. Trend (30) 2. S/R (15) 3. Fib (10) 4. Candle (10) 5. Momentum (10) 6. Volume (10)")
    st.markdown("7. Sentiment (10) 8. Fundamentals (10) 9. Regime (5) 10. ML (10) 11. Sector (10)")
    st.markdown("12. ATR Risk (10) 13. Earnings (10) 14. Insider (10) 15. Breakout (10)")
    st.markdown("16. Trade Mgmt (10) 17. Liquidity (10) 18. Short Int (10) 19. Bearish Div (10)")

# Default watchlist
DEFAULT_SYMBOLS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B",
    "LLY", "AVGO", "JPM", "XOM", "UNH", "V", "PG", "MA", "COST", "JNJ",
    "HD", "WMT", "ABBV", "NFLX", "BAC", "MRK", "KO", "PEP", "CVX", "AMD",
    "TMUS", "ADBE", "WFC", "MCD", "DIS", "CRM", "CSCO", "ACN", "ABT",
    "LIN", "QCOM", "IBM", "INTU", "GE", "TXN", "CAT", "AMGN", "PM",
    "AMAT", "ISRG", "AXP", "NOW", "SPGI", "UBER", "GS", "BKNG", "LOW",
    "PFE", "ETN", "UPS", "MDT", "DE", "SCHW", "HON", "UNP", "CB", "ADI",
    "COP", "NEE", "PANW", "TJX", "GILD", "SBUX", "SYK", "VRTX", "LMT",
    "MO", "MDLZ", "REGN", "PLTR", "BSX", "CI", "SO", "BLK", "MU", "KKR",
    "GEHC", "ITW", "NKE", "C", "INTC", "SHW", "T", "CVS", "EQIX", "HCA",
    "ETR", "SLB"
]

# Input
col1, col2 = st.columns([3, 1])
with col1:
    symbols_input = st.text_input(
        "Enter Stock Symbols (comma separated)",
        ",".join(DEFAULT_SYMBOLS[:max_stocks]),
        help="US Stock symbols for swing trading analysis"
    )
with col2:
    analyze_btn = st.button("🔍 Scan for A+ Setups", type="primary", use_container_width=True)

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

# Trigger auto-refresh
if st.session_state.auto_refresh:
    st_autorefresh(interval=st.session_state.refresh_interval * 1000, key="chart_refresh")

def _build_trade_chart(symbol, current_price, atr_details):
    """Build an interactive Plotly chart with trade levels"""
    if not atr_details:
        return None
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='6mo', auto_adjust=True)
        if df.empty or len(df) < 20:
            return None
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        last_n = min(len(df), 90)
        df = df.tail(last_n)
        sl_price = atr_details.get('suggested_stop', current_price * 0.95)
        hp_price = atr_details.get('half_profit_price', current_price * 1.02)
        fp_price = atr_details.get('full_profit_price', current_price * 1.04)
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.03, row_heights=[0.7, 0.3],
            subplot_titles=(f"{symbol} — Daily Chart", "Volume")
        )
        fig.add_trace(
            go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'],
                           close=df['Close'], name='Price',
                           increasing_line_color='#26a69a', decreasing_line_color='#ef5350'), row=1, col=1)
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA_20'], name='20 SMA', line=dict(color='#42a5f5', width=1)), row=1, col=1)
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA_50'], name='50 SMA', line=dict(color='#ab47bc', width=1)), row=1, col=1)
        x_range = [df.index[-1], df.index[-1] + pd.Timedelta(days=15)]
        fig.add_trace(
            go.Scatter(x=x_range, y=[sl_price, sl_price], name='Stop Loss', mode='lines',
                       line=dict(color='red', dash='dash', width=2)), row=1, col=1)
        fig.add_trace(
            go.Scatter(x=x_range, y=[hp_price, hp_price], name='Half Profit', mode='lines',
                       line=dict(color='orange', dash='dash', width=2)), row=1, col=1)
        fig.add_trace(
            go.Scatter(x=x_range, y=[fp_price, fp_price], name='Full Profit', mode='lines',
                       line=dict(color='green', dash='dash', width=2)), row=1, col=1)
        colors = ['green' if c >= o else 'red' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=colors,
                              opacity=0.5, showlegend=False), row=2, col=1)
        fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
        y_min = min(df['Low'].min(), sl_price) * 0.98
        y_max = max(df['High'].max(), fp_price) * 1.03
        fig.update_yaxes(title_text="Price ($)", row=1, col=1, range=[y_min, y_max])
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_layout(
            height=500, template='plotly_dark', hovermode='x unified',
            margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation='h', y=1.02)
        )
        return fig
    except Exception:
        return None

def _render_swing_card(result, rank):
    """Render a detailed swing trading signal card"""
    symbol = result['symbol']
    score = result['total_score']
    grade = result['grade']
    signal = result['signal']
    price = result['current_price']
    scores = result.get('scores', {})
    details = result.get('details', {})
    
    # Grade emoji
    grade_emoji = "🏆" if grade == 'A+' else "✅" if grade == 'A' else "📊" if grade == 'B' else "👀"
    
    # Score bar
    bar_length = min(score // 2, 90)
    score_bar = "█" * bar_length + "░" * (90 - bar_length)
    
    st.markdown(f"### {grade_emoji} #{rank} {symbol} — **{signal}** ({grade})")
    st.markdown(f"**Score: {score}/180**")
    st.progress(score / 180)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", f"${price:.2f}")
    with col2:
        st.metric("Total Score", f"{score}/180")
    with col3:
        st.metric("Grade", f"{grade_emoji} {grade}")
    
    # Trade levels
    atr_details = details.get('atr_risk', {})
    if atr_details:
        st.markdown("---")
        st.markdown("#### 💰 Trade Levels (ATR-Based)")
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            sl_price = atr_details.get('suggested_stop', 0)
            sl_pct = atr_details.get('stop_loss_pct', 0)
            st.metric("🛑 STOP LOSS", f"${sl_price:.2f}", delta=f"-{sl_pct}%", delta_color="inverse")
        with tc2:
            hp_price = atr_details.get('half_profit_price', 0)
            hp_pct = atr_details.get('half_profit_pct', 0)
            st.metric("🎯 HALF PROFIT (50% Exit)", f"${hp_price:.2f}", delta=f"+{hp_pct}%")
        with tc3:
            fp_price = atr_details.get('full_profit_price', 0)
            fp_pct = atr_details.get('full_profit_pct', 0)
            st.metric("🚀 FULL PROFIT (100% Exit)", f"${fp_price:.2f}", delta=f"+{fp_pct}%")
        pos_size = atr_details.get('position_size', 0)
        if pos_size > 0:
            st.caption(f"💡 Suggested position: **{pos_size} shares** for a $10k account (1% risk per trade = $100 max loss)")

    # Interactive Chart
    with st.expander("📈 Live Chart with Trade Levels", expanded=True):
        try:
            chart_fig = _build_trade_chart(symbol, price, atr_details)
            if chart_fig:
                st.plotly_chart(chart_fig, use_container_width=True)
        except Exception as e:
            st.caption(f"⚠️ Chart unavailable: {str(e)[:60]}")

    # OPG indicator
    opg_details = details.get('opg', {})
    if opg_details and opg_details.get('gap'):
        gap_color = 'green' if opg_details.get('gap_type') == 'GAP_UP' else 'red'
        st.markdown(f"📊 **Gap:** :{gap_color}[{opg_details.get('gap_pct', 0):+}%] — {opg_details.get('signal', 'N/A')} | Score: {opg_details.get('score', 0)}/10")

    # Layer breakdown
    with st.expander("📊 20-Layer Score Breakdown"):
        layers = [
            ("Multi-Timeframe Trend", "trend", 30),
            ("Support/Resistance", "support_resistance", 15),
            ("Fibonacci Levels", "fibonacci", 10),
            ("Candlestick Patterns", "candlestick", 10),
            ("Momentum Indicators", "momentum", 10),
            ("Volume Confirmation", "volume", 10),
            ("News Sentiment", "sentiment", 10),
            ("Fundamentals", "fundamentals", 10),
            ("Market Regime", "regime", 5),
            ("ML Prediction", "ml", 10),
            ("Sector Strength", "sector", 10),
            ("ATR Risk Mgmt", "atr_risk", 10),
            ("Earnings Risk", "earnings", 10),
            ("Insider Activity", "insider", 10),
            ("52-Wk Breakout", "breakout", 10),
            ("Trade Management", "trade_mgmt", 10),
            ("Liquidity", "liquidity", 10),
            ("Short Interest", "short_interest", 10),
            ("Bearish Div", "bearish_divergence", 10),
            ("OPG (Gaps)", "opg", 10),
        ]
        
        for name, key, max_pts in layers:
            pts = scores.get(key, 0)
            pct = pts / max_pts if max_pts > 0 else 0
            bar = "█" * int(pct * 20) + "░" * (20 - int(pct * 20))
            st.write(f"**{name}:** {pts}/{max_pts} |{bar}|")
    
    # Trend details
    trend_details = details.get('trend', {})
    if trend_details:
        with st.expander("📈 Trend Alignment Details"):
            for tf, status in trend_details.items():
                emoji = "🟢" if 'BULL' in status else "🔴"
                st.write(f"{emoji} **{tf}:** {status}")
    
    # Support/Resistance details
    sr_details = details.get('support_resistance', {})
    if sr_details:
        with st.expander("📐 Support/Resistance Details"):
            st.write(f"**Level:** {sr_details.get('level', 'N/A')}")
            st.write(f"**Nearest Support:** ${sr_details.get('nearest_support', 'N/A')} ({sr_details.get('support_distance_pct', 'N/A')}% away)")
            st.write(f"**Nearest Resistance:** ${sr_details.get('nearest_resistance', 'N/A')} ({sr_details.get('resistance_distance_pct', 'N/A')}% away)")
            if sr_details.get('support_tested'):
                st.write(f"**Support Tested:** {sr_details['support_tested']}")
    
    # Fibonacci details
    fib_details = details.get('fibonacci', {})
    if fib_details:
        with st.expander("📏 Fibonacci Details"):
            st.write(f"**Swing High:** ${fib_details.get('swing_high', 'N/A')}")
            st.write(f"**Swing Low:** ${fib_details.get('swing_low', 'N/A')}")
            st.write(f"**38.2%:** ${fib_details.get('fib_382', 'N/A')}")
            st.write(f"**50.0%:** ${fib_details.get('fib_500', 'N/A')}")
            st.write(f"**61.8%:** ${fib_details.get('fib_618', 'N/A')}")
            st.write(f"**78.6%:** ${fib_details.get('fib_786', 'N/A')}")
            if fib_details.get('at_level'):
                st.success(f"✅ At {fib_details['at_level']} level ({fib_details.get('distance_pct', '?')}% away)")
            elif fib_details.get('near_level'):
                st.info(f"📊 Near {fib_details['near_level']} level ({fib_details.get('distance_pct', '?')}% away)")
            if fib_details.get('confluence'):
                st.success(f"🎯 {fib_details['confluence']}")
    
    # Candlestick details
    candle_details = details.get('candlestick', {})
    if candle_details:
        with st.expander("🕯️ Candlestick Pattern Details"):
            pattern = candle_details.get('pattern', 'NONE')
            if pattern != 'NONE':
                st.success(f"✅ **{pattern}**")
            else:
                st.info("No significant pattern detected")
            patterns = candle_details.get('patterns_found', [])
            if patterns:
                st.write(f"Patterns found: {', '.join(patterns)}")
    
    # Momentum details
    mom_details = details.get('momentum', {})
    if mom_details:
        with st.expander("📊 Momentum Indicator Details"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("RSI", f"{mom_details.get('rsi', 0):.1f}", mom_details.get('rsi_zone', ''))
            with col2:
                st.metric("MACD", f"{mom_details.get('macd', 0):.3f}", mom_details.get('macd_signal', ''))
            with col3:
                st.metric("Stoch K/D", f"{mom_details.get('stoch_k', 0):.1f}/{mom_details.get('stoch_d', 0):.1f}", mom_details.get('stoch_signal', ''))
    
    # Volume details
    vol_details = details.get('volume', {})
    if vol_details:
        with st.expander("📊 Volume Confirmation Details"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Vol Ratio", f"{vol_details.get('vol_ratio', 1):.2f}x", vol_details.get('volume_level', ''))
            with col2:
                st.metric("OBV", vol_details.get('obv', 'N/A'))
            with col3:
                st.metric("Vol Trend", vol_details.get('vol_trend', 'N/A'))
    
    # Sentiment details
    sent_details = details.get('sentiment', {})
    if sent_details:
        with st.expander("📰 News Sentiment Details"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Sentiment", sent_details.get('overall', 'N/A'))
            with col2:
                st.metric("Score", f"{sent_details.get('sentiment_score', 0):.2f}")
            with col3:
                st.metric("Articles", sent_details.get('articles', 0))
    
    # Fundamentals details
    fund_details = details.get('fundamentals', {})
    if fund_details:
        with st.expander("💰 Fundamentals Details"):
            if fund_details.get('pe_ratio'):
                st.metric("P/E Ratio", f"{fund_details['pe_ratio']:.1f}", fund_details.get('pe_level', ''))
            if fund_details.get('revenue_growth'):
                st.metric("Revenue Growth", f"{fund_details['revenue_growth']:.1f}%", fund_details.get('growth', ''))
            if fund_details.get('debt_equity'):
                st.metric("Debt/Equity", f"{fund_details['debt_equity']:.1f}", fund_details.get('debt', ''))
            if fund_details.get('profit_margins'):
                st.metric("Profit Margins", f"{fund_details['profit_margins']:.1f}%", fund_details.get('margins', ''))
    
    # Regime details
    regime_details = details.get('regime', {})
    if regime_details:
        with st.expander("🌍 Market Regime Details"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("VIX", f"{regime_details.get('vix', 20):.1f}", regime_details.get('vix_regime', ''))
            with col2:
                st.metric("Direction", regime_details.get('direction', 'N/A'))
            with col3:
                st.metric("Market", regime_details.get('market', 'N/A'), regime_details.get('volatility', ''))
    
    # ML details
    ml_details = details.get('ml', {})
    if ml_details:
        with st.expander("🤖 ML Prediction Details"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("ML Signal", ml_details.get('ml_signal', 'N/A'))
            with col2:
                st.metric("ML Confidence", f"{ml_details.get('ml_confidence', 0):.1f}%", ml_details.get('ml_level', ''))
    
    # ATR Risk Management details
    atr_det = details.get('atr_risk', {})
    if atr_det:
        with st.expander("📐 ATR Risk Management Details"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("ATR(14)", f"${atr_det.get('atr_14', 0):.2f}")
                st.metric("ATR %", f"{atr_det.get('atr_pct', 0):.1f}%")
                st.metric("Volatility", atr_det.get('volatility', 'N/A'))
            with c2:
                st.metric("Risk/Share", f"${atr_det.get('risk_per_share', 0):.2f}")
                st.metric("Position Size", f"{atr_det.get('position_size', 0)} shares")
                st.metric("Risk Level", atr_det.get('risk_level', 'N/A'))
            with c3:
                st.metric("R:R Ratio", f"1:{atr_det.get('risk_reward', 0):.1f}")
                st.metric("R:R Grade", atr_det.get('rr_assessment', 'N/A'))
                if atr_det.get('suggested_stop'):
                    st.metric("Stop Price", f"${atr_det['suggested_stop']:.2f}", f"-{atr_det.get('stop_loss_pct', 0)}%")
    
    st.markdown("---")
if analyze_btn and symbols:
    results = []
    errors = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, symbol in enumerate(symbols):
        status_text.text(f"🔍 Analyzing {symbol} ({i+1}/{len(symbols)})...")
        
        scorer = ConfluenceScorer()
        result = scorer.score_all(symbol, direction=direction)
        
        if 'error' in result:
            errors.append((symbol, result['error']))
        elif result['total_score'] >= min_score:
            results.append(result)
        
        progress_bar.progress((i + 1) / len(symbols))
    
    status_text.text("✅ Analysis complete!")
    
    # Show errors
    for symbol, error in errors:
        st.error(f"❌ {symbol}: {error}")
    
    results.sort(key=lambda x: x['total_score'], reverse=True)
    st.session_state.last_results = results
    st.session_state.last_min_score = min_score
else:
    results = st.session_state.get('last_results', [])
    min_score = st.session_state.get('last_min_score', 162)

if results:
    st.subheader(f"📋 Swing Trading Signals (Score ≥ {min_score})")

    # Build summary table
    table_data = []
    for r in results:
        scores = r.get('scores', {})
        table_data.append({
            'Symbol': r['symbol'],
            'Score': r['total_score'],
            'Grade': r['grade'],
            'Signal': r['signal'],
            'Price': f"${r['current_price']:.2f}",
            '🛑 Stop Loss': f"${r['details'].get('atr_risk', {}).get('suggested_stop', r['current_price']):.2f}",
            '🎯 Half Profit': f"${r['details'].get('atr_risk', {}).get('half_profit_price', 0):.2f}",
            '🚀 Full Profit': f"${r['details'].get('atr_risk', {}).get('full_profit_price', 0):.2f}",
            'Trend': scores.get('trend', 0),
            'S/R': scores.get('support_resistance', 0),
            'Fib': scores.get('fibonacci', 0),
            'Candle': scores.get('candlestick', 0),
            'Momentum': scores.get('momentum', 0),
            'Volume': scores.get('volume', 0),
            'Sentiment': scores.get('sentiment', 0),
            'Fundamentals': scores.get('fundamentals', 0),
            'Regime': scores.get('regime', 0),
            'ML': scores.get('ml', 0),
            'Sector': scores.get('sector', 0),
            'ATR': scores.get('atr_risk', 0),
            'Earnings': scores.get('earnings', 0),
            'Insider': scores.get('insider', 0),
            'Breakout': scores.get('breakout', 0),
            'TradeMgmt': scores.get('trade_mgmt', 0),
            'Liquidity': scores.get('liquidity', 0),
        })

        df = pd.DataFrame(table_data)

        # Color-code the Grade column
        def color_grade(val):
            if val == 'A+':
                return 'background-color: #006400; color: white; font-weight: bold'
            elif val == 'A':
                return 'background-color: #228B22; color: white; font-weight: bold'
            elif val == 'B':
                return 'background-color: #FFD700; color: black; font-weight: bold'
            elif val == 'C':
                return 'background-color: #FF8C00; color: white'
            return ''

        styled_df = df.style.map(color_grade, subset=['Grade'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Download CSV
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download Signals as CSV",
            csv,
            f"swing_signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv"
        )

        # Email alert
        with st.expander("📧 Email Alerts", expanded=False):
            ecol1, ecol2 = st.columns(2)
            with ecol1:
                smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com", key="smtp_srv")
                smtp_port = st.number_input("Port", value=587, key="smtp_port")
                sender_email = st.text_input("Sender Email", value=st.session_state.get('sender_email', ''), key="sender_email")
            with ecol2:
                sender_pw = st.text_input("App Password", type="password",
                                          value=st.session_state.get('sender_pw', ''), key="sender_pw",
                                          help="Gmail: generate App Password at myaccount.google.com/apppasswords")
                recipient = st.text_input("Recipient Email", value=st.session_state.get('recipient', ''), key="recipient")
            if st.button("📧 Send A+ Setups via Email", key="send_email_btn"):
                if not sender_email or not sender_pw or not recipient:
                    st.error("Fill all email fields")
                else:
                    from analysis.alert_engine import AlertEngine
                    alert = AlertEngine(smtp_server=smtp_server, smtp_port=smtp_port,
                                        sender_email=sender_email, sender_password=sender_pw,
                                        recipient_email=recipient)
                    with st.spinner("Sending..."):
                        ok = alert.send_alerts(results, "[Stock Trader]")
                    if ok:
                        st.success(f"✅ Email sent to {recipient}!")
                        st.session_state.email_saved = True
                    else:
                        st.error("❌ Failed. Check SMTP settings and app password.")

        st.markdown("---")

        # Detailed cards for each signal
        st.subheader("🔍 Detailed Analysis")

        for rank, result in enumerate(results, 1):
            _render_swing_card(result, rank)


