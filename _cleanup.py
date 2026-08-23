with open('signal_dashboard.py') as f:
    text = f.read()

# Find the dead sort block and remove it
start = text.find('pass  # old single-table disabled')
end = text.find('else:', start)
print(f"start={start}, end={end}")
if start != -1 and end != -1:
    # Keep everything up to and including "pass  # old single-table disabled\n"
    # Then keep "else:" and what follows
    pass_line_end = text.find('\n', start) + 1
    new_text = text[:pass_line_end] + '\n' + text[end:]
    text = new_text
    print("Removed dead code")

with open('signal_dashboard.py', 'w') as f:
    f.write(text)

import ast
ast.parse(open('signal_dashboard.py').read())
print("Syntax OK")
