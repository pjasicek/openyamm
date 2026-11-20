"""Standing height of the posed skinned mesh (Standing frame 0; the quiver fletchings excluded, as the native sprite's
height is measured to the top of the hair) for the actors.yml scale. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
act = bpy.data.actions['Standing']; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(0)
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear()
quiver = pv >= 1000                                              # m218: only the spear is excluded (the native height includes the leaf crown)
print('HEIGHT standing (hair top)', round(float(z[~quiver].max() - z.min()), 4), 'with fletchings', round(float(z.max() - z.min()), 4))
