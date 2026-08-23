import re

with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py') as f:
    text = f.read()

# Look for the line that defines tabs for cards
tab_start = text.find('    tab1, tab2, tab3 = st.tabs([\n')
if tab_start == -1:
    # Try alternative indentation
    tab_start = text.find('tab1, tab2, tab3 = st.tabs([\n')

# Find the end of tab3 block - look for the next def
after_tab3 = text.find('\ndef _render_signal_card', tab_start)
if tab_start == -1 or after_tab3 == -1:
    print(f'Markers not found: tab_start={tab_start}, after_tab3={after_tab3}')
else:
    # The tab block is from tab_start to after_tab3 (exclusive of next def)
    tab_block = text[tab_start:after_tab3]
    # Re-indent by 4 more spaces (each line)
    new_lines = []
    for line in tab_block.split('\n'):
        if line.strip():
            new_lines.append('    ' + line)
        else:
            new_lines.append(line)
    indented = '\n'.join(new_lines).rstrip() + '\n'
    new_text = (
        text[:tab_start]
        + indented
        + '\n    st.markdown("---")\n\n'
        + text[after_tab3:]
    )
    with open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py', 'w') as f:
        f.write(new_text)
    print(f'Re-indented tab block ({len(tab_block)} chars)')

import ast
ast.parse(open('/Users/nikeshgadekar/Documents/stock-trader/signal_dashboard.py').read())
print('Syntax OK')