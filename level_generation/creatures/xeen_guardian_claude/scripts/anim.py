"""Procedural clips for the Guardian (30 fps), after the Clouds of Xeen frames (sprites/xeen/083.mon, 083.att) and the
Flying Eye (mm6_bh_claude/scripts/anim_bh.py). A floating chrome skull: no body, no floor contact while alive.
  Standing      2.0 s loop   hover bob, slow sway, the jaw chatters (native idle: jaw open/closed every few frames)
  Walking       1.0 s loop   flying forward: nose-down lean, faster bob, jaw nearly shut
  Running       0.8 s loop   stronger lean and bob (whole keys at 30 fps)
  Attack        1.0 s        melee: draws back with the jaw gaping and the eyes flaring, lunges and bites shut:
                             impact (the bite) at IMPACT_MELEE
  AttackRanged  1.0 s        rises a little, the jaw gapes, the eyes and the gem flare (native att 0-2: eyes flare,
                             lightning); release from Socket_Gem at IMPACT_RANGED, then the gem and eyes fade back
  Hit           0.5 s        knocked back with a small spin, the jaw snaps open
  Death         1.5 s        shudders with the jaw gaping and the eyes going out, drops and rolls onto its left side,
                             a short bounce; the lowest point lands on the floor
  Dead          1.0 s        Death's last pose
  Fidget        2.0 s        a jaw-chattering cackle while the skull turns side to side
Flyer floor rule (CLAUDE_QUADRUPED_PLAYBOOK.md, Flyers): one uniform lift for every living clip so that their lowest
point over all frames meets the floor (no z_offset); the death eases it out and grounds the corpse exactly.
Reads work/anim_base.blend (the UV master), writes work/anim_v1.blend and work/anim_info.json."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
rig = bpy.data.objects['Guardian_Rig']; mesh = bpy.data.objects['Skull']
FPS = 30
IMPACT_MELEE, IMPACT_RANGED = 0.45, 0.50
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
P.reset(rig)
_dg = bpy.context.evaluated_depsgraph_get()


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def pose(lift=0.0, forward=0.0, side=0.0, pitch=0.0, yaw=0.0, roll=0.0, jaw=0.0, eyes=1.0, gem=1.0):
    """pitch + = nose down, yaw + = turn to its left, roll + = left side down (degrees); jaw + = open beyond the
    modelled opening, - = closed (about -7.5 brings the tooth rows together: 0.1-0.3 cm apart); eyes, gem = scale of the eye cores and the gem."""
    P.reset(rig)
    if jaw:
        P.rotate_world(rig, 'Jaw', X, jaw)
    for n in ('EyeL', 'EyeR'):
        rig.pose.bones[n].scale = (eyes, eyes, eyes)
    rig.pose.bones['Gem'].scale = (gem, gem, gem)
    root = rig.pose.bones['Body']
    root.matrix = Matrix.Translation(Vector((side, -forward, lift))) @ root.matrix
    bpy.context.view_layer.update()
    if yaw:
        P.rotate_world(rig, 'Body', Z, yaw)
    if pitch:
        P.rotate_world(rig, 'Body', X, pitch)
    if roll:
        P.rotate_world(rig, 'Body', Y, roll)


def lowest():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return float(co.reshape(-1, 3)[:, 2].min())


def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6))
            return {k: a.get(k, D.get(k, 0.0)) + (b.get(k, D.get(k, 0.0)) - a.get(k, D.get(k, 0.0))) * u
                    for k in set(a) | set(b)}
    return dict(keys[-1][1])


D = {'eyes': 1.0, 'gem': 1.0}


def chatter(t, rate, amp, base):
    """Jaw chatter: quick shut-open snaps (native idle frames alternate shut and open)."""
    s = math.sin(2 * math.pi * rate * t)
    return base + amp * (0.5 + 0.5 * math.copysign(abs(s) ** 0.6, s))


def hover(t, period, lean, bob, jaw_base, jaw_amp, chatter_rate):
    w = 2 * math.pi * t / period
    return dict(lift=bob * math.sin(w), pitch=lean + 2.0 * math.sin(w + 0.6), roll=1.5 * math.sin(w * 0.5),
                yaw=3.0 * math.sin(w * 0.5 + 1.0), jaw=chatter(t, chatter_rate, jaw_amp, jaw_base),
                eyes=1.0 + 0.08 * math.sin(w))


ATTACK = [
    (0.00, {}),
    (0.25, {'forward': -0.07, 'lift': 0.03, 'pitch': -12, 'jaw': 24, 'eyes': 1.35}),
    (0.38, {'forward': 0.10, 'lift': -0.01, 'pitch': 8, 'jaw': 26, 'eyes': 1.35}),
    (IMPACT_MELEE, {'forward': 0.13, 'lift': -0.015, 'pitch': 10, 'jaw': -7.5, 'eyes': 1.2}),
    (0.62, {'forward': 0.08, 'pitch': 5, 'jaw': 4}),
    (1.00, {}),
]
RANGED = [
    (0.00, {}),
    (0.22, {'lift': 0.05, 'forward': -0.04, 'pitch': -8, 'jaw': 18, 'eyes': 1.7, 'gem': 1.25}),
    (0.42, {'lift': 0.06, 'forward': -0.02, 'pitch': -4, 'jaw': 26, 'eyes': 2.0, 'gem': 1.45}),
    (IMPACT_RANGED, {'lift': 0.055, 'forward': 0.02, 'pitch': 2, 'jaw': 28, 'eyes': 2.1, 'gem': 1.5}),
    (0.62, {'lift': 0.04, 'forward': 0.01, 'pitch': 1, 'jaw': 14, 'eyes': 1.3, 'gem': 1.15}),
    (1.00, {}),
]
HIT = [
    (0.00, {}),
    (0.10, {'forward': -0.09, 'lift': 0.03, 'pitch': -14, 'yaw': 18, 'roll': -8, 'jaw': 16, 'eyes': 0.8}),
    (0.30, {'forward': -0.05, 'lift': 0.015, 'pitch': -6, 'yaw': 9, 'roll': -4, 'jaw': 6}),
    (0.50, {}),
]
DEATH = [
    (0.00, {}),
    (0.10, {'yaw': 8, 'roll': 6, 'jaw': 24, 'pitch': -10, 'lift': 0.03, 'eyes': 1.4}),
    (0.20, {'yaw': -8, 'roll': -6, 'jaw': 28, 'pitch': -12, 'lift': 0.03, 'eyes': 1.1}),
    (0.32, {'yaw': 6, 'roll': 5, 'jaw': 28, 'pitch': -8, 'lift': 0.02, 'eyes': 0.6}),
    (0.42, {'yaw': 2, 'roll': 3, 'jaw': 22, 'pitch': -4, 'lift': 0.0, 'eyes': 0.35, 'gem': 0.92, 'drop': 0.0}),
    (0.80, {'yaw': 10, 'roll': 70, 'pitch': 14, 'jaw': 10, 'eyes': 0.3, 'gem': 0.92, 'drop': 1.0}),
    (0.95, {'yaw': 11, 'roll': 84, 'pitch': 10, 'jaw': 6, 'eyes': 0.3, 'gem': 0.92, 'drop': 1.0, 'bounce': 1.0}),
    (1.15, {'yaw': 12, 'roll': 90, 'pitch': 8, 'jaw': 8, 'eyes': 0.3, 'gem': 0.92, 'drop': 1.0}),
    (1.50, {'yaw': 12, 'roll': 90, 'pitch': 8, 'jaw': 8, 'eyes': 0.3, 'gem': 0.92, 'drop': 1.0}),
]


def fidget(t):
    u = t / 2.0
    look = math.sin(2 * math.pi * u)
    env = math.sin(math.pi * u) ** 2
    return dict(yaw=16 * look, roll=-3 * look, pitch=-4 * env + 1.5 * math.sin(4 * math.pi * u),
                jaw=chatter(t, 5.0, 12 * env + 4, -7.5), lift=0.012 * math.sin(2 * math.pi * u),
                eyes=1.0 + 0.25 * env)


LIVING = {
    'Standing': (2.0, True, lambda t: hover(t, 2.0, 0.0, 0.020, -7.5, 9, 1.5)),
    'Walking': (1.0, True, lambda t: hover(t, 1.0, 8.0, 0.025, -7.5, 4, 2.0)),
    'Running': (0.8, True, lambda t: hover(t, 0.8, 14.0, 0.03, -7.5, 3, 2.5)),
    'Attack': (1.0, False, lambda t: keyed(ATTACK, t)),
    'AttackRanged': (1.0, False, lambda t: keyed(RANGED, t)),
    'Hit': (0.5, False, lambda t: keyed(HIT, t)),
    'Fidget': (2.0, False, fidget),
}


def frames(seconds, loop):
    n = int(round(seconds * FPS))
    return [(f % n) / FPS if loop else f / FPS for f in range(n + 1)]


# pass 1: the lowest point over every living clip -> one uniform lift
low = {}
for name, (sec, loop, fn) in LIVING.items():
    m = 1e9
    for t in frames(sec, loop):
        pose(**fn(t)); m = min(m, lowest())
    low[name] = m
HOVER = -min(low.values())
print('LOWEST per clip (m, before lift)', {k: round(v, 4) for k, v in low.items()}, 'HOVER lift', round(HOVER, 4))


def living(fn):
    def f(t):
        p = fn(t); p['lift'] = p.get('lift', 0.0) + HOVER; pose(**p)
    return f


def death(t):
    k = keyed(DEATH, t)
    drop = k.pop('drop', 0.0); bounce = k.pop('bounce', 0.0)
    k['lift'] = k.get('lift', 0.0) + HOVER * (1 - ss(min(1.0, t / 0.42)))
    pose(**k)
    if drop > 0:
        lo = lowest()
        target = 0.03 * bounce
        root = rig.pose.bones['Body']
        root.matrix = Matrix.Translation(Vector((0, 0, (target - lo) * drop))) @ root.matrix
        bpy.context.view_layer.update()
    lo = lowest()                     # floor rule: the rolling skull never cuts the floor while it falls
    if lo < 0:
        root = rig.pose.bones['Body']
        root.matrix = Matrix.Translation(Vector((0, 0, -lo))) @ root.matrix
        bpy.context.view_layer.update()


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses = []
    for t in frames(seconds, loop):
        fn(t)
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


report = {}
for name, (sec, loop, fn) in LIVING.items():
    key_action(name, sec, loop, living(fn))
    report[name] = sec
    print('CLIP', name, sec, flush=True)
key_action('Death', 1.5, False, death)
dead_low = lowest()
key_action('Dead', 1.0, False, lambda t: death(1.5))
print('CLIP Death 1.5 Dead 1.0 corpse lowest', round(dead_low, 5))
json.dump({'fps': FPS, 'hover_lift_m': HOVER, 'impact_melee': IMPACT_MELEE, 'impact_ranged': IMPACT_RANGED,
           'lowest_before_lift': low, 'clips': report}, open(os.path.join(HERE, 'work', 'anim_info.json'), 'w'),
          indent=1)
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED anim_v1.blend')
