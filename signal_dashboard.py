"""Advanced Signal Dashboard with ML, Market Breadth, Intermarket & Backtesting
Now with live pre-market integration (4:00-9:30 AM ET) for intraday trading.
"""
import streamlit as st
from analysis.advanced_signals import AdvancedSignalEngine
from analysis.market_analysis import MarketAnalyzer
from analysis.intermarket import IntermarketAnalyzer
from analysis.intraday import get_market_session
import pandas as pd

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

def render_signal_dashboard():
    st.header("📊 Advanced Intraday Signal Generator")

    # Market Session Banner (live pre-market awareness)
    session = get_market_session()
    session_emoji = {"PRE_MARKET": "🟡", "REGULAR_MARKET": "🟢",
                     "AFTER_HOURS": "🟠", "CLOSED": "⚪"}.get(session, "⚪")
    session_msg = {
        "PRE_MARKET": "**PRE-MARKET ACTIVE** (4:00–9:30 AM ET) — 5 live pre-market layers feeding into every signal",
        "REGULAR_MARKET": "Regular session — intraday + pre-market layers both live",
        "AFTER_HOURS": "After-hours — pre-market layers still updating for tomorrow",
        "CLOSED": "Market closed — pre-market resumes 4:00 AM ET",
    }.get(session, "")
    st.info(f"{session_emoji} **{session}** — {session_msg}", icon="⏰")

    if 'signals_analyzed' not in st.session_state:
        st.session_state.signals_analyzed = False
        st.session_state.buy_signals = []
        st.session_state.hold_signals = []
        st.session_state.sell_signals = []
        st.session_state.error_symbols = []
        st.session_state.market_analysis = None
        st.session_state.ml_predictor = None
    
    st.subheader("💰 Trading Capital")
    col0, col1 = st.columns([2, 3])
    with col0:
        trading_capital = st.number_input("Your Trading Capital ($)", value=10000.0, min_value=100.0, help="Total capital you have for trading", key="trading_capital")
    with col1:
        max_risk_pct = st.slider("Max Risk Per Trade (%)", 0.5, 5.0, 2.0, help="Maximum % of capital you risk per trade", key="max_risk_pct")
    
    max_risk_amount = trading_capital * (max_risk_pct / 100)
    st.info(f"📌 Max Risk Per Trade: ${max_risk_amount:.2f} ({max_risk_pct}% of ${trading_capital:,.2f})")
    
    st.markdown("---")
    
    # Advanced Features Toggle
    with st.expander("⚙️ Advanced Analysis Settings", expanded=(session == "PRE_MARKET")):
        col1, col2, col3 = st.columns(3)
        with col1:
            use_ml = st.checkbox("🤖 ML Prediction", value=True, help="Use Machine Learning to predict signal outcomes")
        with col2:
            use_market = st.checkbox("📊 Market Breadth", value=True, help="Validate signals against market conditions")
        with col3:
            use_backtest = st.checkbox("📈 Backtest Validation", value=True, help="Show historical win rate for similar setups")
        # Pre-Market Mode toggle - auto-enabled during pre-market session
        use_premarket = st.checkbox(
            "🌅 Pre-Market Mode (5 live layers: Gap, VWAP, Volume, Range Break, News)",
            value=(session == "PRE_MARKET"),
            help="When ON, adds 5 pre-market institutional layers to every signal. Auto-enables during 4:00-9:30 AM ET. Strongly recommended for intraday trading during pre-market hours."
        )
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        max_stocks = st.slider("Max Stocks to Scan", 5, 50, 20, 1, key="max_stocks_slider")
        analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True, key="analyze_btn")
    with col1:
        symbols_input = st.text_input("Enter Stock Symbols (comma separated)",
                                       ",".join(DEFAULT_SYMBOLS[:max_stocks]),
                                       help="US Stock symbols", key=f"symbols_input_{max_stocks}")
    
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    
    if analyze_btn and symbols:
        engine = AdvancedSignalEngine()
        all_signals = []
        error_symbols = []
        
        # Initialize market analyzer if enabled
        market_analyzer = None
        if use_market:
            with st.spinner("Fetching market breadth data..."):
                market_analyzer = MarketAnalyzer()
                market_analyzer.calculate_market_breadth()
                st.session_state.market_analysis = market_analyzer.breadth_indicators
        
        # Initialize intermarket analyzer
        with st.spinner("Analyzing intermarket conditions..."):
            intermarket = IntermarketAnalyzer()
            intermarket_summary = intermarket.get_summary()
            st.session_state.intermarket_data = intermarket_summary
        
        # Initialize ML predictor if enabled
        ml_predictor = None
        if use_ml:
            with st.spinner("Training ML model with walk-forward validation..."):
                from analysis.ml_signal_predictor import MLSignalPredictor
                ml_predictor = MLSignalPredictor()
                train_result = ml_predictor.train_with_walk_forward('SPY', '2y')
                if train_result.get('success'):
                    st.session_state.ml_predictor = ml_predictor
                    st.session_state.ml_metrics = train_result.get('metrics', {})
                    st.session_state.walk_forward_metrics = train_result.get('walk_forward', {})
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_symbols = len(symbols)
        
        for i, symbol in enumerate(symbols):
            status_text.text(f"🔍 Analyzing {symbol} ({i+1}/{total_symbols})...")
            signal = engine.generate_signal(symbol, include_premarket=use_premarket)
            if 'error' in signal:
                error_symbols.append((symbol, signal['error']))
            else:
                # Add ML prediction
                if use_ml and ml_predictor and ml_predictor.is_trained:
                    try:
                        import yfinance as yf
                        ticker = yf.Ticker(symbol)
                        df = ticker.history(period='6mo', auto_adjust=True)
                        if not df.empty:
                            ml_result = ml_predictor.predict(df)
                            signal['ml_prediction'] = ml_result
                    except:
                        signal['ml_prediction'] = {'ml_signal': 'HOLD', 'ml_confidence': 0}
                
                # Add market validation
                if use_market and market_analyzer:
                    market_validation = market_analyzer.validate_signal_with_market(signal['signal'], symbol)
                    signal['market_validation'] = market_validation
                
                # Add backtest validation
                if use_backtest:
                    backtest_result = _quick_backtest(symbol, signal['signal'])
                    signal['backtest'] = backtest_result
                
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
    
    # Summary Table - All Signals at a Glance
    if st.session_state.signals_analyzed:
        st.subheader("📋 Signals Summary Table")
        
        all_signals = st.session_state.buy_signals + st.session_state.hold_signals + st.session_state.sell_signals
        if all_signals:
            # 3-tab summary table by signal type
            def _build_table(sigs, label):
                if not sigs:
                    st.info(f"No {label} signals in this scan.")
                    return
                tdata = []
                for s in sigs:
                    ml_pred = s.get('ml_prediction', {})
                    backtest = s.get('backtest', {})
                    conf = s.get('confidence', {})
                    tdata.append({
                        'Symbol': s['symbol'], 'Signal': s['signal'],
                        'Price': f"${s['current_price']:.2f}",
                        'Score': s['total_score'],
                        'Confidence': f"{conf.get('confidence', 50):.0f}%",
                        'ML Signal': ml_pred.get('ml_signal', '\u2014'),
                        'ML Conf': f"{ml_pred.get('ml_confidence', 0):.0f}%",
                        'Win Rate': f"{backtest.get('win_rate', 0):.0f}%",
                        'R:R': f"{s.get('risk_reward', 0):.1f}x",
                    })
                tdf = pd.DataFrame(tdata)
                tdf['_s'] = tdf['Score'].astype(int)
                tdf['_c'] = tdf['Confidence'].str.rstrip('%').astype(float)
                tdf['_m'] = (((tdf['Signal']=='BUY')&(tdf['ML Signal']=='BUY'))|((tdf['Signal']=='SELL')&(tdf['ML Signal']=='SELL'))|((tdf['Signal']=='HOLD')&(tdf['ML Signal']=='HOLD'))).astype(int)
                tdf['_mc'] = tdf['ML Conf'].str.rstrip('%').astype(float)
                tdf['_w'] = tdf['Win Rate'].str.rstrip('%').astype(float)
                tdf = tdf.sort_values(['_s','_c','_m','_mc','_w'], ascending=[False]*5).drop(columns=['_s','_c','_m','_mc','_w']).reset_index(drop=True)
                st.dataframe(tdf, use_container_width=True, hide_index=True)
                csv = tdf.to_csv(index=False)
                st.download_button(label=f"Download {label} CSV", data=csv, file_name=f"signals_{label.lower()}.csv", mime="text/csv", key=f"dl_{label}")

            t1, t2, t3 = st.tabs([
                f"BUY ({len(st.session_state.buy_signals)})",
                f"HOLD ({len(st.session_state.hold_signals)})",
                f"SELL ({len(st.session_state.sell_signals)})",
            ])
            with t1:
                _build_table(st.session_state.buy_signals, "BUY")
            with t2:
                _build_table(st.session_state.hold_signals, "HOLD")
            with t3:
                _build_table(st.session_state.sell_signals, "SELL")

            tab1, tab2, tab3 = st.tabs([

                f"🟢 BUY ({len(st.session_state.buy_signals)})",

                f"⚪ HOLD ({len(st.session_state.hold_signals)})",

                f"🔴 SELL ({len(st.session_state.sell_signals)})",

            ])

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

    st.markdown("---")

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
    
    # PRE-MARKET LAYERS DISPLAY (shown when pre-market data is available)
    pm_data = signal.get('premarket_data', {})
    if pm_data and 'error' not in pm_data and pm_data:
        pm_signal = signal.get('premarket_signal', 'PM_NEUTRAL')
        pm_emoji = "🟢" if pm_signal == 'PM_BULLISH' else "🔴" if pm_signal == 'PM_BEARISH' else "⚪"
        st.markdown(f"{pm_emoji} **Pre-Market Bias: {pm_signal}**")
        # Tier 1 filter status badge
        meta = pm_data.get('_meta', {})
        if meta.get('filters_active'):
            warnings = []
            if meta.get('spread_too_wide'):
                warnings.append(f"spread {meta.get('spread_pct', 0):.2f}%")
            pm_vol = meta.get('total_premarket_volume') or 0
            if pm_vol < 10000:
                warnings.append(f"vol {pm_vol:,}")
            et = meta.get('et_time', '?')
            tmult = meta.get('time_multiplier', 1.0)
            if warnings:
                st.caption(f"⚠️ Accuracy filters active: ET={et}, x{tmult}, " + ", ".join(warnings))
            else:
                st.caption(f"✓ Filters OK: ET={et}, time_mult=x{tmult}, spread={meta.get('spread_pct', 0):.2f}%, vol={pm_vol:,}")
        with st.expander("🌅 Pre-Market Live Layers (4:00-9:30 AM ET)", expanded=(session == "PRE_MARKET")):
            pm_cols = st.columns(5)
            pm_labels = [
                ('gap', 'Gap', 'gap_pct'),
                ('vwap', 'VWAP', 'distance_pct'),
                ('volume', 'Volume', 'volume_ratio'),
                ('range_break', 'Range', 'broke_high'),
                ('news', 'News', 'sentiment'),
            ]
            for col_idx, (key, label, metric_key) in enumerate(pm_labels):
                d = pm_data.get(key, {})
                score = d.get('score', 5)
                detail = d.get(metric_key, 'N/A')
                if metric_key == 'broke_high':
                    detail = 'YES' if d.get('broke_high') else ('NO' if d.get('broke_low') else '-')
                if isinstance(detail, float):
                    detail = f"{detail:.2f}"
                with pm_cols[col_idx]:
                    color = "🟢" if score >= 7 else "🔴" if score <= 3 else "⚪"
                    st.metric(f"{color} {label}", f"{score}/10", delta=str(detail))
                    st.caption(d.get('signal', 'N/A'))

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
        
        # News Sentiment Section
        sentiment_data = signal.get('sentiment', {})
        if sentiment_data and sentiment_data.get('overall_sentiment') != 'NO_DATA':
            st.markdown("#### 📰 News Sentiment Analysis")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                sent = sentiment_data.get('overall_sentiment', 'NEUTRAL')
                sent_emoji = "🟢" if sent == 'POSITIVE' else "🔴" if sent == 'NEGATIVE' else "⚪"
                st.metric("Sentiment", f"{sent_emoji} {sent}")
            with col2:
                st.metric("Score", f"{sentiment_data.get('sentiment_score', 0):.2f}")
            with col3:
                st.metric("Articles", sentiment_data.get('article_count', 0))
            with col4:
                pos = sentiment_data.get('positive_count', 0)
                neg = sentiment_data.get('negative_count', 0)
                st.metric("Pos/Neg", f"{pos}/{neg}")
            
            # Show top headlines
            news_items = sentiment_data.get('news', [])
            if news_items:
                with st.expander("📋 Recent Headlines"):
                    for article in news_items[:5]:
                        analysis = article.get('analysis', {})
                        sent_icon = "🟢" if analysis.get('sentiment') == 'POSITIVE' else "🔴" if analysis.get('sentiment') == 'NEGATIVE' else "⚪"
                        st.caption(f"{sent_icon} {article.get('title', '')} ({article.get('publisher', '')})")
        
        # Earnings Warning
        earnings_data = signal.get('earnings', {})
        if earnings_data and earnings_data.get('warning', False):
            days = earnings_data.get('days_until', '?')
            st.warning(f"⚠️ **Earnings in {days} day(s)!** ({earnings_data.get('earnings_date', 'Unknown')}) — Signal confidence reduced by 15% due to binary event risk")
        elif earnings_data and earnings_data.get('has_earnings', False):
            days = earnings_data.get('days_until', '?')
            st.info(f"📅 Earnings in {days} days ({earnings_data.get('earnings_date', 'Unknown')})")
        
        # ML Prediction Section
        ml_pred = signal.get('ml_prediction', {})
        if ml_pred and ml_pred.get('ml_signal'):
            st.markdown("#### 🤖 ML Model Prediction")
            col1, col2, col3 = st.columns(3)
            with col1:
                ml_sig = ml_pred.get('ml_signal', 'HOLD')
                ml_emoji = "🟢" if ml_sig == 'BUY' else "🔴" if ml_sig == 'SELL' else "⚪"
                st.metric("ML Signal", f"{ml_emoji} {ml_sig}")
            with col2:
                st.metric("ML Confidence", f"{ml_pred.get('ml_confidence', 0):.1f}%")
            with col3:
                rf_prob = ml_pred.get('rf_probability', 0)
                gb_prob = ml_pred.get('gb_probability', 0)
                st.metric("RF/GB Proba", f"{rf_prob:.0f}%/{gb_prob:.0f}%")
            
            # ML agreement check
            if ml_pred.get('ml_signal') == signal.get('signal'):
                st.success("✅ ML model agrees with technical signal")
            else:
                st.warning("⚠️ ML model disagrees with technical signal")
        
        # Market Validation Section
        market_val = signal.get('market_validation', {})
        if market_val:
            st.markdown("#### 📊 Market Breadth Validation")
            col1, col2, col3 = st.columns(3)
            with col1:
                val = market_val.get('validation', 'NEUTRAL')
                val_emoji = "✅" if val == 'CONFIRMED' else "⚠️" if val == 'WEAK' else "➡️"
                st.metric("Validation", f"{val_emoji} {val}")
            with col2:
                st.metric("Market Health", market_val.get('market_health', 'N/A'))
            with col3:
                st.metric("Sector", f"{market_val.get('sector_name', 'N/A')} ({market_val.get('sector_trend', 'N/A')})")
            
            # Breadth indicators
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Breadth Score", f"{market_val.get('breadth_score', 0):.1f}")
            with col2:
                st.metric("Sector Breadth", f"{market_val.get('sector_breadth', 0):.1f}")
            with col3:
                st.metric("A/D Ratio", f"{market_val.get('ad_ratio', 1.0):.2f}")
            
            # Confirmations and warnings
            confirmations = market_val.get('confirmations', [])
            warnings_list = market_val.get('warnings', [])
            if confirmations:
                for c in confirmations:
                    st.success(f"✅ {c}")
            if warnings_list:
                for w in warnings_list:
                    st.warning(f"⚠️ {w}")
        
        # Backtest Section
        backtest = signal.get('backtest', {})
        if backtest:
            st.markdown("#### 📈 Backtest Validation")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Win Rate", f"{backtest.get('win_rate', 0):.1f}%")
            with col2:
                st.metric("Avg Return", f"{backtest.get('avg_return', 0):.2f}%")
            with col3:
                st.metric("Sample Size", backtest.get('sample_size', 0))
            
            if backtest.get('win_rate', 0) > 60:
                st.success("✅ Historical win rate above 60%")
            elif backtest.get('win_rate', 0) > 40:
                st.info("📊 Historical win rate moderate")
            else:
                st.warning("⚠️ Historical win rate below 40%")
        
        # ML Training Metrics (show once)
        if st.session_state.get('ml_metrics'):
            with st.expander("🤖 ML Model Performance"):
                metrics = st.session_state.ml_metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Ensemble Accuracy", f"{metrics.get('ensemble_accuracy', 0):.1f}%")
                with col2:
                    st.metric("Ensemble Precision", f"{metrics.get('ensemble_precision', 0):.1f}%")
                with col3:
                    st.metric("Ensemble Recall", f"{metrics.get('ensemble_recall', 0):.1f}%")
                st.caption(f"Trained on {metrics.get('train_samples', 0)} samples, {metrics.get('feature_count', 0)} features")
        
        # Market Breadth Overview (show once)
        if st.session_state.get('market_analysis'):
            with st.expander("📊 Market Breadth Overview"):
                ma = st.session_state.market_analysis
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Market Health", ma.get('market_health', 'N/A'))
                with col2:
                    st.metric("Breadth Score", f"{ma.get('breadth_score', 0):.1f}")
                with col3:
                    st.metric("Bullish ETFs", f"{ma.get('bullish_etfs', 0)}/{ma.get('total_etfs', 0)}")
                with col4:
                    st.metric("SPY RSI", f"{ma.get('spy_rsi', 50):.1f}")
        
        # Intermarket Analysis (show once)
        if st.session_state.get('intermarket_data'):
            with st.expander("🌍 Intermarket Analysis & Regime Detection"):
                im = st.session_state.intermarket_data
                regime = im.get('regime', {})
                
                # Regime header
                vix = regime.get('vix', 20)
                vix_regime = regime.get('vix_regime', 'NORMAL')
                direction = regime.get('direction', 'NEUTRAL')
                strategy = regime.get('strategy', 'NEUTRAL')
                strategy_desc = regime.get('strategy_desc', '')
                pos_mult = im.get('position_multiplier', 1.0)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("VIX", f"{vix:.1f}", delta=f"{vix_regime}")
                with col2:
                    dir_emoji = "📈" if 'BULL' in direction else "📉" if 'BEAR' in direction else "➡️"
                    st.metric("Direction", f"{dir_emoji} {direction}")
                with col3:
                    st.metric("Strategy", strategy, help=strategy_desc)
                with col4:
                    pos_color = "🟢" if pos_mult >= 0.8 else "🟡" if pos_mult >= 0.5 else "🔴"
                    st.metric("Position Size", f"{pos_color} {pos_mult:.0%}")
                
                st.caption(f"💡 **{strategy_desc}**")
                
                # Intermarket signals
                signals = regime.get('signals', [])
                if signals:
                    st.markdown("**Intermarket Signals:**")
                    for s in signals:
                        if s.startswith('✅'):
                            st.success(s)
                        elif s.startswith('⚠️'):
                            st.warning(s)
                
                # Macro data table
                macro_data = im.get('macro_data', {})
                if macro_data:
                    st.markdown("**Macro Indicators:**")
                    macro_rows = []
                    for ticker, data in macro_data.items():
                        if 'error' not in data:
                            trend_emoji = "🟢" if data.get('trend') == 'BULLISH' else "🔴" if data.get('trend') == 'BEARISH' else "⚪"
                            macro_rows.append({
                                'Ticker': ticker,
                                'Name': data.get('name', ''),
                                'Price': f"${data.get('price', 0):.2f}",
                                '5D': f"{data.get('change_5d', 0):+.1f}%",
                                '20D': f"{data.get('change_20d', 0):+.1f}%",
                                'Trend': f"{trend_emoji} {data.get('trend', 'N/A')}",
                                'RSI': f"{data.get('rsi', 50):.0f}"
                            })
                    
                    if macro_rows:
                        macro_df = pd.DataFrame(macro_rows)
                        st.dataframe(macro_df, use_container_width=True, hide_index=True)

def _quick_backtest(symbol: str, signal: str) -> dict:
    """Quick backtest to estimate win rate for similar setups"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='1y', auto_adjust=True)
        
        if df.empty or len(df) < 50:
            return {'win_rate': 0, 'avg_return': 0, 'sample_size': 0}
        
        # Calculate RSI
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, float('inf'))
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # Generate signals
        df['signal'] = 'HOLD'
        df.loc[(df['rsi'] < 40) & (df['macd'] > df['macd_signal']), 'signal'] = 'BUY'
        df.loc[(df['rsi'] > 60) & (df['macd'] < df['macd_signal']), 'signal'] = 'SELL'
        
        # Calculate forward returns
        df['forward_return'] = df['Close'].shift(-5) / df['Close'] - 1
        
        # Filter for similar signals
        similar = df[df['signal'] == signal].dropna()
        
        if len(similar) < 5:
            return {'win_rate': 50, 'avg_return': 0, 'sample_size': len(similar)}
        
        wins = (similar['forward_return'] > 0).sum()
        win_rate = (wins / len(similar)) * 100
        avg_return = similar['forward_return'].mean() * 100
        
        return {
            'win_rate': round(win_rate, 1),
            'avg_return': round(avg_return, 2),
            'sample_size': len(similar)
        }
    except Exception as e:
        return {'win_rate': 0, 'avg_return': 0, 'sample_size': 0}
