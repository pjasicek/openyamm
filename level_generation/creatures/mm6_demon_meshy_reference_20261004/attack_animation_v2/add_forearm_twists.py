import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Matrix

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation_v2')
scene = bpy.data.scenes['MM6_Demon_Attack']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Attack_Rig']
obj = scene.objects['Demon_Attack_Mesh']
rig.animation_data.action = None
for track in rig.animation_data.nla_tracks:
    track.mute = True
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
for item in scene.objects:
    item.select_set(False)
rig.hide_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for side in ('Right', 'Left'):
    parent = rig.data.edit_bones['mixamorig:' + side + 'ForeArm']
    hand = rig.data.edit_bones['mixamorig:' + side + 'Hand']
    delta = hand.head - parent.head
    for number, fraction in enumerate((0, 1/3, 2/3)):
        name = 'Demon_' + side + '_ForearmTwist' + str(number)
        if name not in rig.data.edit_bones:
            bone = rig.data.edit_bones.new(name)
            bone.head = parent.head + delta * fraction
            bone.tail = bone.head + delta * .20
            bone.roll = parent.roll
            bone.parent = parent
            bone.use_connect = False
            bone.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
source = np.load(stage / 'source_geometry.npz')
v = source['vertices']
report = {}
for side in ('Right', 'Left'):
    parent = rig.data.bones['mixamorig:' + side + 'ForeArm']
    hand = rig.data.bones['mixamorig:' + side + 'Hand']
    delta = np.array(hand.head_local - parent.head_local)
    t = np.clip((v - np.array(parent.head_local)) @ delta / np.dot(delta, delta), 0, 1)
    original_group = obj.vertex_groups[parent.name]
    groups = []
    for number in range(3):
        name = 'Demon_' + side + '_ForearmTwist' + str(number)
        groups.append(obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name))
    groups.append(original_group)
    count = 0
    # This operates on the original forearm contribution, retaining wrist/upper-arm seam weights.
    column = list(source['group_names']).index(parent.name)
    original = np.load(stage / 'repaired_weights.npz')['weights'][:, column]
    for index in np.flatnonzero(source['weights'][:, column] > 1e-5):
        s = t[index] * 3
        lower = min(int(s), 2)
        u = s - lower
        for group in groups:
            group.remove([int(index)])
        if original[index] < 1e-7:
            continue
        count += 1
        groups[lower].add([int(index)], float(original[index] * (1 - u)), 'REPLACE')
        if u > 1e-6:
            groups[lower + 1].add([int(index)], float(original[index] * u), 'REPLACE')
    report[side] = {'weighted_vertices': count, 'twist_fractions': [0, 1/3, 2/3, 1],
                    'helpers': [g.name for g in groups[:-1]]}
# Give the package's locomotion actions explicit identity channels for the new helper controls.
for clip, end in [('Walking', 50), ('Running', 32)]:
    name = 'Demon_Package_' + clip
    action = bpy.data.actions.get(name)
    if action is None:
        action = bpy.data.actions[clip].copy()
        action.name = name
        action.use_fake_user = True
        bag = action.layers[0].strips[0].channelbag(action.slots[0], ensure=True)
        for bone in rig.pose.bones:
            if not bone.name.startswith('Demon_'):
                continue
            for prop, vector in [('location', (0,0,0)), ('rotation_quaternion', (1,0,0,0)), ('scale',(1,1,1))]:
                for component, value in enumerate(vector):
                    curve = bag.fcurves.new(data_path='pose.bones[' + json.dumps(bone.name) + '].' + prop, index=component)
                    curve.keyframe_points.add(2)
                    for point, frame in zip(curve.keyframe_points, (0, end)):
                        point.co = frame, value
                        point.interpolation = 'LINEAR'
                    curve.update()
    track = next(t for t in rig.animation_data.nla_tracks if t.name == clip)
    track.strips[0].action = action
    track.strips[0].action_slot = action.slots[0]
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
error = float(np.max(np.abs(np.array([tuple(vertex.co) for vertex in mesh.vertices]) - v)))
evaluated.to_mesh_clear()
assert error < 1e-5
assert max(abs(sum(e.weight for e in vertex.groups) - 1) for vertex in obj.data.vertices) < 1e-5
(stage / 'forearm_twist_repair.json').write_text(json.dumps({'bones': len(rig.data.bones), 'rest_coordinate_error': error, 'sides': report}, indent=2) + '\n')
print('Added six distributed forearm twist controls; rest mesh unchanged:', error)
