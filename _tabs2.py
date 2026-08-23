with open('signal_dashboard.py') as f:
    text = f.read()

# Wrap the existing summary table in 3 tabs
# Find the line: df = pd.DataFrame(table_data) and inject tab wrapper right before it
tab_block = '''            # Summary table in 3 tabs by signal type
            def _build_signal_table(sigs, label):
                if not sigs:
                    st.info(f"No {label} signals in this scan.")
                    return
                tdata = []
                for s in sigs:
                    ml_pred = s.get('ml_prediction', {})
                    backtest = s.get('backtest', {})
                    confidence = s.get('confidence', {})
                    tdata.append({
                        'Symbol': s['symbol'], 'Signal': s['signal'],
                        'Price': f"${s['current_price']:.2f}",
                        'Score': s['total_score'],
                        'Confidence': f"{confidence.get('confidence', 50):.0f}%",
                        'ML Signal': ml_pred.get('ml_signal', '—'),
                        'ML Conf': f"{ml_pred.get('ml_confidence', 0):.0f}%",
                        'Win Rate': f"{backtest.get('win_rate', 0):.0f}%",
                        'R:R': f"{s.get('risk_reward', 0):.1f}x",
                    })
                tdf = pd.DataFrame(tdata)
                st.dataframe(tdf, use_container_width=True, hide_index=True)
                csv = tdf.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download {label} Signals CSV",
                    data=csv,
                    file_name=f"signals_{label.lower()}.csv",
                    mime="text/csv",
                    key=f"dl_{label}",
                )

            tab_buy, tab_hold, tab_sell = st.tabs([
                f"🟢 BUY ({len(st.session_state.buy_signals)})",
                f"⚪ HOLD ({len(st.session_state.hold_signals)})",
                f"🔴 SELL ({len(st.session_state.sell_signals)})",
            ])
            with tab_buy:
                _build_signal_table(st.session_state.buy_signals, "BUY")
            with tab_hold:
                _build_signal_table(st.session_state.hold_signals, "HOLD")
            with tab_sell:
                _build_signal_table(st.session_state.sell_signals, "SELL")
            # Disable the single-table block below
            if False:'''

if 'df = pd.DataFrame(table_data)' in text:
    text = text.replace('df = pd.DataFrame(table_data)', tab_block + '\n            df = pd.DataFrame(table_data)')
    print("Inserted tab wrapper for summary table")
else:
    print("Could not find df assignment")

with open('signal_dashboard.py', 'w') as f:
    f.write(text)

import ast
ast.parse(open('signal_dashboard.py').read())
print("Syntax OK")