"""Free (left) arm hang toward the native (m286sa0, wa..wh): the native's left forearm angles in from the elbow so the
fist hangs beside the kilt (forearm about 15 deg inward from vertical in the front view); Mixamo Orc Idle / Orc Walk
angle it about 15 deg outward. In each listed clip every frame turns B_<SIDE>_UpperArm by UA deg and B_<SIDE>_Forearm
by FA deg toward the midline about the pelvis's forward axis (at the shoulder / elbow), then flexes the elbow by FLEX
deg (forearm forward and up about the pelvis's lateral axis: the native fist sits at the hip with the forearm pointing
forward, m286sa0/sa2); the hand follows the forearm.
arm_clear.py later swings the arm out again only where a hand would enter the body. Local keys from armature-space
matrices (as narrow_stance.py). Args: -- <in blend> <out blend> Clip[:fa[:ua[:flex]]] ...   (env SIDE, default L)"""
import bpy, sys, os, math
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
S = os.environ.get('SIDE', 'L')
SIGN = -1.0 if S == 'L' else 1.0                           # +angle about forward swings a hanging arm toward +X
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
PEL_FWD = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
PEL_LAT = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0))


def basis(bn, P_pose, B_pose):
    b = rig.data.bones[bn]
    rest_rel = b.parent.matrix_local.inverted() @ b.matrix_local
    return rest_rel.inverted() @ (P_pose.inverted() @ B_pose)


def set_act(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


UA_N, FA_N = f'B_{S}_UpperArm', f'B_{S}_Forearm'
for item in items:
    p = item.split(':'); name = p[0]
    fa = float(p[1]) if len(p) > 1 else 30.0; ua = float(p[2]) if len(p) > 2 else 0.0
    flex = float(p[3]) if len(p) > 3 else 0.0
    act = bpy.data.actions[name]; set_act(act)
    f0, f1 = (int(x) for x in act.frame_range)
    keys = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        pb = rig.pose.bones
        fwd = (pb['B_Pelvis'].matrix.to_3x3() @ PEL_FWD).normalized()
        lat = (pb['B_Pelvis'].matrix.to_3x3() @ PEL_LAT).normalized()
        U, F = pb[UA_N].matrix.copy(), pb[FA_N].matrix.copy()
        sh = U.translation.copy()
        Ru = Matrix.Translation(sh) @ Matrix.Rotation(SIGN * math.radians(ua), 4, fwd) @ Matrix.Translation(-sh)
        U2 = Ru @ U; F1 = Ru @ F
        el = F1.translation.copy()
        Rf = Matrix.Translation(el) @ Matrix.Rotation(SIGN * math.radians(fa), 4, fwd) @ Matrix.Translation(-el)
        # a hanging forearm (down) turns toward forward (-Y) under a negative rotation about +X
        Rx = Matrix.Translation(el) @ Matrix.Rotation(-math.radians(flex), 4, lat) @ Matrix.Translation(-el)
        F2 = Rx @ Rf @ F1
        keys.append((f, {UA_N: basis(UA_N, pb[UA_N].parent.matrix, U2).to_quaternion(),
                         FA_N: basis(FA_N, U2, F2).to_quaternion()}))
    set_act(None); set_act(act)
    prev = {}
    for f, fr in keys:
        for bn, q in fr.items():
            if bn in prev and q.dot(prev[bn]) < 0:
                q = -q
            prev[bn] = q
            b = rig.pose.bones[bn]; b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = q
            b.keyframe_insert('rotation_quaternion', frame=f)
    print('ARMHANG', name, S, 'frames', len(keys), 'forearm in', fa, 'deg, upper arm in', ua, 'deg, elbow flex', flex, 'deg')
set_act(None)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
