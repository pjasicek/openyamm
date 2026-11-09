#!/usr/bin/env python3
"""Textures of the MM7 barrels (7dec32 netted barrel, 7dec21 cask on its side): one 1024 atlas per barrel
(textures/<name>_{basecolor,normal,mr}.png) plus the net and rope cards (textures/net_*, rope_*).

Atlas layout (glTF uv, v up; the PNG is flipped on save):
- side strip u 0..1 around the barrel (angle = 2 pi u, seam at the back), v 0..SIDE_V from the base to the chime top;
  STAVES staves, each a plank slice of Poly Haven weathered_planks, dark seams between
  them; iron hoops (Poly Haven rust_coarse_01) over the hoop heights, brass rivet heads on the riveted hoops.
- lid disc centred LID_C, radius LID_R (wood_planks across, a dark chime ring at its edge).
- an iron swatch (net weights, tap) at IRON_SWATCH.
Colours: each region's luminance is rank-matched to the native sprite's pixels of that region (a softened native
shading transfer, NATIVE_SHADING_TRANSFER.md) and coloured by the sprite's luminance-to-colour ramp, then scaled so
its mean is the sprite region's mean / EXPECTED_OCCLUSION (COLOR_0 carries the vertex occlusion).
Metallic-roughness: R = specular mask (openyamm_specular_mask), G = roughness, B = metal.
Usage: barrel_textures.py [7dec32|7dec21|net|all]"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
DECO = os.path.join(REPO, 'level_generation', 'decorations')
X2 = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
OUT = os.path.join(HERE, 'textures')
WOOD = os.path.join(DECO, 'mm7_3d', 'fire', 'source', 'polyhaven', 'wood_planks', 'wood_planks_{}_1k.png')
STAVE = os.path.join(DECO, 'mm8_3d', 'props', 'source', 'weathered_planks', 'weathered_planks_{}_2k.png')
STAVE_SEAMS = [124, 344, 573, 806, 1032, 1262, 1493, 1724, 1947]   # plank seams (columns) of weathered_planks 2k
STAVE_ROWS = (640, 1400)                                             # between its two nail rows
IRON = os.path.join(DECO, 'mm6_dungeons_3d', 'torch_textures', 'source', 'rust_coarse_01', 'rust_coarse_01_{}_1k.png')
SIZE = 1024
SIDE_V = 0.75
LID_C, LID_R = (0.125, 0.875), 0.12
IRON_SWATCH = (0.30, 0.78, 0.50, 0.98)          # u0, v0, u1, v1
DISC_C, DISC_R = (0.63, 0.875), 0.07             # painted face of the net weights (an iron washer)
ROPE_SOURCE = os.path.join(DECO, 'mm6_dungeons_3d', 'leftovers', 'textures', 'rope_{}.png')
ROPE_NATIVE = (150, 134, 108)                    # the sprite's ropes, shaded parts included (sRGB)
EXPECTED_OCCLUSION = 0.70

# Per barrel: geometry shared with build_barrel.py (barrel_spec.json), native regions of the x2 sprite (rows/cols
# in the cropped sprite: y0, y1, x0, x1) whose pixels drive each region's grade.
SPEC = json.load(open(os.path.join(HERE, 'scripts', 'barrel_spec.json')))


def load(path, mode='RGB'):
    return np.asarray(Image.open(path).convert(mode)).astype(np.float32) / 255.0


def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def sprite_pixels(name, regions, sat=None):
    """sRGB pixels (0..1) of the cropped x2 sprite inside any of regions [(y0, y1, x0, x1)], optionally only those
    whose saturation (max - min) / max lies in sat = [lo, hi]."""
    im = Image.open(os.path.join(X2, SPEC[name]['sprite'])).convert('RGBA')
    im = im.crop(im.split()[-1].getbbox())
    a = np.asarray(im).astype(np.float32) / 255.0
    mask = np.zeros(a.shape[:2], bool)
    for y0, y1, x0, x1 in regions:
        mask[y0:y1, x0:x1] = True
    mask &= a[..., 3] > 0.5
    if sat:
        rgb = a[..., :3]
        saturation = (rgb.max(-1) - rgb.min(-1)) / np.maximum(rgb.max(-1), 1e-3)
        mask &= (saturation >= sat[0]) & (saturation <= sat[1])
    return a[mask][:, :3]


def grade(texels, mask, native, strength, contrast=1.0, gain=1.0):
    """Rank-match the luminance of texels[mask] to the native pixels' (blended by strength with the texels' own
    normalised luminance), colour by the native luminance-to-colour ramp, then set the region mean to the native
    mean / EXPECTED_OCCLUSION (linear). Returns a new array."""
    out = texels.copy()
    region = texels[mask]
    lum = region @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    nlum = native @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    order = np.argsort(np.argsort(lum))
    rank = order / max(1, len(lum) - 1)
    sorted_native = np.sort(nlum)
    matched = np.interp(rank, np.linspace(0, 1, len(sorted_native)), sorted_native)
    own = (lum - lum.mean()) * (nlum.std() / max(lum.std(), 1e-4)) * contrast + nlum.mean()
    target_lum = matched * strength + own * (1 - strength)
    # luminance-to-colour ramp: mean chroma of native pixels in 24 luminance bins
    bins = np.linspace(nlum.min(), nlum.max() + 1e-4, 25)
    idx = np.clip(np.digitize(nlum, bins) - 1, 0, 23)
    ramp = np.array([native[idx == k].mean(0) / max(nlum[idx == k].mean(), 1e-3) if (idx == k).sum() > 4
                     else native.mean(0) / nlum.mean() for k in range(24)])
    centres = (bins[:-1] + bins[1:]) / 2
    chroma = np.stack([np.interp(np.clip(target_lum, centres[0], centres[-1]), centres, ramp[:, c])
                       for c in range(3)], 1)
    colour = np.clip(chroma * target_lum[:, None], 0, 1)
    lin = srgb_to_linear(colour)
    target = srgb_to_linear(native.mean(0)) / EXPECTED_OCCLUSION * gain
    lin *= (target / np.maximum(lin.mean(0), 1e-4))[None, :]
    out[mask] = linear_to_srgb(lin)
    return out


def rotate_normal(n):
    """A tangent-space normal map turned 90 degrees counter-clockwise (np.rot90): (x, y) -> (-y, x)."""
    n = np.rot90(n).copy()
    x, y = n[..., 0] * 2 - 1, n[..., 1] * 2 - 1
    n[..., 0] = (-y + 1) / 2
    n[..., 1] = (x + 1) / 2
    return n


def build_atlas(name):
    spec = SPEC[name]
    rng = np.random.default_rng(spec.get('seed', 7))
    wood = load(STAVE.format('diff')); wood_n = load(STAVE.format('nor_gl')); wood_r = load(STAVE.format('rough'), 'L')
    iron = load(IRON.format('diff')); iron_n = load(IRON.format('nor_gl')); iron_r = load(IRON.format('rough'), 'L')
    col = np.zeros((SIZE, SIZE, 3), np.float32); col[:] = wood.mean((0, 1))
    nrm = np.zeros((SIZE, SIZE, 3), np.float32); nrm[:] = (0.5, 0.5, 1.0)
    mr = np.zeros((SIZE, SIZE, 3), np.float32); mr[..., 0] = 0.35; mr[..., 1] = 0.8
    kind = np.zeros((SIZE, SIZE), np.uint8)            # 0 empty, 1 wood, 2 iron, 3 rivet, 4 lid
    # image rows: row 0 is v = 1
    side_rows = int(round(SIDE_V * SIZE))
    y0 = SIZE - side_rows
    staves = spec['staves']
    for s in range(staves):
        x0 = int(round(s * SIZE / staves)); x1 = int(round((s + 1) * SIZE / staves))
        w = x1 - x0
        # a narrow slice (about 1.5 x the stave width) of one plank's interior, rows between the nail lines
        plank = rng.integers(0, len(STAVE_SEAMS) - 1)
        left, right = STAVE_SEAMS[plank] + 12, STAVE_SEAMS[plank + 1] - 12
        span = int(w * 1.5)
        span = min(span, right - left - 1)
        sx0 = int(rng.integers(left, max(left + 1, right - span)))
        src = np.linspace(sx0, sx0 + span - 1, w).astype(int)
        r0, r1 = STAVE_ROWS
        if rng.random() < 0.5:
            r0, r1 = r1, r0                                       # some staves upside down
        rows = np.linspace(r0, r1, side_rows).astype(int)
        col[y0:, x0:x1] = wood[rows][:, src] * (0.86 + 0.28 * rng.random())
        nrm[y0:, x0:x1] = wood_n[rows][:, src]
        mr[y0:, x0:x1, 1] = wood_r[rows][:, src]
        kind[y0:, x0:x1] = 1
        # seam: dark groove with a bevel on either side
        col[y0:, x0:x0 + 2] *= 0.25
        col[y0:, x0 + 2:x0 + 4] *= 0.7
        col[y0:, x1 - 2:x1] *= 0.7
        nrm[y0:, x0:x0 + 3] = (0.2, 0.5, 0.9)
        nrm[y0:, x1 - 3:x1] = (0.8, 0.5, 0.9)
    # hoops (z in units -> v)
    height = spec['height']
    for k, hoop in enumerate(spec['hoops']):
        z0, z1 = hoop['z']
        r0 = SIZE - int(round((z1 + 0.6) / height * SIDE_V * SIZE))
        r1 = SIZE - int(round((z0 - 0.6) / height * SIDE_V * SIZE))
        r0, r1 = max(r0, y0), min(r1, SIZE)
        oy = rng.integers(0, SIZE - (r1 - r0)); ox = rng.integers(0, SIZE)
        cols = (np.arange(SIZE) + ox) % SIZE
        col[r0:r1] = iron[oy:oy + r1 - r0][:, cols]
        nrm[r0:r1] = iron_n[oy:oy + r1 - r0][:, cols]
        mr[r0:r1, :, 1] = iron_r[oy:oy + r1 - r0][:, cols] * 0.6 + 0.3
        mr[r0:r1, :, 2] = 0.45
        mr[r0:r1, :, 0] = 0.9
        kind[r0:r1] = 2
        col[r0:r0 + 2] *= 1.6; col[r0 + 2:r0 + 4] *= 1.25           # lit upper edge, dark lower edge
        col[r1 - 2:r1] *= 0.45
        nrm[r0:r0 + 2] = (0.5, 0.8, 0.85); nrm[r1 - 2:r1] = (0.5, 0.2, 0.85)
        count = hoop.get('rivets', 0)
        if count:
            rad = max(3, int((r1 - r0) * 0.15))
            cy = (r0 + r1) // 2
            for i in range(count):
                cx = int((i + 0.5) / count * SIZE)
                for dy in range(-rad, rad + 1):
                    for dx in range(-rad, rad + 1):
                        d = math.hypot(dx, dy) / rad
                        if d <= 1:
                            yy, xx = cy + dy, (cx + dx) % SIZE
                            h = math.sqrt(max(0.0, 1 - d * d))
                            col[yy, xx] = np.array(spec.get('rivet_colour', [0.62, 0.48, 0.24])) * (0.55 + 0.6 * h) + 0.15 * h ** 8
                            nx, ny = dx / rad, -dy / rad
                            nz = max(0.25, h)
                            l = math.sqrt(nx * nx + ny * ny + nz * nz)
                            nrm[yy, xx] = ((nx / l + 1) / 2, (ny / l + 1) / 2, nz / l)
                            mr[yy, xx] = (1.0, 0.4, 0.8)
                            kind[yy, xx] = 3
    # lid disc
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    u = (xx + 0.5) / SIZE; v = 1 - (yy + 0.5) / SIZE
    d = np.hypot(u - LID_C[0], v - LID_C[1]) / LID_R
    lid = d <= 1.06
    lw = load(WOOD.format('diff')); ln = load(WOOD.format('nor_gl')); lr = load(WOOD.format('rough'), 'L')
    sy = ((v - LID_C[1]) / LID_R * 0.5 + 0.5) * 380 + 300
    sx = ((u - LID_C[0]) / LID_R * 0.5 + 0.5) * 380 + 200
    sy = np.clip(sy.astype(int), 0, SIZE - 1); sx = np.clip(sx.astype(int), 0, SIZE - 1)
    col[lid] = lw[sy[lid], sx[lid]]; nrm[lid] = ln[sy[lid], sx[lid]]; mr[lid, 1] = lr[sy[lid], sx[lid]]
    kind[lid] = 4
    mr[lid, 0] = spec.get('lid_specular', 0.35)     # the open barrel's floor: no sky reflection inside
    edge = lid & (d > 0.9)
    col[edge] *= 0.55
    # iron swatch
    su0, sv0, su1, sv1 = IRON_SWATCH
    sw = (u >= su0) & (u <= su1) & (v >= sv0) & (v <= sv1)
    col[sw] = iron[yy[sw] % SIZE, xx[sw] % SIZE]; nrm[sw] = iron_n[yy[sw] % SIZE, xx[sw] % SIZE]
    mr[sw, 1] = iron_r[yy[sw] % SIZE, xx[sw] % SIZE] * 0.6 + 0.3; mr[sw, 2] = 0.45; mr[sw, 0] = 0.9
    kind[sw] = 5
    # washer face: iron disc, raised rim, a dark centre hole and four small holes
    dd = np.hypot(u - DISC_C[0], v - DISC_C[1]) / DISC_R
    disc = dd <= 1.08
    col[disc] = iron[yy[disc] % SIZE, (xx[disc] + 300) % SIZE]
    mr[disc, 1] = 0.55; mr[disc, 2] = 0.45; mr[disc, 0] = 0.9
    kind[disc] = 5
    ang = np.arctan2(v - DISC_C[1], u - DISC_C[0])
    hole = disc & ((dd < 0.22) | ((np.abs(dd - 0.55) < 0.12) & (np.abs(((ang + math.pi / 4) % (math.pi / 2)) - math.pi / 4) < 0.22)))
    rim = disc & (dd > 0.82)
    nrm[rim] = np.stack([0.5 + 0.35 * np.cos(ang[rim]), 0.5 + 0.35 * np.sin(ang[rim]), np.full(rim.sum(), 0.8)], 1)
    # grades toward the native sprite regions
    regions = spec['native']
    sats = spec.get('native_sat', {})
    col = grade(col, kind == 1, sprite_pixels(name, regions['wood'], sats.get('wood')), spec.get('wood_strength', 0.6), gain=spec.get('gain', 1.0))
    iron_mask = (kind == 2) | (kind == 5)
    col = grade(col, iron_mask, sprite_pixels(name, regions['iron'], sats.get('iron')), spec.get('iron_strength', 0.9), gain=spec.get('gain', 1.0))
    col = grade(col, kind == 4, sprite_pixels(name, regions['lid'], sats.get('lid')), 0.6, gain=spec.get('gain', 1.0))
    col[hole] *= 0.12
    col[rim] *= 1.25
    # rivets: brass, a little darker than the hand-tuned base above
    col[kind == 3] *= spec.get('rivet_gain', 0.8)
    save(name, col, nrm, mr)


def save(name, col, nrm, mr):
    os.makedirs(OUT, exist_ok=True)
    # v up in the atlas: rows were written with row 0 = v 1, which is already PNG order.
    Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, f'{name}_basecolor.png'))
    n = nrm.copy()
    Image.fromarray((np.clip(n, 0, 1) * 255).astype(np.uint8)).resize((512, 512), Image.LANCZOS).save(
        os.path.join(OUT, f'{name}_normal.png'))
    Image.fromarray((np.clip(mr, 0, 1) * 255).astype(np.uint8)).resize((256, 256), Image.LANCZOS).save(
        os.path.join(OUT, f'{name}_mr.png'))
    print('ATLAS', name, 'mean', (col.reshape(-1, 3).mean(0) * 255).round())


NET_NATIVE = (140, 126, 106)     # the sprite's net cords, shaded parts included (beige-grey)


def build_net():
    """A loose, knotted diamond net (alpha-cut card texture, 512, tiling): two families of cords along the
    diagonals, CELLS cells across, bent by a periodic domain warp so the cells are uneven, knots of uneven size where
    the cords cross, a few broken cords. Colour: the sprite's cords."""
    size, cells = 512, 8
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    rng = np.random.default_rng(3)
    w = 2 * math.pi / size

    def periodic(fx, fy, phase):
        return np.sin(fx * w * xx + fy * w * yy + phase)
    # periodic warp (whole frequencies keep the texture tiling)
    wx = 7.0 * periodic(1, 2, 0.3) + 4.0 * periodic(3, -1, 1.7) + 2.0 * periodic(-2, 5, 2.9)
    wy = 6.0 * periodic(2, 1, 0.9) + 4.0 * periodic(-1, 3, 2.2) + 2.0 * periodic(4, 3, 0.4)
    X, Y = xx + wx, yy + wy
    pitch = size / cells
    p = pitch / math.sqrt(2)
    half = 2.1
    cords, dists = [], []
    for sign in (1, -1):
        t = (X + sign * Y) / math.sqrt(2)
        along = (X - sign * Y) / math.sqrt(2)
        dist = np.abs(((t + p / 2) % p) - p / 2)
        width = half * (0.85 + 0.3 * (0.5 + 0.5 * np.sin(along * 0.05 + sign * 2.0)))
        cord = np.clip(1 - (dist / width) ** 2, 0, 1)
        twist = 0.75 + 0.25 * np.sin(along * 0.9 + t * 0.2)
        cords.append(np.sqrt(cord) * twist)
        dists.append(dist)
    # a few broken cords: short gaps in one family
    for _ in range(5):
        cx, cy, r = rng.uniform(0, size), rng.uniform(0, size), rng.uniform(10, 18)
        k = int(rng.integers(0, 2))
        dx = (xx - cx + size / 2) % size - size / 2
        dy = (yy - cy + size / 2) % size - size / 2
        cords[k][dx * dx + dy * dy < r * r] = 0
    height = np.maximum(cords[0], cords[1])
    # knots where both cords cross, of uneven size
    knot_size = 0.9 + 0.8 * (0.5 + 0.5 * periodic(3, 4, 1.1)) * (0.5 + 0.5 * periodic(-5, 2, 0.2))
    knot = np.clip(1 - (np.hypot(dists[0], dists[1]) / (4.6 * knot_size)) ** 2, 0, 1)
    knot *= (cords[0] > 0) | (cords[1] > 0) | (knot > 0.5)
    height = np.maximum(height, np.sqrt(knot) * 1.05)
    alpha = (height > 0.24).astype(np.float32)
    native = np.array(NET_NATIVE, np.float32) / 255.0
    shade = 0.6 + 0.4 * np.clip(height, 0, 1)
    noise = 0.85 + 0.3 * rng.random((size, size)).astype(np.float32)
    col = native[None, None, :] * (shade * noise)[..., None]
    gy, gx = np.gradient(height * 3.0)
    n = np.stack([-gx, gy, np.ones_like(gx)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    rgba = np.concatenate([np.clip(col, 0, 1), alpha[..., None]], -1)
    Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'net_basecolor.png'))
    Image.fromarray(((n + 1) / 2 * 255).astype(np.uint8)).save(os.path.join(OUT, 'net_normal.png'))
    mr = np.zeros((size // 4, size // 4, 3), np.uint8); mr[..., 0] = 60; mr[..., 1] = 235
    Image.fromarray(mr).save(os.path.join(OUT, 'net_mr.png'))
    print('NET', 'coverage', round(float(alpha.mean()), 3))


def build_rope():
    """The MM6 leftovers' procedural laid rope (read only), recoloured to the sprite's pale rope."""
    col = load(ROPE_SOURCE.format('basecolor'))
    lin = srgb_to_linear(col)
    target = srgb_to_linear(np.array(ROPE_NATIVE, np.float32) / 255.0) / 0.9
    lin *= (target / lin.reshape(-1, 3).mean(0))[None, None, :]
    Image.fromarray((linear_to_srgb(lin) * 255).astype(np.uint8)).save(os.path.join(OUT, 'rope_basecolor.png'))
    for kind in ('normal', 'mr'):
        Image.open(ROPE_SOURCE.format(kind)).save(os.path.join(OUT, f'rope_{kind}.png'))
    print('ROPE')


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('net', 'all'):
        build_net()
        build_rope()
    for name in SPEC:
        if which in (name, 'all'):
            build_atlas(name)
