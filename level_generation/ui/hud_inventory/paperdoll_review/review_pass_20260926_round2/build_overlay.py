"""Publish this slice's latest review defaults and retain earlier candidate history."""
import json
import sys
from collections import Counter
from PIL import Image
from prepare import HERE, OUT, read, write

sys.path.insert(0, str(HERE))
from scan_magenta import measure, classify


def main():
    previous = json.loads((OUT/'previous_review.js').read_text().split('=', 1)[1].strip().rstrip(';'))
    latest = read(OUT/'review.original.json')
    new = read(OUT/'repairs.json')['results']
    placements = read(OUT/'placements.effective.json')['placements']
    repairs = {}
    history = {}
    for target in previous['repairs'].keys() | new.keys():
        prior = previous['repairs'].get(target)
        records = ([prior] if prior else []) + ([new[target]] if target in new else [])
        compatible = set()
        for record in records:
            compatible.update([record['old_sha256'], record['sha256']])
            compatible.update(record.get('placement_compatible_hashes', []))
        current = dict(records[-1])
        for placement in placements.values():
            if placement['reviewed_asset'] == target and placement['source_hash'] == current['source_hash']:
                compatible.add(placement['candidate_hash'])
        current['placement_compatible_hashes'] = sorted(compatible)
        current.setdefault('review_baseline_at', previous['exported_at'])
        current.setdefault('pass_id', previous['id'])
        repairs[target] = current
        if prior and target in new and prior['sha256'] != current['sha256']:
            history[target] = [{**prior, 'placement_compatible_hashes': sorted(compatible)}]
    payload = {
        'id': '20260926_round2', 'import_revision': 2, 'exported_at': latest['exported_at'],
        'decisions': latest['decisions'], 'placements': placements,
        'staged': read(OUT/'stage_manifest.json')['records'], 'repairs': repairs,
        'history': history, 'new_targets': sorted(new),
    }
    scans = []
    for target, repair in new.items():
        image = Image.open(HERE/repair['path'])
        native = Image.open(HERE/'native'/(target+'.png'))
        metrics, native_metrics = measure(image), measure(native)
        scans.append({'target': target, 'name': repair['name'], 'candidate_hash': repair['sha256'],
                      'source_hash': repair['source_hash'], 'path': repair['path'],
                      'status': classify(metrics, native_metrics), 'metrics': metrics, 'native_metrics': native_metrics,
                      'report': str((OUT/'magenta_scan.json').relative_to(HERE))})
    scan = {'schema': 'openyamm-magenta-screen-v1', 'records': scans,
            'summary': dict(Counter(r['status'] for r in scans))}
    write(OUT/'magenta_scan.json', scan)
    payload['magenta_scan'] = scan
    (OUT/'review.js').write_text('window.PAPERDOLL_REPAIR_PASS = '+json.dumps(payload, separators=(',', ':'))+';\n')
    write(OUT/'overlay_summary.json', {'new_targets': len(new), 'retained_repairs': len(repairs)-len(new),
                                     'prior_candidate_history': len(history)})
    print(read(OUT/'overlay_summary.json'))


if __name__ == '__main__':
    main()
