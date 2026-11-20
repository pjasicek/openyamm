"""Iron lantern torch02 (dungeons), traced from the restored native frames (x2 pixels at 0.5 units): a domed foot,
a rolled collar, a flaring cage of rusty bars (alpha cut-out on a cone) round a glowing glass chimney, a wide lid
band, a domed cap with a knob, and a wire bail handle. The glow pulses (openyamm_pulse; the four native frames
flicker the light inside the cage: openyamm_flicker), with a faint additive halo card round it.
The placements stand about 10 units from a wall, 176 units above the floor, so the `lantern` variant is wall-mounted:
a plate on the wall (back toward Blender +y) and an arm whose hook holds the bail. `lantern_free` is the lantern
alone, for placements with no wall in reach. Writes work/<variant>_export.glb.
Usage: blender --background --python build_lantern.py -- lantern|lantern_free"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firelib as fl  # noqa: E402

pl = fl.pl
VARIANT = sys.argv[sys.argv.index('--') + 1]
WALL = VARIANT == 'lantern'
pl.reset()
mats = {'Iron': fl.material('Iron', 'rust', extras={'openyamm_specular': 0.5}),
        'Cage': fl.material('Cage', 'grid', alpha=True),
        'Glow': fl.glow_material('Glow', 'rust', (225, 132, 70), extras={'openyamm_flicker': [0.25, 6.0]}),
        'Halo': fl.halo_material('Halo')}

FOOT = [(0, 0), (16, 0.5), (24, 2.5), (28.5, 6), (29.8, 10), (29.3, 14), (27.5, 17.5), (24.5, 21), (21.5, 24),
        (19.5, 26), (15, 26.5)]
NECK = [(11.5, 35), (12.5, 36), (12.5, 38)]
CAGE = [(12.0, 37), (21.7, 75)]
CORE = [(7.0, 39), (10.5, 74)]
LID = [(19, 74), (23.5, 74.5), (25.6, 76), (25.6, 90), (25, 92), (18, 92.8), (10, 93.2), (6, 94), (6.8, 96),
       (5.8, 99), (3, 100.3), (0, 100.6)]
HANDLE_PIVOT, HANDLE_TOP, HANDLE_HALF = 86.0, 126.5, 27.6
PLATE_Y = 31.0                     # wall plate back face (Blender +y), just behind the foot (radius 30)


def handle(level):
    """Wire bail in the x/z plane: from pivots on the lid band's sides up over the cap (a half ellipse)."""
    parts = []
    steps = (12, 8, 5)[level]
    points = []
    for i in range(steps + 1):
        a = math.pi * i / steps
        c, s = math.cos(a), math.sin(a)
        # A squarish arch (superellipse): near-vertical sides, then a round top, as the native bail.
        points.append((HANDLE_HALF * math.copysign(abs(c) ** 0.6, c), 0.0,
                       HANDLE_PIVOT + (HANDLE_TOP - HANDLE_PIVOT) * abs(s) ** 0.8))
    for i, (p0, p1) in enumerate(zip(points, points[1:])):
        parts.append(fl.tube(f'bail{i}', p0, p1, 1.1, 1.1, (4, 3, 3)[level], mats['Iron'], caps=False))
    if level < 2:
        for side in (-1, 1):
            parts.append(fl.tube(f'pivot{side}', (side * 25.2, 0, HANDLE_PIVOT), (side * 28.8, 0, HANDLE_PIVOT), 2.0,
                                 2.0, 6,
                                 mats['Iron']))
    return parts


def bracket(level):
    """Wall plate with an arm reaching forward over the cap to a hook through the bail's top."""
    parts = [pl.box('plate', (0, fl.u(PLATE_Y - 1.2), fl.u(96)), (fl.u(14), fl.u(2.4), fl.u(34)), mats['Iron'],
                    uv_scale=6)]
    sides = (4, 3, 3)[level]
    path = [(0, PLATE_Y - 2, 104), (0, 21, 121), (0, 8, 128.0), (0, 0, 128.6)]
    for i, (p0, p1) in enumerate(zip(path, path[1:])):
        parts.append(fl.tube(f'arm{i}', p0, p1, 1.7, 1.5, sides, mats['Iron'], caps=False))
    if level < 2:
        parts.append(fl.tube('hook', (0, 0, 128.6), (0, -2.6, 124.8), 1.3, 1.0, sides, mats['Iron'], caps=False))
        for z in (85, 107):
            parts.append(fl.tube(f'rivet{z}', (0, PLATE_Y - 2.4, z), (0, PLATE_Y - 3.6, z), 1.6, 1.2, 6,
                                 mats['Iron']))
    return parts


def build(level):
    seg = (16, 10, 8)[level]
    step = (1, 2, 3)[level]

    def thin(profile):
        return [p for i, p in enumerate(profile) if i % step == 0 or i == len(profile) - 1]
    solids = [fl.lathe('foot', thin(FOOT), seg, mats['Iron'], u_repeat=2, v_scale=2),
              fl.torus('roll', 14.6, 4.5, 31.0, seg, (8, 6, 4)[level], mats['Iron'], squash=0.9),
              fl.lathe('neck', NECK, seg, mats['Iron'], u_repeat=2, v_scale=2),
              fl.lathe('lid', thin(LID), seg, mats['Iron'], u_repeat=2, v_scale=2)]
    if level < 2:
        solids.append(fl.torus('cagefoot', 12.6, 1.4, 38.0, seg, 4, mats['Iron']))
    solids += handle(level)
    if WALL:
        solids += bracket(level)
    whites = [fl.lathe('cage', CAGE, seg, mats['Cage'], u_repeat=2, v_scale=1.0 / fl.u(39.2)),
              fl.lathe('core', CORE, max(seg - 4, 6), mats['Glow'], u_repeat=1, v_scale=2),
              fl.glow_card('halo', mats['Halo'], 57.0, 72.0, 58.0)]
    return solids, whites


# Native colours (torch02a, by height): fire-lit rust orange on the foot and roll, dark neck and lid band, the
# glass glowing peach-orange behind dark bars.
STOPS = [(0, (100, 33, 1)), (6, (145, 48, 1)), (16, (140, 46, 1)), (24, (70, 24, 2)), (28, (150, 54, 2)),
         (34, (95, 30, 1)), (37, (50, 14, 1)), (74, (60, 18, 1)), (76, (95, 30, 1)), (86, (90, 28, 1)),
         (92, (55, 15, 1)), (95, (80, 25, 1)), (100, (70, 20, 1))]


def iron(co, n):
    if co.z > 84 and (abs(co.x) > 26 or co.z > 101 or co.y > 4):
        return (80, 24, 1)                  # bail, hook, arm and plate
    return fl.stops(STOPS, co.z)


colours = {'Iron': iron, 'Cage': (64, 20, 2), 'Glow': (150, 80, 35), 'Halo': ('mul', (0.42, 0.19, 0.05))}
fl.build_lods('Lantern', VARIANT, build, colours, rays=(32, 20, 12), distance=12.0, strength=0.6, sharp=40,
              last=('Cage', 'Halo'))
