"""Texel map for the right wrist (head = 4, mirror_armhead.py; 2026-10-30 rework): every HeadUV texel of those faces
takes the texel of the left arm's surface point nearest to its mirror image (x -> -x), bind pose: on the left arm head
(head = 2, its HeadUV texel in the arm-head retexture) or on the left forearm (head = 0 within 0.6 m of the left wrist,
its UVMap texel in the body retexture), since most of that wrist mirrors onto the left forearm, not the head. For
the normal map a 3x3 matrix per texel carries a tangent-space normal from the left face's frame through the mirror into
the right face's frame (glTF convention, +v up; compose_v2.py converts Meshy's +y-down maps around it).
Args: <blend> <out npz> [size]. Writes: dst (texel row, col), src_uv (u, v), src_head (1 head retexture, 0 body retexture), M (3x3), dist (m)."""
import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
N = int(a[2]) if len(a) > 2 else 2048
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
head = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', head)
CO = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
uvl = me.uv_layers['HeadUV'].data
uvb = me.uv_layers['UVMap'].data
piece = np.zeros(len(me.vertices), np.int32)
me.attributes['piece'].data.foreach_get('value', piece)
WL = np.array(rig.matrix_world @ rig.data.bones['Xawrist01'].head_local)
SRC = [p for p in me.polygons if head[p.index] == 2 or
       (head[p.index] == 0 and piece[list(p.vertices)].max() == 0 and np.linalg.norm(CO[list(p.vertices)] - WL, axis=1).max() < 0.6)]
DST = [p for p in me.polygons if head[p.index] == 4]


def tri(p):
    layer = uvl if head[p.index] > 0 else uvb
    return CO[list(p.vertices)], np.array([layer[li].uv[:] for li in p.loop_indices])


def frame(P, U):
    """Rows: tangent (+u), bitangent (+v), normal."""
    e1, e2 = P[1] - P[0], P[2] - P[0]
    d1, d2 = U[1] - U[0], U[2] - U[0]
    r = d1[0] * d2[1] - d2[0] * d1[1]
    n = np.cross(e1, e2); n /= np.linalg.norm(n) + 1e-12
    if abs(r) < 1e-14:
        t = e1 / (np.linalg.norm(e1) + 1e-12); sign = 1.0
    else:
        t = (e1 * d2[1] - e2 * d1[1]) / r
        b = (e2 * d1[0] - e1 * d2[0]) / r
        sign = 1.0 if np.cross(n, t) @ b >= 0 else -1.0
    t = t - n * (t @ n); t /= np.linalg.norm(t) + 1e-12
    return np.stack([t, np.cross(n, t) * sign, n])


src_tris = [tri(p) for p in SRC]
# two lookups: mirror points behind the left head's base ring (along the left forearm axis) take the forearm's
# texels, the others the head's (one nearest-point lookup over both pulled the band's texels onto the head's rim and
# striped them)
AXL = WL - np.array(rig.matrix_world @ rig.data.bones['Xarmmid01'].head_local); AXL /= np.linalg.norm(AXL)
ring = [v for p in SRC if head[p.index] == 2 for v in p.vertices]
ring_ax = np.median((CO[ring] - WL) @ AXL) if ring else 0.0
edges = {}
for p in SRC:
    if head[p.index] == 2:
        for k in range(len(p.vertices)):
            e = tuple(sorted((p.vertices[k], p.vertices[(k + 1) % len(p.vertices)])))
            edges[e] = edges.get(e, 0) + 1
bverts = {i for e, n in edges.items() if n == 1 for i in e if piece[i] == 0}
BASE_AX = float(np.median((CO[list(bverts)] - WL) @ AXL)) if bverts else 0.0
groups = {k: [i for i, p in enumerate(SRC) if (head[p.index] == 2) == bool(k)] for k in (0, 1)}
bvhs = {k: BVHTree.FromPolygons([tuple(c) for c in CO], [tuple(SRC[i].vertices) for i in g]) for k, g in groups.items()}
src_frames = [frame(P, U) for P, U in src_tris]
MIR = np.diag([-1.0, 1.0, 1.0])
dst, suv, mats, dist, shead = [], [], [], [], []
for p in DST:
    P, U = tri(p)
    fr = frame(P, U)
    px = U * N
    x0, y0 = np.floor(px.min(0)).astype(int); x1, y1 = np.ceil(px.max(0)).astype(int)
    gx, gy = np.meshgrid(np.arange(max(x0, 0), min(x1, N)) + 0.5, np.arange(max(y0, 0), min(y1, N)) + 0.5)
    a_, b_, c_ = px
    den = (b_[1] - c_[1]) * (a_[0] - c_[0]) + (c_[0] - b_[0]) * (a_[1] - c_[1])
    if abs(den) < 1e-12 or gx.size == 0:
        continue
    l1 = ((b_[1] - c_[1]) * (gx - c_[0]) + (c_[0] - b_[0]) * (gy - c_[1])) / den
    l2 = ((c_[1] - a_[1]) * (gx - c_[0]) + (a_[0] - c_[0]) * (gy - c_[1])) / den
    l3 = 1 - l1 - l2
    ins = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
    for x, y, w1, w2, w3 in zip(gx[ins], gy[ins], l1[ins], l2[ins], l3[ins]):
        q = w1 * P[0] + w2 * P[1] + w3 * P[2]
        m = np.array((-q[0], q[1], q[2]))
        k = int((m - WL) @ AXL >= BASE_AX)
        loc, _, fj, d = bvhs[k].find_nearest(Vector(m.tolist()))
        fi = groups[k][fj]
        SP, SU = src_tris[fi]
        v0, v1, v2 = SP[1] - SP[0], SP[2] - SP[0], np.array(loc) - SP[0]
        d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
        dd = d00 * d11 - d01 * d01
        s1 = (d11 * d20 - d01 * d21) / dd if abs(dd) > 1e-16 else 1 / 3
        s2 = (d00 * d21 - d01 * d20) / dd if abs(dd) > 1e-16 else 1 / 3
        bc = np.clip([1 - s1 - s2, s1, s2], 0, 1); bc /= bc.sum()
        dst.append((N - 1 - int(y), int(x)))
        suv.append(bc @ SU)
        mats.append(fr @ MIR @ src_frames[fi].T)
        dist.append(d)
        shead.append(int(head[SRC[fi].index] > 0))
np.savez(OUT, dst=np.array(dst, np.int32), src_uv=np.array(suv, np.float32), M=np.array(mats, np.float32),
         dist=np.array(dist, np.float32), src_head=np.array(shead, np.int8), size=N)
print('MIRRORMAP base ring axial', round(BASE_AX, 4), len(dst), 'texels from', len(SRC), 'to', len(DST), 'faces; from the head', int(np.sum(shead)),
      '; mirror distance median',
      round(float(np.median(dist)), 4) if dist else None, 'p90', round(float(np.percentile(dist, 90)), 4) if dist else None)
