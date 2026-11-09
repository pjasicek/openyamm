#!/usr/bin/env python3
"""Do a GLB's LOD0 normals differ from plain smooth normals? For each vertex, the angle between the file's NORMAL and
the area-weighted face normal at its welded position (vertices merged by position, 1e-6 m). Usage: glb_normals.py <node> <glb>..."""
import sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
node_name = sys.argv[1]
for path in sys.argv[2:]:
    d, b = read_glb(Path(path)); n = next(x for x in d['nodes'] if x.get('name') == node_name)
    P, N, F = [], [], []; off = 0
    for pr in d['meshes'][n['mesh']]['primitives']:
        p = np.frombuffer(accessor_bytes(d, b, pr['attributes']['POSITION']), np.float32).reshape(-1, 3)
        nn = np.frombuffer(accessor_bytes(d, b, pr['attributes']['NORMAL']), np.float32).reshape(-1, 3)
        acc = d['accessors'][pr['indices']]; dt = {5123: np.uint16, 5125: np.uint32}[acc['componentType']]
        f = np.frombuffer(accessor_bytes(d, b, pr['indices']), dt).reshape(-1, 3).astype(int) + off
        P.append(p); N.append(nn); F.append(f); off += len(p)
    P, N, F = np.concatenate(P), np.concatenate(N), np.concatenate(F)
    _, key = np.unique(np.round(P / 1e-6).astype(np.int64), axis=0, return_inverse=True)
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    acc = np.zeros((key.max() + 1, 3))
    for k in range(3):
        np.add.at(acc, key[F[:, k]], fn)
    sm = acc[key]; sm /= np.linalg.norm(sm, axis=1, keepdims=True) + 1e-12
    a = np.degrees(np.arccos(np.clip((sm * N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-12)).sum(1), -1, 1)))
    print(Path(path).name, len(P), 'verts; angle to smooth p50 %.1f p90 %.1f p99 %.1f deg' % tuple(np.percentile(a, [50, 90, 99])))
