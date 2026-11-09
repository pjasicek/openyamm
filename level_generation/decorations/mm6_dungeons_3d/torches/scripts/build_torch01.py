"""MM6 wall torch `torch01` (75 placements, 128 x 128 units, 8 frames over 1 s, light 512): a thin wooden torch held
in a carved wooden holder block on the wall. Proportions from the native x2 frames (world units): a stick 5 wide from
the ground to 44 and 6 wide above the block, a turned collar 7 wide under the block (40-44), the block 24 wide
(44-54), a cloth wrap 9-13 wide (68-82) and the flame card above it (81-128, 28 wide; the shared flame02 flipbook,
../textures/FLAMES.md; the native flame is about 17 x 42 units). The stick axis is the model origin; the block reaches
back to the wall (Blender +y, glTF -z) for mount: wall. The _free variant keeps a shallow block centred on the stick
(free_model).
Surfaces: the shared CC0 PBR sets of ../../torch_textures/ (weathered wood for the stick and holder, a tar-soaked
wound rag for the wrap; base colour, normal, metallic-roughness), tinted through COLOR_0 to the native band means.
Writes work/<prop>_export.glb. Usage: blender --background --python build_torch01.py -- torch01[_free]"""
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'torch_textures', 'scripts'))
import tlib  # noqa: E402
import ttex  # noqa: E402

pl = tlib.pl
u = tlib.u
PROP = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'torch01'
FREE = PROP.endswith('_free')
WALL = u(8.0)                                        # back of the holder block behind the stick axis

pl.reset()
mats = {'Wood': ttex.material('Wood', 'torchwood'), 'Holder': ttex.material('Holder', 'torchwood'),
        'Wrap': ttex.material('Wrap', 'torchrag'), 'Embers': tlib.material('Embers', 'embers'),
        'Flame': tlib.flame_material()}

# Native means (sRGB): stick (68, 31, 16) below the block and (98, 45, 29) above it, block (49, 27, 18), collar (39,
# 20, 14), wrap (85, 45, 28) charring to (100, 36, 5) under the flame.
TARGETS = {'Wood': (60, 27, 14), 'Holder': (52, 29, 19), 'Wrap': (84, 44, 26)}


def shade(name, co):
    if name == 'Wood' and u(40) < co.z < u(44):            # the darker turned collar under the block
        return 0.6
    if name == 'Wood' and co.z > u(44):                    # the stick above the block is painted lighter
        return 3.6                                         # (and is occluded by the block and the wrap)
    if name == 'Wrap':
        return 1.0 - 0.45 * max(0.0, (co.z - u(78)) / u(4.5))
    return 1.0


def block(level):
    """The holder: a chamfered block (rounded front edges at LOD0) with a raised rim on its face."""
    back = WALL if not FREE else u(4.5)
    front = -u(4.5)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    centre = Vector((0, (front + back) / 2, u(49)))
    size = Vector((u(24), back - front, u(10)))
    for v in bm.verts:
        v.co = Vector((v.co.x * size.x, v.co.y * size.y, v.co.z * size.z)) + centre
    if level < 2:
        edges = [e for e in bm.edges if all(v.co.y < centre.y for v in e.verts) or
                 all(abs(v.co.x) > u(11.9) for v in e.verts)]
        bmesh.ops.bevel(bm, geom=edges, offset=u(1.4), segments=2 if level == 0 else 1, affect='EDGES',
                        profile=0.5)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        for loop in f.loops:
            co = loop.vert.co
            loop[uv].uv = ((co.x, co.z) if abs(n.y) > 0.5 else (co.y, co.z) if abs(n.x) > 0.5 else (co.x, co.y))
            loop[uv].uv = (loop[uv].uv[0] * 3.0, loop[uv].uv[1] * 3.0)
    return pl.to_object('block', bm, mats['Holder'], smooth=False)


def torch(level):
    sides = (12, 8, 6)[level]
    stick = [(2.6, 0), (2.6, 39.5), (3.6, 40.5), (3.6, 43.5), (3.0, 44.5), (3.0, 68.0)]
    if level == 2:
        stick = [(2.6, 0), (3.0, 68.0)]
    parts = [pl.lathe('stick', [(u(r), u(z)) for r, z in stick], sides, mats['Wood'], u_repeat=1.0, v_scale=3.0,
                      cap_bottom=True)]
    wrap = [(3.0, 67.5), (4.4, 69.0), (4.6, 73.0), (5.0, 77.5), (6.3, 80.5), (5.6, 82.3), (3.2, 82.8)]
    if level == 2:
        wrap = [(3.0, 67.5), (4.6, 70.0), (6.2, 80.5), (3.2, 82.8)]
    parts.append(pl.lathe('wrap', [(u(r), u(z)) for r, z in wrap], sides, mats['Wrap'], u_repeat=2.0, v_scale=5.0))
    if level < 2:
        tlib.flute(parts[-1], sides // 2 + 1, 0.06, u(68.5), u(80.6))     # the wound rag's lumps
    parts.append(block(level))
    for obj in parts:
        tlib.apply_all(obj)
    return pl.join(f'solid{level}', parts)


lods = []
base_name = 'Torch01' + ('Free' if FREE else '')
for level in range(3):
    solid = torch(level)
    occlusion = pl.vertex_occlusion(solid, rays=(32, 20, 12)[level], distance=u(16), strength=0.5, floor=False)
    tints = tlib.tint(solid, TARGETS, shade)
    embers = pl.lathe('embers', [(u(5.9), u(80.8)), (u(4.6), u(82.4)), (u(2.0), u(83.2))], (10, 7, 5)[level],
                      mats['Embers'], u_repeat=2.0, v_scale=6.0)
    pl.white_colour(embers)
    flame = tlib.flame_card('flame', mats['Flame'], u(28), u(81), u(128))
    pl.white_colour(flame)
    name = base_name if level == 0 else f'{base_name}_LOD{level}'
    obj = pl.join(name, [solid, embers, flame])
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'occlusion', round(occlusion, 3), 'tints', tints)
    lods.append(obj)
tlib.export(PROP, lods)
