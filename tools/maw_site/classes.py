#!/usr/bin/env python3
"""The MAW classes for the MAW guide (tools/maw_site/README.md).

    python3 -I tools/maw_site/classes.py        # summary

Generated from the tables a MAW game loads (maw_tables.py applies the ruleset's patches): the classes and their
lines (class_extra.txt kind and step), HP and SP (class_multipliers.txt, with MawClassRules' fixed pools), mastery
caps (class_skills.txt), starting skills (class_starting_skills.txt), the race rules (rulesets/maw/content/
race_skills.yml and MawClassRules.cpp's race tables). Elder and Ultimate follow MawClassRules::promotionFactor: a final
class whose kind's promotion is done on two worlds takes floor(per level × 1.25), on three floor(× 1.5).

Promotions: promotions.yml says what each Enroth, Antagarich and Jadame quest is; MAW's rulesets/maw/data/
promotions.yml says which quest bits count as each kind's promotion on each world (MawPromotions: any of a world's
bits, MM8's award or second bit), and for MAW's own kinds which first-tier bits give the middle step. A quest counts
for a line when its bits (or award) are among the line's. Chedian's promotions come from the MM9 guide: MM9's quests
promote the classes MM9.Promotions names (worlds/mm9/events/common/mm9_common.lua), and MAW counts a quest for a line
when 90000 + its done key (worlds/mm9/dialogue/promotions.yml) is in the line's `mm9` bits (final) or `mid` bits.
The hand-kept notes are in class_notes.yml.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import maw_tables as T  # noqa: E402
import teachers  # noqa: E402

MASTERY_LETTERS = {'B': 'N', 'E': 'E', 'M': 'M', 'G': 'G', '-': '', '': ''}
WORLD_OF = {'Enroth': 'mm6', 'Antagarich': 'mm7', 'Jadame': 'mm8'}
CONTINENT_ORDER = ['Enroth', 'Antagarich', 'Jadame', 'Chedian']
GROUP_ORDER = {'classic': 0, 'new': 1, 'racial': 2, 'other': 3}
RACES = {0: 'Human', 1: 'Vampire', 2: 'Dark Elf', 3: 'Minotaur', 4: 'Troll', 5: 'Dragon', 6: 'Undead', 7: 'Elf',
         8: 'Goblin', 9: 'Dwarf', 10: 'Zombie'}
RACE_ENUM = {'Human': 0, 'Vampire': 1, 'DarkElf': 2, 'Minotaur': 3, 'Troll': 4, 'Dragon': 5, 'Undead': 6, 'Elf': 7,
             'Goblin': 8, 'Dwarf': 9, 'Zombie': 10}
ELEMENTS = {'FireElement': 'Fire', 'AirElement': 'Air', 'WaterElement': 'Water', 'EarthElement': 'Earth',
            'MindElement': 'Mind', 'BodyElement': 'Body'}
CLASS_RULES = T.REPO / 'game' / 'rules' / 'maw' / 'MawClassRules.cpp'
# MawClassSpells.cpp mawClassSchoolName: the skills a line shows under its own names.
SCHOOL_NAMES = {
    11: {'FireMagic': 'Combat', 'AirMagic': 'Subtlety', 'WaterMagic': 'Poisons', 'EarthMagic': 'Assassination'},
    18: {'WaterMagic': 'Frost', 'BodyMagic': 'Blood', 'DarkMagic': 'Unholy'},
    4: {'Unarmed': 'Fangs', 'Dodging': 'Scales'},
}


def key(name: str) -> str:
    """Class names compared the way canonicalClassName looks them up: no spaces or case."""
    return re.sub(r'[\s_\-]', '', name).lower()


def class_rows() -> list[dict]:
    """class_extra.txt: id, kind, step and display name of every class."""
    rows = []
    for row in T.numbered_rows('class_extra.txt'):
        row += [''] * (4 - len(row))
        if row[3] and row[3] != 'n/u':
            rows.append({'id': int(row[0]), 'kind': T.as_int(row[1]), 'step': T.as_int(row[2]), 'name': row[3]})
    return rows


def multipliers() -> dict[int, dict]:
    """class_multipliers.txt by class id (its rows follow the class ids, named by canonical class name)."""
    result = {}
    for class_id, row in enumerate(T.table('class_multipliers.txt')[1:]):
        if len(row) >= 6 and row[0].strip():
            result[class_id] = {'base_hp': T.as_int(row[1]), 'hp': T.as_int(row[2]), 'base_sp': T.as_int(row[3]),
                                   'sp': T.as_int(row[4]), 'stat': row[5].strip()}
    return result


def skill_caps() -> tuple[list[str], dict[int, dict[str, str]]]:
    """class_skills.txt: skill rows, class columns in class id order; the caps by class id then canonical skill."""
    rows = T.table('class_skills.txt')
    header = [c.strip() for c in rows[0]]
    skills, caps = [], defaultdict(dict)
    for row in rows[1:]:
        skill = teachers.canonical_skill(row[0].strip()) if row and row[0].strip() else ''
        if not skill:
            continue
        skills.append(skill)
        for index in range(1, len(header)):
            if header[index]:
                caps[index - 1][skill] = MASTERY_LETTERS.get(T.cell(row, index), T.cell(row, index))
    return skills, caps


def starting_skills() -> dict[str, dict]:
    rows = T.table('class_starting_skills.txt')
    header = [c.strip() for c in rows[0]]
    result = {}
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        free = [header[i] for i in range(1, len(header)) if T.cell(row, i) == 'F']
        choice = [header[i] for i in range(1, len(header)) if T.cell(row, i) == 'C']
        result[key(row[0])] = {'free': free, 'choice': choice}
    return result


def race_rules() -> list[dict]:
    """Per race: the mastery rules (race_skills.yml), the flat skill bonuses and the resistances (MawClassRules.cpp)."""
    races = defaultdict(lambda: {'skills': [], 'bonus_skills': [], 'resistances': []})
    data = yaml.safe_load((T.MAW / 'content' / 'race_skills.yml').read_text())
    for rule in data.get('rules') or []:
        name = RACES.get(rule['race_id'], rule['race'])
        skill = teachers.skill_name(rule['skill'])
        if 'add' in rule:
            races[name]['skills'].append(f"{skill} cap +{rule['add']} rank")
        if rule.get('max_mastery') == 'none':
            races[name]['skills'].append(f"no {skill}")
        elif rule.get('max_mastery'):
            races[name]['skills'].append(f"{skill} at most {rule['max_mastery'].title()}")
        if rule.get('min_mastery'):
            races[name]['skills'].append(f"{skill} at least {rule['min_mastery'].title()}")
    source = CLASS_RULES.read_text()
    flat = re.search(r'FlatSkillBonuses = \{\{(.*?)\}\};', source, re.S)
    for race, skills in re.findall(r'\{(\w+), \{([^}]*)\}\}', flat.group(1) if flat else ''):
        names = [teachers.skill_name(s) for s in re.findall(r'"(\w+)"', skills)]
        races[RACES[RACE_ENUM[race]]]['bonus_skills'] = names
    table = re.search(r'RaceResistanceTable = \{\{(.*?)\}\};', source, re.S)
    for race, elements, base, per_level in re.findall(r'\{(\w+), \{([^}]*)\}, (\d+), (\d+)\}',
                                                      table.group(1) if table else ''):
        names = [ELEMENTS[e] for e in re.findall(r'&(\w+)', elements)]
        races[RACES[RACE_ENUM[race]]]['resistances'].append(
            {'elements': names, 'base': int(base), 'per_level': int(per_level)})
    if not flat or not table:
        raise RuntimeError('MawClassRules.cpp race tables not found: update classes.py race_rules()')
    result = []
    for race_id in sorted(RACES):
        name = RACES[race_id]
        if name in races:
            entry = races[name]
            notes = []
            if entry['bonus_skills']:
                notes.append(f"+3 to {', '.join(entry['bonus_skills'])}, and +1 more per 10 trained levels "
                             "(also while unlearned).")
            for res in entry['resistances']:
                elements = ', '.join(res['elements'])
                notes.append(f"Immune to {elements}." if res['base'] == 0 else
                             f"{elements} resistance +{res['base']}, and +{res['per_level']} per level.")
            if entry['skills']:
                notes.append('Skill limits: ' + '; '.join(entry['skills']) + '.')
            result.append({'race': name, 'notes': notes})
    extra = yaml.safe_load((HERE / 'class_notes.yml').read_text()).get('races') or {}
    for entry in result:
        entry['notes'] += extra.get(entry['race'], [])
    return result


def npc_places() -> dict[int, dict]:
    """Every promoter's place: their house's door (a map script entering the house, as tools/trainer_places.py finds
    it), else the map whose script makes them speak."""
    import trainer_places
    events = trainer_places.load_script_events()
    house_maps = defaultdict(set)
    for stem, by_event in events.items():
        for data in by_event.values():
            for house in data['houses']:
                house_maps[house].add(stem)
    speaks = defaultdict(set)
    for world in ('mm6', 'mm7', 'mm8'):
        for path in (T.WORLDS / world / 'events' / 'maps').glob('*.lua'):
            stem = trainer_places.map_stem_of_script(path)
            for npc in re.findall(r'evt\.SpeakNPC\((\d+)\)', path.read_text(errors='replace')):
                speaks[int(npc)].add(stem)
    return {'house_maps': house_maps, 'speaks': speaks}


def promotion_quests(class_by_name: dict[str, dict]) -> list[dict]:
    data = yaml.safe_load((HERE / 'promotions.yml').read_text())
    npcs = {n['id']: n for n in teachers.load_npcs()}
    houses = T.houses()
    maps = T.maps()
    map_by_stem = {m['file'].rsplit('.', 1)[0]: m for m in maps.values()}
    places = npc_places()
    quest_text = {}
    for row in T.numbered_rows('english/quests.txt'):
        if len(row) > 1:
            quest_text[int(row[0])] = row[1].strip().strip('"')
    result = []
    for quest in data['quests']:
        npc = npcs[quest['npc']]
        house = houses.get(npc['house']) if npc['house'] else None
        stems = sorted(places['house_maps'].get(npc['house'], ())) if house else []
        stems = stems or sorted(places['speaks'].get(npc['id'], ()))
        game_map = None
        if quest.get('map'):
            game_map = map_by_stem.get(quest['map'].rsplit('.', 1)[0])
        elif stems:
            game_map = map_by_stem.get(stems[0])
        elif house and house['map'] in maps:
            game_map = maps[house['map']]
        task = quest.get('task') or quest_text.get(quest['quest'], '')
        if not task:
            raise ValueError(f"promotion quest {quest['id']} has no task text")
        for source, target in quest['promotes'].items():
            for name in (source, target):
                if key(name) not in class_by_name:
                    raise ValueError(f"promotion quest {quest['id']}: unknown class {name!r}")
        result.append({
            'id': quest['id'],
            'continent': quest['continent'],
            'giver': npc['name'],
            'npc_id': npc['id'],
            'house': house['name'].strip() if house and house['name'].strip() not in ('House', '') else '',
            'house_id': npc['house'] if house else None,
            'map': game_map['file'] if game_map else '',
            'map_name': game_map['name'] if game_map else '',
            'task': ' '.join(task.split()),
            'path': quest.get('path', ''),
            'promotes': {class_by_name[key(s)]['name']: class_by_name[key(t)]['name']
                         for s, t in quest['promotes'].items()},
            'bits': quest['bits'],
            'award': quest.get('award', 0),
        })
    return result


# MM9 keys are quest bits 90000 + key under MAW (rulesets/maw/data/promotions.yml).
MM9_KEY_BIT = 90000
# The Lich has no promoter: the Lich Lab's Transmutation Engine gives key 299 (worlds/mm9/events/maps/lichlab.lua).
MM9_LICH_DONE_KEY = 299


def mm9_done_bits() -> dict[str, int]:
    """MM9 promotion name -> the quest bit MAW reads when it is done."""
    data = yaml.safe_load((T.WORLDS / 'mm9' / 'dialogue' / 'promotions.yml').read_text())
    bits = {entry['promotion']: MM9_KEY_BIT + entry['done_key'] for entry in data['promotions']}
    bits['Lich'] = MM9_KEY_BIT + MM9_LICH_DONE_KEY
    return bits


def chedian_promotions(class_by_name: dict[str, dict]) -> list[dict]:
    guide = teachers.mm9_guide()
    done_bits = mm9_done_bits()
    result = []
    for promotion in guide.get('promotions') or []:
        at = (promotion.get('at') or [{}])[0]
        task = promotion.get('note') or ''
        if not task:
            steps = [q.replace('-', ' ') for q in promotion.get('quests') or []]
            task = '; '.join(steps).capitalize() + '.' if steps else ''
        promotes = {}
        for source, target in promotion.get('classes') or []:
            if key(source) in class_by_name and key(target) in class_by_name:
                promotes[class_by_name[key(source)]['name']] = class_by_name[key(target)]['name']
        result.append({'id': f"chedian_{key(promotion['to'])}", 'continent': 'Chedian',
                       'giver': (at.get('name') or '').replace('|', ' / '), 'map': at.get('map', ''),
                       'poi': at.get('poi', ''), 'task': task, 'promotes': promotes,
                       'mm9_promotion': promotion['to'], 'bit': done_bits.get(promotion['to'], 0)})
    return result


def build() -> dict:
    rows = class_rows()
    by_name = {key(r['name']): r for r in rows}
    mults = multipliers()
    skills, caps = skill_caps()
    starting = starting_skills()
    notes = yaml.safe_load((HERE / 'class_notes.yml').read_text())
    maw_kinds = yaml.safe_load((T.MAW / 'data' / 'promotions.yml').read_text())['kinds']
    quests = promotion_quests(by_name)
    chedian = chedian_promotions(by_name)

    classes = []
    for kind, info in notes['kinds'].items():
        members = sorted((r for r in rows if r['kind'] == kind), key=lambda r: (r['step'], r['id']))
        if not members:
            raise ValueError(f'class kind {kind} has no classes')
        names = {r['name'] for r in members}
        rule = maw_kinds.get(kind)
        dragon_line = kind == 4
        tiers = []
        for member in members:
            m = mults[member['id']]
            base_sp = 60 if member['id'] == 10 else m['base_sp']  # MawClassRules::baseMaxSpellPoints
            tier = {'name': member['name'], 'step': member['step'], 'hp': m['hp'], 'sp': m['sp'],
                    'base_hp': m['base_hp'], 'base_sp': base_sp}
            if member['step'] == 2 and rule:
                tier['elder'] = {'hp': int(m['hp'] * 1.25), 'sp': int(m['sp'] * 1.25)}
                tier['ultimate'] = {'hp': int(m['hp'] * 1.5), 'sp': int(m['sp'] * 1.5)}
            tiers.append(tier)
        first = mults[members[0]['id']]
        if kind == 11:
            sp_kind = 'energy'
        elif kind == 18 or dragon_line:
            sp_kind = 'fixed'
        elif all(mults[r['id']]['stat'] == 'None' and mults[r['id']]['sp'] == 0 for r in members):
            sp_kind = 'none'
        else:
            sp_kind = 'personality'
        skill_rows = []
        for skill in skills:
            row = [caps[r['id']].get(skill, '') for r in members]
            if any(row):
                own = SCHOOL_NAMES.get(kind, {}).get(skill)
                name = f"{own} ({teachers.skill_name(skill)})" if own else teachers.skill_name(skill)
                skill_rows.append({'skill': name, 'skill_id': skill, 'caps': row})

        promotions = []
        for quest in quests:
            world = WORLD_OF[quest['continent']]
            bits = set(quest['bits'])
            counts_final = False
            counts_mid = False
            if rule:
                if world == 'mm8':
                    counts_final = bool(bits & {rule['mm8'], rule.get('mm8_qbit2', -1)}) or \
                        (quest['award'] and quest['award'] == rule.get('mm8_award'))
                else:
                    counts_final = bool(bits & set(rule[world]))
                counts_mid = bool(bits & set(rule.get('mid') or []))
            own = any(source in names for source in quest['promotes'])
            own_mid = own and any(r['step'] == 1 and r['name'] in quest['promotes'].values() for r in members) \
                and not any(r['step'] == 2 and r['name'] in quest['promotes'].values() for r in members)
            if not (counts_final or counts_mid or own_mid):
                continue
            if counts_final:
                gained = [r['name'] for r in members if r['step'] == 2]
                step = 'final'
            else:
                gained = [r['name'] for r in members if r['step'] == 1]
                step = 'middle'
            entry = {k: quest[k] for k in ('id', 'continent', 'giver', 'npc_id', 'house', 'house_id', 'map',
                                           'map_name', 'task', 'path')}
            entry['step'] = step
            entry['tier'] = ' / '.join(gained)
            entry['by_quest'] = {s: t for s, t in quest['promotes'].items() if s in names}
            entry['counts'] = counts_final or counts_mid
            promotions.append(entry)
        for promotion in chedian:
            mine = {s: t for s, t in promotion['promotes'].items() if s in names}
            counts_final = bool(rule) and promotion['bit'] in set(rule.get('mm9') or [])
            counts_mid = bool(rule) and promotion['bit'] in set(rule.get('mid') or [])
            if not (mine or counts_final or counts_mid):
                continue
            if counts_final:
                step = 'final'
                tier = ' / '.join(r['name'] for r in members if r['step'] == 2)
                outside = sorted({t for t in mine.values() if t not in names})
                if outside:
                    # MM9's Wizard-to-Lich quest makes a Lich (another line) but counts as this line's promotion.
                    tier = f'{" / ".join(outside)} (counts for {tier})'
            elif counts_mid:
                step = 'middle'
                tier = ' / '.join(r['name'] for r in members if r['step'] == 1)
            else:
                # A target outside the line (MM9's Wizard to Lich) leaves it for another line's final class.
                step = 'final' if any(r['step'] == 2 and r['name'] in mine.values() for r in members) \
                    or any(target not in names for target in mine.values()) else 'middle'
                tier = ' / '.join(sorted(set(mine.values())))
            promotions.append({**{k: promotion[k] for k in ('id', 'continent', 'giver', 'map', 'poi', 'task')},
                               'step': step, 'tier': tier, 'by_quest': mine,
                               'counts': counts_final or counts_mid})
        promotions.sort(key=lambda p: (CONTINENT_ORDER.index(p['continent']), p['step'] != 'middle', p['id']))

        start = starting.get(key(members[0]['name']), {'free': [], 'choice': []})
        classes.append({
            'id': key(info.get('line_name') or info['name']).replace('(', '').replace(')', ''),
            'kind': kind,
            'name': info.get('line_name') or info['name'],
            'group': info['group'],
            'tiers': tiers,
            'base_hp': first['base_hp'],
            'base_sp': 60 if dragon_line else first['base_sp'],
            'sp_kind': sp_kind,
            'skills': skill_rows,
            'starting': {'free': [teachers.skill_name(s) for s in start['free']],
                         'choice': [teachers.skill_name(s) for s in start['choice']]},
            'notes': info.get('notes') or [],
            'promotions': promotions,
            'promotes_across': bool(rule),
        })
    classes.sort(key=lambda c: (GROUP_ORDER[c['group']], c['kind']))
    return {
        'classes': classes,
        'shared_notes': notes.get('shared') or [],
        'races': race_rules(),
        'elder': {'factor': 1.25, 'worlds': 2, 'rounding': 'down'},
        'ultimate': {'factor': 1.5, 'worlds': 3, 'rounding': 'down'},
        'mastery_letters': {'N': 'Novice', 'E': 'Expert', 'M': 'Master', 'G': 'Grandmaster', '': 'cannot learn'},
    }


def main() -> int:
    data = build()
    for c in data['classes']:
        line = ' → '.join(' / '.join(t['name'] for t in c['tiers'] if t['step'] == s)
                          for s in sorted({t['step'] for t in c['tiers']}))
        hp = '/'.join(str(t['hp']) for t in c['tiers'])
        sp = '/'.join(str(t['sp']) for t in c['tiers'])
        by_continent = defaultdict(list)
        for p in c['promotions']:
            by_continent[p['continent']].append(f"{p['step'][0]}:{p['giver']}")
        print(f"{c['kind']:2} {c['name']:22} {c['group']:7} {c['sp_kind']:11} HP {hp:14} SP {sp:12} {line}")
        for continent in CONTINENT_ORDER:
            if by_continent.get(continent):
                print(f"     {continent:10} {', '.join(by_continent[continent])}")
    print(f"{len(data['classes'])} class lines, {len(data['races'])} races")
    return 0


if __name__ == '__main__':
    sys.exit(main())
