"""Shared Blender helpers of the projectile models: scene reset, textured materials, bmesh faces with UVs, export with
the material settings the Blender glTF exporter does not write (blended, additive, unlit, double-sided, flipbook,
emissive). Blender axes: -Y is the flight direction (glTF +Z), +Z up (glTF +Y), +X the side. Every model has its origin
at the projectile's centre; engine/models/projectiles.yml scales it to the binding's length along the flight."""
import json
import math
import os
import struct

import bmesh
import bpy
from mathutils import Vector, noise

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TEXTURES = os.path.join(HERE, 'textures')
SPRITES = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
# The flight sprites were archived once their models were installed (retire_sprites.py); item sprites stay.
SPRITE_DIRS = [SPRITES, os.path.join(REPO, 'assets_legacy', 'projectiles_x2_20261016')]


def sprite_path(name):
    return next((os.path.join(d, name) for d in SPRITE_DIRS if os.path.exists(os.path.join(d, name))),
                os.path.join(SPRITES, name))
WORK = os.path.join(HERE, 'work')


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def image(name, colorspace='sRGB'):
    loaded = bpy.data.images.load(os.path.join(TEXTURES, name), check_existing=True)
    loaded.colorspace_settings.name = colorspace
    return loaded


def material(name, texture, roughness=0.7, metallic=0.0, alpha=False, normal=False):
    """Principled material on textures/<texture>_basecolor.png (and <texture>_normal.png when normal)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    base = nt.nodes.new('ShaderNodeTexImage')
    base.image = image(f'{texture}_basecolor.png')
    nt.links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
    if alpha:
        nt.links.new(base.outputs['Alpha'], bsdf.inputs['Alpha'])
        m.surface_render_method = 'BLENDED'
    if normal:
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = image(f'{texture}_normal.png', 'Non-Color')
        mapping = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(tex.outputs['Color'], mapping.inputs['Color'])
        nt.links.new(mapping.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    return m


def add_face(bm, uv_layer, corners, material_index=0):
    """corners: [(co, uv)], counter-clockwise seen from outside."""
    verts = [bm.verts.new(co) for co, _ in corners]
    face = bm.faces.new(verts)
    face.material_index = material_index
    for loop, (_, texcoord) in zip(face.loops, corners):
        loop[uv_layer].uv = texcoord
    return face


def crossed_cards(bm, uv_layer, back, front, half_width, material_index):
    """Two cards through the flight axis (vertical and horizontal) from y = front to y = back (Blender Y; the flight
    runs toward -Y), each spanning one whole flipbook frame: u runs from the frame's left edge at the front to its
    right edge at the back (make_solid_textures.py lays the flames out that way), v across. The engine maps 0..1 into
    the current cell (model_static.sh)."""
    for vertical in (True, False):
        def corner(y, across, u, v):
            return ((0.0, y, across) if vertical else (across, y, 0.0), (u, v))
        add_face(bm, uv_layer, [corner(front, -half_width, 0.0, 0.0), corner(back, -half_width, 1.0, 0.0),
                                corner(back, half_width, 1.0, 1.0), corner(front, half_width, 0.0, 1.0)],
                 material_index)


def ico(radius, subdivisions):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=radius)
    return bm


def displace(bm, amplitude, scale, seed, axes=(1.0, 1.0, 1.0), octaves=3):
    """Push every vertex along its direction from the centre by fractal noise; axes squash the shape."""
    offset = Vector((seed * 7.31, seed * 3.17, seed * 5.53))
    for vertex in bm.verts:
        direction = vertex.co.normalized()
        value = noise.fractal(direction * scale + offset, 0.5, 2.0, octaves)
        vertex.co = direction * (vertex.co.length * (1.0 + amplitude * value))
        vertex.co = Vector((vertex.co.x * axes[0], vertex.co.y * axes[1], vertex.co.z * axes[2]))


def sphere_uv(bm, uv_layer, repeat=1.0):
    """Spherical UVs with the seam fixed per face (u wrapped near the face's first corner)."""
    for face in bm.faces:
        coordinates = []
        for loop in face.loops:
            co = loop.vert.co.normalized()
            u = 0.5 + math.atan2(co.y, co.x) / (2.0 * math.pi)
            v = 0.5 + math.asin(max(-1.0, min(1.0, co.z))) / math.pi
            coordinates.append([u, v])
        first = coordinates[0][0]
        for coordinate in coordinates:
            if coordinate[0] - first > 0.5:
                coordinate[0] -= 1.0
            elif first - coordinate[0] > 0.5:
                coordinate[0] += 1.0
        for loop, (u, v) in zip(face.loops, coordinates):
            loop[uv_layer].uv = (u * repeat, v * repeat * 0.5)


def cavity_colour(obj, power=1.5, floor=0.35):
    """COLOR_0 from each vertex's distance to the centre against its neighbours': hollows dark, bumps light (the
    engine multiplies the base colour by it), as the painted rocks' deep crevices."""
    mesh = obj.data
    neighbours = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        neighbours[a].append(b)
        neighbours[b].append(a)
    values = []
    for vertex in mesh.vertices:
        around = sum(mesh.vertices[i].co.length for i in neighbours[vertex.index]) / max(len(neighbours[vertex.index]), 1)
        values.append(vertex.co.length / max(around, 1e-6) - 1.0)
    spread = max(max(abs(v) for v in values), 1e-6)
    attribute = mesh.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    for index, value in enumerate(values):
        shade = max(floor, min(1.0, 0.8 + 0.5 * value / spread)) ** power
        attribute.data[index].color = (shade, shade, shade, 1.0)
    mesh.color_attributes.active_color = attribute


def box_uv(bm, uv_layer, tile):
    """Planar UVs per face along its dominant normal axis, tile metres per texture."""
    for face in bm.faces:
        n = face.normal
        axis = max(range(3), key=lambda i: abs(n[i]))
        for loop in face.loops:
            co = loop.vert.co
            a, b = [co[i] for i in range(3) if i != axis]
            loop[uv_layer].uv = (a / tile + 0.5, b / tile + 0.5)


def to_object(name, bm, materials, smooth_angle=None):
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE')
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for m in materials:
        mesh.materials.append(m)
    for polygon in mesh.polygons:
        polygon.use_smooth = smooth_angle is not None
    if smooth_angle is not None:
        with bpy.context.temp_override(active_object=obj, selected_objects=[obj]):
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth_angle))
    return obj


def fix_winding(obj):
    """Flip every closed loose piece whose signed volume is negative (inside-out: the engine culls its front)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    welded = bm.copy()
    bmesh.ops.remove_doubles(welded, verts=welded.verts, dist=1e-6)
    welded.faces.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    seen, flips = set(), []
    for face in welded.faces:
        if face.index in seen:
            continue
        stack, piece = [face], []
        seen.add(face.index)
        while stack:
            current = stack.pop()
            piece.append(current)
            for edge in current.edges:
                for other in edge.link_faces:
                    if other.index not in seen:
                        seen.add(other.index)
                        stack.append(other)
        closed = all(len(edge.link_faces) == 2 for current in piece for edge in current.edges)
        volume = sum(current.verts[0].co.dot(current.verts[1].co.cross(current.verts[2].co)) for current in piece
                     if len(current.verts) == 3) / 6.0
        if closed and volume < 0:
            flips.extend(current.index for current in piece)
    welded.free()
    if flips:
        bmesh.ops.reverse_faces(bm, faces=[bm.faces[i] for i in flips])
        bm.to_mesh(obj.data)
    bm.free()
    return len(flips)


def export(obj, name, settings=None):
    """Export work/<name>_export.glb; settings: material name -> {blend, additive, unlit, double, emissive,
    flipbook: [columns, rows, fps]}. Other materials are opaque and single-sided."""
    flipped = fix_winding(obj)
    if flipped:
        print('WINDING fixed', flipped, 'faces')
    os.makedirs(WORK, exist_ok=True)
    path = os.path.join(WORK, f'{name}_export.glb')
    for other in bpy.data.objects:
        other.select_set(other == obj)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                              export_normals=True, export_tangents=False, export_animations=False,
                              export_skins=False, export_morph=False, export_image_format='AUTO', export_apply=True,
                              export_vertex_color='ACTIVE' if obj.data.color_attributes else 'NONE')
    with open(path, 'rb') as handle:
        data = handle.read()
    json_length = struct.unpack_from('<I', data, 12)[0]
    document = json.loads(data[20:20 + json_length])
    binary = data[20 + json_length:]
    for entry in document.get('materials', []):
        spec = (settings or {}).get(entry['name'], {})
        entry.pop('alphaMode', None)
        entry['doubleSided'] = bool(spec.get('double'))
        if spec.get('blend'):
            entry['alphaMode'] = 'BLEND'
        if spec.get('unlit'):
            entry.setdefault('extensions', {})['KHR_materials_unlit'] = {}
            if 'KHR_materials_unlit' not in document.setdefault('extensionsUsed', []):
                document['extensionsUsed'].append('KHR_materials_unlit')
        if spec.get('emissive'):
            entry['emissiveFactor'] = list(spec['emissive'])
        extras = {}
        if spec.get('additive'):
            extras['openyamm_additive'] = True
        if spec.get('flipbook'):
            extras['openyamm_flipbook'] = list(spec['flipbook'])
        if extras:
            entry.setdefault('extras', {}).update(extras)
    encoded = json.dumps(document, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    with open(path, 'wb') as handle:
        handle.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(encoded) + len(binary)))
        handle.write(struct.pack('<II', len(encoded), 0x4E4F534A))
        handle.write(encoded)
        handle.write(binary)
    print('EXPORTED', name, 'triangles', len(obj.data.polygons), 'vertices', len(obj.data.vertices))
    return path
