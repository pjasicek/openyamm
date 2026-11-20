#!/usr/bin/env python3
"""Textures, region mask and tier ramps for the m190 dwarf (after mm7_m218_claude/scripts/compose_m218.py;
CLAUDE_CREATURE_TEXTURES.md). Run after transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.
Tiers recolour one region, as the native ACT transforms do (mm7_m190 README: entries 199-233): R = the green cloth
(the collar/mantle in the torso shell and the ragged skirt P03). Skin, beard and hair, steel, mail, gold, leather and
the horns stay. Tier A Dwarven Soldier = palette 191 (dark green, the HD masters' colours), B Dwarven Lieutenant = 192
(blue-violet), C Dwarven Commander = 193 (muted red) - from the m191/m192/m193 sprite frame tables. The head set (face,
helmet, horns, braids, the whole beard) has no recolour region and keeps Meshy's colour.
- Skin (body only: the bare arm, hand and leg shells P04/P05/P06/P15/P16, so the ginger beard is never taken for skin;
  the whole leg shell P06, which Meshy partly painted green):
  one albedo (the median of the classified Meshy skin) times Meshy's fine shading, mixed SKIN_MIX over Meshy's colour.
- Base colour graded by the rest-pose AO; ORM red = per-class specular (openyamm_specular_mask), green = roughness,
  blue = 0.
- Ramps: each tier palette's saturated entries among the region's native pixels, sorted by luminance (m218 rule),
  x RAMP_GAIN, over the region texels' 2nd-98th luminance percentile.
- The axe keeps its own texture (make_axe.py, 512 x 1024); ORM from its colour (steel vs wood/leather/gold).
Writes textures/m190_*."""
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
PALS = {'m190_a': 191, 'm190_b': 192, 'm190_c': 193}
REGION_IDX = {'cloth': (199, 234)}
SPEC = {'skin': 0.45, 'cloth': 0.25, 'metal': 0.7, 'gold': 0.8, 'leather': 0.35, 'hair': 0.35, 'horn': 0.5, 'eye': 0.9}
ROUGH = {'skin': 0.55, 'cloth': 0.8, 'metal': 0.35, 'gold': 0.3, 'leather': 0.6, 'hair': 0.6, 'horn': 0.45, 'eye': 0.2}
CLASS_ID = {'skin': 1, 'hair': 2, 'cloth': 8, 'metal': 9, 'gold': 9, 'leather': 8, 'horn': 10, 'eye': 6}


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
    green = (hue > 70) & (hue < 170) & (sat > 0.2) & (val > 0.08)
    cloth = np.zeros_like(cov) if head else cov & (np.isin(piece, [3]) | ((piece == 0) & green))   # skirt P03 + the collar
    gold = cov & ~cloth & (hue > 30) & (hue < 62) & (sat > 0.4) & (val > 0.4)
    if head:                                                      # the ginger beard shares gold's hue (30 vs 34-37 deg)
        gold &= np.isin(piece, [8, 17, 18])
    eye = cov & np.isin(piece, [24, 25])
    horn = cov & np.isin(piece, [17, 18]) & ~gold
    skin_shell = np.isin(piece, [4, 5, 6, 15, 16]) if not head else (piece == 0)
    skin = cov & skin_shell & ~gold & ((hue < 35) | (hue > 330)) & (sat > 0.15) & (sat < 0.7) & (val > 0.25)
    if head:                                                      # face vs ginger beard: the beard is more saturated
        skin &= sat < 0.55
    else:                                                         # the legs are bare (Meshy painted the thighs green)
        skin |= cov & (piece == 6) & ~gold
    metal = cov & ~(cloth | gold | eye | horn | skin) & (sat < 0.2)
    hair = cov & ~(cloth | gold | eye | horn | skin | metal) & np.isin(piece, [0, 9, 10, 21, 22]) & (hue > 12) & (hue < 45) & (sat > 0.35)
    leather = cov & ~(cloth | gold | eye | horn | skin | metal | hair)
    return {'skin': skin, 'cloth': cloth, 'metal': metal, 'gold': gold, 'leather': leather, 'hair': hair, 'horn': horn, 'eye': eye}


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
SKIN = np.median(base[C['skin'] & ~((piece == 6) & (hsv(base)[0] > 60))], 0)   # albedo from the skin-coloured texels
print('SKIN albedo sRGB', np.round(SKIN * 255).tolist())
g = ao_grade(repaint_skin(base, C['skin'], SKIN), load(HERE / 'work' / 'ao_UVMap.png', 'L'), cov)
hg = ao_grade(hb, load(HERE / 'work' / 'ao_HeadUV.png', 'L'), hcov)
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
save(gb, T / 'm190_basecolor_1k.png'); save(pad(normal, cov), T / 'm190_normal_1k.png')
save(np.stack([pad(spec, covs), pad(rgh, covs), np.zeros((N, N))], -1), T / 'm190_metal_rough_1k.png')
Image.fromarray(cm).save(T / 'm190_material_classes.png')
hspec, hrgh, hcm = maps(hg, hn, hr_m, HC, hcov)
save(pad(hg, hcov), T / 'm190_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm190_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm190_head_metal_rough_1k.png')
Image.fromarray(hcm).save(T / 'm190_head_material_classes.png')
# mask (padded like the colour, then blurred)
def soft(m, c):
    return np.clip(ndimage.gaussian_filter(pad(m.astype(float), c), 0.7), 0, 1)


body_r = soft(C['cloth'], cov)
R.write_mask([body_r], T / 'm190_region_mask.png', size=N)
# ---------------------------------------------------------------- ramps (rank-matched to the native sprite pixels)
# The indexed native bitmaps: a region's pixels are those whose palette index lies in its range (hair: only in the top
# HAIR_TOP of the figure, as the range also holds greys used elsewhere). Ordered by their tier-B (216) luminance, the
# 16 stops take each tier's palette colour at the matching ranks (mean over a small window), so one texel luminance
# maps to the same native pixel in every tier.
INV = json.loads((HERE / 'references_native' / 'inventory.json').read_text())
pal = {k: np.frombuffer((REPO / INV['palette_sources'][str(p)]['path']).read_bytes()[:768], np.uint8).reshape(256, 3) / 255
       for k, p in PALS.items()}
FRAMES = [f'm190sa{v}' for v in range(5)] + [f'm190w{c}{v}' for c in 'aceg' for v in (0, 2, 4)] + [f'm190a{c}0' for c in 'aceg']
HAIR_TOP = 0.13
pix = {'cloth': []}
for fr in FRAMES:
    idx = np.array(Image.open(REPO / INV['sources'][fr]['path']))
    rows = np.where((idx != 0).any(1))[0]; top, h = rows.min(), rows.max() - rows.min()
    yy = np.arange(idx.shape[0])[:, None] + np.zeros_like(idx)
    for region, (a, b) in REGION_IDX.items():
        m = (idx >= a) & (idx < b)
        if region == 'hair':
            m &= yy < top + HAIR_TOP * h
        # only entries that really recolour between the tiers (shared greys: fletchings, piping)
        chg = (np.abs(pal['m190_a'] - pal['m190_b']).max(1) > 0.03) | (np.abs(pal['m190_c'] - pal['m190_b']).max(1) > 0.03)
        m &= chg[idx]
        pix[region].append(idx[m])
lum = {'cloth': R.luminance(g[C['cloth']])}
ramps = {k: [] for k in PALS}
report = {}
for region in ('cloth',):
    lo, hi = np.percentile(lum[region], [2, 98])
    # each tier's own saturated cloth entries (sat > 0.4) sorted by its own luminance (m218 rule)
    used = sorted(set(np.concatenate(pix[region]).tolist()))
    n = len(used)
    for k in PALS:
        X = pal[k][used]
        mx, mn = X.max(1), X.min(1); sat = (mx - mn) / np.maximum(mx, 1e-6)
        X = X[sat > 0.4]; X = X[np.argsort(R.luminance(X))]; X = X[len(X) // 8:]   # the darkest entries are near-black shade
        cols = [np.clip(lin(np.clip(X[int(round(i / 15 * (len(X) - 1)))] * RAMP_GAIN, 0, 1)), 0, 1) for i in range(16)]
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': [[round(float(v), 6) for v in c] for c in cols]})
        report[f'{region}_{k}'] = [[round(float(v) * 255) for v in srgb(cols[j])] for j in (2, 8, 14)]
    print('NATIVE', region, 'palette entries used', n)
print('RAMPS sRGB stops 2/8/14', report)
# ---------------------------------------------------------------- props (the axe's base colour from make_axe.py)
ax = np.asarray(Image.open(T / 'm190_axe_basecolor.png').convert('RGB'), np.float64) / 255
ah, as_, av = hsv(ax)
steel = (as_ < 0.2) & (av > 0.3); goldp = (ah > 30) & (ah < 62) & (as_ > 0.4) & (av > 0.4)
asp = np.where(steel, 0.75, np.where(goldp, 0.8, 0.3)); arg = np.where(steel, 0.35, np.where(goldp, 0.3, 0.7))
save(np.stack([asp, arg, np.zeros(ax.shape[:2])], -1), T / 'm190_axe_metal_rough.png')
save(np.dstack([np.full(ax.shape[:2], 0.5), np.full(ax.shape[:2], 0.5), np.ones(ax.shape[:2])]), T / 'm190_axe_normal.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Dwarf_A', 'prefix': 'Dwarf', 'mask': 'm190_region_mask.png', 'regions': ['cloth'],
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm190_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / 'm190_swatches.json').write_text(json.dumps({'skin_srgb': [round(float(v) * 255) for v in SKIN]}, indent=1) + '\n')

