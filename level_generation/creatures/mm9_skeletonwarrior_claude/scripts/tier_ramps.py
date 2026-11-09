#!/usr/bin/env python3
"""Region masks and ramps for the two tiers on one shared paint.
Tier skelwar_c = Skeleton Master (MM9 SKELETONWAR1: red lacquer lamellar, blue lacing, red eyes), the paint itself.
Tier skelwar_b = Skeleton Warrior (SKELETONWAR2): MM9 paints plain black mail where the Master has lamellar, amber eyes, dimmer
horns, no brow insignia. Regions (per texel, in each set's own UV layout, only on the parts named):
R lacquer: red plates (hue) on the armour parts, the brow insignia whole; G lacing: blue on the armour parts; B eyes: the eye
parts whole; A horns (head set only). Ramps: tier C is the paint fitted to itself; tier B takes MM9's own colours: the WAR2 skin at the
texels where the WAR1 skin is red or blue, sorted by luminance and scaled to the paint's lightness (the sprite rule: albedo about
1.35 x a skin with baked shading), matched by quantiles. Writes textures/skelwar[_head]_region_mask.png, textures/skelwar_ramps.json
and the eye emission mask."""
import colorsys, json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import region_variants as RV
T = Path('textures')
F = np.load('work/faces.npz')
S = 1024
ARM_B = [8, 9, 17, 35, 36, 59, 117, 135, 136, 159, 14, 16, 25, 30, 32, 33, 38, 41, 42, 47, 49, 50, 56, 57, 58, 60, 61, 65]
ARM_H = [22, 26, 40, 54, 55, 63, 126, 140, 154, 155, 163, 21]


def raster(uv, ids):
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    keep = np.isin(F['pid'], ids) & (F['lining'] == 0)
    for t in uv[keep]:
        d.polygon([(float(u * S), float((1 - v) * S)) for u, v in t], fill=255)
    return ndimage.binary_dilation(np.asarray(im) > 0, iterations=2)


def hsv(rgb):
    mx, mn = rgb.max(2), rgb.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return hue, sat, mx


def soft(m):
    return np.clip(ndimage.gaussian_filter(m.astype(np.float32), 0.8) * 1.25, 0, 1)


m1 = np.asarray(Image.open('source/war1/skins/skelwar1.png').convert('RGB'), np.float64) / 255
m2 = np.asarray(Image.open('source/war2/skins/skelwar2.png').convert('RGB'), np.float64) / 255
h1, s1, v1 = hsv(m1)
red9 = ((h1 < 20) | (h1 > 340)) & (s1 > 0.4) & (v1 > 0.2)
blue9 = (h1 > 170) & (h1 < 250) & (s1 > 0.25) & (v1 > 0.12)
print('MM9 texels red', red9.sum(), 'blue', blue9.sum())


def mm9_ramp(sel):
    """16 sorted colours (linear) of the WAR2 skin at the selected WAR1 texels."""
    px = RV.srgb_to_linear(m2[sel]); lum = px @ RV.LUMA
    o = np.argsort(lum); px = px[o]
    q = np.linspace(0, len(px) - 1, 16).astype(int)
    return np.array([px[max(0, i - 6):i + 7].mean(0) for i in q])


def quantile_target(base, w, ramp, gain):
    """Target image: each region texel takes the ramp colour at its luminance rank."""
    lum = RV.luminance(base); core = w > 0.5
    order = np.sort(lum[core]); rank = np.searchsorted(order, lum) / max(1, len(order) - 1)
    t = np.clip(rank, 0, 1) * 15
    i = np.minimum(t.astype(int), 14); f = (t - i)[..., None]
    lin = ramp[i] * (1 - f) + ramp[i + 1] * f
    lin = np.clip(lin * gain, 0, 1)
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return srgb


cfg = {'variants': ['skelwar_b', 'skelwar_c'], 'materials': []}
reports = {}
LACQ_GAIN, LACE_GAIN = 1.05, 1.0
for name, base_file, mat, uvk, arm, extra in (
        ('body', 'skelwar_basecolor_final.png', 'SkelWar', 'ub', ARM_B, None),
        ('head', 'skelwar_head_basecolor_final.png', 'SkelWarHead', 'uh', ARM_H, True)):
    base = RV.load_srgb(T / base_file, S)
    hue, sat, val = hsv(base)
    a = raster(F[uvk], arm)
    red = a & ((hue < 26) | (hue > 330)) & (sat > 0.16) & (val > 0.1)
    blue = a & (hue > 165) & (hue < 255) & (sat > 0.18) & (val > 0.08)
    regions = []
    if extra:
        ins = raster(F[uvk], [11, 45])
        red = red | ins
        eyes = raster(F[uvk], [19, 119])
        horns = raster(F[uvk], [15, 46, 115])
    w = [soft(ndimage.binary_closing(red, iterations=2)), soft(ndimage.binary_closing(blue, iterations=1))]
    if extra:
        w += [soft(eyes), soft(horns)]
    tiers = []
    targets = [quantile_target(base, w[0], mm9_ramp(red9), LACQ_GAIN), quantile_target(base, w[1], mm9_ramp(blue9), LACE_GAIN)]
    if extra:
        # MM9 WAR2's amber eye; its rim stays dark
        eye = np.zeros_like(base); lum = RV.luminance(base)
        t = np.clip((lum - np.percentile(lum[w[2] > .9], 5)) / (np.percentile(lum[w[2] > .9], 95) - np.percentile(lum[w[2] > .9], 5)), 0, 1)[..., None]
        eye = np.array([0.33, 0.13, 0.0]) * (1 - t) + np.array([1.0, 0.72, 0.22]) * t
        horn = base * np.array([0.5, 0.45, 0.4])
        targets += [eye, horn]
    ramps = {'skelwar_b': [], 'skelwar_c': []}; rep = []
    for i, wi in enumerate(w):
        fitted, r = RV.fit_ramps(base, {'skelwar_b': targets[i], 'skelwar_c': base}, wi)
        ramps['skelwar_b'].append(fitted['skelwar_b']); ramps['skelwar_c'].append(fitted['skelwar_c']); rep.append(r)
    mask_name = f"skelwar{'_head' if extra else ''}_region_mask.png"
    RV.write_mask(w, T / mask_name, S)
    cfg['materials'].append({'base': mat, 'prefix': mat, 'mask': mask_name, 'ramps': ramps})
    reports[name] = rep
    print(name, [round(float((x > .5).mean() * 100), 1) for x in w], rep)
    if extra:
        # the glow follows the paint's own eye: bright middle, dark rim
        lum = RV.luminance(base); e = raster(F[uvk], [19, 119])
        g = np.clip(lum / np.percentile(lum[e], 98), 0, 1) ** 0.8 * e
        Image.fromarray((g * 255).astype(np.uint8)).save(T / 'skelwar_head_eye_mask.png')
json.dump(cfg, open(T / 'skelwar_ramps.json', 'w'))
json.dump(reports, open('work/ramps_report.json', 'w'), indent=1)
