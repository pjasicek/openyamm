#!/usr/bin/env python3
"""Cloak poke-through of the MM6 Thief per clip, on the GLB (the idea of ../../mm6_thf_claude/scripts/cloak_poke.py):
leg and boot vertices (dominated by thigh, calf, foot or toe bones) behind the hip joints whose ray straight back
(-Z, the body's back; the clips are in place) meets no cloak triangle (dominated by a Cloak_* bone), while they are above
the cloak's lowest point at that moment. Per clip at 48 Hz: share of samples with any poking vertex, mean and max count.

    cloak_poke_probe.py <glb> <clip>[,<clip>...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gaitlib  # noqa: E402
from gaitlib import glb_pose  # noqa: E402
import os  # noqa: E402

PREFIX = os.environ.get('CLOAK_PREFIX', 'Cloak_')     # (h03) Robe_ for the Sorcerer

LEG = ('Thigh', 'Calf', 'Foot', 'Toe', 'UpLeg', 'Leg', 'ToeBase')


def ray_hits(origins, tri):
    """Per origin: does the ray toward -Z hit any triangle (Moller-Trumbore, vectorised over triangles)."""
    d = np.array([0.0, 0.0, -1.0])
    v0, e1, e2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    p = np.cross(d, e2)
    det = np.einsum('ij,ij->i', e1, p)
    ok = np.abs(det) > 1e-12
    v0, e1, e2, p, det = v0[ok], e1[ok], e2[ok], p[ok], det[ok]
    inv = 1.0 / det
    hit = np.zeros(len(origins), dtype=bool)
    for i, o in enumerate(origins):
        s = o - v0
        u = np.einsum('ij,ij->i', s, p) * inv
        q = np.cross(s, e1)
        v = (q @ d) * inv
        t = np.einsum('ij,ij->i', e2, q) * inv
        hit[i] = bool(np.any((u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)))
    return hit


def main():
    glb = gaitlib.open_glb(sys.argv[1])          # (h03) Meshy names read as B_*: B_* rigs work too
    model = glb_pose.Model(glb)
    names = [n.get('name', '') for n in glb.json['nodes']]
    idx = {n: i for i, n in enumerate(names)}
    groups = []
    for prim in model.primitives:
        dom = [names[model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])),
                                                              prim['weights'].argmax(axis=1)]]
        leg = np.array([any(dom_name.endswith(t) for t in LEG) for dom_name in dom])
        cloak = np.array([dom_name.startswith(PREFIX) for dom_name in dom])
        tri_cloak = cloak[prim['triangles']].all(axis=1)
        groups.append((np.where(leg)[0], prim['triangles'][tri_cloak]))
    for clip in sys.argv[2].split(','):
        T = model.clip_times(clip)[-1]
        n = max(1, int(round(T * 48)))
        counts = []
        for k in range(n):
            W = model.world(model.sample(clip, k / n * T))
            hip_z = 0.5 * (W[idx['B_L_Thigh'], 2, 3] + W[idx['B_R_Thigh'], 2, 3])
            posed = model.skinned_positions(W)
            tris = np.concatenate([pts[t] for (pts, _), (_, t) in zip(posed, groups) if len(t)])
            hem = tris[:, :, 1].min()
            legs = np.concatenate([pts[ids] for (pts, _), (ids, _) in zip(posed, groups) if len(ids)])
            behind = legs[(legs[:, 2] < hip_z - 0.02) & (legs[:, 1] > hem + 0.01)]
            counts.append(int((~ray_hits(behind, tris)).sum()) if len(behind) else 0)
        counts = np.array(counts)
        print(f'{clip:9s} poke share {np.mean(counts > 0):.0%}  mean {counts.mean():.1f}  max {counts.max()} vertices')


if __name__ == '__main__':
    main()
