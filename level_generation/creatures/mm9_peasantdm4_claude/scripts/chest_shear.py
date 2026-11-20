#!/usr/bin/env python3
"""Chest/collar shear per clip (Talk review 2026-11-02): body vertices of the upper chest and collarbones (rest, glTF
frame: front z < 0.02, |x| < XM, height H0..H1) are posed at 30 fps; each is compared with its rest position carried
rigidly by Bip01 Spine2. Reports per clip the max over frames of the p95 deviation (cm) and the worst frame.
Usage: chest_shear.py <glb> [--xm 0.16] [--h0 0.80] [--h1 0.97]"""
import argparse, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('--xm', type=float, default=0.16)
ap.add_argument('--h0', type=float, default=0.80); ap.add_argument('--h1', type=float, default=0.97)
o = ap.parse_args()
g = Glb(Path(o.glb)); m = Model(g); names = [n.get('name') for n in g.json['nodes']]
P0 = m.primitives[0]
mats = [g.json['materials'][p.get('material', 0)]['name'] for p in g.json['meshes'][0]['primitives']]
rest_w = m.world({}); sp = m.skinned_positions(rest_w)
R = sp[0][0]
sel = np.nonzero((np.abs(R[:, 0]) < o.xm) & (R[:, 1] > o.h0) & (R[:, 1] < o.h1) & (R[:, 2] < 0.02))[0]
s2 = names.index('Bip01 Spine2'); W0 = rest_w[s2]
for clip in m.clips:
    dur = max(m.clip_times(clip)); worst = (0.0, 0)
    for k, t in enumerate(np.arange(0, dur + 1e-6, 1 / 30)):
        w = m.world(m.sample(clip, float(t))); X = m.skinned_positions(w)[0][0][sel]
        T = w[s2] @ np.linalg.inv(W0)
        rig = (T[:3, :3] @ R[sel].T).T + T[:3, 3]
        d = np.percentile(np.linalg.norm(X - rig, axis=1), 95) * 100
        if d > worst[0]: worst = (d, k)
    print(f'SHEAR {clip:12s} p95 {worst[0]:5.2f} cm @ frame30 {worst[1]}  ({len(sel)} verts)')
