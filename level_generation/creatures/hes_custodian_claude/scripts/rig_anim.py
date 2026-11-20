"""Rig and clips of the Custodian (rigid parts, one bone each; the arm cables blended; quadruped playbook "Rigid
hard-surface creatures": one world transform per bone and frame from a parameter set, no IK).

Bones (forward -Y, left +x, metres; pivots from parts.py `joints` and the mesh):
  Root (floor, not animated) > Body (sphere centre: hover, tilt, the sweep's spin) > Sensor (sensor head on its post)
  Body > Shoulder_L/R (shoulder hub) > Elbow_L/R (elbow hub: forearm, disc housing) > Disc_L/R (saw disc: spins)
  sockets (non-deforming): Socket_Eye (Body, 2 cm in front of the eye lens' apex, work/eye.json from build.py),
  Socket_Disc_L/R (Elbow, at the disc hubs).
Arm poses are given as directions of the upper arm (shoulder -> elbow) and forearm (elbow -> hub) in the body's frame;
`flat` turns the forearm about its own axis so the disc lies flat (the sweep's horizontal blades).

Clips (24 fps): Standing 3 s, Walking 1 s, Attack 1.6 s (sweep, impact 0.5 s), Shoot 1.0 s (eye bolt, impact
0.5 s), Hit 0.5 s, Death 2.0 s, Dead 1 s, Fidget 2.5 s, SweepTelegraphed 3.0 s (the design's two-second wind-up glow
sweep, impact 2.0 s; for a later TelegraphedSweep2s behaviour, not bound).
Args: -- <in.blend> <out.blend>"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc  # noqa: E402

src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=cc.path(src))
scene = bpy.context.scene
scene.render.fps = 24
body = bpy.data.objects['Custodian']
J = {k: Vector(v) for k, v in json.loads(body['joints']).items()}
co = np.array([v.co[:] for v in body.data.vertices])
grp = {g.index: g.name for g in body.vertex_groups}
dom = np.array([grp[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in body.data.vertices])

sens = co[dom == 'Sensor']
J['Sensor'] = Vector((sens[:, 0].mean(), sens[:, 1].mean(), sens[:, 2].min()))
AXIS = {}
for side in 'LR':
    d = co[dom == f'Disc_{side}']
    c = d.mean(0)
    _, _, vt = np.linalg.svd(d - c)
    n = Vector(vt[2]).normalized()
    if n.x * (1 if side == 'L' else -1) < 0:
        n = -n
    AXIS[side] = n
    J[f'Disc_{side}'] = Vector(c)
    DISC_R = float(np.percentile(np.linalg.norm((d - c) - np.outer((d - c) @ vt[2], vt[2]), axis=1), 99))
# eye: the sphere's front surface at the body centre's height
body_pts = co[dom == 'Body']
near = body_pts[np.abs(body_pts[:, 2] - J['Body'].z) < 0.08]
near = near[np.abs(near[:, 0]) < 0.08]
EYE = Vector((0.0, near[:, 1].min() - 0.02, J['Body'].z))
if os.path.exists(cc.path('work/eye.json')):                 # build.py's eye lens: the socket at its apex
    EYE = Vector(json.load(open(cc.path('work/eye.json')))['eye_apex']) + Vector((0, -0.02, 0))
print('PIVOTS', {k: [round(x, 3) for x in v] for k, v in J.items()}, 'disc axis', {k: [round(x, 3) for x in v] for k, v in AXIS.items()},
      'disc r', round(DISC_R, 3), 'eye', [round(x, 3) for x in EYE])

# ---------------------------------------------------------------- armature
arm = bpy.data.armatures.new('Custodian_Rig')
rig = bpy.data.objects.new('Custodian_Rig', arm)
scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in scene.objects:
    o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, head, tail, parent=None, deform=True):
    b = eb.new(name); b.head, b.tail = Vector(head), Vector(tail)
    if parent:
        b.parent = eb[parent]
    b.use_deform = deform
    return b


bone('Root', (0, 0, 0), (0, 0, 0.3))
bone('Body', J['Body'], J['Body'] + Vector((0, 0, 0.4)), 'Root')
bone('Sensor', J['Sensor'], J['Sensor'] + Vector((0, 0, 0.2)), 'Body')
for s in 'LR':
    bone(f'Shoulder_{s}', J[f'Shoulder_{s}'], J[f'Elbow_{s}'], 'Body')
    bone(f'Elbow_{s}', J[f'Elbow_{s}'], J[f'Disc_{s}'], f'Shoulder_{s}')
    bone(f'Disc_{s}', J[f'Disc_{s}'], J[f'Disc_{s}'] + AXIS[s] * 0.2, f'Elbow_{s}')
    bone(f'Socket_Disc_{s}', J[f'Disc_{s}'], J[f'Disc_{s}'] + Vector((0, -0.05, 0)), f'Elbow_{s}', deform=False)
bone('Socket_Eye', EYE, EYE + Vector((0, -0.05, 0)), 'Body', deform=False)
bpy.ops.object.mode_set(mode='OBJECT')
if 'Root' in body.vertex_groups:
    body.vertex_groups.remove(body.vertex_groups['Root'])
body.parent = rig
for m in list(body.modifiers):
    body.modifiers.remove(m)
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
REST = {b.name: b.matrix_local.copy() for b in arm.bones}


def about(p, q):
    """4x4: rotate by quaternion q about point p."""
    return Matrix.Translation(p) @ q.to_matrix().to_4x4() @ Matrix.Translation(-p)


def rot_between(a, b):
    return Vector(a).normalized().rotation_difference(Vector(b).normalized())


def mirror(v, side):
    return Vector((v[0] if side == 'L' else -v[0], v[1], v[2]))


ARM_REST = {}
for s in 'LR':
    ARM_REST[s] = ((J[f'Elbow_{s}'] - J[f'Shoulder_{s}']).normalized(), (J[f'Disc_{s}'] - J[f'Elbow_{s}']).normalized())


def arm_matrices(side, upper=None, fore=None, flat=0.0, spin=0.0, drop=0.0):
    """Shoulder/Elbow/Disc transforms (body frame, rest -> pose) for directions of the upper arm and forearm (None =
    rest), `flat` 0..1 (disc turned flat about the forearm), `spin` (disc turns, radians)."""
    S, E, H = J[f'Shoulder_{side}'], J[f'Elbow_{side}'], J[f'Disc_{side}']
    u0, f0 = ARM_REST[side]
    q1 = rot_between(u0, upper) if upper is not None else Quaternion()
    f1 = q1 @ f0
    q2 = rot_between(f1, fore) if fore is not None else Quaternion()
    fdir = q2 @ f1
    n = q2 @ q1 @ AXIS[side]
    if flat:
        # turn about the forearm so the disc's axis points as close to up as it can
        up = Vector((0, 0, 1)) - fdir * fdir.z
        nn = n - fdir * n.dot(fdir)
        if up.length > 1e-6 and nn.length > 1e-6:
            ang = nn.normalized().angle(up.normalized())
            sign = 1 if nn.normalized().cross(up.normalized()).dot(fdir) > 0 else -1
            q2 = Quaternion(fdir, sign * ang * flat) @ q2
    qd = Quaternion((0, 1, 0), math.radians(drop if side == 'L' else -drop))   # + lowers the arm sideways
    G_sh = about(S, qd @ q1)
    G_el = G_sh @ about(E, (q1.inverted() @ q2 @ q1))
    G_d = G_el @ about(H, Quaternion(AXIS[side], spin))
    return {f'Shoulder_{side}': G_sh, f'Elbow_{side}': G_el, f'Disc_{side}': G_d}


def pose(lift=0.0, fwd=0.0, side=0.0, pitch=0.0, roll=0.0, yaw=0.0, sensor_yaw=0.0, sensor_pitch=0.0,
         arms=None, spin=0.0, drop=None):
    """World transforms per bone. lift/fwd/side: body offset (m; fwd toward -y); pitch + = front down, roll + = left
    side down, yaw + = turn left (degrees). arms = {'L': dict(upper=, fore=, flat=), 'R': ...} in the body frame
    (left-arm directions; mirrored for R)."""
    c = J['Body']
    rb = Quaternion((0, 0, 1), math.radians(yaw)) @ Quaternion((1, 0, 0), math.radians(-pitch)) \
        @ Quaternion((0, 1, 0), math.radians(-roll))
    G_body = Matrix.Translation((side, -fwd, lift)) @ about(c, rb)
    out = {'Root': Matrix.Identity(4), 'Body': G_body, 'Socket_Eye': G_body}
    rs = Quaternion((0, 0, 1), math.radians(sensor_yaw)) @ Quaternion((1, 0, 0), math.radians(sensor_pitch))
    out['Sensor'] = G_body @ about(J['Sensor'], rs)
    for s in 'LR':
        a = (arms or {}).get(s, {})
        up = mirror(a['upper'], s) if a.get('upper') is not None else None
        fo = mirror(a['fore'], s) if a.get('fore') is not None else None
        m = arm_matrices(s, up, fo, a.get('flat', 0.0), spin * (1 if s == 'L' else -1), (drop or {}).get(s, 0.0))
        for k, v in m.items():
            out[k] = G_body @ v
        out[f'Socket_Disc_{s}'] = out[f'Elbow_{s}']
    return out


def apply(world):
    for name in ['Root', 'Body', 'Socket_Eye', 'Sensor', 'Shoulder_L', 'Elbow_L', 'Disc_L', 'Socket_Disc_L',
                 'Shoulder_R', 'Elbow_R', 'Disc_R', 'Socket_Disc_R']:
        pb = rig.pose.bones[name]
        pb.rotation_mode = 'QUATERNION'
        pb.matrix = world[name] @ REST[name]
        bpy.context.view_layer.update()


VERTS = {'body': np.where(np.isin(dom, ['Body', 'Sensor']))[0],
         'L': np.where(np.isin(dom, ['Shoulder_L', 'Elbow_L', 'Disc_L']))[0],
         'R': np.where(np.isin(dom, ['Shoulder_R', 'Elbow_R', 'Disc_R']))[0]}


def minz():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    z = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', z)
    ev.to_mesh_clear()
    z = z.reshape(-1, 3)[:, 2]
    return {k: float(z[v].min()) for k, v in VERTS.items()}


def floor_pose(kw):
    """Floor rules on one frame (quadruped playbook): the body (sphere, vents, sensor) is lifted out of the floor (and
    with floor_body set onto it exactly); an arm under the floor is raised sideways about its shoulder until its lowest
    point is on the floor; with floor_arms set, both arms are lowered or raised onto the floor (the corpse)."""
    floor_body = kw.pop('floor_body', False)
    floor_arms = kw.pop('floor_arms', False)
    drop = {'L': 0.0, 'R': 0.0}
    kw['drop'] = drop
    apply(pose(**kw))
    z = minz()
    if z['body'] < 0 or floor_body:
        kw['lift'] = kw.get('lift', 0.0) - z['body']
        apply(pose(**kw)); z = minz()
    for s in 'LR':
        if z[s] >= -0.002 and not floor_arms:
            continue
        # the arm's lowest point falls as `drop` grows: bisect for the drop that puts it on the floor, keeping the
        # side above it (raise from [-90, 0] when it is under the floor, lower from [0, 80] onto it)
        lo, hi = (-90.0, 0.0) if z[s] < 0 else (0.0, 80.0)
        for _ in range(14):
            drop[s] = (lo + hi) / 2
            apply(pose(**kw))
            if minz()[s] < 0:
                hi = drop[s]
            else:
                lo = drop[s]
        drop[s] = lo
        apply(pose(**kw))
    return kw


def clip(name, length_s, fn):
    """Bake fn(t) -> pose kwargs at every frame of a clip of length_s seconds (end frame included), with the floor
    rules of floor_pose."""
    action = bpy.data.actions.new(name); action.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]
    n = int(round(length_s * 24))
    lows = []
    for f in range(n + 1):
        floor_pose(fn(f / 24.0))
        lows.append(min(minz().values()))
        for pb in rig.pose.bones:
            pb.keyframe_insert('rotation_quaternion', frame=f)
            pb.keyframe_insert('location', frame=f)
    if len(action.slots) and rig.animation_data.action_slot is None:
        rig.animation_data.action_slot = action.slots[0]
    action.use_frame_range = True
    action.frame_start, action.frame_end = 0, n
    print('CLIP', name, n + 1, 'frames', 'lowest point min %.3f max %.3f' % (min(lows), max(lows)))
    return action


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def seg(t, a, b):
    return ease((t - a) / (b - a))


def lerp(a, b, w):
    return a + (b - a) * w


def vlerp(a, b, w):
    return (Vector(a).lerp(Vector(b), w)).normalized()


U0, F0 = ARM_REST['L']
U_OUT, F_OUT = Vector((1, -0.05, -0.12)).normalized(), Vector((1, -0.2, 0.02)).normalized()   # sweep: arms out
U_BRACE, F_BRACE = Vector((0.55, 0.35, -0.75)).normalized(), Vector((0.25, -0.75, -0.6)).normalized()


def arms_mix(w_out=0.0, flat=0.0, brace=0.0, back=0.0):
    """Left-arm directions: rest -> out (sweep) by w_out, -> braced by brace; back swings the arm back (deg)."""
    u = vlerp(U0, U_OUT, w_out); f = vlerp(F0, F_OUT, w_out)
    if brace:
        u = vlerp(u, U_BRACE, brace); f = vlerp(f, F_BRACE, brace)
    if back:
        q = Quaternion((1, 0, 0), math.radians(back))
        u, f = q @ u, q @ f
    a = {'upper': u, 'fore': f, 'flat': flat}
    return {'L': a, 'R': a}


TAU = 2 * math.pi


def standing(t):
    p = TAU * t / 3.0
    return dict(lift=0.03 + 0.03 * math.sin(p), roll=1.2 * math.sin(p + 1.0), pitch=0.8 * math.sin(2 * p),
                sensor_yaw=28 * math.sin(p), arms=arms_mix(back=-1.5 + 1.5 * math.sin(p)), spin=TAU * 2 * t / 3.0)


def walking(t):
    p = TAU * t
    return dict(lift=-0.093 + 0.02 * math.sin(2 * p), pitch=6 + 1.0 * math.sin(p), roll=1.5 * math.sin(p),
                sensor_yaw=8 * math.sin(p), arms=arms_mix(back=-1 + 1.5 * math.sin(p)), spin=TAU * t)


def attack(t):
    # 0-0.45 wind-up (arms out, discs flat, body turns back 60 deg), 0.42-1.0 sweep through 360 deg (the discs pass
    # the front at the 0.5 s impact), 1.0-1.6 settle. The body ends on 0 deg (= 360) facing the party.
    w = seg(t, 0.0, 0.42) * (1 - seg(t, 1.05, 1.5))
    yaw = lerp(0, -60, seg(t, 0.05, 0.42))
    if t >= 0.42:
        yaw = lerp(-60, 300, min(1.0, (t - 0.42) / 0.58) ** 0.85)
    if t >= 1.0:
        yaw = lerp(300, 360, seg(t, 1.0, 1.5))
    return dict(lift=0.05 * w, pitch=-4 * w, yaw=yaw, sensor_yaw=0, arms=arms_mix(w_out=w, flat=w),
                spin=TAU * (0.5 * t + 3.0 * seg(t, 0.1, 1.2)))


def shoot(t):
    # lean back, the eye charges (0-0.5), recoil at the 0.5 s release, settle
    w = seg(t, 0.05, 0.45) * (1 - seg(t, 0.55, 1.0))
    kick = math.exp(-((t - 0.52) / 0.06) ** 2)
    return dict(lift=0.04 * w, pitch=-7 * w - 4 * kick, fwd=-0.08 * kick, sensor_pitch=-10 * w,
                arms=arms_mix(brace=0.6 * w, back=-8 * kick), spin=TAU * 0.6 * t)


def hit(t):
    k = math.exp(-((t - 0.1) / 0.09) ** 2)
    k2 = math.exp(-((t - 0.28) / 0.08) ** 2)
    return dict(lift=0.02 * k, fwd=-0.10 * k + 0.03 * k2, pitch=-8 * k + 3 * k2, roll=4 * k - 2 * k2,
                sensor_yaw=15 * k, sensor_pitch=-10 * k, arms=arms_mix(back=-18 * k + 6 * k2), spin=TAU * 0.4 * t)


def death_pose(t):
    # 0-0.6 shudder and the lights failing, 0.6-1.3 the hover cuts out: the sphere drops, rolls forward and to its
    # left, the arms fall limp outward, 1.3-2.0 settle (a small bounce), the sensor slumps
    sh = (1 - seg(t, 0.4, 0.7)) * min(1.0, t / 0.1)
    shake = sh * math.sin(TAU * 9 * t)
    drop = seg(t, 0.6, 1.25) - 0.04 * math.sin(math.pi * seg(t, 1.25, 1.6)) if t > 1.25 else seg(t, 0.6, 1.25)
    limp = seg(t, 0.6, 1.4)
    u = vlerp(U0, Vector((0.7, -0.2, -0.68)), limp); f = vlerp(F0, Vector((0.75, -0.55, -0.35)), limp)
    a = {'upper': u, 'fore': f, 'flat': 0.8 * limp}
    return dict(lift=-DROP * drop, pitch=lerp(0, 16, drop) + 2 * shake, roll=lerp(0, 9, drop) + 1.5 * shake,
                yaw=4 * drop, sensor_pitch=35 * seg(t, 0.8, 1.5), sensor_yaw=20 * seg(t, 0.8, 1.5),
                arms={'L': a, 'R': a}, spin=TAU * 1.5 * (1 - (1 - min(t / 1.2, 1)) ** 2) / 2,
                floor_body=t >= 1.25, floor_arms=t >= 1.3)


def fidget(t):
    look = math.sin(TAU * seg(t, 0.2, 1.8))
    rev = seg(t, 0.6, 1.0) * (1 - seg(t, 1.6, 2.1))
    return dict(lift=0.03 + 0.02 * math.sin(TAU * t / 2.5), sensor_yaw=70 * look, sensor_pitch=-12 * rev,
                arms={'L': {'upper': vlerp(U0, Vector((0.6, -0.55, -0.3)), rev), 'fore': vlerp(F0, Vector((0.3, -0.95, 0.1)), rev),
                            'flat': 0.0}, 'R': {'upper': U0, 'fore': F0}},
                spin=TAU * (0.8 * t / 2.5 + 2.0 * seg(t, 0.6, 1.8)))


def telegraphed(t):
    # 0-2 s: arms rise out and the body draws back slowly (the 2 s glow wind-up), 2.0-2.6 the sweep, then settle
    w = seg(t, 0.2, 1.6) * (1 - seg(t, 2.6, 3.0))
    yaw = lerp(0, -60, seg(t, 0.4, 1.9))
    if t >= 1.92:
        yaw = lerp(-60, 300, min(1.0, (t - 1.92) / 0.6) ** 0.85)
    if t >= 2.52:
        yaw = lerp(300, 360, seg(t, 2.52, 3.0))
    return dict(lift=0.05 * w + 0.02 * math.sin(TAU * 3 * t) * seg(t, 0.3, 1.9) * (1 - seg(t, 1.9, 2.0)),
                pitch=-4 * w, yaw=yaw, arms=arms_mix(w_out=w, flat=w), spin=TAU * (0.5 * t + 4.0 * seg(t, 0.3, 2.6)))


# the death drop: the vents' bottom to the floor
vent_z = float(body_pts[:, 2].min())
DROP = vent_z - 0.02
print('VENT_Z', round(vent_z, 3))
clip('Standing', 3.0, standing)
clip('Walking', 1.0, walking)
clip('Attack', 1.6, attack)
clip('Shoot', 1.0, shoot)
clip('Hit', 0.5, hit)
clip('Death', 2.0, death_pose)
clip('Dead', 1.0, lambda t: death_pose(2.0))
clip('Fidget', 2.5, fidget)
clip('SweepTelegraphed', 3.0, telegraphed)
rig.animation_data.action = bpy.data.actions['Standing']
if len(bpy.data.actions['Standing'].slots):
    rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
json.dump({'pivots': {k: list(v) for k, v in J.items()}, 'eye': list(EYE), 'disc_radius': DISC_R, 'vent_z': vent_z,
           'disc_axis': {k: list(v) for k, v in AXIS.items()}}, open(cc.path('work/rig_info.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=cc.path(dst))
print('SAVED', dst)
