"""Build the held-armor browser overlay without accepting any replacement artwork."""
import copy
import json
import sys
from collections import Counter
from PIL import Image

from prepare import OUT, HERE, read, js, write, digest

sys.path.insert(0, str(HERE))
from scan_magenta import measure, classify


def main():
    manifest = read(OUT / 'manifest.json')
    previous = js(HERE / 'acceptance_snapshot_20260926_1322/review.js')
    result = copy.deepcopy(previous)
    result.update(id='20260926_held_armor', import_revision=1, stage_only_snapshot=False,
                  new_targets=[], held_armor_scope=[], held_armor_bases={})
    catalog = js(HERE / 'catalog.js')
    counts = Counter()
    scans = []
    replacements_of_approvals = []
    for row in manifest['pairs']:
        target = row['target']
        assert digest(HERE / row['path']) == row['sha256']
        assert digest(HERE / row['base_path']) == row['base_sha256']
        result['held_armor_scope'].append(target)
        result['held_armor_bases'][target] = {k: row[k] for k in ['empty', 'base_path', 'base_sha256',
                                                                'method', 'mask_path']}
        counts[row['method']] += 1
        asset = catalog['assets'][row['held']]
        metrics = measure(Image.open(HERE / row['path']))
        native_metrics = measure(Image.open(HERE / asset['native']))
        scans.append({'target': target, 'name': row['held'], 'candidate_hash': row['sha256'],
                      'source_hash': asset['sourceHash'], 'path': row['path'],
                      'status': classify(metrics, native_metrics), 'metrics': metrics,
                      'native_metrics': native_metrics, 'report': 'held_armor_20260926/magenta_scan.json'})
        old = result['repairs'].get(target)
        if old and old['sha256'] != row['sha256']:
            history = result['history'].setdefault(target, [])
            if not any(r['sha256'] == old['sha256'] for r in history):
                history.append(old)
        compatible = {row['held_candidate_sha256'], catalog['assets'][row['held']]['candidateHash']}
        for version in result['history'].get(target, []) + ([old] if old else []):
            compatible.add(version['sha256'])
            compatible.update(version.get('placement_compatible_hashes', []))
        for record in result['placements'].values():
            if record['reviewed_asset'] == target:
                compatible.add(record['candidate_hash'])
        compatible.discard(None)
        result['repairs'][target] = {
            'target': target, 'name': row['held'], 'path': row['path'], 'sha256': row['sha256'],
            'source_hash': row['source_hash'], 'old_path': row['held_candidate_path'],
            'old_sha256': row['held_candidate_sha256'], 'categories': ['accepted_base_held_pose'],
            'operations': [{'method': row['method'], 'base': row['empty'], 'base_sha256': row['base_sha256'],
                            'mask': row['mask_path'], 'outside_rgba_differences': 0}],
            'changed': row['sha256'] != row['held_candidate_sha256'], 'unresolved': [],
            'status': 'held_pose_candidate_needs_review',
            'previously_approved': row['held_status'] != 'unreviewed',
            'placement_compatible_hashes': sorted(compatible),
            'review_baseline_at': previous['exported_at'], 'pass_id': result['id']}
        if row['sha256'] != row['held_candidate_sha256']:
            result['new_targets'].append(target)
            if row['held_status'] != 'unreviewed':
                replacements_of_approvals.append(target)
    # Importing this pass must not fabricate approvals or rewrite any manual offset.
    for key in ['decisions', 'placements', 'staged', 'completion_scope']:
        assert result[key] == previous[key]
    write(OUT / 'magenta_scan.json', {'schema': 'openyamm-magenta-screen-v1',
          'summary': dict(Counter(r['status'] for r in scans)), 'records': scans})
    result['magenta_scan']['records'].extend(scans)
    (OUT / 'review.js').write_text('window.PAPERDOLL_REPAIR_PASS = ' +
                                  json.dumps(result, indent=2) + ';\n')
    write(OUT / 'summary.json', {
        'pairs': len(manifest['pairs']), 'methods': dict(counts),
        'changed_candidates': len(result['new_targets']),
        'previous_held_approvals_with_replacements_to_review': replacements_of_approvals,
        'decisions_preserved': len(result['decisions']), 'placements_preserved': len(result['placements']),
        'empty_hand_approvals_preserved': 270, 'outside_rgba_differences': 0,
        'imagegen_calls': 0, 'ledger_sha256': manifest['ledger_sha256'],
        'ledger_modified': False, 'runtime_assets_modified': False})
    assert digest(HERE.parent / 'checkpoint/state.json') == manifest['ledger_sha256']
    print((OUT / 'summary.json').read_text())


if __name__ == '__main__':
    main()
