"""Measure actual MM7 generated detail from raw-to-2x registration, without upscaling credit."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit(project):
    path = project / 'registration.json'
    if not path.exists():
        return dict(passed=False, issue='Missing raw-to-export registration', batches={})
    registration = json.loads(path.read_text())
    batches = {}
    for name, frame in registration.items():
        sampling = 2 / frame['scale']
        batch = batches.setdefault(frame['batch'], dict(frames=[], minimum_sampling=sampling,
                                                       below_minimum_frames=[]))
        batch['frames'].append(name)
        batch['minimum_sampling'] = min(batch['minimum_sampling'], sampling)
        if sampling < 2 - 1e-6:
            batch['below_minimum_frames'].append(name)
    return dict(schema_version=1, required_sampling=2,
                measurement='2 / uniform raw-to-2x registration scale; enlargement gives no detail credit',
                passed=bool(batches) and all(not b['below_minimum_frames'] for b in batches.values()),
                batches=batches)


if __name__ == '__main__':
    results = {p.name: audit(p) for p in sorted(HERE.glob('mm7_*'))
               if p.is_dir() and (p / 'registration.json').exists()}
    (HERE / 'mm7_sampling_audit.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps({k: v['passed'] for k, v in results.items()}, indent=2))
