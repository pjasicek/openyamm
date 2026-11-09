"""Read-only scan of accepted exports; writes a review queue, never a regeneration queue."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from PIL import Image

from placement import inspect_placement

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def main():
    sources = read(HERE / 'sources.json')
    jobs = []
    for job in read(HERE / 'index.json'):
        state_path = HERE / 'state' / (job['id'] + '.json')
        if not state_path.exists():
            continue
        state = read(state_path)
        if state['status'] != 'accepted':
            continue
        directory = HERE / state['output_dir']
        old = read(directory / 'checks.json')
        flags = [w for w in old.get('warnings', [])
                 if 'generated_detail_below_2x_target' not in w]
        frames = {}
        for key in job['assets']:
            with Image.open(HERE / sources[key]['native']) as native, Image.open(directory / (key + '.png')) as enhanced:
                placement, warnings = inspect_placement(native, enhanced)
            if warnings:
                frames[key] = placement
                flags.extend(key + ': ' + w for w in warnings)
        reviewed = []
        if (state.get('accepted_checks_sha256') == hashlib.sha256((directory / 'checks.json').read_bytes()).hexdigest()
                and state.get('acceptance_review')):
            decisions = state['acceptance_review'].get('warnings', {})
            reviewed = [flag for flag in set(flags) if len(decisions.get(flag, '').strip()) >= 20]
            flags = [flag for flag in flags if flag not in reviewed]
        jobs.append(dict(id=job['id'], label=job['label'], output_dir=state['output_dir'],
                         current_acceptance=bool(state.get('accepted_checks_sha256')),
                         flags=sorted(set(flags)), reviewed_flags=sorted(reviewed), measurements=frames,
                         disposition='needs_visual_review' if flags else 'no_automatic_geometry_flag'))
    result = dict(purpose='Review existing masters/exports; flags do not authorize blanket regeneration.',
                  summary=dict(accepted_scanned=len(jobs), flagged_jobs=sum(bool(j['flags']) for j in jobs),
                               legacy_acceptance=sum(not j['current_acceptance'] for j in jobs),
                               disposition_counts=dict(Counter(j['disposition'] for j in jobs))), jobs=jobs)
    output = HERE / 'audit' / 'placement_review.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(**result['summary'], file=str(output)), indent=2))


if __name__ == '__main__':
    main()
