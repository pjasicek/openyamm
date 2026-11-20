"""Owned organic ground items. Run with isolated Blender --background --python ...

The 4x4 atlas is a purpose-built UV template, not a projected inventory painting.
Every component maps into its material cell with a 6-pixel gutter at 1024.
"""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'projectiles_claude/scripts'))
import projlib as pl

OUT = PROJECT / 'work/blender'
OWNERSHIP = {i['icon']: i for i in json.loads((PROJECT / 'ownership.json').read_text())}


def atlas_uv(cell, u, v):
    return ((cell % 4 + 0.025 + 0.95 * u) / 4,
            1 - (cell // 4 + 0.025 + 0.95 * (1 - v)) / 4)


def material():
    mat = bpy.data.materials.new('organic_material_atlas')
    mat.use_nodes = True
    mat.use_backface_culling = True
    nodes = mat.node_tree.nodes
    shader = nodes.get('Principled BSDF')
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(str(PROJECT / 'textures/organic_materials.png'))
    mat.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    rough = nodes.new('ShaderNodeTexImage')
    rough.image = bpy.data.images.load(str(PROJECT / 'textures/organic_roughness.png'))
    rough.image.colorspace_settings.name = 'Non-Color'
    mat.node_tree.links.new(rough.outputs['Color'], shader.inputs['Roughness'])
    shader.inputs['Metallic'].default_value = 0
    shader.inputs['Roughness'].default_value = 0.62
    return mat


def mesh(name, vertices, faces, cell, coordinates=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(bpy.data.materials['organic_material_atlas'])
    layer = data.uv_layers.new()
    for poly in data.polygons:
        poly.use_smooth = True
        for index in poly.loop_indices:
            vertex = data.loops[index].vertex_index
            u, v = coordinates[vertex] if coordinates else (vertices[vertex][0] + 0.5, vertices[vertex][1] + 0.5)
            layer.data[index].uv = atlas_uv(cell, max(0, min(1, u)), max(0, min(1, v)))
    if cell == 14:
        colour = data.color_attributes.new('Tint', 'FLOAT_COLOR', 'POINT')
        heights = [p[2] for p in vertices]
        low, high = min(heights), max(heights)
        for value, point in zip(colour.data, vertices):
            t = max(0, min(1, ((point[2] - low) / (high - low) - 0.35) / 0.5))
            value.color = (0.75 + 0.25 * t, 0.09 + 0.91 * t, 0.025 + 0.975 * t, 1)
        data.color_attributes.active_color = colour
        nt = data.materials[0].node_tree
        tint = nt.nodes.new('ShaderNodeVertexColor')
        tint.layer_name = 'Tint'
        multiply = nt.nodes.new('ShaderNodeMixRGB')
        multiply.blend_type = 'MULTIPLY'
        multiply.inputs[0].default_value = 1
        tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image.name.startswith('organic_materials'))
        nt.links.new(tex.outputs['Color'], multiply.inputs[1])
        nt.links.new(tint.outputs['Color'], multiply.inputs[2])
        nt.links.new(multiply.outputs[0], nt.nodes.get('Principled BSDF').inputs['Base Color'])
    return obj


def sphere(name, centre, radius, cell, subdivisions=2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1)
    bm.verts.ensure_lookup_table()
    points = [tuple(Vector(centre) + Vector((v.co.x * radius[0], v.co.y * radius[1], v.co.z * radius[2])))
              for v in bm.verts]
    uv = [(0.5 + math.atan2(v.co.y, v.co.x) / (2 * math.pi),
           0.5 + math.asin(max(-1, min(1, v.co.z))) / math.pi) for v in bm.verts]
    obj = mesh(name, points, [[v.index for v in f.verts] for f in bm.faces], cell, uv)
    bm.free()
    return obj


def sweep(name, centres, radii, cell, sides=12, band_cells=None):
    points, uv, faces = [], [], []
    for k, (point, radius) in enumerate(zip(centres, radii)):
        direction = Vector(centres[min(k + 1, len(centres) - 1)]) - Vector(centres[max(0, k - 1)])
        axis = direction.normalized()
        cross = axis.cross(Vector((0, 0, 1))).normalized()
        if cross.length < 0.1:
            cross = Vector((1, 0, 0))
        up = axis.cross(cross).normalized()
        rx, rz = radius if isinstance(radius, tuple) else (radius, radius)
        for n in range(sides):
            angle = 2 * math.pi * n / sides
            points.append(tuple(Vector(point) + cross * (math.cos(angle) * rx) + up * (math.sin(angle) * rz)))
            uv.append((n / sides, k / (len(centres) - 1)))
    for k in range(len(centres) - 1):
        for n in range(sides):
            faces.append((k * sides + n, k * sides + (n + 1) % sides,
                          (k + 1) * sides + (n + 1) % sides, (k + 1) * sides + n))
    faces += [tuple(reversed(range(sides))), tuple((len(centres) - 1) * sides + n for n in range(sides))]
    obj = mesh(name, points, faces, cell, uv)
    if band_cells:
        for poly in obj.data.polygons:
            k = min(len(band_cells) - 1, poly.index // sides)
            for loop in poly.loop_indices:
                u, v = uv[obj.data.loops[loop].vertex_index]
                obj.data.uv_layers.active.data[loop].uv = atlas_uv(band_cells[k], u, v)
    return obj


def curved_sweep(name, centres, radii, cell, sides=12):
    points, widths = [], []
    for k in range(len(centres) - 1):
        p0, p1 = Vector(centres[max(0, k - 1)]), Vector(centres[k])
        p2, p3 = Vector(centres[k + 1]), Vector(centres[min(len(centres) - 1, k + 2)])
        for n in range(3):
            t = n / 3
            points.append(tuple(0.5 * (2 * p1 + (-p0 + p2) * t +
                                       (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                                       (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)))
            widths.append(radii[k] * (1 - t) + radii[k + 1] * t)
    points.append(centres[-1])
    widths.append(radii[-1])
    return sweep(name, points, widths, cell, sides)


def board(name, centre, scale, cell, angle=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler.z = angle
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new('Soft worn edges', 'BEVEL')
    bevel.width = 0.008
    bevel.segments = 1
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    obj.data.materials.append(bpy.data.materials['organic_material_atlas'])
    layer = obj.data.uv_layers.active or obj.data.uv_layers.new()
    for poly in obj.data.polygons:
        axes = sorted(range(3), key=lambda a: abs(poly.normal[a]))[:2]
        for loop in poly.loop_indices:
            co = obj.data.vertices[obj.data.loops[loop].vertex_index].co
            # Long wood grain follows the long board axis.
            u = co[axes[0]] / max(scale[axes[0]], 0.001) + 0.5
            v = co[axes[1]] / max(scale[axes[1]], 0.001) + 0.5
            layer.data[loop].uv = atlas_uv(cell, max(0, min(1, u)), max(0, min(1, v)))
    return obj


def leaf(centre, size, angle):
    x, y, z = centre
    shape = [(0, -size, 0), (-size * 0.32, -size * 0.25, 0.01),
             (0, size * 0.6, 0.025), (size * 0.32, -size * 0.25, 0.01),
             (0, -size * 0.1, 0.065)]
    points = [(x + a * math.cos(angle) - b * math.sin(angle),
               y + a * math.sin(angle) + b * math.cos(angle), z + c) for a, b, c in shape]
    obj = mesh('leaf', points, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (3, 2, 1, 0)], 4,
               [(0.5, 0), (0.05, 0.5), (0.5, 1), (0.95, 0.5), (0.5, 0.5)])
    return obj


def berries(icon):
    if icon == '7item141':
        positions = [(-0.11, 0.34), (0.06, 0.25), (-0.18, 0.12), (0, 0.05), (0.17, 0.04),
                     (-0.14, -0.1), (0.05, -0.16), (-0.07, -0.29), (-0.15, -0.4)]
        for n, (x, y) in enumerate(positions):
            sphere('red berry', (x, y, 0.12 + 0.035 * (n % 2)), (0.12, 0.13, 0.12), 2, 3)
        leaf((0.05, 0.5, 0.14), 0.32, 2.4)
        leaf((-0.06, 0.49, 0.14), 0.28, -2.0)
        sweep('twig', [(0, -0.35, 0.1), (0, 0.32, 0.13), (0.12, 0.57, 0.14)], [0.02, 0.025, 0.015], 4, 6)
    elif icon == 'herb03':
        for n in range(7):
            angle = n * math.pi / 3
            x, y = (0.24 * math.cos(angle), 0.24 * math.sin(angle)) if n < 6 else (0, 0)
            sphere('raspberry core', (x, y, 0.16), (0.15, 0.15, 0.14), 2)
            for k in range(7):
                a = k * math.pi * 2 / 7
                sphere('raspberry drupelet', (x + 0.08 * math.cos(a), y + 0.08 * math.sin(a), 0.26),
                       (0.055, 0.055, 0.055), 2, 1)
            leaf((x * 1.3, y * 1.3, 0.06), 0.24, angle - math.pi / 2)
    else:
        for x, y in [(-0.15, 0.13), (0.16, 0.32), (0.14, -0.08)]:
            for k in range(5):
                a = k * math.pi * 2 / 5
                sphere('orange berry', (x + 0.085 * math.cos(a), y + 0.085 * math.sin(a), 0.16),
                       (0.065, 0.065, 0.065), 3)
            leaf((x, y - 0.13, 0.07), 0.23, x * 5)
        sweep('stem', [(0, -0.5, 0.05), (0.02, 0, 0.1), (0.16, 0.4, 0.12)], [0.025, 0.02, 0.012], 4, 6)


def eye():
    sphere('eyeball', (0, 0, 0.31), (0.36, 0.36, 0.32), 14, 4)
    points, uv = [], []
    sides = 24
    for ring in range(5):
        radius = 0.003 + ring * 0.055
        for n in range(sides):
            a = n * 2 * math.pi / sides
            points.append((radius * math.cos(a), 0.05 + radius * math.sin(a),
                           0.31 + 0.332 * math.sqrt(1 - (radius / 0.36) ** 2)))
            uv.append((0.5 + 0.48 * radius / 0.223 * math.cos(a), 0.5 + 0.48 * radius / 0.223 * math.sin(a)))
    faces = [tuple(range(sides))]
    for ring in range(4):
        for n in range(sides):
            a, b = ring * sides + n, ring * sides + (n + 1) % sides
            faces.append((a, a + sides, b + sides, b))
    # The curved iris patch is deliberately open and occluded on its back by the eye.
    mesh('iris', points, faces, 15, uv)


def shell():
    points, uv, faces = [], [], []
    slices, rings = 32, 7
    for side in range(2):
        for k in range(rings):
            r = 0.05 + 0.95 * k / (rings - 1)
            for n in range(slices + 1):
                a = -1.28 + 2.56 * n / slices
                scallop = 1 + 0.025 * math.cos(n * math.pi / 2)
                x, y = r * math.sin(a) * 0.58 * scallop, r * math.cos(a) * scallop
                z = 0.2 * (1 - r * r) + 0.045 * r * math.cos(n * math.pi / 2)
                z -= side * 0.025
                points.append((x, y, z))
                uv.append((n / slices, r))
    stride = slices + 1
    layer = rings * stride
    for side in range(2):
        for k in range(rings - 1):
            for n in range(slices):
                a = side * layer + k * stride + n
                face = (a, a + 1, a + stride + 1, a + stride)
                faces.append(face if side == 0 else tuple(reversed(face)))
    boundary = list(range(stride)) + [k * stride + slices for k in range(1, rings)]
    boundary += list(reversed(range((rings - 1) * stride, rings * stride - 1)))
    boundary += [k * stride for k in reversed(range(1, rings - 1))]
    for n, a in enumerate(boundary):
        b = boundary[(n + 1) % len(boundary)]
        faces.append((a, a + layer, b + layer, b))
    mesh('scallop shell', points, faces, 7, uv)


def tooth():
    curved_sweep('ivory curved crown', [(0, -0.42, 0.05), (0.08, -0.25, 0.09), (0.15, -0.04, 0.14),
                                (0.12, 0.18, 0.16), (0.02, 0.31, 0.15)],
          [0.008, 0.045, 0.09, 0.13, 0.115], 0)
    for x in (-0.095, 0.095):
        sweep('forked root', [(0.02 + x * 0.5, 0.24, 0.15), (x, 0.37, 0.15), (x * 1.5, 0.56, 0.1)],
              [0.075, 0.05, 0.012], 1, 8)


def stinger():
    centres = [(0, 0.44, 0.24), (0.015, 0.34, 0.24), (0.03, 0.18, 0.25), (0, 0.01, 0.23),
               (-0.05, -0.15, 0.18), (-0.12, -0.31, 0.12), (-0.22, -0.49, 0.025)]
    sweep('striped wasp abdomen and stinger', centres, [0.07, 0.17, 0.19, 0.155, 0.1, 0.045, 0.003], 8,
          16, [8, 9, 8, 9, 8, 8, 8])


def bark():
    centres = [(-0.23, -0.42, 0.08), (-0.08, -0.23, 0.13), (0.07, 0, 0.15),
               (0.08, 0.23, 0.14), (-0.02, 0.4, 0.1)]
    sweep('thornbark', centres, [0.025, 0.065, 0.08, 0.06, 0.015], 10, 8)
    for n, (x, y, z) in enumerate(centres[1:-1]):
        sign = -1 if n % 2 else 1
        sweep('thorn', [(x, y, z), (x + sign * 0.1, y + 0.01, z + 0.05),
                        (x + sign * 0.2, y - 0.03, z + 0.08)], [0.045, 0.028, 0.002], 8, 6)


def heartwood():
    board('cross plank', (0, -0.06, 0.05), (0.24, 0.95, 0.06), 5, -0.73)
    board('back plank', (0, 0.02, 0.11), (0.25, 0.9, 0.06), 5, 0.74)
    outline = [(-0.16, -0.5), (0.16, -0.5), (0.24, 0.26), (0.16, 0.48), (-0.16, 0.48), (-0.24, 0.26)]
    vertices = [(x, y, z) for z in (0.15, 0.22) for x, y in outline]
    faces = [tuple(reversed(range(6))), tuple(range(6, 12))]
    faces += [(n, (n + 1) % 6, (n + 1) % 6 + 6, n + 6) for n in range(6)]
    mesh('coffin-shaped Heartwood board', vertices, faces, 5)


def fishcrate():
    for n in range(4):
        board('bottom plank', (-0.3 + n * 0.2, 0, 0.035), (0.19, 0.75, 0.07), 6)
        for side in (-1, 1):
            board('side plank', (side * 0.41, 0, 0.12 + n * 0.13), (0.06, 0.8, 0.12), 6)
            board('end plank', (0, side * 0.39, 0.12 + n * 0.13), (0.78, 0.06, 0.12), 6)
    for x in (-0.38, 0.38):
        for y in (-0.36, 0.36):
            board('corner brace', (x, y, 0.3), (0.065, 0.07, 0.52), 6)
    for n in range(3):
        x, y, z = -0.23 + n * 0.23, -0.04 + n * 0.035, 0.52 + n * 0.015
        sphere('dried sunfish', (x, y, z), (0.095, 0.29, 0.08), 12, 3)
        tail = [(x, y + 0.23, z), (x - 0.1, y + 0.4, z), (x + 0.1, y + 0.4, z),
                (x, y + 0.31, z + 0.02)]
        mesh('tail fin', tail, [(0, 1, 3), (1, 2, 3), (2, 0, 3), (2, 1, 0)], 13,
             [(0.5, 0), (0, 1), (1, 1), (0.5, 0.7)])
        sphere('fish eye', (x, y - 0.18, z + 0.065), (0.018, 0.02, 0.012), 9, 1)


def jar():
    z = [0.025, 0.06, 0.14, 0.53, 0.61, 0.67, 0.73, 0.75]
    radii = [0.19, 0.24, 0.25, 0.25, 0.22, 0.17, 0.17, 0.16]
    obj = sweep('glass vessel', [(0, 0, h) for h in z], radii, 11, 20)
    glass = bpy.data.materials.new('clear_glass')
    glass.use_nodes = True
    shader = glass.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (0.8, 0.87, 0.9, 1)
    shader.inputs['Alpha'].default_value = 0.17
    shader.inputs['Roughness'].default_value = 0.13
    glass.surface_render_method = 'DITHERED'
    glass.use_backface_culling = True
    obj.data.materials.clear()
    obj.data.materials.append(glass)
    sweep('golden jelly', [(0, 0, 0.06), (0, 0, 0.1), (0, 0, 0.51)], [0.19, 0.23, 0.23], 11, 20)
    sweep('cork stopper', [(0, 0, 0.72), (0, 0, 0.78), (0, 0, 0.81)], [0.16, 0.19, 0.18], 10, 16)


def finish(icon):
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    # Join fills missing attributes with zero: make the iris tint explicitly white first.
    if icon == 'item161':
        for obj in objects:
            if not obj.data.color_attributes:
                tint = obj.data.color_attributes.new('Tint', 'FLOAT_COLOR', 'POINT')
                for value in tint.data:
                    value.color = (1, 1, 1, 1)
                obj.data.color_attributes.active_color = tint
    # Opaque surfaces share one material/draw; keep glass on its own mesh node.
    opaque = [o for o in objects if o.data.materials[0].name != 'clear_glass']
    bpy.ops.object.select_all(action='DESELECT')
    for obj in opaque:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = opaque[0]
    bpy.ops.object.join()
    opaque[0].name = 'organic_' + icon
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    points = [o.matrix_world @ v.co for o in objects for v in o.data.vertices]
    low = Vector(tuple(min(p[a] for p in points) for a in range(3)))
    high = Vector(tuple(max(p[a] for p in points) for a in range(3)))
    centre = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    longest = max(high.x - low.x, high.y - low.y)
    rotate = high.x - low.x > high.y - low.y
    for obj in objects:
        transform = obj.matrix_world.copy()
        for vertex in obj.data.vertices:
            co = (transform @ vertex.co - centre) / longest
            vertex.co = (-co.y, co.x, co.z) if rotate else co
        obj.matrix_world.identity()
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
        bm.to_mesh(obj.data)
        bm.free()
        pl.fix_winding(obj)
    triangles = sum(len(o.data.polygons) for o in objects)
    assert 0 < triangles < 4000, (icon, triangles)
    points = [v.co for o in objects for v in o.data.vertices]
    assert abs(min(v.z for v in points)) < 1e-5
    assert abs(max(v.y for v in points) + min(v.y for v in points)) < 1e-5
    for obj in objects:
        for loop in obj.data.uv_layers.active.data:
            assert all(-1e-6 <= value <= 1.000001 for value in loop.uv)
    OUT.mkdir(exist_ok=True)
    for obj in objects:
        obj.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / ('organic_' + icon + '.blend')))
    path = OUT / (icon + '_export.glb')
    bpy.ops.export_scene.gltf(filepath=str(path), use_selection=True, export_format='GLB', export_yup=True,
                              export_normals=True, export_tangents=False, export_animations=False,
                              export_skins=False, export_morph=False, export_apply=True, export_vertex_color='ACTIVE')
    return {'icon': icon, 'triangles': triangles, 'binding_length': OWNERSHIP[icon]['length'],
            'export': str(path.relative_to(PROJECT)), 'grounded': True, 'footprint_centred': True,
            'uv_in_0_1': True, 'texture':'textures/organic_materials.png',
            'texel_density': 'Material cells provide 243 usable texels per full component span; repeated parts deliberately overlap.'}


def main():
    builders = {'7item141': lambda: berries('7item141'), 'herb03': lambda: berries('herb03'),
                'item158': lambda: berries('item158'), 'item161': eye, 'item169': bark,
                '7item279': shell, 'item303': jar, 'item314': heartwood, 'item316': fishcrate,
                'item322': stinger, 'tooth': tooth}
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(builders)
    receipts = []
    for icon in only:
        assert icon in OWNERSHIP
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if icon in builders:
            material()
            builders[icon]()
        else:
            assert icon in ('7item149', 'item164', 'item174')
            bpy.ops.import_scene.gltf(filepath=str(PROJECT / 'work/baseline' / (icon + '_export.glb')))
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    for v in obj.data.vertices:
                        v.co.z *= 0.25
        receipts.append(finish(icon))
    receipt_path = OUT / 'build_receipts.json'
    previous = {r['icon']: r for r in json.loads(receipt_path.read_text())} if receipt_path.exists() else {}
    previous.update({r['icon']: r for r in receipts})
    receipt_path.write_text(json.dumps(list(previous.values()), indent=2) + '\n')


if __name__ == '__main__':
    main()
