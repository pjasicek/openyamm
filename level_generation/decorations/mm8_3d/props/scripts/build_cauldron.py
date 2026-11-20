"""Cauldron over burning coals `dec26` (MM7 `7dec03`, animated 7 frames, light 128) -> work/cauldron_export.glb,
installed as mm7_deco_cauldron.glb.

Traced from the sprite: a wide-bellied dark iron pot with a flared rim, its brew glowing red inside the rim, set on
four big glowing coal lumps with two charred logs crossed beneath and small flames licking up between the lumps.
Materials: Iron (cauldron_iron, a hammered dark iron; COLOR_0 reddens its lower belly where the fire lights it),
Brew (unlit glowing surface), Coals (emissive, `openyamm_pulse`), Char (charred logs, faint ember pulse), Fire (the
shared Flame02 flipbook on camera-facing cards, blended, unlit; drawn last). The sprite's animation (flames and
flickering glow) is the flame flipbook plus the pulses. Usage: blender --background --python build_cauldron.py"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl = ml.pl
H = 1.0                     # model height; the binding scales it to 128 units
# pot profile (radius, z), bottom to rim, traced from the x2 sprite (pot 0.26 .. 1.0 of the height, belly 0.46 wide)
POT = [(0.0, 0.27), (0.17, 0.27), (0.3, 0.31), (0.41, 0.4), (0.465, 0.53), (0.46, 0.66), (0.42, 0.79),
       (0.37, 0.88), (0.36, 0.92), (0.41, 0.97), (0.45, 1.0), (0.43, 1.0), (0.36, 0.95)]
COALS = [((-0.33, -0.1, 0.1), 0.15), ((-0.02, -0.24, 0.1), 0.15), ((0.3, -0.12, 0.1), 0.14), ((0.1, 0.2, 0.1), 0.13),
         ((-0.22, 0.2, 0.09), 0.12)]
LOGS = [((-0.55, -0.15, 0.04), (0.55, 0.12, 0.05)), ((-0.5, 0.2, 0.06), (0.52, -0.25, 0.07))]
CARDS = [(-0.17, 0.3, 0.05, 0.36, False), (0.16, 0.3, 0.05, 0.38, True), (0.0, 0.42, 0.06, 0.34, False)]
LEVELS = [{'seg': 28, 'coal': 2, 'log': 8, 'cards': 3}, {'seg': 16, 'coal': 1, 'log': 6, 'cards': 3},
          {'seg': 10, 'coal': 0, 'log': 4, 'cards': 1}]


def lump(name, centre, radius, subdiv, seed, mat):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv + 1, radius=radius)
    for v in bm.verts:
        d = v.co.normalized()
        v.co = d * radius * (1 + 0.3 * noise.noise(d * 1.7 + Vector((seed, 0, 0))))
        v.co.z *= 0.75
        v.co += Vector(centre)
        v.co.z = max(v.co.z, 0.0)
    obj = pl.to_object(name, bm, mat)
    ml.box_uv(obj, 0.4, seed)
    return obj


def build(level, mats):
    lv = LEVELS[level]
    pot = pl.lathe('Pot', [(r * H, z * H) for r, z in POT], lv['seg'], mats['Iron'], u_repeat=2.0, v_scale=1.5)
    ml.smooth(pot, 60)
    brew = pl.lathe('Brew', [(0.36 * H, 0.95 * H), (0.0, 0.955 * H)], lv['seg'], mats['Brew'], v_scale=1.0)
    ml.box_uv(brew, 0.6)
    coals = [lump(f'Coal{i}', c, r, lv['coal'], i, mats['Coals']) for i, (c, r) in enumerate(COALS)]
    logs = [pl.tube(f'Log{i}', a, b, 0.045, 0.04, lv['log'], mats['Char'], v_scale=2.0) for i, (a, b) in enumerate(LOGS)]
    solid = pl.join('Solid', [pot] + logs)
    ml.colour(solid, distance=0.25, strength=0.6)
    # the fire lights the lower belly and the logs red-orange (the sprite's glowing underside)
    def fire_lit(i, co, c):
        k = min(1.0, max(0.0, 0.6 - co.z) / 0.3)
        return (c[0], c[1] * (1 - 0.55 * k), c[2] * (1 - 0.75 * k), 1.0)
    ml.set_colour(solid, fire_lit)
    glow = pl.join('Glow', coals + [brew])
    ml.colour(glow, rays=8, distance=0.01, strength=0.0)
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    for cx, w, lo, hi, mirrored in CARDS[:lv['cards']]:
        verts = [bm.verts.new(c) for c in ((cx - w / 2, 0, lo), (cx + w / 2, 0, lo), (cx + w / 2, 0, hi),
                                           (cx - w / 2, 0, hi))]
        f = bm.faces.new(verts)
        for loop, (u, v) in zip(f.loops, ((0, 1), (1, 1), (1, 0), (0, 0))):
            loop[uv].uv = (1 - u if mirrored else u, (1 - v) * pl.FLAME_FRAME_TOP)
    fire = pl.to_object('Fire', bm, mats['Fire'], smooth=False)
    ml.colour(fire, rays=4, distance=0.01, strength=0.0)
    name = 'Cauldron' if level == 0 else f'Cauldron_LOD{level}'
    return pl.join(name, [solid, glow, fire])            # Fire's primitive last: blended after the solid parts


def main():
    pl.reset()
    mats = {'Iron': ml.material('Iron', 'cauldron_iron', extras={'openyamm_specular': 0.7}),
            'Brew': ml.material('Brew', 'cauldron_brew', extras={'openyamm_specular': 0.0}),
            'Coals': ml.material('Coals', 'cauldron_coals', extras={'openyamm_specular': 0.5}),
            'Char': ml.material('Char', 'cauldron_logs', extras={'openyamm_specular': 0.2}),
            'Fire': pl.flame_material('Fire')}
    levels = [build(k, mats) for k in range(3)]
    ml.ground(levels)
    for o in levels:
        ml.apply_transforms(o)
    print('LODS', [pl.triangles(o) for o in levels])
    ml.export(levels, 'cauldron')


main()
