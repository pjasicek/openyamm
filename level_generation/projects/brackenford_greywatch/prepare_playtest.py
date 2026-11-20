"""Create an isolated playable snapshot with a copied executable and ordinary level25 starting saves.

Never refresh an existing playtest snapshot: the driver may be playing it while generation continues.
"""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--directory', type=Path, default=Path('/tmp/openyamm-brackenford-playtest'))
parser.add_argument('--package', type=Path, help='Install the exported content archive')
parser.add_argument('--no-project-state', action='store_true', help='Keep the authoring project staging pointer')
parser.add_argument('--god-source-save', type=Path,
                    help='Seed starts from the built-in God character saved before visiting these generated maps')
args = parser.parse_args()
destination = args.directory.resolve()
if (destination / 'playtest_snapshot.json').exists():
    raise SystemExit('This snapshot already exists and may be in use. Choose a new --directory.')
install = [sys.executable, str(PROJECT / 'stage_runtime.py'), '--directory', str(destination)]
if args.package:
    install += ['--package', str(args.package.resolve())]
if args.no_project_state:
    install += ['--no-project-state']
subprocess.run(install, check=True)
executable = destination / 'openyamm'
shutil.copy2(ROOT / 'build/game/openyamm', executable)
party = json.loads((PROJECT / 'source/baseline_party.json').read_text())
level = 100 if args.god_source_save else 25
party_label = 'God' if args.god_source_save else 'Level25'
scenario_id = 'levelgen_playtest_' + hashlib.sha256(str(destination).encode()).hexdigest()[:12]
steps = []
for name, map_file in [('outdoor', 'lg01.odm'), ('indoor', 'lg02.blv')]:
    if args.god_source_save:
        if name == 'outdoor':
            semantic = json.loads((PROJECT / 'source/lg01.semantic.json').read_text())
            position = next(a['position'] for a in semantic['arrivals'] if a['id'] == 'default')
            yaw = 0
        else:
            arrival = json.loads((PROJECT / 'source/lg02.semantic.json').read_text())['arrivals']['castle']
            position = arrival['position']
            yaw = arrival['direction_degrees'] * 3.141592653589793 / 180
        steps += [{'load_game': {'path': str(args.god_source_save.resolve(strict=True))}},
                  {'set_pose': dict(map=map_file, **dict(zip('xyz', position)), yaw=yaw, pitch=0)}]
    else:
        steps += [{'new_game_flow': {'start_map': map_file, 'party': party}}]
    steps += [{'save_game': name}]
scenario = {'id': scenario_id, 'title': f'Prepare playable {party_label} starting saves',
            'world': 'mm8', 'mode': 'faithful', 'steps': steps}
source = destination / 'prepare_starts.yml'
source.write_text(yaml.safe_dump(scenario, sort_keys=False))
with (destination / 'prepare_starts.log').open('w') as output:
    subprocess.run([str(executable), '--world', 'mm8', '--headless-run-scenario', str(source),
                    '--scenario-no-color'], cwd=destination, stdout=output, stderr=subprocess.STDOUT, check=True)

settings = configparser.ConfigParser()
settings.read(str(destination / 'settings.ini'))
settings['startup']['start_in_main_menu'] = 'true'
settings['audio']['sound_volume'] = '9'
settings['audio']['music_volume'] = '6'
settings['audio']['voice_volume'] = '9'
verification = []
for name, map_file in [('outdoor', 'lg01.odm'), ('indoor', 'lg02.blv')]:
    play_directory = destination / name
    saves = play_directory / 'saves'
    saves.mkdir(parents=True, exist_ok=True)
    with (play_directory / 'settings.ini').open('w') as output:
        settings.write(output, space_around_delimiters=False)
    save = saves / (('Brackenford_' if name == 'outdoor' else 'Greywatch_') + party_label + '.oysav')
    shutil.copy2(Path('/tmp/openyamm_scenario_saves') / scenario_id / (name + '.oysav'), save)
    verification += [{'load_game': {'path': str(save)}}, {'assert': {'map': map_file}}]
    verification += [{'assert': {'runtime_event_variable': {'id': 9, 'member_index': i, 'value': level}}}
                     for i in range(1 if args.god_source_save else 5)]
scenario.update(id=scenario_id + '_verify', title='Verify copied playtest saves and executable', steps=verification)
source = destination / 'verify_starts.yml'
source.write_text(yaml.safe_dump(scenario, sort_keys=False))
with (destination / 'verify_starts.log').open('w') as output:
    subprocess.run([str(executable), '--world', 'mm8', '--headless-run-scenario', str(source),
                    '--scenario-no-color'], cwd=destination, stdout=output, stderr=subprocess.STDOUT, check=True)

launcher = destination / 'play.sh'
launcher.write_text('''#!/usr/bin/env bash
set -euo pipefail
playtest_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
case "${1:-outdoor}" in
    outdoor) playtest_mode=outdoor ;;
    indoor) playtest_mode=indoor ;;
    *) echo 'Usage: play.sh [outdoor|indoor]' >&2; exit 2 ;;
esac
cd -- "$playtest_root/$playtest_mode"
exec "$playtest_root/openyamm" --world mm8
''')
launcher.chmod(0o755)
manifest = {'created_utc': datetime.now(timezone.utc).isoformat(), 'project': str(PROJECT),
            'status': 'frozen playable snapshot',
            'package_sha256': hashlib.sha256(args.package.read_bytes()).hexdigest() if args.package else None,
            'binary_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
            'native_sha256': {name: hashlib.sha256((destination / 'assets_editor_dev/worlds/mm8/maps' / name)
                             .read_bytes()).hexdigest() for name in ['lg01.odm', 'lg02.blv']},
            'launch': [str(launcher) + ' outdoor', str(launcher) + ' indoor'],
            'instructions': f'Choose Load Game, then the single Scenario entry. This loads the {party_label} party.',
            'god_source_save': str(args.god_source_save) if args.god_source_save else None,
            'isolation': 'Copied executable, maps, scripts and tables; separate settings/saves per launch. Original art is shared.',
            'verification': 'Both copied starting saves loaded using the copied executable; map and party level checked.'}
(destination / 'playtest_snapshot.json').write_text(json.dumps(manifest, indent=2) + '\n')
(destination / 'README.md').write_text('''# Brackenford / Greywatch playtest

Run `./play.sh outdoor` or `./play.sh indoor`. At the main menu choose **Load Game**, then the single **Scenario**
entry. It loads the prepared ordinary five-member level25 party at the selected map's start.

Both dungeon entrances in Brackenford lead to different entrances of Greywatch and return to Brackenford.
Use normal game saves while playing; outdoor/indoor launch folders have separate settings and saves.
This is a frozen development snapshot; subsequent generation builds do not refresh it.

This revision includes the populated terrain/town, varied houses, both entrances, working services/travel,
chest rewards/refill, native lighting, click-operated doors and automatic lift. Functional evidence and precise
limits are in the project's ACCEPTANCE.md. Final combat balance belongs to the driver.

Ordinary doors open by clicking. The records-room control unlocks the shortcut; its landing controls then
operate it from either side. Step onto the lift to ride; its wall controls can also call/recover it. Secret walls
and pressure plates use native Perception highlighting. Dungeon traps fire once per map refill.

The west road goes to Ravenshore; the north road goes to Alvar. Their original stables gain a daily return
in this isolated installation. Brackenford stables retain the borrowed MM8 schedule for their Alvar trip.
''')
if args.god_source_save:
    readme = destination / 'README.md'
    readme.write_text(readme.read_text().replace('ordinary five-member level25 party',
        'built-in God level-100 Lich (Grandmaster-200 skills and all spells)'))
print(json.dumps(manifest, indent=2))
