#!/usr/bin/env python3
"""Job 8 (2026-11-04): the sleeve tube's upper bands (inside F1's short sleeve down to ~0.2 of the forearm) were wound inward when Meshy
painted them (sleeve_rings_pf4.py), so their paint is a smooth, dark smear without the weave, ending in a visible line at mid-forearm.
Their texels are re-painted from the tube's clean bands lower down in every body map that carries them: base colour, normal, ORM, tier
region mask and material classes.
v2 (coordinator, user's back view 13_back_elbows_r40.png: no rectangular patch edges): the first version copied each target triangle from
its twin triangle in a donor band (barycentric), which carried the donor's UV density into a band of another size (a coarser weave and a
horizontal step at the junction). Now each target texel is located on the tube by arc length s along the ring centres and the column
angle theta, and samples the donor bands at the same theta and the arc length mirrored about the junction ring (s_d = s_j + fold(s_j - s),
folded again at the donor's far end): the weave keeps its physical scale and runs on continuously across the junction.
Texels inside other faces are never written; run pad_set_pf4.py afterwards on the RGB maps (seam gutters).
Usage (project folder): sleeve_paint_pf4.py stats | apply [last target band, default 5] [donor rings, default 6:10]"""
import sys, os
import numpy as np
from PIL import Image
D = np.load('work/uv_tex2.npz'); A = np.load('work/asm_frozen.npz')
tri, uv, orig, comp, mat, inner = D['tri'], D['uv'], D['orig'], D['comp'], D['mat'], D['inner']
names = [str(x) for x in D['names']]; ks = names.index('sleeve4')
MS, NR = 12, 13
aq = np.where(A['comp'] == ks)[0]; aco = A['co']
base = {s: aq[A['f4_side'][aq] == s].min() for s in (1, -1)}
# arc length of the ring centres per side (rest pose)
S_ring = {}
for s in (1, -1):
    cen = np.array([aco[base[s] + i * MS: base[s] + (i + 1) * MS].mean(0) for i in range(NR)])
    S_ring[s] = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cen, axis=0), axis=1))]
def rc(v):
    s = int(np.sign(A['f4_side'][v])); k = v - base[s]; return s, k // MS, k % MS
faces = []          # (face, side, lower ring, s of verts, theta of verts)
for f in np.where((comp[tri[:, 0]] == ks) & ~inner & (mat == 0))[0]:
    r = [rc(v) for v in orig[tri[f]]]
    if any(x[1] >= NR for x in r): continue
    s = r[0][0]; i0 = min(x[1] for x in r)
    if max(x[1] for x in r) != i0 + 1: continue
    th = np.array([x[2] for x in r], float)
    if th.max() - th.min() > MS / 2: th[th < MS / 2] += MS
    faces.append((f, s, i0, np.array([S_ring[s][x[1]] for x in r]), th))
def pix(f, W, H):
    p = np.c_[uv[tri[f]][:, 0] * W, (1 - uv[tri[f]][:, 1]) * H]
    x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(x0 - 1, x1 + 2), np.arange(y0 - 1, y1 + 2)); q = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    T = np.c_[p[1] - p[0], p[2] - p[0]]
    if abs(np.linalg.det(T)) < 1e-12: return None, None
    b = np.linalg.solve(T, (q - p[0]).T).T; l = np.c_[1 - b.sum(1), b]
    m = (l > -0.08).all(1)
    return np.floor(q[m]).astype(int), l[m]
mode = sys.argv[1]
if mode == 'stats':
    im = np.asarray(Image.open('textures/pf_body_tone.png').convert('RGB'), np.float32); H, W = im.shape[:2]
    from scipy.ndimage import uniform_filter
    hp = im.mean(2) - uniform_filter(im.mean(2), 9)
    for s in (1, -1):
        for i in range(NR - 1):
            P = []
            for f, s_, i_, _, _ in faces:
                if s_ != s or i_ != i: continue
                q, l = pix(f, W, H)
                if q is None: continue
                q = q[(l > 0).all(1)]; q = q[(q[:, 0] >= 0) & (q[:, 0] < W) & (q[:, 1] >= 0) & (q[:, 1] < H)]; P.append(q)
            P = np.vstack(P); c = im[P[:, 1], P[:, 0]]
            print('side', s, 'band', i, 'texels', len(P), 'mean', c.mean(0).round(1), 'weave std', round(float(hp[P[:, 1], P[:, 0]].std()), 2))
    sys.exit()
last = int(sys.argv[2]) if len(sys.argv) > 2 else 5
d0, d1 = (int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else '6:10').split(':'))
tgt = [x for x in faces if x[2] <= last]
don = [x for x in faces if d0 <= x[2] < d1]
tgt_set = {x[0] for x in tgt}
# donor lookup grid: (side, ring, column) -> the quad's two faces with their (s, theta) triangles
grid = {}
for f, s, i0, sv, th in don:
    j = int(np.floor(th.min() + 1e-6)) % MS
    grid.setdefault((s, i0, j), []).append((f, sv, th))
def bary2(P, T):
    a, b, c = T; v0, v1 = b - a, c - a; v2 = P - a
    den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < 1e-15: return None
    w1 = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den; w2 = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
    return np.c_[1 - w1 - w2, w1, w2]
MAPS = ['textures/pf_body_tone.png', 'textures/pf_body_normal_plain.png', 'textures/pf_body_orm.png', 'textures/pf_body_mask.png',
        'textures/pf_material_classes.png']
def owners(W, H):
    own = np.zeros((H, W), bool)
    for f in np.where(mat == 0)[0]:
        if f in tgt_set: continue
        q, l = pix(f, W, H)
        if q is None: continue
        q = q[(l > 0).all(1)]; q = q[(q[:, 0] >= 0) & (q[:, 0] < W) & (q[:, 1] >= 0) & (q[:, 1] < H)]; own[q[:, 1], q[:, 0]] = True
    return own
OWN = {}
for path in MAPS:
    img = Image.open(path); im = np.asarray(img).astype(np.float32).copy(); H, W = im.shape[:2]; src = im.copy()
    if (W, H) not in OWN: OWN[(W, H)] = owners(W, H)
    own = OWN[(W, H)]; nearest = path.endswith('classes.png'); n = miss = 0
    for f, s, i0, sv, th in tgt:
        q, l = pix(f, W, H)
        if q is None: continue
        ok = (q[:, 0] >= 0) & (q[:, 0] < W) & (q[:, 1] >= 0) & (q[:, 1] < H); q, l = q[ok], l[ok]
        ok = (l > 0).all(1) | ~own[q[:, 1], q[:, 0]]; q, l = q[ok], l[ok]
        st = l @ sv; tt = (l @ th) % MS
        sj = S_ring[s][d0]; Ld = S_ring[s][d1] - sj
        dd = np.abs(sj - st) % (2 * Ld); dd = np.where(dd > Ld, 2 * Ld - dd, dd); sd = np.clip(sj + dd, sj + 1e-6, sj + Ld - 1e-6)
        ring = np.clip(np.searchsorted(S_ring[s], sd, side='right') - 1, d0, d1 - 1); col = np.floor(tt).astype(int) % MS
        out_uv = np.full((len(q), 2), np.nan)
        for key in set(zip(ring.tolist(), col.tolist())):
            m = (ring == key[0]) & (col == key[1])
            cand = grid.get((s, key[0], key[1]), [])
            P = np.c_[sd[m], tt[m]]; best = np.full(m.sum(), -np.inf); buv = np.zeros((m.sum(), 2))
            for fd, svd, thd in cand:
                thd2 = thd - (key[1] - (key[1] % MS)) ; T = np.c_[svd, thd2]
                P2 = P.copy(); P2[:, 1] += np.where(P2[:, 1] < thd2.min() - 1e-6, MS, 0)
                L = bary2(P2, T)
                if L is None: continue
                sc = L.min(1); bt = sc > best
                best[bt] = sc[bt]; buv[bt] = (np.clip(L[bt], 0, None) / np.clip(L[bt], 0, None).sum(1, keepdims=True)) @ uv[tri[fd]]
            out_uv[np.where(m)[0]] = np.where(np.isfinite(best)[:, None], buv, np.nan)
        good = np.isfinite(out_uv[:, 0]); miss += int((~good).sum()); q, out_uv = q[good], out_uv[good]
        sx = out_uv[:, 0] * W; sy = (1 - out_uv[:, 1]) * H
        if nearest:
            im[q[:, 1], q[:, 0]] = src[np.clip(sy.astype(int), 0, H - 1), np.clip(sx.astype(int), 0, W - 1)]
        else:
            x = np.clip(sx - 0.5, 0, W - 1.001); y = np.clip(sy - 0.5, 0, H - 1.001); x0 = x.astype(int); y0 = y.astype(int)
            fx = x - x0; fy = y - y0
            if im.ndim == 3: fx = fx[:, None]; fy = fy[:, None]
            im[q[:, 1], q[:, 0]] = (src[y0, x0] * (1 - fx) * (1 - fy) + src[y0, x0 + 1] * fx * (1 - fy) + src[y0 + 1, x0] * (1 - fx) * fy
                                    + src[y0 + 1, x0 + 1] * fx * fy)
        n += 1
    out = Image.fromarray(np.clip(im + 0.5, 0, 255).astype('u1'), img.mode); tmp = path + '.tmp.png'; out.save(tmp); os.replace(tmp, path)
    print('SLEEVE PAINT v2', path, 'faces', n, 'texels without a donor', miss)
