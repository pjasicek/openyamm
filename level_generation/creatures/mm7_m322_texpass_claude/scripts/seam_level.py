"""Seam levelling for a texture on a chart layout (after Lempitsky and Ivanov): one additive colour correction per
(welded vertex, chart), smooth along the chart's edges, that makes both sides of every chart seam agree; the
correction is interpolated per texel with the raster's barycentrics. Only seam pairs of the same colour class (classify(colours)
-> int per node, e.g. skin, green cloth, hair, other) that differ by less than EDGE levels are levelled; others (a real
colour edge along the seam: trousers beside the dark lacing) are left to the smoothness term, so one material is never
pulled toward another.

level(img, tri_id, bary, uv, wtri, chart) -> (levelled img, report). img (S,S,3) float sRGB levels."""
import numpy as np
from scipy.sparse import coo_matrix, vstack
from scipy.sparse.linalg import lsqr

import texlib

EDGE = 25.0
SEAM_WEIGHT = 4.0
SMOOTH_WEIGHT = 1.0
DAMP = 0.02


def corner_colours(img, uv, wtri, chart):
    """Mean colour per (vertex, chart) from points 20 % in from each corner toward its face centre."""
    centre = uv.mean(1, keepdims=True)
    pts = 0.8 * uv + 0.2 * centre                                    # (T,3,2)
    col = texlib.bilinear(img, pts.reshape(-1, 2)).reshape(len(uv), 3, 3)
    keys = wtri.astype(np.int64) * (chart.max() + 1) + chart[:, None]
    uniq, inv = np.unique(keys.ravel(), return_inverse=True)
    inv = inv.ravel()
    acc = np.zeros((len(uniq), 3))
    np.add.at(acc, inv, col.reshape(-1, 3))
    cnt = np.bincount(inv, minlength=len(uniq)).astype(np.float64)
    return uniq, inv.reshape(-1, 3), acc / cnt[:, None]


def level(img, tri_id, bary, uv, wtri, chart, select=None, classify=None):
    """select: optional per-face bool; only seams between selected faces are levelled (others still smooth)."""
    nch = chart.max() + 1
    uniq, node, col = corner_colours(img, uv, wtri, chart)
    vert = uniq // nch
    n = len(uniq)
    # seam pairs: nodes of the same welded vertex in different charts
    order = np.argsort(vert, kind='stable')
    rows, cols, vals, rhs = [], [], [], []
    r = 0
    pairs = []
    sel_node = np.zeros(n, bool)
    if select is None:
        sel_node[:] = True
    else:
        np.logical_or.at(sel_node, node[select].ravel(), True)
    start = 0
    vs = vert[order]
    while start < n:
        end = start
        while end < n and vs[end] == vs[start]:
            end += 1
        group = order[start:end]
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if sel_node[a] and sel_node[b]:
                    pairs.append((a, b))
        start = end
    pairs = np.array(pairs, np.int64).reshape(-1, 2)
    diff = col[pairs[:, 0]] - col[pairs[:, 1]]                       # (P,3)
    mag = np.abs(diff).max(1)
    same = np.ones(len(pairs), bool) if classify is None else classify(col[pairs[:, 0]]) == classify(col[pairs[:, 1]])
    keep = (mag < EDGE) & same
    pairs, diff, mag = pairs[keep], diff[keep], mag[keep]
    w = np.full(len(pairs), SEAM_WEIGHT)
    # smoothness: edges of each face between its corner nodes
    e = np.concatenate([node[:, [0, 1]], node[:, [1, 2]], node[:, [2, 0]]])
    e = np.unique(np.sort(e, 1), axis=0)
    e = e[e[:, 0] != e[:, 1]]
    P, E = len(pairs), len(e)
    A_seam = coo_matrix((np.r_[w, -w], (np.r_[np.arange(P), np.arange(P)], np.r_[pairs[:, 0], pairs[:, 1]])),
                        shape=(P, n))
    A_smooth = coo_matrix((np.r_[np.full(E, SMOOTH_WEIGHT), np.full(E, -SMOOTH_WEIGHT)],
                           (np.r_[np.arange(E), np.arange(E)], np.r_[e[:, 0], e[:, 1]])), shape=(E, n))
    A_damp = coo_matrix((np.full(n, DAMP), (np.arange(n), np.arange(n))), shape=(n, n))
    A = vstack([A_seam, A_smooth, A_damp]).tocsr()
    g = np.zeros((n, 3))
    for c in range(3):
        b = np.r_[-w * diff[:, c], np.zeros(E), np.zeros(n)]
        g[:, c] = lsqr(A, b, atol=1e-8, btol=1e-8, iter_lim=20000)[0]
    after = (col[pairs[:, 0]] + g[pairs[:, 0]]) - (col[pairs[:, 1]] + g[pairs[:, 1]])
    keep = np.ones(len(pairs), bool)
    report = {'seam_pairs': int(len(same)), 'seam_pairs_levelled': int(keep.sum()),
              'seam_diff_mean_before': round(float(np.abs(diff[keep]).mean()), 2),
              'seam_diff_mean_after': round(float(np.abs(after[keep]).mean()), 2),
              'seam_diff_p95_before': round(float(np.percentile(np.abs(diff[keep]).max(1), 95)), 2),
              'seam_diff_p95_after': round(float(np.percentile(np.abs(after[keep]).max(1), 95)), 2),
              'correction_p95': round(float(np.percentile(np.abs(g).max(1), 95)), 2)}
    cov = tri_id >= 0
    t = tri_id[cov]
    corr = (g[node[t]] * bary[cov][:, :, None]).sum(1)
    out = img.copy()
    out[cov] = img[cov] + corr
    return texlib.pad(out, cov), report
