#!/usr/bin/env python3
"""Head paint fixes per tier, after head_tiers_wy.py (face pre-screen r2, 2026-11-02):
1. Nose underside (geometry tip y -0.133 at z 0.645, underside z 0.633-0.646): Meshy painted an irregular dark nostril smudge; it becomes
   the skin of the nose's sides with two soft nostrils at the geometry's recesses (x +-6.5 mm, z 0.638), as PF1's project_face_pf1.py.
2. Throat: texels below z 0.52 carrying the gown's red/plum (Meshy painted Morgan's gown into the bottom of the head set; on Verdandi it
   showed as a red patch) take the neck skin.
3. Gutters: every chart's gutter re-padded from its nearest inside texel (sym_paint and the recolours left the old paint in the gutters:
   thin grey lines along the UV seams across the cheeks).
Args: <in png> <out png>  (project folder; work/texel_pos_head.npy from texel_pos.py <size> 1)"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]; TIER = sys.argv[3] if len(sys.argv) > 3 else 'y'
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
P = np.load('work/texel_pos_head.npy'); ok = ~np.isnan(P[..., 0]); P = np.nan_to_num(P); x, y, z = P[..., 0], P[..., 1], P[..., 2]
def lin(a): return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def unlin(a): return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.maximum(a, 0) ** (1 / 2.4) - 0.055)
L = lin(im)
hsv = np.asarray(Image.fromarray((im * 255).astype('u1')).convert('HSV'), np.float32) / 255; h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
skin = ok & (h > 8) & (h < 35) & (s > 0.18) & (s < 0.6) & (v > 0.45)
# 1. nose (r15, user: "nose has no nostrils or alae", "blobs on a flat nose"): Meshy's own nose paint is kept (it was painted onto this
#    geometry: tip, wings and nostrils where the mesh has them); only its darkest nostril smudge is lifted halfway toward a soft shadow
#    of the nose-side skin. (r5-r14 painted the whole nose base as flat skin with two dots: that erased the wings.)
side = ok & (v > 0.45) & (np.abs(x) > 0.008) & (np.abs(x) < 0.024) & (z > 0.648) & (z < 0.672) & (y < -0.10)
sk = np.median(L[side], 0)
zone = ok & (np.abs(x) < 0.021) & (z > 0.628) & (z < 0.650) & (y < -0.108)
lum = L @ np.array([0.2126, 0.7152, 0.0722]); skl = float(sk @ np.array([0.2126, 0.7152, 0.0722]))
dark = zone & (lum < 0.45 * skl)
wd = np.clip((0.45 * skl - lum) / (0.25 * skl), 0, 1) * zone
L = L * (1 - 0.5 * wd[..., None]) + (sk * 0.42)[None, None, :] * (0.5 * wd[..., None])
print('NOSE kept (Meshy), dark nostril texels lifted', int(dark.sum()))
# 2. throat
red = ok & (((h > 300) | (h < 12)) & (s > 0.35) & (v < 0.75)) & (z < 0.52)
neck = ok & skin & (z > 0.50) & (z < 0.56) & (y < -0.04)
if neck.sum() > 20 and red.sum():
    nk = np.median(L[neck], 0); wr = np.clip(ni.gaussian_filter(ni.binary_dilation(red, iterations=1).astype(np.float32), 0.8) * 1.5, 0, 1) * ok
    L = L * (1 - wr[..., None]) + nk * (0.75 + 0.25 * lum[..., None] / max(float(nk @ [0.2126, 0.7152, 0.0722]), 1e-3)).clip(0.6, 1.2) * wr[..., None]
print('THROAT red texels', int(red.sum()))
# 2b. the whole throat between the hood's sides (|x| < 4.5 cm, under the chin, front) is neck skin: Verdandi's paint carried a green
# wedge (the hood colour) and a red band there; MM9 shows skin down to the pearl choker (separate geometry)
thr = ok & (np.abs(x) < 0.045) & (z > 0.465) & (z < 0.548) & (y < -0.03)
if neck.sum() > 20:
    nk = np.median(L[neck], 0); lum = L @ np.array([0.2126, 0.7152, 0.0722]); fine = (lum / np.maximum(ni.gaussian_filter(lum, 4), 1e-4)).clip(0.85, 1.15)
    shade = np.clip((z - 0.465) / 0.08, 0, 1) * 0.25 + 0.75                       # a little darker toward the collar
    wt = np.clip(ni.gaussian_filter(thr.astype(np.float32), 1.5) * 1.3, 0, 1) * ok
    L = L * (1 - wt[..., None]) + (nk * (fine * shade)[..., None]) * wt[..., None]
    print('THROAT skin texels', int(thr.sum()))
# 2c. forehead: a white pearl drop painted under the circlet where the mesh has no pearl (Verdandi)
hsv2 = np.asarray(Image.fromarray((unlin(np.clip(L, 0, 1)) * 255).astype('u1')).convert('HSV'), np.float32) / 255
pearl = ok & (np.abs(x) < 0.018) & (z > 0.708) & (z < 0.732) & (y < -0.08) & (hsv2[..., 1] < 0.34) & (hsv2[..., 2] > 0.7)
pearl = ni.binary_dilation(pearl, iterations=3) & ok & (np.abs(x) < 0.022) & (z > 0.706) & (z < 0.734) & (y < -0.08) & (hsv2[..., 1] < 0.45)
fore = ok & (np.abs(x) < 0.03) & (z > 0.700) & (z < 0.710) & (y < -0.08)
if pearl.sum() and fore.sum() > 20:
    fk = np.median(L[fore], 0); wp = np.clip(ni.gaussian_filter(pearl.astype(np.float32), 1.0) * 1.5, 0, 1)
    L = L * (1 - wp[..., None]) + fk * wp[..., None]
print('PEARL texels', int(pearl.sum()))
# 2d. eyelids on the eyeball spheres (rigid on Head: no eye bones): MM9's women look out under relaxed lids, the Meshy eyes stared
# (Verdandi: wide round eyes where MM9 smiles). Upper lid from UP x r above the ball centre, lower lid from LO x r below, a dark lash
# line at the upper edge; the lid colour is the skin just above the socket.
EC = np.array([0.0226, -0.0943, 0.6803]); ER = 0.0143
UP, LO = (0.40, -0.62) if TIER == 'y' else (0.24, -0.30)      # r5: Verdandi's smiling squint, Morgan calm
lidsk = ok & (np.abs(np.abs(x) - EC[0]) < 0.01) & (z > EC[2] + 0.016) & (z < EC[2] + 0.022) & (y < -0.09)
if lidsk.sum() > 10:
    lk = np.median(L[lidsk], 0) * 0.82
    for sx in (1, -1):
        c = EC * [sx, 1, 1]; d = np.sqrt(((P - c) ** 2).sum(-1)); ball = ok & (d < ER + 0.0008) & (y < c[1] + 0.004)
        u = (z - c[2]) / ER
        up = np.clip((u - UP) / 0.10, 0, 1); lo = np.clip((LO - u) / 0.10, 0, 1); lash = np.exp(-((u - UP) / 0.07) ** 2)
        w = np.maximum(up, lo) * ball; wl = lash * ball * 0.75
        L = np.where(ball[..., None], L * (1 - w[..., None]) + lk * w[..., None], L)
        L = np.where(ball[..., None], L * (1 - wl[..., None]) + np.array([0.02, 0.012, 0.01]) * wl[..., None], L)
    print('LIDS', TIER, 'upper', UP, 'lower', LO, 'lid skin', np.round(unlin(lk) * 255).tolist())
# 2e. lips (r15, user: "mouth needs work": r10-r14 painted a thin line on a flat face, ignoring the modelled lips): Meshy's own lip paint is
#    kept on Meshy's lips (the shape follows the geometry); only its colour is toned: its red texels take one tier colour (Morgan soft rose,
#    Verdandi natural warm rose; MM9 shows clearly rose lips) by luminance ratio, so the lip shape and its shading stay.
LIPC = {'y': (196, 96, 92), 'm': (184, 102, 90)}[TIER]
lc = lin(np.array(LIPC) / 255.0); lcl = float(lc @ np.array([0.2126, 0.7152, 0.0722]))
hs0 = np.asarray(Image.fromarray((unlin(np.clip(L, 0, 1)) * 255).astype('u1')).convert('HSV'), np.float32) / 255
mz = ok & (np.abs(x) < 0.03) & (z > 0.604) & (z < 0.636) & (y < -0.08)
redl = mz & ((hs0[..., 0] * 360 > 335) | (hs0[..., 0] * 360 < 12)) & (hs0[..., 1] > 0.40)      # skin is hue ~15-22
redl = ni.binary_closing(redl, iterations=2) & mz
lum = L @ np.array([0.2126, 0.7152, 0.0722]); ml = float(np.median(lum[redl])) if redl.sum() else 1.0
ratio = np.clip(lum / ml, 0.55, 1.3)
wl_ = np.clip(ni.gaussian_filter(redl.astype(np.float32), 1.0) * 1.4, 0, 1) * mz
L = L * (1 - wl_[..., None]) + (lc[None, None, :] * ratio[..., None]) * wl_[..., None]
print('LIPS toned', TIER, int(redl.sum()), 'texels ->', LIPC)
# 2f. Morgan: under the tiara and at the temples the hair read as a flat tan cap (the earlier dark-hair recolour left one flat colour there).
# The side and top hair zone (behind the face, not hood, not the circlet) takes her front strands' blonde with strands combed back
# (a fine 1D noise across the meridians), a little darker toward the back.
if TIER == 'y':
    hs = np.asarray(Image.fromarray((unlin(np.clip(L, 0, 1)) * 255).astype('u1')).convert('HSV'), np.float32) / 255
    hh, ss2, vv2 = hs[..., 0] * 360, hs[..., 1], hs[..., 2]
    circ = (hh > 28) & (hh < 60) & (ss2 > 0.60) & (vv2 > 0.62)
    hoodb = (hh > 195) & (hh < 260) & (ss2 > 0.25)
    facez = ((y < -0.07) & (np.abs(x) < 0.062) & (z < 0.745)) | ((y < -0.04) & (z > 0.715))      # forehead up to the circlet; the circlet band
    scalp = ok & (z > 0.62) & (z < 0.80) & (y > -0.10) & ~facez & ~circ & ~hoodb & ((np.abs(x) > 0.045) | (z > 0.70))
    scalp &= ~(((hh > 30) & (hh < 55) & (vv2 > 0.75)))            # the existing light blonde strands keep their paint
    rgb8 = unlin(np.clip(L, 0, 1)) * 255; lv8 = rgb8 @ np.array([0.2126, 0.7152, 0.0722])
    flat = (np.abs(rgb8 - np.array([144, 115, 69])).max(-1) < 30) & (np.abs(lv8 - ni.uniform_filter(lv8, 5)) < 6)
    scalp |= ok & flat & (z > 0.62) & ~((y < -0.07) & (np.abs(x) < 0.062) & (z < 0.745)) & ~hoodb      # the flat tan left by the r2 recolour
    strands = ok & (z > 0.55) & (z < 0.66) & (y < -0.07) & (np.abs(x) > 0.05) & (hh > 30) & (hh < 55) & (vv2 > 0.6) & (ss2 > 0.2)
    if scalp.sum() and strands.sum() > 50:
        bl = np.median(L[strands], 0)
        rng = np.random.default_rng(7); nz_ = ni.gaussian_filter1d(rng.standard_normal(4096), 1.5, mode='wrap'); nz_ /= np.abs(nz_).max()
        az_ = np.arctan2(x, -y); k_ = ((az_ / np.pi * 0.5 + 0.5) * 2600 + (z - 0.70) * 400).astype(int) % 4096
        back = np.clip((y + 0.06) / 0.12, 0, 1)
        newc = bl[None, None, :] * np.clip(0.92 + 0.30 * nz_[k_] - 0.18 * back, 0.55, 1.15)[..., None]
        ws = np.clip(ni.gaussian_filter(scalp.astype(np.float32), 1.0) * 1.4, 0, 1)[..., None] * ok[..., None]
        L = L * (1 - ws) + newc * ws
        print('SCALP blonde', int(scalp.sum()), 'texels, blonde', np.round(unlin(bl) * 255).tolist())
out = unlin(np.clip(L, 0, 1))
# 3. gutters
D = np.load('work/uv.npz'); tri, uv, mat = D['tri'], D['uv'], D['mat']
cv = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cv)
for t in tri[mat == 1]: dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in t], fill=255)
inside = ni.binary_erosion(np.asarray(cv) > 0, iterations=1)
idx = ni.distance_transform_edt(~inside, return_distances=False, return_indices=True); out = out[idx[0], idx[1]]
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST); print('FACEFIX', DST, 'gutter texels', int((~inside).sum()))
