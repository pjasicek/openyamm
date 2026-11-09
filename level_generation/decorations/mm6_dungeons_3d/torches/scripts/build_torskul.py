"""MM6 skull torch `torskul0` (2 placements, 72 x 179 units, 9 frames over 9/16 s, Lit): a dark bronze post with a
wall bracket like the iron torch's, carrying a crown of skulls around a fire cup. Proportions from the native x2
frames (world units): foot 15 wide (0-6), post 11 wide (6-62), the bracket plate 31 wide (37-54) behind the post, a
collar 20 wide (54-58), struts fanning out to the skulls (62-70), a front skull 28 wide (66-112) between two side
skulls turned outward (70-108; the crown is 72 wide), the fire cup 19 wide (98-110) sunk between the crowns and the
flame card above it (108.5-179, 26 wide; the shared flame02 flipbook, ../textures/FLAMES.md; the native flame is about
15 x 57). The skulls are painted lit from the fire above: bright orange on the crowns, nearly black at the jaws (a
height gradient on their COLOR_0). The post axis is the model origin; the plate's back faces Blender +y (glTF -z) for
mount: wall, level with the side skulls' backs. The _free variant drops the plate and adds a fourth skull at the back
(free_model).
The skulls are the bones batch's Meshy skull (../../bones/: Codex HD masters from the native skulls, Meshy Smart
Topology and retexture; ../../bones/work/skull_tex.blend), decimated per level, with its base colour remapped to the
sprite's fire-lit orange (../../bones/textures/skullfire_*, ../../bones/scripts/make_skullfire.py).
Writes work/<prop>_export.glb. Usage: blender --background --python build_torskul.py -- torskul[_free]"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tlib  # noqa: E402

BONES = os.path.join(tlib.HERE, '..', 'bones')
SKULL_TRIS = (700, 260, 100)          # per skull and level (the Meshy skull has 5329)
SKULL_WIDTH = 31.0                    # native front skull width (map units)
BOW = 22.0                            # degrees the skulls bow forward (the sprite shows faces and crowns)

pl = tlib.pl
u = tlib.u
PROP = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'torskul'
FREE = PROP.endswith('_free')
WALL = u(12.0)                                       # back of the plate (and of the side skulls)

pl.reset()


def skull_material():
    tlib.pl.TEX = os.path.join(BONES, 'textures')
    try:
        return tlib.pl.material('Skull', 'skullfire')
    finally:
        tlib.pl.TEX = tlib.dl.PROPS_TEXTURES


def loose_parts(bm):
    seen, parts = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        stack, part = [v], []
        seen.add(v)
        while stack:
            w = stack.pop(); part.append(w)
            for e in w.link_edges:
                o = e.other_vert(w)
                if o not in seen:
                    seen.add(o); stack.append(o)
        parts.append(part)
    return parts


def meshy_skull(level):
    """The Meshy skull, decimated to SKULL_TRIS[level], centred on its bounds, front turned to +y (the torch's skull
    space) and scaled to unit width."""
    with bpy.data.libraries.load(os.path.join(BONES, 'work', 'skull_tex.blend')) as (src, dst):
        dst.objects = ['skull']
    obj = dst.objects[0]
    obj.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.clear(); obj.data.materials.append(mats['Skull'])
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    if level:
        # Far skulls keep cranium and jaw, not the separate teeth.
        bm = bmesh.new(); bm.from_mesh(obj.data)
        small = [part for part in loose_parts(bm) if len(part) < 200]
        bmesh.ops.delete(bm, geom=[v for part in small for v in part], context='VERTS')
        bm.to_mesh(obj.data); bm.free()
    pl.decimate_to(obj, SKULL_TRIS[level])
    co = np.array([v.co[:] for v in obj.data.vertices])
    lo, hi = co.min(0), co.max(0)
    centre = Vector((lo + hi) / 2)
    width = hi[0] - lo[0]
    turn = Matrix.Rotation(math.pi, 4, 'Z')
    obj.data.transform(Matrix.Scale(1 / width, 4) @ turn @ Matrix.Translation(-centre))
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


mats = {'Bronze': tlib.material('Bronze', 'bronze'), 'Plate': tlib.material('Plate', 'bronze'),
        'Skull': None, 'Embers': tlib.material('Embers', 'embers'),
        'Flame': tlib.flame_material()}
mats['Skull'] = skull_material()

# Native means (sRGB): post (30, 17, 12), plate (49, 30, 20), struts and cup (20, 8, 3); the skulls by height
# (SKULL_LIGHT) from the crown's (250, 160, 90) to the jaws' (25, 6, 0); the Skull target is the brightest, so
# COLOR_0 only darkens the fire-lit skulllit texture (make_textures.py).
TARGETS = {'Bronze': (30, 17, 12), 'Plate': (50, 31, 21), 'Skull': (252, 168, 96)}
SKULL_LIGHT = [(66, (22, 6, 1)), (78, (30, 8, 1)), (86, (45, 14, 2)), (92, (85, 28, 6)), (97, (140, 55, 20)),
               (102, (215, 100, 48)), (106, (245, 150, 80)), (113, (252, 168, 96))]


def skull_light(z):
    """Linear factor (r, g, b) of the native skull colour at native height z against the Skull target."""
    heights = [h for h, _ in SKULL_LIGHT]
    colour = [np.interp(z, heights, [c[i] for _, c in SKULL_LIGHT]) for i in range(3)]
    return tuple(float(x) for x in tlib.srgb_to_linear(colour) / tlib.srgb_to_linear(TARGETS['Skull']))


def shade(name, co):
    if name == 'Skull':
        return skull_light(co.z / u(1))
    if name == 'Bronze' and co.z > u(59):
        return 0.55                                   # struts and the cup under the fire: nearly black
    return 1.0


def skulls(level):
    """(position, yaw, scale) of each skull: front, two side skulls turned out, and (free) one at the back."""
    front = (Vector((0, -u(8), u(88.0))), 0.0, 1.0)
    sides = [(Vector((x * u(21), -u(1.0), u(90.5))), x * math.radians(70), 0.93) for x in (-1, 1)]
    out = [front] + sides
    if FREE:
        out.append((Vector((0, u(8), u(91.0))), math.pi, 0.95))
    parts = []
    template = meshy_skull(level)
    for k, (position, yaw, scale) in enumerate(out):
        obj = template.copy(); obj.data = template.data.copy(); obj.name = f'skull{k}'
        bpy.context.scene.collection.objects.link(obj)
        # Skull space: front +y; the native front faces the viewer (Blender -y), hence the half turn; the skulls
        # bow BOW degrees, showing their crowns and faces to the front as the native sprite does.
        rotation = Euler((math.radians(-BOW), 0, math.pi + yaw), 'XYZ').to_matrix().to_4x4()
        size = Matrix.Scale(u(SKULL_WIDTH) * scale, 4)
        obj.matrix_world = Matrix.Translation(position) @ rotation @ size
        parts.append(obj)
    bpy.data.objects.remove(template)
    return parts


def body(level):
    sides = (12, 8, 6)[level]
    post = [(6.5, 0.0), (7.5, 1.5), (7.5, 4.5), (5.5, 6.0), (5.5, 54.0), (10.0, 54.6), (10.0, 57.4), (5.8, 58.2),
            (5.6, 62.0), (8.0, 64.0)]
    if level == 2:
        post = [(7.0, 0.0), (7.0, 4.5), (5.5, 6.0), (5.5, 54.0), (10.0, 55.0), (10.0, 57.4), (5.6, 62.0)]
    parts = [pl.lathe('post', [(u(r), u(z)) for r, z in post], sides, mats['Bronze'], u_repeat=2.0, v_scale=4.0,
                      cap_bottom=True, cap_top=True)]
    cup = [(5.0, 98.0), (8.6, 104.0), (9.5, 109.4), (8.4, 110.2), (7.6, 108.0)]
    parts.append(pl.lathe('cup', [(u(r), u(z)) for r, z in cup], sides, mats['Bronze'], u_repeat=2.0, v_scale=4.0))
    if level < 2:
        for k, (x, y, z) in enumerate(((0, -6, 71), (-16, 0, 75), (16, 0, 75))):
            parts.append(pl.tube(f'strut{k}', (0, 0, u(61)), (u(x), u(y), u(z)), u(2.4), u(2.0), (6, 4)[level],
                                 mats['Bronze'], v_scale=4.0))
    if not FREE:
        parts.append(pl.box('plate', (0, (u(5.0) + WALL) / 2, u(45.5)), (u(31), WALL - u(5.0), u(17)),
                            mats['Plate'], uv_scale=3.0))
        if level == 0:
            for x in (-1, 1):
                for z in (40.5, 50.5):
                    parts.append(pl.box(f'bolt{x}{z}', (x * u(11), u(4.4), u(z)), (u(3.2), u(1.4), u(3.2)),
                                        mats['Plate'], uv_scale=3.0))
    parts += skulls(level)
    for obj in parts:
        tlib.apply_all(obj)
    return pl.join(f'solid{level}', parts)


lods = []
base_name = 'TorSkul' + ('Free' if FREE else '')
for level in range(3):
    solid = body(level)
    occlusion = pl.vertex_occlusion(solid, rays=(32, 20, 12)[level], distance=u(18), strength=0.55, floor=False)
    tints = tlib.tint(solid, TARGETS, shade)
    embers = pl.lathe('embers', [(u(7.8), u(108.0)), (u(4.0), u(109.6)), (u(0.01), u(110.0))], (10, 7, 5)[level],
                      mats['Embers'], u_repeat=2.0, v_scale=6.0)
    pl.white_colour(embers)
    flame = tlib.flame_card('flame', mats['Flame'], u(26), u(108.5), u(179))
    pl.white_colour(flame)
    name = base_name if level == 0 else f'{base_name}_LOD{level}'
    obj = pl.join(name, [solid, embers, flame])
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'occlusion', round(occlusion, 3), 'tints', tints)
    lods.append(obj)
tlib.export(PROP, lods)
