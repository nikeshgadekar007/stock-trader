with open('signal_dashboard.py') as f:
    text = f.read()

# Replace the `if False: ... df = pd.DataFrame(table_data)` setup with a proper structure
# The previous insertion left an `if False:` followed by `df = pd.DataFrame` which is invalid
# Let's fix it by removing the if False and properly handling the table build

old = '''            # Disable the single-table block below
            if False:
            df = pd.DataFrame(table_data)'''

new = '''            pass  # old single-table disabled, using tab wrapper above'''

if old in text:
    text = text.replace(old, new)
    print("Fixed if-False remnant")
else:
    print("Old pattern not found")

with open('signal_dashboard.py', 'w') as f:
    f.write(text)

import ast
ast.parse(open('signal_dashboard.py').read())
print("Syntax OK")