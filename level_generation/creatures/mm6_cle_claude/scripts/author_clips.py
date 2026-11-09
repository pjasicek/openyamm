"""Authored clips from the native keys (ANIMATION_STUDY.md): work/rig_v3.blend in place.

Standing is a 4 s loop; Hit and Fidget are 0.75 s (18 frames at 24 fps, the native six frames x 125 ms); Attack and
Cast run 1.42 s: their release is marked at 0.75 s (actors.yml animation.events), so the engine fits the wind-up to the
native action and plays the rest as follow-through during the recovery. Every clip starts and ends in the Standing
pose. Keys give, per side, a grip point G, a staff/tunnel axis a and an elbow pole (world,
rest-floor frame), plus the body: hips offset and pelvis rotation, spine bend (spread over Spine01 and Spine) and head.
The feet stay planted (two-bone leg IK onto the rest feet), so hip shifts bend the knees instead of sliding the feet.
Per frame the targets are interpolated (Catmull-Rom for points, normalised Catmull-Rom for axes; never key-to-key
straight lines). The staff arm is solved with staff_rig.Side.solve with a continuity cost on the hand roll, so the hand
cannot flip between keys. The empty right fist is solved to a wrist target (rG) with an anatomical elbow hinge and a
straight wrist (free_arm). Unkeyed right arm: the standing hang (15 deg from vertical).
 - Standing (user review 2026-10-10: "really still"): breath every 2 s (chest and clavicles, head counter-nod), a slow
   weight shift between the feet over 4 s with a slight pelvis roll, and a small head drift.
 - Attack (ranged Air bolt from the staff head; melee uses it too; user review: a wind-up with the hips and centre of
   gravity, then momentum forward): the wind-up sways the hips and chest to his left and back and draws the staff up
   beside the shoulder (held to f12); the release at f18, the marker when the game fires (hips forward and down,
   chest leaning in and turning to the target), has the staff level with the ground, angled 40 deg across the body so
   the ring is in front of the chest centre (the least wrist bend of a grip/axis/elbow search: straight forward bent
   the wrist 83 deg); then the push (f22) and the staff tilting back up (f28) into the stance (f34).
 - Cast (Harm, Flying Fist): the Attack motion (user review); the charge glows at Socket_Staff_Head (actors.yml
   cast_focus_socket, as the New Sorpigal mage). A separate clip, because a caster's cast clip must differ from its
   attack clips.
 - Hit (user review: no body recoil): the hips knocked back and down, the chest and head thrown back and turned away,
   right forearm across the brow, the staff leaning out; recovery.
 - Fidget: the left arm straightens out to the side presenting the staff (lifted 14 cm) with a slight weight shift and
   turn toward it, then returns.
The intent (per key: grip, axis, staff head) is written to work/<clip>_intent.json for the trace gate."""
import bpy, sys, os, math, json
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
import staff_rig as sr
from author_lib import V, catmull, free_arm, staff_on_floor

arm = sr.arm; scene = sr.scene; AW = sr.AW
LEFT, RIGHT = sr.Side('Left'), sr.Side('Right')
CARRY = json.loads(scene['cle_carry'])
UP = Vector((0, 0, 1))
STAND_G = Vector(CARRY['stand_grip'])
POLE_L = Vector((0.3, 0.7, -0.6))
POLE_R = Vector((-0.3, 0.7, -0.6))
RIGHT_HANG_DEG = 15.0


def stand_key(f):
    return {'f': f, 'G': STAND_G, 'a': UP, 'pole': POLE_L}


# The marker (actors.yml animation.events impact) is the release at ATTACK_IMPACT_FRAME: the wind-up before it spans
# the native 0.75 s action, the follow-through after it plays in the recovery that follows.
ATTACK_IMPACT_FRAME = 18
ATTACK = [
    stand_key(0),
    {'f': 9, 'G': V(0.44, -0.06, 1.14), 'a': V(-0.08, 0.28, 0.96), 'pole': V(0.4, 0.6, -0.7),
     'hips': V(0.035, 0.02, -0.012), 'hipsrot': (0, 1.5, 6), 'spine': (-3, 2, 10), 'head': (0, -1, -6)},
    {'f': 12, 'G': V(0.45, -0.05, 1.16), 'a': V(-0.10, 0.32, 0.94), 'pole': V(0.4, 0.6, -0.7),
     'hips': V(0.04, 0.025, -0.014), 'hipsrot': (0, 1.8, 7), 'spine': (-4, 2, 11), 'head': (0, -1, -7)},
    {'f': ATTACK_IMPACT_FRAME, 'G': V(0.34, -0.28, 1.02), 'a': V(-0.64, -0.77, 0.0), 'pole': V(0.3, 0.6, -0.7),
     'hips': V(-0.01, -0.06, -0.028), 'hipsrot': (0, -1, -6), 'spine': (10, -1, -8), 'head': (-6, 0, 4)},
    {'f': 22, 'G': V(0.33, -0.32, 1.01), 'a': V(-0.64, -0.77, 0.0), 'pole': V(0.3, 0.6, -0.7),
     'hips': V(-0.01, -0.055, -0.025), 'hipsrot': (0, -1, -5), 'spine': (8, -1, -6), 'head': (-5, 0, 3)},
    {'f': 28, 'G': V(0.40, -0.16, 1.10), 'a': V(0.10, 0.12, 0.99), 'pole': V(0.5, 0.5, -0.7),
     'hips': V(0.0, -0.015, -0.008), 'hipsrot': (0, 0, -1), 'spine': (2, 0, -2)},
    stand_key(34)]
CLIPS = {
    'Attack': ATTACK,
    'Cast': [dict(k) for k in ATTACK],
    'Hit': [
        stand_key(0),
        {'f': 2, 'G': V(0.50, -0.02, 1.02), 'a': V(0.34, 0.05, 0.94), 'pole': V(0.3, 0.7, -0.6),
         'rG': V(-0.02, -0.22, 1.52), 'rpole': V(-0.3, 0.3, -0.8),
         'hips': V(0.0, 0.065, -0.035), 'hipsrot': (-4, 0, 5), 'spine': (-14, -2, 12), 'head': (-12, 0, 16)},
        {'f': 5, 'G': V(0.50, -0.02, 1.02), 'a': V(0.34, 0.05, 0.94), 'pole': V(0.3, 0.7, -0.6),
         'rG': V(-0.04, -0.24, 1.50), 'rpole': V(-0.3, 0.3, -0.8),
         'hips': V(0.0, 0.055, -0.03), 'hipsrot': (-3, 0, 4), 'spine': (-10, -2, 10), 'head': (-8, 0, 12)},
        {'f': 10, 'G': V(0.50, -0.08, 1.05), 'a': V(0.15, 0, 0.99), 'pole': POLE_L,
         'rG': V(-0.14, -0.20, 1.12), 'rpole': V(-0.7, 0.4, -0.6),
         'hips': V(0.0, 0.02, -0.01), 'hipsrot': (-1, 0, 1), 'spine': (-3, 0, 3), 'head': (-1, 0, 3)},
        stand_key(18)],
    'Fidget': [
        stand_key(0),
        {'f': 6, 'G': V(0.64, -0.06, 1.22), 'a': UP, 'pole': V(0.2, 0.6, -0.8),
         'hips': V(0.018, 0.0, -0.006), 'hipsrot': (0, 1.5, 3), 'spine': (0, 2, 5), 'head': (2, 0, 14)},
        {'f': 11, 'G': V(0.65, -0.06, 1.23), 'a': UP, 'pole': V(0.2, 0.6, -0.8),
         'hips': V(0.02, 0.0, -0.006), 'hipsrot': (0, 1.5, 3), 'spine': (-1, 2, 5), 'head': (3, 0, 15)},
        stand_key(18)],
}
REST_HIPS = (AW @ sr.D('Hips').head_local).copy()
REST_FOOT_M = {s_: (AW @ sr.D(s_ + 'Foot').matrix_local).copy() for s_ in ('Left', 'Right')}
KNEE = V(0, -1, 0.1)


def turn(bone, ang):
    for axis, deg in zip((V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), ang):
        if abs(deg) > 1e-3:
            sr.rotate_bone_world(bone, axis, deg)        # x: lean forward (toward -Y), y: bend to his left, z: turn left


def base_pose(spine, head, hips, hipsrot=(0, 0, 0), clav=0.0):
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    if hips.length > 0:
        pb = sr.B('Hips'); M = AW @ pb.matrix; M = Matrix.Translation(hips) @ M; pb.matrix = AW.inverted() @ M
        bpy.context.view_layer.update()
    turn('Hips', hipsrot)
    turn('Spine01', Vector(spine) * 0.6)
    turn('Spine', Vector(spine) * 0.4)
    turn('Head', head)
    if abs(clav) > 1e-3:                                  # breathing: both clavicles lift
        sr.rotate_bone_world('LeftShoulder', V(0, 1, 0), -clav)
        sr.rotate_bone_world('RightShoulder', V(0, 1, 0), clav)
    for side in ('Left', 'Right'):                        # feet planted
        sr.leg_ik(side, REST_FOOT_M[side], KNEE, None)
    # right arm hang: aim the upper arm 15 deg from vertical, slightly behind the hip line
    ua = sr.B('RightArm'); S = AW @ ua.head; E = AW @ sr.B('RightForeArm').head
    want = V(-math.sin(math.radians(RIGHT_HANG_DEG)), 0.03, -math.cos(math.radians(RIGHT_HANG_DEG))).normalized()
    q = (E - S).normalized().rotation_difference(want)
    M = AW @ ua.matrix; M = Matrix.Translation(S) @ q.to_matrix().to_4x4() @ Matrix.Translation(-S) @ M
    ua.matrix = AW.inverted() @ M
    bpy.context.view_layer.update()


report = {}
# Standing again with the right-arm hang (carry_staff.py keyed the plain bind pose), so all clips share frame 0
N_STAND, BREATH = 96, 48                                 # 4 s loop, a breath every 2 s
if 'Standing' in bpy.data.actions:
    bpy.data.actions.remove(bpy.data.actions['Standing'])
act = bpy.data.actions.new('Standing'); act.use_fake_user = True
phi_l = None
for f in range(N_STAND + 1):
    breath = math.sin(2 * math.pi * f / BREATH)            # inhale > 0: chest rises and opens, clavicles lift
    shift = math.sin(2 * math.pi * f / N_STAND)             # weight onto his left foot > 0
    drift = math.sin(2 * math.pi * f / N_STAND + 1.3)
    base_pose(V(-1.6 * breath, 0.6 * shift, 0.8 * drift), V(1.2 * breath, -0.8 * shift, 3.0 * drift),
              V(0.014 * shift, 0.0, -0.004 * abs(shift)), (0, 1.4 * shift, 1.0 * drift), clav=1.8 * breath)
    r = LEFT.solve(STAND_G, UP, POLE_L, phi_l, steps=72); phi_l = r['phi']
    LEFT.apply(r)
    sr.key_pose(act, f)
sr.fix_quaternion_signs(act)
for clip, keys in CLIPS.items():
    if clip in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[clip])
    act = bpy.data.actions.new(clip); act.use_fake_user = True
    phi_l = phi_r = None; rows = []
    for f in range(keys[-1]['f'] + 1):
        spine = catmull(keys, 'spine', f, (0, 0, 0)); head = catmull(keys, 'head', f, (0, 0, 0))
        hips = catmull(keys, 'hips', f, V(0, 0, 0)); hipsrot = catmull(keys, 'hipsrot', f, (0, 0, 0))
        base_pose(Vector(spine), Vector(head), hips, Vector(hipsrot))
        G = catmull(keys, 'G', f, None); a = staff_on_floor(G, catmull(keys, 'a', f, None).normalized(), 0.0)
        pole = catmull(keys, 'pole', f, None)
        r = LEFT.solve(G, a, pole, phi_l, steps=72); phi_l = r['phi']
        LEFT.apply(r)
        row = {'f': f, 'wrist_swing': round(r['sw'], 1), 'wrist_twist': round(r['tw'], 1),
               'reach_miss_mm': round(r['miss'] * 1000, 1)}
        has_r = any('rG' in k for k in keys) and any(k['f'] <= f for k in keys if 'rG' in k) \
            and any(k['f'] >= f for k in keys if 'rG' in k)
        if has_r:
            rk = [k for k in keys if 'rG' in k]
            first, last = rk[0]['f'], rk[-1]['f']
            # blend in from the hang over the frames before the first right key and out after the last one
            rG = catmull(rk, 'rG', min(max(f, first), last), None)
            rp = catmull(rk, 'rpole', min(max(f, first), last), None)
            miss = free_arm(RIGHT, rG, rp)
            row.update({'r_miss_mm': round(miss * 1000, 1)})
        sr.key_pose(act, f)
        rows.append(row)
    # right arm: frames between the stand keys and the first/last right key ease from the hang (rotation blend)
    rk = [k for k in keys if 'rG' in k]
    if rk:
        sr.set_action(act.name)
        first, last = rk[0]['f'], rk[-1]['f']
        prev_stand = max(k['f'] for k in keys if k['f'] < first)
        next_stand = min(k['f'] for k in keys if k['f'] > last)
        for f0, f1, toward in ((prev_stand, first, True), (last, next_stand, False)):
            scene.frame_set(f0); qa = {n: sr.B('Right' + n).rotation_quaternion.copy() for n in ('Arm', 'ForeArm', 'Hand')}
            scene.frame_set(f1); qb = {n: sr.B('Right' + n).rotation_quaternion.copy() for n in ('Arm', 'ForeArm', 'Hand')}
            for f in range(f0 + 1, f1):
                t = (f - f0) / (f1 - f0); t = t * t * (3 - 2 * t)
                for n in ('Arm', 'ForeArm', 'Hand'):
                    pb = sr.B('Right' + n); pb.rotation_quaternion = qa[n].slerp(qb[n], t)
                    pb.keyframe_insert('rotation_quaternion', frame=f)
        sr.detach()
    flipped = sr.fix_quaternion_signs(act)
    intent = []
    for k in keys:
        a = staff_on_floor(k['G'], k['a'].normalized(), 0.0)     # as played
        intent.append({'f': k['f'], 'grip': list(k['G']), 'axis': list(a),
                       'head': list(k['G'] + a * sr.HEAD_FROM_GRIP)})
    json.dump(intent, open(os.path.join(common.WORK, f'{clip}_intent.json'), 'w'), indent=1)
    report[clip] = rows
    print('CLIP', clip, 'left wrist swing max %.1f twist max %.1f miss max %.1f mm' % (
        max(r['wrist_swing'] for r in rows), max(abs(r['wrist_twist']) for r in rows),
        max(r['reach_miss_mm'] for r in rows)),
        ('right miss max %.1f mm' % max(r.get('r_miss_mm', 0) for r in rows)) if rk else '', 'sign flips fixed', flipped)
json.dump(report, open(os.path.join(common.WORK, 'author_report.json'), 'w'), indent=0)
sr.set_action('Standing')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
