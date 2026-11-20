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
print(f'atlas {100 * TQ.raster_union(uv).mean():.1f} %  islands {len(counts)}  fragments {100 * w[frag].sum():.1f} %  '
      f'stretch p90 {TQ.weighted_percentile(stretch, w, 90):.2f}  density spread '
      f'{TQ.weighted_percentile(dens, w, 90) / TQ.weighted_percentile(dens, w, 10):.2f}  zero-area {int((a2 < 1e-12).sum())}')
