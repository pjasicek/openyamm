"""Compare the bow arm (LArm, LForeArm, LHand, Bow armature-space matrices) between clip frames.
Usage: blender -b -P hold_match.py -- <blend> <action:frame> <action:frame> [...]"""
import bpy, sys, math
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); sc = bpy.context.scene; rig = bpy.data.objects['Rig']; pb = rig.pose.bones
poses = []
for spec in a[1:]:
    act, f = spec.split(':'); rig.animation_data.action = bpy.data.actions[act]
    rig.animation_data.action_slot = rig.animation_data.action.slots[0]; sc.frame_set(int(f))
    poses.append((spec, {n: pb[n].matrix.copy() for n in ('LArm', 'LForeArm', 'LHand', 'Bow')}))
ref = poses[0]
for spec, p in poses[1:]:
    print('MATCH', ref[0], 'vs', spec, {n: (round(math.degrees(ref[1][n].to_quaternion().rotation_difference(p[n].to_quaternion()).angle), 2),
                                         round((ref[1][n].translation - p[n].translation).length * 1000, 2)) for n in p})
