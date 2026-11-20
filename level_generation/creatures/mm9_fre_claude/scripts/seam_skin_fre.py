#!/usr/bin/env python3
"""Fre pass 4 (PeasantF2's hair): between the transplanted hair's rim and the face shell's saw-toothed outline the old hood's faces stay
(build_hair_fre.py keeps the uncovered ones on the face seam) and must read as skin: their texels were Meshy's old hair or never painted
(black). Every old-hood texel, and every face-shell texel the new hair does not cover whose paint is hair-like (dark or red-brown: the
old bob's hairline paint at the jaw sides and nape), takes the mean of the K nearest (3D) clean skin texels (face shell, not covered,
skin-coloured). normal mode: the same texels take a flat normal. Args: <in png> <out png> [normal]   (project folder; work/uv.npz and
work/asm_frozen.npz positions)"""
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from geo4 import raycast
SRC, DST = sys.argv[1:3]; NORMAL = len(sys.argv) > 3 and sys.argv[3] == 'normal'; K = 24
U = np.load('work/uv.npz'); A = np.load('work/asm_frozen.npz'); names = [str(x) for x in U['names']]
co = A['co'][U['orig']]; tri, uv, mat, comp = U['tri'], U['uv'], U['mat'], U['comp']
KH, KS, K2 = names.index('head'), names.index('scarf'), names.index('hair2')
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
POS = np.full((S, S, 3), np.nan); PART = np.full((S, S), -1)
for f in np.where((mat == 1) & np.isin(comp[tri[:, 0]], [KH, KS]))[0]:
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, np.stack([gx.ravel() - q[2, 0], gy.ravel() - q[2, 1]])); bb = np.vstack([l, 1 - l.sum(0)]); ok = (bb >= -1e-4).all(0)
    if ok.any():
        yy, xx = gy.ravel()[ok].astype(int), gx.ravel()[ok].astype(int)
        POS[yy, xx] = (bb[:, ok].T[:, :, None] * co[tri[f]][None]).sum(1); PART[yy, xx] = comp[tri[f, 0]]
ys, xs = np.where(PART >= 0); P = POS[ys, xs]; pt = PART[ys, xs]; col = im[ys, xs]
# covered by the hair cap (ray from the head centre outward hits the cap beyond the texel)
C = np.array([0.0, 0.0, 0.665]); tube = A['hair2_tube'][U['orig']]
capT = tri[(comp[tri] == K2).all(1) & ~tube[tri].any(1)]
d = P - C; r = np.linalg.norm(d, axis=1); u = d / r[:, None]
t = raycast(C + u * 0.6, -u, co, capT); cov = np.isfinite(t) & (0.6 - t > r - 0.001)
hairlike = (col[:, 1] / np.maximum(col[:, 0], 1e-3) < 0.56) | (col.mean(1) < 0.33)
# under the old cap (r43, work/pre_pass4/): Meshy painted hair there on the face shell; uncovered now, it showed as strands and a thin
# dark strip across the temples (r45)
A0 = np.load('work/pre_pass4/asm_frozen.npz'); n0 = [str(x) for x in A0['names']]
oT = A0['tri'][(A0['comp'][A0['tri']] == n0.index('hood4')).all(1)]
t0 = raycast(C + u * 0.6, -u, A0['co'], oT); cov_old = np.isfinite(t0) & (0.6 - t0 > r - 0.002)
hv = np.unique(capT); dh, _ = cKDTree(co[hv]).query(P)      # face-shell texels within 2 cm of the hair only (brows, lashes, lips stay)
if not NORMAL:
    # r46: repainting every texel under the old cap paled the circlet's forehead centre and the temples; only hair paint goes: under
    # the old cap a looser hair test (G/R < 0.62), elsewhere the strict one within 2 cm of the hair
    hair_old = (col[:, 1] / np.maximum(col[:, 0], 1e-3) < 0.55) | (col.mean(1) < 0.36)      # skin G/R 0.62, hair 0.48
    # and the darker ear-plate paint beside the jaw the bob hid (r52: brown blotches in front of the ears): darker than 85 % of the skin
    _sl = np.median(col[(pt == KH) & ~cov & ~cov_old & ~hairlike & (P[:, 2] > 0.52)].mean(1))
    hair_old |= col.mean(1) < 0.85 * _sl
    gold = (col[:, 1] > 0.42) & (col[:, 2] / np.maximum(col[:, 1], 1e-3) < 0.6)      # the circlet's front on the forehead
    skin_src = (pt == KH) & ~cov & ~hairlike & ~gold & ~(cov_old & hair_old) & (P[:, 2] > 0.52)
    fix = (pt == KS) | ((pt == KH) & ~cov & ((cov_old & hair_old) | (hairlike & (dh < 0.02))) & (P[:, 2] > 0.55))
    # one 3D blur over the repainted texels and an 8 mm band of skin round them, so the old hood's teeth and the face shell's teeth
    # take one tone (r46: a zigzag of two skin tones at the temples)
    src = np.where(skin_src)[0]; _, jn = cKDTree(P[src]).query(P[fix], k=K); val = col.copy(); val[fix] = col[src][jn].mean(1)
    db, _ = cKDTree(P[fix]).query(P); band = skin_src & (db < float(__import__('os').environ.get('SEAMBAND', '0.015')))
    zone = fix | band; pool = np.where(zone | skin_src)[0]; _, jz = cKDTree(P[pool]).query(P[zone], k=16)
    sm = val[pool][jz].mean(1)
    # r54: flat mean-colour patches read as separately shaded regions; the band eases from the smoothed tone at the repainted texels to
    # the original paint at its outer edge, and a third of a clean skin texel's fine detail goes back on the repainted ones
    kz = np.clip(1 - db[zone] / float(__import__('os').environ.get('SEAMBAND', '0.015')), 0, 1); kz = np.where(fix[zone], 1.0, kz * kz * (3 - 2 * kz))
    _, jd = cKDTree(P[src]).query(P[zone]); det = col[src][jd] - val[pool][cKDTree(P[pool]).query(P[src][jd], k=16)[1]].mean(1)
    val[zone] = (sm + 0.33 * det * fix[zone][:, None]) * kz[:, None] + col[zone] * (1 - kz[:, None])
    np.save('work/seam_skin_mask.npy', np.c_[ys[zone], xs[zone], fix[zone]])
    out = im.copy(); out[ys[zone], xs[zone]] = val[zone]
else:
    Z = np.load('work/seam_skin_mask.npy'); fix = np.zeros(len(ys), bool)
    out = im.copy(); zf = Z[Z[:, 2] == 1]; out[zf[:, 0], zf[:, 1]] = [0.5, 0.5, 1.0]
    zb = Z[Z[:, 2] == 0]; out[zb[:, 0], zb[:, 1]] = 0.5 * out[zb[:, 0], zb[:, 1]] + 0.5 * np.array([0.5, 0.5, 1.0])
    skin_src = np.zeros(len(ys), bool); cov_old = skin_src
# the old hood's teeth are tiny UV charts: bilinear sampling at their edges read the gutter round them (dark triangle outlines at the
# temples, r51). Their painted texels are grown 3 px into texels that belong to no head-set chart (gutters only: no face texel changes)
from scipy import ndimage as _ni
_any = PART >= 0; _sm = np.zeros((S, S), bool); _sm[ys[pt == KS], xs[pt == KS]] = True
for _ in range(3):
    _g = _ni.binary_dilation(_sm) & ~_any & ~_sm
    if not _g.any(): break
    _acc = np.zeros_like(out); _cnt = np.zeros((S, S))
    for _dy in (-1, 0, 1):
        for _dx in (-1, 0, 1):
            _s2 = np.roll(np.roll(_sm, _dy, 0), _dx, 1); _acc += np.roll(np.roll(out, _dy, 0), _dx, 1) * _s2[..., None]; _cnt += _s2
    out[_g] = _acc[_g] / np.maximum(_cnt[_g], 1)[:, None]; _sm |= _g
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('u1')).save(DST)
print('SEAMSKIN', 'normal' if NORMAL else 'base', 'old-hood texels', int((fix & (pt == KS)).sum()), 'face-shell texels (old cap or hair-like)', int((fix & (pt == KH)).sum()), 'of them under the old cap', int((fix & (pt == KH) & cov_old).sum()),
      'skin sources', int(skin_src.sum()))
