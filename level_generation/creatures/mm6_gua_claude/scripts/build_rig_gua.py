"""Rigged master from Meshy's API auto-rig (meshy/rig_v1, 24 bones, 1.578 m, armature at 0.01 scale) and our UV mesh
(work/step1_uv.blend, same surface; the shoe-rim loop cut adds vertices). Saves work/rig_v1.blend.
 1. The armature scale is applied (location keys rescaled), Meshy's walking/running clips are merged in as
    'Walking'/'Running' (+ any extra Meshy animation GLBs given as arguments, named by their file stem).
 2. Our mesh takes Meshy's skin weights from the nearest surface point of Meshy's mesh (face-interpolated).
 3. Rigid parts: fists (|x| > 0.50) 100 % on their Hand bone; face, helmet, nasal bar and the coif above the jaw
    (z > 1.36) 100 % on Head, so the eye window cannot shear against the face. At most 4 influences elsewhere.
 4. Feet: Meshy's clips carry the source body's foot posture; the Foot bone is rotated about the ankle per frame so
    the sole lies flat while it is on the ground (roll fades 4->12 cm, pitch 1.5->5 cm). A constant Hips offset puts the
    lowest sole of each locomotion clip at z = 0.
 5. Wrists: the clips bend the source body's relaxed open hand; on a fist only 25 % is kept, capped at 25 deg.
 6. Shoulders: clavicles kept within 6 deg of the rest elevation; the upper arm keeps its world aim.
Usage: blender --background --python build_rig_gua.py -- [extra_anim.glb:Name ...]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

EXTRA = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 24
RIG = os.path.join(common.PROJECT, 'meshy', 'rig_v1')


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


def import_glb(path):
    before = set(bpy.data.objects)
    acts = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before], [a for a in bpy.data.actions if a not in acts]


objs, acts = import_glb(os.path.join(RIG, 'result_rigged_character_glb_url.glb'))
arm = next(o for o in objs if o.type == 'ARMATURE')
arm.name = 'Guard_Rig'
src = next(o for o in objs if o.type == 'MESH' and o.name.startswith('char'))
src.name = 'MeshyGuard'
for o in objs:
    if o not in (arm, src):
        bpy.data.objects.remove(o, do_unlink=True)
for a in acts:
    bpy.data.actions.remove(a)
clips = [(os.path.join(RIG, 'result_basic_animations_walking_glb_url.glb'), 'Walking'),
         (os.path.join(RIG, 'result_basic_animations_running_glb_url.glb'), 'Running')]
for e in EXTRA:
    p, n = e.rsplit(':', 1)
    clips.append((os.path.join(common.PROJECT, p), n))
for path, name in clips:
    o2, a2 = import_glb(path)
    for o in o2:
        bpy.data.objects.remove(o, do_unlink=True)
    keep = max(a2, key=lambda a: a.frame_range[1] - a.frame_range[0])
    for a in a2:
        if a is not keep:
            bpy.data.actions.remove(a)
    keep.name = name
    keep.use_fake_user = True
    print('CLIP', name, tuple(round(x, 2) for x in keep.frame_range))

# 1. apply the 0.01 armature scale; location keys are in the old (cm) bone space
k = arm.scale[0]
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.context.view_layer.objects.active = arm
arm.animation_data_create()
arm.animation_data.action = None
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
for a in bpy.data.actions:
    for fc in fcurves(a):
        if fc.data_path.endswith('location'):
            for kp in fc.keyframe_points:
                kp.co[1] *= k
                kp.handle_left[1] *= k
                kp.handle_right[1] *= k
            fc.update()
print('ARMATURE scale applied', k, 'world', tuple(arm.matrix_world.to_scale()))


def resample(act):
    """Meshy keys sit on fractional frames (30 fps keys at 24 fps). Re-key every bone on integer frames 0..N
    spanning the same time (N = rounded length; the last frame repeats the first pose of cyclic clips)."""
    arm.animation_data.action = act
    if getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]
    a0, a1 = act.frame_range
    n = max(1, int(round(a1 - a0)))
    poses = []
    for f in range(n + 1):
        t = a0 + (a1 - a0) * f / n
        scene.frame_set(int(math.floor(t)), subframe=t - math.floor(t))
        poses.append({pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in arm.pose.bones})
    new = bpy.data.actions.new(act.name)
    name = act.name
    bpy.data.actions.remove(act)
    new.name = name
    new.use_fake_user = True
    arm.animation_data.action = new
    for f, pose in enumerate(poses):
        for pb in arm.pose.bones:
            pb.rotation_mode = 'QUATERNION'
            pb.location, pb.rotation_quaternion = pose[pb.name]
            pb.keyframe_insert('location', frame=f)
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print('RESAMPLE', name, 'frames 0 ..', n)


for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'
for a in list(bpy.data.actions):
    resample(a)

with bpy.data.libraries.load(os.path.join(common.WORK, 'step1_uv.blend')) as (df, dt):
    dt.objects = ['Guard']
    dt.scenes = df.scenes[:1]
mesh = dt.objects[0]
scene.collection.objects.link(mesh)
lib = dt.scenes[0]
for key in ('gua_parts', 'gua_uv_regions'):
    scene[key] = lib[key]
bpy.data.scenes.remove(lib)
PARTS = json.loads(scene['gua_parts'])
me = mesh.data

# 2. weights from the nearest point on Meshy's surface (barycentric over the hit triangle)
dg = bpy.context.evaluated_depsgraph_get()
sme = src.data
sco = [src.matrix_world @ v.co for v in sme.vertices]
sme.calc_loop_triangles()
tris = [tuple(t.vertices) for t in sme.loop_triangles]
tree = BVHTree.FromPolygons(sco, tris)
gname = {g.index: g.name for g in src.vertex_groups}
W = np.zeros((len(sco), len(gname)))
for v in sme.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
for g in src.vertex_groups:
    mesh.vertex_groups.new(name=g.name)
dmax = 0.0
OW = np.zeros((len(me.vertices), len(gname)))
for v in me.vertices:
    p = mesh.matrix_world @ v.co
    loc, nrm, ti, d = tree.find_nearest(p)
    dmax = max(dmax, d)
    a, b, c = (sco[i] for i in tris[ti])
    from mathutils.geometry import barycentric_transform
    bc = barycentric_transform(loc, a, b, c, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
    OW[v.index] = sum(max(bc[j], 0.0) * W[tris[ti][j]] for j in range(3))
print('WEIGHT_COPY max distance', round(dmax * 1000, 3), 'mm')

# 3. rigid parts
part = np.zeros(len(me.polygons), dtype=np.int32)
me.attributes['part'].data.foreach_get('value', part)
gidx = {n: i for i, n in gname.items()}
co = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices])
vpart = {}
for p in me.polygons:
    for vi in p.vertices:
        vpart.setdefault(vi, set()).add(PARTS[part[p.index]])
rigid = {'LeftHand': 0, 'RightHand': 0, 'Head': 0}
for vi, ps in vpart.items():
    target = None
    if ps & {'ArmRight', 'ArmLeft'} and abs(co[vi, 0]) > 0.50:
        target = 'LeftHand' if co[vi, 0] > 0 else 'RightHand'
    elif ps & {'Head', 'Helmet', 'Nasal'} or ('Coif' in ps and co[vi, 2] > 1.36):
        target = 'Head'
    if target:
        OW[vi] = 0.0
        OW[vi, gidx[target]] = 1.0
        rigid[target] += 1
print('RIGID', rigid)
for vi in range(len(me.vertices)):
    w = OW[vi]
    top = np.argsort(-w)[:4]
    s = w[top].sum()
    for j in top:
        if w[j] > 1e-4:
            mesh.vertex_groups[gname[j]].add([vi], float(w[j] / s), 'REPLACE')
mesh.parent = arm
mesh.matrix_parent_inverse = arm.matrix_world.inverted()
mod = mesh.modifiers.new('Armature', 'ARMATURE')
mod.object = arm
bpy.data.objects.remove(src, do_unlink=True)


def set_action(act):
    arm.animation_data.action = act
    if getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]


# 4. feet
sole = {}
for s, side in ((1, 'Left'), (-1, 'Right')):
    sole[side] = np.where((co[:, 2] < 0.035) & (co[:, 0] * s > 0.05))[0]


def smooth(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return 1 - t * t * (3 - 2 * t)


def sole_state(side):
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh()
    P = np.array([tuple(mesh.matrix_world @ m.vertices[i].co) for i in sole[side]])
    ev.to_mesh_clear()
    c = P.mean(0)
    n = np.linalg.svd(P - c)[2][2]
    n = n * np.sign(n[2])
    return Vector(n), float(P[:, 2].min())


LOCO = [a for a in bpy.data.actions if a.name in ('Walking', 'Running')]
report = {}
for act in LOCO:
    keep = act.copy()
    keep.name = act.name + '_src'
    keep.use_fake_user = True
    set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    plan = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        row = {}
        for side in ('Left', 'Right'):
            pb = arm.pose.bones[side + 'Foot']
            n, h = sole_state(side)
            if n.z < math.cos(math.radians(40)):
                continue
            toe = arm.matrix_world @ arm.pose.bones[side + 'ToeBase'].tail
            ank = arm.matrix_world @ pb.head
            fwd = Vector((toe.x - ank.x, toe.y - ank.y, 0)).normalized()
            lat = fwd.cross(Vector((0, 0, 1)))
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
            pb = arm.pose.bones[side + 'Foot']
            pb.rotation_mode = 'QUATERNION'
            pb.matrix = Mloc
            pb.keyframe_insert('rotation_quaternion', frame=f)
    report[act.name] = {f: {s: r[1:] for s, r in row.items()} for f, row in plan}
    low = 1.0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        low = min(low, min(sole_state(side)[1] for side in ('Left', 'Right')))
    if abs(low) > 0.005:
        hips = arm.pose.bones['Hips']
        mats = []
        for f in range(f0, f1 + 1):
            scene.frame_set(f)
            mats.append((f, Matrix.Translation((0, 0, -low)) @ (arm.matrix_world @ hips.matrix)))
        for f, Mw in mats:
            scene.frame_set(f)
            hips.matrix = arm.matrix_world.inverted() @ Mw
            hips.keyframe_insert('location', frame=f)
    print('FLOOR', act.name, 'lowest sole before', round(low, 3))
json.dump(report, open(os.path.join(common.WORK, 'rig_v1_feet.json'), 'w'), indent=0)

# 5. wrists
WRIST_KEEP, WRIST_MAX = 0.25, math.radians(25)
for act in LOCO:
    set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    for side in ('Left', 'Right'):
        pb = arm.pose.bones[side + 'Hand']
        pb.rotation_mode = 'QUATERNION'
        keys = []
        for f in range(f0, f1 + 1):
            scene.frame_set(f)
            q = Quaternion().slerp(pb.rotation_quaternion.normalized(), WRIST_KEEP)
            if q.angle > WRIST_MAX:
                q = Quaternion().slerp(q, WRIST_MAX / q.angle)
            keys.append((f, q))
        for f, q in keys:
            pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=f)
for name, frames in report.items():
    worst = {s: max((v[s][1] for v in frames.values() if s in v and v[s][2] < 0.03), default=None)
             for s in ('Left', 'Right')}
    print('FEET', name, 'max tilt on ground after fix', worst)

# 6. shoulders
REST_ELEV = {}
for side in ('Left', 'Right'):
    sh = arm.matrix_world @ arm.data.bones[side + 'Shoulder'].head_local
    ah = arm.matrix_world @ arm.data.bones[side + 'Arm'].head_local
    REST_ELEV[side] = math.atan2(ah.z - sh.z, Vector((ah.x - sh.x, ah.y - sh.y)).length)
for act in LOCO:
    set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    worst = 0.0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        for side in ('Left', 'Right'):
            pb = arm.pose.bones[side + 'Shoulder']
            pb.rotation_mode = 'QUATERNION'
            sh = arm.matrix_world @ pb.head
            ah = arm.matrix_world @ arm.pose.bones[side + 'Arm'].head
            v = ah - sh
            elev = math.atan2(v.z, Vector((v.x, v.y)).length)
            excess = elev - REST_ELEV[side] - math.radians(6)
            upper = arm.pose.bones[side + 'Arm']
            upper.rotation_mode = 'QUATERNION'
            if excess > 0:
                worst = max(worst, excess)
                axis = Vector((0, 0, 1)).cross(v).normalized()
                keepm = (arm.matrix_world @ upper.matrix).to_3x3().normalized()
                M = arm.matrix_world @ pb.matrix
                M = Matrix.Translation(sh) @ Matrix.Rotation(excess, 4, axis) @ Matrix.Translation(-sh) @ M
                pb.matrix = arm.matrix_world.inverted() @ M
                bpy.context.view_layer.update()
                U = keepm.to_4x4()
                U.translation = arm.matrix_world @ upper.head
                upper.matrix = arm.matrix_world.inverted() @ U
                bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=f)
            upper.keyframe_insert('rotation_quaternion', frame=f)
    print('SHOULDERS', act.name, 'lowered by up to %.1f deg' % math.degrees(worst))
set_action(bpy.data.actions['Walking'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
