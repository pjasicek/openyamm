"""The warglaives (2026-10-24): Codex-painted textures for the Meshy Smart Topology glaives, a Harrower-local copy of
level_generation/props/items_claude/scripts/codex_texture.py (same guides, projection and fill) with the glaive's own
frame, budget and material classes.

prep <key>: meshy/warglaive_<key>_st_v1/model_urls_glb.glb welded, then put in the glaive frame: the centre grip at the
    origin (the bounding box's middle along the long axis, the mean of the vertices in a 4 cm slab there across it), the
    long axis +Z, the glowing (concave) side +X, the faces toward -Y/+Y; scaled to LENGTH[key] m tip to tip;
    collapse-reduced to BUDGET[key] triangles (the assembled actor stays under 15 000 with two glaives); Smart UV
    unwrapped; saved as work/warglaive_<key>.blend. Plain grey orthographic guides (warglaives/<key>/paint/guide_<view>.png,
    1024, transparent) from front (-Y), back, left (-X), right and top, one framing (views.json), for Codex to paint.
bake <key>: the paintings (paint_<view>.png) registered onto their guides and projected onto the texels as
    codex_texture.py does (weight (n . view)^4 x eroded alpha, occluded texels skipped, gutters filled, unseen texels
    darkened). Then per texel a material class from the painted colour: glow (bright, saturated orange to white-hot,
    or near-white), gold (warm yellow, mid saturation), ivory (light, low saturation), resin (the rest, dark), for the
    atlas region mask. Every face keeps material index 0 (the plate). Writes warglaives/<key>/tex/{basecolor,normal,
    metal_rough,region,island}.png (1024; region: R ivory, G gold, B glow, as hkr_armour_region_mask.png) and
    work/warglaive_<key>_baked.blend.
glow <key>: the energy seams on their own faces: each stroke of warglaive_seams.py (seams.json, from the front and back
    paintings) mapped back through the bake's registration, ray cast onto the mesh from its view and laid on the
    surface as a ribbon of the painted width (at least RIB_MIN, to read at game distance; the crescents' strip was
    34 mm), each ribbon vertex cast onto the surface itself and RIB_LIFT proud along its normal, material index 1 (the shared HHW glow material: scalar
    emission, coloured per tier; a 1000-texel seam spans parts of many faces, so no face is mostly glow).
    Rewrites work/warglaive_<key>_baked.blend.
Usage: blender --background --python warglaive_texture.py -- prep|bake|glow <harrower|vreth>"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDE = 1024
TEXTURE = 1024
LENGTH = {'harrower': 1.10, 'vreth': 1.18}        # 58 % and 62 % of the 1.891 m body, as the crescents were
BUDGET = {'harrower': 1420, 'vreth': 1190}        # with the glow ribbons: the family assembly (every tier's gear) and Vreth's
                                                  # stay under the 15 000 ceiling (export_harrower.py asserts it)
ROUGH = (0.6, 0.35)                               # roughness where the painting is dark .. bright (resin .. glazed ivory)
NORMAL = 2.0
RIB_MIN, RIB_LIFT = 0.012, 0.0015
VIEWS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (-1, 0, 0), 'right': (1, 0, 0), 'top': (0, 0, 1)}


def paths(key):
    paint = os.path.join(HERE, 'warglaives', key, 'paint')
    return (os.path.join(HERE, 'meshy', f'warglaive_{key}_st_v1', 'model_urls_glb.glb'), paint,
            os.path.join(HERE, 'warglaives', key, 'tex'), os.path.join(HERE, 'work', f'warglaive_{key}.blend'),
            os.path.join(HERE, 'work', f'warglaive_{key}_baked.blend'))


def view_frame(direction):
    d = Vector(direction).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    right = up.cross(d).normalized()
    return d, right, d.cross(right).normalized()


def prep(key):
    glb, paint, _, blend, _ = paths(key)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
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
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(obj.data); bm.free()
    co = np.array([v.co for v in obj.data.vertices])
    ext = co.max(0) - co.min(0); long_axis = int(np.argmax(ext))
    assert long_axis == 2, ('Meshy put the glaive along another axis', ext)
    zc = (co[:, 2].min() + co[:, 2].max()) / 2
    slab = co[np.abs(co[:, 2] - zc) < 0.02 * ext[2]]
    grip = np.array([slab[:, 0].mean(), slab[:, 1].mean(), zc])
    # the concave (glowing) side: the tips bend toward it, away from the grip
    tips = co[np.abs(co[:, 2] - zc) > 0.45 * ext[2]]
    side = 1.0 if tips[:, 0].mean() > grip[0] else -1.0
    s = LENGTH[key] / ext[2]
    for v in obj.data.vertices:
        p = (np.array(v.co) - grip) * s
        v.co = Vector((p[0] * side, p[1] * side, p[2]))     # a turn about Z when the concave side was -X
    obj.name = obj.data.name = f'Warglaive_{key}'
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    if tris > BUDGET[key]:
        m = obj.modifiers.new('decimate', 'DECIMATE'); m.ratio = BUDGET[key] / tris; m.use_collapse_triangulate = True
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_apply(modifier=m.name)
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.01)
        bpy.ops.object.mode_set(mode='OBJECT')
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    os.makedirs(paint, exist_ok=True)
    material = bpy.data.materials.new('clay'); material.use_nodes = True
    bsdf = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (0.55, 0.55, 0.55, 1); bsdf.inputs['Roughness'].default_value = 0.8
    obj.data.materials.clear(); obj.data.materials.append(material)
    scene = bpy.context.scene
    for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.resolution_x = scene.render.resolution_y = GUIDE
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
    background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    background.inputs['Color'].default_value = (1, 1, 1, 1); background.inputs['Strength'].default_value = 0.6
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    lo = Vector([min(p[i] for p in points) for i in range(3)]); hi = Vector([max(p[i] for p in points) for i in range(3)])
    centre = (lo + hi) / 2; scale = max(hi - lo) * 1.08
    camera = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); camera.data.type = 'ORTHO'
    camera.data.ortho_scale = scale; scene.collection.objects.link(camera); scene.camera = camera
    light = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN')); light.data.energy = 2.5
    scene.collection.objects.link(light)
    for view, direction in VIEWS.items():
        d, right, up = view_frame(direction)
        camera.location = centre + d * max(hi - lo) * 3
        camera.rotation_euler = (-d).to_track_quat('-Z', 'Y' if abs(d.z) < 0.9 else 'Z').to_euler()
        light.rotation_euler = (-(d + up * 0.6 + right * 0.3)).normalized().to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(paint, f'guide_{view}.png')
        bpy.ops.render.render(write_still=True)
    with open(os.path.join(paint, 'views.json'), 'w') as handle:
        json.dump({'centre': list(centre), 'scale': scale, 'size': GUIDE, 'views': VIEWS}, handle, indent=1)
    bpy.data.objects.remove(camera); bpy.data.objects.remove(light)
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print('PREP', key, sum(len(p.vertices) - 2 for p in obj.data.polygons), 'tris, dims',
          [round(x, 3) for x in (hi - lo)], 'concave side was', '+X' if side > 0 else '-X', flush=True)


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
    x = np.clip(x, 0, w - 1.001); y = np.clip(y, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (image[y0, x0] * (1 - fx) * (1 - fy) + image[y0, x0 + 1] * fx * (1 - fy)
            + image[y0 + 1, x0] * (1 - fx) * fy + image[y0 + 1, x0 + 1] * fx * fy)


def texels(obj):
    """Every covered texel: its pixel, world position, smooth normal and face (barycentric over the UV triangles)."""
    mesh = obj.data
    mesh.calc_loop_triangles()
    uv = mesh.uv_layers.active.data
    pixels, positions, normals, faces = [], [], [], []
    for tri in mesh.loop_triangles:
        uvs = np.array([uv[i].uv for i in tri.loops]) * TEXTURE - 0.5
        cos = np.array([mesh.vertices[v].co for v in tri.vertices])
        nos = np.array([mesh.corner_normals[i].vector for i in tri.loops])
        x0, y0 = np.floor(uvs.min(0)).astype(int); x1, y1 = np.ceil(uvs.max(0)).astype(int)
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
        pixels.append(p[inside].astype(int)); positions.append(weights @ cos)
        normal = weights @ nos; normals.append(normal / np.linalg.norm(normal, axis=1, keepdims=True))
        faces.append(np.full(int(inside.sum()), tri.polygon_index))
    return np.concatenate(pixels), np.concatenate(positions), np.concatenate(normals), np.concatenate(faces)


def fill(rgb, covered, steps=64):
    rgb = rgb.copy(); known = covered.copy()
    for _ in range(steps):
        if known.all():
            break
        total = np.zeros_like(rgb); count = np.zeros(known.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            shifted = np.roll(np.roll(known, dy, 0), dx, 1)
            total += np.roll(np.roll(rgb * known[..., None], dy, 0), dx, 1) * shifted[..., None]
            count += shifted
        grow = ~known & (count > 0)
        rgb[grow] = total[grow] / count[grow][:, None]; known |= grow
    rgb[~known] = rgb[known].mean(0)
    return rgb


def save_png(rgb, path, colorspace='sRGB'):
    height, width = rgb.shape[:2]
    image = bpy.data.images.new(os.path.basename(path), width, height, alpha=False)
    image.colorspace_settings.name = colorspace
    image.pixels[:] = np.clip(np.concatenate([rgb[::-1], np.ones((height, width, 1), np.float32)], -1), 0, 1).ravel()
    image.filepath_raw = path; image.file_format = 'PNG'; image.save()
    return image


def classify(rgb):
    """0 resin, 1 ivory, 2 gold, 3 glow, from the painted colour (sRGB 0..1)."""
    mx, mn = rgb.max(-1), rgb.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-4)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    glow = ((mx > 0.82) & (sat > 0.55) & (r > g) & (g > b)) | (mn > 0.93)
    gold = ~glow & (mx > 0.45) & (sat > 0.35) & (sat <= 0.75) & (r >= g) & (g > b * 1.15)
    ivory = ~glow & ~gold & (mx > 0.5) & (sat < 0.35)
    cls = np.zeros(rgb.shape[:2], np.uint8)
    cls[ivory] = 1; cls[gold] = 2; cls[glow] = 3
    return cls


def bake(key):
    _, paint, tex, blend, baked = paths(key)
    bpy.ops.wm.open_mainfile(filepath=blend)
    obj = bpy.data.objects[f'Warglaive_{key}']
    frame = json.load(open(os.path.join(paint, 'views.json')))
    centre, scale, size = Vector(frame['centre']), frame['scale'], frame['size']
    pixels, positions, normals, faces = texels(obj)
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    accumulated = np.zeros((len(pixels), 3)); weight_sum = np.zeros(len(pixels))
    for view, direction in VIEWS.items():
        path = os.path.join(paint, f'paint_{view}.png')
        if not os.path.exists(path):
            print('  no painting for', view); continue
        paint_img = load_rgba(path); guide = load_rgba(os.path.join(paint, f'guide_{view}.png'))
        if paint_img.shape[0] != size:
            ys = (np.arange(size) * paint_img.shape[0] / size).astype(int)
            xs = (np.arange(size) * paint_img.shape[1] / size).astype(int)
            paint_img = paint_img[ys][:, xs]
        gx0, gx1, gy0, gy1 = bbox(guide[..., 3]); px0, px1, py0, py1 = bbox(paint_img[..., 3])
        sx, sy = (px1 - px0) / max(gx1 - gx0, 1), (py1 - py0) / max(gy1 - gy0, 1)
        alpha = erode(paint_img[..., 3] > 0.5, 3).astype(np.float32)
        d, right, up = (np.array(v) for v in view_frame(direction))
        facing = normals @ d
        visible = np.zeros(len(pixels), bool)
        for index in np.nonzero(facing > 0.05)[0]:
            origin = Vector(positions[index] + normals[index] * 1e-3 + d * 1e-3)
            visible[index] = bvh.ray_cast(origin, Vector(d))[0] is None
        relative = positions - np.array(centre)
        gx = (relative @ right / scale + 0.5) * size - 0.5; gy = (0.5 - relative @ up / scale) * size - 0.5
        x = px0 + (gx - gx0) * sx; y = py0 + (gy - gy0) * sy
        colour = bilinear(paint_img[..., :3], x, y); coverage = bilinear(alpha[..., None], x, y)[:, 0]
        weight = np.where(visible, np.clip(facing, 0, 1) ** 4 * coverage, 0.0)
        accumulated += colour * weight[:, None]; weight_sum += weight
        print('  view', view, 'visible', int(visible.sum()), 'registration', round(sx, 3), round(sy, 3), flush=True)
    covered_texels = weight_sum > 1e-4
    base = np.zeros((TEXTURE, TEXTURE, 3), np.float32); covered = np.zeros((TEXTURE, TEXTURE), bool)
    rows, cols = pixels[covered_texels, 1], pixels[covered_texels, 0]
    base[rows, cols] = accumulated[covered_texels] / weight_sum[covered_texels, None]; covered[rows, cols] = True
    island = np.zeros((TEXTURE, TEXTURE), bool); island[pixels[:, 1], pixels[:, 0]] = True
    base = fill(base, covered); base[island & ~covered] *= 0.25
    # Material classes; faces mostly glow become the glow material's faces.
    cls = classify(base)
    # PBR
    luminance = base @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    lo, hi = np.percentile(luminance[island], [5, 95]); t = np.clip((luminance - lo) / max(hi - lo, 1e-3), 0, 1)
    rough = ROUGH[0] + (ROUGH[1] - ROUGH[0]) * t
    metal = np.where(cls == 2, 0.85, 0.0).astype(np.float32)
    rough = np.where(cls == 2, 0.35, rough)
    mr = np.stack([np.ones_like(rough), rough, metal], -1)
    blurred = luminance.copy()
    for _ in range(4):
        blurred = (blurred + np.roll(blurred, 1, 0) + np.roll(blurred, -1, 0) + np.roll(blurred, 1, 1) + np.roll(blurred, -1, 1)) / 5
    detail = (luminance - blurred) * NORMAL
    inner = erode(island, 2)
    dx = np.where(inner, (np.roll(detail, -1, 1) - np.roll(detail, 1, 1)) / 2, 0)
    dy = np.where(inner, (np.roll(detail, -1, 0) - np.roll(detail, 1, 0)) / 2, 0)
    normal = np.stack([-dx * 8, -dy * 8, np.ones_like(dx)], -1); normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    region = np.stack([(cls == 1), (cls == 2), (cls == 3)], -1).astype(np.float32)
    os.makedirs(tex, exist_ok=True)
    save_png(base[::-1], os.path.join(tex, 'basecolor.png'))
    save_png(mr[::-1], os.path.join(tex, 'metal_rough.png'), 'Non-Color')
    save_png((normal * 0.5 + 0.5)[::-1], os.path.join(tex, 'normal.png'), 'Non-Color')
    save_png(region[::-1], os.path.join(tex, 'region.png'), 'Non-Color')
    island_img = np.dstack([island] * 3).astype(np.float32)
    save_png(island_img[::-1], os.path.join(tex, 'island.png'), 'Non-Color')
    # two material slots as the old blades: 0 plate (the atlas), 1 glow
    obj.data.materials.clear()
    for name in ('HHW_Plate', 'HHW_Glow'):
        obj.data.materials.append(bpy.data.materials.get(name) or bpy.data.materials.new(name))
    obj.data.polygons.foreach_set('material_index', np.zeros(len(obj.data.polygons), np.int32))
    bpy.ops.wm.save_as_mainfile(filepath=baked)
    share = {n: round(float((cls[island] == i).mean()), 3) for i, n in enumerate(('resin', 'ivory', 'gold', 'glow'))}
    print('BAKED', key, 'coverage', round(float(covered.sum() / max(island.sum(), 1)), 3), 'classes', share,
flush=True)


def glow(key):
    _, paint, _, _, baked = paths(key)
    bpy.ops.wm.open_mainfile(filepath=baked)
    obj = bpy.data.objects[f'Warglaive_{key}']
    frame = json.load(open(os.path.join(paint, 'views.json'))); seams = json.load(open(os.path.join(paint, 'seams.json')))
    centre, scale, size = Vector(frame['centre']), frame['scale'], frame['size']
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    bm = bmesh.new(); bm.from_mesh(obj.data); uv = bm.loops.layers.uv.active; added = 0
    for view in ('front', 'back'):
        d, right, up = view_frame(VIEWS[view])
        guide = load_rgba(os.path.join(paint, f'guide_{view}.png')); pimg = load_rgba(os.path.join(paint, f'paint_{view}.png'))
        f = size / pimg.shape[0]
        ys = (np.arange(size) / f).astype(int); xs = (np.arange(size) / f).astype(int)
        gx0, gx1, gy0, gy1 = bbox(guide[..., 3]); px0, px1, py0, py1 = bbox(pimg[ys][:, xs][..., 3])
        sx, sy = (px1 - px0) / max(gx1 - gx0, 1), (py1 - py0) / max(gy1 - gy0, 1)
        for stroke in seams[view]['strokes']:
            pts, widths, nrms = [], [], []
            for x, y, w in stroke:
                # painting pixel (rows down) -> resized painting -> guide pixel -> the view plane -> the surface
                gx = gx0 + (x * f - px0) / sx; gy = gy0 + (y * f - py0) / sy
                p = centre + right * (((gx + 0.5) / size - 0.5) * scale) + up * ((0.5 - (gy + 0.5) / size) * scale)
                hit, n, _, _ = bvh.ray_cast(p + d * 1.0, -d, 2.0)
                if hit is None:
                    continue
                pts.append(hit); nrms.append(n if n.dot(d) > 0 else -n); widths.append(max(RIB_MIN, w * f / sx / size * scale))
            if len(pts) < 3:
                continue
            row = []
            for i, (p, n, w) in enumerate(zip(pts, nrms, widths)):
                tangent = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
                side = n.cross(tangent).normalized() * (w / 2); pair = []
                for q in (p - side, p + side):
                    hq, nq, _, _ = bvh.ray_cast(q + d * 1.0, -d, 2.0)
                    if hq is None:
                        hq, nq = q, n
                    nq = nq if nq.dot(d) > 0 else -nq
                    pair.append(bm.verts.new(hq + nq * RIB_LIFT))
                row.append(tuple(pair))
            for (a0, a1), (b0, b1) in zip(row[:-1], row[1:]):
                for tri in ((a0, b0, b1), (a0, b1, a1)):
                    face = bm.faces.new(tri); face.material_index = 1; face.smooth = False; added += 1
                    if face.normal.dot(d) < 0:
                        face.normal_flip()
                    for loop in face.loops:
                        loop[uv].uv = (0.002, 0.002)
    bm.to_mesh(obj.data); bm.free()
    bpy.ops.wm.save_as_mainfile(filepath=baked)
    print('GLOW', key, 'ribbon triangles', added, 'total', sum(len(p.vertices) - 2 for p in obj.data.polygons), flush=True)


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    {'prep': prep, 'bake': bake, 'glow': glow}[args[0]](*args[1:])


main()
