#!/usr/bin/env python3
"""Job 8 (2026-11-04): re-paint two regions whose texels no longer fit their faces, by 3D donor lookup (each target texel's 3D point is
moved by an offset, projected onto the nearest donor face, and that face's texel is copied), in every body map: base colour, normal,
ORM, tier region mask and material classes.
- hem: bodice_fix_pf4.py brought the side peplum's notches down to the tips' line; the faces of that band kept F1's sawtooth paint (dark
  teeth where the skirt showed between the tips). Target: dress faces at the sides (|x| > 7.5 cm) with any vertex below the hem line
  + 3.5 cm; donor: the dress 4 cm higher (faces above that line).
- wrist: the forearm skin inside the bell sleeve (f 0.28 .. 0.88 of the forearm) was painted olive by Meshy under the tube (a green blot
  seen up the sleeve at the wrist). Target: those arm faces; donor: the same point moved along the forearm to f = 0.94 (bare wrist skin
  below the bell), onto arm/hand faces with f >= 0.90.
Reads the final geometry work/uv_tex2.npz. Idempotent (donors are never targets). Usage (project folder): region_paint_pf4.py hem wrist"""
import sys, json, os
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
D = np.load('work/uv_tex2.npz'); co, tri, uv, comp, mat, inner = D['co'], D['tri'], D['uv'], D['comp'], D['mat'], D['inner']
names = [str(x) for x in D['names']]
body = (mat == 0)
fc = comp[tri[:, 0]]
J = {k: np.array(v) for k, v in json.load(open('work/rig.json'))['mm9'].items()}
jobs = []
if 'hem' in sys.argv[1:]:
    kd = names.index('dress'); fz = co[tri][:, :, 2]; fx = np.abs(co[tri][:, :, 0]).mean(1)
    zline = 0.093 + 0.035
    tgt = (fc == kd) & body & (fx > 0.075) & (fz.min(1) < zline) & (co[tri][:, :, 2].mean(1) < 0.2)
    don = (fc == kd) & body & ~inner & (fz.min(1) >= zline) & (fz.max(1) < 0.30)
    jobs.append(('hem', tgt, don, lambda p: p + np.array([0, 0, 0.04])))
if 'wrist' in sys.argv[1:]:
    ka = names.index('hands')
    tg = np.zeros(len(tri), bool); dn = np.zeros(len(tri), bool); offs = {}
    cen = co[tri].mean(1)
    for sgn in (1, -1):
        E_ = J['FHP R Forearm'] * [sgn, 1, 1]; W_ = J['FHP R Hand'] * [sgn, 1, 1]; Lf = np.linalg.norm(W_ - E_); af = (W_ - E_) / Lf
        f = (cen - E_) @ af / Lf; on = (fc == ka) & body & (cen[:, 0] * sgn > 0.10)
        tg |= on & (f > 0.28) & (f < 0.88); dn |= on & (f >= 0.90) & (f < 1.02)
        offs[sgn] = (E_, af, Lf)
    def off(p):
        out = p.copy()
        for sgn, (E_, af, Lf) in offs.items():
            m = p[:, 0] * sgn > 0
            f = (p[m] - E_) @ af / Lf; out[m] = p[m] + np.outer(0.94 - f, af) * Lf
        return out
    jobs.append(('wrist', tg, dn, off))
MAPS = ['textures/pf_body_tone.png', 'textures/pf_body_normal_plain.png', 'textures/pf_body_orm.png', 'textures/pf_body_mask.png',
        'textures/pf_material_classes.png']
def texels(f, W, H):
    p = np.c_[uv[tri[f]][:, 0] * W, (1 - uv[tri[f]][:, 1]) * H]
    x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(x0 - 1, x1 + 2), np.arange(y0 - 1, y1 + 2)); q = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    T = np.c_[p[1] - p[0], p[2] - p[0]]
    if abs(np.linalg.det(T)) < 1e-12: return None, None
    b = np.linalg.solve(T, (q - p[0]).T).T; l = np.c_[1 - b.sum(1), b]
    m = (l > -0.08).all(1); return np.floor(q[m]).astype(int), l[m]
def closest_on_tri(p, a, b, c):
    """barycentric of the closest point on triangle abc to p (vectorised over rows)"""
    ab, ac, ap = b - a, c - a, p - a
    n = np.cross(ab, ac); nn = (n * n).sum(1, keepdims=True); nn = np.maximum(nn, 1e-20)
    pp = p - ((ap * n).sum(1, keepdims=True) / nn) * n
    v0, v1, v2 = ab, ac, pp - a
    d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-20)
    v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den; u = 1 - v - w
    L = np.clip(np.c_[u, v, w], 0, None); L /= np.maximum(L.sum(1, keepdims=True), 1e-12)
    q = L[:, :1] * a + L[:, 1:2] * b + L[:, 2:] * c
    return L, np.linalg.norm(q - p, axis=1)
imgs = {pth: Image.open(pth) for pth in MAPS}
arrs = {pth: np.asarray(im).astype(np.float32).copy() for pth, im in imgs.items()}
srcs = {pth: a.copy() for pth, a in arrs.items()}
for name, tgt, don, off in jobs:
    dfs = np.where(don)[0]; dc = co[tri[dfs]].mean(1); kd_ = cKDTree(dc)
    tfs = set(np.where(tgt)[0].tolist())
    for pth in MAPS:
        im, src = arrs[pth], srcs[pth]; H, W = im.shape[:2]; nearest = pth.endswith('classes.png')
        own = np.zeros((H, W), bool)                 # texels inside non-target body faces are never written
        for f in np.where(body)[0]:
            if f in tfs: continue
            q, l = texels(f, W, H)
            if q is None: continue
            k = (l > 0).all(1); q = q[k]; q = q[(q[:, 0] >= 0) & (q[:, 0] < W) & (q[:, 1] >= 0) & (q[:, 1] < H)]; own[q[:, 1], q[:, 0]] = True
        n = 0
        for f in tfs:
            q, l = texels(f, W, H)
            if q is None: continue
            ok = (q[:, 0] >= 0) & (q[:, 0] < W) & (q[:, 1] >= 0) & (q[:, 1] < H); q, l = q[ok], l[ok]
            ok = (l > 0).all(1) | ~own[q[:, 1], q[:, 0]]; q, l = q[ok], l[ok]
            if not len(q): continue
            P = off(l @ co[tri[f]])
            _, cand = kd_.query(P, k=6)
            best_L = None; best_d = np.full(len(P), np.inf); best_f = np.zeros(len(P), int)
            for kk in range(cand.shape[1]):
                ff = dfs[cand[:, kk]]; t3 = co[tri[ff]]
                L, d = closest_on_tri(P, t3[:, 0], t3[:, 1], t3[:, 2])
                bt = d < best_d
                if best_L is None: best_L = L.copy()
                best_L[bt] = L[bt]; best_d[bt] = d[bt]; best_f[bt] = ff[bt]
            suv = (best_L[:, :, None] * uv[tri[best_f]]).sum(1)
            sx = suv[:, 0] * W; sy = (1 - suv[:, 1]) * H
            if nearest:
                im[q[:, 1], q[:, 0]] = src[np.clip(sy.astype(int), 0, H - 1), np.clip(sx.astype(int), 0, W - 1)]
            else:
                x = np.clip(sx - 0.5, 0, W - 1.001); y = np.clip(sy - 0.5, 0, H - 1.001); x0 = x.astype(int); y0 = y.astype(int)
                fx = (x - x0); fy = (y - y0)
                if im.ndim == 3: fx = fx[:, None]; fy = fy[:, None]
                im[q[:, 1], q[:, 0]] = (src[y0, x0] * (1 - fx) * (1 - fy) + src[y0, x0 + 1] * fx * (1 - fy) + src[y0 + 1, x0] * (1 - fx) * fy
                                        + src[y0 + 1, x0 + 1] * fx * fy)
            n += 1
        print('REGION PAINT', name, pth, 'faces', n, 'donors', len(dfs))
for pth in MAPS:
    out = Image.fromarray(np.clip(arrs[pth] + 0.5, 0, 255).astype('u1'), imgs[pth].mode); tmp = pth + '.tmp.png'; out.save(tmp); os.replace(tmp, pth)
