"""Procedural clips for the Xeen sabertooth (quadruped playbook: limbs on IK footholds, every frame checked against
the floor). Native Xeen frames (front only, Darkside 044.mon / 044.att): an idle that lifts and steps a forepaw, and
an attack that crouches forward, then lunges with the mouth gaping, the fangs bared and both forepaws thrown forward
with the claws out. No walk, run, hit or death frames: those follow big-cat motion.

Gait choice: a big cat walks a slow four-beat lateral-sequence walk (left hind, left fore, right hind, right fore),
head carried low and level, shoulder blades rolling over each planted foreleg, the spine swaying and the tail hanging
in a lazy lagging curve; it does not trot like a house cat. It runs in a rotary gallop with the spine flexing and
extending through each stride.

Front legs: Scapula rolls (pitch) with the stride; UpperArm + ForeArm two-bone IK to the wrist, elbow pole behind,
carried by the Chest; FrontPaw keeps its rest orientation plus a pitch (> 0 toes down: the paw folds back in the
swing). Hind legs: the Hock keeps its rest direction in the Body frame plus a pitch; Thigh + Shin two-bone IK to the
hock joint, knee pole in front; HindPaw keeps its rest orientation plus a pitch. Body pitch > 0 raises the front,
roll > 0 lifts the left side. Jaw > 0 opens the mouth. Floor rules every frame: the core is lifted when it sinks; a
paw whose vertices dip under the floor gets its target raised; the tail bends up segment by segment until it clears.

  Standing  3.0 s loop   breathing, slow look round, tail-tip swish
  Walking   1.0 s loop   lateral-sequence walk, slightly crouched, 1.45 m per cycle
  Running   0.633 s loop rotary gallop, 2.30 m per cycle (Standard's chase)
  Sprint    0.6 s loop   the gallop stretched, 3.00 m per cycle (MAW's faster chase)
  Attack    1.2 s        crouch and snarl, lunge with both forepaws thrown forward and the jaw wide (IMPACT), the
                         paws slam down and the jaws snap shut, recover
  Hit       0.5 s        flinches back, head jerks up and aside, snarls
  Death     1.7 s        rears in pain, the hind legs buckle, falls onto its right side
  Dead      1.0 s        Death's last pose
  Fidget    2.6 s        a great yawn baring the sabres, a head shake, a tail flick
Reads work/anim_base.blend (UV master), writes work/anim_v1.blend and work/anim_info.json.
Args: -- [clip ...] reruns only those clips on work/anim_v1.blend."""
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
rig = bpy.data.objects['Saber_Rig']; mesh = bpy.data.objects['Saber']
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
FPS = 30
SIDES = {'L': 1.0, 'R': -1.0}
NTAIL = 8

if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
P.reset(rig)
pbn = rig.pose.bones
W = rig.matrix_world
REST = {b.name: b.matrix.copy() for b in pbn}
WRIST = {s: pbn[f'FrontPaw_{s}'].head.copy() for s in SIDES}
ELBOW = {s: pbn[f'ForeArm_{s}'].head.copy() for s in SIDES}
ANKLE = {s: pbn[f'HindPaw_{s}'].head.copy() for s in SIDES}
HOCKJ = {s: pbn[f'Hock_{s}'].head.copy() for s in SIDES}
KNEE = {s: pbn[f'Shin_{s}'].head.copy() for s in SIDES}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    if t <= a or t >= b:
        return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
LIMB_MASK = {('front', s): np.isin(_dom, (f'FrontPaw_{s}',)) for s in SIDES}
LIMB_MASK.update({('hind', s): np.isin(_dom, (f'HindPaw_{s}',)) for s in SIDES})
TAILV = {k: np.isin(_dom, [f'Tail{i}' for i in range(k, NTAIL + 1)]) for k in range(1, NTAIL + 1)}
LIMB = np.isin(_dom, [f'{n}_{s}' for n in ('FrontPaw', 'ForeArm', 'HindPaw', 'Hock', 'Shin') for s in SIDES])
CORE = ~LIMB & ~TAILV[1]


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    return co @ np.array(W.to_3x3()).T + np.array(W.translation)


REST_DROP = float(mesh_co()[:, 2].min())


def move_root(d):
    root = pbn['Body']
    root.matrix = Matrix.Translation(d) @ root.matrix
    bpy.context.view_layer.update()


def floor_fit(mode):
    """mode 'lift' (0): raise the cat when the core sinks; 'ground' (1): the lowest core point on the floor (lying
    poses); a number between blends the two root offsets (no jump when a fall comes to rest)."""
    g = {'lift': 0.0, 'ground': 1.0}.get(mode, mode)
    co = mesh_co()
    low = co[CORE, 2].min()
    off_lift = -low if low < -0.004 else 0.0
    off = off_lift + g * ((-low + 0.003) - off_lift)
    if abs(off) > 1e-6:
        move_root(Vector((0, 0, off)))


def tail_floor():
    for k in range(1, NTAIL + 1):
        for _ in range(14):
            low = mesh_co()[TAILV[k], 2].min()
            if low > -0.003:
                break
            b = pbn[f'Tail{k}']
            d = (b.tail - b.head).normalized()
            ax = d.cross(Z)
            if ax.length < 1e-3:
                break
            P.rotate_world(rig, f'Tail{k}', ax.normalized(), 5)


def body(forward=0.0, lift=0.0, pitch=0.0, roll=0.0, yaw=0.0, pivot=None):
    move_root(Vector((0, -forward, lift - REST_DROP)))
    c = Vector((0, 0.0 - forward, 0.80 + lift - REST_DROP)) if pivot is None else Vector(pivot)
    if yaw:
        P.rotate_world(rig, 'Body', Z, yaw, c)
    if pitch:
        P.rotate_world(rig, 'Body', X, -pitch, c)
    if roll:
        P.rotate_world(rig, 'Body', Y, -roll, c)


def spine(flex=0.0, sway=0.0, chest=0.0, neck=0.0, neck_yaw=0.0, head=0.0, head_yaw=0.0, head_roll=0.0, jaw=0.0):
    """flex > 0 arches the back (spine and chest pitch down about their heads); neck/head > 0 raise; jaw > 0 opens."""
    if flex:
        P.rotate_world(rig, 'Spine', X, flex * 0.5)
        P.rotate_world(rig, 'Chest', X, flex * 0.5)
    if sway:
        P.rotate_world(rig, 'Spine', Z, sway); P.rotate_world(rig, 'Chest', Z, -sway * 0.6)
    if chest:
        P.rotate_world(rig, 'Chest', X, -chest)
    if neck:
        P.rotate_world(rig, 'Neck', X, -neck)
    if neck_yaw:
        P.rotate_world(rig, 'Neck', Z, neck_yaw)
    if head:
        P.rotate_world(rig, 'Head', X, -head)
    if head_yaw:
        P.rotate_world(rig, 'Head', Z, head_yaw)
    if head_roll:
        P.rotate_world(rig, 'Head', Y, head_roll)
    if jaw:
        ax = (pbn['Head'].matrix.to_3x3() @ Vector((-1, 0, 0))).normalized()   # the head's local X points to -X: open = +
        P.rotate_world(rig, 'Jaw', ax, jaw)


def tail(phase, amp=8.0, lift=0.0, curl=0.0):
    """amp: lagging side sway growing to the tip; lift > 0 raises the whole tail; curl > 0 bends the tip up."""
    for i in range(1, NTAIL + 1):
        if lift:
            P.rotate_world(rig, f'Tail{i}', X, lift / NTAIL * (1.6 if i <= 2 else 0.8))
        if curl and i > NTAIL - 3:
            P.rotate_world(rig, f'Tail{i}', X, curl / 3)
        if amp:
            P.rotate_world(rig, f'Tail{i}', Z, amp * (0.3 + 0.12 * i) * math.sin(phase - 0.55 * i))


def carried(point, bone):
    return pbn[bone].matrix @ REST[bone].inverted() @ point


def set_world_rot(name, q):
    b = pbn[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, b.matrix.to_scale()); bpy.context.view_layer.update()


def carried_rot(name, base, carry):
    q = REST[name].to_quaternion()
    if carry:
        dq = (pbn[base].matrix @ REST[base].inverted()).to_quaternion()
        q = Quaternion().slerp(dq, carry) @ q
    return q


ADJ = {}


def front_leg(s, wrist, pitch=0.0, scap=0.0, carry=0.0):
    """wrist: target in world (carry 0) or in rest body space carried by the Chest (carry 1)."""
    if scap:
        P.rotate_world(rig, f'Scapula_{s}', X, scap)
    if carry:
        wrist = wrist.lerp(carried(wrist, 'Chest'), carry)
    # a wrist pulled up close under the shoulder (high swings) would fold the elbow over the shoulder: keep it away
    sh = pbn[f'UpperArm_{s}'].head.copy(); dv = wrist - sh
    if dv.length < 0.38:
        wrist = sh + dv.normalized() * 0.38
    wrist = wrist + Vector((0, 0, ADJ.get(('front', s), 0.0)))
    pole = carried(ELBOW[s] + Vector((SIDES[s] * 0.05, 0.40, -0.05)), 'Chest')
    P.two_bone_ik(rig, f'UpperArm_{s}', f'ForeArm_{s}', wrist, pole)
    q = carried_rot(f'FrontPaw_{s}', 'Chest', carry)
    if pitch:
        q = Quaternion(X, math.radians(pitch)) @ q
    set_world_rot(f'FrontPaw_{s}', q)


def hind_leg(s, ankle, hock_pitch=0.0, pitch=0.0, carry=0.0):
    if carry:
        ankle = ankle.lerp(carried(ankle, 'Body'), carry)
    ankle = ankle + Vector((0, 0, ADJ.get(('hind', s), 0.0)))
    # the hock keeps its rest direction in the Body frame (yaw and roll only), plus a pitch
    rb = (pbn['Body'].matrix @ REST['Body'].inverted()).to_quaternion()
    hv = (ANKLE[s] - HOCKJ[s])
    hv = (Quaternion().slerp(rb, max(carry, 0.35)) @ hv)
    if hock_pitch:
        hv = Quaternion(X, math.radians(hock_pitch)) @ hv
    hj = ankle - hv
    pole = carried(KNEE[s] + Vector((SIDES[s] * 0.05, -0.45, 0.05)), 'Body')
    P.two_bone_ik(rig, f'Thigh_{s}', f'Shin_{s}', hj, pole)
    P.aim_bone(rig, f'Hock_{s}', ankle)
    q = carried_rot(f'HindPaw_{s}', 'Body', carry)
    if pitch:
        q = Quaternion(X, math.radians(pitch)) @ q
    set_world_rot(f'HindPaw_{s}', q)


# ---------------------------------------------------------------- locomotion
def limb_cycle(p, duty, half, lift):
    """Planted (slides back in clip space from -half to +half) for p < duty, then swings forward with a lift."""
    if p < duty:
        q = p / duty
        return -half + 2 * half * q, 0.0, 0.0
    s = (p - duty) / (1 - duty)
    k = ss(s)
    return half - 2 * half * k, lift * math.sin(math.pi * s), s


WALK = dict(T=1.0, D=1.45, duty=0.58, off={'LH': 0.0, 'LF': 0.24, 'RH': 0.5, 'RF': 0.74}, flift=0.12, hlift=0.10,
            bob=0.012, sway=2.5, neck=-9.0, scap=12.0, fpitch=60.0, hpitch=45.0, flex=0.0, lean=0.0,
            lift0=-0.035, fshift=0.04, hshift=0.08)
RUN = dict(T=19 / 30, D=2.30, duty=0.30, off={'LH': 0.0, 'RH': 0.09, 'LF': 0.47, 'RF': 0.57}, flift=0.15, hlift=0.20,
           bob=0.045, sway=1.5, neck=-4.0, scap=16.0, fpitch=95.0, hpitch=70.0, flex=9.0, lean=2.0,
           lift0=-0.05, fshift=0.06, hshift=0.10)
SPRINT = dict(T=18 / 30, D=3.00, duty=0.24, off={'LH': 0.0, 'RH': 0.09, 'LF': 0.47, 'RF': 0.57}, flift=0.13,
              hlift=0.22, bob=0.06, sway=1.2, neck=-2.0, scap=18.0, fpitch=95.0, hpitch=70.0, flex=12.0, lean=3.0,
              lift0=-0.06, fshift=0.08, hshift=0.12)


def gait(t, G):
    T, D, duty = G['T'], G['D'], G['duty']
    u = (t / T) % 1.0
    two = 4 * math.pi * u
    if G['flex']:   # gallop: gathered (hinds forward, back arched) after the hind stance, extended before it
        flex = G['flex'] * math.cos(2 * math.pi * (u - 0.30))
        lift = G['bob'] * math.cos(2 * math.pi * (u - 0.78))
        pitch = -G['lean'] + 4.0 * math.sin(2 * math.pi * (u - 0.20))
    else:
        flex = 0.0
        lift = G['bob'] * math.cos(two)
        pitch = 0.8 * math.cos(two + 0.6)
    body(lift=lift + G['lift0'], pitch=pitch, roll=G['sway'] * math.sin(2 * math.pi * u), yaw=0.6 * G['sway'] * math.sin(2 * math.pi * u))
    spine(flex=flex, sway=1.8 * math.sin(2 * math.pi * u + 0.5), neck=G['neck'] - 0.5 * pitch,
          head=1.5 * math.sin(two + 1.0) - 0.5 * flex, head_yaw=-0.8 * G['sway'] * math.sin(2 * math.pi * u),
          jaw=1.0 + (6.0 * (0.5 + 0.5 * math.sin(2 * math.pi * u)) if G['flex'] else 0.0))
    tail(2 * math.pi * u, amp=7.0 if not G['flex'] else 4.0, lift=10.0 if not G['flex'] else 25.0 + 8 * math.sin(2 * math.pi * u),
         curl=12.0)
    half = D * duty / 2
    for s, sg in SIDES.items():
        y, h, sw = limb_cycle((u - G['off'][s + 'F']) % 1.0, duty, half, G['flift'])
        stance = sw == 0.0
        pf = G['fpitch'] * math.sin(math.pi * sw) ** 2 if not stance else 0.0
        w = WRIST[s] + Vector((-sg * 0.01 * math.sin(math.pi * sw), y - G['fshift'], h))
        # the shoulder blade turns with the leg: the shoulder joint forward at touchdown, back at lift-off (reach)
        ph = ((u - G['off'][s + 'F']) % 1.0) / duty if stance else 1.0
        scap = G['scap'] * ((2 * ph - 1) if stance else math.cos(math.pi * sw))
        front_leg(s, w, pitch=pf, scap=scap)
        y2, h2, sw2 = limb_cycle((u - G['off'][s + 'H']) % 1.0, duty, half, G['hlift'])
        ph2 = G['hpitch'] * math.sin(math.pi * sw2) ** 2 if sw2 else 0.0
        hind_leg(s, ANKLE[s] + Vector((0, y2 - G['hshift'], h2)), hock_pitch=-0.25 * ph2 + (8 * (y2 / half) if not sw2 else 0.0),
                 pitch=ph2)


# ---------------------------------------------------------------- keyed actions
def keyed(keys, t):
    """A per-side key (l_up) missing from a key takes that key's shared value (up), not 0."""
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


def generic(k):
    body(forward=k.get('fwd', 0), lift=k.get('lift', 0), pitch=k.get('pitch', 0), roll=k.get('roll', 0),
         yaw=k.get('yaw', 0), pivot=k.get('pivot'))
    spine(flex=k.get('flex', 0), chest=k.get('chest', 0), neck=k.get('neck', 0), neck_yaw=k.get('neck_yaw', 0),
          head=k.get('head', 0), head_yaw=k.get('head_yaw', 0), head_roll=k.get('head_roll', 0), jaw=k.get('jaw', 0))
    tail(k.get('tphase', 0.0), amp=k.get('tamp', 0.0), lift=k.get('tlift', 0.0), curl=k.get('tcurl', 0.0))
    carry = k.get('carry', 0.0)
    for s, sg in SIDES.items():
        pre = s.lower() + '_'
        g = lambda n: k.get(pre + n, k.get(n, 0.0))
        w = WRIST[s] + Vector((sg * g('out'), -g('hfwd'), g('up')))
        if not carry:
            w = w + Vector((0, -k.get('fwd', 0), 0)) * k.get('follow', 0.0)
        front_leg(s, w, pitch=g('ppitch'), scap=g('scap'), carry=carry)
        a = ANKLE[s] + Vector((sg * g('hout'), -g('ffwd'), g('hup')))
        hind_leg(s, a, hock_pitch=g('hock'), pitch=g('hpitch'), carry=carry)


# Attack: native att 0-2 (crouched forward, mouth opening, then the lunge at the viewer with the jaws wide and both
# forepaws thrown forward, claws out), att 3 back on its feet. The left paw leads by a few frames.
ATTACK = [(0.0, {}),
          (0.30, {'lift': -0.11, 'pitch': -5, 'fwd': -0.07, 'flex': 6, 'neck': -6, 'head': -4, 'jaw': 16, 'scap': 6,
                  'hock': -10, 'tlift': 12, 'tcurl': 15, 'tamp': 6, 'tphase': 1.0}),
          (0.40, {'lift': -0.05, 'pitch': 4, 'fwd': 0.05, 'flex': -2, 'neck': -2, 'head': 0, 'jaw': 32, 'scap': -6,
                  'up': 0.18, 'hfwd': 0.18, 'ppitch': -20, 'l_up': 0.24, 'l_hfwd': 0.26, 'follow': 1.0,
                  'hock': -4, 'tlift': 18, 'tcurl': 10}),
          (0.50, {'lift': 0.03, 'pitch': 7, 'fwd': 0.22, 'flex': -5, 'neck': 0, 'head': -2, 'jaw': 46, 'scap': -14,
                  'up': 0.24, 'hfwd': 0.44, 'out': 0.04, 'ppitch': -55, 'l_up': 0.32, 'l_hfwd': 0.48, 'follow': 1.0,
                  'ffwd': 0.0, 'hock': 6, 'tlift': 22, 'tcurl': 5}),
          (0.64, {'lift': -0.04, 'pitch': -3, 'fwd': 0.20, 'flex': 2, 'neck': -6, 'head': -8, 'jaw': 4, 'scap': 4,
                  'up': 0.0, 'hfwd': 0.30, 'out': 0.02, 'ppitch': 15, 'follow': 1.0, 'hock': 0, 'tlift': 14}),
          (0.88, {'lift': -0.01, 'fwd': 0.08, 'neck': -3, 'head': -2, 'jaw': 10, 'hfwd': 0.10, 'follow': 1.0,
                  'tlift': 8, 'tamp': 5, 'tphase': 2.0}),
          (1.2, {})]
HIT = [(0.0, {}),
       (0.11, {'fwd': -0.09, 'lift': 0.02, 'pitch': 5, 'roll': 4, 'neck': 9, 'head': 10, 'head_yaw': 10, 'jaw': 20,
               'up': 0.05, 'hfwd': -0.05, 'ppitch': -10, 'scap': -5, 'tlift': 15, 'tcurl': 15}),
       (0.24, {'fwd': -0.06, 'pitch': 2, 'roll': 2, 'neck': 4, 'head': 5, 'head_yaw': 5, 'jaw': 14, 'tlift': 8}),
       (0.5, {})]
FIDGET = [(0.0, {}),
          (0.45, {'neck': 10, 'head': 12, 'jaw': 6, 'tlift': 4, 'tamp': 4, 'tphase': 1.0}),
          (0.95, {'neck': 16, 'head': 24, 'jaw': 42, 'head_roll': 4, 'flex': -2, 'tlift': 6, 'tcurl': 15, 'tamp': 6,
                  'tphase': 2.5}),
          (1.45, {'neck': 15, 'head': 24, 'jaw': 44, 'head_roll': -3, 'flex': -2, 'tlift': 6, 'tcurl': 20,
                  'tamp': 6, 'tphase': 4.0}),
          (1.80, {'neck': 6, 'head': 4, 'jaw': 2, 'tlift': 4, 'tamp': 6, 'tphase': 5.0}),
          (1.98, {'neck': 4, 'head': 2, 'head_yaw': 12, 'head_roll': 8, 'jaw': 2, 'tcurl': 30, 'tamp': 10, 'tphase': 6.0}),
          (2.14, {'neck': 4, 'head': 2, 'head_yaw': -10, 'head_roll': -8, 'jaw': 2, 'tcurl': 10, 'tamp': 8, 'tphase': 7.2}),
          (2.30, {'neck': 2, 'head': 1, 'head_yaw': 4, 'head_roll': 2, 'tamp': 4, 'tphase': 8.0}),
          (2.6, {})]
DEATH = [(0.0, {}),
         (0.25, {'pitch': 9, 'lift': 0.02, 'neck': 14, 'head': 14, 'jaw': 34, 'up': 0.10, 'hfwd': 0.05, 'ppitch': -25,
                 'scap': -8, 'tlift': 20, 'tcurl': 20, 'tamp': 8, 'tphase': 2}),
         (0.55, {'pitch': -4, 'lift': -0.20, 'roll': 14, 'neck': -6, 'head': -4, 'jaw': 20, 'hock': -20,
                 'carry': 0.35, 'tlift': 6, 'tamp': 6, 'tphase': 4}),
         (1.05, {'roll': 80, 'lift': -0.05, 'neck': -14, 'neck_yaw': -12, 'head': -10, 'jaw': 14, 'carry': 1.0,
                 'l_out': -0.22, 'l_hout': -0.22, 'hfwd': 0.10, 'ffwd': -0.10, 'ppitch': 20, 'hpitch': 20,
                 'tamp': 4, 'tphase': 6}),
         (1.35, {'roll': 90, 'neck': -16, 'neck_yaw': -14, 'head': -12, 'jaw': 12, 'carry': 1.0,
                 'l_out': -0.30, 'l_hout': -0.30, 'r_out': -0.04, 'r_hout': -0.04, 'hfwd': 0.16, 'ffwd': -0.14,
                 'l_hfwd': 0.24, 'ppitch': 25, 'hpitch': 25}),
         (1.7, {'roll': 90, 'neck': -16, 'neck_yaw': -14, 'head': -12, 'jaw': 12, 'carry': 1.0,
                'l_out': -0.30, 'l_hout': -0.30, 'r_out': -0.04, 'r_hout': -0.04, 'hfwd': 0.16, 'ffwd': -0.14,
                'l_hfwd': 0.24, 'ppitch': 25, 'hpitch': 25})]


def death(t):
    k = keyed(DEATH, t)
    if k.get('roll', 0) > 1:      # roll about the right-hand lower edge of the trunk
        k['pivot'] = (-0.30, 0.0, 0.45 + k.get('lift', 0) - REST_DROP)
    generic(k)


def standing(t):
    T = 3.0; u = 2 * math.pi * t / T
    generic({'lift': 0.004 * math.sin(2 * u), 'flex': 0.6 * math.sin(2 * u), 'neck': -2 + 1.5 * math.sin(u + 0.6),
             'neck_yaw': 6 * math.sin(u + 1.3), 'head': 1.5 * math.sin(2 * u + 0.4), 'head_yaw': 4 * math.sin(u + 0.9),
             'jaw': 1.5 + 1.5 * math.sin(2 * u), 'tphase': u, 'tamp': 6.0, 'tlift': 4.0,
             'tcurl': 14 + 12 * math.sin(2 * u + 1.0)})


INFO = {}


def key_action(name, n, fn, loop=False, ground=None):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows, core_lows, tips = [], [], [], []
    for f in range(n + 1):
        t = ((f % n) / FPS) if loop else f / FPS
        ADJ.clear()
        mode = ground(t) if ground else 'lift'
        for _ in range(4):
            P.reset(rig); fn(t); floor_fit(mode); tail_floor()
            co = mesh_co(); moved = False
            for key, mask in LIMB_MASK.items():
                low = co[mask, 2].min()
                if low < -0.006:
                    ADJ[key] = ADJ.get(key, 0.0) - low + 0.002; moved = True
            if not moved:
                break
        co = mesh_co()
        lows.append(float(co[:, 2].min())); core_lows.append(float(co[CORE, 2].min()))
        tips.append([tuple(pbn[f'FrontPaw_{s}'].tail) for s in SIDES])
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
                  'adj': {f'{a}_{b}': round(v, 3) for (a, b), v in ADJ.items()}}
    if name == 'Attack':
        tipy = np.array([[p[1] for p in fr] for fr in tips]).mean(1)
        f_imp = int(np.argmin(tipy))
        INFO[name]['paw_tip_y'] = [round(v, 3) for v in tipy]
        INFO[name]['impact_frame'] = f_imp; INFO[name]['impact_s'] = round(f_imp / FPS, 3)
    print('CLIP', name, {k: v for k, v in INFO[name].items() if not k.startswith('paw_tip')}, flush=True)


def main():
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    clips = {
        'Standing': (90, standing, True, None),
        'Walking': (30, lambda t: gait(t, WALK), True, None),
        'Running': (19, lambda t: gait(t, RUN), True, None),
        'Sprint': (18, lambda t: gait(t, SPRINT), True, None),
        'Attack': (36, lambda t: generic(keyed(ATTACK, t)), False, None),
        'Hit': (15, lambda t: generic(keyed(HIT, t)), False, None),
        'Fidget': (78, lambda t: generic(keyed(FIDGET, t)), False, None),
        'Death': (51, death, False, lambda t: ss((t - 0.55) / 0.55)),
        'Dead': (30, lambda t: death(1.7), False, lambda t: 'ground'),
    }
    for name, (n, fn, loop, ground) in clips.items():
        if only and name not in only:
            continue
        key_action(name, n, fn, loop=loop, ground=ground)
    for k, G in (('Walking', WALK), ('Running', RUN), ('Sprint', SPRINT)):
        if k in INFO: INFO[k]['stride'] = G['D']
    info_path = os.path.join(WORK, 'anim_info.json')
    old = json.load(open(info_path))['clips'] if (only and os.path.exists(info_path)) else {}
    old.update(INFO)
    json.dump({'clips': old, 'rest_drop_cm': round(REST_DROP * 100, 2)}, open(info_path, 'w'), indent=1)
    P.reset(rig)
    rig.animation_data.action = bpy.data.actions['Standing'] if 'Standing' in bpy.data.actions else None
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'anim_v1.blend'))
    print('SAVED anim_v1.blend')


main()
