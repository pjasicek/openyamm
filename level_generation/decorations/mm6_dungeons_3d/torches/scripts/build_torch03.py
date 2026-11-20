"""MM6 hanging brazier `torch03` (6 placements, 128 x 128 units, 8 frames over 1 s, light 512): a wide iron dish with
a turned finial below, a heap of glowing coals (lit ember texture plus emission), four chains to a gold ring and one chain up to the ceiling.
Proportions from the native x2 frames (world units above the sprite's bottom; the model starts at the finial's foot,
9.5, so the binding takes z_offset 9.5): finial 13 wide (9.5-20), dish underside 27-62 wide (20-32), rim 67 wide
(32-37), coal heap 35 wide (35-46), the ring at 100-112 and the ceiling chain to 128 (the bounds top, the pivot a
swing binding would use). The fire is the shared flame02 flipbook (../textures/FLAMES.md) on a camera-facing card 60
wide at 38-101 (the native fire is about 37 x 53 units over the coals). Chains are crossed cut-out ribbons
(textures/t3_chain_*: the link strip with brass detail and relief).
Writes work/torch03_export.glb. Usage: blender --background --python build_torch03.py -- torch03"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tlib  # noqa: E402

pl = tlib.pl
PROP = 'torch03'
FOOT = 9.5                                           # native height of the finial's foot (model z = 0)


def u(native_height):
    """Native units above the sprite's bottom to model metres above the finial's foot (for heights)."""
    return tlib.u(native_height - FOOT)


w = tlib.u                                           # widths and radii

pl.reset()
mats = {'Dish': tlib.material('Dish', 't3_iron'), 'Under': tlib.material('Under', 't3_paint'),
        'Rim': tlib.material('Rim', 't3_brass'), 'Gold': tlib.material('Gold', 't3_brass'),
        'Chain': tlib.material('Chain', 't3_chain', alpha=True),
        'Glow': tlib.material('Glow', 't3_ember', extras={'openyamm_pulse': [0.15, 1.0]}),
        'Flame': tlib.flame_material()}
# The coal dome glows: its lit ember texture plus a constant emission (glTF emissiveFactor, not scaled by COLOR_0).
GLOW = (165, 60, 18)
_bsdf = next(n for n in mats['Glow'].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
_bsdf.inputs['Emission Color'].default_value = tuple(float(c) for c in tlib.srgb_to_linear(GLOW)) + (1.0,)
_bsdf.inputs['Emission Strength'].default_value = 1.0

# Native means (sRGB): finial (70, 45, 44), dish underside painted blue (50, 55, 107), the dish's dark flank (34, 24,
# 24) (band mean of the underside (39, 35, 52)), rim side (44, 45, 67) and its fire-lit top (139, 92, 67), coals (170,
# 82, 36), gold ring (190, 122, 46), chains (139, 89, 50); the coal heap is about 34 wide inside a dark dish floor.
# The coal dome's lit albedo is kept dimmer than the native mean: the emission brings it up to the sprite's glow.
TARGETS = {'Dish': (40, 30, 32), 'Under': (50, 55, 107), 'Rim': (80, 64, 62), 'Gold': (160, 104, 44),
           'Chain': (140, 90, 50), 'Glow': (105, 40, 13)}
HUB = 104.0                                          # native height of the ring's centre
RING = 5.0                                           # its radius
RIM = 31.0                                           # chain attachment radius on the rim


def shade(name, co):
    if name == 'Rim':
        return (0.45, 0.6, 0.95) if co.z < u(34.5) else (1.25, 1.0, 0.8)     # blue-grey side, fire-lit top
    if name == 'Dish' and co.z < u(20.5):
        return 2.4                                                          # the finial is lighter
    if name == 'Dish' and co.z > u(35.0):
        return 0.35                                                         # the dark dish floor
    return 1.0


def torus(name, centre, major, minor, segments, sides, mat):
    """A ring in the x/z plane (the hub link)."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    rings = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        axis = Vector((math.cos(a), 0, math.sin(a)))
        ring = []
        for j in range(sides):
            b = 2 * math.pi * j / sides
            p = Vector(centre) + axis * (major + minor * math.cos(b)) + Vector((0, minor * math.sin(b), 0))
            ring.append(bm.verts.new(p))
        rings.append(ring)
    for i in range(segments):
        for j in range(sides):
            a, b = rings[i], rings[(i + 1) % segments]
            f = bm.faces.new((a[j], b[j], b[(j + 1) % sides], a[(j + 1) % sides]))
            for loop, st in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv].uv = (st[0] / segments * 4, st[1] / sides)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, True)


def chain(name, a, b, crossed):
    """Chain from a to b: one or two crossed cut-out ribbons, links about 6 units long."""
    length = (Vector(b) - Vector(a)).length / w(1)
    repeat = length / 48.0                            # 8 links of 6 units per texture strip
    parts = [tlib.strip(name, mats['Chain'], a, b, w(7), 0.0, repeat)]
    if crossed:
        parts.append(tlib.strip(name + 'x', mats['Chain'], a, b, w(7), math.pi / 2, repeat))
    return parts


def brazier(level):
    sides = (20, 12, 8)[level]
    finial = [(0.0, 9.5), (4.6, 9.8), (6.4, 12.0), (6.2, 14.8), (4.2, 17.4), (4.6, 19.6)]
    under = [(4.6, 19.6), (13.0, 21.6), (19.5, 23.6), (23.0, 26.0), (25.0, 28.6), (29.5, 31.0), (31.5, 32.4)]
    rim = [(31.5, 32.4), (33.6, 33.0), (33.6, 34.6), (32.4, 35.6), (29.0, 35.8)]
    inside = [(29.0, 35.8), (27.0, 35.2), (17.0, 35.4)]
    coals = [(17.5, 35.2), (15.5, 38.8), (11.5, 42.4), (6.0, 45.2), (0.0, 46.0)]
    if level == 2:
        finial = [(0.0, 9.5), (6.3, 12.0), (4.4, 17.6), (4.6, 19.6)]
        under = [(4.6, 19.6), (19.5, 23.6), (25.0, 28.6), (31.5, 32.4)]
        rim = [(31.5, 32.4), (33.6, 34.0), (29.0, 35.8)]
        inside = [(29.0, 35.8), (17.0, 35.4)]
        coals = [(17.5, 35.2), (12.0, 42.2), (0.0, 46.0)]
    parts = [pl.lathe('finial', [(w(r), u(z)) for r, z in finial], max(sides // 2, 6), mats['Dish'],
                      u_repeat=2.0, v_scale=4.0),
             pl.lathe('under', [(w(r), u(z)) for r, z in under], sides, mats['Under'], u_repeat=8.0, v_scale=3.0),
             pl.lathe('rim', [(w(r), u(z)) for r, z in rim], sides, mats['Rim'], u_repeat=8.0, v_scale=4.0),
             pl.lathe('inside', [(w(r), u(z)) for r, z in inside], sides, mats['Dish'], u_repeat=6.0, v_scale=3.0)]
    for obj in parts:
        tlib.apply_all(obj)
    solid = pl.join(f'solid{level}', parts)
    heap = pl.lathe('coals', [(w(r), u(z)) for r, z in coals], sides, mats['Glow'], u_repeat=2.0, v_scale=4.0)
    if level < 2:
        tlib.flute(heap, 5, 0.08, u(36.0), u(45.5))                    # a lumpy heap, not a smooth dome
    hub_parts = [torus('hub', (0, 0, u(HUB)), w(RING), w(1.0), (10, 8, 6)[level], (4, 4, 3)[level], mats['Gold'])]
    top = Vector((0, 0, u(HUB + RING)))
    hub_parts += chain('up', top, (0, 0, u(128.0)), level < 2)
    bottom = Vector((0, 0, u(HUB - RING)))
    for k in range(4):
        a = k * math.pi / 2
        end = (w(RIM) * math.cos(a), w(RIM) * math.sin(a), u(36.5))
        start = bottom + Vector((math.cos(a), math.sin(a), 0)) * w(1.5)
        hub_parts += chain(f'chain{k}', start, end, level < 2)
    return solid, heap, hub_parts


lods = []
for level in range(3):
    solid, heap, hub_parts = brazier(level)
    occlusion = pl.vertex_occlusion(solid, rays=(32, 20, 12)[level], distance=w(14), strength=0.5, floor=False)
    tints = tlib.tint(solid, TARGETS, shade)
    pl.white_colour(heap); tlib.tint(heap, TARGETS)
    hardware = pl.join(f'hardware{level}', hub_parts)
    pl.white_colour(hardware); tlib.tint(hardware, TARGETS)
    flame = tlib.flame_card('flame', mats['Flame'], w(60), u(38), u(101))
    pl.white_colour(flame)
    name = 'Torch03' if level == 0 else f'Torch03_LOD{level}'
    obj = pl.join(name, [solid, heap, hardware, flame])
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'occlusion', round(occlusion, 3), 'tints', tints)
    lods.append(obj)
tlib.export(PROP, lods)
