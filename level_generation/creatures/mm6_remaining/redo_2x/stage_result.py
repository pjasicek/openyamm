"""Persist one built-in generation result without accepting it or touching installed art."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sheet_checks import screen


def stage(project, job_id, source):
    out = Path(project) / 'redo_2x'
    # Several independent image calls can finish together. Serialize this shared ledger mutation.
    with (out / '.stage.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        stage_locked(out, job_id, source)


def stage_locked(out, job_id, source):
    path = out / 'run.json'
    run = json.loads(path.read_text())
    job = next(j for j in run['jobs'] if j['id'] == job_id)
    digest = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    for attempt in job['attempts']:
        if attempt['sha256'] == digest:
            assert hashlib.sha256(Path(attempt['raw']).read_bytes()).hexdigest() == digest
            print(attempt['raw'])
            return
    version = len(job['attempts']) + 1
    destination = out / 'raw' / ('%s_v%d.png' % (job_id, version))
    if destination.exists():
        # Recover a completed copy whose ledger write was interrupted. Never overwrite different artwork.
        assert hashlib.sha256(destination.read_bytes()).hexdigest() == digest, destination
    else:
        shutil.copy2(source, destination)
    checks = screen(destination, job['cell_native_size'], [job['columns'], job['rows']], len(job['frames']))
    processing_path = out / 'processing.json'
    policy = json.loads(processing_path.read_text()).get('whole_animation_resolution_policy') if processing_path.exists() else None
    if policy and policy.get('allow_below_2x') and run.get('method') == 'packed_complete_animation_outline_only_detailed_appearance':
        resolution_flags = [flag for flag in checks['failures'] if flag in (
            'Delivered grid budget below 2x; replan or verify corrected cell registration',
            'Measured raw-to-native registration below 2x')]
        checks['failures'] = [flag for flag in checks['failures'] if flag not in resolution_flags]
        checks['warnings'].extend(resolution_flags)
        checks['status'] = 'blocked' if checks['failures'] else 'static_screen_passed_visual_review_required'
        checks['whole_animation_resolution_policy'] = policy
    provenance = dict(raw=str(destination), original_output=source,
                      sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                      actual_size=checks['delivered_size'],
                      prompt=job['prompt'], prompt_sha256=hashlib.sha256(Path(job['prompt']).read_bytes()).hexdigest(),
                      references=[dict(path=p, sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
                                  for p in job['references']],
                      status='generated_pending_validation')
    provenance['static_screen'] = checks
    job['attempts'].append(provenance)
    if not checks['failures']:
        job['selected_raw'] = str(destination)
        job['status'] = 'partial'
    else:
        provenance['status'] = 'blocked_static_screen'
        if not job.get('selected_raw'):
            job['status'] = 'blocked'
    temporary = out / 'run.json.tmp'
    temporary.write_text(json.dumps(run, indent=2) + '\n')
    temporary.replace(path)
    print(json.dumps(dict(raw=str(destination), status=checks['status'], failures=checks['failures'],
                          warnings=checks['warnings'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('job')
    parser.add_argument('source')
    args = parser.parse_args()
    stage(args.project, args.job, args.source)
