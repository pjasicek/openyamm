"""G6 for the skirt: thigh/hip skin (pieces 0-2, weighted to a thigh) that ends up in FRONT of a strip it sits behind
at rest, i.e. pokes through the strip. Per action and strip piece: the deepest skin point beyond the strip surface
(behind-the-face rule inverted: skin vertex on the outer side of the closest strip face within a 45 deg cone, while at
rest it was on the inner side). Args: -- <blend> action [...]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
STRIPS = [44,200,201,202]
gi = {g.name: g.index for g in body.vertex_groups}
thw = np.array([sum(e.weight for e in v.groups if e.group in (gi['B_L_Thigh'], gi['B_R_Thigh'])) for v in me.vertices])
rest = np.array([tuple(v.co) for v in me.vertices])
skin = np.where((pv==6) & (thw > 0.3) & (rest[:, 2] > 0.74) & (rest[:, 2] < 0.95))[0]
sp = [p for p in me.polygons if pv[p.vertices[0]] in STRIPS]


def inside(co):
    t = BVHTree.FromPolygons([tuple(c) for c in co], [tuple(p.vertices) for p in sp])
    side = {}
    for i in skin:
        loc, nrm, fi, d = t.find_nearest(Vector(co[i]), 0.05)
        if loc is not None:
            v = Vector(co[i]) - loc
            side[i] = (v.dot(nrm) > 0 and v.length > 1e-6 and v.normalized().angle(nrm) < math.radians(45), d,
                       int(pv[sp[fi].vertices[0]]))
    return side


r0 = inside(rest)
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    worst = (0.0, None, None)
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
        for i, (out, d, piece) in inside(P).items():
            if out and i in r0 and not r0[i][0] and d > worst[0]:
                worst = (d, f, piece, i, rest[i].tolist(), P[i].tolist())
    print('SKIRT DETAIL',an,worst)
    print(f'SKIRTPOKE {an:9s} deepest thigh skin through a strip {worst[0] * 100:.1f} cm at frame {worst[1]} (strip {worst[2]})')
