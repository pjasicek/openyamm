import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; pl = bpy.data.objects[a[1]]; sc = bpy.context.scene
if a[2] == 'REST':
    rig.animation_data.action = None
    for pb in rig.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
else:
    act = bpy.data.actions[a[2]]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]; sc.frame_set(int(a[3]))
def ev(ob):
    e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    co = np.array([tuple(ob.matrix_world @ v.co) for v in m.vertices]); e.to_mesh_clear(); return co
B = ev(body); P = ev(pl)
uvd = pl.data.uv_layers[0].data; DK = 1 - 12 / 1024
inner = [tuple(p.vertices) for p in pl.data.polygons if p.material_index == 0 and all(abs(uvd[li].uv[0] - DK) < 1e-3 for li in p.loop_indices)]
t = BVHTree.FromPolygons(P.tolist(), inner)
GI = {g.index: g.name for g in body.vertex_groups}
res = []
for i, p in enumerate(B):
    loc, n, fi, d = t.find_nearest(Vector(p), 0.03)
    if loc is None: continue
    v = Vector(p) - loc
    if v.dot(n) < -0.9 * v.length and not any(GI[g.group] in ('Bone_041', 'Bone_036') and g.weight > 0.05 for g in body.data.vertices[i].groups): res.append((d, i))
res.sort(reverse=True)
for d, i in res[:8]:
    w = sorted(((g.weight, GI[g.group]) for g in body.data.vertices[i].groups), reverse=True)[:3]
    print('DBGV', round(d * 100, 2), i, [round(x, 3) for x in B[i]], [(n, round(x, 2)) for x, n in w])
print('DBGV count', len(res))
