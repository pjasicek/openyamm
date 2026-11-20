#!/usr/bin/env python3
"""Faces whose stored vertex normals point against their geometric normal (render black in clay and dark in game):
per face of the mesh node's LOD0, the smallest dot of a corner normal with the face normal.
Usage: normal_flip.py <glb> <mesh node>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
d, b = read_glb(Path(sys.argv[1])); n = next(x for x in d['nodes'] if x.get('name') == sys.argv[2])
for p in d['meshes'][n['mesh']]['primitives']:
    P = np.frombuffer(accessor_bytes(d, b, p['attributes']['POSITION']), np.float32).reshape(-1, 3)
    N = np.frombuffer(accessor_bytes(d, b, p['attributes']['NORMAL']), np.float32).reshape(-1, 3)
    dt = {5123: np.uint16, 5125: np.uint32}[d['accessors'][p['indices']]['componentType']]
    F = np.frombuffer(accessor_bytes(d, b, p['indices']), dt).astype(np.int64).reshape(-1, 3)
    t = P[F]; fn = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-20
    m = (N[F] * fn[:, None]).sum(-1).min(1)
    bad = np.flatnonzero(m < 0)
    print(Path(sys.argv[1]).name, 'faces', len(F), 'corner normal against face:', len(bad), '(< -0.5:', int((m < -0.5).sum()), ')')
    for k in bad[np.argsort(m[bad])][:6]:
        c = t[k].mean(0); print('   at blender', np.round([c[0], -c[2], c[1]], 3), 'dot', round(float(m[k]), 2))
