"""Cut the long body charts of the paint layout (a chart of about 1 m caps the atlas scale) for the runtime repack: each island longer than E in UV is cut across its long axis, repeatedly.
Writes work/pack_in2.npz. The paint needs no redo: runtime colour is sampled from the 4K paint through the old UVs."""
import numpy as np
D = np.load('work/pack_in.npz'); uv, vert = D['uv'].astype(np.float64), D['vert'].astype(np.int64)
E = 0.33
def islands(uv, vert):
    keys = np.c_[vert.reshape(-1), np.round(uv.reshape(-1, 2), 6)]
    _, inv = np.unique(keys, axis=0, return_inverse=True); inv = inv.ravel().reshape(-1, 3)
    p = np.arange(inv.max() + 1)
    def f(x):
        while p[x] != x:
            p[x] = p[p[x]]; x = p[x]
        return x
    for a, b, c in inv:
        ra, rb = f(a), f(b); p[rb] = ra; rc = f(c); p[rc] = ra
    return np.array([f(a) for a in inv[:, 0]])
nextv = vert.max() + 1
for it in range(5):
    lab = islands(uv, vert); changed = 0
    for l in np.unique(lab):
        tris = np.where(lab == l)[0]; q = uv[tris].reshape(-1, 2); c = q.mean(0)
        u, s, vt = np.linalg.svd(q - c, full_matrices=False); ax = vt[0]; t = (q - c) @ ax
        ext = np.ptp(t)
        if ext <= E: continue
        cen = (uv[tris].mean(1) - c) @ ax
        # cut at the point nearest the middle where the band is narrowest
        best, bw = 0.0, 1e9
        for x in np.linspace(t.min() * .35, t.max() * .35, 15):
            m = np.abs(t - x) < 0.01
            if m.sum() < 3: continue
            w = np.ptp((q[m] - c) @ vt[1])
            if w < bw: bw, best = w, x
        side = tris[cen > best]
        # new vertex ids on one side, so the two sides are separate islands
        vs = np.unique(vert[side]); remap = {v: nextv + i for i, v in enumerate(vs)}; nextv += len(vs)
        vert[side] = np.vectorize(remap.get)(vert[side]); changed += 1
    print('pass', it, 'islands', len(np.unique(lab)), 'cut', changed)
    if not changed: break
np.savez('work/pack_in2.npz', uv=uv.astype('f4'), vert=vert)
