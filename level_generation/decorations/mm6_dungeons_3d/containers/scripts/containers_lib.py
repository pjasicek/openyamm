"""Shared Blender helpers for the containers batch: materials from containers/textures/ first (then the project's and
the outdoor props' textures through dungeon_lib), soft bodies of revolution with per-vertex displacement (sacks,
caps), tubes swept along paths (rope, curved stems, rings), COLOR_0 = vertex occlusion x a per-material tint derived
from the native sprite's measured colour, and the LOD/export step. Blender Z up, base centre on the ground."""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import dungeon_lib as dl  # noqa: E402

pl = dl.pl
u = dl.units
TEXTURES = os.path.join(HERE, 'textures')
WORK = os.path.join(HERE, 'work')


# Matte fibre and wood materials (and the crystal, whose sky reflection would wash out its dark violet): dark
# painted albedo is of the order of a dielectric's 4 % reflectance, so full specular would grey them; the engine
# scales their sun/point/sky specular by openyamm_specular.
MATTE = {'burlap': 0.2, 'suede': 0.35, 'rope': 0.4, 'straw': 0.25, 'rag': 0.25, 'staves': 0.4, 'endgrain': 0.4,
         'crystal': 0.5}


def material(name, texture, extras=None):
    extras = dict(extras or {})
    if texture in MATTE:
        extras.setdefault('openyamm_specular', MATTE[texture])
    if os.path.exists(os.path.join(TEXTURES, f'{texture}_basecolor.png')):
        saved = pl.TEX
        pl.TEX = TEXTURES
        try:
            m = pl.material(name, texture, extras=extras)
        finally:
            pl.TEX = saved
    else:
        m = dl.material(name, texture, extras=extras)
    return m


# ---------------------------------------------------------------- colour
def linear(srgb_value):
    c = np.asarray(srgb_value, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def texture_linear_mean(m):
    """Mean linear colour of a material's base colour image (Blender keeps byte images sRGB-encoded in pixels)."""
    image = next(n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE')
    pixels = np.empty(len(image.pixels), np.float32)
    image.pixels.foreach_get(pixels)
    rgb = pixels.reshape(-1, 4)[:, :3].astype(np.float64)
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return lin.mean(0)


def tint_for(m, target_srgb, gain=1.0):
    """Linear COLOR_0 multiplier bringing the texture's mean to the native region's mean (sRGB)."""
    t = linear(target_srgb) / texture_linear_mean(m) * gain
    return tuple(float(v) for v in np.clip(t, 0.0, 1.0))


def colourise(obj, tints, shade=None):
    """COLOR_0 (already holding occlusion) x tints[material name]; shade(name, co) -> extra factor per vertex."""
    me = obj.data
    names = [m.name for m in me.materials]
    attr = me.color_attributes['Color']
    owner = {}
    for polygon in me.polygons:
        for index in polygon.vertices:
            owner[index] = names[polygon.material_index]
    for index, name in owner.items():
        factor = tints.get(name, (1.0, 1.0, 1.0))
        extra = shade(name, me.vertices[index].co) if shade else 1.0
        c = attr.data[index].color
        attr.data[index].color = (c[0] * factor[0] * extra, c[1] * factor[1] * extra, c[2] * factor[2] * extra,
                                  c[3])


# ---------------------------------------------------------------- geometry
def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def soft_body(name, rings, segments, point, mat, u_repeat=1.0, v_scale=1.0, smooth=True, recalc=True):
    """A closed or open body of revolution on a (rings + 1) x segments grid: point(t, theta) -> Vector, t in [0, 1]
    from the bottom pole/ring to the top. A ring whose points all coincide (a pole) is merged into one vertex.
    u runs around (u_repeat times), v along the profile (v_scale per metre of the mean profile length).
    Faces face theta x (the profile's direction): outward for a profile climbing the outside. recalc=False keeps that
    winding (open surfaces, where recalculation may guess wrong)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    grid = []
    for i in range(rings + 1):
        t = i / rings
        pts = [point(t, 2 * math.pi * s / segments) for s in range(segments)]
        spread = max((p - pts[0]).length for p in pts)
        if spread < 1e-6:
            v = bm.verts.new(pts[0])
            grid.append([v] * segments)
        else:
            grid.append([bm.verts.new(p) for p in pts])
    lengths = [0.0]
    for i in range(rings):
        step = sum((grid[i + 1][s].co - grid[i][s].co).length for s in range(segments)) / segments
        lengths.append(lengths[-1] + step)
    for i in range(rings):
        for s in range(segments):
            s2 = (s + 1) % segments
            quad = [grid[i][s], grid[i][s2], grid[i + 1][s2], grid[i + 1][s]]
            coords = [(s, i), (s + 1, i), (s + 1, i + 1), (s, i + 1)]
            keep = []
            for vert, coord in zip(quad, coords):
                if not any(vert is k[0] for k in keep):
                    keep.append((vert, coord))
            if len(keep) < 3:
                continue
            face = bm.faces.new([k[0] for k in keep])
            for loop, (_, (a, b)) in zip(face.loops, keep):
                loop[uv].uv = (a / segments * u_repeat, lengths[b] * v_scale)
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, smooth)


def sweep(name, path, radius, sides, mat, u_repeat=1.0, v_scale=1.0, caps=True, closed=False):
    """Tube along a polyline (parallel-transported frames); radius: number or callable(t) over 0..1."""
    path = [Vector(p) for p in path]
    count = len(path)
    tangents = []
    for i in range(count):
        if closed:
            d = path[(i + 1) % count] - path[(i - 1) % count]
        else:
            d = path[min(i + 1, count - 1)] - path[max(i - 1, 0)]
        tangents.append(d.normalized())
    normal = tangents[0].orthogonal().normalized()
    frames = []
    for i in range(count):
        if i:
            normal = (normal - tangents[i] * normal.dot(tangents[i])).normalized()
        frames.append((normal.copy(), tangents[i].cross(normal).normalized()))
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    rings = []
    length = [0.0]
    for i in range(1, count):
        length.append(length[-1] + (path[i] - path[i - 1]).length)
    for i, (centre, (n, b)) in enumerate(zip(path, frames)):
        r = radius(i / (count - 1)) if callable(radius) else radius
        rings.append([bm.verts.new(centre + (n * math.cos(a) + b * math.sin(a)) * r)
                      for a in (2 * math.pi * s / sides for s in range(sides))])
    segments = count if closed else count - 1
    for i in range(segments):
        j = (i + 1) % count
        for s in range(sides):
            s2 = (s + 1) % sides
            face = bm.faces.new((rings[i][s], rings[i][s2], rings[j][s2], rings[j][s]))
            v0 = length[i] * v_scale
            v1 = (length[j] if j else length[-1] + (path[0] - path[-1]).length) * v_scale
            for loop, (a, b) in zip(face.loops, ((s, v0), (s + 1, v0), (s + 1, v1), (s, v1))):
                loop[uv].uv = (a / sides * u_repeat, b)
    if caps and not closed:
        for ring, flip in ((rings[0], True), (rings[-1], False)):
            face = bm.faces.new(list(reversed(ring)) if flip else ring)
            for loop in face.loops:
                loop[uv].uv = (0.5, 0.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, True)


def transform(obj, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1)):
    """Apply a rotation (Euler XYZ radians), scale and location to an object's mesh data."""
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def duplicate(obj, name):
    copy = obj.copy()
    copy.data = obj.data.copy()
    copy.name = name
    copy.data.name = name
    bpy.context.scene.collection.objects.link(copy)
    return copy


def drop_to_ground(objects):
    lowest = min((o.matrix_world @ Vector(c)).z for o in objects for c in o.bound_box)
    for o in objects:
        for v in o.data.vertices:
            v.co.z -= lowest


def clamp_ground(obj):
    for v in obj.data.vertices:
        v.co.z = max(0.0, v.co.z)


# ---------------------------------------------------------------- LODs and export
def finish(base_name, lods, tints, occlusion, shade=None, prop=None):
    """lods: [LOD0, LOD1, LOD2] objects (uncoloured); occlusion: dict for pl.vertex_occlusion per level (rays scale
    down). Colours, names and exports work/<prop>_export.glb."""
    prop = prop or base_name.lower()
    done = []
    for level, obj in enumerate(lods):
        rays = max(10, int(occlusion.get('rays', 40) * (1.0, 0.6, 0.35, 0.25)[level]))
        mean = pl.vertex_occlusion(obj, rays=rays, distance=occlusion['distance'], strength=occlusion['strength'],
                                   floor=occlusion.get('floor', True))
        colourise(obj, tints, shade)
        name = base_name if level == 0 else f'{base_name}_LOD{level}'
        obj.name = name
        obj.data.name = name
        print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(mean, 3))
        done.append(obj)
    os.makedirs(WORK, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{prop}.blend'))
    pl.export(done, os.path.join(WORK, f'{prop}_export.glb'))
    return done


def decimated(obj, name, target):
    copy = duplicate(obj, name)
    pl.decimate_to(copy, target)
    return copy
