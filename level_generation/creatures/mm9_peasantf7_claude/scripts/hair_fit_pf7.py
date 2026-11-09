"""Fit the hair shell's outer surface to MM9 PeasantF7's own hair silhouette (user rule: hair not bigger, not smaller than MM9's).
Per (height, azimuth round the head axis) bin: delta = MM9's outer radius (its head+hair mesh, work/mm9.npz) - our hair's outer radius,
clipped to [-CLIP_IN, CLIP_OUT], bins where MM9's radius is the shoulders or the face are left alone; smoothed over the bins. Each hair vertex
moves radially by delta x its outer-ness in its bin (inner side on the skull stays), then the displacement is Laplacian-smoothed on the hair.
Args: <asm npz> <out npz> [clip_out 0.025] [clip_in 0.010]"""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.ndimage import gaussian_filter
IN, OUT = sys.argv[1:3]; CO_ = float(sys.argv[3]) if len(sys.argv) > 3 else 0.025; CI_ = float(sys.argv[4]) if len(sys.argv) > 4 else 0.010
D = dict(np.load(IN)); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
M = np.load('work/mm9.npz'); P9, T9 = M['co'], M['tri']
def samp(P, T):
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]; out = [P]
    for u, v in [(i / 6, j / 6) for i in range(7) for j in range(7 - i) if 0 < i + j]: out.append(a + u * (b - a) + v * (c - a))
    return np.vstack(out)
hk = names.index('hair'); hv = np.where(comp == hk)[0]; ht = tri[comp[tri[:, 0]] == hk]
S9 = samp(P9, T9); Sh = samp(co, ht)
ZB = np.arange(0.36, 0.86, 0.02); PB = np.arange(-180, 180, 15.0)
def pol(S): return S[:, 2], np.degrees(np.arctan2(S[:, 0], S[:, 1])), np.hypot(S[:, 0], S[:, 1])
def grid(S, f):
    z, p, r = pol(S); G = np.full((len(ZB), len(PB)), np.nan)
    zi = np.clip(np.round((z - ZB[0]) / 0.02).astype(int), -1, len(ZB)); pi = np.round((p - PB[0]) / 15.0).astype(int) % len(PB)
    ok = (zi >= 0) & (zi < len(ZB))
    for a, b, rr in zip(zi[ok], pi[ok], r[ok]):
        G[a, b] = rr if np.isnan(G[a, b]) else f(G[a, b], rr)
    return G
R9 = grid(S9, max); Rh = grid(Sh, max); Rl = grid(Sh, min)
dl = R9 - Rh
ph = np.abs(PB)[None, :] + 0 * ZB[:, None]; zz = ZB[:, None] + 0 * PB[None, :]
bad = np.isnan(dl) | ((ph > 40) & (ph < 140) & (zz < 0.50)) | (ph > 155)
dl = np.clip(np.where(bad, 0, dl), -CI_, CO_)
dl = gaussian_filter(dl, (1.0, 0.8), mode=('nearest', 'wrap'))
z, p, r = co[hv, 2], np.degrees(np.arctan2(co[hv, 0], co[hv, 1])), np.hypot(co[hv, 0], co[hv, 1])
fz = np.clip((z - ZB[0]) / 0.02, 0, len(ZB) - 1.001); fp = ((p - PB[0]) / 15.0) % len(PB)
z0, p0 = fz.astype(int), fp.astype(int); tz, tp = fz - z0, fp - p0; p1 = (p0 + 1) % len(PB)
def bil(G): return (G[z0, p0] * (1 - tz) * (1 - tp) + G[z0 + 1, p0] * tz * (1 - tp) + G[z0, p1] * (1 - tz) * tp + G[z0 + 1, p1] * tz * tp)
d = bil(dl); lo = np.nan_to_num(bil(np.where(np.isnan(Rl), 0, Rl))); hi = np.nan_to_num(bil(np.where(np.isnan(Rh), 0, Rh)))
w = np.clip((r - lo) / np.maximum(hi - lo, 0.005), 0, 1) ** 1.5
disp = np.zeros_like(co); dirv = np.c_[co[hv, 0], co[hv, 1], 0 * r] / np.maximum(r, 1e-6)[:, None]; disp[hv] = dirv * (d * w)[:, None]
e = np.vstack([ht[:, [0, 1]], ht[:, [1, 2]], ht[:, [2, 0]]])
A = coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(co), len(co))).tocsr(); A.data[:] = 1
deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
for _ in range(6): disp[hv] = 0.5 * disp[hv] + 0.5 * ((A @ disp) / deg[:, None])[hv]
co = co + disp; D['co'] = co
print('HAIRFIT moved verts', int((np.linalg.norm(disp, axis=1) > 1e-4).sum()), 'max cm', round(float(np.linalg.norm(disp, axis=1).max() * 100), 2),
      'back z0.5-0.7 mean cm', round(float(dl[(ZB >= 0.5) & (ZB <= 0.7)][:, np.abs(PB) < 40].mean() * 100), 2))
np.savez(OUT, **D)
