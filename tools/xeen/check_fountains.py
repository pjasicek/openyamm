#!/usr/bin/env python3
"""D-181 (the player's pin XD-06 p1, 2026-11-26, "maybe put a comple fountain there"): a fountain without a basin
stands only in water.

`sta1a` (decoration row 153, hint "Statue") is MM6's New Sorpigal fountain, whose model (`mm6_deco_fountain.glb`,
revision 3) has no basin: it stands in a pool and its streams end just under its base. Picked by its hint as a
"statue", it stood on XD-06's chapel altars and as X8's and X9's offering statues, pouring onto stone. The rule: a
basin-less fountain (BASINLESS) stands in water, its base within NEAR of a water or liquid face (FaceAttribute fluid,
0x10) under or over its foot; a statue is `7dec54`/`7dec55` or another statue.

Every Xeen BLV is read with `oymap export` (decorations: `entities`, `decoration_list_id` = row - 1). The outdoor maps'
projects are searched for the names (no ODM places one today; a new one is an error to look at by hand).

Usage: tools/xeen/check_fountains.py [<map.blv> ...] [--assets ROOT]   (default every xeen_*.blv)
Exit 1 on a finding."""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OY = f'{R}/openyamm-studio/build-xeen/oymap'
BASINLESS = {'sta1a'}
NEAR = 32.0
FLUID = 0x10


def rows(assets):
    out = {}
    with open(f'{assets}/engine/data_tables/decoration_data.txt', encoding='utf-8', errors='replace') as f:
        for line in f:
            c = line.rstrip('\n').split('\t')
            if len(c) > 1 and c[0].isdigit() and c[1].lower() in BASINLESS:
                out[int(c[0]) - 1] = c[1]
    return out


def pip(poly, x, y):
    c = False
    for i in range(len(poly)):
        ax, ay = poly[i][0], poly[i][1]
        bx, by = poly[i - 1][0], poly[i - 1][1]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            c = not c
    return c


def check(path, assets, ids):
    with tempfile.NamedTemporaryFile(suffix='.json') as t:
        subprocess.run([OY, 'export', path, '--world', 'xeen', '--assets', assets, '--out', t.name], check=True,
                       capture_output=True)
        m = json.load(open(t.name))['map']
    V = m['vertices']
    water = []
    for f in m['faces']:
        if f['attributes'] & FLUID and f['plane_normal'][2] > 0.9 * 65536:
            water.append([V[v] for v in f['vertices']])
    out = []
    for e in m.get('entities') or []:
        if e['decoration_list_id'] not in ids:
            continue
        x, y, z = e['position']
        wet = any(pip(w, x, y) and abs(sum(p[2] for p in w) / len(w) - z) <= NEAR for w in water)
        if not wet:
            out.append(f'{os.path.basename(path)}: fountain.dry {e["name"]} ({ids[e["decoration_list_id"]]}, a '
                       f'fountain with no basin) at ({x}, {y}, {z}) stands in no water (none within {NEAR:.0f} of '
                       f'its foot): give it a basin of water or use a statue (7dec54, 7dec55)')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('maps', nargs='*')
    ap.add_argument('--assets', default=f'{R}/assets_dev')
    a = ap.parse_args()
    maps = a.maps or sorted(glob.glob(f'{a.assets}/worlds/xeen/maps/xeen_*.blv'))
    ids = rows(a.assets)
    found = []
    for path in maps:
        found += check(path, a.assets, ids)
    if not a.maps:
        for f in sorted(glob.glob(f'{R}/devdocs/xeen/briefs/*/L4/*.yml')):
            if os.path.exists(os.path.join(os.path.dirname(f), 'rooms.yml')):
                continue                                   # a dungeon: read from its BLV above
            text = open(f, encoding='utf-8').read()
            for name in BASINLESS:
                if f'decoration: {name}' in text or f"decoration: '{name}'" in text:
                    found.append(f'{os.path.relpath(f, R)}: fountain.outdoors {name} placed on an outdoor map: '
                                 f'check by hand that it stands in water')
    for line in found:
        print(line)
    print(f'basin-less fountains out of water: {len(found)}')
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main())
