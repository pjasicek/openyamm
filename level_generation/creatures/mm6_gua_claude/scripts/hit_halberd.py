"""Hit reaction from the native keys: work/rig_v4.blend -> work/rig_v5.blend (structure as attack_halberd.py).

Native guawina..f (ANIMATION_STUDY.md), 125 ms each = 3 frames, 750 ms (frames 0..18):
  a  0  baseline low carry, tiny recoil (trunk back 2 deg)
  b  3  right shaft rises diagonally beside the body, left arm opens low/front; trunk back 8 deg
  c  6  head/chest back 15 deg, left arm out/front at shoulder height, weapon high to the right side
  d  9  maximum recoil (trunk back 20 deg, pelvis down 1 % H): left hand above the helmet, shaft upright at the side
  e 12  head front again, left arm forward near shoulder level, shaft drops diagonally
  f 15  both arms low, weapon near the low carry; 18 = standing carry
The right hand stays on the halberd (one-handed; its roll is the carry's), the left hand is free (wrist targets,
straight wrist). The head follows the trunk back (no counter-turn). Feet planted by leg IK."""
import bpy, sys, os, math, json
from mathutils import Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v4.blend'))
import gua_rig as gr

arm, AW = gr.arm, gr.AW
UP = Vector((0, 0, 1))
F, R = Vector((0, -1, 0)), Vector((-1, 0, 0))               # character forward / right in the rest frame
RIGHT, LEFT = gr.Side('Right'), gr.Side('Left')
SEP = 0.36                                                  # left grip below the right grip along the shaft
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
def carry_axis_v():
    t = math.radians(CARRY['pitch'])
    return (F * math.cos(t) + UP * math.sin(t) - R * 0.06).normalized()


CG = body(CARRY['lat'], CARRY['fwd'], CARRY['z'])
# key: frame, right grip, shaft axis, right pole, left wrist, (unused), yaw, tilt, drop (H)
KEYS = [
    (0, CG, carry_axis_v(), v(0.4, -0.6, -0.6), body(-0.24, 0.01, 0.84), 0.0, 0, -2, 0.0),
    (3, body(0.38, 0.18, 1.10), v(0.70, 0.30, 1.0), v(1.0, -0.3, -0.5), body(-0.38, 0.20, 1.00), 0.0, 0, -8, 0.005),
    (6, body(0.46, 0.18, 1.28), v(0.85, 0.10, 1.0), v(1.0, -0.2, -0.5), body(-0.42, 0.22, 1.22), 0.0, 0, -15, 0.005),
    (9, body(0.36, 0.14, 1.18), v(0.40, 0.0, 1.0), v(1.0, -0.3, -0.5), body(-0.22, 0.02, 1.58), 0.0, 0, -20, 0.010),
    (12, body(0.30, 0.16, 0.96), v(-0.15, 0.80, -0.30), v(1.0, -0.2, -0.5), body(-0.34, 0.32, 1.22), 0.0, 0, -5, 0.005),
    (15, body(CARRY['lat'], CARRY['fwd'] + 0.06, CARRY['z'] + 0.03), carry_axis_v(), v(0.6, -0.4, -0.6),
     body(-0.27, 0.08, 0.92), 0.0, 0, 0, 0.0),
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
        if isinstance(val, Vector) and j in (2, 3):
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
    gr.rotate_bone_world('Head', UP.cross(F), min(tilt, 0) * 0.3)


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
for f in range(0, END + 1):
    gr.set_pose(base)
    if f <= LAST:
        G, a, pole, WL, on, yaw, tilt, drop = lerp_key(f)
        trunk(yaw, tilt, drop)
        feet_planted(feet)
        rr = None
        for p0 in (pole,):
            c = RIGHT.search([(G, a, 'k')], p0, phi_r, steps=72, angles=(-45, -20, 0, 20, 45), share=0.8,
                             prev_ft=prev_r[0], prev_E=prev_r[1], torso=gr.torso_penalty())
            c['cost'] += 40 * c['miss'] + 0.3 * math.degrees(gr.halberd_frame(c['Rh'])[1].angle(R.cross(a)))
            if rr is None or c['cost'] < rr['cost']:
                rr = c
        place(rr, RIGHT)
        rl = LEFT.free(WL, v(-0.6, -0.2, -0.8) if WL.z > 1.4 else v(-0.4, 0.6, -0.6))
        place(rl, LEFT)
        phi_r = rr['phi']
        prev_r = (rr['ft'], rr['E'] - rr['S'])
        rows.append({'f': f, 'right_sw': round(rr['sw'], 1), 'right_tw': round(rr['tw'], 1),
                     'right_forearm_tw': round(rr['ft'], 1), 'right_miss_mm': round(rr['miss'] * 1000, 1),
                     'left_miss_mm': round(rl['miss'] * 1000, 1),
                     'gem_z': round((AW @ gr.B('HalberdTip').head).z, 3)})
    else:
        pass                                            # 16..18 filled below by blending to the carry
    poses.append({pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in arm.pose.bones})
act = bpy.data.actions.new('Hit')
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
print('HIT quaternion flips fixed', gr.fix_quaternion_signs(act))
for r in rows:
    print('HIT', r)
json.dump(rows, open(os.path.join(common.WORK, 'hit_report.json'), 'w'), indent=0)
gr.set_action('Hit')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v5.blend'))
