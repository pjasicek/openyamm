"""Record a supplied visual-review decision after the agent inspects a compact contact."""
import argparse
import json
import shutil
from datetime import datetime, timezone
from process import ROOT, queue, save


def run(keys, note):
    jobs = json.loads((ROOT / 'compact_jobs.json').read_text())
    records = json.loads((ROOT / 'registration.json').read_text())
    for key in keys:
        job = jobs['jobs'][key]
        assert job['status'] in ['processed_unreviewed', 'accepted_visual']
        assert job['sampling'] >= 2
        contact = ROOT / 'review' / (key + '_combined.png')
        assert contact.is_file()
        digest = queue.sha(contact)
        frozen = ROOT / 'checkpoints/review_contacts' / (key + '_' + digest + '.png')
        frozen.parent.mkdir(exist_ok=True)
        if not frozen.exists():
            shutil.copy2(contact, frozen)
        acceptance = ROOT / 'checkpoints' / (key + '_acceptance.json')
        if acceptance.exists():
            previous = ROOT / 'checkpoints/review_contacts' / (key + '_' + queue.sha(acceptance) + '.json')
            if not previous.exists():
                shutil.copy2(acceptance, previous)
        job.update(status='accepted_visual', visual_review=note)
        save(ROOT / 'checkpoints' / (key + '_acceptance.json'), {
            'status': 'accepted_visual', 'reviewed_utc': datetime.now(timezone.utc).isoformat(),
            'note': note, 'generation': job['generation'],
            'contact': {'path': str(frozen.relative_to(ROOT)), 'sha256': digest},
            'sampling': job['sampling'], 'frozen_calibration': job['frozen_calibration']})
        for name in job['frames']:
            if name in records and records[name]['batch'] == key:
                records[name]['status'] = 'accepted_visual'
    save(ROOT / 'compact_jobs.json', jobs)
    save(ROOT / 'registration.json', records)
    save(ROOT / 'calibration_registration.json', records)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('jobs', nargs='+')
    parser.add_argument('--note', required=True)
    args = parser.parse_args()
    run(args.jobs, args.note)
