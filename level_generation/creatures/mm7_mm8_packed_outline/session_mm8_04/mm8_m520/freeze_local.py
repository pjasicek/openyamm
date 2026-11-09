"""Freeze session-local packages only after every recorded visual checkpoint passes."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

repo = Path.cwd()
root = Path(__file__).resolve().parent.parent / sys.argv[1]
now = datetime.now(timezone.utc).isoformat()


def read(name):
    return json.loads((root / name).read_text())


def write(name, value):
    (root / name).write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


run, sources = read('run.json'), read('sources.json')
draft, reg = read('draft_manifest.json'), read('registration.json')
poses, palettes = read('review/pose_checkpoints.json'), read('review/palette_group_checkpoints.json')
processing, checks = read('processing.json'), read('review/export_checks.json')
notes = read('review/final_review_notes.json')
assert notes['status'] == 'all_required_visual_checks_completed'
assert checks['full_coverage'] and not draft['missing_frames']
assert set(draft['frames']) == set(sources['sources'])
assert set(reg) | set(sources['pixel_aliases']) == set(sources['sources'])
for key in ('source_hashes_unchanged', 'exact_crop_reconstruction', 'exact_atlas_extraction',
            'base_mask_placement_identical', 'variant_alpha_unchanged', 'base_bypass_exact'):
    assert checks[key], key
for item in sources['sources'].values():
    assert sha(repo / item['path']) == item['sha256']
for item in sources['source_tables']:
    assert sha(repo / item['path']) == item['sha256']
for key in ('descriptor_table', 'inventory_source'):
    item = sources[key]
    assert sha(repo / item['path']) == item['sha256']
for item in sources['staged_native_palettes'].values():
    assert sha(root / item['path']) == item['sha256']
    assert sha(repo / item['native_source']) == item['sha256']
assert draft['animations'] == sources['bindings']
assert draft['pixel_aliases'] == sources['pixel_aliases']
assert len(poses['jobs']) == len(run['jobs'])
palette_frames = set()
for item in palettes['groups'].values():
    assert item['status'] == 'visually_reviewed'
    assert sha(Path(item['path'])) == item['sha256']
    palette_frames.update(item['frames'])
assert palette_frames == set(reg)
context = ('TASK CONTEXT — MM8 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful '
           'restoration of an EXISTING Might and Magic VIII (MM8) fantasy role-playing game sprite '
           'asset, using the supplied original animation bitmaps. Restore the existing fantasy-game '
           'character and its original animation; preserve its native costume, material coverage, '
           'anatomy and poses. The request is game-art restoration.')
below = []
for job in run['jobs']:
    pose = poses['jobs'][job['id']]
    assert sha(repo / pose['contact_path']) == pose['sha256']
    extraction = processing['extraction'][job['id']]
    assert pose['raw_sha256'] == extraction['raw_sha256']
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
    chosen['visual_screen'] = dict(status='accepted_local', reviewed_utc=now, evidence=pose['contact_path'])
    job['status'] = 'accepted_local'
    sampling = min(min(reg[name]['effective_sampling_xy']) for name in job['frames'] if name in reg)
    if sampling < 2:
        below.append(dict(job=job['id'], sampling=sampling,
                          resolution='Reviewed complete native cycle retained; no sampling-only regeneration.'))

frames = sorted(draft['frames'])
atlas_visual = read('review/atlas_visual_checkpoints.json')['contacts']
assert len(atlas_visual) == (len(frames) + 7) // 8
atlas_checkpoints = []
for index in range((len(frames) + 7) // 8):
    path = root / 'review' / f'atlas_poses_{index:02d}.png'
    visual = atlas_visual[str(index)]
    assert visual['status'] == 'visually_reviewed_actual_atlas_light_dark'
    assert sha(path) == visual['sha256']
    assert visual['frames'] == frames[index * 8:(index + 1) * 8]
    atlas_checkpoints.append(dict(path=str(path.relative_to(root)), sha256=sha(path),
        frames=frames[index * 8:(index + 1) * 8], reviewed_utc=now,
        status='all_actual_atlas_poses_light_dark_visually_reviewed'))
assert notes['atlas_contacts'] == len(atlas_checkpoints)
write('review/atlas_checkpoints.json', dict(status='complete', frames=len(frames), contacts=atlas_checkpoints))
for name, item in reg.items():
    clean_hash = hashlib.sha256(Image.open(root / 'cleaned' / f'{name}.png').convert('RGBA').tobytes()).hexdigest()
    assert clean_hash == item['clean_sha256']
    item['independent_placement_review'] = dict(status='visually_reviewed', reviewed_utc=now,
        features=notes['independent_features'], evidence=poses['jobs'][item['batch']]['contact_path'],
        observations=notes['placement'])
write('registration.json', reg)
poses['status'] = 'all_whole_cycles_visually_reviewed_complete'
write('review/pose_checkpoints.json', poses)
checks.update(visual_review_complete=True, animation_review_complete=True,
    animation_review_method='Complete static chronological native/restored contacts; native timing and mirrors preserved. No timed playback claim.')
write('review/export_checks.json', checks)
edge = read('review/atlas_edge_scan.json')
edge['visual_review'] = notes['edges']
write('review/atlas_edge_scan.json', edge)
run['status'] = 'accepted_local_complete'
run['coverage'].update(accepted_files=len(frames), complete=True)
write('run.json', run)
draft['status'] = 'accepted_local_complete'
write('draft_manifest.json', draft)
evidence = [str(Path(p['contact_path']).relative_to(root.relative_to(repo))) for p in poses['jobs'].values()]
evidence += [x['path'] for x in atlas_checkpoints]
evidence += ['review/all_masks.png', 'review/atlas_worst_edges.png', 'review/palette_group_checkpoints.json']
evidence += notes['material_evidence']
minimum = min(min(item['effective_sampling_xy']) for item in reg.values())
acceptance = dict(status='accepted_local_complete', reviewed_utc=now, creature=sources['creature'],
    label=sources['label'], descriptor_ids=notes['descriptor_ids'], method=run['method'],
    scope=dict(native_files=len(frames), referenced_files=sum(v['referenced'] for v in sources['sources'].values()),
        unused_files=len(sources['orphan_images']), whole_sheets=len(run['jobs']), split_sheets=0,
        palettes=list(map(int, sources['staged_native_palettes'])), playback_additions=0),
    review=dict(reviewed_frames=frames, evidence=evidence, placement=notes['placement'], material=notes['material'],
        edges=notes['edges'], variants=notes['variants'], animation=checks['animation_review_method']),
    sampling=dict(export_pixels_per_logical_pixel=2, minimum_registered_generated_sampling=minimum, below_2x=below),
    limitations=['Fine material reconstruction is interpretive.', 'Static chronology review; no timed gameplay playback.'],
    installed=False)
(root / 'README.md').write_text(
    f'# {sources["label"]} — accepted local restoration\n\n'
    f'{len(run["jobs"])} complete packed animation/view sheets, {len(frames)} native files, '
    f'{acceptance["scope"]["referenced_files"]} playback files and {len(sources["orphan_images"])} unused files. '
    f'Native descriptor IDs {notes["descriptor_ids"]} and all native ACT palettes are preserved.\n\n'
    f'Checked physical masters are 2x. Minimum measured generated detail is {minimum:.6f}x; '
    f'{len(below)} reviewed whole-cycle sheets fall below 2x. Every pose, independent placement feature, '
    f'palette/mask, exported alpha edge and 100% material detail was reviewed. '
    f'See review/acceptance.json for frozen hashes and run.json for the actual ordered '
    f'attachment paths, roles, hashes and every attempt.\n\n'
    f'{len(draft["pages"])} RGBA8/R8 atlas pairs, {checks["memory_bytes"]["total_base_mask_packing"]:,} bytes '
    f'uncompressed. Native aliases, timing, mirrors, fractional anchors and unused art remain preserved. '
    f'No gameplay installation. Static chronological review; no timed playback claim.\n')
acceptance['artifact_hashes'] = {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
    if p.is_file() and p != root / 'review/acceptance.json'}
write('review/acceptance.json', acceptance)
print(sources['label'], len(frames), 'native files; minimum generated detail', minimum,
      'frozen artifacts', len(acceptance['artifact_hashes']))
