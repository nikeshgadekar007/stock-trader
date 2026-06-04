"""
Trade Copier - Simple Dashboard for Intraday Trading
Get EXACT trades: Symbol, Entry, Stop, Target, Size
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.fetcher import fetch_stock_data
from analysis.technical import TechnicalAnalyzer
from trading.signals import generate_trade_recommendation
from trading.risk_management import TradeSetup, get_risk_assessment
from scalping.scalping_engine import ScalpingEngine
from utils.time_utils import get_local_time, get_us_market_time
import config

def get_trade_copier_signals():
    """Generate simple, actionable trade signals"""
    signals = []
    engine = ScalpingEngine()
    
    # Hot stocks for intraday
    hot_stocks = ['TSLA', 'NVDA', 'AMD', 'COIN', 'AAPL', 'META', 'AMZN', 'PLTR', 'SPY', 'QQQ']
    
    for symbol in hot_stocks:
        try:
            # Get data
            quote = engine.get_realtime_quote(symbol)
            if 'error' in quote:
                continue
                
            df = engine.get_5min_chart(symbol)
            if df.empty:
                continue
                
            indicators = engine.calculate_scalping_indicators(df)
            if not indicators:
                continue
            
            # Generate signal
            signal = engine.generate_scalp_signal(quote, indicators)
            
            if signal['action'] != 'HOLD' and signal['confidence'] >= 60:
                # Calculate position size
                entry = signal['entry']
                stop = signal['stop']
                target = signal['target']
                
                setup = TradeSetup(symbol, entry, stop, target, config.CAPITAL, 1.0)
                risk_result = get_risk_assessment(setup)
                
                signals.append({
                    'symbol': symbol,
                    'action': signal['action'],
                    'confidence': signal['confidence'],
                    'entry': entry,
                    'stop': stop,
                    'target': target,
                    'risk': abs(entry - stop),
                    'reward': abs(target - entry),
                    'rr_ratio': signal['risk_reward'],
                    'shares': risk_result['position_size']['shares'],
                    'position_value': risk_result['position_size']['value'],
                    'price': quote.get('last', entry),
                    'change': quote.get('change_pct', 0),
                    'volume_ratio': indicators.get('vol_ratio', 1),
                    'rsi': indicators.get('rsi', 50),
                    'momentum': 'BULLISH' if quote.get('change_pct', 0) > 0 else 'BEARISH'
                })
        except Exception as e:
            continue
    
    # Sort by confidence
    signals.sort(key=lambda x: x['confidence'], reverse=True)
    return signals

def render_trade_copier():
    """Render the Trade Copier dashboard"""
    st.set_page_config(page_title="Trade Copier", page_icon="📋")
    
    # Header
    st.title("📋 Trade Copier - Your Daily Trading Plan")
    
    # Show local time and US market time
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**🕐 Your Local Time:** {get_local_time().strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        st.markdown(f"**🏛️ US Market Time:** {get_us_market_time()}")
    
    # Market status
    from analysis.intraday import get_market_session
    session = get_market_session()
    if session == "REGULAR_MARKET":
        st.success("🟢 MARKET OPEN - Trading Active")
    elif session == "PRE_MARKET":
        st.warning("🟡 PRE-MARKET - Trading Soon")
    elif session == "AFTER_HOURS":
        st.info("🔵 AFTER HOURS - Limited Trading")
    else:
        st.error("🔴 MARKET CLOSED")
    
    st.markdown("---")
    
    # Generate signals
    if st.button("🔍 SCAN MARKET NOW", type="primary", use_container_width=True):
        with st.spinner("Scanning hot stocks..."):
            st.session_state.signals = get_trade_copier_signals()
    
    # Auto-refresh option
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.checkbox("🔄 Auto-refresh every 30 seconds", value=False):
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=30000, key="trade_copier_refresh")
            st.session_state.signals = get_trade_copier_signals()
    
    with col2:
        if st.button("📱 Setup Notifications"):
            st.session_state.show_notifications_setup = True
    
    st.markdown("---")
    
    # Display signals
    if st.session_state.get('signals'):
        signals = st.session_state.signals
        
        # Summary
        buy_signals = [s for s in signals if s['action'] == 'BUY']
        sell_signals = [s for s in signals if s['action'] == 'SELL']
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Total Signals", len(signals))
        col2.metric("🟢 BUY", len(buy_signals))
        col3.metric("🔴 SELL", len(sell_signals))
        
        st.markdown("---")
        
        # BUY Signals
        if buy_signals:
            st.subheader("🟢 BUY Opportunities")
            
            for sig in buy_signals[:5]:
                with st.container():
                    # Signal header
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        emoji = "🚀" if sig['volume_ratio'] > 2 else "📈"
                        st.markdown(f"### {emoji} **{sig['symbol']}**")
                        st.caption(f"Confidence: {sig['confidence']}% | RSI: {sig['rsi']:.0f}")
                    
                    with col2:
                        st.metric("Entry", f"${sig['entry']:.2f}")
                        st.caption(f"Stop: ${sig['stop']:.2f}")
                    
                    with col3:
                        st.metric("Target", f"${sig['target']:.2f}")
                        st.caption(f"R:R = {sig['rr_ratio']:.1f}x")
                    
                    # Trade details
                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("Shares", sig['shares'])
                    col_b.metric("Position", f"${sig['position_value']:,.0f}")
                    col_c.metric("Risk", f"${sig['risk']:.2f}")
                    col_d.metric("Reward", f"${sig['reward']:.2f}")
                    
                    # Action buttons
                    st.markdown("---")
        
        # SELL Signals
        if sell_signals:
            st.subheader("🔴 SELL Opportunities")
            
            for sig in sell_signals[:5]:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"### 📉 **{sig['symbol']}**")
                        st.caption(f"Confidence: {sig['confidence']}% | RSI: {sig['rsi']:.0f}")
                    
                    with col2:
                        st.metric("Entry", f"${sig['entry']:.2f}")
                        st.caption(f"Stop: ${sig['stop']:.2f}")
                    
                    with col3:
                        st.metric("Target", f"${sig['target']:.2f}")
                        st.caption(f"R:R = {sig['rr_ratio']:.1f}x")
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("Shares", sig['shares'])
                    col_b.metric("Position", f"${sig['position_value']:,.0f}")
                    col_c.metric("Risk", f"${sig['risk']:.2f}")
                    col_d.metric("Reward", f"${sig['reward']:.2f}")
                    
                    st.markdown("---")
        
        # Quick Reference
        st.subheader("📖 Quick Reference Guide")
        
        with st.expander("How to use this dashboard"):
            st.markdown("""
            **1. SCAN MARKET** - Click the button to find current opportunities
            
            **2. COPY THE TRADE** - Look at BUY signals (green) or SELL signals (red)
            
            **3. CHECK CONFIDENCE** - Higher % = more reliable signal
            
            **4. CALCULATE POSITION** - Shows how many shares to buy
            
            **5. SET ALERTS** - Get notified when signals appear
            
            ---
            
            **Risk Management:**
            - Never risk more than 1-2% per trade
            - Use the stop loss shown
            - Target should be 2x the risk
            """)
        
        with st.expander("Signal Colors Explained"):
            st.markdown("""
            🟢 **GREEN (BUY)** - Stock is likely to go UP
            - Buy at the Entry price
            - Set stop loss at the Stop price
            - Take profit at the Target price
            
            🔴 **RED (SELL)** - Stock is likely to go DOWN
            - Short sell at the Entry price
            - Cover at the Target price
            - Stop loss at the Stop price
            
            📊 **Confidence** - Higher % means more indicators agree
            """)
    
    else:
        # No signals yet
        st.info("👆 Click 'SCAN MARKET NOW' to find trading opportunities")
        
        # Show sample trade
        st.subheader("📋 Sample Trade Format")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Symbol", "AAPL")
        col2.metric("Action", "BUY")
        col3.metric("Confidence", "75%")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Entry", "$178.50")
        col2.metric("Stop", "$175.00")
        col3.metric("Target", "$185.00")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Shares", "56")
        col2.metric("Risk", "$196")
        col3.metric("Reward", "$364")
        
        st.markdown("---")
        st.caption("This is what your trade signals will look like after scanning")

if __name__ == "__main__":
    render_trade_copier()
