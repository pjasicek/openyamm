#!/usr/bin/env python3
"""How far a GLB's LOD0 normals are from plain smooth normals (welded positions), per head (u > 0.5) / body set.
Large values mean authored normals that a smooth-normal candidate would lose. Usage: normal_dev.py <glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import build_actor_lods as g  # noqa: E402
d, b = g.read_glb(Path(sys.argv[1]))
def arr(i):
    a = d['accessors'][i]
    return np.frombuffer(g.accessor_bytes(d, b, i), dtype={5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']]).reshape(a['count'], -1)
p = d['meshes'][0]['primitives'][0]
P, N, UV = arr(p['attributes']['POSITION']), arr(p['attributes']['NORMAL']), arr(p['attributes']['TEXCOORD_0'])
T = arr(p['indices']).reshape(-1, 3)
key = np.unique(np.round(P, 6), axis=0, return_inverse=True)[1].ravel()
fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); acc = np.zeros((key.max() + 1, 3))
for k in range(3):
    np.add.at(acc, key[T[:, k]], fn)
sm = acc[key]; sm /= np.linalg.norm(sm, axis=1, keepdims=True) + 1e-12
ang = np.degrees(np.arccos(np.clip((sm * N).sum(1), -1, 1))); head = UV[:, 0] > .5
for nm, m in (('head', head), ('body', ~head)):
    print('NORMALDEV', nm, int(m.sum()), 'median', round(float(np.median(ang[m])), 1), 'p90', round(float(np.percentile(ang[m], 90)), 1))
