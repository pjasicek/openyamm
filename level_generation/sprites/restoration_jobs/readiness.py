"""Offline, conservative readiness ledger. Historical acceptance is retained, never silently upgraded."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MIN_MASTER_SCALE = 2.0


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registration_scale(registration):
    values = registration.get('source_pixels_per_output_pixel')
    if not values or len(values) != 2 or any(not math.isfinite(v) or v <= 0 for v in values):
        return None
    if registration.get('method') == 'native_rectangle_inverse_v2':
        return [2 * v for v in values]
    if 'source_bounds' in registration and 'target_bounds' in registration:
        # Historical exporter MISNAMED this field: it stored output/master, not master/output.
        return [2 / v for v in values]
    return None


def resolution(job, state, root=HERE):
    """Recover actual extraction scale, not full sheet dimensions or enlarged output dimensions.

    Missing provenance stays unknown. Never use the frozen input grid to certify a legacy crop.
    """
    result = {}
    if not state.get('attempts'):
        return result
    latest = state['attempts'][-1]
    raw_hash = latest['raw_sha256']
    for attempt in reversed(state['attempts']):
        if attempt.get('raw_sha256') != raw_hash:
            continue
        path = (root / attempt['raw']).parent / 'checks.json'
        # Batched raw is shared; per-job checks are alongside the exported canvases.
        if attempt is latest:
            path = root / state['output_dir'] / 'checks.json'
        if path.exists():
            for key, frame in read(path).get('frames', {}).items():
                scale = registration_scale(frame.get('registration', {}))
                if key in job['assets'] and key not in result and scale:
                    result[key] = dict(scale=scale, evidence=str(path.relative_to(root)))
    if latest.get('imported_draft'):
        manifest = read(root.parent / 'concurrency_trial_10/manifest.json')
        for frame in manifest['frames'].values():
            if frame['raw_sha256'] == raw_hash and len(job['assets']) == 1:
                result[job['assets'][0]] = dict(scale=[2 / v for v in frame['registration']['scale_xy']],
                                               evidence='concurrency_trial_10/manifest.json')
    return result


def require_resolution(job, state, root=HERE):
    measured = resolution(job, state, root)
    failures = [key for key in job['assets'] if key not in measured
                or min(measured[key]['scale']) < MIN_MASTER_SCALE]
    if failures:
        raise ValueError('Master must supply >=2 pixels/native pixel in BOTH axes; missing/low evidence: '
                         + ', '.join(failures))
    return measured


def assess_job(job, state, sources, root=HERE):
    if state.get('user_excluded'):
        return {key: dict(job=job['id'], recorded_status=state['status'], ready=False, reasons=[],
                          disposition='user_excluded_keep_native', exclusion=state['user_excluded'])
                for key in job['assets']}
    from placement import validate_review
    reasons = []
    measured = resolution(job, state, root)
    if state['status'] != 'accepted':
        reasons.append('not_accepted:' + state['status'])
    directory = root / state.get('output_dir', '__missing__')
    checks_path = directory / 'checks.json'
    if not state.get('accepted_checks_sha256'):
        reasons.append('missing_current_acceptance')
    else:
        try:
            if digest(checks_path) != state['accepted_checks_sha256']:
                raise ValueError('accepted checks hash changed')
            validate_review(read(checks_path), state.get('acceptance_review', {}), job['timeline_frames'] > 1)
            if state.get('attempts') and state['attempts'][-1].get('batch_manifest'):
                from batching import validate_asset_reviews
                validate_asset_reviews(job['assets'], state['acceptance_review'])
        except (ValueError, OSError, KeyError) as error:
            reasons.append('invalid_review:' + str(error))
    if len(state.get('acceptance_review', {}).get('master_detail', '').strip()) < 20:
        reasons.append('missing_master_detail_review')
    if state.get('attempts'):
        latest = state['attempts'][-1]
        if not (root / latest['raw']).is_file() or digest(root / latest['raw']) != latest['raw_sha256']:
            reasons.append('raw_missing_or_changed')
    else:
        reasons.append('no_master')
    result = {}
    for key in job['assets']:
        issues = list(reasons)
        scale = measured.get(key, {}).get('scale')
        if scale is None:
            issues.append('master_resolution_unknown')
        elif min(scale) < MIN_MASTER_SCALE:
            issues.append('master_below_2x')
        path = directory / (key + '.png')
        try:
            if digest(path) != state.get('accepted_hashes', {}).get(key):
                issues.append('output_missing_acceptance_or_changed')
            with Image.open(path) as image:
                if (image.mode != 'RGBA' or list(image.size) != [2 * n for n in sources[key]['native_size']]
                        or not image.getchannel('A').getbbox()):
                    issues.append('invalid_output_canvas_or_alpha')
        except OSError:
            issues.append('output_missing')
        result[key] = dict(job=job['id'], recorded_status=state['status'], ready=not issues,
                           reasons=issues, master_resolution=measured.get(key),
                           file=str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path))
    return result


def build_ledger(root=HERE):
    sources = read(root / 'sources.json')
    assets = {}
    for brief in read(root / 'index.json'):
        job = read(root / 'jobs' / (brief['id'] + '.json'))
        path = root / 'state' / (job['id'] + '.json')
        state = read(path) if path.exists() else dict(status=job['status'], attempts=[])
        assets.update(assess_job(job, state, sources, root))
    sorpigal = REPO / 'level_generation/decorations/mm6_new_sorpigal'
    registration = read(sorpigal / 'registration.json')
    generation = read(sorpigal / 'generation.json')
    shared_master = {'6tree06': 'food_tree', 'tree06a': 'food_tree', 'swrdstn': 'sword_stone',
                     'swrdstx': 'sword_stone', **{f'shp{i}': 'ship' for i in range(5)}}
    for key, source in sources.items():
        if 'reuse' in source:
            path = REPO / source['reuse']['path']
            scale = [2 / v for v in registration[path.stem]['scale_xy']]
            issues = []
            master = generation[shared_master.get(path.stem, path.stem)]
            raw = sorpigal / master['raw']
            if not raw.is_file() or digest(raw) != master['raw_sha256']:
                issues.append('raw_missing_or_changed')
            review_path = root / 'audit/reuse_reviews' / (key + '.json')
            if review_path.exists():
                receipt = read(review_path)
                if (receipt.get('raw_sha256') != master['raw_sha256']
                        or receipt.get('output_sha256') != source['reuse']['sha256']
                        or receipt.get('registration_sha256') != digest(sorpigal / 'registration.json')):
                    issues.append('reused_review_binding_changed')
                from placement import CHECKS_VERSION, validate_review
                try:
                    validate_review(dict(checks_version=CHECKS_VERSION, warnings=[]), receipt.get('review', {}), False)
                except ValueError as error:
                    issues.append('invalid_review:' + str(error))
            else:
                issues.append('missing_master_detail_review')
            if min(scale) < MIN_MASTER_SCALE:
                issues.append('master_below_2x')
            if not path.is_file() or digest(path) != source['reuse']['sha256']:
                issues.append('reused_output_missing_or_changed')
            assets[key] = dict(recorded_status='reused_historical_acceptance', ready=not issues, reasons=issues,
                               master_resolution=dict(scale=scale, evidence='Sorpigal registration.json'),
                               file=source['reuse']['path'])
        elif 'keep_native' in source:
            assets[key] = dict(recorded_status='native_placeholder', ready=False, reasons=[],
                               disposition='retain_native_placeholder')
    files = []
    for entry in read(root / 'coverage.json')['referenced']:
        appearances = [assets[key] for key in entry['assets']]
        retained = all(a.get('disposition') == 'retain_native_placeholder' for a in appearances)
        excluded = all(a.get('disposition') == 'user_excluded_keep_native' for a in appearances)
        issues = sorted({issue for a in appearances for issue in a['reasons']})
        source_path = REPO / entry['path']
        if not source_path.is_file() or digest(source_path) != entry['sha256']:
            issues.append('native_source_missing_or_changed')
        ready = all(a['ready'] for a in appearances) and not issues
        files.append(dict(path=entry['path'], assets=entry['assets'], ready=ready, reasons=issues,
                          disposition='user_excluded_keep_native' if excluded and not issues
                          else 'retain_native_placeholder' if retained and not issues
                          else 'restored_ready' if ready else 'restoration_pending'))
    by_artifact = {str((REPO / a['file']).resolve()): a for a in assets.values() if a.get('file')}
    supplemental = root / 'supplemental/noose_views'
    supplemental_review = read(supplemental / 'visual_review.json')
    supplemental_checks = read(supplemental / 'checks.json')
    for entry in read(root / 'triage.json'):
        path = root / 'state' / (entry['id'] + '.json')
        state = read(path) if path.exists() else {}
        disposition = state.get('disposition', 'unresolved')
        issues, ready = [], False
        if state.get('status') != 'resolved':
            issues.append('triage_unresolved')
        artifact = state.get('artifact')
        if disposition in ('restored', 'alias'):
            if not artifact or not Path(artifact).is_file() or digest(Path(artifact)) != state['artifact_sha256']:
                issues.append('triage_artifact_missing_or_changed')
            elif str(Path(artifact).resolve()) in by_artifact:
                target = by_artifact[str(Path(artifact).resolve())]
                issues.extend(target['reasons'])
                ready = target['ready']
            elif Path(artifact).parent == supplemental:
                frame = supplemental_checks['frames'].get(entry['name'], {})
                scale = registration_scale(frame.get('registration', {}))
                if not scale or min(scale) < MIN_MASTER_SCALE:
                    issues.append('master_below_2x_or_unknown')
                if len(supplemental_review.get('master_detail', '').strip()) < 20:
                    issues.append('missing_master_detail_review')
                if digest(supplemental / 'checks.json') != supplemental_review.get('checks_sha256'):
                    issues.append('supplemental_checks_changed')
                if digest(supplemental / 'raw.png') != supplemental_checks.get('raw_sha256'):
                    issues.append('supplemental_raw_changed')
                if frame.get('sha256') != state['artifact_sha256']:
                    issues.append('supplemental_output_changed')
                ready = not issues
            else:
                issues.append('triage_readiness_evidence_unknown')
        source_path = REPO / entry['path']
        if not source_path.is_file() or digest(source_path) != entry['sha256']:
            issues.append('native_source_missing_or_changed')
        ready = ready and not issues
        retained = disposition in ('unused_keep_native', 'utility_keep_native') and not issues
        final_disposition = disposition if retained else 'restored_ready' if ready else 'restoration_pending'
        files.append(dict(path=entry['path'], ready=ready, reasons=issues, triage=entry['id'],
                          disposition=final_disposition))
    inventory = read(root.parent / 'inventory.json')
    creature_classes = ('creature', 'unused_creature_pose')
    creatures = [f['path'] for f in inventory['files'] if f['classification'] in creature_classes
                 and f['path'].startswith('assets_dev/engine/sprites/')]
    native_roots = (REPO / 'assets_dev/engine/sprites', REPO / 'assets_dev/_legacy/sprites_original')
    actual = {str(p.relative_to(REPO)) for directory in native_roots if directory.exists()
              for p in directory.iterdir() if p.suffix.lower() == '.bmp'}
    accounted = set(creatures) | {f['path'] for f in files}
    counts = dict(Counter(f['disposition'] for f in files))
    pending = Counter()
    for entry in files:
        if entry['disposition'] != 'restoration_pending':
            continue
        issues = entry['reasons']
        if any(issue.startswith('not_accepted:') for issue in issues):
            reason = 'not_accepted'
        elif 'master_below_2x' in issues:
            reason = 'master_below_2x'
        elif 'missing_master_detail_review' in issues:
            reason = 'missing_master_detail_review'
        elif 'master_resolution_unknown' in issues:
            reason = 'missing_resolution_provenance'
        else:
            reason = 'other_evidence_failure'
        pending[reason] += 1
    return dict(schema_version=1, updated_utc=datetime.now(timezone.utc).isoformat(),
                policy='Recorded visual acceptance + explicit master detail evidence + >=2x BOTH axes; '
                       'hash-checked assets. This audit is not a new visual review or runtime installation.',
                summary=dict(total_folder_files=len(actual), creature_files=len(creatures),
                             non_creature_files=len(files), **counts,
                             pending_by_primary_reason=dict(pending),
                             unaccounted_files=sorted(actual - accounted), missing_files=sorted(accounted - actual)),
                assets=assets, files=files)


def write_ledger(root=HERE):
    report = build_ledger(root)
    path = root / 'readiness.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    counts = report['summary']
    lines = ['# Non-creature restoration readiness', '',
             'Generated by `python3 level_generation/sprites/restoration_jobs/readiness.py`.', '',
             report['policy'], '', '| File disposition | Count |', '| --- | ---: |']
    lines.extend(f'| {key} | {value} |' for key, value in counts.items() if isinstance(value, int))
    lines += ['', 'Pending files, grouped by the first blocking reason (a file may have additional issues):', '',
              '| Primary blocker | Files |', '| --- | ---: |']
    lines.extend(f'| {key} | {value} |' for key, value in counts['pending_by_primary_reason'].items())
    lines += ['', 'All counts are original BMP files, not jobs, deduplicated appearances or map placements.',
              'Historical state/acceptance records are preserved. `readiness.json` records per-asset reasons.',
              'Missing detail evidence calls for review of existing masters, not automatic regeneration.',
              'Only missing/defective art or insufficient master sampling justifies new generation.', '']
    (root / 'READINESS.md').write_text('\n'.join(lines))
    return counts


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(write_ledger(), indent=2))
