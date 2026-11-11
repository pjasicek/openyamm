#!/usr/bin/env python3
"""Index installed MM9 teacher positions without loading other maps at runtime.
Run after a city/map rebuild; --check detects stale positions. Lessons stay in skill_trainers.txt.
"""
import argparse
import csv
import io
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / 'assets_dev/worlds/mm9'
OUTPUT = WORLD / 'data_tables/trainer_places.txt'


def generate():
    with (WORLD / 'data_tables/skill_trainers.txt').open() as stream:
        ids = {int(row['RudeId']) for row in csv.DictReader(stream, delimiter='\t')}
    racial = yaml.safe_load((WORLD / 'dialogue/racial_trainers.yml').read_text())
    ids.update(row['rude'] for row in racial['trainers'])
    found = set()
    rows = []
    for path in sorted((WORLD / 'maps').glob('*.scene.yml')):
        text = path.read_text()
        if 'mm9_rude_id' not in text:
            continue
        scene = json.loads(text) if text.lstrip().startswith('{') else yaml.safe_load(text)
        for actor in scene.get('initial_state', {}).get('actors', []):
            rude = actor.get('mm9_rude_id')
            if rude not in ids:
                continue
            position = actor['position']
            rows.append([rude, actor['name'], scene['source']['geometry_file'],
                         position['x'], position['y'], position['z']])
            found.add(rude)
    if ids != found:
        raise ValueError(f'Teachers without installed positions: {sorted(ids - found)}')
    assert len({(r[0], r[2]) for r in rows}) == len(rows), 'Duplicate teacher on a map'
    result = io.StringIO()
    writer = csv.writer(result, delimiter='\t', lineterminator='\n')
    writer.writerow(['RudeId', 'Name', 'Map', 'X', 'Y', 'Z'])
    writer.writerows(sorted(rows))
    return result.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = generate()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            raise SystemExit(f'Stale {OUTPUT}; run {Path(__file__).name}')
    else:
        OUTPUT.write_text(text)
    print(f'{len(text.splitlines()) - 1} MM9 teacher locations verified')


if __name__ == '__main__':
    main()
