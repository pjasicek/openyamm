"""Spear bone world frame and the spear mesh's lowest point at action frames. Args: -- <blend> <action> <frame> [...]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
act = bpy.data.actions[a[1]]; rig.animation_data_create(); rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
for f in a[2:]:
    bpy.context.scene.frame_set(int(float(f)), subframe=float(f) % 1)
    M = rig.matrix_world @ rig.pose.bones['Spear'].matrix
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
    sp = P[pv >= 1000]
    print('PROP', f, 'origin', [round(x, 3) for x in M.translation], 'axis', [round(x, 2) for x in M.col[1].xyz],
          'up', [round(x, 2) for x in M.col[2].xyz], 'mesh z', round(float(sp[:, 2].min()), 3), round(float(sp[:, 2].max()), 3))
