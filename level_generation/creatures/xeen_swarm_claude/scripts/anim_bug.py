"""Procedural clips of the Doom Bug (giant cricket; quadruped playbook, segmented creatures). Legs: femur + tibia two-bone
IK to the tarsus root, knee pole up and out carried by the body, the tarsus keeps its rest direction; every foot is
pushed out of the floor per frame. Gait: alternating tripod (L1 R2 L3 / R1 L2 R3). The Xeen frames show only an idle
(front view, green drool); actions follow cricket anatomy.

  Standing  2.0 s loop   breathing, antennae sway, palps work
  Walking   0.8 s loop   tripod, 0.70 m per cycle
  Running   0.5 s loop   tripod, lower, 0.80 m per cycle
  Attack    0.9 s        rears on the hind legs, lunges and bites: IMPACT 0.42 s
  Hit       0.5 s        jolt back and down
  Death     1.5 s        rears, flips onto its back, legs curl
  Dead      held
  Fidget    2.0 s        head turns, a front leg cleans an antenna
Reads work/bug_anim_base.blend or work/bug_rig.blend, writes work/bug_anim.blend, work/bug_anim_info.json."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ = os.path.join(HERE, 'work')
src = os.path.join(W_, 'bug_anim_base.blend')
bpy.ops.wm.open_mainfile(filepath=src if os.path.exists(src) else os.path.join(W_, 'bug_rig.blend'))
rig = bpy.data.objects['Bug_Rig']; mesh = bpy.data.objects['Bug']
info = json.load(open(os.path.join(W_, 'bug_rig.json')))
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
FPS = 30; IMPACT = 0.42
for b in rig.pose.bones: b.rotation_mode = 'QUATERNION'
P.reset(rig)
pb = rig.pose.bones
REST = {b.name: b.matrix.copy() for b in pb}
LEGS = {l['key']: l for l in info['legs']}
HEAD = info['head']; ANT = info['antennae']
SIDE = {'L': 1.0, 'R': -1.0}
GROUP_A = ('L1', 'R2', 'L3')
_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] for v in mesh.data.vertices])
tree = info['tree']


def desc(name):
    out = {name}
    for c, p in tree.items():
        if p == name: out |= desc(c)
    return out


FOOTSET = {k: desc(l['chain'][-1]) for k, l in LEGS.items()}
LEGSET = set().union(*[desc(l['chain'][0]) for l in LEGS.values()])
FOOTMASK = {k: np.isin(_dom, list(s)) for k, s in FOOTSET.items()}
CORE = ~np.isin(_dom, list(LEGSET))


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


REST_CO = mesh_co()
ANKLE = {k: pb[l['chain'][-1]].head.copy() for k, l in LEGS.items()}
# each foot's target height: its claws on the floor (front feet float 8-12 cm in the Meshy rest pose)
FOOT_DROP = {k: float(REST_CO[FOOTMASK[k], 2].min()) for k in LEGS}
KNEE = {k: pb[l['chain'][1]].head.copy() for k, l in LEGS.items()}
ADJ = {}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    return 0.0 if t <= a or t >= b else math.sin(math.pi * (t - a) / (b - a)) ** 2


def body(fwd=0.0, lift=0.0, pitch=0.0, roll=0.0, yaw=0.0, pivot=None):
    root = pb['Body']
    root.matrix = Matrix.Translation(Vector((0, -fwd, lift))) @ root.matrix; bpy.context.view_layer.update()
    c = Vector((0, 0.1 - fwd, 0.3 + lift)) if pivot is None else Vector(pivot)
    if yaw: P.rotate_world(rig, 'Body', Z, yaw, c)
    if pitch: P.rotate_world(rig, 'Body', X, pitch, c)
    if roll: P.rotate_world(rig, 'Body', Y, -roll, c)


def head(pitch=0.0, yaw=0.0, ant=0.0, t=0.0):
    if pitch: P.rotate_world(rig, HEAD, X, pitch)
    if yaw: P.rotate_world(rig, HEAD, Z, yaw)
    for k, a in enumerate(ANT):
        P.rotate_local(rig, a, 'X', 8 * math.sin(2 * math.pi * 0.8 * t + k * 1.7) + ant)
        P.rotate_local(rig, a, 'Z', 6 * math.sin(2 * math.pi * 0.55 * t + k))


def carried(point, bone):
    return pb[bone].matrix @ REST[bone].inverted() @ point


def leg(k, off=Vector(), free=None):
    l = LEGS[k]; ch = l['chain']
    if free is not None:                                   # FK: femur (lift deg, swing deg), tibia flex deg
        lift, swing, flex = free
        P.rotate_world(rig, ch[0], Z, swing * SIDE[k[0]])
        P.rotate_world(rig, ch[0], (pb[ch[0]].tail - pb[ch[0]].head).cross(Z).normalized(), lift)
        if len(ch) > 1: P.rotate_local(rig, ch[1], 'X', flex)
        return
    target = ANKLE[k] - Vector((0, 0, FOOT_DROP[k])) + off + Vector((0, 0, ADJ.get(k, 0.0)))
    if len(ch) < 3:
        return
    pole = carried(KNEE[k] + Vector((SIDE[k[0]] * (0.1 if k[1] == '3' else 0.15), 0, 0.5 if k[1] == '3' else 0.35)), 'Body')
    P.two_bone_ik(rig, ch[0], ch[1], target, pole)
    tq = REST[ch[2]].to_quaternion()
    b = pb[ch[2]]; b.matrix = Matrix.LocRotScale(b.head.copy(), tq, Vector((1, 1, 1))); bpy.context.view_layer.update()


def gait(t, T, D, H, duty, low=0.0):
    u0 = (t / T) % 1.0
    body(lift=-low + 0.012 * math.cos(4 * math.pi * u0), roll=2 * math.sin(2 * math.pi * u0))
    head(pitch=2 * math.sin(4 * math.pi * u0), t=t)
    for k in LEGS:
        u = (u0 + (0.0 if k in GROUP_A else 0.5)) % 1.0
        d = D * (0.45 if k[1] == '3' else 1.0)          # the big jumping legs only shuffle when walking
        if u < duty:
            y = -d / 2 + d * (u / duty); z = 0.0
        else:
            s = (u - duty) / (1 - duty)
            y = d / 2 - d * ss(s); z = H * math.sin(math.pi * s)
        leg(k, Vector((0, y, z)))


def standing(t):
    br = math.sin(2 * math.pi * t / 2.0)
    body(lift=0.006 * br, pitch=0.8 * br)
    head(pitch=1.5 * math.sin(2 * math.pi * t / 2.0 + 1), yaw=3 * math.sin(2 * math.pi * t / 2.0), t=t)
    for k in LEGS: leg(k)


def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            k = ss((t - t0) / (t1 - t0)); return {n: a.get(n, 0) + (b.get(n, 0) - a.get(n, 0)) * k for n in set(a) | set(b)}
    return dict(keys[-1][1])


def generic(k, t):
    body(fwd=k.get('fwd', 0), lift=k.get('lift', 0), pitch=k.get('pitch', 0), roll=k.get('roll', 0))
    head(pitch=k.get('head', 0), yaw=k.get('hyaw', 0), ant=k.get('ant', 0), t=t)
    for name in LEGS:
        off = Vector((0, -k.get('front_reach', 0) if name[1] == '1' else 0, k.get('front_up', 0) if name[1] == '1' else 0))
        if name == 'L1' and k.get('clean', 0):
            off += Vector((-0.1, -0.15, 0.3)) * k['clean']
        leg(name, off)


ATTACK = [(0.0, {}), (0.25, {'fwd': -0.10, 'pitch': 14, 'head': -10, 'ant': -15, 'front_up': 0.12, 'front_reach': -0.05}),
          (0.42, {'fwd': 0.22, 'pitch': -6, 'head': 18, 'ant': 10, 'front_reach': 0.1}),
          (0.55, {'fwd': 0.18, 'pitch': -4, 'head': 12}), (0.9, {})]
HIT = [(0.0, {}), (0.08, {'fwd': -0.12, 'lift': -0.03, 'pitch': -5, 'head': -10, 'roll': 5}), (0.25, {'fwd': -0.06, 'roll': 2}),
       (0.5, {})]
FIDGET = [(0.0, {}), (0.35, {'hyaw': 18, 'head': -4}), (0.8, {'hyaw': 18, 'head': -8, 'clean': 1.0}),
          (1.3, {'hyaw': 10, 'head': -6, 'clean': 1.0}), (1.7, {'hyaw': 0}), (2.0, {})]


def death(t):
    k = ss(t / 0.4); flip = ss((t - 0.25) / 0.7); curl = ss((t - 0.5) / 0.7)
    c = Vector((0, 0.1, 0.35 + 0.25 * bump(t, 0.1, 0.9)))
    root = pb['Body']
    root.matrix = Matrix.Translation(Vector((0, 0, 0.25 * bump(t, 0.1, 0.9)))) @ root.matrix; bpy.context.view_layer.update()
    P.rotate_world(rig, 'Body', X, 20 * bump(t, 0.0, 0.6), c)
    P.rotate_world(rig, 'Body', Y, 180 * flip, c)
    head(pitch=-20 * curl, ant=-30 * curl, t=0)
    tw = math.sin(2 * math.pi * 6 * t) * bump(t, 0.8, 1.4)
    for name in LEGS:
        leg(name, free=(35 * curl + 6 * tw, 0, 45 * curl))   # + lifts toward the sky: belly up, legs curl up


INFO = {}


def key_action(name, n, fn, loop=False, ground='lift'):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows = [], []
    for f in range(n + 1):
        t = (f % n) / FPS if loop else f / FPS
        ADJ.clear(); P.reset(rig); fn(t)
        g = ground(t) if callable(ground) else ground
        if g == 'lift':
            for _ in range(3):
                co = mesh_co(); moved = False
                for k, mask in FOOTMASK.items():
                    lo = co[mask, 2].min()
                    if lo < -0.006:
                        ADJ[k] = ADJ.get(k, 0.0) - lo + 0.002; moved = True
                if not moved: break
                P.reset(rig); fn(t)
            co = mesh_co(); lo = co[CORE, 2].min()
            if lo < -0.004:
                r = pb['Body']; r.matrix = Matrix.Translation(Vector((0, 0, -lo))) @ r.matrix; bpy.context.view_layer.update()
        else:
            co = mesh_co(); lo = co[:, 2].min()
            if g == 'ground' or lo < -0.004:
                r = pb['Body']; r.matrix = Matrix.Translation(Vector((0, 0, -lo + 0.002))) @ r.matrix
                bpy.context.view_layer.update()
        lows.append(float(mesh_co()[:, 2].min()))
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in pb})
    if loop: poses[-1] = poses[0]
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, pose in enumerate(poses):
        for b in pb:
            q, loc, sc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0: q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc; b.scale = sc
            for path in ('rotation_quaternion', 'location', 'scale'):
                b.keyframe_insert(path, frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n; act['fps'] = FPS
    rig.animation_data.action = None
    INFO[name] = {'seconds': round(n / FPS, 4), 'lowest_cm': [round(min(lows) * 100, 2), round(max(lows) * 100, 2)]}
    print('CLIP', name, INFO[name], flush=True)


key_action('Standing', 60, standing, True)
key_action('Walking', 24, lambda t: gait(t, 0.8, 0.70, 0.10, 0.6), True)
key_action('Running', 15, lambda t: gait(t, 0.5, 0.80, 0.12, 0.5, low=0.03), True)
key_action('Attack', 27, lambda t: generic(keyed(ATTACK, t), t))
key_action('Hit', 15, lambda t: generic(keyed(HIT, t), t))
key_action('Fidget', 60, lambda t: generic(keyed(FIDGET, t), t))
key_action('Death', 45, death, ground=lambda t: 'ground' if t >= 1.2 else 'lift_all')
key_action('Dead', 30, lambda t: death(1.5), ground='ground')
INFO['Walking']['stride'] = 0.70; INFO['Running']['stride'] = 0.80
json.dump({'clips': INFO, 'impact': IMPACT}, open(os.path.join(W_, 'bug_anim_info.json'), 'w'), indent=1)
P.reset(rig); rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W_, 'bug_anim.blend'))
print('SAVED bug_anim.blend')
