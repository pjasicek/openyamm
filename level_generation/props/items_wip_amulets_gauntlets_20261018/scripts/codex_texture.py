"""Six orthographic mesh guides and four-view painting projection for the gauntlets.

Geometry is prepared by prepare_gauntlets.py. register_atlases.py calibrates the generated side paintings and
semantic masks to the fixed guide frame, retaining raw art and agreement metrics. The axial paintings are not
baked: their perspective drift was rejected. Unobserved outer caps inherit the nearest painted surface in 3D;
explicit inner walls use painted leather albedo. Metalness is binary and roughness follows physical material
classes. Fine painted detail supplies OpenGL tangent normals. Finished rigid meshes get their reviewed rest pose.

Blender --background --python codex_texture.py -- guides|bake <name> [aligned paintings folder]
"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'projectiles_claude',
                                'scripts'))
import projlib as pl  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import material_masks as masks

WORK = os.path.join(HERE, 'work', 'codex_tex')
PAINT = os.path.join(HERE, 'codex_tex')
GUIDE = 768
TEXTURE = 512
# View name: direction from the object toward the camera.
VIEWS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (-1, 0, 0), 'right': (1, 0, 0), 'top': (0, 0, 1), 'bottom': (0, 0, -1)}
PAINT_VIEWS = ['front', 'back', 'left', 'right']
# Each design records its triangle budget, geometry source and explicit material classes.
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))


def view_frame(direction):
    d = Vector(direction).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    right = up.cross(d).normalized()
    return d, right, d.cross(right).normalized()



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
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
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


def load_rgba(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    rgba = np.array(image.pixels[:], np.float32).reshape(height, width, 4)[::-1].copy()
    bpy.data.images.remove(image)
    return rgba


def load_view(folder, kind, view, atlas=False):
    if not atlas:
        return load_rgba(os.path.join(folder, f'{kind}_{view}.png'))
    image = load_rgba(os.path.join(folder, f'{kind}_atlas.png'))
    height, width = image.shape[:2]
    if width % 3 or height % 2 or abs(width / height - 1.5) > 0.01:
        raise ValueError('View atlas must have a 3:2 canvas and three columns by two rows of square cells')
    index = list(VIEWS).index(view)
    x, y = (index % 3) * (width // 3), (index // 3) * (height // 2)
    return image[y:y + height // 2, x:x + width // 3].copy()


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
    pixels, positions, normals, interior = [], [], [], []
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
        weights = np.maximum(weights, 0)
        weights /= weights.sum(axis=1, keepdims=True)
        attribute = mesh.attributes.get('inner_wall')
        inner = attribute.data[tri.polygon_index].value if attribute else False
        interior.append(np.full(len(weights), inner, dtype=bool))
        pixels.append(p[inside].astype(int))
        positions.append(weights @ cos)
        normal = weights @ nos
        normals.append(normal / np.linalg.norm(normal, axis=1, keepdims=True))
    return np.concatenate(pixels), np.concatenate(positions), np.concatenate(normals), np.concatenate(interior)


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
    centre, scale, size = Vector(frame['centre']), frame['scale'], frame['size']
    pixels, positions, normals, interior = texels(obj)
    print('BAKE', name, len(pixels), 'texels')
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    accumulated = np.zeros((len(pixels), 3), np.float64)
    weight_sum = np.zeros(len(pixels), np.float64)
    material_votes = np.zeros((len(pixels), len(masks.NAMES)), np.float64)
    for view, direction in VIEWS.items():
        if view not in PAINT_VIEWS:
            continue
        folder = paint_dir or os.path.join(PAINT, name)
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
        if not (0.95 <= sx <= 1.05 and 0.95 <= sy <= 1.05):
            raise ValueError(f'{view}: painted silhouette registration outside 0.95-1.05: {sx}, {sy}')
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
        guide_coverage = erode(guide[..., 3] > .5, 2).astype(np.float32)
        coverage *= bilinear(guide_coverage[..., None], gx, gy)[:, 0]
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
        if not (0.95 <= msx <= 1.05 and 0.95 <= msy <= 1.05):
            raise ValueError(f'{view}: material mask registration outside 0.95-1.05: {msx}, {msy}')
        # register_atlases already placed this mask in the exact guide frame; a second box fit shifts edges.
        mx = np.clip(np.rint((gx + .5) * mask.shape[1] / size - .5).astype(int), 0, mask.shape[1] - 1)
        my = np.clip(np.rint((gy + .5) * mask.shape[0] / size - .5).astype(int), 0, mask.shape[0] - 1)
        samples = mask[my, mx]
        active = weight > 1e-4
        missing = active & (samples[:, 3] < 0.5)
        if missing.sum() / max(active.sum(), 1) > 0.02:
            raise ValueError(f'{view}: material mask misses {missing.sum()} of {active.sum()} painted texels')
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
    # Axial atlas views often invent a perspective. Bake the four verified side views, then carry nearby
    # painted material onto the small unseen outer caps in 3D; explicitly tagged inner walls stay leather.
    known = np.nonzero(covered_texels & ~interior)[0]
    assert len(known), 'No exterior painting samples'
    tree = KDTree(len(known))
    for index in known:
        tree.insert(Vector(positions[index]), int(index))
    tree.balance()
    nearest = np.nonzero(~covered_texels & ~interior)[0]
    for index in nearest:
        _, source_index, _ = tree.find(Vector(positions[index]))
        accumulated[index] = accumulated[source_index] / weight_sum[source_index]
        material_votes[index] = material_votes[source_index] / weight_sum[source_index]
        weight_sum[index] = 1
    covered_texels = weight_sum > 1e-4
    base = np.zeros((TEXTURE, TEXTURE, 3), np.float32)
    covered = np.zeros((TEXTURE, TEXTURE), bool)
    rows, cols = pixels[covered_texels, 1], pixels[covered_texels, 0]
    base[rows, cols] = accumulated[covered_texels] / weight_sum[covered_texels, None]
    covered[rows, cols] = True
    island = np.zeros((TEXTURE, TEXTURE), bool)
    island[pixels[:, 1], pixels[:, 0]] = True
    # Use the declared interior material's painted albedo; artificial darkening creates black UV triangles.
    unseen = island & ~covered
    if unseen.any():
        base[unseen] = masks.interior_albedo(base[rows, cols], material_votes[covered_texels],
                                            design['unseen_material'])
    base = fill(base, island)
    base = np.clip(base, 30 / 255, 243 / 255)
    # Roughness and binary metalness follow the painted material classes, including dark leather beside metal.
    luminance = base @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    mr = np.zeros((TEXTURE, TEXTURE, 3), np.float32)
    mr[pixels[:, 1], pixels[:, 0]] = masks.pbr(material_votes, design['unseen_material'])
    mr = fill(mr, island)
    mr[..., 2] = (mr[..., 2] >= .5).astype(np.float32)
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
    # Keep the painting frame reusable; rigidly pose the finished gauntlet palm-down before export.
    if design.get('family') == 'gauntlets':
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        obj.rotation_mode = 'XYZ'
        obj.rotation_euler.x = math.radians(design['export_rest_x_degrees'])
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        coordinates = [vertex.co.copy() for vertex in obj.data.vertices]
        low = Vector([min(point[i] for point in coordinates) for i in range(3)])
        high = Vector([max(point[i] for point in coordinates) for i in range(3)])
        assert high.z - low.z < max(high.x - low.x, high.y - low.y), name
        shift = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
        for vertex in obj.data.vertices:
            vertex.co -= shift
    pl.WORK = WORK
    pl.export(obj, name)
    print('BAKED', name, 'coverage', round(float(covered.sum() / max(island.sum(), 1)), 3))


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    {'guides': guides, 'bake': bake}[args[0]](*args[1:])


if __name__ == '__main__':
    main()
