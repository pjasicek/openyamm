#!/usr/bin/env python3
"""Draw the UV layout of work/uv3d.npz (parts coloured) and print the atlas coverage -> review/uv_layout.png"""
import json
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
H = Path(__file__).resolve().parents[1]; d = np.load(H / 'work/uv3d.npz'); N = 1024
COL = {0: (90, 160, 90), 1: (220, 150, 40), 2: (220, 30, 30), 3: (120, 30, 40), 4: (240, 240, 210), 5: (255, 255, 255)}
im = Image.new('RGB', (N, N)); dr = ImageDraw.Draw(im)
for t, p in zip(d['uv'], d['part']):
    dr.polygon([(u * N, (1 - v) * N) for u, v in t], fill=COL[int(p)])
im.save(H / 'review/uv_layout.png')
cov = float((np.asarray(im).sum(-1) > 0).mean())
m = json.loads((H / 'work/uv_metrics.json').read_text()); m['coverage'] = round(cov, 3)
(H / 'work/uv_metrics.json').write_text(json.dumps(m, indent=1)); print('COVERAGE', round(cov, 3), m)
