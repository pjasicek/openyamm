"""MM6 iron wall torch `trchb00` (lit, 26 x 130 units) and `nwtrchnf` (unlit, 26 x 93): events toggle between them, so
both share one iron body. Proportions from the native x2 frames (world units): a foot ring 13 wide (0-5), a shaft 10
wide (5-30) and 9 wide (47-77), two collar rings 16 wide (29-33, 44-47) about a wall plate 26 wide (32-44.5) with four
bolt heads, and a fluted iron bowl 17 wide (78-92.6). The lit torch has an ember bed in the open bowl and the native
flame card above it (91-130, 30 wide: the shared flame02 flipbook, ../textures/FLAMES.md; the native flame is about 18
x 34 units); the unlit one has a closed, domed bowl topping out at 93. The shaft axis is the model origin; the plate's
back faces Blender +y (glTF -z) for mount: wall. The _free variants drop the wall plate and bolts (free_model).
Surface: the shared CC0 PBR set ../../torch_textures/textures/darkiron (glossy dark blue-grey forged iron with
copper-brown streaks; base colour, normal, metallic-roughness), tinted through COLOR_0 to the native band means.
Writes work/<prop>_export.glb. Usage: blender --background --python build_irontorch.py -- irontorch[_unlit][_free]"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'torch_textures', 'scripts'))
import tlib  # noqa: E402
import ttex  # noqa: E402

pl = tlib.pl
u = tlib.u
PROP = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'irontorch'
LIT = '_unlit' not in PROP
FREE = PROP.endswith('_free')
WALL = u(8.5)                                        # back of the wall plate behind the shaft axis

pl.reset()
mats = {'Iron': ttex.material('Iron', 'darkiron'), 'Bracket': ttex.material('Bracket', 'darkiron')}
if LIT:
    mats['Embers'] = tlib.material('Embers', 'embers')
    mats['Flame'] = tlib.flame_material()

# Native band means (sRGB) of the lit sprite, painted dark: lower shaft (55, 53, 64), upper shaft (72, 69, 86),
# bowl (72, 69, 81), collar and plate (50, 52, 64). The Iron target is the shaft's mean; shade() scales by height.
# The unlit sprite (nwtrchnf, lit by its sector) is painted a little lighter and rustier on its plate and collar.
TARGETS = {'Iron': (64, 62, 77), 'Bracket': (47, 49, 61)} if LIT else {'Iron': (66, 63, 77), 'Bracket': (62, 61, 70)}


def shade(name, co):
    if name != 'Iron':
        return 1.0
    if co.z < u(5.5):
        return 0.72
    if co.z < u(30):
        return 0.85 if LIT else 0.95
    return 1.2


def body(level):
    sides = (12, 8, 6)[level]
    profile = [(6.2, 0), (6.8, 1.5), (6.8, 4.0), (5.0, 5.5), (4.5, 77.0), (5.6, 78.5),
               (8.0, 80.0), (8.6, 82.5), (8.6, 88.0), (8.0, 91.0), (7.3, 92.6)]
    if LIT:
        profile += [(6.4, 92.6), (6.0, 90.6)]          # the bowl's inner lip around the ember bed
    else:
        profile += [(5.6, 93.0), (0.0, 93.0)]          # closed, domed cap
    if level == 2:
        profile = [(6.5, 0), (6.5, 4.0), (5.0, 5.5), (4.6, 77.0), (8.4, 81.0), (8.4, 90.0), (7.3, 92.6)]
        profile += [(6.0, 91.0)] if LIT else [(0.0, 93.0)]
    parts = [pl.lathe('body', [(u(r), u(z)) for r, z in profile], sides, mats['Iron'], u_repeat=2.0,
                      v_scale=4.0, cap_bottom=True)]
    if level < 2:
        tlib.flute(parts[0], sides // 2 if level else 6, 0.07, u(78.4), u(92.7))
    for z0, z1 in ((29.4, 32.6), (44.2, 47.2)):          # the two collar rings above and below the plate
        parts.append(pl.lathe('collar', [(u(4.8), u(z0)), (u(8.0), u(z0 + 0.5)), (u(8.0), u(z1 - 0.5)),
                                         (u(4.6), u(z1))], sides, mats['Bracket'], u_repeat=2.0, v_scale=4.0))
    if not FREE:
        parts.append(pl.box('plate', (0, WALL - u(2.2), u(38.3)), (u(26), u(4.4), u(12.5)), mats['Bracket'],
                            uv_scale=3.0))
        if level == 0:
            for x in (-1, 1):
                for z in (35.2, 41.4):
                    parts.append(pl.box(f'bolt{x}{z}', (x * u(9.5), WALL - u(4.9), u(z)), (u(3), u(1.2), u(3)),
                                        mats['Bracket'], uv_scale=3.0))
    for obj in parts:
        tlib.apply_all(obj)
    return pl.join(f'solid{level}', parts)


lods = []
base_name = ('IronTorch' if LIT else 'IronTorchUnlit') + ('Free' if FREE else '')
for level in range(3):
    solid = body(level)
    occlusion = pl.vertex_occlusion(solid, rays=(32, 20, 12)[level], distance=u(16), strength=0.5, floor=False)
    tints = tlib.tint(solid, TARGETS, shade)
    parts = [solid]
    if LIT:
        embers = pl.lathe('embers', [(u(6.2), u(90.6)), (u(3.5), u(91.8)), (u(0.01), u(92.3))], (10, 7, 5)[level],
                          mats['Embers'], u_repeat=2.0, v_scale=6.0)
        pl.white_colour(embers)
        parts.append(embers)
        flame = tlib.flame_card('flame', mats['Flame'], u(30), u(91), u(130))
        pl.white_colour(flame)
        parts.append(flame)
    name = base_name if level == 0 else f'{base_name}_LOD{level}'
    obj = pl.join(name, parts)
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'occlusion', round(occlusion, 3), 'tints', tints)
    lods.append(obj)
tlib.export(PROP, lods)
