"""Procedural Treant clips (30 fps) after the native MM7 m480 actions (only these exist natively; walk/fidget reuse the
standing frame, shoot reuses attack, so no other clip is invented):
  Standing  4.0 s loop   the disguise (native m479sa0: no face): mouth closed, eyes sunk into the bark, slow wind
                         sway of the trunk and the six limb sectors (phase-shifted, larger toward the tips)
  Attack    1.125 s      native 18 x 62.5 ms (m479ab0..as0): the face wakes (eyes, mouth opens), wind-up leaning back
                         to its right with the right-hand limbs drawn back, then a whip-lash lean forward to its left
                         with every limb sweeping forward (chains lag: base, then middle, then tips); impact IMPACT;
                         recovers upright with the mouth open
  Hit       0.4375 s     native 7 x 62.5 ms (m479na0..ng0): eyes open, mouth gapes, recoil back, limbs shudder
  Death     0.9 s        native da0..dd0 (the tree bursts apart, corpse = toothed stump m479xa0): shudder, the six
                         limb sectors fly outward and shrink to splinters, the spire and upper trunk collapse, the
                         trunk between z 1.2 and 1.9 flattens onto a stump at about 1.3 m with the mouth bared
  Dead      1.0 s        last Death pose held
Eyes: bones Eye_L / Eye_R (added by eyes_add.py) scale 0.05 (sunk) .. 1 (open); teeth rows TeethU / TeethL
(teeth_bones.py) scale 0.35 with the mouth closed, so the corner teeth draw in behind the lips.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; MESH = bpy.data.objects['Body']
bpy.context.scene.render.fps = 30; bpy.context.scene.render.fps_base = 1
FPS = 30; X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
IMPACT = 0.6875                                       # native frame ak0 (11th of 18 at 62.5 ms)
NS = 6
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
DIR = {}
for k in range(NS):
    h = REST[f'Limb{k}_1'].translation; d = Vector((h.x, h.y + 0.06, 0)).normalized(); DIR[k] = d
EYES = [n for n in ('Eye_L', 'Eye_R') if n in rig.pose.bones]


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def set_scale(name, s):
    b = rig.pose.bones[name]
    b.scale = Vector(s) if hasattr(s, '__len__') else Vector((s, s, s)); bpy.context.view_layer.update()


def move(name, d):
    b = rig.pose.bones[name]
    b.matrix = Matrix.Translation(d) @ b.matrix; bpy.context.view_layer.update()


TRUNK_SHARE = (('Trunk1', 0.12), ('Trunk2', 0.3), ('Trunk3', 0.33), ('Spire', 0.25))


def pose(pm, t=0.0):
    """pm: lean (deg forward), side (deg toward +X), twist (deg about Z), mouth (0 closed, 1 modelled, >1 wide),
    eyes (0..1), lift (deg, all limbs), pitch (deg, limbs tip forward), sweep (deg, limbs swing toward the front),
    lift_<k> per sector, wave (deg) + wave_f (Hz): per-limb oscillation, lag (0..1 whip delay along the chains),
    sway (0..1): the standing wind loop at clip time t"""
    P.reset(rig)
    sw = pm.get('sway', 0.0)
    lean = pm.get('lean', 0.0) + sw * 0.9 * math.sin(2 * math.pi * t / 4.0)
    side = pm.get('side', 0.0) + sw * 1.2 * math.sin(2 * math.pi * (t / 4.0 + 0.3))
    twist = pm.get('twist', 0.0) + sw * 1.0 * math.sin(2 * math.pi * (t / 2.0 + 0.1))
    for n, s in TRUNK_SHARE:
        rot(n, Z, twist * s); rot(n, X, lean * s); rot(n, Y, side * s)
    # limbs: base pivots, tips lag
    for k in range(NS):
        d = DIR[k]; lift_axis = d.cross(Z).normalized()
        fwd_sign = -1.0 if d.x > 0 else 1.0                  # rotation about Z that turns the limb toward -Y
        if abs(d.x) < 0.2:
            fwd_sign = 0.0
        for i, gain in ((1, 0.5), (2, 0.3), (3, 0.2)):
            n = f'Limb{k}_{i}'
            lag = pm.get('lag', 0.0) * (i - 1)
            lift = pm.get('lift', 0.0) + pm.get(f'lift_{k}', 0.0)
            wv = pm.get('wave', 0.0) * math.sin(2 * math.pi * (pm.get('wave_f', 0.0) * t - 0.15 * i - k / NS))
            wv += sw * (1.5 + 1.2 * i) * math.sin(2 * math.pi * (t / 4.0 - 0.08 * i + k / NS))
            wz = sw * (1.0 + 0.8 * i) * math.sin(2 * math.pi * (t / 2.0 - 0.1 * i + 0.37 * k))
            rot(n, lift_axis, (lift * (1 - lag)) * gain + wv)
            rot(n, Z, fwd_sign * pm.get('sweep', 0.0) * gain * (1 - lag) + wz)
            rot(n, X, pm.get('pitch', 0.0) * gain * (1 - lag))
    m = pm.get('mouth', 0.0)
    jz = 0.22 * (1 - m) if m <= 1 else -0.14 * (m - 1)
    uz = -0.10 * (1 - m) if m <= 1 else 0.04 * (m - 1)
    move('Jaw', Vector((0, -0.02 * max(0.0, 1 - m), jz)))
    move('UpperLip', Vector((0, 0, uz)))
    ts = 0.35 + 0.65 * min(1.0, max(0.0, (m - 0.15) / 0.6))            # teeth draw in behind the closed lips
    for n in ('TeethU', 'TeethL'):
        if n in rig.pose.bones:
            set_scale(n, ts)
    e = max(0.05, min(1.0, pm.get('eyes', 0.0)))
    for n in EYES:
        set_scale(n, e)


def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6)); o = {}
            for k in set(a) | set(b):
                o[k] = a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * u
            return o
    return dict(keys[-1][1])


AWAKE = {'mouth': 1.0, 'eyes': 1.0}
ATTACK = [
    (0.000, {'sway': 1.0}),
    (0.250, dict(AWAKE, mouth=1.2, lean=-3, lift=5)),                                       # ab-ae: wakes
    (0.500, dict(AWAKE, mouth=1.4, lean=-14, side=-16, twist=18, lift=12, lift_4=16, lift_5=20,
                 sweep=-18, pitch=-14)),                                                   # af-ai: wind-up
    (IMPACT, dict(AWAKE, mouth=1.6, lean=24, side=20, twist=-22, lift=-8, sweep=30, pitch=34, lag=0.35)),  # aj-ak
    (0.820, dict(AWAKE, mouth=1.5, lean=18, side=14, twist=-14, lift=-5, sweep=20, pitch=24, lag=-0.25)),
    (1.125, dict(AWAKE, mouth=1.3)),                                                         # an-as
]
HIT = [
    (0.000, {'sway': 1.0}),
    (0.090, dict(AWAKE, mouth=1.6, lean=-8, side=3, lift=6, wave=5, wave_f=7)),
    (0.250, dict(AWAKE, mouth=1.5, lean=-4, side=1, lift=3, wave=4, wave_f=7)),
    (0.4375, dict(AWAKE, mouth=1.3, wave=1, wave_f=7)),
]


def standing(t):
    pose({'sway': 1.0}, t)


def death(t):
    pm = keyed([(0.0, dict(AWAKE, mouth=1.4)), (0.12, dict(AWAKE, mouth=1.7, lean=-4, side=3, wave=6, wave_f=9)),
                (0.9, dict(mouth=1.6, eyes=0.0))], t)
    pose(pm, t)
    if t > 0.10:                                                             # upper trunk collapses onto the stump
        u = ss((t - 0.12) / 0.45)
        rot('Spire', Vector((1, 0.4, 0)).normalized(), -50 * u)
        set_scale('Spire', 1 - 0.99 * u)
        set_scale('Trunk3', 1 - 0.99 * ss((t - 0.2) / 0.35))
        b = rig.pose.bones['Trunk2']; b.scale = Vector((1.0, 1 - 0.82 * ss((t - 0.25) / 0.4), 1.0))
        bpy.context.view_layer.update()
        for k in range(NS):                         # limbs snap off outward, tumble and splinter (shrink to 0.5 %)
            v = ss((t - 0.10) / 0.35); d = DIR[k]       # short flight: junction strands blend limb and trunk
            name = f'Limb{k}_1'; b = rig.pose.bones[name]
            M0 = REST[name]
            spin = Quaternion(d.cross(Z).normalized(), math.radians(-60 * v)) @ Quaternion(Z, math.radians(30 * v * (1 if k % 2 else -1)))
            loc = M0.translation + d * (0.45 * v) + Vector((0, 0, 0.25 * v - 0.55 * v * v))
            s = max(0.005, 1 - 0.995 * ss((t - 0.12) / 0.30))
            home = rig.pose.bones['Trunk3'].head                 # splinters end inside the collapsed stump top, so
            loc = loc.lerp(home, ss((t - 0.30) / 0.25))          # strands blending limb and trunk do not web out
            b.matrix = Matrix.LocRotScale(loc, spin @ M0.to_quaternion(), Vector((s, s, s)))
            bpy.context.view_layer.update()
            rot(f'Limb{k}_2', d.cross(Z).normalized(), -25 * v); rot(f'Limb{k}_3', d.cross(Z).normalized(), -30 * v)


CLIPS = {
    'Standing': (4.0, True, standing),
    'Attack': (1.125, False, lambda t: pose(keyed(ATTACK, t), t)),
    'Hit': (0.4375, False, lambda t: pose(keyed(HIT, t), t)),
    'Death': (0.9, False, death),
}


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = None
    n = int(round(seconds * FPS)); poses = []
    for f in range(n + 1):
        t = (f % n) / FPS if loop else min(f / FPS, seconds)
        fn(t)
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, ps in enumerate(poses):
        for b in rig.pose.bones:
            q, loc, sc = ps[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q; b.rotation_quaternion = q; b.location = loc; b.scale = sc
            b.keyframe_insert('rotation_quaternion', frame=f); b.keyframe_insert('location', frame=f)
            b.keyframe_insert('scale', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    return act


for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
for name, (sec, loop, fn) in CLIPS.items():
    key_action(name, sec, loop, fn)
    print('CLIP', name, sec, flush=True)
key_action('Dead', 1.0, False, lambda t: death(0.9))
json.dump({'fps': FPS, 'attack_impact_s': IMPACT, 'durations': {k: v[0] for k, v in CLIPS.items()}},
          open(os.path.join(HERE, 'work', 'clips.json'), 'w'), indent=1)
P.reset(rig)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print('SAVED', out)
