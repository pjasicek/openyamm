#!/usr/bin/env python3
"""X3 measure (A5, 2026-11-20): MAPS section 0's figures and D-11.1/D-11.4 from a build folder and the L4 project.

Usage: measure.py [<build dir>] [<project dir>]

hostiles at load: spawn markers x the mean of their slot's per_marker, plus hostile placed actors.
first fight: nearest hostile to each arrival; the camp and the Newcastle gate (D-11.1: 5,000-6,500).
POIs (D-20): the shipped census on the build (census() below); other places count for the 6,000 rule.
6,000 rule: no land tile inside the party's square farther than 6,000 from a place (a POI, a door, an arrival) or a
fight. Roads: road tiles of the land inside the square. Height range: the land's lowest to highest node.
"""
import math
import sys
from pathlib import Path
import json

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'output/xeen_review/scale'))
sys.path.insert(0, str(ROOT / 'util'))
from heatmaps import terrain_rows, tile_flags  # noqa: E402
from map_export import parse_odm_file  # noqa: E402

B = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'output/studio_cal/x3/build_w'
P = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'devdocs/xeen/briefs/x3/L4'
CHEST_KINDS = ('chest',)
# structures that are a point of interest by themselves (D-11.4 merges anything within 400)
# (signposts, the road-end sign, plinth boards, camp fires and the huts that stand by their own chest are not counted
# by themselves: the shipped census counts the place, and they lie by a counted thing or on a road)
POI_KINDS = ('chest', 'well', 'fountain', 'obelisk', 'portal', 'hatch', 'cave_mouth')
POI_IDS = ('thing:rhyme_board', 'thing:count_sign', 'thing:sundial_1', 'thing:sundial_2', 'thing:sundial_3',
           'thing:garlic_shrine', 'thing:food_tree_1', 'thing:food_tree_2', 'thing:food_tree_3', 'thing:newcastle_ruin',
           'thing:sunken_grave_1', 'thing:coffin_closed', 'thing:ranger_tent_1', 'thing:ebenezer_tent')


def W(at):
    return ((at[0] - 64) * 512, (64 - at[1]) * 512)

# D-20: the shipped census (devdocs/xeen/research/map_craft/measure_outdoor.py: luaEvents, classify, components), run
# on the build: the events bound to faces and decorations, classified by what they call and their hint (residences,
# map exits and events that only name a thing are no POI; NPC actors are none), the same class and hint within 600
# taken once (one set piece, one spot), the shipped native interactive decorations added, chained joining within 400.
# The studio's Lua carries no event kinds: a structure's sketch kind (well, fountain, obelisk) stands in for them, and
# a Xeen mirror (Xeen.useMirror) is a travel service, as a shipped stable.
HINT_RULES = [
    ('fountain', r'fountain'), ('well', r'\bwell\b'), ('shrine', r'shrine|altar'), ('obelisk', r'obelisk'),
    ('pedestal', r'pedestal'), ('barrel', r'barrel|keg'), ('cauldron', r'cauldron'), ('campfire', r'campfire|fire\b'),
    ('sign', r'\bsign|signpost|post\b'), ('statue', r'statue'), ('tree', r'\btree'),
    ('stone', r'stone|rock|boulder|menhir'), ('boat/ship', r'boat|ship|wreck'),
    ('grave', r'grave|tomb|crypt|coffin|sarcophag'), ('chest', r'chest|crate|box|cask'),
    ('door/gate', r'\bdoor|gate|portcullis'), ('teleporter', r'teleport|portal|pad\b'), ('lever', r'lever|switch|button'),
    ('trough/cart', r'trough|cart|wagon'), ('hut/tent', r'tent|hut\b'), ('library/book', r'book|library|tome'),
]
NATIVE = (('buff_pedestal', r'dec(4[4-9]|5[0-5])$'), ('stat_challenge', r'dec4[0-3]$'), ('pedestal', r'ped'),
          ('sword_in_stone', r'swrdstn$'),
          ('campfire', r'(ckfyr00|cmpfyr00|dec24|dec25|dec24x|7dec02|dec06|dec04)$'), ('ship', r'shp$'),
          ('cauldron', r'dec26$'))


def house_types():
    out = {}
    for f in ('assets_dev/engine/data_tables/house_data.txt', 'assets_dev/worlds/xeen/data_tables/house_data.txt'):
        for line in (ROOT / f).read_text(encoding='latin-1').splitlines():
            r = line.split('\t')
            if len(r) > 2 and r[0].strip().isdigit():
                out[int(r[0])] = r[2]
    return out


def chained(pts, radius):
    """components() of the shipped census: groups of points joined by chains of steps no longer than radius."""
    parent = list(range(len(pts)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]) <= radius:
                parent[root(i)] = root(j)
    groups = {}
    for i in range(len(pts)):
        groups.setdefault(root(i), []).append(i)
    return list(groups.values())


def census(B, P, sketch):
    import re
    text = next(B.glob('*.lua')).read_text(encoding='latin-1')
    regs = list(re.finditer(r'^Register(?:NoOp)?Event\((\d+),\s*(?:"([^"]*)"|nil)', text, re.M))
    ev = {}
    for i, m in enumerate(regs):
        block = text[m.start(): regs[i + 1].start() if i + 1 < len(regs) else len(text)]
        ev[int(m[1])] = {'hint': m[2] or '', 'calls': set(re.findall(r'evt\.(\w+)\(', block)),
                         'houses': set(map(int, re.findall(r'evt\.EnterHouse\((\d+)', block))),
                         'mirror': bool(re.search(r'Xeen\.useMirror\(', block)),
                         'dest': set(x.lower() for x in re.findall(r'"([^"\n]+\.(?:blv|odm))"', block)),
                         'named_only': bool(re.match(r'Register(?:NoOp)?Event\(\d+,\s*(?:"[^"]*"|nil),\s*nil', block))}
    kinds = {s['id']: s['kind'] for s in sketch['structures']}
    ids = yaml.safe_load((P / 'ids.lock.yml').read_text())
    for name, number in (ids.get('events') or {}).items():
        if number in ev and name.startswith('evt:thing:'):
            ev[number]['kind'] = kinds.get(name[4:], '')
    houses = house_types()

    def classify(e):
        hint = e['hint'].lower()
        if e['named_only']:
            return 'unnamed'     # a name on hover only: an event-less landmark (D-20)
        if e['houses']:
            t = houses.get(sorted(e['houses'])[0], '?')
            return 'residence' if t == 'House' else 'service:' + t
        if e['mirror']:
            return 'service:mirror'
        if 'OpenChest' in e['calls']:
            return 'chest'
        if e['dest']:
            return 'dungeon_entrance' if sorted(e['dest'])[0].endswith('.blv') else 'map_exit'
        if e.get('kind') in ('fountain', 'well', 'obelisk'):
            return e['kind']
        for name, rx in HINT_RULES:
            if re.search(rx, hint):
                return name
        return 'other' if hint else 'unnamed'
    # a studio build keeps the bound events and the decorations in its scene file (the shipped maps in the ODM)
    p = parse_odm_file(next(B.glob('*.odm')))['payload']
    scene = yaml.load(next(B.glob('*.scene.yml')).read_text(), Loader=yaml.CSafeLoader)
    binds = {}
    for f in scene['bmodel_faces']['interactive_faces']:
        eid = f['cog_triggered_number']
        if eid:
            m = p['bmodels'][f['bmodel_index']]
            face = m['faces'][f['face_index']]
            v = np.array([[m['vertices'][i][a] for a in 'xyz'] for i in face['vertex_indices']]).mean(axis=0)
            binds.setdefault(eid, []).append(v)
    entities = scene['entities']
    for e in entities:
        if e['event_id_secondary']:
            binds.setdefault(e['event_id_secondary'], []).append(np.array([e['position'][a] for a in 'xyz'], float))
    pois = []
    for eid, lst in binds.items():
        e = ev.get(eid, {'hint': '', 'calls': set(), 'houses': set(), 'mirror': False, 'dest': set(),
                         'named_only': True})
        pois.append({'name': '%s (%d)' % (e['hint'] or '?', eid), 'class': classify(e), 'hint': e['hint'].lower(),
                     'pos': np.mean(lst, axis=0)})
    # one set piece, one spot (D-20): the same class and hint chained within 600 (a churchyard's graves, the dials)
    ded = []
    for key in sorted(set((x['class'], x['hint']) for x in pois)):
        same = [x for x in pois if (x['class'], x['hint']) == key]
        for g in chained([x['pos'] for x in same], 600):
            ded.append(dict(same[g[0]], pos=np.mean([same[i]['pos'] for i in g], axis=0),
                            name=same[g[0]]['name'] + (' x%d' % len(g) if len(g) > 1 else '')))
    spots = [(x['name'] + ' ' + x['class'], x['pos']) for x in ded
             if x['class'] not in ('residence', 'map_exit', 'unnamed', 'other')]
    for e in entities:
        n = e['name'].lower()
        for tag, rx in NATIVE:
            if re.match(rx, n):
                spots.append(('%s %s' % (n, tag), np.array([e['position'][a] for a in 'xyz'], float)))
                break
    merged = [[None, tuple(np.mean([spots[i][1] for i in g], axis=0)[:2]), [spots[i][0] for i in g]]
              for g in chained([x[1] for x in spots], 400)]
    chests = sum(1 for x in pois if x['class'] == 'chest')
    return merged, chests


def main():
    project = yaml.safe_load((P / 'project.yml').read_text())
    sketch = yaml.safe_load((P / 'sketch.yml').read_text())
    build = json.loads((B / 'build.json').read_text())
    scene = yaml.load(next(B.glob('*.scene.yml')).read_text(), Loader=yaml.CSafeLoader)
    means = [sum(s['per_marker']) / 2 for s in project['map_stats']['slots']]
    hostiles = []
    markers = 0
    for s in scene.get('spawns') or []:
        if s['type_id'] != 3 or not 1 <= s['index'] <= 3:
            continue
        markers += 1
        hostiles.append((s['position']['x'], s['position']['y'], means[s['index'] - 1], s['index']))
    placed = 0
    for a in sketch.get('actors') or []:
        if a.get('hostile'):
            x, y = W(a['at'])
            hostiles.append((x, y, a.get('count', 1), 'placed'))
            placed += a.get('count', 1)
    total = sum(h[2] for h in hostiles)
    print('hostiles at load %.0f (%d markers, %d placed)' % (total, markers, placed))

    def nearest(x, y):
        return min(math.hypot(h[0] - x, h[1] - y) for h in hostiles)
    arrivals = {a['entrance']: a['at'] for a in build['arrivals']}
    pts = {p['id']: p['at'] for p in sketch['points']}
    arr = {'east (X2)': arrivals.get('entrance:east_road'), 'west (X5)': arrivals.get('entrance:west_road'),
           'north start (X4)': W((50.9, 20.6)),
           'nightshadow_square': W(pts['entrance:nightshadow_square']),
           'newcastle_gate': W(pts['entrance:newcastle_gate']), 'camp_fire': W(pts['entrance:camp_fire']),
           'xd11 door': W((64.5, 67.2))}
    for k, v in arr.items():
        print('first fight from %-28s %6.0f' % (k, nearest(v[0], v[1])))
    doors = {b['id']: b['door'] for b in build['buildings'] if b.get('door')}
    for k in ('building:camp_shrine',):
        print('nearest monster to %-28s %6.0f' % (k, nearest(doors[k][0], doors[k][1])))
    st = {s['id']: s for s in sketch['structures']}
    tent = W(st['thing:ebenezer_tent']['at'])
    print('nearest monster to %-28s %6.0f' % ('Ebenezer\'s tent', nearest(*tent)))
    print('nearest monster to %-28s %6.0f' % ('the Newcastle gate', nearest(*W((82.5, 36.8)))))
    ns = [d for k, d in doors.items() if 'nightshadow' in k or k in ('building:moon_guild', 'building:du_monay_manor',
                                                                    'building:treasure_trove', 'building:gnome_home')]
    print('nearest monster to a Nightshadow door          %6.0f' % min(nearest(d[0], d[1]) for d in ns))
    # places (the 6,000 rule and the wild-land figure): every spot a party walks to, POI or not: structures, doors, NPCs
    places_spots = []
    for s in sketch['structures']:
        if s['kind'] in POI_KINDS or s['id'] in POI_IDS:
            if 'at' in s:
                places_spots.append(W(s['at']))
            elif 'line' in s:
                places_spots.append(W(s['line'][0]))
    for k, d in doors.items():
        if 'nightshadow_houses' not in k and k != 'thing:high_magic':
            places_spots.append((d[0], d[1]))
    for a in sketch['actors']:
        if a.get('npc'):
            places_spots.append(W(a['at']))
    merged, chests = census(B, P, sketch)
    print('POIs (D-20: the shipped census, bound events chained within 400): %d; chests %d' % (len(merged), chests))
    for m in merged:
        print('   %s' % ', '.join(m[2]))
    # land, roads, the 6,000 rule
    p = parse_odm_file(next(B.glob('*.odm')))['payload']
    rows = terrain_rows('mm7')
    tm = np.array(p['tile_map']).reshape(128, 128)
    hm = np.array(p['height_map']).reshape(128, 128) * 32 if 'height_map' in p else None
    flags = {t: tile_flags(p, 'mm7', rows, t) for t in np.unique(tm)}
    places = ([m[1][:2] for m in merged] + [p[:2] for p in places_spots] + [v[:2] for v in arr.values()]
              + [(h[0], h[1]) for h in hostiles])
    places = np.array(places)
    far = []
    land = 0
    road = 0
    worst = (0, None)
    farcells = []
    for ty in range(19, 109):
        for tx in range(19, 109):
            if ty >= 104:
                continue
            f = flags[tm[ty, tx]]
            if f & 2 and not f & 0x100:
                continue
            land += 1
            if f & 0x100:
                road += 1
            x, y = (tx + 0.5 - 64) * 512, (64 - ty - 0.5) * 512
            d = np.min(np.hypot(places[:, 0] - x, places[:, 1] - y))
            far.append(d)
            if d > 6000:
                farcells.append((tx, ty, int(d)))
            if d > worst[0]:
                worst = (d, (tx, ty))
    far = np.array(far)
    print('6,000 rule: farthest land from a place or fight %.0f at cell %s; tiles over 6,000: %d; over 3,000: %.2f'
          % (worst[0], worst[1], int((far > 6000).sum()), (far > 3000).mean()))
    print('   over 6,000: %s' % farcells)
    print('road tiles (paved, the build) %d of %d land tiles in the square (%.1f %%)' % (
        build['counts']['road_cells'], land, 100.0 * build['counts']['road_cells'] / land))
    if hm is not None:
        lm = hm[19:104, 19:109]
        print('land heights in the square %d-%d' % (lm.min(), lm.max()))
    print('build: highest %d' % build['counts']['highest'])


if __name__ == '__main__':
    main()
