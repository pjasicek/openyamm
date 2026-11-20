#!/usr/bin/env python3
"""Takes in-game pictures of an original outdoor map and of its rebuild from the same cameras, and measures how
alike each pair is: the outdoor twin of ingame_compare.py.

  outdoor_ingame.py <project> <world> <original map file> <shots.yml> <output folder> --root <scratch asset root>
                    [--oymap <binary>] [--only <name,name>] [--with-actors] [--no-game] [--weather <n|auto>]
                    [--time HH:MM]

shots.yml: `shots: [{name, at: [x, y, z], yaw, pitch}]`, map units, yaw in radians (0 east, counter-clockwise),
pitch in degrees (negative down); `oymap compare --out` writes one for an outdoor pair: its twelve worst regions,
each from its south side. The camera stands at exactly the same place in both maps (outdoors a camera is not
put on the ground: the land's height is what is compared).

The project is copied into <output>/project and built there (the project itself is only read), installed into the
scratch root (a hard-link copy of assets_dev: `cp -al assets_dev <root>`; never assets_dev itself), and given its
terrain material file with outdoor_materials.py, without which the game draws no ground. Pictures are taken with
the HUD off, and with actors and effects off unless --with-actors (monsters wander; decorations stay on).

Both maps are shown under the same weather. The game rolls a map's weather for the day from the map's number, so
an original and its rebuild (which has a number of its own) have different skies and fog on the same day; and
which skies a map has at all comes from its continent in its row of engine/data_tables/bolster_maps.txt, which
`oymap install` writes for the rebuild (core/OutdoorInstall.cpp). So every shot first sets the weather by the
debug console: `sky weather <n>` (the step of the continent's skies from clear to storm, 0 when --weather is left
out: the clear sky) and `weather clear` (no rain or snow); `--weather auto` leaves each map its own roll.
`--time HH:MM` moves both clocks to that hour first (the game starts at 09:00). The sky each side was drawn
under is written to <output>/<side>.sky.txt and printed; the script says so when they differ (a rebuild
installed without its bolster row has no skies to step through).

Writes <output>/original/NN-name.png, <output>/rebuilt/NN-name.png, and through ingame_compare.py's measure for
every pair <output>/diff/NN-name.png and <output>/pixels.json (edge agreement, blurred difference).
`--no-game` measures the pictures already in the output folder again."""
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

studio = Path(__file__).resolve().parents[1]
repo = studio.parent
assets = repo / 'assets_dev'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from outdoor_materials import make_materials, take_option  # noqa: E402


def measure(output):
    """ingame_compare.py's sheets and scores over the two picture folders."""
    done = subprocess.run([sys.executable, str(studio / 'calibration/ingame_compare.py'), '-', '-', '-', '-',
                           str(output), '--no-game'], capture_output=True, text=True)
    print((done.stdout + done.stderr).strip())


def sky_of(launcher_output):
    """The last answer of the tour's `sky` command in the run's measurement log: what the map was drawn under."""
    record = [line.split(':', 1)[1].strip() for line in launcher_output.splitlines()
              if line.startswith('Run record:')]
    if not record:
        return 'unknown (no run record)'
    log = Path(record[-1]).parent / 'measurement.log'
    if not log.is_file():
        return 'unknown (no measurement log)'
    answers = [line.split('weather_sky=', 1)[1] for line in log.read_text(errors='replace').splitlines()
               if 'weather_sky=' in line]
    return 'weather_sky=' + answers[-1].strip() if answers else 'unknown (the sky command gave no answer)'


def sky_name(answer):
    """The sky texture and the fog of a `sky` answer, without what differs by the map's own clouds."""
    return ' '.join(word for word in answer.split() if word.split('=')[0] in ('weather_sky', 'sky_name', 'foggy',
                                                                             'fog'))


def main():
    arguments = sys.argv[1:]
    root = take_option(arguments, '--root')
    oymap = take_option(arguments, '--oymap', os.environ.get('OYMAP', str(studio / 'build/oymap')))
    only = take_option(arguments, '--only')
    weather = take_option(arguments, '--weather', '0')
    hour = take_option(arguments, '--time')
    with_actors = '--with-actors' in arguments
    no_game = '--no-game' in arguments
    for flag in ('--with-actors', '--no-game'):
        if flag in arguments:
            arguments.remove(flag)
    if len(arguments) != 5 or (root is None and not no_game):
        sys.exit(__doc__)
    source, world, original, shots_file, output = arguments
    output = Path(output).resolve()
    if no_game:
        measure(output)
        return
    root = Path(root).resolve()
    if root == assets.resolve() or not root.is_dir():
        sys.exit(f'{root}: name a scratch asset root that exists (cp -al assets_dev <root>), never assets_dev')
    shots = yaml.safe_load(Path(shots_file).read_text())['shots']
    if only:
        shots = [shot for shot in shots if shot['name'] in only.split(',')]
    project = output / 'project'
    shutil.rmtree(project, ignore_errors=True)
    project.mkdir(parents=True)
    for entry in sorted(Path(source).iterdir()):
        if entry.is_file():
            shutil.copy2(entry, project / entry.name)
    card = yaml.safe_load((project / 'project.yml').read_text())
    rebuilt = card['id'].lower() + '.odm'
    for command in ([oymap, 'build', str(project), '--assets', str(assets)],
                    [oymap, 'install', str(project), '--root', str(root)]):
        done = subprocess.run(command, capture_output=True, text=True)
        if done.returncode != 0:
            sys.exit(f'{" ".join(command)} failed:\n{done.stdout}{done.stderr}')
    print('materials:', ', '.join(make_materials(project, root)))
    commands = ['render hud off'] + ([] if with_actors else ['render actors off', 'render effects off'])
    if weather != 'auto':
        commands += [f'sky weather {int(weather)}', 'weather clear']
    commands.append('sky')
    skies = {}
    for side, map_file in (('original', original), ('rebuilt', rebuilt)):
        folder = output / side
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
        lines = [f'output_dir: "{folder}"', 'exit: true', 'settle_seconds: 2.5', 'shots:']
        for shot in shots:
            x, y, z = shot['at']
            quoted = ', '.join(f'"{command}"' for command in commands)
            clock = f', time: "{hour}"' if hour else ''
            lines.append(f'  - {{name: {shot["name"]}, position: [{x}, {y}, {z}], yaw: {shot["yaw"]}, '
                         f'pitch: {math.radians(shot.get("pitch", 0.0)):.4f}{clock}, commands: [{quoted}]}}')
        tour = output / f'{side}.tour.yml'
        tour.write_text('\n'.join(lines) + '\n')
        environment = dict(os.environ, SDL_AUDIODRIVER='dummy')
        run = subprocess.run([str(repo / 'tools/run_game.sh'), '--isolated', f'studiooutdoor{side}{os.getpid()}',
                              '--world', world, '--map', map_file, '--assets', str(root), '--warmup', '5',
                              '--seconds', str(25 + 4 * len(shots)), '--set', f'debug.screenshot_tour_path={tour}'],
                             capture_output=True, text=True, env=environment)
        (output / f'{side}.run.log').write_text(run.stdout + run.stderr)
        skies[side] = sky_of(run.stdout + run.stderr)
        (output / f'{side}.sky.txt').write_text(skies[side] + '\n')
        print(side, len(list(folder.glob('*.png'))), 'pictures; sky:', skies[side])
    if sky_name(skies['original']) != sky_name(skies['rebuilt']):
        print('THE TWO MAPS WERE DRAWN UNDER DIFFERENT SKIES: the pairs do not compare the maps alone. Install '
              'the rebuild with an oymap that writes its row of bolster_maps.txt.')
    measure(output)


if __name__ == '__main__':
    main()
