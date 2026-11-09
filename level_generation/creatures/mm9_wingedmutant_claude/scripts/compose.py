#!/usr/bin/env python3
"""Shared texture set, region mask and per-tier ramps for the Winged Mutant family (CLAUDE_CREATURE_TEXTURES.md;
after mm9_lobber_claude/scripts/compose.py). Usage: compose.py

Inputs: meshy/retexture_v2 maps (4K on the texture-pass UVs of scripts/uv_texpass.py, 2026-10-30; v1: retexture_v1 at
2K on the Smart UV layout), textures/wmut_ao_2k_v2.png, work/regions_body_v2.npz and work/regions_mm9.npz
(dump_regions.py: region per triangle from its bones), the three MM9 skins. The 4K colour is downsampled once to 2K,
the 4K normal once to 1K.
Regions (mask channels): R skin (face, lower legs, feet, claws, tail), G feathers (torso, thighs), B wing membrane,
A hair (the Xhair locks and the dark scalp texels of the head triangles; the head's bright texels are skin). The
same rule on the MM9 mesh and tier-1 skin picks the MM9 texels sampled in each tier skin.
Tier colours (dragonfly method): tier A keeps the HD look (identity ramps); B/C take the chroma of their own MM9
skin by luminance percentile, saturation scaled by how much more vivid our A is than MM9's A, brightness by the MM9
tier/A ratio.
The wing channel's ramps come from textures/wmut_wing_tone.json (scripts/wing_tone.py), so the sharper 4K paint keeps the
approved wing tone and contrast.
Outputs in textures/: wmut_basecolor.png (2K padded; graded by grade_basecolor.py), wmut_normal_1k.png,
wmut_metal_rough_1k.png (R AO, G roughness, B 0), wmut_region_mask.png, wmut_material_classes.png, wmut_ramps.json.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

T = HERE / 'textures'
M = HERE / 'meshy' / 'retexture_v2'
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = {'wmut_a': 'tier1/skins/wmut1.png', 'wmut_b': 'tier2/skins/wmut2.png', 'wmut_c': 'tier3/skins/wmut3.png'}
TIER_A = 'wmut_a'
REGIONS = ('skin', 'feathers', 'wing', 'hair')
MAT = 'Wmut'
HAIR_LUM = 0.16   # head texels darker than this (sRGB luminance) are hair


def lin(c):
    return RV.srgb_to_linear(c)


def encode(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def raster(npz, size):
    d = np.load(npz)
    uv = d['uv'] * size
    reg = np.zeros((size, size), np.int32)
    for t in range(len(uv)):
        p = uv[t]
        x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), size - 1)
        y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (1 - l1 - l2 >= -1e-4)
        iy, ix = np.nonzero(inside)
        reg[size - 1 - (iy + y0), ix + x0] = d['region'][t]
    return reg


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def feather(m, covered):
    m = pad(m.astype(np.float32), covered)
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)),
                      np.float32) / 255


def classes(reg, rgb, sigma):
    """region index 0..3 per texel (-1 outside); head texels split into skin / hair by smoothed luminance"""
    lum = ndimage.gaussian_filter(rgb @ W, sigma)
    out = np.full(reg.shape, -1)
    out[reg == 1] = 0
    out[reg == 2] = 1
    out[reg == 3] = 2
    out[reg == 4] = 3
    head = reg == 5
    out[head & (lum >= HAIR_LUM)] = 0
    out[head & (lum < HAIR_LUM)] = 3
    return out


S = 1024
reg = raster(HERE / 'work' / 'regions_body_v2.npz', S)
covered = reg > 0
base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                    np.float32) / 255
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
cl = classes(reg, base, 1.5)
masks = [(cl == k) & covered for k in range(4)]
mat_classes = np.zeros((S, S), np.uint8)
for k, val in enumerate((1, 2, 3, 2)):   # skin, fur/feathers, membrane, hair (CLAUDE_CREATURE_TEXTURES.md labels)
    mat_classes[masks[k]] = val
regions = [feather(m, covered) for m in masks]
RV.write_mask(regions, T / 'wmut_region_mask.png')
Image.fromarray(mat_classes * 60).save(T / 'wmut_material_classes.png')
reg2 = raster(HERE / 'work' / 'regions_body_v2.npz', 2048)
Image.fromarray((pad(base2k, reg2 > 0) * 255).astype(np.uint8)).save(T / 'wmut_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                 np.float32) / 255
Image.fromarray((pad(nrm, reg2 > 0) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(T / 'wmut_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
rough = pad(np.where(masks[3], np.clip(rough, 0.45, 0.7), np.clip(rough, 0.5, 0.85)), covered)
ao = np.asarray(Image.open(T / 'wmut_ao_2k_v2.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'wmut_metal_rough_1k.png')

# MM9 side: 256x256 skins, the same rule on the MM9 mesh with the tier-1 skin (all tiers share the MM9 UVs)
ms = 256
mreg = raster(HERE / 'work' / 'regions_mm9.npz', ms)
mcov = mreg > 0
skins = {k: np.asarray(Image.open(HERE / 'source' / p).convert('RGB'), np.float32) / 255 for k, p in TIERS.items()}
mcl = classes(mreg, skins[TIER_A], 0.7)
mm9_sets = {name: (mcl == k) & mcov for k, name in enumerate(REGIONS)}
counts = {k: int(m.sum()) for k, m in mm9_sets.items()}


def chroma_targets(graded, weight, mm9_mask):
    core = weight > 0.5
    glum = lin(graded[core]) @ W
    rank = np.empty(glum.size)
    rank[np.argsort(glum)] = (np.arange(glum.size) + 0.5) / glum.size
    ours = lin(graded[core])
    our_sat = float(np.abs(ours / np.maximum(glum, 1e-3)[:, None] - 1).mean())

    def bands(k):
        pal = lin(skins[k][mm9_mask if mm9_mask.sum() >= 12 else mcov])
        pal = pal[np.argsort(pal @ W)]
        mid = pal[int(0.15 * len(pal)):int(0.95 * len(pal))]
        return pal, np.array([(b / np.maximum(b @ W, 1e-3)[:, None]).mean(0) for b in np.array_split(mid, 6)])

    pal_a, band_a = bands(TIER_A)
    k_sat = float(np.clip(our_sat / max(float(np.abs(band_a - 1).mean()), 1e-3), 0.8, 1.8))
    targets = {TIER_A: graded.copy()}
    for k in TIERS:
        if k == TIER_A:
            continue
        pal, band = bands(k)
        x = np.clip(rank, 0, 1) * (len(band) - 1)
        i0 = np.minimum(x.astype(int), len(band) - 2)
        fr = (x - i0)[:, None]
        chroma = band[i0] * (1 - fr) + band[i0 + 1] * fr
        chroma = 1 + (chroma - 1) * k_sat
        gain = float((pal @ W).mean()) / float((pal_a @ W).mean())
        tgt = graded.copy()
        tgt[core] = encode(np.clip(chroma * (glum * gain)[:, None], 0, 1))
        targets[k] = tgt
    return targets


graded = RV.load_srgb(T / 'wmut_basecolor_graded.png', S) if (T / 'wmut_basecolor_graded.png').exists() else base
report, ramps = [], {k: [] for k in TIERS}
previews = {k: graded.copy() for k in TIERS}
for name, weight in zip(REGIONS, regions):
    targets = chroma_targets(graded, weight, mm9_sets[name])
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k in TIERS:
        ramps[k].append(fitted[k])
        core = weight > 0.5
        previews[k][core] = targets[k][core]
    report.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in rep.items()}})
# wing channel: ramps matched to the approved wing's tone, contrast and hue in every tier (scripts/wing_tone.py)
tone = json.load(open(T / 'wmut_wing_tone.json'))['ramps']
for k in TIERS:
    ramps[k][REGIONS.index('wing')] = tone[k]
json.dump({'variants': list(TIERS), 'mm9_region_texels': counts, 'report': report,
           'sources': {k: f'source/{p}' for k, p in TIERS.items()},
           'materials': [{'base': MAT, 'prefix': MAT, 'mask': 'wmut_region_mask.png', 'ramps': ramps},
                         {'base': MAT + '_Wing', 'prefix': MAT + '_Wing', 'mask': 'wmut_region_mask.png',
                          'ramps': ramps}]},
          open(T / 'wmut_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
for m, c in zip(masks, ((0.4, 0.8, 0.9), (0.3, 0.2, 0.7), (0.5, 0.6, 0.6), (0.9, 0.9, 0.2))):
    prev[m] = c
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k] for k in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / 'wmut_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'mm9_texels': counts, 'fit': report}))
