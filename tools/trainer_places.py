#!/usr/bin/env python3
"""Writes assets_dev/engine/data_tables/trainer_places.txt: where each skill teacher's house is entered, for the
journal's trainer finder (level_generation/ui/journal_trainers_20261105/native/README.md).

    python3 -I tools/trainer_places.py [--check]

The game builds the trainer list itself from the tables it loads (TrainerDirectory); it does not read other maps, so
this tool locates the houses once, one row per house:
  - which houses: those of the NPCs whose npc.txt topic slots are mastery-teacher topics (teacher_topics.txt, or MM8's
    300-416 range as resolveMasteryTeacherTopic reads them), of the NPCs the MMMerge map-load script gives teacher
    topics (Global_mm6_mmmerge.lua enrothGrandmasterTeacherTopics) and MAW's extra houses (npc_extra_houses.yml);
  - a house's door: the map script event that enters it (evt.EnterHouse, or an exported enter_house action) and the
    BModel faces or entities of that map carrying the event (the scene yml's interactive faces when it has one), kind
    door, at the centre of those faces and entities;
  - a house inside a dungeon or castle: the shortest chain of map moves from an outdoor map to it, kind entrance,
    marked on that outdoor map's entrance; indoor when no outdoor map leads there.
Houses whose door event no face or entity carries are printed and left out (the unit test's skip list names them).
Positions are world coordinates; the journal map places them with the map's own transform. --check exits non-zero when
the file on disk differs from what the tool would write. A world package may add rows for its own houses with a
`trainer_places` append contribution in its world.yml (same columns).
"""

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from util.map_export import parse_odm_file  # noqa: E402

import yaml  # noqa: E402

TABLES = REPO / 'assets_dev' / 'engine' / 'data_tables'
WORLDS = REPO / 'assets_dev' / 'worlds'
MAW_EXTRA_HOUSES = REPO / 'assets_dev' / 'engine' / 'rulesets' / 'maw' / 'data' / 'npc_extra_houses.yml'
OUTPUT = TABLES / 'trainer_places.txt'
WORLD_IDS = ('mm6', 'mm7', 'mm8')
# The canonical skills by MM8 skill id (resolveMasteryTeacherTopic's fallback range covers ids 0-38).
SKILL_COUNT = 40

EVENT_START = re.compile(r'^(RegisterEvent|ReplaceMapEvent)\((\d+),', re.M)
ACTION_LINE = re.compile(r'^\s*\[(\d+)\] = \{ kind = "([a-z_]+)"(.*)\},?$', re.M)
SCRIPTED_TOPIC = re.compile(r'\{npc = (\d+), slot = (\d+), topic = (\d+)(?:, qbit = (\d+))?\}')


def table_rows(name):
    with open(TABLES / name, encoding='latin-1', newline='') as handle:
        rows = list(csv.reader(handle, delimiter='\t'))
    return [[cell.strip() for cell in row] for row in rows if row and row[0].strip().isdigit()]


def as_int(text, default=0):
    try:
        return int(text)
    except ValueError:
        return default


def teacher_topic_ids():
    """Topic ids that resolve as mastery-teacher topics."""
    topics = set()
    for row in table_rows('teacher_topics.txt'):
        row += [''] * (4 - len(row))
        if as_int(row[2], -1) in range(SKILL_COUNT) and as_int(row[3]) in (1, 2, 3):
            topics.add(int(row[0]))
    topics.update(range(300, 417))
    return topics


def scripted_topics():
    source = (WORLDS / 'mm6' / 'events' / 'Global_mm6_mmmerge.lua').read_text()
    table = re.search(r'enrothGrandmasterTeacherTopics = \{(.*?)\n\}', source, re.S)
    result = []
    for npc, _, topic, qbit in SCRIPTED_TOPIC.findall(table.group(1) if table else ''):
        entry = {'npc': int(npc), 'topic': int(topic)}
        if qbit:
            entry['qbit'] = int(qbit)
        result.append(entry)
    return result


def teacher_houses(topics, scripted):
    houses = set()
    npc_houses = {}
    for row in table_rows('npc.txt'):
        npc_id = int(row[0])
        house = as_int(row[6]) if len(row) > 6 else 0
        npc_houses[npc_id] = house
        if house and any(as_int(cell) in topics for cell in row[10:16]):
            houses.add(house)
    for entry in scripted:
        if npc_houses.get(entry['npc']):
            houses.add(npc_houses[entry['npc']])
    extra = yaml.safe_load(MAW_EXTRA_HOUSES.read_text()).get('extra_houses') or {}
    for house_ids in extra.values():
        houses.update(int(house) for house in house_ids)
    return houses


def map_stem_of_script(path):
    stem = re.sub(r'_mmmerge$', '', path.stem)
    return re.sub(r'_\d+$', '', stem)


def load_script_events():
    """Per map stem: event id -> {'houses': set, 'targets': set} from every script of that map."""
    events = defaultdict(lambda: defaultdict(lambda: {'houses': set(), 'targets': set()}))
    for world in WORLD_IDS:
        for path in sorted((WORLDS / world / 'events' / 'maps').glob('*.lua')):
            if path.stem.endswith('_intro'):
                continue
            stem = map_stem_of_script(path)
            source = path.read_text(errors='replace')
            for match in ACTION_LINE.finditer(source):
                event, kind, rest = int(match.group(1)), match.group(2), match.group(3)
                house = re.search(r'houseId = (\d+)', rest)
                target = re.search(r'targetMap = "([^"]+)"', rest)
                if kind == 'enter_house' and house:
                    events[stem][event]['houses'].add(int(house.group(1)))
                if target and kind in ('enter_dungeon', 'passage', 'teleport', 'leave_dungeon'):
                    events[stem][event]['targets'].add(target.group(1).lower())
            starts = [(m.start(), int(m.group(2))) for m in EVENT_START.finditer(source)]
            for index, (start, event) in enumerate(starts):
                end = starts[index + 1][0] if index + 1 < len(starts) else len(source)
                body = source[start:end]
                for house in re.findall(r'evt\.EnterHouse\((\d+)\)', body):
                    events[stem][event]['houses'].add(int(house))
                for target in re.findall(r'evt\.MoveToMap\([^)]*"([^"]+\.(?:blv|odm))"', body):
                    events[stem][event]['targets'].add(target.lower())
    return events


def find_map_file(file_name):
    for world in WORLD_IDS:
        path = WORLDS / world / 'maps' / file_name
        if path.exists():
            return path
    return None


OUTDOOR_CACHE = {}


def outdoor_event_points(map_file):
    """Event id -> [(x, y)]: the centres of the faces and the entities that carry the event on an outdoor map."""
    if map_file in OUTDOOR_CACHE:
        return OUTDOOR_CACHE[map_file]
    result = defaultdict(list)
    path = find_map_file(map_file)
    if path is not None:
        payload = parse_odm_file(path)['payload']
        face_events = {}
        for model in payload['bmodels']:
            for face in model['faces']:
                face_events[(model['index'], face['index'])] = face.get('cog_triggered_number') or 0
        entities = payload.get('entities') or []
        scene_path = path.with_suffix('.scene.yml')
        if scene_path.exists():
            scene = yaml.load(scene_path.read_text(), Loader=yaml.CSafeLoader)
            interactive = ((scene.get('bmodel_faces') or {}).get('interactive_faces')) or []
            face_events = {(f['bmodel_index'], f['face_index']): f.get('cog_triggered_number') or 0
                           for f in interactive}
            entities = scene.get('entities') or []
        for model in payload['bmodels']:
            vertices = model['vertices']
            for face in model['faces']:
                event = face_events.get((model['index'], face['index']), 0)
                if event:
                    points = [vertices[i] for i in face['vertex_indices'][:face['vertex_count']]]
                    result[event].append((sum(p['x'] for p in points) / len(points),
                                          sum(p['y'] for p in points) / len(points)))
        for entity in entities:
            position = entity.get('position') or {}
            for key in ('event_id_primary', 'event_id_secondary'):
                event = entity.get(key) or 0
                if event and 'x' in position:
                    result[event].append((position['x'], position['y']))
    OUTDOOR_CACHE[map_file] = result
    return result


def event_marker(map_file, event_ids):
    """The mean position of the first event (lowest id) that some face or entity of the map carries."""
    points = outdoor_event_points(map_file)
    for event in sorted(event_ids):
        hits = points.get(event)
        if hits:
            return round(sum(p[0] for p in hits) / len(hits)), round(sum(p[1] for p in hits) / len(hits))
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--check', action='store_true', help='fail when the file on disk is out of date')
    args = parser.parse_args()

    houses = {}
    for row in table_rows('house_data.txt'):
        row += [''] * (6 - len(row))
        houses[int(row[0])] = {'map': as_int(row[3]), 'name': row[5]}
    maps = {}
    continents = {}
    for row in table_rows('map_stats.txt'):
        maps[int(row[0])] = row[2].lower()
    for row in table_rows('bolster_maps.txt'):
        continents[int(row[0])] = as_int(row[2])
    ids_by_file = {file: map_id for map_id, file in maps.items()}

    scripted = scripted_topics()
    wanted = teacher_houses(teacher_topic_ids(), scripted)
    script_events = load_script_events()

    doors = defaultdict(list)  # house -> [(map file, event)]
    edges_into = defaultdict(list)  # map file -> [(source map file, event)]
    for stem, events in script_events.items():
        source = next((f for f in ids_by_file if Path(f).stem == stem), None)
        if source is None:
            continue
        for event, data in events.items():
            for house in data['houses']:
                doors[house].append((source, event))
            for target in data['targets']:
                if target != source:
                    edges_into[target].append((source, event))

    def continent_of(map_file):
        return continents.get(ids_by_file.get(map_file, -1), 0)

    def entrance(indoor_file):
        """(outdoor map, its events, chain of maps) of the shortest chain of map moves from an outdoor map to the
        indoor one, an outdoor map of the indoor map's own continent first."""
        parents = {indoor_file: None}
        frontier = [indoor_file]
        while frontier:
            found = [(node, source, event) for node in frontier for source, event in sorted(edges_into.get(node, []))
                     if source.endswith('.odm')]
            if found:
                home = continent_of(indoor_file)
                found.sort(key=lambda f: (continent_of(f[1]) != home, f[1], f[2]))
                first_hop, outdoor, _ = found[0]
                events = sorted(e for (hop, o, e) in found if o == outdoor and hop == first_hop)
                chain = [outdoor, first_hop]
                while parents[chain[-1]] is not None:
                    chain.append(parents[chain[-1]])
                return outdoor, events, chain
            following = []
            for node in frontier:
                for source, _ in sorted(edges_into.get(node, [])):
                    if source not in parents:
                        parents[source] = node
                        following.append(source)
            frontier = following
        return None

    rows = []
    left_out = []
    for house_id in sorted(wanted):
        house = houses.get(house_id)
        door_maps = sorted({m for m, _ in doors.get(house_id, [])})
        table_map = maps.get(house['map']) if house else None
        map_file = table_map if table_map in door_maps else (door_maps[0] if door_maps else table_map)
        if house is None or not door_maps:
            left_out.append((house_id, 'no map script enters it'))
            continue
        events = sorted(e for m, e in doors[house_id] if m == map_file)
        if map_file.endswith('.odm'):
            marker = event_marker(map_file, events)
            if marker is None:
                left_out.append((house_id, f'door event(s) {events} of {map_file} are on no face or entity'))
                continue
            rows.append([house_id, map_file, 'door', map_file, marker[0], marker[1], ''])
            continue
        found = entrance(map_file)
        marker = event_marker(found[0], found[1]) if found else None
        if marker is None:
            rows.append([house_id, map_file, 'indoor', '', '', '', ''])
        else:
            rows.append([house_id, map_file, 'entrance', found[0], marker[0], marker[1], '>'.join(found[2])])

    lines = [
        '# Generated by tools/trainer_places.py from the map scripts and maps: do not edit, rerun the tool after a '
        'teacher, house or map change.',
        '\t'.join(['House', 'Map', 'Kind', 'Marker map', 'X', 'Y', 'Entrance chain']),
    ]
    lines += ['\t'.join(str(cell) for cell in row) for row in rows]
    text = '\n'.join(lines) + '\n'

    if args.check:
        current = OUTPUT.read_text() if OUTPUT.exists() else ''
        if current != text:
            print(f'{OUTPUT.relative_to(REPO)} is out of date: run python3 -I tools/trainer_places.py')
            return 1
        print(f'{OUTPUT.relative_to(REPO)} is up to date')
        return 0

    OUTPUT.write_text(text)
    kinds = defaultdict(int)
    for row in rows:
        kinds[row[2]] += 1
    print(f'wrote {OUTPUT.relative_to(REPO)}: {len(rows)} houses {dict(kinds)}')
    for house_id, reason in left_out:
        print(f'  left out house {house_id}: {reason}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
