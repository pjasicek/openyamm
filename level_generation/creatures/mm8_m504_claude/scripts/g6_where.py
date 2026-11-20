"""Which body region the forearms/hands enter: per frame and side, the deepest inside sample (closed shell inside
test as in g6_contacts.py, own arm excluded) and the dominant bone of the face it lies under.
Args: -- <blend> <action> [frame step]"""
import bpy, sys, os
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); an = a[1]; step = float(a[2]) if len(a) > 2 else 1.0
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
act = bpy.data.actions[an]; rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
names = [g.name for g in body.vertex_groups]; nv = len(me.vertices)
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups: Wt[v.index, e.group] = e.weight
dom = np.array(names)[Wt.argmax(1)]
def side(s, keys): return Wt[:, [i for i, n in enumerate(names) if n.startswith(f'B_{s}_') and any(k in n for k in keys)]].sum(1)
faces = [tuple(p.vertices) for p in me.polygons]
f = 0.0
while f <= act.frame_range[1]:
    sc.frame_set(int(f), subframe=f - int(f))
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = [body.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear()
    out = []
    for s in 'LR':
        arm_all = side(s, ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) > 0.2
        samp = np.where(side(s, ('Forearm', 'Hand', 'Finger')) > 0.5)[0]
        fl = [fc for fc in faces if not any(arm_all[i] for i in fc)]
        bvh = BVHTree.FromPolygons(co, fl)
        best = (0.0, None)
        for i in samp:
            loc, nrm, idx, d = bvh.find_nearest(co[i], 0.2)
            if loc is None: continue
            if (co[i] - loc).dot(nrm) < -0.7 * d and d > best[0]:
                best = (d, dom[fl[idx][0]])
        out.append(f'{s} {100*best[0]:5.1f} {best[1]}')
    print('WHERE', f, ' | '.join(out))
    f += step
