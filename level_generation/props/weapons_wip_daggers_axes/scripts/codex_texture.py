"""Prepare owned sculptural weapons and bake six Codex-painted views into 1K PBR maps.
Closed source topology, supported ground pose, UV seams and neutral guides precede painting. Visibility-weighted
projection uses separate metal/organic/gem/bone masks; fixed class roughness is independent of colour. Normal detail
uses only fine paint variation, in glTF +Y convention. Raw paintings and per-view registrations remain reviewable.
Usage: Blender --background --python codex_texture.py -- prep|bake w02_<icon> ...
"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'projectiles_claude',
                                'scripts'))
import projlib as pl  # noqa: E402
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rest_pose import rest_weapon
from repair_topology import repair

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESHY = os.path.join(HERE, 'meshy', 'meshy')
WORK = os.path.join(HERE, 'work', 'codex_tex')
PAINT = os.path.join(HERE, 'codex_tex')
GUIDE = 512
TEXTURE = 1024
# View name: direction from the object toward the camera.
VIEWS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (-1, 0, 0), 'right': (1, 0, 0),
         'top': (0, 0, 1), 'bottom': (0, 0, -1)}
# designs.json: per design its triangle budget ('tris', reduced before the unwrap when Meshy gave more), metallic,
# roughness range (dark .. bright painting) and normal strength.
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))


def clean_normals(obj):
    # Vertex rotations require recalculated geometry normals rather than imported custom normals.
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        if obj.data.has_custom_normals:
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    pl.fix_winding(obj)
    obj.data.update()


def unwrap(obj):
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(40), island_margin=0.01)
        bpy.ops.object.mode_set(mode='OBJECT')
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.active
    for edge in bm.edges:
        if len(edge.link_faces) != 2:
            edge.seam = True
            continue
        a, b = [{loop.vert: loop[uv].uv.copy() for loop in face.loops} for face in edge.link_faces]
        hard = edge.calc_face_angle() > math.radians(40)
        edge.smooth = not hard
        edge.seam = hard or any((a[vertex] - b[vertex]).length > 1e-5 for vertex in edge.verts)
    bm.to_mesh(obj.data)
    bm.free()
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.01)
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(margin=0.006)
        bpy.ops.object.mode_set(mode='OBJECT')
    # A seam ending inside an island can stay joined; isolate the few affected triangles before packing again.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.active
    isolated = 0
    for edge in bm.edges:
        if len(edge.link_faces) != 2 or edge.calc_face_angle() <= math.radians(40):
            continue
        a, b = [{loop.vert: loop[uv].uv.copy() for loop in face.loops} for face in edge.link_faces]
        if all((a[vertex] - b[vertex]).length < 1e-5 for vertex in edge.verts):
            for border in min(edge.link_faces, key=lambda face: face.calc_area()).edges:
                border.seam = True
            isolated += 1
    bm.to_mesh(obj.data)
    bm.free()
    if isolated:
        with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.01)
            bpy.ops.uv.average_islands_scale()
            bpy.ops.uv.pack_islands(margin=0.006)
            bpy.ops.object.mode_set(mode='OBJECT')


def view_frame(direction):
    d = Vector(direction).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    right = up.cross(d).normalized()
    return d, right, d.cross(right).normalized()


def prep(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MESHY, f'{name}_st_v1', 'model_urls_glb.glb'))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in bpy.context.scene.objects:
        o.select_set(o in meshes)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for other in list(bpy.context.scene.objects):
        if other != obj:
            bpy.data.objects.remove(other)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(obj.data)
    bm.free()
    report=repair(obj,DESIGNS[name].get('seam_union_voxel'),DESIGNS[name].get('tris',5500))
    with open(os.path.join(HERE,'work',f'{name}_topology_repair.json'),'w') as handle:json.dump(report,handle,indent=2)
    rotation = DESIGNS[name].get('rest_rotation_degrees', [0, 0, 0])
    for axis, degrees in zip('XYZ', rotation):
        if degrees:
            matrix = Matrix.Rotation(math.radians(degrees), 3, axis)
            for vertex in obj.data.vertices:
                vertex.co = matrix @ vertex.co
    support = rest_weapon([obj])
    with open(os.path.join(HERE, 'work', f'{name}_support.json'), 'w') as handle:
        json.dump(support, handle, indent=2)
    xs, ys, zs = ([v.co[i] for v in obj.data.vertices] for i in range(3))
    shift = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    for v in obj.data.vertices:
        v.co -= shift
    if max(xs) - min(xs) > max(ys) - min(ys):
        for vertex in obj.data.vertices:
            vertex.co.x, vertex.co.y = -vertex.co.y, vertex.co.x
    if DESIGNS[name].get('hybrid_head'):
        from hybrid_amuck import rebuild
        obj=rebuild(obj)
        rest_weapon([obj])
    if DESIGNS[name].get('hybrid_grip'):
        import build_weapons as weapons
        weapons.material();z=(min(v.co.z for v in obj.data.vertices)+max(v.co.z for v in obj.data.vertices))/2
        grip=weapons.tube('closed leather grip',[(0,-.35,z),(0,-.065,z)],.022,'brown',12)
        for y in [-.35,-.065]:weapons.tube('tang collar',[(0,y-.008,z),(0,y+.008,z)],.026,'iron',12)
        bpy.ops.object.select_all(action='DESELECT')
        for ob in bpy.context.scene.objects:ob.select_set(ob.type=='MESH')
        bpy.context.view_layer.objects.active=obj;bpy.ops.object.join();rest_weapon([obj])
    obj.name = name
    clean_normals(obj)
    if DESIGNS[name].get('voxel_cleanup'):
        modifier = obj.modifiers.new('Remove intersecting interior sheets', 'REMESH')
        modifier.mode = 'VOXEL'
        modifier.voxel_size = DESIGNS[name]['voxel_cleanup']
        modifier.use_smooth_shade = True
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    budget = DESIGNS[name].get('tris')
    triangles = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    if budget and triangles > budget:
        modifier = obj.modifiers.new('decimate', 'DECIMATE')
        modifier.ratio = budget / triangles
        modifier.use_collapse_triangulate = True
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    unwrap(obj)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(os.path.join(PAINT, name), exist_ok=True)
    # Guides: grey clay, soft light from the camera side, orthographic, one framing for all views.
    material = bpy.data.materials.new('clay')
    material.use_nodes = True
    bsdf = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (0.55, 0.55, 0.55, 1)
    bsdf.inputs['Roughness'].default_value = 0.8
    obj.data.materials.clear()
    obj.data.materials.append(material)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 8
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 6
    scene.render.resolution_x = scene.render.resolution_y = GUIDE
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('w')
    scene.world = world
    world.use_nodes = True
    background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    background.inputs['Color'].default_value = (1, 1, 1, 1)
    background.inputs['Strength'].default_value = 0.6
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    centre = (lo + hi) / 2
    scale = max(hi - lo) * 1.15
    camera = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = scale
    scene.collection.objects.link(camera)
    scene.camera = camera
    light = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN'))
    light.data.energy = 2.5
    scene.collection.objects.link(light)
    for view, direction in VIEWS.items():
        d, right, up = view_frame(direction)
        camera.matrix_world = Matrix((right, up, d)).transposed().to_4x4()
        camera.location = centre + d * max(hi - lo) * 3
        assert right.cross(up).dot(d) > .999
        light.rotation_euler = (-(d + up * 0.6 + right * 0.3)).normalized().to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(PAINT, name, f'guide_{view}.png')
        bpy.ops.render.render(write_still=True)
    with open(os.path.join(PAINT, name, 'views.json'), 'w') as handle:
        json.dump({'centre': list(centre), 'scale': scale, 'size': GUIDE, 'views': VIEWS}, handle, indent=1)
    bpy.data.objects.remove(camera)
    bpy.data.objects.remove(light)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{name}.blend'))
    print('PREP', name, len(obj.data.polygons), 'faces, guides in', os.path.join(PAINT, name))


def load_rgba(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    rgba = np.array(image.pixels[:], np.float32).reshape(height, width, 4)[::-1].copy()
    bpy.data.images.remove(image)
    return rgba


def bbox(alpha):
    ys, xs = np.nonzero(alpha > 0.5)
    return xs.min(), xs.max(), ys.min(), ys.max()


def erode(mask, steps):
    for _ in range(steps):
        mask = mask & np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1)
    return mask


def bilinear(image, x, y):
    h, w = image.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (image[y0, x0] * (1 - fx) * (1 - fy) + image[y0, x0 + 1] * fx * (1 - fy)
            + image[y0 + 1, x0] * (1 - fx) * fy + image[y0 + 1, x0 + 1] * fx * fy)


def texels(obj):
    """Every covered texel: its pixel, world position and smooth normal (barycentric over the UV triangles)."""
    mesh = obj.data
    mesh.calc_loop_triangles()
    uv = mesh.uv_layers.active.data
    pixels, positions, normals = [], [], []
    for tri in mesh.loop_triangles:
        uvs = np.array([uv[i].uv for i in tri.loops]) * TEXTURE - 0.5
        cos = np.array([mesh.vertices[v].co for v in tri.vertices])
        nos = np.array([mesh.corner_normals[i].vector for i in tri.loops])
        x0, y0 = np.floor(uvs.min(0)).astype(int)
        x1, y1 = np.ceil(uvs.max(0)).astype(int)
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        p = np.stack([gx.ravel(), gy.ravel()], 1).astype(np.float64)
        a, b, c = uvs
        area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
        if abs(area) < 1e-12:
            continue
        w1 = ((p[:, 0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (p[:, 1] - a[1])) / area
        w2 = ((b[0] - a[0]) * (p[:, 1] - a[1]) - (p[:, 0] - a[0]) * (b[1] - a[1])) / area
        w0 = 1 - w1 - w2
        inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        inside &= (p[:, 0] >= 0) & (p[:, 0] < TEXTURE) & (p[:, 1] >= 0) & (p[:, 1] < TEXTURE)
        if not inside.any():
            continue
        weights = np.stack([w0, w1, w2], 1)[inside]
        pixels.append(p[inside].astype(int))
        positions.append(weights @ cos)
        normal = weights @ nos
        normals.append(normal / np.linalg.norm(normal, axis=1, keepdims=True))
    return np.concatenate(pixels), np.concatenate(positions), np.concatenate(normals)


def fill(rgb, covered, steps=64):
    """Push colours outward into uncovered texels (gutters, unseen spots), ring by ring, then nearest."""
    rgb = rgb.copy()
    known = covered.copy()
    for _ in range(steps):
        if known.all():
            break
        total = np.zeros_like(rgb)
        count = np.zeros(known.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            shifted = np.roll(np.roll(known, dy, 0), dx, 1)
            total += np.roll(np.roll(rgb * known[..., None], dy, 0), dx, 1) * shifted[..., None]
            count += shifted
        grow = ~known & (count > 0)
        rgb[grow] = total[grow] / count[grow][:, None]
        known |= grow
    rgb[~known] = rgb[known].mean(0)
    return rgb


def save_png(rgb, path, colorspace='sRGB'):
    height, width = rgb.shape[:2]
    image = bpy.data.images.new(os.path.basename(path), width, height, alpha=False)
    image.colorspace_settings.name = colorspace
    image.pixels[:] = np.clip(np.concatenate([rgb[::-1], np.ones((height, width, 1), np.float32)], -1), 0, 1).ravel()
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    return image


def bake(name, paint_dir=None):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, f'{name}.blend'))
    obj = bpy.data.objects[name]
    clean_normals(obj)
    unwrap(obj)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{name}.blend'))
    design = DESIGNS[name]
    frame = json.load(open(os.path.join(PAINT, name, 'views.json')))
    centre, scale, size = Vector(frame['centre']), frame['scale'], frame['size']
    pixels, positions, normals = texels(obj)
    print('BAKE', name, len(pixels), 'texels')
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    accumulated = np.zeros((len(pixels), 3), np.float64)
    accumulated_metal = np.zeros(len(pixels), np.float64)
    accumulated_gem = np.zeros(len(pixels), np.float64)
    accumulated_bone = np.zeros(len(pixels), np.float64)
    weight_sum = np.zeros(len(pixels), np.float64)
    registrations = {}
    for view, direction in VIEWS.items():
        path = os.path.join(paint_dir or os.path.join(PAINT, name), f'paint_{view}.png')
        assert os.path.exists(path), (name, 'missing painted view', view)
        paint = load_rgba(path)
        guide = load_rgba(os.path.join(PAINT, name, f'guide_{view}.png'))
        if paint.shape[:2] != (size, size):
            ys = (np.arange(size) * paint.shape[0] / size).astype(int)
            xs = (np.arange(size) * paint.shape[1] / size).astype(int)
            paint = paint[ys][:, xs]
        # Register the painted silhouette's box onto the guide's.
        gx0, gx1, gy0, gy1 = bbox(guide[..., 3])
        px0, px1, py0, py1 = bbox(paint[..., 3])
        sx, sy = (px1 - px0) / max(gx1 - gx0, 1), (py1 - py0) / max(gy1 - gy0, 1)
        alpha = erode(paint[..., 3] > 0.5, 3).astype(np.float32)
        d, right, up = view_frame(direction)
        d, right, up = np.array(d), np.array(right), np.array(up)
        facing = normals @ d
        candidates = np.nonzero(facing > 0.05)[0]
        visible = np.zeros(len(pixels), bool)
        for index in candidates:
            origin = Vector(positions[index] + normals[index] * 1e-3 + d * 1e-3)
            visible[index] = bvh.ray_cast(origin, Vector(d))[0] is None
        relative = positions - np.array(centre)
        gx = (relative @ right / scale + 0.5) * size - 0.5
        gy = (0.5 - relative @ up / scale) * size - 0.5
        x = px0 + (gx - gx0) * sx
        y = py0 + (gy - gy0) * sy
        colour = bilinear(paint[..., :3], x, y)
        coverage = bilinear(alpha[..., None], x, y)[:, 0]
        weight = np.where(visible, np.clip(facing, 0, 1) ** 4 * coverage, 0.0)
        accumulated += colour * weight[:, None]
        mixed = design.get('material_mode') in ('mixed',)
        if mixed:
            mask = load_rgba(os.path.join(paint_dir or os.path.join(PAINT, name), f'metal_{view}.png'))
            mx0, mx1, my0, my1 = bbox(mask[..., 3])
            mx = mx0 + (gx - gx0) * (mx1 - mx0) / max(gx1 - gx0, 1)
            my = my0 + (gy - gy0) * (my1 - my0) / max(gy1 - gy0, 1)
            classification = bilinear(mask[..., :3], mx, my)
            metal = (classification.min(axis=1) > .55).astype(float)
            accumulated_gem += (classification[:, 1] - classification[:, 0] > .4) * weight
            accumulated_bone += (classification[:, 2] - classification[:, 0] > .4) * weight
        else:
            metal = np.full(len(pixels), design['metallic'])
        accumulated_metal += metal * weight
        weight_sum += weight
        registrations[view] = {'scale_x': float(sx), 'scale_y': float(sy), 'visible': int(visible.sum())}
        print('  view', view, 'visible', int(visible.sum()), 'scale', round(sx, 3), round(sy, 3))
    covered_texels = weight_sum > 1e-4
    base = np.zeros((TEXTURE, TEXTURE, 3), np.float32)
    covered = np.zeros((TEXTURE, TEXTURE), bool)
    rows, cols = pixels[covered_texels, 1], pixels[covered_texels, 0]
    base[rows, cols] = accumulated[covered_texels] / weight_sum[covered_texels, None]
    covered[rows, cols] = True
    island = np.zeros((TEXTURE, TEXTURE), bool)
    island[pixels[:, 1], pixels[:, 0]] = True
    base = fill(base, covered)
    base = np.clip(base, 30/255, 243/255) # Image pixels and PNG storage use normalized sRGB channels.
    metal = np.zeros((TEXTURE, TEXTURE, 1), np.float32)
    metal[rows, cols, 0] = accumulated_metal[covered_texels] / weight_sum[covered_texels]
    metal = (fill(metal, covered)[..., 0] >= .5).astype(np.float32)
    assert set(np.unique(metal)) <= {0, 1}
    # Hidden texels keep the material colour; lighting supplies cavity shading.
    # Surface class controls roughness and metallic; only fine paint detail contributes to the normal.
    luminance = base @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    classes = np.zeros((TEXTURE, TEXTURE, 2), np.float32)
    classes[rows, cols, 0] = accumulated_gem[covered_texels] / weight_sum[covered_texels]
    classes[rows, cols, 1] = accumulated_bone[covered_texels] / weight_sum[covered_texels]
    classes = fill(classes, covered)
    rough = np.where(metal > .5, .39, .7)
    rough = np.where(classes[..., 0] > .5, .23, rough)
    rough = np.where(classes[..., 1] > .5, .5, rough)
    mr = np.stack([np.ones_like(rough), rough, metal], -1)
    blurred = luminance.copy()
    for _ in range(4):
        blurred = (blurred + np.roll(blurred, 1, 0) + np.roll(blurred, -1, 0) + np.roll(blurred, 1, 1)
                   + np.roll(blurred, -1, 1)) / 5
    detail = (luminance - blurred) * design['normal']
    inner = erode(island, 2)
    dx = np.where(inner, (np.roll(detail, -1, 1) - np.roll(detail, 1, 1)) / 2, 0)
    dy = np.where(inner, (np.roll(detail, -1, 0) - np.roll(detail, 1, 0)) / 2, 0)
    # The maps are built with row = v (bottom up) and flipped when written: +v is +row.
    normal = np.stack([-dx * 8, -dy * 8, np.ones_like(dx)], -1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    textures = os.path.join(WORK, 'textures')
    os.makedirs(textures, exist_ok=True)
    base_image = save_png(base[::-1], os.path.join(textures, f'{name}_basecolor.png'))
    mr_image = save_png(mr[::-1], os.path.join(textures, f'{name}_mr.png'), 'Non-Color')
    normal_image = save_png((normal * 0.5 + 0.5)[::-1], os.path.join(textures, f'{name}_normal.png'), 'Non-Color')
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nt = material.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    for image, socket in ((base_image, 'Base Color'),):
        node = nt.nodes.new('ShaderNodeTexImage')
        node.image = image
        nt.links.new(node.outputs['Color'], bsdf.inputs[socket])
    mr_node = nt.nodes.new('ShaderNodeTexImage')
    mr_node.image = mr_image
    separate = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mr_node.outputs['Color'], separate.inputs['Color'])
    nt.links.new(separate.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(separate.outputs['Blue'], bsdf.inputs['Metallic'])
    normal_node = nt.nodes.new('ShaderNodeTexImage')
    normal_node.image = normal_image
    mapping = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(normal_node.outputs['Color'], mapping.inputs['Color'])
    nt.links.new(mapping.outputs['Normal'], bsdf.inputs['Normal'])
    obj.data.materials.clear()
    obj.data.materials.append(material)
    lo = Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
    shift = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for vertex in obj.data.vertices:
        vertex.co -= shift
    pl.WORK = WORK
    pl.export(obj, name)
    with open(os.path.join(PAINT, name, 'bake_report.json'), 'w') as handle:
        json.dump({'coverage': float(covered.sum() / max(island.sum(), 1)), 'registrations': registrations,
                   'binary_metallic': True, 'roughness': 'metal .39 / organic .70 / gems .23 / ivory or coated enamel .50; independent of albedo brightness', 'texture_size': TEXTURE}, handle, indent=2)
    print('BAKED', name, 'coverage', round(float(covered.sum() / max(island.sum(), 1)), 3))


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    for name in args[1:]:
        assert name in DESIGNS
        {'prep': prep, 'bake': bake}[args[0]](name)


main()
