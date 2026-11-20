#!/usr/bin/env python3
"""Do the GLB's LOD0 normals equal plain smooth (angle-weighted) vertex normals over the position-welded surface?
Prints per primitive the angle between each stored normal and the smooth normal at the same position (p50/p99/max deg) and the
count over 5 deg. Usage: normal_check.py <glb> [node]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb  # noqa: E402
g = Glb(sys.argv[1]); doc = g.json; NODE = sys.argv[2] if len(sys.argv) > 2 else 'Kira'
node = next(n for n in doc['nodes'] if n.get('name') == NODE); mesh = doc['meshes'][node['mesh']]
P, N, F, off = [], [], [], 0
for p in mesh['primitives']:
    pos = np.asarray(g.accessor(p['attributes']['POSITION']), float); nor = np.asarray(g.accessor(p['attributes']['NORMAL']), float)
    idx = np.asarray(g.accessor(p["indices"])).astype(np.int64).reshape(-1, 3)
    P.append(pos); N.append(nor); F.append(idx + off); off += len(pos)
P, N, F = np.vstack(P), np.vstack(N), np.vstack(F)
key = np.round(P / 1e-6).astype(np.int64); _, wid = np.unique(key, axis=0, return_inverse=True); wid = wid.reshape(-1)
wf = wid[F]; tri = P[F]
acc = np.zeros((wid.max() + 1, 3))
fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-20
for k in range(3):
    a = tri[:, (k + 1) % 3] - tri[:, k]; b = tri[:, (k + 2) % 3] - tri[:, k]
    ang = np.arccos(np.clip((a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) + 1e-20), -1, 1))
    np.add.at(acc, wf[:, k], fn * ang[:, None])
sm = acc / (np.linalg.norm(acc, axis=1, keepdims=True) + 1e-20)
d = np.degrees(np.arccos(np.clip((sm[wid] * N).sum(1), -1, 1)))
o = 0
for p in mesh['primitives']:
    n = doc['accessors'][p['attributes']['POSITION']]['count']; x = d[o:o + n]; o += n
    print(doc['materials'][p['material']]['name'], 'verts', n, 'p50', round(float(np.median(x)), 2), 'p99', round(float(np.percentile(x, 99)), 2),
          'max', round(float(x.max()), 1), 'over5', int((x > 5).sum()))
