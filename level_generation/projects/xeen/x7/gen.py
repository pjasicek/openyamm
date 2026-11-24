#!/usr/bin/env python3
"""X7 Mount Firestone: writes the L2, L3 and L4 briefs from the approved L1 plan (A5, 2026-11-20; X6's gen.py the
model).

    gen.py [briefs folder]      (default devdocs/xeen/briefs/x7)

L1 is the MU-3 plan approved with changes by D-40 (gen_l1.py writes it; this script leaves it alone); L2 the
specification (the plan without the sketch); L3 the plan with the full sketch; L4 the same, built and installed
(ids.lock.yml beside it after a build). The land is land.py, the structures, actors and events places.py, the scatter
scatter.py; the spawn markers are placed here on walkable ground. Edit those and run ../vw.sh, never the YAML.

Switches (environment): X7_SOUTH_MARKERS (8 by A2's Act I count; 10 is L1's), X7_<KEY>_INSIDE=1 to wire a dungeon's
proposed named arrival (places.PROPOSED) once its lane has it.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
import math
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import gen_l1 as L1          # noqa: E402
import kit as K              # noqa: E402
import land as LD            # noqa: E402
import places as P           # noqa: E402
import scatter as SC         # noqa: E402

BRIEFS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(P.ROOT, 'devdocs/xeen/briefs/x7')


def units(c):
    return (c - 64) * 512


def neighbour_ground(stem, cell):
    """The installed neighbour's ground under a cell (its height map, 32 a unit)."""
    sys.path.insert(0, os.path.join(P.ROOT, 'util'))
    from map_export import parse_odm_file
    p = parse_odm_file(Path(P.WORLD) / 'maps' / stem)['payload']
    hm = p['height_map']
    i, j = cell
    return max(hm[j * 128 + i], hm[j * 128 + i + 1], hm[(j + 1) * 128 + i], hm[(j + 1) * 128 + i + 1]) * 32


# Where X7's edges land on its installed neighbours (degrees: east 0, north 90, west 180, south 270): X1's
# entrance:north_road [69, 21] facing south; X4's entrance:east_road [107, 66.5] facing west.
X1_ARRIVAL = (units(69), (64 - 21) * 512, neighbour_ground('xeen_x1.odm', (69, 21)), 270)
X4_ARRIVAL = (units(107), round((64 - 66.5) * 512), neighbour_ground('xeen_x4.odm', (107, 66)), 180)
# X7's own edge arrivals (what X1's north edge and X4's east edge send here)
X7_SOUTH_START = (units(69), (64 - 107) * 512, 90)    # entrance:south_road, facing north
X7_WEST_START = (units(21), (64 - 66) * 512, 0)       # entrance:west_road, facing east


def project():
    pr = copy.deepcopy(L1.PROJECT)
    neigh = []
    for n in pr['neighbours']:
        n = dict(n)
        if n['id'] == 'edge:south':
            n['span'] = [-32768, 32768]
            n['arrival'] = list(X1_ARRIVAL[:3])
            n['direction'] = X1_ARRIVAL[3]
            n['notes'] = ("X1 Vertigo Meadows (installed): the whole south edge leads to X1's north road at its "
                          "entrance:north_road [69, 21] = (%d, %d, %d) facing south (edge_spans, 5 days, as L1). X1's "
                          "north edge should arrive here at entrance:south_road (69, 107) = (%d, %d, about %d) facing "
                          "north (A5 reopens it, D-40 change 6)."
                          % (X1_ARRIVAL[0], X1_ARRIVAL[1], X1_ARRIVAL[2], X7_SOUTH_START[0], X7_SOUTH_START[1],
                             LD.q32(LD.raw_height(69, 107))))
        if n['id'] == 'edge:west':
            n['span'] = [-32768, 32768]
            n['arrival'] = list(X4_ARRIVAL[:3])
            n['direction'] = X4_ARRIVAL[3]
            n['notes'] = ("X4 Burlock Savannah (installed): the whole west edge leads to X4's Firestone road at its "
                          "entrance:east_road [107, 66.5] = (%d, %d, %d) facing west (edge_spans, 5 days, as L1). "
                          "X4's east edge should arrive here at entrance:west_road (21, 66) = (%d, %d, about %d) "
                          "facing east." % (X4_ARRIVAL[0], X4_ARRIVAL[1], X4_ARRIVAL[2], X7_WEST_START[0],
                                            X7_WEST_START[1], LD.q32(LD.raw_height(21, 66))))
        if n['id'].startswith('door:'):
            key = n['id'][5:]
            if key == 'xd17':
                n['condition'] = {'qbit': 'cleft_open'}
                n['notes'] = ("XD-17 Shangri-La (A5, phase 5; D-40 question 3): the valley's back gate, a cleft in "
                              'the black rock east of the Volcano Cave; a rockfall from this side until the party '
                              "leaves the valley once by its back passage (A3's xd17.cleft_opened sets cleft_open "
                              "116140); the door asks A3's xd17.cleft. Sealed until XD-17 exists.")
            if not (P.DUNGEON[key] and P.INSIDE[key]):
                n['listed_only'] = True
                n.pop('condition', None)
        neigh.append(n)
    pr['neighbours'] = neigh
    pr['qbits'] = dict(pr['qbits'], outpost_burned=116160, cleft_open=116140)
    pr['notes'] = ("X7 Mount Firestone (A5, 2026-11-20): a trap map. The south slopes (orcs, the abandoned dwarves' "
                   "watch, Sablewing's cave, the Shrine of Fire, the Well of Speed, XD-05's back gate), the Red Dwarf "
                   'Range and the Firestone Gap, the deadly north (the ash flats, the lava lake and its island, the '
                   'Volcano Cave and the cleft, the Dragon Cave, the Dragon Tower, Mount Firestone and the lava '
                   'cove). Built from the approved L1 with D-40. Written by output/studio_cal/x7/tools/gen.py; '
                   'NOTES.md in L4.')
    return pr


def plan(level):
    p = L1.plan()
    p['level'] = level
    p.pop('totals', None)
    for e in p['entrances']:
        if e.get('neighbour', '').startswith('door:'):
            key = e['neighbour'][5:]
            if key == 'xd17':
                e['condition'] = {'qbit': 'cleft_open'}
                e['how'] = ("Shangri-La's back gate (D-40 question 3): a cleft in the black rock; before the party "
                            'has left the valley that way, "Fallen rock chokes the cleft. Cool air, and a smell of '
                            'grass, seeps between the stones." (A3\'s xd17.cleft)')
            if not (P.DUNGEON[key] and P.INSIDE[key]):
                e.pop('neighbour')
                e.pop('condition', None)
                e['kind'] = 'both'
                e['how'] = e['how'] + ' Sealed with a line until the dungeon names its inside arrival (D-37).'
    # the build's start (a new game, the tests) is the first entrance: the X1 road
    p['entrances'] = ([e for e in p['entrances'] if e['id'] == 'entrance:south_road']
                      + [e for e in p['entrances'] if e['id'] != 'entrance:south_road'])
    for st in p.get('states') or []:
        if st['id'] == 'state:cleft_shut':
            st['condition'] = {'not': {'qbit': 'cleft_open'}}
            st['notes'] = ("D-40 question 3: opens from inside the first time the party leaves Shangri-La by its "
                           "back passage (xd17.cleft_opened, cleft_open 116140).")
            st.pop('locks', None)
        if st['id'] == 'state:xd05_barred':
            st.pop('locks', None)
    for poi in p['points_of_interest']:
        if poi['id'] == 'poi:signposts':
            poi['behaviour'] = ("Signposts at the forks: the Gap's carries D-40's warning (\"North: Mount Firestone. "
                                'Dragons. Turn back.") when clicked; the other two name their roads when clicked (D-40\'s 22 POIs).')
        if poi['id'] == 'poi:demon_idols':
            poi['behaviour'] += " One spot with XD-16's door (D-40 change 5; A3's x7.idols)."
        if poi['id'] == 'poi:outpost_chest':
            poi['behaviour'] += ' One spot with the outpost (D-40 change 5).'
        for key, lvl in (('poi:orc_outpost', None), ('poi:outpost_chest', 1), ('poi:orc_den', 1),
                         ('poi:watch_chest', 2), ('poi:miner_cache', 3), ('poi:knight_remains', 5),
                         ('poi:hydra_wallow', 5), ('poi:dragon_hoard', 6)):
            if poi['id'] == key and lvl:
                poi['behaviour'] += ' Treasure level %d (D-40 change 1).' % lvl
        if poi['id'] == 'poi:watch_chest':
            poi['behaviour'] += (' A note by it: "The dragons came south. Pay owed to the end of the month. Nobody '
                                 'stays." (D-40 question 8; A3\'s x7.watch_note)')
    p['notes'] = ('Written by output/studio_cal/x7/tools/gen.py from gen_l1.py (the approved L1 with D-40). Sealed '
                  'until their maps name an inside arrival: XD-05 (built; A7), XD-16, XD-18, FD-04 (A7), XD-17 (A5).')
    if level == 'L2':
        p.pop('sketch', None)
    return p


# ---------------------------------------------------------------- spawn markers on walkable ground
EDGE_ARRIVALS = {'entrance:south_road': (69.5, 107.5), 'entrance:west_road': (21.5, 66.5)}
DOOR_FRONTS = {'xd16': (66.0, 45.0), 'xd17': (73.0, 48.0), 'xd18': (56.5, 30.0), 'fd04': (29.0, 31.6),
               'xd05': (87.6, 100.0)}
CLEFT_AT = P.CLEFT_ARRIVAL
DRAGON_KEEP = [LD.NORTH_TRACK, [list(DOOR_FRONTS['xd18'])], [list(DOOR_FRONTS['xd16'])]]


def walkable(x, y):
    if LD.in_void(x, y) or min(LD.RIM_X - x, y - LD.RIM_Y) < 1.6 or K.edge_dist((x, y), LD.COVE) < 1.6:
        return False
    if K.inside((x, y), LD.LAKE) or K.edge_dist((x, y), LD.LAKE) < 1.2 or K.inside((x, y), LD.ISLAND):
        return False
    if K.inside((x, y), LD.CRATER) or LD.dist_to_line(x, y, LD.RIVER) < 1.8 or LD.dist_to_line(x, y, LD.ARM) < 1.5:
        return False
    if math.hypot(x - LD.TOWER_CRAG[0], y - LD.TOWER_CRAG[1]) < LD.TOWER_CRAG[2] + 2:
        return False
    hs = [LD.raw_height(x + dx, y + dy) for dx in (-0.5, 0.5) for dy in (-0.5, 0.5)]
    return max(hs) - min(hs) <= 300                 # the engine slides over 512 a tile: keep a margin


def dline(x, y, line):
    return LD.dist_to_line(x, y, line) if len(line) > 1 else math.hypot(x - line[0][0], y - line[0][1])


def markers():
    clear = [poly for _aid, poly, _n in L1.KEEP_CLEAR]
    roads = [ln for _l, ln, _w, _s in L1.ROADS] + [ln for ln, _p, _h, _b in LD.PROFILED]
    out = []
    south = []
    for pid, slot, count, poly, note in L1.AREAS:
        xs = [q[0] for q in poly]
        ys = [q[1] for q in poly]
        cand = []
        y = math.floor(min(ys))
        while y < max(ys):
            x = math.floor(min(xs))
            while x < max(xs):
                p = (x, y)
                ok = (K.inside(p, poly) and K.edge_dist(p, poly) > 0.6
                      and (walkable(x, y) if slot != 3 else
                           (not LD.in_void(x, y) and min(LD.RIM_X - x, y - LD.RIM_Y) > 1.6
                            and not K.inside(p, LD.CRATER) and LD.dist_to_line(x, y, LD.RIVER) > 1.5
                            and LD.dist_to_line(x, y, LD.ARM) > 1.5))
                      and not any(K.inside(p, c) for c in clear)
                      and min(math.hypot(x - d[0], y - d[1]) for d in DOOR_FRONTS.values()) > 4.0
                      and math.hypot(x - CLEFT_AT[0], y - CLEFT_AT[1]) > 4.8          # D-40: 2,000 from the cleft
                      and all(math.hypot(x - a[0], y - a[1]) > 4.4 for a in EDGE_ARRIVALS.values())
                      and min(LD.dist_to_line(x, y, r) for r in roads) > 0.8)
                if ok and slot == 3:   # D-40: dragons 4,000 from the cleft, 6,000 from the tax track and the caves
                    ok = (math.hypot(x - CLEFT_AT[0], y - CLEFT_AT[1]) > 7.9
                          and min(dline(x, y, ln) for ln in DRAGON_KEEP) > 11.8)
                if ok:
                    cand.append(p)
                x += 1
            y += 1
        want = count
        if len(cand) < want:
            raise SystemExit('%s: only %d places for %d markers' % (pid, len(cand), want))
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        start = min(cand, key=lambda q: math.hypot(q[0] - cx, q[1] - cy))
        for a in EDGE_ARRIVALS.values():
            near = min(cand, key=lambda q: math.hypot(q[0] - a[0], q[1] - a[1]))
            if math.hypot(near[0] - a[0], near[1] - a[1]) < 11:
                start = near
        seeds = [start]
        n_seeds = (want + 1) // 2 + (want // 6)
        if slot == 1:   # F10: the south's small orc bands (1-2 each) spread one by one, no pairs
            n_seeds = want
        while len(seeds) < n_seeds:
            seeds.append(max(cand, key=lambda q: min(math.hypot(q[0] - c[0], q[1] - c[1]) for c in seeds)))
        chosen = list(seeds)
        k = 0
        while len(chosen) < want and k < 4 * want:
            sx, sy = seeds[k % len(seeds)]
            k += 1
            near = [q for q in cand if 2.0 <= math.hypot(q[0] - sx, q[1] - sy) <= 3.2 and q not in chosen
                    and min(math.hypot(q[0] - c[0], q[1] - c[1]) for c in chosen) >= 2.0]
            if near:
                chosen.append(min(near, key=lambda q: (q[0] * 7 + q[1] * 13) % 11))
        while len(chosen) < want:
            chosen.append(max(cand, key=lambda q: min(math.hypot(q[0] - c[0], q[1] - c[1]) for c in chosen)))
        for (x, y) in chosen:
            m = {'id': pid, 'slot': slot, 'at': (x, y), 'note': note}
            (south if slot == 1 else out).append(m)
    # D-40 change 2 and A2's count: the south from L1's 10 markers to SOUTH_MARKERS, the farthest from the arrivals go
    farthest = sorted(south, key=lambda m: min(math.hypot(m['at'][0] - a[0], m['at'][1] - a[1])
                                               for a in EDGE_ARRIVALS.values()))
    south = farthest[:P.SOUTH_MARKERS]
    res = []
    idx = {}
    for m in out + south:
        idx[m['id']] = idx.get(m['id'], 0) + 1
        k = idx[m['id']]
        res.append({'id': m['id'], 'index': k, 'count': 1, 'slot': m['slot'],
                    'circle': {'at': [int(m['at'][0]), int(m['at'][1])], 'r': 1},
                    'notes': m['note'] if k == 1 else 'walkable ground'})
    for aid, poly, note in L1.KEEP_CLEAR:
        a = {'id': aid, 'kind': 'keep_clear', 'polygon': poly}
        if note:
            a['notes'] = note
        res.append(a)
    for aid, poly, note in L1.OPEN:
        res.append({'id': aid, 'kind': 'open', 'polygon': poly, 'notes': note})
    return res


MOVED = {  # points the L3 detail moved (cells; facing)
    'entrance:xd16_mouth': ([65, 45], 'w'),
    'entrance:xd17_cleft': ([72, 48], 'w'),
    'entrance:xd18_mouth': ([56, 31], 's'),
    'entrance:fd04_door': ([29, 32], 's'),
    'entrance:xd05_gate': ([87, 100], 'w'),
    'poi:demon_idols': ([65, 44], None),
    'poi:shrine_fire': ([52, 98], None),
    'poi:well_speed': ([28, 102], None),
    'poi:fire_reflector': ([101, 26], None),
    'poi:hot_spring': ([94, 84], None),
    'poi:sablewing': ([75, 90], None),
    'poi:watch_chest': ([68, 85], None),
    'poi:outpost_chest': ([31, 86], None),
    'poi:orc_den': ([83, 102], None),
    'poi:miner_cache': ([44, 69], None),
    'poi:knight_remains': ([59, 36], None),
    'poi:dragon_hoard': ([97, 46], None),
    'poi:hydra_wallow': ([41, 54], None),
    'landmark:lava_falls': ([73, 29], None),
}
SIGNPOST_AT = [P.GAP_SIGN, P.FORK_SIGN, P.SLOPE_SIGN]


def sketch():
    s = L1.sketch()
    s['heights'] = LD.heights()
    s['water'] = LD.water()
    s['roads'] = LD.roads()
    s['ground'] = LD.ground()
    for d in s['districts']:
        if d['space'] == 'zone:rim':
            d['polygon'] = [list(p) for p in LD.RIM_SEA_POLY]
    for b in s['heights'].get('bands') or []:
        pass
    pts = []
    for q in s['points']:
        q = dict(q)
        if q['id'] in MOVED:
            q['at'], f = MOVED[q['id']]
            if f:
                q['facing'] = f
        if q['id'] == 'poi:signposts':
            q['at'] = [int(a) for a in SIGNPOST_AT[q['index'] - 1]]
        pts.append(q)
    s['points'] = pts
    s['areas'] = markers()
    s['structures'] = P.structures()
    s['actors'] = P.actors()
    if P.LAVAFALL_LIVE:   # AU (2026-11-21): one looping point source over the three lava falls (panned, D-48)
        mid = P.LAVAFALLS[len(P.LAVAFALLS) // 2]
        s['sounds'] = [{'id': 'sound:lavafalls', 'at': list(mid), 'sound': 'xeen_lavafall_loop', 'radius': 4500,
                        'inner_radius': 1800, 'volume': 0.6, 'loop': True}]
    s['events'] = P.events()
    s['scatter'] = SC.scatter()
    # D-90 (A5 s30, merge point 42): Q-C14's Ever-Hot Lava Rock on the ground of the cooled-flow island
    s['items'] = [{'id': 'item:lava_rock', 'item': 12314, 'at': list(P.LAVA_ROCK)}]
    s['notes'] = ('X7 Mount Firestone, L3/L4 sketch (A5, 2026-11-20), written by output/studio_cal/x7/tools/gen.py. '
                  'Cells [x, y], x east, y south. Heights above the stars below the rims (0): the lava lake 1,500, '
                  'the south slopes 1,650-2,300, the Red Dwarf Range to 3,200 with the Firestone Gap at 2,300, the '
                  'ash flats 2,000-2,250, Mount Firestone to 4,900 (its crater pool 4,600). Lava is the lava tile '
                  'set (D-40 change 3).')
    return s


def dump(folder, name, data):
    if name == 'sketch.yml':   # AU's outdoor beds (A5, 2026-11-21; level_generation/projects/xeen/common/beds): X7's volcano and wind
        sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common/beds')
        import beds as _beds
        data = _beds.with_beds(data, 'x7')
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, name), 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)


ATMOSPHERE = {
    'format': 0, 'sky_theme': 'ashen', 'weather': {}, 'ash': 40,
    'notes': "D-40 question 9: the world default sky (Cloudside's fair preset) with the ashen theme (A6's world sky.yml "
             'maps xeen_x7.odm to it); no rain or snow; ash fall on 40 % of days (`ash`, A1\'s word, written into the '
             "scene's weather as ash_chance).",
}


def main():
    pr = project()
    sk = sketch()
    # F2/F8 (2026-11-21) + D-91/F16 (A5 s29, 2026-11-22): wing doors as double doors, cave mouths as wide as their rim
    # (the shelters and the blocked adit say their own form: no click line to nowhere), the entrance window's lines
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common')
    import house_doors as HD
    import entrance as EN
    for _note in HD.double_doors_sketch(sk) + HD.bury_mouths_sketch(sk) + EN.apply(sk, 'x7'):
        print('door:', _note)
    # P2 feedback F29/F32/F33 (agent xeen-fb2-wild, 2026-11-23): shrine altars, campfires, the rim fall
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'common'))
    import wild as WILD
    for _note in WILD.apply(sk, 'x7'):
        print('wild:', _note)
    # The classic Clouds kit (2026-11-24): Clouds of Xeen's own half-timbered walls on the map's houses
    import classic_kit as CK
    for _note in CK.apply(sk, 'x7'):
        print(_note)
    for level in ('L2', 'L3', 'L4'):
        out = os.path.join(BRIEFS, level)
        dump(out, 'project.yml', pr)
        dump(out, 'plan.yml', plan('L3' if level == 'L4' else level))
        if level != 'L2':
            dump(out, 'sketch.yml', sk)
            dump(out, 'atmosphere.yml', ATMOSPHERE)
    n = sum(1 for a in sk['areas'] if 'slot' in a)
    print('structures', len(sk['structures']), 'actors', len(sk['actors']), 'scatter', len(sk['scatter']),
          'markers', n, 'south', sum(1 for a in sk['areas'] if a.get('slot') == 1),
          'lava falls', 'placed' if P.LAVAFALL_LIVE else 'off (S)', [P.fall_turn(a) for a in P.LAVAFALLS])
    print('X1 arrival', X1_ARRIVAL, 'X4 arrival', X4_ARRIVAL)
    print('hooks used', sorted(P.USED))


if __name__ == '__main__':
    main()
