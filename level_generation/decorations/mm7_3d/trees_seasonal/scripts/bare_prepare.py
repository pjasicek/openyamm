#!/usr/bin/env python3
"""Twig atlas of a bare (winter) tree: work/<id>/twigs_basecolor.png (1024 RGBA, 2 x 2 cells) and twigs_normal.png.
Fine twig sprays painted procedurally as in the MM6 dead trees (../../mm6_new_sorpigal_3d/trees/scripts/
dead_prepare.py twig_atlas, rewritten here): a tapering main twig from the cell's bottom centre with forked side twigs,
a dark body and a pale lit stroke on its upper-left edge. Colours: bare.twig_srgb / bare.twig_highlight_srgb.
The bark maps come from prepare.py (the family's own bark). Usage: bare_prepare.py <id>"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
import common

spec = common.load(); W = spec['work']; BARE = spec['bare']
rng = np.random.default_rng(BARE.get('seed', 1717) + 17)
CELL, SS = 512, 2


def normal_from_height(height, strength):
    gy, gx = np.gradient(height)
    n = np.stack([-gx * strength, gy * strength, np.ones_like(height)], 2)
    return n / np.linalg.norm(n, axis=2, keepdims=True)


def stroke(db, dl, p, q, w0, w1):
    steps = max(2, int(np.linalg.norm(q - p) / (3 * SS)))
    for i in range(steps):
        a = p + (q - p) * i / steps; b = p + (q - p) * (i + 1) / steps
        w = w0 + (w1 - w0) * (i + 0.5) / steps
        db.line([tuple(a), tuple(b)], fill=255, width=max(1, int(round(w))))
        e = w / 2
        db.ellipse([b[0] - e, b[1] - e, b[0] + e, b[1] + e], fill=255)
        off = np.array([-0.3, -0.3]) * w
        dl.line([tuple(a + off), tuple(b + off)], fill=255, width=max(1, int(round(w * 0.35))))


def twig(db, dl, p, angle, length, width, depth):
    """A slightly crooked twig with alternating side twigs and a fork at its end."""
    segs = 4; pts = [p]; a = angle
    for i in range(segs):
        a += rng.normal(0, BARE.get('twig_kink', 0.12))
        pts.append(pts[-1] + np.array([math.sin(a), -math.cos(a)]) * length / segs)
    for i in range(segs):
        stroke(db, dl, pts[i], pts[i + 1], width * (1 - 0.7 * i / segs), width * (1 - 0.7 * (i + 1) / segs))
    if depth <= 0:
        return
    sides = int(rng.integers(*BARE.get('twig_sides', [3, 6])))
    for s in range(sides):
        t = (s + 0.7) / (sides + 0.5) * rng.uniform(0.85, 1.05)
        i = min(int(t * segs), segs - 1)
        q = pts[i] + (pts[i + 1] - pts[i]) * (t * segs - i)
        side = 1 if s % 2 == 0 else -1
        twig(db, dl, q, a + side * rng.uniform(0.45, 0.9), length * rng.uniform(0.42, 0.62) * (1.1 - 0.45 * t),
             width * 0.55, depth - 1)
    for side in (-1, 1):
        twig(db, dl, pts[-1], a + side * rng.uniform(0.25, 0.55), length * rng.uniform(0.18, 0.3), width * 0.5,
             depth - 2)


body = Image.new('L', (2 * CELL * SS, 2 * CELL * SS), 0); lit = Image.new('L', body.size, 0)
for k in range(4):
    row, col = divmod(k, 2)
    cb = Image.new('L', (CELL * SS, CELL * SS), 0); cl = Image.new('L', cb.size, 0)
    db, dl = ImageDraw.Draw(cb), ImageDraw.Draw(cl)
    twig(db, dl, np.array([0.5 * CELL * SS, CELL * SS - 4 * SS]), rng.normal(0, 0.06),
         CELL * SS * rng.uniform(0.66, 0.74), BARE.get('twig_width', 14) * SS, BARE.get('twig_depth', 3))
    body.paste(cb, (col * CELL * SS, row * CELL * SS)); lit.paste(cl, (col * CELL * SS, row * CELL * SS))
alpha = np.asarray(body.resize((2 * CELL, 2 * CELL), Image.LANCZOS)).astype(np.float32) / 255
hl = np.asarray(lit.filter(ImageFilter.GaussianBlur(SS)).resize((2 * CELL, 2 * CELL), Image.LANCZOS)) / 255.0
dark = common.lin(np.array(BARE['twig_srgb']) / 255.0)
light = common.lin(np.array(BARE['twig_highlight_srgb']) / 255.0)
colour = dark + (light - dark) * (0.6 * np.clip(hl, 0, 1))[..., None]
inside = alpha >= 0.5
rgb = (np.clip(common.srgb(colour), 0, 1) * 255).astype(np.uint8)
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
rgba = np.zeros((2 * CELL, 2 * CELL, 4), np.uint8)
rgba[..., :3] = rgb[idx[0], idx[1]]; rgba[..., 3] = (alpha * 255).astype(np.uint8)
Image.fromarray(rgba, 'RGBA').save(os.path.join(W, 'twigs_basecolor.png'))
dist = ndimage.distance_transform_edt(alpha > 0.3)
nrm = normal_from_height(ndimage.gaussian_filter(np.sqrt(np.minimum(dist, 6.0) / 6.0), 1.0), 3.0)
Image.fromarray(((nrm * 0.5 + 0.5) * 255).astype(np.uint8)).save(os.path.join(W, 'twigs_normal.png'))
print('TWIGS coverage', round(float(inside.mean()), 3))

# The native bare sprite's silhouette for bare_build.py's crown fit (bare.gnarl.fit): half-width per height in model
# metres. The bare sprite stands at its own DSFT scale; model metres per world unit come from the family's summer
# sprite (its art height = the family's LOD0 top, work/<family>/model.json).
import json
inventory = {d['name']: d for d in json.load(open(os.path.join(common.TREES, '..', 'inventory.json')))}
summer = inventory[spec['family']]; bare = inventory[spec['id']]
top = json.load(open(os.path.join(common.load(spec['family'])['work'], 'model.json')))['bounds_max'][1]
m_per_unit = top / summer['art_height']
a = np.asarray(Image.open(spec['sprite_path']).convert('RGBA'))[..., 3] > 128
rows = np.where(a.any(1))[0]; bottom = rows.max()
cols = np.where(a[bottom - max(4, (bottom - rows.min()) // 12):bottom + 1].any(0))[0]
axis = cols.mean()
unit = bare['scale'] / 2.0                      # world units per x2 pixel
prof = []
for y in range(bottom, rows.min() - 1, -2):
    c = np.where(a[y])[0]
    if c.size:
        prof.append([(bottom - y) * unit * m_per_unit, max(axis - c.min(), c.max() - axis) * unit * m_per_unit])
json.dump({'half_width_m_by_z': prof, 'axis_px': float(axis), 'height_m': prof[-1][0]},
          open(os.path.join(W, 'bare_profile.json'), 'w'))
print('BARE profile height', round(prof[-1][0], 2), 'm, max half-width', round(max(p[1] for p in prof), 2), 'm')
