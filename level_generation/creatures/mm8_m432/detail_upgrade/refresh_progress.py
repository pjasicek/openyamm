"""Refresh detail-stage coverage without declaring the whole family validated."""
from pathlib import Path
import collections
import datetime
import hashlib
import json

D = Path(__file__).resolve().parent
jobs = json.loads((D / 'jobs.json').read_text())
palette_path = D / 'variant_acceptance.json'
palettes = json.loads(palette_path.read_text()) if palette_path.exists() else {}

def checked(record):
    return all((D / p).is_file() and hashlib.sha256((D / p).read_bytes()).hexdigest() == sha
               for p, sha in record['hashes'].items())

accepted = set(jobs['seeded_trial_frames'])
trial = json.loads((D / 'review/trial_acceptance.json').read_text())
assert checked({'hashes': trial['artifact_hashes']})
for job in jobs['jobs'].values():
    if job['status'] == 'accepted_detail_and_placement':
        assert checked(job['visual_acceptance'])
        accepted.update(job['frames'])
palette_frames = set()
for key, record in palettes.items():
    assert checked(record), ('palette acceptance changed', key)
    palette_frames.update(record['frames'])
path = D.parents[1] / 'mm8_remaining/progress.json'
ledger = json.loads(path.read_text())
entry = ledger['families']['m432']
entry['status'] = 'partial'
entry['detail_refinement'].update({
    'accepted_detail_and_placement_frames': len(accepted),
    'accepted_palette_frames': len(palette_frames),
    'remaining_detail_frames': 160 - len(accepted),
    'job_states': dict(collections.Counter(j['status'] for j in jobs['jobs'].values())),
})
ledger['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
path.write_text(json.dumps(ledger, indent=2) + '\n')
print(f'Detail/placement: {len(accepted)}/160; palettes: {len(palette_frames)}/160. Family partial.')
