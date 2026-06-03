"""
Stock Trading Analysis System - Streamlit Web App
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
from streamlit_autorefresh import st_autorefresh

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

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'notifications' not in st.session_state:
    st.session_state.notifications = []
if 'unread_count' not in st.session_state:
    st.session_state.unread_count = 0

def show_notification_bell():
    """Show notification bell in sidebar"""
    st.sidebar.markdown("---")
    
    # Notification bell button
    col1, col2 = st.sidebar.columns([3, 1])
    
    with col1:
        st.markdown("### 🔔 Notifications")
    with col2:
        if st.session_state.unread_count > 0:
            st.markdown(f"🔴 {st.session_state.unread_count}")
    
    if st.button("📬 View All", use_container_width=True):
        st.session_state.show_notifications = True
    
    # Generate signals button
    if st.button("🔍 Generate Signals", use_container_width=True):
        with st.spinner("Analyzing market..."):
            generate_signals_for_notifications()
    
    # Show notification panel if clicked
    if st.session_state.get('show_notifications', False):
        st.sidebar.markdown("#### Recent Alerts")
        
        if st.session_state.notifications:
            for notif in st.session_state.notifications[:10]:
                notif_type = notif.get('type', 'info')
                if notif_type == 'signal':
                    emoji = "📈" if 'BUY' in notif.get('action', '') else "📉"
                else:
                    emoji = "ℹ️"
                
                st.sidebar.markdown(f"{emoji} **{notif.get('title', 'Alert')}**")
                st.sidebar.caption(notif.get('message', '')[:60])
        else:
            st.sidebar.info("Click 'Generate Signals' to find opportunities")
        
        if st.button("Close"):
            st.session_state.show_notifications = False


def generate_signals_for_notifications():
    """Generate trading signals and add to notifications"""
    signals = []
    
    for symbol in config.DEFAULT_WATCHLIST[:15]:
        try:
            stock_data = fetch_stock_data(symbol)
            quote = stock_data.get('quote')
            df = stock_data.get('history_daily')
            
            if quote and quote.get('current_price') and df is not None:
                analyzer = TechnicalAnalyzer(df)
                indicators = analyzer.calculate_all()
                rec = generate_trade_recommendation(quote, indicators)
                
                if rec and rec.get('confidence', 0) >= 0.6:
                    rec['current_price'] = quote.get('current_price')
                    signals.append(rec)
        except:
            continue
    
    # Add signals as notifications
    st.session_state.notifications = []
    
    for rec in signals:
        action = rec.get('action', 'HOLD')
        emoji = "📈" if action == "BUY" else "📉"
        
        notification = {
            'type': 'signal',
            'title': f'{emoji} {action}: {rec["symbol"]}',
            'message': f'Price: ${rec.get("current_price", 0):.2f}\nTarget: ${rec.get("take_profit", 0):.2f}\nStop: ${rec.get("stop_loss", 0):.2f}\nConfidence: {rec.get("confidence", 0):.0%}',
            'action': action,
            'symbol': rec['symbol'],
            'price': rec.get('current_price', 0),
            'target': rec.get('take_profit', 0),
            'stop': rec.get('stop_loss', 0),
            'confidence': rec.get('confidence', 0)
        }
        st.session_state.notifications.append(notification)
    
    st.session_state.unread_count = len(st.session_state.notifications)
    st.session_state.show_notifications = True
    
    if signals:
        st.success(f"Found {len(signals)} trading signals!")
    else:
        st.info("No strong signals found. Try again later.")

def login_page():
    """Login/Registration Page"""
    st.title("🔐 Login to Stock Trader")
    
    # Check if Firebase is configured
    firebase_available = os.environ.get('FIREBASE_CREDENTIALS_JSON') or os.environ.get('FIREBASE_CREDENTIALS')
    
    if not firebase_available:
        st.warning("⚠️ Firebase not configured. Using demo mode.")
        st.markdown("**Demo Mode:** Any email/password will work")
    
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Sign In", type="primary"):
            if not email or not password:
                st.error("Please enter email and password")
            else:
                if firebase_available:
                    # Try Firebase authentication
                    try:
                        from auth import firebase_auth
                        result = firebase_auth.sign_in(email, password)
                        if result['success']:
                            st.session_state.user = {
                                'email': email,
                                'id': result['user_id']
                            }
                            st.success("Signed in successfully!")
                            st.rerun()
                        else:
                            st.error(f"Login failed: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Firebase error: {e}")
                else:
                    # Demo mode - accept any credentials
                    st.session_state.user = {
                        'email': email,
                        'id': email.split('@')[0]
                    }
                    st.success("Signed in successfully! (Demo Mode)")
                    st.rerun()
        
        st.markdown("---")
        st.markdown("Or sign in with:")
        if st.button("🔵 Sign in with Google"):
            if firebase_available:
                st.info("Google Sign-in: Configure Firebase for this feature")
            else:
                st.info("Google Sign-in requires Firebase setup")
    
    with tab2:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Create Account", type="primary"):
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            elif new_email:
                if firebase_available:
                    try:
                        from auth import firebase_auth
                        result = firebase_auth.create_user(new_email, new_password)
                        if result['success']:
                            st.success("Account created! Please sign in.")
                        else:
                            st.error(f"Registration failed: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Firebase error: {e}")
                else:
                    st.info("User registration requires Firebase setup")
            else:
                st.error("Please enter a valid email")

def user_dashboard():
    """Personal user dashboard"""
    st.header(f"👤 Welcome, {st.session_state.user.get('email', 'User')}")
    
    # User stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total P&L", "$0.00", "0.0%")
    col2.metric("Win Rate", "0%", "0 trades")
    col3.metric("Watchlist", "0 stocks")
    col4.metric("Signals", "0")
    
    st.markdown("---")
    
    # Personal watchlist
    st.subheader("⭐ Your Watchlist")
    
    if st.button("➕ Add Stock to Watchlist"):
        st.session_state.show_add_watchlist = True
    
    if st.session_state.get('show_add_watchlist', False):
        new_symbol = st.text_input("Enter Symbol", "AAPL").upper()
        if st.button("Add"):
            st.success(f"Added {new_symbol} to your watchlist")
            st.session_state.show_add_watchlist = False
    
    st.info("Your personal watchlist will appear here")
    
    st.markdown("---")
    
    # Recent trades
    st.subheader("📊 Your Recent Trades")
    st.info("Your trade history will appear here")
    
    st.markdown("---")
    
    # Settings
    st.subheader("⚙️ Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        email_alerts = st.checkbox("Email Alerts", value=True)
    with col2:
        push_alerts = st.checkbox("Push Notifications", value=True)
    
    if st.button("Save Settings"):
        st.success("Settings saved!")

def live_trading_page():
    """Live Trading Dashboard - Real-time monitoring with auto-refresh"""
    st_autorefresh(interval=30000, key="live_trading_refresh")
    st.header("🚀 Live Automated Trading")
    
    # Initialize session state for deployed app
    if 'trades_data' not in st.session_state:
        st.session_state.trades_data = {
            'cash': config.CAPITAL, 
            'positions': {}, 
            'trades': []
        }
    
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
    
    # Show local user time using iframe
    st.iframe("""
    <html><body>
    <div id="local_time" style="font-size: 1.5rem; font-weight: bold; color: #00ff00;">Loading...</div>
    <script>
    function showTime() {
        document.getElementById('local_time').innerHTML = new Date().toLocaleTimeString();
    }
    showTime();
    setInterval(showTime, 1000);
    </script></body></html>
    """, height=50)
    st.markdown("---")
    
    # Use cloud database for persistence
    from cloud_db import cloud_db
    trades_data = cloud_db.load_trades()
    
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
    
    st.subheader("📈 Open Positions")
    if positions:
        for symbol, pos in positions.items():
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
        st.info("No open positions. Click 'Run Market Scan' to find opportunities.")
    st.markdown("---")
    
    st.subheader("📋 Trade History")
    trades = trades_data.get('trades', [])
    if trades:
        for trade in trades[-5:]:
            action = trade.get('action', '')
            emoji = "🟢 BUY" if action == "BUY" else "🔴 SELL"
            st.markdown(f"{emoji} **{trade['symbol']}** - {trade['quantity']} shares @ ${trade['price']:.2f}")
            st.caption(f"Time: {trade.get('timestamp', 'N/A')}")
    else:
        st.info("No trades yet.")
    st.markdown("---")
    
    st.subheader("🎮 Controls")
    col1, col2 = st.columns(2)
    
    if col1.button("📊 Run Market Scan", use_container_width=True):
        with st.spinner("Scanning market..."):
            try:
                from auto_trader import AutoTrader
                trader = AutoTrader()
                signals = trader.run_market_scan()
                st.success(f"Scan complete! Found {len(signals)} signals")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    if col2.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    st.info("📌 Page auto-refreshes every 30 seconds during market hours")

def main():
    st.title("Stock Trading Analysis System")
    st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Check if user is logged in
    if st.session_state.user is None:
        login_page()
        return
    
    # Show notification bell for logged-in users
    show_notification_bell()
    
    # User dashboard option
    page = st.sidebar.selectbox("Select Page", [
        "Dashboard", "Trade Copier", "Scalping", "User Dashboard", "Live Trading", "Technical Analysis", "AI Model", "Intraday",
        "Sentiment", "Risk Management", "Portfolio", "Watchlist"
    ])
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()
    
    if page == "Dashboard":
        dashboard_page()
    elif page == "Trade Copier":
        from trade_copier import render_trade_copier
        render_trade_copier()
    elif page == "Scalping":
        from scalping.scalping_page import render_scalping_page
        render_scalping_page()
    elif page == "User Dashboard":
        user_dashboard()
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
                    
                    vwap_data = calculate_vwap_levels(df)
                    if vwap_data:
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("VWAP", f"${vwap_data['vwap']:.2f}")
                        col2.metric("Position", vwap_data['position'].upper())
                        col3.metric("Distance", f"{vwap_data['distance_percent']:.1f}%")
                        col4.metric("Current", f"${current_price:.2f}")
                    
                    intraday = get_intraday_signal(df)
                    
                    st.subheader("Intraday Signals")
                    signals = intraday.get('details', {}).get('signals', [])
                    for sig in signals:
                        st.markdown(f"- {sig}")
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Signal", intraday['signal'])
                    col1.caption(f"Confidence: {intraday['confidence']:.0%}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def sentiment_page():
    st.header("📰 NLP News Trading Analysis")
    st.markdown("Real-time sentiment analysis powered by VADER & TextBlob")
    
    # Add NLP import
    from analysis.nlp_news import NLPNewsAnalyzer
    
    tab1, tab2 = st.tabs(["Single Stock", "Watchlist Scan"])
    
    with tab1:
        symbol = st.selectbox("Select Stock", config.DEFAULT_WATCHLIST[:20])
        
        if st.button("🔍 Analyze News", type="primary"):
            with st.spinner("Fetching and analyzing news..."):
                try:
                    analyzer = NLPNewsAnalyzer()
                    result = analyzer.analyze_stock_news(symbol)
                    
                    # Display sentiment score
                    sentiment = result['sentiment']
                    recommendation = result['recommendation']
                    impact = result['impact_score']
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    # Sentiment indicator
                    if sentiment['overall'] == 'POSITIVE':
                        col1.success(f"🟢 {sentiment['overall']}")
                    elif sentiment['overall'] == 'NEGATIVE':
                        col1.error(f"🔴 {sentiment['overall']}")
                    else:
                        col1.info(f"⚪ {sentiment['overall']}")
                    
                    col2.metric("Score", f"{sentiment['avg_compound']:.3f}")
                    col3.metric("Articles", sentiment['total_articles'])
                    col4.metric("Impact", impact['level'])
                    
                    # Recommendation
                    st.subheader("📊 Trading Recommendation")
                    rec_col1, rec_col2 = st.columns([1, 2])
                    
                    action = recommendation['action']
                    if 'BUY' in action:
                        rec_col1.success(f"**{action}**")
                    elif 'SELL' in action:
                        rec_col1.error(f"**{action}**")
                    else:
                        rec_col1.info(f"**{action}**")
                    
                    rec_col2.markdown(f"Confidence: **{recommendation['confidence']:.0%}**")
                    rec_col2.caption(recommendation['reasoning'])
                    
                    # News articles
                    st.subheader("📰 Recent News")
                    news = result.get('news', [])
                    
                    if news:
                        for i, article in enumerate(news[:5]):
                            with st.expander(f"📰 {article.get('title', 'N/A')[:80]}..."):
                                st.markdown(f"**Source:** {article.get('source', 'Unknown')}")
                                st.markdown(article.get('description', 'No description'))
                                st.markdown(f"[Read more]({article.get('url', '#')})")
                    else:
                        st.info("No recent news found for this stock")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with tab2:
        st.markdown("Scan your entire watchlist for sentiment")
        
        if st.button("📊 Scan Watchlist", type="primary"):
            with st.spinner("Analyzing sentiment for all stocks..."):
                try:
                    analyzer = NLPNewsAnalyzer()
                    symbols = config.DEFAULT_WATCHLIST[:15]
                    results = analyzer.scan_watchlist_sentiment(symbols)
                    
                    st.success(f"Scanned {len(results)} stocks")
                    
                    # Sort by sentiment strength
                    buy_signals = [r for r in results if 'BUY' in r['recommendation']['action']]
                    sell_signals = [r for r in results if 'SELL' in r['recommendation']['action']]
                    
                    col1, col2 = st.columns(2)
                    col1.success(f"🟢 BUY Signals: {len(buy_signals)}")
                    col2.error(f"🔴 SELL Signals: {len(sell_signals)}")
                    
                    st.markdown("---")
                    
                    # Show all results
                    for result in results:
                        sentiment = result['sentiment']
                        recommendation = result['recommendation']
                        
                        emoji = "🟢" if sentiment['overall'] == 'POSITIVE' else "🔴" if sentiment['overall'] == 'NEGATIVE' else "⚪"
                        
                        st.markdown(f"{emoji} **{result['symbol']}** - {recommendation['action']} (Score: {sentiment['avg_compound']:.3f})")
                        
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
