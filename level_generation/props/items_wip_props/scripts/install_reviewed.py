"""Resume only this worker's visually reviewed, validated replacements through the shared installer lock."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    owned = {x['icon'] for x in json.loads((PROJECT / 'ownership.json').read_text())}
    reviewed = json.loads((PROJECT / 'review' / 'reviewed_models.json').read_text())['icons']
    report = json.loads((PROJECT / 'review' / 'validation.json').read_text())
    assert not report['errors'] and len(reviewed) == len(set(reviewed))
    assert set(reviewed) <= owned & set(report['models'])
    receipt_path = PROJECT / 'install_receipts.json'
    receipts = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    with (PROJECT / 'review' / 'install.log').open('a') as log:
        for icon in reviewed:
            export = PROJECT / 'work' / 'exports' / f'props_{icon}_export.glb'
            source = ROOT / 'assets_source/engine/world_items/models' / f'item_{icon}.glb'
            runtime = ROOT / 'assets_dev/engine/world_items/models' / f'item_{icon}.glb'
            digest = sha(export)
            assert digest == report['models'][icon]['sha256'], (icon, 'export changed after validation')
            old = receipts.get(icon, {})
            if old.get('source_sha256') == digest and source.exists() and runtime.exists():
                if sha(source) == digest and sha(runtime) == old.get('runtime_sha256'):
                    continue
            subprocess.run([sys.executable, str(ROOT / 'tools/install_model.py'), str(export),
                            '--world-items', '--name', f'item_{icon}.glb'],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
            assert sha(source) == digest and runtime.exists(), icon
            receipts[icon] = {'export': str(export.relative_to(ROOT)), 'source_sha256': digest,
                              'runtime_sha256': sha(runtime), 'status': 'installed_cooked_desktop'}
            receipt_path.write_text(json.dumps(receipts, indent=2) + '\n')
            print('INSTALLED', icon, flush=True)
    print('RECEIPTS', len(receipts), flush=True)


if __name__ == '__main__':
    main()
