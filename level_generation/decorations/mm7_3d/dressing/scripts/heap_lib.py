"""Builders shared by the heaps (7dec10, 7dec11): a polar-grid mound from a height function, lumpy rocks, bare
dead shrubs, and a per-face box projection of texture coordinates. Map units throughout."""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

pl, hl, u = dlib.pl, dlib.hl, dlib.u


def fbm(x, y, z=0.0, octaves=3, scale=40.0, seed=0.0):
    """Fractal noise about zero (roughly -1..1) of map-unit coordinates."""
    total, amp, freq = 0.0, 1.0, 1.0 / scale
    for _ in range(octaves):
        total += amp * noise.noise(Vector((x * freq + seed, y * freq - seed, z * freq)))
        amp *= 0.5; freq *= 2.0
    return total


def box_uv(bm, scale):
    """Texture coordinates by face: projected along the face normal's dominant axis, scale repeats per metre."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for loop in f.loops:
            c = loop.vert.co
            a, b = [(c.y, c.z), (c.x, c.z), (c.x, c.y)][ax]
            loop[uv].uv = (a * scale, b * scale)


def mound(name, height_fn, rx, ry, rings, segments, materials, material_fn, uv_scale=1.0):
    """A closed-bottom mound over the ellipse rx x ry (map units): rings of vertices at radius fraction t (0 centre .. 1
    edge) with z = height_fn(x, y), edge at z 0. material_fn(x, y, z) -> index into materials, per face centroid."""
    bm = bmesh.new()
    centre = bm.verts.new((0, 0, u(height_fn(0.0, 0.0))))
    grid = []
    for i in range(1, rings + 1):
        t = i / rings
        t = t ** 0.85
        row = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            x, y = rx * t * math.cos(a), ry * t * math.sin(a)
            z = 0.0 if i == rings else max(0.0, height_fn(x, y))
            row.append(bm.verts.new((u(x), u(y), u(z))))
        grid.append(row)
    for s in range(segments):
        bm.faces.new((centre, grid[0][s], grid[0][(s + 1) % segments]))
    for lower, upper in zip(grid, grid[1:]):
        for s in range(segments):
            s2 = (s + 1) % segments
            bm.faces.new((lower[s], upper[s], upper[s2], lower[s2]))
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        c = f.calc_center_median() * dlib.UNITS_PER_METRE
        f.material_index = material_fn(c.x, c.y, c.z)
    box_uv(bm, uv_scale)
    obj = pl.to_object(name, bm, None, True)
    for m in materials:
        obj.data.materials.append(m)
    return obj


def rock(name, centre, size, seed, level, mat, flat=0.75, sink=0.25, uv_scale=1.5):
    """A lumpy stone: an icosphere (subdivisions by level) scaled to size (x, y, z, map units), displaced by noise,
    its lower part sunk below centre z by sink x height."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=(2, 1, 1, 1)[level], radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        k = 1 + 0.3 * noise.noise(d * 1.4 + Vector((seed, 0, seed))) + 0.1 * noise.noise(d * 4 + Vector((0, seed, 0)))
        p = d * k
        if p.z < 0:
            p.z *= flat
        v.co = Vector((u(centre[0] + p.x * size[0] / 2), u(centre[1] + p.y * size[1] / 2),
                       u(centre[2] + p.z * size[2] / 2 - sink * size[2] / 2)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    box_uv(bm, uv_scale)
    return pl.to_object(name, bm, mat, True)


def shrub(name, base, height, spread, seed, level, mat, radius=1.6):
    """A bare dead shrub: a few crooked stems from base, each forking twice into thinning twigs (swept tubes)."""
    rng = np.random.default_rng(int(seed * 1000) % 2 ** 31)
    parts = []
    sides = (4, 3, 3, 3)[level]
    depth = (2, 1, 0, 0)[level]

    def grow(start, direction, length, r, d, k):
        pts, radii = [Vector(start)], [r]
        p, dirn = Vector(start), Vector(direction).normalized()
        steps = 3 if level == 0 else 2
        for i in range(steps):
            dirn = (dirn + Vector(rng.normal(0, 0.25, 3))).normalized()
            p = p + dirn * (length / steps)
            pts.append(p.copy()); radii.append(r * (1 - 0.55 * (i + 1) / steps))
        parts.append(hl.sweep(f'{name}{k}', pts, radii, sides, mat, caps=False, v_scale=4.0))
        if d > 0:
            for j in range(2):
                side = Vector(rng.normal(0, 1, 3)); side.z = abs(side.z) * 0.5 + 0.3
                grow(p, (dirn + side * 0.7).normalized(), length * 0.6, radii[-1] * 0.9, d - 1, f'{k}_{j}')

    stems = (4, 3, 2, 2)[level]
    for s in range(stems):
        a = 2 * math.pi * s / stems + seed
        direction = Vector((math.cos(a) * spread, math.sin(a) * spread, 1.0))
        grow(base, direction, height * (0.55 + 0.1 * s % 3), radius, depth, str(s))
    return parts
