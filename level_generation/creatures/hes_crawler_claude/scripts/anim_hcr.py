"""Procedural clips for the Acid Crawler (quadruped playbook: legs on IK footholds, every frame checked against the
floor). No native sprite exists; the actions follow the brief (low scuttling arthropod that rears up and spits acid).

Legs: two-bone IK (Femur + Tibia; the ankle ring and the clawed foot ride the Tibia) to a foothold; the knee bends in its
rest plane (pole = knee pushed away from the hip-tip line, transported with the body). Spine: Body (root) -> Thorax ->
Head, Body -> Abdomen -> Tail; `curl` bends the whole chain ventrally (the pill-bug roll), `pitch`/`yaw` per segment.
Sac: a damped spring on the Head's vertical motion (jiggle) plus a squeeze in the spit. Gaits are authored for the
game's speeds (Walk 2.4, Run 4.8 model units/s: hes_acid_crawler 300 / 100, brood 300 / 125, matron 280 / 150 world
units/s; chasing twice that) with an alternating tetrapod (L1 R2 L3 R4 / R1 L2 R3 L4), footholds planned within reach
(after mm6_spi1_claude gait2_spi1.py) and the body lowered so long sweeps stay reachable.

  Standing  2.0 s loop   breathing, sac pulse, mandibles work
  Walking   loop         tetrapod scuttle, stride = 2.4 x clip length
  Running   loop         lower, longer sweep, duty 0.42, stride = 4.8 x clip length
  Attack    1.1 s        rear up on the middle/back legs, front legs up, mandibles spread, head snaps forward and the
                         sac squeezes: the spit leaves Socket_Mouth at IMPACT (0.60 s); settle
  Bite      0.8 s        melee: lunge forward, mandibles snap shut at 0.38 s
  Hit       0.55 s       jolt back and down, legs splay, sac wobbles
  Death     1.6 s        rears, rolls over onto its back (toward its right), legs fold up over the belly, body curls
  Dead      held last Death pose
  Fidget    2.0 s        head sweeps left/right, mandibles clean, front legs tap
Reads work/anim_base.blend (UV-mapped master) or work/rig_v1.blend, writes work/anim_v1.blend and work/anim_info.json."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
src = os.path.join(WORK, 'anim_base.blend')
bpy.ops.wm.open_mainfile(filepath=src if os.path.exists(src) else os.path.join(WORK, 'rig_v1.blend'))
rig = bpy.data.objects['Crawler_Rig']; mesh = bpy.data.objects['Crawler']
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
LEGS = [f'{s}{i}' for s in 'LR' for i in range(1, 5)]
GROUP_A = ('L1', 'R2', 'L3', 'R4')
FLOOR_CLEAR = 0.002
WALK_SPEED, RUN_SPEED = 2.4, 4.8
IMPACT_SPIT, IMPACT_BITE = 0.60, 0.38

P.reset(rig)
W = rig.matrix_world
pbn = rig.pose.bones
REST_TIP = {l: (W @ pbn[f'Tibia_{l}'].tail).copy() for l in LEGS}
REST_KNEE = {l: (W @ pbn[f'Tibia_{l}'].head).copy() for l in LEGS}
REST_HIP = {l: (W @ pbn[f'Femur_{l}'].head).copy() for l in LEGS}
CHAIN = {l: pbn[f'Femur_{l}'].length + pbn[f'Tibia_{l}'].length for l in LEGS}
MIN_RATIO = {l: abs(pbn[f'Femur_{l}'].length - pbn[f'Tibia_{l}'].length) / CHAIN[l] + 0.12 for l in LEGS}
SAC_REST = pbn['Sac'].matrix.copy()


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def side(leg):
    return 1.0 if leg[0] == 'L' else -1.0


# ---------------------------------------------------------------- mesh, floor
_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    return co @ np.array(W.to_3x3()).T + np.array(W.translation)


REST_CO = mesh_co()
TIBIA = {l: _dom == f'Tibia_{l}' for l in LEGS}
# tip target height so that the foot piece's lowest vertex sits FLOOR_CLEAR above the floor
TIP_Z = {l: REST_TIP[l].z - REST_CO[TIBIA[l], 2].min() + FLOOR_CLEAR for l in LEGS}
ATTACH = np.isin(_dom, ('Pods', 'Sacs_F', 'Sacs_M', 'Sacs_R'))   # tier attachments: never floor contacts
NOT_LEG = ~ATTACH & ~(np.char.startswith(_dom.astype(str), 'Tibia') | np.char.startswith(_dom.astype(str), 'Femur'))


# ---------------------------------------------------------------- posing
def body(lift=0.0, forward=0.0, pitch=0.0, roll=0.0, yaw=0.0, side_shift=0.0):
    """Root (Body) offset and rotation about its head; positive pitch raises the front; roll + = toward its left
    side up (rolls onto its right side)."""
    root = pbn['Body']
    root.matrix = Matrix.Translation(Vector((side_shift, -forward, lift))) @ root.matrix
    bpy.context.view_layer.update()
    if yaw:
        P.rotate_world(rig, 'Body', Z, yaw)
    if pitch:
        P.rotate_world(rig, 'Body', X, -pitch)
    if roll:
        P.rotate_world(rig, 'Body', Y, -roll)


def spine(curl=0.0, front_pitch=0.0, head_pitch=0.0, front_yaw=0.0, head_yaw=0.0, rear_pitch=0.0, tail_pitch=0.0,
          rear_yaw=0.0):
    """Segment bends in degrees. curl > 0 bends every joint ventrally (pill-bug roll); *_pitch > 0 lifts that end."""
    for bone, sgn, deg, yaw in (('Thorax', 1, curl * 0.9 - front_pitch, front_yaw),
                                ('Head', 1, curl * 1.1 - head_pitch, head_yaw),
                                ('Abdomen', -1, curl * 0.9 - rear_pitch, rear_yaw),
                                ('Tail', -1, curl * 1.1 - tail_pitch, rear_yaw * 0.6)):
        if deg:
            P.rotate_world(rig, bone, X, sgn * deg)      # forward bones: +X dips the front; rear bones: -X dips the rear
        if yaw:
            P.rotate_world(rig, bone, Z, yaw)


def mandibles(spread):
    """Spread > 0 opens both mandibles outward (about the head's forward axis)."""
    for s in 'LR':
        b = pbn[f'Mandible_{s}']
        fwd = (pbn['Head'].tail - pbn['Head'].head).normalized()
        P.rotate_world(rig, f'Mandible_{s}', fwd, spread * side(s))


def pole_for(leg):
    """Knee pole: the rest knee pushed away from the rest hip-tip line, carried by the leg's parent bone."""
    parent = pbn[f'Femur_{leg}'].parent
    M = (W @ parent.matrix) @ (W @ parent.bone.matrix_local).inverted()
    mid = (REST_HIP[leg] + REST_TIP[leg]) / 2
    pole_rest = REST_KNEE[leg] + (REST_KNEE[leg] - mid).normalized() * 0.25 + Z * 0.08
    return M @ pole_rest


def place_tip(leg, tip):
    P.two_bone_ik(rig, f'Femur_{leg}', f'Tibia_{leg}', tip, pole_for(leg))
    return ((W @ pbn[f'Tibia_{leg}'].tail) - Vector(tip)).length


def fold_leg(leg, raise_deg, fold_deg):
    """Free (FK) leg: femur raised about its outward axis (+ = up), tibia folded in under/over the body."""
    for name, deg in ((f'Femur_{leg}', raise_deg), (f'Tibia_{leg}', -fold_deg)):
        b = pbn[name]
        d = (b.tail - b.head).normalized()
        axis = d.cross(Z)
        if axis.length < 1e-3:
            axis = Vector((0, -side(leg), 0))
        P.rotate_world(rig, name, axis.normalized(), deg)


def floor_fit(ground=False, parts=None):
    co = mesh_co()
    low = co[parts if parts is not None else ~ATTACH, 2].min()
    if low < -0.002 or (ground and low > 0.002):
        root = pbn['Body']
        root.matrix = Matrix.Translation(Vector((0, 0, -low))) @ root.matrix
        bpy.context.view_layer.update()
        return -low
    return 0.0


# ---------------------------------------------------------------- footholds (gait)
def plan(leg, sweep, base):
    """Foothold centre (x, y) for a stance sweep along Y so hip-to-tip stays in [MIN_RATIO, REACH] x chain."""
    hip = REST_HIP[leg] + Vector((0, 0, base))
    foot = REST_TIP[leg]
    best = None
    for r in np.linspace(0.75, 1.05, 31):
        for dy in np.linspace(-0.12, 0.12, 49):
            cx, cy = hip.x + (foot.x - hip.x) * r, foot.y + dy
            ratios = [(Vector((cx, cy + k * sweep, TIP_Z[leg])) - hip).length / CHAIN[leg] for k in np.linspace(-0.5, 0.5, 11)]
            cost = 100 * max(0.0, max(ratios) - 0.95) + 100 * max(0.0, MIN_RATIO[leg] - min(ratios)) + abs(r - 1) * 0.5 + abs(dy) * 2
            if best is None or cost < best[0]:
                best = (cost, cx, cy, min(ratios), max(ratios), r, dy)
    return best


GAITS = {
    # frames at 60 fps, duty, swing lift, body base (crouch), bob, roll, yaw, pitch, sweep target (m), lead
    'Walking': dict(speed=WALK_SPEED, frames=12, duty=0.55, lift=0.05, base=-0.035, bob=0.004, roll=1.5, yaw=1.5,
                    pitch=0.0, lead=0.04),
    'Running': dict(speed=RUN_SPEED, frames=10, duty=0.42, lift=0.065, base=-0.038, bob=0.006, roll=2.0, yaw=1.0,
                    pitch=-1.0, lead=0.03),
}


def gait_pose(p, c, centres, stride):
    P.reset(rig)
    body(lift=c['base'] + c['bob'] * math.cos(4 * math.pi * p) - c['bob'], pitch=c['pitch'],
         roll=c['roll'] * math.sin(2 * math.pi * p), yaw=c['yaw'] * math.sin(2 * math.pi * p))
    spine(front_yaw=-c['yaw'] * 0.8 * math.sin(2 * math.pi * p), rear_yaw=c['yaw'] * math.sin(2 * math.pi * p),
          head_pitch=1.5 * math.sin(4 * math.pi * p))
    mandibles(2.0 * math.sin(2 * math.pi * p))
    miss = 0.0
    s = stride * c['duty']
    for leg in LEGS:
        q = (p + (0.0 if leg in GROUP_A else 0.5) + c['lead'] * (int(leg[1]) - 1)) % 1.0
        cx, cy = centres[leg]
        if q < c['duty']:
            y = cy - s / 2 + s * (q / c['duty']); z = 0.0
        else:
            u = (q - c['duty']) / (1 - c['duty'])
            y = cy + s / 2 - s * ss(u); z = c['lift'] * math.sin(math.pi * u) ** 0.8
        miss = max(miss, place_tip(leg, Vector((cx, y, TIP_Z[leg] + z))))
    return miss


# ---------------------------------------------------------------- keyed actions
def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6))
            return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * u for k in set(a) | set(b)}
    return dict(keys[-1][1])


def generic(k, planted=True):
    """Keyed body/spine pose; feet on their rest footholds (offset by splay, front legs free when front_up > 0)."""
    P.reset(rig)
    body(lift=k.get('lift', 0.0), forward=k.get('forward', 0.0), pitch=k.get('pitch', 0.0), roll=k.get('roll', 0.0),
         yaw=k.get('yaw', 0.0))
    spine(curl=k.get('curl', 0.0), front_pitch=k.get('front_pitch', 0.0), head_pitch=k.get('head_pitch', 0.0),
          head_yaw=k.get('head_yaw', 0.0), front_yaw=k.get('front_yaw', 0.0), rear_pitch=k.get('rear_pitch', 0.0),
          tail_pitch=k.get('tail_pitch', 0.0))
    mandibles(k.get('mand', 0.0))
    for leg in LEGS:
        n = int(leg[1])
        if n == 1 and k.get('front_up', 0.0) > 0:
            fold_leg(leg, k['front_up'], k.get('front_fold', 0.0))
            continue
        foot = REST_TIP[leg].copy(); foot.z = TIP_Z[leg]
        out = Vector((foot.x, 0, 0)).normalized()
        foot += out * k.get('splay', 0.0)
        foot.y += k.get('feet_fwd', 0.0) * (1.0 if n <= 2 else 0.5)
        if n == 1:
            foot += Vector((0, -k.get('tap_fwd', 0.0), k.get('tap', 0.0) * (k.get('tap_l', 1.0) if leg[0] == 'L' else k.get('tap_r', 1.0))))
        place_tip(leg, foot)


ATTACK = [  # rear and spit
    (0.00, {}),
    (0.30, {'lift': 0.03, 'pitch': 14, 'front_pitch': 10, 'head_pitch': 6, 'front_up': 35, 'front_fold': 25, 'mand': 22,
            'feet_fwd': 0.02, 'rear_pitch': -3, 'sac': 0.15}),
    (0.50, {'lift': 0.04, 'pitch': 18, 'front_pitch': 14, 'head_pitch': 12, 'front_up': 42, 'front_fold': 30,
            'mand': 30, 'feet_fwd': 0.02, 'rear_pitch': -4, 'sac': 0.18}),
    (IMPACT_SPIT, {'lift': 0.03, 'pitch': 12, 'forward': 0.04, 'front_pitch': 4, 'head_pitch': -8, 'front_up': 38,
                   'front_fold': 28, 'mand': 34, 'feet_fwd': 0.02, 'sac': -0.25}),
    (0.75, {'lift': 0.02, 'pitch': 8, 'forward': 0.03, 'front_pitch': 2, 'head_pitch': -4, 'front_up': 20,
            'front_fold': 15, 'mand': 16, 'sac': -0.1}),
    (1.10, {}),
]
BITE = [
    (0.00, {}),
    (0.22, {'lift': 0.01, 'pitch': 6, 'forward': -0.04, 'head_pitch': 8, 'mand': 34, 'feet_fwd': -0.01}),
    (IMPACT_BITE, {'lift': -0.01, 'pitch': -5, 'forward': 0.08, 'head_pitch': -6, 'mand': -6, 'feet_fwd': 0.03}),
    (0.52, {'lift': -0.005, 'pitch': -3, 'forward': 0.06, 'head_pitch': -3, 'mand': 6, 'feet_fwd': 0.02}),
    (0.80, {}),
]
HIT = [
    (0.00, {}),
    (0.12, {'lift': -0.025, 'forward': -0.05, 'pitch': 7, 'splay': 0.025, 'mand': 18, 'curl': 6, 'head_pitch': 6}),
    (0.32, {'lift': -0.015, 'forward': -0.035, 'pitch': 4, 'splay': 0.015, 'mand': 10, 'curl': 3}),
    (0.55, {}),
]
FIDGET = [
    (0.00, {}),
    (0.35, {'head_yaw': 14, 'front_yaw': 6, 'mand': 14, 'tap': 0.04, 'tap_l': 1.0, 'tap_r': 0.0, 'head_pitch': 3}),
    (0.60, {'head_yaw': 12, 'front_yaw': 5, 'mand': 2, 'tap': 0.0}),
    (0.95, {'head_yaw': -14, 'front_yaw': -6, 'mand': 16, 'tap': 0.04, 'tap_l': 0.0, 'tap_r': 1.0, 'head_pitch': 2}),
    (1.25, {'head_yaw': -10, 'front_yaw': -4, 'mand': 4, 'tap': 0.0}),
    (1.55, {'head_yaw': 0, 'mand': 12, 'head_pitch': -4}),
    (2.00, {}),
]
DEATH = [  # roll over onto the back (toward the right side), legs fold over the belly, the body curls a little
    (0.00, dict(lift=0.0, pitch=0, roll=0, curl=0, femur=0, tibia=0, mand=0, sac=0.0)),
    (0.25, dict(lift=0.03, pitch=16, roll=8, curl=-4, femur=25, tibia=10, mand=30, sac=0.2)),
    (0.70, dict(lift=0.0, pitch=6, roll=110, curl=6, femur=40, tibia=45, mand=20, sac=0.1)),
    (1.10, dict(lift=0.0, pitch=0, roll=176, curl=12, femur=58, tibia=80, mand=8, sac=-0.1)),
    (1.35, dict(lift=0.0, pitch=0, roll=181, curl=14, femur=62, tibia=88, mand=4, sac=-0.15)),
    (1.60, dict(lift=0.0, pitch=0, roll=180, curl=14, femur=64, tibia=90, mand=3, sac=-0.15)),
]


def death(t):
    k = keyed(DEATH, t)
    P.reset(rig)
    for leg in LEGS:
        n = int(leg[1])
        fold_leg(leg, k['femur'] * (1.0 - 0.06 * (n - 1)), k['tibia'] * (1.0 + 0.05 * math.sin(n * 1.7)))
    mandibles(k['mand'])
    spine(curl=k['curl'])
    body(lift=k['lift'], pitch=k['pitch'], roll=k['roll'])
    if 'Pods' in pbn:                                  # the brood's egg pods are crushed as it rolls onto its back
        s = 1.0 - 0.65 * ss((k['roll'] - 60) / 90)
        pbn['Pods'].scale = (s, s, s)
        bpy.context.view_layer.update()
    return k


def standing(t):
    u = t / 2.0
    k = {'lift': 0.004 * math.sin(2 * math.pi * u), 'curl': 1.0 * math.sin(2 * math.pi * u),
         'mand': 6 * max(0.0, math.sin(2 * math.pi * u * 2)), 'head_pitch': 1.5 * math.sin(2 * math.pi * u + 1)}
    generic(k)
    return {'sac': 0.06 * math.sin(2 * math.pi * u * 2)}


# ---------------------------------------------------------------- sac spring
class Sac:
    """Damped spring on the throat sac: its offset lags the Head's motion (jiggle); `squeeze` scales it."""
    def __init__(self, fps):
        self.dt = 1.0 / fps; self.x = Vector(); self.v = Vector(); self.prev = None

    def apply(self, squeeze=0.0):
        head = pbn['Head']
        anchor = (W @ head.matrix) @ (W @ head.bone.matrix_local).inverted() @ (W @ pbn['Sac'].bone.head_local)
        if self.prev is not None:
            k, c = 520.0, 16.0                           # ~3.6 Hz, damping ratio ~0.35
            self.v += (-self.x * k - self.v * c) * self.dt
            self.x += self.v * self.dt - (anchor - self.prev) * 0.25
        self.prev = anchor.copy()
        self.x = Vector([max(-0.01, min(0.01, a)) for a in self.x])
        sac = pbn['Sac']
        s = 1.0 + squeeze
        M = sac.matrix.copy()
        loc, rot, _ = M.decompose()
        sac.matrix = Matrix.LocRotScale(loc + self.x, rot, Vector((s, s * (1 + 0.2 * squeeze), s)))
        bpy.context.view_layer.update()


INFO = {}


def key_action(name, n, fps, fn, loop=False, ground=None, warm=0):
    """Pose every frame with fn(t) (t = frame / fps; loops wrap), simulate the sac, apply the floor rule, key it."""
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    sac = Sac(fps)
    frames = list(range(-warm, n + 1))
    poses, lows, body_lows, miss = [], [], [], 0.0
    for f in frames:
        t = ((f % n) / fps) if loop else max(f, 0) / fps
        out = fn(t) or {}
        if 'miss' in out:
            miss = max(miss, out['miss'])
        sac.apply(out.get('sac', 0.0))
        if f < 0:
            continue
        if ground is not None:
            g = ground(t)
            if g == 'ground':
                floor_fit(ground=True)
            elif g == 'lift':
                floor_fit()
        co = mesh_co()
        lows.append(float(co[~ATTACH, 2].min())); body_lows.append(float(co[NOT_LEG, 2].min()))
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in pbn})
    if loop:                                           # the last key repeats the first exactly
        poses[-1] = poses[0]
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, pose in enumerate(poses):
        for b in pbn:
            q, loc, sc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc; b.scale = sc
            b.keyframe_insert('rotation_quaternion', frame=f)
            b.keyframe_insert('location', frame=f)
            b.keyframe_insert('scale', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    act['fps'] = fps
    rig.animation_data.action = None
    INFO[name] = {'seconds': n / fps, 'frames': n, 'fps': fps, 'lowest_cm': [round(min(lows) * 100, 2),
                  round(max(lows) * 100, 2)], 'body_lowest_cm': round(min(body_lows) * 100, 2),
                  'tip_miss_mm': round(miss * 1000, 1)}
    print('CLIP', name, INFO[name], flush=True)
    return act


def main():
    for b in pbn:
        b.rotation_mode = 'QUATERNION'
    # gaits at 60 fps
    for name, c in GAITS.items():
        T = c['frames'] / 60.0
        stride = c['speed'] * T
        centres = {}
        for leg in LEGS:
            cost, cx, cy, lo, hi, r, dy = plan(leg, stride * c['duty'], c['base'])
            centres[leg] = (cx, cy)
            print(f'PLAN {name} {leg}: r {r:.2f} dy {dy:+.3f} hip-tip {lo:.2f}-{hi:.2f} of chain cost {cost:.2f}', flush=True)
        key_action(name, c['frames'], 60, lambda t, c=c, centres=centres, stride=stride:
                   {'miss': gait_pose((t * 60 / c['frames']) % 1.0, c, centres, stride),
                    'sac': 0.04 * math.sin(4 * math.pi * t * 60 / c['frames'])},
                   loop=True, ground=lambda t: 'lift', warm=c['frames'] * 2)
        INFO[name]['stride'] = round(stride, 4); INFO[name]['sweep'] = round(stride * c['duty'], 4)
    key_action('Standing', 60, 30, standing, loop=True, ground=lambda t: 'lift', warm=60)
    key_action('Attack', 33, 30, lambda t: (generic(k := keyed(ATTACK, t)), {'sac': k.get('sac', 0.0)})[1],
               ground=lambda t: 'lift', warm=6)
    key_action('Bite', 24, 30, lambda t: (generic(keyed(BITE, t)), {})[1], ground=lambda t: 'lift', warm=6)
    key_action('Hit', 17, 30, lambda t: (generic(keyed(HIT, t)), {'sac': 0.0})[1], ground=lambda t: 'lift', warm=6)
    key_action('Fidget', 60, 30, lambda t: (generic(keyed(FIDGET, t)), {})[1], ground=lambda t: 'lift', warm=6)
    key_action('Death', 48, 30, lambda t: {'sac': death(t)['sac']},
               ground=lambda t: 'ground' if t >= 0.3 else 'lift', warm=6)
    key_action('Dead', 30, 30, lambda t: {'sac': death(1.6)['sac']}, ground=lambda t: 'ground', warm=30)
    json.dump({'clips': INFO, 'walk_speed': WALK_SPEED, 'run_speed': RUN_SPEED, 'impact_spit': IMPACT_SPIT,
               'impact_bite': IMPACT_BITE}, open(os.path.join(WORK, 'anim_info.json'), 'w'), indent=1)
    P.reset(rig)
    rig.animation_data.action = bpy.data.actions['Standing']
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'anim_v1.blend'))
    print('SAVED anim_v1.blend')


main()
