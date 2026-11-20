"""Align the existing source walk's lift envelope with its swing phase, preserving its horizontal paths."""
from pathlib import Path
import json
import sys
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix, Quaternion
p = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(p / 'scripts'))
import armik
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/rig_uv_master.blend'))
rig, body, scene = bpy.data.objects['Rig'], bpy.data.objects['Body'], bpy.context.scene
action = bpy.data.actions['Walking']
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
end = float(action.frame_range[1])
frames = np.arange(round(end * 4)) / 4
masks = {}
for side in 'LR':
    group = body.vertex_groups[f'B_{side}_Foot'].index
    masks[side] = [v.index for v in body.data.vertices if any(g.group == group and g.weight > .5 for g in v.groups)]
rows = []
for frame in frames:
    scene.frame_set(int(frame), subframe=float(frame % 1))
    bpy.context.view_layer.update()
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    lows = {s: min(mesh.vertices[i].co.z for i in masks[s]) for s in 'LR'}
    evaluated.to_mesh_clear()
    rows.append({'basis': {b.name: b.matrix_basis.copy() for b in rig.pose.bones},
                 'world': {b.name: armik.W(rig, b.name).copy() for b in rig.pose.bones}, 'low': lows})
velocity = {s: (np.roll([r['world'][f'B_{s}_Foot'].translation.y for r in rows], -1) -
                 np.roll([r['world'][f'B_{s}_Foot'].translation.y for r in rows], 1)) * 60 for s in 'LR'}
lifts = {s: np.array([max(0, row['low'][s] - .002) for row in rows]) for s in 'LR'}
scores = [sum(float(np.dot(np.roll(lifts[s], -shift), -velocity[s])) for s in 'LR')
          for shift in range(len(rows))]
shift = int(np.argmax(scores))
lifts = {s: np.roll(lifts[s], -shift) for s in 'LR'}
minimum = np.minimum(lifts['L'], lifts['R'])
lifts = {s: lifts[s] - minimum for s in 'LR'}
stride = {s: float(np.median(velocity[s][lifts[s] < .01]) * end / 30) for s in 'LR'}
assert all(value > .2 for value in stride.values()), stride
rig.animation_data.action = None
poses = []
for index, row in enumerate(rows):
    for name, matrix in row['basis'].items():
        rig.pose.bones[name].matrix_basis = matrix
    bpy.context.view_layer.update()
    targets = {}
    lower_by = 0
    for side in 'LR':
        foot = row['world'][f'B_{side}_Foot']
        target = foot.translation.copy()
        target.z += .002 + float(lifts[side][index]) - row['low'][side]
        hip, knee, ankle = [row['world'][f'B_{side}_{part}'].translation for part in ('Thigh', 'Calf', 'Foot')]
        length = ((knee - hip).length + (ankle - knee).length) * .998
        horizontal = (target.x - hip.x) ** 2 + (target.y - hip.y) ** 2
        assert horizontal < length * length
        lower_by = max(lower_by, hip.z - target.z - math.sqrt(length * length - horizontal))
        direction = (ankle - hip).normalized()
        pole = knee - hip
        pole = (pole - direction * pole.dot(direction)).normalized()
        targets[side] = target, foot.to_3x3(), pole
    if lower_by > 0:
        pelvis = armik.W(rig, 'B_Pelvis').copy()
        pelvis.translation.z -= lower_by
        armik.set_world(rig, 'B_Pelvis', pelvis)
    for side, (target, rotation, pole) in targets.items():
        armik.solve_leg(rig, side, target, rotation, pole)
        assert (armik.W(rig, f'B_{side}_Foot').translation - target).length < .0001
    deform = rig.pose.bones['B_Pelvis'].matrix @ rig.data.bones['B_Pelvis'].matrix_local.inverted()
    angles = []
    for side in 'LR':
        direction = deform.inverted().to_3x3() @ (rig.pose.bones[f'B_{side}_Calf'].matrix.translation -
                                                 rig.pose.bones[f'B_{side}_Thigh'].matrix.translation)
        angles.append(math.atan2(-direction.y, -direction.z))
    angle = max(0, min(math.radians(80), max(angles))) + math.radians(8)
    cloth = rig.data.bones['B_Loincloth'].matrix_local
    matrix = deform @ cloth
    rotation = deform.to_3x3() @ Quaternion((1, 0, 0), -angle).to_matrix() @ cloth.to_3x3()
    armik.set_world(rig, 'B_Loincloth', armik.rot_world(matrix, rotation))
    names = ['B_Pelvis', 'B_Loincloth'] + [f'B_{s}_{part}' for s in 'LR' for part in ('Thigh', 'Calf', 'Foot')]
    poses.append({n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names})
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
previous = {}
for frame, pose in zip(np.r_[frames, end], poses + [poses[0]]):
    for name, (rotation, location) in pose.items():
        if name in previous and rotation.dot(previous[name]) < 0:
            rotation = -rotation
        bone = rig.pose.bones[name]
        bone.rotation_quaternion = rotation
        bone.keyframe_insert('rotation_quaternion', frame=float(frame))
        if name == 'B_Pelvis':
            bone.location = location
            bone.keyframe_insert('location', frame=float(frame))
        previous[name] = rotation.copy()
for layer in action.layers:
    for strip in layer.strips:
        for channelbag in strip.channelbags:
            for curve in channelbag.fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = 'LINEAR'
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix()
report = {'lift_phase_advance_s': shift / 120, 'source_duration_s': end / 30,
          'planted_stride_by_foot_m': stride, 'stride_length_m': sum(stride.values()) / 2,
          'change': 'Retained horizontal source paths and lift envelope; aligned lift with forward swing.'}
(p / 'work/walk_fit.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p / 'work/rig_uv_master.blend'))
print('WALK_SUPPORT', report, flush=True)
