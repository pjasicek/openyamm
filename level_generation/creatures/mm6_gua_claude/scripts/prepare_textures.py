#!/usr/bin/env python3
"""Runtime body maps and colour tiers for the guard (CLAUDE_CREATURE_TEXTURES.md), from meshy/retexture_v1.

- Base colour: Meshy's map with the baked AO (work/ao_body.png from claude_shared/bake_creature_ao.py on rig_v6)
  graded in (claude_shared/grade_basecolor.py).
- Mail and belt (user review 2159: mail too bright and flat next to the sprite; Meshy mean sRGB (136, 92, 58) vs native
  (57, 37, 27)): native shading transfer (claude_shared/native_shading.py, ../NATIVE_SHADING_TRANSFER.md, config
  native_shading.json, height coordinate on the standing front/back views): the mail texels take the native
  brightness at their height x ALBEDO times Meshy's own ring detail (amount MAIL_AMOUNT), and a detail normal from
  the ring pattern is blended into Meshy's normal map so the rings read in relief.
- Region mask (1024 RGBA) + ramps: R sleeves (blue cloth texels), G trousers (leg regions), B mail/belt/shoes (torso,
  sleeve and shoe regions minus blue). Sleeves/trousers: each tier's native palette family (748 navy/teal, 749
  green/olive, 750 red/maroon) sorted by luminance into 16 stops x ALBEDO over the region's texel p2..p98. Mail:
  native_shading.transfer_ramps (for each stop the 748 mail pixels nearest in luminance, read in each palette).
- Halberd (user review 2159: blade and shaft looked solid, the gem too cyan): the body atlas is squeezed horizontally
  to u * BODY_U (an axis scale keeps tangent directions, so the normal map stays valid) and the freed strip on the right
  holds the halberd: the blade cut from the native broadside frame (guawinc0, the one the outline was traced in)
  through the same shaft frame as trace_halberd.py (user review 2161: the restored 2x art did not fit the outline), the shaft as wood in the native shaft colours with grain, the
  blue band under the head and the gem in the native blue (52, 123, 158). textures/halberd_swatches.json records the
  layout for export_runtime.py.
- Normal 1024, metal/roughness 1024 = glTF ORM (R baked AO, G roughness, B metallic); material classes 1024.
Writes into textures/: gua_a_basecolor.png (2K), gua_a_basecolor_1k.png, gua_normal_1k.png, gua_metal_rough_1k.png,
gua_region_mask.png, gua_ramps.json, halberd_swatches.json, gua_material_classes.png."""
import colorsys
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
PAL = HERE.parent / 'new_sorpigal_3d_stage1_20261006' / 'gua' / 'source' / 'palettes'
TIERS = {'gua_a': 748, 'gua_b': 749, 'gua_c': 750}
ALBEDO = 1.35
MAIL_AMOUNT = 0.85
RING_NORMAL = 2.2                      # detail-normal strength (height = ring luminance high-pass)
BODY_U = 0.90                          # body atlas squeeze; the strip [STRIP_U0, STRIP_U1] holds the halberd
STRIP_U0, STRIP_U1 = 0.905, 0.995
BLADE_LIFT = 1.35                      # sRGB gain on the native blade tone (sprites carry baked shading)
N = 1024
T.mkdir(exist_ok=True)


def palettes():
    return {k: np.frombuffer((PAL / f'pal{k}.act').read_bytes()[:768], np.uint8).reshape(256, 3).astype(float) / 255
            for k in TIERS.values()}


def family(pal748, name):
    out = []
    for i in range(256):
        h, s, v = colorsys.rgb_to_hsv(*pal748[i])
        h *= 360
        if name == 'sleeves' and (i in (220, 221, 222) or 227 <= i <= 244) and 190 <= h <= 245 and v > 0.05:
            out.append(i)
        elif name == 'trousers' and 196 <= i <= 226 and 160 <= h <= 200 and s > 0.25 and v > 0.04:
            out.append(i)
    return out


def palette_ramp(colors, lo, hi):
    lin = R.srgb_to_linear(colors)
    order = np.argsort(lin @ R.LUMA)
    lin = lin[order]
    q, pos = np.linspace(0, 1, 16), np.linspace(0, 1, len(lin))
    stops = np.stack([np.interp(q, pos, lin[:, c]) for c in range(3)], 1) * ALBEDO
    return {'range': [round(lo, 6), round(hi, 6)], 'colors': np.round(np.clip(stops, 0, 1), 6).tolist()}


def raster(regions_wanted, layout, size):
    img = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(img)
    for r, pts in layout['faces']:
        if layout['regions'][r] in regions_wanted:
            d.polygon([(u * size, (1 - v) * size) for u, v in pts], fill=255, outline=255)
    return np.asarray(img) > 0


def raster_xyz(size):
    """Rest-pose 3D position per texel (work/uv3d.npz from dump_uv3d.py), NaN outside the islands."""
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


def ring_normal(lum, region, strength):
    """Tangent-space detail normal from a height = high-passed luminance (bright rings raised)."""
    h = lum - ndimage.gaussian_filter(lum, 4.0)
    h = ndimage.gaussian_filter(h, 0.6) * region
    gy, gx = np.gradient(h)
    n = np.stack([-gx * strength * 1.2, gy * strength * 1.2, np.ones_like(h)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def squeeze(img):
    """Body map -> u * BODY_U; the strip on the right is filled afterwards."""
    h, w = img.shape[:2]
    out = np.zeros_like(img)
    nw = int(round(w * BODY_U))
    out[:, :nw] = np.asarray(Image.fromarray(img).resize((nw, h), Image.LANCZOS)).reshape(out[:, :nw].shape)
    return out


PARTS_UV = {'axe': (-0.06, 0.20, -0.13, 0.0), 'spike': (-0.03, 0.17, 0.0, 0.18)}   # u0, u1, v0, v1 (H units)


def halberd_strip(size):
    """RGB strip (size rows x strip width), a bevel height map for the blade cells, and the cells as
    (col0, row0, col1, row1) with cols in 0..1 of the strip.

    Axe and spike get a full-width cell each (texel density). Sprite texels are blurry at this density (user review:
    blurry blade; the restored 2x art also draws the spike at a different angle), so the steel is built from the
    traced vector outline: the native frame's tone (blurred, exact fit since the outline was traced from it), a bright
    bevelled rim by the distance to the outline edge (the native's light edges around a dark centre), a darker fuller
    line along each part, and fine hammered noise. The height map gives the rim its relief in the normal map."""
    outline = json.loads((HERE / 'work' / 'halberd_outline.json').read_text())
    width = int(round((STRIP_U1 - STRIP_U0) * size))
    strip = np.zeros((size, width, 3), np.float64)
    height = np.zeros((size, width), np.float64)
    top, ax = np.array(outline['top_px']), np.array(outline['axis_px'])
    perp = np.array([-ax[1], ax[0]])
    H = outline['body_px']
    nat = np.asarray(Image.open(HERE.parent / 'new_sorpigal_3d_stage1_20261006' / 'gua' / 'source' / 'frames' /
                                'guawinc0.png').convert('RGBA'), np.float64) / 255
    nat[..., :3] *= nat[..., 3:]                     # premultiplied: the transparent colour (cyan) must not bleed
    rng = np.random.default_rng(11)
    cells, y = {}, 0
    for part, (U0, U1, V0, V1) in PARTS_UV.items():
        h = int(round(width * (U1 - U0) / (V1 - V0)))
        rows, cols = np.mgrid[0:h, 0:width]
        u = U0 + (rows + 0.5) / h * (U1 - U0)
        v = V0 + (cols + 0.5) / width * (V1 - V0)
        img = Image.new('L', (width, h), 0)
        ImageDraw.Draw(img).polygon([((vv - V0) / (V1 - V0) * width, (uu - U0) / (U1 - U0) * h)
                                     for uu, vv in outline[part]], fill=255)
        inside = np.asarray(img) > 0
        dist = ndimage.distance_transform_edt(inside)
        px_per_h = width / (V1 - V0)
        pr = top[0] + u * H * ax[0] + v * H * perp[0] - 0.5
        pc = top[1] + u * H * ax[1] + v * H * perp[1] - 0.5
        rgba = np.stack([ndimage.map_coordinates(nat[..., c], [pr, pc], order=3, mode='nearest') for c in range(4)],
                        -1)
        tone = np.clip(rgba[..., :3] / np.maximum(rgba[..., 3:], 1e-3), 0, 1)
        tone = ndimage.gaussian_filter(tone, (3, 3, 0)).mean(-1, keepdims=True) * np.array([0.98, 1.0, 1.04])
        tone = np.clip(tone * BLADE_LIFT, 0.12, 0.55)
        rim_w = 0.012 * px_per_h                        # ~1.9 cm bevel
        rim = np.exp(-dist / max(rim_w, 1.0)) * (dist > 0)
        edge = (dist > 0) & (dist < 1.6)                # a thin dark line at the very edge, as in the sprite
        fuller = np.exp(-((np.abs(v) - (0.06 if part == 'axe' else 0.05)) * px_per_h / 5.0) ** 2)
        noise = ndimage.gaussian_filter(rng.normal(0, 1, (h, width)), 0.8)
        brushed = ndimage.gaussian_filter(rng.normal(0, 1, (h, width)), (6.0, 0.6))
        t0 = tone[..., 0]
        t0 = t0[inside].mean() + 0.35 * (t0 - t0[inside].mean())       # keep only a hint of the sprite's blotches
        inset = np.exp(-((dist - 1.5 * rim_w) / 1.4) ** 2)               # engraved border line inset from the edge
        groove = np.exp(-((dist - 1.5 * rim_w - 2.4) / 1.1) ** 2)
        lum = t0 * (1 - 0.2 * fuller) + 0.42 * rim + 0.16 * inset - 0.06 * groove + 0.03 * noise + 0.035 * brushed
        lum = np.where(edge, lum * 0.55, lum)
        col = np.clip(lum[..., None] * np.array([0.97, 1.0, 1.05]), 0, 1)
        idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
        strip[y:y + h] = col[idx[0], idx[1]]
        height[y:y + h] = np.clip(dist / max(rim_w * 1.5, 1.0), 0, 1)[idx[0], idx[1]] * inside[idx[0], idx[1]]
        cells[part] = (0, y, 1, y + h)
        y += h + 6
    bh = y
    # wood: u along the shaft (gem end at W0, butt at W1), v around the circumference
    W0, W1 = bh + 8, size - 40
    wl = W1 - W0
    rows, cols = np.mgrid[0:wl, 0:width]
    t = rows / wl
    around = cols / width
    rng = np.random.default_rng(5)
    grain = np.sin(around * 2 * np.pi * 3 + np.sin(t * 40) * 0.6) * 0.5 + 0.5
    streak = ndimage.gaussian_filter(rng.normal(0, 1, (wl, width)), (18, 0.7))
    shade = 0.55 + 0.45 * np.sin(around * 2 * np.pi) ** 2
    wood = np.array([0.50, 0.27, 0.12])[None, None] * (0.75 + 0.18 * grain[..., None] + 0.12 * streak[..., None])
    strip[W0:W1] = wood * (0.7 + 0.3 * shade[..., None])
    cells['wood'] = (0, W0, 1, W1)
    y = W1 + 4
    for name, colour in (('iron', (0.24, 0.24, 0.26)), ('band', (0.13, 0.20, 0.42)), ('gem', (0.20, 0.48, 0.62))):
        strip[y:y + 10] = colour
        cells[name] = (0, y + 2, 1, y + 8)
        y += 12
    return np.clip(strip, 0, 1), height, cells, PARTS_UV


def main():
    layout = json.loads((HERE / 'work' / 'uv_layout.json').read_text())
    raw = T / 'gua_a_basecolor_raw.png'
    Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').save(raw)
    subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'), '--ao',
                    str(HERE / 'work' / 'ao_body.png'), '--ao-strength', '0.6', '--local', '0.4', '--contrast', '1.05',
                    '--saturation', '1.0', str(raw)], check=True)
    base = np.asarray(Image.open(T / 'gua_a_basecolor_raw_graded.png').convert('RGB'), np.float64) / 255
    S2 = base.shape[0]
    normal = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((N, N), Image.LANCZOS),
                        np.float64) / 255 * 2 - 1
    rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((N, N), Image.LANCZOS)).copy()
    metal = np.asarray(Image.open(M / 'texture_urls_0_metallic.png').convert('L').resize((N, N), Image.LANCZOS)).copy()
    ao = np.asarray(Image.open(HERE / 'work' / 'ao_body.png').convert('L').resize((N, N), Image.LANCZOS)).copy()

    # region weights (2K)
    hsv = np.asarray(Image.fromarray((base * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    blue = ndimage.binary_opening((h > 195) & (h < 250) & (s > 0.25) & (v > 0.08), iterations=1)
    legs = raster({'LegL', 'LegR'}, layout, S2)
    mailreg = raster({'Torso', 'SleeveL', 'SleeveR', 'ShoeL', 'ShoeR'}, layout, S2)
    soft = lambda m: ndimage.gaussian_filter(m.astype(np.float64), 1.2)
    w_sleeve = soft(blue & raster({'SleeveL', 'SleeveR', 'Torso'}, layout, S2))
    w_legs = soft(ndimage.binary_dilation(legs, iterations=3))
    w_mail = soft(mailreg & ~blue) * (1 - w_sleeve)
    weights = [np.clip(w, 0, 1) for w in (w_sleeve, w_legs, w_mail)]

    # native shading transfer on the mail/belt (torso and the mail part of the sleeves; shoes keep Meshy's shading)
    xyz = raster_xyz(S2)
    coord = NS.texel_coordinate(np.nan_to_num(xyz), 'height', z_range=(0.0, 1.579))
    profile = json.loads((HERE / 'work' / 'native_shading' / 'profile.json').read_text())
    shaded = (weights[2] > 0.5) & raster({'Torso', 'SleeveL', 'SleeveR'}, layout, S2) & ~np.isnan(xyz[..., 0])
    detail = NS.detail_of(base)
    before_lum = base @ NS.LUMA
    NS.shade(base, coord, shaded, profile, scale=ALBEDO, detail_strength=1.0, detail=detail, amount=MAIL_AMOUNT,
             luminance=profile['regions']['mail']['luminance'])
    # ring relief: detail normal from the ring pattern, blended (whiteout) into Meshy's normal map
    lum_small = np.asarray(Image.fromarray((np.clip(before_lum, 0, 1) * 255).astype(np.uint8)).resize(
        (N, N), Image.LANCZOS), np.float64) / 255
    reg_small = np.asarray(Image.fromarray(shaded.astype(np.uint8) * 255).resize((N, N), Image.BILINEAR),
                           np.float64) / 255
    dn = ring_normal(lum_small, reg_small, RING_NORMAL)
    nn = np.stack([normal[..., 0] + dn[..., 0], normal[..., 1] + dn[..., 1], normal[..., 2] * dn[..., 2]], -1)
    normal = nn / np.linalg.norm(nn, axis=-1, keepdims=True)
    tilt = np.degrees(np.arccos(np.clip(normal[..., 2], -1, 1)))

    # ramps (fitted on the unsqueezed maps)
    lum = R.luminance(base)
    pal = palettes()
    ramps = {t: [] for t in TIERS}
    report = {'mail_normal_tilt_p50_p90': np.percentile(tilt[reg_small > 0.5], [50, 90]).round(1).tolist()}
    for name, w in zip(('sleeves', 'trousers'), weights[:2]):
        core = w > 0.9
        lo, hi = np.percentile(lum[core], 2), np.percentile(lum[core], 98)
        idx = family(pal[748], name)
        report[name] = {'texels': int(core.sum()), 'range': [round(float(lo), 4), round(float(hi), 4)],
                        'palette_entries': len(idx)}
        for t, pid in TIERS.items():
            ramps[t].append(palette_ramp(pal[pid][idx], float(lo), float(hi)))
    pixels = np.load(HERE / 'work' / 'native_shading' / 'pixels.npz')
    mail = NS.transfer_ramps(base, {'mail': weights[2]}, pixels, {'mail': 'mail'}, TIERS, reference=748,
                             gain={'mail': ALBEDO})
    for t in TIERS:
        ramps[t].append(mail[t][0])
    report['mail'] = {'texels': int((weights[2] > 0.9).sum()), 'range': mail['gua_a'][0]['range'],
                      'shaded_mean_srgb': (base[shaded] * 255).mean(0).round(0).tolist()}

    # squeeze every body map and add the halberd strip
    strip2, height2, cells, blade_bounds = halberd_strip(S2)
    body2 = squeeze((np.clip(base, 0, 1) * 255).astype(np.uint8))
    x0 = int(round(STRIP_U0 * S2))
    body2[:, x0:x0 + strip2.shape[1]] = (strip2 * 255).astype(np.uint8)
    Image.fromarray(body2).save(T / 'gua_a_basecolor.png', optimize=True)
    Image.fromarray(body2).resize((N, N), Image.LANCZOS).save(T / 'gua_a_basecolor_1k.png', optimize=True)
    x1 = int(round(STRIP_U0 * N))
    n8 = squeeze(((normal * 0.5 + 0.5) * 255).astype(np.uint8))
    n8[:, x1:] = (128, 128, 255)
    # blade bevel relief from the strip's height map (1K)
    hs = np.asarray(Image.fromarray((height2 * 255).astype(np.uint8)).resize((N - x1, N), Image.LANCZOS),
                    np.float64)[:, :N - x1] / 255
    gy, gx = np.gradient(ndimage.gaussian_filter(hs, 0.7))
    bn = np.stack([-gx * 3.0, gy * 3.0, np.ones_like(hs)], -1)
    bn /= np.linalg.norm(bn, axis=-1, keepdims=True)
    n8[:, x1:] = ((bn * 0.5 + 0.5) * 255).astype(np.uint8)
    Image.fromarray(n8).save(T / 'gua_normal_1k.png', optimize=True)
    orm = squeeze(np.stack([ao, rough, metal], -1))
    orm[:, x1:] = (255, 200, 0)
    Image.fromarray(orm).save(T / 'gua_metal_rough_1k.png', optimize=True)
    masks = []
    for w in weights:
        m = squeeze((np.clip(w, 0, 1) * 255).astype(np.uint8)).astype(np.float64) / 255
        m[:, x0:] = 0
        masks.append(m)
    R.write_mask(masks, T / 'gua_region_mask.png', size=N)
    span = STRIP_U1 - STRIP_U0
    swatches = {name: [STRIP_U0 + c0 * span, 1 - r1 / S2, STRIP_U0 + c1 * span, 1 - r0 / S2]
                for name, (c0, r0, c1, r1) in cells.items()}
    swatches['blade_parts_h'] = blade_bounds
    swatches['body_u'] = BODY_U
    (T / 'halberd_swatches.json').write_text(json.dumps(swatches, indent=1) + '\n')
    config = {'variants': list(TIERS),
              'materials': [{'base': 'Guard_A', 'prefix': 'Guard', 'mask': 'gua_region_mask.png',
                             'regions': ['sleeves', 'trousers', 'mail'], 'palettes': TIERS,
                             'ramps': ramps, 'report': report}]}
    (T / 'gua_ramps.json').write_text(json.dumps(config, indent=1) + '\n')

    cls = np.zeros((N, N), np.uint8)
    for names, label in (({'ArmL', 'ArmR', 'FistL', 'FistR', 'Face', 'Hidden', 'HeadHidden'}, 1),
                         ({'SleeveL', 'SleeveR', 'LegL', 'LegR', 'ShoeL', 'ShoeR'}, 8),
                         ({'Torso', 'Coif', 'Helmet', 'Nasal'}, 9)):
        cls[raster(names, layout, N)] = label
    cls = squeeze(cls)
    cls[:, x1:] = 10
    Image.fromarray(cls, 'L').save(T / 'gua_material_classes.png')
    print('MAPS', json.dumps(report))


if __name__ == '__main__':
    main()
