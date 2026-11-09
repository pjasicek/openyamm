"""Per-frame numbers of a clip with the spear on the solved handle: pelvis/chest yaw (deg, 0 = facing -Y), trunk pitch,
spear pitch (+ up) and yaw (0 = forward), hand height, tip position (forward = -Y), tip speed (m/s at 30 fps keys).
Args: -- <blend> <action> [step]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, action = a[0], a[1]; step = float(a[2]) if len(a) > 2 else 1.0
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json')))
c = Vector(G['handle_centre_hand_local']); ax = Vector(G['handle_axis_hand_local']).normalized()
act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
f0, f1 = act.frame_range
fps = scene.render.fps / scene.render.fps_base
W = rig.matrix_world
def yaw(v):
    return math.degrees(math.atan2(v.x, -v.y))
prev = None; f = f0
print('PROBE', action, 'frames', f0, f1, 'fps', fps)
while f <= f1 + 1e-6:
    scene.frame_set(int(f), subframe=f - int(f))
    P = lambda n: W @ rig.pose.bones[n].matrix
    pel = P('B_Pelvis'); ch = P('B_Spine2')
    lp, rp = P('B_L_Thigh').translation, P('B_R_Thigh').translation
    pel_fwd = Vector((0, 0, 1)).cross(lp - rp).normalized()          # left-hip minus right-hip x up ... forward
    pel_fwd = -pel_fwd if pel_fwd.y > 0.9 else pel_fwd
    ls, rs = P('B_L_UpperArm').translation, P('B_R_UpperArm').translation
    ch_fwd = (ls - rs).cross(Vector((0, 0, 1))).normalized()
    trunk = (P('B_Neck').translation - pel.translation).normalized()
    H = P('B_R_Hand'); d = (H.to_3x3() @ ax).normalized(); g = H @ c; tip = g + d * 1.15
    sp = (tip - prev).length * fps / step if prev is not None else 0.0
    prev = tip.copy()
    print(f'F {f:5.1f} pelvis_yaw {yaw(pel_fwd):6.1f} chest_yaw {yaw(ch_fwd):6.1f} trunk_pitch {math.degrees(math.asin(max(-1, min(1, -trunk.y)))):5.1f}'
          f' spear_pitch {math.degrees(math.asin(max(-1,min(1,d.z)))):6.1f} spear_yaw {yaw(Vector((d.x, d.y, 0))):6.1f}'
          f' hand_z {g.z:5.2f} tip ({tip.x:5.2f},{-tip.y:5.2f},{tip.z:5.2f}) tip_speed {sp:5.1f} pelvis_z {pel.translation.z:4.2f}')
    f += step
