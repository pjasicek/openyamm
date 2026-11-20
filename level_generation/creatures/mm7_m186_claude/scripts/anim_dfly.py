"""Procedural dragonfly clips (24 fps) from the native MM7 m186 frames and ticks (1/16 s):
  Fly    24 f (16 ticks) loop: four wings beat fast (fore and hind pairs in opposition, six beats per loop), a slow
         wave runs down the S-shaped abdomen, the claw opens and closes, small hover bob;
  Attack 21 f (14 ticks): native aa-ag: coil (abdomen curls, head draws back), then lunge: the abdomen swings back
         towards horizontal while the head strikes forward (bite at 0.55 s), recover;
  Cast   21 f: rear up, head lifts, wings high, then the head snaps forward to spit (release at 0.5 s), recover;
  Hit    21 f (14 ticks): native na-ng: jolt back, body twists, wings flung, recover;
  Death  27 f (18 ticks): native na-nc, da-df: flinch, wings fold up, the body straightens out horizontally behind
         the head and drops onto the floor (corpse xa: lying flat, wings raised); Dead = held.
Bones rotate about world axes through their heads (forward -Y, up +Z, left +X): +X on an abdomen bone swings its
end backwards; wings flap about the forward axis.
Args: [in.blend out.blend] relative to the project (default work/rig_v1.blend -> work/anim_v1.blend)."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SRC = a[0] if a else 'work/rig_v1.blend'; DST = a[1] if len(a) > 1 else 'work/anim_v1.blend'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, SRC))
rig = bpy.data.objects['Dragonfly_Rig']; mesh = bpy.data.objects['Dragonfly']
FPS = 24
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
ABD = [f'Abd{k}' for k in range(1, 11)]
DUR = {'Fly': 24, 'Attack': 21, 'Cast': 21, 'Hit': 21, 'Death': 27, 'Dead': 24}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg)


def straighten(u, direction):
    """Aim each abdomen bone (and the claw) along `direction` by fraction u, from the thorax down."""
    if u <= 1e-4:
        return
    for name in ABD + ['Claw']:
        b = rig.pose.bones[name]
        cur = (b.tail - b.head).normalized()
        q = cur.rotation_difference(direction.normalized())
        q = Quaternion().slerp(q, u)
        h = b.head.copy()
        b.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ b.matrix
        bpy.context.view_layer.update()


def wings(phase, amp, up=0.0, sweep=0.0):
    """Fore and hind pairs beat in opposition; up raises both, sweep swings them back about the vertical."""
    for side, sg in (('L', 1), ('R', -1)):
        f = up + amp * math.sin(2 * math.pi * phase)
        h = up + amp * math.sin(2 * math.pi * phase + math.pi * 0.8)
        rot(f'ForeWing_{side}', Z, -sg * sweep); rot(f'HindWing_{side}', Z, -sg * sweep * 1.2)
        rot(f'ForeWing_{side}', Y, -sg * f); rot(f'HindWing_{side}', Y, -sg * h)


def pose(t_beat, k):
    P.reset(rig)
    root = rig.pose.bones['Thorax']
    root.matrix = Matrix.Translation(k.get('d', Vector())) @ root.matrix; bpy.context.view_layer.update()
    rot('Thorax', Y, k.get('roll', 0.0)); rot('Thorax', Z, k.get('yaw', 0.0)); rot('Thorax', X, k.get('pitch', 0.0))
    wave = k.get('wave', 0.0)
    for i, n in enumerate(ABD):
        rot(n, X, k.get('curl', 0.0) + wave * math.sin(2 * math.pi * (k.get('wt', 0.0) - i * 0.09)))
        rot(n, Z, k.get('twist', 0.0) * (0.5 + i / 20))
    straighten(k.get('straight', 0.0), k.get('sdir', Vector((0, 1, -0.15))) if k.get('sdir', Vector()).length > 0 else Vector((0, 1, -0.15)))
    rot('Claw', X, k.get('claw', 0.0))
    rot('Neck', X, k.get('neck', 0.0)); rot('Head', X, k.get('head', 0.0)); rot('Head', Z, k.get('hyaw', 0.0))
    wings(t_beat, k.get('amp', 32.0), k.get('wup', 0.0), k.get('sweep', 0.0))


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
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            return blend(a, b, ss((t - t0) / max(t1 - t0, 1e-6)))
    return keys[-1][1]


def hover(t):
    return {'d': Vector((0, 0, 0.008 * math.sin(2 * math.pi * t))), 'wave': 3.0, 'wt': t, 'claw': 8 * math.sin(2 * math.pi * t),
            'head': -2 * math.sin(2 * math.pi * t), 'pitch': 1.5 * math.sin(2 * math.pi * t)}


V = Vector
BEATS = 6        # wing beats per second
A = DUR['Attack'] / FPS
ATTACK = [(0.0, hover(0)),
          (0.25, {'curl': -4, 'neck': -14, 'head': -12, 'd': V((0, 0.03, 0.01)), 'claw': -25, 'amp': 30}),
          (0.40, {'pitch': 30, 'straight': 0.5, 'neck': -22, 'head': -10, 'd': V((0, -0.04, 0.0)), 'claw': 10, 'amp': 34}),
          (0.55, {'pitch': 62, 'straight': 0.85, 'neck': -55, 'head': 12, 'd': V((0, -0.12, -0.03)), 'claw': 20, 'amp': 36}),
          (0.68, {'pitch': 55, 'straight': 0.8, 'neck': -50, 'head': 4, 'd': V((0, -0.10, -0.02)), 'claw': 15}),
          (A, hover(0))]
CAST = [(0.0, hover(0)),
        (0.30, {'pitch': -18, 'curl': 3, 'neck': -10, 'head': -25, 'd': V((0, 0.03, 0.03)), 'claw': -30, 'wup': 15, 'amp': 34}),
        (0.50, {'pitch': 12, 'neck': 10, 'head': 18, 'd': V((0, -0.04, 0.0)), 'claw': 10, 'wup': -5, 'amp': 36}),
        (0.62, {'pitch': 8, 'neck': 6, 'head': 10, 'd': V((0, -0.03, 0.0)), 'claw': 5}),
        (A, hover(0))]
H = DUR['Hit'] / FPS
HIT = [(0.0, hover(0)),
       (0.10, {'pitch': -22, 'roll': 18, 'twist': 4, 'curl': 3, 'neck': -15, 'head': -20, 'd': V((0, 0.06, 0.03)), 'wup': 25,
               'amp': 40, 'claw': -20}),
       (0.40, {'pitch': -10, 'roll': -8, 'twist': -2, 'neck': -6, 'head': -8, 'd': V((0, 0.03, 0.01)), 'wup': 8}),
       (H, hover(0))]
D = DUR['Death'] / FPS
DEATH = [(0.0, hover(0)),
         (0.18, {'pitch': -20, 'roll': 15, 'neck': -18, 'head': -22, 'd': V((0, 0.05, 0.03)), 'wup': 30, 'amp': 40, 'claw': -25}),
         (0.45, {'pitch': 45, 'straight': 0.6, 'neck': -40, 'head': 8, 'wup': 55, 'amp': 15, 'sweep': 20, 'claw': 15,
                 'd': V((0, 0.02, -0.06))}),
         (0.80, {'pitch': 80, 'straight': 1.0, 'neck': -108, 'head': -30, 'wup': 70, 'amp': 0, 'sweep': 35, 'claw': 25,
                 'd': V((0, 0.04, -0.12)), 'sdir': V((0, 1, 0.02))}),
         (D, {'pitch': 82, 'straight': 1.0, 'neck': -112, 'head': -32, 'wup': 72, 'amp': 0, 'sweep': 38, 'claw': 25,
              'd': V((0, 0.04, -0.12)), 'sdir': V((0, 1, 0.02))})]

_vg = {g.index: g.name for g in mesh.vertex_groups}
_dom = [_vg.get(max(v.groups, key=lambda g: g.weight).group, '') if v.groups else '' for v in mesh.data.vertices]
BODY = np.array(['Wing' not in n for n in _dom])


def mesh_co():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    c = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', c); ev.to_mesh_clear(); return c.reshape(-1, 3)


def land(u):
    """Death floor rule: lower (or raise) the root so the body's lowest point reaches the floor (2 mm), by fraction u;
    then raise each wing until it clears the floor."""
    if u <= 0:
        return
    low = mesh_co()[BODY, 2].min()
    root = rig.pose.bones['Thorax']
    root.matrix = Matrix.Translation(Vector((0, 0, (0.002 - low) * u))) @ root.matrix; bpy.context.view_layer.update()
    co = mesh_co()
    for side, sg in (('L', 1), ('R', -1)):
        for w in ('ForeWing', 'HindWing'):
            name = f'{w}_{side}'; m = np.array([n == name for n in _dom])
            step = 0
            while co[m, 2].min() < 0.002 and step < 40:
                rot(name, Y, -sg * 3); co = mesh_co(); step += 1


def fly(t):
    pose((t * BEATS) % 1.0, hover(t))


def clip(keys, death=False, frames=24):
    beats = round(frames / FPS * BEATS)            # whole beats, so the clip ends on the Fly start pose

    def fn(t):
        pose((t * FPS / frames * beats) % 1.0, keyed(keys, t))
        if death:
            land(ss((t - 0.3) / 0.5))
    return fn


CLIPS = {'Fly': (True, fly), 'Attack': (False, clip(ATTACK, frames=DUR['Attack'])),
         'Cast': (False, clip(CAST, frames=DUR['Cast'])), 'Hit': (False, clip(HIT, frames=DUR['Hit'])),
         'Death': (False, clip(DEATH, True, DUR['Death'])), 'Dead': (False, lambda t: (pose(0.0, keyed(DEATH, D)), land(1.0)))}


def key_action(name, frames, loop, fn):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = None
    poses = []
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
