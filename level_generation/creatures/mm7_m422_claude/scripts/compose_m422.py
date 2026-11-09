#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the Vampire (palettes 99/104/105 from ../mm7_m422/variants.json for
monsters 415/416/417; adapted from the Mage's compose, mm7_m422_claude/scripts/compose_m422.py). Run after uv_raster.py
(UVMap and HeadUV at 1024) and bake_ao_natm.py.
Regions (native palette ranges, ../mm7_m422/variants.json): R = the coat (indices 137-169: green / royal blue / red),
G = the cape and its stand-up collar (202-239: dark green / burgundy / black), B = the hair (85-101, head set only;
charcoal in every tier, kept as a region so the tiers stay exact). Skin, gold (belt, buckle, front strip, clasps,
trims), the white shirt and cuffs and the black trousers and boots stay.
- Coat texels: garments 1/2 (coat top, sleeves, skirt) minus gold (yellow hue) and the white cuffs/shirt (low
  saturation, bright). Cape texels: garment 10 and the collar piece 28 minus the gold trims. Hair: piece 3.
- Skin (the hands in the body set, the face in the head set): one pale albedo SKIN (the native face pixels, mean
  195/181/170, x1.1) times Meshy's fine shading, mixed SKIN_MIX over Meshy's paint (the head paint came out warm).
- AO graded into the base colour (strength 0.4, floor 0.45); ORM red = per-class specular mask (openyamm_specular_mask),
  G roughness by class (+ half of Meshy's variation), B 0.
- Ramps per tier from the ORIGINAL indexed bitmaps (assets_dev/engine/sprites/m422*.bmp) in each palette: the pixels
  whose index lies in the region's range, sorted by luminance, rank-matched to the region's texel luminance (2nd-98th
  percentile range), gain per tier and region from textures/m422_ramp_gains.json (tier_match.py).
- Material classes (8-bit, 1K): 1 skin, 2 hair, 6 eye, 8 cloth/leather, 9 metal (gold), 11 other (white shirt linen).
Writes textures/m422_*."""
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
SKIN = np.array([215, 199, 187]) / 255
SKIN_MIX = 0.8
# per-tier, per-region ramp gain (sRGB multiplier on the native colours), calibrated by scripts/tier_match.py so the
# RENDERED median luminance in the viewer matches each tier's native pixels (review 2026-10-20: the guide's 1.35 made
# the coats flat bright green / red and the hair light brown / mauve); textures/m422_ramp_gains.json
_GF = HERE / 'textures' / 'm422_ramp_gains.json'
GAINS = json.load(open(_GF)) if _GF.exists() else {}
gain = lambda region, k: float(GAINS.get(region, {}).get(k, 1.35))
PALS = {'m422_a': 99, 'm422_b': 104, 'm422_c': 105}
_V = {r['name']: r for r in json.load(open(HERE.parent / 'mm7_m422' / 'variants.json'))['regions']}
IDX = {'robe': _V['blue_coat']['palette_indices'], 'cape': _V['burgundy_cape']['palette_indices'], 'beard': _V['hair']['palette_indices']}
SPEC = {'skin': 0.35, 'hair': 0.3, 'cloth': 0.15, 'gold': 1.0, 'eye': 0.9, 'shirt': 0.15}
ROUGH = {'skin': 0.6, 'hair': 0.55, 'cloth': 0.88, 'gold': 0.32, 'eye': 0.2, 'shirt': 0.8}


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
src = json.load(open(HERE.parent / 'mm7_m422' / 'sources.json'))['sources']
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
BLACK = {}
for r in IDX:
    for k in PALS:
        X = np.concatenate(native[r][k]); L = R.luminance(X); keep = L > 0.01
        BLACK[(r, k)] = float(1 - keep.mean()) > 0.7          # the Elder Vampire's cape: palette 105 draws it pure black
        X, L = X[keep], L[keep]; o = np.argsort(L); native[r][k] = X[o]
print('BLACK regions (> 70 % pure black native pixels)', [rk for rk, b in BLACK.items() if b])
# a pure-black native region keeps the fold shading of the texture as a neutral near-black ramp (linear BLACK_LO..HI,
# sRGB about 12..52 after the tier review; renders median ~30)
# sRGB about 25..80) instead of the few lit pixels left after dropping the black ones (they made the cape mid grey)
BLACK_LO, BLACK_HI = 0.004, 0.035
print('NATIVE pixels', {r: len(native[r]['m422_a']) for r in IDX}, 'frames', len(frames))


def ramps_for(region, texel_lum):
    lo, hi = np.percentile(texel_lum, [2, 98]); srt = np.sort(texel_lum)
    out = {}
    for k in PALS:
        if BLACK[(region, k)]:
            v = [BLACK_LO + (BLACK_HI - BLACK_LO) * (i / 15) ** 1.6 for i in range(16)]
            out[k] = {'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': [[round(x, 6)] * 3 for x in v]}
            continue
        X = native[region][k]; cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            c = X[min(len(X) - 1, int(q * (len(X) - 1)))]
            cols.append([round(float(v), 6) for v in np.clip(lin(np.clip(c * gain(region, k), 0, 1)), 0, 1)])
        out[k] = {'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}
    return out


# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / json.load(open(HERE / 'creature.json')).get('body_retexture', 'retexture_v1')   # retexture_v2: the final mesh (2026-10-20)
base = load(M / 'texture_urls_0_base_color.png'); normal = load(M / 'texture_urls_0_normal.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); gar, pos = Rz['garment'], Rz['pos']; cov = gar >= 0
hue, sat, val = hsv(base)
pc = Rz['piece']
gold = cov & (hue > 25) & (hue < 65) & (sat > 0.28) & (val > 0.35)
goldish = cov & (hue > 22) & (hue < 68) & (sat > 0.2) & (val > 0.25)
white = cov & (sat < 0.18) & (val > 0.62)
coat_g = cov & np.isin(gar, [1, 2])
robe = coat_g & ~ndimage.binary_dilation(goldish, iterations=1) & ~white
cape = cov & ((gar == 10) | (pc == 28)) & ~ndimage.binary_dilation(goldish, iterations=1)
shirt = cov & ((pc == 9) | (white & coat_g))
skin = cov & (gar == 0)
shoe = cov & (gar == 15)
g = repaint_skin(base, skin)


def gold_grade(img, m):
    h, s_, v = hsv(img)
    h2 = h + ((GOLD_HUE - h + 180) % 360 - 180) * 0.5
    s2 = np.clip(s_ * GOLD_SAT + 0.08, 0, 1); v2 = np.clip(v * GOLD_VAL, 0, 1)
    rgb = np.asarray(Image.fromarray((np.stack([h2 / 360, s2, v2], -1) * 255 + 0.5).astype(np.uint8), 'HSV').convert('RGB'), np.float64) / 255
    out = img.copy(); out[m] = rgb[m]; return out


# m422 tier review: the Meshy gold rendered at median sRGB 225/185/72 against the native 134/92/44 (palette 104):
# darker, warmer, less saturated
GOLD_HUE, GOLD_SAT, GOLD_VAL = 36.0, 1.05, 0.62
g = gold_grade(g, gold)
g = ao_grade(g, load(HERE / 'work' / 'ao_UVMap.png', 'L'), cov)
cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
for name, m, c in (('skin', skin, 1), ('cloth', robe | cape | shoe, 8), ('gold', gold, 9), ('shirt', shirt, 11)):
    cls[m] = c; spec[m] = SPEC[name]; rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
print('CLASSES body texels', {n: int(m.sum()) for n, m in (('coat', robe), ('cape', cape), ('skin', skin), ('gold', gold), ('shirt', shirt), ('covered', cov))})
save(pad(g, cov), T / 'm422_basecolor_1k.png'); save(pad(normal, cov), T / 'm422_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm422_metal_rough_1k.png')
Image.fromarray(cls).save(T / 'm422_material_classes.png')
# ---------------------------------------------------------------- head set (face, hair, beard, braids)
HM = HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png')
Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hg_, hpos = Rh['garment'], Rh['pos']; hcov = hg_ >= 0
hh, hs, hv = hsv(hb)
eye = hcov & (hg_ == 4)
beard = hcov & (Rh['piece'] == 3)                    # the hair piece (region B)
hskin = hcov & (hg_ == 0) & ~beard & ~eye
hgr = ao_grade(repaint_skin(hb, hskin), load(HERE / 'work' / 'ao_HeadUV.png', 'L'), hcov, strength=0.4)
print('CLASSES head texels', {'skin': int(hskin.sum()), 'hair': int(beard.sum()), 'eye': int(eye.sum()), 'covered': int(hcov.sum())})
hspec = np.where(hskin, SPEC['skin'], 0.3); hspec[eye] = SPEC['eye']
hrgh = np.where(hskin, ROUGH['skin'], 0.6); hrgh[eye] = ROUGH['eye']
save(pad(hgr, hcov), T / 'm422_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm422_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm422_head_metal_rough_1k.png')
hc = np.zeros((N, N), np.uint8); hc[hcov] = 11; hc[hskin] = 1; hc[eye] = 6; hc[beard] = 2
Image.fromarray(hc).save(T / 'm422_head_material_classes.png')
# ---------------------------------------------------------------- ramps (one list for body and head) and masks
rr = ramps_for('robe', R.luminance(g[robe])); rc = ramps_for('cape', R.luminance(g[cape])); rb = ramps_for('beard', R.luminance(hgr[beard]))
ramps = {k: [rr[k], rc[k], rb[k]] for k in PALS}
z = np.zeros((N, N))
R.write_mask([ndimage.gaussian_filter(pad(robe.astype(float), cov), 0.7), ndimage.gaussian_filter(pad(cape.astype(float), cov), 0.7), z],
             T / 'm422_region_mask.png', size=N)
R.write_mask([z, z, ndimage.gaussian_filter(pad(beard.astype(float), hcov), 0.7)], T / 'm422_head_region_mask.png', size=N)
cfg = {'variants': list(PALS),
       'materials': [{'base': 'M422_A', 'prefix': 'M422', 'mask': 'm422_region_mask.png', 'regions': ['coat', 'cape', 'hair'],
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'M422Head_A', 'prefix': 'M422Head', 'mask': 'm422_head_region_mask.png', 'regions': ['coat', 'cape', 'hair'],
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm422_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'coat', [round(x, 3) for x in rr[k]['colors'][8]], 'cape', [round(x, 3) for x in rc[k]['colors'][8]],
          'hair', [round(x, 3) for x in rb[k]['colors'][8]])
