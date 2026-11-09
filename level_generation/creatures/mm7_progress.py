"""Refresh the resumable MM7 ledger without promoting files to visually accepted art."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from mm7_sampling_audit import audit

HERE = Path(__file__).resolve().parent


def run():
    path = HERE / 'mm7_progress.json'
    previous = json.loads(path.read_text()) if path.exists() else {'families': {}}
    inventory = json.loads((HERE / 'remaining_inventory.json').read_text())
    records = {}
    for family in inventory['families']:
        if family['world'] != 'mm7':
            continue
        stem = re.match(r'^[67]?m\d{3}', family['standing_images'][0]).group()
        key = 'mm7_' + stem
        root = HERE / key
        old = previous['families'].get(key, {})
        record = dict(old, label=family['label'], project=str(root.relative_to(HERE)),
                      descriptors=family['descriptors'], expected_referenced_frames=len(family['images']),
                      expected_all_native_frames=len(family.get('all_native_family_images',family['images'])),
                      unreferenced_native_frames=family.get('unreferenced_family_images',[]),
                      native_palettes=family['palettes'], missing_sources=family['missing_images'])
        if family['completed_package']:
            record.pop('blocker', None)
            record.update(status='validated', package=family['completed_package'],
                evidence='Existing package: full referenced frame coverage, current source hashes, atlas files, '
                         'validation checks and retained visual-review evidence verified by inventory. '
                         'See the project acceptance record or historical review documentation.',
                resume='Reuse accepted package; rerun only stages affected by a demonstrated defect.')
        elif old.get('status') == 'blocked':
            pass
        elif root.exists() and any(root.iterdir()):
            record.update(status='partial')
            record.setdefault('resume', 'Inspect sources.json, batches.json and generation.json; reuse accepted raw '
                              'checkpoints, finish missing base batches, clean/register, author masks, export and review.')
        else:
            record.update(status='pending', resume='Resolve descriptor actions and all family-owned native frames, '
                          'compare palettes, prepare and inspect a compact identity sheet, then use built-in imagegen.')
        if family['missing_images']:
            record.update(status='blocked', blocker='Missing native source images: '+', '.join(family['missing_images']))
        if (root / 'registration.json').exists():
            sampling = audit(root)
            record['sampling_batches_to_replace'] = [k for k,v in sampling['batches'].items()
                                                       if v['below_minimum_frames']]
            if not sampling['passed'] and record['status'] != 'blocked':
                record.update(status='partial', evidence='Prior reviewed artwork retained; actual detail gate fails.',
                    resume='Use mm7_sampling_audit.json to repack only undersampled batches into smaller complete-pose '
                           'sheets with shared transitions. Preserve raw outputs and old settings. Generate using the '
                           'accepted identity, measure 2 / registration scale >= 2, then rebuild and renew visual review.')
        records[key] = record
    result = dict(schema_version=1, updated_utc=datetime.now(timezone.utc).isoformat(),
                  run_blockers=previous.get('run_blockers', []),
                  resolved_run_blockers=previous.get('resolved_run_blockers', []),
                  scope='All 72 MM7 native monster, peasant, animal and special actor families; staged only.',
                  status_definitions=dict(pending='No restoration checkpoint yet.', partial='Work exists, completion '
                      'gates not passed.', validated='Complete coverage and package checks, with retained visual review.',
                      blocked='Concrete unresolved prerequisite or demonstrated defect; see blocker and resume.'),
                  summary=dict(Counter(r['status'] for r in records.values())), families=records)
    path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary']))


if __name__ == '__main__':
    run()
