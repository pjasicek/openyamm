#!/usr/bin/env python3
"""Unique texture set of one sack (revision 2) from its bakes (build_sacks.py bake), a CC0 Poly Haven hessian weave
(textures/polyhaven/) and the native sprite's painted shading and palette (the native shading transfer,
level_generation/creatures/NATIVE_SHADING_TRANSFER.md, adapted to a static prop):

- shading score per texel = weighted, standardised sum of: the sprite's median luminance at the texel's height (the
  painted light from above), the baked up-facing component of the fold normals (lit tops, dark undersides), fold
  convexity (bright ridges, dark creases), baked ambient occlusion with the floor, and the hessian's own luminance
  (the weave);
- base colour = the sprite's own colour ramp (its body texels sorted by luminance, rim outline excluded) read at the
  texel's area-weighted rank of that score, so the sack carries the sprite's colour distribution: saturated dark
  browns in the creases, golden highlights on the ridges;
- normal = baked fold normals with the hessian normal map blended in (UDN); roughness = the hessian roughness,
  remapped to a matte fabric range (metallic-roughness texture: G roughness, B metal 0).
bag_a also gets a twisted three-strand rope texture coloured from the sprite's rope texels.
Writes textures/<prop>_{basecolor,normal,mr}.png (and bag_a_rope_*). Usage: compose_sacks.py <prop>"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'level_generation', 'creatures', 'claude_shared'))
import native_shading as ns  # noqa: E402

BAKE = os.path.join(HERE, 'work', 'bake')
OUT = os.path.join(HERE, 'textures')
POLYHAVEN = os.path.join(OUT, 'polyhaven')
X2 = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')

# weights: height profile, up-facing normal, fold convexity, occlusion, weave; mottle: low-frequency blotches;
# gain: linear albedo scale; saturation: ramp saturation; weave_normal: UDN strength; rough: roughness range.
SETTINGS = {
    'bag_a': {'weave': 'hessian_380', 'sprite': 'bag_a_p547.png',
              'weights': (1.2, 0.9, 0.4, 1.0, 0.35), 'mottle': 1.3, 'gain': 0.65, 'saturation': 1.08, 'weave_normal': 0.5,
              'rough': (0.62, 0.92)},
    'bag01': {'weave': 'hessian_230', 'sprite': 'bag01_p547.png',
              'weights': (0.35, 0.55, 1.0, 0.9, 0.55), 'mottle': 0.3, 'gain': 0.8, 'saturation': 1.15, 'weave_normal': 0.9,
              'rough': (0.7, 0.98)},
    'floursac': {'weave': 'hessian_230', 'sprite': 'floursac_p547.png',
                 'weights': (0.45, 0.55, 1.0, 0.9, 0.55), 'mottle': 0.4, 'gain': 0.8, 'saturation': 1.15, 'weave_normal': 0.9,
                 'rough': (0.7, 0.98)},
}


def standard(x, mask):
    values = x[mask]
    return (x - values.mean()) / (values.std() + 1e-9)


def load_rgb(path):
    return np.asarray(Image.open(path).convert('RGB'), np.float64) / 255.0


def tiled(image, u_repeat, v_repeat, size):
    """The tile resampled to one repeat's texel size, then repeated over a size x size map (row 0 = v 0)."""
    tile_w = max(8, int(round(size / u_repeat)))
    tile_h = max(8, int(round(size / v_repeat)))
    mode = 'RGB' if image.ndim == 3 else 'L'
    data = (np.clip(image, 0, 1) * 255 + 0.5).astype(np.uint8)
    small = np.asarray(Image.fromarray(data, mode).resize((tile_w, tile_h), Image.LANCZOS), np.float64) / 255.0
    reps = (int(np.ceil(size / tile_h)) + 1, int(np.ceil(size / tile_w)) + 1) + ((1,) if image.ndim == 3 else ())
    return np.tile(small, reps)[:size, :size]


def sprite_regions(name):
    rgba = np.asarray(Image.open(os.path.join(X2, name)).convert('RGBA'), np.float64) / 255.0
    alpha = rgba[..., 3] > 0.5
    inner = alpha                       # the outline and the dark limbs are part of the sprite's colour range
    rgb = rgba[..., :3]
    spread = rgb.max(-1) - rgb.min(-1)
    grey = spread < 22 / 255
    rope_core = grey & (rgb.mean(-1) > 80 / 255) & inner
    near_rope = ndimage.binary_dilation(rope_core, iterations=2) & inner
    rope = near_rope & grey & (rgb.mean(-1) > 40 / 255)             # the rope's light crowns and grey grooves
    body = inner & ~near_rope
    rows = np.where(alpha.any(1))[0]
    top, bottom = rows[0], rows[-1]
    return rgb, alpha, body, rope, top, bottom


def colour_ramp(rgb, mask, stops=256):
    """Mean colour per equal-count luminance bin of the masked texels (dark to bright)."""
    pixels = rgb[mask]
    lum = ns.srgb_luminance(pixels)
    order = np.argsort(lum)
    bins = np.array_split(order, stops)
    return np.array([pixels[b].mean(0) for b in bins])


def height_profile(rgb, body, top, bottom, bins=40):
    """Median luminance of the central band of the body per height bin (0 bottom, 1 top)."""
    lum = ns.srgb_luminance(rgb)
    profile = np.zeros(bins)
    for k in range(bins):
        r0 = int(round(bottom - (k + 1) / bins * (bottom - top)))
        r1 = int(round(bottom - k / bins * (bottom - top)))
        values = []
        for r in range(max(r0, top), min(r1, bottom) + 1):
            cols = np.where(body[r])[0]
            if len(cols) < 4:
                continue
            centre, half = (cols[0] + cols[-1]) / 2, (cols[-1] - cols[0]) / 2
            keep = cols[np.abs(cols - centre) <= half * 0.7]
            values.extend(lum[r, keep])
        profile[k] = np.median(values) if values else np.nan
    good = ~np.isnan(profile)
    profile = np.interp(np.arange(bins), np.where(good)[0], profile[good])
    return ndimage.gaussian_filter1d(profile, 1.0)


def weighted_rank(score, weight, mask):
    values = score[mask]
    w = weight[mask]
    order = np.argsort(values)
    cumulative = np.cumsum(w[order])
    cumulative = (cumulative - 0.5 * w[order]) / cumulative[-1]
    ranks = np.empty_like(values)
    ranks[order] = cumulative
    out = np.full(score.shape, 0.5)
    out[mask] = ranks
    return out


def save(name, rgb, size=None):
    path = os.path.join(OUT, name)
    image = Image.fromarray((np.clip(np.flipud(rgb), 0, 1) * 255 + 0.5).astype(np.uint8))
    if size:
        image = image.resize((size, size), Image.LANCZOS)
    image.save(path, optimize=True)
    os.chmod(path, 0o664)
    print('WROTE', path)


def rope_textures(rgb, rope_mask, size=512):
    """Three twisted strands with a diagonal lay (u around the rope, v along it), coloured from the sprite's rope."""
    y, x = np.mgrid[0:size, 0:size] / size
    rng = np.random.default_rng(11)
    phase = (y * 6 + x * 3) % 1.0
    crown = np.sin(np.pi * phase) ** 0.4
    fibre = ndimage.gaussian_filter(rng.normal(size=(size, size)), (0.6, 3.0), mode='wrap')
    fibre = (fibre - fibre.mean()) / fibre.std()
    lay = ndimage.gaussian_filter(rng.normal(size=(size, size)), 1.2, mode='wrap')
    lay = (lay - lay.mean()) / lay.std()
    height = crown + 0.06 * fibre + 0.03 * lay
    score = crown * 1.0 + 0.12 * fibre
    ramp = colour_ramp(rgb, rope_mask)
    flat = score.ravel()
    ranks = np.empty(flat.size)
    ranks[np.argsort(flat)] = np.linspace(0, 1, flat.size)
    colour = ramp[np.clip((ranks * (len(ramp) - 1)).astype(int), 0, len(ramp) - 1)].reshape(size, size, 3)
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * 18.0
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * 18.0
    normal = np.stack([-dx, -dy, np.ones_like(height)], -1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    rough = np.clip(0.8 + 0.08 * fibre - 0.1 * (crown - 0.5), 0.6, 0.98)
    mr = np.stack([np.ones_like(rough), rough, np.zeros_like(rough)], -1)
    save('bag_a_rope_basecolor.png', colour)
    save('bag_a_rope_normal.png', normal * 0.5 + 0.5)
    save('bag_a_rope_mr.png', mr)


def main():
    prop = sys.argv[1]
    cfg = SETTINGS[prop]
    with open(os.path.join(BAKE, f'{prop}.json')) as stream:
        meta = json.load(stream)
    tangent = np.load(os.path.join(BAKE, f'{prop}_normal.npy')).astype(np.float64) * 2 - 1
    world = np.load(os.path.join(BAKE, f'{prop}_wnormal.npy')).astype(np.float64) * 2 - 1
    ao = ndimage.gaussian_filter(np.load(os.path.join(BAKE, f'{prop}_ao.npy'))[..., 0].astype(np.float64), 1.5)
    data = np.load(os.path.join(BAKE, f'{prop}_data.npy')).astype(np.float64)
    fold, height, radius = data[..., 0], np.clip(data[..., 1], 0, 1), data[..., 2]
    size = tangent.shape[0]
    u_repeat = max(1, round(meta['u_repeat']))
    v_repeat = meta['v_repeat']
    # texels that cover the visible body (the floor disc under the sack is excluded from the statistics)
    mask = (height > 0.004) & (radius > 0.002)

    # tiles flipped to row 0 = v 0 like the bakes (keeps the OpenGL normal map's green channel valid)
    diff = np.flipud(load_rgb(os.path.join(POLYHAVEN, f"{cfg['weave']}_diff_1k.png")))
    nrm = np.flipud(load_rgb(os.path.join(POLYHAVEN, f"{cfg['weave']}_nor_gl_1k.png")))
    rough_tile = np.flipud(np.asarray(Image.open(os.path.join(POLYHAVEN, f"{cfg['weave']}_rough_1k.png")),
                                      np.float64) / 255)
    weave = tiled(ns.srgb_luminance(diff), u_repeat, v_repeat, size)
    weave_n = tiled(nrm, u_repeat, v_repeat, size) * 2 - 1
    rough_t = tiled(rough_tile, u_repeat, v_repeat, size)

    rgb, alpha, body, rope, top, bottom = sprite_regions(cfg['sprite'])
    profile = height_profile(rgb, body, top, bottom)
    native_height = np.interp(height, (np.arange(len(profile)) + 0.5) / len(profile), profile)

    wh, wz, wf, wa, ww = cfg['weights']
    rng = np.random.default_rng(3)
    blob = 0.05 * meta['height_m']                                   # isotropic blotches on the body
    sigma = (blob * size / (v_repeat * meta['tile']), blob * size / (meta['u_repeat'] * meta['tile']))
    mottle = ndimage.gaussian_filter(rng.normal(size=(size, size)), sigma, mode='wrap')
    convex = fold - ndimage.gaussian_filter(fold, 24, mode='wrap')        # local convexity of the folds
    score = (wh * standard(native_height, mask) + wz * standard(world[..., 2], mask)
             + wf * standard(convex, mask) + wa * standard(ao, mask) + ww * standard(weave, mask)
             + cfg.get('mottle', 0.0) * standard(mottle, mask))
    rank = weighted_rank(score, np.maximum(radius, 1e-4), mask)
    ramp = colour_ramp(rgb, body)
    # saturation (linear, about each stop's luminance): offsets the grey of the engine's light and sheen
    lin = ns.srgb_to_linear(ramp)
    lum = (lin @ ns.LUMA)[:, None]
    ramp = ns.linear_to_srgb(np.clip(lum + (lin - lum) * cfg.get('saturation', 1.0), 0, 1))
    base = ramp[np.clip((rank * (len(ramp) - 1)).astype(int), 0, len(ramp) - 1)]
    base[~mask] = ramp[len(ramp) // 8]
    # gain (linear): the engine lights the model on top of the painted light, so the albedo sits a little under
    # the sprite's own colours (displayed means of the review renders then match the sprite's)
    base = ns.linear_to_srgb(ns.srgb_to_linear(base) * cfg.get('gain', 1.0))

    # normals: UDN blend of the weave into the baked folds
    k = cfg['weave_normal']
    combined = np.stack([tangent[..., 0] + k * weave_n[..., 0], tangent[..., 1] + k * weave_n[..., 1],
                         tangent[..., 2]], -1)
    combined /= np.linalg.norm(combined, axis=-1, keepdims=True)
    lo, hi = cfg['rough']
    rough_norm = (rough_t - rough_t.mean()) / (rough_t.std() + 1e-9)
    rough = np.clip((lo + hi) / 2 + rough_norm * (hi - lo) / 4 + (1 - ao) * 0.05, lo, hi)
    mr = np.stack([np.ones_like(rough), rough, np.zeros_like(rough)], -1)

    save(f'{prop}_basecolor.png', base)
    save(f'{prop}_normal.png', combined * 0.5 + 0.5)
    save(f'{prop}_mr.png', mr, 512)
    shown = base[mask]
    lum = ns.srgb_luminance(shown) * 255
    native_lum = ns.srgb_luminance(rgb[body]) * 255
    print('MEAN texture', (ns.linear_to_srgb(ns.srgb_to_linear(shown).mean(0)) * 255).round(1),
          'native', (ns.linear_to_srgb(ns.srgb_to_linear(rgb[body]).mean(0)) * 255).round(1))
    print('LUMINANCE p10/50/90 texture', np.percentile(lum, [10, 50, 90]).round(1),
          'native', np.percentile(native_lum, [10, 50, 90]).round(1), 'u_repeat', u_repeat,
          'v_repeat', round(v_repeat, 2))
    if prop == 'bag_a':
        rope_textures(rgb, rope)


if __name__ == '__main__':
    main()
