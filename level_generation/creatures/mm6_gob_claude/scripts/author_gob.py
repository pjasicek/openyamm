"""Clips for the MM6 goblin, sword always in the right fist (revision 2, after the viewer review).

Arm specs use the mirrored shoulder frame ('sh': True): x = outward from the body, y = up, z = forward, origin at the
posed shoulder joint. The torso half-width is ~0.22-0.27 m at the hips/skirt and the chest front is ~0.13 m ahead of
the shoulders, so hands stay >= 0.15 m out at hip height and >= 0.25 m forward when in front of the chest.
Walking keeps the Meshy legs/spine and replaces the arms (clavicles at rest, arms out like Standing, counter-swing).
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import author_clips as A
import posing as P
from mathutils import Vector, Matrix

v = A.variant
SWORD_R = {'sh': True, 'wrist': (0.15, -0.42, 0.14), 'pole': (0.6, -0.2, -0.6), 'blade': (0.25, -0.35, 1.0),
           'curl': 80, 'thumb': 35}
LOW_L = {'sh': True, 'wrist': (0.16, -0.46, 0.02), 'pole': (0.6, 0.0, -0.6), 'finger': (0.1, -1.0, 0.25),
         'palm': (-1.0, 0.0, 0.1), 'curl': 22, 'thumb': 10}
STAND = {'arm_R': SWORD_R, 'arm_L': LOW_L, 'hips': (0, 0, -0.012), 'spine': (3, 0, 0), 'head': (2, 0, 0)}
STANDING = [(1, STAND), (49, v(STAND, spine=(2.2, 0, 0), hips=(0, 0, -0.016))), (97, STAND)]
FIDGET = [(1, STAND),
          (4, v(STAND, spine=(4, 0, 3), head=(4, 2, 5), arm_R=v(SWORD_R, wrist=(0.16, -0.40, 0.16)))),
          (7, v(STAND, spine=(5, 0, 4), head=(5, 3, 8), arm_L=v(LOW_L, curl=8, wrist=(0.18, -0.44, 0.04)),
                arm_R=v(SWORD_R, wrist=(0.17, -0.39, 0.18), blade=(0.25, 0.2, 1.0)))),
          (10, v(STAND, spine=(4, 0, 2), head=(3, 1, 3))), (13, v(STAND, head=(2, -1, 0))), (19, STAND)]

# Attack from the native gobata a-f (125 ms each): a) sword low across the belly, b) right hand lifts across to the
# left shoulder, blade high, open left hand comes up beside it, c) blade vertical at the left shoulder, d) diagonal cut
# down to the right hip, e) arm extended out to the right, blade level, f) sword hangs at the right side, then ready.
# Spine twist +: right shoulder forward (chest turns to the character's left).
L_BALANCE = {'sh': True, 'wrist': (0.20, -0.30, 0.22), 'pole': (0.6, -0.2, -0.4), 'finger': (0.0, -0.3, 1.0),
             'palm': (-1.0, 0.0, 0.0), 'curl': 25, 'thumb': 12}
R_GRIP = {'curl': 80, 'thumb': 35}
ATTACK = [
    (1, {'arm_R': {'sh': True, 'wrist': (0.04, -0.40, 0.22), 'pole': (0.7, -0.3, -0.5), 'blade': (-0.85, 0.45, 0.3),
                   **R_GRIP},
         'arm_L': LOW_L, 'spine': (3, 0, 2), 'head': (2, 0, 0), 'hips': (0, 0, -0.012)}),
    (4, {'arm_R': {'sh': True, 'wrist': (-0.13, 0.02, 0.43), 'pole': (0.7, -0.7, 0.0), 'blade': (-0.45, 0.85, -0.15),
                   **R_GRIP},
         'arm_L': {'sh': True, 'wrist': (-0.02, -0.16, 0.38), 'pole': (0.7, -0.5, -0.2), 'finger': (-0.5, 0.2, 1.0),
                   'palm': (-0.3, 0.9, 0.0), 'curl': 38, 'thumb': 15},
         'spine': (-2, 0, 14), 'head': (0, 0, -8), 'hips': (0, 0.01, -0.015), 'feet_offset': {'Left': (0, 0.0, 0.05)}}),
    (7, {'arm_R': {'sh': True, 'wrist': (-0.10, 0.05, 0.42), 'pole': (0.7, -0.7, 0.0), 'blade': (-0.2, 1.0, -0.2),
                   **R_GRIP},
         'arm_L': {'sh': True, 'wrist': (-0.03, -0.10, 0.36), 'pole': (0.7, -0.5, -0.2), 'finger': (-0.5, 0.4, 1.0),
                   'palm': (-0.4, 0.9, 0.0), 'curl': 40, 'thumb': 15},
         'spine': (-3, 0, 18), 'head': (0, 0, -10), 'hips': (0, 0.012, -0.02), 'feet_offset': {'Left': (0, 0.0, 0.03)}}),
    (10, {'arm_R': {'sh': True, 'wrist': (0.08, -0.34, 0.34), 'pole': (0.7, -0.5, -0.3), 'blade': (-0.7, -0.25, 0.65),
                    **R_GRIP},
          'arm_L': {'sh': True, 'wrist': (-0.06, -0.30, 0.34), 'pole': (0.7, -0.2, -0.4), 'finger': (-0.6, 0.0, 1.0),
                    'palm': (-0.6, 0.0, -0.8), 'curl': 22, 'thumb': 10},
          'spine': (8, 0, -6), 'head': (6, 0, 4), 'hips': (0, -0.005, -0.03)}),
    (13, {'arm_R': {'sh': True, 'wrist': (0.34, -0.28, 0.32), 'pole': (0.4, -0.6, -0.6), 'blade': (1.0, -0.05, 0.35),
                    **R_GRIP},
          'arm_L': {'sh': True, 'wrist': (-0.02, -0.36, 0.30), 'pole': (0.7, -0.2, -0.4), 'finger': (-0.3, -0.3, 1.0),
                    'palm': (-0.5, 0.5, 0.0), 'curl': 30, 'thumb': 12},
          'spine': (14, 0, -14), 'head': (8, 0, 8), 'hips': (0, -0.01, -0.04), 'feet_offset': {'Right': (0, -0.03, 0)}}),
    (16, {'arm_R': {'sh': True, 'wrist': (0.16, -0.44, 0.16), 'pole': (0.6, -0.2, -0.6), 'blade': (0.15, -0.8, 0.55),
                    **R_GRIP},
          'arm_L': v(LOW_L, wrist=(0.19, -0.42, 0.10)), 'spine': (8, 0, -6), 'head': (6, 0, 4), 'hips': (0, 0, -0.025)}),
    (19, STAND),
]

# Hit: recoil, sword arm flung out/up, left forearm covers the face (back of the hand outward), bow, recover.
GUARD_L = {'sh': True, 'wrist': (-0.06, 0.10, 0.42), 'pole': (0.7, -0.8, 0.1), 'finger': (-0.25, 1.0, 0.1),
           'palm': (0.0, 0.0, -1.0), 'curl': 22, 'thumb': 10, 'humeral_ok': 100}
SWORD_UP = {'sh': True, 'wrist': (0.30, -0.16, 0.12), 'pole': (0.8, -0.4, -0.3), 'blade': (0.25, 1.0, 0.2),
            'curl': 80, 'thumb': 35}
HIT = [
    (1, STAND),
    (4, {'arm_R': v(SWORD_UP, wrist=(0.30, -0.26, 0.06), blade=(0.5, 0.6, 0.6)),
         'arm_L': v(GUARD_L, wrist=(0.02, -0.04, 0.42)), 'spine': (-10, 0, -8), 'head': (-12, 0, 0),
         'hips': (0, 0.03, -0.015), 'feet_offset': {'Left': (0, 0.04, 0)}}),
    (7, {'arm_R': SWORD_UP, 'arm_L': GUARD_L, 'spine': (2, 0, -6), 'head': (4, 0, 0), 'hips': (0, 0.025, -0.03),
         'feet_offset': {'Left': (0, 0.04, 0)}}),
    (10, {'arm_R': v(SWORD_UP, wrist=(0.28, -0.20, 0.14)), 'arm_L': v(GUARD_L, wrist=(-0.04, 0.06, 0.42)),
          'spine': (16, 0, -2), 'head': (12, 0, 0), 'hips': (0, 0.03, -0.05), 'feet_offset': {'Left': (0, 0.04, 0)}}),
    (13, {'arm_R': v(SWORD_R, wrist=(0.18, -0.38, 0.16)), 'arm_L': v(L_BALANCE, wrist=(0.12, -0.32, 0.22)),
          'spine': (9, 0, 0), 'head': (7, 0, 0), 'hips': (0, 0.015, -0.03)}),
    (16, v(STAND, spine=(5, 0, 0))),
    (19, STAND),
]

# Spell (Goblin Shaman/King Fire Bolt): left hand gathers in front of the chest, then thrusts forward open.
GATHER_L = {'sh': True, 'wrist': (-0.02, -0.20, 0.32), 'pole': (0.7, -0.3, -0.3), 'finger': (-0.45, 0.25, 1.0),
            'palm': (-1.0, 0.3, 0.0), 'curl': 40, 'thumb': 20}
THRUST_L = {'sh': True, 'wrist': (0.0, -0.02, 0.52), 'pole': (0.7, -0.4, 0.0), 'finger': (-0.1, 0.3, 1.0),
            'palm': (-0.7, 0.0, 0.7), 'curl': 6, 'thumb': 5}
CAST = [
    (1, STAND),
    (3, v(STAND, arm_L=v(LOW_L, wrist=(0.20, -0.36, 0.16), finger=(0.0, -0.6, 1.0)))),
    (5, {'arm_R': SWORD_R, 'arm_L': GATHER_L, 'spine': (-3, 0, 8), 'head': (0, 0, -4), 'hips': (0, 0.01, -0.02)}),
    (10, {'arm_R': SWORD_R, 'arm_L': v(GATHER_L, wrist=(-0.03, -0.12, 0.28), curl=48), 'spine': (-5, 0, 12),
          'head': (-2, 0, -6), 'hips': (0, 0.015, -0.025)}),
    (14, {'arm_R': SWORD_R, 'arm_L': THRUST_L, 'spine': (8, 0, -8), 'head': (4, 0, 4), 'hips': (0, -0.01, -0.025),
          'feet_offset': {'Left': (0, -0.04, 0)}}),
    (19, STAND),
]


def kneel_legs(hips_y, spread=0.10):
    return {side: {'ankle': (sx * spread, hips_y + 0.30, 0.07), 'pole': (sx * spread, hips_y - 1.0, -0.4),
                   'foot_pitch': -70} for side, sx in (('Left', 1), ('Right', -1))}


# Death: buckle, kneel with the left palm bracing on the ground, fall prone (corpse hips from revision 1).
DEATH = [
    (1, {'arm_R': v(SWORD_R, wrist=(0.18, -0.38, 0.20)), 'arm_L': v(LOW_L, wrist=(0.20, -0.33, 0.24)),
         'spine': (22, 0, 0), 'head': (18, 0, 0), 'hips': (0, 0.03, -0.04)}),
    (4, {'arm_R': {'sh': True, 'wrist': (0.10, -0.40, 0.30), 'pole': (0.7, -0.2, -0.3), 'blade': (0.2, -0.4, 1.0),
                   'curl': 80, 'thumb': 35},
         'arm_L': {'sh': True, 'wrist': (0.10, -0.40, 0.28), 'pole': (0.7, -0.2, -0.3), 'finger': (0.0, -1.0, 0.3),
                   'palm': (-1.0, 0.0, 0.0), 'curl': 20},
         'spine': (45, 0, 0), 'head': (20, 0, 0), 'hips': (0, 0.06, -0.20)}),
    (7, {'arm_R': {'sh': True, 'wrist': (0.20, -0.48, 0.24), 'pole': (0.7, 0.2, -0.2), 'blade': (0.4, -0.2, 1.0),
                   'curl': 80, 'thumb': 35},
         'arm_L': {'wrist_world': (0.33, -0.45, 0.06), 'pole': (0.5, 0.3, 0.2), 'finger': (0.3, -0.3, 1.0),
                   'palm': (0, -1, 0), 'curl': 10},
         'spine': (40, 0, 0), 'head': (15, 0, 0), 'hips': (0, -0.02, -0.40), 'hips_rot': (0, 25, 0),
         'legs': 'ik', 'leg_ik': kneel_legs(-0.05)}),
    (10, {'arm_R': {'sh': True, 'wrist': (0.36, 0.12, 0.20), 'pole': (0.3, -0.6, -0.6), 'blade': (0.3, 0.6, 0.0),
                    'curl': 80, 'thumb': 35},
          'arm_L': {'sh': True, 'wrist': (0.20, -0.40, 0.14), 'pole': (0.6, 0.0, -0.6), 'finger': (0.1, -1.0, 0.0),
                    'palm': (-0.3, 0.0, 1.0), 'curl': 30, 'thumb': 12},
          'drop_sword': {'out': 0.06, 'angle': 35.0},
          'spine': (2, 0, 0), 'head': (0, 22, 62), 'hips': (0, -0.42, -0.60), 'hips_rot': (-55, 88, 0), 'legs': 'fk',
          'leg_fk': {'Left': {'hip': 0, 'knee': 6, 'ankle': A.ANKLE_PRONE, 'abduct': 8},
                     'Right': {'hip': 0, 'knee': 4, 'ankle': A.ANKLE_PRONE, 'abduct': 6}}}),
]
DEATH.append((13, v(DEATH[-1][1], head=(0, 20, 60), spine=(0, 0, 2))))
DEATH.append((16, DEATH[-1][1]))
DEATH_FULL = DEATH + [(40, DEATH[-1][1])]

# Walking: arm counter-swing amplitude (m of wrist travel along forward) and phase lag (frames) behind the legs.
WALK_SWING = {'Right': 0.11, 'Left': 0.14}
WALK_LAG = 2
ARM_CHAIN = ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'ForeArmTwist1', 'ForeArmTwist2')


def walk_arms(phase_r):
    """phase_r in [-1, 1]: +1 when the right foot is furthest forward (right arm furthest back)."""
    back = max(0.0, phase_r); fwd = max(0.0, -phase_r)
    arm_r = v(SWORD_R, wrist=(0.16, -0.43 + 0.03 * fwd, 0.08 - WALK_SWING['Right'] * phase_r),
              blade=(0.2, -0.15 - 0.35 * back + 0.15 * fwd, 1.0))
    arm_l = v(LOW_L, wrist=(0.17, -0.45 + 0.05 * back, 0.04 + WALK_SWING['Left'] * phase_r),
              finger=(0.1, -1.0, 0.25 + 0.5 * back), curl=20)
    return arm_r, arm_l


def build_walk(source_blend):
    rig = A.rig
    with bpy.data.libraries.load(source_blend, link=False) as (src, dst):
        dst.actions = ['Walking']
    src_act = dst.actions[0]
    f0, f1 = (int(round(x)) for x in src_act.frame_range)
    frames = list(range(f0, f1 + 1))
    sampled, diff = [], []
    for f in frames:
        rig.animation_data.action = src_act
        bpy.context.scene.frame_set(f)
        pose = A.capture()
        lf = rig.matrix_world @ rig.pose.bones['mixamorig:LeftFoot'].head
        rf = rig.matrix_world @ rig.pose.bones['mixamorig:RightFoot'].head
        sampled.append(pose); diff.append(lf.y - rf.y)          # > 0 when the right foot is ahead (-Y forward)
    rig.animation_data.action = None
    amp = max(abs(d) for d in diff) or 1.0
    n = len(frames) - 1                                           # last frame repeats the first (loop)
    out = []
    for i, f in enumerate(frames):
        for name, (q, loc, scale) in sampled[i].items():
            b = rig.pose.bones[name]
            b.rotation_quaternion = q; b.location = loc; b.scale = scale
        for side in ('Left', 'Right'):
            for part in ARM_CHAIN:
                P.pb(rig, side + part).rotation_quaternion = (1, 0, 0, 0)
            for b in rig.pose.bones:
                if b.name.startswith(f'mixamorig:{side}Hand') and b.name != f'mixamorig:{side}Hand':
                    b.rotation_quaternion = (1, 0, 0, 0)
        bpy.context.view_layer.update()
        phase = diff[(i - WALK_LAG) % n] / amp
        arm_r, arm_l = walk_arms(phase)
        A.pose_arm('Right', arm_r); A.pose_arm('Left', arm_l)
        for side in ('Left', 'Right'):
            A.PREV_WRIST[side] = A.wrist_relative(side)
        out.append((f - f0 + 1, A.capture()))
    bpy.data.actions.remove(src_act)
    return A.write_action('Walking', out, loop=True)


LOCO_MIN_OUT = 0.17       # wrist distance out from the shoulder line while beside the hips/skirt (m)
LOCO_MIN_OUT_FRONT = {'Walking': 0.13, 'Running': 0.05}  # ... while in front of the chest
LOCO_MAX_UP_FRONT = -0.08  # pumping hands stay below shoulder height (inner arm vs pectoral)
LOCO_ELBOW_OUT = 0.14      # elbow distance out from the shoulder line (lats/ribs clearance)
LOCO_BLADE = {'Walking': (0.2, -0.35, 1.0), 'Running': (0.15, 0.8, 0.8)}
LOCO_SWING = {'Walking': 1.0, 'Running': 0.7}   # Meshy arm swing kept, around a neutral (up -0.32, fwd 0.08)
LOCO_LEFT_CURL = {'Walking': 25, 'Running': 45}
LOCO_TORSO_LEAN = {'Walking': 10.5, 'Running': 15.0}   # hips->neck forward lean (deg); Standing is 10.4
LOCO_NECK_LEAN = 18.0                                  # neck->head lean kept at the Standing value
LOCO_CLAVICLE_LIFT = {'Walking': 5.0, 'Running': 7.0}
LOCO_WRIST_UP = -0.44                                  # lowest wrist height under the shoulder (Standing -0.42..-0.46)


def lean(a, b):
    d = P.bone_world(A.rig, b) - P.bone_world(A.rig, a)
    return math.degrees(math.atan2(-d.y, d.z))


def straighten(name):
    """Pull Meshy's forward torso/neck lean back to the goblin's own posture (spine split 0.3/0.35/0.35)."""
    excess = lean('Hips', 'Neck') - LOCO_TORSO_LEAN[name]
    for bone, share in (('Spine', 0.3), ('Spine1', 0.35), ('Spine2', 0.35)):
        P.rotate_local(A.rig, 'mixamorig:' + bone, 'X', -excess * share)
    excess = lean('Neck', 'Head') - LOCO_NECK_LEAN
    for bone, share in (('Neck', 0.4), ('Head', 0.6)):
        P.rotate_local(A.rig, 'mixamorig:' + bone, 'X', -excess * share)


def build_locomotion(src_name, name):
    """Meshy locomotion (retargeted onto the rig as `src_name`) with the goblin's arms kept clear of the body:
    hips, legs, spine and head stay Meshy's; clavicles return to rest; each wrist keeps Meshy's swing but is pushed
    out to LOCO_MIN_OUT while it is beside the hips; the elbow follows Meshy's elbow; the right fist holds the sword
    (blade forward, grip solved per finger), the left hand keeps Meshy's orientation, relaxed."""
    rig = A.rig
    src = bpy.data.actions[src_name]
    f0, f1 = (int(round(x)) for x in src.frame_range)
    out = []
    for f in range(f0, f1 + 1):
        rig.animation_data.action = src
        bpy.context.scene.frame_set(f)
        pose = A.capture()
        targets = {}
        for side in ('Left', 'Right'):
            targets[side] = (P.bone_world(rig, side + 'Hand'), P.bone_world(rig, side + 'ForeArm'),
                             (rig.matrix_world @ P.pb(rig, side + 'Hand').matrix).to_quaternion())
        rig.animation_data.action = None
        for bname, (q, loc, scale) in pose.items():
            b = rig.pose.bones[bname]; b.rotation_quaternion = q; b.location = loc; b.scale = scale
        for side in ('Left', 'Right'):
            for part in ARM_CHAIN:
                P.pb(rig, side + part).rotation_quaternion = (1, 0, 0, 0)
            for b in rig.pose.bones:
                if b.name.startswith(f'mixamorig:{side}Hand') and b.name != f'mixamorig:{side}Hand':
                    b.rotation_quaternion = (1, 0, 0, 0)
        bpy.context.view_layer.update()
        for _ in range(3):
            straighten(name)
        for side in ('Left', 'Right'):
            P.rotate_local(rig, f'mixamorig:{side}Shoulder', 'X', -LOCO_CLAVICLE_LIFT[name])
        for side in ('Right', 'Left'):
            wrist, elbow, hand_q = targets[side]
            origin, x, y, z = A.shoulder_frame(side)
            d = wrist - origin
            o, u, w = d.dot(x), d.dot(y), d.dot(z)
            k = LOCO_SWING[name]
            u = -0.32 + (u + 0.32) * k; w = 0.08 + (w - 0.08) * k
            u = max(u, LOCO_WRIST_UP)
            if u < -0.25 and w < 0.20:
                o = max(o, LOCO_MIN_OUT + (0.04 if side == 'Left' else 0.0))   # open claws clear the thigh
            else:
                o = max(o, LOCO_MIN_OUT_FRONT[name])      # pumping arms never cross in front of the chest
                if w >= 0.10:
                    u = min(u, LOCO_MAX_UP_FRONT)
            wrist = origin + x * o + y * u + z * w
            e = elbow - origin                          # Meshy's elbow, kept off the ribs
            e = e + x * max(0.0, LOCO_ELBOW_OUT - e.dot(x))
            if name == 'Running':
                # running arm: elbow drives down and back, fist forward; only a little outward
                pole = origin + x * 0.20 - y * 0.6 - z * 0.7
            else:
                pole = origin + e * 1.5 + x * 0.25                # elbows out, upper arm not wrung
            A.solve_arm_low_roll(side, wrist, pole, max_dev=40 if name == 'Running' else 75)
            if side == 'Right':
                # blade across the forearm (natural hammer grip): the up+forward direction with the forearm
                # component removed, so it points up when the forearm pumps forward and forward when it hangs
                fa = (P.bone_world(rig, 'RightHand') - P.bone_world(rig, 'RightForeArm')).normalized()
                want = A.chest_dir(LOCO_BLADE[name])
                perp = want - fa * want.dot(fa)
                A.orient_blade('Right', perp.normalized() if perp.length > 0.2 else want)
                P.curl_hand(rig, 'Right', 80, thumb=35)
                A.wrap_grip('Right'); A.wrap_thumb('Right')
            else:
                hand = P.pb(rig, 'LeftHand')
                hand.matrix = Matrix.LocRotScale(hand.head.copy(), rig.matrix_world.to_quaternion().inverted() @ hand_q,
                                                 Vector((1, 1, 1)))
                bpy.context.view_layer.update()
                A.limit_wrist('Left')
                P.curl_hand(rig, 'Left', LOCO_LEFT_CURL[name], thumb=12)
            A.PREV_WRIST[side] = A.wrist_relative(side)
        out.append((f - f0 + 1, A.capture()))
    A.PREV_WRIST.clear()
    act = A.write_action(name, out, loop=True)
    bpy.data.actions.remove(src)
    return act


def build_meshy_action(src_name, name, loop=False):
    """A Meshy library clip retargeted onto the rig as `src_name`: body and arms are Meshy's; the sword stays in
    the right fist in Meshy's hand orientation (blade out of the thumb side), fingers are solved onto the grip,
    the left hand is a loose fist, wrists are kept within the anatomical limit."""
    rig = A.rig
    src = bpy.data.actions[src_name]
    f0, f1 = (int(round(x)) for x in src.frame_range)
    out = []
    A.PREV_WRIST.clear()
    for f in range(f0, f1 + 1):
        rig.animation_data.action = src
        bpy.context.scene.frame_set(f)
        pose = A.capture()
        rig.animation_data.action = None
        for bname, (q, loc, scale) in pose.items():
            b = rig.pose.bones[bname]; b.rotation_quaternion = q; b.location = loc; b.scale = scale
        for side in ('Left', 'Right'):
            for b in rig.pose.bones:
                if b.name.startswith(f'mixamorig:{side}Hand') and b.name != f'mixamorig:{side}Hand':
                    b.rotation_quaternion = (1, 0, 0, 0)
        bpy.context.view_layer.update()
        for side in ('Left', 'Right'):
            A.limit_wrist(side)
        P.curl_hand(rig, 'Right', 80, thumb=35)
        A.wrap_grip('Right'); A.wrap_thumb('Right')
        P.curl_hand(rig, 'Left', 45, thumb=15)
        for side in ('Left', 'Right'):
            A.PREV_WRIST[side] = A.wrist_relative(side)
        out.append((f - f0 + 1, A.capture()))
    A.PREV_WRIST.clear()
    act = A.write_action(name, out, loop=loop)
    bpy.data.actions.remove(src)
    return act


def split_death():
    full = bpy.data.actions['DeathFull']
    for name, first, last in (('Death', 1, 16), ('Dead', 16, 40)):
        old = bpy.data.actions.get(name)
        if old:
            bpy.data.actions.remove(old)
        act = full.copy(); act.name = name; act.use_fake_user = True
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for k in reversed(range(len(fc.keyframe_points))):
                            x = fc.keyframe_points[k].co.x
                            if x < first - 1e-3 or x > last + 1e-3:
                                fc.keyframe_points.remove(fc.keyframe_points[k])
                        for kp in fc.keyframe_points:
                            kp.co.x -= first - 1; kp.handle_left.x -= first - 1; kp.handle_right.x -= first - 1
                        fc.update()
    bpy.data.actions.remove(full)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    which = args[0].split(',') if args else ['Standing', 'Fidget', 'Attack', 'Cast_FireBolt', 'Hit', 'DeathFull',
                                             'Walking', 'Running']
    table = {'Standing': (STANDING, True), 'Fidget': (FIDGET, False), 'Attack': (ATTACK, False),
             'Cast_FireBolt': (CAST, False), 'Hit': (HIT, False), 'DeathFull': (DEATH_FULL, False)}
    for name in which:
        if name in ('Walking', 'Running'):
            if name + '_meshy' in bpy.data.actions:
                build_locomotion(name + '_meshy', name)
            elif name == 'Walking':
                build_walk(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work',
                                        'final_v1_before_anim_fix.blend'))
            print('AUTHORED', name)
            continue
        keys, loop = table[name]
        A.key_clip(name, keys, loop=loop)
        print('AUTHORED', name, keys[-1][0])
    if 'DeathFull' in which:
        split_death()
    A.rig.animation_data.action = bpy.data.actions['Standing']
    bpy.ops.wm.save_mainfile()
