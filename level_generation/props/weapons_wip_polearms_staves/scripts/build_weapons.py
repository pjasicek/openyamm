"""Physical round hafts and separately forged blade heads, with purpose-painted cylindrical UVs.

Usage: blender --background --python build_weapons.py -- [--clay] <icon> ...
No icon colour is projected onto the model. Source alpha defines blade cutting outlines only.
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'projectiles_claude/scripts'))
import projlib as pl

DESIGNS = json.loads((HERE / 'designs.json').read_text())


def image_array(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    w, h = image.size
    data = np.array(image.pixels[:], np.float32).reshape(h, w, 4)[::-1].copy()
    bpy.data.images.remove(image)
    return data


def add(bm, layer, coordinates, uv):
    face = bm.faces.new(coordinates)
    for loop, value in zip(face.loops, uv):
        loop[layer].uv = value
    return face


def shaft(bm, layer, design, socket_metal=None):
    w, h = design['image_size']
    scale = 2 / h
    profile = design['shaft_profile']
    if len(profile) < 2:
        return
    rings = []
    sides = 12
    for y, cx, radius in profile:
        if socket_metal:
            radius *= .97  # Inset the overlapping tenon so its ring never coincides with the haft's cap.
        rings.append([bm.verts.new(((cx - w / 2) * scale + radius * scale * math.cos(i * 2 * math.pi / sides),
                                   (h / 2 - y) * scale, radius * scale * math.sin(i * 2 * math.pi / sides)))
                      for i in range(sides)])
    for k in range(len(rings) - 1):
        for i in range(sides):
            j = (i + 1) % sides
            vs = [rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]]
            y0 = (profile[k][0] - profile[0][0]) / max(profile[-1][0] - profile[0][0], 1)
            y1 = (profile[k + 1][0] - profile[0][0]) / max(profile[-1][0] - profile[0][0], 1)
            uv = [((4 + 56 * i / sides) / 512, (1020 - 1016 * y0) / 1024),
                  ((4 + 56 * (i + 1) / sides) / 512, (1020 - 1016 * y0) / 1024),
                  ((4 + 56 * (i + 1) / sides) / 512, (1020 - 1016 * y1) / 1024),
                  ((4 + 56 * i / sides) / 512, (1020 - 1016 * y1) / 1024)]
            if socket_metal:
                base_v = .54 if socket_metal == 'steel' else .04
                distance = abs(profile[-1][0] - profile[0][0]) * scale * 500 / 1024
                uv = [(.3 + 40 / 512 * u, base_v + distance * v)
                      for u, v in [(i / sides, y0), ((i + 1) / sides, y0), ((i + 1) / sides, y1), (i / sides, y1)]]
                if socket_metal == 'wood':
                    uv = [(.01 + .1 * u, .4 + .2 * v)
                          for u, v in [(i / sides, y0), ((i + 1) / sides, y0), ((i + 1) / sides, y1), (i / sides, y1)]]
            add(bm, layer, vs, uv)
    # Strip-triangulated caps avoid a high-valence radial fan.
    for end, ring in enumerate([rings[0], rings[-1]]):
        def cap_uv(i):
            if socket_metal:
                return (.34 + 6 / 512 * math.cos(i * 2 * math.pi / sides),
                        (.72 if socket_metal == 'steel' else .22) + 6 / 1024 * math.sin(i * 2 * math.pi / sides))
            return ((32 + 8 * math.cos(i * 2 * math.pi / sides)) / 512,
                    ((1010 if end == 0 else 14) + 8 * math.sin(i * 2 * math.pi / sides)) / 1024)
        for i in range(1, sides - 1):
            add(bm, layer, [ring[0], ring[i], ring[i + 1]], [cap_uv(0), cap_uv(i), cap_uv(i + 1)])


def swept_parts(bm, layer, design):
    w, h = design['image_size']
    scale = 2 / h
    for part in design.get('swept_parts', []):
        profile = part['profile']
        rings = []
        for k, (x, y, radius) in enumerate(profile):
            a, b = profile[max(0, k - 1)], profile[min(len(profile) - 1, k + 1)]
            tangent = Vector((b[0] - a[0], -(b[1] - a[1]), 0)).normalized()
            radial = Vector((-tangent.y, tangent.x, 0))
            centre = Vector(((x - w / 2) * scale, (h / 2 - y) * scale, 0))
            rings.append([bm.verts.new(centre + radius * scale *
                                      (radial * math.cos(i * math.pi / 4) + Vector((0, 0, math.sin(i * math.pi / 4)))))
                          for i in range(8)])
        def uv(k, i):
            if part['material'] in ('wood', 'rope'):
                sy = (profile[k][1] - design['shaft_profile'][0][0]) / (h - design['shaft_profile'][0][0])
                if part['material'] == 'rope':
                    sy = .06
                return ((4 + 56 * i / 8) / 512, (1020 - 1016 * sy) / 1024)
            return (.25 + i / 8 * .15, (.56 if part['material'] == 'steel' else .06) + k / len(profile) * .3)
        for k in range(len(rings) - 1):
            for i in range(8):
                j = (i + 1) % 8
                add(bm, layer, [rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]],
                    [uv(k, i), uv(k, i + 1), uv(k + 1, i + 1), uv(k + 1, i)])
        for k in (0, len(rings) - 1):
            for i in range(1, 7):
                add(bm, layer, [rings[k][0], rings[k][i], rings[k][i + 1]],
                    [(uv(k, 0)[0] + .004 * math.cos(j * math.pi / 4),
                      uv(k, 0)[1] + .002 * math.sin(j * math.pi / 4)) for j in (0, i, i + 1)])


def blade(bm, layer, design):
    loops = design['head_loops']
    if not loops:
        return
    w, h = design['image_size']
    scale = 2 / h
    icon = image_array(ROOT / 'assets_dev/engine/icons_x2' / (design['master_icon'] + '.png'))
    mask = icon[:, :, 3] > .5
    end = design['head_end']
    points, edges = [], []
    for loop in loops:
        base = len(points)
        points.extend(loop)
        edges.extend((base + i, base + (i + 1) % len(loop)) for i in range(len(loop)))
    outline_count = len(points)
    # Blade ridges get a few purposeful centre vertices; the haft is an independent round solid.
    for y in range(3, end - 2, 8):
        xs = np.flatnonzero(mask[y])
        runs = np.split(xs, np.flatnonzero(np.diff(xs) > 1) + 1)
        for run in runs:
            if len(run) >= 3:
                points.append((float((run[0] + run[-1]) / 2), float(y)))
    result = delaunay_2d_cdt([Vector(p) for p in points], edges, [], 0, 1e-5)
    positions, _, faces, originals = result[:4]
    def inside(x, y):
        filled = False
        for loop in loops:
            for a, b in zip(loop, loop[1:] + loop[:1]):
                if (a[1] > y) != (b[1] > y):
                    if x < a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
                        filled = not filled
        return filled
    selected = []
    for face in faces:
        if len(face) != 3:
            continue
        centre = sum((positions[i] for i in face), Vector((0, 0))) / 3
        x, y = int(centre.x), int(centre.y)
        if inside(centre.x, centre.y):
            selected.append(face)
    edge_faces = {}
    for index, face in enumerate(selected):
        for j in range(3):
            edge_faces.setdefault(tuple(sorted((face[j], face[(j + 1) % 3]))), []).append(index)
    seen, clean = set(), []
    for index in range(len(selected)):
        if index in seen:
            continue
        todo, component = [index], []
        seen.add(index)
        while todo:
            current = todo.pop()
            component.append(selected[current])
            f = selected[current]
            for j in range(3):
                for other in edge_faces[tuple(sorted((f[j], f[(j + 1) % 3])))]:
                    if other not in seen:
                        seen.add(other)
                        todo.append(other)
        area = sum(abs((positions[f[1]] - positions[f[0]]).cross(positions[f[2]] - positions[f[0]])) / 2
                   for f in component)
        if area >= 3:
            clean.extend(component)
    selected = clean
    counts = Counter(tuple(sorted((face[i], face[(i + 1) % 3]))) for face in selected for i in range(3))
    boundary = {v for edge, count in counts.items() if count == 1 for v in edge}
    front, back = {}, {}
    head_width = max(p[0] for p in points) - min(p[0] for p in points)
    thickness = max(.004, min(.012, head_width * scale * .08))
    used = {i for face in selected for i in face}
    for i in used:
        p = positions[i]
        depth = .00045 if i in boundary else thickness / 2
        co = ((p.x - w / 2) * scale, (h / 2 - p.y) * scale)
        front[i] = bm.verts.new((*co, depth))
        back[i] = bm.verts.new((*co, -depth))
    minimum_x = min(p.x for p in positions)
    density = min(500, 500 / max(end * scale, 1e-3), 432 / max(head_width * scale, 1e-3))

    def uv(index, gold):
        p = positions[index]
        return ((72 + (p.x - minimum_x) * scale * density) / 512,
                (1016 - int(gold) * 512 - p.y * scale * density) / 1024)

    for face in selected:
        centre = sum((positions[i] for i in face), Vector((0, 0))) / 3
        colour = icon[min(h - 1, max(0, int(centre.y))), min(w - 1, max(0, int(centre.x))), :3]
        gold_designs = {'7item035', '7item041', '7item225', '7item227', 'item043', 'item044',
                        'item045', 'item055', 'item081', 'item331', 'item341', 'spear5', 'trident2'}
        gold = design['master_icon'] in gold_designs
        if design['master_icon'] == 'trident1':
            gold = abs(centre.x - w / 2) > w * .12 or centre.y > end * .7
        elif design['master_icon'] == 'item053':
            gold = centre.y > end * .52
        for verts, order in [(front, list(reversed(face))), (back, face)]:
            add(bm, layer, [verts[i] for i in order], [uv(i, gold) for i in order])
    for (a, b), count in counts.items():
        if count == 1:
            gold = design['master_icon'] in gold_designs
            add(bm, layer, [front[a], front[b], back[b], back[a]], [uv(a, gold), uv(b, gold)] * 2)


def rest(obj):
    # Rest on a lower convex-hull edge spanning the haft's middle, so actual parts support both ends.
    points = sorted(set((float(v.co.y), float(v.co.z)) for v in obj.data.vertices))
    hull = []
    for p in points:
        while len(hull) >= 2:
            a, b = hull[-2:]
            cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
            if cross > 1e-10:
                break
            hull.pop()
        hull.append(p)
    middle = (points[0][0] + points[-1][0]) / 2
    a, b = next((a, b) for a, b in zip(hull, hull[1:]) if a[0] <= middle <= b[0] and b[0] > a[0])
    angle = -math.atan2(b[1] - a[1], b[0] - a[0])
    assert abs(angle) < math.radians(25), angle
    rotation = Matrix.Rotation(angle, 3, 'X')
    for vertex in obj.data.vertices:
        vertex.co = rotation @ vertex.co
    lo = Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
    shift = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for vertex in obj.data.vertices:
        vertex.co -= shift
    return math.degrees(angle)


def gem_head(bm, layer, design):
    """A solid gem and separate swept cage fingers, not the source's painted circular outline."""
    spec = design['gem_head']
    w, h = design['image_size']
    radius = w * .42 * 2 / h
    half_height = spec['height_fraction']
    centre = Vector((0, 1 - half_height, 0))
    sphere = bmesh.ops.create_icosphere(bm, subdivisions=2 if spec['faceted'] else 3, radius=1)
    for vertex in sphere['verts']:
        vertex.co = Vector((vertex.co.x * radius, vertex.co.y * half_height, vertex.co.z * radius)) + centre
    sphere_set = set(sphere['verts'])
    for face in bm.faces:
        if all(v in sphere_set for v in face.verts):
            face.material_index = 1
            face.normal_update()
            axes = [i for i in range(3) if i != max(range(3), key=lambda i: abs(face.normal[i]))]
            for loop in face.loops:
                relative = loop.vert.co - centre
                loop[layer].uv = ((288 + relative[axes[0]] * 500) / 512,
                                   (768 + relative[axes[1]] * 500) / 1024)
    root = centre.y - half_height - .015
    root_radius = design['shaft_profile'][0][2] * 2 / h
    neck = [[half_height * h, w / 2, w * .14],
            [(half_height * h + design['head_end']) / 2, w / 2, w * .09],
            [design['head_end'] + 1, w / 2, design['shaft_profile'][0][2]]]
    shaft(bm, layer, {**design, 'shaft_profile': neck}, 'wood' if spec['cup'] == 'wood' else 'gold')
    for finger in range(4 if spec['cup'] == 'wood' else 6):
        angle = finger * 2 * math.pi / (4 if spec['cup'] == 'wood' else 6)
        radial = Vector((math.cos(angle), 0, math.sin(angle)))
        rings = []
        for t, distance, axial in [(0, root_radius, root), (.3, radius * .45, centre.y - half_height * .9),
                                    (.7, radius * 1.02, centre.y - half_height * .2),
                                    (1, radius * .85, centre.y + half_height * .45)]:
            point = radial * distance + Vector((0, axial, 0))
            width = max(.0012, radius * (.10 - .085 * t))
            ring = []
            for side in range(6):
                phase = side * 2 * math.pi / 6
                tangent = Vector((-radial.z, 0, radial.x))
                ring.append(bm.verts.new(point + width * (tangent * math.cos(phase)
                                                        + Vector((0, math.sin(phase), 0)))))
            rings.append(ring)
        for k in range(3):
            for side in range(6):
                j = (side + 1) % 6
                vs = [rings[k][side], rings[k][j], rings[k + 1][j], rings[k + 1][side]]
                if spec['cup'] == 'wood':
                    uv = [((4 + 56 * u) / 512, .985 - v * .03)
                          for u, v in [(side / 6, k / 3), (j / 6, k / 3), (j / 6, (k + 1) / 3), (side / 6, (k + 1) / 3)]]
                else:
                    uv = [((144 + 16 * u) / 512, .12 + v * .25)
                          for u, v in [(side / 6, k / 3), ((side + 1) / 6, k / 3), ((side + 1) / 6, (k + 1) / 3), (side / 6, (k + 1) / 3)]]
                add(bm, layer, vs, uv)
        for ring in (rings[0], rings[-1]):
            for side in range(1, 5):
                uv = [(0.29 + .008 * math.cos(s * math.pi / 3), .24 + .008 * math.sin(s * math.pi / 3))
                      for s in (0, side, side + 1)]
                add(bm, layer, [ring[0], ring[side], ring[side + 1]], uv)


def material(icon, clay):
    mat = bpy.data.materials.new(icon)
    mat.use_nodes = True
    mat.use_backface_culling = True
    tree = mat.node_tree
    bsdf = tree.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = .55
    if clay:
        bsdf.inputs['Base Color'].default_value = (.4, .4, .4, 1)
        return mat
    for kind, socket in [('basecolor', 'Base Color'), ('mr', None), ('normal', None)]:
        image = bpy.data.images.load(str(HERE / 'textures' / icon / (kind + '.png')))
        if kind != 'basecolor':
            image.colorspace_settings.name = 'Non-Color'
        node = tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        if socket:
            tree.links.new(node.outputs['Color'], bsdf.inputs[socket])
        elif kind == 'normal':
            mapping = tree.nodes.new('ShaderNodeNormalMap')
            tree.links.new(node.outputs['Color'], mapping.inputs['Color'])
            tree.links.new(mapping.outputs['Normal'], bsdf.inputs['Normal'])
        else:
            separate = tree.nodes.new('ShaderNodeSeparateColor')
            tree.links.new(node.outputs['Color'], separate.inputs['Color'])
            tree.links.new(separate.outputs['Green'], bsdf.inputs['Roughness'])
            tree.links.new(separate.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


def build_one(icon, clay):
    design = DESIGNS['pole_' + icon]
    pl.reset()
    bm = bmesh.new()
    layer = bm.loops.layers.uv.new('UVMap')
    shaft(bm, layer, design)
    swept_parts(bm, layer, design)
    if design.get('socket_profile'):
        shaft(bm, layer, {**design, 'shaft_profile': design['socket_profile']}, design['socket_metal'])
    if design.get('gem_head'):
        gem_head(bm, layer, design)
    elif not design.get('mesh_head'):
        blade(bm, layer, design)
    for gem_index, fitting in [(1, design.get('fitting_gem')), (2, design.get('butt_gem'))]:
        if not fitting:
            continue
        x0, y0, x1, y1 = fitting['bbox']
        w, h = design['image_size']
        scale = 2 / h
        verts = set(bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1)['verts'])
        for vertex in verts:
            vertex.co = Vector(((x0 + x1 - w) / 2 * scale + vertex.co.x * (x1 - x0) / 2 * scale,
                                (h - y0 - y1) / 2 * scale + vertex.co.y * (y1 - y0) / 2 * scale,
                                vertex.co.z * max(.008, (x1 - x0) * scale * .4)))
        for face in bm.faces:
            if all(v in verts for v in face.verts):
                face.material_index = gem_index
                for loop in face.loops:
                    loop[layer].uv = (.5 + loop.vert.co.x * .25, .5 + loop.vert.co.y * .25)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    assert all(len(e.link_faces) == 2 for e in bm.edges), Counter(len(e.link_faces) for e in bm.edges)
    assert all(f.calc_area() > 1e-11 for f in bm.faces)
    materials = [material(icon, clay or design.get('route') == 'meshy_full')]
    gem = design.get('gem_head') or design.get('fitting_gem')
    if gem:
        mat = bpy.data.materials.new(icon + '_gem')
        mat.use_nodes = True
        mat.use_backface_culling = True
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = tuple((c / 255) ** 2.2 for c in gem['colour']) + (1,)
        shader.inputs['Roughness'].default_value = .22
        materials.append(mat)
    if design.get('butt_gem'):
        mat = bpy.data.materials.new(icon + '_butt_gem')
        mat.use_nodes = True
        mat.use_backface_culling = True
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = tuple((c / 255) ** 2.2 for c in design['butt_gem']['colour']) + (1,)
        shader.inputs['Roughness'].default_value = .22
        materials.append(mat)
    obj = pl.to_object('pole_' + icon, bm, materials, 40)
    if gem:
        for polygon in obj.data.polygons:
            if polygon.material_index == 1:
                polygon.use_smooth = not gem.get('faceted', True)
            elif polygon.material_index == 2:
                polygon.use_smooth = False
    if design.get('mesh_head'):
        head_name = 'pole_' + design['mesh_head']
        folder = 'head_clay' if clay else 'codex_tex'
        bpy.ops.import_scene.gltf(filepath=str(HERE / 'work' / folder / (head_name + '_export.glb')))
        head = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o != obj)
        bounds = [Vector([min(v.co[i] for v in head.data.vertices) for i in range(3)]),
                  Vector([max(v.co[i] for v in head.data.vertices) for i in range(3)])]
        w, h = design['image_size']
        scale = 2 / h
        extent = bounds[1] - bounds[0]
        source_head_width = w * scale
        source_head_height = design['head_end'] * scale
        resize = Vector((source_head_width / extent.x, source_head_width / extent.x,
                         source_head_height / extent.z))
        rotation = Matrix.Rotation(-math.pi / 2, 3, 'X')
        for vertex in head.data.vertices:
            co = vertex.co - Vector(((bounds[0].x + bounds[1].x) / 2,
                                     (bounds[0].y + bounds[1].y) / 2, bounds[0].z))
            vertex.co = rotation @ Vector([co[i] * resize[i] for i in range(3)])
            vertex.co.y += 1 - source_head_height - min(.015, source_head_height * .04)
        if design['mesh_head'] == 'staff3':
            # The ram's socket is off-centre inside the skull/horns' overall bounding box.
            neck_y = min(v.co.y for v in head.data.vertices)
            neck = [v.co for v in head.data.vertices if v.co.y <= neck_y + source_head_height * .1]
            socket = Vector(((min(v.x for v in neck) + max(v.x for v in neck)) / 2, 0,
                             (min(v.z for v in neck) + max(v.z for v in neck)) / 2))
            shaft_y, shaft_x, radius = design['shaft_profile'][0]
            offset = Vector(((shaft_x - w / 2) * scale, 0, 0)) - socket
            for vertex in head.data.vertices:
                vertex.co += offset
            assert neck_y < (h / 2 - shaft_y) * scale < neck_y + source_head_height * .1
            assert max(abs((socket + offset)[i] - ((shaft_x - w / 2) * scale if i == 0 else 0))
                       for i in (0, 2)) < 1e-6
            surfaces = [BVHTree.FromPolygons([v.co for v in part.data.vertices],
                                             [tuple(f.vertices) for f in part.data.polygons])
                        for part in (obj, head)]
            assert surfaces[0].overlap(surfaces[1]), 'Ram socket must intersect the shaft tenon'
        for other in bpy.context.scene.objects:
            other.select_set(other in (obj, head))
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.join()
    angle = rest(obj)
    pl.WORK = str(HERE / 'work' / ('clay' if clay else 'finished'))
    export = pl.export(obj, 'pole_' + icon)
    assert len(obj.data.polygons) <= design['tris']
    folder = HERE / 'work/blend'
    folder.mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder / ('pole_' + icon + ('_clay' if clay else '') + '.blend')))
    report = {'icon': icon, 'triangles': len(obj.data.polygons), 'rest_angle_degrees': angle,
              'export': str(Path(export).relative_to(ROOT)), 'construction': 'round profiled haft; ridged bevel-edged closed blade components'}
    (HERE / 'receipts' / ('geometry_' + ('clay_' if clay else '') + icon + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    print('BUILT', icon, report['triangles'], 'triangles, resting pitch', round(angle, 2))

def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    clay = '--clay' in args
    failures = []
    for icon in [a for a in args if not a.startswith('--')]:
        try:
            build_one(icon, clay)
        except Exception as error:
            failures.append({'icon': icon, 'error': str(error)})
            print('BUILD FAILED', icon, repr(error), flush=True)
    (HERE / 'receipts' / ('build_failures_clay.json' if clay else 'build_failures_finished.json')).write_text(
        json.dumps(failures, indent=2) + '\n')
    assert not failures, failures


main()
