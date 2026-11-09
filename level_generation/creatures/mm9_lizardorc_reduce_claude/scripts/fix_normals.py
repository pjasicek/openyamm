#!/usr/bin/env python3
"""LOD0 normals of the reduced Lizard-Orc the way its own build made them (../mm9_lizardorc_claude/scripts/build_glb.py),
after mm9_ebora_reduce_claude/scripts/fix_normals.py: every candidate vertex that is a source vertex (same material,
position and UV within 1e-5) takes the installed normal byte for byte (kept hands, soles, neck band, small pieces,
grip and the cut edge of the reduced parts); every new vertex takes build_glb's rule on the reduced mesh: area-weighted
face normals summed over every LOD0 primitive at the same rounded position (5 decimals). Blender's export normals are
discarded. Primitives in KEEP_PRIMS (default LizHead_A: face, helm, teeth, tongue, neck strip, the chin-crease and
neck-ring normals) are restored from the installed file byte for byte (attributes and indices).
Usage: fix_normals.py <source.glb> <in.glb> <out.glb> [mesh node]   (also: --selftest <source.glb>)"""
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


def rule_all(D):
    names = list(D); off = np.cumsum([0] + [len(D[n]['P']) for n in names])
    P = np.vstack([D[n]['P'] for n in names]); T = np.vstack([D[n]['T'] + o for n, o in zip(names, off)])
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    key = np.round(P, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    Ns = np.zeros((inv.max() + 1, 3))
    for c in range(3):
        np.add.at(Ns, inv[T[:, c]], fn)
    N = Ns[inv]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return {n: N[off[k]:off[k + 1]] for k, n in enumerate(names)}


NODE = 'LizardOrc'
if sys.argv[1] == '--selftest':
    doc, binary = read_glb(Path(sys.argv[2])); D = prims(doc, binary, next(n for n in doc['nodes'] if n.get('name') == NODE))
    R = rule_all(D)
    for name, s in D.items():
        dev = np.degrees(np.arccos(np.clip((R[name] * s['N']).sum(1), -1, 1)))
        print('SELFTEST', name, 'rule vs installed deg: median', round(float(np.median(dev)), 3), 'p99', round(float(np.percentile(dev, 99)), 2),
              'max', round(float(dev.max()), 2), '>1deg', int((dev > 1).sum()), 'of', len(dev))
    sys.exit()

src, inp, out = (Path(a) for a in sys.argv[1:4]); NODE = sys.argv[4] if len(sys.argv) > 4 else NODE
KEEP = [n for n in os.environ.get('KEEP_PRIMS', 'LizHead_A').split(',') if n]
sdoc, sbin = read_glb(src); doc, binary = read_glb(inp); binary = bytearray(binary)
S = prims(sdoc, sbin, next(n for n in sdoc['nodes'] if n.get('name') == NODE))
C = prims(doc, binary, next(n for n in doc['nodes'] if n.get('name') == NODE))
for name in KEEP:                                   # the rule sees the installed geometry of the kept primitives
    C[name].update(P=S[name]['P'], T=S[name]['T'], UV=S[name]['UV'], N=S[name]['N'])
R = rule_all(C)
for name, c in C.items():
    if name in KEEP:
        continue
    s = S[name]; tree = cKDTree(s['P']); N = R[name]
    copied = 0
    for i, h in enumerate(tree.query_ball_point(c['P'], 1e-5)):
        h = [j for j in h if np.abs(s['UV'][j] - c['UV'][i]).max() < 1e-5]
        if h:
            j = max(h, key=lambda j: float(s['N'][j] @ N[i])); N[i] = s['N'][j]; copied += 1
    acc = doc['accessors'][c['prim']['attributes']['NORMAL']]
    c['prim']['attributes']['NORMAL'] = append_accessor(doc, binary, acc, N.astype('<f4').tobytes())
    print('NORMALS', name, 'vertices', len(N), 'installed normal kept', copied, 'rule', len(N) - copied)
for name in KEEP:
    sp, cp = S[name]['prim'], C[name]['prim']
    cp['attributes'] = {k: append_accessor(doc, binary, sdoc['accessors'][i], accessor_bytes(sdoc, sbin, i)) for k, i in sp['attributes'].items()}
    cp['indices'] = append_accessor(doc, binary, sdoc['accessors'][sp['indices']], accessor_bytes(sdoc, sbin, sp['indices']))
    print('KEPT PRIMITIVE', name, 'installed bytes', len(S[name]['T']), 'triangles')
write_glb(out, doc, bytes(binary))
