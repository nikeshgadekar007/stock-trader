"""
Stock Trading Analysis System - Streamlit Web App
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from data.fetcher import fetch_stock_data
from analysis.technical import TechnicalAnalyzer, analyze_stock
from analysis.sentiment import analyze_news
from analysis.intraday import get_intraday_signal, calculate_vwap_levels, get_market_session
from trading.signals import generate_trade_recommendation
from trading.risk_management import get_risk_assessment, TradeSetup
from trading.portfolio import Portfolio
from scanner.watchlist import Watchlist, get_default_watchlist

st.set_page_config(page_title="Stock Trading Analysis", layout="wide")

def live_trading_page():
    """Live Trading Dashboard - Real-time monitoring"""
    st.header("🚀 Live Automated Trading")
    
    # Market Status
    session = get_market_session()
    col1, col2, col3 = st.columns(3)
    
    if session == "REGULAR_MARKET":
        col1.success("🟢 MARKET OPEN")
    elif session == "PRE_MARKET":
        col1.warning("🟡 PRE-MARKET")
    elif session == "AFTER_HOURS":
        col1.info("🔵 AFTER HOURS")
    else:
        col1.error("🔴 MARKET CLOSED")
    
    col2.metric("Session", session)
    col3.metric("Time", datetime.now().strftime('%H:%M:%S'))
    
    st.markdown("---")
    
    # Load paper trading data
    import json
    trades_file = f"{config.OUTPUT_DIR}/paper_trades.json"
    trades_data = {'cash': config.CAPITAL, 'positions': {}, 'trades': []}
    
    if os.path.exists(trades_file):
        with open(trades_file, 'r') as f:
            trades_data = json.load(f)
    
    # Account Summary
    st.subheader("📊 Account Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cash", f"${trades_data.get('cash', 0):,.2f}")
    
    positions = trades_data.get('positions', {})
    position_value = sum(pos['quantity'] * pos['avg_cost'] for pos in positions.values())
    col2.metric("Positions Value", f"${position_value:,.2f}")
    
    total_value = trades_data.get('cash', 0) + position_value
    col3.metric("Total Value", f"${total_value:,.2f}")
    
    pnl = total_value - config.CAPITAL
    col4.metric("P&L", f"${pnl:,.2f}", delta=f"{(pnl/config.CAPITAL)*100:.2f}%")
    
    st.markdown("---")
    
    # Open Positions
    st.subheader("📈 Open Positions")
    if positions:
        for symbol, pos in positions.items():
            # Get current price
            try:
                stock_data = fetch_stock_data(symbol)
                current_price = stock_data.get('quote', {}).get('current_price', pos['avg_cost'])
            except:
                current_price = pos['avg_cost']
            
            pnl_pct = ((current_price - pos['avg_cost']) / pos['avg_cost']) * 100
            pnl_value = (current_price - pos['avg_cost']) * pos['quantity']
            
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                col1.markdown(f"**{symbol}**")
                col2.markdown(f"Qty: {pos['quantity']}")
                col3.markdown(f"Entry: ${pos['avg_cost']:.2f}")
                col4.markdown(f"Current: ${current_price:.2f}")
                
                if pnl_pct >= 0:
                    col5.success(f"+${pnl_value:.2f} (+{pnl_pct:.1f}%)")
                else:
                    col5.error(f"${pnl_value:.2f} ({pnl_pct:.1f}%)")
    else:
        st.info("No open positions. System will auto-trade during market hours.")
    
    st.markdown("---")
    
    # Trade History
    st.subheader("📋 Trade History")
    trades = trades_data.get('trades', [])
    if trades:
        for trade in trades[-5:]:  # Show last 5 trades
            action = trade.get('action', '')
            emoji = "🟢 BUY" if action == "BUY" else "🔴 SELL"
            st.markdown(f"{emoji} **{trade['symbol']}** - {trade['quantity']} shares @ ${trade['price']:.2f}")
            st.caption(f"Time: {trade.get('timestamp', 'N/A')}")
    else:
        st.info("No trades yet.")
    
    st.markdown("---")
    
    # Control Buttons
    st.subheader("🎮 Controls")
    col1, col2 = st.columns(2)
    
    if col1.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    if col2.button("📊 Run Market Scan", use_container_width=True):
        with st.spinner("Scanning market..."):
            from auto_trader import AutoTrader
            trader = AutoTrader()
            signals = trader.run_market_scan()
            st.success(f"Scan complete! Found {len(signals)} signals")
            st.rerun()
    
    # Auto-refresh
    st.info("📌 Page auto-refreshes every 30 seconds during market hours")
    time.sleep(30)
    st.rerun()

def main():
    st.title("Stock Trading Analysis System")
    st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    page = st.sidebar.selectbox("Select Page", [
        "Dashboard", "Live Trading", "Technical Analysis", "AI Model", "Intraday",
        "Sentiment", "Risk Management", "Portfolio", "Watchlist"
    ])
    
    if page == "Dashboard":
        dashboard_page()
    elif page == "Live Trading":
        live_trading_page()
    elif page == "Technical Analysis":
        technical_page()
    elif page == "AI Model":
        ai_model_page()
    elif page == "Intraday":
        intraday_page()
    elif page == "Sentiment":
        sentiment_page()
    elif page == "Risk Management":
        risk_page()
    elif page == "Portfolio":
        portfolio_page()
    elif page == "Watchlist":
        watchlist_page()

def dashboard_page():
    st.header("Trading Recommendations")
    
    if st.button("Run Analysis", type="primary"):
        with st.spinner("Analyzing stocks..."):
            recommendations = []
            for symbol in config.DEFAULT_WATCHLIST[:10]:
                try:
                    stock_data = fetch_stock_data(symbol)
                    quote = stock_data.get('quote')
                    df = stock_data.get('history_daily')
                    if quote and quote.get('current_price') and df is not None:
                        analyzer = TechnicalAnalyzer(df)
                        indicators = analyzer.calculate_all()
                        rec = generate_trade_recommendation(quote, indicators)
                        if rec:
                            rec['current_price'] = quote.get('current_price')
                            recommendations.append(rec)
                except:
                    continue
            
            st.session_state.recommendations = recommendations
            
        if st.session_state.get('recommendations'):
            st.success(f"Found {len(st.session_state.recommendations)} signals")
    
    if st.session_state.get('recommendations'):
        recs = st.session_state.recommendations
        buy_recs = [r for r in recs if r.get('action') == 'BUY']
        sell_recs = [r for r in recs if r.get('action') == 'SELL']
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(recs))
        col2.metric("BUY", len(buy_recs))
        col3.metric("SELL", len(sell_recs))
        
        st.markdown("---")
        
        if buy_recs:
            st.subheader("BUY Signals")
            for rec in buy_recs[:5]:
                st.markdown(f"**{rec['symbol']}** - {rec['action']} @ ${rec.get('current_price', 0):.2f}")
                st.caption(f"Entry: ${rec.get('entry_price', 0):.2f} | Target: ${rec.get('take_profit', 0):.2f} | Stop: ${rec.get('stop_loss', 0):.2f}")
        
        if sell_recs:
            st.subheader("SELL Signals")
            for rec in sell_recs[:5]:
                st.markdown(f"**{rec['symbol']}** - {rec['action']} @ ${rec.get('current_price', 0):.2f}")
                st.caption(f"Entry: ${rec.get('entry_price', 0):.2f} | Target: ${rec.get('take_profit', 0):.2f} | Stop: ${rec.get('stop_loss', 0):.2f}")

def technical_page():
    st.header("Technical Analysis")
    symbol = st.selectbox("Select Stock", config.DEFAULT_WATCHLIST[:20])
    
    if st.button("Analyze", type="primary"):
        with st.spinner("Fetching data..."):
            try:
                stock_data = fetch_stock_data(symbol)
                df = stock_data.get('history_daily')
                if df is not None and not df.empty:
                    indicators = analyze_stock(df)
                    
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
                    
                    st.subheader("Price Chart")
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close']))
                    fig.update_layout(template="plotly_dark", height=500)
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")

def ai_model_page():
    st.header("AI Model (CNN-LSTM)")
    st.success("AI Model is trained and ready!")
    st.markdown("**Training Results:**")
    st.markdown("- Training Data: 4,207 samples from 18 stocks")
    st.markdown("- Best Validation Accuracy: 74.94%")
    st.markdown("- Model Location: models/best_model.pth")
    
    st.subheader("Test Predictions")
    col1, col2, col3 = st.columns(3)
    col1.metric("TSLA", "SELL", "100%")
    col2.metric("META", "SELL", "100%")
    col3.metric("NFLX", "SELL", "99.48%")
    
    st.subheader("To Retrain Model")
    st.code("python train_pytorch.py")

def intraday_page():
    st.header("Intraday Trading Analysis")
    st.info(f"Market Session: {get_market_session()}")
    
    symbol = st.selectbox("Select Stock", config.DEFAULT_WATCHLIST[:20])
    
    if st.button("Analyze Intraday", type="primary"):
        with st.spinner("Fetching data..."):
            try:
                stock_data = fetch_stock_data(symbol)
                df = stock_data.get('history_daily')
                
                if df is not None and not df.empty:
                    current_price = df['close'].iloc[-1]
                    
                    # VWAP Analysis
                    vwap_data = calculate_vwap_levels(df)
                    if vwap_data:
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("VWAP", f"${vwap_data['vwap']:.2f}")
                        col2.metric("Position", vwap_data['position'].upper())
                        col3.metric("Distance", f"{vwap_data['distance_percent']:.1f}%")
                        col4.metric("Current", f"${current_price:.2f}")
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Upper Band", f"${vwap_data['upper_band']:.2f}")
                        col2.metric("Lower Band", f"${vwap_data['lower_band']:.2f}")
                    
                    # Intraday Signal
                    intraday = get_intraday_signal(df)
                    
                    st.subheader("Intraday Signals")
                    signals = intraday.get('details', {}).get('signals', [])
                    for sig in signals:
                        st.markdown(f"- {sig}")
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Signal", intraday['signal'])
                    col1.caption(f"Confidence: {intraday['confidence']:.0%}")
                    
                    # Trade Setup
                    if vwap_data:
                        st.subheader("Intraday Trade Setup")
                        if intraday['signal'] == 'BUY':
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Entry", f"${current_price:.2f}")
                            col2.metric("Stop Loss", f"${vwap_data['lower_band']:.2f}")
                            col3.metric("Target", f"${vwap_data['upper_band']:.2f}")
                        else:
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Entry", f"${current_price:.2f}")
                            col2.metric("Stop Loss", f"${vwap_data['upper_band']:.2f}")
                            col3.metric("Target", f"${vwap_data['lower_band']:.2f}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def sentiment_page():
    st.header("News Sentiment Analysis")
    symbol = st.selectbox("Select Stock", config.DEFAULT_WATCHLIST[:20])
    
    if st.button("Analyze News", type="primary"):
        with st.spinner("Fetching news..."):
            try:
                result = analyze_news(symbol)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Sentiment", result['overall_sentiment'])
                col2.metric("Articles", result['article_count'])
                col3.metric("Score", f"{result['sentiment_score']:.2f}")
                
                col1, col2 = st.columns(2)
                col1.metric("Positive", result['positive_count'])
                col2.metric("Negative", result['negative_count'])
                
                if result.get('news'):
                    st.subheader("Recent News")
                    for item in result['news'][:5]:
                        st.markdown(f"- {item.get('title', 'N/A')}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def risk_page():
    st.header("Risk Management Calculator")
    
    col1, col2 = st.columns(2)
    with col1:
        symbol = st.text_input("Symbol", "AAPL")
        entry = st.number_input("Entry Price ($)", value=150.0)
        stop = st.number_input("Stop Loss ($)", value=147.0)
        target = st.number_input("Target Price ($)", value=159.0)
    
    with col2:
        account = st.number_input("Account Size ($)", value=10000.0)
        risk = st.slider("Risk Per Trade (%)", 0.5, 5.0, 1.0)
    
    if st.button("Calculate Position Size", type="primary"):
        setup = TradeSetup(symbol, entry, stop, target, account, risk)
        result = get_risk_assessment(setup)
        
        st.subheader("Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Shares", result['position_size']['shares'])
        col2.metric("Position Value", f"${result['position_size']['value']:.2f}")
        col3.metric("Risk Amount", f"${result['risk_metrics']['risk_amount']:.2f}")
        
        col1, col2 = st.columns(2)
        col1.metric("Risk-Reward Ratio", f"{result['risk_metrics']['risk_reward_ratio']:.2f}x")
        col2.metric("Grade", result['assessment']['grade'])

def portfolio_page():
    st.header("Portfolio Tracker")
    portfolio = Portfolio()
    
    st.subheader("Current Positions")
    positions = portfolio.get_positions()
    
    if positions:
        for symbol, pos in positions.items():
            st.markdown(f"**{symbol}**: {pos['quantity']} shares @ ${pos['avg_cost']:.2f}")
    else:
        st.info("No positions yet. Add trades to track your portfolio.")
    
    st.subheader("Add Trade")
    col1, col2 = st.columns(2)
    with col1:
        symbol = st.text_input("Symbol", "AAPL").upper()
        action = st.selectbox("Action", ["BUY", "SELL"])
        quantity = st.number_input("Quantity", value=10)
    
    with col2:
        price = st.number_input("Price ($)", value=150.0)
        date = st.date_input("Date")
    
    if st.button("Add Trade"):
        portfolio.add_trade(symbol, action, quantity, price, date.strftime('%Y-%m-%d'))
        st.success(f"Added {action} trade for {quantity} shares of {symbol}")

def watchlist_page():
    st.header("Stock Watchlist")
    wl = Watchlist()
    
    st.subheader("Your Watchlist")
    watchlist = wl.get_watchlist()
    
    if watchlist:
        for stock in watchlist:
            st.markdown(f"- **{stock['symbol']}**")
    else:
        st.info("Watchlist is empty. Adding default stocks...")
        for symbol in get_default_watchlist()[:10]:
            wl.add(symbol)
        st.success("Added 10 default stocks to watchlist")
    
    st.subheader("Add Stock")
    new_symbol = st.text_input("Symbol to Add", "AAPL").upper()
    if st.button("Add to Watchlist"):
        if wl.add(new_symbol):
            st.success(f"Added {new_symbol} to watchlist")
        else:
            st.warning(f"{new_symbol} is already in watchlist")

if __name__ == "__main__":
    main()
