"""Gait pass (2026-10-21): two new locomotion clips on the clip master, sized for the game's speeds, and a donor GLB
for add_clips.py. The installed Walking (0.327 m per 1.25 s, 0.26 m/s) plays 2.3-3.8x wandering and 4.5-7.7x chasing;
gait_gate.py asks for authored speeds of about 0.72 (walk, window 0.67-0.78) and 1.45 (run, 1.33-1.57) m/s.

  Walk2 18 f (0.75 s) loop: four-beat lateral-sequence walk (RL, FL, RR, FR a quarter cycle apart), duty 0.65, so two
        or three spikes are always planted. Stride 0.54 m (0.72 m/s). The chassis rides 3 cm higher than at rest so
        the spikes, sliding through their sleeves, can reach under and behind the hips; it rolls toward the swinging
        side, bobs on each footfall; the neck counter-sways and the head holds steady; the gun swings on its bracket.
  Run2  14 f (0.583 s) loop: trotting run with diagonal pairs (FL+RR, FR+RL), duty 0.36, so each pair is followed by a
        short suspension. Stride 0.85 m (1.46 m/s). The chassis pitches nose down and sinks at each mid-stance and
        rises through the suspension; the neck stretches forward with the head level; the tail streams back lower
        with a whip; the gun is tucked higher. Spikes lift 8 cm in swing.

In stance each spike tip stays on its foothold, moving back at exactly the body speed, so the binding stride equals
the clip stride. Slides stay within the rig's range (-1.2 ... +9 cm); a stance target outside it is reported (FOOT).
Args: [in.blend out.blend donor.glb] (default work/uv_master.blend -> work/gait2.blend, work/gait2_donor.glb)."""
import bpy, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SRC = a[0] if a else 'work/uv_master.blend'
DST = a[1] if len(a) > 1 else 'work/gait2.blend'
DONOR = a[2] if len(a) > 2 else 'work/gait2_donor.glb'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, SRC))
rig = bpy.data.objects['Robot_Rig']; mesh = bpy.data.objects['Robot']
FPS = 24
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
LEGS = ['FL', 'FR', 'RL', 'RR']
TAIL = [f'Tail{k}' for k in range(1, 9)]
SLIDE_MIN, SLIDE_MAX = -0.012, 0.09      # cap overlap in the ring above / hidden rod extension inside the sleeve (rig)
STOW = 14.0
GAITS = {
    # fwd: centre of each stance relative to its hip (m, -Y forward). The spike reaches 0.30-0.40 m from the hip, so
    # the long steps are centred near the hips: front feet a little ahead, rear feet level with them.
    'Walk2': dict(frames=18, stride=0.54, duty=0.65, phase={'RL': 0.0, 'FL': 0.25, 'RR': 0.5, 'FR': 0.75},
                  lift=0.05, raise_=0.030, fwd={'FL': -0.05, 'FR': -0.05, 'RL': 0.0, 'RR': 0.0}),
    'Run2': dict(frames=14, stride=0.85, duty=0.36, phase={'FL': 0.0, 'RR': 0.0, 'FR': 0.5, 'RL': 0.5},
                 lift=0.08, raise_=0.040, fwd={'FL': -0.08, 'FR': -0.08, 'RL': 0.0, 'RR': 0.0}),
}
SLIDE = {}
CLAMP = []
P.reset(rig)
REST_TIP = {s: (rig.matrix_world @ rig.pose.bones[f'Leg_{s}'].tail).copy() for s in LEGS}
REST_HIP = {s: (rig.matrix_world @ rig.pose.bones[f'Leg_{s}'].head).copy() for s in LEGS}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg)


def place_leg(s, target, stance):
    """Aim the leg sleeve from its (posed) hip at target, then slide the spike so its tip reaches target."""
    leg = rig.pose.bones[f'Leg_{s}']; spike = rig.pose.bones[f'Spike_{s}']
    hip = leg.head.copy(); cur = (leg.tail - leg.head)
    q = cur.normalized().rotation_difference((target - hip).normalized())
    leg.matrix = Matrix.Translation(hip) @ q.to_matrix().to_4x4() @ Matrix.Translation(-hip) @ leg.matrix
    bpy.context.view_layer.update()
    want = (target - hip).length - (leg.tail - leg.head).length
    d = min(max(want, SLIDE_MIN), SLIDE_MAX)
    if stance and abs(d - want) > 1e-4:
        CLAMP.append((s, round(want, 4), tuple(round(v, 3) for v in (target - hip))))
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


def feet(g, p):
    """Foot targets in the body frame at cycle phase p: stance moves back at the body speed, swing forward with lift."""
    step = g['stride'] * g['duty']
    out = {}
    for s in LEGS:
        q = (p - g['phase'][s]) % 1.0
        base = Vector((REST_TIP[s].x, REST_HIP[s].y + g['fwd'][s], 0))
        if q < g['duty']:
            u = q / g['duty']
            out[s] = (base + Vector((0, -step / 2 + step * u, 0)), True)
        else:
            u = (q - g['duty']) / (1 - g['duty']); w = ss(u)
            # Lift peaks early (the tip clears the floor before it reaches forward) and sets down softly.
            lift = g['lift'] * math.sin(math.pi * u ** 0.8)
            out[s] = (base + Vector((0, step / 2 - step * w, lift)), False)
    for s, (t, stance) in out.items():
        t.z = 0.0 if stance else max(t.z, 0.0)
    return out


def walk2(t):
    g = GAITS['Walk2']; p = t / (g['frames'] / FPS); w = 2 * math.pi * p
    P.reset(rig)
    # Four footfalls per cycle: a small dip after each, roll away from the swinging side (left swings at 0.68-1.0 for
    # RL and 0.93-0.25 for FL; right half a cycle later).
    k = {'d': Vector((0, 0, g['raise_'] - 0.005 * math.cos(4 * w))),
         'roll': 2.2 * math.sin(w + 0.6), 'pitch': 0.8 * math.sin(2 * w), 'yaw': 1.5 * math.sin(w + 0.3),
         'neck': 1.5 * math.cos(4 * w), 'head': -1.5 * math.cos(4 * w),           # head holds level over the bob
         'nyaw': -3.0 * math.sin(w + 0.3), 'hyaw': -2.0 * math.sin(w + 0.3),
         'tail': 0.0, 'twave': 3.5, 'tt': p, 'tyaw': 6.0 * math.sin(w + 1.6),
         'gun': STOW + 2.5 * math.sin(4 * w + 0.8), 'gyaw': 2.0 * math.sin(w + 1.2)}
    body(k)
    for s, (target, stance) in feet(g, p).items():
        place_leg(s, target, stance)


def run2(t):
    g = GAITS['Run2']; p = t / (g['frames'] / FPS); w = 2 * math.pi * p
    P.reset(rig)
    # Each diagonal pair is planted for 0.36 of the cycle from p = 0 / 0.5: lowest at mid-stance (p = 0.18 / 0.68),
    # highest in the suspension (0.43 / 0.93). The sink and pitch stay small: the short spikes must still reach the
    # floor under the hips (at least 0.30 m from the hip).
    c = math.cos(4 * math.pi * (p - 0.18))
    k = {'d': Vector((0, 0, g['raise_'] - 0.005 * c)),
         'pitch': 1.5 + 0.5 * c, 'roll': 0.8 * math.sin(w), 'yaw': 1.0 * math.sin(w + 0.5),
         'neck': 8.0 + 2.5 * c, 'head': -11.0 - 2.5 * c,                           # neck forward, head level
         'nyaw': -2.5 * math.sin(w), 'hyaw': -1.5 * math.sin(w),
         'tail': -3.0, 'twave': 6.0, 'tt': 2 * p, 'tyaw': 5.0 * math.sin(w + 1.6),
         'gun': 6.0 + 3.5 * math.cos(4 * math.pi * (p - 0.32)), 'gyaw': 1.5 * math.sin(w + 1.2), 'jaw': 2.0}
    body(k)
    for s, (target, stance) in feet(g, p).items():
        place_leg(s, target, stance)


def key_action(name, frames, fn):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = None; poses = []
    for f in range(frames + 1):
        fn((f % frames) / FPS)
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
for name, fn in (('Walk2', walk2), ('Run2', run2)):
    SLIDE.clear(); CLAMP.clear()
    g = GAITS[name]
    key_action(name, g['frames'], fn)
    print('CLIP', name, round(g['frames'] / FPS, 4), 'stride', g['stride'], 'speed', round(g['stride'] * FPS / g['frames'], 3),
          'slide', {s: (round(lo, 3), round(hi, 3)) for s, (lo, hi) in SLIDE.items()}, flush=True)
    print('FOOT', name, 'stance clamps', len(CLAMP), CLAMP[:8], flush=True)
rig.animation_data.action = bpy.data.actions['Standing']
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, DST))
for o in bpy.context.scene.objects: o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, DONOR), use_selection=True, export_format='GLB',
    export_yup=True, export_animations=True, export_animation_mode='ACTIONS', export_frame_range=False,
    export_force_sampling=True, export_frame_step=1, export_skins=True, export_all_influences=False,
    export_attributes=False, export_morph=False, export_materials='NONE', export_reset_pose_bones=True,
    export_anim_slide_to_zero=True, export_extras=True)
print('DONOR', DONOR, sorted(x.name for x in bpy.data.actions), flush=True)
