"""Twelve letters, documents and a quill as real 3D ground items, consistent with the scrolls batch.

- Sealed letters 7item252-7item258: the scrolls batch's folded envelope (closed body and overlapping flaps, its
  `7item251` parchment) with a raised emblem extruded from the Codex emblem painting's own mask, so its silhouette
  and painted colours coincide; placed and sized as on each icon.
- item266 False Report: a landscape folded sheet with a folded-down flap and a raised red rosette wax seal.
- item318 Forged Vouchers: the scrolls batch's closed thick sheet, rolled at one end and lifting at the other.
- item320 Prophecies of the Snake: a closed book (boards, page block, rounded spine) carrying the Codex cover and
  spine paintings, with the gold snake head raised from the cover.
- 7item247 Parson's Quill: the harpy feather's closed vane and rachis (items_gems_feather_redo_20261018) with a
  peacock vane: green barbs and an eye spot near the tip.
Every part is a closed solid; one material per item (one 512 px PBR atlas), single-sided.

Usage: blender --background --python build_letters.py -- [icon ...]   -> work/exports/item_<icon>_export.glb"""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT / 'level_generation/props/items_wip_scrolls_20261018/scripts'))
import build_scrolls as bs  # noqa: E402

bs.P = P
TAU = math.tau
ENVELOPE_TOP = .037
# Emblem footprint on each icon: centre and size in envelope-relative units (x from left, y from top).
EMBLEMS = {'7item252': (.48, .49, .32, .36), '7item253': (.50, .53, .38, .39), '7item254': (.50, .52, .48, .43),
           '7item255': (.535, .445, .57, .39), '7item256': (.50, .485, .36, .75), '7item257': (.50, .515, .50, .45),
           '7item258': (.49, .51, .36, .50)}


def relief_data(icon):
    data = np.load(P / 'textures' / f'{icon}_relief.npz')
    return data['small'], data['dist'], tuple(int(v) for v in data['size']), int(data['pool'])


def relief(name, data, place, uv_of, thickness, base_z, mat, budget=900, edge=4.0):
    """A raised closed solid from a mask prepared by prepare_textures.relief_data: a stepped heightfield (domed by
    distance to the silhouette), voxel-merged and smoothed, then reduced; top-down UVs from the mask's own pixels.
    place(px, py) -> (x, y) in model units; uv_of(px, py) -> (u, v), both in full-resolution mask pixels."""
    small, distance, (w, h), pool = data
    height = thickness * np.clip(distance / edge, 0, 1) ** .5
    rows, cols = small.shape
    corner = {}
    vertices, faces = [], []

    def vertex(i, j, top):
        key = (i, j, top)
        if key not in corner:
            if top:
                around = [height[a, b] for a in (i - 1, i) for b in (j - 1, j)
                          if 0 <= a < rows and 0 <= b < cols and small[a, b]]
                z = base_z + (sum(around) / len(around) if around else 0)
            else:
                z = base_z - .004
            x, y = place(j * pool, i * pool)
            corner[key] = len(vertices)
            vertices.append((x, y, z))
        return corner[key]

    for i in range(rows):
        for j in range(cols):
            if not small[i, j]:
                continue
            faces.append((vertex(i, j, 1), vertex(i + 1, j, 1), vertex(i + 1, j + 1, 1), vertex(i, j + 1, 1)))
            faces.append((vertex(i, j + 1, 0), vertex(i + 1, j + 1, 0), vertex(i + 1, j, 0), vertex(i, j, 0)))
            for (di, dj), (a, b) in (((-1, 0), ((i, j), (i, j + 1))), ((1, 0), ((i + 1, j + 1), (i + 1, j))),
                                     ((0, -1), ((i + 1, j), (i, j))), ((0, 1), ((i, j + 1), (i + 1, j + 1)))):
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols and small[ni, nj]:
                    continue
                faces.append((vertex(*a, 1), vertex(*a, 0), vertex(*b, 0), vertex(*b, 1)))
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    pixel = abs(place(pool, 0)[0] - place(0, 0)[0])
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    data.remesh_voxel_size = pixel * .7
    bpy.context.view_layer.objects.active = obj
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
        bpy.ops.object.voxel_remesh()
        smooth = obj.modifiers.new('relax', 'SMOOTH')
        smooth.factor, smooth.iterations = .5, 3
        bpy.ops.object.modifier_apply(modifier=smooth.name)
        data.calc_loop_triangles()
        if len(data.loop_triangles) > budget:
            decimate = obj.modifiers.new('budget', 'DECIMATE')
            decimate.ratio = budget / len(data.loop_triangles)
            decimate.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=decimate.name)
    # Collapse reduction leaves a few folded-over slivers (normal against their neighbours, shading dark):
    # collapse each one's shortest edge, then re-orient the shell outward.
    bm = bmesh.new()
    bm.from_mesh(data)
    for _ in range(8):
        bm.normal_update()
        folded = []
        for face in bm.faces:
            around = [other.normal for edge in face.edges for other in edge.link_faces if other is not face]
            mean = sum(around, Vector()) if around else Vector()
            if mean.length > 1e-9 and face.normal.dot(mean.normalized()) < -.2:
                folded.append(min(face.edges, key=lambda e: e.calc_length()))
        if not folded:
            break
        bmesh.ops.collapse(bm, edges=list(set(folded)))
        bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    # Top-down UVs: invert place() (axis-aligned, uniform) back to mask pixels.
    (x0, y0), (x1, y1) = place(0, 0), place(w, h)
    layer = data.uv_layers.new(name='UVMap')
    for polygon in data.polygons:
        polygon.use_smooth = True
        for loop in polygon.loop_indices:
            co = data.vertices[data.loops[loop].vertex_index].co
            px = (co.x - x0) / (x1 - x0) * w
            py = (co.y - y0) / (y1 - y0) * h
            layer.data[loop].uv = uv_of(min(max(px, 0), w - 1), min(max(py, 0), h - 1))
    data.materials.append(mat)
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
    return obj


def emblem_uv(px, py):
    # Emblem tile: bottom-left atlas quadrant, mask pixel rows from the top of the tile.
    return (px / 256 / 2, (1 - py / 256) / 2)


def place_emblem(data, centre_x, centre_y, width, height):
    """Fit the mask's own bounding box uniformly into the icon footprint (model units), centred on it."""
    small, _, _, pool = data
    ys, xs = np.nonzero(small)
    ys, xs = ys * pool, xs * pool
    mw, mh = xs.max() - xs.min() + pool, ys.max() - ys.min() + pool
    scale = min(width / mw, height / mh)
    mx, my = (xs.min() + xs.max() + pool) / 2, (ys.min() + ys.max() + pool) / 2
    return lambda px, py: (centre_x + (px - mx) * scale, centre_y - (py - my) * scale)


def envelope_body(mat):
    """The scrolls batch's folded envelope (`build_scrolls.envelope`) without its round wax seal."""
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
        uvs = [bs.uv_tile([(vertices[i][0] + .5, vertices[i][1] / .78 + .5) for i in f], 'front') for f in faces]
        bs.mesh('Folded letter' if level == 0 else f'Overlapping flap {level}', vertices, faces, mat, uvs, False)


def sealed_letter(icon):
    mat = bs.material(icon)
    envelope_body(mat)
    data = relief_data(icon)
    cx, cy, w, h = EMBLEMS[icon]
    place = place_emblem(data, cx - .5, .39 - cy * .78, w, h * .78)
    relief('Raised emblem', data, place, emblem_uv, .026, ENVELOPE_TOP - .004, mat)


def folded_report(icon):
    mat = bs.material(icon)
    for name, (y0, y1, z0, z1, tile) in {'Folded sheet': (-.31, .31, .003, .015, 'back'),
                                          'Folded-down flap': (-.035, .31, .011, .023, 'front')}.items():
        outline = [(-.5, y0), (.5, y0), (.5, y1), (-.5, y1)]
        if name == 'Folded-down flap':
            # A slightly uneven folded edge.
            outline = [(-.5, y1), (-.5, y0 + .012), (-.2, y0 - .004), (.15, y0 + .006), (.5, y0 - .002), (.5, y1)]
        vertices = [(x, y, z) for z in (z0, z1) for x, y in outline]
        n = len(outline)
        faces = [tuple(reversed(range(n))), tuple(range(n, n * 2))]
        faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
        uvs = [bs.uv_tile([(vertices[i][0] + .5, vertices[i][1] / .62 + .5) for i in f], tile) for f in faces]
        bs.mesh(name, vertices, faces, mat, uvs, False)
    data = relief_data(icon)
    place = place_emblem(data, 0, .31 - .46 * .62, .24, .24)
    relief('Raised rosette wax seal', data, place, emblem_uv, .03, .019, mat)


def vouchers(icon):
    """Mostly rolled, as on the icon: a fat roll of about two turns, a short flat tail and a lifted end."""
    mat = bs.material(icon)
    path = []
    turns, steps = 2.2, 44
    centre_y, radius = -.12, .085
    # From the inside of the roll outward, finishing at its bottom where the tail leaves it.
    for i in range(steps + 1):
        t = i / steps
        angle = -math.pi / 2 - turns * TAU * (1 - t)
        r = .03 + (radius - .03) * t
        path.append((centre_y + r * math.cos(angle), .006 + radius + r * math.sin(angle), .45 * t))
    for i in range(1, 7):
        t = i / 6
        path.append((centre_y + .32 * t, .004 + .003 * math.sin(math.pi * t), .45 + .4 * t))
    for i in range(1, 6):
        t = i / 5
        path.append((centre_y + .32 + .1 * math.sin(1.1 * t), .004 + .06 * (1 - math.cos(1.1 * t)), .85 + .15 * t))
    bs.sheet('Forged voucher sheet, mostly rolled', path, .62, mat, aged=True, thickness=.005)


def book(icon):
    mat = bs.material(icon)
    W, H, T, B, O = 1.0, .667, .2, .032, .022
    leather = (.87, .75)

    def box(name, x0, x1, y0, y1, z0, z1, top=None, sides=None):
        vertices = [(x, y, z) for z in (z0, z1) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        uvs = []
        for index, face in enumerate(faces):
            if index == 1 and top:
                uvs.append([top(vertices[i][0], vertices[i][1]) for i in face])
            elif index > 1 and sides:
                uvs.append([sides(vertices[i], index) for i in face])
            else:
                uvs.append([leather] * 4)
        bs.mesh(name, vertices, faces, mat, uvs, False)

    def cover_uv(x, y):
        return (x / W * .75, .5 + y / H * .5)

    def pages_uv(point, index):
        along = point[1] / H if index in (3, 5) else point[0] / W
        across = (point[2] - B) / (T - 2 * B)
        return (.02 + .71 * along, .26 + .1 * min(max(across, 0), 1))

    box('Back board', 0, W, 0, H, 0, B)
    box('Front board', 0, W, 0, H, T - B, T, top=cover_uv)
    box('Page block', .02, W - O, O, H - O, B - .003, T - B + .003, sides=pages_uv)
    # Rounded spine: a closed half-round solid along the book's height at x = 0.
    segments = 8
    radius = T / 2
    profile = [(-radius * .5 * math.sin(math.pi * i / segments), radius - radius * math.cos(math.pi * i / segments))
               for i in range(segments + 1)]
    profile.append((.03, T))
    profile.append((.03, 0))
    vertices = [(x, y, z) for y in (-.002, H + .002) for x, z in profile]
    n = len(profile)
    faces = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
    uvs = [[leather] * n, [leather] * n]
    for i in range(n):
        k = (i + 1) % n
        faces.append((i, i + n, k + n, k))
        if i < segments:
            uvs.append([(.75 * 0, .375 + .125 * i / segments), (.75, .375 + .125 * i / segments),
                        (.75, .375 + .125 * (i + 1) / segments), (0, .375 + .125 * (i + 1) / segments)])
        else:
            uvs.append([leather] * 4)
    bs.mesh('Rounded spine', vertices, faces, mat, uvs, True, flat_start=2 + segments)
    relief('Raised gold snake head', relief_data(icon), lambda px, py: (px / 384 * W, H - py / 256 * H),
           lambda px, py: (px / 512, 1 - py / 512), .03, T - .004, mat, budget=1100, edge=5.0)


def quill(icon):
    sys.path.insert(0, str(ROOT / 'level_generation/props/items_gems_feather_redo_20261018/scripts'))
    import build_items as gi

    def peacock_textures():
        n = gi.FEATHER_TEXTURE
        u, v = np.meshgrid((np.arange(n) + .5) / n, (np.arange(n) + .5) / n)
        across = (u / .94 - .5) * 2
        # Green barbs with bronze sheen toward the edges, an eye spot near the tip.
        green = np.array([.08, .42, .12])
        bronze = np.array([.42, .36, .08])
        colour = green * (1 - .35 * np.abs(across)[..., None]) + bronze * (.35 * np.abs(across) ** 2)[..., None]
        streak = .5 + .5 * np.sin(TAU * (v * 60 + np.abs(across) * 14))
        colour *= (.8 + .25 * streak)[..., None]
        eye = ((across / .8) ** 2 + ((v - .74) / .17) ** 2) ** .5
        for radius, tint in ((1.0, (.42, .34, .1)), (.78, (.05, .45, .42)), (.55, (.1, .55, .55)),
                             (.42, (.04, .12, .42)), (.25, (.02, .04, .2))):
            colour[eye < radius] = tint
        colour *= (1 - .3 * np.clip(v - .95, 0, 1) / .05)[..., None]
        rachis = u >= gi.RACHIS_U[0]
        colour[rachis] = np.array([.62, .72, .5])
        roughness = np.where(rachis, .4, .55)
        height = .5 + .5 * np.sin(TAU * (v * 70 + np.abs(across) * 20))
        height[rachis] = .5
        dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * .5
        dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * .5
        normal = np.stack([-dx * 1.2, -dy * 1.2, np.ones_like(dx)], -1)
        normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
        mr = np.stack([np.ones_like(roughness), roughness, np.zeros_like(roughness)], -1)
        return pack('item_7item247', colour, mr, normal * .5 + .5)

    gi.feather_textures = peacock_textures
    gi.feather()


def pack(name, colour, mr, normal):
    n = colour.shape[0]
    images = {}
    for kind, data, colorspace in (('basecolor', colour, 'sRGB'), ('mr', mr, 'Non-Color'),
                                   ('normal', normal, 'Non-Color')):
        image = bpy.data.images.new(f'{name}_{kind}', n, n, alpha=False)
        image.colorspace_settings.name = colorspace
        image.pixels[:] = np.concatenate([np.clip(data, 0, 1), np.ones((n, n, 1))], -1).astype(np.float32).ravel()
        image.file_format = 'PNG'
        image.pack()
        images[kind] = image
    material = bpy.data.materials.new(name)
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


BUILDERS = {**{icon: sealed_letter for icon in EMBLEMS}, 'item266': folded_report, 'item318': vouchers,
            'item320': book, '7item247': quill}


def finish(icon):
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for obj in objects:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    coords = [v.co for o in objects for v in o.data.vertices]
    low = Vector([min(p[i] for p in coords) for i in range(3)])
    high = Vector([max(p[i] for p in coords) for i in range(3)])
    centre = (low + high) / 2
    # Longest footprint side along Blender Y (glTF Z), resting on Z = 0, footprint centred.
    rotate = high.x - low.x > high.y - low.y
    for obj in objects:
        for v in obj.data.vertices:
            x, y, z = v.co.x - centre.x, v.co.y - centre.y, v.co.z - low.z
            v.co = (-y, x, z) if rotate else (x, y, z)
        obj.data.update()
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = f'item_{icon}'
    materials = list(obj.data.materials)
    obj.data.materials.clear()
    obj.data.materials.append(materials[0])
    for polygon in obj.data.polygons:
        polygon.material_index = 0
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    triangles = len(bm.faces)
    bm.free()
    # Near-degenerate slivers left by reduction can get a smoothed normal facing away from the face; shade them flat
    # (their own normal) until no corner normal opposes its face.
    for _ in range(6):
        mesh = obj.data
        flipped = [polygon for polygon in mesh.polygons
                   if polygon.use_smooth and min(mesh.corner_normals[i].vector.dot(polygon.normal)
                                                 for i in polygon.loop_indices) < .05]
        if not flipped:
            break
        for polygon in flipped:
            polygon.use_smooth = False
        mesh.update()
    out = P / 'work/exports'
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / f'{icon}.blend'))
    bpy.ops.export_scene.gltf(filepath=str(out / f'item_{icon}_export.glb'), export_format='GLB',
                              use_selection=True, export_yup=True, export_animations=False, export_cameras=False,
                              export_lights=False)
    return {'triangles': triangles, 'size': [round(high[i] - low[i], 4) for i in range(3)]}


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    receipts = P / 'work/build_receipts.json'
    records = json.loads(receipts.read_text()) if receipts.exists() else {}
    for icon in args or list(BUILDERS):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bs.UV_LAYOUT.clear()
        BUILDERS[icon](icon)
        records[icon] = finish(icon)
        receipts.write_text(json.dumps(records, indent=2) + '\n')
        print('BUILT', icon, records[icon], flush=True)


if __name__ == '__main__':
    main()
