#!/usr/bin/env python3
"""Head orientation gate: per frame, the snout direction and the head-up vector of our fish against MM9's swim.
Bind-space landmarks on each mesh (glTF: y up, head towards +z): tip = the front 8 mm of the mesh, top/bottom = the
highest/lowest 8 vertices of the slice 2-9 cm behind the tip. Snout direction = tip - (top+bottom)/2, up = top - bottom
made perpendicular to it. Both models play their own clip at the same time.
Usage: head_gate.py <our glb> <mm9 glb> [json]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model


def verts(m, pose=None, n=None):
    posed = m.skinned_positions(m.world(pose or {}))
    return np.concatenate([p for p, _ in (posed[:n] if n else posed)])


def ids(v):
    t = v[:, 2]
    tip = np.nonzero(t > t.max() - 0.008)[0]
    near = np.nonzero((t > t.max() - 0.09) & (t < t.max() - 0.02))[0]
    return tip, near[np.argsort(-v[near, 1])[:6]], near[np.argsort(v[near, 1])[:6]]


def dirs(v, tip, up, bot):
    c = (v[up].mean(0) + v[bot].mean(0)) / 2
    d = v[tip].mean(0) - c; d /= np.linalg.norm(d)
    n = v[up].mean(0) - v[bot].mean(0); n -= d * n.dot(d); n /= np.linalg.norm(n)
    return d, n


ours, mm9 = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2]))
iA, iB = ids(verts(ours, n=1)), ids(verts(mm9))
times = ours.clip_times('Walking')
rows = []
for t in np.arange(times[0], times[-1] + 1e-6, 1 / 30):
    da, na = dirs(verts(ours, ours.sample('Walking', t), n=1), *iA)
    db, nb = dirs(verts(mm9, mm9.sample('swim', t)), *iB)
    rows.append((np.degrees(np.arccos(np.clip(da @ db, -1, 1))), np.degrees(np.arccos(np.clip(na @ nb, -1, 1)))))
rows = np.array(rows)
# the bind poses differ a little (our head is deeper): report the clip's offset from the bind difference too
da0, na0 = dirs(verts(ours, n=1), *iA); db0, nb0 = dirs(verts(mm9), *iB)
rep = {'frames': len(rows), 'bind_snout_deg': round(float(np.degrees(np.arccos(np.clip(da0 @ db0, -1, 1)))), 2),
       'snout_vs_mm9_deg_max': round(float(rows[:, 0].max()), 2), 'snout_vs_mm9_deg_mean': round(float(rows[:, 0].mean()), 2),
       'up_vs_mm9_deg_max': round(float(rows[:, 1].max()), 2)}
print('HEAD', json.dumps(rep))
if len(sys.argv) > 3:
    json.dump(rep, open(sys.argv[3], 'w'), indent=1)
