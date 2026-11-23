#!/usr/bin/env python3
"""Capture, sheet and compare the outdoor sky review matrix.

  sky_review.py capture <label> [--targets mm6,mm7,mm8,specials,maps] [--style classic|enhanced] [--set S.K=V ...]
  sky_review.py sheet <directory>
  sky_review.py compare <baseline-dir> <candidate-dir> <output-dir>

Captures go to output/sky_review/<label>/<target>/ through the engine-native screenshot tour, using the
`time` tour field and `sky ...` console overrides, so every run sees the same clock and weather.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageStat

ROOT = Path(__file__).resolve().parents[2]
REVIEW_ROOT = ROOT / 'output' / 'sky_review'

WEATHER_COMMANDS = {
    'clear': ['sky clear', 'sky weather 0', 'sky rain off'],
    'overcast': ['sky clear', 'sky weather 3', 'sky rain off'],
    'storm': ['sky clear', 'sky weather 6', 'sky rain heavy'],
    'fog': ['sky clear', 'sky weather 0', 'sky rain off', 'sky fog 0 4096'],
    'auto': ['sky clear'],
}

CLEAR_TIMES = ['05:30', '09:00', '13:00', '20:00', '20:45', '23:30']
WEATHER_TIMES = ['09:00', '20:45']

# Poses reuse the checked-in water review viewpoints; the high view looks across the map edge.
WORLD_TARGETS = {
    'mm6': {'world': 'mm6', 'map': 'oute3.odm', 'pos': [1370.718, -8612.107, 974.502], 'yaw': 0.7,
            'high': [1370.718, -8612.107, 3500.0], 'high_yaw': 2.0},
    'mm7': {'world': 'mm7', 'map': '7out01.odm', 'pos': [13670.097, 1821.473, 2295.133], 'yaw': 4.273,
            'high': [13670.097, 1821.473, 4500.0], 'high_yaw': 4.273},
    'mm8': {'world': 'mm8', 'map': 'out02.odm', 'pos': [10256.120, -16018.912, 2461.032], 'yaw': 4.540,
            'high': [10256.120, -16018.912, 4500.0], 'high_yaw': 3.4},
}

SPECIAL_TARGETS = {
    'mm8-elemf': {'world': 'mm8', 'map': 'elemf.odm', 'pos': [99.0, -22056.0, 3600.0], 'yaw': 1.5708},
    'mm8-elema': {'world': 'mm8', 'map': 'elema.odm', 'pos': [0.0, 0.0, 3000.0], 'yaw': 0.0},
    'mm8-out15': {'world': 'mm8', 'map': 'out15.odm', 'pos': [0.0, 0.0, 3000.0], 'yaw': 0.0},
    'mm8-out01': {'world': 'mm8', 'map': 'out01.odm', 'pos': [3560.0, 7696.0, 1800.0], 'yaw': 1.0},
    'mm7-7out15': {'world': 'mm7', 'map': '7out15.odm', 'pos': [0.0, 0.0, 3000.0], 'yaw': 0.0},
    # MM9's regions are BLV maps with terrain and the outdoor sky (the MM9 rework); over Thjorgard's start point.
    'mm9-thjorgard': {'world': 'mm9', 'map': 'thjorgard.blv', 'pos': [-12830.0, -19987.0, 3600.0], 'yaw': 3.1416},
}

# Themed maps (sky.yml `maps`): one boot each, comparing Classic, Enhanced without a theme and themed at four times.
THEMED_MAPS = {
    'mm8': ['out01', 'out04', 'out06', 'out07', 'out08', 'out13', 'pbp'],
    'mm7': ['7out01', '7out04', '7out05', '7out06', 'out09', 'out10', 'out11', 'out12', '7out13', 'out14'],
    'mm6': ['outa1', 'outa3', 'outb1', 'outb2', 'outb3', 'outc1', 'outc3', 'oute2'],
}
MAP_TARGETS = {f'map-{world}-{name}': {'world': world, 'map': f'{name}.odm', 'pos': [0.0, 0.0, 4200.0], 'yaw': 0.8}
               for world, names in THEMED_MAPS.items() for name in names}
MAP_VARIANTS = [('classic', ['sky style classic']), ('plain', ['sky style enhanced', 'sky theme none']),
                ('themed', ['sky style enhanced'])]
MAP_TIMES = [('09:00', 0.8, 0.02), ('13:00', 0.8, 0.45), ('19:40', 2.9, 0.02), ('23:30', 0.8, 0.02)]


def map_shots(target):
    shots = []
    for time, yaw, pitch in MAP_TIMES:
        for variant, commands in MAP_VARIANTS:
            entry = shot(f"{time.replace(':', '')}-{variant}", target['pos'], yaw, pitch, time, 'auto')
            entry['commands'] = entry['commands'] + commands
            shots.append(entry)
    return shots


def shot(name, pos, yaw, pitch, time, weather):
    return {'name': name, 'position': pos, 'yaw': yaw, 'pitch': pitch, 'time': time,
            'commands': WEATHER_COMMANDS[weather]}


def world_shots(target):
    shots = []
    for time in CLEAR_TIMES:
        stamp = time.replace(':', '')
        shots.append(shot(f'{stamp}-clear-horizon', target['pos'], target['yaw'], 0.05, time, 'clear'))
        shots.append(shot(f'{stamp}-clear-up', target['pos'], target['yaw'], 0.6, time, 'clear'))
        shots.append(shot(f'{stamp}-clear-high', target['high'], target['high_yaw'], -0.08, time, 'clear'))
    # Aim at the setting sun and at the late-evening moon (directions from game/render/SkyState.cpp).
    shots.append(shot('2035-clear-sun', target['pos'], 3.1416, 0.06, '20:35', 'clear'))
    shots.append(shot('2330-clear-moon', target['pos'], -0.31, 0.42, '23:30', 'clear'))
    for weather in ('overcast', 'storm', 'fog'):
        for time in WEATHER_TIMES:
            stamp = time.replace(':', '')
            shots.append(shot(f'{stamp}-{weather}-horizon', target['pos'], target['yaw'], 0.05, time, weather))
            shots.append(shot(f'{stamp}-{weather}-up', target['pos'], target['yaw'], 0.6, time, weather))
    return shots


def special_shots(target):
    return [
        shot('0900-auto-horizon', target['pos'], target['yaw'], 0.05, '09:00', 'auto'),
        shot('1300-auto-up', target['pos'], target['yaw'], 0.6, '13:00', 'auto'),
        shot('2045-auto-horizon', target['pos'], target['yaw'], 0.05, '20:45', 'auto'),
        shot('2330-auto-horizon', target['pos'], target['yaw'], 0.05, '23:30', 'auto'),
    ]


def yaml_text(output_dir, shots):
    lines = [f'output_dir: {output_dir}', 'settle_seconds: 1.5', 'exit: true', 'shots:']
    for entry in shots:
        x, y, z = entry['position']
        commands = ', '.join(f'"{command}"' for command in entry['commands'])
        lines += [
            f"  - name: {entry['name']}",
            f'    position: [{x}, {y}, {z}]',
            f"    yaw: {entry['yaw']}",
            f"    pitch: {entry['pitch']}",
            f"    time: \"{entry['time']}\"",
            f'    commands: [{commands}]',
        ]
    return '\n'.join(lines) + '\n'


def capture(args):
    label_dir = REVIEW_ROOT / args.label
    names = [name.strip() for name in args.targets.split(',') if name.strip()]
    jobs = []
    for name in names:
        if name in WORLD_TARGETS:
            jobs.append((name, WORLD_TARGETS[name], world_shots(WORLD_TARGETS[name])))
        elif name == 'maps':
            jobs += [(key, value, map_shots(value)) for key, value in MAP_TARGETS.items()]
        elif name in MAP_TARGETS:
            jobs.append((name, MAP_TARGETS[name], map_shots(MAP_TARGETS[name])))
        elif name == 'specials':
            jobs += [(key, value, special_shots(value)) for key, value in SPECIAL_TARGETS.items()]
        elif name in SPECIAL_TARGETS:
            jobs.append((name, SPECIAL_TARGETS[name], special_shots(SPECIAL_TARGETS[name])))
        else:
            sys.exit(f'unknown target {name}')

    overrides = list(args.set)
    if args.style:
        overrides.append(f'video.sky_style={args.style}')

    failures = []
    for name, target, shots in jobs:
        output_dir = label_dir / name
        output_dir.mkdir(parents=True, exist_ok=True)
        for old in output_dir.glob('*.png'):
            old.unlink()
        tour_path = label_dir / 'tours' / f'{name}.yml'
        tour_path.parent.mkdir(parents=True, exist_ok=True)
        tour_path.write_text(yaml_text(output_dir, shots))
        command = [str(ROOT / 'tools' / 'run_game.sh'), '--isolated', f'sky-{args.label}-{name}',
                   '--world', target['world'], '--map', target['map'], '--warmup', '0', '--seconds', '600',
                   '--set', f'debug.screenshot_tour_path={tour_path}']
        for override in overrides:
            command += ['--set', override]
        log_path = label_dir / 'tours' / f'{name}.log'
        print(f'capture {name}: {len(shots)} shots -> {output_dir}', flush=True)
        with log_path.open('w') as log:
            result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        captured = len(list(output_dir.glob('*.png')))
        if result.returncode != 0 or captured != len(shots):
            failures.append(f'{name}: exit={result.returncode} captured={captured}/{len(shots)} log={log_path}')
        write_sheet(output_dir)
    for failure in failures:
        print('FAILED', failure)
    return 1 if failures else 0


def labelled_thumb(path, width):
    image = Image.open(path).convert('RGB')
    image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, width, 14], fill=(0, 0, 0))
    draw.text((4, 1), path.stem, fill=(255, 255, 255))
    return image


def grid(images, columns):
    width, height = images[0].size
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new('RGB', (width * columns, height * rows), (24, 24, 24))
    for index, image in enumerate(images):
        sheet.paste(image, ((index % columns) * width, (index // columns) * height))
    return sheet


def write_sheet(directory, columns=3, width=480):
    paths = sorted(Path(directory).glob('[0-9][0-9]-*.png'))
    if not paths:
        return None
    sheet_path = Path(directory) / 'contact_sheet.jpg'
    grid([labelled_thumb(path, width) for path in paths], columns).save(sheet_path, quality=88)
    return sheet_path


def compare(args):
    baseline = Path(args.baseline)
    candidate = Path(args.candidate)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    pairs = []
    report = []
    for base_path in sorted(baseline.rglob('[0-9][0-9]-*.png')):
        relative = base_path.relative_to(baseline)
        candidate_path = candidate / relative
        if not candidate_path.exists():
            report.append(f'{relative}: missing in candidate')
            continue
        base_image = Image.open(base_path).convert('RGB')
        candidate_image = Image.open(candidate_path).convert('RGB')
        if base_image.size != candidate_image.size:
            report.append(f'{relative}: size {base_image.size} vs {candidate_image.size}')
            continue
        difference = ImageChops.difference(base_image, candidate_image)
        mean = sum(ImageStat.Stat(difference).mean) / 3.0
        report.append(f'{relative}: mean_abs_diff={mean:.3f}')
        left = labelled_thumb(base_path, 480)
        right = labelled_thumb(candidate_path, 480)
        pair = Image.new('RGB', (960, left.height))
        pair.paste(left, (0, 0))
        pair.paste(right, (480, 0))
        pairs.append((relative, pair))
    by_folder = {}
    for relative, pair in pairs:
        by_folder.setdefault(relative.parent, []).append(pair)
    for folder, images in by_folder.items():
        name = '_'.join(folder.parts) or 'root'
        for start in range(0, len(images), 8):
            grid(images[start:start + 8], 1).save(output / f'{name}_{start // 8:02d}.jpg', quality=85)
    (output / 'report.txt').write_text('\n'.join(report) + '\n')
    print('\n'.join(report))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    capture_parser = commands.add_parser('capture')
    capture_parser.add_argument('label')
    capture_parser.add_argument('--targets', default='mm6,mm7,mm8')
    capture_parser.add_argument('--style', choices=['classic', 'enhanced'])
    capture_parser.add_argument('--set', action='append', default=[])
    sheet_parser = commands.add_parser('sheet')
    sheet_parser.add_argument('directory')
    compare_parser = commands.add_parser('compare')
    compare_parser.add_argument('baseline')
    compare_parser.add_argument('candidate')
    compare_parser.add_argument('output')
    args = parser.parse_args()
    if args.command == 'capture':
        return capture(args)
    if args.command == 'sheet':
        print(write_sheet(args.directory))
        return 0
    return compare(args)


if __name__ == '__main__':
    sys.exit(main())
