#!/usr/bin/env python3
"""Stage 4 (numpy): the bakes -> the export maps.

Every atlas texel gets its model position and normal by rasterising the LOD0 triangles (tris.npz); the SDF tells
body, nemes (head) and door frame apart there, so the stripes come from the same function as the carved relief.
Base colour: pale sandstone grain (egywalh, MM6 x4, triplanar at 256 and 960 units per tile) on a ramp around X6's
Egyptian stone, horizontal strata, broad weathering patches, AO (4 m and 0.6 m) darkening, wind-blown sand in
up-facing crevices, on top faces and in a band at the foot; the nemes and lappets in gold and dark umber stripes
(egycol64's colours), the forehead band and the uraeus gold. Roughness 0.85-0.97 (gold 0.72). Normal: the tangent
bake, misses and wild hits flat. Every map gets the nearest-texel gutter fill last (claude_shared/gutter_fill.py).
Writes map_basecolor.png (2048, sRGB), map_normal.png (2048), map_mr.png (1024) and finish.json.
Usage: finish_maps.py <id>"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'level_generation' / 'creatures' / 'claude_shared'))
sys.path.insert(0, str(HERE))
from gutter_fill import coverage, pad  # noqa: E402
import sphinx_sdf  # noqa: E402

sid = sys.argv[1]
cfg = json.loads((HERE / 'sphinx.json').read_text())[sid]
work = HERE.parent / 'work' / sid
GRAIN = REPO / 'assets_source' / 'worlds' / 'mm6' / 'textures_x4' / 'egywalh.png'
SIZE = 2048
rng = np.random.default_rng(7)


def rasterise(tri_uv, attrs, size):
    """Per texel: barycentric interpolation of per-corner attributes (dict name -> (M, 3, k)); -1 part = empty."""
    out = {k: np.zeros((size, size, v.shape[-1]), np.float32) for k, v in attrs.items()}
    hit = np.zeros((size, size), bool)
    tid = np.full((size, size), -1, np.int32)
    p = tri_uv * size - 0.5           # texel centres at integer coordinates
    for t in range(len(p)):
        a, b, c = p[t]
        x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
        x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if not m.any():
            continue
        yy, xx = ys[m], xs[m]
        for k, v in attrs.items():
            out[k][yy, xx] = w0[m, None] * v[t, 0] + w1[m, None] * v[t, 1] + w2[m, None] * v[t, 2]
        hit[yy, xx] = True
        tid[yy, xx] = t
    return out, hit, tid


def value_noise3(P, period, seed):
    """Smooth 3D value noise in [0, 1] at points P (N, 3), lattice spacing `period` units."""
    r = np.random.default_rng(seed)
    lat = r.random((64, 64, 64)).astype(np.float32)
    q = P / period
    return ndimage.map_coordinates(lat, [np.mod(q[:, 0], 64), np.mod(q[:, 1], 64), np.mod(q[:, 2], 64)],
                                   order=3, mode='grid-wrap')


def value_noise1(z, period, seed):
    r = np.random.default_rng(seed)
    lat = r.random(4096).astype(np.float32)
    return ndimage.map_coordinates(lat, [np.mod(z / period, 4096)], order=3, mode='grid-wrap')


def triplanar(img, P, N, tile):
    h, w = img.shape
    wts = np.abs(N) ** 4
    wts /= wts.sum(1, keepdims=True) + 1e-9
    acc = np.zeros(len(P), np.float32)
    # planes: x-facing samples (f, z), f-facing (x, z), z-facing (x, f)
    for axis, (u, v) in enumerate(((1, 2), (0, 2), (0, 1))):
        uu = np.mod(P[:, u] / tile, 1.0) * w
        vv = np.mod(-P[:, v] / tile, 1.0) * h
        acc += wts[:, axis] * ndimage.map_coordinates(img, [vv, uu], order=1, mode='grid-wrap')
    return acc


def srgb_to_lin(c):
    c = np.asarray(c, np.float32) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255.0


d = np.load(work / 'tris.npz')
tri_uv = d['uv'].astype(np.float64)
part = d['part'].astype(np.float32)
attrs = {'pos': d['pos'], 'nrm': d['nrm'], 'part': np.repeat(part[:, None, None], 3, 1)}
R, hit, tid = rasterise(tri_uv, attrs, SIZE)
idx = np.nonzero(hit)
P = R['pos'][idx].astype(np.float64)
N = R['nrm'][idx].astype(np.float64)
N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-9
is_face = R['part'][idx][:, 0] > 0.5
X, F, Z = P[:, 0], P[:, 1], P[:, 2]
print('texels', len(P))

# labels from the SDF
_, d_body, d_head = sphinx_sdf.full_sdf(X, F, Z, cfg)
frame, opening = sphinx_sdf.door_cut(X, F, Z, cfg['door'])
is_head = (np.abs(d_head) < np.abs(d_body)) & ~is_face
is_frame = (np.minimum(np.abs(frame), np.abs(opening)) < 14) & ~is_head & ~is_face

# stone grain
gimg = np.asarray(Image.open(GRAIN).convert('L'), np.float32) / 255.0
lo, hi = np.percentile(gimg, [3, 97])
gimg = np.clip((gimg - lo) / (hi - lo), 0, 1)
g = 0.6 * triplanar(gimg, P, N, 256.0) + 0.4 * triplanar(gimg, P, N, 960.0)
g = np.where(is_face, 0.5 + 0.6 * (g - 0.5), g)
dark, light = srgb_to_lin((150, 118, 74)), srgb_to_lin((228, 198, 146))
col = dark[None] + (light - dark)[None] * g[:, None] ** 1.1
strata = 1.0 + 0.07 * (value_noise1(Z, 46.0, 1) - 0.5) + 0.05 * (value_noise1(Z, 190.0, 2) - 0.5)
patches = value_noise3(P, 640.0, 3)
col *= (strata * (0.90 + 0.16 * patches))[:, None]
col *= np.array([1.0, 0.985, 0.95])[None] ** ((patches - 0.5) * 4)[:, None]
col = np.where(is_frame[:, None], col * 1.06, col)

# nemes stripes (head-local, the SDF's own band function)
H = sphinx_sdf.HEAD
hs = cfg['head']['scale']
zl = (Z - cfg['head']['z']) / hs
xl = np.abs(X) / hs
st = H['stripe']
top_face = (N[:, 2] > 0.7) & (zl > H['top'] - 60)
band = np.where(top_face, sphinx_sdf.bands(xl + 0.5 * st['period'] * st['gold'], st['period'], st['gold']),
                sphinx_sdf.bands(zl, st['period'], st['gold']))
plain = (zl > H['band'][0]) & (zl < H['band'][1]) & ~top_face
band = np.where(plain | (zl > H['band'][1]) & ~top_face & (np.abs(X) < 80 * hs), 1.0, band)
gold, umber = srgb_to_lin((218, 172, 86)), srgb_to_lin((104, 72, 40))
nem = umber[None] + (gold - umber)[None] * band[:, None]
nem *= (0.86 + 0.28 * g)[:, None]
wear = 0.18 + 0.22 * value_noise3(P, 220.0, 4)
nem = nem * (1 - wear[:, None]) + col * wear[:, None]
col = np.where(is_head[:, None], nem, col)

# occlusion
def bake(name):
    a = np.asarray(Image.open(work / name).convert('L'), np.float32) / 255.0
    return a[idx]


ao_big, ao_small = bake('bake_ao_big.png'), bake('bake_ao_small.png')
occl = (0.52 + 0.48 * ao_big) * (0.62 + 0.38 * ao_small)
col *= occl[:, None]

# sand: up-facing crevices, top faces, the foot
up = np.clip(N[:, 2], 0, 1)
crev = np.clip(1.0 - ao_small, 0, 1)
sand_n = value_noise3(P, 90.0, 5)
amt = np.clip(crev * 2.2 * up ** 0.7, 0, 1) * 0.85
amt += np.clip((up - 0.72) / 0.25, 0, 1) * (0.15 + 0.45 * np.clip(sand_n - 0.45, 0, 1) * 2)
amt += np.clip(1 - (Z + 10) / 70.0, 0, 1) * (0.55 + 0.3 * sand_n)
amt = np.clip(amt, 0, 0.92) * np.where(is_face, 0.5, 1.0)
sand = srgb_to_lin((206, 174, 128))[None] * (0.86 + 0.18 * sand_n[:, None]) * (0.75 + 0.25 * ao_big[:, None])
col = col * (1 - amt[:, None]) + sand * amt[:, None]

# in game the models are lit by a cool sky ambient that greys warm stone (review/ingame_v1): lift the chroma in
# linear space around each texel's luminance and darken a little, so the stone matches A5's egy textures there
CHROMA, GAIN = 1.45, 0.92
lum_lin = (col @ np.array([0.2126, 0.7152, 0.0722]))[:, None]
col = np.clip((lum_lin + (col - lum_lin) * CHROMA) * GAIN, 0, 1)
srgb = lin_to_srgb(col)
srgb = np.clip(srgb, 34, 240)
covered = coverage(tri_uv, SIZE, SIZE)
img = np.zeros((SIZE, SIZE, 3), np.uint8)
img[idx] = srgb.astype(np.uint8)
lum = srgb @ np.array([0.2126, 0.7152, 0.0722])
stats = {'texels': int(len(P)), 'atlas_covered': float(covered.mean()),
         'srgb_lum_p1_p50_p99': [float(v) for v in np.percentile(lum, [1, 50, 99])],
         'head_share': float(is_head.mean()), 'frame_share': float(is_frame.mean()), 'face_share': float(is_face.mean())}
print('COLOUR', stats)
Image.fromarray(pad(img, hit), 'RGB').save(work / 'map_basecolor.png', optimize=True)

# roughness / metallic (glTF: G roughness, B metallic)
rough = 0.86 + 0.07 * (1 - g) + 0.04 * amt
rough = np.where(is_head, 0.72 + 0.16 * (1 - band) + 0.06 * amt, rough)
mr = np.zeros((SIZE, SIZE, 3), np.uint8)
mr[..., 0] = 255
mr[idx[0], idx[1], 1] = np.clip(rough * 255, 0, 255).astype(np.uint8)
mr = pad(mr, hit)
mr_small = np.asarray(Image.fromarray(mr).resize((1024, 1024), Image.LANCZOS))
cov_small = coverage(tri_uv, 1024, 1024)
mr_small = pad(mr_small.copy(), cov_small)
mr_small[..., 0] = 255
mr_small[..., 2] = 0
Image.fromarray(mr_small, 'RGB').save(work / 'map_mr.png', optimize=True)

# normal: misses (black) and wild hits (tilted past ~55 degrees) flat
nm = np.asarray(Image.open(work / 'bake_normal.png').convert('RGB')).copy()
n = nm.astype(np.float32) / 127.5 - 1.0
bad = covered & ((nm.sum(-1) < 30) | (n[..., 2] < 0.57))
nm[bad] = (128, 128, 255)
stats['normal_flat_filled'] = float(bad.sum() / covered.sum())
print('NORMAL flat-filled %.1f %% of island texels' % (100 * stats['normal_flat_filled']))
Image.fromarray(pad(nm, covered), 'RGB').save(work / 'map_normal.png', optimize=True)
json.dump(stats, open(work / 'finish.json', 'w'), indent=1)
print('FINISH_DONE')
