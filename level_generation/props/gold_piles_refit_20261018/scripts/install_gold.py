"""Install only reviewed exports from this worker's exact ownership list, retaining receipts and originals."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    subprocess.run([sys.executable, str(PROJECT / 'scripts/validate_gold.py')], check=True)
    ownership = json.loads((PROJECT / 'ownership.json').read_text())
    reviewed = json.loads((PROJECT / 'work/visual_review.json').read_text())
    assert set(reviewed) == {row['icon'] for row in ownership}
    assert all(row['examined'] for row in reviewed.values())
    receipt_path = PROJECT / 'work/install_receipts.json'
    receipts = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    bindings = ROOT / 'assets_dev/engine/world_items/items.yml'
    binding_hash = digest(bindings)
    backups = PROJECT / 'references/baseline_models'
    logs = PROJECT / 'work/install_logs'
    backups.mkdir(exist_ok=True)
    logs.mkdir(exist_ok=True)
    for row in ownership:
        icon = row['icon']
        if reviewed[icon]['decision'] != 'replace':
            continue
        assert reviewed[icon]['decision'] == 'replace'
        export = PROJECT / 'work/exports' / f'{icon}_export.glb'
        for mode in ('clay','replacement'):
            for view in ('above','three_quarter','low','underside'):
                assert (PROJECT / f'review/{mode}' / f'{icon}_{view}.png').stat().st_mtime > export.stat().st_mtime,(icon,mode,view)
        source = ROOT / 'assets_source/engine/world_items/models' / f'item_{icon}.glb'
        runtime = ROOT / 'assets_dev/engine/world_items/models' / source.name
        backup = backups / source.name
        if not backup.exists():
            shutil.copyfile(source, backup)
        expected = digest(export)
        assert reviewed[icon]['export_sha256']==expected,(icon,'The current export needs visual review')
        receipt = receipts.get(icon, {})
        if (digest(source) != expected or receipt.get('source_sha256') != expected or not runtime.exists()
                or digest(runtime) != receipt.get('runtime_sha256')):
            with (logs / f'{icon}.log').open('w') as log:
                subprocess.run([sys.executable, str(ROOT / 'tools/install_model.py'), str(export),
                                '--world-items', '--name', source.name], stdout=log, stderr=subprocess.STDOUT,
                               check=True, cwd=ROOT)
        assert digest(source) == expected and runtime.exists(), icon
        receipts[icon] = {'source_sha256': expected, 'previous_sha256': digest(backup),
                          'runtime_sha256': digest(runtime), 'binding_length_preserved': row['binding']['length'],
                          'install_log': f'work/install_logs/{icon}.log'}
        receipt_path.write_text(json.dumps(receipts, indent=2) + '\n')
        print('INSTALLED', icon, len(receipts), flush=True)
    assert digest(bindings) == binding_hash, 'Shared binding changed during installation; inspect coordinator changes'
    selected={r['icon'] for r in ownership if reviewed[r['icon']]['decision']=='replace'}
    assert selected <= set(receipts) <= {r['icon'] for r in ownership}


if __name__ == '__main__':
    main()
