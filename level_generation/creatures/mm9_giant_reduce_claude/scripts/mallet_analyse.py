"""Measure the installed Meshy mallet (bind space, glTF axes) for the low-poly rebuild: pieces, shaft axis, head axis and
cross-section, radial profile of everything within 9 cm of the shaft axis. Writes work/mallet_geom.json."""
import json, sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
m = np.load('work/mallet_old.npz'); P, I = m['P'].astype(float), m['I']
key = np.round(P, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); F = inv[I]
n = inv.max() + 1; e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[F[:, 0]]
U = np.zeros((n, 3)); U[inv] = P
c = U.mean(0); ax = np.linalg.svd(U - c, full_matrices=False)[2][0]
t = (U - c) @ ax; r = np.linalg.norm((U - c) - np.outer(t, ax), axis=1)
if r[t < 0].max() < r[t > 0].max():
    ax = -ax; t = -t
# refine the shaft axis on the thin shaft pieces (all vertices within 4 cm of the first axis, away from the head)
sel = (r < 0.04) & (t > -0.25) & (t < 0.8)
c2 = U[sel].mean(0); ax2 = np.linalg.svd(U[sel] - c2, full_matrices=False)[2][0]
if ax2 @ ax < 0: ax2 = -ax2
t = (U - c2) @ ax2; R = (U - c2) - np.outer(t, ax2); r = np.linalg.norm(R, axis=1)
out = {'shaft_c': c2.tolist(), 'shaft_ax': ax2.tolist(), 'pieces': []}
for p in np.unique(pc):
    vs = np.unique(F[pc == p]); out['pieces'].append({'id': int(p), 'faces': int((pc == p).sum()), 't': [float(t[vs].min()), float(t[vs].max())], 'r': [float(r[vs].min()), float(r[vs].max())]})
    print('piece', p, (pc == p).sum(), 't %.3f..%.3f r %.3f..%.3f' % (t[vs].min(), t[vs].max(), r[vs].min(), r[vs].max()))
# head: vertices with r > 0.1
H = U[r > 0.1]; hc = H.mean(0); hax = np.linalg.svd(H - hc, full_matrices=False)[2]
print('head centre t', float((hc - c2) @ ax2), 'head pca axes', hax)
# head long axis = the PCA axis most perpendicular to the shaft
k = int(np.argmin(np.abs(hax @ ax2))); hx = hax[k] - (hax[k] @ ax2) * ax2; hx /= np.linalg.norm(hx)
s = (H - hc) @ hx; q = (H - hc) - np.outer(s, hx); qr = np.linalg.norm(q, axis=1)
print('head length', s.min(), s.max(), 'cross radius max', qr.max())
# cross-section polygon: angle histogram of vertices at the outer radius around the head axis
e1 = ax2 - (ax2 @ hx) * hx; e1 /= np.linalg.norm(e1); e2 = np.cross(hx, e1)
ang = np.degrees(np.arctan2(q @ e2, q @ e1)) % 360
outer = qr > 0.9 * qr.max()
hist = np.histogram(ang[outer], bins=72, range=(0, 360))[0]
print('outer-radius angle histogram (5 deg bins):', ' '.join(str(x) for x in hist))
prof = []
for t0 in np.arange(t.min(), t.max() + 0.005, 0.005):
    mm = (t >= t0) & (t < t0 + 0.005) & (r < 0.09)
    prof.append([float(t0), float(r[mm].max()) if mm.any() else None])
out.update(head_c=hc.tolist(), head_ax=hx.tolist(), head_e1=e1.tolist(), head_e2=e2.tolist(), head_s=[float(s.min()), float(s.max())],
           head_rmax=float(qr.max()), profile=prof)
json.dump(out, open('work/mallet_geom.json', 'w'), indent=1)
print('PROFILE'); print('\n'.join(f'{a:.3f} {b if b is None else round(b, 4)}' for a, b in prof))
