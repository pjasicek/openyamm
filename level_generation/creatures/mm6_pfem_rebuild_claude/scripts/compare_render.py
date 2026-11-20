#!/usr/bin/env python3
"""Before | after software renders at identical orthographic cameras (follow-up 4 diagnostics). Usage:
compare_render.py <before glb> <after glb> <out.png> name=az:el:cx,cy,cz:radius ..."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glbio import Glb
import soft_render as sr
pa, pb = sr.load(Glb(sys.argv[1])), sr.load(Glb(sys.argv[2])); rows = []
for spec in sys.argv[4:]:
    name, v = spec.split('='); p = v.split(':'); az, el = float(p[0]), float(p[1]); c = tuple(map(float, p[2].split(','))); r = float(p[3])
    a, _ = sr.render(pa, az, el, c, r, size=560); b, _ = sr.render(pb, az, el, c, r, size=560)
    row = Image.fromarray(np.concatenate([a, np.zeros((560, 6, 3), np.uint8) + 255, b], 1)); d = ImageDraw.Draw(row)
    d.text((6, 6), f'{name} before', fill=(255, 255, 0)); d.text((572, 6), f'{name} after', fill=(255, 255, 0)); rows.append(row)
out = Image.new('RGB', (rows[0].width, 560 * len(rows))); [out.paste(r, (0, 560 * k)) for k, r in enumerate(rows)]; out.save(sys.argv[3]); print('COMPARE', sys.argv[3])
