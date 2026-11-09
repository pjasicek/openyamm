"""Record completed human/agent visual review and verify staged deliverable/source integrity."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

stage = Path(__file__).resolve().parent
spec = json.loads((stage.parent / 'attack_study/attack_motion_spec.json').read_text())
manifest = json.loads((stage / 'animation_manifest.json').read_text())
numeric = json.loads((stage / 'deformation_review.json').read_text())['summary']
roundtrip = json.loads((stage / 'export_roundtrip_audit.json').read_text())
startup = json.loads((stage / 'blend_startup_validation.json').read_text())
surface = json.loads((stage / 'surface_flags.json').read_text())
export_visual = json.loads((stage / 'export_visual_review.json').read_text())

def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

preserved = {}
for filename, expected in spec['preserved_file_sha256'].items():
    actual = checksum(Path(filename))
    assert actual == expected, ('Source changed', filename)
    preserved[filename] = actual

assert numeric['samples'] == 145 and numeric['output_samples'] == 37
assert numeric['maximum_arm_length_relative_error'] < 1e-5
assert numeric['maximum_rigid_tip_edge_relative_error'] < .01
assert numeric['maximum_foot_drift'] < .002
assert numeric['minimum_rigid_sole_height'] >= 0
assert numeric['minimum_distal_digit_surface_gap'] >= .003
assert numeric['maximum_hand_torso_triangle_intersections'] == 0
assert not surface['surface_flags']
assert startup['normal_startup_project'] and startup['active_action'] == 'Attack'
assert startup['fps'] == 48
assert set(startup['actions']) == {'Attack', 'Walking', 'Running'}
assert roundtrip['actual_glb_reimport'] and roundtrip['triangle_indices_match']
assert roundtrip['clips']['Attack']['duration_seconds'] == .75
assert roundtrip['pose_checks']['Attack']['sampled_times'] == 145
assert roundtrip['pose_checks']['Walking']['sampled_times'] == 101
assert roundtrip['pose_checks']['Running']['sampled_times'] == 65
for result in roundtrip['pose_checks'].values():
    assert result['maximum_mesh_coordinate_error'] < 1e-5

visual_files = []
for first in range(0, 37, 6):
    for view, suffix in [('front', 'jpg'), ('side', 'jpg'), ('hands', 'png'), ('heads', 'png')]:
        visual_files.append(f'review_plates/{view}_{first:02d}.{suffix}')
visual_files += [f'review_plates/{view}_anchors.jpg' for view in ('rear', 'opposite', 'threequarter', 'walking', 'running')]
visual_files += [f'review_plates/export_{view}.jpg' for view in ('front', 'side', 'threequarter', 'opposite_threequarter')]
visual_files.append('native_comparison.jpg')
for filename in visual_files:
    with Image.open(stage / filename) as image:
        image.verify()
assert len(export_visual['rendered_images']) == 20
for filename in export_visual['rendered_images']:
    assert (stage / filename).exists()
for sample in range(37):
    assert (stage / 'review_frames' / f'front_{sample:02d}.png').exists()
    assert (stage / 'review_frames' / f'side_{sample:02d}.png').exists()
with Image.open(stage / 'attack_preview.gif') as preview:
    durations = []
    for sample in range(preview.n_frames):
        preview.seek(sample)
        durations.append(preview.info.get('duration', 0))
assert sum(durations) == 1100, durations

outputs = ['mm6_demon_attack.glb', 'mm6_demon_attack.blend', 'attack_preview.gif',
           'native_comparison.jpg', 'animation_manifest.json', 'README.md', 'deformation_review.json',
           'control_repairs.json', 'surface_flags.json', 'export_roundtrip_audit.json',
           'blend_startup_validation.json', 'export_visual_review.json', 'motion.py', 'render_export.py']
record = {
    'schema_version': 1,
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'complete_for_requested_attack_animation_and_rig_repairs',
    'reviewer': 'Codex',
    'user_artistic_acceptance': 'not recorded; delivered for user review',
    'family': 'mm6_dmn',
    'native': spec['native'],
    'clips': manifest['clips'],
    'mesh': {'vertices': 7899, 'triangles': 15686, 'bones': 85, 'rest_geometry_and_topology_preserved': True},
    'visual_review': {
        'complete': True,
        'attack_front_and_profile_poses': list(range(37)),
        'original_pixel_hand_and_head_detail_poses': list(range(37)),
        'rear_opposite_profile_and_both_threequarter_poses': [0, 6, 12, 18, 24, 30, 36],
        'walking_representative_pose_count': 7,
        'running_representative_pose_count': 7,
        'actual_export_rendered_pose_view_count': 20,
        'inspected_plates': visual_files,
        'notes': [
            'Inspected arm joint shape, both hands and rigid tips, jaw/upper face, horns, harness, planted feet and tail.',
            'Actual GLB review import uses 48 fps before importing the animation; an initial wrong-rate preview was replaced.',
            'Wider common exported three-quarter views supersede the clipped fingertip in the earlier narrow D diagnostic.',
            'Native/model comparison openly retains different proportions and terminal-claw curvature.',
        ],
    },
    'numerical_review': numeric,
    'actual_glb_reimport': roundtrip,
    'resolved_findings': [
        'Upper face/skull/upper teeth incorrectly followed jaw opening.',
        'Hard claw tips stretched and neighboring finger weights crossed physical branches.',
        'Initial control probe omitted Ring and thumb terminal geometry.',
        'Palm orientation flipped during interpolated crossing sweep.',
        'Forearm twist interpolation wrapped and collapsed intermediate skinning.',
        'Stray head-region weights affected shoulder horn tips.',
    ],
    'known_limitations': [
        'Only one genuine native frontal attack view exists; depth and smooth intermediate motion are inferred.',
        'Supplied mesh has four long claws plus thumb per hand; native art exposes three long claws plus thumb.',
        'Supplied body/head proportions, curved terminal claws and larger tail blade remain; exact native silhouette/feature fits are not claimed.',
        'Numerical surface screening covers hands versus torso and distal-digit gaps, not all possible body self-intersections.',
        'Mesh is untextured with no original UV layer; material/texture work is separate.',
        'Attack is nonlooping; outgoing standing blend and gameplay impact hooks are outside this staged clip.',
        'GIF includes a 350 ms preview-only pause and 10 ms timestamp rounding.',
    ],
    'remaining_rig_or_deformation_blockers': [],
    'source_hash_verification': {'all_match': True, 'files': preserved},
    'deliverables': {name: {'sha256': checksum(stage / name), 'bytes': (stage / name).stat().st_size} for name in outputs},
    'scope': {'gameplay_installation': False, 'shared_code_skills_global_ledgers_runtime_edits': False},
}
(stage / 'acceptance.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'status': record['status'], 'preserved_source_files': len(preserved),
                  'inspected_plates': len(visual_files), 'attack_times_checked': numeric['samples'],
                  'export_roundtrip_times_checked': 311, 'gif_total_ms': sum(durations),
                  'glb_bytes': record['deliverables']['mm6_demon_attack.glb']['bytes']}, indent=2))
