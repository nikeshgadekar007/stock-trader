import re

with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py') as f:
    lines = f.readlines()

# Find the if all_signals: line and find the end of its block (next line at less indentation)
new_lines = []
in_if = False
if_indent = None
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.lstrip()
    indent = len(line) - len(stripped)
    if 'if all_signals:' in line and not in_if:
        # This is our target
        if_indent = indent
        in_if = True
        new_lines.append(line)
        # Replace the comment-only body with tab content
        i += 1
        # Skip until we find the tab definition
        while i < len(lines) and 'tab1, tab2, tab3 = st.tabs' not in lines[i]:
            i += 1
        # Now lines[i] is the tab definition - add it with correct indentation
        # All tab content should be at indent + 4
        target_indent = indent + 4
        # Add tabs and inner content
        while i < len(lines):
            tl = lines[i]
            tl_stripped = tl.lstrip()
            if not tl_stripped:
                new_lines.append(tl)
                i += 1
                continue
            # If we hit a line at less indent than target_indent, we're done
            tl_indent = len(tl) - len(tl_stripped)
            if tl_indent < target_indent and tl_stripped.strip():
                # End of if block
                break
            # Re-indent to target
            if tl_indent == indent:
                # Same indent as if - shouldn't happen
                break
            # Add extra indent to push it inside if
            new_lines.append(' ' * target_indent + tl_stripped)
            i += 1
        # Now add the closing of if block (de-dent back to if_indent) by NOT adding further
        continue
    new_lines.append(line)
    i += 1

with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py', 'w') as f:
    f.writelines(new_lines)
print('Done')

import ast
ast.parse(open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py').read())
print('Syntax OK')