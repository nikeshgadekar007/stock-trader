"""
Daily Trading Workflow - Step by Step Guide
"""
import streamlit as st
from datetime import datetime

def render_daily_workflow():
    st.header("📋 Daily Trading Workflow")
    
    # Market status
    from analysis.intraday import get_market_session
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
    
    col2.write(f"Session: {session}")
    col3.write(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    
    st.markdown("---")
    
    # Step-by-step workflow
    st.subheader("🎯 Your Trading Checklist")
    
    # Step 1: Pre-market
    with st.expander("📌 STEP 1: Pre-Market Setup (8:00-9:30 AM)", expanded=True):
        st.markdown("""
        **Before market opens, do this:**
        1. Open app at http://localhost:8501
        2. Go to **Advanced Signals** page
        3. Enter stocks: `AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA`
        4. Click **Analyze** to get signals
        5. Note top BUY signals with prices
        """)
        
        if st.button("✅ I've completed pre-market setup"):
            st.session_state.step1_done = True
        
        if st.session_state.get('step1_done'):
            st.success("✓ Pre-market setup complete!")
    
    # Step 2: Wait for market open
    with st.expander("📌 STEP 2: Wait for Market Open (9:30 AM)"):
        st.markdown("""
        **After market opens:**
        1. Wait 15-30 minutes for market to settle
        2. Check if price is near your entry price
        3. Only enter if price is AT or BELOW entry
        4. Never chase a stock that's already moved up
        """)
        
        if st.button("✅ Market opened, waiting for entry"):
            st.session_state.step2_done = True
    
    # Step 3: Enter trade
    with st.expander("📌 STEP 3: Enter Trade"):
        st.markdown("""
        **When you find your entry:**
        
        | Field | Action |
        |-------|--------|
        | Entry Price | Enter ONLY if at/below signal price |
        | Stop Loss | Set immediately - App gives you this |
        | Target 1 | Set TP1 - App gives you this |
        | Target 2 | Set TP2 - App gives you this |
        
        **Position Size Formula:**
        ```
        Risk Amount = Total Capital × 2%
        Risk Per Share = Entry - Stop
        Shares to Buy = Risk Amount ÷ Risk Per Share
        ```
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            capital = st.number_input("Your Capital ($)", value=10000, key="trade_capital")
        with col2:
            risk_pct = st.slider("Risk Per Trade (%)", 1.0, 5.0, 2.0, key="trade_risk")
        
        risk_amount = capital * (risk_pct / 100)
        st.info(f"💰 Max Risk Per Trade: ${risk_amount:,.2f}")
        
        if st.button("✅ Trade entered with stop loss set"):
            st.session_state.step3_done = True
    
    # Step 4: Monitor trade
    with st.expander("📌 STEP 4: Monitor Trade"):
        st.markdown("""
        **During the trade:**
        
        | Scenario | Action |
        |----------|--------|
        | Price hits Target 1 | Sell 50% of shares |
        | Price hits Target 2 | Sell remaining shares |
        | Price hits Stop Loss | Exit immediately |
        | 3:00 PM arrives | Close all positions |
        | News event | Exit if major announcement |
        
        **REMEMBER:**
        - Never move your stop loss down
        - Let winners run, cut losers quick
        - Take partial profits at TP1
        """)
        
        if st.button("✅ Trade monitoring complete"):
            st.session_state.step4_done = True
    
    # Step 5: Post-market review
    with st.expander("📌 STEP 5: Post-Market Review (3:00 PM+)"):
        st.markdown("""
        **After market closes:**
        
        1. Go to **Portfolio** page
        2. Review all closed trades
        3. Calculate P&L for the day
        4. Write down what worked and what didn't
        5. Update watchlist for tomorrow
        
        **Daily Journal Entry:**
        - Date: ___________
        - Trades taken: ___
        - Win/Loss: ___
        - What went right: ___________
        - What to improve: ___________
        """)
        
        if st.button("✅ Daily review complete"):
            st.session_state.step5_done = True
    
    # Progress summary
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
    
    # Quick reference
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
        - Close ALL by 3 PM
        """)
    
    # Risk calculator
    st.markdown("---")
    st.subheader("🧮 Position Size Calculator")
    
    calc_col1, calc_col2, calc_col3 = st.columns(3)
    
    with calc_col1:
        entry = st.number_input("Entry Price ($)", value=185.0, key="calc_entry")
    with calc_col2:
        stop = st.number_input("Stop Loss ($)", value=182.5, key="calc_stop")
    with calc_col3:
        capital = st.number_input("Capital ($)", value=10000, key="calc_capital")
    
    risk_per_share = entry - stop
    risk_amount = capital * 0.02
    shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
    total_cost = shares * entry
    
    result_col1, result_col2, result_col3, result_col4 = st.columns(4)
    result_col1.metric("Risk/Share", f"${risk_per_share:.2f}")
    result_col2.metric("Max Risk", f"${risk_amount:,.2f}")
    result_col3.metric("Shares", str(shares))
    result_col4.metric("Total Cost", f"${total_cost:,.2f}")
    
    if total_cost > capital:
        st.warning(f"⚠️ Total cost (${total_cost:,.2f}) exceeds capital (${capital:,.2f})")
    else:
        usage = (total_cost / capital) * 100
        st.success(f"✓ Using {usage:.1f}% of capital")

# Initialize session state
if 'step1_done' not in st.session_state:
    st.session_state.step1_done = False
if 'step2_done' not in st.session_state:
    st.session_state.step2_done = False
if 'step3_done' not in st.session_state:
    st.session_state.step3_done = False
if 'step4_done' not in st.session_state:
    st.session_state.step4_done = False
if 'step5_done' not in st.session_state:
    st.session_state.step5_done = False