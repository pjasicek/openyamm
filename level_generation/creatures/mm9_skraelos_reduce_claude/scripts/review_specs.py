#!/usr/bin/env python3
"""Viewer shot specs for the reduction review, from the installed GLB in Standing 0.5 (world = the viewer's frame, facing +z).
face: f0 front close-up, f1 3/4, f2 true profile, f3 low 3/4, f4 party (target FHP Head + (0, 0.035, 0.07), as
../mm9_skraelos_claude/scripts/face_specs.py). close: c0/c1 right hand + staff grip front / 3/4, c2/c3/c4 left hand + held skull
front / 3/4 / low, c5 necklace + pendant, c6 hood from behind above, c7 hem front low, c8 staff head, c9 tabard hem 3/4,
c10 cuffs from below. Usage: review_specs.py <glb> face|close"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, what = sys.argv[1:3]
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]
w = m.world(m.sample('Standing', 0.5)); J = lambda j: w[names.index(j)][:3, 3]
g = np.load(Path(__file__).resolve().parents[1] / 'work' / 'glb_parts.npz'); part = g['part']
posed = [p for p, _ in m.skinned_positions(w)]
TH = np.asarray(m.primitives[1]['triangles']).reshape(-1, 3); nA = len(np.asarray(m.primitives[0]['triangles']).reshape(-1, 3))
sv = posed[1][np.unique(TH[part[nA:] == 7])]; staff_top = sv[sv[:, 1].argmax()]


def spec(name, t, d, dist):
    d = np.array(d, float); d /= np.linalg.norm(d); c = np.asarray(t) + d * dist
    return f'{name}:Standing:0.5:front:body:' + ','.join(f'{x:.3f}' for x in c) + ':' + ','.join(f'{x:.3f}' for x in t)


out = []
if what == 'face':
    t = J('FHP Head') + [0, 0.035, 0.07]
    for k, (d, dist) in enumerate((((0, 0.03, 1), 0.42), ((0.75, 0.05, 0.7), 0.42), ((1, 0.02, 0.05), 0.42), ((0.35, -0.7, 0.75), 0.42), ((0.05, 0.12, 1), 2.6))):
        out.append(spec(f'f{k}', t, d, dist))
else:
    rh = J('FHP R Hand') + [0, -0.05, 0.03]; lh = J('FHP L Hand') + [0, -0.10, 0.02]
    out += [spec('c0', rh, (0, 0.15, 1), 0.35), spec('c1', rh, (-0.8, 0.2, 0.7), 0.35),
            spec('c2', lh, (0, 0.15, 1), 0.35), spec('c3', lh, (0.8, 0.2, 0.7), 0.35), spec('c4', lh, (0.3, -0.6, 0.8), 0.35),
            spec('c5', J('FHP Spine2') + [0, 0.08, 0.17], (0.15, 0.1, 1), 0.55), spec('c6', J('FHP Head'), (0.2, 0.5, -1), 0.8),
            spec('c7', [0, 0.25, 0.1], (0.3, 0.15, 1), 1.0), spec('c8', staff_top - [0, 0.06, 0], (-0.4, 0.2, 1), 0.4),
            spec('c9', [0, 0.55, 0.15], (0.7, 0.05, 0.7), 0.7), spec('c10', (J('FHP R Hand') + J('FHP L Hand')) / 2 + [0, -0.05, 0.05], (0, -0.8, 0.6), 0.75)]
print(' '.join(out))
