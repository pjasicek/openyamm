"""Build nine icon-faithful parchment volumes in an isolated background Blender process.

The sheet is a closed thick ribbon following a spiral cross-section, not an icon relief.
All components use one packed PBR material per icon. No shared bindings are written.
"""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
TAU = math.tau
LOW = '--lod' in sys.argv
UV_LAYOUT = {}
QUADS = {'front': (0, 1), 'back': (1, 1), 'metal': (0, 0), 'trim': (1, 0)}


def uv_tile(points, tile):
    x, y = QUADS[tile]
    return [((x + .025 + .95 * u) / 2, (y + .025 + .95 * v) / 2) for u, v in points]


def material(icon):
    mat = bpy.data.materials.new('Painted parchment and fittings')
    mat.use_nodes = True
    mat.use_backface_culling = True
    tree = mat.node_tree
    bsdf = tree.nodes.get('Principled BSDF')
    for name in ('basecolor', 'mr', 'normal'):
        node = tree.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(P / 'textures' / f'{icon}_{name}.png'))
        if name == 'basecolor':
            tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
        elif name == 'mr':
            node.image.colorspace_settings.name = 'Non-Color'
            separate = tree.nodes.new('ShaderNodeSeparateColor')
            tree.links.new(node.outputs['Color'], separate.inputs['Color'])
            tree.links.new(separate.outputs['Green'], bsdf.inputs['Roughness'])
            tree.links.new(separate.outputs['Blue'], bsdf.inputs['Metallic'])
        else:
            node.image.colorspace_settings.name = 'Non-Color'
            normal = tree.nodes.new('ShaderNodeNormalMap')
            tree.links.new(node.outputs['Color'], normal.inputs['Color'])
            tree.links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def mesh(name, vertices, faces, mat, uvs, smooth=True, flat_start=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    layer = data.uv_layers.new(name='UVMap')
    for face, coords in zip(data.polygons, uvs):
        face.use_smooth = smooth and (flat_start is None or face.index < flat_start)
        for loop, uv in zip(face.loop_indices, coords):
            layer.data[loop].uv = uv
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(mat)
    return obj


def sheet(name, path, width, mat, aged=False, front='front', thickness=.004):
    # Cross-section tangent gives the local sheet normal; both skins and all rims are explicit.
    n, across = len(path), 4 if LOW else 8
    distances = [0]
    for a, b in zip(path, path[1:]):
        distances.append(distances[-1] + math.dist(a[:2], b[:2]))
    length = distances[-1]
    scale = max(length, width)
    usize, vsize = width / scale, length / scale
    UV_LAYOUT.update({'u_size': usize, 'v_size': vsize, 'length': length, 'width': width,
                      'texels_per_model_unit': 256 * .475 * 2 / scale})
    def paper_uv(i, j):
        return (.5 + (i / across - .5) * usize, .5 + (distances[j] / length - .5) * vsize)
    vertices = []
    for skin in (-1, 1):
        for j, (y, z, v) in enumerate(path):
            before, after = path[max(0, j - 1)], path[min(n - 1, j + 1)]
            tangent = Vector((0, after[0] - before[0], after[1] - before[1])).normalized()
            normal = Vector((0, -tangent.z, tangent.y))
            for i in range(across + 1):
                u = i / across
                ragged = (.014 * math.sin(j * 2.3) + .009 * math.sin(j * 5.1)) if aged else .002 * math.sin(j)
                x = (u - .5) * (width + ragged * 2)
                warp = .003 * math.sin(u * math.pi) * math.sin(v * 8)
                vertices.append(Vector((x, y, z + warp)) + normal * skin * thickness / 2)
    count = n * (across + 1)
    faces, uvs = [], []
    for skin in range(2):
        for j in range(n - 1):
            for i in range(across):
                a = skin * count + j * (across + 1) + i
                faces.append((a, a + 1, a + across + 2, a + across + 1))
                uvs.append(uv_tile([paper_uv(i, j), paper_uv(i + 1, j),
                                    paper_uv(i + 1, j + 1), paper_uv(i, j + 1)],
                                   front if skin == 1 else 'back'))
    boundary = list(range(across + 1))
    boundary += [j * (across + 1) + across for j in range(1, n)]
    boundary += [(n - 1) * (across + 1) + i for i in range(across - 1, -1, -1)]
    boundary += [j * (across + 1) for j in range(n - 2, 0, -1)]
    for a, b in zip(boundary, boundary[1:] + boundary[:1]):
        faces.append((a, b, b + count, a + count))
        uvs.append(uv_tile([(.1, .1), (.9, .1), (.9, .14), (.1, .14)], 'back'))
    return mesh(name, vertices, faces, mat, uvs, flat_start=(n - 1) * across * 2)


def scroll_path(span, radii, turns=1.3, steps=28):
    if LOW:
        steps = max(12, round(steps * .75))
    sections = []
    for side, radius in zip((-1, 1), radii):
        section = []
        for i in range(steps + 1):
            t = i / steps
            angle = -math.pi / 2 + turns * TAU * t
            r = radius - .014 * turns * t
            section.append((side * (span / 2 + r * math.cos(angle)),
                            .012 + radius + r * math.sin(angle),
                            (.12 * (1 - t) if side == -1 else .88 + .12 * t)))
        sections.append(section)
    middle = [(span * (i / 8 - .5), .012 + .006 * math.sin(math.pi * i / 8), .12 + .76 * i / 8)
              for i in range(1, 8)]
    return list(reversed(sections[0])) + middle + sections[1]


def lathe(name, profile, mat, tile='metal', centre=(0, 0, 0), segments=16):
    # Axis X. Closed low-valence ear caps, UV seams on each end's hard edge.
    if LOW:
        segments = max(8, round(segments * .66))
    vertices = [(centre[0] + x, centre[1] + r * math.cos(TAU * i / segments),
                 centre[2] + r * math.sin(TAU * i / segments)) for x, r in profile for i in range(segments)]
    faces, uvs = [], []
    total = sum(math.dist(a, b) for a, b in zip(profile, profile[1:]))
    dist = 0
    for j in range(len(profile) - 1):
        start = dist / total
        dist += math.dist(profile[j], profile[j + 1])
        for i in range(segments):
            k = (i + 1) % segments
            faces.append((j * segments + i, j * segments + k,
                          (j + 1) * segments + k, (j + 1) * segments + i))
            uvs.append(uv_tile([(start, i / segments), (start, (i + 1) / segments),
                                (dist / total, (i + 1) / segments), (dist / total, i / segments)], tile))
    for row in (0, len(profile) - 1):
        ids = list(range(row * segments, (row + 1) * segments))
        while len(ids) > 2:
            tri = (ids.pop(0), ids[0], ids[-1])
            faces.append(tri)
            uvs.append(uv_tile([(.5 + .45 * math.cos(TAU * (i % segments) / segments),
                                .5 + .45 * math.sin(TAU * (i % segments) / segments)) for i in tri], tile))
            ids.reverse()
    return mesh(name, vertices, faces, mat, uvs, flat_start=(len(profile) - 1) * segments)


def tube(name, points, radius, mat, tile='trim', sides=6):
    closed = (Vector(points[0]) - Vector(points[-1])).length < 1e-7
    if closed:
        points = points[:-1]
    vertices = []
    for i, p in enumerate(points):
        after = points[(i + 1) % len(points)] if closed else points[min(i + 1, len(points) - 1)]
        before = points[i - 1] if closed else points[max(0, i - 1)]
        direction = (Vector(after) - Vector(before)).normalized()
        right = direction.cross(Vector((1, 0, 0)))
        if right.length < .01:
            right = direction.cross(Vector((0, 1, 0)))
        right.normalize()
        up = direction.cross(right)
        vertices += [Vector(p) + radius * (right * math.cos(TAU * j / sides) + up * math.sin(TAU * j / sides))
                     for j in range(sides)]
    faces, uvs = [], []
    for i in range(len(points) if closed else len(points) - 1):
        for j in range(sides):
            faces.append((i * sides + j, i * sides + (j + 1) % sides,
                          ((i + 1) % len(points)) * sides + (j + 1) % sides,
                          ((i + 1) % len(points)) * sides + j))
            uvs.append(uv_tile([(j / sides, i / len(points)), ((j + 1) / sides, i / len(points)),
                                ((j + 1) / sides, (i + 1) / len(points)), (j / sides, (i + 1) / len(points))], tile))
    for row in (() if closed else (0, len(points) - 1)):
        for i in range(1, sides - 1):
            faces.append((row * sides, row * sides + i, row * sides + i + 1))
            uvs.append(uv_tile([(.2, .2), (.8, .2), (.5, .8)], tile))
    return mesh(name, vertices, faces, mat, uvs)


def envelope(mat):
    # Closed thin body and separately folded triangular flaps, never a raised painting.
    outlines = [[(-.5, -.39), (.5, -.39), (.5, .39), (-.5, .39)],
                [(-.5, -.39), (.5, -.39), (0, .05)],
                [(-.5, .39), (-.5, -.39), (.04, 0)],
                [(.5, -.39), (.5, .39), (-.04, 0)],
                [(.5, .39), (-.5, .39), (0, -.09)]]
    for level, outline in enumerate(outlines):
        low, high = .003 + level * .005, .017 + level * .005
        vertices = [(x, y, z) for z in (low, high) for x, y in outline]
        n = len(outline)
        faces = [tuple(reversed(range(n))), tuple(range(n, n * 2))]
        faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
        uvs = [uv_tile([(vertices[i][0] + .5, vertices[i][1] / .78 + .5) for i in f], 'front') for f in faces]
        mesh('Folded letter' if level == 0 else f'Overlapping flap {level}', vertices, faces, mat, uvs, False)
    seal = lathe('Raised red wax seal', [(-.018, .074), (-.013, .088), (.003, .09), (.012, .077)],
                 mat, 'trim', segments=20)
    seal.rotation_euler.y = -math.pi / 2
    seal.location.z = .060
    ring = [(r * math.cos(TAU * i / 24), r * math.sin(TAU * i / 24), .08)
            for i in range(25) for r in (.061,)]
    tube('Wax seal rim impression', ring, .003, mat)
    tube('Wax seal impressed sigil', [(-.025, -.026, .08), (-.025, .027, .08), (.02, .027, .08),
                                     (.025, 0, .08), (-.025, -.003, .08), (.025, -.03, .08)], .004, mat)


def build(icon):
    UV_LAYOUT.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mat = material(icon)
    if icon in ('item264', 'item265'):
        sheet('Open written parchment with curled ends', scroll_path(.78, (.055, .052), .85, 18),
              .76, mat, aged=icon == 'item264')
    elif icon == '7item251':
        envelope(mat)
    elif icon == '7item182':
        path = []
        steps = 36 if LOW else 56
        for i in range(steps + 1):
            t = i / steps
            angle = TAU * (2.1 * t + .18)
            r = .058 + .032 * t
            path.append((r * math.cos(angle), .10 + r * math.sin(angle), t))
        sheet('Continuous tied parchment spiral', path, 1, mat, front='front', thickness=.005)
        for x in (-.025, 0, .025):
            segments = 12 if LOW else 20
            points = [(x, .098 * math.cos(TAU * i / segments), .10 + .098 * math.sin(TAU * i / segments))
                      for i in range(segments + 1)]
            tube('Red binding cord', points, .009, mat)
        for side in (-1, 1):
            points = [(side * .014, -.04, .19), (side * .035, -.08, .19), (side * .06, -.16, .12),
                      (side * .10, -.20, .05), (side * .14, -.22, .025)]
            tube('Loose binding tail', points, .012, mat)
    else:
        radii, span = (.090, .067), .29
        sheet('Continuous double-ended curled parchment', scroll_path(span, radii), 1, mat)
        for side, radius in zip((-1, 1), radii):
            for end in (-1, 1):
                profile = [(0, .046), (.012, .056), (.022, .059), (.033, .045), (.048, .045),
                           (.058, .030), (.075, .028), (.083, .014)]
                profile = [(end * (.49 + x), r) for x, r in profile]
                lathe('Turned spindle finial', profile, mat, centre=(0, side * span / 2, .012 + radius), segments=12)
        if icon == 'scroll5':
            # Thick rolled textile collars carry the purple identity, with two thin real brass rims.
            for side, radius in zip((-1, 1), radii):
                for end in (-1, 1):
                    x = end * .452
                    lathe('Purple embroidered end collar', [(x - .045, radius + .003),
                                                            (x + .045, radius + .003)], mat, 'trim',
                          centre=(0, side * span / 2, .012 + radius), segments=20)
                    for edge in (-.046, .046):
                        lathe('Brass collar edge', [(x + edge - .003, radius + .005),
                                                   (x + edge + .003, radius + .005)], mat, 'metal',
                              centre=(0, side * span / 2, .012 + radius), segments=16)
    finish(icon)


def finish(icon):
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for obj in objects:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        obj.select_set(False)
    coords = [v.co for o in objects for v in o.data.vertices]
    low = Vector([min(p[i] for p in coords) for i in range(3)])
    high = Vector([max(p[i] for p in coords) for i in range(3)])
    centre = (low + high) / 2
    # Longest footprint side along Blender Y, baked resting pose with floor contact at Z=0.
    rotate = high.x - low.x > high.y - low.y
    for obj in objects:
        for v in obj.data.vertices:
            x, y, z = v.co.x - centre.x, v.co.y - centre.y, v.co.z - low.z
            v.co = (-y, x, z) if rotate else (x, y, z)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = 'scroll_' + icon
    # All atlas regions share the same shader and one material, so one primitive survives export.
    mats = list(obj.data.materials)
    obj.data.materials.clear()
    obj.data.materials.append(mats[0])
    for face in obj.data.polygons:
        face.material_index = 0
    if not LOW:
        (P / 'work' / f'uv_{icon}.json').write_text(json.dumps(UV_LAYOUT, indent=2) + '\n')
        bpy.ops.wm.save_as_mainfile(filepath=str(P / 'blends' / f'{icon}.blend'))
    out = P / ('work/lod' if LOW else 'work/finished')
    out.mkdir(exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(out / f'scroll_{icon}_export.glb'),
                              export_format='GLB', use_selection=True, export_yup=True,
                              export_animations=False, export_cameras=False, export_lights=False)
    print('BUILT', icon, sum(len(f.vertices) - 2 for f in obj.data.polygons), flush=True)


if __name__ == '__main__':
    only = set(sys.argv[sys.argv.index('--') + 1:]) - {'--lod'} if '--' in sys.argv else set()
    entries = json.loads((P / 'audit.json').read_text())
    for entry in entries:
        if entry['status'] == 'rebuild' and (not only or entry['icon'] in only):
            build(entry['icon'])
