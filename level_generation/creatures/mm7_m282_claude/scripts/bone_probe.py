"""Print posed bone heads and axes (lat=X, up=Y, fwd=Z of the bone) for an action frame. Args: <blend> <action> <frame> <bones,...>"""
import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); rig = bpy.data.objects['Rig']
act = bpy.data.actions[a[1]]; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[2]))
for n in a[3].split(','):
    M = rig.matrix_world @ rig.pose.bones[n].matrix; R = M.to_3x3().normalized()
    print('BONE', n, 'head', tuple(round(x, 3) for x in M.translation), 'X', tuple(round(x, 2) for x in R.col[0]),
          'Y', tuple(round(x, 2) for x in R.col[1]), 'Z', tuple(round(x, 2) for x in R.col[2]))
