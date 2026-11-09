"""Check four local-art pilots against the unchanged compatible land inventory."""
import json
from common import *
from check_land import checks

F = P / 'transitions/grey_fringe_ai'
baseline = json.loads((P / 'reports/land_validation.json').read_text())
images, files = {}, {}
for relative, expected in baseline['files'].items():
    path = P / relative
    assert sha(path) == expected, path
    name = path.stem
    # Master runtime filenames use family names instead of native texture names.
    if path.parent == M / 'runtime':
        from inventory import GROUPS
        name = GROUPS[name][0]
    images[name], files[name] = read(path), path
names = ('gsn', 'gse', 'gsne', 'gsnw')
for name in names:
    path = F / 'runtime_pilot' / (name + '.png')
    report = json.loads((F / (name + '_pilot.json')).read_text())
    assert sha(path) == report['runtime_sha256'], name
    for relative, expected in report['inputs'].items():
        assert sha(P / relative) == expected, relative
    images[name], files[name] = read(path), path
results = []
for record in baseline['checks']:
    a, b, side = record['a'], record['b'], record['side']
    metrics, _, _ = checks.metrics(images[a], images[b], side)
    results.append(dict(a=a, b=b, side=side, **metrics))
report = dict(scope='Four local grey-fringe pilots substituted into screened land candidates only',
              checked_tiles=len(images), compatible_checks=len(results),
              failures=[r for r in results if not r['passed']],
              checks=results, files={str(path.relative_to(P)):sha(path) for path in files.values()},
              baseline_sha256=sha(P/'reports/land_validation.json'),
              visual_acceptance=False,
              limitation='Old protected border artwork is still present; seam checks cannot accept its chipped forms.')
(F/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
print(len(results), 'compatible land joins;', len(report['failures']), 'failures')
