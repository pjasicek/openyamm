"""Attack (two-handed halberd chop) from the native keys: work/rig_v3.blend -> work/rig_v4.blend.

Native guaatka..f (ANIMATION_STUDY.md), 125 ms each = 3 frames at 24 fps, 750 ms total (frames 0..18):
  a  0  shaft raised upright at the right side, right wrist at chest/shoulder, left arm still down
  b  3  shaft diagonal high at the right, right wrist by the temple, left hand reaches the lower shaft
  c  6  two-handed raised ready: blade above/outside the right shoulder, broadside, ribs turned right 12 deg
  d  9  downstroke toward the target (user review: the native front view draws it at image left only because it is
        2D; native e shows the shaft foreshortened = pointing at the viewer): shaft forward and a little down, both
        hands at the waist (right in front of the belly, left by the belt), blade ~1 m in front; trunk forward 8 deg
  e 12  low passage: both hands near the waist, head forward/down (edge-on)
  f 15  shaft diagonally across the chest, left hand at the lower station
    18  back to the standing carry (left hand released)
Hand targets (grip point, shaft axis toward the gem, elbow pole, wanted axe direction) are keyed in the body frame
and interpolated with a periodic-free Catmull-Rom spline; both hands are solved onto the same rigid shaft (left grip
0.36 m below the right), the right hand's roll keeps the axe edge leading, the left hand's roll is free. Trunk yaw/tilt
is spread over the three spine bones with the head turned back half way; feet stay planted by leg IK. Poses are built
with no action attached and keyed afterwards. Per-frame numbers: work/attack_report.json."""
import bpy, sys, os, math, json
from mathutils import Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
import gua_rig as gr

arm, AW = gr.arm, gr.AW
UP = Vector((0, 0, 1))
F, R = Vector((0, -1, 0)), Vector((-1, 0, 0))               # character forward / right in the rest frame
RIGHT, LEFT = gr.Side('Right'), gr.Side('Left')
SEP = 0.36                                                  # left grip below the right grip along the shaft
# forearm twist bones (twist_gua.py) carry the hand's twist along the forearm, so the solver keeps the forearm bone
# untwisted and prefers twisting over bending the wrist (user review: wrist pinch at 55 deg, forearm candy-wrap)
ELBOW_DROP = float(os.environ.get('ELBOW_DROP', '-0.01'))   # rear elbow at least this far below the shoulder
ELBOW_W = float(os.environ.get('ELBOW_W', '3000'))
TWIST = dict(share=0.0, w_sw=1.6, w_tw=float(os.environ.get('W_TW', '0.4')), tw_limit=float(os.environ.get('TW_LIM', '115')))
H = 1.578
HIPS0 = AW @ gr.D('Hips').head_local
CARRY = json.loads(gr.scene['gua_carry'])
base = gr.sample_pose('Standing', 0)
arm.animation_data.action = None


def body(lat, fwd, z):
    return Vector((HIPS0.x, HIPS0.y, 0)) + R * lat + F * fwd + UP * z


def v(r, f, u):
    return (R * r + F * f + UP * u).normalized()


def carry_axis():
    t = math.radians(CARRY['pitch'])
    return (F * math.cos(t) + UP * math.sin(t) - R * 0.06).normalized()


# key: frame, right grip, shaft axis, right pole, wanted axe dir, left on shaft (0..1), yaw, tilt, drop (H)
K8G = tuple(float(x) for x in os.environ.get('K8G', '0.14,0.30,1.32').split(','))
K8A = tuple(float(x) for x in os.environ.get('K8A', '0.35,0.2,0.9').split(','))
KD = float(os.environ.get('KD', '0.08'))
KE = float(os.environ.get('KE', '0.08'))
AD = tuple(float(x) for x in os.environ.get('AD', '0.70,0.70,-0.17').split(','))
AE = tuple(float(x) for x in os.environ.get('AE', '0.68,0.66,-0.32').split(','))
KDF = float(os.environ.get('KDF', '0.38'))
KEF = float(os.environ.get('KEF', '0.34'))
KEZ = float(os.environ.get('KEZ', '0.90'))
KET = float(os.environ.get('KET', '6'))
KEYS = [
    (0, body(0.28, 0.22, 1.12), v(0.15, 0.10, 1.0), v(1.0, -0.3, -0.6), v(1, 0, 0), 0.0, 0, 0, 0.005),
    (3, body(0.26, 0.20, 1.38), v(0.50, -0.15, 1.0), v(1.0, -0.2, -0.3), v(1, 0.3, 0), 0.6, 10, 2, 0.005),
    (6, body(0.22, 0.17, 1.44), v(0.50, -0.30, 1.0), v(1.0, -0.2, -0.2), v(1, 0.4, 0), 1.0, 12, 3, 0.010),
    (8, body(*K8G), v(*K8A), v(0.6, -0.2, -1.0), v(0.3, 0.6, -0.5), 1.0, -4, 6, 0.012),
    (9, body(KD, KDF, 0.92), v(*AD), v(0.3, 0.0, -1.0), v(0.2, 0.5, -1.0), 1.0, -4, 8, 0.015),
    (12, body(KE, KEF, KEZ), v(*AE), v(0.3, -0.2, -1.0), v(0, 0.3, -1.0), 1.0, -3, KET, 0.005),
    (15, body(0.10, 0.26, 1.18), v(0.60, 0.20, 0.70), v(0.6, -0.3, -0.7), v(0.3, 0.6, -0.3), 1.0, 0, 0, 0.0),
]
END = 18
LAST = 15


def lerp_key(f):
    """Catmull-Rom over the keys (clamped ends) for vectors and scalars; returns the blended key tuple."""
    fr = [k[0] for k in KEYS]
    i = max(j for j in range(len(fr)) if fr[j] <= f) if f < fr[-1] else len(fr) - 2
    t = (f - fr[i]) / (fr[i + 1] - fr[i])
    k0, k1 = KEYS[max(i - 1, 0)], KEYS[i]
    k2, k3 = KEYS[i + 1], KEYS[min(i + 2, len(KEYS) - 1)]

    def cr(a, b, c, d):
        return 0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
    out = []
    for j in range(1, 9):
        a, b, c, d = k0[j], k1[j], k2[j], k3[j]
        val = cr(a, b, c, d)
        if isinstance(val, Vector) and j in (2, 3, 4):
            val = val.normalized()
        out.append(val)
    return out


def trunk(yaw, tilt, drop):
    hips = gr.B('Hips')
    M = AW @ hips.matrix
    M.translation = M.translation - UP * drop * H
    hips.matrix = AW.inverted() @ M
    bpy.context.view_layer.update()
    for n in ('Spine02', 'Spine01', 'Spine'):
        gr.rotate_bone_world(n, F.cross(R), yaw / 3.0)
        gr.rotate_bone_world(n, UP.cross(F), tilt / 3.0)
    gr.rotate_bone_world('Head', F.cross(R), -yaw * 0.5)
    gr.rotate_bone_world('Head', UP.cross(F), -tilt * 0.5)


def feet_planted(feet):
    for side, Mf in feet.items():
        gr.leg_ik(side, Mf, F, None)


def place(r, side):
    for bn, R3, head in (('Arm', r['Ra'], r['S']), ('ForeArm', r['Rf'], r['E']), ('Hand', r['Rh'], r['W'])):
        pb = gr.B(side.s + bn)
        pb.rotation_mode = 'QUATERNION'
        M = R3.to_4x4()
        M.translation = head
        pb.matrix = AW.inverted() @ M
        bpy.context.view_layer.update()


AXE_W = float(os.environ.get('AXE_W', '0.4'))


def axe_cost(want):
    def cost(Rh):
        shaft, n, axe = gr.halberd_frame(Rh)
        w = (want - shaft * want.dot(shaft))
        if w.length < 1e-4:
            return 0.0
        return AXE_W * math.degrees(axe.angle(w.normalized()))
    return cost


gr.set_pose(base)
feet = {s: AW @ gr.B(s + 'Foot').matrix for s in ('Left', 'Right')}
hang_left = AW @ gr.B('LeftHand').head
poses, rows = [], []
phi_r = phi_l = None
prev_r = (None, None)
left_sgn = None
for f in range(0, END + 1):
    gr.set_pose(base)
    if f <= LAST:
        G, a, pole, want, on, yaw, tilt, drop = lerp_key(f)
        trunk(yaw, tilt, drop)
        feet_planted(feet)
        rr = None
        for p0 in (pole, v(1.0, -0.2, -0.3), v(0.3, -0.3, -1.0), v(0.6, 0.6, -0.6)):
            c = RIGHT.search([(G, a, 'k')], p0, phi_r, steps=72, angles=(-90, -60, -30, 0, 30, 60, 90), **TWIST,
                             prev_ft=prev_r[0], prev_E=prev_r[1], torso=gr.torso_penalty())
            c['cost'] += 40 * c['miss']
            if rr is None or c['cost'] < rr['cost']:
                rr = c
        # the rear (left) fist may hold the shaft either way round (thumb toward the blade or toward the butt, as a
        # real rear hand does in a low finish); changing the way round between frames costs a lot (no hand flips)
        best = None
        for sgn in (1, -1):
            for ang in (-60, -30, 0, 30, 60):
                for pr in (v(-0.4, 0.1, -1.0), v(-1.0, 0.2, -0.5), v(-0.6, -0.6, -0.5), v(-0.3, -0.4, -1.0),
                           v(-0.2, -0.8, -0.6)):
                    ax = (G - a * SEP - (AW @ gr.B('LeftArm').head)).normalized()
                    p = Quaternion(ax, math.radians(ang)) @ pr
                    rl = LEFT.solve(G - a * SEP, a * sgn, p, phi_l if sgn == left_sgn else None,
                                    torso=gr.torso_penalty(), **TWIST)
                    rl['cost'] += 0.05 * abs(ang) + 40 * rl['miss'] + (60 if left_sgn is not None and sgn != left_sgn else 0)
                    # the rear elbow hangs down and back by the ribs (user review: no chicken wing above the shoulder)
                    rl['cost'] += ELBOW_W * max(0.0, rl['E'].z - (rl['S'].z - ELBOW_DROP))
                    rl['sgn'] = sgn
                    if best is None or rl['cost'] < best['cost']:
                        best = rl
        rl = best
        if on >= 0.999:
            left_sgn = rl['sgn']
        place(rr, RIGHT)
        if on >= 0.999:
            place(rl, LEFT)
        else:                                           # reaching: wrist moves from the hang toward the shaft grip
            W = hang_left.lerp(rl['W'], on)
            place(LEFT.free(W, v(-0.5, -0.3, -1.0)), LEFT)
        phi_r, phi_l = rr['phi'], rl['phi']
        prev_r = (rr['ft'], rr['E'] - rr['S'])
        shaft, n, axe = gr.halberd_frame(rr['Rh'])
        rows.append({'f': f, 'right_sw': round(rr['sw'], 1), 'right_tw': round(rr['tw'], 1),
                     'right_forearm_tw': round(rr['ft'], 1),
                     'left_sw': round(rl['sw'], 1), 'left_tw': round(rl['tw'], 1),
                     'left_miss_mm': round(rl['miss'] * 1000, 1) if on >= 0.999 else None,
                     'right_miss_mm': round(rr['miss'] * 1000, 1),
                     'gem_z': round((AW @ gr.B('HalberdTip').head).z, 3),
                     'axe_body': [round(axe.dot(R), 2), round(axe.dot(F), 2), round(axe.dot(UP), 2)]})
    else:
        pass                                            # 16..18 filled below by blending to the carry
    poses.append({pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in arm.pose.bones})
# halberd roll (user review: the blade must slice): the Halberd bone rolls about the shaft inside the fist so the axe
# edge (bone +X, the crescent side; -X is the spike) leads the blade head's motion during the downstroke (STRIKE frames, velocity perpendicular to the
# shaft), and faces the overall strike direction (head at the last strike frame minus head at the first) in the
# wind-up and just after the strike, so the spike side leads the lift and the edge never flips. Eased from the carry
# roll at the start and back toward it in the recovery; frames 16-18 then slerp to the carry pose.
STRIKE = range(7, 12)
BLADE = gr.L - gr.GRIP_FROM_FOOT - 0.11 * H            # grip -> blade centre along the shaft
frames_info = []
for f in range(0, LAST + 1):
    gr.set_pose(poses[f])
    M = AW @ gr.B('Halberd').matrix
    M3 = M.to_3x3().normalized()
    shaft = (M3 @ Vector((0, 1, 0))).normalized()
    frames_info.append((shaft, (M3 @ Vector((1, 0, 0))).normalized(), M.translation + shaft * BLADE))   # +X = axe
d_strike = (frames_info[STRIKE[-1]][2] - frames_info[STRIKE[0] - 1][2]).normalized()
d_strike = (d_strike + Vector((0, 0, -0.6))).normalized()        # the crescent hangs down at the end of the cut
ease = {0: 0.0, 1: 0.1, 2: 0.35, 3: 0.65, 4: 0.9}
roll = []
for f, (shaft, axe0, head) in enumerate(frames_info[:STRIKE[-1] + 1]):
    w = d_strike
    if f in STRIKE:
        vel = frames_info[min(f + 1, LAST)][2] - frames_info[max(f - 1, 0)][2]
        if (vel - shaft * vel.dot(shaft)).length > 0.06:   # follow the motion only while the blade moves fast
            w = vel.normalized()
    w = w - shaft * w.dot(shaft)
    th = math.atan2(axe0.cross(w).dot(shaft), axe0.dot(w)) if w.length > 1e-4 else (roll[-1] if roll else 0.0)
    if roll and f > 1:                                  # unwrap toward the previous frame (the short way from carry first)
        while th - roll[-1] > math.pi:
            th -= 2 * math.pi
        while th - roll[-1] < -math.pi:
            th += 2 * math.pi
    roll.append(th)
k = round(roll[STRIKE[0]] / (2 * math.pi))              # the short way from the carry roll (0) to the strike roll
roll = [r - 2 * math.pi * k for r in roll]
last = STRIKE[-1]
for f in range(last + 1, LAST + 1):                     # recovery: ease from the last strike roll back toward carry
    u = (f - last) / (END - last)
    roll.append(roll[last] * (1 - u * u * (3 - 2 * u)))
sm = [roll[0]] + [(roll[i - 1] + 2 * roll[i] + roll[i + 1]) / 4 for i in range(1, LAST)] + [roll[LAST]]
for f in range(0, LAST + 1):
    th = sm[f] * ease.get(f, 1.0)
    q, loc = poses[f]['Halberd']
    poses[f]['Halberd'] = (Quaternion((0, 1, 0), th) @ q, loc)
print('ROLL deg', [round(math.degrees(sm[f] * ease.get(f, 1.0))) for f in range(LAST + 1)])
act = bpy.data.actions.new('Attack')
act.use_fake_user = True
arm.animation_data.action = act
if getattr(act, 'slots', None) and len(act.slots):
    arm.animation_data.action_slot = act.slots[0]
carry = gr.sample_pose('Standing', 0)
arm.animation_data.action = act
for f in range(0, END + 1):
    if f <= LAST:
        pose = poses[f]
    else:                                               # ease from key f to the carry pose
        t = (f - LAST) / (END - LAST)
        t = t * t * (3 - 2 * t)
        pose = {}
        for n, (q, loc) in poses[LAST].items():
            q2, l2 = carry[n]
            if q.dot(q2) < 0:
                q2 = -q2
            pose[n] = (q.slerp(q2, t), loc.lerp(l2, t))
    gr.set_pose(pose)
    gr.key_all(f)
print('ATTACK quaternion flips fixed', gr.fix_quaternion_signs(act))
for r in rows:
    print('ATK', r)
json.dump(rows, open(os.path.join(common.WORK, 'attack_report.json'), 'w'), indent=0)
gr.set_action('Attack')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v4.blend'))
