"""Attack v2 (2026-10-18 user review: "the whole attack anatomy is strange, he doesnt angle the body, he is stiff,
hand disappears, wrists bend"). Rebakes only Attack in work/centaur_master.blend -> work/centaur_master_attack_v2.blend
and exports the LOD0 GLB (CENTAUR_LOD0, default work/attack_v2_lod0.glb) with the export settings of export_model.py.

Upper body after the stored humanoid bow shot the MM6 Lizard Archer uses (2HandBowAttack1): the torso turns side-on,
the bow arm extends toward the target with a straight wrist, the draw hand anchors the nock at the jaw, release, and a
short follow-through back along the arrow. Horse body after the native m532 attack frames: the forequarters rear while
the bow is drawn angled upward, come down as the aim levels, release at 1.0 s (frame 48, the existing impact marker).

Fixes against v1: hands are oriented along their forearms (v1 fixed the bow and derived the hand, a 143 deg wrist
bend, and after the release pointed the draw hand forward while the arm swung back, folding it into the forearm).
The bow follows the bow hand rigidly (fitted grip unchanged). Clip length 1.5 s, first and last frames are the
Standing pose of v1, as before."""
from pathlib import Path
import bpy, sys, json, math, os
from mathutils import Vector, Matrix, Quaternion
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'mm6_rat_claude/scripts')); import posing as Q
sys.path.insert(0, str(Path(__file__).resolve().parent)); import carry
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/centaur_master.blend'))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
G = json.loads((P / 'work/equipment.json').read_text())
for k in (1, 2, 3):
    G['finger_local']['LThumb' + str(k)] = Quaternion().slerp(Quaternion(G['finger_local']['LThumb' + str(k)]), .55 if k == 1 else .7)
rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
handrest = Matrix(G['rest_hand_matrix']).to_3x3(); bowrest = Matrix(G['bow_rest_matrix']).to_3x3()
centre_local = Vector(G['centre_hand_local']); tau = 2 * math.pi
UP = Vector((0, 0, 1))
RELEASE = 2 / 3
T_QUIVER, T_NOCK = .11, .25                   # hand at the quiver top; string hooked, draw starts
RESIDUAL = [0.]
RESIDUALS = []
SPIN = [None]                                 # last bow spin (radians) for continuity
HOOK = [None]                                 # last reach fingertip in the chest frame (string hook point)
ROLL = {'LArm': 0, 'RArm': 0, 'LForeArm': 0, 'RForeArm': 0}
WRIST_MAX = 15.
PALM_IN, PALM_DOWN = (float(os.environ.get(k, d)) for k, d in (('CENTAUR_PALM_IN', '.6'), ('CENTAUR_PALM_DOWN', '.8')))


def smooth(x):
    x = max(0., min(1., x)); return x * x * (3 - 2 * x)


def ramp(t, a, b):
    return smooth((t - a) / (b - a))


def bell(t, a, peak, b):
    return ramp(t, a, peak) * (1 - ramp(t, peak, b))


def orient(name, R):
    b = rig.pose.bones[name]; b.matrix = Matrix.Translation(b.head) @ R.to_4x4(); bpy.context.view_layer.update()


def world_rot(name):
    return rig.pose.bones[name].matrix.to_3x3().normalized()


# Standing hold (carry.py): the Standing bow pose with the fist turned about the stave for a straight wrist.
CARRY_B = carry.carry_matrix(); CARRY_PREV = [None]


def carry_bow_hand():
    """Solved once on the first frame (the Standing pose, as is the last frame) and held in world space: the hold
    only weighs in at the clip ends, where the torso is back in the Standing pose."""
    if CARRY_PREV[0] is None:
        out, up, fwd = carry.body_axes(rig, rest)
        CARRY_PREV[0] = carry.solve(rig.pose.bones['LArm'].head, rig.pose.bones['LArm'].length,
                                    rig.pose.bones['LForeArm'].length, CARRY_B, handrest.inverted() @ bowrest,
                                    centre_local, out, up, fwd)[:3]
    H, W, E = CARRY_PREV[0]
    return W.copy(), E.copy(), H.copy()


def carry_right_hand(target=(-.45, -.62, 1.43)):
    Q.two_bone_ik(rig, 'RArm', 'RForeArm', Vector(target), Vector((-.85, -.15, 1.6)))
    desired = Vector((0, -1, -.65)).normalized()
    R = rest['RHand'].to_3x3(); return R.col[1].rotation_difference(desired).to_matrix() @ R


def along_forearm(side, palm_toward=None, bow_up=None):
    """Hand frame with its Y along the posed forearm (straight wrist). The roll about the forearm turns the palm
    (local -Z) toward `palm_toward`, or turns the held bow's axis toward `bow_up` (bow hand)."""
    f = (rig.pose.bones[side + 'ForeArm'].tail - rig.pose.bones[side + 'ForeArm'].head).normalized()
    R0 = rest[side + 'Hand'].to_3x3(); R = R0.col[1].rotation_difference(f).to_matrix() @ R0
    if bow_up is not None:
        cur = (R @ handrest.inverted() @ bowrest).col[1]; want = Vector(bow_up)
    else:
        cur = -R.col[2]; want = Vector(palm_toward)
    cur = (cur - f * cur.dot(f)).normalized(); want = (want - f * want.dot(f)).normalized()
    ang = cur.angle(want) * (1 if cur.cross(want).dot(f) > 0 else -1)
    return Matrix.Rotation(ang, 3, f) @ R


def slerp_rot(A, B, w):
    return A.to_quaternion().slerp(B.to_quaternion(), smooth(w)).to_matrix()


def place_left(wrist, pole, H):
    Q.two_bone_ik(rig, 'LArm', 'LForeArm', wrist, pole); orient('LHand', H)
    for name, q in G['finger_local'].items():
        rig.pose.bones[name].rotation_quaternion = q
    bpy.context.view_layer.update()


def tip_ik(side, target, pole):
    """Two-bone IK where the lower segment is the forearm plus the straight hand to the index tip: the upper arm aims
    at the solved elbow and the forearm straight at the target, so the hand laid along it reaches the target."""
    up, lo = rig.pose.bones[side + 'Arm'], rig.pose.bones[side + 'ForeArm']
    s0 = up.head.copy(); la = up.length
    lb = lo.length + (rig.pose.bones[side + 'Index3'].tail - rig.pose.bones[side + 'Hand'].head).length
    d = Vector(target) - s0; dist = min(d.length, (la + lb) * .999); d.normalize()
    c = max(-1, min(1, (la * la + dist * dist - lb * lb) / (2 * la * dist)))
    pd = Vector(pole) - s0; pd = (pd - d * pd.dot(d)).normalized()
    elbow = s0 + (d * c + pd * math.sqrt(1 - c * c)) * la
    Q.aim_bone(rig, side + 'Arm', elbow); Q.aim_bone(rig, side + 'ForeArm', Vector(target))


def spin_bow(target, k):
    """Turn the bow about its own long axis (local Y) in the fist: its string side (local -Z) goes from the Standing
    hold's (k = 0, the bow exactly as in Standing) to the line from the grip to `target` (k = 1), so the plane holds the
    shot with the string on the archer's side (2026-10-19 user review: "rotated 90 deg")."""
    b = rig.pose.bones['Bow']; R = b.matrix.to_3x3().normalized(); y = R.col[1]
    flat = lambda v: (v - y * v.dot(y)).normalized()
    want = flat(flat(-CARRY_B.to_3x3().col[2]) * (1 - k) + flat(target - b.head) * k)
    cur = flat(-R.col[2])
    ang = cur.angle(want) * (1 if cur.cross(want).dot(y) > 0 else -1)
    if SPIN[0] is not None:                                       # continuous branch over the baked frames
        ang += tau * round((SPIN[0] - ang) / tau)
    SPIN[0] = ang
    orient('Bow', Matrix.Rotation(ang, 3, y) @ R)


def curl_right(R, degrees):
    for n in ('Index', 'Middle', 'Ring', 'Pinky'):
        for k in (1, 2, 3):
            Q.rotate_world(rig, 'R' + n + str(k), R.col[0], degrees)


def leg(side, front, dy=0, lift=0):
    pre = 'Front' if front else 'Hind'; sg = 1 if side == 'L' else -1
    hoof = pre + 'Hoof_' + side; ankle = rest[hoof].translation + Vector((0, dy, lift))
    if front:
        Q.two_bone_ik(rig, pre + 'Upper_' + side, pre + 'Lower_' + side, ankle, (sg * .32, -.15, .62))
    else:
        hock = ankle + rest['HindCannon_' + side].translation - rest[hoof].translation   # rest cannon, exact
        Q.two_bone_ik(rig, 'HindUpper_' + side, 'HindLower_' + side, hock, (sg * .36, -.1, .8))
        Q.aim_bone(rig, 'HindCannon_' + side, ankle)
    orient(hoof, rest[hoof].to_3x3())


def aim_dir(elev_deg):
    e = math.radians(elev_deg); return Vector((0, -math.cos(e), math.sin(e)))


# Phase weights over t in [0, 1] (1.5 s, release at 2/3 = 1.0 s).
def phases(t):
    return dict(
        twist=ramp(t, .06, .36) * (1 - ramp(t, .72, .97)),  # torso side-on
        raise_=ramp(t, .20, .43) * (1 - ramp(t, .70, .95)),  # bow arm up to the aim line (arrow nocked low first)
        draw=ramp(t, T_NOCK, .45) if t < RELEASE else 0.,     # nock from the bow to the jaw, while raising
        rear=bell(t, .16, .42, .64),                        # forequarters up (native 375-500 ms)
        follow=ramp(t, RELEASE, RELEASE + .06) * (1 - ramp(t, .74, .97)),
        recover=ramp(t, .70, .97))


def elevation(t):
    if t < .42:
        return 34 * ramp(t, .20, .42)                    # native m532 v2 375-500 ms: drawn well upward
    return 34 - 30 * ramp(t, .42, .60)                     # level to 4 deg before the release


def pose(t):
    Q.reset(rig); rig.pose.bones['Arrow'].scale = (.001,) * 3
    w = phases(t); cycle = math.sin(tau * t)
    Q.rotate_world(rig, 'Chest', 'X', .8 * cycle); Q.rotate_world(rig, 'Head', 'Z', 2 * math.sin(tau * t + .4))
    for k in range(1, 6):
        Q.rotate_world(rig, 'Tail' + str(k), 'Z', (2 + k * .7) * math.sin(tau * t - k * .38) + 10 * w['rear'] * (k / 5))
    # Horse body: rear on the hind legs, front legs folded, hind hooves replanted.
    r = w['rear']
    if r > 1e-4:
        Q.rotate_world(rig, 'HorsePelvis', 'X', -17 * r)
        for side in ('L', 'R'):
            chain = ['HindUpper_' + side, 'HindLower_' + side, 'HindCannon_' + side, 'HindHoof_' + side]
            fk = {n: rig.pose.bones[n].matrix.to_quaternion() for n in chain}
            leg(side, False)
            k = ramp(r, 0, .10)                             # fade the replant in and out with the rear: no pop
            if k < 1:
                ik = {n: rig.pose.bones[n].matrix.to_quaternion() for n in chain}
                for n in chain:
                    orient(n, fk[n].slerp(ik[n], k).to_matrix())
            Q.rotate_world(rig, 'FrontUpper_' + side, 'X', -28 * r)
            Q.rotate_world(rig, 'FrontLower_' + side, 'X', 72 * r)
        Q.rotate_world(rig, 'Spine', 'X', 12 * r)            # rider leans into the rear, stays upright
    # Torso side-on: left shoulder to the target, head back to the aim line.
    tw = w['twist']
    for name, deg in (('Spine', -18), ('Spine1', -24), ('Chest', -24)):
        Q.rotate_world(rig, name, 'Z', deg * tw)
    Q.rotate_world(rig, 'Spine1', 'X', 5 * w['raise_'])         # slight lean toward the shot
    fwd = world_rot('Chest').col[2]                               # chest forward
    Q.rotate_world(rig, 'RShoulder', fwd, -14 * w['draw'])        # draw shoulder up behind the string
    Q.rotate_world(rig, 'LShoulder', fwd, -5 * w['raise_'])       # bow shoulder settled down
    Q.rotate_world(rig, 'Neck', 'Z', 28 * tw); Q.rotate_world(rig, 'Head', 'Z', 30 * tw)
    Q.rotate_world(rig, 'Head', 'Y', -6 * w['draw'])            # cheek to the string
    a = aim_dir(elevation(t))
    # Bow arm: carry hold -> straight arm on the aim line, hand along the forearm, bow canted 10 deg.
    cw, cpole, cH = carry_bow_hand()
    ls = rig.pose.bones['LArm'].head.copy()
    la = rig.pose.bones['LArm'].length; lb = rig.pose.bones['LForeArm'].length
    side_in = Vector((a.y, -a.x, 0)).normalized() if a.xy.length > 1e-6 else Vector((1, 0, 0))   # toward the archer's right
    aim_wrist = ls + a * (la + lb) * .965 + side_in * .015
    aim_pole = ls + a * .35 - side_in * .30 - UP * .35          # elbow down and out, string clears the forearm
    m = w['raise_']
    nock_w = Vector((.16, -.88, 1.80))                           # bow in front of the belly to nock (source frames 2-4)
    nk = ramp(t, .04, .20) * (1 - ramp(t, .86, 1.0))
    cw = cw.lerp(nock_w, nk); cpole = cpole.lerp(Vector((.95, -.3, 1.65)), nk)   # elbow out to the side once the bow leaves
    wrist = cw.lerp(aim_wrist, smooth(m)); pole = cpole.lerp(aim_pole, smooth(m))
    Q.two_bone_ik(rig, 'LArm', 'LForeArm', wrist, pole)
    bow_up = (UP - a * UP.dot(a)).normalized(); bow_up = (Matrix.Rotation(math.radians(10), 3, a) @ bow_up)
    Hf = along_forearm('L', bow_up=bow_up)
    y = bow_up; z = (a - y * a.dot(y)).normalized(); x = y.cross(z)
    Hb = Matrix((x, y, z)).transposed() @ bowrest.inverted() @ handrest      # bow square to the arrow
    bend = math.degrees(Hf.col[1].angle(Hb.col[1]))
    Ha = slerp_rot(Hf, Hb, 1.0) if bend <= WRIST_MAX else Hf.to_quaternion().slerp(Hb.to_quaternion(), WRIST_MAX / bend).to_matrix()
    hw = max(m, ramp(t, .0, .16) * (1 - ramp(t, .86, 1.0)))     # straighten the Standing wrist early, bend it back late
    H = slerp_rot(cH, Ha, hw)
    place_left(wrist, pole, H)
    # Right hand: carry -> quiver -> string -> jaw anchor -> follow-through -> carry.
    pb = rig.pose.bones
    head = pb['Head']; HR = world_rot('Head')
    anchor = head.head + HR @ Vector((-.065, .0, .10))        # right jaw corner (Head X left, Y up, Z forward)
    spin_bow(pb['Neck'].head.lerp(anchor, smooth(m)), hw)       # string toward the chest, the jaw once on the aim line
    nock_rest = pb['StringNock'].head.copy()
    quiver_top = pb['Quiver'].tail + Vector((0, 0, .10))
    rs = pb['RArm'].head.copy()
    draw_pole = rs + side_in * .18 + UP * .12 - a * .45        # draw elbow back along the arrow, a little out and up
    carry_t = Vector((-.45, -.62, 1.43)); carry_tip = Vector((-.384, -.816, 1.339))   # v1 Standing wrist, fingertip
    if t < RELEASE:
        if t < T_QUIVER:
            target = carry_tip.lerp(quiver_top, ramp(t, 0, T_QUIVER)); mode = 'reach'
        elif t < T_NOCK:
            target = quiver_top.lerp(nock_rest, ramp(t, T_QUIVER, T_NOCK - .03)); mode = 'reach'   # on the string 2 frames early
        else:
            # the hand keeps the string where it hooked it (chest frame) and pulls it to the jaw; the bow arm pushes
            # away at the same time, so the string never runs ahead of the hand
            hook_pt = world_rot('Chest') @ HOOK[0] + pb['Chest'].head if HOOK[0] is not None else nock_rest
            target = hook_pt.lerp(anchor, w['draw']); mode = 'draw'
    else:
        target = None; mode = 'follow'
    if mode == 'follow':
        # nock released at the anchor; the hand continues back along the arrow and slightly out, then home
        back = anchor - a * .10 + side_in * .10 + UP * .03          # back past the cheek and out, clear of the hair
        fwd = ramp(t, RELEASE, RELEASE + .06)
        target = anchor.lerp(back, fwd).lerp(carry_tip, w['recover'])
    # fingers first (local to the hand): carry curl, hook the string while drawing, open on the release
    hook = 1 if mode in ('draw',) else (ramp(t, .10, .21) if mode == 'reach' else 0)
    open_ = ramp(t, RELEASE, RELEASE + .04) * (1 - w['recover'])
    curl_right(world_rot('RHand'), -10 - 14 * hook + 16 * open_)
    # finger hook point: RIndex3 tail on the target while the hand is aligned with its forearm
    pole_r = Vector((-.85, -.15, 1.6)).lerp(draw_pole, smooth(w['twist']))
    aim_t = target.copy()
    for _ in range(6):
        tip_ik('R', aim_t, pole_r)
        palm = -side_in * PALM_IN - UP * PALM_DOWN                 # palm to the body/neck, back of the hand outward
        orient('RHand', along_forearm('R', palm_toward=palm))
        aim_t = aim_t + (target - pb['RIndex3'].tail)
    if mode == 'reach':
        HOOK[0] = world_rot('Chest').inverted() @ (pb['RIndex3'].tail - pb['Chest'].head)
    RESIDUAL[0] = max(RESIDUAL[0], (target - pb['RIndex3'].tail).length)
    RESIDUALS.append((round(t, 3), mode, round((target - pb['RIndex3'].tail).length, 4)))
    # blend the whole right arm back into the carry pose at both clip ends
    home = max(1 - ramp(t, 0, .10), w['recover'] * ramp(t, .90, 1.0))
    if home > 1e-4:
        keep = {n: pb[n].matrix.copy() for n in ('RArm', 'RForeArm', 'RHand')}
        Rc = carry_right_hand(carry_t)
        carried = {n: pb[n].matrix.copy() for n in ('RArm', 'RForeArm')}
        for n in ('RArm', 'RForeArm'):
            q = keep[n].to_quaternion().slerp(carried[n].to_quaternion(), home)
            pb[n].matrix = Matrix.Translation(pb[n].head) @ q.to_matrix().to_4x4(); bpy.context.view_layer.update()
        orient('RHand', slerp_rot(keep['RHand'].to_3x3(), Rc, home))
    if t >= 1:                                                    # last frame: the full search, as Standing's first
        ROLL.pop('_seeded_LArm', None); ROLL.pop('_seeded_LForeArm', None); ROLL['LArm'] = ROLL['LForeArm'] = 0
    carry.settle_roll(rig, Q, rest, 'L', 1., ROLL); carry.settle_roll(rig, Q, rest, 'R', 1 - home if home > 1e-4 else 1., ROLL)
    # string and arrow
    if mode == 'draw':
        nock = pb['RIndex3'].tail.copy()                           # on the string since T_NOCK - .03: no jump
        b = pb['StringNock']; M = b.matrix.copy(); M.translation = nock; b.matrix = M; bpy.context.view_layer.update()
    if T_QUIVER <= t < RELEASE:
        bowR = world_rot('Bow'); rest_pt = pb['Bow'].head + bowR.col[1] * .055
        nock = pb['StringNock'].head if mode == 'draw' else pb['RIndex3'].tail
        direction = (rest_pt - nock).normalized()
        ar = pb['Arrow']; R = Vector((0, -1, 0)).rotation_difference(direction).to_matrix() @ rest['Arrow'].to_3x3()
        ar.matrix = Matrix.Translation(nock) @ R.to_4x4(); ar.scale = (1, 1, 1)
    bpy.context.view_layer.update()


old = bpy.data.actions['Attack']; old.name = 'Attack_v1'; old.use_fake_user = False
a = bpy.data.actions.new('Attack'); a.use_fake_user = True; rig.animation_data.action = a
n = 72; previous = {}
for f in range(n + 1):
    sc.frame_set(f); pose(f / n)
    for b in rig.pose.bones:
        if b.name in previous and b.rotation_quaternion.dot(previous[b.name]) < 0:
            b.rotation_quaternion.negate()
        previous[b.name] = b.rotation_quaternion.copy()
        for path in ('location', 'rotation_quaternion', 'scale'):
            b.keyframe_insert(path, frame=f, group=b.name)
for layer in a.layers:
    for strip in layer.strips:
        bag = strip.channelbag(a.slots[0])
        for fc in bag.fcurves:
            for key in fc.keyframe_points:
                key.interpolation = 'CONSTANT' if 'Arrow' in fc.data_path and fc.data_path.endswith('.scale') else 'LINEAR'
a['role'] = 'attack'; a['duration_seconds'] = n / 48; a.pose_markers.new('impact').frame = 48
bpy.data.actions.remove(old)
rig.animation_data.action = bpy.data.actions['Standing']; rig.animation_data.action_slot = rig.animation_data.action.slots[0]
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/centaur_master_attack_v2.blend'))
b = bpy.data.objects['Body']
for o in sc.objects:
    o.select_set(o == b or o == rig or o.name.startswith('Socket_'))
bpy.context.view_layer.objects.active = rig
out = os.environ.get('CENTAUR_LOD0', str(P / 'work/attack_v2_lod0.glb'))
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True, export_animations=True,
                          export_animation_mode='ACTIONS', export_force_sampling=True, export_frame_step=1, export_skins=True,
                          export_all_influences=False, export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True, export_extras=True)
print('ATTACK_V2', out, 'max hook residual m', round(RESIDUAL[0], 4))
print('RESIDUALS', [r for r in RESIDUALS if r[2] > .01])
