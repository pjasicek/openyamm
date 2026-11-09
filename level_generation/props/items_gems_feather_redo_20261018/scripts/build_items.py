"""Mounted Ruby, Yellow Topaz and Diamond, and the Harpy Feather, as real 3D ground items.

The gems reuse the jewellery batch's builders (palette, glass shell over a solid core, bezels, engraved gold trim
tiles) so they match its 88 installed models: opaque parts on one node, glass shells on a second `_glass` node.
The feather is a closed curved vane with a raised rachis and bare calamus, lying on the ground, with parametric UVs
and generated 512 px base colour (cream with brown bars from its icon), metallic-roughness and barb normal maps.

blender --background --python build_items.py -- [icon ...]   -> work/exports/item_<icon>_export.glb
"""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'level_generation/props/items_wip_jewellery/scripts'))
import build_jewellery as jw  # noqa: E402
from surface_detail import engrave  # noqa: E402

TAU = math.tau
jw.PALETTE.update({
    'garnet_enamel': ('7a0c1c', 0, .3),
    'blackened': ('1c150e', 0, .55),
    # The icons' stones are more saturated than the batch's loose-gem palette.
    'ruby': ('a80818', 0, .14),
    'topaz': ('e8a000', 0, .15),
    'moonblue': ('8db6f0', 0, .12),
})
jw.GEM_COLOURS.update({'ruby', 'topaz', 'moonblue'})


def closed_tube(name, points, radius, mat, sides=6):
    """A closed ring swept along a closed path (no caps)."""
    vertices = []
    count = len(points)
    for i, p in enumerate(points):
        p = Vector(p)
        tangent = (Vector(points[(i + 1) % count]) - Vector(points[i - 1])).normalized()
        normal = Vector((0, 0, 1)).cross(tangent).normalized()
        other = tangent.cross(normal)
        for j in range(sides):
            a = TAU * j / sides
            vertices.append(p + radius * (normal * math.cos(a) + other * math.sin(a)))
    faces = [(i * sides + j, i * sides + (j + 1) % sides, ((i + 1) % count) * sides + (j + 1) % sides,
              ((i + 1) % count) * sides + j) for i in range(count) for j in range(sides)]
    return jw.mesh(name, [tuple(v) for v in vertices], faces, mat, True)


def flat_tube(name, points, radius, mat, sides=6):
    """An open capped tube for parts lying flat: its frame uses Z as the reference, so it cannot flip between rings
    (the jewellery tube's Y reference twists tubes that run along Y)."""
    vertices = []
    for i, p in enumerate(points):
        p = Vector(p)
        tangent = (Vector(points[min(i + 1, len(points) - 1)]) - Vector(points[max(i - 1, 0)])).normalized()
        normal = Vector((0, 0, 1)).cross(tangent).normalized()
        other = tangent.cross(normal)
        for j in range(sides):
            a = TAU * j / sides
            vertices.append(p + radius * (normal * math.cos(a) + other * math.sin(a)))
    count = len(points)
    faces = [(i * sides + j, i * sides + (j + 1) % sides, (i + 1) * sides + (j + 1) % sides, (i + 1) * sides + j)
             for i in range(count - 1) for j in range(sides)]
    faces += [tuple(reversed(range(sides))), tuple((count - 1) * sides + j for j in range(sides))]
    return jw.mesh(name, [tuple(v) for v in vertices], faces, mat, True)


def bead(name, position, radius, mat):
    # A 20-face bead: smoothed vertex normals oppose some facets of so coarse a solid, so it stays faceted.
    obj = jw.ball(name, position, (radius, radius, radius * .8), mat, 0)
    for polygon in obj.data.polygons:
        polygon.use_smooth = False
    return obj


def ruby():
    # Pointed oval gold frame (marquise points top and bottom) with garnet enamel and gold filigree around a large
    # oval cabochon ruby in a raised bezel; small rubies at the sides.
    count = 36
    shape = []
    for i in range(count):
        a = TAU * i / count
        s = math.sin(a)
        shape.append((.40 * math.cos(a) * (1 - .3 * abs(s) ** 4), .42 * s + .1 * math.copysign(abs(s) ** 12, s)))
    base = jw.plate('Back plate', shape, 0, .05, 'gold')
    engrave(base, 0)
    inner = [(x * .9, y * .9) for x, y in shape]
    jw.plate('Garnet enamel field', inner, .05, .018, 'garnet_enamel')
    closed_tube('Outer rim', [(x * .985, y * .985, .06) for x, y in shape], .022, 'gold')
    # Filigree: gold scroll bars radiating between the bezel and the rim, beads between them.
    for i in range(12):
        a = TAU * (i + .5) / 12
        inside = (.27 * math.cos(a), .35 * math.sin(a), .07)
        outside = (.36 * math.cos(a), .41 * math.sin(a), .07)
        middle = ((inside[0] + outside[0]) / 2 + .02 * math.sin(a), (inside[1] + outside[1]) / 2, .085)
        flat_tube('Filigree scroll', [inside, middle, outside], .011, 'gold')
        bead('Filigree bead', (.33 * math.cos(a + TAU / 24), .385 * math.sin(a + TAU / 24), .075), .014, 'gold')
    bezel = jw.hoop('Cabochon bezel', .24, .315, .095, .025, .07, 'gold', 28)
    engrave(bezel, 0, band=True)
    jw.stone('Ruby cabochon', (0, 0, .06), (.44, .64, .28), 'ruby', 'pearl')
    for side in (-1, 1):
        jw.hoop('Side setting', .045, .055, .085, .012, .04, 'gold', 12).location.x = side * .325
        jw.stone('Side ruby', (side * .325, 0, .07), (.08, .1, .07), 'ruby', 'pearl')
        bead('Point bead', (0, side * .49, .055), .024, 'gold')
    for i in range(4):
        a = TAU * (i + .5) / 4
        bead('Bezel claw', (.25 * math.cos(a), .325 * math.sin(a), .14), .02, 'gold')


def rounded_rectangle(width, height, radius, corner_steps=4):
    points = []
    for cx, cy, start in ((width / 2 - radius, height / 2 - radius, 0), (-width / 2 + radius, height / 2 - radius, 90),
                          (-width / 2 + radius, -height / 2 + radius, 180), (width / 2 - radius, -height / 2 + radius, 270)):
        for k in range(corner_steps + 1):
            a = math.radians(start + 90 * k / corner_steps)
            points.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return points


def topaz():
    # Blackened metal tray with a beaded gold border, a stepped inner frame and an emerald-cut yellow topaz held by
    # four gold claws.
    outline = rounded_rectangle(.78, 1.0, .09)
    jw.plate('Blackened tray', outline, 0, .07, 'blackened')
    closed_tube('Tray rim', [(x * .99, y * .99, .072) for x, y in rounded_rectangle(.76, .98, .085)], .016,
                'blackened')
    path = rounded_rectangle(.66, .88, .06, 3)
    # Evenly spaced beads along the rounded rectangle.
    lengths = [0]
    for i in range(len(path)):
        a, b = Vector(path[i]), Vector(path[(i + 1) % len(path)])
        lengths.append(lengths[-1] + (b - a).length)
    total = lengths[-1]
    for k in range(30):
        d = total * k / 30
        i = max(j for j in range(len(path)) if lengths[j] <= d)
        a, b = Vector(path[i]), Vector(path[(i + 1) % len(path)])
        p = a.lerp(b, (d - lengths[i]) / max((b - a).length, 1e-6))
        bead('Border bead', (p.x, p.y, .078), .022, 'gold')
    jw.plate('Inner frame', rounded_rectangle(.54, .76, .04), .07, .03, 'blackened')
    jw.setting(0, 0, .1, .46, .66, 'topaz', 'gold', 'emerald')
    for sx in (-1, 1):
        for sy in (-1, 1):
            bead('Corner claw', (sx * .235, sy * .335, .16), .03, 'gold')


def diamond():
    # Large round brilliant, pale blue-white, in a gold bezel ringed by irregular gold leaf claws, on a gold back.
    back = jw.plate('Gold back', [(math.cos(TAU * i / 32) * .46, math.sin(TAU * i / 32) * .48) for i in range(32)],
                    0, .05, 'gold')
    engrave(back, 0)
    bezel = jw.hoop('Scalloped bezel', .37, .39, .09, .045, .08, 'gold', 32)
    engrave(bezel, 0, band=True)
    for i in range(10):
        a = TAU * i / 10 + .12 * math.sin(i * 2.3)
        leaf = jw.ball('Leaf claw', (.45 * math.cos(a), .47 * math.sin(a), .08), (.075, .045, .035), 'gold', 1)
        leaf.rotation_euler.z = a + math.pi / 2
        bead('Leaf bead', (.36 * math.cos(a + .31), .38 * math.sin(a + .31), .15), .022, 'gold')
    jw.stone('Brilliant', (0, 0, .07), (.64, .68, .36), 'moonblue', 'round')


FEATHER_TEXTURE = 512
RACHIS_U = (.94, 1.0)


def feather_textures():
    """Cream vane with brown bars running back from the rachis (chevrons), darker tip, golden rachis column."""
    n = FEATHER_TEXTURE
    u, v = np.meshgrid((np.arange(n) + .5) / n, (np.arange(n) + .5) / n)
    # Texture u (x) in [0, .94): across the vane, .47 = rachis line; v (y): along the feather, 0 base, 1 tip.
    across = (u / .94 - .5) * 2
    bars = .5 + .5 * np.sin(TAU * (v * 12 + np.abs(across) * 1.6))
    bars = np.clip((bars - .45) * 4, 0, 1) * (.5 + .5 * np.clip(np.abs(across) * 1.6, 0, 1))
    cream = np.array([.74, .62, .47])
    brown = np.array([.36, .19, .09])
    rose = np.array([.70, .52, .50])
    colour = cream * (1 - bars[..., None]) + brown * bars[..., None]
    colour = colour * (1 - .2 * np.clip(np.abs(across) - .7, 0, 1)[..., None]) + rose * .08
    colour *= (1 - .25 * np.clip(v - .85, 0, 1) / .15)[..., None]
    rachis = u >= RACHIS_U[0]
    colour[rachis] = np.array([.72, .52, .26]) * (.9 + .1 * np.sin(TAU * v[rachis] * 3))[..., None]
    roughness = np.where(rachis, .45, .72)
    # Barbs: fine grooves angled back from the rachis.
    height = .5 + .5 * np.sin(TAU * (v * 70 + np.abs(across) * 20))
    height[rachis] = .5
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * .5
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * .5
    normal = np.stack([-dx * 1.2, -dy * 1.2, np.ones_like(dx)], -1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    mr = np.stack([np.ones_like(roughness), roughness, np.zeros_like(roughness)], -1)
    images = {}
    for name, data, colorspace in (('basecolor', colour, 'sRGB'), ('mr', mr, 'Non-Color'),
                                   ('normal', normal * .5 + .5, 'Non-Color')):
        image = bpy.data.images.new(f'item_quill_{name}', n, n, alpha=False)
        image.colorspace_settings.name = colorspace
        rgba = np.concatenate([np.clip(data, 0, 1), np.ones((n, n, 1))], -1).astype(np.float32)
        image.pixels[:] = rgba.ravel()
        image.file_format = 'PNG'
        image.pack()
        images[name] = image
    material = bpy.data.materials.new('item_quill')
    material.use_nodes = True
    material.use_backface_culling = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes['Principled BSDF']
    base = nodes.new('ShaderNodeTexImage')
    base.image = images['basecolor']
    links.new(base.outputs['Color'], shader.inputs['Base Color'])
    mr_node = nodes.new('ShaderNodeTexImage')
    mr_node.image = images['mr']
    separate = nodes.new('ShaderNodeSeparateColor')
    links.new(mr_node.outputs['Color'], separate.inputs['Color'])
    links.new(separate.outputs['Green'], shader.inputs['Roughness'])
    links.new(separate.outputs['Blue'], shader.inputs['Metallic'])
    normal_node = nodes.new('ShaderNodeTexImage')
    normal_node.image = images['normal']
    mapping = nodes.new('ShaderNodeNormalMap')
    links.new(normal_node.outputs['Color'], mapping.inputs['Color'])
    links.new(mapping.outputs['Normal'], shader.inputs['Normal'])
    return material


def spine(t):
    """Feather centre line: lying on the ground, gently curved to its left, arched up and lifting at the tip."""
    return Vector((-.07 * math.sin(math.pi * t) - .03 * t * t, t, .022 * math.sin(math.pi * t) + .03 * t ** 4))


def feather():
    material = feather_textures()
    vertices, faces, uvs = [], [], []
    stations = 26
    start = .14
    # Lens cross-section: left edge, three top points, right edge, three bottom points.
    for i in range(stations):
        t = start + (1 - start) * i / (stations - 1)
        s = (t - start) / (1 - start)
        shape = math.sin(math.pi * min(1.0, .1 + s * .95)) ** .55 * (1 - .65 * s ** 6)
        left, right = .135 * shape + .006, .095 * shape + .006
        thickness = .016 * (1 - .6 * s) + .004
        centre = spine(t)
        tangent = (spine(min(1, t + .01)) - spine(max(0, t - .01))).normalized()
        across = Vector((0, 0, 1)).cross(tangent).normalized()
        up = tangent.cross(across).normalized()
        # The vane droops slightly to both edges like a real lying feather.
        points = [(-left, 0, -.006), (-left / 2, thickness / 2, -.002), (0, thickness / 2 + .002, 0),
                  (right / 2, thickness / 2, -.002), (right, 0, -.006), (right / 2, -thickness / 2, -.002),
                  (0, -thickness / 2, 0), (-left / 2, -thickness / 2, -.002)]
        for a, h, droop in points:
            vertices.append(centre + across * a + up * (h + droop))
        width = left + right
        for a, h, droop in points:
            uvs.append(((a + left) / width * .94 * .999, s))
    ring = 8
    for i in range(stations - 1):
        for k in range(ring):
            faces.append((i * ring + k, i * ring + (k + 1) % ring, (i + 1) * ring + (k + 1) % ring,
                          (i + 1) * ring + k))
    faces.append(tuple(reversed(range(ring))))
    tip = len(vertices)
    end = spine(1.0)
    vertices.append(end + (end - spine(.99)).normalized() * .012)
    uvs.append((.47, 1.0))
    last = (stations - 1) * ring
    faces += [(last + k, last + (k + 1) % ring, tip) for k in range(ring)]
    vane = len(faces)
    # Rachis: a round shaft from the bare calamus at the base along the top of the vane, thinning to the tip.
    offset = len(vertices)
    shaft = 22
    sides = 6
    for i in range(shaft):
        t = .97 * i / (shaft - 1)
        radius = .013 * (1 - .75 * t) + .002
        centre = spine(t) + Vector((0, 0, .008 if t > start else 0))
        tangent = (spine(min(1, t + .01)) - spine(max(0, t - .01))).normalized()
        across = Vector((0, 0, 1)).cross(tangent).normalized()
        up = tangent.cross(across).normalized()
        for k in range(sides):
            a = TAU * k / sides
            vertices.append(centre + radius * (across * math.cos(a) + up * math.sin(a)))
            uvs.append((RACHIS_U[0] + (RACHIS_U[1] - RACHIS_U[0]) * k / sides * .999, t))
    for i in range(shaft - 1):
        for k in range(sides):
            faces.append((offset + i * sides + k, offset + i * sides + (k + 1) % sides,
                          offset + (i + 1) * sides + (k + 1) % sides, offset + (i + 1) * sides + k))
    faces.append(tuple(offset + k for k in reversed(range(sides))))
    faces.append(tuple(offset + (shaft - 1) * sides + k for k in range(sides)))
    data = bpy.data.meshes.new('item_quill')
    data.from_pydata([tuple(v) for v in vertices], [], faces)
    data.update()
    layer = data.uv_layers.new(name='UVMap')
    for polygon in data.polygons:
        for loop in polygon.loop_indices:
            layer.data[loop].uv = uvs[data.loops[loop].vertex_index]
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new('item_quill', data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(material)
    for polygon in data.polygons:
        polygon.use_smooth = True
    print('FEATHER vane faces', vane)


BUILDERS = {'7item146': ruby, '7item154': topaz, '7item264': diamond, 'quill': feather}


def finish(icon):
    """The jewellery batch's export: opaque parts joined on one node, glass shells on a `_glass` node; centred,
    grounded, longest side along glTF Z; closed manifold parts only."""
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for obj in objects:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        if not obj.data.uv_layers:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(island_margin=.015)
            bpy.ops.object.mode_set(mode='OBJECT')
        assert len(obj.data.uv_layers) == 1, obj.name
        obj.data.uv_layers.active.name = 'UVMap'
    name = 'item_' + icon
    groups = [[obj for obj in objects if bool(obj.get('jewellery_glass')) == glass] for glass in (False, True)]
    objects = []
    for group in groups:
        if not group:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        if len(group) > 1:
            bpy.ops.object.join()
        obj = bpy.context.object
        obj.name = name + ('_glass' if obj.get('jewellery_glass') else '')
        objects.append(obj)
    points = [v.co for obj in objects for v in obj.data.vertices]
    low = Vector([min(p[i] for p in points) for i in range(3)])
    high = Vector([max(p[i] for p in points) for i in range(3)])
    shift = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    triangles = 0
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        for vertex in obj.data.vertices:
            vertex.co -= shift
        if high.x - low.x > high.y - low.y:
            obj.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Z'))
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        assert all(edge.is_manifold for edge in bm.edges), icon + ': open component'
        assert all(face.calc_area() > 1e-10 for face in bm.faces), icon + ': degenerate face'
        triangles += len(bm.faces)
        bm.to_mesh(obj.data)
        bm.free()
        obj.select_set(True)
    assert 0 < triangles <= 3200, (icon, triangles)
    export = PROJECT / 'work/exports' / f'{name}_export.glb'
    export.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT / 'work' / f'{name}.blend'))
    bpy.ops.export_scene.gltf(filepath=str(export), export_format='GLB', use_selection=True, export_yup=True,
                              export_materials='EXPORT', export_cameras=False, export_animations=False,
                              export_extras=True)
    return {'icon': icon, 'export': str(export.relative_to(PROJECT)), 'triangles': triangles,
            'size': [round(high[i] - low[i], 4) for i in range(3)]}


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    receipts = PROJECT / 'work/build_receipts.json'
    records = json.loads(receipts.read_text()) if receipts.exists() else {}
    for icon in args or list(BUILDERS):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        jw.MATERIALS.clear()
        BUILDERS[icon]()
        records[icon] = finish(icon)
        receipts.write_text(json.dumps(records, indent=2) + '\n')
        print('BUILT', icon, records[icon]['triangles'], records[icon]['size'], flush=True)


if __name__ == '__main__':
    main()
