"""Skirt/coat faces turned inside out by the pose: per clip frame, faces of the given garments whose posed normal
points INTO the body (against the horizontal direction from the pelvis axis) while their rest normal pointed out,
plus which bones dominate them. Also leg/trouser vertices in front of the coat (outward pelvis ray meets no coat).
Args: -- <blend> <action> <frame> [garments, default 1,2]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
GAR = [int(x) for x in (a[3] if len(a) > 3 else '1,2').split(',')]
gv = np.array([x.value for x in me.attributes['garment'].data])
rest = np.array([v.co[:] for v in me.vertices])
faces = [p for p in me.polygons if all(gv[i] in GAR for i in p.vertices)]
def normals(P):
    out = []
    for p in faces:
        v = P[list(p.vertices)]; n = np.cross(v[1] - v[0], v[2] - v[0]); out.append(n / (np.linalg.norm(n) + 1e-12))
    return np.array(out)
pel0 = np.array(rig.data.bones['B_Pelvis'].head_local)
C0 = np.array([rest[list(p.vertices)].mean(0) for p in faces])
o0 = C0 - pel0; o0[:, 2] = 0; o0 /= np.linalg.norm(o0, axis=1)[:, None] + 1e-9
N0 = normals(rest); out0 = (N0 * o0).sum(1) > 0.2
act = bpy.data.actions[a[1]]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(float(a[2])))
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = np.array([(body.matrix_world @ v.co)[:] for v in m.vertices]); ev.to_mesh_clear()
pel = np.array((rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).translation)
C = np.array([P[list(p.vertices)].mean(0) for p in faces]); o = C - pel; o[:, 2] = 0; o /= np.linalg.norm(o, axis=1)[:, None] + 1e-9
N = normals(P); inv = out0 & ((N * o).sum(1) < -0.2)
names = {g.index: g.name for g in body.vertex_groups}
doms = {}
for k in np.where(inv)[0]:
    v = faces[k].vertices[0]; g = max(me.vertices[v].groups, key=lambda e: e.weight)
    doms[names[g.group]] = doms.get(names[g.group], 0) + 1
print('FLIP', a[1], a[2], 'faces', len(faces), 'inverted', int(inv.sum()), 'rest z', np.round(np.percentile(C0[inv, 2], [5, 50, 95]), 2).tolist() if inv.any() else None, 'bones', dict(sorted(doms.items(), key=lambda kv: -kv[1])[:6]))
# trousers in front of the coat
T = BVHTree.FromPolygons([tuple(x) for x in P], [tuple(p.vertices) for p in faces])
leg = np.where(gv == 15)[0]; front = 0; deep = 0.0
for i in leg:
    p = Vector(P[i]); d = Vector((P[i][0] - pel[0], P[i][1] - pel[1], 0))
    if d.length < 1e-4 or P[i][2] < 0.35: continue
    d.normalize()
    if T.ray_cast(p + d * 1e-4, d, 0.4)[0] is None:
        h = T.ray_cast(p, -d, 0.4)
        if h[0] is not None and h[3] < 0.1:
            front += 1; deep = max(deep, h[3])
print('LEGOUT', a[1], a[2], 'leg verts outside the coat', front, 'max cm', round(deep * 100, 1))
