"""Author a full-body Walking for the MM8 Lizardman Warrior on the installed GLB and write it in place.

Usage: blender -b -P author_walk.py -- <in.glb> <out.glb> [report.json]
Only the Walking clip's 193-key channels change (same key times, 0.8 s); every other clip, the geometry, skin,
LODs and variants stay byte-identical.

Upper body: the installed Walking is the source sword walk (2HandSwordWalk) damped by posture_timing.py (spine
chain 35 %, pelvis rotation 30 %); those factors are undone (quaternion powers) and a gain applied, so the hips turn
and roll with the stride and the chest counter-turns as in the source. Clavicles, arms, hands and fingers keep their
installed locals, so the two-hand grip is unchanged; the arms ride on the chest and get a small common bounce about
the shoulder line. The head is stabilised toward its cycle mean with a slight nod.
Legs: new foot plan at full stride with heel strike, flat stance, heel-off roll about the ball and a lifted swing,
solved by two-bone IK; the toes stay flat on the floor while the heel rises. The pelvis is crouched slightly, bobs
twice per cycle (lowest just after each contact), sways toward the stance foot and is lowered further only where a
leg would otherwise overreach. Timing follows the source: left contact 0.79, right 0.29 of the cycle.
Tail: installed sway plus a lagging counter-swing to the stronger hip turn. Loincloth: the build's leading-thigh
rule (finish_walk.py)."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from glb_io import Glb
from gltf_pose import GltfPose

args = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = args[0], args[1]
REPORT = args[2] if len(args) > 2 else None
E = lambda k, d: float(os.environ.get(k, d))
STRIDE = E('WALK_STRIDE', 1.45)        # m per cycle
CROUCH = E('WALK_CROUCH', 0.03)        # m below the standing pelvis height (mean)
BOB = E('WALK_BOB', 0.022)             # m amplitude (range 2x)
SWAY = E('WALK_SWAY', 0.018)           # m toward the stance foot
SURGE = E('WALK_SURGE', 0.008)         # m forward-back
GP = E('WALK_PELVIS_GAIN', 0.8)        # fraction of the source pelvis rotation
GS = E('WALK_SPINE_GAIN', 0.85)        # fraction of the source spine rotation
HEAD_STAB = E('WALK_HEAD_STAB', 0.7)   # 0 = head follows the chest, 1 = fixed at its cycle mean
NOD = E('WALK_NOD_DEG', 1.5)
THETA_C = math.radians(E('WALK_HEEL_DEG', 9))    # toe-up at heel strike
THETA_O = math.radians(E('WALK_TOEOFF_DEG', 20))  # heel-up at toe-off
LIFT = E('WALK_LIFT', 0.045)           # m extra swing lift of the ankle
LIFT_SKEW = E('WALK_LIFT_SKEW', 0.85)   # <1 moves the lift peak earlier in the swing
DUTY = E('WALK_DUTY', 0.62)
PAD_BACK = E('WALK_PAD_BACK', 0.0)     # roll pivot behind the toe tips (m)
ARM_BOUNCE = math.radians(E('WALK_ARM_BOUNCE_DEG', 2.0))
TAIL_COUNTER = E('WALK_TAIL_COUNTER', 0.5)
LEAN_GAIN = E('WALK_LEAN_GAIN', 1.3)     # mean posture relative to the installed walk's
CONTACT = {'L': 0.79, 'R': 0.29}
T_CLIP = 0.8

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
scene = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = max((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: len(o.data.polygons))
P = rig.pose.bones
fps = scene.render.fps / scene.render.fps_base
acts = {a.name.split('|')[-1]: a for a in bpy.data.actions}
g = Glb(SRC); gp = GltfPose(g.json, rig)
walk = g.animation('Walking')
lin_input = next(s['input'] for s in walk['samplers'] if g.json['accessors'][s['input']]['count'] > 2)
times = g.read(lin_input)[:, 0]
N = len(times)
upd = bpy.context.view_layer.update


def set_action(name):
    a = acts[name]; rig.animation_data.action = a; rig.animation_data.action_slot = a.slots[0]
    return a


def goto(name, t):
    a = set_action(name); f = a.frame_range[0] + t * fps
    scene.frame_set(int(f), subframe=f % 1); upd()


def qpow(q, e):
    q = q.copy()
    if q.w < 0:
        q.negate()
    axis, ang = q.to_axis_angle()
    return Quaternion(axis, ang * e)


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def minjerk(x):
    x = min(1.0, max(0.0, x)); return x ** 3 * (10 - 15 * x + 6 * x * x)


def W(n):
    return P[n].matrix.copy()


def set_W(n, M):
    P[n].matrix = M; upd()


def rot_about(M, R3, pivot):
    """World matrix M rotated by R3 about the world point pivot."""
    out = M.copy()
    out.translation = pivot + R3 @ (M.translation - pivot)
    out = Matrix.Translation(out.translation) @ (R3 @ M.to_3x3()).to_4x4()
    return out


# ---- reference pose: Standing frame 0 -----------------------------------------------------------------------
goto('Standing', 0.0)
stand = {n: W(n) for n in P.keys()}
groups = [x.name for x in body.vertex_groups]
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
co = np.array([(body.matrix_world @ v.co)[:] for v in m.vertices]); ev.to_mesh_clear()
foot = {}
for s in 'LR':
    wsum = np.zeros(len(co))
    for v in body.data.vertices:
        wsum[v.index] = sum(gr.weight for gr in v.groups if groups[gr.group] in (f'B_{s}_Foot', f'B_{s}_Toe0'))
    ids = np.where(wsum > .5)[0]
    sole = ids[co[ids, 2] < co[ids, 2].min() + 0.012]
    # the toes are skinned to the foot (Toe0 carries no skin), so the whole sole is rigid: heel strike pivots on
    # the rearmost floor point, the heel-off roll on the toe pads just behind the tips
    fz = co[ids, 2].min()
    heel = Vector(co[sole[np.argmax(co[sole, 1])]]); heel.z = fz      # rearmost low point (+y is backward)
    tip = Vector(co[sole[np.argmin(co[sole, 1])]]); tip.z = fz
    ball = tip + Vector((0, PAD_BACK, 0))
    toe_ids = np.array([v.index for v in body.data.vertices
                        if sum(gr.weight for gr in v.groups if groups[gr.group] == f'B_{s}_Toe0') > .5])
    # heel->toe line of the 5 mm sole band (as the shared gates measure foot yaw); the foot pitches about the
    # horizontal axis perpendicular to it, so the line keeps its heading while the heel or toes lift
    band = ids[co[ids, 2] <= fz + 0.005]; along = -co[band, 1]
    line = co[band[along >= np.quantile(along, .7)]].mean(0) - co[band[along <= np.quantile(along, .3)]].mean(0)
    line[2] = 0
    Finv = stand[f'B_{s}_Foot'].inverted()
    sole_local = [Finv @ Vector(c) for c in co[ids[co[ids, 2] <= fz + 0.03]]]
    foot[s] = dict(heel=heel, tip=tip, ball=ball, ids=ids, toe_ids=toe_ids, floor=float(co[ids, 2].min()),
                   line=Vector(line).normalized(), sole_local=sole_local)
leg = {s: (stand[f'B_{s}_Calf'].translation - stand[f'B_{s}_Thigh'].translation).length +
          (stand[f'B_{s}_Foot'].translation - stand[f'B_{s}_Calf'].translation).length for s in 'LR'}
pole = {}
for s in 'LR':
    H, K_, A = [stand[f'B_{s}_{b}'].translation for b in ('Thigh', 'Calf', 'Foot')]
    u = (A - H).normalized(); pv = (K_ - H) - u * (K_ - H).dot(u)
    pole[s] = (pv + Vector((0, -0.25, 0))).normalized()                   # knees forward
stand_pelvis = stand['B_Pelvis'].translation.copy()

# ---- installed Walking, resampled at the clip's key times ------------------------------------------------------
inst = []
for t in times:
    goto('Walking', float(t))
    inst.append({n: (P[n].rotation_quaternion.copy(), P[n].location.copy()) for n in P.keys()})
rig.animation_data.action = None

# mean head rotation of the amplified chest (for stabilisation), first pass
SPINE = ('B_Spine', 'B_Spine1', 'B_Spine2')


def qmean(qs):
    acc = np.zeros(4); ref = np.array(qs[0][:])
    for q in qs:
        v = np.array(q[:]); acc += v if np.dot(v, ref) >= 0 else -v
    return Quaternion(acc / np.linalg.norm(acc))


# The oscillation about each bone's cycle mean is amplified back to the source level; the mean posture (the
# source walk's forward lean relative to the native guard) is raised only by LEAN_GAIN, so the sword stays near the
# native guard height while the hips and chest turn fully.
amp = {'B_Pelvis': GP / 0.3, 'B_Spine': GS / 0.35, 'B_Spine1': GS / 0.35, 'B_Spine2': GS / 0.35}
qm = {n: qmean([inst[i][n][0] for i in range(N)]) for n in amp}


def amplified(n, i):
    q = inst[i][n][0]; m = qm[n]
    osc = m.inverted() @ q
    return qpow(m, LEAN_GAIN) @ qpow(osc, amp[n])


def apply_upper(i):
    for n in P.keys():
        q, l = inst[i][n]; P[n].rotation_quaternion = q; P[n].location = l
    for n in amp:
        P[n].rotation_quaternion = amplified(n, i)
    upd()


heads, extra_world = [], []
for i in range(N):
    for n in P.keys():
        q, l = inst[i][n]; P[n].rotation_quaternion = q; P[n].location = l
    upd(); r_inst = W('B_Pelvis').to_quaternion()
    apply_upper(i); heads.append(W('B_Head').to_quaternion())
    extra_world.append(W('B_Pelvis').to_quaternion() @ r_inst.inverted())
mean = heads[0].copy()
acc = np.zeros(4)
for q in heads:
    v = np.array(q[:]); v = v if np.dot(v, np.array(mean[:])) >= 0 else -v; acc += v
mean_head = Quaternion(acc / np.linalg.norm(acc))


# ---- per-foot plan ---------------------------------------------------------------------------------------------
v = STRIDE / T_CLIP                       # m/s backward foot speed in the clip frame (+y)
UH, UR = 0.07, DUTY - 0.22                # heel rocker end, heel-off start (fractions of the cycle)
travel = DUTY * STRIDE


def foot_pose(s, phi):
    """(foot world matrix, toe flat?) for side s at cycle phase phi, before IK, relative to the standing foot."""
    u = (phi - CONTACT[s]) % 1.0
    F0 = stand[f'B_{s}_Foot']; b0 = foot[s]['ball']; h0 = foot[s]['heel']
    yc = b0.y - travel * 0.5 + 0.02      # ball at contact (forward of the standing ball)

    def flat(yb):
        M = F0.copy(); M.translation = F0.translation + Vector((0, yb - b0.y, 0)); return M
    lateral = foot[s]['line'].cross(Vector((0, 0, 1))).normalized()       # pitch about the sole's side axis
    if lateral.x < 0:
        lateral = -lateral

    def pitched(M, theta, pivot):
        # the pivot axis is not exactly along the sole's front and rear edges: lift the foot so that no sole point
        # goes below the standing floor height while it rolls
        out = rot_about(M, Matrix.Rotation(theta, 3, lateral), pivot)
        low = min((out @ p).z for p in foot[s]['sole_local'])
        if low < foot[s]['floor']:
            out.translation.z += foot[s]['floor'] - low
        return out
    if u <= DUTY:
        yb = yc + v * T_CLIP * u
        M = flat(yb)
        if u < UH:
            th = THETA_C * (1 - smooth(u / UH)); piv = h0 + Vector((0, yb - b0.y, 0))
            return pitched(M, -th, piv), 0.0, 'heel'
        if u > UR:
            th = THETA_O * smooth((u - UR) / (DUTY - UR)); piv = b0 + Vector((0, yb - b0.y, 0))
            return pitched(M, th, piv), th, 'roll'
        return M, 0.0, 'flat'
    w = (u - DUTY) / (1 - DUTY)
    off_M = pitched(flat(yc + travel), THETA_O, b0 + Vector((0, yc + travel - b0.y, 0)))
    on_M = pitched(flat(yc), -THETA_C, h0 + Vector((0, yc - b0.y, 0)))
    s_ = minjerk(w)
    pos = off_M.translation.lerp(on_M.translation, s_)
    # fore-aft: cubic Hermite whose end slopes equal the stance speed, so the foot leaves and meets the ground at
    # the ground's speed (no forward skid just before contact, no jerk at toe-off)
    y0, y1 = off_M.translation.y, on_M.translation.y; m = v * T_CLIP * (1 - DUTY)
    h00, h10, h01, h11 = 2*w**3 - 3*w**2 + 1, w**3 - 2*w**2 + w, -2*w**3 + 3*w**2, w**3 - w**2
    pos.y = h00 * y0 + h10 * m + h01 * y1 + h11 * m
    pos.z += LIFT * math.sin(math.pi * w ** LIFT_SKEW) ** 1.3    # quick toe pick-up, soft heel landing
    # hold the toe-off pitch while the toes clear the floor, then swing the foot level and toe-up for the heel
    th = THETA_O + (-THETA_C - THETA_O) * minjerk((w - 0.15) / 0.65)
    R3 = Matrix.Rotation(th, 3, lateral) @ F0.to_3x3()
    M = Matrix.Translation(pos) @ R3.to_4x4()
    low = min((M @ p).z for p in foot[s]['sole_local'])
    if low < foot[s]['floor']:
        M.translation.z += foot[s]['floor'] - low
    toe = THETA_O * (1 - smooth(w / 0.45))
    return M, toe, 'swing'


def solve_leg(s, target):
    """Two-bone IK: thigh and calf put the foot head at target (world), knee toward pole[s]."""
    th, ca, fo = f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot'
    Mt, Mc, Mf = W(th), W(ca), W(fo)
    S_, E0, W0 = Mt.translation.copy(), Mc.translation.copy(), Mf.translation.copy()
    a, b = (E0 - S_).length, (W0 - E0).length
    d = target - S_; dist = d.length
    reach = dist / (a + b)
    if dist > (a + b) * 0.9995:
        target = S_ + d.normalized() * (a + b) * 0.9995; d = target - S_; dist = d.length
    uu = d.normalized()
    pv = pole[s] - uu * pole[s].dot(uu); pv.normalize()
    cos_a = max(-1, min(1, (a * a + dist * dist - b * b) / (2 * a * dist)))
    knee = S_ + a * (uu * cos_a + pv * math.sqrt(max(0, 1 - cos_a * cos_a)))
    q = (E0 - S_).rotation_difference(knee - S_)
    set_W(th, Matrix.Translation(S_) @ (q.to_matrix() @ Mt.to_3x3()).to_4x4())
    Mc = W(ca); K2 = Mc.translation.copy(); W1 = W(fo).translation
    q = (W1 - K2).rotation_difference(target - K2)
    set_W(ca, Matrix.Translation(K2) @ (q.to_matrix() @ Mc.to_3x3()).to_4x4())
    return reach


def pelvis_design(phi):
    ms = {s: (CONTACT[s] + DUTY / 2) % 1 for s in 'LR'}
    z = stand_pelvis.z - CROUCH + BOB * math.cos(4 * math.pi * (phi - ms['L']))
    x = stand_pelvis.x + SWAY * math.cos(2 * math.pi * (phi - ms['L']))       # +x is the left side
    y = stand_pelvis.y + SURGE * math.cos(4 * math.pi * (phi - CONTACT['L'] - 0.06))
    return Vector((x, y, z))


def place_pelvis(i, pos):
    apply_upper(i)
    M = W('B_Pelvis'); M.translation = pos; set_W('B_Pelvis', M)


# pass 1: how far each frame's pelvis must drop so that neither leg overreaches
need = np.zeros(N)
for i in range(N):
    phi = i / (N - 1)
    place_pelvis(i, pelvis_design(phi))
    for s in 'LR':
        M, _, _ = foot_pose(s, phi)
        H = W(f'B_{s}_Thigh').translation
        d = M.translation - H; L = leg[s] * 0.995
        hz = math.sqrt(max(0.0, L * L - d.x * d.x - d.y * d.y))
        need[i] = max(need[i], (H.z - M.translation.z) - hz)
need = np.maximum(need, 0)
# cyclic max filter + gaussian so the extra drop is smooth and never less than needed
k = 9
padded = np.r_[need[-k:], need, need[:k]]
mx = np.array([padded[j:j + 2 * k + 1].max() for j in range(N)])
sig = 6.0; ker = np.exp(-0.5 * (np.arange(-24, 25) / sig) ** 2); ker /= ker.sum()
pad = np.r_[mx[-24:], mx, mx[:24]]
drop = np.convolve(pad, ker, mode='same')[24:-24]
drop = np.maximum(drop, need) + 0.001
drop[-1] = drop[0]

# pass 2: build the poses and convert to glTF locals
frames, reaches, toe_low, sole_low = [], [], [], []
for i in range(N):
    phi = i / (N - 1)
    pos = pelvis_design(phi); pos.z -= drop[i]
    place_pelvis(i, pos)
    # head: stabilise toward the cycle mean, slight nod down after each contact
    Mh = W('B_Head'); qh = Mh.to_quaternion()
    tgt = qh.slerp(mean_head, HEAD_STAB)
    nod = math.radians(NOD) * math.cos(4 * math.pi * (phi - CONTACT['L'] - 0.08))
    tgt = Quaternion(Vector((1, 0, 0)), nod) @ tgt
    set_W('B_Head', Matrix.Translation(Mh.translation) @ tgt.to_matrix().to_4x4())
    # arms: common bounce about the shoulder line (keeps the two-hand grip)
    if ARM_BOUNCE:
        aL, aR = W('B_L_UpperArm'), W('B_R_UpperArm')
        axis = (aL.translation - aR.translation).normalized()
        ang = ARM_BOUNCE * math.cos(4 * math.pi * (phi - CONTACT['L'] - 0.12))
        R3 = Matrix.Rotation(ang, 3, axis)
        set_W('B_L_UpperArm', rot_about(aL, R3, aL.translation))
        aR2 = W('B_R_UpperArm')
        set_W('B_R_UpperArm', rot_about(aR2, R3, aR2.translation))
    # tail: lagging counter-swing to the added hip turn
    for j in range(7):
        n = f'Tail{j}'
        if n not in P:
            continue
        lag_i = (i - 6 * (j + 1)) % (N - 1)
        Mt = W(n)
        Rw = qpow(extra_world[lag_i], -TAIL_COUNTER / 7.0 * (1.0 if j < 4 else 0.6)).to_matrix()
        set_W(n, rot_about(Mt, Rw, Mt.translation))
    # legs
    plan = {s: foot_pose(s, phi) for s in 'LR'}
    r = {}
    for s in 'LR':
        M, toe, phase = plan[s]
        r[s] = solve_leg(s, M.translation)
        Mf = W(f'B_{s}_Foot')
        set_W(f'B_{s}_Foot', Matrix.Translation(Mf.translation) @ M.to_3x3().to_4x4())
        # Toe0 carries no skin; it keeps its standing pose relative to the foot
        Mt = W(f'B_{s}_Toe0'); ts = stand[f'B_{s}_Toe0']
        rel = stand[f'B_{s}_Foot'].to_3x3().inverted() @ ts.to_3x3()
        set_W(f'B_{s}_Toe0', Matrix.Translation(Mt.translation) @ (M.to_3x3() @ rel).to_4x4())
    reaches.append(max(r.values()))
    # loincloth: leading thigh angle + 8 deg, clamped (finish_walk.py)
    deform = P['B_Pelvis'].matrix @ rig.data.bones['B_Pelvis'].matrix_local.inverted()
    angs = []
    for s in 'LR':
        dvec = deform.inverted().to_3x3() @ (P[f'B_{s}_Calf'].matrix.translation - P[f'B_{s}_Thigh'].matrix.translation)
        angs.append(math.atan2(-dvec.y, -dvec.z))
    ang = max(0, min(math.radians(80), max(angs))) + math.radians(8)
    cloth = rig.data.bones['B_Loincloth'].matrix_local
    Mx = deform @ cloth
    R3 = deform.to_3x3() @ Quaternion((1, 0, 0), -ang).to_matrix() @ cloth.to_3x3()
    set_W('B_Loincloth', Matrix.Translation(Mx.translation) @ R3.to_4x4())
    frames.append(gp.node_locals())

# make the loop exact
frames[-1] = frames[0]

# ---- write the Walking channels in place ------------------------------------------------------------------------
changed = []
for (node, path), (smp, out) in g.channels('Walking').items():
    if g.json['accessors'][smp['input']]['count'] != N or node not in frames[0]:
        continue
    if path == 'rotation':
        vals = np.array([f[node][1] for f in frames])
        for k in range(1, N):
            if np.dot(vals[k], vals[k - 1]) < 0:
                vals[k] = -vals[k]
    elif path == 'translation':
        vals = np.array([f[node][0] for f in frames])
    else:
        continue
    old = g.read(out)
    if np.abs(old - vals).max() > 1e-6:
        changed.append(f'{node}.{path}')
    g.write(out, vals)
# constant channels must not have needed a change
const_drift = 0.0
for (node, path), (smp, out) in g.channels('Walking').items():
    if g.json['accessors'][smp['input']]['count'] == N or node not in frames[0] or path != 'rotation':
        continue
    ref = g.read(out)[0]
    for f in frames:
        q = f[node][1]; const_drift = max(const_drift, min(np.abs(q - ref).max(), np.abs(q + ref).max()))
g.save(OUT)
rep = dict(stride_m=STRIDE, crouch=CROUCH, bob=BOB, sway=SWAY, pelvis_gain=GP, spine_gain=GS, head_stab=HEAD_STAB,
           max_reach=float(max(reaches)), extra_drop_cm=[round(float(drop.min()) * 100, 2), round(float(drop.max()) * 100, 2)],
           changed_channels=changed, constant_channel_drift=float(const_drift))
print('AUTHOR', json.dumps(rep), flush=True)
if REPORT:
    json.dump(rep, open(REPORT, 'w'), indent=1)
