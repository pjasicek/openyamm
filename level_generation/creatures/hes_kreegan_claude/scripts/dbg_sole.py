import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
GI = {g.index: g.name for g in body.vertex_groups}
DOM = [GI[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices]
act = bpy.data.actions[a[1]]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
    sc.frame_set(f); e = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    z = np.array([v.co.z for v in m.vertices]); e.to_mesh_clear(); i = int(np.argmin(z))
    pel = (rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).translation.z
    print('DBGSOLE', f, round(z[i] * 100, 1), DOM[i], 'pelvis z', round(pel, 3))
