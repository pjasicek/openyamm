#!/usr/bin/env python3
"""Where MM puts decorations: distance to the nearest wall of their sector and to the nearest other prop.

Reads data/sectors.json and re-parses each BLV that has decorations. Prints per-world medians and shares.
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
DATA = Path(__file__).resolve().parents[1] / 'data'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tours import newell, seg_dist  # noqa: E402

LIGHT = re.compile(r'torch|brazier|lantern|chandelier|candle|flambeau|sconce|fire|lamp|campfire|burning', re.I)


def main():
    table = ROOT / 'assets_dev/engine/data_tables/decoration_data.txt'
    hints = {r[1].lower(): (r[2], int(r[6])) for r in csv.reader(table.open(), delimiter='\t') if r and r[0].isdigit()}
    rows = json.loads((DATA / 'sectors.json').read_text())
    by_map = defaultdict(list)
    for r in rows:
        if r['decoration_positions']:
            by_map[(r['world'], r['map'])].append(r)
    stats = defaultdict(lambda: defaultdict(list))
    for (world, name), rs in by_map.items():
        p = parse_blv_file(ROOT / 'assets_dev/worlds' / world / 'maps' / name)['payload']
        V = np.array([[v['x'], v['y'], v['z']] for v in p['vertices']], float)
        walls = defaultdict(list)
        for f in p['faces']:
            if f['is_portal']:
                continue
            P = V[f['vertex_indices']]
            n = newell(P)
            a = np.linalg.norm(n)
            if a and abs(n[2] / a) < 0.3:
                for i in range(len(P)):
                    walls[f['room_number']].append((P[i, :2], P[(i + 1) % len(P), :2]))
        for r in rs:
            props = []
            for deco, pos in r['decoration_positions']:
                hint, light = hints.get(deco, ('', 0))
                role = 'light' if light or LIGHT.search(hint + ' ' + deco) else 'prop'
                pt = np.array(pos[:2], float)
                d = min([seg_dist(pt, a, b) for a, b in walls[r['sector']]] or [1e9])
                stats[world][role + '_wall'].append(d)
                if role == 'prop':
                    props.append(pt)
            for i, pt in enumerate(props):
                others = [np.linalg.norm(pt - q) for j, q in enumerate(props) if j != i]
                stats[world]['prop_nn'].append(min(others) if others else 1e9)
            if props:
                stats[world]['props_per_dressed_sector'].append(len(props))
    for world in ('mm6', 'mm7', 'mm8'):
        s = stats[world]
        pw, lw, nn = map(np.array, (s['prop_wall'], s['light_wall'], s['prop_nn']))
        print(f"== {world}: props {len(pw)}: median wall distance {np.median(pw):.0f}, within 160 of a wall "
              f"{np.mean(pw < 160):.0%}, further than 400 {np.mean(pw > 400):.0%}; nearest other prop median "
              f"{np.median(nn[nn < 1e8]):.0f} (alone in sector {np.mean(nn >= 1e8):.0%}, within 200 {np.mean(nn < 200):.0%}); "
              f"props per dressed sector median {np.median(s['props_per_dressed_sector']):.0f} "
              f"max {max(s['props_per_dressed_sector'])}")
        print(f"   lights {len(lw)}: median wall distance {np.median(lw):.0f}, within 64 {np.mean(lw < 64):.0%}")


if __name__ == '__main__':
    main()
