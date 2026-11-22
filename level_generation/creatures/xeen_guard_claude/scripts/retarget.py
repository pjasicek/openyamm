"""Retarget the stand-in's clips (mm8_m592, D-19) onto Guard_Rig: work/rig_v1.blend -> work/anim_v1.blend.

Reference pose S0 = the source's Standing frame 0. For every bone b the source's world rotation change since S0,
D_b(t) = Rs_b(t) Rs_b(S0)^-1, is applied to our pose at S0:
  W_b(t) = D_b(t) Q_b R_b                     (R_b = our rest frame, Q_b = our standing posture)
- limbs (upper arm, forearm, hand, thigh, calf, foot): Q_b maps our segment (direction + hinge axis; hand: direction
  + palm normal; foot: direction + up) onto the source's at S0, so the arms hang and swing as the source's do;
- trunk (pelvis, spines, clavicles): Q = identity plus POSTURE pitch (degrees forward, cumulative up the chain);
  neck and head (the dome) follow the chest with only HEAD_K of the source's own head motion;
- positions: the pelvis moves by K x the source pelvis' displacement since S0 from our rest pelvis lowered so the knees
  bend as much as the source's at S0; the legs are two-bone IK to our rest ankles plus K x the source ankles'
  displacement (the feet plant where the source's plant), knee pole from the FK thigh;
- floor: a foot whose sole dips under z 0 lifts its ankle target; a death lowers/raises the whole body so the corpse
  rests on the floor (CORPSE ramp over the clip's second half); living clips never sink.
Clips: CLIPS (ours <- source). Dead = Death's last pose for 1 s. Prints per-clip reach deficit and floor numbers."""
import bpy, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CLIPS = [('Standing', 'Standing'), ('Walking', 'Walk2'), ('Running', 'Jog'), ('Attack', 'Attack'), ('Hit', 'Hit'),
         ('Death', 'Death'), ('Fidget', 'Fidget')]
POSTURE = {'B_Pelvis': 0.0, 'B_Spine': 4.0, 'B_Spine1': 4.0, 'B_Spine2': 6.0}   # forward pitch, degrees per joint
HEAD_K = 0.5
CLAV_K = 0.5      # share of the source's own clavicle motion (its shrugs turned the pauldrons' cut faces out)
POLE_OUT = 0.35
K_H = 0.9        # horizontal travel of the pelvis and feet: our legs are shorter for the body than the source's
SIDES = ('L', 'R')
LIMBS = ['UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot']
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = set(a)

_m = os.path.join(HERE, 'work', 'rig_uv.blend')
bpy.ops.wm.open_mainfile(filepath=_m if os.path.exists(_m) else os.path.join(HERE, 'work', 'rig_v1.blend'))
sc = bpy.context.scene
sc.render.fps = 30; sc.render.fps_base = 1
rig = bpy.data.objects['Guard_Rig']; mesh = bpy.data.objects['Guard']
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, 'assets_source/worlds/mm8/models/mm8_m592.glb'))
src = next(o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE')
for o in [o for o in bpy.data.objects if o not in before and o.type == 'MESH']:
    bpy.data.objects.remove(o, do_unlink=True)
src.name = 'SrcRig'
SRC_ACTIONS = {a.name: a for a in bpy.data.actions}
for _n, _a in SRC_ACTIONS.items():
    _a.name = 'SRC_' + _n
if src.animation_data is None:
    src.animation_data_create()

BONES = [b.name for b in rig.data.bones if not b.name.startswith('Socket')]
R = {b: rig.data.bones[b].matrix_local.copy() for b in BONES}
PARENT = {b: (rig.data.bones[b].parent.name if rig.data.bones[b].parent else None) for b in BONES}
ORDER = []
def _add(b):
    if b in ORDER: return
    if PARENT[b]: _add(PARENT[b])
    ORDER.append(b)
for b in BONES: _add(b)


def set_src(action, frame):
    src.animation_data.action = action
    if len(getattr(action, 'slots', [])):
        src.animation_data.action_slot = action.slots[0]
    sc.frame_set(frame)
    return {pb.name: (src.matrix_world @ pb.matrix).copy() for pb in src.pose.bones}


def rot(m):
    return m.to_quaternion()


def basis(d, h):
    d = d.normalized(); h = (h - d * h.dot(d)).normalized(); t = d.cross(h)
    return Matrix((d, h, t)).transposed()       # columns d, h, t


S0 = set_src(SRC_ACTIONS['Standing'], 0)


def sj(M, b):
    return M[b].translation.copy()


def hinge(p0, p1, p2, prior):
    h = (p1 - p0).cross(p2 - p1)
    if (p1 - p0).angle(p2 - p1) < math.radians(20):     # nearly straight: the cross product is noise
        h = prior
    h = h.normalized()
    return h if h.dot(prior) >= 0 else -h


def our(b):
    return R[b].translation.copy()


Q = {}
FWD = Vector((0, -1, 0)); BACK = Vector((0, 1, 0)); UP = Vector((0, 0, 1))
for s in SIDES:
    pre = f'B_{s}_'
    # arms: hinge = cross(upper, forearm) (forearm bends forward); our A-pose prior cross(upper dir, forward)
    S, E, W = our(pre + 'UpperArm'), our(pre + 'Forearm'), our(pre + 'Hand')
    ho = hinge(S, E, W, (E - S).cross(FWD))
    sS, sE, sW = sj(S0, pre + 'UpperArm'), sj(S0, pre + 'Forearm'), sj(S0, pre + 'Hand')
    hs = hinge(sS, sE, sW, (sE - sS).cross(FWD))
    Q[pre + 'UpperArm'] = basis(sE - sS, hs) @ basis(E - S, ho).transposed()
    Q[pre + 'Forearm'] = basis(sW - sE, hs) @ basis(W - E, ho).transposed()
    # hand: direction wrist -> finger bases, palm normal (ours: the hand plate's thinnest axis, toward the front)
    fing = [sj(S0, pre + f'Finger{i}') for i in range(3)]
    fc = sum(fing, Vector()) / 3
    tips = [S0[pre + f'Finger{i}'] @ Vector((0, 0.1, 0)) for i in range(3)]
    ns = (fing[1] - fing[0]).cross(fing[2] - fing[0]).normalized()
    if ns.dot(sum(tips, Vector()) / 3 - fc) < 0: ns = -ns
    vg = mesh.vertex_groups[pre + 'Hand'].index
    hv = np.array([v.co[:] for v in mesh.data.vertices if any(g.group == vg for g in v.groups)])
    c = hv.mean(0); u, sv, vt = np.linalg.svd(hv - c, full_matrices=False)
    no = Vector(vt[2])
    if no.dot(FWD) < 0: no = -no
    he = our(pre + 'Hand') + (R[pre + 'Hand'] @ Vector((0, 1, 0)) - our(pre + 'Hand')).normalized() * 0.1
    # the hand keeps its rest relation to the forearm at S0 (the source's palm convention differs: matching it turned
    # the wrist 150 degrees); the source's wrist motion since S0 comes in through D
    Q[pre + 'Hand'] = Q[pre + 'Forearm']
    # legs: hinge prior cross(dir, back) (the shin swings back)
    H, K, A = our(pre + 'Thigh'), our(pre + 'Calf'), our(pre + 'Foot')
    hol = hinge(H, K, A, (K - H).cross(BACK))
    sH, sK, sA = sj(S0, pre + 'Thigh'), sj(S0, pre + 'Calf'), sj(S0, pre + 'Foot')
    hsl = hinge(sH, sK, sA, (sK - sH).cross(BACK))
    Q[pre + 'Thigh'] = basis(sK - sH, hsl) @ basis(K - H, hol).transposed()
    Q[pre + 'Calf'] = basis(sA - sK, hsl) @ basis(A - K, hol).transposed()
    sT = sj(S0, pre + 'Toe0'); T = R[pre + 'Foot'] @ Vector((0, rig.data.bones[pre + 'Foot'].length, 0))
    d_s = sT - sA; d_s.z = 0; d_o = T - A; d_o.z = 0
    Q[pre + 'Foot'] = basis(d_s, UP) @ basis(d_o, UP).transposed()
    print('HINGE', s, 'arm ours', [round(x, 2) for x in ho], 'src', [round(x, 2) for x in hs],
          'leg ours', [round(x, 2) for x in hol], 'src', [round(x, 2) for x in hsl])
    print('PALM', s, 'ours', [round(x, 2) for x in no], 'src', [round(x, 2) for x in ns])
cum = 0.0
for b in ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2']:
    cum += POSTURE[b]
    Q[b] = Matrix.Rotation(math.radians(cum), 3, 'X')       # +X rotation pitches the top toward -Y (forward)
for b in ['B_Neck', 'B_Head', 'B_L_Clavicle', 'B_R_Clavicle']:
    Q[b] = Q['B_Spine2'].copy()
# arms: our A-pose (hands forward of the hips, claws spread, as the native sprite holds them) is the standing pose;
# the source's arm motion comes in through D. Matching the source's long hanging arms pushed our big hands far out.
for s in SIDES:
    for part in ('UpperArm', 'Forearm', 'Hand'):
        Q[f'B_{s}_{part}'] = Matrix.Identity(3)
Q = {b: m.to_quaternion() for b, m in Q.items()}

# lengths, K, the standing drop
la = {s: (our(f'B_{s}_Calf') - our(f'B_{s}_Thigh')).length for s in SIDES}
lb = {s: (our(f'B_{s}_Foot') - our(f'B_{s}_Calf')).length for s in SIDES}
sla = (sj(S0, 'B_L_Calf') - sj(S0, 'B_L_Thigh')).length; slb = (sj(S0, 'B_L_Foot') - sj(S0, 'B_L_Calf')).length
K = (la['L'] + lb['L']) / (sla + slb)
th = (sj(S0, 'B_L_Calf') - sj(S0, 'B_L_Thigh')).angle(sj(S0, 'B_L_Foot') - sj(S0, 'B_L_Calf'))
dt = math.sqrt(la['L'] ** 2 + lb['L'] ** 2 + 2 * la['L'] * lb['L'] * math.cos(th))
H, A = our('B_L_Thigh'), our('B_L_Foot')
dz = H.z - A.z; dxy = math.hypot(H.x - A.x, H.y - A.y)
drop = dz - math.sqrt(max(dt * dt - dxy * dxy, 0))
print('K', round(K, 3), 'source knee bend', round(math.degrees(th), 1), 'pelvis drop', round(drop, 3))
P0 = our('B_Pelvis') - Vector((0, 0, drop))

# vertices per bone (rest) for the floor and the gates
me = mesh.data
gi = {g.index: g.name for g in mesh.vertex_groups}
VB = {}
for v in me.vertices:
    VB.setdefault(gi[v.groups[0].group], []).append(v.co[:])
VB = {b: np.array(p) for b, p in VB.items()}
RINV = {b: R[b].inverted() for b in BONES}


def lowest(Wm, bones):
    z = 1e9
    for b in bones:
        if b in VB:
            M = np.array(Wm[b] @ RINV[b])
            p = VB[b] @ M[:3, :3].T + M[:3, 3]
            z = min(z, p[:, 2].min())
    return z


def hk(v):
    return Vector((v.x * K * K_H * hk.travel, v.y * K * K_H * hk.travel, v.z * K))


hk.travel = 1.0


def mat(q, t):
    m = q.to_matrix().to_4x4(); m.translation = t; return m


def child_head(Wp, p, c):
    return Wp @ (RINV[p] @ our(c))


def solve(M, Ms0, foot_lift, body_dz):
    """World matrices of our bones for one source frame."""
    W = {}
    D = {b: rot(M[b]) @ rot(Ms0[b]).inverted() for b in M}
    for b in ORDER:
        qb = Q[b] if b not in TRUNK or solve.posture >= 1.0 else Quaternion().slerp(Q[b], solve.posture)
        if b in ('B_Neck', 'B_Head', 'B_L_Clavicle', 'B_R_Clavicle'):
            full = D[b] @ qb @ rot(R[b])
            rigid = D['B_Spine2'] @ qb @ rot(R[b])
            q = rigid.slerp(full, HEAD_K if 'Clavicle' not in b else CLAV_K)
        else:
            q = D[b] @ qb @ rot(R[b])
        if b == 'B_Pelvis':
            t = P0 + hk(sj(M, 'B_Pelvis') - sj(Ms0, 'B_Pelvis')) + Vector((0, 0, body_dz))
        else:
            t = child_head(W[PARENT[b]], PARENT[b], b)
        W[b] = mat(q, t)
        if b.endswith('_Thigh'):
            s = b[2]
            # IK: ankle target, knee pole from the FK thigh
            hip = t
            tgt = our(f'B_{s}_Foot') + hk(sj(M, f'B_{s}_Foot') - sj(Ms0, f'B_{s}_Foot')) \
                + Vector((0, 0, foot_lift.get(s, 0.0)))
            a_, b_ = la[s], lb[s]
            dvec = tgt - hip; dist = dvec.length
            short = max(0.0, dist - (a_ + b_) * 0.999)
            dist = min(dist, (a_ + b_) * 0.999); dn = dvec.normalized()
            kfk = W[b] @ (RINV[b] @ our(f'B_{s}_Calf'))
            # knee pole: forward and a little out in the pelvis frame (the native's bowed knees); the FK thigh's own
            # knee direction swung the knee 30 cm out in the walk's swing and snapped it back at the landing
            side = 1.0 if s == 'L' else -1.0
            pole = W['B_Pelvis'].to_3x3() @ (rot(R['B_Pelvis']).inverted().to_matrix() @ Vector((POLE_OUT * side, -1.0, 0.0)))
            pole = (pole - dn * pole.dot(dn)).normalized()
            ca = (a_ * a_ + dist * dist - b_ * b_) / (2 * a_ * dist)
            ang = math.acos(max(-1, min(1, ca)))
            knee = hip + (dn * math.cos(ang) + pole * math.sin(ang)) * a_
            dfk = (kfk - hip).normalized()
            q_ik = dfk.rotation_difference((knee - hip).normalized()) @ q
            # a falling death hands the legs over to plain FK on our own wide stance (no Q: the source's narrow
            # stance crossed our big boots)
            q_fk = D[b] @ rot(R[b])
            W[b] = mat(q_ik.slerp(q_fk, solve.fkw) if solve.fkw > 0 else q_ik, hip)
            if solve.fkw == 0:
                solve.short[s] = max(solve.short.get(s, 0.0), short); solve.cur_short[s] = short
            solve.ankle[s] = hip + dn * dist
        elif b.endswith('_Calf'):
            s = b[2]
            knee = t
            afk = mat(q, knee) @ (RINV[b] @ our(f'B_{s}_Foot'))
            q_ik = (afk - knee).normalized().rotation_difference((solve.ankle[s] - knee).normalized()) @ q
            q_fk = D[b] @ rot(R[b])
            W[b] = mat(q_ik.slerp(q_fk, solve.fkw) if solve.fkw > 0 else q_ik, knee)
    return W


solve.short = {}; solve.knee = {}; solve.ankle = {}; solve.fk = False; solve.cur_short = {}; solve.posture = 1.0; solve.fkw = 0.0
TRUNK = ('B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head', 'B_L_Clavicle', 'B_R_Clavicle')


def pose_frame(M, Ms0, mode, dz_fixed=None):
    """Living clips: legs that cannot reach lower the pelvis; a sole under the floor lifts its ankle target; walks and
    idles keep one foot on the floor (both targets lowered); anything else under the floor raises the pelvis."""
    lift = {}; dz = 0.0 if dz_fixed is None else dz_fixed
    nonfeet = [b for b in BONES if not b.endswith('_Foot')]
    for it in range(8):
        W = solve(M, Ms0, lift, dz)
        changed = False
        sh = max(solve.cur_short.values()) if solve.cur_short else 0.0
        if sh > 1e-4 and dz_fixed is None:
            dz -= sh; changed = True
        feet = {s: lowest(W, [f'B_{s}_Foot']) for s in SIDES}
        for s in SIDES:
            if feet[s] < -1e-4:
                lift[s] = lift.get(s, 0.0) - feet[s]; changed = True
        if pose_frame.ground and min(feet.values()) > 1e-4:
            m = min(feet.values())
            for s in SIDES:
                lift[s] = lift.get(s, 0.0) - m
            changed = True
        zl = lowest(W, nonfeet)
        if zl < -1e-4 and dz_fixed is None:
            dz -= zl; changed = True
        if not changed:
            break
    W = solve(M, Ms0, lift, dz)
    return W, dz, lift


pose_frame.ground = False


def key(W, frame):
    for b in ORDER:
        pb = rig.pose.bones[b]
        if PARENT[b]:
            local = (R[PARENT[b]].inverted() @ R[b]).inverted() @ (W[PARENT[b]].inverted() @ W[b])
        else:
            local = R[b].inverted() @ W[b]
        loc, q, _ = local.decompose()
        pb.rotation_mode = 'QUATERNION'
        prev = key.prev.get(b)
        if prev is not None and prev.dot(q) < 0:
            q = -q
        key.prev[b] = q
        pb.rotation_quaternion = q; pb.location = loc; pb.scale = (1, 1, 1)
        pb.keyframe_insert('rotation_quaternion', frame=frame)
        pb.keyframe_insert('location', frame=frame)


key.prev = {}
if rig.animation_data is None:
    rig.animation_data_create()
results = {}
for ours, sname in CLIPS:
    if ONLY and ours not in ONLY:
        continue
    sa = SRC_ACTIONS[sname]
    n = int(round(sa.frame_range[1]))
    old = bpy.data.actions.get(ours)
    if old and old is not sa:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(ours); act.use_fake_user = True
    rig.animation_data.action = act
    key.prev = {}; solve.short = {}
    mode = 'death' if ours == 'Death' else 'live'
    pose_frame.ground = ours in ('Standing', 'Walking', 'Fidget', 'Hit', 'Attack')
    hk.travel = 0.5 if mode == 'death' else 0.9 if ours == 'Walking' else 1.0   # a far-travelling death leaves the
    # corpse off its spot; the walk's long steps over-reached our legs (the pelvis dipped 13 cm)
    frames = [set_src(sa, f) for f in range(n + 1)]
    dz_plan = None
    if mode == 'live':
        # first pass: the pelvis drop each frame needs (legs that cannot reach, parts under the floor); then a
        # 5-frame minimum (the lower value wins, so the legs still reach) and a gentle blur, wrapped on loops: the
        # per-frame drop jumped 9 cm in one frame at the walk's heel strike
        req = np.array([pose_frame(M, S0, mode)[1] for M in frames])
        loop = ours in ('Standing', 'Walking', 'Running')
        pad = 4
        ext = np.concatenate([req[-pad - 1:-1], req, req[1:pad + 1]]) if loop else np.pad(req, pad, mode='edge')
        mn = np.array([ext[i - 2:i + 3].min() for i in range(2, len(ext) - 2)])
        mn = np.pad(mn, 2, mode='edge')
        kern = np.exp(-0.5 * (np.arange(-3, 4) / 1.2) ** 2); kern /= kern.sum()
        sm = np.convolve(mn, kern, mode='same')
        dz_plan = sm[pad:pad + len(req)]
        if loop:
            dz_plan[-1] = dz_plan[0]
        print('DZPLAN', ours, 'req cm', np.round(req * 100, 1).tolist(), 'plan cm', np.round(dz_plan * 100, 1).tolist())
    corpse = 0.0
    dzs = []; lows = []
    for f, M in enumerate(frames):
        if mode == 'death':
            ramp = min(1.0, max(0.0, (f / n - 0.5) / 0.4))
            fall = min(1.0, max(0.0, (f / n - 0.15) / 0.45))
            solve.posture = 1.0 - fall * fall * (3 - 2 * fall)     # the forward hunch eases out as it falls back
            fk = min(1.0, max(0.0, (f / n - 0.08) / 0.32))
            solve.fkw = fk * fk * (3 - 2 * fk)
            # end: the corpse's lowest point on the floor; before: never under it
            W0 = solve(M, S0, {}, 0.0)
            zl = lowest(W0, BONES)
            g = min(1.0, max(0.0, (f / n - 0.1) / 0.2))
            dz = -zl if (zl < 0 or ramp >= 1.0) else -zl * max(ramp, g * 0.85)
            lift = {}
            W = solve(M, S0, lift, dz)
            for s in SIDES:
                zf = lowest(W, [f'B_{s}_Foot'])
                if zf < -1e-4:
                    lift[s] = -zf
            W = solve(M, S0, lift, dz)
        else:
            W, dz, lift = pose_frame(M, S0, mode, dz_fixed=None if dz_plan is None else dz_plan[f])
        dzs.append(dz); lows.append(lowest(W, BONES))
        key(W, f)
    solve.posture = 1.0; solve.fkw = 0.0
    rig.animation_data.action = act
    results[ours] = {'frames': n + 1, 'seconds': n / 30, 'short_cm': {s: round(v * 100, 2) for s, v in solve.short.items()},
                     'body_dz_cm': [round(min(dzs) * 100, 2), round(max(dzs) * 100, 2)],
                     'lowest_cm': [round(min(lows) * 100, 2), round(max(lows) * 100, 2)]}
    print('CLIP', ours, '<-', sname, results[ours])
    if ours == 'Death':
        last = W
        dead = bpy.data.actions.get('Dead')
        if dead: bpy.data.actions.remove(dead)
        dact = bpy.data.actions.new('Dead'); dact.use_fake_user = True
        rig.animation_data.action = dact
        key.prev = {}
        key(last, 0); key(last, 30)
        print('CLIP Dead (Death last pose, 1 s)')
for ob in [src]:
    bpy.data.objects.remove(ob, do_unlink=True)
for a_ in list(SRC_ACTIONS.values()):
    bpy.data.actions.remove(a_)
rig.animation_data.action = bpy.data.actions['Standing']
json.dump(results, open(os.path.join(HERE, 'work', 'retarget_report.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED anim_v1.blend', [a_.name for a_ in bpy.data.actions])
