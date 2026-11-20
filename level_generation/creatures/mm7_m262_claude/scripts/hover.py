"""m262 hover: the harpy never stands (native standing, walking and fidget are all the flight loop wa..wh, 1.0 s).
1. Walking = the flight loop, authored over Standing frame 0 (Mixamo Standard Idle): the trunk pitched PITCH deg
   forward about the pelvis (+-2 with the beat), a bob BOB m (up on the downstroke; phase 0 = top of the upstroke as
   the native wa frame), the left arm raised forward before the body (the right arm is aimed by author_carry.py:
   knife up before the chest, as the native flight frames).
2. Bird legs on Walking, Attack, Hit and Death (the retargeted humanoid legs are replaced): angles about the
   pelvis' lateral axis, applied to each bone in turn (negative = the distal end swings forward): thigh (hip ->
   hidden knee) TUCK_THIGH forward, drumstick (knee -> hock) TUCK_CALF back, tarsus (hock -> ball) TUCK_TARSUS
   forward, toes TUCK_TOES curled; legs half a cycle apart sway +-KICK in the flight. Attack: a talon kick toward the
   blow (thighs up, drumsticks and tarsi extended forward, toes open) peaking at the impact (IMPACT s), eased in/out.
   Hit: the tuck, flinching back by 15 deg at 0.15 s. Death: the tuck easing into LEGS UP (the corpse lies on its back
   with the legs raised and the toes clenched, native xa) from the fall's start.
3. Height: Walking, Attack and Hit hover at a constant pelvis lift per clip so the lowest vertex over the clip is
   CLEAR m above the floor (the actor origin; playbook flyers: no extra hover); Death keeps the clip's fall and lifts
   any frame whose lowest vertex is under the floor.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
PITCH, BOB, CLEAR, KICK = E('PITCH', 15), E('BOB', 0.03), E('CLEAR', 0.05), E('KICK', 5)
TUCK = [E('TUCK_THIGH', -55), E('TUCK_CALF', 95), E('TUCK_TARSUS', -70), E('TUCK_TOES', 35)]
TALON = [-95, 45, -35, -15]
UP = [-85, 70, -40, 55]
IMPACT = E('IMPACT', 0.983)
FPS, N = 30, 30
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; scene.render.fps = FPS
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
deps = bpy.context.evaluated_depsgraph_get()
LEG = {s: [f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot', f'B_{s}_Toe0'] for s in 'LR'}


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def rot_world(pb, deg, axis):
    bpy.context.view_layer.update()
    M = rig.matrix_world @ pb.matrix
    h = M.translation.copy()
    R = Matrix.Rotation(math.radians(deg), 4, axis)
    pb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M)


def legs(angles_L, angles_R):
    bpy.context.view_layer.update()
    pel = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
    lat = (pel.to_3x3() @ (rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0)))).normalized()
    for s, ang in (('L', angles_L), ('R', angles_R)):
        for n in LEG[s]:
            rig.pose.bones[n].matrix_basis = Matrix()
        for n, a in zip(LEG[s], ang):
            rot_world(rig.pose.bones[n], a, lat)


def lowest():
    bpy.context.view_layer.update(); deps.update()
    ev = body.evaluated_get(deps); m = ev.to_mesh()
    z = min((body.matrix_world @ v.co).z for v in m.vertices); ev.to_mesh_clear()
    return z


TAILV = None
if 'B_Tail' in body.vertex_groups:
    gi_ = body.vertex_groups['B_Tail'].index
    TAILV = np.array([v.index for v in body.data.vertices if any(g.group == gi_ and g.weight > 0.5 for g in v.groups)])


def _zs():
    bpy.context.view_layer.update(); deps.update()
    ev = body.evaluated_get(deps); m = ev.to_mesh()
    z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear()
    return z


def tail_low():
    return float(_zs()[TAILV].min())


def body_low_no_tail():
    z = _zs(); m = np.ones(len(z), bool); m[TAILV] = False
    return float(z[m].min())


def lift(pb, dz):
    up = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, 0, dz))
    pb.location = pb.location + up


def ss(t):
    t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)


def mix(a, b, t):
    return [x + (y - x) * t for x, y in zip(a, b)]


# ---------------------------------------------------------------- 1. Walking = flight over Standing frame 0
set_act(bpy.data.actions['Standing']); scene.frame_set(0)
stand = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
set_act(None)


def flight_pose(t):
    ph = 2 * math.pi * t
    for pb in rig.pose.bones:
        pb.matrix_basis = stand[pb.name].copy()
    pel = rig.pose.bones['B_Pelvis']
    rot_world(pel, PITCH + 2 * math.sin(ph), Vector((1, 0, 0)))
    for n in ('B_Spine1', 'B_Spine2'):
        rot_world(rig.pose.bones[n], -PITCH * 0.25, Vector((1, 0, 0)))
    rot_world(rig.pose.bones['B_Neck'], -PITCH * 0.3, Vector((1, 0, 0)))
    # left arm forward and bent before the body (native flight frames), with a small pump on the beat
    rot_world(rig.pose.bones['B_L_UpperArm'], -50 - 4 * math.sin(ph), Vector((1, 0, 0)))
    rot_world(rig.pose.bones['B_L_Forearm'], -45, Vector((1, 0, 0)))
    if 'B_Tail' in rig.pose.bones:
        rig.pose.bones['B_Tail'].matrix_basis = Matrix()
        rot_world(rig.pose.bones['B_Tail'], 6 * math.sin(ph + 1.0), Vector((1, 0, 0)))
    k = KICK * math.sin(ph)
    legs([TUCK[0] + k, TUCK[1] + k, TUCK[2], TUCK[3]], [TUCK[0] - k, TUCK[1] - k, TUCK[2], TUCK[3]])


lows = []
for i in range(N):
    flight_pose(i / N); lows.append(lowest())
LIFT = CLEAR - min(lows)
act = bpy.data.actions.new('Walking_flight'); act.use_fake_user = True
set_act(act)
for i in range(N + 1):
    t = (i % N) / N
    flight_pose(t)
    lift(rig.pose.bones['B_Pelvis'], LIFT + BOB * math.sin(2 * math.pi * t))
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.keyframe_insert('rotation_quaternion', frame=i)
        if pb.name == 'B_Pelvis':
            pb.keyframe_insert('location', frame=i)
set_act(None)
old = bpy.data.actions.get('Walking')
if old is not None:
    old.name = 'Walking_mixamo'
act.name = 'Walking'
print('HOVER Walking flight frames', N + 1, 'lift cm', round(LIFT * 100, 1))


# ---------------------------------------------------------------- 2./3. bird legs on the one-shot clips
def rewrite(name, leg_fn, hover=True):
    act = bpy.data.actions[name]; set_act(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    poses = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        t = (f - f0) / FPS
        aL, aR = leg_fn(t, (f1 - f0) / FPS)
        legs(aL, aR)
        if name == 'Death' and 'B_Tail' in rig.pose.bones:     # fold the tail up until it clears the floor
            tb = rig.pose.bones['B_Tail']; tb.matrix_basis = Matrix()
            bpy.context.view_layer.update()
            pelm = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
            lat = (pelm.to_3x3() @ (rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0)))).normalized()
            best = None
            for ang in range(0, 181, 15):
                for sg in (1, -1):
                    tb.matrix_basis = Matrix(); rot_world(tb, sg * ang, lat)
                    zt = tail_low()
                    if zt >= body_low_no_tail() - 0.02:
                        best = (sg * ang); break
                if best is not None:
                    break
            tb.matrix_basis = Matrix()
            if best:
                rot_world(tb, best, lat)
        poses.append({pb.name: (pb.matrix_basis.copy()) for pb in rig.pose.bones})
    # height
    zs = []
    for p in poses:
        for n, m in p.items():
            rig.pose.bones[n].matrix_basis = m
        zs.append(lowest())
    zs = np.array(zs)
    if hover:
        # the clip's own vertical pelvis motion is kept relative to its first frame; one constant lift per clip
        dz = np.full(len(zs), CLEAR - zs.min())
    else:
        # death: before the fall only lift what dips under the floor; from the fall on, settle the lowest vertex on
        # the floor (the chain's floor pass had lifted the whole fall over the old pelvis-rigid tail)
        wf = np.array([ss((i - FALL0) / 12.0) for i in range(len(zs))])
        dz = np.maximum(0.0, 0.01 - zs) * (1 - wf) + (0.01 - zs) * wf
        dz = np.convolve(np.pad(dz, 2, mode='edge'), np.ones(5) / 5, 'valid')
        dz = np.maximum(dz, 0.01 - zs)
    for i, (f, p) in enumerate(zip(range(f0, f1 + 1), poses)):
        for n, m in p.items():
            pb = rig.pose.bones[n]; pb.matrix_basis = m
        lift(rig.pose.bones['B_Pelvis'], float(dz[i]))
        for n in LEG['L'] + LEG['R'] + ['B_Pelvis'] + (['B_Tail'] if 'B_Tail' in rig.pose.bones else []):
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            pb.keyframe_insert('rotation_quaternion', frame=f)
            if n == 'B_Pelvis':
                pb.keyframe_insert('location', frame=f)
    set_act(None)
    print('HOVER', name, 'frames', f1 - f0 + 1, 'lift cm', round(float(dz.min()) * 100, 1), '..', round(float(dz.max()) * 100, 1), 'last', round(float(dz[-1]) * 100, 1))


def attack_legs(t, T):
    w = ss((t - (IMPACT - 0.45)) / 0.4) * (1 - ss((t - (IMPACT + 0.15)) / 0.45))
    a = mix(TUCK, TALON, w)
    return a, a


def hit_legs(t, T):
    w = ss(t / 0.15) * (1 - ss((t - 0.2) / 0.3))
    a = mix(TUCK, [TUCK[0] + 15, TUCK[1] + 10, TUCK[2], TUCK[3] + 10], w)
    return a, a


death = bpy.data.actions['Death']; set_act(death)
pz = []
for f in range(int(death.frame_range[0]), int(death.frame_range[1]) + 1):
    scene.frame_set(f); pz.append((rig.matrix_world @ rig.pose.bones['B_Pelvis'].head).z)
pz = np.array(pz); FALL0 = int(np.argmax(pz < pz[0] - 0.15)) if (pz < pz[0] - 0.15).any() else len(pz) // 3
set_act(None)


def death_legs(t, T):
    w = ss((t * FPS - FALL0) / max(len(pz) - FALL0 - 6, 1))
    a = mix(TUCK, UP, w)
    return a, a


rewrite('Attack', attack_legs)
rewrite('Hit', hit_legs)
rewrite('Death', death_legs, hover=False)
print('HOVER death legs up from frame', FALL0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
