"""The Warlock's wand cast (user review 2026-10-20: "the wand should be the main casting thing"). On the Cast clip
(set Unarmed Cast L Attack 3, faced front and carried), the wand hand is moved by IK (armik.solve, elbow down and
out) through targets in the chest frame of frame 0, relative to the left shoulder: WINDUP (wand raised beside the
head, crystal up and back), THRUST (arm forward at chest height, crystal toward the target), held, then back to the
clip's own (carried) arm. Smoothstep between the keys; the hand is turned so the wand axis (grip_pose.json) follows
the aim, with roll continuity. The other arm keeps the clip. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, common
src, out = sys.argv[sys.argv.index('--') + 1:]
# (frame, weight, target offset (out, fwd, up) from the shoulder, aim (out, fwd, up))
KEYS = [(3, 0.0, (0.10, 0.05, -0.40), (0.0, 0.3, 1.0)),
        (10, 1.0, (0.16, -0.02, 0.10), (0.15, -0.35, 1.0)),
        (15, 1.0, (0.08, 0.40, -0.02), (0.0, 1.0, 0.30)),
        (20, 1.0, (0.08, 0.41, -0.03), (0.0, 1.0, 0.25)),
        (29, 0.0, (0.10, 0.05, -0.40), (0.0, 0.3, 1.0))]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']; AW = rig.matrix_world
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json'))); side = G['side']; SG = 1 if side == 'L' else -1
AX = Vector(G['handle_axis_hand_local']).normalized()
act = bpy.data.actions['Cast']; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
f0, f1 = (int(round(x)) for x in act.frame_range)


def sstep(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def at(f):
    """weight, target offset, aim at frame f (smoothstep between the keys)."""
    if f <= KEYS[0][0]:
        k = KEYS[0]; return k[1], Vector(k[2]), Vector(k[3])
    for a, b in zip(KEYS, KEYS[1:]):
        if f <= b[0]:
            t = sstep((f - a[0]) / (b[0] - a[0]))
            return a[1] + (b[1] - a[1]) * t, Vector(a[2]).lerp(Vector(b[2]), t), Vector(a[3]).lerp(Vector(b[3]), t)
    k = KEYS[-1]; return k[1], Vector(k[2]), Vector(k[3])


scene.frame_set(f0)
C0 = AW @ rig.pose.bones['B_Spine2'].matrix
Rc = C0.to_3x3().normalized() @ rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
fwd, up, xs = Rc @ Vector((0, -1, 0)), Rc @ Vector((0, 0, 1)), Rc @ Vector((1, 0, 0))
outv = xs * SG
prev_roll = None
for f in range(f0, f1 + 1):
    scene.frame_set(f)
    w, off, aim = at(f)
    if w <= 0:
        continue
    S = (AW @ rig.pose.bones[f'B_{side}_UpperArm'].matrix).translation
    Wh = (AW @ rig.pose.bones[f'B_{side}_Hand'].matrix).translation
    T = S + outv * off.x + fwd * off.y + up * off.z
    armik.solve(rig, side, Wh.lerp(T, w), pole=S + outv * 0.30 - up * 0.35 - fwd * 0.10)
    cur = ((AW @ rig.pose.bones[f'B_{side}_Hand'].matrix).to_3x3() @ AX).normalized()
    want = (outv * aim.x + fwd * aim.y + up * aim.z).normalized()
    R, prev_roll, sw, tw = armik.hand_for_axis(rig, side, AX, cur.lerp(want, w).normalized(), prev_roll=prev_roll)
    armik.set_world(rig, f'B_{side}_Hand', armik.rot_world(AW @ rig.pose.bones[f'B_{side}_Hand'].matrix, R))
    for b in ('UpperArm', 'Forearm', 'Hand'):
        pb = rig.pose.bones[f'B_{side}_{b}']; pb.rotation_mode = 'QUATERNION'; pb.keyframe_insert('rotation_quaternion', frame=f)
rig.animation_data.action = None
print('WANDCAST frames', f1 - f0 + 1, 'keys', [k[0] for k in KEYS])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
