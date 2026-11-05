#!/usr/bin/env python3
"""Perception difficulty (map_stats.txt "Per" column) for a world's dungeons from their monster strength, fitted on
MM7/MM8, whose designers set it. A party sees a map's secret faces at Perception >= 2 * difficulty
(GameMechanics::partyDetectsSecretFaces).

    python3 tools/secret_faces/perception_difficulty.py            # print the fit and the MM6 values
    python3 tools/secret_faces/perception_difficulty.py --check    # compare with map_stats.txt
    python3 tools/secret_faces/perception_difficulty.py --write    # write them (rows of the world's BLV maps)

Strength of a map: the strongest of its three encounter slots, each the A/B/C levels of its monster (monster_data.txt
by picture name) weighted by the slot's 1-5 difficulty. MM7/MM8 maps with a difficulty and monsters fit
per = a * sqrt(strength) + b (about 3 points of error; linear and log fits are as good), rounded and clamped to 1-20.
Maps without encounter monsters get 1, like MM7's Arena and Strange Temple.
"""

import argparse
import csv
import math
import os
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TABLES = REPO / 'assets_dev' / 'engine' / 'data_tables'
MAP_STATS = TABLES / 'map_stats.txt'
PER_COLUMN = 5                  # MapStats.cpp PerceptionDifficultyColumn
SLOTS = ((16, 18), (20, 22), (24, 26))   # (monster picture, 1-5 difficulty) columns
TIER_MIX = {1: (1, 0, 0), 2: (.6, .4, 0), 3: (.3, .5, .2), 4: (.1, .5, .4), 5: (0, .4, .6)}


def monster_levels():
    levels = {}
    with open(TABLES / 'monster_data.txt', errors='replace') as file:
        for row in csv.reader(file, delimiter='\t'):
            if len(row) > 4 and row[0].strip().isdigit():
                try:
                    levels[row[2].strip().lower()] = int(row[3])
                except ValueError:
                    pass
    return levels


def world_of(file_name):
    return next((w for w in ('mm6', 'mm7', 'mm8') if (REPO / 'assets_dev' / 'worlds' / w / 'maps' / file_name).exists()),
                None)


def maps():
    levels = monster_levels()
    result = []
    with open(MAP_STATS, errors='replace') as file:
        for row in csv.reader(file, delimiter='\t'):
            if len(row) < 28 or not row[0].strip().isdigit():
                continue
            file_name = row[2].strip().lower()
            if not file_name.endswith('.blv'):
                continue
            strength = 0.0
            for picture_column, difficulty_column in SLOTS:
                picture = row[picture_column].strip().lower()
                tiers = [levels.get(f'{picture} {tier}') for tier in 'abc']
                if not picture or picture == '0' or None in tiers:
                    continue
                try:
                    weights = TIER_MIX.get(int(row[difficulty_column]), TIER_MIX[1])
                except ValueError:
                    weights = TIER_MIX[1]
                strength = max(strength, sum(level * weight for level, weight in zip(tiers, weights)))
            result.append(dict(file=file_name, name=row[1], world=world_of(file_name), per=int(row[PER_COLUMN] or 0),
                               strength=strength))
    return result


def fit(rows):
    train = [r for r in rows if r['world'] in ('mm7', 'mm8') and r['strength'] > 0 and r['per'] > 0]
    xs = [math.sqrt(r['strength']) for r in train]
    ys = [r['per'] for r in train]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    b = my - a * mx
    error = statistics.mean([(predict(a, b, x * x) - y) ** 2 for x, y in zip(xs, ys)]) ** 0.5
    return a, b, error, len(train)


def predict(a, b, strength):
    return 1 if strength <= 0 else min(20, max(1, round(a * math.sqrt(strength) + b)))


def write(values):
    data = MAP_STATS.read_bytes().decode('latin-1')
    lines = data.splitlines(keepends=True)
    changed = 0
    for index, line in enumerate(lines):
        body = line.rstrip('\r\n')
        columns = body.split('\t')
        if len(columns) > PER_COLUMN and columns[0].strip().isdigit() and columns[2].strip().lower() in values:
            value = str(values[columns[2].strip().lower()])
            if columns[PER_COLUMN] != value:
                columns[PER_COLUMN] = value
                lines[index] = '\t'.join(columns) + line[len(body):]
                changed += 1
    temporary = MAP_STATS.with_suffix('.txt.tmp')    # temp file + rename: assets_dev files are hard-linked
    temporary.write_bytes(''.join(lines).encode('latin-1'))
    os.chmod(temporary, os.stat(MAP_STATS).st_mode & 0o777)
    os.replace(temporary, MAP_STATS)
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--world', default='mm6')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='exit 1 when map_stats.txt differs')
    mode.add_argument('--write', action='store_true')
    args = parser.parse_args()
    rows = maps()
    a, b, error, count = fit(rows)
    print(f'fit on {count} MM7/MM8 maps: per = {a:.3f} * sqrt(strength) {b:+.3f}, rms error {error:.2f}')
    targets = [r for r in rows if r['world'] == args.world]
    values = {r['file']: predict(a, b, r['strength']) for r in targets}
    for r in sorted(targets, key=lambda r: (values[r['file']], r['file'])):
        mark = '' if r['per'] == values[r['file']] else f'  (table {r["per"]})'
        print(f"  {r['file']:12} {r['name'][:28]:28} strength {r['strength']:5.1f}  per {values[r['file']]:2}{mark}")
    if args.check:
        differ = [r['file'] for r in targets if r['per'] != values[r['file']]]
        print('map_stats.txt matches' if not differ else f'differs: {differ}')
        sys.exit(1 if differ else 0)
    if args.write:
        print('rows changed:', write(values))


if __name__ == '__main__':
    main()
