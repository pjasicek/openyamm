"""Procedural clips for the bat (24 fps), following the native MM6 bat actions.
  Fly     0.75 s loop  flap: wings high (native a) -> down sweep (d) -> spread (e) -> rising (f); elbow and finger
                       tips lag the shoulder, fingers fold a little on the upstroke, body bobs opposite the wings
  Attack  0.75 s       wings up, lunge forward with the head striking down-forward while the wings sweep forward
                       and down around the target (native b-d), open back out to the flap (e-f)
  Hit     0.75 s       jolt back and up, wings snap up and fold, head thrown back, recover into the flap
  Death   1.0 s        wings jerk up, body rolls and drops, lands on its belly (pitch 35 deg lays the trunk
                       flattest) with the wings laid on the floor (native corpse);
                       Dead = last pose held
Hover: none. The native fly frames float ~60 px above the sprite anchor, but billboards lean toward the camera; a
lifted upright model pokes through low ceilings (the engine keeps only the 67-unit collision box under the ceiling),
so the model fills the collision box from the actor origin up. HOVER stays as a knob for that offset.
Bone rotations about world axes through each bone head (forward -Y, up +Z, left +X).
Writes work/anim_v1.blend.
"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Bat_Rig']; mesh = bpy.data.objects['Bat']
FPS = 24
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
SG = {'L': 1.0, 'R': -1.0}
HOVER = 0.0


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg)


def wing(side, up, elbow, fold, sweep=0.0, finger_curl=0.0):
    """up: shoulder raise (deg, + up); elbow: extra forearm raise; fold: fingers/forearm swept back toward the body
    (deg); sweep: whole wing swung forward (+) about the vertical; finger_curl: fingertips bend down (+)."""
    s = SG[side]
    rot(f'UpperArm_{side}', Z, s * sweep)
    rot(f'UpperArm_{side}', Y, -s * up)
    rot(f'ForeArm_{side}', Y, -s * elbow)
    if fold:
        rot(f'ForeArm_{side}', Z, -s * fold * 0.5)
        for k in (1, 2, 3):
            rot(f'Finger{k}a_{side}', Z, -s * fold * (0.35 + 0.15 * k))
    for k in (1, 2, 3):
        rot(f'Finger{k}b_{side}', Y, s * finger_curl * (0.6 + 0.2 * k))


def body(d=Vector(), pitch=0.0, roll=0.0, head=0.0, legs=0.0, ears=0.0):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(d) @ root.matrix; bpy.context.view_layer.update()
    rot('Spine1', Y, roll); rot('Spine1', X, pitch)
    rot('Neck1', X, head * 0.4); rot('Head', X, head * 0.6)
    for s in 'LR':
        rot(f'Thigh_{s}', X, legs)
        rot(f'Ear_{s}', Y, -SG[s] * ears)


def flap_params(p):
    c = math.cos(2 * math.pi * p)
    return {'up': 6 + 38 * c, 'elbow': 6 + 16 * math.cos(2 * math.pi * (p - 0.07)),
            'fold': 18 * max(0.0, math.sin(2 * math.pi * p)) ** 1.5,          # upstroke: wings partly folded
            'curl': 10 * math.sin(2 * math.pi * (p - 0.12)),
            'bob': 0.018 * math.cos(2 * math.pi * (p + 0.5)), 'pitch': 4 * math.sin(2 * math.pi * p)}


def fly(t):
    P.reset(rig)
    f = flap_params((t / 0.75) % 1.0)
    body(d=Vector((0, 0, HOVER + f['bob'])), pitch=f['pitch'], head=-3 * f['pitch'] / 4,
         legs=6 * math.sin(2 * math.pi * t / 0.75))
    for s in 'LR':
        wing(s, f['up'], f['elbow'], f['fold'], finger_curl=f['curl'])


def blend(a, b, u):
    out = {}
    for k in set(a) | set(b):
        va, vb = a.get(k, 0.0), b.get(k, 0.0)
        if isinstance(va, Vector) or isinstance(vb, Vector):
            va = va if isinstance(va, Vector) else Vector(); vb = vb if isinstance(vb, Vector) else Vector()
            out[k] = va.lerp(vb, u)
        else:
            out[k] = va + (vb - va) * u
    return out


def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            return blend(a, b, ss((t - t0) / max(t1 - t0, 1e-6)))
    return keys[-1][1]


def flap_key(p):
    f = flap_params(p)
    return {'up': f['up'], 'elbow': f['elbow'], 'fold': f['fold'], 'curl': f['curl'],
            'd': Vector((0, 0, HOVER + f['bob'])),
            'pitch': f['pitch']}


def generic(k):
    P.reset(rig)
    body(d=k.get('d', Vector()), pitch=k.get('pitch', 0.0), roll=k.get('roll', 0.0), head=k.get('head', 0.0),
         legs=k.get('legs', 0.0), ears=k.get('ears', 0.0))
    for s in 'LR':
        wing(s, k.get('up', 0.0), k.get('elbow', 0.0), k.get('fold', 0.0), k.get('sweep', 0.0), k.get('curl', 0.0))


V = Vector
ATTACK = [
    (0.00, flap_key(0.0)),
    (0.18, {'up': 50, 'elbow': 25, 'fold': 10, 'd': V((0, 0.03, HOVER + 0.03)), 'pitch': -8, 'head': -10, 'ears': 10}),
    (0.38, {'up': -35, 'elbow': -25, 'fold': 5, 'sweep': 35, 'curl': 25, 'd': V((0, -0.14, HOVER * 0.5 - 0.02)), 'pitch': 18,
            'head': 22, 'legs': 20}),
    (0.52, {'up': -30, 'elbow': -20, 'sweep': 30, 'curl': 20, 'd': V((0, -0.12, HOVER * 0.6 - 0.01)), 'pitch': 14, 'head': 15}),
    (0.75, flap_key(0.0)),
]
HIT = [
    (0.00, flap_key(0.0)),
    (0.12, {'up': 60, 'elbow': 35, 'fold': 40, 'd': V((0, 0.07, HOVER + 0.04)), 'pitch': -18, 'head': -25, 'legs': -15,
            'ears': -15}),
    (0.40, {'up': 45, 'elbow': 25, 'fold': 30, 'd': V((0, 0.05, HOVER + 0.02)), 'pitch': -10, 'head': -12}),
    (0.75, flap_key(0.0)),
]
DEATH = [
    (0.00, flap_key(0.0)),
    (0.20, {'up': 65, 'elbow': 40, 'fold': 30, 'd': V((0, 0.02, HOVER + 0.05)), 'pitch': -25, 'head': -30, 'roll': 30}),
    (0.50, {'up': 30, 'elbow': 20, 'fold': 45, 'd': V((0, 0.04, HOVER * 0.6)), 'pitch': 20, 'head': -10, 'roll': 80,
            'legs': 25}),
    (0.80, {'fold': 18, 'd': V((0, 0.04, 0.0)), 'pitch': 30, 'head': 6, 'ears': -20, 'legs': -40}),
    (1.00, {'fold': 22, 'd': V((0, 0.04, 0.0)), 'pitch': 35, 'head': 8, 'ears': -25, 'legs': -45}),
]

import numpy as np
_dg = bpy.context.evaluated_depsgraph_get()


_vg = {g.index: g.name for g in mesh.vertex_groups}
_dom = [_vg.get(max(v.groups, key=lambda g: g.weight).group, '') if v.groups else '' for v in mesh.data.vertices]
WING = {s: np.array([n.endswith('_' + s) and n.startswith(('UpperArm', 'ForeArm', 'Finger')) for n in _dom])
        for s in 'LR'}
TIPS = {s: np.array([n.endswith('_' + s) and n.startswith(('ForeArm', 'Finger')) for n in _dom]) for s in 'LR'}
FINGERS = {s: np.array([n.endswith('_' + s) and n.startswith('Finger') for n in _dom]) for s in 'LR'}
BODY = ~(WING['L'] | WING['R'])


def mesh_co():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


def fit_down(bone, side, mask, u, target=0.01):
    """Rotate a wing bone down (or up) until the masked vertices just touch the floor; apply u of that angle."""
    def low_at(deg):
        rot(bone, Y, SG[side] * deg)
        z = mesh_co()[mask, 2].min()
        rot(bone, Y, -SG[side] * deg)
        return z
    lo, hi = -60.0, 60.0                 # + lowers the wing
    if low_at(lo) < target:
        best = lo
    elif low_at(hi) > target:
        best = hi
    else:
        for _ in range(12):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if low_at(mid) > target else (lo, mid)
        best = lo
    rot(bone, Y, SG[side] * best * u)


def land(u):
    """Death: blend the body down so its belly (not the wingtips) reaches the floor at the end of the fall, then lay
    each wing at belly height: upper arm until the forearm touches, forearm until the fingers touch."""
    low = mesh_co()[BODY, 2].min()
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(Vector((0, 0, -low * u))) @ root.matrix; bpy.context.view_layer.update()
    if u <= 0:
        return
    belly = mesh_co()[BODY, 2].min() + 0.01      # fit relative to the belly, so the fall blends smoothly
    for side in 'LR':
        fit_down(f'UpperArm_{side}', side, TIPS[side], u, belly)
        fit_down(f'ForeArm_{side}', side, FINGERS[side], u, belly)


CLIPS = {'Fly': (0.75, True, fly),
         'Attack': (0.75, False, lambda t: generic(keyed(ATTACK, t))),
         'Hit': (0.75, False, lambda t: generic(keyed(HIT, t))),
         'Death': (1.0, False, lambda t: (generic(keyed(DEATH, t)), land(ss((t - 0.35) / 0.45))))}


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
            b.keyframe_insert('rotation_quaternion', frame=f + 1); b.keyframe_insert('location', frame=f + 1)
    rig.animation_data.action = None


for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
for name, (sec, loop, fn) in CLIPS.items():
    key_action(name, sec, loop, fn)
    print('CLIP', name, sec, flush=True)
key_action('Dead', 1.0, False, lambda t: (generic(keyed(DEATH, 1.0)), land(1.0)))
rig.animation_data.action = bpy.data.actions['Fly']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED')
