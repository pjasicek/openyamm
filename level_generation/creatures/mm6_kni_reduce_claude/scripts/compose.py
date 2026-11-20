#!/usr/bin/env python3
"""Runtime maps and colour tiers for the retextured knight (CLAUDE_CREATURE_TEXTURES.md), body and helmet sets.

Body (meshy/$MESHY_BODY, default body_texture_v1, 2K, runtime layout = upload layout): base colour graded with the baked AO
(work/ao_body.png); armour texels take the native chrome brightness by height (native shading transfer,
SHADE_AMOUNT) times Meshy's own detail; normal and MR at 1K.
Helmet (meshy/helmet_model_v1, its own UVs): base colour, normal and MR at 1K, graded without AO.
Regions (both sets): R trim = the tier colour (violet in Meshy's paint: hue 200-320, saturation >= TRIM_SAT), G chrome
= every other texel inside the islands. Ramps from the aligned native standing pixels (scripts/native_pixels.py):
trim and chrome by luminance (native_shading.transfer_ramps, gain ALBEDO); B/C keep the sprites' navy sheen where
their palettes have it. (By luminance rank, the dark 3D chrome took the sprites' specular whites: bleached B/C.) Each set gets its own ramps (own luminance range).
MR (glTF ORM, engine contract for this material): R specular mask (openyamm_specular_mask: armour 1, hair 0.25),
G roughness (Meshy's, clamped into ROUGH for the chrome glints), B metallic 0 (the material has metallicFactor 0;
a metallic texel has no diffuse term).
Writes textures/: kni_body_basecolor.png (2K) + _1k, kni_body_normal_1k.png, kni_body_mr_1k.png, kni_body_mask.png,
kni_helm_basecolor_1k.png, kni_helm_normal_1k.png, kni_helm_mr_1k.png, kni_helm_mask.png, kni_ramps.json,
kni_material_classes.png, maps.json (for apply_textures.py); prints a report."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import native_shading as NS  # noqa: E402
import region_variants as R  # noqa: E402

T = HERE / 'textures'; T.mkdir(exist_ok=True)
MB = HERE / 'meshy' / os.environ.get('MESHY_BODY', 'body_texture_v1'); MH = HERE / 'meshy' / 'helmet_model_v1'
TIERS = {'kni_a': 760, 'kni_b': 761, 'kni_c': 762}
SHADE_AMOUNT, SHADE_DETAIL = 0.5, 1.0
TRIM_SAT = 0.22
# trim gain/chroma (env TRIM_GAIN, TRIM_CHROMA): body_texture_v2 (graded masters) is darker, and its luminance picks
# darker native trim colours, which read muted under game light
ALBEDO = {'trim': float(os.environ.get('TRIM_GAIN', '1.0')), 'chrome': 1.3}
TRIM_CHROMA = float(os.environ.get('TRIM_CHROMA', '1.0'))
ROUGH = (0.22, 0.5)
CHROME_GAIN = 1.2
CHROME_CHROMA = 0.6
SMOOTH, DETAIL, GAMMA = 1.5, 0.5, 1.6
N = 1024


def raster(npz, size):
    """Rest-pose position per texel (NaN outside the islands) from work/uv3d_<set>.npz."""
    d = np.load(npz); out = np.full((size, size, 3), np.nan)
    for uv, xyz in zip(d['uv'], d['xyz']):
        p = np.stack([uv[:, 0] * size, (1 - uv[:, 1]) * size], 1)
        x0, y0 = np.maximum(np.floor(p.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(p.max(0)).astype(int), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        a, b, c = p; den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den; w2 = 1 - w0 - w1
        inside = (w0 >= -.02) & (w1 >= -.02) & (w2 >= -.02); ys, xs = np.nonzero(inside)
        out[y0 + ys, x0 + xs] = w0[inside, None] * xyz[0] + w1[inside, None] * xyz[1] + w2[inside, None] * xyz[2]
    return out


def hsv_of(rgb):
    hsv = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]


def weights(base, islands):
    h, s, v = hsv_of(base)
    trim = (h > 200) & (h < 320) & (s >= TRIM_SAT) & (v > .06) & islands
    trim = ndimage.binary_closing(ndimage.binary_opening(trim, iterations=1), iterations=1)
    soft = lambda m: np.clip(ndimage.gaussian_filter(m.astype(np.float64), 1.0), 0, 1)
    wt = soft(trim) * islands
    wc = soft(islands & ~trim) * (1 - wt)
    return wt, wc


def pad(img, islands, iterations=8):
    """Grow island colours into the gutters (nearest island texel) so filtering never draws gutter colour."""
    idx = ndimage.distance_transform_edt(~islands, return_distances=False, return_indices=True)
    out = img[idx[0], idx[1]]
    grown = ndimage.binary_dilation(islands, iterations=iterations)
    return np.where(grown[..., None] if img.ndim == 3 else grown, out, img)


def match_native(base, region, pixels, gain=CHROME_GAIN):
    """Chrome contrast like the sprites (user: "completely bleached out"): smoothed texel luminance mapped by a power
    curve (GAMMA) so its median meets the native chrome median (palette 760, all standing views) times gain; hue and Meshy's detail order
    kept by scaling RGB. The sprites' chrome is near black with a long bright tail (median 0.015, p97 0.36 linear);
    Meshy's was mid grey without highlights (median 0.03, p97 0.12). The rank map runs on a smoothed luminance
    (SMOOTH texels per 1K) and only DETAIL of the fine variation returns: mapped texel by texel, Meshy's surface noise
    turned into speckle."""
    sel = pixels['region'] == list(pixels['region_names']).index('chrome')
    target = np.sort(R.srgb_to_linear(pixels['p760'][sel]) @ R.LUMA)
    lin = R.srgb_to_linear(base); lum = lin @ R.LUMA
    sigma = SMOOTH * base.shape[0] / 1024
    w = ndimage.gaussian_filter(region.astype(np.float64), sigma)
    smooth = ndimage.gaussian_filter(np.where(region, lum, 0), sigma) / np.maximum(w, 1e-6)
    vals, svals = lum[region], smooth[region]
    # power curve to the native median (a full rank map turned Meshy's broad light-grey plates into the sprites' thin
    # highlight values: near-white pauldrons and gauntlets); the engine's specular adds the glints
    med_t, med_s = float(np.median(target)) * gain, float(np.median(svals))
    new = med_t * (np.maximum(svals, 1e-5) / med_s) ** GAMMA
    new = new * (np.maximum(vals, 1e-4) / np.maximum(svals, 1e-4)) ** DETAIL
    scale = np.clip(new / np.maximum(vals, 1e-4), 0, 20)
    out = lin.copy(); out[region] = np.clip(lin[region] * scale[:, None], 0, 1)
    srgb = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.clip(out, 0, None) ** (1 / 2.4) - 0.055)
    base[...] = srgb
    return {'before': np.percentile(vals, [50, 97]).round(3).tolist(),
            'after': np.percentile(np.clip(vals * scale, 0, 1), [50, 97]).round(3).tolist()}


def ramps_for(base, wt, wc, pixels):
    # chrome at CHROME_CHROMA: the sprites' blue reflections plus the engine's sky reflection gave the whole suit a navy
    # cast in game (review/ingame/rt6_h0.png)
    trim = NS.transfer_ramps(base, {'trim': wt}, pixels, {'trim': 'trim'}, TIERS, reference=760, gain=ALBEDO,
                             chroma=TRIM_CHROMA)
    chrome = NS.transfer_ramps(base, {'chrome': wc}, pixels, {'chrome': 'chrome'}, TIERS, reference=760, gain=ALBEDO,
                               chroma=CHROME_CHROMA)
    return {t: trim[t] + chrome[t] for t in TIERS}


def mr_map(meshy, islands_n, spec):
    rough = np.asarray(Image.open(meshy / 'texture_urls_0_roughness.png').convert('L').resize((N, N), Image.LANCZOS),
                       np.float64) / 255
    rough = np.clip(rough, *ROUGH)
    r = (np.clip(spec, 0, 1) * 255).astype(np.uint8); g = (rough * 255).astype(np.uint8)
    return np.stack([r, g, np.zeros_like(r)], -1)


def main():
    pixels = np.load(HERE / 'work' / 'native' / 'pixels.npz')
    report = {}
    # body
    raw = T / 'kni_body_basecolor_raw.png'
    Image.open(MB / 'texture_urls_0_base_color.png').convert('RGB').save(raw)
    subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'), '--ao',
                    str(HERE / 'work' / 'ao_body.png'), '--ao-strength', '0.6', '--local', '0.4', '--contrast', '1.08',
                    '--saturation', '1.0', str(raw)], check=True)
    base = np.asarray(Image.open(T / 'kni_body_basecolor_raw_graded.png').convert('RGB'), np.float64) / 255
    S = base.shape[0]
    xyz = raster(HERE / 'work' / 'uv3d_body.npz', S); islands = ~np.isnan(xyz[..., 0])
    hair = islands & (np.nan_to_num(xyz[..., 1]) > .05) & (np.nan_to_num(xyz[..., 2]) > 1.0) & (np.abs(np.nan_to_num(xyz[..., 0])) < .17)
    wt, wc = weights(base, islands)
    # native shading: chrome by height (feet 0 .. horn tips 1), not on the hair
    sel = pixels['region'] == 1
    bins = np.round(np.arange(0, 1.025, .05), 6)
    curve, _ = NS._binned(pixels['coord'][sel], NS.srgb_luminance(pixels['p760'][sel]), bins, .05)
    coord = NS.texel_coordinate(np.nan_to_num(xyz), 'height', z_range=(0.0, float(os.environ.get('Z_TOP', '1.79'))))
    shade_region = (wc > .5) & ~hair
    before = float(np.median(NS.srgb_luminance(base[shade_region])))
    NS.shade(base, coord, shade_region, {'bins': bins, 'luminance': curve}, detail_strength=SHADE_DETAIL,
             detail=NS.detail_of(base), amount=SHADE_AMOUNT)
    report['body_shade'] = {'median_luminance': [round(before, 3), round(float(np.median(NS.srgb_luminance(base[shade_region]))), 3)]}
    report['body_contrast'] = match_native(base, (wc > .5) & islands, pixels)
    base = pad(base, islands)
    body_ramps = ramps_for(base, wt, wc, pixels)
    Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).save(T / 'kni_body_basecolor.png', optimize=True)
    Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).resize((N, N), Image.LANCZOS).save(T / 'kni_body_basecolor_1k.png')
    Image.open(MB / 'texture_urls_0_normal.png').convert('RGB').resize((N, N), Image.LANCZOS).save(T / 'kni_body_normal_1k.png')
    small = lambda m: np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize((N, N), Image.BILINEAR), np.float64) / 255
    spec = np.where(small(hair.astype(float)) > .5, .25, 1.0)
    Image.fromarray(mr_map(MB, None, spec)).save(T / 'kni_body_mr_1k.png')
    mask_t, mask_c = pad(wt, islands), pad(wc, islands)
    R.write_mask([mask_t, mask_c], T / 'kni_body_mask.png', size=N)
    report['body'] = {'trim_texels': int((wt > .9).sum()), 'chrome_texels': int((wc > .9).sum()), 'hair_texels': int(hair.sum())}

    if os.environ.get('HELMET', '1') == '0':
        # body-only retexture of a model as it is (its own helmet in the body texture)
        finish(report, [{'base': 'KnightPlate_A', 'prefix': 'KnightPlate', 'mask': 'kni_body_mask.png',
                         'regions': ['trim', 'chrome'], 'palettes': TIERS, 'ramps': body_ramps}], islands, hair, small)
        return
    # helmet: Meshy's own textures and UVs
    hb = np.asarray(Image.open(MH / 'texture_urls_0_base_color.png').convert('RGB').resize((N, N), Image.LANCZOS), np.float64) / 255
    hxyz = raster(HERE / 'work' / 'uv3d_helmet.npz', N); hisl = ~np.isnan(hxyz[..., 0])
    hwt, hwc = weights(hb, hisl)
    hb = pad(hb, hisl)
    helm_ramps = ramps_for(hb, hwt, hwc, pixels)
    Image.fromarray((np.clip(hb, 0, 1) * 255).astype(np.uint8)).save(T / 'kni_helm_basecolor_1k.png')
    Image.open(MH / 'texture_urls_0_normal.png').convert('RGB').resize((N, N), Image.LANCZOS).save(T / 'kni_helm_normal_1k.png')
    Image.fromarray(mr_map(MH, None, np.ones((N, N)))).save(T / 'kni_helm_mr_1k.png')
    R.write_mask([pad(hwt, hisl), pad(hwc, hisl)], T / 'kni_helm_mask.png', size=N)
    report['helmet'] = {'trim_texels': int((hwt > .9).sum()), 'chrome_texels': int((hwc > .9).sum())}

    finish(report, [
        {'base': 'KnightPlate_A', 'prefix': 'KnightPlate', 'mask': 'kni_body_mask.png', 'regions': ['trim', 'chrome'],
         'palettes': TIERS, 'ramps': body_ramps},
        {'base': 'KnightHelm_A', 'prefix': 'KnightHelm', 'mask': 'kni_helm_mask.png', 'regions': ['trim', 'chrome'],
         'palettes': TIERS, 'ramps': helm_ramps}], islands, hair, small)


def finish(report, materials, islands, hair, small):
    maps = {'KnightPlate_A': {'base': 'kni_body_basecolor.png', 'normal': 'kni_body_normal_1k.png', 'mr': 'kni_body_mr_1k.png'},
            'KnightHelm_A': {'base': 'kni_helm_basecolor_1k.png', 'normal': 'kni_helm_normal_1k.png', 'mr': 'kni_helm_mr_1k.png'}}
    config = {'variants': list(TIERS), 'materials': materials, 'report': report}
    (T / 'kni_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    (T / 'maps.json').write_text(json.dumps({m['base']: maps[m['base']] for m in materials}, indent=1))
    cls = np.zeros((N, N), np.uint8); cls[small(islands.astype(float)) > .5] = 9; cls[small(hair.astype(float)) > .5] = 2
    Image.fromarray(cls, 'L').save(T / 'kni_material_classes.png')
    print('COMPOSE', json.dumps(report))


if __name__ == '__main__':
    main()
