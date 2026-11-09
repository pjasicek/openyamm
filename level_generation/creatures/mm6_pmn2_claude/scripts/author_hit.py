"""Hit: authored from the native pmn2 hit study (pmn2wia0-wif0, 6 x 125 ms) on the idle carry pose.
work/rig_v4.blend -> work/rig_v5.blend, action 'Hit' (18 frames at 24 fps = 0.75 s). Meshy's Hit_Reaction was not
usable: it starts in a 60-degree turned boxing stance and staggers 0.8 m sideways with real steps.
Keys k0/3/6/9/12/15 = native a-f, k18 = ready. Per key: world trunk tilt (spread over Spine/Spine1/Spine2), rib yaw,
head pitch/roll, pelvis height (fractions of H = 1.7 m), left-foot lift (the native lifts the left knee in a-c and
lands it in d), left-arm counterweight (abduction / shoulder back / elbow), and the staff (forward tilt, outward
lean of the top, grip height/side offset: thrown wide and diagonal outward in b, raised beside the face in c), with
the smallest extra adjustment per frame that keeps the whole staff 15 mm off the body. Parameters are interpolated with
smoothstep between keys. The right foot stays planted (leg IK), the left foot follows the lift, the right arm is
solved onto the staff with staff_rig.Side('Right')."""
import bpy, sys, os, math, json
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v4.blend'))
import staff_rig as sr

H = 1.7
#        k:     0      3      6      9      12     15     18
KEYS = [0, 3, 6, 9, 12, 15, 18]
P = {
    'trunk':   [-10, -18, -3, 20, 10, 0, 0],               # deg, + = forward
    'ribyaw':  [0, 8, -5, 0, 0, 0, 0],                      # deg, + = toward character right
    'head':    [-12, -15, -5, 10, 8, 0, 0],                 # deg, + = chin down
    'headroll': [0, 10, -8, 0, 0, 0, 0],                    # deg, + = toward character right
    'pelvis':  [-0.005, -0.01, -0.025, -0.05, -0.025, 0, 0],  # x H
    'lift':    [0.3, 1.0, 0.7, 0.0, 0.0, 0.0, 0.0],         # left foot lift
    'abduct':  [0, 5, 30, 35, 30, 15, 0],                   # left arm, deg
    'back':    [5, 18, 0, 0, 0, 0, 0],                      # left arm swings back, deg
    'elbow':   [0, 10, 25, 25, 20, 10, 0],                  # left elbow extra flex, deg
    'tilt':    [4, 0, 4, 10, 4, 4, 4],                      # staff forward tilt, deg
    'out':     [-0.10, -0.35, 0.0, -0.05, 0.02, 0.02, 0.02],  # staff: - = top leans out
    'gripdz':  [0.05, 0.30, 0.28, 0.0, 0.0, 0.0, 0.0],      # grip height offset, m (b: wrist near shoulder height)
    'gripdx':  [0.05, 0.28, 0.06, 0.0, 0.0, 0.0, 0.0],      # grip further out to the right, m (b: arm thrown wide)
}


def value(name, k):
    v = P[name]
    for i in range(len(KEYS) - 1):
        if KEYS[i] <= k <= KEYS[i + 1]:
            t = (k - KEYS[i]) / (KEYS[i + 1] - KEYS[i]); t = t * t * (3 - 2 * t)
            return v[i] + (v[i + 1] - v[i]) * t
    return v[-1]


carry = json.loads(sr.scene['pmn2_carry'])
HIPS_REST_Z = (sr.AW @ sr.D('Hips').head_local).z
RIGHT = sr.Side('Right')
base = sr.sample_pose('Idle_9', 0)
feet0 = {s: (sr.AW @ sr.B(s + 'Foot').matrix).copy() for s in ('Left', 'Right')}
act = bpy.data.actions.new('Hit'); act.use_fake_user = True
sr.arm.animation_data.action = act
rows = []; phi = None
Z = Vector((0, 0, 1))
for k in range(0, 19):
    sr.set_pose(base)
    hips0, F, R = sr.body_frame()
    lat_axis = Z.cross(F)                                   # rotating Z about it moves Z toward F (forward tilt)
    hb = sr.B('Hips'); M = sr.AW @ hb.matrix; M.translation.z += value('pelvis', k) * H; hb.matrix = sr.AW.inverted() @ M
    bpy.context.view_layer.update()
    for bn, share in (('Spine', 0.3), ('Spine1', 0.35), ('Spine2', 0.35)):
        sr.rotate_bone_world(bn, lat_axis, value('trunk', k) * share)
    sr.rotate_bone_world('Spine2', Z, -value('ribyaw', k))
    for bn, share in (('Neck', 0.4), ('Head', 0.6)):
        sr.rotate_bone_world(bn, lat_axis, value('head', k) * share)
        sr.rotate_bone_world(bn, F, value('headroll', k) * share)
    sr.rotate_bone_world('LeftArm', F, value('abduct', k))
    sr.rotate_bone_world('LeftArm', lat_axis, -value('back', k))
    sr.rotate_bone_world('LeftForeArm', lat_axis, value('elbow', k))
    sr.key_all(k)
    knee = (F + R * 0.15).normalized()
    miss_r = sr.leg_ik('Right', feet0['Right'], knee, k)
    lift = value('lift', k)
    lf = feet0['Left'].copy(); lf.translation += (F * 0.12 + Z * 0.20) * lift
    miss_l = sr.leg_ik('Left', lf, (F - R * 0.15).normalized(), k)
    # staff carry with per-key tilt / lean / grip height
    hips, F, R = sr.body_frame()
    Pb = sr.body_points(skip=('mixamorig:RightHand', 'mixamorig:RightForeArm', 'mixamorig:RightArm'))

    def target(dlat, dtilt, dout):
        t = math.radians(value('tilt', k) + dtilt); out = value('out', k) + dout
        a = (Z * math.cos(t) + F * math.sin(t) - R * out).normalized()
        G = Vector((hips.x, hips.y, 0)) + F * carry['fwd'] + R * (carry['lat'] + value('gripdx', k) + dlat)
        G.z = max(carry['grip_z'] + (hips.z - HIPS_REST_Z) + value('gripdz', k), 0.012 + a.z * sr.GRIP_FROM_FOOT)
        return G, a
    # smallest adjustment that keeps the whole staff 15 mm off the body (legs, skirt, torso, head, left arm)
    best = None
    for dlat in (0.0, 0.04, 0.08, 0.12):
        for dtilt in (0, 5, 10, 15):
            for dout in (0.0, -0.08, 0.08, -0.16):
                G, a = target(dlat, dtilt, dout)
                clr = sr.shaft_clearance(Pb, G, a, below_grip=sr.GRIP_FROM_FOOT, above_grip=sr.L - sr.GRIP_FROM_FOOT, radius=0.03)
                change = dlat * 100 + dtilt * 0.5 + abs(dout) * 40
                key = (clr < 0.015, change if clr >= 0.015 else -clr)
                if best is None or key < best[0]:
                    best = (key, G, a, clr, (dlat, dtilt, dout))
    _, G, a, clr, adj = best
    pole = Z * -0.6 - F * 0.6 + R * 0.4
    r = RIGHT.solve(G, a, pole, phi); phi = r['phi']; RIGHT.apply(r, k)
    row = {'k': k, 'adjust': adj, 'r_swing': round(r['sw'], 1), 'r_twist': round(r['tw'], 1), 'miss_mm': round(1000 * max(miss_r, miss_l, r['miss']), 1),
           'staff_clearance_mm': round(clr * 1000, 1), 'staff_foot_z': round((G - a * sr.GRIP_FROM_FOOT).z, 3),
           'left_foot_z': round((sr.AW @ sr.B('LeftFoot').head).z, 3)}
    rows.append(row); print('HIT', row)
act.use_frame_range = True; act.frame_start, act.frame_end = 0, 18
json.dump(rows, open(os.path.join(common.WORK, 'hit_report.json'), 'w'), indent=0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v5.blend'))
