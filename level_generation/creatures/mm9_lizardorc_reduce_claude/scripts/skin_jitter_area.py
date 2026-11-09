#!/usr/bin/env python3
"""Population-independent check of jitter_gate.py's shoulder-skin term: the same second difference (mm/frame^2 at 30 fps)
of the vertices dominated by a side's Clavicle/UpperArm joints (pauldrons on the half joints included), but its 95th
percentile weighted by each vertex's surface area, so a decimated mesh (fewer, larger faces on the flat pauldron domes)
is not judged on a different vertex population. Excess = clip GLB minus the same mesh with the untouched reference clips
(ref_swap.py). Usage: skin_jitter_area.py <glb> <ref glb> <clip,...>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model


def curve(path, clip, tok):
    m = Model(Glb(Path(path))); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
    P = [p for p in m.primitives if p['node'] == m.primitives[0]['node'] and p['skinned']]
    dom = np.concatenate([np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]) for p in P])
    off = np.cumsum([0] + [len(p['positions']) for p in P]); T = np.vstack([p['triangles'] + o for p, o in zip(P, off)])
    X0 = np.vstack([p['positions'] for p in P]); a = np.linalg.norm(np.cross(X0[T[:, 1]] - X0[T[:, 0]], X0[T[:, 2]] - X0[T[:, 0]]), axis=1) / 6
    area = np.zeros(len(X0))
    for k in range(3):
        np.add.at(area, T[:, k], a)
    sv = np.where([tok in d and (d.endswith('Clavicle') or d.endswith('UpperArm')) for d in dom])[0]
    ts = np.arange(0, max(m.clip_times(clip)) + 1e-6, 1 / 30)
    Y = np.array([np.vstack([sp[0] for k, sp in enumerate(m.skinned_positions(m.world(m.sample(clip, float(t))))) if k < len(P)])[sv] for t in ts])
    acc = np.linalg.norm(Y[2:] - 2 * Y[1:-1] + Y[:-2], axis=2) * 1000; w = area[sv]
    out = []
    for row in acc:
        o = np.argsort(row); c = np.cumsum(w[o]) / w.sum(); out.append(row[o][np.searchsorted(c, .95)])
    return np.array(out)


glb, ref, clips = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
for clip in clips:
    for side, tok in (('L', ' L '), ('R', ' R ')):
        a, b = curve(glb, clip, tok), curve(ref, clip, tok)
        print(f'{clip:13s} {side} area-weighted p95 max {a.max():7.2f} (ref {b.max():7.2f}) excess {(a - b).max():5.2f} mm/f2', flush=True)
