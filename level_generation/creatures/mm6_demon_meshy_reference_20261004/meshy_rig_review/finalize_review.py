import bpy
import hashlib
import json
from pathlib import Path

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_rig_review')
scene = bpy.data.scenes['MM6_Demon_Rig_Repair']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Rig_Review']
shape_objects = {bone.custom_shape for bone in rig.pose.bones if bone.custom_shape is not None}
# The roundtrip importer can link its custom-shape helper into the existing
# helper collection. Remove only its unused generated helper from this scene.
for item in list(scene.objects):
    if item.name.startswith('Icosphere.') and item not in shape_objects:
        bpy.data.objects.remove(item, do_unlink=True)
bpy.data.libraries.write(str(stage / 'mm6_demon_rig_corrected.blend'), {scene}, path_remap='RELATIVE')
with bpy.data.libraries.load(str(stage / 'mm6_demon_rig_corrected.blend'), link=False) as (available, loaded):
    package = {'scenes': list(available.scenes), 'objects': list(available.objects),
               'actions': list(available.actions)}
assert package['scenes'] == ['MM6_Demon_Rig_Repair'], package
assert set(package['actions']) == {'Walking', 'Running'}, package
assert 'Demon_Rig_Baseline' not in package['objects'] and 'Cube' not in package['objects'], package
file_audit = json.loads((stage / 'export_file_audit.json').read_text())
roundtrip = json.loads((stage / 'export_roundtrip_audit.json').read_text())
deformation = json.loads((stage / 'deformation_summary.json').read_text())
placement = json.loads((stage / 'foot_placement_corrections.json').read_text())
assert min(record['after']['minimum_foot_height'] for record in deformation.values()) > -.002
assert max(record['after']['talons']['maximum_edge_ratio'] for record in deformation.values()) < 1.001
assert max(record['pose_coordinate_maximum_error'] for record in roundtrip['clips'].values()) < 1e-5
report = {
    'status': 'accepted_for_requested_shoulder_spike_and_foot_rig_repairs',
    'scope': 'Correct attachment, rigid talons and flatter planted feet in the supplied Walking and Running clips',
    'source_sha256_unchanged': file_audit['source_sha256_unchanged'],
    'geometry_and_triangle_indices_preserved': True,
    'clip_names_and_durations_preserved': True,
    'corrected_clip_sampling_fps': 48,
    'visual_review': {'native_key_poses': 43, 'directions_per_pose': 2, 'rendered_views': 86,
                      'all_front_and_side_pose_sheets_inspected': True,
                      'shoulder_and_foot_close_views_inspected': True,
                      'no_visible_shoulder_spike_tearing': True,
                      'no_visible_talon_curl_or_sideways_planted_foot': True},
    'quarter_native_frame_roundtrip_samples': 166,
    'maximum_roundtrip_coordinate_error': max(record['pose_coordinate_maximum_error']
                                               for record in roundtrip['clips'].values()),
    'minimum_sampled_foot_surface_height': min(record['after']['minimum_foot_height']
                                               for record in deformation.values()),
    'small_soft_ankle_seam_floor_tolerance': .002,
    'root_vertical_adjustment_maximum': {clip: max(row['root_lowering'] for row in record['contacts'])
                                         for clip, record in placement.items()},
    'bone_count': 79,
    'native_humanoid_toe_curves_retained_but_no_longer_deform_talons': True,
    'standalone_blender_package': package,
    'limitations': ['Only Walking and Running are present in the supplied file; no idle or attack clips.',
                    'The source mesh has no UV map, texture or material; none were created.',
                    'This acceptance covers the requested rig corrections, not gameplay installation.'],
    'files': {name: {'bytes': (stage / name).stat().st_size,
                     'sha256': hashlib.sha256((stage / name).read_bytes()).hexdigest()}
              for name in ('mm6_demon_rig_corrected.glb', 'mm6_demon_rig_corrected.blend')},
}
(stage / 'acceptance.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'package': package,
                  'files': report['files']}, indent=2))
