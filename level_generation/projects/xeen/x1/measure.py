#!/usr/bin/env python3
"""X1 rebase measure (A5, 2026-11-20): the CHANGES_FOR_BUILT_MAPS X1-4..X1-8 figures from a build folder.

Usage: measure.py <build dir> [<project dir>]

Counts, by the scale review's method (output/xeen_review/scale/heatmaps.py: 16 x 16 cells of 4,096, central 12 x 12):
  hostiles at load    spawn markers x the mean of their slot's per_marker (index 4-12: one), plus hostile placed actors
  markers, groups     spawn markers; placed groups
  decorations         entities that are not party starts, sounds or lights
  open meadow cells   central land cells (water < 48 tiles of 64) with fewer than 3 decorations
  quiet land          central land cells with no hostile
  encounter areas     8-connected regions of central cells holding hostiles
  chests              scene chests
  first fight         nearest hostile to each arrival (edges, start, dungeon exits)
"""
import math
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'output/xeen_review/scale'))
sys.path.insert(0, str(ROOT / 'util'))
from heatmaps import terrain_rows, tile_flags  # noqa: E402
from map_export import parse_odm_file  # noqa: E402

N, CELL = 16, 4096
TOWNFOLK = {'371', '368', '354', '350', '404', 'Peasant'}


def cell_of(x, y):
    return min(max(int((32768 - y) // CELL), 0), N - 1), min(max(int((x + 32768) // CELL), 0), N - 1)


def regions(occ):
    seen = np.zeros_like(occ)
    sizes = []
    for r in range(occ.shape[0]):
        for c in range(occ.shape[1]):
            if occ[r, c] and not seen[r, c]:
                stack, n = [(r, c)], 0
                seen[r, c] = True
                while stack:
                    y, x = stack.pop()
                    n += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y + dy, x + dx
                            if 0 <= yy < occ.shape[0] and 0 <= xx < occ.shape[1] and occ[yy, xx] and not seen[yy, xx]:
                                seen[yy, xx] = True
                                stack.append((yy, xx))
                sizes.append(n)
    return sorted(sizes, reverse=True)


def main():
    b = Path(sys.argv[1])
    proj = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'devdocs/xeen/briefs/x1/L4'
    project = yaml.load((proj / 'project.yml').read_text(), Loader=yaml.CSafeLoader)
    sketch = yaml.load((proj / 'sketch.yml').read_text(), Loader=yaml.CSafeLoader)
    means = [sum(s['per_marker']) / 2 for s in project['map_stats']['slots']]
    scene = yaml.load(next(b.glob('*.scene.yml')).read_text(), Loader=yaml.CSafeLoader)
    p = parse_odm_file(next(b.glob('*.odm')))['payload']
    rows = terrain_rows('mm7')
    tm = np.array(p['tile_map']).reshape(128, 128)
    flags = {t: tile_flags(p, 'mm7', rows, t) for t in np.unique(tm)}
    water = np.zeros((N, N))
    for r in range(128):
        for c in range(128):
            if flags[tm[r, c]] & 2 and not flags[tm[r, c]] & 0x100:
                water[r // 8, c // 8] += 1
    mon = np.zeros((N, N))
    deco = np.zeros((N, N))
    hostiles = []          # (x, y, count)
    markers = {1: 0, 2: 0, 3: 0, 'single': 0}
    for s in scene.get('spawns') or []:
        if s['type_id'] != 3:
            continue
        i = s['index']
        if 1 <= i <= 3:
            n = means[i - 1]
            markers[i] += 1
        elif 4 <= i <= 12:
            n = 1
            markers['single'] += 1
        else:
            continue
        x, y = s['position']['x'], s['position']['y']
        mon[cell_of(x, y)] += n
        hostiles.append((x, y, n))
    placed = 0
    for a in sketch.get('actors') or []:
        if not a.get('hostile'):
            continue
        n = a.get('count', 1)
        x, y = (a['at'][0] - 64) * 512, (64 - a['at'][1]) * 512
        mon[cell_of(x, y)] += n
        hostiles.append((x, y, n))
        placed += n
    names = {}
    for e in scene['entities']:
        n = e['name'].lower()
        if 'start' in n or n.startswith('snd') or 'sound' in n or n.startswith('light') or n == 'fire light':
            continue
        deco[cell_of(e['position']['x'], e['position']['y'])] += 1
        names[e['name']] = names.get(e['name'], 0) + 1
    cen = slice(2, 14)
    land = water[cen, cen] < 48
    cmon = mon[cen, cen]
    cdeco = deco[cen, cen]
    total = sum(h[2] for h in hostiles)
    print('hostiles at load %.0f (markers %s = %d; placed hostile %d)' % (
        total, markers, sum(markers.values()), placed))
    print('decorations %d (central %d, outside %d)' % (deco.sum(), deco[2:14, 2:14].sum(),
                                                        deco.sum() - deco[2:14, 2:14].sum()))
    print('open meadow cells (central land, < 3 decorations) %d of %d' % (int((cdeco[land] < 3).sum()), land.sum()))
    print('quiet central land cells %d of %d (%.2f)' % (int((cmon[land] == 0).sum()), land.sum(),
                                                         (cmon[land] == 0).mean()))
    print('encounter regions (8-connected central cells) %s' % regions((cmon > 0) & land))
    import re
    lua = next(b.glob('*.lua')).read_text()
    print('chests opened by events %d (scene chest records %d)' % (
        len(set(re.findall(r'evt\.OpenChest\((\d+)\)', lua))), len(scene['initial_state'].get('chests') or [])))
    arrivals = {'party start': (54, 47)}
    for pt in sketch['points']:
        if pt['id'] in ('entrance:west_road', 'entrance:north_road'):
            arrivals[pt['id']] = tuple(pt['at'])
    for name, at in (('xd02 exit', (-10240, 16131)), ('xd03 exit', (-1024, 17565)), ('xd04 exit', (12288, -8987)),
                     ('xd05 exit', (9216, 16643)), ('xd01 yard', (-1930, 2918))):
        arrivals[name] = (at[0] / 512 + 64, 64 - at[1] / 512)
    for name, (ax, ay) in arrivals.items():
        x, y = (ax - 64) * 512, (64 - ay) * 512
        d = min(math.hypot(h[0] - x, h[1] - y) for h in hostiles)
        print('first fight from %-22s %6.0f' % (name, d))
    pois_path = Path(__file__).with_name('pois.yml')
    if pois_path.exists():
        pois = [((q['at'][0] - 64) * 512, (64 - q['at'][1]) * 512) for q in yaml.safe_load(pois_path.read_text())]
        doors = [((d['door'][0] - 64) * 512, (64 - d['door'][1]) * 512)
                 for d in yaml.safe_load(Path(__file__).with_name('house_doors.yml').read_text())]
        pts = pois + doors + [(h[0], h[1]) for h in hostiles]
        gap = np.zeros((24, 22), dtype=int)
        far = []
        for ty in range(19, 109):
            for tx in range(19, 104):
                if flags[tm[ty, tx]] & 2 and not flags[tm[ty, tx]] & 0x100:
                    continue
                x, y = (tx + 0.5 - 64) * 512, (64 - ty - 0.5) * 512
                far.append(min(math.hypot(px - x, py - y) for px, py in pts))
                if far[-1] > 3000:
                    gap[(ty - 16) // 4, (tx - 16) // 4] += 1
        far = np.array(far)
        print('central land tiles farther than 3,000 from a point of interest or a fight: %.3f; farthest %.0f' % (
            (far > 3000).mean(), far.max()))
        print('  where (4 x 4 tiles, x 16-104 across, y 16-112 down; # = mostly far):')
        for r in range(24):
            print('  %3d ' % (16 + 4 * r) + ''.join('#' if gap[r, c] >= 8 else ('+' if gap[r, c] else '.')
                                               for c in range(22)))
    top = sorted(names.items(), key=lambda kv: -kv[1])[:25]
    print('decorations by kind: ' + ', '.join('%s %d' % kv for kv in top))
    np.set_printoptions(linewidth=200)
    print('hostiles per central cell (rows north to south):')
    for r in range(2, 14):
        print('  ' + ' '.join(('%3.0f' % mon[r, c]) if mon[r, c] else ('  ~' if water[r, c] >= 48 else '  .')
                               for c in range(2, 14)))
    print('decorations per central cell:')
    for r in range(2, 14):
        print('  ' + ' '.join(('%3.0f' % deco[r, c]) if water[r, c] < 48 else '  ~' for c in range(2, 14)))


if __name__ == '__main__':
    main()
