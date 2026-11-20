#!/usr/bin/env python3
"""Skin harmonised in 3D round the face (PF3 second pass, 2026-11-02; orchestrator: a blocky square patch in front of each ear, a hard lighter
block on the chin/jaw, a pixelated block under the chin). Those were paint, not UVs (the ear-plate islands have the face's texel density,
1614 px/m): the ear plates were filled with one flat colour, and the face repaint's window edges (below the chin, at the jaw's sides) met
head_fix's flat neck fill along hard lines.
Here every head-shell skin texel outside the face core (eyes, nose, mouth, the front of the cheeks keep the repaint as it is) takes
  low-pass colour in 3D (Gaussian, SIGMA m, over the skin texels round it, ear plates excluded as sources) + its own fine detail
(UV high-pass at 1.5 px; on the ear plates, which have none, the Meshy paint's fine detail x 0.6), blended in by a weight that is 0 in the
core and rises over 1 cm, so the cheek, ear plate, jaw, chin underside and neck read as one surface.
Args: <tier> <in png (project_face output)> <meshy sym png (detail source)> <out png>   (project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
from scipy.spatial import cKDTree
t, SRC, MESHY, DST = sys.argv[1:5]
SIGMA = 0.006; Z0 = -0.9297
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32); S = im.shape[0]
mz = np.asarray(Image.open(MESHY).convert('RGB').resize((S, S), Image.LANCZOS), np.float32)
kh = names.index('head')
POS = np.full((S, S, 3), np.nan); NOR = np.zeros((S, S, 3)); PRT = np.full((S, S), -1)
ks = names.index('scarf')
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
for fi in np.where((mat == 1) & np.isin(comp[tri[:, 0]], [kh, ks]))[0]:
    q = uv[tri[fi]] * [S, -S] + [0, S]; x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, S)), np.arange(max(y0, 0), min(y1 + 1, S)))
    pts = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (pts - q[2]).T).T; l3 = np.c_[l, 1 - l.sum(1)]; ok = (l3 > -0.01).all(1)
    yy, xx = pts[ok, 1].astype(int), pts[ok, 0].astype(int); POS[yy, xx] = l3[ok] @ co[tri[fi]]; NOR[yy, xx] = fn[fi]; PRT[yy, xx] = comp[tri[fi][0]]
cov = ~np.isnan(POS[..., 0]); x, y, z = (np.nan_to_num(POS[..., k]) for k in range(3)); zs = z - Z0
def ramp(v, a, b): return np.clip((v - a) / (b - a), 0, 1)
hsv = np.asarray(Image.fromarray(np.clip(im, 0, 255).astype('u1')).convert('HSV'), np.float32) / 255
skinc = cov & (hsv[..., 0] * 360 < 32) & (hsv[..., 1] > 0.12) & (hsv[..., 2] > 0.3)
skin = cov & (PRT == kh) & (hsv[..., 0] * 360 < 32) & (hsv[..., 1] > 0.12) & (hsv[..., 2] > 0.3) & (zs < 1.66)
# the clamped ear plates (tweak_pf1.py, |x| > 5.6 cm in the ear zone): flat colour, no sources
# (the hood's faces interleave with the head's at its edge beside the ear: skin-painted hood texels there are plate too)
skinh = skinc & (hsv[..., 1] > 0.30) & (hsv[..., 2] < 0.85)      # clearly skin-painted hood texels only (the linen is warm-tinted too)
skinh = ni.binary_opening(skinh, iterations=1)
hairish = (im @ np.array([0.2126, 0.7152, 0.0722]) < 110) | ((hsv[..., 0] * 360 > 30) & (hsv[..., 1] > 0.35))      # tier B's dark hair, A's blonde: not plate
# pass 3 (user: "a dark brown blotch at each temple where the braid starts"): the temple in front of the ear, below the hood edge, is skin
temple = (np.abs(x) > 0.050) & (zs > 1.580) & (zs < 1.640) & (y > -0.070) & (y < 0.010) & (PRT == kh)
hairish &= ~temple
plate = (((PRT == kh) & (~hairish | (zs < 1.600)) & (zs < 1.615)) | ((PRT == ks) & skinh & ~hairish)) & cov & (np.abs(x) > 0.052) & (zs > 1.525) & (zs < 1.635) & (y > -0.085) & (y < 0.03)
# the face core keeps the repaint: eyes, nose, mouth and the front of the cheeks
core = (1 - ramp(np.abs(x), 0.040, 0.052)) * ramp(zs, 1.512, 1.525) * (1 - ramp(zs, 1.655, 1.665)) * ramp(-y, 0.085, 0.095)
w = np.clip(1 - core, 0, 1) * (cov & (PRT == kh) & (zs < 1.66)).astype(np.float32)
w = np.maximum(w, plate.astype(np.float32))
src = skin & ~hairish & ~ni.binary_dilation(plate, iterations=2)
tgt = cov & (w > 0.01) & ((skin & ~hairish & (zs < 1.625)) | plate | (temple & cov))
sy, sx = np.where(src); ps = POS[sy, sx]; cs = im[sy, sx]
sub = np.arange(len(ps))[::3]; kd = cKDTree(ps[sub])
ty, tx = np.where(tgt); pt = POS[ty, tx]
d, ii = kd.query(pt, k=96, distance_upper_bound=7 * SIGMA)
valid = np.isfinite(d); ii = np.where(valid, ii, 0)
g = np.exp(-0.5 * (np.where(valid, d, 1e9) / SIGMA) ** 2) * valid
lo = (cs[sub][ii] * g[..., None]).sum(1) / np.maximum(g.sum(1), 1e-9)[:, None]
has = g.sum(1) > 1e-6
# the plates take the cheek in front of them (the skin round them behind the jaw is shadowed paint and read as a darker block)
chk = skin & (np.abs(x) > 0.038) & (np.abs(x) < 0.056) & (zs > 1.535) & (zs < 1.625) & (y < -0.035) & ~plate
cy, cx = np.where(chk); pc = POS[cy, cx]; cc = im[cy, cx]; kc = cKDTree(pc)
pl = plate[ty, tx]
dc, ic = kc.query(pt[pl], k=48)
gc = 1.0 / np.maximum(dc, 1e-3) ** 2
lo[pl] = (cc[ic] * gc[..., None]).sum(1) / gc.sum(1)[:, None]; has[pl] = True
# fine detail: own high-pass (plates: Meshy's)
lum = im @ np.array([0.2126, 0.7152, 0.0722]); det = lum - ni.gaussian_filter(lum, 1.5)
lm = mz @ np.array([0.2126, 0.7152, 0.0722]); detm = lm - ni.gaussian_filter(lm, 1.5)
dd = np.where(plate[ty, tx], detm[ty, tx] * 0.6, det[ty, tx])
new = np.clip(lo + dd[:, None], 0, 255)
out = im.copy(); wt = w[ty, tx][:, None] * has[:, None]
out[ty, tx] = im[ty, tx] * (1 - wt) + new * wt
Image.fromarray((np.clip(out, 0, 255) + 0.5).astype('u1')).save(DST)
print('HARMONISE', t, 'targets', len(ty), 'plate', int(plate.sum()), 'sources', len(sub), 'unreached', int((~has).sum()))
