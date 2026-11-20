"""Debug: plate vertices inside the body at one clip frame, with the nearest body face's rest position and its
dominant bones. Args: -- <blend> <plate> <clip> <frame>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; pl = bpy.data.objects['Arm_' + a[1]]; sc = bpy.context.scene
me = body.data; GI = {g.index: g.name for g in body.vertex_groups}
def ev(ob):
    e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    co = np.array([ob.matrix_world @ v.co for v in m.vertices]); e.to_mesh_clear(); return co
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update(); B0 = ev(body); P0 = ev(pl)
act = bpy.data.actions[a[2]]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc.frame_set(int(a[3])); B = ev(body); P = ev(pl)
F = [tuple(p.vertices) for p in me.polygons]; t = BVHTree.FromPolygons(B.tolist(), F)
rows = []
for k, p in enumerate(P):
    loc, n, fi, d = t.find_nearest(Vector(p), 0.06)
    if loc is not None and (Vector(p) - loc).dot(n) < -0.5 * d:
        vi = F[fi][0]; v = me.vertices[vi]
        gs = sorted(((g.weight, GI[g.group]) for g in v.groups), reverse=True)[:3]
        rows.append((d, k, P0[k], B0[vi], gs))
for d, k, p0, b0, gs in sorted(rows, key=lambda r: -r[0])[:12]:
    print('INSIDE', round(d * 100, 2), 'plate rest', np.round(p0, 3).tolist(), 'body rest', np.round(b0, 3).tolist(), [(round(w, 2), n) for w, n in gs])
