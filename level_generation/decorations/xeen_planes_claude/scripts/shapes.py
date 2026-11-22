"""Mesh builders (Blender bmesh) shared by the statues and the props: swept tubes, lathes, lofts, flattened
ellipsoids, rough blocks; and a helper to turn a bmesh into an object."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise


def to_object(bm, name, material=None, collection=None):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    if material is not None:
        me.materials.append(material)
    return ob


def _frames(pts):
    """Parallel-transport frames (tangent, normal, binormal) along a polyline."""
    tans = []
    for i in range(len(pts)):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tans.append((b - a).normalized())
    t0 = tans[0]
    ref = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    n = (ref - t0 * ref.dot(t0)).normalized()
    out = []
    for t in tans:
        n = (n - t * n.dot(t)).normalized()
        out.append((t, n, t.cross(n)))
    return out


def catmull(points, per=6):
    """Catmull-Rom resample of control points (Vectors), `per` samples per span."""
    p = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(points[-1])
    return out


def tube(bm, pts, radii, sides=10, flat=1.0, twist=0.0, cap_start=True, cap_end=True, up=None):
    """Sweep an ellipse (radius r, r*flat) along pts; a radius of 0 at an end closes it to a point."""
    frames = _frames(pts)
    if up is not None:
        frames2 = []
        for t, n, b in frames:
            n2 = (Vector(up) - t * Vector(up).dot(t))
            if n2.length < 1e-6:
                frames2.append((t, n, b))
                continue
            n2.normalize()
            frames2.append((t, n2, t.cross(n2)))
        frames = frames2
    rings = []
    for i, (p, (t, n, b), r) in enumerate(zip(pts, frames, radii)):
        if r <= 1e-5:
            rings.append([bm.verts.new(p)])
            continue
        ang0 = twist * i / max(1, len(pts) - 1)
        ring = []
        for k in range(sides):
            a = ang0 + 2 * math.pi * k / sides
            ring.append(bm.verts.new(p + n * (math.cos(a) * r) + b * (math.sin(a) * r * flat)))
        rings.append(ring)
    for ra, rb in zip(rings, rings[1:]):
        if len(ra) == 1 and len(rb) == 1:
            continue
        if len(ra) == 1:
            for k in range(sides):
                bm.faces.new((ra[0], rb[k], rb[(k + 1) % sides]))
        elif len(rb) == 1:
            for k in range(sides):
                bm.faces.new((ra[k], rb[0], ra[(k + 1) % sides]))
        else:
            for k in range(sides):
                bm.faces.new((ra[k], rb[k], rb[(k + 1) % sides], ra[(k + 1) % sides]))
    if cap_start and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if cap_end and len(rings[-1]) > 1:
        bm.faces.new(rings[-1])


def lathe(bm, profile, segments=24, centre=Vector((0, 0, 0)), axis_matrix=None, cap_bottom=True, cap_top=True):
    """Revolve a (radius, z) profile about z; radius 0 rows become poles."""
    m = axis_matrix or Matrix.Identity(3)
    rings = []
    for r, z in profile:
        if r <= 1e-6:
            rings.append([bm.verts.new(centre + m @ Vector((0, 0, z)))])
            continue
        rings.append([bm.verts.new(centre + m @ Vector((r * math.cos(2 * math.pi * k / segments),
                                                          r * math.sin(2 * math.pi * k / segments), z)))
                      for k in range(segments)])
    for ra, rb in zip(rings, rings[1:]):
        if len(ra) == 1 and len(rb) == 1:
            continue
        if len(ra) == 1:
            for k in range(segments):
                bm.faces.new((ra[0], rb[(k + 1) % segments], rb[k]))
        elif len(rb) == 1:
            for k in range(segments):
                bm.faces.new((ra[k], ra[(k + 1) % segments], rb[0]))
        else:
            for k in range(segments):
                bm.faces.new((ra[k], ra[(k + 1) % segments], rb[(k + 1) % segments], rb[k]))
    if cap_bottom and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if cap_top and len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    return rings


def loft(bm, rings, cap_bottom=True, cap_top=False):
    """Quads between consecutive rings of equal length (lists of Vectors)."""
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for ra, rb in zip(vs, vs[1:]):
        for k in range(n):
            bm.faces.new((ra[k], ra[(k + 1) % n], rb[(k + 1) % n], rb[k]))
    if cap_bottom:
        c = bm.verts.new(sum(rings[0], Vector()) / n)
        for k in range(n):
            bm.faces.new((vs[0][(k + 1) % n], vs[0][k], c))
    if cap_top:
        c = bm.verts.new(sum(rings[-1], Vector()) / n)
        for k in range(n):
            bm.faces.new((vs[-1][k], vs[-1][(k + 1) % n], c))
    return vs


def ellipsoid(bm, centre, axes_matrix, radii, segs=10, rings=6):
    """A UV ellipsoid: axes_matrix columns are its axes, radii along them."""
    geom = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    m = Matrix.Translation(centre) @ axes_matrix.to_4x4() @ Matrix.Diagonal((*radii, 1.0))
    bmesh.ops.transform(bm, matrix=m, verts=geom['verts'])


def rough_block(bm, lo, hi, cuts=6, amp=0.03, seed=1, scale=3.0, chamfer=0.06):
    """A box from lo to hi, subdivided, its corners chamfered and its faces displaced by noise (rough-hewn)."""
    geom = bmesh.ops.create_cube(bm, size=1.0)
    verts = geom['verts']
    size = Vector(hi) - Vector(lo)
    mid = (Vector(hi) + Vector(lo)) / 2
    bmesh.ops.transform(bm, matrix=Matrix.Translation(mid) @ Matrix.Diagonal((*size, 1.0)), verts=verts)
    edges = list({e for v in verts for e in v.link_edges})
    bmesh.ops.bevel(bm, geom=edges + verts, offset=chamfer, segments=1, affect='EDGES')
    faces = list({f for v in bm.verts for f in v.link_faces})
    bmesh.ops.subdivide_edges(bm, edges=list({e for f in faces for e in f.edges}), cuts=cuts, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.normal_update()
    off = Vector((seed * 7.1, seed * 3.3, seed * 1.7))
    for v in bm.verts:
        if v.co.z <= lo[2] + 1e-4:
            continue
        d = noise.noise(v.co * scale + off) * amp + noise.noise(v.co * scale * 3.1 + off) * amp * 0.4
        v.co += v.normal * d


def rng(seed):
    return random.Random(seed)
