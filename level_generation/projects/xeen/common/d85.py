#!/usr/bin/env python3
"""D-85 / D-87 check (A6 s31): talking givers and every arrival point of A6's maps against hostile spawn markers and
placed actors (the hostile ones, as check_arrivals.hostiles reads them), with D-87's ranged-disabler kind filter.

Usage: d85.py [maps_dir] [stems...] [--kept-group N ...]

Arrival points: the studio's named arrivals (start, edges, falls, dungeon exits), and from the world tables the edge
spans' set-down points, mirrors, Town Portal points and coach/boat/dock arrivals into the map.

A ranged disabler (D-87.3): a monster row with Stone, Curse, Paralyze, Asleep, Insane, Afraid, Uncon, Dead or Errad as
its attack bonus on an attack with a missile (attack 1's missile column), or a Paralyze / Finger of Death spell. A spawn
marker counts if any monster its slot can roll qualifies: slots 1-3 roll the family's tiers A-C (map_stats Dif; every
tier counts, MAW rolls all three), slots 4-12 a fixed tier. A ranged disabler within 5,888 fails; any other kind keeps
D-85's 5,120 / 5,888 report (melee kinds are warnings only, D-87.4). A placed actor with a `leash_radius` (a post) is
measured at its home distance less the leash (D-200: it reaches any point of its circle).

D-15's first-fight buffer, counting spawn markers (D-133, 2026-11-24): an arrival with a hostile that moves or shoots
(a placed hostile, or a scene spawn marker whose slot can roll such a row) within 2,000 (2D, less the marker's radius)
is flagged `FF` (tools/xeen/check_arrivals.py `first_fight`, the rule x2/check_d85.py fails a build on). The open-air
BLVs (X8, D7) keep their BLV markers outside the scene: check_arrivals.py holds those maps.
D-142 (2026-11-25): the floor depends on the arrival's kind (check_arrivals.arrival_kind): edge arrivals and a new
game's start 4,096, 5,888 if any row shoots or casts, the same at dungeon exits of the maps in
check_arrivals.D142_EXITS (else 2,000, the D-142 floor a warning), towns 2,000. `FF` lines are errors (exit 1), `FFW`
warnings; `ROAD` warns of a spawn marker centre within 1,024 of a road's centreline (the map's
devdocs/xeen/briefs/<key>/L4/sketch.yml `roads`). A maps_dir without the studio file (a scratch build) takes the
arrivals from its build.json (`named_arrivals`), else the installed studio file.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import check_arrivals  # noqa: E402

ROOT = Path(_REPO_ROOT + '/assets_dev')
XT = ROOT / 'worlds/xeen/data_tables'
# --kept-group N (2026-11-25, D-161): placed hostiles of actor group N near a dungeon-exit or town arrival are KEPT
# lines, not FF (a decision's door guards, as x2/check_d85.py --kept-group; never at an edge or the start)
_ARGV, KEPT_GROUPS = [], set()
_args = sys.argv[1:]
while _args:
    _a = _args.pop(0)
    if _a == '--kept-group':
        KEPT_GROUPS.add(int(_args.pop(0)))
    else:
        _ARGV.append(_a)
MAPS = Path(_ARGV[0]) if _ARGV and '/' in _ARGV[0] else ROOT / 'worlds/xeen/maps'
STEMS = [a for a in _ARGV if '/' not in a] or \
    ['xeen_x5', 'xeen_x8', 'xeen_d1', 'xeen_d2', 'xeen_d4', 'xeen_d5', 'xeen_d6', 'xeen_d7']
R, WARN, SHOW = 5120, 5888, 6500
L = yaml.CSafeLoader
DIS_BONUS = {'Stone', 'Curse', 'Paralyze', 'Asleep', 'Insane', 'Afraid', 'Uncon', 'Dead', 'Errad'}
DIS_SPELL = {'Paralyze', 'Finger of Death'}


def rows(path):
    out = {}
    for line in open(path, encoding='utf-8', errors='replace'):
        f = line.rstrip('\n').split('\t')
        if not f or not f[0].isdigit() or len(f) < 28:
            continue
        out[int(f[0])] = f
    return out


MON = rows(ROOT / 'engine/data_tables/monster_data.txt')
MON.update(rows(XT / 'monster_data.txt'))
BY_PIC = {}
for mid, f in sorted(MON.items()):
    BY_PIC.setdefault(f[2], mid)


def disabler(mid):
    """The reason the row is a ranged disabler, or ''."""
    f = MON.get(mid)
    if not f:
        return ''
    bonus = re.sub(r'x\d+$', '', f[16].strip())
    miss = f[19].strip()
    if bonus in DIS_BONUS and miss not in ('', '0'):
        return '%s by %s missile' % (bonus, miss)
    for col in (25, 27):
        spell = f[col].strip().strip('"').split(',')[0]
        if spell in DIS_SPELL:
            return '%s spell' % spell
    return ''


def name(mid):
    f = MON.get(mid)
    return f[1] if f else '?'


# map_stats: file -> (id, [(picture, dif)] for slots 1-3)
STATS = {}
for f in rows(XT / 'map_stats.txt').values():
    STATS[f[2]] = (int(f[0]), [(f[16 + 4 * k], f[18 + 4 * k]) for k in range(3)])
FILE_BY_ID = {v[0]: k for k, v in STATS.items()}


def slot_rows(fname, index):
    """The monster rows a spawn marker of this index can roll on the map."""
    if not 1 <= index <= 12 or fname not in STATS:
        return []
    if index <= 3:
        slot, tiers = index, 'ABC'
    else:
        slot, tiers = (index - 4) % 3 + 1, 'ABC'[(index - 4) // 3]
    pic = STATS[fname][1][slot - 1][0]
    if pic in ('', '0'):
        return []
    return [BY_PIC[pic + ' ' + t] for t in tiers if pic + ' ' + t in BY_PIC]


def arrivals(stem, fname, st):
    out = [(a['name'], a['at']) for a in (st.get('arrivals') or [])]
    es = yaml.load(open(XT / 'edge_spans.yml'), Loader=L)
    for e in es.get('edge_spans') or []:
        if e.get('to_map') == fname and e.get('at'):
            out.append(('edge span from %s %s' % (e['map'], e['edge']), e['at']))
    mir = yaml.load(open(XT / 'mirrors.yml'), Loader=L)
    for side in mir.values():
        for m in side or []:
            if m.get('map') == fname and m.get('at'):
                out.append(('mirror %s %s' % (m.get('id'), m.get('town')), m['at']))
    for line in open(XT / 'town_portal_switch.txt'):
        f = line.rstrip('\n').split('\t')
        if len(f) > 5 and f[0].isdigit() and f[1].isdigit() and FILE_BY_ID.get(int(f[1])) == fname:
            out.append(('town portal %s' % (f[14] if len(f) > 14 else f[0]), [int(f[2]), int(f[3]), int(f[4])]))
    for line in open(XT / 'transport_locations.txt'):
        f = line.rstrip('\n').split('\t')
        if len(f) > 12 and f[0].isdigit() and f[1] == fname:
            out.append(('transport %s %s' % (f[0], f[15] if len(f) > 15 else ''), [int(f[10]), int(f[11]), int(f[12])]))
    seen, uniq = set(), []
    for n, at in out:
        k = (round(at[0]), round(at[1]))
        if k not in seen:
            seen.add(k)
            uniq.append((n, at))
        else:
            for i, (n2, at2) in enumerate(uniq):
                if (round(at2[0]), round(at2[1])) == k:
                    uniq[i] = (n2 + ' = ' + n, at2)
    return uniq


def d2(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


totals = {'DIS': 0, 'FAIL': 0, 'WARN': 0, 'FF': 0, 'FFW': 0, 'ROAD': 0}
WORLD = check_arrivals.World(str(ROOT))
for stem in STEMS:
    scp = MAPS / f'{stem}.scene.yml'
    if not scp.exists():
        print(f'== {stem}: no scene')
        continue
    sc = yaml.load(open(scp), Loader=L)
    if (MAPS / f'{stem}.studio.yml').exists():
        st = yaml.load(open(MAPS / f'{stem}.studio.yml'), Loader=L)
    elif (MAPS / 'build.json').exists():
        st = {'arrivals': yaml.load(open(MAPS / 'build.json'), Loader=L).get('named_arrivals') or []}
    else:
        st = yaml.load(open(ROOT / f'worlds/xeen/maps/{stem}.studio.yml'), Loader=L)
    fname = next((k for k in STATS if k.startswith(stem + '.')), stem)
    actors = sc['initial_state'].get('actors') or []
    spawns = [s for s in (sc.get('spawns') or []) if s.get('type_id') == 3]
    talk = [a for a in actors if a.get('npc_id')]
    # the hostiles only (2026-11-24): a placed actor counts as check_arrivals counts it (an aggressor, or a row not
    # friendly to the party); the towns' villagers (D1's peasants and monks of group 47) are no threat to a giver
    hostile_ids = {h['id'] for h in check_arrivals.hostiles(WORLD, sc, fname)}
    others = [a for a in actors if not a.get('npc_id') and 'actor %d' % a['actor_index'] in hostile_ids]
    print(f'== {stem} ({fname}): {len(actors)} actors ({len(talk)} talking), {len(spawns)} monster markers; '
          f'slots {STATS.get(fname, (0, []))[1]}')
    things = []
    for s in spawns:
        rs = slot_rows(fname, s['index'])
        dis = [(m, disabler(m)) for m in rs if disabler(m)]
        things.append(((s['position']['x'], s['position']['y']), None,
                       f"marker {s['spawn_index']} idx {s['index']} grp {s['group']} "
                       f"({s['position']['x']}, {s['position']['y']}) [{'/'.join(name(m) for m in rs)}]", dis, 0))
    for a in others:
        m = a['monster_id']
        dis = [(m, disabler(m))] if disabler(m) else []
        # D-200: a placed post (`leash_radius`) reaches any point of its circle: measured at home less the leash
        leash = a.get('leash_radius') or 0
        things.append(((a['position']['x'], a['position']['y']), a['group'],
                       f"actor {a['actor_index']} {name(m)} ({m}) grp {a['group']} hos {a.get('hostility_type')} "
                       f"({a['position']['x']}, {a['position']['y']})" + (f" leash {leash}" if leash else ''), dis,
                       leash))

    def report(label, p, own_group=None):
        hits = []
        for q, grp, text, dis, leash in things:
            if own_group is not None and grp == own_group:
                continue
            d = d2(p, q) - leash
            if d < SHOW:
                hits.append((d, text, dis))
        hits.sort(key=lambda h: h[0])
        near = min([h[0] for h in hits], default=None)
        neard = min([h[0] for h in hits if h[2]], default=None)
        if neard is not None and neard < WARN:
            flag = 'DIS'
        elif near is not None and near < R:
            flag = 'FAIL'
        elif near is not None and near < WARN:
            flag = 'WARN'
        else:
            flag = 'ok'
        totals[flag] = totals.get(flag, 0) + 1
        print(f'  {flag:4} {label}  nearest {near and round(near)}  nearest disabler {neard and round(neard)}')
        for d, t, dis in hits:
            if d < WARN or (dis and d < SHOW):
                print(f"        {round(d):6} {t}" + (f"  DISABLER: {'; '.join(f'{name(m)} {why}' for m, why in dis)}"
                                                      if dis else ''))

    for a in talk:
        p = (a['position']['x'], a['position']['y'])
        report(f"giver actor {a['actor_index']} npc {a['npc_id']} {name(a['monster_id'])} grp {a['group']} at {p}",
               p, a['group'])
    for n, at in arrivals(stem, fname, st):
        report(f"arrival {n} at {tuple(at[:2])}", at)
        kind = check_arrivals.arrival_kind(WORLD, n.split(' = '), fname)
        for h in check_arrivals.first_fight(WORLD, sc, fname, at, KEPT_GROUPS, kind=kind):
            flag = 'KEPT' if h.get('kept') else 'FF' if h['level'] == 'error' else 'FFW'
            totals.setdefault(flag, 0)
            totals[flag] += 1
            print(f"  {flag:4} first fight (D-15, D-133, D-142): {h['id']} {h['name']} group {h['group']} at "
                  f"({h['at'][0]}, {h['at'][1]}) {h['distance']} (2D) < {h['floor']} from {kind} arrival {n}"
                  + (' (shoots or casts)' if h['ranged'] else ''))
    sketch = Path(_REPO_ROOT) / 'devdocs/xeen/briefs' / stem[5:] / 'L4/sketch.yml'
    if sketch.exists():
        for s, link, d in check_arrivals.road_setbacks(sc, check_arrivals.sketch_roads(str(sketch))):
            totals['ROAD'] += 1
            print(f"  ROAD spawn {s['spawn_index']} idx {s['index']} at ({s['position']['x']}, {s['position']['y']}) "
                  f"{d} from the road, lane or path {link} (D-142, D-157: 1,024)")
print('totals', totals)
sys.exit(1 if totals['FF'] else 0)
