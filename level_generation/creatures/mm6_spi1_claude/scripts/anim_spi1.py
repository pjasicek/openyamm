"""Procedural clips for the spider (24 fps), following the native MM6 spider actions (spi1 frames).

Legs: two-bone IK (Femur + Tibia) places each ankle so the tarsus keeps its rest direction and the foot lands on its
foothold; the knee pole is above and outside the knee, so knees stay high like the sprite's arched legs.
  Standing  2.0 s loop   slow breathing of the abdomen, small body sway, fang twitch
  Walking   0.75 s loop  alternating tetrapod gait (L1 R2 L3 R4 / R1 L2 R3 L4), native walk length
  Running   0.5 s loop   same gait, longer stride, lower duty
  Attack    0.75 s       rear up on the back legs with front legs raised and fangs spread, then lunge down and bite
  Hit       0.75 s       jolt back and down, legs splay, recover
  Death     1.0 s        rear, roll over onto the back, legs curl up (native death); Dead = last frame held
  Fidget    1.0 s        front legs tap and fangs work
Reads work/rig_v1.blend (or the UV-mapped work/anim_v1.blend when it exists), writes work/anim_v1.blend."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Spider_Rig']; mesh = bpy.data.objects['Spider']
FPS = 24
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
    body(lift=0.008 * math.cos(4 * math.pi * p) - 0.004, roll=1.5 * math.sin(2 * math.pi * p),
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
    (0.25, {'lift': 0.06, 'pitch': 24, 'forward': -0.03, 'front_up': 0.26, 'front_out': 0.05, 'front_fwd': 0.06,
            'second_up': 0.08, 'fangs': 22, 'abdomen': -6}),
    (0.42, {'lift': -0.01, 'pitch': -10, 'forward': 0.08, 'front_up': 0.02, 'front_fwd': 0.12, 'fangs': -6,
            'abdomen': 4}),
    (0.55, {'lift': -0.005, 'pitch': -6, 'forward': 0.06, 'front_fwd': 0.10, 'fangs': -4, 'abdomen': 3}),
    (0.75, {}),
]
HIT = [
    (0.00, {}),
    (0.14, {'lift': -0.04, 'forward': -0.05, 'pitch': 8, 'splay': 0.05, 'fangs': 14, 'abdomen': 8}),
    (0.45, {'lift': -0.03, 'forward': -0.04, 'pitch': 5, 'splay': 0.04, 'fangs': 10, 'abdomen': 6}),
    (0.75, {}),
]
DEATH = [  # (time, body roll/lift/pitch, leg curl femur/tibia/tarsus)
    (0.00, dict(lift=0.0, pitch=0, roll=0, femur=0, tibia=0, tarsus=0, fangs=0)),
    (0.25, dict(lift=0.10, pitch=30, roll=10, femur=25, tibia=-10, tarsus=0, fangs=24)),
    (0.60, dict(lift=0.22, pitch=10, roll=120, femur=35, tibia=40, tarsus=30, fangs=14)),
    (0.85, dict(lift=0.0, pitch=0, roll=178, femur=45, tibia=75, tarsus=60, fangs=6)),
    (1.00, dict(lift=0.0, pitch=0, roll=180, femur=50, tibia=85, tarsus=70, fangs=4)),
]


def death(t):
    k = keyed(DEATH, t)
    P.reset(rig)
    for leg in LEGS:
        curl_leg(leg, k['femur'], k['tibia'], k['tarsus'])
    fangs(k['fangs'])
    body(lift=k['lift'], pitch=k['pitch'], roll=k['roll'])


CLIPS = {
    'Standing': (2.0, True, standing),
    'Walking': (18 / FPS, True, lambda t: gait(t, 18 / FPS, 0.26, 0.55, 0.07)),
    'Running': (12 / FPS, True, lambda t: gait(t, 12 / FPS, 0.40, 0.45, 0.09)),
    'Attack': (0.75, False, lambda t: generic(keyed(ATTACK, t))),
    'Hit': (0.75, False, lambda t: generic(keyed(HIT, t))),
    'Death': (1.0, False, death),
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
            floor_fit(ground=name == 'Dead' or (name == 'Death' and f / FPS >= 0.85))
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    prev = {}
    for f, pose in enumerate(poses):
        for b in rig.pose.bones:
            q, loc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc
            b.keyframe_insert('rotation_quaternion', frame=f + 1)
            b.keyframe_insert('location', frame=f + 1)
    rig.animation_data.action = None
    return act


for name, (sec, loop, fn) in CLIPS.items():
    key_action(name, sec, loop, fn)
    print('CLIP', name, sec, flush=True)
key_action('Dead', 1.0, False, lambda t: death(1.0))
json.dump({'fps': FPS, 'walk_stride_m': 0.26, 'run_stride_m': 0.40},
          open(os.path.join(HERE, 'work', 'anim_info.json'), 'w'))
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED anim_v1.blend')
