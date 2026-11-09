"""Hold the shield arm in its Standing guard on candidate clips: every left clavicle/arm/hand/finger bone takes
Standing frame 0's local pose (so the shield follows the chest, like the accepted clips). Saves in place.
Usage: blender -b -P lock_left_arm.py -- <blend> <action> [...]"""
import os, sys, bpy
a = sys.argv[sys.argv.index('--') + 1:]
blend, acts = a[0], a[1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
LEFT = [b.name for b in rig.data.bones if b.name.startswith('B_L_') and not any(t in b.name for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]


def use(act):
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


use(bpy.data.actions['Standing']); sc.frame_set(0)
hold = {n: rig.pose.bones[n].matrix_basis.copy() for n in LEFT}
for an in acts:
    act = bpy.data.actions[an]; use(act)
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for n in LEFT:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.matrix_basis = hold[n]
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print('LOCKED', an, f1 - f0 + 1, 'frames', len(LEFT), 'bones')
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
