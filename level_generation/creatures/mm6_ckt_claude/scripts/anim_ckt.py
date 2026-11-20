"""Procedural clips for the cockatrice (24 fps), following the native MM6 cockatrice actions (ckt frames).
The bat's flyer route for the wings (shoulder raise with a lagging elbow and a finger fan) plus two walking bird
legs: the ankle is placed on a foothold, the tarsus keeps its rest direction (plus a pitch), the hock comes from that,
and Thigh + Shin reach the hock by two-bone IK with the knee pole in front (bird knee forward, hock back); the foot
keeps its rest orientation plus a toe pitch.
  Standing  1.5 s loop   breathing, slow wing flex, tail sway, head small turns (native: wings spread, still)
  Walking   0.75 s loop  bipedal walk, duty 0.6, two wing beats per stride (native walk raises the wings twice),
                         head bobs, hips roll, tail sways; stride per cycle STRIDE (binding stride_length)
  Attack    0.75 s       crouch, hop with a wing down-sweep, both feet kick forward with the talons, land (native)
  Hit       0.625 s      head thrown back, one foot lifted, wings flail unevenly, recover (native wnc)
  Death     1.0 s        head back and wings up, then collapses forward onto its belly with the wings laid flat on
                         the floor (native die / ded); Dead = last pose held
  Fidget    1.5 s        looks left and right with small wing lifts (native fgt)
  Cast      0.75 s       Mind Blast: rears up, wings high, head raised, head thrust at the release
Floor rules every frame: the body never dips below the floor; tail segments lift when their end dips under it.
Reads work/rig_v1.blend (or the UV-mapped work/anim_v1.blend when it exists), writes work/anim_v1.blend."""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Ckt_Rig']; mesh = bpy.data.objects['Cockatrice']
FPS = 24
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
SG = {'L': 1.0, 'R': -1.0}
STRIDE = 0.30
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
P.reset(rig)
W = lambda name, tail=False: (rig.matrix_world @ (rig.pose.bones[name].tail if tail else rig.pose.bones[name].head)).copy()
REST = {s: {'hip': W(f'Thigh_{s}'), 'knee': W(f'Shin_{s}'), 'hock': W(f'Tarsus_{s}'), 'ankle': W(f'Foot_{s}'),
            'toe': W(f'Foot_{s}', True)} for s in 'LR'}
REST_FOOT_Q = {s: rig.pose.bones[f'Foot_{s}'].matrix.to_quaternion() for s in 'LR'}
HIPS_REST = W('Hips')
TAILS = [f'Tail{i}' for i in range(1, 9)]


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg)


# ------------------------------------------------------------------------------------------------ body parts

def body(lift=0.0, fwd=0.0, side=0.0, pitch=0.0, roll=0.0, yaw=0.0, chest=0.0):
    """Hips offset and rotation (+pitch tips the front down), chest pitch on top."""
    root = rig.pose.bones['Hips']
    root.matrix = Matrix.Translation(Vector((side, -fwd, lift))) @ root.matrix
    bpy.context.view_layer.update()
    rot('Hips', Z, yaw); rot('Hips', Y, roll); rot('Hips', X, pitch)   # +X rotation tips the front (-Y) down
    rot('Chest', X, chest)


def head(pitch=0.0, yaw=0.0, reach=0.0):
    """pitch + = head up (beak raised); yaw + = toward the creature's left; reach + = neck stretched forward."""
    rot('Neck1', X, -pitch * 0.35 - reach); rot('Neck2', X, -pitch * 0.35 + reach * 0.6)   # +X lowers the head
    rot('Head', X, -pitch * 0.3 + reach * 0.4)
    rot('Neck1', Z, yaw * 0.4); rot('Neck2', Z, yaw * 0.35); rot('Head', Z, yaw * 0.25)


def tail(t, sway=6.0, lift=0.0, freq=1.0, phase=0.0, curl=0.0):
    for i, name in enumerate(TAILS):
        u = (i + 1) / len(TAILS)
        rot(name, Z, sway * u * math.sin(2 * math.pi * (freq * t + phase) - i * 0.5) + curl * u)
        rot(name, X, lift * (1.0 - u * 0.6))


def wing(side, up=0.0, elbow=0.0, fan=0.0, sweep=0.0, curl=0.0):
    """up: shoulder raise (deg, + up); elbow: extra forearm raise; fan: fingers close toward the leading finger (+)
    or spread (-); sweep: wing swung forward (+) about the vertical; curl: fingertips bend forward (+)."""
    s = SG[side]
    rot(f'UpperArm_{side}', Z, s * sweep)
    rot(f'UpperArm_{side}', Y, -s * up)
    rot(f'ForeArm_{side}', Y, -s * elbow)
    for k, share in ((2, 0.5), (3, 1.0)):
        rot(f'Finger{k}a_{side}', Y, -s * fan * share)
    for k in (1, 2, 3):
        rot(f'Finger{k}b_{side}', Z, s * curl * (0.6 + 0.2 * k))


def place_leg(side, ankle, tarsus_pitch=0.0, toe_pitch=0.0):
    """IK: ankle at `ankle` (world); tarsus = rest direction pitched about X (+ = foot end forward-up); foot = rest
    orientation pitched (+ = toes up)."""
    r = REST[side]
    tv = Matrix.Rotation(math.radians(-tarsus_pitch), 3, X) @ (r['ankle'] - r['hock'])
    hock = Vector(ankle) - tv
    hip = W(f'Thigh_{side}')
    pole = hip + (r['knee'] - r['hip']) + Vector((0, -0.3, 0))
    P.two_bone_ik(rig, f'Thigh_{side}', f'Shin_{side}', hock, pole)
    P.aim_bone(rig, f'Tarsus_{side}', Vector(ankle))
    foot = rig.pose.bones[f'Foot_{side}']
    q = Quaternion(X, math.radians(-toe_pitch)) @ REST_FOOT_Q[side]
    foot.matrix = Matrix.LocRotScale(foot.head.copy(), q, Vector((1, 1, 1)))
    bpy.context.view_layer.update()


def rest_ankle(side, dx=0.0, dy=0.0, dz=0.0):
    return REST[side]['ankle'] + Vector((dx, dy, dz))


# ------------------------------------------------------------------------------------------------ floor

_vg = {g.index: g.name for g in mesh.vertex_groups}
_dom = [_vg.get(max(v.groups, key=lambda g: g.weight).group, '') if v.groups else '' for v in mesh.data.vertices]
WINGS = np.array([n.startswith(('UpperArm', 'ForeArm', 'Finger')) for n in _dom])
TAILV = np.array([n.startswith('Tail') for n in _dom])
LEGS = np.array([n.startswith(('Thigh', 'Shin', 'Tarsus', 'Foot')) for n in _dom])
CORE = ~(WINGS | TAILV | LEGS)
TIPS = {s: np.array([n.endswith('_' + s) and n.startswith(('ForeArm', 'Finger')) for n in _dom]) for s in 'LR'}
FINGERS = {s: np.array([n.endswith('_' + s) and n.startswith('Finger') for n in _dom]) for s in 'LR'}


def mesh_co():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


def _tail_members():
    out = {}
    for name in TAILS:
        group = mesh.vertex_groups[name].index
        out[name] = [v.index for v in mesh.data.vertices
                     if v.groups and max(v.groups, key=lambda g: g.weight).group == group]
    return out


TAIL_MEMBERS = _tail_members()
_rest_co = np.array([tuple(v.co) for v in mesh.data.vertices])
# Rest clearance of each tail bone's end above the bottom of its own segment (its radius there).
TAIL_R = {n: max(0.006, float(W(n, True).z - _rest_co[TAIL_MEMBERS[n], 2].min())) if TAIL_MEMBERS[n] else 0.01
          for n in TAILS}


def tail_floor(margin=0.003):
    """Tail on or above the floor without bending it upward: from the base, each segment whose end would sit lower
    than its radius is aimed so its end rests at that height (direction kept in plan view)."""
    for name in TAILS:
        end = W(name, True)
        need = TAIL_R[name] + margin
        if end.z < need:
            P.aim_bone(rig, name, Vector((end.x, end.y, need)))
        z = mesh_co()[TAIL_MEMBERS[name], 2].min() if TAIL_MEMBERS[name] else 1.0
        if z < margin:                                     # bottom still under the floor (thick segment): small lift
            end = W(name, True)
            P.aim_bone(rig, name, Vector((end.x, end.y, end.z + (margin - z))))


def core_floor(margin=0.0):
    low = mesh_co()[CORE | LEGS, 2].min()
    if low < margin:
        root = rig.pose.bones['Hips']
        root.matrix = Matrix.Translation(Vector((0, 0, margin - low))) @ root.matrix
        bpy.context.view_layer.update()


def fit_down(bone, side, mask, u, target):
    """Rotate a wing bone down until the masked vertices just touch `target` height; apply u of that angle."""
    def low_at(deg):
        rot(bone, Y, SG[side] * deg)
        z = mesh_co()[mask, 2].min()
        rot(bone, Y, -SG[side] * deg)
        return z
    lo, hi = -80.0, 100.0
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


# ------------------------------------------------------------------------------------------------ clips

def standing(t):
    P.reset(rig)
    w = 2 * math.pi * t / 1.5
    body(lift=0.004 * math.sin(2 * w), pitch=1.5 * math.sin(w), chest=1.0 * math.sin(2 * w))
    head(pitch=3 * math.sin(w + 0.6), yaw=6 * math.sin(w * 0.5))
    tail(t, sway=5, freq=1 / 1.5)
    for s in 'LR':
        wing(s, up=4 * math.sin(w + (0.3 if s == 'L' else 0.0)), elbow=3 * math.sin(w - 0.6), fan=3 * math.sin(w))
        place_leg(s, rest_ankle(s))
    tail_floor()


def gait(p, side):
    """Ankle offset (dy along travel, dz lift) and toe pitch for walk phase p (0..1) of one leg."""
    duty = 0.6
    if p < duty:                                   # stance: foot slides back under the moving body
        u = p / duty
        return STRIDE * (0.5 - u), 0.0, 0.0
    u = (p - duty) / (1 - duty)                    # swing: lift and bring forward
    return STRIDE * (-0.5 + ss(u)), 0.07 * math.sin(math.pi * u), 25 * math.sin(math.pi * u)


def walking(t):
    P.reset(rig)
    p = (t / 0.75) % 1.0
    w = 2 * math.pi * p
    body(lift=0.012 * math.cos(2 * w) - 0.01, pitch=6 + 2 * math.sin(2 * w), roll=4 * math.sin(w),
         side=0.008 * math.sin(w), yaw=3 * math.sin(w))
    head(pitch=-4 + 5 * math.sin(2 * w + 1.2), reach=4 * math.sin(2 * w + 0.6), yaw=-3 * math.sin(w))
    tail(t, sway=7, freq=1 / 0.75, lift=0)
    flap = math.cos(2 * w)                         # two wing beats per stride
    for s in 'LR':
        wing(s, up=8 + 26 * flap, elbow=6 + 12 * math.cos(2 * w - 0.5), fan=-4 + 10 * max(0.0, -flap),
             curl=8 * math.sin(2 * w - 0.8))
        dy, dz, toe = gait((p + (0.0 if s == 'L' else 0.5)) % 1.0, s)
        place_leg(s, rest_ankle(s, dy=-dy, dz=dz), tarsus_pitch=dz * 120, toe_pitch=toe)
    tail_floor()


def keyed(keys, t):
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6))
            return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * u for k in set(a) | set(b)}
    return dict(keys[-1][1])


def generic(k, t):
    """Pose from a parameter dict: body/head/tail/wings per side (L*/R* prefixes override both) and feet offsets."""
    P.reset(rig)
    g = lambda key: k.get(key, 0.0)
    body(lift=g('lift'), fwd=g('fwd'), pitch=g('pitch'), roll=g('roll'), yaw=g('yaw'), chest=g('chest'))
    head(pitch=g('hpitch'), yaw=g('hyaw'), reach=g('reach'))
    tail(t, sway=g('tsway') or 4, lift=g('tlift'), curl=g('tcurl'))
    for s in 'LR':
        wing(s, up=g('up') + g(s + 'up'), elbow=g('elbow') + g(s + 'elbow'), fan=g('fan'), sweep=g('sweep'),
             curl=g('curl'))
        lift_body = Vector((0, -g('fwd'), g('lift')))
        ankle = rest_ankle(s, dy=-g('ffwd') - g(s + 'ffwd'), dz=g('fup') + g(s + 'fup')) + lift_body * g('ffollow')
        place_leg(s, ankle, tarsus_pitch=g('tpitch') + g(s + 'tpitch'), toe_pitch=g('toe') + g(s + 'toe'))


ATTACK = [
    (0.00, {}),
    (0.15, {'lift': -0.03, 'pitch': 12, 'hpitch': -8, 'up': 30, 'elbow': 10, 'ffollow': 0.0}),
    (0.32, {'lift': 0.10, 'fwd': 0.06, 'pitch': -14, 'chest': -6, 'hpitch': 10, 'up': -25, 'elbow': -15,
            'sweep': 20, 'curl': 15, 'ffollow': 1.0, 'ffwd': 0.10, 'fup': 0.06, 'tpitch': 40, 'toe': 35}),
    (0.42, {'lift': 0.09, 'fwd': 0.08, 'pitch': -18, 'chest': -8, 'hpitch': 14, 'up': -20, 'elbow': -10,
            'sweep': 25, 'curl': 18, 'ffollow': 1.0, 'ffwd': 0.16, 'fup': 0.10, 'tpitch': 55, 'toe': 45}),
    (0.56, {'lift': 0.0, 'fwd': 0.04, 'pitch': 8, 'up': 20, 'elbow': 8, 'ffwd': 0.04, 'ffollow': 0.0}),
    (0.75, {}),
]
HIT = [
    (0.00, {}),
    (0.10, {'fwd': -0.05, 'lift': 0.02, 'pitch': -14, 'roll': 6, 'hpitch': 35, 'hyaw': 10, 'Lup': 30, 'Rup': -10,
            'elbow': 10, 'fan': 6, 'Lfup': 0.08, 'Lffwd': 0.06, 'Ltpitch': 40, 'Ltoe': 30}),
    (0.30, {'fwd': -0.03, 'lift': 0.01, 'pitch': -8, 'roll': -3, 'hpitch': 25, 'hyaw': -6, 'Lup': 18, 'Rup': 8,
            'Lfup': 0.05, 'Lffwd': 0.04, 'Ltpitch': 25, 'Ltoe': 20}),
    (0.625, {}),
]
DEATH = [
    (0.00, {}),
    (0.20, {'lift': 0.02, 'fwd': -0.02, 'pitch': -14, 'hpitch': 40, 'Lup': 35, 'Rup': 15, 'elbow': 15, 'fan': 8,
            'Lfup': 0.06, 'Ltpitch': 30, 'tlift': 10}),
    (0.45, {'lift': -0.05, 'fwd': 0.02, 'pitch': 10, 'roll': 8, 'hpitch': 10, 'up': 25, 'elbow': 10, 'tlift': -8,
            'ffwd': -0.06, 'tpitch': -20}),
    (0.75, {'lift': -0.15, 'fwd': 0.06, 'pitch': 8, 'hpitch': -50, 'reach': 18, 'up': 0, 'ffwd': -0.14,
            'fup': 0.02, 'tpitch': -70, 'toe': -20, 'tlift': -10}),
    (1.00, {'lift': -0.16, 'fwd': 0.06, 'pitch': 8, 'hpitch': -55, 'reach': 20, 'up': 0, 'ffwd': -0.15,
            'fup': 0.02, 'tpitch': -75, 'toe': -25, 'tlift': -10}),
]


def land(u):
    """Death: lay each wing at belly height (upper arm until the forearm touches, forearm until the fingers do)."""
    if u <= 0:
        return
    belly = mesh_co()[CORE, 2].min() + 0.01
    for s in 'LR':
        fit_down(f'UpperArm_{s}', s, TIPS[s], u, belly)
        fit_down(f'ForeArm_{s}', s, FINGERS[s], u, belly)


def death(t):
    generic(keyed(DEATH, t), t)
    core_floor()
    land(ss((t - 0.5) / 0.35))
    tail_floor()


# Cast (Mind Blast, all tiers): rear up with the wings spread high, head raised, then thrust the head forward at the
# release; the engine scales the clip to the cast time and glows at Socket_Head (cast_focus_socket).
CAST = [
    (0.00, {}),
    (0.25, {'lift': 0.02, 'pitch': -10, 'hpitch': 25, 'up': 35, 'elbow': 15, 'fan': -6, 'tlift': 4}),
    (0.45, {'lift': 0.03, 'pitch': -12, 'hpitch': 30, 'up': 40, 'elbow': 18, 'fan': -8, 'tlift': 5}),
    (0.58, {'lift': 0.0, 'fwd': 0.04, 'pitch': 10, 'hpitch': -10, 'reach': 18, 'up': 15, 'elbow': 5}),
    (0.75, {}),
]
FIDGET = [
    (0.00, {}),
    (0.30, {'hyaw': 45, 'hpitch': 5, 'Lup': 8, 'yaw': 4}),
    (0.70, {'hyaw': 45, 'hpitch': 2, 'Lup': 10, 'yaw': 4}),
    (0.95, {'hyaw': -40, 'hpitch': 4, 'Rup': 10, 'yaw': -4}),
    (1.25, {'hyaw': -38, 'Rup': 8, 'yaw': -3}),
    (1.50, {}),
]


def clip(keys):
    def f(t):
        generic(keyed(keys, t), t)
        core_floor()
        tail_floor()
    return f


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


CLIPS = {'Standing': (1.5, True, standing), 'Walking': (0.75, True, walking), 'Attack': (0.75, False, clip(ATTACK)),
         'Hit': (0.625, False, clip(HIT)), 'Death': (1.0, False, death), 'Fidget': (1.5, False, clip(FIDGET)),
         'Cast': (0.75, False, clip(CAST))}
only = sys.argv[sys.argv.index('--') + 1].split(',') if '--' in sys.argv else list(CLIPS)
for name in only:
    sec, loop, fn = CLIPS[name]
    key_action(name, sec, loop, fn)
    print('CLIP', name, sec, flush=True)
if 'Death' in only:
    key_action('Dead', 1.0, False, lambda t: death(1.0))
json.dump({'fps': FPS, 'walk_stride_m': STRIDE}, open(os.path.join(HERE, 'work', 'anim_info.json'), 'w'))
rig.animation_data.action = bpy.data.actions['Standing'] if 'Standing' in bpy.data.actions else None
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED anim_v1.blend')
