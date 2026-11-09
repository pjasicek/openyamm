#!/usr/bin/env python3
"""Scholar head colour per tier (textures/sc_head_<t>_raw.png -> sc_head_<t>_final.png), fixes by 3D position (work/texel_pos_head.npy):
1. EARS PAINTED ON THE HAIR: both head retextures drew a pale ear on the hair shell beside the temple (the mesh's ears are under the hair).
   Hair texels in the ear zone (|x| > 0.06, z 0.73-0.85, -0.05 < y < 0.06) with a skin colour (hue 5-32, saturation 0.18-SKINSAT, value >
   0.5) take the hair around them (normalised convolution of the other hair texels) with their own luminance detail.
Args: <tier a|b>  (project folder)"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
t = sys.argv[1]; SKINSAT = float(os.environ.get('SKINSAT', '0.55' if t == 'a' else '0.6'))
im = np.asarray(Image.open(f'textures/sc_head_{t}_raw.png').convert('RGB'), np.float32) / 255
P = np.load('work/texel_pos_head.npy'); part = np.load('work/texel_part_head.npy'); names = [str(x) for x in np.load('work/asm.npz')['names']]
X, Y, Z = (np.nan_to_num(P[..., i]) for i in range(3))
hsv = np.asarray(Image.fromarray((im * 255).astype('u1')).convert('HSV'), np.float32) / 255; h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
LUMA = np.array([0.2126, 0.7152, 0.0722]); L = im @ LUMA
hair = part == names.index('hair')
zone = hair & (np.abs(X) > 0.06) & (Z > 0.73) & (Z < 0.85) & (Y > -0.05) & (Y < 0.06)
ear = zone & (h > 5) & (h < 32) & (s > 0.18) & (s < SKINSAT) & (v > 0.5)
# second test: texels off the local hair colour (Gaussian 10 px of the zone): paler and less saturated than the ginger hair (tier a), or more
# saturated than the white hair (tier b): the painted ear's outline strokes
zf = zone.astype(np.float32); ls = ni.gaussian_filter(s * zf, 10) / np.maximum(ni.gaussian_filter(zf, 10), 1e-4); lv = ni.gaussian_filter(v * zf, 10) / np.maximum(ni.gaussian_filter(zf, 10), 1e-4)
off = (s < ls - 0.12) & (v > lv + 0.04) if t == 'a' else (s > ls + 0.08)
ear = ear | (zone & off & (np.abs(X) > 0.065))
ear = ni.binary_dilation(ni.binary_opening(ear, iterations=1), iterations=2) & zone
ok = hair & ~ear; fill = None
for sg in (16.0, 8.0, 4.0):
    wv = ni.gaussian_filter(ok.astype(np.float32), sg)
    f2 = np.stack([ni.gaussian_filter(im[..., i] * ok, sg) for i in range(3)], -1) / np.maximum(wv, 1e-6)[..., None]
    fill = f2 if fill is None else np.where((wv > 0.2)[..., None], f2, fill)
det = L - ni.gaussian_filter(L, 3)
w = np.clip(ni.gaussian_filter(ear.astype(np.float32), 1.0) * 1.5, 0, 1) * zone
# 2026-11-04 ("the faint ear outline on tier A's hair"): the ear's own detail (0.6 x det) kept its outline strokes, and none left a smooth
# patch: the strand detail now comes from hair texels STRAND_DY texels along the texture's v axis (nearest shift whose source is clean hair)
dmask = ni.binary_dilation(ear, iterations=4); sdet = np.zeros_like(det); have = np.zeros(det.shape, bool)
for dy in (24, -24, 40, -40, 56, -56, 72, -72):
    src_ok = np.roll(ok & ~dmask, dy, axis=0); src_det = np.roll(det, dy, axis=0)
    take = dmask & src_ok & ~have; sdet[take] = src_det[take]; have |= take
out = im * (1 - w[..., None]) + np.clip(fill + (float(os.environ.get('EARDET', '0.0')) * det + sdet)[..., None], 0, 1) * w[..., None]
# 1b. JAW: the face shell's lower jaw sides (under the beard, z < 0.72) were painted the robe's blue on tier B (review r9: two dark blue
#     triangles beside the chin in the front view): blue texels there take the tier's beard colour (median of the beard texels in front of
#     the chin) with their own luminance detail.
jz = (part == names.index('head')) & (Z < 0.74) & (Z > 0.55) & (Y < 0.0) & ~((Z > 0.715) & (np.abs(X) < 0.03))
jb = jz & (((h > 180) & (h < 270) & (s > 0.12)) | ((v < 0.4) & (Z < 0.73)))
jb = ni.binary_dilation(jb, iterations=2) & jz
if jb.any():
    beard = hair & (Y < -0.05) & (Z > 0.6) & (Z < 0.7) & (np.abs(X) < 0.04)
    bc = np.median(im[beard], 0); Lj = im @ LUMA; dj = Lj - ni.gaussian_filter(Lj, 3)
    wj = np.clip(ni.gaussian_filter(jb.astype(np.float32), 1.0) * 1.5, 0, 1) * jz
    out = out * (1 - wj[..., None]) + np.clip(bc + 0.6 * dj[..., None], 0, 1) * wj[..., None]
print('JAW blue texels', int(jb.sum()))
# 1d. MOUTH (tier b, review r15-r17: the Master Scholar still read stern: a horseshoe moustache hanging down beside a full, level lower lip;
#     MM9's master has a short moustache over a slight smile). In front coordinates (x, z of each texel): the moustache's hanging tips
#     beside the mouth (whitish texels, MX0 < |x| < MX1, MZ0 < z < MZ; not the white band along the face shell's lower edge, which meets
#     the beard) take the skin around them (normalised convolution of the lower face's skin texels) with their own detail. (r18 also cut the
#     lower lip into a crescent and every white texel down to the jaw edge: mottled chin; dropped.)
LOWERA = t == 'b' and os.environ.get('LOWERA', '1') == '1'
if t == 'b' and os.environ.get('MOUTHFIX', '0' if LOWERA else '1') == '1':
    MX0, MX1, MZ, MZ0 = (float(os.environ.get(k, d)) for k, d in (('MX0', '0.026'), ('MX1', '0.045'), ('MZ', '0.737'), ('MZ0', '0.711')))
    hs = np.asarray(Image.fromarray((np.clip(out, 0, 1) * 255).astype('u1')).convert('HSV'), np.float32) / 255; h2, s2, v2 = hs[..., 0] * 360, hs[..., 1], hs[..., 2]
    face = (part == names.index('head')) & (Y < -0.03) & (np.abs(X) < 0.06) & (Z > 0.69) & (Z < 0.76)
    white = (s2 < 0.22) & (v2 > 0.5); pink = ((h2 < 14) | (h2 > 340)) & (s2 > 0.25)
    skin = face & (h2 > 6) & (h2 < 35) & (s2 > 0.22) & (s2 < 0.65) & (v2 > 0.45) & ~white
    grey = (s2 < 0.26) & (v2 > 0.36)
    side = face & grey & (np.abs(X) > MX0) & (np.abs(X) < MX1) & (Z < MZ) & (Z > MZ0)
    mk = ni.binary_closing(side, iterations=2) & face; mk = ni.binary_dilation(mk, iterations=1) & face
    ok = skin & ~mk; fill = None
    for sg in (12.0, 6.0, 3.0):
        wv = ni.gaussian_filter(ok.astype(np.float32), sg)
        f2 = np.stack([ni.gaussian_filter(out[..., i] * ok, sg) for i in range(3)], -1) / np.maximum(wv, 1e-6)[..., None]
        fill = f2 if fill is None else np.where((wv > 0.2)[..., None], f2, fill)
    Lm = out @ LUMA; dm = Lm - ni.gaussian_filter(Lm, 2)
    wm = np.clip(ni.gaussian_filter(mk.astype(np.float32), 1.5) * 1.4, 0, 1) * face
    out = out * (1 - wm[..., None]) + np.clip(fill + 0.4 * dm[..., None], 0, 1) * wm[..., None]
    print('MOUTH moustache sides', int(side.sum()), 'texels')
# 1e. LOWER FACE FROM TIER A (tier b, finishing round 2026-11-04: after 1b-1d the Master Scholar still read as a pout: Meshy painted tier B's
#     face shell with a horseshoe moustache over a full pink lower lip and a bare chin, where MM9's Master Scholar has a short moustache over
#     a slight smile and a beard from the lower lip down; tier A's head paint has exactly that layout on the same face shell). Inside the lower
#     face (head shell below the nose base, rising to LA_ZSIDE on the jaw sides, feathered 4 mm), tier A's colour is carried over: its facial-
#     hair texels (hue BH-42, saturation > BS, plus everything below LA_ZCHIN, minus the lips) take tier B's white beard colour at the same
#     luminance quantile as on B's beard sheet (A's strand detail kept); its skin and lips take A's colour times the cheek-skin ratio B / A.
#     Replaces 1d (MOUTHFIX defaults to 0 with LOWERA). The shared head normal map is tier A's, so the relief now matches on both tiers.
if LOWERA:
    A_ = np.asarray(Image.open('textures/sc_head_a_raw.png').convert('RGB'), np.float32) / 255
    qa = np.asarray(Image.open('textures/sc_head_a_raw.png').convert('HSV'), np.float32) / 255; ha, sa = qa[..., 0] * 360, qa[..., 1]
    def ss_(x, a, b):
        tt = np.clip((x - a) / (b - a), 0, 1); return tt * tt * (3 - 2 * tt)
    ax_ = np.abs(X); headm = part == names.index('head')
    ztop = 0.751 + (float(os.environ.get('LA_ZSIDE', '0.775')) - 0.751) * ss_(ax_, 0.036, 0.062)
    zone = headm & (Y < 0.03) & (Z < ztop)
    zw = (1 - ss_(Z - ztop, -0.004, 0.0)) * headm * (Y < 0.03)
    beardA = zone & (ha > float(os.environ.get('BH', '21.5'))) & (ha < 42) & (sa > float(os.environ.get('BS', '0.45')))
    lipsA = ni.binary_closing(zone & ((ha < 15) | (ha > 335)) & (sa > 0.18) & (Z > 0.715) & (Z < 0.75) & (ax_ < 0.04), iterations=2)
    bm = ni.binary_closing(ni.binary_opening(beardA, iterations=1), iterations=4)
    bm = (bm | (Z < float(os.environ.get('LA_ZCHIN', '0.712')))) & zone & ~lipsA
    bw = np.clip(ni.gaussian_filter(bm.astype(np.float32), 1.0) * 1.3, 0, 1) * zone
    bb = hair & (Y < -0.05) & (Z > 0.6) & (Z < 0.69) & (ax_ < 0.05)
    Lb = out[bb] @ LUMA; qs = np.linspace(2, 98, 25); qB = np.percentile(Lb, qs)
    cB = np.median(out[bb] / np.maximum(Lb, 1e-3)[:, None], 0)
    LA_ = A_ @ LUMA; qA = np.percentile(LA_[beardA], qs)
    white = np.clip(cB[None, None] * np.interp(LA_, qA, qB)[..., None], 0, 1)
    ck = headm & (Y < -0.02) & (Z > 0.745) & (Z < 0.775) & (ax_ > 0.03) & (ax_ < 0.05)
    gain = np.median(out[ck], 0) / np.maximum(np.median(A_[ck & (sa < 0.55)], 0), 1e-3)
    new = np.clip(A_ * gain, 0, 1) * (1 - bw[..., None]) + white * bw[..., None]
    out = out * (1 - zw[..., None]) + new * zw[..., None]
    print('LOWERA zone', int(zone.sum()), 'beard', int(bm.sum()), 'gain', np.round(gain, 3))
    # the beard sheet's top edge under the chin (hair part, z > 0.665): Meshy painted a few skin texels there (a pink notch under the chin
    # in the front view): they take the beard colour at their own luminance quantile
    hb = np.asarray(Image.fromarray((np.clip(out, 0, 1) * 255).astype('u1')).convert('HSV'), np.float32) / 255
    nt = hair & (Y < 0.0) & (Z > 0.665) & (ax_ < 0.05) & (hb[..., 0] * 360 < 40) & (hb[..., 1] > 0.15)
    nt = ni.binary_dilation(nt, iterations=1) & hair & (Y < 0.0) & (Z > 0.66)
    Ln = out @ LUMA; rk = np.interp(Ln, np.percentile(Ln[nt], qs) if nt.any() else qs, qB)
    wn = np.clip(ni.gaussian_filter(nt.astype(np.float32), 0.8) * 1.5, 0, 1) * hair
    out = out * (1 - wn[..., None]) + np.clip(cB[None, None] * rk[..., None], 0, 1) * wn[..., None]
    print('LOWERA beard-top skin texels', int(nt.sum()))
# 1c. SMILE, after 1d (review r15: the Master Scholar's mouth still read downturned; MM9's smiles slightly; the mouth-corner vertex lift in tweak_sc.py
#     moved too little paint): the head texels around each mouth corner (SM_X, SM_Z mirrored, radius SM_R; placed from a grid-painted render, r19) take the colour from SMILE metres lower
#     on the face, falling off as (1 - d / SR)^2, so the lip corners and the moustache's lower edge rise. Paint only, tier b by default.
SMILE = float(os.environ.get('SMILE', '0.0035' if t == 'b' else '0'))
if SMILE > 0:
    from scipy.spatial import cKDTree
    SCX, SCZ, SR = (float(os.environ.get(k, d)) for k, d in (('SM_X', '0.029'), ('SM_Z', '0.733'), ('SM_R', '0.012')))
    hd = (part == names.index('head')) & (Y < -0.02) & (np.abs(X) < 0.07) & (Z > 0.68) & (Z < 0.79)
    hy_, hx_ = np.nonzero(hd); pts = np.c_[X[hd], Y[hd], Z[hd]]; kd = cKDTree(pts)
    dz = np.zeros(len(pts))
    for sx in (1, -1): dz += SMILE * np.clip(1 - np.hypot(pts[:, 0] - sx * SCX, pts[:, 2] - SCZ) / SR, 0, 1) ** 2
    mv = dz > 1e-5; src = pts[mv] - np.c_[np.zeros(mv.sum()), np.zeros(mv.sum()), dz[mv]]
    _, j = kd.query(src, k=1)
    col = out[hy_[j], hx_[j]]
    out[hy_[mv], hx_[mv]] = col
    print('SMILE texels', int(mv.sum()), 'lift mm', SMILE * 1000)
# 1f. EARS UNDER THE HAIR (finishing round 2026-11-04: "the faint ear outline on tier A's hair"): the head shell's ears (folded flat
#     under the hair shell by tweak_sc.py) are still painted as ears, skin with a dark rim, and their tips show through the hair at grazing
#     angles as a pale ear outline. MM9's hair covers the ears: the ear texels of the head shell (EAR zone) take the tier's hair colour (median
#     of the hair sheet beside the ear) with a little of their own luminance detail.
if os.environ.get('EARHAIR', '1') == '1':
    ez = (part == names.index('head')) & (np.abs(X) > 0.05) & (Y > 0.005) & (Y < 0.075) & (Z > 0.73) & (Z < 0.82)
    he_ = np.asarray(Image.fromarray((np.clip(out, 0, 1) * 255).astype('u1')).convert('HSV'), np.float32) / 255
    ez &= ((he_[..., 0] * 360 < 45) | (he_[..., 0] * 360 > 330)) & (he_[..., 1] > 0.12)      # the painted ear (skin, its rim), not the cap's blue
    ez = ni.binary_closing(ez, iterations=2) & (part == names.index('head'))
    hz = hair & (np.abs(X) > 0.05) & (Y > 0.0) & (Y < 0.08) & (Z > 0.73) & (Z < 0.84)
    hc = np.median(out[hz], 0); Le = out @ LUMA; Lh = float(np.median(Le[ez])) if ez.any() else 0.5
    ec = np.clip(hc[None, None] * ((Le / max(Lh, 1e-3)) ** 0.2)[..., None], 0, 1)
    we = np.clip(ni.gaussian_filter(ez.astype(np.float32), 1.5) * 1.3, 0, 1) * (part == names.index('head'))
    out = out * (1 - we[..., None]) + ec * we[..., None]
    print('EARHAIR head-shell ear texels', int(ez.sum()), 'hair colour', (hc * 255).round(0))
cov = part >= 0; idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); out = out[idx[0], idx[1]]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('u1')).save(f'textures/sc_head_{t}_final.png')
# 2. the ear's relief in the shared head normal map (Meshy painted the ear's outline into it too: pale curls under light): the hair texels
#    of the ear zone take the hair's smoothed normal (Gaussian 6 px). Tier a only (the normal map is shared). Hair only, not the face.
if t == 'a':
    import shutil
    src = 'textures/sc_head_normal_raw.png'
    if not os.path.exists(src): shutil.copyfile('textures/sc_head_normal.png', src)
    nm = np.asarray(Image.open(src).convert('RGB'), np.float32) / 255
    if nm.shape[0] != part.shape[0]: nm = np.asarray(Image.open(src).convert('RGB').resize(part.shape[::-1], Image.LANCZOS), np.float32) / 255
    sm = np.stack([ni.gaussian_filter(nm[..., i], 6) for i in range(3)], -1)
    wz = np.clip(ni.gaussian_filter((zone & (np.abs(X) > 0.06)).astype(np.float32), 2.0) * 1.2, 0, 1) * hair
    nm2 = nm * (1 - wz[..., None]) + sm * wz[..., None]
    v3 = nm2 * 2 - 1; v3 /= np.maximum(np.linalg.norm(v3, axis=-1, keepdims=True), 1e-6); nm2 = (v3 + 1) / 2
    Image.fromarray((np.clip(nm2, 0, 1) * 255 + 0.5).astype('u1')).save('textures/sc_head_normal.png'); print('NORMAL ear zone texels', int((wz > 0.5).sum()))
print('HEADFIX', t, 'ear texels', int(ear.sum()))
