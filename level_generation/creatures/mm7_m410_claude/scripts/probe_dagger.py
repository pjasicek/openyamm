"""Print the Dagger bone's world origin and axis (+Y) at frames of actions. Args: -- <blend> action:frame [...]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); rig = bpy.data.objects['Rig']; sc = bpy.context.scene
for it in a[1:]:
    an, f = it.split(':'); act = bpy.data.actions[an]
    rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    f = float(f); sc.frame_set(int(f), subframe=f - int(f))
    M = rig.matrix_world @ rig.pose.bones['Dagger'].matrix
    P = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
    print('DPROBE', it, 'origin', [round(x, 3) for x in M.translation], 'axis', [round(x, 3) for x in M.col[1].xyz.normalized()],
          'pelvis-local axis', [round(x, 3) for x in (P.to_3x3().inverted() @ M.col[1].xyz).normalized()])
