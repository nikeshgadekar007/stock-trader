"""
Broker Integration Page - Connect to IBKR
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brokers.ibkr_integration import get_ibkr_setup_instructions, get_manual_trade_steps, TRADE_TEMPLATE

def render_broker_page():
    """Render broker integration page"""
    st.header("🔗 Broker Integration")
    st.markdown("Connect your app to Interactive Brokers for automated trading")
    
    # Tab selection
    tab1, tab2, tab3 = st.tabs(["IBKR Setup", "Manual Trading", "Auto Trading"])
    
    with tab1:
        st.subheader("📋 IBKR Setup Guide")
        
        st.markdown("""
        ### Step 1: Enable API in IBKR TWS
        
        1. Open **Trader Workstation (TWS)**
        2. Go to **Edit** → **Preferences** → **API**
        3. Check ✅ **Enable ActiveX and Socket Clients**
        4. Set **Socket port** to:
           - `7496` for Paper Trading
           - `7497` for Live Trading
        5. Add your IP: `127.0.0.1` (localhost)
        6. Click **Apply** and **OK**
        """)
        
        st.markdown("""
        ### Step 2: Install IB API
        
        ```bash
        pip install ib_insync
        ```
        """)
        
        st.markdown("""
        ### Step 3: Start IB Gateway
        
        1. Download **IB Gateway** from interactivebrokers.com
        2. Log in with your IBKR credentials
        3. Select **Paper Trading** account for testing
        4. Go to **Settings** → **API** → Enable socket connections
        5. Keep IB Gateway running
        """)
        
        st.info("💡 Make sure IB Gateway/TWS is running before connecting!")
    
    with tab2:
        st.subheader("📱 Manual Trading in IBKR")
        
        st.markdown("""
        ### How to Enter Trade from App:
        
        1. **Open IBKR** → Trade tab
        2. **Search symbol** (e.g., TSLA)
        3. **Select BUY or SELL**
        4. **Enter Quantity** from app
        5. **Order Type**: LIMIT
        6. **Price**: Entry price from app
        7. **Advanced Options**:
           - Stop Loss: from app
           - Take Profit: from app
        8. **Submit Order**
        """)
        
        st.markdown("---")
        
        # Example trade
        st.subheader("📋 Example Trade Entry")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Symbol", "TSLA")
        col2.metric("Action", "BUY")
        col3.metric("Qty", "40 shares")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Entry", "$245.50")
        col2.metric("Stop", "$242.00")
        col3.metric("Target", "$252.00")
        
        st.markdown("""
        **IBKR Steps:**
        1. Type `TSLA` in search
        2. Click **BUY**
        3. Quantity: `40`
        4. Order Type: **LMT**
        5. Price: `$245.50`
        6. Click **Advanced**
        7. Stop: `$242.00`
        8. Target: `$252.00`
        9. Submit!
        """)
    
    with tab3:
        st.subheader("🤖 Automated Trading")
        
        st.markdown("""
        ### Connect to IBKR for Auto-Trading
        
        Once connected, the app can:
        - ✅ Place orders automatically
        - ✅ Set stop loss
        - ✅ Set take profit targets
        - ✅ Monitor positions
        - ✅ Close trades at targets
        """)
        
        # Connection status
        try:
            from brokers.ibkr_trader import IBKRTrader, IBKR_AVAILABLE
            
            if not IBKR_AVAILABLE:
                st.warning("⚠️ ib_insync not installed. Run: `pip install ib_insync`")
            else:
                st.success("✅ ib_insync is installed")
                
                # Connection form
                st.subheader("🔌 Connect to IBKR")
                
                col1, col2 = st.columns(2)
                with col1:
                    host = st.text_input("Host", value="127.0.0.1")
                    port = st.selectbox("Port", [7496, 7497], index=0)
                
                with col2:
                    client_id = st.number_input("Client ID", value=1, min_value=1, max_value=10)
                
                if st.button("🔗 Connect", use_container_width=True):
                    with st.spinner("Connecting..."):
                        trader = IBKRTrader(host=host, port=port, client_id=client_id)
                        result = trader.connect()
                        
                        if result.get('success'):
                            st.success("✅ Connected to IBKR!")
                            st.json(result)
                            
                            # Get account info
                            account = trader.get_account_info()
                            st.json(account)
                            
                            trader.disconnect()
                        else:
                            st.error(f"❌ Connection failed: {result.get('error')}")
                
                st.markdown("---")
                
                # Demo trade
                st.subheader("🧪 Demo Trade (No Connection)")
                
                if st.button("📋 Generate Demo Trade", use_container_width=True):
                    from trade_copier import get_trade_copier_signals
                    signals = get_trade_copier_signals()
                    
                    if signals:
                        sig = signals[0]
                        st.success(f"Demo Trade Generated!")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Symbol", sig['symbol'])
                        col2.metric("Action", sig['action'])
                        col3.metric("Confidence", f"{sig['confidence']}%")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Entry", f"${sig['entry']:.2f}")
                        col2.metric("Stop", f"${sig['stop']:.2f}")
                        col3.metric("Target", f"${sig['target']:.2f}")
                        
                        st.info("💡 Connect IBKR to execute this trade automatically!")
                    else:
                        st.info("No signals available. Try scanning the market first.")
        
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    render_broker_page()