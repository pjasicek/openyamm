"""Validate the completed owned batch and render only current exports that passed."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

project = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project / 'scripts'))
import review_items

designs = json.loads((project / 'designs.json').read_text())
external = {entry['design'] for entry in json.loads((project / 'ledger.json').read_text())
            if entry.get('external_install')}
batch = json.loads((project / 'review/bake_batch_latest.json').read_text())
assert len(batch) == len(designs) == 95 and set(batch) == set(designs)
results = {}
valid = []
for name, status in batch.items():
    results[name] = dict(status)
    if not status['baked']:
        continue
    export = project / 'work/codex_tex' / f'{name}_export.glb'
    assert hashlib.sha256(export.read_bytes()).hexdigest() == status['export_sha256'], name
    check = subprocess.run(['python3', str(project / 'scripts/check_exports.py'), name],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log = project / 'review' / f'{name}_export_check.log'
    log.write_text(check.stdout)
    results[name].update(valid=check.returncode == 0, validation_log=str(log.relative_to(project)))
    if name in external:
        results[name]['external_retained'] = True
    elif check.returncode == 0:
        valid.append(name)
    else:
        results[name]['error'] = check.stdout.strip().splitlines()[-1]
(project / 'review/final_validation.json').write_text(json.dumps(results, indent=2) + '\n')
assert valid
print('FINAL_REVIEW', len(valid), 'valid candidates; failures retained in final_validation.json', flush=True)
sys.argv = [__file__, '--', 'codex_tex', *valid]
review_items.main()
