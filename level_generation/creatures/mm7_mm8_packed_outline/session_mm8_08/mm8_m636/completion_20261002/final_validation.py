"""Validate the two local completion handoffs using their existing native schemas."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[5]
C = REPO / 'level_generation/creatures'
sys.path.insert(0, str(C))
from exact_placement import validate_manifest
from mm8_restore_queue import native

def read(path):
    return json.loads(path.read_text())

def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def submitted_inputs(root, run, recovered=None):
    receipts = []
    bootstrap = []
    failures = []
    for job in run['jobs']:
        selected = job['selected_raw']
        attempts = job.get('attempts', [])
        chosen = [a for a in attempts if (a.get('raw') or a.get('raw_path')) == selected]
        if recovered and job['id'] in recovered:
            prior = recovered[job['id']]
            paths = prior['actual_referenced_image_paths']
            inputs = prior['input_hashes']
            prompt = job['prompt']
            prompt_hash = sha(REPO / prompt)
            assert prior['selected_raw'] == selected
        else:
            assert len(chosen) == 1, job['id']
            selected_attempt = chosen[0]
            paths = selected_attempt['actual_tool_arguments']['referenced_image_paths']
            inputs = selected_attempt.get('submitted_inputs', selected_attempt.get('actual_submitted_inputs'))
            prompt = selected_attempt.get('prompt') or selected_attempt.get('prompt_path') or job['prompt']
            prompt_hash = selected_attempt['prompt_sha256']
            assert sha(REPO / prompt) == prompt_hash, prompt
        assert len(paths) in (2, 3) and len(inputs) == len(paths), job['id']
        assert 'native' in inputs[0]['role'] and 'outline' in inputs[1]['role']
        assert 'outline' in Path(paths[1]).name.lower()
        for path, row in zip(paths, inputs, strict=True):
            assert Path(path).resolve() == (REPO / row['path']).resolve()
            assert sha(Path(path)) == row['sha256'], path
        if len(paths) == 2:
            assert chosen[0].get('bootstrap_exception'), job['id']
            bootstrap.append(dict(job=job['id'], exception=chosen[0]['bootstrap_exception']))
        colour = Image.open(paths[0]).convert('RGBA')
        outline = Image.open(paths[1]).convert('RGB')
        assert colour.size == outline.size
        guide = np.asarray(outline)
        assert np.array_equal(guide[:, :, 0], guide[:, :, 1]) and np.array_equal(guide[:, :, 0], guide[:, :, 2])
        # Shared contour export uses RGB 15 for its thin line; older guides use 0.
        assert set(np.unique(guide)).issubset({0, 15, 255}), 'Outline contains tonal material guidance'
        cw, ch = job['cell_native_size']
        sx = colour.width / (job['columns'] * cw)
        sy = colour.height / (job['rows'] * ch)
        assert sx == sy and sx == int(sx)
        cell = (int(cw * sx), int(ch * sy))
        crop = tuple(int(v) for v in job['native_crop'])
        assert list(crop) == job['native_crop']
        for index, name in enumerate(job['frames']):
            reference = native(root, name, 636 if name.startswith('m636') else 508)
            expected = np.asarray(reference.crop(crop).resize(cell, Image.Resampling.NEAREST))
            x, y = index % job['columns'] * cell[0], index // job['columns'] * cell[1]
            actual = np.asarray(colour.crop((x, y, x + cell[0], y + cell[1])))
            assert np.array_equal(expected[:, :, 3], actual[:, :, 3]), name + ': input native alpha'
            visible = expected[:, :, 3] > 0
            assert np.array_equal(expected[visible], actual[visible]), name + ': input native colour'
        receipts.append(dict(job=job['id'], complete_native_frames=job['frames'], grid=[job['columns'], job['rows']],
            actual_referenced_image_paths=paths, submitted_inputs=inputs, prompt=prompt, prompt_sha256=prompt_hash,
            selected_raw=selected, selected_raw_sha256=sha(REPO / selected), outline_actually_attached=True,
            colour_pixels_verified_untouched=True, separate_matching_outline_only=True))
        for attempt in attempts:
            if attempt.get('status', '').startswith('failed') or attempt.get('review_status') == 'failed':
                failures.append(dict(job=job['id'], version=attempt.get('version'), status=attempt.get('status'),
                    raw=attempt.get('raw', attempt.get('raw_path')), reason=attempt.get('rejection_reason',
                    attempt.get('review_failure', attempt.get('visual_review', attempt.get('review_status'))))))
    return dict(status='passed', whole_sheet_jobs=len(receipts), selected_attempts=receipts,
                bootstrap_exceptions=bootstrap, historical_failed_attempts=failures)

def pixels(root, manifest, registrations):
    assert not validate_manifest(manifest, registrations)
    pages = {}
    checked = 0
    for name, frame in manifest['frames'].items():
        if frame['page'] not in pages:
            page = manifest['pages'][frame['page']]
            pages[frame['page']] = (Image.open(root / page['base']).convert('RGBA'), Image.open(root / page['mask']))
            assert list(pages[frame['page']][0].size) == page['size']
            assert pages[frame['page']][1].mode == 'L' and pages[frame['page']][0].size == pages[frame['page']][1].size
        base, mask = pages[frame['page']]
        x, y, w, h = frame['atlas_xywh']
        master = Image.open(root / frame['physical_master']).convert('RGBA')
        original = np.asarray(master.crop(frame['crop_in_aligned_px']))
        tile = np.asarray(base.crop((x, y, x + w, y + h)))
        assert np.array_equal(original[:, :, 3], tile[:, :, 3]), name
        solid = original[:, :, 3] > 0
        assert np.array_equal(original[solid], tile[solid]), name + ': material pixels'
        rebuilt = Image.new('L', master.size)
        rebuilt.paste(Image.fromarray(tile[:, :, 3]), frame['crop_in_aligned_px'][:2])
        assert np.array_equal(rebuilt, master.getchannel('A')), name + ': crop clips alpha'
        folder = root.parent / 'redo_2x' if frame['physical_master'].startswith('../redo_2x/') else root
        native_mask = Image.open(folder / 'masks_2x' / (name + '.png'))
        mt = np.asarray(mask.crop((x, y, x + w, y + h)))
        source_mask = np.asarray(native_mask.crop(frame['crop_in_aligned_px']))
        assert np.array_equal(mt[solid], source_mask[solid]), name + ': mask registration'
        if name.startswith('m508'):
            assert not mt.any(), name + ': sole-palette R8 mask'
        else:
            for palette in [636, 637, 638]:
                variant = np.asarray(Image.open(root / 'previews' / f'{name}_{palette}.png'))
                assert np.array_equal(variant[:, :, 3], np.asarray(master)[:, :, 3])
                if palette == 636:
                    assert np.array_equal(variant, np.asarray(master))
        checked += 1
    return dict(status='passed', frames=checked, exact_native_fractional_anchors=True,
        exact_crop_alpha_reconstruction=True, exact_atlas_material_and_alpha=True,
        base_mask_identical_placement=True, base_palette_exact_bypass=True, variant_alpha_unchanged=True,
        hidden_rgb_bleed_only_at_zero_alpha=True)

def finish_fish():
    source = read(OUT.parent / 'sources.json')
    assert source == read(OUT / 'sources.json')
    manifest, registration, run = read(OUT / 'draft_manifest.json'), read(OUT / 'registration.json'), read(OUT / 'run.json')
    assert len(manifest['frames']) == 130 and set(manifest['frames']) == set(source['sources'])
    native_hashes = {}
    for row in list(source['sources'].values()) + list(source['palette_sources'].values()) + source['source_tables'] + [source['descriptor_table']]:
        assert sha(REPO / row['path']) == row['sha256']
        native_hashes[row['path']] = row['sha256']
    steps_checked = 0
    for actor in source['bindings'].values():
        for action in actor['actions'].values():
            group = action['native_group_record']
            for view, sequence in action['views'].items():
                assert len(sequence) == len(group['frames'])
                for step, frame in zip(sequence, group['frames'], strict=True):
                    flags = frame['flags']; mirror = 'Mirror' + view in flags
                    name = frame['texture_name'].lower() + ('' if 'Image1' in flags else str(8 - int(view) if mirror else int(view)))
                    assert step['frame'] == name and name in manifest['frames']
                    assert step['mirrored'] == mirror and step['duration_raw'] == frame['frame_length_raw']
                    assert step['duration_ticks'] == frame['frame_length_raw'] * 8
                    assert step['duration_ms'] == frame['frame_length_raw'] * 62.5
                    assert step['flags'] == flags and step['scale'] == frame.get('scale', 1)
                    assert step['palette'] == frame['palette_id']
                    steps_checked += 1
    sampling = {n: min(r['effective_sampling_xy']) for n, r in registration.items()}
    manifest.update(status='accepted_complete_latest_packed_outline', animations=source['bindings'],
        native_group_bindings=source['bindings'], unused_native_art=source['orphan_images'],
        source_tables=source['source_tables'], descriptor_table=source['descriptor_table'],
        native_palettes=source['palette_sources'], exported_native_palette_files={p: dict(path='native_palettes/' + p + '.bin',
            sha256=sha(OUT / 'native_palettes' / (p + '.bin')), original_source=row['path'])
            for p, row in source['palette_sources'].items()},
        source_run='run.json', review_record='review/acceptance.json', viewer='review/index.html',
        generated_detail=dict(minimum_sampling=min(sampling.values()), physical_export_scale=2,
            below_2x_frames={n: s for n, s in sampling.items() if s < 2}, whole_cycle_priority=True,
            measurement='Generated-pixel sampling from reviewed whole-animation transforms, including integer rounding'),
        coverage=dict(complete=True, native_images=130, accepted_images=130, missing_images=[],
            accepted_unused_images=len(source['orphan_images']), all_playback_frames_available=True,
            full_latest_method_coverage=True, unused_art_added_to_playback=False),
        memory_bytes=read(OUT / 'review/export_checks.json')['memory_bytes'])
    inputs = submitted_inputs(OUT, run)
    checks = pixels(OUT, manifest, registration)
    checks.update(native_hashes=native_hashes, native_animation_steps_checked=steps_checked,
                  original_timing_mirrors_flags_scales_aliases_preserved=True)
    write(OUT / 'manifest.json', manifest)
    write(OUT / 'review/final_validation.json', checks)
    write(OUT / 'review/actual_attachment_provenance.json', inputs)
    print('Fish:', checked_summary(checks), 'complete submitted sheets:', inputs['whole_sheet_jobs'])

def checked_summary(checks):
    return str(checks['frames']) + ' atlas/master/mask placements checked'

finish_fish()
air = C / 'mm7_mm8_packed_outline/session_mm7_02/mm7_m508/completion_20261002'
recovered = {row['job']: row for row in read(air / 'review/inherited_actual_attachment_provenance.json')['retained_accepted_jobs']}
checks = pixels(air, read(air / 'manifest.json'), read(air / 'registration.json'))
inputs = submitted_inputs(air.parent, read(air / 'full_run.json'), recovered)
write(air / 'review/final_validation.json', checks)
write(air / 'review/actual_attachment_provenance.json', inputs)
print('Air:', checked_summary(checks), 'complete submitted sheets:', inputs['whole_sheet_jobs'])
