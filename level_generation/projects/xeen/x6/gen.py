#!/usr/bin/env python3
"""X6 Desert of the Sphinx: writes the L2, L3 and L4 briefs from the approved L1 plan (A5, 2026-11-20; D3's gen.py
the model).

    gen.py [briefs folder]      (default devdocs/xeen/briefs/x6)

L1 is the MU-3 plan approved by D-31 (gen_l1.py writes it; this script leaves it alone); L2 the specification (the
plan without the sketch); L3 the plan with the full sketch; L4 the same, built and installed (ids.lock.yml beside it
after a build). The land is land.py, the plots, structures, actors and events places.py, the scatter scatter.py; the
spawn markers are placed here on walkable ground. Edit those and run ../vw.sh, never the YAML.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
import math
import os
import sys
sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import villagers as V  # noqa: E402  D-96 (A4, F20): each settlement's street villagers, source/towns/villagers.yml
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import gen_l1 as L1          # noqa: E402
import kit as K              # noqa: E402
import land as LD            # noqa: E402
import places as P           # noqa: E402
import scatter as SC         # noqa: E402

BRIEFS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(P.ROOT, 'devdocs/xeen/briefs/x6')


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


# Where X6's edges land on its installed neighbours (proposed to their owners; their edges open when they add the
# matching arrival into X6): X4's west road just inside its x 20 (its sign at [19.8, 59.2] goes), facing east; X5's
# steppe road just inside its y 20, facing south.
X4_ARRIVAL = (units(20), (64 - 60) * 512, neighbour_ground('xeen_x4.odm', (20, 60)), 0)       # degrees: east
X5_ARRIVAL = (units(50), (64 - 20) * 512, neighbour_ground('xeen_x5.odm', (50, 20)), 270)     # degrees: south
# X6's own edge arrivals (what X4's west edge and X5's north edge send here)
X6_EAST_START = (units(107), (64 - 60) * 512, None, 180)    # entrance:east_road, facing west
X6_SOUTH_START = (units(50), (64 - 107) * 512, None, 90)    # entrance:south_road, facing north


def project():
    pr = copy.deepcopy(L1.PROJECT)
    neigh = []
    for n in pr['neighbours']:
        n = dict(n)
        if n['kind'] in ('stable', 'boat'):
            n['listed_only'] = True
        if n['kind'] == 'edge':
            n['days'] = 7          # A2's travel rows and edge_spans: wilderness edges are 7 days (A6, 2026-11-20)
        if n['id'] == 'edge:east':
            n['span'] = [-32768, 32768]
            n['arrival'] = list(X4_ARRIVAL[:3])
            n['direction'] = X4_ARRIVAL[3]
            n['notes'] = ("X4 Burlock Savannah (installed): the whole east edge leads to X4's west road at its x 20 "
                          "(%d, %d, %d) facing east (edge_spans, 7 days). X4's west edge arrives here at "
                          "entrance:east_road (107, 60) = (%d, %d, about %d) facing west (open since 2026-11-20)."
                          % (X4_ARRIVAL[0], X4_ARRIVAL[1], X4_ARRIVAL[2], X6_EAST_START[0], X6_EAST_START[1],
                             LD.q32(LD.raw_height(107, 60))))
        if n['id'] == 'edge:south':
            n['span'] = [-32768, 32768]
            n['arrival'] = list(X5_ARRIVAL[:3])
            n['direction'] = X5_ARRIVAL[3]
            n['notes'] = ("X5 Winterkill Tundra (installed): the whole south edge leads to X5's steppe road at its y 20 "
                          "(%d, %d, %d) facing south (edge_spans, 7 days). X5's north edge arrives here at "
                          "entrance:south_road (50, 107) = (%d, %d, about %d) facing north (A6, 19:56)."
                          % (X5_ARRIVAL[0], X5_ARRIVAL[1], X5_ARRIVAL[2], X6_SOUTH_START[0], X6_SOUTH_START[1],
                             LD.q32(LD.raw_height(50, 107))))
        if n['id'].startswith('door:'):
            key = n['id'][5:]
            if not (P.DUNGEON[key] and P.INSIDE[key]):
                n['listed_only'] = True
                n.pop('condition', None)
        neigh.append(n)
    pr['neighbours'] = neigh
    pr['rules'] = dict(pr['rules'], respawn='entrance:sphinx_wells')
    pr['notes'] = ("X6 Desert of the Sphinx (A5, 2026-11-20): Sphinx Wells on the pan, the oasis, the Northern Sphinx "
                   "in the dunes, Castle Basenji on its crag at the north rim, the rim dunes and the Southern Sphinx, "
                   "the Warzone coach yard against the Barbaric cliffs. Built from the approved L1 with D-31. Written "
                   "by output/studio_cal/x6/tools/gen.py; NOTES.md in L4.")
    return pr


def plan(level):
    p = L1.plan()
    p['level'] = level
    p.pop('totals', None)
    for e in p['entrances']:
        if e['id'] in ('entrance:sphinx_wells', 'entrance:warzone_coach'):
            e.pop('neighbours', None)
        if e.get('neighbour', '').startswith('door:'):
            key = e['neighbour'][5:]
            if not (P.DUNGEON[key] and P.INSIDE[key]):
                e.pop('neighbour')
                e.pop('condition', None)
                e['kind'] = 'both'
                e['how'] = e['how'] + ' Sealed with a line until the dungeon is installed and its inside point given.'
    # the build's start (a new game, the tests) is the last arrival: Sphinx Wells
    p['entrances'] = ([e for e in p['entrances'] if e['id'] != 'entrance:sphinx_wells']
                      + [e for e in p['entrances'] if e['id'] == 'entrance:sphinx_wells'])
    for poi in p['points_of_interest']:
        if poi['id'] == 'poi:signposts':
            poi['behaviour'] = 'Signposts at the forks: arms only (not POIs by D-20).'
    p['spaces'].append({'id': 'water:cove', 'name': 'The sand-fall cove', 'kind': 'water', 'part_of': 'zone:west_dunes',
                        'purpose': "A cove cut into the west rim before the dune crest (D-31's signature view): the "
                                   'dunes pour over its walls into the stars.'})
    p['links'].append({'id': 'link:prospector_path', 'from': 'zone:south_steppe', 'to': 'zone:barbaric_mountains',
                       'kind': 'path', 'notes': "Up a gully to the prospector's notch."})
    p['notes'] = ('Written by output/studio_cal/x6/tools/gen.py from gen_l1.py (the approved L1 with D-31). Sealed '
                  'until their maps exist: XD-14, XD-15, XD-20, FD-02 (phase 6).')
    if level == 'L2':
        p.pop('sketch', None)
    return p


# ---------------------------------------------------------------- spawn markers on walkable ground
EDGE_ARRIVALS = {'entrance:east_road': (107.5, 60.5), 'entrance:south_road': (50.5, 107.5)}
KNOBS = [(cx, cy) for cx, cy, r, top in LD.BARBARIC + LD.GARGOYLE if top >= 2900]
NO_MARKERS = [  # things the markers keep off (the castle, the sphinxes, the mesa tops, the serai, the paths)
    [[34.2, 26.8], [41.8, 26.8], [41.8, 37.8], [34.2, 37.8]],
    [[79.6, 29.4], [84.4, 29.4], [84.4, 46.0], [79.6, 46.0]],
    [[33.4, 81.4], [40.8, 81.4], [40.8, 87.0], [33.4, 87.0]],
    [[75.8, 73.8], [80.6, 73.8], [80.6, 78.6], [75.8, 78.6]],
]


def walkable(x, y):
    if any(math.hypot(x - a[0], y - a[1]) < 3.0 for a in KNOBS):
        return False
    for cx, cy, r, top in LD.MESAS:
        if math.hypot((x - cx) * 0.85, y - cy) < r + 1.8:
            return False
    hs = [LD.raw_height(x + dx, y + dy) for dx in (-0.5, 0.5) for dy in (-0.5, 0.5)]
    if max(hs) - min(hs) > 300:                    # the engine slides over 512 a tile: keep a margin
        return False
    if K.inside((x, y), LD.POND) or K.edge_dist((x, y), LD.POND) < 1.5:
        return False
    for line in (LD.CLIFF_PATH, LD.PROSPECT_PATH, LD.NEST_CRACK):
        if LD.dist_to_line(x, y, line) < 1.5:
            return False
    return x > LD.RIM_X + 1.5 and y > LD.RIM_Y + 1.2 and x < 109 and y < 109

# D-85 (s26): no hostile marker within 5,888 (missile range 5,120 + 768) of an outdoor talking quest giver. The markers
# of these areas that the sampling puts nearer than 12.5 cells (5,888 + the circle's 512) move to the nearest free
# candidate beyond it; the area's other markers and every other area keep their places.
GIVER_CLEAR = {'pop:west_dunes': [(31.1, 70.6)]}   # Saul (4602)
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


# F10 (A5 s30): areas whose markers stand at fixed cells (gen_l1.AREAS pop:pan_west), not sampled
FIXED_SPOTS = {'pop:pan_west': [(26, 59), (36, 55)]}


def markers():
    clear = [poly for _aid, poly, _n in L1.KEEP_CLEAR] + NO_MARKERS
    door_pts = [d[2] for d in P.doors]
    roads = [ln for _l, ln, _w, _s in L1.ROADS]
    out = []
    for pid, slot, count, poly, note in L1.AREAS:
        if pid in FIXED_SPOTS:
            spots = FIXED_SPOTS[pid]
            assert len(spots) == count and all(walkable(x, y) and K.inside((x, y), poly) for x, y in spots), pid
            for k, (x, y) in enumerate(spots, 1):
                out.append({'id': pid, 'index': k, 'count': 1, 'slot': slot, 'circle': {'at': [x, y], 'r': 1},
                            'notes': note if k == 1 else 'walkable ground'})
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
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        start = min(cand, key=lambda q: math.hypot(q[0] - cx, q[1] - cy))
        for a in EDGE_ARRIVALS.values():
            near = min(cand, key=lambda q: math.hypot(q[0] - a[0], q[1] - a[1]))
            if math.hypot(near[0] - a[0], near[1] - a[1]) < 11:
                start = near
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
                        'notes': note if k == 1 else 'walkable ground'})
    for aid, poly, note in L1.KEEP_CLEAR:
        a = {'id': aid, 'kind': 'keep_clear', 'polygon': poly}
        if note:
            a['notes'] = note
        out.append(a)
    for aid, poly, note in L1.OPEN:
        out.append({'id': aid, 'kind': 'open', 'polygon': poly, 'notes': note})
    return out


SIGNPOST_AT = [(54.9, 60.5), (80.9, 60.2), (51.0, 83.1)]
MOVED = {  # points the L3 detail moved (cells; facing)
    'entrance:sphinx_wells': ([int(P.WELLS_ARRIVAL[0]), int(P.WELLS_ARRIVAL[1])], 'w'),
    'entrance:warzone_coach': ([int(P.YARD_ARRIVAL[0]), int(P.YARD_ARRIVAL[1])], 'w'),
    'entrance:xd14_gate': ([38, 34], 's'),
    'entrance:xd20_gate': ([88, 95], 'w'),
    'entrance:fd02_door': ([40, 84], 'e'),   # D-57: (-12288, -10240), 256 before the carrier's leaves (x 39.5); points take whole cells, the nearest to D-57's -12144
    'poi:oasis_fountain': ([45, 61], None),
    'poi:wells_well': ([61, 60], None),
    'poi:cloud_hoard': ([81, 44], None),
    'poi:shrine_energy': ([28, 54], None),
    'poi:waters_power': ([30, 34], None),
    'poi:well_accuracy': ([52, 92], None),
    'poi:prospector_camp': ([99, 101], None),
    'poi:mesa_nest': ([66, 34], None),
}


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
    s['actors'] = V.fill(P.actors(), 'X6')   # D-96: Sphinx Wells' villagers
    s['relations'] = (s.get('relations') or []) + V.relations('X6')
    # A1's E9 (merge point 20): AU's sand-fall loop (devdocs/xeen/AUDIO.md, 62505) over the three falls on the cove's
    # north wall; one source in the middle of the row (1,600 either side lies inside its inner radius), so three
    # copies of one noise loop never comb against each other
    if P.SANDFALL_LIVE:
        mid = P.SANDFALLS_SOUTH[len(P.SANDFALLS_SOUTH) // 2]
        s['sounds'] = [{'id': 'sound:sandfalls', 'at': list(mid), 'sound': 'xeen_sandfall_loop', 'radius': 4500,
                        'inner_radius': 1800, 'volume': 0.6, 'loop': True}]
    s['events'] = P.events()
    s['scatter'] = SC.scatter()
    s['notes'] = ('X6 Desert of the Sphinx, L3/L4 sketch (A5, 2026-11-20), written by output/studio_cal/x6/tools/gen.py. '
                  'Cells [x, y], x east, y south. Heights above the stars below the rims (0): the oasis pond 1,000, '
                  'the pan and Sphinx Wells 1,248, the dunes 1,300-1,750, the red mesas to 2,240, the Basenji heights '
                  "2,400-2,750 (the castle's gate terrace 2,592), the Barbaric Mountains to 3,700 (D-31).")
    return s


def dump(folder, name, data):
    if name == 'sketch.yml':   # AU's outdoor beds (A5, 2026-11-21; level_generation/projects/xeen/common/beds)
        sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common/beds')
        import beds as _beds
        data = _beds.with_beds(data, 'x6')
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, name), 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)


def main():
    pr = project()
    sk = sketch()
    # F2/F8 (2026-11-21): wing doors as double doors, cave mouths as wide as their rim; D-91/F16 (A5 s29): the den
    # blocked (its own form and line, no click line to nowhere), the entrance window's trans.txt lines
    sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
    sys.path.insert(0, _REPO_ROOT + '/level_generation/projects/xeen/common')
    import house_doors as HD
    import entrance as EN
    # D-91 (A5 s30): the Summer Druid stands on S's row 11929 (friendly in the world): no map relation for row 517
    for _note in HD.double_doors_sketch(sk) + HD.bury_mouths_sketch(sk) + EN.apply(sk, 'x6'):
        print('door:', _note)
    # P2 feedback F29/F32/F33 (agent xeen-fb2-wild, 2026-11-23): shrine altars, campfires, the rim fall
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'common'))
    import wild as WILD
    for _note in WILD.apply(sk, 'x6'):
        print('wild:', _note)
    atmos = {'format': 0, 'sky': 'plansky2', 'weather': {},
             'notes': "D-31: the shipped clear preset (plansky2 is the clear preset's alias) in every weather, no rain; "
                      "the world's sky.yml gives xeen_x6.odm the arid theme (A6)."}
    for level in ('L2', 'L3', 'L4'):
        out = os.path.join(BRIEFS, level)
        dump(out, 'project.yml', pr)
        dump(out, 'plan.yml', plan('L3' if level == 'L4' else level))
        if level != 'L2':
            dump(out, 'sketch.yml', sk)
            dump(out, 'atmosphere.yml', atmos)
    print('plots', sum(len(v) for v in P.plots_by_space.values()), 'structures', len(sk['structures']),
          'actors', len(sk['actors']), 'scatter', len(sk['scatter']), 'markers',
          sum(1 for a in sk['areas'] if 'slot' in a), 'sand-falls', 'placed' if P.SANDFALL_LIVE else 'off (S)')
    print('X4 arrival', X4_ARRIVAL, 'X5 arrival', X5_ARRIVAL)
    print('hooks used', sorted(P.USED))
    print('missing', sorted(P.MISSING))


if __name__ == '__main__':
    main()
