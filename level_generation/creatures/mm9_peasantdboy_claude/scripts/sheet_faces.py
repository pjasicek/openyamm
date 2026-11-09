"""Contact sheet of face_views.py renders: row 1 head views + 128 px sim, row 2 body views. Args: <dir> <prefix> <out> [mm9 head views png]"""
import sys, os
from PIL import Image
d, p, out = sys.argv[1:4]
hv = [f'{d}/{p}_{v}.png' for v in ('front', 'q34', 'profile', 'low', 'party', 'ear_l', 'ear_r')]
bv = [f'{d}/{p}_{v}.png' for v in ('body_front', 'body_q34', 'body_back')]
S = 420
r1 = [Image.open(f).convert('RGB').resize((S, S)) for f in hv if os.path.exists(f)]
if r1:
    sim = Image.open(hv[0]).convert('RGB').resize((48, 48), Image.LANCZOS).resize((S, S), Image.NEAREST)
    r1.append(sim)
r2 = [Image.open(f).convert('RGB').resize((S, S)) for f in bv if os.path.exists(f)]
rows = [r1, r2]
if len(sys.argv) > 4:
    m = Image.open(sys.argv[4]).convert('RGB'); rows.insert(0, [m.resize((int(m.width * S / m.height), S))])
W = max(sum(i.width for i in r) for r in rows if r)
s = Image.new('RGB', (W, S * len([r for r in rows if r])), (60, 60, 60)); y = 0
for r in rows:
    if not r: continue
    x = 0
    for i in r: s.paste(i, (x, y)); x += i.width
    y += S
s.save(out); print('SHEET', out)
