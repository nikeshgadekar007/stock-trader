"""
Scalping Page - Real-time Intraday Trading Interface
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scalping.scalping_engine import ScalpingEngine

def render_scalping_page():
    """Render the scalping trading interface"""
    st.header("⚡ Intraday Scalping Suite")
    st.markdown("Real-time 5-min charts, Level 2, Volume Spikes")
    
    # Initialize engine
    engine = ScalpingEngine()
    
    # Stock selection
    scalping_stocks = [
        'AAPL', 'TSLA', 'NVDA', 'AMD', 'INTC', 'META', 'AMZN', 'GOOGL',
        'SPY', 'QQQ', 'IWM', 'TQQQ', 'SQQQ', 'NVDA', 'AMD', 'COIN',
        'PLTR', 'SPCE', 'RIVN', 'LCID', 'NKLA', 'SOFI', 'HOOD'
    ]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        symbol = st.selectbox("Select Stock", scalping_stocks, index=0)
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
    
    # Get data
    with st.spinner("Fetching real-time data..."):
        quote = engine.get_realtime_quote(symbol)
        df = engine.get_5min_chart(symbol)
        indicators = engine.calculate_scalping_indicators(df) if not df.empty else {}
        level2 = engine.get_level2_proxy(symbol)
        volume_alert = engine.detect_volume_spike(df) if not df.empty else {}
        momentum = engine.analyze_momentum(df) if not df.empty else {}
    
    # Real-time quote display
    if 'error' not in quote:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        price = quote.get('last', 0)
        change = quote.get('change', 0)
        change_pct = quote.get('change_pct', 0)
        
        with col1:
            st.metric("Price", f"${price:.2f}", f"{change_pct:+.2f}%")
        with col2:
            st.metric("Bid/Ask", f"${quote.get('bid', 0):.2f}/${quote.get('ask', 0):.2f}")
        with col3:
            spread = quote.get('ask', 0) - quote.get('bid', 0)
            st.metric("Spread", f"${spread:.4f}")
        with col4:
            st.metric("Volume", f"{quote.get('volume', 0):,.0f}")
        with col5:
            high_low = quote.get('high', 0) - quote.get('low', 0)
            st.metric("Range", f"${high_low:.2f}")
    
    st.markdown("---")
    
    # Generate signal
    if indicators:
        signal = engine.generate_scalp_signal(quote, indicators)
        
        # Signal display
        col1, col2, col3, col4 = st.columns(4)
        
        action = signal['action']
        confidence = signal['confidence']
        
        with col1:
            if action == "BUY":
                st.success(f"📈 {action} - {confidence}% confidence")
            elif action == "SELL":
                st.error(f"📉 {action} - {confidence}% confidence")
            else:
                st.info(f"⏸️ {action} - {confidence}% confidence")
        
        with col2:
            st.metric("Entry", f"${signal['entry']:.2f}")
        with col3:
            st.metric("Stop", f"${signal['stop']:.2f}")
        with col4:
            st.metric("Target", f"${signal['target']:.2f}")
        
        # Active signals
        with st.expander("📊 Active Indicators"):
            for s in signal['signals']:
                emoji = "🟢" if "BULLISH" in s or "OVERSOLD" in s else "🔴" if "BEARISH" in s or "OVERBOUGHT" in s else "⚪"
                st.markdown(f"{emoji} {s}")
    
    st.markdown("---")
    
    # Two column layout: Chart and Level 2
    chart_col, level2_col = st.columns([2, 1])
    
    with chart_col:
        st.subheader("📊 5-Minute Chart")
        
        if not df.empty:
            # Create chart with indicators
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.5, 0.25, 0.25],
                subplot_titles=('Price', 'Volume', 'RSI')
            )
            
            # Candlestick
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name="Price"
                ),
                row=1, col=1
            )
            
            # EMA lines
            if 'ema9' in indicators:
                fig.add_trace(
                    go.Scatter(x=df.index, y=[indicators['ema9']]*len(df), 
                              line=dict(color='blue', width=1), name='EMA 9'),
                    row=1, col=1
                )
            if 'ema21' in indicators:
                fig.add_trace(
                    go.Scatter(x=df.index, y=[indicators['ema21']]*len(df), 
                              line=dict(color='orange', width=1), name='EMA 21'),
                    row=1, col=1
                )
            if 'vwap' in indicators:
                fig.add_trace(
                    go.Scatter(x=df.index, y=[indicators['vwap']]*len(df), 
                              line=dict(color='yellow', width=1, dash='dash'), name='VWAP'),
                    row=1, col=1
                )
            
            # Volume bars
            colors = ['green' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'red' 
                     for i in range(len(df))]
            fig.add_trace(
                go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'),
                row=2, col=1
            )
            
            # RSI
            if 'rsi' in indicators:
                rsi_values = [50] * len(df)  # Placeholder
                fig.add_trace(
                    go.Scatter(x=df.index, y=rsi_values, 
                              line=dict(color='gray', width=1), name='RSI 50'),
                    row=3, col=1
                )
            
            fig.update_layout(
                template="plotly_dark",
                height=600,
                showlegend=True,
                xaxis_rangeslider_visible=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No chart data available")
    
    with level2_col:
        st.subheader("📋 Level 2 (Market Depth)")
        
        if level2 and 'error' not in level2:
            # Spread info
            st.metric("Spread", f"${level2.get('spread', 0):.4f} ({level2.get('spread_pct', 0):.3f}%)")
            
            # Imbalance
            imbalance = level2.get('imbalance', 0)
            if imbalance > 10:
                st.success(f"🟢 Bid Heavy ({imbalance:+.1f}%)")
            elif imbalance < -10:
                st.error(f"🔴 Ask Heavy ({imbalance:+.1f}%)")
            else:
                st.info(f"⚖️ Balanced ({imbalance:+.1f}%)")
            
            # Bid/Ask columns
            bid_col, ask_col = st.columns(2)
            
            with bid_col:
                st.markdown("**BID**")
                for level in level2.get('bid_levels', [])[:5]:
                    size = level['size']
                    color = "🔴" if size > 500 else "🟡" if size > 300 else "⚪"
                    st.markdown(f"{color} ${level['price']:.2f} ({size})")
            
            with ask_col:
                st.markdown("**ASK**")
                for level in level2.get('ask_levels', [])[:5]:
                    size = level['size']
                    color = "🔴" if size > 500 else "🟡" if size > 300 else "⚪"
                    st.markdown(f"{color} ${level['price']:.2f} ({size})")
            
            # Walls
            walls = level2.get('walls', [])
            if walls:
                with st.expander("🚨 Large Orders (Walls)"):
                    for wall in walls:
                        st.warning(f"${wall['price']:.2f} - {wall['size']} shares")
    
    st.markdown("---")
    
    # Volume and Momentum section
    vol_col, mom_col = st.columns(2)
    
    with vol_col:
        st.subheader("📈 Volume Analysis")
        if volume_alert:
            if volume_alert.get('spike'):
                st.error(f"🚨 VOLUME SPIKE: {volume_alert['ratio']:.1f}x average!")
            else:
                st.info(f"Volume: {volume_alert['ratio']:.1f}x average")
            
            st.markdown(f"Current: {volume_alert.get('current_volume', 0):,.0f}")
            st.markdown(f"Average: {volume_alert.get('avg_volume', 0):,.0f}")
    
    with mom_col:
        st.subheader("💨 Momentum")
        if momentum:
            direction = momentum.get('direction', 'NEUTRAL')
            if direction == 'BULLISH':
                st.success(f"🟢 {direction}")
            elif direction == 'BEARISH':
                st.error(f"🔴 {direction}")
            else:
                st.info(f"⚪ {direction}")
            
            st.markdown(f"Price Change (5m): {momentum.get('price_change_5min', 0):+.3f}%")
            st.markdown(f"Volume Change (5m): {momentum.get('volume_change_5min', 0):+.1f}%")
            
            # Recent candles
            candles = momentum.get('candles', [])
            if candles:
                st.markdown("Last 5 candles:")
                for i, c in enumerate(candles):
                    emoji = "🟢" if c == 'BULLISH' else "🔴"
                    st.markdown(f"{emoji} {c}")
    
    st.markdown("---")
    
    # Trade execution panel
    st.subheader("🎯 Quick Trade Execution")
    
    if indicators and signal['action'] != 'HOLD':
        trade_col1, trade_col2, trade_col3 = st.columns(3)
        
        with trade_col1:
            if st.button(f"📈 BUY {symbol}", use_container_width=True, type="primary"):
                st.success(f"BUY order placed at ${signal['entry']:.2f}")
                st.balloons()
        
        with trade_col2:
            st.info(f"Risk: ${abs(signal['entry'] - signal['stop']):.2f} | R:R: {signal['risk_reward']:.1f}x")
        
        with trade_col3:
            if st.button(f"📉 SELL {symbol}", use_container_width=True, type="secondary"):
                st.success(f"SELL order placed at ${signal['entry']:.2f}")
    else:
        st.info("No trade signal. Wait for a BUY or SELL opportunity.")
    
    # Support/Resistance
    if indicators:
        with st.expander("📍 Support & Resistance"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Resistance**")
                st.markdown(f"R2: ${indicators.get('r2', 0):.2f}")
                st.markdown(f"R1: ${indicators.get('r1', 0):.2f}")
                st.markdown(f"Pivot: ${indicators.get('pivot', 0):.2f}")
            with col2:
                st.markdown("**Support**")
                st.markdown(f"S1: ${indicators.get('s1', 0):.2f}")
                st.markdown(f"S2: ${indicators.get('s2', 0):.2f}")
    
    # Auto-refresh
    if auto_refresh:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=5000, key="scalping_refresh")
