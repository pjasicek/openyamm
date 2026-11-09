"""Create isolated original review stage and stable source/camera records."""
import configparser
import json
import shutil
import sys

from common import *
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file


def main():
    STAGE.mkdir(exist_ok=True)
    binary = STAGE / 'openyamm'
    if not binary.exists():
        shutil.copy2(ROOT / 'build/game/openyamm', binary)
    assets = STAGE / 'original/assets_dev'
    assets.mkdir(parents=True, exist_ok=True)
    for path in (ROOT / 'assets_dev').iterdir():
        if not (assets / path.name).exists():
            (assets / path.name).symlink_to(path, target_is_directory=path.is_dir())
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'settings.ini')
    config['assets']['root'] = str(assets)
    config['video_quality']['terrain'] = 'x1'
    config['startup'] = {'start_in_main_menu': 'true'}
    config['debug']['start_world'] = 'mm8'
    config['debug']['start_map_file'] = 'out01.odm'
    config['video'].update(resolution='1600x1200', fullscreen='false', vsync='false')
    with (STAGE / 'original/settings.ini').open('w') as stream:
        config.write(stream)
    inventory = json.loads((P / 'inventory.json').read_text())
    grids = json.loads((P / 'grids.json').read_text())
    poses = {}
    for name, map_id, tile in [
        ('dirt', 'out02', 'dirttyl'), ('grass', 'out02', 'grastyl'),
        ('volcano', 'out01', 'voltyl'), ('rock', 'out03', 'rktyl'),
        ('sandstone', 'out08', 'rctyl'), ('plains', 'out04', 'plntyl'),
        ('plains_sand', 'out04', 'plsatyl'), ('grey_stone', 'out06', 'gstyl'),
        ('roads_dirt', 'out02', 'drsrns'), ('roads_plains', 'out04', 'plrdns'),
        ('roads_grey', 'out06', 'gdrdns'), ('lava', 'elemf', 'lavtyl'),
        ('tar', 'out06', 'tartyl'), ('water', 'out01', 'wtrtyl')]:
        record = next(m for m in inventory['maps'] if m['id'] == map_id)
        data = parse_odm_file(ROOT / record['source'])['payload']
        grid = grids[map_id]
        candidates = [(y, x) for y in range(8, 119) for x in range(8, 119) if grid[y][x] == tile]
        def score(pos):
            y, x = pos
            heights = [data['height_map'][yy * 128 + xx] for yy in range(y - 2, y + 3)
                       for xx in range(x - 2, x + 3)]
            span = max(heights) - min(heights)
            count = sum(n == tile for row in grid[y - 2:y + 3] for n in row[x - 2:x + 3])
            return (span <= 4, count, -span, -abs(y - 64) - abs(x - 64))
        y, x = max(candidates, key=score)
        height = max(data['height_map'][yy * 128 + xx] for yy in (y, y + 1) for xx in (x, x + 1)) * 32
        poses[name] = dict(map=map_id, tile=tile, row=y, column=x,
                           pose=[(x + .5 - 64) * 512, (64 - y - .5) * 512, height + 161,
                                 1.5707963268, -.48], source_sha256=record['sha256'])
    (P / 'captures').mkdir(exist_ok=True)
    report = dict(stage=str(STAGE), binary_sha256=sha(binary), poses=poses)
    (P / 'reports/native_stage.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Original stage ready:', len(poses), 'material poses')


if __name__ == '__main__':
    main()
