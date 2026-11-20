"""Session-only alpha ownership checks for visually inspected complete returns."""
import argparse
from PIL import Image
from process_session import REPO, SESSION, connected_cells, read, sha, write


def audit(family):
    root = SESSION / family
    assert not (root / 'review/acceptance.json').exists()
    run = read(root / 'run.json')
    path = root / 'processing.json'
    processing = read(path) if path.exists() else {}
    policies = processing.setdefault('component_seed_policy', {})
    failures = processing.setdefault('processing_failures', [])
    for job in run['jobs']:
        attempts = [a for a in job['attempts'] if a['status'] == 'returned'
                    and a.get('visual_screen', {}).get('status') != 'rejected']
        if not attempts:
            continue
        attempt = attempts[-1]
        raw_path = REPO / attempt['raw_path']
        digest = sha(raw_path)
        assert digest == attempt['raw_sha256']
        if job['id'] in policies:
            if policies[job['id']]['raw_sha256'] == digest:
                continue
            processing.setdefault('superseded_component_seed_policies', []).append(
                dict(job=job['id'], **policies.pop(job['id'])))
        raw = Image.open(raw_path).convert('RGBA')
        outcomes = {}
        for threshold in (1, 4, 16, 32, 64):
            try:
                frames = connected_cells(raw, job, seed_alpha_threshold=threshold)
                outcomes[threshold] = len(frames)
                if threshold == 1:
                    break
            except (AssertionError, ValueError) as error:
                outcomes[threshold] = str(error)
        passing = [t for t, count in outcomes.items() if count == len(job['frames'])]
        if not passing:
            failures.append(dict(job=job['id'], raw_sha256=digest, ownership_trials=outcomes))
            print(job['id'], 'UNRESOLVED', outcomes, flush=True)
            continue
        threshold = min(passing)
        if threshold != 1:
            reason = (f'Alpha=1 fringe joins whole-sheet bodies. Compared seeds: {outcomes}; '
                      f'least passing {threshold} ownership seed chosen. All original foreground '
                      'and soft alpha retained. Body count requires separate visual pose review.')
            policies[job['id']] = dict(threshold=threshold, raw_sha256=digest, reason=reason)
            failures.append(dict(job=job['id'], raw_sha256=digest, ownership_trials=outcomes,
                                 resolution=reason))
            print(job['id'], threshold, outcomes, flush=True)
    write(path, processing)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family')
    audit(parser.parse_args().family)
