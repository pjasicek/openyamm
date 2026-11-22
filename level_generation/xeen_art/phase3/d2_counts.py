#!/usr/bin/env python3
"""D2's figures against MAPS for the review board, measured on the brief (A6, phase 3).

    d2_counts.py        -> prints the figures and writes d2/counts.json

POIs: one point per spot, chained merging within 400 units (D-11.4, D-15), service and house doors included, landmarks,
junctions and the edge arrivals left out. Quiet land: cells of the playable square above the rim (y < 106) outside every
encounter area (the five marker areas and the ogres' placed area). First fight: the distance from an edge arrival to the
nearest encounter area (markers stand inside), or to the nearest placed hostile.
"""
import json
import math
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OGRE_AREA = [[60, 30], [98, 30], [100, 48], [60, 47]]


def mask(poly, scale=4):
    img = Image.new('L', (128 * scale, 128 * scale), 0)
    ImageDraw.Draw(img).polygon([(x * scale, y * scale) for x, y in poly], fill=255)
    return np.asarray(img) > 127


def poly_distance(p, poly):
    """Distance in cells from a point to a polygon (0 inside)."""
    m = mask(poly)
    if m[int(p[1] * 4), int(p[0] * 4)]:
        return 0.0
    ys, xs = np.nonzero(m)
    return float(np.min(np.hypot(xs / 4 - p[0], ys / 4 - p[1])))


def door_point(plot, footprint):
    x, y = plot['at']
    front, depth = footprint
    wx, wy = (front, depth) if plot['facing'] in 'ns' else (depth, front)
    return {'n': (x + wx / 2, y), 's': (x + wx / 2, y + wy), 'e': (x + wx, y + wy / 2), 'w': (x, y + wy / 2)}[plot['facing']]


def main():
    base = ROOT / 'devdocs/xeen/briefs/d2/L1'
    plan = yaml.safe_load((base / 'plan.yml').read_text())
    sketch = yaml.safe_load((base / 'sketch.yml').read_text())
    buildings = {b['id']: b for s in plan['spaces'] for b in s.get('buildings', []) or []}
    spots = []
    for p in sketch['points']:
        pid = p['id']
        if pid.startswith(('landmark:', 'junction:')) or pid in ('entrance:west_road', 'entrance:east_road'):
            continue
        spots.append((pid, p['at'][0] + 0.5, p['at'][1] + 0.5))
    doors = []
    for d in sketch['districts']:
        for plot in d.get('plots', []) or []:
            fp = buildings[plot['building']]['footprint_cells'][(plot.get('index') or 1) - 1]
            x, y = door_point(plot, fp)
            doors.append((plot['building'] + (f"#{plot['index']}" if plot.get('index') else ''), x, y))
    spots += doors
    # chained merging within 400 units (0.78 cells)
    groups = list(range(len(spots)))

    def find(i):
        while groups[i] != i:
            groups[i] = groups[groups[i]]
            i = groups[i]
        return i
    for i in range(len(spots)):
        for j in range(i + 1, len(spots)):
            if math.hypot(spots[i][1] - spots[j][1], spots[i][2] - spots[j][2]) * 512 <= 400:
                groups[find(i)] = find(j)
    merged = {}
    for i, s in enumerate(spots):
        merged.setdefault(find(i), []).append(s[0])
    # areas
    enc = [a for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter']
    land = np.zeros((512, 512), bool)
    land[19 * 4:106 * 4, 19 * 4:109 * 4] = True
    covered = np.zeros_like(land)
    for a in enc:
        covered |= mask(a['polygon'])
    covered |= mask(OGRE_AREA)
    quiet = float((land & ~covered).sum() / land.sum())
    range_land = land & mask([[0, 0], [128, 0], [128, 22], [116, 22], [104, 19], [96, 21], [88, 17], [80, 20],
                              [72, 18], [62, 17], [50, 15], [38, 17], [26, 15], [14, 19], [0, 21]])
    arrivals = {p['id']: p['at'] for p in sketch['points'] if p['id'] in ('entrance:west_road', 'entrance:east_road')}
    first = {}
    for aid, at in arrivals.items():
        best = []
        for a in enc:
            best.append((poly_distance(at, a['polygon']) * 512, a['id']))
        for act in sketch['actors']:
            if act.get('hostile'):
                best.append((math.hypot(act['at'][0] - at[0], act['at'][1] - at[1]) * 512, 'placed ' + act['monster']))
        first[aid] = sorted(best)[:2]
    markers = sum(a['count'] for a in enc)
    placed_hostile = sum(a['count'] for a in sketch['actors'] if a.get('hostile'))
    out = {
        'poi_spots': len(merged), 'poi_groups': sorted(merged.values()), 'doors': len(doors),
        'markers': markers, 'placed_hostile': placed_hostile, 'quiet_share': round(quiet, 3),
        'range_share_of_square': round(float(range_land.sum() / land.sum()), 3),
        'first_fight': {k: [(round(d), n) for d, n in v] for k, v in first.items()},
        'encounter_cells': {a['id']: int(mask(a['polygon']).sum() / 16) for a in enc},
        'ogre_area_cells': int(mask(OGRE_AREA).sum() / 16),
    }
    (HERE / 'd2' / 'counts.json').write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != 'poi_groups'}, indent=1))
    for g in out['poi_groups']:
        print('  ', ', '.join(g))


if __name__ == '__main__':
    main()
