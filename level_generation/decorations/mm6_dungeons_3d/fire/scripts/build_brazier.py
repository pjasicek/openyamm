"""MM6 hanging brazier: `brazir2f` (unlit, one frame; 111 placements) and `brzier00` (lit, six frames; the events
light a brazier by switching its sprite to brzier00). One geometry for both, traced from brazir2f (x2 pixels at
0.5 units, bowl bottom at its row 293): a hemispherical iron bowl with a rolled lip (48 units wide, 25 high), three
chains from the lip (one in front, two behind at 120 degrees) up to a ring at 64 units, and one chain from the ring
up to the ceiling end at 146.5 units (the bounds top, so a swing would pivot there). Links are 6 x 3 oval tori at
LOD0 (12 + 3 x 7 links, about 6.9 units each, 4.8 units wide with a heavy 1.7-unit wire like the sprite's chain); LOD1/LOD2 replace each chain
with a thin tube. The lit model adds a glowing ember bed (lit ember texture plus emission, Glow) in the bowl and the flame card (the shared flame02
flipbook) with its base in the embers at 16 units and its tip at 72, where the lit sprite's flame ends (scaled
146.5 / 282 units per x2 pixel). COLOR_0: the unlit sprite's near-black iron, or the lit sprite's colours:
chains and bowl warmed by the fire toward the flame, the bowl's inside glowing orange.
Writes work/<prop>_export.glb. Usage: blender --background --python build_brazier.py -- brazier|brazier_unlit"""
import math
import os
import sys

from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fire_lib as fl  # noqa: E402

pl, u = fl.pl, fl.u
PROP = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'brazier'
LIT = PROP == 'brazier'
TOP = 146.5
RING_Z = 64.0
LIP = (23.0, 24.5)                 # chain ends on the lip: radius, height
CHAIN_ANGLES = (-90, 30, 150)      # degrees; -90 faces the camera (Blender -y)

pl.reset()
mats = {'Iron': fl.material('Iron', 'ph_ironpit'), 'Chain': fl.material('Chain', 'ph_ironpit')}
if LIT:
    # The glowing bed: ember texture, lit, plus a constant orange emission flickering with the fire.
    mats['Glow'] = fl.glow_material('Glow', 'ph_ember', (170, 78, 26), pulse=(0.18, 0.75))
    mats['Flame'] = fl.flame_material('Flame', 'flame02')

BOWL = [(0, 0), (8, 3), (14.5, 6.5), (19.5, 11.5), (22.5, 17), (24.3, 22), (24.3, 24.5), (22.5, 25), (19, 17),
        (11, 10.5), (0, 8.5)]


def chains(level):
    ring_bottom = Vector((0, 0, u(RING_Z - 2.5)))
    ends = [Vector((math.cos(math.radians(a)) * u(LIP[0]), math.sin(math.radians(a)) * u(LIP[0]), u(LIP[1])))
            for a in CHAIN_ANGLES]
    if level == 0:
        parts = fl.chain('main', mats['Chain'], (0, 0, u(RING_Z + 2.5)), (0, 0, u(TOP - 1.0)), u(6.9), u(4.8),
                         u(1.7), 6, 3)
        parts.append(fl.link('ring', mats['Chain'], (0, 0, u(RING_Z)), (0, 0, 1), u(6.5), u(6.5), u(1.8), 6, 3, 0))
        for k, end in enumerate(ends):
            parts += fl.chain(f'branch{k}', mats['Chain'], ring_bottom, end, u(6.4), u(4.6), u(1.6), 6, 3, k)
        return parts
    sides = (0, 4, 3)[level]
    parts = [pl.tube('main', (0, 0, u(RING_Z)), (0, 0, u(TOP)), u(1.5), u(1.5), sides, mats['Chain'],
                     v_scale=3.0, caps=False)]
    for k, end in enumerate(ends):
        parts.append(pl.tube(f'branch{k}', ring_bottom + Vector((0, 0, u(2.5))), end, u(1.3), u(1.3), sides,
                             mats['Chain'], v_scale=3.0, caps=False))
    return parts


def build(level):
    segments = (12, 10, 7)[level]
    profile = BOWL if level < 2 else [BOWL[0], BOWL[2], BOWL[4], BOWL[6], BOWL[8], BOWL[10]]
    solids = [pl.lathe('bowl', [(u(r), u(z)) for r, z in profile], segments, mats['Iron'], u_repeat=6.0,
                       v_scale=3.3)] + chains(level)
    whites = []
    if LIT:
        # The ember bed, rising up the inside of the bowl just within its wall (the lit sprite's glowing inside).
        bed = [(0, 14), (10, 13.2), (18.6, 16.4), (21.7, 22.4), (22.1, 24.6)]
        bed = bed if level < 2 else [bed[0], bed[2], bed[4]]
        whites.append(pl.lathe('embers', [(u(r), u(z)) for r, z in bed], segments, mats['Glow'], u_repeat=1.5,
                               v_scale=1.5))
        whites.append(fl.flame_card('flame', mats['Flame'], 'flame02', 16.0, 72.0, 50.0))
    return solids, whites


def inside(co, normal):
    """The bowl's inner surface and lip top (normals up or toward the axis)."""
    radial = Vector((co.x, co.y, 0))
    return normal.z > 0.6 or (radial.length > 1e-6 and radial.normalized().dot(normal) < -0.2)


if LIT:
    CHAIN = [(0, (60, 34, 18)), (70, (56, 32, 16)), (110, (48, 28, 20)), (128, (50, 27, 18)), (138, (14, 12, 13)),
             (150, (12, 11, 12))]
    # Measured on brzier00 by 3-unit band (pixels darker than the fire): blue-lit bottom, near-black flank,
    # fire-reddened upper wall, dark lip.
    OUTER = [(0, (53, 55, 91)), (3, (32, 31, 43)), (7, (37, 27, 26)), (10.5, (48, 30, 24)), (13.5, (61, 37, 29)),
             (17, (93, 38, 27)), (20.5, (97, 39, 30)), (23, (62, 30, 24)), (25, (48, 26, 21))]
    INNER = (120, 70, 35)
else:
    CHAIN = [(0, (8, 8, 9)), (150, (8, 8, 9))]
    OUTER = [(0, (4, 3, 4)), (2.5, (6, 5, 5)), (5.5, (10, 8, 8)), (8.5, (18, 16, 16)), (11.5, (24, 21, 22)),
             (15.5, (26, 24, 23)), (19.5, (12, 11, 11)), (21.5, (7, 7, 7)), (25, (7, 7, 7))]
    INNER = (12, 11, 11)
COLOURS = {
    'Chain': lambda co, n: fl.stops(CHAIN, co.z),
    'Iron': lambda co, n: INNER if inside(co, n) else fl.stops(OUTER, co.z),
    # The bed's lit albedo stays dim (charred crust); the emission carries the glow whatever the room light.
    'Glow': lambda co, n: fl.stops([(0, (160, 70, 24)), (15, (150, 64, 22)), (24.6, (120, 50, 20))], co.z),
}
fl.build_lods('Brazier' if LIT else 'BrazierUnlit', PROP, build, COLOURS, rays=(32, 20, 12), distance=20.0,
              strength=0.5, merge={'Chain': 'Iron'})
