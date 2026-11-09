"""Move the goblin onto Meshy's auto-rig (rig_v1 job): Meshy joint placement and skin weights for the body, our
extras on top (finger chains + finger weights, forearm twist bones, Sword/Tip bones, palm sockets).

Bone names stay ours (mixamorig:*), so engine bindings, sockets and scripts keep working.
  1. sample every existing clip as world-space bone rotations (+ hips position),
  2. edit-bone the 22 mapped bones onto Meshy's joints/axes (fingers, sword and sockets keep their world rest),
  3. weights: each non-sword vertex outside the hands takes the weights of the nearest vertex of Meshy's skinned
     mesh (same base mesh); hand/finger vertices keep ours; forearm weight is re-split onto the twist bones,
  4. existing clips are re-applied as world rotations; Meshy library clips (anim_lib_v1) and Meshy walk/run
     (rig_v1) are applied directly from Meshy's skeleton (identical joints, so no retarget loss).
Run on work/final_v1.blend; saves work/meshy_rig.blend.
"""
import bpy, os, sys, json, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
rig = bpy.data.objects['Peasant_Rig']; mesh = bpy.data.objects['Peasant']; me = mesh.data
scene = bpy.context.scene
MAP = {'Hips': 'Hips', 'Spine02': 'Spine', 'Spine01': 'Spine1', 'Spine': 'Spine2', 'neck': 'Neck', 'Head': 'Head'}
for side in ('Left', 'Right'):
    for b in ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg', 'Foot', 'ToeBase'):
        MAP[side + b] = side + b
MAP_FULL = {k: 'mixamorig:' + v for k, v in MAP.items()}
ORDER = [b.name for b in rig.data.bones]                 # parents first


def norm(m):
    loc, rot, _ = m.decompose()
    return Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))


# ---------------------------------------------------------------- 1. sample existing clips (world space)
def sample_action(arm_obj, action, names):
    arm_obj.animation_data.action = action
    f0, f1 = (int(round(x)) for x in action.frame_range)
    frames = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        frames.append({n: norm(arm_obj.matrix_world @ arm_obj.pose.bones[n].matrix) for n in names})
    return frames


old_names = [b.name for b in rig.pose.bones]
OLD_CLIPS = {}
for act in list(bpy.data.actions):
    if act.name in ('Standing', 'Fidget', 'Attack', 'Cast_FireBolt', 'Hit', 'Death', 'Dead'):
        OLD_CLIPS[act.name] = (sample_action(rig, act, old_names), bool(act.get('loop', act.name == 'Standing')))
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
OLD_REST = {b.name: (rig.matrix_world @ b.matrix_local).to_quaternion() for b in rig.data.bones}
print('SAMPLED', {k: len(v[0]) for k, v in OLD_CLIPS.items()})

# ---------------------------------------------------------------- Meshy rig + clips
before = set(bpy.data.objects); before_act = set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/anim_lib_v1/result_animation_glb_url.glb'))
lib_objs = [o for o in bpy.data.objects if o not in before]
marm = next(o for o in lib_objs if o.type == 'ARMATURE')
mmesh = max((o for o in lib_objs if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
lib_actions = [a for a in bpy.data.actions if a not in before_act]
loco = {}
for src, name in (('walking', 'Walking'), ('running', 'Running')):
    b2 = set(bpy.data.objects); ba = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, f'meshy/rig_v1/result_basic_animations_{src}_glb_url.glb'))
    objs = [o for o in bpy.data.objects if o not in b2]
    arm2 = next(o for o in objs if o.type == 'ARMATURE')
    act = next(a for a in bpy.data.actions if a not in ba)
    loco[name] = sample_action(arm2, act, list(MAP))
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
LIB = {}
NAMES = {'Right_Hand_Sword_Slash': 'M_SwordSlash', 'Charged_Upward_Slash': 'M_UpwardSlash', 'Charged_Slash': 'M_ChargedSlash',
         'Hit_Reaction_1': 'M_HitGuard', 'Hit_Reaction': 'M_Hit', 'Shot_and_Fall_Forward': 'M_DeathForward',
         'dying_backwards': 'M_DeathBackward', 'mage_soell_cast': 'M_Cast'}
for a in lib_actions:
    if a.name in NAMES:
        LIB[NAMES[a.name]] = sample_action(marm, a, list(MAP))
marm.animation_data.action = None
for b in marm.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
print('MESHY CLIPS', {k: len(v) for k, v in LIB.items()}, {k: len(v) for k, v in loco.items()})

# ---------------------------------------------------------------- 2. move bones onto Meshy joints
inv = rig.matrix_world.inverted()
mw = marm.matrix_world
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
sock_world = {o.name: o.matrix_world.copy() for o in bpy.data.objects if o.name.startswith('Socket_')}
for mname, ours in MAP_FULL.items():
    mb = marm.data.bones[mname]
    m = mw @ mb.matrix_local
    head = mw @ mb.head_local; tail = mw @ mb.tail_local
    e = eb[ours]
    e.use_connect = False
    e.head = inv @ head; e.tail = inv @ tail
    e.align_roll(inv.to_3x3() @ (m.to_3x3() @ Vector((0, 0, 1))).normalized())
for side in ('Left', 'Right'):
    fa = eb[f'mixamorig:{side}ForeArm']
    for k, (t0, t1) in ((1, (0.35, 0.6)), (2, (0.7, 0.95))):
        tb = eb[f'{side}ForeArmTwist{k}']
        tb.head = fa.head.lerp(fa.tail, t0); tb.tail = fa.head.lerp(fa.tail, t1); tb.roll = fa.roll
bpy.ops.object.mode_set(mode='OBJECT')
for n, m in sock_world.items():
    o = bpy.data.objects[n]; o.matrix_world = m
print('BONES moved')

# ---------------------------------------------------------------- 3. weights
PARTS = json.loads(scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
vpart = np.full(len(me.vertices), -1)
for p in me.polygons:
    vpart[list(p.vertices)] = part[p.index]
mnames = [g.name for g in mmesh.vertex_groups]
mco = [mmesh.matrix_world @ v.co for v in mmesh.data.vertices]
kd = KDTree(len(mco))
for i, c in enumerate(mco):
    kd.insert(c, i)
kd.balance()
names = [g.name for g in mesh.vertex_groups]
HAND = lambda n: ('Hand' in n) and 'mixamorig:' in n
moved = kept = 0
for v in me.vertices:
    if vpart[v.index] == PARTS.index('Sword'):
        continue
    cur = {names[g.group]: g.weight for g in v.groups}
    if sum(w for n, w in cur.items() if HAND(n)) > 0.3:
        kept += 1
        continue
    _, i, d = kd.find(mesh.matrix_world @ v.co)
    if d > 0.02:
        kept += 1
        continue
    new_w = {}
    for g in mmesh.data.vertices[i].groups:
        n = mnames[g.group]
        n = 'Head' if n in ('head_end', 'headfront') else n
        if n in MAP_FULL and g.weight > 1e-4:
            new_w[MAP_FULL[n]] = new_w.get(MAP_FULL[n], 0) + g.weight
    if not new_w:
        kept += 1
        continue
    for g in list(v.groups):
        mesh.vertex_groups[g.group].remove([v.index])
    for n, w in new_w.items():
        (mesh.vertex_groups.get(n) or mesh.vertex_groups.new(name=n)).add([v.index], w, 'REPLACE')
    moved += 1
# forearm weight -> twist bones (same tents as twist_bones.py setup)
groups = {g.name: g for g in mesh.vertex_groups}
for side in ('Left', 'Right'):
    bone = rig.data.bones[f'mixamorig:{side}ForeArm']
    head = rig.matrix_world @ bone.head_local; tail = rig.matrix_world @ bone.tail_local
    axis = tail - head; L = axis.length; axis.normalize()
    fa_g = groups[f'mixamorig:{side}ForeArm']; t_g = {k: groups[f'{side}ForeArmTwist{k}'] for k in (1, 2)}
    for v in me.vertices:
        w = next((g.weight for g in v.groups if g.group == fa_g.index), 0.0)
        if w <= 0:
            continue
        t = (mesh.matrix_world @ v.co - head).dot(axis) / L
        w1 = max(0.0, 1.0 - abs(t - 0.5) / 0.3)
        w2 = max(0.0, 1.0 - abs(t - 0.9) / 0.3) if t < 0.9 else 1.0
        w0 = max(0.0, 1.0 - t / 0.35)
        s = w0 + w1 + w2
        if s <= 0:
            continue
        fa_g.add([v.index], w * w0 / s, 'REPLACE')
        for k, wk in ((1, w1), (2, w2)):
            if wk > 0:
                prev = next((g.weight for g in v.groups if g.group == t_g[k].index), 0.0)
                t_g[k].add([v.index], prev + w * wk / s, 'REPLACE')
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
print('WEIGHTS meshy', moved, 'kept ours', kept)

# ---------------------------------------------------------------- 4. clips
for a in list(bpy.data.actions):
    if a.name in OLD_CLIPS or a.name in ('Walking', 'Running') or a.name.startswith('M_') or a in lib_actions:
        bpy.data.actions.remove(a)
for o in lib_objs:
    if o.name in bpy.data.objects:
        bpy.data.objects.remove(o, do_unlink=True)
import author_clips as A                                  # imported now: rest frames measured on the new rig
import posing as P
rig.animation_data_create()


def apply_world(frame_mats, names, hips_name, old_rest=None):
    """Pose each bone from source world matrices. With old_rest (a different rest skeleton), the source rotation
    is taken relative to the old rest and re-applied relative to the new rest (delta transfer)."""
    rig.animation_data.action = None
    P.reset(rig)
    new_rest = {b.name: (rig.matrix_world @ b.matrix_local).to_quaternion() for b in rig.data.bones}
    for n in ORDER:
        if n not in names:
            continue
        pb = rig.pose.bones[n]
        src = frame_mats[names[n]]
        q = src.to_quaternion()
        if old_rest is not None:
            q = (q @ old_rest[names[n]].inverted()) @ new_rest[n]
        q = rig.matrix_world.to_quaternion().inverted() @ q
        head = (inv @ src.translation) if n == hips_name else pb.head.copy()
        pb.matrix = Matrix.LocRotScale(head, q, Vector((1, 1, 1)))
        bpy.context.view_layer.update()


def build(name, frames, names, loop, sword_fix, old_rest=None):
    out = []
    A.PREV_WRIST.clear()
    for k, fm in enumerate(frames):
        apply_world(fm, names, 'mixamorig:Hips', old_rest)
        if sword_fix:
            for side in ('Left', 'Right'):
                for b in rig.pose.bones:
                    if b.name.startswith(f'mixamorig:{side}Hand') and b.name != f'mixamorig:{side}Hand':
                        b.rotation_quaternion = (1, 0, 0, 0)
            bpy.context.view_layer.update()
            for side in ('Left', 'Right'):
                A.limit_wrist(side)
            P.curl_hand(rig, 'Right', 80, thumb=35)
            A.wrap_grip('Right'); A.wrap_thumb('Right')
            P.curl_hand(rig, 'Left', 30, thumb=12)
        for side in ('Left', 'Right'):
            A.PREV_WRIST[side] = A.wrist_relative(side)
        out.append((k + 1, A.capture()))
    A.PREV_WRIST.clear()
    A.write_action(name, out, loop=loop)
    print('CLIP', name, len(frames))


same = {n: n for n in old_names}
for name, (frames, loop) in OLD_CLIPS.items():
    build(name, frames, same, loop, sword_fix=False, old_rest=OLD_REST)
for name, frames in loco.items():
    build(name, frames, {MAP_FULL[k]: k for k in MAP}, True, sword_fix=True)
for name, frames in LIB.items():
    build(name, frames, {MAP_FULL[k]: k for k in MAP}, False, sword_fix=True)
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'meshy_rig.blend'))
print('SAVED meshy_rig.blend')
