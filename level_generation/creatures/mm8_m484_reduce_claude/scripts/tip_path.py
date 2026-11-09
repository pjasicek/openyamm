#!/usr/bin/env python3
"""Axe-head path of the Attack clip, old against new (glTF model space, sampled at 60 Hz): top view (x his left /
z forward), front view (x / y up) and head speed against time, with the impact marked
-> review/attack/tip_path.png. Dots mark the impact. Usage: tip_path.py <old.glb> <new.glb> [old impact s] [new impact s] [old label] [new label]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gltf_pose import Pose, qrot  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
IMP = {'old': float(sys.argv[3]) if len(sys.argv) > 3 else 0.8166667, 'new': float(sys.argv[4]) if len(sys.argv) > 4 else 0.8166667}
NAME = {'old': sys.argv[5] if len(sys.argv) > 5 else 'old', 'new': sys.argv[6] if len(sys.argv) > 6 else 'new'}
paths = {}
for label, glb in (('old', sys.argv[1]), ('new', sys.argv[2])):
    p = Pose(glb); c = p.clip('Attack'); i = p.idx
    end = max(float(v[0][-1]) for ch in c.values() for v in ch.values()); t = np.arange(0, end + 1e-6, 1 / 60); h = []
    for x in t:
        P, Q = p.world(p.local(c, x)); h.append(P[i['Axe']] + qrot(Q[i['Axe']], np.array([0, 1.05, 0])))
    h = np.array(h); paths[label] = (t, h, np.r_[0, np.linalg.norm(np.diff(h, axis=0), axis=1) * 60])
S = 420; img = Image.new('RGB', (3 * S + 40, S + 60), (250, 250, 250)); d = ImageDraw.Draw(img)
COL = {'old': (74, 127, 193), 'new': (224, 123, 40)}
# panels: (title, x range, y range, mapping of (t, head, speed) to points)
panels = [('top view from above: his right <- -> his left, up = forward', (-1.4, 1.4), (-1.3, 1.8), lambda t, h, v: np.c_[h[:, 0], h[:, 2]]),
          ('front view as the viewer sees him (dashed = centre line)', (-1.4, 1.4), (0, 2.6), lambda t, h, v: np.c_[h[:, 0], h[:, 1]]),
          ('axe-head speed m/s over time (dots = impact)', (0, 1.6667), (0, 40), lambda t, h, v: np.c_[t, v])]
for k, (title, xr, yr, fn) in enumerate(panels):
    ox = 20 + k * (S + 0); d.rectangle([ox, 40, ox + S - 20, 40 + S - 20], outline=(180, 180, 180))
    d.text((ox, 22), title, fill=(30, 30, 30))
    tr = lambda q: (ox + (q[0] - xr[0]) / (xr[1] - xr[0]) * (S - 20), 40 + (1 - (q[1] - yr[0]) / (yr[1] - yr[0])) * (S - 20))
    if k == 0:
        a, b = tr((-.2, .2)), tr((.2, -.2)); d.ellipse([a[0], a[1], b[0], b[1]], outline=(160, 160, 160))
    if k < 2:
        a, b = tr((0, yr[0])), tr((0, yr[1])); d.line([a, b], fill=(150, 150, 150), width=1)
    for label in ('old', 'new'):
        t, h, v = paths[label]; pts = [tr(q) for q in fn(t, h, v)]
        d.line(pts, fill=COL[label], width=3); m = int(np.argmin(abs(t - IMP[label]))); x, y = pts[m]
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=COL[label])
    d.text((ox + 8, 46), NAME['old'], fill=COL['old']); d.text((ox + 8, 60), NAME['new'], fill=COL['new'])
out = HERE / 'review/attack/tip_path.png'; img.save(out)
for label in paths:
    t, h, v = paths[label]; k = np.argmin(abs(t - IMP[label]))
    print(label, 'impact head', h[k].round(3), 'peak speed', round(float(v.max()), 1), 'm/s at', round(float(t[v.argmax()]), 3))
