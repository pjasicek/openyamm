#!/usr/bin/env python3
"""Before | after software renders of posed GLBs (numpy skinning) at identical orthographic cameras. Usage:
compare_posed.py <before glb> <after glb> <out.png> name=clip:t:az:el:cx,cy,cz:radius ...  (cy in the posed frame: feet at 0)"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glbio import Glb
import soft_render as sr
from pose import pose_prims
ga, gb = Glb(sys.argv[1]), Glb(sys.argv[2]); rows = []
for spec in sys.argv[4:]:
    name, v = spec.split('='); p = v.split(':'); clip, t, az, el = p[0], float(p[1]), float(p[2]), float(p[3])
    c = tuple(map(float, p[4].split(','))); r = float(p[5])
    a, _ = sr.render(pose_prims(ga, clip, t), az, el, c, r, size=520); b, _ = sr.render(pose_prims(gb, clip, t), az, el, c, r, size=520)
    row = Image.fromarray(np.concatenate([a, np.zeros((520, 6, 3), np.uint8) + 255, b], 1)); d = ImageDraw.Draw(row)
    d.text((6, 6), f'{name} before', fill=(255, 255, 0)); d.text((532, 6), f'{name} after', fill=(255, 255, 0)); rows.append(row)
out = Image.new('RGB', (rows[0].width, 520 * len(rows))); [out.paste(r, (0, 520 * k)) for k, r in enumerate(rows)]; out.save(sys.argv[3]); print('COMPARE', sys.argv[3])
