#!/usr/bin/env python3
"""Frame strips of every clip from the viewer: review/strip_<clip>.png six frames each at two azimuths, and one sheet of all. Args: tier id. Run from the repo root."""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
P = Path('level_generation/creatures/mm9_ghost_claude')
tier = sys.argv[1] if len(sys.argv) > 1 else 'ghost_b'
m = json.load(open(P / 'review/viewer/manifest.json'))
clips = list(m['clips'])
specs = []
for c in clips:
    d = m['clips'][c]['duration']
    for k in range(6):
        t = round(min(d - 0.001, d * k / 5), 3)
        specs.append(f'st{tier[-1]}_{c}_{k}:{c}:{t}:35:6:3.2:0.95')
print(len(specs))
chunks = [specs[i:i + 24] for i in range(0, len(specs), 24)]
for ch in chunks:
    r = subprocess.run(['python3', str(P / 'scripts/vshot.py'), '/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/e3a0eb70-7038-4872-820e-174fbf0faa9c/scratchpad/ghost/_s.png', '6', '--tier', tier, *ch], capture_output=True, text=True, timeout=500)
    print(r.stdout[-80:], r.stderr[-200:])
w, h = 300, 221
sheet = Image.new('RGB', (6 * w, len(clips) * h))
for r, c in enumerate(clips):
    for k in range(6):
        im = Image.open(P / f'review/shots/st{tier[-1]}_{c}_{k}.png').convert('RGB').resize((w, h), Image.LANCZOS)
        ImageDraw.Draw(im).text((4, 4), f'{c} {k}/5', fill=(255, 255, 0))
        sheet.paste(im, (k * w, r * h))
sheet.save(P / f'review/sheet_clips_{tier}.png')
print('STRIPS', sheet.size)
