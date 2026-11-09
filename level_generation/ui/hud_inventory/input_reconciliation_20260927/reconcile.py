"""Record the existing inventory-grid offset changes without changing frozen icon contracts."""

import copy
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import yaml

OUT = Path(__file__).resolve().parent
HUD = OUT.parent
ROOT = HUD.parents[2]
sys.path.insert(0, str(HUD))
from queue import Queue, save

CHANGES = {
    'assets_dev/engine/data_tables/chest_data.txt':
        'ca552e695589f345d9069ece484219dc92001695a94118d578166fbac06f3cb7',
    'assets_dev/engine/ui/gameplay/character.yml':
        '1e1b92dd61de67853197046fa54004970dbe003b5dc3e578ce59c230fe8dc341',
    'assets_dev/engine/ui/gameplay/chest.yml':
        '131ec7d7ae1c01fd1920aee63c3bed13aa4392b08a7cb26beaab3d32ab6a6ea2',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


def main():
    with (HUD / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state_path = HUD / 'checkpoint/state.json'
        state = json.loads(state_path.read_text())
        receipt_path = OUT / 'receipt.json'
        if receipt_path.exists():
            assert state['input_reconciliation'] == {
                'path': str(receipt_path.relative_to(ROOT)), 'sha256': sha(receipt_path)}
            Queue()
            print('Already reconciled; exact recorded inputs still match.')
            return
        assert 'input_reconciliation' not in state, 'Review and retain the previous reconciliation first'
        manifest_path = HUD / 'expected_targets.json'
        manifest = json.loads(manifest_path.read_text())
        drift = {name for name, expected in manifest['inputs'].items() if sha(ROOT / name) != expected}
        assert drift == set(CHANGES), drift
        rows = {}
        for name, current_sha in CHANGES.items():
            live = ROOT / name
            assert sha(live) == current_sha, name
            original = subprocess.run(['git', 'show', 'HEAD:' + name], cwd=ROOT,
                                      stdout=subprocess.PIPE, check=True).stdout
            frozen_sha = hashlib.sha256(original).hexdigest()
            assert frozen_sha == manifest['inputs'][name], name
            before = OUT / 'before' / live.name
            after = OUT / 'current' / live.name
            for path, content in [(before, original), (after, live.read_bytes())]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            if live.suffix == '.txt':
                old_rows = [line.split('\t') for line in original.decode().splitlines()]
                new_rows = [line.split('\t') for line in after.read_text().splitlines()]
                actual = [(a[0], i, x, y) for a, b in zip(old_rows, new_rows, strict=True)
                          for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y]
                assert actual == [('1', 6, '18', '42'), ('2', 6, '18', '42')], actual
                changes = [{'row': item[0], 'field': 'GridOffsetX', 'before': 18, 'after': 42} for item in actual]
            else:
                old = yaml.safe_load(original)
                new = yaml.safe_load(after.read_text())
                node_id = 'CharacterInventoryGrid' if live.name == 'character.yml' else 'ChestNestedInventoryGrid'
                changed = [node for node in nodes(new) if node.get('id') == node_id]
                assert len(changed) == 1
                assert [changed[0]['offset_x'], changed[0]['offset_y']] == [7, 8]
                changed[0].update(offset_x=5, offset_y=6)
                assert new == old, 'Other YAML changes require a separate audit: ' + name
                changes = [{'element': node_id, 'field': 'offset_x', 'before': 5, 'after': 7},
                           {'element': node_id, 'field': 'offset_y', 'before': 6, 'after': 8}]
            rows[name] = {
                'frozen_sha256': frozen_sha, 'current_sha256': current_sha,
                'before_snapshot': str(before.relative_to(ROOT)), 'current_snapshot': str(after.relative_to(ROOT)),
                'changes': changes,
            }
        receipt = {
            'schema': 'openyamm-icon-input-reconciliation-v1', 'frozen_manifest_sha256': sha(manifest_path),
            'inputs': rows, 'reason': 'Existing runtime inventory-grid offsets changed after the art catalog was frozen.',
            'audit': 'Only the six listed offset values changed. Asset bindings, image canvases, source bitmaps, '
                     'Town Portal geometry, frozen targets, and job definitions remain unchanged.',
            'recipe_sha256': sha(Path(__file__).resolve()),
        }
        save(receipt_path, receipt)
        save(OUT / 'checkpoint.before.json', state)
        revised = copy.deepcopy(state)
        revised['input_reconciliation'] = {'path': str(receipt_path.relative_to(ROOT)), 'sha256': sha(receipt_path)}
        save(OUT / 'checkpoint.reconciled.json', revised)
        Queue(state_path=OUT / 'checkpoint.reconciled.json')
        save(state_path, revised)
        assert json.loads(state_path.read_text()) == {**state, 'input_reconciliation': revised['input_reconciliation']}
        print(json.dumps({'reconciled_inputs': len(rows), 'artwork_or_runtime_files_changed': 0}, indent=2))


if __name__ == '__main__':
    main()
