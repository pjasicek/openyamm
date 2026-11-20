"""m270 staff attack (native m270a: the staff tips toward the target, rises high while the spell bursts at the orb,
and returns; the free hand hangs). The body comes from a mocap clip (planted, <BodyAction>: Mixamo "Standing 1H
Cast Spell 01", whose cast arm goes low-forward then overhead like the native staff arm), resampled at SPEED and cut
at BODY_END seconds; its spine/neck/head turn against Standing is damped (DAMP) so the head stays on the target.
The staff arm (the RIGHT arm in this mirrored build) is solved on top with the carry machinery (author_carry.py): per
frame a wrist target in the chest frame and a staff direction in the pelvis frame, interpolated between KEYS with
smoothstep, and the arm solved by armik.arm_dp (global elbow plane / hand roll / staff deviation, least wrist strain).
A key is (source seconds, body share, OUT share, staff direction): the wrist is the carry wrist moved with the clip's own
wrist motion (body share 0) or the clip's own wrist position (body share 1), plus that share of OUT (world); the clip
starts and ends on the carry.
The release is at RELEASE (source seconds). The first version (Mixamo "Standing 1H Magic Attack 01" with keyed wrist
offsets) swept both arms out, turned the chest 48 deg and the head with it.
The free arm keeps FREE_KEEP of the clip's motion against Standing (the clip held it out from the side, still) and
casts on top (FREE_KEYS: a reach toward the target, a forward thrust at chest height on the release; user review: a
hanging arm read as idle). The staff-side clavicle lifts up to SHRUG as the wrist rises above the shoulder: the pauldron is ~42 %
clavicle, ~58 % upper arm, and with the arm overhead and a still clavicle it lifted off the shoulder (user review).
Body: PELVIS_KEEP of the unplanted clip's pelvis travel (<FullAction>: a 12 cm dip as the staff tips, a sideways shift
and a rise with the raise; never above the planted height, the legs are straight there) on the planted pose, the legs
solved back onto the planted feet (two-bone IK, knee toward its planted side), so the feet do not slide (the unplanted
clip slides the standing foot 14 cm and stamps the other).
Writes the action <Name>. Args: -- <in blend> <out blend> <BodyAction> <Name> [<FullAction>]"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, common
a = sys.argv[sys.argv.index('--') + 1:]
src, out, body_name, name = a[:4]
full_name = a[4] if len(a) > 4 else None
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
G = json.load(open(os.path.join(common.WORK, 'grip_pose.json')))
AX = Vector(G['handle_axis_hand_local']).normalized()
CARRY = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'carry.json')))
WRIST = Vector(CARRY['wrist'])
ya, pi_ = math.radians(CARRY['yaw_out']), math.radians(CARRY['pitch'])
UPRIGHT = Vector((-math.sin(ya) * math.cos(pi_), -math.cos(ya) * math.cos(pi_), math.sin(pi_)))
TIP = Vector((0.05, -0.75, 0.65)).normalized()       # ~40 deg above horizontal, at the target's head (a hammer grip
RAISED = Vector((-0.10, -0.30, 0.95)).normalized()   # cannot aim a long prop along the forearm); raised: high, a little
OUT = Vector(eval(os.environ.get('STAFF_OUT', '(-0.25, 0.0, -0.05)')))   # world offset of the raised hand (-X: out)
KEYS = [(0.00, 0.0, 0.0, UPRIGHT),                   # forward and out (in front of the face it hid the skull)
        (0.12, 0.0, 0.0, UPRIGHT),
        (0.40, 1.0, 0.0, TIP),                       # the clip's hand low and forward
        # raised: the clip's overhead hand (1.9 m) moved out by OUT (straight up, the rigid pauldron rose into the
        # coif beside the jaw); a lower hand (blended toward the carry, or dropped 10-25 cm) rolled the forearm ~150 deg
        (0.80, 1.0, 1.0, RAISED),                    # release
        (1.05, 1.0, 1.0, RAISED),                    # hold through the burst
        (1.40, 0.2, 0.0, UPRIGHT),
        (1.60, 0.0, 0.0, UPRIGHT)]
RELEASE = 0.80
BODY_END = float(os.environ.get('BODY_END', '1.75'))   # the source settles from 1.5 s; the blend-out finishes it
DAMP = {'B_Spine': 0.6, 'B_Spine1': 0.6, 'B_Spine2': 0.6, 'B_Neck': 0.4, 'B_Head': 0.4}
FREE_KEEP = float(os.environ.get('FREE_KEEP', '0.25'))
DAMP.update({n: FREE_KEEP for n in ('B_L_Clavicle', 'B_L_UpperArm', 'B_L_Forearm', 'B_L_Hand')})
SHRUG = math.radians(float(os.environ.get('SHRUG', '25')))
PELVIS_KEEP = float(os.environ.get('PELVIS_KEEP', '0.7'))


def set_act(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def at(t):
    for (t0, k0, z0, d0), (t1, k1, z1, d1) in zip(KEYS[:-1], KEYS[1:]):
        if t0 <= t <= t1:
            k = ss((t - t0) / max(t1 - t0, 1e-6))
            return k0 + (k1 - k0) * k, z0 + (z1 - z0) * k, d0.slerp(d1, k).normalized()
    return KEYS[-1][1], KEYS[-1][2], KEYS[-1][3]


SPEED = float(os.environ.get('STAFF_SPEED', '1.3'))    # release + the 0.15 s ready pause near the native 0.75 s
src_act = bpy.data.actions[body_name]
old = bpy.data.actions.get(name)
if old:
    bpy.data.actions.remove(old)
# the body clip resampled at SPEED (keys every frame of the new action)
sf0, sf1 = src_act.frame_range
sf1 = min(sf1, sf0 + BODY_END * 30)
n_out = int(round((sf1 - sf0) / SPEED))
names_ = [b.name for b in rig.data.bones]
set_act(bpy.data.actions['Standing']); scene.frame_set(0)
REST = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in DAMP}
samples, hand_src, pel_full = [], [], []
for i in range(n_out + 1):
    t = sf0 + i * SPEED; set_act(src_act); scene.frame_set(int(t), subframe=t - int(t))
    # the clip's own wrist in its chest frame (before the damping moves the chest)
    hand_src.append(armik.W(rig, 'B_Spine2').inverted() @ armik.W(rig, 'B_R_Hand').translation)
    if full_name:
        set_act(bpy.data.actions[full_name]); scene.frame_set(int(t), subframe=t - int(t))
        pel_full.append(armik.W(rig, 'B_Pelvis').translation.copy()); set_act(src_act); scene.frame_set(int(t), subframe=t - int(t))
    pose = {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names_}
    for n, f_ in DAMP.items():
        q = pose[n][0]
        if q.dot(REST[n]) < 0:
            q = -q
        pose[n] = (REST[n].slerp(q, f_), pose[n][1])
    samples.append(pose)
act = bpy.data.actions.new(name); act.use_fake_user = True; set_act(act)
prev = {}
for i, pose in enumerate(samples):
    for n, (q, l) in pose.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        if n in prev and q.dot(prev[n]) < 0:
            q = -q
        prev[n] = q; pb.rotation_quaternion = q; pb.location = l
        pb.keyframe_insert('rotation_quaternion', frame=i)
        if n == 'B_Pelvis':
            pb.keyframe_insert('location', frame=i)
act.use_frame_range = True; act.frame_start, act.frame_end = 0, n_out
f0, f1 = 0, n_out


def aim(n, target):
    """turn bone n (world, about its head) so its axis points at target"""
    M = armik.W(rig, n); d = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    armik.set_world(rig, n, armik.rot_world(M, d.rotation_difference((target - M.translation).normalized()).to_matrix()
                                            @ M.to_3x3().normalized()))


if full_name:
    LEGB = {s_: (f'B_{s_}_Thigh', f'B_{s_}_Calf', f'B_{s_}_Foot') for s_ in 'LR'}
    dips = []
    for f in range(f0, f1 + 1):
        set_act(act); scene.frame_set(f)
        feet = {s_: {n: armik.W(rig, n).copy() for n in LEGB[s_]} for s_ in 'LR'}
        d = (pel_full[f] - pel_full[0]) * PELVIS_KEEP; d.z = min(d.z, 0.0); dips.append(d.z)
        P = armik.W(rig, 'B_Pelvis'); P.translation += d; armik.set_world(rig, 'B_Pelvis', P)
        for s_, (th, ca, ft) in LEGB.items():
            H = armik.W(rig, th).translation; K0 = feet[s_][ca].translation; A = feet[s_][ft].translation
            a_, b_ = (K0 - feet[s_][th].translation).length, (A - K0).length
            u = A - H; dist = min(u.length, a_ + b_ - 1e-4); u.normalize()
            pole = (K0 - feet[s_][th].translation); pole = (pole - u * pole.dot(u)).normalized()
            ca_ = max(-1.0, min(1.0, (a_ * a_ + dist * dist - b_ * b_) / (2 * a_ * dist)))
            K = H + u * a_ * ca_ + pole * a_ * math.sqrt(1 - ca_ * ca_)
            aim(th, K); aim(ca, A); armik.set_world(rig, ft, feet[s_][ft])
        for n in ['B_Pelvis'] + [n for v in LEGB.values() for n in v]:
            pb = rig.pose.bones[n]; pb.keyframe_insert('rotation_quaternion', frame=f)
            if n == 'B_Pelvis':
                pb.keyframe_insert('location', frame=f)
    print(f'STAFFBODY pelvis from {full_name} x{PELVIS_KEEP}: dip {100 * min(dips):.1f} cm')
set_act(act); scene.frame_set(f0)
C0 = armik.W(rig, 'B_Spine2'); P0 = armik.W(rig, 'B_Pelvis')
wrist_chest = C0.inverted() @ WRIST
# the staff direction may deviate up to 25 deg (k_dev) where that saves wrist bend or forearm roll
DEVS = tuple((p_, y_) for p_ in (-25, -12, 0, 12, 25) for y_ in (-25, -12, 0, 12, 25))
frames_in = []
for f in range(f0, f1 + 1):
    set_act(act); scene.frame_set(f)
    snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    C = armik.W(rig, 'B_Spine2'); P = armik.W(rig, 'B_Pelvis')
    u = (f - f0) / max(f1 - f0, 1)
    kb, ko, d = at(f * SPEED / 30)
    target = C @ ((wrist_chest + hand_src[f] - hand_src[0]).lerp(hand_src[f], kb)) + OUT * ko
    # shrug: the clavicle lifts with the wrist above the shoulder (about the axis turning its direction up)
    S_ = armik.W(rig, 'B_R_UpperArm').translation
    e = ss((target.z - S_.z) / 0.45)
    if e > 0:
        M = armik.W(rig, 'B_R_Clavicle'); dcl = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
        R = Matrix.Rotation(SHRUG * e, 3, dcl.cross(Vector((0, 0, 1))).normalized())
        armik.set_world(rig, 'B_R_Clavicle', armik.rot_world(M, R @ M.to_3x3().normalized()))
        snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    dw = P.to_3x3().normalized() @ (P0.to_3x3().normalized().inverted() @ d)
    # no deviation at the ends (the carry has none: the clip starts and ends on it), full grid through the strike
    k = ss((u - 0.02) / 0.12) * (1 - ss((u - 0.70) / 0.18))
    frames_in.append({'snap': snap, 'wrist': target, 'dir': dw,
                      'devs': [(p_ * k, y_ * k) for p_, y_ in DEVS]})
set_act(None)
ch = armik.arm_dp(rig, 'R', frames_in, AX, twist_neutral=30.0, k_twist=float(os.environ.get('K_TWIST', '1.0')), k_dphi=1.0,
                  k_dpsi=0.8, devs=DEVS, k_dev=0.4,
                  k_ddev=float(os.environ.get('K_DDEV', '1.0')))
gk = np.exp(-0.5 * (np.arange(-3, 4) / 2.0) ** 2); gk /= gk.sum()
sm = lambda x: np.convolve(np.concatenate([np.repeat(x[:1], 3), x, np.repeat(x[-1:], 3)]), gk, 'valid')
phi = sm(np.array([c['phi'] for c in ch], float)); psi = sm(np.degrees(np.unwrap(np.radians([c['psi'] for c in ch]))))
# the deviation is chosen per frame: smoothed too (a jump between grid values turned the staff and hand in one frame)
dev = np.stack([sm(np.array([c['dev'][k] for c in ch], float)) for k in (0, 1)], 1)
ARM = ['B_R_Clavicle', 'B_R_UpperArm', 'B_R_Forearm', 'B_R_Hand']
poses, stats = [], []
for i, fr in enumerate(frames_in):
    sw, tw = armik.apply_arm(rig, 'R', fr['snap'], fr['wrist'], AX, fr['dir'], phi[i], psi[i], tuple(dev[i]))
    stats.append((sw, tw)); poses.append({n: rig.pose.bones[n].matrix_basis.copy() for n in ARM})
for i, f in enumerate(range(f0, f1 + 1)):
    set_act(act)
    for n in ARM:
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        q = poses[i][n].to_quaternion()
        if i and q.dot(poses[i - 1][n].to_quaternion()) < 0:
            q = -q
        pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
set_act(None)
# the free hand casts with the staff: reaches toward the target as the staff tips, thrusts forward, the arm nearly
# straight just below the shoulder, on the release, holds through the burst, returns. FREE_KEYS: source seconds, share,
# wrist offset from the shoulder in the world rest axes of the chest (+X out for this left arm, -Y forward, +Z up); the
# wrist is the clip's own (share 0) or the shoulder + offset (share 1). Offsets from the clip's wrist put the hand at
# the chin with the elbow folded up. Arm by two-bone IK in its own elbow plane, the hand kept on the forearm.
FREE_KEYS = [(0.00, 0.0, (0.0, 0.0, 0.0)), (0.12, 0.0, (0.0, 0.0, 0.0)),
             (0.40, 0.6, (0.06, -0.33, -0.28)),
             (0.80, 1.0, (0.08, -0.45, -0.10)),
             (1.05, 1.0, (0.08, -0.43, -0.12)),
             (1.45, 0.2, (0.06, -0.30, -0.30)), (1.65, 0.0, (0.06, -0.30, -0.30))]


def free_at(t):
    for (t0, k0, w0), (t1, k1, w1) in zip(FREE_KEYS[:-1], FREE_KEYS[1:]):
        if t0 <= t <= t1:
            k = ss((t - t0) / max(t1 - t0, 1e-6))
            return k0 + (k1 - k0) * k, Vector(w0).lerp(Vector(w1), k)
    return FREE_KEYS[-1][1], Vector(FREE_KEYS[-1][2])


FREE = ['B_L_UpperArm', 'B_L_Forearm', 'B_L_Hand']
R0i = C0.to_3x3().normalized().inverted()
prevq = {}
for f in range(f0, f1 + 1):
    set_act(act); scene.frame_set(f)
    hand_basis = rig.pose.bones['B_L_Hand'].matrix_basis.copy()
    C = armik.W(rig, 'B_Spine2')
    k, off = free_at(f * SPEED / 30)
    own = C.inverted() @ armik.W(rig, 'B_L_Hand').translation
    target = C @ own.lerp(C.inverted() @ armik.W(rig, 'B_L_UpperArm').translation + R0i @ off, k)
    armik.solve(rig, 'L', target)
    rig.pose.bones['B_L_Hand'].matrix_basis = hand_basis; bpy.context.view_layer.update()
    for n in FREE:
        pb = rig.pose.bones[n]; q = pb.rotation_quaternion.copy()
        if n in prevq and q.dot(prevq[n]) < 0:
            q = -q
        prevq[n] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
set_act(None)
scene['staff_release_u'] = RELEASE / (n_out * SPEED / 30)
print(f'STAFFATTACK {name} from {body_name}: frames {f1 - f0 + 1}, release at frame {RELEASE * 30 / SPEED:.1f}, '
      f'wrist swing max {max(s for s, t in stats):.1f} deg, hand twist {min(t for s, t in stats):.1f}..{max(t for s, t in stats):.1f} deg')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
