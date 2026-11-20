"""Check resumable preparation, ownership and unchanged installed baselines without spending credits."""
import hashlib
import json
from pathlib import Path

from PIL import Image

project = Path(__file__).resolve().parents[1]
repo = project.parents[2]
ownership = json.loads((project / 'ownership.json').read_text())
designs = json.loads((project / 'designs.json').read_text())
budget = json.loads((project / 'budget_request.json').read_text())
ledger = json.loads((project / 'ledger.json').read_text())
owned = {entry['icon'] for entry in ownership}
assert len(ownership) == len(owned) == len(designs) == len(ledger) == 95
assert {icon for design in designs.values() for icon in design['icons']} == owned
assert {entry['icon'] for entry in ledger} == owned
assert not owned.intersection({'item111', '7item089', '7item094', '7item115', '7item118', '7item117'})
geometry = {design['geometry_design'] for design in designs.values()}
assert geometry == {job['design'] for job in budget['jobs']}
assert len(geometry) == budget['unique_shapes'] == 83
assert budget['requested_credits'] == sum(job['credits'] for job in budget['jobs']) == 415
assert 0 <= budget['spent_credits'] <= budget['approved_credits'] == 415
assert sum(len(job['icons']) for job in budget['jobs']) == 95
for entry in ledger:
    assert entry['inspected']
    assert (project / entry['review_sheet']).is_file()
    if entry.get('delegated_geometry_project'):
        continue
    for folder, key in [('assets_source', 'baseline_source_sha256'), ('assets_dev', 'baseline_runtime_sha256')]:
        path = repo / folder / 'engine/world_items/models' / f"item_{entry['icon']}.glb"
        if entry['replacement_installed']:
            key = key.replace('baseline_', 'installed_')
        elif entry.get('external_install'):
            key = key.replace('baseline_', 'external_')
        elif folder == 'assets_dev' and entry.get('retained_runtime_sha256'):
            key = 'retained_runtime_sha256'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry[key], path
for name in geometry:
    folder = project / 'meshy' / name / 'references_hd'
    receipt = json.loads((folder / 'generation_runs.json').read_text())
    assert receipt['selected'], name
    assert hashlib.sha256((repo / receipt['input']).read_bytes()).hexdigest() == receipt['input_sha256']
    assert hashlib.sha256((folder / receipt['output']).read_bytes()).hexdigest() == receipt['output_sha256']
    alpha = Image.open(folder / receipt['output']).getchannel('A').getextrema()
    assert alpha[0] == 0 and alpha[1] >= 250
    request = json.loads((project / 'meshy/requests' / f'{name}_st_v1.json').read_text())
    assert request['should_texture'] is False and request['model_type'] == 'smart-topology'
delegated = sum(bool(entry.get('delegated_geometry_project')) for entry in ledger)
print(f'Preparation passed: 95 inspected entries, {95 - delegated} current source/runtime records checked, '
      f'{delegated} delegated geometry entries, 83 verified masters, 415-credit limit.')
