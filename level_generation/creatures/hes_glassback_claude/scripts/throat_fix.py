#!/usr/bin/env python3
"""Chin, throat and chest repair (polish 2026-10-22), run after compose.py. Meshy painted the pale chest in several UV
islands with different brightness and the head set's throat darker than the body's chest, so the ramps drew pale
stair-step blocks and a hard edge at the neck seam. Under the jaw and on the chest (in front of the forelegs, y < -0.62 m
feathered from -0.40, below z 0.70-0.84, surfaces facing sideways or down) both
sets get (1) a geometric belly/hide split (underside facing: belly) instead of the per-texel pale test, and (2) one
brightness field shared across islands and both sets: the luminance averaged on a 4 cm grid in 3D, times each texel's
own fine detail (luminance over its 2D blur, to the power 0.6). Rewrites the graded base colours and region masks."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
ROOT = Path(__file__).resolve().parents[1]
T = ROOT / 'textures'
W3 = np.array([0.2126, 0.7152, 0.0722])
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
ss = lambda e0, e1, x: (lambda t: t * t * (3 - 2 * t))(np.clip((x - e0) / (e1 - e0), 0, 1))
sets = []
for base, mask, ras in (('hgb_basecolor_1k_graded.png', 'hgb_region_mask_1k.png', 'uvraster_UVMap.npz'),
                        ('hgb_head_basecolor_1k_graded.png', 'hgb_head_region_mask_1k.png', 'uvraster_HeadUV.npz')):
    r = np.load(ROOT / 'work' / ras)
    col = lin(np.asarray(Image.open(T / base).convert('RGB'), np.float64) / 255)
    m = np.asarray(Image.open(T / mask).convert('RGBA'), np.float64) / 255
    pos, nrm, valid = r['pos'], r['nrm'], r['valid'].astype(bool)
    w = ss(-0.40, -0.62, pos[..., 1]) * ss(0.84, 0.70, pos[..., 2]) * ss(0.5, 0.2, nrm[..., 2]) * valid * ((m[..., 0] + m[..., 1]) > 0.5)
    sets.append(dict(base=base, mask=mask, col=col, m=m, pos=pos, nrm=nrm, valid=valid, w=w))
# shared brightness field on a 4 cm grid
lo = np.array([-0.8, -1.6, 0.0]); cell = 0.04; shape = (41, 31, 31)
acc = np.zeros(shape); cnt = np.zeros(shape)
for s in sets:
    sel = s['w'] > 0.01
    idx = np.clip(((s['pos'][sel] - lo) / cell).astype(int), 0, np.array(shape) - 1)
    lum = s['col'][sel] @ W3
    np.add.at(acc, tuple(idx.T), lum); np.add.at(cnt, tuple(idx.T), 1)
filled = cnt > 0
avg = np.where(filled, acc / np.maximum(cnt, 1), 0)
_, near = ndimage.distance_transform_edt(~filled, return_indices=True)
avg = avg[tuple(near)]
avg = ndimage.gaussian_filter(avg, 1.0)
for s in sets:
    w = s['w']; col = s['col']
    lum = col @ W3
    coords = ((s['pos'] - lo) / cell - 0.5).transpose(2, 0, 1)
    field = ndimage.map_coordinates(avg, coords, order=1, mode='nearest')
    blur = ndimage.gaussian_filter(lum, 4)
    detail = (lum / np.maximum(blur, 1e-4)) ** 0.6
    target = field * detail
    gain = np.where(lum > 1e-4, target / np.maximum(lum, 1e-4), 1)
    col = col * (1 - w[..., None]) + np.clip(col * gain[..., None], 0, 1) * w[..., None]
    belly = ss(0.15, -0.35, s['nrm'][..., 2])
    belly = ndimage.gaussian_filter(belly, 2)
    m = s['m'].copy()
    tot = m[..., 0] + m[..., 1]
    m[..., 1] = m[..., 1] * (1 - w) + belly * tot * w
    m[..., 0] = m[..., 0] * (1 - w) + (1 - belly) * tot * w
    m[..., 3] = m[..., 3] * (1 - w)
    Image.fromarray((np.clip(srgb(col), 0, 1) * 255 + 0.5).astype(np.uint8)).save(T / s['base'], optimize=True)
    Image.fromarray((np.clip(m, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(T / s['mask'], optimize=True)
    print('THROAT', s['base'], 'texels', int((w > 0.5).sum()))
