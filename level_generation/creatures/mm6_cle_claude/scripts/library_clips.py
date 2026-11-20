"""Attack and Cast from the animation library (user review 2026-10-14: "best fitting library animations for the cast
and attack; he has the staff and one hand free"), replacing the authored ones in work/rig_v3.blend.

  Attack = Mixamo "Spell Cast": the LEFT (staff) arm thrusts at the target and returns; the staff swings down from
           upright to point at the target (native cleatt b-c: the ring in front of the chest, glow, release).
  Cast   = Mixamo "Spell Cast" mirrored: the free right hand thrusts palm-first at the target; the staff arm keeps
           Standing's carry.
  Death  = Mixamo "Dying (7)" (user review 2026-10-14 (2)), its fall up to the settle played in DEATH_S; once the
           hips are down the legs settle into the authored corpse's (author_death.py 'Dead'); 'Dead' holds the last
           pose. Full pelvis travel and turn, no foot planting, eased in from Standing only; the staff is
           tipped toward level about the grip wherever it would reach under the floor.

Per clip (anim_library sources, retargeted with the WORLD rule of ../../mm6_cle_reduce_claude/anim/retarget_cle.py:
each bone takes the source's world rotation change from its rest, applied to our rig matched to the humanoid set's
upright rest; Mixamo files are 30 fps and resampled to 24):
1. Yaw: the whole clip is turned so the hand that delivers the blow points at -Y (the target) at its release.
2. Pelvis: Standing's frame-0 position plus PELVIS_KEEP of the source pelvis travel (the Mixamo stances step and dip)
   and PELVIS_TURN of its rotation (the lowest spine bone takes the rest).
3. Ease: every bone's local rotation and the pelvis blend from Standing frame 0 over EASE_IN s and back to it over
   EASE_OUT s (the engine crossfades only 0.06-0.12 s).
4. Feet: both feet stay on Standing's frame-0 footprints (analytic two-bone leg IK from Standing's leg rotations, the
   knee in Standing's bend plane; foot world rotation = Standing's).
5. Staff: Attack turns the staff hand (bell weight around the release) so the staff points at the target, slightly
   up; Cast holds the staff arm at Standing's local pose.
Writes the actions into the blend in place and work/library_clips.json (release times, sources, yaw).
Args: -- <blend in work/> [<blend out in work/>]"""
import bpy, sys, os, json, math
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

a = sys.argv[sys.argv.index('--') + 1:]
src_blend = os.path.join(common.WORK, a[0]); out_blend = os.path.join(common.WORK, a[1] if len(a) > 1 else a[0])
bpy.ops.wm.open_mainfile(filepath=src_blend)
sc = bpy.context.scene; FPS = 24          # the FBX import sets the scene to the file's 30 fps; restored on save
rig = bpy.data.objects['Cleric_Rig']
ROOT = os.path.abspath(os.path.join(common.PROJECT, '..', '..', '..'))
MX = os.path.join(ROOT, 'anim_library', 'mixamo')
REF_GLB = os.path.join(ROOT, 'anim_library', 'humanoid_set', '2Hand Staff.glb')
DEATH_S = 1.75               # the source fall (to its settle) played in this time
DOWN_Z = 0.35                # Death: hips below this height (m) = on the floor; the legs then settle into the authored
LEGS_SETTLE = 0.35           # corpse's straight legs over this time (s): the source kicks a leg up as it lands and
                             # the cloak caught on the raised shin and piled up on his shoulders
CLIPS = {
    'Attack': dict(src=os.path.join(MX, 'Spell Cast.fbx'), fps=30, hand='LeftHand', staff=True),
    # Spell Cast mirrored: the free right hand thrusts palm-first at the target (native intent "right palm forward").
    # Tried and dropped (review/lib_*.png in mm6_cle_reduce_claude): Standing 1H Cast Spell 01 (a side-on throwing
    # stance, profile to the party), Sword And Shield Casting (bows 90 degrees into a ground slam), Magic Heal (turns
    # its back mid-clip).
    'Cast': dict(src=os.path.join(MX, 'Spell Cast.fbx'), fps=30, hand='RightHand', staff=False, mirror=True),
    # user review 2026-10-14 (2): "death anim - pick some better from library". Dying (7): staggers back, drops to a
    # knee and falls face down, arms forward (native cledyi: sways back, knees, topples face down; corpse cledyif0).
    # Previewed against Dying (4), (5), (6), Standing Death Forward 01/02, Standing React Death Forward, Falling
    # Forward Death, Sword And Shield Death (1), Death From Front Headshot and the set's Staff Death1
    # (mm6_cle_reduce_claude/review/deaths_*.png).
    'Death': dict(src=os.path.join(MX, 'Dying (7).fbx'), fps=30, death=True, seconds=DEATH_S),
}
PELVIS_KEEP = 0.35
PELVIS_TURN = 0.35           # share of the source pelvis rotation (Spell Cast turns the hips 50 degrees over planted
                             # feet; the spine takes the rest, so the chest keeps the source's facing)
EASE_IN, EASE_OUT = 0.22, 0.30
STAFF_UP_DEG = 28.0          # staff tip above level at the release: the shaft runs back past the hip (native cleatt b)
OURS = ['Hips', 'Spine02', 'Spine01', 'Spine', 'neck', 'Head',
        'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand', 'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand',
        'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase']
MIXAMO = {o: 'mixamorig:' + s for o, s in zip(OURS, [
    'Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head',
    'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand', 'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand',
    'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase'])}
SET = dict(zip(OURS, [
    'B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head',
    'B_L_Clavicle', 'B_L_UpperArm', 'B_L_Forearm', 'B_L_Hand', 'B_R_Clavicle', 'B_R_UpperArm', 'B_R_Forearm', 'B_R_Hand',
    'B_L_Thigh', 'B_L_Calf', 'B_L_Foot', 'B_L_Toe0', 'B_R_Thigh', 'B_R_Calf', 'B_R_Foot', 'B_R_Toe0']))
CHILD = {'LeftShoulder': 'LeftArm', 'LeftArm': 'LeftForeArm', 'LeftForeArm': 'LeftHand',
         'RightShoulder': 'RightArm', 'RightArm': 'RightForeArm', 'RightForeArm': 'RightHand',
         'LeftUpLeg': 'LeftLeg', 'LeftLeg': 'LeftFoot', 'LeftFoot': 'LeftToeBase',
         'RightUpLeg': 'RightLeg', 'RightLeg': 'RightFoot', 'RightFoot': 'RightToeBase'}
LEGS = ('LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase')
STAFF_ARM = ('LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand')


def upd():
    bpy.context.view_layer.update()


def rest_pose(arm):
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    upd()


def wm(o):
    return rig.matrix_world @ rig.pose.bones[o].matrix


def rot(m):
    return m.to_quaternion().to_matrix()


def set_world_rot(o, R, head=None):
    cur = wm(o)
    m = Matrix.Translation(head if head is not None else cur.to_translation()) @ R.to_4x4()
    rig.pose.bones[o].matrix = rig.matrix_world.inverted() @ m
    upd()


MXR = Matrix.Diagonal((-1, 1, 1, 1))


def other(n):
    return n.replace('Left', '\0').replace('Right', 'Left').replace('\0', 'Right')


def src_world(src, names, turn, mirror=False):
    """world matrices of our-named bones as the source poses them (mirror swaps sides and reflects x)"""
    if not mirror:
        return {o: turn @ (src.matrix_world @ src.pose.bones[names[o]].matrix) for o in OURS}
    return {o: turn @ (MXR @ (src.matrix_world @ src.pose.bones[names[other(o)]].matrix) @ MXR) for o in OURS}


def import_armature(path):
    objs, acts = set(bpy.data.objects), set(bpy.data.actions)
    if path.lower().endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False)
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    new = set(bpy.data.objects) - objs
    return next(o for o in new if o.type == 'ARMATURE'), new, list(set(bpy.data.actions) - acts)


def drop(objs, acts):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    for x in acts:
        bpy.data.actions.remove(x)


def standing0():
    """local quaternions of every bone and the pelvis location at Standing frame 0, plus foot world matrices"""
    rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0); upd()
    loc = {pb.name: pb.matrix_basis.to_quaternion() for pb in rig.pose.bones}
    out = dict(q=loc, hips_loc=rig.pose.bones['Hips'].matrix_basis.to_translation(),
               feet={f: wm(f).copy() for f in ('LeftFoot', 'RightFoot', 'LeftToeBase', 'RightToeBase')},
               hips_world=wm('Hips').to_translation(), hips_rot=wm('Hips').to_quaternion(),
               leg_rot={s + b: rot(wm(s + b)) for s in ('Left', 'Right') for b in ('UpLeg', 'Leg')}, pole={}, len={}, reach={})
    for s in ('Left', 'Right'):
        H, K, A = (wm(s + b).to_translation() for b in ('UpLeg', 'Leg', 'Foot'))
        d = (A - H).normalized(); out['pole'][s] = ((K - H) - d * (K - H).dot(d)).normalized()
        out['len'][s] = ((K - H).length, (A - K).length); out['reach'][s] = (A - H).length
    rig.animation_data.action = None
    return out


# the humanoid set's upright rest: the reference both kinds of source are matched through
ref, robjs, racts = import_armature(REF_GLB)
rest_pose(ref)
_w = src_world(ref, SET, Matrix.Identity(4)); _lr = _w['LeftUpLeg'].to_translation() - _w['RightUpLeg'].to_translation()
WREF = src_world(ref, SET, Matrix.Rotation(-math.atan2(_lr.y, _lr.x), 4, 'Z'))
drop(robjs, racts)
ST = standing0()
# the authored corpse (author_death.py 'Dead', native cledyif0: face down, legs straight behind), read before
# the library Death replaces it
CORPSE_LEGS = None
if 'Dead' in bpy.data.actions:
    rig.animation_data.action = bpy.data.actions['Dead']; sc.frame_set(0); upd()
    CORPSE_LEGS = {o: wm(o).to_quaternion() for o in LEGS}     # world: legs straight behind on the floor
    rig.animation_data.action = None


def matched_offsets(Ws0):
    """our rest swung limb by limb onto the set's rest directions; C = R_src_rest^-1 R_ours_matched"""
    rest_pose(rig)
    for o in OURS:
        if o in CHILD:
            cur = wm(o); dt = wm(CHILD[o]).to_translation() - cur.to_translation()
            ds = WREF[CHILD[o]].to_translation() - WREF[o].to_translation()
            set_world_rot(o, dt.normalized().rotation_difference(ds.normalized()).to_matrix() @ rot(cur))
    return {o: rot(Ws0[o]).inverted() @ rot(wm(o)) for o in OURS}


def leg_ik(leg, ankle_target, foot_world):
    """two-bone IK from Standing's leg: thigh and shin start at their Standing frame-0 world rotations and are swung
    (minimal swing) so the ankle lands on the target, the knee bending in Standing's plane (its offset from the
    hip-ankle line). Starting from the source pose kept the source's thigh roll (up to 36 degrees off the shin, a
    twisted knee and ankle) and a pole from the pelvis bone's axis bent the knees inward (user review 2026-10-14)."""
    up, kn = leg + 'UpLeg', leg + 'Leg'
    set_world_rot(up, ST['leg_rot'][up]); set_world_rot(kn, ST['leg_rot'][kn])
    H = wm(up).to_translation(); L1, L2 = ST['len'][leg]
    d = ankle_target - H; dl = min(d.length, (L1 + L2) * 0.999); dn = d.normalized()
    pole = ST['pole'][leg]; pole = (pole - dn * pole.dot(dn)).normalized()
    a = (L1 * L1 + dl * dl - L2 * L2) / (2 * L1 * dl); a = max(-1.0, min(1.0, a))
    K = H + dn * (L1 * a) + pole * (L1 * math.sqrt(1 - a * a))
    for bone, child, goal in ((up, kn, K), (kn, leg + 'Foot', ankle_target)):
        cur = wm(bone); p0 = cur.to_translation(); c = wm(child).to_translation()
        set_world_rot(bone, (c - p0).normalized().rotation_difference((goal - p0).normalized()).to_matrix() @ rot(cur))
    set_world_rot(leg + 'Foot', rot(foot_world))


WRIST_MAX = 55.0             # wrist swing cap (pose_audit gate 60)
STAFF_FLOOR = 0.006          # lowest staff point above the floor (m)


def limit_swing(o, max_deg):
    """cap the swing part of a bone's rest-relative rotation about its own Y (the pose_audit wrist measure)"""
    pb = rig.pose.bones[o]; q = pb.matrix_basis.to_quaternion()
    p = Vector((q.x, q.y, q.z)).project(Vector((0, 1, 0)))
    tw = Quaternion((q.w, p.x, p.y, p.z)); tw.normalize(); sw = q @ tw.inverted()
    if math.degrees(sw.angle) > max_deg:
        sw = Quaternion(sw.axis, math.radians(max_deg))
        pb.rotation_quaternion = sw @ tw; upd()


def two_bone(upper, lower, end, target):
    """upper/lower swung so the end joint lands on target; the elbow keeps its current bend plane; end keeps its world
    rotation"""
    keep = rot(wm(end))
    S0 = wm(upper).to_translation(); E0 = wm(lower).to_translation(); W0 = wm(end).to_translation()
    L1, L2 = (E0 - S0).length, (W0 - E0).length
    d = target - S0; dl = min(d.length, (L1 + L2) * 0.999); dn = d.normalized()
    pole = (E0 - S0) - dn * (E0 - S0).dot(dn)
    pole = pole.normalized() if pole.length > 1e-6 else Vector((0, 1, 0))
    a = max(-1.0, min(1.0, (L1 * L1 + dl * dl - L2 * L2) / (2 * L1 * dl)))
    K = S0 + dn * (L1 * a) + pole * (L1 * math.sqrt(1 - a * a))
    cur = wm(upper); set_world_rot(upper, (E0 - S0).normalized().rotation_difference((K - S0).normalized()).to_matrix()
                                   @ rot(cur))
    cur = wm(lower); E1 = cur.to_translation(); W1 = wm(end).to_translation()
    set_world_rot(lower, (W1 - E1).normalized().rotation_difference((target - E1).normalized()).to_matrix() @ rot(cur))
    set_world_rot(end, keep)


def staff_low():
    st = bpy.data.objects['Staff']; ev = st.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    z = min((st.matrix_world @ v.co).z for v in me.vertices); ev.to_mesh_clear(); return z


def lift_staff():
    """raise the staff hand (arm IK) until the staff clears the floor"""
    for _ in range(4):
        z = staff_low()
        if z >= STAFF_FLOOR - 1e-4:
            return
        two_bone('LeftArm', 'LeftForeArm', 'LeftHand', wm('LeftHand').to_translation() + Vector((0, 0, STAFF_FLOOR - z)))


# Death floor: joint heads kept this far above the floor (their flesh radius); trunk and legs by lifting the pelvis,
# the arms by IK (the retargeted kneel sank a knee 18 cm and the corpse's hand 13 cm into the floor, and
# cloak_sim's body floor pass then floated the whole corpse 12 cm)
FLOOR_TRUNK = {'Hips': 0.11, 'Spine02': 0.12, 'Spine': 0.12, 'Head': 0.10, 'LeftUpLeg': 0.09, 'RightUpLeg': 0.09,
               'LeftLeg': 0.065, 'RightLeg': 0.065, 'LeftFoot': 0.06, 'RightFoot': 0.06, 'LeftToeBase': 0.03,
               'RightToeBase': 0.03, 'LeftArm': 0.06, 'RightArm': 0.06}
FLOOR_ARM = {'ForeArm': 0.045, 'Hand': 0.035}


def death_floor():
    for _ in range(3):
        pts = [(wm(o).to_translation(), r) for o, r in FLOOR_TRUNK.items()]
        for leg in ('LeftUpLeg', 'RightUpLeg'):          # mid-thigh (the kneel lands on it)
            a, b = wm(leg).to_translation(), wm(leg.replace('UpLeg', 'Leg')).to_translation()
            pts.append(((a + b) / 2, 0.08))
        lift = max(r - p.z for p, r in pts)
        if lift <= 1e-4:
            break
        pb = rig.pose.bones['Hips']; m = wm('Hips'); m.translation.z += lift
        pb.matrix = rig.matrix_world.inverted() @ m; upd()
    for side in ('Left', 'Right'):
        for _ in range(3):
            e, w = wm(side + 'ForeArm').to_translation(), wm(side + 'Hand').to_translation()
            if e.z < FLOOR_ARM['ForeArm'] - 1e-4:        # elbow: swing the upper arm up about the shoulder
                sh = wm(side + 'Arm'); s0 = sh.to_translation(); d = e - s0
                up = Vector((d.x, d.y, FLOOR_ARM['ForeArm'] - s0.z))
                set_world_rot(side + 'Arm', d.normalized().rotation_difference(up.normalized()).to_matrix() @ rot(sh))
                continue
            if w.z < FLOOR_ARM['Hand'] - 1e-4:
                two_bone(side + 'Arm', side + 'ForeArm', side + 'Hand', Vector((w.x, w.y, FLOOR_ARM['Hand'])))
                continue
            break


def staff_level():
    """Death: tip the staff about the grip toward the horizontal (hand rotation) until it clears the floor; the hand
    lies on the floor in the corpse, so lifting the arm would hold the staff up in the air"""
    z = staff_low()
    if z >= STAFF_FLOOR - 1e-4:
        return
    ax = (rot(rig.matrix_world @ rig.pose.bones['Staff'].matrix) @ Vector((0, 1, 0))).normalized()
    flat = Vector((ax.x, ax.y, 0.0)).normalized()
    if ax.z > 0:                                     # the lower end is the foot: lift the foot end to level
        flat = -flat if flat.dot(ax) < 0 else flat
    full = ax.rotation_difference(flat)
    keep = rot(wm('LeftHand'))
    lo, hi = 0.0, 1.0
    for _ in range(12):
        mid = (lo + hi) / 2
        set_world_rot('LeftHand', Quaternion().slerp(full, mid).to_matrix() @ keep)
        if staff_low() >= STAFF_FLOOR:
            hi = mid
        else:
            lo = mid
    set_world_rot('LeftHand', Quaternion().slerp(full, hi).to_matrix() @ keep)


def reach_hips():
    """lower the pelvis where a planted ankle is farther from the hip than in Standing (the source rises onto its toes;
    with the feet planted the straightened legs lifted the heels 1.5 cm off the floor)"""
    for _ in range(4):
        drop = 0.0
        for leg in ('Left', 'Right'):
            H = wm(leg + 'UpLeg').to_translation(); A = ST['feet'][leg + 'Foot'].to_translation(); d = A - H
            L = ST['reach'][leg]
            if d.length > L:
                # lowering the hip by x shortens d to sqrt(dxy^2 + (dz + x)^2) with dz < 0
                dxy2 = d.x * d.x + d.y * d.y
                drop = max(drop, -d.z - math.sqrt(max(L * L - dxy2, 0.0)))
        if drop <= 1e-5:
            return
        pb = rig.pose.bones['Hips']; m = wm('Hips'); m.translation.z -= drop
        pb.matrix = rig.matrix_world.inverted() @ m; upd()


def smooth01(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


report = {}
for name, cfg in CLIPS.items():
    src, sobjs, sacts = import_armature(cfg['src'])
    names = MIXAMO if cfg['src'].lower().endswith('.fbx') else SET
    sact = sacts[0]
    rest_pose(src)
    MIR = cfg.get('mirror', False)
    W0 = src_world(src, names, Matrix.Identity(4), MIR)
    lr = W0['LeftUpLeg'].to_translation() - W0['RightUpLeg'].to_translation()
    turn0 = Matrix.Rotation(-math.atan2(lr.y, lr.x), 4, 'Z')
    Ws0 = src_world(src, names, turn0, MIR)
    C = matched_offsets(Ws0)
    rest_pose(rig)
    k = (wm('Hips').to_translation().z - min(wm('LeftFoot').to_translation().z, wm('RightFoot').to_translation().z)) / \
        (Ws0['Hips'].to_translation().z - min(Ws0['LeftFoot'].to_translation().z, Ws0['RightFoot'].to_translation().z))
    src.animation_data.action = sact
    if len(sact.slots):
        src.animation_data.action_slot = sact.slots[0]
    f0, f1 = sact.frame_range
    DEATH = cfg.get('death', False)
    if DEATH:
        # the fall up to its settle (pelvis within 1 cm of its final height from then on), played in cfg['seconds']
        hz = []
        for f in range(int(f0), int(f1) + 1):
            sc.frame_set(f); hz.append(src_world(src, names, turn0, MIR)['Hips'].to_translation().z)
        settle = next(i for i in range(len(hz)) if all(abs(z - hz[-1]) < 0.01 / k for z in hz[i:]))
        f1 = f0 + settle
        n_out = int(round(cfg['seconds'] * FPS)) + 1
        times = [f0 + (f1 - f0) * i / (n_out - 1) for i in range(n_out)]
        rel_i, yaw, turn = 0, 0.0, turn0
    else:
        if cfg.get('end_s'):
            f1 = min(f1, f0 + cfg['end_s'] * cfg['fps'])
        n_out = int(round((f1 - f0) / cfg['fps'] * FPS)) + 1
        times = [f0 + i * cfg['fps'] / FPS for i in range(n_out)]
        # release: the delivering hand's farthest reach in front of the chest (source frames, unturned)
        # (Cast: the throw after the hand's overhead peak, not the wind-up)
        hand = cfg['hand']; best = (-1, 0); track = []
        for i, f in enumerate(times):
            sc.frame_set(int(f), subframe=f - int(f))
            Ws = src_world(src, names, turn0, MIR)
            reach = (Ws[hand].to_translation() - Ws['Spine'].to_translation())
            track.append((reach.z, Vector((reach.x, reach.y, 0))))
        start = max(range(len(track)), key=lambda i: track[i][0]) if cfg.get('after_peak') else 0
        for i in range(start, len(track)):
            if track[i][1].length > best[0]:
                best = (track[i][1].length, i, track[i][1].copy())
        rel_i = best[1]; reach = best[2]
        yaw = math.atan2(-reach.x, -reach.y)                 # turn the reach direction onto -Y
        turn = Matrix.Rotation(yaw, 4, "Z") @ turn0
    sc.frame_set(int(times[0]), subframe=times[0] - int(times[0]))
    hips_src0 = src_world(src, names, turn, MIR)['Hips'].to_translation()
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    dur = (n_out - 1) / FPS; t_rel = rel_i / FPS
    keep, turn_share = (1.0, 1.0) if DEATH else (PELVIS_KEEP, PELVIS_TURN)
    poses = []                                          # per frame: {bone: local quaternion}, pelvis location
    hips_z = []
    for i, f in enumerate(times):
        sc.frame_set(int(f), subframe=f - int(f))
        Ws = src_world(src, names, turn, MIR)
        rest_pose(rig)
        for o in OURS:
            R = rot(Ws[o]) @ C[o]; head = None
            if o == 'Hips':
                head = ST['hips_world'] + (Ws['Hips'].to_translation() - hips_src0) * k * keep
                R = ST['hips_rot'].slerp(R.to_quaternion(), turn_share).to_matrix()
            set_world_rot(o, R, head)
        t = i / FPS
        # 0 at both ends, 1 in the middle (Death: eased in only, it ends lying)
        w = smooth01(t / EASE_IN) * (1.0 if DEATH else smooth01((dur - t) / EASE_OUT))
        for o in OURS:
            pb = rig.pose.bones[o]; qc = pb.matrix_basis.to_quaternion(); qs = ST['q'][o]
            if cfg.get('staff') is False and o in STAFF_ARM:
                q = qs.copy()
            else:
                if qs.dot(qc) < 0:
                    qc.negate()
                q = qs.slerp(qc, w)
            loc = ST['hips_loc'].lerp(pb.matrix_basis.to_translation(), w) if o == 'Hips' else Vector()
            pb.rotation_quaternion = q; pb.location = loc
        upd()
        if not DEATH:
            reach_hips()
            for leg in ('Left', 'Right'):
                leg_ik(leg, ST['feet'][leg + 'Foot'].to_translation(), ST['feet'][leg + 'Foot'])
                rig.pose.bones[leg + 'ToeBase'].rotation_quaternion = ST['q'][leg + 'ToeBase']; upd()
        limit_swing('RightHand', WRIST_MAX); limit_swing('LeftHand', WRIST_MAX)
        if DEATH:
            death_floor()
            staff_level()
        else:
            lift_staff()
        poses.append(({o: rig.pose.bones[o].matrix_basis.to_quaternion() for o in OURS},
                      rig.pose.bones['Hips'].matrix_basis.to_translation()))
        hips_z.append(wm('Hips').to_translation().z)
    if DEATH and CORPSE_LEGS:
        i_down = next(i for i, z in enumerate(hips_z) if z < DOWN_Z)
        for i in range(i_down, len(poses)):
            wl = smooth01((i - i_down) / FPS / LEGS_SETTLE)
            rest_pose(rig)
            for o, q in poses[i][0].items():
                rig.pose.bones[o].rotation_quaternion = q
            rig.pose.bones['Hips'].location = poses[i][1]; upd()
            for o in LEGS:                                  # parents first: thigh, shin, foot, toes per side
                q, qc = wm(o).to_quaternion(), CORPSE_LEGS[o].copy()
                if q.dot(qc) < 0:
                    qc.negate()
                set_world_rot(o, q.slerp(qc, wl).to_matrix())
            death_floor(); staff_level()
            poses[i] = ({o: rig.pose.bones[o].matrix_basis.to_quaternion() for o in OURS},
                        rig.pose.bones['Hips'].matrix_basis.to_translation())

    def apply_pose(p):
        rest_pose(rig)
        for o, q in p[0].items():
            rig.pose.bones[o].rotation_quaternion = q
        rig.pose.bones['Hips'].location = p[1]; upd()

    def staff_axis():
        return (rot(rig.matrix_world @ rig.pose.bones['Staff'].matrix) @ Vector((0, 1, 0))).normalized()

    staff_deg = None
    if cfg.get('staff'):
        # staff toward the target at the release: the forearm takes half of the turn that brings the staff axis
        # there and the hand the rest (bell weight around the release, zero at both ends)
        apply_pose(poses[rel_i])
        want = Vector((0, -math.cos(math.radians(STAFF_UP_DEG)), math.sin(math.radians(STAFF_UP_DEG))))
        Q = staff_axis().rotation_difference(want); staff_deg = math.degrees(Q.angle)
        sigma = max(t_rel - EASE_IN * 0.5, 0.15)
        for i, p in enumerate(poses):
            t = i / FPS; bw = math.exp(-((t - t_rel) / (sigma if t < t_rel else sigma * 1.4)) ** 2)
            bw *= smooth01(t / EASE_IN) * smooth01((dur - t) / EASE_OUT)
            apply_pose(p)
            goal = Quaternion().slerp(Q, bw) @ staff_axis()
            set_world_rot('LeftForeArm', Quaternion().slerp(Q, bw * 0.5).to_matrix() @ rot(wm('LeftForeArm')))
            set_world_rot('LeftHand', staff_axis().rotation_difference(goal).to_matrix() @ rot(wm('LeftHand')))
            limit_swing('LeftHand', WRIST_MAX)
            lift_staff()
            for o in ('LeftArm', 'LeftForeArm', 'LeftHand'):
                p[0][o] = rig.pose.bones[o].matrix_basis.to_quaternion()
    # keys: written straight into the action (keying with an action attached re-evaluates it over the solved pose)
    act = bpy.data.actions.get(name)
    if act:
        bpy.data.actions.remove(act)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rest_pose(rig); rig.animation_data_create(); rig.animation_data.action = act
    for o in OURS:
        qs = [p[0][o] for p in poses]
        for j in range(1, len(qs)):
            if qs[j - 1].dot(qs[j]) < 0:
                qs[j] = -qs[j]
        chans = [('rotation_quaternion', c, [q[c] for q in qs]) for c in range(4)]
        if o == 'Hips':
            chans += [('location', c, [p[1][c] for p in poses]) for c in range(3)]
        for prop, c, vals in chans:
            fc = act.fcurve_ensure_for_datablock(rig, f'pose.bones["{o}"].{prop}', index=c, group_name=o)
            fc.keyframe_points.add(len(vals))
            fc.keyframe_points.foreach_set('co', [x for j, v in enumerate(vals) for x in (j, v)])
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
            fc.update()
    if DEATH:
        # 'Dead': the last Death pose held (two keys)
        if 'Dead' in bpy.data.actions:
            bpy.data.actions.remove(bpy.data.actions['Dead'])
        dead = bpy.data.actions.new('Dead'); dead.use_fake_user = True
        rig.animation_data.action = dead
        last = poses[-1]
        for o in OURS:
            chans = [('rotation_quaternion', c, last[0][o][c]) for c in range(4)]
            if o == 'Hips':
                chans += [('location', c, last[1][c]) for c in range(3)]
            for prop, c, v in chans:
                fc = dead.fcurve_ensure_for_datablock(rig, f'pose.bones["{o}"].{prop}', index=c, group_name=o)
                fc.keyframe_points.add(2); fc.keyframe_points.foreach_set('co', [0, v, 1, v]); fc.update()
    report[name] = dict(source=os.path.relpath(cfg['src'], ROOT), frames=n_out, seconds=round(dur, 4),
                        release_s=round(t_rel, 4), yaw_deg=round(math.degrees(yaw), 1), hip_ratio=round(k, 3),
                        staff_turn_deg=None if staff_deg is None else round(staff_deg, 1))
    rig.animation_data.action = None
    drop(sobjs, sacts)
    print('LIBCLIP', name, json.dumps(report[name]))
json.dump(report, open(os.path.join(common.WORK, 'library_clips.json'), 'w'), indent=1)
sc.render.fps, sc.render.fps_base = FPS, 1.0
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
