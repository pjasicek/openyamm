#!/usr/bin/env python3
"""D-85 and D-87 checks of a built outdoor Xeen map (A5, 2026-11-21).

Usage: check_d85.py <scene.yml> [giver_limit] [--kept SUBSTR ...] [--kept-group N ...]

--kept: an arrival whose labels contain SUBSTR is reported as KEPT, not ERROR (a breach waiting on a decider, named in
the map's NOTES). No map uses it now.
--kept-group: placed hostile actors of actor group N are reported as KEPT, not ERROR, near an arrival (every other
marker and actor still counts there). X2's temple guards, group 63, by D-88: the XD-06 exit's only way in is past them.

D-85: no hostile spawn marker or placed hostile within `giver_limit` (default 5,888 = missile range 5,120 + 768) of a
talking NPC (npc_id). X6 passes 5,120: D-87 (4) keeps melee and damage-only kinds in the 5,120-5,888 band.

D-87 (3): no RANGED DISABLER within 5,888 of a talking NPC or of any outdoor arrival point. A ranged disabler is a
monster whose special attack (monster_data "Bonus") is Stone, Curse, Paralyze, Asleep, Insane, Afraid, Uncon, Dead or
Errad and one of whose attacks has a missile, or one with a Paralyze or Finger of Death spell. A spawn marker counts if
any monster its slot can roll qualifies (slots 1-3: tier A at Dif 0, A-C otherwise; 4-12: the fixed tier). Arrival
points: the build's named arrivals and edge starts (build.json beside the scene, else the installed studio.yml),
coaches and docks (transport_locations), mirrors, Town Portal points, edge_spans' `at`, every installed map's Lua
MoveToMap into this map, the own built Lua's moves within the map, and Xeen.SkyFalls / Xeen.skyFall landings.
Other kinds near an arrival are listed for information (D-15's band is measured elsewhere). Exit 1 on any ERROR.
"""
import json
import math
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
XEEN = ROOT / 'assets_dev/worlds/xeen'
TABLES = XEEN / 'data_tables'
RANGE = 5888.0
CONDITIONS = {'stone', 'curse', 'paralyze', 'asleep', 'insane', 'afraid', 'uncon', 'dead', 'errad'}
SPELLS = {'paralyze', 'finger of death'}
Loader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)


def tsv_rows(path):
    for line in open(path, encoding='utf-8', errors='replace'):
        if line.startswith('#'):
            continue
        yield line.rstrip('\n').split('\t')


def load_monsters():
    """picture -> (id, name, reason or None); id -> same."""
    by_pic, by_id = {}, {}
    for f in tsv_rows(TABLES / 'monster_data.txt'):
        if len(f) < 28 or not f[0].strip().isdigit():
            continue
        mid, name, pic = int(f[0]), f[1], f[2]
        bonus, miss1, att2, miss2 = f[16].strip(), f[19].strip(), f[20].strip(), f[23].strip()
        spells = [f[25], f[27]]
        reason = None
        missile = (miss1 not in ('', '0')) or (miss2 not in ('', '0') and att2 not in ('', '0'))
        if bonus.lower() in CONDITIONS and missile:
            reason = '%s by missile' % bonus
        for s in spells:
            sp = s.strip('"').split(',')[0].strip().lower()
            if sp in SPELLS:
                reason = '%s spell' % sp.title()
        entry = (mid, name, reason)
        by_pic[pic] = entry
        by_id[mid] = entry
    return by_pic, by_id


def load_slots(map_file):
    """slot 1-3 -> (picture base, dif)."""
    for f in tsv_rows(TABLES / 'map_stats.txt'):
        if len(f) > 27 and f[2].strip() == map_file:
            return {1: (f[16].strip(), int(f[18] or 0)), 2: (f[20].strip(), int(f[22] or 0)),
                    3: (f[24].strip(), int(f[26] or 0))}, int(f[0])
    return {}, None


def slot_kinds(index, slots, by_pic):
    if 1 <= index <= 3:
        base, dif = slots[index]
        tiers = 'A' if dif == 0 else 'ABC'
    elif 4 <= index <= 12:
        base = slots[(index - 4) % 3 + 1][0]
        tiers = 'ABC'[(index - 4) // 3]
    else:
        return []
    return [by_pic[base + ' ' + t] for t in tiers if base + ' ' + t in by_pic]


MOVE = re.compile(r'evt\.MoveToMap\(\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,[^()"]*?(?:"([^"]+)")?\s*(?:,\s*\{[^}]*\})?\s*\)')
SKYFALL = re.compile(r'Xeen\.skyFall\(\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*-?\d+\s*,\s*"([^"]+)"')
SKYFALLS_ROW = re.compile(r'(\w+)\s*=\s*\{\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*-?\d+\s*,\s*"([^"]+)"\s*\}')


def arrival_points(scene, scene_path, stem, map_file, map_id):
    pts = []
    for e in scene.get('entities') or []:
        if e.get('name', '').endswith('start'):
            pts.append((e['name'], (e['position']['x'], e['position']['y'])))
    build = scene_path.parent / 'build.json'
    if build.exists():
        b = json.load(open(build))
        st = b.get('start') or {}
        if 'x' in st:
            pts.append(('start (%s)' % st.get('entrance', ''), (st['x'], st['y'])))
        for a in b.get('named_arrivals') or []:
            pts.append((a['name'], tuple(a['at'][:2])))
        for a in b.get('arrivals') or []:
            pts.append(('%s (%s)' % (a['name'], a.get('entrance', '')), tuple(a['at'][:2])))
    else:
        studio = XEEN / 'maps' / (stem + '.studio.yml')
        if studio.exists():
            for a in yaml.load(open(studio), Loader=Loader).get('arrivals') or []:
                pts.append((a['name'], tuple(a['at'][:2])))
    for f in tsv_rows(TABLES / 'transport_locations.txt'):
        if len(f) > 12 and f[1].strip() == map_file:
            pts.append(('coach/dock %s %s' % (f[0], f[15].strip() if len(f) > 15 else ''), (int(f[10]), int(f[11]))))
    mirrors = yaml.load(open(TABLES / 'mirrors.yml'), Loader=Loader) or {}
    for side in mirrors.values():
        for m in side or []:
            if m.get('map') == map_file:
                pts.append(('mirror %s' % m.get('town'), tuple(m['at'][:2])))
    for f in tsv_rows(TABLES / 'town_portal_switch.txt'):
        if len(f) > 13 and f[0].strip().isdigit() and f[1].strip().isdigit() and int(f[1]) == map_id:
            pts.append(('town portal %s' % f[13].strip(), (int(f[2]), int(f[3]))))
    spans = yaml.load(open(TABLES / 'edge_spans.yml'), Loader=Loader) or {}
    for s in spans.get('edge_spans') or []:
        if s.get('to_map') == map_file and s.get('at'):
            pts.append(('edge from %s %s' % (s['map'], s['edge']), tuple(s['at'][:2])))
    own_lua = scene_path.parent / (stem + '.lua')
    if not own_lua.exists():
        own_lua = XEEN / 'events/maps' / (stem + '.lua')
    luas = [p for p in sorted((XEEN / 'events/maps').glob('*.lua')) if p.stem != stem] + [own_lua]
    luas += sorted((XEEN / 'events/common').glob('*.lua'))
    for lua in luas:
        text = open(lua, encoding='utf-8', errors='replace').read()
        for m in MOVE.finditer(text):
            target = m.group(4)
            if target == map_file or (target is None and lua == own_lua):
                pts.append(('move in %s' % lua.stem, (int(m.group(1)), int(m.group(2)))))
        for m in SKYFALL.finditer(text):
            if m.group(4) == map_file:
                pts.append(('skyFall in %s' % lua.stem, (int(m.group(1)), int(m.group(2)))))
        for m in SKYFALLS_ROW.finditer(text):
            if m.group(5) == map_file:
                pts.append(('Lua table %s.%s' % (lua.stem, m.group(1)), (int(m.group(2)), int(m.group(3)))))
    merged = []
    for name, p in pts:
        for e in merged:
            if math.hypot(e[1][0] - p[0], e[1][1] - p[1]) < 128:
                if name not in e[0]:
                    e[0].append(name)
                break
        else:
            merged.append(([name], p))
    return merged


def main():
    args, kept, kept_groups = [], [], set()
    argv = sys.argv[1:]
    while argv:
        a = argv.pop(0)
        if a == '--kept':
            kept.append(argv.pop(0))
        elif a == '--kept-group':
            kept_groups.add(int(argv.pop(0)))
        else:
            args.append(a)
    scene_path = Path(args[0]).resolve()
    limit = float(args[1]) if len(args) > 1 else RANGE
    stem = scene_path.name.split('.')[0]
    scene = yaml.load(open(scene_path), Loader=Loader)
    by_pic, by_id = load_monsters()
    for map_file in (stem + '.odm', stem + '.blv'):   # X9's sky is a BLV with outdoor-style arrivals
        slots, map_id = load_slots(map_file)
        if slots:
            break
    if not slots:
        print('ERROR no map_stats row for %s' % map_file)
        return 1
    actors = scene['initial_state'].get('actors') or []
    givers = [a for a in actors if a.get('npc_id')]
    hostile = []   # (label, (x, y), disabler reason or None)
    unknown = []
    for s in scene.get('spawns') or []:
        if s.get('type_id') != 3:
            continue
        kinds = slot_kinds(s['index'], slots, by_pic)
        why = ['%s: %s' % (k[1], k[2]) for k in kinds if k[2]]
        hostile.append(('spawn %d slot %d' % (s['spawn_index'], s['index']), (s['position']['x'], s['position']['y']),
                        '; '.join(why) or None))
    for a in actors:
        if not a.get('npc_id') and a.get('attributes', 0) & 0x80000:
            mid = a.get('monster_info_id') or a['monster_id']   # BLV scenes keep the table id in monster_info_id
            k = by_id.get(mid)
            if k is None:
                print('ERROR actor %d: monster %d not in the Xeen monster table' % (a['actor_index'], mid))
                unknown.append(mid)
            why = '%s: %s' % (k[1], k[2]) if k and k[2] else None
            hostile.append(('actor %d (%d)%s' % (a['actor_index'], mid,
                                                 ' group %d kept' % a['group'] if a.get('group') in kept_groups else ''),
                            (a['position']['x'], a['position']['y']), why))
    print('%s: map_stats %s slots %s; ranged-disabler markers/actors %d of %d' % (
        stem, map_id, {k: v for k, v in slots.items()}, sum(1 for h in hostile if h[2]), len(hostile)))
    for h in hostile:
        if h[2]:
            print('  disabler %s at (%d, %d): %s' % (h[0], h[1][0], h[1][1], h[2]))
    bad = len(unknown)

    def near(p, pool):
        return sorted((math.hypot(q[0] - p[0], q[1] - p[1]), n, w) for n, q, w in pool)

    for g in givers:
        gp = (g['position']['x'], g['position']['y'])
        ds = near(gp, hostile)
        if not ds:
            print('ok npc %d actor %d: no hostile on the map' % (g['npc_id'], g['actor_index']))
            continue
        d, name, _ = ds[0]
        dis = [x for x in ds if x[2]]
        err = d < limit or (dis and dis[0][0] < RANGE)
        bad += bool(err)
        print('%s npc %d actor %d at (%d, %d): nearest %s %.0f; within %d: %s; nearest disabler %s' % (
            'ERROR' if err else 'ok', g['npc_id'], g['actor_index'], gp[0], gp[1], name, d, limit,
            [n for dd, n, _ in ds if dd < limit], '%s %.0f' % (dis[0][1], dis[0][0]) if dis else '-'))
    for names, p in arrival_points(scene, scene_path, stem, map_file, map_id):
        ds = near(p, hostile)
        waived = [x for x in ds if x[2] and x[1].endswith(' kept') and x[0] < RANGE]
        dis = [x for x in ds if x[2] and not x[1].endswith(' kept')]
        err = bool(dis) and dis[0][0] < RANGE
        keep = err and any(k in n for k in kept for n in names)
        bad += err and not keep
        print('%s arrival (%d, %d) [%s]: nearest disabler %s; nearest other %s' % (
            'KEPT' if keep else 'ERROR' if err else 'ok', p[0], p[1], ', '.join(names),
            '%s %.0f' % (dis[0][1], dis[0][0]) if dis else '-',
            '%s %.0f' % (ds[0][1], ds[0][0]) if ds else '-'))
        if err:
            for dd, n, w in dis:
                if dd < RANGE:
                    print('    %6.0f %s (%s)' % (dd, n, w))
        for dd, n, w in waived:
            print('    KEPT %6.0f %s (%s)' % (dd, n, w))
    print('%s: %d errors' % (stem, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
