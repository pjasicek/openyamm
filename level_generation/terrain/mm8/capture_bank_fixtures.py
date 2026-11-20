"""Capture named isolated flat-bank views with frozen terrain and fixture hashes."""
import argparse
import json
import subprocess
from pathlib import Path

from common import P, ROOT, STAGE, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('names', nargs='+')
    parser.add_argument('--cycle', action='store_true')
    parser.add_argument('--roads', action='store_true')
    parser.add_argument('--road-extras', action='store_true')
    parser.add_argument('--land', action='store_true')
    parser.add_argument('--extra-banks', action='store_true')
    parser.add_argument('--walk', action='store_true', help='Capture twelve forward movement steps on grounded roads')
    parser.add_argument('--record-existing', action='store_true',
                        help='Bind a completed capture made through tools/capture_gameplay.sh to this fixture')
    args = parser.parse_args()
    assert not args.walk or (args.roads or args.road_extras) and not args.cycle
    assert sum((args.roads, args.road_extras, args.land, args.extra_banks)) <= 1
    category = ('road_extra' if args.road_extras else 'road' if args.roads else
                'land' if args.land else 'bank_extra' if args.extra_banks else 'bank')
    manifest = P / ('reports/' + category + '_fixture_stage.json')
    report = json.loads(manifest.read_text())
    assert sha(STAGE / 'openyamm') == report['binary_sha256']
    output = P / ('fixtures/roads_v1/captures' if args.roads or args.road_extras else
                  'fixtures/land_v1/captures' if args.land else 'fixtures/banks_extra_v1/captures' if args.extra_banks
                  else 'fixtures/banks_v2/captures')
    output.mkdir(exist_ok=True)
    for name in args.names:
        pose = report['poses'][name]
        if args.walk:
            assert pose.get('grounded', False), 'Walking requires a grounded fixture pose'
        stage = Path(pose['stage'])
        world = stage / 'assets_dev/worlds/mm8'
        assert sha(world / 'maps/out01.odm') == pose['map_sha256']
        assert {f.name: sha(f) for f in (world / 'terrain_x2').glob('*.png')} == report['files']
        save = P / pose['save']
        assert sha(save) == pose['save_sha256']
        capture_name = 'mm8_' + name + ('_walk' if args.walk else '')
        command = [str(ROOT / 'tools/capture_gameplay.sh'),
                   capture_name, '--world', 'mm8', '--map', 'out01.odm', '--stage', str(stage),
                   '--binary', str(STAGE / 'openyamm'), '--start-save', str(save),
                   '--review-directory', str(output), '--warmup', '1', '--seconds', '0']
        if not pose.get('grounded', False):
            command.append('--diagnostic-flying')
        if args.cycle:
            command += ['--actions', str(P / 'liquids/v1/capture_cycle.json')]
        if args.walk:
            command += ['--actions', str(P / 'fixtures/roads_v1/movement_actions.json')]
        if not args.record_existing:
            with (output / (capture_name + '.log')).open('w') as stream:
                subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
        assert {f.name: sha(f) for f in (world / 'terrain_x2').glob('*.png')} == report['files']
        path = output / (capture_name + '.json')
        metadata = json.loads(path.read_text())
        assert metadata['binary_sha256'] == report['binary_sha256']
        assert metadata['native_sha256'] == pose['map_sha256']
        metadata['fixture_stage_sha256'] = sha(manifest)
        metadata['fixture_pose'] = pose
        if args.walk:
            metadata['movement_actions_sha256'] = sha(P / 'fixtures/roads_v1/movement_actions.json')
            metadata['movement_samples'] = {p.name: sha(p) for p in output.glob(capture_name + '_walk_*.png')}
        metadata['screenshot_sha256'] = sha(path.with_suffix('.png'))
        path.write_text(json.dumps(metadata, indent=2) + '\n')
        print('Captured', name, flush=True)


if __name__ == '__main__':
    main()
