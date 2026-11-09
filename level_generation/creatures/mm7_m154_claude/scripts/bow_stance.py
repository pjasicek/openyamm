"""m154 attack stance (batch A review 2026-10-20: "he is not looking/aiming in front of him"). The planted retarget held
the pelvis and legs on Standing and turned the source chest onto Standing's chest, but an archer stands side-on: the
Mixamo draw turns the whole body ~90 deg so that the bow arm, the arrow and the head point at the target. Planted, the
arrow and the head pointed 86 deg to the right. Now Draw and Recoil are retargeted unplanted (the source's own body
turn), and this step keeps the feet near Standing's, as m214's author_bow.py: the source's bow stance (feet ~0.9 m
apart along the aim) is narrowed to STANCE of its spread from Standing's feet (foot rotation blended the same), the
pelvis raised by RAISE of its drop below Standing and kept over the feet, legs re-solved by two-bone IK.
Aim: the mirrored source ends its turn ~8 deg past straight ahead; the pelvis turns back by the full-draw yaw of the bow
hand seen from the head (yaw 0 = straight ahead, -Y), in proportion to the body's turn so far (0 at the start).
The ease from/to Standing stays in clip_timing.py (BLEND_IN/BLEND_OUT). Args: -- <in blend> <out blend> [Action]"""
import bpy, sys, os, math, json
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
src, out = a[0], a[1]; NAME = a[2] if len(a) > 2 else 'Attack'
STANCE = float(os.environ.get('STANCE', '0.4'))
RAISE = float(os.environ.get('RAISE', '0.85'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
names = [b.name for b in rig.data.bones]
LEGS = [n for n in names if any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'


def set_act(x):
    rig.animation_data_create(); rig.animation_data.action = x
    if x is not None and len(x.slots):
        rig.animation_data.action_slot = x.slots[0]


def basis(act, f):
    set_act(act); scene.frame_set(int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def apply(P):
    set_act(None)
    for n, (q, l) in P.items():
        pb = rig.pose.bones[n]; pb.rotation_quaternion = q; pb.location = l
    bpy.context.view_layer.update()


def leg_ik(side, ankle_target, foot_rot):
    th, ca, ft = f'B_{side}_Thigh', f'B_{side}_Calf', f'B_{side}_Foot'
    Hh = armik.W(rig, th).translation; Kk = armik.W(rig, ca).translation; Aa = armik.W(rig, ft).translation
    L1, L2 = (Kk - Hh).length, (Aa - Kk).length
    T = Vector(ankle_target); d = T - Hh; dist = min(d.length, (L1 + L2) * 0.999); u = d.normalized()
    p = (Kk - Hh) - (Aa - Hh).normalized() * (Kk - Hh).dot((Aa - Hh).normalized())     # the source knee's bend side
    p = (Aa - Hh).normalized().rotation_difference(u) @ p
    v = (p - u * p.dot(u)).normalized()
    c = max(-1, min(1, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)))
    K = Hh + L1 * (u * c + v * math.sqrt(1 - c * c))
    q = (Kk - Hh).normalized().rotation_difference((K - Hh).normalized())
    armik.set_world(rig, th, armik.rot_world(armik.W(rig, th), q.to_matrix() @ armik.W(rig, th).to_3x3().normalized()))
    Mc = armik.W(rig, ca)
    q2 = (armik.W(rig, ft).translation - Mc.translation).normalized().rotation_difference((Hh + u * dist - Mc.translation).normalized())
    armik.set_world(rig, ca, armik.rot_world(Mc, q2.to_matrix() @ Mc.to_3x3().normalized()))
    armik.set_world(rig, ft, armik.rot_world(armik.W(rig, ft), foot_rot.to_matrix()))


apply(basis(bpy.data.actions['Standing'], 0))
st_pz = armik.W(rig, 'B_Pelvis').translation.z
st_ank = {s: armik.W(rig, f'B_{s}_Foot').translation.copy() for s in 'LR'}
st_frot = {s: armik.W(rig, f'B_{s}_Foot').to_quaternion() for s in 'LR'}
act = bpy.data.actions[NAME]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
nd = json.loads(scene.get('concat', '{}')).get(NAME, [f1 - f0 + 1])[0]
PEL_FWD = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))


def yaw_of(v):
    return math.degrees(math.atan2(v.x, -v.y))


def aim_yaw():
    d = armik.W(rig, 'B_R_Hand').translation - armik.W(rig, 'B_Head').translation
    return yaw_of(d)


pel_yaw = []
for f in range(f0, f1 + 1):
    apply(basis(act, f)); pel_yaw.append(yaw_of(armik.W(rig, 'B_Pelvis').to_3x3() @ PEL_FWD))
    if f - f0 == nd - 1:
        aim0 = aim_yaw()
turn = lambda i: max(0.0, min(1.0, (pel_yaw[i] - pel_yaw[0]) / (pel_yaw[nd - 1] - pel_yaw[0])))
poses, raised, yaws = [], [], []
for f in range(f0, f1 + 1):
    P = basis(act, f); apply(P)
    R = Matrix.Rotation(math.radians(-aim0 * turn(f - f0)), 4, 'Z')
    pel = armik.W(rig, 'B_Pelvis'); t = pel.translation.copy(); pel = R @ pel; pel.translation = t
    armik.set_world(rig, 'B_Pelvis', pel)
    pel = armik.W(rig, 'B_Pelvis'); dz = max(0.0, st_pz - pel.translation.z) * RAISE
    ank = {s: st_ank[s].lerp(armik.W(rig, f'B_{s}_Foot').translation, STANCE) for s in 'LR'}
    frot = {s: st_frot[s].slerp(armik.W(rig, f'B_{s}_Foot').to_quaternion(), STANCE) for s in 'LR'}
    M = pel.copy(); M.translation.z += dz
    old_mid = (armik.W(rig, 'B_L_Foot').translation + armik.W(rig, 'B_R_Foot').translation) / 2
    shift = (ank['L'] + ank['R']) / 2 - old_mid                 # the pelvis keeps its place over the feet
    M.translation.x += shift.x; M.translation.y += shift.y
    armik.set_world(rig, 'B_Pelvis', M)
    for s in 'LR':
        leg_ik(s, ank[s], frot[s])
    for n in ['B_Pelvis'] + LEGS:
        pb = rig.pose.bones[n]; P[n] = (pb.rotation_quaternion.copy(), pb.location.copy())
    poses.append(P); raised.append(dz)
    yaws.append(aim_yaw())
set_act(act)
for i, P in enumerate(poses):
    for n in ['B_Pelvis'] + LEGS:
        q, l = P[n]; pb = rig.pose.bones[n]
        if i and q.dot(poses[i - 1][n][0]) < 0:
            q = -q; P[n] = (q, l)
        pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f0 + i)
        if n == 'B_Pelvis':
            pb.location = l; pb.keyframe_insert('location', frame=f0 + i)
set_act(None)
print(f'STANCE {NAME}: feet at {STANCE:.2f} of the source spread, pelvis raised max {100 * max(raised):.1f} cm; '
      f'full-draw aim (bow hand from the head, frame {nd - 1}) yaw {aim0:+.1f} -> {yaws[nd - 1]:+.1f} deg')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
