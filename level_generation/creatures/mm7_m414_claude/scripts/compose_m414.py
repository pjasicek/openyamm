#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the m414 titan (after mm7_m410_claude/scripts/compose_m410.py;
CLAUDE_CREATURE_TEXTURES.md). Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.
Tiers recolour two regions, as the native ACT transforms do: R = the scale tunic, its skirt tiers, the vambraces and the
greaves (palette entries 144-213), G = the helmet crest (entries 223-252). The stone skin, gold trim, belt and sandals,
the steel helmet and the sword stay. Tier A Titan = palette 91 (blue, white crest: the HD masters' colours), B Storm
Titan = 92 (olive, orange), C Blood Titan = 93 (red, pink) - from the 7m415/m416/7m417 sprite frame tables. The head set
holds the crest (and the tunic collar), so it has a region mask too, with the body's ramps.
- Skin (the grey stone of the torso, arm and leg shells and the face): one albedo (the median of the classified Meshy
  skin of both sets) times Meshy's fine shading, mixed SKIN_MIX over Meshy's colour.
- Base colour graded by the rest-pose AO; ORM red = per-class specular (openyamm_specular_mask), green = roughness,
  blue = 0.
- Ramps: each tier's colours of the region's native pixels (with repetition), sorted by luminance and rank-matched to
  the region texels (m410 rule), x RAMP_GAIN (body and head pooled).
- The sword keeps its own texture (make_sword.py, 256 x 1024); ORM from its colour (steel vs leather, gold).
Writes textures/m414_*."""
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
SKIN_MIX, RAMP_GAIN = 0.85, 1.35
PALS = {'m414_a': 91, 'm414_b': 92, 'm414_c': 93}
REGION_IDX = {'tunic': (144, 214), 'crest': (223, 253)}
SPEC = {'skin': 0.35, 'tunic': 0.55, 'crest': 0.2, 'metal': 0.7, 'gold': 0.8, 'leather': 0.35, 'eye': 0.9}
ROUGH = {'skin': 0.6, 'tunic': 0.45, 'crest': 0.85, 'metal': 0.35, 'gold': 0.3, 'leather': 0.6, 'eye': 0.2}
CLASS_ID = {'skin': 1, 'tunic': 9, 'crest': 2, 'metal': 9, 'gold': 9, 'leather': 8, 'eye': 6}


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


def repaint_skin(img, m, albedo, sigma=6.0):
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma); den = ndimage.gaussian_filter(m.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** 1.15, 0.5, 1.5)
    new = srgb(np.clip(lin(albedo)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - SKIN_MIX) + new * SKIN_MIX
    return out


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


def classify(base, cov, piece, garment, head=False):
    hue, sat, val = hsv(base)
    gold = cov & (hue > 28) & (hue < 62) & (sat > 0.4) & (val > 0.4) & (piece != 5)
    eye = cov & np.isin(piece, [11, 12])
    crest = cov & (piece == 5) & ~gold
    blue = (hue > 185) & (hue < 255) & (sat > 0.2)
    tunic = cov & ~(gold | eye | crest) & (np.isin(piece, [4, 8, 9]) | (np.isin(piece, [0, 1, 2, 3]) & blue))
    metal = cov & ~(gold | eye | crest | tunic) & np.isin(piece, [6, 7])                  # steel helmet and guards
    skin = cov & ~(gold | eye | crest | tunic | metal) & np.isin(piece, [0, 1, 2, 3]) & (sat < 0.3) & (val > 0.25)
    leather = cov & ~(gold | eye | crest | tunic | metal | skin)
    return {'skin': skin, 'tunic': tunic, 'crest': crest, 'metal': metal, 'gold': gold, 'leather': leather, 'eye': eye}


# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'body_retexture_v1'
base = load(M / 'texture_urls_0_base_color.png'); normal = load(M / 'texture_urls_0_normal.png')
rough_m = load(M / 'texture_urls_0_roughness.png', 'L')
Rz = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); piece, gar = Rz['piece'], Rz['garment']; cov = piece >= 0
C = classify(base, cov, piece, gar)
# ---------------------------------------------------------------- head set
HM = HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png'); hn = load(HM / 'texture_urls_0_normal.png')
hr_m = load(HM / 'texture_urls_0_roughness.png', 'L')
Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); hpiece, hgar = Rh['piece'], Rh['garment']; hcov = hpiece >= 0
HC = classify(hb, hcov, hpiece, hgar, head=True)
SKIN = np.median(np.concatenate([base[C['skin']], hb[HC['skin']]]), 0)
print('SKIN albedo sRGB', np.round(SKIN * 255).tolist())
g = ao_grade(repaint_skin(base, C['skin'], SKIN), load(HERE / 'work' / 'ao_UVMap.png', 'L'), cov)
hg = ao_grade(repaint_skin(hb, HC['skin'], SKIN), load(HERE / 'work' / 'ao_HeadUV.png', 'L'), hcov)
print('CLASSES body', {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()))
print('CLASSES head', {k: int(m.sum()) for k, m in HC.items()}, 'covered', int(hcov.sum()))
def maps(img, nrm, rgh_m, cls, cov_, extra=None):
    spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8); cm = np.zeros((N, N), np.uint8)
    for k, m in cls.items():
        if not m.any():
            continue
        cm[m] = CLASS_ID[k]; spec[m] = SPEC[k]
        rgh[m] = np.clip(ROUGH[k] + (rgh_m[m] - np.median(rgh_m[m])) * 0.5, 0.1, 1)
    return spec, rgh, cm


spec, rgh, cm = maps(g, normal, rough_m, C, cov)
gb = pad(g, cov); covs = cov
save(gb, T / 'm414_basecolor_1k.png'); save(pad(normal, cov), T / 'm414_normal_1k.png')
save(np.stack([pad(spec, covs), pad(rgh, covs), np.zeros((N, N))], -1), T / 'm414_metal_rough_1k.png')
Image.fromarray(cm).save(T / 'm414_material_classes.png')
hspec, hrgh, hcm = maps(hg, hn, hr_m, HC, hcov)
save(pad(hg, hcov), T / 'm414_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm414_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm414_head_metal_rough_1k.png')
Image.fromarray(hcm).save(T / 'm414_head_material_classes.png')
# mask (padded like the colour, then blurred)
def soft(m, c):
    return np.clip(ndimage.gaussian_filter(pad(m.astype(float), c), 0.7), 0, 1)


R.write_mask([soft(C['tunic'], cov), soft(C['crest'], cov)], T / 'm414_region_mask.png', size=N)
R.write_mask([soft(HC['tunic'], hcov), soft(HC['crest'], hcov)], T / 'm414_head_region_mask.png', size=N)
# ---------------------------------------------------------------- ramps (rank-matched to the native sprite pixels)
# The indexed native bitmaps: a region's pixels are those whose palette index lies in its range and recolours between
# the tiers.
INV = json.loads((HERE / 'references_native' / 'inventory.json').read_text())
pal = {k: np.frombuffer((REPO / INV['palette_sources'][str(p)]['path']).read_bytes()[:768], np.uint8).reshape(256, 3) / 255
       for k, p in PALS.items()}
FRAMES = [f'm414sa{v}' for v in range(5)] + [f'm414w{c}{v}' for c in 'aceg' for v in (0, 2, 4)] + [f'm414a{c}0' for c in 'ace']
pix = {'tunic': [], 'crest': []}
for fr in FRAMES:
    idx = np.array(Image.open(REPO / INV['sources'][fr]['path']))
    rows = np.where((idx != 0).any(1))[0]; top, h = rows.min(), rows.max() - rows.min()
    yy = np.arange(idx.shape[0])[:, None] + np.zeros_like(idx)
    for region, (a, b) in REGION_IDX.items():
        m = (idx >= a) & (idx < b)
        # only entries that really recolour between the tiers (shared greys: fletchings, piping)
        chg = (np.abs(pal['m414_a'] - pal['m414_b']).max(1) > 0.03) | (np.abs(pal['m414_c'] - pal['m414_b']).max(1) > 0.03)
        m &= chg[idx]
        pix[region].append(idx[m])
lum = {'tunic': np.concatenate([R.luminance(g[C['tunic']]), R.luminance(hg[HC['tunic']])]),
       'crest': np.concatenate([R.luminance(g[C['crest']]), R.luminance(hg[HC['crest']])])}
ramps = {k: [] for k in PALS}
report = {}
for region in ('tunic', 'crest'):
    lo, hi = np.percentile(lum[region], [2, 98])
    # m410: each tier's colours of the region's native PIXELS (with repetition), sorted by luminance, stops at the
    # 2..98 % quantiles: unique palette entries over-weighted the many near-black shade entries (tier A vest came out
    # black)
    # rank-matched: stop i sits at t = i/15 of the texels' linear-luminance range; it takes the native colour at the
    # quantile equal to the share of region texels below that t (dark texels crowd the low t: evenly spaced quantiles
    # turned the trousers black)
    tt = np.clip((lum[region] - lo) / (hi - lo), 0, 1)
    qs = [float(np.clip((tt <= i / 15).mean(), 0.02, 0.98)) for i in range(16)]
    used = np.concatenate(pix[region]); n = len(used)
    for k in PALS:
        X = pal[k][used]; X = X[np.argsort(R.luminance(X))]
        cols = [np.clip(lin(np.clip(X[int(round(qs[i] * (len(X) - 1)))] * RAMP_GAIN, 0, 1)), 0, 1) for i in range(16)]
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': [[round(float(v), 6) for v in c] for c in cols]})
        report[f'{region}_{k}'] = [[round(float(v) * 255) for v in srgb(cols[j])] for j in (2, 8, 14)]
    print('NATIVE', region, 'pixels', n)
print('RAMPS sRGB stops 2/8/14', report)
# ---------------------------------------------------------------- props (the sword's base colour from make_sword.py)
ax = np.asarray(Image.open(T / 'm414_sword_basecolor.png').convert('RGB'), np.float64) / 255
ah, as_, av = hsv(ax)
steel = (as_ < 0.25) & (av > 0.3); goldp = (ah > 28) & (ah < 62) & (as_ > 0.4) & (av > 0.35)
save(np.stack([np.where(steel, 0.75, np.where(goldp, 0.8, 0.3)), np.where(steel, 0.35, np.where(goldp, 0.3, 0.7)), np.zeros(ax.shape[:2])], -1), T / 'm414_sword_metal_rough.png')
save(np.dstack([np.full(ax.shape[:2], 0.5), np.full(ax.shape[:2], 0.5), np.ones(ax.shape[:2])]), T / 'm414_sword_normal.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Titan_A', 'prefix': 'Titan', 'mask': 'm414_region_mask.png', 'regions': ['tunic', 'crest'],
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'TitanHead_A', 'prefix': 'TitanHead', 'mask': 'm414_head_region_mask.png', 'regions': ['tunic', 'crest'],
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm414_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / 'm414_swatches.json').write_text(json.dumps({'skin_srgb': [round(float(v) * 255) for v in SKIN]}, indent=1) + '\n')

