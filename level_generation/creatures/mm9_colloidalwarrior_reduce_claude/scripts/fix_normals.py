#!/usr/bin/env python3
"""LOD0 normals of the reduced Ebora the way her own build made them (mm9_ebora_claude/scripts/build_glb.py):
every candidate vertex that is a source vertex (same material, position and UV within 1e-5) takes the installed
normal byte for byte (kept head set with the smoothed nose ridge, wings with the bent membrane normals, hands, neck
seam, soles, and the cut edge of the reduced parts); every new vertex takes build_glb's rule on the reduced mesh:
area-weighted face normals merged by position within the material, own faces' normal where the merge cancels (thin
shells), and on wing membranes the bend along glTF +y (x1.6). Blender's export normals are discarded.
Usage: fix_normals.py <source.glb> <in.glb> <out.glb> [mesh node]   (also: --selftest <source.glb>)"""
import os, struct, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402
BEND = 1.6


def arr(doc, binary, idx, dt='<f4'):
    a = doc['accessors'][idx]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    ct = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
    return np.frombuffer(accessor_bytes(doc, binary, idx), ct).reshape(-1, n) if n > 1 else np.frombuffer(accessor_bytes(doc, binary, idx), ct)


def prims(doc, binary, node):
    out = {}
    for p in doc['meshes'][node['mesh']]['primitives']:
        a = p['attributes']
        out[doc['materials'][p['material']]['name']] = dict(prim=p, P=arr(doc, binary, a['POSITION']).astype(float),
            UV=arr(doc, binary, a['TEXCOORD_0']).astype(float), N=arr(doc, binary, a['NORMAL']).astype(float),
            T=arr(doc, binary, p['indices']).astype(int).reshape(-1, 3))
    return out


def membrane_vertices(P, T):
    """vertices of the two membrane shells (connected pieces of the wing primitive with 600-900 faces; spars 420)"""
    key = np.round(P, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    par = np.arange(inv.max() + 1)

    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for t in inv[T]:
        a = f(t[0]); par[f(t[1])] = a; par[f(t[2])] = a
    root = np.array([f(i) for i in inv[T[:, 0]]])
    u, c = np.unique(root, return_counts=True)
    mem_roots = u[(c > 500) & (c < 1200)]
    sel = np.isin(root, mem_roots)
    m = np.zeros(len(P), bool); m[np.unique(T[sel])] = True
    return m, [int(x) for x in c[(c > 500) & (c < 1200)]]


def rule_all(D, mems):
    """build_glb's rule over all primitives at once (it merges positions across materials: neck and waist seams)"""
    names = list(D); off = np.cumsum([0] + [len(D[n]['P']) for n in names])
    P = np.vstack([D[n]['P'] for n in names]); T = np.vstack([D[n]['T'] + o for n, o in zip(names, off)])
    mem = np.concatenate([mems.get(n, np.zeros(len(D[n]['P']), bool)) for n in names])
    N = rule(P, T, mem)
    return {n: N[off[k]:off[k + 1]] for k, n in enumerate(names)}


def rule(P, T, mem=None):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    key = np.round(P, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    Ns = np.zeros((inv.max() + 1, 3))
    for c in range(3):
        np.add.at(Ns, inv[T[:, c]], fn)
    N = Ns[inv]; own = np.zeros_like(P)
    for c in range(3):
        np.add.at(own, T[:, c], fn)
    nl = np.linalg.norm(N, axis=1); ol = np.linalg.norm(own, axis=1)
    bad = (nl < 0.5 * ol) | ((N * own).sum(1) < 0)
    N[bad] = own[bad]
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    if mem is not None and mem.any():
        U = np.array([0.0, 1.0, 0.0])
        Nm = N[mem] + BEND * (U - (N[mem] @ U)[:, None] * N[mem])
        N[mem] = Nm / np.maximum(np.linalg.norm(Nm, axis=1, keepdims=True), 1e-12)
    return N


if sys.argv[1] == '--selftest':
    doc, binary = read_glb(Path(sys.argv[2])); node = next(n for n in doc['nodes'] if n.get('name') == 'Ebora')
    D = prims(doc, binary, node); R = rule_all(D, {'EboraWing': membrane_vertices(D['EboraWing']['P'], D['EboraWing']['T'])[0]})
    for name, s in D.items():
        sizes = membrane_vertices(s['P'], s['T'])[1] if name == 'EboraWing' else []
        N = R[name]; dev = np.degrees(np.arccos(np.clip((N * s['N']).sum(1), -1, 1)))
        print('SELFTEST', name, 'membranes', sizes, 'rule vs installed deg: median', round(float(np.median(dev)), 3),
              'p99', round(float(np.percentile(dev, 99)), 2), 'max', round(float(dev.max()), 2), '>1deg', int((dev > 1).sum()), 'of', len(dev))
    sys.exit()

src, inp, out = (Path(a) for a in sys.argv[1:4]); NODE = sys.argv[4] if len(sys.argv) > 4 else 'Ebora'
sdoc, sbin = read_glb(src); doc, binary = read_glb(inp); binary = bytearray(binary)
S = prims(sdoc, sbin, next(n for n in sdoc['nodes'] if n.get('name') == NODE))
C = prims(doc, binary, next(n for n in doc['nodes'] if n.get('name') == NODE))
smem = membrane_vertices(S['EboraWing']['P'], S['EboraWing']['T'])[0]
R = rule_all(C, {'EboraWing': smem[cKDTree(S['EboraWing']['P']).query(C['EboraWing']['P'])[1]]})
for name, c in C.items():
    s = S[name]; tree = cKDTree(s['P']); N = R[name]
    hits = tree.query_ball_point(c['P'], 1e-5)
    copied = 0
    for i, h in enumerate(hits):
        h = [j for j in h if np.abs(s['UV'][j] - c['UV'][i]).max() < 1e-5]
        if h:
            j = max(h, key=lambda j: float(s['N'][j] @ N[i])); N[i] = s['N'][j]; copied += 1
    acc = doc['accessors'][c['prim']['attributes']['NORMAL']]
    c['prim']['attributes']['NORMAL'] = append_accessor(doc, binary, acc, N.astype('<f4').tobytes())
    print('NORMALS', name, 'vertices', len(N), 'installed normal kept', copied, 'rule', len(N) - copied)
# primitives kept whole (head set, wings): the installed primitive byte for byte (attributes and indices), so twin
# vertices with the same position and UV but different normals cannot be swapped
for name in [n for n in os.environ.get('KEEP_PRIMS', 'EboraHead,EboraWing').split(',') if n]:
    sp, cp = S[name]['prim'], C[name]['prim']
    assert len(S[name]['T']) == len(C[name]['T']), f'{name} was not kept whole'
    cp['attributes'] = {k: append_accessor(doc, binary, sdoc['accessors'][i], accessor_bytes(sdoc, sbin, i)) for k, i in sp['attributes'].items()}
    cp['indices'] = append_accessor(doc, binary, sdoc['accessors'][sp['indices']], accessor_bytes(sdoc, sbin, sp['indices']))
    print('KEPT PRIMITIVE', name, 'installed bytes')
# one attribute encoding for every LOD0 primitive, the installed one (JOINTS_0 u16, indices u32): build_actor_lods
# merges the primitives into the shadow mesh and refuses mixed encodings
kept_names = [n for n in os.environ.get('KEEP_PRIMS', 'EboraHead,EboraWing').split(',') if n]
for name, c in C.items():
    if name in kept_names:
        continue
    p_ = c['prim']; ja = doc['accessors'][p_['attributes']['JOINTS_0']]
    if ja['componentType'] != 5123:
        J = arr(doc, binary, p_['attributes']['JOINTS_0']).astype('<u2')
        p_['attributes']['JOINTS_0'] = append_accessor(doc, binary, dict(ja, componentType=5123), J.tobytes())
    ia = doc['accessors'][p_['indices']]
    if ia['componentType'] != 5125:
        p_['indices'] = append_accessor(doc, binary, dict(ia, componentType=5125), c['T'].astype('<u4').tobytes())
write_glb(out, doc, bytes(binary))
