#!/usr/bin/env python3
"""Igrid's head colour from the SECOND 4K head retexture (2026-11-04, meshy/wo_head_v2 from references_head_v2/: the first paint's face
needed more than two patch passes), fixes by 3D position (work/texel_pos_head.npy). As head_fix_wo.py, with these changes:
- 4 COIF v2: the head shell above the circlet and at the temples (Meshy painted it as a dark-brown fringe of hair: the hood is not in the
  head upload) takes the Codex v2 front view's linen coif, projected straight from the front (x by the eye spacing, z anchored on the
  circlet gem; image u grows with -x, the true-handed mirror), where the projected pixel is coif-white and the texel faces the front;
  elsewhere (back and top under the hood, or where the Codex view shows hood) the procedural linen of head_fix_wo.py step 4.
- 4b: every dark fringe texel on the forehead below the circlet band takes the local skin (was: maroon swag only).
- 5 NET off by default (NETK 0: the second paint's wrinkles are soft creases); 6 nostril / under-lip lifts off by default (LIFT 0).
Original step list:
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
# v2: the dark fringe Meshy painted over the scalp, above the circlet (and at the temples, |x| > SIDEX, down to the jaw)
SIDEX = float(os.environ.get('SIDEX', '0.058'))
maroon = hm & ~gm & (val < 0.5) & ~eyez & ~nosez & ((Z > zc - 0.004) | ((np.abs(X) > SIDEX) & (Z > 0.45)))
maroon = ni.binary_opening(maroon, iterations=1) & hm
hw = np.clip(ni.gaussian_filter(maroon.astype(np.float32), 2.0) * 1.2, 0, 1) * hm * ~gm
lh = lum[maroon]; lo2, hi2 = np.percentile(lh, 2), np.percentile(lh, 98)
th_ = np.clip((lum - lo2) / max(hi2 - lo2, 1e-4), 0, 1)
# (coordinator review r9: the grey hair read as a bald grey skull cap; MM9 shows a pale veil under the hood) -> a soft white linen coif:
# cream linen by Meshy's own luminance (its hood folds become the coif's folds, contrast x COIFK), a faint linen weave, in the hood's shade
# deeper inside the hood
COIFK = float(os.environ.get('COIFK', '1.0'))
hdark, hlight = np.array([142, 132, 116]) / 255, np.array([226, 218, 200]) / 255
tc = np.clip(0.5 + (ni.gaussian_filter(th_, 3.0) - 0.5) * COIFK, 0, 1)     # v2: blurred (Meshy's fringe strands and seams)
yy_, xx_ = np.mgrid[0:S, 0:S]; weave = 0.02 * (np.sin(xx_ * 1.9) * np.sin(yy_ * 1.9))
hcol = hdark + (hlight - hdark) * tc[..., None] ** 0.9 + weave[..., None]
shade = 1 - 0.30 * ss(Y + 0.30, 0.0, 0.07)
hcol = hcol * np.clip(shade, 0.6, 1)[..., None]
# v2: the Codex front view's coif projected straight from the front where it shows white linen and the texel faces the front
cdx = np.asarray(Image.open('references_head_v2/01_front.png').convert('RGBA'), np.float32) / 255
CU, CV, CA = (float(os.environ.get(k, d)) for k, d in (('CU', '633.3'), ('CV', '366.1'), ('CA', '3052')))
# height map (shared with 4b): uniform scale CA anchored on the eyes up to the brow line ZB, then stretched so the circlet gem meets the
# Codex circlet (the Codex forehead is lower than ours), uniform again above the gem
ZE, ZB = float(EC[2]), float(os.environ.get('ZB', '0.567')); VE = float(os.environ.get('VE', '471.3'))
vb = VE - CA * (ZB - ZE)
vz = np.where(Z <= ZB, VE - CA * (Z - ZE), np.where(Z <= zc, vb + (CV - vb) * np.clip((Z - ZB) / max(zc - ZB, 1e-4), 0, 1), CV - CA * (Z - zc)))
uu = np.clip(CU - CA * X, 0, cdx.shape[1] - 1).astype(int); vv = np.clip(vz, 0, cdx.shape[0] - 1).astype(int)
cp = cdx[vv, uu]; cph = np.asarray(Image.fromarray((cp[..., :3] * 255).astype('u1')).convert('HSV'), np.float32) / 255
cw = np.clip((0.30 - cph[..., 1]) / 0.12, 0, 1) * np.clip((cph[..., 2] - 0.5) / 0.15, 0, 1) * (cp[..., 3] > 0.8) * (1 - ss(Y, -0.25, -0.20))
cw = ni.gaussian_filter(cw, 1.5)
hcol = hcol * (1 - cw[..., None]) + cp[..., :3] * cw[..., None]
print('COIF v2 projected texels', int(((cw > 0.5) & (hw > 0.5)).sum()), 'of', int((hw > 0.5).sum()))
out = out * (1 - hw[..., None]) + hcol * hw[..., None]
# 4b (v2). FOREHEAD from the Codex v2 front view: Meshy's dark fringe covers the forehead down to the brows (no brows painted). Dark
# texels in front below the circlet band take the Codex forehead, brows and creases, projected from the front with a piecewise height
# map (uniform scale CA anchored on the eyes up to the brow line ZB, then stretched so the circlet gem meets the Codex circlet: the
# Codex forehead is lower than ours) and brought to Meshy's skin tone (ratio of medians on the upper cheeks).
uu2 = np.clip(CU - CA * X, 0, cdx.shape[1] - 1).astype(int); vv2 = np.clip(vz, 0, cdx.shape[0] - 1).astype(int)
cf = cdx[vv2, uu2][..., :3]
fz = hm & ~gm & (np.abs(X) < 0.075) & (Z > 0.548) & ~maroon & (Z < zc - 0.0016) & (Y < -0.25) & ~eyez
bad = fz & (val < 0.55)
bad = ni.binary_closing(bad, iterations=2) & fz
ck = hm & (Y < -0.27) & (Z > 0.52) & (Z < 0.545) & (np.abs(X) > 0.035) & (np.abs(X) < 0.05) & (val > 0.55)
gainf = np.median(out[ck], 0) / np.maximum(np.median(cf[ck], 0), 1e-3)
bw = np.clip(ni.gaussian_filter(bad.astype(np.float32), 2.5) * 1.4, 0, 1) * fz * (1 - ss(np.abs(X), 0.058, 0.075))
cg = np.clip(cf * gainf, 0, 1); gy = (cg @ LUMA)[..., None]; cg = gy + (cg - gy) * float(os.environ.get('FHSAT', '0.8'))
out = out * (1 - bw[..., None]) + cg * bw[..., None]
print('FOREHEAD fringe texels', int(bad.sum()), 'gain', np.round(gainf, 3))
# v2: the circlet band again on top (steps 4 and 4b painted over it)
out[fm] = out[fm] * (1 - band[:, None]) + col * band[:, None]
# 5. net: thin dark lines on the face skin
import os
DROP, NETK = float(os.environ.get('DROP', '0.022')), float(os.environ.get('NETK', '0.0'))     # review r9: the 0.035 / 0.65 net still read as painted lines
L2 = out @ LUMA; clo = ni.grey_closing(L2, size=(7, 7)); cimg = np.stack([ni.grey_closing(out[..., i], size=(7, 7)) for i in range(3)], -1)
eyez2 = np.minimum(np.hypot(np.hypot(X - EC[0], Y - EC[1]), Z - EC[2]), np.hypot(np.hypot(X + EC[0], Y - EC[1]), Z - EC[2])) < float(os.environ.get('EYEKEEP', '0.0135'))
skin = hm & ~gm & ~maroon & (hh > 5) & (hh < 32) & (val > 0.40) & (Y < -0.2) & ~eyez2      # review r9: the orange rings round the eyes too (only the ball and lid rims kept)
line = skin & ((clo - L2) > DROP)
lw = np.clip(ni.gaussian_filter(line.astype(np.float32), 0.7) * 1.5, 0, 1) * skin * NETK
out = out * (1 - lw[..., None]) + cimg * lw[..., None]
# 6. nostrils and lips
nz = hm & (np.abs(X) < 0.027) & (Z > 0.494) & (Z < 0.52) & (Y < -0.305)
if nz.any() and os.environ.get('LIFT', '0') == '1':
    ref = np.median(out[hm & (np.abs(X) > 0.02) & (np.abs(X) < 0.03) & (Z > 0.50) & (Z < 0.52) & (Y < -0.3)], 0)
    Ln = out[nz] @ LUMA; dk = np.clip((np.median(Ln) - Ln) / 0.15, 0, 1)[:, None] * 0.7
    out[nz] = out[nz] * (1 - dk) + ref * dk
# the nose underside and the dark dimple under the lower lip: lifted toward the upper-lip skin
und = hm & (np.abs(X) < 0.022) & (Y < -0.30) & (((Z > 0.497) & (Z < 0.513)) | ((Z > 0.466) & (Z < 0.478) & (np.abs(X) < 0.016)))
if und.any() and os.environ.get('LIFT', '0') == '1':
    ref2 = np.median(out[hm & (np.abs(X) > 0.006) & (np.abs(X) < 0.02) & (Z > 0.494) & (Z < 0.498) & (Y < -0.3)], 0)
    Lu = out[und] @ LUMA; Lr = ref2 @ LUMA; k2 = np.clip((Lr - Lu) / 0.25, 0, 1)[:, None] * 0.8
    out[und] = out[und] * (1 - k2) + ref2 * (Lu / max(Lr, 1e-3))[:, None] ** 0.3 * k2
# 6b (v2). SHADE: the upper lip under the nose renders as a dark moustache-like band and the nose underside as dark nostrils in the
# viewer's top light (shading of the rebuilt mouth patch's rim, face geometry final), though the paint there is clean: brighten the paint
# in those bands by UL (smooth falloff), skin hue kept.
UL = float(os.environ.get('UL', '1.04'))
if UL != 1.0:
    def ss2(x, a, b):
        tt = np.clip((x - a) / (b - a), 0, 1); return tt * tt * (3 - 2 * tt)
    ULZ0, ULZ1 = float(os.environ.get('ULZ0', '0.489')), float(os.environ.get('ULZ1', '0.507'))
    wl = hm & (Y < -0.29)
    wz = ss2(Z, ULZ0 - 0.002, ULZ0 + 0.002) * (1 - ss2(Z, ULZ1 - 0.002, ULZ1 + 0.002)) * (1 - ss2(np.abs(X), 0.020, 0.028)) * wl
    out = np.clip(out * (1 + (UL - 1) * wz[..., None]), 0, 1)
    print('SHADE upper lip texels', int((wz > 0.5).sum()), 'x', UL)
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
# ---- Orchestrator pre-screen of r15 (2026-11-04), paint only, no geometry moved ----
# texel normals (nearest head vertex of the final head mesh, npz frame: y back, z up)
_U = np.load('work/uv_tw.npz'); _co, _tri, _mat = _U['co'], _U['tri'], _U['mat']
_t = _tri[_mat == 1]; _fn = np.cross(_co[_t[:, 1]] - _co[_t[:, 0]], _co[_t[:, 2]] - _co[_t[:, 0]]); _vn = np.zeros_like(_co)
for _c in range(3): np.add.at(_vn, _t[:, _c], _fn)
_key = np.round(_co, 5); _, _inv = np.unique(_key, axis=0, return_inverse=True); _inv = _inv.ravel(); _Ns = np.zeros((_inv.max() + 1, 3)); np.add.at(_Ns, _inv, _vn); _vn = _Ns[_inv]
_vn /= np.maximum(np.linalg.norm(_vn, axis=1, keepdims=True), 1e-12); _hv = np.unique(_t)
_m = hm & np.isfinite(P[..., 0]); _, _j = cKDTree(_co[_hv]).query(np.nan_to_num(P[_m]))
TN = np.zeros(P.shape, np.float32); TN[_m] = _vn[_hv][_j]
# 7. AGE: the Codex v2 front view's creases (crow's feet, nasolabial folds, forehead and cheek lines, the jaw's sag) carried onto the
#    face skin as a multiplicative detail (Codex luminance / its 7 px blur, after a 1.2 px prefilter), projected from the front with a
#    landmark height map (eyes 0.550 -> v 471, nose base 0.503 -> 617, mouth 0.4855 -> 647, uniform CA below), weighted by how much the
#    texel faces the front; skin warmed toward MM9's ruddy tone and the cheeks flushed from the Codex view's own low-frequency redness.
AGEK = float(os.environ.get('AGEK', '0.75'))
if AGEK > 0:
    cl = (cdx[..., :3] @ LUMA); cl1 = ni.gaussian_filter(cl, 1.2); cdet = cl1 / np.maximum(ni.gaussian_filter(cl1, 7.0), 1e-3)
    ZA = np.array([0.40, 0.4855, 0.503, 0.550, 0.567]); VA = np.array([647 + CA * 0.0855, 647, 617, VE, VE - CA * 0.017])
    vf = np.interp(Z, ZA, VA); vf = np.where(Z > ZB, vz, vf)
    uf = np.clip(CU - CA * X, 0, cdx.shape[1] - 1).astype(int); vf = np.clip(vf, 0, cdx.shape[0] - 1).astype(int)
    eyed = np.minimum(np.hypot(np.hypot(X - EC[0], Y - EC[1]), Z - EC[2]), np.hypot(np.hypot(X + EC[0], Y - EC[1]), Z - EC[2]))
    face7 = hm & ~gm & ~maroon & (eyed > 0.0125) & (Y < -0.2) & (Z > 0.43) & (Z < zc - 0.002) & (cdx[vf, uf, 3] > 0.8)
    face7 &= ~(nosez & (TN[..., 2] < -0.5))                                  # not the nose underside (step 8)
    front = np.clip((-TN[..., 1] - 0.35) / 0.35, 0, 1)                       # facing the front (-y)
    lipel = np.clip(1 - np.hypot(X / 0.029, (Z - 0.4855) / 0.0080), 0, 1)     # the lips keep their own paint (no second lip line)
    ww = ni.gaussian_filter(face7.astype(np.float32), 1.0) * face7 * front * np.clip((eyed - 0.0125) / 0.004, 0, 1)
    wa = ww * (1 - np.clip(lipel * 2.5, 0, 1) * 0.85)
    d7 = np.clip(cdet[vf, uf], 0.6, 1.25)
    out = out * (1 + (d7[..., None] ** AGEK - 1) * wa[..., None])
    # warmth: a ruddier skin, the cheeks flushed where the Codex view's skin is redder than its median
    cr = ni.gaussian_filter(cdx[..., 0] - 0.5 * (cdx[..., 1] + cdx[..., 2]), 12)[vf, uf]; crm = float(np.median(cr[face7]))
    flush = ni.gaussian_filter(np.clip((cr - crm) / 0.12, 0, 1) * ww, 4) * 0.6
    warm = np.array([float(x) for x in os.environ.get('WARM', '1.05,0.97,0.91').split(',')])
    out = out * (1 + (warm - 1) * ww[..., None]) + flush[..., None] * np.array([0.05, -0.02, -0.03])
    out = np.clip(out, 0, 1)
    print('AGE texels', int((wa > 0.5).sum()), 'k', AGEK)
# 8. NOSE: from below and in front the nose tip and nostrils read as a dark brown blot. The paint there is clean skin (unlit raster
#    work/hv2/raster_low.png): it is the hemisphere light on the large downward-facing nose underside of a head tilted forward. The paint
#    of downward-facing nose texels is lifted (up to NOSEK, by -n_z) to read as skin; the real nostril openings (small pits beside the
#    columella) keep a soft shadow.
NOSEK = float(os.environ.get('NOSEK', '1.06'))
if NOSEK > 1:
    nzone = hm & (np.abs(X) < 0.022) & (Z > 0.495) & (Z < 0.522) & (Y < -0.30)
    down = np.clip((-TN[..., 2] - 0.25) / 0.5, 0, 1) * nzone
    pit = np.exp(-(((np.abs(X) - 0.0065) / 0.0028) ** 2 + ((Z - 0.5045) / 0.0018) ** 2)) * (Y < -0.325)
    lift = 1 + (NOSEK - 1) * ni.gaussian_filter(down, 1.5) * (1 - 0.8 * pit)
    ref = np.median(out[hm & (np.abs(X) > 0.012) & (np.abs(X) < 0.022) & (Z > 0.51) & (Z < 0.52) & (Y < -0.3)], 0)
    Lo = out @ LUMA; Lr = float(ref @ LUMA)
    sk = ref * (Lo / max(Lr, 1e-3))[..., None] ** 0.5                       # skin tone, the paint's own shading kept softly
    wn = np.clip(ni.gaussian_filter(down, 1.5), 0, 1)[..., None] * 0.6
    out = np.clip((out * (1 - wn) + sk * wn) * lift[..., None], 0, 1)
    print('NOSE underside texels', int((down > 0.5).sum()), 'lift', NOSEK)
    # small soft shadows in the real nostril openings (NOSTRILK), now that the tilted underside normals light the tip
    out = out * (1 - float(os.environ.get('NOSTRILK', '0.38')) * ni.gaussian_filter(pit * nzone, 1.0))[..., None]
# 9. COIF EDGE: the face skin met the coif at the temples and cheeks in a hard line (front, 3/4). By 3D distance to the edge (texel
#    positions, so UV seams do not matter): the coif darkens toward the face over EDGEW m (the cloth turning in and tucking behind the
#    cheek, a soft fold shadow), and the skin within EDGES m of the coif takes the coif's cast shade.
EDGEW, EDGES = float(os.environ.get('EDGEW', '0.018')), float(os.environ.get('EDGES', '0.006'))
if EDGEW > 0:
    cm = (hw > 0.5) & hm & (Y < -0.12) & (np.abs(X) > 0.035)
    skin9 = hm & (hw < 0.2) & ~gm & (Y < -0.12) & (np.abs(X) > 0.03) & (Z < zc - 0.003) & (Z > 0.43)
    ki = np.argwhere(skin9); kc = np.argwhere(cm)
    ds, _ = cKDTree(P[skin9][::3]).query(P[cm]); dc, _ = cKDTree(P[cm][::3]).query(P[skin9])
    shc = 1 - 0.55 * np.clip(1 - ds / EDGEW, 0, 1) ** 1.6
    shs = 1 - 0.35 * np.clip(1 - dc / EDGES, 0, 1) ** 1.5
    sh = np.ones(S * S if False else hm.shape, np.float32); sh[kc[:, 0], kc[:, 1]] = shc; sh[ki[:, 0], ki[:, 1]] = shs
    sh = ni.gaussian_filter(sh, 0.8)
    out = out * np.where(hm, sh, 1.0)[..., None]
    print('COIF EDGE coif texels', int((shc < 0.97).sum()), 'skin texels', int((shs < 0.97).sum()))
# keep the gutters padded from inside the charts
cov = part >= 0; idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True)
out = out[idx[0], idx[1]]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('u1')).save(DST); print('HEADFIX', DST)
