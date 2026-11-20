"""MM6 dungeon bucket `bucket`: a tapered tub of 24 brown staves (`staves`: eight planks per texture repeat with dark
gaps, three repeats around), wider at the top (0.94 x the height across) than at the foot (0.78), with a pale
`endgrain` rim, the staves' inner face, a plank floor and dark water standing below the rim (the sprite shows a thin
grey-blue sliver of it behind the front rim). Three riveted iron hoops (`hoop`) at the sprite's heights: a wide one
at the foot (0.03-0.12), one at 0.24-0.29 and one under the rim at 0.77-0.83. Lathes per level (32 / 16 / 10 sides).
COLOR_0: occlusion x the tints that bring each texture to the sprite's colours (wood (90, 58, 35), hoops (40, 40, 44),
rim (150, 120, 88), water (30, 35, 45)). Writes work/bucket_export.glb.
Usage: blender --background --python build_bucket.py"""
import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import containers_lib as cl  # noqa: E402

pl = cl.pl
H = cl.u(67)
R_FOOT, R_TOP = 0.39 * H, 0.47 * H
WALL = 0.05 * H
WATER = 0.82 * H
HOOPS = ((0.03, 0.12), (0.24, 0.29), (0.77, 0.83))

pl.reset()
mats = {'Wood': cl.material('Wood', 'staves'), 'Rim': cl.material('Rim', 'endgrain'),
        'Hoop': cl.material('Hoop', 'hoop'), 'Water': cl.material('Water', 'water')}


def radius(z):
    return R_FOOT + (R_TOP - R_FOOT) * z / H


def disc(name, z, r, sides, mat, flip=False, uv_scale=1.0):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    verts = [bm.verts.new((r * math.cos(2 * math.pi * s / sides), r * math.sin(2 * math.pi * s / sides), z))
             for s in range(sides)]
    face = bm.faces.new(list(reversed(verts)) if flip else verts)
    for loop in face.loops:
        loop[uv].uv = (loop.vert.co.x * uv_scale + 0.5, loop.vert.co.y * uv_scale + 0.5)
    return pl.to_object(name, bm, mat, smooth=False)


def build(level):
    sides = (32, 16, 10)[level]
    rings = (6, 3, 1)[level]
    outer = [(radius(H * i / rings), H * i / rings) for i in range(rings + 1)]
    outer[0] = (R_FOOT, 0.0)
    parts = [pl.lathe('staves', [(R_FOOT - WALL, 0.0)] + outer, sides, mats['Wood'], u_repeat=3, v_scale=1.6)]
    # the rim's end grain, then the staves' inner face down to the water line
    parts.append(pl.lathe('rim', [(R_TOP, H), (R_TOP - WALL * 0.5, H + 0.006 * H), (R_TOP - WALL, H)], sides,
                          mats['Rim'], u_repeat=6, v_scale=8.0))
    parts.append(pl.lathe('inner', [(R_TOP - WALL, H), (radius(WATER) - WALL, WATER)], sides, mats['Wood'],
                          u_repeat=3, v_scale=1.6))
    parts.append(disc('water', WATER, radius(WATER) - WALL + 0.002, sides, mats['Water'], uv_scale=1.0 / H))
    parts.append(disc('floor', 0.0, R_FOOT - WALL, sides, mats['Wood'], flip=True, uv_scale=1.0 / H))
    for k, (z0, z1) in enumerate(HOOPS):
        z0, z1 = z0 * H, z1 * H
        r0, r1 = radius(z0), radius(z1)
        proud = 0.012 * H
        profile = [(r0 - 0.002, z0), (r0 + proud, z0), (r1 + proud, z1), (r1 - 0.002, z1)]
        if level == 2:
            profile = [(r0 + proud, z0), (r1 + proud, z1)]
        repeat = max(1, round(2 * math.pi * r0 / 0.25))
        parts.append(pl.lathe(f'hoop{k}', profile, sides, mats['Hoop'], u_repeat=repeat,
                              v_scale=1.0 / (z1 - z0 + 2 * proud)))
    return pl.join(f'bucket{level}', parts)


lods = [build(level) for level in range(3)]
# Wood and hoop targets: the sprite's means, wood pushed a little warmer (86, 54, 28) because the sky and sun
# specular grey it in the renders.
tints = {'Wood': cl.tint_for(mats['Wood'], (86, 54, 28)), 'Hoop': cl.tint_for(mats['Hoop'], (48, 48, 54)),
         'Rim': cl.tint_for(mats['Rim'], (150, 120, 88)), 'Water': cl.tint_for(mats['Water'], (30, 35, 45))}
print('TINTS', tints)
cl.finish('Bucket', lods, tints, {'rays': 40, 'distance': H * 0.4, 'strength': 0.65}, prop='bucket')
