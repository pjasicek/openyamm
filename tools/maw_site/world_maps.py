#!/usr/bin/env python3
"""The MM6-MM8 maps of the MAW guide: names, continents, MAW level bands, refill days, map images and markers.

    python3 -I tools/maw_site/world_maps.py [--out output/maw_site]   # summary; writes the images when --out is given

Markers come from the map scripts and the maps themselves, located the way tools/trainer_places.py locates teacher
houses: an event's position is the centre of the faces and entities that carry it. Outdoor maps use their journal map
image (icons_x2/<stem>); indoor maps use the floor plan dungeon_plans.py draws from the BLV.
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(REPO))
import trainer_places as places  # noqa: E402

TABLES = REPO / 'assets_dev' / 'engine' / 'data_tables'
WORLDS = REPO / 'assets_dev' / 'worlds'
MAW_DATA = REPO / 'assets_dev' / 'engine' / 'rulesets' / 'maw' / 'data'

# bolster_maps.txt continent ids.
CONTINENTS = {
    3: {'id': 'enroth', 'name': 'Enroth', 'world': 'mm6'},
    2: {'id': 'antagarich', 'name': 'Antagarich', 'world': 'mm7'},
    1: {'id': 'jadame', 'name': 'Jadame', 'world': 'mm8'},
}
WORLD_IDS = ('mm6', 'mm7', 'mm8')

# An outdoor map image spans -32768..32768 in x and y with north at the top (MapPresentation defaults).
OUTDOOR_HALF = 32768

HORIZONTAL_MULTIPLIER = 2.5
# mawArenaMap: arenas pick their fighters by the party's level, not by a band.
ARENA_MAPS = {'d42.blv', '7d05.blv', 'zarena.blv', 'thearena.blv'}

# MawMonsterRules::mapRespawnDays: map ids that never refill.
NEVER_REFILL = ((1, 8), (13, 13), (62, 70), (72, 74), (99, 100), (140, 141), (143, 151))

# house_data.txt type -> (marker type, what the house is). Marker types are the MM9 guide's plus guild, castle, house
# and entrance.
HOUSE_TYPES = {
    'Weapon Shop': ('vendor', 'Weapon shop'), 'Armor Shop': ('vendor', 'Armour shop'),
    'Magic Shop': ('vendor', 'Magic shop'), 'Alchemist': ('vendor', 'Alchemist'),
    'General Store': ('vendor', 'General store'), 'Temple': ('service', 'Temple'),
    'Tavern': ('service', 'Tavern'), 'Bank': ('service', 'Bank'), 'Training': ('service', 'Training hall'),
    'Town Hall': ('service', 'Town hall'), 'Circus': ('service', 'Circus'),
    "The Adventurer's Inn": ('service', "Adventurer's Inn"), 'Boats': ('transport', 'Boats'),
    'Stables': ('transport', 'Stables'), 'Throne': ('castle', 'Throne room'),
    'Castle Entrance': ('castle', 'Castle'), 'Dungeon Ent': ('entrance', 'Entrance'), 'Seer': ('house', 'Seer'),
    'Jail': ('house', 'Jail'), 'House': ('house', ''),
}
GUILD = re.compile(r'Guild|guild')

FEATURES = (
    (re.compile(r'well|fountain|shrine|altar', re.I), 'bonus'),
    (re.compile(r'obelisk', re.I), 'hint'),
    (re.compile(r'pedestal|statue', re.I), 'objective'),
)

REGISTER = re.compile(r'^RegisterEvent\((\d+),\s*(?:"((?:[^"\\]|\\.)*)"|nil)', re.M)
AUTONOTE = re.compile(r'SetAutonote\(\d+\)\s*--\s*(.+)$', re.M)
STATUS = re.compile(r'evt\.StatusText\("((?:[^"\\]|\\.)*)"\)')
MOVE = re.compile(r'evt\.MoveToMap\(([^)]*)"([^"]+\.(?:blv|odm))"\)', re.I)


def table_rows(name):
    with open(TABLES / name, encoding='latin-1', newline='') as handle:
        rows = list(csv.reader(handle, delimiter='\t'))
    return [[cell.strip() for cell in row] for row in rows if row and row[0].strip().isdigit()]


def as_int(text, default=0):
    try:
        return int(text)
    except ValueError:
        return default


def map_world(file_name):
    for world in WORLD_IDS:
        if (WORLDS / world / 'maps' / file_name).exists():
            return world
    return None


def load_maps():
    """file -> map record for every MM6-MM8 map the engine tables list."""
    continents = {int(row[0]): as_int(row[2]) for row in table_rows('bolster_maps.txt') if len(row) > 2}
    maps = {}
    for row in table_rows('map_stats.txt'):
        row += [''] * (8 - len(row))
        file_name = row[2].lower()
        world = map_world(file_name) if file_name else None
        continent = CONTINENTS.get(continents.get(int(row[0]), 0))
        # MMMerge's placeholder rows (zddb*, zdtl*, zdwj*) are named "pending" and lead nowhere.
        if world is None or continent is None or row[1].strip().lower() == 'pending':
            continue
        map_id = int(row[0])
        refill = max(as_int(row[6]), 0)
        if any(first <= map_id <= last for first, last in NEVER_REFILL):
            refill = 0
        maps[file_name] = {
            'id': Path(file_name).stem, 'num': map_id, 'file': file_name, 'name': row[1] or file_name,
            'continent': continent['id'], 'world': world,
            'kind': 'outdoor' if file_name.endswith('.odm') else 'dungeon', 'refill_days': refill,
        }
    return maps


def maw_round(value):
    """MAW's round half up."""
    return int(value + 0.5) if value >= 0 else -int(-value + 0.5)


def map_levels(file_name, levels_data):
    """The levels of the map's three native families (MawMonsterLevels.cpp) for each progression."""
    band = (levels_data.get('bands') or {}).get(file_name)
    if not band:
        return None
    low, mid, high = (float(x) for x in band)
    mean = (low + mid + high) / 3
    result = {'free': [int(low), int(mid), int(high)], 'band': [low, mid, high]}
    starter = file_name in set(levels_data.get('horizontal_starter_maps') or [])
    if starter:
        result['starter'] = True
    if file_name in ARENA_MAPS:
        result['arena'] = True
    if file_name in set((levels_data.get('madness') or {}).get('starting_maps') or []):
        result['madness_start'] = True
    if starter:
        # A starter map's monsters follow the party, from the band up to 2.5 times it.
        result['horizontal'] = [int(low), int(high)]
        result['horizontal_cap'] = maw_round(high * HORIZONTAL_MULTIPLIER)
    else:
        slots = [max(slot * HORIZONTAL_MULTIPLIER - 9 + (mean - slot) * 1.5, 5.0) for slot in (low, mid, high)]
        result['horizontal'] = [maw_round(min(slots)), maw_round(max(slots))]
    madness = ((levels_data.get('madness') or {}).get('levels') or {}).get(file_name)
    if madness:
        result['madness'] = int(madness)
    return result


def script_paths(world, stem):
    folder = WORLDS / world / 'events' / 'maps'
    return [path for path in sorted(folder.glob(f'{stem}*.lua'))
            if places.map_stem_of_script(path) == stem and not path.stem.endswith('_intro')]


def unescape(text):
    return text.replace('\\"', '"').replace('\\\\', '\\')


def load_events(world, stem):
    """(event id -> {name, houses, targets, note}, entrance house -> target map) from every script of the map."""
    events = defaultdict(lambda: {'name': '', 'houses': set(), 'targets': set(), 'note': ''})
    house_moves = {}
    for path in script_paths(world, stem):
        source = path.read_text(errors='replace')
        for match in places.ACTION_LINE.finditer(source):
            event, kind, rest = int(match.group(1)), match.group(2), match.group(3)
            house = re.search(r'houseId = (\d+)', rest)
            target = re.search(r'targetMap = "([^"]+)"', rest)
            name = re.search(r'targetName = "((?:[^"\\]|\\.)*)"', rest)
            if kind == 'enter_house' and house:
                events[event]['houses'].add(int(house.group(1)))
            if target and kind in ('enter_dungeon', 'passage', 'teleport', 'leave_dungeon'):
                events[event]['targets'].add(target.group(1).lower())
            if name and not events[event]['name']:
                events[event]['name'] = unescape(name.group(1))
        starts = [(m.start(), int(m.group(1)), unescape(m.group(2) or '')) for m in REGISTER.finditer(source)]
        for index, (start, event, name) in enumerate(starts):
            end = starts[index + 1][0] if index + 1 < len(starts) else len(source)
            body = source[start:end]
            entry = events[event]
            if name and not entry['name']:
                entry['name'] = name.strip()
            entry['houses'].update(int(h) for h in re.findall(r'evt\.EnterHouse\((\d+)\)', body))
            for move in MOVE.finditer(body):
                target = move.group(2).lower()
                entry['targets'].add(target)
                args = [a.strip() for a in move.group(1).split(',')]
                # The seventh argument is the dungeon-entrance house whose Enter button makes this move.
                if len(args) > 6 and args[6].isdigit() and int(args[6]):
                    house_moves[int(args[6])] = target
            if not entry['note']:
                note = AUTONOTE.search(body)
                status = STATUS.search(body)
                if note:
                    entry['note'] = note.group(1).strip()
                elif status:
                    entry['note'] = unescape(status.group(1)).strip()
    return events, house_moves


def load_houses():
    houses = {}
    for row in table_rows('house_data.txt'):
        row += [''] * (8 - len(row))
        houses[int(row[0])] = {'type': row[2], 'map': as_int(row[3]), 'name': row[5], 'owner': row[6],
                               'title': row[7]}
    return houses


def load_npcs_by_house():
    result = defaultdict(list)
    for row in table_rows('npc.txt'):
        row += [''] * (7 - len(row))
        house = as_int(row[6])
        if house and row[1]:
            result[house].append({'id': int(row[0]), 'name': row[1]})
    return result


def house_marker_type(house):
    kind = house['type']
    if GUILD.search(kind):
        return 'guild', kind.replace('guild', 'Guild')
    return HOUSE_TYPES.get(kind, ('house', ''))


def feature_type(name):
    for pattern, kind in FEATURES:
        if pattern.search(name):
            return kind
    return None


def outdoor_uv(x, y):
    u = (x + OUTDOOR_HALF) / (2 * OUTDOOR_HALF)
    v = (OUTDOOR_HALF - y) / (2 * OUTDOOR_HALF)
    return min(max(u, 0.0), 1.0), min(max(v, 0.0), 1.0)


def plan_uv(plan, x, y):
    min_x, min_y, max_x, max_y = plan['bounds']
    u = (x - min_x) / max(max_x - min_x, 1e-6)
    v = (max_y - y) / max(max_y - min_y, 1e-6)
    return min(max(u, 0.0), 1.0), min(max(v, 0.0), 1.0)


def mean_point(points):
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)


def edge_markers(record, maps, travels):
    """Markers on the four edges of an outdoor map that lead to a neighbour (outdoor_travels.txt)."""
    row = travels.get(record['file'])
    if not row:
        return []
    out = []
    for index, (edge, u, v) in enumerate((('north', 0.5, 0.015), ('south', 0.5, 0.985), ('west', 0.015, 0.5),
                                         ('east', 0.985, 0.5))):
        target = row[1 + index * 3].lower() if len(row) > 1 + index * 3 else ''
        days = row[3 + index * 3] if len(row) > 3 + index * 3 else ''
        if target and target in maps:
            detail = f'Walk off the {edge} edge' + (f': {days} days of travel' if days else '')
            out.append({'id': f'edge{edge}', 't': 'exit', 'n': maps[target]['name'], 'd': detail, 'u': round(u, 4),
                        'v': round(v, 4), 'map': maps[target]['id']})
    return out


def load_travels():
    with open(TABLES / 'outdoor_travels.txt', encoding='latin-1', newline='') as handle:
        rows = list(csv.reader(handle, delimiter='\t'))
    return {row[0].strip().lower(): [cell.strip() for cell in row] for row in rows[1:] if row and row[0].strip()}


def build_pois(record, maps, houses, npcs_by_house, travels, plan_events=None):
    """The markers of one map. plan_events: event points of an indoor map (dungeon_plans.indoor_event_points)."""
    stem = record['id']
    events, house_moves = load_events(record['world'], stem)
    if record['kind'] == 'outdoor':
        points = places.outdoor_event_points(record['file'])
        to_uv = outdoor_uv
    else:
        points = plan_events or {}
        to_uv = None
    pois = []
    seen_houses = set()
    seen_targets = set()
    for event in sorted(events):
        hits = points.get(event)
        if not hits:
            continue
        x, y = mean_point(hits)
        uv = to_uv(x, y) if to_uv else (x, y)
        data = events[event]
        poi = None
        for house_id in sorted(data['houses']):
            house = houses.get(house_id)
            if house is None or house_id in seen_houses:
                continue
            seen_houses.add(house_id)
            kind, label = house_marker_type(house)
            people = [npc['name'] for npc in npcs_by_house.get(house_id, [])]
            name = house['name'] if house['name'] not in ('', 'House') else ''
            if not name:
                name = people[0] if people else data['name'] if data['name'] not in ('', 'House') else 'Home'
                label = label or 'Home'
            poi = {'id': f'h{house_id}', 't': kind, 'n': name, 'house': house_id}
            if label:
                poi['k'] = label
            if people:
                poi['people'] = people
            if kind == 'entrance':
                target = house_moves.get(house_id) or next((t for t in sorted(data['targets']) if t in maps), None)
                if target in maps:
                    poi['map'] = maps[target]['id']
                    seen_targets.add(target)
            break
        if poi is None and data['targets']:
            target = next((t for t in sorted(data['targets']) if t in maps and t != record['file']), None)
            if target and target not in seen_targets:
                seen_targets.add(target)
                into = maps[target]
                kind = 'entrance' if record['kind'] == 'outdoor' and into['kind'] == 'dungeon' else 'exit'
                poi = {'id': f'm{into["id"]}', 't': kind, 'n': into['name'], 'map': into['id']}
                if data['name'] and data['name'] != into['name']:
                    poi['d'] = data['name']
        if poi is None and data['name']:
            kind = feature_type(data['name'])
            if kind:
                poi = {'id': f'e{event}', 't': kind, 'n': data['name']}
                if data['note']:
                    poi['d'] = data['note']
        if poi is None:
            continue
        poi['u'], poi['v'] = round(uv[0], 4), round(uv[1], 4)
        pois.append(poi)
    if record['kind'] == 'outdoor':
        pois += edge_markers(record, maps, travels)
    return pois


def outdoor_image(record):
    folder = WORLDS / record['world'] / 'icons_x2'
    for suffix in ('.png', '.bmp', '.PNG', '.BMP'):
        path = folder / f'{record["id"]}{suffix}'
        if path.exists():
            return path
    return None


def write_webp(source, target, longest=1400):
    from PIL import Image
    with Image.open(source) as image:
        image = image.convert('RGB')
        scale = min(1.0, longest / max(image.size))
        if scale < 1.0:
            image = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target, 'WEBP', quality=86, method=5)
        return image.width, image.height


def image_entry(target, stem):
    from PIL import Image
    with Image.open(target) as image:
        width, height = image.size
    return {'img': f'img/maps/{stem}.webp', 'thumb': f'img/maps/{stem}_thumb.webp', 'w': width, 'h': height}


def build(out_dir, skip_images=False, only=None):
    """Every MM6-MM8 map with its levels, image and markers; images go to out_dir/img/maps/."""
    maps = load_maps()
    levels_data = yaml.safe_load((MAW_DATA / 'map_levels.yml').read_text())
    houses = load_houses()
    npcs_by_house = load_npcs_by_house()
    travels = load_travels()
    image_dir = Path(out_dir) / 'img' / 'maps'
    plan_dir = Path(out_dir) / 'work' / 'plans'
    plan_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for file_name, record in sorted(maps.items(), key=lambda item: item[1]['num']):
        if only and file_name not in only:
            continue
        entry = dict(record)
        levels = map_levels(file_name, levels_data)
        if levels:
            entry['levels'] = levels
        stem = record['id']
        target = image_dir / f'{stem}.webp'
        thumb = image_dir / f'{stem}_thumb.webp'
        reuse = skip_images and target.exists() and thumb.exists()
        if record['kind'] == 'outdoor':
            source = outdoor_image(record)
            if source is not None:
                if not reuse:
                    write_webp(source, target)
                    write_webp(source, thumb, longest=320)
                entry.update(image_entry(target, stem))
            entry['pois'] = build_pois(record, maps, houses, npcs_by_house, travels)
        else:
            import dungeon_plans  # noqa: E402  (beside this file)
            info = plan_dir / f'{stem}.json'
            if reuse and info.exists():
                plan = json.loads(info.read_text())
            else:
                plan_png = plan_dir / f'{stem}.png'
                plan = dungeon_plans.render_plan(file_name, plan_png)
                if plan is not None:
                    write_webp(plan_png, target, longest=1600)
                    write_webp(plan_png, thumb, longest=320)
                    info.write_text(json.dumps(plan))
            entry['pois'] = []
            if plan is not None:
                entry.update(image_entry(target, stem))
                raw = build_pois(record, maps, houses, npcs_by_house, travels,
                                 dungeon_plans.indoor_event_points(file_name))
                for poi in raw:
                    poi['u'], poi['v'] = (round(c, 4) for c in plan_uv(plan, poi['u'], poi['v']))
                entry['pois'] = raw
        result.append(entry)

    # Each indoor map's ways in: the markers of other maps that lead to it.
    by_id = {entry['id']: entry for entry in result}
    for entry in result:
        for poi in entry.get('pois', []):
            target = by_id.get(poi.get('map'))
            if target is not None and poi['t'] in ('entrance', 'exit'):
                target.setdefault('entrances', []).append({'map': entry['id'], 'poi': poi['id']})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--out', type=Path, help='write the map images under <out>/img/maps')
    parser.add_argument('--only', nargs='*', help='map files to build')
    args = parser.parse_args()
    out = args.out or Path('/tmp/maw_site_world_maps')
    result = build(out, skip_images=args.out is None, only=set(args.only) if args.only else None)
    counts = defaultdict(int)
    for entry in result:
        counts[(entry['continent'], entry['kind'])] += 1
    print(dict(counts))
    types = defaultdict(int)
    for entry in result:
        for poi in entry.get('pois', []):
            types[poi['t']] += 1
    print(dict(types))
    return 0


if __name__ == '__main__':
    sys.exit(main())
