#!/usr/bin/env python3
"""Shared leaf atlas of the MM8 trees_other broadleaf species (shared/leaves_basecolor.png 2048 RGBA,
leaves_normal.png, leaves.json), embedded byte-identical in every GLB so the cooker stores it once.

4 x 4 cells of 512 px, each a maple spray for a ~1.1 m card (leaves 85-115 px, about 0.2 m: the MM8 sprites draw
large leaves): 6-8 twigs radiating from the hub, alternate leaves along each and a tip leaf, filler leaves, a few
leaves across the hub (no dark star seen from below). Leaves from ambientCG LeafSet010 (green maple) and LeafSet027
(autumn maple), CC0. Each leaf keeps its own tangent normal, rotated with it, plus a fold across its midrib, and is
recoloured to one palette colour (per leaf) as target x (luminance ratio x (1 - keep) + per-channel ratio x keep)
against the leaf's own mean, so veins and blotches survive. Cell groups:
  0-3   green (tree17, tree19): mid and dark green with yellow-green highlights;
  4-7   orange autumn (tree62c): orange, amber, yellow, red;
  8-11  red autumn (tree63b): crimson and dark red with some orange;
  12-13 green with autumn sprinkles (tree14, tree15): green, a few yellow and orange leaves;
  14-15 yellow-olive (tree21).
leaves.json: per cell its uv rectangle, alpha-weighted mean linear colour and coverage (common.tints()).
Usage: make_leaf_shared.py"""
import json, math, os
import numpy as np
from PIL import Image
from scipy import ndimage
import common

OUT = common.SHARED
lin, srgb = common.lin, common.srgb
CELL, GRID = 512, 4
GAIN = 1.4          # brighter than the palettes (linear): the COLOR_0 tints stay below 1


def leaf_set(name, keep):
    S = os.path.join(common.SOURCE, name)
    color = np.asarray(Image.open(os.path.join(S, f'{name}_1K-PNG_Color.png')).convert('RGB'), np.float32) / 255
    alpha = np.asarray(Image.open(os.path.join(S, f'{name}_1K-PNG_Opacity.png')).convert('L'), np.float32) / 255
    normal = np.asarray(Image.open(os.path.join(S, f'{name}_1K-PNG_NormalGL.png')).convert('RGB'), np.float32) / 255
    lab, _ = ndimage.label(alpha > 0.5)
    out = []
    for sl in ndimage.find_objects(lab):
        if sl[0].stop - sl[0].start < 80:
            continue
        pad = 6
        ys = slice(max(sl[0].start - pad, 0), sl[0].stop + pad); xs = slice(max(sl[1].start - pad, 0), sl[1].stop + pad)
        c, a, n = color[ys, xs], alpha[ys, xs], normal[ys, xs]
        mean = lin(c)[a > 0.5].mean(0)
        out.append((c, a, n, mean, keep))
    return out


GREEN_LEAVES = leaf_set('LeafSet010', 0.25)
AUTUMN_LEAVES = leaf_set('LeafSet027', 0.45)
print('LEAVES green', len(GREEN_LEAVES), 'autumn', len(AUTUMN_LEAVES))

GROUPS = [
    # (name, leaf sources, palette [(srgb, weight)], value range, extra linear gain). MM8 greens are olive (red / green
    # about 0.6-0.8 in linear); the green groups are brighter than the autumn ones so their COLOR_0 tints stay below 1.
    ('green', GREEN_LEAVES, [((96, 122, 40), 0.45), ((116, 140, 46), 0.3), ((148, 164, 60), 0.17), ((168, 178, 72), 0.08)],
     (0.82, 1.12), 1.5),
    ('orange', AUTUMN_LEAVES, [((214, 112, 30), 0.3), ((232, 160, 40), 0.22), ((240, 196, 60), 0.12),
                               ((184, 58, 26), 0.24), ((140, 40, 24), 0.12)], (0.85, 1.15), 1.0),
    ('red', AUTUMN_LEAVES, [((150, 32, 22), 0.42), ((178, 48, 26), 0.28), ((116, 26, 20), 0.12),
                            ((212, 96, 34), 0.13), ((232, 150, 44), 0.05)], (0.85, 1.12), 1.0),
    ('mixed', GREEN_LEAVES, [((98, 124, 40), 0.55), ((120, 142, 46), 0.2), ((196, 158, 44), 0.12),
                             ((204, 112, 36), 0.09), ((150, 60, 30), 0.04)], (0.82, 1.12), 1.4),
    ('olive', GREEN_LEAVES, [((150, 150, 42), 0.4), ((176, 168, 50), 0.3), ((120, 132, 40), 0.2),
                             ((204, 184, 64), 0.1)], (0.82, 1.12), 1.4),
]


def resize(img, w, h):
    return np.asarray(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS),
                      np.float32) / 255


def paste_leaf(acc_c, acc_a, acc_n, r, leaves, palette, bx, by, angle_deg, length_px, value):
    c, a, nm, mean, keep = leaves[r.integers(len(leaves))]
    s = length_px / c.shape[0]
    hgt, wid = max(int(c.shape[0] * s), 4), max(int(c.shape[1] * s), 3)
    c, a, nm = resize(c, wid, hgt), resize(a, wid, hgt), resize(nm, wid, hgt)
    x = (np.arange(wid) - (wid - 1) / 2) / max(wid / 2, 1)
    fold = np.clip(x, -1, 1)[None, :] * math.sin(math.radians(22)) * r.choice([-1.0, 1.0])
    n = nm * 2 - 1
    n[..., 0] = n[..., 0] + fold
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    pad = lambda img: np.concatenate([img, np.zeros(img.shape, img.dtype)], 0)      # stem end at the image centre
    cR = ndimage.rotate(pad(c), -angle_deg, reshape=True, order=1)
    aR = ndimage.rotate(pad(a), -angle_deg, reshape=True, order=1)
    nR = ndimage.rotate(pad(n), -angle_deg, reshape=True, order=1)
    th = math.radians(-angle_deg)
    nx, ny = nR[..., 0], -nR[..., 1]
    rx = nx * math.cos(th) - ny * math.sin(th); ry = nx * math.sin(th) + ny * math.cos(th)
    nR = np.stack([rx, -ry, nR[..., 2]], -1) * 0.5 + 0.5
    weights = np.array([w for _, w in palette]); weights /= weights.sum()
    target = lin(np.array(palette[int(r.choice(len(palette), p=weights))][0]) / 255.0)
    leaf = lin(np.clip(cR, 0, 1))
    lum = leaf @ np.array([0.2126, 0.7152, 0.0722]); mean_lum = float(mean @ np.array([0.2126, 0.7152, 0.0722]))
    cl = target * ((lum / mean_lum)[..., None] * (1 - keep) + leaf / mean * keep) * value * GAIN * CURRENT_GAIN[0]
    cl *= np.array([r.uniform(0.93, 1.07), 1.0, r.uniform(0.9, 1.08)])
    hh, ww = aR.shape
    ox, oy = int(round(bx - ww / 2)), int(round(by - hh / 2))
    ys_, xs_ = np.nonzero(aR > 0.05)
    if ys_.size == 0 or oy + ys_.min() < 8 or ox + xs_.min() < 8 or oy + ys_.max() >= CELL - 8 \
            or ox + xs_.max() >= CELL - 8:
        return False
    x0, y0 = max(ox, 0), max(oy, 0); x1, y1 = min(ox + ww, CELL), min(oy + hh, CELL)
    sub = (slice(y0 - oy, y1 - oy), slice(x0 - ox, x1 - ox))
    av = np.clip(aR[sub], 0, 1)[..., None]
    region = (slice(y0, y1), slice(x0, x1))
    acc_c[region] = acc_c[region] * (1 - av) + srgb(np.clip(cl[sub], 0, 1)) * av
    acc_n[region] = acc_n[region] * (1 - av) + nR[sub] * av
    acc_a[region] = np.maximum(acc_a[region], av[..., 0])
    return True


CURRENT_GAIN = [1.0]                # the group's extra gain while its cells are drawn


def spray(seed, leaves, palette, values, gain):
    CURRENT_GAIN[0] = gain
    r = np.random.default_rng(seed)
    acc_c = np.zeros((CELL, CELL, 3), np.float32); acc_a = np.zeros((CELL, CELL), np.float32)
    acc_n = np.zeros((CELL, CELL, 3), np.float32); acc_n[...] = (0.5, 0.5, 1.0)
    yy, xx = np.mgrid[:CELL, :CELL]
    origin = np.array([CELL * 0.5, CELL * 0.5]) + r.uniform(-12, 12, 2)
    twigs = int(r.integers(6, 9))
    spread = np.linspace(0, 360, twigs, endpoint=False) + r.uniform(0, 360) + r.uniform(-16, 16, twigs)
    placed = 0
    for heading in spread:
        steps = int(r.uniform(68, 92)); ang = math.radians(heading); p = origin.copy(); path = []
        for i in range(steps):
            path.append(p.copy()); p += 2.0 * np.array([math.sin(ang), -math.cos(ang)]); ang += r.uniform(-0.02, 0.02)
        for i, (tx, ty) in enumerate(path):
            if i < 0.3 * steps:
                continue
            w = 1.8 * (1 - i / steps) + 0.8
            m = (xx - tx) ** 2 + (yy - ty) ** 2 < w * w
            acc_c[m] = (0.24, 0.19, 0.12); acc_a[m] = 1
        count = int(r.integers(4, 6))
        for k in range(count):
            f = 0.3 + 0.65 * (k + r.uniform(-0.2, 0.2)) / count
            i = min(int(f * steps), steps - 1); tx, ty = path[i]
            side = 1 if k % 2 == 0 else -1
            value = r.uniform(*values) * (0.78 + 0.22 * f)
            placed += paste_leaf(acc_c, acc_a, acc_n, r, leaves, palette, tx, ty, heading + side * r.uniform(30, 55),
                                 r.uniform(85, 112), value)
        tx, ty = path[-1]
        placed += paste_leaf(acc_c, acc_a, acc_n, r, leaves, palette, tx, ty, heading + r.uniform(-12, 12),
                             r.uniform(92, 116), r.uniform(0.95, 1.18))
    for k in range(int(r.integers(8, 12))):
        heading = r.uniform(0, 360); d = r.uniform(20, 120)
        tx, ty = origin + d * np.array([math.sin(math.radians(heading)), -math.cos(math.radians(heading))])
        placed += paste_leaf(acc_c, acc_a, acc_n, r, leaves, palette, tx, ty, heading, r.uniform(84, 104),
                             r.uniform(0.85, 1.1))
    hub = np.random.default_rng(seed + 1000)
    for k in range(4):
        heading = hub.uniform(0, 360); d = -hub.uniform(25, 50)
        tx, ty = origin + d * np.array([math.sin(math.radians(heading)), -math.cos(math.radians(heading))])
        placed += paste_leaf(acc_c, acc_a, acc_n, hub, leaves, palette, tx, ty, heading, hub.uniform(84, 104),
                             hub.uniform(0.9, 1.1))
    border = np.zeros_like(acc_a); border[6:-6, 6:-6] = 1
    return acc_c, acc_a * border, acc_n, placed


size = CELL * GRID
base = np.zeros((size, size, 4), np.float32); nrm = np.zeros((size, size, 3), np.float32); nrm[...] = (0.5, 0.5, 1.0)
cells = []
CELLS_OF = {'green': [0, 1, 2, 3], 'orange': [4, 5, 6, 7], 'red': [8, 9, 10, 11], 'mixed': [12, 13], 'olive': [14, 15]}
for g, (name, leaves, palette, values, gain) in enumerate(GROUPS):
    for cell in CELLS_OF[name]:
        c, a, nm, placed = spray(9100 + cell * 7, leaves, palette, values, gain)
        row, col = divmod(cell, GRID)
        sl = (slice(row * CELL, (row + 1) * CELL), slice(col * CELL, (col + 1) * CELL))
        base[sl[0], sl[1], :3] = c; base[sl[0], sl[1], 3] = a; nrm[sl] = nm
        inside = a > 0.5
        mean = lin(np.clip(c, 0, 1))[inside].mean(0)
        cells.append({'group': name, 'uv': [col / GRID, 1 - (row + 1) / GRID, 1 / GRID, 1 / GRID],
                      'mean_linear': mean.round(5).tolist(), 'coverage': round(float(inside.mean()), 4),
                      'leaves': int(placed)})
        print('LEAF cell', cell, name, 'leaves', placed, 'coverage', cells[-1]['coverage'],
              'mean sRGB', (srgb(mean) * 255).round(0))
inside = base[..., 3] > 0.5
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
base[..., :3] = base[..., :3][idx[0], idx[1]]
nrm = np.where(inside[..., None], nrm, nrm[idx[0], idx[1]])
Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'leaves_basecolor.png'))
Image.fromarray((np.clip(nrm, 0, 1) * 255).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'leaves_normal.png'))
preview = Image.new('RGBA', (size, size), (150, 160, 175, 255))
preview.alpha_composite(Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8) * inside[..., None], 'RGBA'))
preview.convert('RGB').resize((1024, 1024), Image.LANCZOS).save(os.path.join(OUT, 'leaves_preview.png'))
json.dump({'size': [size, size], 'cells': cells}, open(os.path.join(OUT, 'leaves.json'), 'w'), indent=1)
