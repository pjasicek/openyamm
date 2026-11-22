"""Procedural clips for the Carnage Hand (30 fps), after the Clouds of Xeen frames (sprites/xeen/049.mon, 049.att):
a huge disembodied right hand with a fanged mouth in the palm, hovering. Native idle: the hand closes to a fist and
opens through half open to fully spread twice per cycle, the mouth bared whenever it is open. Native attack: fist,
spread with the mouth, a lunge with the fingers splayed and the maw gaping, then palm down clawing.
  Standing   2.4 s loop  hover bob; two open-close cycles: fist -> half -> spread -> half -> fist (fingers in a
                         small wave, pinky leading), the lip lids opening with the hand
  Walking    1.6 s loop  flying forward: leaned 14 deg toward the travel direction, half open, a crawling finger wave
  Running    1.2 s loop  leaned 22 deg, faster wave
  Attack     1.0 s       draws back and up while spreading and gaping (native att 1), lunges 9 cm (att 2) and bites:
                         the lids snap shut and the fingers clamp at IMPACT (0.45 s), then claws back into the fist
  Hit        0.5 s       knocked back with a twist, the fingers spasm open and the mouth gasps
  Death      1.5 s       spasm (spread, gaping), clench, rolls palm down and drops to the floor: lies on its curled
                         fingertips and heel, the mouth shut
  Dead       1.0 s       Death's last pose
  Fidget     2.0 s       opens to half, drums the fingers pinky to index twice, cracks back into the fist
One-shot clips start and end on Standing frame 0 (the fist). Flyer floor rule (CLAUDE_QUADRUPED_PLAYBOOK.md,
Flyers): one uniform lift for every living clip so that their lowest point meets the floor; the death eases it out
and grounds the corpse. Reads work/anim_base.blend, writes work/anim_v1.blend and work/anim_info.json (with the
contact gate: per clip the most finger-on-other-part triangle overlaps in a frame)."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import handpose as H

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
rig = bpy.data.objects['Hand_Rig']; mesh = bpy.data.objects['Hand']
FPS = 30
IMPACT = 0.45
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
BASE_ROLL, BASE_PITCH = -25.0, -10.0     # fingers lean to the image left, palm tilted a little up to the party
LIPS_OPEN = 55.0
FIST = {'Thumb': (35, 35, 40), 'Index': (70, 85, 60), 'Middle': (70, 85, 60), 'Ring': (70, 85, 60),
        'Pinky': (70, 85, 60)}
SPREAD = {'Thumb': (-15, -15, -10), 'Index': (-30, -30, -20), 'Middle': (-30, -30, -20), 'Ring': (-30, -30, -20),
          'Pinky': (-30, -30, -20)}
CLAW = {'Thumb': (20, 25, 30), 'Index': (25, 55, 55), 'Middle': (25, 55, 55), 'Ring': (25, 55, 55),
        'Pinky': (25, 55, 55)}
ORDER = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
H.reset(rig)
_dg = bpy.context.evaluated_depsgraph_get()


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def pose(open_=0.5, fingers=None, lips=None, claw=0.0, lift=0.0, forward=0.0, side=0.0, pitch=0.0, yaw=0.0,
         roll=0.0, wave=None):
    """open_: hand openness (0 fist, 0.5 rest, 1 spread); fingers: per-finger openness overrides; wave: per-finger
    extra flex (degrees on joints 2 and 3); claw: blend toward the clawed reach (att 3); lips: lid angle (default
    from the openness); body: lift/forward (m), pitch + = fingers tip toward the party, yaw + = turn left, roll + =
    lean fingers to +X (degrees), on top of the base orientation."""
    H.reset(rig)
    flex = {}
    for f in ORDER:
        o = (fingers or {}).get(f, open_)
        if o < 0.5:
            k = 1 - o / 0.5; a = [x * k for x in FIST[f]]
        else:
            k = (o - 0.5) / 0.5; a = [x * k for x in SPREAD[f]]
        if claw:
            a = [x * (1 - claw) + c * claw for x, c in zip(a, CLAW[f])]
        if wave:
            w = wave.get(f, 0.0); a = [a[0] + 0.3 * w, a[1] + w, a[2] + 0.7 * w]
        flex[f] = tuple(a)
    sp = 14 * max(0.0, (open_ - 0.5) / 0.5) - 5 * max(0.0, (0.5 - open_) / 0.5)
    if lips is None:
        lips = LIPS_OPEN * ss((open_ - 0.2) / 0.5)
    H.hand(rig, flex, spread=sp * (1 - claw), lips=max(0.0, lips))
    root = rig.pose.bones['Root']
    H.rot_about(rig, 'Root', Z, yaw)
    H.rot_about(rig, 'Root', X, BASE_PITCH + pitch)          # + about X tips the fingers (+Z) toward -Y
    H.rot_about(rig, 'Root', Y, BASE_ROLL + roll)
    root.matrix = Matrix.Translation(Vector((side, -forward, lift))) @ root.matrix
    bpy.context.view_layer.update()


def evaluated():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
    ev.to_mesh_clear()
    return co.reshape(-1, 3)


def lowest():
    return float(evaluated()[:, 2].min())


# contact gate: faces by dominant bone; distal finger faces (bones _2, _3) against every face of another finger,
# the palm skin away from that finger's own knuckle, the lids and the fangs
me0 = mesh.data
gname = {g.index: g.name for g in mesh.vertex_groups}
dom = []
for v in me0.vertices:
    dom.append(gname[max(v.groups, key=lambda e: e.weight).group] if v.groups else 'Palm')
tris = np.array([p.vertices[:] for p in me0.polygons])
fdom = [max(set(dom[i] for i in t), key=[dom[i] for i in t].count) for t in tris]
DIST = {f: [k for k, d in enumerate(fdom) if d in (f + '_2', f + '_3')] for f in ORDER}
OTHER = {f: [k for k, d in enumerate(fdom) if not d.startswith(f)] for f in ORDER}


def contacts():
    co = evaluated()
    worst = 0
    for f in ORDER:
        a = BVHTree.FromPolygons(co.tolist(), tris[DIST[f]].tolist())
        b = BVHTree.FromPolygons(co.tolist(), tris[OTHER[f]].tolist())
        worst = max(worst, len(a.overlap(b)))
    return worst


def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6))
            ks = set(a) | set(b)
            return {k: _mix(a.get(k, D.get(k, 0.0)), b.get(k, D.get(k, 0.0)), u) for k in ks}
    return dict(keys[-1][1])


def _mix(x, y, u):
    if isinstance(x, dict) or isinstance(y, dict):
        x = x if isinstance(x, dict) else {}; y = y if isinstance(y, dict) else {}
        return {k: x.get(k, 0.0) + (y.get(k, 0.0) - x.get(k, 0.0)) * u for k in set(x) | set(y)}
    if x is None or y is None:
        return y if u >= 0.5 else x
    return x + (y - x) * u


D = {'open_': 0.0, 'lips': None}
LAG = {'Pinky': 0.0, 'Ring': 0.04, 'Middle': 0.08, 'Index': 0.12, 'Thumb': 0.10}


def cycle_open(t, period):
    """Native idle: fist (0) -> half -> spread (1) -> half -> fist; holds briefly at the ends."""
    ph = (t / period) % 1.0
    return 0.5 - 0.5 * math.cos(2 * math.pi * ph)


def standing(t):
    P = 1.2
    fingers = {f: cycle_open(t - LAG[f], P) for f in ORDER}
    o = cycle_open(t - 0.06, P)
    w = 2 * math.pi * t / 2.4
    return dict(open_=o, fingers=fingers, lift=0.015 * math.sin(w), pitch=2.5 * math.sin(w + 0.7),
                roll=2.0 * math.sin(w), yaw=3.0 * math.sin(w + 1.3))


def travel(period, lean, amp):
    def f(t):
        w = 2 * math.pi * t / period
        wave = {g: amp * math.sin(w - 1.1 * k) for k, g in enumerate(('Pinky', 'Ring', 'Middle', 'Index'))}
        wave['Thumb'] = 0.5 * amp * math.sin(w + 1.5)
        return dict(open_=0.55, wave=wave, pitch=lean + 2.0 * math.sin(w), lift=0.02 * math.sin(2 * w),
                    roll=2.5 * math.sin(w), lips=18 + 8 * math.sin(w))
    return f


ATTACK = [
    (0.00, {'open_': 0.0}),
    (0.24, {'open_': 1.0, 'lips': LIPS_OPEN, 'forward': -0.06, 'lift': 0.04, 'pitch': -12}),
    (0.36, {'open_': 1.0, 'lips': LIPS_OPEN, 'forward': 0.08, 'lift': 0.0, 'pitch': 8}),
    (IMPACT, {'open_': 0.8, 'claw': 0.5, 'lips': 0.0, 'forward': 0.09, 'pitch': 12}),
    (0.62, {'open_': 0.6, 'claw': 1.0, 'lips': 8.0, 'forward': 0.06, 'pitch': 16}),
    (1.00, {'open_': 0.0}),
]
HIT = [
    (0.00, {'open_': 0.0}),
    (0.16, {'open_': 0.6, 'lips': 30.0, 'forward': -0.07, 'lift': 0.03, 'pitch': -14, 'yaw': 12, 'roll': -8}),
    (0.33, {'open_': 0.35, 'lips': 10.0, 'forward': -0.03, 'lift': 0.012, 'pitch': -5, 'yaw': 5, 'roll': -3}),
    (0.50, {'open_': 0.0}),
]
DEATH = [
    (0.00, {'open_': 0.0}),
    (0.22, {'open_': 0.9, 'lips': LIPS_OPEN, 'lift': 0.03, 'pitch': -14, 'yaw': 10, 'roll': -8}),
    (0.32, {'open_': 0.9, 'lips': LIPS_OPEN, 'lift': 0.04, 'pitch': -10, 'yaw': -6, 'roll': 6}),
    (0.50, {'open_': 0.15, 'lips': 10.0, 'lift': 0.02, 'pitch': 0, 'yaw': 4, 'roll': 0, 'drop': 0.0}),
    (0.90, {'open_': 0.4, 'claw': 0.6, 'lips': 0.0, 'pitch': 100, 'yaw': 25, 'roll': 25, 'drop': 1.0}),
    (1.05, {'open_': 0.42, 'claw': 0.7, 'lips': 0.0, 'pitch': 98, 'yaw': 27, 'roll': 25, 'drop': 1.0, 'bounce': 1.0}),
    (1.22, {'open_': 0.45, 'claw': 0.75, 'lips': 0.0, 'pitch': 100, 'yaw': 28, 'roll': 25, 'drop': 1.0}),
    (1.50, {'open_': 0.45, 'claw': 0.75, 'lips': 0.0, 'pitch': 100, 'yaw': 28, 'roll': 25, 'drop': 1.0}),
]


def fidget(t):
    env = ss(t / 0.35) * (1 - ss((t - 1.55) / 0.45))
    wave = {}
    for k, g in enumerate(('Pinky', 'Ring', 'Middle', 'Index')):
        tap = 0.0
        for start in (0.45, 0.95):
            x = (t - start - 0.07 * k) / 0.16
            if 0 < x < 1: tap += math.sin(math.pi * x)
        wave[g] = 28 * tap * env
    o = 0.5 * env
    return dict(open_=o, wave=wave, lips=20 * env, pitch=-4 * env, yaw=6 * math.sin(math.pi * t) * env)


LIVING = {
    'Standing': (2.4, True, standing),
    'Walking': (1.6, True, travel(1.6, 14.0, 18.0)),
    'Running': (1.2, True, travel(1.2, 22.0, 24.0)),
    'Attack': (1.0, False, lambda t: keyed(ATTACK, t)),
    'Hit': (0.5, False, lambda t: keyed(HIT, t)),
    'Fidget': (2.0, False, fidget),
}


def frames(seconds, loop):
    n = int(round(seconds * FPS))
    return [(f % n) / FPS if loop else f / FPS for f in range(n + 1)]


low = {}; cont = {}
for name, (sec, loop, fn) in LIVING.items():
    m = 1e9; c = 0
    for i, t in enumerate(frames(sec, loop)):
        pose(**fn(t)); m = min(m, lowest())
        if i % 2 == 0: c = max(c, contacts())
    low[name] = m; cont[name] = c
HOVER = -min(low.values())
print('LOWEST per clip (m, before lift)', {k: round(v, 4) for k, v in low.items()}, 'HOVER lift', round(HOVER, 4))
print('CONTACTS max finger overlaps per frame', cont)


def living(fn):
    def f(t):
        p = fn(t); p['lift'] = p.get('lift', 0.0) + HOVER; pose(**p)
    return f


def death(t):
    k = keyed(DEATH, t)
    drop = k.pop('drop', 0.0); bounce = k.pop('bounce', 0.0)
    k['lift'] = k.get('lift', 0.0) + HOVER * (1 - ss(min(1.0, t / 0.5)))
    pose(**k)
    root = rig.pose.bones['Root']
    if drop > 0:
        lo = lowest()
        root.matrix = Matrix.Translation(Vector((0, 0, (0.025 * bounce - lo) * drop))) @ root.matrix
        bpy.context.view_layer.update()
    lo = lowest()
    if lo < 0:
        root.matrix = Matrix.Translation(Vector((0, 0, -lo))) @ root.matrix
        bpy.context.view_layer.update()


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = None
    poses = []; c = 0
    for i, t in enumerate(frames(seconds, loop)):
        fn(t)
        if name in ('Death', 'Dead') and i % 2 == 0: c = max(c, contacts())
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    prev = {}
    for f, frame in enumerate(poses):
        for b in rig.pose.bones:
            q, loc, sc = frame[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0: q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc; b.scale = sc
            b.keyframe_insert('rotation_quaternion', frame=f + 1)
            b.keyframe_insert('location', frame=f + 1)
            b.keyframe_insert('scale', frame=f + 1)
    rig.animation_data.action = None
    return c


for name, (sec, loop, fn) in LIVING.items():
    key_action(name, sec, loop, living(fn)); print('CLIP', name, sec, flush=True)
cont['Death'] = key_action('Death', 1.5, False, death)
dead_low = lowest()
key_action('Dead', 1.0, False, lambda t: death(1.5))
print('CLIP Death 1.5 Dead 1.0 corpse lowest', round(dead_low, 5), 'death contacts', cont['Death'])
json.dump({'fps': FPS, 'hover_lift_m': HOVER, 'impact_melee': IMPACT, 'lowest_before_lift': low,
           'contacts_max_overlap_pairs': cont,
           'clips': {k: v[0] for k, v in LIVING.items()} | {'Death': 1.5, 'Dead': 1.0}},
          open(os.path.join(HERE, 'work', 'anim_info.json'), 'w'), indent=1)
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED anim_v1.blend')
