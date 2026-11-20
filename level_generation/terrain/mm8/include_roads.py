"""Add the screened cobble candidates to the partial runtime union for native review."""
import json
import shutil
from common import *

folder = P / 'roads/v3'
build = json.loads((folder / 'build.json').read_text())
validation = json.loads((folder / 'validation.json').read_text())
assert validation['build_sha256'] == sha(folder / 'build.json')
assert not validation['failures'] and all(r['passed'] for r in validation['masks'])
assert not build['missing'] and len(build['tiles']) == 36
inventory = json.loads((P / 'inventory.json').read_text())
expected = {r['name'] for r in inventory['tiles'] if r['family'] in ('roads_dirt', 'roads_grey')}
assert expected == {r['name'] for r in build['tiles']}
records = {}
for record in build['tiles']:
    source = folder / 'runtime' / (record['name'] + '.png')
    assert sha(source) == record['runtime_sha256']
    assert Image.open(source).size == (256, 256)
    shutil.copy2(source, OUT / source.name)
    records[source.name] = sha(source)
(P / 'reports/road_candidate_union.json').write_text(json.dumps(dict(status='candidates_for_native_review_not_installation',
    build_sha256=sha(folder / 'build.json'), validation_sha256=sha(folder / 'validation.json'), files=records), indent=2) + '\n')
print('Added36 screened cobble candidates to partial runtime union')
