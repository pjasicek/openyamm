#!/usr/bin/env python3
"""Runtime body maps and colour tiers for the thief (CLAUDE_CREATURE_TEXTURES.md), from meshy/retexture_v1.

- Base colour: Meshy's map with the baked AO (work/ao_body.png, claude_shared/bake_creature_ao.py on rig_v2) graded in
  (claude_shared/grade_basecolor.py); hand texels x HAND_GAIN; cloth texels take the native cloth brightness by height
  (../NATIVE_SHADING_TRANSFER.md, work/uv3d.npz from dump_uv3d.py) at SHADE_AMOUNT (the sprites darken the hem).
- Region mask (1024, R = cloth) + ramps: every texel of the cloak and hood UV regions, plus Meshy's jade undershirt
  texels (hue 95-200, saturation >= 0.12) on the torso, sleeves and jerkin skirt; skin, hair, leather, trousers, boots
  and daggers keep their colour in every tier (native palettes 825/826/827 recolour only the cloth,
  scripts/native_pixels.py). One ramp per tier: claude_shared/native_shading.transfer_ramps from the aligned native
  cloth pixels (for each stop the 825 pixels nearest in luminance, read in 825/826/827, times ALBEDO): the dark cloak
  stops take the green / purple / brown wool, the light stops the jade / lilac / pink shirt.
- Dagger swatches: steel blade, dark iron guard and pommel, brown leather grip, painted into an empty corner of the
  atlas (outside every UV island, outside the mask); export_runtime.py maps the dagger faces into them
  (textures/thf_dagger_swatches.json).
- Normal 1024, ORM 1024 (R baked AO, G roughness, B metallic), material classes 1024.
Writes into textures/: thf_a_basecolor.png (2K), thf_a_basecolor_1k.png, thf_normal_1k.png, thf_metal_rough_1k.png,
thf_region_mask.png, thf_ramps.json, thf_material_classes.png, thf_dagger_swatches.json."""
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
TIERS = {'thf_a': 825, 'thf_b': 826, 'thf_c': 827}
ALBEDO = {'cloth': 1.0}     # 1.3 read 30-40 % brighter than the sprites in game (review/ingame/crop_2.png)
NATIVE_SHADE, SHADE_AMOUNT, SHADE_DETAIL, MODEL_TOP = True, 0.5, 1.0, 1.578
HAND_GAIN = 0.85            # Meshy's hands read near-white next to the sprites' tan skin
N = 1024
CLOTH_REGIONS = {'CloakB', 'CloakBi', 'CloakL', 'CloakLi', 'CloakR', 'CloakRi', 'Hood', 'Hoodi'}
SHIRT_REGIONS = {'TorsoF', 'TorsoB', 'ArmL', 'ArmR', 'Skirt'}
SWATCHES = {'blade': (186, 188, 192), 'iron': (78, 78, 82), 'grip': (92, 58, 34)}
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


def cloth_weight(base, layout):
    S = base.shape[0]
    cloak = raster(CLOTH_REGIONS, layout, S)
    shirt_shells = raster(SHIRT_REGIONS, layout, S)
    h, s, v = hsv_of(base)
    jade = shirt_shells & (h > 95) & (h < 200) & (s >= 0.12) & (v > 0.08)
    jade = ndimage.binary_closing(ndimage.binary_opening(jade, iterations=1), iterations=1)
    cloth = ndimage.binary_dilation(cloak, iterations=2) | jade
    return np.clip(ndimage.gaussian_filter(cloth.astype(np.float64), 1.0), 0, 1)


def swatch_cells(layout, size=N, cell=24):
    """Three empty cells (no island within 6 texels) in the 1K atlas, scanning from the bottom-right corner."""
    occ = ndimage.binary_dilation(raster(set(layout['regions']), layout, size), iterations=6)
    cells = []
    for y in range(size - cell - 4, 0, -cell):
        for x in range(size - cell - 4, 0, -cell):
            if not occ[y:y + cell, x:x + cell].any() and not any(abs(x - cx) < cell and abs(y - cy) < cell
                                                                  for cx, cy in cells):
                cells.append((x, y))
            if len(cells) == 3:
                return cells, cell
    raise SystemExit('no empty atlas cells for the dagger swatches')


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
    """Cloth texels take the native cloth brightness at their height (median sRGB luminance of the 825 cloth pixels
    per 5 % height bin, all standing views) x their own local detail, blended by SHADE_AMOUNT."""
    sel = pixels['region'] == list(pixels['region_names']).index('cloth')
    bins = np.round(np.arange(0, 1 + 0.025, 0.05), 6)
    curve, _ = NS._binned(pixels['coord'][sel], NS.srgb_luminance(pixels['p825'][sel]), bins, 0.05)
    xyz = raster_xyz(base.shape[0])
    coord = NS.texel_coordinate(np.nan_to_num(xyz), 'height', z_range=(0.0, MODEL_TOP))
    region = region & ~np.isnan(xyz[..., 0])
    before = float(np.median(NS.srgb_luminance(base[region])))
    NS.shade(base, coord, region, {'bins': bins, 'luminance': curve}, detail_strength=SHADE_DETAIL,
             detail=NS.detail_of(base), amount=SHADE_AMOUNT)
    return {'profile': np.round(curve, 3).tolist(), 'texels': int(region.sum()),
            'median_luminance': [round(before, 3), round(float(np.median(NS.srgb_luminance(base[region]))), 3)]}


def main():
    layout = json.loads((HERE / 'work' / 'uv_layout.json').read_text())
    raw = T / 'thf_a_basecolor_raw.png'
    Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').save(raw)
    subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'), '--ao',
                    str(HERE / 'work' / 'ao_body.png'), '--ao-strength', '0.6', '--local', '0.4', '--contrast', '1.05',
                    '--saturation', '1.0', str(raw)], check=True)
    base = np.asarray(Image.open(T / 'thf_a_basecolor_raw_graded.png').convert('RGB'), np.float64) / 255
    S2 = base.shape[0]
    w = cloth_weight(base, layout)
    pixels = np.load(HERE / 'work' / 'native_shading' / 'pixels.npz')
    hands = raster({'HandL', 'HandR'}, layout, S2)
    base[hands] *= HAND_GAIN
    shade_report = native_shade(base, w > 0.5, pixels) if NATIVE_SHADE else None
    ramps = NS.transfer_ramps(base, {'cloth': w}, pixels, {'cloth': 'cloth'}, TIERS, reference=825, gain=ALBEDO)
    # dagger swatches (2K base: cells scaled x2)
    cells, cell = swatch_cells(layout)
    sw = {}
    k = S2 // N
    for (x, y), (name, rgb) in zip(cells, SWATCHES.items()):
        base[y * k:(y + cell) * k, x * k:(x + cell) * k] = np.array(rgb) / 255
        w[y * k:(y + cell) * k, x * k:(x + cell) * k] = 0
        sw[name] = [(x + cell / 2) / N, 1 - (y + cell / 2) / N, (cell / 4) / N]     # u, v centre, half size
    (T / 'thf_dagger_swatches.json').write_text(json.dumps(sw, indent=1) + '\n')
    report = {'cloth_texels': int((w > 0.9).sum()), 'ranges': [r['range'] for r in ramps['thf_a']], 'swatches': sw,
              'native_shade': shade_report}
    Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).save(T / 'thf_a_basecolor.png', optimize=True)
    Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).resize((N, N), Image.LANCZOS).save(
        T / 'thf_a_basecolor_1k.png', optimize=True)
    nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((N, N), Image.LANCZOS)).copy()
    rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((N, N), Image.LANCZOS)).copy()
    metal = np.asarray(Image.open(M / 'texture_urls_0_metallic.png').convert('L').resize((N, N), Image.LANCZOS)).copy()
    ao = np.asarray(Image.open(HERE / 'work' / 'ao_body.png').convert('L').resize((N, N), Image.LANCZOS)).copy()
    for (x, y), name in zip(cells, SWATCHES):
        nrm[y:y + cell, x:x + cell] = (128, 128, 255); ao[y:y + cell, x:x + cell] = 255
        rough[y:y + cell, x:x + cell] = 110 if name != 'grip' else 200; metal[y:y + cell, x:x + cell] = 0
    Image.fromarray(nrm).save(T / 'thf_normal_1k.png', optimize=True)
    Image.fromarray(np.stack([ao, rough, metal], -1)).save(T / 'thf_metal_rough_1k.png', optimize=True)
    R.write_mask([w], T / 'thf_region_mask.png', size=N)
    config = {'variants': list(TIERS),
              'materials': [{'base': 'Thief_A', 'prefix': 'Thief', 'mask': 'thf_region_mask.png',
                             'regions': ['cloth'], 'palettes': TIERS, 'ramps': ramps, 'report': report}]}
    (T / 'thf_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    small = lambda m: np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((N, N), Image.BILINEAR)) > 127
    cls = np.zeros((N, N), np.uint8)
    cls[raster(set(layout['regions']), layout, N)] = 1
    cls[raster({'BootL', 'BootR', 'BracerL', 'BracerR', 'Pouch', 'Sheath', 'Strap', 'Skirt'}, layout, N)] = 8
    cls[small(w)] = 8
    for (x, y), name in zip(cells, SWATCHES):
        cls[y:y + cell, x:x + cell] = 9 if name != 'grip' else 8
    Image.fromarray(cls, 'L').save(T / 'thf_material_classes.png')
    print('MAPS', json.dumps(report))


if __name__ == '__main__':
    main()
