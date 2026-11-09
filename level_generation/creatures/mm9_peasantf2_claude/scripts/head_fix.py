#!/usr/bin/env python3
"""Head paint fixes on textures/pf_head_<t>_sym.png -> pf_head_<t>_fix.png (per tier; work/headmap.npz from headmap.py). By 3D position:
- eyes: Meshy painted the eyeball cups white with a small iris, so with the lid opening of the mesh the eyes stared (white all round). Each
  eyeball is repainted: sclera, iris (tier colour) and pupil centred on the cup, an upper lid of skin with a lash line over the top of the iris,
  a lower lid below it (the mesh's lids stay where they are).
- mouth: the lips are a slit into a mouth cavity Meshy painted bright red; the cavity is painted dark, the lips toned down toward the skin.
- nostrils: the dark holes softened.
- hair: the scalp in the coif opening above the hairline (painted coif cream) and the temple strips beside it take the tier's hair colour,
  with the paint's luminance detail.
Args: [tiers] (default ab). Project folder."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
H = np.load('work/headmap.npz'); pos, nrm, face, cov = H['pos'], H['nrm'], H['face'], H['cov']
A = np.load('work/asm_frozen.npz'); D = np.load('work/uv_tex2.npz')
# eyeball faces: the head part's small connected components (the kept eyeball cups), via the frozen mesh
ac, at, acomp = A['co'], A['tri'], A['comp']; hk = [str(x) for x in A['names']].index('head')
par = np.arange(len(ac))
def find(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a, b, c in at[acomp[at[:, 0]] == hk]:
    ra = find(a); par[find(b)] = ra; par[find(c)] = ra
hv = np.where(acomp == hk)[0]; roots = np.array([find(v) for v in hv]); big = np.bincount(roots).argmax()
eyev = np.zeros(len(ac), bool); eyev[hv[roots != big]] = True
eyef = eyev[D['orig'][D['tri'][:, 0]]]
EYE = cov & eyef[np.maximum(face, 0)]
ctr = {}
for sg in (1, -1):
    q = ac[eyev & (ac[:, 0] * sg > 0)]; c = q.mean(0); ctr[sg] = (c, float(np.linalg.norm(q - c, axis=1).mean()))
print('eyes', {k: (v[0].round(4).tolist(), round(v[1], 4)) for k, v in ctr.items()}, 'texels', int(EYE.sum()))
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
X, Y, Z = pos[..., 0], pos[..., 1], pos[..., 2]
IRIS = {'a': np.array([84, 108, 132.]), 'b': np.array([92, 106, 116.])}
HAIR_LIGHT = {'b': 1.12}            # B's grey-white hair came out tan: lifted a little and desaturated toward grey
FLAT = np.zeros(cov.shape, np.float32)   # where the head normal map is flattened (its chart seams lit up as light lines in the smooth hair)
U, L = 0.13, -0.40                  # lid edges on the eyeball, in eyeball radii above / below its centre
for t in (sys.argv[1] if len(sys.argv) > 1 else 'ab'):
    im = np.asarray(Image.open(f'textures/pf_head_{t}_sym.png').convert('RGB'), np.float32)
    out = im.copy()
    # skin reference round the eyes (below the brows, outside the cups)
    skin_m = cov & ~EYE & (np.abs(np.abs(X) - 0.03) < 0.012) & (Z > 0.64) & (Z < 0.655) & (Y < -0.09)
    skin = np.median(im[skin_m], 0); print(t, 'eye skin', skin.round(0))
    # ---- eyes
    for sg in (1, -1):
        c, r = ctr[sg]; m = EYE & (X * sg > 0)
        d = (pos[m] - c) / r; dx = d[:, 0] * sg; dz = d[:, 2]
        rr = np.sqrt(dx ** 2 + (dz + 0.02) ** 2)
        noise = np.random.default_rng(1 if sg > 0 else 2).normal(0, 1, len(rr))
        scl = np.array([222, 212, 204.]) * (1 - 0.18 * ss(np.abs(dx), 0.35, 0.95))[:, None]       # whites shaded toward the corners
        ir = IRIS[t] * (0.85 + 0.25 * ss(rr, 0.10, 0.30))[:, None] * (1 + 0.06 * noise)[:, None]
        ir = ir * (1 - 0.45 * ss(rr, 0.27, 0.35))[:, None]                                          # limbal ring
        iris_w = 1 - ss(rr, 0.34, 0.38)
        col = scl * (1 - iris_w)[:, None] + ir * iris_w[:, None]
        pup = 1 - ss(rr, 0.12, 0.15); col = col * (1 - pup)[:, None] + np.array([18, 16, 18.]) * pup[:, None]
        hl = np.exp(-(((dx + 0.15) ** 2 + (dz - 0.12) ** 2) / 0.004)); col = col + (255 - col) * (0.55 * hl)[:, None]   # catchlight
        shade = 1 - 0.35 * np.exp(-((dz - (U - 0.05)) / 0.18) ** 2) * (dz < U)                    # shadow under the upper lid
        col = col * shade[:, None]
        lash = np.exp(-((dz - (U - 0.015)) / 0.045) ** 2) * (1 - 0.5 * ss(np.abs(dx), 0.6, 1.0))
        col = col * (1 - 0.85 * lash)[:, None] + np.array([42, 30, 28.]) * (0.85 * lash)[:, None]
        up = ss(dz, U, U + 0.06); lo = ss(dz, L, L - 0.06)
        wl = np.exp(-((dz - (L + 0.02)) / 0.035) ** 2); col = col * (1 - 0.35 * wl)[:, None] + np.array([196, 140, 128.]) * (0.35 * wl)[:, None]
        # the upper lid over the ball is the shadowed lid under the mesh's lash line (light skin there read as a pale band), the lower lid skin
        col = col * (1 - up)[:, None] + (skin * 0.42 + np.array([40, 28, 26.]) * 0.25) * up[:, None]
        col = col * (1 - lo)[:, None] + (skin * 0.88) * lo[:, None]
        out[m] = col
    # ---- lid rims: Meshy's red-orange ring round each eye goes toward the skin
    rim = np.zeros_like(cov)
    for sg in (1, -1):
        c, r = ctr[sg]; dd = np.linalg.norm(pos - c, axis=2); rim |= cov & ~EYE & (dd < r + 0.007) & (X * sg > 0)
    hsv0 = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype('u1')).convert('HSV'), np.float32) / 255
    sk_s = np.asarray(Image.fromarray(skin.astype('u1')[None, None]).convert('HSV'), np.float32)[0, 0, 1] / 255
    redrim = rim & ((hsv0[..., 0] * 360 < 22) | (hsv0[..., 0] * 360 > 340)) & (hsv0[..., 1] > sk_s + 0.06)
    rw = ni.gaussian_filter(redrim.astype(np.float32), 1.0)[..., None] * 0.75
    lum0 = out.mean(2, keepdims=True); out = out * (1 - rw) + skin * np.clip(lum0 / skin.mean(), 0.6, 1.1) * rw
    print(t, 'red rim texels', int(redrim.sum()))
    # ---- mouth: the cavity dark, the lips toned toward the skin
    box = cov & (np.abs(X) < 0.034) & (Z > 0.585) & (Z < 0.63)
    hsv = np.asarray(Image.fromarray(im.astype('u1')).convert('HSV'), np.float32) / 255
    h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    cav = box & (np.abs(X) < 0.021) & (Y > -0.118) & (((h < 16) | (h > 335)) & (s > 0.42))       # the bright red cavity only (cheeks are not red)
    cav = ni.binary_closing(cav, iterations=2) & box & (np.abs(X) < 0.021) & (Y > -0.118)
    cw = ni.gaussian_filter(cav.astype(np.float32), 1.0)
    out = out * (1 - 0.9 * cw[..., None]) + np.array([118, 58, 54.]) * (0.9 * cw[..., None])      # lip-shadow tone: a dark gap read as an open mouth
    lips = box & ~cav & (((h < 16) | (h > 335)) & (s > 0.35))
    lw = ni.gaussian_filter(lips.astype(np.float32), 1.2)[..., None]
    lipskin = np.array([178, 92, 88.]) * 0.6 + skin * 0.4
    out = out * (1 - 0.5 * lw) + lipskin * np.clip(im.mean(2, keepdims=True) / im[lips].mean(), 0.7, 1.2) * (0.5 * lw)
    # ---- nostrils
    # nose underside (faces turned down round the nostrils): shaded by the mesh already, the paint's orange-brown lifted toward the skin
    nb = cov & (np.abs(X) < 0.022) & (Z > 0.618) & (Z < 0.64) & (Y < -0.11) & (nrm[..., 2] < -0.35)
    nw = ni.gaussian_filter(nb.astype(np.float32), 1.0)[..., None] * 0.55
    out = out * (1 - nw) + skin * nw
    # ---- hair: scalp above the hairline inside the coif opening and the temple strips
    hairref = cov & (np.abs(X) < 0.03) & (Z > 0.712) & (Z < 0.735) & (Y < -0.10)
    hc = np.median(im[hairref], 0)
    if t in HAIR_LIGHT: g = hc.mean(); hc = np.clip((hc * 0.35 + g * 0.65) * HAIR_LIGHT[t], 0, 235)
    scalp = cov & ~EYE & (Z > 0.728)                 # the whole crown under the coif (a cut at y -0.02 showed as light lines in the opening)
    temple = cov & ~EYE & (((np.abs(X) > 0.058) & (Z > 0.645)) | ((np.abs(X) > 0.045) & (Z > 0.69))) & (Y > -0.105) & (Y < 0.06)
    vsk = skin.max() / 255; ssk = (skin.max() - skin.min()) / max(skin.max(), 1)
    hairlike = cov & ~EYE & (Z > 0.695) & (Y < -0.02) & ((v < 0.86 * vsk) | (s < ssk - 0.08))   # the painted fringe, so scalp and fringe match
    creamy = cov & ~EYE & (s < 0.28) & (v > 0.55) & (Z > 0.69) & (Y < -0.02)        # coif cream Meshy painted on the head at the hairline corners
    hm = ni.gaussian_filter((scalp | temple | creamy | hairlike).astype(np.float32), 1.5)[..., None]
    idx0 = ni.distance_transform_edt(~ni.binary_erosion(cov, iterations=1), return_distances=False, return_indices=True)
    lum = im[idx0[0], idx0[1]].mean(2, keepdims=True); lb = ni.gaussian_filter(lum, (8, 8, 0)) + 1      # padded first: no seams from the gutters
    hair = hc * np.clip(lum / lb, 0.75, 1.25)
    out = out * (1 - hm) + hair * hm
    # gutters refilled from the nearest chart texel (the recolour's blur left the old colour in them: light seams in the hair)
    idx = ni.distance_transform_edt(~ni.binary_erosion(cov, iterations=1), return_distances=False, return_indices=True); out = out[idx[0], idx[1]]
    print(t, 'hair', hc.round(0), 'scalp', int(scalp.sum()), 'temple', int(temple.sum()), 'lips', int(lips.sum()), 'cavity', int(cav.sum()), 'nostril', int(nb.sum()))
    FLAT = np.maximum(FLAT, np.maximum(hm[..., 0], np.clip(nw[..., 0] * 1.8, 0, 1)))
    Image.fromarray(np.clip(out, 0, 255).astype('u1')).save(f'textures/pf_head_{t}_fix.png')
NM = np.asarray(Image.open('textures/pf_head_normal.png').convert('RGB'), np.float32)
F_ = ni.zoom(FLAT, NM.shape[0] / FLAT.shape[0], order=1)[..., None] if NM.shape[0] != FLAT.shape[0] else FLAT[..., None]
Image.fromarray(np.clip(NM * (1 - F_) + np.array([128, 128, 255.]) * F_, 0, 255).astype('u1')).save('textures/pf_head_normal_fix.png')
print('normal flattened texels', int((FLAT > 0.5).sum()))
print('HEADFIX')
