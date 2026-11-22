"""Procedural clips for the Electrapede (quadruped playbook: segmented creatures and snakes). Every frame is built as
armature-space bone matrices and converted to local bases:
- the spine is a chain of plate bones posed by an absolute heading per segment (yaw: the S-wave; pitch: rearing;
  roll), laid out from an anchor joint so the segment lengths never change; gait loops are re-centred on the body axis
  (in place);
- every leg is a two-bone IK (Femur + Tibia) to a foot target with the knee kept up and out (the rest knee's side of
  the hip-foot line); in the gait each pair runs a stance/swing cycle a little behind the pair in front
  (metachronal wave, lag DELTA of a cycle per pair), left and right in antiphase; a stance foot stays planted on the
  floor (it slides back at exactly the body speed); legs under a raised segment are carried with it and paddle;
- head, jaw, mandibles and antennae are local rotations on top.
Floor rules every frame (evaluated mesh): the core (plates, head) is lifted when it sinks; a leg whose vertices dip
under the floor gets its foot target raised.
Native Xeen frames (front only, Darkside 007.mon / 007.att): an idle with the head bobbing, antennae and mouth
moving; the attack opens the mouth while lightning crackles around the head and antennae (the engine's melee glow at
the mouth and antenna-tip sockets stands in for it); att 3 shows the body curled (used for the death pose).

  Standing  2.0 s loop   breathing ripple, head drift, antennae sway, mandibles chew
  Walking   0.8 s loop   S-wave head to tail, metachronal leg waves, 0.45 m per cycle
  Running   0.5 s loop   larger S-wave, faster legs, 0.70 m per cycle
  Attack    1.0 s        the front rears with the mouth opening and antennae raised, lunges and bites (impact)
  Hit       0.5 s        recoils: front jerks up and back, body kinks
  Death     1.5 s        thrashes, then curls into a C on the floor, legs folding in
  Dead      1.0 s        Death's last pose
  Fidget    2.0 s        head turns left and right, antennae flick, the front pair lifts and cleans
Reads work/anim_base.blend, writes work/anim_v1.blend and work/anim_info.json. Args: -- [clip ...] (partial rerun)."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
ONLY = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
src = 'anim_v1.blend' if ONLY and os.path.exists(os.path.join(WORK, 'anim_v1.blend')) else 'anim_base.blend'
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, src))
RJ = json.load(open(os.path.join(WORK, 'rig_v1.json')))
rig = bpy.data.objects['Pede_Rig']; mesh = bpy.data.objects['Pede']
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
ORDER = [b.name for b in BONES]                       # Blender lists parents before children
N = len(RJ['leg_y'])
SPINE = [f'Seg{i}' for i in range(N)] + ['Tail']
JR = [Vector(j) for j in RJ['joints']]
LEN = [(JR[i + 1] - JR[i]).length for i in range(N + 1)]
LEGS = [(l['seg'], l['side']) for l in RJ['legs']]
SN = {1: 'L', -1: 'R'}
ANTS = list(RJ['antennae'].values())


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    if t <= a or t >= b:
        return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


def rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, Vector(axis))


def frac(x):
    return x - math.floor(x)


# ---- spine --------------------------------------------------------------------------------------------------------------
def spine(yaw, pitch, roll, anchor=8, offset=Vector(), recentre=False):
    """yaw/pitch/roll: degrees per spine bone (N + 1 values; pitch > 0 lifts the front of that segment). Returns
    armature-space matrices of Seg0..Tail."""
    dirs, rots = [], []
    for i, b in enumerate(SPINE):
        Rt = rot(Z, yaw[i]) @ rot(X, -pitch[i])
        bdir = (Rt @ (JR[i + 1] - JR[i]).to_4d()).to_3d().normalized() if False else \
            (Rt.to_3x3() @ (JR[i + 1] - JR[i])).normalized()
        Rr = Matrix.Rotation(math.radians(roll[i]), 4, bdir)
        rots.append(Rr @ Rt @ Matrix(R[b].to_3x3()).to_4x4())
        dirs.append(bdir)
    P = [None] * (N + 2)
    P[anchor] = JR[anchor] + offset
    for i in range(anchor, N + 1):
        P[i + 1] = P[i] + dirs[i] * LEN[i]
    for i in range(anchor - 1, -1, -1):
        P[i] = P[i + 1] - dirs[i] * LEN[i]
    M = {}
    for i, b in enumerate(SPINE):
        m = rots[i].copy(); m.translation = P[i]; M[b] = m
    if recentre:
        ys = np.array([p.y for p in P]); xs = np.array([p.x for p in P])
        k, c = np.polyfit(ys, xs, 1)
        fix = Matrix.Translation((-c, 0, 0)) @ rot(Z, math.degrees(math.atan(k)))
        for b in M:
            M[b] = fix @ M[b]
    return M


def follow(M, child):
    p = PARENT[child]
    return M[p] @ RI[p] @ R[child]


def about(m, pivot, axis, deg):
    return Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-pivot) @ m


# ---- legs ---------------------------------------------------------------------------------------------------------------
LEGD = {}
for l in RJ['legs']:
    j, sd = l['seg'], l['side']; s = SN[sd]
    H, K, F = Vector(l['hip']), Vector(l['knee']), Vector(l['foot'])
    fem, tib = f'Femur{j}_{s}', f'Tibia{j}_{s}'
    raw = (K - H).cross(F - K)
    zrest = Vector(R[fem].col[2][:3])
    sign = 1.0 if raw.dot(zrest) >= 0 else -1.0
    d = (F - H).normalized(); kp = K - (H + d * (K - H).dot(d))
    LEGD[(j, sd)] = dict(fem=fem, tib=tib, H=H, K=K, F=F, l1=(K - H).length, l2=(F - K).length, sign=sign,
                         pole=kp.normalized(), seg=f'Seg{j}')


def leg_matrices(key, M, target):
    d = LEGD[key]
    ms = M[d['seg']] @ RI[d['seg']]
    H = ms @ d['H']
    pole = (ms.to_3x3() @ d['pole']).normalized()
    l1, l2 = d['l1'], d['l2']
    v = target - H
    dist = min(max(v.length, abs(l1 - l2) * 1.05 + 1e-4), (l1 + l2) * 0.998)
    u = v.normalized()
    ca = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    a = math.acos(max(-1.0, min(1.0, ca)))
    perp = (pole - u * pole.dot(u))
    if perp.length < 1e-6:
        perp = Z - u * Z.dot(u)
    perp.normalize()
    K = H + (u * math.cos(a) + perp * math.sin(a)) * l1
    T = H + u * dist
    yf = (K - H).normalized(); yt = (T - K).normalized()
    n = (K - H).cross(T - K) * d['sign']
    if n.length < 1e-8:
        n = Vector(R[d['fem']].col[2][:3])
    n.normalize()

    def mat(y, n, p):
        x = y.cross(n).normalized(); z = x.cross(y).normalized()
        m = Matrix((x, y, z)).transposed().to_4x4(); m.translation = p; return m
    return mat(yf, n, H), mat(yt, n, K)


def carried_foot(key, M):
    d = LEGD[key]
    return M[d['seg']] @ RI[d['seg']] @ d['F']


def rest_foot(key):
    return LEGD[key]['F'].copy()


# ---- mesh masks for the floor rules ----------------------------------------------------------------------------------
_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
LEGMASK = {k: np.isin(_dom, (d['fem'], d['tib'])) for k, d in LEGD.items()}
ANYLEG = np.zeros(len(_dom), bool)
for m in LEGMASK.values():
    ANYLEG |= m
ANTM = np.array([n.startswith('Ant') for n in _dom])
CORE = ~ANYLEG & ~ANTM


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    W = rig.matrix_world
    return co @ np.array(W.to_3x3()).T + np.array(W.translation)


# ---- one pose ------------------------------------------------------------------------------------------------------------
def build(spec, lift=0.0, leg_adj=None):
    """spec: dict with spine (yaw, pitch, roll lists, anchor, offset, recentre), head (pitch, yaw, roll), jaw, mand,
    ant (list of (pitch, yaw) per antenna bone chain), feet (dict key -> world target), lift (root z)."""
    leg_adj = leg_adj or {}
    sp = spec['spine']
    off = sp.get('offset', Vector()) + Vector((0, 0, lift))
    M = spine(sp['yaw'], sp['pitch'], sp['roll'], sp.get('anchor', 8), off, sp.get('recentre', False))
    M['Root'] = Matrix.Translation(Vector((0, 0, 0))) @ R['Root']
    h = spec.get('head', (0, 0, 0))
    M['Head'] = follow(M, 'Head') @ rot((1, 0, 0), h[0]) @ rot((0, 0, 1), h[1]) @ rot((0, 1, 0), h[2])
    if 'Jaw' in R:
        M['Jaw'] = follow(M, 'Jaw') @ rot((1, 0, 0), -spec.get('jaw', 0.0))
    for name in RJ['mandibles']:
        sgn = -1 if name.endswith('_L') else 1
        M[name] = follow(M, name) @ rot((0, 0, 1), sgn * spec.get('mand', 0.0))
    ant = spec.get('ant', {})
    for a in ANTS:
        p, yw = ant.get(a['bones'][0], (0.0, 0.0))
        for k, b in enumerate(a['bones']):
            f = 1.0 if k == 0 else 0.8
            M[b] = follow(M, b) @ rot((1, 0, 0), p * f) @ rot((0, 0, 1), yw * f)
    feet = spec['feet'](M) if callable(spec['feet']) else spec['feet']
    for key in LEGD:
        t = feet[key].copy()
        t.z = max(t.z, 0.0) + leg_adj.get(key, 0.0)
        M[LEGD[key]['fem']], M[LEGD[key]['tib']] = leg_matrices(key, M, t)
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


def solve(spec_fn, t):
    lift = 0.0; adj = {}
    for _ in range(5):
        spec = spec_fn(t)
        apply(build(spec, lift, adj))
        co = mesh_co(); moved = False
        low = co[CORE, 2].min()
        floor = spec.get('floor', 'lift')
        if floor == 'ground' or low < -0.004:
            dl = -low + (0.002 if floor == 'ground' else 0.0)
            if abs(dl) > 1e-4:
                lift += dl; moved = True
        for key, m in LEGMASK.items():
            lw = co[m, 2].min()
            if lw < -0.005:
                adj[key] = adj.get(key, 0.0) - lw + 0.002; moved = True
        if not moved:
            break
    co = mesh_co()
    return co, lift, adj


# ---- clip parameters -------------------------------------------------------------------------------------------------------
NB = N + 1
DELTA = 0.11            # leg-pair lag (fraction of a cycle) behind the pair in front


def wave(t, T, amp, waves=1.0, env=None):
    out = []
    for i in range(NB):
        e = env(i) if env else (0.35 + 0.65 * math.sin(math.pi * min(i, N) / N))
        out.append(amp * e * math.sin(2 * math.pi * (t / T - waves * i / NB)))
    return out


def gait_spec(T, stride, duty, lift, amp, waves=1.0):
    L = stride * duty

    def spine_at(t):
        return spine(wave(t, T, amp, waves), [0.0] * NB, [0.0] * NB, 8, Vector(), True)

    def hip_x(key, t):
        M = spine_at(t); d = LEGD[key]
        return (M[d['seg']] @ RI[d['seg']] @ d['H']).x

    def foot(key, t):
        j, sd = key
        p = frac(t / T - j * DELTA + (0.5 if sd < 0 else 0.0))
        F0 = rest_foot(key); off = F0.x - LEGD[key]['H'].x
        if p < duty:
            u = p / duty
            tm = t - (p - duty / 2) * T
            x = hip_x(key, tm) + off
            return Vector((x, F0.y - L / 2 + L * u, 0.0))
        u = (p - duty) / (1 - duty)
        t0 = t - (p - duty / 2) * T                # mid of the stance just ended
        t1 = t0 + T                                # mid of the next stance
        x = hip_x(key, t0) + (hip_x(key, t1) - hip_x(key, t0)) * ss(u) + off
        return Vector((x, F0.y + L / 2 - L * ss(u), lift * math.sin(math.pi * u)))

    def fn(t):
        return dict(spine=dict(yaw=wave(t, T, amp, waves), pitch=[0.0] * NB, roll=[0.0] * NB, recentre=True),
                    head=(2.0 * math.sin(2 * math.pi * t / T * 2), -0.5 * wave(t, T, amp, waves)[0], 0.0),
                    jaw=0.0, mand=4.0 * math.sin(2 * math.pi * 2 * t / T),
                    ant={a['bones'][0]: (6 * math.sin(2 * math.pi * t / T + k), 8 * math.sin(2 * math.pi * t / T + 1.3 * k))
                         for k, a in enumerate(ANTS)},
                    feet={key: foot(key, t) for key in LEGD})
    return fn


def planted(M_unused=None):
    return {key: rest_foot(key) for key in LEGD}


def front_profile(amount, n_front=5):
    """pitch per segment for a rear-up: the first n_front segments pitched up, fading toward the back."""
    return [amount * max(0.0, 1.0 - i / n_front) ** 1.3 for i in range(NB)]


def legs_follow(raise_from, paddle=0.0, t=0.0):
    """feet: planted on the floor, but carried with their segment (plus a paddle) where the hip is lifted."""
    def f(M):
        out = {}
        for key, d in LEGD.items():
            hip = (M[d['seg']] @ RI[d['seg']] @ d['H'])
            rise = hip.z - d['H'].z
            c = ss((rise - 0.02) / 0.08)
            g = rest_foot(key)
            cf = carried_foot(key, M)
            j, sd = key
            pad = Vector((0, paddle * math.sin(2 * math.pi * (3.0 * t) + j * 1.1 + (math.pi if sd < 0 else 0)), 0))
            cf = cf + (M[d['seg']].to_3x3() @ pad) + Vector((0, 0, 0.04 * c))
            out[key] = g.lerp(cf, c)
        return out
    return f


def standing(t):
    T = 2.0; w = 2 * math.pi * t / T
    yaw = [1.5 * math.sin(w - 2 * math.pi * i / NB) * (0.4 + 0.6 * i / NB) for i in range(NB)]
    return dict(spine=dict(yaw=yaw, pitch=[0.8 * math.sin(w) * max(0, 1 - i / 4) for i in range(NB)], roll=[0.0] * NB,
                           recentre=True),
                head=(3.0 * math.sin(w + 0.5), 5.0 * math.sin(w), 2.0 * math.sin(w + 1.0)),
                jaw=4.0 * bump(t, 0.4, 0.8) + 3.0 * bump(t, 1.3, 1.6), mand=8.0 * math.sin(2 * w),
                ant={a['bones'][0]: (7 * math.sin(w + k * 0.9), 9 * math.sin(w + 0.6 + k * 1.4)) for k, a in enumerate(ANTS)},
                feet=legs_follow(0))


def keyed(keys, t):
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            u = ss((t - t0) / (t1 - t0))
            out = {}
            for k in set(a) | set(b):
                va, vb = a.get(k, 0.0), b.get(k, 0.0)
                out[k] = va + (vb - va) * u
            return out
    return keys[-1][1]


# attack: rear (pitch of the front), back (body offset +y), head pitch, jaw open, mandibles, antennae raise
ATTACK = [(0.00, dict()),
          (0.18, dict(rear=14, back=0.04, head=-4, jaw=10, mand=-10, ant=-15, kink=3)),
          (0.34, dict(rear=40, back=0.09, head=-18, jaw=32, mand=-22, ant=-28, kink=-4)),
          (0.45, dict(rear=8, back=-0.10, head=8, jaw=6, mand=14, ant=-10, kink=2)),
          (0.52, dict(rear=4, back=-0.11, head=10, jaw=0, mand=16, ant=-6)),
          (0.70, dict(rear=8, back=-0.05, head=2, jaw=6, mand=0, ant=-4)),
          (1.00, dict())]


def attack(t):
    k = keyed(ATTACK, t)
    tw = 1.5 * math.sin(2 * math.pi * 9 * t) * bump(t, 0.05, 0.45)      # electric twitch while charging
    yaw = [k.get('kink', 0) * math.sin(math.pi * i / 4) * max(0, 1 - i / 8) for i in range(NB)]
    return dict(spine=dict(yaw=yaw, pitch=front_profile(k.get('rear', 0), 6), roll=[0.0] * NB,
                           offset=Vector((0, k.get('back', 0), 0)), anchor=10),
                head=(k.get('head', 0) + tw, tw * 0.6, 0.0), jaw=k.get('jaw', 0), mand=k.get('mand', 0),
                ant={a['bones'][0]: (k.get('ant', 0) + 6 * math.sin(2 * math.pi * 7 * t + i),
                                     4 * math.sin(2 * math.pi * 5 * t + 2 * i)) for i, a in enumerate(ANTS)},
                feet=legs_follow(0, paddle=0.05, t=t))


HIT = [(0.00, dict()), (0.08, dict(rear=12, back=0.08, head=16, kink=8, ant=20, jaw=8)),
       (0.22, dict(rear=6, back=0.05, head=6, kink=-4, ant=8, jaw=3)), (0.50, dict())]


def hit(t):
    k = keyed(HIT, t)
    yaw = [k.get('kink', 0) * math.sin(math.pi * i / 6) for i in range(NB)]
    return dict(spine=dict(yaw=yaw, pitch=front_profile(k.get('rear', 0), 5), roll=[0.0] * NB,
                           offset=Vector((0, k.get('back', 0), 0)), anchor=10),
                head=(k.get('head', 0), 0.0, 4 * bump(t, 0.03, 0.3)), jaw=k.get('jaw', 0), mand=-6 * bump(t, 0.0, 0.3),
                ant={a['bones'][0]: (k.get('ant', 0), 10 * bump(t, 0.02, 0.3) * (1 if i % 2 else -1))
                     for i, a in enumerate(ANTS)},
                feet=legs_follow(0, paddle=0.03, t=t))


CURL = 235.0            # total heading change of the C (degrees) in the corpse


def death(t):
    thr = bump(t, 0.0, 0.75)
    w = 2 * math.pi * t / 0.45
    yaw_thr = [26 * thr * (0.4 + 0.6 * math.sin(math.pi * i / N)) * math.sin(w - 2 * math.pi * 1.2 * i / NB)
               for i in range(NB)]
    c = ss((t - 0.55) / 0.85)
    # C curl: heading turns steadily along the body (head end turning right, toward -X)
    yaw_curl = [-CURL * c * (i / NB - 0.5) for i in range(NB)]
    yaw = [a + b for a, b in zip(yaw_thr, yaw_curl)]
    rear = 22 * bump(t, 0.05, 0.6)
    pitch = front_profile(rear, 6)
    fold = ss((t - 0.6) / 0.7)
    head = (14 * bump(t, 0.05, 0.6) - 18 * fold, -10 * fold, 0.0)

    def feet(M):
        out = {}
        for key, d in LEGD.items():
            j, sd = key
            cf = carried_foot(key, M)
            hip = M[d['seg']] @ RI[d['seg']] @ d['H']
            # flail during the thrash, then fold the foot in under the hip
            flail = M[d['seg']].to_3x3() @ Vector((0, 0.07 * math.sin(2 * math.pi * 4 * t + j * 1.3 + (sd < 0) * math.pi),
                                                   0.03 * thr))
            # dead insects pull their legs in: the foot comes up beside the hip, the knee folds high
            tuck = hip + M[d['seg']].to_3x3() @ Vector((sd * 0.09, 0.03, 0.03))
            tgt = (cf + flail).lerp(tuck, fold)
            out[key] = tgt
        return out
    return dict(spine=dict(yaw=yaw, pitch=pitch, roll=[0.0] * NB, anchor=8, recentre=False),
                head=head, jaw=20 * bump(t, 0.05, 0.7) + 10 * fold, mand=-14 * fold,
                ant={a['bones'][0]: (-20 * fold + 15 * thr * math.sin(2 * math.pi * 6 * t + i), 0.0) for i, a in enumerate(ANTS)},
                feet=feet, floor='ground' if t > 1.1 else 'lift')


FID = [(0.00, dict()), (0.35, dict(hyaw=22, hp=6)), (0.75, dict(hyaw=22, hp=10, lift0=1)), (1.05, dict(hyaw=-6, hp=4, lift0=1)),
       (1.40, dict(hyaw=-24, hp=4)), (1.75, dict(hyaw=-10)), (2.00, dict())]


def fidget(t):
    k = keyed(FID, t)
    w = 2 * math.pi * t / 2.0
    yaw = [0.4 * k.get('hyaw', 0) * max(0, 1 - i / 4) + 1.2 * math.sin(w - 2 * math.pi * i / NB) for i in range(NB)]
    lf = k.get('lift0', 0)

    def feet(M):
        out = legs_follow(0)(M)
        for sd in (1, -1):
            key = (0, sd)
            # the front pair lifts and rubs at the mandibles (cleaning)
            d = LEGD[key]
            mouth = M['Head'] @ RI['Head'] @ Vector((sd * 0.07, -1.10, 0.14))
            rub = Vector((0, 0.02 * math.sin(2 * math.pi * 4 * t + (sd < 0) * math.pi), 0.015 * math.sin(2 * math.pi * 4 * t)))
            out[key] = out[key].lerp(mouth + rub, 0.75 * lf)
        return out
    return dict(spine=dict(yaw=yaw, pitch=front_profile(6 * lf + 2 * bump(t, 0.2, 0.6), 4), roll=[0.0] * NB, recentre=True),
                head=(k.get('hp', 0), k.get('hyaw', 0), 0.0), jaw=6 * lf * abs(math.sin(2 * math.pi * 3 * t)),
                mand=10 * lf * math.sin(2 * math.pi * 4 * t),
                ant={a['bones'][0]: (10 * math.sin(2 * math.pi * 1.5 * t + i) + 12 * bump(t, 1.2, 1.6),
                                     14 * math.sin(2 * math.pi * 1.0 * t + 1.7 * i)) for i, a in enumerate(ANTS)},
                feet=feet)


# ---- keying --------------------------------------------------------------------------------------------------------------
INFO = {}


def key_action(name, n, fn, loop=False, impact_track=False):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows, core_lows, lifts, mouth = [], [], [], [], []
    adj_max = 0.0
    for f in range(n + 1):
        t = ((f % n) / FPS) if loop else f / FPS
        co, lift, adj = solve(fn, t)
        lows.append(float(co[:, 2].min())); core_lows.append(float(co[CORE, 2].min())); lifts.append(lift)
        adj_max = max([adj_max] + list(adj.values()))
        hm = rig.matrix_world @ pbn['Head'].matrix @ Vector((0, pbn['Head'].length, 0))
        mouth.append(tuple(hm))
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
                  'lowest_cm': [round(min(lows) * 100, 2), round(max(lows) * 100, 2)],
                  'core_lowest_cm': round(min(core_lows) * 100, 2), 'max_lift_cm': round(max(lifts) * 100, 2),
                  'max_leg_raise_cm': round(adj_max * 100, 2)}
    if impact_track:
        my = np.array([m[1] for m in mouth]); mz = np.array([m[2] for m in mouth])
        INFO[name]['head_tip_y'] = [round(v, 3) for v in my]
        INFO[name]['head_tip_z'] = [round(v, 3) for v in mz]
        f_imp = int(np.argmin(my)); INFO[name]['impact_frame'] = f_imp; INFO[name]['impact_s'] = round(f_imp / FPS, 3)
    print('CLIP', name, {k: v for k, v in INFO[name].items() if not k.startswith('head_tip')}, flush=True)


def main():
    clips = {
        'Standing': (60, standing, True, False),
        'Walking': (24, gait_spec(0.8, 0.45, 0.65, 0.05, 10.0), True, False),
        'Running': (15, gait_spec(0.5, 0.70, 0.5, 0.07, 15.0), True, False),
        'Attack': (30, attack, False, True),
        'Hit': (15, hit, False, False),
        'Fidget': (60, fidget, False, False),
        'Death': (45, death, False, False),
        'Dead': (30, lambda t: death(1.5), False, False),
    }
    for name, (n, fn, loop, imp) in clips.items():
        if ONLY and name not in ONLY:
            continue
        key_action(name, n, fn, loop=loop, impact_track=imp)
    for k, v in (('Walking', 0.45), ('Running', 0.70)):
        if k in INFO:
            INFO[k]['stride'] = v
    info_path = os.path.join(WORK, 'anim_info.json')
    old = json.load(open(info_path))['clips'] if (ONLY and os.path.exists(info_path)) else {}
    old.update(INFO)
    json.dump({'clips': old}, open(info_path, 'w'), indent=1)
    for b in pbn:
        b.matrix_basis = Matrix.Identity(4)
    rig.animation_data.action = bpy.data.actions['Standing'] if 'Standing' in bpy.data.actions else None
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'anim_v1.blend'))
    print('SAVED anim_v1.blend')


main()
