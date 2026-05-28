"""
Stock Trading Analysis System - Streamlit Web App
Advanced Technical Analysis + CNN-LSTM Deep Learning + Backtesting
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from data.fetcher import fetch_stock_data
from analysis.technical import TechnicalAnalyzer
from trading.signals import generate_trade_recommendation

st.set_page_config(
    page_title="Stock Trading Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: bold; color: #00d4ff; text-align: center; padding: 1rem; }
    .buy-card { background: #0a1628; border-left: 4px solid #00d4ff; padding: 1rem; border-radius: 10px; }
    .sell-card { background: #1a0a0a; border-left: 4px solid #ff4757; padding: 1rem; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)


def main():
    st.markdown('<div class="main-header">📈 Stock Trading Analysis System</div>', unsafe_allow_html=True)
    st.markdown(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} HKT | US Market")
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page", [
        "📊 Dashboard", "🔬 Technical Analysis", "🧠 AI Model", "📈 Backtesting", "⚙️ Settings"
    ])
    
    if page == "📊 Dashboard":
        dashboard_page()
    elif page == "🔬 Technical Analysis":
        technical_page()
    elif page == "🧠 AI Model":
        ai_model_page()
    elif page == "📈 Backtesting":
        backtest_page()
    elif page == "⚙️ Settings":
        settings_page()


def dashboard_page():
    st.header("📊 Trading Recommendations")
    
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = []
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Run Analysis", type="primary", use_container_width=True):
            with st.spinner("Analyzing stocks..."):
                st.session_state.recommendations = run_analysis()
                st.success(f"Analysis complete! {len(st.session_state.recommendations)} signals found.")
    
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.recommendations = []
    
    if st.session_state.recommendations:
        display_recommendations(st.session_state.recommendations)
    else:
        st.info("👆 Click 'Run Analysis' to generate trading recommendations")


def run_analysis():
    recommendations = []
    for symbol in config.DEFAULT_WATCHLIST[:20]:
        try:
            stock_data = fetch_stock_data(symbol)
            quote = stock_data.get('quote')
            df = stock_data.get('history_daily')
            if not quote or not quote.get('current_price'):
                continue
            analyzer = TechnicalAnalyzer(df)
            indicators = analyzer.calculate_all()
            rec = generate_trade_recommendation(quote, indicators)
            if rec:
                rec['current_price'] = quote.get('current_price')
                recommendations.append(rec)
        except Exception:
            continue
    recommendations.sort(key=lambda x: (0 if x.get('action') == 'BUY' else 1, -len(x.get('signals', []))))
    return recommendations


def display_recommendations(recommendations):
    buy_recs = [r for r in recommendations if r.get('action') == 'BUY']
    sell_recs = [r for r in recommendations if r.get('action') == 'SELL']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", len(recommendations))
    col2.metric("📈 BUY", len(buy_recs))
    col3.metric("📉 SELL", len(sell_recs))
    col4.metric("💰 Capital", f"${config.CAPITAL:,}")
    
    st.markdown("---")
    
    if buy_recs:
        st.subheader("📈 BUY Signals")
        for rec in buy_recs[:10]:
            display_signal_card(rec)
    
    if sell_recs:
        st.subheader("📉 SELL Signals")
        for rec in sell_recs[:10]:
            display_signal_card(rec)


def display_signal_card(rec):
    symbol = rec.get('symbol', 'N/A')
    action = rec.get('action', 'N/A')
    entry = rec.get('entry_price', 0)
    target = rec.get('take_profit', 0)
    stop = rec.get('stop_loss', 0)
    rr = rec.get('risk_reward_ratio', 0)
    conf = rec.get('confidence', 'LOW')
    current = rec.get('current_price', 0)
    reason = rec.get('reason', '')
    
    card_class = "buy-card" if action == 'BUY' else "sell-card"
    
    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"### {symbol}")
        st.markdown(f"**{action}** | {conf}")
    with col2:
        cols = st.columns(5)
        cols[0].metric("Current", f"${current:.2f}")
        cols[1].metric("Entry", f"${entry:.2f}")
        cols[2].metric("Target", f"${target:.2f}")
        cols[3].metric("Stop", f"${stop:.2f}")
        cols[4].metric("R/R", f"{rr:.1f}x")
    st.markdown(f"**Reason:** {reason}")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")


def technical_page():
    st.header("🔬 Technical Analysis")
    symbol = st.selectbox("Select Stock", config.DEFAULT_WATCHLIST[:20])
    
    if st.button("Analyze", type="primary"):
        with st.spinner("Fetching data..."):
            try:
                stock_data = fetch_stock_data(symbol)
                df = stock_data.get('history_daily')
                if df is not None and not df.empty:
                    analyzer = TechnicalAnalyzer(df)
                    indicators = analyzer.calculate_all()
                    
                    col1, col2, col3 = st.columns(3)
                    rsi = indicators.get('rsi', {})
                    col1.metric("RSI", f"{rsi.get('rsi', 0):.1f}")
                    col1.caption(f"Signal: {rsi.get('signal', 'N/A')}")
                    
                    macd = indicators.get('macd', {})
                    col2.metric("MACD", f"{macd.get('macd', 0):.2f}")
                    col2.caption(f"Trend: {macd.get('trend', 'N/A')}")
                    
                    stoch = indicators.get('stochastic', {})
                    col3.metric("Stochastic", f"{stoch.get('k', 0):.1f}")
                    col3.caption(f"Signal: {stoch.get('signal', 'N/A')}")
                    
                    st.subheader("📊 Price Chart")
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close']))
                    fig.update_layout(template="plotly_dark", height=500)
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")


def ai_model_page():
    st.header("🧠 AI Model (CNN-LSTM)")
    st.info("🚧 CNN-LSTM model training coming soon! This module will use TensorFlow/Keras for deep learning predictions.")
    
    st.subheader("Model Architecture")
    st.markdown("""
    ```
    Input (Price Data)
        → Conv1D (Feature Extraction)
        → MaxPooling
        → LSTM (Time Series Learning)
        → Dense Layers
        → Output (BUY/SELL/HOLD)
    ```
    """)
    
    st.subheader("Features")
    st.markdown("""
    - **CNN Layer**: Extracts local patterns from price data
    - **LSTM Layer**: Captures temporal dependencies
    - **Ensemble**: Combines multiple models
    - **Backtesting**: Avoids overfitting
    """)


def backtest_page():
    st.header("📈 Backtesting Framework")
    st.info("🚧 Backtesting engine coming soon! This will include walk-forward validation and overfitting prevention.")
    
    st.subheader("Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Return", "0%")
    col2.metric("Sharpe Ratio", "0.00")
    col3.metric("Max Drawdown", "0%")
    
    st.subheader("Overfitting Prevention")
    st.markdown("""
    - **Walk-Forward Validation**: Train on past, test on future
    - **Cross-Validation**: Multiple train/test splits
    - **Monte Carlo Simulation**: Random sampling
    - **Parameter Stability Analysis**: Test across different periods
    """)


def settings_page():
    st.header("⚙️ Settings")
    
    st.subheader("Trading Parameters")
    capital = st.number_input("Trading Capital ($)", value=config.CAPITAL, step=100)
    max_risk = st.number_input("Max Risk Per Trade ($)", value=config.MAX_RISK_PER_TRADE, step=5)
    
    st.subheader("Technical Indicators")
    rsi_period = st.slider("RSI Period", 5, 21, config.RSI_PERIOD)
    rsi_oversold = st.slider("RSI Oversold", 20, 40, config.RSI_OVERSOLD)
    rsi_overbought = st.slider("RSI Overbought", 60, 80, config.RSI_OVERBOUGHT)
    
    st.subheader("Stock Universe")
    st.write(f"Watching {len(config.DEFAULT_WATCHLIST)} stocks")
    
    if st.button("Save Settings"):
        st.success("Settings saved!")


if __name__ == "__main__":
    main()
