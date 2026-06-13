"""
Daily Trading Workflow - Step by Step Guide
"""
import streamlit as st
from datetime import datetime, timezone, timedelta

def get_hk_time():
    utc = timezone.utc
    now_utc = datetime.now(utc)
    hk_offset = timedelta(hours=8)
    hk = timezone(hk_offset)
    now_hk = now_utc.astimezone(hk)
    return now_hk

def get_us_market_time():
    utc = timezone.utc
    now_utc = datetime.now(utc)
    est_offset = timedelta(hours=-5)
    est = timezone(est_offset)
    now_est = now_utc.astimezone(est)
    return now_est

def render_daily_workflow():
    st.header("📋 Daily Trading Workflow")
    
    hk_now = get_hk_time()
    us_now = get_us_market_time()
    us_hour = us_now.hour
    
    col1, col2, col3 = st.columns(3)
    if 21 <= us_hour or us_hour < 4:
        col1.warning("🟡 US PRE-MARKET")
    elif 4 <= us_hour < 9:
        col1.info("🔵 US AFTER HOURS")
    elif 9 <= us_hour < 16:
        col1.success("🟢 US MARKET OPEN")
    else:
        col1.error("🔴 US MARKET CLOSED")
    
    col2.success(f"🇭🇰 HK: {hk_now.strftime('%H:%M:%S')}")
    col3.info(f"🇺🇸 US: {us_now.strftime('%H:%M:%S')}")
    
    st.markdown("---")
    st.subheader("🎯 Your Trading Checklist")
    
    with st.expander("📌 STEP 1: Pre-Market Setup", expanded=True):
        st.markdown("""
        **Before market opens:**
        1. Open app at http://localhost:8501
        2. Go to **Advanced Signals** page
        3. Enter stocks: `AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA`
        4. Click **Analyze** to get signals
        5. Note top BUY signals with prices
        """)
        st.success("🕐 **HK Time: 9:30 PM - 10:00 PM**")
        st.info("🇺🇸 US Time: 8:30 AM - 9:00 AM EST")
        
        if st.button("✅ I've completed pre-market setup"):
            st.session_state.step1_done = True
        
        if st.session_state.get('step1_done'):
            st.success("✓ Pre-market setup complete!")
    
    with st.expander("📌 STEP 2: Wait for Market Open"):
        st.markdown("""
        **After market opens:**
        1. Wait 15-30 minutes for market to settle
        2. Check if price is near your entry price
        3. Only enter if price is AT or BELOW entry
        4. Never chase a stock that's already moved up
        """)
        st.success("🕐 **HK Time: 12:00 AM - 12:30 AM**")
        st.info("🇺🇸 US Time: 9:30 AM - 10:00 AM EST")
        
        if st.button("✅ Market opened, waiting for entry"):
            st.session_state.step2_done = True
    
    with st.expander("📌 STEP 3: Enter Trade"):
        st.markdown("""
        **When you find your entry:**
        - Entry Price: Enter ONLY if at/below signal price
        - Stop Loss: Set immediately
        - Target 1: Set TP1
        - Target 2: Set TP2
        """)
        st.success("🕐 **HK Time: 12:30 AM - 3:00 AM**")
        st.info("🇺🇸 US Time: 10:00 AM - 12:30 PM EST")
        
        col1, col2 = st.columns(2)
        with col1:
            capital = st.number_input("Your Capital ($)", value=10000, key="trade_capital")
        with col2:
            risk_pct = st.slider("Risk Per Trade (%)", 1.0, 5.0, 2.0, key="trade_risk")
        
        risk_amount = capital * (risk_pct / 100)
        st.info(f"💰 Max Risk Per Trade: ${risk_amount:,.2f}")
        
        if st.button("✅ Trade entered with stop loss set"):
            st.session_state.step3_done = True
    
    with st.expander("📌 STEP 4: Monitor Trade"):
        st.markdown("""
        **During the trade:**
        - Price hits Target 1: Sell 50% of shares
        - Price hits Target 2: Sell remaining shares
        - Price hits Stop Loss: Exit immediately
        - 3:00 PM arrives: Close all positions
        """)
        st.success("🕐 **HK Time: 3:00 AM - 4:00 AM**")
        st.info("🇺🇸 US Time: 12:30 PM - 1:30 PM EST")
        
        if st.button("✅ Trade monitoring complete"):
            st.session_state.step4_done = True
    
    with st.expander("📌 STEP 5: Post-Market Review"):
        st.markdown("""
        **After market closes:**
        1. Go to **Portfolio** page
        2. Review all closed trades
        3. Calculate P&L for the day
        4. Write down what worked and what didn't
        5. Update watchlist for tomorrow
        """)
        st.success("🕐 **HK Time: 5:00 AM - 6:00 AM**")
        st.info("🇺🇸 US Time: 2:30 PM - 3:30 PM EST")
        
        if st.button("✅ Daily review complete"):
            st.session_state.step5_done = True
    
    st.markdown("---")
    st.subheader("📊 Today's Progress")
    
    steps = [
        ("Pre-Market Setup", st.session_state.get('step1_done', False)),
        ("Wait for Entry", st.session_state.get('step2_done', False)),
        ("Enter Trade", st.session_state.get('step3_done', False)),
        ("Monitor Trade", st.session_state.get('step4_done', False)),
        ("Post-Market Review", st.session_state.get('step5_done', False)),
    ]
    
    completed = sum(1 for _, done in steps if done)
    progress = completed / len(steps) * 100
    
    st.progress(progress / 100, text=f"{completed}/{len(steps)} steps completed")
    
    for i, (name, done) in enumerate(steps, 1):
        if done:
            st.success(f"✓ Step {i}: {name}")
        else:
            st.info(f"○ Step {i}: {name}")
    
    st.markdown("---")
    st.subheader("🕐 Complete HK Time Schedule")
    
    st.markdown("""
    | Activity | HK Time | US Time |
    |----------|---------|---------|
    | Pre-Market Scan | 9:30 PM | 8:30 AM |
    | Market Opens | 12:00 AM | 9:30 AM |
    | Trading Hours | 12:00 AM - 4:00 AM | 9:30 AM - 4:00 PM |
    | Market Closes | 4:00 AM | 4:00 PM |
    | After Hours End | 9:30 AM | 8:00 PM |
    """)
    
    st.markdown("---")
    st.subheader("⚡ Quick Reference")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **📈 ENTRY RULES:**
        - Price must be at/below signal entry
        - All timeframes must align
        - Confidence > 60%
        - Volume above average
        """)
    with col2:
        st.markdown("""
        **🛑 EXIT RULES:**
        - Stop loss is MANDATORY
        - Sell 50% at TP1
        - Sell rest at TP2
        - Close ALL by 4 AM HK
        """)