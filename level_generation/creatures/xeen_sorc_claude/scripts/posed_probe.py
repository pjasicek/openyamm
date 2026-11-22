"""Vertices near a posed point at action:frame: index, piece, garment, rest position, posed position, top weights.
Args: -- <blend> <action> <frame> x y z [radius]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; names = [g.name for g in body.vertex_groups]
act = bpy.data.actions[a[1]]; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[2]))
p = np.array([float(x) for x in a[3:6]]); r = float(a[6]) if len(a) > 6 else 0.03
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
idx = np.where(np.linalg.norm(P - p, axis=1) < r)[0]
by = {}
for i in idx:
    top = sorted(((e.weight, names[e.group]) for e in me.vertices[i].groups), reverse=True)[:2]
    k = (int(pv[i]), top[0][1]); by[k] = by.get(k, 0) + 1
for i in idx[:6]:
    print('POSEDV', int(i), 'rest', [round(x, 3) for x in me.vertices[i].co], 'posed', [round(float(x), 3) for x in P[i]], sorted(((round(e.weight, 2), names[e.group]) for e in me.vertices[i].groups), reverse=True)[:3])
print('POSED near', p.tolist(), 'count', len(idx), 'by (piece, top bone)', by)
