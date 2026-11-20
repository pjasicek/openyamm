"""Fold the mantle's rear hem onto the floor during death; neutral helper preserves the other clips."""
from pathlib import Path
import math
import json
import bpy
from mathutils import Vector, Matrix, Quaternion
p = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/rig_finished_motion.blend'))
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Body']
scene = bpy.context.scene
name = 'B_MantleBack'
assert name not in rig.data.bones
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix()
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
parent = rig.data.edit_bones['B_Spine2']
bone = rig.data.edit_bones.new(name)
bone.matrix = parent.matrix.copy()
bone.head = Vector((0, .1, 1.54))
bone.tail = bone.head + parent.y_axis * .1
bone.parent = parent
bpy.ops.object.mode_set(mode='OBJECT')
group = body.vertex_groups.new(name=name)
old_group = body.vertex_groups['B_Spine2']
vertices = []
for vertex in body.data.vertices:
    if body.data.attributes['piece'].data[vertex.index].value != 1 or vertex.co.y <= .015:
        continue
    weight = sum(g.weight for g in vertex.groups if g.group == old_group.index)
    share = max(0, min(1, (vertex.co.y - .015) / .04))
    if weight * share > 0:
        group.add([vertex.index], weight * share, 'REPLACE')
        old_group.add([vertex.index], weight * (1 - share), 'REPLACE')
        vertices.append(vertex.index)
assert len(vertices) > 50
axis = (rig.data.bones[name].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0))).normalized()


def low():
    bpy.context.view_layer.update()
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    value = min(mesh.vertices[index].co.z for index in vertices)
    evaluated.to_mesh_clear()
    return value


report = {}
for label in ('Death', 'Dead'):
    action = bpy.data.actions[label]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    rows = []
    for index in range(round(float(action.frame_range[1]) * 4) + 1):
        frame = index / 4
        scene.frame_set(int(frame), subframe=frame % 1)
        bone = rig.pose.bones[name]
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_quaternion = Quaternion()
        angle = 0
        if low() < .003:
            lo, hi = 0, math.radians(85)
            bone.rotation_quaternion = Quaternion(axis, -hi)
            assert low() >= .003, ('Rear mantle cannot clear floor', label, frame, low())
            for _ in range(14):
                mid = (lo + hi) / 2
                bone.rotation_quaternion = Quaternion(axis, -mid)
                if low() < .003:
                    lo = mid
                else:
                    hi = mid
            angle = hi
        bone.rotation_quaternion = Quaternion(axis, -angle)
        rows.append((frame, bone.rotation_quaternion.copy(), low()))
    for frame, rotation, _ in rows:
        bone.rotation_quaternion = rotation
        bone.keyframe_insert('rotation_quaternion', frame=frame)
    report[label] = {'minimum_rear_hem_z_m': min(row[2] for row in rows),
                     'maximum_fold_deg': max(math.degrees(row[1].angle) for row in rows)}
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for curve in channelbag.fcurves:
                    if name in curve.data_path:
                        for key in curve.keyframe_points:
                            key.interpolation = 'LINEAR'
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix()
(p / 'work/mantle_floor.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p / 'work/rig_finished_motion.blend'))
print('MANTLE_FLOOR', report, flush=True)
