#!/usr/bin/env python3
"""Compares a rebuilt map's metrics with the original's (devdocs/map_studio/CALIBRATION.md).

  compare.py <rebuilt: project folder or metrics.json> <original metrics.json> [--assets <root>] [--json]

Each number is shown for both with their ratio and a reading against a band. Bands (version 1, deliberately wide,
to be tightened as rebuilds accumulate): counts and sizes are "in" within a quarter of the original, "near" within
a half, otherwise "out". A rebuild is not meant to equal the original, only to be like it. Metrics that depend on
stages a brief level does not reach (density at L3, palette) are listed but do not count toward the summary; say
which groups count with --groups (default: structure,scale,play).
"""
import json
import subprocess
import sys
from pathlib import Path

studio = Path(__file__).resolve().parents[1]


def flatten(value, prefix=''):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from flatten(child, f'{prefix}.{key}' if prefix else key)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield prefix, float(value)


def metrics_of(target, assets):
    path = Path(target)
    if path.is_file():
        return json.loads(path.read_text())
    out = subprocess.run([str(studio / 'build/oymap'), 'metrics', str(path), '--assets', str(assets), '--reach'],
                         capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f'oymap metrics failed for {path}:\n{out.stderr}')
    return json.loads(out.stdout)


def reading(rebuilt, original):
    if original == 0:
        return 'in' if rebuilt == 0 else 'out'
    ratio = rebuilt / original
    if 0.75 <= ratio <= 1.0 / 0.75:
        return 'in'
    if 0.5 <= ratio <= 2.0:
        return 'near'
    return 'out'


def main():
    arguments = [a for a in sys.argv[1:] if not a.startswith('--')]
    option = lambda name, default: sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
    assets = option('--assets', studio.parent / 'assets_dev')
    groups = option('--groups', 'structure,scale,play').split(',')
    rebuilt = dict(flatten(metrics_of(arguments[0], assets)))
    original = dict(flatten(json.loads(Path(arguments[1]).read_text())))
    rows = []
    for name, value in original.items():
        # Floor levels are heights above a datum, not sizes: compare their spread instead of the values.
        if name.startswith('scale.floor_level.') or name not in rebuilt:
            continue
        rows.append((name, rebuilt[name], value, reading(rebuilt[name], value), name.split('.')[0] in groups))
    for name in ('scale.floor_level',):
        if f'{name}.max' in original and f'{name}.max' in rebuilt:
            spread = lambda table: table[f'{name}.max'] - table[f'{name}.min']
            rows.append((f'{name}.spread', spread(rebuilt), spread(original),
                         reading(spread(rebuilt), spread(original)), 'scale' in groups))
    counted = [row for row in rows if row[4]]
    summary = {key: sum(1 for row in counted if row[3] == key) for key in ('in', 'near', 'out')}
    if '--json' in sys.argv:
        print(json.dumps({'summary': summary, 'rows': [
            {'metric': n, 'rebuilt': r, 'original': o, 'reading': s, 'counted': c} for n, r, o, s, c in rows]}, indent=1))
        return
    print(f'{"metric":44} {"rebuilt":>12} {"original":>12} {"ratio":>6}  reading')
    for name, mine, theirs, state, counts in rows:
        ratio = f'{mine / theirs:6.2f}' if theirs else '     -'
        print(f'{name:44} {mine:12.6g} {theirs:12.6g} {ratio}  {state}{"" if counts else " (not counted)"}')
    print(f'\ncounted ({", ".join(groups)}): {summary["in"]} in, {summary["near"]} near, {summary["out"]} out')


main()
