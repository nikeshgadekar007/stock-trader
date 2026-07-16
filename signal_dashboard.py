"""Advanced Signal Dashboard"""
import streamlit as st
from analysis.advanced_signals import AdvancedSignalEngine

def render_signal_dashboard():
    st.header("📊 Advanced Intraday Signal Generator")
    
    if 'signals_analyzed' not in st.session_state:
        st.session_state.signals_analyzed = False
        st.session_state.buy_signals = []
        st.session_state.hold_signals = []
        st.session_state.sell_signals = []
        st.session_state.error_symbols = []
    
    st.subheader("💰 Trading Capital")
    col0, col1 = st.columns([2, 3])
    with col0:
        trading_capital = st.number_input("Your Trading Capital ($)", value=10000.0, min_value=100.0, help="Total capital you have for trading", key="trading_capital")
    with col1:
        max_risk_pct = st.slider("Max Risk Per Trade (%)", 0.5, 5.0, 2.0, help="Maximum % of capital you risk per trade", key="max_risk_pct")
    
    max_risk_amount = trading_capital * (max_risk_pct / 100)
    st.info(f"📌 Max Risk Per Trade: ${max_risk_amount:.2f} ({max_risk_pct}% of ${trading_capital:,.2f})")
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        symbols_input = st.text_input("Enter Stock Symbols (comma separated)", "AAPL, TSLA, NVDA, MSFT, AMZN, GOOGL, META", help="US Stock symbols", key="symbols_input")
    with col2:
        analyze_btn = st.button("🔍 Analyze", type="primary", key="analyze_btn")
    
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    
    if analyze_btn and symbols:
        engine = AdvancedSignalEngine()
        all_signals = []
        error_symbols = []
        
        with st.spinner("Analyzing stocks..."):
            for symbol in symbols:
                signal = engine.generate_signal(symbol)
                if 'error' in signal:
                    error_symbols.append((symbol, signal['error']))
                else:
                    all_signals.append(signal)
        
        st.session_state.error_symbols = error_symbols
        st.session_state.buy_signals = sorted([s for s in all_signals if s['signal'] == 'BUY'], key=lambda x: x['total_score'], reverse=True)
        st.session_state.hold_signals = sorted([s for s in all_signals if s['signal'] == 'HOLD'], key=lambda x: x['total_score'], reverse=True)
        st.session_state.sell_signals = sorted([s for s in all_signals if s['signal'] == 'SELL'], key=lambda x: x['total_score'], reverse=True)
        st.session_state.signals_analyzed = True
        
        for signal in st.session_state.buy_signals:
            key = f"amount_{signal['symbol']}"
            if key not in st.session_state:
                st.session_state[key] = 500.0
    
    for symbol, error in st.session_state.error_symbols:
        st.error(f"❌ {symbol}: {error}")
    
    col1, col2, col3 = st.columns(3)
    col1.success(f"🟢 BUY: {len(st.session_state.buy_signals)}")
    col2.info(f"⚪ HOLD: {len(st.session_state.hold_signals)}")
    col3.error(f"🔴 SELL: {len(st.session_state.sell_signals)}")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["🟢 BUY Signals", "⚪ HOLD Signals", "🔴 SELL Signals"])
    
    with tab1:
        if st.session_state.buy_signals:
            for rank, signal in enumerate(st.session_state.buy_signals, 1):
                _render_signal_card(signal, rank, "BUY", trading_capital, max_risk_amount)
        else:
            st.info("No BUY signals found. Click 'Analyze' to scan stocks.")
    
    with tab2:
        if st.session_state.hold_signals:
            for rank, signal in enumerate(st.session_state.hold_signals, 1):
                _render_signal_card(signal, rank, "HOLD", trading_capital, max_risk_amount)
        else:
            st.info("No HOLD signals found")
    
    with tab3:
        if st.session_state.sell_signals:
            for rank, signal in enumerate(st.session_state.sell_signals, 1):
                _render_signal_card(signal, rank, "SELL", trading_capital, max_risk_amount)
        else:
            st.info("No SELL signals found")


def _render_signal_card(signal, rank, action_type, trading_capital=10000, max_risk_amount=200):
    action = signal['signal']
    confidence = signal['total_score']
    
    emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚪"
    
    st.markdown(f"### {emoji} #{rank} {signal['symbol']} - **{action}** (Score: {confidence})")
    
    # Display confidence level
    confidence = signal.get('confidence', {})
    conf_level = confidence.get('level', 'MEDIUM')
    conf_value = confidence.get('confidence', 50)
    
    conf_color = "🟢" if conf_level == 'HIGH' else "🟡" if conf_level == 'MEDIUM' else "🔴"
    st.markdown(f"{conf_color} **Confidence: {conf_value:.0f}%** ({conf_level})")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${signal['current_price']:.2f}")
    with col2:
        st.metric("Entry", f"${signal['entry']:.2f}")
    with col3:
        st.metric("Stop Loss", f"${signal['stop_loss']:.2f}")
    with col4:
        st.metric("Target", f"${signal['target']:.2f}")
    
    risk = abs(signal['entry'] - signal['stop_loss'])
    reward = abs(signal['target'] - signal['entry'])
    rr_ratio = reward / risk if risk > 0 else 0
    risk_reward = signal.get('risk_reward', rr_ratio)
    
    st.info(f"💰 Risk/Reward: {risk_reward:.2f}x")
    
    # Display market regime
    regime = signal.get('regime', {})
    regime_text = regime.get('regime', 'UNKNOWN')
    regime_dir = regime.get('direction', 'NEUTRAL')
    regime_emoji = "📈" if regime_dir == 'BULLISH' else "📉" if regime_dir == 'BEARISH' else "➡️"
    st.caption(f"{regime_emoji} Market: {regime_text} ({regime_dir})")
    
    if action == "BUY":
        st.markdown("#### 📊 Position Size Calculator")
        
        amount_key = f"amount_{signal['symbol']}"
        if amount_key not in st.session_state:
            st.session_state[amount_key] = 500.0
        
        col1, col2 = st.columns([2, 1])
        with col1:
            # Ensure value doesn't exceed max_value
            safe_value = min(st.session_state[amount_key], trading_capital)
            amount_usd = st.number_input(
                f"How much to invest in {signal['symbol']}? ($)",
                min_value=0.0,
                max_value=float(trading_capital),
                value=safe_value,
                step=50.0,
                key=amount_key
            )
        
        current_price = signal['current_price']
        stop_loss = signal['stop_loss']
        risk_per_share = current_price - stop_loss
        
        shares = int(amount_usd / current_price)
        total_cost = shares * current_price
        actual_risk = shares * risk_per_share
        risk_pct_of_capital = (actual_risk / trading_capital) * 100
        
        max_shares_by_risk = int(max_risk_amount / risk_per_share) if risk_per_share > 0 else 0
        max_amount_by_risk = max_shares_by_risk * current_price
        
        with col2:
            st.metric("Max Risk", f"${max_risk_amount:.2f}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Shares to Buy", f"{shares}")
        with col2:
            st.metric("Total Cost", f"${total_cost:.2f}")
        with col3:
            st.metric("Actual Risk", f"${actual_risk:.2f}")
        with col4:
            risk_status = "✅ Safe" if actual_risk <= max_risk_amount else "⚠️ Too High"
            st.metric("Risk Status", risk_status)
        
        if actual_risk > max_risk_amount:
            st.error(f"⚠️ WARNING: Risk ${actual_risk:.2f} exceeds your limit of ${max_risk_amount:.2f}!")
            st.info(f"💡 Suggested: Invest max ${max_amount_by_risk:.2f} ({max_shares_by_risk} shares)")
        else:
            st.success(f"✅ Risk ${actual_risk:.2f} is within your ${max_risk_amount:.2f} limit ({risk_pct_of_capital:.2f}% of capital)")
        
        potential_profit = shares * (signal['target'] - current_price)
        profit_pct = (potential_profit / total_cost) * 100 if total_cost > 0 else 0
        st.info(f"📈 Potential Profit: ${potential_profit:.2f} ({profit_pct:.1f}% return)")
    
    with st.expander("📊 Detailed Analysis"):
        tab1, tab2, tab3, tab4 = st.tabs(["Timeframe", "Patterns", "Momentum", "Volume"])
        
        with tab1:
            st.subheader("Multi-Timeframe Confluence")
            confluence = signal.get('confluence', {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Confluence Score", f"{confluence.get('confluence_pct', 0):.1f}%")
            with col2:
                st.metric("Bullish Timeframes", confluence.get('bullish_count', 0))
            with col3:
                st.metric("Bearish Timeframes", confluence.get('bearish_count', 0))
            
            if confluence.get('aligned', False):
                st.success("✅ ALL TIMEFRAMES ALIGNED!")
            
            st.write("**Timeframe Scores:**")
            scores = confluence.get('scores', {})
            for tf, score in scores.items():
                bar = "🟢" if score > 0 else "🔴"
                st.write(f"{tf}: {bar} {'+' if score > 0 else ''}{score}")
        
        with tab2:
            st.subheader("Pattern Recognition")
            patterns = signal.get('patterns', {})
            pattern_list = patterns.get('patterns', [])
            st.write(f"**Patterns Detected:** {len(pattern_list)}")
            for p in pattern_list:
                emoji = "🟢" if "BULLISH" in p or "HIGHER" in p else "🔴" if "BEARISH" in p or "LOWER" in p else "⚪"
                st.write(f"{emoji} {p}")
            st.write(f"**Pattern Score:** {patterns.get('score', 0)}")
        
        with tab3:
            st.subheader("Momentum Matrix (10 Indicators)")
            momentum = signal.get('momentum', {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("RSI(14)", f"{momentum.get('rsi_14', 0):.1f}")
                st.metric("MACD", f"{momentum.get('macd', 0):.2f}")
                st.metric("MFI", f"{momentum.get('mfi', 0):.1f}")
            with col2:
                st.metric("Stochastic K", f"{momentum.get('stoch_k', 0):.1f}")
                st.metric("Williams %R", f"{momentum.get('williams_r', 0):.1f}")
                st.metric("ROC", f"{momentum.get('roc', 0):.2f}%")
            with col3:
                st.metric("CCI", f"{momentum.get('cci', 0):.1f}")
                st.metric("Aroon", f"{momentum.get('aroon_up', 0):.0f}/{momentum.get('aroon_down', 0):.0f}")
                st.metric("ADX", f"{momentum.get('adx', 0):.1f}")
            
            # Calculate direction and score from indicators
            bullish_count = 0
            bearish_count = 0
            if momentum.get('rsi_14', 50) > 50:
                bullish_count += 1
            elif momentum.get('rsi_14', 50) < 50:
                bearish_count += 1
            if momentum.get('macd', 0) > 0:
                bullish_count += 1
            else:
                bearish_count += 1
            if momentum.get('stoch_k', 50) > 50:
                bullish_count += 1
            elif momentum.get('stoch_k', 50) < 50:
                bearish_count += 1
            if momentum.get('williams_r', -50) > -50:
                bullish_count += 1
            else:
                bearish_count += 1
            if momentum.get('mfi', 50) > 50:
                bullish_count += 1
            elif momentum.get('mfi', 50) < 50:
                bearish_count += 1
            
            direction = "BULLISH" if bullish_count > bearish_count else "BEARISH" if bearish_count > bullish_count else "NEUTRAL"
            momentum_score = (bullish_count - bearish_count) * 10
            
            st.write(f"**Direction:** {direction}")
            st.write(f"**Momentum Score:** {momentum_score:.1f}")
            st.write(f"🟢 Bullish: {bullish_count}/10 | 🔴 Bearish: {bearish_count}/10")
            
            # SuperTrend
            st.write(f"**SuperTrend:** ${momentum.get('supertrend', 0):.2f} ({momentum.get('supertrend_signal', 'N/A')})")
        
        with tab4:
            st.subheader("Volume Analysis")
            volume = signal.get('volume', {})
            if volume:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Volume", f"{volume.get('current_volume', 0):,.0f}")
                with col2:
                    st.metric("Avg Volume", f"{volume.get('avg_volume', 0):,.0f}")
                with col3:
                    st.metric("Vol Ratio", f"{volume.get('vol_ratio', 0):.2f}x")
                
                col1, col2 = st.columns(2)
                with col1:
                    vol_trend = volume.get('vol_trend_pct', 0)
                    trend_emoji = "📈" if vol_trend > 0 else "📉" if vol_trend < 0 else "➡️"
                    st.metric("Volume Trend", f"{trend_emoji} {vol_trend:+.1f}%")
                with col2:
                    if volume.get('volume_surge', False):
                        st.warning("⚠️ VOLUME SURGE DETECTED!")
                    else:
                        st.info("📊 Normal Volume")
                
                if volume.get('above_vwap', False):
                    st.success("✅ Price above VWAP")
                else:
                    st.error("❌ Price below VWAP")
        
        # Confidence Breakdown
        st.markdown("#### 🎯 Signal Confidence Breakdown")
        conf_data = signal.get('confidence', {})
        factors = conf_data.get('factors', {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            rsi_score = factors.get('rsi_zone', 0)
            st.metric("RSI Zone", f"{rsi_score:.0%}", help="RSI in neutral zone (40-60) = 100%")
        with col2:
            macd_score = factors.get('macd_confirmation', 0)
            st.metric("MACD Confirm", f"{macd_score:.0%}", help="MACD above signal line = 100%")
        with col3:
            vol_score = factors.get('volume_confirmed', 0)
            st.metric("Volume", f"{vol_score:.0%}", help="Volume > 1.2x avg = 100%")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            trend_score = factors.get('trend_strength', 0)
            st.metric("ADX Trend", f"{trend_score:.0%}", help="ADX > 25 = 100%")
        with col2:
            conflu_score = factors.get('timeframe_confluence', 0)
            st.metric("Confluence", f"{conflu_score:.0%}", help="> 75% timeframe agreement = 100%")
        with col3:
            pattern_score = factors.get('pattern_quality', 0)
            st.metric("Patterns", f"{pattern_score:.0%}", help="Pattern score > 50 = 100%")
        
        regime_mult = conf_data.get('regime_multiplier', 1.0)
        regime_note = "📈 Boosted (Trending)" if regime_mult > 1 else "➡️ Normal" if regime_mult == 1 else "📉 Reduced (Ranging)"
        st.caption(f"Market Regime: {regime_note} ({regime_mult:.1f}x multiplier)")
