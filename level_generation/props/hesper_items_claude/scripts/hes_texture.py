"""Codex-painted textures for a Hesper item model (the playbook's steps 5-6, with surface classes per face).

prep <icon>: work/<icon>.blend (build_hesper.py: one object, one material per surface class) unwrapped (Smart UV,
    islands packed with a margin) and saved as work/<icon>_prep.blend with each face's class recorded; then
    orthographic guide renders from the five VIEWS (codex_tex/<icon>/guide_<view>.png, 1024, transparent, one framing:
    views.json), lightly tinted by class (classes.png names the tints) for Codex to paint over, and the brief
    codex_tex/<icon>/CODEX_BRIEF.md with the icon's 1254 px Codex original as design_reference.png.
bake <icon>: the paintings (codex_tex/<icon>/paint_<view>.png) registered onto their guides by silhouette box and
    projected onto every texel (weight (n . view)^4 times the eroded alpha; texels a view cannot see skipped); gutters
    filled. Metallic and roughness by surface class (build_hesper.CLASSES; roughness a little lower where the painting
    is bright), emission = base colour x the class's strength, a tangent normal from the painting's fine detail.
    Writes work/<icon>_export.glb: colour and emission 512, normal and metallic-roughness 256 (the item caps), each
    averaged down from a 1024 bake.
reuv <icon>: the unwrap again on the prepared blend (after an unwrap change), keeping its guides.
Usage: blender --background --python hes_texture.py -- prep|bake|reuv <icon> [icon ...]"""
import json
import math
import os
import shutil
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'projectiles_claude',
                                'scripts'))
import projlib as pl  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ART = os.path.join(REPO, 'design', 'kreegan_world', 'art', 'item_icons')
WORK = os.path.join(HERE, 'work')
PAINT = os.path.join(HERE, 'codex_tex')
GUIDE = 1024
TEXTURE = 1024           # baked at 1024, written at half (colour) and a quarter (normal, metallic-roughness)
# How strongly the view facing a texel most squarely wins over the others (blending views ghosts misregistered detail).
FACING_POWER = 10
EDGE_PX = 6
NEAR_OCCLUSION = 0.03
VIEWS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (-1, 0, 0), 'right': (1, 0, 0), 'top': (0, 0, 1)}
# Used when its painting exists: a face Meshy built from the icon that rests face down (bottom-guide; see flip).
EXTRA_VIEWS = {'bottom': (0, 0, -1)}
# Surface class: (metallic, roughness, emission strength), as in build_hesper.py.
CLASSES = {'ceramic': (0, 0.42, 0), 'gold': (1, 0.32, 0), 'steel': (1, 0.5, 0), 'copper': (1, 0.38, 0),
           'resin': (0, 0.3, 0), 'bone': (0, 0.5, 0), 'glass': (0, 0.08, 0.15), 'crystal': (0, 0.08, 0.35),
           'glow': (0, 0.2, 1.0), 'screen': (0, 0.12, 0.6), 'leather': (0, 0.65, 0), 'cloth': (0, 0.8, 0),
           'paper': (0, 0.85, 0), 'food': (0, 0.9, 0), 'string': (0, 0.75, 0)}
TINTS = {'ceramic': (0.82, 0.82, 0.82), 'gold': (0.8, 0.72, 0.5), 'steel': (0.6, 0.62, 0.66),
         'copper': (0.75, 0.55, 0.45), 'resin': (0.42, 0.38, 0.46), 'bone': (0.78, 0.74, 0.66),
         'glass': (0.6, 0.72, 0.82), 'crystal': (0.62, 0.74, 0.86), 'glow': (0.66, 0.84, 0.95),
         'screen': (0.4, 0.46, 0.56), 'leather': (0.6, 0.5, 0.42), 'cloth': (0.72, 0.5, 0.5),
         'paper': (0.86, 0.83, 0.74), 'food': (0.6, 0.66, 0.46), 'string': (0.7, 0.62, 0.5),
         'auto': (0.7, 0.7, 0.7)}
AUTO_CLASSES = ('ceramic', 'gold', 'resin', 'glow')
DESCRIPTIONS = {}
for _name in ('items.json', 'items_p4.json', 'items_expansion.json'):
    for _entry in json.load(open(os.path.join(ART, _name))):
        DESCRIPTIONS[_entry['file'][:-4]] = _entry['description']


def view_frame(direction):
    d = Vector(direction).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    right = up.cross(d).normalized()
    return d, right, d.cross(right).normalized()


def unwrap(obj, names):
    """Smart UV project. A Meshy model splits into hundreds of islands: a tight margin and a repack keep its texel
    density (at 0.02 the Grav Boots used 9 % of the square and baked blocky)."""
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    margin = 0.004 if 'auto' in names else 0.02
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=margin)
    if margin < 0.02:
        bpy.ops.uv.pack_islands(rotate=True, margin=margin)
    bpy.ops.object.mode_set(mode='OBJECT')


def bottom_guide(icon):
    """guide_bottom.png of the prepared model, framed as its other guides (views.json)."""
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, f'{icon}_prep.blend'))
    folder = os.path.join(PAINT, icon)
    frame = json.load(open(os.path.join(folder, 'views.json')))
    scene = bpy.context.scene
    for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.resolution_x = scene.render.resolution_y = frame['size']
    scene.render.film_transparent = True
    camera = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = frame['scale']
    scene.collection.objects.link(camera)
    scene.camera = camera
    d, right, up = view_frame(EXTRA_VIEWS['bottom'])
    camera.location = Vector(frame['centre']) + d * frame['scale'] * 3
    # The camera's axes are the projection's own frame (right, up, toward the camera), so the guide matches bake().
    camera.rotation_euler = Matrix((right, up, d)).transposed().to_euler()
    scene.render.filepath = os.path.join(folder, 'guide_bottom.png')
    bpy.ops.render.render(write_still=True)
    print('GUIDE bottom', icon, 'screen right', [round(v, 2) for v in camera.matrix_world.col[0][:3]],
          'expected', [round(v, 2) for v in right])


def reuv(icon):
    """Unwraps work/<icon>_prep.blend again (its guides and paintings stay valid: they do not depend on the UVs)."""
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, f'{icon}_prep.blend'))
    obj = bpy.data.objects[icon]
    unwrap(obj, list(obj['surface_classes']))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{icon}_prep.blend'))
    print('REUV', icon)


def prep(icon):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, f'{icon}.blend'))
    obj = bpy.data.objects[icon]
    classes = [obj.material_slots[p.material_index].material.name.split('.')[0] for p in obj.data.polygons]
    attribute = obj.data.attributes.new(name='surface_class', type='INT', domain='FACE')
    names = sorted(set(classes))
    attribute.data.foreach_set('value', [names.index(c) for c in classes])
    obj['surface_classes'] = names
    unwrap(obj, names)
    folder = os.path.join(PAINT, icon)
    os.makedirs(folder, exist_ok=True)
    for slot in obj.material_slots:
        bsdf = next(n for n in slot.material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Base Color'].default_value = (*TINTS[slot.material.name.split('.')[0]], 1)
        bsdf.inputs['Metallic'].default_value = 0
        bsdf.inputs['Roughness'].default_value = 0.8
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
    world = bpy.data.worlds.new('w')
    scene.world = world
    world.use_nodes = True
    background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    background.inputs['Color'].default_value = (1, 1, 1, 1)
    background.inputs['Strength'].default_value = 0.6
    points = [v.co for v in obj.data.vertices]
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
        scene.render.filepath = os.path.join(folder, f'guide_{view}.png')
        bpy.ops.render.render(write_still=True)
    with open(os.path.join(folder, 'views.json'), 'w') as handle:
        json.dump({'centre': list(centre), 'scale': scale, 'size': GUIDE, 'views': VIEWS, 'classes': names},
                  handle, indent=1)
    bpy.data.objects.remove(camera)
    bpy.data.objects.remove(light)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{icon}_prep.blend'))
    write_brief(icon, names)
    print('PREP', icon, len(obj.data.polygons), 'faces', names)


def write_brief(icon, names):
    folder = os.path.join(PAINT, icon)
    designs = json.load(open(os.path.join(HERE, 'classification.json')))
    shutil.copyfile(os.path.join(ART, designs[icon]['master']), os.path.join(folder, 'design_reference.png'))
    tints = '' if names == ['auto'] else (
        ' Its parts are lightly tinted by material only to tell them apart: '
        + ', '.join(f'{name} (tinted {"light" if sum(TINTS[name]) > 2.2 else "mid"} '
                    f'{"grey" if name == "ceramic" else "tone"})' for name in names)
        + '. The tints are not colours to copy.')
    rel = os.path.relpath(folder, REPO)
    brief = f"""# Codex brief: paint the five views of the Hesper item model `{icon}` (texture source)

Scope: image generation only. Write ONLY into `{rel}/`. Do not edit any other file, do not run builds.

Use your built-in image generation tool. Inputs in this folder: `design_reference.png` (the approved item art: the
design, colour and material authority) and five guides `guide_front.png`, `guide_back.png`, `guide_left.png`,
`guide_right.png`, `guide_top.png`: plain orthographic renders of the EXACT 3D model from that side, transparent
background. Each guide fixes the silhouette, position, scale and every part's edge.{tints}

Item: {DESCRIPTIONS.get(icon, '')}

## Deliverables (1024 x 1024, transparent background, unresized returns)
- `paint_front.png`, `paint_back.png`, `paint_left.png`, `paint_right.png`, `paint_top.png`: each painted over its
  guide of the same name (the item seen from the front, back, left, right and from directly above).

Each painting keeps its guide's silhouette EXACTLY: the same outline, size and position in the frame, every part where
the guide has it; nothing added outside the silhouette, nothing cropped. Paint the design reference's surfaces onto
each part: white ceramic with fine wear, brushed gold, black-violet resin, glowing blue-white or orange light, glass
and crystal, leather, cloth or paper as the design shows, with its engraved lines, seams, panel joins and small
markings. Faces the design reference does not show (the back, the underside of a part) continue its materials
plausibly.

LIGHTING: a TEXTURE SOURCE (albedo). Even, flat, shadowless light from the viewer; no cast shadows, no ambient
occlusion darkening, no strong specular highlights or reflections (metal as its base colour with only a faint sheen),
no rim light, no background, no floor. Glowing parts are painted as their bright light colour.

Write `generation_runs.json` (view, prompt, inputs with sha256, output, selected, reason). At most one corrective
regeneration per view. If the tool returns another size, keep it unresized and record it.

Checks per image: silhouette identical to the guide; colours and materials match the design reference; flat even light
with no shadows or hot highlights; transparent background; no text or letters.
"""
    with open(os.path.join(folder, 'CODEX_BRIEF.md'), 'w') as handle:
        handle.write(brief)


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
    """Every covered texel: pixel, position, smooth normal and surface class index."""
    mesh = obj.data
    mesh.calc_loop_triangles()
    uv = mesh.uv_layers.active.data
    labels = mesh.attributes['surface_class'].data
    pixels, positions, normals, classes = [], [], [], []
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
        inside = (w0 >= -0.03) & (w1 >= -0.03) & (w2 >= -0.03)
        inside &= (p[:, 0] >= 0) & (p[:, 0] < TEXTURE) & (p[:, 1] >= 0) & (p[:, 1] < TEXTURE)
        if not inside.any():
            continue
        weights = np.stack([w0, w1, w2], 1)[inside]
        pixels.append(p[inside].astype(int))
        positions.append(weights @ cos)
        normal = weights @ nos
        normals.append(normal / np.linalg.norm(normal, axis=1, keepdims=True))
        classes.append(np.full(len(weights), labels[tri.polygon_index].value, int))
    return (np.concatenate(pixels), np.concatenate(positions), np.concatenate(normals), np.concatenate(classes))


def fill(rgb, covered, steps=48):
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
    rgb[~known] = rgb[known].mean(0) if known.any() else 0.5
    return rgb


def half(image):
    return (image[0::2, 0::2] + image[1::2, 0::2] + image[0::2, 1::2] + image[1::2, 1::2]) / 4


def save_png(rgb, path, colorspace='sRGB'):
    height, width = rgb.shape[:2]
    image = bpy.data.images.new(os.path.basename(path), width, height, alpha=False)
    image.colorspace_settings.name = colorspace
    image.pixels[:] = np.clip(np.concatenate([rgb[::-1], np.ones((height, width, 1), np.float32)], -1), 0, 1).ravel()
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    return image


def bake(icon):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, f'{icon}_prep.blend'))
    obj = bpy.data.objects[icon]
    folder = os.path.join(PAINT, icon)
    frame = json.load(open(os.path.join(folder, 'views.json')))
    names = frame['classes']
    centre, scale, size = Vector(frame['centre']), frame['scale'], frame['size']
    pixels, positions, normals, classes = texels(obj)
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    accumulated = np.zeros((len(pixels), 3), np.float64)
    weight_sum = np.zeros(len(pixels), np.float64)
    seen = np.zeros(len(pixels), bool)
    registration = {}
    for view, direction in {**VIEWS, **EXTRA_VIEWS}.items():
        path = os.path.join(folder, f'paint_{view}.png')
        if not os.path.exists(path):
            print('  no painting for', view)
            continue
        paint = load_rgba(path)
        guide = load_rgba(os.path.join(folder, f'guide_{view}.png'))
        if paint.shape[0] != size or paint.shape[1] != size:
            ys = (np.arange(size) * paint.shape[0] / size).astype(int)
            xs = (np.arange(size) * paint.shape[1] / size).astype(int)
            paint = paint[ys][:, xs]
        gx0, gx1, gy0, gy1 = bbox(guide[..., 3])
        px0, px1, py0, py1 = bbox(paint[..., 3])
        sx, sy = (px1 - px0) / max(gx1 - gx0, 1), (py1 - py0) / max(gy1 - gy0, 1)
        registration[view] = [round(float(sx), 3), round(float(sy), 3)]
        # Samples near the painted outline are where a painting drifts from its guide: only the inside counts.
        alpha = erode(paint[..., 3] > 0.5, EDGE_PX).astype(np.float32)
        d, right, up = (np.array(v) for v in view_frame(direction))
        facing = normals @ d
        visible = np.zeros(len(pixels), bool)
        # An occluder within NEAR_OCCLUSION of the model's size (a fold, a rib beside the texel) does not hide it: the
        # flicker between views it caused patched organic Meshy surfaces; the painting there shows that bump anyway.
        near = NEAR_OCCLUSION * scale
        for index in np.nonzero(facing > 0.05)[0]:
            origin = Vector(positions[index] + normals[index] * 1e-3 + d * 1e-3)
            hit = bvh.ray_cast(origin, Vector(d))
            visible[index] = hit[0] is None or hit[3] < near
        relative = positions - np.array(centre)
        gx = (relative @ right / scale + 0.5) * size - 0.5
        gy = (0.5 - relative @ up / scale) * size - 0.5
        x = px0 + (gx - gx0) * sx
        y = py0 + (gy - gy0) * sy
        colour = bilinear(paint[..., :3], x, y)
        coverage = bilinear(alpha[..., None], x, y)[:, 0]
        weight = np.where(visible, np.clip(facing, 0, 1) ** FACING_POWER * coverage, 0.0)
        seen |= visible & (coverage > 0.5)
        accumulated += colour * weight[:, None]
        weight_sum += weight
    # Covered: some view sees the texel inside its painting. The weights only rank the views (a texel facing every
    # view obliquely has tiny ones), so they are not the coverage test.
    covered_texels = seen & (weight_sum > 0)
    base = np.zeros((TEXTURE, TEXTURE, 3), np.float32)
    covered = np.zeros((TEXTURE, TEXTURE), bool)
    class_map = np.full((TEXTURE, TEXTURE), -1, int)
    class_map[pixels[:, 1], pixels[:, 0]] = classes
    rows, cols = pixels[covered_texels, 1], pixels[covered_texels, 0]
    base[rows, cols] = accumulated[covered_texels] / weight_sum[covered_texels, None]
    covered[rows, cols] = True
    island = class_map >= 0
    # Texels no view sees (inner faces of a pair, crevices, undersides) take the colour of the nearest painted texel of
    # their own class on the surface, a little darker; a class nothing paints takes its tint.
    texel_class = classes
    for index, name in enumerate(names):
        seen_index = np.nonzero(covered_texels & (texel_class == index))[0]
        unseen_index = np.nonzero(~covered_texels & (texel_class == index))[0]
        if not len(unseen_index):
            continue
        if not len(seen_index):
            base[pixels[unseen_index, 1], pixels[unseen_index, 0]] = np.array(TINTS[name], np.float32) * 0.7
        else:
            tree = KDTree(len(seen_index))
            for order, texel in enumerate(seen_index):
                tree.insert(positions[texel], order)
            tree.balance()
            source = np.array([tree.find(positions[texel])[1] for texel in unseen_index])
            base[pixels[unseen_index, 1], pixels[unseen_index, 0]] = \
                base[pixels[seen_index[source], 1], pixels[seen_index[source], 0]] * 0.85
        covered[pixels[unseen_index, 1], pixels[unseen_index, 0]] = True
    base = fill(base, covered)
    class_map = np.where(island, class_map, 0)
    if 'auto' in names:
        # A Meshy model's single class: each texel's surface from its painted colour.
        names = names + [name for name in AUTO_CLASSES if name not in names]
        auto = island & (class_map == names.index('auto'))
        r, g, b = base[..., 0], base[..., 1], base[..., 2]
        value, low = base.max(-1), base.min(-1)
        saturation = (value - low) / np.maximum(value, 1e-3)
        # Gold: a saturated yellow-orange hue; beige cloth, bone and worn ceramic are less saturated (as gold they were
        # metallic mirrors on the Weave Suit).
        chroma = np.maximum(value - low, 1e-6)
        hue = np.where(value == r, ((g - b) / chroma) % 6, np.where(value == g, (b - r) / chroma + 2,
                                                                    (r - g) / chroma + 4)) * 60
        gold = (hue > 28) & (hue < 56) & (saturation > 0.45) & (value > 0.3) & (value < 0.97)
        glow = (value > 0.82) & (saturation > 0.3) & ((b > r + 0.15) | (r > g + 0.25))
        resin = (value < 0.32) & ~gold
        choice = np.where(glow, names.index('glow'), np.where(gold, names.index('gold'),
                          np.where(resin, names.index('resin'), names.index('ceramic'))))
        class_map = np.where(auto, choice, class_map)
    table = np.array([CLASSES.get(name, (0, 0.5, 0)) for name in names], np.float32)
    luminance = base @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    lo, hi = np.percentile(luminance[island], [5, 95])
    t = np.clip((luminance - lo) / max(hi - lo, 1e-3), 0, 1)
    rough = np.clip(table[class_map, 1] + 0.08 - 0.16 * t, 0.04, 1)
    mr = np.stack([np.ones_like(rough), rough, table[class_map, 0]], -1)
    emission = base * table[class_map, 2][..., None]
    blurred = luminance.copy()
    for _ in range(3):
        blurred = (blurred + np.roll(blurred, 1, 0) + np.roll(blurred, -1, 0) + np.roll(blurred, 1, 1)
                   + np.roll(blurred, -1, 1)) / 5
    detail = (luminance - blurred) * 1.5
    inner = erode(island, 2)
    dx = np.where(inner, (np.roll(detail, -1, 1) - np.roll(detail, 1, 1)) / 2, 0)
    dy = np.where(inner, (np.roll(detail, -1, 0) - np.roll(detail, 1, 0)) / 2, 0)
    normal = np.stack([-dx * 12, -dy * 12, np.ones_like(dx)], -1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    # Written at the ground items' sizes (tools/cook/model_textures.yml): colour 512, normal and metallic-roughness
    # 256, each averaged down from the 1024 bake.
    base, emission = half(base), half(emission)
    mr = half(half(mr))
    normal = half(half(normal))
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    textures = os.path.join(WORK, 'textures')
    os.makedirs(textures, exist_ok=True)
    material = bpy.data.materials.new(icon)
    material.use_nodes = True
    nt = material.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    base_node = nt.nodes.new('ShaderNodeTexImage')
    base_node.image = save_png(base[::-1], os.path.join(textures, f'{icon}_basecolor.png'))
    nt.links.new(base_node.outputs['Color'], bsdf.inputs['Base Color'])
    mr_node = nt.nodes.new('ShaderNodeTexImage')
    mr_node.image = save_png(mr[::-1], os.path.join(textures, f'{icon}_mr.png'), 'Non-Color')
    separate = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mr_node.outputs['Color'], separate.inputs['Color'])
    nt.links.new(separate.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(separate.outputs['Blue'], bsdf.inputs['Metallic'])
    normal_node = nt.nodes.new('ShaderNodeTexImage')
    normal_node.image = save_png((normal * 0.5 + 0.5)[::-1], os.path.join(textures, f'{icon}_normal.png'),
                                 'Non-Color')
    mapping = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(normal_node.outputs['Color'], mapping.inputs['Color'])
    nt.links.new(mapping.outputs['Normal'], bsdf.inputs['Normal'])
    glows = bool(table[:, 2].any())
    if glows:
        emission_node = nt.nodes.new('ShaderNodeTexImage')
        emission_node.image = save_png(emission[::-1], os.path.join(textures, f'{icon}_emissive.png'))
        nt.links.new(emission_node.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
    obj.data.materials.clear()
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.material_index = 0
    # meshy_rest.json `flip` / `turn`: a rest pose corrected after the bake, which keeps the paintings valid: `flip`
    # turns a model that landed face down over (180 degrees about its long horizontal axis); `turn` is any Euler
    # rotation in degrees (the Founder's Head laid face up, so the face shows from above).
    rest = json.load(open(os.path.join(HERE, 'meshy_rest.json'))).get(icon, {})
    if rest.get('flip') or rest.get('turn'):
        if rest.get('flip'):
            obj.data.transform(Matrix.Rotation(math.pi, 4, 'Y'))
        if rest.get('turn'):
            obj.data.transform(Euler([math.radians(a) for a in rest['turn']]).to_matrix().to_4x4())
        points = [v.co for v in obj.data.vertices]
        low = Vector([min(p[i] for p in points) for i in range(3)])
        high = Vector([max(p[i] for p in points) for i in range(3)])
        obj.data.transform(Matrix.Translation((-(low.x + high.x) / 2, -(low.y + high.y) / 2, -low.z)))
    # Triangulated first: projlib's winding fix measures a piece's volume over its triangles only, so a correct
    # piece of quads and triangles (a lathed socket) would come out flipped.
    triangulated = bmesh.new()
    triangulated.from_mesh(obj.data)
    bmesh.ops.triangulate(triangulated, faces=triangulated.faces)
    triangulated.to_mesh(obj.data)
    triangulated.free()
    # An open Meshy shell (a garment's armholes, a boot's shaft) has no inner wall: drawn single-sided, its inside
    # would be see-through on the ground.
    probe = bmesh.new()
    probe.from_mesh(obj.data)
    open_shell = 'auto' in frame['classes'] and any(edge.is_boundary for edge in probe.edges)
    probe.free()
    settings = {'emissive': [1, 1, 1]} if glows else {}
    if open_shell:
        settings['double'] = True
    pl.WORK = WORK
    pl.export(obj, icon, {icon: settings})
    obj.data.calc_loop_triangles()
    receipt = {'triangles': len(obj.data.loop_triangles), 'registration': registration, 'classes': names,
               'coverage': round(float(covered_texels.mean()), 3), 'emissive': glows, 'double_sided': open_shell}
    with open(os.path.join(folder, 'bake.json'), 'w') as handle:
        json.dump(receipt, handle, indent=1)
    print('BAKED', icon, json.dumps(receipt))


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    for icon in args[1:]:
        {'prep': prep, 'bake': bake, 'reuv': reuv, 'bottom-guide': bottom_guide}[args[0]](icon)


main()
