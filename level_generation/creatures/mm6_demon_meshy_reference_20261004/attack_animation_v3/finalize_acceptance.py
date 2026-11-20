"""Freeze the completed local visual/numerical review and verify preserved files."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

STAGE = Path(__file__).resolve().parent
controls = json.loads((STAGE / 'foot_controls.json').read_text())
numeric = json.loads((STAGE / 'foot_deformation_review.json').read_text())['summary']
roundtrip = json.loads((STAGE / 'export_roundtrip_audit.json').read_text())
preservation = json.loads((STAGE / 'preservation_review.json').read_text())
startup = json.loads((STAGE / 'blend_startup_validation.json').read_text())
retained = json.loads((STAGE / 'retained_clips_review.json').read_text())
manifest = json.loads((STAGE / 'animation_manifest.json').read_text())
native = json.loads((STAGE.parent / 'attack_study/feet_review_20261004/pixel_measurements.json').read_text())
spec = json.loads((STAGE.parent / 'attack_study/attack_motion_spec.json').read_text())


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


preserved_files = {}
for filename, expected in controls['preserved_file_sha256'].items():
    path = STAGE.parent / filename
    assert checksum(path) == expected, filename
    preserved_files[str(path)] = expected
for filename, expected in spec['preserved_file_sha256'].items():
    assert checksum(Path(filename)) == expected, filename
    preserved_files[filename] = expected
prior_record = json.loads((STAGE.parent / 'attack_animation_v2/acceptance.json').read_text())
for filename, metadata in prior_record['deliverables'].items():
    path = STAGE.parent / 'attack_animation_v2' / filename
    assert checksum(path) == metadata['sha256'], filename
    preserved_files[str(path)] = metadata['sha256']
assert numeric['samples'] == 145 and numeric['keyed_poses'] == 37
assert numeric['maximum_preserved_bone_basis_error'] == 0
assert numeric['maximum_preserved_bone_world_error'] == 0
assert numeric['maximum_preserved_upper_body_mesh_error'] == 0
assert numeric['maximum_left_foot_change'] == 0
assert numeric['minimum_sole_height'] > 0
assert numeric['maximum_sole_height_change'] < .0002
assert numeric['maximum_rigid_foot_edge_length_relative_error'] < .0001
assert numeric['maximum_leg_segment_length_relative_error'] < 1e-5
assert numeric['minimum_shin_median_core_radius_ratio_vs_v2'] > .99
assert numeric['minimum_thigh_median_core_radius_ratio_vs_v2'] > .99
assert numeric['minimum_triangle_area_ratio'] > .1
assert preservation['rest_mesh_coordinates_identical'] and preservation['vertex_groups_and_weights_identical']
assert preservation['all_85_bind_matrices_identical']
assert preservation['clips']['Attack']['changed_curves'] == 12
assert all(retained[c]['maximum_mesh_change_vs_v2'] == 0 for c in retained)
assert startup['normal_startup_project'] and startup['active_action'] == 'Attack' and startup['fps'] == 48
assert set(startup['actions']) == {'Attack', 'Walking', 'Running'}
assert roundtrip['actual_glb_reimport'] and roundtrip['triangle_indices_match']
assert roundtrip['clips']['Attack']['duration_seconds'] == .75
assert sum(r['sampled_times'] for r in roundtrip['pose_checks'].values()) == 311
assert max(r['maximum_mesh_coordinate_error'] for r in roundtrip['pose_checks'].values()) < 1e-5

# These plates were actually inspected before this acceptance record was frozen.
visual_files = [f'review_plates/{kind}_{first:02d}.{suffix}' for first in range(0, 37, 6)
                for kind, suffix in [('full', 'jpg'), ('legs', 'png'), ('feet', 'png')]]
visual_files += [f'review_plates/foot_detail_{frame:02d}.png' for frame in [0, 6, 12, 18, 24, 30]]
visual_files += [f'review_plates/export_{view}.jpg' for view in ['front', 'side', 'threequarter', 'opposite_threequarter']]
visual_files += ['foot_revision_comparison.png', 'cleaned_viewport.png']
for filename in visual_files:
    with Image.open(STAGE / filename) as image:
        image.verify()
for frame in range(37):
    assert all((STAGE / 'review_frames' / f'{view}_{frame:02d}.png').exists() for view in ['front', 'side'])
for name in ['attack_preview.gif', 'feet_preview.gif']:
    image = Image.open(STAGE / name)
    durations = []
    for frame in range(image.n_frames):
        image.seek(frame)
        durations.append(image.info['duration'])
    assert image.n_frames == 37 and sum(durations) == 1100, (name, durations)

outputs = ['mm6_demon_attack.blend', 'mm6_demon_attack.glb', 'attack_preview.gif', 'feet_preview.gif',
           'foot_revision_comparison.png', 'README.md', 'animation_manifest.json', 'foot_controls.json',
           'foot_deformation_review.json', 'retained_clips_review.json', 'preservation_review.json',
           'export_roundtrip_audit.json', 'export_visual_review.json', 'blend_startup_validation.json']
record = {
    'schema_version': 3,
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'complete_for_requested_foot_motion_revision',
    'reviewer': 'Codex',
    'user_artistic_acceptance': 'not recorded; staged revision delivered for user review',
    'family': 'mm6_dmn',
    'revision': 3,
    'extends_and_supersedes': '../attack_animation_v2/',
    'native_evidence': '../attack_study/feet_review_20261004/',
    'native_colour_and_alpha_verified': all(f['original_colour_and_alpha_exact'] for f in native['frames']),
    'authored_foot_angles_are_inferred': True,
    'native_timing_and_order_preserved': True,
    'changed_curves': preservation['clips']['Attack'],
    'preserved_corrected_upper_body': True,
    'geometry_weights_bind_pose_and_locomotion_preserved': True,
    'foot_contact_and_deformation': numeric,
    'actual_export_checked_at_times': 311,
    'visual_review': {
        'complete': True,
        'all_37_attack_poses_front_and_right_profile': True,
        'detail': '100% unscaled leg/foot plate pixels; six closer right-foot anchors',
        'floor_findings': 'No penetration or visible lift; rigid claws retain their shape; smooth foot pivot and knee-follow return',
        'native_comparison': 'Right foot turns inward at D/E and returns at F; degree values are not recoverable uniquely from one frontal native view',
        'actual_export_views': '22 poses across front, right profile and both three-quarter views',
        'reviewed_plates': visual_files,
    },
    'known_limits': ['Supplied Meshy proportions, broad feet and curved claws retained',
                     'Single genuine frontal native attack view; depth and intermediate angles inferred',
                     'Untextured source; no source UV layer'],
    'preserved_file_sha256': preserved_files,
    'gameplay_installation': False,
    'deliverables': {filename: {'sha256': checksum(STAGE / filename), 'bytes': (STAGE / filename).stat().st_size} for filename in outputs},
}
record['foot_contact_and_deformation']['visual_review_pending'] = False
(STAGE / 'acceptance.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'status': record['status'], 'reviewed_plates': len(visual_files),
                  'source_files_preserved': len(preserved_files), 'deliverables': {n: record['deliverables'][n]['bytes'] for n in ['mm6_demon_attack.blend', 'mm6_demon_attack.glb']}}, indent=2))
