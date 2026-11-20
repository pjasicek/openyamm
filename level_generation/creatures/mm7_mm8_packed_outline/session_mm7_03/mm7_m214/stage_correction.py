"""Activate a returned immutable revision while preserving the previous selected checkpoint."""
import argparse
import copy
import json
from pathlib import Path
import sys

REPO = Path.cwd().resolve()
SESSION = REPO / 'level_generation/creatures/mm7_mm8_packed_outline/session_mm7_03'
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_remaining/redo_2x'))
from stage_result import stage


def write(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def activate(family, job_id, version, source):
    root = SESSION / family
    out = root / 'redo_2x'
    revision_path = out / 'review' / f'{job_id}_revision_v{version}.json'
    revision = json.loads(revision_path.read_text())
    run_path = out / 'run.json'
    run = json.loads(run_path.read_text())
    index = next(i for i, j in enumerate(run['jobs']) if j['id'] == job_id)
    prior = copy.deepcopy(run['jobs'][index])
    if revision.get('status') == 'returned_selected_pending_review':
        stage(str(root.relative_to(REPO)), job_id, source)
        return
    assert len(prior['attempts']) + 1 == version
    revision['prior_job_checkpoint'] = prior
    write(revision_path, revision)
    revised = copy.deepcopy(revision['job'])
    revised['attempts'] = prior['attempts']
    revised['selected_raw'] = prior.get('selected_raw')
    run['jobs'][index] = revised
    write(run_path, run)
    stage(str(root.relative_to(REPO)), job_id, source)
    run = json.loads(run_path.read_text())
    revised = run['jobs'][index]
    attempt = revised['attempts'][-1]
    if attempt['static_screen']['failures']:
        prior['attempts'] = revised['attempts']
        run['jobs'][index] = prior
        write(run_path, run)
        revision['status'] = 'blocked_static_screen_previous_checkpoint_retained'
    else:
        revision['status'] = 'returned_selected_pending_review'
    revision['returned_raw'] = attempt['raw']
    revision['returned_sha256'] = attempt['sha256']
    write(revision_path, revision)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family')
    parser.add_argument('job')
    parser.add_argument('version', type=int)
    parser.add_argument('source')
    args = parser.parse_args()
    activate(args.family, args.job, args.version, args.source)
