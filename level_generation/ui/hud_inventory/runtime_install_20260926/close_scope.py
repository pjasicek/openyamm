"""Record unused-source retirement separately from image acceptance in the canonical queue."""
import fcntl
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
HUD = OUT.parent
ROOT = HUD.parents[2]
sys.path.insert(0, str(HUD))
from queue import Queue, save


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    with (HUD / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        q = Queue()
        approved = json.loads((OUT / 'accepted.json').read_text())['records']
        audit_path = HUD / 'finalization_20260926/icon_coverage.json'
        audit = json.loads(audit_path.read_text())
        audit_hash = sha(audit_path)
        by_id = {r['target']: r for r in audit['files'] if r['target']}
        dispositions = {}
        reasons = {'excluded_legacy_ui', 'excluded_unreferenced_art',
                   'unused_equipment_variant', 'metadata_only_head_or_beard'}
        for target, contract in q.targets.items():
            if target in approved:
                dispositions[target] = 'accepted_installed'
            elif contract['namespace'] == 'worlds/mm9':
                dispositions[target] = 'retained_mm9_outside_scope'
            else:
                row = by_id[target]
                assert row['status'] in reasons, (target, row)
                dispositions[target] = 'archived_unused'
                q.state.setdefault('retired_targets', {})[target] = dict(status='archived_unused',
                    reason=row['status'], source_archive=str(OUT / 'source_archive.json'),
                    authority='User-authorized retirement of originals unused by current runtime, 2026-09-26',
                    evidence_hashes={str(audit_path):audit_hash})
        summary = dict(Counter(dispositions.values()))
        assert summary == dict(accepted_installed=9920, retained_mm9_outside_scope=936, archived_unused=3924)
        save(OUT / 'scope_disposition.json', dict(summary=summary, targets=dispositions,
            policy='Retired targets are NOT accepted images. MM9 remains a separate retained-native scope.'))
        save(q.state_path, q.state)
        print(json.dumps(summary))


if __name__ == '__main__':
    main()
