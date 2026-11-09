#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the Moon Cleric (CLAUDE_CREATURE_TEXTURES.md), adapted from
mm6_natm_claude/scripts/compose_natm.py. Run after uv_raster.py (UVMap and HeadUV at 1024) and bake_ao_natm.py.

Tiers: palettes 37 Acolyte (green) / 38 Cleric (blue) / 39 Priest (red) (sprite frame tables m171/m172/m173) recolour two
regions, as the native palette ranges do (mm7_m170/variants.json): R = the robe (indices 165-227: the green cloth of the
robe top, sleeves and skirt), G = the two back banners (indices 139-164, dark olive). Skin, gold (helmet, crescent,
frame, trim, rope), the black-and-gold collar and the turquoise beads stay.
- Robe texels: garments 1/2 in green hues; gold trim (yellow hue, bright) stays out. Banners: garment 10, all texels.
- Skin (the claws in the body set, the face in the head set): one ashen grey albedo SKIN times Meshy's fine shading
  (luminance over its masked blur), mixed SKIN_MIX over Meshy's paint (it painted purple-grey patches).
- AO graded into the base colour (strength 0.4, floor 0.45); ORM red = per-class specular mask (openyamm_specular_mask),
  G roughness by class (+ half of Meshy's variation), B 0.
- Ramps per tier from the ORIGINAL indexed bitmaps (assets_dev/engine/sprites/m170*.bmp) in each palette: the pixels
  whose index lies in the region's range, sorted by luminance, rank-matched to the region's texel luminance (2nd-98th
  percentile range), gain RAMP_GAIN (sprites carry baked shading).
- Material classes (8-bit, 1K): 1 skin, 2 hair, 6 eye, 8 cloth, 9 metal (gold), 11 other (turquoise beads, collar enamel).
Writes textures/m170_*."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
N = 1024
SKIN = np.array([128, 126, 130]) / 255
SKIN_MIX = 0.8; RAMP_GAIN = 1.35
PALS = {'m170_a': 37, 'm170_b': 38, 'm170_c': 39}
V = json.load(open(HERE.parent / 'mm7_m170' / 'variants.json'))['variants'][0]['regions']
IDX = {'robe': V[0]['native_indices'], 'banner': V[1]['native_indices']}
SPEC = {'skin': 0.35, 'hair': 0.3, 'cloth': 0.15, 'gold': 1.0, 'bead': 0.7, 'eye': 0.9, 'collar': 0.6}
ROUGH = {'skin': 0.6, 'hair': 0.55, 'cloth': 0.88, 'gold': 0.32, 'bead': 0.35, 'eye': 0.2, 'collar': 0.45}


def load(path, mode='RGB', n=N):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((n, n), Image.LANCZOS) if im.size != (n, n) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]; return out


lin = R.srgb_to_linear
def srgb(x):
    x = np.asarray(x, np.float64); return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.maximum(x, 0), 1 / 2.4) - 0.055)


def repaint_skin(img, m, sigma=6.0):
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma); den = ndimage.gaussian_filter(m.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** 1.15, 0.5, 1.5)
    new = srgb(np.clip(lin(SKIN)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - SKIN_MIX) + new * SKIN_MIX
    return out


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


# ---------------------------------------------------------------- native region colours per tier (indexed bitmaps)
src = json.load(open(HERE.parent / 'mm7_m170' / 'sources.json'))['sources']
frames = [n for n, s in src.items() if s.get('referenced') and n[4] in 'swa']          # standing, walking, attack
pals = {k: np.frombuffer(open(REPO / f'assets_dev/worlds/mm7/textures/pal{p:03d}.act', 'rb').read()[:768], np.uint8)
        .reshape(256, 3).astype(np.float64) / 255 for k, p in PALS.items()}
native = {r: {k: [] for k in PALS} for r in IDX}
for n in frames:
    ix = np.asarray(Image.open(REPO / src[n]['path']))
    assert ix.ndim == 2, n
    for r, ids in IDX.items():
        sel = ix[np.isin(ix, ids)]
        for k in PALS:
            native[r][k].append(pals[k][sel])
for r in IDX:
    for k in PALS:
        X = np.concatenate(native[r][k]); L = R.luminance(X); keep = L > 0.01
        X, L = X[keep], L[keep]; o = np.argsort(L); native[r][k] = X[o]
print('NATIVE pixels', {r: len(native[r]['m170_a']) for r in IDX}, 'frames', len(frames))


def ramps_for(region, texel_lum):
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    out = {}
    for k in PALS:
        X = native[region][k]; cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            c = X[min(len(X) - 1, int(q * (len(X) - 1)))]
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(c * RAMP_GAIN, 0, 1)), 0, 1)])
        out[k] = {'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}
    return out


# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'retexture_v1'
base = load(M / 'texture_urls_0_base_color.png'); normal = load(M / 'texture_urls_0_normal.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); gar, piece, pos = Rz['garment'], Rz['piece'], Rz['pos']; cov = gar >= 0
hue, sat, val = hsv(base)
green = (hue > 60) & (hue < 170) & (sat > 0.25) & (val > 0.06)
yellow = (hue > 25) & (hue < 62) & (sat > 0.3) & (val > 0.45)
# the robe garments hold only cloth and its gold trim: every texel that is not gold-yellow is robe (a green-hue test
# left dark folds and shadowed texels green on the blue/red tiers); the trim's soft edge stays out by one texel
trim = cov & np.isin(gar, [1, 2]) & (yellow | ((hue > 25) & (hue < 62) & (sat > 0.25) & (val > 0.3)))
robe = cov & np.isin(gar, [1, 2]) & ~ndimage.binary_dilation(trim, iterations=1)
banner = cov & (gar == 10)
skin = cov & (gar == 0)
hair = cov & (gar == 3) & (val < 0.25) & (sat < 0.5)
bead = cov & (((hue > 165) & (hue < 200) & (sat > 0.35)) | ((gar == 11) & (sat > 0.35) & (hue > 160) & (hue < 210)))
collar_dark = cov & (gar == 6) & (val < 0.2)
gold = cov & ~robe & ~banner & ~skin & ~hair & ~bead & ~collar_dark & ~np.isin(gar, [1, 2, 8]) | (cov & np.isin(gar, [1, 2, 8]) & yellow)
rope = cov & (gar == 8) & ~gold
g = repaint_skin(base, skin)


def gold_grade(img, m):
    """Meshy's gold reads pale cream next to the native's rich gold (viewer review): saturation x GOLD_SAT (+0.08),
    value x GOLD_VAL, hue pulled halfway to GOLD_HUE."""
    h, s_, v = hsv(img)
    h2 = h + ((GOLD_HUE - h + 180) % 360 - 180) * 0.5
    s2 = np.clip(s_ * GOLD_SAT + 0.08, 0, 1); v2 = np.clip(v * GOLD_VAL, 0, 1)
    hsv8 = np.stack([h2 / 360, s2, v2], -1)
    rgb = np.asarray(Image.fromarray((hsv8 * 255 + 0.5).astype(np.uint8), 'HSV').convert('RGB'), np.float64) / 255
    out = img.copy(); out[m] = rgb[m]; return out


GOLD_HUE, GOLD_SAT, GOLD_VAL = 40.0, 1.35, 0.9
g = gold_grade(g, gold & (sat > 0.15))
ao = load(HERE / 'work' / 'ao_UVMap.png', 'L')
g = ao_grade(g, ao, cov)
cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
for name, m, c in (('skin', skin, 1), ('hair', hair, 2), ('cloth', robe | banner | rope, 8), ('gold', gold, 9), ('bead', bead, 11),
                   ('collar', collar_dark, 11)):
    cls[m] = c; spec[m] = SPEC[name]; rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
print('CLASSES body texels', {n: int(m.sum()) for n, m in (('robe', robe), ('banner', banner), ('skin', skin), ('hair', hair),
                                                         ('gold', gold), ('bead', bead), ('collar', collar_dark), ('covered', cov))})
robe_ramps = ramps_for('robe', R.luminance(g[robe])); banner_ramps = ramps_for('banner', R.luminance(g[banner]))
save(pad(g, cov), T / 'm170_basecolor_1k.png'); save(pad(normal, cov), T / 'm170_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm170_metal_rough_1k.png')
# masks padded like the colour (nearest island texel into the gutters) before the soft edge (gob2 seam lesson)
R.write_mask([ndimage.gaussian_filter(pad(robe.astype(float), cov), 0.7),
              ndimage.gaussian_filter(pad(banner.astype(float), cov), 0.7)], T / 'm170_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm170_material_classes.png')
# ---------------------------------------------------------------- head set
HM = HERE / 'meshy' / 'head_retexture_v1'
materials = [{'base': 'M170_A', 'prefix': 'M170', 'mask': 'm170_region_mask.png', 'regions': ['robe', 'banner'],
              'palettes': PALS, 'ramps': {k: [robe_ramps[k], banner_ramps[k]] for k in PALS}}]
if (HM / 'texture_urls_0_base_color.png').exists():
    hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png')
    Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hg_ = Rh['garment']; hcov = hg_ >= 0
    hh, hs, hv = hsv(hb)
    eye = hcov & (hg_ == 4)
    hgold = hcov & (hh > 28) & (hh < 62) & (hs > 0.35) & (hv > 0.4)
    hhair = hcov & (hv < 0.16)
    hskin = hcov & (hg_ == 0) & ~hgold & ~hhair
    hgr = ao_grade(gold_grade(repaint_skin(hb, hskin), hgold), load(HERE / 'work' / 'ao_HeadUV.png', 'L'), hcov, strength=0.4)
    print('CLASSES head texels', {'skin': int(hskin.sum()), 'eye': int(eye.sum()), 'gold': int(hgold.sum()), 'hair': int(hhair.sum()),
                                  'covered': int(hcov.sum())},
          'skin before', np.round(np.median(hb[hskin], 0) * 255), 'after', np.round(np.median(hgr[hskin], 0) * 255))
    hspec = np.where(hskin, SPEC['skin'], 0.3); hspec[eye] = SPEC['eye']; hspec[hgold] = SPEC['gold']
    hrgh = np.where(hskin, ROUGH['skin'], 0.6); hrgh[eye] = ROUGH['eye']; hrgh[hgold] = ROUGH['gold']
    save(pad(hgr, hcov), T / 'm170_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm170_head_normal_1k.png')
    save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm170_head_metal_rough_1k.png')
    hc = np.zeros((N, N), np.uint8); hc[hcov] = 11; hc[hskin] = 1; hc[eye] = 6; hc[hgold] = 9; hc[hhair] = 2
    Image.fromarray(hc).save(T / 'm170_head_material_classes.png')
cfg = {'variants': list(PALS), 'materials': materials}
(T / 'm170_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'robe mid', [round(x, 3) for x in robe_ramps[k]['colors'][8]], 'banner mid',
          [round(x, 3) for x in banner_ramps[k]['colors'][8]])
