#!/usr/bin/env python3
"""Remove the buried triangles of every colour LOD and its shadow LOD in the Malevolent Boulder GLB: triangles that
lie inside another stone in every sampled frame of every clip (method of hidden_faces.py, which finds the same 444
on the welded LOD0). Stones with open edges never count as enclosing. Each LOD is tested on its own geometry; nothing else changes. Vertex buffers, normals, UVs,
weights, materials, colour variants, region masks, clips and sockets are untouched: each culled primitive only gets a new
index accessor. A shadow LOD with the same positions and indices as its colour LOD takes the same cut (a buried face
cannot cast a shadow through the stone around it).
Posing: every vertex has one joint (rigid stones), so each joint's transform per frame is fitted (Kabsch) from the
source stones on that bone, rest (work/mesh_in.npz) -> posed (work/posed_verts.npz).
Usage: cull_glb.py <in.glb> <out.glb>"""
import copy
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import accessor_bytes, append_accessor, read_glb, write_glb  # noqa: E402

B = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [.5, .5, 0], [0, .5, .5], [.5, 0, .5], [1 / 3] * 3,
              [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
B = 0.98 * B + 0.02 / 3
DEPTH = 0.005                                  # samples 5 mm out along the face normal must be inside too


def winding(P, tris):
    a = tris[None, :, 0] - P[:, None]; b = tris[None, :, 1] - P[:, None]; c = tris[None, :, 2] - P[:, None]
    la, lb, lc = (np.linalg.norm(x, axis=2) for x in (a, b, c))
    det = np.einsum('mki,mki->mk', a, np.cross(b, c))
    den = (la * lb * lc + np.einsum('mki,mki->mk', a, b) * lc + np.einsum('mki,mki->mk', b, c) * la
           + np.einsum('mki,mki->mk', c, a) * lb)
    return (2 * np.arctan2(det, den)).sum(1) / (4 * np.pi)


def buried(V, f, fl, faces, closed):
    T = V[f[faces]]; nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    S = np.einsum('sk,fkd->fsd', B, T); S = np.concatenate([S, S + DEPTH * nrm[:, None]], 1); out = np.zeros(len(faces), bool)
    for c in closed:
        tris = V[f[fl == c]]; lo = tris.reshape(-1, 3).min(0); hi = tris.reshape(-1, 3).max(0)
        cand = np.where(~out & (fl[faces] != c) & np.all((S >= lo) & (S <= hi), axis=(1, 2)))[0]
        if len(cand):
            w = winding(S[cand].reshape(-1, 3), tris).reshape(len(cand), -1)
            out[cand[np.all(w > 0.5, 1)]] = True
    return out


def kabsch(a, b):
    ca, cb = a.mean(0), b.mean(0); u, _, vt = np.linalg.svd((a - ca).T @ (b - cb))
    r = (u @ np.diag([1, 1, np.sign(np.linalg.det(u @ vt))]) @ vt).T
    return r, cb - r @ ca


def compact(doc, binary):
    """keep only referenced accessors and buffer views (the replaced index buffers drop out); swap_lod0.py's method"""
    used = set()
    for m in doc['meshes']:
        for p in m['primitives']:
            used |= set(p['attributes'].values()) | {p['indices']}
    for s in doc['skins']:
        used.add(s['inverseBindMatrices'])
    for a in doc.get('animations', []):
        for s in a['samplers']:
            used |= {s['input'], s['output']}
    amap = {old: new for new, old in enumerate(sorted(used))}
    views_used = sorted({doc['accessors'][i]['bufferView'] for i in used}
                        | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
    vmap, out, views = {}, bytearray(), []
    for new, old in enumerate(views_used):
        v = copy.deepcopy(doc['bufferViews'][old]); start = v.get('byteOffset', 0)
        out.extend(b'\0' * (-len(out) % 4)); v['byteOffset'] = len(out)
        out.extend(binary[start:start + v['byteLength']]); views.append(v); vmap[old] = new
    doc['accessors'] = [dict(doc['accessors'][old], bufferView=vmap[doc['accessors'][old]['bufferView']]) for old in sorted(used)]
    doc['bufferViews'] = views
    for im in doc.get('images', []):
        if 'bufferView' in im:
            im['bufferView'] = vmap[im['bufferView']]
    for m in doc['meshes']:
        for p in m['primitives']:
            p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}; p['indices'] = amap[p['indices']]
    for s in doc['skins']:
        s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
    for a in doc.get('animations', []):
        for s in a['samplers']:
            s['input'] = amap[s['input']]; s['output'] = amap[s['output']]
    return out


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    doc, binary = read_glb(src); binary = bytearray(binary)
    mi = np.load('work/mesh_in.npz'); sw = np.load('work/src_weights.npz'); pv = np.load('work/posed_verts.npz')
    rest = mi['verts']; sbone = sw['names'][sw['weights'].argmax(1)]; P = pv['P'].astype(np.float64)
    joints = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
    xf = {}
    for name in set(sbone):
        ids = np.where(sbone == name)[0]
        xf[name] = [kabsch(rest[ids], P[k][ids]) for k in range(len(P))]
    shadows = {m.get('name', ''): i for i, m in enumerate(doc['meshes'])}
    for mi_, mesh in enumerate(doc['meshes']):
        name = mesh.get('name', '')
        if name.endswith('_Shadow'):
            continue
        p = mesh['primitives'][0]; A = p['attributes']
        pos = np.frombuffer(accessor_bytes(doc, binary, A['POSITION']), np.float32).reshape(-1, 3).astype(np.float64)
        ia = doc['accessors'][p['indices']]; dt = {5123: np.uint16, 5125: np.uint32}[ia['componentType']]
        f = np.frombuffer(accessor_bytes(doc, binary, p['indices']), dt).reshape(-1, 3).astype(np.int64)
        ja = doc['accessors'][A['JOINTS_0']]
        J = np.frombuffer(accessor_bytes(doc, binary, A['JOINTS_0']), {5121: np.uint8, 5123: np.uint16}[ja['componentType']]).reshape(-1, 4)
        Wt = np.frombuffer(accessor_bytes(doc, binary, A['WEIGHTS_0']), np.float32).reshape(-1, 4)
        assert np.all(Wt.max(1) > 0.999), 'expected one joint per vertex'
        vb = np.c_[pos[:, 0], -pos[:, 2], pos[:, 1]]                 # glTF Y-up -> Blender Z-up
        jn = np.array([joints[j] for j in J[np.arange(len(J)), Wt.argmax(1)]])
        key = np.round(vb, 5); _, weld = np.unique(np.c_[key, np.unique(jn, return_inverse=True)[1]], axis=0, return_inverse=True)
        weld = weld.ravel(); fw = weld[f]; n = weld.max() + 1
        e = np.concatenate([fw[:, [0, 1]], fw[:, [1, 2]], fw[:, [2, 0]]])
        lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)[1]
        fl = lab[fw[:, 0]]
        u, cnt = np.unique(np.sort(e, 1), axis=0, return_counts=True)
        closed = np.setdiff1d(np.unique(fl), lab[u[cnt == 1][:, 0]])   # open stones never enclose
        alive = np.where(buried(vb, f, fl, np.arange(len(f)), closed))[0]
        for k in range(len(P)):
            V = vb.copy()
            for name_ in set(jn):
                ids = jn == name_; r, t = xf[name_][k]; V[ids] = vb[ids] @ r.T + t
            alive = alive[buried(V, f, fl, alive, closed)]
        keep = np.ones(len(f), bool); keep[alive] = False
        if not len(alive):
            print(f'CULL {name}: {len(f)} -> {len(f)} (none buried), unchanged')
            continue
        packed = f[keep].astype(dt).tobytes()
        new = append_accessor(doc, binary, ia, packed); doc['accessors'][new]['count'] = int(keep.sum()) * 3
        doc['accessors'][new].pop('min', None); doc['accessors'][new].pop('max', None)
        p['indices'] = new
        sh = shadows.get(name + '_Shadow')
        if sh is not None:
            q = doc['meshes'][sh]['primitives'][0]
            qa = doc['accessors'][q['indices']]
            qf = np.frombuffer(accessor_bytes(doc, binary, q['indices']), {5123: np.uint16, 5125: np.uint32}[qa['componentType']])
            qp = np.frombuffer(accessor_bytes(doc, binary, q['attributes']['POSITION']), np.float32).reshape(-1, 3)
            same = qf.size == f.size and np.array_equal(qf.reshape(-1, 3), f) and qp.shape == pos.shape and np.allclose(qp, pos, atol=0)
            if same:
                q['indices'] = new
        print(f'CULL {name}: {len(f)} -> {int(keep.sum())} ({len(alive)} buried), shadow {"cut too" if sh is not None and same else "unchanged"}')
    write_glb(dst, doc, bytes(compact(doc, binary)))


main()
