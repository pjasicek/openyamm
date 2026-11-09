#!/usr/bin/env python3
"""Statue textures from the bake (statue_<model>.py --stage bake) and the native sprites (native shading transfer,
level_generation/creatures/NATIVE_SHADING_TRANSFER.md, applied to a static prop): per texel a score from the
creature's own painted luminance (carved detail: beard strands, mail rings, folds), baked occlusion, up-facing normal
and a box-projected CC0 stone grain; the base colour is the sprites' own colour ramp (their opaque pixels sorted by
luminance, gold excluded) at the texel's area rank of that score, with its contrast eased (the engine lights the
model on top). Texels of saturated yellow in the creature atlas (buttons, buckles, studs) take the sprites' gold ramp
when the statue has gold trim. Normal map: the creature's own, halved; roughness uniform.
Also writes the shared tileable stone (statue_stone_*) for the procedural parts, from Poly Haven rock_01.
Usage: statue_compose.py <prop>   |   statue_compose.py stone"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(HERE, 'textures')
WORK = os.path.join(HERE, 'work')
SRC = os.path.join(WORK, 'statue_src')
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_dev', 'engine', 'decorations_x2')
if not os.path.exists(os.path.join(X2, '7dec54a0_p3.png')):        # the statue sprites were archived 2026-10-16
    X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_legacy', 'decorations_x2_20261016')
LUMA = np.array([0.2126, 0.7152, 0.0722])

SPECS = {
    'dec94': {'atlas': None, 'normal': None, 'sprites': ['dec94_p2.png'], 'rows': 0.76, 'gold': False,
              'size': (1024, 1024), 'weights': (0.0, 0.5, 0.3, 0.2), 'contrast': 0.8, 'absolute': 0.0},
    'dec95': {'atlas': 'mm6_kni__kni_body_basecolor.png', 'normal': 'mm6_kni__kni_body_normal_1k.png',
              'sprites': ['dec95_p2.png'], 'rows': 0.74, 'gold': False, 'size': (1024, 1024),
              'weights': (0.16, 0.48, 0.24, 0.08), 'contrast': 0.8, 'absolute': 0.04, 'normal_size': (512, 512)},
    '7dec55': {'atlas': 'mm6_dwa1__dwa1_basecolor_1k_head_atlas.png', 'normal': 'mm6_dwa1__dwa1_normal_1k_head_atlas.png',
               'sprites': [f'7dec55a{k}_p3.png' for k in range(4)], 'gold': False, 'size': (1536, 768),
               'weights': (0.16, 0.48, 0.24, 0.08), 'contrast': 0.8, 'absolute': 0.04},
    '7dec54': {'atlas': 'mm6_dwa1__dwa1_basecolor_1k_head_atlas.png', 'normal': 'mm6_dwa1__dwa1_normal_1k_head_atlas.png',
               'sprites': [f'7dec54a{k}_p3.png' for k in range(5)], 'gold': True, 'size': (1536, 768),
               'weights': (0.16, 0.48, 0.24, 0.08), 'contrast': 0.8, 'absolute': 0.04},
}


def load(path, size=None, mode='RGB'):
    im = Image.open(path).convert(mode)
    if size and im.size != size:
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255


def gold_mask(rgb, bright=0.24):
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    return (sat > 0.35) & (rgb[..., 0] > rgb[..., 1]) & (rgb[..., 1] > rgb[..., 2]) & (mx > bright)


def atlas_gold_mask(rgb):
    """Brass on the creature atlas (studs, buckles, rings): bright, saturated, hue 38-58 degrees, grown by two
    texels so the shaded sides of a stud follow its highlight. (The sprite test above also passes brown leather.)"""
    from scipy.ndimage import binary_dilation
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = np.maximum(mx - mn, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.where(mx == r, 60 * ((g - b) / d % 6), np.where(mx == g, 60 * ((b - r) / d + 2), 60 * ((r - g) / d + 4)))
    core = ((mx - mn) / np.maximum(mx, 1e-3) > 0.4) & (mx > 0.45) & (hue > 38) & (hue < 58)
    return binary_dilation(core, iterations=2)


def sprite_pixels(names, gold, rows=1.0):
    pix = []
    for n in names:
        im = load(os.path.join(X2, n), mode='RGBA')
        im = im[:int(round(im.shape[0] * rows))]                 # rows: the figure above the plinth
        p = im[im[..., 3] > 0.5][:, :3]
        g = gold_mask(p)
        pix.append(p[g] if gold else p[~g])
    p = np.concatenate(pix)
    return p[np.argsort(p @ LUMA)]


def ramp(rank, colours):
    n = len(colours)
    k = max(1, n // 100)
    cs = np.cumsum(np.vstack([np.zeros(3), colours]), axis=0)
    idx = np.clip((rank * (n - 1)).astype(int), 0, n - 1)
    lo, hi = np.clip(idx - k, 0, n), np.clip(idx + k + 1, 0, n)
    return (cs[hi] - cs[lo]) / (hi - lo)[:, None]


def rank(values):
    order = np.argsort(values, kind='stable')
    r = np.empty(len(values), np.float32); r[order] = np.linspace(0, 1, len(values))
    return r


def save(path, rgb, size=None):
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))
    if size and im.size != size:
        im = im.resize(size, Image.LANCZOS)
    im.save(path); print('WROTE', path, im.size)


def dilate_fill(rgb, covered, steps=24):
    """Grow covered colours into the uncovered texels (mip-safe margins), the rest gets the mean."""
    out = rgb.copy(); cov = covered.copy()
    for _ in range(steps):
        acc = np.zeros_like(out); cnt = np.zeros(cov.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(out * cov[..., None], dy, 0), dx, 1)
            c = np.roll(np.roll(cov, dy, 0), dx, 1)
            acc += sh; cnt += c
        grow = (~cov) & (cnt > 0)
        out[grow] = acc[grow] / cnt[grow, None]; cov = cov | grow
    out[~cov] = rgb[covered].mean(0)
    return out


def compose(prop):
    spec = SPECS[prop]
    w, h = spec['size']
    atlas = load(os.path.join(SRC, spec['atlas']), (w, h)) if spec['atlas'] else np.zeros((h, w, 3), np.float32)
    bake = np.load(os.path.join(WORK, f'{prop}_bake.npy'))[::-1]          # Blender rows run bottom to top
    bake = np.stack([np.asarray(Image.fromarray(bake[..., c]).resize((w, h), Image.BILINEAR)) for c in range(4)], -1)
    covered = bake[..., 3] > 0.5
    stone, ao, up = bake[..., 0], bake[..., 1], bake[..., 2]
    lum = atlas @ LUMA
    # Carved detail = the painted luminance's local contrast (normalised blur inside the covered texels), so dark
    # paint (black beard, green tunic) does not turn into dark stone; a little absolute luminance stays.
    from scipy.ndimage import gaussian_filter

    def blur(a, r):
        return gaussian_filter(a.astype(np.float32), r)
    m = covered.astype(np.float32)
    local = blur(lum * m, 2.5) / np.maximum(blur(m, 2.5), 1e-3)
    detail = blur(lum - local, 0.8)
    ao = blur(ao * m, 2.0) / np.maximum(blur(m, 2.0), 1e-3)         # bake noise
    cov = covered.ravel()
    wl, wa, wu, ws = spec['weights']
    wabs = spec.get('absolute', 0.12)
    score = (wl * rank(detail.ravel()[cov]) + wabs * rank(lum.ravel()[cov]) + wa * rank(ao.ravel()[cov])
             + wu * up.ravel()[cov] + ws * rank(stone.ravel()[cov]))
    stone_ramp = sprite_pixels(spec['sprites'], gold=False, rows=spec.get('rows', 1.0))
    colour = ramp(rank(score), stone_ramp)
    mean = colour.mean(0)
    colour = mean + (colour - mean) * spec['contrast']
    colour = colour * spec.get('gain', 1.12)          # headroom: COLOR_0 (occlusion x tint) only darkens
    out = np.zeros((h * w, 3), np.float32); out[cov] = colour
    if spec['gold']:
        gold = atlas_gold_mask(atlas).ravel() & cov
        gold_ramp = sprite_pixels(spec['sprites'], gold=True)
        gscore = 0.6 * rank(lum.ravel()[gold]) + 0.4 * up.ravel()[gold]
        out[gold] = ramp(rank(gscore), gold_ramp)
        print('GOLD texels', int(gold.sum()))
    out = dilate_fill(out.reshape(h, w, 3), covered)
    print('MEAN', prop, (out[covered].mean(0) * 255).round(), 'sprite stone mean', (stone_ramp.mean(0) * 255).round())
    exposed = covered & (np.asarray(Image.fromarray(ao).resize((w, h))) > 0.6) if False else covered & (ao > 0.6)
    import json
    json.dump({'exposed_mean': (out[exposed].mean(0) * 255).round(1).tolist(),
               'texture_mean': (out[covered].mean(0) * 255).round(1).tolist()},
              open(os.path.join(WORK, f'{prop}_texture.json'), 'w'))
    print('EXPOSED mean', (out[exposed].mean(0) * 255).round())
    save(os.path.join(TEX, f'statue_{prop}_basecolor.png'), out)
    if spec['normal'] is None:                     # no painted normals (MPFB body): a flat map
        normal = np.ones((16, 16, 3), np.float32) * np.array([0.5, 0.5, 1.0], np.float32)
        save(os.path.join(TEX, f'statue_{prop}_normal.png'), normal)
        mr = np.zeros((32, 64, 3), np.float32); mr[..., 1] = 0.85
        save(os.path.join(TEX, f'statue_{prop}_mr.png'), mr)
        return
    normal = load(os.path.join(SRC, spec['normal']))
    save(os.path.join(TEX, f'statue_{prop}_normal.png'), normal, spec.get('normal_size', (1024, 512)))
    mr = np.zeros((32, 64, 3), np.float32); mr[..., 1] = 0.8
    save(os.path.join(TEX, f'statue_{prop}_mr.png'), mr)


def stone_tile():
    """Neutral tileable stone (Poly Haven rock_01, CC0): luminance kept, colour pulled to grey at mean 0.5, 512."""
    src = os.path.join(TEX, 'source', 'rock_01')
    diff = load(os.path.join(src, 'rock_01_diff_1k.png'), (512, 512))
    lum = diff @ LUMA
    grey = 0.85 * lum[..., None] + 0.15 * diff
    grey = 0.5 + (grey - grey.mean()) * 1.3
    save(os.path.join(TEX, 'statue_stone_basecolor.png'), grey)
    save(os.path.join(TEX, 'statue_stone_normal.png'), load(os.path.join(src, 'rock_01_nor_gl_1k.png'), (512, 512)))
    rough = load(os.path.join(src, 'rock_01_rough_1k.png'), (256, 256))[..., 0]
    mr = np.zeros((256, 256, 3), np.float32); mr[..., 1] = 0.55 + 0.4 * rough
    save(os.path.join(TEX, 'statue_stone_mr.png'), mr)
    # a light variant (mean 0.78) for parts brighter than mid grey (axe blades), so their tint stays below one
    light = 0.78 + (grey - grey.mean()) * 0.8
    save(os.path.join(TEX, 'statue_stonelight_basecolor.png'), light)
    save(os.path.join(TEX, 'statue_stonelight_normal.png'), load(os.path.join(src, 'rock_01_nor_gl_1k.png'), (512, 512)))
    save(os.path.join(TEX, 'statue_stonelight_mr.png'), mr)
    # weathered granite for plinths (Poly Haven rock_surface, CC0): luminance and a little colour, mean 0.6
    src2 = os.path.join(TEX, 'source', 'rock_surface')
    diff = load(os.path.join(src2, 'rock_surface_diff_1k.png'), (512, 512))
    g = 0.7 * (diff @ LUMA)[..., None] + 0.3 * diff
    save(os.path.join(TEX, 'statue_granite_basecolor.png'), 0.6 + (g - g.mean()) * 1.2)
    save(os.path.join(TEX, 'statue_granite_normal.png'), load(os.path.join(src2, 'rock_surface_nor_gl_1k.png'), (512, 512)))
    rough = load(os.path.join(src2, 'rock_surface_rough_1k.png'), (256, 256))[..., 0]
    mr2 = np.zeros((256, 256, 3), np.float32); mr2[..., 1] = 0.6 + 0.35 * rough
    save(os.path.join(TEX, 'statue_granite_mr.png'), mr2)


if __name__ == '__main__':
    if sys.argv[1] == 'stone':
        stone_tile()
    else:
        compose(sys.argv[1])
