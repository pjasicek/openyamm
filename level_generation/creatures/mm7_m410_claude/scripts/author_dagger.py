"""m410 attack and the dagger track (after clip_timing.py; grip_pose.json from grip_solve.py).
The native attack (m410aa..ah, then back to aa: 26 ticks, 1.625 s) draws the dagger from the left-hip sheath, raises
it, lunges into a forward thrust (ag/ah) and sheathes it again. Built here as one clip of NA frames:
- draw (frames 0..FG): Standing frame 0's body; the right wrist is solved (armik.arm_dp, global elbow plane/hand
  roll) onto the dagger's hilt in the sheath, eased in; at FG the dagger leaves the sheath for the fist;
- strike (FR0..): the body blends into the humanoid set's DaggerAttackR3 (overhead wind-up, forward lunging thrust),
  its wind-up retimed so the thrust's full reach lands at BLOW (0.87 s, native ag/ah); after the blow the recovery
  plays at REC_SPEED; the lunge is narrowed to STANCE of its foot spread and the pelvis raised by RAISE of its drop
  (two-bone leg IK, author_spear.py's rule);
- sheathe (..FS): the body blends back to Standing while the right wrist is solved onto the hilt again; at FS the
  dagger returns to the sheath, the arm eases back to the Standing pose by NA.
Dagger track: bone 'Dagger' (child of B_Pelvis, deforming, added here; the dagger mesh is skinned to it at export), keyed
in world terms in every clip: in the sheath (measured from the sheath shell P09: axis down the sheath, the crossguard at its throat;
the roll is the fist's at the draw; per frame it follows the sheath's deformed vertices, a rigid best fit (Kabsch),
as the sheath is skinned 0.75 pelvis / 0.25 left thigh) except Attack frames FG..FS-1,
where it is the fist's grip frame (grip_pose.json, axis = the handle axis, roll DAGGER_ROLL from the knuckle line).
Writes work/attack_timing.json (impact = the blow) and work/fist_weight.json (apply_grip.py FIST_WEIGHTS).
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; scene = bpy.context.scene
scene.render.fps = 30
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json')))
AXR = Vector(G['handle_axis_hand_local']).normalized(); GCR = Vector(G['handle_centre_hand_local'])
DG = json.load(open(os.path.join(common.WORK, 'dagger.json')))
ROLL = math.radians(float(os.environ.get('DAGGER_ROLL', '90')))
FG, FR0, FR1, BLOW = 10, 10, 17, 26                              # grab, R3 blend in, blow (frames at 30 fps)
REC_SPEED = float(os.environ.get('REC_SPEED', '1.5'))
STANCE, RAISE = float(os.environ.get('STANCE', '0.55')), float(os.environ.get('RAISE', '0.6'))
smooth = lambda x: x * x * (3 - 2 * min(max(x, 0.0), 1.0)) if 0 < x < 1 else (0.0 if x <= 0 else 1.0)
ARMR = ['B_R_Clavicle', 'B_R_UpperArm', 'B_R_Forearm', 'B_R_Hand']


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'
set_act(None)
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix()
bpy.context.view_layer.update()
# ---------------------------------------------------------------- the dagger bone at the sheath (rest pose)
me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
S = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])[pv == 9]
c = S.mean(0); u, sv, vt = np.linalg.svd(S - c)
ax = Vector(vt[0]); ax = -ax if ax.z > 0 else ax                 # down the sheath, toward its tip
wd = Vector(vt[1]).normalized()
proj = (S - c) @ np.array(ax)
throat = Vector(S[proj < proj.min() + 0.015].mean(0))
origin = throat - ax * DG['guard_y']                              # the crossguard rests on the throat
X = (wd - ax * wd.dot(ax)).normalized(); Z = X.cross(ax)
S_REST = Matrix((X, ax, Z)).transposed().to_4x4(); S_REST.translation = origin
PEL_REST = rig.data.bones['B_Pelvis'].matrix_local.copy()
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.get('Dagger') or rig.data.edit_bones.new('Dagger')
eb.head = origin; eb.tail = origin + ax * 0.15; eb.align_roll(Z); eb.parent = rig.data.edit_bones['B_Pelvis']; eb.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
if 'Dagger' not in body.vertex_groups:
    body.vertex_groups.new(name='Dagger')
names = [b.name for b in rig.data.bones]
print('DAGGERRIG sheath axis', [round(x, 3) for x in ax], 'throat', [round(x, 3) for x in throat], 'origin', [round(x, 3) for x in origin])


def hand_local():
    """Dagger frame in B_R_Hand space: origin at the handle centre, +Y along the handle axis, +X the knuckle line
    turned ROLL about it (axe_frame.py's rule)."""
    kn = rig.data.bones['B_R_Hand'].matrix_local.inverted() @ rig.data.bones['B_R_Finger2'].head_local
    side = kn - GCR; side = (side - AXR * side.dot(AXR)).normalized()
    sx = (side * math.cos(ROLL) + AXR.cross(side) * math.sin(ROLL)).normalized(); sz = sx.cross(AXR)
    M = Matrix((sx, AXR, sz)).transposed().to_4x4(); M.translation = GCR
    return M


MH = hand_local()
SH_IDX = np.where(pv == 9)[0]
SH_REST = np.array([tuple(body.matrix_world @ me.vertices[i].co) for i in SH_IDX])


def sheath_T():
    """Rigid transform (world) taking the rest sheath vertices onto the current deformed ones (Kabsch)."""
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    D = np.array([tuple(body.matrix_world @ m.vertices[i].co) for i in SH_IDX]); ev.to_mesh_clear()
    ca, cb = SH_REST.mean(0), D.mean(0)
    U, _, Vt = np.linalg.svd((SH_REST - ca).T @ (D - cb))
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    Rm = Vt.T @ np.diag([1, 1, d]) @ U.T
    T = Matrix(Rm.tolist()).to_4x4(); T.translation = Vector(cb - Rm @ ca)
    return T


S_SH = S_REST.copy()                                              # sheathed dagger frame at rest (roll replaced below)


def basis_int(act, f):
    set_act(act); scene.frame_set(int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def basis(act, f):
    f0 = int(math.floor(f)); t = f - f0
    A = basis_int(act, f0)
    if t < 1e-6:
        return A
    B = basis_int(act, f0 + 1); o = {}
    for n in names:
        qa, la = A[n]; qb, lb = B[n]
        if qa.dot(qb) < 0:
            qb = -qb
        o[n] = (qa.slerp(qb, t), la.lerp(lb, t))
    return o


def mix(A, B, w):
    o = {}
    for n in names:
        qa, la = A[n]; qb, lb = B[n]
        if qa.dot(qb) < 0:
            qb = -qb
        o[n] = (qa.slerp(qb, w), la.lerp(lb, w))
    return o


def apply(P):
    for n, (q, l) in P.items():
        pb = rig.pose.bones[n]; pb.rotation_quaternion = q; pb.location = l
    bpy.context.view_layer.update()


st, r3 = bpy.data.actions['Standing'], bpy.data.actions['DaggerR3']
S0 = basis(st, 0)
n_src = int(r3.frame_range[1]) + 1
# the blow in the source: the fist's furthest forward reach (the character faces -Y) in its middle 20-85 %
reach = []
for f in range(n_src):
    set_act(r3); scene.frame_set(f); reach.append(-(armik.W(rig, 'B_R_Hand') @ GCR).y)
lo_, hi_ = int(0.2 * n_src), int(0.85 * n_src)
B_SRC = lo_ + int(np.argmax(reach[lo_:hi_]))
A_SRC = 0
F_END = BLOW + int(math.ceil((n_src - 1 - B_SRC) / REC_SPEED))
FS = F_END + 3                                                   # back at the sheath
NA = FS + 9


def src_of(f):
    if f <= FR0:
        return A_SRC
    if f <= BLOW:
        return A_SRC + (B_SRC - A_SRC) * (f - FR0) / (BLOW - FR0)
    return min(B_SRC + (f - BLOW) * REC_SPEED, n_src - 1)


wR = [smooth((f - FR0) / (FR1 - FR0)) * (1 - smooth((f - (FS - 9)) / 7)) for f in range(NA)]
wI = [max(smooth((f - 1) / (FG - 1)) * (1 - smooth((f - FR0) / (FR1 - FR0))),
          smooth((f - (FS - 8)) / 8) * (1 - smooth((f - FS) / 7))) for f in range(NA)]
wF = [smooth((f - (FG - 4)) / 4) * (1 - smooth((f - FS) / 4)) for f in range(NA)]
poses = [mix(S0, basis(r3, src_of(f)), wR[f]) for f in range(NA)]
# the source flicks the dagger arm right after its thrust (79-114 deg per 1/48 s, sharper at REC_SPEED): Gaussian
# smoothing (SMOOTH_SIGMA frames) of both arms' local rotations over the strike, quaternions sign-aligned per window
SIG = float(os.environ.get('SMOOTH_SIGMA', '1.6'))
ARMS = [f'B_{sd}_{b}' for sd in 'LR' for b in ('Clavicle', 'UpperArm', 'Forearm', 'Hand')]
sm_poses = {}
for f in range(FR1, FS - 8):
    for n in ARMS:
        q0 = poses[f][n][0]; acc = Quaternion((0, 0, 0, 0)); ws = 0.0
        for j in range(-4, 5):
            g_ = min(max(f + j, FR1), FS - 9); q = poses[g_][n][0]; wj = math.exp(-0.5 * (j / SIG) ** 2)
            acc = acc + (q if q.dot(q0) >= 0 else -q) * wj; ws += wj
        sm_poses[(f, n)] = (acc * (1.0 / ws)).normalized()
for (f, n), q in sm_poses.items():
    poses[f][n] = (q, poses[f][n][1])
# ---------------------------------------------------------------- narrow and raise the lunge (author_spear.py)
LEGS = [n for n in names if any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]
set_act(None); apply(S0)
st_pz = armik.W(rig, 'B_Pelvis').translation.z
st_ank = {s: armik.W(rig, f'B_{s}_Foot').translation.copy() for s in 'LR'}
st_frot = {s: armik.W(rig, f'B_{s}_Foot').to_quaternion() for s in 'LR'}


def leg_ik(side, ankle_target, foot_rot):
    th, ca, ft = f'B_{side}_Thigh', f'B_{side}_Calf', f'B_{side}_Foot'
    Hh = armik.W(rig, th).translation; Kk = armik.W(rig, ca).translation; Aa = armik.W(rig, ft).translation
    L1, L2 = (Kk - Hh).length, (Aa - Kk).length
    T = Vector(ankle_target); d = T - Hh; dist = min(d.length, (L1 + L2) * 0.999); u_ = d.normalized()
    p = (Kk - Hh) - (Aa - Hh).normalized() * (Kk - Hh).dot((Aa - Hh).normalized())
    p = (Aa - Hh).normalized().rotation_difference(u_) @ p
    v = (p - u_ * p.dot(u_)).normalized()
    cc = max(-1, min(1, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)))
    K = Hh + L1 * (u_ * cc + v * math.sqrt(1 - cc * cc))
    q = (Kk - Hh).normalized().rotation_difference((K - Hh).normalized())
    armik.set_world(rig, th, armik.rot_world(armik.W(rig, th), q.to_matrix() @ armik.W(rig, th).to_3x3().normalized()))
    Mc = armik.W(rig, ca)
    q2 = (armik.W(rig, ft).translation - Mc.translation).normalized().rotation_difference((Hh + u_ * dist - Mc.translation).normalized())
    armik.set_world(rig, ca, armik.rot_world(Mc, q2.to_matrix() @ Mc.to_3x3().normalized()))
    armik.set_world(rig, ft, armik.rot_world(armik.W(rig, ft), foot_rot.to_matrix()))


raised = []
for f, P in enumerate(poses):
    if wR[f] <= 0:
        continue
    apply(P)
    pel = armik.W(rig, 'B_Pelvis'); dz = max(0.0, st_pz - pel.translation.z) * RAISE
    ank = {s: st_ank[s].lerp(armik.W(rig, f'B_{s}_Foot').translation, STANCE) for s in 'LR'}
    frot = {s: st_frot[s].slerp(armik.W(rig, f'B_{s}_Foot').to_quaternion(), STANCE) for s in 'LR'}
    M = pel.copy(); M.translation.z += dz
    mid = (armik.W(rig, 'B_L_Foot').translation + armik.W(rig, 'B_R_Foot').translation) / 2
    sh = (ank['L'] + ank['R']) / 2 - mid
    M.translation.x += sh.x; M.translation.y += sh.y
    armik.set_world(rig, 'B_Pelvis', M)
    for s in 'LR':
        leg_ik(s, ank[s], frot[s])
    for n in ['B_Pelvis'] + LEGS:
        pb = rig.pose.bones[n]; P[n] = (pb.rotation_quaternion.copy(), pb.location.copy())
    raised.append(dz)
# ---------------------------------------------------------------- right wrist onto the hilt (draw and sheathe)
segs = [(1, FR1), (FS - 8, NA - 1)]
# elbow plane: the solver's default -90..90 put the elbow at the midline, inside the torso, for the cross-body reach;
# 110..250 swings it forward and out to the right (PHI_SCAN=1 prints the elbow per angle at the grab)
PHIS = range(*[int(x) for x in os.environ.get('PHIS', '110,251,10').split(',')])


def solve_segment(f0, f1, roll_frame=None):
    frames_in, keep = [], []
    for f in range(f0, f1 + 1):
        if wI[f] <= 0:
            continue
        apply(poses[f])
        D = sheath_T() @ S_SH
        HR = armik.W(rig, 'B_R_Hand')
        snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
        for n in ARMR:
            snap[n] = Matrix()                                    # reference arm at rest (m218 lesson: no source flips)
        frames_in.append({'snap': snap, 'wrist': D.translation - HR.to_3x3().normalized() @ GCR, 'dir': D.col[1].xyz.normalized(),
                          'D': D})
        keep.append(f)
    if os.environ.get('PHI_SCAN') and f0 < FR1:                   # elbow position per elbow-plane angle at the grab
        fr = frames_in[keep.index(FG)]
        for n, m in fr['snap'].items():
            rig.pose.bones[n].matrix_basis = m
        bpy.context.view_layer.update()
        S_ = armik.W(rig, 'B_R_UpperArm').translation.copy(); E0 = armik.W(rig, 'B_R_Forearm').translation.copy(); W0 = armik.W(rig, 'B_R_Hand').translation.copy()
        T_ = Vector(fr['wrist']); u_ = (T_ - S_).normalized(); r_ = (W0 - S_).normalized(); p0 = (E0 - S_) - r_ * (E0 - S_).dot(r_)
        p0 = (r_.rotation_difference(u_) @ p0); p0 = (p0 - u_ * p0.dot(u_)).normalized()
        for phi in range(-180, 180, 20):
            for n, m in fr['snap'].items():
                rig.pose.bones[n].matrix_basis = m
            bpy.context.view_layer.update()
            armik.solve(rig, 'R', T_, pole=S_ + Quaternion(u_, math.radians(phi)) @ p0)
            E = armik.W(rig, 'B_R_Forearm').translation
            print('PHISCAN', phi, 'elbow', [round(x, 3) for x in E], 'shoulder', [round(x, 3) for x in S_])
    ch = armik.arm_dp(rig, 'R', frames_in, AXR, phis=PHIS, twist_neutral=30.0, k_twist=0.6, k_dphi=1.5, k_dpsi=1.2)
    gk = np.exp(-0.5 * (np.arange(-3, 4) / 1.5) ** 2); gk /= gk.sum()
    sm = lambda x: np.convolve(np.concatenate([np.repeat(x[:1], 3), x, np.repeat(x[-1:], 3)]), gk, 'valid')
    phi = sm(np.array([c_['phi'] for c_ in ch], float)); psi = sm(np.degrees(np.unwrap(np.radians([c_['psi'] for c_ in ch]))))
    res = {}
    for i, f in enumerate(keep):
        fr = frames_in[i]; apply(poses[f])
        armik.apply_arm(rig, 'R', fr['snap'], fr['wrist'], AXR, fr['dir'], phi[i], psi[i], ch[i]['dev'])
        R_ = armik.W(rig, 'B_R_Hand').to_3x3().normalized()
        armik.apply_arm(rig, 'R', fr['snap'], fr['D'].translation - R_ @ GCR, AXR, fr['dir'], phi[i], psi[i], ch[i]['dev'])
        res[f] = ({n: rig.pose.bones[n].rotation_quaternion.copy() for n in ARMR}, (armik.W(rig, 'B_R_Hand') @ GCR - fr['D'].translation).length)
    return res


draw = solve_segment(*segs[0])
# the sheathed dagger's roll = the fist's at the grab (only its hilt shows; no snap when it leaves the sheath)
apply(poses[FG]); P_ = poses[FG]
for n, q in draw[FG][0].items():
    P_[n] = (q, P_[n][1])
apply(P_)
S_SH = sheath_T().inverted() @ (armik.W(rig, 'B_R_Hand') @ MH)
sheathe = solve_segment(*segs[1])
gaps = []
for f in range(NA):
    sol = draw.get(f) or sheathe.get(f)
    if sol is None:
        continue
    P = poses[f]
    for n in ARMR:
        q0, l0 = P[n]; q1 = sol[0][n]
        if q0.dot(q1) < 0:
            q1 = -q1
        P[n] = (q0.slerp(q1, wI[f]), l0)
    if wI[f] > 0.99:
        gaps.append(sol[1])
# ---------------------------------------------------------------- floor pass: the lowest sole at Standing's level
# (the narrowed, raised lunge left the feet 1.8-4.9 cm under the floor); the pelvis carries the arms and the sheath, so
# the hand on the hilt is kept
vgn = [g.name for g in body.vertex_groups]
FEETV = np.array([sum(e.weight for e in v.groups if vgn[e.group] in ('B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0')) > 0.5 for v in me.vertices])


def lowest(P):
    apply(P)
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    z = np.array([(body.matrix_world @ m.vertices[i].co).z for i in np.where(FEETV)[0]]); ev.to_mesh_clear()
    return float(z.min())


z_st = lowest(S0)
lows = np.array([lowest(P) for P in poses])
pad_ = np.concatenate([np.repeat(lows[:1], 3), lows, np.repeat(lows[-1:], 3)])
gk2 = np.exp(-0.5 * (np.arange(-3, 4) / 1.0) ** 2); gk2 /= gk2.sum()
dzs = z_st - np.convolve(pad_, gk2, 'valid')
for f, P in enumerate(poses):
    apply(P)
    M = armik.W(rig, 'B_Pelvis'); M.translation.z += float(dzs[f]); armik.set_world(rig, 'B_Pelvis', M)
    P['B_Pelvis'] = (rig.pose.bones['B_Pelvis'].rotation_quaternion.copy(), rig.pose.bones['B_Pelvis'].location.copy())
print('DAGGER floor: lowest sole before', round(100 * (lows.min() - z_st), 1), '..', round(100 * (lows.max() - z_st), 1),
      'cm from Standing, lift', round(100 * dzs.min(), 1), '..', round(100 * dzs.max(), 1), 'cm')
# ---------------------------------------------------------------- write Attack and the dagger track
if 'Attack' in bpy.data.actions:
    bpy.data.actions.remove(bpy.data.actions['Attack'])
att = bpy.data.actions.new('Attack'); att.use_fake_user = True
set_act(att)
prev = {}
for f, P in enumerate(poses):
    for n, (q, l) in P.items():
        if n == 'Dagger':
            continue
        pb = rig.pose.bones[n]
        if n in prev and q.dot(prev[n]) < 0:
            q = -q
        prev[n] = q
        pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
        if n == 'B_Pelvis':
            pb.location = l; pb.keyframe_insert('location', frame=f)
att.use_frame_range = True; att.frame_start, att.frame_end = 0, NA - 1
LASTQ = {}


def key_dagger(Mw, f, an):
    pb = rig.pose.bones['Dagger']; pb.rotation_mode = 'QUATERNION'
    pb.matrix = rig.matrix_world.inverted() @ Mw; bpy.context.view_layer.update()
    q = LASTQ.get(an)
    if q is not None and pb.rotation_quaternion.dot(q) < 0:
        pb.rotation_quaternion = -pb.rotation_quaternion
    LASTQ[an] = pb.rotation_quaternion.copy()
    pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)


tips = []
for act in [a for a in bpy.data.actions if a.use_fake_user and a.name not in ('GripRef', 'DaggerR3')]:
    set_act(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        inhand = act.name == 'Attack' and FG <= f < FS
        Mw = armik.W(rig, 'B_R_Hand') @ MH if inhand else sheath_T() @ S_SH
        key_dagger(Mw, f, act.name)
        if act.name == 'Attack':
            tips.append(-(Mw @ Vector((0, DG['tip_y'], 0))).y)
set_act(None)
tips = np.array(tips)
k = int(np.argmax(tips[FR1:FS])) + FR1
lo = tips[FR1:k + 1].min(); t95 = lo + 0.95 * (tips[k] - lo)
fc = next(f for f in range(FR1, k + 1) if tips[f] >= t95)
impact = ((fc - 1) + (t95 - tips[fc - 1]) / max(tips[fc] - tips[fc - 1], 1e-6)) / 30
report = {'frames': NA, 'seconds': round(NA / 30, 3), 'src_blow_frame': B_SRC, 'src_frames': n_src, 'grab_frame': FG,
          'sheathe_frame': FS, 'blow_frame': BLOW, 'impact_s': round(impact, 4), 'tip_reach_m': round(float(tips[k] - lo), 3),
          'hilt_gap_mm_max': round(1000 * max(gaps), 1) if gaps else None, 'pelvis_raised_cm_max': round(100 * max(raised), 1) if raised else 0}
print('DAGGER attack', json.dumps(report))
json.dump(report, open(os.path.join(common.WORK, 'attack_timing.json'), 'w'), indent=1)
json.dump({'Attack': [round(w, 4) for w in wF]}, open(os.path.join(common.WORK, 'fist_weight.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
