"""Campfire `dec24` (9 outdoor placements: out08 4, out02 2, out01, out04, out13; eight frames in 1 s, light 128;
63 x 51 units). Unlike the MM6 campfire (a stone ring with a log teepee), dec24 is a low pile of four cut logs with
no stones, traced from the unlit frame dec24x and dec24a (x2 pixels at 0.5 units): two logs lying side by side in
front (the left one 12 thick, its red cut end at x -30; the right one 11 thick, further forward), one resting
across them behind (13 thick, red end at the left, 15-28 high) and a short one at the back right (red end at x 28).
The fire rises from inside the pile to 51.

Surfaces: `bark` (CC0 Bark Brown 02) tinted to the sprite's brown bark, warmer and redder where it faces the fire,
cut ends on the procedural `logend` (reddish sapwood rings). Fire (2026-10-16): a broad blaze of three
camera-facing Flame02 tongues side by side, an additive Flame02 blaze over their bases, rising additive sparks, a
glowing ember bed with coals under the logs (`Embers`), the bark faintly ember-lit, and a soft additive halo; every
fire-lit part flickers (`openyamm_flicker`).
Writes work/campfire_export.glb. Usage: blender --background --python build_campfire.py"""
import math
import os
import sys

import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as al  # noqa: E402

pl, u = al.pl, al.u
pl.reset()
mats = {
    'Bark': al.glow_material('Bark', 'bark', (16, 5, 1), extras={'openyamm_specular': 0.25}, flicker=(0.45, 6.0)),
    'LogEnd': al.material('LogEnd', 'logend', extras={'openyamm_specular': 0.2}),
    'Embers': al.glow_material('Embers', 'ember', (150, 60, 14), flicker=(0.4, 9.0)),
    'Halo': al.halo_material('Halo', emission=(70, 30, 8), flicker=(0.3, 6.0)),
    'Flame': al.flame_material('Flame', 'flame02'),
    # Additive fire low across the pile: the sprite's broad, bright blaze.
    'Blaze': al.flame_material('Blaze', 'flame02', additive=True, flicker=(0.25, 8.0), emission=(30, 12, 3)),
    'Sparks': al.flame_material('Sparks', 'sparks', additive=True, flipbook=(8, 4, 12)),
}
# (foot, tip, radius, which end shows a cut face): units, x across, y toward the back, z up.
LOGS = [((-30.0, -6.0, 6.0), (4.0, -4.0, 6.0), 6.0),
        ((-2.0, -13.0, 5.5), (29.0, -11.0, 5.5), 5.5),
        ((-18.0, 1.0, 21.5), (17.0, 9.0, 17.0), 6.4),
        ((7.0, 9.0, 12.5), (28.0, 5.0, 13.5), 5.0)]
CENTRE = Vector((0.0, -1.0, 8.0))


def log(name, a, b, r, sides, seed):
    """A slightly irregular log: bark round its length, logend discs on both cut ends."""
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    side = axis.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(axis)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    rings = []
    length = (b - a).length
    for e, centre in enumerate((a, b)):
        ring = []
        for s in range(sides):
            ang = 2 * math.pi * s / sides
            wobble = 1 + 0.06 * math.sin(ang * 3 + seed + e)
            p = centre + (side * math.cos(ang) + up * math.sin(ang)) * r * wobble
            ring.append(bm.verts.new((u(p.x), u(p.y), u(p.z))))
        rings.append(ring)
    for s in range(sides):
        s2 = (s + 1) % sides
        f = bm.faces.new((rings[0][s], rings[1][s], rings[1][s2], rings[0][s2]))     # outward
        for loop, (i, e) in zip(f.loops, ((s, 0), (s, 1), (s + 1, 1), (s + 1, 0))):
            loop[uv].uv = (i / sides * 0.8 + seed * 0.37, e * length / 60.0)
    coords = [[Vector(v.co) for v in ring] for ring in rings]
    bark = pl.to_object(name, bm, mats['Bark'])
    ends = []
    for e, (centre, ring) in enumerate(((a, coords[0]), (b, coords[1]))):
        bm = bmesh.new()
        uv = bm.loops.layers.uv.verify()
        verts = [bm.verts.new(co) for co in ring]
        f = bm.faces.new(verts if e == 0 else list(reversed(verts)))                # facing away from the log
        for loop in f.loops:
            p = Vector(loop.vert.co) * al.dl.UNITS_PER_METRE - centre
            loop[uv].uv = (0.5 + p.dot(side) / (2.15 * r), 0.5 + p.dot(up) / (2.15 * r))
        ends.append(pl.to_object(f'{name}_end{e}', bm, mats['LogEnd'], smooth=False))
    return [bark] + ends


def ember_bed(level):
    # Profile from the rim in and up: lathe faces point to the right of the profile's direction (up, here).
    parts = [pl.lathe('bed', [(u(14.0), 0.0), (u(10.5), u(2.4)), (u(6.0), u(5.0)), (0.0, u(6.0))], (14, 10, 6)[level],
                      mats['Embers'], u_repeat=2.0, v_scale=6.0, centre=(u(CENTRE.x), u(CENTRE.y), 0))]
    if level < 1:
        for k in range(7):
            a = 2 * math.pi * k / 7 + 0.5
            cb = bmesh.new()
            bmesh.ops.create_icosphere(cb, subdivisions=1, radius=1.0)
            cuv = cb.loops.layers.uv.verify()
            r = 6.0 + 2.5 * (k % 2)
            for v in cb.verts:
                v.co = Vector((u(v.co.x * 3.2 + CENTRE.x + math.cos(a) * r), u(v.co.y * 2.6 + CENTRE.y + math.sin(a) * r),
                               u(v.co.z * 2.0 + 4.5 - (k % 2))))
            for f in cb.faces:
                for loop in f.loops:
                    loop[cuv].uv = (loop.vert.co.x * 6 + k * 0.3, loop.vert.co.y * 6)
            parts.append(pl.to_object(f'coal{k}', cb, mats['Embers']))
    return parts


def build(level):
    sides = (10, 7, 5)[level]
    solids = []
    for k, (a, b, r) in enumerate(LOGS):
        solids += log(f'log{k}', a, b, r, sides, k)
    whites = ember_bed(level) + [al.halo_card('halo', mats['Halo'], 25.0, 24.0)]
    # A broad blaze: three tongues side by side in the camera-facing plane (a model-axis billboard keeps each
    # card's offset across the model), each on its own part of the loop, and an additive blaze over their bases.
    whites.append(al.flame_card('flame', mats['Flame'], 'flame02', 7.0, 51.0, 46.0))
    whites.append(al.flame_card('blaze', mats['Blaze'], 'flame02', 5.0, 34.0, 58.0, frame_offset=11))
    if level < 2:
        whites.append(al.flame_card('flame_l', mats['Flame'], 'flame02', 6.0, 40.0, 34.0, x=-14.0, mirrored=True,
                                    frame_offset=21))
        whites.append(al.flame_card('flame_r', mats['Flame'], 'flame02', 6.0, 43.0, 34.0, x=15.0, frame_offset=43))
        whites.append(al.spark_card('sparks', mats['Sparks'], 8.0, 51.0, 36.0))
    return solids, whites


def bark(co, n):
    """dec24x's bark (lit tops about 129, 86, 56; shaded sides 56-73, 36-49, 22-31), reddened where it faces the
    fire (dec24a's lit logs)."""
    base = al.stops([(-1, (60, 40, 25)), (0.6, (110, 76, 50)), (1, (132, 90, 58))], n.z)
    to_fire = (CENTRE - co).normalized()
    f = max(0.0, n.dot(to_fire)) * 0.6
    return (min(255, base[0] * (1 + 0.5 * f)), base[1] * (1 - 0.15 * f), base[2] * (1 - 0.4 * f))


COLOURS = {'Bark': bark, 'LogEnd': (178, 86, 60), 'Embers': (200, 96, 32), 'Halo': (255, 150, 60)}
al.build_lods('Campfire', 'campfire', build, COLOURS, rays=(24, 16, 10), distance=12.0, strength=0.5,
              last=('Halo', 'Flame', 'Blaze', 'Sparks'))
