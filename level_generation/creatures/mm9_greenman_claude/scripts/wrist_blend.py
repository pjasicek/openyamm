"""Bare-arm wrist blend (mm9_greenman, 2026-11-04): the Green Man has no cuff. Where the body's trimmed forearm rim
(cuff_trim.py) meets the grafted MPFB stub the two surfaces crossed each other (a jagged seam, a flap and slits under
the wrist), and the rim stood as a step like a sleeve edge.
Per side, with the forearm axis (Forearm -> Hand joint) and radial rays from it:
1. body vertices within LEN before the rim: r' = r + ((r_stub + GAP) - r) * smoothstep(along) where r_stub is the stub
   surface's radius on the same ray (ray cast against the hand faces only); radii only shrink;
2. stub vertices more than 5 mm behind the rim that stand outside the body (ray cast against the body faces) move to
   GAP inside it, so behind the rim only the body shows and in front of it only the stub.
Positions only (UVs, weights, attributes unchanged). Args: <in blend> <out blend> [LEN 0.07] [GAP 0.0015]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
LEN = float(a[2]) if len(a) > 2 else 0.07
GAP = float(a[3]) if len(a) > 3 else 0.0015
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
hl = bm.faces.layers.int['hand']
hf = [f for f in bm.faces if f[hl]]; bf = [f for f in bm.faces if not f[hl]]
def bvh_of(faces):
    vs = sorted({v.index for f in faces for v in f.verts}); m = {i: k for k, i in enumerate(vs)}
    return BVHTree.FromPolygons([bm.verts[i].co.copy() for i in vs], [[m[v.index] for v in f.verts] for f in faces])
Bh, Bb = bvh_of(hf), bvh_of(bf)
handv = {v for f in hf for v in f.verts}
rep = {}
for tok, sx in (('L', -1), ('R', 1)):
    a0 = rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local
    a1 = rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local
    d = (a1 - a0).normalized()
    def polar(p):
        r = p - a1; al = r.dot(d); q = r - d * al
        return al, q
    rim = [polar(v.co)[0] for v in bm.verts if v.is_boundary and v not in handv and (v.co.x > 0) == (sx > 0)
           and abs(polar(v.co)[0]) < 0.08]
    a_rim = float(np.median(rim)) if rim else -0.02
    moved_b = moved_h = 0; maxb = maxh = 0.0
    for v in bm.verts:
        if (v.co.x > 0) != (sx > 0):
            continue
        al, q = polar(v.co); r = q.length
        if r < 1e-6 or r > 0.2:
            continue
        o = a1 + d * al; dirn = q / r
        if v not in handv and a_rim - LEN <= al <= a_rim + 0.003:
            hit = Bh.ray_cast(o, dirn, 0.3)
            if hit[0] is None:
                continue
            rs = (hit[0] - o).length
            t = min(1.0, max(0.0, (al - (a_rim - LEN)) / LEN)); s = t * t * (3 - 2 * t)
            tr = rs + GAP
            if tr < r:
                nr = r + (tr - r) * s; v.co = o + dirn * nr; moved_b += 1; maxb = max(maxb, r - nr)
        elif v in handv and al < a_rim - 0.005 and al > a_rim - 0.3:
            hit = Bb.ray_cast(o, dirn, 0.3)
            if hit[0] is None:
                continue
            rb = (hit[0] - o).length
            if r > rb - GAP:
                v.co = o + dirn * (rb - GAP); moved_h += 1; maxh = max(maxh, r - (rb - GAP))
    rep[tok] = {'rim_along': round(a_rim, 4), 'body_moved': moved_b, 'body_max_shrink_cm': round(maxb * 100, 2),
                'stub_tucked': moved_h, 'stub_max_cm': round(maxh * 100, 2)}
bm.to_mesh(me); me.update()
print('WRIST', rep)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
