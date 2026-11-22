#!/usr/bin/env python3
"""X6 measure (A5, 2026-11-20; D3's measure.py): MAPS section 0's figures with D-15, D-20 and D-31 from a build folder
and the L4 project.

Usage: measure.py [<build dir>] [<project dir>] [-v]

hostiles at load: spawn markers x the mean of their slot's per_marker (no placed hostiles on X6).
kill XP per member: each marker's slot at its Dif mix (tools/xeen/balance.py) over its family's A/B/C levels, L(L+10).
first fight (D-15): the map-edge arrivals 2,000-6,000; town arrivals and town doors keep the town buffer (2,500, no
  upper limit); dungeon doors fall under the 6,000 rule.
POIs (D-20): the shipped census: bound events that do something, chained within 400, one set piece one spot; service
  doors in, residences, exits, hover-only titles and NPC actors out. D-31: at most 30.
quiet land: land tiles outside every encounter area (at least a third).
6,000 rule and wild land (D-11.5): no land tile farther than 6,000 from a place or fight; land more than 3 cells from
  anything at most 0.16.
relief (D-31): the height range of the land inside the playable box (at least 2,500).
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'output/xeen_review/scale'))
sys.path.insert(0, str(ROOT / 'util'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from heatmaps import terrain_rows, tile_flags  # noqa: E402
from map_export import parse_odm_file  # noqa: E402
import gen_l1 as L1  # noqa: E402
import kit as K  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('-')]
B = Path(args[0]) if args else ROOT / 'output/studio_cal/x6/build_w'
P = Path(args[1]) if len(args) > 1 else ROOT / 'devdocs/xeen/briefs/x6/L4'
SETS = {'the yard gate': ('thing:yard_gate_',), "the Sphinx's door and the hoard mound (L1: one spot)": ('thing:northern_sphinx', 'thing:cloud_hoard')}
NOT_POI = ()
LANDMARKS = ('thing:northern_sphinx', 'thing:southern_sphinx', 'thing:castle_basenji', 'thing:caravanserai',
             'thing:druid_spring', 'thing:swallowed_wagon', 'thing:werewolf_den', 'thing:saul_hut',
             'thing:arie_tent', 'thing:prospector_tent', 'thing:shrine_energy_house', 'thing:gargoyle_watch')
EDGE_ARRIVALS = {'X4 road (east start)': 'entrance:east_road', 'X5 road (south start)': 'entrance:south_road'}
TOWN_ARRIVALS = ('entrance:sphinx_wells', 'entrance:warzone_coach')
OTHER_ARRIVALS = ('entrance:xd14_gate', 'entrance:xd15_door', 'entrance:xd20_gate', 'entrance:fd02_door')
DIF_MIX = {0: (1, 0, 0), 1: (0.9, 0.08, 0.02), 2: (0.7, 0.2, 0.1), 3: (0.5, 0.3, 0.2), 4: (0.3, 0.4, 0.3),
           5: (0.1, 0.5, 0.4)}   # tools/xeen/balance.py
LEVELS = {'Xeen Sand Worm': (30, 38, 45), 'Xeen Werewolf': (20, 30, 40), 'Xeen Elemental Golem': (22, 28, 50)}


def W(at):
    return ((at[0] - 64) * 512, (64 - at[1]) * 512)


def is_poi(s):
    """A bound event that does something: effects, a condition, Lua, a way in or a chest (a title alone is a hover)."""
    sid = s['id']
    if any(sid.startswith(p) for p in NOT_POI) or s.get('same_event_as'):
        return False
    if any(p.get('effects') or p.get('condition') for p in s.get('parts') or []):
        return True
    if any(d.get('effects') or d.get('into') or d.get('question') or d.get('condition') for d in s.get('doors') or []):
        return True
    return bool(s.get('effects') or s.get('else_effects') or s.get('chest') or s.get('condition') or s.get('into')
                or s.get('lua') or s.get('question'))


def where(s):
    if s.get('doors') and s['id'] in DOOR_AT:
        return DOOR_AT[s['id']]
    if 'at' in s:
        return W(s['at'])
    ln = s.get('line') or s['outline']
    return W(((ln[0][0] + ln[-1][0]) / 2, (ln[0][1] + ln[-1][1]) / 2))


DOOR_AT = {}


def main():
    for b in json.loads((B / 'build.json').read_text())['buildings']:
        pass
    things = subprocess.run([str(ROOT / 'openyamm-studio/build-xeen/oymap'), 'things', str(P), '--assets',
                             str(ROOT / 'assets_dev')], capture_output=True, text=True).stdout
    for line in things.split('\n'):
        if ' evt:door:thing:' in line and ' at [' in line:
            tid = line.split(' evt:door:')[1].split('.')[0].split(' ')[0]
            xyz = line.split(' at [')[1].split(']')[0].split(',')
            DOOR_AT[tid] = (float(xyz[0]), float(xyz[1]))
    project = yaml.safe_load((P / 'project.yml').read_text())
    sketch = yaml.safe_load((P / 'sketch.yml').read_text())
    build = json.loads((B / 'build.json').read_text())
    scene = yaml.load(next(B.glob('*.scene.yml')).read_text(), Loader=yaml.CSafeLoader)
    slots = project['map_stats']['slots']
    means = [sum(s['per_marker']) / 2 for s in slots]
    hostiles = []
    markers = {1: 0, 2: 0, 3: 0}
    kill = 0.0
    fam = {}
    for s in scene.get('spawns') or []:
        if s['type_id'] != 3 or not 1 <= s['index'] <= 3:
            continue
        i = s['index']
        markers[i] += 1
        hostiles.append((s['position']['x'], s['position']['y'], means[i - 1], i))
        sl = slots[i - 1]
        v = means[i - 1] * sum(w * L * (L + 10) for w, L in zip(DIF_MIX[sl['tier']], LEVELS[sl['monster']]))
        kill += v
        fam[sl['monster']] = fam.get(sl['monster'], 0) + v
    placed = sum(a.get('count', 1) for a in sketch.get('actors') or [] if a.get('hostile'))
    total = sum(h[2] for h in hostiles) + placed
    print('hostiles at load %.1f (markers %s = %d, placed %d)' % (total, markers, sum(markers.values()), placed))
    print('kill XP per member %.1fk (MAPS 41.5k; D-31 42.1k): %s' % (
        kill / 4000, ', '.join('%s %.1fk' % (k, v / 4000) for k, v in fam.items())))

    def nearest(x, y):
        return min(math.hypot(h[0] - x, h[1] - y) for h in hostiles)
    pts = {p['id']: p['at'] for p in sketch['points']}
    built = {a['entrance']: a['at'] for a in build['arrivals']}
    print('first fight from the map-edge arrivals (D-15: 2,000-6,000):')
    for name, eid in EDGE_ARRIVALS.items():
        at = built.get(eid) or W(pts[eid])
        print('   %-36s %6.0f' % (name, nearest(at[0], at[1])))
    st = build.get('start') or {}
    if st:
        print("   %-36s %6.0f  (the build's start, %s; a town arrival)" % ('new-game start', nearest(st['x'], st['y']),
                                                                         st.get('entrance')))
    doors = {b['id']: b['door'] for b in build['buildings'] if b.get('door')}
    print('town buffer (D-15: 2,500, no upper limit):')
    wells = [d for k, d in doors.items() if k.startswith('building:x6_')]
    print('   %-36s %6.0f' % ("Sphinx Wells' doors, nearest hostile", min(nearest(d[0], d[1]) for d in wells)))
    yard = [d for k, d in doors.items() if k.startswith('building:warzone')]
    for s in sketch['structures']:
        if s['id'] in ('thing:arena_gate', 'thing:yard_gate_outer_n'):
            yard.append(where(s))
    print('   %-36s %6.0f' % ('the coach yard (house, both gates)', min(nearest(d[0], d[1]) for d in yard)))
    for eid in TOWN_ARRIVALS:
        x, y = W(pts[eid])
        print('   %-36s %6.0f' % (eid, nearest(x, y)))
    for name, poly in (('Arie', 'zone:arie_camp'), ('Saul', 'zone:saul_hermitage'), ('the Summer Druid',
                                                                                     'zone:druid_grove')):
        a = next(q for q in sketch['actors'] if q.get('npc') and K.inside(q['at'], L1.TOWNS[poly]))
        x, y = W(a['at'])
        print('   %-36s %6.0f' % (name, nearest(x, y)))
    print('other arrivals (dungeon doors, under the 6,000 rule):')
    for eid in OTHER_ARRIVALS:
        x, y = W(pts[eid])
        print('   %-36s %6.0f' % (eid, nearest(x, y)))
    # POIs (D-20)
    spots = [(s['id'], where(s)) for s in sketch['structures'] if is_poi(s)]
    town = yaml.safe_load((ROOT / 'assets_dev/worlds/xeen/source/towns/x6.yml').read_text())
    kinds = {h['door']: h.get('kind') for h in town['houses'] if h.get('door')}
    for b in build['buildings']:
        if b.get('door') and b.get('house') and kinds.get(b['id']) != 'residence' and '_houses#' not in b['id']:
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
    obelisks = [s for s in sketch['structures'] if s['kind'] == 'obelisk' and 'obelisks.' in json.dumps(s)]
    print('POIs (D-20 census; D-31 cap 30): %d; chests %d; obelisks %d' % (len(merged), len(chests), len(obelisks)))
    if '-v' in sys.argv:
        for m in sorted(merged, key=lambda m: m[1][0]):
            print('   %s' % ', '.join(m[1]))
    xs = sorted(m[0] for m in merged)
    nn = []
    for i, a in enumerate(merged):
        nn.append(min(math.hypot(a[0][0] - b[0][0], a[0][1] - b[0][1]) for j, b in enumerate(merged) if j != i))
    print('   POI nearest-neighbour median %.0f (min %.0f, max %.0f)' % (float(np.median(nn)), min(nn), max(nn)))
    landmarks = [where(s) for s in sketch['structures'] if s['id'] in LANDMARKS]
    npcs = [W(a['at']) for a in sketch['actors'] if a.get('npc')]
    # land, roads, quiet land, relief, the 6,000 rule
    p = parse_odm_file(next(B.glob('*.odm')))['payload']
    rows = terrain_rows('mm7')
    tm = np.array(p['tile_map']).reshape(128, 128)
    hm = np.array(p['height_map']).reshape(128, 128) * 32
    flags = {t: tile_flags(p, 'mm7', rows, t) for t in np.unique(tm)}
    places = [m[0] for m in merged] + [W(pts[e]) for e in pts if e.startswith('entrance:')] + landmarks + npcs
    places += list(doors.values())
    places = [q[:2] for q in places] + [(h[0], h[1]) for h in hostiles]
    places = np.array(places, dtype=float)
    ents = np.array([(e['position']['x'], e['position']['y']) for e in scene.get('entities') or []] +
                    [tuple(q) for q in places], dtype=float)
    far, farcells, worst = [], [], (0, None)
    land = road = quiet = bare = 0
    hmin, hmax, wet = (1e9, None), (0, None), 0
    for ty in range(19, 109):
        for tx in range(19, 109):
            f = flags[tm[ty, tx]]
            water = f & 2 and not f & 0x100
            if hm[ty:ty + 2, tx:tx + 2].min() < 256:     # the rim cliff and the stars below it, not land
                continue
            if water:
                wet += 1
                continue
            land += 1
            h = hm[ty:ty + 2, tx:tx + 2]
            if h.min() < hmin[0]:
                hmin = (int(h.min()), (tx, ty))
            if h.max() > hmax[0]:
                hmax = (int(h.max()), (tx, ty))
            if f & 0x100:
                road += 1
            c = (tx + 0.5, ty + 0.5)
            if not any(K.inside(c, a[3]) for a in L1.AREAS):
                quiet += 1
            x, y = (tx + 0.5 - 64) * 512, (64 - ty - 0.5) * 512
            d = float(np.min(np.hypot(places[:, 0] - x, places[:, 1] - y)))
            far.append(d)
            if d > 5500:
                farcells.append((tx, ty, int(d)))
            if d > worst[0]:
                worst = (d, (tx, ty))
            if np.min(np.hypot(ents[:, 0] - x, ents[:, 1] - y)) > 1536:
                bare += 1
    far = np.array(far)
    print('quiet land (outside every encounter area): %.2f (>= 1/3)' % (quiet / land))
    print('land more than 3 cells (1,536) from anything (decorations, places, fights): %.3f (<= 0.16)' % (bare / land))
    print('6,000 rule: farthest land from a place or fight %.0f at cell %s; tiles over 6,000: %d; over 3,000: %.3f'
          % (worst[0], worst[1], int((far > 6000).sum()), (far > 3000).mean()))
    print('   over 5,500: %s' % farcells[:20])
    print('relief inside the box (land): %d at %s to %d at %s = %d (D-31 >= 2,500); the oasis pond water 1,000 '
          '(range from it %d); water tiles %d' % (hmin[0], hmin[1], hmax[0], hmax[1], hmax[0] - hmin[0],
                                                  hmax[0] - 1000, wet))
    print('road tiles %d of %d land tiles in the square (%.1f %%)' % (build['counts']['road_cells'], land,
                                                                       100.0 * build['counts']['road_cells'] / land))
    print('decorations %d, entities %d, buildings %d' % (len(scene.get('entities') or []), build['counts']['entities'],
                                                        build['counts']['buildings']))
    exp = B / 'export.json'
    if not exp.exists() or exp.stat().st_mtime < next(B.glob('*.odm')).stat().st_mtime:
        subprocess.run([str(ROOT / 'openyamm-studio/build-xeen/oymap'), 'export', str(next(B.glob('*.odm'))),
                        '--out', str(exp)], check=True, stdout=subprocess.DEVNULL)
    m = json.loads(exp.read_text())['map']
    tex = set()
    for b in m['bmodels']:
        for f in b['faces']:
            tex.add(f['texture'])
    print('BModel face textures: %d distinct (outdoor cap 120)' % len(tex))
    if '-v' in sys.argv:
        print('   ' + ' '.join(sorted(tex)))


if __name__ == '__main__':
    main()
