#!/usr/bin/env python3
"""Igrid's head colour from the 4K head retexture (textures/wo_head_raw.png, 1K), fixes by 3D position (work/texel_pos_head.npy):
1. BRAIDS: Meshy painted the thin braid cords the hood's brown. Their texels take a warm grey ramp by Meshy's own luminance (weave detail
   kept), as the Codex head masters and MM9's skin draw them.
2. CIRCLET GEM (the small piece on the forehead, its own faces): gold with a dark-red cabochon centre (it was painted brown skin).
3. CIRCLET BAND: a thin gold band across the forehead at the gem's height, fading out toward the temples under the hood's edge.
4. COIF: Meshy painted the head shell above the face (scalp, temples inside the hood) the hood's maroon, so the face read as a mask in a
   maroon cap (and as a grey skull cap when painted grey hair, review r9). Those texels (hood-maroon by colour, outside the nose, mouth and
   eye zones) take a soft white linen coif by Meshy's luminance (its folds) with a faint weave, shaded deeper inside the hood.
5. NET: the wrinkles came out as a net of dark thin lines over the cheeks and forehead; thin dark lines on the face skin (below their
   5 px grey closing by more than DROP) are pulled NETK of the way to the closing (wrinkles stay, softer; no vein net).
6. NOSTRILS: the darkest texels under the nose lifted halfway toward the nose-side skin; LIPS: saturation x LIPSAT (no lipstick).
Args: <in png> <out png>  (project folder)"""
import sys, os
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
P = np.load('work/texel_pos_head.npy'); part = np.load('work/texel_part_head.npy')
D = np.load('work/asm_f.npz'); names = [str(x) for x in D['names']]; co, tri, comp = D['co'], D['tri'], D['comp']
H, B = names.index('head'), names.index('braids')
LUMA = np.array([0.2126, 0.7152, 0.0722])
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
lum = im @ LUMA
out = im.copy()
# 1. braids
bm = part == B
lb = lum[bm]; lo, hi = np.percentile(lb, 2), np.percentile(lb, 98); t = np.clip((lb - lo) / max(hi - lo, 1e-4), 0, 1)
dark, light = np.array([78, 74, 70]) / 255, np.array([186, 180, 172]) / 255
# a three-strand plait: lobes every PL m down the braid, the two halves (left / right of the braid's axis) offset by half a lobe
PL = 0.011; BP = P[bm]; bx = np.where(BP[:, 0] > 0, 1, -1)
axc = {}
for sx in (1, -1):
    q = BP[bx == sx]; axc[sx] = (np.median(q[:, 0]), np.median(q[:, 1]))
side = np.array([np.sign(p[0] - axc[sx][0]) if True else 1 for p, sx in zip(BP, bx)])
ph = (BP[:, 2] / PL + 0.5 * (side > 0)) % 1.0
lobe = np.sin(np.pi * ph) ** 0.7
tt = np.clip(0.35 + 0.35 * lobe + 0.35 * (t - 0.5), 0, 1)
out[bm] = dark + (light - dark) * tt[:, None]
# 2. the gem: head texels whose nearest head vertex belongs to the small forehead piece
hv = np.where(comp == H)[0]; ht = tri[np.isin(tri[:, 0], hv)]
par = {v: v for v in hv}
def f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a, b, c in ht: r = f(a); par[f(b)] = r; par[f(c)] = r
root = np.array([f(v) for v in hv]); u, cnt = np.unique(root, return_counts=True)
gem_roots = [r for r, n in zip(u, cnt) if n < 200 and abs(co[r, 0]) < 0.03 and co[r, 2] > 0.57 and co[r, 1] < -0.3]
gemv = np.isin(root, gem_roots); print('GEM verts', int(gemv.sum()))
hm = part == H
# texels ON the gem's faces (uv-npz faces whose original vertices are gem vertices)
U_ = np.load('work/uv.npz'); fidx = np.load('work/texel_face_head.npy'); gset = np.zeros(len(co), bool); gset[hv[gemv]] = True
gemface = gset[U_['orig'][U_['tri']]].all(1); gm = hm & (fidx >= 0) & gemface[np.maximum(fidx, 0)]
gc = co[hv[gemv]].mean(0); dg = np.linalg.norm(P[gm] - gc, axis=1)
gold = np.array([184, 142, 58]) / 255; ruby = np.array([128, 18, 26]) / 255
lg = lum[gm]; sh = np.clip(0.75 + 0.6 * (lg - lg.mean()), 0.55, 1.2)[:, None]
cen = 1 - ss(dg, 0.0035, 0.0050)
out[gm] = (gold * (1 - cen)[:, None] + ruby * cen[:, None]) * sh
# 3. the band: face texels in front (y < -0.27) at the gem's height, |x| fading out by 6.5 cm
fm = hm & ~gm
Q = P[fm]; zc = gc[2]
band = (1 - ss(np.abs(Q[:, 2] - zc), 0.0016, 0.0026)) * (1 - ss(np.abs(Q[:, 0]), 0.055, 0.068)) * (Q[:, 1] < -0.27)
lf = lum[fm]; shb = np.clip(0.85 + 0.8 * (lf - np.median(lf[band > 0.5])) if (band > 0.5).any() else 1.0, 0.6, 1.2)
col = gold[None, :] * (shb[:, None] if np.ndim(shb) else shb)
out[fm] = out[fm] * (1 - band[:, None]) + col * band[:, None]
# 4. hair: hood-maroon texels of the head shell (not nose, mouth or eyes)
from PIL import Image as _I
hsv = np.asarray(_I.fromarray((np.clip(im, 0, 1) * 255).astype('u1')).convert('HSV'), np.float32) / 255
hh, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
X, Y, Z = (np.nan_to_num(P[..., i]) for i in range(3))
EC = D['eye_c']
eyez = np.minimum(np.hypot(np.hypot(X - EC[0], Y - EC[1]), Z - EC[2]), np.hypot(np.hypot(X + EC[0], Y - EC[1]), Z - EC[2])) < 0.022
nosez = (np.abs(X) < 0.03) & (Z > 0.47) & (Z < 0.54) & (Y < -0.29)
maroon = hm & ~gm & ((hh < 14) | (hh > 335)) & (sat > 0.33) & (val < 0.47) & ~eyez & ~nosez
maroon = ni.binary_opening(maroon, iterations=1) & hm
hw = np.clip(ni.gaussian_filter(maroon.astype(np.float32), 2.0) * 1.2, 0, 1) * hm * ~gm
lh = lum[maroon]; lo2, hi2 = np.percentile(lh, 2), np.percentile(lh, 98)
th_ = np.clip((lum - lo2) / max(hi2 - lo2, 1e-4), 0, 1)
# (coordinator review r9: the grey hair read as a bald grey skull cap; MM9 shows a pale veil under the hood) -> a soft white linen coif:
# cream linen by Meshy's own luminance (its hood folds become the coif's folds, contrast x COIFK), a faint linen weave, in the hood's shade
# deeper inside the hood
COIFK = float(os.environ.get('COIFK', '1.8'))
hdark, hlight = np.array([142, 132, 116]) / 255, np.array([226, 218, 200]) / 255
tc = np.clip(0.5 + (th_ - 0.5) * COIFK, 0, 1)
yy_, xx_ = np.mgrid[0:S, 0:S]; weave = 0.02 * (np.sin(xx_ * 1.9) * np.sin(yy_ * 1.9))
hcol = hdark + (hlight - hdark) * tc[..., None] ** 0.9 + weave[..., None]
shade = 1 - 0.30 * ss(Y + 0.30, 0.0, 0.07)
hcol = hcol * np.clip(shade, 0.6, 1)[..., None]
out = out * (1 - hw[..., None]) + hcol * hw[..., None]
# 4b. forehead between the brows and the band: Meshy painted a maroon swag (its circlet) there; reddish / dark texels take the local skin
fz = hm & ~gm & (np.abs(X) < 0.065) & (Z > 0.566) & (Z < zc - 0.0016) & (Y < -0.27)
fhs = np.asarray(_I.fromarray((np.clip(out, 0, 1) * 255).astype('u1')).convert('HSV'), np.float32) / 255
okskin = fz & (fhs[..., 0] * 360 > 10) & (fhs[..., 0] * 360 < 32) & (fhs[..., 2] > 0.55)
bad = fz & ~okskin
fill = None
for sg in (10.0, 5.0, 2.5):
    wv = ni.gaussian_filter(okskin.astype(np.float32), sg)
    f2 = np.stack([ni.gaussian_filter(out[..., i] * okskin, sg) for i in range(3)], -1) / np.maximum(wv, 1e-6)[..., None]
    fill = f2 if fill is None else np.where((wv > 0.2)[..., None], f2, fill)
bw = np.clip(ni.gaussian_filter(bad.astype(np.float32), 1.0) * 1.5, 0, 1) * fz
detail = (out @ LUMA) - ni.gaussian_filter(out @ LUMA, 3)
out = out * (1 - bw[..., None]) + (fill + 0.4 * detail[..., None]) * bw[..., None]
print('FOREHEAD swag texels', int(bad.sum()))
# 5. net: thin dark lines on the face skin
import os
DROP, NETK = float(os.environ.get('DROP', '0.022')), float(os.environ.get('NETK', '0.9'))     # review r9: the 0.035 / 0.65 net still read as painted lines
L2 = out @ LUMA; clo = ni.grey_closing(L2, size=(7, 7)); cimg = np.stack([ni.grey_closing(out[..., i], size=(7, 7)) for i in range(3)], -1)
eyez2 = np.minimum(np.hypot(np.hypot(X - EC[0], Y - EC[1]), Z - EC[2]), np.hypot(np.hypot(X + EC[0], Y - EC[1]), Z - EC[2])) < float(os.environ.get('EYEKEEP', '0.0135'))
skin = hm & ~gm & ~maroon & (hh > 5) & (hh < 32) & (val > 0.40) & (Y < -0.2) & ~eyez2      # review r9: the orange rings round the eyes too (only the ball and lid rims kept)
line = skin & ((clo - L2) > DROP)
lw = np.clip(ni.gaussian_filter(line.astype(np.float32), 0.7) * 1.5, 0, 1) * skin * NETK
out = out * (1 - lw[..., None]) + cimg * lw[..., None]
# 6. nostrils and lips
nz = hm & (np.abs(X) < 0.027) & (Z > 0.494) & (Z < 0.52) & (Y < -0.305)
if nz.any():
    ref = np.median(out[hm & (np.abs(X) > 0.02) & (np.abs(X) < 0.03) & (Z > 0.50) & (Z < 0.52) & (Y < -0.3)], 0)
    Ln = out[nz] @ LUMA; dk = np.clip((np.median(Ln) - Ln) / 0.15, 0, 1)[:, None] * 0.7
    out[nz] = out[nz] * (1 - dk) + ref * dk
# the nose underside and the dark dimple under the lower lip: lifted toward the upper-lip skin
und = hm & (np.abs(X) < 0.022) & (Y < -0.30) & (((Z > 0.497) & (Z < 0.513)) | ((Z > 0.466) & (Z < 0.478) & (np.abs(X) < 0.016)))
if und.any():
    ref2 = np.median(out[hm & (np.abs(X) > 0.006) & (np.abs(X) < 0.02) & (Z > 0.494) & (Z < 0.498) & (Y < -0.3)], 0)
    Lu = out[und] @ LUMA; Lr = ref2 @ LUMA; k2 = np.clip((Lr - Lu) / 0.25, 0, 1)[:, None] * 0.8
    out[und] = out[und] * (1 - k2) + ref2 * (Lu / max(Lr, 1e-3))[:, None] ** 0.3 * k2
# pale texels low on the neck (inside the collar): the hood's dark cloth
nk = hm & (Z < 0.425) & (sat < 0.3) & (val > 0.5)
nk = ni.binary_dilation(nk, iterations=2) & hm & (Z < 0.43)
out[nk] = np.array([60, 33, 34]) / 255 * (0.8 + 0.4 * ((out[nk] @ LUMA) - 0.5))[:, None]
print('UNDER-NOSE/LIP texels', int(und.sum()), 'NECK pale', int(nk.sum()))
LIPSAT = float(os.environ.get('LIPSAT', '0.8'))
lipz = hm & (np.abs(X) < 0.03) & (np.abs(Z - 0.4855) < 0.009) & (Y < -0.29) & ((hh < 10) | (hh > 340)) & (sat > 0.35)
g_ = (out[lipz] @ LUMA)[:, None]; out[lipz] = g_ + (out[lipz] - g_) * LIPSAT
print('HAIR texels', int(maroon.sum()), 'NET texels', int(line.sum()), 'NOSTRIL', int(nz.sum()), 'LIP', int(lipz.sum()))
print('BRAID texels', int(bm.sum()), 'GEM texels', int(gm.sum()), 'BAND texels', int((band > 0.5).sum()))
# keep the gutters padded from inside the charts
cov = part >= 0; idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True)
out = out[idx[0], idx[1]]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('u1')).save(DST); print('HEADFIX', DST)
