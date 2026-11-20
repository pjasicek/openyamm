"""natm Attack: an underhand spear thrust with a lunge, authored over Mixamo "Stabbing (2)" (Stab2, retargeted :turn).

Why: the humanoid set's spear attacks plunge the tip into the ground (R3 tip at 2 cm height) and its overhand pass
needs a reversed grip; the source grip holds the spear like a hammer (tip on the thumb side), so the natural blow is
an underhand thrust from the hip, as the native carries the spear. Stab2 gives a natural mocap trunk, head, shield
arm counterbalance and wrist path; everything that decides how the blow reads is authored on top:
- timeline: source frames are time-remapped (monotone cubic) - lead-in/anticipation, strike, follow-through, recovery;
  the upper body blends from/to Standing frame 0 (smoothstep);
- body: pelvis path (sink + draw back, then drive forward into the lunge), hip-then-chest yaw coil (kinetic chain:
  the pelvis leads the chest by KC_LAG s), forward lean into the blow, the neck counter-turns to keep the eyes on the
  target;
- legs: two-bone IK to authored foot plans - the left foot steps into the lunge (sine lift) and back, the right foot
  stays planted and peels its heel up (rotation about the toe joint) while it drives; knees bend over the toes;
- right arm (armik.py): wrist = the Standing wrist blended into Stab2's wrist path in the chest frame plus a draw-back
  in the anticipation; the spear points at a target at chest height in front (blended from/to the carry direction),
  dipping a little in the follow-through; hand roll by least wrist strain with continuity.
Writes the 'Attack' action, work/attack_intent.json (per frame wrist target and spear direction) and prints IMPACT
(fastest tip motion while the spear points at the target). Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, common
a = sys.argv[sys.argv.index('--') + 1:]
src_blend, out_blend = a[0], a[1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
FPS = 30; scene.render.fps = FPS; scene.render.fps_base = 1
P = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attack_params.json')))
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json')))
AX = Vector(G['handle_axis_hand_local']).normalized(); GC = Vector(G['handle_centre_hand_local'])
names = [b.name for b in rig.data.bones]
SRC = bpy.data.actions[P.get('source', 'Stab2')]; ST = bpy.data.actions['Standing']


def set_act(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def sample(act, f):
    set_act(act); scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def world_of(act, f, bones):
    set_act(act); scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    return {n: armik.W(rig, n).copy() for n in bones}


def apply(pose):
    set_act(None)
    for n, (q, l) in pose.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
    bpy.context.view_layer.update()


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def pchip(ts, vs):
    """Monotone cubic through (ts, vs) (Fritsch-Carlson); returns f(t)."""
    ts = np.array(ts, float); vs = np.array(vs, float); h = np.diff(ts); dl = np.diff(vs) / h
    m = np.zeros(len(ts)); m[0], m[-1] = dl[0], dl[-1]
    for i in range(1, len(ts) - 1):
        m[i] = 0.0 if dl[i - 1] * dl[i] <= 0 else 3 * (h[i - 1] + h[i]) / ((2 * h[i] + h[i - 1]) / dl[i - 1] + (h[i] + 2 * h[i - 1]) / dl[i])
    def f(t):
        if t <= ts[0]: return float(vs[0])
        if t >= ts[-1]: return float(vs[-1])
        i = int(np.searchsorted(ts, t) - 1); s = (t - ts[i]) / h[i]
        h00, h10, h01, h11 = 2*s**3 - 3*s**2 + 1, s**3 - 2*s**2 + s, -2*s**3 + 3*s**2, s**3 - s**2
        return float(h00 * vs[i] + h10 * h[i] * m[i] + h01 * vs[i + 1] + h11 * h[i] * m[i + 1])
    return f


def curve(keys):
    """keys [[t, value], ...] -> smooth (C1, no overshoot) curve of t."""
    return pchip([k[0] for k in keys], [k[1] for k in keys])


DUR = P['duration']; N = int(round(DUR * FPS)) + 1
src_frame = curve(P['timeline'])                          # output seconds -> Stab2 frame
w_body = curve(P['w_body']); w_arm = curve(P['w_arm']); w_aim = curve(P['w_aim'])
pel_fwd = curve(P['pelvis_forward']); pel_down = curve(P['pelvis_down'])
yaw_pel = curve(P['yaw_pelvis']); lean = curve(P['lean']); draw = curve(P['drawback']); dip = curve(P['dip'])
KC = P['kc_lag']
S0 = sample(ST, 0)
SW0 = world_of(ST, 0, ['B_Pelvis', 'B_Spine2', 'B_R_Hand', 'B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0'])
TARGET = Vector(P['target'])
# Standing references: wrist in the chest frame, carry spear direction in the pelvis frame
w_st_chest = SW0['B_Spine2'].inverted() @ SW0['B_R_Hand'].translation
d_carry_pel = SW0['B_Pelvis'].to_3x3().normalized().inverted() @ (SW0['B_R_Hand'].to_3x3().normalized() @ AX)
FEET = {sd: (SW0[f'B_{sd}_Foot'].copy(), SW0[f'B_{sd}_Toe0'].translation.copy()) for sd in 'LR'}
TOE_REST = {sd: SW0[f'B_{sd}_Toe0'].to_3x3().normalized() for sd in 'LR'}
TOE_LOCAL = {sd: Quaternion() for sd in 'LR'}   # the rest relation (the Mixamo toes curl up 4-7 cm)
UP = Vector((0, 0, 1))
SPINE = ['B_Spine', 'B_Spine1', 'B_Spine2']; SPINE_SHARE = P['spine_share']


def rotate_world(bone, R, pivot=None):
    M = armik.W(rig, bone); t = M.translation.copy(); pv = pivot if pivot is not None else t
    M2 = R.to_4x4() @ M; M2.translation = pv + R @ (t - pv)
    armik.set_world(rig, bone, M2)


def foot_plan(sd, t):
    """(ankle world position, foot world rotation) for the foot at time t."""
    M0, toe0 = FEET[sd]; ank0 = M0.translation.copy(); R0 = M0.to_3x3().normalized()
    fp = P['feet'][sd]
    if fp.get('step'):
        s = fp['step']; off = Vector(s['offset'])
        u_out = smooth((t - s['out'][0]) / (s['out'][1] - s['out'][0])); u_back = smooth((t - s['back'][0]) / (s['back'][1] - s['back'][0]))
        u = u_out * (1 - u_back)
        lift = 0.0
        for a0, a1 in (s['out'], s['back']):
            if a0 < t < a1:
                lift = s['lift'] * math.sin(math.pi * (t - a0) / (a1 - a0))
        pos = ank0 + off * u + Vector((0, 0, lift))
        # toe-up / heel-strike flavour: pitch the foot slightly while it travels (about its own right axis)
        pitch = 0.0
        for a0, a1 in (s['out'], s['back']):
            if a0 < t < a1:
                pitch = math.radians(s.get('pitch', 0)) * math.sin(math.pi * (t - a0) / (a1 - a0))
        yaw = math.radians(s.get('yaw', 0)) * u
        R = Matrix.Rotation(yaw, 3, 'Z') @ R0
        right = (R @ Vector((1, 0, 0))).normalized()
        R = Matrix.Rotation(pitch, 3, right) @ R
        return pos, R
    if fp.get('heel'):
        h = curve(fp['heel'])(t); ang = math.radians(h)
        fwd = toe0 - ank0; fwd.z = 0; fwd.normalize(); axis = UP.cross(fwd).normalized()   # heel up = toe stays
        R = Matrix.Rotation(-ang, 3, axis)
        piv = Vector((toe0.x, toe0.y, 0.0))            # under the ball of the foot, on the floor (the toe joint sits ~5 cm up)
        pos = piv + R @ (ank0 - piv)
        return pos, R @ R0
    return ank0, R0


def leg_ik(sd, ank, Rfoot):
    th, ca, ft = f'B_{sd}_Thigh', f'B_{sd}_Calf', f'B_{sd}_Foot'
    H = armik.W(rig, th).translation; K = armik.W(rig, ca).translation; A0 = armik.W(rig, ft).translation
    l1, l2 = (K - H).length, (A0 - K).length
    d_ = (ank - H); dist = min(d_.length, (l1 + l2) * 0.9995); u = d_.normalized()
    toe_dir = Rfoot @ (SW0['B_L_Toe0' if sd == 'L' else 'B_R_Toe0'].translation - FEET[sd][0].translation)
    toe_dir = FEET[sd][0].to_3x3().normalized().inverted() @ toe_dir   # (unused fallback)
    fwd = Rfoot @ (FEET[sd][0].to_3x3().normalized().inverted() @ (FEET[sd][1] - FEET[sd][0].translation)); fwd.z = 0
    v = fwd - u * fwd.dot(u); v = v.normalized() if v.length > 1e-6 else Vector((0, -1, 0))
    c = max(-1.0, min(1.0, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)))
    Kn = H + l1 * (u * c + v * math.sqrt(max(0.0, 1 - c * c)))
    def aim(bone, direction):
        M = armik.W(rig, bone); cur = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
        rotate_world(bone, cur.rotation_difference(direction.normalized()).to_matrix())
    aim(th, Kn - H); aim(ca, (H + u * dist) - armik.W(rig, ca).translation)
    armik.set_world(rig, ft, armik.rot_world(armik.W(rig, ft), Rfoot))
    return (d_.length - (l1 + l2)) if d_.length > (l1 + l2) else 0.0


frames, intent = [], []
reach_short = 0.0; floor_lift = 0.0
import numpy as np
BODY = bpy.data.objects['Body']; _vg = [g.name for g in BODY.vertex_groups]
FOOTV = {sd: np.array([sum(e.weight for e in v.groups if _vg[e.group] in (f'B_{sd}_Foot', f'B_{sd}_Toe0')) > 0.5 for v in BODY.data.vertices]) for sd in 'LR'}
ARMK = P['arm_keys']                                     # [t, [flex deg, length m, abduction deg]]
arm_flex = curve([[k[0], k[1][0]] for k in ARMK]); arm_abd = curve([[k[0], k[1][2]] for k in ARMK])
def chest_heading_rot():
    ls, rs = armik.W(rig, 'B_L_UpperArm').translation, armik.W(rig, 'B_R_UpperArm').translation
    fwd = (ls - rs).cross(UP); fwd.z = 0; fwd.normalize()   # character faces -Y at rest: fwd = (0,-1,0)
    return Matrix.Rotation(math.atan2(fwd.x, -fwd.y), 3, 'Z')     # yaw taking the rest forward (0, -1, 0) onto fwd


apply(S0); RH0 = chest_heading_rot(); SH0 = armik.W(rig, 'B_R_UpperArm').translation.copy()
v0 = RH0.inverted() @ (SW0['B_R_Hand'].translation - SH0)              # Standing arm vector (shoulder -> wrist)
L0 = v0.length
arm_len = curve([[k[0], k[1][1] if k[1][1] > 0 else L0] for k in ARMK])   # length 0 in the keys = the Standing length
print('ARM standing shoulder->wrist', round(L0, 3))
body = []
for i in range(N):
    t = i / FPS
    sf = src_frame(t); wb = w_body(t)
    ps = sample(SRC, sf)
    pose = {}
    for n in names:
        q0, l0 = S0[n]; q1, l1 = ps[n]
        if q0.dot(q1) < 0: q1 = -q1
        pose[n] = (q0.slerp(q1, wb), l0.lerp(l1, wb))
    pose['B_Pelvis'] = (S0['B_Pelvis'][0], S0['B_Pelvis'][1])
    apply(pose)
    Mp = armik.W(rig, 'B_Pelvis')
    Mp.translation = SW0['B_Pelvis'].translation + Vector((0, -pel_fwd(t), -pel_down(t)))
    armik.set_world(rig, 'B_Pelvis', Mp)
    rotate_world('B_Pelvis', Matrix.Rotation(math.radians(yaw_pel(t)), 3, 'Z'))
    ychest = math.radians(P['chest_gain'] * yaw_pel(t - KC) - yaw_pel(t))
    for b_, s_ in zip(SPINE, SPINE_SHARE):
        rotate_world(b_, Matrix.Rotation(ychest * s_, 3, 'Z') @ Matrix.Rotation(math.radians(lean(t)) * s_, 3, Vector((1, 0, 0))))
    rotate_world('B_Neck', Matrix.Rotation(-(ychest + math.radians(yaw_pel(t))) * P['neck_comp'], 3, 'Z')
                 @ Matrix.Rotation(-math.radians(lean(t)) * 0.6, 3, Vector((1, 0, 0))))
    # right clavicle reaches forward with the thrust (protraction), about the chest's up axis
    rotate_world('B_R_Clavicle', Matrix.Rotation(-math.radians(curve(P['clavicle'])(t)), 3, 'Z'))
    for it in range(3):
        miss = 0.0
        for sd in 'LR':
            ank, Rf = foot_plan(sd, t)
            sh = leg_ik(sd, ank, Rf)
            if not P['feet'][sd].get('step') or not (P['feet'][sd]['step']['out'][0] < t < P['feet'][sd]['step']['back'][1]):
                miss = max(miss, sh)                                   # a planted foot that the leg cannot reach
        if miss < 0.002:
            break
        Mp = armik.W(rig, 'B_Pelvis'); Mp.translation.z -= miss + 0.002; armik.set_world(rig, 'B_Pelvis', Mp)
    reach_short = max(reach_short, miss)
    # mesh floor clamp (review 1: the heel-peeling foot dipped 3-4 cm): lift a foot whose lowest vertex is below the floor
    lift = {'L': 0.0, 'R': 0.0}
    for it in range(3):
        ev = BODY.evaluated_get(bpy.context.evaluated_depsgraph_get()); mm = ev.to_mesh()
        zz = np.array([(BODY.matrix_world @ v.co).z for v in mm.vertices]); ev.to_mesh_clear()
        low = {sd: float(zz[FOOTV[sd]].min()) for sd in 'LR'}
        if min(low.values()) > -0.003:
            break
        for sd in 'LR':
            if low[sd] < -0.003:
                lift[sd] += -low[sd]; ank, Rf = foot_plan(sd, t); leg_ik(sd, ank + Vector((0, 0, lift[sd])), Rf)
    floor_lift = max(floor_lift, max(lift.values()))
    # toes: the heel-peeling (planted) foot keeps its toes flat on the floor; a stepping foot keeps the Standing toe pose
    for sd in 'LR':
        if P['feet'][sd].get('heel'):
            armik.set_world(rig, f'B_{sd}_Toe0', armik.rot_world(armik.W(rig, f'B_{sd}_Toe0'), TOE_REST[sd]))
        else:
            pb = rig.pose.bones[f'B_{sd}_Toe0']; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = TOE_LOCAL[sd]
            bpy.context.view_layer.update()
    # wrist target: Standing wrist + authored offsets, in the chest heading frame
    # wrist = shoulder + the Standing arm vector swung forward (flex, about the heading's lateral axis) and out
    # (abduction, about the heading's forward axis), scaled to the wanted shoulder -> wrist length (elbow bend)
    RH = chest_heading_rot(); SH = armik.W(rig, 'B_R_UpperArm').translation.copy()
    v = Matrix.Rotation(-math.radians(arm_flex(t)), 3, Vector((1, 0, 0))) @ (Matrix.Rotation(math.radians(arm_abd(t)), 3, Vector((0, 1, 0))) @ v0)
    v = v.normalized() * arm_len(t)
    wrist = SH + RH @ v
    snap = {n: rig.pose.bones[n].matrix_basis.copy() for n in names}
    armik.solve(rig, 'R', wrist); grip = armik.W(rig, 'B_R_Hand') @ GC
    for n in names: rig.pose.bones[n].matrix_basis = snap[n]
    bpy.context.view_layer.update()
    d_carry = armik.W(rig, 'B_Pelvis').to_3x3().normalized() @ d_carry_pel
    d_aim = (TARGET - grip).normalized(); right = d_aim.cross(UP).normalized()
    d_aim = Matrix.Rotation(-math.radians(dip(t)), 3, right) @ d_aim
    d = d_carry.lerp(d_aim, w_aim(t)).normalized()
    wa_ = w_aim(t); cone = P.get('cone', 12)
    devs = [(dp * wa_, dy * wa_) for dp in (-cone, -cone / 2, 0, cone / 2, cone) for dy in (-cone, -cone / 2, 0, cone / 2, cone)]
    body.append({'snap': snap, 'wrist': wrist, 'dir': d, 'devs': devs, 't': t, 'sf': sf})
choice = armik.arm_dp(rig, 'R', body, AX, twist_neutral=P.get('twist_neutral', 30), k_dev=P.get('k_dev', 0.5), k_twist=P.get('k_twist', 0.35))
# smooth the chosen phi, unwrapped psi and dev over time (Gaussian, sigma 1 frame) and pose
import numpy as np
gk = np.exp(-0.5 * (np.arange(-3, 4) / P.get('sigma', 1.0)) ** 2); gk /= gk.sum()
def sm(x):
    x = np.array(x, float); pad = np.concatenate([np.repeat(x[:1], 3), x, np.repeat(x[-1:], 3)]); return np.convolve(pad, gk, 'valid')
phi_s = sm([c['phi'] for c in choice]); psi_s = sm(np.degrees(np.unwrap(np.radians([c['psi'] for c in choice]))))
dp_s = sm([c['dev'][0] for c in choice]); dy_s = sm([c['dev'][1] for c in choice])
for i, fr in enumerate(body):
    sw, tw = armik.apply_arm(rig, 'R', fr['snap'], fr['wrist'], AX, fr['dir'], phi_s[i], psi_s[i], (dp_s[i], dy_s[i]))
    miss = (fr['wrist'] - armik.W(rig, 'B_R_Hand').translation).length
    Mh = armik.W(rig, 'B_R_Hand')
    intent.append({'t': round(fr['t'], 4), 'src_frame': round(fr['sf'], 3), 'wrist': [round(x, 4) for x in fr['wrist']],
                   'spear': [round(x, 4) for x in (Mh.to_3x3() @ AX).normalized()], 'phi': round(float(phi_s[i]), 1),
                   'psi': round(float(psi_s[i]), 1), 'wrist_miss_cm': round(miss * 100, 2), 'wrist_swing': round(sw, 1), 'hand_twist': round(tw, 1)})
    frames.append({n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names})
# head stabiliser (review 1: the head jerked right at 0.60-0.71 s): the head's world forward is smoothed over time
# (Gaussian, HEAD_SIGMA frames) and its yaw pulled HEAD_HOLD toward the Standing gaze; the correction is shared by
# the neck (50 %) and the head
import numpy as np
apply(S0); HF_L = armik.W(rig, 'B_Head').to_3x3().normalized().inverted() @ Vector((0, -1, 0))
g0 = armik.W(rig, 'B_Head').to_3x3().normalized() @ HF_L
fw = []
for pose in frames:
    apply(pose); fw.append(np.array(armik.W(rig, 'B_Head').to_3x3().normalized() @ HF_L))
fw = np.array(fw); sig = P.get('head_sigma', 2.5); hold = P.get('head_hold', 0.5)
gk = np.exp(-0.5 * (np.arange(-6, 7) / sig) ** 2); gk /= gk.sum()
pad = np.concatenate([np.repeat(fw[:1], 6, 0), fw, np.repeat(fw[-1:], 6, 0)])
fs = np.array([sum(gk[k] * pad[i + k] for k in range(13)) for i in range(len(fw))])
yaw0 = math.atan2(g0.x, -g0.y); hmax = 0.0
for i, pose in enumerate(frames):
    v = Vector(fs[i]).normalized(); y = math.atan2(v.x, -v.y); yn = y + (yaw0 - y) * hold
    tgt = (Matrix.Rotation(yn - y, 3, 'Z') @ v).normalized()         # yaw = atan2(x, -y); +Z rotation adds yaw
    apply(pose)
    cur = (armik.W(rig, 'B_Head').to_3x3().normalized() @ HF_L).normalized()
    q = cur.rotation_difference(tgt); hmax = max(hmax, math.degrees(q.angle))
    for b_, share in (('B_Neck', 0.5), ('B_Head', 1.0)):
        c2 = (armik.W(rig, 'B_Head').to_3x3().normalized() @ HF_L).normalized()
        qq = Quaternion().slerp(c2.rotation_difference(tgt), share)
        rotate_world(b_, qq.to_matrix())
    frames[i] = {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}
print(f'HEAD stabiliser: max correction {hmax:.1f} deg')
# write
old = bpy.data.actions.get('Attack')
if old: bpy.data.actions.remove(old)
act = bpy.data.actions.new('Attack'); act.use_fake_user = True; set_act(act)
prev = {}
for i, pose in enumerate(frames):
    for n, (q, l) in pose.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        if n in prev and q.dot(prev[n]) < 0: q = -q
        prev[n] = q; pb.rotation_quaternion = q; pb.location = l
        pb.keyframe_insert('rotation_quaternion', frame=i)
        if n == 'B_Pelvis': pb.keyframe_insert('location', frame=i)
act.use_frame_range = True; act.frame_start, act.frame_end = 0, N - 1
# impact: fastest tip motion while the spear points forward (at the target)
tips, fw = [], []
for i in range(N):
    scene.frame_set(i); Mh = armik.W(rig, 'B_R_Hand'); g = Mh @ GC; d = (Mh.to_3x3() @ AX).normalized()
    tips.append(np.array(g + d * 1.15)); fw.append(-d.y)
sp = np.linalg.norm(np.diff(np.array(tips), axis=0), axis=1) * FPS
vf = -np.diff(np.array(tips)[:, 1]) * FPS                       # forward (-Y) tip velocity
cand = np.where(np.array(fw[:-1]) > 0.8, vf, 0.0); k = int(np.argmax(cand)); impact = (k + 0.5) / FPS
set_act(None)
json.dump(choice, open(os.path.join(common.WORK, 'attack_choices_raw.json'), 'w'))
json.dump({'frames': intent, 'impact_s': impact, 'tip_speed': [round(float(x), 2) for x in sp]}, open(os.path.join(common.WORK, 'attack_intent.json'), 'w'), indent=0)
print(f'ATTACK {N} frames = {(N - 1) / FPS:.3f} s; IMPACT {impact:.3f} s (tip forward {vf[k]:.1f} m/s); peak tip speed {sp.max():.1f} m/s at {(int(np.argmax(sp)) + 0.5) / FPS:.3f} s; '
      f'leg reach short max {reach_short * 100:.1f} cm; floor lift max {floor_lift * 100:.1f} cm; wrist miss max {max(x["wrist_miss_cm"] for x in intent):.1f} cm; '
      f'wrist swing max {max(x["wrist_swing"] for x in intent):.0f} deg; hand twist {min(x["hand_twist"] for x in intent):.0f}..{max(x["hand_twist"] for x in intent):.0f} deg')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
