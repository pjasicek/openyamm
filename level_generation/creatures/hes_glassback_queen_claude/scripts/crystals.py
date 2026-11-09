"""Faceted glass crystals for the Glassback crest (run inside Blender; pure bmesh, no inputs).

A crystal is an irregular N-sided prism sunk into the hide, ending in an off-centre faceted point. Every facet is
flat-shaded (its own vertices: hard edges, glTF exports split normals) and maps onto one whole tile of the glass atlas
(glass_texture.py: 2x2 tiles; u across the facet, v from the root to the tip). Glowing cracks are thin emissive strips
standing 1.5 mm proud of some facets, from the root up; a glowing seam ring sits around the root where the crystal
enters the hide. Material slots: 0 Glass, 1 Glow.

crystal(bm, root, axis, height, radius, sides, rng, lod, crack_count) adds one crystal to bm."""
import math
import random

import bmesh
from mathutils import Vector, Matrix, Quaternion

TILES = [(0.0, 0.5), (0.5, 0.5), (0.0, 0.0), (0.5, 0.0)]      # tile origins (u, v) in the 2x2 atlas


def _frame(axis):
    z = axis.normalized()
    x = Vector((1, 0, 0)) if abs(z.x) < 0.9 else Vector((0, 1, 0))
    y = z.cross(x).normalized()
    x = y.cross(z).normalized()
    return x, y, z


def _quad_uv(tile, u0, u1, v0, v1):
    tu, tv = TILES[tile]
    return [(tu + 0.5 * u0, tv + 0.5 * v0), (tu + 0.5 * u1, tv + 0.5 * v0),
            (tu + 0.5 * u1, tv + 0.5 * v1), (tu + 0.5 * u0, tv + 0.5 * v1)]


def _face(bm, uv_layer, pts, uvs, mat):
    verts = [bm.verts.new(p) for p in pts]
    f = bm.faces.new(verts)
    f.material_index = mat
    f.smooth = False
    for loop, uv in zip(f.loops, uvs):
        loop[uv_layer].uv = uv
    return f


def crystal(bm, root, axis, height, radius, sides, rng, lod=0, crack_count=2, sink=None, seam=True, twist=0.0,
            glow_scale=1.0, long_dir=None, aspect=(1.0, 1.0), edge_glow=0, hide_hit=None):
    """long_dir/aspect make a plate: the cross-section is aspect[0] x radius along long_dir (the body's length) and
    aspect[1] x radius across it; edge_glow adds glowing strips along that many vertical edges."""
    uv_layer = bm.loops.layers.uv.verify()
    x, y, z = _frame(axis)
    if long_dir is not None:
        x = (Vector(long_dir) - z * Vector(long_dir).dot(z)).normalized()
        y = z.cross(x).normalized()
    rot = Matrix.Rotation(twist, 3, z)
    x, y = rot @ x, rot @ y
    ax, ay = aspect
    sink = radius * 1.3 if sink is None else sink
    base_c = Vector(root) - z * sink
    shaft = height * rng.uniform(0.45, 0.62)              # prism part above the hide, the rest is the point
    radii = [radius * rng.uniform(0.75, 1.15) for _ in range(sides)]
    angles = sorted(2 * math.pi * (i + rng.uniform(-0.22, 0.22)) / sides for i in range(sides))
    taper = rng.uniform(0.72, 0.92)                       # the prism narrows a little toward the point
    lean = (x * rng.uniform(-0.18, 0.18) + y * rng.uniform(-0.18, 0.18)) * radius
    apex = Vector(root) + z * height + lean * 1.6
    bottom = [base_c + (x * math.cos(a) * ax + y * math.sin(a) * ay) * r for a, r in zip(angles, radii)]
    top = [Vector(root) + z * shaft + lean + (x * math.cos(a) * ax + y * math.sin(a) * ay) * r * taper
           for a, r in zip(angles, radii)]
    for i in range(sides):
        j = (i + 1) % sides
        tile = rng.randrange(4)
        # prism facet (v 0..0.6 of the tile), then its point facet (0.6..1) as a triangle
        f = _face(bm, uv_layer, [bottom[i], bottom[j], top[j], top[i]], _quad_uv(tile, 0, 1, 0, 0.6), 0)
        tu, tv = TILES[tile]
        tri = [bm.verts.new(p) for p in (top[i], top[j], apex)]
        ft = bm.faces.new(tri)
        ft.material_index = 0
        ft.smooth = False
        for loop, uv in zip(ft.loops, [(tu, tv + 0.3), (tu + 0.5, tv + 0.3), (tu + 0.25, tv + 0.5)]):
            loop[uv_layer].uv = uv
    if lod >= 2:
        return
    # glowing cracks on a few facets: thin zig-zag strips standing proud of the facet
    if lod == 0:
        for k in rng.sample(range(sides), min(crack_count, sides)):
            j = (k + 1) % sides
            a0, a1, b0, b1 = bottom[k], bottom[j], top[k], top[j]
            n = (a1 - a0).cross(b0 - a0).normalized()
            if n.dot((a0 + a1) / 2 - base_c) < 0:
                n = -n
            s0 = rng.uniform(0.3, 0.7)
            width = radius * 0.15 * glow_scale
            pts_l, pts_r = [], []
            segs = 4
            reach = rng.uniform(0.55, 1.0)
            for m in range(segs + 1):
                t = m / segs * reach
                s = min(max(s0 + rng.uniform(-0.12, 0.12) * (m > 0), 0.12), 0.88)
                e0 = a0.lerp(b0, t)
                e1 = a1.lerp(b1, t)
                c = e0.lerp(e1, s) + n * 0.0015
                side = (e1 - e0).normalized() * width * (1.0 - 0.6 * m / segs)
                pts_l.append(c - side)
                pts_r.append(c + side)
            for m in range(segs):
                _face(bm, uv_layer, [pts_l[m], pts_r[m], pts_r[m + 1], pts_l[m + 1]],
                      [(0.25, 0.25)] * 4, 1)
    for k in rng.sample(range(sides), min(edge_glow, sides)) if lod <= 1 else []:
        # light leaking along a vertical edge: a strip straddling the edge, slightly proud of both facets
        i0, ip, inx = k, (k - 1) % sides, (k + 1) % sides
        n = ((bottom[k] - base_c) + (top[k] - Vector(root) - z * shaft - lean)).normalized()
        along = (top[k] - bottom[k]).normalized()
        across = along.cross(n).normalized() * radius * 0.08 * glow_scale
        pts = [bottom[k].lerp(top[k], t) + n * 0.002 for t in (0.0, 0.35, 0.7, 0.92)]
        for m in range(3):
            w0 = 1.0 - 0.25 * m; w1 = 1.0 - 0.25 * (m + 1)
            _face(bm, uv_layer, [pts[m] - across * w0, pts[m] + across * w0, pts[m + 1] + across * w1,
                                 pts[m + 1] - across * w1], [(0.25, 0.25)] * 4, 1)
    if seam:
        # root seam: a thin glowing band lying on the hide around the crystal's foot. hide_hit(origin, direction) ->
        # point or None finds the hide; each prism edge is followed down to where it enters the hide, and the band
        # reaches 0.22 r outward from there (a ring floating at the root height read as a flange or a cuff)
        foot, band = [], []
        for i in range(sides):
            d = (bottom[i] - top[i]).normalized()
            radial = (top[i] - (Vector(root) + z * shaft + lean))
            radial = (radial - z * radial.dot(z)).normalized()
            p = hide_hit(top[i], d) if hide_hit else None
            if p is not None and (p - top[i]).length > (top[i] - bottom[i]).length:
                p = None
            if p is None:
                p = Vector(root) + (top[i] - Vector(root) - z * shaft - lean) / taper
            q = hide_hit(p + radial * 0.22 * radius * glow_scale + z * 0.1, -z) if hide_hit else None
            if q is None or (q - p).length > 0.5 * radius:      # the ray found a leg or a lower plate: keep it short
                q = p + radial * 0.22 * radius * glow_scale - z * 0.02
            foot.append(p + radial * 0.003 + z * 0.004); band.append(q + z * 0.004)
        for i in range(sides):
            j = (i + 1) % sides
            _face(bm, uv_layer, [band[i], band[j], foot[j], foot[i]], [(0.25, 0.25)] * 4, 1)
