"""The stage's tech-skill schools (skills.yml): Hesper's house_data rows that sell the technology skills' Novice, the
teachers' NPC, greeting, topic and teacher_topics rows, the skill sheet descriptions, and the map-event overlay that
enters the houses. Called by stage.py after its NPC section (which rewrites npc.txt, npc_greet.txt and npc_topic.txt
from assets_dev each run).

Every table edited here is a stage copy under engine/data_tables. Tables the NPC section also writes get this block's
rows appended to the stage copy (any rows of the block from an earlier run are dropped first); the others are
rewritten from assets_dev each run.
"""
import shutil
from pathlib import Path

import yaml

MASTERY_RANK = {'Expert': 1, 'Master': 2, 'Grandmaster': 3}
BLOCK = range(9201, 9300)
# skills.yml's `engine_pending`: tech skills the design has but the engine does not know yet. The engine rejects the
# whole teacher_topics table over one unknown skill name, so their rows wait: houses do not offer them and their
# teachers' topics are plain text until the engine adds the skill (then drop it from the list).
PENDING = set()


def offered(skills):
    """A house's `teaches` as the house_data cell: the skills the engine knows (stage.py's houses use it too)."""
    return ','.join(skill for skill in skills if skill not in PENDING)


def check_cells(rows):
    for row in rows:
        assert all('\t' not in cell and '\n' not in cell and '"' not in cell for cell in row), row


def encode(rows):
    check_cells(rows)
    return ''.join('\t'.join(row) + '\r\n' for row in rows).encode('ascii')


def native_ids(path):
    ids = set()
    for line in path.read_bytes().split(b'\n'):
        head = line.split(b'\t', 1)[0].strip()
        if head.isdigit():
            ids.add(int(head))
    return ids


def append_from_assets_dev(dev, assets, relative, rows):
    """The assets_dev table with the rows appended, written to the stage copy."""
    native = (dev / 'engine/data_tables' / relative).read_bytes()
    assert not native_ids(dev / 'engine/data_tables' / relative) & {int(row[0]) for row in rows if row[0].isdigit()}
    if not native.endswith(b'\n'):
        native += b'\r\n'
    (assets / 'engine/data_tables' / relative).write_bytes(native + encode(rows))


def append_to_stage_copy(dev, assets, relative, rows):
    """The stage copy (already holding other stage rows) without this block's rows, then the rows appended."""
    assert not native_ids(dev / 'engine/data_tables' / relative) & set(BLOCK), relative
    path = assets / 'engine/data_tables' / relative
    kept = [line for line in path.read_bytes().split(b'\n')
            if not (line.split(b'\t', 1)[0].strip().isdigit() and int(line.split(b'\t', 1)[0]) in BLOCK)]
    data = b'\n'.join(kept)
    if not data.endswith(b'\n'):
        data += b'\r\n'
    taken = native_ids(path) - set(BLOCK)
    assert not taken & {int(row[0]) for row in rows}, relative
    path.write_bytes(data + encode(rows))


def install(project, dev, assets, world, map_ids, portrait_source):
    """map_ids: map file name -> the stage's map_stats id (maps.yml); portrait_source: the file installed for a
    portrait named by its approved x2 copy (stage.py --portrait-look)."""
    data = yaml.safe_load((project / 'skills.yml').read_text())
    PENDING.update(data.get('engine_pending', []))
    houses = {house['id']: house for house in data['houses']}
    # A teacher is a stage NPC of this block, or (`existing`) an NPC of npcs*.yml who gets a teacher topic of this
    # block (`topic`; npcs*.yml lists it in the NPC's topics).
    for key in list(houses) + [t.get('topic', t['npc']) for t in data['teachers']]:
        assert key in BLOCK, key
    gates = []                                          # (teacher topic, QBit): shown from the QBit

    # house_data: # # Type Map Picture Name Proprietor Title Picture State Rep Per Val A B C Notes Notes(2) Open
    # Closed Pic Map Restrictions EnterText OfferedSkills. "House" rows with offered skills teach them (Learn Skills);
    # a "Training" row also trains levels (MM's training hall: no level cap, `price` its Val multiplier).
    house_rows = []
    for house in data['houses']:
        teaches = offered(house.get('teaches', []))
        kind = house.get('type', 'House')
        assert kind in ('House', 'Training'), house
        house_rows.append([str(house['id']), '0', kind, str(map_ids.get(house['map'], 0)), str(house['picture']),
                           house['name'], '', '', '0', '0', '0', '0', str(house.get('price', 1)),
                           str(house.get('skill_price', 0)), '', '',
                           'Hesper (stage)', '', *[str(hour) for hour in house.get('hours', [0, 0])],
                           '0', '0', '0', '', teaches])
    append_from_assets_dev(dev, assets, 'house_data.txt', house_rows)

    npc_rows, greet_rows, topic_rows, text_rows, teacher_rows = [], [], [], [], []
    icons = world / 'icons_x2'
    icons.mkdir(exist_ok=True)
    for teacher in data['teachers']:
        key = str(teacher.get('topic', teacher['npc']))       # the teacher topic's id (and a stage NPC's own id)
        title = f"{teacher['mastery']} {' '.join(_display(teacher['skill']))}"
        if 'gate' in teacher:
            gates.append((int(key), teacher['gate']))
        if not teacher.get('existing'):
            # house: one of these houses, a house of npcs*.yml (the Chapel, Wren's post), or none (a street teacher, an
            # actor's NPC). npcs*.yml's houses are the packages' and the integrator's blocks (stage.py HOUSE_IDS).
            house = teacher.get('house', 0)
            assert house in houses or house == 0 or house in range(9300, 9500), teacher
            # The portrait as npc<id>.png in the world's icons; the row's picture is the NPC's own id (as npcs.yml's).
            shutil.copy2(portrait_source(teacher['portrait']), icons / f'npc{teacher["npc"]:04d}.png')
            # # Name Pic A B C 2D-location profession greet join topics A-F notes; the greeting shares the NPC's id.
            # topics: the teacher topic first, then any of npcs*.yml's topics (their Lua is there).
            extra = [str(topic) for topic in teacher.get('topics', [])]
            assert len(extra) <= 5, teacher
            npc_rows.append([key, teacher['name'], key, '0', '0', '0', str(house), '0',
                             key, '0', key] + extra + ['0'] * (5 - len(extra)) + [f'{title} (Hesper stage)'])
            greet_rows.append([key, teacher['greeting'][0], teacher['greeting'][1], '', 'Hesper'])
        topic_rows.append([key, title, '0', '', key, 'Hesper', ''])
        text_rows.append([key, teacher['text'], title, 'Hesper'])
        if teacher['skill'] in PENDING:
            continue                                    # a plain topic (its text) until the engine has the skill
        # TopicId Notes SkillId Mastery TextId Req.Gold Req.Skill: the skill by name (technology skills, ids 40+).
        teacher_rows.append([key, title, teacher['skill'], str(MASTERY_RANK[teacher['mastery']]), key,
                             str(teacher['gold']), ''])
    append_to_stage_copy(dev, assets, 'npc.txt', npc_rows)
    append_to_stage_copy(dev, assets, 'npc_greet.txt', greet_rows)
    append_to_stage_copy(dev, assets, 'npc_topic.txt', topic_rows)
    append_from_assets_dev(dev, assets, 'npc_topic_text.txt', text_rows)
    append_from_assets_dev(dev, assets, 'teacher_topics.txt', teacher_rows)

    skill_rows = [[skill['name'], skill['description'], skill['novice'], skill['expert'], skill['master'],
                   skill['grandmaster']] for skill in data['skills']]
    native = (dev / 'engine/data_tables/english/skill_des.txt').read_bytes()
    assert not any(line.split(b'\t', 1)[0] == row[0].encode() for line in native.split(b'\n') for row in skill_rows)
    if not native.endswith(b'\n'):
        native += b'\r\n'
    (assets / 'engine/data_tables/english/skill_des.txt').write_bytes(native + encode(skill_rows))

    # The gated teacher topics (the Grandmaster teachers: Iver from two shards, Dace from M12), appended to the world's
    # global overlay that stage.py's NPC section wrote.
    if gates:
        overlay = world / 'events/Global_hesper.lua'
        overlay.write_text(overlay.read_text() + ''.join(
            f'RegisterCanShowTopic({npc}, function() return IsQBitSet(QBit({qbit})) end)\n' for npc, qbit in gates))

    # The map events that enter the houses, appended to the installed map scripts (a later RegisterEvent of an id
    # replaces the earlier handler).
    wired = []
    for map_name, events in data['events'].items():
        script = world / 'events/maps' / (Path(map_name).stem + '.lua')
        if not script.exists():
            continue
        lines = ['', '-- Appended by level_generation/projects/hesper_stage/skills_stage.py (skills.yml): the tech-skill '
                 'houses.']
        for event_id, house_id in sorted(events.items()):
            name = houses[house_id]['name']
            lines.append(f'RegisterEvent({event_id}, "{name}", function() evt.EnterHouse({house_id}) end, "{name}")')
            wired.append(f'{map_name}:{event_id}')
        script.write_text(script.read_text().rstrip('\n') + '\n' + '\n'.join(lines) + '\n')
    print('tech skills: houses ' + ', '.join(str(h) for h in houses) + '; events ' + ', '.join(wired))
    return {'houses': sorted(houses), 'teachers': [t['npc'] for t in data['teachers']], 'events': wired}


def _display(skill):
    names = {'EnergyGuns': ['Energy', 'Guns'], 'EnergyBlades': ['Energy', 'Blades'], 'ShieldTech': ['Shield', 'Tech'],
             'Hacking': ['Hacking'], 'Cybernetics': ['Cybernetics']}
    return names[skill]
