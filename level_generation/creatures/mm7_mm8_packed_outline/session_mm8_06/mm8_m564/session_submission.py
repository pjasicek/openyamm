"""Session-local attachment/provenance orchestration; no image API or shared-file writes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

REPO = Path.cwd().resolve()
STAGE = REPO / 'level_generation/creatures/mm7_mm8_packed_outline/session_mm8_06'
HEADER = 'TASK CONTEXT — MM8 FANTASY-GAME ASSET RESTORATION:'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def submit(family, job_id):
    root = STAGE / family
    path = root / 'redo_2x/run.json'
    run = json.loads(path.read_text())
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    refs = [(REPO / value).resolve() for value in job['references']]
    assert len(refs) in (2, 3)
    assert refs[0].name == job_id + '_native.png'
    assert refs[1].name == job_id + '_outline.png'
    assert all(value.is_file() and value.is_relative_to(root) for value in refs)
    assert len(job['reference_roles']) == len(refs)
    assert len(refs) == 3 or job.get('bootstrap_exception')
    for item in job['prepared_assets']:
        assert digest(REPO / item['path']) == item['sha256'], item['path']
    color = Image.open(refs[0]).convert('RGBA')
    outline = Image.open(refs[1]).convert('RGB')
    assert color.size == outline.size
    inside = np.array(color.getchannel('A'))[::2, ::2] > 0
    boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
    expected = np.full((*inside.shape, 3), 255, np.uint8)
    expected[boundary] = 0
    expected = Image.fromarray(expected).resize(color.size, Image.Resampling.NEAREST)
    assert np.array_equal(np.array(expected), np.array(outline)), 'Outline does not match native alpha'
    prompt_path = REPO / job['prompt']
    prompt = prompt_path.read_text()
    assert prompt.startswith(HEADER)
    arguments = dict(prompt=prompt, referenced_image_paths=[str(value) for value in refs],
                     transparent_background=True)
    job.setdefault('submissions', []).append(dict(
        submitted_utc=datetime.now(timezone.utc).isoformat(), actual_tool_arguments=arguments,
        input_assets=[dict(path=str(value), role=role, sha256=digest(value))
                      for value, role in zip(refs, job['reference_roles'])],
        prompt_sha256=digest(prompt_path), bootstrap_exception=len(refs) == 2,
        status='submitted_waiting_for_imagegen'))
    save(path, run)
    return dict(family=family, job=job_id, args=arguments)


def complete(family, job_id, raw=None, error=None):
    root = STAGE / family
    path = root / 'redo_2x/run.json'
    run = json.loads(path.read_text())
    job = next(job for job in run['jobs'] if job['id'] == job_id)
    submission = job['submissions'][-1]
    if error:
        submission.update(status='failed_imagegen', error=error)
        job['status'] = 'failed_imagegen'
    else:
        sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_remaining/redo_2x'))
        from stage_result import stage
        stage(str(root.relative_to(REPO)), job_id, raw)
        run = json.loads(path.read_text())
        job = next(job for job in run['jobs'] if job['id'] == job_id)
        attempt = job['attempts'][-1]
        submission = job['submissions'][-1]
        submission.update(status='returned_pending_visual_validation', raw=attempt['raw'],
                          raw_sha256=attempt['sha256'], delivered_size=attempt['actual_size'])
        attempt['actual_submitted_inputs'] = submission['input_assets']
        attempt['bootstrap_exception'] = submission['bootstrap_exception']
    save(path, run)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('submit', 'complete'))
    parser.add_argument('family', choices=[f'mm8_m{n}' for n in range(564, 593, 4)])
    parser.add_argument('job')
    parser.add_argument('--raw')
    parser.add_argument('--error')
    args = parser.parse_args()
    if args.operation == 'submit':
        print(json.dumps(submit(args.family, args.job)))
    else:
        assert bool(args.raw) != bool(args.error)
        complete(args.family, args.job, args.raw, args.error)
