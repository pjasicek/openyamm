#!/usr/bin/env python3
"""Procedural ram-horn texture set on the horn_geom.py layout (1K): base colour, normal, ORM, material classes.

The colours come from MM9's RAMHORNBLACK.dtx (the Ram row's SkinName2): its texels sorted by luminance give a ramp,
and every horn texel picks its colour by a value built from the horn's own (arc length s, angle) coordinates:
- growth ridges across the horn, spaced by the local radius (coarse at the base, fine near the tip), with a gentle
  wave round the section and deeper yearly grooves every few ridges;
- fine keratin fibres along the horn (anisotropic noise) and a slight darkening of the inner face of the curl;
- the tip and the ridge crests lighter (the pale olive streaks of the MM9 skin), the grooves darkest.
The normal map is the gradient of the same ridge height (glTF +Y up). Usage: compose_horn.py
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / 'scripts'))
import horn_geom as H

S = 1024
T = HERE / 'textures'
T.mkdir(exist_ok=True)
SKIN = HERE / 'source' / 'ram' / 'skins' / 'ram1.png'   # RAMHORNBLACK.dtx
W = np.array([0.2126, 0.7152, 0.0722])


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def enc(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


V, Tr, UV, info = H.build(-1)
C, s_st, r_st = H.centreline()
L = info['length']
s_split = info['split_s']
# texel coverage: rasterise the horn UV triangles (to know the islands for padding)
cov = np.zeros((S, S), bool)
uvp = UV * S
for p in uvp:
    x0, x1 = int(np.floor(p[:, 0].min())), int(np.ceil(p[:, 0].max()))
    y0, y1 = int(np.floor(p[:, 1].min())), int(np.ceil(p[:, 1].max()))
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = p
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
    l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
    inside = (l1 >= -0.02) & (l2 >= -0.02) & (1 - l1 - l2 >= -0.02)
    iy, ix = np.nonzero(inside)
    rows, cols = np.clip(S - 1 - (iy + y0), 0, S - 1), np.clip(ix + x0, 0, S - 1)
    cov[rows, cols] = True

yy, xx = np.mgrid[0:S, 0:S]
u = (xx + 0.5) / S
v = 1 - (yy + 0.5) / S
s, a, strip = H.texel_to_s_theta(u, v, info, s_split)
s = np.clip(s, 0, L)
r = np.interp(s, s_st, r_st)
circ = 2 * np.pi * r * 1.0
theta = a / np.maximum(circ, 1e-4) * 2 * np.pi          # 0 = outer face (row centre), +-pi = inner face
rng = np.random.default_rng(9)


def noise(shape_scale_s, shape_scale_a, seed, octaves=3):
    """Smooth value noise in (s, a) metres via blurred random grids sampled bilinearly."""
    out = np.zeros_like(s)
    amp = 1.0
    for o in range(octaves):
        g = np.random.default_rng(seed + o).normal(size=(256, 64))
        g = ndimage.gaussian_filter(g, 1.0, mode='wrap')
        cs = shape_scale_s / 2 ** o
        ca = shape_scale_a / 2 ** o
        out += amp * ndimage.map_coordinates(g, [(s / cs) % 256, (a / ca) % 64], order=1, mode='wrap')
        amp *= 0.5
    return out / np.abs(out).max()


# ridges: spacing from the local radius (about 0.22 r, 6-16 mm), phase integrated along the length so it is smooth
ss = np.linspace(0, L, 4000)
spacing = np.clip(0.14 * np.interp(ss, s_st, r_st), 0.004, 0.0095)
phase_tab = np.concatenate([[0], np.cumsum(np.diff(ss) / spacing[1:])])
phase = np.interp(s, ss, phase_tab)
wobble = 0.35 * np.sin(theta * 1.0 + 0.7) + 0.25 * noise(0.08, 0.05, 3)
ph = phase + wobble
fr = ph - np.floor(ph)
ridge = np.clip(1 - np.abs(2 * fr - 1), 0, 1) ** 1.6                      # crest 1, groove 0
year = np.floor(ph) % 5 == 0
groove = np.exp(-((fr - 0.5) / 0.08) ** 2) * year                          # a deeper groove every fifth ridge
fibre = noise(0.04, 0.0035, 11, 3)                                          # along the horn
blot = noise(0.12, 0.06, 21, 2)
height = 0.55 * ridge - 0.5 * groove + 0.12 * fibre
# value for the colour ramp: darker at the root and on the inner face, lighter crests and tip
t = (0.27 + 0.13 * ridge - 0.14 * groove + 0.12 * fibre + 0.12 * blot + 0.17 * (s / L) ** 1.5
     - 0.10 * (np.cos(theta) < -0.3))
t = np.clip(t, 0, 1)
skin = np.asarray(Image.open(SKIN).convert('RGB'), np.float64) / 255
pal = lin(skin.reshape(-1, 3))
pal = pal[np.argsort(pal @ W)]
q = np.linspace(0.04, 0.97, 64)
ramp = pal[(q * (len(pal) - 1)).astype(int)]
ramp = ndimage.gaussian_filter1d(ramp, 2, axis=0)
idx = t * (len(ramp) - 1)
i0 = np.minimum(idx.astype(int), len(ramp) - 2)
f = (idx - i0)[..., None]
col = ramp[i0] * (1 - f) + ramp[i0 + 1] * f
col = enc(col)
col = np.clip(col, 30 / 255, 243 / 255)


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


cov_d = ndimage.binary_dilation(cov, iterations=2)
base = pad(col, cov_d)
Image.fromarray((base * 255).astype(np.uint8)).save(T / 'ramhorn_basecolor.png')
# normal: height in metres (ridge relief ~1.2 mm), gradient per texel (texel size = 1 / (D * S) m)
texel = 1.0 / (info['density_uv_per_m'] * S)
hm = ndimage.gaussian_filter(height * 0.0012, 0.7)
gy_, gx_ = np.gradient(hm, texel)
n = np.stack([-gx_, gy_, np.ones_like(hm)], -1)          # image y runs down = -v: flip for +Y up
n /= np.linalg.norm(n, axis=-1, keepdims=True)
nrm = pad(n * 0.5 + 0.5, cov_d)
Image.fromarray((nrm * 255).astype(np.uint8)).save(T / 'ramhorn_normal_1k.png')
rough = pad(np.clip(0.74 - 0.08 * ridge + 0.05 * blot, 0.55, 0.85), cov_d)
ao = pad(np.clip(1 - 0.35 * groove - 0.15 * (np.cos(theta) < -0.3), 0, 1), cov_d)
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'ramhorn_metal_rough_1k.png')
classes = np.where(cov, 4, 0).astype(np.uint8)              # 4 = claw / nail / horn
Image.fromarray(classes).save(T / 'ramhorn_material_classes.png')
rep = {'size': S, 'coverage': float(cov.mean()), 'ramp_srgb_lo_hi': [enc(ramp[0]).round(3).tolist(),
                                                                       enc(ramp[-1]).round(3).tolist()],
       'layout': info}
json.dump(rep, open(T / 'ramhorn_texture.json', 'w'), indent=1, default=float)
print('HORN_TEX', json.dumps({k: v for k, v in rep.items() if k != 'layout'}))
