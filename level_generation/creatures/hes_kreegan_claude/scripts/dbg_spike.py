import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
print('DBGS parent of Bone_041', rig.data.bones['Bone_041'].parent.name, 'pauldron parent', rig.data.bones['B_L_Pauldron'].parent.name)
for nm in (None, 'Walking'):
    rig.animation_data.action = bpy.data.actions[nm] if nm else None
    if nm: rig.animation_data.action_slot = bpy.data.actions[nm].slots[0]
    else:
        for pb in rig.pose.bones: pb.matrix_basis.identity()
    sc.frame_set(20); bpy.context.view_layer.update()
    e = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    p = m.vertices[9840].co.copy(); e.to_mesh_clear()
    Mp = rig.pose.bones['B_L_Pauldron'].matrix; Ms = rig.pose.bones['Bone_041'].matrix
    print('DBGS', nm, 'in pauldron space', [round(x, 4) for x in Mp.inverted() @ p], 'spike bone basis', [round(x, 3) for x in rig.pose.bones['Bone_041'].matrix_basis.to_quaternion()])
ob = bpy.data.objects['Arm_pauldron_L']; print('DBGS plate groups', [g.name for g in ob.vertex_groups], [m.type for m in ob.modifiers])
