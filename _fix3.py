with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py') as f:
    text = f.read()

old = '        if all_signals:\n            # Build table data\n            # (Old single-table replaced by 3 tabs below), using tab wrapper above\n        else:\n            st.info("No signals generated. Click \'Analyze\' to scan stocks.")\n'
new = '        if all_signals:\n            # (Old single-table replaced by 3 tabs below)\n'
if old in text:
    text = text.replace(old, new)
    with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py', 'w') as f:
        f.write(text)
    print('Cleaned if/else')
else:
    print('Pattern not found')
import ast
ast.parse(open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py').read())
print('Syntax OK')
