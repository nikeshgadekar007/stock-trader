import re

with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py') as f:
    text = f.read()

# Strategy: replace the entire dead table_data building block with just a comment + pass
# Match from "            table_data = []" up to "            pass  # old single-table disabled"
start_marker = '            table_data = []'
end_marker = '            pass  # old single-table disabled'

start_idx = text.find(start_marker)
end_idx = text.find(end_marker, start_idx)
if start_idx != -1 and end_idx != -1:
    # Calculate end of the end_marker
    end_of_marker = end_idx + len(end_marker)
    # Replace the dead block with a simple comment
    new_text = text[:start_idx] + '            # (Old single-table replaced by 3 tabs below)' + text[end_of_marker:]
    with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py', 'w') as f:
        f.write(new_text)
    print(f"Removed dead block ({end_idx - start_idx} chars)")
else:
    print(f"Not found: start={start_idx}, end={end_idx}")

import ast
ast.parse(open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py').read())
print('Syntax OK')