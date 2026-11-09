"""Game clips from the retargeted Mixamo sources (retarget_fbx.py, 'src_<Name>' actions on Skeleton_Rig).

Per clip: a source window [t0, t1] resampled to the output duration at 24 fps, then
- yaw: the whole body is turned about the rest hips so the mean chest heading faces -Y (Mixamo's sword-and-shield
  stance turns the torso ~40 degrees; the native skeleton faces the viewer),
- straighten s: spine, thigh, shin and foot rotations slerped toward the bind pose by s (the native stance is
  upright with a slight knee bend; Mixamo's is a deep crouch),
- drift: 'loop' removes the hips' linear XY travel (walk/run; the travel per cycle is the stride), 'start' keeps the
  XY offset relative to frame 0 scaled by `keep`,
- ground: per frame the lowest body vertex (sword excluded) is put on z = 0,
- the right hand keeps the solved grip (scene['ske_grip']) on every frame,
- Death: the skull comes off at the end and rolls to the ground beside the body (native last frames); Dead holds it.
Quaternion keys are made sign-continuous. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
src_blend, out_blend = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
scene = bpy.context.scene
rig = bpy.data.objects['Skeleton_Rig']; body = bpy.data.objects['Skeleton']
W = rig.matrix_world
grip = {k: Quaternion(v) for k, v in json.loads(scene['ske_grip']).items()}
FPS = 24
CLIPS = {
    'Standing': dict(src='src_Standing', t=(0.0, 2.533), dur=2.5, stance=True, right_arm=True),
    'Walking': dict(src='src_Walking', t=(0.0, 1.1), dur=1.1, straighten=0.4, drift='loop'),
    'Running': dict(src='src_Running', t=(0.0, 0.7), dur=0.7, straighten=0.5, drift='loop'),
    'Attack': dict(src='src_Attack', t=(0.05, 1.35), dur=1.3, stance=True, spine=0.6),   # source speed; a ready pause is prepended below, marked in actors.yml events
    'Hit': dict(src='src_Hit3', t=(0.0, 0.7), dur=0.75, stance=True, spine=0.8),
    # Death and Fidget at source speed (2026-10-10): the engine plays a longer death and fidget to their end
    # (they were 1.53x / 1.2x in 1.5 s / 1.0 s)
    'Death': dict(src='src_Death', t=(0.0, 2.3), dur=2.3, straighten=0.0, drift='start', keep=0.5, skull=0.55),
    'Fidget': dict(src='src_Fidget', t=(1.2, 2.4), dur=1.2, stance=True, right_arm=True),
}
# stance clips (titan route): hips and legs planted in the skeleton's own stance (bind pose plus a slight knee bend),
# spine at `spine` of the source, neck/head and arms as the source (relative to the chest), plus the native stoop.
# Angles are about each bone's local X (+ = tail toward its local Z = forward for spine and legs).
STANCE = {'LeftUpLeg': 12, 'RightUpLeg': 12, 'LeftLeg': -24, 'RightLeg': -24, 'LeftFoot': 12, 'RightFoot': 12,
          'Spine2': 7, 'Neck': 12, 'Head': -6}
# native stand (skesta0-2): right upper arm hanging close to the body, elbow bent forward, the cutlass pointing forward
# and out, slightly down. World-axis turns in the rest chest frame (carried by the posed chest), applied in order.
RIGHT_ARM = [('RightArm', (0, 1, 0), -6), ('RightArm', (1, 0, 0), -10), ('RightForeArm', (1, 0, 0), -40),
             ('RightHand', (0, 0, 1), -40), ('RightHand', (1, 0, 0), 48)]   # +48: undo the forearm's 40 deg lift
STRAIGHT = ['Spine', 'Spine1', 'Spine2', 'LeftUpLeg', 'RightUpLeg', 'LeftLeg', 'RightLeg', 'LeftFoot', 'RightFoot']
bones = [b.name for b in rig.data.bones]
piece = np.zeros(len(body.data.vertices), dtype=np.int32)
body.data.attributes['piece'].data.foreach_get('value', piece)
not_sword = piece != 999


def set_action(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def pb(n):
    return rig.pose.bones['mixamorig:' + n]


def eval_frame(sf):
    scene.frame_set(int(math.floor(sf)), subframe=sf - math.floor(sf))


def lowest():
    deps = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(deps); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3)[not_sword]
    return float(co[:, 2].min())


def heading():
    l = W @ pb('LeftArm').head; r = W @ pb('RightArm').head
    line = Vector((l.x - r.x, l.y - r.y, 0)).normalized()
    f = line.cross(Vector((0, 0, 1)))
    return math.atan2(f.x, -f.y)                # 0 when facing -Y


rest_hips = W @ rig.data.bones['mixamorig:Hips'].head_local
stride = {}
for name, c in CLIPS.items():
    src = bpy.data.actions[c['src']]
    n = int(round(c['dur'] * FPS))
    times = [c['t'][0] + (c['t'][1] - c['t'][0]) * i / n for i in range(n + 1)]
    # pass 1: sample source poses (matrix_basis per bone) and the chest heading
    set_action(src)
    frames, heads, hips_w = [], [], []
    for t in times:
        eval_frame(t * FPS)
        frames.append({b: rig.pose.bones[b].matrix_basis.copy() for b in bones})
        heads.append(heading())
        hips_w.append((W @ pb('Hips').matrix).copy())
    yaw = 0.0 if name in ('Walking', 'Running') or c.get('stance') else \
        -math.atan2(np.mean(np.sin(heads)), np.mean(np.cos(heads)))
    if name in ('Walking', 'Running'):
        travel = hips_w[-1].translation - hips_w[0].translation
        stride[name + '_source'] = round(math.hypot(travel.x, travel.y), 3)
    set_action(None)
    act = bpy.data.actions.get(name)
    if act:
        bpy.data.actions.remove(act)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    set_action(act)
    Ryaw = Matrix.Translation(rest_hips) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation(-rest_hips)
    p0 = hips_w[0].translation.copy()
    prev = {}
    for i, (fr, hw) in enumerate(zip(frames, hips_w)):
        for b in bones:
            rig.pose.bones[b].matrix_basis = fr[b]
        bpy.context.view_layer.update()
        if c.get('stance'):
            z0 = hips_w[0].translation.z
            p = pb('Hips'); p.matrix_basis = Matrix()
            bpy.context.view_layer.update()
            m = W @ p.matrix
            m.translation.z += (hw.translation.z - z0) * 0.5
            p.matrix = W.inverted() @ m
            for b in ('LeftUpLeg', 'RightUpLeg', 'LeftLeg', 'RightLeg', 'LeftFoot', 'RightFoot', 'LeftToeBase',
                      'RightToeBase'):
                pb(b).matrix_basis = Matrix()
            for b in ('Spine', 'Spine1', 'Spine2'):
                q = pb(b).matrix_basis.to_quaternion(); pb(b).rotation_mode = 'QUATERNION'
                pb(b).rotation_quaternion = Quaternion().slerp(q, c.get('spine', 0.3))
            for b, deg in STANCE.items():
                q = pb(b).matrix_basis.to_quaternion(); pb(b).rotation_mode = 'QUATERNION'
                pb(b).rotation_quaternion = q @ Quaternion((1, 0, 0), math.radians(deg))
            bpy.context.view_layer.update()
        # hips: drift, then yaw about the rest hips
        m = hw.copy()
        d = m.translation - p0
        if c.get('drift') == 'loop':
            lin = (hips_w[-1].translation - p0) * (i / n)
            m.translation = Vector((p0.x + d.x - lin.x, p0.y + d.y - lin.y, m.translation.z))
            m.translation.x += rest_hips.x - p0.x; m.translation.y += rest_hips.y - p0.y
        else:
            k = c.get('keep', 0.0)
            m.translation = Vector((rest_hips.x + d.x * k, rest_hips.y + d.y * k, m.translation.z))
        if not c.get('stance'):
            m = Ryaw @ m
            pb('Hips').matrix = W.inverted() @ m
            bpy.context.view_layer.update()
        if c.get('right_arm'):
            chest_rest = (W @ rig.data.bones['mixamorig:Spine2'].matrix_local).to_3x3()
            for b in ('RightShoulder', 'RightArm', 'RightForeArm', 'RightHand'):
                pb(b).matrix_basis = Matrix()
            bpy.context.view_layer.update()
            Rc = (W @ pb('Spine2').matrix).to_3x3() @ chest_rest.inverted()
            for b, axis, deg in RIGHT_ARM:
                p = pb(b)
                m = W @ p.matrix
                h = m.translation.copy()
                ax = (Rc @ Vector(axis)).normalized()
                p.matrix = W.inverted() @ (Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, ax)
                                           @ Matrix.Translation(-h) @ m)
                bpy.context.view_layer.update()
        s = c.get('straighten', 0.0)
        if s > 0:
            for b in STRAIGHT:
                p = pb(b); q = p.matrix_basis.to_quaternion()
                p.rotation_mode = 'QUATERNION'
                p.rotation_quaternion = q.slerp(Quaternion(), s)
        for bname, q in grip.items():
            rig.pose.bones[bname].rotation_mode = 'QUATERNION'
            rig.pose.bones[bname].rotation_quaternion = q
        bpy.context.view_layer.update()
        dz = -lowest()
        m = W @ pb('Hips').matrix
        m.translation.z += dz
        pb('Hips').matrix = W.inverted() @ m
        bpy.context.view_layer.update()
        for b in bones:
            p = rig.pose.bones[b]
            p.rotation_mode = 'QUATERNION'
            q = p.rotation_quaternion.copy()
            if b in prev and q.dot(prev[b]) < 0:
                q.negate(); p.rotation_quaternion = q
            prev[b] = q
            p.keyframe_insert('rotation_quaternion', frame=i)
            if b in ('mixamorig:Hips', 'mixamorig:Head'):
                p.keyframe_insert('location', frame=i)
    if c.get('skull'):
        # the skull separates over the last part and rolls to the ground beside the body (native skedy* last frames)
        fall = c['skull'] * FPS
        start = n + 1
        hb = pb('Head')
        bpy.context.view_layer.update()
        h0 = (W @ hb.matrix).copy()
        body_c = W @ pb('Spine1').head
        side = Vector((h0.translation.x - body_c.x, h0.translation.y - body_c.y, 0))
        side = side.normalized() if side.length > 1e-4 else Vector((1, 0, 0))
        dest = h0.translation + side * 0.22 + Vector((0.12, 0.0, 0.0)).cross(Vector((0, 0, 1))) * 0.0
        dest.z = 0.085
        roll_axis = side.cross(Vector((0, 0, 1))).normalized()
        for j in range(1, int(round(fall)) + 1):
            u = j / fall
            e = 1 - (1 - u) ** 2                                   # ease out
            bounce = 0.06 * math.sin(math.pi * min(1.0, u * 1.6)) * (1 - u)
            pos = h0.translation.lerp(dest, e) + Vector((0, 0, bounce))
            R = Matrix.Rotation(math.radians(-110) * e, 4, roll_axis) @ Matrix.Rotation(math.radians(35) * e, 4, 'Z')
            M = R @ h0.to_3x3().to_4x4(); M.translation = pos
            hb.matrix = W.inverted() @ M
            bpy.context.view_layer.update()
            hb.keyframe_insert('rotation_quaternion', frame=n + j)
            hb.keyframe_insert('location', frame=n + j)
            for b in bones:
                if b != hb.name:
                    rig.pose.bones[b].keyframe_insert('rotation_quaternion', frame=n + j)
            pb('Hips').keyframe_insert('location', frame=n + j)
            jaw = pb('Jaw'); jaw.rotation_mode = 'QUATERNION'
            jaw.rotation_quaternion = Quaternion((1, 0, 0), math.radians(18) * e)
            jaw.keyframe_insert('rotation_quaternion', frame=n + j)
        n = n + int(round(fall))
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    if name in ('Walking', 'Running'):
        # stride per cycle from the processed feet: each foot sweeps back one step length per cycle while planted
        ys = []
        for f in range(n + 1):
            scene.frame_set(f)
            ys.append([(W @ pb(s_ + 'Foot').head).y for s_ in ('Left', 'Right')])
        ys = np.array(ys)
        stride[name] = round(float(np.mean(ys.max(0) - ys.min(0))) * 2, 3)
    print('CLIP', name, f'{n / FPS:.3f} s', 'yaw', round(math.degrees(yaw), 1), 'stride', stride.get(name, ''))
    if name == 'Death':
        # Dead: the final pose held (one second, like the other creatures)
        dead = bpy.data.actions.get('Dead')
        if dead:
            bpy.data.actions.remove(dead)
        dead = bpy.data.actions.new('Dead'); dead.use_fake_user = True
        set_action(act); scene.frame_set(n)
        poses = {b: (rig.pose.bones[b].rotation_quaternion.copy(), rig.pose.bones[b].location.copy()) for b in bones}
        set_action(dead)
        for f in (0, FPS):
            for b in bones:
                p = rig.pose.bones[b]; p.rotation_quaternion, p.location = poses[b]
                p.keyframe_insert('rotation_quaternion', frame=f)
                if b in ('mixamorig:Hips', 'mixamorig:Head'):
                    p.keyframe_insert('location', frame=f)
        dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, FPS
    set_action(None)
    for p in rig.pose.bones:
        p.matrix_basis = Matrix()


# ---------------------------------------------------------------- attack body motion (user request 2026-10-09)
# The planted stance made the swing arm-only. Layered on the built Attack, timed from the sword grip's own path
# (wind-up peak = highest grip, strike end = lowest grip after it):
#  wind-up: weight back onto the right leg, hips turned sword-shoulder back, torso leaning back;
#  swing:   momentum forward - hips turn through and drop, torso leans into the cut, the left foot steps forward;
#  recover: back toward the stance (the engine then blends to Standing).
# Feet stay where the stance put them (two-bone IK in the leg's current bend plane, foot kept at its stance world
# orientation); the stepping foot follows its own target with a small lift.
def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def swing_to(p, direction):
    bpy.context.view_layer.update()
    m = W @ p.matrix
    cur = (m.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = cur.rotation_difference(direction.normalized())
    h = m.translation.copy()
    p.matrix = W.inverted() @ (Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ m)
    bpy.context.view_layer.update()


def leg_ik(side, ankle, foot_rot):
    up, lo, ft = pb(side + 'UpLeg'), pb(side + 'Leg'), pb(side + 'Foot')
    bpy.context.view_layer.update()
    H = W @ up.head; K0 = W @ lo.head
    L1 = (rig.data.bones['mixamorig:' + side + 'UpLeg'].tail_local - rig.data.bones['mixamorig:' + side + 'UpLeg'].head_local).length
    L2 = (rig.data.bones['mixamorig:' + side + 'Leg'].tail_local - rig.data.bones['mixamorig:' + side + 'Leg'].head_local).length
    d = min((ankle - H).length, L1 + L2 - 1e-4)
    axis = (ankle - H).normalized()
    along = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
    hgt = math.sqrt(max(L1 * L1 - along * along, 0.0))
    perp = (K0 - H) - axis * (K0 - H).dot(axis)
    perp = perp.normalized() if perp.length > 1e-5 else Vector((0, -1, 0))
    K = H + axis * along + perp * hgt
    swing_to(up, K - H)
    swing_to(lo, (H + axis * d) - K)
    m = W @ ft.matrix
    M = foot_rot.to_4x4(); M.translation = m.translation
    ft.matrix = W.inverted() @ M
    bpy.context.view_layer.update()


act = bpy.data.actions['Attack']
set_action(act)
n = int(act.frame_range[1])
grip_z = []
for f in range(n + 1):
    scene.frame_set(f)
    grip_z.append((W @ rig.pose.bones['Sword'].head).z)
grip_z = np.array(grip_z)
tw = int(np.argmax(grip_z[:int(n * 0.6) + 1]))
ts = tw + int(np.argmin(grip_z[tw:]))
ts = max(ts, tw + 3)
scene.frame_set(0)
stance_feet = {s: ((W @ pb(s + 'Foot').head).copy(), (W @ pb(s + 'Foot').matrix).to_3x3().copy()) for s in ('Left', 'Right')}
captured = []
BODY = ['Hips', 'Spine', 'Spine1', 'Spine2', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'RightUpLeg', 'RightLeg', 'RightFoot']
for f in range(n + 1):
    scene.frame_set(f)
    t = f
    wind = smooth(t / max(tw, 1)) if t <= tw else 1 - smooth((t - tw) / (ts - tw))
    strike = 0.0 if t <= tw else (smooth((t - tw) / (ts - tw)) if t <= ts else 1 - 0.7 * smooth((t - ts) / max(n - ts, 1)))
    step = 0.0 if t <= tw else (smooth((t - tw) / (0.7 * (ts - tw))) if t <= ts else 1 - smooth((t - ts - 1) / max(n - ts - 1, 1)))
    lift = 0.045 * math.sin(math.pi * min(1.0, max(0.0, (t - tw) / (0.7 * (ts - tw))))) if tw < t <= tw + 0.7 * (ts - tw) else 0.0
    # hips: back/forward travel (character faces -Y), drop, yaw (- = right shoulder back), torso pitch
    hp = pb('Hips')
    m = W @ hp.matrix
    c = m.translation.copy()
    off = Vector((0.0, 0.045 * wind - 0.085 * strike, -0.012 * wind - 0.035 * strike))
    yaw = math.radians(-16 * wind + 14 * strike)
    R = Matrix.Translation(c + off) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation(-c)
    hp.matrix = W.inverted() @ (R @ m)
    bpy.context.view_layer.update()
    for b, back, fwd in (('Spine1', -7, 9), ('Spine2', -5, 7)):
        p = pb(b); p.rotation_mode = 'QUATERNION'
        p.rotation_quaternion = p.rotation_quaternion @ Quaternion((1, 0, 0), math.radians(back * wind + fwd * strike))
    bpy.context.view_layer.update()
    ra, rr = stance_feet['Right']
    la, lr = stance_feet['Left']
    leg_ik('Right', ra, rr)
    leg_ik('Left', la + Vector((0.0, -0.15 * step, lift)), lr)
    captured.append({b: pb(b).matrix.copy() for b in BODY})
set_action(None)
for p in rig.pose.bones:
    p.matrix_basis = Matrix()
set_action(act)
for f, mats in enumerate(captured):
    scene.frame_set(f)
    for b in BODY:
        pb(b).matrix = mats[b]
        bpy.context.view_layer.update()
    for b in BODY:
        p = pb(b); p.rotation_mode = 'QUATERNION'
        p.keyframe_insert('rotation_quaternion', frame=f)
        if b == 'Hips':
            p.keyframe_insert('location', frame=f)
set_action(None)
for p in rig.pose.bones:
    p.matrix_basis = Matrix()
print('ATTACK body motion: wind-up peak frame', tw, 'strike end', ts, 'of', n)
scene['ske_stride'] = json.dumps(stride)
for a in list(bpy.data.actions):
    if a.name.startswith('src_'):
        a.use_fake_user = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
# ready pause before the attack (playbook "Clip timing"): ease from the Standing pose into the attack's first pose,
# so the source slash keeps its own speed and the blow lands near the native 0.75 s action end
LEAD = 0.2
act = bpy.data.actions['Attack']; st_act = bpy.data.actions['Standing']
def grab(a, f):
    set_action(a); scene.frame_set(f)
    return {b: (rig.pose.bones[b].rotation_quaternion.copy(), rig.pose.bones[b].location.copy()) for b in bones}
s0, a0 = grab(st_act, 0), grab(act, 0)
seq = []
n_lead = int(round(LEAD * FPS))
for i in range(n_lead):
    u = i / n_lead; u = u * u * (3 - 2 * u)
    seq.append({b: (s0[b][0].slerp(a0[b][0], u), s0[b][1].lerp(a0[b][1], u)) for b in bones})
for f in range(int(act.frame_range[1]) + 1):
    seq.append(grab(act, f))
set_action(None); bpy.data.actions.remove(act)
act = bpy.data.actions.new('Attack'); act.use_fake_user = True; set_action(act)
prev = {}
for i, pose in enumerate(seq):
    for b, (q, l) in pose.items():
        p_ = rig.pose.bones[b]; p_.rotation_mode = 'QUATERNION'
        if b in prev and q.dot(prev[b]) < 0:
            q = -q
        prev[b] = q; p_.rotation_quaternion = q; p_.location = l
        p_.keyframe_insert('rotation_quaternion', frame=i)
        if b in ('mixamorig:Hips', 'mixamorig:Head'):
            p_.keyframe_insert('location', frame=i)
act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(seq) - 1
set_action(None)
# blow = peak sword-tip speed in the final Attack (for actors.yml `events: attack_melee: {impact}`)
act = bpy.data.actions['Attack']; set_action(act)
tips = []
for f in range(int(act.frame_range[1]) + 1):
    scene.frame_set(f)
    M = W @ rig.pose.bones['Sword'].matrix
    tips.append(np.array(M @ Vector((0, 0.8, 0))))
sp = np.linalg.norm(np.diff(np.array(tips), axis=0), axis=1); k = int(np.argmax(sp))
print(f'IMPACT Attack {act.frame_range[1] / FPS:.3f} s, blow at {(k + 0.5) / FPS:.3f} s, '
      f'wind-up stretch to the native 0.75 s: {0.75 / ((k + 0.5) / FPS):.2f}x')
set_action(None)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
