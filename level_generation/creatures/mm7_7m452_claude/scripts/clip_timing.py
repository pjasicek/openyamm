"""m302 clip timing (peasant: no attack; playbook "Clip timing"; trimmed from mm7_m190_claude's m222 version):
<in blend> -> <out blend>.
- Stance blends: Hit, Death and Fidget ease in from (and Hit/Fidget out to) the Standing pose (smoothstep per bone);
  the engine crossfades only 0.06-0.12 s (the death not at all).
- natm's death travel halving and a floor pass per frame for the hit, fidget and death (lowest sole; the whole body
  for the death); the walk gets one constant pelvis lift centring the lowest sole's range on the floor.
"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Quaternion, Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
LEAD = float(os.environ.get('LEAD', '0.15'))   # ready pause before the source attack (set from the native wind-up)
TWIST_FREE, TWIST_MAX = math.radians(25), math.radians(45)
SPINE = ('B_Spine', 'B_Spine1', 'B_Spine2')
SRC_BLEND, OUT_BLEND = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC_BLEND))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']
names = [b.name for b in rig.data.bones]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def sample(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def segment_axis(j, child):
    b, c = rig.data.bones[j], rig.data.bones[child]
    return (b.matrix_local.to_3x3().inverted() @ (c.head_local - b.head_local)).normalized()


TWIST_AXES = {'B_Spine': segment_axis('B_Spine', 'B_Spine1'), 'B_Spine1': segment_axis('B_Spine1', 'B_Spine2'),
              'B_Spine2': segment_axis('B_Spine2', 'B_Neck'), 'B_Neck': segment_axis('B_Neck', 'B_Head')}


def split_twist(q, axis):
    """q = swing @ twist about the bone-local axis; returns (swing, twist angle)."""
    t = 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(axis), q.w)
    t = (t + math.pi) % (2 * math.pi) - math.pi
    return q @ Quaternion(axis, t).inverted(), t


def limit_spine_twist(pose):
    parts = {j: split_twist(pose[j][0], TWIST_AXES[j]) for j in TWIST_AXES}
    total = sum(parts[j][1] for j in SPINE)
    if abs(total) <= TWIST_FREE:
        return pose, total, total
    span = TWIST_MAX - TWIST_FREE
    limited = math.copysign(TWIST_FREE + span * math.tanh((abs(total) - TWIST_FREE) / span), total)
    k = limited / total
    for j in SPINE:
        swing, t = parts[j]; pose[j] = (swing @ Quaternion(TWIST_AXES[j], t * k), pose[j][1])
    swing, t = parts['B_Neck']; pose['B_Neck'] = (swing @ Quaternion(TWIST_AXES['B_Neck'], t + total - limited),
                                                  pose['B_Neck'][1])
    return pose, total, limited


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def write(name, frames):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; set_act(act)
    prev = {}
    for i, pose in enumerate(frames):
        for n, (q, l) in pose.items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            if n in prev and q.dot(prev[n]) < 0:
                q = -q
            prev[n] = q
            pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == 'B_Pelvis':
                pb.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(frames) - 1
    set_act(None)
    return act


# ---------------------------------------------------------------- stance blends from/to Standing
BLEND_IN = {'Hit': 0.20, 'Death': 0.25, 'Fidget': 0.30}
BLEND_OUT = {'Hit': 0.20, 'Fidget': 0.30}


def blend_ends(name, frames_or_act):
    st_pose = sample(bpy.data.actions['Standing'], 0)
    if isinstance(frames_or_act, list):
        poses = frames_or_act
    else:
        poses = [sample(frames_or_act, f) for f in range(int(frames_or_act.frame_range[1]) + 1)]
    n = len(poses); fi, fo = BLEND_IN.get(name, 0) * FPS, BLEND_OUT.get(name, 0) * FPS
    out = []
    for i, pose in enumerate(poses):
        w = 1.0
        if fi:
            w = min(w, smooth(i / fi))
        if fo:
            w = min(w, smooth((n - 1 - i) / fo))
        out.append({k: (st_pose[k][0].slerp(q, w) if q.dot(st_pose[k][0]) >= 0 else (-st_pose[k][0]).slerp(q, w),
                        st_pose[k][1].lerp(l, w)) for k, (q, l) in pose.items()})
    return out


for nm in ('Hit', 'Death', 'Fidget'):
    write(nm, blend_ends(nm, bpy.data.actions[nm]))
print('BLENDS in', BLEND_IN, 'out', BLEND_OUT)

# ---------------------------------------------------------------- natm: death travel, toes, floor pass
DEATH_TRAVEL = 0.5
death = bpy.data.actions['Death']; nd = int(death.frame_range[1]) + 1
res = [sample(death, f) for f in range(nd)]
set_act(None); W0 = None
for k, p in enumerate(res):
    for b_, (q, l) in p.items():
        pb = rig.pose.bones[b_]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
    bpy.context.view_layer.update()
    M = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
    if W0 is None:
        W0 = M.translation.copy()
    t = M.translation.copy(); t.x = W0.x + (t.x - W0.x) * DEATH_TRAVEL; t.y = W0.y + (t.y - W0.y) * DEATH_TRAVEL
    M.translation = t; rig.pose.bones['B_Pelvis'].matrix = rig.matrix_world.inverted() @ M
    bpy.context.view_layer.update()
    res[k]['B_Pelvis'] = (rig.pose.bones['B_Pelvis'].rotation_quaternion.copy(), rig.pose.bones['B_Pelvis'].location.copy())
write('Death', res)
body = bpy.data.objects['Body']; me = body.data; vg = [g.name for g in body.vertex_groups]
FEETV = np.array([sum(e.weight for e in v.groups if vg[e.group] in ('B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0')) > 0.5 for v in me.vertices])
gk2 = np.exp(-0.5 * (np.arange(-4, 5) / 0.8) ** 2); gk2 /= gk2.sum()
for name in ('Hit', 'Fidget', 'Death'):
    act = bpy.data.actions[name]; n = int(act.frame_range[1]) + 1; lows = []
    for f in range(n):
        set_act(act); scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear()
        lows.append(z.min() if name == 'Death' else z[FEETV].min())
    lows = np.array(lows); pad = np.concatenate([np.repeat(lows[:1], 4), lows, np.repeat(lows[-1:], 4)])
    dz = -np.convolve(pad, gk2, 'valid')
    poses = [sample(act, f) for f in range(n)]
    for f, p_ in enumerate(poses):
        set_act(None)
        for b_, (q, l) in p_.items():
            pb = rig.pose.bones[b_]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
        bpy.context.view_layer.update()
        M = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix; M.translation.z += float(dz[f])
        rig.pose.bones['B_Pelvis'].matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
        p_['B_Pelvis'] = (rig.pose.bones['B_Pelvis'].rotation_quaternion.copy(), rig.pose.bones['B_Pelvis'].location.copy())
    write(name, poses)
    print(f'TIMING floor {name}: lowest point before {lows.min() * 100:.1f}..{lows.max() * 100:.1f} cm, pelvis shift {dz.min() * 100:.1f}..{dz.max() * 100:.1f} cm')
# walk: one constant pelvis lift that centres the lowest sole's range on the floor (Mixamo walks sank 2.5-3.2 cm)
act = bpy.data.actions['Walking']; n = int(act.frame_range[1]) + 1; lows = []
for f in range(n):
    set_act(act); scene.frame_set(f)
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear(); lows.append(z[FEETV].min())
lift = -(min(lows) + max(lows)) / 2
poses = [sample(act, f) for f in range(n)]
for p_ in poses:
    set_act(None)
    for b_, (q, l) in p_.items():
        pb = rig.pose.bones[b_]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
    bpy.context.view_layer.update()
    M = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix; M.translation.z += lift
    rig.pose.bones['B_Pelvis'].matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
    p_['B_Pelvis'] = (rig.pose.bones['B_Pelvis'].rotation_quaternion.copy(), rig.pose.bones['B_Pelvis'].location.copy())
write('Walking', poses)
print(f'TIMING floor Walking: lowest sole {min(lows) * 100:.1f}..{max(lows) * 100:.1f} cm, constant lift {lift * 100:.1f} cm')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT_BLEND))
