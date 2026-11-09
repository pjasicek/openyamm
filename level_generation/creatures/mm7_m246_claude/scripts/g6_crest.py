"""G6 for the long rigid crest and the hair (m246): per clip and frame, crest (piece 1) and hair (piece 2) vertices
behind the body skin (garment 0 without head/neck-weighted skin; inside = behind the nearest face within a 45 deg cone,
6 cm search, the g6_contacts rule). Reports the deepest point per clip. Args: -- <blend> action [...]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
gi = {g.name: g.index for g in body.vertex_groups}
hw = np.array([sum(e.weight for e in v.groups if e.group in (gi['B_Head'], gi['B_Neck'])) for v in me.vertices])
keep = (gv == 0) & (hw < 0.3)
faces = [tuple(p.vertices) for p in me.polygons if all(keep[i] for i in p.vertices)]
for name, piece in (('crest', 1), ('hair', 2)):
    ids = np.where(pv == piece)[0][::2]
    for an in a[1:]:
        act = bpy.data.actions[an]; rig.animation_data.action = act
        if len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        worst = (0.0, None)
        for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
            bpy.context.scene.frame_set(f)
            ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
            P = [body.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear()
            t = BVHTree.FromPolygons(P, faces)
            for i in ids:
                loc, nrm, fi, d = t.find_nearest(P[i], 0.06)
                if loc is None:
                    continue
                v = P[i] - loc
                if v.dot(nrm) < 0 and v.length > 1e-6 and (-v).normalized().angle(nrm) < math.radians(45) and d > worst[0]:
                    worst = (d, f)
        print(f'CREST {name:5s} {an:9s} deepest {worst[0] * 100:.1f} cm at frame {worst[1]}')
