#!/usr/bin/env python3
"""Runtime body maps and colour tiers for the titan (CLAUDE_CREATURE_TEXTURES.md), from meshy/retexture_v1.

- Base colour: Meshy's map with the baked AO (work/ao_body.png, claude_shared/bake_creature_ao.py on rig_v2) graded in
  (claude_shared/grade_basecolor.py).
- Region mask (1024 RGBA) + ramps: R armour (every non-gold, non-red texel of the armour shells, plus Meshy's blue
  metal on the skin shells: hue 190-300, saturation >= 0.12), G trim (gold: hue
  28-70, saturation >= 0.35, value >= 0.3); skin, the red belt gem and the eyes keep their colour in every tier (the
  native palettes 828/829/830 change only armour, trim and crest; the crest is in the head set, head_tiers.py).
  Armour ramps of tiers B/C by luminance rank (rank_ramps; tier A by luminance, rank read chalky white), trim ramps: native_shading.transfer_ramps from the aligned native
  standing pixels (scripts/native_pixels.py): for each
  stop the 828 pixels of the region nearest in luminance, read in 828/829/830, times ALBEDO (sprites carry baked
  shading). Tier A thus turns Meshy's saturated blue into the native lavender; B and C get the black armour with its
  teal sheen, C the blue trim.
- Native shading transfer (NATIVE_SHADE, ../NATIVE_SHADING_TRANSFER.md, user request 2026-10-09): before the ramps,
  the armour texels take the native armour brightness by height (dark greaves, lighter skirt, darker waist, bright
  chest and shoulders: the sprites' light from above) x Meshy's hammered detail, at SHADE_AMOUNT. Face and head set are
  not shaded. Pre-transfer maps: textures_pre_native/.
- Normal 1024, metal/roughness 1024 = glTF ORM (R baked AO, G roughness, B metallic); material classes 1024.
Writes into textures/: ttn_a_basecolor.png (2K), ttn_a_basecolor_1k.png, ttn_normal_1k.png, ttn_metal_rough_1k.png,
ttn_region_mask.png, ttn_ramps.json, ttn_material_classes.png, ttn_body_weights.npz (2K armour/trim weights)."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import native_shading as NS
import region_variants as R

T = HERE / 'textures'
M = HERE / 'meshy' / 'retexture_v1'
TIERS = {'ttn_a': 828, 'ttn_b': 829, 'ttn_c': 830}
NATIVE_SHADE = True        # native shading transfer on the armour (../NATIVE_SHADING_TRANSFER.md)
SHADE_AMOUNT, SHADE_DETAIL, MODEL_TOP = 0.7, 1.0, 1.578
ALBEDO = {'armour': 1.35, 'trim': 1.0}   # trim 1.3 read neon-yellow in game (review/ingame/far_1.png)
N = 1024
T.mkdir(exist_ok=True)


def raster(regions_wanted, layout, size):
    img = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(img)
    for r, pts in layout['faces']:
        if layout['regions'][r] in regions_wanted:
            d.polygon([(u * size, (1 - v) * size) for u, v in pts], fill=255, outline=255)
    return np.asarray(img) > 0


def hsv_of(rgb):
    hsv = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]


ARMOUR_REGIONS = {'Skirt', 'Pauldron', 'Bracer', 'Band', 'Greave', 'GreaveFused', 'Knee', 'Dome', 'Helmet'}


def weights_of(base, keep=None, shells=None):
    """Soft armour / trim weights. On armour shells (shells: texel mask) every texel that is not gold or red is
    armour (low-saturation plate texels kept their lavender in tier B with a hue rule alone); on skin shells the blue
    hue class (cuirass on the torso)."""
    h, s, v = hsv_of(base)
    trim = (h > 28) & (h < 70) & (s >= 0.35) & (v >= 0.3)
    red = ((h < 15) | (h > 340)) & (s >= 0.5)
    armour = (h > 190) & (h < 300) & (s >= 0.12) & (v > 0.04)
    armour = ndimage.binary_closing(ndimage.binary_opening(armour, iterations=1), iterations=1)
    if shells is not None:
        armour |= shells & ~trim & ~red
    trim = ndimage.binary_closing(trim, iterations=1)
    if keep is not None:
        armour &= keep; trim &= keep
    soft = lambda m: np.clip(ndimage.gaussian_filter(m.astype(np.float64), 1.0), 0, 1)
    wa, wt = soft(armour), soft(trim)
    return wa * (1 - wt), wt


def raster_xyz(size):
    """Rest-pose 3D position per texel (work/uv3d.npz from dump_uv3d.py on rig_v2), NaN outside the islands."""
    data = np.load(HERE / 'work' / 'uv3d.npz')
    out = np.full((size, size, 3), np.nan)
    for uv, xyz in zip(data['uv'], data['xyz']):
        p = np.stack([uv[:, 0] * size, (1 - uv[:, 1]) * size], 1)
        x0, y0 = np.floor(p.min(0)).astype(int)
        x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        ys, xs = np.nonzero(inside)
        out[y0 + ys, x0 + xs] = (w0[inside, None] * xyz[0] + w1[inside, None] * xyz[1] + w2[inside, None] * xyz[2])
    return out


def native_shade(base, region, pixels):
    """Armour texels take the native armour brightness at their height (median sRGB luminance of the 828 armour pixels
    per 5 % height bin, all standing views) x their own local detail, blended by SHADE_AMOUNT."""
    sel = pixels['region'] == list(pixels['region_names']).index('armour')
    bins = np.round(np.arange(0, 1 + 0.025, 0.05), 6)
    curve, _ = NS._binned(pixels['coord'][sel], NS.srgb_luminance(pixels['p828'][sel]), bins, 0.05)
    xyz = raster_xyz(base.shape[0])
    coord = NS.texel_coordinate(np.nan_to_num(xyz), 'height', z_range=(0.0, MODEL_TOP))
    region = region & ~np.isnan(xyz[..., 0])
    before = float(np.median(NS.srgb_luminance(base[region])))
    NS.shade(base, coord, region, {'bins': bins, 'luminance': curve}, detail_strength=SHADE_DETAIL,
             detail=NS.detail_of(base), amount=SHADE_AMOUNT)
    return {'profile': np.round(curve, 3).tolist(), 'texels': int(region.sum()),
            'median_luminance': [round(before, 3), round(float(np.median(NS.srgb_luminance(base[region]))), 3)]}


def rank_ramps(base, weight, pixels, region, gain):
    """Ramps by luminance rank (as mm6_bat_claude/scripts/native_tiers.py): stop k sits at the texel luminance whose
    quantile q_k is read from the native region pixels sorted by their 828 luminance, in every palette. The shaded 3D
    armour is darker than most native armour pixels, so nearest-luminance matching gave tiers B/C only the sprites'
    darkest black, without the teal sheen of their plates (in game, review/ingame/ns_compare.png)."""
    lum = R.luminance(base)[weight > 0.9]
    lo, hi = np.percentile(lum, 0.5), np.percentile(lum, 99.5)
    quant = np.searchsorted(np.sort(lum), lo + (hi - lo) * np.arange(16) / 15) / len(lum)
    sel = pixels['region'] == list(pixels['region_names']).index(region)
    order = np.argsort(R.srgb_to_linear(pixels['p828'][sel]) @ R.LUMA)
    out = {}
    for variant, palette in TIERS.items():
        native = pixels[f'p{palette}'][sel][order]; half = max(len(native) // 100, 2); colours = []
        for q in quant:
            c = int(np.clip(q, 0, 1) * (len(native) - 1))
            colours.append(R.srgb_to_linear(np.clip(np.median(native[max(c - half, 0):c + half + 1], 0) * gain, 0, 1)))
        out[variant] = {'range': [round(float(lo), 6), round(float(hi), 6)],
                        'colors': np.round(np.clip(colours, 0, 1), 6).tolist()}
    return out


def main():
    layout = json.loads((HERE / 'work' / 'uv_layout.json').read_text())
    raw = T / 'ttn_a_basecolor_raw.png'
    Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').save(raw)
    subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'), '--ao',
                    str(HERE / 'work' / 'ao_body.png'), '--ao-strength', '0.6', '--local', '0.4', '--contrast', '1.05',
                    '--saturation', '1.0', str(raw)], check=True)
    base = np.asarray(Image.open(T / 'ttn_a_basecolor_raw_graded.png').convert('RGB'), np.float64) / 255
    S2 = base.shape[0]
    islands = raster(set(layout['regions']), layout, S2)
    shells = raster(ARMOUR_REGIONS, layout, S2)
    wa, wt = weights_of(base, ndimage.binary_dilation(islands, iterations=3), shells)
    np.savez_compressed(T / 'ttn_body_weights.npz', armour=wa.astype(np.float32), trim=wt.astype(np.float32))
    pixels = np.load(HERE / 'work' / 'native_shading' / 'pixels.npz')
    shade_report = native_shade(base, wa > 0.5, pixels) if NATIVE_SHADE else None
    ramps = NS.transfer_ramps(base, {'armour': wa, 'trim': wt}, pixels, {'armour': 'armour', 'trim': 'trim'}, TIERS,
                              reference=828, gain=ALBEDO)
    armour = rank_ramps(base, wa, pixels, 'armour', ALBEDO['armour'])
    for t in ('ttn_b', 'ttn_c'):           # tier A keeps the luminance-matched ramp (by rank it read chalky white)
        ramps[t][0] = armour[t]
    report = {'armour_texels': int((wa > 0.9).sum()), 'trim_texels': int((wt > 0.9).sum()),
              'ranges': [r['range'] for r in ramps['ttn_a']], 'native_shade': shade_report}

    Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).save(T / 'ttn_a_basecolor.png', optimize=True)
    Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).resize((N, N), Image.LANCZOS).save(
        T / 'ttn_a_basecolor_1k.png', optimize=True)
    Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((N, N), Image.LANCZOS).save(
        T / 'ttn_normal_1k.png', optimize=True)
    rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((N, N), Image.LANCZOS))
    metal = np.asarray(Image.open(M / 'texture_urls_0_metallic.png').convert('L').resize((N, N), Image.LANCZOS))
    ao = np.asarray(Image.open(HERE / 'work' / 'ao_body.png').convert('L').resize((N, N), Image.LANCZOS))
    Image.fromarray(np.stack([ao, rough, metal], -1)).save(T / 'ttn_metal_rough_1k.png', optimize=True)
    R.write_mask([wa, wt], T / 'ttn_region_mask.png', size=N)
    config = {'variants': list(TIERS),
              'materials': [{'base': 'Titan_A', 'prefix': 'Titan', 'mask': 'ttn_region_mask.png',
                             'regions': ['armour', 'trim'], 'palettes': TIERS, 'ramps': ramps, 'report': report}]}
    (T / 'ttn_ramps.json').write_text(json.dumps(config, indent=1) + '\n')

    small = lambda m: np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((N, N), Image.BILINEAR)) > 127
    cls = np.zeros((N, N), np.uint8)
    cls[raster(set(layout['regions']), layout, N)] = 1
    cls[small(wa) | small(wt)] = 9
    Image.fromarray(cls, 'L').save(T / 'ttn_material_classes.png')
    print('MAPS', json.dumps(report))


if __name__ == '__main__':
    main()
