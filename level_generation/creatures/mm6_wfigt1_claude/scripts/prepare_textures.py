#!/usr/bin/env python3
"""Runtime body maps and colour tiers for the werewolf (CLAUDE_CREATURE_TEXTURES.md), from meshy/retexture_v1.
Adapted from mm6_ttn1_claude/scripts/prepare_textures.py.

- Base colour: Meshy's map with the baked AO (work/ao_body.png, claude_shared/bake_creature_ao.py on rig_v2) graded in
  (claude_shared/grade_basecolor.py).
- Projection leaks repaired first (Meshy paints occluders onto what lies behind them): rust texels on the hands,
  teeth, fur cards, mane and the torso above the waist (z > 1.0), and chain-yellow texels on the torso, mane and fur
  cards, take the colour of the nearest clean texel of the same UV region.
- Fur scaled by FUR_GAIN (0.7) toward the native charcoal (keeps claws, teeth, chain, pendant and cloth), except the
  ash-grey chest, shoulders and upper back (torso and arms above z 1.02-1.12), as in the sprites.
- Region mask (1024 RGBA) + ramps: R shorts (texels of the shorts and fused right-leg shell, the left leg's top and
  the hidden skin under the shorts, and the torso below z 1.0 (waistband), hue 8-48, saturation >= 0.2: Meshy
  painted the jagged hem, the fur below it stays fur), G gem (pendant texels, hue 140-220, saturation
  >= 0.2). Fur, claws, chain and pendant ring keep their colour in every tier: the native palettes 831/832/833 change
  only the shorts (rust, blue, red) and the gem (cyan, red, blue) (scripts/native_pixels.py measured the gold within
  a few levels). Ramps: shorts by luminance rank (rank_ramps), the gem by native_shading.transfer_ramps from the aligned native
  pixels (for each stop, the 831 pixels of
  the region nearest in luminance, read in 831/832/833, times ALBEDO: sprites carry baked shading).
- Normal 1024, metal/roughness 1024 = glTF ORM (R baked AO, G roughness, B metallic); material classes 1024.
Writes into textures/: wwf_a_basecolor.png (2K), wwf_a_basecolor_1k.png, wwf_normal_1k.png, wwf_metal_rough_1k.png,
wwf_region_mask.png, wwf_ramps.json, wwf_material_classes.png."""
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
TIERS = {'wwf_a': 831, 'wwf_b': 832, 'wwf_c': 833}
ALBEDO = {'shorts': 1.05, 'gem': 1.0}      # shorts 1.35 read brighter than the sprites in game (review/ingame)
FUR_GAIN = 0.7      # Meshy fur median 50 (sRGB luminance) vs native 25 x 1.35: the 3D wolf read mid-grey in game
N = 1024
T.mkdir(exist_ok=True)
SHORTS = {'ShortsF', 'ShortsB', 'LegRF', 'LegRB', 'LegLF', 'LegLB', 'Hidden'}
ORANGE_LEAK = {'HandL', 'HandR', 'Teeth', 'Fur', 'Mane', 'TorsoF', 'TorsoB', 'ArmL', 'ArmR'}
YELLOW_LEAK = {'TorsoF', 'TorsoB', 'Mane', 'Fur', 'ArmL', 'ArmR'}


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


def soft(m):
    return np.clip(ndimage.gaussian_filter(m.astype(np.float64), 1.0), 0, 1)


def rank_ramps(base, weight, pixels, region, gain):
    """Ramps by luminance rank (titan prepare_textures.py): stop k sits at the texel luminance whose quantile q_k is
    read from the native region pixels sorted by their 831 luminance, in every palette. Nearest-luminance matching
    kept Meshy's bright tan brightness on the shorts (salmon in the viewer); by rank the shorts take the sprites' rust,
    navy and red brightness spread."""
    lum = R.luminance(base)[weight > 0.9]
    lo, hi = np.percentile(lum, 0.5), np.percentile(lum, 99.5)
    quant = np.searchsorted(np.sort(lum), lo + (hi - lo) * np.arange(16) / 15) / len(lum)
    sel = pixels['region'] == list(pixels['region_names']).index(region)
    order = np.argsort(R.srgb_to_linear(pixels['p831'][sel]) @ R.LUMA)
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
    raw = T / 'wwf_a_basecolor_raw.png'
    Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').save(raw)
    subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'), '--ao',
                    str(HERE / 'work' / 'ao_body.png'), '--ao-strength', '0.6', '--local', '0.4', '--contrast', '1.05',
                    '--saturation', '1.0', str(raw)], check=True)
    base = np.asarray(Image.open(T / 'wwf_a_basecolor_raw_graded.png').convert('RGB'), np.float64) / 255
    S2 = base.shape[0]
    z = raster_xyz(S2)[..., 2]
    h, s, v = hsv_of(base)
    orange = (h > 8) & (h < 48) & (s >= 0.2) & (v >= 0.06)
    yellow = (h >= 38) & (h < 72) & (s >= 0.35) & (v >= 0.2)
    waist = (z < 1.0) & raster({'TorsoF', 'TorsoB'}, layout, S2)
    leaks = 0
    for region in set(layout['regions']):
        m = raster({region}, layout, S2)
        bad = m & ((orange & ~waist) if region in ORANGE_LEAK else False)
        bad = bad | (m & yellow if region in YELLOW_LEAK else False)
        bad = ndimage.binary_dilation(bad, iterations=1) & m
        if not bad.any() or bad.sum() == m.sum():
            continue
        _d, (iy, ix) = ndimage.distance_transform_edt(bad | ~m, return_indices=True)
        base[bad] = base[iy[bad], ix[bad]]
        leaks += int(bad.sum())
    # fur darkened to the sprites' charcoal: every texel outside the shorts/gem colours, the chain, pendant, teeth,
    # tongue and the pale claws on hands and feet
    h, s, v = hsv_of(base)
    keep = raster({'Chain', 'Pendant', 'Teeth', 'Tongue'}, layout, S2) | ((orange | yellow) & ~raster(
        {'Mane', 'Fur', 'ArmL', 'ArmR'}, layout, S2))
    keep |= raster({'HandL', 'HandR', 'FootL', 'FootR'}, layout, S2) & (v > 0.5) & (s < 0.35)
    keep = ndimage.binary_dilation(keep, iterations=1)
    wf = 1 - soft(keep)
    # the sprites' chest, shoulders and upper back are ash-grey over a black belly: no darkening above z 1.12 on the
    # torso and arms, full darkening below 1.02
    upper = raster({'TorsoF', 'TorsoB', 'ArmL', 'ArmR'}, layout, S2) & ~np.isnan(z)
    t = np.clip((np.nan_to_num(z) - 1.02) / 0.10, 0, 1)
    wf = wf * (1 - np.where(upper, t * t * (3 - 2 * t), 0.0))
    base *= (1 - wf * (1 - FUR_GAIN))[..., None]
    h, s, v = hsv_of(base)
    grow = lambda m: ndimage.binary_dilation(m, iterations=3)
    shorts_shell = grow(raster(SHORTS, layout, S2)) | waist
    pendant = grow(raster({'Pendant'}, layout, S2))
    shorts = shorts_shell & (h > 8) & (h < 48) & (s >= 0.2) & (v >= 0.06)
    shorts = ndimage.binary_closing(ndimage.binary_opening(shorts, iterations=1), iterations=2)
    gem = pendant & (h > 140) & (h < 220) & (s >= 0.2)
    ws, wg = soft(shorts), soft(gem)
    pixels = np.load(HERE / 'work' / 'native_shading' / 'pixels.npz')
    ramps = NS.transfer_ramps(base, {'shorts': ws, 'gem': wg}, pixels, {'shorts': 'shorts', 'gem': 'gem'}, TIERS,
                              reference=831, gain=ALBEDO)
    shorts_rank = rank_ramps(base, ws, pixels, 'shorts', ALBEDO['shorts'])
    for t in TIERS:
        ramps[t][0] = shorts_rank[t]
    report = {'leak_texels_repaired': leaks, 'shorts_texels': int((ws > 0.9).sum()), 'gem_texels': int((wg > 0.9).sum()),
              'ranges': [r['range'] for r in ramps['wwf_a']]}

    Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).save(T / 'wwf_a_basecolor.png', optimize=True)
    Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).resize((N, N), Image.LANCZOS).save(
        T / 'wwf_a_basecolor_1k.png', optimize=True)
    Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((N, N), Image.LANCZOS).save(
        T / 'wwf_normal_1k.png', optimize=True)
    rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((N, N), Image.LANCZOS))
    metal = np.asarray(Image.open(M / 'texture_urls_0_metallic.png').convert('L').resize((N, N), Image.LANCZOS))
    ao = np.asarray(Image.open(HERE / 'work' / 'ao_body.png').convert('L').resize((N, N), Image.LANCZOS))
    Image.fromarray(np.stack([ao, rough, metal], -1)).save(T / 'wwf_metal_rough_1k.png', optimize=True)
    R.write_mask([ws, wg], T / 'wwf_region_mask.png', size=N)
    config = {'variants': list(TIERS),
              'materials': [{'base': 'Werewolf_A', 'prefix': 'Werewolf', 'mask': 'wwf_region_mask.png',
                             'regions': ['shorts', 'gem'], 'palettes': TIERS, 'ramps': ramps, 'report': report}]}
    (T / 'wwf_ramps.json').write_text(json.dumps(config, indent=1) + '\n')

    # material classes (CLAUDE_CREATURE_TEXTURES.md labels): fur 2, claw 4, tooth 5, mouth 7, cloth 8, metal 9
    small = lambda m: np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((N, N), Image.BILINEAR)) > 127
    hn, sn, vn = hsv_of(np.asarray(Image.fromarray((base * 255).astype(np.uint8)).resize((N, N), Image.LANCZOS)) / 255)
    cls = np.zeros((N, N), np.uint8)
    cls[raster(set(layout['regions']), layout, N)] = 2
    extremity = raster({'HandL', 'HandR', 'FootL', 'FootR'}, layout, N)
    cls[extremity & (vn > 0.55) & (sn < 0.35)] = 4
    cls[raster({'Teeth'}, layout, N)] = 5
    cls[raster({'Tongue'}, layout, N)] = 7
    cls[small(ws)] = 8
    cls[raster({'Chain', 'Pendant'}, layout, N)] = 9
    Image.fromarray(cls, 'L').save(T / 'wwf_material_classes.png')
    print('MAPS', json.dumps(report))


if __name__ == '__main__':
    main()
