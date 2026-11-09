"""The Monk's folded arms (native hvf sa/wa/fi: the forearms crossed in front of the waist, each hand hidden in the
other sleeve). Per frame of each listed clip, both wrists are moved (armik.solve, minimal change, elbow pole out and
down) to a point in the chest frame: in front of the chest, DOWN below the chest joint, the wrist crossed SIDE past
the centre line toward the other elbow; the hand points along the other forearm (armik.hand_for_axis, continuity).
A share KEEP of the clip's own wrist motion (relative to the chest) stays, so the walk still sways. Weight per clip
(name:keep[:in:out] seconds of smoothstep blend from/to the source arm, for one-shots that unfold).
Args: -- <in blend> <out blend> Clip[:keep[:in:out]] ..."""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
FWD, DOWN, SIDE = float(os.environ.get('FOLD_FWD', '0.21')), float(os.environ.get('FOLD_DOWN', '0.20')), float(os.environ.get('FOLD_SIDE', '0.05'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']; AW = rig.matrix_world
AX = {}
for s in ('L', 'R'):
    h = rig.data.bones[f'B_{s}_Hand']; m = rig.data.bones[f'B_{s}_Finger2']
    AX[s] = (h.matrix_local.to_3x3().inverted() @ (m.head_local - h.head_local)).normalized()


def sstep(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


for it in items:
    p = it.split(':'); name = p[0]; keep = float(p[1]) if len(p) > 1 else 0.2
    tin = float(p[2]) if len(p) > 2 else 0.0; tout = float(p[3]) if len(p) > 3 else 0.0
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range); fps = 30.0
    scene.frame_set(f0)
    own0 = {s: armik.W(rig, 'B_Spine2').inverted() @ armik.W(rig, f'B_{s}_Hand').translation for s in 'LR'}
    prev = {'L': None, 'R': None}
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        w = 1.0
        if tin > 0:
            w = min(w, sstep((f - f0) / (tin * fps)))
        if tout > 0:
            w = min(w, sstep((f1 - f) / (tout * fps)))
        if w <= 0:
            continue
        C = AW @ rig.pose.bones['B_Spine2'].matrix
        Rc = C.to_3x3().normalized() @ rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
        fwd, up, xs = Rc @ Vector((0, -1, 0)), Rc @ Vector((0, 0, 1)), Rc @ Vector((1, 0, 0))
        for s, sg in (('L', 1), ('R', -1)):
            Wh = (AW @ rig.pose.bones[f'B_{s}_Hand'].matrix).translation.copy()
            own = armik.W(rig, 'B_Spine2').inverted() @ Wh
            T = C.translation + fwd * FWD - up * DOWN - xs * (sg * SIDE) + (C.to_3x3() @ (own - own0[s])) * keep
            # left forearm slightly above the right (crossed arms): offset forward/up for the left
            if s == 'L':
                T = T + fwd * 0.03 + up * 0.03
            S = (AW @ rig.pose.bones[f'B_{s}_UpperArm'].matrix).translation
            armik.solve(rig, s, Wh.lerp(T, w), pole=S + xs * (sg * 0.30) - up * 0.30 + fwd * -0.05)
            aim = (-xs * sg + fwd * 0.25).normalized()
            cur = ((AW @ rig.pose.bones[f'B_{s}_Hand'].matrix).to_3x3() @ AX[s]).normalized()
            R, prev[s], sw, tw = armik.hand_for_axis(rig, s, AX[s], cur.lerp(aim, w).normalized(), prev_roll=prev[s])
            armik.set_world(rig, f'B_{s}_Hand', armik.rot_world(AW @ rig.pose.bones[f'B_{s}_Hand'].matrix, R))
        for s in 'LR':
            for b in ('UpperArm', 'Forearm', 'Hand'):
                pb = rig.pose.bones[f'B_{s}_{b}']; pb.rotation_mode = 'QUATERNION'; pb.keyframe_insert('rotation_quaternion', frame=f)
    print('FOLD', name, 'frames', f1 - f0 + 1, 'keep', keep, 'blend in/out s', tin, tout)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
