"""Bell buoy `dec30` (17 placements: out01 9, out02 4, out13 4; eight frames in 1 s, light 0; 87 x 234 units), traced
from dec30a-h (x2 pixels at 0.5 units): a tapering barrel of wooden staves (r 43 at 35 to 35.5 at its rim, 110),
two dark studded bands (25-33, 93-100), a copper cage of four flat bars from the rim to a top ring (r 23.5 at
205-213) through a middle ring (r 27 at 177-181), a brass bell hanging from a crossbar under the middle ring (mouth
125, crown 170) with its clapper below, and a copper dome (213-234). No lamp: the frames show no light. The frames
rock the whole buoy (its top about +-5 units, sideways and toward the viewer) and swing the bell about +-15 degrees
inside the cage in 1 s.

Motion: every material sways with `openyamm_wind` (rocking that grows with height, slow 5.7 s bend plus 1.9 s
flutter); the bell and clapper have a larger amplitude, so they swing against the cage. Surfaces: `staves` (CC0 Brown
Planks 03, one plank per stave), `copper` (CC0 Blue Metal Plate scratches graded to copper) for cage and rings,
`brass` (the same scan, paler) for the dome and bell, `iron_dark` (CC0 Rusty Metal 04) for the bands with raised studs.
Writes work/buoy_export.glb. Usage: blender --background --python build_buoy.py"""
import math
import os
import sys

import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as al  # noqa: E402

pl, u = al.pl, al.u
pl.reset()
WIND = 0.09                 # model metres at the top (2.86 m model): about 7 units at the dome
BELL_WIND = 0.2
mats = {
    'Staves': al.material('Staves', 'staves', extras={'openyamm_wind': WIND, 'openyamm_specular': 0.35}),
    'Band': al.material('Band', 'iron_dark', extras={'openyamm_wind': WIND, 'openyamm_specular': 0.5}),
    'Copper': al.material('Copper', 'copper', extras={'openyamm_wind': WIND, 'openyamm_specular': 1.0}),
    'Brass': al.material('Brass', 'brass', extras={'openyamm_wind': WIND, 'openyamm_specular': 1.0}),
    'Bell': al.material('Bell', 'brass', extras={'openyamm_wind': BELL_WIND, 'openyamm_specular': 1.0}),
}
BARREL = [(0.0, 0.0), (30.0, 0.0), (37.5, 1.6), (40.6, 6.0), (42.6, 18.0), (43.4, 34.0), (42.8, 50.0),
          (41.4, 66.0), (39.6, 82.0), (37.4, 98.0), (35.8, 106.0), (35.6, 110.0), (33.4, 110.4), (32.6, 108.6),
          (0.0, 108.6)]
DOME = [(0.0, 212.6), (23.0, 212.6), (21.0, 216.0), (19.0, 221.0), (15.6, 226.0), (10.6, 230.0), (5.0, 232.4), (2.4, 232.8),
        (2.6, 234.0), (0.0, 234.0)]
BELL = [(0.0, 172.0), (4.0, 171.6), (8.4, 169.4), (10.6, 165.0), (11.4, 158.0), (12.6, 148.0), (15.0, 138.0),
        (18.4, 131.0), (21.4, 127.0), (21.6, 125.2), (19.8, 125.6), (16.0, 130.0), (12.0, 136.0), (9.0, 146.0),
        (7.6, 158.0), (6.0, 165.0), (0.0, 166.0)]
BELL = BELL[::-1]           # lathe faces point to the right of the profile's direction: inner crown first
BELL_X = 3.0                # the bell hangs a little off the cage axis in every frame


def radius_at(profile, z):
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        if z0 <= z <= z1 and z1 > z0:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return profile[-1][0]


def lathe(name, profile, segments, mat, u_repeat, v_scale, step=1, centre=(0, 0, 0)):
    pts = profile[::step] + ([profile[-1]] if (len(profile) - 1) % step else [])
    return pl.lathe(name, [(u(r), u(z)) for r, z in pts], segments, mat, u_repeat=u_repeat, v_scale=v_scale,
                    centre=centre)


def band(name, z0, z1, segments, level):
    r0, r1 = radius_at(BARREL, z0), radius_at(BARREL, z1)
    profile = [(r0 - 0.4, z0), (r0 + 1.6, z0 + 0.6), (r0 + 2.2, (z0 + z1) / 2), (r1 + 1.6, z1 - 0.6), (r1 - 0.4, z1)]
    parts = [lathe(name, profile, segments, mats['Band'], 6.0, 8.0, step=1 if level == 0 else 2)]
    if level == 0:
        # Studs (the sprite's bright stones and rivets in the bands).
        for k in range(22):
            a = 2 * math.pi * (k + 0.5 * (int(z0) % 2)) / 22
            r = (r0 + r1) / 2 + 2.4
            sb = bmesh.new()
            bmesh.ops.create_icosphere(sb, subdivisions=1, radius=u(1.5))
            suv = sb.loops.layers.uv.verify()
            for v in sb.verts:
                v.co = Vector((v.co.x, v.co.y * 0.8, v.co.z * 1.1)) + Vector((u(r * math.cos(a)), u(r * math.sin(a)),
                                                                                u((z0 + z1) / 2)))
            for f in sb.faces:
                for loop in f.loops:
                    loop[suv].uv = (loop.vert.co.x * 8, loop.vert.co.z * 8)
            parts.append(pl.to_object(f'{name}_stud{k}', sb, mats['Band']))
    return parts


def flat_ring(name, z0, z1, r, segments):
    t = 1.6
    profile = [(r - t, z0), (r, z0), (r, z1), (r - t, z1), (r - t, z0)]
    return lathe(name, profile, segments, mats['Copper'], 4.0, 6.0)


def build(level):
    seg = (28, 16, 10)[level]
    parts = [lathe('barrel', BARREL, seg, mats['Staves'], 16 / 9 * 1.0, 0.55, step=1 if level < 2 else 2)]
    parts += band('band0', 25.0, 33.0, seg, level)
    parts += band('band1', 93.0, 100.0, seg, level)
    parts.append(flat_ring('ring_mid', 176.0, 182.0, 27.4, (24, 14, 8)[level]))
    parts.append(flat_ring('ring_top', 205.0, 213.0, 24.2, (24, 14, 8)[level]))
    parts.append(lathe('dome', DOME, (20, 12, 8)[level], mats['Brass'], 2.0, 3.0, step=1 if level < 2 else 2))
    # Four flat bars: rim (r 32) to the top ring (r 23.4), turned 25 degrees so the front view shows four.
    for k in range(4):
        a = math.radians(25 + 90 * k)
        d = Vector((math.cos(a), math.sin(a), 0))
        bottom = d * u(32.4) + Vector((0, 0, u(108.0)))
        top = d * u(23.2) + Vector((0, 0, u(212.0)))
        parts.append(al.sweep(f'bar{k}', [bottom, top], u(2.4), 4, mats['Copper'], v_scale=2.0,
                              flat=(1.5, 0.6)))
    # Crossbar under the middle ring and the bell on its hook.
    parts.append(pl.tube('crossbar', (u(-26.0), 0, u(178.0)), (u(26.0), 0, u(178.0)), u(1.2), u(1.2),
                         (6, 4, 3)[level], mats['Copper']))
    parts.append(lathe('bell', BELL, (18, 12, 8)[level], mats['Bell'], 2.0, 4.0, step=1 if level < 2 else 3,
                       centre=(u(BELL_X), 0, 0)))
    if level < 2:
        parts.append(pl.tube('hook', (u(BELL_X), 0, u(171.0)), (u(BELL_X), 0, u(178.0)), u(1.6), u(1.2), 5,
                             mats['Bell']))
        parts.append(pl.tube('clapper', (u(BELL_X), 0, u(166.0)), (u(BELL_X), 0, u(121.0)), u(0.9), u(0.9), 5,
                             mats['Bell']))
        cb = bmesh.new()
        bmesh.ops.create_icosphere(cb, subdivisions=1, radius=u(3.2))
        cb.loops.layers.uv.verify()
        for v in cb.verts:
            v.co += Vector((u(BELL_X), 0, u(119.5)))
        parts.append(pl.to_object('ball', cb, mats['Bell']))
    al.apply(parts)
    return parts, []


def staves(co, n):
    """dec30a's staves: warm orange (183-187, 110-115, 53-56) lit, darker low down and at the rim."""
    return al.stops([(0, (120, 66, 22)), (8, (150, 85, 36)), (40, (180, 110, 54)), (85, (184, 112, 55)),
                     (104, (160, 96, 44)), (111, (140, 84, 40))], co.z)


COLOURS = {
    'Staves': staves,
    'Band': (48, 34, 22),
    # Cage bars and rings dark copper (113-143, 66-93, 31-51); the dome and bell bright brass (190-204, 143-165, 98-138).
    'Copper': (132, 84, 44),
    'Brass': (200, 150, 112),
    'Bell': (192, 144, 92)}
al.build_lods('Buoy', 'buoy', build, COLOURS, rays=(24, 16, 10), distance=30.0, strength=0.5)
