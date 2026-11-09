"""m218 attack, fidget and the spear track (after spear_rig.py).
Attack = humanoid set "2Hand-Spear-Attack9" (THRUST: spear lifted to the shoulder with both hands, then thrust forward
at chest height and recovered; native m218ab..ag: raise, two-handed horizontal thrust), its wind-up retimed (IMP_SRC ->
IMP_OUT frames) so the blow lands near the native 0.875 s action end, eased from Standing frame 0 over EASE_IN frames
and back to it over EASE_OUT frames; the set's lunge is narrowed to STANCE of its foot spread from Standing's feet
(feet planted, foot rotation blended the same) and the pelvis raised by RAISE of its drop below Standing, legs
re-solved by two-bone IK. (Tried and rejected: natm's authored hip-level thrust over Mixamo "Stabbing (2)" - the left
hand could not reach the shaft, 8-19 cm gaps.)
Spear track (bone 'Spear', child of B_Pelvis, keyed in world terms): the spear rides in the left fist (grip_pose_L.json)
in every clip; in the attack the set's left grip axis points along the thrust, and the right hand is solved onto the
shaft at a fixed 0.5 m behind the left grip (the set's median spacing), its grip axis along the spear, the hand
roll of least wrist bend, eased in with the attack weight (no blend of two spear frames, which swept the shaft through
the torso during the regrip).
IMPACT = the frame the tip reaches 95 % of its forward travel in the thrust.
Fidget: Standing's body; the left wrist path (chest frame) lifts the spear upright beside the body, holds it and lowers it
again (native fa..fd), solved with the global arm solver (armik.arm_dp).
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
GL = json.load(open(os.path.join(common.WORK, 'grip_pose_L.json')))
GR = json.load(open(os.path.join(common.WORK, 'grip_pose.json')))
AX = Vector(GL['handle_axis_hand_local']).normalized(); GCL = Vector(GL['handle_centre_hand_local'])
AXR = Vector(GR['handle_axis_hand_local']).normalized(); GCR = Vector(GR['handle_centre_hand_local'])
SPR = json.load(open(os.path.join(common.WORK, 'spear_rig.json')))
S_HAND_L = Matrix(SPR['spear_hand_L'])
GRIP_GAP = float(os.environ.get('GRIP_GAP', '0.40'))           # spear origin ahead of the right grip (m)
LGRIP = (0.05, 0.75)                                            # left grip along the shaft from the right grip (m)


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def basis_int(act, f):
    set_act(act); scene.frame_set(int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def basis(act, f):
    # fractional frames: slerp the two neighbouring keys with the sign fixed (the retargeted keys are not sign-continuous,
    # so Blender's per-component interpolation between them flipped the arms at the retimed half frames)
    f0 = int(math.floor(f)); t = f - f0
    A = basis_int(act, f0)
    if t < 1e-6:
        return A
    B = basis_int(act, f0 + 1)
    out = {}
    for n in names:
        qa, la = A[n]; qb, lb = B[n]
        if qa.dot(qb) < 0:
            qb = -qb
        out[n] = (qa.slerp(qb, t), la.lerp(lb, t))
    return out


for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'
smooth = lambda x: x * x * (3 - 2 * x)
st = bpy.data.actions['Standing']
TRACKS_ONLY = bool(os.environ.get('TRACKS_ONLY'))                # second pass after spear_clear.py: track + right fist only
if not TRACKS_ONLY:
    st, th = bpy.data.actions['Standing'], bpy.data.actions['Thrust']
    # EASE_OUT 16 (user review 2026-10-20: the 10-frame return to the idle swung the right elbow abruptly in frames
    # 33-39; it now starts right after full reach)
    EASE_IN, EASE_OUT, RAISE = 9, int(os.environ.get('EASE_OUT', '16')), float(os.environ.get('RAISE', '0.85'))
    STANCE = float(os.environ.get('STANCE', '0.5'))
    S0 = basis(st, 0)
    # retime: the wind-up [0, IMP_SRC] (source frames, the measured blow) is stretched to [0, IMP_OUT] so the blow lands near
    # the native action's end (0.875 s, the game acts then); the follow-through keeps its speed
    IMP_SRC = float(os.environ.get('IMP_SRC', '17.86')); IMP_OUT = float(os.environ.get('IMP_OUT', '25.5'))
    n_src = int(th.frame_range[1]) + 1
    N = int(round(IMP_OUT + (n_src - 1 - IMP_SRC))) + 1
    src_frames = [(th, i * IMP_SRC / IMP_OUT if i <= IMP_OUT else min(IMP_SRC + (i - IMP_OUT), n_src - 1)) for i in range(N)]
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
    # arms swung out during the eased transitions (a straight rotation blend from the hanging carry to the two-handed
    # hold swept the fists and the shaft through the thighs and the pelvis)
    BUMP = math.radians(float(os.environ.get('ARM_BUMP', '16')))
    for i, P in enumerate(poses):
        u = i / EASE_IN if i < EASE_IN else ((N - 1 - i) / EASE_OUT if i > N - 1 - EASE_OUT else None)
        if u is None:
            continue
        b = BUMP * math.sin(math.pi * min(max(u, 0.0), 1.0))
        apply(P)
        fwd = armik.W(rig, 'B_Pelvis').to_3x3().normalized() @ Vector((0, -1, 0))
        for sd, sgn in (('L', -1.0), ('R', 1.0)):               # measured: these signs swing the fists out of the thighs
            ua = f'B_{sd}_UpperArm'; M = armik.W(rig, ua)
            armik.set_world(rig, ua, armik.rot_world(M, Matrix.Rotation(sgn * b, 3, fwd) @ M.to_3x3().normalized()))
            pb = rig.pose.bones[ua]; P[ua] = (pb.rotation_quaternion.copy(), pb.location.copy())
    # the shaft line moved by LSHIFT (m, in the chest bone's axes: x forward, y up, z to the right) with the attack
    # weight: the left wrist is re-solved
    # there, its hand keeping its world turn, so the spear moves parallel (user review 2026-10-20: the set's thrust on
    # this turned chest put the right grip in front of the sternum and the right arm 10-12 cm into the chest)
    LSHIFT = Vector([float(x) for x in os.environ.get('LSHIFT', '0,0,0').split(',')])
    if LSHIFT.length > 0:
        for i, P in enumerate(poses):
            w = smooth(i / EASE_IN) if i < EASE_IN else 1.0
            if i > N - 1 - EASE_OUT:
                w = min(w, smooth((N - 1 - i) / EASE_OUT))
            apply(P); H = armik.W(rig, 'B_L_Hand').copy(); C3 = armik.W(rig, 'B_Spine2').to_3x3().normalized()
            armik.solve(rig, 'L', H.translation + (C3 @ LSHIFT) * w, hand_rot=H.to_3x3().normalized())
            for n in ('B_L_UpperArm', 'B_L_Forearm', 'B_L_Hand'):
                pb = rig.pose.bones[n]; P[n] = (pb.rotation_quaternion.copy(), pb.location.copy())
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
    WEIGHT = [1.0] * N
    for i in range(N):
        if i < EASE_IN:
            WEIGHT[i] = smooth(i / EASE_IN)
        if i > N - 1 - EASE_OUT:
            WEIGHT[i] = min(WEIGHT[i], smooth((N - 1 - i) / EASE_OUT))
    print(f'ATTACK frames {N} ({N / 30:.3f} s), source blow frame {IMP_SRC} -> {IMP_OUT}, pelvis raised max cm {100 * max(raised):.1f}')
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


    KEYS = [(0, Vector(CAR['wrist']), (CAR['yaw_out'], CAR['pitch'])),            # carry, tip forward-down
            (14, Vector((0.36, -0.14, 0.98)), (0, 82)),                              # lifted upright beside the body (native fc/fd)
            (52, Vector((0.36, -0.15, 0.99)), (0, 84)),
            (66, Vector(CAR['wrist']), (CAR['yaw_out'], CAR['pitch'])), (NF - 1, Vector(CAR['wrist']), (CAR['yaw_out'], CAR['pitch']))]


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
else:
    N = int(bpy.data.actions['Attack'].frame_range[1]) + 1
    WEIGHT = json.load(open(os.path.join(common.WORK, 'attack_weight.json')))
json.dump(WEIGHT, open(os.path.join(common.WORK, 'attack_weight.json'), 'w'))


# ---------------------------------------------------------------- spear track and the left hand on the shaft


def grip_L():
    return armik.W(rig, 'B_L_Hand') @ S_HAND_L


def grip_R():
    H = armik.W(rig, 'B_R_Hand'); R3 = H.to_3x3().normalized()
    y = (R3 @ AXR).normalized(); hy = R3 @ Vector((0, 1, 0)); x = (hy - y * hy.dot(y)).normalized(); z = x.cross(y)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = H @ GCR + y * GRIP_GAP
    return M


def blend(A, B, w):
    qa, qb = A.to_quaternion(), B.to_quaternion()
    if qa.dot(qb) < 0:
        qb = -qb
    M = qa.slerp(qb, w).to_matrix().to_4x4(); M.translation = A.translation.lerp(B.translation, w)
    return M


LASTQ = {}


def key_spear(M, f):
    pb = rig.pose.bones['Spear']; pb.rotation_mode = 'QUATERNION'
    pb.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
    q = LASTQ.get(rig.animation_data.action.name)
    if q is not None and pb.rotation_quaternion.dot(q) < 0:      # sign-continuous keys
        pb.rotation_quaternion = -pb.rotation_quaternion
    LASTQ[rig.animation_data.action.name] = pb.rotation_quaternion.copy()
    pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)


ARMR = ['B_R_Clavicle', 'B_R_UpperArm', 'B_R_Forearm', 'B_R_Hand']
ARC = float(os.environ.get('ARC', '0.12'))                     # outward bow of the right arm's eased frames (m)
RGRIP_FIXED = float(os.environ.get('RGRIP', '-0.42'))          # right grip 0.42 m behind the left (set median 0.5; less pulls the forearm off the chest)
report = {}
for act in [a for a in bpy.data.actions if a.use_fake_user and a.name not in ('GripRef', 'GripRefR', 'Thrust')]:
    set_act(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    if act.name != 'Attack':
        for f in range(f0, f1 + 1):
            scene.frame_set(f); key_spear(grip_L(), f)
        continue
    tips, gaps = [], []
    frames_in, info = [], []
    for f in range(f0, f1 + 1):                                 # pass 1: shaft line and the right grip target per frame
        scene.frame_set(f)
        S = grip_L(); y = S.col[1].xyz.normalized()
        snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
        HR = armik.W(rig, 'B_R_Hand'); src_g = HR @ GCR
        yr = RGRIP_FIXED                                        # fixed spacing: a source-driven one slid the fist 0.5 m
        g = S.translation + y * yr
        frames_in.append({'snap': snap, 'wrist': g - HR.to_3x3().normalized() @ GCR, 'dir': y})
        info.append((S, y, g))
    set_act(None)
    # global elbow-plane / hand-roll choice (armik.arm_dp) with the right arm at REST in the reference snapshots: a
    # reference taken from the source arm flipped with it at the thrust (100+ deg elbow and 175 deg hand steps)
    for fr in frames_in:
        for n in ARMR:
            fr['snap'][n] = Matrix()
    ch = armik.arm_dp(rig, 'R', frames_in, AXR, twist_neutral=30.0, k_twist=0.6, k_dphi=1.5, k_dpsi=1.2)
    gk = np.exp(-0.5 * (np.arange(-3, 4) / 1.5) ** 2); gk /= gk.sum()
    sm = lambda x: np.convolve(np.concatenate([np.repeat(x[:1], 3), x, np.repeat(x[-1:], 3)]), gk, 'valid')
    phi = sm(np.array([c['phi'] for c in ch], float)); psi = sm(np.degrees(np.unwrap(np.radians([c['psi'] for c in ch]))))
    poses, KPREV = [], {}
    for i, fr in enumerate(frames_in):
        S, y, g = info[i]
        armik.apply_arm(rig, 'R', fr['snap'], fr['wrist'], AXR, y, phi[i], psi[i], ch[i]['dev'])
        R = armik.W(rig, 'B_R_Hand').to_3x3().normalized()
        armik.apply_arm(rig, 'R', fr['snap'], g - R @ GCR, AXR, y, phi[i], psi[i], ch[i]['dev'])
        gaps.append((armik.W(rig, 'B_R_Hand') @ GCR - g).length)
        poses.append({n: rig.pose.bones[n].rotation_quaternion.copy() for n in ARMR})
    print('SPEAR right arm phi range', round(float(phi.min())), round(float(phi.max())), 'psi range', round(float(psi.min())), round(float(psi.max())))
    set_act(act)
    for i, f in enumerate(range(f0, f1 + 1)):
        scene.frame_set(f)
        w = WEIGHT[i]
        base = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in ARMR}
        for n in ARMR:                                          # the solved fist eases in with the attack weight
            pb = rig.pose.bones[n]; q0 = base[n]; q = poses[i][n]
            if q0.dot(q) < 0:
                q = -q
            pb.rotation_quaternion = q0.slerp(q, w)
        bpy.context.view_layer.update()
        if 1e-3 < w < 0.999 and ARC > 0:
            # between the hanging arm and the fist on the shaft (user review 2026-10-20: a joint blend swept the right
            # forearm through the chest on the way back to the idle): the wrist and the elbow follow the blend of the
            # two poses' positions bowed ARC m out to the chest's right and forward, solved by IK, the hand turn
            # slerped
            def arm_world():
                bpy.context.view_layer.update()
                return (armik.W(rig, 'B_R_Hand').translation.copy(), armik.W(rig, 'B_R_Forearm').translation.copy(),
                        armik.W(rig, 'B_R_Hand').to_quaternion())
            for n in ARMR:
                rig.pose.bones[n].rotation_quaternion = base[n]
            Wb, Eb, Hb = arm_world()
            for n in ARMR:
                rig.pose.bones[n].rotation_quaternion = poses[i][n]
            Ws, Es, Hs = arm_world()
            for n in ARMR:                                      # the clavicle keeps the joint blend
                pb = rig.pose.bones[n]; q = poses[i][n]
                if base[n].dot(q) < 0:
                    q = -q
                pb.rotation_quaternion = base[n].slerp(q, w)
            bpy.context.view_layer.update()
            C3 = armik.W(rig, 'B_Spine2').to_3x3().normalized()
            bow = (C3 @ Vector((0.5, 0, 1))).normalized() * ARC * math.sin(math.pi * w)   # chest frame: x fwd, z right
            if Hb.dot(Hs) < 0:
                Hs = -Hs
            armik.solve(rig, 'R', Wb.lerp(Ws, w) + bow, pole=Eb.lerp(Es, w) + bow * 1.5,
                        hand_rot=Hb.slerp(Hs, w).to_matrix())
        for n in ARMR:
            pb = rig.pose.bones[n]; qk = pb.rotation_quaternion.copy()
            if n in KPREV and qk.dot(KPREV[n]) < 0:              # sign-continuous keys (in-between frames interpolate)
                qk = -qk
            KPREV[n] = qk.copy()
            pb.rotation_quaternion = qk; pb.keyframe_insert('rotation_quaternion', frame=f)
        bpy.context.view_layer.update()
        S, y, g = info[i]
        key_spear(S, f)
        tips.append(-(S.translation + y * 1.15).y)
    tips = np.array(tips); s0 = next(i for i in range(N) if WEIGHT[i] > 0.95)        # after the regrip
    k0 = s0 + int(np.argmin(tips[s0:N // 2 + 1])); k1 = k0 + int(np.argmax(tips[k0:]))
    lo, hi = tips[k0], tips[k1]; fc = next(f for f in range(k0, k1 + 1) if tips[f] >= lo + 0.95 * (hi - lo))
    t95 = lo + 0.95 * (hi - lo); fr = (fc - 1) + (t95 - tips[fc - 1]) / max(tips[fc] - tips[fc - 1], 1e-6)
    full = [gaps[i] for i in range(N) if WEIGHT[i] > 0.99]
    report = {'frames': N, 'impact_frame': round(fr, 2), 'impact_s': round(fr / 30, 4), 'tip_travel_m': round(float(hi - lo), 3),
              'drawn_back_frame': k0, 'full_reach_frame': k1, 'right_grip_gap_max_mm (full weight)': round(1000 * max(full), 1)}
    print('SPEAR attack', json.dumps(report))
json.dump(report, open(os.path.join(common.WORK, 'attack_timing.json'), 'w'), indent=1)
set_act(None)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
