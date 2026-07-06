import re, sys
html = open('ship.html', 'r', encoding='utf-8').read()
m = re.search(r'<script type="module">(.*?)</script>', html, re.DOTALL)
if not m: print('No module script'); sys.exit(1)
js = m.group(1)
stack, ln, ins, sc, esc, lc, bc, pc = [], 1, False, None, False, False, False, ''
for ch in js:
    if ch == '\n': ln += 1; lc = False; pc = ch; continue
    if lc: pc = ch; continue
    if bc:
        if pc == '*' and ch == '/': bc = False
        pc = ch; continue
    if esc: esc = False; pc = ch; continue
    if ins:
        if ch == '\\': esc = True
        elif ch == sc: ins = False
        pc = ch; continue
    if pc == '/' and ch == '/': lc = True; pc = ch; continue
    if pc == '/' and ch == '*': bc = True; pc = ch; continue
    if ch in '"\'`': ins = True; sc = ch; pc = ch; continue
    if ch in '{([': stack.append((ch, ln))
    elif ch in '})]':
        exp = {'}': '{', ')': '(', ']': '['}[ch]
        if not stack: print(f'ERR: unmatched {ch} at line {ln}'); sys.exit(1)
        o, ol = stack.pop()
        if o != exp: print(f'ERR: mismatch at line {ln}: {o}@{ol} vs {ch}'); sys.exit(1)
    pc = ch
if stack: print(f'ERR: unclosed {stack[-1][0]} at line {stack[-1][1]} ({len(stack)} total)'); sys.exit(1)
print(f'OK - {ln} lines balanced')
