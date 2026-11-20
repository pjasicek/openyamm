"""Blender helpers for the MM7 plants batch, on top of the MM6 succulents library (succ_lib: the Geo accumulator with
ray-traced vertex occlusion, ribbed sweeps, prickly-pear pads, materials and the LOD export), which is imported
from ../../mm6_new_sorpigal_3d/succulents/scripts with its texture and work folders pointed at plants/.
Adds bent foliage strips (fronds, broad leaves with a folded midrib, hanging dry fronds), tubes mapped into an atlas
strip or a tiling texture, lathes (pots) and crossed cards. Blender Z is up; models stand on z = 0 round the origin.
Texture coordinates are given in image space (v down)."""
import math, os, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'mm6_new_sorpigal_3d', 'succulents', 'scripts'))
import succ_lib as sl      # noqa: E402
import common              # noqa: E402

sl.TEX = common.TEX
sl.WORK = common.WORK
Geo, ribbed, pad, card, export, material, transport_frames, frame = (sl.Geo, sl.ribbed, sl.pad, sl.card, sl.export,
                                                                    sl.material, sl.transport_frames, sl.frame)


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def rotate(v, axis, angle):
    return Matrix.Rotation(angle, 3, Vector(axis).normalized()) @ Vector(v)


def bezier(ctrl, n):
    """Points of a quadratic or cubic Bézier through ctrl (2-4 Vectors), n + 1 samples."""
    c = [Vector(p) for p in ctrl]
    out = []
    for i in range(n + 1):
        t = i / n
        pts = c[:]
        while len(pts) > 1:
            pts = [a * (1 - t) + b * t for a, b in zip(pts, pts[1:])]
        out.append(pts[0])
    return out


def bent_spine(start, direction, length, segments, droop, gravity_power=1.6, side_bend=None):
    """A spine of `segments` equal steps from `start`, turning down by up to `droop` radians (more toward the tip)."""
    d = Vector(direction).normalized()
    pts = [Vector(start)]
    p = Vector(start)
    for j in range(segments):
        t = (j + 0.5) / segments
        axis = d.cross(Vector((0, 0, 1)))
        if axis.length < 1e-6:
            axis = Vector((1, 0, 0))
        dj = rotate(d, axis, -droop * t ** gravity_power) if droop else d
        if side_bend is not None:
            dj = rotate(dj, Vector((0, 0, 1)), side_bend * t)
        p = p + dj * (length / segments)
        pts.append(p.copy())
    return pts


def strip(g, pts, side, width, rect, mat=0, occ_fn=None, normal_fn=None, across=1, fold=0.0, widths=None,
          roll=0.0):
    """A foliage card along the spine `pts` (base -> tip) spanning the atlas rect (u0, v0, u1, v1; the base at v1).
    side: the card's across direction at the base (kept perpendicular to the spine, rotated by `roll` toward the
    tip). across=2 adds a midrib column raised by fold x width along the card normal (a folded leaf). Each quad is
    one axis-aligned texture rectangle, so tools/cut_foliage_cards.py can cut it. Faces wind toward the shading
    normal (normal_fn(p, card_normal) -> normal; default the card normal turned upward)."""
    u0, v0, u1, v1 = rect
    n = len(pts)
    lengths = [0.0]
    for a, b in zip(pts, pts[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    total = lengths[-1] or 1.0
    frames = transport_frames(pts)
    side = Vector(side)
    t0 = frames[0][0]
    side = (side - t0 * side.dot(t0)).normalized()
    sides = []
    for i, (t, a, b) in enumerate(frames):
        if i:
            q = frames[i - 1][0].rotation_difference(t)
            side = q @ side
            side = (side - t * side.dot(t)).normalized()
        sides.append(rotate(side, t, roll * lengths[i] / total) if roll else side)
    cols = [-0.5, 0.0, 0.5] if across == 2 else [-0.5, 0.5]
    us = [u0 + (c + 0.5) * (u1 - u0) for c in cols]
    grid = []
    for i, p in enumerate(pts):
        t = frames[i][0]
        cn = sides[i].cross(t).normalized()
        if cn.z < 0:
            cn = -cn
        w = width * (widths[i] if widths else 1.0)
        row = []
        for c in cols:
            q = p + sides[i] * (c * w)
            if across == 2 and c == 0.0:
                q = q + cn * fold * w
            nrm = normal_fn(q, cn) if normal_fn else (cn + Vector((0, 0, 0.6))).normalized()
            vi = g.vert(q, occ_fn(q, lengths[i] / total) if occ_fn else 1.0)
            g.ao_normal[vi] = nrm
            row.append((vi, nrm))
        grid.append(row)
    vcoord = [v1 - (v1 - v0) * (L / total) for L in lengths]
    for i in range(n - 1):
        for k in range(len(cols) - 1):
            quad = [grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]]
            uv = [(us[k], vcoord[i]), (us[k + 1], vcoord[i]), (us[k + 1], vcoord[i + 1]), (us[k], vcoord[i + 1])]
            idx = [q[0] for q in quad]; nrm = [q[1] for q in quad]
            fn = g.face_normal(idx)
            if fn.dot(sum(nrm, Vector((0, 0, 0)))) < 0:
                idx, uv, nrm = idx[::-1], uv[::-1], nrm[::-1]
            g.face(idx, uv, nrm, mat, solid=False)


def tube(g, pts, radii, sides, mat=0, rect=None, tile=None, occ_fn=None, cap=False, solid=True, phase=0.0):
    """A tube along pts with ring radii; texture either an atlas rect (u round the tube over u0..u1, v base -> tip
    over v1..v0) or tile = (u repeats round, v per metre). Smooth radial normals (a seam column of duplicates).
    cap: closes the tip with a fan."""
    pts = [Vector(p) for p in pts]
    frames = transport_frames(pts)
    lengths = [0.0]
    for a, b in zip(pts, pts[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    total = lengths[-1] or 1.0
    rings = []
    for i, p in enumerate(pts):
        t, a, b = frames[i]
        ring = []
        for s in range(sides + 1):
            ang = phase + 2 * math.pi * s / sides
            d = a * math.cos(ang) + b * math.sin(ang)
            q = p + d * radii[i]
            if rect:
                u = rect[0] + (rect[2] - rect[0]) * s / sides
                v = rect[3] - (rect[3] - rect[1]) * lengths[i] / total
            else:
                u = tile[0] * s / sides
                v = -lengths[i] * tile[1]
            vi = g.vert(q, occ_fn(q) if occ_fn else 1.0)
            g.ao_normal[vi] = d
            ring.append((vi, d, (u, v)))
        rings.append(ring)
    for i in range(len(pts) - 1):
        for s in range(sides):
            quad = [rings[i][s], rings[i][s + 1], rings[i + 1][s + 1], rings[i + 1][s]]
            idx = [q[0] for q in quad]; nrm = [q[1] for q in quad]; uv = [q[2] for q in quad]
            fn = g.face_normal(idx)
            if fn.dot(sum(nrm, Vector((0, 0, 0)))) < 0:
                idx, uv, nrm = idx[::-1], uv[::-1], nrm[::-1]
            g.face(idx, uv, nrm, mat, solid=solid)
    if cap:
        t = frames[-1][0]
        tip = g.vert(pts[-1] + t * radii[-1] * 0.5, occ_fn(pts[-1]) if occ_fn else 1.0)
        g.ao_normal[tip] = t
        for s in range(sides):
            a, b = rings[-1][s], rings[-1][s + 1]
            idx = [a[0], b[0], tip]
            uv = [a[2], b[2], ((a[2][0] + b[2][0]) / 2, a[2][1] - 0.02)]
            nrm = [a[1], b[1], t]
            if g.face_normal(idx).dot(t) < 0:
                idx, uv, nrm = idx[::-1], uv[::-1], nrm[::-1]
            g.face(idx, uv, nrm, mat, solid=solid)


def lathe(g, profile, segments, mat=0, u_repeat=1.0, vcoords=None, occ_fn=None, phase=0.0, crease=(), flat=False,
          solid=True):
    """Surface of revolution of profile [(r, z)] round the z axis (a profile point with r = 0 becomes a fan apex).
    v per profile point from vcoords (image space), u = s / segments x u_repeat. Profile normals are smooth except
    at the indices in `crease` (both neighbouring segments keep their own normals); flat=True gives face normals
    everywhere (a 4-segment lathe is then a square planter)."""
    n = len(profile)
    P = [Vector((r, 0, z)) for r, z in profile]

    def segnormal(k):          # outward normal of segment k -> k + 1 in the (r, z) plane
        dr = profile[k + 1][0] - profile[k][0]; dz = profile[k + 1][1] - profile[k][1]
        L = math.hypot(dr, dz) or 1.0
        return (dz / L, -dr / L)

    def pnormal(k, seg):
        if k in crease or k == 0 or k == n - 1:
            return segnormal(seg)
        a = segnormal(k - 1); b = segnormal(k)
        x, z = a[0] + b[0], a[1] + b[1]
        L = math.hypot(x, z) or 1.0
        return (x / L, z / L)
    vc = vcoords or [1.0 - k / (n - 1) for k in range(n)]
    rings = []
    for k, (r, z) in enumerate(profile):
        ring = []
        for s in range(segments + 1):
            ang = phase + 2 * math.pi * s / segments
            if r < 1e-6:
                vi = g.vert((0, 0, z), occ_fn(Vector((0, 0, z))) if occ_fn else 1.0)
            else:
                q = Vector((math.cos(ang) * r, math.sin(ang) * r, z))
                vi = g.vert(q, occ_fn(q) if occ_fn else 1.0)
            ring.append(vi)
            if r < 1e-6:
                ring = [vi] * (segments + 1)
                break
        rings.append(ring)
    for k in range(n - 1):
        for s in range(segments):
            a0 = phase + 2 * math.pi * s / segments; a1 = phase + 2 * math.pi * (s + 1) / segments
            am = (a0 + a1) / 2
            idx = [rings[k][s], rings[k][s + 1], rings[k + 1][s + 1], rings[k + 1][s]]
            uv = [(u_repeat * s / segments, vc[k]), (u_repeat * (s + 1) / segments, vc[k]),
                  (u_repeat * (s + 1) / segments, vc[k + 1]), (u_repeat * s / segments, vc[k + 1])]
            nrm = []
            for (kk, aa) in ((k, a0), (k, a1), (k + 1, a1), (k + 1, a0)):
                if flat:
                    nrm.append('flat')
                else:
                    nr, nz = pnormal(kk, k)
                    nrm.append(Vector((math.cos(aa) * nr, math.sin(aa) * nr, nz)))
            # drop the degenerate corner of a fan apex
            keep = [i for i in range(4) if not (i > 0 and idx[i] == idx[i - 1]) and not (i == 3 and idx[3] == idx[0])]
            idx = [idx[i] for i in keep]; uv = [uv[i] for i in keep]; nrm = [nrm[i] for i in keep]
            if len(idx) < 3:
                continue
            nr, nz = segnormal(k)
            want = Vector((math.cos(am) * nr, math.sin(am) * nr, nz))
            if g.face_normal(idx).dot(want) < 0:
                idx, uv, nrm = idx[::-1], uv[::-1], nrm[::-1]
            g.face(idx, uv, nrm, mat, solid=solid)
    return rings


def crossed(g, centre, size, rect, count, rng, mat=0, occ_fn=None, normal_fn=None, up_bias=0.0, squash=1.0):
    """`count` square cards through `centre` with normals spread over the sphere (Fibonacci, randomly rotated):
    a spiky ball from a full-star texture (Joshua tree rosettes)."""
    rot = Matrix.Rotation(rng.uniform(0, 2 * math.pi), 3, 'Z') @ Matrix.Rotation(rng.uniform(0, math.pi), 3, 'X')
    for i in range(count):
        z = 1 - (i + 0.5) / count
        r = math.sqrt(max(1 - z * z, 0)); th = i * math.pi * (3 - math.sqrt(5))
        nrm = (rot @ Vector((math.cos(th) * r, math.sin(th) * r, z))).normalized()
        a, b, _ = frame(nrm)
        b = b * squash
        base = centre - b * size * 0.5
        card(g, base, a * size, b * size, (rect[0], rect[1], rect[2], rect[3]),
             (lambda q, c=centre: normal_fn(q) if normal_fn else (q - c).normalized() + Vector((0, 0, up_bias))),
             occ_fn or (lambda q: 1.0), mat=mat)
