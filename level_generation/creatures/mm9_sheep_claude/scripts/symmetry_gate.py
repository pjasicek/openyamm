#!/usr/bin/env python3
"""Symmetry and hoof splay of a GLB against MM9's mesh: bind pose and Standing (t = 0, 0.6).
Mirror asymmetry = for each LOD0 vertex, distance of its x-mirror to the nearest vertex (mean / p95 / max, model units).
Bones: x of the midline joints and world yaw/roll of the head. Hoof: toe direction = (front tip - hoof centroid) of the
vertices dominated by a foot joint, flattened to the ground; splay = its yaw from body forward (+ = outward).
Usage: symmetry_gate.py <glb> [<glb> ...]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
FEET = {'FL': 'Xffoot01', 'FR': 'Xffoot', 'HL': 'Xbfoot01', 'HR': 'Xbfoot'}
MID = ['XCENTER', 'Xback', 'Xneck', 'Xheadpiv', 'Xhead', 'Xjawpiv', 'Xtail']


def report(path):
    m = Model(Glb(path))
    names = [n.get('name') for n in m.glb.json['nodes']]
    jn = [m.glb.json['nodes'][j].get('name') for j in m.joints]
    clip = 'Standing' if 'Standing' in m.clips else 'stand'
    poses = [('bind', {})] + [(f'{clip}@{t}', m.sample(clip, t)) for t in (0.0, 0.6)]
    for tag, local in poses:
        W = m.world(local)
        posed = m.skinned_positions(W)
        P = np.concatenate([p for p, _ in posed])
        P = np.unique(P.round(5), axis=0)
        d = cKDTree(P).query(P * [-1, 1, 1])[0]
        # plane of the root: spine joints
        mid = {b: W[names.index(b)][:3, 3].round(3).tolist() for b in MID if b in names}
        print(f'{tag:14s} mirror mean {d.mean():.4f} p95 {np.percentile(d, 95):.4f} max {d.max():.4f} | x: ' +
              ' '.join(f'{b} {v[0]:+.3f}' for b, v in mid.items()))
        out = []
        for k, b in FEET.items():
            pts = []
            for (p, _), pr in zip(posed, m.primitives):
                if not pr['skinned']:
                    continue
                dom = pr['joints'][np.arange(len(p)), pr['weights'].argmax(1)]
                pts.append(p[dom == jn.index(b)])
            q = np.concatenate(pts)
            # glTF: forward +Z, right-hand: x left of sheep; flatten to the XZ plane
            c = q.mean(0)
            axis = q[:, [0, 2]] - c[[0, 2]]
            u, s, vt = np.linalg.svd(axis, full_matrices=False)
            dirn = vt[0] * np.sign(vt[0][1] or 1)
            yaw = np.degrees(np.arctan2(dirn[0], dirn[1]))     # + = toward +x
            out.append(f'{k} {yaw:+.1f} (x {c[0]:+.3f}, aspect {s[0] / max(s[1], 1e-6):.2f})')
        print('   hoof long-axis yaw from forward: ' + '  '.join(out))


for p in sys.argv[1:]:
    print('==', p.split('/')[-1])
    report(p)
