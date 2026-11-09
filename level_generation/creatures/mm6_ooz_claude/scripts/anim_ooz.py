"""Ooze clips (24 fps): work/rig_uv.blend -> work/anim_v1.blend. No limbs: every clip is a function of time giving,
per bone, a world-space offset and scale about the bone's rest head. Lump heads lie on the floor, so their scales
and horizontal offsets never lift or sink the underside; the pod is hidden (PodRoot scale 0.02 inside the blob)
except in Attack. Native timing (mm6_ooz manifest): walk/attack/hit/fidget 750 ms (6 x 125 ms), death 625 ms.
  Standing  24 f  slow pulse (body breathes, lumps undulate out of phase)
  Walking   18 f  peristaltic wave front -> back: lumps rise and push forward in turn, body stretches along travel
  Running   12 f  the same, larger and faster
  Attack    18 f  native a-f: pod shoots up from the middle (2.1x the blob height), bends into an inverted L,
                  arches over into a loop, angles up again, sinks back (bends forward toward the target)
  Hit       18 f  lumps bubble up in two waves, the body jiggles and settles
  Death     15 f  centre swells and bursts, lumps splash outward, everything collapses into a flat spread residue
  Dead       2 f  the residue held
  Fidget    18 f  pulse with one bubble rising and sinking
  Cast      18 f  spit: the middle rears into a dome, contracts sharply, settles (Socket_Spit on the centre lump)
Pose: world matrices set with no action attached, keyed afterwards."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_uv.blend'))
arm, mesh = bpy.data.objects['Ooze_Rig'], bpy.data.objects['Ooze']
# decimation left a few underside vertices up to 1 cm below the floor; clamp them (positions only, UVs kept)
for v in mesh.data.vertices:
    if v.co.z < 0.0:
        v.co.z = 0.0
mesh.data.update()
scene = bpy.context.scene
scene.render.fps = 24
# spit socket for the cast glow (BOoze B/C cast Poison Spray / Toxic Cloud): top of the centre lump, rides with it
if 'Socket_Spit' not in arm.data.bones:
    for o in bpy.data.objects:
        o.select_set(o == arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    sb = arm.data.edit_bones.new('Socket_Spit')
    top = dict(scene['ooz_dims'])['top']
    sb.head, sb.tail = Vector((0, 0, top)), Vector((0, 0, top + 0.04))
    sb.parent = arm.data.edit_bones['Lump_C']
    sb.use_deform = False
    bpy.ops.object.mode_set(mode='OBJECT')
AW = arm.matrix_world
DIMS = dict(scene['ooz_dims'])
LUMPS = [f'Lump_{i}' for i in range(8)]
PODS = [f'Pod{i + 1}' for i in range(6)]
ORDER = ['Root', 'Body', 'Lump_C'] + LUMPS + ['PodRoot'] + PODS + ['Socket_Spit']
REST = {n: AW @ arm.data.bones[n].matrix_local for n in ORDER}
HEAD = {n: REST[n].translation.copy() for n in ORDER}
F = Vector((0, -1, 0))                                  # forward
ss = lambda x: x * x * (3 - 2 * x)


def lump_xy(n):
    h = HEAD[n]
    return Vector((h.x, h.y, 0))


def keyed(t, keys):
    """Smoothstep between (time, value) keys; values are floats or tuples."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            u = ss((t - t0) / (t1 - t0))
            if isinstance(a, tuple):
                return tuple(x + (y - x) * u for x, y in zip(a, b))
            return a + (b - a) * u
    return keys[-1][1]


def base_pose():
    p = {n: {'off': Vector(), 'scale': Vector((1, 1, 1)), 'rot': Quaternion()} for n in ORDER}
    p['PodRoot']['scale'] = Vector((0.02, 0.02, 0.02))
    return p


def body_squash(p, sx, sy, sz, dx=0.0, dy=0.0):
    """Whole-body squash about the floor centre: lump heads move with the xy scale, their own scales follow."""
    p['Body']['scale'] = Vector((sx, sy, sz))
    for n in ['Lump_C'] + LUMPS:
        xy = lump_xy(n)
        p[n]['off'] += Vector((xy.x * (sx - 1) + dx, xy.y * (sy - 1) + dy, 0))
        p[n]['scale'] = Vector((p[n]['scale'].x * sx, p[n]['scale'].y * sy, p[n]['scale'].z * sz))


def standing(t, amp=1.0):
    p = base_pose()
    w = 2 * math.pi * t
    for i, n in enumerate(LUMPS):
        p[n]['scale'].z *= 1 + 0.06 * amp * math.sin(w + i * math.pi / 4)
    p['Lump_C']['scale'].z *= 1 + 0.05 * amp * math.sin(w + 1.0)
    body_squash(p, 1 - 0.012 * amp * math.sin(w), 1 - 0.012 * amp * math.sin(w), 1 + 0.035 * amp * math.sin(w))
    return p


def crawl(t, amp):
    p = base_pose()
    w = 2 * math.pi * t
    for n in ['Lump_C'] + LUMPS:
        y = lump_xy(n).y / max(DIMS['ry'], 1e-3)          # -1 front .. +1 back
        ph = w + 2.2 * y                                  # the wave starts at the front and runs back
        p[n]['scale'].z *= 1 + 0.20 * amp * math.sin(ph)
        p[n]['scale'].x *= 1 - 0.06 * amp * math.sin(ph)
        p[n]['off'] += F * (0.025 * amp * math.cos(ph))
    body_squash(p, 1 - 0.02 * amp * math.sin(2 * w), 1 + 0.05 * amp * math.sin(2 * w), 1 - 0.03 * amp * math.sin(2 * w))
    return p


# native attack keys (oozata..f, front view, 125 ms each): bend per pod segment (deg, + = forward, toward the target;
# the front-view sprites draw it sideways only because they are 2D; user review: strike toward the party) and pod scale. a bump, b tall lumpy column, c column bent 90 deg at the top
# (inverted L), d arched over into a loop with the tip pointing down, e tall with the tip angled up and sideways,
# f sinking back.
ATTACK_KEYS = [
    (0.000, 0.02, (0, 0, 0, 0, 0, 0)),
    (0.075, 0.35, (0, 0, 0, 0, 0, 0)),
    (0.125, 1.00, (4, -6, 5, -4, 6, 4)),
    (0.250, 1.00, (0, 0, 0, 10, 72, 12)),
    (0.375, 1.00, (0, 0, 12, 58, 62, 60)),
    (0.500, 1.00, (0, 0, 0, 0, 22, 32)),
    (0.625, 0.65, (3, -5, 6, -4, 5, 3)),
    (0.750, 0.02, (0, 0, 0, 0, 0, 0)),
]


def attack(t):
    p = standing(0.0, 0.0)
    T = t * 0.75
    grow = keyed(T, [(k[0], k[1]) for k in ATTACK_KEYS])
    bends = keyed(T, [(k[0], tuple(float(x) for x in k[2])) for k in ATTACK_KEYS])
    p['PodRoot']['scale'] = Vector((grow, grow, grow))
    lean = keyed(T, [(0.0, 0.0), (0.125, -6.0), (0.25, 0.0), (0.75, 0.0)])         # a short wind-up back before the strike
    p['PodRoot']['rot'] = Quaternion(Vector((1, 0, 0)), math.radians(lean))      # +X rotation tips +Z toward -Y
    for n, ang in zip(PODS, bends):
        p[n]['rot'] = Quaternion(Vector((1, 0, 0)), math.radians(ang))           # +X rotation tips +Z toward -Y (forward)
    sq = keyed(T, [(0.0, 1.0), (0.1, 1.06), (0.25, 0.96), (0.375, 0.92), (0.5, 0.95), (0.75, 1.0)])
    body_squash(p, 1 + (1 - sq) * 0.5, 1 + (1 - sq) * 0.5, sq)
    p['Lump_C']['scale'] *= 1 + 0.35 * (grow - 0.02)      # the base swells where the pod emerges
    return p


def hit(t):
    p = base_pose()
    T = t * 0.75
    for i, n in enumerate(['Lump_C'] + LUMPS):
        delay = 0.0 if i % 2 == 0 else 0.15
        b = keyed(T, [(0.0, 0.0), (0.12 + delay, 1.0), (0.32 + delay, 0.25), (0.6, 0.0)])
        p[n]['scale'].z *= 1 + 0.6 * b
        p[n]['scale'].x *= 1 + 0.15 * b
        p[n]['scale'].y *= 1 + 0.15 * b
    j = math.exp(-4 * T) * math.sin(2 * math.pi * 3 * T)
    body_squash(p, 1 + 0.06 * j, 1 - 0.06 * j, 1 - 0.05 * j)
    return p


def death(t):
    p = base_pose()
    T = t * 0.625
    swell = keyed(T, [(0.0, 0.0), (0.18, 1.0), (0.25, 0.3), (0.625, 0.0)])
    burst = keyed(T, [(0.0, 0.0), (0.18, 0.0), (0.28, 1.0), (0.625, 1.0)])
    flat = keyed(T, [(0.0, 0.0), (0.22, 0.0), (0.625, 1.0)])
    p['Lump_C']['scale'] = Vector((1 + 0.3 * swell + 0.6 * burst, 1 + 0.3 * swell + 0.6 * burst, 1 + 1.4 * swell))
    for n in LUMPS:
        xy = lump_xy(n)
        p[n]['off'] += xy.normalized() * (0.07 * burst)
        p[n]['scale'] = Vector((1 + 0.25 * burst, 1 + 0.25 * burst, 1 + 0.5 * swell))
    body_squash(p, 1 + 0.25 * flat, 1 + 0.25 * flat, 1 - 0.82 * flat)
    return p


def cast(t):
    """Spit (Poison Spray / Toxic Cloud): the middle rears into a dome, then contracts sharply and settles."""
    p = base_pose()
    T = t * 0.75
    rear = keyed(T, [(0.0, 0.0), (0.3, 1.0), (0.38, 1.0), (0.45, -0.35), (0.6, 0.1), (0.75, 0.0)])
    p['Lump_C']['scale'] = Vector((1 - 0.15 * max(rear, 0), 1 - 0.15 * max(rear, 0), 1 + 1.3 * rear))
    for n in LUMPS:
        p[n]['scale'].z *= 1 + 0.35 * rear
        p[n]['off'] += -lump_xy(n).normalized() * (0.03 * max(rear, 0))     # draw in toward the middle
    body_squash(p, 1 - 0.05 * rear, 1 - 0.05 * rear, 1 + 0.08 * rear)
    return p


def fidget(t):
    p = standing(t, 0.8)
    b = math.sin(math.pi * min(t / 0.8, 1.0)) ** 2
    p['Lump_3']['scale'] *= Vector((1 + 0.2 * b, 1 + 0.2 * b, 1 + 0.55 * b))
    return p


CLIPS = {'Standing': (24, lambda t: standing(t)), 'Walking': (18, lambda t: crawl(t, 1.0)),
         'Running': (12, lambda t: crawl(t, 1.5)), 'Attack': (18, attack), 'Hit': (18, hit),
         'Death': (15, death), 'Dead': (1, lambda t: death(1.0)), 'Fidget': (18, fidget), 'Cast': (18, cast)}


def apply(p):
    for n in ORDER:
        d = p[n]
        R = REST[n]
        head = HEAD[n]
        rot = d['rot'].to_matrix().to_4x4()
        S = Matrix.Diagonal((d['scale'].x, d['scale'].y, d['scale'].z, 1.0))
        if n.startswith('Pod') and n != 'PodRoot':
            # pod segments: rotate about their own head, carried by the parent's current pose
            parent = arm.pose.bones[n].parent
            P = AW @ parent.matrix
            Pr = AW @ arm.data.bones[parent.name].matrix_local
            M = P @ Pr.inverted() @ R                     # rest relation to the parent kept
            M = Matrix.Translation(M.translation) @ rot @ Matrix.Translation(-M.translation) @ M
        else:
            M = Matrix.Translation(head + d['off']) @ rot @ S @ Matrix.Translation(-head) @ R
        arm.pose.bones[n].matrix = AW.inverted() @ M
        bpy.context.view_layer.update()


arm.animation_data_create()
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'
report = {}
for name, (n, fn) in CLIPS.items():
    arm.animation_data.action = None
    poses = []
    for f in range(n + 1):
        t = f / n if n > 0 else 0.0
        apply(fn(t))
        poses.append({pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy())
                      for pb in arm.pose.bones})
        dg = bpy.context.evaluated_depsgraph_get()
        em = mesh.evaluated_get(dg).to_mesh()
        zs = np.array([(mesh.matrix_world @ v.co).z for v in em.vertices])
        report.setdefault(name, []).append((round(float(zs.min()), 4), round(float(zs.max()), 3)))
        mesh.evaluated_get(dg).to_mesh_clear()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    for f, pose in enumerate(poses):
        for pb in arm.pose.bones:
            pb.location, pb.rotation_quaternion, pb.scale = pose[pb.name]
            pb.keyframe_insert('location', frame=f)
            pb.keyframe_insert('rotation_quaternion', frame=f)
            pb.keyframe_insert('scale', frame=f)
    lows = [r[0] for r in report[name]]
    highs = [r[1] for r in report[name]]
    print('CLIP', name, 'frames', n + 1, 'min z %.4f' % min(lows), 'max z %.3f' % max(highs))
arm.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'anim_v1.blend'))
