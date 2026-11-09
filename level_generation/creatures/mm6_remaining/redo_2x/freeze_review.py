"""Freeze an explicitly reviewed staged redo. Never infer visual approval from numeric checks."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from exact_placement import validate_animation_bindings, validate_landmark_usage, validate_manifest
from whole_animation_resolution import validate_policy


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_browser_review(decision, playback, manifest_digest):
    """Require a visual-review declaration separately from mechanical playback evidence."""
    assert decision.get('checks', {}).get('watched_playback') is True, (
        'Browser acceptance requires an explicit watched_playback review; automated playback is not visual review')
    assert playback['status'] == 'passed'
    assert playback['manifest_sha256'] == manifest_digest
    assert playback.get('bindings'), 'Playback coverage must not be empty'
    assert all(row['all_frames_seen'] for row in playback['bindings'])


def freeze(project, with_viewer=True):
    root = Path(project).resolve()
    out = root / 'redo_2x'
    decision = read(out / 'review/decision.json')
    assert decision['status'] == 'accepted_after_visual_review'
    assert decision.get('method'), 'Describe the actual visual review in the decision record'
    if 'reviewed_notes_sha256' in decision:
        assert decision['reviewed_notes_sha256'] == sha(out / 'review_notes.md')
    manifest = read(out / 'manifest.json')
    assert decision['reviewed_manifest_sha256'] == sha(out / 'manifest.json')
    original = read(root / 'manifest.json')
    registration = read(out / 'registration.json')
    placement_errors = validate_manifest(manifest, registration)
    placement_errors.extend(validate_animation_bindings(manifest))
    assert not placement_errors, 'Exact native placement failed: ' + '; '.join(placement_errors)
    annotations = out / 'review/anatomy_points.json'
    if annotations.exists():
        landmark_errors = validate_landmark_usage(read(annotations), registration)
        assert not landmark_errors, 'Unreliable registration landmarks: ' + '; '.join(landmark_errors)
    validation = read(out / 'validation.json')
    processing = read(out / 'processing.json')
    exceptions = processing.get('retained_detail_exceptions', {})
    policy = processing.get('whole_animation_resolution_policy')
    run = read(out / 'run.json')
    if policy:
        validate_policy(policy, run, original, registration)
        assert manifest['generated_detail'].get('whole_animation_resolution_policy') == policy
        assert decision.get('whole_animation_resolution_policy') == policy
        measured = min(min(row['effective_sampling_xy']) for row in registration.values()
                       if not row.get('empty_native_endpoint'))
        assert manifest['generated_detail']['measured_minimum'] == measured
        assert manifest['generated_detail']['below_target_frames'] == sorted(
            name for name, row in registration.items()
            if not row.get('empty_native_endpoint') and min(row['effective_sampling_xy']) < 2)
    below_target = bool(policy and manifest['generated_detail']['below_target_frames'])
    assert manifest['generated_detail'].get('retained_detail_exceptions', {}) == exceptions
    if exceptions:
        assert decision.get('retained_detail_exceptions') == exceptions
    evidence = []
    for name, digest in decision.get('reviewed_artifact_hashes', {}).items():
        path = (out / name).resolve()
        assert path.is_relative_to(out), name
        assert sha(path) == digest, 'Changed reviewed artwork: ' + name
    playback = None
    if decision.get('review_mode') == 'static_contacts':
        assert set(decision['reviewed_frames']) == set(manifest['frames']), 'Review every selected pose'
        for key in ('faithful_detail', 'poses_and_placement', 'edges_and_alpha', 'masks_and_variants'):
            assert decision['checks'].get(key) is True, key
        assert decision.get('evidence_artifacts'), 'Record the contacts actually inspected'
        for name, digest in decision['evidence_artifacts'].items():
            path = (out / name).resolve()
            assert path.is_relative_to(out), 'Review evidence must belong to this staged package'
            assert sha(path) == digest, 'Changed review evidence: ' + name
            evidence.append(path)
    else:
        # Preserve the historical browser-backed acceptance path without requiring it for new contact reviews.
        assert decision['reviewed_notes_sha256'] == sha(out / 'review_notes.md')
        playback = read(out / 'review/browser_playback.json')
        validate_browser_review(decision, playback, sha(out / 'manifest.json'))
    assert set(registration) == set(original['frames']) == set(manifest['frames'])
    for name, row in registration.items():
        assert not row['raw_clip'], name
        if row.get('empty_native_endpoint'):
            from PIL import Image
            import numpy as np
            assert Image.open(root/'native'/(name+'.png')).getbbox() is None, name
            for folder in ('cleaned', 'aligned_2x', 'masks_2x'):
                assert not np.array(Image.open(out/folder/(name+'.png'))).any(), name
            continue
        if min(row['effective_sampling_xy']) > 2:
            continue
        if policy and 'retained_from' not in row:
            # Sampling remains measured and reported; visual acceptance is still required above.
            continue
        # Adequate historical frames are explicitly outside the redo scope. Require exact retention,
        # independently inventoried sampling, and immutable provenance rather than relaxing the new-art gate.
        from PIL import Image
        import numpy as np
        retained = row['retained_from']
        inventory = read(Path(__file__).parent / 'inventory.json')
        family = next(f for f in inventory['families'] if f['project'] == retained['project'])
        frame = next(f for f in family['frames'] if f['frame'] == name)
        if name in exceptions:
            exception = exceptions[name]
            assert exception.get('user_authorization') and exception.get('reason'), name
            assert row.get('retained_detail_exception') == exception, name
            assert np.allclose(row['effective_sampling_xy'], [frame['sampling_x'], frame['sampling_y']]), name
        else:
            assert not frame['required_redo'] and min(frame['sampling_x'], frame['sampling_y']) >= 2, name
            assert min(row['effective_sampling_xy']) >= 2, name
        assert sha(root/'registration.json') == retained['registration_sha256']
        for relative, digest in retained['assets'].items():
            assert sha(root/relative) == digest
            assert np.array_equal(np.array(Image.open(root/relative)), np.array(Image.open(out/relative))), relative
    for key in ('animations', 'animations_by_palette', 'logical_canvas', 'logical_pivot', 'native_frame_scale'):
        assert manifest.get(key) == original.get(key), key
    for key, value in validation.items():
        if key != 'visual_review_complete':
            assert value is not False, key
    for key in ('source_hashes_unchanged', 'generation_provenance_hashes_verified', 'raw_cells_unclipped',
                'exact_crop_reconstruction', 'exact_atlas_extraction', 'variant_alpha_unchanged',
                'zero_mask_unchanged', 'base_bypass_exact', 'per_palette_native_sequences_preserved'):
        assert validation.get(key) is True, 'Missing or failed validation: ' + key
    for row in registration.values():
        row['review_status'] = 'accepted; see review/acceptance.json'
    write(out / 'registration.json', registration)
    manifest['quality_status'] = ('validated_staged_complete_animation_below_target' if below_target else
                                 'validated_staged_with_detail_exceptions' if exceptions else 'validated_staged_redo')
    manifest['review_record'] = 'review/acceptance.json'
    write(out / 'manifest.json', manifest)
    # The browser exercised the identical runtime manifest before review metadata was attached.
    if playback is not None:
        playback['accepted_manifest_sha256'] = sha(out / 'manifest.json')
        playback['metadata_only_change'] = ['quality_status', 'review_record']
        write(out / 'review/browser_playback.json', playback)
    validation['visual_review_complete'] = True
    validation['visual_review'] = decision['method'] + '; see review/decision.json'
    write(out / 'validation.json', validation)
    review_viewer = out / 'review.html'
    placement_viewer = out / 'placement_review.html'
    if with_viewer or review_viewer.exists() or placement_viewer.exists():
        template_path = root/'viewer.html'
        if not template_path.exists():
            template_path = Path(__file__).resolve().parents[2]/'mm6_peasants/viewer.html'
        template = template_path.read_text()
        assert template.count('/* MANIFEST */') == 1, 'Viewer template must embed one final manifest'
        creature_title = read(out / 'config.json')['title']
        title = creature_title + (' — reviewed complete animations, below 2x detail target, staged' if below_target else
            ' — reviewed with retained detail exceptions, staged'
            if exceptions else ' — reviewed >2x redo, staged')
        manifest_json = json.dumps(manifest, separators=(',', ':'))
        if with_viewer or review_viewer.exists():
            review_viewer.write_text(template.replace('__TITLE__', title)
                                     .replace('/* MANIFEST */', manifest_json))
        if placement_viewer.exists():
            placement_viewer.write_text(template.replace('__TITLE__', creature_title + ' — accepted staged placement')
                                        .replace('/* MANIFEST */', manifest_json))
    run['status'] = 'validated_with_detail_exceptions' if exceptions else 'validated'
    run['quality_status'] = manifest['quality_status']
    run['generated_detail'] = manifest['generated_detail']
    if policy:
        run.pop('minimum_sampling_exclusive', None)
    run['completion_note'] = ('All native images reviewed and staged as complete animation/view sheets; actual '
        'sampling below the 2x target is reported under the recorded user policy.' if below_target else
        'All native images reviewed and staged; explicitly authorized historical detail '
        'exceptions are recorded in processing.json and the manifest.' if exceptions else
        'All native images reviewed and staged with the required generated sampling.')
    selected = {r['raw_path'] for r in registration.values() if 'raw_path' in r}
    for job in run['jobs']:
        selected_frames = {n for n, r in registration.items() if r['batch'] == job['id']}
        job['status'] = 'validated' if selected_frames else 'superseded_by_reviewed_selection'
        if job.get('retained_native_frames'):
            assert job['retained_native_frames'] == job['frames']
            assert all('retained_from' in registration[name] for name in job['frames'])
            job['status'] = 'validated_retained_art'
        for attempt in job['attempts']:
            attempt['review_status'] = 'selected' if attempt.get('raw', attempt.get('raw_path')) in selected else 'superseded'
    write(out / 'run.json', run)
    paths = [p for name in ('manifest.json', 'registration.json', 'calibration.json', 'processing.json',
        'generation.json', 'validation.json', 'config.json', 'sources.json', 'recolor_vectors.json', 'recolor_presets.json',
        'materials.py', 'blade_axes_reviewed.json', 'review.html', 'placement_review.html', 'review_notes.md',
        'README.md', 'run.json',
        'review/browser_playback.json', 'review/decision.json') if (p := out / name).exists()]
    for pattern in ('atlas/*.png', 'review/*_registered_contact.png', 'review/all_*.png',
                    'aligned_2x/*.png', 'masks_2x/*.png', 'cleaned/*.png',
                    'review/edge_current.*', 'review/standing_variants.png'):
        paths.extend(out.glob(pattern))
    paths.extend(evidence)
    record = dict(status='accepted', installed=False, method=decision['method'],
                  reviewed_frames=len(registration), generated_minimum=manifest['generated_detail']['measured_minimum'],
                  artifact_hashes={str(p.relative_to(out)): sha(p) for p in sorted(set(paths))})
    if policy:
        record['whole_animation_resolution_policy'] = policy
        record['below_target_frames'] = manifest['generated_detail']['below_target_frames']
    write(out / 'review/acceptance.json', record)
    write(out / 'acceptance.json', dict(status=run['status'], review_record='review/acceptance.json',
                                     sha256=sha(out / 'review/acceptance.json')))
    print(json.dumps(dict(project=str(root), frames=len(registration), status='validated_staged')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--skip-viewer', action='store_true', help='Skip the shared-template HTML export')
    args = parser.parse_args()
    freeze(args.project, not args.skip_viewer)
