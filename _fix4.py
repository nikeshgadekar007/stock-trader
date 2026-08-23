import re

with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py') as f:
    text = f.read()

# The issue: we have:
#   if all_signals:
#       # (Old single-table replaced by 3 tabs below)
#
#   st.markdown("---")     <-- needs to be at function level
#
#   tab1, tab2, tab3 = st.tabs([...])
#   with tab1: ...
#
# Fix: indent everything from "tab1, tab2, tab3 = st.tabs" through end of "with tab3" block to be inside the if.
# Then add a st.markdown("---") right after the if block (still at function level).

# Find the tab block
tab_start = text.find('        tab1, tab2, tab3 = st.tabs([')
# Find the end of tab3 block - look for the next "def " or class at function level
after_tab3 = text.find('def _render_signal_card', tab_start)
if tab_start == -1 or after_tab3 == -1:
    print('Markers not found')
else:
    # The tab block is from tab_start to after_tab3 (exclusive of next def)
    tab_block = text[tab_start:after_tab3]
    # Re-indent by 4 more spaces
    indented = '\n'.join('    ' + line if line.strip() else line for line in tab_block.split('\n'))
    # Remove trailing whitespace
    indented = indented.rstrip() + '\n'
    # Build new content
    new_text = (
        text[:tab_start]
        + indented
        + '\n    st.markdown("---")\n\n'
        + text[after_tab3:]
    )
    with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py', 'w') as f:
        f.write(new_text)
    print('Re-indented tab block')

import ast
ast.parse(open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py').read())
print('Syntax OK')