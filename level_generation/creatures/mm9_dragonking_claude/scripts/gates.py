#!/usr/bin/env python3
"""Numeric deformation gates on the delivered GLB, every clip at 60 Hz (LOD0 primitives):
  stretch  - edge length ratio posed / bind (p1, p99, min, max) per material: tearing or collapse
  floor    - lowest point per clip (also in floor_audit.py)
  seam     - loop clips: largest vertex jump between the last and first frame (model units)
Usage: gates.py <glb> [report.json]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

m = Model(Glb(sys.argv[1]))
doc = m.glb.json
clips = [a['name'] for a in doc['animations']]
LOOPS = {'Standing', 'Walking', 'Running'}  # (from mm9_dfly_claude; Dragon King: 30 Hz, LOD0)


def tri_normals(p, t):
    n = np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


rest = m.skinned_positions(m.world({}))
edges, bind_len, bind_n = [], [], []
for pos, tris in rest:
    t = np.asarray(tris).reshape(-1, 3)
    e = np.unique(np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1), axis=0)
    edges.append(e)
    bind_len.append(np.linalg.norm(pos[e[:, 0]] - pos[e[:, 1]], axis=1))
    bind_n.append(tri_normals(pos, t))
report = {}
for clip in clips:
    times = m.clip_times(clip)
    ts = np.arange(times[0], times[-1] + 1e-6, 1 / 30)
    rmin, rmax, p1, p99, low = 9, 0, [], [], 1e9
    first = last = None
    for ti, tt in enumerate(ts):
        posed = m.skinned_positions(m.world(m.sample(clip, tt)))
        for k, (pos, tris) in enumerate(posed):
            e = edges[k]
            keep = bind_len[k] > 1e-4
            r = np.linalg.norm(pos[e[:, 0]] - pos[e[:, 1]], axis=1)[keep] / bind_len[k][keep]
            rmin, rmax = min(rmin, r.min()), max(rmax, r.max())
            p1.append(np.percentile(r, 1))
            p99.append(np.percentile(r, 99))
            low = min(low, pos[:, 1].min())
        allpos = np.concatenate([p for p, _ in posed])
        if ti == 0:
            first = allpos
        last = allpos
    rep = {'edge_ratio_min': round(float(rmin), 3), 'edge_ratio_max': round(float(rmax), 3),
           'edge_ratio_p1': round(float(min(p1)), 3), 'edge_ratio_p99': round(float(max(p99)), 3),
           'lowest': round(float(low), 4)}
    if clip in LOOPS:
        rep['loop_seam_max_jump'] = round(float(np.linalg.norm(last - first, axis=1).max()), 4)
    report[clip] = rep
    print(clip, rep)
if len(sys.argv) > 2:
    json.dump(report, open(sys.argv[2], 'w'), indent=1)
