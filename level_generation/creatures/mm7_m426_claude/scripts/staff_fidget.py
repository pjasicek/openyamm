"""Mage Fidget (native m274 fa-fd: he brings the staff in front of his body and holds it upright with both hands, then
returns it to his side). Built on the carried Standing (author_carry.py ran first): Fidget = a copy of Standing; the
left wrist blends (smoothstep IN, hold, OUT) from its carry point to FRONT (in the chest frame of frame 0) with the
staff upright (the hand rotation re-chosen per frame by armik.hand_for_axis with continuity); the right hand reaches
the staff RIGHT_BELOW m under the left grip (armik.solve, palm toward the staff). Both arms are solved for the full
pose and then blended from the clip's own arm rotations by the weight (bone-local slerp): solving partway re-chose
the upper-arm roll at once and twisted the free arm in the first frames (user review 2026-10-20).
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, common
a = sys.argv[sys.argv.index('--') + 1:]
src, out = a[0], a[1]
IN, HOLD_END, OUT = (4, 22), 42, 16
FRONT = Vector(json.loads(os.environ.get('FRONT', '[0.10, -0.30, 0.04]')))     # chest frame offset (x out, y fwd(-), z)
RIGHT_BELOW = 0.16
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']; AW = rig.matrix_world
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json'))); side = G['side']; other = 'R' if side == 'L' else 'L'
AX = Vector(G['handle_axis_hand_local']).normalized(); GC = Vector(G['handle_centre_hand_local'])
st = bpy.data.actions['Standing']
if 'Fidget' in bpy.data.actions:
    bpy.data.actions.remove(bpy.data.actions['Fidget'])
act = st.copy(); act.name = 'Fidget'; act.use_fake_user = True
rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
f0, f1 = (int(round(x)) for x in act.frame_range)


def sstep(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def weight(f):
    if f < IN[1]:
        return sstep((f - IN[0]) / (IN[1] - IN[0]))
    return 1.0 if f <= HOLD_END else 1.0 - sstep((f - HOLD_END) / OUT)


scene.frame_set(f0)
C0 = AW @ rig.pose.bones['B_Spine2'].matrix
Rc = C0.to_3x3().normalized() @ rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
front_w = Rc @ Vector((0, 0, 0)) + C0.translation
fwd, up, xs = Rc @ Vector((0, -1, 0)), Rc @ Vector((0, 0, 1)), Rc @ Vector((1, 0, 0))
SG = 1 if side == 'L' else -1
target_front = C0.translation + xs * (SG * FRONT.x) + fwd * (-FRONT.y) + up * FRONT.z - up * 0.30
prev_roll = None
for f in range(f0, f1 + 1):
    scene.frame_set(f)
    w = weight(f)
    if w <= 0:
        continue
    ARM = [f'B_{s_}_{b}' for s_ in (side, other) for b in ('UpperArm', 'Forearm', 'Hand')]
    for n in ARM:
        rig.pose.bones[n].rotation_mode = 'QUATERNION'
    q0 = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in ARM}
    T = target_front
    S = (AW @ rig.pose.bones[f'B_{side}_UpperArm'].matrix).translation
    armik.solve(rig, side, T, pole=S + xs * (SG * 0.25) - up * 0.4 + fwd * -0.1)
    R, prev_roll, sw, tw = armik.hand_for_axis(rig, side, AX, Vector((0, 0, 1)), prev_roll=prev_roll)
    armik.set_world(rig, f'B_{side}_Hand', armik.rot_world(AW @ rig.pose.bones[f'B_{side}_Hand'].matrix, R))
    Hm = AW @ rig.pose.bones[f'B_{side}_Hand'].matrix
    grip = Hm @ GC; axw = (Hm.to_3x3() @ AX).normalized()
    Wo = (AW @ rig.pose.bones[f'B_{other}_Hand'].matrix).translation
    T2 = grip - axw * RIGHT_BELOW + xs * (-SG * 0.03) + fwd * 0.02
    So = (AW @ rig.pose.bones[f'B_{other}_UpperArm'].matrix).translation
    armik.solve(rig, other, T2, pole=So - xs * (SG * 0.25) - up * 0.4 + fwd * -0.1)
    for n in ARM:
        pb = rig.pose.bones[n]; q1 = pb.rotation_quaternion.copy()
        if q0[n].dot(q1) < 0:
            q1.negate()
        pb.rotation_quaternion = q0[n].slerp(q1, w); pb.keyframe_insert('rotation_quaternion', frame=f)
    bpy.context.view_layer.update()
rig.animation_data.action = None
print('STAFFFIDGET frames', f1 - f0 + 1, 'hold', IN[1], '-', HOLD_END)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
