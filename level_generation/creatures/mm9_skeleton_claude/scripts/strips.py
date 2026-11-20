#!/usr/bin/env python3
"""Frame strips of every clip from viewer shots: 8 frames per clip, side and 3/4. Args: <tier> <out dir> [clips]"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
H = Path(__file__).resolve().parents[1]
tier, out = sys.argv[1], H / sys.argv[2]; out.mkdir(parents=True, exist_ok=True)
man = json.load(open(H / 'review/viewer/manifest.json'))
clips = sys.argv[3].split(',') if len(sys.argv) > 3 else list(man['clips'])
url = subprocess.check_output(['python3', str(H / 'scripts/viewer_url.py'), tier], text=True).strip()
specs = []; rows = {}
for c in clips:
    d = man['clips'][c]['duration']; ts = [round(d * i / 7, 3) for i in range(8)] if c != 'Dead' else [0.5]
    rows[c] = []
    for v, foc in (('right', 'body'), ('quarter', 'body')):
        for k, t in enumerate(ts):
            n = f'{c}_{v}_{k}'; specs.append(f'{n}:{c}:{t}:{v}:{foc}'); rows[c].append((n, t))
print(subprocess.run(['node', str(H.parent / 'mm8_m424_claude/scripts/viewer_shots.mjs'), url, str(out), *specs], capture_output=True, text=True).stdout[-60:])
for c, r in rows.items():
    n8 = len(r) // 2; W, Hh = 300, 290
    s = Image.new('RGB', (W * n8, Hh * 2), (30, 30, 30)); d = ImageDraw.Draw(s)
    for i, (n, t) in enumerate(r):
        im = Image.open(out / f'{n}.png').convert('RGB'); w0, h0 = im.size
        im = im.crop((int(w0 * .2), int(h0 * .02), int(w0 * .8), int(h0 * .93))); im.thumbnail((W, Hh))
        s.paste(im, ((i % n8) * W, (i // n8) * Hh)); d.text(((i % n8) * W + 4, (i // n8) * Hh + 4), f'{c} {t}s', fill=(255, 255, 0))
    s.save(out / f'strip_{c}.png')
print('STRIPS', len(rows))
