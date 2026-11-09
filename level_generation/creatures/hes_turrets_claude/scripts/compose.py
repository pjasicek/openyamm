#!/usr/bin/env python3
"""v2 step 4: the turret's runtime textures from its Meshy retexture (meshy/<name>_retexture_v1/).

The atlas is split as prepare_uv.py packed it: top half (v 0.5..1) = the turning actor, bottom half = the mount.
- Base colour: Meshy's, with fixes: the Ward's hazard-striped access hatch painted on its pedestal front (the
  retexture left a plain plate there); an energy swatch painted into empty actor texels (ENERGY_SWATCH: a blue-white
  radial disc and a flat strip) for the added emitter geometry (build_actor_v2.py); every island dilated 8 texels
  into its gutter.
- Normal: Meshy's, measured with tools/normal_map_convention.measure and converted to glTF (+y up) when needed.
- Metal/roughness (glTF ORM, R = 1): metallic binarised (Meshy >= 0.5 -> 0.85, the builder's gold; else 0),
  roughness Meshy's, at least 0.45 on non-metal (Meshy's glazed ceramic read like plastic).
Writes textures/<name>_{actor,mount}_{basecolor,normal,orm}.png (actor base 2048x1024, normal/ORM 1024x512; mount
1024x512 each) and textures/<name>_energy_swatch.json (the swatch UV rectangles in actor UV space).
Usage: compose.py <ward_turret|gate_bastion>"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE / 'scripts'))
sys.path.insert(0, str(REPO / 'tools'))
from raster import dilate, rasterise  # noqa: E402
import normal_map_convention  # noqa: E402

NAME = sys.argv[1]
RES = 2048
SRC = HERE / 'meshy' / f'{NAME}_retexture_v1'
OUT = HERE / 'textures'
OUT.mkdir(exist_ok=True)
# Ward: the hatch on the pedestal front (metres, after parts.py turned the mount): x, z box on faces facing -y.
HATCH = {'ward_turret': (0.135, 0.285, 0.15, 0.335)}


def load(kind):
    return np.array(Image.open(SRC / f'texture_urls_0_{kind}.png').convert('RGB')).astype(np.float32) / 255.0


d = np.load(HERE / 'work' / f'{NAME}_tris.npz')
tri, pos = rasterise(d['uv'], d['co'], d['n'], RES)
covered = tri >= 0
part = np.where(covered, d['part'][np.maximum(tri, 0)], -1)
normal_face = np.where(covered[..., None], d['n'][np.maximum(tri, 0)], 0)
base, metal, rough, nrm = load('base_color'), load('metallic'), load('roughness'), load('normal')

if NAME in HATCH:                                     # yellow / black stripes at 45 degrees, a dark frame
    x0, x1, z0, z1 = HATCH[NAME]
    m = covered & (part == 0) & (normal_face[..., 1] < -0.5)
    m &= (pos[..., 0] > x0) & (pos[..., 0] < x1) & (pos[..., 2] > z0) & (pos[..., 2] < z1)
    u = (pos[..., 0] - x0) / (x1 - x0); w = (pos[..., 2] - z0) / (z1 - z0)
    frame = (u < 0.08) | (u > 0.92) | (w < 0.06) | (w > 0.94)
    stripe = (np.floor(((pos[..., 0] + pos[..., 2]) / 0.045)) % 2) == 0
    shade = base.mean(-1, keepdims=True) / max(float(base[m].mean()), 1e-3)
    col = np.where(stripe[..., None], np.array([0.86, 0.66, 0.12]), np.array([0.07, 0.07, 0.07]))
    col = np.where(frame[..., None], np.array([0.30, 0.32, 0.30]), col) * np.clip(shade, 0.75, 1.15)
    base[m] = col[m]
    metal[m] = 0.0
    print('hatch texels', int(m.sum()))

# Bastion: the barrels' cooling-fin band glows between its fins (concept: blue-white tubes behind dark fins). Its
# faces go to the energy material (build_actor_v2.py FIN_BAND); the grooves (darker half) are painted blue-white,
# the fins dark gunmetal, so the emissive texture lights only the grooves.
FIN_BAND = {'gate_bastion': (-1.635, -1.415)}
if NAME in FIN_BAND:
    y0, y1 = FIN_BAND[NAME]
    centre_y = np.where(covered, d['co'][np.maximum(tri, 0)][..., 1].mean(-1), 0)
    m = covered & (part == 3) & (centre_y > y0) & (centre_y < y1)
    lum = base @ np.array([0.2126, 0.7152, 0.0722])
    groove = m & (lum < np.median(lum[m]))
    base[groove] = np.array([0.30, 0.55, 1.0])
    base[m & ~groove] = base[m & ~groove] * 0.2 + 0.03
    metal[m] = 0.0
    print('fin band texels', int(m.sum()), 'grooves', int(groove.sum()))

# Energy swatch in the actor half: an empty square (no island within 6 texels), a radial disc and a flat strip.
occ = covered.copy()
for _ in range(4):
    occ = occ | np.roll(occ, 1, 0) | np.roll(occ, -1, 0) | np.roll(occ, 1, 1) | np.roll(occ, -1, 1)
S = 48


def free_square():
    for y in range(8, RES // 2 - S - 8, 4):            # image rows 0..1023 = the actor half (v 0.5..1)
        for x in range(8, RES - S - 8, 4):
            if not occ[y:y + S, x:x + S].any():
                occ[y - 4:y + S + 4, x - 4:x + S + 4] = True
                return x, y
    sys.exit('no free texels for the energy swatch')


(sx, sy), (tx, ty) = free_square(), free_square()
yy, xx = np.mgrid[0:S, 0:S]
r = np.hypot(xx + 0.5 - S / 2, yy + 0.5 - S / 2) / (S / 2)
core, rim = np.array([1.0, 1.0, 1.0]), np.array([0.32, 0.62, 1.0])
disc = core + (rim - core) * np.clip(r, 0, 1)[..., None] ** 1.4
base[sy:sy + S, sx:sx + S] = disc
base[ty:ty + S, tx:tx + S] = np.array([0.62, 0.82, 1.0])
for x, y in ((sx, sy), (tx, ty)):
    metal[y:y + S, x:x + S] = 0.0
    rough[y:y + S, x:x + S] = 0.4
    covered[y:y + S, x:x + S] = True


def uvrect(x, y, w, h):                                  # image rect -> actor UV (0..1 over the top half)
    return [x / RES, 1 - (y + h) / (RES / 2), (x + w) / RES, 1 - y / (RES / 2)]


swatch = {'disc': uvrect(sx, sy, S, S), 'strip': uvrect(tx, ty, S, S)}
json.dump(swatch, open(OUT / f'{NAME}_energy_swatch.json', 'w'), indent=1)

base = dilate(base, covered, 8); metal = dilate(metal, covered, 8)
rough = dilate(rough, covered, 8); nrm = dilate(nrm, covered, 8)
metallic = np.where(metal[..., 0] >= 0.5, 0.85, 0.0)
roughness = np.where(metallic > 0, rough[..., 0], np.maximum(rough[..., 0], 0.45))
orm = np.stack([np.ones_like(roughness), roughness, metallic], -1)
correlation = normal_map_convention.measure((nrm * 255).astype(np.uint8))
if correlation <= -0.15:
    nrm[..., 1] = 1.0 - nrm[..., 1]
print('normal correlation', round(float(correlation), 3), 'flipped' if correlation <= -0.15 else 'kept')


def save(img, half, size, kind):
    rows = slice(0, RES // 2) if half == 'actor' else slice(RES // 2, RES)
    im = Image.fromarray((np.clip(img[rows], 0, 1) * 255 + 0.5).astype(np.uint8))
    im.resize(size, Image.LANCZOS).save(OUT / f'{NAME}_{half}_{kind}.png')


save(base, 'actor', (2048, 1024), 'basecolor'); save(nrm, 'actor', (1024, 512), 'normal')
save(orm, 'actor', (1024, 512), 'orm')
save(base, 'mount', (1024, 512), 'basecolor'); save(nrm, 'mount', (1024, 512), 'normal')
save(orm, 'mount', (1024, 512), 'orm')
print('COMPOSED', NAME, 'swatch', swatch)
