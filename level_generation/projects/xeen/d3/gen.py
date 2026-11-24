#!/usr/bin/env python3
"""D3 Sandcaster and the Aging Forest: writes the L2, L3 and L4 briefs from the approved L1 plan (A5, 2026-11-20,
seventh session; X4's gen.py the model).

    gen.py [briefs folder]      (default devdocs/xeen/briefs/d3)

L1 is the MU-3 plan with D-28 (gen_l1.py writes it; run.sh draws it); L2 the specification (the plan without the
sketch); L3 the plan with the full sketch; L4 the same, built and installed (ids.lock.yml beside it after a build). The
land is land.py, the plots, structures, actors and events places.py, the scatter scatter.py; the spawn markers are
placed here on walkable ground (D-28: mantis markers on the shoulders). Edit those and run ../vw.sh, never the YAML.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
import math
import os
import sys
sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import villagers as V  # noqa: E402  D-96 (A4, F20): each settlement's street villagers, source/towns/villagers.yml

import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import gen_l1 as L1          # noqa: E402
import kit as K              # noqa: E402
import land as LD            # noqa: E402
import places as P           # noqa: E402
import scatter as SC         # noqa: E402

BRIEFS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(P.ROOT, 'devdocs/xeen/briefs/d3')

# the D4 crossing (D-28 (6)): D4 continues these north-edge spans and heights (units along the edge, x for north)
NORTH_SPANS = [([0, 24], 'ridge', '2,600-3,400', 'the last Gemstone crags'),
               ([24, 82], 'ridge', '1,500-2,000', 'dunes of the desert edge'),
               ([82, 94], 'level', '1,750', "the Lakeside road (the crossing at x 88, the road's bed 1,760)"),
               ([94, 104], 'ridge', '1,900-2,400', "the Wrath crest's north shoulder"),
               ([104, 128], 'level', '0', 'the rim: the land ends in the east cliff')]


D2_ARRIVAL = (21504, 10240, 1312, 180)   # D2's east start (106, 44), facing west (degrees; A6, 2026-11-20)
D7_FALL = [34, 41]   # D-58: D7's E3-F4 fall lands here, (-15360, 11776, 1440) facing east (Xeen.SkyFalls.d7_ef34)
D3_WEST_START = (-22528, 10240, 1312, 0)  # D3's entrance:west_road (20, 44), facing east: D2's east edge lands here


def units(c):
    return (c - 64) * 512


def project():
    pr = copy.deepcopy(L1.PROJECT)
    neigh = []
    for n in pr['neighbours']:
        n = dict(n)
        if n['kind'] in ('stable', 'boat'):
            n['listed_only'] = True
        if n['id'] == 'edge:west':
            # A6 (2026-11-20): D2's east-edge arrival; the whole west edge leads there (edge_spans, as X3's north)
            n['span'] = [-32768, 32768]
            n['arrival'] = list(D2_ARRIVAL[:3])
            n['direction'] = D2_ARRIVAL[3]
            n['notes'] = ("D2 Sprite Forest and Ogre Pass (installed): D3's west edge arrives at D2's east start (106, 44) "
                          "= (21504, 10240, about 1,300) facing west; D2's east edge arrives here at entrance:west_road "
                          "(20, 44) = (-22528, 10240, 1312) facing east. A2 writes the travel row once both are "
                          "installed; D2 opens its east road (D2_D3_LIVE) at its next install (A6).")
        if n['id'] == 'edge:north':
            spans = '; '.join('x %d-%d (%d to %d) %s %s: %s' % (a, b, units(a), units(b), form, h, what)
                              for (a, b), form, h, what in NORTH_SPANS)
            n['notes'] = ("D4 Lakeside and Blackfang (phase 4, not built): sealed by a sign at the road's end until D4 "
                          "is installed. D-28 (6): the crossing at x 88 (units 12288), the Lakeside road east of the "
                          "River of Wrath; D4 continues D3's north-edge spans and heights: " + spans + '.')
            if not P.D4_LIVE:
                n['listed_only'] = True
            else:
                # tenth session: D4 installed (A6, 21:09); A2's travel rows: D3 north -> D4 'down' 7 days, D4 south ->
                # D3 'up' 7 days (D4's entrance:south_road and D3's entrance:north_road are those sides' starts)
                n['days'] = 7
                n['notes'] = ("D4 Lakeside and Blackfang (installed): the whole north edge leads to D4's south start "
                              "entrance:south_road (88, 105) = (12288, -20992) facing north; D4's south edge lands "
                              "at D3's entrance:north_road (88, 20) = (12288, 22528, 1760) facing south (A2's travel "
                              "rows, 7 days each way). D-28 (6): the crossing at x 88 (units 12288); D4 continues "
                              "D3's north-edge spans and heights: " + spans + '.')
        if n['id'].startswith('door:dd'):
            key = n['id'][5:]
            if not (P.DUNGEON[key] and P.INSIDE[key]):
                n['listed_only'] = True
                n.pop('condition', None)
            else:   # live: the sealed sentence of the L1 note no longer holds
                n['notes'] = n['notes'].replace(' Sealed with a line after the hook until %s is installed.'
                                                % ('DD-' + key[2:]), '')
        neigh.append(n)
    pr['neighbours'] = neigh
    pr['rules'] = {'weather': 'none', 'respawn': 'entrance:sandcaster_square',
                   'town_portal_anchor': 'entrance:sandcaster_square'}
    pr['notes'] = ("D3 Sandcaster and the Aging Forest (A5, 2026-11-20): Sandcaster on its terrace with the wizard "
                   "quarter, the Crossroads, the Aging Forest, the Howling ridge, the River of Wrath from its gorge to "
                   "the falls over the rim, the Wrath crest, Venom Pond. Built from the approved L1 with D-28. "
                   "Written by output/studio_cal/d3/tools/gen.py; NOTES.md in L4.")
    return pr


def plan(level):
    p = L1.plan()
    p['level'] = level
    p.pop('totals', None)
    for e in p['entrances']:
        if e['id'] == 'entrance:sandcaster_stables':
            e.pop('neighbours', None)
            e['how'] = "The caravans (A4's routes 416, 417) arrive in the fenced yard outside the south gate (D-28)."
        if e.get('neighbour', '').startswith('door:dd'):
            key = e['neighbour'][5:]
            if not (P.DUNGEON[key] and P.INSIDE[key]):
                e.pop('neighbour')
                e.pop('condition', None)
                e['kind'] = 'both'
                e['how'] = e['how'] + ' Sealed with a line until the dungeon is installed and its inside point given.'
        if e['id'] == 'entrance:north_road' and not P.D4_LIVE:
            e['how'] = ("The Lakeside road from D4 (not built: the road ends at a sign; the crossing at x 88, D-28).")
    p['links'] += [
        {'id': 'link:gate_street', 'from': 'zone:sc_main_street', 'to': 'zone:sc_square', 'kind': 'road',
         'notes': 'From the south gate to the square (sandstone setts).'},
        {'id': 'link:bazaar_street', 'from': 'zone:sc_square', 'to': 'zone:sc_east_street', 'kind': 'road',
         'notes': 'From the square to the east gate.'},
        {'id': 'link:west_lane', 'from': 'zone:sc_west_lane', 'to': 'zone:sc_square', 'kind': 'path',
         'notes': "Past the temple and Barticus' Gym."},
        {'id': 'link:guild_row', 'from': 'zone:sc_north_street', 'to': 'zone:sc_square', 'kind': 'path',
         'notes': 'Along the guilds to the quarter.'}]
    # D-58: the landing of D7's E3-F4 fall zone (A3's Xeen.SkyFalls.d7_ef34), confirmed at install (D-54's checks).
    # Kind `both` with no neighbour (as the sealed dungeon doors): the build's start is the plan's first entrance of kind
    # `arrival` in id order after fmt, and as an arrival d7_fall would sort before sandcaster_square and take the start.
    p['entrances'].append(
        {'id': 'entrance:d7_fall', 'space': 'zone:caravan_yard', 'kind': 'both',
         'how': "A fall from D7, the Skyroads' E3-F4 zone (D-58; Xeen.skyFallTo(\"d7_ef34\"), with falling damage): "
                "on the whole cell outside Sandcaster's south gate, facing east; no ranged hostile within 5,888 (D-54)."})
    # the build's start (a new game, the tests) is the plan's first arrival (oymap fmt sorts entrances by id): the square
    p['entrances'] = ([e for e in p['entrances'] if e['id'] != 'entrance:sandcaster_square']
                      + [e for e in p['entrances'] if e['id'] == 'entrance:sandcaster_square'])
    p['notes'] = ('Written by output/studio_cal/d3/tools/gen.py from gen_l1.py (the approved L1 with D-28). Sealed '
                  'until their maps exist: D4 (north edge), DD-18, DD-19, DD-07.')
    if level == 'L2':
        p.pop('sketch', None)
    return p


# ---------------------------------------------------------------- spawn markers on walkable ground
EDGE_ARRIVALS = {'entrance:west_road': (20.5, 44.5), 'entrance:north_road': (88.5, 20.5)}


KNOBS = [at for at, h, _n in LD.POINTS if h >= 2300] + [at for at, _h in LD.SPIRE_AT + LD.RIDGE_SPIRES]   # steeper than the grid


def walkable(x, y):
    if any(math.hypot(x - a[0], y - a[1]) < 3.2 for a in KNOBS):
        return False
    if any(LD.dist_to_line(x, y, c['line']) < 2.0 for c in LD.CREST_SHELVES):    # the crest's shelves
        return False
    hs = [LD.raw_height(x + dx, y + dy) for dx in (-0.5, 0.5) for dy in (-0.5, 0.5)]
    if max(hs) - min(hs) > 300:                    # the engine slides over 512 a tile: keep a margin
        return False
    if min(hs) < LD.POND_LVL + 60:
        return False
    if LD.dist_to_line(x, y, LD.RIVER_LINE) < 2.6 or K.edge_dist((x, y), LD.POND) < 1.5 or K.inside((x, y), LD.POND):
        return False
    return x < LD.RIM_X - 1.5 and y < LD.RIM_Y - 1.5

# D-85 (s26): no hostile marker within 5,888 (missile range 5,120 + 768) of an outdoor talking quest giver. The markers
# of these areas that the sampling puts nearer than 12.5 cells (5,888 + the circle's 512) move to the nearest free
# candidate beyond it; the area's other markers and every other area keep their places.
GIVER_CLEAR = {'pop:howling_woods': [(40.2, 72.2)]}   # Cornelius (5247)
GIVER_CELLS = 12.5


def clear_givers(pid, chosen, cand):
    givers = GIVER_CLEAR.get(pid, [])
    far = lambda q: min([math.hypot(q[0] - g[0], q[1] - g[1]) for g in givers] or [1e9])
    for i, q in enumerate(chosen):
        if far(q) >= GIVER_CELLS:
            continue
        others = chosen[:i] + chosen[i + 1:]
        ok = [c for c in cand if c not in chosen and far(c) >= GIVER_CELLS
              and min(math.hypot(c[0] - o[0], c[1] - o[1]) for o in others) >= 2.0]
        if not ok:
            raise SystemExit('%s: no place for marker %d beyond %.1f cells of the giver' % (pid, i + 1, GIVER_CELLS))
        chosen[i] = min(ok, key=lambda c: (math.hypot(c[0] - q[0], c[1] - q[1]), c))
        print('D-85: %s marker %d %s -> %s' % (pid, i + 1, q, chosen[i]))
    return chosen


# F10 (A5 s30): areas whose markers stand at fixed cells (gen_l1.AREAS pop:outside_walls, pop:forest_edge)
FIXED_SPOTS = {'pop:outside_walls': [(21, 24), (46, 49)], 'pop:forest_edge': [(70, 63)]}


def markers():
    clear = [poly for _aid, poly, _n in L1.KEEP_CLEAR]
    door_pts = [d[2] for d in P.doors]
    roads = [ln for _l, ln, _w, _s in L1.ROADS]
    out = []
    for pid, slot, count, poly, note in L1.AREAS:
        if pid in FIXED_SPOTS:
            spots = FIXED_SPOTS[pid]
            assert len(spots) == count and all(walkable(x, y) and K.inside((x, y), poly) for x, y in spots), pid
            for k, (x, y) in enumerate(spots, 1):
                out.append({'id': pid, 'index': k, 'count': 1, 'slot': slot, 'circle': {'at': [x, y], 'r': 1},
                            'notes': note if k == 1 else 'walkable ground (F10)'})
            continue
        xs = [q[0] for q in poly]
        ys = [q[1] for q in poly]
        cand = []
        y = math.floor(min(ys))
        while y < max(ys):
            x = math.floor(min(xs))
            while x < max(xs):
                p = (x, y)
                if (K.inside(p, poly) and K.edge_dist(p, poly) > 0.6 and walkable(x, y)
                        and not any(K.inside(p, c) for c in clear)
                        and min(math.hypot(x - d[0], y - d[1]) for d in door_pts) > 5.2
                        and all(math.hypot(x - a[0], y - a[1]) > 4.4 for a in EDGE_ARRIVALS.values())
                        and min(LD.dist_to_line(x, y, r) for r in roads) > 0.8):
                    cand.append(p)
                x += 1
            y += 1
        if len(cand) < count:
            raise SystemExit('%s: only %d walkable places for %d markers' % (pid, len(cand), count))
        # farthest-point sampling from the place nearest an edge arrival (its first fight), else the centroid
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        start = min(cand, key=lambda q: math.hypot(q[0] - cx, q[1] - cy))
        for a in EDGE_ARRIVALS.values():
            near = min(cand, key=lambda q: math.hypot(q[0] - a[0], q[1] - a[1]))
            if math.hypot(near[0] - a[0], near[1] - a[1]) < 11:
                start = near
        # seeds spread by farthest-point sampling, about half of them with a second group 2-3 cells off (the shipped
        # maps' groups cluster: town_feel's group-to-group median and spacing variation)
        seeds = [start]
        n_seeds = (count + 1) // 2 + (count // 6)
        while len(seeds) < n_seeds:
            seeds.append(max(cand, key=lambda q: min(math.hypot(q[0] - c[0], q[1] - c[1]) for c in seeds)))
        chosen = list(seeds)
        k = 0
        while len(chosen) < count and k < 4 * count:
            sx, sy = seeds[k % len(seeds)]
            k += 1
            near = [q for q in cand if 2.0 <= math.hypot(q[0] - sx, q[1] - sy) <= 3.2 and q not in chosen
                    and min(math.hypot(q[0] - c[0], q[1] - c[1]) for c in chosen) >= 2.0]
            if near:
                chosen.append(min(near, key=lambda q: (q[0] * 7 + q[1] * 13) % 11))
        while len(chosen) < count:
            chosen.append(max(cand, key=lambda q: min(math.hypot(q[0] - c[0], q[1] - c[1]) for c in chosen)))
        chosen = clear_givers(pid, chosen, cand)
        for k, (x, y) in enumerate(chosen, 1):
            out.append({'id': pid, 'index': k, 'count': 1, 'slot': slot, 'circle': {'at': [int(x), int(y)], 'r': 1},
                        'notes': note if k == 1 else 'walkable ground (D-28)'})
    for aid, poly, note in L1.KEEP_CLEAR:
        a = {'id': aid, 'kind': 'keep_clear', 'polygon': poly}
        if note:
            a['notes'] = note
        out.append(a)
    for aid, poly, note in L1.OPEN:
        out.append({'id': aid, 'kind': 'open', 'polygon': poly, 'notes': note})
    return out


def sketch():
    s = L1.sketch()
    s['heights'] = LD.heights()
    s['water'] = LD.water()
    s['roads'] = LD.roads()
    s['ground'] = LD.ground()
    for d in s['districts']:
        if d['space'] in P.plots_by_space:
            d['plots'] = P.plots_by_space[d['space']]
        elif 'plots' in d:
            d.pop('plots')
    moved = {'entrance:sandcaster_stables': ([int(P.YARD_ARRIVAL[0]), int(P.YARD_ARRIVAL[1])], 'n'),
             'entrance:dd18_shaft': ([int(P.DD18_SHAFT[0]), int(P.DD18_SHAFT[1])], None),
             'entrance:dd19_gate': ([43, 21], 'n'), 'entrance:dd07_door': ([94, 46], 'w'),
             'entrance:sandcaster_square': ([36, 30], 's'), 'poi:great_oak': ([53, 65], None)}
    pts = []
    for q in s['points']:
        q = dict(q)
        if q['id'] in moved:
            q['at'], f = moved[q['id']]
            if f:
                q['facing'] = f
        pts.append(q)
    pts.append({'id': 'entrance:d7_fall', 'at': D7_FALL, 'facing': 'e'})
    s['points'] = pts
    s['areas'] = markers()
    s['structures'] = P.structures()
    s['actors'] = V.fill(P.actors(), 'D3')   # D-96: Sandcaster's and the Crossroads' villagers
    s['relations'] = (s.get('relations') or []) + V.relations('D3')
    s['events'] = P.events()
    s['scatter'] = SC.scatter()
    s['notes'] = ('D3 Sandcaster and the Aging Forest, L3/L4 sketch (A5, 2026-11-20), written by '
                  'output/studio_cal/d3/tools/gen.py. Cells [x, y], x east, y south. Heights above the stars below the '
                  'rim (0): Venom Pond 864, the River of Wrath 992, the forest and fen 900-1,200, the Crossroads 1,248, '
                  "Sandcaster's terrace 1,504 (the quarter 1,728), the Howling ridge to 2,200, the west-bank hills "
                  '2,400, the Wrath crest to 3,400 (D-28).')
    return s


def dump(folder, name, data):
    if name == 'sketch.yml':   # AU's outdoor beds (A5, 2026-11-21; level_generation/projects/xeen/common/beds)
        sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common/beds')
        import beds as _beds
        data = _beds.with_beds(data, 'd3')
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, name), 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)


def main():
    L1.main()
    pr = project()
    sk = sketch()
    # F2/F8 (2026-11-21): wing doors as double doors, cave mouths as wide as their rim; F16 (A5 s29): the entrance
    # window's trans.txt lines
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common')
    import house_doors as HD
    import entrance as EN
    for _note in HD.double_doors_sketch(sk) + HD.bury_mouths_sketch(sk) + HD.blind_mouths_sketch(sk) + EN.apply(sk, 'd3'):
        print('door:', _note)
    # P2 feedback F29/F32/F33 (agent xeen-fb2-wild, 2026-11-23): shrine altars, campfires, the rim fall
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'common'))
    import wild as WILD
    for _note in WILD.apply(sk, 'd3'):
        print('wild:', _note)
    # The classic kits (2026-11-24): Clouds of Xeen's own walls on the map's buildings (classic_kit.yml)
    import classic_kit as CK
    for _note in CK.apply(sk, 'd3'):
        print(_note)
    atmos = {'format': 0, 'sky': 'xeendark1', 'weather': {},
             'notes': "Darkside's amber day (xeendark1; A3's Lua switches xeendark2/3 by the sun's stage on load, "
                      'evt:sky). No weather. The bright face\'s glow above the east rim: asked of A6 (the preset has '
                      'no directional band).'}
    for level in ('L2', 'L3', 'L4'):
        out = os.path.join(BRIEFS, level)
        dump(out, 'project.yml', pr)
        dump(out, 'plan.yml', plan('L3' if level == 'L4' else level))
        if level != 'L2':
            dump(out, 'sketch.yml', sk)
            dump(out, 'atmosphere.yml', atmos)
    print('plots', sum(len(v) for v in P.plots_by_space.values()), 'structures', len(sk['structures']),
          'actors', len(sk['actors']), 'scatter', len(sk['scatter']), 'markers',
          sum(1 for a in sk['areas'] if 'slot' in a))
    print('hooks used', sorted(P.USED))
    print('missing', sorted(P.MISSING))


if __name__ == '__main__':
    main()
