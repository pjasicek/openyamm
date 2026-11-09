#!/usr/bin/env python3
"""Inputs for one dead tree (work/dead_<id>/):
 - profile.json: the sprite's left/right extent per height (fractions of the sprite height, measured from the trunk
   axis found at the base), used for branch lengths;
 - bark_basecolor.png / bark_normal.png / bark_mr.png (1024²) from the species' Poly Haven set: diffuse x AO^1.5 x a
   little height, contrast about the mean raised by bark.contrast, channels scaled to bark.target_srgb (linear mean);
 - wood_*.png: pale stripped wood (rough_wood graded orange-tan) for broken tops and peeled trunk strips; the stump
   gets an end-grain top instead (procedural rings, cracks and rot);
 - twigs_*.png (1024², 2 x 2 cells): fine twig sprays painted procedurally (dark twigs with a pale lit edge, as the
   sprites draw them), alpha-tested cards whose base is the bottom centre of each cell.
Usage: dead_prepare.py <id>"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
import dead_common as dc

spec = dc.load(); W = spec['work']
SIZE = (spec.get('texture_size', 1024),) * 2      # bark/wood maps


def profile():
    a = np.asarray(Image.open(spec['sprite_path']).convert('RGBA'))[..., 3] > 128
    rows = np.where(a.any(1))[0]; top, bottom = rows.min(), rows.max(); H = bottom - top + 1
    base_cols = np.where(a[bottom - max(2, H // 40):bottom + 1].any(0))[0]
    # trunk axis: centre of the opaque columns in the lowest 8 % above the root flare
    band = a[bottom - H // 8:bottom - H // 20]
    cols = np.where(band.any(0))[0]
    weights = band.sum(0)[cols]
    axis = float((cols * weights).sum() / weights.sum())
    out = []
    for k in range(51):
        y = int(bottom - k / 50 * (H - 1))
        c = np.where(a[y])[0]
        out.append([k / 50, float((axis - c.min()) / H) if c.size else 0.0,
                    float((c.max() - axis) / H) if c.size else 0.0])
    json.dump({'height_px': int(H), 'width_px': int(a.any(0).sum()), 'axis_px': axis - a.any(0).argmax(),
               'base_width_px': int(base_cols.size), 'left_right_by_height': out},
              open(os.path.join(W, 'profile.json'), 'w'), indent=1)
    print('PROFILE height', H, 'width', int(a.any(0).sum()), [(p[0], round(p[1], 2), round(p[2], 2)) for p in out[::5]])


def load(asset, name, channels):
    path = os.path.join(dc.SOURCE, asset, f'{asset}_{name}_2k.png')
    raw = np.asarray(Image.open(path))
    values = raw.astype(np.float32) / (65535.0 if raw.dtype == np.uint16 else 255.0)
    if values.ndim == 2:
        values = values[..., None]
    return values[..., :channels] if channels > 1 else values[..., :1].mean(2)


def graded(asset, target_srgb, contrast, stem, gain_ao=1.5, gain_height=0.3, grey=False):
    diffuse = dc.lin(load(asset, 'diff', 3))
    ao = load(asset, 'ao', 1) if os.path.exists(os.path.join(dc.SOURCE, asset, f'{asset}_ao_2k.png')) else 1.0
    height = load(asset, 'disp', 1)
    height = (height - height.min()) / max(float(height.max() - height.min()), 1e-6)
    if grey:                            # luminance detail only: the hue comes from target_srgb (and COLOR_0)
        diffuse = np.repeat((diffuse @ np.array([0.2126, 0.7152, 0.0722]))[..., None], 3, 2)
    tex = diffuse * (np.asarray(ao) ** gain_ao * (1.0 - gain_height + gain_height * height))[..., None]
    lum = tex @ np.array([0.2126, 0.7152, 0.0722])
    mean_lum = float(lum.mean())
    if contrast < 1.0:                  # a compressing grade: black texels must not divide by zero
        lum = np.maximum(lum, 1e-4)
    tex = tex * ((lum / mean_lum) ** (contrast - 1.0))[..., None]
    target = dc.lin(np.array(target_srgb) / 255.0)
    tex = tex / tex.reshape(-1, 3).mean(0) * target
    Image.fromarray((np.clip(dc.srgb(tex), 0, 1) * 255).astype(np.uint8)).resize(SIZE, Image.LANCZOS).save(
        os.path.join(W, f'{stem}_basecolor.png'))
    Image.open(os.path.join(dc.SOURCE, asset, f'{asset}_nor_gl_2k.png')).convert('RGB').resize(
        SIZE, Image.LANCZOS).save(os.path.join(W, f'{stem}_normal.png'))
    rough = (load(asset, 'rough', 1) * 255).astype(np.uint8); zero = np.zeros_like(rough)
    Image.fromarray(np.stack([zero, rough, zero], 2)).resize(SIZE, Image.LANCZOS).save(
        os.path.join(W, f'{stem}_mr.png'))
    print('TEXTURE', stem, asset, 'mean sRGB', (dc.srgb(tex.reshape(-1, 3).mean(0)) * 255).round(1))


def normal_from_height(height, strength):
    gy, gx = np.gradient(height)
    n = np.stack([-gx * strength, gy * strength, np.ones_like(height)], 2)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n


def end_grain():
    """Stump top: dark weathered end grain, growth rings, radial cracks, a rotten soft centre; lighter rim."""
    rng = np.random.default_rng(spec['seed'] + 9)
    n = 1024
    y, x = np.mgrid[0:n, 0:n] / (n - 1) * 2 - 1
    r = np.hypot(x, y); th = np.arctan2(y, x)
    noise = ndimage.gaussian_filter(rng.normal(0, 1, (n, n)), 18); noise /= noise.std()
    fine = ndimage.gaussian_filter(rng.normal(0, 1, (n, n)), 2); fine /= fine.std()
    rr = r * (1 + 0.04 * noise)
    rings = 0.5 + 0.5 * np.cos(rr * 2 * math.pi * 13)
    value = 0.42 + 0.12 * rings + 0.05 * fine
    crack = np.zeros_like(r)
    for k in range(9):
        a = rng.uniform(-math.pi, math.pi); width = rng.uniform(0.012, 0.03)
        d = np.abs(np.angle(np.exp(1j * (th - a)))) * r
        crack = np.maximum(crack, np.clip(1 - d / width, 0, 1) * (r > rng.uniform(0.05, 0.4)))
    value *= 1 - 0.65 * crack
    value *= 0.55 + 0.45 * np.clip(r / 0.35, 0, 1)            # rotten dark centre
    value *= 1 + 0.35 * np.clip((r - 0.82) / 0.18, 0, 1)      # weathered pale rim
    base = dc.lin(np.array([96, 76, 60]) / 255.0)
    tint = 1 + 0.08 * noise[..., None] * np.array([1.0, 0.6, 0.2])
    col = value[..., None] * base / 0.47 * tint
    TOP = (512, 512)                    # the cut top is small on screen
    Image.fromarray((np.clip(dc.srgb(col), 0, 1) * 255).astype(np.uint8)).resize(TOP, Image.LANCZOS).save(
        os.path.join(W, 'wood_basecolor.png'))
    nrm = normal_from_height(rings * 0.5 - crack * 2 + 0.2 * fine, 6.0)
    Image.fromarray(((nrm * 0.5 + 0.5) * 255).astype(np.uint8)).resize(TOP, Image.LANCZOS).save(
        os.path.join(W, 'wood_normal.png'))
    rough = np.full(TOP, 235, np.uint8); zero = np.zeros_like(rough)
    Image.fromarray(np.stack([zero, rough, zero], 2)).save(os.path.join(W, 'wood_mr.png'))
    print('TEXTURE wood end grain')


def twig_atlas():
    """Four cells of fine twig sprays; supersampled 2x. Each spray: a tapering main twig from the cell's bottom centre
    with forked side twigs, drawn as a dark body and a pale stroke on its upper/left edge."""
    rng = np.random.default_rng(spec['seed'] + 17)
    cell, ss = 512, 2
    kind = spec['kind']
    body = Image.new('L', (2 * cell * ss, 2 * cell * ss), 0)
    lit = Image.new('L', body.size, 0)

    def stroke(db, dl, p, q, w0, w1):
        steps = max(2, int(np.linalg.norm(q - p) / (3 * ss)))
        for i in range(steps):
            a = p + (q - p) * i / steps; b = p + (q - p) * (i + 1) / steps
            w = w0 + (w1 - w0) * (i + 0.5) / steps
            db.line([tuple(a), tuple(b)], fill=255, width=max(1, int(round(w))))
            ell = w / 2
            db.ellipse([b[0] - ell, b[1] - ell, b[0] + ell, b[1] + ell], fill=255)
            off = np.array([-0.3, -0.3]) * w
            dl.line([tuple(a + off), tuple(b + off)], fill=255, width=max(1, int(round(w * 0.35))))

    def twig(db, dl, p, angle, length, width, depth):
        """Recursive twig: a slightly crooked line, side twigs alternating, a fork at the end."""
        segs = 4
        pts = [p]
        a = angle
        for i in range(segs):
            a += rng.normal(0, 0.12)
            pts.append(pts[-1] + np.array([math.sin(a), -math.cos(a)]) * length / segs)
        for i in range(segs):
            w0 = width * (1 - 0.7 * i / segs); w1 = width * (1 - 0.7 * (i + 1) / segs)
            stroke(db, dl, pts[i], pts[i + 1], w0, w1)
        if depth <= 0:
            ends.append(pts[-1])
            return
        sides = int(rng.integers(3, 6)) if kind != 'shrub' else int(rng.integers(2, 4))
        for s in range(sides):
            t = (s + 0.7) / (sides + 0.5) * rng.uniform(0.85, 1.05)
            i = min(int(t * segs), segs - 1)
            q = pts[i] + (pts[i + 1] - pts[i]) * (t * segs - i)
            side = 1 if s % 2 == 0 else -1
            spread = rng.uniform(0.55, 1.05) if kind != 'shrub' else rng.uniform(0.25, 0.5)
            twig(db, dl, q, a + side * spread, length * rng.uniform(0.42, 0.62) * (1.1 - 0.45 * t), width * 0.55,
                 depth - 1)
        for side in (-1, 1):
            twig(db, dl, pts[-1], a + side * rng.uniform(0.25, 0.55), length * rng.uniform(0.18, 0.3), width * 0.5,
                 depth - 2)

    ends = []
    buds = []                                           # (x, y, colour) in atlas pixels (1x)
    for k in range(4):
        row, col = divmod(k, 2)
        ends.clear()
        cb = Image.new('L', (cell * ss, cell * ss), 0); cl = Image.new('L', cb.size, 0)
        db, dl = ImageDraw.Draw(cb), ImageDraw.Draw(cl)
        origin = np.array([0.5 * cell * ss, cell * ss - 4 * ss])
        twig(db, dl, origin, rng.normal(0, 0.06), cell * ss * rng.uniform(0.66, 0.74),
             13 * ss * (0.8 if kind == 'shrub' else 1) * spec.get('twig_width', 1.0),
             (3 if kind != 'shrub' else 2) + spec.get('twig_depth', 0))
        if spec.get('buds'):
            bd = ImageDraw.Draw(cb)
            for e in ends:
                if rng.random() < spec['buds']['fraction']:
                    rr = rng.uniform(*spec['buds']['radius']) * ss
                    bd.ellipse([e[0] - rr, e[1] - rr, e[0] + rr, e[1] + rr], fill=255)
                    colour = spec['buds']['srgb'][int(rng.integers(len(spec['buds']['srgb'])))]
                    buds.append(((e[0] + col * cell * ss) / ss, (e[1] + row * cell * ss) / ss, rr / ss, colour))
        body.paste(cb, (col * cell * ss, row * cell * ss)); lit.paste(cl, (col * cell * ss, row * cell * ss))
    alpha = np.asarray(body.resize((2 * cell, 2 * cell), Image.LANCZOS)).astype(np.float32) / 255
    hl = np.asarray(lit.filter(ImageFilter.GaussianBlur(ss)).resize((2 * cell, 2 * cell), Image.LANCZOS)) / 255.0
    dark = dc.lin(np.array(spec['twig_srgb']) / 255.0)
    light = dc.lin(np.array(spec['twig_highlight_srgb']) / 255.0)
    col = dark + (light - dark) * (0.6 * np.clip(hl, 0, 1))[..., None]
    yy, xx = np.mgrid[:2 * cell, :2 * cell]
    for bx, by, br, colour in buds:                    # small coloured buds at the twig ends
        m = (xx - bx) ** 2 + (yy - by) ** 2 <= br * br
        col[m] = dc.lin(np.array(colour) / 255.0) * rng.uniform(0.85, 1.15)
    rgba = np.zeros((2 * cell, 2 * cell, 4), np.uint8)
    inside = alpha >= 0.5
    rgb = (np.clip(dc.srgb(col), 0, 1) * 255).astype(np.uint8)
    idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
    rgba[..., :3] = rgb[idx[0], idx[1]]
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(W, 'twigs_basecolor.png'))
    # rounded cross-section normals: height = distance to the twig edge (capped), so twigs read cylindrical
    dist = ndimage.distance_transform_edt(alpha > 0.3)
    h = np.sqrt(np.minimum(dist, 6.0) / 6.0)
    nrm = normal_from_height(ndimage.gaussian_filter(h, 1.0), 3.0)
    Image.fromarray(((nrm * 0.5 + 0.5) * 255).astype(np.uint8)).save(os.path.join(W, 'twigs_normal.png'))
    print('TEXTURE twigs coverage', round(float(inside.mean()), 3))


def native_ramp(ns):
    """Native shading transfer (level_generation/creatures/NATIVE_SHADING_TRANSFER.md) for tiled bark, where the
    texture cannot carry it: the sprite's opaque core pixels (rim eroded) sorted by luminance give a colour ramp
    (linear RGB per luminance quantile) and a luminance profile by height (0 = lowest opaque row). dead_build.py maps
    each vertex's shading value onto this ramp by rank, so the model's light and dark take the sprite's own colours."""
    a = np.asarray(Image.open(spec['sprite_path']).convert('RGBA')).astype(np.float64) / 255
    opaque = a[..., 3] > 0.9
    core = ndimage.binary_erosion(opaque, iterations=ns.get('erode', 2))
    rgb = dc.lin(a[core][:, :3]); lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    order = np.argsort(lum, kind='stable')
    stops = ns.get('stops', 32)
    ramp = []
    for k in range(stops):
        lo, hi = int(k / stops * len(order)), int((k + 1) / stops * len(order))
        ramp.append(rgb[order[lo:max(hi, lo + 1)]].mean(0).tolist())
    rows = np.where(opaque.any(1))[0]; top, bottom = rows.min(), rows.max()
    h = (bottom - np.nonzero(core)[0]) / max(bottom - top, 1)
    bins = []
    for k in range(10):
        sel = (h >= k / 10) & (h < (k + 1) / 10 + (k == 9))
        bins.append(float(np.median(lum[sel])) if sel.any() else float(np.median(lum)))
    json.dump({'ramp_linear': ramp, 'height_luminance': bins, 'median_luminance': float(np.median(lum))},
              open(os.path.join(W, 'native_ramp.json'), 'w'), indent=1)
    print('NATIVE ramp', len(ramp), 'stops, dark', (dc.srgb(np.array(ramp[0])) * 255).round(0),
          'light', (dc.srgb(np.array(ramp[-1])) * 255).round(0), 'height profile', np.round(bins, 3).tolist())


profile()
b = spec['bark']
graded(b['source'], b['target_srgb'], b['contrast'], 'bark', b.get('ao_gain', 1.5), b.get('height_gain', 0.3),
       b.get('grey', False))
if spec.get('native_shading'):
    native_ramp(spec['native_shading'])
if spec['kind'] == 'stump':
    end_grain()
else:
    if spec['kind'] == 'snag':
        graded('rough_wood', [214, 182, 140] if spec['id'] == '6tree28' else [170, 160, 140], 1.2, 'wood')
    twig_atlas()
