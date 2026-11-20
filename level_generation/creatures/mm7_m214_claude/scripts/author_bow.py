"""m214 attack, fidget and the bow/string/arrow tracks (after bow_rig.py).
Attack = Mixamo "Standing Draw Arrow" (Draw: reach over the right shoulder into the quiver, nock, raise and draw) then
"Standing Aim Recoil" (Recoil: release and lower), eased from Standing frame 0 over EASE_IN frames and back to it over
EASE_OUT frames; the source's bow stance (feet 0.9 m apart along the aim) is narrowed to STANCE of its spread from Standing's feet
(feet planted, foot rotation blended the same), the pelvis raised by RAISE of its drop below Standing, legs re-solved
by two-bone IK. Native: draw from the quiver, nock, raise, draw, release.
Tracks (attack frames at 30 fps, measured with probe_bow.py on the source arms):
- Arrow: hidden (scale 0) before GRAB; from GRAB to NOCK its nock end sits at the right-hand pinch (thumb/index tips)
  and it turns from the quiver direction (pointing into the quiver) to the nocked direction; from NOCK to RELEASE it is
  nocked: nock at the string's nocking point, pointing at the arrow rest (Socket_Arrow_Release); hidden from RELEASE
  (the game launches its projectile at the impact event, which is the release).
- String: StringNock at rest except NOCK..RELEASE, where it follows the pinch (never in front of the braced string),
  then snaps back with a 1 cm overshoot.
- Every other clip: arrow hidden, string at rest (constant keys).
Fidget: Standing's body; the left wrist path (chest frame) raises the bow in front of the chest, turns it up and out,
holds, and lowers it again (native fa..fe), solved with the global arm solver (armik.arm_dp).
Writes work/attack_timing.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; scene = bpy.context.scene
scene.render.fps = 30
names = [b.name for b in rig.data.bones]
GRIP = json.load(open(os.path.join(common.WORK, 'grip_pose_L.json')))
FJ = json.load(open(os.path.join(common.WORK, 'finger_joints.json')))['R']
BR = json.load(open(os.path.join(common.WORK, 'bow_rig.json')))
AX = Vector(GRIP['handle_axis_hand_local']).normalized()
EASE_IN, EASE_OUT, RAISE = 9, 10, float(os.environ.get('RAISE', '0.85'))
STANCE = float(os.environ.get('STANCE', '0.4'))                 # share of the source's foot spread kept (0.9 m wide)
GRAB, NOCK, RELEASE_R = 10, 17, 1                                 # Draw frames; release = Recoil frame 1
NOCK_X = BR['nock_bow'][0]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def basis(act, f):
    set_act(act); scene.frame_set(int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'
smooth = lambda x: x * x * (3 - 2 * x)
st, dr, rc = (bpy.data.actions[n] for n in ('Standing', 'Draw', 'Recoil'))
S0 = basis(st, 0)
nd, nr = int(dr.frame_range[1]) + 1, int(rc.frame_range[1]) + 1
src_frames = [(dr, f) for f in range(nd)] + [(rc, f) for f in range(nr)]
N = len(src_frames)
RELEASE = nd + RELEASE_R
LEGS = [n for n in names if any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]
# ---------------------------------------------------------------- Attack body
if 'Attack' in bpy.data.actions:
    bpy.data.actions.remove(bpy.data.actions['Attack'])
att = bpy.data.actions.new('Attack'); att.use_fake_user = True
poses = []
for i, (a, f) in enumerate(src_frames):
    B = basis(a, f)
    w = 1.0
    if i < EASE_IN:
        w = smooth(i / EASE_IN)
    if i > N - 1 - EASE_OUT:
        w = min(w, smooth((N - 1 - i) / EASE_OUT))
    P = {}
    for n in names:
        q0, l0 = S0[n]; q1, l1 = B[n]
        if q0.dot(q1) < 0:
            q1 = -q1
        P[n] = (q0.slerp(q1, w), l0.lerp(l1, w))
    poses.append(P)
# raise the planted stance: pelvis up by RAISE x its drop below Standing, feet held by two-bone leg IK
st_pz = None


def apply(P):
    for n, (q, l) in P.items():
        pb = rig.pose.bones[n]; pb.rotation_quaternion = q; pb.location = l
    bpy.context.view_layer.update()


set_act(None)
apply(S0); st_pz = armik.W(rig, 'B_Pelvis').translation.z
st_ank = {s: armik.W(rig, f'B_{s}_Foot').translation.copy() for s in 'LR'}
st_frot = {s: armik.W(rig, f'B_{s}_Foot').to_quaternion() for s in 'LR'}


def leg_ik(side, ankle_target, foot_rot=None):
    th, ca, ft = f'B_{side}_Thigh', f'B_{side}_Calf', f'B_{side}_Foot'
    Mf = foot_rot.to_matrix() if foot_rot is not None else armik.W(rig, ft).to_3x3().normalized().copy()
    Hh = armik.W(rig, th).translation; Kk = armik.W(rig, ca).translation; Aa = armik.W(rig, ft).translation
    L1, L2 = (Kk - Hh).length, (Aa - Kk).length
    T = Vector(ankle_target); d = T - Hh; dist = min(d.length, (L1 + L2) * 0.999); u = d.normalized()
    p = (Kk - Hh) - (Aa - Hh).normalized() * (Kk - Hh).dot((Aa - Hh).normalized())
    p = (Aa - Hh).normalized().rotation_difference(u) @ p
    v = (p - u * p.dot(u)).normalized()
    c = max(-1, min(1, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)))
    K = Hh + L1 * (u * c + v * math.sqrt(1 - c * c))
    q = (Kk - Hh).normalized().rotation_difference((K - Hh).normalized())
    armik.set_world(rig, th, armik.rot_world(armik.W(rig, th), q.to_matrix() @ armik.W(rig, th).to_3x3().normalized()))
    Mc = armik.W(rig, ca)
    q2 = (armik.W(rig, ft).translation - Mc.translation).normalized().rotation_difference((Hh + u * dist - Mc.translation).normalized())
    armik.set_world(rig, ca, armik.rot_world(Mc, q2.to_matrix() @ Mc.to_3x3().normalized()))
    armik.set_world(rig, ft, armik.rot_world(armik.W(rig, ft), Mf))


raised = []
for i, P in enumerate(poses):
    apply(P)
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
    raised.append(dz)
set_act(att)
for i, P in enumerate(poses):
    for n, (q, l) in P.items():
        pb = rig.pose.bones[n]
        if i and q.dot(poses[i - 1][n][0]) < 0:
            q = -q; P[n] = (q, l)
        pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=i)
        if n == 'B_Pelvis':
            pb.location = l; pb.keyframe_insert('location', frame=i)
att.use_frame_range = True; att.frame_start, att.frame_end = 0, N - 1
print(f'ATTACK frames {N} ({N / 30:.3f} s), release frame {RELEASE} ({RELEASE / 30:.3f} s), pelvis raised max cm '
      f'{100 * max(raised):.1f}')
# ---------------------------------------------------------------- Fidget (left arm path over Standing's body)
if 'Fidget' in bpy.data.actions:
    bpy.data.actions.remove(bpy.data.actions['Fidget'])
NF = 75
fid = bpy.data.actions.new('Fidget'); fid.use_fake_user = True
SB = [basis(st, f) for f in range(NF)]
set_act(fid)
for f in range(NF):
    for n in names:
        pb = rig.pose.bones[n]; pb.rotation_quaternion, pb.location = SB[f][n]
        pb.keyframe_insert('rotation_quaternion', frame=f)
        if n == 'B_Pelvis':
            pb.keyframe_insert('location', frame=f)
fid.use_frame_range = True; fid.frame_start, fid.frame_end = 0, NF - 1
CAR = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'carry_L.json')))


def dir_of(yaw_out, pitch):
    ya, pi_ = math.radians(yaw_out), math.radians(pitch)
    return Vector((math.sin(ya) * math.cos(pi_), -math.cos(ya) * math.cos(pi_), math.sin(pi_)))


KEYS = [(0, Vector(CAR['wrist']), (CAR['yaw_out'], CAR['pitch'])),            # carry
        (10, Vector((0.37, -0.32, 0.98)), (-8, 40)),                             # tipped up-forward, lower limb outside the thigh
        (20, Vector((0.20, -0.42, 1.04)), (-40, 50)),                            # raised across the front: upper tip in front of
        (32, Vector((0.19, -0.44, 1.08)), (-35, 58)),                            # the chest, lower tip down and out (native fb..fd)
        (48, Vector((0.21, -0.42, 1.06)), (-45, 45)),
        (58, Vector((0.37, -0.32, 0.98)), (-8, 40)),
        (68, Vector(CAR['wrist']), (CAR['yaw_out'], CAR['pitch'])), (NF - 1, Vector(CAR['wrist']), (CAR['yaw_out'], CAR['pitch']))]


def key_at(f):
    for (f0, w0, d0), (f1, w1, d1) in zip(KEYS[:-1], KEYS[1:]):
        if f0 <= f <= f1:
            t = smooth((f - f0) / max(f1 - f0, 1))
            return w0.lerp(w1, t), (d0[0] + (d1[0] - d0[0]) * t, d0[1] + (d1[1] - d0[1]) * t)
    return KEYS[-1][1], KEYS[-1][2]


set_act(fid); scene.frame_set(0)
C0 = armik.W(rig, 'B_Spine2'); P0 = armik.W(rig, 'B_Pelvis')
frames_in = []
for f in range(NF):
    set_act(fid); scene.frame_set(f)
    snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    w, (yo, pt) = key_at(f)
    C = armik.W(rig, 'B_Spine2'); P = armik.W(rig, 'B_Pelvis')
    target = C @ (C0.inverted() @ w)
    d = P.to_3x3().normalized() @ (P0.to_3x3().normalized().inverted() @ dir_of(yo, pt))
    frames_in.append({'snap': snap, 'wrist': target, 'dir': d})
set_act(None)
ch = armik.arm_dp(rig, 'L', frames_in, AX, twist_neutral=-30.0, k_twist=0.6, k_dphi=1.0, k_dpsi=0.8)
ARM = ['B_L_Clavicle', 'B_L_UpperArm', 'B_L_Forearm', 'B_L_Hand']
gk = np.exp(-0.5 * (np.arange(-3, 4) / 2.0) ** 2); gk /= gk.sum()
sm = lambda x: np.convolve(np.concatenate([np.repeat(x[:1], 3), x, np.repeat(x[-1:], 3)]), gk, 'valid')
phi = sm(np.array([c['phi'] for c in ch], float)); psi = sm(np.degrees(np.unwrap(np.radians([c['psi'] for c in ch]))))
arm_poses = []
for i, fr in enumerate(frames_in):
    armik.apply_arm(rig, 'L', fr['snap'], fr['wrist'], AX, fr['dir'], phi[i], psi[i], ch[i]['dev'])
    arm_poses.append({n: rig.pose.bones[n].matrix_basis.to_quaternion() for n in ARM})
set_act(fid)
for i in range(NF):
    for n in ARM:
        pb = rig.pose.bones[n]; q = arm_poses[i][n]
        if i and q.dot(arm_poses[i - 1][n]) < 0:
            q = -q; arm_poses[i][n] = q
        pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=i)
print('FIDGET frames', NF, 'wrist swing max', round(max(c['swing'] for c in ch), 1), 'twist range',
      round(min(c['twist'] for c in ch), 1), round(max(c['twist'] for c in ch), 1))
# ---------------------------------------------------------------- tracks


def tip(n):
    pb = rig.pose.bones[n]
    return rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted() @ Vector(FJ[n + '_tip'])


# quiver axis (into the quiver) in the B_Spine2 rest frame: PCA of the quiver shell, pointing down
co = np.array([tuple(v.co) for v in body.data.vertices]); pv = np.zeros(len(co), np.int32)
body.data.attributes['piece'].data.foreach_get('value', pv)
q = co[pv == 9]; c = q.mean(0); ax = np.linalg.svd(q - c)[2][0]; ax = ax if ax[2] < 0 else -ax
QUIVER_DIR = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector(ax)
for act in [a for a in bpy.data.actions if a.use_fake_user]:
    set_act(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    an, sn = rig.pose.bones['Arrow'], rig.pose.bones['StringNock']
    for pb in (an, sn):
        pb.rotation_mode = 'QUATERNION'
    if act.name != 'Attack':
        for f in (f0, f1):
            an.matrix_basis = Matrix.Diagonal((0, 0, 0, 1)); sn.matrix_basis = Matrix()
            an.keyframe_insert('scale', frame=f); an.keyframe_insert('location', frame=f)
            an.keyframe_insert('rotation_quaternion', frame=f); sn.keyframe_insert('location', frame=f)
        continue
    log = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        Bw = rig.matrix_world @ rig.pose.bones['Bow'].matrix
        rest_w = (rig.matrix_world @ rig.pose.bones['Socket_Arrow_Release'].matrix).translation
        pinch = (tip('B_R_Finger0.002') + tip('B_R_Finger12')) / 2
        pb_bow = Bw.inverted() @ pinch
        nock_bow = Vector(BR['nock_bow'])
        if NOCK <= f < RELEASE:
            nb = pb_bow.copy(); nb.x = min(nb.x, NOCK_X)
            k = smooth(min(1.0, (f - NOCK) / 2.0))                  # the string is caught over two frames
            nock_bow = nock_bow.lerp(nb, k)
        elif RELEASE <= f < RELEASE + 3:
            nock_bow = nock_bow + Vector((0.01 * (1, -0.4, 0.1)[f - RELEASE], 0, 0))
        nw = Bw @ nock_bow
        Mn = rig.pose.bones['Bow'].matrix.copy(); Mn.translation = rig.matrix_world.inverted() @ nw
        sn.matrix = Mn; bpy.context.view_layer.update(); sn.keyframe_insert('location', frame=f)
        # arrow
        if GRAB <= f < RELEASE:
            nocked_dir = (rest_w - nw).normalized()
            if f < NOCK:
                C = (rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix).to_3x3().normalized()
                dq = (C @ QUIVER_DIR).normalized()
                t = smooth((f - GRAB) / (NOCK - GRAB))
                d = Quaternion().slerp(dq.rotation_difference(nocked_dir), t) @ dq
                base = pinch
            else:
                d = nocked_dir; base = nw
            up = Bw.col[0].xyz
            x = up.cross(d).normalized(); z = x.cross(d)
            Mw = Matrix((x, d, z)).transposed().to_4x4(); Mw.translation = base
            an.matrix = rig.matrix_world.inverted() @ Mw
        else:
            an.matrix_basis = Matrix.Diagonal((0, 0, 0, 1))
        bpy.context.view_layer.update()
        an.keyframe_insert('location', frame=f); an.keyframe_insert('rotation_quaternion', frame=f)
        an.keyframe_insert('scale', frame=f)
        log.append({'f': f, 'pinch_bow': [round(v, 3) for v in pb_bow], 'nock_bow': [round(v, 3) for v in nock_bow]})
    draw = max(-e['nock_bow'][0] for e in log)
    print('TRACKS Attack: arrow visible frames', GRAB, '..', RELEASE - 1, 'nocked from', NOCK, 'max draw (string from grip) cm',
          round(100 * draw, 1), 'full-draw anchor in the bow frame', log[RELEASE - 1]['pinch_bow'])
json.dump({'frames': N, 'fps': 30, 'grab': GRAB, 'nock': NOCK, 'release_frame': RELEASE, 'release_s': RELEASE / 30,
           'ease_in': EASE_IN, 'ease_out': EASE_OUT, 'raise': RAISE},
          open(os.path.join(common.WORK, 'attack_timing.json'), 'w'), indent=1)
set_act(None)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
