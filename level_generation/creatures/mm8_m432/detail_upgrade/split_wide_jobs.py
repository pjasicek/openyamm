"""Split pending wide strips without changing their common native crop or scale."""
from pathlib import Path
import copy
import hashlib
import json
import math
from PIL import Image

D = Path(__file__).resolve().parent
path = D / 'jobs.json'
data = json.loads(path.read_text())
snapshot = D / 'checkpoints/jobs_before_wide_split.json'
assert not snapshot.exists(), 'One-time migration already recorded'
snapshot.parent.mkdir(exist_ok=True)
snapshot.write_bytes(path.read_bytes())
new_jobs = {}
retired = {}
for key, job in data['jobs'].items():
    width, height = job['reference_cell_size_px']
    size = max(1, math.floor(3 * height / width))
    if job['status'] != 'pending' or job['columns'] <= size:
        new_jobs[key] = job
        continue
    retired[key] = copy.deepcopy(job)
    retired[key]['reason'] = ('Wide output changed the requested aspect/layout; split equal cells '
                              'to stay within 3:1 while preserving the recorded native crop.')
    raw = D / 'raw' / (key + '_v1.png')
    if raw.exists():
        retired[key]['rejected_raw'] = {
            'path': str(raw.relative_to(D)),
            'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
            'reason': 'Generated layout differs from native reference; not accepted or processed.',
        }
    for index, start in enumerate(range(0, job['columns'], size)):
        end = min(start + size, job['columns'])
        child_key = key + '_part' + str(index + 1)
        child = copy.deepcopy(job)
        child['frames'] = job['frames'][start:end]
        child['columns'] = end - start
        child['split_from'] = key
        child['references'] = []
        for reference in job['references']:
            if reference.startswith('references/'):
                image = Image.open(D / reference)
                assert image.size == (width * job['columns'], height)
                destination = reference.replace(key, child_key)
                image.crop((start * width, 0, end * width, height)).save(D / destination)
                child['references'].append(destination)
            else:
                child['references'].append(reference)
        prompt = (D / job['prompt']).read_text()
        prompt = prompt.replace(', '.join(job['frames']), ', '.join(child['frames']))
        prompt = prompt.replace(f'these {job["columns"]} exact', f'these {end-start} exact')
        prompt = prompt.replace(f'in {job["columns"]} equal columns', f'in {end-start} equal columns')
        child['prompt'] = job['prompt'].replace(key, child_key)
        (D / child['prompt']).write_text(prompt)
        new_jobs[child_key] = child
data['jobs'] = new_jobs
path.write_text(json.dumps(data, indent=2) + '\n')
(D / 'checkpoints/retired_wide_jobs.json').write_text(json.dumps(retired, indent=2) + '\n')
print('Split', len(retired), 'wide jobs;', len(new_jobs), 'active jobs; native coverage unchanged.')
