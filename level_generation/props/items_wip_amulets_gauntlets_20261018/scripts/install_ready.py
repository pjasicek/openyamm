"""Install only owned, hash-validated exports, with the standard serialized installer and exact cook verification."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


owned = json.loads((P / 'ownership.json').read_text())
baseline = {e['icon']: e for e in owned}
validated = {e['icon']: e for e in json.loads((P / 'review/validation.json').read_text())}
installed_path = P / 'receipts/installed.json'
installed = {e['icon']: e for e in json.loads(installed_path.read_text())} if installed_path.exists() else {}
assert len(owned) == len(validated) == 38 and set(validated) == set(baseline)
for entry in owned:
    icon = entry['icon']
    if icon not in validated:
        continue
    prefix = 'amulet_' if entry['family'] == 'amulets' else 'equipment_'
    export = P / 'work/finished' / (prefix + icon + '_export.glb')
    assert digest(export) == validated[icon]['sha256'], (icon, 'unreviewed export changed')
    source = ROOT / baseline[icon]['source']
    expected = installed.get(icon, {}).get('source_sha256', baseline[icon]['baseline_source_sha256'])
    assert digest(source) == expected, (icon, 'source changed outside this session')
    if installed.get(icon, {}).get('export_sha256') == digest(export):
        continue
    assert all((P / 'review/finished' / (icon + '_' + view + '.png')).exists()
               for view in ['above', 'three_quarter', 'low', 'underside'])
    with (P / 'receipts' / ('install_' + icon + '.log')).open('w') as log:
        subprocess.run([sys.executable, 'tools/install_model.py', str(export), '--world-items',
                        '--name', 'item_' + icon + '.glb'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run([sys.executable, 'tools/cook_models.py', '--verify', '--profile', 'desktop', '--only',
                        'engine/world_items/models/item_' + icon + '.glb'], cwd=ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    runtime = ROOT / baseline[icon]['runtime']
    installed[icon] = {'icon': icon, 'source': str(source.relative_to(ROOT)), 'source_sha256': digest(source),
                       'runtime': str(runtime.relative_to(ROOT)), 'runtime_sha256': digest(runtime),
                       'binding_length': entry['binding']['length'], 'export': str(export.relative_to(ROOT)),
                       'export_sha256': digest(export), 'desktop_scoped_verify': 'passed'}
    installed_path.write_text(json.dumps(list(installed.values()), indent=2) + '\n')
    print('INSTALLED', icon, len(installed), '/ 38', flush=True)
