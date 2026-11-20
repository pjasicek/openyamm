"""Capture named native MM8 material views using the frozen stage executable."""
import argparse
import json
import subprocess

from common import *


def candidate_snapshot():
    path = P / 'reports/candidate_stage.json'
    report = json.loads(path.read_text())
    folder = STAGE / 'enhanced/assets_dev/worlds/mm8/terrain_x2'
    files = {p.name: sha(p) for p in folder.glob('*.png')}
    assert files == report['files'], 'Staged terrain differs from the candidate manifest'
    return dict(manifest_sha256=sha(path), files=files)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('families', nargs='+')
    parser.add_argument('--quality', choices=['x1', 'x2'], default='x1')
    args = parser.parse_args()
    report = json.loads((P / 'reports/native_stage.json').read_text())
    assert sha(STAGE / 'openyamm') == report['binary_sha256']
    for name in args.families:
        snapshot = candidate_snapshot() if args.quality == 'x2' else None
        record = report['poses'][name]
        assert sha(ROOT / 'assets_dev/worlds/mm8/maps' / (record['map'] + '.odm')) == record['source_sha256']
        mode = 'original' if args.quality == 'x1' else 'enhanced'
        command = ['python3', str(ROOT / 'level_generation/projects/brackenford_greywatch/capture_gameplay.py'),
                   'mm8_' + name + '_' + args.quality, '--world', 'mm8', '--map', record['map'] + '.odm',
                   '--stage', str(STAGE / mode), '--binary', str(STAGE / 'openyamm'),
                   '--review-directory', str(P / 'captures'),
                   '--warmup', '1', '--seconds', '0']
        if not record.get('start_save'):
            command.extend(['--pose', *map(str, record['pose'])])
        if record.get('diagnostic_flying', False):
            command.append('--diagnostic-flying')
        if record.get('start_save'):
            start_save = P / record['start_save']
            assert sha(start_save) == record['start_save_sha256']
            command.extend(['--start-save', str(start_save)])
        if record.get('actions'):
            actions = P / record['actions']
            assert sha(actions) == record['actions_sha256']
            command.extend(['--actions', str(actions)])
        with (P / 'captures' / f'capture_{name}_{args.quality}.log').open('w') as stream:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
        if snapshot is not None:
            assert candidate_snapshot() == snapshot, 'Staged terrain changed during capture'
        path = P / 'captures' / f'mm8_{name}_{args.quality}.json'
        metadata = json.loads(path.read_text())
        metadata['terrain_candidates'] = snapshot
        metadata['review_pose'] = record
        metadata['screenshot_sha256'] = sha(path.with_suffix('.png'))
        path.write_text(json.dumps(metadata, indent=2) + '\n')
        print('Captured', name, args.quality, flush=True)


if __name__ == '__main__':
    main()
