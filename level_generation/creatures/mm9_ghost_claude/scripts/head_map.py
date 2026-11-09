"""Per-texel 3D position, face id and inward flag of the head UV (1K), saved to work/head_map.npz, shared by head paint scripts. Run from the project folder."""
import numpy as np
from scipy import ndimage
S = 1024
d = np.load('work/uv_v1.npz')
idx, uv, co = d['Head_idx'], d['Head_uv'].copy(), d['Head_co']
uv[..., 1] = 1 - uv[..., 1]
P = np.zeros((S, S, 3), np.float32); F = np.full((S, S), -1, np.int32); N = np.zeros((S, S, 3), np.float32)
for f in range(len(idx)):
    t = uv[f] * S
    lo = np.floor(t.min(0)).astype(int) - 1; hi = np.ceil(t.max(0)).astype(int) + 2
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    if xs.size == 0:
        continue
    mt = np.array([t[1] - t[0], t[2] - t[0]]).T
    if abs(np.linalg.det(mt)) < 1e-10:
        continue
    st = (np.stack([xs + 0.5, ys + 0.5], -1) - t[0]) @ np.linalg.inv(mt).T
    ok = (st[..., 0] >= -0.01) & (st[..., 1] >= -0.01) & (st.sum(-1) <= 1.02)
    if not ok.any():
        continue
    w = st[ok]; b0 = 1 - w[:, 0] - w[:, 1]; v = idx[f]
    P[ys[ok], xs[ok]] = b0[:, None] * co[v[0]] + w[:, 0:1] * co[v[1]] + w[:, 1:2] * co[v[2]]
    F[ys[ok], xs[ok]] = f
    n = np.cross(co[v[1]] - co[v[0]], co[v[2]] - co[v[0]]); N[ys[ok], xs[ok]] = n / max(np.linalg.norm(n), 1e-12)
np.savez('work/head_map.npz', P=P, F=F, N=N)
print('MAP', (F >= 0).mean())
