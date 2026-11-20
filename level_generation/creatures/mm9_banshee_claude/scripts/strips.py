#!/usr/bin/env python3
"""Frame strips of every clip from the viewer: six frames each, one sheet. Args: tier id [azimuth, default 35]. Run from the repo root. Writes review/sheet_clips_<tier>_az<az>.png."""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
P = Path('level_generation/creatures/mm9_banshee_claude')
tier = sys.argv[1]; az = sys.argv[2] if len(sys.argv) > 2 else '35'
m = json.load(open(P / 'review/viewer/manifest.json'))
clips = list(m['clips'])
tag = f'st{tier[-1]}{az}'.replace('-', 'm')
specs = []
for c in clips:
    d = m['clips'][c]['duration']
    for k in range(6):
        t = round(min(d - 0.001, d * k / 5), 3)
        ty = 0.75 if c in ('Death', 'Dead') else 1.05
        specs.append(f'{tag}_{c}_{k}:{c}:{t}:{az}:6:3.6:{ty}')
chunks = [specs[i:i + 24] for i in range(0, len(specs), 24)]
for ch in chunks:
    r = subprocess.run(['python3', str(P / 'scripts/vshot.py'), str(P / f'review/shots/_{tag}.png'), '6', '--tier', tier, *ch], capture_output=True, text=True, timeout=590)
    print(r.stdout[-60:], r.stderr[-200:], flush=True)
w, h = 300, 221
sheet = Image.new('RGB', (6 * w, len(clips) * h))
for r, c in enumerate(clips):
    for k in range(6):
        im = Image.open(P / f'review/shots/{tag}_{c}_{k}.png').convert('RGB').resize((w, h), Image.LANCZOS)
        ImageDraw.Draw(im).text((4, 4), f'{c} {k}/5 {tier} az{az}', fill=(255, 255, 0))
        sheet.paste(im, (k * w, r * h))
sheet.save(P / f'review/sheet_clips_{tier}_az{az}.png')
print('STRIPS', tier, az, sheet.size)
