"""Skin weights for every ladder step, piece-aware and interpolated (MM6 Titan/Nightmare lessons; the nearest-vertex
piece weights of reduce_ladder.py left 13-20 mm errors at Ebora's hips, knees and shoulders, where the half-joint
helpers blend steeply): source vertices keep their source weights exactly; a new vertex takes the barycentric blend of
the closest point on the source triangles of its own source piece (piece by majority vote of the candidate piece's
nearest source vertices). Top 4 influences, normalised. Usage: interp_weights.py <tag,...>  -> work/weights_<tag>.npz"""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree


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


S = np.load('work/mesh_in.npz'); sv, sf, W = S['verts'], S['faces'], S['W']
spc = pieces(len(sv), sf); sfp = spc[sf[:, 0]]; stree = cKDTree(sv)
cen_trees = {}
for tag in sys.argv[1].split(','):
    C = np.load(f'work/mesh_{tag}.npz'); cv, cf, sidx = C['verts'], C['faces'], C['src_index']
    out = np.zeros((len(cv), W.shape[1]), np.float32)
    have = sidx >= 0; out[have] = W[sidx[have]]
    cpc = pieces(len(cv), cf); near = spc[stree.query(cv)[1]]
    new = np.flatnonzero(~have)
    for pc in np.unique(cpc[new]):
        sp = np.bincount(near[cpc == pc]).argmax()
        ids = new[cpc[new] == pc]
        if sp not in cen_trees:
            fi = np.flatnonzero(sfp == sp); cen_trees[sp] = (fi, cKDTree(sv[sf[fi]].mean(1)))
        fi, t = cen_trees[sp]
        k = min(24, len(fi)); _, cand = t.query(cv[ids], k); cand = fi[cand.reshape(len(ids), k)]
        tri = sv[sf[cand]]  # (n, k, 3, 3)
        bary, dist = closest_on_tris(np.repeat(cv[ids][:, None], k, 1), tri[:, :, 0], tri[:, :, 1], tri[:, :, 2])
        best = dist.argmin(1); r = np.arange(len(ids))
        bt = sf[cand[r, best]]; bb = bary[r, best]
        out[ids] = (W[bt] * bb[..., None]).sum(1)
    if 'copy_of' in C.files:  # rebuilt hair back copies: the front vertex's weights exactly
        co = C['copy_of']; m = co >= 0; out[m] = out[co[m]]
    o4 = np.argsort(-out, 1)[:, 4:]
    np.put_along_axis(out, o4, 0, 1)
    out /= np.maximum(out.sum(1, keepdims=True), 1e-12)
    np.savez(f'work/weights_{tag}.npz', W=out, names=S['names'])
    print('WEIGHTS', tag, 'source', int(have.sum()), 'interpolated', len(new), 'pieces', len(np.unique(cpc)))
