"""Print the Bow bone axes in world space (Y limbs, -Z string side, X plane normal) at given Attack frames.
Usage: blender -b -P bow_axes.py -- <master.blend> <frames,comma>"""
import bpy, sys
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0]); sc = bpy.context.scene; rig = bpy.data.objects['Rig']
rig.animation_data.action = bpy.data.actions['Attack']; rig.animation_data.action_slot = rig.animation_data.action.slots[0]
for f in (int(x) for x in args[1].split(',')):
    sc.frame_set(f); R = rig.pose.bones['Bow'].matrix.to_3x3().normalized()
    r = lambda v: [round(x, 2) for x in v]
    print('AXES', f, 'limbs', r(R.col[1]), 'string_side', r(-R.col[2]), 'normal', r(R.col[0]))
