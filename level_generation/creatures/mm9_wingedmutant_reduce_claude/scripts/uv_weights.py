#!/usr/bin/env python3
"""Skin weights for decimated meshes through the preserved UVs (REA_WEIGHTS=component in reduce_ladder.py reads the
output). MM8 Nightmare: its slime lumps interpenetrate and its rest pose differs from the bind pose, so a nearest-face
transfer took weights from a neighbouring lump and new vertices flew off in every pose. The texture-aware collapse
keeps each vertex's UV on its own chart, so the source triangle containing that UV (barycentric weights) is the
surface the vertex came from. A vertex whose UV hit lies over 1 cm away in 3D (or misses every triangle) falls back to
the nearest source vertex with a similar normal. Source vertices keep their weights exactly.
Winged Mutant: the fallback is the Ebora interp_weights.py rule instead (barycentric blend at the closest point of the
source triangles of the vertex's own source piece): 411 of 732 new vertices missed the UV hit (hair locks with a low
texel density, wing membranes), and a nearest-vertex copy turns the steep membrane-helper blends into steps.
Usage: uv_weights.py <ratio,...>  (work/mesh_in.npz, work/src_weights.npz, work/mesh_r<NN>.npz -> work/weights_r<NN>.npz)"""
import sys
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

def pieces(nv, f):
    e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    return connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nv, nv)), directed=False)[1]


def closest_on_tris(p, a, b, c):
    """Ericson's closest point on triangle, vectorised; returns barycentric (u, v, w) for a, b, c"""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(-1), (ac * ap).sum(-1)
    bp = p - b; d3, d4 = (ab * bp).sum(-1), (ac * bp).sum(-1)
    cp = p - c; d5, d6 = (ab * cp).sum(-1), (ac * cp).sum(-1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-30, 1e-30, va + vb + vc)
    v = vb / den; w = vc / den; bary = np.stack([1 - v - w, v, w], -1)
    def setb(m, x):
        bary[m] = x[m]
    ones = lambda *k: np.stack(k, -1)
    z = np.zeros_like(d1); o = np.ones_like(d1)
    # edge and vertex regions (order matters: later rules win only where their conditions hold)
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); t = d1 / np.where(d1 - d3 == 0, 1e-30, d1 - d3); setb(m, ones(1 - t, t, z))
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); t = d2 / np.where(d2 - d6 == 0, 1e-30, d2 - d6); setb(m, ones(1 - t, z, t))
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    t = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-30, (d4 - d3) + (d5 - d6)); setb(m, ones(z, 1 - t, t))
    setb((d1 <= 0) & (d2 <= 0), ones(o, z, z)); setb((d3 >= 0) & (d4 <= d3), ones(z, o, z)); setb((d6 >= 0) & (d5 <= d6), ones(z, z, o))
    q = bary[..., :1] * a + bary[..., 1:2] * b + bary[..., 2:] * c
    return bary, np.linalg.norm(p - q, axis=-1)



s = np.load('work/mesh_in.npz'); sw = np.load('work/src_weights.npz'); W = sw['weights']
sv, sf = s['verts'], s['faces']; suv = s['wuv'].reshape(-1, 3, 2)
utree = cKDTree(suv.mean(1)); vtree = cKDTree(sv)


def vnormals(v, f):
    n = np.zeros_like(v); fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


sn = vnormals(sv, sf)
spc = pieces(len(sv), sf); sfp = spc[sf[:, 0]]
for r in [float(x) for x in sys.argv[1].split(',')]:
    tag = int(round(r * 100)); d = np.load(f'work/mesh_r{tag}.npz'); v, f = d['verts'], d['faces']
    cuv = d['wuv'].reshape(-1, 3, 2); cn = vnormals(v, f)
    first = np.full(len(v), -1); corner = np.repeat(np.arange(len(f)), 3); fv = f.reshape(-1)
    first[fv[::-1]] = np.arange(len(fv))[::-1]  # one wedge per vertex
    uv = cuv.reshape(-1, 2)[first]
    out = np.zeros((len(v), W.shape[1]), np.float32); hit = np.zeros(len(v), bool)
    _, cand = utree.query(uv, 48)
    for i in range(len(v)):
        for t in cand[i]:
            a, b, c = suv[t]; m = np.array([b - a, c - a]).T
            try:
                l1, l2 = np.linalg.solve(m, uv[i] - a)
            except np.linalg.LinAlgError:
                continue
            l0 = 1 - l1 - l2
            if min(l0, l1, l2) < -1e-4:
                continue
            bary = np.clip([l0, l1, l2], 0, 1); bary /= bary.sum()
            if np.linalg.norm(bary @ sv[sf[t]] - v[i]) > .01:
                continue
            out[i] = bary @ W[sf[t]]; hit[i] = True
            break
    miss = np.where(~hit)[0]
    if len(miss):
        cpc = pieces(len(v), f); near = spc[vtree.query(v)[1]]
        for pc in np.unique(cpc[miss]):
            sp = np.bincount(near[cpc == pc]).argmax()
            ids = miss[cpc[miss] == pc]
            fi = np.flatnonzero(sfp == sp); t = cKDTree(sv[sf[fi]].mean(1))
            k = min(24, len(fi)); _, cand = t.query(v[ids], k); cand = fi[cand.reshape(len(ids), k)]
            tri = sv[sf[cand]]
            bary, dist = closest_on_tris(np.repeat(v[ids][:, None], k, 1), tri[:, :, 0], tri[:, :, 1], tri[:, :, 2])
            best = dist.argmin(1); rr = np.arange(len(ids))
            out[ids] = (W[sf[cand[rr, best]]] * bary[rr, best][..., None]).sum(1)
    sidx = d['src_index'] if 'src_index' in d.files else np.full(len(v), -1)
    out[sidx >= 0] = W[sidx[sidx >= 0]]
    np.savez(f'work/weights_r{tag}.npz', weights=out, names=sw['names'])
    print('UVWEIGHTS', tag, len(v), 'exact', int((sidx >= 0).sum()), 'uv hits', int(hit.sum()), 'fallback', len(miss))
