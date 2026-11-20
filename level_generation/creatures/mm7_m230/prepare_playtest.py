"""Prepare a separate Brackenford atlas demo; source map and existing playtest saves stay intact."""
import argparse
import configparser
import copy
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys

import yaml

from install_runtime import ROOT, REPO, VARIANTS

PROJECT = REPO / 'level_generation/projects/brackenford_greywatch'


def prepare(stage, god_source_save=None):
    if not (stage / 'levelgen-stage.json').exists():
        subprocess.run([sys.executable, str(PROJECT / 'stage_runtime.py'), '--package',
                        str(PROJECT / 'dist/brackenford_greywatch_content.zip'),
                        '--directory', str(stage), '--no-project-state'], check=True)
    assets = stage / 'assets_editor_dev'
    for filename in ['monster_data.txt', 'monster_descriptors.txt']:
        shutil.copy2(REPO / 'assets_dev/engine/data_tables' / filename, assets / 'engine/data_tables' / filename)
    shutil.copytree(REPO / 'assets_dev/engine/sprites_new', assets / 'engine/sprites_new', dirs_exist_ok=True)
    for _, _, _, family in VARIANTS:
        relative = Path(f'engine/rendering/sprite_frames/monsters/{family}.yml')
        shutil.copy2(REPO / 'assets_dev' / relative, assets / relative)
    sys.path.insert(0, str(PROJECT))
    from build_outdoor_content import terrain_height
    samples = bytes.fromhex(json.loads((PROJECT / 'source/lg01.terrain.yml').read_text())['height_map_hex'])
    stats = {int(r[0]): r for r in csv.reader((assets / 'engine/data_tables/monster_data.txt').open(), delimiter='\t')
             if r and r[0].isdigit()}
    scene = json.loads((PROJECT / 'runtime/worlds/mm8/maps/lg01.scene.yml').read_text())
    actors = scene['initial_state']['actors']
    demo = []
    # Enhanced trio nearest the western arrival, originals in the next row for comparison.
    for column, (monster_id, native_id, color, _) in enumerate(VARIANTS):
        for row, identity in enumerate([monster_id, native_id]):
            x, y = -18176 + row * 640, -2048 + column * 384
            actor = copy.deepcopy(actors[0])
            actor.update(actor_index=len(actors), name=stats[identity][1], monster_id=identity,
                         monster_info_id=identity, radius=45, height=165, hp=int(stats[identity][4]),
                         move_speed=0, hostility_type=0, group=38, ally=8,
                         position=dict(x=x, y=y, z=terrain_height(x, y, samples)))
            actors.append(actor)
            demo.append({'actor_index': actor['actor_index'], 'monster_id': identity, 'color': color,
                         'enhanced': row == 0, 'position': actor['position']})
    (assets / 'worlds/mm8/maps/lg01.scene.yml').write_text(json.dumps(scene, indent=2) + '\n')
    # Also exercise the shared indoor renderer in Greywatch's entrance hall.
    indoor = json.loads((PROJECT / 'runtime/worlds/mm8/maps/lg02.scene.yml').read_text())
    indoor_actors = indoor['initial_state']['actors']
    for i, (identity, _, color, _) in enumerate(VARIANTS):
        actor = copy.deepcopy(actors[-6 + i * 2])
        actor['actor_index'] = len(indoor_actors)
        actor['position'] = dict(x=-384 + i * 384, y=256, z=768)
        actor['sector_id'] = 1
        indoor_actors.append(actor)
    (assets / 'worlds/mm8/maps/lg02.scene.yml').write_text(json.dumps(indoor, indent=2) + '\n')
    settings = configparser.ConfigParser()
    settings.read(stage / 'settings.ini')
    settings['startup'] = {'start_in_main_menu': 'true'}
    settings['debug']['new_game_god_lich'] = 'true'
    settings['debug']['start_map_file'] = 'lg01.odm'
    settings['video'] = {'resolution': '1600x1200', 'fullscreen': 'false', 'vsync': 'false'}
    with (stage / 'settings.ini').open('w') as stream:
        settings.write(stream, space_around_delimiters=False)
    party = json.loads((PROJECT / 'source/baseline_party.json').read_text())
    pose = dict(map='lg01.odm', x=-18816, y=-1664, z=terrain_height(-18816, -1664, samples), yaw=0, pitch=0)
    steps = [{'new_game_flow': {'start_map': 'lg01.odm', 'party': party}}, {'set_pose': pose}]
    if god_source_save:
        steps = [{'load_game': {'path': str(god_source_save.resolve(strict=True))}}, {'set_pose': pose}]
    steps += [{'assert': {'actor_visible': {'actor_index': row['actor_index'], 'monster_id': row['monster_id'],
                                          'dead': False}}} for row in demo]
    steps += [{'save_game': 'crusader_demo'}]
    scenario = {'id': 'custom_crusader_demo', 'world': 'mm8', 'mode': 'faithful', 'steps': steps}
    path = stage / 'prepare_demo.yml'
    path.write_text(yaml.safe_dump(scenario, sort_keys=False))
    with (stage / 'prepare_demo.log').open('w') as stream:
        subprocess.run([str(REPO / 'build/game/openyamm'), '--world', 'mm8', '--headless-run-scenario', str(path),
                        '--scenario-no-color'], cwd=stage, stdout=stream, stderr=subprocess.STDOUT, check=True)
    (stage / 'saves').mkdir(exist_ok=True)
    shutil.copy2('/tmp/openyamm_scenario_saves/custom_crusader_demo/crusader_demo.oysav',
                 stage / 'saves/crusader_demo.oysav')
    (ROOT / 'review/runtime_demo.json').write_text(json.dumps({'stage': str(stage), 'pose': pose, 'actors': demo}, indent=2))
    print(stage)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('/tmp/openyamm-crusader-playtest'))
    parser.add_argument('--god-source-save', type=Path, default=ROOT / 'playtest/crusader_demo.oysav',
                        help='Preserve a God character created through New Game')
    args = parser.parse_args()
    prepare(args.directory.resolve(), args.god_source_save)
