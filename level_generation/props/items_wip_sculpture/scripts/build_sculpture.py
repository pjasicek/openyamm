"""Assigned simple sculptures; closed low-poly volumes with explicit UVs and per-material PBR.

Run in an isolated Blender: --background --python build_sculpture.py -- [icon ...].
Painted square material tiles belong in textures/<bone|egg|horn|enamel>.png; signet.png is a face template.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / 'work' / 'blender'
DESIGNS = json.loads((HERE / 'designs.json').read_text())


def material(name, colour, roughness, metallic=0, tile=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*colour, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if tile:
        image = bpy.data.images.load(str(HERE / 'textures' / (tile + '.png')), check_existing=True)
        tex = m.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = image
        m.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        mr_path = HERE / 'textures' / (tile + '_mr.png')
        if mr_path.exists():
            tex = m.node_tree.nodes.new('ShaderNodeTexImage')
            tex.image = bpy.data.images.load(str(mr_path), check_existing=True)
            tex.image.colorspace_settings.name = 'Non-Color'
            channels = m.node_tree.nodes.new('ShaderNodeSeparateColor')
            m.node_tree.links.new(tex.outputs['Color'], channels.inputs['Color'])
            m.node_tree.links.new(channels.outputs['Green'], bsdf.inputs['Roughness'])
            m.node_tree.links.new(channels.outputs['Blue'], bsdf.inputs['Metallic'])
        normal_path = HERE / 'textures' / (tile + '_normal.png')
        if normal_path.exists():
            tex = m.node_tree.nodes.new('ShaderNodeTexImage')
            tex.image = bpy.data.images.load(str(normal_path), check_existing=True)
            tex.image.colorspace_settings.name = 'Non-Color'
            node = m.node_tree.nodes.new('ShaderNodeNormalMap')
            m.node_tree.links.new(tex.outputs['Color'], node.inputs['Color'])
            m.node_tree.links.new(node.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def surface(name, rings, mat, sides=16, smooth=True, closed=False):
    """Loft ordered closed cross sections; UV seam is the underside, end caps use separate UV space."""
    vertices = [tuple(p) for ring in rings for p in ring]
    faces, uvs = [], []
    sections = len(rings) if closed else len(rings) - 1
    for j in range(sections):
        for i in range(sides):
            nxt = (i + 1) % sides
            following = (j + 1) % len(rings)
            faces.append((j * sides + i, j * sides + nxt, following * sides + nxt, following * sides + i))
            u0, u1 = 0.02 + 0.96 * i / sides, 0.02 + 0.96 * (i + 1) / sides
            v0, v1 = 0.02 + 0.96 * j / sections, 0.02 + 0.96 * (j + 1) / sections
            uvs.append(((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
    # A strip triangulates the caps without a high-valence centre vertex.
    for end in (() if closed else (0, len(rings) - 1)):
        order = list(range(sides))
        for i in range(sides - 2):
            tri = (order.pop(0), order[0], order[-1]) if i % 2 == 0 else (order.pop(), order[0], order[-1])
            faces.append(tuple(end * sides + k for k in tri))
            uvs.append(tuple((0.25 + 0.5 * end / (len(rings) - 1) + math.cos(k * math.tau / sides) * 0.1,
                              0.9 + math.sin(k * math.tau / sides) * 0.08) for k in tri))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    layer = mesh.uv_layers.new(name='UVMap')
    for poly, coords in zip(mesh.polygons, uvs):
        poly.use_smooth = smooth and len(poly.vertices) == 4
        for loop, uv in zip(poly.loop_indices, coords):
            layer.data[loop].uv = uv
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges), name
    assert bm.calc_volume(signed=True) > 0, name
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def tube(name, path, radii, mat, sides=8, closed=False):
    rings = []
    for j, centre in enumerate(path):
        previous = (j - 1) % len(path) if closed else max(j - 1, 0)
        following = (j + 1) % len(path) if closed else min(j + 1, len(path) - 1)
        tangent = (Vector(path[following]) - Vector(path[previous])).normalized()
        right = tangent.cross(Vector((0, 0, 1)))
        if right.length < 0.01:
            right = tangent.cross(Vector((1, 0, 0)))
        right.normalize()
        up = tangent.cross(right).normalized()
        rings.append([Vector(centre) + radii[j] * (math.cos(i * math.tau / sides) * right
                                                  + math.sin(i * math.tau / sides) * up) for i in range(sides)])
    return surface(name, rings, mat, sides, closed=closed)


def ellipsoid(name, radii, mat, centre=(0, 0, 0), sides=20, rows=12):
    rings = []
    for j in range(rows + 1):
        angle = 0.025 + (math.pi - 0.05) * j / rows
        rings.append([(centre[0] + radii[0] * math.sin(angle) * math.cos(i * math.tau / sides),
                       centre[1] + radii[1] * math.cos(angle),
                       centre[2] + radii[2] * math.sin(angle) * math.sin(i * math.tau / sides))
                      for i in range(sides)])
    return surface(name, rings, mat, sides)


def icon_volume(icon, mat, depth=0.8):
    """Use the face-on bone/horn outline for a round-section loft, never as its colour projection."""
    image = bpy.data.images.load(str(HERE.parents[2] / 'assets_dev/engine/icons_x2' / (icon + '.png')))
    width, height = image.size
    pixels = np.asarray(image.pixels[:]).reshape(height, width, 4)
    ys, xs = np.nonzero(pixels[:, :, 3] >= 0.5)
    points = np.column_stack((xs, ys)).astype(float)
    points -= points.mean(axis=0)
    _, axes = np.linalg.eigh(np.cov(points.T))
    along = axes[:, 1]
    if along[np.argmax(np.abs(along))] < 0:
        along = -along
    across = np.array((along[1], -along[0]))
    lengths, widths = points @ along, points @ across
    low, high = lengths.min(), lengths.max()
    scale = 2 / (high - low)
    rings = []
    for j in range(25):
        y = low + (high - low) * j / 24
        selected = widths[np.abs(lengths - y) <= max(1, (high - low) / 70)]
        assert len(selected), (icon, j)
        centre = (selected.min() + selected.max()) / 2 * scale
        radius = max(0.008, (selected.max() - selected.min() + 1) * scale / 2)
        if j in (0, 24):
            radius = min(radius, 0.025)
        rings.append([(centre + radius * math.cos(a), (y - (low + high) / 2) * scale,
                       radius * depth * math.sin(a)) for a in [i * math.tau / 12 for i in range(12)]])
    return surface(icon, rings, mat, 12)


def bone(icon):
    tile = 'bone_dark' if icon == 'item305' else ('bone_pale' if icon == '7item271' else 'bone')
    mat = material('weathered_bone', (0.6, 0.48, 0.3), 0.8, tile=tile)
    icon_volume('7item271' if icon == '7item271' else '6thybone', mat)


def horn():
    mat = material('keratin', (0.5, 0.33, 0.1), 0.62, tile='horn')
    icon_volume('item308', mat, depth=0.9)


def egg():
    obj = ellipsoid('dragon_egg', (0.44, 0.65, 0.44), material('eggshell', (0.6, 0.56, 0.4), 0.85, tile='egg'))
    for v in obj.data.vertices:
        taper = 1 - 0.2 * v.co.y / 0.65
        v.co.x *= taper
        v.co.z *= taper


def gem(icon):
    colours = {'item270': (0.9, 0.28, 0.025), 'item271': (0.31, 0.32, 0.65),
               'item272': (0.58, 0.6, 0.57), 'item273': (0.06, 0.48, 0.13)}
    mat = material('elemental_crystal', colours[icon], 0.23, tile='crystal_' + icon)
    rings = []
    for y, scale in ((-0.7, 0.23), (-0.45, 0.88), (0.4, 1), (0.63, 0.55)):
        rings.append([(math.cos(i * math.tau / 8) * 0.55 * scale,
                       y + 0.035 * math.sin(i * math.tau / 8),
                       math.sin(i * math.tau / 8) * 0.36 * scale) for i in range(8)])
    surface(icon, rings, mat, 8, smooth=False)


def urn():
    gold = material('gold_cage', (0.72, 0.43, 0.075), 0.37, 1)
    enamel = material('violet_enamel', (0.1, 0.035, 0.4), 0.4, tile='enamel')
    ellipsoid('violet_body', (0.42, 0.42, 0.65), enamel, centre=(0, 0, 0.7), sides=16, rows=10)
    for i in range(8):
        a = i * math.tau / 8
        path = []
        for j in range(11):
            t = j / 10
            radius = 0.19 + 0.26 * math.sin(t * math.pi)
            path.append((radius * math.cos(a + 0.13 * math.sin(t * math.tau)),
                         radius * math.sin(a + 0.13 * math.sin(t * math.tau)), 0.09 + 1.23 * t))
        tube('gold_cage_rib', path, [0.022] * len(path), gold, 6)
    for z, radius in ((0.12, 0.24), (1.3, 0.24), (0.7, 0.455)):
        path = [(radius * math.cos(i * math.tau / 20), radius * math.sin(i * math.tau / 20), z)
                for i in range(20)]
        tube('gold_band', path, [0.024] * len(path), gold, 6, closed=True)
    ellipsoid('gold_stopper', (0.2, 0.2, 0.12), gold, centre=(0, 0, 1.43), sides=16, rows=4)
    ellipsoid('gold_foot', (0.24, 0.24, 0.06), gold, centre=(0, 0, 0.05), sides=16, rows=3)
    # Roll the capped vessel onto its side; the widest rib supplies its support.
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            for v in obj.data.vertices:
                x, y, z = v.co
                v.co = (x, z, -y)


def ring():
    gold = material('signet_gold', (0.75, 0.48, 0.12), 0.32, 1)
    path = [(0.45 * math.cos(i * math.tau / 32), 0.52 * math.sin(i * math.tau / 32), 0)
            for i in range(32)]
    tube('signet_band', path, [0.085] * len(path), gold, 8, closed=True)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.43, 0.1))
    obj = bpy.context.object
    obj.name = 'signet_bezel'
    obj.scale = (0.55, 0.5, 0.14)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material('silver_rim', (0.65, 0.65, 0.62), 0.4, 1))
    bevel = obj.modifiers.new('bevel', 'BEVEL')
    bevel.width, bevel.segments = 0.025, 1
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    mat = material('dragon_seal', (0.03, 0.03, 0.03), 0.55, tile='signet')
    # A thin closed inset has a dedicated full-face UV template rather than an oblique icon projection.
    corners = [(-0.235, 0.22), (0.235, 0.22), (0.235, 0.64), (-0.235, 0.64)]
    inset = surface('black_signet_face', [[(x, y, z) for x, y in corners] for z in (0.17, 0.18)], mat, 4,
                    smooth=False)
    for poly in inset.data.polygons:
        if all(inset.data.vertices[i].co.z > 0.175 for i in poly.vertices):
            for loop in poly.loop_indices:
                v = inset.data.vertices[inset.data.loops[loop].vertex_index].co
                inset.data.uv_layers.active.data[loop].uv = ((v.x + 0.235) / 0.47, (v.y - 0.22) / 0.42)


def finish(icon):
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for obj in objects:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(objects) > 1:
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        objects = [bpy.context.object]
        objects[0].name = 'sculpture_' + icon
    points = [v.co for o in objects for v in o.data.vertices]
    shift = Vector(((min(v.x for v in points) + max(v.x for v in points)) / 2,
                    (min(v.y for v in points) + max(v.y for v in points)) / 2, min(v.z for v in points)))
    for obj in objects:
        for v in obj.data.vertices:
            v.co -= shift
        if not obj.data.uv_layers:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(island_margin=0.02)
            bpy.ops.object.mode_set(mode='OBJECT')
        mod = obj.modifiers.new('triangulate', 'TRIANGULATE')
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        assert all(p.area > 1e-10 for p in obj.data.polygons), obj.name
        assert all(-1e-6 <= uv <= 1.000001 for item in obj.data.uv_layers.active.data for uv in item.uv)
    count = sum(len(o.data.polygons) for o in objects)
    name = 'sculpture_' + icon
    assert count <= DESIGNS[name]['tris'], (icon, count, DESIGNS[name]['tris'])
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (name + '.blend')))
    bpy.ops.export_scene.gltf(filepath=str(OUT / (name + '_export.glb')), export_format='GLB',
                              use_selection=True, export_yup=True, export_tangents=False)
    print('SCULPTURE', icon, count, 'triangles')


def main():
    only = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else set()
    builders = {'6thybone': lambda: bone('6thybone'), 'item305': lambda: bone('item305'),
                '7item271': lambda: bone('7item271'), 'item308': horn, '7item291': egg,
                '7item272': urn, '7item250': ring}
    builders.update({icon: lambda icon=icon: gem(icon) for icon in ('item270', 'item271', 'item272', 'item273')})
    ownership = json.loads((HERE / 'ownership.json').read_text())
    assert set(builders) <= {e['icon'] for e in ownership}
    assert all(DESIGNS['sculpture_' + icon]['route'] == 'blender' for icon in builders)
    for icon, build in builders.items():
        if only and icon not in only:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        build()
        finish(icon)


main()
