"""Procedural clips for the Xeen Armadillo (quadruped playbook: legs on IK targets, every frame checked against the
floor). Native Darkside frames (front only, 005.mon / 005.att): the idle breathes with a forked green tongue flicking
out (mon 4-7) and the tail swaying; the attack raises the forelegs with the claws out and lifts the tail (att 0), the
tail arcs over the back as the ball sprouts long spikes (att 1), the spiked ball comes down over the head at the
viewer with both claws thrown forward (att 2), and the beast hunches into a defensive ball (att 3). No walk, hit or
death frames: those follow armadillo anatomy (a low, heavy waddle on short sprawled legs; flinching into the shell;
rolling onto its side).

Front legs: two-bone IK (UpperArm + ForeArm) to the wrist target, elbow pole out and up carried by the Chest; the
Hand keeps its rest orientation plus a pitch (claws down > 0). Hind legs: Thigh + Shin IK to the ankle target, knee
pole out and forward; the HindFoot keeps its rest orientation plus a pitch. Tail: per-segment pitch (curl > 0 lifts
and bends it over the back; a profile weights the root or the tip), side sway with a phase lag along the chain.
Spikes: uniform scale of the Spikes bone (0.4 hides them in the ball, 1.0 out); TailBall scale swells the mace;
Tongue: uniform scale (0.05 in the mouth, 1.0 out). Floor rules every frame: the core (trunk, head, upper legs) is
lifted when it sinks; a foot whose vertices dip under the floor gets its target raised; tail segments bend up until
they clear.

  Standing  2.4 s loop   breathing heave, two tongue flicks, small head drift, slow tail sway
  Walking   1.0 s loop   heavy waddle (LF+RH / RF+LH, duty 0.65), the tail swinging low, 0.45 m per cycle
  Running   0.6 s loop   same, longer, faster and lower, 0.80 m per cycle
  Attack    1.5 s        forelegs up, tail over the back, spikes out, the mace whips down over the head (IMPACT
                         measured: the ball furthest forward), claws slam down, hunch, recover
  Hit       0.5 s        flinches into the shell: head ducked, body dropped, tail tucked
  Death     1.6 s        rears in pain, rolls onto its right side, legs curl, tail falls limp
  Dead      1.0 s        Death's last pose
  Fidget    2.4 s        curls partly into a ball (head tucked, back arched, tail round) and uncurls; long tongue flick
Reads work/anim_base.blend (UV master), writes work/anim_v1.blend and work/anim_info.json."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
_args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
_src_override = next((a for a in _args if a.endswith('.blend')), None)
_only = [a for a in _args if not a.endswith('.blend')]
_src = _src_override or ('anim_v1.blend' if _only and os.path.exists(os.path.join(WORK, 'anim_v1.blend'))
                         else 'anim_base.blend')
_dst = 'preview.blend' if _src_override else 'anim_v1.blend'
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, _src))   # a partial rerun keeps the other clips
rig = bpy.data.objects['Dillo_Rig']; mesh = bpy.data.objects['Dillo']
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
FPS = 30
SIDES = {'L': 1.0, 'R': -1.0}
SPK_IN, TONGUE_IN = 0.4, 0.05

if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
P.reset(rig)
pbn = rig.pose.bones
W = rig.matrix_world
REST = {b.name: b.matrix.copy() for b in pbn}
WRIST = {s: pbn[f'Hand_{s}'].head.copy() for s in SIDES}
ELBOW = {s: pbn[f'ForeArm_{s}'].head.copy() for s in SIDES}
ANKLE = {s: pbn[f'HindFoot_{s}'].head.copy() for s in SIDES}
KNEE = {s: pbn[f'Shin_{s}'].head.copy() for s in SIDES}
BALL0 = pbn['Spikes'].head.copy()


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    if t <= a or t >= b:
        return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
LIMB_MASK = {('front', s): np.isin(_dom, (f'Hand_{s}',)) for s in SIDES}
LIMB_MASK.update({('hind', s): np.isin(_dom, (f'HindFoot_{s}',)) for s in SIDES})
TAILV = {k: np.isin(_dom, [f'Tail{i}' for i in range(k, 9)] + ['TailBall', 'Spikes']) for k in range(1, 9)}
TONGUE = np.isin(_dom, ['Tongue'])
LIMB = np.isin(_dom, [f'{n}_{s}' for n in ('Hand', 'ForeArm', 'HindFoot', 'Shin') for s in SIDES])
CORE = ~LIMB & ~TAILV[1] & ~TONGUE
BALLV = np.isin(_dom, ['TailBall'])


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
    """'lift': raise the beast when the core sinks; 'ground': the lowest core point on the floor (lying poses)."""
    co = mesh_co()
    low = co[CORE, 2].min()
    if mode == 'ground' or low < -0.004:
        move_root(Vector((0, 0, -low + (0.003 if mode == 'ground' else 0.0))))


def tail_floor():
    """Bend tail segments up (about tail-direction x Z) until each segment's run clears the floor."""
    for k in range(1, 9):
        for _ in range(14):
            low = mesh_co()[TAILV[k], 2].min()
            if low > -0.003:
                break
            b = pbn[f'Tail{k}']
            d = (b.tail - b.head).normalized()
            ax = d.cross(Z)
            if ax.length < 1e-3:
                break
            P.rotate_world(rig, f'Tail{k}', ax.normalized(), 4)   # + lifts (d x Z)


def body(forward=0.0, lift=0.0, pitch=0.0, roll=0.0, yaw=0.0, pivot=None):
    move_root(Vector((0, -forward, lift - REST_DROP)))
    c = Vector((0, -0.45 - forward, 0.22 + lift - REST_DROP)) if pivot is None else Vector(pivot)
    if yaw:
        P.rotate_world(rig, 'Body', Z, yaw, c)
    if pitch:
        P.rotate_world(rig, 'Body', X, -pitch, c)
    if roll:
        P.rotate_world(rig, 'Body', Y, -roll, c)


def spine(back=0.0, chest=0.0, neck=0.0, head=0.0, head_yaw=0.0, head_roll=0.0):
    """back/chest/neck/head > 0 raise (pitch up); back < 0 arches the back up (hunch)."""
    if back:
        P.rotate_world(rig, 'Spine', X, -back)
    if chest:
        P.rotate_world(rig, 'Chest', X, -chest)
    if neck:
        P.rotate_world(rig, 'Neck', X, -neck)
    if head:
        P.rotate_world(rig, 'Head', X, -head)
    if head_yaw:
        P.rotate_world(rig, 'Neck', Z, head_yaw * 0.4)
        P.rotate_world(rig, 'Head', Z, head_yaw * 0.6)
    if head_roll:
        P.rotate_world(rig, 'Head', Y, head_roll)


PROFILES = {'even': [1.0] * 8, 'base': [1.6, 1.4, 1.2, 1.0, 0.8, 0.7, 0.6, 0.5],
            'tip': [0.3, 0.45, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]}


def tail(curl=0.0, prof='even', amp=0.0, phase=0.0, side=0.0, droop=0.0, coil=0.0):
    """curl > 0 lifts the tail and bends it forward over the back; side > 0 swings it toward +X (left); coil bends it
    round to the side progressively (a curl in the floor plane)."""
    w = PROFILES[prof]
    for i in range(1, 9):
        n = f'Tail{i}'
        if droop:
            P.rotate_world(rig, n, X, -droop)
        if curl:
            P.rotate_world(rig, n, X, curl * w[i - 1])
        yaw = side + coil * (0.4 + 0.15 * i) + amp * (0.5 + 0.12 * i) * math.sin(phase - 0.6 * i)
        if yaw:
            P.rotate_world(rig, n, Z, yaw)


def scales(spikes=SPK_IN, ball=1.0, tongue=TONGUE_IN):
    for n, s in (('TailBall', ball), ('Spikes', spikes), ('Tongue', tongue)):
        pbn[n].scale = (s, s, s)
    bpy.context.view_layer.update()


def carried(point, bone):
    return pbn[bone].matrix @ REST[bone].inverted() @ point


def set_world_rot(name, q):
    b = pbn[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, b.matrix.to_scale()); bpy.context.view_layer.update()


ADJ = {}


def foot_rot(name, carry, carrier, pitch, yaw=0.0, s=1.0):
    q = REST[name].to_quaternion()
    if carry:
        dq = (pbn[carrier].matrix @ REST[carrier].inverted()).to_quaternion()
        q = Quaternion().slerp(dq, carry) @ q
    if yaw:
        q = Quaternion(Z, math.radians(-s * yaw)) @ q
    if pitch:
        q = Quaternion(X, math.radians(pitch)) @ q
    set_world_rot(name, q)


def front_leg(s, wrist, pitch=0.0, carry=0.0, yaw=0.0):
    if carry:
        wrist = wrist.lerp(carried(wrist, 'Chest'), carry)
    wrist = wrist + Vector((0, 0, ADJ.get(('front', s), 0.0)))
    pole = carried(ELBOW[s] + Vector((SIDES[s] * 0.30, 0.0, 0.10)), 'Chest')
    P.two_bone_ik(rig, f'UpperArm_{s}', f'ForeArm_{s}', wrist, pole)
    foot_rot(f'Hand_{s}', carry, 'Chest', pitch, yaw, SIDES[s])


def hind_leg(s, ankle, pitch=0.0, carry=0.0):
    if carry:
        ankle = ankle.lerp(carried(ankle, 'Body'), carry)
    ankle = ankle + Vector((0, 0, ADJ.get(('hind', s), 0.0)))
    pole = carried(KNEE[s] + Vector((SIDES[s] * 0.20, -0.20, 0.05)), 'Body')
    P.two_bone_ik(rig, f'Thigh_{s}', f'Shin_{s}', ankle, pole)
    foot_rot(f'HindFoot_{s}', carry, 'Body', pitch)


# ---------------------------------------------------------------- locomotion
def limb_cycle(p, duty, half, lift):
    """Planted (slides back in clip space from -half to +half) for p < duty, then swings forward with a lift."""
    if p < duty:
        q = p / duty
        return -half + 2 * half * q, 0.0, 0.0
    s = (p - duty) / (1 - duty)
    k = ss(s)
    return half - 2 * half * k, lift * math.sin(math.pi * s), s


def gait(t, T, D, duty, lift, bob, sway, lean=0.0):
    u = (t / T) % 1.0
    # waddle: the shell rolls toward the planted front foot and yaws with the stride
    body(lift=bob * math.cos(4 * math.pi * u), pitch=-lean + 0.8 * math.cos(4 * math.pi * u),
         roll=sway * math.sin(2 * math.pi * u), yaw=0.5 * sway * math.sin(2 * math.pi * u))
    spine(head=-0.4 * lean + 1.5 * math.sin(4 * math.pi * u + 0.8), head_yaw=-0.9 * sway * math.sin(2 * math.pi * u))
    tail(amp=1.6 * sway, phase=2 * math.pi * u + 1.2, droop=1.2)
    scales()
    half = D * duty / 2
    for s, sg in SIDES.items():
        ph_front = u if s == 'L' else (u + 0.5) % 1.0
        ph_hind = (ph_front + 0.5) % 1.0
        y, h, sw = limb_cycle(ph_front, duty, half, lift)
        front_leg(s, WRIST[s] + Vector((sg * 0.015 * math.sin(math.pi * sw), y, h)), pitch=-18 * math.sin(math.pi * sw))
        y2, h2, sw2 = limb_cycle(ph_hind, duty, half, lift * 0.8)
        hind_leg(s, ANKLE[s] + Vector((0, y2, h2)), pitch=-12 * math.sin(math.pi * sw2))


# ---------------------------------------------------------------- keyed actions
def keyed(keys, t):
    """Smoothstep between keys. A per-side key (l_up) missing from a key takes that key's shared value (up)."""
    keys = sorted(keys, key=lambda k: k[0])
    sided = {n for _, d in keys for n in d if n[:2] in ('l_', 'r_')}
    keys = [(t0, {**{n: d.get(n[2:], DEFAULTS.get(n[2:], 0.0)) for n in sided}, **d}) for t0, d in keys]
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            k = ss((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            out = {}
            for n in set(a) | set(b):
                va, vb = a.get(n, DEFAULTS.get(n, 0.0)), b.get(n, DEFAULTS.get(n, 0.0))
                out[n] = vb if isinstance(va, str) or isinstance(vb, str) else va + (vb - va) * k
            return out
    return dict(keys[-1][1])


DEFAULTS = {'spk': SPK_IN, 'ball': 1.0, 'tongue': TONGUE_IN, 'tprof': 'even'}


def generic(k):
    g0 = lambda n: k.get(n, DEFAULTS.get(n, 0.0))
    body(forward=g0('fwd'), lift=g0('lift'), pitch=g0('pitch'), roll=g0('roll'), yaw=g0('yaw'), pivot=k.get('pivot'))
    spine(back=g0('back'), chest=g0('chest'), neck=g0('neck'), head=g0('head'), head_yaw=g0('head_yaw'),
          head_roll=g0('head_roll'))
    tail(curl=g0('tcurl'), prof=k.get('tprof', 'even'), amp=g0('tamp'), phase=g0('tphase'), side=g0('tside'),
         droop=g0('tdroop'), coil=g0('tcoil'))
    scales(spikes=g0('spk'), ball=g0('ball'), tongue=g0('tongue'))
    carry = g0('carry')
    for s, sg in SIDES.items():
        pre = s.lower() + '_'
        g = lambda n: k.get(pre + n, k.get(n, 0.0))
        w = WRIST[s] + Vector((sg * g('out'), -g('hfwd'), g('up')))
        if not carry:
            w = w + Vector((0, -g0('fwd'), 0)) * g0('follow')
        front_leg(s, w, pitch=g('hpitch'), carry=carry)
        a = ANKLE[s] + Vector((sg * g('fout'), -g('ffwd'), g('fup')))
        hind_leg(s, a, pitch=g('fpitch'), carry=carry)


# Attack (native att 0-3): forelegs rise with the claws out and the tail lifts, the tail arcs over the back as the
# spikes pop out, the mace whips down over the head at the party while the claws slam down, the beast hunches,
# the spikes go back in.
ATTACK = [(0.0, {}),
          (0.22, {'pitch': 8, 'lift': 0.015, 'fwd': -0.03, 'neck': 6, 'head': 6, 'up': 0.12, 'hfwd': 0.06,
                  'out': 0.03, 'hpitch': -35, 'tcurl': 10, 'tprof': 'base', 'spk': 0.55, 'ball': 1.05}),
          (0.42, {'pitch': 11, 'lift': 0.02, 'fwd': -0.05, 'neck': 8, 'head': 8, 'up': 0.17, 'hfwd': 0.08,
                  'out': 0.04, 'hpitch': -45, 'tcurl': 16, 'tprof': 'base', 'spk': 1.08, 'ball': 1.25}),
          (0.56, {'pitch': 9, 'lift': 0.02, 'fwd': -0.04, 'neck': 6, 'head': 4, 'up': 0.18, 'hfwd': 0.06,
                  'out': 0.04, 'hpitch': -48, 'tcurl': 18, 'tprof': 'base', 'spk': 1.0, 'ball': 1.3}),
          (0.74, {'pitch': -7, 'lift': 0.0, 'fwd': 0.10, 'back': -6, 'neck': -10, 'head': -8, 'up': 0.0,
                  'hfwd': 0.20, 'out': 0.0, 'hpitch': 25, 'follow': 1.0, 'tcurl': 25, 'tprof': 'base', 'spk': 1.0,
                  'ball': 1.35, 'ffwd': 0.0}),
          (0.88, {'pitch': -6, 'fwd': 0.08, 'back': -8, 'neck': -14, 'head': -10, 'hfwd': 0.16, 'hpitch': 35,
                  'follow': 1.0, 'tcurl': 22, 'tprof': 'base', 'spk': 1.0, 'ball': 1.3}),
          (1.08, {'pitch': -3, 'lift': -0.02, 'fwd': 0.02, 'back': -12, 'neck': -18, 'head': -14, 'hfwd': 0.02,
                  'out': -0.02, 'hpitch': 10, 'follow': 1.0, 'tcurl': 13, 'tprof': 'base', 'tcoil': 6,
                  'spk': 0.5, 'ball': 1.05}),
          (1.5, {})]
HIT = [(0.0, {}),
       (0.11, {'fwd': -0.06, 'lift': -0.03, 'pitch': -3, 'back': -8, 'neck': -16, 'head': -14, 'roll': 4,
               'tcoil': 2.5, 'tcurl': 2, 'up': 0.0, 'out': 0.02, 'hpitch': 8}),
       (0.26, {'fwd': -0.04, 'lift': -0.02, 'pitch': -2, 'back': -5, 'neck': -10, 'head': -8, 'roll': 2,
               'tcoil': 1.5}),
       (0.5, {})]
FIDGET = [(0.0, {}),
          (0.35, {'lift': -0.015, 'back': -10, 'neck': -16, 'head': -16, 'tcoil': 8, 'tcurl': 6, 'hfwd': -0.02}),
          (0.85, {'lift': -0.02, 'back': -14, 'neck': -22, 'head': -22, 'tcoil': 11, 'tcurl': 8, 'hfwd': -0.03,
                  'pitch': -2}),
          (1.25, {'lift': -0.01, 'back': -6, 'neck': -8, 'head': -6, 'tcoil': 5, 'tcurl': 4}),
          (1.55, {'neck': 4, 'head': 6, 'head_yaw': 6, 'tongue': TONGUE_IN}),
          (1.7, {'neck': 5, 'head': 8, 'head_yaw': 6, 'tongue': 1.25}),
          (1.85, {'neck': 5, 'head': 8, 'head_yaw': -4, 'tongue': 1.2}),
          (2.0, {'neck': 3, 'head': 4, 'head_yaw': -2, 'tongue': TONGUE_IN}),
          (2.4, {})]
DEATH = [(0.0, {}),
         (0.25, {'pitch': 9, 'lift': 0.02, 'neck': 14, 'head': 12, 'up': 0.08, 'out': 0.03, 'hpitch': -30,
                 'tcurl': 12, 'tamp': 8, 'tphase': 3, 'spk': 0.7}),
         (0.55, {'pitch': 3, 'roll': 30, 'neck': 4, 'head': 2, 'up': 0.04, 'hpitch': -10, 'carry': 0.6,
                 'tamp': 6, 'tphase': 6, 'tdroop': 2}),
         (1.05, {'roll': 84, 'neck': -10, 'head': -8, 'head_yaw': -10, 'up': 0.02, 'out': -0.04, 'hfwd': -0.03,
                 'l_out': -0.10, 'l_up': -0.04, 'hpitch': 25, 'fpitch': 20, 'carry': 1.0, 'tdroop': 6, 'tamp': 3,
                 'tphase': 9}),
         (1.3, {'roll': 90, 'neck': -12, 'head': -10, 'head_yaw': -12, 'up': 0.0, 'out': -0.05, 'hfwd': -0.04,
                'l_out': -0.12, 'l_up': -0.05, 'hpitch': 30, 'fpitch': 25, 'carry': 1.0, 'tdroop': 7}),
         (1.6, {'roll': 90, 'neck': -12, 'head': -10, 'head_yaw': -12, 'up': 0.0, 'out': -0.05, 'hfwd': -0.04,
                'l_out': -0.12, 'l_up': -0.05, 'hpitch': 30, 'fpitch': 25, 'carry': 1.0, 'tdroop': 7})]


def death(t):
    k = keyed(DEATH, t)
    if k.get('roll', 0) > 1:      # roll about the right-hand lower edge of the shell
        k['pivot'] = (-0.38, -0.45, 0.06 + k.get('lift', 0) - REST_DROP)
    generic(k)


def standing(t):
    flick = bump(t, 0.55, 0.85) + bump(t, 0.95, 1.2)
    generic({'lift': 0.005 * math.sin(2 * math.pi * t / 2.4), 'pitch': 0.6 * math.sin(2 * math.pi * t / 2.4),
             'head': 1.5 * math.sin(2 * math.pi * t / 2.4 + 0.6) + 3 * flick,
             'head_yaw': 2.5 * math.sin(2 * math.pi * t / 2.4 + 1.3),
             'tamp': 4.0, 'tphase': 2 * math.pi * t / 2.4, 'tdroop': 0.6,
             'tongue': TONGUE_IN + (1.0 - TONGUE_IN) * flick})


INFO = {}


def key_action(name, n, fn, loop=False, ground=None):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows, core_lows, balls = [], [], [], []
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
        balls.append(tuple(pbn['Spikes'].head))
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
        by = np.array([p[1] for p in balls]); bz = np.array([p[2] for p in balls])
        INFO[name]['ball_y'] = [round(v, 3) for v in by]
        INFO[name]['ball_z'] = [round(v, 3) for v in bz]
        f_imp = int(np.argmin(by))
        INFO[name]['impact_frame'] = f_imp; INFO[name]['impact_s'] = round(f_imp / FPS, 3)
        INFO[name]['ball_at_impact'] = [round(v, 3) for v in balls[f_imp]]
    print('CLIP', name, {k: v for k, v in INFO[name].items() if not k.startswith('ball_') or k == 'ball_at_impact'},
          flush=True)


def main():
    clips = {
        'Standing': (72, standing, True, None),
        'Walking': (30, lambda t: gait(t, 1.0, 0.45, 0.65, 0.045, 0.008, 3.0), True, None),
        'Running': (18, lambda t: gait(t, 0.6, 0.80, 0.50, 0.07, 0.016, 4.5, lean=3.0), True, None),
        'Attack': (45, lambda t: generic(keyed(ATTACK, t)), False, None),
        'Hit': (15, lambda t: generic(keyed(HIT, t)), False, None),
        'Fidget': (72, lambda t: generic(keyed(FIDGET, t)), False, None),
        'Death': (48, death, False, lambda t: 'ground' if t >= 1.15 else 'lift'),
        'Dead': (30, lambda t: death(1.6), False, lambda t: 'ground'),
    }
    for name, (n, fn, loop, ground) in clips.items():
        if _only and name not in _only:
            continue
        key_action(name, n, fn, loop=loop, ground=ground)
    for k, v in (('Walking', 0.45), ('Running', 0.80)):
        if k in INFO: INFO[k]['stride'] = v
    info_path = os.path.join(WORK, 'anim_info.json')
    old = json.load(open(info_path))['clips'] if (_only and os.path.exists(info_path)) else {}
    old.update(INFO)
    json.dump({'clips': old, 'rest_drop_cm': round(REST_DROP * 100, 2)}, open(info_path, 'w'), indent=1)
    P.reset(rig)
    rig.animation_data.action = bpy.data.actions['Standing'] if 'Standing' in bpy.data.actions else None
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, _dst))
    print('SAVED', _dst)


main()
