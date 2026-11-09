import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
arm = bpy.data.objects['Thief_Rig']; mesh = bpy.data.objects['Thief']; me = mesh.data
act = bpy.data.actions['Walking']; arm.animation_data.action = act; arm.animation_data.action_slot = act.slots[0]
PARTS = json.loads(bpy.context.scene['thf_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
cl = PARTS.index('Cloak'); legp = {PARTS.index('Legs'), PARTS.index('Boot')}
cfaces = [p for p in me.polygons if part[p.index] == cl]
lverts = sorted({v for p in me.polygons if part[p.index] in legp for v in p.vertices})
CH = json.loads(bpy.context.scene['thf_cloak'])
sc = bpy.context.scene; sc.frame_set(8)
ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = [mesh.matrix_world @ v.co for v in m.vertices]
tree = BVHTree.FromPolygons(P, [tuple(p.vertices) for p in cfaces])
hips = arm.matrix_world @ arm.pose.bones['Hips'].head
print('HIPS', tuple(round(x, 3) for x in hips))
for b in ('LeftUpLeg', 'LeftLeg', 'LeftFoot', 'RightUpLeg', 'RightLeg', 'RightFoot'):
    print('BONE', b, tuple(round(x, 3) for x in arm.matrix_world @ arm.pose.bones[b].head))
bad = []
for i in lverts:
    p = P[i]
    if p.y < hips.y + 0.02 or p.z < 0.14 or p.z > 0.9: continue
    if tree.ray_cast(p + Vector((0, 1e-4, 0)), Vector((0, 1, 0)), 1.0)[0] is None:
        bad.append(p)
B = np.array([tuple(p) for p in bad]); print('BAD n', len(B), 'x', B[:, 0].min().round(3), B[:, 0].max().round(3), 'y', B[:, 1].min().round(3), B[:, 1].max().round(3), 'z', B[:, 2].min().round(3), B[:, 2].max().round(3))
for c in CH:
    if abs(c['deg']) > 45: continue
    pts = []
    for k, b in enumerate(c['bones']):
        pb = arm.pose.bones[b]; pts.append(tuple(round(x, 3) for x in arm.matrix_world @ pb.tail))
    print('CHAIN', c['deg'], 'tails', pts, 'rest', [tuple(round(x, 3) for x in p) for p in c['pts'][1:]])
# cloak verts near the poke, and their weights
G = {g.index: g.name for g in mesh.vertex_groups}
cv = sorted({v for p in cfaces for v in p.vertices})
c0 = Vector(B.mean(0))
near = sorted(cv, key=lambda i: (Vector((P[i].x, 0, P[i].z)) - Vector((c0.x, 0, c0.z))).length)[:6]
for i in near:
    print('CV', i, tuple(round(x, 3) for x in P[i]), 'rest', tuple(round(x, 3) for x in me.vertices[i].co),
          sorted(((round(g.weight, 2), G[g.group]) for g in me.vertices[i].groups), reverse=True)[:4])
