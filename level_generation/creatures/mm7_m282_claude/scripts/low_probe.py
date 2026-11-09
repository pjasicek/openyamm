"""Lowest evaluated vertices per piece for an action frame. Args: <blend> <action> <frame>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
act = bpy.data.actions[a[1]]; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[2]))
me = body.data; pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
for p in range(pv.max() + 1):
    ids = np.where(pv == p)[0]; i = ids[np.argmin(P[ids, 2])]
    if P[i, 2] < 0.01:
        g = sorted(((x.weight, body.vertex_groups[x.group].name) for x in me.vertices[i].groups), reverse=True)[:3]
        print('LOW piece', p, round(float(P[i, 2]), 3), [(n, round(w, 2)) for w, n in g])
