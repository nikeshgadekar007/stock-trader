#!/usr/bin/env python3
lines = open('pages/swing_trading.py').readlines()
for i in range(411, len(lines)):
    l = lines[i]
    if l.startswith('        '):
        stripped = l.lstrip()
        groups = (len(l) - len(stripped)) // 4
        if groups >= 2:
            lines[i] = '    ' * (groups - 1) + stripped
open('pages/swing_trading.py', 'w').writelines(lines)
print('Done')

"""Fix indentation under if results:"""
with open('pages/swing_trading.py') as f:
    lines = f.readlines()

# Find the if results: line and fix indentation below it
for i, line in enumerate(lines):
    if line.strip() == 'if results:':
        # Fix all subsequent lines to 4-space indent if they're at 8
        for j in range(i+1, len(lines)):
            if lines[j].startswith('        ') and lines[j].strip():
                spaces = len(lines[j]) - len(lines[j].lstrip())
                if spaces >= 8:
                    lines[j] = '    ' + lines[j].lstrip()
            elif lines[j].startswith('        ') and not lines[j].strip():
                lines[j] = '\n'
            elif lines[j].startswith('    ') or not lines[j].strip():
                pass  # already correct or blank
            else:
                break  # end of the if block
        break

with open('pages/swing_trading.py', 'w') as f:
    f.writelines(lines)
print("Fixed")
# Verify
import ast
ast.parse(''.join(lines))
print("Syntax OK")