"""Add grounded cameras on existing native-context stepping pads, preserving old evidence."""
import json
import math
import shutil
import subprocess

from common import P, STAGE, sha


def main():
    source = P / 'reports/road_fixture_stage.json'
    report = json.loads(source.read_text())
    assert sha(STAGE / 'openyamm') == report['binary_sha256']
    fixture = json.loads((P / 'reports/road_fixtures.json').read_text())['fixtures']['roads_plains']
    placements = {r['tile']: r for r in fixture['placements']}
    output = P / 'fixtures/roads_v1/stepping_walks'
    output.mkdir(exist_ok=True)
    poses = {}
    for tile, sides in [('plrdew', [('west', 0), ('east', math.pi)]),
                        ('plrdns', [('south', math.pi / 2), ('north', 3 * math.pi / 2)])]:
        placement = placements[tile]
        center = ((placement['col'] + .5 - 64) * 512, (64 - placement['row'] - .5) * 512)
        for side, yaw in sides:
            pose = [center[0] - math.cos(yaw) * 512, center[1] - math.sin(yaw) * 512, 0, yaw, -.4]
            save = output / (side + '.oysav')
            subprocess.run(['/tmp/mm8-terrain-capture-save', str(P / 'liquids/v1/water_flying.oysav'),
                            str(save), *map(str, pose), 'empty-world', '--grounded'], check=True)
            for quality in ('x1', 'x2'):
                record = dict(report['poses']['flat_roads_plains_' + tile + '_' + quality])
                source_stage = STAGE / ('flat_roads_plains_' + quality)
                private_stage = STAGE / ('flat_stepping_' + side + '_' + quality)
                private_stage.mkdir(exist_ok=True)
                assets = private_stage / 'assets_dev'
                if not assets.exists():
                    assets.symlink_to(source_stage / 'assets_dev', target_is_directory=True)
                shutil.copy2(source_stage / 'settings.ini', private_stage / 'settings.ini')
                record.update(save=str(save.relative_to(P)), save_sha256=sha(save), pose=pose,
                              kind=side, grounded=True, native_placement=placement, stage=str(private_stage))
                poses['flat_stepping_' + side + '_' + quality] = record
    report.update(poses=poses, source_stage_sha256=sha(source),
                  script_sha256=sha(P / 'prepare_stepping_walks.py'))
    (P / 'reports/road_extra_fixture_stage.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Prepared', len(poses), 'grounded stepping-path views')


if __name__ == '__main__':
    main()
