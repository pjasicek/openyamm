"""Shared helpers of the torch batch: materials from this folder's textures/, then the project's ../textures (the
shared flame02 flipbook), then the outdoor props textures (read only); flame cards; fluting; per-material COLOR_0
tints matched to measured native sprite colours; a procedural skull (after the outdoor skull pile's, matched to the
`skull` texture layout); export. Blender Z up, base centre on the ground at the origin, units() converts native map
units to metres."""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import dungeon_lib as dl  # noqa: E402

pl = dl.pl
u = dl.units
OWN_TEXTURES = os.path.join(HERE, 'textures')
WORK = os.path.join(HERE, 'work')


def material(name, texture, alpha=False, extras=None):
    """pl.material from this batch's textures/, else the project's ../textures, else the props textures."""
    for folder in (OWN_TEXTURES, dl.TEXTURES):
        if os.path.exists(os.path.join(folder, f'{texture}_basecolor.png')):
            pl.TEX = folder
            try:
                return pl.material(name, texture, alpha=alpha, extras=extras)
            finally:
                pl.TEX = dl.PROPS_TEXTURES
    return pl.material(name, texture, alpha=alpha, extras=extras)


FLAME_COLUMNS, FLAME_ROWS, FLAME_FPS = 16, 4, 30       # ../textures/FLAMES.md: flame02, a 64-frame 2.1 s loop


def flame_material(name='Flame', texture='flame02'):
    """The shared CC0 Unity Labs flame flipbook (../textures/flame02_basecolor.png, FLAMES.md)."""
    return material(name, texture, alpha=True, extras={'openyamm_billboard': True,
                                                       'openyamm_flipbook': [FLAME_COLUMNS, FLAME_ROWS, FLAME_FPS],
                                                       'openyamm_specular': 0.0})


def flame_card(name, mat, width, z0, z1):
    """A flame card in the model's x/up plane centred on the flame axis (x = y = 0) over the lower 80 % of a
    flipbook frame (FLAMES.md: the flame is about 60 % of the card's width, its flat base about 2.5 % above the
    bottom edge and its tips 5-20 % below the top edge)."""
    return card(name, mat, -width / 2, width / 2, z0, z1, v_top=0.8)


def card(name, mat, x0, x1, z0, z1, y=0.0, v_top=1.0):
    """A quad in the x/up plane, texture coordinates 0..1 (v up to v_top) over one flipbook frame (Blender v up)."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    corners = ((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1))
    face = bm.faces.new([bm.verts.new(c) for c in corners])
    for loop, (s, t) in zip(face.loops, ((0, 0), (1, 0), (1, v_top), (0, v_top))):
        loop[uv].uv = (s, t)
    obj = pl.to_object(name, bm, mat, smooth=False)
    return obj


def strip(name, mat, a, b, width, turn=0.0, repeat=1.0):
    """A cut-out ribbon from point a to point b (a chain), facing turn radians about its own axis; v runs along it
    (repeat texture repeats), u across."""
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    side = axis.cross(Vector((0, 0, 1)))
    if side.length < 1e-4:
        side = Vector((1, 0, 0))
    side.normalize()
    side = side * math.cos(turn) + axis.cross(side) * math.sin(turn)
    half = side * width / 2
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    face = bm.faces.new([bm.verts.new(c) for c in (a - half, a + half, b + half, b - half)])
    for loop, st in zip(face.loops, ((0, 0), (1, 0), (1, repeat), (0, repeat))):
        loop[uv].uv = st
    return pl.to_object(name, bm, mat, smooth=False)


def apply_all(obj):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def flute(obj, count, amount, z0, z1):
    """Radial ribs: scales the xy radius of vertices between z0 and z1 by 1 + amount cos(count angle)."""
    for v in obj.data.vertices:
        if z0 - 1e-6 <= v.co.z <= z1 + 1e-6:
            a = math.atan2(v.co.y, v.co.x)
            k = 1 + amount * math.cos(count * a)
            v.co.x *= k; v.co.y *= k


def srgb_to_linear(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


_means = {}


def texture_mean(mat):
    """Linear mean base colour of a material's base-colour image."""
    if mat.name not in _means:
        image = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE').image
        pixels = np.array(image.pixels[:], np.float32).reshape(-1, 4)
        if not image.is_float:                                  # byte images: sRGB-encoded values
            rgb = pixels[:, :3]
            pixels[:, :3] = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
        weights = pixels[:, 3:4] if pixels[:, 3].min() < 0.99 else np.ones((len(pixels), 1), np.float32)
        _means[mat.name] = (pixels[:, :3] * weights).sum(0) / max(weights.sum(), 1e-6)
    return _means[mat.name]


def tint(obj, targets, shade=None):
    """COLOR_0 *= linear(native sRGB target) / (linear texture mean x the material's mean occlusion), so a
    material's displayed mean matches the native sprite's measured mean colour. shade(name, co) -> extra factor
    or (r, g, b) factors (painted light gradients); materials not in targets keep their colours."""
    me = obj.data
    attr = me.color_attributes['Color']
    owner = {}
    for polygon in me.polygons:
        for index in polygon.vertices:
            owner[index] = me.materials[polygon.material_index]
    occlusion = {}
    for index, mat in owner.items():
        occlusion.setdefault(mat.name, []).append(attr.data[index].color[0])
    factors = {}
    for mat in set(owner.values()):
        if mat.name in targets:
            factors[mat.name] = srgb_to_linear(targets[mat.name]) / (
                np.maximum(texture_mean(mat), 1e-4) * max(np.mean(occlusion[mat.name]), 0.05))
    for index, mat in owner.items():
        factor = factors.get(mat.name)
        if factor is None:
            continue
        extra = shade(mat.name, me.vertices[index].co) if shade else 1.0
        if not isinstance(extra, tuple):
            extra = (extra, extra, extra)
        c = attr.data[index].color
        attr.data[index].color = (c[0] * factor[0] * extra[0], c[1] * factor[1] * extra[1],
                                  c[2] * factor[2] * extra[2], c[3])
    return {name: tuple(round(float(x), 3) for x in f) for name, f in factors.items()}


# ---------------------------------------------------------------- skull (texture layout of the props `skull`)
U_NODES = ([0, 0.14, 0.27, 0.33, 0.375, 0.418, 0.46, 0.5, 0.54, 0.582, 0.625, 0.67, 0.73, 0.86, 1.0],
           [0, 0.2, 0.33, 0.418, 0.5, 0.582, 0.67, 0.8, 1.0],
           [0, 0.25, 0.418, 0.5, 0.582, 0.75, 1.0])
V_NODES = ([0, 0.12, 0.235, 0.29, 0.345, 0.43, 0.505, 0.585, 0.665, 0.75, 0.87, 1.0],
           [0, 0.2, 0.33, 0.43, 0.585, 0.72, 1.0],
           [0, 0.35, 0.585, 0.8, 1.0])
FEATURES = [(0.418, 0.585, 0.065, 0.10, -0.15), (0.582, 0.585, 0.065, 0.10, -0.15),
            (0.5, 0.43, 0.05, 0.10, -0.10), (0.5, 0.675, 0.17, 0.05, 0.035),
            (0.375, 0.45, 0.05, 0.07, 0.045), (0.625, 0.45, 0.05, 0.07, 0.045),
            (0.5, 0.29, 0.09, 0.05, 0.02),
            (0.33, 0.6, 0.05, 0.09, -0.035), (0.67, 0.6, 0.05, 0.09, -0.035),
            (0.4, 0.33, 0.04, 0.05, -0.03), (0.6, 0.33, 0.04, 0.05, -0.03)]


def skull(name, mat, level):
    """Unit skull (front +y, up +z; about 0.72 wide, 0.96 long, 0.95 tall) with u around and v bottom to top."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    grid = []
    for v in V_NODES[level]:
        phi = math.pi * (1 - v)
        row = []
        for uu in U_NODES[level]:
            theta = 2 * math.pi * uu
            d = Vector((math.sin(phi) * math.sin(theta), -math.sin(phi) * math.cos(theta), math.cos(phi)))
            p = Vector((d.x * 0.36, d.y * 0.48, d.z * 0.40))
            front = max(d.y, 0.0)
            if p.z < 0:
                p.z *= 1 + 0.45 * front
                p.x *= 1 - 0.3 * front * min(-d.z / 0.6, 1.0)
            for cu, cv, ru, rv, offset in FEATURES:
                w = 1 - ((uu - cu) / ru) ** 2 - ((v - cv) / rv) ** 2
                if w > 0:
                    p += d * offset * w ** 0.7
            row.append((bm.verts.new(p), uu, v))
        grid.append(row)
    for lower, upper in zip(grid, grid[1:]):
        for j in range(len(lower) - 1):
            quad = (lower[j], lower[j + 1], upper[j + 1], upper[j])
            f = bm.faces.new([q[0] for q in quad])
            for loop, (_, uu, v) in zip(f.loops, quad):
                loop[uv].uv = (uu, v)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, True)


def export(prop, lods):
    os.makedirs(WORK, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{prop}.blend'))
    pl.export(lods, os.path.join(WORK, f'{prop}_export.glb'))
