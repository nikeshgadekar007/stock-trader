"""
Swing Trading Dashboard - 12-Layer Confluence Scoring System
Only shows A+ setups (score >= 126/140) for maximum accuracy
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from analysis.confluence_scorer import ConfluenceScorer

st.set_page_config(page_title="Swing Trading Signals", page_icon="🎯", layout="wide")

st.title("🎯 Swing Trading — A+ Setups Only")
st.caption("12-Layer Confluence Scoring System | Only trades with score ≥ 126/140 are shown")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    min_score = st.slider("Minimum Score Threshold", 80, 140, 126, 2, 
                          help="Only show signals above this score. 126+ = A+ setups (90%)")
    max_stocks = st.slider("Max Stocks to Scan", 5, 50, 20, 5)
    
    st.markdown("---")
    st.markdown("### 📊 Score Guide (/140)")
    st.markdown("| Score | Grade | Signal |")
    st.markdown("|-------|-------|--------|")
    st.markdown("| 126-140 | A+ | STRONG BUY |")
    st.markdown("| 112-125 | A | BUY |")
    st.markdown("| 98-111 | B | MODERATE BUY |")
    st.markdown("| 84-97 | C | WEAK BUY |")
    st.markdown("| 56-83 | D | HOLD |")
    
    st.markdown("---")
    st.markdown("### 🎯 12 Layers")
    st.markdown("1. Multi-Timeframe Trend (30 pts)")
    st.markdown("2. Support/Resistance (15 pts)")
    st.markdown("3. Fibonacci Levels (10 pts)")
    st.markdown("4. Candlestick Patterns (10 pts)")
    st.markdown("5. Momentum Indicators (10 pts)")
    st.markdown("6. Volume Confirmation (10 pts)")
    st.markdown("7. News Sentiment (10 pts)")
    st.markdown("8. Fundamentals (10 pts)")
    st.markdown("9. Market Regime (5 pts)")
    st.markdown("10. ML Prediction (10 pts)")
    st.markdown("11. Sector Strength (10 pts)")
    st.markdown("12. ATR Risk Mgmt (10 pts)")

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
    bar_length = min(score // 2, 70)
    score_bar = "█" * bar_length + "░" * (70 - bar_length)
    
    st.markdown(f"### {grade_emoji} #{rank} {symbol} — **{signal}** ({grade})")
    st.markdown(f"**Score: {score}/140**")
    st.progress(score / 140)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", f"${price:.2f}")
    with col2:
        st.metric("Total Score", f"{score}/140")
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

    # Layer breakdown
    with st.expander("📊 12-Layer Score Breakdown"):
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
        result = scorer.score_all(symbol)
        
        if 'error' in result:
            errors.append((symbol, result['error']))
        elif result['total_score'] >= min_score:
            results.append(result)
        
        progress_bar.progress((i + 1) / len(symbols))
    
    status_text.text("✅ Analysis complete!")
    
    # Show errors
    for symbol, error in errors:
        st.error(f"❌ {symbol}: {error}")
    
    # Sort by score descending
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Summary
    a_plus = [r for r in results if r['total_score'] >= 126]
    a_grade = [r for r in results if 112 <= r['total_score'] < 126]
    b_grade = [r for r in results if 98 <= r['total_score'] < 112]
    c_grade = [r for r in results if 84 <= r['total_score'] < 98]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏆 A+ Setups (126+)", len(a_plus))
    col2.metric("✅ A Grade (112-125)", len(a_grade))
    col3.metric("📊 B Grade (98-111)", len(b_grade))
    col4.metric("👀 C Grade (84-97)", len(c_grade))
    
    st.markdown("---")
    
    if not results:
        st.warning(f"No stocks scored above {min_score}. Try lowering the threshold or scanning different stocks.")
    else:
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
        
        st.markdown("---")
        
        # Detailed cards for each signal
        st.subheader("🔍 Detailed Analysis")
        
        for rank, result in enumerate(results, 1):
            _render_swing_card(result, rank)


