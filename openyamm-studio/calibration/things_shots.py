#!/usr/bin/env python3
"""Pictures of every interactive thing of an indoor map, from where a player uses it, before and after it is used.

  things_shots.py <map file | project> <world> <output folder> --root <scratch asset root>
                  [--oymap <binary>] [--kinds lever,button,switch,door,chest,...] [--near x,y,radius] [--no-use]
                  [--no-game]

The things come from `oymap things --json` (every face a click runs an event from, grouped by the event; clicked
decorations): what each is (door, lever, button, switch, chest, exit, teleport, panel, decoration), its textures, what
using it changes, and where a player stands to use it (in front of it, on the floor there, looking at its middle from
the party's eye). A project is read as the game would read it (built privately; its ids name the things); a map file
is read from the root, where a rebuild must be installed first (`oymap install <project> --root <root>`).

For each thing the game takes `NN-<kind>-e<event>-before.png`; where using it is harmless (no chest screen, question,
teleport or leaving the map) and `--no-use` is not given, its event is run and `-used.png` is taken once its parts
have moved, then it is run again and `-again.png` taken (a lever pulled and pulled back, a door shut again). One game
run per group of things that want about the same downward look: the run's single screenshot-tour shot sets the pitch
(the game has no console word for it), then a menu-input tour moves the party to each place with evt.MoveToMap
(position and facing), takes the pictures and runs the events (`event <n>` in the console). The HUD is off.

Writes things.json (oymap's list), shots.json (each thing's pictures) and contact.png (every picture, small, with its
caption) into the output folder. `--no-game` makes the contact sheet again from the pictures there.
"""
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

studio = Path(__file__).resolve().parents[1]
repo = studio.parent
oymap = os.environ.get('OYMAP', str(studio / 'build/oymap'))
PART_SECONDS = 3.5


def take_option(arguments, name, default=None):
    if name in arguments:
        at = arguments.index(name)
        value = arguments[at + 1]
        del arguments[at:at + 2]
        return value
    return default


def take_flag(arguments, name):
    if name in arguments:
        arguments.remove(name)
        return True
    return False


def list_things(target, world, root):
    command = [oymap, 'things', target, '--assets', str(root), '--json']
    if not Path(target, 'project.yml').is_file():
        command[3:3] = ['--world', world]
    run = subprocess.run(command, capture_output=True, text=True)
    if run.returncode != 0:
        sys.exit(f'oymap things failed: {run.stderr.strip()}')
    return json.loads(run.stdout)


def direction_units(yaw):
    """The engine's facing (2048 to the full turn, 0 east, counter-clockwise) of a yaw in radians."""
    return int(round(yaw * 2048.0 / (2.0 * math.pi))) % 2048


def shot_name(index, thing):
    return f'{index:02d}-{thing["kind"]}-e{thing["event"]}'


def contact_sheet(output, shots):
    pictures = []
    for shot in shots:
        for state in ('before', 'used', 'again'):
            path = output / 'pictures' / f'{shot["name"]}-{state}.png'
            if path.exists():
                pictures.append((path, f'{shot["name"]} {state}: {shot["caption"]}'))
    if not pictures:
        return
    width, height, columns = 400, 225, 3
    rows = (len(pictures) + columns - 1) // columns
    sheet = Image.new('RGB', (columns * width, rows * (height + 18)), (16, 16, 20))
    draw = ImageDraw.Draw(sheet)
    for index, (path, caption) in enumerate(pictures):
        column, row = index % columns, index // columns
        picture = Image.open(path).convert('RGB').resize((width, height), Image.LANCZOS)
        sheet.paste(picture, (column * width, row * (height + 18) + 18))
        draw.text((column * width + 4, row * (height + 18) + 3), caption[:64], fill=(235, 235, 235))
    sheet.save(output / 'contact.png')
    print(f'contact sheet: {output / "contact.png"} ({len(pictures)} pictures)')


def main():
    arguments = sys.argv[1:]
    global oymap
    root = take_option(arguments, '--root')
    oymap = take_option(arguments, '--oymap', oymap)
    kinds = take_option(arguments, '--kinds')
    near = take_option(arguments, '--near')
    no_use = take_flag(arguments, '--no-use')
    no_game = take_flag(arguments, '--no-game')
    if len(arguments) != 3 or root is None:
        sys.exit(__doc__)
    target, world, output = arguments
    root = Path(root).resolve()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if no_game:
        contact_sheet(output, json.loads((output / 'shots.json').read_text()))
        return

    listed = list_things(target, world, root)
    (output / 'things.json').write_text(json.dumps(listed, indent=2) + '\n')
    things = listed['things']
    if kinds:
        things = [thing for thing in things if thing['kind'] in kinds.split(',')]
    if near:
        x, y, radius = (float(value) for value in near.split(','))
        things = [thing for thing in things if math.hypot(thing['middle'][0] - x, thing['middle'][1] - y) <= radius]
    map_file = listed['map']
    pictures = output / 'pictures'
    shutil.rmtree(pictures, ignore_errors=True)
    pictures.mkdir(parents=True)

    shots = []
    for index, thing in enumerate(things, 1):
        textures = ', '.join(f'{name} {count}' for name, count in thing['textures'].items())
        shots.append({'name': shot_name(index, thing), 'event': thing['event'], 'kind': thing['kind'],
                      'use': thing['safe_to_use'] and not no_use, 'stand': thing['stand'], 'yaw': thing['yaw'],
                      'pitch': thing['pitch'], 'caption': f'{thing["title"] or thing["id"]} ({textures})',
                      'overlaps': thing['overlaps'], 'changes': thing['changes']})
    (output / 'shots.json').write_text(json.dumps(shots, indent=2) + '\n')

    # One run for each look downward (to a tenth of a radian): the screenshot tour's one shot sets it.
    groups = {}
    for shot in shots:
        groups.setdefault(round(shot['pitch'], 1), []).append(shot)
    for group_index, (pitch, group) in enumerate(sorted(groups.items())):
        first = group[0]
        stand = first['stand']
        tour = output / f'pose{group_index}.tour.yml'
        tour.write_text('\n'.join([
            f'output_dir: "{output / "scratch"}"', 'exit: false', 'settle_seconds: 1.0', 'shots:',
            f'  - {{name: pose, position: [{stand[0]}, {stand[1]}, {stand[2]}], yaw: {first["yaw"]}, '
            f'pitch: {pitch}, commands: ["render hud off"]}}']) + '\n')
        steps = ['  - wait: 9', '  - console: render hud off']
        for shot in group:
            x, y, z = shot['stand']
            steps.append(f'  - console: lua evt.MoveToMap({x}, {y}, {z}, {direction_units(shot["yaw"])}, 0, 0, 0, 0)')
            steps.append('  - wait: 1.5')
            steps.append(f'  - capture: {shot["name"]}-before')
            if shot['use']:
                for state in ('used', 'again'):
                    steps.append(f'  - console: event {shot["event"]}')
                    steps.append(f'  - wait: {PART_SECONDS}')
                    steps.append(f'  - capture: {shot["name"]}-{state}')
        menu = output / f'run{group_index}.menu.yml'
        menu.write_text('\n'.join([f'output_dir: "{pictures}"', 'exit: true', 'steps:'] + steps) + '\n')
        seconds = 40 + sum(2 + (2 * PART_SECONDS + 1 if shot['use'] else 0) for shot in group)
        command = [str(repo / 'tools/run_game.sh'), '--isolated', f'studiothings{os.getpid()}g{group_index}',
                   '--world', world, '--map', map_file, '--assets', str(root), '--warmup', '5',
                   '--seconds', str(int(seconds)), '--set', f'debug.screenshot_tour_path={tour}',
                   '--set', f'debug.menu_input_tour_path={menu}']
        environment = dict(os.environ, SDL_AUDIODRIVER='dummy')
        run = subprocess.run(command, capture_output=True, text=True, env=environment)
        taken = len(list(pictures.glob('*.png')))
        print(f'pitch {pitch}: {len(group)} things, run exit {run.returncode}, {taken} pictures so far')
        if run.returncode != 0 and taken == 0:
            print('\n'.join(('    ' + line) for line in (run.stdout + run.stderr).strip().splitlines()[-20:]))
    contact_sheet(output, shots)


main()
