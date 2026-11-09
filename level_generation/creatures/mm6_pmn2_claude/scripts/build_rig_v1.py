"""Rigged master from the user's Meshy auto-rig (meshy/rig_manual_v1_anims2/model.glb, 1.7 m; same rig as rig_manual_v1) and our UV'd mesh
(work/step1_uv.blend, 1.578 m, identical topology). Saves work/rig_v1.blend.
 1. our mesh is scaled to Meshy's 1.7 m and takes Meshy's skin weights vertex-for-vertex (nearest position, ~0 mm),
 2. each fist shell is rigid on its Hand bone (Meshy spread it over thumb/middle chains it animates and three finger
    chains parented to the forearm, which tore the fists), at most 4 influences elsewhere,
 3. feet: Meshy's clips carry the source body's foot posture (soles ~15 deg rolled and pitched while standing). Per
    frame the Foot bone is rotated about the ankle so the sole lies flat while it is on the ground: roll fades out
    between 4 and 12 cm sole height, pitch between 1.5 and 5 cm (heel strike/toe-off keep their pitch). Deaths are
    left alone. Original clips are kept with a '_src' suffix.
 5. wrists: the clips bend the source body's relaxed open hand 45-60 deg even at idle (up to 87 in the run, +-25
    twist); on a fist that reads as a broken wrist. Hand rotation relative to the forearm is kept at 25 % and the bend
    capped at 25 deg (all clips, death included).
 6. shoulders: clavicles kept within 6 deg of their rest elevation (Meshy's idle shrugs them ~33 deg); the upper
    arm keeps its world orientation, so lowering the clavicle does not swing the hanging arm into the torso.
 4. clips whose lowest grounded sole is more than 5 mm off the floor (Meshy's idle sinks ~4 cm) get a constant Hips
    height offset so the lowest sole point over the clip sits at z=0."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.read_factory_settings(use_empty=True)
SRC = os.environ.get('PMN2_RIG_SRC', 'meshy/rig_manual_v1_anims2/model.glb')      # same rig, more clips than rig_manual_v1
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, SRC))
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Mage':
        bpy.data.objects.remove(o, do_unlink=True)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); arm.name = 'Mage_Rig'
src = bpy.data.objects['Mage']; src.name = 'MeshyMage'
with bpy.data.libraries.load(os.path.join(common.WORK, 'step1_uv.blend')) as (df, dt):
    dt.objects = ['Mage']
mesh = dt.objects[0]; bpy.context.scene.collection.objects.link(mesh)
scene = bpy.context.scene
PARTS = json.loads(bpy.data.scenes[0].get('pmn2_parts') or '[]')
if not PARTS:                                        # scene props live in the library scene, not appended
    with bpy.data.libraries.load(os.path.join(common.WORK, 'step1_uv.blend')) as (df, dt):
        dt.scenes = df.scenes[:1]
    lib = dt.scenes[0]
    for k in ('pmn2_parts', 'pmn2_eyes', 'pmn2_uv_regions'):
        scene[k] = lib[k]
    PARTS = json.loads(scene['pmn2_parts'])
    bpy.data.scenes.remove(lib)

# 1. scale + weights
sc = 1.7 / 1.578
me = mesh.data
for v in me.vertices:
    v.co *= sc
me.update()
sco = [src.matrix_world @ v.co for v in src.data.vertices]
kd = KDTree(len(sco))
for i, p in enumerate(sco):
    kd.insert(p, i)
kd.balance()
gname = {g.index: g.name for g in src.vertex_groups}
for g in src.vertex_groups:
    mesh.vertex_groups.new(name=g.name)
dmax = 0.0
for v in me.vertices:
    p, j, d = kd.find(mesh.matrix_world @ v.co); dmax = max(dmax, d)
    for g in src.data.vertices[j].groups:
        mesh.vertex_groups[gname[g.group]].add([v.index], g.weight, 'REPLACE')
print('WEIGHT_COPY max distance', round(dmax * 1000, 3), 'mm')

# 2. rigid fists, then <=4 influences, normalised
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
for side, hand in (('Left', 'HandLeft'), ('Right', 'HandRight')):
    vs = sorted({vi for p in me.polygons if PARTS[part[p.index]] == hand for vi in p.vertices})
    for g in mesh.vertex_groups:
        g.remove(vs)
    mesh.vertex_groups['mixamorig:%sHand' % side].add(vs, 1.0, 'REPLACE')
    print('FIST', side, len(vs), 'verts -> mixamorig:%sHand' % side)
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
mesh.parent = arm
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
bpy.data.objects.remove(src, do_unlink=True)

# 3. feet
sole = {}
co = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices])
for s, side in ((1, 'Left'), (-1, 'Right')):
    sole[side] = np.where((co[:, 2] < 0.04) & (co[:, 0] * s > 0.05))[0]


def smooth(x, a, b):
    """1 below a, 0 above b, smoothstep between."""
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return 1 - t * t * (3 - 2 * t)


def sole_state(side):
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh()
    P = np.array([tuple(mesh.matrix_world @ m.vertices[i].co) for i in sole[side]])
    ev.to_mesh_clear()
    c = P.mean(0); n = np.linalg.svd(P - c)[2][2]; n = n * np.sign(n[2])
    return Vector(n), float(P[:, 2].min())


def set_action(act):
    arm.animation_data.action = act
    if getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]


DEATHS = {'Dead', 'dying_backwards'}                   # lying clips: feet and floor are handled with the corpse
report = {}
for act in [a for a in bpy.data.actions]:
    keep = act.copy(); keep.name = act.name + '_src'; keep.use_fake_user = True
    if act.name in DEATHS:
        continue
    set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    plan = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        row = {}
        for side in ('Left', 'Right'):
            pb = arm.pose.bones['mixamorig:%sFoot' % side]
            n, h = sole_state(side)
            if n.z < math.cos(math.radians(40)):
                continue                                        # foot lifted steeply: leave the clip alone
            toe = arm.matrix_world @ arm.pose.bones['mixamorig:%sToe_End' % side].head
            ank = arm.matrix_world @ pb.head
            fwd = Vector((toe.x - ank.x, toe.y - ank.y, 0)).normalized(); lat = fwd.cross(Vector((0, 0, 1)))
            wr, wp = smooth(h, 0.04, 0.12), smooth(h, 0.015, 0.05)
            nt = (n - fwd * (n.dot(fwd) * wp) - lat * (n.dot(lat) * wr)).normalized()
            R = n.rotation_difference(nt).to_matrix().to_4x4()
            M = arm.matrix_world @ pb.matrix
            Mn = Matrix.Translation(ank) @ R @ Matrix.Translation(-ank) @ M
            row[side] = (arm.matrix_world.inverted() @ Mn, round(math.degrees(n.angle(Vector((0, 0, 1)))), 1),
                         round(math.degrees(nt.angle(Vector((0, 0, 1)))), 1), round(h, 3))
        plan.append((f, row))
    for f, row in plan:
        scene.frame_set(f)
        for side, (Mloc, *_r) in row.items():
            pb = arm.pose.bones['mixamorig:%sFoot' % side]
            pb.rotation_mode = 'QUATERNION'
            pb.matrix = Mloc
            pb.keyframe_insert('rotation_quaternion', frame=f)
    report[act.name] = {f: {s: r[1:] for s, r in row.items()} for f, row in plan}
    # 4. floor contact: constant Hips offset per clip
    low = 1.0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        low = min(low, min(sole_state(side)[1] for side in ('Left', 'Right')))
    if abs(low) > 0.005:
        hips = arm.pose.bones['mixamorig:Hips']
        mats = []
        for f in range(f0, f1 + 1):
            scene.frame_set(f); mats.append((f, Matrix.Translation((0, 0, -low)) @ (arm.matrix_world @ hips.matrix)))
        for f, Mw in mats:
            scene.frame_set(f); hips.matrix = arm.matrix_world.inverted() @ Mw
            hips.keyframe_insert('location', frame=f)
    print('FLOOR', act.name, 'lowest sole before', round(low, 3), 'shifted' if abs(low) > 0.005 else 'kept')
json.dump(report, open(os.path.join(common.WORK, 'rig_v1_feet.json'), 'w'), indent=0)
# 5. wrists
from mathutils import Quaternion
WRIST_KEEP, WRIST_MAX = 0.25, math.radians(25)
for act in [a for a in bpy.data.actions if not a.name.endswith('_src')]:
    set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    for side in ('Left', 'Right'):
        pb = arm.pose.bones['mixamorig:%sHand' % side]; pb.rotation_mode = 'QUATERNION'
        keys = []
        for f in range(f0, f1 + 1):
            scene.frame_set(f)
            q = Quaternion().slerp(pb.rotation_quaternion.normalized(), WRIST_KEEP)
            if q.angle > WRIST_MAX:
                q = Quaternion().slerp(q, WRIST_MAX / q.angle)
            keys.append((f, q))
        for f, q in keys:
            pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    print('WRIST', act.name, 'damped')
for name, frames in report.items():
    worst = {s: max((v[s][1] for v in frames.values() if s in v and v[s][2] < 0.03), default=None) for s in ('Left', 'Right')}
    print('FEET', name, 'max tilt on ground after fix', worst)
# 6. shoulders: Meshy's idle (and clips built on it) shrugs both clavicles ~31-35 deg above rest; any frame whose
#    clavicle (Shoulder head -> Arm head) rises more than 6 deg above the rest elevation is rotated back down.
REST_ELEV = {}
for side in ('Left', 'Right'):
    sh = arm.matrix_world @ arm.data.bones['mixamorig:%sShoulder' % side].head_local
    ah = arm.matrix_world @ arm.data.bones['mixamorig:%sArm' % side].head_local
    REST_ELEV[side] = math.atan2(ah.z - sh.z, Vector((ah.x - sh.x, ah.y - sh.y)).length)
for act in [a for a in bpy.data.actions if not a.name.endswith('_src') and a.name not in DEATHS]:
    set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range); worst = 0.0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        for side in ('Left', 'Right'):
            pb = arm.pose.bones['mixamorig:%sShoulder' % side]; pb.rotation_mode = 'QUATERNION'
            sh = arm.matrix_world @ pb.head; ah = arm.matrix_world @ arm.pose.bones['mixamorig:%sArm' % side].head
            v = ah - sh; elev = math.atan2(v.z, Vector((v.x, v.y)).length)
            excess = elev - REST_ELEV[side] - math.radians(6)
            if excess > 0:
                worst = max(worst, excess)
                axis = Vector((0, 0, 1)).cross(v).normalized()
                upper = arm.pose.bones['mixamorig:%sArm' % side]; upper.rotation_mode = 'QUATERNION'
                keep = (arm.matrix_world @ upper.matrix).to_3x3().normalized()     # upper arm keeps its world aim
                M = arm.matrix_world @ pb.matrix
                M = Matrix.Translation(sh) @ Matrix.Rotation(excess, 4, axis) @ Matrix.Translation(-sh) @ M
                pb.matrix = arm.matrix_world.inverted() @ M
                bpy.context.view_layer.update()
                U = keep.to_4x4(); U.translation = arm.matrix_world @ upper.head
                upper.matrix = arm.matrix_world.inverted() @ U
                bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=f)
            arm.pose.bones['mixamorig:%sArm' % side].keyframe_insert('rotation_quaternion', frame=f)
    print('SHOULDERS', act.name, 'lowered by up to %.1f deg' % math.degrees(worst))
arm.animation_data.action = bpy.data.actions['Idle_9']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
