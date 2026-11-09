"""Codex-painted textures for an untextured Meshy Smart Topology item: prep (unwrap, guide views) and bake (project
the painted views onto the UVs, derive PBR maps, export).

prep <name>: the Smart Topology GLB (meshy/meshy/<name>_st_v1/model_urls_glb.glb) welded, centred and grounded,
    collapse-reduced to the design's 'tris' budget (designs.json) when larger, Smart UV unwrapped (islands packed with a margin); saved as work/codex_tex/<name>.blend. Then plain grey
    orthographic guide renders of exactly that mesh (codex_tex/<name>/guide_<view>.png, 1024 x 1024, transparent
    background) from the views below, framed alike (views.json records centre and scale), for Codex to paint over.
bake <name>: Codex's paintings (codex_tex/<name>/paint_<view>.png, the guide's framing; transparent background) are
    each registered onto their guide (scale and offset that fit the painted silhouette's box to the guide's), then
    projected onto every texel: weight (n . view)^4 times the painting's eroded alpha, texels the view cannot see
    (ray cast toward the camera) skipped; uncovered texels and the gutters filled outward, and texels no view sees (the
    inner wall of a shell) filled with the declared interior material's painted colour. PBR: metallic and roughness
    from discrete guide-aligned material masks, a tangent-space
    normal from the painting's fine luminance detail inside each island. Writes work/codex_tex/<name>_export.glb.
Usage: blender --background --python codex_texture.py -- prep|bake <name> [paintings folder, for bake]"""
import hashlib
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'projectiles_claude',
                                'scripts'))
import projlib as pl  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import material_masks as masks

MESHY = os.path.join(HERE, 'meshy', 'meshy')
WORK = os.path.join(HERE, 'work', 'codex_tex')
PAINT = os.path.join(HERE, 'codex_tex')
GUIDE = 1024
TEXTURE = 512
# Guide silhouettes thinner than this (pixels, short side) are edge-on slivers of flat items: not baked
# (register_views.py skips them too).
METAL_FLOOR = 0.5
METAL_GAIN = 2.0
SLIVER = 82
# View name: direction from the object toward the camera.
VIEWS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (-1, 0, 0), 'right': (1, 0, 0), 'top': (0, 0, 1)}
# Each design records its triangle budget, geometry source and explicit material classes.
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))


def view_frame(direction):
    d = Vector(direction).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    right = up.cross(d).normalized()
    return d, right, d.cross(right).normalized()


def prep(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if 'geometry' in DESIGNS[name]:
        source = os.path.join(HERE, 'work', 'procedural', f'{name}.glb')
    else:
        version = DESIGNS[name].get('meshy_version', 'v1')
        source = os.path.join(MESHY, f'{name}_st_{version}', 'model_urls_glb.glb')
    bpy.ops.import_scene.gltf(filepath=source)
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
    obj.name = name
    rest(obj, DESIGNS[name].get('rest'))
    budget = DESIGNS[name].get('tris')
    obj.data.calc_loop_triangles()
    triangles = len(obj.data.loop_triangles)
    if budget and triangles > budget * 1.15:
        modifier = obj.modifiers.new('decimate', 'DECIMATE')
        modifier.ratio = budget / triangles
        modifier.use_collapse_triangulate = True
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    xs, ys, zs = ([v.co[i] for v in obj.data.vertices] for i in range(3))
    shift = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    for v in obj.data.vertices:
        v.co -= shift
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.01)
        bpy.ops.object.mode_set(mode='OBJECT')
    # Faceted cuts stay flat (smooth_angle 0); Meshy shapes split their normals at 40 degrees.
    angle = DESIGNS[name].get('smooth_angle', 40)
    for polygon in obj.data.polygons:
        polygon.use_smooth = angle > 0
    if 0 < angle < 180:
        with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    os.makedirs(WORK, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{name}.blend'))
    guides(name)


def rest(obj, mode):
    """'pca' / 'pca_flip' / 'pca_front': a flat item Meshy stood on edge or tilted lies on its broad side: the vertices' least-variance
    axis becomes vertical (flipped for pca_flip); the longest horizontal spread stays as it falls."""
    if not mode:
        return
    points = np.array([v.co for v in obj.data.vertices])
    centre = points.mean(0)
    _, vectors = np.linalg.eigh(np.cov((points - centre).T))
    normal = vectors[:, 0]
    if normal[2] < 0:
        normal = -normal
    if mode == 'pca_flip':
        normal = -normal
    # pca_front: Meshy stood the item up facing its master's camera (-Y); that face goes up.
    if mode == 'pca_front' and normal[1] > 0:
        normal = -normal
    rotation = Vector(normal).rotation_difference(Vector((0, 0, 1))).to_matrix().to_4x4()
    obj.data.transform(rotation)
    print('REST', obj.name, mode, [round(float(c), 3) for c in normal])


def guides(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, f'{name}.blend'))
    obj = bpy.data.objects[name]
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
    for polygon in obj.data.polygons:
        polygon.material_index = 0
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 4
    scene.cycles.use_denoising = True
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
        camera.location = centre + d * max(hi - lo) * 3
        camera.rotation_euler = (-d).to_track_quat('-Z', 'Y' if abs(d.z) < 0.9 else 'Z').to_euler()
        light.rotation_euler = (-(d + up * 0.6 + right * 0.3)).normalized().to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(PAINT, name, f'guide_{view}.png')
        bpy.ops.render.render(write_still=True)
    with open(os.path.join(PAINT, name, 'views.json'), 'w') as handle:
        json.dump({'centre': list(centre), 'scale': scale, 'size': GUIDE, 'views': VIEWS}, handle, indent=1)
    bpy.data.objects.remove(camera)
    bpy.data.objects.remove(light)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{name}.blend'))
    print('PREP', name, len(obj.data.polygons), 'faces, guides in', os.path.join(PAINT, name))


def load_rgba(path, non_color=False):
    image = bpy.data.images.load(path, check_existing=False)
    if non_color:
        image.colorspace_settings.name = 'Non-Color'
    width, height = image.size
    rgba = np.array(image.pixels[:], np.float32).reshape(height, width, 4)[::-1].copy()
    bpy.data.images.remove(image)
    return rgba


def load_view(folder, kind, view, atlas=False):
    if not atlas:
        return load_rgba(os.path.join(folder, f'{kind}_{view}.png'), kind == 'mask')
    image = load_rgba(os.path.join(folder, f'{kind}_atlas.png'), kind == 'mask')
    height, width = image.shape[:2]
    if width % 3 or height % 2 or abs(width / height - 1.5) > 0.01:
        raise ValueError('View atlas must have a 3:2 canvas and three columns by two rows of square cells')
    index = list(VIEWS).index(view)
    x, y = (index % 3) * (width // 3), (index // 3) * (height // 2)
    return image[y:y + height // 2, x:x + width // 3].copy()


def bbox(alpha):
    ys, xs = np.nonzero(alpha > 0.5)
    return xs.min(), xs.max(), ys.min(), ys.max()


def registration_ok(reference, measured, pixel=1, budget=0.05):
    # Round the five-percent budget to a source pixel, rather than rejecting its fractional boundary.
    return abs(measured - reference) <= math.ceil(budget * reference / pixel) * pixel


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


def texels(obj, with_classes=False):
    """Every covered texel: its pixel, world position and smooth normal (barycentric over the UV triangles)."""
    mesh = obj.data
    mesh.calc_loop_triangles()
    uv = mesh.uv_layers.active.data
    pixels, positions, normals, classes = [], [], [], []
    labels = mesh.attributes.get('ground_material_class') if with_classes else None
    assert not with_classes or labels is not None
    for tri in mesh.loop_triangles:
        if mesh.polygons[tri.polygon_index].material_index != 0:
            continue
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
        # UV gutters are filled later; extrapolated points fall outside the actual mesh/material silhouette.
        inside = (w0 >= -1e-8) & (w1 >= -1e-8) & (w2 >= -1e-8)
        inside &= (p[:, 0] >= 0) & (p[:, 0] < TEXTURE) & (p[:, 1] >= 0) & (p[:, 1] < TEXTURE)
        if not inside.any():
            continue
        weights = np.stack([w0, w1, w2], 1)[inside]
        pixels.append(p[inside].astype(int))
        positions.append(weights @ cos)
        normal = weights @ nos
        normals.append(normal / np.linalg.norm(normal, axis=1, keepdims=True))
        if labels is not None:
            classes.append(np.full(len(weights), labels.data[tri.polygon_index].value, dtype=int))
    result = (np.concatenate(pixels), np.concatenate(positions), np.concatenate(normals))
    return (*result, np.concatenate(classes)) if with_classes else result


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
    design = DESIGNS[name]
    frame = json.load(open(os.path.join(PAINT, name, 'views.json')))
    frame = json.load(open(os.path.join(PAINT, name, 'views.json')))
    centre, scale, size = Vector(frame['centre']), frame['scale'], frame['size']
    pixels, positions, normals = texels(obj)
    print('BAKE', name, len(pixels), 'texels')
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    accumulated = np.zeros((len(pixels), 3), np.float64)
    weight_sum = np.zeros(len(pixels), np.float64)
    material_votes = np.zeros((len(pixels), len(masks.NAMES)), np.float64)
    # Edge-on slivers: under SLIVER pixels and under half the widest view's short side (as register_views.py).
    sides = {}
    for view in VIEWS:
        gx0, gx1, gy0, gy1 = bbox(load_rgba(os.path.join(PAINT, name, f'guide_{view}.png'))[..., 3])
        sides[view] = min(gx1 - gx0, gy1 - gy0)
    slivers = {view: side < SLIVER and side < 0.5 * max(sides.values()) for view, side in sides.items()}
    # A view whose painting does not register is left out when the other views cover the model: at most two.
    rejected = []

    def reject(view, reason):
        rejected.append(view)
        print('  view', view, 'rejected:', reason)
        if len(rejected) > 2:
            raise ValueError(f'{view}: {reason} (views rejected: {rejected})')

    for view, direction in VIEWS.items():
        # skip_views: a view whose painting cannot register (a thin ring seen edge-on) and whose surfaces the
        # other views cover.
        if view in design.get('skip_views', ()):
            continue
        folder = paint_dir or os.path.join(PAINT, name)
        if slivers[view]:
            print('  view', view, 'skipped: edge-on sliver')
            continue
        atlas = frame.get('paint_layout') == 'atlas_3x2'
        paint = load_view(folder, 'paint', view, atlas)
        guide = load_rgba(os.path.join(PAINT, name, f'guide_{view}.png'))
        if paint.shape[0] != size:
            ys = (np.arange(size) * paint.shape[0] / size).astype(int)
            xs = (np.arange(size) * paint.shape[1] / size).astype(int)
            paint = paint[ys][:, xs]
        # Register the painted silhouette's box onto the guide's.
        gx0, gx1, gy0, gy1 = bbox(guide[..., 3])
        px0, px1, py0, py1 = bbox(paint[..., 3])
        sx, sy = (px1 - px0) / max(gx1 - gx0, 1), (py1 - py0) / max(gy1 - gy0, 1)
        if not (registration_ok(gx1 - gx0, px1 - px0) and registration_ok(gy1 - gy0, py1 - py0)):
            reject(view, f'painted silhouette registration outside 0.95-1.05: {sx}, {sy}')
            continue
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
        if 'surface_material' in design:
            classes = np.full(len(pixels), masks.NAMES.index(design['surface_material']), dtype=int)
            active = weight > 1e-4
            material_votes[np.nonzero(active)[0], classes[active]] += weight[active]
            accumulated += colour * weight[:, None]
            weight_sum += weight
            print('  view', view, 'visible', int(visible.sum()), 'scale', round(sx, 3), round(sy, 3))
            continue
        mask_atlas = frame.get('mask_layout', frame.get('paint_layout')) == 'atlas_3x2'
        mask = load_view(folder, 'mask', view, mask_atlas)
        mx0, mx1, my0, my1 = bbox(mask[..., 3])
        msx = (mx1 - mx0) / max(gx1 - gx0, 1) * size / mask.shape[1]
        msy = (my1 - my0) / max(gy1 - gy0, 1) * size / mask.shape[0]
        mask_pixel = size / mask.shape[1]
        # The mask is sampled through its own box, and its classes are coarse: it may miss the guide by 10 %.
        if not (registration_ok(gx1 - gx0, (mx1 - mx0) * mask_pixel, mask_pixel, 0.1)
                and registration_ok(gy1 - gy0, (my1 - my0) * mask_pixel, mask_pixel, 0.1)):
            reject(view, f'material mask registration outside 0.9-1.1: {msx}, {msy}')
            continue
        mx = np.clip((mx0 + (gx - gx0) / max(gx1 - gx0, 1) * (mx1 - mx0)).astype(int),
                     0, mask.shape[1] - 1)
        my = np.clip((my0 + (gy - gy0) / max(gy1 - gy0, 1) * (my1 - my0)).astype(int),
                     0, mask.shape[0] - 1)
        samples = mask[my, mx]
        active = weight > 1e-4
        missing = active & (samples[:, 3] < 0.5)
        if missing.sum() / max(active.sum(), 1) > 0.05:
            reject(view, f'material mask misses {missing.sum()} of {active.sum()} painted texels')
            continue
        # Exclude silhouette-edge samples without a material class; other views may cover them.
        weight[missing] = 0
        active &= ~missing
        classes = masks.classify(samples[active, :3])
        material_votes[np.nonzero(active)[0], classes] += weight[active]
        accumulated += colour * weight[:, None]
        weight_sum += weight
        print('  view', view, 'visible', int(visible.sum()), 'scale', round(sx, 3), round(sy, 3))
    covered_texels = weight_sum > 1e-4
    if not covered_texels.any():
        raise ValueError('No painted texels cover this mesh')
    base = np.zeros((TEXTURE, TEXTURE, 3), np.float32)
    covered = np.zeros((TEXTURE, TEXTURE), bool)
    rows, cols = pixels[covered_texels, 1], pixels[covered_texels, 0]
    base[rows, cols] = accumulated[covered_texels] / weight_sum[covered_texels, None]
    covered[rows, cols] = True
    island = np.zeros((TEXTURE, TEXTURE), bool)
    island[pixels[:, 1], pixels[:, 0]] = True
    # Use the declared interior material's painted albedo; artificial darkening creates black UV triangles.
    unseen = island & ~covered
    # The interior is the declared material where the painting has it, else the item's dominant painted material
    # (a gold statue has no leather to line it with).
    painted = np.bincount(np.argmax(material_votes[covered_texels], axis=-1), minlength=len(masks.NAMES))
    interior = design['unseen_material']
    if not painted[masks.NAMES.index(interior)]:
        interior = masks.NAMES[int(np.argmax(painted))]
        print('  interior material', design['unseen_material'], 'not painted: using', interior)
    if unseen.any():
        base[unseen] = masks.interior_albedo(base[rows, cols], material_votes[covered_texels], interior)
    base = fill(base, island)
    # Roughness and binary metalness follow the painted material classes, including dark leather beside metal.
    mr = np.zeros((TEXTURE, TEXTURE, 3), np.float32)
    mr[pixels[:, 1], pixels[:, 0]] = masks.pbr(material_votes, interior)
    mr = fill(mr, island)
    # Metal brightness floor (MM9, 2026-11-05): the paintings copy the icons' shaded dark steel, but a metal's base
    # colour is its reflectance (Khronos: 0.5 and above); dark steel mirrored a dark world into black. Lift the metal
    # texels' median luminance to METAL_FLOOR, at most METAL_GAIN times, keeping their hue and detail.
    weights = np.array([0.2126, 0.7152, 0.0722], np.float32)
    metal = island & (mr[..., 2] > 0.5)
    if metal.any():
        level = float(np.median(base[metal] @ weights))
        if level < METAL_FLOOR:
            gain = min(METAL_FLOOR / max(level, 1e-3), METAL_GAIN)
            base[metal] = np.clip(base[metal] * gain, 0, 1)
            print('  metal albedo', round(level, 3), 'lifted by', round(gain, 2))
    luminance = base @ weights
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
    for polygon in obj.data.polygons:
        polygon.material_index = 0
    coordinates = [vertex.co.copy() for vertex in obj.data.vertices]
    low = Vector([min(point[i] for point in coordinates) for i in range(3)])
    high = Vector([max(point[i] for point in coordinates) for i in range(3)])
    shift = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    for vertex in obj.data.vertices:
        vertex.co -= shift
    pl.WORK = WORK
    export_name = name
    for image in (base_image, mr_image, normal_image):
        image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, export_name + '_pbr.blend'))
    pl.export(obj, export_name)
    print('BAKED', name, 'coverage', round(float(covered.sum() / max(island.sum(), 1)), 3))


def uv_coverage(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    uv = mesh.uv_layers.active.data
    t = np.array([[uv[i].uv for i in tri.loops] for tri in mesh.loop_triangles])
    return float(0.5 * np.abs((t[:, 1, 0] - t[:, 0, 0]) * (t[:, 2, 1] - t[:, 0, 1])
                              - (t[:, 2, 0] - t[:, 0, 0]) * (t[:, 1, 1] - t[:, 0, 1])).sum())


def repack(name):
    """Denser UVs for a prepared mesh, same geometry and guides (its paintings stay valid; bake again afterwards).
    Smart UV leaves Meshy armour and cage-like builds at 11-30 % of the atlas: hundreds of loose islands, each with
    its 0.01 margin. Candidates: the same islands at one density, concave-packed with a 2-texel margin, and
    uv_atlas.py's xatlas charts (fewer, merged); xatlas is kept only when it covers 5 points more."""
    sys.path.insert(0, os.path.join(HERE, '..', '..', 'creatures', 'claude_shared'))
    import uv_atlas
    path = os.path.join(WORK, f'{name}.blend')
    bpy.ops.wm.open_mainfile(filepath=path)
    obj = bpy.data.objects[name]
    before = uv_coverage(obj)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(rotate=True, margin_method='FRACTION', margin=2 / TEXTURE, shape_method='CONCAVE')
        bpy.ops.object.mode_set(mode='OBJECT')
    packed = uv_coverage(obj)
    packed_uv = np.array([loop.uv[:] for loop in obj.data.uv_layers.active.data])
    method, after = 'pack', packed
    try:
        uv_atlas.unwrap(obj, size=TEXTURE, margin_px=2)
        charted = uv_coverage(obj)
    except Exception as error:  # a mesh xatlas cannot chart keeps the packed islands
        print('REPACK', name, 'xatlas failed:', error)
        charted = 0.0
    if charted >= packed + 0.05:
        method, after = 'xatlas', charted
    else:
        layer = obj.data.uv_layers.active.data
        layer.foreach_set('uv', packed_uv.ravel())
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print(f'REPACK {name} {before:.3f} -> {after:.3f} ({method}; packed {packed:.3f}, xatlas {charted:.3f})')


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    {'prep': prep, 'guides': guides, 'bake': bake, 'repack': repack}[args[0]](*args[1:])


if __name__ == '__main__':
    main()
