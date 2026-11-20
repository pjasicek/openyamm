import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_rig_review')
scene = bpy.data.scenes['MM6_Demon_Rig_Repair']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Rig_Review']
obj = scene.objects['Demon_Rigged_Review']
baseline_rig = scene.objects.get('Demon_Rig_Baseline')
baseline_obj = scene.objects.get('Demon_Rigged_Baseline')
if baseline_rig is None:
    with bpy.data.libraries.load(str(stage / 'rig_before_weights.blend'), link=False) as (available, loaded):
        loaded.objects = ['Demon_Rig_Review', 'Demon_Rigged_Review']
    baseline_rig = next(item for item in loaded.objects if item.type == 'ARMATURE')
    baseline_obj = next(item for item in loaded.objects if item.type == 'MESH')
    baseline_rig.name = 'Demon_Rig_Baseline'
    baseline_obj.name = 'Demon_Rigged_Baseline'
    for item in loaded.objects:
        scene.collection.objects.link(item)
for item in (baseline_rig, baseline_obj):
    item.hide_render = True
    item.hide_set(False)
baseline_actions = {track.name: track.strips[0].action for track in baseline_rig.animation_data.nla_tracks}
for target in (rig, baseline_rig):
    target.data.pose_position = 'POSE'
    for track in target.animation_data.nla_tracks:
        track.mute = True
arrays = np.load(stage / 'source_arrays.npz')
source = json.loads((stage / 'source.json').read_text())['audit']
vertices = arrays['vertices']
faces = arrays['faces']
edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
rest_lengths = np.linalg.norm(vertices[edges[:, 0]] - vertices[edges[:, 1]], axis=1)
bad_bones = [source['joint_names'].index(name) for name in ('Bone_036', 'Bone_035', 'Bone_041', 'Bone_040')]
spike_weight = (arrays['weights'] * np.isin(arrays['joints'], bad_bones)).sum(1)
spike_vertices = spike_weight > .05
forefoot_vertices = (vertices[:, 1] < .14) & (vertices[:, 2] > .29) & (np.abs(vertices[:, 0]) > .12)
feature_edges = {'shoulder_spikes': np.any(spike_vertices[edges], axis=1),
                 'shoulder_spike_tips': np.all((spike_weight > .999)[edges], axis=1),
                 'talons': np.all(forefoot_vertices[edges], axis=1)}
foot_vertices = (vertices[:, 1] < .19) & (vertices[:, 2] > .08) & (np.abs(vertices[:, 0]) > .12)

def evaluate(mesh_obj):
    evaluated = mesh_obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    coordinates = np.array([tuple(evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices])
    evaluated.to_mesh_clear()
    return coordinates

metrics = {}
for action_name, end in [('Walking', 25), ('Running', 16)]:
    action = bpy.data.actions[action_name]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    baseline_action = baseline_actions[action_name]
    baseline_rig.animation_data.action = baseline_action
    baseline_rig.animation_data.action_slot = baseline_action.slots[0]
    records = []
    for time in np.arange(0, end + .125, .25):
        record = {'frame': float(time)}
        for label, mesh_obj in [('before', baseline_obj), ('after', obj)]:
            local_frame = time if label == 'before' else time * 2
            scene.frame_set(int(local_frame), subframe=float(local_frame % 1))
            coordinates = evaluate(mesh_obj)
            assert np.isfinite(coordinates).all()
            ratios = np.linalg.norm(coordinates[edges[:, 0]] - coordinates[edges[:, 1]], axis=1) / rest_lengths
            record[label] = {feature: {'maximum_edge_ratio': float(ratios[mask].max()),
                                       'p99_edge_ratio': float(np.quantile(ratios[mask], .99)),
                                       'minimum_edge_ratio': float(ratios[mask].min())}
                             for feature, mask in feature_edges.items()}
            record[label]['minimum_foot_height'] = float(coordinates[foot_vertices, 2].min())
        records.append(record)
    metrics[action_name] = records
(stage / 'deformation_samples.json').write_text(json.dumps(metrics, indent=2) + '\n')
summary = {}
for clip, records in metrics.items():
    summary[clip] = {'quarter_native_frame_samples': len(records)}
    for label in ('before', 'after'):
        summary[clip][label] = {feature: {
            'maximum_edge_ratio': max(record[label][feature]['maximum_edge_ratio'] for record in records),
            'p99_edge_ratio_maximum': max(record[label][feature]['p99_edge_ratio'] for record in records),
        } for feature in feature_edges}
        summary[clip][label]['minimum_foot_height'] = min(record[label]['minimum_foot_height'] for record in records)
(stage / 'deformation_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
baseline_rig.hide_set(True)
baseline_obj.hide_set(True)
camera = scene.camera
floor = scene.objects.get('DemonRigReviewFloor')
if floor is None:
    mesh = bpy.data.meshes.new('DemonRigReviewFloor')
    mesh.from_pydata([(-3, -3, 0), (3, -3, 0), (3, 3, 0), (-3, 3, 0)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new('DemonRigReviewFloor', mesh)
    scene.collection.objects.link(floor)
    floor.color = (.17, .19, .22, 1)
scene.display.shading.color_type = 'OBJECT'
obj.color = (.62, .66, .7, 1)

def render(name, direction, center, scale):
    center = Vector(center)
    camera.data.ortho_scale = scale
    camera.location = center + Vector(direction) * 2
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(stage / (name + '.png'))
    bpy.ops.render.render(write_still=True)

for action_name, frame in [('Walking', 0), ('Walking', 6), ('Walking', 12), ('Walking', 17),
                           ('Walking', 23), ('Running', 4), ('Running', 12)]:
    action = bpy.data.actions[action_name]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    scene.frame_set(frame * 2)
    render('after_' + action_name.lower() + '_' + str(frame), (1.2, -3, .25), (0, -.05, .85), 2.12)
    if action_name == 'Walking' and frame == 6:
        render('after_shoulders', (0, 3, .25), (0, -.02, 1.37), 1.05)
        render('after_feet', (1.2, -3, .5), (0, -.14, .26), .95)
print('Reviewed corrected rig samples')
