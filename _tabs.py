with open('signal_dashboard.py') as f:
    text = f.read()
old = 'tab1, tab2, tab3 = st.tabs(["🟢 BUY Signals", "⚪ HOLD Signals", "🔴 SELL Signals"])'
new = 'tab1, tab2, tab3 = st.tabs([\n        f"🟢 BUY ({len(st.session_state.buy_signals)})",\n        f"⚪ HOLD ({len(st.session_state.hold_signals)})",\n        f"🔴 SELL ({len(st.session_state.sell_signals)})",\n    ])'
if old in text:
    text = text.replace(old, new)
    with open('signal_dashboard.py', 'w') as f:
        f.write(text)
    print("Updated")
else:
    print("NOT FOUND")
import ast
ast.parse(open('signal_dashboard.py').read())
print("Syntax OK")
