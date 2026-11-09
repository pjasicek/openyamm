"""MM6 gold sconces, traced from the native frames (x2 pixels at 0.5 units):
- `scon200` (20 placements, six frames, 127 units): a goblet cup (rim 44 units wide at 58) with two loop handles at
  its sides, six leaf lobes round its lower bell, a stem with a ring knob and a spike tip at the bottom, and the
  flame card above the cup to the sprite top.
- `scon100` (2 placements, seven frames, 98 units): a squat spinning-top bowl 62 units wide (widest band at 20), its
  domed top stepped up in gold rings with dark grooves to a central opening at 31 that the flame card rises from.
The flame cards (the shared flame03 flipbook, narrowed like the sprites' tall thin flames) have their base in the cup
or opening and their tip at the sprite top; a small unlit ember disc fills each opening. The wall variants (mount: wall) add a gold arm from the stem or
bowl back to a wall plate (Blender +y, glTF -z) that stays within the sprite's height; the _free variants (free_model)
are the sprite's fixture alone. COLOR_0: the sprite's gold and orange by height (bright rims and bands, dark orange
stem and spike, a dark opening). Writes work/<prop>_export.glb.
Usage: blender --background --python build_sconce.py -- sconce2|sconce2_free|sconce1|sconce1_free"""
import math
import os
import sys

import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fire_lib as fl  # noqa: E402

pl, u = fl.pl, fl.u
PROP = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'sconce2'
KIND = PROP.split('_')[0]
FREE = PROP.endswith('_free')

SPECS = {
    'sconce2': {
        'flame': (51.0, 127.0, 24.0),          # flame base, tip, card width
        'profile': [(0, 0), (1.5, 1), (2.5, 4), (2.6, 7), (3.5, 10), (4.5, 13), (5.8, 15.5), (6.2, 18), (5.8, 20.5),
                    (4.8, 23), (5, 25), (7, 28), (8.5, 31), (11.5, 34), (16, 37), (19, 40), (20.5, 43), (20, 46.5),
                    (19.5, 49), (20.5, 53), (22, 56.5), (22.6, 58.2), (22, 58.8), (20.6, 58), (17.5, 54), (12, 50.5),
                    (0, 49.5)],
        'embers': [(0, 50.2), (6, 50.6)],
        'colours': [(0, (40, 10, 0)), (4, (72, 19, 0)), (7, (99, 28, 0)), (10, (97, 29, 1)), (13, (161, 61, 3)),
                    (16, (197, 86, 7)), (19, (200, 101, 10)), (22, (170, 61, 2)), (25, (120, 37, 3)),
                    (28, (129, 41, 3)), (31, (136, 45, 4)), (34, (129, 43, 4)), (37, (144, 50, 6)), (40, (186, 84, 9)),
                    (43, (195, 108, 17)), (46, (216, 146, 39)), (49, (185, 95, 19)), (52, (183, 99, 18)),
                    (55, (246, 195, 54)), (58.6, (181, 122, 37))],
        'inside': (90, 32, 8),
        # Wall arm (y from, y to, z), brace (y, z) to (y, z), plate (y back face, half width, z from, z to).
        'arm': (3, 26, 27), 'brace': ((4.5, 13), (26, 22)), 'plate': (28, 6, 9, 45),
    },
    'sconce1': {
        'flame': (29.5, 98.0, 24.0),
        'profile': [(0, 0), (5.5, 0.5), (12, 3), (17, 5.5), (19.5, 8), (23, 10.5), (25.5, 13), (28.5, 15.5),
                    (30.5, 18), (31, 20.5), (30.5, 23), (28, 24), (27.2, 23.8), (25, 25.5), (24, 25.4), (22.5, 26.5),
                    (20.5, 28), (19.5, 27.9), (16, 29.3), (13, 30), (12.2, 29.9), (10.5, 31), (9, 30.6), (7, 28.6),
                    (0, 28)],
        'embers': [(0, 28.6), (4.5, 28.9)],
        # Dark grooves between the domed top's gold rings (radii of the groove vertices).
        'grooves': (27.2, 24, 19.5, 12.2),
        'colours': [(0, (155, 27, 0)), (3, (92, 16, 0)), (5.5, (102, 26, 1)), (8, (144, 52, 0)), (10.5, (117, 31, 1)),
                    (13, (185, 105, 3)), (15.5, (223, 141, 6)), (18, (238, 126, 6)), (20.5, (249, 167, 10)),
                    (23, (245, 147, 12)), (25.5, (240, 155, 7)), (28, (167, 86, 8)), (31, (101, 27, 5))],
        'inside': (101, 27, 5),
        'arm': (14, 32, 7), 'brace': None, 'plate': (34, 6, 1, 19),
    },
}
SPEC = SPECS[KIND]
pl.reset()
mats = {
    'Gold': fl.material('Gold', 'fx_gold'),
    'Embers': fl.material('Embers', 'embers'),
    'Flame': fl.flame_material('Flame', 'flame03'),
}


def lobe(name, angle, level):
    """A leaf lobe on scon200's lower bell: a squashed sphere standing out from the bell."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=(2, 1, 1)[level], radius=1.0)
    uv = bm.loops.layers.uv.verify()
    out = Vector((math.cos(angle), math.sin(angle), 0))
    side = Vector((-out.y, out.x, 0))
    for v in bm.verts:
        p = v.co.copy()
        # tear shape: wide at the top, narrowing to a point downward
        width = 3.8 * (0.45 + 0.55 * (p.z + 1) / 2)
        v.co = out * (u(18.2) + u(2.2) * p.x) + side * u(width) * p.y + Vector((0, 0, u(41) + u(5.5) * p.z))
    for face in bm.faces:
        for loop in face.loops:
            loop[uv].uv = (loop.vert.co.x * 4 + angle, loop.vert.co.z * 4)
    return pl.to_object(name, bm, mats['Gold'])


def handle(name, sign, level):
    """A C-shaped loop handle on one side (x = sign): a tube bent out from the body at 54 and back in at 42."""
    points = []
    steps = (8, 5, 3)[level]
    for i in range(steps + 1):
        t = math.pi / 2 - math.pi * i / steps
        points.append(Vector((sign * (u(20.5) + u(6.2) * math.cos(t)), 0, u(48) + u(6) * math.sin(t))))
    sides = (6, 4, 3)[level]
    return [pl.tube(f'{name}{i}', points[i], points[i + 1], u(1.6), u(1.6), sides, mats['Gold'], v_scale=4.0,
                    caps=False) for i in range(steps)]


def wall(level):
    arm_from, arm_to, arm_z = SPEC['arm']
    sides = (8, 6, 4)[level]
    parts = [pl.tube('arm', (0, u(arm_from), u(arm_z)), (0, u(arm_to), u(arm_z)), u(2.3), u(2.0), sides,
                     mats['Gold'], v_scale=4.0)]
    if SPEC['brace'] and level < 2:
        (y0, z0), (y1, z1) = SPEC['brace']
        parts.append(pl.tube('brace', (0, u(y0), u(z0)), (0, u(y1), u(z1)), u(1.4), u(1.4), sides, mats['Gold'],
                             v_scale=4.0))
    back, half, z0, z1 = SPEC['plate']
    parts.append(pl.box('plate', (0, u(back - 1.2), u((z0 + z1) / 2)), (u(half * 2), u(2.4), u(z1 - z0)),
                        mats['Gold'], uv_scale=3.0))
    if level == 0:
        parts.append(pl.box('boss', (0, u(back - 2.9), u(arm_z)), (u(7), u(1.2), u(7)), mats['Gold'], uv_scale=3.0))
    return parts


def build(level):
    profile = SPEC['profile']
    if level == 2:
        profile = profile[::2] + ([profile[-1]] if len(profile) % 2 == 0 else [])
    solids = [pl.lathe('body', [(u(r), u(z)) for r, z in profile], (20, 12, 8)[level], mats['Gold'], u_repeat=2.0,
                       v_scale=4.0)]
    if KIND == 'sconce2':
        for k in range(6 if level < 2 else 3):
            solids.append(lobe(f'lobe{k}', math.radians(-90 + k * (60 if level < 2 else 120)), level))
        solids += handle('handleL', -1, level) + handle('handleR', 1, level)
    if not FREE:
        solids += wall(level)
    fl.apply(solids)
    base, tip, width = SPEC['flame']
    whites = [pl.lathe('embers', [(u(r), u(z)) for r, z in SPEC['embers']], (12, 8, 6)[level], mats['Embers']),
              fl.flame_card('flame', mats['Flame'], 'flame03', base, tip, width)]
    return solids, whites


def gold(co, normal):
    radial = Vector((co.x, co.y, 0)).length
    if radial < SPEC['profile'][-4][0] + 0.2 and co.z > SPEC['profile'][-1][1] - 0.5 and normal.z > 0.2:
        return SPEC['inside']                  # inside the cup or opening
    if 'grooves' in SPEC and normal.z > 0.3 and co.z > 23.5:
        if any(abs(radial - g) < 0.3 for g in SPEC['grooves']):
            return (110, 30, 0)
        return (242, 165, 12)                  # the domed top's bright gold rings
    return fl.stops(SPEC['colours'], co.z)


fl.build_lods('Sconce' + KIND[-1] + ('Free' if FREE else ''), PROP, build, {'Gold': gold}, rays=(32, 20, 12),
              distance=15.0, strength=0.5)
