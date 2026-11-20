"""Fidget for the Moon Cleric, authored on Standing (native m170 fa-fd: both claws come together in front of the chest,
the collar glows, then they part again; no library clip does this upright).
Fidget = a copy of Standing (its breathing kept); weight w(t) smoothsteps in over IN, holds, smoothsteps out over OUT.
Both wrists move (armik.solve, minimal change) toward targets in the chest frame: FWD in front of the chest, DOWN below
the chest joint, SIDE apart; the elbows bend toward an outward-down-back pole; each hand aims its finger axis
(wrist -> middle knuckle) up-forward-inward with the least wrist bend (armik.hand_for_axis). The head bows HEAD_BOW deg
and the chest leans CHEST_LEAN deg during the hold. Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
src, out = a[0], a[1]
IN, HOLD_END, OUT = (3, 21), 40, 18          # frames at 30 fps
FWD, DOWN, SIDE = 0.24, 0.10, 0.055
HEAD_BOW, CHEST_LEAN = 9.0, 3.0
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']; AW = rig.matrix_world
st = bpy.data.actions['Standing']
if 'Fidget' in bpy.data.actions:
    bpy.data.actions.remove(bpy.data.actions['Fidget'])
act = st.copy(); act.name = 'Fidget'; act.use_fake_user = True
rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
f0, f1 = (int(round(x)) for x in act.frame_range)


def sstep(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def weight(f):
    if f < IN[1]:
        return sstep((f - IN[0]) / (IN[1] - IN[0]))
    if f <= HOLD_END:
        return 1.0
    return 1.0 - sstep((f - HOLD_END) / OUT)


AX = {}
for s in ('L', 'R'):
    h = rig.data.bones[f'B_{s}_Hand']; m = rig.data.bones[f'B_{s}_Finger2']
    AX[s] = (h.matrix_local.to_3x3().inverted() @ (m.head_local - h.head_local)).normalized()
ARM = [f'B_{s}_{b}' for s in ('L', 'R') for b in ('UpperArm', 'Forearm', 'Hand')]
prev = {'L': None, 'R': None}
for f in range(f0, f1 + 1):
    scene.frame_set(f)
    w = weight(f)
    if w <= 0:
        continue
    for n, ang in (('B_Spine2', CHEST_LEAN), ('B_Head', HEAD_BOW)):
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        Mw = AW @ pb.matrix
        right = Mw.to_3x3() @ (rig.data.bones[n].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0)))
        R = Quaternion(right.normalized(), math.radians(ang * w)).to_matrix() @ Mw.to_3x3().normalized()
        armik.set_world(rig, n, armik.rot_world(Mw, R))
        pb.keyframe_insert('rotation_quaternion', frame=f)
    C = AW @ rig.pose.bones['B_Spine2'].matrix
    Rc = C.to_3x3().normalized() @ rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
    fwd, up, xs = Rc @ Vector((0, -1, 0)), Rc @ Vector((0, 0, 1)), Rc @ Vector((1, 0, 0))
    for s, sg in (('L', 1), ('R', -1)):
        W0 = (AW @ rig.pose.bones[f'B_{s}_Hand'].matrix).translation.copy()
        T = C.translation + fwd * FWD - up * DOWN + xs * (sg * SIDE)
        S = (AW @ rig.pose.bones[f'B_{s}_UpperArm'].matrix).translation
        pole = S + xs * (sg * 0.18) - up * 0.45 + fwd * -0.15
        armik.solve(rig, s, W0.lerp(T, w), pole=pole)
        aim = (up * 0.55 + fwd * 0.7 - xs * (sg * 0.35)).normalized()
        cur = ((AW @ rig.pose.bones[f'B_{s}_Hand'].matrix).to_3x3() @ AX[s]).normalized()
        d = cur.lerp(aim, w).normalized()
        R, roll, sw, tw = armik.hand_for_axis(rig, s, AX[s], d, prev_roll=prev[s])
        prev[s] = roll
        armik.set_world(rig, f'B_{s}_Hand', armik.rot_world(AW @ rig.pose.bones[f'B_{s}_Hand'].matrix, R))
    for n in ARM:
        rig.pose.bones[n].rotation_mode = 'QUATERNION'; rig.pose.bones[n].keyframe_insert('rotation_quaternion', frame=f)
rig.animation_data.action = None
print('FIDGET frames', f1 - f0 + 1, 'hold', IN[1], '-', HOLD_END)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
