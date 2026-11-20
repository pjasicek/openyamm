"""Procedural clips for the Flying Eye (24 fps), following the native MM6 frames (bh*). It flies: no feet, no
ground contact while alive; the model's lowest point (tendril tips) rests at the actor origin.
  Standing  2.0 s loop   hover bob, slow tilt, tendrils sway with a lag, eye drifts
  Walking   1.0 s loop   flying forward: nose-down lean, faster bob, tendrils trail back
  Running   0.75 s loop  stronger lean and bob
  Attack    0.75 s       draw back, jaw opens wide with the eye staring, lunge, recover (native bhatk: wide mouth)
  Cast      0.75 s       rise, jaw gapes, eyeball pushes forward and trembles (the native attack's eye flare);
                         spellcasting tiers need a cast clip distinct from Attack
  Hit       0.625 s      twist and recoil, jaw snaps, recover (native bhwnc)
  Death     1.0 s        shudder with the jaw gaping, then drop and roll onto its side on the floor (the engine adds
                         disintegration particles, native bhdth shatters); Dead = last frame held
  Fidget    1.0 s        looks left and right, eye leading
Reads work/rig_v1.blend (or the UV-mapped work/anim_v1.blend), writes work/anim_v1.blend."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Eye_Rig']; mesh = bpy.data.objects['Eye']
FPS = 24
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
P.reset(rig)


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def pose(lift=0.0, forward=0.0, side=0.0, pitch=0.0, yaw=0.0, roll=0.0, jaw=0.0, eye_yaw=0.0, eye_pitch=0.0,
         tendril_pitch=0.0, tendril_roll=0.0):
    """pitch + = nose down, yaw + = turn to its left, roll + = left side down; jaw + = open (degrees)."""
    P.reset(rig)
    root = rig.pose.bones['Body']
    root.matrix = Matrix.Translation(Vector((side, -forward, lift))) @ root.matrix
    bpy.context.view_layer.update()
    if yaw:
        P.rotate_world(rig, 'Body', Z, yaw)
    if pitch:
        P.rotate_world(rig, 'Body', X, pitch)
    if roll:
        P.rotate_world(rig, 'Body', Y, roll)
    if jaw:
        P.rotate_local(rig, 'Jaw', 'X', -jaw)
    if eye_yaw:
        P.rotate_local(rig, 'EyeBall', 'Z', eye_yaw)
    if eye_pitch:
        P.rotate_local(rig, 'EyeBall', 'X', eye_pitch)
    if tendril_pitch:
        P.rotate_local(rig, 'Tendrils', 'X', tendril_pitch)
    if tendril_roll:
        P.rotate_local(rig, 'Tendrils', 'Z', tendril_roll)


_dg = bpy.context.evaluated_depsgraph_get()


def lowest():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)[:, 2].min()


def ground():
    low = lowest()
    root = rig.pose.bones['Body']
    root.matrix = Matrix.Translation(Vector((0, 0, -low))) @ root.matrix
    bpy.context.view_layer.update()


def hover(t, period, lean, bob, speed_sway):
    u = t / period
    w = 2 * math.pi * u
    pose(lift=bob * math.sin(w), pitch=lean + 2.5 * math.sin(w + 0.6), roll=2.0 * math.sin(w * 0.5),
         yaw=1.5 * math.sin(w * 0.5 + 1.0), jaw=3 + 2 * math.sin(w),
         eye_yaw=6 * math.sin(w * 0.5), eye_pitch=3 * math.sin(w * 0.5 + 1.2),
         tendril_pitch=-(lean * 1.2) - 8 * speed_sway * math.sin(w - 1.2),
         tendril_roll=6 * math.sin(w * 0.5 - 1.0))


def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6))
            return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * u for k in set(a) | set(b)}
    return keys[-1][1]


ATTACK = [
    (0.00, {'jaw': 3}),
    (0.22, {'forward': -0.08, 'lift': 0.03, 'pitch': -14, 'jaw': 26, 'tendril_pitch': 12, 'eye_pitch': -4}),
    (0.42, {'forward': 0.14, 'lift': -0.02, 'pitch': 12, 'jaw': 34, 'tendril_pitch': -18}),
    (0.55, {'forward': 0.10, 'pitch': 6, 'jaw': 10, 'tendril_pitch': -10}),
    (0.75, {'jaw': 3}),
]
CAST = [
    (0.00, {'jaw': 3}),
    (0.20, {'lift': 0.05, 'forward': -0.04, 'pitch': -10, 'jaw': 30, 'eye_pitch': -6, 'tendril_pitch': 10}),
    (0.32, {'lift': 0.06, 'forward': -0.02, 'pitch': -6, 'jaw': 36, 'eye_pitch': 4, 'tendril_pitch': 14, 'roll': 2}),
    (0.44, {'lift': 0.06, 'forward': 0.02, 'pitch': -4, 'jaw': 36, 'eye_pitch': -4, 'tendril_pitch': 14, 'roll': -2}),
    (0.56, {'lift': 0.04, 'pitch': 2, 'jaw': 20, 'tendril_pitch': 6}),
    (0.75, {'jaw': 3}),
]
HIT = [
    (0.00, {'jaw': 3}),
    (0.12, {'forward': -0.10, 'lift': 0.04, 'pitch': -16, 'yaw': 22, 'roll': -10, 'jaw': 18, 'tendril_pitch': 20,
            'tendril_roll': -14, 'eye_yaw': -10}),
    (0.38, {'forward': -0.06, 'lift': 0.02, 'pitch': -8, 'yaw': 12, 'roll': -5, 'jaw': 8, 'tendril_pitch': 10}),
    (0.625, {'jaw': 3}),
]
DEATH = [
    (0.00, {'jaw': 3}),
    (0.12, {'yaw': 8, 'roll': 6, 'jaw': 30, 'pitch': -10, 'lift': 0.04}),
    (0.22, {'yaw': -8, 'roll': -6, 'jaw': 34, 'pitch': -12, 'lift': 0.04}),
    (0.32, {'yaw': 6, 'roll': 5, 'jaw': 34, 'pitch': -8, 'lift': 0.02}),
    (0.70, {'roll': 70, 'pitch': 20, 'jaw': 20, 'tendril_pitch': 25, 'drop': 1.0}),
    (1.00, {'roll': 88, 'pitch': 8, 'jaw': 16, 'tendril_pitch': 30, 'drop': 1.0}),
]


def death(t):
    k = keyed(DEATH, t)
    drop = k.pop('drop', 0.0)
    pose(**k)
    if drop > 0:
        low = lowest()
        root = rig.pose.bones['Body']
        root.matrix = Matrix.Translation(Vector((0, 0, -low * drop))) @ root.matrix
        bpy.context.view_layer.update()
    if t >= 0.70:
        ground()


def fidget(t):
    u = t / 1.0
    look = math.sin(2 * math.pi * u)
    pose(yaw=14 * look, roll=-3 * look, pitch=2 * math.sin(math.pi * u), eye_yaw=16 * math.sin(2 * math.pi * u + 0.4),
         jaw=3 + 4 * math.sin(math.pi * u), tendril_roll=-8 * look, lift=0.01 * math.sin(2 * math.pi * u))


CLIPS = {
    'Standing': (2.0, True, lambda t: hover(t, 2.0, 0.0, 0.020, 0.6)),
    'Walking': (1.0, True, lambda t: hover(t, 1.0, 8.0, 0.025, 1.0)),
    'Running': (0.75, True, lambda t: hover(t, 0.75, 14.0, 0.03, 1.3)),
    'Attack': (0.75, False, lambda t: pose(**keyed(ATTACK, t))),
    'Cast': (0.75, False, lambda t: pose(**keyed(CAST, t))),
    'Hit': (0.625, False, lambda t: pose(**keyed(HIT, t))),
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
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    prev = {}
    for f, frame in enumerate(poses):
        for b in rig.pose.bones:
            q, loc = frame[b.name]
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
json.dump({'fps': FPS, 'fly_stride_m': 0.0}, open(os.path.join(HERE, 'work', 'anim_info.json'), 'w'))
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED anim_v1.blend')
