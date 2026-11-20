"""Shrink the grafted hands' forearm stub inside the leather cuffs (mm9_markel, 2026-11-02). graft_hands.py conformed the
MPFB stub to the old cuff opening, and after cuff_trim.py/sleeve_tuck.py the stub surface still lay within a millimetre of
the cuff wall over its first centimetres, so the stub's toothed top edge showed through the cuff as red/skin wedges in
part views (review/wrist_R_r1.png) in bind and every clip. Per side, bind pose, axis = forearm joint -> hand joint (t from
the forearm joint, L at the hand joint): the cuff wall is the first body-face hit along the ray from the
axis through each stub vertex (hand face vertex at t < L + 0.005), more than 4 mm out; the vertex is pulled radially to at
most FRAC x that wall - 1 mm, fully from 5 mm
inside the cuff (t < L - 0.005), eased to nothing at L + 0.005. Positions only: weights, UVs and attributes unchanged.
Args: -- <in blend> <out blend> [frac 0.80]"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
FRAC = float(a[2]) if len(a) > 2 else 0.80
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world; mwi = mw.inverted()
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
hand = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hand)
head = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', head)
hv = np.zeros(len(CO), bool); bv = np.zeros(len(CO), bool)
for p in me.polygons:
    (hv if hand[p.index] else (bv if not head[p.index] else np.zeros(len(CO), bool)))[list(p.vertices)] = True
bv &= ~hv
rep = {}
for tok in ('L', 'R'):
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    L = np.linalg.norm(a1 - a0); ax = (a1 - a0) / L
    u = np.cross(ax, [0, 0, 1.0]); u /= np.linalg.norm(u); w_ = np.cross(ax, u)
    t = (CO - a0) @ ax
    rvec = CO - a0 - np.outer(t, ax); rad = np.linalg.norm(rvec, axis=1)
    ang = np.arctan2(rvec @ w_, rvec @ u)
    # the cuff wall along each stub vertex's own ray (axis -> vertex): the FIRST body-face hit more than 4 mm from the axis
    # (the old forearm skin Meshy left under the sleeve lies within 1-2 mm of it). The body is too sparse after reduction
    # for per-slice vertex radii (tried first: walls of 1.4 cm read from single vertices)
    from mathutils.bvhtree import BVHTree
    faces = [list(p.vertices) for p in me.polygons if not hand[p.index] and not head[p.index]
             and ((CO[list(p.vertices)] - a0) @ ax).max() > L - 0.2 and np.linalg.norm(np.cross(CO[list(p.vertices)].mean(0) - a0, ax)) < 0.1]
    bvh = BVHTree.FromPolygons([Vector(c) for c in CO], faces)
    stub = hv & (t < L + 0.005) & (t > L - 0.16) & (rad < 0.08)
    moved, mx, nohit = 0, 0.0, 0
    for i in np.where(stub)[0]:
        p0 = a0 + t[i] * ax; rd = rvec[i] / max(rad[i], 1e-6)
        start, hitd = Vector(p0 + rd * 0.004), None
        h = bvh.ray_cast(start, Vector(rd), 0.08)
        if h[0] is not None:
            hitd = (np.array(h[0]) - p0) @ rd
        if hitd is None:
            nohit += 1
            continue
        lim = FRAC * hitd - 0.001
        k = float(np.clip((L + 0.005 - t[i]) / 0.01, 0, 1))
        if rad[i] > lim and k > 0 and lim > 0.004:
            new = lim + (rad[i] - lim) * (1 - k)
            CO[i] = p0 + rd * new
            moved += 1; mx = max(mx, rad[i] - new)
    rep[tok] = {'stub_verts': int(stub.sum()), 'moved': moved, 'max_in_mm': round(mx * 1000, 1), 'no_hit': nohit}
for i in range(len(CO)):
    me.vertices[i].co = mwi @ Vector(CO[i])
me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('STUB_SHRINK', rep)
