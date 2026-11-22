#!/usr/bin/env python3
"""D3 measure (A5, 2026-11-20, seventh session; X4's measure_x4.py): MAPS section 0's figures with D-15, D-20 and
D-28 from a build folder and the L4 project.

Usage: measure.py [<build dir>] [<project dir>]

hostiles at load: spawn markers x the mean of their slot's per_marker, plus hostile placed actors.
first fight (D-15): only the map-edge arrivals and a new game's start are held to 2,000-6,000; town arrivals (stables,
  the Travel Pit, the mirrors' squares, the Town Portal anchor) keep the town buffer: 2,500 from town doors, no upper
  limit (D-11.2); dungeon-exit arrivals fall under the 6,000 rule.
POIs (D-20): as the shipped census (components() in devdocs/xeen/research/map_craft/measure_outdoor.py): bound
  events that do something, chained within 400, one set piece one spot; service doors and mirrors in, residences, map
  exits, hover-only titles and NPC actors out (NPCs and event-less landmarks still count for the 6,000 rule). Band
  35-55.
6,000 rule (D-11.5): no land tile inside the party's square farther than about 6,000 from a place (a POI, a door, an
  arrival) or a fight; wild land more than 3,000 (about 6 cells) from anything at most about 0.16.
"""
import json
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

B = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'output/studio_cal/d3/build_w'
P = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'devdocs/xeen/briefs/d3/L4'
# D-20: the shipped census (devdocs/xeen/research/map_craft/measure_outdoor.py, components()): every bound event that
# does something when clicked (a service door, a way into a dungeon, a chest, a well, a sign with words), chained within
# 400; residences, map exits and hover-only titles are not POIs. One set piece is one spot (SETS). NPC actors and the
# event-less landmarks (LANDMARKS) are not POIs but count as places for the 6,000 rule and as "anything" for the
# wild-land figure.
SETS = {
    "Sandcaster's south gate": ('thing:south_gate_',),
    "Sandcaster's east gate": ('thing:east_gate_',),
    'the pear hut': ('thing:pear_',),
    'the fig hut': ('thing:fig_',),
}
NOT_POI = ()
LANDMARKS = ('thing:wrath_bridge', 'thing:wrath_falls', 'thing:spring_fall', 'thing:jetty_deck', 'thing:great_oak_x')
EDGE_ARRIVALS = {'D2 road (west start)': 'entrance:west_road', 'D4 road (north start)': 'entrance:north_road'}
TOWN_ARRIVALS = ('entrance:sandcaster_square', 'entrance:sandcaster_stables')
OTHER_ARRIVALS = ('entrance:dd18_shaft', 'entrance:dd19_gate', 'entrance:dd07_door')


def W(at):
    return ((at[0] - 64) * 512, (64 - at[1]) * 512)


def is_poi(s):
    """A bound event that does something: effects, a condition, Lua, a way in or a chest (a title alone is a hover)."""
    sid = s['id']
    if any(sid.startswith(p) for p in NOT_POI) or s.get('same_event_as'):
        return False
    if any(p.get('effects') or p.get('condition') for p in s.get('parts') or []):
        return True
    return bool(s.get('effects') or s.get('else_effects') or s.get('chest') or s.get('condition') or s.get('into')
                or s.get('lua'))


def where(s):
    if 'at' in s:
        return W(s['at'])
    ln = s.get('line') or s['outline']
    return W(((ln[0][0] + ln[-1][0]) / 2, (ln[0][1] + ln[-1][1]) / 2))


def main():
    project = yaml.safe_load((P / 'project.yml').read_text())
    sketch = yaml.safe_load((P / 'sketch.yml').read_text())
    build = json.loads((B / 'build.json').read_text())
    scene = yaml.load(next(B.glob('*.scene.yml')).read_text(), Loader=yaml.CSafeLoader)
    means = [sum(s['per_marker']) / 2 for s in project['map_stats']['slots']]
    hostiles = []
    markers = {1: 0, 2: 0, 3: 0}
    for s in scene.get('spawns') or []:
        if s['type_id'] != 3 or not 1 <= s['index'] <= 3:
            continue
        markers[s['index']] += 1
        hostiles.append((s['position']['x'], s['position']['y'], means[s['index'] - 1], s['index']))
    placed = 0
    for a in sketch.get('actors') or []:
        if a.get('hostile'):
            x, y = W(a['at'])
            hostiles.append((x, y, a.get('count', 1), 'placed'))
            placed += a.get('count', 1)
    total = sum(h[2] for h in hostiles)
    print('hostiles at load %.1f (markers %s = %d, placed %d)' % (total, markers, sum(markers.values()), placed))

    def nearest(x, y):
        return min(math.hypot(h[0] - x, h[1] - y) for h in hostiles)
    pts = {p['id']: p['at'] for p in sketch['points']}
    built = {a['entrance']: a['at'] for a in build['arrivals']}
    print('first fight from the map-edge arrivals (D-15: 2,000-6,000):')
    for name, eid in EDGE_ARRIVALS.items():
        at = built.get(eid) or (W(pts[eid]) if eid in pts else W((36, 107)))
        print('   %-36s %6.0f' % (name, nearest(at[0], at[1])))
    st = build.get('start') or {}
    if st:
        print('   %-36s %6.0f  (the build\'s start, %s)' % ('new-game start', nearest(st['x'], st['y']),
                                                            st.get('entrance')))
    doors = {b['id']: b['door'] for b in build['buildings'] if b.get('door')}
    town_doors = [d for k, d in doors.items() if k.startswith(('building:sc_', 'building:wq_', 'building:xr_', 'building:celia', 'building:thaddeus'))]
    print('town buffer (D-15: 2,500, no upper limit):')
    print('   %-36s %6.0f' % ('nearest hostile to a town door', min(nearest(d[0], d[1]) for d in town_doors)))
    for eid in TOWN_ARRIVALS:
        if eid in pts:
            x, y = W(pts[eid])
            print('   %-36s %6.0f' % (eid, nearest(x, y)))
    print('other arrivals (dungeon exits under the 6,000 rule):')
    for eid in OTHER_ARRIVALS:
        if eid in pts:
            x, y = W(pts[eid])
            print('   %-36s %6.0f' % (eid, nearest(x, y)))
    # POIs (D-20)
    spots = []
    for s in sketch['structures']:
        if is_poi(s):
            spots.append((s['id'], where(s)))
    town = yaml.safe_load((ROOT / 'assets_dev/worlds/xeen/source/towns/d3.yml').read_text())
    kinds = {h['door']: h.get('kind') for h in town['houses'] if h.get('door')}
    for b in build['buildings']:
        if b.get('door') and b.get('house') and kinds.get(b['id']) != 'residence' \
                and '_houses#' not in b['id']:
            spots.append((b['id'], (b['door'][0], b['door'][1])))
    n = len(spots)
    parent = list(range(n))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            same_set = any(any(spots[i][0].startswith(p) for p in ps) and any(spots[j][0].startswith(p) for p in ps)
                           for ps in SETS.values())
            if same_set or math.hypot(spots[i][1][0] - spots[j][1][0], spots[i][1][1] - spots[j][1][1]) <= 400:
                parent[root(i)] = root(j)
    groups = {}
    for i in range(n):
        groups.setdefault(root(i), []).append(i)
    merged = [(spots[g[0]][1], [spots[i][0] for i in g]) for g in groups.values()]
    chests = [s for s in sketch['structures'] if s.get('chest')]
    print('POIs (D-20: bound events chained within 400, one set piece one spot, residences and NPCs out): %d '
          '(band 35-55, D-28 cap 55); chests %d' % (len(merged), len(chests)))
    if '-v' in sys.argv:
        for m in sorted(merged, key=lambda m: m[1][0]):
            print('   %s' % ', '.join(m[1]))
    landmarks = [where(s) for s in sketch['structures'] if s['id'] in LANDMARKS]
    npcs = [W(a['at']) for a in sketch['actors'] if a.get('npc')]
    # land, roads, the 6,000 rule
    p = parse_odm_file(next(B.glob('*.odm')))['payload']
    rows = terrain_rows('mm7')
    tm = np.array(p['tile_map']).reshape(128, 128)
    hm = np.array(p['height_map']).reshape(128, 128)
    flags = {t: tile_flags(p, 'mm7', rows, t) for t in np.unique(tm)}
    places = [m[0] for m in merged] + [W(pts[e]) for e in pts if e.startswith('entrance:')] + landmarks + npcs
    places += list(doors.values())
    places = [q[:2] for q in places] + [(h[0], h[1]) for h in hostiles]
    places = np.array(places, dtype=float)
    far = []
    worst = (0, None)
    farcells = []
    land = road = 0
    for ty in range(19, 108):
        for tx in range(19, 109):
            f = flags[tm[ty, tx]]
            if f & 2 and not f & 0x100:
                continue
            if hm[ty:ty + 2, tx:tx + 2].min() < 8:      # the rim cliff and the stars below it, not land
                continue
            land += 1
            if f & 0x100:
                road += 1
            x, y = (tx + 0.5 - 64) * 512, (64 - ty - 0.5) * 512
            d = float(np.min(np.hypot(places[:, 0] - x, places[:, 1] - y)))
            far.append(d)
            if d > 5500:
                farcells.append((tx, ty, int(d)))
            if d > worst[0]:
                worst = (d, (tx, ty))
    far = np.array(far)
    # the wild-land figure of OUTDOOR_REBUILD_PROCEDURE.md (shipped 0.28-0.60): land more than 3 cells from anything
    ents = np.array([(e['position']['x'], e['position']['y']) for e in scene.get('entities') or []] +
                    [tuple(q) for q in places], dtype=float)
    bare = 0
    for ty in range(19, 108):
        for tx in range(19, 109):
            f = flags[tm[ty, tx]]
            if (f & 2 and not f & 0x100) or hm[ty:ty + 2, tx:tx + 2].min() < 8:
                continue
            x, y = (tx + 0.5 - 64) * 512, (64 - ty - 0.5) * 512
            if np.min(np.hypot(ents[:, 0] - x, ents[:, 1] - y)) > 1536:
                bare += 1
    print('land more than 3 cells (1,536) from anything (decorations, places, fights): %.3f' % (bare / land))
    print('6,000 rule: farthest land from a place or fight %.0f at cell %s; tiles over 6,000: %d; over 3,000: %.3f'
          % (worst[0], worst[1], int((far > 6000).sum()), (far > 3000).mean()))
    print('   over 5,500: %s' % farcells)
    print('road tiles %d of %d land tiles in the square (%.1f %%)' % (build['counts']['road_cells'], land,
                                                                       100.0 * build['counts']['road_cells'] / land))
    print('decorations %d, entities %d, buildings %d' % (len(scene.get('entities') or []), build['counts']['entities'],
                                                        build['counts']['buildings']))


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
