"""Procedural clips for the bloodsucker (24 fps), following the native MM6 bloodsucker actions.
  Fly     0.75 s loop  flap from the rest V (native a) down past level to curved low tips (c-d) and back (e-f);
                       elbow lags, fingers sweep back on the upstroke, body bobs, neck counters, tail waves
  Attack  0.75 s       rear back, lunge with the round maw gaping (native b-c: the Maw disc scales x5.5 while the
                       tube flares), snap and dip the head (d-e)
  Hit     0.75 s       jolt back with wings snapped up and mouth open, recover (no native hit frames)
  Death   1.0 s        rear up vertically with the maw open (native a-c), twist (d), fall and coil on the floor with
                       the wings laid flat (corpse); Dead = last pose held
  Fidget  1.0 s        glide on level wings with a bank and head turn (native fidget frames)
No hover lift: the model starts at the actor origin (see the bat README). Rotations about world axes through each
bone head (forward -Y, up +Z, left +X): +X pitches the front down, +Z turns toward +X; a wing lowers with
side * deg about Y. Writes work/anim_v1.blend.
"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Bld_Rig']; mesh = bpy.data.objects['Bld']
FPS = 24
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
SG = {'L': 1.0, 'R': -1.0}
V = Vector


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg)


def wing(side, down, elbow, fold, sweep=0.0):
    """down: whole wing lowered from the rest V (deg); elbow: outer wing bent further down; fold: fingers and hand
    swept back toward the tail; sweep: whole wing swung forward about the vertical."""
    s = SG[side]
    rot(f'UpperArm_{side}', Z, -s * sweep)
    rot(f'UpperArm_{side}', Y, s * down)
    rot(f'ForeArm_{side}', Y, s * elbow)
    if fold:
        rot(f'Hand_{side}', Z, s * fold * 0.6)
        for k in (1, 2):
            rot(f'Finger{k}a_{side}', Z, s * fold * (0.5 + 0.25 * k))


def body(d=V(), pitch=0.0, roll=0.0, neck=0.0, head=0.0, yaw=0.0, legs=0.0, tail_yaw=0.0, tail_pitch=0.0,
         tail_phase=None, mouth=1.0):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(d) @ root.matrix; bpy.context.view_layer.update()
    rot('Spine1', Y, roll); rot('Spine1', X, pitch)
    rot('Neck1', X, neck * 0.5); rot('Neck2', X, neck * 0.5); rot('Head', X, head)
    rot('Neck1', Z, yaw * 0.5); rot('Neck2', Z, yaw * 0.5)
    for i in range(1, 7):
        if tail_phase is None:
            rot(f'Tail{i}', Z, tail_yaw); rot(f'Tail{i}', X, tail_pitch)
        else:
            amp = 3.0 + 1.5 * i
            rot(f'Tail{i}', Z, amp * math.sin(tail_phase - 0.7 * i) + tail_yaw)
            rot(f'Tail{i}', X, 0.4 * amp * math.cos(tail_phase - 0.7 * i) + tail_pitch)
    for s in 'LR':
        rot(f'FrontLeg_{s}', X, -legs); rot(f'HindLeg_{s}', X, -legs)
    flare = 1.0 + (mouth - 1.0) * 0.3                # the tube flares a little; the maw disc carries the opening
    rig.pose.bones['Mouth'].scale = (flare, 1.0, flare)
    maw = 0.55 + (mouth - 1.0) * 1.1                # resting opening sits inside the tube; attack ~x5.5
    rig.pose.bones['Maw'].scale = (maw, 1.0, maw); bpy.context.view_layer.update()


def flap_params(p):
    c = math.cos(2 * math.pi * p)
    return {'down': 55 - 55 * c, 'elbow': 22 * max(0.0, math.sin(2 * math.pi * (p - 0.08))),
            'fold': 28 * max(0.0, -math.sin(2 * math.pi * p)) ** 1.3,
            'd': V((0, 0, 0.02 * math.sin(2 * math.pi * p))), 'pitch': 3 * math.sin(2 * math.pi * p),
            'neck': -4 * math.sin(2 * math.pi * p), 'tail_phase': 2 * math.pi * p, 'legs': 0.0, 'mouth': 1.0}


def pose(k):
    P.reset(rig)
    body(d=k.get('d', V()), pitch=k.get('pitch', 0.0), roll=k.get('roll', 0.0), neck=k.get('neck', 0.0),
         head=k.get('head', 0.0), yaw=k.get('yaw', 0.0), legs=k.get('legs', 0.0), tail_yaw=k.get('tail_yaw', 0.0),
         tail_pitch=k.get('tail_pitch', 0.0), tail_phase=k.get('tail_phase'), mouth=k.get('mouth', 1.0))
    for s in 'LR':
        bank = k.get('bank', 0.0) * SG[s]
        wing(s, k.get('down', 0.0) + bank, k.get('elbow', 0.0), k.get('fold', 0.0), k.get('sweep', 0.0))


def blend(a, b, u):
    out = {}
    for key in set(a) | set(b):
        va, vb = a.get(key), b.get(key)
        if key == 'tail_phase':
            out[key] = va if vb is None else vb if va is None else va + (vb - va) * u
            continue
        va = 1.0 if va is None and key == 'mouth' else va
        vb = 1.0 if vb is None and key == 'mouth' else vb
        if isinstance(va, Vector) or isinstance(vb, Vector):
            va = va if isinstance(va, Vector) else V(); vb = vb if isinstance(vb, Vector) else V()
            out[key] = va.lerp(vb, u)
        else:
            va = 0.0 if va is None else va; vb = 0.0 if vb is None else vb
            out[key] = va + (vb - va) * u
    return out


def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            return blend(a, b, ss((t - t0) / max(t1 - t0, 1e-6)))
    return keys[-1][1]


F0 = flap_params(0.0)
ATTACK = [
    (0.00, F0),
    (0.16, {'down': -8, 'd': V((0, 0.06, 0.03)), 'pitch': -14, 'neck': -18, 'head': -6, 'mouth': 1.2,
            'tail_pitch': 4, 'tail_phase': 0.6}),
    (0.30, {'down': 62, 'elbow': 10, 'sweep': 15, 'd': V((0, -0.08, -0.01)), 'pitch': 4, 'neck': 6, 'head': -4,
            'mouth': 4.8, 'tail_pitch': -3, 'tail_phase': 1.4}),
    (0.42, {'down': 58, 'elbow': 8, 'sweep': 12, 'd': V((0, -0.09, -0.01)), 'pitch': 4, 'neck': 6, 'head': -4,
            'mouth': 4.9, 'tail_phase': 2.0}),
    (0.56, {'down': 40, 'elbow': 6, 'd': V((0, -0.07, -0.03)), 'pitch': 16, 'neck': 18, 'head': 12, 'mouth': 1.4,
            'tail_phase': 2.8}),
    (0.75, dict(F0, tail_phase=2 * math.pi)),
]
HIT = [
    (0.00, F0),
    (0.12, {'down': -14, 'fold': 30, 'd': V((0, 0.08, 0.03)), 'pitch': -18, 'neck': -22, 'head': -10, 'mouth': 1.7,
            'tail_yaw': 6, 'tail_pitch': 6, 'legs': -15}),
    (0.40, {'down': 10, 'fold': 18, 'd': V((0, 0.05, 0.02)), 'pitch': -8, 'neck': -10, 'mouth': 1.3,
            'tail_yaw': -3}),
    (0.75, dict(F0, tail_phase=2 * math.pi)),
]
DEATH = [
    (0.00, F0),
    (0.25, {'down': 40, 'elbow': 20, 'd': V((0, 0.0, 0.06)), 'pitch': -62, 'neck': -22, 'head': -12, 'mouth': 2.3,
            'tail_yaw': 10, 'tail_pitch': -6, 'legs': 20}),
    (0.50, {'down': 75, 'elbow': 25, 'fold': 20, 'd': V((0, 0.02, 0.03)), 'pitch': -40, 'roll': 40, 'neck': -10,
            'mouth': 1.9, 'tail_yaw': 20, 'legs': 25}),
    (0.80, {'down': 95, 'elbow': 10, 'fold': 15, 'd': V((0, 0.03, 0.0)), 'neck': 12, 'head': 10, 'yaw': 20,
            'mouth': 1.3, 'tail_yaw': 22, 'legs': -10}),
    (1.00, {'down': 98, 'elbow': 10, 'fold': 18, 'd': V((0, 0.03, 0.0)), 'neck': 14, 'head': 12, 'yaw': 24,
            'mouth': 1.25, 'tail_yaw': 24, 'legs': -12}),
]
FIDGET = [
    (0.00, F0),
    (0.25, {'down': 58, 'elbow': -4, 'bank': 10, 'roll': -8, 'yaw': 16, 'neck': 4, 'tail_yaw': -3,
            'tail_phase': 1.2}),
    (0.60, {'down': 54, 'elbow': -2, 'bank': -8, 'roll': 6, 'yaw': -12, 'neck': 2, 'tail_yaw': 3, 'tail_phase': 3.4}),
    (1.00, dict(F0, tail_phase=2 * math.pi)),
]

_vg = {g.index: g.name for g in mesh.vertex_groups}
_dom = [_vg.get(max(v.groups, key=lambda g: g.weight).group, '') if v.groups else '' for v in mesh.data.vertices]
WING_BONES = ('UpperArm', 'ForeArm', 'Hand', 'Finger')
WING = {s: np.array([n.endswith('_' + s) and n.startswith(WING_BONES) for n in _dom]) for s in 'LR'}
TIPS = {s: np.array([n.endswith('_' + s) and n.startswith(WING_BONES[1:]) for n in _dom]) for s in 'LR'}
HAND = {s: np.array([n == f'Hand_{s}' for n in _dom]) for s in 'LR'}
TAIL = {i: np.array([n == f'Tail{i}' for n in _dom]) for i in range(1, 7)}
HEAD = np.array([n in ('Neck2', 'Head', 'Mouth') for n in _dom])
BODY = ~(WING['L'] | WING['R'])


def mesh_co():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


def fit(bone, axis, sign, mask, u, target, span=80.0):
    """Rotate bone about a world axis (sign * deg, + lowers) until the masked vertices just reach target height;
    apply u of the found angle."""
    def low_at(deg):
        rot(bone, axis, sign * deg)
        z = mesh_co()[mask, 2].min()
        rot(bone, axis, -sign * deg)
        return z
    lo, hi = -span, span
    if low_at(lo) < target:
        best = lo
    elif low_at(hi) > target:
        best = hi
    else:
        for _ in range(12):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if low_at(mid) > target else (lo, mid)
        best = lo
    rot(bone, axis, sign * best * u)


def flatten(side, u):
    """Twist the wing about its upper-arm axis so the membrane lies flattest (least height spread)."""
    b = rig.pose.bones[f'UpperArm_{side}']
    axis = ((rig.matrix_world @ b.tail) - (rig.matrix_world @ b.head)).normalized()
    def spread(deg):
        rot(f'UpperArm_{side}', axis, deg)
        z = np.std(mesh_co()[WING[side], 2])
        rot(f'UpperArm_{side}', axis, -deg)
        return z
    best = min(range(-90, 91, 15), key=spread)
    best = min((best + d for d in (-10, -5, 0, 5, 10)), key=spread)
    rot(f'UpperArm_{side}', axis, best * u)


def land(u):
    """Death: lower the body so its belly reaches the floor, then lay wings, head and tail on the floor (fitted
    relative to the belly, so the fall blends smoothly)."""
    low = mesh_co()[BODY, 2].min()
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(Vector((0, 0, -low * u))) @ root.matrix; bpy.context.view_layer.update()
    if u <= 0:
        return
    belly = mesh_co()[BODY, 2].min() + 0.01
    for side in 'LR':
        flatten(side, u)
        fit(f'UpperArm_{side}', Y, SG[side], TIPS[side], u, belly)
        fit(f'ForeArm_{side}', Y, SG[side], HAND[side], u, belly)
    fit('Neck1', X, 1.0, HEAD, u, belly - 0.005, 40.0)
    for i in range(1, 7):
        tail = np.zeros(len(BODY), bool)
        for j in range(i, 7):
            tail |= TAIL[j]
        fit(f'Tail{i}', X, -1.0, tail, u, belly - 0.005, 40.0)


def fly(t):
    pose(flap_params((t / 0.75) % 1.0))


CLIPS = {'Fly': (0.75, True, fly),
         'Attack': (0.75, False, lambda t: pose(keyed(ATTACK, t))),
         'Hit': (0.75, False, lambda t: pose(keyed(HIT, t))),
         'Death': (1.0, False, lambda t: (pose(keyed(DEATH, t)), land(ss((t - 0.4) / 0.45)))),
         'Fidget': (1.0, False, lambda t: pose(keyed(FIDGET, t)))}


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    n = int(round(seconds * FPS))
    poses = []
    rig.animation_data.action = None
    for f in range(n + 1):
        fn((f % n) / FPS if loop else f / FPS)
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy())
                      for b in rig.pose.bones})
    rig.animation_data.action = act
    prev = {}
    for f, frame in enumerate(poses):
        for b in rig.pose.bones:
            q, loc, scale = frame[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc; b.scale = scale
            b.keyframe_insert('rotation_quaternion', frame=f + 1); b.keyframe_insert('location', frame=f + 1)
            b.keyframe_insert('scale', frame=f + 1)
    rig.animation_data.action = None


for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
for name, (sec, loop, fn) in CLIPS.items():
    key_action(name, sec, loop, fn)
    print('CLIP', name, sec, flush=True)
key_action('Dead', 1.0, False, lambda t: (pose(keyed(DEATH, 1.0)), land(1.0)))
rig.animation_data.action = bpy.data.actions['Fly']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED')
