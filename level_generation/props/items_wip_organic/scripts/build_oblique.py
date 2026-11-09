"""Oblique icons: items whose icon is painted as an oblique view of the item lying on the ground (a folded cloak, a belt
coiled into a loop) -> work/<family>/<icon>_export.glb, a solid whose view from the icon's angle is the icon.

The icon is projected onto the solid along its view: a ground point (x, y) at height z (x2 icon pixels; y away from the
viewer) lands on icon row bottom - (y sin e + z cos e) for the view elevation e, so from that angle the model shows the
painting exactly, and from the player's similar low view nearly so.
- pile (cloaks, books, helms, boots, gold, rings): per icon column, a cushion of the family's depth (a fraction of the icon's width) whose rounded
  cross-section (superellipse) is as high as the column's painted extent needs at elevation e; where a column is too
  short for that depth (the pile's ends, flat MM6 capes) the depth shrinks and the height goes to nothing.
- lathe (bottles): standing, per icon row a ring as wide as the painted row, the painting wrapped round it.
- loop (belts): a band standing on edge round an ellipse as wide as the icon, depth 'depth' x its width; the band is
  'band' x the icon's height and the elevation is solved so the loop fills the icon. Hidden walls (the back of the
  outer face, the front of the inner face) take the visible wall's mapping mirrored front to back.
Model contract as build_icon_relief.py: icon width along X, lowest point at 0, origin at the centre of the footprint,
1 Blender unit = 100 x2 icon pixels.
Usage: blender --background --python build_oblique.py -- <family> [icon ...]"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'projectiles_claude',
                                'scripts'))
import projlib as pl  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = os.path.join(HERE, '..', '..', '..', 'assets_dev', 'engine', 'icons_x2')
PX = 0.01
TEMPLATES = {
    'cloaks': {'shape': 'pile', 'elevation': 20.0, 'depth': 0.75, 'power': 4.0, 'step': 4, 'segments': 14,
               'roughness': 0.85},
    'belts': {'shape': 'loop', 'depth': 0.85, 'band': 0.55, 'wall': 3.0, 'segments': 64, 'roughness': 0.6},
    'rings': {'shape': 'pile', 'elevation': 30.0, 'depth': 0.7, 'power': 2.5, 'step': 2, 'segments': 14,
              'roughness': 0.25},
    'books': {'shape': 'pile', 'elevation': 30.0, 'depth': 0.7, 'power': 10.0, 'step': 3, 'segments': 14,
              'roughness': 0.6},
    'helms': {'shape': 'pile', 'elevation': 15.0, 'depth': 0.8, 'power': 2.5, 'step': 3, 'segments': 16,
              'roughness': 0.4},
    'boots': {'shape': 'pile', 'elevation': 10.0, 'depth': 0.45, 'power': 3.0, 'step': 3, 'segments': 14,
              'roughness': 0.55},
    'gold': {'shape': 'pile', 'elevation': 30.0, 'depth': 0.8, 'power': 1.6, 'step': 3, 'segments': 14,
             'roughness': 0.3},
    # Standing bottles, turned from the icon's outline.
    'bottles': {'shape': 'lathe', 'step': 3, 'segments': 24, 'roughness': 0.15},
}


def alpha_of(icon):
    image = bpy.data.images.load(os.path.join(ICONS, icon + '.png'), check_existing=True)
    width, height = image.size
    return np.array(image.pixels[:], np.float32).reshape(height, width, 4)[::-1][:, :, 3]


def smooth(values, radius):
    padded = np.pad(values, radius, mode='edge')
    kernel = np.ones(2 * radius + 1) / (2 * radius + 1)
    return np.convolve(padded, kernel, mode='valid')


def pile(icon, entry, template):
    """Vertices and faces (lists) plus a UV function for a cushion pile."""
    alpha = alpha_of(icon) >= 0.5
    columns = np.flatnonzero(alpha.any(axis=0))
    first, last = int(columns[0]), int(columns[-1])
    xs = np.arange(first, last + 1, template['step'], dtype=np.float64)
    if xs[-1] != last:
        xs = np.append(xs, last)
    tops = np.array([np.flatnonzero(alpha[:, int(x)]).min() if alpha[:, int(x)].any() else 0 for x in xs], float)
    bottoms = np.array([np.flatnonzero(alpha[:, int(x)]).max() + 1 if alpha[:, int(x)].any() else 0 for x in xs],
                       float)
    # Only the bottom edge's broad slope (an item drawn turned) sets the footprint's front: at a low elevation each
    # pixel of a detailed edge (cheek guards, soles) would push the column far back. The column spans from its
    # painted top to that smoothed edge.
    tops = smooth(tops, 1)
    bottoms = np.maximum(smooth(bottoms, max(3, len(xs) // 6)), smooth(bottoms, 1))
    elevation = math.radians(template['elevation'])
    sin_e, cos_e = math.sin(elevation), math.cos(elevation)
    power, segments = template['power'], template['segments']
    s_values = np.linspace(-1.0, 1.0, segments + 1)
    shape = (1.0 - np.abs(s_values) ** power) ** (1.0 / power)
    half_depth = template['depth'] * (last - first) / 2.0
    reference = bottoms.max()

    def extent(a, c):
        projected = (s_values + 1.0) * a * sin_e + c * shape * cos_e
        return projected.max()
    profiles = []
    for top, bottom in zip(tops, bottoms):
        span = max(bottom - top, 1.0)
        a = min(half_depth, span / (2.0 * sin_e) * 0.98)
        low, high = 0.0, span / cos_e * 2.0
        for _ in range(40):
            c = (low + high) / 2.0
            if extent(a, c) > span:
                high = c
            else:
                low = c
        front = min((reference - bottom) / sin_e, 0.5 * half_depth)
        profiles.append((front, a, low))
    # Ends taper to a point so the pile closes.
    vertices, faces, kinds, middles = [], [], [], []
    top_index, bottom_index = [], []
    for column, (x, (front, a, c)) in enumerate(zip(xs, profiles)):
        ends = column in (0, len(xs) - 1)
        row_top, row_bottom = [], []
        for k, s in enumerate(s_values):
            y = front + (s + 1.0) * a
            z = 0.0 if ends else c * shape[k]
            vertices.append((x, y, z))
            middles.append(front + a)
            row_top.append(len(vertices) - 1)
        for k in range(1, segments):
            if ends:
                row_bottom.append(row_top[k])
            else:
                vertices.append((x, front + (s_values[k] + 1.0) * a, 0.0))
                middles.append(front + a)
                row_bottom.append(len(vertices) - 1)
        top_index.append(row_top)
        bottom_index.append([row_top[0]] + row_bottom + [row_top[-1]])
    tan_e = sin_e / cos_e
    for column in range(len(xs) - 1):
        for k in range(segments):
            quad = [top_index[column][k], top_index[column][k + 1], top_index[column + 1][k + 1],
                    top_index[column + 1][k]]
            faces.append(quad)
            # Turned away from the painting's view (the pile's back): it takes the front's painting, mirrored.
            rise = sum(vertices[quad[i]][2] - vertices[quad[i - 1]][2] for i in (1, 2)) / 2.0
            run = sum(vertices[quad[i]][1] - vertices[quad[i - 1]][1] for i in (1, 2)) / 2.0
            kinds.append('back' if run > 1e-6 and rise / run < -tan_e else 'top')
            faces.append([bottom_index[column][k], bottom_index[column + 1][k], bottom_index[column + 1][k + 1],
                          bottom_index[column][k + 1]])
            kinds.append('bottom')

    def uv(index, face_centre, kind):
        x, y, z = vertices[index]
        if kind == 'back':
            y = 2.0 * middles[index] - y
        return x, reference - (y * sin_e + z * cos_e)
    return vertices, faces, uv, kinds


def loop(icon, entry, template):
    box = entry['opaque_box']
    width, height = box[2] - box[0], box[3] - box[1]
    radius_x = width / 2.0
    radius_y = template['depth'] * radius_x
    band = template['band'] * height
    low, high = math.radians(2.0), math.radians(70.0)
    for _ in range(50):
        elevation = (low + high) / 2.0
        if 2.0 * radius_y * math.sin(elevation) + band * math.cos(elevation) > height:
            high = elevation
        else:
            low = elevation
    sin_e, cos_e = math.sin(low), math.cos(low)
    centre_x = (box[0] + box[2]) / 2.0
    wall, segments = template['wall'], template['segments']
    vertices, faces, kinds = [], [], []
    rings = []
    for inset, z in ((0.0, 0.0), (0.0, band), (wall, band), (wall, 0.0)):
        ring = []
        for k in range(segments):
            angle = 2.0 * math.pi * k / segments
            vertices.append((centre_x + (radius_x - inset) * math.cos(angle),
                             (radius_y - inset) * math.sin(angle), z))
            ring.append(len(vertices) - 1)
        rings.append(ring)
    outer_bottom, outer_top, inner_top, inner_bottom = rings
    for k in range(segments):
        n = (k + 1) % segments
        faces.append([outer_bottom[k], outer_bottom[n], outer_top[n], outer_top[k]])
        kinds.append('outer')
        faces.append([outer_top[k], outer_top[n], inner_top[n], inner_top[k]])
        kinds.append('rim')
        faces.append([inner_top[k], inner_top[n], inner_bottom[n], inner_bottom[k]])
        kinds.append('inner')
        faces.append([inner_bottom[k], inner_bottom[n], outer_bottom[n], outer_bottom[k]])
        kinds.append('rim')
    bottom = box[3]

    def uv(index, face_centre, kind):
        x, y, z = vertices[index]
        # The outer wall's back and the inner wall's front are hidden in the painting: mirror the visible side.
        if (kind == 'outer' and face_centre[1] > 0.0) or (kind == 'inner' and face_centre[1] < 0.0):
            y = -y
        return x, bottom - ((y + radius_y) * sin_e + z * cos_e)
    return vertices, faces, uv, kinds


def lathe(icon, entry, template):
    """A solid of revolution standing on its base: per icon row, a ring as wide as the painted row about the icon's
    middle; the painting wraps round it (front and back alike)."""
    alpha = alpha_of(icon) >= 0.5
    rows = np.flatnonzero(alpha.any(axis=1))
    first, last = int(rows[0]), int(rows[-1])
    lefts = np.array([np.flatnonzero(alpha[r]).min() if alpha[r].any() else 0 for r in range(first, last + 1)], float)
    rights = np.array([np.flatnonzero(alpha[r]).max() + 1 if alpha[r].any() else 0 for r in range(first, last + 1)],
                      float)
    centre = float(np.median((lefts + rights) / 2.0))
    radii = smooth((rights - lefts) / 2.0, 1)
    step, segments = template['step'], template['segments']
    sample_rows = list(range(0, last - first + 1, step))
    if sample_rows[-1] != last - first:
        sample_rows.append(last - first)
    vertices, faces, kinds, angles = [], [], [], []
    rings = []
    for r in sample_rows:
        ring = []
        z = float(last + 1 - (first + r))
        for k in range(segments):
            angle = 2.0 * math.pi * k / segments
            vertices.append((centre + radii[r] * math.sin(angle), -radii[r] * math.cos(angle), z))
            angles.append(angle)
            ring.append(len(vertices) - 1)
        rings.append((ring, first + r))
    # Bottom (last row) and top (first row) caps.
    for ring, row in (rings[0], rings[-1]):
        vertices.append((centre, 0.0, float(last + 1 - row)))
        angles.append(0.0)
        rings_centre = len(vertices) - 1
        for k in range(segments):
            faces.append([ring[k], ring[(k + 1) % segments], rings_centre])
            kinds.append(row)
    for (upper, row), (lower, _) in zip(rings[:-1], rings[1:]):
        for k in range(segments):
            n = (k + 1) % segments
            faces.append([upper[k], upper[n], lower[n], lower[k]])
            kinds.append(None)

    def uv(index, face_centre, kind):
        x, y, z = vertices[index]
        if kind is not None:
            return centre, float(kind)
        return x, float(last + 1) - z
    return vertices, faces, uv, kinds


def build(icon, entry, template):
    canvas_w, canvas_h = entry['canvas']
    vertices, faces, uv_of, kinds = {'pile': pile, 'loop': loop, 'lathe': lathe}[template['shape']](
        icon, entry, template)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    verts = [bm.verts.new((x * PX, -y * PX, z * PX)) for x, y, z in vertices]
    for face, kind in zip(faces, kinds):
        unique = list(dict.fromkeys(face))
        if len(unique) < 3:
            continue
        try:
            created = bm.faces.new([verts[i] for i in unique])
        except ValueError:
            continue
        centre = np.mean([vertices[i] for i in unique], axis=0)
        for loop_, i in zip(created.loops, unique):
            u, v = uv_of(i, centre, kind)
            loop_[uv_layer].uv = ((u + 0.5) / canvas_w, 1.0 - (v + 0.5) / canvas_h)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    xs, ys, zs = ([v.co[i] for v in bm.verts] for i in range(3))
    shift = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs))
    for v in bm.verts:
        v.co.x -= shift[0]
        v.co.y -= shift[1]
        v.co.z -= shift[2]
    return bm


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
        bm = build(icon, entry, template)
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
