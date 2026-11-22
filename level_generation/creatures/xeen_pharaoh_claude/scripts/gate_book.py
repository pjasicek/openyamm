#!/usr/bin/env python3
"""Gate: the book (an oriented box, the open book's hull) against the posed LOD0 body, every frame of the living clips.
Counts body vertices inside the book other than the two hands' fingers and palms (which grip its edges), and right-hand
finger vertices inside it (the page turn). gate_book.py <body.glb> <book_local.json> [out.json]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pglb import load, lod0_body
g, m, names = load(sys.argv[1])
cfg = json.load(open(sys.argv[2]))
B = np.array(cfg['book_in_B_L_Hand']); b = cfg['book']
prim, dom = lod0_body(m)
inv = {i: k for k, i in names.items()}
domn = np.array([inv[d] for d in dom])
grip = np.array([('Hand' in s or 'Finger' in s) for s in domn])
rfing = np.array([s.startswith('B_R_Finger') for s in domn])
half = np.array([b['width'] / 2, (b['page_thickness'] + b['cover_thickness']) / 2, b['height'] / 2])
ctr = np.array([0, (b['page_thickness'] + b['cover_thickness']) / 2, 0])
res = {}
for clip in ['Standing', 'Fidget', 'Bless', 'Walking', 'Hit']:
    worst_body, worst_rf, worst_t = 0, 0, 0
    for t in np.linspace(0, max(m.clip_times(clip)), 41):
        W = m.world(m.sample(clip, t))
        pts = m.skinned_positions(W)
        P = max(pts, key=lambda x: len(x[1]))[0]
        BW = W[names['B_L_Hand']] @ B
        loc = (np.c_[P, np.ones(len(P))] @ np.linalg.inv(BW).T)[:, :3] - ctr
        inside = np.all(np.abs(loc) < half, axis=1)
        nb = int((inside & ~grip).sum()); nr = int((inside & rfing).sum())
        depth = (half - np.abs(loc)).min(1)
        if (inside & rfing).any():
            res.setdefault(clip + '_finger_depth_mm', 0.0)
            res[clip + '_finger_depth_mm'] = max(res[clip + '_finger_depth_mm'], float(depth[inside & rfing].max() * 1000))
        if (inside & ~grip).any():
            res.setdefault(clip + '_body_depth_mm', 0.0)
            res[clip + '_body_depth_mm'] = max(res[clip + '_body_depth_mm'], float(depth[inside & ~grip].max() * 1000))
        if nb > worst_body: worst_body, worst_t = nb, t
        worst_rf = max(worst_rf, nr)
    res[clip] = {'body_vertices_in_book_max': worst_body, 'at': round(float(worst_t), 2), 'right_fingers_in_book_max': worst_rf}
    print(clip, res[clip], {k: round(v, 1) for k, v in res.items() if k.startswith(clip + '_')})
if len(sys.argv) > 3:
    json.dump(res, open(sys.argv[3], 'w'), indent=1)
