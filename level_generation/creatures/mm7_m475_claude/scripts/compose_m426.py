#!/usr/bin/env python3
"""Textures, region mask and tier ramps for the Warlock (palettes 107/108/109; one region from
mm7_m426/variants.json: R the crimson gown, indices 152-242 -> red / violet / green; the navy cape, copper hair and
gold stay). Adapted from the Mage's compose (mm7_m274_claude), itself from the Sun Cleric (CLAUDE_CREATURE_TEXTURES.md), adapted from the Moon Cleric's
compose (mm7_m170_claude/scripts/compose_m170.py). Run after uv_raster.py (UVMap and HeadUV at 1024) and bake_ao_natm.py.
Sun Cleric differences: ONE tier region, the stole (native indices 228-238: teal in palette 40, violet in 41, black in
42; mm7_m174/variants.json); the robe's vertical stripes (orange-red on deep red, lost in Meshy's paint) are re-painted
by the angle round the body axis (STRIPES per turn) times Meshy's fine shading; skin is the tan of the bare forearms.
The original Moon Cleric notes follow.

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
Writes textures/m174_*."""
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
SKIN = np.array([212, 160, 128]) / 255
SKIN_MIX = 0.8; RAMP_GAIN = 1.35
PALS = {'m426_a': 107, 'm426_b': 108, 'm426_c': 109}
_V = json.load(open(HERE.parent / 'mm7_m426' / 'variants.json'))['regions']
IDX = {'gown': _V[0]['palette_indices']}
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
src = json.load(open(HERE.parent / 'mm7_m426' / 'sources.json'))['sources']
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
print('NATIVE pixels', {r: len(native[r]['m426_a']) for r in IDX}, 'frames', len(frames))


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
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); gar, pos = Rz['garment'], Rz['pos']; cov = gar >= 0
hue, sat, val = hsv(base)
gold = cov & (hue > 28) & (hue < 65) & (sat > 0.3) & (val > 0.4)
gown = cov & np.isin(gar, [1, 2]) & ((hue < 11) | (hue > 335)) & (sat > 0.45) & ~ndimage.binary_dilation(gold, iterations=1)
gown = ndimage.binary_closing(gown, iterations=2) & cov & np.isin(gar, [1, 2]) & ~gold
cape = cov & (hue > 200) & (hue < 290) & (sat > 0.15)
hair = cov & (hue >= 11) & (hue < 30) & (sat > 0.55) & (val > 0.25) & (pos[..., 1] > -0.05) & (pos[..., 2] > 1.0)
skin = cov & np.isin(gar, [1, 2, 15]) & ~gown & ~gold & ~cape & ~hair & (sat < 0.6) & (hue < 40)
g = repaint_skin(base, skin)


def gold_grade(img, m):
    h, s_, v = hsv(img)
    h2 = h + ((GOLD_HUE - h + 180) % 360 - 180) * 0.5
    s2 = np.clip(s_ * GOLD_SAT + 0.08, 0, 1); v2 = np.clip(v * GOLD_VAL, 0, 1)
    rgb = np.asarray(Image.fromarray((np.stack([h2 / 360, s2, v2], -1) * 255 + 0.5).astype(np.uint8), 'HSV').convert('RGB'), np.float64) / 255
    out = img.copy(); out[m] = rgb[m]; return out


GOLD_HUE, GOLD_SAT, GOLD_VAL = 42.0, 1.25, 1.0
g = gold_grade(g, gold)
g = ao_grade(g, load(HERE / 'work' / 'ao_UVMap.png', 'L'), cov)
cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
for name, m, c in (('skin', skin, 1), ('hair', hair, 2), ('cloth', gown | cape, 8), ('gold', gold, 9)):
    cls[m] = c; spec[m] = SPEC[name]; rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
print('CLASSES body texels', {n: int(m.sum()) for n, m in (('gown', gown), ('cape', cape), ('hair', hair), ('skin', skin), ('gold', gold), ('covered', cov))})
save(pad(g, cov), T / 'm426_basecolor_1k.png'); save(pad(normal, cov), T / 'm426_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm426_metal_rough_1k.png')
Image.fromarray(cls).save(T / 'm426_material_classes.png')
gr = ramps_for('gown', R.luminance(g[gown]))
R.write_mask([ndimage.gaussian_filter(pad(gown.astype(float), cov), 0.7)], T / 'm426_region_mask.png', size=N)
materials = [{'base': 'M426_A', 'prefix': 'M426', 'mask': 'm426_region_mask.png', 'regions': ['gown'], 'palettes': PALS,
              'ramps': {k: [gr[k]] for k in PALS}}]
# ---------------------------------------------------------------- head set (face, hair; no tier region)
HM = HERE / 'meshy' / 'head_retexture_v1'
if (HM / 'texture_urls_0_base_color.png').exists():
    hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png')
    Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hg_ = Rh['garment']; hcov = hg_ >= 0
    hh, hs, hv = hsv(hb)
    eye = hcov & (hg_ == 4)
    hhair = hcov & (hh >= 8) & (hh < 32) & (hs > 0.55)
    hgold = hcov & (hg_ == 5)
    hskin = hcov & ~hhair & ~eye & ~hgold & ((hs < 0.6) | ((hh > 30) & (hh < 65)))   # gold streaks painted on the cheek -> skin
    lids = hcov & np.isin(Rh['piece'], [8, 9])         # crescent shells under the eyes, painted gold by Meshy
    hskin |= lids
    hb = hb.copy(); hb[lids] = np.median(hb[hskin & ~lids], 0)
    # the crescents are also painted on the face skin under those shells (dropped at export): refill that patch from
    # the surrounding skin (normalised blur over the skin outside the patch)
    hp = Rh['pos']; ax_ = np.abs(hp[..., 0])
    under = hcov & (Rh['piece'] == 0) & hskin & (ax_ > 0.010) & (ax_ < 0.068) & (hp[..., 2] > 1.512) & (hp[..., 2] < 1.562) & (hp[..., 1] < -0.07)
    src_ = hskin & ~under & ~lids
    num = np.stack([ndimage.gaussian_filter(np.where(src_, hb[..., c], 0.0), 6) for c in range(3)], -1)
    den = ndimage.gaussian_filter(src_.astype(float), 6)[..., None]
    fill = num / np.maximum(den, 1e-4)
    hb[under] = np.where(den[under] > 0.05, fill[under], np.median(hb[src_], 0))
    print('UNDEREYE texels refilled', int(under.sum()))
    hao = load(HERE / 'work' / 'ao_HeadUV.png', 'L').copy(); hn = hn.copy()
    if under.any():                                  # the AO and normals were baked with the shells there: refill too
        aon = ndimage.gaussian_filter(np.where(src_, hao, 0.0), 6) / np.maximum(den[..., 0], 1e-4)
        hao[under] = np.where(den[under, 0] > 0.05, aon[under], np.median(hao[src_]))
        for c in range(3):
            nn = ndimage.gaussian_filter(np.where(src_, hn[..., c], 0.0), 6) / np.maximum(den[..., 0], 1e-4)
            hn[..., c][under] = np.where(den[under, 0] > 0.05, nn[under], np.median(hn[..., c][src_]))
    hgr = ao_grade(repaint_skin(hb, hskin), hao, hcov, strength=0.4)
    print('CLASSES head texels', {'skin': int(hskin.sum()), 'hair': int(hhair.sum()), 'eye': int(eye.sum()), 'covered': int(hcov.sum())})
    hspec = np.where(hskin, SPEC['skin'], 0.3); hspec[eye] = SPEC['eye']; hspec[hgold] = SPEC['gold']
    hrgh = np.where(hskin, ROUGH['skin'], 0.55); hrgh[eye] = ROUGH['eye']; hrgh[hgold] = ROUGH['gold']
    save(pad(hgr, hcov), T / 'm426_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm426_head_normal_1k.png')
    save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm426_head_metal_rough_1k.png')
    hc = np.zeros((N, N), np.uint8); hc[hcov] = 11; hc[hskin] = 1; hc[eye] = 6; hc[hhair] = 2; hc[hgold] = 9
    Image.fromarray(hc).save(T / 'm426_head_material_classes.png')
(T / 'm426_ramps.json').write_text(json.dumps({'variants': list(PALS), 'materials': materials}, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'gown mid', [round(x, 3) for x in gr[k]['colors'][8]])
