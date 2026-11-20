"""MM8 dungeon chandeliers (six frames in 12/16 s, light 96; the frames change only the candle flames):

chandelier1 = `dec08` (15 placements: d40 13, d27 2; 106 x 127 units), silvery wrought iron traced from dec08a: a
chain of five links (84-127, the pivot), a hanger ring, two pairs of thorn horns rising from the crown, four heart
scrolls framing the tall centre candle (cup 42, candle to 57, flame to 69), two long arms to outer candles at +-47.5
(cups 40-45, candles to 60) and four short arms to inner candles (front pair lower, back pair higher, as the
sprite's perspective shows them), a spindle with a bulb and four scroll legs curling down to finial points (0).

chandelier2 = `dec27` (9 placements: d09 5, d06 4; 123 x 127 units), dark iron and red-brown wood traced from
dec27a: a twisted chain (84-127), a crown (66-82), four scalloped straps down to four square wooden posts with iron
bands (20-50), eight radial iron arms at 31 ending in cups with thick white candles (40-55, flames to 63), pendant
finials under the posts and the diagonal cups, and a central pendant.

Surfaces: CC0 Poly Haven derived sets (`iron_grey`, `iron_dark`, `wood`, `wax`), COLOR_0 tinted to the sprites.
Flames (2026-10-16 "pretty lights" pass): `candleglow`, the shared Flame03 flipbook re-centred with a soft halo baked
round each frame, drawn additive (`openyamm_additive`) with a smooth random flicker (`openyamm_flicker`). Every
off-axis candle has its own card billboard (`openyamm_billboard: card`, turning about its own centre, one primitive
per candle at LOD0/LOD1); dec08's centre flame turns about the model axis; LOD2 shares one material of crossed fixed
cards. Each candle plays its own flipbook frame offset. The bounds top is the chain's top: `swing` pivots there.
Writes work/<prop>_export.glb. Usage: blender --background --python build_chandelier.py -- chandelier1|chandelier2"""
import math
import os
import sys

from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as al  # noqa: E402

pl, u = al.pl, al.u
prop = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'chandelier1'
pl.reset()


def polar(r, angle, z):
    a = math.radians(angle)
    return Vector((u(r * math.sin(a)), u(-r * math.cos(a)), u(z)))   # angle 0 = front (-y), 90 = right (+x)


def curve(name, points, angle, radius, level, mat, samples=(10, 5, 3), sides=(5, 4, 3), taper=None):
    """A bar through (r, z) points in the vertical plane at `angle`."""
    path = [polar(r, angle, z) for r, z in points]
    if level < 2 and len(path) > 2:
        path = al.bezier(path, samples[level])
    elif len(path) > 2:
        path = [path[0], path[len(path) // 2], path[-1]]
    radii = [u(radius) * (1 - (taper or 0) * i / (len(path) - 1)) for i in range(len(path))]
    return al.sweep(name, path, radii, sides[level], mat, v_scale=3.0)


def lathe_at(name, profile, segments, mat, centre=(0, 0, 0), step=1):
    pts = profile[::step] + ([profile[-1]] if (len(profile) - 1) % step else [])
    return pl.lathe(name, [(u(r), u(z)) for r, z in pts], segments, mat, u_repeat=1.0, v_scale=4.0,
                    centre=(centre[0], centre[1], 0))


def candle_set(k, r, angle, cup_z, top_z, wax_r, cup_r, level, mats, flame_tip, solids, whites, flame_w=5.5,
               cup_mat='Iron', cup=None, segments=(10, 7, 5)):
    c = polar(r, angle, 0)
    seg = segments[level]
    if cup is None:
        cup = [(1.2, cup_z - 4.0), (cup_r * 0.55, cup_z - 2.6), (cup_r * 0.95, cup_z - 0.8), (cup_r, cup_z),
               (cup_r * 0.75, cup_z + 0.2), (wax_r, cup_z)]
    if level > 0:
        cup = cup[:-3:2] + cup[-3:] if len(cup) > 6 else [cup[0], cup[2], cup[3], cup[5]]
    solids.append(lathe_at(f'cup{k}', cup, seg, mats[cup_mat], (c.x, c.y)))
    wax = [(wax_r, cup_z), (wax_r, top_z - 0.8), (wax_r * 0.75, top_z), (0.0, top_z - 0.3)]
    if level > 0:
        wax = [(wax_r, cup_z), (wax_r, top_z), (0.0, top_z)]
    solids.append(lathe_at(f'wax{k}', wax, seg, mats['Wax'], (c.x, c.y)))
    x, y = c.x * al.dl.UNITS_PER_METRE, c.y * al.dl.UNITS_PER_METRE
    flame = flame_w * 0.6                          # the flame's own width (flame_w was the Flame03 card width)
    if level < 2:
        # Its own camera-facing card (pivot per primitive) with the candle's halo baked in, added to the scene.
        whites.append(al.candle_card(f'Candle{k}', x, y, top_z + 0.3, flame_tip, flame, 13 * k + 3))
    else:
        whites += al.flame_star(f'far{k}', mats['CandleFar'], 'candleglow', top_z + 0.3, flame_tip,
                                flame / al.FLAME_SPAN['candleglow'], x, y, cards=2, frame_offset=13 * k + 3,
                                yaw=45.0 + angle)


def build_dec08(level):
    mats = MATS
    solids, whites = [], []
    step = (1, 2, 3)[level]
    # Chain, hanger ring and crown.
    if level < 2:
        solids += al.chain('link', mats['Iron'], (0, 0, u(84.0)), (0, 0, u(127.0 - 2.8)), u(9.0), u(11.4), u(2.8),
                           (8, 6)[level], (4, 3)[level])
    else:
        solids.append(pl.tube('chain', (0, 0, u(84.0)), (0, 0, u(127.0)), u(3.0), u(3.0), 4, mats['Iron']))
    crown = [(0.0, 70.0), (3.0, 70.4), (5.2, 72.6), (5.4, 75.4), (3.6, 78.0), (2.2, 80.0), (3.4, 82.0),
             (2.0, 84.6), (0.0, 85.0)]
    solids.append(lathe_at('crown', crown, (10, 8, 5)[level], mats['Iron'], step=step))
    # Thorn horns (diagonals, so the front view shows a pair) and heart scrolls round the centre candle.
    for k, angle in enumerate((45, 135, 225, 315)):
        solids.append(curve(f'horn{k}', [(3.0, 72.0), (7.0, 74.5), (12.5, 78.5), (17.0 * 1.25, 82.0)], angle, 3.4,
                            level, mats['Iron'], samples=(6, 4, 3), sides=(4, 3, 3), taper=0.85))
        solids.append(curve(f'heart{k}', [(2.5, 73.0), (10.0, 76.0), (19.0, 73.5), (25.5, 66.0), (27.5, 58.0),
                                          (24.0, 50.0), (14.0, 44.0), (5.0, 41.0)], angle, 2.9, level, mats['Iron']))
    # Spindle with a bulb, the centre cup.
    spindle = [(0.0, 12.0), (2.6, 13.0), (3.0, 18.0), (6.4, 23.0), (8.4, 29.0), (7.0, 35.0), (3.2, 38.0),
               (2.4, 40.4), (9.5, 41.2), (10.2, 42.6), (8.0, 43.4), (2.4, 43.0)]
    solids.append(lathe_at('spindle', spindle, (12, 8, 6)[level], mats['Iron'], step=step))
    # Scroll legs curling down to finial points (the bounds bottom).
    for k, angle in enumerate((30, 90, 150, 210, 270, 330)):
        solids.append(curve(f'leg{k}', [(4.5, 31.0), (14.0, 28.0), (21.0, 21.0), (22.5, 13.0), (19.0, 6.5),
                                        (14.5, 3.4), (12.0, 1.2)], angle, 3.0, level, mats['Iron'], taper=0.6))
    # Inner C-curls filling the lower body (the sprite's dense dark mass of scrolls).
    if level < 2:
        for k, angle in enumerate((0, 120, 240)):
            solids.append(curve(f'curl{k}', [(3.0, 28.0), (9.0, 26.0), (13.0, 20.0), (11.0, 13.0), (6.0, 11.0),
                                             (5.0, 15.0)], angle, 2.4, level, mats['Iron'], samples=(8, 5, 3)))
    # Arms: outer pair to the sides, inner four (front lower, back higher).
    outer = [(4.0, 31.0), (14.0, 28.5), (27.0, 29.5), (37.0, 33.0), (44.0, 36.6), (47.5, 39.6)]
    for k, angle in enumerate((90, 270)):
        solids.append(curve(f'outer{k}', outer, angle, 2.8, level, mats['Iron']))
        candle_set(k, 47.5, angle, 45.0, 60.0, 2.6, 5.4, level, mats, 68.5, solids, whites)
    for k, (angle, cup_z, top_z) in enumerate(((35, 26.0, 41.0), (325, 26.0, 41.0), (145, 32.0, 50.0),
                                               (215, 32.0, 50.0))):
        path = [(4.0, 30.0), (11.0, 25.0), (18.0, cup_z - 6.5), (24.0, cup_z - 5.0), (26.0, cup_z - 4.0)]
        solids.append(curve(f'inner{k}', path, angle, 2.6, level, mats['Iron']))
        candle_set(k + 2, 26.0, angle, cup_z, top_z, 2.3, 4.6, level, mats, top_z + 8.0, solids, whites)
    # Centre candle on the axis: camera-facing flame and a halo.
    solids.append(lathe_at('centre', [(2.6, 43.0), (2.6, 56.2), (2.0, 57.0), (0.0, 56.8)], (10, 8, 6)[level],
                           mats['Wax']))
    whites.append(al.flame_card('flame', mats['Flame'], 'candleglow', 57.3, 69.5, 6.5 * 0.6 / al.FLAME_SPAN['candleglow'],
                                v_top=0.85))
    al.apply(solids)
    return solids, whites


def build_dec27(level):
    mats = MATS
    solids, whites = [], []
    step = (1, 2, 3)[level]
    if level < 2:
        solids += al.chain('link', mats['Iron'], (0, 0, u(82.0)), (0, 0, u(127.0 - 1.8)), u(6.6), u(6.4), u(1.8),
                           (6, 6)[level], (4, 3)[level])
    else:
        solids.append(pl.tube('chain', (0, 0, u(82.0)), (0, 0, u(127.0)), u(2.4), u(2.4), 4, mats['Iron']))
    crown = [(0.0, 64.0), (4.0, 64.4), (9.0, 66.4), (11.6, 69.8), (12.0, 72.0), (10.0, 75.0), (9.6, 78.6),
             (6.0, 80.4), (3.0, 81.6), (2.2, 83.0), (0.0, 83.4)]
    solids.append(lathe_at('crown', crown, (12, 8, 6)[level], mats['Iron'], step=step))
    # Hub, central pendant.
    hub = [(0.0, 14.0), (1.0, 15.0), (2.4, 20.0), (4.0, 25.0), (6.0, 28.8), (6.4, 33.4), (4.0, 35.0), (2.2, 40.0),
           (2.2, 64.4)]
    solids.append(lathe_at('hub', hub, (10, 8, 5)[level], mats['Iron'], step=step))
    for k, angle in enumerate((45, 135, 225, 315)):
        # Wooden post with iron bands and a pendant finial under it; a scalloped strap down from the crown.
        c = polar(22.0, angle, 0)
        post = pl.box(f'post{k}', (0, 0, u(35.0)), (u(11.0), u(11.0), u(30.0)), mats['Wood'], uv_scale=4.0)
        post.rotation_euler = (0, 0, math.radians(-angle))
        post.location = (c.x, c.y, 0)
        solids.append(post)
        for z in ((23.5, 46.5) if level < 2 else (35.0,)):
            band = pl.box(f'band{k}_{z}', (0, 0, u(z)), (u(12.2), u(12.2), u(2.8)), mats['Iron'], uv_scale=4.0)
            band.rotation_euler = (0, 0, math.radians(-angle))
            band.location = (c.x, c.y, 0)
            solids.append(band)
        solids.append(lathe_at(f'finial{k}', [(0.0, 0.0), (1.6, 3.0), (3.6, 9.0), (4.4, 14.0), (3.0, 18.0),
                                              (4.6, 20.0)], (8, 5, 4)[level], mats['Iron'], (c.x, c.y), step=step))
        strap = [(8.0, 76.0), (13.0, 74.0), (18.0, 68.5), (21.0, 61.0), (23.0, 54.0), (24.0, 50.0)]
        solids.append(curve(f'strap{k}', strap, angle, 2.4, level, mats['Iron'], sides=(4, 4, 3)))
        if level == 0:
            for j, (r, z) in enumerate(((12.5, 72.5), (17.0, 66.0), (20.0, 58.5))):
                p = polar(r + 2.0, angle, z)
                solids.append(pl.tube(f'curl{k}{j}', p - Vector((0, 0, u(3.0))), p + Vector((0, 0, u(3.0))),
                                      u(2.6), u(0.6), 5, mats['Iron']))
    # Eight radial arms at 31 to the candle cups; pendants under the diagonal cups.
    for k in range(8):
        angle = 22.5 + 45.0 * k
        solids.append(pl.tube(f'arm{k}', polar(3.0, angle, 31.0), polar(54.0, angle, 31.0), u(1.9), u(1.9),
                              (5, 4, 3)[level], mats['Iron']))
        cup = [(0.0, 29.0), (3.0, 29.6), (5.4, 32.4), (6.2, 36.0), (6.8, 39.6), (5.4, 40.2), (4.2, 40.0)]
        candle_set(k, 54.0, angle, 40.0, 55.0, 4.2, 6.6, level, mats, 63.5, solids, whites, flame_w=6.0, cup=cup,
                   segments=(8, 5, 4))
        if level < 2:
            a, b = polar(42.0, angle, 31.0), polar(42.0, angle + 45.0, 31.0)
            solids.append(pl.tube(f'ring{k}', a, b, u(1.5), u(1.5), (4, 3)[level], mats['Iron']))
        if k % 2 == 0 and level < 2:
            solids.append(lathe_at(f'drop{k}', [(0.0, 10.0), (1.6, 13.0), (3.0, 20.0), (2.4, 26.0), (2.0, 30.0)],
                                   6, mats['Iron'], (polar(36.0, angle, 0).x, polar(36.0, angle, 0).y)))
            solids.append(curve(f'dropbar{k}', [(36.0, 29.0), (36.0, 31.0)], angle, 1.6, level, mats['Iron']))
    al.apply(solids)
    return solids, whites


CANDLE_FLICKER = (0.3, 8.0)
if prop == 'chandelier1':
    MATS = {
        'Iron': al.material('Iron', 'iron_grey', extras={'openyamm_specular': 1.0}),
        'Wax': al.material('Wax', 'wax', extras={'openyamm_specular': 0.4}),
        'Flame': al.flame_material('Flame', 'candleglow', additive=True, flicker=CANDLE_FLICKER, emission=(26, 10, 2)),
        'CandleFar': al.flame_material('CandleFar', 'candleglow', billboard=False, additive=True,
                                       flicker=CANDLE_FLICKER, emission=(26, 10, 2)),
    }
    COLOURS = {
        # dec08a: bright grey scrolls and chain (90-105), dark spindle and legs (46-66).
        'Iron': lambda co, n: (70, 68, 74) if co.z > 40 or math.hypot(co.x, co.y) > 30 else (40, 38, 44),
        'Wax': lambda co, n: al.stops([(20, (176, 168, 146)), (45, (200, 194, 172)), (60, (226, 220, 196))], co.z)}
    al.build_lods('Chandelier', 'chandelier1', build_dec08, COLOURS, distance=14.0, strength=0.45,
                  last=('Candle', 'Flame'))
else:
    MATS = {
        'Iron': al.material('Iron', 'iron_dark', extras={'openyamm_specular': 0.6}),
        'Wood': al.material('Wood', 'wood', extras={'openyamm_specular': 0.3}),
        'Wax': al.material('Wax', 'wax', extras={'openyamm_specular': 0.4}),
        'CandleFar': al.flame_material('CandleFar', 'candleglow', billboard=False, additive=True,
                                       flicker=CANDLE_FLICKER, emission=(26, 10, 2)),
    }
    COLOURS = {
        # dec27a: blue-grey dark iron (40-65, chain 37-61), the posts' red-brown wood (~140, 64, 34), white candles.
        'Iron': lambda co, n: (60, 60, 66) if co.z > 25 else (40, 40, 48),
        'Wood': (140, 66, 36),
        'Wax': lambda co, n: al.stops([(40, (196, 196, 194)), (55, (236, 236, 232))], co.z)}
    al.build_lods('Chandelier', 'chandelier2', build_dec27, COLOURS, distance=14.0, strength=0.45,
                  last=('Candle',))
