#!/usr/bin/env python3
"""D-85 / D-87 check (A6 s31): talking givers and every arrival point of A6's maps against hostile spawn markers and
placed actors, with D-87's ranged-disabler kind filter.

Usage: d85.py [maps_dir] [stems...]

Arrival points: the studio's named arrivals (start, edges, falls, dungeon exits), and from the world tables the edge
spans' set-down points, mirrors, Town Portal points and coach/boat/dock arrivals into the map.

A ranged disabler (D-87.3): a monster row with Stone, Curse, Paralyze, Asleep, Insane, Afraid, Uncon, Dead or Errad as
its attack bonus on an attack with a missile (attack 1's missile column), or a Paralyze / Finger of Death spell. A spawn
marker counts if any monster its slot can roll qualifies: slots 1-3 roll the family's tiers A-C (map_stats Dif; every
tier counts, MAW rolls all three), slots 4-12 a fixed tier. A ranged disabler within 5,888 fails; any other kind keeps
D-85's 5,120 / 5,888 report (melee kinds are warnings only, D-87.4).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(_REPO_ROOT + '/assets_dev')
XT = ROOT / 'worlds/xeen/data_tables'
MAPS = Path(sys.argv[1]) if len(sys.argv) > 1 and '/' in sys.argv[1] else ROOT / 'worlds/xeen/maps'
STEMS = [a for a in sys.argv[1:] if '/' not in a] or \
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


totals = {'DIS': 0, 'FAIL': 0, 'WARN': 0}
for stem in STEMS:
    scp = MAPS / f'{stem}.scene.yml'
    if not scp.exists():
        print(f'== {stem}: no scene')
        continue
    sc = yaml.load(open(scp), Loader=L)
    st = yaml.load(open(MAPS / f'{stem}.studio.yml'), Loader=L)
    fname = next((k for k in STATS if k.startswith(stem + '.')), stem)
    actors = sc['initial_state'].get('actors') or []
    spawns = [s for s in (sc.get('spawns') or []) if s.get('type_id') == 3]
    talk = [a for a in actors if a.get('npc_id')]
    others = [a for a in actors if not a.get('npc_id')]
    print(f'== {stem} ({fname}): {len(actors)} actors ({len(talk)} talking), {len(spawns)} monster markers; '
          f'slots {STATS.get(fname, (0, []))[1]}')
    things = []
    for s in spawns:
        rs = slot_rows(fname, s['index'])
        dis = [(m, disabler(m)) for m in rs if disabler(m)]
        things.append(((s['position']['x'], s['position']['y']), None,
                       f"marker {s['spawn_index']} idx {s['index']} grp {s['group']} "
                       f"({s['position']['x']}, {s['position']['y']}) [{'/'.join(name(m) for m in rs)}]", dis))
    for a in others:
        m = a['monster_id']
        dis = [(m, disabler(m))] if disabler(m) else []
        things.append(((a['position']['x'], a['position']['y']), a['group'],
                       f"actor {a['actor_index']} {name(m)} ({m}) grp {a['group']} hos {a.get('hostility_type')} "
                       f"({a['position']['x']}, {a['position']['y']})", dis))

    def report(label, p, own_group=None):
        hits = []
        for q, grp, text, dis in things:
            if own_group is not None and grp == own_group:
                continue
            d = d2(p, q)
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
print('totals', totals)
