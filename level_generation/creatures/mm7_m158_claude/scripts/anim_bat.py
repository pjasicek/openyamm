"""Procedural clips for the MM7 bat (24 fps), adapted from mm6_bat_claude/scripts/anim_bat.py to the native MM7
m158 actions and timing (raw ticks of 1/16 s: fly 19, attack 13, hit 13, death 14).
  Fly     28 frames loop  flap: wings high (native a) -> down sweep (d) -> spread (e) -> rising (f); elbow and finger
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
Args: [in.blend out.blend] relative to the project (default work/rig_v1.blend -> work/anim_v1.blend).
"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SRC = _args[0] if _args else 'work/rig_v1.blend'
DST = _args[1] if len(_args) > 1 else 'work/anim_v1.blend'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, SRC))
rig = bpy.data.objects['Bat_Rig']; mesh = bpy.data.objects['Bat']
FPS = 24
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
SG = {'L': 1.0, 'R': -1.0}
HOVER = 0.0
FLY, ATT, HIT_T, DIE = 28 / FPS, 20 / FPS, 20 / FPS, 21 / FPS


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
        for k in (1, 2, 3, 4):
            rot(f'Finger{k}a_{side}', Z, -s * fold * (0.35 + 0.12 * k))
    for k in (1, 2, 3, 4):
        rot(f'Finger{k}b_{side}', Y, s * finger_curl * (0.6 + 0.15 * k))


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
    return {'up': 2 + 40 * c, 'elbow': 4 + 16 * math.cos(2 * math.pi * (p - 0.07)),
            'fold': 18 * max(0.0, math.sin(2 * math.pi * p)) ** 1.5,          # upstroke: wings partly folded
            'curl': 10 * math.sin(2 * math.pi * (p - 0.12)),
            'bob': 0.018 * math.cos(2 * math.pi * (p + 0.5)), 'pitch': 4 * math.sin(2 * math.pi * p)}


def fly(t):
    P.reset(rig)
    f = flap_params((t / FLY) % 1.0)
    body(d=Vector((0, 0, HOVER + f['bob'])), pitch=f['pitch'], head=-3 * f['pitch'] / 4,
         legs=6 * math.sin(2 * math.pi * t / FLY))
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
# Native attack (front view): aa-ab wings raised high, ac spread, ad-ae wings sweep down and forward around the
# target while the head bites (ae holds 3 ticks: the blow), af-ag open back out. Impact at 0.44 s.
ATTACK = [
    (0.00, flap_key(0.0)),
    (0.17, {'up': 52, 'elbow': 25, 'fold': 8, 'd': V((0, 0.03, HOVER + 0.03)), 'pitch': -10, 'head': -12, 'ears': 10}),
    (0.30, {'up': 4, 'elbow': 2, 'd': V((0, -0.03, HOVER + 0.01)), 'pitch': 0, 'head': 0}),
    (0.44, {'up': -38, 'elbow': -25, 'fold': 5, 'sweep': 32, 'curl': 25, 'd': V((0, -0.09, HOVER - 0.02)), 'pitch': 16,
            'head': 22, 'legs': 20}),
    (0.60, {'up': -30, 'elbow': -18, 'sweep': 26, 'curl': 18, 'd': V((0, -0.07, HOVER - 0.01)), 'pitch': 10, 'head': 12}),
    (ATT, flap_key(0.0)),
]
# Native reaction: jolt back and up, wings flung up and half folded, head thrown back, then recovery.
HIT = [
    (0.00, flap_key(0.0)),
    (0.10, {'up': 60, 'elbow': 35, 'fold': 40, 'd': V((0, 0.06, HOVER + 0.04)), 'pitch': -18, 'head': -25, 'legs': -15,
            'ears': -15, 'roll': 10}),
    (0.40, {'up': 40, 'elbow': 22, 'fold': 28, 'd': V((0, 0.04, HOVER + 0.02)), 'pitch': -10, 'head': -12, 'roll': -6}),
    (HIT_T, flap_key(0.0)),
]
# Native death: na/nb reaction frames, then da-de the bat drops flat with its wings spread (corpse xa).
DEATH = [
    (0.00, flap_key(0.0)),
    (0.16, {'up': 60, 'elbow': 35, 'fold': 30, 'd': V((0, 0.02, HOVER + 0.04)), 'pitch': -22, 'head': -28, 'roll': 20}),
    (0.42, {'up': 25, 'elbow': 15, 'fold': 30, 'd': V((0, 0.03, HOVER * 0.6)), 'pitch': 15, 'head': -8, 'roll': 10,
            'legs': 20}),
    (0.70, {'fold': 10, 'd': V((0, 0.03, 0.0)), 'pitch': 8, 'head': 6, 'ears': -20, 'legs': -25}),
    (DIE, {'fold': 12, 'd': V((0, 0.03, 0.0)), 'pitch': 8, 'head': 8, 'ears': -25, 'legs': -30}),
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


CLIPS = {'Fly': (FLY, True, fly),
         'Attack': (ATT, False, lambda t: generic(keyed(ATTACK, t))),
         'Hit': (HIT_T, False, lambda t: generic(keyed(HIT, t))),
         'Death': (DIE, False, lambda t: (generic(keyed(DEATH, t)), land(ss((t - 0.30) / 0.45))))}


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
key_action('Dead', 1.0, False, lambda t: (generic(keyed(DEATH, DIE)), land(1.0)))
rig.animation_data.action = bpy.data.actions['Fly']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, DST))
print('SAVED')
