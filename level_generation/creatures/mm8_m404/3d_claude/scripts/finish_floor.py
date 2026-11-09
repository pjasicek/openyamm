"""Keep the tail above the floor between the original death keys, measured on the final reduced skin."""
from pathlib import Path
import json
import math
import bpy
from mathutils import Matrix, Vector, Quaternion
p = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/rig_uv_master.blend'))
rig, body, scene = bpy.data.objects['Rig'], bpy.data.objects['Body'], bpy.context.scene
names = [group.name for group in body.vertex_groups]
tail = [v.index for v in body.data.vertices if sum(g.weight for g in v.groups
        if names[g.group].startswith('Tail')) > .1]
assert len(tail) > 100


def lows():
    bpy.context.view_layer.update()
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    lowest = min((mesh.vertices[i] for i in tail), key=lambda v: v.co.z)
    result = lowest.co.z, min(v.co.z for v in mesh.vertices), lowest.co.copy()
    evaluated.to_mesh_clear()
    return result


report = {}
for label in ('Death', 'Dead'):
    action = bpy.data.actions[label]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    rows = []
    for index in range(round(float(action.frame_range[1]) * 4) + 1):
        frame = index / 4
        scene.frame_set(int(frame), subframe=frame % 1)
        bone = rig.pose.bones['Tail0']
        base = bone.matrix.copy()
        axis = (lows()[2] - bone.head).cross(Vector((0, 0, 1))).normalized()

        def trial(angle):
            matrix = (Quaternion(axis, angle).to_matrix() @ base.to_3x3()).to_4x4()
            matrix.translation = base.translation
            bone.matrix = matrix
            return lows()[0]

        correction = 0
        if lows()[0] < .006:
            hi = next((math.radians(a) for a in range(1, 61) if trial(math.radians(a)) >= .006), None)
            assert hi is not None, (label, frame, lows()[0])
            lo = hi - math.radians(1)
            for _ in range(12):
                mid = (lo + hi) / 2
                if trial(mid) < .006:
                    lo = mid
                else:
                    hi = mid
            correction = hi
            trial(hi)
        tail_low, body_low, _ = lows()
        assert body_low >= -.01, (label, frame, body_low)
        if body_low < .002:
            pelvis = rig.pose.bones['B_Pelvis']
            matrix = pelvis.matrix.copy()
            matrix.translation.z += .002 - body_low
            pelvis.matrix = matrix
            tail_low, body_low, _ = lows()
        assert body_low >= .001, (label, frame, body_low)
        rows.append((frame, bone.rotation_quaternion.copy(), tail_low, body_low, correction,
                     rig.pose.bones['B_Pelvis'].location.copy()))
    previous = None
    for frame, rotation, _, _, _, location in rows:
        if previous is not None and rotation.dot(previous) < 0:
            rotation = -rotation
        bone.rotation_quaternion = rotation
        bone.keyframe_insert('rotation_quaternion', frame=frame)
        previous = rotation.copy()
        pelvis = rig.pose.bones['B_Pelvis']
        pelvis.location = location
        pelvis.keyframe_insert('location', frame=frame)
    report[label] = {'minimum_tail_z_m': min(row[2] for row in rows),
                     'minimum_body_z_m': min(row[3] for row in rows),
                     'maximum_correction_deg': max(math.degrees(row[4]) for row in rows)}
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for curve in channelbag.fcurves:
                    if 'Tail0' in curve.data_path:
                        for key in curve.keyframe_points:
                            key.interpolation = 'LINEAR'
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix()
(p / 'work/final_floor.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p / 'work/rig_uv_master.blend'))
print('FINAL_FLOOR', report, flush=True)
