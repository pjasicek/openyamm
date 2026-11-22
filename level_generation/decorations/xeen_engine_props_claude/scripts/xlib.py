"""Shared Blender helpers of the Xeen engine props (haybale2, 7dec12, 7dec41). Imports the New Sorpigal props library
(../../mm6_new_sorpigal_3d/props/scripts/props_lib.py, read only) as pl for lathes, joins, occlusion, export and renders;
materials come from this project's textures/. Adapted copies of the MM7 dressing batch's dlib (fix_winding, save) and
heap_lib (fbm); sweep() is the hanging batch's swept tube with whole texture repeats around the section (seamless,
v per metre along the path, so bark keeps one density along every branch). Sizes in map units (81.7 per metre)."""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector, noise

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DECO = os.path.join(REPO, 'level_generation', 'decorations')
sys.path.insert(0, os.path.join(DECO, 'mm6_new_sorpigal_3d', 'props', 'scripts'))
import props_lib as pl  # noqa: E402

UNITS_PER_METRE = 81.7
TEXTURES = os.path.join(HERE, 'textures')
WORK = os.path.join(HERE, 'work')
REVIEW = os.path.join(HERE, 'review')


def u(value):
    """Map units to Blender metres."""
    return value / UNITS_PER_METRE


def material(name, texture, alpha=False, extras=None):
    saved = pl.TEX
    pl.TEX = TEXTURES
    try:
        return pl.material(name, texture, alpha=alpha, extras=extras)
    finally:
        pl.TEX = saved


def apply(obj):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def fbm(p, octaves=3, scale=40.0, seed=0.0):
    """Fractal noise about zero (roughly -1..1) of a map-unit position."""
    total, amp, freq = 0.0, 1.0, 1.0 / scale
    for _ in range(octaves):
        total += amp * noise.noise(Vector((p[0] * freq + seed, p[1] * freq - seed, p[2] * freq + seed * 0.5)))
        amp *= 0.5; freq *= 2.0
    return total


def _frames(points):
    tangents = []
    for i in range(len(points)):
        a = points[max(i - 1, 0)]; b = points[min(i + 1, len(points) - 1)]
        tangents.append((b - a).normalized())
    normals = []
    up = Vector((0, 0, 1))
    for t in tangents:
        ref = up if abs(t.dot(up)) < 0.9 else Vector((1, 0, 0))
        n = (ref - t * ref.dot(t)).normalized()
        if normals and n.dot(normals[-1]) < 0:
            n = -n
        normals.append(n)
    return tangents, normals


def sweep(name, points, radii, sides, mat, tile=0.6, caps=True, phase=0.0):
    """Tube along points (map units) with a radius per point. u: a whole number of texture repeats around the section
    (round(circumference / tile), at least one: no seam), v: path length in metres / tile. Ends get a flat cap
    (UV centre)."""
    pts = [Vector(p) / UNITS_PER_METRE for p in points]
    rs = [u(r) for r in radii]
    tangents, normals = _frames(pts)
    mean_r = sum(rs) / len(rs)
    repeats = max(1, round(2 * math.pi * mean_r / tile))
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    rings = []
    for p, t, nrm, r in zip(pts, tangents, normals, rs):
        b = t.cross(nrm)
        rings.append([bm.verts.new(p + (nrm * math.cos(2 * math.pi * s / sides + phase) +
                                       b * math.sin(2 * math.pi * s / sides + phase)) * r) for s in range(sides)])
    lengths = [0.0]
    for a, c in zip(pts, pts[1:]):
        lengths.append(lengths[-1] + (c - a).length)
    for i in range(len(pts) - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            f = bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
            for loop, (uu, vv) in zip(f.loops, ((s, i), (s + 1, i), (s + 1, i + 1), (s, i + 1))):
                loop[uv].uv = (uu / sides * repeats, lengths[vv] / tile)
    if caps:
        for ring in (rings[0], rings[-1]):
            f = bm.faces.new(ring)
            for loop in f.loops:
                loop[uv].uv = (0.5, 0.5)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method='BEAUTY',
                          ngon_method='BEAUTY')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, True)


def fix_winding(obj):
    """Turn every closed loose part outward (positive signed volume); parts split by shared positions, as
    check_winding.py does. Returns the number of parts flipped. (Copy of the MM7 dressing dlib.fix_winding.)"""
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    key = {v: tuple(round(c, 6) for c in v.co) for v in bm.verts}
    by_pos = {}
    for f in bm.faces:
        for v in f.verts:
            by_pos.setdefault(key[v], []).append(f.index)
    parent = list(range(len(bm.faces)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for faces in by_pos.values():
        for f in faces[1:]:
            a, b = find(faces[0]), find(f)
            if a != b:
                parent[a] = b
    groups = {}
    for f in bm.faces:
        groups.setdefault(find(f.index), []).append(f)
    flipped = 0
    for faces in groups.values():
        edges = {}
        volume = 0.0
        for f in faces:
            p = [Vector(key[v]) for v in f.verts]
            for i in range(1, len(p) - 1):
                volume += p[0].dot(p[i].cross(p[i + 1])) / 6.0
            for i in range(len(p)):
                e = tuple(sorted((key[f.verts[i]], key[f.verts[(i + 1) % len(p)]])))
                edges[e] = edges.get(e, 0) + 1
        if all(n == 2 for n in edges.values()) and volume < 0:
            bmesh.ops.reverse_faces(bm, faces=faces)
            flipped += 1
    bm.to_mesh(obj.data); bm.free()
    obj.data.update()
    return flipped


def save(prop, lods, winding=True):
    """Save work/<prop>.blend (review.py renders it) and export work/<prop>_export.glb (finish.py links the LODs).
    lods: [LOD0, LOD1, ...] named Base, Base_LOD1, ..."""
    os.makedirs(WORK, exist_ok=True)
    if winding:
        print('WINDING fixed', prop, [fix_winding(o) for o in lods])
    lo, hi = pl.bounds(lods[:1])
    print('BOUNDS', prop, [round(v * UNITS_PER_METRE, 1) for v in lo], [round(v * UNITS_PER_METRE, 1) for v in hi])
    print('TRIS', prop, [pl.triangles(o) for o in lods])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{prop}.blend'))
    pl.export(lods, os.path.join(WORK, f'{prop}_export.glb'))
