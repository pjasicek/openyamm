"""Mesh npz for build_glb: joined body + weights + UVs (body corners, head corners) + strips.
Args: <joined npz> <weights npz> <out npz> [--uv uv npz with pb ub ph uh] [--tex json]; env NOSTRIPS=1 leaves the strips out (gates on the skin)."""
import sys, json, os
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import strips
J_, W_, OUT = sys.argv[1:4]
args = sys.argv[4:]
uvf = args[args.index('--uv') + 1] if '--uv' in args else None
texj = args[args.index('--tex') + 1] if '--tex' in args else None
D = np.load(J_); co, tri = D['co'], D['tri']; head = D['head']
W = np.load(W_); wj, ww = W['wj'], W['ww']; names = [str(x) for x in W['wnames']]
S = strips.build()
for b in sorted({b for p in S['wb'] for b in p}):
    if b not in names: names.append(b)
ix = {n: i for i, n in enumerate(names)}
matnames = ['Mummy', 'MummyHead']
if uvf:
    U = np.load(uvf)
    tree = cKDTree(co)
    def corners(pos, uv, m):
        d, vid = tree.query(pos); assert d.max() < 1e-4, d.max()
        return vid, uv, np.full(len(vid), m)
    vb, ub, mb = corners(U['pb'], U['ub'], 0); vh, uh, mh = corners(U['ph'], U['uh'], 1)
    vid = np.r_[vb, vh]; uv = np.vstack([ub, uh]); mm = np.r_[mb, mh]
    key = np.c_[vid, mm, np.round(uv, 6)]
    uq, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    co1 = co[uq[:, 0].astype(int)]; wj1 = wj[uq[:, 0].astype(int)]; ww1 = ww[uq[:, 0].astype(int)]; uv1 = uq[:, 2:4]
    tri1 = inv.reshape(-1, 3); mat1 = mm[::3]
else:
    co1, wj1, ww1 = co, wj, ww; uv1 = np.zeros((len(co), 2)); tri1 = tri; mat1 = head.astype(int)
n0 = len(co1)
# head islands too small to matter: out (the 5-triangle one left the audit's only flag)
if uvf:
    hm = np.where(mat1 == 1)[0]
    par = np.arange(len(co1))
    def f_(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    pos_key = {}
    for i in np.unique(tri1[hm]):
        k = tuple(np.round(co1[i], 5))
        if k in pos_key: par[f_(i)] = f_(pos_key[k])
        else: pos_key[k] = i
    for a_, b_, c_ in tri1[hm]:
        par[f_(b_)] = f_(a_); par[f_(c_)] = f_(a_)
    lab = np.array([f_(t[0]) for t in tri1[hm]]); u_, cnt = np.unique(lab, return_counts=True)
    small = set(u_[cnt < 16].tolist()); keep_t = np.ones(len(tri1), bool); keep_t[hm[np.isin(lab, list(small))]] = False
    print('HEAD ISLANDS removed', (~keep_t).sum(), 'tris of', len(hm), sorted(cnt.tolist())[:6]); tri1, mat1 = tri1[keep_t], mat1[keep_t]
if os.environ.get('NOSTRIPS'):
    co2, wj2, ww2, tri2, uv2, mat2 = co1, wj1, ww1, tri1, uv1, mat1
else:
    sco = np.c_[S['co'][:, 0], -S['co'][:, 2], S['co'][:, 1]]         # glTF -> Blender frame, as the body
    swj = np.zeros((len(sco), 4), int); sww = np.zeros((len(sco), 4), 'f4')
    for i, (p, w) in enumerate(zip(S['wb'], S['ww'])):
        swj[i, 0], swj[i, 1] = ix[p[0]], ix[p[1]]; sww[i, 0], sww[i, 1] = w
    # strip UVs: rows of the swatch rectangle the packer placed (corners r[0] r[1] r[2] r[3]: s along, t across)
    r = np.load(uvf)['rect'] if uvf and 'rect' in np.load(uvf).files else np.array([[0, .92], [1, .92], [1, 1], [0, 1.]])
    rows = {0: (0.003, 0.997, 0.68, 0.99)}
    suv = np.zeros((len(sco), 2))
    for si, (u0, u1, v0, v1) in rows.items():
        m = S['sid'] == si
        a_ = u0 + (u1 - u0) * S['uv'][m, 0]; b_ = v0 + (v1 - v0) * S['uv'][m, 1]
        suv[m] = r[0] + np.outer(a_, r[1] - r[0]) + np.outer(b_, r[3] - r[0])
    # thigh and arm strips: lie on the skin, each vertex skinned from the triangle under it, so they bend with the limb (second pass: MM9's rigid spikes read as shards in sit, crouch and death poses)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
    from detached_parts_audit import closest_on_triangles
    from meshlib import section, nearest_loop
    tb = tri[head == 0]; Z = np.array([0, 0, 1.0])
    A, B, C = co[tb[:, 0]], co[tb[:, 1]], co[tb[:, 2]]
    nrm = np.cross(B - A, C - A); nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
    cen = (A + B + C) / 3; tr_ = cKDTree(cen)
    def on_skin(path, dv, w0, row, seed):
        n = len(path)
        path = np.c_[[np.convolve(np.pad(path[:, c], 2, 'edge'), np.ones(5) / 5, 'valid') for c in range(3)]].T
        tan = np.gradient(path, axis=0); tan /= np.linalg.norm(tan, axis=1, keepdims=True)
        bin_ = np.cross(tan, dv); bin_ /= np.linalg.norm(bin_, axis=1, keepdims=True)
        rng = np.random.default_rng(seed)
        wid = w0 * (1 - np.linspace(0, 1, n) ** 2.2) + 0.002; jit = 1 + np.clip(rng.normal(0, .12, (n, 2)), -.3, .3)
        pts = []; uvt = []
        for i in range(n):
            for j, t in enumerate((-1, 0, 1)):
                w_ = wid[i] * (jit[i, 0 if t < 0 else 1] if t else 0)
                pts.append(path[i] + bin_[i] * w_ * t); uvt.append((i / (n - 1), j / 2))
        pts = np.array(pts); uvt = np.array(uvt)
        _, cand = tr_.query(pts, k=24)
        out_p = np.zeros_like(pts); j_ = np.zeros((len(pts), 4), int); w4 = np.zeros((len(pts), 4), 'f4')
        for i in range(len(pts)):
            cs = cand[i]; q, bar = closest_on_triangles(np.repeat(pts[i][None], len(cs), 0), A[cs], B[cs], C[cs])
            k = np.linalg.norm(q - pts[i], axis=1).argmin(); f = cs[k]
            out_p[i] = q[k] + nrm[f] * 0.0055
            acc = {}
            for v_, w_ in zip(tb[f], bar[k]):
                for jj, ww_ in zip(wj[v_], ww[v_]): acc[int(jj)] = acc.get(int(jj), 0) + float(ww_) * float(w_)
            top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; tot = sum(v for _, v in top)
            for c_, (jj, v) in enumerate(top): j_[i, c_] = jj; w4[i, c_] = v / tot
        tt_ = []
        for i in range(n - 1):
            for j in range(2):
                a_, b_, c_, d_ = i * 3 + j, i * 3 + j + 1, (i + 1) * 3 + j + 1, (i + 1) * 3 + j
                tt_ += [(a_, b_, c_), (a_, c_, d_)]
        tt_ = np.array(tt_)
        if np.cross(out_p[tt_[4, 1]] - out_p[tt_[4, 0]], out_p[tt_[4, 2]] - out_p[tt_[4, 0]]) @ dv < 0: tt_ = tt_[:, ::-1]
        u0, u1, v0, v1 = row
        uvs = r[0] + np.outer(u0 + (u1 - u0) * uvt[:, 0], r[1] - r[0]) + np.outer(v0 + (v1 - v0) * uvt[:, 1], r[3] - r[0])
        return out_p, j_, w4, uvs, tt_
    dv = np.array([0.82, 0.57, 0.0]); path = []
    for z in np.linspace(0.90, 0.60, 15):
        L = [l for l in section(co, tb, np.array([0, 0, z]), Z) if l['c'][0] > 0]
        l = max(L, key=lambda q: q['per']); path.append(l['pts'][(l['pts'] @ dv).argmax()])
    rig_ = json.load(open(Path(J_).parent / 'rig.json'))['joints']
    sh, el = np.array(rig_['Bip01 R UpperArm']), np.array(rig_['Bip01 R Forearm'])
    dva = np.array([-0.25, 0.93, -0.29]); dva /= np.linalg.norm(dva)
    arm_path = np.array([sh + (el - sh) * t + dva * 0.07 for t in np.linspace(0.30, 0.95, 11)])
    for (pth, dd, w0, row, seed) in ((np.array(path), dv, 0.038, (0.003, 0.60, 0.02, 0.32), 11), (arm_path, dva, 0.030, (0.003, 0.60, 0.35, 0.65), 5)):
        op, j_, w4, uvs, tt_ = on_skin(pth, dd, w0, row, seed)
        base_ = len(sco)
        sco = np.vstack([sco, op]); swj = np.vstack([swj, j_]); sww = np.vstack([sww, w4]); suv = np.vstack([suv, uvs]); S['tri'] = np.vstack([S['tri'], tt_ + base_])
    co2 = np.vstack([co1, sco]); wj2 = np.vstack([wj1, swj]); ww2 = np.vstack([ww1, sww]); tri2 = np.vstack([tri1, S['tri'] + n0]); uv2 = np.vstack([uv1, suv])
    mat2 = np.r_[mat1, np.zeros(len(S['tri']), int)]
kw = {}
if texj: kw['textures'] = Path(texj).read_text()
np.savez(OUT, co=co2, tri=tri2, wj=wj2, ww=ww2, wnames=np.array(names), mat=mat2, matnames=np.array(matnames), uv=uv2, **kw)
print('ASSEMBLED', len(co2), len(tri2))
