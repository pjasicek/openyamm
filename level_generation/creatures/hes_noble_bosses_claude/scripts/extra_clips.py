"""Extra clips on the Noble rig, authored over the accepted Overseer clips (imported by assemble.py).

wing_spread(rig, scene): Noble_WingSpread, 1.5 s: the Cast's arms with the wings eased into the Flight clip's widest
    spread (0.35 s), held, eased back (1.15-1.5 s). The Hierarch's storm telegraph (perform clip 'wing_spread').
seated(rig, scene): the enthroned Hierarch (10145): Noble_Seated (4 s loop: breathing, a slow wing sway),
    Noble_SeatedCast (1.2 s: the right palm raised toward the party, release at 0.45 s) and Noble_SeatedHit (0.5 s).
    Pose by world bone directions (swing only, parents first); the pelvis lowered so the soles stay on the floor.
Clips are keyed at 24 frames per second (the rig's scene rate) on every bone."""
import math
import bpy
from mathutils import Vector, Quaternion, Matrix

FPS = 24


def _bones(rig):
    return [pb.name for pb in rig.pose.bones]


def _set_action(rig, act):
    rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]


def _sample(rig, scene, act, t):
    _set_action(rig, act)
    f = t * FPS
    scene.frame_set(int(math.floor(f)), subframe=f % 1)
    return {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}


def _key(rig, act, frame, pose, previous):
    _set_action(rig, act)
    for name, M in pose.items():
        pb = rig.pose.bones[name]
        loc, q, sc = M.decompose()
        if name in previous and q.dot(previous[name]) < 0:
            q.negate()
        previous[name] = q.copy()
        pb.rotation_mode = 'QUATERNION'; pb.location = loc; pb.rotation_quaternion = q; pb.scale = sc
        for path in ('location', 'rotation_quaternion', 'scale'):
            pb.keyframe_insert(path, frame=frame)


def _blend(a, b, w):
    la, qa, sa = a.decompose(); lb, qb, sb = b.decompose()
    return Matrix.LocRotScale(la.lerp(lb, w), qa.slerp(qb, w), sa.lerp(sb, w))


def _ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def _new(name, seconds):
    act = bpy.data.actions.new(name); act.use_fake_user = True
    act.use_frame_range = True; act.frame_start = 0; act.frame_end = seconds * FPS
    return act


def _span(rig):
    pts = {}
    for side in 'LR':
        pts[side] = [rig.matrix_world @ rig.pose.bones[f'B_Wing_{side}_{n}'].tail for n in ('Finger1', 'Finger2', 'Lead')]
    return max((a - b).length for a in pts['L'] for b in pts['R'])


def spread_pose(rig, scene, flight, amount=1.0):
    best = None
    for k in range(int(flight.frame_range[1]) + 1):
        pose = _sample(rig, scene, flight, k / FPS)
        bpy.context.view_layer.update()
        s = _span(rig)
        if best is None or s > best[0]:
            best = (s, pose)
    return {n: M for n, M in best[1].items() if n.startswith('B_Wing_')}


def wing_spread(rig, scene, prefix='Noble'):
    cast = bpy.data.actions[f'{prefix}_Cast']; flight = bpy.data.actions[f'{prefix}_Flight']
    spread = spread_pose(rig, scene, flight)
    dur = 1.5; cast_dur = cast.frame_range[1] / FPS
    act = _new(f'{prefix}_WingSpread', dur); prev = {}
    for k in range(int(dur * FPS) + 1):
        t = k / FPS
        pose = _sample(rig, scene, cast, min(t * cast_dur / dur, cast_dur))
        w = _ease(t / 0.35) * (1 - _ease((t - 1.15) / 0.35))
        for n, M in spread.items():
            pose[n] = _blend(pose[n], M, w)
        _key(rig, act, k, pose, prev)
    rig.animation_data.action = None
    return act


def _aim(rig, name, direction):
    pb = rig.pose.bones[name]
    M = rig.matrix_world @ pb.matrix
    cur = Vector(M.col[1][:3]).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    R = (q.to_matrix() @ M.to_3x3()).to_4x4(); R.translation = M.translation
    pb.matrix = rig.matrix_world.inverted() @ R
    bpy.context.view_layer.update()


def _keep_world(rig, name, world_rot):
    pb = rig.pose.bones[name]; M = rig.matrix_world @ pb.matrix
    R = world_rot.to_4x4(); R.translation = M.translation
    pb.matrix = rig.matrix_world.inverted() @ R
    bpy.context.view_layer.update()


def seated_pose(rig, scene, flight, drop=0.36, lean=0.0, arm_raise=0.0, wings=None, wing_amount=0.6):
    """Pose dict (matrix_basis per bone) of the enthroned Hierarch."""
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    rest_world = {pb.name: (rig.matrix_world @ pb.matrix).to_3x3().normalized() for pb in rig.pose.bones}
    pel = rig.pose.bones['B_Pelvis']
    M = rig.matrix_world @ pel.matrix
    M.translation.z -= drop
    pel.matrix = rig.matrix_world.inverted() @ M
    bpy.context.view_layer.update()
    for side, sx in (('L', 1), ('R', -1)):
        _aim(rig, f'B_{side}_Thigh', (0.18 * sx, -1.0, 0.04))
        _aim(rig, f'B_{side}_Calf', (0.06 * sx, -0.12, -1.0))
        _keep_world(rig, f'B_{side}_Foot', rest_world[f'B_{side}_Foot'])
        _keep_world(rig, f'B_{side}_Toe0', rest_world[f'B_{side}_Toe0'])
    # trunk leaning back into the backrest, head level toward the party
    for name, ang in (('B_Spine', 4 + lean), ('B_Spine1', 4 + lean), ('B_Spine2', 3 + lean)):
        pb = rig.pose.bones[name]
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion((1, 0, 0), math.radians(-ang))
        bpy.context.view_layer.update()
    _keep_world(rig, 'B_Head', rest_world['B_Head'])
    # arms on the armrests: upper arm down and a little forward, forearm forward along the rest, hand over the claw
    for side, sx in (('L', 1), ('R', -1)):
        raise_ = arm_raise if side == 'R' else 0.0
        up = Vector((0.22 * sx, -0.30, -0.93)).lerp(Vector((0.25 * sx, -0.85, 0.45)), raise_)
        fore = Vector((0.08 * sx, -1.0, -0.06)).lerp(Vector((0.12 * sx, -0.95, 0.35)), raise_)
        hand = Vector((0.05 * sx, -0.75, -0.65)).lerp(Vector((0.05 * sx, -0.6, 0.8)), raise_)
        _aim(rig, f'B_{side}_UpperArm', up)
        _aim(rig, f'B_{side}_Forearm', fore)
        _aim(rig, f'B_{side}_Hand', hand)
    pose = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    if wings:
        for n, Mw in wings.items():
            pose[n] = _blend(Matrix.Identity(4), Mw, wing_amount)
    return pose


def seated(rig, scene, prefix='Noble'):
    flight = bpy.data.actions[f'{prefix}_Flight']
    spread = spread_pose(rig, scene, flight)
    base = seated_pose(rig, scene, flight, wings=spread)
    # idle: breathing in the spine, a slow wing sway taken from the flight cycle at a fifth of its amplitude
    act = _new(f'{prefix}_Seated', 4.0); prev = {}
    for k in range(int(4.0 * FPS) + 1):
        t = k / FPS; breath = math.sin(2 * math.pi * t / 4.0)
        pose = seated_pose(rig, scene, flight, lean=1.5 * breath, wings=spread)
        fl = _sample(rig, scene, flight, (t * 0.75) % (flight.frame_range[1] / FPS))
        for n in pose:
            if n.startswith('B_Wing_'):
                pose[n] = _blend(pose[n], fl[n], 0.12)
        _key(rig, act, k, pose, prev)
    cast = _new(f'{prefix}_SeatedCast', 1.2); prev = {}
    for k in range(int(1.2 * FPS) + 1):
        t = k / FPS
        r = _ease(t / 0.35) * (1 - _ease((t - 0.7) / 0.5))
        pose = seated_pose(rig, scene, flight, lean=-4 * r, arm_raise=r, wings=spread, wing_amount=0.6 + 0.4 * r)
        _key(rig, cast, k, pose, prev)
    hit = _new(f'{prefix}_SeatedHit', 0.5); prev = {}
    for k in range(int(0.5 * FPS) + 1):
        t = k / FPS
        r = math.sin(math.pi * min(t / 0.5, 1.0))
        pose = seated_pose(rig, scene, flight, lean=6 * r, wings=spread)
        _key(rig, hit, k, pose, prev)
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    return act, cast, hit
