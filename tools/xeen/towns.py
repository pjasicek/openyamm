#!/usr/bin/env python3
"""Checks the Xeen town files (lane A4; devdocs/xeen/formats/TOWNS_FORMAT.md section 5).

    python3 -I tools/xeen/towns.py            # report; exit 1 on an error
    python3 -I tools/xeen/towns.py --strict   # missing portraits are errors too
    python3 -I tools/xeen/towns.py --stock-scenario   # also writes tests/scenarios/xeen/shop_stock.yml

Checks: ids inside their blocks and the world's ranges and never twice; every house door of the built map's project
(its L4 sketch, or an indoor map's L4 wiring) has a house and every house a door; the installed script enters every
built house, a house that opens by qbit only behind it with its closed text; residences and services per town against WORLD_DESIGN 5; teacher offers against
teachers_plan.yml, with a warning (WARN) when a Master place's level is below its Expert place's (D-73; Grandmaster
before Master is no fault, U-2); every NPC has a portrait, and a profession, a teacher offer or a greeting; every built
guild has a book of the world for each spell its shelf sells (feedback F7: Xeen had no books of its own and every guild's
shelf was empty); every built town map's house hangs the sign of its kind (house_signs.py; a service of a signed kind
hanging none is a WARN); the generator runs.

`--stock-scenario` writes the headless check that opens every built shop's and guild's stock in the game and fails on
an empty one (tests/scenarios/xeen/shop_stock.yml; run it after a town file, gen_items or a shop rule changes).
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_towns  # noqa: E402
import house_signs  # noqa: E402

REPO = gen_towns.REPO
BRIEFS = REPO / 'devdocs' / 'xeen' / 'briefs'
ICONS = gen_towns.WORLD / 'icons_x2'
WORLD_YML = gen_towns.WORLD / 'world.yml'
PLAN = gen_towns.TOWNS / 'teachers_plan.yml'

# WORLD_DESIGN 5.1/5.2: residences at full strength, and the role that sets the service list.
TOWN_TARGETS = {
    'Vertigo': (18, 'start'), 'Rivercity': (30, 'hub'), 'Castle Burlock': (8, 'regional'), 'Asp': (10, 'regional'),
    'Winterkill': (12, 'regional'), 'Nightshadow': (10, 'regional'), 'Shangri-La': (8, 'hidden'),
    'Castleview': (28, 'hub'), 'Sandcaster': (26, 'city'), 'Lakeside': (10, 'regional'),
    'Necropolis': (6, 'regional'), 'Olympus': (6, 'regional'),
    "Bosco's Hall": (3, 'wilderness'),   # D-62: WORLD_DESIGN's two burrows plus the King's Hall (4704)
    'Olympus Sewer': (1, 'wilderness'),  # D-65 Q57: Cyrano's Pets Unlimited (4815), a residence for his topics
    "Ebenezer's camp": (0, 'wilderness'), "Kai Wu's monastery": (0, 'wilderness'),
    # WORLD_DESIGN 5.1 hamlets: tavern, stables or boat, 1-3 houses
    'Sphinx Wells': (2, 'wilderness'), 'The Warzone': (0, 'wilderness'),
}
FULL_SET = {'weapon_shop', 'armor_shop', 'magic_shop', 'alchemist', 'temple', 'tavern', 'bank', 'training', 'stables',
            'mirror'}
# A hub's boat is Rivercity's (Castleview has none); Sandcaster is a city: more than a regional town, no bank.
ROLE_SERVICES = {'start': (FULL_SET, None), 'hub': (FULL_SET, None), 'city': (set(), (10, 16)), 'regional': (set(), (6, 9)),
                 # Shangri-La: WORLD_DESIGN 5.1 names four services and the library (no mirror, not a Town Portal town)
                 'hidden': (set(), (4, 6)),
                 'wilderness': (set(), (0, 3))}
RESIDENCE_TOLERANCE = 3
MIN_TAVERN_DAYS = 14    # D-29: packs a tavern fills off the start pocket (X1)
# WORLD_DESIGN 5: the cursed towns, closed until their quest but for one service or two and one open house.
CURSED = {'Asp', 'Winterkill', 'Nightshadow', 'Lakeside'}
ENTER_HOUSE = re.compile(r'evt\.EnterHouse\((\d+)\)')
USE_MIRROR = re.compile(r'Xeen\.useMirror\((\d+)\b')
# D-21: an NPC's title is a capitalised noun phrase naming a person, with no leading "The"; none where the name carries
# one (a rank or form of address first, or a word of the title already in the name: Princess Roxanne, Captain Nystor).
HONORIFICS = {'king', 'queen', 'prince', 'princess', 'count', 'countess', 'lord', 'lady', 'sir', 'dame', 'brother',
              'sister', 'father', 'mother'}
GROUP_WORDS = {'cult', 'kitchen', 'guild', 'hall', 'inn', 'tavern', 'temple', 'shop', 'clan', 'order', 'council',
               'house', 'library', 'market', 'xeen', 'cloudside', 'darkside'}
MINOR_WORDS = {'of', 'the', 'a', 'an', 'for', 'in', 'at', 'and', 'to'}


def words(text):
    return [w for w in re.split(r"[\s,]+", text) if w]


def title_problem(name, title):
    """None for a good title (or none); else 'carried' (the name carries a title: there must be none), 'the',
    'capitals' or 'group' (the title names a group or place, not a person)."""
    name_words = [w.lower() for w in words(name)]
    if name_words and name_words[0] == 'the':
        name_words = name_words[1:]
    significant = {w.strip("'") for w in name_words if len(w) > 2 and w not in MINOR_WORDS and w != 'old'}
    carried = bool(name_words) and name_words[0] in HONORIFICS
    if not title:
        return None
    title_words = words(title)
    if carried or significant & {w.lower().strip("'") for w in title_words}:
        return 'carried'
    if title_words[0] == 'The':
        return 'the'
    if any(not w[0].isupper() for w in title_words if w.lower() not in MINOR_WORDS) or not title_words[0][0].isupper():
        return 'capitals'
    head = words(title.split(' of ')[0])[-1].lower()
    if head in GROUP_WORDS:
        return 'group'
    return None


def ranges_of(block):
    """A block is [first, last] or a list of such ranges (a map whose block is full takes more ids from the rest block,
    TOWNS_FORMAT section 2)."""
    return block if block and isinstance(block[0], list) else [block]


def in_block(value, block):
    return any(low <= value <= high for low, high in ranges_of(block))


def project_ids(key):
    """Every id the map's L4 sketch names (things too: a mirror is a portal thing, not a house door)."""
    sketch = l4(key) / 'sketch.yml'
    if not sketch.exists():
        return set()
    ids = set()

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get('id'), str):
                ids.add(node['id'])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(yaml.safe_load(sketch.read_text()))
    return ids


def l4(key):
    """The map's L4 brief folder (`XD-07` -> briefs/xd07/L4)."""
    return BRIEFS / key.lower().replace('-', '') / 'L4'


def wiring_mirrors(key):
    """An indoor map's mirrors from its L4 wiring: {event source: mirror house id} for each event whose Lua runs
    `Xeen.useMirror(n, ...)` (DD-03's framed glass panel); empty without a wiring file or a sketch map."""
    wiring = l4(key) / 'wiring.yml'
    if (l4(key) / 'sketch.yml').exists() or not wiring.exists():
        return {}
    mirrors = {}
    for event in yaml.safe_load(wiring.read_text()).get('events') or []:
        effects = [event] + [e for e in event.get('effects') or [] if isinstance(e, dict)]
        for effect in effects:
            match = USE_MIRROR.search(str(effect.get('lua', '')))
            if match and event.get('source'):
                mirrors[event['source']] = int(match.group(1))
    return mirrors


def wiring_doors(key):
    """An indoor map's doors from its L4 wiring (no sketch): {event source: house id} for each event whose effects
    enter a house (`evt.EnterHouse(n)`); None without a wiring file."""
    wiring = l4(key) / 'wiring.yml'
    if not wiring.exists():
        return None
    doors = {}
    for event in yaml.safe_load(wiring.read_text()).get('events') or []:
        for effect in event.get('effects') or []:
            match = ENTER_HOUSE.search(str(effect.get('lua', ''))) if isinstance(effect, dict) else None
            if match and event.get('source'):
                doors[event['source']] = int(match.group(1))
    return doors


def script_errors(key, town, script_text):
    """Each non-mirror house is entered by some event of the installed map script; each event entering a house with
    `opens:` tests that qbit (`QBit(n)` or `Xeen.isSet("name")`) before it does and shows the file's closed_text
    (TOWNS_FORMAT section 1)."""
    events = script_text.split('\nRegisterEvent(')
    errors = []
    for house in town['houses']:
        if house['kind'] == 'mirror':
            continue
        entering = [event for event in events if f'evt.EnterHouse({house["id"]})' in event]
        if not entering:
            if not house.get('new_door'):
                errors.append(f'{key}: house {house["id"]} {house["name"]}: no event of the installed script enters it')
            continue
        if not house.get('opens'):
            continue
        try:
            number = gen_towns.quest_qbit(house['opens'])
        except gen_towns.TownError:
            continue  # the name waits for A3 (reported with the routes' qbits)
        tests = (f'QBit({number})', f'Xeen.isSet("{house["opens"]}")')
        for event in entering:
            before = event.split(f'evt.EnterHouse({house["id"]})')[0]
            if not any(test in before for test in tests):
                errors.append(f'{key}: house {house["id"]} {house["name"]} opens on {house["opens"]}, but the script '
                              f'enters it without testing it')
            elif house.get('closed_text') and house['closed_text'].replace('"', '\\"') not in event:
                errors.append(f'{key}: house {house["id"]} {house["name"]}: the script\'s closed text is not the file\'s')
    return errors


def project_doors(key):
    """Building ids (with #index) that open a house on the built map, from its L4 sketch (an indoor map: the sources
    of its wiring's house events); None without either."""
    sketch = l4(key) / 'sketch.yml'
    if not sketch.exists():
        wired = wiring_doors(key)
        return None if wired is None else set(wired)
    data = yaml.safe_load(sketch.read_text())
    doors = set()

    def walk(node):
        if isinstance(node, dict):
            if 'house' in node and ('building' in node or 'id' in node):
                name = node.get('building') or node.get('id')
                if node.get('index') is not None:
                    name = f'{name}#{node["index"]}'
                doors.add(name)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(data)
    return doors


GUILD_SCHOOLS = {'fire_guild': [0], 'air_guild': [1], 'water_guild': [2], 'earth_guild': [3], 'spirit_guild': [4],
                 'mind_guild': [5], 'body_guild': [6], 'light_guild': [7], 'dark_guild': [8]}
SPELLS_PER_SCHOOL = 11
STOCK_SCENARIO = REPO / 'tests' / 'scenarios' / 'xeen' / 'shop_stock.yml'
# A1's F1 change (a proprietor who is also a resident NPC, the same portrait, is one person on the house screen): until
# merge point 40 the house listed him twice and the scenario picked the proprietor's portrait first.
PROPRIETOR_TWIN_MERGED = True


def world_books():
    """Spell ids that have a spell book Xeen's guilds may sell: a Book row of the engine or the world's items.txt with no
    World: flag or World:xeen (ItemTable::spellbookItemIdForSpell, ItemDefinition::availableInWorld)."""
    spells = set()
    world_items = gen_towns.WORLD / 'data_tables' / 'items.txt'
    rows = gen_towns.read_table('items.txt')
    if world_items.exists():
        rows += [line.split('\t') for line in world_items.read_text(encoding='utf-8').splitlines()]
    for row in rows:
        if len(row) < 7 or row[4] != 'Book' or not row[6].startswith('S') or not row[6][1:].isdigit():
            continue
        worlds = [flag.strip().lower()[6:] for flag in (row[20] if len(row) > 20 else '').split('|')
                  if flag.strip().lower().startswith('world:')]
        if not worlds or 'xeen' in worlds:
            spells.add(int(row[6][1:]))
    return spells


def guild_book_errors(towns, rule_sections):
    books = world_books()
    errors = []
    for town in towns:
        for house in gen_towns.built(town, 'houses', []):
            if house['kind'] not in gen_towns.GUILD_KINDS:
                continue
            row = gen_towns.pick_guild_row(rule_sections, house['guild'])
            sold = rule_sections['Spellbook shops'][row][0]
            missing = [school * SPELLS_PER_SCHOOL + spell + 1 for school in GUILD_SCHOOLS[house['kind']]
                       for spell in range(sold) if school * SPELLS_PER_SCHOOL + spell + 1 not in books]
            if missing:
                errors.append(f'{town["key"]}: guild {house["id"]} {house["name"]} sells {sold} spells per school but '
                              f'Xeen has no book of spells {missing} (source/items.yml spellbooks, gen_items)')
    return errors


def stock_scenario(towns):
    """The headless check: every built shop's Buy Standard and Buy Special and every guild's Buy Spellbooks shows a
    stock of at least one thing (the `coop shop` console line counts the open stock screen)."""
    data = gen_towns.WORLD / 'data_tables'
    read = lambda name: [line.split('\t') for line in (data / name).read_text(encoding='utf-8').splitlines()]
    house_rows = {row[0]: row for row in read('house_data.txt') if row and row[0].isdigit()}
    listed = {row[0]: [r for r in row[3].split(',') if r] for row in read('house_animations.txt')
              if row and row[0].isdigit() and len(row) > 3}
    npc_rows = [row for row in read('npc.txt') if row and row[0].isdigit()]
    steps = [
        {'new_game_flow': {'start_map': 'xeen_x1.odm', 'party': {'gold': 50000, 'food': 10, 'members': [
            {'name': 'A', 'class': 'Sorcerer', 'level': 10,
             'skills': [{'name': 'Fire Magic', 'level': 4, 'mastery': 1}], 'equipment': {}}]}}},
        {'advance_runtime': {'seconds': 6, 'present_dialogs': True}},
        {'play_lua': {'source': 'close()'}},
    ]
    day, night = [], []
    for town in towns:
        for house in gen_towns.built(town, 'houses', []):
            kind = house['kind']
            if kind not in gen_towns.SHOP_SECTIONS and kind not in gen_towns.GUILD_KINDS:
                continue
            row = house_rows[str(house['id'])]
            opens, closes = int(row[18]), int(row[19])
            (night if opens > closes else day).append((house, row))
    for index, group in enumerate((day, night)):
        if index == 1 and group:
            # the game starts in the morning; night houses (Necropolis) open after 21:00
            steps.append({'advance_game_time': {'hours': 13}})
        for house, row in group:
            hid = str(house['id'])
            residents = listed.get(hid, []) + [npc[0] for npc in npc_rows if npc[6] == hid]
            if PROPRIETOR_TWIN_MERGED:
                residents = [r for r in residents
                             if not any(npc[0] == r and npc[2] == row[8] for npc in npc_rows)]
            buys = ['Buy Spellbooks'] if house['kind'] in gen_towns.GUILD_KINDS else ['Buy Standard', 'Buy Special']
            for buy in buys:
                steps.append({'lua_event': {'source': f'evt.EnterHouse({hid})'}})
                steps.append({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
                if residents:
                    steps.append({'select_topic': {'match_label': row[6] + (f', {row[7]}' if row[7] else '')}})
                    steps.append({'advance_runtime': {'seconds': 0.2}})
                steps.append({'select_topic': {'match_label': buy}})
                steps.append({'advance_runtime': {'seconds': 0.2}})
                steps.append({'console': {'line': 'coop shop', 'expect_contains': f'stock of {row[5]}: '}})
                steps.append({'console': {'line': 'coop shop', 'expect_not_contains': ': 0 things'}})
                steps.append({'play_lua': {'source': 'close() close() close()'}})
                steps.append({'advance_runtime': {'seconds': 0.2}})
    doc = {
        'id': 'xeen.a4.shop_stock',
        'title': "Every built Xeen shop and guild has stock (feedback F7: the guilds' shelves were empty)",
        'world': 'xeen', 'mode': 'faithful', 'steps': steps,
    }
    header = ('# Generated by tools/xeen/towns.py --stock-scenario from the town files and data_tables; do not edit.\n'
              f'# {len(day) + len(night)} houses. Run: build-xeen/game/openyamm --headless-run-scenario '
              'tests/scenarios/xeen/shop_stock.yml --scenario-no-color\n')
    STOCK_SCENARIO.write_text(header + yaml.safe_dump(doc, sort_keys=False, width=120))
    return len(day) + len(night)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--strict', action='store_true', help='missing portraits are errors')
    parser.add_argument('--stock-scenario', action='store_true', help=f'write {STOCK_SCENARIO.relative_to(REPO)}')
    args = parser.parse_args()
    errors, waits = [], []
    towns = gen_towns.load_towns()
    ranges = yaml.safe_load(WORLD_YML.read_text())['idRanges']
    plan = yaml.safe_load(PLAN.read_text())

    house_ids, npc_ids, route_ids = Counter(), Counter(), Counter()
    later_greets = []
    routes = []
    arrival_names = {name for town in towns for name in (town.get('arrivals') or {})}
    taught = {}
    by_town = {}
    engine_houses = gen_towns.engine_lookups()[2]
    rule_sections = gen_towns.read_rule_sections()
    for town in towns:
        key = town['key']
        house_block = town['blocks']['houses']
        npc_block = town['blocks']['npcs']
        for house in town['houses']:
            house_ids[house['id']] += 1
            if not in_block(house['id'], house_block):
                errors.append(f'{key}: house {house["id"]} outside its block {house_block}')
            for route in house.get('routes', []):
                route_ids[route['id']] += 1
                routes.append((key, house, route))
                if not ranges['transport']['begin'] <= route['id'] <= ranges['transport']['end']:
                    errors.append(f'{key}: route {route["id"]} outside the transport range')
        for npc in town['npcs']:
            npc_ids[npc['id']] += 1
            if not in_block(npc['id'], npc_block):
                errors.append(f'{key}: npc {npc["id"]} outside its block {npc_block}')
            problem = title_problem(npc['name'], npc.get('title', ''))
            if problem:
                reason = {'carried': 'the name carries a title already: none', 'the': 'no leading "The"',
                          'capitals': 'a capitalised noun phrase', 'group': 'a person, not a group or place'}[problem]
                errors.append(f'{key}: npc {npc["id"]} {npc["name"]}: title "{npc["title"]}": {reason} (D-21)')
            if not (npc.get('profession') or npc.get('teaches') or npc.get('greet')):
                errors.append(f'{key}: npc {npc["id"]} {npc["name"]} has no profession, offer or greeting')
            portrait = ICONS / f'npc{gen_towns.PORTRAIT_BASE + npc["id"]}.png'
            if not portrait.exists():
                (errors if args.strict else waits).append(f'{key}: npc {npc["id"]} {npc["name"]}: no portrait {portrait.name}')
            for offer in npc.get('teaches', []):
                taught.setdefault((offer['skill'], offer['mastery']), []).append((key, npc['id'], offer.get('opens')))
            for entry in npc.get('greet_after', []):
                later_greets.append((key, npc, entry))
                if not in_block(entry['id'], npc_block):
                    errors.append(f'{key}: npc {npc["id"]}: greeting {entry["id"]} outside its block {npc_block}')
                if not npc.get('greet') or not entry.get('greet') or not entry.get('after'):
                    errors.append(f'{key}: npc {npc["id"]}: greet_after {entry["id"]} needs `greet`, its own lines '
                                  'and `after`')
        for domain, block, label in (('houses', house_block, 'house'), ('npcs', npc_block, 'npc')):
            for low, high in ranges_of(block):
                if not ranges[domain]['begin'] <= low <= high <= ranges[domain]['end']:
                    errors.append(f'{key}: {label} block {block} outside the world range')

        # every shop and guild has an engine house_rules row, planned files too (else the build fails at install)
        for house in town['houses']:
            try:
                if 'shop' in house:
                    gen_towns.pick_shop_row(rule_sections, house['kind'], house['shop'])
                if 'guild' in house:
                    gen_towns.pick_guild_row(rule_sections, house['guild'])
            except gen_towns.TownError as error:
                errors.append(f'{key}: house {house["id"]} {house["name"]}: {error}')

        # an indoor door is named by its own id: `#n` (an outdoor building's index) cannot name one (D-50 change 5)
        if town['stem'].endswith('.blv'):
            for house in town['houses']:
                for door in [house['door'], *house.get('also_doors', [])]:
                    if '#' in door:
                        errors.append(f'{key}: house {house["id"]} door {door}: an indoor door id has no #index')

        # doors of the built map
        doors = project_doors(key)
        # a house may have more doors than one (Nystor's dock and his ship both enter 4063): `also_doors:`
        house_doors = {d for h in town['houses'] if not h.get('alternate_of')
                       for d in [h['door'], *h.get('also_doors', [])]}
        if doors is None:
            waits.append(f'{key}: no L4 sketch to check doors against')
        else:
            for door in sorted(doors - house_doors):
                errors.append(f'{key}: door {door} opens a house on the built map but has no Xeen house')
            # a mirror is a map thing, not a house door: its event in the installed map's script names it
            script = gen_towns.MAP_SCRIPTS / (Path(town['stem']).stem + '.lua')
            script_text = script.read_text() if script.exists() else ''
            sketch_ids = project_ids(key)
            mirrors = wiring_mirrors(key)
            for house in town['houses']:
                if house['kind'] == 'mirror' and (f'-- evt:{house["door"]}\n' in script_text
                                                  or house['door'] in sketch_ids):
                    continue
                if house['kind'] == 'mirror' and house['door'] in mirrors:
                    if mirrors[house['door']] != house['id']:
                        errors.append(f'{key}: mirror {house["door"]} runs Xeen.useMirror({mirrors[house["door"]]}) '
                                      f'on the map, the file says {house["id"]}')
                    continue
                if house['door'] not in doors and not house.get('new_door') and not house.get('alternate_of'):
                    errors.append(f'{key}: house {house["id"]} names door {house["door"]}, which the map does not have')
            # an indoor map's wiring names the house it enters: it must be the one this file gives the door
            wired = {} if (l4(key) / 'sketch.yml').exists() else (wiring_doors(key) or {})
            for house in town['houses']:
                for door in [house['door'], *house.get('also_doors', [])]:
                    if door in wired and wired[door] != house['id'] and not house.get('alternate_of'):
                        errors.append(f'{key}: door {door} enters house {wired[door]} on the map, the file says '
                                      f'{house["id"]}')
            # the installed script: every house of a built file is entered, one that opens by qbit only behind it
            if script_text and not town.get('planned'):
                errors.extend(script_errors(key, town, script_text))
            for house in town['houses']:
                if house.get('new_door'):
                    waits.append(f'{key}: house {house["id"]} {house["name"]}: door to change ({house["new_door"]})')

        for house in town['houses']:
            if house.get('opens') and not house.get('closed_text'):
                errors.append(f'{key}: house {house["id"]} opens by qbit but has no closed_text')
            # D-29: a tavern fills packs to its Val in days; off the start pocket at least 14 (an edge costs 5 food)
            if house['kind'] == 'tavern' and key != 'X1':
                val = float(gen_towns.house_prices(house, engine_houses)[0])
                if val < MIN_TAVERN_DAYS:
                    errors.append(f'{key}: tavern {house["id"]} {house["name"]} fills packs to {val:g} days, '
                                  f'off X1 at least {MIN_TAVERN_DAYS} (D-29: `price:`)')
            if house.get('alternate_of'):
                continue
            by_town.setdefault(house.get('town', town['town']), []).append(house)
        for name, arrival in (town.get('arrivals') or {}).items():
            if arrival.get('at') is None and not town.get('planned'):
                errors.append(f'{key}: arrival {name} has no coordinates (only a planned file may leave them out)')

    # residences and services per town (a house's `town`, else its file's), against WORLD_DESIGN 5. A cursed town
    # (houses that open by qbit) is checked twice: before its quest (only the houses open from day one, at most the
    # wilderness band) and after it (all of them, the town's role).
    for name, houses in sorted(by_town.items()):
        target = TOWN_TARGETS.get(name)
        if not target:
            continue
        residences = [h for h in houses if h['kind'] == 'residence' and not h.get('outside')]
        if abs(len(residences) - target[0]) > RESIDENCE_TOLERANCE:
            errors.append(f'{name}: {len(residences)} residences, WORLD_DESIGN has {target[0]}')
        kinds = {h['kind'] for h in houses}
        required, band = ROLE_SERVICES[target[1]]
        missing = required - kinds
        if missing:
            errors.append(f'{name} ({target[1]}) lacks {sorted(missing)}')
        if not any(k.endswith('_guild') for k in kinds) and target[1] in ('start', 'hub'):
            errors.append(f'{name} ({target[1]}) has no guild')
        services = [h for h in houses if h['kind'] != 'residence']
        if band and not band[0] <= len(services) <= band[1]:
            errors.append(f'{name} has {len(services)} services with its mirror, a {target[1]} town {band}')
        if name in CURSED:
            before = [h for h in services if not h.get('opens')]
            low, high = ROLE_SERVICES['wilderness'][1]
            if not low <= len(before) <= high:
                errors.append(f'{name} (cursed or staged) has {len(before)} services before its quest, at most {high}')
            # `open_before: true` marks a house open before the quest by design (WORLD_DESIGN 5.1, D-73 4c)
            open_houses = [h['name'] for h in houses if not h.get('opens') and not h.get('open_before')]
            if open_houses:
                waits.append(f'{name}: open before its quest: {", ".join(open_houses)}')

    # a stable or boat with routes but none open yet (every landing's map unbuilt or held by `after:`): no trips yet
    planned_keys = {town['key'] for town in towns if town.get('planned')}
    built_arrivals = {name for town in towns if not town.get('planned') for name in (town.get('arrivals') or {})}
    stops = {}
    for key, house, route in routes:
        stops.setdefault(house['id'], (key, house, []))[2].append(route)
    for key, house, house_routes in stops.values():
        if house.get('opens') or key in planned_keys:
            continue
        held = [r['to'] for r in house_routes if r.get('after') or r['to'] not in built_arrivals]
        if len(held) == len(house_routes):
            waits.append(f'{key}: house {house["id"]} {house["name"]}: no trip open yet, waits for {", ".join(held)}')

    # routes: a landing some file names (planned files too), and a qbit A3 has registered (a name waits for it)
    for key, house, route in routes:
        if route['to'] not in arrival_names:
            errors.append(f'{key}: route {route["id"]} of house {house["id"]} lands at {route["to"]}, which no file names')
        if route.get('qbit'):
            try:
                gen_towns.quest_qbit(route['qbit'])
            except gen_towns.TownError as error:
                waits.append(f'{key}: route {route["id"]} of house {house["id"]}: {error} (A3)')
    # later greetings (`greet_after`): an id of the NPC's block that no NPC and no other greeting has; the qbit is
    # A3's, and A3's quest step that sets it switches the greeting (evt.SetNPCGreeting in xeen_quests.lua)
    quests_lua = gen_towns.WORLD / 'events' / 'common' / 'xeen_quests.lua'
    quests_text = quests_lua.read_text() if quests_lua.exists() else ''
    greet_ids = Counter(entry['id'] for _, _, entry in later_greets)
    for key, npc, entry in later_greets:
        if entry['id'] in npc_ids:
            errors.append(f'{key}: npc {npc["id"]}: greeting {entry["id"]} is an NPC id (its own greeting)')
        if greet_ids[entry['id']] > 1:
            errors.append(f'{key}: npc {npc["id"]}: greeting {entry["id"]} used {greet_ids[entry["id"]]} times')
        try:
            gen_towns.quest_qbit(entry['after'])
        except gen_towns.TownError as error:
            waits.append(f'{key}: npc {npc["id"]} greeting {entry["id"]}: {error} (A3)')
        if f'SetNPCGreeting({npc["id"]}, {entry["id"]})' not in quests_text:
            waits.append(f'{key}: npc {npc["id"]} greeting {entry["id"]}: A3 calls evt.SetNPCGreeting({npc["id"]}, '
                         f'{entry["id"]}) where {entry["after"]} is set (xeen_quests.lua)')
    for counter, label in ((house_ids, 'house'), (npc_ids, 'npc'), (route_ids, 'route')):
        for value, count in counter.items():
            if count > 1:
                errors.append(f'{label} id {value} used {count} times')

    # teachers against the plan
    mastery_names = ['expert', 'master', 'grandmaster']
    # planned files count too: their teachers are fixed with their NPC ids, ahead of the map
    town_keys = {t['key'] for t in towns}
    planned = {}
    for skill, places in plan['offers'].items():
        for mastery, place in zip(mastery_names, places):
            planned.setdefault((skill, mastery), []).append(place)
    # second offers of a mastery (a teacher there before his Grandmaster offer opens: Gem, Errol)
    for extra in plan.get('extra') or []:
        key = (extra['skill'], extra['mastery'])
        if key not in planned:
            errors.append(f'plan: extra offer {extra} names a skill the plan does not hold')
        planned.setdefault(key, []).append(extra['place'])
    for (skill, mastery), places in planned.items():
        teachers = taught.get((skill, mastery), [])
        per_map = Counter(plan['places'][place]['map'] for place in places)
        for map_key, count in per_map.items():
            if map_key in town_keys:
                here = [t for t in teachers if t[0] == map_key]
                if len(here) != count:
                    errors.append(f'plan: {mastery} {skill} on {map_key} ({", ".join(places)}) is taught by '
                                  f'{len(here)} NPCs there, the plan has {count}')
    for (skill, mastery), teachers in taught.items():
        places = planned.get((skill, mastery))
        if places is None:
            errors.append(f'{mastery} {skill} is taught ({teachers}) but is not a skill of the plan')
            continue
        maps = {plan['places'][place]['map'] for place in places}
        for map_key, npc_id, _ in teachers:
            if map_key not in maps:
                errors.append(f'npc {npc_id} teaches {mastery} {skill}; the plan puts it at {", ".join(places)}')
    # An offer that opens by qbit is hidden through its engine topic id (A3's RegisterCanShowTopic from
    # gen_towns.teacher_gates()), which every Xeen NPC with that topic shares: it must be the only such offer.
    for (skill, mastery), teachers in taught.items():
        gated = [t for t in teachers if t[2]]
        if gated and len(teachers) > 1:
            errors.append(f'{mastery} {skill} opens by qbit at {gated} but is also taught by {teachers}')
    # D-73: the engine sells Master only to an Expert, so a Master place must not come before its Expert place (plan
    # levels). The user (U-2): a Grandmaster before its Master is no fault, so that order is not checked.
    notes = []
    for (skill, mastery), places in sorted(planned.items()):
        if mastery != 'master' or not planned.get((skill, 'expert')):
            continue
        expert_level = min(plan['places'][place]['level'] for place in planned[(skill, 'expert')])
        for place in places:
            if plan['places'][place]['level'] < expert_level:
                notes.append(f'plan: master {skill} at {place} (level {plan["places"][place]["level"]}) comes before '
                             f'its Expert (level {expert_level}, {", ".join(planned[(skill, "expert")])})')
    offers = sum(len(places) for places in planned.values())
    written = sum(len(v) for v in taught.values())
    errors += guild_book_errors(towns, rule_sections)
    # every built town map's house signs against their kinds (house_signs.py; the user 2026-11-22: the Adventurer's
    # Inn hung the tavern's mug)
    sign_errors, sign_warnings = house_signs.check_all()
    errors += sign_errors
    notes += sign_warnings
    if args.stock_scenario:
        print(f'wrote {STOCK_SCENARIO.relative_to(REPO)}: {stock_scenario(towns)} shops and guilds')

    try:
        tables = gen_towns.generate()
    except gen_towns.TownError as error:
        errors.append(f'gen_towns: {error}')
        tables = {}

    print(f'towns: {len(towns)} files, {len(house_ids)} houses, {len(npc_ids)} NPCs; teacher plan {offers} offers, '
          f'{written} in town files; tables: ' + ', '.join(f'{k} {len(v)}' for k, v in tables.items()))
    for line in waits:
        print(f'  wait  {line}')
    for line in notes:
        print(f'  WARN  {line}')
    for line in errors:
        print(f'  ERROR {line}')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
