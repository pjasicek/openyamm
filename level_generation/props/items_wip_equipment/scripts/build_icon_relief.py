"""Icon relief: every icon of a family's manifest -> work/<family>/<icon>.glb, an item model lying flat.

The icon's outline is traced from its alpha (marching squares at 0.5 with linear interpolation, chained into loops,
outer outlines and holes alike), simplified (Ramer-Douglas-Peucker, SIMPLIFY px), and triangulated with interior points
on a SPACING px grid (Blender's constrained Delaunay; triangles whose centre lies outside the icon are dropped). Each
vertex rises by its distance d to the outline (x2 px): z = ROUND * (1 - exp(-d / ROUND)) + SLOPE * d, so edges are
bevelled at about 45 degrees, narrow parts (grips, guards, pommels) come out nearly round and wide ones (blades) as a
low ridge. Front and back mirror each other and meet at the outline, so the piece is closed. UVs map straight onto the
icon (textures/<icon>.png, make_icon_textures.py), which is the base colour: the painted light stays.
Model contract (GROUND_ITEMS_3D_PLAN.md): lying flat, icon up along +Y, thickness along Z with the underside at 0,
origin at the centre of the footprint; 1 Blender unit = 100 x2 icon pixels (the binding's length sets the world size).
Propped (template 'prop': pitch, roll in degrees, optionally which end is raised): the piece is baked resting with one
end raised (by default the end whose outer third is wider: a sword's guard) and turned a little about its length, then dropped onto 0, so it stands out of grass
and reads as an object rather than a decal; the engine only adds a yaw and the ground's slope.
Usage: blender --background --python build_icon_relief.py -- <family> [icon ...]"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'projectiles_claude',
                                'scripts'))
import projlib as pl  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PX = 0.01
# family: template (thickness profile in x2 px, outline simplification, interior spacing, roughness)
TEMPLATES = {
    'swords': {'round': 3.5, 'slope': 0.1, 'simplify': 1.0, 'spacing': 10.0, 'roughness': 0.45, 'prop': (9.0, 7.0)},
    'daggers': {'round': 3.5, 'slope': 0.1, 'simplify': 1.0, 'spacing': 8.0, 'roughness': 0.45, 'prop': (9.0, 7.0)},
    # Long hafts rest on their head with the butt raised; heavy heads (axes, maces) lie on the ground.
    'spears': {'round': 3.5, 'slope': 0.12, 'simplify': 1.0, 'spacing': 10.0, 'roughness': 0.55,
               'prop': (6.0, 6.0, 'narrow')},
    'axes': {'round': 3.5, 'slope': 0.06, 'simplify': 1.0, 'spacing': 10.0, 'roughness': 0.5,
             'prop': (8.0, 6.0, 'narrow')},
    'maces': {'round': 4.0, 'slope': 0.35, 'simplify': 1.0, 'spacing': 10.0, 'roughness': 0.55,
              'prop': (8.0, 6.0, 'narrow')},
    'staves': {'round': 4.0, 'slope': 0.2, 'simplify': 1.0, 'spacing': 10.0, 'roughness': 0.6,
               'prop': (6.0, 6.0, 'narrow')},
    'bows': {'round': 3.0, 'slope': 0.1, 'simplify': 0.8, 'spacing': 10.0, 'roughness': 0.55, 'prop': (3.0, 5.0)},
    'blasters': {'round': 4.0, 'slope': 0.2, 'simplify': 1.0, 'spacing': 8.0, 'roughness': 0.35, 'prop': (4.0, 6.0)},
    'wands': {'round': 3.5, 'slope': 0.2, 'simplify': 1.0, 'spacing': 8.0, 'roughness': 0.5, 'prop': (8.0, 6.0)},
    # Plates lie face up.
    'shields': {'round': 2.5, 'slope': 0.02, 'simplify': 1.0, 'spacing': 10.0, 'roughness': 0.5, 'dome': 0.18,
                'prop': (0.0, 4.0)},
    'armour': {'round': 2.5, 'slope': 0.02, 'simplify': 1.0, 'spacing': 10.0, 'roughness': 0.6, 'dome': 0.22,
               'prop': (0.0, 3.0)},
    # Rolled scrolls come out round (a rolling bevel as deep as the roll), sheets as a thin stack.
    'scrolls': {'round': 9.0, 'slope': 0.0, 'simplify': 1.0, 'spacing': 8.0, 'roughness': 0.75, 'prop': (0.0, 4.0)},
    'amulets': {'round': 2.5, 'slope': 0.05, 'simplify': 0.8, 'spacing': 8.0, 'roughness': 0.4, 'dome': 0.08},
    'gauntlets': {'round': 3.0, 'slope': 0.15, 'simplify': 1.0, 'spacing': 8.0, 'roughness': 0.5, 'dome': 0.2,
                  'prop': (0.0, 5.0)},
    'gems': {'round': 3.0, 'slope': 0.3, 'simplify': 1.0, 'spacing': 6.0, 'roughness': 0.15, 'dome': 0.3},
    'lumps': {'round': 3.0, 'slope': 0.25, 'simplify': 1.0, 'spacing': 6.0, 'roughness': 0.6, 'dome': 0.25},
    'misc': {'round': 3.0, 'slope': 0.12, 'simplify': 1.0, 'spacing': 8.0, 'roughness': 0.55, 'dome': 0.1},
}


def alpha_of(path):
    image = bpy.data.images.load(path, check_existing=True)
    width, height = image.size
    pixels = np.array(image.pixels[:], np.float32).reshape(height, width, 4)[::-1]
    return pixels[:, :, 3]


def marching_squares(alpha, level=0.5):
    """Closed outline loops of alpha >= level, in pixel-centre coordinates (x right, y down)."""
    a = np.pad(alpha, 1)
    height, width = a.shape
    segments = []

    def point(y0, x0, y1, x1):
        v0, v1 = a[y0, x0], a[y1, x1]
        t = (level - v0) / (v1 - v0) if v1 != v0 else 0.5
        return (round(x0 + (x1 - x0) * t - 1, 4), round(y0 + (y1 - y0) * t - 1, 4))

    inside = a >= level
    for y in range(height - 1):
        for x in range(width - 1):
            code = (inside[y, x] << 3) | (inside[y, x + 1] << 2) | (inside[y + 1, x + 1] << 1) | inside[y + 1, x]
            if code in (0, 15):
                continue
            top = point(y, x, y, x + 1)
            right = point(y, x + 1, y + 1, x + 1)
            bottom = point(y + 1, x, y + 1, x + 1)
            left = point(y, x, y + 1, x)
            table = {1: [(left, bottom)], 2: [(bottom, right)], 3: [(left, right)], 4: [(top, right)],
                     5: [(left, top), (bottom, right)], 6: [(top, bottom)], 7: [(left, top)], 8: [(top, left)],
                     9: [(top, bottom)], 10: [(top, right), (bottom, left)], 11: [(top, right)], 12: [(left, right)],
                     13: [(bottom, right)], 14: [(left, bottom)]}
            segments.extend(table[code])
    # Chain segments into loops through shared end points.
    following = {}
    for start, end in segments:
        following.setdefault(start, []).append(end)
        following.setdefault(end, []).append(start)
    loops, used = [], set()
    for start, end in segments:
        if (start, end) in used or (end, start) in used:
            continue
        loop = [start, end]
        used.add((start, end))
        while True:
            options = [p for p in following[loop[-1]] if (loop[-1], p) not in used and (p, loop[-1]) not in used]
            if not options:
                break
            used.add((loop[-1], options[0]))
            if options[0] == loop[0]:
                break
            loop.append(options[0])
        if len(loop) >= 8:
            loops.append(np.array(loop, np.float64))
    return loops


def simplify(points, epsilon):
    """Ramer-Douglas-Peucker on a closed loop (split at the two farthest points)."""
    def rdp(segment):
        if len(segment) < 3:
            return segment
        a, b = segment[0], segment[-1]
        direction = b - a
        length = np.hypot(*direction)
        if length < 1e-9:
            distances = np.hypot(*(segment - a).T)
        else:
            distances = np.abs(np.cross(direction, segment - a)) / length
        index = int(np.argmax(distances))
        if distances[index] <= epsilon:
            return np.array([a, b])
        return np.vstack([rdp(segment[:index + 1])[:-1], rdp(segment[index:])])
    far = int(np.argmax(np.hypot(*(points - points[0]).T)))
    first = rdp(np.vstack([points[:far + 1]]))
    second = rdp(np.vstack([points[far:], points[:1]]))
    return np.vstack([first[:-1], second[:-1]])


def sample(alpha, x, y):
    h, w = alpha.shape
    xi, yi = int(round(x)), int(round(y))
    return alpha[min(max(yi, 0), h - 1), min(max(xi, 0), w - 1)]


def relief(icon, entry, template):
    alpha = alpha_of(os.path.join(HERE, 'textures', '..', '..', '..', '..', 'assets_dev', 'engine', 'icons_x2',
                                  icon + '.png'))
    dense = marching_squares(alpha)
    outline = np.vstack(dense)
    loops = [simplify(loop, template['simplify']) for loop in dense]
    vertices, edges = [], []
    for loop in loops:
        base = len(vertices)
        vertices.extend(tuple(p) for p in loop)
        edges.extend((base + i, base + (i + 1) % len(loop)) for i in range(len(loop)))
    boundary_count = len(vertices)
    spacing = template['spacing']
    height, width = alpha.shape
    for y in np.arange(spacing / 2, height, spacing):
        for x in np.arange(spacing / 2, width, spacing):
            if sample(alpha, x, y) >= 0.5:
                if np.min(np.hypot(outline[:, 0] - x, outline[:, 1] - y)) > spacing * 0.45:
                    vertices.append((x, y))
    result = delaunay_2d_cdt([Vector(v) for v in vertices], edges, [], 0, 1e-4)
    out_vertices, _, out_faces, original = result[0], result[1], result[2], result[3]
    on_outline = [any(o < boundary_count for o in ids) for ids in original]
    faces = []
    for face in out_faces:
        if len(face) != 3:
            continue
        centre = sum((out_vertices[i] for i in face), Vector((0, 0))) / 3
        if sample(alpha, centre.x, centre.y) >= 0.5:
            faces.append(face)
    rounding, slope = template['round'], template['slope']
    distances = [0.0 if on_outline[i] else float(np.min(np.hypot(outline[:, 0] - v.x, outline[:, 1] - v.y)))
                 for i, v in enumerate(out_vertices)]
    heights = [rounding * (1.0 - math.exp(-d / rounding)) + slope * d for d in distances]
    # The mid-surface: flat for weapons; a shell (template 'dome': rise over the deepest distance) curves front and
    # back alike, so a shield or cuirass is a plate with a concave back resting on its rim.
    middle = [0.0] * len(out_vertices)
    if 'dome' in template:
        deepest = max(distances)
        rise = template['dome'] * deepest
        middle = [rise * (1.0 - (1.0 - min(d / deepest, 1.0)) ** 2) for d in distances]
    box = entry['opaque_box']
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    canvas_w, canvas_h = entry['canvas']
    lift = max(heights)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    front, back = {}, {}
    for i, v in enumerate(out_vertices):
        x, y = (v.x - cx) * PX, -(v.y - cy) * PX
        front[i] = bm.verts.new((x, y, (lift + middle[i] + heights[i]) * PX))
        back[i] = front[i] if on_outline[i] else bm.verts.new((x, y, (lift + middle[i] - heights[i]) * PX))

    def uv(i):
        v = out_vertices[i]
        return ((v.x + 0.5) / canvas_w, 1.0 - (v.y + 0.5) / canvas_h)

    for face in faces:
        a, b, c = face
        # The image's y runs down: the 2D winding is mirrored, so the front takes the reversed order.
        for verts, order in ((front, (a, c, b)), (back, (a, b, c))):
            try:
                created = bm.faces.new([verts[i] for i in order])
            except ValueError:
                continue
            for loop, i in zip(created.loops, order):
                loop[uv_layer].uv = uv(i)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    prop(bm, *template.get('prop', (0.0, 0.0)))
    return bm


def prop(bm, pitch, roll, raised='wide'):
    """Rest the piece on one end with the other raised by pitch and turned by roll about its length, lowest point
    at 0, footprint centred on the origin. raised: 'wide' lifts the end whose outer third is wider (a sword's guard),
    'narrow' the other one (an axe's or mace's handle, its heavy head on the ground)."""
    ys = [v.co.y for v in bm.verts]
    low, high = min(ys), max(ys)
    third = (high - low) / 3

    def width(selected):
        xs = [v.co.x for v in selected]
        return max(xs) - min(xs)
    hilt_up = width([v for v in bm.verts if v.co.y > high - third]) >= width([v for v in bm.verts
                                                                             if v.co.y < low + third])
    if raised == 'narrow':
        hilt_up = not hilt_up
    p = math.radians(pitch if hilt_up else -pitch)
    r = math.radians(roll)
    for v in bm.verts:
        x, y, z = v.co
        y, z = y * math.cos(p) - z * math.sin(p), y * math.sin(p) + z * math.cos(p)
        x, z = x * math.cos(r) + z * math.sin(r), -x * math.sin(r) + z * math.cos(r)
        v.co = (x, y, z)
    xs, ys, zs = ([v.co[i] for v in bm.verts] for i in range(3))
    shift = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    for v in bm.verts:
        v.co -= shift


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    family, only = args[0], set(args[1:])
    template = TEMPLATES[family]
    manifest = json.load(open(os.path.join(HERE, 'work', f'{family}_manifest.json')))
    pl.TEXTURES = os.path.join(HERE, 'textures')
    out_dir = os.path.join(HERE, 'work', family)
    os.makedirs(out_dir, exist_ok=True)
    pl.WORK = out_dir
    for icon, entry in manifest.items():
        if only and icon not in only:
            continue
        pl.reset()
        bm = relief(icon, entry, template)
        m = bpy.data.materials.new(icon)
        m.use_nodes = True
        bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        tex = m.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(os.path.join(HERE, 'textures', icon + '.png'), check_existing=True)
        m.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = template['roughness']
        obj = pl.to_object(icon, bm, [m], 55)
        pl.export(obj, icon)


main()
