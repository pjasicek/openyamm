#!/usr/bin/env python3
"""F41 check (2026-11-24): hostile monsters that cannot come to the party and cannot reach it either.

A player found two Orc Guards at XD-05's back gate, a Goblin Warden at his table in XD-04 and two Mad Dwarves at
XD-03's gate standing still until the party walked up to them: their maps place them `immobile: true`, and the rows
have no missile and no spell, so they fight only what touches them and can be shot from anywhere. An immobile monster
must shoot or cast (a turret, an archer on a wall), be peaceful (a prisoner, a child in a cage), or be held another
way: `leash: <radius>` keeps a guard at its post and lets it fight within the circle (Map Studio objects.yml).

Reads every Xeen map project's objects.yml (devdocs/xeen/briefs/<map>/L4/objects.yml) and the monster rows (Xeen's
monster_data.txt, then the engine's). Rows whose Move column is `stand` are checked the same way wherever they are
placed. Prints one line per finding; exit 1 when there is one.

Placements held on purpose are listed, with the reason, in tools/xeen/check_immobile.yml.

  python3 tools/xeen/check_immobile.py [--json]
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BRIEFS = ROOT / 'devdocs' / 'xeen' / 'briefs'
TABLES = [ROOT / 'assets_dev' / 'worlds' / 'xeen' / 'data_tables' / 'monster_data.txt',
          ROOT / 'assets_dev' / 'engine' / 'data_tables' / 'monster_data.txt']


def monster_rows():
    rows = {}
    for path in TABLES:
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            cells = line.split('\t')
            if not cells or not cells[0].strip().isdigit():
                continue
            rows.setdefault(int(cells[0]), cells)
    return rows


def cell(cells, index):
    return cells[index].strip().strip('"') if index < len(cells) else ''


def reaches_from_afar(cells):
    """A missile on attack 1, a used attack 2 with a missile, or a spell in use."""
    def used(value):
        return value not in ('', '0')

    def percent(value):
        try:
            return float(value) > 0
        except ValueError:
            return False

    return (used(cell(cells, 19))
            or (percent(cell(cells, 20)) and used(cell(cells, 23)))
            or (percent(cell(cells, 24)) and used(cell(cells, 25)))
            or (percent(cell(cells, 26)) and used(cell(cells, 27))))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    rows = monster_rows()
    held = (yaml.safe_load((Path(__file__).with_suffix('.yml')).read_text(encoding='utf-8')) or {}).get('held') or {}
    findings = []
    placed = 0
    for objects in sorted(BRIEFS.glob('*/L4/objects.yml')):
        stem = objects.parts[-3]
        data = yaml.safe_load(objects.read_text(encoding='utf-8')) or {}
        for monster in data.get('monsters') or []:
            row_id = monster.get('monster')
            cells = rows.get(row_id) if isinstance(row_id, int) else None
            stands = cells is not None and cell(cells, 10).lower() == 'stand'
            if not (monster.get('immobile') or stands) or monster.get('leash'):
                continue
            placed += 1
            if monster.get('hostile') is not True or cells is None or reaches_from_afar(cells):
                continue
            if stem in held and held[stem]['pattern'] in str(monster.get('id')):
                continue
            findings.append({
                'map': stem, 'id': monster.get('id'), 'row': row_id, 'name': cell(cells, 1),
                'at': monster.get('at'), 'why': 'immobile' if monster.get('immobile') else 'row moves: stand'})
    if args.json:
        print(json.dumps(findings, indent=1))
    else:
        for finding in findings:
            print(f"{finding['map']}: {finding['id']} ({finding['row']} {finding['name']}) at {finding['at']}: "
                  f"{finding['why']}, hostile, no missile or spell: it fights only what walks up to it")
        print(f'{placed} immobile or standing placements, {len(findings)} hostile melee-only', file=sys.stderr)
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
