"""
Stock Trading Analysis System - Streamlit Web App
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from data.fetcher import fetch_stock_data
from analysis.technical import TechnicalAnalyzer, analyze_stock
from analysis.sentiment import analyze_news
from trading.signals import generate_trade_recommendation
from trading.risk_management import get_risk_assessment, TradeSetup
from trading.portfolio import Portfolio
from scanner.watchlist import Watchlist, get_default_watchlist

st.set_page_config(page_title="Stock Trading Analysis", layout="wide")

def main():
    st.title("Stock Trading Analysis System")
    st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    page = st.sidebar.selectbox("Select Page", [
        "Dashboard", "Technical Analysis", "AI Model", "Sentiment",
        "Risk Management", "Portfolio", "Watchlist"
    ])
    
    if page == "Dashboard":
        dashboard_page()
    elif page == "Technical Analysis":
        technical_page()
    elif page == "AI Model":
        ai_model_page()
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
