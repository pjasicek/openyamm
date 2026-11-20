"""Posed mesh bounds (min/max z, x span) of the body at the given action:frame entries, for the actors.yml scale.
Args: -- <blend> action:frame [...]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
for item in a[1:]:
    n, f = item.split(':')
    act = bpy.data.actions[n]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(f)); deps = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(deps); m = ev.to_mesh(); co = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
    print('POSEH', item, 'z', round(float(co[:, 2].min()), 3), round(float(co[:, 2].max()), 3), 'height', round(float(np.ptp(co[:, 2])), 3), 'x span', round(float(np.ptp(co[:, 0])), 3))
