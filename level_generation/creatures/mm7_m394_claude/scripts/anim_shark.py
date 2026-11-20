"""Procedural MM7 Sea Monster (shark) clips (30 fps), quadruped-playbook style (each clip is a function of time) and the
native m394 actions (one frame per 125 ms):
  Standing  1.0 s loop   hover in place: slow tail beat, a little body sway, pectorals trimming, jaw breathing
                         (native m395f: the front view with the jaw opening and closing)
  Walking   1.25 s loop  swimming: a travelling lateral wave, amplitude growing toward the tail (native m394w, 10 frames)
  Attack    1.25 s       rears nose-up with the jaws wide (m394ad/ae), lunges at the target and snaps shut (impact
                         IMPACT, m394af: jaws at the camera), dives down and back (m394ag..ai) and levels out (aj)
  Hit       0.875 s      twists onto its side and curls (belly flash, m394na..nd), recovers
  Death     1.5 s        rolls belly-up with the jaws agape, curls, sinks to the floor and settles on its back and flank (-140 deg: fully
                         belly-up propped it on the dorsal fin) (m394d, corpse
                         m394xa); Dead holds the last frame
  Fidget    = Standing in the binding (native fidget = the standing loop)
The shark faces -Y; X is its left. Rotations are world-axis about each bone's head on top of the parent's pose
(posing.rotate_world). Root (Spine1) translation stays small: melee attackers sit at the camera.
Floor: the actor origin is the swimming shark's lowest rest point (no hover lift, flyer rule); in every swimming
clip the lowest point stays >= -FLOOR_TOL; the corpse rests on z = 0.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; MESH = bpy.data.objects['Body']; sc = bpy.context.scene
FPS = 30; X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
IMPACT = 0.6
FLOOR_TOL = 0.02
TAIL = [b.name for b in rig.pose.bones if b.name.startswith('Tail')]
TAIL.sort(key=lambda n: int(n[4:]))
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
ROOT = 'Spine1'


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def mesh_co():
    dg = bpy.context.evaluated_depsgraph_get(); ev = MESH.evaluated_get(dg); me = ev.to_mesh()
    c = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', c); ev.to_mesh_clear()
    return c.reshape(-1, 3)


def pose(root_d=Vector(), pitch=0.0, roll=0.0, yaw=0.0, wave_amp=0.0, wave_phase=0.0, wave_len=1.0, tail_pitch=0.0,
         tail_curl=0.0, head_pitch=0.0, head_yaw=0.0, jaw=0.0, fins=0.0, fin_sweep=0.0):
    """One pose. Body: root offset, pitch (+ nose up), roll (+ right side down), yaw (+ nose to its left).
    Wave: lateral travelling wave along the tail, amplitude wave_amp deg at the tip (growing quadratically from the
    root), phase in turns; the chest/head counter-sway by 25 % of the first tail segment. tail_pitch/tail_curl: deg
    per segment about X (+ = tail tip up) and Z (sideways curl). Jaw opening in deg. Fins: pectoral depression (+ down)
    and sweep (+ back)."""
    P.reset(rig)
    rb = rig.pose.bones[ROOT]
    rb.matrix = Matrix.Translation(root_d) @ rb.matrix; bpy.context.view_layer.update()
    c = rb.head.copy()
    rot(ROOT, Y, roll, c); rot(ROOT, X, -pitch, c); rot(ROOT, Z, yaw, c)    # roll about the body axis first;
    # facing -Y, +X rotation pitches the nose DOWN (rat pitfall): + pitch = nose up
    n = len(TAIL); first = 0.0
    for i, name in enumerate(TAIL):
        u = (i + 1) / n
        a = wave_amp * (0.15 + 0.85 * u * u) / n * 2.2 * math.sin(2 * math.pi * (wave_phase - wave_len * u))
        if i == 0:
            first = a
        b = rig.pose.bones[name]; h = b.head.copy()
        axz = (rig.matrix_world @ rig.pose.bones[ROOT].matrix).to_3x3() @ Z      # the body's own up
        axx = (rig.matrix_world @ rig.pose.bones[ROOT].matrix).to_3x3() @ X
        rot(name, axz, a + tail_curl, h); rot(name, axx, tail_pitch, h)
    if 'Spine2' in rig.pose.bones:
        b = rig.pose.bones['Spine2']; axz = (rig.matrix_world @ rb.matrix).to_3x3() @ Z
        rot('Spine2', axz, -0.25 * first + 0.5 * head_yaw, b.head.copy())
    hb = rig.pose.bones['Head']; M = (rig.matrix_world @ hb.matrix).to_3x3()
    rot('Head', M @ X, 0.0, None)
    axx = (rig.matrix_world @ rb.matrix).to_3x3() @ X; axz = (rig.matrix_world @ rb.matrix).to_3x3() @ Z
    rot('Head', axx, -head_pitch, hb.head.copy()); rot('Head', axz, 0.5 * head_yaw, hb.head.copy())
    if 'Jaw' in rig.pose.bones:
        jb = rig.pose.bones['Jaw']; axj = (rig.matrix_world @ hb.matrix).to_3x3() @ X
        # the jaw hangs down: rotate its tip down about the head's lateral axis (+ angle = opening)
        rot('Jaw', (rig.matrix_world @ rb.matrix).to_3x3() @ X, -jaw, jb.head.copy())
    for s, sg in (('L', 1.0), ('R', -1.0)):
        fn = f'Fin_{s}'
        if fn in rig.pose.bones:
            fb = rig.pose.bones[fn]; M = (rig.matrix_world @ rb.matrix).to_3x3()
            rot(fn, M @ Y, -sg * fins, fb.head.copy())     # depress the fin tip (+ down)
            rot(fn, M @ Z, sg * fin_sweep, fb.head.copy())


def floor_fit(ground=False):
    co = mesh_co(); low = co[:, 2].min()
    if low < -FLOOR_TOL or ground:
        rb = rig.pose.bones[ROOT]
        rb.matrix = Matrix.Translation(Vector((0, 0, -low if ground else -low - FLOOR_TOL))) @ rb.matrix
        bpy.context.view_layer.update()


def lerp(a, b, u):
    return a + (b - a) * u


def keyed(keys, t):
    """keys: [(time, {param: value})], smoothstep between keys; params missing in a key hold the previous value."""
    names = set(k for _, d in keys for k in d)
    full = []; cur = {}
    for tk, d in keys:
        cur = dict(cur); cur.update(d); full.append((tk, cur))
    if t <= full[0][0]:
        return dict(full[0][1])
    for (t0, a), (t1, b) in zip(full, full[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6)); r = {}
            for k in names:
                va, vb = a.get(k, 0.0), b.get(k, a.get(k, 0.0))
                r[k] = va.lerp(vb, u) if isinstance(va, Vector) else lerp(va, vb, u)
            return r
    return dict(full[-1][1])


def standing(t):
    T = 1.0; ph = t / T
    pose(root_d=Vector((0, 0, 0.012 * math.sin(2 * math.pi * ph))), wave_amp=14, wave_phase=ph, wave_len=0.8,
         roll=1.5 * math.sin(2 * math.pi * ph), jaw=6 + 6 * (0.5 - 0.5 * math.cos(2 * math.pi * ph)),
         fins=4 * math.sin(2 * math.pi * ph + 1.0), head_yaw=-2 * math.sin(2 * math.pi * ph))


def walking(t):
    T = 38 / FPS; ph = t / T                  # 1.25 s native = 37.5 frames: the loop is 38 whole frames
    pose(root_d=Vector((0.015 * math.sin(2 * math.pi * ph), 0, 0.01 * math.sin(4 * math.pi * ph))),
         wave_amp=34, wave_phase=ph, wave_len=1.0, jaw=8, fins=6 + 3 * math.sin(2 * math.pi * ph),
         fin_sweep=4, head_yaw=-4 * math.sin(2 * math.pi * ph), roll=2 * math.sin(2 * math.pi * ph))


ATTACK = [(0.0, {'pitch': 0.0, 'jaw': 8.0, 'root_d': Vector(), 'tail_pitch': 0.0, 'head_pitch': 0.0, 'fins': 4.0}),
          (0.30, {'pitch': 32.0, 'jaw': 38.0, 'root_d': Vector((0, 0.10, 0.18)), 'tail_pitch': -6.0, 'head_pitch': 6.0, 'fins': 22.0}),
          (0.45, {'pitch': 26.0, 'jaw': 46.0, 'root_d': Vector((0, 0.06, 0.22)), 'tail_pitch': -4.0, 'head_pitch': 4.0}),
          (0.60, {'pitch': -8.0, 'jaw': 4.0, 'root_d': Vector((0, -0.22, 0.12)), 'tail_pitch': 4.0, 'head_pitch': -6.0, 'fins': 10.0}),
          (0.85, {'pitch': -22.0, 'jaw': 6.0, 'root_d': Vector((0, -0.08, 0.06)), 'tail_pitch': 6.0, 'head_pitch': -4.0}),
          (1.25, {'pitch': 0.0, 'jaw': 8.0, 'root_d': Vector(), 'tail_pitch': 0.0, 'head_pitch': 0.0, 'fins': 4.0})]


def attack(t):
    k = keyed(ATTACK, t)
    pose(root_d=k['root_d'], pitch=k['pitch'], jaw=k['jaw'], tail_pitch=k['tail_pitch'], head_pitch=k['head_pitch'],
         fins=k['fins'], wave_amp=20 + 18 * math.sin(math.pi * min(t / 1.25, 1)), wave_phase=t / 0.6, wave_len=0.9)


HIT = [(0.0, {'roll': 0.0, 'tail_curl': 0.0, 'pitch': 0.0, 'jaw': 8.0, 'root_d': Vector()}),
       (0.18, {'roll': -70.0, 'tail_curl': 14.0, 'pitch': 10.0, 'jaw': 30.0, 'root_d': Vector((0.04, 0.10, 0.04))}),
       (0.40, {'roll': -95.0, 'tail_curl': 18.0, 'pitch': 6.0, 'jaw': 22.0}),
       (0.875, {'roll': 0.0, 'tail_curl': 0.0, 'pitch': 0.0, 'jaw': 8.0, 'root_d': Vector()})]


def hit(t):
    k = keyed(HIT, t)
    pose(root_d=k['root_d'], roll=k['roll'], tail_curl=k['tail_curl'], pitch=k['pitch'], jaw=k['jaw'],
         wave_amp=12, wave_phase=t / 0.5)


DEATH = [(0.0, {'roll': 0.0, 'tail_curl': 0.0, 'tail_pitch': 0.0, 'pitch': 0.0, 'jaw': 8.0, 'fins': 4.0}),
         (0.35, {'roll': -110.0, 'tail_curl': 16.0, 'pitch': 14.0, 'jaw': 40.0, 'fins': -10.0}),
         (0.75, {'roll': -150.0, 'tail_curl': 8.0, 'tail_pitch': 3.0, 'pitch': 4.0, 'jaw': 34.0, 'fins': -12.0}),
         (1.5, {'roll': -140.0, 'tail_curl': 5.0, 'tail_pitch': 2.0, 'pitch': 0.0, 'jaw': 28.0, 'fins': -8.0})]


def death(t):
    k = keyed(DEATH, t)
    pose(roll=k['roll'], tail_curl=k['tail_curl'], tail_pitch=k['tail_pitch'], pitch=k['pitch'], jaw=k['jaw'],
         fins=k['fins'], wave_amp=10 * (1 - ss(t / 0.9)), wave_phase=t / 0.5)


def key_action(name, seconds, loop, fn, ground_after=None):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = None
    n = int(round(seconds * FPS)); poses = []; lows = []
    for f in range(n + 1):
        t = (f % n) / FPS if loop else f / FPS
        fn(t)
        if ground_after is not None:
            # sink: blend the root down until the lowest point rests on the floor
            co = mesh_co(); low = co[:, 2].min(); u = ss((t - ground_after[0]) / (ground_after[1] - ground_after[0]))
            rb = rig.pose.bones[ROOT]
            rb.matrix = Matrix.Translation(Vector((0, 0, -low * u))) @ rb.matrix; bpy.context.view_layer.update()
            floor_fit()
        else:
            floor_fit()
        lows.append(float(mesh_co()[:, 2].min()))
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, ps in enumerate(poses):
        for b in rig.pose.bones:
            q, loc = ps[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q; b.rotation_quaternion = q; b.location = loc
            b.keyframe_insert('rotation_quaternion', frame=f); b.keyframe_insert('location', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    print(f'CLIP {name} {seconds} s lowest point {100 * min(lows):.1f}..{100 * max(lows):.1f} cm')
    return act


for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
key_action('Standing', 1.0, True, standing)
key_action('Walking', 1.25, True, walking)
key_action('Attack', 1.25, False, attack)
key_action('Hit', 0.875, False, hit)
key_action('Death', 1.5, False, death, ground_after=(0.5, 1.3))
key_action('Dead', 1.0, False, lambda t: death(1.5), ground_after=(-1.0, 0.0))
json.dump({'fps': FPS, 'attack_impact_s': IMPACT}, open(os.path.join(HERE, 'work', 'clips.json'), 'w'), indent=1)
P.reset(rig)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print('SAVED', out)
