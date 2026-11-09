"""Add the selected slash's steps and weight transfer without refitting its approved upper body."""
from pathlib import Path
import hashlib
import json
import math
import sys
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

project = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project / 'scripts'))
import armik

bpy.ops.wm.open_mainfile(filepath=str(project / 'work/rig_mixamo_attack.blend'))
rig = bpy.data.objects['Rig']
body = bpy.data.objects['Body']
scene = bpy.context.scene
lower = ['B_Pelvis'] + [f'B_{side}_{part}' for side in 'LR' for part in ('Thigh', 'Calf', 'Foot', 'Toe0')]


def set_action(action):
    rig.animation_data.action = action
    if action is not None and action.slots:
        rig.animation_data.action_slot = action.slots[0]


def smooth(value):
    value = max(0, min(1, value))
    return value * value * (3 - 2 * value)


set_action(bpy.data.actions['Standing'])
scene.frame_set(0)
home = {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}
home_world = {bone.name: armik.W(rig, bone.name).copy() for bone in rig.pose.bones}
set_action(bpy.data.actions['Attack'])
duration = float(bpy.data.actions['Attack'].frame_range[1]) / 30
frames = np.arange(round(duration * 120) + 1) / 4
approved = []
for frame in frames:
    scene.frame_set(int(frame), subframe=float(frame % 1))
    approved.append({
        'basis': {b.name: b.matrix_basis.copy() for b in rig.pose.bones},
        'world': {b.name: armik.W(rig, b.name).copy() for b in rig.pose.bones},
    })
set_action(None)
source_path = project.parents[3] / 'anim_library/mixamo/Great Sword Slash (2).fbx'
before_objects, before_actions = set(bpy.data.objects), set(bpy.data.actions)
bpy.ops.import_scene.fbx(filepath=str(source_path))
source = next(o for o in set(bpy.data.objects) - before_objects if o.type == 'ARMATURE')
prefix = next(b.name for b in source.pose.bones if b.name.endswith('Hips'))[:-4]
first, last = source.animation_data.action.frame_range
source_fps = scene.render.fps / scene.render.fps_base
assert abs((last - first) / source_fps - duration) < 1e-6


def source_world(name):
    return source.matrix_world @ source.pose.bones[prefix + name].matrix


def plane(hip, knee, ankle):
    direction = (ankle - hip).normalized()
    pole = knee - hip
    pole = (pole - direction * pole.dot(direction)).normalized()
    return Matrix((direction, pole, direction.cross(pole))).transposed()


scene.frame_set(int(first))
initial = {name: source_world(name).copy() for name in (
    'Hips', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase',
    'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase')}
across = initial['LeftUpLeg'].translation - initial['RightUpLeg'].translation
target_across = home_world['B_L_Thigh'].translation - home_world['B_R_Thigh'].translation
alignment = Matrix.Rotation(math.atan2(target_across.y, target_across.x) - math.atan2(across.y, across.x), 3, 'Z')
source_length = sum((initial[a].translation - initial[b].translation).length
                    for a, b in (('LeftUpLeg', 'LeftLeg'), ('LeftLeg', 'LeftFoot')))
target_length = sum((home_world[a].translation - home_world[b].translation).length
                    for a, b in (('B_L_Thigh', 'B_L_Calf'), ('B_L_Calf', 'B_L_Foot')))
scale = target_length / source_length
pole_maps = {}
sole = {}
for side, long_side in (('L', 'Left'), ('R', 'Right')):
    names = [f'B_{side}_{part}' for part in ('Thigh', 'Calf', 'Foot')]
    target_plane = plane(*(home_world[n].translation for n in names))
    source_plane = plane(*(initial[long_side + part].translation for part in ('UpLeg', 'Leg', 'Foot')))
    pole_maps[side] = target_plane @ source_plane.transposed()
    group = body.vertex_groups[f'B_{side}_Foot'].index
    points = [v.co.copy() for v in body.data.vertices if any(g.group == group and g.weight > .5 for g in v.groups)]
    inverse = rig.data.bones[f'B_{side}_Foot'].matrix_local.inverted()
    sole[side] = [inverse @ point for point in points]
    assert len(sole[side]) > 20
samples = []
for frame in frames:
    source_frame = first + frame / 30 * source_fps
    scene.frame_set(int(source_frame), subframe=float(source_frame % 1))
    samples.append({name: source_world(name).copy() for name in initial})
for obj in set(bpy.data.objects) - before_objects:
    bpy.data.objects.remove(obj, do_unlink=True)
for action in set(bpy.data.actions) - before_actions:
    bpy.data.actions.remove(action)
scene.render.fps = 30


poses = []
foot_paths = {s: [] for s in 'LR'}
pelvis_path = []
maximum_grip_error = 0
minimum_sole = 100
minimum_tail = 100
max_tail_lift = 0
tail_vertices = json.loads((project / 'work/tail_fit.json').read_text())['vertices']


def tail_low():
    bpy.context.view_layer.update()
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    low = min(mesh.vertices[index].co.z for index in tail_vertices)
    evaluated.to_mesh_clear()
    return low

for frame, old, src in zip(frames, approved, samples):
    for name, matrix in old['basis'].items():
        rig.pose.bones[name].matrix_basis = home[name] if name in lower else matrix
    bpy.context.view_layer.update()
    weight = min(smooth(frame / 4.5), smooth((duration * 30 - frame) / 4.5))
    lifts = {s: max(0, min(src[n].translation.z - initial[n].translation.z
                          for n in (s + 'Foot', s + 'ToeBase'))) * scale * weight
             for s in ('Left', 'Right')}
    support_lift = min(lifts.values())
    root_delta = alignment @ (src['Hips'].translation - initial['Hips'].translation) * scale * weight
    root_delta.z -= support_lift
    pelvis = home_world['B_Pelvis'].copy()
    delta = alignment @ (src['Hips'].to_3x3() @ initial['Hips'].to_3x3().inverted()) @ alignment.inverted()
    rotation = Quaternion().slerp(delta.to_quaternion(), weight).to_matrix() @ pelvis.to_3x3()
    pelvis = Matrix.LocRotScale(pelvis.translation + root_delta, rotation.to_quaternion(), Vector((1, 1, 1)))
    armik.set_world(rig, 'B_Pelvis', pelvis)
    targets = {}
    for side, long_side in (('L', 'Left'), ('R', 'Right')):
        name = f'B_{side}_Foot'
        foot, toe = long_side + 'Foot', long_side + 'ToeBase'
        delta = alignment @ (src[foot].to_3x3() @ initial[foot].to_3x3().inverted()) @ alignment.inverted()
        rotation = Quaternion().slerp(delta.to_quaternion(), weight).to_matrix() @ home_world[name].to_3x3()
        travel = alignment @ (src[foot].translation - initial[foot].translation) * scale * weight
        target = home_world[name].translation + travel
        lift = lifts[long_side] - support_lift
        home_low = min((home_world[name] @ point).z for point in sole[side])
        target.z = home_low + lift - min((rotation @ point).z for point in sole[side])
        source_plane = plane(*(src[long_side + part].translation for part in ('UpLeg', 'Leg', 'Foot')))
        pole = pole_maps[side] @ source_plane.col[1]
        home_pole = plane(*(home_world[f'B_{side}_{part}'].translation for part in ('Thigh', 'Calf', 'Foot'))).col[1]
        pole = home_pole.lerp(pole, weight).normalized()
        targets[side] = target, rotation, pole
    # Lower the hips only if this creature's proportions otherwise put a foot beyond reach.
    lower_by = 0
    for side, (target, _, _) in targets.items():
        hip, knee, ankle = [armik.W(rig, f'B_{side}_{part}').translation for part in ('Thigh', 'Calf', 'Foot')]
        length = ((knee - hip).length + (ankle - knee).length) * .998
        horizontal = (target.x - hip.x) ** 2 + (target.y - hip.y) ** 2
        assert horizontal < length * length, 'Source step exceeds this creature leg reach'
        lower_by = max(lower_by, hip.z - target.z - math.sqrt(length * length - horizontal))
    if lower_by > 0:
        pelvis.translation.z -= lower_by
        armik.set_world(rig, 'B_Pelvis', pelvis)
    for side, (target, rotation, pole) in targets.items():
        armik.solve_leg(rig, side, target, rotation, pole)
        matrix = armik.W(rig, f'B_{side}_Foot')
        minimum_sole = min(minimum_sole, min((matrix @ point).z for point in sole[side]))
        foot_paths[side].append(tuple(matrix.translation))
    # Preserve the approved torso, arms and grip in world orientation while the hips carry their position.
    for bone in rig.pose.bones:
        if bone.name not in lower and bone.name != 'B_Loincloth':
            armik.set_world(rig, bone.name, armik.rot_world(armik.W(rig, bone.name), old['world'][bone.name].to_3x3()))
    before = old['world']['B_R_Hand'].inverted() @ old['world']['B_L_Hand']
    after = armik.W(rig, 'B_R_Hand').inverted() @ armik.W(rig, 'B_L_Hand')
    maximum_grip_error = max(maximum_grip_error, (before.translation - after.translation).length)
    deform = rig.pose.bones['B_Pelvis'].matrix @ rig.data.bones['B_Pelvis'].matrix_local.inverted()
    angles = []
    for side in 'LR':
        hip = deform.inverted() @ rig.pose.bones[f'B_{side}_Thigh'].matrix.translation
        knee = deform.inverted() @ rig.pose.bones[f'B_{side}_Calf'].matrix.translation
        direction = knee - hip
        angles.append(math.atan2(-direction.y, -direction.z))
    angle = max(0, min(math.radians(80), max(angles))) + math.radians(8)
    cloth_rest = rig.data.bones['B_Loincloth'].matrix_local
    cloth = deform @ cloth_rest
    cloth_rotation = deform.to_3x3() @ Quaternion((1, 0, 0), -angle).to_matrix() @ cloth_rest.to_3x3()
    armik.set_world(rig, 'B_Loincloth', armik.rot_world(cloth, cloth_rotation))
    # Lift the existing tail curve when the source crouch would drive its tip through the floor.
    if tail_low() < .006:
        bone = rig.pose.bones['Tail0']
        base = bone.matrix.copy()
        axis = (bone.tail - bone.head).cross(Vector((0, 0, 1))).normalized()

        def trial(angle):
            matrix = armik.rot_world(base, Quaternion(axis, angle).to_matrix() @ base.to_3x3())
            bone.matrix = matrix
            return tail_low()

        lo, hi = 0, math.radians(30)
        assert trial(hi) >= .006, 'Tail cannot clear the floor within its existing curve'
        for _ in range(14):
            mid = (lo + hi) / 2
            if trial(mid) < .006:
                lo = mid
            else:
                hi = mid
        trial(hi)
        max_tail_lift = max(max_tail_lift, math.degrees(hi))
    minimum_tail = min(minimum_tail, tail_low())
    pelvis_path.append(tuple(armik.W(rig, 'B_Pelvis').translation))
    poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
for name in ('Attack', 'Attack2'):
    action = bpy.data.actions[name]
    set_action(action)
    previous = {}
    for frame, pose in zip(frames, poses):
        for bone_name, (rotation, location) in pose.items():
            if bone_name in previous and rotation.dot(previous[bone_name]) < 0:
                rotation = -rotation
            bone = rig.pose.bones[bone_name]
            bone.rotation_mode = 'QUATERNION'
            bone.rotation_quaternion = rotation
            bone.keyframe_insert('rotation_quaternion', frame=float(frame))
            if bone_name == 'B_Pelvis':
                bone.location = location
                bone.keyframe_insert('location', frame=float(frame))
            previous[bone_name] = rotation.copy()
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for curve in channelbag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
report = {
    'source': str(source_path.relative_to(project.parents[3])),
    'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
    'duration_s': duration, 'leg_scale': scale, 'max_grip_change_m': maximum_grip_error,
    'minimum_sole_z_m': minimum_sole,
    'minimum_tail_z_m': minimum_tail, 'max_tail_clearance_rotation_deg': max_tail_lift,
    'foot_travel_xyz_m': {s: np.ptp(foot_paths[s], axis=0).tolist() for s in 'LR'},
    'pelvis_travel_xyz_m': np.ptp(pelvis_path, axis=0).tolist(),
    'adaptation': 'Source steps, foot pitch and pelvis weight transfer over native guard; 0.15 s guard blends.',
}
assert maximum_grip_error < .0001, report
assert minimum_sole >= -.001, report
assert minimum_tail >= .001, report
assert all(max(report['foot_travel_xyz_m'][s]) > .05 for s in 'LR'), report
set_action(None)
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix()
scene['attack_lower_body_source'] = json.dumps(report)
(project / 'work/mixamo_legs.json').write_text(json.dumps(report, indent=2))
fit_path = project / 'work/mixamo_attack.json'
fit = json.loads(fit_path.read_text())
fit['lower_body_fit'] = report
fit['adaptation'] = ('Source steps and pelvis weight transfer over native guard; approved upper-body fit '
                     'and rigid grip; 0.15 s guard blends.')
fit_path.write_text(json.dumps(fit, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(project / 'work/rig_mixamo_attack.blend'))
print('MIXAMO_LEGS', report, flush=True)
