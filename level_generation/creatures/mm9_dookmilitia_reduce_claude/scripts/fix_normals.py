#!/usr/bin/env python3
"""LOD0 normals of the reduced Half-Orc. The installed normals are Blender's glTF export of the creature's own mesh
(../mm9_dookmilitia_claude/scripts/export_dook.py), not a rule that can be re-run (selftest of the area-weighted rule:
median 2-6 deg, p99 38-65 deg off), so they are carried over instead:
- every candidate vertex that is a source vertex (same primitive, position and UV within 1e-5) takes the installed
  normal byte for byte (face skin, eyes, kept hands, soles, linings, small pieces, the cut edge of the reduced parts);
- every new vertex takes the installed normals interpolated (barycentric) on the source triangle of the same primitive
  that contains its UV, if that triangle lies within 1 cm in 3D (the collapse keeps each vertex on its own chart, so
  this is the surface it came from, never the far side of a thin shell); otherwise the nearest source vertex of the
  primitive whose normal faces the same way as the candidate's own area-weighted normal.
Primitives in KEEP_PRIMS (default DookWeapon_A, the sword kept exactly) are restored from the installed file byte for byte.
Usage: fix_normals.py <source.glb> <in.glb> <out.glb> [mesh node]"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402


def arr(doc, binary, idx):
    a = doc['accessors'][idx]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    ct = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
    v = np.frombuffer(accessor_bytes(doc, binary, idx), ct)
    return v.reshape(-1, n) if n > 1 else v


def prims(doc, binary, node):
    out = {}
    for p in doc['meshes'][node['mesh']]['primitives']:
        a = p['attributes']
        out[doc['materials'][p['material']]['name']] = dict(prim=p, P=arr(doc, binary, a['POSITION']).astype(float),
            UV=arr(doc, binary, a['TEXCOORD_0']).astype(float), N=arr(doc, binary, a['NORMAL']).astype(float),
            T=arr(doc, binary, p['indices']).astype(int).reshape(-1, 3))
    return out


def vnormals(P, T):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); N = np.zeros_like(P)
    for c in range(3):
        np.add.at(N, T[:, c], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


src, inp, out = (Path(a) for a in sys.argv[1:4]); NODE = sys.argv[4] if len(sys.argv) > 4 else 'DookMilitia'
KEEP = [n for n in os.environ.get('KEEP_PRIMS', 'DookWeapon_A').split(',') if n]
sdoc, sbin = read_glb(src); doc, binary = read_glb(inp); binary = bytearray(binary)
S = prims(sdoc, sbin, next(n for n in sdoc['nodes'] if n.get('name') == NODE))
C = prims(doc, binary, next(n for n in doc['nodes'] if n.get('name') == NODE))
for name, c in C.items():
    if name in KEEP:
        continue
    s = S[name]; tree = cKDTree(s['P']); own = vnormals(c['P'], c['T']); N = np.zeros_like(c['P'])
    suv = s['UV'][s['T']]; utree = cKDTree(suv.mean(1))
    copied = interp = fall = 0
    for i, h in enumerate(tree.query_ball_point(c['P'], 1e-5)):
        h = [j for j in h if np.abs(s['UV'][j] - c['UV'][i]).max() < 1e-5]
        if h:
            j = max(h, key=lambda j: float(s['N'][j] @ own[i])); N[i] = s['N'][j]; copied += 1
            continue
        done = False
        for t in utree.query(c['UV'][i], 16)[1]:
            a, b, cc = suv[t]
            try:
                l1, l2 = np.linalg.solve(np.array([b - a, cc - a]).T, c['UV'][i] - a)
            except np.linalg.LinAlgError:
                continue
            bary = np.array([1 - l1 - l2, l1, l2])
            if bary.min() < -1e-4:
                continue
            bary = np.clip(bary, 0, 1); bary /= bary.sum()
            if np.linalg.norm(bary @ s['P'][s['T'][t]] - c['P'][i]) > .01:
                continue
            n = bary @ s['N'][s['T'][t]]; N[i] = n / max(np.linalg.norm(n), 1e-12); interp += 1; done = True
            break
        if not done:
            _, nn = tree.query(c['P'][i], 12)
            ok = [j for j in nn if s['N'][j] @ own[i] > .3]
            N[i] = s['N'][ok[0] if ok else nn[0]]; fall += 1
    acc = doc['accessors'][c['prim']['attributes']['NORMAL']]
    c['prim']['attributes']['NORMAL'] = append_accessor(doc, binary, acc, N.astype('<f4').tobytes())
    print('NORMALS', name, 'vertices', len(N), 'installed', copied, 'interpolated', interp, 'fallback', fall)
for name in KEEP:
    sp, cp = S[name]['prim'], C[name]['prim']
    cp['attributes'] = {k: append_accessor(doc, binary, sdoc['accessors'][i], accessor_bytes(sdoc, sbin, i)) for k, i in sp['attributes'].items()}
    cp['indices'] = append_accessor(doc, binary, sdoc['accessors'][sp['indices']], accessor_bytes(sdoc, sbin, sp['indices']))
    print('KEPT PRIMITIVE', name, 'installed bytes', len(S[name]['T']), 'triangles')
write_glb(out, doc, bytes(binary))
