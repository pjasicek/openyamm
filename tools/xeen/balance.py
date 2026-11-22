#!/usr/bin/env python3
"""Xeen balance recount (ROADMAP 5.9; the successor of output/xeen_review/combat/proposed.py).

Per map and per act: monsters at load, their levels and kill XP per member (four members), chests, against the adopted
table of MAPS.md section 0; quest XP per act from A3's quest files (source/quests/*.yml, the `xp` effects and once-per-character
`AddValue(Experience, n)` hooks, repeatable topics and the `alternative: true` branch of each exclusive choice left out: one route per choice) and from A3's NPC
files (source/npcs/*.yml, in the act of each file's map: `xp` effects and once-per-character `AddValue(Experience, n)`
hooks). A map, an act or a group of maps more than 15 % off its kill XP is marked.

    python3 tools/xeen/balance.py                        the maps installed in assets_dev/worlds/xeen/maps/
    python3 tools/xeen/balance.py --maps-dir output/studio_play/xeen_root/worlds/mm7/maps    a scratch root
    python3 tools/xeen/balance.py --out report.md        also write the report to a file
    python3 tools/xeen/balance.py --detail               also list, per map, the monsters behind its kill XP

What it counts, per installed map (`<stem>.scene.yml`):
- placed actors (initial_state.actors, by their monster row), townsfolk left out (pictures of the peasant, guard,
  noble and merchant families, the z-rows, and rows named Peasant, Guard, Nobleman or Merchant), and so is every actor
  with an npc_id (a named character such as Ligono, not a kill), and every row friendly to the party in the world's
  relations.yml (Castle Burlock's King's Guards, Crodo), except a map's `count_friendly` rows (map_rows.yml: a
  peaceful group whose war route the budget counts, DD-24's People, D-47);
- traps: placed rows listed in the map's `traps` (source/map_rows.yml), deliberate traps far above the map's band,
  are left out of the map's own count and counted, in a column of their own, in the act of the quest that asks for the
  kill (`quest:`, that quest file's `act`), or with no quest in the first act whose leaving party level (MAPS.md
  section 0) is at least 60 % of the trap's level (DECISIONS D-1.2);
- act regions: placed actors and outdoor markers inside a map's `act_regions` (map_rows.yml) count in that act, beside
  the traps (X5's east pocket in Act II), and so do a map's `act_rows`, placed or from a marker (X7's south orcs in
  Act I);
- spawn markers: outdoors the scene's `spawns` (index 1-3 a slot whose tier follows the slot's Dif, 4-12 a fixed
  tier); indoors the map project's objects.yml `spawns` (devdocs/xeen/briefs/<key>/L4/; slot and tier; `kind: item`
  spawns left out), as the BLV's
  spawn points are not read here. A marker brings the middle of its slot's group range (map_stats).
- monster rows from the engine tables, MM9's and the world's generated ones (data_tables/monster_data.txt); map_stats
  rows from the world's generated table.
Random-tier markers take the game's tier weights by Dif; the count is the expectation, not one roll.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import xeenlib  # noqa: E402

# The game's tier weights for a random-tier marker by its slot's Dif (IndoorWorldRuntime.cpp
# IndoorEncounterDifficultyTierWeights); a fixed-tier marker (index 4-12) still brings a whole group.
DIF_MIX = {0: (1, 0, 0), 1: (0.9, 0.08, 0.02), 2: (0.7, 0.2, 0.1), 3: (0.5, 0.3, 0.2), 4: (0.3, 0.4, 0.3),
           5: (0.1, 0.5, 0.4)}
TOWNSFOLK = re.compile(r'^(peasant|guard |nobleman|merchant|z|mm9 \d+ (commoner|town|shopkeeper|prisoner))', re.I)
# Engine rows placed as townsfolk whatever their picture (MM7's town guard 404 is a Swordsman, row 49 a vampire peasant).
TOWNSFOLK_NAMES = re.compile(r'^(peasant|guard|nobleman|noblewoman|merchant)$', re.I)
ACTS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'optional']
# The optional content is spelled three ways: MAPS §0 `opt.`, the quest files `opt`, maps.yml `optional`.
OPTIONAL_ACTS = {'opt', 'opt.', 'optional'}


def act_key(value):
    """An act name as the act table keys it (`optional` for every spelling of the optional content)."""
    text = str(value).strip()
    return 'optional' if text.lower() in OPTIONAL_ACTS else text
MAP_KEY = re.compile(r'\b((?:XD|DD|FD)-\d\d[A-C]?|X\d|D\d|P\d)\b')
TOLERANCE = 0.15
# Acts whose counted quest XP a decider accepted over the 1.12 trigger and closed at that figure: any later addition
# needs an equal trim, and a recount above it goes back to a decider (D-60: Act IV, the Soul Waters' 3k counted).
CLOSED_QUEST_XP = {'IV': (179500, '179.5k of 160k (1.12), accepted, D-60; closed: additions need an equal trim')}


def monster_rows():
    """id -> row and picture -> row over the engine, MM9 and Xeen monster tables."""
    by_id, by_picture = {}, {}
    sources = [xeenlib.engine_table('monster_data.txt')]
    for path in (xeenlib.WORLDS / 'mm9' / 'data_tables' / 'monster_data.txt',
                 xeenlib.DATA_TABLES / 'monster_data.txt'):
        if path.exists():
            sources.append(xeenlib.read_tsv(path))
    for rows in sources:
        for row in rows:
            row_id = xeenlib.parse_int(xeenlib.cell(row, 0))
            if row_id is None:
                continue
            info = {'id': row_id, 'name': xeenlib.cell(row, 1), 'picture': xeenlib.cell(row, 2),
                    'level': xeenlib.parse_int(xeenlib.cell(row, 3)) or 0,
                    'xp': xeenlib.parse_int(xeenlib.cell(row, 6)) or 0}
            by_id[row_id] = info
            by_picture.setdefault(info['picture'].lower(), info)
    return by_id, by_picture


def trap_rows():
    """Map key -> {monster row id: the act of the quest that asks for the kill, or None} (map_rows.yml `traps`)."""
    data = xeenlib.load_yaml(xeenlib.SOURCE / 'map_rows.yml') or {}
    result = {}
    for key, extra in (data.get('maps') or {}).items():
        for trap in (extra or {}).get('traps') or []:
            act = act_key(trap['act']) if trap.get('act') else None   # a decision's act wins (D-36: D4's octopods)
            if act is None and trap.get('quest'):
                quest = xeenlib.load_yaml(xeenlib.SOURCE / 'quests' / f"{trap['quest'].lower()}.yml") or {}
                act = act_key(quest.get('act')) if quest.get('act') else None
            result.setdefault(key, {})[int(trap['monster'])] = act
    return result


def act_rows():
    """Map key -> {monster row id: act} (map_rows.yml `act_rows`: XD-13's stage 3 in Act IV, X7's south orcs in Act I;
    placed actors and spawn markers alike)."""
    data = xeenlib.load_yaml(xeenlib.SOURCE / 'map_rows.yml') or {}
    result = {}
    for key, extra in (data.get('maps') or {}).items():
        for act, ids in ((extra or {}).get('act_rows') or {}).items():
            for row_id in ids:
                result.setdefault(key, {})[int(row_id)] = str(act)
    return result


def act_regions():
    """Map key -> [region dict with act and optional x_min, x_max, y_min, y_max] (map_rows.yml `act_regions`)."""
    data = xeenlib.load_yaml(xeenlib.SOURCE / 'map_rows.yml') or {}
    return {key: list((extra or {}).get('act_regions') or []) for key, extra in (data.get('maps') or {}).items()
            if (extra or {}).get('act_regions')}


def region_act(regions, position):
    """The act of the first region holding the position ({x, y} or [x, y, z]), or None."""
    if not regions or position is None:
        return None
    if isinstance(position, dict):
        x, y, z = position.get('x'), position.get('y'), position.get('z', 0)
    else:
        x, y, z = position[0], position[1], position[2] if len(position) > 2 else 0
    for region in regions:
        if (x >= region.get('x_min', x) and x <= region.get('x_max', x) and y >= region.get('y_min', y)
                and y <= region.get('y_max', y) and z >= region.get('z_min', z) and z <= region.get('z_max', z)):
            return act_key(region['act'])
    return None


def friendly_rows():
    """Monster row ids whose faction is friendly to the party (the world's relations.yml)."""
    data = xeenlib.load_yaml(xeenlib.WORLD / 'relations.yml') or {}
    # The relation at load: a rule that switches on a quest bit (after_qbit, until_qbit) does not decide the count.
    friendly = {entry.get('from') for entry in data.get('relations') or []
                if entry.get('to') == 'party' and entry.get('relation') == 'friendly'
                and 'after_qbit' not in entry and 'until_qbit' not in entry}
    ids = set()
    for name, faction in (data.get('factions') or {}).items():
        if name not in friendly:
            continue
        for item in faction.get('monsters') or []:
            low, _, high = str(item).partition('-')
            ids.update(range(int(low), int(high or low) + 1))
    return ids


def act_levels():
    """Act -> highest party level on leaving any of its maps (MAPS.md section 0), in act order."""
    text = (xeenlib.ROOT / 'devdocs' / 'xeen' / 'MAPS.md').read_text(encoding='utf-8')
    section = text.split('## 0.', 1)[1].split('\n## ', 1)[0]
    top = {}
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        match = re.search(r'(\d+)\s*→\s*(\d+)', cells[2]) if len(cells) > 2 else None
        if match and cells[1] in ACTS:
            top[cells[1]] = max(top.get(cells[1], 0), int(match.group(2)))
    return [(act, top[act]) for act in ACTS if act in top]


def act_for_level(level, bands):
    """The first act whose leaving party level is at least 60 % of the level (DECISIONS D-1.2)."""
    for act, top in bands:
        if top >= 0.6 * level:
            return act
    return bands[-1][0]


def map_stats_rows():
    path = xeenlib.DATA_TABLES / 'map_stats.txt'
    rows = {}
    if not path.exists():
        return rows
    for row in xeenlib.read_tsv(path):
        if xeenlib.parse_int(xeenlib.cell(row, 0)) is None:
            continue
        slots = []
        for start in (16, 20, 24):
            name = xeenlib.cell(row, start + 1)
            counts = [int(value) for value in re.findall(r'\d+', xeenlib.cell(row, start + 3))] or [0, 0]
            slots.append({'name': name if name not in ('', '0') else '',
                          'dif': xeenlib.parse_int(xeenlib.cell(row, start + 2)) or 0,
                          'group': sum(counts[:2]) / len(counts[:2])})
        rows[xeenlib.cell(row, 2).lower()] = {'treasure': xeenlib.cell(row, 11), 'slots': slots}
    return rows


def targets():
    """MAPS.md section 0: per row (one map or a group), act, monster count and kill XP per member."""
    text = (xeenlib.ROOT / 'devdocs' / 'xeen' / 'MAPS.md').read_text(encoding='utf-8')
    section = text.split('## 0.', 1)[1].split('\n## ', 1)[0]
    result = []
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        # The kill XP cell starts with the row's figure ("3.7k", or "5.6k: Act II 1.9k, Act IV 3.7k" for a row split
        # between acts).
        xp_match = re.match(r'(\d+(?:\.\d+)?)k\b', cells[7]) if len(cells) >= 8 else None
        if not xp_match:
            continue
        keys = MAP_KEY.findall(cells[0])
        if 'P1' in keys and 'P1–P4' in cells[0]:
            keys = ['P1', 'P2', 'P3', 'P4']
        if not keys:
            continue
        numbers = re.findall(r'\d+', cells[6])
        monsters = eval_times(cells[6]) if '×' in cells[6] else int(numbers[0]) if numbers else 0
        # A row split between acts ("5.6k: Act II 1.9k, Act IV 3.7k"; monsters "28: Act II 15, Act IV 10"): the first
        # part is the map's own target, the others parts counted in their act (the map's act_rows, map_rows.yml).
        parts = re.findall(r'Act ([IV]+) (\d+(?:\.\d+)?)k', cells[7])
        if parts:
            counts = dict(re.findall(r'Act ([IV]+) (\d+)', cells[6]))
            for index, (act, xp) in enumerate(parts):
                result.append({'label': cells[0] + (f' (Act {act} part)' if index else ''), 'keys': keys, 'act': act,
                               'monsters': int(counts.get(act, 0)), 'xp': float(xp) * 1000, 'part': index > 0})
            continue
        result.append({'label': cells[0], 'keys': keys, 'act': act_key(cells[1]), 'monsters': monsters,
                       'xp': float(xp_match.group(1)) * 1000})
    return result


def expand_pockets(rows, registry_keys):
    """A row naming a split dungeon by its number ("DD-10, DD-11") covers its pockets in maps.yml (DD-10A, DD-10B, ...)
    except those another row names itself (DD-10C, moved to Act V by D-27)."""
    known = set(registry_keys)
    named = {key for row in rows for key in row['keys'] if key in known}
    for row in rows:
        keys = []
        for key in row['keys']:
            if key in known:
                keys.append(key)
            else:
                keys += [other for other in registry_keys if re.fullmatch(re.escape(key) + '[A-Z]', other)
                         and other not in named]
        row['keys'] = keys or row['keys']
    return rows


def eval_times(text):
    match = re.search(r'(\d+)\s*×\s*(\d+)', text)
    return int(match.group(1)) * int(match.group(2)) if match else 0


def project_spawns(key):
    path = xeenlib.ROOT / 'devdocs' / 'xeen' / 'briefs' / key.lower().replace('-', '') / 'L4' / 'objects.yml'
    if not path.exists():
        return None
    data = xeenlib.load_yaml(path) or {}
    # A spawn of `kind: item` places treasure, not monsters (A7, 2026-11-20).
    return [(spawn.get('slot', 1), spawn.get('tier')) for spawn in data.get('spawns') or []
            if spawn.get('kind', 'monster') == 'monster']


def count_map(entry, scene, stats, by_id, by_picture, detail=None, traps=(), trapped=None, regions=(), elsewhere=None,
              friendly=frozenset(), rows_in_acts=None, most_rows=frozenset(), most=None):
    """(monsters, kill XP for the party, chests, levels seen, notes). most: a list filled with the party XP of each
    placed actor whose row is in most_rows (map_rows.yml `most_experience`), left off the route. detail: a dict filled with
    (placed or spawned, monster name, level) -> [count, party XP]; trapped: a list filled with the (level, party XP,
    quest act or None) of each placed actor whose row is in traps (row id -> quest act); elsewhere: a dict filled with
    act -> [count, party XP] for the monsters inside one of the map's act regions."""
    detail = {} if detail is None else detail
    trapped = [] if trapped is None else trapped
    elsewhere = {} if elsewhere is None else elsewhere
    monsters = 0.0
    party_xp = 0.0
    levels = []
    notes = []
    for actor in ((scene.get('initial_state') or {}).get('actors') or []):
        info = by_id.get(actor.get('monster_info_id') or actor.get('monster_id'))
        if info is None or TOWNSFOLK.match(info['picture']) or TOWNSFOLK_NAMES.match(info['name']):
            continue
        if info['id'] in most_rows and most is not None and not actor.get('npc_id'):
            # Off the counted route, peaceful or not (D7's Sky Bandits and the Megadragon, D-58).
            most.append(info['xp'])
            cell = detail.setdefault(('most experience', info['name'], info['level']), [0.0, 0.0])
            cell[0] += 1
            cell[1] += info['xp']
            continue
        if actor.get('npc_id') or info['id'] in friendly:
            continue
        if info['id'] in traps:
            trapped.append((info['level'], info['xp'], traps[info['id']]))
            cell = detail.setdefault(('trap', info['name'], info['level']), [0.0, 0.0])
            cell[0] += 1
            cell[1] += info['xp']
            continue
        act = (rows_in_acts or {}).get(info['id']) or region_act(regions, actor.get('position'))
        if act is not None:
            cell = elsewhere.setdefault(act, [0.0, 0.0])
            cell[0] += 1
            cell[1] += info['xp']
            cell = detail.setdefault((f'act {act}', info['name'], info['level']), [0.0, 0.0])
            cell[0] += 1
            cell[1] += info['xp']
            continue
        monsters += 1
        party_xp += info['xp']
        levels.append(info['level'])
        cell = detail.setdefault(('placed', info['name'], info['level']), [0.0, 0.0])
        cell[0] += 1
        cell[1] += info['xp']

    row = stats.get(entry['stem'].lower())
    if entry['kind'] == 'odm':
        markers = []
        for spawn in scene.get('spawns') or []:
            if spawn.get('type_id') != 3:
                continue
            index = spawn.get('index', 0)
            act = region_act(regions, spawn.get('position'))
            if 1 <= index <= 3:
                markers.append((index, None, act))
            elif 4 <= index <= 12:
                markers.append(((index - 4) % 3 + 1, 'abc'[(index - 4) // 3], act))
    else:
        markers = [(slot, tier, None) for slot, tier in project_spawns(entry['key']) or []]
        if not markers and not monsters and not elsewhere and not trapped:
            notes.append('no project spawns read')
    if markers and row is None:
        notes.append('no map_stats row: spawns not counted')
        markers = []
    for slot_number, tier, act in markers:
        slot = row['slots'][slot_number - 1]
        if not slot['name']:
            notes.append(f'spawn on empty slot {slot_number}')
            continue
        mix = {'a': (1, 0, 0), 'b': (0, 1, 0), 'c': (0, 0, 1)}.get(str(tier).lower()) if tier else None
        mix = mix or DIF_MIX.get(slot['dif'], DIF_MIX[1])
        for share, letter in zip(mix, 'ABC'):
            if share <= 0:
                continue
            info = by_picture.get(f"{slot['name']} {letter}".lower())
            if info is None:
                notes.append(f"no monster row {slot['name']} {letter}")
                continue
            count = share * slot['group']
            # A row counted in another act (map_rows.yml `act_rows`) counts there from a marker too (X7's south
            # orcs in Act I, D-40); a marker inside an act region keeps the region's act.
            row_act = act or (rows_in_acts or {}).get(info['id'])
            if row_act is not None:
                cell = elsewhere.setdefault(row_act, [0.0, 0.0])
                cell[0] += count
                cell[1] += count * info['xp']
                cell = detail.setdefault((f'act {row_act}', info['name'], info['level']), [0.0, 0.0])
                cell[0] += count
                cell[1] += count * info['xp']
                continue
            monsters += count
            party_xp += count * info['xp']
            levels.append(info['level'])
            cell = detail.setdefault(('spawned', info['name'], info['level']), [0.0, 0.0])
            cell[0] += count
            cell[1] += count * info['xp']
    chests = len(scene.get('loot_containers') or (scene.get('initial_state') or {}).get('chests') or [])
    return monsters, party_xp, chests, levels, notes


def experience_in_lua(text):
    """The experience of a hook's `AddValue(Experience, n)` lines."""
    return sum(int(n) for n in re.findall(r'AddValue\(\s*Experience\s*,\s*(\d+)\s*\)', text))


def quest_xp_by_act():
    totals = defaultdict(float)
    directory = xeenlib.SOURCE / 'quests'
    if not directory.exists():
        return totals, 0
    files = 0

    def walk(node):
        if isinstance(node, dict):
            # `alternative: true` marks the other branch of an exclusive choice (Q-C26's second skull, Q-D16's throne,
            # Q-D17's oath): a party takes one route, so only the unmarked one counts (A3's route rule, 2026-11-21).
            if node.get('repeatable') or node.get('alternative') is True:
                return 0
            total = 0
            for key, value in node.items():
                if key == 'rewards':
                    continue
                if key == 'xp' and isinstance(value, (int, float)):
                    total += value
                elif key == 'lua' and isinstance(value, str):
                    # A hook paying the clicking member once per character (the Tome, X9's crystals, DD-12's Soul
                    # Waters): every member takes it, as in the NPC files (D-59).
                    total += experience_in_lua(value)
                else:
                    total += walk(value)
            return total
        if isinstance(node, list):
            return sum(walk(item) for item in node)
        return 0

    for path in sorted(directory.glob('*.yml')):
        data = xeenlib.load_yaml(path) or {}
        files += 1
        totals[act_key(data.get('act', '?'))] += walk(data)
    return totals, files


def npc_xp_by_act():
    """XP per member from A3's NPC files (source/npcs/*.yml: a map's hooks, D5's lair, X9's nests), in the act of the
    file's `map` (maps.yml): the `xp` effects (every member) and the `AddValue(Experience, n)` lines of a hook that
    pays the clicking member once per character (D6's Books of the Dead, XD-17's well), as every member takes it."""
    totals = defaultdict(float)
    directory = xeenlib.SOURCE / 'npcs'
    acts = {entry.get('key'): act_key(entry.get('act')) for entry in
            (xeenlib.load_yaml(xeenlib.SOURCE / 'maps.yml') or {}).get('maps') or []}
    files = 0

    def walk(node):
        if isinstance(node, dict):
            if node.get('repeatable') or node.get('alternative') is True:
                return 0
            total = 0
            for key, value in node.items():
                if key == 'xp' and isinstance(value, (int, float)):
                    total += value
                elif key == 'lua' and isinstance(value, str):
                    total += experience_in_lua(value)
                else:
                    total += walk(value)
            return total
        if isinstance(node, list):
            return sum(walk(item) for item in node)
        return 0

    for path in sorted(directory.glob('*.yml')) if directory.exists() else []:
        data = xeenlib.load_yaml(path) or {}
        xp = walk(data)
        if xp:
            files += 1
            totals[acts.get(data.get('map'), '?')] += xp
    return totals, files


def xp_choices_by_act():
    """The experience-or-goods choices (map_rows.yml `xp_choices`, per map: {<quest id>.<hook>: times}, Q-D27's wish
    lamps, D-53) taken as experience at every chance: times x the highest `xp` under that hook of A3's quest file, in
    the act of the map. The counted route leaves these `alternative` branches out; the act table's "most experience"
    column adds them (D-53: that line too stays within 15 % of the QUESTS budget)."""
    totals = defaultdict(float)
    listed = []
    acts = {entry.get('key'): act_key(entry.get('act')) for entry in
            (xeenlib.load_yaml(xeenlib.SOURCE / 'maps.yml') or {}).get('maps') or []}
    quests = {}
    for path in sorted((xeenlib.SOURCE / 'quests').glob('*.yml')):
        data = xeenlib.load_yaml(path) or {}
        quests[str(data.get('id'))] = data

    def find(node, name):
        if isinstance(node, dict):
            if name in node and isinstance(node[name], dict):
                return node[name]
            for value in node.values():
                found = find(value, name)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = find(item, name)
                if found is not None:
                    return found
        return None

    def highest_xp(node):
        if isinstance(node, dict):
            values = [value for key, value in node.items() if key == 'xp' and isinstance(value, (int, float))]
            return max(values + [highest_xp(value) for key, value in node.items() if key != 'xp'] + [0])
        if isinstance(node, list):
            return max([highest_xp(item) for item in node] + [0])
        return 0

    per_map = (xeenlib.load_yaml(xeenlib.SOURCE / 'map_rows.yml') or {}).get('maps') or {}
    for key, extra in per_map.items():
        for choice, times in (extra.get('xp_choices') or {}).items():
            quest_id, _, hook = str(choice).partition('.')
            node = find(quests.get(quest_id), hook) if quest_id in quests and hook else None
            if node is None:
                raise SystemExit(f'map_rows.yml {key} xp_choices: no {hook!r} in quest {quest_id}')
            xp = highest_xp(node)
            totals[acts.get(key, '?')] += xp * int(times)
            listed.append(f'{key} {choice} {int(times)} x {xp:,.0f}')
    return totals, listed


def quest_budgets():
    """QUESTS.md: the act quest budgets per member ("I 16.5k, II 83k, ...")."""
    text = ' '.join((xeenlib.ROOT / 'devdocs' / 'xeen' / 'QUESTS.md').read_text(encoding='utf-8').split())
    match = re.search(r'budgets per member: (.*?)\(MAPS', text)
    if not match:
        return {}
    return {act: float(value) * 1000 for act, value in re.findall(r'\b([IV]+|optional) (\d+(?:\.\d+)?)k', match.group(1))}


def verdict(actual, target):
    if not target:
        return ''
    ratio = actual / target
    return f'{ratio:.2f}' + (' **off**' if abs(ratio - 1) > TOLERANCE else '')


# ---------------------------------------------------------------------- stat gates and the gem budget (D-68 Q1.5)
STATS = ('Might', 'Intellect', 'Personality', 'Endurance', 'Speed', 'Accuracy', 'Luck')
STAT = r'(Might|Intellect|Personality|Endurance|Speed|Accuracy|Luck)'
GATE_RE = re.compile(r'IsAtLeast\(\s*(Base|Actual)' + STAT + r'\s*,\s*(\d+)\s*\)')
EFFECT_RE = re.compile(r'AddValue\(\s*(Base)?' + STAT + r'(Bonus)?\s*,\s*(\d+)\s*\)')
LOOP_RE = re.compile(r'ipairs\(\{([^}]*)\}\)\s*do\s*AddValue\(\s*stat\s*,\s*(\d+)\s*\)')
EACH_RE = re.compile(r'giveEachOnce\(\s*\d+\s*,\s*Base' + STAT + r'\s*,\s*(\d+)\s*\)')
# The boost potions an event hands over (MM7's Might Boost 240 ... Accuracy Boost 245, Luck Boost 255): +3 x power to
# one statistic for 30 minutes per point of power, one at a time (a second drink replaces the buff).
BOOST_RE = re.compile(r'(?:SetHeldItem|GiveItem)\(\s*(24[0-5]|255)\s*,\s*\{\s*bonus\s*=\s*(\d+)')
BOOSTS = {240: 'Might', 241: 'Intellect', 242: 'Personality', 243: 'Endurance', 244: 'Speed', 245: 'Accuracy',
          255: 'Luck'}
PAY_RE = re.compile(r'payGems\(\s*(\d+)\s*\)')
# Temporary effects (D-70 Q2): an AddValue on a `*Bonus` (statistics, ArmorClassBonus, the resistances' bonuses) or a
# level, directly, in a loop over such names or through Xeen.giveEachOnce. Every one is guarded once a day for the
# party by Xeen.usedToday; capped HP and SP restorations are not temporary effects.
TEMP_RE = re.compile(r'AddValue\(\s*(\w*Bonus|Level\w*)\s*,'
                     r'|ipairs\(\{[^}]*\w+Bonus[^}]*\}\)\s*do\s*AddValue\(\s*stat\s*,'
                     r'|giveEachOnce\(\s*\d+\s*,\s*\w+Bonus\s*,')
# Party creation (game/ui/screens/NewGameScreen.cpp): 15 bonus points, a statistic lowered at most 2 below its race's
# base; race bases, maxima and steps from the engine's class_starting_stats.txt.
CREATION_POOL, CREATION_DROP = 15, 2
SHORTFALL_ALLOWED = 10   # D-59's standard (D-68 Q1.5): within 10 one item or one buff covers
# Per gate: the maps of the gate's own act whose sources come before it on the route (sources of earlier acts always
# do; the gate's own map counts its own temporary help), and the far temporary help a party can carry to the gate
# without a rest (map key, hook or event label, route). The far help is listed as extra and not counted in the value:
# a route no in-game text explains does not carry a main-quest gate (D-70 Q1). Keyed `<map> <label>` as the table
# prints it.
GATE_ROUTE = {
    'X9 m34.*': {
        'before': ('X7', 'D5', 'D6', 'XD-16', 'XD-17', 'DD-08', 'DD-10C', 'DD-15', 'DD-16', 'DD-17', 'DD-21', 'DD-24',
                   'DD-25'),
        # No outdoor edge on the way: an edge walk rests the party (TravelRuntime.cpp), which ends the buffs. D5 has
        # no mirror; its grate leads through DD-18 to Sandcaster's (D3) mirror, Rivercity's (X2) mirror, XD-12, X9.
        'temp': [('D5', 'd5.shrine', "D5's Shrine of Great Power, through DD-18 to Sandcaster's mirror, Rivercity's "
                                     "mirror, XD-12's cloud stair; no edge walk (D-68)"),
                 ('D5', 'd5.fountain_might', "D5's Fountain of Might, the same way (D-68)")],
        'note': 'Act V before the carnival: every Act V map but XD-19 (behind the gate). X9\'s Dragon Clouds are '
                "Q-F1's (after M39, optional), so the Well of Fantastic Skill is not reachable here.",
    },
    'DD-21 q-d23.dead_food': {'before': ('D5', 'D6'), 'temp': [], 'note': ''},
}
# Gem payments of optional quests that a promotion cannot be reached without (D-75 case 3), keyed as GATE_ROUTE: the
# act whose fixed gems all come before the payment (the main chain's point where the promotion chain branches) and the
# promotion. Report-only: a row short of gems goes to a decider, it does not fail `--gates` (only main payments do).
# D-81: such a row also counts fixed choices (the `alternative: true` gem gives the party can pick before the payment,
# choice_gems), the fewest uses that close its gap; main payments stay fixed-only.
PROMOTION_PAYMENTS = {
    'X7 q-c25.*': {'after': 'V', 'promotion': 'Dragon to Great Wyrm',
                   'note': "the Dragon Tax at XD-18's mouth; reached from main 83 (after Castle Xeen, the end of "
                           "Act V, level 50; promotions 67)"},
}


def stats_in(text):
    """[(statistic, amount, 'base' or 'bonus')] of a script's AddValue lines, its seven-statistic loops and its
    Xeen.giveEachOnce calls."""
    found = []
    for match in EFFECT_RE.finditer(text):
        if match.group(1) or match.group(3):
            found.append((match.group(2), int(match.group(4)), 'base' if match.group(1) else 'bonus'))
    for match in LOOP_RE.finditer(text):
        for name in re.findall(r'Base' + STAT, match.group(1)):
            found.append((name, int(match.group(2)), 'base'))
    for match in EACH_RE.finditer(text):
        found.append((match.group(1), int(match.group(2)), 'base'))
    return found


def source_scope(text):
    """How often a device gives: random (excluded), gems (paid, listed apart), each (once per character), daily, once
    (once for the party), unguarded (every click)."""
    if 'RandomBetween' in text:
        return 'random'
    if 'payGems' in text:
        return 'gems'
    if 'giveEachOnce' in text or 'PlayerBit' in text:
        return 'each'
    if re.search(r'usedToday|markToday|tomorrow|today', text):
        return 'daily'
    if re.search(r'MapVar|QBit|SetMapVar|once', text):
        return 'once'
    return 'unguarded'


def act_rank(value):
    """An act's place in ACTS; a range (`II-IV`) by its first act, `any` first."""
    text = act_key(value)
    if text in ACTS:
        return ACTS.index(text)
    first = re.split(r'[-–]', text)[0].strip()
    return ACTS.index(first) if first in ACTS else 0


def best_creation():
    """Statistic -> (best value a new character can have, [races]) over the races the world's new-game card offers."""
    continents = xeenlib.load_yaml(xeenlib.DATA_TABLES / 'new_game_continents.yml') or {}
    card = next((entry for entry in continents.get('new_game_continents') or [] if entry.get('key') == xeenlib.WORLD_ID),
                {})
    allowed = set(card.get('available_race_ids') or [])
    rows = xeenlib.engine_table('class_starting_stats.txt')
    header = rows[0]
    races = {}
    for column, name in enumerate(header[1:], 1):
        match = re.match(r'(.*)\((\d+)\)', name)
        if match and int(match.group(2)) in allowed:
            races[column] = match.group(1).strip()
    rules = {column: {} for column in races}
    for index, row in enumerate(rows):
        if row and row[0] in STATS and index + 1 < len(rows):
            for column in races:
                base_text, _, top_text = xeenlib.cell(row, column).partition('/')
                base, top = int(base_text), int(top_text or 25)
                add_text, _, drop_text = xeenlib.cell(rows[index + 1], column).partition('/')
                add = int(add_text)
                drop = int(drop_text) if drop_text else (1 if base > 11 else add)
                rules[column][row[0]] = (base, top, add, drop)
    best = {}
    for column, name in races.items():
        for stat, (base, top, add, drop) in rules[column].items():
            # Every other statistic lowered as far as it goes; the points raise this one.
            points = CREATION_POOL + sum(other[2] * (CREATION_DROP // other[3]) for key, other in rules[column].items()
                                         if key != stat)
            value = base + min(points // drop, (top - base) // add) * add
            if value > best.get(stat, (0, []))[0]:
                best[stat] = (value, [name])
            elif value == best.get(stat, (0, []))[0]:
                best[stat][1].append(name)
    return best


def map_lua_events():
    """(map key, event label, script text) for every event of the installed map scripts (events/maps/*.lua)."""
    registry = (xeenlib.load_yaml(xeenlib.SOURCE / 'maps.yml') or {}).get('maps') or []
    keys = {entry['stem'].rsplit('.', 1)[0]: entry['key'] for entry in registry}
    for path in sorted((xeenlib.WORLD / 'events' / 'maps').glob('*.lua')):
        key = keys.get(path.stem)
        if key is None:
            continue
        label, lines, tag = None, [], None
        for line in path.read_text(encoding='utf-8').splitlines() + ['RegisterEvent(0, nil']:
            comment = re.match(r'-- evt:(\S+)', line)
            if comment:
                tag = comment.group(1)
            match = re.match(r'RegisterEvent\(\s*\d+\s*,\s*(?:"((?:[^"\\]|\\.)*)"|nil)', line)
            if match:
                if label is not None:
                    yield key, label, '\n'.join(lines)
                label, lines = match.group(1) or tag or '(event)', [line]
            elif label is not None:
                lines.append(line)


def quest_hook_nodes():
    """(source file, act, map key, hook label, hook node, quest kind) for each hook, topic and step of A3's quest and
    NPC files; the `alternative: true` branch of an exclusive choice and the `rewards` summary are left out."""
    registry = (xeenlib.load_yaml(xeenlib.SOURCE / 'maps.yml') or {}).get('maps') or []
    map_acts = {entry['key']: entry.get('act') for entry in registry}
    for directory in ('quests', 'npcs'):
        for path in sorted((xeenlib.SOURCE / directory).glob('*.yml')):
            data = xeenlib.load_yaml(path) or {}
            default_map = data.get('map') or (data.get('maps') or [None])[0]
            prefix = str(data.get('id') or path.stem).lower() if directory == 'quests' else path.stem
            for section, entries in data.items():
                if section in ('rewards', 'qbits', 'player_bits', 'autonotes', 'items') or not isinstance(entries,
                                                                                                         dict):
                    continue
                for name, node in entries.items():
                    if not isinstance(node, dict) or node.get('alternative') is True:
                        continue
                    key = node.get('map') or default_map
                    ranks = [act_rank(map_acts.get(key, 'I'))]
                    if data.get('act'):
                        ranks.append(act_rank(data['act']))   # a hook never fires before its quest's act
                    yield (path.relative_to(xeenlib.SOURCE), ACTS[max(ranks)], key, f'{prefix}.{name}', node,
                           data.get('kind'))


def hook_text(node):
    """Every Lua string and `stat`/`give` effect of a hook, alternative branches left out, as one text."""
    parts = []

    def walk(item):
        if isinstance(item, dict):
            if item.get('alternative') is True:
                return
            for key, value in item.items():
                if key == 'lua' and isinstance(value, str):
                    parts.append(value)
                elif key == 'stat' and isinstance(value, str) and 'value' in item:
                    parts.append(f'AddValue(Base{value.capitalize()}, {int(item["value"])})')
                elif key == 'give' and isinstance(value, str) and value.startswith('engine:'):
                    parts.append(f'GiveItem({value.split(":", 1)[1]})')
                elif key == 'once' and value is True:
                    parts.append('once')
                else:
                    walk(value)
        elif isinstance(item, list):
            for value in item:
                walk(value)

    walk(node)
    return '\n'.join(parts)


def gate_survey():
    """Stat gates, stat sources and gem flows over the installed map scripts and A3's quest and NPC files."""
    registry = (xeenlib.load_yaml(xeenlib.SOURCE / 'maps.yml') or {}).get('maps') or []
    map_acts = {entry['key']: act_key(entry.get('act')) for entry in registry}
    common = (xeenlib.WORLD / 'events' / 'common' / 'xeen_common.lua').read_text(encoding='utf-8')
    gems = {int(n) for n in re.findall(r'\d+', common.split('Xeen.GemItems = {', 1)[1].split('}', 1)[0])}
    gates, sources, boosts, pays, gifts = [], [], [], [], []

    def record(origin, act, key, label, text, kind=None):
        rank = act_rank(act)
        needs = [(m.group(1), m.group(2), int(m.group(3))) for m in GATE_RE.finditer(text)]
        effects = stats_in(text)
        for gate_kind, stat, value in needs:
            gates.append({'map': key, 'act': act, 'rank': rank, 'label': label, 'stat': stat, 'value': value,
                          'kind': gate_kind, 'origin': origin, 'gives': bool(effects)})
        scope = source_scope(text)
        for stat, amount, effect_kind in effects:
            sources.append({'map': key, 'act': act, 'rank': rank, 'label': label, 'stat': stat, 'amount': amount,
                            'kind': effect_kind, 'scope': scope, 'needs': needs, 'origin': origin,
                            'fee': 'IsAtLeast(Gold' in text or '{gold:' in text})
        for match in BOOST_RE.finditer(text):
            item_id, power = int(match.group(1)), int(match.group(2))
            boosts.append({'map': key, 'act': act, 'rank': rank, 'label': label, 'stat': BOOSTS[item_id],
                           'amount': 3 * power, 'origin': origin})
        paid = [int(n) for n in PAY_RE.findall(text)]
        if paid:
            pays.append({'map': key, 'act': act, 'rank': rank, 'label': label, 'gems': max(paid), 'kind': kind,
                         'origin': origin})
        given = [int(n) for n in re.findall(r'\bGiveItem\((\d+)\)', text) if int(n) in gems]
        if given:
            count = 1 if 'RandomBetween' in text and len(given) > 1 else len(given)
            gifts.append({'map': key, 'act': act, 'rank': rank, 'label': label, 'gems': count, 'origin': origin})

    for key, label, text in map_lua_events():
        # A map event that only calls a quest hook is counted with the hook.
        record(f'events/maps ({key})', map_acts.get(key, '?'), key, label, text)
    for origin, act, key, label, node, kind in quest_hook_nodes():
        record(str(origin), act, key, label, hook_text(node), kind)
    return gates, sources, boosts, pays, gifts, gems


def choice_gems(gems):
    """The fixed choices that hand over gems (D-81): each `alternative: true` hook of A3's quest and NPC files that gives
    gem items, with one use per place that offers it. A choice offered by Xeen.genieLamp is offered once by every lamp
    of its kind (xeen_common.lua's GenieKinds and GenieLamps, the lamp key's map prefix giving the lamp's map and act);
    any other once at its hook's map."""
    registry = (xeenlib.load_yaml(xeenlib.SOURCE / 'maps.yml') or {}).get('maps') or []
    map_acts = {entry['key']: act_key(entry.get('act')) for entry in registry}
    common = (xeenlib.WORLD / 'events' / 'common' / 'xeen_common.lua').read_text(encoding='utf-8')
    kinds_text = common.split('Xeen.GenieKinds = {', 1)[1].split('\nXeen.GenieLamps', 1)[0]
    lamps_text = common.split('Xeen.GenieLamps = {', 1)[1].split('\n}', 1)[0]
    kind_of_answer = {}
    for match in re.finditer(r'^    (\w+) = \{(.*?)^    \},', kinds_text, re.M | re.S):
        for label in re.findall(r'"([\w-]+\.\w+)"', match.group(2)):
            kind_of_answer[label] = match.group(1)
    lamps = [(name, (re.search(r'kind = "(\w+)"', body) or [None, 'wish'])[1])
             for name, body in re.findall(r'^    (\w+) = \{(.*?)\},?\s*$', lamps_text, re.M | re.S)]
    choices = []
    for directory in ('quests', 'npcs'):
        for path in sorted((xeenlib.SOURCE / directory).glob('*.yml')):
            data = xeenlib.load_yaml(path) or {}
            default_map = data.get('map') or (data.get('maps') or [None])[0]
            prefix = str(data.get('id') or path.stem).lower() if directory == 'quests' else path.stem
            for section, entries in data.items():
                if section in ('rewards', 'qbits', 'player_bits', 'autonotes', 'items') or not isinstance(entries,
                                                                                                         dict):
                    continue
                for name, node in entries.items():
                    if not isinstance(node, dict) or node.get('alternative') is not True:
                        continue
                    count = 0
                    for step in node.get('do') or []:
                        give = str(step.get('give', '')) if isinstance(step, dict) else ''
                        if give.startswith('engine:') and int(give.split(':', 1)[1]) in gems:
                            count += int(step.get('count', 1))
                        if isinstance(step, dict) and isinstance(step.get('lua'), str):
                            count += sum(1 for n in re.findall(r'\bGiveItem\((\d+)\)', step['lua'])
                                         if int(n) in gems)
                    if not count:
                        continue
                    label = f'{prefix}.{name}'
                    kind = kind_of_answer.get(label)
                    places = ([lamp.split('_', 1)[0].upper() for lamp, lamp_kind in lamps if lamp_kind == kind]
                              if kind else [node.get('map') or default_map])
                    for place in places:
                        act = map_acts.get(place, data.get('act') or 'I')
                        rank = max(act_rank(act), act_rank(data['act'])) if data.get('act') else act_rank(act)
                        choices.append({'map': place, 'rank': rank, 'label': label, 'gems': count,
                                        'origin': str(path.relative_to(xeenlib.SOURCE))})
    return choices


def guard_check():
    """Events and hooks with a temporary effect (TEMP_RE) and no `Xeen.usedToday` guard (D-70 Q2), with the lane
    that owns each: a map event its map's lane, a hook A3."""
    registry = (xeenlib.load_yaml(xeenlib.SOURCE / 'maps.yml') or {}).get('maps') or []
    lanes = {entry['key']: entry.get('lane') or '?' for entry in registry}
    found = []

    def check(origin, key, label, text, owner):
        effects = sorted({name for match in TEMP_RE.finditer(text)
                          for name in re.findall(r'\w+Bonus|Level\w*', match.group(0))})
        if effects and 'Xeen.usedToday' not in text:
            found.append({'map': key, 'label': label, 'effect': ', '.join(effects), 'origin': origin,
                          'owner': owner})

    for key, label, text in map_lua_events():
        check(f'events/maps ({key})', key, label, text, lanes.get(key, '?'))
    for origin, _act, key, label, node, _kind in quest_hook_nodes():
        check(str(origin), key, label, hook_text(node), 'A3')
    return sorted(found, key=lambda item: (item['owner'], item['map'], item['label']))


def scene_gems(gems):
    """Map key -> fixed gem items in its installed scene: chest records, loot containers' fixed items, ground items."""
    import struct
    registry = (xeenlib.load_yaml(xeenlib.SOURCE / 'maps.yml') or {}).get('maps') or []
    result = {}
    for entry in registry:
        path = xeenlib.WORLD / 'maps' / (entry['stem'].rsplit('.', 1)[0] + '.scene.yml')
        if not path.exists():
            continue
        scene = xeenlib.load_yaml(path) or {}
        count = 0
        state = scene.get('initial_state') or {}
        for chest in state.get('chests') or []:
            raw = bytes.fromhex(chest.get('raw_items_hex') or '')
            count += sum(struct.unpack_from('<i', raw, offset)[0] in gems
                         for offset in range(0, len(raw) - len(raw) % 36, 36))
        for box in scene.get('loot_containers') or []:
            count += sum(item.get('item_id') in gems for item in box.get('fixed_items') or [])
        for obj in state.get('sprite_objects') or []:
            raw = obj.get('raw_containing_item_hex') or ''
            if len(raw) >= 8:
                count += struct.unpack_from('<i', bytes.fromhex(raw[:8]), 0)[0] in gems
        if count:
            result[entry['key']] = (act_key(entry.get('act')), count)
    return result


def gate_id(gate):
    return f"{gate['map']} {gate['label']}"


def route_for(gate):
    for pattern, route in GATE_ROUTE.items():
        if re.fullmatch(pattern.replace('.', r'\.').replace(r'\.*', '.*'), gate_id(gate)):
            return route
    return {'before': (), 'temp': [], 'note': ''}


def gate_tables():
    """The stat-gate table and the gem budget (D-68 Q1.5), as report lines, and the gates outside the pass rule."""
    gates, sources, boosts, pays, gifts, gems = gate_survey()
    best = best_creation()
    # One row per gate: a device asked twice (FD-02's two sarcophagi, X9's three balls) is one row.
    rows = {}
    for gate in gates:
        row_key = (gate['map'], gate['label'].split('.')[0] if gate['label'].startswith(('q-f1.ball', 'm34.')) else
                   gate['label'], gate['stat'], gate['value'], gate['kind'])
        rows.setdefault(row_key, dict(gate, count=0))['count'] += 1
    lines = ['## Stat gates (D-68 Q1 point 5)', '',
             'Every `IsAtLeast(Base<stat>, n)` and `IsAtLeast(Actual<stat>, n)` in the installed map scripts and in A3\'s '
             'quest and NPC files. The best-suited member\'s value is the best creation value for the statistic '
             f'(the races the Xeen card offers, {CREATION_POOL} bonus points, others lowered by {CREATION_DROP}) + the '
             'permanent sources before the gate (earlier acts; of the gate\'s own act only the maps the route names; '
             'once per character, once for the party or daily, the member who needs it taking each) + for an '
             '`Actual` gate the fixed temporary help at hand (the gate\'s own map and the boost potions events hand '
             'over before it, one at a time). Random items, random devices (XD-04\'s vat), spells, gem-paid devices '
             '(XD-10\'s skulls) and far help carried along a route without a rest (D5\'s shrine to X9) are left out; '
             'the last two are listed as extra (D-70 Q1). '
             f'Pass (D-59): the fixed sources reach the number or fall short by at most {SHORTFALL_ALLOWED}.', '',
             '| Gate | Act | Check | Creation (races) | Permanent before | Temporary help | Value | Short | Verdict | '
             'Extra, not counted (gem-paid, route help) |',
             '| --- | --- | --- | --: | --- | --- | --: | --: | --- | --- |']
    failing = []
    for row_key, gate in sorted(rows.items(), key=lambda item: (item[1]['rank'], item[1]['map'], item[0][1])):
        stat, value, rank = gate['stat'], gate['value'], gate['rank']
        route = route_for(gate)
        creation, races = best.get(stat, (0, []))
        total = creation
        permanent, paid = [], []
        for source in sorted(sources, key=lambda s: (s['rank'], s['map'])):
            if source['stat'] != stat or source['kind'] != 'base' or source['scope'] == 'random':
                continue
            if source['map'] == gate['map'] and source['label'] == gate['label']:
                continue   # the gated device's own reward
            before = source['rank'] < rank or (source['rank'] == rank and source['map'] in route['before'])
            if not before:
                continue
            same_need = [need for need in source['needs'] if need[1] == stat]
            if any(total < need[2] for need in same_need):
                continue   # its own check is not met yet on this member (X5's Giants' Stones at base Might 40)
            text = f"{source['map']} {source['label']} +{source['amount']}"
            if source['scope'] == 'gems':
                paid.append(text)
                continue
            permanent.append(text + (' (fee)' if source['fee'] else ''))
            total += source['amount']
        permanent_total = total - creation
        temporary = []
        if gate['kind'] == 'Actual':
            own = {}
            for source in sources:
                if (source['kind'] == 'bonus' and source['stat'] == stat and source['map'] == gate['map']
                        and source['rank'] <= rank):
                    own[source['label']] = max(own.get(source['label'], 0), source['amount'])
            for label, amount in own.items():
                temporary.append((amount, f'{gate["map"]} {label} +{amount}'))
            for key, label, why in route['temp']:
                amount = max((s['amount'] for s in sources if s['kind'] == 'bonus' and s['stat'] == stat
                              and s['map'] == key and s['label'] == label), default=0)
                if amount:
                    paid.append(f'{key} {label} +{amount} (route help, not counted: {why})')
            potions = [boost for boost in boosts if boost['stat'] == stat and (boost['rank'] < rank or (
                boost['rank'] == rank and boost['map'] in route['before'] + (gate['map'],)))]
            if potions:
                strongest = max(potions, key=lambda boost: boost['amount'])
                givers = sorted({f"{boost['map']} {boost['label']}" for boost in potions})
                article = 'an' if stat[0] in 'AEIOU' else 'a'
                temporary.append((strongest['amount'], f"{article} {stat} Boost +{strongest['amount']} (event-given, "
                                  f"one at a time: {', '.join(givers)})"))
        temp_total = sum(amount for amount, _ in temporary)
        total += temp_total
        short = max(0, value - total)
        passed = short <= SHORTFALL_ALLOWED
        verdict_text = 'pass' if short == 0 else (f'pass (short {short})' if passed else '**outside the rule**')
        if not passed:
            failing.append((gate, total, short))
        label = gate['label'] + (f' (x{gate["count"]})' if gate['count'] > 1 else '')
        lines.append(f"| {gate['map']} {label} | {gate['act']} | {gate['kind']} {stat} >= {value} | {creation} "
                     f"({', '.join(races)}) | +{permanent_total}: {', '.join(permanent) or '-'} | "
                     f"+{temp_total}: {'; '.join(text for _, text in temporary) or '-'} | {total} | {short} | "
                     f"{verdict_text} | {', '.join(paid) or '-'} |")
    notes = [f"- {pattern}: {route['note']}" for pattern, route in GATE_ROUTE.items() if route.get('note')]
    lines += [''] + notes
    unguarded = guard_check()
    lines += ['', '## Daily guards (D-70 Q2)', '',
              'Every event and hook with a temporary effect (`AddValue` on a `*Bonus`, `ArmorClassBonus`, a '
              'resistance\'s bonus or a level) must be guarded once a day for the party by `Xeen.usedToday`. '
              + (f'**{len(unguarded)} without the guard (the check fails):**' if unguarded else
                 'None is without it: the check passes.')]
    if unguarded:
        lines += ['', '| Map | Event or hook | Effect | Source | Owner |', '| --- | --- | --- | --- | --- |']
        lines += [f"| {item['map']} | {item['label']} | {item['effect']} | {item['origin']} | {item['owner']} |"
                  for item in unguarded]

    # Gem budget: fixed gem sources on the route before each required payment (main-quest hooks) and each
    # promotion-path payment (PROMOTION_PAYMENTS).
    lines += ['', '## Gem budget (D-68 Q1 point 5)', '',
              'Fixed gem items only: chest and ground items placed in the installed scenes, and gems events and hooks '
              'hand over (a draw of one of several gems is one). Random loot and drops, which the gem ledger '
              '(`output/xeen_a2_check/gems/report.md`) adds, are left out. A required payment is a main quest\'s, '
              'at the first try; before it are the fixed gems of earlier acts, of its own map and of the maps its '
              'route names (the stat-gate routes above), less the required payments before it.', '',
              '| Required payment | Act | Gems | Fixed gems before it | Required so far | Margin |',
              '| --- | --- | --: | --- | --: | --: |']
    fixed = [{'map': key, 'rank': act_rank(act), 'gems': count, 'text': f'{key} placed {count}'}
             for key, (act, count) in scene_gems(gems).items()]
    fixed += [{'map': gift['map'], 'rank': gift['rank'], 'gems': gift['gems'],
               'text': f"{gift['map']} {gift['label']} {gift['gems']}"} for gift in gifts]

    def promotion_for(pay):
        for pattern, entry in PROMOTION_PAYMENTS.items():
            if re.fullmatch(pattern.replace('.', r'\.').replace(r'\.*', '.*'), gate_id(pay)):
                return entry
        return None

    # Main payments in act order; a promotion-path payment after every fixed gem of its `after` act and after the main
    # payments up to that act. Its own fee and the main ones before it count against it; it is not charged to later
    # main rows (a party need not take the promotion).
    rows = [(pay['rank'], 0, pay, None) for pay in pays if pay['kind'] == 'main']
    rows += [(act_rank(entry['after']), 1, pay, entry) for pay in pays if pay['kind'] != 'main'
             for entry in [promotion_for(pay)] if entry]
    rows.sort(key=lambda row: (row[0], row[1]))
    promoted = {id(row[2]) for row in rows if row[3]}
    optional = [pay for pay in pays if pay['kind'] != 'main' and id(pay) not in promoted]
    choices = choice_gems(gems)
    budget_fail, promotion_short, notes = [], [], []
    main_so_far = promotion_so_far = 0
    for rank, _order, pay, entry in rows:
        if entry:
            before = [item for item in fixed if item['rank'] <= rank]
            promotion_so_far += pay['gems']
            required_so_far = main_so_far + promotion_so_far
        else:
            route = route_for(pay)
            before = [item for item in fixed if item['rank'] < pay['rank'] or (
                item['rank'] == pay['rank'] and (item['map'] == pay['map'] or item['map'] in route['before']))]
            main_so_far += pay['gems']
            required_so_far = main_so_far
        available = sum(item['gems'] for item in before)
        margin = available - required_so_far
        # D-81: a promotion-path row short on fixed gems takes the fewest fixed choices (largest first) before it.
        taken = []
        if entry and margin < 0:
            for choice in sorted((item for item in choices if item['rank'] <= rank), key=lambda item: -item['gems']):
                if margin >= 0:
                    break
                taken.append(choice)
                margin += choice['gems']
            if margin < 0:
                taken = []
                margin = available - required_so_far
        if margin < 0:
            (promotion_short if entry else budget_fail).append((gate_id(pay), margin))
        by_act = defaultdict(int)
        for item in before:
            by_act[ACTS[item['rank']]] += item['gems']
        label = gate_id(pay) + (f" (promotion path: {entry['promotion']})" if entry else '')
        act = f"{pay['act']}, after {entry['after']}" if entry else pay['act']
        with_choices = ''
        if taken:
            uses = defaultdict(lambda: [0, 0])
            for choice in taken:
                uses[choice['label']][0] += 1
                uses[choice['label']][1] += choice['gems']
            with_choices = ' + ' + ', '.join(f"{count} x {label} ({gems_total})"
                                             for label, (count, gems_total) in uses.items())
        verdict = (' **short**' if margin < 0 else
                   f" pass ({'one fixed choice' if len(taken) == 1 else f'{len(taken)} fixed choices'})" if taken
                   else '')
        lines.append(f"| {label} | {act} | {pay['gems']} | {available} "
                     f"({', '.join(f'{act} {count}' for act, count in by_act.items())}){with_choices} | "
                     f"{required_so_far} | {margin}{verdict} |")
        if entry:
            offered = [item for item in choices if item['rank'] <= rank]
            notes.append(f"{gate_id(pay)}: {entry['note']}"
                         + (f"; fixed choices before it (D-81): {len(offered)} uses, "
                            + ', '.join(f"{item['map']} {item['label']} {item['gems']}" for item in offered)
                            if offered else ''))
    if notes:
        lines += ['', 'Promotion-path payments (D-75, report-only: every fixed gem of the acts up to the branch point '
                      'counts; the payment does not fail `--gates`; D-81: when the fixed gems fall short, the fewest '
                      'fixed choices before it (an `alternative: true` gem give, one use per lamp or place that offers '
                      'it) may close the gap, and the row is short only if every such use still leaves one; random '
                      'loot never counts): ' + '; '.join(notes) + '.']
    lines += ['', 'Fixed gems by act: ' + '; '.join(
        f"{act} {sum(item['gems'] for item in fixed if ACTS[item['rank']] == act)} ("
        + ', '.join(item['text'] for item in fixed if ACTS[item['rank']] == act) + ')'
        for act in ACTS if any(ACTS[item['rank']] == act for item in fixed)) + '.',
              '', 'Optional sinks (not in the budget): ' + '; '.join(
                  f"{gate_id(pay)} {pay['gems']} ({pay['act']})" for pay in optional) + '.']
    for gate, total, short in failing:
        lines.append(f"\n**Outside the rule: {gate_id(gate)} needs {gate['kind']} {gate['stat']} {gate['value']}, "
                     f"the fixed sources reach {total} (short {short}): to a decider (another source or another "
                     f"number).**")
    for where, margin in budget_fail:
        lines.append(f'\n**Gem budget short at {where} by {-margin}: to a decider.**')
    for where, margin in promotion_short:
        lines.append(f'\n**Promotion-path gem budget short at {where} by {-margin} on fixed gems and every fixed '
                     f'choice before it (D-81): to a decider (report-only, D-75).**')
    return lines, failing, budget_fail, unguarded


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--maps-dir', type=Path, default=xeenlib.WORLD / 'maps')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--detail', action='store_true', help='per map, the monsters behind its count and kill XP')
    parser.add_argument('--gates', action='store_true',
                        help='only the stat-gate table and the gem budget (D-68), not the kill and quest XP count')
    args = parser.parse_args()

    if args.gates:
        lines, failing, budget_fail, unguarded = gate_tables()
        report = '# Xeen stat gates and gem budget\n\n' + '\n'.join(lines) + '\n'
        print(report)
        if args.out:
            args.out.write_text(report, encoding='utf-8')
        # A gate outside the rule, a short gem budget or an unguarded temporary effect fails the check.
        sys.exit(1 if failing or budget_fail or unguarded else 0)

    by_id, by_picture = monster_rows()
    stats = map_stats_rows()
    registry = (xeenlib.load_yaml(xeenlib.SOURCE / 'maps.yml') or {}).get('maps') or []
    traps = trap_rows()
    regions = act_regions()
    rows_by_act = act_rows()
    map_elsewhere = {}
    friendly = friendly_rows()
    counted_friendly = {key: set(extra.get('count_friendly') or [])
                        for key, extra in ((xeenlib.load_yaml(xeenlib.SOURCE / 'map_rows.yml') or {}).get('maps')
                                           or {}).items()}
    # Rows a map leaves off the counted route (map_rows.yml `most_experience`: D7's Sky Bandits and Megadragon, D-58);
    # their kill XP is the act's "most experience" kill line.
    most_rows = {key: set(extra.get('most_experience') or [])
                 for key, extra in ((xeenlib.load_yaml(xeenlib.SOURCE / 'map_rows.yml') or {}).get('maps')
                                    or {}).items()}
    most_kill_by_act = defaultdict(float)
    bands = act_levels()
    trap_xp_by_act = defaultdict(float)
    measured = {}
    details = {}
    lines = [f'# Xeen balance recount', '', f'Maps from `{args.maps_dir}`; targets from MAPS.md section 0. Kill XP '
             f'is per member (party XP / 4). Ratios outside 0.85-1.15 are marked.', '',
             '## Maps', '',
             '| Map | Act | Monsters (target) | Levels | Kill XP per member (target) | Ratio | Traps and regions (act) | '
             'Chests | '
             'Notes |',
             '| --- | --- | --: | --- | --: | --: | --- | --: | --- |']
    target_rows = expand_pockets(targets(), [entry['key'] for entry in registry])
    single = {row['keys'][0]: row for row in target_rows if len(row['keys']) == 1 and not row.get('part')}
    for entry in registry:
        scene_path = args.maps_dir / (entry['stem'].rsplit('.', 1)[0] + '.scene.yml')
        if not scene_path.exists():
            continue
        scene = xeenlib.load_yaml(scene_path) or {}
        details[entry['key']] = {}
        trapped = []
        elsewhere = {}
        most = []
        monsters, party_xp, chests, levels, notes = count_map(entry, scene, stats, by_id, by_picture,
                                                              details[entry['key']], traps.get(entry['key'], {}),
                                                              trapped, regions.get(entry['key'], ()), elsewhere,
                                                              friendly - counted_friendly.get(entry['key'], set()),
                                                              rows_by_act.get(entry['key']),
                                                              most_rows.get(entry['key'], set()), most)
        most_kill_by_act[act_key(entry.get('act'))] += sum(most) / 4
        map_elsewhere[entry['key']] = elsewhere
        member_xp = party_xp / 4
        trap_acts = defaultdict(lambda: [0, 0.0])
        for level, xp, quest_act in trapped:
            act = quest_act or act_for_level(level, bands)
            trap_acts[act][0] += 1
            trap_acts[act][1] += xp / 4
            trap_xp_by_act[act] += xp / 4
        for act, (count, xp) in elsewhere.items():
            trap_acts[f'{act}, region'][0] += count
            trap_acts[f'{act}, region'][1] += xp / 4
            trap_xp_by_act[act] += xp / 4
        trap_text = ', '.join(f'{count:.0f} ({act}, {xp / 1000:.1f}k)' for act, (count, xp) in trap_acts.items()) or '-'
        measured[entry['key']] = (monsters, member_xp)
        target = single.get(entry['key'])
        band = f'{min(levels)}-{max(levels)}' if levels else '-'
        lines.append(f"| {entry['key']} {entry['name']} | {entry.get('act')} | {monsters:.0f} "
                     f"({target['monsters'] if target else '-'}) | {band} | {member_xp / 1000:.1f}k "
                     f"({target['xp'] / 1000 if target else 0:.1f}k) | "
                     f"{verdict(member_xp, target['xp']) if target else ''} | {trap_text} | {chests} | "
                     f"{'; '.join(sorted(set(notes)))} |")

    lines += ['', '## Groups and acts (installed maps only)', '',
              '| Row of MAPS §0 | Installed | Kill XP per member (target) | Ratio |', '| --- | --- | --: | --: |']
    act_actual = defaultdict(float)
    act_target = defaultdict(float)
    act_budget = defaultdict(float)
    for row in target_rows:
        act_budget[row['act']] += row['xp']
    for row in target_rows:
        present = [key for key in row['keys'] if key in measured]
        if not present:
            continue
        if row.get('part'):
            # Counted beside the map (its act_rows), already in the act's "traps and regions" column.
            actual = sum((map_elsewhere[key].get(row['act']) or [0, 0])[1] / 4 for key in present)
            lines.append(f"| {row['label']} | {', '.join(present)} | {actual / 1000:.1f}k ({row['xp'] / 1000:.1f}k) | "
                         f"{verdict(actual, row['xp'])} |")
            act_target[row['act']] += row['xp']
            continue
        actual = sum(measured[key][1] for key in present)
        complete = len(present) == len(row['keys'])
        lines.append(f"| {row['label']} | {', '.join(present)}{'' if complete else ' (part)'} | "
                     f"{actual / 1000:.1f}k ({row['xp'] / 1000:.1f}k) | {verdict(actual, row['xp']) if complete else ''} |")
        if complete:
            act_actual[row['act']] += actual
            act_target[row['act']] += row['xp']

    quest_xp, quest_files = quest_xp_by_act()
    npc_xp, npc_files = npc_xp_by_act()
    for act, xp in npc_xp.items():
        quest_xp[act] += xp
    lines += ['', '| Act | Kill XP per member, installed maps (their targets) | Traps and regions counted here | '
              'Ratio, traps '
              f'included | Act kill budget, all maps (MAPS §0) | Quest XP per member ({quest_files} quest files and '
              f'{npc_files} NPC files with XP; QUESTS budget), counted route | Quest XP, most experience (every '
              'experience-or-goods choice as experience) | Kill XP off the route, most experience (map_rows '
              '`most_experience`) |',
              '| --- | --: | --: | --: | --: | --: | --: | --: |']
    budgets = quest_budgets()
    choice_xp, choices = xp_choices_by_act()
    over_closed = []
    present = set(act_actual) | set(quest_xp) | set(trap_xp_by_act)
    for act in [act for act in ACTS if act in present] + sorted(present - set(ACTS)):
        total = act_actual[act] + trap_xp_by_act[act]
        budget = budgets.get(act, 0)
        most = quest_xp.get(act, 0) + choice_xp.get(act, 0)
        closed = ''
        if act in CLOSED_QUEST_XP:
            cap, note = CLOSED_QUEST_XP[act]
            closed = f' ({note})'
            if quest_xp.get(act, 0) > cap + 0.5:
                closed += f' **over the closed {cap / 1000:.1f}k: to a decider**'
                over_closed.append(f'Act {act} quest XP {quest_xp.get(act, 0) / 1000:.1f}k is over its closed '
                                   f'{cap / 1000:.1f}k ({note}): to a decider.')
        lines.append(f'| {act} | {act_actual[act] / 1000:.1f}k ({act_target[act] / 1000:.1f}k) | '
                     f'{trap_xp_by_act[act] / 1000:.1f}k | {verdict(total, act_target[act])} | '
                     f'{act_budget.get(act, 0) / 1000:.1f}k | {quest_xp.get(act, 0) / 1000:.1f}k ({budget / 1000:.1f}k) '
                     f'{verdict(quest_xp.get(act, 0), budget)}{closed} | '
                     f'{most / 1000:.1f}k {verdict(most, budget)} | {most_kill_by_act[act] / 1000:.1f}k |')
    lines += ['', 'Traps (map_rows.yml `traps`) are not in their map\'s kill XP; they count in the act of the quest '
              'that asks for the kill, else in the first act whose leaving party level is at least 60 % of theirs '
              '(MAPS §0 leaving levels: ' + ', '.join(f'{act} {top}' for act, top in bands) + '). A map\'s act regions '
              '(map_rows.yml `act_regions`) count in their own act the same way. Rows friendly to the party '
              '(relations.yml) are not counted. While an act has few maps installed, its traps and regions weigh on '
              'the ratio against those maps only; the act\'s whole budget is in its own column.',
              '', 'Quest XP counts one route per exclusive choice (an `alternative: true` branch left out); the most-'
              'experience column adds each experience-or-goods choice at its highest experience, as often as a map '
              'offers it (map_rows.yml `xp_choices`, D-53): ' + ('; '.join(choices) or 'none') + '.']
    if over_closed:
        lines += [''] + [f'**{line}**' for line in over_closed]

    lines += [''] + gate_tables()[0]

    if args.detail:
        lines += ['', '## Per map: where the kill XP comes from', '']
        for key, detail in details.items():
            lines += [f'### {key}', '', '| How | Monster | Level | Count | Kill XP per member |', '| --- | --- | --: | --: | --: |']
            for (how, name, level), (count, xp) in sorted(detail.items(), key=lambda item: -item[1][1]):
                lines.append(f'| {how} | {name} | {level} | {count:.1f} | {xp / 4:.0f} |')
            lines.append('')

    report = '\n'.join(lines) + '\n'
    print(report)
    if args.out:
        args.out.write_text(report, encoding='utf-8')


if __name__ == '__main__':
    main()
