#!/usr/bin/env python3
"""Build trainers.json for the journal "Trainers" page mockup: every skill teacher of the merged MMMerge world
(base game, no ruleset), with the outdoor map image and a marker in its pixels.

    python3 -I level_generation/ui/journal_trainers_20261105/data/scripts/build_trainers.py

Teacher selection mirrors the engine:
  - npc.txt topic slots (columns 10-15, NpcDialogTable::loadFromRows) that resolve as mastery-teacher topics
    (teacher_topics.txt, or the MM8 fallback range 300-416 in resolveMasteryTeacherTopic);
  - the scripted MM6 Grand Master topics (Global_mm6_mmmerge.lua enrothGrandmasterTeacherTopics) set on load;
  - William Lasker's enter hook (Global_mm7_mmmerge.lua) overwrites slots 0 and 1, so his npc.txt topics never show.
An NPC stands in its npc.txt "2D Location" house; a house's door is found from the map scripts (evt.EnterHouse).
Marker transform = OutdoorWorldRuntime::tryGetGameplayMinimapState + gameplayMinimapWorldToUv (+/-32768, flipV).
"""

import csv
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
from util.map_export import parse_blv_file, parse_odm_file  # noqa: E402

import yaml  # noqa: E402
from PIL import Image  # noqa: E402

TABLES = REPO / 'assets_dev' / 'engine' / 'data_tables'
WORLDS = REPO / 'assets_dev' / 'worlds'
OUT = Path(__file__).resolve().parents[1]
WORLD_IDS = ('mm6', 'mm7', 'mm8')

CANONICAL_SKILLS = [
    'Staff', 'Sword', 'Dagger', 'Axe', 'Spear', 'Bow', 'Mace', 'Blaster', 'Shield', 'LeatherArmor', 'ChainArmor',
    'PlateArmor', 'FireMagic', 'AirMagic', 'WaterMagic', 'EarthMagic', 'SpiritMagic', 'MindMagic', 'BodyMagic',
    'LightMagic', 'DarkMagic', 'DarkElfAbility', 'VampireAbility', 'DragonAbility', 'IdentifyItem', 'Merchant',
    'RepairItem', 'Bodybuilding', 'Meditation', 'Perception', 'Regeneration', 'DisarmTraps', 'Dodging', 'Unarmed',
    'IdentifyMonster', 'Armsmaster', 'Stealing', 'Alchemy', 'Learning', 'Throwing',
]
DISPLAY_SKILLS = {
    'Throwing': 'Throwing Weapons', 'LeatherArmor': 'Leather Armor', 'ChainArmor': 'Chain Armor',
    'PlateArmor': 'Plate Armor', 'FireMagic': 'Fire Magic', 'AirMagic': 'Air Magic', 'WaterMagic': 'Water Magic',
    'EarthMagic': 'Earth Magic', 'SpiritMagic': 'Spirit Magic', 'MindMagic': 'Mind Magic', 'BodyMagic': 'Body Magic',
    'LightMagic': 'Light Magic', 'DarkMagic': 'Dark Magic', 'DarkElfAbility': 'Dark Elf Ability',
    'VampireAbility': 'Vampire Ability', 'DragonAbility': 'Dragon Ability', 'IdentifyItem': 'Identify Item',
    'RepairItem': 'Repair Item', 'Bodybuilding': 'Body Building', 'IdentifyMonster': 'Identify Monster',
    'DisarmTraps': 'Disarm Traps',
}
MASTERY_NAMES = {1: 'Expert', 2: 'Master', 3: 'Grand Master'}
REQUIRED_LEVEL = {1: 4, 2: 7, 3: 10}  # SkillRules::masteryRequiredLevel
CONTINENT_NAMES = {1: 'Jadame', 2: 'Antagarich', 3: 'Enroth'}

# MasteryTeacherDialog.cpp masteryTeacherCost (base game; a topic's Req. Gold overrides it).
ARMOR = {'Shield', 'LeatherArmor', 'ChainArmor', 'PlateArmor'}
ELEMENT_SELF = {'FireMagic', 'AirMagic', 'WaterMagic', 'EarthMagic', 'SpiritMagic', 'MindMagic', 'BodyMagic'}
WEAPON_LIKE = {'Staff', 'Sword', 'Dagger', 'Axe', 'Spear', 'Bow', 'Throwing', 'Mace', 'LightMagic', 'DarkMagic',
               'Merchant', 'Dodging', 'Unarmed', 'Armsmaster', 'Learning'}
MISC = {'IdentifyItem', 'RepairItem', 'Bodybuilding', 'Meditation', 'Perception', 'Regeneration', 'DisarmTraps',
        'IdentifyMonster', 'Stealing', 'Alchemy', 'DarkElfAbility', 'VampireAbility', 'DragonAbility'}


def standard_cost(skill, mastery):
    if skill == 'Blaster':
        return {1: 2000, 2: 5000, 3: 10000}[mastery]
    if mastery == 1:
        if skill in ARMOR or skill in ELEMENT_SELF:
            return 1000
        if skill in WEAPON_LIKE:
            return 2000
        if skill in MISC:
            return 500
    if mastery == 2:
        if skill in ARMOR:
            return 3000
        if skill in ELEMENT_SELF:
            return 4000
        if skill in WEAPON_LIKE:
            return 5000
        if skill in MISC:
            return 2500
    if mastery == 3:
        if skill in ARMOR:
            return 7000
        if skill in WEAPON_LIKE or skill in ELEMENT_SELF:
            return 8000
        if skill in MISC:
            return 6000
    return 0


def extra_requirements(skill, mastery):
    # MasteryTeacherDialog.cpp masteryRequirementFailure
    extra = [f'{MASTERY_NAMES[mastery - 1]} mastery first'] if mastery > 1 else []
    if mastery == 2 and skill == 'Merchant':
        extra.append('50 base Personality')
    if mastery == 2 and skill == 'Bodybuilding':
        extra.append('50 base Endurance')
    if mastery == 2 and skill == 'Learning':
        extra.append('50 base Intellect')
    if mastery == 3 and skill == 'Dodging':
        extra.append('Unarmed skill 10')
    if mastery == 3 and skill == 'Unarmed':
        extra.append('Dodging skill 10')
    return extra


def table_rows(name):
    with open(TABLES / name, encoding='latin-1', newline='') as handle:
        rows = [row for row in csv.reader(handle, delimiter='\t')]
    return [[cell.strip() for cell in row] for row in rows if row and row[0].strip().isdigit()]


def as_int(text, default=0):
    try:
        return int(text)
    except ValueError:
        return default


def load_tables():
    teacher_topics = {}
    for row in table_rows('teacher_topics.txt'):
        row += [''] * (7 - len(row))
        teacher_topics[int(row[0])] = dict(skillId=as_int(row[2]), mastery=as_int(row[3]), textId=as_int(row[4]),
                                           gold=as_int(row[5]), skill=as_int(row[6]), note=row[1])
    npcs = {}
    for row in table_rows('npc.txt'):
        if row[1] == 'Boob':
            continue
        npcs[int(row[0])] = dict(name=row[1].strip(), house=as_int(row[6]),
                                 topics=[as_int(cell) for cell in row[10:16]])
    houses = {}
    for row in table_rows('house_data.txt'):
        row += [''] * (6 - len(row))
        houses[int(row[0])] = dict(type=row[2], map=as_int(row[3]), name=row[5])
    maps = {}
    for row in table_rows('map_stats.txt'):
        maps[int(row[0])] = dict(name=row[1], file=row[2].lower())
    continents = {}
    for row in table_rows('bolster_maps.txt'):
        continents[int(row[0])] = as_int(row[2])
    autonotes = {}
    for row in table_rows('teacher_autonotes.txt'):
        for index in range(2, len(row) - 1, 2):
            if row[index].isdigit() and row[index + 1].isdigit():
                autonotes[(int(row[0]), int(row[index]))] = int(row[index + 1])
    topic_titles = {}
    for row in table_rows('npc_topic.txt'):
        topic_titles[int(row[0])] = row[1] if len(row) > 1 else ""
    return teacher_topics, npcs, houses, maps, continents, autonotes, topic_titles


def resolve_teacher_topic(topic_id, teacher_topics):
    # MasteryTeacherDialog.cpp resolveMasteryTeacherTopic
    entry = teacher_topics.get(topic_id)
    if entry is None and 300 <= topic_id <= 416:
        entry = dict(skillId=(topic_id - 300) // 3, mastery=(topic_id - 300) % 3 + 1, textId=topic_id, gold=0, skill=0)
    if entry is None or entry['skillId'] >= len(CANONICAL_SKILLS) or entry['mastery'] not in MASTERY_NAMES:
        return None
    return entry


EVENT_START = re.compile(r'^(RegisterEvent|ReplaceMapEvent)\((\d+),', re.M)
ACTION_LINE = re.compile(r'^\s*\[(\d+)\] = \{ kind = "([a-z_]+)"(.*)\},?$', re.M)


def map_stem_of_script(path):
    stem = path.stem
    stem = re.sub(r'_mmmerge$', '', stem)
    stem = re.sub(r'_\d+$', '', stem)
    return stem


def load_scripts():
    """Per map file: {event id: {'houses': set, 'targets': set}} from every script of that map."""
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
                body = source[start:starts[index + 1][0] if index + 1 < len(starts) else len(source)]
                for house in re.findall(r'evt\.EnterHouse\((\d+)\)', body):
                    events[stem][event]['houses'].add(int(house))
                for target in re.findall(r'evt\.MoveToMap\([^)]*"([^"]+\.(?:blv|odm))"', body):
                    events[stem][event]['targets'].add(target.lower())
    return events


def find_map_file(file_name):
    for world in WORLD_IDS:
        path = WORLDS / world / 'maps' / file_name
        if path.exists():
            return world, path
    return None, None


ODM_CACHE = {}


def outdoor_event_points(map_file):
    """event id -> list of (x, y) points (face vertices or entity positions) carrying that event."""
    if map_file in ODM_CACHE:
        return ODM_CACHE[map_file]
    world, path = find_map_file(map_file)
    result = defaultdict(list)
    info = {'world': world, 'faceSource': None}
    if path is None:
        ODM_CACHE[map_file] = (result, info)
        return ODM_CACHE[map_file]
    payload = parse_odm_file(path)['payload']
    bmodels = payload['bmodels']
    face_events = {}
    for model in bmodels:
        for face in model['faces']:
            face_events[(model['index'], face['index'])] = face.get('cog_triggered_number') or 0
    entities = []
    scene_path = path.with_suffix('.scene.yml')
    if scene_path.exists():
        scene = yaml.load(scene_path.read_text(), Loader=yaml.CSafeLoader)
        interactive = ((scene.get('bmodel_faces') or {}).get('interactive_faces')) or []
        face_events = {(f['bmodel_index'], f['face_index']): f.get('cog_triggered_number') or 0 for f in interactive}
        entities = scene.get('entities') or []
        info['faceSource'] = scene_path.name
    else:
        info['faceSource'] = path.name
        entities = payload.get('entities') or []
    for model in bmodels:
        vertices = model['vertices']
        for face in model['faces']:
            event = face_events.get((model['index'], face['index']), 0)
            if event:
                points = [vertices[i] for i in face['vertex_indices'][:face['vertex_count']]]
                cx = sum(p['x'] for p in points) / len(points)
                cy = sum(p['y'] for p in points) / len(points)
                result[event].append(('face', cx, cy))
    for entity in entities:
        position = entity.get('position') or {}
        for key in ('event_id_primary', 'event_id_secondary'):
            event = entity.get(key) or 0
            if event and 'x' in position:
                result[event].append(('entity', position['x'], position['y']))
    ODM_CACHE[map_file] = (result, info)
    return ODM_CACHE[map_file]


INDOOR_CACHE = {}
EVENT_KEYS = {'cog_triggered', 'cog_triggered_number', 'event_id', 'event_id_primary', 'event_id_secondary', 'event'}


def collect_events(node, out):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in EVENT_KEYS and isinstance(value, int) and value:
                out.add(value)
            else:
                collect_events(value, out)
    elif isinstance(node, list):
        for value in node:
            collect_events(value, out)


def indoor_event_ids(map_file):
    """Events carried by faces or entities of an indoor map (BLV plus its scene yml)."""
    if map_file not in INDOOR_CACHE:
        _, path = find_map_file(map_file)
        events = set()
        if path is not None:
            payload = parse_blv_file(path)['payload']
            for face in payload['faces']:
                event = (face['face_param'] or {}).get('cog_triggered') or 0
                if event:
                    events.add(event)
            collect_events(payload.get('entities') or [], events)
            scene_path = path.with_suffix('.scene.yml')
            if scene_path.exists():
                collect_events(yaml.load(scene_path.read_text(), Loader=yaml.CSafeLoader), events)
        INDOOR_CACHE[map_file] = events
    return INDOOR_CACHE[map_file]


def event_marker(map_file, event_ids):
    points, _ = outdoor_event_points(map_file)
    for event in sorted(event_ids):
        hits = points.get(event)
        if hits:
            x = sum(p[1] for p in hits) / len(hits)
            y = sum(p[2] for p in hits) / len(hits)
            kinds = sorted({p[0] for p in hits})
            return dict(event=event, worldX=round(x), worldY=round(y), carriers=len(hits), carrierKind=kinds)
    return None


def world_to_pixel(x, y, width, height):
    # gameplayMinimapWorldToUv with worldMin/Max = -/+32768, flipU false, flipV true.
    u = (x + 32768.0) / 65536.0
    v = 1.0 - (y + 32768.0) / 65536.0
    return round(u * width, 1), round(v * height, 1)


def map_image_source(map_file):
    stem = Path(map_file).stem
    for world in WORLD_IDS:
        for ext in ('.png', '.bmp'):
            path = WORLDS / world / 'icons_x2' / (stem + ext)
            if path.exists():
                return path
    return None


def main():
    teacher_topics, npcs, houses, maps, continents, autonotes, topic_titles = load_tables()
    maps_by_file = {entry['file']: (map_id, entry) for map_id, entry in maps.items()}
    scripts = load_scripts()
    notes = []

    # --- which NPC teaches which topic -----------------------------------------------------------------------
    slots = {npc_id: list(npc['topics']) + [0] * (6 - len(npc['topics'])) for npc_id, npc in npcs.items()}
    conditions = {}
    mm6_global = (WORLDS / 'mm6' / 'events' / 'Global_mm6_mmmerge.lua').read_text()
    table = re.search(r'enrothGrandmasterTeacherTopics = \{(.*?)\n\}', mm6_global, re.S).group(1)
    scripted = set()
    for npc, slot, topic, qbit in re.findall(
            r'\{npc = (\d+), slot = (\d+), topic = (\d+)(?:, qbit = (\d+))?\}', table):
        npc, slot, topic = int(npc), int(slot), int(topic)
        slots.setdefault(npc, [0] * 6)[slot] = topic
        scripted.add((npc, topic))
        if qbit:
            conditions[(npc, topic)] = f'QBit {qbit} set'
    mm7_global = (WORLDS / 'mm7' / 'events' / 'Global_mm7_mmmerge.lua').read_text()
    if 'context.npcId ~= 354' in mm7_global:
        lasker = [t for t in slots.get(354, [])[:2] if resolve_teacher_topic(t, teacher_topics)]
        slots[354][0] = slots[354][1] = 0
        if lasker:
                notes.append(dict(npcId=354, npcName=npcs[354]['name'], topics=lasker, reason=(
                'the MMMerge enter hook in Global_mm7_mmmerge.lua rewrites topic slots 0 and 1, hiding these.')))

    # --- house doors from the map scripts --------------------------------------------------------------------
    house_doors = defaultdict(list)  # house id -> [(map file, event id)]
    edges_into = defaultdict(list)  # target map -> [(source map file, event id)]
    for stem, events in scripts.items():
        source_file = next((f for f in maps_by_file if Path(f).stem == stem), None)
        if source_file is None:
            continue
        for event, data in events.items():
            for house in data['houses']:
                house_doors[house].append((source_file, event))
            for target in data['targets']:
                if target != source_file:
                    edges_into[target].append((source_file, event))

    def continent_of(map_file):
        map_id = maps_by_file.get(map_file, (None,))[0]
        return continents.get(map_id, 0) if map_id is not None else 0

    def entrance_chain(indoor_file):
        """Shortest chain outdoor.odm -> ... -> indoor_file, preferring the indoor map's continent."""
        home = continent_of(indoor_file)
        parents = {indoor_file: None}
        frontier = [indoor_file]
        found = []
        while frontier and not found:
            for node in frontier:
                for source, event in sorted(edges_into.get(node, [])):
                    if source.endswith('.odm'):
                        found.append((node, source, event))
            if found:
                break
            following = []
            for node in frontier:
                for source, event in sorted(edges_into.get(node, [])):
                    if source not in parents:
                        parents[source] = (node, event)
                        following.append(source)
            frontier = following
        if not found:
            return None
        found.sort(key=lambda f: (continent_of(f[1]) != home, f[1], f[2]))
        first_hop, outdoor, event = found[0]
        chain = [outdoor, first_hop]
        node = first_hop
        while parents[node] is not None:
            node = parents[node][0]
            chain.append(node)
        all_events = sorted(e for (fh, o, e) in found if o == outdoor and fh == first_hop)
        return dict(outdoor=outdoor, events=all_events, chain=chain)

    maw_extra = yaml.safe_load((REPO / 'assets_dev' / 'engine' / 'rulesets' / 'maw' / 'data' /
                                'npc_extra_houses.yml').read_text())['extra_houses']

    def house_location(house_id):
        house = houses.get(house_id)
        doors = house_doors.get(house_id, [])
        door_maps = sorted({d[0] for d in doors})
        table_map = maps.get(house['map'], {}).get('file') if house else None
        if table_map in door_maps:
            map_file = table_map
        elif door_maps:
            map_file = door_maps[0]
        else:
            map_file = table_map
        return house, doors, door_maps, map_file, table_map

    rows = []
    seen = set()
    skipped_unplaced = []
    images = {}
    for npc_id in sorted(slots):
        npc = npcs.get(npc_id)
        if npc is None:
            continue
        for slot_index, topic_id in enumerate(slots[npc_id]):
            topic = resolve_teacher_topic(topic_id, teacher_topics) if topic_id else None
            if topic is None:
                continue
            skill = CANONICAL_SKILLS[topic['skillId']]
            mastery = topic['mastery']
            house_id = npc['house']
            if house_id == 0:
                skipped_unplaced.append(dict(npcId=npc_id, npcName=npc['name'], topicId=topic_id))
                continue
            house, doors, door_maps, map_file, table_map = house_location(house_id)
            if (npc_id, topic_id) in seen:
                continue
            seen.add((npc_id, topic_id))
            if house is None or not doors:
                notes.append(dict(npcId=npc_id, npcName=npc['name'], topicId=topic_id, houseId=house_id, reason=(
                    'house is not entered by any map script event (no evt.EnterHouse), unreachable')))
                continue
            map_id, map_entry = maps_by_file.get(map_file, (None, {}))
            continent_id = continents.get(map_id, 0)
            row = dict(
                skill=DISPLAY_SKILLS.get(skill, skill),
                skillCanonical=skill,
                skillId=topic['skillId'],
                mastery=MASTERY_NAMES[mastery],
                npcName=npc['name'],
                npcId=npc_id,
                topicId=topic_id,
                topicTitle=topic_titles.get(topic_id, ''),
                topicSlot=slot_index,
                topicSource='script' if (npc_id, topic_id) in scripted else 'npc.txt',
                houseName=house['name'],
                houseId=house_id,
                mapFile=map_file,
                mapName=map_entry.get('name'),
                continent=CONTINENT_NAMES.get(continent_id),
                continentId=continent_id,
                world=find_map_file(map_file)[0] if map_file else None,
            )
            if table_map and table_map != map_file:
                row['houseDataMapFile'] = table_map
            if (npc_id, topic_id) in conditions:
                row['condition'] = conditions[(npc_id, topic_id)]
            gold = topic['gold'] or standard_cost(skill, mastery)
            row['requirements'] = dict(
                skillLevel=max(topic['skill'], REQUIRED_LEVEL[mastery]),
                gold=gold,
                goldSource='teacher_topics.txt Req. Gold' if topic['gold'] else 'standard cost (masteryTeacherCost)',
                extra=extra_requirements(skill, mastery),
            )
            autonote = autonotes.get((topic_id, npc_id))
            if autonote is not None:
                row['autonoteId'] = autonote

            outdoor = None
            marker_kind = None
            marker = None
            if map_file and map_file.endswith('.odm'):
                outdoor = map_file
                events = sorted(e for (m, e) in doors if m == map_file)
                found = event_marker(map_file, events)
                if found is None:
                    notes.append(dict(npcId=npc_id, npcName=npc['name'], topicId=topic_id, skill=row['skill'],
                                      mastery=row['mastery'], houseId=house_id, houseName=house['name'],
                                      mapFile=map_file, reason=(
                        f'door event(s) {events} of {map_file} are not on any BModel face or decoration of the map '
                        '(scene yml and ODM checked), so the house cannot be entered')))
                    continue
                marker_kind = 'house'
                marker = found
                row['doorEvents'] = events
            elif map_file:
                events = sorted(e for (m, e) in doors if m == map_file)
                row['doorEvents'] = events
                row['doorEventOnIndoorFace'] = bool(set(events) & indoor_event_ids(map_file))
                chain = entrance_chain(map_file)
                if chain:
                    outdoor = chain['outdoor']
                    found = event_marker(outdoor, chain['events'])
                    if found:
                        marker_kind = 'entrance'
                        marker = found
                    row['entranceChain'] = chain['chain']
                    row['entranceEvents'] = chain['events']
            row['outdoorMapFile'] = outdoor
            if outdoor:
                out_id, out_entry = maps_by_file.get(outdoor, (None, {}))
                row['outdoorMapName'] = out_entry.get('name')
                if continent_of(outdoor) != continent_id:
                    row['outdoorContinent'] = CONTINENT_NAMES.get(continent_of(outdoor))
                image = map_image_source(outdoor)
                if image is not None:
                    if outdoor not in images:
                        with Image.open(image) as source_image:
                            images[outdoor] = (image, source_image.size)
                    width, height = images[outdoor][1]
                    row['mapImage'] = f'maps/{Path(outdoor).stem}.png'
                    row['mapImageSize'] = [width, height]
                    if marker:
                        px, py = world_to_pixel(marker['worldX'], marker['worldY'], width, height)
                        row['marker'] = dict(x=px, y=py, worldX=marker['worldX'], worldY=marker['worldY'],
                                             event=marker['event'], carriers=marker['carriers'])
            row.setdefault('marker', None)
            row['markerKind'] = marker_kind if row['marker'] else None
            if npc_id in maw_extra:
                extra = []
                for extra_house in maw_extra[npc_id]:
                    h, _, _, extra_map, _ = house_location(extra_house)
                    extra.append(dict(houseId=extra_house, houseName=h['name'] if h else None, mapFile=extra_map,
                                      continent=CONTINENT_NAMES.get(continent_of(extra_map)) if extra_map else None))
                row['mawExtraHouses'] = extra
            if slot_index >= 5:
                row['warning'] = 'topic in slot 6; the engine shows at most five topics'
            rows.append(row)

    if skipped_unplaced:
        notes.append(dict(reason=(
            'npc.txt rows with a teacher topic but no house (2D Location 0) and no script that places them: '
            'never met in the base game.'), npcs=skipped_unplaced))

    # --- outputs ------------------------------------------------------------------------------------------------
    (OUT / 'maps').mkdir(parents=True, exist_ok=True)
    for outdoor, (source, _) in sorted(images.items()):
        with Image.open(source) as image:
            image.convert('RGB').save(OUT / 'maps' / f'{Path(outdoor).stem}.png', optimize=True)

    continent_order = {'Jadame': 0, 'Antagarich': 1, 'Enroth': 2}
    rows.sort(key=lambda r: (continent_order.get(r['continent'], 9), r['skillId'], list(MASTERY_NAMES.values())
                             .index(r['mastery']), r['npcName']))
    data = dict(
        generatedBy='level_generation/ui/journal_trainers_20261105/data/scripts/build_trainers.py',
        transform=dict(
            description='pixel = ((x + 32768) / 65536 * width, (32768 - y) / 65536 * height)',
            source='game/outdoor/OutdoorWorldRuntime.cpp tryGetGameplayMinimapState (texture = map file stem, '
                   'world bounds +/-32768) and game/ui/GameplayMinimapTransform.h gameplayMinimapWorldToUv '
                   '(flipU false, flipV true)'),
        continents=[dict(id=k, name=v) for k, v in CONTINENT_NAMES.items()],
        trainers=rows,
        notes=notes,
    )
    (OUT / 'trainers.json').write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n')
    print(f'{len(rows)} rows, {sum(1 for r in rows if r["marker"])} with marker, {len(images)} map images')


if __name__ == '__main__':
    main()
