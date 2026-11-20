"""Hanging and impaling props for the leftover corpses (Blender): polyline tubes with parallel-transport frames
(ropes, hooks, bent wire), a hangman's knot coil, chains of alternating stadium links (a plain tube at coarse LODs)
and J hooks. All return pl.to_object meshes in world space, u around and v along (v in metres x v_scale)."""
import math

import bmesh
from mathutils import Vector

import leftovers_lib as ll

pl = ll.pl


def polyline_tube(name, points, radius, sides, mat=None, v_scale=1.0, caps=True, twist=0.0, radii=None):
    """Tube through the points (radius per point via radii); twist turns the ring by radians per metre."""
    pts = [Vector(p) for p in points]
    radii = radii or [radius] * len(pts)
    tangents = []
    for i in range(len(pts)):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        tangents.append((b - a).normalized())
    normal = tangents[0].orthogonal().normalized()
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    rings, along = [], [0.0]
    for i, (p, t) in enumerate(zip(pts, tangents)):
        if i:
            along.append(along[-1] + (p - pts[i - 1]).length)
            normal = (normal - t * normal.dot(t)).normalized()
        binormal = t.cross(normal)
        ring = []
        for s in range(sides):
            a = 2 * math.pi * s / sides + twist * along[-1]
            ring.append(bm.verts.new(p + (normal * math.cos(a) + binormal * math.sin(a)) * radii[i]))
        rings.append(ring)
    for i in range(len(pts) - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            f = bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
            for loop, (uu, k) in zip(f.loops, ((s, i), (s + 1, i), (s + 1, i + 1), (s, i + 1))):
                loop[uv].uv = (uu / sides, along[k] * v_scale)
    if caps:
        for ring, flip in ((rings[0], True), (rings[-1], False)):
            f = bm.faces.new(list(reversed(ring)) if flip else ring)
            for loop in f.loops:
                loop[uv].uv = (0.5, 0.5)
    bm.normal_update()
    return pl.to_object(name, bm, mat)


def rope(name, points, radius, sides, mat, level=0):
    """Laid rope: the rope texture repeats every four diameters along it (three strands per repeat)."""
    return polyline_tube(name, points, radius, sides, mat, v_scale=1.0 / (8 * radius), caps=True)


def subdivide(points, step):
    out = [Vector(points[0])]
    for a, b in zip(points, points[1:]):
        a, b = Vector(a), Vector(b)
        n = max(1, int(math.ceil((b - a).length / step)))
        out += [a.lerp(b, k / n) for k in range(1, n + 1)]
    return out


def coil(name, bottom, top, radius, wire, turns, sides, mat, ring_sides=10):
    """Hangman's knot: a column of tight rope wraps (a helix of `turns` turns) round the vertical line bottom..top."""
    bottom, top = Vector(bottom), Vector(top)
    axis = (top - bottom); length = axis.length; axis.normalize()
    side = axis.orthogonal().normalized(); other = axis.cross(side)
    steps = int(turns * ring_sides) + 1
    points = []
    for k in range(steps):
        t = k / (steps - 1)
        a = 2 * math.pi * turns * t
        points.append(bottom + axis * (length * t) + (side * math.cos(a) + other * math.sin(a)) * radius)
    return polyline_tube(name, points, wire, sides, mat, v_scale=1.0 / (8 * wire))


def link_ring(bm, uv, centre, axis, across, length, width, wire, segments, sides):
    """One stadium chain link in the plane of axis/across (axis along the chain)."""
    axis, across = axis.normalized(), across.normalized()
    normal = axis.cross(across)
    straight = max(length - width, 0.0) / 2
    r = width / 2 - wire
    path = []
    for k in range(segments):
        a = 2 * math.pi * k / segments
        x = math.cos(a) * r; y = math.sin(a) * r
        y += straight if y >= 0 else -straight
        path.append(centre + across * x + axis * y)
    rings = []
    for k, p in enumerate(path):
        t = (path[(k + 1) % segments] - path[k - 1]).normalized()
        n1 = normal; n2 = t.cross(n1)
        rings.append([bm.verts.new(p + (n1 * math.cos(2 * math.pi * s / sides) +
                                        n2 * math.sin(2 * math.pi * s / sides)) * wire) for s in range(sides)])
    for k in range(segments):
        k2 = (k + 1) % segments
        for s in range(sides):
            s2 = (s + 1) % sides
            f = bm.faces.new((rings[k][s], rings[k][s2], rings[k2][s2], rings[k2][s]))
            for loop, (a, b) in zip(f.loops, ((s, k), (s2, k), (s2, k2), (s, k2))):
                loop[uv].uv = (a / sides, b / segments)


def chain(name, top, bottom, link_length, wire, mat, level=0, twist_deg=0.0, detail=((10, 4), (6, 3))):
    """Chain from top to bottom: links of link_length (outer) overlapping by two wire diameters, each turned 90
    degrees from the last. detail: (segments, sides) of a link at LOD0 and LOD1; LOD2+ a single four-sided tube of the
    chain's width (from LOD1 when detail has one entry)."""
    top, bottom = Vector(top), Vector(bottom)
    axis = (bottom - top); length = axis.length; axis.normalize()
    if level >= min(2, len(detail)):
        return polyline_tube(name, [top, bottom], link_length * 0.22, 4, mat, v_scale=2.0)
    across0 = axis.orthogonal().normalized()
    a = math.radians(twist_deg)
    across0 = across0 * math.cos(a) + axis.cross(across0) * math.sin(a)
    pitch = link_length - 2 * wire * 2
    count = max(1, int(round((length - link_length) / pitch)) + 1)
    pitch = (length - link_length) / max(count - 1, 1)
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    segments, sides = detail[level]
    for k in range(count):
        centre = top + axis * (link_length / 2 + k * pitch)
        across = across0 if k % 2 == 0 else axis.cross(across0)
        link_ring(bm, uv, centre, axis, across, link_length, link_length * 0.55, wire, segments, sides)
    bm.normal_update()
    return pl.to_object(name, bm, mat)


def hook(name, top, drop, bend_radius, wire, mat, sides=6, facing=(1, 0, 0), tip=0.6):
    """J hook hanging from top: a straight shank down `drop`, a half-circle bend toward `facing` and back up to a
    point (tip x bend_radius tall, tapered)."""
    top = Vector(top); f = Vector(facing).normalized()
    pts = [top, top - Vector((0, 0, drop))]
    centre = pts[-1] + f * bend_radius
    for k in range(1, 9):
        a = math.pi * k / 8
        pts.append(centre - f * bend_radius * math.cos(a) - Vector((0, 0, bend_radius * math.sin(a))))
    end = pts[-1]
    pts.append(end + Vector((0, 0, tip * bend_radius)) - f * 0.15 * bend_radius)
    radii = [wire] * (len(pts) - 1) + [wire * 0.2]
    return polyline_tube(name, pts, wire, sides, mat, v_scale=4.0, radii=radii)
