"""Arrows -> work/<variant>_export.glb, installed as engine/models/projectile_<variant>.glb:
- arrow (object 545, sprite `arrow` / arrowa);
- fire_arrow (object 550, sprite `frarw` / frarwa-f): the same arrow with the fire arrow's fletching, and its flames.

Traced from the restored side-view sprites (frame 2, 400 x 120 at x2; tip at the right): a hexagonal shaft, a ferrule
taper into a flat broadhead (blade plane vertical, as the side view shows its full width), and three vanes (one up,
two at +-120 degrees) whose outline is the top feather's contour. Every UV lands on sprite pixels of
textures/<variant>_basecolor.png (make_textures.py): the shaft samples the shaft strip (the painted band's mean per
column, so its detail runs along it), the head and vanes are projected from the side view. Material Arrow: opaque.
The fire arrow adds two crossed cards (vertical and horizontal, through the shaft) over its front half, material
Fire: the painted flames as a flipbook (textures/fire_arrow_flame_basecolor.png, 2 x 4 cells), blended additively,
unlit and double-sided, so the flame streams back along the arrow whatever its heading.
No LODs (about 100 triangles). The model points along Blender -Y (glTF +Z) with its origin at its centre;
engine/models/projectiles.yml scales it to the sprite's length.
Usage: blender --background --python build_arrow.py -- <arrow|fire_arrow>"""
import json
import math
import os
import struct
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SPRITES = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
# The flight sprites were archived once their models were installed (retire_sprites.py); item sprites stay.
SPRITE_DIRS = [SPRITES, os.path.join(REPO, 'assets_legacy', 'projectiles_x2_20261016')]


def sprite_path(name):
    return next((os.path.join(d, name) for d in SPRITE_DIRS if os.path.exists(os.path.join(d, name))),
                os.path.join(SPRITES, name))
WORK = os.path.join(HERE, 'work')
# variant: (side-view sprite whose top feather outlines the vanes, vane columns, flames)
VARIANTS = {
    'arrow': ('arrowa2_p338.png', (10.0, 108.0), False),
    'fire_arrow': ('frarwa2_p5.png', (4.0, 100.0), True),
}
# Flame cards: the flipbook cell's sprite window (make_textures.py FLAME_WINDOW, FLAME_CELL), 2 x 4 cells.
FLAME_X0, FLAME_ROW0, FLAME_W, FLAME_H = 160.0, -4.0, 256.0, 128.0
FLAME_GRID = (2, 4)
FLAME_FPS = 12.0
TEX_W, TEX_H = 512, 128

# Sprite pixel geometry (x2 frame): shaft centre row, tail and tip columns.
ROW = 88.0
TAIL_X, TIP_X = 4.0, 395.0
CENTRE_X = 0.5 * (TAIL_X + TIP_X)
SHAFT_R = 6.5                      # px; the painted shaft spans rows 81-95
SHAFT_STRIP_ROW = 124.0            # the shaft strip below the sprite (make_textures.py)
FERRULE_X0, FERRULE_X1, FERRULE_R = 349.0, 362.0, 3.5
HEAD_BACK_X, BARB_X, WAIST_X = 356.0, 354.0, 372.0
BARB_HALF, HEAD_THICK = 15.5, 2.5
VANE_SEGMENTS = 5
VANE_THICK = 0.35
PX = 0.01                          # Blender metres per sprite pixel (the binding sets the in-game length)


def to_blender(x, side, up):
    """Sprite column x (tail to tip), sideways and upward offsets in px -> Blender coordinates (-Y forward)."""
    return (side * PX, -(x - CENTRE_X) * PX, up * PX)


def uv(x, row):
    return (x / TEX_W, 1.0 - row / TEX_H)


def top_contour(sprite, columns):
    """Top row of the upper feather's opaque pixels per sprite column, above the shaft."""
    image = bpy.data.images.load(sprite_path(sprite), check_existing=True)
    width, height = image.size
    pixels = np.array(image.pixels[:], np.float32).reshape(height, width, 4)[::-1]
    alpha = pixels[:, :, 3] >= 0.5
    tops = {}
    for x in range(int(columns[0]), int(columns[1]) + 1):
        column = np.nonzero(alpha[:int(ROW - SHAFT_R), x])[0]
        tops[x] = float(column.min()) if len(column) else ROW - SHAFT_R
    return tops


def add_face(bm, uv_layer, corners):
    """corners: [(co, uv)], counter-clockwise seen from outside."""
    verts = [bm.verts.new(co) for co, _ in corners]
    face = bm.faces.new(verts)
    for loop, (_, texcoord) in zip(face.loops, corners):
        loop[uv_layer].uv = texcoord
    return face


def shaft(bm, uv_layer, sides=6):
    """Hexagonal shaft from the tail to the ferrule, the ferrule taper and a tail cap; one shared ring per station."""
    stations = [(TAIL_X, SHAFT_R), (FERRULE_X0, SHAFT_R), (FERRULE_X1, FERRULE_R)]
    rings = []
    for x, radius in stations:
        ring = []
        for k in range(sides):
            angle = 2.0 * math.pi * k / sides
            co = to_blender(x, radius * math.cos(angle), radius * math.sin(angle))
            ring.append((bm.verts.new(co), uv(x, SHAFT_STRIP_ROW)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(sides):
            n = (k + 1) % sides
            face = bm.faces.new((a[k][0], a[n][0], b[n][0], b[k][0]))
            for loop, (_, texcoord) in zip(face.loops, (a[k], a[n], b[n], b[k])):
                loop[uv_layer].uv = texcoord
    # Tail cap (nock end), a quad strip so no vertex fans out; the painted tail pixels are dark, so it takes the
    # shaft colour.
    tail = rings[0]
    for indices in ((0, 2, 1), (0, 3, 2), (0, 5, 3), (3, 5, 4)):
        face = bm.faces.new([tail[i][0] for i in indices])
        for loop in face.loops:
            loop[uv_layer].uv = uv(200.0, SHAFT_STRIP_ROW)
    # The ferrule's narrow end is hidden inside the head: no cap.


def head(bm, uv_layer):
    """Flat broadhead: tip, barbs up and down, a waist ring sideways and a back point, projected from the side."""
    def point(x, side, up):
        return (to_blender(x, side, up), uv(x, ROW - up))
    tip = point(TIP_X, 0.0, 0.0)
    top = point(BARB_X, 0.0, BARB_HALF)
    bottom = point(BARB_X, 0.0, -BARB_HALF)
    left = point(WAIST_X, -HEAD_THICK, 0.0)
    right = point(WAIST_X, HEAD_THICK, 0.0)
    back = point(HEAD_BACK_X, 0.0, 0.0)
    for a, b in ((top, right), (right, bottom), (bottom, left), (left, top)):
        add_face(bm, uv_layer, [tip, b, a])
        add_face(bm, uv_layer, [back, a, b])


def vanes(bm, uv_layer, tops, columns):
    """Three vanes, each two faces back to back (a hair apart), outlined by the upper feather's contour."""
    xs = np.linspace(columns[0], columns[1], VANE_SEGMENTS + 1)
    heights = []
    for i, x in enumerate(xs):
        top = tops[int(round(x))]
        # Close the outline at both ends onto the shaft.
        heights.append(0.0 if i in (0, VANE_SEGMENTS) else max(ROW - SHAFT_R - top, 0.0))
    for angle in (90.0, 210.0, 330.0):
        radians = math.radians(angle)
        out = (math.cos(radians), math.sin(radians))
        normal = (-math.sin(radians), math.cos(radians))
        for side in (1.0, -1.0):
            offset = side * VANE_THICK * 0.5
            strip = []
            for x, h in zip(xs, heights):
                inner = SHAFT_R * 0.8
                outer = SHAFT_R + h
                row_inner, row_outer = ROW - SHAFT_R, ROW - SHAFT_R - h
                for radius, row in ((inner, row_inner), (outer, row_outer)):
                    co = to_blender(x, radius * out[0] + offset * normal[0], radius * out[1] + offset * normal[1])
                    strip.append((co, uv(x, row)))
            for i in range(VANE_SEGMENTS):
                a, b, c, d = strip[2 * i], strip[2 * i + 2], strip[2 * i + 3], strip[2 * i + 1]
                quad = [a, b, c, d] if side > 0 else [a, d, c, b]
                if heights[i] == 0.0 and heights[i + 1] == 0.0:
                    continue
                add_face(bm, uv_layer, quad)


def flames(bm, uv_layer):
    """Two crossed cards through the shaft. Their UVs span one whole flipbook frame (0..1); the engine's static
    model shader maps them into the current cell (model_static.sh), so Blender shows the whole atlas on them."""
    x0, x1 = FLAME_X0, FLAME_X0 + FLAME_W
    up0, up1 = ROW - FLAME_ROW0, ROW - FLAME_ROW0 - FLAME_H
    for vertical in (True, False):
        def corner(x, up, u, v):
            return (to_blender(x, 0.0 if vertical else up, up if vertical else 0.0), (u, v))
        add_face(bm, uv_layer, [corner(x0, up1, 0.0, 0.0), corner(x1, up1, 1.0, 0.0), corner(x1, up0, 1.0, 1.0),
                                corner(x0, up0, 0.0, 1.0)])


def material(name, texture, alpha=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(HERE, 'textures', f'{texture}_basecolor.png'), check_existing=True)
    tex.image.colorspace_settings.name = 'sRGB'
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    if alpha:
        nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        m.surface_render_method = 'BLENDED'
    bsdf.inputs['Roughness'].default_value = 0.72
    bsdf.inputs['Metallic'].default_value = 0.0
    return m


def finish(path):
    """Fire: blended additively, unlit, double-sided, a flipbook. The Blender exporter writes none of these."""
    with open(path, 'rb') as handle:
        data = handle.read()
    json_length = struct.unpack_from('<I', data, 12)[0]
    document = json.loads(data[20:20 + json_length])
    binary = data[20 + json_length:]
    for material_entry in document.get('materials', []):
        if material_entry['name'] == 'Fire':
            material_entry['alphaMode'] = 'BLEND'
            material_entry['doubleSided'] = True
            material_entry.setdefault('extensions', {})['KHR_materials_unlit'] = {}
            material_entry.setdefault('extras', {}).update(
                {'openyamm_additive': True, 'openyamm_flipbook': [FLAME_GRID[0], FLAME_GRID[1], FLAME_FPS]})
            if 'KHR_materials_unlit' not in document.setdefault('extensionsUsed', []):
                document['extensionsUsed'].append('KHR_materials_unlit')
        else:
            material_entry.pop('alphaMode', None)
            material_entry['doubleSided'] = False
    encoded = json.dumps(document, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    with open(path, 'wb') as handle:
        handle.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(encoded) + len(binary)))
        handle.write(struct.pack('<II', len(encoded), 0x4E4F534A))
        handle.write(encoded)
        handle.write(binary)


def main():
    variant = sys.argv[sys.argv.index('--') + 1]
    sprite, columns, has_flames = VARIANTS[variant]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    shaft(bm, uv_layer)
    head(bm, uv_layer)
    vanes(bm, uv_layer, top_contour(sprite, columns), columns)
    body_faces = len(bm.faces)
    if has_flames:
        flames(bm, uv_layer)
        bm.faces.ensure_lookup_table()
        for face in bm.faces[body_faces:]:
            face.material_index = 1
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE')
    mesh = bpy.data.meshes.new('Arrow')
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new('Arrow', mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(material('Arrow', variant))
    if has_flames:
        mesh.materials.append(material('Fire', 'fire_arrow_flame', alpha=True))
    # Smooth round the shaft; the flat head and vanes get hard edges from their own unshared vertices.
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj]):
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
    print('ARROW', variant, 'triangles', len(mesh.polygons), 'vertices', len(mesh.vertices))
    os.makedirs(WORK, exist_ok=True)
    path = os.path.join(WORK, f'{variant}_export.glb')
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                              export_normals=True, export_tangents=False, export_animations=False,
                              export_skins=False, export_morph=False, export_image_format='AUTO',
                              export_apply=True)
    finish(path)
    print('EXPORTED', path)


main()
