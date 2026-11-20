"""Publish the user-selected direct-2x MM7/MM8 minimaps into the current icons ledger."""
import argparse
import copy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sys

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HUD = ROOT / 'level_generation/ui/hud_inventory'
CURRENT = HUD / 'accepted_icons.json'
sys.path.insert(0, str(HUD))
from queue import Queue, save


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def immutable(path, data):
    if path.exists():
        assert read(path) == data, f'Receipt changed: {path}'
    else:
        save(path, data)


def copy_verified(source, destination, digest):
    assert sha(source) == digest, source
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        assert sha(destination) == digest, destination
    else:
        shutil.copyfile(source, destination)
    destination.chmod(0o644)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    with (HUD / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        queue = Queue()
        previous = read(CURRENT)
        assert queue.state['accepted_icon_index']['sha256'] == sha(CURRENT)
        if (HERE / 'accepted.json').exists():
            for target, record in read(HERE / 'accepted.json')['records'].items():
                assert previous['records'][target] == record, 'Superseded: deploy only the current index.'
                assert all(queue.accepted(cell) for cell in queue.target_cells[target])
            print('Already accepted; use the standard deployment tool.')
            return
        exports = read(HERE / 'exports.json')
        validation = read(HERE / 'validation.json')
        visual = read(HERE / 'visual_review.json')
        recipe = read(HERE / 'approved_recipe.json')
        assert len(exports['records']) == 27 and exports['recommended'] == 'video2'
        assert validation['result'] == visual['result'] == 'PASS'
        assert validation['exports_sha256'] == sha(HERE / 'exports.json')
        assert visual['exports_sha256'] == sha(HERE / 'exports.json')
        assert recipe['model'] == 'realesr-animevideov3' and recipe['scale'] == 2
        assert recipe['blend'] == {'esrgan': 1.0, 'original_lanczos_x2': 0.0}
        authority = {
            'schema': 'openyamm-minimap-esrgan-approval-v1',
            'instruction': 'anime video v3, direct 2x is good, regenerate all of them for MM7/MM8 and accept it',
            'scope': {'mm7': 13, 'mm8': 14, 'total': 27},
            'approval': 'Explicit user selection of full-strength direct-2x anime-video and batch acceptance.',
            'review': 'User selected the model; assistant inspected every map overview and representative detail crops.',
            'recipe': recipe,
            'evidence': {str(path.relative_to(ROOT)): sha(path) for path in [
                HERE / 'exports.json', HERE / 'validation.json', HERE / 'visual_review.json',
                HERE / 'browser_check.json',
            ]},
        }
        immutable(HERE / 'authority.json', authority)
        records, replacements = {}, {}
        frozen_runtime = read(HERE / 'runtime_before.json')
        for export in exports['records']:
            assert export['world'] in ('mm7', 'mm8')
            target = export['target']
            prior = previous['records'][target]
            cells = queue.target_cells[target]
            assert len(cells) == 1
            cell = cells[0]
            assert queue.accepted(cell)
            assert queue.state['staged_targets'][target]['sha256'] == prior['sha256']
            assert sha(prior['artifact']) == prior['sha256'] == sha(ROOT / prior['runtime_output_path'])
            assert frozen_runtime[prior['runtime_output_path']] == prior['sha256']
            assert sha(ROOT / export['source']) == export['source_sha256'] == prior['source_sha256']
            directory = HERE / 'maps' / export['key']
            variant = export['variants']['video2']
            source = directory / 'video2.png'
            assert sha(directory / 'video2_master.png') == variant['master_sha256']
            with Image.open(source) as image:
                assert image.format == 'PNG' and list(image.size) == queue.targets[target]['x2_size']
                assert list(image.size) == export['x2_size']
            destination = HERE / 'accepted' / Path(prior['runtime_output_path']).relative_to('assets_dev')
            copy_verified(source, destination, variant['x2_sha256'])
            record = {
                'target': target, 'artifact': str(destination), 'sha256': sha(destination),
                'source': prior['source'], 'source_sha256': prior['source_sha256'],
                'native_source_artifact': export['source'], 'x2_size': export['x2_size'],
                'runtime_output_path': prior['runtime_output_path'],
                'previous_artifact': prior['artifact'], 'previous_sha256': prior['sha256'],
                'master_artifact': str(directory / 'video2_master.png'),
                'master_sha256': variant['master_sha256'], 'reviewed_artifact': str(source),
                'authority': str(HERE / 'authority.json'), 'recipe': str(HERE / 'approved_recipe.json'),
                'acceptance': 'explicit_user_selected_direct_2x_animevideo_batch',
                'placement_changes': False, 'world_bounds': [-32768, 32768, -32768, 32768],
                'method': 'native_realesr_animevideov3_direct_2x',
            }
            receipt = HERE / 'receipts' / f'{target}.json'
            immutable(receipt, record)
            records[target] = record
            replacements[cell] = (record, receipt)
        if not args.apply:
            print(json.dumps({'prepared': True, 'targets': len(records)}))
            return
        copy_verified(CURRENT, HERE / 'previous_accepted_index.json', sha(CURRENT))
        copy_verified(queue.state_path, HERE / 'checkpoint.before.json', sha(queue.state_path))
        old_cells = copy.deepcopy(queue.state['cells'])
        for cell, (record, receipt) in replacements.items():
            evidence = {str(receipt): sha(receipt), str(HERE / 'authority.json'): sha(HERE / 'authority.json')}
            review = {'authority': str(HERE / 'authority.json'), 'decision': str(receipt)}
            queue.state['cells'][cell] = {
                'status': 'accepted', 'artifact': record['artifact'], 'sha256': record['sha256'],
                'acceptance_method': 'user_selected_minimap_animevideo_direct2x',
                'layout_sha256': queue.layout_hash(cell), 'dependency_cells': {},
                'evidence_hashes': evidence, 'review': review,
            }
            target = record['target']
            contract = queue.targets[target]
            cell_hashes = {cell: record['sha256']}
            queue.state['staged_targets'][target] = {
                'target': target, 'source_path': contract['source_path'],
                'source_sha256': record['source_sha256'], 'artifact': record['artifact'],
                'sha256': record['sha256'], 'native_size': contract['native_size'],
                'x2_size': record['x2_size'], 'runtime_output_path': record['runtime_output_path'],
                'cells': cell_hashes, 'status': 'accepted_staged', 'evidence_hashes': evidence, 'review': review,
            }
            queue.state['reconstructed_targets'][target] = {
                'target': target, 'path': record['artifact'], 'sha256': record['sha256'],
                'size': record['x2_size'], 'cells': cell_hashes, 'status': 'accepted_full_canvas',
            }
            if target in queue.state.get('restoration_inventory', {}):
                queue.state['restoration_inventory'][target].update(
                    status='accepted', canonical_artifact=record['artifact'],
                    canonical_sha256=record['sha256'], acceptance_receipt=str(receipt))
        frozen = []
        for cell, record in queue.state['cells'].items():
            if cell in replacements:
                continue
            for dependency, expected in list(record.get('dependency_cells', {}).items()):
                if dependency not in replacements:
                    continue
                old = old_cells[dependency]
                assert sha(old['artifact']) == expected == old['sha256']
                record.setdefault('evidence_hashes', {})[old['artifact']] = expected
                record.setdefault('reference_revision_history', []).append(
                    {'cell': dependency, 'sha256': expected, 'artifact': old['artifact']})
                del record['dependency_cells'][dependency]
                frozen.append(cell)
        assert all(queue.accepted(cell) for cell in list(replacements) + frozen)
        current = copy.deepcopy(previous)
        current['records'].update(records)
        current['latest_revision'] = str((HERE / 'accepted.json').relative_to(ROOT))
        current['updated_at'] = datetime.now(timezone.utc).isoformat()
        assert current['count'] == len(current['records']) == previous['count']
        assert all(current['records'][target] == record for target, record in previous['records'].items()
                   if target not in records)
        save(CURRENT, current)
        queue.state['accepted_icon_index'] = {
            'path': str(CURRENT.relative_to(ROOT)), 'sha256': sha(CURRENT), 'targets': current['count'],
        }
        save(queue.state_path, queue.state)
        save(queue.storage_root() / 'exports/manifest.json', {'targets': list(queue.state['staged_targets'].values())})
        save(HERE / 'accepted.json', {
            'schema': 'openyamm-minimap-accepted-replacement-v1', 'count': len(records), 'records': records,
            'authority': str(HERE / 'authority.json'), 'canonical_index_sha256': sha(CURRENT),
            'ledger_sha256': sha(queue.state_path), 'published_at': current['updated_at'],
            'frozen_reference_cells': frozen,
        })
        print(json.dumps({'accepted': True, 'replacements': len(records), 'total': current['count'],
                          'unrelated_records_unchanged': True}))


if __name__ == '__main__':
    main()
