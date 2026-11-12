"""Quick layout numbers of a texture-pass layout npz (as texture_quality.py): atlas use, fragments, stretch p90,
density spread. Usage: tp_layout_stats.py <layout npz>"""
import sys
import numpy as np
import tp_common as C
import texture_quality as TQ

L = np.load(sys.argv[1])
uv, xyz = L['uv'].astype(np.float64), L['xyz'].astype(np.float64)
a3, a2 = C.tri_area3(xyz), C.tri_area2(uv)
isl = TQ.islands(uv, xyz)
_, isl = np.unique(isl, return_inverse=True)
counts = np.bincount(isl)
frag = (counts[isl] < 8)
e1, e2 = xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]
d1, d2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
stretch = []
for i in range(len(uv)):
    n = np.cross(e1[i], e2[i]); n /= max(np.linalg.norm(n), 1e-12)
    u = e1[i] / max(np.linalg.norm(e1[i]), 1e-12); v = np.cross(n, u)
    P = np.array([[e1[i] @ u, e2[i] @ u], [e1[i] @ v, e2[i] @ v]])
    T = np.array([d1[i], d2[i]]).T
    try:
        J = T @ np.linalg.inv(P)
        s = np.linalg.svd(J, compute_uv=False)
        stretch.append(s[0] / max(s[1], 1e-12))
    except np.linalg.LinAlgError:
        stretch.append(np.inf)
stretch = np.array(stretch)
dens = np.sqrt(a2 / np.maximum(a3, 1e-12))
w = a3 / a3.sum()
union = TQ.raster_union(uv).mean()
print(f'overlap: uv sum {100 * a2.sum():.1f} % against union {100 * union:.1f} % '
      '(must be equal; a gap means overlapping charts: never upload such a layout)')
print(f'atlas {100 * union:.1f} %  islands {len(counts)}  fragments {100 * w[frag].sum():.1f} %  '
      f'stretch p90 {TQ.weighted_percentile(stretch, w, 90):.2f}  density spread '
      f'{TQ.weighted_percentile(dens, w, 90) / TQ.weighted_percentile(dens, w, 10):.2f}  zero-area {int((a2 < 1e-12).sum())}')
# fragments that are whole 3D pieces (separate closed or open pieces under 8 triangles) cannot merge into bigger charts
from scipy.sparse import coo_matrix  # noqa: E402
from scipy.sparse.csgraph import connected_components  # noqa: E402
_, pv = np.unique(np.round(xyz.reshape(-1, 3), 6), axis=0, return_inverse=True)
pv = pv.reshape(-1, 3)
nv = pv.max() + 1
gr = coo_matrix((np.ones(pv.size), (pv.ravel(), np.roll(pv, 1, 1).ravel())), shape=(nv, nv))
_, lab = connected_components(gr, directed=False)
piece = lab[pv[:, 0]]
small_piece = np.bincount(piece)[piece] < 8
print(f'fragments on pieces under 8 triangles {100 * w[frag & small_piece].sum():.1f} %, pieces {piece.max() + 1}')
