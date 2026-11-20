"""Install the nine visually reviewed exports, preserving concurrent source work and bindings."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    audit = {e['icon']: e for e in json.loads((P / 'audit.json').read_text())}
    validation = json.loads((P / 'review/validation.json').read_text())
    approved = json.loads((P / 'review/approved_exports.json').read_text())
    receipt = P / 'receipts/installed.json'
    installed = {e['icon']: e for e in json.loads(receipt.read_text())} if receipt.exists() else {}
    assert len(validation) == len(approved) == 9
    for entry in validation:
        icon = entry['icon']
        export = ROOT / entry['path']
        assert sha(export) == entry['sha256'] == approved[icon]
        source = ROOT / 'assets_source/engine/world_items/models' / f'item_{icon}.glb'
        runtime = ROOT / 'assets_dev/engine/world_items/models' / source.name
        expected = installed.get(icon, {}).get('source_sha256', audit[icon]['source_sha256'])
        assert sha(source) == expected, (icon, 'concurrent source edit; stop before overwrite')
        if installed.get(icon, {}).get('export_sha256') == sha(export):
            continue
        with (P / 'receipts' / f'install_{icon}.log').open('w') as log:
            subprocess.run([sys.executable, 'tools/install_model.py', str(export), '--world-items',
                            '--name', source.name], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
            subprocess.run([sys.executable, 'tools/cook_models.py', '--verify', '--profile', 'desktop', '--only',
                            'engine/world_items/models/' + source.name], cwd=ROOT,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        installed[icon] = {'icon': icon, 'export_sha256': sha(export), 'source_sha256': sha(source),
                           'runtime_sha256': sha(runtime), 'desktop_scoped_verify': 'passed'}
        receipt.write_text(json.dumps(list(installed.values()), indent=2) + '\n')
        print('INSTALLED', icon, len(installed), '/ 9', flush=True)


if __name__ == '__main__':
    main()
