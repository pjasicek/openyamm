"""Carry arm of a locomotion clip taken from the idle (user review 2026-10-20: in the walk the carrying elbow tucked
against the torso and the hand moved in front of the thigh, while the idle holds the arm out beside the body). Per frame
of the target action, the carrying arm takes one frame of the source action: the clavicle its local turn, the upper
arm, forearm and hand their WORLD orientation (the local channels alone kept the walk's chest posture and left the hand
in front of the thigh), so the arm hangs beside the body as in the idle; then the upper arm swings about the world
lateral axis through the shoulder by SWING degrees, in phase opposite to the OTHER arm's own forward swing in the
target clip (that arm keeps the clip's motion, so the timing stays matched to the legs). Writes the action in place.
Args: -- <in blend> <out blend> <source action>:<frame> <target action>:<swing deg> ...   (env SIDE=L|R)"""
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
src, out, ref, items = a[0], a[1], a[2], a[3:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
S = os.environ.get('SIDE', 'L'); O = 'R' if S == 'L' else 'L'
ARM = [f'B_{S}_Clavicle', f'B_{S}_UpperArm', f'B_{S}_Forearm', f'B_{S}_Hand']


def set_act(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


ra, rf = ref.split(':'); set_act(bpy.data.actions[ra]); sc.frame_set(int(rf))
HOLD = {n: rig.pose.bones[n].matrix_basis.copy() for n in ARM}
HOLDW = {n: armik.W(rig, n).to_3x3().normalized() for n in ARM}   # world orientation (both clips face -Y in place)
for item in items:
    name, swing = item.split(':'); swing = math.radians(float(swing))
    act = bpy.data.actions[name]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    set_act(act)
    fwd = []                                                       # the other hand's forward offset from the chest
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        C = armik.W(rig, 'B_Spine2').translation; h = armik.W(rig, f'B_{O}_Hand').translation
        fwd.append(-(h - C).y)                                     # character faces -Y
    fwd = np.array(fwd); mid = 0.5 * (fwd.max() + fwd.min()); half = max(0.5 * (fwd.max() - fwd.min()), 1e-6)
    phase = -(fwd - mid) / half                                    # this arm swings opposite to the other
    poses = []
    for i, f in enumerate(range(f0, f1 + 1)):
        set_act(act); sc.frame_set(f)
        snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
        set_act(None)
        for pb in rig.pose.bones:
            pb.matrix_basis = snap[pb.name]
        rig.pose.bones[ARM[0]].matrix_basis = HOLD[ARM[0]].copy()
        bpy.context.view_layer.update()
        for n in ARM[1:]:                                          # upper arm, forearm, hand: the idle's world turn
            M = HOLDW[n].to_4x4(); M.translation = armik.W(rig, n).translation; armik.set_world(rig, n, M)
            bpy.context.view_layer.update()
        U = armik.W(rig, f'B_{S}_UpperArm'); sh = U.translation.copy()
        hand = armik.W(rig, f'B_{S}_Hand').translation - sh
        ang = swing * phase[i]
        R = Matrix.Rotation(ang, 4, Vector((1, 0, 0)))
        if (R @ hand).y > hand.y and ang > 0 or (R @ hand).y < hand.y and ang < 0:
            R = Matrix.Rotation(-ang, 4, Vector((1, 0, 0)))        # + phase = hand forward (-Y)
        M = R @ U; M.translation = sh; armik.set_world(rig, f'B_{S}_UpperArm', M)
        bpy.context.view_layer.update()
        poses.append({n: rig.pose.bones[n].matrix_basis.to_quaternion() for n in ARM})
    set_act(act)
    for i, f in enumerate(range(f0, f1 + 1)):
        for n in ARM:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            q = poses[i][n]
            if i and q.dot(poses[i - 1][n]) < 0:
                q = -q; poses[i][n] = q
            pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    set_act(None)
    print(f'ARMHOLD {name} {S}: arm from {ref}, swing +-{math.degrees(swing):.0f} deg against {O} (its forward '
          f'range {(fwd.max() - fwd.min()) * 100:.0f} cm), frames {f1 - f0 + 1}')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
