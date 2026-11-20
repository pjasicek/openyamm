#!/usr/bin/env python3
"""Njam: shots.sh <outdir> specs; one sheet per 8 clips (<out>_<k>.png); CLIPS=a,b limits the clips.
Frame strips of every clip from viewer shots (node viewer_shots.mjs): N times per clip, one row per clip, two views (quarter, right). Args: <tier id> <out png> [N]"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
tier, out = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 7
man = json.load(open('review/viewer/manifest.json'))
clips = man['clips']
names = list(clips.keys()) if isinstance(clips, dict) else [c['name'] for c in clips]
import os
if os.environ.get('CLIPS'): names = [n for n in names if n in os.environ['CLIPS'].split(',')]
dur = {k: (v if isinstance(v, (int, float)) else v.get('duration', v.get('seconds', 1.0))) for k, v in clips.items()} if isinstance(clips, dict) else {c['name']: c.get('duration', 1) for c in clips}
specs = []
for c in names:
    for i in range(N):
        t = dur[c] * i / (N - 1) * 0.999
        specs.append(f'{tier}_{c}_{i}:{c}:{t:.3f}:quarter:body')
        specs.append(f'{tier}_{c}_{i}s:{c}:{t:.3f}:right:body')
d = Path('review/strips'); d.mkdir(exist_ok=True)
if '--fresh' not in sys.argv:
    specs = [x for x in specs if not (d / (x.split(':')[0] + '.png')).exists()]
for k in range(0, len(specs), 40):
    subprocess.run(['scripts/shots.sh', 'review/strips'] + specs[k:k + 40], check=True, capture_output=True)
W, H = 260, 260
for g in range(0, len(names), 8):
    grp = names[g:g + 8]
    sheet = Image.new('RGB', (W * N, H * 2 * len(grp)), (30, 30, 30)); dr = ImageDraw.Draw(sheet)
    for r, c in enumerate(grp):
        for i in range(N):
            for v, sfx in enumerate(('', 's')):
                im = Image.open(d / f'{tier}_{c}_{i}{sfx}.png').convert('RGB')
                w, h = im.size; im = im.crop(((w - h) // 2 + 60, 30, (w + h) // 2 - 60, h - 30)).resize((W, H))
                sheet.paste(im, (i * W, (2 * r + v) * H))
        dr.text((4, 2 * r * H + 4), c, fill=(255, 255, 0))
    sheet.save(f'{out}_{g // 8}.png'); print('STRIP', f'{out}_{g // 8}.png', sheet.size)
