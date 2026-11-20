"""Procedural Griffin clips (30 fps keys), from the native MM7 griffin actions (m258: the creature never lands;
standing, walking and fidget share the flight frames; 7 frames x 125 ms per action).
  Fly      0.900 s loop  wing beat on the native rhythm (0.875 s), downstroke 45 % of the cycle; body rises on the downstroke,
                         eagle legs reach forward, lion legs trail, tail streams straight back with a lagging wave
  Attack   1.000 s       rear up with the wings raised (native m258ab/ac), rake both talons forward and down with a
                         hard downbeat (impact IMPACT), recover into the flight pose
  Hit      0.750 s       jolt back and up, wings flare, head pulls back, legs flail, recover
  Death    1.250 s       wings fold, tumble over onto the back, wings spread flat on landing (native m258da..dd)
  Dead     1.000 s       last Death pose held
Wings: each segment's DIRECTION and feather-plane NORMAL are set in the chest's frame from one parametric left-wing
pose (mirrored for the right), so the asymmetric rest wings (three-quarter master) move as one symmetric pose.
The tail is aimed segment by segment along the body's back axis (the rest tail swings 45 deg to the left).
Floor: the airborne clips get one constant clearance (the lowest vertex over the whole Fly cycle at z = FLOOR_GAP),
no per-frame grounding (wyvern lesson); Attack/Hit add an eased lift only where rearing up would dip below it;
Death moves the lowest vertex smoothly from its flight height down to exactly z = 0 (Dead holds it there).
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
FLY_T = 0.9; IMPACT = 0.55; FLOOR_GAP = 0.02   # native cycle 0.875 s; 0.9 s = 27 whole frames, a seamless loop
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
names = [b.name for b in rig.data.bones]
SIDE = {'L': 1.0, 'R': -1.0}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def env(t, a, b, c, d):
    """0 before a, ease up to 1 at b, hold, ease down to 0 at d"""
    if t <= a or t >= d:
        return 0.0
    if t < b:
        return ss((t - a) / (b - a))
    if t <= c:
        return 1.0
    return 1.0 - ss((t - c) / (d - c))


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def set_frame(name, ydir, znrm):
    """world orientation of a bone from its Y (along) and Z (roll/normal) axes, head kept"""
    b = rig.pose.bones[name]
    y = ydir.normalized(); z = (znrm - y * znrm.dot(y)).normalized(); x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = b.head.copy()
    b.matrix = M; bpy.context.view_layer.update()


def chest():
    return (rig.matrix_world @ rig.pose.bones['Spine3'].matrix).to_3x3()


CH0 = REST['Spine3'].to_3x3()


def wing_pose(elev, sweep, fold, droop, twist, spread=1.0):
    """left-wing segment directions and normals in a body frame (x left, -y forward, z up), degrees.
    elev: shoulder elevation; sweep: backward sweep of the arm; fold: extra sweep at elbow and wrist (folding);
    droop: hand drop below the arm; twist: feather plane pitch (leading edge down = +)."""
    out = []
    e = [elev, elev * 0.75 - droop * 0.5, elev * 0.55 - droop]
    a = [sweep, sweep + fold * 0.8, sweep + fold * 1.6]
    for k in range(3):
        er, ar = math.radians(e[k]), math.radians(a[k])
        d = Vector((math.cos(er) * math.cos(ar) * spread, math.sin(ar) * math.cos(er), math.sin(er)))
        side = d.cross(Vector((0, 0, 1))).normalized()              # points backward (+y) for the left wing
        n = Vector((0, 0, 1)) - d * d.z
        n = (Quaternion(d, math.radians(twist)) @ n).normalized()
        out.append((d.normalized(), n))
    return out


def wings(elev, sweep, fold, droop, twist):
    C = chest() @ CH0.inverted()                                    # the chest's rotation from rest
    for s, sg in (('L', 1), ('R', -1)):
        for k, (d, n) in enumerate(wing_pose(elev, sweep, fold, droop, twist)):
            m = Vector((sg, 1, 1))
            dw = C @ Vector((d.x * sg, d.y, d.z)); nw = C @ Vector((n.x * sg, n.y, n.z))
            set_frame(f'Wing{k + 1}_{s}', dw, nw)


def tail(yaw_amp, pitch_amp, phase, droop=8.0, lift=0.0):
    hips = (rig.matrix_world @ rig.pose.bones['Spine1'].matrix).to_3x3() @ REST['Spine1'].to_3x3().inverted()
    for i in range(1, 6):
        b = rig.pose.bones[f'Tail{i}']; L = (b.tail - b.head).length
        k = i / 5
        yaw = yaw_amp * k * math.sin(2 * math.pi * (phase - 0.12 * i))
        pitch = -droop * (0.4 + 0.6 * k) + lift * (1 - k) + pitch_amp * k * math.sin(2 * math.pi * (phase - 0.12 * i) + 1.0)
        d = Quaternion(Z, math.radians(yaw)) @ Quaternion(X, math.radians(pitch)) @ Vector((0, 1, 0))
        P.aim_bone(rig, b.name, rig.matrix_world @ b.head + (hips @ d) * L)


def leg_fk(name, axis_world, deg):
    rot(name, axis_world, deg)


def body(dz=0.0, dy=0.0, pitch=0.0, roll=0.0, yaw=0.0, spine=0.0, neck=0.0, head=0.0, head_yaw=0.0):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(Vector((0, dy, dz))) @ root.matrix; bpy.context.view_layer.update()
    c = rig.pose.bones['Spine2'].head.copy()                         # pitch about the body's middle
    rot('Spine1', Z, yaw, c); rot('Spine1', Y, roll, c); rot('Spine1', X, pitch, c)
    rot('Spine2', X, spine * 0.5); rot('Spine3', X, spine * 0.5)
    rot('Neck1', X, neck * 0.5); rot('Neck2', X, neck * 0.5); rot('Head', X, head); rot('Head', Z, head_yaw)


def legs(front_reach=0.0, front_curl=0.0, hind_swing=0.0, hind_tuck=0.0, phase=0.0, flail=0.0):
    for s in 'LR':
        ph = 0.0 if s == 'L' else 0.5
        f = flail * math.sin(2 * math.pi * (phase * 3 + ph))
        rot(f'UpperArm_{s}', X, -front_reach + f * 0.6)               # -X rotation swings the leg forward/up
        rot(f'ForeArm_{s}', X, front_curl * 0.5)
        rot(f'FrontPaw_{s}', X, front_curl)
        rot(f'Thigh_{s}', X, hind_swing * math.sin(2 * math.pi * (phase + ph * 0.3)) - f * 0.5)
        rot(f'Shin_{s}', X, hind_tuck)


# ---------------------------------------------------------------- clip functions (t in seconds)
def beat(t, T=FLY_T, down=0.45):
    """wing phase 0..1 warped so the downstroke takes `down` of the cycle; returns elevation factor +1 up .. -1 down"""
    u = (t / T) % 1.0
    if u < down:
        return math.cos(math.pi * u / down)                          # +1 -> -1 (downstroke)
    return -math.cos(math.pi * (u - down) / (1 - down))              # -1 -> +1 (upstroke)


def fly_pose(t, amp=1.0):
    b = beat(t); up = (b + 1) / 2
    phase = (t / FLY_T) % 1.0
    body(dz=-0.05 * b * amp, pitch=2.0 * b, spine=-2 * b, neck=-3 * b, head=4 * b)
    upst = max(0.0, -math.sin(2 * math.pi * (phase - 0.45) / 0.55 * 0.5)) if phase > 0.45 else 0.0
    wings(elev=8 + 40 * b * amp, sweep=6 - 4 * b, fold=10 + 28 * upst, droop=8 * up + 6, twist=6 + 10 * b)
    legs(front_reach=4 * b, front_curl=6, hind_swing=6, hind_tuck=4, phase=phase)
    tail(10, 6, phase)


def attack_pose(t):
    # 0-0.40 rear up, wings rise; 0.40-IMPACT rake + downbeat; to 1.0 recover
    r = env(t, 0.0, 0.40, 0.48, 0.95); s = env(t, 0.36, IMPACT, IMPACT + 0.05, 0.95)
    phase = (t / FLY_T) % 1.0
    up = env(t, 0.0, 0.38, 0.40, IMPACT)
    elev = 8 + 55 * up - 45 * s
    body(dz=0.06 * r - 0.04 * s, dy=0.12 * r - 0.30 * s, pitch=-28 * r + 18 * s, spine=-10 * r + 6 * s,
         neck=-12 * r + 22 * s, head=-8 * r + 14 * s)
    wings(elev=elev, sweep=8 - 14 * up + 10 * s, fold=10 + 6 * up, droop=6 + 10 * s, twist=6 + 18 * s)
    legs(front_reach=35 * r + 25 * s, front_curl=-25 * r + 35 * s, hind_swing=4, hind_tuck=10 * r, phase=phase)
    tail(8, 10, phase, lift=12 * r)


def hit_pose(t):
    h = env(t, 0.0, 0.10, 0.18, 0.70); phase = (t / FLY_T) % 1.0
    body(dz=0.05 * h, dy=0.15 * h, pitch=-16 * h, roll=8 * h, spine=-8 * h, neck=-14 * h, head=-12 * h)
    wings(elev=8 + 50 * h, sweep=6 - 10 * h, fold=10, droop=6, twist=6 - 8 * h)
    legs(front_reach=-10 * h, front_curl=10, hind_swing=4, hind_tuck=8 * h, phase=phase, flail=14 * h)
    tail(14, 14, phase, lift=10 * h)


DEATH_T = 1.25


def death_pose(t):
    """wings fold while it tumbles over onto its back, then spread flat on the floor as it lands (a wing folded
    under a side-lying body propped the corpse 30 cm up)"""
    f = ss(t / 0.30)
    folded = env(t, 0.0, 0.30, 0.60, 1.05)
    roll = ss((t - 0.12) / 0.85)
    fall = ss((t - 0.10) / 0.95)
    phase = (t / FLY_T) % 1.0
    body(dz=-0.25 * fall, pitch=-10 * f + 10 * fall, roll=-180 * roll, spine=-6 * fall, neck=-25 * f + 10 * fall,
         head=-10 * f - 10 * fall, head_yaw=25 * fall)
    wp = dict(elev=30 * (1 - f) + 14 * ss((t - 0.6) / 0.45) - 12 * folded, sweep=6 + 50 * folded + 12 * fall,
              fold=10 + 40 * folded, droop=6 - 10 * fall, twist=6)
    wings(**wp)
    legs(front_reach=10 * f + 20 * fall, front_curl=10 + 35 * fall, hind_swing=4 * (1 - fall), hind_tuck=25 * fall,
         phase=phase, flail=12 * env(t, 0.0, 0.15, 0.45, 0.8))
    tail(10 * (1 - fall), 8 * (1 - fall), phase, droop=8 + 6 * fall)
    if fall > 0.3:
        clamp_limbs()
        # wings no lower than the back: spread wings drooping below the body propped the corpse up like a tent (bat)
        for _ in range(15):
            z = mesh_z()
            if z[WING].min() > z[CORE].min() - 0.01:
                break
            wp['elev'] -= 3 * fall; wp['droop'] -= 2 * fall
            wings(**wp)


# ---------------------------------------------------------------- limb floor rule (rat clamp_limbs)
_vn = [g.name for g in MESH.vertex_groups]
_dom = np.array([_vn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in MESH.data.vertices])
CORE = np.array([n.startswith(('Spine', 'Neck', 'Head')) for n in _dom])
WING = np.array([n.startswith('Wing') for n in _dom])
LIMB = {(u, sd): np.array([n.endswith('_' + sd) and n.split('_')[0] in grp for n in _dom])
        for u, grp in (('UpperArm', ('UpperArm', 'ForeArm', 'FrontPaw')), ('Thigh', ('Thigh', 'Shin', 'HindPaw')))
        for sd in 'LR'}


def mesh_z():
    dg = bpy.context.evaluated_depsgraph_get(); ev = MESH.evaluated_get(dg); m = ev.to_mesh()
    c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); ev.to_mesh_clear()
    return c.reshape(-1, 3)[:, 2]


def clamp_limbs(margin=0.03):
    """a leg reaching below the body's lowest core point (spine/neck/head) swings up about its upper joint"""
    for (upper, sd), mask in LIMB.items():
        name = f'{upper}_{sd}'
        for _ in range(20):
            z = mesh_z(); low, core = z[mask].min(), z[CORE].min()
            if low > core - margin:
                break
            b = rig.pose.bones[name]
            d = (b.tail - b.head).normalized(); axis = d.cross(Vector((0, 0, 1)))
            if axis.length < 1e-3:
                axis = Vector((1, 0, 0))
            axis.normalize()
            P.rotate_world(rig, name, axis, -8.0)
            if mesh_z()[mask].min() < low:
                P.rotate_world(rig, name, axis, 16.0)


# ---------------------------------------------------------------- write, floor


def low_z():
    dg = bpy.context.evaluated_depsgraph_get(); ev = MESH.evaluated_get(dg); m = ev.to_mesh()
    c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); ev.to_mesh_clear()
    return float(c.reshape(-1, 3)[:, 2].min())


def make(name, dur, fn, loop=False):
    n = int(round(dur * FPS)); act = bpy.data.actions.get(name)
    if act:
        bpy.data.actions.remove(act)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    lows = []
    for i in range(n + 1):
        t = (i / FPS) % dur if loop else i / FPS
        P.reset(rig); fn(t)
        lows.append(low_z())
        for b in rig.pose.bones:
            b.keyframe_insert('rotation_quaternion', frame=i)
            if b.name == 'Spine1':
                b.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    return act, np.array(lows)


def shift(act, dz):
    """add dz (array per frame or scalar) to the root's world z"""
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = map(int, act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        b = rig.pose.bones['Spine1']; M = rig.matrix_world @ b.matrix
        M.translation.z += float(dz[f - f0] if hasattr(dz, '__len__') else dz)
        b.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
        b.keyframe_insert('location', frame=f)
    rig.animation_data.action = None


report = {}
fly, lf = make('Fly', FLY_T, fly_pose, loop=True)
clear = FLOOR_GAP - lf.min()


def eased_lift(lows, base):
    """base clearance plus an eased extra lift wherever the clip would dip below FLOOR_GAP (rearing up lowers the
    hind legs): max over +-3 frames, then a 7-frame smoothing that never goes below the need"""
    need = np.clip(FLOOR_GAP - (lows + base), 0, None)
    m = np.array([need[max(0, i - 3):i + 4].max() for i in range(len(need))])
    k = np.array([1, 2, 3, 4, 3, 2, 1], float); k /= k.sum()
    sm = np.convolve(np.pad(m, 3, mode='edge'), k, 'valid')
    return base + np.maximum(sm, need)


for name, dur, fn in (('Attack', 1.0, attack_pose), ('Hit', 0.75, hit_pose)):
    act, l = make(name, dur, fn)
    lift = eased_lift(l, clear); shift(act, lift)
    report[name] = {'lowest_cm': round(float((l + lift).min()) * 100, 1), 'extra_lift_cm': round(float((lift - clear).max()) * 100, 1),
                    'duration': dur}
shift(fly, clear); report['Fly'] = {'clearance_m': round(clear, 3), 'duration': FLY_T,
                                    'lowest_cm': round((lf.min() + clear) * 100, 1)}
death, ld = make('Death', DEATH_T, death_pose)
# start at the flight clearance, then fall: grounded (lowest vertex on z = 0) once the airborne offset is used up
# the lowest vertex descends from its flight height to exactly the floor (z = 0) and stays there
h0 = ld[0] + clear
h = np.array([h0 * (1 - ss(i / FPS / 0.95)) for i in range(len(ld))])
shift(death, h - ld)
rig.animation_data.action = death; sc.frame_set(int(death.frame_range[1]))
held = {b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones}
rig.animation_data.action = None
dead = bpy.data.actions.new('Dead'); dead.use_fake_user = True; rig.animation_data.action = dead
if len(dead.slots):
    rig.animation_data.action_slot = dead.slots[0]
for f in (0, FPS):
    for b in rig.pose.bones:
        b.rotation_quaternion, b.location = held[b.name]
        b.keyframe_insert('rotation_quaternion', frame=f); b.keyframe_insert('location', frame=f)
dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, FPS
rig.animation_data.action = None
P.reset(rig)
report['Death'] = {'duration': DEATH_T}
report['Attack']['impact'] = IMPACT
json.dump(report, open(os.path.join(HERE, 'work', 'clips.json'), 'w'), indent=1)
print('ANIM', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
