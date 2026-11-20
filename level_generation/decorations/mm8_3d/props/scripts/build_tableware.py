"""Tableware (dungeons): `dec32` stack of five nested metal bowls, `dec36` wooden plate, `dec37` stack of five wooden
plates, `dec39` stack of six metal plates -> work/<metalbowls|woodplate|woodplates|metalplates>_export.glb.

Lathes traced from the sprites. A plate: a low foot ring, a recessed well and a wide sloped rim with a rolled edge;
stacked plates sit one plate-thickness apart and only the top plate keeps its upper surface (the lower plates show
their rim bands). A bowl: a hemispherical shell with a rolled lip; nested bowls rise by their lip spacing, only the
top bowl keeps its inner surface and each lower bowl shows the band of outer wall below the next lip. Texture
coordinates are a top-down planar projection (wood grain runs across the plate, like the sprite) for plates and the
lathe's own (u around, v along the profile) for bowls. Textures table_wood, table_pewter, table_tarnish
(make_textures.py `tableware`). Usage: blender --background --python build_tableware.py -- <name> [...]"""
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl = ml.pl
R = 0.12                       # plate / bowl radius (m); the bindings scale by the sprites' widths
# plate cross-section (radius, z) / R, from the foot's centre round the underside and rim to the well's centre
PLATE_FULL = [(0.0, 0.0), (0.5, 0.0), (0.56, 0.025), (0.94, 0.11), (1.0, 0.12), (1.0, 0.17), (0.95, 0.18),
              (0.68, 0.12), (0.62, 0.05), (0.0, 0.045)]
PLATE_LOWER = [(0.5, 0.0), (0.56, 0.025), (0.94, 0.11), (1.0, 0.12), (1.0, 0.17), (0.95, 0.18), (0.88, 0.165)]
# bowl: deep hemispherical shell (height 0.85 R) with a rolled lip
BOWL_OUT = [(0.0, 0.0), (0.4, 0.0), (0.66, 0.1), (0.85, 0.3), (0.96, 0.55), (1.0, 0.8)]
BOWL_LIP = [(1.0, 0.8), (1.035, 0.83), (1.0, 0.86), (0.96, 0.84)]
BOWL_IN = [(0.96, 0.84), (0.93, 0.6), (0.82, 0.35), (0.6, 0.16), (0.3, 0.08), (0.0, 0.075)]
SPECS = {
    'metalbowls': {'kind': 'bowl', 'count': 5, 'step': 0.11, 'texture': 'table_tarnish', 'segments': (24, 14, 8)},
    'woodplate': {'kind': 'plate', 'count': 1, 'step': 0.0, 'texture': 'table_wood', 'segments': (24, 14, 8)},
    'woodplates': {'kind': 'plate', 'count': 5, 'step': 0.07, 'texture': 'table_wood', 'segments': (22, 12, 6)},
    'metalplates': {'kind': 'plate', 'count': 6, 'step': 0.065, 'texture': 'table_pewter', 'segments': (22, 12, 6),
                    'uv': 0.2},
}


def planar_uv(obj, scale=0.5):
    """Top-down planar coordinates; steep faces (the rim edge) run round the rim instead, so they do not stretch."""
    uv = obj.data.uv_layers[0].data
    for poly in obj.data.polygons:
        steep = abs(poly.normal.z) < 0.5
        centre = poly.center
        a0 = math.atan2(centre.y, centre.x)
        for li in poly.loop_indices:
            co = obj.data.vertices[obj.data.loops[li].vertex_index].co
            if steep:
                a = math.atan2(co.y, co.x)
                a += 2 * math.pi * round((a0 - a) / (2 * math.pi))
                uv[li].uv = (a / (2 * math.pi) * 3.0, 0.3 + co.z / R * 0.5)
            else:
                uv[li].uv = (0.5 + co.x / (2 * R) * scale, 0.5 + co.y / (2 * R) * scale)


def darken_undersides(obj, value=0.35):
    """Plate undersides between stacked plates: dark grooves (COLOR_0, corner domain via the point attribute)."""
    shade = np.ones(len(obj.data.vertices))
    for poly in obj.data.polygons:
        if poly.normal.z < -0.2:
            for v in poly.vertices:
                shade[v] = value
    ml.set_colour(obj, lambda i, co, c: (c[0] * shade[i], c[1] * shade[i], c[2] * shade[i], 1.0))


def plate(name, top, segments, mat, dz, full, uv_scale=0.5):
    """One plate: the underside foot, the outer slope and rim; the well and upper rim only when `full`."""
    profile = PLATE_FULL if full else PLATE_LOWER
    obj = pl.lathe(name, [(r * R, (z + dz) * R) for r, z in profile], segments, mat)
    planar_uv(obj, uv_scale)
    return obj


def bowl(name, segments, mat, dz, top, band_from):
    """A bowl from z = band_from (the next lower bowl's lip) up: the visible outer band, the lip and, for the top
    bowl, the inner surface."""
    outer = [p for p in BOWL_OUT if p[1] >= band_from - 1e-6]
    if band_from > 0 and outer and outer[0][1] > band_from:
        r = np.interp(band_from, [p[1] for p in BOWL_OUT], [p[0] for p in BOWL_OUT])
        outer = [(r, band_from)] + outer
    profile = outer + BOWL_LIP[1:] + (BOWL_IN[1:] if top else [])
    return pl.lathe(name, [(r * R, (z + dz) * R) for r, z in profile], segments, mat, u_repeat=2.0, v_scale=8.0)


def build(name):
    spec = SPECS[name]
    mat = ml.material(spec['texture'].replace('table_', '').title(), spec['texture'],
                      extras={'openyamm_specular': 0.8})
    levels = []
    for k, segments in enumerate(spec['segments']):
        parts = []
        for i in range(spec['count']):
            top = i == spec['count'] - 1
            dz = i * spec['step']
            if spec['kind'] == 'plate':
                parts.append(plate(f'P{i}', top, segments, mat, dz, top, spec.get('uv', 0.5)))
            else:
                band = 0.0 if i == 0 else 0.8 - spec['step'] + 0.005
                parts.append(bowl(f'B{i}', segments, mat, dz, top, band))
        lod = pl.join(name.title() if k == 0 else f'{name.title()}_LOD{k}', parts)
        ml.smooth(lod, 40)
        ml.colour(lod, distance=0.04, strength=0.6)
        if spec['kind'] == 'plate' and spec['count'] > 1:
            darken_undersides(lod)
        levels.append(lod)
    print('LODS', name, [pl.triangles(o) for o in levels])
    ml.export(levels, name)


for name in sys.argv[sys.argv.index('--') + 1:]:
    pl.reset()
    pl._images.clear()
    build(name)
