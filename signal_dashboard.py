"""Advanced Signal Dashboard"""
import streamlit as st
import yfinance as yf
from analysis.advanced_signals import AdvancedSignalEngine
from datetime import datetime

def render_signal_dashboard():
    st.header("📊 Advanced Intraday Signal Generator")
    
    # Symbol input
    col1, col2 = st.columns([3, 1])
    with col1:
        symbols_input = st.text_input("Enter Stock Symbols (comma separated)", "AAPL, TSLA, NVDA, MSFT, AMZN", help="US Stock symbols")
    with col2:
        analyze_btn = st.button("🔍 Analyze", type="primary")
    
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    
    if analyze_btn and symbols:
        engine = AdvancedSignalEngine()
        
        for symbol in symbols:
            with st.container():
                st.markdown("---")
                signal = engine.generate_signal(symbol)
                
                if 'error' in signal:
                    st.error(f"❌ {symbol}: {signal['error']}")
                    continue
                
                # Signal header
                action = signal['action']
                confidence = signal['confidence']
                
                if action == "BUY":
                    color = "green"
                    emoji = "🟢"
                elif action == "SELL":
                    color = "red"
                    emoji = "🔴"
                else:
                    color = "gray"
                    emoji = "⚪"
                
                st.markdown(f"## {emoji} {symbol} - **{action}** ({confidence:.1f}% confidence)")
                
                # Price info
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Current Price", f"${signal['current_price']:.2f}")
                with col2:
                    st.metric("Entry", f"${signal['entry']:.2f}")
                with col3:
                    st.metric("Stop Loss", f"${signal['stop']:.2f}", delta=f"{((signal['stop']-signal['current_price'])/signal['current_price']*100):.2f}%")
                with col4:
                    st.metric("Target", f"${signal['target1']:.2f}", delta=f"{((signal['target1']-signal['current_price'])/signal['current_price']*100):.2f}%")
                
                # Detailed analysis
                with st.expander("📈 Detailed Analysis", expanded=True):
                    tab1, tab2, tab3, tab4 = st.tabs(["Timeframe", "Patterns", "Momentum", "Volume"])
                    
                    with tab1:
                        st.subheader("Multi-Timeframe Confluence")
                        confluence = signal['confluence']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Confluence Score", f"{confluence['confluence_pct']:.1f}%")
                        with col2:
                            st.metric("Bullish Timeframes", confluence['bullish_count'])
                        with col3:
                            st.metric("Bearish Timeframes", confluence['bearish_count'])
                        
                        if confluence['aligned']:
                            st.success("✅ ALL TIMEFRAMES ALIGNED!")
                        
                        st.write("**Timeframe Scores:**")
                        for tf, score in confluence['scores'].items():
                            bar_color = "green" if score > 0 else "red"
                            st.write(f"{tf}: {'+' if score > 0 else ''}{score}")
                    
                    with tab2:
                        st.subheader("Pattern Recognition")
                        patterns = signal['patterns']
                        st.write(f"**Patterns Detected:** {len(patterns['patterns'])}")
                        for p in patterns['patterns']:
                            st.write(f"• {p}")
                        st.write(f"**Pattern Score:** {patterns['score']}")
                    
                    with tab3:
                        st.subheader("Momentum Matrix")
                        momentum = signal['momentum']
                        if momentum:
                            indicators = momentum['indicators']
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("RSI(14)", f"{indicators['rsi_14']:.1f}")
                                st.metric("MACD", f"{indicators['macd']:.2f}")
                            with col2:
                                st.metric("Stochastic K", f"{indicators['stoch_k']:.1f}")
                                st.metric("Williams %R", f"{indicators['williams_r']:.1f}")
                            with col3:
                                st.metric("CCI", f"{indicators['cci']:.1f}")
                                st.metric("Aroon", f"{indicators['aroon_up']:.0f}/{indicators['aroon_down']:.0f}")
                            
                            st.write(f"**Direction:** {momentum['direction']}")
                            st.write(f"**Momentum Score:** {momentum['momentum_score']:.1f}")
                            st.write(f"Bullish: {momentum['bullish_count']}/6 | Bearish: {momentum['bearish_count']}/6")
                    
                    with tab4:
                        st.subheader("Volume Analysis")
                        volume = signal['volume']
                        if volume:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Current Volume", f"{volume['current_volume']:,.0f}")
                            with col2:
                                st.metric("Avg Volume", f"{volume['avg_volume']:,.0f}")
                            with col3:
                                st.metric("Vol Ratio", f"{volume['vol_ratio']:.2f}x")
                            
                            if volume['volume_surge']:
                                st.warning("⚠️ VOLUME SURGE DETECTED!")
                            if volume['above_vwap']:
                                st.success("✅ Price above VWAP")
                            else:
                                st.error("❌ Price below VWAP")
                
                # Risk/Reward
                risk = abs(signal['entry'] - signal['stop'])
                reward = abs(signal['target1'] - signal['entry'])
                rr_ratio = reward / risk if risk > 0 else 0
                
                st.info(f"💰 Risk/Reward Ratio: {rr_ratio:.2f}x | Max Risk: ${risk:.2f} | Max Reward: ${reward:.2f}")

if __name__ == "__main__":
    render_signal_dashboard()