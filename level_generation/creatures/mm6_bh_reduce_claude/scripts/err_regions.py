"""Rest-pose error by source region: source surface samples -> exact distance to the candidate's triangles (16 nearest
by centroid), and candidate vertices -> source. Usage: err_regions.py work/mesh_rNN.npz [label.npy]"""
import sys
import numpy as np
from scipy.spatial import cKDTree


def pt_tri(p, a, b, c):
    # closest point on triangle (Ericson), vectorised
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(-1), (ac * ap).sum(-1)
    bp = p - b; d3, d4 = (ab * bp).sum(-1), (ac * bp).sum(-1)
    cp = p - c; d5, d6 = (ab * cp).sum(-1), (ac * cp).sum(-1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-30, 1e-30, va + vb + vc)
    v = vb / den; w = vc / den; q = a + ab * v[..., None] + ac * w[..., None]
    sel = lambda m, x: np.where(m[..., None], x, q)
    with np.errstate(all='ignore'):
        e = (va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0); q = sel(e, b + (c - b) * ((d4 - d3) / (d4 - d3 + d5 - d6))[..., None])
        e = (vb <= 0) & (d2 >= 0) & (d6 <= 0); q = sel(e, a + ac * (d2 / (d2 - d6))[..., None])
        e = (vc <= 0) & (d1 >= 0) & (d3 <= 0); q = sel(e, a + ab * (d1 / (d1 - d3))[..., None])
        q = sel((d6 >= 0) & (d5 <= d6), c); q = sel((d3 >= 0) & (d4 <= d3), b); q = sel((d1 <= 0) & (d2 <= 0), a)
    return np.linalg.norm(p - q, axis=-1)


def dist(p, v, f, k=16):
    t = v[f]; _, i = cKDTree(t.mean(1)).query(p, k)
    return pt_tri(p[:, None], t[i, 0], t[i, 1], t[i, 2]).min(1)


def samples(v, f, n=150000):
    a = v[f]; ar = np.linalg.norm(np.cross(a[:, 1] - a[:, 0], a[:, 2] - a[:, 0]), axis=1)
    i = np.random.default_rng(0).choice(len(f), n, p=ar / ar.sum()); r = np.random.default_rng(1).random((n, 2))
    m = r.sum(1) > 1; r[m] = 1 - r[m]
    return a[i, 0] + r[:, :1] * (a[i, 1] - a[i, 0]) + r[:, 1:] * (a[i, 2] - a[i, 0]), i


if __name__ == '__main__':
    s = np.load('work/mesh_in.npz'); c = np.load(sys.argv[1])
    comp = np.load('work/components.npy'); reg = np.load('work/mask_region.npy')
    ps, fi = samples(s['verts'], s['faces'])
    d1 = dist(ps, c['verts'], c['faces']) * 1000; d2 = dist(c['verts'], s['verts'], s['faces']) * 1000
    print(sys.argv[1], 'p99 s->c', round(np.percentile(d1, 99), 2), 'c->s', round(np.percentile(d2, 99), 2),
          'max', round(max(d1.max(), d2.max()), 2))
    lab = np.load(sys.argv[2])[fi] if len(sys.argv) > 2 else np.where(comp[fi] != 1, 9, reg[fi])
    for L in np.unique(lab):
        m = lab == L
        print(f' label {L}: p99 {np.percentile(d1[m], 99):.2f} max {d1[m].max():.2f} frac>2mm {(d1[m] > 2).mean():.3f}')
    hi = ps[d1 > 3]; key = np.round(hi / .05).astype(int)
    if len(hi):
        u, cnt = np.unique(key, axis=0, return_counts=True)
        for k in np.argsort(-cnt)[:8]: print(' spot', np.round(u[k] * .05, 2), cnt[k])
