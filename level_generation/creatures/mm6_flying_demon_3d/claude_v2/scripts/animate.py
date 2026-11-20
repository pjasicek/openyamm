"""Flying demon v2 clips on claude_v2/work/assembled.blend (24 fps keys; saves work/animated.blend).

Body motion comes from Meshy library clips (meshy/claude_anim_v1, rigged on this body by claude_rig_v1): each mapped
bone copies the clip bone's world rotation change from rest (delta retarget; both skeletons are Meshy auto-rigs of
the same mesh). On top, per frame:
  - hover posture: hips translation damped, wingbeat bob, body leans forward like the native side frames,
  - legs dangle (thighs slightly forward, knees bent, feet and toes pointed down) with a lagging sway,
  - wrists keep half of the clip's hand flex; forearm twist bones share the hand roll (25/50/75 %),
  - fingers keep the hooked rest claws, opening for the attack spread and closing for the clutch,
  - wings flap on the native 0.75 s cycle: high V (a) -> spread/drooping (d) -> rising (e, f), outer wing lagging,
    fingers folding on the upstroke, tips sweeping back at the top.
Clips: Flight 2.25 s loop (Idle 1 body, 3 beats), Attack 0.75 s (Mage Spell Cast 1: arms spread wide, sweep and
clutch, as native wdmatk), Cast 0.75 s (same spell clip: gather, then fling wide), Hit 0.75 s (Hit Reaction, torso turn damped to 45 % to stay facing like the native recoil), Death 1.0 s (Electrocution Reaction flail; the body shrinks
away from 0.45 s as the engine's disintegration burst plays), Dead (fully shrunk, held).
"""
import bpy, os, sys, math
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(HERE)
FPS = 24
rig = bpy.data.objects['Flying_Demon_Rig']
scene = bpy.context.scene; scene.render.fps = FPS
MAP = {'Hips': 'Hips', 'Spine02': 'Spine', 'Spine01': 'Spine1', 'Spine': 'Spine2', 'neck': 'Neck', 'Head': 'Head'}
for s in ('Left', 'Right'):
    for b in ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg', 'Foot', 'ToeBase'):
        MAP[s + b] = s + b
BODY_BONES = {'mixamorig:Hips', 'mixamorig:Spine', 'mixamorig:Spine1', 'mixamorig:Spine2'}
LEG_BONES = {f'mixamorig:{s}{b}' for s in ('Left', 'Right') for b in ('UpLeg', 'Leg', 'Foot', 'ToeBase')}
FINGERS = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
SIDES = {'Left': 1.0, 'Right': -1.0}

# ---- source clips -----------------------------------------------------------------------------------------------
before = set(bpy.data.objects); before_act = set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=os.path.join(PROJECT, 'meshy', 'claude_anim_v1', 'result_animation_glb_url.glb'))
imported = [o for o in bpy.data.objects if o not in before]
marm = next(o for o in imported if o.type == 'ARMATURE')
src_actions = {a.name: a for a in bpy.data.actions if a not in before_act}
for o in imported:
    if o.type == 'MESH':
        o.hide_viewport = True
new_rest = {k: (marm.matrix_world @ marm.data.bones[k].matrix_local) for k in MAP}
old_rest = {('mixamorig:' + v): (rig.matrix_world @ rig.data.bones['mixamorig:' + v].matrix_local) for v in MAP.values()}
cache = {}


def sample(action, t):
    """World matrices of the Meshy bones at clip time t (seconds)."""
    key = (action, round(t, 4))
    if key not in cache:
        marm.animation_data.action = src_actions[action]
        f = t * FPS
        scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        cache[key] = {k: marm.matrix_world @ marm.pose.bones[k].matrix for k in MAP}
    return cache[key]


# ---- posing helpers ---------------------------------------------------------------------------------------------
ORDER = [b.name for b in rig.data.bones]
rig_rot_inv = rig.matrix_world.to_quaternion().inverted()
inv = rig.matrix_world.inverted()


def update():
    bpy.context.view_layer.update()


def reset():
    rig.animation_data_create(); rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    update()


def rotate_world(name, axis, deg, pivot=None):
    if abs(deg) < 1e-6:
        return
    pb = rig.pose.bones[name]
    head = rig.matrix_world @ pb.head if pivot is None else pivot
    m = rig.matrix_world @ pb.matrix
    r = Matrix.Translation(head) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis).normalized()) \
        @ Matrix.Translation(-head)
    pb.matrix = inv @ (r @ m)
    update()


def world_rot(name):
    return (rig.matrix_world @ rig.pose.bones[name].matrix).to_quaternion()


def retarget(frame, hips_xy=0.5, hand_keep=0.5, body_keep=1.0):
    for n in ORDER:
        if not n.startswith('mixamorig:') or n[10:] not in MAP.values() or n in LEG_BONES:
            continue
        src = next(k for k, v in MAP.items() if 'mixamorig:' + v == n)
        delta = frame[src].to_quaternion() @ new_rest[src].to_quaternion().inverted()
        if n.endswith('Hand'):
            delta = Quaternion().slerp(delta, hand_keep)
        elif n in BODY_BONES:
            delta = Quaternion().slerp(delta, body_keep)
        target = delta @ old_rest[n].to_quaternion()
        pb = rig.pose.bones[n]
        head = pb.head.copy()
        if n == 'mixamorig:Hips':
            move = frame[src].translation - new_rest[src].translation
            head = inv @ (old_rest[n].translation + Vector((move.x * hips_xy, move.y * hips_xy, 0.0)))
        pb.matrix = Matrix.LocRotScale(head, rig_rot_inv @ target, Vector((1, 1, 1)))
        update()


def body_axes():
    """Current body frame from Spine2: forward (-Y at rest), up (+Z), lateral (+X)."""
    q = world_rot('mixamorig:Spine2') @ old_rest['mixamorig:Spine2'].to_quaternion().inverted()
    return q @ Vector((0, -1, 0)), q @ Vector((0, 0, 1)), q @ Vector((1, 0, 0))


def hover(lean, bob):
    hips = rig.pose.bones['mixamorig:Hips']
    hips.location = hips.location + Vector((0, 0, 0))
    m = rig.matrix_world @ hips.matrix
    hips.matrix = inv @ (Matrix.Translation(Vector((0, 0, bob))) @ m); update()
    rotate_world('mixamorig:Hips', (1, 0, 0), lean)


def legs(t, swing=1.0, spread=0.0):
    _, _, lat = body_axes()
    hips_q = world_rot('mixamorig:Hips') @ old_rest['mixamorig:Hips'].to_quaternion().inverted()
    lat = hips_q @ Vector((1, 0, 0)); fwd = hips_q @ Vector((0, -1, 0))
    for side, sg in SIDES.items():
        lag = math.sin(2 * math.pi * (t / 0.75) - 1.2 - (0.4 if sg > 0 else 0.0))
        rotate_world(f'mixamorig:{side}UpLeg', lat, -6 - 4 * swing * lag)
        rotate_world(f'mixamorig:{side}UpLeg', fwd, sg * spread)
        rotate_world(f'mixamorig:{side}Leg', lat, 22 + 6 * swing * lag)
        rotate_world(f'mixamorig:{side}Foot', lat, 48 + 6 * swing * lag)
        rotate_world(f'mixamorig:{side}ToeBase', lat, 18)


_CURL_SIGN = {}


def curl_sign(side, finger):
    """+1 or -1: the local-X direction that flexes this finger toward its palm (the rest claws already hook)."""
    key = (side, finger)
    if key not in _CURL_SIGN:
        b1 = rig.data.bones[f'mixamorig:{side}Hand{finger}1']
        b3 = rig.data.bones[f'mixamorig:{side}Hand{finger}3']
        axis = (b1.tail_local - b1.head_local).normalized()
        bend = (b3.tail_local - b1.head_local); bend = bend - axis * bend.dot(axis)
        local_x = b1.matrix_local.to_3x3() @ Vector((1, 0, 0))
        moved = axis.cross(local_x)          # tip motion direction for a +X rotation (approx.)
        _CURL_SIGN[key] = 1.0 if moved.dot(bend) < 0 else -1.0
    return _CURL_SIGN[key]


def fingers(side, curl):
    for finger in FINGERS:
        sg = curl_sign(side, finger)
        for k in (1, 2, 3):
            pb = rig.pose.bones[f'mixamorig:{side}Hand{finger}{k}']
            amount = curl * (0.6 if k == 1 else 1.0) * (0.6 if finger == 'Thumb' else 1.0)
            pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion((1, 0, 0), math.radians(sg * amount))
    update()


def twist(side):
    """Share the hand's roll about the forearm axis with the forearm twist bones."""
    hand = rig.pose.bones[f'mixamorig:{side}Hand']
    q = hand.rotation_quaternion
    axis = Vector((0, 1, 0))
    proj = Vector((q.x, q.y, q.z)).dot(axis)
    tw = Quaternion((q.w, 0, proj, 0)); tw.normalize()
    angle = 2 * math.atan2(proj, q.w)
    for k, frac in enumerate((0.25, 0.5, 0.75)):
        name = f'Demon_{side}_ForearmTwist{k}'
        if name in rig.pose.bones:
            rig.pose.bones[name].rotation_quaternion = Quaternion((0, 1, 0), angle * frac)
    update()


def wings(up, sweep, fold, lag):
    fwd, upv, _ = body_axes()
    for side, sg in SIDES.items():
        root, arm = f'Wing_{side}_Root', f'Wing_{side}_Arm'
        rotate_world(root, upv * sg, sweep)
        rotate_world(root, fwd * sg, up)
        rotate_world(arm, fwd * sg, lag)
        for k in range(1, 5):
            rotate_world(f'Wing_{side}_Finger{k}', fwd * sg, -fold * (1.0 - 0.2 * (k - 1)))


def flap(p, amp=1.0, mid=20.0):
    c, s = math.cos(2 * math.pi * p), math.sin(2 * math.pi * p)
    return {'up': mid + 30 * amp * c, 'sweep': 6 + 8 * amp * c, 'fold': 16 * amp * max(0.0, -s) ** 1.2,
            'lag': 9 * amp * s, 'bob': -0.025 * amp * c}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def lerp_keys(keys, t):
    for (t0, v0), (t1, v1) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = (t - t0) / max(t1 - t0, 1e-6)
            return v0 + (v1 - v0) * u
    return keys[-1][1]


def capture():
    return {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}


def mix(a, b, u):
    out = {}
    for k in a:
        qa, la, sa = a[k]; qb, lb, sb = b[k]
        if qa.dot(qb) < 0:
            qb = -qb
        out[k] = (qa.slerp(qb, u), la.lerp(lb, u), sa.lerp(sb, u))
    return out


def apply(pose):
    for k, (q, l, s) in pose.items():
        pb = rig.pose.bones[k]; pb.rotation_quaternion = q; pb.location = l; pb.scale = s
    update()


# ---- clip definitions -------------------------------------------------------------------------------------------
IDLE_LEN = 1.867


def pose_flight(t, period=2.25):
    reset()
    retarget(sample('Idle_02', (t / period) * IDLE_LEN % IDLE_LEN))
    f = flap((t % 0.75) / 0.75)
    hover(10, f['bob'])
    legs(t)
    for side in SIDES:
        twist(side); fingers(side, 6)
    wings(f['up'], f['sweep'], f['fold'], f['lag'])
    return capture()


ATTACK_SRC = [(0.0, 0.55), (0.12, 0.85), (0.30, 1.55), (0.45, 2.30), (0.56, 2.62), (0.75, 2.95)]


def pose_attack(t):
    base = pose_flight(t)
    reset()
    retarget(sample('mage_soell_cast_1', lerp_keys(ATTACK_SRC, t)), hips_xy=0.6)
    f = flap((t % 0.75) / 0.75, amp=0.5, mid=12)
    hover(14, f['bob'])
    legs(t, spread=4)
    curl = lerp_keys([(0, 6), (0.30, -18), (0.42, -10), (0.55, 30), (0.75, 6)], t)
    for side in SIDES:
        twist(side); fingers(side, curl)
    wings(f['up'], f['sweep'], f['fold'], f['lag'])
    action = capture()
    w = ss(t / 0.12) * (1.0 - ss((t - 0.58) / 0.17))
    return mix(base, action, w)


CAST_SRC = [(0.0, 0.0), (0.28, 0.40), (0.40, 0.75), (0.52, 1.55), (0.75, 2.0)]


def pose_cast(t):
    """Native casting reuses the attack frames; the engine needs a distinct clip: hands gather in front (the spell
    glow sits between the palms), then fling wide on release."""
    base = pose_flight(t)
    reset()
    retarget(sample('mage_soell_cast_1', lerp_keys(CAST_SRC, t)), hips_xy=0.5)
    f = flap((t % 0.75) / 0.75, amp=0.6, mid=18)
    hover(12, f['bob'])
    legs(t, spread=3)
    curl = lerp_keys([(0, 6), (0.3, 25), (0.45, -15), (0.75, 6)], t)
    for side in SIDES:
        twist(side); fingers(side, curl)
    wings(f['up'], f['sweep'], f['fold'], f['lag'])
    action = capture()
    w = ss(t / 0.1) * (1.0 - ss((t - 0.6) / 0.15))
    return mix(base, action, w)


HIT_SRC = [(0.0, 0.0), (0.2, 0.45), (0.5, 1.1), (0.75, 1.6)]


def pose_hit(t):
    base = pose_flight(t)
    reset()
    retarget(sample('Hit_Reaction', lerp_keys(HIT_SRC, t)), hips_xy=0.5, body_keep=0.45)
    jolt = math.sin(math.pi * min(1.0, t / 0.4))
    hover(10 - 16 * jolt, 0.03 * jolt)
    legs(t, swing=1.6, spread=6 * jolt)
    for side in SIDES:
        twist(side); fingers(side, 6 - 14 * jolt)
    wings(20 + 38 * jolt, 6 + 10 * jolt, 22 * jolt, -6 * jolt)
    action = capture()
    w = ss(t / 0.06) * (1.0 - ss((t - 0.5) / 0.25))
    return mix(base, action, w)


def pose_death(t):
    reset()
    retarget(sample('Electrocution_Reaction', 0.6 + t * 2.2), hips_xy=0.4)
    f = flap((t % 0.4) / 0.4, amp=1.1, mid=25)
    hover(10 + 25 * ss(t / 0.8), f['bob'])
    legs(t, swing=2.0, spread=8)
    for side in SIDES:
        twist(side); fingers(side, 20 * math.sin(14 * t))
    wings(f['up'], f['sweep'], f['fold'], f['lag'])
    k = 1.0 - 0.995 * ss((t - 0.45) / 0.45)            # burns away inside the disintegration burst
    rig.pose.bones['mixamorig:Hips'].scale = (k, k, k); update()
    return capture()


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    n = int(round(seconds * FPS))
    poses = [fn(((f % n) if loop else f) / FPS) for f in range(n + 1)]
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data.action = act
    prev = {}
    for f, pose in enumerate(poses):
        for k, (q, l, s) in pose.items():
            if k in prev and prev[k].dot(q) < 0:
                q = -q
            prev[k] = q
            pb = rig.pose.bones[k]; pb.rotation_quaternion = q; pb.location = l; pb.scale = s
            pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
            pb.keyframe_insert('scale', frame=f)
    rig.animation_data.action = None
    print('CLIP', name, seconds, flush=True)


mods = [m for o in bpy.data.objects if o.type == 'MESH' for m in o.modifiers if m.type == 'ARMATURE']
for m in mods:
    m.show_viewport = False                       # skip mesh deformation while posing
CLIPS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
todo = {'Flight': (2.25, True, pose_flight), 'Attack': (0.75, False, pose_attack),
        'Cast': (0.75, False, pose_cast), 'Hit': (0.75, False, pose_hit),
        'Death': (1.0, False, pose_death), 'Dead': (1.0, False, lambda t: pose_death(1.0))}
for name, (sec, loop, fn) in todo.items():
    if not CLIPS or name in CLIPS:
        key_action(name, sec, loop, fn)
for m in mods:
    m.show_viewport = True
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)
for a in src_actions.values():
    bpy.data.actions.remove(a)
rig.animation_data.action = bpy.data.actions['Flight']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'animated.blend'))
print('SAVED')
