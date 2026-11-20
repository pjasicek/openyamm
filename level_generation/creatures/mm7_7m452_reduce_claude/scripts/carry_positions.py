#!/usr/bin/env python3
"""Carry rest-position repairs of the source mesh into the reduced GLB (review 2026-10-20: the source's despike pass
gained an unfold stage after this reduction, which moved the vertices of a folded skin triangle at the right biceps).
The moved vertices are found by comparing two exports of the source (before / after, same topology, LOD0 colour
primitive); every vertex of every colour primitive of the target that sits at a moved vertex's old position (within
0.05 mm: kept faces keep their source vertices exactly) takes the new position. Normals are left as they are.
Usage: carry_positions.py <source before.glb> <source after.glb> <target.glb> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402


def positions(doc, binary, prim):
    a = doc['accessors'][prim['attributes']['POSITION']]; v = doc['bufferViews'][a['bufferView']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0); stride = v.get('byteStride', 12)
    raw = np.frombuffer(binary, np.uint8, count=stride * (a['count'] - 1) + 12, offset=off)
    idx = (np.arange(a['count'])[:, None] * stride + np.arange(12)[None, :])
    return np.frombuffer(raw[idx].tobytes(), np.float32).reshape(-1, 3), off, stride


before, after, target, out = (Path(x) for x in sys.argv[1:5])
d0, b0 = read_glb(before); d1, b1 = read_glb(after)
p0 = positions(d0, b0, d0['meshes'][0]['primitives'][0])[0]; p1 = positions(d1, b1, d1['meshes'][0]['primitives'][0])[0]
assert p0.shape == p1.shape, 'source exports differ in topology'
mv = np.linalg.norm(p1 - p0, axis=1) > 1e-5
old, new = p0[mv], p1[mv]
print(f'CARRY {int(mv.sum())} moved source vertices (max {np.linalg.norm(new - old, axis=1).max() * 100:.1f} cm)')
doc, binary = read_glb(target); binary = bytearray(binary)
from scipy.spatial import cKDTree
tree = cKDTree(old); total = 0
for mi, m in enumerate(doc['meshes']):
    if 'Shadow' in m.get('name', ''):
        continue
    for prim in m['primitives']:
        P, off, stride = positions(doc, bytes(binary), prim)
        d, j = tree.query(P, distance_upper_bound=5e-5); hit = np.isfinite(d)
        for i in np.flatnonzero(hit):
            binary[off + i * stride: off + i * stride + 12] = new[j[i]].astype(np.float32).tobytes()
        if hit.any():
            a = doc['accessors'][prim['attributes']['POSITION']]
            P2 = positions(doc, bytes(binary), prim)[0]; a['min'] = P2.min(0).tolist(); a['max'] = P2.max(0).tolist()
        total += int(hit.sum()); print(f'CARRY mesh {m.get("name")}: {int(hit.sum())} vertices moved')
write_glb(out, doc, bytes(binary))
print(f'CARRY {total} target vertices moved -> {out.name}')
