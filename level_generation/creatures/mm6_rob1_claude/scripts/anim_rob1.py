"""Procedural clips for the Patrol Unit (24 fps), following the native MM6 robot actions (rob1 frames).

Every part is rigid, so each frame is a set of parameters turned into one world transform per bone.
The robot hovers HOVER above the actor origin (native frames float about a quarter of the figure height above the
anchor; the full height stays inside the descriptor collision height), with a slow bob.
  Standing  1.5 s loop   bob, eye sweeps along the belt, sensor head scans
  Walking   0.75 s loop  leans into travel, faster bob, eye sweep (native: the walk is the standing loop)
  Attack    0.75 s       sensor aims, body draws back, shot at 0.4 s: recoil of the sensor head and body, recover
  Hit       0.75 s       knocked back and up, pitched back and rolled, eye and sensor whip, damped wobble
  Death     1.0 s        shudder with the eye spinning, then bursts: the rings and sensor head fly off, the core tumbles;
                         all shrink
                         to nothing inside the explosion (native: fireball, no corpse); Dead = Death end, held
  Fidget    1.5 s        sensor head turns to look aside and back; eye shifts the other way
Reads work/rig_v1.blend (or the UV-mapped work/anim_v1.blend when it exists), writes work/anim_v1.blend."""
import bpy, os, sys, math, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Robot_Rig']
FPS = 24
HOVER = 0.25
STRIDE = 0.9
# 1.0 since sensor_rebuild.py builds the sensor head at the native proportions (the Meshy one needed 1.4).
SENSOR_SCALE = 1.0
ORDER = ['Root', 'Body', 'CapTop', 'CapBottom', 'RingTop', 'RingBottom', 'Eye', 'Sensor']
REST = {b.name: b.bone.matrix_local.copy() for b in rig.pose.bones}
CENTRE = REST['Body'].translation.copy()
POST = REST['Sensor'].translation.copy()
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def keyed(keys, t):
    """Smoothstep between parameter dicts at key times; missing values are 0."""
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6))
            return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * u for k in set(a) | set(b)}
    return dict(keys[-1][1])


def about(pivot, axis, degrees):
    return (Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(degrees), 4, axis)
            @ Matrix.Translation(-pivot))


def scaled(pivot, s):
    return Matrix.Translation(pivot) @ Matrix.Scale(max(s, 1e-3), 4) @ Matrix.Translation(-pivot)


def pose(p):
    """p: hover (m, added to HOVER), fwd (m toward -Y), side (m toward +X), pitch (deg, top toward -Y), roll (deg, top
    toward +X), yaw (deg, front toward +X), eye (deg along the belt, + = robot's left), sensor_yaw, sensor_pitch
    (+ = nozzle up), sensor_lift (m), and for the burst: top/bottom (cap separation, m), ring_top/ring_bottom
    (ring separation, m). The core halves stay together in every clip (the faces
    across the equator would stretch), tilt (deg, ring tumble), fly (sensor head flight, m), shrink (0..1 scale loss)."""
    g = lambda k: p.get(k, 0.0)
    root = Matrix.Translation(Vector((g('side'), -g('fwd'), HOVER + g('hover'))))
    body = (root @ about(CENTRE, Vector((0, 0, 1)), g('yaw')) @ about(CENTRE, Vector((1, 0, 0)), g('pitch'))
            @ about(CENTRE, Vector((0, 1, 0)), -g('roll')))
    s = 1.0 - g('shrink')
    T = {'Root': root, 'Body': body}
    T['CapTop'] = body @ Matrix.Translation(Vector((0, 0, g('top')))) @ about(CENTRE, Vector((1, 0, 0)), -g('tilt') * 0.5) \
        @ scaled(CENTRE, s)
    T['CapBottom'] = body @ Matrix.Translation(Vector((0, 0, -g('bottom')))) @ about(CENTRE, Vector((0, 1, 0)), g('tilt') * 0.4) \
        @ scaled(CENTRE, s)
    T['RingTop'] = body @ Matrix.Translation(Vector((0.4 * g('ring_top'), 0, g('ring_top')))) \
        @ about(CENTRE, Vector((1, 1, 0)).normalized(), g('tilt')) @ scaled(CENTRE + Vector((0, 0, 0.1)), s)
    T['RingBottom'] = body @ Matrix.Translation(Vector((-0.4 * g('ring_bottom'), 0.2 * g('ring_bottom'), -0.6 * g('ring_bottom')))) \
        @ about(CENTRE, Vector((1, -1, 0)).normalized(), -g('tilt')) @ scaled(CENTRE - Vector((0, 0, 0.1)), s)
    T['Eye'] = T['CapTop'] @ about(CENTRE, Vector((0, 0, 1)), g('eye'))
    T['Sensor'] = (T['CapTop'] @ Matrix.Translation(Vector((0, 0.3 * g('fly'), g('sensor_lift') + g('fly'))))
                   @ about(POST, Vector((0, 0, 1)), g('sensor_yaw')) @ about(POST, Vector((1, 0, 0)), -g('sensor_pitch')) @ scaled(POST, SENSOR_SCALE * s))
    for name in ORDER:
        rig.pose.bones[name].matrix = T[name] @ REST[name]
        bpy.context.view_layer.update()


def standing(t):
    w = 2 * math.pi * t / 1.5
    pose({'hover': 0.012 * math.sin(w), 'pitch': 1.5 * math.sin(w + 1.0), 'roll': 1.2 * math.sin(w * 2 + 0.3),
          'eye': 24 * math.sin(w), 'sensor_yaw': 12 * math.sin(w - 0.8), 'sensor_pitch': 3 * math.sin(2 * w)})


def walking(t):
    w = 2 * math.pi * t / 0.75
    pose({'hover': 0.01 * math.sin(2 * w), 'pitch': 7 + 1.2 * math.sin(2 * w + 0.5), 'roll': 2.0 * math.sin(w),
          'eye': 18 * math.sin(w), 'sensor_yaw': 6 * math.sin(w + 1.2), 'sensor_pitch': -4})


def attack(t):
    k = keyed([(0.0, {}),
               (0.25, {'pitch': -6, 'fwd': -0.02, 'sensor_pitch': -6, 'hover': 0.01}),
               (0.38, {'pitch': -7, 'fwd': -0.025, 'sensor_pitch': -7, 'hover': 0.012}),
               (0.44, {'pitch': -13, 'fwd': -0.07, 'sensor_pitch': 14, 'sensor_lift': -0.012, 'hover': 0.02}),
               (0.58, {'pitch': -4, 'fwd': -0.03, 'sensor_pitch': 2, 'hover': 0.008}),
               (0.75, {})], t)
    pose(k)


def hit(t):
    k = keyed([(0.0, {}),
               (0.10, {'pitch': -18, 'roll': 8, 'fwd': -0.10, 'hover': 0.05, 'eye': 50, 'sensor_yaw': -35,
                       'sensor_pitch': 18}),
               (0.30, {'pitch': 8, 'roll': -5, 'fwd': -0.06, 'hover': 0.02, 'eye': -20, 'sensor_yaw': 20,
                       'sensor_pitch': -8}),
               (0.48, {'pitch': -4, 'roll': 2, 'fwd': -0.02, 'hover': 0.005, 'eye': 8, 'sensor_yaw': -6}),
               (0.75, {})], t)
    pose(k)


def death(t):
    if t < 0.38:
        u = t / 0.38
        jit = math.sin(t * 95) * (2 + 6 * u)
        pose({'pitch': -6 * u + jit * 0.6, 'roll': jit, 'yaw': 25 * u, 'hover': -0.04 * u + 0.006 * math.sin(t * 70),
              'eye': 360 * u * u * 1.5, 'sensor_yaw': 40 * math.sin(t * 30) * u, 'sensor_pitch': -20 * u})
        return
    u = (t - 0.38) / 0.62
    burst = 1 - (1 - min(u * 1.6, 1.0)) ** 3      # fast out
    pose({'pitch': -6 - 30 * burst, 'roll': 18 * burst, 'yaw': 25 + 40 * burst, 'hover': -0.04 - 0.05 * burst,
          'eye': 540, 'ring_top': 0.22 * burst, 'ring_bottom': 0.12 * burst,
          'tilt': 55 * burst, 'fly': 0.30 * burst, 'sensor_yaw': 160 * burst, 'sensor_pitch': -20 + 70 * burst,
          'shrink': ss((u - 0.15) / 0.65)})


def fidget(t):
    k = keyed([(0.0, {}),
               (0.30, {'sensor_yaw': 70, 'sensor_pitch': -6, 'eye': -15, 'yaw': 6}),
               (0.90, {'sensor_yaw': 75, 'sensor_pitch': -2, 'eye': -20, 'yaw': 8}),
               (1.25, {'sensor_yaw': -10, 'eye': 5}),
               (1.5, {})], t)
    pose(k)


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    n = int(round(seconds * FPS))
    poses = []
    for f in range(n + 1):
        fn((f % n) / FPS if loop else f / FPS)
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    prev = {}
    for f, frame in enumerate(poses):
        for b in rig.pose.bones:
            q, loc, sc = frame[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc; b.scale = sc
            b.keyframe_insert('rotation_quaternion', frame=f + 1)
            b.keyframe_insert('location', frame=f + 1)
            b.keyframe_insert('scale', frame=f + 1)
    rig.animation_data.action = None
    return act


CLIPS = {'Standing': (1.5, True, standing), 'Walking': (0.75, True, walking), 'Attack': (0.75, False, attack),
         'Hit': (0.75, False, hit), 'Death': (1.0, False, death), 'Fidget': (1.5, False, fidget)}
for name, (sec, loop, fn) in CLIPS.items():
    key_action(name, sec, loop, fn)
    print('CLIP', name, sec, flush=True)
key_action('Dead', 1.0, False, lambda t: death(1.0))
json.dump({'fps': FPS, 'walk_stride_m': STRIDE, 'hover_m': HOVER},
          open(os.path.join(HERE, 'work', 'anim_info.json'), 'w'))
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED anim_v1.blend')
