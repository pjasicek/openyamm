"""Procedural MM7 spider clips (30 fps), adapted from mm6_spi1_claude/scripts/anim_spi1.py and the native m402 actions.
Legs: two-bone IK (Femur + Tibia) places each ankle so the tarsus keeps its rest direction and the foot lands on its
foothold; knee pole above and outside. Footholds are made symmetric (mean of each mirrored pair; the rest legs are
uneven from the three-quarter master).
  Standing  2.0 s loop   abdomen breathing, small sway, fang twitch
  Walking   1.0 s loop   alternating tetrapod (L1 R2 L3 R4 / R1 L2 R3 L4), native 8 x 125 ms
  Running   0.6 s loop   same gait, longer stride, lower duty
  Attack    1.0 s        rears up on the back legs with the front legs raised and fangs spread (m402ab/ac), lunges
                         and bites (impact IMPACT), recovers
  Hit       0.75 s       jolt back and down, legs splay, recover
  Death     1.2 s        rears with the front legs flailing (m402da0/db0), then collapses flat with the legs splayed
                         and partly curled (dc0/dd0, corpse xa0); Dead = last frame held
  Fidget    1.0 s        front legs tap, fangs work
Args: -- <in blend> <out blend>"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC))
rig = bpy.data.objects['Rig']; mesh = bpy.data.objects['Body']
FPS = 30
IMPACT = 0.55
STRIDE_WALK, STRIDE_RUN = 0.9, 1.4
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
LEGS = [f'{s}{i}' for s in 'LR' for i in range(1, 5)]
GROUP_A = ('L1', 'R2', 'L3', 'R4')
P.reset(rig)
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
bpy.context.view_layer.update()
REST_FOOT = {leg: (rig.matrix_world @ rig.pose.bones[f'Tarsus_{leg}'].tail).copy() for leg in LEGS}
REST_ANKLE = {leg: (rig.matrix_world @ rig.pose.bones[f'Tarsus_{leg}'].head).copy() for leg in LEGS}
REST_KNEE = {leg: (rig.matrix_world @ rig.pose.bones[f'Tibia_{leg}'].head).copy() for leg in LEGS}
REST_TARSUS = {leg: rig.pose.bones[f'Tarsus_{leg}'].matrix.to_quaternion() for leg in LEGS}
# symmetric footholds: mean of each mirrored pair (x mirrored)
for i in range(1, 5):
    l, r = REST_FOOT[f'L{i}'], REST_FOOT[f'R{i}']
    m = Vector(((l.x - r.x) / 2, (l.y + r.y) / 2, 0.0))
    REST_FOOT[f'L{i}'] = Vector((m.x, m.y, 0.02)); REST_FOOT[f'R{i}'] = Vector((-m.x, m.y, 0.02))   # all on the floor (R4 rested 14 cm up)


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def side(leg):
    return 1.0 if leg[0] == 'L' else -1.0


def body(lift=0.0, forward=0.0, pitch=0.0, roll=0.0, yaw=0.0, abdomen=0.0):
    """Root (Thorax) offset and rotation; positive pitch raises the front."""
    root = rig.pose.bones['Thorax']
    root.matrix = Matrix.Translation(Vector((0, -forward, lift))) @ root.matrix
    bpy.context.view_layer.update()
    if roll:
        P.rotate_world(rig, 'Thorax', Y, roll)
    if pitch:
        P.rotate_world(rig, 'Thorax', X, -pitch)
    if yaw:
        P.rotate_world(rig, 'Thorax', Z, yaw)
    if abdomen:
        P.rotate_world(rig, 'Abdomen', X, abdomen)


def fangs(spread):
    for s, sgn in (('L', 1), ('R', -1)):
        P.rotate_world(rig, f'Fang_{s}', Y, -spread * sgn)


def place_foot(leg, foot):
    """IK the leg so the foot reaches `foot`; the tarsus keeps its rest world orientation."""
    ankle = Vector(foot) + (REST_ANKLE[leg] - REST_FOOT[leg])
    knee = REST_KNEE[leg]
    out = Vector((knee.x, knee.y, 0)).normalized()
    pole = knee + out * 0.15 + Z * 0.35
    P.two_bone_ik(rig, f'Femur_{leg}', f'Tibia_{leg}', ankle, pole)
    tarsus = rig.pose.bones[f'Tarsus_{leg}']
    tarsus.matrix = Matrix.LocRotScale(tarsus.head.copy(), REST_TARSUS[leg], Vector((1, 1, 1)))
    bpy.context.view_layer.update()


def curl_leg(leg, femur, tibia, tarsus):
    """Free (FK) leg: femur raised (+ = up), tibia and tarsus folded under (+ = curl toward the body)."""
    s = side(leg)
    for name, deg, axis_from in ((f'Femur_{leg}', femur, 'up'), (f'Tibia_{leg}', tibia, 'fold'),
                                 (f'Tarsus_{leg}', tarsus, 'fold')):
        b = rig.pose.bones[name]
        d = (b.tail - b.head).normalized()
        axis = d.cross(Z)
        if axis.length < 1e-3:
            axis = Vector((0, -s, 0))
        axis.normalize()
        P.rotate_world(rig, name, axis, deg if axis_from == 'up' else -deg)


# ---------------------------------------------------------------- floor
_dg = bpy.context.evaluated_depsgraph_get()


def lowest():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)[:, 2].min()


def floor_fit(ground=False):
    """Lift the spider out of the floor; with ground=True also lower it onto the floor (the corpse lies flat)."""
    low = lowest()
    if low < -0.004 or (ground and low > 0.002):
        root = rig.pose.bones['Thorax']
        root.matrix = Matrix.Translation(Vector((0, 0, -low))) @ root.matrix
        bpy.context.view_layer.update()


# ---------------------------------------------------------------- clips
def gait(t, T, stride, duty, lift):
    p = (t / T) % 1.0
    P.reset(rig)
    body(lift=0.008 * math.cos(4 * math.pi * p) + 0.012,   # +1.6 cm: the low abdomen grazed the floor roll=1.5 * math.sin(2 * math.pi * p),
         yaw=1.5 * math.sin(2 * math.pi * p), abdomen=2 * math.sin(4 * math.pi * p))
    s = stride * duty
    for leg in LEGS:
        q = (p + (0.0 if leg in GROUP_A else 0.5)) % 1.0
        if q < duty:
            dy = -s / 2 + s * (q / duty); dz = 0.0
        else:
            u = (q - duty) / (1 - duty)
            dy = s / 2 - s * ss(u); dz = lift * math.sin(math.pi * u)
        place_foot(leg, REST_FOOT[leg] + Vector((0, dy, dz)))


def standing(t):
    P.reset(rig)
    u = t / 2.0
    body(lift=0.004 * math.sin(2 * math.pi * u), roll=0.8 * math.sin(2 * math.pi * u * 0.5),
         abdomen=3 * math.sin(2 * math.pi * u))
    fangs(4 * max(0.0, math.sin(2 * math.pi * u * 2)))
    for leg in LEGS:
        place_foot(leg, REST_FOOT[leg])


def fidget(t):
    P.reset(rig)
    u = t / 1.0
    body(pitch=3 * math.sin(math.pi * u), abdomen=4 * math.sin(math.pi * u))
    fangs(10 * abs(math.sin(2 * math.pi * 2 * u)))
    for leg in LEGS:
        foot = REST_FOOT[leg].copy()
        if leg in ('L1', 'R1'):
            phase = u * 2 + (0.0 if leg == 'L1' else 0.5)
            foot += Vector((0, -0.02, 0.07 * max(0.0, math.sin(2 * math.pi * phase))))
        place_foot(leg, foot)


def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6))
            return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * u for k in set(a) | set(b)}
    return keys[-1][1]


def generic(k):
    """Keyed body pose; front legs (L1/R1) and the rest of the feet offset from their footholds."""
    P.reset(rig)
    body(lift=k.get('lift', 0.0), forward=k.get('forward', 0.0), pitch=k.get('pitch', 0.0), roll=k.get('roll', 0.0),
         abdomen=k.get('abdomen', 0.0))
    fangs(k.get('fangs', 0.0))
    splay = k.get('splay', 0.0)
    for leg in LEGS:
        foot = REST_FOOT[leg].copy()
        out = Vector((foot.x, foot.y, 0)).normalized()
        foot += out * splay
        if leg in ('L1', 'R1'):
            foot += Vector((side(leg) * k.get('front_out', 0.0), -k.get('front_fwd', 0.0), k.get('front_up', 0.0)))
        if leg in ('L2', 'R2'):
            foot += Vector((0, 0, k.get('second_up', 0.0)))
        place_foot(leg, foot)


ATTACK = [
    (0.00, {}),
    (0.32, {'lift': 0.10, 'pitch': 28, 'forward': -0.05, 'front_up': 0.40, 'front_out': 0.08, 'front_fwd': 0.08,
            'second_up': 0.12, 'fangs': 24, 'abdomen': -8}),
    (0.42, {'lift': 0.11, 'pitch': 30, 'forward': -0.05, 'front_up': 0.44, 'front_out': 0.10, 'front_fwd': 0.10,
            'second_up': 0.14, 'fangs': 26, 'abdomen': -8}),
    (IMPACT, {'lift': -0.02, 'pitch': -12, 'forward': 0.14, 'front_up': 0.02, 'front_fwd': 0.20, 'fangs': -8,
              'abdomen': 5}),
    (0.72, {'lift': -0.01, 'pitch': -8, 'forward': 0.10, 'front_fwd': 0.16, 'fangs': -4, 'abdomen': 3}),
    (1.00, {}),
]
HIT = [
    (0.00, {}),
    (0.14, {'lift': -0.04, 'forward': -0.05, 'pitch': 8, 'splay': 0.05, 'fangs': 14, 'abdomen': 8}),
    (0.45, {'lift': -0.03, 'forward': -0.04, 'pitch': 5, 'splay': 0.04, 'fangs': 10, 'abdomen': 6}),
    (0.75, {}),
]
DEATH = [  # rear with the front legs flailing, then collapse flat with the legs splayed and partly curled
    (0.00, dict(lift=0.0, pitch=0, femur=0, tibia=0, tarsus=0, fangs=0, front=0)),
    (0.30, dict(lift=0.10, pitch=26, femur=10, tibia=-5, tarsus=0, fangs=24, front=1)),
    (0.55, dict(lift=0.06, pitch=12, femur=18, tibia=10, tarsus=8, fangs=18, front=0.6)),
    (0.85, dict(lift=-0.12, pitch=-4, femur=-28, tibia=-42, tarsus=-14, fangs=8, front=0)),
    (1.20, dict(lift=-0.16, pitch=-3, femur=-40, tibia=-60, tarsus=-20, fangs=4, front=0)),
]


def death(t):
    k = keyed(DEATH, t)
    P.reset(rig)
    body(lift=k['lift'], pitch=k['pitch'])
    fangs(k['fangs'])
    for leg in LEGS:
        flail = k['front'] * (1.0 if leg[1] in '12' else 0.3)
        wob = 18 * flail * math.sin(2 * math.pi * (t * 4 + (0.0 if leg[0] == 'L' else 0.5) + int(leg[1]) * 0.2))
        curl_leg(leg, k['femur'] + 35 * flail + wob, k['tibia'] - 20 * flail, k['tarsus'])


CLIPS = {
    'Standing': (2.0, True, standing),
    'Walking': (1.0, True, lambda t: gait(t, 1.0, STRIDE_WALK, 0.55, 0.16)),
    'Running': (0.6, True, lambda t: gait(t, 0.6, STRIDE_RUN, 0.45, 0.20)),
    'Attack': (1.0, False, lambda t: generic(keyed(ATTACK, t))),
    'Hit': (0.75, False, lambda t: generic(keyed(HIT, t))),
    'Death': (1.2, False, death),
    'Fidget': (1.0, False, fidget),
}


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    n = int(round(seconds * FPS))
    rig.animation_data.action = None
    poses = []
    for f in range(n + 1):
        fn((f % n) / FPS if loop else f / FPS)
        if name in ('Attack', 'Hit', 'Death', 'Dead'):
            floor_fit(ground=name == 'Dead' or (name == 'Death' and f / FPS >= 0.8))
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, pose in enumerate(poses):
        for b in rig.pose.bones:
            q, loc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc
            b.keyframe_insert('rotation_quaternion', frame=f)
            b.keyframe_insert('location', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    return act


for name, (sec, loop, fn) in CLIPS.items():
    key_action(name, sec, loop, fn)
    print('CLIP', name, sec, flush=True)
key_action('Dead', 1.0, False, lambda t: death(1.2))
json.dump({'fps': FPS, 'walk_stride_m': STRIDE_WALK, 'run_stride_m': STRIDE_RUN, 'attack_impact_s': IMPACT},
          open(os.path.join(HERE, 'work', 'clips.json'), 'w'))
P.reset(rig)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT))
print('SAVED', OUT)
