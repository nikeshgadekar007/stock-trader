"""Backtesting Page for Strategy Testing"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from backtesting import BacktestEngine

def render_backtesting_page():
    st.header("📊 Strategy Backtesting")
    st.markdown("Test your trading strategy on historical data to validate performance before real trading.")
    
    col1, col2 = st.columns(2)
    with col1:
        symbol = st.text_input("Stock Symbol", "AAPL", help="US Stock symbol").upper()
    with col2:
        interval = st.selectbox("Time Interval", ["5m", "15m", "30m", "1h"], index=0)
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        initial_capital = st.number_input("Initial Capital ($)", value=10000.0, min_value=1000.0)
    with col2:
        risk_per_trade = st.slider("Risk Per Trade (%)", 0.5, 5.0, 2.0) / 100
    with col3:
        atr_multiplier = st.slider("ATR Multiplier for Stop", 1.0, 3.0, 1.5, 0.1)
    
    run_btn = st.button("🚀 Run Backtest", type="primary", use_container_width=True)
    
    if run_btn:
        engine = BacktestEngine(initial_capital=initial_capital, risk_per_trade=risk_per_trade)
        
        with st.spinner("Running backtest... This may take a moment."):
            results = engine.run_backtest(
                symbol=symbol,
                start_date=str(start_date),
                end_date=str(end_date),
                interval=interval,
                atr_multiplier=atr_multiplier
            )
        
        if 'error' in results:
            st.error(results['error'])
        else:
            st.success("✅ Backtest Complete!")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Return", f"{results['total_return']:.2f}%", 
                         delta="🟢" if results['total_return'] > 0 else "🔴")
            with col2:
                st.metric("Win Rate", f"{results['win_rate']:.1f}%")
            with col3:
                st.metric("Total Trades", results['total_trades'])
            with col4:
                st.metric("Profit Factor", f"{results['profit_factor']:.2f}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Final Capital", f"${results['final_capital']:,.2f}")
            with col2:
                st.metric("Winning Trades", results['winning_trades'])
            with col3:
                st.metric("Losing Trades", results['losing_trades'])
            with col4:
                st.metric("Max Drawdown", f"{results['max_drawdown']:.2f}%")
            
            st.markdown("---")
            st.subheader("📈 Trade History")
            
            if results['trades']:
                trades_df = pd.DataFrame(results['trades'])
                trades_df['pnl'] = trades_df['pnl'].apply(lambda x: f"${x:.2f}")
                st.dataframe(trades_df, use_container_width=True)
                
                st.markdown("---")
                st.subheader("📊 Exit Reason Analysis")
                
                exit_reasons = trades_df['exit_reason'].value_counts()
                for reason, count in exit_reasons.items():
                    emoji = "🎯" if reason == "TARGET_HIT" else "🛡️" if reason == "STOP_LOSS" else "⏰"
                    st.write(f"{emoji} {reason}: {count} trades ({count/len(trades_df)*100:.1f}%)")
            else:
                st.info("No trades generated during this period.")
            
            st.markdown("---")
            st.subheader("📋 Strategy Summary")
            
            if results['total_return'] > 10:
                st.success("🎉 **EXCELLENT STRATEGY!** Returns exceed 10%. Consider live testing.")
            elif results['total_return'] > 0:
                st.info("📈 **POSITIVE STRATEGY** - Returns are positive but consider optimizing.")
            else:
                st.warning("⚠️ **NEGATIVE STRATEGY** - This strategy lost money. Consider adjusting parameters.")
            
            if results['win_rate'] >= 55:
                st.success(f"✅ High win rate ({results['win_rate']:.1f}%) - Good for intraday trading")
            elif results['win_rate'] >= 45:
                st.info(f"📊 Moderate win rate ({results['win_rate']:.1f}%) - Acceptable with good R:R")
            else:
                st.warning(f"⚠️ Low win rate ({results['win_rate']:.1f}%) - Need better entry signals")
            
            if results['max_drawdown'] > 20:
                st.warning(f"⚠️ High max drawdown ({results['max_drawdown']:.1f}%) - Risk management needs improvement")
            else:
                st.success(f"✅ Controlled drawdown ({results['max_drawdown']:.1f}%) - Good risk management")
    
    st.markdown("---")
    st.markdown("""
    ### 📚 How to Interpret Results
    
    | Metric | Good | Acceptable | Poor |
    |--------|------|------------|------|
    | Total Return | > 10% | 0-10% | < 0% |
    | Win Rate | > 55% | 45-55% | < 45% |
    | Profit Factor | > 1.5 | 1.0-1.5 | < 1.0 |
    | Max Drawdown | < 10% | 10-20% | > 20% |
    
    ### 🎯 Tips for Better Results
    1. Test on different market conditions (trending vs ranging)
    2. Adjust ATR multiplier based on stock volatility
    3. Consider the time of day - first hour often more volatile
    4. Higher win rate isn't always better - focus on overall return
    """)