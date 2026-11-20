"""Procedural beholder clips (24 fps) from the native MM7 m166 frames, tier A timing (3 ticks of 1/16 s per pose):
  Fly    36 f (24 ticks, wa-wh) loop: hover bob and slow sway, each tentacle waves with a lag along its chain and a
         phase of its own, the eye stalks sway;
  Attack 22 f (15 ticks, aa-ae): the head draws back and the tentacles flare while the central eye charges (glow
         event), then the head thrusts forward at the release (0.6 s), recover;
  Hit    18 f (12 ticks, na-nd): recoil back and twist, tentacles flung, recover;
  Death  27 f (18 ticks: wa0 wb0 da-dd): shudder, the top-left stalk's eyeball pops off, arcs up and falls beside the body;
         the head drops onto the floor and the tentacles lie splayed flat around it (corpse xa); Dead = held.
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
rig = bpy.data.objects['Beholder_Rig']; mesh = bpy.data.objects['Beholder']
FPS = 24
DUR = {'Fly': 36, 'Attack': 22, 'Hit': 18, 'Death': 27, 'Dead': 24}
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
CH = {}
for b in rig.pose.bones:
    if b.name.startswith(('Tentacle', 'Stalk')) and '_' in b.name:
        CH.setdefault(b.name.split('_')[0], []).append(b.name)
CH = {k: sorted(v, key=lambda n: int(n.split('_')[1])) for k, v in CH.items()}
TENT = sorted(k for k in CH if k.startswith('Tentacle')); STALK = sorted(k for k in CH if k.startswith('Stalk'))
P.reset(rig)
HEAD0 = rig.pose.bones['Head'].head.copy()
RADIAL = {}
for k, names in CH.items():
    r = rig.pose.bones[names[0]].tail - HEAD0; r.z = 0
    RADIAL[k] = r.normalized() if r.length > 1e-4 else Vector((0, 1, 0))
PHASE = {k: (i * 0.37) % 1.0 for i, k in enumerate(sorted(CH))}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg):
    if abs(deg) > 1e-6: P.rotate_world(rig, name, axis, deg)


def axis_of(k):
    return -Z.cross(RADIAL[k])             # rotating about it swings the chain outward (+)


def chain(k, degs):
    for n, d in zip(CH[k], degs): rot(n, axis_of(k), d)


def pose(t, k):
    P.reset(rig)
    root = rig.pose.bones['Body']
    root.matrix = Matrix.Translation(k.get('d', Vector())) @ root.matrix; bpy.context.view_layer.update()
    rot('Body', Z, k.get('yaw', 0.0)); rot('Body', Y, k.get('roll', 0.0)); rot('Body', X, k.get('pitch', 0.0))
    period = k.get('period', DUR['Fly'] / FPS); wave = k.get('wave', 7.0); flare = k.get('flare', 0.0)
    for kk in TENT:
        n = len(CH[kk])
        chain(kk, [flare * (1.0 if j == 0 else 0.5) + wave * (0.5 + j / n) *
                   math.sin(2 * math.pi * (t / period + PHASE[kk]) - 0.9 * j) for j in range(n)])
    for kk in STALK:
        chain(kk, [k.get('stalk', 0.0) + 6 * math.sin(2 * math.pi * (t / period * 2 + PHASE[kk])), 4 * math.sin(2 * math.pi * (t / period * 2 + PHASE[kk]) - 1)])
    eb = rig.pose.bones['StalkEye']
    if k.get('pop'):
        eb.matrix = Matrix.Translation(k['pop']) @ eb.matrix; bpy.context.view_layer.update()
        rot('StalkEye', X, k.get('spin', 0.0))


def hover(t):
    T = DUR['Fly'] / FPS
    return {'d': Vector((0, 0, 0.015 * math.sin(2 * math.pi * t / T))), 'pitch': 3 * math.sin(2 * math.pi * t / T + 1),
            'roll': 2.5 * math.sin(2 * math.pi * t / T), 'yaw': 3 * math.sin(2 * math.pi * t / T), 'wave': 7.0}


def blend(a, b, u):
    out = {}
    for key in set(a) | set(b):
        va, vb = a.get(key, 0.0), b.get(key, 0.0)
        if isinstance(va, Vector) or isinstance(vb, Vector):
            va = va if isinstance(va, Vector) else Vector(); vb = vb if isinstance(vb, Vector) else Vector()
            out[key] = va.lerp(vb, u)
        else:
            out[key] = va + (vb - va) * u
    return out


def keyed(keys, t):
    for (t0, a_), (t1, b_) in zip(keys[:-1], keys[1:]):
        if t <= t1: return blend(a_, b_, ss((t - t0) / max(t1 - t0, 1e-6)))
    return keys[-1][1]


V = Vector
A = DUR['Attack'] / FPS; H = DUR['Hit'] / FPS; D = DUR['Death'] / FPS
ATTACK = [(0.0, hover(0)),
          (0.35, {'pitch': -14, 'd': V((0, 0.04, 0.02)), 'flare': 16, 'wave': 4, 'stalk': 12}),
          (0.60, {'pitch': 10, 'd': V((0, -0.06, -0.01)), 'flare': 6, 'wave': 9, 'stalk': -6}),
          (0.75, {'pitch': 6, 'd': V((0, -0.04, 0.0)), 'flare': 2, 'wave': 8}),
          (A, hover(0))]
HIT = [(0.0, hover(0)),
       (0.10, {'pitch': -20, 'roll': 14, 'yaw': 10, 'd': V((0, 0.07, 0.03)), 'flare': 20, 'wave': 12, 'stalk': 18}),
       (0.40, {'pitch': -8, 'roll': -6, 'd': V((0, 0.03, 0.01)), 'flare': 6, 'wave': 8}),
       (H, hover(0))]
DEATH = [(0.0, hover(0)),
         (0.20, {'pitch': -15, 'roll': 10, 'd': V((0, 0.03, 0.03)), 'flare': 18, 'wave': 14, 'stalk': 20,
                 'pop': V((0.04, -0.03, 0.12)), 'spin': 90}),
         (0.45, {'pitch': 5, 'roll': -8, 'd': V((0, 0.0, -0.10)), 'flare': 30, 'wave': 6, 'stalk': 25,
                 'pop': V((0.10, -0.10, 0.10)), 'spin': 250}),
         (0.80, {'pitch': 10, 'roll': -4, 'd': V((0, 0.0, -0.30)), 'flare': 45, 'wave': 0, 'stalk': 30,
                 'pop': V((0.16, -0.20, -0.30)), 'spin': 400}),
         (D, {'pitch': 10, 'roll': -4, 'd': V((0, 0.0, -0.32)), 'flare': 48, 'wave': 0, 'stalk': 32,
              'pop': V((0.17, -0.22, -0.32)), 'spin': 420})]

vg = {g.index: g.name for g in mesh.vertex_groups}
dom = np.array([vg.get(max(v.groups, key=lambda g: g.weight).group, '') if v.groups else '' for v in mesh.data.vertices])
HEADV = np.isin(dom, ['Head', 'Body', 'Tongue']); EYEV = dom == 'StalkEye'
TV = {k: np.array([d.startswith(k + '_') for d in dom]) for k in TENT}


def mesh_co():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    c = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', c); ev.to_mesh_clear(); return c.reshape(-1, 3)


def land(u):
    """Death floor rule: drop the head onto the floor (2 mm), lay every tentacle bone flat along its radial direction
    at its own radius above the floor, lift any tentacle still under the floor bone by bone, and rest the popped eye on the floor."""
    if u <= 0: return
    co = mesh_co()
    root = rig.pose.bones['Body']
    root.matrix = Matrix.Translation(Vector((0, 0, (0.002 - co[HEADV, 2].min()) * u))) @ root.matrix
    bpy.context.view_layer.update()
    for k in TENT:
        for n in CH[k]:
            b = rig.pose.bones[n]; L = (b.tail - b.head).length
            cur = (b.tail - b.head).normalized()
            dz = (0.014 - b.head.z)
            want = (RADIAL[k] * L + Vector((0, 0, max(-L * 0.9, min(L * 0.9, dz))))).normalized()
            q = Quaternion().slerp(cur.rotation_difference(want), u)
            h = b.head.copy(); b.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ b.matrix
            bpy.context.view_layer.update()
    co = mesh_co()
    for k in TENT:                         # a tentacle still under the floor lifts bone by bone, not the body
        for j, n in enumerate(CH[k]):
            sel = np.isin(dom, CH[k][j:]); step = 0
            while co[sel, 2].min() < 0.0015 and step < 30:
                rot(n, axis_of(k), 2.0); co = mesh_co(); step += 1
    low = co[~EYEV, 2].min()
    if low < 0.0015:
        root.matrix = Matrix.Translation(Vector((0, 0, 0.0015 - low))) @ root.matrix; bpy.context.view_layer.update()
    co = mesh_co(); el = co[EYEV, 2].min()
    eb = rig.pose.bones['StalkEye']
    eb.matrix = Matrix.Translation(Vector((0, 0, (0.002 - el) * u))) @ eb.matrix; bpy.context.view_layer.update()


def clip(keys, frames, death=False):
    def fn(t):
        pose(t - frames / FPS, keyed(keys, t))     # waves end on the Fly start phase
        if death: land(ss((t - 0.45) / 0.4))
    return fn


CLIPS = {'Fly': (True, lambda t: pose(t, hover(t))), 'Attack': (False, clip(ATTACK, DUR['Attack'])),
         'Hit': (False, clip(HIT, DUR['Hit'])), 'Death': (False, clip(DEATH, DUR['Death'], True)),
         'Dead': (False, lambda t: (pose(0.0, keyed(DEATH, D)), land(1.0)))}


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
    key_action(name, DUR[name], loop, fn); print('CLIP', name, DUR[name] / FPS, flush=True)
rig.animation_data.action = bpy.data.actions['Fly']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, DST))
print('SAVED')
