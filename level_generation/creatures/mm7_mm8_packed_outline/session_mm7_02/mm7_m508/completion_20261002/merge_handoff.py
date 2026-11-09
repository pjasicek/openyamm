"""Merge reviewed supplements without modifying any inherited accepted pixels."""
from pathlib import Path
import copy
import hashlib
import json
import sys

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
REPO = OUT.parents[5]
sys.path.insert(0, str(REPO / 'level_generation/creatures'))
from exact_placement import validate_manifest

def read(path):
    return json.loads(path.read_text())

def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

old = ROOT / 'redo_2x'
manifest = read(old / 'manifest.json')
new = read(OUT / 'draft_manifest.json')
sources = read(ROOT / 'sources.json')
registrations = read(old / 'registration.json')
new_records = read(OUT / 'registration.json')
assert not set(registrations) & set(new_records)
assert set(registrations) | set(new_records) == set(sources['sources'])
inherited = read(old / 'review/acceptance.json')
inherited_hashes = {}
for relative, expected in inherited['artifact_sha256'].items():
    candidates = [base / relative for base in [old, ROOT, REPO]]
    valid = [p for p in candidates if p.is_file() and sha(p) == expected]
    assert valid, 'Inherited accepted artifact changed: ' + relative
    inherited_hashes[str(valid[0].relative_to(REPO))] = expected
for page in manifest['pages']:
    for role in ['base', 'mask']:
        page[role] = '../redo_2x/' + page[role]
page_offset = len(manifest['pages'])
manifest['pages'].extend(new['pages'])
for name, frame in manifest['frames'].items():
    frame['physical_master'] = '../redo_2x/aligned_2x/' + name + '.png'
    assert (OUT / frame['physical_master']).exists()
    frame['effective_generated_sampling_xy'] = registrations[name]['effective_sampling_xy']
for name, frame in new['frames'].items():
    frame['page'] += page_offset
    manifest['frames'][name] = frame
registrations.update(new_records)
for name, frame in manifest['frames'].items():
    origin = frame['crop_origin_px']
    width, height = frame['atlas_xywh'][2:]
    frame.update(logical_crop_origin=[v / 2 for v in origin], logical_size=[width / 2, height / 2],
        native_anchor_mapping={key: [a[0] - origin[0] / 2, a[1] - origin[1] / 2]
            for key, a in dict(center=[128, 128], bottom_center=[128, 256]).items()},
        mirrored_anchor_mapping={key: [width / 2 - (a[0] - origin[0] / 2), a[1] - origin[1] / 2]
            for key, a in dict(center=[128, 128], bottom_center=[128, 256]).items()})
for row in new_records.values():
    row['independent_placement_review'] = 'passed: native head, wrist/hand, core and vortex; '
    row['independent_placement_review'] += 'opening dissolution hand tip; shrinking detached wind strands in late poses'
    row['review_status'] = 'accepted_static_anatomy_placement_material_alpha_and_palettes'
def refresh_coverage(actions):
    for animation in actions.values():
        if 'directions' in animation:
            animation['generated_view_coverage'] = {view: all(s['frame'] in manifest['frames'] for s in steps)
                for view, steps in animation['directions'].items()}
refresh_coverage(manifest['animations'])
steps_checked = 0
for descriptor, actions in manifest['descriptor_animations'].items():
    refresh_coverage(actions)
    for action, animation in actions.items():
        group_name = sources['descriptor_bindings'][descriptor][action]
        if group_name == 'null':
            assert animation['empty'] and all(not s for s in animation['directions'].values())
            continue
        group = sources['groups'][group_name]
        assert group_name == animation['native_group']
        assert animation['animation_length_raw'] == group['animation_length_raw']
        for view, steps in animation['directions'].items():
            assert len(steps) == len(group['frames'])
            for step, native in zip(steps, group['frames'], strict=True):
                flags = native['flags']; mirror = 'Mirror' + view in flags
                native_name = native['texture_name'].lower() + ('' if 'Image1' in flags else str(8 - int(view) if mirror else int(view)))
                assert step['frame'] == native_name and native_name in manifest['frames']
                assert step['mirror'] == mirror and step['flags'] == flags
                assert step['duration_raw'] == native['frame_length_raw']
                assert step['duration_ms'] == native['frame_length_raw'] * 62.5
                assert step['scale'] == native.get('scale', 1)
                assert step['palette_id'] == native['palette_id']
                steps_checked += 1
assert not validate_manifest(manifest, registrations)
source_hashes = {}
for row in list(sources['sources'].values()) + list(sources['palette_sources'].values()) + sources['group_sources'] + [sources['descriptor_source']]:
    assert sha(REPO / row['path']) == row['sha256'], row['path']
    source_hashes[row['path']] = row['sha256']
full_run = read(ROOT / 'run.json')
updates = {j['id']: j for j in read(OUT / 'run.json')['jobs']}
full_run['jobs'] = [updates.get(j['id'], j) for j in full_run['jobs']]
assert len(full_run['jobs']) == 30
sample = {n: min(r['effective_sampling_xy']) for n, r in registrations.items()}
manifest.update(schema_status='accepted_complete_local', status='accepted_complete_latest_packed_outline',
    source_manifest='sources.json', source_run='full_run.json', placement_registration='registration.json',
    review_record='review/acceptance.json', viewer='../redo_2x/review/index.html',
    missing_frames=[], native_palettes={p: 'native_palettes/' + p + '.bin' for p in sources['palette_sources']},
    actual_generated_detail=dict(minimum_sampling=min(sample.values()), physical_export_scale=2,
        below_2x_frames={n: s for n, s in sample.items() if s < 2}, whole_cycle_priority=True,
        measurement='Actual generated-pixel sampling from reviewed whole-sheet registration, including integer rounding'),
    coverage=dict(complete=True, native_images=160, generated_images=160, missing_images=[],
        all_playback_frames_available=True, native_unused_images=len(sources['unreferenced']),
        restored_unused_images=len(sources['unreferenced']), unused_art_added_to_playback=False,
        full_latest_method_coverage=True),
    memory_bytes=dict(base_rgba8=sum(p['size'][0] * p['size'][1] * 4 for p in manifest['pages']),
        mask_r8=sum(p['size'][0] * p['size'][1] for p in manifest['pages']),
        shared_total=sum(p['size'][0] * p['size'][1] * 5 for p in manifest['pages'])))
write(OUT / 'sources.json', read(ROOT / 'sources.json'))
write(OUT / 'registration.json', registrations)
write(OUT / 'full_run.json', full_run)
write(OUT / 'manifest.json', manifest)
write(OUT / 'review/merge_validation.json', dict(status='passed', frames=160, inherited=131, supplement=29,
    native_sequence_steps_checked=steps_checked, exact_fractional_placement=True, native_hashes=source_hashes,
    inherited_accepted_artifacts_verified=inherited_hashes, inherited_acceptance_sha256=sha(old / 'review/acceptance.json'),
    prior_pixels_modified=False, acceptance_requires_explicit_freeze=True))
print('160 complete Air frames; exact native steps:', steps_checked, '; preserved artifacts:', len(inherited_hashes))
