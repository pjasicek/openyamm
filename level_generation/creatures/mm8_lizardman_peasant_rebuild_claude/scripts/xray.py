#!/usr/bin/env python3
"""Joint X-ray: flat mesh (light) with the skeleton's joints and bones drawn on top, front and side, plus hand zooms.
Usage: xray.py <glb> <out.png> [clip@time]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit, motion_frames
a = motion_audit.Audit(sys.argv[1]); clip, t = (sys.argv[3].split('@') if len(sys.argv) > 3 else (None, 0))
posed, scale, pal, world = a.pose(clip, float(t))
cells = []
nodes = a.model.glb.json['nodes']
for yaw, joint, zoom in ((0, None, 0), (1.57, None, 0), (0, 'Bip01 L Hand', 0.18), (0, 'Bip01 R Hand', 0.18), (1.57, 'Bip01 Head', 0.25), (0, 'Bip01 L Foot', 0.2)):
    rot = motion_frames.view(yaw, 0.0); cam = posed @ rot.T
    if joint:
        jn = a.model.joints[a.joint_names.index(joint)]; c = (world[jn][:3, 3] @ rot.T)[:2]; span = zoom * a.height
    else:
        lo, hi = cam.min(0), cam.max(0); c = (lo[:2] + hi[:2]) / 2; span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
    cell = 420
    img = motion_frames.draw(cam, a.tris, None, c, span, cell)
    img = Image.blend(img, Image.new('RGB', img.size, 'white'), 0.45)
    d = ImageDraw.Draw(img); sc = (cell - 10) / span
    P = lambda p: (cell / 2 + (p[0] - c[0]) * sc, cell / 2 - (p[1] - c[1]) * sc)
    for j in a.model.joints:
        p = world[j][:3, 3] @ rot.T; par = a.model.parent[j]
        if par in a.model.joints:
            q = world[par][:3, 3] @ rot.T; d.line([P(q), P(p)], fill=(0, 90, 255), width=2)
        x, y = P(p); d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 0, 0))
    cells.append(img)
sh = Image.new('RGB', (420 * len(cells), 420), 'white')
for i, c in enumerate(cells): sh.paste(c, (i * 420, 0))
sh.save(sys.argv[2]); print(sys.argv[2])
