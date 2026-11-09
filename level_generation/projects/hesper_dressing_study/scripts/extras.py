#!/usr/bin/env python3
"""Extra census figures for README.md: decoration roles, texture-built furniture, geometry chests. Prints only."""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DATA = Path(__file__).resolve().parents[1] / 'data'
LIGHT = re.compile(r'torch|brazier|lantern|chandelier|candle|flambeau|sconce|fire|lamp|campfire|burning', re.I)
FURN = {
    'cabinet/shelf/books': re.compile(r'cab|book|shelf|bookcas|rack|wine'),
    'bed/table/desk': re.compile(r'bed|tabl|desk|chair|bench'),
    'crate/barrel/sack': re.compile(r'crat|cr_w|barl|barrel|cb\d'),
    'chest': re.compile(r'^ch\d|chest'),
    'machine/pipe/console': re.compile(r'pipe|girder|pnl|panel|scrn|scon|console|gear|mach|tank|^sw(trpnl|pipes)'),
}


def main():
    table = ROOT / 'assets_dev/engine/data_tables/decoration_data.txt'
    hints = {r[1].lower(): (r[2], int(r[6])) for r in csv.reader(table.open(), delimiter='\t') if r and r[0].isdigit()}
    rows = json.loads((DATA / 'sectors.json').read_text())
    for world in ('mm6', 'mm7', 'mm8'):
        rs = [r for r in rows if r['world'] == world and r['floor_area'] > 20000]
        roles = Counter()
        for r in rs:
            for name, c in r['decorations']:
                hint, light = hints.get(name, ('', 0))
                roles['light' if light or LIGHT.search(hint + ' ' + name) else 'prop'] += c
        furn = Counter()
        for r in rs:
            texs = {t for t, _ in r['detail_textures']} | set(r['top_textures'])
            for k, rx in FURN.items():
                if any(rx.search(t) for t in texs):
                    furn[k] += 1
        offtex = sum(r['detail_offtex'] for r in rs) / sum(r['faces'] for r in rs)
        props_sectors = sum(any(not (hints.get(n, ('', 0))[1] or LIGHT.search(hints.get(n, ('', 0))[0] + n))
                                for n, _ in r['decorations']) for r in rs)
        print(f'== {world}: decorations by role {dict(roles)}; sectors with any non-light prop decoration '
              f'{props_sectors}/{len(rs)} ({props_sectors / len(rs):.0%}); off-top-3-texture face share {offtex:.0%}')
        print('   sectors using furniture/machine textures:',
              {k: f'{v} ({v / len(rs):.0%})' for k, v in furn.items()})
        clicks = [c for r in rs for c in r['clickable']]
        print('   clickable faces', len(clicks), 'top textures', Counter(c['texture'] for c in clicks).most_common(12))


if __name__ == '__main__':
    main()
