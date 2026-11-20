"""MM6 wall torch `6torch01` (lit) and `torchnf` (unlit): a wooden torch held upright in an open iron ring clamp on an
arm from a wall plate. Proportions from the native sprite (x2 frames; world units): stick 7 wide from the ground to
60, the clamp (two flat hoops 21-23 wide at 28.5-32.5 and 40.5-43.2 joined by thin bars, teeth under the lower hoop)
at 26-43, a tarred head 12 wide at 60-74 and the flame card at 72-128 (the CC0 Unity Labs
Flame02 flipbook, textures/FLAMES.md). The torch axis is the model origin, where the flame card turns toward the
camera; the arm and plate reach back to the wall (Blender +y, glTF -z), so mount: wall hangs the plate on the nearest
wall face. The lit head carries a ring of unlit embers; the unlit one is charred. The _free variants keep only the
ring clamp (no arm or plate), for torches with no wall in reach (free_model), as the native sprite shows them.
Surfaces: the shared CC0 PBR sets of ../torch_textures/ (weathered wood stick, tar-soaked wound rag, rusty forged
iron; base colour, normal, metallic-roughness), tinted through COLOR_0 to the native sprite's measured colours.
Writes work/<prop>_export.glb.
Usage: blender --background --python build_torch.py -- torch|torchnf[_free]"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'torch_textures', 'scripts'))
import dungeon_lib as dl  # noqa: E402
import ttex  # noqa: E402

pl = dl.pl
u = dl.units
PROP = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'torch'
LIT = PROP in ('torch', 'torch_free')
FREE = PROP.endswith('_free')
FLAME_COLUMNS, FLAME_ROWS, FLAME_FPS = 16, 4, 30     # textures/FLAMES.md

pl.reset()
mats = {
    'Wood': ttex.material('Wood', 'torchwood'),
    'Iron': ttex.material('Iron', 'rustiron'),
    'Tar': ttex.material('Tar', 'torchrag'),
}
if LIT:
    mats['Embers'] = dl.material('Embers', 'embers')
    mats['Flame'] = dl.material('Flame', 'flame02', alpha=True,
                                extras={'openyamm_billboard': True,
                                        'openyamm_flipbook': [FLAME_COLUMNS, FLAME_ROWS, FLAME_FPS],
                                        'openyamm_specular': 0.0})

WALL = u(15.5)          # back of the wall plate behind the torch axis


def sharpen(obj, degrees=50):
    """Mark edges between faces meeting at more than `degrees` sharp (split normals on export)."""
    limit = math.radians(degrees)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    for edge in bm.edges:
        if len(edge.link_faces) == 2 and edge.calc_face_angle(0.0) > limit:
            edge.smooth = False
    bm.to_mesh(obj.data); bm.free()
    return obj


# The native clamp (x2 frames, world units): an open iron cage round the stick, like a spool. A flat hoop 22-23 wide
# at 28.5-32.5 and one 21 wide at 40.5-43.2, joined by thin vertical bars about 2 wide whose outer edges are 14 apart
# (radius 5.75 about the axis, the stick showing between them), and small teeth hanging under the lower hoop's rim.
CAGE_BARS = (6, 4, 0)          # bars per LOD; LOD2 keeps the old solid ring


def hoop(name, r_out, z0, z1, sides):
    """A flat iron washer round the stick (its inner edge is hidden inside the stick)."""
    return sharpen(pl.lathe(name, [(u(3.6), u(z0)), (u(r_out), u(z0)), (u(r_out), u(z1)), (u(3.6), u(z1))], sides,
                            mats['Iron'], u_repeat=2.0, v_scale=6.0))


def clamp(level):
    """The open ring clamp (two hoops, vertical bars and teeth; a solid ring at LOD2), an arm and a wall plate."""
    if level == 2:
        parts = [pl.lathe('ring', [(u(9.5), u(28)), (u(10.5), u(30)), (u(10.5), u(39)), (u(9.5), u(41))], 6,
                          mats['Iron'], u_repeat=2.0, v_scale=6.0, cap_top=True, cap_bottom=True)]
    else:
        sides = (10, 8)[level]
        parts = [hoop('hoop_low', 11.2, 28.5, 32.5, sides), hoop('hoop_high', 10.6, 40.5, 43.2, sides)]
        bars = CAGE_BARS[level]
        for k in range(bars):
            a = 2 * math.pi * k / bars
            centre = Vector((math.cos(a), math.sin(a), 0)) * u(5.75)
            parts.append(pl.tube(f'bar{k}', centre + Vector((0, 0, u(32))), centre + Vector((0, 0, u(41))),
                                 u(1.15), u(1.15), 4, mats['Iron'], v_scale=4.0, caps=False))
        if level == 0:
            for k in range(4):                     # the teeth under the lower hoop's rim
                a = math.pi / 4 + k * math.pi / 2
                centre = Vector((math.cos(a), math.sin(a), 0)) * u(9.8)
                parts.append(pl.box(f'tooth{k}', centre + Vector((0, 0, u(27.6))), (u(1.6), u(1.6), u(2.0)),
                                    mats['Iron'], uv_scale=3.0))
    if FREE:
        return parts
    parts.append(pl.box('arm', (0, u(12.5), u(33)), (u(4), u(6), u(3.5)), mats['Iron'], uv_scale=3.0))
    parts.append(pl.box('plate', (0, WALL - u(1), u(34)), (u(12), u(2), u(20)), mats['Iron'], uv_scale=3.0))
    if level == 0:
        for x, z in ((-1, 1), (1, 1), (-1, -1), (1, -1)):        # rivet heads on the plate's face
            parts.append(pl.box(f'rivet{x}{z}', (x * u(4), WALL - u(2.3), u(34) + z * u(7)), (u(2), u(0.8), u(2)),
                                mats['Iron'], uv_scale=3.0))
    return parts


def torch(level):
    sides = (10, 7, 5)[level]
    parts = [pl.tube('stick', (0, 0, 0), (0, 0, u(61)), u(3.4), u(4.4), sides, mats['Wood'], v_scale=3.0)]
    # The tarred head: rag wound around the stick's top, widest near the top.
    parts.append(pl.lathe('head', [(u(4.4), u(58)), (u(5.8), u(62)), (u(6.2), u(70)), (u(5.4), u(73.5)),
                                   (u(3.0 if LIT else 2.0), u(74))], sides, mats['Tar'], u_repeat=2.0, v_scale=5.0,
                          cap_top=True))
    parts += clamp(level)
    for obj in parts:
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return pl.join(f'solid{level}', parts)


# Native sprite means (sRGB) that COLOR_0 brings each material's displayed mean to (ttex.tint: linear target over the
# texture mean and the material's mean occlusion). The lit torch is self-lit and painted at night tones: stick
# (44, 22, 9), clamp (36, 19, 10), head (38, 21, 10). The unlit torchnf sprite is lit by its sector and painted
# lighter: stick (66, 41, 19) to (68, 45, 24), clamp (63, 47, 32), head (67, 44, 24) charring toward its top.
TARGETS = ({'Wood': (44, 22, 9), 'Iron': (36, 19, 10), 'Tar': (38, 21, 10)} if LIT else
           {'Wood': (67, 43, 21), 'Iron': (63, 47, 32), 'Tar': (72, 47, 26)})


def shade(name, co):
    """The unlit sprite's stick is painted lighter above the clamp than below it; its head chars toward the top."""
    if LIT:
        return 1.0
    if name == 'Tar':
        return 1.0 - 0.3 * max(0.0, (co.z - u(66)) / u(8))
    if name == 'Wood':
        return 1.3 if co.z > u(42) else 0.88
    return 1.0


def embers(level):
    """A glowing ring where the flame meets the head (unlit)."""
    return pl.lathe('embers', [(u(5.6), u(71.5)), (u(4.6), u(73.8)), (u(2.5), u(74.4))], (10, 7, 5)[level],
                    mats['Embers'], u_repeat=2.0, v_scale=6.0)


def flame():
    """The flame card in the model's x/up plane over the lower 80 % of a flipbook frame (textures/FLAMES.md): the
    native flame's 17 x 48 units from the head top at 74, so 28 x 56 units with the flame's flat base just above the
    card's bottom edge."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    corners = ((-u(14), 0, u(72)), (u(14), 0, u(72)), (u(14), 0, u(128)), (-u(14), 0, u(128)))
    face = bm.faces.new([bm.verts.new(c) for c in corners])
    for loop, (s, t) in zip(face.loops, ((0, 0), (1, 0), (1, 0.8), (0, 0.8))):
        loop[uv].uv = (s, t)
    return pl.to_object('flame', bm, mats['Flame'], smooth=False)


lods = []
base_name = ('Torch' if LIT else 'TorchUnlit') + ('Free' if FREE else '')
for level in range(3):
    solid = torch(level)
    occlusion = pl.vertex_occlusion(solid, rays=(32, 20, 12)[level], distance=u(20), strength=0.5, floor=False)
    tints = ttex.tint(solid, TARGETS, shade)
    parts = [solid]
    if LIT:
        glow = embers(level); pl.white_colour(glow); parts.append(glow)
        card = flame(); pl.white_colour(card); parts.append(card)
    name = base_name if level == 0 else f'{base_name}_LOD{level}'
    obj = pl.join(name, parts)
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(occlusion, 3), 'tints', tints)
    lods.append(obj)
work = os.path.join(dl.HERE, 'work'); os.makedirs(work, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, f'{PROP}.blend'))
pl.export(lods, os.path.join(work, f'{PROP}_export.glb'))
