#!/usr/bin/env python3
"""PF7 head paint fixes (per tier) on the head set (head shell with eyeballs, hair, braids), by texel 3D position (rest mesh):
- hair: Meshy projected the green pinafore and cream chemise onto the hair ends and the braids' inner sides: texels off the hair's median hue
  (HUE_TOL) or nearly grey take the median hair chroma at their own luminance (strand detail kept).
- eyes (F5's head_fix.py): Meshy's eyeballs stared (iris fully visible, white above it). Each eyeball is repainted: sclera, iris (tier colour),
  pupil, catchlight, a shadowed upper lid with a lash line over the top of the iris, a lower lid; red lid rims toward the skin.
- nostrils: dark paint on forward-facing texels round the nose tip (the dark blotch seen from the front) goes to the nose skin; down-facing
  texels keep a soft cool shadow (F5 r19).
- freckles: the blotchy cheek spots softened (their contrast against a 3 px blur x FRECKLE).
The head normal map is not touched. Args: <tier a|b> <in png> <out png>   (project folder; uses work/uv.npz + work/asm_frozen.npz)"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
T_, SRC, DST = sys.argv[1:4]; TOL = float(os.environ.get('HUE_TOL', '15'))
D = np.load('work/uv.npz'); co, tri, uv, mat, comp, orig = D['co'], D['tri'], D['uv'], D['mat'], D['comp'], D['orig']; names = [str(x) for x in D['names']]
if os.path.exists('work/uv_tex2.npz'):
    D2 = np.load('work/uv_tex2.npz')
    if len(D2['co']) == len(co): co = D2['co']      # texel positions after the face tweak (closed mouth etc.)
A = np.load('work/asm_frozen.npz'); ac, at, acomp = A['co'], A['tri'], A['comp']
S = 1024; fi = np.where(mat == 1)[0]
im_ = Image.new('I', (S, S), -1); dr = ImageDraw.Draw(im_)
for k, f in enumerate(fi): dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in tri[f]], fill=int(k))
F = np.asarray(im_).astype(np.int64); cov = F >= 0
yy, xx = np.nonzero(cov); f = fi[F[yy, xx]]
P = np.stack([(xx + 0.5) / S, 1 - (yy + 0.5) / S], 1); Au, Bu, Cu = uv[tri[f, 0]], uv[tri[f, 1]], uv[tri[f, 2]]
v0, v1, v2 = Bu - Au, Cu - Au, P - Au; d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
den = d00 * d11 - d01 * d01; den[np.abs(den) < 1e-14] = 1e-14; b1 = (d11 * d20 - d01 * d21) / den; b2 = (d00 * d21 - d01 * d20) / den; b0 = 1 - b1 - b2
pos = np.zeros((S, S, 3)); pos[yy, xx] = co[tri[f, 0]] * b0[:, None] + co[tri[f, 1]] * b1[:, None] + co[tri[f, 2]] * b2[:, None]
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
nrm = np.zeros((S, S, 3)); nrm[yy, xx] = fn[f]
part = np.full((S, S), -1); part[yy, xx] = comp[tri[f, 0]]
# eyeballs: small closed components of the head part near each eye
hk = names.index('head'); par = np.arange(len(ac))
def fd(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a, b, c in at[acomp[at[:, 0]] == hk]:
    r = fd(a); par[fd(b)] = r; par[fd(c)] = r
hv = np.where(acomp == hk)[0]; rt = np.array([fd(v) for v in hv]); big = np.bincount(rt).argmax()
small = np.zeros(len(ac), bool); small[hv[rt != big]] = True
EYEC = np.array([0.032, -0.08, 0.685]); ctr = {}
eyev = np.zeros(len(ac), bool)
for sg in (1, -1):
    m = small & (np.linalg.norm(ac - EYEC * [sg, 1, 1], axis=1) < 0.03); eyev |= m
    q = ac[m]; c = q.mean(0); ctr[sg] = (c, float(np.linalg.norm(q - c, axis=1).mean()))
eyef = eyev[orig[tri[:, 0]]]; EYE = np.zeros((S, S), bool); EYE[yy, xx] = eyef[f]
X, Y, Z = pos[..., 0], pos[..., 1], pos[..., 2]
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
src = Image.open(SRC).convert('RGB'); im = np.asarray(src, np.float32); out = im.copy()
hsv = np.asarray(src.convert('HSV'), np.float32) / 255; h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
# ---- hair
hair = np.isin(part, [names.index(n) for n in ('hair', 'braids') if n in names])
good = hair & (s > 0.25); hm = np.median(h[good]); dh = np.abs((h - hm + 180) % 360 - 180)
bad = ni.binary_dilation(hair & ((dh > TOL) | (s < 0.12)), iterations=1) & hair
lumv = im @ np.array([0.2126, 0.7152, 0.0722]); ref = im[hair & ~bad]; rl = ref @ np.array([0.2126, 0.7152, 0.0722])
chroma = np.median(ref / np.maximum(rl, 1)[:, None], 0)
k = np.clip(ni.gaussian_filter(bad.astype(np.float32), 0.8) * 1.5, 0, 1)[..., None] * hair[..., None]
out = out * (1 - k) + np.clip(chroma[None, None] * lumv[..., None], 0, 255) * k
# ---- eyes
skin_m = cov & ~EYE & (part == hk) & (np.abs(np.abs(X) - 0.032) < 0.012) & (Z > EYEC[2] - 0.03) & (Z < EYEC[2] - 0.015) & (Y < -0.07)
skin = np.median(im[skin_m], 0)
IRIS = {'a': np.array([96, 130, 78.]), 'b': np.array([104, 122, 112.])}[T_]
U, L = 0.16, -0.42
for sg in ((1, -1) if os.environ.get('EYES', '0') == '1' else ()):
    c, r = ctr[sg]; m = EYE & (X * sg > 0)
    d = (pos[m] - c) / r; dx = d[:, 0] * sg; dz = d[:, 2]; rr = np.sqrt(dx ** 2 + (dz + 0.02) ** 2)
    noise = np.random.default_rng(1 if sg > 0 else 2).normal(0, 1, len(rr))
    scl = np.array([222, 212, 204.]) * (1 - 0.18 * ss(np.abs(dx), 0.35, 0.95))[:, None]
    ir = IRIS * (0.85 + 0.25 * ss(rr, 0.10, 0.30))[:, None] * (1 + 0.06 * noise)[:, None]; ir = ir * (1 - 0.45 * ss(rr, 0.27, 0.35))[:, None]
    iw = 1 - ss(rr, 0.34, 0.38); col = scl * (1 - iw)[:, None] + ir * iw[:, None]
    pup = 1 - ss(rr, 0.12, 0.15); col = col * (1 - pup)[:, None] + np.array([18, 16, 18.]) * pup[:, None]
    hl = np.exp(-(((dx + 0.15) ** 2 + (dz - 0.10) ** 2) / 0.004)); col = col + (255 - col) * (0.5 * hl)[:, None]
    col = col * (1 - 0.35 * np.exp(-((dz - (U - 0.05)) / 0.18) ** 2) * (dz < U))[:, None]
    lash = np.exp(-((dz - (U - 0.015)) / 0.045) ** 2) * (1 - 0.5 * ss(np.abs(dx), 0.6, 1.0))
    col = col * (1 - 0.8 * lash)[:, None] + np.array([46, 32, 28.]) * (0.8 * lash)[:, None]
    up = ss(dz, U, U + 0.06); lo = ss(dz, L, L - 0.06)
    col = col * (1 - up)[:, None] + (skin * 0.55 + np.array([40, 28, 26.]) * 0.2) * up[:, None]
    col = col * (1 - lo)[:, None] + (skin * 0.9) * lo[:, None]
    out[m] = col
rim = np.zeros_like(cov)
for sg in (1, -1):
    c, r = ctr[sg]; rim |= cov & ~EYE & (np.linalg.norm(pos - c, axis=2) < r + 0.008) & (X * sg > 0) & (part == hk)
hsv0 = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype('u1')).convert('HSV'), np.float32) / 255
sk_s = (skin.max() - skin.min()) / max(skin.max(), 1)
redrim = rim & ((hsv0[..., 0] * 360 < 22) | (hsv0[..., 0] * 360 > 340)) & (hsv0[..., 1] > sk_s + 0.06)
rw = ni.gaussian_filter(redrim.astype(np.float32), 1.0)[..., None] * 0.75 * (os.environ.get('EYES', '0') == '1')
out = out * (1 - rw) + skin * np.clip(out.mean(2, keepdims=True) / skin.mean(), 0.6, 1.1) * rw
# ---- nostrils: around the nose tip (z 0.628-0.648), dark forward-facing paint -> nose skin; down-facing -> soft cool shadow
nose = cov & (part == hk) & (np.abs(X) < 0.02) & (Z > 0.627) & (Z < 0.648) & (Y < -0.085)
nsk = np.median(im[cov & (part == hk) & (np.abs(X) < 0.006) & (Z > 0.650) & (Z < 0.665) & (Y < -0.10)], 0)
lumn = out.mean(2); dark = nose & (lumn < 0.72 * nsk.mean())
fw = dark & (nrm[..., 2] > -0.45)
dw = nose & (nrm[..., 2] <= -0.45)
NOSE_ON = os.environ.get('NOSTRIL', '0') == '1'
w1 = NOSE_ON * np.clip(ni.gaussian_filter(fw.astype(np.float32), 0.8) * 1.4, 0, 1)[..., None] * nose[..., None]
out = out * (1 - w1) + nsk * w1
w2 = NOSE_ON * np.clip(ni.gaussian_filter(dw.astype(np.float32), 0.8), 0, 1)[..., None] * nose[..., None]
cool = nsk * 0.62; cool = cool * 0.75 + cool.mean() * 0.25
out = out * (1 - w2) + np.minimum(out, cool) * w2 * 0.6 + out * w2 * 0.4
# gentle default: dark paint on the nose underside lifted halfway toward the nose skin (no new shadow; the geometry shades it)
dk2 = nose & (lumn < 0.80 * nsk.mean())
w3 = (1 - NOSE_ON) * float(os.environ.get('NOSE_LIFT', '0.55')) * np.clip(ni.gaussian_filter(dk2.astype(np.float32), 1.0) * 1.3, 0, 1)[..., None] * nose[..., None]
out = out * (1 - w3) + nsk * 0.92 * w3
# ---- mouth/philtrum specks: texels that differ strongly from their 9-texel median (inner-mouth paint brought to the surface by the mouth
# closure, light/blue lines) take the median; the nose underside (down-facing) lifted LIFT_UNDER against the shading
box = cov & (part == hk) & (np.abs(X) < 0.03) & (Z > 0.600) & (Z < 0.646) & (Y < -0.07)
med = np.stack([ni.median_filter(out[..., c], size=9) for c in range(3)], -1)
spk = box & (np.abs(out - med).sum(2) > float(os.environ.get('SPECK', '45')))
spk = ni.binary_dilation(spk, iterations=1) & box
ws = np.clip(ni.gaussian_filter(spk.astype(np.float32), 0.7) * 1.5, 0, 1)[..., None]
out = out * (1 - ws) + med * ws
und = nose & (nrm[..., 2] < -0.35)
wu = np.clip(ni.gaussian_filter(und.astype(np.float32), 1.2), 0, 1)[..., None] * nose[..., None]
LU = float(os.environ.get('LIFT_UNDER', '0.30'))
redn = und & (hsv[..., 0] * 360 < 20) & (hsv[..., 1] > 0.45)
out = out * (1 + LU * wu); out = np.where((redn & (LU > 0))[..., None], out * 0.5 + nsk * 0.5, out)
print('SPECKS', int(spk.sum()), 'nose under', int(und.sum()), 'red nostril', int(redn.sum()))
# ---- freckles: cheek/nose spots softened
FR = float(os.environ.get('FRECKLE', '0.3'))
face = cov & (part == hk) & ~EYE & (Y < -0.04) & (Z > 0.60) & (Z < EYEC[2] - 0.008)
blur = np.stack([ni.gaussian_filter(out[..., c], 3) for c in range(3)], -1)
spot = np.clip((blur.mean(2) - out.mean(2)) / 25.0, 0, 1)[..., None] * face[..., None]
out = out * (1 - FR * spot) + blur * FR * spot
# ---- PASS2 paint finish (face pass 2, on the fresh Meshy 4K paint over the final geometry; paint only, geometry fixed)
if os.environ.get('PASS2', '0') == '1':
    SL = float(os.environ.get('SLIT_Z', '0.6235'))
    def hsvof(a): return np.asarray(Image.fromarray(np.clip(a, 0, 255).astype('u1')).convert('HSV'), np.float32) / 255
    med9 = np.stack([ni.median_filter(out[..., c], size=9) for c in range(3)], -1)
    face_ = cov & (part == hk) & ~EYE
    # (1) lips: lipstick red -> rose (saturation x0.72, value x1.05) inside the lip band
    lipb = face_ & (np.abs(X) < 0.032) & (Z > SL - 0.014) & (Z < SL + 0.012) & (Y < -0.07)
    rg_ = (out[..., 0] - out[..., 1]) / np.maximum(out[..., 0], 1); sk_rg = np.median(rg_[face_ & (np.abs(X) > 0.035) & (np.abs(X) < 0.05) & (Z > SL - 0.01) & (Z < SL + 0.02)])
    red = lipb & (rg_ > sk_rg + 0.12)      # lip red only: redder than the cheek skin beside the mouth by 0.12 in (R-G)/R
    wr = np.clip(ni.gaussian_filter(red.astype(np.float32), 1.0) * 1.3, 0, 1)[..., None]
    g_ = out.mean(2, keepdims=True); rose = np.clip((g_ + (out - g_) * 0.84) * 1.03, 0, 255)
    if os.environ.get('LIPROSE', '1') == '1': out = out * (1 - wr) + rose * wr      # off on the v3 paint (its lips are already rose)
    # (2) light outliers (pale specks/ticks) in the mouth, philtrum and the forehead midline: back to the local median
    zone = face_ & (np.abs(X) < 0.034) & (Z > SL - 0.016) & (Z < SL + 0.035) & (Y < -0.07)
    zone |= face_ & (np.abs(X) < 0.012) & (Z > EYEC[2] + 0.02) & (Y < -0.04)
    lum_ = out.mean(2); light = zone & (lum_ - med9.mean(2) > 22)
    light = ni.binary_dilation(light, iterations=1) & zone
    if os.environ.get('LIGHTSPK', '1') == '1': out[light] = med9[light]      # off on the v3 paint (the 9-texel median across UV islands drew blocks)
    # (3) nostrils: paint under the nose tip lifted to at least NOST_MIN of the nose skin (geometry shades the pits)
    nbox = face_ & (np.abs(X) < 0.02) & (Z > max(SL + 0.006, float(os.environ.get('NBOX_Z0', '0')))) & (Z < SL + 0.030) & (Y < -0.085)      # v3: NBOX_Z0 keeps the upper lip out
    nsk2 = np.median(out[face_ & (np.abs(X) < 0.006) & (Z > SL + 0.035) & (Z < SL + 0.050) & (Y < -0.09)], 0)
    l2 = out.mean(2); mn = float(os.environ.get('NOST_MIN', '0.62')) * nsk2.mean()
    lift = nbox & (l2 < mn); k2 = np.where(lift, mn / np.maximum(l2, 1), 1.0)
    out = out * np.clip(ni.gaussian_filter(k2, 1.0), 1, 2.5)[..., None]
    # (4) hair parting / hair midline: texels lighter than the hair's local median by > 18 -> the median x 0.92
    hm2 = cov & hair & (np.abs(X) < 0.005) & (Y < -0.03)
    hmed = np.stack([ni.median_filter(out[..., c], size=13) for c in range(3)], -1)
    pl = hm2 & (out.mean(2) - hmed.mean(2) > 18); out[pl] = hmed[pl] * 0.92
    # (5) a soft lid shadow on the top of each eyeball (the white above the iris read as a stare)
    LS = float(os.environ.get('LID_SHADE', '0.55'))
    for sg in (1, -1):
        c, r = ctr[sg]; m = EYE & (X * sg > 0)
        dz = (pos[..., 2] - c[2]) / r; w5 = np.clip((dz - 0.05) / 0.25, 0, 1) * m
        out = out * (1 - (1 - LS) * w5[..., None])
    # (6) forehead midline band evened: |x| < 9 mm between the brows and the hairline scaled to the luminance at |x| 11-17 mm
    fb = face_ & (np.abs(X) < 0.009) & (Z > EYEC[2] + 0.005) & (Y < -0.06)
    fr = face_ & (np.abs(X) > 0.011) & (np.abs(X) < 0.017) & (Z > EYEC[2] + 0.005) & (Y < -0.06)
    if fb.sum() > 50 and fr.sum() > 50 and os.environ.get('FH2', '0') != '1':
        gfb = np.clip(np.median(out[fr], 0) / np.maximum(np.median(out[fb], 0), 1), 0.85, 1.0)
        wb = np.clip(ni.gaussian_filter(fb.astype(np.float32), 3.0) * 1.2, 0, 1)[..., None]
        out = out * (1 - wb) + out * gfb * wb
    else: gfb = None
    # (6b) neck pass 2026-11-04 (replaces (6) with FH2=1): (F2) tier A's forehead still read as a band with sharp edges ~1 cm either side of the
    # midline (Meshy painted the middle UV island lighter; (6)'s flat gain then made it darker): paint profile P(x, z) in 1 mm x 4 mm bins
    # over the forehead (z 0.716 to the hairline, eased in over 8 mm, |x| < 18 mm), target T(z) = the paint at |x| 13-18 mm, gain T / P per channel for |x| < 13 mm,
    # eased to 1 by 18 mm. The step at the island edges is in the gain, so it cancels; texel detail kept.
    if os.environ.get('FH2', '0') == '1':
        Z0 = float(os.environ.get('FH2_Z0', '0.716'))      # above the inner brow ends (a reference over the brows put a grey bar there)
        fh = face_ & (np.abs(X) < 0.018) & (Z > Z0) & (Y < -0.04)
        xb = np.clip(np.round((X + 0.018) / 0.001).astype(int), 0, 36); zb = np.clip(np.round((Z - Z0) / 0.004).astype(int), 0, 40)
        g6 = np.ones(out.shape, np.float32); nfix = 0
        for zz in np.unique(zb[fh]):
            mz = fh & (zb == zz); ref = mz & (np.abs(X) > 0.013)
            if ref.sum() < 30: continue
            Tz = np.median(out[ref], 0)
            for xx in np.unique(xb[mz]):
                mb = mz & (xb == xx)
                if mb.sum() < 4: continue
                ax = abs(xx * 0.001 - 0.018); w = np.clip((0.018 - ax) / 0.005, 0, 1) * np.clip((Z[mb] - Z0) / 0.008, 0, 1)[:, None]
                g6[mb] = 1 + (np.clip(Tz / np.maximum(np.median(out[mb], 0), 1), 0.85, 1.15) - 1) * w; nfix += int(mb.sum())
        out = out * g6
        print('PASS2 forehead profile texels', nfix)
    # (7) nose underside (geometry smoothed by tweak_pf7 COL_PASSES): down-facing texels under the tip -> nose-skin shade with two soft
    # cool nostrils; texels are read at the tweaked positions (work/uv_tex2.npz), so their colour follows the new surface
    und7 = face_ & (np.abs(X) < 0.017) & (Z > float(os.environ.get('UND_Z0', '0.630'))) & (Z < 0.648) & (Y < -0.092) & (nrm[..., 2] < -0.2)
    if und7.any():
        shade = nsk2 * float(os.environ.get('UNDER_SHADE', '0.94'))
        dn7 = ((np.abs(X) - 0.0068) / 0.0024) ** 2 + ((Z - 0.6430) / 0.0018) ** 2      # pass 3: small, on the real openings
        nk7 = np.clip((1.0 - dn7) / 0.6, 0, 1); nk7 = nk7 * nk7 * (3 - 2 * nk7)
        cool = nsk2 * float(os.environ.get('NOST_COOL', '0.68')); cool = cool * 0.8 + cool.mean() * 0.2
        col7 = shade * (1 - nk7[..., None]) + cool * nk7[..., None]
        w7 = np.clip(ni.gaussian_filter(und7.astype(np.float32), 1.2) * 1.5, 0, 1)[..., None] * face_[..., None]
        out = out * (1 - w7) + col7 * w7
    # (8) philtrum top (the hole closed by tweak_pf7 HOLES: faces stretched over it carry mismatched texels): texels |x| < 6 mm,
    # z 0.629-0.640, front-facing, take the skin at |x| 6-10 mm of the same band, feathered
    ph8 = face_ & (np.abs(X) < 0.006) & (Z > 0.629) & (Z < 0.640) & (Y < -0.096) & (nrm[..., 2] >= -0.2)
    rg8 = face_ & (np.abs(X) > 0.006) & (np.abs(X) < 0.010) & (Z > 0.629) & (Z < 0.640) & (Y < -0.094)
    if ph8.any() and rg8.sum() > 20 and os.environ.get('PHIL', '1') == '1':      # off on the v3 paint (the hole is gone; it left a pale box)
        w8 = np.clip(ni.gaussian_filter(ph8.astype(np.float32), 1.0) * 1.5, 0, 1)[..., None] * face_[..., None]
        out = out * (1 - w8) + np.median(out[rg8], 0) * w8
    # (9) pass 3: the nose-bridge midline band (Meshy painted a highlight strip): |x| < 4 mm, z 0.648-0.705 scaled to the paint at
    # |x| 5-9 mm of the same height (row by row, feathered)
    bb9 = face_ & (np.abs(X) < 0.004) & (Z > 0.648) & (Z < 0.705) & (Y < -0.07)
    sd9 = face_ & (np.abs(X) > 0.005) & (np.abs(X) < 0.009) & (Z > 0.648) & (Z < 0.705) & (Y < -0.07)
    if bb9.any() and sd9.any() and os.environ.get('BRIDGE', '0') == '1':
        zb = np.round((Z - 0.648) / 0.004).astype(int); g9 = np.ones(out.shape)
        for zz in np.unique(zb[bb9]):
            mb = bb9 & (zb == zz); ms = sd9 & (np.abs(zb - zz) <= 1)
            if ms.sum() > 10: g9[mb] = np.clip(np.median(out[ms], 0) / np.maximum(np.median(out[mb], 0), 1), 0.8, 1.05)
        w9 = np.clip(ni.gaussian_filter(bb9.astype(np.float32), 1.5) * 1.3, 0, 1)[..., None]
        g9s = np.stack([ni.gaussian_filter(g9[..., c], 2.0) for c in range(3)], -1)
        out = out * (1 - w9) + out * g9s * w9
    # (9b) pass 3: the 1 mm mirror-seam line in the paint (sym_paint keeps the midline faces' own paint): texels |x| < 1.6 mm from the nose
    # tip to the hairline take the mean of the 8 nearest skin texels at |x| 2-3.5 mm (matched by height and depth)
    from scipy.spatial import cKDTree as _K9
    ln9 = face_ & (np.abs(X) < 0.0016) & (Z > 0.640) & (Z < 0.79) & (Y < -0.05)
    rg9 = face_ & (np.abs(X) > 0.002) & (np.abs(X) < 0.0035) & (Z > 0.635) & (Z < 0.795) & (Y < -0.05)
    if ln9.any() and rg9.sum() > 20:
        _q = np.c_[Y[ln9], Z[ln9]]; _, ii9 = _K9(np.c_[Y[rg9], Z[rg9]]).query(_q, k=24); _, jj9 = _K9(_q).query(_q, k=24)
        _ring = out[rg9][ii9].mean(1); _line = out[ln9][jj9].mean(1)
        out[ln9] = out[ln9] * np.clip(_ring / np.maximum(_line, 1), 0.75, 1.1)      # gain only: each texel keeps its own detail
    print('PASS2 seam line texels', int(ln9.sum()))
    # (10) pass 3: the hair parting (pale scalp line): hair texels within 5 mm of the midline, front/top, lighter than the hair 1-2 cm aside -> it
    pt10 = cov & hair & (np.abs(X) < 0.005) & (Y < 0.02) & (Z > 0.70)
    rf10 = cov & hair & (np.abs(X) > 0.010) & (np.abs(X) < 0.020) & (Y < 0.02) & (Z > 0.70)
    if pt10.any() and rf10.sum() > 50:
        hc10 = np.median(out[rf10], 0); l10 = out.mean(2)
        pl10 = pt10 & (l10 > hc10.mean() * 0.95)
        w10 = np.clip(ni.gaussian_filter(pl10.astype(np.float32), 1.0) * 1.4, 0, 1)[..., None] * hair[..., None]
        out = out * (1 - w10) + np.minimum(out, hc10 * 0.95) * w10
    else: pl10 = np.zeros_like(cov)
    # (11) neck graft (user review 2026-11-04, "soldered on her body"). h = texel height above the head/dress seam at its azimuth round the
    # neck. NECK_CLONE tiers (F7: both tiers - Meshy painted the chemise/collar colours on the bottom ~1.2 cm of the head) take
    # the skin texel NECK_DZ higher at the same place round the neck for h < 2.0 cm, eased out by 2.6 cm. Then every tier: the paint's low
    # frequencies within NECK_FEATHER of the seam are pulled to the neck's median skin (h 2-5.5 cm, below the jaw), so the seam meets the
    # chest skin region (tiers_pf2.py ramps it to the same skin) on one tone; texel detail kept.
    from scipy.spatial import cKDTree as _K8
    _k8 = np.round(co, 5); _, _i8 = np.unique(_k8, axis=0, return_inverse=True); _i8 = _i8.ravel(); _P8 = np.zeros((_i8.max() + 1, 3)); _P8[_i8] = co
    _hw8 = np.zeros(len(_P8), bool); _hw8[_i8[comp == hk]] = True; _dw8 = np.zeros(len(_P8), bool); _dw8[_i8[comp == names.index('dress')]] = True
    _S8 = _P8[_hw8 & _dw8]; _C8 = np.array([0.0, -0.001]); _az = np.arctan2(_S8[:, 1] - _C8[1], _S8[:, 0] - _C8[0]); _o8 = np.argsort(_az)
    _A8 = np.arctan2(Y - _C8[1], X - _C8[0]); hseam = Z - np.interp(_A8, _az[_o8], _S8[_o8, 2], period=2 * np.pi)
    neck8 = cov & (part == hk) & ~EYE & (Z < 0.60) & (hseam > -0.01)
    if os.environ.get('NECK', '1') == '1' and neck8.any():
        DZ = float(os.environ.get('NECK_DZ', '0.022'))
        if T_ in os.environ.get('NECK_CLONE', 'ab'):
            src8 = neck8 & (hseam > 0.020) & (hseam < 0.060); tg8 = neck8 & (hseam < float(os.environ.get('NECK_CLONE_H', '0.026')))
            _, j8 = _K8(pos[src8]).query(pos[tg8] + [0, 0, DZ]); cl8 = out[src8][j8]
            wc = np.zeros(cov.shape, np.float32); _ch = float(os.environ.get('NECK_CLONE_H', '0.026')); wc[tg8] = np.clip((_ch - hseam[tg8]) / 0.006, 0, 1)
            out[tg8] = out[tg8] * (1 - wc[tg8][:, None]) + cl8 * wc[tg8][:, None]
            print('PASS2 neck clone texels', int(tg8.sum()))
        NF = float(os.environ.get('NECK_FEATHER', '0.032'))
        ref8 = np.median(out[neck8 & (hseam > 0.02) & (hseam < 0.055)], 0)
        num = np.stack([ni.gaussian_filter(out[..., c] * neck8, 5) for c in range(3)], -1); den8 = ni.gaussian_filter(neck8.astype(np.float32), 5)[..., None]
        low = num / np.maximum(den8, 1e-3)
        # F7: the body has no free region channel for a per-tier chest-skin ramp, so both tiers' necks and the chest skin (tiers_pf7.py)
        # are feathered to one shared skin, NECK_TARGET (the mean of the two tiers' neck medians)
        tgt8 = np.array([float(v) for v in os.environ['NECK_TARGET'].split(',')]) if os.environ.get('NECK_TARGET') else ref8
        g8 = np.clip(tgt8 / np.maximum(low, 1), 0.7, 1.4)
        w8 = np.clip((NF - hseam) / NF, 0, 1); w8 = (w8 * w8 * (3 - 2 * w8)) * neck8
        out = out * (1 - w8[..., None]) + out * g8 * w8[..., None]
        # outliers on the bottom 1.5 cm (gold/brown specks on the midline slivers at the seam, every tier): the skin texel NECK_DZ higher
        ol8 = neck8 & (hseam < 0.015) & (np.abs(out - ref8).sum(2) > 45)
        ol8 = ni.binary_dilation(ol8, iterations=2) & neck8 & (hseam < 0.02)
        if ol8.any():
            src8 = neck8 & (hseam > 0.020) & (hseam < 0.060)
            _, j8 = _K8(pos[src8]).query(pos[ol8] + [0, 0, DZ]); out[ol8] = out[src8][j8]
        print('PASS2 neck outliers replaced', int(ol8.sum()))
        np.save(f'work/neck_ref_{T_}.npy', ref8)
        print('PASS2 neck feather texels', int((w8 > 0).sum()), 'neck skin', ref8.round(1).tolist())
    # (11b) the mirror-seam line in the neck paint (as 9b): texels |x| < 1.6 mm from the graft seam to the under-chin
    _zr = (Z > 0.515) & (Z < 0.600)
    ln9n = face_ & (np.abs(X) < 0.0016) & _zr & (Y < -0.02)
    rg9n = face_ & (np.abs(X) > 0.002) & (np.abs(X) < 0.0035) & _zr & (Y < -0.02)
    if ln9n.any() and rg9n.sum() > 20:
        _q = np.c_[Y[ln9n], Z[ln9n]]; _, ii9 = _K8(np.c_[Y[rg9n], Z[rg9n]]).query(_q, k=24); _, jj9 = _K8(_q).query(_q, k=24)
        _ring = out[rg9n][ii9].mean(1); _line = out[ln9n][jj9].mean(1)
        out[ln9n] = out[ln9n] * np.clip(_ring / np.maximum(_line, 1), 0.75, 1.15)
    print('PASS2 neck seam line texels', int(ln9n.sum()))
    # (12) mouth (user review 2026-11-04: "the black stuff on her upper lip"): the upper lip's down-facing underside over the closed slit was
    # painted at ~0.7x the lip front (198,82,72 vs 229,125,99), so with its own shading it read as a black band and a black triangle at the
    # tubercle. Underside texels (normal z < -0.3) take the lip-front colour with their own detail; the slit's crease texels take the lip tone
    # x MOUTH_CREASE (a soft line, not a cavity). Paint only.
    if os.environ.get('MOUTH_LIFT', '0') == '1':
        SLZ = float(os.environ.get('MOUTH_SLZ', '0.6220'))
        lipf = face_ & (np.abs(X) < 0.015) & (((Z > SLZ - 0.010) & (Z < SLZ - 0.002)) | ((Z > SLZ + 0.004) & (Z < SLZ + 0.010))) & (nrm[..., 1] < -0.6)
        _rg = (out[..., 0] - out[..., 1]) / np.maximum(out[..., 0], 1); lipr = lipf & (_rg > sk_rg + 0.12)      # lip-red texels only (B's painted lips are thinner)
        lc = np.median(out[lipr if lipr.sum() > 50 else lipf], 0)
        und12 = face_ & (np.abs(X) < float(os.environ.get('MOUTH_HALF_W', '0.016'))) & (Z > SLZ - 0.0005) & (Z < SLZ + 0.007) & (Y < -0.08) & (nrm[..., 2] < -0.3)
        cr12 = face_ & (np.abs(X) < float(os.environ.get('MOUTH_CREASE_W', '0.024'))) & (Z > SLZ - 0.0015) & (Z < SLZ + 0.0005) & (Y < -0.085) & ~und12
        l12 = out.mean(2); det = np.clip(l12 / np.maximum(ni.gaussian_filter(l12, 3), 1), 0.85, 1.15)[..., None]
        _xf = np.clip((float(os.environ.get('MOUTH_HALF_W', '0.016')) - np.abs(X)) / 0.004, 0, 1)      # eased out before the lip corners
        w12 = (np.clip(ni.gaussian_filter(und12.astype(np.float32), 1.0) * 1.5, 0, 1) * _xf)[..., None] * face_[..., None]
        out = out * (1 - w12) + lc * det * w12
        _xc = np.clip((float(os.environ.get('MOUTH_CREASE_W', '0.024')) - np.abs(X)) / float(os.environ.get('MOUTH_CREASE_EASE', '0.003')), 0, 1)      # to the corners (orange specks there)
        wc12 = (np.clip(ni.gaussian_filter(cr12.astype(np.float32), 0.8) * 1.5, 0, 1) * _xc)[..., None] * face_[..., None]
        out = out * (1 - wc12) + lc * float(os.environ.get('MOUTH_CREASE', '0.8')) * det * wc12
        print('PASS2 mouth underside texels', int(und12.sum()), 'crease', int(cr12.sum()), 'lip', lc.round(0).tolist())
    # (13) v3 head paint (2026-11-04, on the MOUTH2 geometry): Meshy painted a 3-4 mm dark open-mouth band on the lip line (texel luminance
    # 107-116 against lips 140-150 and skin 172) and orange specks at the corners. Within |x| < M3_HALF of the line LZ (eased out over the
    # last 4 mm), texels darker than the lips are lifted to the lip-red colour times a soft line profile (M3_LINE at the line, 1.0 by
    # M3_DZ above/below), their detail kept; corner texels far from both skin and lip colour take the lip/skin mix.
    if os.environ.get('MOUTH3', '0') == '1':
        LZ3 = float(os.environ.get('M3_LZ', '0.6250')); H3 = float(os.environ.get('M3_HALF', '0.022')); DZ3 = float(os.environ.get('M3_DZ', '0.0026'))
        _rg3 = (out[..., 0] - out[..., 1]) / np.maximum(out[..., 0], 1)
        lipz = face_ & (np.abs(X) < 0.014) & (np.abs(Z - LZ3) > 0.0035) & (np.abs(Z - LZ3) < 0.0075) & (Y < -0.085) & (_rg3 > sk_rg + 0.10)
        lc3 = np.median(out[lipz], 0) if lipz.sum() > 50 else np.array([200., 110., 100.])
        sk3 = np.median(out[face_ & (np.abs(X) > 0.026) & (np.abs(X) < 0.034) & (np.abs(Z - LZ3) < 0.004) & (Y < -0.07)], 0)
        xe = np.clip((H3 - np.abs(X)) / 0.004, 0, 1); dz = np.abs(Z - LZ3)
        prof = float(os.environ.get('M3_LINE', '0.78')) + (1 - float(os.environ.get('M3_LINE', '0.78'))) * np.clip(dz / DZ3, 0, 1) ** 1.5
        zone3 = face_ & (np.abs(X) < H3) & (dz < DZ3) & (Y < -0.085)
        l3 = out.mean(2); tgt3 = lc3[None, None] * prof[..., None]
        dark3 = zone3 & (l3 < tgt3.mean(2))
        det3 = np.clip(l3 / np.maximum(ni.gaussian_filter(l3, 2), 1), 0.9, 1.1)[..., None]
        w3 = (np.clip(ni.gaussian_filter(dark3.astype(np.float32), 0.8) * 1.4, 0, 1) * xe)[..., None] * face_[..., None]
        out = out * (1 - w3) + tgt3 * det3 * w3
        far = lambda c: np.linalg.norm(out - c, axis=2)
        cz = face_ & (np.abs(X) > H3 - 0.008) & (np.abs(X) < H3 + 0.003) & (dz < 0.004) & (Y < -0.07) & (far(lc3) > 60) & (far(sk3) > 60)
        wcz = np.clip(ni.gaussian_filter(cz.astype(np.float32), 0.8) * 1.6, 0, 1)[..., None] * face_[..., None]
        out = out * (1 - wcz) + (0.5 * lc3 + 0.5 * sk3) * wcz
        print('PASS2 v3 mouth line texels', int(dark3.sum()), 'corner specks', int(cz.sum()), 'lip', lc3.round(0).tolist(), 'skin', sk3.round(0).tolist())
    print('PASS2 nose underside texels', int(und7.sum()), 'philtrum', int(ph8.sum()), 'bridge', int(bb9.sum()), 'parting', int(pl10.sum()))
    print('PASS2 lips', int(red.sum()), 'light specks', int(light.sum()), 'nostril lift', int(lift.sum()), 'parting', int(pl.sum()), 'forehead gain', None if gfb is None else np.round(gfb, 3).tolist())
idx = ni.distance_transform_edt(~(ni.binary_erosion(cov, iterations=int(os.environ.get('PAD_ERODE', '1'))) if int(os.environ.get('PAD_ERODE', '1')) > 0 else cov), return_distances=False, return_indices=True); out = out[idx[0], idx[1]]      # v3: PAD_ERODE=0 (the erosion refilled tiny faces from neighbouring islands: orange specks on the lips)
Image.fromarray(np.clip(out, 0, 255).astype('u1')).save(DST)
print('HEADFIX', T_, 'hair hue', round(float(hm), 1), 'hair recoloured', int(bad.sum()), 'eyes', {k: (np.round(v[0], 4).tolist(), round(v[1], 4)) for k, v in ctr.items()},
      'eye texels', int(EYE.sum()), 'red rim', int(redrim.sum()), 'nostril front', int(fw.sum()), 'down', int(dw.sum()))
