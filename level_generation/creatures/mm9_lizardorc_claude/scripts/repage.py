"""Body density: the 4K paint on one 2K page gives 690 texels per metre against the head's 1430. The right half takes the left half's UVs (the mesh is exactly mirrored, the masters are symmetric), the freed space goes, and the left charts move at 1:1 from the 4K paint onto two 2K pages. No resample, no repaint.
Writes work/pages.npz: ub2 (faces,3,2; page uv, v up as ub), page (per face), boxes (x0,y0,w,h,page,px,py per chart in 4K pixels, y down)."""
import numpy as np, sys
sys.path.insert(0, "scripts")
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components as cc
J = np.load('work/joined.npz'); U = np.load('work/uv.npz'); up = J['co_up']; ub, ob = U['ub'].copy(), U['ob']
S4 = 4096; S = 2048; M = 6
cu = up[ob]; xc = cu[:, :, 0].mean(1)
key = lambda P: tuple(sorted(map(tuple, np.round(P, 5).tolist())))
L = {}
for i in np.where(xc >= 0)[0]: L[key(cu[i])] = i
miss = 0; twin = np.arange(len(ob))
for i in np.where(xc < 0)[0]:
    j = L.get(key(cu[i] * [-1, 1, 1]))
    if j is None: miss += 1; continue
    twin[i] = j
    q = np.round(cu[i] * [-1, 1, 1], 5); r = np.round(cu[j], 5)
    o = [int(np.argmin(((r - q[k]) ** 2).sum(1))) for k in range(3)]
    ub[i] = U['ub'][j][o]
print('faces', len(ob), 'right', int((xc < 0).sum()), 'no twin', miss)
own = twin == np.arange(len(ob))
# charts of the kept faces: shared uv corners
k = np.round(ub[own].reshape(-1, 2) * 2 ** 18).astype(np.int64); _, inv = np.unique(k, axis=0, return_inverse=True); inv = inv.ravel().reshape(-1, 3)
n = inv.max() + 1; e = np.vstack([inv[:, [0, 1]], inv[:, [1, 2]]]); nc, lb = cc(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fc = lb[inv[:, 0]]; ids = np.where(own)[0]; chart = -np.ones(len(ob), int); chart[ids] = fc; chart[~own] = chart[twin[~own]]
import rast
from scipy import ndimage as ndi
from scipy.signal import fftconvolve
sys.path.insert(0, 'scripts')
C = 4; G4 = S4 // C; G2 = S // C
F4, _ = rast.raster(ub[ids], S4)                      # 4K raster of the kept faces
lab = -np.ones((S4, S4), np.int32); m = F4 >= 0; lab[m] = fc[F4[m]]
masks = {}
for c in range(nc):
    yy, xx = np.where(lab == c)
    q = ub[ids[fc == c]].reshape(-1, 2); xx = np.r_[xx, np.round(q[:, 0] * S4).astype(int).clip(0, S4 - 1)]; yy = np.r_[yy, np.round((1 - q[:, 1]) * S4).astype(int).clip(0, S4 - 1)]
    g = np.zeros((G4, G4), bool); g[yy // C, xx // C] = True; g = ndi.binary_dilation(g, iterations=1)
    y0, x0 = np.where(g.any(1))[0][[0, -1]], np.where(g.any(0))[0][[0, -1]]
    masks[c] = (y0[0], x0[0], g[y0[0]:y0[1] + 1, x0[0]:x0[1] + 1])
order = sorted(masks, key=lambda c: -masks[c][2].sum())
occ = [np.zeros((G2, G2), bool)]; place = {}
for c in order:
    my, mx, g = masks[c]; h, w = g.shape; done = False
    for p in range(len(occ) + 1):
        if p == len(occ): occ.append(np.zeros((G2, G2), bool))
        o = occ[p].astype(np.float32); cor = fftconvolve(o, g[::-1, ::-1].astype(np.float32), mode='full')[h - 1:G2, w - 1:G2]
        free = np.argwhere(cor < .5)
        if len(free):
            k = np.argmin(free[:, 0] * 2 + free[:, 1]); oy, ox = free[k]; occ[p][oy:oy + h, ox:ox + w] |= g; place[c] = (p, oy, ox); done = True; break
print('pages', len(occ), 'fill', [round(float(o.mean()), 2) for o in occ])
ub2 = np.zeros_like(ub); page = np.zeros(len(ob), int); moves = []
for c, (p, oy, ox) in place.items():
    my, mx, g = masks[c]; dy = (oy - my) * C; dx = (ox - mx) * C; moves.append((c, p, dy, dx, my, mx, *g.shape))
    mk = chart == c; page[mk] = p; q = ub[mk].reshape(-1, 2)
    ub2[mk] = np.c_[(q[:, 0] * S4 + dx) / S, 1 - ((1 - q[:, 1]) * S4 + dy) / S].reshape(-1, 3, 2)
np.savez('work/pages.npz', ub2=ub2, page=page, moves=np.array(moves), own=own, masks=np.array([masks[c][2] for c in range(nc)], dtype=object), allow_pickle=True)
# measured density, texels per metre on the fitted mesh
co = J['co']; P = co[ob]; a3 = np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1) / 2
for nm, u_, s_ in (('old body 2K', U['ub'], 2048), ('new body', ub2, 2048)):
    a2 = np.abs((u_[:, 1, 0] - u_[:, 0, 0]) * (u_[:, 2, 1] - u_[:, 0, 1]) - (u_[:, 2, 0] - u_[:, 0, 0]) * (u_[:, 1, 1] - u_[:, 0, 1])) / 2
    d = np.sqrt(a2 / np.maximum(a3, 1e-9)) * s_; print(nm, 'texels/m median', round(float(np.median(d[a3 > 1e-5]))))
ch, oh = U['uh'], U['oh']; P = co[oh]; a3 = np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1) / 2; a2 = np.abs((ch[:, 1, 0] - ch[:, 0, 0]) * (ch[:, 2, 1] - ch[:, 0, 1]) - (ch[:, 2, 0] - ch[:, 0, 0]) * (ch[:, 1, 1] - ch[:, 0, 1])) / 2
print('head texels/m median', round(float(np.median((np.sqrt(a2 / np.maximum(a3, 1e-9)) * 2048)[a3 > 1e-5]))))
