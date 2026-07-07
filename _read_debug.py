import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('debug_output.txt', 'rb') as f:
    data = f.read()
# Try different encodings
for enc in ['utf-8', 'utf-16', 'utf-16-le', 'ascii']:
    try:
        text = data.decode(enc)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        print(f"Encoding: {enc}, lines: {len(lines)}")
        for l in lines[:8]:
            print(l[:300])
        break
    except:
        continue
