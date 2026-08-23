import re

with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py') as f:
    lines = f.readlines()

# Find the broken block and replace it cleanly
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if '        if all_signals:\n' == line or '    if all_signals:\n' == line:
        # Check if next non-empty line is the tab def at same indent
        if i + 1 < len(lines) and 'tab1, tab2, tab3 = st.tabs' in lines[i + 1]:
            # Keep the if line and replace the broken block with properly indented content
            # Find indent level
            indent = len(line) - len(line.lstrip())
            new_lines.append(line)
            i += 1
            # Now process the tab block, adding 4 spaces of indent
            while i < len(lines):
                tl = lines[i]
                tl_stripped = tl.lstrip()
                if tl_stripped == '':
                    # blank line, keep
                    new_lines.append(tl)
                    i += 1
                    continue
                tl_indent = len(tl) - len(tl_stripped)
                # If we hit a line with less or equal indent than the if line, we're done
                if tl_indent <= indent:
                    break
                # Re-indent to tl_indent + 4 (push deeper into if)
                new_lines.append(' ' * (tl_indent + 4) + tl_stripped)
                i += 1
            continue
    new_lines.append(line)
    i += 1

with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py', 'w') as f:
    f.writelines(new_lines)

import ast
ast.parse(open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py').read())
print('Syntax OK')