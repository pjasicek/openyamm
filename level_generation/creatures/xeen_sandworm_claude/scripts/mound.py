"""Procedural sand mound and rubble for the sand worm (run inside Blender; imported by clean.py).

The mound is a low irregular heap on the floor around the worm's base: a polar grid (rings x segments) whose height
follows a soft dome profile with a lumpy, angle- and radius-dependent noise, the rim at the floor and no bottom (an open
shell: the floor hides its underside, which would only waste atlas space). The rubble is a handful of angular rock chunks (convex hulls of jittered points)
lying on the mound's slope and around its rim, each partly sunk into the sand and never below the floor.
Everything is deterministic (fixed seed)."""
import math
import bmesh
import numpy as np
from mathutils import Vector, Matrix


def noise2(r, th, seed=0.0):
    """Smooth lumpy noise in -1..1 from a few sine terms (angle-periodic)."""
    return (0.45 * math.sin(3 * th + 1.3 + seed) + 0.30 * math.sin(5 * th + 0.4 + 2 * r + seed)
            + 0.20 * math.sin(8 * th + 2.1 - 3 * r) + 0.15 * math.sin(13 * th + 0.7 + 5 * r + seed)) / 1.1


def height(r, th, R0, R1, H):
    """Mound height at radius r (R0 = worm base radius, R1 = mound rim) and angle th."""
    if r >= R1:
        return 0.0
    u = max(0.0, (r - R0 * 0.55) / (R1 - R0 * 0.55))
    prof = (1 - u * u) ** 1.6 if u > 0 else 1.0
    lump = 1 + 0.22 * noise2(u, th) + 0.10 * math.sin(11 * th + 6 * u)
    rim_wobble = 1.0
    return H * prof * lump * rim_wobble


def rim_radius(th, R1):
    return R1 * (1 + 0.08 * math.sin(3 * th + 0.8) + 0.05 * math.sin(7 * th + 2.0) + 0.03 * math.sin(11 * th))


def build_mound(bm, R0, R1, H, rings=11, segs=48):
    """Add the mound to bm; returns the list of new faces."""
    faces = []
    grid = []
    for i in range(rings + 1):
        row = []
        for j in range(segs):
            th = 2 * math.pi * j / segs
            Rr = rim_radius(th, R1)
            # radii: dense near the worm and the rim
            s = i / rings
            r = 0.15 * R0 + (Rr - 0.15 * R0) * (0.5 - 0.5 * math.cos(math.pi * s)) ** 0.85
            z = max(0.0015, height(r, th, R0, Rr, H)) if i < rings else 0.0015
            row.append(bm.verts.new((r * math.cos(th), r * math.sin(th), z)))
        grid.append(row)
    top = bm.verts.new((0, 0, height(0, 0, R0, R1, H)))
    for j in range(segs):
        faces.append(bm.faces.new((top, grid[0][j], grid[0][(j + 1) % segs])))
    for i in range(rings):
        for j in range(segs):
            a, b = grid[i][j], grid[i][(j + 1) % segs]
            c, d = grid[i + 1][(j + 1) % segs], grid[i + 1][j]
            faces.append(bm.faces.new((a, d, c)))
            faces.append(bm.faces.new((a, c, b)))
    return faces


def build_rocks(bm, R0, R1, H, n=11, seed=7):
    """Angular rock chunks on the slope and at the rim. Returns a list of face lists (one per rock)."""
    rng = np.random.default_rng(seed)
    out = []
    for k in range(n):
        th = 2 * math.pi * (k + 0.35 * rng.random()) / n
        on_rim = k % 3 == 0
        r = (rim_radius(th, R1) * (0.98 + 0.12 * rng.random())) if on_rim else \
            (R0 * 1.05 + (rim_radius(th, R1) - R0 * 1.05) * (0.25 + 0.5 * rng.random()))
        size = (0.032 + 0.04 * rng.random()) * (1.25 if on_rim else 1.0)
        # a flattened slab: random points in an ellipsoid, convex hull
        pts = rng.normal(size=(18, 3))
        pts /= np.linalg.norm(pts, axis=1, keepdims=True)
        pts *= np.array([1.0, 0.7 + 0.3 * rng.random(), 0.42 + 0.15 * rng.random()]) * size
        pts *= (0.8 + 0.4 * rng.random(size=(18, 1)))
        rot = Matrix.Rotation(rng.random() * 2 * math.pi, 3, 'Z') @ Matrix.Rotation((rng.random() - 0.5) * 0.7, 3, 'X')
        ground = height(r, th, R0, rim_radius(th, R1), H) if r < rim_radius(th, R1) else 0.0
        centre = Vector((r * math.cos(th), r * math.sin(th), 0.0))
        verts = []
        for p in pts:
            v = rot @ Vector(p)
            verts.append(bm.verts.new(centre + v))
        res = bmesh.ops.convex_hull(bm, input=verts)
        geom_faces = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]
        for v in verts:
            if v.is_valid and not v.link_faces:
                bm.verts.remove(v)
        # sink: lowest point 18 % of its height below the local sand surface, never below the floor
        hv = {v for f in geom_faces for v in f.verts}
        zmin = min(v.co.z for v in hv); zmax = max(v.co.z for v in hv)
        dz = ground - 0.18 * (zmax - zmin) - zmin
        dz = max(dz, -zmin + 0.001)
        for v in hv:
            v.co.z += dz
        out.append(geom_faces)
    return out
