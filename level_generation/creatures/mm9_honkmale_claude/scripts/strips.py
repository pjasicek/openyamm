#!/usr/bin/env python3
"""Frame strips of every clip from viewer shots: one row per clip, evenly spaced times, tight crop round the figure.
Usage (repo root): strips.py <project> <token> <tier> <out png> [view=left] [frames=7] [clips, comma separated] [focus=body]"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
proj, token, tier, out = sys.argv[1:5]
view = sys.argv[5] if len(sys.argv) > 5 else 'left'
N = int(sys.argv[6]) if len(sys.argv) > 6 else 7
only = sys.argv[7].split(',') if len(sys.argv) > 7 and sys.argv[7] else None
focus = sys.argv[8] if len(sys.argv) > 8 else 'body'
man = json.loads((Path(proj) / 'review/viewer/manifest.json').read_text())
names = [(k, float(v['duration'])) for k, v in man['clips'].items()]
if only:
    names = [c for c in names if c[0] in only]
spec = []
for c, d in names:
    for i in range(N):
        t = d * i / (N - 1) if N > 1 else 0
        t = min(t, d - 0.01)
        spec.append(f'st_{c}_{i}:{c}:{t:.3f}:{view}:{focus}')
subprocess.run(['python3', 'tools/run_creature_review.py', '--project', proj, '--token', token, '--tier', tier, 'shots', *spec], check=True, stdout=subprocess.DEVNULL)
T = 240
S = Image.new('RGB', (T * N, T * len(names)), (40, 40, 40))
d = ImageDraw.Draw(S)
shots = Path(proj) / 'review/shots'
for r, (c, dur) in enumerate(names):
    ims = [Image.open(shots / f'st_{c}_{i}.png').convert('RGB') for i in range(N)]
    arr = np.asarray(ims[0], np.int32)[30:-60]
    bg = arr[5, 5]
    boxes = []
    for im in ims:
        a = np.asarray(im, np.int32)[30:-60]
        ys, xs = np.nonzero(np.abs(a - bg).sum(2) > 40)
        boxes.append((xs.min(), xs.max(), ys.min() + 30, ys.max() + 30))
    b = np.array(boxes)
    x0, x1, y0, y1 = b[:, 0].min(), b[:, 1].max(), b[:, 2].min(), b[:, 3].max()
    s = int(max(x1 - x0, y1 - y0) * 1.04)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    for i, im in enumerate(ims):
        S.paste(im.crop((cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2)).resize((T, T), Image.LANCZOS), (i * T, r * T))
    d.text((6, r * T + 4), f'{c} {dur:.2f}s  ({tier} {view})', fill=(255, 255, 120))
S.save(out)
print('STRIP', out, S.size)
