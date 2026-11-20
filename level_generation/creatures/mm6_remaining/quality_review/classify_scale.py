"""Deterministic, read-only MM6 scale triage and evidence-gated downsample proposals."""

import argparse
from collections import Counter, defaultdict
import csv
from itertools import combinations
import json
import math
from pathlib import Path
from statistics import median
import sys

from PIL import Image

from audit_row_scale import HERE, REPO, alpha_metrics, digest, packages, read


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def measure(name, axis, native, restored, native_error, restored_error, tier, basis, role=None):
    """Errors bound the measured span, not each endpoint; restored units are physical export pixels."""
    values = [native, restored, native_error, restored_error, tier]
    if not all(positive(value) for value in values):
        raise ValueError(f'{name}: lengths, uncertainties and tier must be finite and positive')
    if native_error >= native or restored_error >= restored:
        raise ValueError(f'{name}: uncertainty must be smaller than its measured span')
    return dict(name=name, axis=axis, basis=basis, role=role, native_length=native,
                restored_length_px=restored, native_error=native_error, restored_error_px=restored_error,
                correction=tier * native / restored,
                correction_interval=[tier * (native - native_error) / (restored + restored_error),
                                     tier * (native + native_error) / (restored - restored_error)])


def intersection(measures):
    return (max(item['correction_interval'][0] for item in measures),
            min(item['correction_interval'][1] for item in measures))


def screen(measures, threshold):
    """A reproducible shortlist, never an anatomical acceptance or a resize instruction."""
    if not measures:
        return 'insufficient_evidence'
    low, high = intersection(measures)
    if low > high:
        return 'proportion_or_pose_review'
    nominal = median(item['correction'] for item in measures)
    if (low > 1 or high < 1) and abs(nominal - 1) >= threshold:
        if {item['axis'] for item in measures} >= {'x', 'y'}:
            return 'uniform_scale_candidate'
        return 'size_signal_needs_body_measurements'
    return 'no_scale_signal'


def saved_measurements(record, native, restored, tier):
    measures = []
    excluded = set(record.get('diagnostic_landmarks', []))
    points = {key: value for key, value in record.get('review_landmarks', {}).items()
              if key not in excluded and 'native' in value and 'restored_before_translation' in value}
    for first, second in combinations(sorted(points), 2):
        a, b = points[first], points[second]
        for index, axis in enumerate(('x', 'y')):
            n = abs(a['native'][index] - b['native'][index])
            p = abs(a['restored_before_translation'][index] - b['restored_before_translation'][index])
            if n >= 20 and p / tier >= 20:
                # Conservative screening assumption: one logical pixel per endpoint on both images.
                measures.append(measure(f'{first}/{second}', axis, n, p, 2, 2 * tier, tier,
                                        'unverified_saved_landmarks'))
    if native and restored:
        for field, axis in [('width', 'x'), ('height', 'y')]:
            if native[field] >= 20 and restored[field] >= 20:
                measures.append(measure('silhouette_' + field, axis, native[field], restored[field] * tier,
                                        2, 2 * tier, tier, 'silhouette_including_equipment_and_effects'))
    return measures


def solve_verified(annotation, provenance, tier, export_scale, sampling, strict, blockers, deadband):
    """Fit body dimensions only; withheld dimensions never influence the proposed factor."""
    result = dict(decision='review_measurements', proposed_export_scale=None)
    if annotation is None:
        return dict(result, reason='No artifact-bound, verified body dimensions; screening cannot authorize resizing.')
    if annotation.get('provenance') != provenance:
        raise ValueError('Body measurements refer to different artifacts; remeasure before using them')
    if annotation.get('verified') is not True or not annotation.get('reviewer'):
        raise ValueError('Body measurements require verified=true and an identified reviewer')
    measured = []
    features = set()
    for item in annotation.get('dimensions', []):
        name = item['name']
        if name in features or item['axis'] not in ('x', 'y') or item['role'] not in ('fit', 'check'):
            raise ValueError('Dimensions require unique names, x/y axes and fit/check roles')
        features.add(name)
        measured.append(measure(name, item['axis'], item['native_length'], item['restored_length_px'],
                                item['native_error'], item['restored_error_px'], tier,
                                'verified_body_dimension', item['role']))
    result['dimensions'] = measured
    fit = [item for item in measured if item['role'] == 'fit']
    checks = [item for item in measured if item['role'] == 'check']
    if len(fit) < 2 or {item['axis'] for item in fit} != {'x', 'y'} or not checks:
        return dict(result, reason='Need X and Y fitting dimensions and a separately measured withheld body feature.')
    low, high = intersection(fit)
    if low > high:
        return dict(result, decision='proportion_or_pose_review',
                    reason='Fitting dimensions require incompatible scales.')
    # Weighted least squares in logical units, constrained by every fitting uncertainty interval.
    weights = [1 / (item['native_error'] + item['restored_error_px'] / tier) ** 2 for item in fit]
    numerator = sum(w * item['restored_length_px'] / tier * item['native_length'] for w, item in zip(weights, fit))
    denominator = sum(w * (item['restored_length_px'] / tier) ** 2 for w, item in zip(weights, fit))
    factor = min(high, max(low, numerator / denominator))
    result.update(fitted_correction=factor, fit_interval=[low, high])
    if any(not item['correction_interval'][0] <= factor <= item['correction_interval'][1] for item in checks):
        return dict(result, decision='proportion_or_pose_review', reason='Uniform fit fails a withheld body dimension.')
    # When unchanged scale is plausible, avoid chasing annotation noise or tiny differences.
    if low <= 1 + deadband and high >= 1 - deadband:
        if all(item['correction_interval'][0] <= 1 + deadband and
               item['correction_interval'][1] >= 1 - deadband for item in checks):
            return dict(result, decision='keep_scale',
                        reason='Evidence does not establish a change beyond the deadband.')
        return dict(result,
                    reason='Fit cannot establish a change, but the withheld feature disagrees with current scale.')
    if not positive(export_scale) or sampling is None or blockers:
        return dict(result, decision='source_review', reason='Source transform, clipping or sampling needs review.')
    remaining = sampling / factor
    result['estimated_sampling_after'] = remaining
    if remaining < 2 or (strict and remaining <= 2):
        return dict(result, decision='source_review',
                    reason='Correction would violate the generated-detail requirement.')
    return dict(result, decision='downsample_trial_candidate', correction=factor,
                proposed_export_scale=export_scale * factor,
                reason='Verified X/Y dimensions agree and a withheld feature passes; trial export still needs review.')


def bindings(manifest):
    result = defaultdict(set)
    for palette, actions in manifest['animations_by_palette'].items():
        for action, animation in actions.items():
            for view, steps in animation['views'].items():
                for index, step in enumerate(steps, 1):
                    result[step['frame']].add((str(palette), action, str(view), index, len(steps),
                                               bool(step.get('mirrored'))))
    return {name: [dict(palette=p, action=a, view=v, position=i, length=n, mirrored=m)
                   for p, a, v, i, n, m in sorted(entries)] for name, entries in result.items()}


def raw_source(root, record, generation):
    path = record.get('raw_path')
    if path:
        return REPO / path
    batch = generation.get('batches', {}).get(record.get('batch'), {})
    path = batch.get('raw', {}).get('path')
    return root / path if path else None


def source_sampling(record, tier, empty_pair):
    if record.get('empty_native_endpoint'):
        if not empty_pair:
            raise ValueError('Declared empty native endpoint contains foreground')
        return None, 'not_applicable_empty_endpoint'
    scale = record.get('scale')
    effective = record.get('effective_sampling_xy')
    if scale is not None and not positive(scale):
        raise ValueError('Invalid recorded export scale')
    if effective is not None:
        if len(effective) != 2 or not all(positive(v) for v in effective):
            raise ValueError('Invalid recorded effective sampling')
        return min(effective), 'recorded_effective_sampling_xy'
    if scale is not None:
        return tier / scale, 'nominal_tier_divided_by_scale'
    return None, 'unknown_source_sampling'


def viewer_notes(root, manifest, checkpoints):
    versions = checkpoints.get('families', {}).get(manifest['creature'].replace(':', '_'), {})
    candidates = {key: value for key, value in versions.items()
                  if any(item.get('regenerate') or item.get('note') for item in value.get('frames', {}).values())}
    if not candidates:
        return {}, []
    # Reuse the viewer's exact version check; a manifest-only comparison misses changed image pixels.
    sys.path.insert(0, str(HERE.parent / 'acceptance_viewer'))
    from serve import artifact_digest
    current = artifact_digest(root, (root / 'manifest.json').read_bytes(), manifest)
    return candidates.get(current, {}).get('frames', {}), sorted(set(candidates) - {current})


def classify_family(label, root, annotations, checkpoints, threshold, deadband):
    manifest = read(root / 'manifest.json')
    registration = read(root / 'registration.json')
    generation = read(root / 'generation.json')
    tier = manifest['pixels_per_logical_pixel']
    if not positive(tier):
        raise ValueError(f'{label}: invalid export tier')
    palette = next(key for key, variant in manifest['variants'].items() if variant.get('exact_base_bypass'))
    hashes = dict(manifest_sha256=digest(root / 'manifest.json'),
                  registration_sha256=digest(root / 'registration.json'))
    mapped = bindings(manifest)
    notes, stale = viewer_notes(root, manifest, checkpoints)
    frames = []
    raw_hashes = {}
    for name in sorted(manifest['frames']):
        record = registration[name]
        native_path = root / 'native_variants' / f'{name}_{palette}.png'
        restored_path = root / 'aligned_2x' / f'{name}.png'
        native = alpha_metrics(native_path, 1)
        restored = alpha_metrics(restored_path, tier)
        empty_pair = False
        if native is None or restored is None:
            with Image.open(native_path) as image:
                native_empty = image.getchannel('A').getbbox() is None
            with Image.open(restored_path) as image:
                restored_empty = image.getchannel('A').getbbox() is None
            empty_pair = native_empty and restored_empty
        source = raw_source(root, record, generation)
        if source and source.is_file() and source not in raw_hashes:
            raw_hashes[source] = digest(source)
        raw_hash = raw_hashes.get(source)
        provenance = dict(hashes, native_sha256=digest(native_path), restored_sha256=digest(restored_path),
                          raw_sha256=raw_hash)
        evidence = saved_measurements(record, native, restored, tier)
        landmarks = [item for item in evidence if item['basis'] == 'unverified_saved_landmarks']
        silhouette = [item for item in evidence if item['basis'] != 'unverified_saved_landmarks']
        # Keep independent screens visible: silhouette disagreement never overrides vetted body measurements.
        landmark_screen, silhouette_screen = screen(landmarks, threshold), screen(silhouette, threshold)
        if 'proportion_or_pose_review' in (landmark_screen, silhouette_screen):
            category = 'proportion_or_pose_review'
        elif 'uniform_scale_candidate' in (landmark_screen, silhouette_screen):
            category = 'uniform_scale_candidate'
        elif 'size_signal_needs_body_measurements' in (landmark_screen, silhouette_screen):
            category = 'size_signal_needs_body_measurements'
        elif evidence:
            category = 'no_scale_signal'
        else:
            category = 'insufficient_evidence'
        flags = []
        if not raw_hash:
            flags.append('missing_raw_source')
        if record.get('raw_sha256') and record['raw_sha256'] != raw_hash:
            flags.append('raw_hash_mismatch')
        if record.get('raw_clip'):
            flags.append('recorded_raw_clipping')
        if record.get('local_geometry'):
            flags.append('nonuniform_source_geometry')
        scale = record.get('scale')
        sampling, sampling_basis = source_sampling(record, tier, empty_pair)
        strict = root.name == 'redo_2x'
        if sampling is not None and (sampling < 2 or (strict and sampling <= 2)):
            flags.append('current_sampling_below_requirement')
        annotation = annotations.get(manifest['creature'], {}).get(name)
        blockers = [flag for flag in flags if flag != 'current_sampling_below_requirement']
        decision = solve_verified(annotation, provenance, tier, scale, sampling, strict, blockers, deadband)
        if native is None or restored is None:
            category = 'empty_endpoint' if empty_pair else 'missing_foreground_review'
            decision = dict(decision='keep_empty_endpoint' if category == 'empty_endpoint' else 'source_review',
                            proposed_export_scale=None,
                            reason='No measurable foreground at alpha>=128; only exactly empty pairs may be skipped.')
        note = notes.get(name, {})
        frames.append(dict(frame=name, batch=record.get('batch'),
                           raw_path=str(source.relative_to(REPO)) if source else None,
                           raw_rect=record.get('raw_rect'), provenance=provenance, screen=category,
                           landmark_screen=landmark_screen, silhouette_screen=silhouette_screen,
                           evidence=evidence, body_measurements_present=annotation is not None,
                           resolution=decision, source_flags=flags, current_export_scale=scale,
                           current_sampling=sampling, sampling_basis=sampling_basis,
                           sampling_requirement='>2' if strict else '>=2',
                           viewer_regeneration_flag=bool(note.get('regenerate')), viewer_note=note.get('note', ''),
                           bindings=mapped.get(name, [])))
    unknown = set(annotations.get(manifest['creature'], {})) - set(manifest['frames'])
    if unknown:
        raise ValueError(f'{label}: measurements contain unknown frames: {sorted(unknown)}')
    sheets = defaultdict(list)
    for frame in frames:
        sheets[frame['raw_path']].append(frame)
    groups = []
    for path, members in sorted(sheets.items(), key=lambda item: item[0] or ''):
        row_tops = sorted({frame['raw_rect'][1] for frame in members if frame['raw_rect']})
        rows = []
        for top in row_tops:
            row = [frame for frame in members if frame['raw_rect'] and frame['raw_rect'][1] == top]
            cells = defaultdict(list)
            for frame in row:
                vertical = [item for item in frame['evidence'] if item['axis'] == 'y' and
                            item['basis'] == 'unverified_saved_landmarks']
                if vertical:
                    best = max(vertical, key=lambda item: item['native_length'])
                    cells[tuple(frame['raw_rect'])].append(best['correction'])
            rows.append(dict(raw_top=top, frames=[frame['frame'] for frame in row], distinct_cells=len(cells),
                             median_vertical_correction=median(median(v) for v in cells.values()) if cells else None))
        groups.append(dict(raw_path=path, frames=[frame['frame'] for frame in members],
                           screens=dict(sorted(Counter(frame['screen'] for frame in members).items())), rows=rows))
    return dict(family=label, creature=manifest['creature'], root=str(root.relative_to(REPO)),
                frames=frames, sheets=groups, stale_viewer_note_versions=stale)


def compact_bindings(frame):
    return '; '.join(sorted({f"{item['action']} v{item['view']} #{item['position']}/{item['length']}"
                            + (' mirrored' if item['mirrored'] else '')
                            for item in frame['bindings']})) or 'Master only'


def write_report(report, output):
    # Refuse to overwrite a prior audit or any production directory accidentally.
    output.mkdir(parents=True, exist_ok=False)
    (output / 'classification.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    columns = ['family', 'frame', 'screen', 'decision', 'bindings', 'batch', 'raw_path',
               'current_export_scale', 'proposed_export_scale', 'current_sampling', 'source_flags',
               'viewer_regeneration_flag', 'viewer_note']
    with (output / 'frames.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for family in report['families']:
            for frame in family['frames']:
                row = {key: frame[key] for key in columns if key in frame}
                row.update(family=family['family'], decision=frame['resolution']['decision'],
                           bindings=compact_bindings(frame), source_flags='; '.join(frame['source_flags']),
                           proposed_export_scale=frame['resolution']['proposed_export_scale'])
                writer.writerow(row)
    lines = ['# MM6 deterministic scale classification', '',
             'Every current frame is included. Screens are review priorities, not accepted art diagnoses.',
             'Translation remains in the user’s viewer workflow. This run changes no artwork or viewer state.', '',
             '```json', json.dumps(report['counts'], indent=2), '```', '',
             'Full frame/action/view mapping: [frames.csv](frames.csv). Evidence and source hashes: '
             '[classification.json](classification.json).', '',
             '| Family | Frames | Scale candidate | Size signal | Proportion/pose review | No scale signal | Other |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for family in report['families']:
        counts = Counter(frame['screen'] for frame in family['frames'])
        keys = ['uniform_scale_candidate', 'size_signal_needs_body_measurements',
                'proportion_or_pose_review', 'no_scale_signal']
        values = [counts[key] for key in keys]
        lines.append(f"| {family['family']} | {len(family['frames'])} | "
                     + ' | '.join(str(v) for v in values + [len(family['frames']) - sum(values)]) + ' |')
    lines += ['', '## Interpretation', '',
              '- A scale candidate may come from silhouette bounds; it still needs verified body dimensions.',
              '- Proportion/pose review can also indicate bad landmarks, weapons, or effects. '
              'It is not a regeneration order.',
              '- No scale signal is not a clean bill of health. Missing/small/occluded features can hide defects.',
              '- New downsample factors require artifact-bound X/Y fit dimensions and a withheld check dimension.',
              '- Row summaries deduplicate source cells; they never assign a common resize to a row.',
              '- Sampling estimates do not prove visual detail. Trial export must recheck integer resize rounding, '
              'clipping, masks, sampling, proportions and motion.',
              '- Viewer offsets are ignored; notes/flags are included only for the exact '
              'current viewer artifact digest.']
    (output / 'SUMMARY.md').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path,
                        help='New report directory; existing directories are rejected')
    parser.add_argument('--measurements', type=Path,
                        help='Optional verified body-dimension JSON; see SPRITE_SCALE_DIAGNOSIS.md')
    parser.add_argument('--family', action='append', help='Exact manifest creature ID; repeat to select several')
    parser.add_argument('--screen-percent', type=float, default=2)
    parser.add_argument('--adjustment-deadband-percent', type=float, default=1)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output directory already exists; use a new checkpoint directory')
    if not positive(args.screen_percent) or not positive(args.adjustment_deadband_percent):
        parser.error('Thresholds must be finite and positive')
    annotations = read(args.measurements) if args.measurements else {}
    checkpoints_path = HERE.parent / 'acceptance_viewer/frame_fixups.json'
    checkpoints = read(checkpoints_path) if checkpoints_path.exists() else {}
    selected = [(label, root) for label, root in packages()
                if not args.family or read(root / 'manifest.json')['creature'] in args.family]
    known = {read(root / 'manifest.json')['creature'] for _, root in packages()}
    if (set(args.family or []) | set(annotations)) - known:
        parser.error('Unknown creature ID in --family or body measurements')
    families = []
    for index, (label, root) in enumerate(selected, 1):
        families.append(classify_family(label, root, annotations, checkpoints,
                                        args.screen_percent / 100, args.adjustment_deadband_percent / 100))
        print(f'{index}/{len(selected)} {label}', flush=True)
    frames = [frame for family in families for frame in family['frames']]
    counts = dict(families=len(families), frames=len(frames),
                  screens=dict(sorted(Counter(frame['screen'] for frame in frames).items())),
                  decisions=dict(sorted(Counter(frame['resolution']['decision'] for frame in frames).items())),
                  frames_with_body_measurements=sum(frame['body_measurements_present'] for frame in frames),
                  source_flags=dict(sorted(Counter(flag for frame in frames
                                                   for flag in frame['source_flags']).items())))
    report = dict(schema_version=1, counts=counts, screen_percent=args.screen_percent,
                  adjustment_deadband_percent=args.adjustment_deadband_percent,
                  classifier_sha256=digest(Path(__file__)), measurement_file_sha256=digest(args.measurements)
                  if args.measurements else None, checkpoint_sha256=digest(checkpoints_path)
                  if checkpoints_path.exists() else None, families=families)
    write_report(report, args.output)
    print(json.dumps(counts, indent=2))


if __name__ == '__main__':
    main()
