"""`7dec11` (dungeon 7d29, 1 placement): a heap of dug earth. A steep cone of dark soil (peak 170 high, a little
right of and behind the centre) rises from a low, wide apron of pale gravel (256 x 220 across, about 38 high,
steep at its rim); rocks lie on it as the sprite shows them (a large dark boulder front right, a dark stone and a grey
stone left of the cone, mossy yellow rocks high on the cone, small stones at the rim) and three bare dead shrubs
stand on the cone's flanks and crest. The sprite is seen from above, so its 185-unit art includes the apron's depth;
the model's own height is the cone's.
Textures (Poly Haven, CC0): gravelly_sand (apron), brown_mud_rocks_01 (soil), rock_boulder_dry (stones),
rock_pitted_mossy (mossy rocks), bark_platanus (shrubs). COLOR_0 = vertex occlusion x a tint per part group toward
the sprite's region colours (hanging_lib.tint). Usage: blender --background --python heap_mound.py"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402
import heap_lib as hp  # noqa: E402

pl, hl, u = dlib.pl, dlib.hl, dlib.u
PROP = '7dec11'
RX, RY = 128.0, 110.0
PEAK = (4.0, 10.0, 146.0)          # crest x, y, height
# Native region colours (sRGB, small_measure.py bands): pale gravel apron, dark soil cone, rocks, moss, shrubs.
TARGET = {'gravel': (120, 101, 74), 'soil': (50, 41, 32), 'rock': (62, 56, 56), 'moss': (96, 90, 62),
          'shrub': (58, 48, 38)}


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def height(x, y):
    """A peaked heap: steep near its crest, spreading into a low gravel apron; broad lumps and a left shoulder."""
    rc = math.hypot((x - PEAK[0]) / (RX - abs(PEAK[0])), (y - PEAK[1]) / (RY - abs(PEAK[1])))
    rc *= 1 + 0.08 * hp.fbm(x, y, scale=60, seed=9.0)
    if rc >= 1:
        return 0.0
    h = PEAK[2] * (0.3 * (1 - rc) ** 1.7 + 0.7 * (1 - rc ** 1.6))
    h += 30.0 * math.exp(-((x + 45) ** 2 + (y + 5) ** 2) / 900.0)          # the shoulder left of the crest
    h += 12.0 * hp.fbm(x, y, scale=32, seed=5.0) * min(1.0, (1 - rc) * 3)
    return h * smoothstep(1.0, 0.9, rc)


def material_of(x, y, z):
    """Soil above a wavy line about 55 high (lower behind the crest), gravel below."""
    line = 50 + 24 * hp.fbm(x, y, scale=40, seed=1.5) - 0.35 * max(0.0, y)
    return 1 if z > line else 0


ROCKS = [  # centre (x, y, z on the surface + lift), size (x, y, z), seed, group, last level kept
    ((50, -72, 0), (74, 50, 56), 1.1, 'rock', 3),
    ((-40, -52, 0), (36, 30, 28), 2.3, 'rock', 3),
    ((-80, -46, 0), (30, 26, 24), 3.7, 'rock', 2),
    ((26, -22, 0), (30, 24, 26), 4.1, 'moss', 2),
    ((-18, -24, 0), (34, 26, 36), 5.3, 'moss', 2),
    ((90, -30, 0), (16, 14, 14), 6.7, 'rock', 1),
    ((-104, -26, 0), (14, 12, 12), 7.9, 'rock', 1),
    ((40, 50, 0), (30, 26, 24), 8.3, 'rock', 2),
    ((-50, 40, 0), (26, 24, 22), 9.1, 'moss', 1),
]
SHRUBS = [((-56, -22), 52, 0.9, 1.3), ((50, -14), 46, 0.8, 2.9), ((2, 12), 28, 0.6, 4.4)]

pl.reset()
mats = {'gravel': dlib.material('Gravel', 'misc_gravel', extras={'openyamm_specular': 0.2}),
        'soil': dlib.material('Soil', 'misc_soil', extras={'openyamm_specular': 0.2}),
        'rock': dlib.material('Rock', 'misc_rock', extras={'openyamm_specular': 0.3}),
        'moss': dlib.material('Moss', 'misc_mossrock', extras={'openyamm_specular': 0.2}),
        'shrub': dlib.material('Shrub', 'misc_driftwood', extras={'openyamm_specular': 0.2})}
lods = []
for level in range(4):
    rings, segments = [(22, 44), (13, 28), (7, 16), (4, 10)][level]
    body = hp.mound('mound', height, RX, RY, rings, segments, [mats['gravel'], mats['soil']], material_of, 0.8)
    # COLOR_0 targets by material: tag per vertex from its first face's material
    parts = [body]
    groups = {'rock': [], 'moss': [], 'shrub': []}
    for k, (c, size, seed, group, keep) in enumerate(ROCKS):
        if level > keep:
            continue
        z = height(c[0], c[1])
        groups[group].append(hp.rock(f'rock{k}', (c[0], c[1], z + size[2] * 0.35), size, seed, level, mats[group]))
    if level < 3:
        for k, ((x, y), h, spread, seed) in enumerate(SHRUBS):
            if level == 2 and k == 2:
                continue
            groups['shrub'] += hp.shrub(f'shrub{k}', (x, y, height(x, y) - 2), h, spread, seed, level, mats['shrub'])
    for group, objs in groups.items():
        hl.tag(objs, TARGET[group]); parts += objs
    me = body.data
    attr = me.attributes.new('Target', 'FLOAT_COLOR', 'POINT')
    colours = [None] * len(me.vertices)
    for poly in me.polygons:
        t = TARGET['soil'] if poly.material_index == 1 else TARGET['gravel']
        for v in poly.vertices:
            colours[v] = t
    for v, t in enumerate(colours):
        attr.data[v].color = (t[0] / 255, t[1] / 255, t[2] / 255, 1.0)
    for p in parts:
        dlib.apply(p)
    obj = pl.join('Base' if level == 0 else f'Base_LOD{level}', parts)
    pl.vertex_occlusion(obj, rays=(40, 24, 12, 8)[level], distance=u(40), strength=0.6, floor=False)
    hl.tint(obj, report=f'{PROP} L{level}')
    lods.append(obj)
dlib.save(PROP, lods)
