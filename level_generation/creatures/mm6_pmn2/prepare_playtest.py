"""Stage Brackenford's seven mage groups and create fresh God-character starts."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import yaml

from install_runtime import ROOT, REPO, VARIANTS

PROJECT = REPO / 'level_generation/projects/brackenford_greywatch'


def prepare(stage, god_source):
    assert not stage.exists(), 'Use a new directory; existing snapshots may contain personal saves.'
    god_source = god_source.resolve(strict=True)
    subprocess.run([sys.executable, str(PROJECT / 'stage_runtime.py'), '--package',
                    str(PROJECT / 'dist/brackenford_greywatch_content.zip'), '--directory', str(stage),
                    '--no-project-state'], check=True)
    scene = json.loads((stage / 'assets_editor_dev/worlds/mm8/maps/lg01.scene.yml').read_text())
    mages = [actor for actor in scene['initial_state']['actors'] if actor['monster_id'] in [904, 905, 906]]
    assert len(mages) == 21 and len({actor['group'] for actor in mages}) == 7
    binary = stage / 'openyamm'
    shutil.copy2(REPO / 'build/game/openyamm', binary)
    settings = configparser.ConfigParser()
    settings.read(stage / 'settings.ini')
    settings['startup'] = {'start_in_main_menu': 'true'}
    settings['video'] = {'resolution': '1600x1200', 'fullscreen': 'false', 'vsync': 'false'}
    with (stage / 'settings.ini').open('w') as stream:
        settings.write(stream, space_around_delimiters=False)

    sys.path.insert(0, str(PROJECT))
    from build_outdoor_content import terrain_height
    heights = bytes.fromhex(json.loads((PROJECT / 'source/lg01.terrain.yml').read_text())['height_map_hex'])
    pose = dict(map='lg01.odm', x=15360, y=10000, z=terrain_height(15360, 10000, heights), yaw=0, pitch=0)
    arrival = next(entry['position'] for entry in json.loads((PROJECT / 'source/lg01.semantic.json').read_text())
                   ['arrivals'] if entry['id'] == 'default')
    town_pose = dict(map='lg01.odm', **dict(zip('xyz', arrival)), yaw=0, pitch=0)
    steps = [{'load_game': {'path': str(god_source)}}, {'set_pose': town_pose}]
    steps += [{'assert': {'actor_visible': dict(actor_index=a['actor_index'], monster_id=a['monster_id'],
                dead=False, hostile_to_party=True, current_hp=a['hp'])}} for a in mages]
    steps += [{'save_game': 'Brackenford_God'}, {'set_pose': pose}, {'save_game': 'Mage_Groups_God'},
              {'advance_runtime': {'seconds': 1}}]
    # The nearest trio must engage the party, not merely have a hostile source flag.
    steps += [{'assert': {'actor_visible': dict(actor_index=a['actor_index'], monster_id=a['monster_id'],
                hostile_to_party=True, has_detected_party=True, combat_targeting_party=True)}} for a in mages[3:6]]
    scenario_id = 'pmn2_playtest_' + hashlib.sha256(str(stage).encode()).hexdigest()[:10]
    source = stage / 'prepare.yml'
    source.write_text(yaml.safe_dump(dict(id=scenario_id, world='mm8', mode='faithful', steps=steps), sort_keys=False))
    with (stage / 'prepare.log').open('w') as stream:
        subprocess.run([str(binary), '--world', 'mm8', '--headless-run-scenario', str(source),
                        '--scenario-no-color'], cwd=stage, stdout=stream, stderr=subprocess.STDOUT, check=True)
    saves = stage / 'saves'
    saves.mkdir()
    checks = []
    for name in ['Brackenford_God', 'Mage_Groups_God']:
        destination = saves / (name + '.oysav')
        shutil.copy2(Path('/tmp/openyamm_scenario_saves') / scenario_id / (name + '.oysav'), destination)
        checks += [{'load_game': {'path': str(destination)}}, {'assert': {'map': 'lg01.odm'}},
                   {'assert': {'runtime_event_variable': {'id': 9, 'member_index': 0, 'value': 100}}}]
        checks += [{'assert': {'actor_visible': dict(actor_index=a['actor_index'], monster_id=a['monster_id'],
                                                   dead=False, hostile_to_party=True)}} for a in mages]
    source = stage / 'verify.yml'
    source.write_text(yaml.safe_dump(dict(id=scenario_id + '_reload', world='mm8', mode='faithful', steps=checks),
                                     sort_keys=False))
    with (stage / 'verify.log').open('w') as stream:
        subprocess.run([str(binary), '--world', 'mm8', '--headless-run-scenario', str(source),
                        '--scenario-no-color'], cwd=stage, stdout=stream, stderr=subprocess.STDOUT, check=True)
    # Scenario saves share a display label; separate launch folders make the chosen start unambiguous.
    for mode, name in [('mages', 'Mage_Groups_God'), ('town', 'Brackenford_God')]:
        directory = stage / mode
        (directory / 'saves').mkdir(parents=True)
        shutil.copy2(stage / 'settings.ini', directory / 'settings.ini')
        shutil.copy2(saves / (name + '.oysav'), directory / 'saves' / (name + '.oysav'))
    report = dict(stage=str(stage), pose=pose, actors=mages, group_count=7,
                  binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                  validation='All 21 hostile actors and both God saves checked; nearby trio detected/targeted party.')
    (ROOT / 'review/runtime').mkdir(exist_ok=True)
    (ROOT / 'review/runtime/playtest.json').write_text(json.dumps(report, indent=2) + '\n')
    (stage / 'playtest_snapshot.json').write_text(json.dumps(report, indent=2) + '\n')
    print(stage)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('/tmp/openyamm-pmn2-playtest'))
    parser.add_argument('--god-source-save', type=Path, default=ROOT / 'playtest/god_source.oysav')
    args = parser.parse_args()
    prepare(args.directory.resolve(), args.god_source_save)
