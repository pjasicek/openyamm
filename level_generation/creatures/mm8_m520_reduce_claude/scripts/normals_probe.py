#!/usr/bin/env python3
"""Does a GLB carry sculpt normals? Angle between the file's NORMAL and area-weighted smooth normals of the same
triangles (positions merged), LOD0 of node REA_NODE. Usage: normals_probe.py <glb> [node]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
doc, b = read_glb(Path(sys.argv[1])); name = sys.argv[2] if len(sys.argv) > 2 else 'Cyclops'
node = next(n for n in doc['nodes'] if n.get('name') == name); pr = doc['meshes'][node['mesh']]['primitives'][0]
P = np.frombuffer(accessor_bytes(doc, b, pr['attributes']['POSITION']), np.float32).reshape(-1, 3)
N = np.frombuffer(accessor_bytes(doc, b, pr['attributes']['NORMAL']), np.float32).reshape(-1, 3)
ct = {5125: np.uint32, 5123: np.uint16}[doc['accessors'][pr['indices']]['componentType']]
I = np.frombuffer(accessor_bytes(doc, b, pr['indices']), ct).reshape(-1, 3).astype(int)
inv = np.unique(np.round(P, 6), axis=0, return_inverse=True)[1].ravel()
fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]); acc = np.zeros((inv.max() + 1, 3))
for k in range(3):
    np.add.at(acc, inv[I[:, k]], fn)
S = acc[inv]; S /= np.linalg.norm(S, axis=1, keepdims=True) + 1e-12
ang = np.degrees(np.arccos(np.clip((S * N).sum(1), -1, 1)))
print(sys.argv[1], 'verts', len(P), 'file vs smooth normal angle: median %.1f p90 %.1f p99 %.1f deg' % tuple(np.percentile(ang, [50, 90, 99])))
