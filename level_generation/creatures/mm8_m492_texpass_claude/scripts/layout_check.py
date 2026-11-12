"""texture_quality.py measures of a layout npz before any paint: atlas use (all parts, and part 0 = the LOD0 body as
the audit counts it), islands, fragment surface, stretch p90, density spread. Usage: layout_check.py <layout npz>"""
import sys

import numpy as np

import tp
import texture_quality as TQ

lay = np.load(sys.argv[1])
uv, xyz, part = lay['uv'], lay['xyz'], lay['part']


def measure(sel, label):
    tu, tx = uv[sel], xyz[sel]
    e1, e2 = tx[:, 1] - tx[:, 0], tx[:, 2] - tx[:, 0]
    a3 = tp.tri_area3(tx)
    px = tu * 2048
    d1, d2 = px[:, 1] - px[:, 0], px[:, 2] - px[:, 0]
    a2 = 0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0])
    ok = a3 > 1e-12
    extent = float(np.ptp(tx.reshape(-1, 3), 0).max())
    dens = np.sqrt(a2[ok] / a3[ok]) * extent
    w = a3[ok]
    x = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-12)
    n = np.cross(e1, e2)
    y = np.cross(n, x)
    y /= np.maximum(np.linalg.norm(y, axis=1, keepdims=True), 1e-12)
    P = np.stack([np.stack([(e1 * x).sum(1), (e1 * y).sum(1)], 1), np.stack([(e2 * x).sum(1), (e2 * y).sum(1)], 1)], 2)[ok]
    T = np.stack([d1, d2], 2)[ok]
    sv = np.linalg.svd(T @ np.linalg.pinv(P), compute_uv=False)
    st = sv[:, 0] / np.maximum(sv[:, 1], 1e-9)
    isl = TQ.islands(tu, tx)
    _, inv, cnt = np.unique(isl, return_inverse=True, return_counts=True)
    frag = cnt[inv] < 8
    p10, p50, p90 = (TQ.weighted_percentile(dens, w, q) for q in (10, 50, 90))
    print(f'{label}: atlas {100 * TQ.raster_union(tu).mean():.1f}% islands {len(cnt)} fragments '
          f'{100 * a3[frag].sum() / a3.sum():.1f}% stretch p90 {TQ.weighted_percentile(st, w, 90):.2f} '
          f'density p10/p50/p90 {p10:.0f}/{p50:.0f}/{p90:.0f} spread {p90 / p10:.2f} zero-area {(a2 < 1e-9).sum()}')


measure(np.ones(len(uv), bool), 'all parts')
if part.max() > 0:
    measure(part == 0, 'part 0 (LOD0 body)')
