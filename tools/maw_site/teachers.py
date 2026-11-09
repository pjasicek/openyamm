#!/usr/bin/env python3
"""The skill teachers of a MAW game for the MAW guide (tools/maw_site/README.md).

    python3 -I tools/maw_site/teachers.py        # summary and spot checks

Enroth, Antagarich and Jadame: a port of TrainerDirectory::build (game/gameplay/TrainerDirectory.cpp) over the tables
a MAW game loads (maw_tables.py applies the ruleset's patches): every NPC of npc.txt whose topic slots hold mastery
teacher topics (teacher_topics.txt, or MM8's original 300-416 range as resolveMasteryTeacherTopic reads it), with the
Enroth grandmaster topics MMMerge's map-load script sets (Global_mm6_mmmerge.lua enrothGrandmasterTeacherTopics), in
its home house and in the extra houses MAW moves it to (rulesets/maw/data/npc_extra_houses.yml), placed by
trainer_places.txt (tools/trainer_places.py). One entry per skill, mastery, NPC and house, as the journal's trainer
finder lists them.

What MAW changes (game/rules/maw/MawSkillRules.cpp, MawSkillFormulas.cpp): for every skill but the eight utility ones
(Identify Item, Merchant, Repair, Perception, Disarm Traps, Identify Monster, Stealing, Alchemy) a mastery needs the
skill level of the game's mode (masteryRequiredLevel: Expert/Master/GM 4/7/10 Free, 6/12/20 Horizontal and Doom,
8/16/25 Road to Insanity, 10/24/40 Beyond Madness) and costs the mode's base price (1000/4000/20000 Free and
Horizontal, 2000/10000/50000 Doom, 10000/50000/250000 Road to Insanity, 15000/300000/1250000 Beyond Madness) times
(1 + the learner's other skills of that kind already at that mastery or remembered at it; MAW's four own skills do not
count): masteryTeacherCost. The utility skills keep Standard's 4/7/10 and the topic's price (or the engine's default
price for the skill). A topic's own Req. Skill, when set, is a further floor. Cover, Mana Shield, Enlightenment and
Retaliation have no teachers: their masteries come at fixed skill levels (teacherlessMasteryLadders).

Chedian (MM9) is not playable under MAW yet (rulesets/maw/ruleset.yml `worlds`, devdocs/maw/MM9_SUPPORT.md). Its
lessons come from the MM9 guide's data (output/mm9_site/data/guide.js, rebuilt when missing or older than its
sources); an MM9 lesson goes through the same evaluateSkillMasteryTraining as the others, so the same MAW requirements
and prices are given for it. MM9's "Learn" lessons (first rank) are left out like the other continents' learning
places.
"""

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import maw_tables as T  # noqa: E402

MASTERIES = {1: 'Expert', 2: 'Master', 3: 'Grandmaster'}
MASTERY_INDEX = {'Expert': 0, 'Master': 1, 'Grandmaster': 2}

# Skill ids are positions in SkillData.cpp's CanonicalSkillNames (teacher topics name skills by id).
SKILL_IDS = [
    'Staff', 'Sword', 'Dagger', 'Axe', 'Spear', 'Bow', 'Mace', 'Blaster', 'Shield', 'LeatherArmor', 'ChainArmor',
    'PlateArmor', 'FireMagic', 'AirMagic', 'WaterMagic', 'EarthMagic', 'SpiritMagic', 'MindMagic', 'BodyMagic',
    'LightMagic', 'DarkMagic', 'DarkElfAbility', 'VampireAbility', 'DragonAbility', 'IdentifyItem', 'Merchant',
    'RepairItem', 'Bodybuilding', 'Meditation', 'Perception', 'Regeneration', 'DisarmTraps', 'Dodging', 'Unarmed',
    'IdentifyMonster', 'Armsmaster', 'Stealing', 'Alchemy', 'Learning', 'Throwing', 'EnergyGuns', 'EnergyBlades',
    'ShieldTech', 'Hacking', 'Cover', 'ManaShield', 'Enlightenment', 'Retaliation', 'Cybernetics',
]
# SkillData.cpp DisplaySkillNames, with MAW's skillNames (Learning shows as Ascension).
DISPLAY_NAMES = {
    'Throwing': 'Throwing Weapons', 'LeatherArmor': 'Leather Armor', 'ChainArmor': 'Chain Armor',
    'PlateArmor': 'Plate Armor', 'FireMagic': 'Fire Magic', 'AirMagic': 'Air Magic', 'WaterMagic': 'Water Magic',
    'EarthMagic': 'Earth Magic', 'SpiritMagic': 'Spirit Magic', 'MindMagic': 'Mind Magic', 'BodyMagic': 'Body Magic',
    'LightMagic': 'Light Magic', 'DarkMagic': 'Dark Magic', 'DarkElfAbility': 'Dark Elf Ability',
    'VampireAbility': 'Vampire Ability', 'DragonAbility': 'Dragon Ability', 'IdentifyItem': 'Identify Item',
    'RepairItem': 'Repair Item', 'Bodybuilding': 'Body Building', 'IdentifyMonster': 'Identify Monster',
    'DisarmTraps': 'Disarm Traps', 'EnergyGuns': 'Energy Guns', 'EnergyBlades': 'Energy Blades',
    'ShieldTech': 'Shield Tech', 'ManaShield': 'Mana Shield',
}
DISPLAY_NAMES.update(T.ruleset().get('skillNames') or {})

# The modes a MAW game is played in, as the requirement and price tables tell them apart. Austerity combines with
# Free or Horizontal progression and reads like them; Doom reads Horizontal's requirements whatever its progression.
MODES = [
    {'id': 'free', 'name': 'Free'},
    {'id': 'horizontal', 'name': 'Horizontal'},
    {'id': 'doom', 'name': 'Doom'},
    {'id': 'road_to_insanity', 'name': 'Road to Insanity'},
    {'id': 'beyond_madness', 'name': 'Beyond Madness'},
]
# MawSkillFormulas.cpp mawMasteryRequiredLevel, by mode.
REQUIRED_LEVEL = {
    'free': (4, 7, 10), 'horizontal': (6, 12, 20), 'doom': (6, 12, 20), 'road_to_insanity': (8, 16, 25),
    'beyond_madness': (10, 24, 40),
}
STANDARD_LEVEL = (4, 7, 10)  # SkillRules::masteryRequiredLevel
# MawSkillFormulas.cpp mawTeacherBasePrice, by mode (MawPriceMode: Free and Horizontal are both Normal).
BASE_PRICE = {
    'free': (1000, 4000, 20000), 'horizontal': (1000, 4000, 20000), 'doom': (2000, 10000, 50000),
    'road_to_insanity': (10000, 50000, 250000), 'beyond_madness': (15000, 300000, 1250000),
}
# MawSkillFormulas.cpp mawIsHorizontalSkill: the skills whose requirement and price MAW rewrites are all but these.
UTILITY_SKILLS = {'IdentifyItem', 'Merchant', 'RepairItem', 'Perception', 'DisarmTraps', 'IdentifyMonster',
                  'Stealing', 'Alchemy'}
# mawSkillMasteryLadder: the skills without teachers and the base levels that bring their masteries.
TEACHERLESS = {
    'Cover': {'normal': (6, 12, 20), 'insanity': (8, 20, 30)},
    'ManaShield': {'normal': (6, 12, 20), 'insanity': (8, 20, 32)},
    'Enlightenment': {'normal': (6, 12, 20), 'insanity': (6, 12, 20)},
    'Retaliation': {'normal': (10, 24, 40), 'insanity': (10, 24, 40)},
}
# MawSkillRules::extraHouseSkills: where the teacherless skills are learned (Retaliation comes with Cover 30).
TEACHERLESS_LEARNED = {'Cover': 'training halls', 'ManaShield': 'magic shops', 'Enlightenment': 'magic shops',
                       'Retaliation': 'by itself when Cover reaches 30'}

# MasteryTeacherDialog.cpp masteryTeacherCost: the engine's price when a topic names none, by skill group.
_PRICE_GROUPS = [
    ({'Blaster'}, (2000, 5000, 10000)),
    ({'Shield', 'LeatherArmor', 'ChainArmor', 'PlateArmor'}, (1000, 3000, 7000)),
    ({'FireMagic', 'AirMagic', 'WaterMagic', 'EarthMagic', 'SpiritMagic', 'MindMagic', 'BodyMagic'},
     (1000, 4000, 8000)),
    ({'Staff', 'Sword', 'Dagger', 'Axe', 'Spear', 'Bow', 'Throwing', 'Mace', 'LightMagic', 'DarkMagic', 'Merchant',
      'Dodging', 'Unarmed', 'Armsmaster', 'Learning'}, (2000, 5000, 8000)),
    ({'IdentifyItem', 'RepairItem', 'Bodybuilding', 'Meditation', 'Perception', 'Regeneration', 'DisarmTraps',
      'IdentifyMonster', 'Stealing', 'Alchemy', 'DarkElfAbility', 'VampireAbility', 'DragonAbility'},
     (500, 2500, 6000)),
]
# masteryRequirementFailure: what a lesson asks besides the skill level and the previous mastery.
EXTRA_REQUIREMENTS = {
    ('Merchant', 'Master'): 'Personality 50',
    ('Bodybuilding', 'Master'): 'Endurance 50',
    ('Learning', 'Master'): 'Intellect 50',
    ('Dodging', 'Grandmaster'): 'Unarmed 10',
    ('Unarmed', 'Grandmaster'): 'Dodging 10',
}

MM9_GUIDE = T.REPO / 'output' / 'mm9_site' / 'data' / 'guide.js'
MM9_SOURCES = [T.REPO / 'tools' / 'mm9_site' / 'build_site.py',
               T.WORLDS / 'mm9' / 'data_tables' / 'skill_trainers.txt']
# The quest bits that hold a scripted lesson back, in words (the quest table has only a designer's note for them).
QUEST_NOTES = {1051: "after Snergle's axe is returned from Snergle's Caverns"}
SCRIPTED_TOPIC = re.compile(r'\{npc = (\d+), slot = (\d+), topic = (\d+)(?:, qbit = (\d+))?\}')


def skill_name(canonical: str) -> str:
    return DISPLAY_NAMES.get(canonical, canonical)


# SkillData.cpp SkillAliases: the short names tables use ("Leather", "Fire", "Repair").
SKILL_ALIASES = {
    'thrown': 'Throwing', 'throwingweapon': 'Throwing', 'throwingweapons': 'Throwing', 'leather': 'LeatherArmor',
    'chain': 'ChainArmor', 'plate': 'PlateArmor', 'fire': 'FireMagic', 'air': 'AirMagic', 'water': 'WaterMagic',
    'earth': 'EarthMagic', 'spirit': 'SpiritMagic', 'mind': 'MindMagic', 'body': 'BodyMagic', 'light': 'LightMagic',
    'dark': 'DarkMagic', 'darkelf': 'DarkElfAbility', 'vampire': 'VampireAbility', 'dragon': 'DragonAbility',
    'iditem': 'IdentifyItem', 'repair': 'RepairItem', 'bbuilding': 'Bodybuilding', 'meditate': 'Meditation',
    'disarm': 'DisarmTraps', 'disarmtrap': 'DisarmTraps', 'identmon': 'IdentifyMonster',
}


def canonical_skill(text: str) -> str:
    """A skill name as a table or MM9's guide data writes it ("Disarm Traps", "Leather") to the canonical name, the
    way canonicalSkillName looks it up (letters and digits, lower case; aliases first)."""
    key = re.sub(r'[^0-9a-z]', '', text.lower())
    if key in SKILL_ALIASES:
        return SKILL_ALIASES[key]
    for name in SKILL_IDS:
        if name.lower() == key or re.sub(r'[^0-9a-z]', '', skill_name(name).lower()) == key:
            return name
    return text


def default_price(canonical: str, slot: int) -> int:
    for skills, prices in _PRICE_GROUPS:
        if canonical in skills:
            return prices[slot]
    return 0


def needs(canonical: str, mastery: str, topic_required: int = 0) -> dict[str, int]:
    """The base skill level the lesson needs in each mode: the rules' level, and the topic's own when higher."""
    slot = MASTERY_INDEX[mastery]
    levels = {}
    for mode in MODES:
        table = STANDARD_LEVEL if canonical in UTILITY_SKILLS else REQUIRED_LEVEL[mode['id']]
        levels[mode['id']] = max(table[slot], topic_required)
    return levels


def prices(canonical: str, mastery: str, topic_gold: int = 0) -> tuple[dict[str, int], bool]:
    """The lesson's price per mode and whether it rises with the learner's other skills at that mastery."""
    slot = MASTERY_INDEX[mastery]
    if canonical in UTILITY_SKILLS:
        standard = topic_gold or default_price(canonical, slot)
        return {mode['id']: standard for mode in MODES}, False
    return {mode['id']: BASE_PRICE[mode['id']][slot] for mode in MODES}, True


def load_topics() -> dict[int, dict]:
    """resolveMasteryTeacherTopic over every topic id: teacher_topics.txt, then MM8's 300-416 fallback."""
    topics = {}
    for row in T.numbered_rows('teacher_topics.txt'):
        row += [''] * (7 - len(row))
        skill_id, rank = T.as_int(row[2], -1), T.as_int(row[3])
        if 0 <= skill_id < len(SKILL_IDS) and rank in MASTERIES:
            topics[int(row[0])] = {'skill': SKILL_IDS[skill_id], 'skill_id': skill_id, 'mastery': MASTERIES[rank],
                                   'gold': T.as_int(row[5]), 'required': T.as_int(row[6])}
    for topic_id in range(300, 417):
        topics.setdefault(topic_id, {'skill': SKILL_IDS[(topic_id - 300) // 3], 'skill_id': (topic_id - 300) // 3,
                                     'mastery': MASTERIES[(topic_id - 300) % 3 + 1], 'gold': 0, 'required': 0})
    return topics


def load_npcs() -> list[dict]:
    """NpcDialogTable: id, name, house (2D Location) and the topic slots (columns 10-15; empty cells are skipped, so
    later topics move up a slot, and trailing zeros are dropped)."""
    npcs = []
    for row in T.table('npc.txt'):
        if not row or not row[0].strip().isdigit():
            continue
        row = row + [''] * (16 - len(row))
        if row[1] == 'Boob':
            continue
        slots = [int(cell.strip()) for cell in row[10:16] if cell.strip().isdigit()]
        while slots and slots[-1] == 0:
            slots.pop()
        npcs.append({'id': int(row[0]), 'name': row[1].strip(), 'house': T.as_int(row[6]), 'topics': slots})
    return npcs


def scripted_topics() -> list[dict]:
    """MMMerge's Enroth grandmaster topics, which its map-load script sets in fixed NPC slots (a quest bit can hold
    one back: the slot stays empty until it is set)."""
    source = (T.WORLDS / 'mm6' / 'events' / 'Global_mm6_mmmerge.lua').read_text()
    block = re.search(r'enrothGrandmasterTeacherTopics = \{(.*?)\n\}', source, re.S)
    return [{'npc': int(npc), 'slot': int(slot), 'topic': int(topic), 'qbit': int(qbit) if qbit else 0}
            for npc, slot, topic, qbit in SCRIPTED_TOPIC.findall(block.group(1) if block else '')]


def load_places() -> dict[int, dict]:
    places = {}
    for row in T.numbered_rows('trainer_places.txt'):
        row += [''] * (7 - len(row))
        places[int(row[0])] = {'map': row[1].lower(), 'kind': row[2], 'marker_map': row[3].lower(),
                               'x': T.as_int(row[4], None), 'y': T.as_int(row[5], None),
                               'chain': row[6].split('>') if row[6] else []}
    return places


def quest_names() -> dict[int, str]:
    names = {}
    path = T.TABLES / 'english' / 'quests.txt'
    if path.exists():
        for row in T.numbered_rows('english/quests.txt'):
            row += [''] * (3 - len(row))
            # The note text, else the designers' note without its leading map number.
            names[int(row[0])] = row[1] or re.sub(r'^\d+\s+', '', row[2])
    return names


def build_continents() -> list[dict]:
    """Every lesson of MM6-MM8 as a MAW game's trainer finder lists it, before any party state."""
    topics = load_topics()
    npcs = load_npcs()
    houses = T.houses()
    maps = T.maps()
    ids_by_file = {m['file']: map_id for map_id, m in maps.items()}
    places = load_places()
    extra = {int(npc): [int(h) for h in house_ids] for npc, house_ids in
             (yaml.safe_load((T.MAW / 'data' / 'npc_extra_houses.yml').read_text()).get('extra_houses') or {}).items()}
    overrides = defaultdict(dict)
    gated = {}
    for entry in scripted_topics():
        overrides[entry['npc']][entry['slot']] = entry['topic']
        if entry['qbit']:
            gated[(entry['npc'], entry['topic'])] = entry['qbit']
    quests = quest_names()

    place_cache = {}

    def place_of(house_id: int):
        if house_id in place_cache:
            return place_cache[house_id]
        house = houses.get(house_id)
        place = places.get(house_id)
        map_id = house['map'] if house else 0
        if place and place['map'] in ids_by_file:
            map_id = ids_by_file[place['map']]
        result = None
        if house and map_id in maps:
            game_map = maps[map_id]
            result = {
                'house': '' if house['name'].strip() == 'House' else house['name'].strip(),
                'house_id': house_id,
                'house_type': house['type'],
                'continent': T.CONTINENTS.get(game_map['continent'], ''),
                'map': game_map['file'],
                'map_name': game_map['name'] or game_map['file'],
                'marker_map': place['marker_map'] if place else '',
                'x': place['x'] if place else None,
                'y': place['y'] if place else None,
                'kind': place['kind'] if place else '',
                'chain': place['chain'] if place else [],
            }
            if place and place['marker_map'] in ids_by_file:
                result['marker_map_name'] = maps[ids_by_file[place['marker_map']]]['name']
        place_cache[house_id] = result
        return result

    teachers = []
    listed = set()
    for npc in npcs:
        slots = list(npc['topics'])
        for slot, topic_id in overrides.get(npc['id'], {}).items():
            slots.extend([0] * (slot + 1 - len(slots)))
            slots[slot] = topic_id
        taught = [(topic_id, topics[topic_id]) for topic_id in slots if topic_id in topics]
        if not taught:
            continue
        homes = [(npc['house'], False)] if npc['house'] else []
        for house_id in extra.get(npc['id'], []):
            if house_id and all(house_id != h for h, _ in homes):
                homes.append((house_id, True))
        for house_id, moved in homes:
            place = place_of(house_id)
            if place is None:
                continue
            for topic_id, topic in taught:
                key = (topic['skill'], topic['mastery'], npc['id'], house_id)
                if key in listed:
                    continue
                listed.add(key)
                price, escalates = prices(topic['skill'], topic['mastery'], topic['gold'])
                entry = {
                    'skill': skill_name(topic['skill']),
                    'skill_id': topic['skill'],
                    'mastery': topic['mastery'],
                    'name': npc['name'],
                    'npc_id': npc['id'],
                    'topic_id': topic_id,
                    **place,
                    'gold': price['free'],
                    'prices': price,
                    'escalates': escalates,
                    'needs': needs(topic['skill'], topic['mastery'], topic['required']),
                    'moved': moved,
                }
                if (topic['skill'], topic['mastery']) in EXTRA_REQUIREMENTS:
                    entry['also'] = EXTRA_REQUIREMENTS[(topic['skill'], topic['mastery'])]
                qbit = gated.get((npc['id'], topic_id))
                if qbit:
                    entry['quest'] = QUEST_NOTES.get(qbit) or f"quest bit {qbit}: {quests.get(qbit, '')}".rstrip(': ')
                teachers.append(entry)
    return teachers


def mm9_guide() -> dict:
    """The MM9 guide's data, rebuilt first when it is missing or older than its sources."""
    stale = not MM9_GUIDE.exists() or any(
        source.exists() and source.stat().st_mtime > MM9_GUIDE.stat().st_mtime for source in MM9_SOURCES)
    if stale:
        subprocess.run([sys.executable, str(T.REPO / 'tools' / 'mm9_site' / 'build_site.py'), '--skip-images'],
                       cwd=T.REPO, check=True)
    text = MM9_GUIDE.read_text()
    return json.loads(text[text.index('{'):text.rindex('}') + 1])


def build_chedian(guide: dict | None = None) -> list[dict]:
    """MM9's lessons (Expert to Grandmaster) as a MAW game would price them. A lesson in an MM9 skill teaches every
    OpenYAMM skill listed under it, each its own lesson; when they differ, the strictest requirement and the highest
    price are given."""
    guide = guide or mm9_guide()
    teachers = []
    for lesson in guide['teachers']:
        if lesson['mastery'] not in MASTERY_INDEX:
            continue
        skills = [canonical_skill(s.strip()) for s in lesson['skills'].split(',')]
        level = {mode['id']: max(needs(s, lesson['mastery'], lesson.get('rank') or 0)[mode['id']] for s in skills)
                 for mode in MODES}
        price = {mode['id']: max(prices(s, lesson['mastery'], lesson.get('gold') or 0)[0][mode['id']]
                                 for s in skills) for mode in MODES}
        entry = {
            'skill': lesson['skill'],
            'skills': [skill_name(s) for s in skills],
            'mastery': lesson['mastery'],
            'name': lesson['name'].replace('|', ' / '),
            'house': '',
            'continent': 'Chedian',
            'map': lesson['at'][0]['map'] if lesson.get('at') else '',
            'map_name': lesson.get('region', ''),
            'region': lesson.get('region', ''),
            'kind': 'mm9',
            'gold': price['free'],
            'prices': price,
            'escalates': any(s not in UTILITY_SKILLS for s in skills),
            'needs': level,
            'moved': False,
            'at': lesson.get('at') or [],
        }
        if lesson.get('gated'):
            entry['quest'] = 'quest'
        if lesson.get('racial'):
            entry['racial'] = True
        teachers.append(entry)
    return teachers


def teacherless() -> list[dict]:
    rows = []
    for canonical, ladder in TEACHERLESS.items():
        levels = {}
        for mode in MODES:
            insanity = mode['id'] in ('road_to_insanity', 'beyond_madness')
            levels[mode['id']] = list(ladder['insanity' if insanity else 'normal'])
        rows.append({'skill': skill_name(canonical), 'skill_id': canonical, 'levels': levels,
                     'learned': TEACHERLESS_LEARNED[canonical]})
    return rows


def build(include_chedian: bool = True) -> dict:
    teachers = build_continents()
    if include_chedian:
        teachers += build_chedian()
    order = {'Enroth': 0, 'Antagarich': 1, 'Jadame': 2, 'Chedian': 3}
    teachers.sort(key=lambda t: (order.get(t['continent'], 9), t['skill'], MASTERY_INDEX[t['mastery']], t['name'],
                                 t.get('house_id') or 0))
    return {'teachers': teachers, 'teacherless': teacherless(), 'modes': MODES,
            'utility_skills': sorted(skill_name(s) for s in UTILITY_SKILLS)}


def main() -> int:
    data = build()
    teachers = data['teachers']
    counts = Counter((t['continent'], t['mastery']) for t in teachers)
    print(f"{len(teachers)} lessons")
    for continent in ('Enroth', 'Antagarich', 'Jadame', 'Chedian', ''):
        row = [counts.get((continent, m), 0) for m in MASTERY_INDEX]
        if any(row):
            print(f"  {continent or '(no continent)':11} Expert {row[0]:3}  Master {row[1]:3}  Grandmaster {row[2]:3}")
    print(f"  moved by MAW: {sum(t['moved'] for t in teachers)}, entrances: "
          f"{sum(t.get('kind') == 'entrance' for t in teachers)}, indoor without a way in: "
          f"{sum(t.get('kind') == 'indoor' for t in teachers)}, no place: "
          f"{sum(t.get('kind') == '' for t in teachers)}, quest-gated: {sum('quest' in t for t in teachers)}")
    skills_by_continent = defaultdict(set)
    for t in teachers:
        skills_by_continent[t['continent']].add((t['skill'], t['mastery']))
    for continent, lessons in skills_by_continent.items():
        all_skills = {t['skill'] for t in teachers if t['continent'] == continent}
        missing = sorted(f"{s} {m}" for s in all_skills for m in MASTERY_INDEX if (s, m) not in lessons)
        if missing and continent != 'Chedian':
            print(f"  {continent}: no teacher for {', '.join(missing)}")
    print('teacherless:', ', '.join(f"{t['skill']} {t['levels']['free']}" for t in data['teacherless']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
