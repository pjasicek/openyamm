"""Author the native-derived clips (Standing, Fidget, Attack, Hit, DeathFull) as keyed poses at 24 fps.

Coordinates: world X = character left, -Y = forward, Z = up. Arm targets are chest-local (left, up, forward)
relative to the posed Spine2 head. Timing follows ANIMATION_STUDY.md: 125 ms native entries = 3 frames.
"""
import bpy, sys, os, math, json
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, posing as P

rig = bpy.data.objects['Peasant_Rig']
if rig.animation_data is not None:
    rig.animation_data.action = None          # an attached action would re-evaluate over the pose being built
REST = {b.name: rig.matrix_world @ b.matrix_local for b in rig.data.bones}


def rest_head(name):
    return REST['mixamorig:' + name].translation.copy()


ANKLE = {s: rest_head(s + 'Foot') for s in ('Left', 'Right')}
HIPS_REST = rest_head('Hips')


def hand_rest_frame(side):
    """Finger direction and palm normal measured from the rig: the palm is where flexing fingertips move."""
    P.reset(rig)
    hand = rest_head(side + 'Hand')
    f = (rest_head(side + 'HandMiddle1') - hand).normalized()
    tip0 = P.bone_world(rig, side + 'HandMiddle3', tail=True)
    P.rotate_local(rig, 'mixamorig:' + side + 'HandMiddle1', 'X', 20)
    tip1 = P.bone_world(rig, side + 'HandMiddle3', tail=True)
    P.reset(rig)
    p = tip1 - tip0
    p = (p - f * p.dot(f)).normalized()
    return f, p


HAND_REST = {s: hand_rest_frame(s) for s in ('Left', 'Right')}


def chest_matrix():
    """Chest frame: canonical body axes at rest (x = left, y = up, z = forward), carried by the posed Spine2."""
    posed = rig.matrix_world @ P.pb(rig, 'Spine2').matrix
    rest = REST['mixamorig:Spine2']
    delta = (posed.to_3x3() @ rest.to_3x3().inverted()).normalized()
    canon = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))            # columns: left, up, forward
    m = (delta @ canon).to_4x4()
    m.translation = posed.translation
    return m


def chest_point(local):
    m = chest_matrix()
    x, y, z = (m.col[i].xyz.normalized() for i in range(3))
    return m.translation + x * local[0] + y * local[1] + z * local[2]


def chest_dir(local):
    m = chest_matrix()
    x, y, z = (m.col[i].xyz.normalized() for i in range(3))
    return (x * local[0] + y * local[1] + z * local[2]).normalized()


def frame_from(f, p):
    f = f.normalized(); p = (p - f * p.dot(f)).normalized()
    return Matrix((f, p, f.cross(p))).transposed()


def orient_hand(side, finger=None, palm=None, blade=None, limit=True):
    """Set the hand world rotation from finger/palm directions (or blade/palm for the knife hand)."""
    f0, p0 = HAND_REST[side]
    if blade is not None:
        # map the prop's rest frame (blade axis, palm normal) onto the requested one
        prop = json.loads(bpy.context.scene.get('pfem_sword') or bpy.context.scene['pfem_knife'])
        b0 = Vector(prop['blade_dir'])
        R = frame_from(blade, palm) @ frame_from(b0, p0).inverted()
    else:
        R = frame_from(finger, palm) @ frame_from(f0, p0).inverted()
    bone = P.pb(rig, side + 'Hand')
    rest_rot = REST['mixamorig:' + side + 'Hand'].to_3x3()
    head = bone.head.copy()
    bone.matrix = Matrix.LocRotScale(head, (R @ rest_rot).to_quaternion(), Vector((1, 1, 1)))
    bpy.context.view_layer.update()
    if limit:
        limit_wrist(side)


WRIST_SWING_LIMIT = math.radians(70)


PREV_WRIST = {}            # side -> previous key's hand rotation relative to the forearm (roll continuity)


def wrist_relative(side):
    fa = P.pb(rig, side + 'ForeArm'); hand = P.pb(rig, side + 'Hand')
    rest_rel = fa.bone.matrix_local.to_quaternion().inverted() @ hand.bone.matrix_local.to_quaternion()
    return rest_rel.inverted() @ (fa.matrix.to_quaternion().inverted() @ hand.matrix.to_quaternion())


def wrist_strain(side):
    d = wrist_relative(side)
    swing, twist = d.to_swing_twist('Y')
    strain = swing.angle + abs(twist) + 3.0 * max(0.0, abs(twist) - math.radians(100))
    if side in PREV_WRIST:
        strain += 0.5 * d.rotation_difference(PREV_WRIST[side]).angle
    return strain


BLADE_CONE_DEG = 35.0


def orient_blade(side, blade):
    """Point the held prop near `blade`: search rolls about the blade and small tilts of the blade itself (up to
    BLADE_CONE_DEG), trading direction error against wrist strain so the wrist never has to fold."""
    blade = blade.normalized()
    u = blade.orthogonal().normalized(); v = blade.cross(u)
    candidates = [(blade, 0.0)]
    for tilt in (12.0, 24.0, BLADE_CONE_DEG):
        for k in range(8):
            a = math.radians(45 * k)
            axis = u * math.cos(a) + v * math.sin(a)
            candidates.append(((Quaternion(axis, math.radians(tilt)) @ blade).normalized(), math.radians(tilt)))
    best = None
    for cand, err in candidates:
        ref = cand.orthogonal().normalized()
        for k in range(24):
            palm = Quaternion(cand, math.radians(15 * k)) @ ref
            orient_hand(side, palm=palm, blade=cand, limit=False)
            d = wrist_relative(side); swing, twist = d.to_swing_twist('Y')
            cost = wrist_strain(side) + 2.0 * max(0.0, swing.angle - math.radians(45)) + 0.8 * err
            if best is None or cost < best[0]:
                best = (cost, palm, cand)
    orient_hand(side, palm=best[1], blade=best[2])


def limit_wrist(side):
    """Keep wrist flexion/deviation anatomical; twist is left for the forearm twist bones."""
    fa = P.pb(rig, side + 'ForeArm'); hand = P.pb(rig, side + 'Hand')
    rest_rel = fa.bone.matrix_local.to_quaternion().inverted() @ hand.bone.matrix_local.to_quaternion()
    fa_q = fa.matrix.to_quaternion()
    d = rest_rel.inverted() @ (fa_q.inverted() @ hand.matrix.to_quaternion())
    swing, twist = d.to_swing_twist('Y')
    if swing.angle <= WRIST_SWING_LIMIT:
        return
    swing = Quaternion().slerp(swing, WRIST_SWING_LIMIT / swing.angle)
    q = fa_q @ rest_rel @ swing @ Quaternion((0, 1, 0), twist)
    hand.matrix = Matrix.LocRotScale(hand.head.copy(), q, Vector((1, 1, 1)))
    bpy.context.view_layer.update()


def set_foot_world(side, pitch=0.0):
    bone = P.pb(rig, side + 'Foot')
    rest_rot = REST['mixamorig:' + side + 'Foot'].to_3x3()
    R = Matrix.Rotation(math.radians(pitch), 3, 'X')
    bone.matrix = Matrix.LocRotScale(bone.head.copy(), (R @ rest_rot).to_quaternion(), Vector((1, 1, 1)))
    bpy.context.view_layer.update()


def apply_pose(spec):
    P.reset(rig)
    hips = P.pb(rig, 'Hips')
    off = Vector(spec.get('hips', (0, 0, 0)))
    hips.matrix = Matrix.Translation(off) @ hips.matrix
    bpy.context.view_layer.update()
    yaw, pitch, roll = spec.get('hips_rot', (0, 0, 0))
    if yaw: P.rotate_local(rig, 'mixamorig:Hips', 'Y', yaw)
    if pitch: P.rotate_local(rig, 'mixamorig:Hips', 'X', pitch)
    if roll: P.rotate_local(rig, 'mixamorig:Hips', 'Z', roll)
    legs = spec.get('legs', 'planted')
    for side, sx in (('Left', 1), ('Right', -1)):
        if legs == 'planted':
            target = ANKLE[side] + Vector(spec.get('feet_offset', {}).get(side, (0, 0, 0)))
            pole = target + Vector((0.03 * sx, -0.6, 0.45))
            P.two_bone_ik(rig, f'mixamorig:{side}UpLeg', f'mixamorig:{side}Leg', target, pole)
            set_foot_world(side, spec.get('foot_pitch', {}).get(side, 0.0))
        elif legs == 'ik':
            leg = spec['leg_ik'][side]
            P.two_bone_ik(rig, f'mixamorig:{side}UpLeg', f'mixamorig:{side}Leg', Vector(leg['ankle']), Vector(leg['pole']))
            if 'foot_pitch' in leg:
                set_foot_world(side, leg['foot_pitch'])
        elif legs == 'fk':
            leg = spec['leg_fk'][side]
            P.rotate_local(rig, f'mixamorig:{side}UpLeg', 'X', leg.get('hip', 0))
            if leg.get('abduct'): P.rotate_local(rig, f'mixamorig:{side}UpLeg', 'Z', leg['abduct'] * -sx)
            P.rotate_local(rig, f'mixamorig:{side}Leg', 'X', -leg.get('knee', 0))
            if leg.get('ankle'): P.rotate_local(rig, f'mixamorig:{side}Foot', 'X', leg['ankle'])
    fwd, right, twist = spec.get('spine', (0, 0, 0))
    for name, share in (('Spine', 0.3), ('Spine1', 0.35), ('Spine2', 0.35)):
        if fwd: P.rotate_local(rig, 'mixamorig:' + name, 'X', fwd * share)
        if right: P.rotate_local(rig, 'mixamorig:' + name, 'Z', right * share)
        if twist: P.rotate_local(rig, 'mixamorig:' + name, 'Y', twist * share)
    nf, nr, nt = spec.get('head', (0, 0, 0))
    for name, share in (('Neck', 0.4), ('Head', 0.6)):
        if nf: P.rotate_local(rig, 'mixamorig:' + name, 'X', nf * share)
        if nr: P.rotate_local(rig, 'mixamorig:' + name, 'Z', nr * share)
        if nt: P.rotate_local(rig, 'mixamorig:' + name, 'Y', nt * share)
    pose_arms(spec)
    if 'drop_sword' in spec:
        drop_sword(**spec['drop_sword'])
    knife = P.pb(rig, 'Knife') if 'Knife' in rig.pose.bones else P.pb(rig, 'Sword')
    s = 1.0 if spec.get('knife', 'Sword' in rig.pose.bones) else 0.0
    knife.scale = (s, s, s)
    bpy.context.view_layer.update()


def drop_sword(out=0.06, angle=30.0, height=0.015):
    """Lay the sword flat on the ground beside the right hand (it leaves the fist when the body hits the floor)."""
    prop = json.loads(bpy.context.scene['pfem_sword'])
    origin, x, y, z = shoulder_frame('Right')
    hand = P.bone_world(rig, 'RightHand')
    flat_out = Vector((x.x, x.y, 0)).normalized()
    blade = (Matrix.Rotation(math.radians(angle), 3, 'Z') @ flat_out) if flat_out.cross(Vector((y.x, y.y, 0))).z > 0 \
        else (Matrix.Rotation(-math.radians(angle), 3, 'Z') @ flat_out)
    grip = hand + flat_out * out
    grip.z = height
    R = frame_from(blade, Vector((0, 0, 1))) @ frame_from(Vector(prop['blade_dir']), Vector(prop['palm_normal'])).inverted()
    inv = rig.matrix_world.inverted()
    bone = P.pb(rig, 'Sword')
    rest = rig.matrix_world @ bone.bone.matrix_local
    world = Matrix.Translation(grip) @ R.to_4x4() @ Matrix.Translation(-Vector(prop['grip'])) @ rest
    bone.matrix = inv @ world
    bpy.context.view_layer.update()


def shoulder_frame(side):
    """Mirrored per-side frame at the posed shoulder joint: x = outward, y = up, z = forward (chest axes)."""
    m = chest_matrix()
    x, y, z = (m.col[i].xyz.normalized() for i in range(3))
    if side == 'Right':
        x = -x
    return P.bone_world(rig, side + 'Arm'), x, y, z


def arm_elevation(side):
    m = chest_matrix(); down = -m.col[1].xyz.normalized()
    arm = P.pb(rig, side + 'Arm')
    return math.degrees((arm.tail - arm.head).normalized().angle(down))


SHRUG_FROM = 70.0


def pose_arm(side, arm):
    """Place one arm. With 'sh': True every vector is in the mirrored shoulder frame (out, up, forward)."""
    if arm.get('shrug'):
        P.rotate_local(rig, f'mixamorig:{side}Shoulder', 'X', -arm['shrug'])
    if arm.get('sh'):
        origin, x, y, z = shoulder_frame(side)
        point = lambda v: origin + x * v[0] + y * v[1] + z * v[2]
        direction = lambda v: (x * v[0] + y * v[1] + z * v[2]).normalized()
    else:
        point, direction = chest_point, chest_dir
    wrist = Vector(arm['wrist_world']) if 'wrist_world' in arm else point(arm['wrist'])
    pole = point(arm['pole'])
    solve_arm(side, wrist, pole, arm.get('humeral_ok'))
    elev = arm_elevation(side)
    if arm.get('sh') and elev > SHRUG_FROM and not arm.get('shrug'):
        # raised arms lift the clavicle so the shoulder cap and pauldron are not crushed
        P.rotate_local(rig, f'mixamorig:{side}Shoulder', 'X', -min(22.0, (elev - SHRUG_FROM) * 0.5))
        solve_arm(side, wrist, pole, arm.get('humeral_ok'))
    if 'blade' in arm:
        orient_blade(side, direction(arm['blade']))
    elif 'finger' in arm:
        orient_hand(side, finger=direction(arm['finger']), palm=direction(arm['palm']))
    P.curl_hand(rig, side, arm.get('curl', 15), thumb=arm.get('thumb'))
    if 'blade' in arm and 'Sword' in rig.pose.bones:
        wrap_grip(side)
    if arm.get('curl', 15) >= 60:
        wrap_thumb(side)


GRIP_RADIUS = 0.0135
GRIP_HALF = 0.048
FINGER_RADIUS = 0.010


def grip_axis():
    """World grip centre and direction of the posed sword (rest prop frame carried by the Sword bone)."""
    prop = json.loads(bpy.context.scene['pfem_sword'])
    bone = P.pb(rig, 'Sword')
    m = rig.matrix_world @ bone.matrix @ (rig.matrix_world @ bone.bone.matrix_local).inverted()
    return m @ Vector(prop['grip']), (m.to_3x3() @ Vector(prop['blade_dir'])).normalized()


def wrap_grip(side):
    """Curl each finger only until its phalanges lie on the grip surface (no empty ring, no finger through it)."""
    centre, axis = grip_axis()
    target = GRIP_RADIUS + FINGER_RADIUS

    def dist(p):
        d = p - centre
        return (d - axis * d.dot(axis)).length

    for name in ('Index', 'Middle', 'Ring', 'Pinky'):
        bones = [f'mixamorig:{side}Hand{name}{k}' for k in (1, 2, 3)]
        if bones[0] not in rig.pose.bones or P.pb(rig, bones[0]).length < 0.01:
            continue
        def pose_finger(spread, c1, c2):
            for b in bones:
                P.pb(rig, b).rotation_quaternion = Quaternion((1, 0, 0), 0)
            P.pb(rig, bones[0]).rotation_quaternion = Quaternion((0, 0, 1), math.radians(spread))
            for k, b in enumerate(bones):
                P.pb(rig, b).rotation_quaternion = P.pb(rig, b).rotation_quaternion @ \
                    Quaternion((1, 0, 0), math.radians(c1 if k == 0 else c2))
            bpy.context.view_layer.update()

        def cost(spread, c1, c2):
            pose_finger(spread, c1, c2)
            pts = [P.bone_world(rig, f'{side}Hand{name}{k}') for k in (2, 3)] + \
                  [P.bone_world(rig, f'{side}Hand{name}3', tail=True)]
            # contact points must lie along the handle (not past its ends) and on its surface, not inside it
            return sum((dist(p) - target) ** 2 for p in pts) + \
                4.0 * sum(max(0.0, target * 0.85 - dist(p)) ** 2 for p in pts) + \
                10.0 * sum(max(0.0, abs((p - centre).dot(axis)) - GRIP_HALF) ** 2 for p in pts) + 1e-6 * spread * spread

        # coarse grid over spread (knuckle side-swing), knuckle curl and distal curl, then a local refinement
        best = min((cost(sp, c1, c2), sp, c1, c2) for sp in range(-15, 16, 5) for c1 in range(10, 101, 10)
                   for c2 in range(20, 121, 10))
        step = 5.0
        while step >= 1.25:
            cand = min((cost(best[1] + dsp, best[2] + d1, best[3] + d2), best[1] + dsp, best[2] + d1, best[3] + d2)
                       for dsp in (-step, 0, step) for d1 in (-step, 0, step) for d2 in (-step, 0, step))
            if cand[0] >= best[0]:
                step /= 2
            else:
                best = cand
        pose_finger(best[1], best[2], best[3])


def wrap_thumb(side, iterations=6):
    """Closed fist: lay the thumb tip over the middle joints of the index/middle fingers (CCD on the thumb chain)."""
    pip = [P.bone_world(rig, f'{side}Hand{n}3') for n in ('Index', 'Middle')]
    hand = P.pb(rig, side + 'Hand')
    knuckles = (P.bone_world(rig, f'{side}HandIndex1') + P.bone_world(rig, f'{side}HandMiddle1')) / 2
    out = ((pip[0] + pip[1]) / 2 - knuckles)
    back = (knuckles - P.bone_world(rig, side + 'Hand')).normalized()
    target = (pip[0] + pip[1]) / 2 + (out - back * out.dot(back)).normalized() * 0.004 - back * 0.006
    for _ in range(iterations):
        for name in (f'{side}HandThumb2', f'{side}HandThumb1'):
            tip = P.bone_world(rig, f'{side}HandThumb3', tail=True)
            head = P.bone_world(rig, name)
            q = (tip - head).rotation_difference(target - head)
            q = Quaternion().slerp(q, 0.7)
            P.rotate_world(rig, name, q.axis, math.degrees(q.angle))


def humeral_roll(side):
    """Upper-arm roll about its own axis relative to the clavicle, rest-relative (deg). Large values wring the skin."""
    sh = P.pb(rig, side + 'Shoulder'); arm = P.pb(rig, side + 'Arm')
    rel0 = sh.bone.matrix_local.to_quaternion().inverted() @ arm.bone.matrix_local.to_quaternion()
    d = rel0.inverted() @ (sh.matrix.to_quaternion().inverted() @ arm.matrix.to_quaternion())
    return math.degrees(d.to_swing_twist('Y')[1])


HUMERAL_OK = 40.0


def solve_arm(side, wrist, pole, humeral_ok=None):
    """Hinge IK toward `pole`; if that wrings the upper arm, try elbow directions around the shoulder-wrist line
    and keep the one with the least upper-arm roll that stays near the requested elbow direction."""
    upper, lower = f'mixamorig:{side}Arm', f'mixamorig:{side}ForeArm'
    P.two_bone_ik_hinge(rig, upper, lower, wrist, pole)
    if abs(humeral_roll(side)) <= (humeral_ok or HUMERAL_OK):
        return
    shoulder = P.bone_world(rig, side + 'Arm')
    axis = (wrist - shoulder).normalized()
    base = pole - shoulder
    _, out_dir, _, _ = shoulder_frame(side)
    best = None
    for deg in range(-120, 121, 15):
        cand = shoulder + Quaternion(axis, math.radians(deg)) @ base
        P.two_bone_ik_hinge(rig, upper, lower, wrist, cand)
        elbow = P.bone_world(rig, side + 'ForeArm')
        inward = max(0.0, 0.02 - (elbow - shoulder).dot(out_dir))       # elbow must stay outside the shoulder line
        cost = max(0.0, abs(humeral_roll(side)) - 25.0) + 0.35 * abs(deg) + max(0.0, arm_elevation(side) - 100.0) \
            + 3000.0 * inward
        if best is None or cost < best[0]:
            best = (cost, cand)
    P.two_bone_ik_hinge(rig, upper, lower, wrist, best[1])


def solve_arm_low_roll(side, wrist, pole, target_roll=5.0, max_dev=75):
    """Elbow direction (rotation about the shoulder-wrist line) that keeps the upper-arm roll near its rest
    value; for cyclic clips, where swinging roll reads as the upper arm wringing."""
    upper, lower = f'mixamorig:{side}Arm', f'mixamorig:{side}ForeArm'
    shoulder = P.bone_world(rig, side + 'Arm')
    axis = (wrist - shoulder).normalized()
    base = pole - shoulder
    _, out_dir, _, _ = shoulder_frame(side)

    def cost(deg):
        cand = shoulder + Quaternion(axis, math.radians(deg)) @ base
        P.two_bone_ik_hinge(rig, upper, lower, wrist, cand)
        elbow = P.bone_world(rig, side + 'ForeArm')
        inward = max(0.0, 0.10 - (elbow - shoulder).dot(out_dir))
        return abs(humeral_roll(side) - target_roll) + 0.05 * abs(deg) + 1500.0 * inward

    best = min((cost(d), d) for d in range(-max_dev, max_dev + 1, 5))
    d = best[1]
    for step in (2.5, 1.0):
        d = min((cost(d + k * step), d + k * step) for k in (-1, 0, 1))[1]
    cost(d)


def pose_arms(spec):
    for side in ('Right', 'Left'):
        arm = spec.get('arm_' + side[0])
        if arm:
            pose_arm(side, arm)


def capture():
    return {b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in rig.pose.bones}


def write_action(name, frames, loop=False, hold=False):
    """frames: list of (frame, captured pose). Keys are written without depsgraph re-evaluation."""
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    action = bpy.data.actions.new(name); action.use_fake_user = True
    rig.animation_data.action = action
    previous = {}
    for frame, pose in frames:
        for bone in rig.pose.bones:
            q, loc, scale = pose[bone.name]
            q = q.copy()
            if bone.name in previous and previous[bone.name].dot(q) < 0:
                q.negate()
            previous[bone.name] = q
            bone.rotation_quaternion = q; bone.location = loc; bone.scale = scale
            if bone.name.startswith(('Skirt_', 'Braid_')):
                continue
            bone.keyframe_insert('rotation_quaternion', frame=frame)
            if bone.name == 'mixamorig:Hips':
                bone.keyframe_insert('location', frame=frame)
            if bone.name in ('Knife', 'Sword'):
                bone.keyframe_insert('scale', frame=frame)
                bone.keyframe_insert('location', frame=frame)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'BEZIER'
                        kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
                    fc.update()
    action['loop'] = loop
    action['hold'] = hold
    rig.animation_data.action = None
    return action


def key_clip(name, keys, loop=False, hold=False):
    """keys: list of (frame, spec), posed with no action attached so nothing re-evaluates mid-pose."""
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    frames = []
    PREV_WRIST.clear()
    for frame, spec in keys:
        apply_pose(spec)
        for side in ('Left', 'Right'):
            PREV_WRIST[side] = wrist_relative(side)
        frames.append((frame, capture()))
    PREV_WRIST.clear()
    return write_action(name, frames, loop=loop, hold=hold)


# ------------------------------------------------------------------ poses
CLASP = {
    # right hand lies across the back of the left, both nearly level, palms toward the body (native pfemsta)
    'arm_R': {'wrist': (-0.070, -0.222, 0.248), 'pole': (-0.5, -0.05, -0.35), 'finger': (0.93, -0.33, 0.08),
              'palm': (0.25, 0.30, -0.92), 'curl': 30, 'thumb': 10},
    'arm_L': {'wrist': (0.068, -0.238, 0.222), 'pole': (0.5, -0.05, -0.35), 'finger': (-0.93, -0.36, 0.02),
              'palm': (-0.20, 0.25, -0.95), 'curl': 22, 'thumb': 8},
    'hips': (0, 0, -0.004),
}


def variant(base, **changes):
    out = json.loads(json.dumps(base))
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key].update(value)
        else:
            out[key] = value
    return out


INHALE = variant(CLASP, spine=(-0.8, 0, 0), head=(0.5, 0, 0), hips=(0, 0, -0.002))
STANDING = [(1, CLASP), (49, INHALE), (97, CLASP)]

FIDGET = [
    (1, CLASP),
    (5, variant(CLASP, head=(2, -3, 6), spine=(0, -0.6, 1.0))),
    (10, variant(CLASP, head=(-3, 4, 11), spine=(-0.5, 0.5, 2.0), hips=(0.004, 0, -0.004),
                 arm_R={'curl': 34}, arm_L={'curl': 18})),
    (14, variant(CLASP, head=(1, 1, 4))),
    (19, CLASP),
]

KNIFE_LOW = {'wrist': (-0.24, -0.36, 0.06), 'pole': (-0.4, 0.0, -0.4), 'blade': (0.0, -0.45, 1.0),
             'palm': (1.0, 0.0, 0.0), 'curl': 80, 'thumb': 35}
ATTACK = [
    (1, {'arm_R': KNIFE_LOW, 'arm_L': {'wrist': (0.13, -0.23, 0.13), 'pole': (0.45, -0.1, -0.3),
          'finger': (-0.2, -1, 0.1), 'palm': (-1, 0, -0.2), 'curl': 25}, 'spine': (3, 0, -3), 'head': (6, 2, -4),
          'hips': (0, 0, -0.008), 'knife': True}),
    (4, {'arm_R': {'wrist': (-0.36, -0.26, -0.10), 'pole': (-0.3, -0.4, -0.3), 'blade': (-0.6, -0.75, 0.1),
                   'palm': (0.2, 0.1, 1.0), 'curl': 82, 'thumb': 35},
         'arm_L': {'wrist': (0.27, -0.24, 0.10), 'pole': (0.7, 0.1, -0.2), 'finger': (0, -1, 0.2),
                   'palm': (-1, 0, 0), 'curl': 25},
         'spine': (8, 3, -15), 'head': (10, 4, -8), 'hips': (0, 0.01, -0.03), 'knife': True}),
    (7, {'arm_R': {'wrist': (-0.06, -0.10, 0.44), 'pole': (-0.35, -0.35, 0.0), 'blade': (0.15, 0.25, 1.0),
                   'palm': (1, 0, 0), 'curl': 82, 'thumb': 35},
         'arm_L': {'wrist': (0.33, -0.30, 0.14), 'pole': (0.6, -0.1, -0.1), 'finger': (0.3, -1, 0.3),
                   'palm': (-1, 0, 0), 'curl': 22},
         'spine': (8, 0, 0), 'head': (8, 0, 0), 'hips': (0, -0.01, -0.03), 'knife': True}),
    (10, {'arm_R': {'wrist': (0.40, -0.01, 0.36), 'pole': (-0.1, -0.5, 0.1), 'blade': (0.7, 0.7, 0.2),
                    'palm': (0, -0.3, -1), 'curl': 82, 'thumb': 35},
          'arm_L': {'wrist': (0.20, -0.32, -0.10), 'pole': (0.3, 0.0, -0.4), 'finger': (0, -1, -0.2),
                    'palm': (-1, 0, 0), 'curl': 22},
          'spine': (8, 0, 30), 'head': (6, 3, 12), 'hips': (0, -0.005, -0.016), 'knife': True,
          'feet_offset': {'Left': (0, 0, 0), 'Right': (0, 0, 0)}}),
    (13, {'arm_R': {'wrist': (0.12, -0.07, 0.26), 'pole': (-0.25, -0.4, 0.05), 'blade': (0.45, 0.65, 0.5),
                    'palm': (0, -0.3, -1), 'curl': 82, 'thumb': 35},
          'arm_L': {'wrist': (0.20, -0.32, -0.08), 'pole': (0.3, 0.0, -0.4), 'finger': (0, -1, -0.2),
                    'palm': (-1, 0, 0), 'curl': 22},
          'spine': (6, 0, 25), 'head': (8, 2, 10), 'hips': (0, 0, -0.008), 'knife': True}),
    (16, {'arm_R': {'wrist': (-0.02, -0.22, 0.21), 'pole': (-0.4, -0.15, -0.3), 'blade': (0.6, 0.55, 0.4),
                    'palm': (0.2, 0, -1), 'curl': 80, 'thumb': 35},
          'arm_L': {'wrist': (0.06, -0.24, 0.18), 'pole': (0.4, -0.15, -0.3), 'finger': (-0.45, -0.85, 0.05),
                    'palm': (-0.3, 0, -0.95), 'curl': 22},
          'spine': (0, 0, 3), 'head': (2, 0, 2), 'hips': (0, 0, -0.004), 'knife': True}),
    (19, CLASP),
]

CLUTCH_R = {'wrist': (0.09, -0.19, 0.19), 'pole': (-0.35, -0.25, 0.0), 'finger': (0.6, -0.5, -0.5),
            'palm': (0, 0, -1), 'curl': 40, 'thumb': 20}
HIT = [
    (1, {'arm_R': CLUTCH_R, 'arm_L': {'wrist': (0.17, -0.2, 0.14), 'pole': (0.6, 0.0, -0.1),
          'finger': (-0.4, -0.8, 0.3), 'palm': (-0.6, 0, -0.6), 'curl': 30},
         'spine': (16, 0, 0), 'head': (16, 0, 0), 'hips': (0, 0.02, -0.012)}),
    (4, {'arm_R': variant(CLUTCH_R, wrist=(0.11, -0.2, 0.17)), 'arm_L': {'wrist': (0.30, -0.16, 0.10),
          'pole': (0.6, 0.25, 0.0), 'finger': (0, -1, 0.1), 'palm': (-1, 0, 0), 'curl': 35},
         'spine': (34, -4, 3), 'head': (20, 0, 0), 'hips': (0, 0.04, -0.035)}),
    (7, {'arm_R': variant(CLUTCH_R, wrist=(0.11, -0.21, 0.16)), 'arm_L': {'wrist': (0.31, -0.17, 0.09),
          'pole': (0.6, 0.3, 0.0), 'finger': (0, -1, 0.15), 'palm': (-1, 0, 0), 'curl': 40},
         'spine': (48, -5, 4), 'head': (24, 0, 0), 'hips': (0, 0.055, -0.06)}),
    (10, {'arm_R': variant(CLUTCH_R, wrist=(0.09, -0.21, 0.17)), 'arm_L': {'wrist': (0.28, -0.2, 0.10),
           'pole': (0.6, 0.2, 0.0), 'finger': (0, -1, 0.1), 'palm': (-1, 0, 0), 'curl': 35},
          'spine': (36, -3, 2), 'head': (20, 0, 0), 'hips': (0, 0.04, -0.04)}),
    (13, {'arm_R': {'wrist': (-0.19, -0.33, 0.12), 'pole': (-0.5, -0.1, -0.2), 'finger': (0.1, -1, 0.2),
                    'palm': (1, 0, 0), 'curl': 25},
          'arm_L': {'wrist': (0.19, -0.33, 0.12), 'pole': (0.5, -0.1, -0.2), 'finger': (-0.1, -1, 0.2),
                    'palm': (-1, 0, 0), 'curl': 25},
          'spine': (16, 0, 0), 'head': (10, 0, 0), 'hips': (0, 0.02, -0.02)}),
    (16, {'arm_R': {'wrist': (-0.15, -0.32, 0.15), 'pole': (-0.45, -0.1, -0.3), 'finger': (0.2, -1, 0.15),
                    'palm': (0.8, 0, -0.5), 'curl': 25},
          'arm_L': {'wrist': (0.15, -0.32, 0.15), 'pole': (0.45, -0.1, -0.3), 'finger': (-0.2, -1, 0.15),
                    'palm': (-0.8, 0, -0.5), 'curl': 25},
          'spine': (5, 0, 0), 'head': (6, 0, 0), 'hips': (0, 0.005, -0.006)}),
    (19, CLASP),
]

import os
CORPSE_HIPS = tuple(float(x) for x in os.environ.get('CORPSE_HIPS', '0,-0.42,-0.728').split(','))
ANKLE_PRONE = float(os.environ.get('ANKLE_PRONE', '60'))
# Death: fold -> buckle -> kneel -> hands to floor -> prone (625 ms), then a 1 s held corpse for the settle.
def kneel_legs(hips_y, hips_z, spread=0.11):
    out = {}
    for side, sx in (('Left', 1), ('Right', -1)):
        out[side] = {'ankle': (sx * spread, hips_y + 0.34, 0.07), 'pole': (sx * spread, hips_y - 1.0, -0.4),
                     'foot_pitch': -70}
    return out


DEATH = [
    (1, HIT[1][1]),
    (4, {'arm_R': variant(CLUTCH_R, wrist=(0.11, -0.21, 0.16)), 'arm_L': {'wrist': (0.32, -0.12, 0.12),
          'pole': (0.6, 0.3, 0.0), 'finger': (0, -1, 0.15), 'palm': (-1, 0, 0), 'curl': 40},
         'spine': (52, -4, 4), 'head': (25, 0, 0), 'hips': (0, 0.06, -0.08)}),
    (7, {'arm_R': variant(CLUTCH_R, wrist=(0.10, -0.22, 0.17)), 'arm_L': {'wrist': (0.30, -0.15, 0.15),
          'pole': (0.6, 0.3, 0.0), 'finger': (0, -1, 0.2), 'palm': (-1, 0, 0), 'curl': 40},
         'spine': (45, -3, 3), 'head': (22, 0, 0), 'hips': (0, 0.0, -0.30)}),
    (10, {'arm_R': {'wrist': (0.05, -0.26, 0.20), 'pole': (-0.4, -0.2, 0.0), 'finger': (0.3, -1, 0.2),
                    'palm': (0, 0, -1), 'curl': 35},
          'arm_L': {'wrist': (0.25, -0.30, 0.18), 'pole': (0.6, 0.1, 0.0), 'finger': (0, -1, 0.3),
                    'palm': (-1, 0, 0), 'curl': 30},
          'spine': (35, -2, 0), 'head': (25, 0, 0), 'hips': (0, -0.02, -0.43), 'hips_rot': (0, 10, 0),
          'legs': 'ik', 'leg_ik': kneel_legs(-0.04, 0.42)}),
    (13, {'arm_R': {'wrist_world': (-0.17, -0.47, 0.06), 'pole': (-0.3, 0.3, 0.2), 'finger': (0, -0.3, 1),
                    'palm': (0, 1, 0), 'curl': 15},
          'arm_L': {'wrist_world': (0.19, -0.45, 0.06), 'pole': (0.3, 0.3, 0.2), 'finger': (0, -0.3, 1),
                    'palm': (0, 1, 0), 'curl': 15},
          'spine': (30, 0, 0), 'head': (10, 0, 0), 'hips': (0, -0.06, -0.47), 'hips_rot': (0, 38, 0),
          'legs': 'ik', 'leg_ik': kneel_legs(-0.08, 0.38)}),
    (16, {'arm_R': {'wrist': (-0.24, 0.24, 0.10), 'pole': (-0.5, -0.1, -0.2), 'finger': (0.1, 0.7, 0.3),
                    'palm': (0, 0, 1), 'curl': 25},
          'arm_L': {'wrist': (0.20, -0.30, 0.09), 'pole': (0.5, 0.0, -0.2), 'finger': (0, -1, 0.1),
                    'palm': (0, 0, 1), 'curl': 25},
          'spine': (2, 0, 0), 'head': (0, 22, 62), 'hips': CORPSE_HIPS, 'hips_rot': (-55, 88, 0),
          'legs': 'fk', 'leg_fk': {'Left': {'hip': 0, 'knee': 3, 'ankle': ANKLE_PRONE, 'abduct': 4},
                                   'Right': {'hip': 0, 'knee': 2, 'ankle': ANKLE_PRONE, 'abduct': 2}}}),
]
DEATH_FULL = DEATH + [(40, DEATH[-1][1])]

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    which = args[0].split(',') if args else ['Standing', 'Fidget', 'Attack', 'Hit', 'DeathFull']
    table = {'Standing': (STANDING, True), 'Fidget': (FIDGET, False), 'Attack': (ATTACK, False),
             'Hit': (HIT, False), 'DeathFull': (DEATH_FULL, False)}
    for name in which:
        keys, loop = table[name]
        key_clip(name, keys, loop=loop)
        print('AUTHORED', name, keys[-1][0])
    bpy.ops.wm.save_mainfile()
