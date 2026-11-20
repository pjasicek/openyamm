"""Right-wrist bend (swing of the hand off the forearm axis, twist removed) and twist per frame, deg.
Args: -- <blend> action [action ...]"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
fb, hb = rig.data.bones['B_R_Forearm'], rig.data.bones['B_R_Hand']
seg = (fb.matrix_local.inverted() @ hb.head_local).normalized()
rest_rel = (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion()
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    out = []
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        sc.frame_set(f)
        rel = (rig.pose.bones['B_R_Forearm'].matrix.inverted() @ rig.pose.bones['B_R_Hand'].matrix).to_quaternion() @ rest_rel.inverted()
        swing, twist = rel.to_swing_twist('Y') if False else (None, None)
        v = rel @ seg; bend = math.degrees(seg.angle(v))
        out.append(round(bend))
    print('WRIST', an, 'max bend', max(out), 'per frame', out)
