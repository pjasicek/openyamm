"""Procedural clips for the Xeen mantis ants and the Lava Roach (quadruped playbook, segmented creatures: rigid chitin
pieces on their own bones, legs on IK footholds, every frame checked against the floor). Native Xeen frames (front
only, Darkside 010.mon / 010.att): an idle in which the raised hooks bob and the head shifts; the attack: att 1 both
raptorial arms thrown out wide with the scythes open, att 2 the scythes snapped together in front of the body (the
blow), att 3 the arms folded back. No walk, hit or death frames: those follow insect anatomy.

Legs: two-bone IK (Thigh + Shin) to the ankle target, the knee pole up and out (a crouching frog's knees) carried by
the Body; the Foot keeps its rest orientation (flat on the floor) plus a toe pitch in swing. Gait: trot on diagonal
pairs (L1 + R2 / R1 + L2). Arms are FK: the upper arm turns about the shoulder ball (sp raises it sideways, fw swings
it forward), the forearm about the elbow hinge (el > 0 opens the elbow), the hook about the wrist hinge (hk > 0 opens
the hook away from the forearm). The Mouth bone (the yellow bead ring) scales to open the radial mouth.
Floor rules every frame: the core (body, thorax, head, abdomen) is lifted when it sinks ('ground' mode puts the lowest
core point on the floor for lying poses); a foot whose vertices dip under the floor gets its target raised; hooks
and antennae are kept above the floor by lifting the whole creature.

  Standing  2.0 s loop   breathing, hooks bob, antennae sway, mouth pulses
  Walking   0.8 s loop   diagonal trot, 0.50 m per cycle
  Running   0.5 s loop   same, lower and leaning, 0.80 m per cycle
  Attack    1.0 s        rears, arms thrown out wide (att 1), scythes snap together forward and down (att 2): IMPACT
  Hit       0.5 s        jolts back, arms flinch up, head back
  Death     1.5 s        rears, topples backward onto its back, legs curl up, arms fold
  Dead      1.0 s        Death's last pose
  Fidget    2.0 s        head tilts, the left hook wipes the mouth and an antenna, antennae twitch
Reads work/anim_base.blend (UV master), writes work/anim_v1.blend and work/anim_info.json.
Usage: anim_mantis.py [clip ...]  (a partial rerun keeps the other clips of anim_v1.blend)"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
_only = '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 1
_src = 'anim_v1.blend' if _only and os.path.exists(os.path.join(WORK, 'anim_v1.blend')) else 'anim_base.blend'
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, _src))
rig = bpy.data.objects['Mantis_Rig']; mesh = bpy.data.objects['Mantis']
J = json.load(open(os.path.join(WORK, 'joints.json')))
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
FPS = 30
SIDES = {'L': 1.0, 'R': -1.0}
LEGS = ('L1', 'R1', 'L2', 'R2')
PAIR_A = ('L1', 'R2')

if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
P.reset(rig)
pbn = rig.pose.bones
W = rig.matrix_world
REST = {b.name: b.matrix.copy() for b in pbn}
ANKLE = {k: pbn[f'Foot_{k}'].head.copy() for k in LEGS}
KNEE = {k: pbn[f'Shin_{k}'].head.copy() for k in LEGS}
HIP = {k: pbn[f'Thigh_{k}'].head.copy() for k in LEGS}
HIPC = pbn['Body'].head.copy()


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    if t <= a or t >= b:
        return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] for v in mesh.data.vertices])
FOOTMASK = {k: _dom == f'Foot_{k}' for k in LEGS}
LEGMASK = {k: np.isin(_dom, (f'Thigh_{k}', f'Shin_{k}', f'Foot_{k}')) for k in LEGS}
CORE = np.isin(_dom, ('Body', 'Thorax', 'Head', 'Abdomen', 'Mouth'))
UPPER = ~np.isin(_dom, [f'{n}_{k}' for n in ('Thigh', 'Shin', 'Foot') for k in LEGS])


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    return co @ np.array(W.to_3x3()).T + np.array(W.translation)


REST_CO = mesh_co()
FOOT_DROP = {k: float(REST_CO[FOOTMASK[k], 2].min()) for k in LEGS}


def move_root(d):
    root = pbn['Body']
    root.matrix = Matrix.Translation(d) @ root.matrix
    bpy.context.view_layer.update()


def floor_fit(mode):
    co = mesh_co()
    low = co[UPPER, 2].min()
    if mode == 'ground':
        move_root(Vector((0, 0, -co[CORE, 2].min() + 0.003)))
    elif low < -0.004:
        move_root(Vector((0, 0, -low)))


def carried(point, bone):
    return pbn[bone].matrix @ REST[bone].inverted() @ point


def set_world_rot(name, q):
    b = pbn[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, b.matrix.to_scale()); bpy.context.view_layer.update()


def hinge_rotate(parent, child, deg):
    """Rotate `child` about the hinge normal of (parent dir x child dir); deg > 0 opens the joint."""
    a = pbn[parent]; b = pbn[child]
    u = (a.tail - a.head).normalized(); f = (b.tail - b.head).normalized()
    n = u.cross(f)
    if n.length < 1e-4 or not deg:
        return
    P.rotate_world(rig, child, n.normalized(), deg)


def body(fwd=0.0, lift=0.0, lean=0.0, roll=0.0, yaw=0.0, pivot=None):
    """lean > 0 tips the upright body forward (toward -Y), roll > 0 lowers the left side."""
    move_root(Vector((0, -fwd, lift)))
    c = HIPC + Vector((0, -fwd, lift)) if pivot is None else Vector(pivot)
    if yaw:
        P.rotate_world(rig, 'Body', Z, yaw, c)
    if lean:
        P.rotate_world(rig, 'Body', X, lean, c)
    if roll:
        P.rotate_world(rig, 'Body', Y, roll, c)


def upper(tlean=0.0, tyaw=0.0, troll=0.0, hpitch=0.0, hyaw=0.0, hroll=0.0, ab=0.0, ab_roll=0.0, mouth=0.0):
    """tlean > 0 bends the thorax forward; hpitch > 0 nods the head down; ab > 0 swings the abdomen tip back."""
    if tlean: P.rotate_world(rig, 'Thorax', X, tlean)
    if tyaw: P.rotate_world(rig, 'Thorax', Z, tyaw)
    if troll: P.rotate_world(rig, 'Thorax', Y, troll)
    if hpitch: P.rotate_world(rig, 'Head', X, hpitch)
    if hyaw: P.rotate_world(rig, 'Head', Z, hyaw)
    if hroll: P.rotate_world(rig, 'Head', Y, hroll)
    if ab: P.rotate_world(rig, 'Abdomen', X, ab)
    if ab_roll: P.rotate_world(rig, 'Abdomen', Y, ab_roll)
    if mouth:
        m = pbn['Mouth']; m.scale = Vector((1 + mouth, 1 + mouth, 1 + mouth)); bpy.context.view_layer.update()


def antennae(t, amp=1.0, lift=0.0, period=2.0):
    """Sway with whole cycles per `period` (the loop length of looping clips), so loops close."""
    for k, s in enumerate(SIDES):
        P.rotate_local(rig, f'Antenna_{s}', 'X', amp * 7 * math.sin(2 * math.pi * 2 * t / period + 1.9 * k) + lift)
        P.rotate_local(rig, f'Antenna_{s}', 'Z', amp * 5 * math.sin(2 * math.pi * t / period + k))


def _dir(az, el, sg):
    """Unit direction: az from outward (0) toward forward (+90) in the horizontal plane, el elevation (degrees)."""
    a, e = math.radians(az), math.radians(el)
    return Vector((sg * math.cos(e) * math.cos(a), -math.cos(e) * math.sin(a), math.sin(e)))


def _angles(v, sg):
    v = v.normalized()
    return math.degrees(math.atan2(-v.y, sg * v.x)), math.degrees(math.asin(max(-1, min(1, v.z))))


ARM_REST = {}
for _s, _sg in SIDES.items():
    _u = pbn[f'UpperArm_{_s}']; _f = pbn[f'ForeArm_{_s}']
    ARM_REST[_s] = (_angles(_u.tail - _u.head, _sg), _angles(_f.tail - _f.head, _sg))


def arm(s, uaz=0.0, uel=0.0, faz=0.0, fel=0.0, hk=0.0):
    """Arm by directions in the thorax frame, as offsets from the rest angles: the upper arm (uaz, uel) and the
    forearm (faz, fel); az > 0 swings toward the front, el > 0 raises. hk > 0 opens the hook from the forearm."""
    sg = SIDES[s]
    (ua0, ue0), (fa0, fe0) = ARM_REST[s]
    dq = (pbn['Thorax'].matrix @ REST['Thorax'].inverted()).to_quaternion()
    for bone, az, el in ((f'UpperArm_{s}', ua0 + uaz, ue0 + uel), (f'ForeArm_{s}', fa0 + faz, fe0 + fel)):
        b = pbn[bone]
        L = (b.tail - b.head).length
        P.aim_bone(rig, bone, W @ (b.head + (dq @ _dir(az, el, sg)) * L))
    hinge_rotate(f'ForeArm_{s}', f'Hook_{s}', hk)


ADJ = {}


def leg(k, off=Vector(), toe=0.0, carry=0.0, curl=0.0):
    """off: target offset in world; carry 1 places the target in rest body space carried by the Body (lying poses);
    curl pulls the foot toward the hip and up (a dead insect's folded legs)."""
    sg = SIDES[k[0]]
    target = ANKLE[k] - Vector((0, 0, FOOT_DROP[k])) + off
    if curl:
        target = target.lerp(HIP[k] + Vector((sg * 0.06, 0, -0.02)), 0.55 * curl)
    if carry:
        target = target.lerp(carried(target, 'Body'), carry)
    target = target + Vector((0, 0, ADJ.get(k, 0.0)))
    pole = carried(KNEE[k] + Vector((sg * 0.30, 0.0, 0.30)), 'Body')
    P.two_bone_ik(rig, f'Thigh_{k}', f'Shin_{k}', target, pole)
    q = REST[f'Foot_{k}'].to_quaternion()
    if carry:
        dq = (pbn['Body'].matrix @ REST['Body'].inverted()).to_quaternion()
        q = Quaternion().slerp(dq, carry) @ q
    fd = (pbn[f'Foot_{k}'].tail - pbn[f'Foot_{k}'].head)
    if toe or curl:
        ax = fd.cross(Z)
        if ax.length > 1e-4:
            q = Quaternion(ax.normalized(), math.radians(toe + 60 * curl)) @ q
    set_world_rot(f'Foot_{k}', q)


# ---------------------------------------------------------------- locomotion
def limb_cycle(p, duty, half, lift):
    if p < duty:
        q = p / duty
        return -half + 2 * half * q, 0.0, 0.0
    s = (p - duty) / (1 - duty)
    k = ss(s)
    return half - 2 * half * k, lift * math.sin(math.pi * s), s


def gait(t, T, D, duty, lift, bob, sway, lean=0.0, low=0.0):
    u = (t / T) % 1.0
    body(lift=-low + bob * math.cos(4 * math.pi * u), lean=lean + 1.0 * math.cos(4 * math.pi * u),
         roll=sway * math.sin(2 * math.pi * u), yaw=0.5 * sway * math.sin(2 * math.pi * u))
    upper(tlean=1.5 * math.sin(4 * math.pi * u + 0.6), tyaw=-0.8 * sway * math.sin(2 * math.pi * u),
          hpitch=-0.5 * lean + 1.5 * math.sin(4 * math.pi * u + 1.2), hyaw=-1.0 * sway * math.sin(2 * math.pi * u),
          ab=2.5 * math.sin(4 * math.pi * u + 1.8))
    antennae(t, 1.2, lift=-6 * math.sin(4 * math.pi * u), period=T)
    for s, sg in SIDES.items():
        ph = 2 * math.pi * u + (0 if s == 'L' else math.pi)
        arm(s, uaz=4 * math.sin(ph), uel=3 * math.sin(ph + 0.5), faz=5 * math.sin(ph + 1.0), fel=-3 + 3 * math.sin(ph + 1.0), hk=2 * math.sin(ph + 1.5))
    half = D * duty / 2
    for k in LEGS:
        ph = (u + (0.0 if k in PAIR_A else 0.5)) % 1.0
        y, h, sw = limb_cycle(ph, duty, half, lift)
        leg(k, Vector((0, y, h)), toe=-25 * math.sin(math.pi * sw))


# ---------------------------------------------------------------- keyed actions
def keyed(keys, t):
    """A per-side key (l_sp) missing from a key takes that key's shared value (sp), not 0."""
    keys = sorted(keys, key=lambda k: k[0])
    sided = {n for _, d in keys for n in d if n[:2] in ('l_', 'r_')}
    keys = [(t0, {**{n: d.get(n[2:], 0.0) for n in sided}, **d}) for t0, d in keys]
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            k = ss((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return {n: a.get(n, 0.0) + (b.get(n, 0.0) - a.get(n, 0.0)) * k for n in set(a) | set(b)}
    return dict(keys[-1][1])


def generic(k, t=0.0):
    body(fwd=k.get('fwd', 0), lift=k.get('lift', 0), lean=k.get('lean', 0), roll=k.get('roll', 0),
         yaw=k.get('yaw', 0), pivot=k.get('pivot'))
    upper(tlean=k.get('tlean', 0), tyaw=k.get('tyaw', 0), troll=k.get('troll', 0), hpitch=k.get('hpitch', 0),
          hyaw=k.get('hyaw', 0), hroll=k.get('hroll', 0), ab=k.get('ab', 0), ab_roll=k.get('ab_roll', 0),
          mouth=k.get('mouth', 0))
    antennae(t, k.get('ant_amp', 1.0), lift=k.get('ant', 0))
    for s in SIDES:
        pre = s.lower() + '_'
        g = lambda n: k.get(pre + n, k.get(n, 0.0))
        arm(s, uaz=g('uaz'), uel=g('uel'), faz=g('faz'), fel=g('fel'), hk=g('hk'))
    carry = k.get('carry', 0.0); curl = k.get('curl', 0.0); follow = k.get('follow', 0.0)
    for leg_k in LEGS:
        off = Vector((0, -k.get('fwd', 0) * follow, 0))
        leg(leg_k, off, carry=carry, curl=curl)


# Attack (native att 1 -> att 2 -> att 3): rear and open both arms wide (scythes open), then lunge a little and snap
# the scythes forward, inward and down at the party; hold; fold back.
ATTACK = [(0.0, {}),
          (0.30, {'lean': -8, 'lift': 0.03, 'fwd': -0.04, 'tlean': -6, 'hpitch': -8, 'uaz': 18, 'uel': 52,
                  'faz': -40, 'fel': -30, 'hk': 20, 'mouth': 0.15, 'ab': 6, 'ant': -10}),
          (0.34, {'lean': -9, 'lift': 0.035, 'fwd': -0.05, 'tlean': -7, 'hpitch': -9, 'uaz': 20, 'uel': 57,
                  'faz': -43, 'fel': -32, 'hk': 25, 'mouth': 0.18, 'ab': 7, 'ant': -12}),
          (0.50, {'lean': 12, 'lift': 0.0, 'fwd': 0.07, 'tlean': 10, 'hpitch': 8, 'uaz': 80, 'uel': 35,
                  'faz': 70, 'fel': -40, 'hk': -25, 'mouth': 0.30, 'ab': -4, 'ant': 6}),
          (0.62, {'lean': 11, 'fwd': 0.065, 'tlean': 9, 'hpitch': 8, 'uaz': 78, 'uel': 33, 'faz': 68, 'fel': -42,
                  'hk': -27, 'mouth': 0.2, 'ab': -3}),
          (0.82, {'lean': 3, 'fwd': 0.02, 'tlean': 2, 'hpitch': 2, 'uaz': 25, 'uel': 10, 'faz': 20, 'fel': -12,
                  'hk': -8, 'mouth': 0.05}),
          (1.0, {})]
HIT = [(0.0, {}),
       (0.10, {'fwd': -0.06, 'lift': 0.015, 'lean': -10, 'tlean': -8, 'hpitch': -14, 'hroll': 6, 'roll': 4,
               'uel': 22, 'uaz': -8, 'fel': 12, 'faz': -15, 'hk': 15, 'ab': 8, 'mouth': 0.12, 'ant': -15}),
       (0.24, {'fwd': -0.03, 'lean': -4, 'tlean': -3, 'hpitch': -5, 'hroll': 2, 'roll': 2, 'uel': 8, 'fel': 4,
               'faz': -5, 'hk': 5, 'ab': 3}),
       (0.5, {})]
FIDGET = [(0.0, {}),
          (0.25, {'hpitch': 6, 'hyaw': 10, 'hroll': -6, 'l_uaz': 35, 'l_uel': 5, 'l_faz': 45, 'l_fel': -15, 'l_hk': -5}),
          (0.45, {'hpitch': 10, 'hyaw': 12, 'hroll': -8, 'l_uaz': 60, 'l_uel': 10, 'l_faz': 85, 'l_fel': -30,
                  'l_hk': -10, 'mouth': 0.12}),
          (0.60, {'hpitch': 8, 'hyaw': 8, 'hroll': -6, 'l_uaz': 55, 'l_uel': 18, 'l_faz': 80, 'l_fel': -18,
                  'l_hk': -5, 'mouth': 0.06}),
          (0.75, {'hpitch': 10, 'hyaw': 12, 'hroll': -8, 'l_uaz': 60, 'l_uel': 10, 'l_faz': 85, 'l_fel': -30,
                  'l_hk': -10, 'mouth': 0.12}),
          (1.0, {'hpitch': -4, 'hyaw': -4, 'hroll': 4, 'l_uaz': 15, 'l_uel': 5, 'l_faz': 15, 'ant': -8}),
          (1.25, {'hpitch': -6, 'hyaw': -12, 'hroll': 6, 'tyaw': -4, 'r_uel': 8, 'r_faz': -10, 'ant': 8}),
          (1.5, {'hpitch': -3, 'hyaw': -8, 'hroll': 3, 'tyaw': -2, 'ab': 4}),
          (2.0, {})]
DEATH = [(0.0, {}),
         (0.22, {'lean': -14, 'lift': 0.05, 'tlean': -10, 'hpitch': -18, 'uaz': 0, 'uel': 35, 'faz': -25,
                 'fel': -10, 'hk': 20, 'mouth': 0.3, 'ab': 10, 'ant': -20}),
         (0.55, {'lean': -45, 'roll': 10, 'tlean': -8, 'hpitch': -10, 'uaz': 10, 'uel': 25, 'faz': -10, 'fel': -10,
                 'hk': 10, 'mouth': 0.15, 'ab': 15, 'carry': 0.6, 'curl': 0.4, 'fwd': 0.08}),
         (0.95, {'lean': -92, 'roll': 14, 'tlean': -4, 'hpitch': -20, 'hroll': 15, 'uaz': 45, 'uel': 10, 'faz': 90,
                 'fel': -50, 'hk': -20, 'mouth': -0.1, 'ab': 8, 'carry': 1.0, 'curl': 1.0, 'ant': 20, 'fwd': 0.2}),
         (1.2, {'lean': -95, 'roll': 16, 'tlean': -2, 'hpitch': -22, 'hroll': 18, 'uaz': 50, 'uel': 5, 'faz': 100,
                'fel': -60, 'hk': -30, 'mouth': -0.1, 'ab': 6, 'carry': 1.0, 'curl': 1.15, 'ant': 25, 'ant_amp': 0.3,
                'fwd': 0.22}),
         (1.5, {'lean': -95, 'roll': 16, 'tlean': -2, 'hpitch': -22, 'hroll': 18, 'uaz': 50, 'uel': 5, 'faz': 100,
                'fel': -60, 'hk': -30, 'mouth': -0.1, 'ab': 6, 'carry': 1.0, 'curl': 1.15, 'ant': 25, 'ant_amp': 0.0,
                'fwd': 0.22})]


def death(t):
    k = keyed(DEATH, t)
    if k.get('lean', 0) < -20:     # topple about the rear edge of the abdomen
        k['pivot'] = (0.0, 0.25 - k.get('fwd', 0), 0.08 + k.get('lift', 0))
    generic(k, t if t < 1.5 else 1.5)


INFO = {}


def key_action(name, n, fn, loop=False, ground=None):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows, core_lows, tips, lowgrp = [], [], [], [], []
    for f in range(n + 1):
        t = ((f % n) / FPS) if loop else f / FPS
        ADJ.clear()
        mode = ground(t) if ground else 'lift'
        for _ in range(4):
            P.reset(rig); fn(t); floor_fit(mode)
            co = mesh_co(); moved = False
            for k, mask in LEGMASK.items():
                low = co[mask, 2].min()
                if low < -0.006:
                    ADJ[k] = ADJ.get(k, 0.0) - low + 0.002; moved = True
            if not moved:
                break
        co = mesh_co()
        lows.append(float(co[:, 2].min())); core_lows.append(float(co[CORE, 2].min()))
        lowgrp.append(_dom[int(co[:, 2].argmin())])
        tips.append([tuple(pbn[f'Hook_{s}'].tail) for s in SIDES])
        poses.append({b.name: (b.matrix_basis.copy()) for b in pbn})
    if loop:
        poses[-1] = poses[0]
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, pose in enumerate(poses):
        for b in pbn:
            loc, q, sc = pose[b.name].decompose()
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc; b.scale = sc
            b.keyframe_insert('rotation_quaternion', frame=f)
            b.keyframe_insert('location', frame=f)
            b.keyframe_insert('scale', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    INFO[name] = {'seconds': round(n / FPS, 4), 'frames': n,
                  'lowest_cm': [round(min(lows) * 100, 2), round(max(lows) * 100, 2)],
                  'core_lowest_cm': round(min(core_lows) * 100, 2),
                  'adj': {k: round(v, 3) for k, v in ADJ.items()}, 'lowest_part': lowgrp[int(np.argmin(lows))]}
    if name == 'Attack':
        tipy = np.array([[p[1] for p in fr] for fr in tips]).mean(1)
        tipz = np.array([[p[2] for p in fr] for fr in tips]).mean(1)
        INFO[name]['hook_tip_y'] = [round(v, 3) for v in tipy]
        INFO[name]['hook_tip_z'] = [round(v, 3) for v in tipz]
        sep = np.array([np.linalg.norm(np.array(fr[0]) - np.array(fr[1])) for fr in tips])
        INFO[name]['hook_gap'] = [round(v, 3) for v in sep]
        f_imp = int(np.where(sep <= sep.min() + 0.01)[0][0])   # the scythes snap together: the blow lands
        INFO[name]['impact_frame'] = f_imp; INFO[name]['impact_s'] = round(f_imp / FPS, 3)
    print('CLIP', name, {k: v for k, v in INFO[name].items() if not k.startswith('hook_tip')}, flush=True)


def main():
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    clips = {
        'Standing': (60, lambda t: generic({'lift': 0.005 * math.sin(math.pi * t), 'lean': 0.8 * math.sin(math.pi * t),
                                            'tlean': 1.2 * math.sin(math.pi * t + 0.5),
                                            'hpitch': 1.5 * math.sin(math.pi * t + 0.9),
                                            'hyaw': 3 * math.sin(math.pi * t + 1.4),
                                            'ab': 2.5 * math.sin(math.pi * t + 0.3),
                                            'mouth': 0.06 * bump(t, 0.4, 0.9) + 0.05 * bump(t, 1.3, 1.7),
                                            'l_uel': 3 * math.sin(math.pi * t + 0.2), 'r_uel': 3 * math.sin(math.pi * t + 1.4),
                                            'l_fel': 4 * math.sin(math.pi * t + 0.6), 'r_fel': 4 * math.sin(math.pi * t + 1.8),
                                            'l_hk': 5 * math.sin(math.pi * t + 0.8), 'r_hk': 5 * math.sin(math.pi * t + 2.0)}, t),
                      True, None),
        'Walking': (24, lambda t: gait(t, 0.8, 0.50, 0.60, 0.07, 0.010, 3.0), True, None),
        'Running': (15, lambda t: gait(t, 0.5, 0.80, 0.45, 0.10, 0.018, 4.0, lean=6.0, low=0.03), True, None),
        'Attack': (30, lambda t: generic(keyed(ATTACK, t), t), False, None),
        'Hit': (15, lambda t: generic(keyed(HIT, t), t), False, None),
        'Fidget': (60, lambda t: generic(keyed(FIDGET, t), t), False, None),
        'Death': (45, death, False, lambda t: 'ground' if t >= 0.95 else 'lift'),
        'Dead': (30, lambda t: death(1.5), False, lambda t: 'ground'),
    }
    for name, (n, fn, loop, ground) in clips.items():
        if only and name not in only:
            continue
        key_action(name, n, fn, loop=loop, ground=ground)
    for k, v in (('Walking', 0.50), ('Running', 0.80)):
        if k in INFO: INFO[k]['stride'] = v
    info_path = os.path.join(WORK, 'anim_info.json')
    old = json.load(open(info_path))['clips'] if (only and os.path.exists(info_path)) else {}
    old.update(INFO)
    json.dump({'clips': old}, open(info_path, 'w'), indent=1)
    P.reset(rig)
    rig.animation_data.action = bpy.data.actions['Standing'] if 'Standing' in bpy.data.actions else None
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'anim_v1.blend'))
    print('SAVED anim_v1.blend')


main()
