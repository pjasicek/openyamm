"""Lowest/highest points of Body and Wings at the last Death frame (and the pelvis height). Args: -- <blend>"""
import bpy, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
a = bpy.data.actions['Death']; rig.animation_data_create(); rig.animation_data.action = a
if getattr(a, 'slots', None) is not None and len(a.slots):
    rig.animation_data.action_slot = a.slots[0]
deps = bpy.context.evaluated_depsgraph_get()
for f in (int(a.frame_range[1]) - 20, int(a.frame_range[1])):
    sc.frame_set(f); deps.update()
    for n in ('Body', 'Wings'):
        if n not in bpy.data.objects:
            continue
        ob = bpy.data.objects[n]; ev = ob.evaluated_get(deps); m = ev.to_mesh()
        z = np.array([(ob.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear()
        if n == 'Body':
            pc = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pc)
            low = np.argsort(z)[:40]
            print('CORPSE lowest pieces', sorted(set(pc[low].tolist())), 'piece 0 min', round(float(z[pc == 0].min()), 3))
        print('CORPSE frame', f, n, 'z min', round(float(z.min()), 3), 'p5', round(float(np.percentile(z, 5)), 3), 'max', round(float(z.max()), 3))
    print('CORPSE pelvis z', round((rig.matrix_world @ rig.pose.bones['B_Pelvis'].head).z, 3))
