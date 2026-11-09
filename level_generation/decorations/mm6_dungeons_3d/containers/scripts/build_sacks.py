"""MM6 dungeon sacks, revision 2: `bag_a` (a squat napped-leather pouch tied below a frilled mouth with a pale rope
whose end hangs down the front), `bag01` (a tall burlap sack gathered into a twisted tip, leaning a little) and
`floursac` (a wide, slumped burlap sack with its mouth crumpled shut).

Each sack is one soft body of revolution traced from the sprite's half-widths (fractions of the content height),
elliptical in depth, with noise folds displaced along the surface. Its texture coordinates are the body's own
parameters (u around, v along the profile by arc length, both 0..1), so every LOD, decimated from the same dense
body, shares one unique texture set:

  bake    dense body (about 100000 triangles) -> LOD0 body: tangent- and object-space normals of the folds
          (selected to active), ambient occlusion with the floor, and a data pass (fold displacement, height, radius) as float arrays in
          work/bake/<prop>_*.npy plus work/bake/<prop>.json (weave tiling from the body's real size);
          saves work/<prop>_geo.blend.
  (compose_sacks.py, system python: Poly Haven hessian weave + native sprite shading and palette -> textures/)
  export  work/<prop>_geo.blend + textures/<prop>_{basecolor,normal,mr}.png -> work/<prop>_export.glb
          (COLOR_0 white: occlusion and colour are in the unique base colour).

Usage: blender --background --python build_sacks.py -- bag_a|bag01|floursac bake|export"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import containers_lib as cl  # noqa: E402

pl = cl.pl
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['bag_a', 'bake']
PROP, STAGE = ARGS[0], ARGS[1]
BAKE = os.path.join(cl.WORK, 'bake')
BAKE_SIZE = 1024

# Profiles (half-width, height) as fractions of the content height, bottom centre to the top (or into the mouth).
# tile: the hessian tile's size in metres (the sprites' weave is much coarser than real sackcloth).
SPECS = {
    'bag_a': {
        'height': 47, 'depth': 0.95, 'base': 'BagA', 'widen': 1.1, 'tile': 0.30, 'specular': 0.2,
        'profile': [(0, 0), (0.40, 0), (0.47, 0.02), (0.515, 0.06), (0.54, 0.12), (0.552, 0.19), (0.552, 0.25),
                    (0.535, 0.31), (0.495, 0.38), (0.445, 0.45), (0.39, 0.52), (0.335, 0.59), (0.275, 0.66),
                    (0.21, 0.72), (0.15, 0.765), (0.125, 0.785), (0.145, 0.805), (0.19, 0.84), (0.22, 0.875),
                    (0.225, 0.905), (0.20, 0.925), (0.16, 0.915), (0.11, 0.88), (0.05, 0.85), (0, 0.845)],
        'lean': [(0, 0), (0.6, 0), (1.0, 0.03)],
        # gathers: vertical folds radiating down from the neck, strongest just below it, fading toward the bulge
        'folds': {'amp': [(0, 0), (0.05, 0.004), (0.35, 0.008), (0.6, 0.016), (0.75, 0.026), (0.8, 0.03),
                          (1.0, 0.04)], 'lumps': [(0, 0), (0.05, 0.008), (0.3, 0.012), (0.7, 0.006), (1.0, 0.0)],
                  'scale': (3.6, 0.5), 'angular': 10, 'ridge': 0.7, 'lift': 0.025, 'fine': 0.25},
        'wrinkle': 0.0025,
    },
    'bag01': {
        'height': 92, 'depth': 0.78, 'base': 'Bag01', 'tile': 0.85, 'specular': 0.25,
        'profile': [(0, 0), (0.22, 0), (0.30, 0.02), (0.345, 0.06), (0.365, 0.12), (0.365, 0.18), (0.35, 0.25),
                    (0.325, 0.32), (0.305, 0.40), (0.285, 0.47), (0.272, 0.55), (0.258, 0.62), (0.232, 0.68),
                    (0.20, 0.74), (0.163, 0.80), (0.124, 0.85), (0.088, 0.90), (0.058, 0.945), (0.04, 0.975),
                    (0.025, 0.995), (0, 1.0)],
        'lean': [(0, 0.005), (0.3, -0.012), (0.5, -0.012), (0.7, -0.045), (0.85, -0.055), (1.0, -0.075)],
        # broad soft diagonal folds over a lumpy body, thin gathers twisted into the tip
        'folds': {'amp': [(0, 0), (0.05, 0.012), (0.6, 0.015), (0.8, 0.03), (0.95, 0.03), (1.0, 0.0)],
                  'lumps': [(0, 0), (0.06, 0.01), (0.2, 0.02), (0.45, 0.035), (0.7, 0.03), (0.95, 0.01), (1.0, 0.0)],
                  'scale': (2.2, 0.6), 'angular': 6, 'ridge': 0.8, 'lift': 0.0, 'twist': 1.4, 'fine': 0.3},
        'lines': {'count': 9, 'seed': 17, 'z': (0.18, 0.75), 'length': (0.35, 0.7), 'slope': (0.6, 1.5),
                  'bias': 0.8, 'width': (0.25, 0.45), 'amp': (0.04, 0.07)},
        'wrinkle': 0.004,
    },
    'floursac': {
        'height': 82, 'depth': 0.74, 'base': 'FlourSack', 'flatten': 0.5, 'tile': 0.8, 'specular': 0.25,
        'profile': [(0, 0), (0.40, 0), (0.48, 0.03), (0.535, 0.09), (0.555, 0.15), (0.54, 0.25), (0.495, 0.35),
                    (0.455, 0.47), (0.425, 0.58), (0.38, 0.665), (0.355, 0.735), (0.385, 0.80), (0.425, 0.87),
                    (0.43, 0.92), (0.39, 0.96), (0.33, 0.975), (0.25, 0.94), (0.13, 0.89), (0, 0.87)],
        'lean': [(0, 0), (1.0, 0.01)],
        # crumpled creases strongest under the mouth, a smoother bulging lower half
        'folds': {'amp': [(0, 0), (0.05, 0.01), (0.4, 0.015), (0.65, 0.04), (0.85, 0.06), (1.0, 0.05)],
                  'lumps': [(0, 0), (0.05, 0.025), (0.35, 0.04), (0.7, 0.03), (1.0, 0.015)],
                  'scale': (2.6, 0.55), 'angular': 6, 'ridge': 0.85, 'lift': 0.05, 'twist': 0.6, 'fine': 0.3},
        'lines': {'count': 11, 'seed': 5, 'z': (0.2, 0.78), 'length': (0.3, 0.6), 'slope': (0.5, 1.4),
                  'bias': 0.5, 'width': (0.18, 0.36), 'amp': (0.03, 0.055)},
        'wrinkle': 0.004,
    },
}
SPEC = SPECS[PROP]
H = cl.u(SPEC['height'])
BUDGETS = (1500, 600, 250)


def interpolate(table, x):
    if x <= table[0][0]:
        return table[0][1]
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return table[-1][1]


def resample(profile, count):
    """Points evenly spaced along the profile polyline (smoothed by a light Chaikin pass first)."""
    pts = [Vector((r, 0, z)) for r, z in profile]
    for _ in range(2):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [a * 0.75 + b * 0.25, a * 0.25 + b * 0.75]
        out.append(pts[-1])
        pts = out
    lengths = [0.0]
    for a, b in zip(pts, pts[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    result = []
    for k in range(count + 1):
        target = lengths[-1] * k / count
        i = max(0, min(len(pts) - 2, next(j for j in range(len(lengths) - 1) if lengths[j + 1] >= target - 1e-12)))
        span = lengths[i + 1] - lengths[i]
        f = 0 if span == 0 else (target - lengths[i]) / span
        p = pts[i].lerp(pts[i + 1], f)
        result.append((p.x, p.z))
    result[0] = (0.0, profile[0][1])
    result[-1] = (profile[-1][0], profile[-1][1])
    return result


def make_fold_lines():
    """Explicit cloth folds: each a soft ridge with a crease along one side, running diagonally over part of the
    height (centre angle drifting with height), fading at both ends. Noise creases alone close into loops."""
    spec = SPEC.get('lines')
    if not spec:
        return []
    rng = random.Random(spec['seed'])
    lines = []
    for k in range(spec['count']):
        zc = rng.uniform(*spec['z'])
        half = rng.uniform(*spec['length']) / 2
        sign = 1 if rng.random() < spec.get('bias', 0.5) else -1
        lines.append({'theta': 2 * math.pi * (k + rng.uniform(-0.3, 0.3)) / spec['count'],
                      'z0': zc - half, 'z1': zc + half, 'zc': zc, 'slope': sign * rng.uniform(*spec['slope']),
                      'width': rng.uniform(*spec['width']), 'amp': rng.uniform(*spec['amp']),
                      'side': rng.choice((-1, 1))})
    return lines


def fold_lines_value(theta, z):
    total = 0.0
    for line in FOLD_LINES:
        if not line['z0'] < z < line['z1']:
            continue
        env = math.sin(math.pi * (z - line['z0']) / (line['z1'] - line['z0'])) ** 0.8
        centre = line['theta'] + line['slope'] * (z - line['zc'])
        d = math.atan2(math.sin(theta - centre), math.cos(theta - centre)) / line['width']
        ridge = math.exp(-d * d) - 0.75 * math.exp(-((d - 1.25 * line['side']) / 0.45) ** 2)
        total += line['amp'] * env * ridge
    return total


def surface_point(samples, rings, t, theta, seed=0.0, fine_detail=True):
    """Body point at profile parameter t (ring index / rings) and angle theta; returns (position, fold value)."""
    folds = SPEC['folds']
    r, z = samples[round(t * rings)]
    c, s = math.cos(theta), math.sin(theta)
    # creases follow a twist that varies with height and a low-frequency warp, so they do not run in step
    warp = folds.get('warp', 0.0) * noise.noise(Vector((c * 1.1, s * 1.1, z * 1.7)) + Vector((5.2, seed, 0.4)))
    twist = folds.get('twist', 0.0) * z + warp
    q = Vector((math.cos(theta + twist) * folds['angular'] / 6.0, math.sin(theta + twist) * folds['angular'] / 6.0, 0))
    sx, sz = folds['scale']
    n = noise.noise(Vector((q.x * sx, q.y * sx, z * sz * 4)) + Vector((seed, 3.1, 7.7)))
    ridge = (min(1.0, abs(n) * 1.6)) ** 0.7 * 2.0 - 1.0          # rounded bulges, sharp creases
    fine = noise.noise(Vector((q.x * sx * 2.7, q.y * sx * 2.7, z * sz * 9)) + Vector((1.3, seed, 2.2)))
    d = (ridge * folds['ridge'] + n * (1 - folds['ridge'])) * 0.8 + fine * folds.get('fine', 0.35)
    amp = interpolate(folds['amp'], z) if r > 1e-6 else 0.0
    if z < 0.002:
        amp = 0.0
    # broad soft lumps (the stuffing pressing the cloth out)
    lumps = folds.get('lumps')
    if lumps and r > 1e-6 and z >= 0.002:
        lump = noise.noise(Vector((c * 1.4, s * 1.4, z * 2.4)) + Vector((2.7, 9.1, seed)))
        lump += 0.5 * noise.noise(Vector((c * 2.8, s * 2.8, z * 4.4)) + Vector((7.3, seed, 3.3)))
        d_lump = interpolate(lumps, z) * lump
    else:
        d_lump = 0.0
    wrinkle = 0.0
    if fine_detail and r > 1e-6 and z > 0.01:
        # small crumples for the normal map only (the LODs cannot carry them as geometry)
        w = noise.noise(Vector((c * 9.0, s * 9.0, z * 14.0)) + Vector((seed, 8.3, 1.9)))
        w2 = noise.noise(Vector((c * 21.0, s * 21.0, z * 30.0)) + Vector((4.1, seed, 6.6)))
        wrinkle = (w * 0.7 + w2 * 0.3) * SPEC['wrinkle'] / H * min(1.0, z / 0.05)
    d_lines = fold_lines_value(theta, z) if r > 1e-6 and z >= 0.002 else 0.0
    rr = max(0.0, r + amp * d + d_lump + d_lines + wrinkle)
    lift = folds.get('lift', 0.0) * noise.noise(Vector((c * 2.2, s * 2.2, 5.0 + seed))) * cl.smoothstep(0.85, 1, z)
    widen = SPEC.get('widen', 1.0)
    x = rr * c * widen + interpolate(SPEC['lean'], z)
    flatten = 1.0 - SPEC.get('flatten', 0.0) * cl.smoothstep(0.55, 0.95, z)      # mouth pressed shut
    x += rr * c * (1.0 - flatten) * 0.35
    y = rr * s * SPEC['depth'] * widen * flatten
    return Vector((x * H, y * H, max(0.0, (z + lift) * H))), amp * d + d_lump + d_lines


def sack_body(name, rings, segments, mat, fine_detail):
    """Grid body with u = segment / segments, v = arc length / total (per mean ring spacing); a 'fold' point
    attribute holds the fold displacement (fraction of the height). Poles collapse to one vertex."""
    samples = resample(SPEC['profile'], rings)
    grid_points = []
    grid_folds = []
    for i in range(rings + 1):
        row = [surface_point(samples, rings, i / rings, 2 * math.pi * k / segments, fine_detail=fine_detail)
               for k in range(segments)]
        grid_points.append([p for p, _ in row])
        grid_folds.append([f for _, f in row])
    lengths = [0.0]
    for i in range(rings):
        step = sum((grid_points[i + 1][k] - grid_points[i][k]).length for k in range(segments)) / segments
        lengths.append(lengths[-1] + step)
    total = lengths[-1]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    fold_layer = bm.verts.layers.float.new('fold')
    grid = []
    for i in range(rings + 1):
        pts = grid_points[i]
        if max((p - pts[0]).length for p in pts) < 1e-6:
            v = bm.verts.new(pts[0])
            v[fold_layer] = 0.0
            grid.append([v] * segments)
        else:
            row = []
            for p, f in zip(pts, grid_folds[i]):
                v = bm.verts.new(p)
                v[fold_layer] = f
                row.append(v)
            grid.append(row)
    for i in range(rings):
        for k in range(segments):
            k2 = (k + 1) % segments
            quad = [grid[i][k], grid[i][k2], grid[i + 1][k2], grid[i + 1][k]]
            coords = [(k / segments, lengths[i] / total), ((k + 1) / segments, lengths[i] / total),
                      ((k + 1) / segments, lengths[i + 1] / total), (k / segments, lengths[i + 1] / total)]
            keep = []
            for vert, coord in zip(quad, coords):
                if not any(vert is kept[0] for kept in keep):
                    keep.append((vert, coord))
            if len(keep) < 3:
                continue
            if len(keep) == 3 and quad[0] is quad[1]:      # bottom pole: centre the pole's coordinate
                pass
            face = bm.faces.new([kept[0] for kept in keep])
            for loop, (_, coord) in zip(face.loops, keep):
                loop[uv].uv = coord
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mid = samples[len(samples) // 2][0]
    obj = pl.to_object(name, bm, mat, True)
    return obj, total * H, mid * H


def rope_parts(solid, level, mat):
    """bag_a: a rope wound twice round the neck, a knot at the front and the end hanging down the front."""
    bvh = BVHTree.FromObject(solid, bpy.context.evaluated_depsgraph_get())
    radius = 0.017 * H
    sides = (6, 5, 4)[level]

    def surface(angle, z, offset):
        d = Vector((math.cos(angle), math.sin(angle), 0))
        origin = Vector((0, 0, z)) + d * H
        hit, normal, *_ = bvh.ray_cast(origin, -d, 2 * H)
        if hit is None:
            hit = Vector((0, 0, z))
        return hit + d * offset

    parts = []
    loops = (2, 1, 1)[level]
    for k in range(loops):
        z = (0.772 + 0.03 * k) * H
        count = (16, 12, 8)[level]
        path = [surface(2 * math.pi * i / count, z + 0.006 * H * math.sin(i * 1.7), radius * 0.8)
                for i in range(count)]
        parts.append(cl.sweep(f'rope{k}', path, radius, sides, mat, u_repeat=1.0, v_scale=1.0 / (H * 0.25),
                              closed=True))
    front = -math.pi / 2 + 0.25
    if level < 2:
        knot = surface(front, 0.78 * H, radius * 1.2)
        parts.append(cl.sweep('knot', [knot + Vector((0, 0, -0.022 * H)), knot + Vector((0, 0, 0.022 * H))],
                              radius * 1.6, sides, mat, v_scale=4.0))
    steps = (10, 6, 4)[level]
    path = []
    for i in range(steps + 1):
        z = (0.76 - 0.43 * i / steps) * H
        path.append(surface(front + 0.1 * math.sin(i * 0.6), z, radius * 0.9))
    parts.append(cl.sweep('cord', path, lambda t: radius * (1.0 - 0.15 * t), sides, mat, v_scale=1.0 / (H * 0.25)))
    if level < 2:
        tail = path[-1]
        parts.append(cl.sweep('end', [tail, tail + Vector((0, -0.01 * H, -0.04 * H))],
                              lambda t: radius * (1.25 - 0.5 * t), sides, mat, v_scale=4.0))
    return parts


FOLD_LINES = make_fold_lines()


def plain_material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m


def bake_image(name, mat):
    image = bpy.data.images.new(name, BAKE_SIZE, BAKE_SIZE, float_buffer=True, alpha=False)
    image.colorspace_settings.is_data = True
    nt = mat.node_tree
    for n in nt.nodes:
        n.select = False
    node = nt.nodes.new('ShaderNodeTexImage')
    node.image = image
    node.select = True
    nt.nodes.active = node
    return image


def save_array(image, path):
    pixels = np.empty(len(image.pixels), np.float32)
    image.pixels.foreach_get(pixels)
    np.save(path, pixels.reshape(image.size[1], image.size[0], 4)[..., :3])   # row 0 = v 0


def bake():
    pl.reset()
    scene = bpy.context.scene
    try:
        scene.render.engine = 'CYCLES'
    except TypeError as error:
        raise SystemExit(f'no Cycles: {error}')
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    body_mat = plain_material('Body')
    source_mat = plain_material('BakeSource')
    dense, length, mid_radius = sack_body('dense', 200, 256, source_mat, True)
    # LOD bodies from a geometric copy without the normal-map wrinkles (decimation keeps the folds only)
    smooth, _, _ = sack_body('smooth', 72, 96, body_mat, False)
    rope_mat = cl.material('Rope', 'rope') if PROP == 'bag_a' else None
    lods = []
    for level, budget in enumerate(BUDGETS):
        parts = rope_parts(smooth, level, rope_mat) if PROP == 'bag_a' else []
        extra = sum(pl.triangles(p) for p in parts)
        solid = cl.decimated(smooth, f'solid{level}', budget - extra)
        lods.append((solid, parts))
    bpy.data.objects.remove(smooth)
    # Ground plane for the floor occlusion (not a bake source).
    bpy.ops.mesh.primitive_plane_add(size=H * 6, location=(0, 0, -0.0005))
    ground = bpy.context.active_object
    ground.name = 'ground'

    # Source material: emission = (fold, height, radius) for the data pass; plain diffuse otherwise.
    nt = source_mat.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    attr = nt.nodes.new('ShaderNodeAttribute')
    attr.attribute_name = 'fold'
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs['Vector'])
    zscale = nt.nodes.new('ShaderNodeMath')
    zscale.operation = 'DIVIDE'
    zscale.inputs[1].default_value = H
    nt.links.new(sep.outputs['Z'], zscale.inputs[0])
    radius = nt.nodes.new('ShaderNodeVectorMath')
    radius.operation = 'LENGTH'
    flat = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(sep.outputs['X'], flat.inputs['X'])
    nt.links.new(sep.outputs['Y'], flat.inputs['Y'])
    nt.links.new(flat.outputs['Vector'], radius.inputs[0])
    rscale = nt.nodes.new('ShaderNodeMath')
    rscale.operation = 'DIVIDE'
    rscale.inputs[1].default_value = H
    nt.links.new(radius.outputs['Value'], rscale.inputs[0])
    combine = nt.nodes.new('ShaderNodeCombineColor')
    nt.links.new(attr.outputs['Fac'], combine.inputs['Red'])
    nt.links.new(zscale.outputs['Value'], combine.inputs['Green'])
    nt.links.new(rscale.outputs['Value'], combine.inputs['Blue'])
    emission = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(combine.outputs['Color'], emission.inputs['Color'])
    bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)

    world = bpy.data.worlds.new('bake')
    scene.world = world
    world.light_settings.distance = H * 0.35

    lod0 = lods[0][0]
    os.makedirs(BAKE, exist_ok=True)
    bake_settings = scene.render.bake
    bake_settings.use_selected_to_active = True
    bake_settings.cage_extrusion = H * 0.06
    bake_settings.max_ray_distance = H * 0.15
    bake_settings.margin = 16
    bake_settings.margin_type = 'EXTEND'
    bpy.ops.object.select_all(action='DESELECT')
    dense.select_set(True)
    lod0.select_set(True)
    bpy.context.view_layer.objects.active = lod0

    def run(kind, image_name, target_mat, **kwargs):
        image = bake_image(image_name, target_mat)
        bpy.ops.object.bake(type=kind, **kwargs)
        save_array(image, os.path.join(BAKE, f'{PROP}_{image_name}.npy'))
        target_mat.node_tree.nodes.remove(target_mat.node_tree.nodes.active)

    run('NORMAL', 'normal', body_mat, normal_space='TANGENT')
    run('NORMAL', 'wnormal', body_mat, normal_space='OBJECT')
    # Occlusion on the dense body itself (same texture coordinates), with the LOD copies out of the scene's rays.
    hidden = [o for o in bpy.data.objects if o not in (dense, ground)]
    for o in hidden:
        o.hide_render = True
    bake_settings.use_selected_to_active = False
    bpy.ops.object.select_all(action='DESELECT')
    dense.select_set(True)
    bpy.context.view_layer.objects.active = dense
    run('AO', 'ao', source_mat)
    for o in hidden:
        o.hide_render = False
    bake_settings.use_selected_to_active = True
    dense.select_set(True)
    lod0.select_set(True)
    bpy.context.view_layer.objects.active = lod0
    nt.links.new(emission.outputs['Emission'], out.inputs['Surface'])
    run('EMIT', 'data', body_mat)
    meta = {'tile': SPEC['tile'], 'u_repeat': 2 * math.pi * mid_radius / SPEC['tile'],
            'v_repeat': length / SPEC['tile'], 'height_m': H, 'specular': SPEC['specular']}
    with open(os.path.join(BAKE, f'{PROP}.json'), 'w') as stream:
        json.dump(meta, stream, indent=1)
    print('BAKED', PROP, meta)
    bpy.data.objects.remove(dense)
    bpy.data.objects.remove(ground)
    joined = []
    for level, (solid, parts) in enumerate(lods):
        name = SPEC['base'] if level == 0 else f"{SPEC['base']}_LOD{level}"
        joined.append(pl.join(name, [solid] + parts))
    cl.drop_to_ground(joined)
    for obj in joined:
        cl.clamp_ground(obj)
        print('LEVEL', obj.name, 'tris', pl.triangles(obj))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(cl.WORK, f'{PROP}_geo.blend'))


def export():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(cl.WORK, f'{PROP}_geo.blend'))
    with open(os.path.join(BAKE, f'{PROP}.json')) as stream:
        meta = json.load(stream)
    for m in list(bpy.data.materials):
        m.name = 'old_' + m.name
    material = cl.material('Leather' if PROP == 'bag_a' else 'Burlap', PROP,
                           extras={'openyamm_specular': meta['specular']})
    rope = cl.material('Rope', 'bag_a_rope', extras={'openyamm_specular': 0.4}) if PROP == 'bag_a' else None
    lods = sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: len(o.name))
    for obj in lods:
        for index, slot in enumerate(obj.data.materials):
            if slot.name.startswith('old_Body'):
                obj.data.materials[index] = material
            elif slot.name.startswith('old_Rope'):
                obj.data.materials[index] = rope
        pl.white_colour(obj)
        print('LEVEL', obj.name, 'tris', pl.triangles(obj), [m.name for m in obj.data.materials])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(cl.WORK, f'{PROP}.blend'))
    pl.export(lods, os.path.join(cl.WORK, f'{PROP}_export.glb'))


if STAGE == 'bake':
    bake()
else:
    export()
