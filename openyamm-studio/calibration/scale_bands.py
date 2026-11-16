#!/usr/bin/env python3
"""How a built map's rooms compare in size with the shipped MM6-8 dungeons.

The user found XD-01 cramped (2026-11-13): its bigger rooms were less than half the size of a typical shipped
dungeon's, while the map's total floor area was inside the bands. This compares room sizes, not totals:

    scale_bands.py <map.blv> --world <world> [--assets <root>]   (the map as installed in that root)
    scale_bands.py <project folder> [--assets <root>]           (the project, built privately by oymap)
    scale_bands.py ... --json             the figures as JSON (the studio host's job: schema/rpc/jobs.rpc.json)
    scale_bands.py --rebuild-index        measure every shipped MM6-8 BLV again (oymap metrics)

The oymap binary is $OYMAP when set (the studio host passes its own), else openyamm-studio/build/oymap.

For each figure it prints where the map stands among the 161 shipped dungeons with ten rooms or more (percentile),
and flags a figure below the shipped 25th percentile. A new dungeon's main rooms should sit at least at the shipped
median unless its brief says it is small or cramped on purpose (pens, cells, crawlways stay small; they are not
what the upper quarter of rooms measures). The index lives in output/studio_lead/scale/shipped.json.
"""
import glob
import json
import os
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OYMAP = os.environ.get('OYMAP') or os.path.join(REPO, 'openyamm-studio', 'build', 'oymap')
INDEX = os.path.join(REPO, 'output', 'studio_lead', 'scale', 'shipped.json')
FIGURES = [
    (4, 'bigger rooms: upper-quarter room floor area', lambda d: d['sector_floor_area']['q3']),
    (5, 'largest room floor area', lambda d: d['sector_floor_area']['max']),
    (6, 'typical ceiling height', lambda d: d['sector_height']['median']),
    (7, 'taller rooms: upper-quarter height', lambda d: d['sector_height']['q3']),
    (8, 'typical doorway width', lambda d: d['doorway_width']['median']),
]


def metrics(path, world, assets):
    # A project is built privately by oymap and measured as built: no installed copy to check against.
    if os.path.isfile(os.path.join(path, 'project.yml')):
        done = subprocess.run([OYMAP, 'metrics', path, '--assets', assets], capture_output=True, text=True)
        if done.returncode != 0:
            sys.exit(f'oymap metrics {path}: {done.stderr.strip()}')
        return json.loads(done.stdout)['scale']
    # `oymap metrics` measures the map of that name in the asset root, not the file given (found by XD-03's second
    # pass): refuse a file that differs from the root's map of its name, so a figure is never the wrong map's.
    import filecmp
    installed = os.path.join(assets, 'worlds', world, 'maps', os.path.basename(path))
    if not os.path.exists(installed):
        sys.exit(f'{path}: the root {assets} has no map {os.path.basename(path)} for {world}; install the build there '
                 '(oymap install <project> --build <build> --root <root>) and measure that')
    if not filecmp.cmp(path, installed, shallow=False):
        sys.exit(f'{path} differs from {installed}: oymap metrics would measure the installed one; install this build '
                 'into the root first, or pass the installed file')
    out = subprocess.run([OYMAP, 'metrics', path, '--world', world, '--assets', assets],
                         capture_output=True, text=True).stdout
    return json.loads(out)['scale']


def rebuild():
    with open(os.path.join(REPO, 'output', 'studio_lead', 'blv_names.json')) as names_file:
        names = json.load(names_file)
    rows = []
    for world in ('mm6', 'mm7', 'mm8'):
        for path in sorted(glob.glob(os.path.join(REPO, 'assets_dev', 'worlds', world, 'maps', '*.blv'))):
            try:
                d = metrics(path, world, os.path.join(REPO, 'assets_dev'))
            except (ValueError, KeyError):
                continue
            a = d['sector_floor_area']
            h = d['sector_height']
            rows.append((f'{world}/{os.path.basename(path)}', names.get(os.path.basename(path).lower(), '?'),
                         a['count'], a['median'], a['q3'], a['max'], h['median'], h['q3'],
                         d['doorway_width']['median'], d['floor_area_millions']))
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    with open(INDEX, 'w') as out_file:
        json.dump(rows, out_file)
    print(f'{len(rows)} shipped maps measured')


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    if argv[0] == '--rebuild-index':
        rebuild()
        return 0
    path = argv[0]
    world = argv[argv.index('--world') + 1] if '--world' in argv else 'mm7'
    assets = argv[argv.index('--assets') + 1] if '--assets' in argv else os.path.join(REPO, 'assets_dev')
    with open(INDEX) as index_file:
        shipped = [row for row in json.load(index_file) if row[2] >= 10]
    d = metrics(path, world, assets)
    low = 0
    figures = []
    for column, label, read in FIGURES:
        value = read(d)
        values = sorted(row[column] for row in shipped)
        below = sum(1 for v in values if v < value)
        percentile = round(100 * below / len(values))
        p25, p50 = values[len(values) // 4], values[len(values) // 2]
        flag = '  BELOW THE SHIPPED 25TH PERCENTILE' if value < p25 else ''
        low += 1 if flag else 0
        figures.append({'label': label, 'value': round(value), 'p25': round(p25), 'median': round(p50),
                        'percentile': percentile, 'below_p25': value < p25})
        if '--json' not in argv:
            print(f'{label:45s} {value:>10.0f}   shipped p25 {p25:>9.0f}, median {p50:>9.0f}; percentile '
                  f'{percentile:3d}{flag}')
    if '--json' in argv:
        print(json.dumps({'map': os.path.basename(os.path.normpath(path)), 'shipped_maps': len(shipped),
                          'figures': figures, 'below_p25': low}, indent=1))
    return 1 if low else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
