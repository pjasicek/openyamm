#!/usr/bin/env python3
"""XD-18's test rows in the scratch root's copied tables only (never assets_dev): A4's house 4852, the Dragon Tax
Office (source/towns/xd18.yml, `planned: true`, so build_world.py has not written it yet), with Scaldrith (5702) as its
one resident. Idempotent; run after copy_tables.py / resync_root.py. Each row is listed under NOTES "Test rows".
Usage: test_rows.py [--check]  (--check: say whether A4's real rows have landed in assets_dev)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

R = Path(_REPO_ROOT)
ROOT = R / 'output/studio_cal/xd18/root/worlds/xeen/data_tables'
DEV = R / 'assets_dev/worlds/xeen/data_tables'
ROWS = {
    'house_data.txt': '4852\t0\tHouse\t9130\thuman poor house 1\tThe Dragon Tax Office\t\t\t0\t0\t0\t0\t1.5\t\t\t\t\t\t0\t0\t0\t0\t0\t0',
    'house_animations.txt': '4852\t0\tThe Dragon Tax Office\t5702\thuman poor house 1\t\t\t\t0\tHouse',
}


def landed(name):
    return any(line.startswith('4852\t') for line in (DEV / name).read_text().splitlines())


if '--check' in sys.argv:
    for name in ROWS:
        print(name, 'A4 row landed' if landed(name) else 'not landed')
    npc = [l for l in (DEV / 'npc.txt').read_text().splitlines() if l.startswith('5702\t')]
    print('npc.txt 5702 2D location:', npc[0].split('\t')[6] if npc else 'no row')
    sys.exit(0)

for name, row in ROWS.items():
    p = ROOT / name
    if p.stat().st_nlink != 1:
        sys.exit(f'{p} is a hard link: copy the tables first')
    lines = p.read_text().split('\n')
    if any(l.startswith('4852\t') for l in lines):
        print(name, 'has 4852')
        continue
    at = max(i for i, l in enumerate(lines) if l.split('\t')[0].isdigit() and int(l.split('\t')[0]) < 4852) + 1
    lines.insert(at, row)
    p.write_text('\n'.join(lines))
    print(name, 'test row 4852 added')
p = ROOT / 'npc.txt'
lines = p.read_text().split('\n')
for i, l in enumerate(lines):
    if l.startswith('5702\t'):
        f = l.split('\t')
        if f[6] != '4852':
            f[6] = '4852'
            lines[i] = '\t'.join(f)
            p.write_text('\n'.join(lines))
            print('npc.txt 5702 put in house 4852')
        else:
            print('npc.txt 5702 already in 4852')
