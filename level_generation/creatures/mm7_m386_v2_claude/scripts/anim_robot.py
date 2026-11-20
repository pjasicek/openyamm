"""Procedural robot clips (24 fps), native MM7 m386 timing (ticks of 1/16 s):
  Standing 36 f loop (native sa held): idle hum: body bob, slow head scan, tail sway;
  Walking  30 f loop (native wa-wj, 20 ticks): diagonal pairs FL+RR / FR+RL, duty 0.55; each spike tip stays on its
           foothold in stance (leg sleeve aimed at the foothold, spike slid through the sleeve to reach it) and lifts
           in swing; body bob, tail and neck counter-sway. Body travel per cycle STRIDE (binding stride_length);
  Attack   21 f (14 ticks, native aa-ag): the gun under the chassis is stowed muzzle-down in every other clip; it
           swings up level onto the target while the chassis braces and the head stays on target, charges (coil glow
           from the binding's glow event on Socket_Muzzle), fires at IMPACT with a hard recoil (gun slides back along
           its barrel and kicks, chassis jolts back, tail whips), then re-stows;
  Hit      21 f (14 ticks): jolt sideways and back, legs skid, head whips, jaw snaps open;
  Death    18 f (12 ticks, native na-nb, da-dd): shudder, the legs splay out and the chassis drops onto the floor, neck
           and tail fall and rest on the floor (native corpse xa); Dead = held;
  Fidget   18 f (12 ticks, native fa-ff): looks around (head turns left and right).
Floor rule every frame: spike tips at or above z 0; in Death/Dead every part above the floor (land()).
Args: [in.blend out.blend] (default work/rig_v1.blend -> work/anim_v1.blend)."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SRC = a[0] if a else 'work/rig_v1.blend'; DST = a[1] if len(a) > 1 else 'work/anim_v1.blend'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, SRC))
rig = bpy.data.objects['Robot_Rig']; mesh = bpy.data.objects['Robot']
FPS = 24
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
LEGS = ['FL', 'FR', 'RL', 'RR']
PHASE = {'FL': 0.0, 'RR': 0.0, 'FR': 0.5, 'RL': 0.5}
TAIL = [f'Tail{k}' for k in range(1, 9)]
DUR = {'Standing': 36, 'Walking': 30, 'Attack': 21, 'Hit': 21, 'Death': 18, 'Dead': 24, 'Fidget': 18}
STEP = 0.18        # foot travel relative to the body during stance (m)
DUTY = 0.55
STRIDE = STEP / DUTY
LIFT = 0.06
RAISE = 0.015      # chassis carried higher while walking: spikes mostly slide out of their sleeves
FWD = {'FL': -0.03, 'FR': -0.03, 'RL': 0.0, 'RR': 0.0}   # stance centre relative to the rest foothold (front legs reach)
SLIDE_MIN, SLIDE_MAX = -0.012, 0.09   # cap overlap in the ring above / hidden rod extension inside the sleeve (rig)
STOW = 14.0        # gun pitch (deg, muzzle down) outside the attack
IMPACT = 0.44
SLIDE = {}
P.reset(rig)
REST_TIP = {s: (rig.matrix_world @ rig.pose.bones[f'Leg_{s}'].tail).copy() for s in LEGS}
REST_HIP = {s: (rig.matrix_world @ rig.pose.bones[f'Leg_{s}'].head).copy() for s in LEGS}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg)


def place_leg(s, target):
    """Aim the leg sleeve from its (posed) hip at target, then slide the spike so its tip reaches target."""
    leg = rig.pose.bones[f'Leg_{s}']; spike = rig.pose.bones[f'Spike_{s}']
    hip = leg.head.copy(); cur = (leg.tail - leg.head)
    q = cur.normalized().rotation_difference((target - hip).normalized())
    leg.matrix = Matrix.Translation(hip) @ q.to_matrix().to_4x4() @ Matrix.Translation(-hip) @ leg.matrix
    bpy.context.view_layer.update()
    d = (target - hip).length - (leg.tail - leg.head).length
    d = min(max(d, SLIDE_MIN), SLIDE_MAX)    # swing lift / corpse splay: the tip leaves the target along the leg
    lo, hi = SLIDE.get(s, (9, -9)); SLIDE[s] = (min(lo, d), max(hi, d))
    axis = (spike.tail - spike.head).normalized()
    spike.matrix = Matrix.Translation(axis * d) @ spike.matrix; bpy.context.view_layer.update()


def body(k):
    root = rig.pose.bones['Body']
    root.matrix = Matrix.Translation(k.get('d', Vector())) @ root.matrix; bpy.context.view_layer.update()
    rot('Body', Y, k.get('roll', 0.0)); rot('Body', X, k.get('pitch', 0.0)); rot('Body', Z, k.get('yaw', 0.0))
    rot('Neck1', X, k.get('neck', 0.0) * 0.5); rot('Neck2', X, k.get('neck', 0.0) * 0.5)
    rot('Neck1', Z, k.get('nyaw', 0.0) * 0.5); rot('Neck2', Z, k.get('nyaw', 0.0) * 0.5)
    rot('Head', X, k.get('head', 0.0)); rot('Head', Z, k.get('hyaw', 0.0))
    for i, n in enumerate(TAIL):
        rot(n, X, k.get('tail', 0.0) + k.get('twave', 0.0) * math.sin(2 * math.pi * (k.get('tt', 0.0) - i * 0.1)))
        rot(n, Z, k.get('tyaw', 0.0) * (0.4 + i / 10))
    rot('Jaw', X, -k.get('jaw', 0.0))
    rot('Gun', X, k.get('gun', STOW)); rot('Gun', Z, k.get('gyaw', 0.0))
    if k.get('recoil', 0.0):
        g = rig.pose.bones['Gun']; ax = (g.tail - g.head).normalized()
        g.matrix = Matrix.Translation(-ax * k['recoil']) @ g.matrix; bpy.context.view_layer.update()


def legs_planted(offsets=None, splay=0.0):
    """Feet on their rest footholds (+offset), body pose already applied; splay swings the targets outward."""
    for s in LEGS:
        t = REST_TIP[s].copy()
        if offsets and s in offsets:
            t += offsets[s]
        if splay:
            out = (REST_TIP[s] - REST_HIP[s]); out.z = 0; out.normalize()
            t = t + out * splay
        t.z = max(t.z, 0.0)
        place_leg(s, t)


def gait(p):
    off = {}
    for s in LEGS:
        q = (p + PHASE[s]) % 1.0
        if q < DUTY:                        # stance: foot moves back relative to the body (+Y)
            u = q / DUTY; off[s] = Vector((0, FWD[s] - STEP / 2 + STEP * u, 0))
        else:                               # swing: forward with a lift
            u = (q - DUTY) / (1 - DUTY); w = ss(u)
            off[s] = Vector((0, FWD[s] + STEP / 2 - STEP * w, LIFT * math.sin(math.pi * u)))
    return off


def idle(t, period):
    w = 2 * math.pi * t / period
    return {'d': Vector((0, 0, 0.006 * math.sin(2 * w))), 'pitch': 1.0 * math.sin(w), 'hyaw': 8 * math.sin(w),
            'neck': 2 * math.sin(w + 1), 'twave': 3.0, 'tt': t / period, 'tyaw': 4 * math.sin(w),
            'gun': STOW + 1.5 * math.sin(w + 2)}


def standing(t):
    P.reset(rig); body(idle(t, DUR['Standing'] / FPS)); legs_planted()


def walking(t):
    P.reset(rig); p = t / (DUR['Walking'] / FPS)
    k = idle(t, DUR['Walking'] / FPS / 2)
    k['d'] = Vector((0, 0, RAISE + 0.008 * math.cos(4 * math.pi * p))); k['roll'] = 2.5 * math.sin(2 * math.pi * p)
    k['gun'] = STOW + 3 * math.sin(4 * math.pi * p + 0.6)
    k['tyaw'] = 7 * math.sin(2 * math.pi * p + 1); k['nyaw'] = -4 * math.sin(2 * math.pi * p)
    body(k); legs_planted(gait(p))


def blend(a_, b_, u):
    out = {}
    for key in set(a_) | set(b_):
        va, vb = a_.get(key, 0.0), b_.get(key, 0.0)
        if isinstance(va, Vector) or isinstance(vb, Vector):
            va = va if isinstance(va, Vector) else Vector(); vb = vb if isinstance(vb, Vector) else Vector()
            out[key] = va.lerp(vb, u)
        else:
            out[key] = va + (vb - va) * u
    return out


def keyed(keys, t):
    for (t0, a_), (t1, b_) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            return blend(a_, b_, ss((t - t0) / max(t1 - t0, 1e-6)))
    return keys[-1][1]


V = Vector
I0 = idle(0, DUR['Standing'] / FPS)
A = DUR['Attack'] / FPS
ATTACK = [(0.0, I0),
          (0.17, {'d': V((0, 0.005, -0.01)), 'pitch': 1.5, 'neck': 4, 'head': -2, 'tail': 4, 'gun': -1.5}),
          (0.26, {'d': V((0, 0.008, -0.012)), 'pitch': 1.5, 'neck': 4, 'head': -2, 'tail': 5, 'gun': 0.5}),
          (0.36, {'d': V((0, 0.010, -0.013)), 'pitch': 1.5, 'neck': 5, 'head': -3, 'tail': 6, 'gun': -0.5}),
          (IMPACT, {'d': V((0, 0.010, -0.013)), 'pitch': 1.5, 'neck': 5, 'head': -3, 'tail': 6, 'gun': 0.0}),
          (IMPACT + 0.06, {'d': V((0, 0.045, -0.002)), 'pitch': -4, 'neck': 9, 'head': 1, 'tail': -4, 'twave': 8,
                           'tt': 0.3, 'gun': -2.0, 'recoil': 0.035, 'jaw': 6}),
          (0.62, {'d': V((0, 0.02, -0.008)), 'pitch': 0.5, 'neck': 5, 'head': -2, 'tail': 3, 'gun': 1.5,
                  'recoil': 0.008}),
          (0.74, {'d': V((0, 0.006, -0.004)), 'neck': 2, 'tail': 1, 'gun': 6}),
          (A, I0)]
H = DUR['Hit'] / FPS
HIT = [(0.0, I0),
       (0.10, {'d': V((-0.04, 0.05, 0.03)), 'roll': 12, 'pitch': -8, 'yaw': 10, 'neck': -15, 'hyaw': -25, 'head': -15,
               'tail': 10, 'tyaw': 15, 'jaw': 18, 'gun': STOW + 8}),
       (0.40, {'d': V((-0.015, 0.02, 0.0)), 'roll': -4, 'yaw': 3, 'neck': -4, 'hyaw': 8, 'tail': 2, 'tyaw': -6, 'jaw': 4,
               'gun': STOW - 2}),
       (H, I0)]
D = DUR['Death'] / FPS
DEATH = [(0.0, I0),
         (0.12, {'d': V((0.02, 0.03, 0.03)), 'roll': -8, 'pitch': -6, 'neck': -18, 'head': -20, 'hyaw': 20, 'tail': 10,
                 'jaw': 22, 'gun': STOW + 6}),
         (0.45, {'d': V((0, 0.03, -0.10)), 'roll': 6, 'pitch': 4, 'neck': 18, 'head': 10, 'tail': -12, 'splay': 0.20,
                 'jaw': 14, 'gun': 6}),
         (D, {'d': V((0, 0.03, -0.16)), 'roll': 4, 'pitch': 5, 'neck': 30, 'head': 15, 'tail': -18, 'splay': 0.26,
              'jaw': 16, 'gun': -2})]     # the gun folds up under the chassis, which settles onto its ball
FIDGET = [(0.0, I0), (0.18, {'nyaw': 25, 'hyaw': 20, 'neck': -5}), (0.40, {'nyaw': -25, 'hyaw': -20, 'neck': -3}),
          (0.62, {'nyaw': 10, 'hyaw': 5}), (DUR['Fidget'] / FPS, I0)]

_vg = {g.index: g.name for g in mesh.vertex_groups}
_dom = np.array([_vg.get(max(v.groups, key=lambda g: g.weight).group, '') if v.groups else '' for v in mesh.data.vertices])


def mesh_co():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    c = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', c); ev.to_mesh_clear(); return c.reshape(-1, 3)


def land(u):
    """Death floor rule: drop or lift the chassis so the lowest non-leg part rests on the floor (by fraction u), then
    raise each tail/neck segment whose parts sink below the floor."""
    if u <= 0: return
    co = mesh_co(); m = ~np.char.startswith(_dom.astype(str), 'Spike') & ~np.char.startswith(_dom.astype(str), 'Leg')
    low = co[m, 2].min()
    root = rig.pose.bones['Body']
    dz = (0.003 - low) * u
    if low + dz < 0.002: dz = 0.003 - low     # never through the floor while it falls
    root.matrix = Matrix.Translation(Vector((0, 0, dz))) @ root.matrix; bpy.context.view_layer.update()
    for chain, sign in ((TAIL, 1), (['Neck1', 'Neck2', 'Head'], -1)):
        for n in chain:
            for _ in range(30):
                co = mesh_co()
                idx = np.isin(_dom, chain[chain.index(n):])
                if co[idx, 2].min() >= 0.002: break
                rot(n, X, 2 * sign)


def generic(keys, death=False):
    def fn(t):
        P.reset(rig); k = keyed(keys, t); body(k); legs_planted(splay=k.get('splay', 0.0))
        if death:
            land(ss((t - 0.25) / 0.45))
            for s in LEGS:                   # spikes never below the floor
                for _ in range(20):
                    co = mesh_co(); m = np.isin(_dom, [f'Spike_{s}', f'Leg_{s}'])
                    if co[m, 2].min() >= 0.0: break
                    sp = rig.pose.bones[f'Spike_{s}']; ax = (sp.tail - sp.head).normalized()
                    sp.matrix = Matrix.Translation(-ax * 0.01) @ sp.matrix; bpy.context.view_layer.update()
    return fn


CLIPS = {'Standing': (True, standing), 'Walking': (True, walking), 'Attack': (False, generic(ATTACK)),
         'Hit': (False, generic(HIT)), 'Death': (False, generic(DEATH, True)),
         'Dead': (False, lambda t: generic(DEATH, True)(D)), 'Fidget': (False, generic(FIDGET))}


def key_action(name, frames, loop, fn):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = None; poses = []
    for f in range(frames + 1):
        fn((f % frames) / FPS if loop else f / FPS)
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act; prev = {}
    for f, ps in enumerate(poses):
        for b in rig.pose.bones:
            q, loc = ps[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0: q = -q
            prev[b.name] = q; b.rotation_quaternion = q; b.location = loc
            b.keyframe_insert('rotation_quaternion', frame=f + 1); b.keyframe_insert('location', frame=f + 1)
    rig.animation_data.action = None


for b in rig.pose.bones: b.rotation_mode = 'QUATERNION'
for name, (loop, fn) in CLIPS.items():
    SLIDE.clear()
    key_action(name, DUR[name], loop, fn)
    print('CLIP', name, DUR[name] / FPS, 'slide', {s: (round(a, 3), round(b, 3)) for s, (a, b) in SLIDE.items()}, flush=True)
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, DST))
print('SAVED STRIDE', round(STRIDE, 3))
