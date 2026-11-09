#!/usr/bin/env python3
"""Baked metal look of the goblet and vase (quality pass round 2, 2026-10-16). Indoor decorations get no specular
(fs_model.sc: diffuse base x (1 - metallic); IndoorRenderer.cpp: no lobes, reflection x 0.1), so the sprites' local
contrast is baked into the albedo, from the lathe's own geometry only (rotationally symmetric: it does not depend on
the view or the placement's yaw). Texture: u once around, v along the LOD0 profile (small_profiles.arc_v).
Per texel a score = convexity of the profile (bright lip, bead, foot rim and knops; dark crevices where it turns in)
+ facing up (top bright, undersides dark) + height + inner-wall depth (dark bowl and neck) + the scan's grain, with
tarnish texels (Poly Haven rusty_metal_02 saturation, CC0) lower and with a wider grain. The score's area rank
(texel area ~ radius) picks a colour from the sprite's own ramp (its opaque pixels sorted by luminance; the vase
uses separate grey-metal and warm-tarnish ramps), eased toward the mean (the engine lights the model on top).
Metallic falls with the rank (dark reflections metal, highlights painted) and the base colour is ramp / (1 -
metallic), so the dungeon's diffuse shows the ramp itself while lit views keep metal. Writes
textures/misc_<prop>_baked_{basecolor,normal,mr}.png and the effective diffuse mean in misc_metal_means.json.
Usage: small_lathe_compose.py <prop>"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import small_profiles as sp  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(HERE, 'textures')
SRC = os.path.join(TEX, 'source', 'rusty_metal_02')
REPO = os.path.join(HERE, '..', '..', '..', '..')
X2 = next(p for p in (os.path.join(REPO, 'assets_legacy', 'decorations_x2_20261016'),
                      os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')) if os.path.isdir(p))
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)

SPECS = {
    '7dec46': dict(sprite='7dec46_p3.png', size=(256, 512), tile=(2, 4), split=False, tarnish=(0.5, 0.08),
                   weights=dict(convex=1.7, up=0.5, height=0.45, inner=1.1, grain=0.04, tarnish=0.35,
                                tarnish_grain=0.2, bands=1.6), ease=0.85, blur=1.5,
                   bands=[(0.14, 0.022, 1.0), (0.19, 0.03, 0.5), (0.29, 0.016, 0.7), (0.38, 0.035, -0.8)], metal_max=0.6, rough=(0.30, 0.42), dirty_rough=0.62,
                   normal=0.25),
    'dec97': dict(sprite='dec97_p3.png', size=(512, 1024), tile=(4, 8), split=True, tarnish=(0.34, 0.12),
                  weights=dict(convex=1.4, up=0.5, height=0.25, inner=1.0, grain=0.35, tarnish=0.0,
                               tarnish_grain=0.4, bands=1.3), ease=0.85, blur=0.5,
                  bands=[(0.15, 0.02, 1.0), (0.20, 0.035, 0.45), (0.34, 0.02, 0.55), (0.43, 0.035, -0.8)], metal_max=0.6, rough=(0.30, 0.45), dirty_rough=0.55,
                  normal=0.4),
}


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def ramp(pixels, n=256):
    """The sprite's colours by luminance rank: n stops, each the mean of a luminance-sorted slice."""
    order = np.argsort(pixels @ LUMA)
    chunks = np.array_split(pixels[order], n)
    return np.array([c.mean(0) for c in chunks], np.float32)


def rows(profile, height):
    """Per texture row (v from 0 at the bottom row to 1): radius, z, facing up, convexity, inner depth."""
    v, length = sp.arc_v(profile)
    rim = sp.rim_index(profile)
    pts = np.array([(r, z) for r, z, _ in profile], np.float32)
    zmax = pts[:, 1].max()
    vv = (np.arange(height) + 0.5) / height
    seg = np.clip(np.searchsorted(v, vv) - 1, 0, len(v) - 2)
    t = (vv - np.array(v)[seg]) / np.maximum(np.array(v)[seg + 1] - np.array(v)[seg], 1e-6)
    p = pts[seg] * (1 - t[:, None]) + pts[seg + 1] * t[:, None]
    d = pts[seg + 1] - pts[seg]
    d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
    up = -d[:, 0]                                        # outward normal (dz, -dr): its z is -dr
    # signed turn at every point (convex positive), spread over about 1.6 units of arc
    convex = np.zeros(height, np.float32)
    for i in range(1, len(profile) - 1):
        a = pts[i] - pts[i - 1]; b = pts[i + 1] - pts[i]
        if np.linalg.norm(a) < 1e-6 or np.linalg.norm(b) < 1e-6:
            continue
        a /= np.linalg.norm(a); b /= np.linalg.norm(b)
        turn = float(np.arctan2(a[0] * b[1] - a[1] * b[0], a @ b))
        if pts[i, 0] < 0.5:                              # the axis points of the bottom and the inner floor
            continue
        # sharp turns (lip, bead, foot rim, knops) as narrow highlights or crevices; the small turns of a smooth
        # curve as a broad, weak term (a narrow one would draw a stripe at every profile vertex)
        units = 1.2 if abs(turn) > 0.45 else 5.0
        width = units / length
        convex += turn * np.exp(-((vv - v[i]) / width) ** 2) * (1.2 / units) ** 0.5
    inner = np.where(np.arange(height) > 0, 0.0, 0.0)
    inside = vv > v[rim] + 0.5 / length
    inner = np.where(inside, -(0.35 + 0.65 * (1 - p[:, 1] / zmax)), 0.0)
    return p[:, 0], p[:, 1] / zmax, up, convex, inner


def norm(a):
    return (a - a.mean()) / max(a.std(), 1e-6)


def make(prop):
    s = SPECS[prop]
    w, h = s['size']
    tu, tv = s['tile']
    tw, th = w // tu, h // tv
    def tiled(kind, mode='RGB'):
        im = Image.open(os.path.join(SRC, f'rusty_metal_02_{kind}_1k.png')).convert(mode).resize((tw, th), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32) / 255.0
        return np.tile(a, (tv, tu, 1) if a.ndim == 3 else (tv, tu))
    scan = tiled('diff')
    scan = np.asarray(Image.fromarray((scan * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(s['blur']))) / 255.0
    satur = scan.max(2) - scan.min(2)
    thr, spread = s['tarnish']
    mask = np.clip((satur - thr) / spread, 0, 1)
    mask = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))) / 255.0
    grain = norm(scan @ LUMA)
    radius, height, up, convex, inner = rows(sp.PROFILES[prop], h)
    # image rows run top (v = 1) to bottom (v = 0)
    flip = lambda a: a[::-1][:, None]
    k = s['weights']
    score = (k['convex'] * flip(np.clip(convex, -1.5, 1.5)) + k['up'] * flip(up) + k['height'] * flip(height)
             + k['inner'] * flip(inner) + k['grain'] * grain * (1 - mask) + mask * (k['tarnish_grain'] * grain
                                                                                     - k['tarnish']))
    # v1's reflection bands, baked: a bright and a dark vertical band on each side (period 0.5 around), soft
    uu = (np.arange(w) + 0.5) / w
    band = np.zeros(w, np.float32)
    for c, width, amp in s['bands']:
        d = np.abs(uu % 0.5 - c); d = np.minimum(d, 0.5 - d)
        band += amp * np.exp(-(d / width) ** 2)
    score = score + k['bands'] * band[None, :] * (1 - 0.5 * mask)
    area = np.broadcast_to(flip(np.maximum(radius, 0.3)), score.shape)
    pixels = np.asarray(Image.open(os.path.join(X2, s['sprite'])).convert('RGBA')).astype(np.float32)
    pixels = pixels[pixels[..., 3] > 128][:, :3] / 255.0
    psat = pixels.max(1) - pixels.min(1)
    out = np.zeros((h, w, 3), np.float32)
    rank = np.zeros((h, w), np.float32)
    classes = [(mask < 0.5, psat < 20 / 255), (mask >= 0.5, psat >= 20 / 255)] if s['split'] else \
        [(np.ones_like(mask, bool), np.ones(len(pixels), bool))]
    for texels, sprite_px in classes:
        stops = ramp(pixels[sprite_px])
        sc = score[texels]; wt = area[texels]
        order = np.argsort(sc)
        cum = np.empty_like(sc); cum[order] = np.cumsum(wt[order]) / wt.sum()
        idx = np.clip((cum * (len(stops) - 1)).astype(int), 0, len(stops) - 1)
        col = stops[idx]
        mean = (stops * 1.0).mean(0)
        col = mean + (col - mean) * s['ease']
        out[texels] = col
        rank[texels] = cum
    metal = s['metal_max'] * (1 - rank) * (1 - 0.5 * mask)
    base_lin = np.clip(lin(out) / (1 - metal[..., None]), 0, 1)
    clipped = float((lin(out) / (1 - metal[..., None]) > 1).any(2).mean())
    rough = tiled('rough', 'L')
    lo, hi = s['rough']
    rough = lo + (hi - lo) * (rough - rough.min()) / max(1e-6, rough.max() - rough.min())
    rough = (1 - mask) * rough + mask * s['dirty_rough']
    nor = tiled('nor_gl') * 2 - 1
    kk = s['normal'] * (1 - mask) + mask
    nor[..., :2] *= kk[..., None]
    nor /= np.linalg.norm(nor, axis=2, keepdims=True)
    name = f'misc_{prop}_baked'
    Image.fromarray((srgb(base_lin) * 255 + 0.5).clip(0, 255).astype(np.uint8)).save(os.path.join(TEX, f'{name}_basecolor.png'))
    Image.fromarray(((nor + 1) * 127.5 + 0.5).clip(0, 255).astype(np.uint8)).save(os.path.join(TEX, f'{name}_normal.png'))
    mr = np.stack([np.zeros_like(rough), rough, metal], 2)
    Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).save(os.path.join(TEX, f'{name}_mr.png'))
    eff = (base_lin * (1 - metal[..., None]) * area[..., None]).reshape(-1, 3).sum(0) / area.sum()
    path = os.path.join(TEX, 'misc_metal_means.json')
    means = json.load(open(path)) if os.path.exists(path) else {}
    means[name] = [float(x) for x in eff]
    open(path, 'w').write(json.dumps(means, indent=1, sort_keys=True) + '\n')
    print('BAKED', prop, 'effective mean', (srgb(eff) * 255).round().astype(int).tolist(), 'sprite mean',
          (pixels.mean(0) * 255).round().astype(int).tolist(), 'clipped', round(clipped, 3),
          'tarnish', round(float(mask.mean()), 3))


if __name__ == '__main__':
    for p in sys.argv[1:] or SPECS:
        make(p)
