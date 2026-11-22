#!/usr/bin/env python3
"""X7 measure (A5, 2026-11-20; X6's measure.py): MAPS section 0's figures with D-15, D-20 and D-40 from a build folder
and the L4 project.

Usage: measure.py [<build dir>] [<project dir>] [-v]

hostiles at load: spawn markers x the mean of their slot's per_marker, plus the placed hostiles.
kill XP per member: each marker's slot at its Dif mix (tools/xeen/balance.py) over its family's A/B/C levels, L(L+10);
  the south's orcs (Act I, D-40 change 2) apart from the north (Act V).
first fight (D-15): the map-edge arrivals 2,000-6,000.
D-40: no marker within 2,000 of the cleft's arrival; dragons 4,000 from it and 6,000 from the Dragon Cave track and the
  tax office's mouth.
POIs (D-20 census, the lane's for X6 and D3): bound events that do something, chained within 400, one set piece one spot
  (D-40 change 5: the idols with XD-16's door, the outpost's chest with the outpost); D-40 at most 28.
quiet land, 6,000 rule and wild land (D-11.5), relief inside the box, textures.
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
import land as LD  # noqa: E402
import places as PL  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('-')]
B = Path(args[0]) if args else ROOT / 'output/studio_cal/x7/build_w'
P = Path(args[1]) if len(args) > 1 else ROOT / 'devdocs/xeen/briefs/x7/L4'
SETS = {"XD-16's door and its idols (D-40)": ('thing:xd16_mouth', 'thing:idol_'),
        'the Dragon Tower and its gate': ('thing:dragon_tower', 'thing:fd04_gate'),
        'the orc outpost and its chest (D-40)': ('thing:outpost_',),
        'the cleft and its rock': ('thing:xd17_cleft', 'thing:cleft_')}
LANDMARKS = ('thing:watch_tower', 'thing:watch_barracks', 'thing:pony_shed', 'thing:east_lookout',
             'thing:boundary_stone', 'thing:fallen_cart', 'thing:sablewing_cave', 'thing:dragon_tower',
             'thing:black_bridge', 'thing:miner_adit', 'thing:orc_den', 'thing:slag_1', 'thing:charcoal_pit_1',
             'thing:dragon_skull_1', 'thing:signpost_fork', 'thing:signpost_slope', 'thing:broken_wagon')
EDGE_ARRIVALS = {'X1 road (south start)': 'entrance:south_road', 'X4 road (west start)': 'entrance:west_road'}
DIF_MIX = {0: (1, 0, 0), 1: (0.9, 0.08, 0.02), 2: (0.7, 0.2, 0.1), 3: (0.5, 0.3, 0.2), 4: (0.3, 0.4, 0.3),
           5: (0.1, 0.5, 0.4)}   # tools/xeen/balance.py
LEVELS = {'Xeen Orc': (5, 7, 10), 'Xeen Hydra': (45, 55, 65), 'Xeen Dragon': (60, 66, 75)}
PLACED_LEVEL = {'11593': 55, '11030': 5, '11032': 10}


def W(at):
    return ((at[0] - 64) * 512, (64 - at[1]) * 512)


def is_poi(s):
    if any(p.get('effects') or p.get('condition') for p in s.get('parts') or []):
        return True
    if any(d.get('effects') or d.get('into') or d.get('question') or d.get('condition') for d in s.get('doors') or []):
        return True
    return bool(s.get('effects') or s.get('else_effects') or s.get('chest') or s.get('condition') or s.get('into')
                or s.get('lua') or s.get('question'))


def where(s):
    if s['kind'] == 'building':
        if s.get('doors') and s['id'] in DOOR_AT:
            return DOOR_AT[s['id']]
        return W((s['at'][0] + s['size'][0] / 2, s['at'][1] + s['size'][1] / 2))
    if 'at' in s:
        return W(s['at'])
    ln = s.get('line') or s['outline']
    return W(((ln[0][0] + ln[-1][0]) / 2, (ln[0][1] + ln[-1][1]) / 2))


DOOR_AT = {}


def main():
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
    kill = {1: 0.0, 2: 0.0, 3: 0.0}
    for s in scene.get('spawns') or []:
        if s['type_id'] != 3 or not 1 <= s['index'] <= 3:
            continue
        i = s['index']
        markers[i] += 1
        hostiles.append((s['position']['x'], s['position']['y'], means[i - 1], i))
        sl = slots[i - 1]
        kill[i] += means[i - 1] * sum(w * L * (L + 10) for w, L in zip(DIF_MIX[sl['tier']], LEVELS[sl['monster']]))
    placed = [a for a in sketch.get('actors') or [] if a.get('hostile')]
    n_placed = sum(a.get('count', 1) for a in placed)
    placed_xp = {}
    for a in placed:
        L = PLACED_LEVEL[a['monster']]
        placed_xp[a['monster']] = placed_xp.get(a['monster'], 0) + a.get('count', 1) * L * (L + 10)
        for _ in range(a.get('count', 1)):
            x, y = W(a['at'])
            hostiles.append((x, y, 1, 'placed'))
    total = sum(h[2] for h in hostiles if h[3] != 'placed') + n_placed
    print('hostiles at load %.1f (markers orcs %d, hydras %d, dragons %d = %d; placed %d: %s)' % (
        total, markers[1], markers[2], markers[3], sum(markers.values()), n_placed,
        ', '.join('%s x%d' % (a['monster'], a.get('count', 1)) for a in placed)))
    act1 = (kill[1] + placed_xp.get('11030', 0) + placed_xp.get('11032', 0)) / 4000
    act5 = (kill[2] + kill[3] + placed_xp.get('11593', 0)) / 4000
    print('kill XP per member %.1fk: Act I (the south orcs, D-40 change 2) %.2fk; Act V %.1fk (hydras %.1fk, dragons '
          '%.1fk, golems %.1fk)' % (act1 + act5, act1, act5, kill[2] / 4000, kill[3] / 4000,
                                    placed_xp.get('11593', 0) / 4000))

    def nearest(x, y, which=None):
        hs = [h for h in hostiles if which is None or h[3] in which]
        return min(math.hypot(h[0] - x, h[1] - y) for h in hs)
    pts = {p['id']: p['at'] for p in sketch['points']}
    built = {a['entrance']: a['at'] for a in build['arrivals']}
    print('first fight from the map-edge arrivals (D-15: 2,000-6,000):')
    for name, eid in EDGE_ARRIVALS.items():
        at = built.get(eid) or W(pts[eid])
        print('   %-36s %6.0f' % (name, nearest(at[0], at[1])))
    cx, cy = W(PL.CLEFT_ARRIVAL)
    print("D-40: the cleft's arrival %s: nearest marker %.0f (>= 2,000), nearest dragon marker %.0f (>= 4,000)" % (
        PL.CLEFT_ARRIVAL, nearest(cx, cy, (1, 2, 3)), nearest(cx, cy, (3,))))
    dr = [h for h in hostiles if h[3] == 3]
    track = [W(p) for p in LD.NORTH_TRACK]

    def seg(px, py, a, b):
        return K.seg_dist((px, py), a, b)
    dtrack = min(min(seg(h[0], h[1], a, b) for a, b in zip(track, track[1:])) for h in dr)
    m18 = W(PL.XD18)
    m16 = W(PL.XD16)
    print('D-40: dragons from the Dragon Cave track %.0f, from the tax office mouth (XD-18) %.0f (>= 6,000); from '
          'the Volcano Cave %.0f' % (dtrack, min(math.hypot(h[0] - m18[0], h[1] - m18[1]) for h in dr),
                                     min(math.hypot(h[0] - m16[0], h[1] - m16[1]) for h in dr)))
    sx, sy = W(PL.SABLEWING)
    print("Sablewing's nearest fight %.0f (town buffer 2,500)" % nearest(sx, sy))
    gx, gy = W(L1.GAP)
    print('north monsters (hydras, dragons, golems) from the Gap %.0f, from the north road\'s end' % nearest(
        gx, gy, (2, 3, 'placed')))
    # POIs (D-20)
    spots = [(s['id'], where(s)) for s in sketch['structures'] if is_poi(s)]
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
    print('POIs (D-20 census; D-40 at most 28): %d; chests %d' % (len(merged), len(chests)))
    if '-v' in sys.argv:
        for m in sorted(merged, key=lambda m: m[1][0]):
            print('   %s' % ', '.join(m[1]))
    nn = []
    for i, a in enumerate(merged):
        nn.append(min(math.hypot(a[0][0] - b[0][0], a[0][1] - b[0][1]) for j, b in enumerate(merged) if j != i))
    print('   POI nearest-neighbour median %.0f (min %.0f, max %.0f; D-40 accepts 3,280 for a trap map)' % (
        float(np.median(nn)), min(nn), max(nn)))
    landmarks = [where(s) for s in sketch['structures'] if s['id'] in LANDMARKS]
    npcs = [W(a['at']) for a in sketch['actors'] if a.get('npc')]
    p = parse_odm_file(next(B.glob('*.odm')))['payload']
    rows = terrain_rows('mm7')
    tm = np.array(p['tile_map']).reshape(128, 128)
    hm = np.array(p['height_map']).reshape(128, 128) * 32
    flags = {t: tile_flags(p, 'mm7', rows, t) for t in np.unique(tm)}
    places = [m[0] for m in merged] + [W(pts[e]) for e in pts if e.startswith('entrance:')] + landmarks + npcs
    places = [q[:2] for q in places] + [(h[0], h[1]) for h in hostiles]
    places = np.array(places, dtype=float)
    ents = np.array([(e['position']['x'], e['position']['y']) for e in scene.get('entities') or []] +
                    [tuple(q) for q in places], dtype=float)
    far, farcells, worst = [], [], (0, None)
    land = quiet = bare = wet = 0
    hmin, hmax = (1e9, None), (0, None)
    for ty in range(19, 109):
        for tx in range(19, 109):
            f = flags[tm[ty, tx]]
            if hm[ty:ty + 2, tx:tx + 2].min() < 256:     # the rim cliff and the stars below it, not land
                continue
            if f & 2 and not f & 0x100:
                wet += 1
                continue
            land += 1
            h = hm[ty:ty + 2, tx:tx + 2]
            if h.min() < hmin[0]:
                hmin = (int(h.min()), (tx, ty))
            if h.max() > hmax[0]:
                hmax = (int(h.max()), (tx, ty))
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
    print('relief inside the box (land): %d at %s to %d at %s = %d (>= 2,500); liquid tiles %d' % (
        hmin[0], hmin[1], hmax[0], hmax[1], hmax[0] - hmin[0], wet))
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
