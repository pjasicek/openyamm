#!/usr/bin/env python3
"""Wing tone of the texture pass against the approved look (coordinator request 2026-10-30: membrane tinted back, new
sharpness and layout kept). The approved rework (work/before_texpass) and the current maps are compared as the game
shows them: Wmut_Wing LOD0 surface sampled area-weighted, region-mask wing texels only, each tier's ramp applied.

Usage: wing_tone.py [--write]
--write stores textures/wmut_wing_tone.json: per tier a wing ramp fitted by quantile matching: a texel at quantile p of
the current wing targets the approved ramp's colour at the approved wing's quantile p (least squares on the 16 stops,
range cut at the 98.5th percentile so the stops sit where the texels are). So tone, contrast and hue of every tier
follow the approved wing while the texels stay sharp.
compose.py puts these ramps in the wing channel.
Prints per tier mean sRGB, luminance sd (sRGB levels), and the band contrast of the luminance at the pebble scale."""
import argparse, io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV
import texture_quality as TQ

W = np.array([0.2126, 0.7152, 0.0722])
N = 600000
BEFORE = HERE / 'work' / 'before_texpass'


def surface(glb, seed=7):
    doc, binary = TQ.read_glb(glb)
    mesh = doc['meshes'][0]
    prim = next(p for p in mesh['primitives'] if doc['materials'][p['material']]['name'].startswith('Wmut_Wing'))
    pos = TQ.accessor(doc, binary, prim['attributes']['POSITION'])
    uv = TQ.accessor(doc, binary, prim['attributes']['TEXCOORD_0'])
    idx = TQ.accessor(doc, binary, prim['indices']).astype(np.int64).reshape(-1, 3)
    p = pos[idx]
    area = np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1) / 2
    rng = np.random.default_rng(seed)
    t = rng.choice(len(idx), N, p=area / area.sum())
    r = np.sqrt(rng.random(N))[:, None]
    s = rng.random(N)[:, None]
    q = uv[idx[t]]
    return q[:, 0] * (1 - r) + q[:, 1] * r * (1 - s) + q[:, 2] * r * s


def sample(img, uv):
    h, w = img.shape[:2]
    xy = [uv[:, 1] * h - 0.5, uv[:, 0] * w - 0.5]
    if img.ndim == 2:
        return ndimage.map_coordinates(img, xy, order=1, mode='nearest')
    return np.stack([ndimage.map_coordinates(img[..., k], xy, order=1, mode='nearest') for k in range(img.shape[2])], -1)


def ramp_eval(ramp, lum):
    lo, hi = ramp['range']
    c = np.array(ramp['colors'])
    x = np.clip((lum - lo) / (hi - lo), 0, 1) * 15
    i = np.minimum(x.astype(int), 14)
    f = (x - i)[:, None]
    return c[i] * (1 - f) + c[i + 1] * f


def enc(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def load(tex, mask, ramps_json, glb, scale):
    uv = surface(glb)
    rgb = RV.load_srgb(tex)
    lin = RV.srgb_to_linear(rgb)
    m = np.asarray(Image.open(mask).convert('RGBA'), np.float32) / 255
    keep = sample(m[..., 2], uv) > 0.9
    lum = sample(lin @ W, uv)[keep]
    base = lin @ W
    d = float(scale)
    band = ndimage.gaussian_filter(base, 2.0 * d) - ndimage.gaussian_filter(base, 8.0 * d)
    fine = base - ndimage.gaussian_filter(base, 2.0 * d)
    R = json.load(open(ramps_json))
    mat = next(x for x in R['materials'] if x['base'] == 'Wmut_Wing')
    return {'lum': lum, 'ramps': {k: mat['ramps'][k][2] for k in R['variants']},
            'band': sample(band, uv)[keep], 'fine': sample(fine, uv)[keep], 'n': int(keep.sum()), 'R': R}


ap = argparse.ArgumentParser()
ap.add_argument('--write', action='store_true')
args = ap.parse_args()
a = load(BEFORE / 'textures' / 'wmut_basecolor_graded_v2.png', BEFORE / 'textures' / 'wmut_region_mask_v2.png',
         BEFORE / 'textures' / 'wmut_ramps_v2.json', BEFORE / 'mm9_wingedmutant_installed.glb', 1.0)
b = load(HERE / 'textures' / 'wmut_basecolor_graded_v2.png', HERE / 'textures' / 'wmut_region_mask_v2.png',
         HERE / 'textures' / 'wmut_ramps_v2.json', HERE / 'export' / 'mm9_wingedmutant.glb', 2.51)
q = (np.arange(4096) + 0.5) / 4096
qa, qb = np.quantile(a['lum'], q), np.quantile(b['lum'], q)
new = {}
rank = np.interp(b['lum'], qb, q)
lo, hi = b['ramps']['wmut_a']['range'][0], float(np.quantile(b['lum'], 0.985))    # stops where the wing's texels are
x = np.clip((b['lum'] - lo) / (hi - lo), 0, 1) * 15
i0 = np.minimum(x.astype(int), 14)
f = x - i0
basis = np.zeros((len(x), 16))
basis[np.arange(len(x)), i0] = 1 - f
basis[np.arange(len(x)), i0 + 1] = f
for k in b['ramps']:
    target = ramp_eval(a['ramps'][k], np.interp(rank, q, qa))
    weight = 1 / (target @ W + 0.02)                      # about perceptual: dark texels count as much as bright ones
    A = basis * weight[:, None]
    second = np.zeros((14, 16))
    for r in range(14):
        second[r, r:r + 3] = (1, -2, 1)
    colors = np.linalg.solve(A.T @ A + 1e-3 * len(x) * second.T @ second, A.T @ (target * weight[:, None]))
    new[k] = {'range': [round(lo, 6), round(hi, 6)], 'colors': np.round(np.clip(colors, 0, 1), 6).tolist()}
for k in b['ramps']:
    ca = enc(ramp_eval(a['ramps'][k], a['lum']))
    cb = enc(ramp_eval(b['ramps'][k], b['lum']))
    cn = enc(ramp_eval(new[k], b['lum']))
    fmt = lambda c: f'{np.round(c.mean(0) * 255).astype(int)} sd {(c @ W).std() * 255:.1f}'
    print(k, 'approved', fmt(ca), '| current', fmt(cb), '| matched', fmt(cn))
print('samples', a['n'], b['n'], 'linear lum p5/50/95 approved', np.percentile(a['lum'], [5, 50, 95]).round(4),
      'current', np.percentile(b['lum'], [5, 50, 95]).round(4))
print('pebble band sd (same surface scale), relative to mean lum: approved %.3f current %.3f; fine %.3f / %.3f' % (
    a['band'].std() / a['lum'].mean(), b['band'].std() / b['lum'].mean(),
    a['fine'].std() / a['lum'].mean(), b['fine'].std() / b['lum'].mean()))
if args.write:
    json.dump({'note': 'Wing ramps quantile-matched to the approved wing (scripts/wing_tone.py).', 'ramps': new},
              open(HERE / 'textures' / 'wmut_wing_tone.json', 'w'), indent=1)
    print('WROTE wmut_wing_tone.json')
