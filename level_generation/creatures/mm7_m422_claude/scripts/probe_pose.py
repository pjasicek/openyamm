"""Print world joint positions of chosen bones at chosen frames of one action. Args: -- <blend> <action> <frame,...> <bone> [...]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; act = bpy.data.actions[a[1]]
rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
for f in [int(x) for x in a[2].split(',')]:
    bpy.context.scene.frame_set(f)
    print('PROBE', a[1], f, ' '.join(f"{b}=({', '.join(f'{c:.3f}' for c in (rig.matrix_world @ rig.pose.bones[b].head))})" for b in a[3:]))
