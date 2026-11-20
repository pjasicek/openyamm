#!/usr/bin/env python3
"""How far the GLB's own LOD0 normals are from plain smooth normals (area-weighted over position-welded vertices), per
region: head atlas (u > 0.505) vs body. Usage: normal_audit.py <glb> <node>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
d, b = read_glb(Path(sys.argv[1])); node = sys.argv[2]
p = d['meshes'][next(n for n in d['nodes'] if n.get('name') == node)['mesh']]['primitives'][0]
g = lambda a, k: np.frombuffer(accessor_bytes(d, b, p['attributes'][a]), np.float32).reshape(-1, k)
P, N, U = g('POSITION', 3), g('NORMAL', 3), g('TEXCOORD_0', 2)
ia = d['accessors'][p['indices']]
T = np.frombuffer(accessor_bytes(d, b, p['indices']), np.uint32 if ia['componentType'] == 5125 else np.uint16).reshape(-1, 3)
_, w = np.unique(P.round(6), axis=0, return_inverse=True); w = w.ravel()
fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
acc = np.zeros((w.max() + 1, 3))
for k in range(3):
    np.add.at(acc, w[T[:, k]], fn)
S = acc[w]; S /= np.linalg.norm(S, axis=1, keepdims=True) + 1e-12
ang = np.degrees(np.arccos(np.clip((S * N).sum(1) / (np.linalg.norm(N, axis=1) + 1e-12), -1, 1)))
head = U[:, 0] > .505
for name, m in (('head', head), ('body', ~head)):
    print(f'{name:5s} verts {m.sum():6d} median {np.median(ang[m]):5.1f} deg  p90 {np.percentile(ang[m], 90):5.1f}')
