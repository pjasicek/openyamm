"""Procedural clips for the sand worm (quadruped playbook: snakes and segmented creatures). Every frame is a set of
armature-space bone matrices converted to local bases:
- the body chain Ring0..Ring4 > Head is laid out from the floor joint: each ring keeps its rest length times its own
  uniform scale s (a ring shrinks into the mound when the worm sinks: joints carry uniform scale only) and turns by its
  own pitch (positive = the top moves forward, toward -Y), side bend (positive = toward +X, the worm's left) and twist,
  accumulated up the chain;
- the six mound lobes are lifted (translation only; the mound rim is weighted to Root and stays on the floor), each
  with its own phase, so the mound breathes, grows into a travelling hump and ripples;
- the six lips move out along their radial direction and tilt outward to open the maw (negative closes it); the fangs
  flare with them.
Floor rule every frame (evaluated mesh): the body (rings, spikes, head, fangs) never below the floor: the chain is
lifted when it sinks; Death's corpse is solved down onto the floor (its droop grows until the lying rings touch).
Native Xeen frames (front only, Clouds 056): mon 0-7 the worm rising out of the sand mound (rock shards flying) and
sinking back; att 0-3 the worm bent forward over its coils with the round maw facing the party.

  Standing  2.4 s loop   upright, slow sway travelling up the rings, maw slowly opening and closing, mound breathing
  Walking   1.0 s loop   sunk into a travelling mound (lower rings shrunk inside it), upper rings and maw above, the
                         hump rippling front to back, body undulating
  Running   0.6 s loop   sunk deeper, leaning forward, faster ripple
  Attack    1.2 s        rears back with the maw opening, lunges forward-down bent over toward the party, maw wide
                         open facing forward (impact), snaps shut, recovers
  Hit       0.5 s        recoils back and aside, maw clenched
  Death     1.6 s        writhes with the maw gaping, sinks partly into the mound and topples aside onto the floor
  Dead      1.0 s        Death's last pose: slumped half out of the mound on the floor
  Fidget    2.0 s        sinks partly into the mound and rises again, maw flexing wide
Reads work/anim_base.blend, writes work/anim_v1.blend and work/anim_info.json. Args: -- [clip ...] (partial rerun)."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
BLENDS = [a for a in ARGS if a.endswith('.blend')]          # optional: <source.blend> [<output.blend>] (previews)
ONLY = [a for a in ARGS if not a.endswith('.blend')]
SRC = BLENDS[0] if BLENDS else None
OUT = BLENDS[1] if len(BLENDS) > 1 else 'anim_v1.blend'
src = SRC or ('anim_v1.blend' if ONLY and os.path.exists(os.path.join(WORK, 'anim_v1.blend')) else 'anim_base.blend')
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, src))
RJ = json.load(open(os.path.join(WORK, 'rig_v1.json')))
rig = bpy.data.objects['Worm_Rig']; mesh = bpy.data.objects['Worm']
FPS = 30
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
if rig.animation_data:
    rig.animation_data.action = None
pbn = rig.pose.bones
for b in pbn:
    b.rotation_mode = 'QUATERNION'; b.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
BONES = rig.data.bones
R = {b.name: b.matrix_local.copy() for b in BONES}
RI = {k: v.inverted() for k, v in R.items()}
PARENT = {b.name: (b.parent.name if b.parent else None) for b in BONES}
ORDER = [b.name for b in BONES]
RINGS = RJ['rings']
JZ = RJ['joints']
LEN = [JZ[i + 1] - JZ[i] for i in range(6)]
LIPS = RJ['lips']; LOBES = RJ['lobes']
MAW_C = Vector(RJ['maw']['centre']); MAW_N = Vector(RJ['maw']['normal'])


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    if t <= a or t >= b:
        return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


def rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, Vector(axis))


def follow(M, child):
    p = PARENT[child]
    return M[p] @ RI[p] @ R[child]


# ---- one pose ----------------------------------------------------------------------------------------------------------
def build(spec, lift=0.0):
    """spec: pitch/side/twist (6 values each, degrees), scale (6), base (x, y offset), lips (6 openings or one),
    lobes (6 lifts in m or one), lobe_xy (shift of the mound in m)."""
    M = {'Root': R['Root'].copy()}
    pitch = spec.get('pitch', [0.0] * 6); side = spec.get('side', [0.0] * 6); twist = spec.get('twist', [0.0] * 6)
    scale = spec.get('scale', [1.0] * 6)
    bx, by = spec.get('base', (0.0, 0.0))
    P = Vector((bx, by, JZ[0] + lift))
    Rc = Matrix.Identity(4)
    for i, name in enumerate(RINGS):
        Rc = Rc @ rot(X, pitch[i]) @ rot(Y, side[i]) @ rot(Z, twist[i])
        m = Matrix.Translation(P) @ Rc @ Matrix.Scale(scale[i], 4) @ Matrix(R[name].to_3x3()).to_4x4()
        M[name] = m
        P = P + (Rc.to_3x3() @ Vector((0, 0, LEN[i] * scale[i])))
    lips = spec.get('lips', 0.0)
    lips = lips if isinstance(lips, (list, tuple)) else [lips] * 6
    for k, L in enumerate(LIPS):
        name = L['name']; o = lips[k]
        base = follow(M, name)
        # in the lip's own frame: y along the maw normal, z along its radial direction (roll), x tangent
        out = Matrix.Translation(Vector((0, 0.008 * o, 0.030 * o))) @ rot(X, 28 * o)
        M[name] = base @ out
    lobes = spec.get('lobes', 0.0)
    lobes = lobes if isinstance(lobes, (list, tuple)) else [lobes] * 6
    lx, ly = spec.get('lobe_xy', (0.0, 0.0))
    for k, L in enumerate(LOBES):
        M[L['name']] = Matrix.Translation(Vector((lx, ly, lobes[k]))) @ R[L['name']]
    return M


def apply(M):
    for name in ORDER:
        m = M.get(name)
        if m is None:
            m = follow(M, name); M[name] = m
        p = PARENT[name]
        basis = RI[name] @ m if p is None else (RI[name] @ R[p]) @ (M[p].inverted() @ m)
        pbn[name].matrix_basis = basis
    bpy.context.view_layer.update()


_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
MOUNDV = np.array([n == 'Root' or n.startswith('Lobe') for n in _dom])
BODY = ~MOUNDV
_part = np.zeros(len(_dom), int)
for p in mesh.data.polygons:
    for v in p.vertices:
        _part[v] = mesh.data.attributes['part'].data[p.index].value
UPPER = BODY & np.isin(_dom, ('Ring3', 'Ring4', 'Head') + tuple(L['name'] for L in LIPS))


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    Wm = rig.matrix_world
    return co @ np.array(Wm.to_3x3()).T + np.array(Wm.translation)


def solve(spec_fn, t):
    spec = spec_fn(t)
    lift = 0.0
    for _ in range(4):
        apply(build(spec, lift))
        co = mesh_co()
        low = co[BODY, 2].min()
        if low < -0.003:
            lift += -low; continue
        break
    co = mesh_co()
    if spec.get('settle'):
        # corpse: increase the droop (extra pitch on the given rings) until the lying rings touch the floor
        lo, hi = -40.0, 60.0
        for _ in range(16):
            mid = (lo + hi) / 2
            s2 = dict(spec); s2['pitch'] = [p + mid * w for p, w in zip(spec['pitch'], spec['settle'])]
            apply(build(s2, lift)); co = mesh_co()
            if co[BODY, 2].min() < 0.004:
                hi = mid
            else:
                lo = mid
        s2 = dict(spec); s2['pitch'] = [p + lo * w for p, w in zip(spec['pitch'], spec['settle'])]
        apply(build(s2, lift)); co = mesh_co()
        if co[BODY, 2].min() < -0.003:
            lift2 = lift - co[BODY, 2].min()
            apply(build(s2, lift2)); co = mesh_co(); lift = lift2
    return co, lift


# ---- clips ---------------------------------------------------------------------------------------------------------------
def wave6(t, T, amp, lag=0.12, ph=0.0, grow=True):
    return [amp * ((0.3 + 0.7 * i / 5) if grow else 1.0) * math.sin(2 * math.pi * (t / T - lag * i) + ph) for i in range(6)]


def standing(t):
    T = 2.4; w = 2 * math.pi * t / T
    pitch = wave6(t, T, 2.2)
    side = wave6(t, T, 2.6, ph=1.3)
    opening = 0.25 + 0.35 * (0.5 - 0.5 * math.cos(w))            # maw slowly opening and closing
    lobes = [0.004 * (1 + math.sin(w + L['theta'])) for L in LOBES]
    return dict(pitch=pitch, side=side, twist=[0.6 * math.sin(w)] * 6, lips=opening, lobes=lobes)


SINK_WALK = [0.32, 0.42, 0.58, 0.92, 1.0, 1.0]
SINK_RUN = [0.28, 0.34, 0.45, 0.62, 0.95, 1.0]


def travel(T, sink, hump, lean, amp, ripple):
    def fn(t):
        w = 2 * math.pi * t / T
        pitch = [a + b for a, b in zip([0, 0, 0, lean * 0.4, lean * 0.4, lean * 0.2], wave6(t, T, amp, lag=0.18))]
        side = wave6(t, T, amp * 0.8, lag=0.18, ph=math.pi / 2)
        # the hump: front lobes higher (it ploughs forward), a ripple running front to back around the mound
        lobes = []
        for L in LOBES:
            th = L['theta']; front = -math.sin(th)                # +1 at the front (-Y), -1 at the back
            lobes.append(hump * (1 + 0.18 * front) + ripple * math.sin(w - 1.4 * (1 - front)))
        return dict(pitch=pitch, side=side, scale=sink, lips=0.15 + 0.15 * math.sin(2 * w), lobes=lobes,
                    twist=[1.5 * math.sin(w)] * 6)
    return fn


ATTACK = [(0.00, dict(lips=0.25)),
          (0.30, dict(back=-7, top=-10, lips=0.6, hump=0.01)),
          (0.40, dict(back=-8, top=-12, lips=0.85, hump=0.012)),
          (0.56, dict(back=13, top=14, lips=1.05, hump=0.03)),
          (0.66, dict(back=12, top=12, lips=-0.35, hump=0.025)),
          (0.80, dict(back=7, top=8, lips=0.2, hump=0.015)),
          (1.20, dict(lips=0.25))]


def keyed(keys, t):
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            u = ss((t - t0) / (t1 - t0))
            return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * u for k in set(a) | set(b)}
    return keys[-1][1]


def attack(t):
    k = keyed(ATTACK, t)
    b, tp = k.get('back', 0), k.get('top', 0)
    # 'back' bends the middle rings, 'top' the upper rings and head: positive = forward toward the party
    pitch = [0, b * 0.35, b * 0.6, b * 0.8 + tp * 0.3, tp * 0.75, tp * 0.85]
    shake = 1.2 * math.sin(2 * math.pi * 7 * t) * bump(t, 0.05, 0.4)
    side = [0, 0, shake * 0.4, shake * 0.7, shake, shake * 0.6]
    return dict(pitch=pitch, side=side, lips=k.get('lips', 0.25),
                lobes=[k.get('hump', 0) * (1 - 0.5 * math.sin(L['theta'])) for L in LOBES])


HIT = [(0.00, dict(lips=0.25)), (0.12, dict(p=-12, s=7, lips=-0.6)), (0.26, dict(p=-5, s=-3, lips=-0.3)),
       (0.50, dict(lips=0.25))]


def hit(t):
    k = keyed(HIT, t)
    p, s = k.get('p', 0), k.get('s', 0)
    return dict(pitch=[0, p * 0.2, p * 0.4, p * 0.6, p * 0.8, p], side=[0, s * 0.2, s * 0.4, s * 0.6, s * 0.8, s],
                lips=k.get('lips', 0.25), lobes=[0.01 * bump(t, 0.02, 0.3)] * 6)


DEATH_SINK = [0.45, 0.55, 1.0, 1.0, 1.0, 1.0]
TOPPLE = [0.0, 28.0, 34.0, 16.0, 12.0, 6.0]          # total forward-side bend of the corpse (degrees per ring)
TOPPLE_SIDE = 40.0                                    # the fall leans toward +X (the worm's left) by this azimuth


def death(t):
    thr = bump(t, 0.0, 0.8)
    w = 2 * math.pi * t / 0.4
    side = [thr * 10 * (i / 5) * math.sin(w - 0.6 * i) for i in range(6)]
    pitch = [thr * (-8 * i / 5) for i in range(6)]
    c = ss((t - 0.55) / 0.85)
    sink = [1 + (s - 1) * ss((t - 0.4) / 0.7) for s in DEATH_SINK]
    a = math.radians(TOPPLE_SIDE)
    pitch = [p + c * tb * math.cos(a) for p, tb in zip(pitch, TOPPLE)]
    side = [s + c * tb * math.sin(a) for s, tb in zip(side, TOPPLE)]
    spec = dict(pitch=pitch, side=side, scale=sink, lips=0.9 * bump(t, 0.05, 0.9) + 0.35 * c,
                lobes=[0.02 * bump(t, 0.3, 1.2)] * 6, twist=[4 * c] * 6)
    if t > 1.2:
        u = ss((t - 1.2) / 0.3)
        spec['settle'] = [0, 0.3 * u, 0.4 * u, 0.2 * u, 0.15 * u, 0.1 * u]
    return spec


FID = [(0.00, dict()), (0.45, dict(sink=1)), (0.95, dict(sink=1, lips=1)), (1.15, dict(sink=0.6, lips=-0.4)),
       (1.40, dict(sink=0.2, lips=1.0)), (1.60, dict(lips=-0.2)), (2.00, dict())]


def fidget(t):
    k = keyed(FID, t)
    s = k.get('sink', 0)
    scale = [1 + (x - 1) * s for x in (0.35, 0.45, 0.62, 1, 1, 1)]
    w = 2 * math.pi * t / 2.0
    return dict(pitch=wave6(t, 2.0, 2.0), side=wave6(t, 2.0, 3.0, ph=1.0), scale=scale,
                lips=0.25 + k.get('lips', 0) * 0.75, lobes=[0.09 * s + 0.01 * math.sin(3 * w + L['theta']) * s
                                                             for L in LOBES])


# ---- keying ----------------------------------------------------------------------------------------------------------------
INFO = {}


def key_action(name, n, fn, loop=False, impact_track=False):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows, mlows, lifts, maw = [], [], [], [], []
    for f in range(n + 1):
        t = ((f % n) / FPS) if loop else f / FPS
        co, lift = solve(fn, t)
        lows.append(float(co[BODY, 2].min())); mlows.append(float(co[MOUNDV, 2].min())); lifts.append(lift)
        hm = rig.matrix_world @ (pbn['Head'].matrix @ RI['Head'] @ MAW_C)
        maw.append(tuple(hm))
        poses.append({b.name: b.matrix_basis.copy() for b in pbn})
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
                  'body_lowest_cm': [round(min(lows) * 100, 2), round(max(lows) * 100, 2)],
                  'mound_lowest_cm': round(min(mlows) * 100, 2), 'max_lift_cm': round(max(lifts) * 100, 2),
                  'maw_top_z': round(max(m[2] for m in maw), 3)}
    if impact_track:
        my = np.array([m[1] for m in maw])
        INFO[name]['maw_y'] = [round(v, 3) for v in my]
        INFO[name]['maw_z'] = [round(m[2], 3) for m in maw]
        f_imp = int(np.argmin(my)); INFO[name]['impact_frame'] = f_imp; INFO[name]['impact_s'] = round(f_imp / FPS, 3)
    print('CLIP', name, {k: v for k, v in INFO[name].items() if not k.startswith('maw_y') and k != 'maw_z'}, flush=True)


def main():
    clips = {
        'Standing': (72, standing, True, False),
        'Walking': (30, travel(1.0, SINK_WALK, 0.11, 6.0, 4.0, 0.022), True, False),
        'Running': (18, travel(0.6, SINK_RUN, 0.15, 12.0, 5.0, 0.03), True, False),
        'Attack': (36, attack, False, True),
        'Hit': (15, hit, False, False),
        'Fidget': (60, fidget, False, False),
        'Death': (48, death, False, False),
        'Dead': (30, lambda t: death(1.6), False, False),
    }
    for name, (n, fn, loop, imp) in clips.items():
        if ONLY and name not in ONLY:
            continue
        key_action(name, n, fn, loop=loop, impact_track=imp)
    info_path = os.path.join(WORK, 'anim_info.json')
    old = json.load(open(info_path))['clips'] if (ONLY and os.path.exists(info_path)) else {}
    old.update(INFO)
    json.dump({'clips': old}, open(info_path, 'w'), indent=1)
    for b in pbn:
        b.matrix_basis = Matrix.Identity(4)
    rig.animation_data.action = bpy.data.actions['Standing'] if 'Standing' in bpy.data.actions else None
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, OUT))
    print('SAVED', OUT)


main()
