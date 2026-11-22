"""Procedural clips for the Xeen moles (quadruped playbook: limbs on IK targets, every frame checked against the
floor). Native Xeen frames (front only, 011.mon / 011.att): an idle with a breathing heave, a twitching snout and
narrowing eyes; an attack: att 1 the left claw raised and swiped across, att 2 both hands thrown forward and down
at the viewer with the claws splayed, att 3 the claws digging in. No walk, hit or death frames: those follow mole
anatomy (front paddles that stroke back and out like a swimmer, small hind feet under the rump).

Front legs: two-bone IK (UpperArm + ForeArm) to a wrist target, elbow pole out-back-up carried by the Chest; the
Hand keeps its rest orientation plus a pitch (claws down > 0); Claws curl about their local X. Hind legs: Thigh +
HindFoot IK to the toe target, knee out-forward-up. Body pitch > 0 raises the front, roll > 0 lifts the left side.
Floor rules every frame: the core (trunk, head, snout, thighs) is lifted when it sinks; a hand or hind foot whose
vertices dip under the floor gets its target raised; the tail bends up segment by segment until it clears. The
bind pose stands 3.4 cm high on its claw tips (the dropped fur shingles reached lower), so every clip lowers the
root by that amount: the claws meet the floor.

  Standing  2.0 s loop   breathing heave, snout twitches, small head drift, tail sway
  Walking   0.8 s loop   paddle gait (LF+RH / RF+LH), 0.60 m per cycle
  Running   0.5 s loop   same, longer and lower, 0.95 m per cycle
  Attack    1.0 s        rears, both claws raised and splayed, thrown forward and down (IMPACT measured), dig in
  Hit       0.5 s        jolts back, head up, hands flinch
  Death     1.5 s        rears in pain, rolls onto its right side, claws curl
  Dead      1.0 s        Death's last pose
  Fidget    2.0 s        digs: left then right hand scrape the ground, snout sniffs
Reads work/anim_base.blend (UV master), writes work/anim_v1.blend and work/anim_info.json."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
_only = '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 1
_src = 'anim_v1.blend' if _only and os.path.exists(os.path.join(WORK, 'anim_v1.blend')) else 'anim_base.blend'
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, _src))   # a partial rerun keeps the other clips
rig = bpy.data.objects['Dillo_Rig']; mesh = bpy.data.objects['Dillo']
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
FPS = 30
SIDES = {'L': 1.0, 'R': -1.0}
CURL = -1.0         # curl > 0 bends the claws down into a grip (review/curl_sheet.png); splays (< 0) stay above -12

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
TOE = {s: pbn[f'HindFoot_{s}'].tail.copy() for s in SIDES}
KNEE = {s: pbn[f'HindFoot_{s}'].head.copy() for s in SIDES}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    if t <= a or t >= b:
        return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
LIMB_MASK = {('front', s): np.isin(_dom, (f'Hand_{s}', f'Claws_{s}')) for s in SIDES}
LIMB_MASK.update({('hind', s): np.isin(_dom, (f'HindFoot_{s}',)) for s in SIDES})
TAILV = {k: np.isin(_dom, [f'Tail{i}' for i in range(k, 5)]) for k in range(1, 5)}
LIMB = np.isin(_dom, [f'{n}_{s}' for n in ('Hand', 'Claws', 'ForeArm', 'HindFoot') for s in SIDES])
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
    """'lift': raise the mole when the core sinks; 'ground': the lowest core point on the floor (lying poses)."""
    co = mesh_co()
    low = co[CORE, 2].min()
    if mode == 'ground' or low < -0.004:
        move_root(Vector((0, 0, -low + (0.003 if mode == 'ground' else 0.0))))


def tail_floor():
    """Bend tail segments up (toward world up, about tail-direction x Z) until each segment's run clears."""
    for k in range(1, 5):
        for _ in range(14):
            low = mesh_co()[TAILV[k], 2].min()
            if low > -0.003:
                break
            b = pbn[f'Tail{k}']
            d = (b.tail - b.head).normalized()
            ax = d.cross(Z)
            if ax.length < 1e-3:
                break
            P.rotate_world(rig, f'Tail{k}', ax.normalized(), 6)


def body(forward=0.0, lift=0.0, pitch=0.0, roll=0.0, yaw=0.0, pivot=None):
    move_root(Vector((0, -forward, lift - REST_DROP)))
    c = Vector((0, 0.05 - forward, 0.28 + lift - REST_DROP)) if pivot is None else Vector(pivot)
    if yaw:
        P.rotate_world(rig, 'Body', Z, yaw, c)
    if pitch:
        P.rotate_world(rig, 'Body', X, -pitch, c)
    if roll:
        P.rotate_world(rig, 'Body', Y, -roll, c)


def spine(chest=0.0, head=0.0, head_yaw=0.0, head_roll=0.0, snout=0.0, snout_yaw=0.0):
    """chest/head/snout > 0 raise (pitch up)."""
    if chest:
        P.rotate_world(rig, 'Chest', X, -chest)
    if head:
        P.rotate_world(rig, 'Head', X, -head)
    if head_yaw:
        P.rotate_world(rig, 'Head', Z, head_yaw)
    if head_roll:
        P.rotate_world(rig, 'Head', Y, head_roll)
    if snout:
        P.rotate_world(rig, 'Snout', X, -snout)
    if snout_yaw:
        P.rotate_world(rig, 'Snout', Z, snout_yaw)


def tail(phase, amp=8.0, lift=0.0):
    for i in range(1, 5):
        if lift:
            P.rotate_world(rig, f'Tail{i}', X, -lift / 4)
        if amp:
            P.rotate_world(rig, f'Tail{i}', Z, amp * (0.6 + 0.2 * i) * math.sin(phase - 0.7 * i))


def carried(point, bone):
    return pbn[bone].matrix @ REST[bone].inverted() @ point


def set_world_rot(name, q):
    b = pbn[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, b.matrix.to_scale()); bpy.context.view_layer.update()


ADJ = {}


def front_leg(s, wrist, hand_pitch=0.0, curl=0.0, hand_yaw=0.0, carry=0.0):
    """wrist: target in world (carry 0) or in rest body space carried by the Chest (carry 1)."""
    if carry:
        wrist = wrist.lerp(carried(wrist, 'Chest'), carry)
    wrist = wrist + Vector((0, 0, ADJ.get(('front', s), 0.0)))
    pole = carried(ELBOW[s] + Vector((SIDES[s] * 0.25, 0.20, 0.20)), 'Chest')
    P.two_bone_ik(rig, f'UpperArm_{s}', f'ForeArm_{s}', wrist, pole)
    q = REST[f'Hand_{s}'].to_quaternion()
    if carry:
        dq = (pbn['Chest'].matrix @ REST['Chest'].inverted()).to_quaternion()
        q = Quaternion().slerp(dq, carry) @ q
    if hand_yaw:
        q = Quaternion(Z, math.radians(-SIDES[s] * hand_yaw)) @ q
    if hand_pitch:
        q = Quaternion(X, math.radians(hand_pitch)) @ q
    set_world_rot(f'Hand_{s}', q)
    if curl:
        P.rotate_local(rig, f'Claws_{s}', 'X', CURL * curl)


def hind_leg(s, toe, carry=0.0):
    if carry:
        toe = toe.lerp(carried(toe, 'Body'), carry)
    toe = toe + Vector((0, 0, ADJ.get(('hind', s), 0.0)))
    pole = carried(KNEE[s] + Vector((SIDES[s] * 0.30, -0.15, 0.20)), 'Body')
    P.two_bone_ik(rig, f'Thigh_{s}', f'HindFoot_{s}', toe, pole)


# ---------------------------------------------------------------- locomotion
def limb_cycle(p, duty, half, lift):
    """Planted (slides back in clip space from -half to +half) for p < duty, then swings forward with a lift."""
    if p < duty:
        q = p / duty
        return -half + 2 * half * q, 0.0, q, 0.0
    s = (p - duty) / (1 - duty)
    k = ss(s)
    return half - 2 * half * k, lift * math.sin(math.pi * s), 1 - k, s


def gait(t, T, D, duty, hand_lift, foot_lift, bob, sway, lean=0.0):
    u = (t / T) % 1.0
    body(lift=bob * math.cos(4 * math.pi * u), pitch=-lean + 1.2 * math.cos(4 * math.pi * u),
         roll=sway * math.sin(2 * math.pi * u), yaw=0.6 * sway * math.sin(2 * math.pi * u))
    spine(head=-0.4 * lean + 1.5 * math.sin(4 * math.pi * u + 0.8), head_yaw=-0.8 * sway * math.sin(2 * math.pi * u),
          snout=2.0 * math.sin(4 * math.pi * u + 1.6))
    tail(2 * math.pi * u, amp=6.0)
    half = D * duty / 2
    for s, sg in SIDES.items():
        ph_front = u if s == 'L' else (u + 0.5) % 1.0
        ph_hind = (ph_front + 0.5) % 1.0
        y, h, q, sw = limb_cycle(ph_front, duty, half, hand_lift)
        # swimmer's stroke: the hand reaches in front, pushes back and out, swings forward close to the body
        x = sg * (-0.05 + 0.09 * q + 0.04 * math.sin(math.pi * sw))
        w = WRIST[s] + Vector((x, y + 0.06, h))
        front_leg(s, w, hand_pitch=-25 * math.sin(math.pi * sw) + 8 * (1 - q) * (sw == 0), curl=-8 * math.sin(math.pi * sw))
        y2, h2, _, _ = limb_cycle(ph_hind, duty, min(half, 0.07), foot_lift)
        hind_leg(s, TOE[s] + Vector((0, y2, h2)))


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
    spine(chest=k.get('chest', 0), head=k.get('head', 0), head_yaw=k.get('head_yaw', 0),
          snout=k.get('snout', 0), snout_yaw=k.get('snout_yaw', 0))
    tail(k.get('tphase', 0.0), amp=k.get('tamp', 0.0), lift=k.get('tlift', 0.0))
    carry = k.get('carry', 0.0)
    for s, sg in SIDES.items():
        pre = s.lower() + '_'
        g = lambda n: k.get(pre + n, k.get(n, 0.0))
        w = WRIST[s] + Vector((sg * g('out'), -g('hfwd'), g('up')))
        if not carry:
            w = w + Vector((0, -k.get('fwd', 0), 0)) * k.get('follow', 0.0)
        front_leg(s, w, hand_pitch=g('hpitch'), curl=g('curl'), hand_yaw=g('hyaw'), carry=carry)
        hind_leg(s, TOE[s] + Vector((0, -k.get('ffwd', 0), 0)), carry=carry)


# Attack: wind up (rear, both claws raised and splayed back), throw both hands forward and down at the party
# (native att 2), claws dig in (att 3), recover. The left hand leads by a few frames (att 1's swipe across).
ATTACK = [(0.0, {}),
          (0.22, {'pitch': 9, 'lift': 0.02, 'fwd': -0.05, 'head': 10, 'snout': 8, 'up': 0.17, 'hfwd': 0.02,
                  'out': 0.03, 'hpitch': -40, 'curl': -10, 'tlift': 20}),
          (0.34, {'pitch': 12, 'lift': 0.03, 'fwd': -0.06, 'head': 12, 'snout': 10, 'up': 0.21, 'hfwd': 0.0,
                  'out': 0.04, 'hpitch': -50, 'curl': -12, 'l_up': 0.24, 'l_hpitch': -55, 'tlift': 25}),
          (0.48, {'pitch': -5, 'lift': 0.0, 'fwd': 0.14, 'head': -6, 'snout': -4, 'up': 0.0, 'hfwd': 0.27,
                  'out': -0.02, 'hpitch': 20, 'curl': 20, 'follow': 1.0, 'tlift': 5}),
          (0.62, {'pitch': -4, 'fwd': 0.10, 'head': -8, 'snout': -6, 'up': 0.0, 'hfwd': 0.20, 'out': 0.0,
                  'hpitch': 45, 'curl': 45, 'follow': 1.0}),
          (0.82, {'pitch': -1, 'fwd': 0.03, 'head': -2, 'hfwd': 0.06, 'hpitch': 12, 'curl': 12, 'follow': 1.0}),
          (1.0, {})]
HIT = [(0.0, {}),
       (0.08, {'fwd': -0.09, 'lift': 0.01, 'pitch': 6, 'head': 14, 'snout': 12, 'roll': 4, 'up': 0.06, 'out': 0.03,
               'hpitch': -20, 'curl': -10, 'tlift': 15}),
       (0.24, {'fwd': -0.06, 'pitch': 3, 'head': 6, 'snout': 4, 'roll': 2, 'up': 0.02, 'hpitch': -8, 'curl': -5}),
       (0.5, {})]
FIDGET = [(0.0, {}),
          (0.25, {'head': -6, 'snout': -10, 'l_up': 0.08, 'l_hfwd': 0.10, 'l_hpitch': -20, 'pitch': -2}),
          (0.45, {'head': -8, 'snout': -12, 'l_up': 0.0, 'l_hfwd': 0.12, 'l_hpitch': 40, 'l_curl': 30, 'pitch': -3}),
          (0.65, {'head': -6, 'snout': -10, 'l_up': 0.0, 'l_hfwd': -0.06, 'l_hpitch': 30, 'l_curl': 35}),
          (0.85, {'head': -6, 'snout': -10, 'r_up': 0.08, 'r_hfwd': 0.10, 'r_hpitch': -20, 'pitch': -2}),
          (1.05, {'head': -8, 'snout': -12, 'r_up': 0.0, 'r_hfwd': 0.12, 'r_hpitch': 40, 'r_curl': 30, 'pitch': -3}),
          (1.25, {'head': -6, 'snout': -10, 'r_up': 0.0, 'r_hfwd': -0.06, 'r_hpitch': 30, 'r_curl': 35}),
          (1.45, {'head': 2, 'snout': 6, 'snout_yaw': 8}), (1.6, {'head': 3, 'snout': 8, 'snout_yaw': -8}),
          (1.75, {'head': 2, 'snout': 5, 'snout_yaw': 6}), (2.0, {})]
DEATH = [(0.0, {}),
         (0.25, {'pitch': 14, 'lift': 0.03, 'head': 20, 'snout': 15, 'up': 0.12, 'out': 0.04, 'hpitch': -35,
                 'curl': -12, 'tlift': 25, 'tamp': 10, 'tphase': 3}),
         (0.5, {'pitch': 6, 'roll': 30, 'head': 6, 'snout': 4, 'up': 0.05, 'hpitch': -10, 'curl': 10, 'carry': 0.6,
                'tamp': 8, 'tphase': 6}),
         (0.95, {'roll': 82, 'head': -10, 'head_yaw': -10, 'snout': -8, 'up': 0.03, 'out': -0.05, 'hfwd': -0.04,
                 'l_out': -0.13, 'l_up': -0.05, 'l_hfwd': 0.06,
                 'hpitch': 20, 'curl': 55, 'carry': 1.0, 'tamp': 4, 'tphase': 9}),
         (1.2, {'roll': 90, 'head': -14, 'head_yaw': -12, 'snout': -10, 'up': 0.0, 'out': -0.06, 'hfwd': -0.05,
                'l_out': -0.15, 'l_up': -0.07, 'l_hfwd': 0.08,
                'hpitch': 25, 'curl': 65, 'carry': 1.0}),
         (1.5, {'roll': 90, 'head': -14, 'head_yaw': -12, 'snout': -10, 'up': 0.0, 'out': -0.06, 'hfwd': -0.05,
                'l_out': -0.15, 'l_up': -0.07, 'l_hfwd': 0.08,
                'hpitch': 25, 'curl': 65, 'carry': 1.0})]


def death(t):
    k = keyed(DEATH, t)
    if k.get('roll', 0) > 1:      # roll about the right-hand lower edge of the trunk
        k['pivot'] = (-0.32, 0.05, 0.05 + k.get('lift', 0) - REST_DROP)
    generic(k)


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
        tips.append([tuple(pbn[f'Claws_{s}'].tail) for s in SIDES])
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
                  'core_lowest_cm': round(min(core_lows) * 100, 2), 'adj': {f'{a}_{b}': round(v, 3) for (a, b), v in ADJ.items()}}
    if name == 'Attack':
        tipy = np.array([[p[1] for p in fr] for fr in tips]).mean(1)
        tipz = np.array([[p[2] for p in fr] for fr in tips]).mean(1)
        INFO[name]['claw_tip_y'] = [round(v, 3) for v in tipy]
        INFO[name]['claw_tip_z'] = [round(v, 3) for v in tipz]
        f_imp = int(np.argmin(tipy))
        INFO[name]['impact_frame'] = f_imp; INFO[name]['impact_s'] = round(f_imp / FPS, 3)
    print('CLIP', name, {k: v for k, v in INFO[name].items() if not k.startswith('claw_tip')}, flush=True)


def main():
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    clips = {
        'Standing': (60, lambda t: generic({'lift': 0.006 * math.sin(math.pi * t), 'pitch': 0.8 * math.sin(math.pi * t),
                                            'head': 1.5 * math.sin(math.pi * t + 0.6),
                                            'head_yaw': 2.5 * math.sin(math.pi * t + 1.3),
                                            'snout': 4 * bump(t, 0.3, 0.55) + 3 * bump(t, 1.2, 1.4),
                                            'snout_yaw': 6 * math.sin(2 * math.pi * 3 * t) * (bump(t, 0.25, 0.75) + bump(t, 1.15, 1.5)),
                                            'tphase': math.pi * t, 'tamp': 5.0}), True, None),
        'Walking': (24, lambda t: gait(t, 0.8, 0.60, 0.62, 0.07, 0.035, 0.010, 3.0), True, None),
        'Running': (15, lambda t: gait(t, 0.5, 0.95, 0.48, 0.10, 0.05, 0.020, 4.0, lean=4.0), True, None),
        'Attack': (30, lambda t: generic(keyed(ATTACK, t)), False, None),
        'Hit': (15, lambda t: generic(keyed(HIT, t)), False, None),
        'Fidget': (60, lambda t: generic(keyed(FIDGET, t)), False, None),
        'Death': (45, death, False, lambda t: 'ground' if t >= 1.05 else 'lift'),
        'Dead': (30, lambda t: death(1.5), False, lambda t: 'ground'),
    }
    for name, (n, fn, loop, ground) in clips.items():
        if only and name not in only:
            continue
        key_action(name, n, fn, loop=loop, ground=ground)
    for k, v in (('Walking', 0.60), ('Running', 0.95)):
        if k in INFO: INFO[k]['stride'] = v
    info_path = os.path.join(WORK, 'anim_info.json')
    old = json.load(open(info_path))['clips'] if (only and os.path.exists(info_path)) else {}
    old.update(INFO)
    json.dump({'clips': old, 'rest_drop_cm': round(REST_DROP * 100, 2)}, open(info_path, 'w'), indent=1)
    P.reset(rig)
    rig.animation_data.action = bpy.data.actions['Standing'] if 'Standing' in bpy.data.actions else None
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'anim_v1.blend'))
    print('SAVED anim_v1.blend')


main()
