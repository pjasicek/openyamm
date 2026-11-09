"""Freeze only the Thunder Lizard package after its recorded full visual review."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

repo = Path.cwd()
root = Path(__file__).resolve().parent
now = datetime.now(timezone.utc).isoformat()

def read(name):
    return json.loads((root / name).read_text())

def write(name, value):
    (root / name).write_text(json.dumps(value, indent=2) + "\n")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

run = read('run.json')
sources = read('sources.json')
draft = read('draft_manifest.json')
reg = read('registration.json')
poses = read('review/pose_checkpoints.json')
palettes = read('review/palette_group_checkpoints.json')
processing = read('processing.json')
checks = read('review/export_checks.json')
assert len(draft['frames']) == len(sources['sources']) == len(reg) == 170
assert checks['full_coverage'] and not draft['missing_frames']
for key in ('source_hashes_unchanged', 'exact_crop_reconstruction', 'exact_atlas_extraction',
            'base_mask_placement_identical', 'variant_alpha_unchanged', 'base_bypass_exact'):
    assert checks[key], key
for item in sources['sources'].values():
    assert sha(repo / item['path']) == item['sha256']
for item in sources['staged_native_palettes'].values():
    assert sha(root / item['path']) == item['sha256']
    assert sha(repo / item['native_source']) == item['sha256']
assert len(poses['jobs']) == len(run['jobs']) == 36
assert len(palettes['groups']) == 43
palette_frames = set()
for item in palettes['groups'].values():
    assert item['status'] == 'visually_reviewed'
    evidence = item
    assert sha(Path(evidence['path'])) == evidence['sha256']
    palette_frames.update(evidence['frames'])
assert palette_frames == set(draft['frames'])
context = ('TASK CONTEXT — MM8 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful '
           'restoration of an EXISTING Might and Magic VIII (MM8) fantasy role-playing game sprite '
           'asset, using the supplied original animation bitmaps. Restore the existing fantasy-game '
           'character and its original animation; preserve its native costume, material coverage, '
           'anatomy and poses. The request is game-art restoration.')
for job in run['jobs']:
    pose = poses['jobs'][job['id']]
    assert sha(repo / pose['contact_path']) == pose['sha256']
    extraction = processing['extraction'][job['id']]
    chosen = next(a for a in job['attempts'] if a.get('raw_sha256') == extraction['raw_sha256'])
    assert chosen['status'] == 'returned'
    assert chosen.get('visual_screen', {}).get('status') != 'rejected'
    for attempt in job['attempts']:
        inputs = attempt['actual_submitted_inputs']
        arguments = attempt['actual_tool_arguments']['referenced_image_paths']
        assert len(inputs) == len(arguments) >= 2
        assert inputs[0]['role'] == 'untouched_native_colour_complete_animation'
        assert inputs[1]['role'] == 'matching_outline_only_geometry'
        assert job['id'] + '_outline' in arguments[1]
        assert len(inputs) == 3 or attempt['bootstrap_exception']
        for source, argument in zip(inputs, arguments):
            assert Path(argument) == repo / source['path']
            assert sha(Path(argument)) == source['sha256']
        assert sha(repo / attempt['prompt_path']) == attempt['prompt_sha256']
        assert (repo / attempt['prompt_path']).read_text().startswith(context)
    assert sha(repo / chosen['raw_path']) == chosen['raw_sha256']
    chosen['visual_screen'] = {'status': 'accepted_local', 'reviewed_utc': now,
                              'evidence': pose['contact_path']}
    job['status'] = 'accepted_local'
    pose['status'] = 'all_native_steps_and_independent_placement_visually_reviewed'

frames = sorted(draft['frames'])
atlas_checkpoints = []
for i in range(22):
    path = root / 'review' / f'atlas_poses_{i:02d}.png'
    atlas_checkpoints.append({'path': str(path.relative_to(root)), 'sha256': sha(path),
                              'frames': frames[i * 8:(i + 1) * 8], 'reviewed_utc': now,
                              'status': 'all_actual_atlas_poses_light_dark_visually_reviewed'})
write('review/atlas_checkpoints.json', {'status': 'complete', 'frames': 170,
                                      'contacts': atlas_checkpoints})
for name, item in reg.items():
    assert hashlib.sha256(Image.open(root / 'cleaned' / f'{name}.png').convert('RGBA').tobytes()).hexdigest() == item['clean_sha256']
    item['independent_placement_review'] = {
        'status': 'visually_reviewed', 'reviewed_utc': now,
        'features': ['core anchor', 'head/frill upper feature', 'foot/tail lower feature'],
        'evidence': poses['jobs'][item['batch']]['contact_path'],
        'observations': 'Native movement and near/far limbs compared at every stored step; common sheet scale and fractional placement retained.'}
write('registration.json', reg)
poses['status'] = 'all_whole_cycles_visually_reviewed_complete'
write('review/pose_checkpoints.json', poses)
checks.update(visual_review_complete=True, animation_review_complete=True,
              animation_review_method='Complete static chronological native/restored contacts; native timing and mirrors preserved. No timed playback claim.')
write('review/export_checks.json', checks)
edge = read('review/atlas_edge_scan.json')
edge['visual_review'] = 'All 170 exported poses on light/dark, all R8 masks and worst six frill/head edges visually reviewed; no visible fringe or copied guide bands.'
write('review/atlas_edge_scan.json', edge)
run['status'] = 'accepted_local_complete'
run['coverage'].update(accepted_files=170, complete=True)
write('run.json', run)
draft['status'] = 'accepted_local_complete'
write('draft_manifest.json', draft)
material_evidence = [f'cleaned/{n}.png' for n in ('m516aa2', 'm516nc1', 'm516df0')]
evidence = [str(Path(p['contact_path']).relative_to(root.relative_to(repo))) for p in poses['jobs'].values()]
evidence += [x['path'] for x in atlas_checkpoints]
evidence += ['review/all_masks.png', 'review/atlas_worst_edges.png', 'review/palette_group_checkpoints.json'] + material_evidence
minimum = min(min(item['effective_sampling_xy']) for item in reg.values())
acceptance = {
    'status': 'accepted_local_complete', 'reviewed_utc': now,
    'creature': sources['creature'], 'label': sources['label'], 'descriptor_ids': [88, 89, 90],
    'method': run['method'], 'scope': {'native_files': 170, 'referenced_files': 141,
    'unused_files': 29, 'whole_sheets': 36, 'split_sheets': 0, 'palettes': [516, 518, 519], 'playback_additions': 0},
    'review': {'reviewed_frames': frames, 'evidence': evidence,
    'placement': 'All 36 whole native chronological cycles and independent upper/lower features reviewed; near/far limbs, frill, claws, tail and falling extremes retained.',
    'material': 'Original delivered detail viewed at 100% in attack, fidget and fallen poses. Fine scales, natural belly shading, red/orange frills and ivory claws retained without copied outline bands.',
    'edges': edge['visual_review'],
    'variants': 'All 170 poses reviewed in ACT 516/518/519 with authored enhanced material masks. No spill into stable belly shading; exact base bypass and unchanged alpha verified.',
    'animation': checks['animation_review_method']},
    'sampling': {'export_pixels_per_logical_pixel': 2, 'minimum_registered_generated_sampling': minimum,
                 'below_2x': []},
    'limitations': ['Fine scale reconstruction is interpretive.', 'Static chronology review; no timed gameplay playback.'],
    'installed': False}
assert minimum >= 2
(root / 'README.md').write_text(
    f'# Thunder Lizard A — accepted local restoration\n\n'
    f'Complete packed animation/view sheets with matching attached outline guides: 36 sheets, '
    f'170 native files, 141 playback files and 29 unused files retained without playback additions. '
    f'Native descriptor IDs 88–90 and ACT palettes 516/518/519 are preserved.\n\n'
    f'Physical masters are 2x. Minimum measured generated detail is {minimum:.6f}x. '
    f'All poses, independent placement features, all palettes/masks, exported alpha edges and '
    f'100% delivered material detail were reviewed. See review/acceptance.json for frozen hashes '
    f'and run.json for actual imagegen attachments and every attempt. '
    f'Timing, aliases, mirrors, fractional anchors and unused art remain native.\n\n'
    f'10 RGBA8/R8 atlas page pairs, {checks["memory_bytes"]["total_base_mask_packing"]:,} bytes '
    f'uncompressed. No gameplay installation. Static chronological review; no timed playback claim.\n')
acceptance['artifact_hashes'] = {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
                               if p.is_file() and p != root / 'review/acceptance.json'}
write('review/acceptance.json', acceptance)
print('Accepted Thunder Lizard:', len(frames), 'native files; minimum generated detail', minimum,
      'frozen artifacts', len(acceptance['artifact_hashes']))
