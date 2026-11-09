"""Procedural clips for the rat (24 fps), following the native MM6 rat actions.

Each clip is a function of time returning pose parameters; legs are placed by two-bone IK on footholds
(stance feet planted, swing feet lifted), the tail follows the body with a lagging wave.
  Standing  2.0 s loop   breathing, small head/tail motion
  Walking   trot loop    diagonal pairs, front paws paddle high (native walk)
  Running   faster trot  longer stride, spine flex
  Attack    0.75 s       rear up with claws spread, lunge and bite, recover (native attack)
  Hit       0.75 s       flatten, legs splay, tail whips straight up, recover (native hit)
  Death     1.0 s        rear up flailing, fall onto the side (native death); Dead = last frame held
  Fidget    1.0 s        sniff/chew head twitches, tail flick
Writes the actions into work/rig_v1.blend -> work/anim_v1.blend and prints clip/stride info.
"""
import bpy, sys, os, math, json
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Rat_Rig']; mesh = bpy.data.objects['Rat']; sc = bpy.context.scene
FPS = 24
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
WRIST = {s: REST[f'FrontPaw_{s}'].translation.copy() for s in 'LR'}
ANKLE = {s: REST[f'HindPaw_{s}'].translation.copy() for s in 'LR'}
SIDE = {'L': 1.0, 'R': -1.0}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def set_world_rot(name, q):
    b = rig.pose.bones[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, Vector((1, 1, 1))); bpy.context.view_layer.update()


def place_leg(kind, side, target, pitch=0.0, free=None):
    """kind 'front'/'hind'; target = wrist/ankle world point; pitch tilts the paw (+ = toes down)."""
    if free is not None:                                      # FK: (upper deg, lower deg, splay deg)
        up, lo, splay = free
        u, l = (f'UpperArm_{side}', f'ForeArm_{side}') if kind == 'front' else (f'Thigh_{side}', f'Shin_{side}')
        rot(u, Y, splay * SIDE[side]); rot(u, X, up); rot(l, X, lo)
        return
    if kind == 'front':
        pole = target + Vector((SIDE[side] * 0.05, 0.25, 0.05))
        P.two_bone_ik(rig, f'UpperArm_{side}', f'ForeArm_{side}', target, pole)
        paw, rest = f'FrontPaw_{side}', REST[f'FrontPaw_{side}']
    else:
        pole = target + Vector((SIDE[side] * 0.04, -0.25, 0.10))
        P.two_bone_ik(rig, f'Thigh_{side}', f'Shin_{side}', target, pole)
        paw, rest = f'HindPaw_{side}', REST[f'HindPaw_{side}']
    q = Quaternion(X, math.radians(pitch)) @ rest.to_quaternion()
    set_world_rot(paw, q)


def tail_wave(amp_yaw, amp_pitch, phase, lift=0.0, base_pitch=0.0):
    for i in range(1, 7):
        k = i / 6.0
        rot(f'Tail{i}', Z, amp_yaw * k * math.sin(2 * math.pi * (phase - 0.09 * i)))
        rot(f'Tail{i}', X, (lift if i == 1 else lift * 0.15) + amp_pitch * math.sin(2 * math.pi * (phase - 0.09 * i))
            + (base_pitch if i == 1 else 0))


def body(hips_d=Vector(), hips_pitch=0.0, hips_roll=0.0, spine_pitch=0.0, spine_yaw=0.0, head_pitch=0.0,
         head_yaw=0.0):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(hips_d) @ root.matrix; bpy.context.view_layer.update()
    rot('Spine1', Y, hips_roll); rot('Spine1', X, hips_pitch)
    for n, s in (('Spine2', 0.5), ('Spine3', 0.5)):
        rot(n, X, spine_pitch * s); rot(n, Z, spine_yaw * s)
    rot('Neck1', X, head_pitch * 0.4); rot('Head', X, head_pitch * 0.6)
    rot('Neck1', Z, head_yaw * 0.5); rot('Head', Z, head_yaw * 0.5)


# ---------------------------------------------------------------- floor rules
import numpy as np
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
CORE = np.array([n.startswith(('Spine', 'Neck', 'Head', 'Thigh', 'UpperArm', 'ForeArm', 'Shin')) for n in _dom])
_dg = bpy.context.evaluated_depsgraph_get()
FLOOR = 0.004


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


def clamp_tail():
    """Raise any tail segment whose end dips under the floor (bone by bone, base to tip)."""
    for i in range(1, 7):
        b = rig.pose.bones[f'Tail{i}']
        t = rig.matrix_world @ b.tail
        if t.z < 0.012:
            h = rig.matrix_world @ b.head
            d = t - h; L = d.length
            flat = Vector((d.x, d.y, 0)).normalized()
            dz = 0.012 - h.z
            target = h + flat * math.sqrt(max(L * L - dz * dz, 1e-6)) + Vector((0, 0, dz)) if abs(dz) < L else h + flat * L
            P.aim_bone(rig, b.name, target)


LIMBS = {(k, sd): np.array([n in ((f'UpperArm_{sd}', f'ForeArm_{sd}', f'FrontPaw_{sd}') if k == 'front' else
                                  (f'Thigh_{sd}', f'Shin_{sd}', f'HindPaw_{sd}')) for n in _dom])
         for k in ('front', 'hind') for sd in 'LR'}


def clamp_limbs():
    """A limb through the floor (body lying on its side) swings up about its upper joint until it clears."""
    for (kind, sd), mask in LIMBS.items():
        upper = f'UpperArm_{sd}' if kind == 'front' else f'Thigh_{sd}'
        for _ in range(15):
            co = mesh_co(); low = co[mask, 2].min()
            if low > -0.006:
                break
            b = rig.pose.bones[upper]
            d = (b.tail - b.head).normalized(); axis = d.cross(Vector((0, 0, 1)))
            if axis.length < 1e-3:
                axis = Vector((1, 0, 0))
            axis.normalize()
            P.rotate_world(rig, upper, axis, -6.0)
            if mesh_co()[mask, 2].min() < low:
                P.rotate_world(rig, upper, axis, 12.0)


def floor_fit(lift_core=True):
    """Keep the body out of the floor: lift the whole rat if core (body/head/upper legs) sinks, then the tail."""
    if lift_core:
        co = mesh_co()
        low = co[CORE, 2].min()
        if low < -FLOOR:
            root = rig.pose.bones['Spine1']
            root.matrix = Matrix.Translation(Vector((0, 0, -low))) @ root.matrix; bpy.context.view_layer.update()
    clamp_tail()


# ---------------------------------------------------------------- clips
def gait(t, T, stride, duty, lift_f, lift_h, flex):
    p = (t / T) % 1.0
    P.reset(rig)
    body(hips_d=Vector((0, 0, -0.006 * math.cos(4 * math.pi * p) - 0.004)), spine_pitch=flex * math.sin(4 * math.pi * p),
         spine_yaw=3 * math.sin(2 * math.pi * p), head_pitch=-2 * math.cos(4 * math.pi * p), head_yaw=-2 * math.sin(2 * math.pi * p))
    tail_wave(14, 4, p, lift=6)
    s = stride * duty
    for kind, side, ph in (('front', 'L', 0.0), ('hind', 'R', 0.0), ('front', 'R', 0.5), ('hind', 'L', 0.5)):
        q = (p + ph) % 1.0
        if q < duty:
            dy = -s / 2 + s * (q / duty); dz = 0.0; pitch = 0.0
        else:
            u = (q - duty) / (1 - duty)
            dy = s / 2 - s * ss(u); dz = (lift_f if kind == 'front' else lift_h) * math.sin(math.pi * u)
            pitch = 30 * math.sin(math.pi * u)
        base = WRIST[side] if kind == 'front' else ANKLE[side]
        place_leg(kind, side, base + Vector((0, dy, dz)), pitch)


def standing(t):
    P.reset(rig)
    b = math.sin(2 * math.pi * t / 2.0)
    body(spine_pitch=-1.2 * b, head_pitch=1.5 * b, head_yaw=4 * math.sin(2 * math.pi * t / 2.0 * 0.5))
    tail_wave(5, 2, t / 2.0)
    for kind in ('front', 'hind'):
        for side in 'LR':
            place_leg(kind, side, (WRIST if kind == 'front' else ANKLE)[side])


def fidget(t):
    P.reset(rig)
    u = t / 1.0
    sniff = 3 * math.sin(2 * math.pi * 6 * u) * math.sin(math.pi * u)
    body(head_pitch=-12 * math.sin(math.pi * u) + sniff, head_yaw=10 * math.sin(2 * math.pi * u), spine_pitch=-3 * math.sin(math.pi * u))
    tail_wave(18 * math.sin(math.pi * u), 3, u * 2)
    for kind in ('front', 'hind'):
        for side in 'LR':
            place_leg(kind, side, (WRIST if kind == 'front' else ANKLE)[side])


def keyed(keys, t):
    """keys: list of (time, params dict); smoothstep interpolation per segment."""
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6))
            out = {}
            for k in set(a) | set(b):
                va, vb = a.get(k, 0.0), b.get(k, 0.0)
                out[k] = va + (vb - va) * u if not isinstance(va, Vector) and not isinstance(vb, Vector) else \
                    (va if isinstance(va, Vector) else Vector()).lerp(vb if isinstance(vb, Vector) else Vector(), u)
            return out
    return keys[-1][1]


def generic(params, legs_free=False):
    P.reset(rig)
    body(hips_d=params.get('hips', Vector()), hips_pitch=params.get('hips_pitch', 0.0), hips_roll=params.get('roll', 0.0),
         spine_pitch=params.get('spine', 0.0), spine_yaw=params.get('yaw', 0.0),
         head_pitch=params.get('head', 0.0), head_yaw=params.get('head_yaw', 0.0))
    tail_wave(params.get('tail_sway', 0.0), 0, params.get('tail_phase', 0.0), lift=params.get('tail_lift', 0.0))
    for side in 'LR':
        if legs_free:
            place_leg('front', side, None, free=(params.get('fu', 0.0), params.get('fl', 0.0), params.get('fs', 0.0)))
            place_leg('hind', side, None, free=(params.get('hu', 0.0), params.get('hl', 0.0), params.get('hs', 0.0)))
        else:
            off = params.get('front_' + side, Vector())
            place_leg('front', side, WRIST[side] + off, params.get('paw', 0.0))
            place_leg('hind', side, ANKLE[side] + params.get('hind_' + side, Vector()))


V = Vector
ATTACK = [
    (0.00, {}),
    (0.22, {'hips': V((0, 0.03, 0.0)), 'hips_pitch': -22, 'spine': -18, 'head': 10, 'tail_lift': 10,
            'front_L': V((0.06, 0.02, 0.20)), 'front_R': V((-0.06, 0.02, 0.20)), 'paw': -40}),
    (0.40, {'hips': V((0, -0.07, 0.0)), 'hips_pitch': 2, 'spine': 6, 'head': 10, 'tail_lift': -6,
            'front_L': V((0.03, -0.12, 0.0)), 'front_R': V((-0.03, -0.12, 0.0)), 'paw': 10}),
    (0.52, {'hips': V((0, -0.06, 0.0)), 'hips_pitch': 2, 'spine': 5, 'head': 6,
            'front_L': V((0.03, -0.10, 0.0)), 'front_R': V((-0.03, -0.10, 0.0))}),
    (0.75, {}),
]
HIT = [
    (0.00, {}),
    (0.15, {'hips': V((0, 0.03, -0.018)), 'spine': 5, 'head': 4, 'tail_lift': 75,
            'front_L': V((0.07, 0.0, 0.0)), 'front_R': V((-0.07, 0.0, 0.0)),
            'hind_L': V((0.04, 0.0, 0.0)), 'hind_R': V((-0.04, 0.0, 0.0))}),
    (0.50, {'hips': V((0, 0.02, -0.015)), 'spine': 4, 'head': 3, 'tail_lift': 70,
            'front_L': V((0.07, 0.0, 0.0)), 'front_R': V((-0.07, 0.0, 0.0)),
            'hind_L': V((0.04, 0.0, 0.0)), 'hind_R': V((-0.04, 0.0, 0.0))}),
    (0.75, {}),
]
DEATH = [
    (0.00, {}),
    (0.25, {'hips': V((0, 0.03, 0.01)), 'hips_pitch': -35, 'spine': -20, 'head': -15, 'fu': -70, 'fl': 40, 'fs': 25,
            'hu': -20, 'hl': 10}),
    (0.55, {'hips': V((0, 0.06, -0.01)), 'hips_pitch': -25, 'roll': 50, 'spine': -10, 'head': -10, 'fu': -40,
            'fl': 50, 'fs': 40, 'hu': -30, 'hl': 30, 'hs': 20, 'tail_sway': 20, 'tail_phase': 0.3}),
    (0.85, {'hips': V((0, 0.06, -0.035)), 'hips_pitch': -5, 'roll': 92, 'spine': 6, 'head': 10, 'fu': 15,
            'fl': 45, 'fs': 20, 'hu': 20, 'hl': 40, 'hs': 15, 'tail_sway': 12, 'tail_phase': 0.2}),
    (1.00, {'hips': V((0, 0.06, -0.035)), 'hips_pitch': -5, 'roll': 90, 'spine': 8, 'head': 12, 'fu': 18,
            'fl': 50, 'fs': 20, 'hu': 22, 'hl': 45, 'hs': 15, 'tail_sway': 12, 'tail_phase': 0.2}),
]

CLIPS = {
    'Standing': (2.0, True, standing),
    'Walking': (14 / FPS, True, lambda t: gait(t, 14 / FPS, 0.28, 0.55, 0.06, 0.04, 2)),
    'Running': (12 / FPS, True, lambda t: gait(t, 12 / FPS, 0.43, 0.45, 0.07, 0.05, 5)),
    'Attack': (0.75, False, lambda t: generic(keyed(ATTACK, t))),
    'Hit': (0.75, False, lambda t: generic(keyed(HIT, t))),
    'Death': (1.0, False, lambda t: generic(keyed(DEATH, t), legs_free=True)),
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
    poses = []
    rig.animation_data.action = None
    for f in range(n + 1):
        t = (f % n) / FPS if loop else f / FPS
        fn(t)
        floor_fit(lift_core=name in ('Attack', 'Hit', 'Death', 'Dead'))
        if name in ('Death', 'Dead'):
            clamp_limbs()
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


for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
for name, (sec, loop, fn) in CLIPS.items():
    key_action(name, sec, loop, fn)
    print('CLIP', name, sec, flush=True)
# Dead: last Death pose held for 1 s
death_last = lambda t: generic(keyed(DEATH, 1.0), legs_free=True)
key_action('Dead', 1.0, False, death_last)
info = {'fps': FPS, 'walk_stride_m': 0.28, 'run_stride_m': 0.43}
json.dump(info, open(os.path.join(HERE, 'work', 'anim_info.json'), 'w'))
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED anim_v1.blend')
