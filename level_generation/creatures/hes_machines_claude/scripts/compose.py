#!/usr/bin/env python3
"""Runtime textures from a machine's Meshy retexture, and its glowing faces.

- The turret's atlas is split as prepare_uv.py packed it: top half (v 0.5..1) = the turning actor, bottom half = the
  mount decoration. An energy swatch (a blue-white radial disc and a flat strip) is painted into empty actor texels
  for the added emitter geometry (build_machine.py: the lens and muzzle discs, the coil core).
- The cell and the conduit use the whole square. Their glowing faces are found by colour: a triangle whose texels
  are mostly bright violet (B high, G well below B) is energy (the drums, the core, the crown node), written to
  work/<name>_energy.json (polygon indices of work/<name>_tex.blend) for build_machine.py; their texels are lifted
  toward violet-white so the factor-only glow (emissiveFactor) reads as light, not paint.
- Normal: Meshy's, converted to glTF (+y up) when tools/normal_map_convention.measure says it is +y down.
- Metal/roughness (glTF ORM, R = 1): metallic 0.85 where Meshy says metal and the colour is gold/bronze, else 0;
  roughness at least 0.45 (turret) / 0.4 on non-metal.
Writes textures/<name>[_actor|_mount]_{basecolor,normal,orm}.png (base 2048 wide, normal/ORM 1024 wide).
Usage: compose.py <name>"""
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
TURRET = NAME == 'starport_turret'
RES = 2048
OUT = HERE / 'textures'
OUT.mkdir(exist_ok=True)
d = np.load(HERE / 'work' / f'{NAME}_tris.npz')
SRC = HERE / 'meshy' / str(d['retexture'])


def load(kind):
    return np.array(Image.open(SRC / f'texture_urls_0_{kind}.png').convert('RGB')).astype(np.float32) / 255.0


tri, pos = rasterise(d['uv'], d['co'], d['n'], RES)
covered = tri >= 0
base, metal, rough, nrm = load('base_color'), load('metallic'), load('roughness'), load('normal')
if base.shape[0] != RES:
    sys.exit(f'expected {RES} px maps')
report = {'retexture': str(d['retexture'])}

if not TURRET:
    # violet energy: bright blue channel, green well below it, red not far below it (lavender to violet-white)
    r, g, b = base[..., 0], base[..., 1], base[..., 2]
    violet = covered & (b > 0.55) & (b - g > 0.18) & (r > 0.35)
    ntri = len(d['uv'])
    hit = np.bincount(tri[covered], weights=violet[covered].astype(float), minlength=ntri)
    total = np.bincount(tri[covered], minlength=ntri)
    frac = hit / np.maximum(total, 1)
    energy_tri = (frac > 0.5) & (total > 0)
    polys = d['poly']
    geo = HERE / 'work' / f'{NAME}_energy_geo.json'          # mark_energy.py: the conduit's core and node by geometry
    repaint = 0.45
    if geo.exists():
        energy_tri = np.isin(polys, json.load(open(geo)))
        repaint = 0.85                                        # painted copper: replace most of it
    energy_poly = sorted({int(polys[t]) for t in np.nonzero(energy_tri)[0]})
    json.dump(energy_poly, open(HERE / 'work' / f'{NAME}_energy.json', 'w'))
    m = covered & energy_tri[np.maximum(tri, 0)]
    lum = base[m].max(-1, keepdims=True)
    glow = np.array([0.80, 0.70, 1.0])
    base[m] = np.clip(base[m] * (1 - repaint) + glow * repaint * np.clip(lum + 0.35, 0, 1), 0, 1)
    metal[m] = 0.0
    rough[m] = 0.35
    report.update(energy_triangles=int(energy_tri.sum()), energy_polygons=len(energy_poly), triangles=ntri)
else:
    # Energy swatch in the actor half: two empty squares (no island within 6 texels): a radial disc, a flat strip.
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
    rr = np.hypot(xx + 0.5 - S / 2, yy + 0.5 - S / 2) / (S / 2)
    core, rim = np.array([1.0, 1.0, 1.0]), np.array([0.32, 0.62, 1.0])
    base[sy:sy + S, sx:sx + S] = core + (rim - core) * np.clip(rr, 0, 1)[..., None] ** 1.4
    base[ty:ty + S, tx:tx + S] = np.array([0.62, 0.82, 1.0])
    for x, y in ((sx, sy), (tx, ty)):
        metal[y:y + S, x:x + S] = 0.0
        rough[y:y + S, x:x + S] = 0.4
        covered[y:y + S, x:x + S] = True

    def uvrect(x, y, w, h):                                  # image rect -> actor UV (0..1 over the top half)
        return [x / RES, 1 - (y + h) / (RES / 2), (x + w) / RES, 1 - y / (RES / 2)]

    swatch = {'disc': uvrect(sx, sy, S, S), 'strip': uvrect(tx, ty, S, S)}
    json.dump(swatch, open(OUT / f'{NAME}_energy_swatch.json', 'w'), indent=1)
    report['swatch'] = swatch

base = dilate(base, covered, 8); metal = dilate(metal, covered, 8)
rough = dilate(rough, covered, 8); nrm = dilate(nrm, covered, 8)
# Meshy marks most of these machines metal (79-86 %: ivory ceramic, paint and resin too), which renders them dark:
# metal only where it says so AND the colour is gold or bronze (hue 20-60 degrees, saturated, not dark)
mx, mn = base.max(-1), base.min(-1)
sat = (mx - mn) / np.maximum(mx, 1e-4)
hue = np.degrees(np.arctan2(np.sqrt(3) * (base[..., 1] - base[..., 2]),
                            2 * base[..., 0] - base[..., 1] - base[..., 2])) % 360
gold = (hue > 20) & (hue < 60) & (sat > 0.38) & (mx > 0.35)
metallic = np.where((metal[..., 0] >= 0.5) & gold, 0.85, 0.0)
report['metal_fraction'] = round(float((metallic > 0)[covered].mean()), 3)
roughness = np.where(metallic > 0, rough[..., 0], np.maximum(rough[..., 0], 0.45 if TURRET else 0.4))
orm = np.stack([np.ones_like(roughness), roughness, metallic], -1)
correlation = normal_map_convention.measure((nrm * 255).astype(np.uint8))
if correlation <= -0.15:
    nrm[..., 1] = 1.0 - nrm[..., 1]
report['normal_correlation'] = round(float(correlation), 3)
report['normal_flipped'] = bool(correlation <= -0.15)


def save(img, rows, size, stem):
    im = Image.fromarray((np.clip(img[rows], 0, 1) * 255 + 0.5).astype(np.uint8))
    im.resize(size, Image.LANCZOS).save(OUT / f'{stem}.png')


if TURRET:
    top, bottom = slice(0, RES // 2), slice(RES // 2, RES)
    for half, rows, bsize in (('actor', top, (2048, 1024)), ('mount', bottom, (1024, 512))):
        save(base, rows, bsize, f'{NAME}_{half}_basecolor')
        save(nrm, rows, (1024, 512), f'{NAME}_{half}_normal')
        save(orm, rows, (1024, 512), f'{NAME}_{half}_orm')
else:
    rows = slice(0, RES)
    save(base, rows, (2048, 2048), f'{NAME}_basecolor')
    save(nrm, rows, (1024, 1024), f'{NAME}_normal')
    save(orm, rows, (1024, 1024), f'{NAME}_orm')
json.dump(report, open(OUT / f'{NAME}_compose.json', 'w'), indent=1)
print('COMPOSED', NAME, json.dumps(report))
