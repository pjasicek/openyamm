#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the m214 elf archer (CLAUDE_CREATURE_TEXTURES.md). Run after
transfer_uv.py, uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.
Tiers recolour two regions, as the native ACT transforms do (mm7_m214/variants.json): R = the green garments (vest,
trousers; palette entries 104-171), G = the hair (entries 62-103). Skin, ivory piping, leather, the gold quiver
fittings, bow and arrow stay. Tier A Elven Archer = palette 215 (olive/blond), B Elven Scout = 216 (green/silver, the
HD masters' colours), C Elven Ranger = 217 (red/brown) - from the m215/m216/m217 sprite frame tables.
- Skin (body + head): one albedo (the median of the classified Meshy skin of both sets, so the neck seam matches) times
  Meshy's fine shading (luminance over its masked blur), mixed SKIN_MIX over Meshy's colour.
- Base colour graded by the rest-pose AO; ORM red = per-class specular (openyamm_specular_mask), green = roughness,
  blue = 0 (no metal: the runtime has no environment for it on a dim creature).
- Ramps: rank-matched to the native sprite pixels of each region (see the ramps block), x RAMP_GAIN (sprites carry
  baked shading), over the region texels' 2nd-98th luminance percentile (body and head pooled, so the head's ramps
  equal the body's for tools/merge_head_material.py).
- The bowstring is part of the body mesh: it samples a pale swatch painted into an empty corner of the body set
  (texture/region mask zeroed there); its UV is written to textures/m214_swatches.json.
- The scalp skin under the hair mesh, which Meshy painted hair-grey, joins the hair region (else grey shows through
  blond or brown hair).
- Bow and arrow keep their own textures (bow cropped to its columns, 256 x 1024; arrow 64 x 256).
Writes textures/m214_*."""
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
PALS = {'m214_a': 215, 'm214_b': 216, 'm214_c': 217}
REGION_IDX = {'cloth': (104, 172), 'hair': (62, 104)}
SPEC = {'skin': 0.45, 'cloth': 0.25, 'piping': 0.3, 'leather': 0.35, 'gold': 0.9, 'hair': 0.35, 'eye': 0.9}
ROUGH = {'skin': 0.55, 'cloth': 0.75, 'piping': 0.7, 'leather': 0.6, 'gold': 0.3, 'hair': 0.6, 'eye': 0.2}
CLASS_ID = {'skin': 1, 'hair': 2, 'cloth': 8, 'piping': 8, 'leather': 8, 'gold': 9, 'eye': 6}


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


def classify(base, cov, piece, garment):
    hue, sat, val = hsv(base)
    green = cov & (hue > 70) & (hue < 175) & (sat > 0.2) & (val > 0.06)
    piping = cov & ~green & (sat < 0.16) & (val > 0.62)
    skin = cov & (garment == 0) & ~green & ~piping & ((hue < 38) | (hue > 335)) & (sat > 0.1) & (sat < 0.72) & (val > 0.3)
    gold = cov & ~green & ~skin & (hue > 30) & (hue < 62) & (sat > 0.35) & (val > 0.45)
    leather = cov & ~(green | piping | skin | gold)
    return {'skin': skin, 'cloth': green, 'piping': piping, 'gold': gold, 'leather': leather}


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
HC = classify(hb, hcov, hpiece, hgar)
hpos = Rh['pos']
_hh, _hs, _hv = hsv(hb)
scalp = hcov & (hpiece == 0) & (_hs < 0.2) & (hpos[..., 2] > 1.60)   # grey-painted scalp under the hair mesh
hair = hcov & ((hpiece == 3) | scalp)
eye = hcov & np.isin(hpiece, [15, 17])
for k in HC:
    HC[k] &= ~hair & ~eye
HC['hair'], HC['eye'] = hair, eye
SKIN = np.median(np.concatenate([base[C['skin']], hb[HC['skin']]]), 0)
print('SKIN albedo sRGB', np.round(SKIN * 255).tolist())
g = ao_grade(repaint_skin(base, C['skin'], SKIN), load(HERE / 'work' / 'ao_UVMap.png', 'L'), cov)
hg = ao_grade(repaint_skin(hb, HC['skin'], SKIN), load(HERE / 'work' / 'ao_HeadUV.png', 'L'), hcov)
print('CLASSES body', {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()))
print('CLASSES head', {k: int(m.sum()) for k, m in HC.items()}, 'covered', int(hcov.sum()), 'scalp', int(scalp.sum()))
# string swatch: the emptiest 12 x 12 block far from any island
dist = ndimage.distance_transform_edt(~cov)
sy, sx = np.unravel_index(int(np.argmax(dist)), dist.shape)
SW = 6
sw = np.zeros((N, N), bool); sw[max(sy - SW, 0):sy + SW, max(sx - SW, 0):sx + SW] = True
STRING = np.array([0.84, 0.80, 0.68])


def maps(img, nrm, rgh_m, cls, cov_, extra=None):
    spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8); cm = np.zeros((N, N), np.uint8)
    for k, m in cls.items():
        if not m.any():
            continue
        cm[m] = CLASS_ID[k]; spec[m] = SPEC[k]
        rgh[m] = np.clip(ROUGH[k] + (rgh_m[m] - np.median(rgh_m[m])) * 0.5, 0.1, 1)
    return spec, rgh, cm


spec, rgh, cm = maps(g, normal, rough_m, C, cov)
gb = pad(g, cov); gb[sw] = STRING; covs = cov | sw
spec[sw] = 0.2; rgh[sw] = 0.7; cm[sw] = 8
save(gb, T / 'm214_basecolor_1k.png'); save(pad(normal, cov), T / 'm214_normal_1k.png')
save(np.stack([pad(spec, covs), pad(rgh, covs), np.zeros((N, N))], -1), T / 'm214_metal_rough_1k.png')
Image.fromarray(cm).save(T / 'm214_material_classes.png')
hspec, hrgh, hcm = maps(hg, hn, hr_m, HC, hcov)
save(pad(hg, hcov), T / 'm214_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'm214_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm214_head_metal_rough_1k.png')
Image.fromarray(hcm).save(T / 'm214_head_material_classes.png')
# masks (padded like the colour, then blurred; zero on the string swatch)
def soft(m, c):
    return np.clip(ndimage.gaussian_filter(pad(m.astype(float), c), 0.7), 0, 1)


body_r = soft(C['cloth'], cov); body_r[sw] = 0
R.write_mask([body_r, np.zeros((N, N))], T / 'm214_region_mask.png', size=N)
R.write_mask([soft(HC['cloth'], hcov), soft(hair, hcov)], T / 'm214_head_region_mask.png', size=N)
# ---------------------------------------------------------------- ramps (rank-matched to the native sprite pixels)
# The indexed native bitmaps: a region's pixels are those whose palette index lies in its range (hair: only in the top
# HAIR_TOP of the figure, as the range also holds greys used elsewhere). Ordered by their tier-B (216) luminance, the
# 16 stops take each tier's palette colour at the matching ranks (mean over a small window), so one texel luminance
# maps to the same native pixel in every tier.
INV = json.loads((HERE / 'references_native' / 'inventory.json').read_text())
pal = {k: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{p}.act').read_bytes()[:768], np.uint8).reshape(256, 3) / 255
       for k, p in PALS.items()}
FRAMES = [f'm214sa{v}' for v in range(5)] + [f'm214w{c}{v}' for c in 'aceg' for v in (0, 2, 4)] + [f'm214a{c}0' for c in 'aceg']
HAIR_TOP = 0.13
pix = {'cloth': [], 'hair': []}
for fr in FRAMES:
    idx = np.array(Image.open(REPO / INV['sources'][fr]['path']))
    rows = np.where((idx != 0).any(1))[0]; top, h = rows.min(), rows.max() - rows.min()
    yy = np.arange(idx.shape[0])[:, None] + np.zeros_like(idx)
    for region, (a, b) in REGION_IDX.items():
        m = (idx >= a) & (idx < b)
        if region == 'hair':
            m &= yy < top + HAIR_TOP * h
        # only entries that really recolour between the tiers (shared greys: fletchings, piping)
        chg = (np.abs(pal['m214_a'] - pal['m214_b']).max(1) > 0.03) | (np.abs(pal['m214_c'] - pal['m214_b']).max(1) > 0.03)
        m &= chg[idx]
        pix[region].append(idx[m])
lum = {'cloth': np.concatenate([R.luminance(g[C['cloth']]), R.luminance(hg[HC['cloth']])]),
       'hair': R.luminance(hg[hair])}
ramps = {k: [] for k in PALS}
report = {}
for region in ('cloth', 'hair'):
    lo, hi = np.percentile(lum[region], [2, 98])
    ids = np.concatenate(pix[region]); o = np.argsort(R.luminance(pal['m214_b'][ids])); ids = ids[o]
    n = len(ids); win = max(3, n // 60)
    for k in PALS:
        cols = []
        for i in range(16):
            c = int(round((0.02 + 0.96 * i / 15) * (n - 1)))
            X = pal[k][ids[max(0, c - win):min(n, c + win + 1)]].mean(0)
            cols.append(np.clip(lin(np.clip(X * RAMP_GAIN, 0, 1)), 0, 1))
        ramps[k].append({'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': [[round(float(v), 6) for v in c] for c in cols]})
        report[f'{region}_{k}'] = [[round(float(v) * 255) for v in srgb(cols[j])] for j in (2, 8, 14)]
    print('NATIVE', region, 'pixels', n)
print('RAMPS sRGB stops 2/8/14', report)
# ---------------------------------------------------------------- props
bow = Image.open(HERE / 'references_hd' / 'bow.png').convert('RGBA')
X0, CW = 380, 320                                   # bow columns 397-665 (make_bow.py UVs are remapped by the export)
bc = np.asarray(bow, np.float64)[:, X0:X0 + CW] / 255
bcov = bc[..., 3] > 0.5
bimg = pad(bc[..., :3], bcov)
bimg = np.asarray(Image.fromarray((bimg * 255).astype(np.uint8)).resize((256, 1024), Image.LANCZOS), np.float64) / 255
save(bimg, T / 'm214_bow_basecolor.png')
save(np.stack([np.full((1024, 256), 0.35), np.full((1024, 256), 0.6), np.zeros((1024, 256))], -1), T / 'm214_bow_metal_rough.png')
flat = lambda h, w: np.dstack([np.full((h, w), 0.5), np.full((h, w), 0.5), np.ones((h, w))])
save(flat(1024, 256), T / 'm214_bow_normal.png')     # flat, at the base size (split_attachment.py crops every map)
aw = np.asarray(Image.open(HERE / 'textures' / 'props' / 'arrow.png').convert('RGB'), np.float64) / 255
save(aw, T / 'm214_arrow_basecolor.png'); save(flat(*aw.shape[:2]), T / 'm214_arrow_normal.png')
save(np.stack([np.full(aw.shape[:2], 0.3), np.full(aw.shape[:2], 0.6), np.zeros(aw.shape[:2])], -1), T / 'm214_arrow_metal_rough.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Elf_A', 'prefix': 'Elf', 'mask': 'm214_region_mask.png', 'regions': ['cloth', 'hair'],
                      'palettes': PALS, 'ramps': ramps},
                     {'base': 'ElfHead_A', 'prefix': 'ElfHead', 'mask': 'm214_head_region_mask.png', 'regions': ['cloth', 'hair'],
                      'palettes': PALS, 'ramps': ramps}]}
(T / 'm214_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
(T / 'm214_swatches.json').write_text(json.dumps({'string_uv': [(sx + 0.5) / N, 1 - (sy + 0.5) / N], 'bow_crop': [X0, CW, 1024, 1536],
                                                  'skin_srgb': [round(float(v) * 255) for v in SKIN]}, indent=1) + '\n')
print('SWATCH string at texel', int(sx), int(sy), 'free distance', round(float(dist[sy, sx]), 1))
