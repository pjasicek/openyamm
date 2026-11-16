#!/usr/bin/env python3
"""Takes in-game pictures of an original map and of its rebuild from the same camera positions, and measures how
alike each pair is.

  ingame_compare.py <project> <world> <original map file> <shots.yml> <output folder>
                    [--root <scratch asset root>] [--oymap <binary>] [--no-game]

shots.yml: `shots: [{name, at: [x, y] or [x, y, z], yaw, pitch?, rebuilt_z?, exact?}]` in map units and radians
(`oymap compare --out` writes one of its worst points; rebuilt_z is the rebuild's floor height where it is known).
The camera stands on the floor under each point in each map (found with `oymap probe`: the highest floor, or with
a z the floor at that height), so a rebuild whose floors differ a little is still seen from eye height. `pitch`
(default 0, up is positive) tilts the camera: down from a balcony, up at a vault. `exact: true` takes `at`'s z as
the height the camera stands at in both maps, with no floor looked up (a view from mid-air, or from a floor the
lookup does not find). The project is copied into <output>/project and built there, so the project itself is only read.
The rebuild is installed into a scratch asset root (default output/studio_slice_root, a hard-link copy of
assets_dev), because the desktop launcher takes an asset root and no mount.

Pictures are taken with the HUD off and the world stopped (a screenshot tour freezes gameplay). The engine has no
switch for monsters, decorations or lights of an indoor map, so the original's furniture and creatures stay in its
pictures; the outdoor layers (actors, decoration sprites, effects) are switched off for outdoor maps.

Writes <output>/original/NN-name.png, <output>/rebuilt/NN-name.png, and for every pair <output>/diff/NN-name.png
(original, rebuild, and their difference with the original's edges in cyan, the rebuild's in orange, shared ones
white) and <output>/pixels.json:
  edges_original_found  share of the original's edge pixels with an edge of the rebuild within 3 pixels
  edges_rebuilt_found   the same the other way round
  edge_agreement        the mean of the two
  blurred_difference    mean absolute difference of the blurred greyscale pictures, 0 to 1
Both pictures are reduced to 640 pixels wide and greyscale, brought to the same mean brightness and lifted
together to a middle grey first (dungeons are dark).
`--no-game` measures the pictures already in the output folder again.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFilter

studio = Path(__file__).resolve().parents[1]
repo = studio.parent
assets = repo / 'assets_dev'
oymap = os.environ.get('OYMAP', str(studio / 'build/oymap'))

# What the console can switch off for a picture. `render hud off` works on every map; the three layers are the
# outdoor view's and change nothing indoors.
SHOT_COMMANDS = ['render hud off', 'render actors off', 'render deco_sprites off', 'render effects off']
WORK_WIDTH = 640
EDGE_REACH = 3


def floor_under(target, world, root, x, y, below=4000):
    """The highest floor at or below a height, by the core's own floor lookup."""
    command = [oymap, 'probe', target, '--assets', str(root), '--from', f'{x},{y},{below}', '--to', f'{x},{y},{below}']
    if world:
        command[3:3] = ['--world', world]
    out = subprocess.run(command, capture_output=True, text=True).stdout
    found = re.search(r'from: floor z (-?\d+)', out)
    return int(found[1]) if found else None


def grey_of(path):
    """A picture as greyscale floats, WORK_WIDTH wide."""
    picture = Image.open(path).convert('L')
    height = max(1, round(picture.height * WORK_WIDTH / picture.width))
    return picture.resize((WORK_WIDTH, height), Image.LANCZOS)


def blurred(grey, radius):
    return np.asarray(grey.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)


def edges_of(values):
    """Sobel edges of a blurred greyscale array: the strongest eighth of the picture, and never flat noise."""
    padded = np.pad(values, 1, mode='edge')
    across = (padded[:-2, 2:] + 2 * padded[1:-1, 2:] + padded[2:, 2:]
              - padded[:-2, :-2] - 2 * padded[1:-1, :-2] - padded[2:, :-2])
    down = (padded[2:, :-2] + 2 * padded[2:, 1:-1] + padded[2:, 2:]
            - padded[:-2, :-2] - 2 * padded[:-2, 1:-1] - padded[:-2, 2:])
    strength = np.hypot(across, down)
    return strength > max(float(np.percentile(strength, 87.5)), 24.0)


def near(mask):
    """A mask grown by EDGE_REACH pixels."""
    picture = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * EDGE_REACH + 1))
    return np.asarray(picture) > 0


def compare_pair(original_path, rebuilt_path, sheet_path, title):
    original = grey_of(original_path)
    rebuilt = grey_of(rebuilt_path).resize(original.size, Image.LANCZOS)
    first = np.asarray(original, dtype=np.float32)
    second = np.asarray(rebuilt, dtype=np.float32)
    # The same mean brightness: lighting differs between a shipped map and a fresh build.
    gain = float(first.mean()) / max(1.0, float(second.mean()))
    # Dungeons are dark: both are lifted by one factor to a middle grey, so edges are found in dim pictures too.
    lift = min(6.0, max(1.0, 96.0 / max(1.0, float(first.mean()))))
    original = Image.fromarray(np.clip(first * lift, 0, 255).astype(np.uint8))
    rebuilt = Image.fromarray(np.clip(second * gain * lift, 0, 255).astype(np.uint8))
    first_edges = edges_of(blurred(original, 1.5))
    second_edges = edges_of(blurred(rebuilt, 1.5))
    first_found = float((first_edges & near(second_edges)).sum()) / max(1, int(first_edges.sum()))
    second_found = float((second_edges & near(first_edges)).sum()) / max(1, int(second_edges.sum()))
    difference = np.abs(blurred(original, 8) - blurred(rebuilt, 8))
    scores = {
        'edges_original_found': round(first_found, 3),
        'edges_rebuilt_found': round(second_found, 3),
        'edge_agreement': round((first_found + second_found) / 2, 3),
        'blurred_difference': round(float(difference.mean()) / 255.0, 4),
        'brightness_gain': round(gain, 3),
        'lift': round(lift, 2),
    }

    # The sheet: original, rebuild, and the difference (bright where the blurred pictures differ) under the edges.
    width, height = original.size
    base = np.clip(difference * 1.5, 0, 255).astype(np.uint8)
    panel = np.stack([base, base, base], axis=2)
    panel[first_edges & ~second_edges] = (0, 200, 255)
    panel[second_edges & ~first_edges] = (255, 140, 0)
    panel[first_edges & second_edges] = (255, 255, 255)
    band = 28
    sheet = Image.new('RGB', (width * 3 + 8, height + band), (16, 16, 20))
    sheet.paste(Image.open(original_path).convert('RGB').resize((width, height), Image.LANCZOS), (0, band))
    sheet.paste(Image.open(rebuilt_path).convert('RGB').resize((width, height), Image.LANCZOS), (width + 4, band))
    sheet.paste(Image.fromarray(panel), (2 * width + 8, band))
    draw = ImageDraw.Draw(sheet)
    draw.text((6, 8), f'original   {title}', fill=(235, 235, 235))
    draw.text((width + 10, 8), 'rebuilt', fill=(235, 235, 235))
    draw.text((2 * width + 14, 8),
              f'edges: original cyan, rebuilt orange, both white   agreement {scores["edge_agreement"]:.2f}   '
              f'difference {scores["blurred_difference"]:.3f}', fill=(235, 235, 235))
    sheet.save(sheet_path)
    return scores


def measure(output):
    """Difference sheets and scores of every pair in the output folder, and the summary."""
    sheets = output / 'diff'
    shutil.rmtree(sheets, ignore_errors=True)
    sheets.mkdir(parents=True)
    by_name = {side: {re.sub(r'^\d+-', '', path.stem): path for path in sorted((output / side).glob('*.png'))}
               for side in ('original', 'rebuilt')}
    pairs = []
    for number, (name, original_path) in enumerate(by_name['original'].items(), 1):
        rebuilt_path = by_name['rebuilt'].get(name)
        if rebuilt_path is None:
            print(f'{name}: no picture of the rebuild; not measured')
            continue
        sheet = sheets / f'{number:02d}-{name}.png'
        scores = compare_pair(original_path, rebuilt_path, sheet, name)
        pairs.append({'name': name, **scores, 'sheet': str(sheet.relative_to(output))})
    summary = {'pairs': len(pairs)}
    for key in ('edge_agreement', 'edges_original_found', 'edges_rebuilt_found', 'blurred_difference'):
        summary['mean_' + key] = round(sum(pair[key] for pair in pairs) / len(pairs), 4) if pairs else None
    summary['least_alike_first'] = [pair['name'] for pair in sorted(pairs, key=lambda pair: pair['edge_agreement'])]
    summary['shots'] = pairs
    (output / 'pixels.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(f'{len(pairs)} pairs measured: edge agreement {summary["mean_edge_agreement"]}, blurred difference '
          f'{summary["mean_blurred_difference"]}; sheets in {sheets}')


def take_option(arguments, name, default=None):
    if name in arguments:
        at = arguments.index(name)
        value = arguments[at + 1]
        del arguments[at:at + 2]
        return value
    return default


def main():
    global oymap
    arguments = sys.argv[1:]
    root = Path(take_option(arguments, '--root', str(repo / 'output/studio_slice_root'))).resolve()
    oymap = take_option(arguments, '--oymap', oymap)
    no_game = '--no-game' in arguments
    if no_game:
        arguments.remove('--no-game')
    if len(arguments) != 5:
        sys.exit(__doc__)
    source, world, original, shots_file, output = arguments
    output = Path(output).resolve()
    if no_game:
        measure(output)
        return
    shots = yaml.safe_load(Path(shots_file).read_text())['shots']
    # A private copy of the project's own files: the build writes ids.lock.yml and build/ beside them.
    project = output / 'project'
    shutil.rmtree(project, ignore_errors=True)
    project.mkdir(parents=True)
    for entry in sorted(Path(source).iterdir()):
        if entry.is_file():
            shutil.copy2(entry, project / entry.name)
    project = str(project)
    card = yaml.safe_load((Path(project) / 'project.yml').read_text())
    rebuilt = card['id'] + '.blv'
    if not root.exists():
        subprocess.run(['cp', '-al', str(assets), str(root)], check=True)
    subprocess.run([oymap, 'build', project, '--assets', str(assets)], check=True, capture_output=True)
    subprocess.run([oymap, 'install', project, '--root', str(root)], check=True, capture_output=True)
    # The original's floors first: the rebuild's floor is then looked for from just above the same height, so a
    # beam or a ledge higher up in the rebuild is not taken for the floor.
    heights = {}
    for side, map_file, target, target_world in (('original', original, original, world),
                                                 ('rebuilt', rebuilt, project, None)):
        folder = output / side
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
        lines = [f'output_dir: "{folder}"', 'exit: true', 'settle_seconds: 2.0', 'shots:']
        for shot in shots:
            x, y = shot['at'][:2]
            below = shot['at'][2] + 20 if len(shot['at']) > 2 else 4000
            if side == 'rebuilt' and 'rebuilt_z' in shot:
                below = shot['rebuilt_z'] + 20
            elif side == 'rebuilt' and shot['name'] in heights:
                below = heights[shot['name']] + 250
            z = floor_under(target, target_world, assets, x, y, below)
            if shot.get('exact') and len(shot['at']) > 2:
                z = shot['at'][2]
            if side == 'original' and z is not None:
                heights[shot['name']] = z
            if z is None:
                print(f'{side}: no floor under {shot["name"]} at {x}, {y}; skipped')
                continue
            commands = ', '.join(f'"{command}"' for command in SHOT_COMMANDS)
            lines.append(f'  - {{name: {shot["name"]}, position: [{x}, {y}, {z}], yaw: {shot["yaw"]}, pitch: {float(shot.get("pitch", 0.0))}, '
                         f'commands: [{commands}]}}')
        tour = output / f'{side}.tour.yml'
        tour.write_text('\n'.join(lines) + '\n')
        command = [str(repo / 'tools/run_game.sh'), '--isolated', f'studiocompare{side}{os.getpid()}', '--world', world,
                   '--map', map_file, '--assets', str(root), '--warmup', '5',
                   '--seconds', str(20 + 3 * len(shots)), '--set', f'debug.screenshot_tour_path={tour}']
        # A run that yields no pictures (the game binary being rebuilt at that moment, a map that does not load) is
        # shown with what the launcher said, and tried once more after a minute.
        for attempt in (1, 2):
            run = subprocess.run(command, capture_output=True, text=True)
            pictures = len(list(folder.glob('*.png')))
            if pictures > 0 or len(lines) <= 4:
                break
            print(f'{side}: no pictures from attempt {attempt} (exit status {run.returncode}). The launcher said:')
            print('\n'.join(('    ' + line) for line in (run.stdout + run.stderr).strip().splitlines()[-30:]))
            if attempt == 1:
                print(f'{side}: trying once more in 60 seconds')
                time.sleep(60)
        print(side, len(list(folder.glob('*.png'))), 'pictures')
    measure(output)


main()
