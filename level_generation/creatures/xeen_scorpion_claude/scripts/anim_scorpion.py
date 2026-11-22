"""Procedural clips for the Xeen giant scorpion (quadruped playbook, segmented creatures: an exoskeleton rig, legs on
IK footholds, every frame checked against the floor). Native Xeen frames (Clouds image 19, front only): 019.mon an idle
in which the claws shift and the tail sways; 019.att the right pincer thrown open toward the viewer while the tail
stays high. The task's attack: the pincers open and snap, and the tail strikes forward over the head.

Legs: two-bone IK (Femur + Tibia) to the ankle target, the knee pole above and outside (carried by the Body); the
Tarsus keeps its rest direction (carried by the Body in lying poses). Gait: alternating tetrapod (L1 R2 L3 R4 /
R1 L2 R3 L4). Pedipalps: two-bone IK (Arm1 + Arm2) to a wrist target in the body frame, the elbow pole up and out;
the Chela keeps its rest orientation in the body frame plus a pitch and yaw; the front finger opens about its hinge
(`op` > 0 opens, < 0 snaps shut). Tail: each joint (Tail1..5, Stinger) curls about the body's X axis (> 0 curls
forward), sways about the body's Z axis with a lag along the chain; the strike and the cocked pose were solved in the
tail's plane for the sting tip (planar FK + Powell: strike tip 0.45 m ahead of the body centre, 0.42 m high).
Floor rules every frame: the core (body, abdomen, tail) is lifted when it sinks ('ground' mode puts the lowest core
point on the floor for lying poses); a leg or claw whose vertices dip under the floor gets its target raised.

  Standing  2.0 s loop   breathing, tail sway, claws shift and twitch open
  Walking   0.8 s loop   tetrapod, 0.50 m per cycle
  Running   0.5 s loop   the same, lower, 0.80 m per cycle
  Attack    1.0 s        rears, claws open, tail cocks back (0.30 s); the right claw lunges and snaps, the tail strikes
                         forward over the head: IMPACT at the sting's furthest reach; recovers
  Hit       0.5 s        jolts back, claws flinch up and open, tail flinches back
  Death     1.5 s        rears in pain, collapses on its belly tilted to the left, legs curl in, tail falls to the floor
  Dead      1.0 s        Death's last pose
  Fidget    2.0 s        the tail curls and sways, the left then the right claw snaps twice
Reads work/anim_base.blend (UV master; work/rig_v1.blend before it exists), writes work/anim_v1.blend and
work/anim_info.json. Usage: anim_scorpion.py [clip ...]  (a partial rerun keeps the other clips of anim_v1.blend)"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
_only = '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 1
_base = 'anim_base.blend' if os.path.exists(os.path.join(WORK, 'anim_base.blend')) else 'rig_v1.blend'
_src = 'anim_v1.blend' if _only and os.path.exists(os.path.join(WORK, 'anim_v1.blend')) else _base
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, _src))
rig = bpy.data.objects['Scorpion_Rig']; mesh = bpy.data.objects['Scorpion']
J = json.load(open(os.path.join(WORK, 'joints.json')))
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
FPS = 30
SIDES = {'L': 1.0, 'R': -1.0}
LEGS = ('L1', 'R1', 'L2', 'R2', 'L3', 'R3', 'L4', 'R4')
GROUP_A = ('L1', 'R2', 'L3', 'R4')
TAIL = ('Tail1', 'Tail2', 'Tail3', 'Tail4', 'Tail5', 'Stinger')

if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
P.reset(rig)
pbn = rig.pose.bones
W = rig.matrix_world
REST = {b.name: b.matrix.copy() for b in pbn}
ANKLE = {k: pbn[f'Tarsus_{k}'].head.copy() for k in LEGS}
KNEE = {k: pbn[f'Tibia_{k}'].head.copy() for k in LEGS}
HIP = {k: pbn[f'Femur_{k}'].head.copy() for k in LEGS}
WRIST = {s: pbn[f'Chela_{s}'].head.copy() for s in SIDES}
ELBOW = {s: pbn[f'Arm2_{s}'].head.copy() for s in SIDES}
BODYC = pbn['Body'].head.copy()
HINGE = {s: Vector(J['claws'][s]['hinge_normal']) for s in SIDES}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    if t <= a or t >= b:
        return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] for v in mesh.data.vertices])
LEGMASK = {k: np.isin(_dom, (f'Tibia_{k}', f'Tarsus_{k}')) for k in LEGS}     # raised by their targets
TARSUS = {k: _dom == f'Tarsus_{k}' for k in LEGS}
CLAWMASK = {s: np.isin(_dom, (f'Arm2_{s}', f'Chela_{s}', f'Finger_{s}')) for s in SIDES}
CORE = np.isin(_dom, ('Body', 'Abdomen') + TAIL)
# the body's floor fit also keeps the limb roots (femurs, upper pedipalps) above the floor: targets cannot lift them
LOWBODY = CORE | np.isin(_dom, [f'Femur_{k}' for k in LEGS] + [f'Arm1_{s}' for s in SIDES])


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    return co @ np.array(W.to_3x3()).T + np.array(W.translation)


REST_CO = mesh_co()
FOOT_DROP = {k: float(REST_CO[TARSUS[k], 2].min()) for k in LEGS}


def move_root(d):
    root = pbn['Body']
    root.matrix = Matrix.Translation(d) @ root.matrix
    bpy.context.view_layer.update()


def floor_fit(mode):
    co = mesh_co()
    low = co[LOWBODY, 2].min()
    if mode == 'ground':
        move_root(Vector((0, 0, -low + 0.003)))
    elif low < -0.004:
        move_root(Vector((0, 0, -low)))


def body_q():
    return (pbn['Body'].matrix @ REST['Body'].inverted()).to_quaternion()


def carried(point, bone='Body'):
    return pbn[bone].matrix @ REST[bone].inverted() @ point


def set_world_rot(name, q):
    b = pbn[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, b.matrix.to_scale()); bpy.context.view_layer.update()


def body(fwd=0.0, lift=0.0, pitch=0.0, roll=0.0, yaw=0.0, pivot=None):
    """pitch > 0 raises the front, roll > 0 lowers the left (+X) side, yaw > 0 turns the head toward +X."""
    move_root(Vector((0, -fwd, lift)))
    c = BODYC + Vector((0, -fwd, lift)) if pivot is None else Vector(pivot)
    if yaw:
        P.rotate_world(rig, 'Body', Z, yaw, c)
    if pitch:
        P.rotate_world(rig, 'Body', X, -pitch, c)
    if roll:
        P.rotate_world(rig, 'Body', Y, roll, c)


def abdomen(ab=0.0, ab_yaw=0.0):
    """ab > 0 lifts the rear of the body (and the tail base)."""
    bq = body_q()
    if ab:
        P.rotate_world(rig, 'Abdomen', bq @ X, ab)
    if ab_yaw:
        P.rotate_world(rig, 'Abdomen', bq @ Z, ab_yaw)


def tail(curl=(0, 0, 0, 0, 0, 0), yaw=(0, 0, 0, 0, 0, 0)):
    """Per joint, root to tip: curl > 0 bends the tail forward about the body's X axis, yaw about its Z axis."""
    bq = (pbn['Abdomen'].matrix @ REST['Abdomen'].inverted()).to_quaternion()
    for name, c, y in zip(TAIL, curl, yaw):
        if c:
            P.rotate_world(rig, name, bq @ X, c)
        if y:
            P.rotate_world(rig, name, bq @ Z, y)


ADJ = {}


def leg(k, off=Vector(), carry=0.0, curl=0.0):
    """off: target offset in world; carry 1 places the target in rest body space carried by the Body (lying poses);
    curl relaxes a dead leg: the foot slides outward, the knee drops (lower pole) and the tarsus tip sinks."""
    sg = SIDES[k[0]]
    target = ANKLE[k] - Vector((0, 0, FOOT_DROP[k])) + off
    if curl:
        target = target + Vector((sg * 0.07 * curl, 0, 0))
    if carry:
        target = target.lerp(carried(target), carry)
    target = target + Vector((0, 0, ADJ.get(k, 0.0)))
    pole = carried(KNEE[k] + Vector((sg * (0.25 + 0.1 * curl), 0.0, 0.35 - 0.25 * curl)))
    P.two_bone_ik(rig, f'Femur_{k}', f'Tibia_{k}', target, pole)
    q = REST[f'Tarsus_{k}'].to_quaternion()
    if carry:
        q = Quaternion().slerp(body_q(), carry) @ q
    if curl:
        fd = pbn[f'Tarsus_{k}'].tail - pbn[f'Tarsus_{k}'].head
        ax = fd.cross(Z)
        if ax.length > 1e-4:
            q = Quaternion(ax.normalized(), math.radians(-15 * curl)) @ q
    set_world_rot(f'Tarsus_{k}', q)


def claw(s, cf=0.0, cu=0.0, co=0.0, cp=0.0, cy=0.0, op=0.0):
    """Pedipalp s: wrist target moved forward (cf), up (cu), outward (co) in the body frame; the chela pitched up (cp)
    and turned inward (cy, degrees); the front finger opened by op degrees (< 0 snaps it shut)."""
    sg = SIDES[s]
    target = carried(WRIST[s] + Vector((sg * co, -cf, cu)))
    target = target + Vector((0, 0, ADJ.get('C' + s, 0.0)))
    pole = carried(ELBOW[s] + Vector((sg * 0.20, 0.05, 0.25)))
    P.two_bone_ik(rig, f'Arm1_{s}', f'Arm2_{s}', target, pole)
    bq = body_q()
    q = bq @ REST[f'Chela_{s}'].to_quaternion()
    if cp:
        q = Quaternion(bq @ (X * sg), math.radians(-cp * sg)) @ q
    if cy:
        q = Quaternion(bq @ Z, math.radians(-cy * sg)) @ q
    set_world_rot(f'Chela_{s}', q)
    if op:
        cq = (pbn[f'Chela_{s}'].matrix @ REST[f'Chela_{s}'].inverted()).to_quaternion()
        P.rotate_world(rig, f'Finger_{s}', cq @ HINGE[s], -op)


# ---------------------------------------------------------------- locomotion
def limb_cycle(p, duty, half, lift):
    if p < duty:
        q = p / duty
        return -half + 2 * half * q, 0.0
    s = (p - duty) / (1 - duty)
    k = ss(s)
    return half - 2 * half * k, lift * math.sin(math.pi * s)


def tail_sway(t, period, amp=1.0, curl0=0.0):
    yaw = [amp * (1.5 + 1.2 * i) * math.sin(2 * math.pi * t / period - 0.5 * i) for i in range(6)]
    curl = [curl0 + amp * 1.2 * math.sin(2 * math.pi * t / period * 2 - 0.6 * i) for i in range(6)]
    return curl, yaw


def gait(t, T, D, duty, lift, bob, sway, pitch=0.0, low=0.0):
    u = (t / T) % 1.0
    body(lift=-low + bob * math.cos(4 * math.pi * u), pitch=pitch + 0.8 * math.cos(4 * math.pi * u),
         roll=sway * math.sin(2 * math.pi * u), yaw=0.6 * sway * math.sin(2 * math.pi * u))
    abdomen(ab=1.5 * math.sin(4 * math.pi * u + 0.8), ab_yaw=-1.0 * sway * math.sin(2 * math.pi * u + 0.6))
    c, y = tail_sway(t, T, 1.0)
    tail(c, y)
    for s, sg in SIDES.items():
        ph = 2 * math.pi * u + (0 if s == 'L' else math.pi)
        claw(s, cf=0.025 * math.sin(ph), cu=0.03 + 0.01 * math.sin(ph + 1.0), op=4 * math.sin(ph + 1.5))
    half = D * duty / 2
    for k in LEGS:
        ph = (u + (0.0 if k in GROUP_A else 0.5) + 0.04 * (int(k[1]) - 1)) % 1.0
        y, h = limb_cycle(ph, duty, half, lift)
        leg(k, Vector((0, y, h)))


# ---------------------------------------------------------------- keyed actions
def keyed(keys, t):
    """A per-side key (l_cf) missing from a key takes that key's shared value (cf), not 0."""
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


def generic(k, t=0.0, sway_amp=0.0, period=2.0):
    body(fwd=k.get('fwd', 0), lift=k.get('lift', 0), pitch=k.get('pitch', 0), roll=k.get('roll', 0),
         yaw=k.get('yaw', 0), pivot=k.get('pivot'))
    abdomen(k.get('ab', 0), k.get('ab_yaw', 0))
    c, y = tail_sway(t, period, sway_amp)
    curl = [c[i] + k.get(f't{i + 1}', 0) for i in range(6)]
    yaw = [y[i] + k.get('ty', 0) * (0.5 + 0.2 * i) for i in range(6)]
    tail(curl, yaw)
    for s in SIDES:
        pre = s.lower() + '_'
        g = lambda n: k.get(pre + n, k.get(n, 0.0))
        claw(s, cf=g('cf'), cu=g('cu'), co=g('co'), cp=g('cp'), cy=g('cy'), op=g('op'))
    carry = k.get('carry', 0.0); curl_l = k.get('curl', 0.0); follow = k.get('follow', 0.0)
    for leg_k in LEGS:
        leg(leg_k, Vector((0, -k.get('fwd', 0) * follow, 0)), carry=carry, curl=curl_l)


COCK = {'t1': -20, 't2': -15, 't3': -9, 't4': -4, 't5': 1, 't6': 2}
STRIKE = {'t1': 26, 't2': 6, 't3': -12, 't4': -14, 't5': -18, 't6': -15}
# Attack: rear and cock (claws up and open, tail drawn back and up; native att 1), the right claw lunges at the party
# and snaps while the tail whips forward over the head (att 2); hold; recover (att 3).
ATTACK = [(0.0, {}),
          (0.26, {'pitch': 6, 'lift': 0.02, 'fwd': -0.03, 'ab': 3, **COCK, 'cu': 0.10, 'cf': -0.02, 'co': 0.04,
                  'cp': 20, 'op': 28, 'cy': -6}),
          (0.32, {'pitch': 7, 'lift': 0.025, 'fwd': -0.035, 'ab': 3.5, **{k: v * 1.1 for k, v in COCK.items()},
                  'cu': 0.11, 'cf': -0.025, 'co': 0.045, 'cp': 22, 'op': 30, 'cy': -7}),
          (0.47, {'pitch': -4, 'fwd': 0.08, 'ab': 10, **STRIKE, 'l_cf': 0.08, 'r_cf': 0.17, 'l_cu': 0.03,
                  'r_cu': 0.06, 'co': -0.01, 'cp': -4, 'r_cp': 4, 'cy': 8, 'op': -16}),
          (0.60, {'pitch': -3.5, 'fwd': 0.075, 'ab': 9, **{k: v * 0.95 for k, v in STRIKE.items()}, 'l_cf': 0.07,
                  'r_cf': 0.15, 'l_cu': 0.03, 'r_cu': 0.05, 'cp': -3, 'r_cp': 3, 'cy': 7, 'op': -14}),
          (0.82, {'pitch': -1, 'fwd': 0.02, 'ab': 2, **{k: v * 0.25 for k, v in STRIKE.items()}, 'cf': 0.02,
                  'cu': 0.01, 'op': 4}),
          (1.0, {})]
HIT = [(0.0, {}),
       (0.10, {'fwd': -0.06, 'lift': 0.015, 'pitch': 7, 'roll': 4, 'ab': -4, 't1': -8, 't2': -6, 't3': -4, 't4': 4,
               't5': 8, 't6': 10, 'ty': 6, 'cu': 0.07, 'cf': -0.04, 'cp': 15, 'op': 22}),
       (0.24, {'fwd': -0.03, 'pitch': 3, 'roll': 2, 'ab': -2, 't1': -3, 't2': -2, 't4': 2, 't5': 3, 't6': 4,
               'ty': 2, 'cu': 0.03, 'cf': -0.02, 'cp': 6, 'op': 8}),
       (0.5, {})]
FIDGET = [(0.0, {}),
          (0.25, {'t1': -4, 't3': 4, 't5': 6, 't6': 8, 'ty': 6, 'l_op': 25, 'l_cu': 0.04, 'l_cp': 8}),
          (0.38, {'t1': -5, 't3': 5, 't5': 7, 't6': 10, 'ty': 8, 'l_op': -12, 'l_cu': 0.04, 'l_cp': 8}),
          (0.50, {'t1': -5, 't3': 5, 't5': 7, 't6': 10, 'ty': 8, 'l_op': 22, 'l_cu': 0.04, 'l_cp': 8}),
          (0.62, {'t1': -4, 't3': 4, 't5': 6, 't6': 8, 'ty': 6, 'l_op': -12, 'l_cu': 0.03, 'l_cp': 6}),
          (0.85, {'yaw': -3, 'ty': -4, 't4': 3, 'r_op': 2}),
          (1.10, {'yaw': -4, 'ty': -8, 't4': 4, 't6': 4, 'r_op': 25, 'r_cu': 0.04, 'r_cp': 8, 'r_cf': 0.03}),
          (1.22, {'yaw': -4, 'ty': -8, 't4': 4, 't6': 4, 'r_op': -12, 'r_cu': 0.04, 'r_cp': 8, 'r_cf': 0.03}),
          (1.34, {'yaw': -4, 'ty': -8, 't4': 4, 't6': 4, 'r_op': 22, 'r_cu': 0.04, 'r_cp': 8, 'r_cf': 0.03}),
          (1.46, {'yaw': -3, 'ty': -6, 't4': 3, 't6': 3, 'r_op': -12, 'r_cu': 0.03, 'r_cp': 6, 'r_cf': 0.02}),
          (1.7, {'yaw': -1, 'ty': -2, 'r_op': 2}),
          (2.0, {})]
# the tail falls back onto the floor behind the body (segment angles solved in the tail plane: base segment 20 deg
# down-back, the rest level, the stinger bulb curled up a little)
DROP = {'t1': -105, 't2': 9, 't3': -40, 't4': -6, 't5': -26, 't6': -14}
DEATH = [(0.0, {}),
         (0.22, {'pitch': 9, 'lift': 0.04, 'roll': -3, 'ab': 4, 't1': -12, 't2': -10, 't3': -4, 't4': 4, 't5': 10,
                 't6': 16, 'ty': -8, 'cu': 0.10, 'cp': 20, 'op': 30, 'co': 0.03}),
         (0.60, {'pitch': 2, 'lift': -0.06, 'roll': 4, 'ab': -3, **{k: v * 0.6 for k, v in DROP.items()}, 'ty': 6,
                 'cu': 0.0, 'cp': -8, 'op': 12, 'co': 0.05, 'cf': 0.03, 'curl': 0.5}),
         (1.0, {'pitch': -2, 'lift': -0.12, 'roll': 7, 'ab': -6, **DROP, 'ty': 10, 'cu': 0.03, 'cp': -14,
                'op': 6, 'co': 0.06, 'cf': 0.05, 'cy': -10, 'curl': 1.0}),
         (1.5, {'pitch': -2, 'lift': -0.12, 'roll': 7.5, 'ab': -6, **{k: v * 1.03 for k, v in DROP.items()},
                'ty': 11, 'cu': 0.03, 'cp': -15, 'op': 4, 'co': 0.06, 'cf': 0.05, 'cy': -10, 'curl': 1.05,
                })]


def death(t):
    k = keyed(DEATH, min(t, 1.5))
    generic(k, min(t, 1.5), sway_amp=0.0)


INFO = {}


def tail_floor(settle=0.0):
    """Floor rule for a lying tail (quadruped playbook, cockatrice): joint by joint from the root, bend each segment
    only until its own vertices rest on the floor, never arcing the whole tail up for a later segment. With `settle`
    (0..1, a corpse settling) a segment after the first that floats above the floor is lowered onto it too, by at
    most settle x 40 degrees (eased in over the fall, so the tail does not jump)."""
    for i, name in enumerate(TAIL):
        sel = _dom == name
        down = int(round(settle * 40))
        for _ in range(60):
            low = mesh_co()[sel, 2].min()
            bq = (pbn['Abdomen'].matrix @ REST['Abdomen'].inverted()).to_quaternion()
            if low < 0.003:
                P.rotate_world(rig, name, bq @ X, 1.0)
            elif down > 0 and i > 0 and low > 0.015:
                P.rotate_world(rig, name, bq @ X, -1.0); down -= 1
            else:
                break


def key_action(name, n, fn, loop=False, ground=None, tail_rule=None):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows, core_lows, tips, lowgrp, claws = [], [], [], [], [], []
    for f in range(n + 1):
        t = ((f % n) / FPS) if loop else f / FPS
        ADJ.clear()
        mode = ground(t) if ground else 'lift'
        for _ in range(5):
            P.reset(rig); fn(t)
            if tail_rule:
                floor_fit(mode)
                tail_floor(settle=tail_rule(t))
            floor_fit(mode)
            co = mesh_co(); moved = False
            for k, mask in LEGMASK.items():
                low = co[mask, 2].min()
                if low < -0.006:
                    ADJ[k] = ADJ.get(k, 0.0) - low + 0.002; moved = True
            for s, mask in CLAWMASK.items():
                low = co[mask, 2].min()
                if low < -0.004:
                    ADJ['C' + s] = ADJ.get('C' + s, 0.0) - low + 0.003; moved = True
            if not moved:
                break
        co = mesh_co()
        lows.append(float(co[:, 2].min())); core_lows.append(float(co[CORE, 2].min()))
        lowgrp.append(_dom[int(co[:, 2].argmin())])
        tips.append(tuple(pbn['Stinger'].tail))
        claws.append(tuple(pbn['Finger_R'].tail))
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
        ty = np.array([p[1] for p in tips]); tz = np.array([p[2] for p in tips])
        INFO[name]['sting_y'] = [round(v, 3) for v in ty]
        INFO[name]['sting_z'] = [round(v, 3) for v in tz]
        INFO[name]['claw_r_y'] = [round(p[1], 3) for p in claws]
        f_imp = int(np.argmin(ty))          # the sting at its furthest reach: the blow lands
        INFO[name]['impact_frame'] = f_imp; INFO[name]['impact_s'] = round(f_imp / FPS, 3)
    print('CLIP', name, {k: v for k, v in INFO[name].items() if not k.startswith(('sting_', 'claw_'))}, flush=True)


def main():
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    idle = lambda t: generic({'lift': 0.006 * math.sin(math.pi * t), 'pitch': 0.8 * math.sin(math.pi * t),
                              'ab': 1.5 * math.sin(math.pi * t + 0.4),
                              'l_cf': 0.015 * math.sin(math.pi * t + 0.3), 'r_cf': 0.015 * math.sin(math.pi * t + 1.6),
                              'l_cu': 0.02 + 0.01 * math.sin(math.pi * t + 0.8),
                              'r_cu': 0.02 + 0.01 * math.sin(math.pi * t + 2.1),
                              'l_op': 6 * bump(t, 0.3, 0.8) - 2, 'r_op': 6 * bump(t, 1.2, 1.7) - 2,
                              'l_cp': 3 * math.sin(math.pi * t + 0.5), 'r_cp': 3 * math.sin(math.pi * t + 1.9)},
                             t, sway_amp=1.0, period=2.0)
    clips = {
        'Standing': (60, idle, True, None, None),
        'Walking': (24, lambda t: gait(t, 0.8, 0.50, 0.60, 0.07, 0.008, 2.0), True, None, None),
        'Running': (15, lambda t: gait(t, 0.5, 0.80, 0.45, 0.10, 0.014, 3.0, pitch=-2.0, low=0.02), True, None, None),
        'Attack': (30, lambda t: generic(keyed(ATTACK, t), t, sway_amp=0.0), False, None, None),
        'Hit': (15, lambda t: generic(keyed(HIT, t), t), False, None, None),
        'Fidget': (60, lambda t: generic(keyed(FIDGET, t), t, sway_amp=0.6), False, None, None),
        'Death': (45, death, False, lambda t: 'ground' if t >= 0.75 else 'lift', lambda t: ss((t - 0.6) / 0.6)),
        'Dead': (30, lambda t: death(1.5), False, lambda t: 'ground', lambda t: 1.0),
    }
    for name, (n, fn, loop, ground, tr) in clips.items():
        if only and name not in only:
            continue
        key_action(name, n, fn, loop=loop, ground=ground, tail_rule=tr)
    for k, v in (('Walking', 0.50), ('Running', 0.80)):
        if k in INFO: INFO[k]['stride'] = v
    info_path = os.path.join(WORK, 'anim_info.json')
    old = json.load(open(info_path))['clips'] if (only and os.path.exists(info_path)) else {}
    old.update(INFO)
    json.dump({'clips': old}, open(info_path, 'w'), indent=1)
    P.reset(rig)
    rig.animation_data.action = bpy.data.actions['Standing'] if 'Standing' in bpy.data.actions else None
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'anim_v1.blend'))
    print('SAVED anim_v1.blend from', _src)


main()
