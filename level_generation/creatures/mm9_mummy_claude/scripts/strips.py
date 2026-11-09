"""The three loose strips as two-sided ribbons, authored in MM9's bind space (glTF frame of source/mummy1), on MM9's strip bones.
Library: build() -> dict(co[n,3] glTF, tri, wj names, ww, uv (u along 0..1, v across 0..1), sid)"""
import numpy as np
STRIPS = {
 # name: knots (x,y,z) raw MM9, bone per knot, half width per knot
 'band': dict(k=[(.100, .020, .090), (.215, -.060, .095), (.262, -.132, .097), (.361, -.108, .101), (.441, -.060, .114), (.500, .130, .140), (.513, .345, .149)],
              b=['XstripRoot', 'Bone04', 'Bone05', 'Bone06', 'Bone07', 'Bone08', 'XstripTip'], w=[.040, .032, .030, .032, .032, .030, .020], n=36, seed=3),
}


def catmull(P, t):
    P = np.asarray(P, float); n = len(P)
    i = np.clip(np.floor(t * (n - 1)).astype(int), 0, n - 2); u = t * (n - 1) - i
    p0 = P[np.maximum(i - 1, 0)]; p1 = P[i]; p2 = P[i + 1]; p3 = P[np.minimum(i + 2, n - 1)]
    u = u[:, None]
    return 0.5 * (2 * p1 + (p2 - p0) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2 + (3 * p1 - p0 - 3 * p2 + p3) * u ** 3)


def refine_band(n=13):
    """13 knots along MM9's band, each with its own bone, so rotations change little from knot to knot (second pass: 7 knots folded the ribbon)."""
    S = STRIPS['band']; K = np.array(S['k'], float)
    if len(K) == n: return
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(K, axis=0), axis=1))]; L /= L[-1]
    t = np.linspace(0, 1, n); par = np.interp(t, L, np.linspace(0, 1, len(K)))
    S['w'] = np.interp(par, np.linspace(0, 1, len(K)), S['w']).tolist()
    S['k'] = [tuple(x) for x in catmull(K, par)]
    S['b'] = ['XstripRoot'] + [f'Xband{i:02d}' for i in range(1, n - 1)] + ['XstripTip']


def build():
    refine_band()
    co, tri, wb, ww, uv, sid = [], [], [], [], [], []
    base = 0; ofs = 0.0
    for si, (name, S) in enumerate(STRIPS.items()):
        rng = np.random.default_rng(S['seed'])
        n = S['n']; K = np.array(S['k']); m = len(K)
        L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(K, axis=0), axis=1))]; L /= L[-1]
        # arc parameter: knots at their true length
        tt = np.linspace(0, 1, n + 1)
        kpar = np.interp(tt, L, np.linspace(0, 1, m))
        C = catmull(K, kpar)
        Tg = np.gradient(C, axis=0); Tg /= np.linalg.norm(Tg, axis=1, keepdims=True)
        Nz = np.array([0, 0, 1.0]); Bn = np.cross(Nz, Tg); Bn /= np.linalg.norm(Bn, axis=1, keepdims=True); Nn = np.cross(Tg, Bn)
        wid = np.interp(kpar, np.linspace(0, 1, m), S['w'])
        ja = rng.normal(0, .12, (n + 1, 2)); ja = np.clip(ja, -.3, .3); ja[0] = 0
        Lpos = C + Bn * (wid * (1 + ja[:, 0]))[:, None]; Rpos = C - Bn * (wid * (1 + ja[:, 1]))[:, None]
        # slight curl across
        mid = C + Nn * (wid * 0.18)[:, None]
        ring = np.stack([Lpos, mid, Rpos], 1)             # (n+1, 3, 3)
        for side, off in ((0, 0.0015), (1, -0.0015)):
            v = ring + (Nn[:, None, :] * off)
            nv = v.reshape(-1, 3)
            co.append(nv)
            for i in range(n):
                for j in range(2):
                    a, b, c, d = base + i * 3 + j, base + i * 3 + j + 1, base + (i + 1) * 3 + j + 1, base + (i + 1) * 3 + j
                    q = [(a, b, c), (a, c, d)] if side == 0 else [(a, c, b), (a, d, c)]
                    tri += q
            for i in range(n + 1):
                u = tt[i]
                # weights between the two neighbouring knots' bones
                kp = kpar[i] * (m - 1); k0 = int(min(np.floor(kp), m - 2)); f = kp - k0
                for j in range(3):
                    wb.append((S['b'][k0], S['b'][k0 + 1])); ww.append((1 - f, f))
                    uv.append((u, j / 2)); sid.append(si)
            base += (n + 1) * 3
    return dict(co=np.vstack(co), tri=np.array(tri), wb=wb, ww=np.array(ww), uv=np.array(uv), sid=np.array(sid))


refine_band_done = False
