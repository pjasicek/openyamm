#!/usr/bin/env python3
"""Crown envelope silhouette (no sprite, no Codex): source/crown_silhouette.png, a front silhouette of the crown model
from the stub's base (bottom row, z = 0) to the crown top (top row, z = height_m), drawn procedurally for a broad,
layered, slightly irregular dome on a lifted rim. prepare.py traces its half-width per height into work/<id>/profile.json
(revolved: the per-row width only, so left/right irregularity reads as tiers). Metres:
 - stub: radius `stub_r` up to the fork, the limbs flaring to `fork_r` at `fork_z`;
 - rim: the crown's lowest leaves at `rim_z`, already `rim_r` out; widest `widest_r` at `widest_z`;
 - dome: from the widest point to the top, a superellipse (exponent `shoulder` < 1 keeps broad shoulders);
 - tiers: the half-width modulated by two sine terms (`tiers` [[amplitude, wavelength m, phase], ...]): layered
   foliage shelves; plus a little per-row noise.
Usage: make_envelope.py <id>"""
import math, os
import numpy as np
from PIL import Image
import common

spec = common.load()
E = spec['envelope']
H = spec['height_m']
PX = 1000                                 # silhouette height in pixels
rng = np.random.default_rng(E.get('seed', 4242))


def half_width(z):
    if z < E['rim_z']:
        t = min(max((z - E['stub_top']) / (E['fork_z'] - E['stub_top']), 0.0), 1.0)
        return E['stub_r'] + (E['fork_r'] - E['stub_r']) * t * t
    if z < E['widest_z']:
        t = (E['widest_z'] - z) / (E['widest_z'] - E['rim_z'])
        w = E['rim_r'] + (E['widest_r'] - E['rim_r']) * math.sqrt(max(1 - t * t, 0.0))
    else:
        t = (z - E['widest_z']) / (H - E['widest_z'])
        w = E['widest_r'] * max(1 - t ** 2, 0.0) ** (0.5 * E['shoulder'])
    for amp, wave, phase in E.get('tiers', []):
        w *= 1 + amp * math.sin(2 * math.pi * z / wave + phase)
    return max(w, 0.6)              # a small flat top row, so the traced height is the full height


width_m = 2 * max(half_width(z) for z in np.linspace(0, H, 500)) * 1.04
W = int(PX * width_m / H) + 8
img = np.zeros((PX, W, 4), np.uint8)
noise = rng.normal(0, 0.012, PX)
noise = np.convolve(noise, np.ones(9) / 9, mode='same') * 3
for row in range(PX):
    z = (PX - 1 - row) / (PX - 1) * H
    hw = half_width(z)
    if hw <= 0:
        continue
    lo = hw * (1 + noise[row]); hi = hw * (1 - 0.7 * noise[row])      # slightly irregular, a little lopsided
    c = W / 2
    x0 = int(round(c - lo / H * (PX - 1))); x1 = int(round(c + hi / H * (PX - 1)))
    img[row, max(x0, 0):min(x1 + 1, W)] = (40, 92, 60, 255)
path = spec['sprite_path']
Image.fromarray(img, 'RGBA').save(path)
print('SILHOUETTE', path, 'size', img.shape[1], 'x', img.shape[0], 'width m', round(width_m / 1.04, 2), 'height m', H)
