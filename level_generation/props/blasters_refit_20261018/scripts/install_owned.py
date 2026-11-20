"""Install only visually accepted and validated owned exports; retain per-icon receipts."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    owned = {x['icon']: x for x in json.loads((HERE / 'ownership.json').read_text())}
    ledger = json.loads((HERE / 'ledger.json').read_text())
    validation = json.loads((HERE / 'receipts/validation.json').read_text())
    acceptance = json.loads((HERE / 'review/acceptance.json').read_text())
    receipt_path = HERE / 'receipts/installed.json'
    receipts = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    selected = sys.argv[1:] or list(owned)
    for icon in selected:
        assert icon in owned and acceptance[icon]['accepted']
        export = HERE / ledger[icon]['source_export']
        source = ROOT / 'assets_source' / owned[icon]['binding']['model']
        runtime = ROOT / 'assets_dev' / owned[icon]['binding']['model']
        assert sha(export) == validation[icon]['sha256'], (icon, 'export changed after validation')
        assert acceptance[icon]['export_sha256'] == sha(export), (icon, 'export changed after visual review')
        # An interrupted cook may already have installed this exact validated source.
        assert sha(source) in {sha(export), ledger[icon]['baseline_sha256'],
                               receipts.get(icon, {}).get('source_sha256')}, (
            icon, 'another session changed this source')
        relative = owned[icon]['binding']['model']
        with (HERE / f'receipts/install_{icon}.log').open('w') as log:
            subprocess.run([sys.executable, 'tools/install_model.py', str(export), '--world-items',
                            '--name', f'item_{icon}.glb'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        verification = subprocess.run([sys.executable, 'tools/cook_models.py', '--verify', '--profile', 'desktop',
                                       '--only', relative], cwd=ROOT, capture_output=True, text=True, check=True)
        assert '0 problems' in verification.stdout and not verification.stderr, verification
        (HERE / f'receipts/verify_{icon}.log').write_text(verification.stdout)
        assert sha(source) == sha(export)
        receipts[icon] = {'source_sha256': sha(source), 'runtime_sha256': sha(runtime),
                          'source_bytes': source.stat().st_size, 'runtime_bytes': runtime.stat().st_size,
                          'verification': 'desktop scoped cook: 0 problems'}
        ledger[icon].update({'status': 'installed', 'defects': ['Awaiting native batch review']})
        receipt_path.write_text(json.dumps(receipts, indent=2) + '\n')
        (HERE / 'ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
        print(f'Installed and verified {icon}', flush=True)


if __name__ == '__main__':
    main()
