"""Procedural clips for the Giant Toad (quadruped playbook: limbs on IK footholds, every frame checked against the
floor). Native Xeen frames (front only): an idle with a blink, a tongue attack (a thick turquoise tongue shot at the
viewer) and a leap with the front legs spread; there are no walk, hit or death frames, so those follow toad anatomy.

Front legs: two-bone IK (UpperArm + ForeArm) to a wrist target, elbow pole back-out-up carried by the Chest; the Hand
keeps its rest (flat) orientation on the ground. Hind legs: Thigh + Shin two-bone IK to the ankle, knee pole forward-
out-up carried by the Body; the Foot aims at its toe-base target, the Toes stay flat while planted.
Gaits are hops (a toad's locomotion): feet planted in the world while in contact (they slide back in clip space at the
clip's travel speed), the body launches, flies an arc and lands; `stride_length` = travel per cycle.

  Standing  2.0 s loop   breathing, throat pulses twice, small head drift
  Walking   0.8 s loop   short hops, 1.30 m per cycle (1.63 m/s = 195 units/s at scale 120)
  Running   0.73 s loop  long hops, 2.40 m per cycle (3.3 m/s = 393 units/s)
  Attack    1.0 s        rear the head, throat puffs, the tongue shoots at the party (IMPACT 0.42 s) and snaps back
  Hit       0.5 s        jolt back and down, throat squeezed, head ducks
  Death     1.4 s        convulsive leap, flips onto its back, legs twitch and sag
  Dead      held last Death pose
  Fidget    2.0 s        throat puffs, head turns, a short tongue flick
Reads work/anim_base.blend (UV-mapped master) or work/rig_v1.blend, writes work/anim_v1.blend and work/anim_info.json.
"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
src = os.path.join(WORK, 'anim_base.blend')
bpy.ops.wm.open_mainfile(filepath=src if os.path.exists(src) else os.path.join(WORK, 'rig_v1.blend'))
rig = bpy.data.objects['Toad_Rig']; mesh = bpy.data.objects['Toad']
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
FPS = 30
IMPACT = 0.42
SIDES = {'L': 1.0, 'R': -1.0}
TONGUE_HIDDEN = 0.02

for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
P.reset(rig)
pbn = rig.pose.bones
W = rig.matrix_world
REST = {b.name: b.matrix.copy() for b in pbn}
WRIST = {s: pbn[f'Hand_{s}'].head.copy() for s in SIDES}
ELBOW = {s: pbn[f'ForeArm_{s}'].head.copy() for s in SIDES}
ANKLE = {s: pbn[f'Foot_{s}'].head.copy() for s in SIDES}
KNEE = {s: pbn[f'Shin_{s}'].head.copy() for s in SIDES}
TOEB = {s: pbn[f'Toes_{s}'].head.copy() for s in SIDES}
FOOT_LEN = {s: pbn[f'Foot_{s}'].length for s in SIDES}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    """0 outside [a, b], a smooth hump inside."""
    if t <= a or t >= b:
        return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


# ---------------------------------------------------------------- mesh and floor
_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
LIMB = np.array([n.startswith(('Hand', 'Toes', 'Foot', 'ForeArm')) for n in _dom])
CORE = ~LIMB


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    return co @ np.array(W.to_3x3()).T + np.array(W.translation)


def lift_body(dz):
    root = pbn['Body']
    root.matrix = Matrix.Translation(Vector((0, 0, dz))) @ root.matrix
    bpy.context.view_layer.update()


def floor_fit(mode):
    """'lift': raise the whole toad if the core (body, head, thighs, upper arms) sinks under the floor;
    'ground': put the lowest vertex of the whole mesh on the floor (lying poses)."""
    co = mesh_co()
    low = co[:, 2].min() if mode in ('ground', 'lift_all') else co[CORE, 2].min()
    if mode == 'ground' or low < -0.004:
        lift_body(-low + (0.002 if mode == 'ground' else 0.0))


# ---------------------------------------------------------------- posing primitives
def body(forward=0.0, lift=0.0, pitch=0.0, roll=0.0, yaw=0.0, pivot=None):
    """Root offset (forward = toward -Y) and rotation about the body's centre; pitch > 0 raises the front,
    roll > 0 lifts the left side."""
    root = pbn['Body']
    root.matrix = Matrix.Translation(Vector((0, -forward, lift))) @ root.matrix
    bpy.context.view_layer.update()
    c = Vector((0, 0.10 - forward, 0.36 + lift)) if pivot is None else Vector(pivot)
    if yaw:
        P.rotate_world(rig, 'Body', Z, yaw, c)
    if pitch:
        P.rotate_world(rig, 'Body', X, pitch, c)
    if roll:
        P.rotate_world(rig, 'Body', Y, -roll, c)


def spine(chest=0.0, head=0.0, head_yaw=0.0, head_roll=0.0):
    if chest:
        P.rotate_world(rig, 'Chest', X, chest)
    if head:
        P.rotate_world(rig, 'Head', X, head)
    if head_yaw:
        P.rotate_world(rig, 'Head', Z, head_yaw)
    if head_roll:
        P.rotate_world(rig, 'Head', Y, head_roll)


def throat(s):
    b = pbn['Throat']
    b.scale = Vector((1 + 0.6 * s, 1 + 0.3 * s, 1 + 0.9 * s)); bpy.context.view_layer.update()


def tongue(extend, pitch=0.0, curl=0.0, yaw=0.0):
    """extend 0..1 grows the tongue out of the mouth (scale of the whole chain), pitch > 0 aims it up, curl > 0
    bends the tip up."""
    e = TONGUE_HIDDEN + (1.5 - TONGUE_HIDDEN) * max(0.0, min(1.0, extend))   # full reach 1.17 m
    pbn['Tongue1'].scale = Vector((min(1.0, 0.45 + e), e, min(1.0, 0.45 + e)))
    bpy.context.view_layer.update()
    # local rotations only: world-space edits under the non-uniformly scaled Tongue1 decompose into a sheared,
    # exploded scale on its children
    if pitch:
        P.rotate_local(rig, 'Tongue1', 'X', pitch)
    if yaw:
        P.rotate_local(rig, 'Tongue1', 'Z', yaw)
    for i in (2, 3, 4):
        if curl:
            P.rotate_local(rig, f'Tongue{i}', 'X', curl / 3)


def carried(point, bone, rest_bone_matrix):
    """A rest-space point carried by a bone's current transform."""
    return pbn[bone].matrix @ rest_bone_matrix.inverted() @ point


def set_world_rot(name, q):
    b = pbn[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, b.matrix.to_scale()); bpy.context.view_layer.update()


ADJ = {}
LIMB_MASK = {('front', s): np.array([n in (f'Hand_{s}', f'ForeArm_{s}') for n in _dom]) for s in SIDES}
LIMB_MASK.update({('hind', s): np.array([n in (f'Foot_{s}', f'Toes_{s}') for n in _dom]) for s in SIDES})


def front_leg(s, wrist, hand_pitch=0.0, hand_spread=0.0):
    wrist = wrist + Vector((0, 0, ADJ.get(('front', s), 0.0)))
    pole = carried(ELBOW[s] + Vector((SIDES[s] * 0.25, 0.35, 0.25)), 'Chest', REST['Chest'])
    P.two_bone_ik(rig, f'UpperArm_{s}', f'ForeArm_{s}', wrist, pole)
    q = REST[f'Hand_{s}'].to_quaternion()
    if hand_spread:
        q = Quaternion(Z, math.radians(-SIDES[s] * hand_spread)) @ q
    if hand_pitch:
        q = Quaternion(X, math.radians(hand_pitch)) @ q
    set_world_rot(f'Hand_{s}', q)


def hind_leg(s, toeb, heel_lift=0.0, toes_flat=True, toe_pitch=0.0):
    """toeb = toe-base (ball) target; heel_lift = degrees the foot rises about the ball (takeoff)."""
    toeb = toeb + Vector((0, 0, ADJ.get(('hind', s), 0.0)))
    rest_dir = (ANKLE[s] - TOEB[s]).normalized()
    flat = Vector((rest_dir.x, rest_dir.y, 0)).normalized()
    a = math.radians(heel_lift + math.degrees(math.asin(max(-1, min(1, rest_dir.z)))))
    ankle = toeb + (flat * math.cos(a) + Z * math.sin(a)) * FOOT_LEN[s]
    pole = carried(KNEE[s] + Vector((SIDES[s] * 0.55, -0.30, 0.06)), 'Body', REST['Body'])
    P.two_bone_ik(rig, f'Thigh_{s}', f'Shin_{s}', ankle, pole)
    P.aim_bone(rig, f'Foot_{s}', toeb)
    if toes_flat:
        q = REST[f'Toes_{s}'].to_quaternion()
        if toe_pitch:
            q = Quaternion(X, math.radians(toe_pitch)) @ q
        set_world_rot(f'Toes_{s}', q)


def tuck_hind(s, amount):
    """Airborne: blend the leg toward its folded rest pose (amount 1 = rest fold relative to the body)."""
    pass


# ---------------------------------------------------------------- clips
def standing(t, T=2.0):
    ph = t / T
    breathe = math.sin(2 * math.pi * ph)
    body(lift=0.006 * breathe, pitch=0.6 * breathe)
    spine(head=1.2 * math.sin(2 * math.pi * ph + 0.6), head_yaw=2.0 * math.sin(2 * math.pi * ph * 1 + 1.3))
    throat(0.35 * bump(ph, 0.05, 0.30) + 0.35 * bump(ph, 0.55, 0.80))
    tongue(0)
    for s in SIDES:
        front_leg(s, WRIST[s]); hind_leg(s, TOEB[s])


def hop(t, T, D, H, launch=12.0):
    """One hop cycle at phase u = t/T. Contact 0..0.45 (front) / 0..0.52 (hind), flight, landing 0.85 (hands) and
    0.93 (feet). Body world travel p(u): still while planted, launched over 0.35..0.88."""
    u = (t / T) % 1.0
    p = D * ss((u - 0.33) / 0.55)
    off = p - D * u                                     # body offset ahead of the steadily moving actor
    h = H * bump(u, 0.40, 0.92) - 0.035 * bump(u, 0.12, 0.40) - 0.03 * bump(u, 0.86, 1.0)
    pitch = launch * bump(u, 0.30, 0.62) - 0.45 * launch * bump(u, 0.62, 0.95)
    body(forward=off, lift=h, pitch=pitch)
    spine(chest=-0.4 * pitch, head=-0.3 * pitch)
    throat(0.25 * bump(u, 0.85, 1.0))
    tongue(0)
    for s in SIDES:
        # front: planted until 0.45 at world rest (clip: slides back), lands at 0.85 a full cycle ahead
        if u < 0.45:
            w = WRIST[s] + Vector((0, D * u, 0))
            front_leg(s, w)
        elif u >= 0.85:
            w = WRIST[s] + Vector((0, -D * (1 - u), 0))
            front_leg(s, w)
        else:
            k = ss((u - 0.45) / 0.40)
            a = WRIST[s] + Vector((0, D * 0.45, 0)); b = WRIST[s] + Vector((0, -D * 0.15, 0))
            w = a.lerp(b, k) + Vector((0, -0.10 * bump(u, 0.45, 0.85), 0.10 * bump(u, 0.45, 0.85) + H * 0.2 * bump(u, 0.5, 0.8)))
            front_leg(s, w, hand_pitch=25 * bump(u, 0.45, 0.85))
        # hind: toes planted until 0.52 (heel peels from 0.30), airborne, land at 0.93
        if u < 0.52:
            tb = TOEB[s] + Vector((0, D * u, 0))
            hind_leg(s, tb, heel_lift=55 * ss((u - 0.28) / 0.24))
        elif u >= 0.93:
            tb = TOEB[s] + Vector((0, -D * (1 - u), 0))
            hind_leg(s, tb)
        else:
            k = ss((u - 0.52) / 0.41)
            a = TOEB[s] + Vector((0, D * 0.52, 0)); b = TOEB[s] + Vector((0, -D * 0.07, 0))
            tb = a.lerp(b, k) + Vector((0, 0.10 * bump(u, 0.52, 0.75), 0.03 + 0.25 * H * bump(u, 0.52, 0.93)))
            hind_leg(s, tb, heel_lift=55 * (1 - ss((u - 0.55) / 0.30)), toe_pitch=-30 * bump(u, 0.52, 0.80))


def keyed(keys, t):
    """Smoothstep interpolation of parameter dicts keyed at times."""
    keys = sorted(keys, key=lambda k: k[0])
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            k = ss((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            out = {}
            for name in set(a) | set(b):
                va, vb = a.get(name, 0.0), b.get(name, 0.0)
                out[name] = va + (vb - va) * k
            return out
    return dict(keys[-1][1])


def generic(k):
    body(forward=k.get('fwd', 0), lift=k.get('lift', 0), pitch=k.get('pitch', 0), roll=k.get('roll', 0),
         yaw=k.get('yaw', 0))
    spine(chest=k.get('chest', 0), head=k.get('head', 0), head_yaw=k.get('head_yaw', 0))
    throat(k.get('throat', 0))
    tongue(k.get('tongue', 0), pitch=k.get('tpitch', 0), curl=k.get('tcurl', 0))
    for s in SIDES:
        sg = SIDES[s]
        lift = k.get('hands_up', 0)
        w = WRIST[s] + Vector((sg * k.get('hands_out', 0), -k.get('hands_fwd', 0), lift))
        front_leg(s, w, hand_pitch=k.get('hand_pitch', 0))
        hind_leg(s, TOEB[s] + Vector((0, -k.get('feet_fwd', 0), 0)), heel_lift=k.get('heel', 0))


ATTACK = [(0.0, {}), (0.22, {'pitch': 6, 'head': 10, 'throat': 0.9, 'fwd': -0.04, 'heel': 8}),
          (0.36, {'pitch': 8, 'head': 12, 'throat': 1.0, 'fwd': -0.05, 'tongue': 0.05, 'heel': 10}),
          (0.42, {'pitch': 2, 'head': 2, 'throat': 0.2, 'fwd': 0.10, 'tongue': 1.0, 'tpitch': 6, 'heel': 20}),
          (0.52, {'pitch': 1, 'head': 0, 'throat': 0.1, 'fwd': 0.10, 'tongue': 0.95, 'tpitch': 2, 'tcurl': 25,
                  'heel': 16}),
          (0.68, {'pitch': 2, 'head': 3, 'fwd': 0.03, 'tongue': 0.0, 'tcurl': 10}),
          (1.0, {})]
HIT = [(0.0, {}), (0.08, {'fwd': -0.10, 'lift': -0.03, 'pitch': -4, 'head': -12, 'throat': -0.3, 'roll': 4,
                          'hands_out': 0.05}),
       (0.22, {'fwd': -0.07, 'lift': -0.02, 'pitch': -2, 'head': -6, 'throat': -0.2, 'roll': 2}), (0.5, {})]
FIDGET = [(0.0, {}), (0.3, {'throat': 0.8, 'head': 4}), (0.55, {'throat': 0.0, 'head': 2, 'head_yaw': 14}),
          (0.9, {'head_yaw': 16, 'head': 2}), (1.05, {'head_yaw': 4, 'tongue': 0.18, 'tpitch': -8}),
          (1.18, {'head_yaw': 0, 'tongue': 0.0}), (1.45, {'throat': 0.8, 'head': 3}), (1.7, {'throat': 0.0}),
          (2.0, {})]


def death(t):
    """Convulsive leap, flip onto the back (rolling toward the right), legs up, twitch, sag."""
    k = ss(t / 0.35)
    jump = 0.32 * bump(t, 0.0, 0.75)
    roll_deg = -180 * ss((t - 0.18) / 0.55)
    c = Vector((0, 0.10, 0.40 + jump))
    root = pbn['Body']
    root.matrix = Matrix.Translation(Vector((0, 0, jump))) @ root.matrix; bpy.context.view_layer.update()
    P.rotate_world(rig, 'Body', X, 18 * bump(t, 0.0, 0.5), c)
    P.rotate_world(rig, 'Body', Y, -roll_deg, c)
    spine(chest=-8 * k, head=-15 * ss((t - 0.5) / 0.5))
    throat(-0.2 * k + 0.5 * bump(t, 0.9, 1.3))
    tongue(0.35 * ss((t - 0.7) / 0.4), pitch=-20, curl=-20)
    tw = math.sin(2 * math.pi * 7 * t) * bump(t, 0.75, 1.3)
    sag = ss((t - 0.9) / 0.5)
    for s in SIDES:
        sg = SIDES[s]
        # FK: legs splay up/out, then sag sideways
        P.rotate_world(rig, f'UpperArm_{s}', Y, -sg * (45 * k - 20 * sag + 8 * tw))
        P.rotate_world(rig, f'ForeArm_{s}', Y, -sg * (25 * k))
        P.rotate_world(rig, f'Thigh_{s}', X, 25 * k + 10 * tw)
        P.rotate_world(rig, f'Shin_{s}', X, -(30 * k - 25 * sag))
        P.rotate_world(rig, f'Thigh_{s}', Z, -sg * 20 * sag)
    return {}


INFO = {}


def key_action(name, n, fn, loop=False, ground=None, warm=0):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows, core_lows = [], [], []
    for f in range(-warm, n + 1):
        t = ((f % n) / FPS) if loop else max(f, 0) / FPS
        ADJ.clear()
        P.reset(rig); fn(t)
        for _ in range(3):                              # planted or swinging limbs never cut the floor
            co = mesh_co(); moved = False
            for key, mask in LIMB_MASK.items():
                low = co[mask, 2].min()
                if low < -0.008:
                    ADJ[key] = ADJ.get(key, 0.0) - low + 0.002; moved = True
            if not moved:
                break
            P.reset(rig); fn(t)
        if f < 0:
            continue
        if ground is not None:
            floor_fit(ground(t))
        co = mesh_co()
        lows.append(float(co[:, 2].min())); core_lows.append(float(co[CORE, 2].min()))
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in pbn})
    if loop:
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
    act['fps'] = FPS
    rig.animation_data.action = None
    INFO[name] = {'seconds': round(n / FPS, 4), 'frames': n, 'lowest_cm': [round(min(lows) * 100, 2),
                  round(max(lows) * 100, 2)], 'core_lowest_cm': round(min(core_lows) * 100, 2)}
    print('CLIP', name, INFO[name], flush=True)


def main():
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    clips = {
        'Standing': (60, standing, True, lambda t: 'lift'),
        'Walking': (24, lambda t: hop(t, 0.8, 1.30, 0.14, launch=9), True, lambda t: 'lift'),
        'Running': (22, lambda t: hop(t, 22 / FPS, 2.40, 0.30, launch=14), True, lambda t: 'lift'),
        'Attack': (30, lambda t: generic(keyed(ATTACK, t)), False, lambda t: 'lift'),
        'Hit': (15, lambda t: generic(keyed(HIT, t)), False, lambda t: 'lift'),
        'Fidget': (60, lambda t: generic(keyed(FIDGET, t)), False, lambda t: 'lift'),
        'Death': (42, death, False, lambda t: 'ground' if t >= 1.2 else 'lift_all'),
        'Dead': (30, lambda t: death(1.4), False, lambda t: 'ground'),
    }
    for name, (n, fn, loop, ground) in clips.items():
        if only and name not in only:
            continue
        key_action(name, n, fn, loop=loop, ground=ground, warm=0)
    for k, v in (('Walking', 1.30), ('Running', 2.40)):
        if k in INFO: INFO[k]['stride'] = v
    json.dump({'clips': INFO, 'impact': IMPACT}, open(os.path.join(WORK, 'anim_info.json'), 'w'), indent=1)
    P.reset(rig)
    rig.animation_data.action = bpy.data.actions['Standing']
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'anim_v1.blend'))
    print('SAVED anim_v1.blend')


main()
