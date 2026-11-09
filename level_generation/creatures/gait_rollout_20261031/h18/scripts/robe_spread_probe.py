"""Robe/skirt hem spread (h18): robe chain end points' horizontal distance from the pelvis axis per clip (p50/p95/max, m) and their
fore-aft reach (front/back max).

    robe_spread_probe.py <glb> <clip,...> <chain prefix>
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import gaitlib
from gaitlib import glb_pose
g = gaitlib.open_glb(sys.argv[1]); M = glb_pose.Model(g)
I = {n['name']: i for i, n in enumerate(g.json['nodes'])}
ends = [i for n, i in I.items() if n.startswith(sys.argv[3]) and n.endswith('_3')]
for clip in sys.argv[2].split(','):
    T = M.clip_times(clip)[-1]; d = []; fz = []
    for t in np.linspace(0, T, 60, endpoint=False):
        W = M.world(M.sample(clip, float(t)))
        p = W[I['B_Pelvis'], :3, 3]
        q = W[ends][:, :3, 3] + W[ends][:, :3, 1] * 0.1   # a little down the last bone
        r = q[:, [0, 2]] - p[[0, 2]]
        d.extend(np.linalg.norm(r, axis=1)); fz.extend(r[:, 1])
    d = np.array(d); fz = np.array(fz)
    print(f'{clip:8s} hem radius p50 {np.median(d):.3f} p95 {np.percentile(d,95):.3f} max {d.max():.3f}  front {fz.max():.3f} back {fz.min():.3f}')
