"""MM6 flambeaux `flamb00` (33 placements, six frames): a free-standing fire dish on a tall pole, violet metal.
Traced from the native frames (x2 pixels at 0.5 units, bottom row 397.5): a stepped octagonal plinth 58 units wide
and 24 high (flat shaded, as the sprite's faceted base), a pole 6 units thick with a dark collar above the plinth and
one under the dish, a shallow dish 58 units wide (rim top at 158), an unlit ember bed in the dish, and the flame card
(the shared flame02 flipbook) with its base in the embers at 155.5 and its tip at the sprite top, 199. COLOR_0: the sprite's violet pole (darkening downward), pink-violet plinth, deep blue dish
underside and fire-lit pink rim. Writes work/flambeaux_export.glb.
Usage: blender --background --python build_flambeaux.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fire_lib as fl  # noqa: E402

pl, u = fl.pl, fl.u
pl.reset()
mats = {
    'Metal': fl.material('Metal', 'fx_steel'),
    'Embers': fl.material('Embers', 'embers'),
    'Flame': fl.flame_material('Flame', 'flame02'),
}
PLINTH = [(0, 0), (26, 0), (29, 3), (29, 8.5), (24, 10), (21, 11), (20.5, 14.5), (17.5, 16.5), (10, 19.5), (5, 22),
          (3.6, 24.5)]
DISH = [(3.6, 140), (4.6, 141), (8, 142.6), (14, 144.2), (19, 146.5), (25.5, 150.5), (29, 154.5), (29.6, 156.5),
        (29, 158), (27.5, 158.2), (24, 156.6), (14, 153.6), (0, 152.6)]


def lathe(name, profile, segments, smooth=True, mat='Metal'):
    return pl.lathe(name, [(u(r), u(z)) for r, z in profile], segments, mats[mat], u_repeat=2.0, v_scale=3.0,
                    smooth=smooth)


def build(level):
    sides = (10, 6, 4)[level]
    dish = DISH if level < 2 else [DISH[0], DISH[4], DISH[6], DISH[8], DISH[10], DISH[12]]
    solids = [lathe('plinth', PLINTH if level < 2 else [PLINTH[i] for i in (0, 1, 3, 5, 6, 8, 10)], 8,
                    smooth=False),
              pl.tube('pole', (0, 0, u(24)), (0, 0, u(141)), u(3.0), u(3.0), sides, mats['Metal'], v_scale=1.0,
                      caps=False),
              lathe('dish', dish, (20, 12, 8)[level])]
    if level < 2:
        solids.append(lathe('collar', [(3.0, 28.5), (3.9, 29.5), (3.9, 32.5), (3.0, 33.5)], sides))
        solids.append(lathe('neck', [(3.0, 135), (3.8, 136), (4.4, 140)], sides))
    bed = [(0, 155.4), (14, 155.8), (24.4, 157.4)]
    whites = [lathe('embers', bed, (16, 10, 8)[level], mat='Embers'),
              fl.flame_card('flame', mats['Flame'], 'flame02', 155.5, 199.0, 44.0)]
    return solids, whites


POLE = [(24, (75, 60, 113)), (28, (41, 33, 59)), (33, (41, 33, 59)), (35, (62, 48, 97)), (50, (74, 58, 110)),
        (80, (86, 70, 133)), (100, (90, 74, 143)), (120, (98, 80, 148)), (138, (110, 86, 151))]
PLINTH_COLOURS = [(0, (150, 104, 165)), (3, (180, 128, 205)), (6.75, (150, 104, 165)), (10.75, (153, 111, 174)),
                  (14.75, (142, 99, 162)), (18.75, (110, 91, 156)), (23, (75, 60, 113))]
DISH_COLOURS = [(140, (31, 30, 66)), (146, (34, 33, 80)), (150, (40, 37, 107)), (154, (90, 72, 120)),
                (157, (116, 93, 130))]


def metal(co, normal):
    if co.z < 24.6:
        return fl.stops(PLINTH_COLOURS, co.z)
    if co.z < 141.5 and co.xy.length < 4.5:
        return fl.stops(POLE, co.z)
    if normal.z > 0.5 and co.z > 152:
        return (225, 160, 105)                 # the fire-lit rim top and inside
    return fl.stops(DISH_COLOURS, co.z)


fl.build_lods('Flambeaux', 'flambeaux', build, {'Metal': metal}, rays=(32, 20, 12), distance=20.0, strength=0.45)
