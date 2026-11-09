"""Hanging lantern `dec07` (54 placements: d24 51, d06 3; six frames in 12/16 s, light 96; 81 x 128 units). The
native frames change only the flame (the iron is still): an open oil lamp on a chain, traced from dec07a (x2 pixels
at 0.5 units): five links from the neck ring (79-83) to the pivot (128, the bounds top), a domed hood (collar 66-71,
dome to a flat brim 40.5 wide at 43.5-47.5), three thin rods (two in front at +-18 from the axis, one behind)
curving in to the oil bowl (rim 22 wide at 16.5, a point under it to 0) and a narrow flame from the bowl's centre (19)
to 41.

Surfaces: `iron_dark` (CC0 Rusty Metal 04) tinted to the sprite's fire-lit black iron with reddish chain highlights.
The flame is the shared Flame03 candle flipbook (camera-facing, on the axis). The flicker also lights the fixture:
the hood's underside and the bowl's inside are a lit `Underside` material whose warm emission flickers
(2026-10-16: `openyamm_flicker`, smooth random), the wick glows (`Oil`, the ember texture, flickering) and a soft
camera-facing additive warm halo (`Halo`, `openyamm_additive`) round the flame flickers with it. No glass: the sprite's lamp is open.
Writes work/lantern_export.glb. Usage: blender --background --python build_lantern.py"""
import math
import os
import sys

from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as al  # noqa: E402

pl, u = al.pl, al.u
pl.reset()
FLICKER = [0.35, 8.0]         # smooth random flicker (openyamm_flicker): amplitude, changes per second
mats = {
    'Iron': al.material('Iron', 'iron_dark', extras={'openyamm_specular': 0.6}),
    'Hood': al.material('Hood', 'iron_smooth', extras={'openyamm_specular': 0.8}),
    'Underside': al.glow_material('Underside', 'iron_dark', (60, 26, 8), extras={'openyamm_specular': 0.6},
                                  flicker=FLICKER),
    'Oil': al.glow_material('Oil', 'ember', (150, 70, 20), flicker=[0.4, 10.0]),
    'Halo': al.halo_material('Halo', emission=(60, 28, 8), flicker=[0.35, 8.0]),     # additive
    'Flame': al.flame_material('Flame', 'flame03'),
}
# Hood (radius, z units). pl.lathe faces point to the right of the profile's direction (outward for a profile that
# climbs, downward for one that runs outward and down), so the dome's outside runs from the brim in and up to the
# collar, and its inside, a shell 1.8 under the dome, from the axis out and down to the brim: from below one looks
# up into a deep, sooty hood instead of through it.
HOOD_TOP = [(40.8, 44.8), (40.5, 46.2), (37.0, 46.9), (33.5, 48.0), (31.8, 50.6), (30.6, 54.0), (28.6, 57.0),
            (25.0, 59.6), (20.0, 61.6), (14.0, 63.8), (9.0, 65.8), (5.5, 67.0)]
HOOD_UNDER = [(0.0, 64.6), (5.2, 64.4)] + [(r - 1.0, z - 1.8) for r, z in HOOD_TOP[-2:2:-1]] + [(39.0, 44.6),
                                                                                              (40.8, 44.8)]
BOWL_OUT = [(0.0, 0.0), (1.2, 1.2), (2.6, 3.8), (5.5, 6.0), (10.0, 7.6), (14.5, 9.8), (17.5, 12.5), (20.0, 14.8),
            (22.0, 16.4), (21.4, 17.4)]
BOWL_IN = [(21.4, 17.4), (19.5, 16.8), (15.0, 15.4)]
OIL = [(15.0, 15.4), (9.0, 15.9), (4.2, 16.2)]
WICK = [(4.2, 16.2), (3.6, 17.4), (2.4, 18.6), (0.0, 19.2)]
NECK = [(0.0, 67.0), (5.6, 67.0), (6.0, 69.0), (5.4, 71.0), (2.6, 71.6), (2.4, 76.5), (3.6, 78.0), (5.4, 79.2),
        (5.6, 81.6), (3.8, 83.0), (2.0, 83.4), (0.0, 83.4)]
RODS = [90.0, 210.0, 330.0]      # degrees: one behind (+y), two in front (x = +-18 in the front view)
WIRE = 2.4


def lathe(name, profile, segments, mat, u_repeat=2.0, v_scale=3.0, flat_every=1):
    pts = [(u(r), u(z)) for r, z in profile[::flat_every]]
    if flat_every > 1 and pts[-1] != (u(profile[-1][0]), u(profile[-1][1])):
        pts.append((u(profile[-1][0]), u(profile[-1][1])))
    return pl.lathe(name, pts, segments, mat, u_repeat=u_repeat, v_scale=v_scale)


def build(level):
    seg = (20, 12, 8)[level]
    step = (1, 2, 3)[level]
    solids = [lathe('hood', HOOD_TOP, seg, mats['Hood'], flat_every=step),
              lathe('hoodunder', HOOD_UNDER, seg, mats['Underside'], flat_every=step),
              lathe('bowl', BOWL_OUT, seg, mats['Hood'], flat_every=step),
              lathe('bowlin', BOWL_IN, seg, mats['Underside']),
              lathe('oil', OIL, seg, mats['Underside']),
              lathe('neck', NECK, (10, 6, 5)[level], mats['Iron'], flat_every=step)]
    for k, angle in enumerate(RODS):
        a = math.radians(angle)
        d = Vector((math.cos(a), math.sin(a), 0))
        if level < 2:
            path = [d * u(r) + Vector((0, 0, u(z))) for r, z in ((19.0, 17.0), (20.6, 20.5), (21.0, 25.0),
                                                                 (21.0, 40.0), (21.6, 44.8))]
            path = al.bezier(path, (8, 5)[level])
        else:
            path = [d * u(20.0) + Vector((0, 0, u(17.0))), d * u(21.4) + Vector((0, 0, u(44.8)))]
        solids.append(al.sweep(f'rod{k}', path, u(1.3), (5, 4, 3)[level], mats['Iron'], v_scale=4.0))
    if level < 2:
        solids += al.chain('link', mats['Iron'], (0, 0, u(81.0)), (0, 0, u(128.0 - WIRE)), u(9.4), u(11.0),
                           u(WIRE), (10, 6)[level], (4, 3)[level])
    else:
        solids.append(pl.tube('chain', (0, 0, u(81.0)), (0, 0, u(128.0)), u(3.2), u(3.2), 4, mats['Iron']))
    al.apply(solids)
    whites = [lathe('wick', WICK, (10, 8, 6)[level], mats['Oil']),
              al.halo_card('halo', mats['Halo'], 29.0, 15.0),
              al.flame_card('flame', mats['Flame'], 'flame03', 18.6, 41.0, 9.0)]
    return solids, whites


def iron(co, n):
    """The sprite's fire-lit black iron: reddish chain, a pale highlight band on the dome's shoulder, a copper-red
    brim edge, and the bowl paler at its rim than at its point."""
    r = math.hypot(co.x, co.y)
    if co.z > 79:
        return (58, 16, 8)
    if co.z > 66:
        return (62, 34, 22)
    if co.z > 43.5:
        if r > 37:
            return (96, 46, 28)
        return al.stops([(46, (56, 32, 24)), (50, (60, 46, 42)), (56, (52, 42, 40)), (61, (30, 26, 26)),
                         (66, (26, 22, 22))], co.z)
    if co.z > 18:
        return (66, 30, 18)                                  # rods, lit by the flame
    return al.stops([(0, (40, 28, 22)), (6, (52, 38, 30)), (12, (88, 64, 50)), (17.5, (100, 58, 40))], co.z)


COLOURS = {'Iron': iron, 'Hood': iron,
           # Inside the hood: soot-black at its top, warmer toward the brim where the flame's light reaches.
           'Underside': lambda co, n: al.stops([(0, (26, 18, 14)), (20, (34, 22, 16)), (34, (52, 30, 20)),
                                                (41, (66, 36, 22))], math.hypot(co.x, co.y)), 'Oil': (190, 100, 40), 'Halo': (255, 168, 80),
           'Flame': (255, 255, 255)}
al.build_lods('Lantern', 'lantern', build, COLOURS, rays=(32, 20, 12), distance=20.0, strength=0.5,
              last=('Halo', 'Flame'))
