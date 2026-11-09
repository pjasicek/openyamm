#!/usr/bin/env python3
"""Shared textures for every MM8 broadleaf tree (shared/), embedded byte-identical in each GLB so the cooker stores
them once (tools/cook_models.py keys textures by content):

 - bark_basecolor.png / bark_normal.png / bark_mr.png (1024): Poly Haven bark_brown_01 (CC0) as in the MM6 trees
   (diffuse x AO^1.5 x a little height), graded to a light neutral brown BARK_SRGB; species colour comes from COLOR_0.
 - leaves_basecolor.png (2048 RGBA) / leaves_normal.png (2048): GRID x GRID cells of 512 px, each a maple spray for a
   ~1.1 m card: 6-8 twigs radiating from the hub with alternate leaves and a tip leaf, filler leaves and a few leaves
   across the hub (no dark star seen from below). Each leaf keeps its own tangent normal, rotated with it, plus a fold
   across its midrib. Cell groups (CELLS):
     0-7   green maple (ambientCG LeafSet010, CC0), recoloured per leaf from GREEN, a few yellow-green highlights;
     8-11  yellow maple (LeafSet027, CC0), recoloured from YELLOW keeping part of each leaf's own blotches;
     12-15 autumn mix (LeafSet010 + LeafSet027): green, olive, yellow, orange and red leaves.
   Leaves are recoloured as target x (luminance ratio x (1 - keep) + per-channel ratio x keep) against the leaf's
   own mean, so veins and blotches survive. RGB/normals are dilated into transparent texels.
 - atlas.json: per cell the alpha-weighted mean linear colour and coverage, and the bark's mean linear colour, from
   which common.tints() derives each species' COLOR_0 tint.
Usage: make_shared.py"""
import json, math, os
import numpy as np
from PIL import Image
from scipy import ndimage
import common

OUT = common.SHARED
os.makedirs(OUT, exist_ok=True)
lin, srgb = common.lin, common.srgb
CELL = 512
GRID = common.GRID

# ---------------------------------------------------------------- bark
BARK_SRGB = [176, 156, 138]
S = os.path.join(common.SOURCE, 'bark_brown_01')


def load(name, channels):
    raw = np.asarray(Image.open(os.path.join(S, f'bark_brown_01_{name}_2k.png')))
    values = raw.astype(np.float32) / (65535.0 if raw.dtype == np.uint16 else 255.0)
    return values[..., :channels] if values.ndim == 3 else values


diffuse = lin(load('diff', 3))
ao = load('ao', 1)
height = load('disp', 3).mean(2)
height = (height - height.min()) / max(float(height.max() - height.min()), 1e-6)
bark = diffuse * (ao ** 1.5 * (0.7 + 0.3 * height))[..., None]
# the scan is lit brighter on its left half: divide out the low-frequency luminance (sigma 100 px of 2k), so a trunk
# wrapped with it shows no light/dark split, and add a little contrast (the sprites' bark is strongly flecked)
luma = bark.dot([0.2126, 0.7152, 0.0722])
low = ndimage.gaussian_filter(luma, 400, mode='wrap')   # 2026-10-16: 100 -> 400, keep the mid-scale mottling
bark = bark / (low / low.mean())[..., None]
# contrast (2026-10-16: 0.25 -> 0.4; the sprites' bark is dark with bright flecks, the first grade read flat)
bark = bark * ((bark.dot([0.2126, 0.7152, 0.0722]) / luma.mean()) ** 0.4)[..., None]
bark = bark / bark.reshape(-1, 3).mean(0) * lin(np.array(BARK_SRGB) / 255.0)
SIZE = (1024, 1024)
bark_img = Image.fromarray((np.clip(srgb(bark), 0, 1) * 255).astype(np.uint8)).resize(SIZE, Image.LANCZOS)
bark_img.save(os.path.join(OUT, 'bark_basecolor.png'))
bark_mean = lin(np.asarray(bark_img, np.float32) / 255.0).reshape(-1, 3).mean(0)
Image.open(os.path.join(S, 'bark_brown_01_nor_gl_2k.png')).convert('RGB').resize(SIZE, Image.LANCZOS).save(
    os.path.join(OUT, 'bark_normal.png'))
rough = (load('rough', 1) * 255).astype(np.uint8); zero = np.zeros_like(rough)
Image.fromarray(np.stack([zero, rough, zero], 2)).resize(SIZE, Image.LANCZOS).save(os.path.join(OUT, 'bark_mr.png'))
print('BARK mean sRGB', (srgb(bark_mean) * 255).round(1))

# ---------------------------------------------------------------- leaves


def leaf_set(name):
    src = os.path.join(common.SOURCE, name)
    color = np.asarray(Image.open(os.path.join(src, f'{name}_1K-PNG_Color.png')).convert('RGB'), np.float32) / 255
    alpha = np.asarray(Image.open(os.path.join(src, f'{name}_1K-PNG_Opacity.png')).convert('L'), np.float32) / 255
    normal = np.asarray(Image.open(os.path.join(src, f'{name}_1K-PNG_NormalGL.png')).convert('RGB'), np.float32) / 255
    if color.shape[:2] != alpha.shape:
        alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).resize(color.shape[1::-1]), np.float32) / 255
    lab, _ = ndimage.label(alpha > 0.5)
    out = []
    for sl in ndimage.find_objects(lab):
        if sl[0].stop - sl[0].start < 100:
            continue
        pad = 6
        ys = slice(max(sl[0].start - pad, 0), sl[0].stop + pad); xs = slice(max(sl[1].start - pad, 0), sl[1].stop + pad)
        c, a, n = color[ys, xs], alpha[ys, xs], normal[ys, xs]
        m = a > 0.5
        mean = lin(c)[m].mean(0)
        out.append({'c': c, 'a': a, 'n': n, 'mean': mean, 'set': name})
    return out


MAPLE_GREEN = leaf_set('LeafSet010')
MAPLE_AUTUMN = leaf_set('LeafSet027')
print('LEAF SETS', len(MAPLE_GREEN), len(MAPLE_AUTUMN))

GREEN = [([176, 214, 64], 0.45), ([194, 222, 72], 0.2), ([150, 200, 60], 0.15), ([222, 220, 68], 0.2)]
YELLOW = [([238, 206, 46], 0.5), ([226, 214, 70], 0.2), ([240, 176, 44], 0.18), ([196, 200, 72], 0.12)]
AUTUMN = [([118, 176, 56], 0.34), ([150, 160, 60], 0.16), ([230, 196, 52], 0.18), ([226, 132, 44], 0.16),
          ([182, 58, 40], 0.16)]
CELLS = ([{'group': 'green', 'sets': [MAPLE_GREEN], 'palette': GREEN, 'keep': 0.7, 'seed': 1001 + k} for k in range(8)]
         + [{'group': 'yellow', 'sets': [MAPLE_AUTUMN, MAPLE_GREEN], 'palette': YELLOW, 'keep': 0.45,
             'seed': 2001 + k} for k in range(4)]
         + [{'group': 'autumn', 'sets': [MAPLE_GREEN, MAPLE_AUTUMN], 'palette': AUTUMN, 'keep': 0.5,
             'seed': 3001 + k} for k in range(4)])
LENGTH = (128, 162)         # leaf image length incl. petiole, px of a 512 cell (~1.2 m card: blades ~25-32 cm,
                            # the sprites' oversized maple leaves)
VALUE = (0.78, 1.22)


def resize(img, w, h):
    return np.asarray(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS),
                      np.float32) / 255


def pick(r, palette):
    weights = np.array([w for _, w in palette]); weights /= weights.sum()
    return lin(np.array(palette[int(r.choice(len(palette), p=weights))][0]) / 255.0)


def paste_leaf(acc, r, cfg, bx, by, angle_deg, length_px, value):
    """One leaf with its stem end at (bx, by), tip pointing at screen angle angle_deg (0 = up, clockwise)."""
    pool = cfg['sets'][int(r.integers(len(cfg['sets'])))]
    leaf = pool[int(r.integers(len(pool)))]
    c, a, nm = leaf['c'], leaf['a'], leaf['n']
    s = length_px / c.shape[0]
    hgt, wid = max(int(c.shape[0] * s), 4), max(int(c.shape[1] * s), 3)
    c, a, nm = resize(c, wid, hgt), resize(a, wid, hgt), resize(nm, wid, hgt)
    x = (np.arange(wid) - (wid - 1) / 2) / max(wid / 2, 1)
    fold = np.clip(x, -1, 1)[None, :] * math.sin(math.radians(22)) * r.choice([-1.0, 1.0])
    n = nm * 2 - 1
    n[..., 0] = n[..., 0] + fold
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    pad = lambda img: np.concatenate([img, np.zeros(img.shape, img.dtype)], 0)
    cR = ndimage.rotate(pad(c), -angle_deg, reshape=True, order=1)
    aR = ndimage.rotate(pad(a), -angle_deg, reshape=True, order=1)
    nR = ndimage.rotate(pad(n), -angle_deg, reshape=True, order=1)
    th = math.radians(-angle_deg)
    nx, ny = nR[..., 0], -nR[..., 1]
    rx = nx * math.cos(th) - ny * math.sin(th); ry = nx * math.sin(th) + ny * math.cos(th)
    nR = np.stack([rx, -ry, nR[..., 2]], -1) * 0.5 + 0.5
    ratio = lin(np.clip(cR, 0, 1)) / leaf['mean']
    lum = (ratio * leaf['mean']).dot([0.2126, 0.7152, 0.0722]) / float(leaf['mean'].dot([0.2126, 0.7152, 0.0722]))
    keep = cfg['keep']
    cl = pick(r, cfg['palette']) * value * (lum[..., None] * (1 - keep) + ratio * keep)
    cl *= np.array([r.uniform(0.92, 1.08), 1.0, r.uniform(0.9, 1.1)])
    hh, ww = aR.shape
    ox, oy = int(round(bx - ww / 2)), int(round(by - hh / 2))
    ys_, xs_ = np.nonzero(aR > 0.05)
    if ys_.size == 0 or oy + ys_.min() < 8 or ox + xs_.min() < 8 or oy + ys_.max() >= CELL - 8 \
            or ox + xs_.max() >= CELL - 8:
        return False
    acc_c, acc_a, acc_n = acc
    x0, y0 = max(ox, 0), max(oy, 0); x1, y1 = min(ox + ww, CELL), min(oy + hh, CELL)
    sub = (slice(y0 - oy, y1 - oy), slice(x0 - ox, x1 - ox))
    av = np.clip(aR[sub], 0, 1)[..., None]
    region = (slice(y0, y1), slice(x0, x1))
    acc_c[region] = acc_c[region] * (1 - av) + srgb(np.clip(cl[sub], 0, 1)) * av
    acc_n[region] = acc_n[region] * (1 - av) + nR[sub] * av
    acc_a[region] = np.maximum(acc_a[region], av[..., 0])
    return True


def spray(cfg):
    r = np.random.default_rng(cfg['seed'])
    acc_c = np.zeros((CELL, CELL, 3), np.float32); acc_a = np.zeros((CELL, CELL), np.float32)
    acc_n = np.zeros((CELL, CELL, 3), np.float32); acc_n[...] = (0.5, 0.5, 1.0)
    acc = (acc_c, acc_a, acc_n)
    yy, xx = np.mgrid[:CELL, :CELL]
    origin = np.array([CELL * 0.5, CELL * 0.5]) + r.uniform(-10, 10, 2)
    twigs = int(r.integers(5, 8))
    headings = np.linspace(0, 360, twigs, endpoint=False) + r.uniform(0, 360) + r.uniform(-14, 14, twigs)
    placed = 0
    for heading in headings:
        steps = int(r.uniform(58, 78)); ang = math.radians(heading); p = origin.copy(); path = []
        for i in range(steps):
            path.append(p.copy()); p += 2.0 * np.array([math.sin(ang), -math.cos(ang)]); ang += r.uniform(-0.025, 0.025)
        for i, (tx, ty) in enumerate(path):
            if i < 0.3 * steps:
                continue
            w = 1.8 * (1 - i / steps) + 0.8
            m = (xx - tx) ** 2 + (yy - ty) ** 2 < w * w
            acc_c[m] = (0.24, 0.19, 0.11); acc_a[m] = 1
        count = int(r.integers(2, 4))
        for k in range(count):
            f = 0.3 + 0.62 * (k + r.uniform(-0.2, 0.2)) / count
            i = min(int(f * steps), steps - 1); tx, ty = path[i]
            side = 1 if k % 2 == 0 else -1
            value = r.uniform(*VALUE) * (0.78 + 0.22 * f)
            placed += paste_leaf(acc, r, cfg, tx, ty, heading + side * r.uniform(35, 60), r.uniform(*LENGTH), value)
        tx, ty = path[-1]
        placed += paste_leaf(acc, r, cfg, tx, ty, heading + r.uniform(-12, 12), r.uniform(*LENGTH),
                             r.uniform(0.95, 1.2))
    for _ in range(int(r.integers(4, 7))):
        heading = r.uniform(0, 360); d = r.uniform(10, 110)
        tx, ty = origin + d * np.array([math.sin(math.radians(heading)), -math.cos(math.radians(heading))])
        placed += paste_leaf(acc, r, cfg, tx, ty, heading, r.uniform(*LENGTH), r.uniform(0.85, 1.12))
    hub = np.random.default_rng(cfg['seed'] + 1000)
    for _ in range(3):                                   # leaves lying across the hub
        heading = hub.uniform(0, 360); d = -hub.uniform(25, 50)
        tx, ty = origin + d * np.array([math.sin(math.radians(heading)), -math.cos(math.radians(heading))])
        placed += paste_leaf(acc, hub, cfg, tx, ty, heading, hub.uniform(*LENGTH), hub.uniform(0.9, 1.1))
    border = np.zeros_like(acc_a); border[6:-6, 6:-6] = 1
    acc_a *= border
    return acc_c, acc_a, acc_n, placed


N = GRID * CELL
base = np.zeros((N, N, 4), np.float32); nrm = np.zeros((N, N, 3), np.float32); nrm[...] = (0.5, 0.5, 1.0)
meta = {'grid': GRID, 'cells': []}
for cell, cfg in enumerate(CELLS):
    c, a, nm, placed = spray(cfg)
    row, col = divmod(cell, GRID)
    sl = (slice(row * CELL, (row + 1) * CELL), slice(col * CELL, (col + 1) * CELL))
    base[sl[0], sl[1], :3] = c; base[sl[0], sl[1], 3] = a; nrm[sl] = nm
    inside = a > 0.5
    meta['cells'].append({'group': cfg['group'], 'leaves': int(placed), 'coverage': round(float(inside.mean()), 4),
                          'mean_linear': lin(c[inside]).mean(0).round(5).tolist()})
    print('CELL', cell, cfg['group'], 'leaves', placed, 'coverage', meta['cells'][-1]['coverage'],
          'mean sRGB', (srgb(lin(c[inside]).mean(0)) * 255).round().tolist())
inside = base[..., 3] > 0.5
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
base[..., :3] = base[..., :3][idx[0], idx[1]]
nrm = np.where(inside[..., None], nrm, nrm[idx[0], idx[1]])
Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'leaves_basecolor.png'))
Image.fromarray((np.clip(nrm, 0, 1) * 255).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'leaves_normal.png'))
preview = Image.new('RGBA', (N, N), (150, 160, 175, 255))
preview.alpha_composite(Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8) * inside[..., None], 'RGBA'))
preview.convert('RGB').resize((1024, 1024), Image.LANCZOS).save(os.path.join(OUT, 'atlas_preview.png'))
meta['bark_mean_linear'] = bark_mean.round(5).tolist()
json.dump(meta, open(os.path.join(OUT, 'atlas.json'), 'w'), indent=1)
