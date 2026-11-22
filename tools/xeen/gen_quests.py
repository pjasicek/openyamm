"""Quests, NPC topics, journal, autonotes, awards and map hooks of the Xeen world (A3).

A module of tools/xeen/build_world.py (see xeenlib.py). It reads
    assets_dev/worlds/xeen/source/quests/*.yml    one file per quest
    assets_dev/worlds/xeen/source/npcs/*.yml      A3's NPC topics that belong to no quest, street news, books
    assets_dev/worlds/xeen/source/npcs/flavour/*.yml   A4's flavour topics of NPCs with no quest role (same format;
                                                  blocks 170-198, no effects or hooks: QUESTS_FORMAT.md section 5)
and adds
    npc_topic.txt  npc_topic_text.txt  npc_news.txt  english/quests.txt  english/autonote.txt  english/awards.txt
    (every one written, header-only when empty: devdocs/xeen/lanes/TABLES.md)
    data_tables/quest_hooks.yml                   the hook table the map lanes wire by name
    events/common/xeen_quests.lua                 the topics as global events, the hooks as Lua
and publishes ctx.shared['npc_topics'] ({npc id: [topic id per slot]}) for gen_towns (npc.txt columns 10-15).

The format is devdocs/xeen/formats/QUESTS_FORMAT.md. tools/xeen/quests.py audits the same files through load_model().
A quest whose items are not in A2's rows yet is skipped whole, with a warning: never generated with a stand-in.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import xeenlib  # noqa: E402

QUESTS_DIR = xeenlib.SOURCE / 'quests'
NPCS_DIR = xeenlib.SOURCE / 'npcs'
FLAVOUR_DIR = NPCS_DIR / 'flavour'
FLAVOUR_BLOCKS = (170, 198)
TOWNS_DIR = xeenlib.SOURCE / 'towns'
TOPIC_BASE = 40000
BLOCK_SIZE = 50
BLOCK_COUNT = 200
SLOTS = 6
LUA_FILE = 'events/common/xeen_quests.lua'
HOOKS_FILE = 'data_tables/quest_hooks.yml'
KIND_ORDER = {'main': 0, 'side': 1, 'promotion': 2, 'ours': 3}
# A topic's label from its role (QUESTS_FORMAT section 4.4, MM6-MM8's merged tables): every topic that gives, tracks
# or hands in a quest reads "Quest" (MM6's and MM7's quest givers, MM8's Dadeross and Arion Hunter); one that only
# promotes reads "Promotion" (MM8's "Promotion to <class>": Xeen's promotions serve several class lines at once).
ROLE_LABELS = {'quest': 'Quest', 'promotion': 'Promotion'}
ACTS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'opt']
CONDITION_KEYS = {'qbit', 'item', 'items', 'found', 'award', 'gold', 'promotable', 'lua', 'not', 'all', 'any'}
# D-89 (DESIGN_GATING_AND_IDENTITY.md 1.5): the tags a condition inside a dungeon carries (`gate:`).
GATE_TAGS = {'beat', 'puzzle', 'order', 'faction', 'shortcut'}
EFFECT_KEYS = {'set', 'clear', 'give', 'take', 'xp', 'gold', 'pay', 'treasure', 'award', 'autonote', 'promote',
               'move_npc', 'stat', 'lua'}
# `{stat: personality, value: 5}`: every member's base statistic (event_support.lua's Base* variables).
STATS = {'might': 'BaseMight', 'intellect': 'BaseIntellect', 'personality': 'BasePersonality',
         'endurance': 'BaseEndurance', 'accuracy': 'BaseAccuracy', 'speed': 'BaseSpeed', 'luck': 'BaseLuck'}


class QuestError(xeenlib.BuildError):
    pass


# ---------------------------------------------------------------------------------------------------------------------
# Loading


def _load_dir(directory: Path) -> list[dict]:
    files = []
    if not directory.exists():
        return files
    for path in sorted(directory.glob('*.yml')):
        try:
            data = xeenlib.load_yaml(path) or {}
        except Exception as error:  # noqa: BLE001 - report any parse problem with its file
            raise QuestError(f'{path}: {error}') from error
        if not isinstance(data, dict):
            raise QuestError(f'{path}: not a mapping')
        data['_stem'] = path.stem
        data['_path'] = str(path.relative_to(xeenlib.ROOT))
        files.append(data)
    return files


def load_towns() -> dict[int, dict]:
    """A4's NPCs (source/towns/*.yml `npcs:`), by id."""
    npcs = {}
    if not TOWNS_DIR.exists():
        return npcs
    for path in sorted(TOWNS_DIR.glob('*.yml')):
        data = xeenlib.load_yaml(path) or {}
        for entry in data.get('npcs') or []:
            if isinstance(entry, dict) and isinstance(entry.get('id'), int):
                npcs[entry['id']] = dict(entry, _town=path.stem)
    return npcs


def blocks_of(data: dict) -> list[int]:
    if 'blocks' in data:
        return [int(value) for value in data['blocks']]
    if 'block' in data:
        return [int(data['block'])]
    raise QuestError(f"{data['_path']}: no block")


def topic_list(npc_entry) -> list[dict]:
    if not isinstance(npc_entry, dict):
        return []
    return [topic for topic in npc_entry.get('topics') or [] if isinstance(topic, dict)]


def topic_states(topic: dict) -> list[dict]:
    if 'states' in topic:
        return list(topic['states'] or [])
    if 'text' in topic:
        return [{'text': topic['text'], 'do': topic.get('do') or []}]
    return []


class Model:
    """Every quest and NPC file with its ids resolved (qbits, autonotes, awards, topics, texts, hooks)."""

    def __init__(self, quests: list[dict], npc_files: list[dict], towns: dict[int, dict]):
        self.quests = sorted(quests, key=lambda q: (KIND_ORDER.get(q.get('kind'), 9), _natural(q['_stem'])))
        self.npc_files = npc_files
        self.towns = towns
        self.by_stem = {q['_stem']: q for q in self.quests}
        self.qbits: dict[tuple[str, str], int] = {}
        self.autonotes: dict[tuple[str, str], int] = {}
        self.awards: dict[tuple[str, str], int] = {}
        self.hooks: dict[str, dict] = {}
        self.topics: list[dict] = []          # {id, label, npc, file, n, slot, show, states, repeatable}
        self.texts: list[tuple[int, str, str]] = []   # (text id, text, origin)
        self.problems: list[str] = []
        self._index()

    # -- indexing -----------------------------------------------------------------------------------------------------

    def _check_flavour(self, data: dict):
        """Flavour topics change nothing: a topic that sets, gives, pays or moves belongs in a quest file (A3)."""
        for key in ('hooks', 'qbits', 'items', 'autonotes', 'awards', 'books'):
            if data.get(key):
                self.problems.append(f"{data['_path']}: a flavour file has no `{key}:` (quest content is A3's)")
        for npc_id, entry in (data.get('npcs') or {}).items():
            for topic in topic_list(entry):
                for state in topic_states(topic):
                    if state.get('do'):
                        self.problems.append(f"{data['_path']}: npc {npc_id} {topic.get('label')!r} has effects "
                                             "(`do:`); flavour topics only talk, quest topics are A3's")

    def _index(self):
        used_blocks: dict[int, str] = {}
        for data in self.quests + self.npc_files:
            for block in blocks_of(data):
                if not 0 <= block < BLOCK_COUNT:
                    self.problems.append(f"{data['_path']}: block {block} outside 0-{BLOCK_COUNT - 1}")
                if block in used_blocks:
                    self.problems.append(f"{data['_path']}: block {block} is also {used_blocks[block]}'s")
                used_blocks[block] = data['_path']
                if data.get('_flavour') and not FLAVOUR_BLOCKS[0] <= block <= FLAVOUR_BLOCKS[1]:
                    self.problems.append(f"{data['_path']}: a flavour file's block must be "
                                         f"{FLAVOUR_BLOCKS[0]}-{FLAVOUR_BLOCKS[1]}, not {block}")
            if data.get('_flavour'):
                self._check_flavour(data)

        for quest in self.quests:
            if str(quest.get('id', '')).lower() != quest['_stem']:
                self.problems.append(f"{quest['_path']}: id {quest.get('id')!r} does not match the file name")
        for quest in self.quests + self.npc_files:
            stem = quest['_stem']
            for name, entry in (quest.get('qbits') or {}).items():
                self.qbits[(stem, name)] = int(entry['id'])
            for name, entry in (quest.get('autonotes') or {}).items():
                self.autonotes[(stem, name)] = int(entry['id'])
            for name, entry in (quest.get('awards') or {}).items():
                self.awards[(stem, name)] = int(entry['id'])
        # The journal's tasks: a qbit with a line opens one; a bit in a line's `until`, or clearing the line's own bit,
        # closes it. A topic that does either gives, tracks or hands in a quest (its role, ROLE_LABELS).
        self.journal_bits: set[tuple[str, str]] = set()
        self.closing_bits: set[tuple[str, str]] = set()
        for quest in self.quests + self.npc_files:
            stem = quest['_stem']
            for name, entry in (quest.get('qbits') or {}).items():
                if isinstance(entry, dict) and entry.get('journal'):
                    self.journal_bits.add((stem, name))
                    for ref in entry.get('until') or []:
                        self.closing_bits.add(self.qbit_key(stem, ref))

        for data in self.quests + self.npc_files:
            self._index_texts(data)

    def topic_role(self, stem: str, states: list[dict]) -> str | None:
        """The role a topic's effects give it: 'quest' when a state opens or closes a journal task, 'promotion' when it
        only promotes, else None (a named topic)."""
        promotes = False
        for state in states:
            for effect in state.get('do') or []:
                if not isinstance(effect, dict):
                    continue
                for key, closes_only in (('set', False), ('clear', True)):
                    refs = effect.get(key)
                    for ref in refs if isinstance(refs, list) else [refs] if refs is not None else []:
                        bit = self.qbit_key(stem, ref)
                        if bit in self.journal_bits or (not closes_only and bit in self.closing_bits):
                            return 'quest'
                if 'promote' in effect:
                    promotes = True
        return 'promotion' if promotes else None

    def _topic_label(self, data: dict, npc_id, topic: dict) -> str:
        """A topic's label: from its `role:` (MM6-MM8's convention, QUESTS_FORMAT section 4.4), else its `label:`; the
        role its effects give it must be the one it declares, unless it says why it keeps a name (`named:`)."""
        where = f"{data['_path']}: npc {npc_id} topic n {topic.get('n')}"
        role, label, named = topic.get('role'), topic.get('label'), topic.get('named')
        derived = self.topic_role(data['_stem'], topic_states(topic))
        if role is not None:
            if data.get('_flavour'):
                self.problems.append(f'{where}: a flavour topic has no role')
            if role not in ROLE_LABELS:
                self.problems.append(f"{where}: role {role!r} is not one of {', '.join(ROLE_LABELS)}")
                return str(label or '')
            if label is not None or named is not None:
                self.problems.append(f'{where}: a topic with `role: {role}` takes no `label:` or `named:` '
                                     f'(the generator writes {ROLE_LABELS[role]!r})')
            if derived != role and not (role == 'quest' and derived == 'promotion'):
                self.problems.append(f"{where}: `role: {role}` but its effects "
                                     + ('give it no role' if derived is None else f'make it a {derived} topic'))
            return ROLE_LABELS[role]
        if label is None or str(label) == '':
            self.problems.append(f'{where}: no `label:` and no `role:`')
            return ''
        if str(label) in ROLE_LABELS.values():
            self.problems.append(f'{where}: label {label!r} is written by `role:`, not by hand')
        if derived is not None and not named:
            self.problems.append(f"{where}: {label!r} {'gives, tracks or hands in a quest' if derived == 'quest' else 'promotes'}"
                                 f": `role: {derived}` (the label {ROLE_LABELS[derived]!r}), or `named: \"<why>\"` "
                                 "for a choice's answer")
        return str(label)

    def _index_texts(self, data: dict):
        blocks = blocks_of(data)
        counter = 0

        def text_id(origin: str) -> int:
            nonlocal counter
            if counter >= BLOCK_SIZE * len(blocks):
                self.problems.append(f"{data['_path']}: more than {BLOCK_SIZE * len(blocks)} texts; add a block")
            block = blocks[min(counter // BLOCK_SIZE, len(blocks) - 1)]
            value = TOPIC_BASE + BLOCK_SIZE * block + counter % BLOCK_SIZE
            counter += 1
            return value

        for npc_id, npc_entry in (data.get('npcs') or {}).items():
            for topic in topic_list(npc_entry):
                n = int(topic.get('n', 0))
                if not 1 <= n < BLOCK_SIZE:
                    self.problems.append(f"{data['_path']}: npc {npc_id} topic {topic.get('label')!r}: n {n} not 1-49")
                record = {
                    'id': TOPIC_BASE + BLOCK_SIZE * blocks[0] + n,
                    'label': self._topic_label(data, npc_id, topic),
                    'role': topic.get('role'),
                    'npc': int(npc_id),
                    'file': data,
                    'n': n,
                    'slot': topic.get('slot'),
                    'show': topic.get('show'),
                    'repeatable': bool(topic.get('repeatable')),
                    'states': [],
                }
                ask = topic.get('ask')
                if ask is not None:
                    # `ask: {text, declined}`: the topic asks first, with Yes and No buttons under its own text
                    # (merge point 28); Yes runs the states, No the declined line.
                    origin = f"{data['_stem']} npc {npc_id} {record['label']}"
                    if not isinstance(ask, dict) or not ask.get('text') or not ask.get('declined') \
                            or set(ask) - {'text', 'declined'}:
                        self.problems.append(f"{data['_path']}: npc {npc_id} topic {record['label']!r}: "
                                             f"ask takes text and declined only (Yes/No buttons)")
                    else:
                        record['ask'] = {}
                        for key in ('text', 'declined'):
                            record['ask'][key] = clean(ask[key])
                            record['ask'][f'{key}_id'] = text_id(f'{origin} ask {key}')
                            self.texts.append((record['ask'][f'{key}_id'], record['ask'][key], f'{origin} ask {key}'))
                for state in topic_states(topic):
                    origin = f"{data['_stem']} npc {npc_id} {record['label']}"
                    entry = dict(state)
                    entry['text_id'] = text_id(origin)
                    self.texts.append((entry['text_id'], clean(state.get('text', '')), origin))
                    record['states'].append(entry)
                if not record['states']:
                    self.problems.append(f"{data['_path']}: npc {npc_id} topic {record['label']!r} has no text")
                self.topics.extend(self._split_afterword(data, npc_id, topic, record))

        for name, hook in (data.get('hooks') or {}).items():
            full = f"{data['_stem']}.{name}"
            entry = dict(hook, _file=data, _name=name)
            for key in ('text', 'else_text', 'fail_text'):
                if hook.get(key):
                    entry[f'{key}_id'] = text_id(f'{full} {key}')
                    self.texts.append((entry[f'{key}_id'], clean(hook[key]), f'{full} {key}'))
            entry['states'] = []
            for index, state in enumerate(hook.get('states') or []):
                state = dict(state)
                state['text_id'] = text_id(f'{full} state {index}')
                self.texts.append((state['text_id'], clean(state.get('text', '')), f'{full} state {index}'))
                entry['states'].append(state)
            cinematic = hook.get('cinematic')
            if cinematic is not None:
                # `cinematic: {id, done, event}`: the hook plays the map's cinematic; its done event is a global event
                # 40000 + 50 * block + event (a topic number of this file's block that no topic takes) that runs the
                # file's hook `done` (QUESTS_FORMAT section 7).
                n = int(cinematic.get('event', 0)) if isinstance(cinematic, dict) else 0
                if not isinstance(cinematic, dict) or not cinematic.get('id') or not cinematic.get('done'):
                    self.problems.append(f"{data['_path']}: hook {full}: cinematic needs id, done and event")
                elif not 1 <= n < BLOCK_SIZE:
                    self.problems.append(f"{data['_path']}: hook {full}: cinematic event {n} not 1-49")
                elif cinematic['done'] not in (data.get('hooks') or {}):
                    self.problems.append(f"{data['_path']}: hook {full}: cinematic done hook "
                                         f"{cinematic['done']!r} is not a hook of this file")
                else:
                    entry['cinematic_event_id'] = TOPIC_BASE + BLOCK_SIZE * blocks[0] + n
                    entry['cinematic_done'] = f"{data['_stem']}.{cinematic['done']}"
            if full in self.hooks:
                self.problems.append(f"{data['_path']}: hook {full} twice")
            self.hooks[full] = entry

    def _split_afterword(self, data: dict, npc_id, topic: dict, record: dict) -> list[dict]:
        """A Quest topic goes when its quest is handed in (MM6-MM8 clear it); its leading `afterword: true` states (what
        the person says afterwards) become a topic of their own, `afterword: {n, label}`, shown instead."""
        where = f"{data['_path']}: npc {npc_id} topic {record['label']!r}"
        states = record['states']
        leading = 0
        while leading < len(states) and states[leading].get('afterword'):
            leading += 1
        if any(state.get('afterword') for state in states[leading:]):
            self.problems.append(f'{where}: `afterword: true` states come first')
        spec = topic.get('afterword')
        if record['role'] == 'quest' and not leading:
            # A Quest topic whose first state is the thanks after the hand-in would stay labelled Quest forever.
            first = states[0] if states else {}
            when = first.get('when') if isinstance(first.get('when'), dict) else {}
            bit = self.qbit_key(data['_stem'], when['qbit']) if set(when) == {'qbit'} else None
            if not first.get('do') and bit is not None and bit[1] in ('done', 'rewarded') \
                    and bit[0] == data['_stem'] and not topic.get('stays'):
                self.problems.append(f"{where}: its first state answers after the hand-in ({when['qbit']}): mark it "
                                     "`afterword: true` and give the topic `afterword: {n, label}`")
        if topic.get('stays') is not None and (leading or record['role'] != 'quest'):
            self.problems.append(f'{where}: `stays: <why>` is for a Quest topic with no afterword (its after-text '
                                 'tracks the next quest)')
        if not leading and spec is None:
            return [record]
        if not leading or not isinstance(spec, dict) or set(spec) != {'n', 'label'} or record['role'] != 'quest':
            self.problems.append(f'{where}: a Quest topic (`role: quest`) with `afterword: true` states needs '
                                 '`afterword: {n, label}`, and the other way round')
            return [record]
        if any('when' not in state or state.get('do') for state in states[:leading]) or leading == len(states):
            self.problems.append(f'{where}: an afterword state has a `when`, no effects, and is not the last state')
            return [record]
        n = int(spec['n'])
        if not 1 <= n < BLOCK_SIZE:
            self.problems.append(f'{where}: afterword n {n} not 1-49')
        after_when = {'any': [state['when'] for state in states[:leading]]} if leading > 1 else states[0]['when']
        own_show = record['show']
        after = dict(record, id=TOPIC_BASE + BLOCK_SIZE * blocks_of(data)[0] + n, label=str(spec['label']), role=None,
                     afterword_of=record['id'],
                     n=n, slot=None, states=states[:leading],
                     show=after_when if own_show is None else {'all': [own_show, after_when]})
        record = dict(record, states=states[leading:],
                      show={'not': after_when} if own_show is None else {'all': [own_show, {'not': after_when}]})
        return [record, after]

    # -- references -------------------------------------------------------------------------------------------------

    def resolve(self, table: dict, stem: str, ref: str, what: str, where: str) -> int | None:
        ref = str(ref)
        key = tuple(ref.split('.', 1)) if '.' in ref else (stem, ref)
        if key not in table:
            self.problems.append(f'{where}: unknown {what} {ref!r}')
            return None
        return table[key]

    def qbit(self, stem, ref, where):
        return self.resolve(self.qbits, stem, ref, 'qbit', where)

    def qbit_key(self, stem: str, ref: str) -> tuple[str, str]:
        ref = str(ref)
        return tuple(ref.split('.', 1)) if '.' in ref else (stem, ref)


def clean(text) -> str:
    """One line, single spaces after full stops (the source's double spaces removed)."""
    text = ' '.join(str(text).split())
    return text


def _natural(stem: str):
    parts = []
    number = ''
    for character in stem:
        if character.isdigit():
            number += character
        else:
            if number:
                parts.append(int(number))
                number = ''
            parts.append(character)
    if number:
        parts.append(int(number))
    return [(0, part) if isinstance(part, int) else (1, part) for part in parts]


def _load_flavour() -> list[dict]:
    """A4's flavour files (source/npcs/flavour/<map>.yml): stems `flavour_<map>`, so they never meet A3's files."""
    files = _load_dir(FLAVOUR_DIR)
    for data in files:
        data['_stem'] = f"flavour_{data['_stem']}"
        data['_flavour'] = True
    return files


def load_model() -> Model:
    return Model(_load_dir(QUESTS_DIR), _load_dir(NPCS_DIR) + _load_flavour(), load_towns())


# ---------------------------------------------------------------------------------------------------------------------
# Lua


def lua_str(text: str) -> str:
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


class Emitter:
    """Turns conditions and effects into Lua, collecting the item keys it could not resolve."""

    def __init__(self, model: Model, items: dict[str, int] | None):
        self.model = model
        self.items = items
        self.missing_items: set[str] = set()

    def item(self, key) -> int:
        key = str(key)
        if key.startswith('engine:'):
            return int(key.split(':', 1)[1])
        if self.items is not None and key in self.items:
            return int(self.items[key])
        self.missing_items.add(key)
        return 0

    def cond(self, condition, stem: str, where: str) -> str:
        if not isinstance(condition, dict) or len(condition) != 1:
            self.model.problems.append(f'{where}: a condition must be one key: {condition!r}')
            return 'false'
        (key, value), = condition.items()
        if key == 'qbit':
            return f'IsQBitSet(QBit({self.model.qbit(stem, value, where)}))'
        if key == 'item':
            return f'HasItem({self.item(value)})'
        if key == 'found':
            # D-90 5: the item was ever in the party's packs (the engine records every gain and saves the record), so a
            # chest opened and left full, or an item sold or handed over, reads right.
            return f'HasEverOwnedItem({self.item(value)})'
        if key == 'items':
            item, count = value
            return f'Xeen.itemCount({self.item(item)}) >= {int(count)}'
        if key == 'award':
            return f'HasAward(Award({self.model.resolve(self.model.awards, stem, value, "award", where)}))'
        if key == 'gold':
            return f'IsAtLeast(Gold, {int(value)})'
        if key == 'promotable':
            return f'Xeen.canPromote({lua_str(str(value))})'
        if key == 'lua':
            return f'({value})'
        if key == 'not':
            return f'not ({self.cond(value, stem, where)})'
        if key in ('all', 'any'):
            parts = [self.cond(part, stem, where) for part in value]
            joiner = ' and ' if key == 'all' else ' or '
            return '(' + joiner.join(parts) + ')' if parts else ('true' if key == 'all' else 'false')
        self.model.problems.append(f'{where}: unknown condition {key!r}')
        return 'false'

    def effects(self, effects, stem: str, where: str, indent: str) -> list[str]:
        lines = []
        for effect in effects or []:
            if not isinstance(effect, dict):
                self.model.problems.append(f'{where}: an effect must be a mapping: {effect!r}')
                continue
            key = next((name for name in effect if name in EFFECT_KEYS), None)
            if key is None:
                self.model.problems.append(f'{where}: unknown effect {effect!r}')
                continue
            value = effect[key]
            if key == 'set':
                lines.append(f'SetQBit(QBit({self.model.qbit(stem, value, where)}))')
            elif key == 'clear':
                lines.append(f'ClearQBit(QBit({self.model.qbit(stem, value, where)}))')
            elif key == 'give':
                item = self.item(value)
                lines.extend([f'AddValue(InventoryItem({item}), {item})'] * int(effect.get('count', 1)))
            elif key == 'take':
                lines.extend([f'RemoveItem({self.item(value)})'] * int(effect.get('count', 1)))
            elif key == 'xp':
                lines.extend(['evt.ForPlayer(Players.All)', f'AddValue(Experience, {int(value)})'])
            elif key == 'gold':
                lines.append(f'AddValue(Gold, {int(value)})')
            elif key == 'pay':
                lines.append(f'SubtractValue(Gold, {int(value)})')
            elif key == 'treasure':
                # Type 0 is any item (EventRuntime matchesRandomGiveItemType); event_support's ItemType has no Any.
                lines.append(f'evt.GiveItem({int(value)}, 0)')
            elif key == 'award':
                award = self.model.resolve(self.model.awards, stem, value, 'award', where)
                lines.extend(['evt.ForPlayer(Players.All)', f'SetAward(Award({award}))'])
            elif key == 'autonote':
                lines.append(f'SetAutonote({self.model.resolve(self.model.autonotes, stem, value, "autonote", where)})')
            elif key == 'promote':
                lines.append(f'Xeen.promote({lua_str(str(value))})')
            elif key == 'stat':
                if str(value).lower() not in STATS:
                    self.model.problems.append(f'{where}: unknown stat {value!r}')
                    continue
                lines.extend(['evt.ForPlayer(Players.All)', f"AddValue({STATS[str(value).lower()]}, {int(effect.get('value', 0))})"])
            elif key == 'move_npc':
                npc, house = value
                lines.append(f'evt.MoveNPC({int(npc)}, {int(house)})')
            elif key == 'lua':
                lines.append(str(value))
        return [indent + line for line in lines]


def quest_items(data: dict) -> set[str]:
    """Every item key a file's conditions and effects name (to skip a quest whose items do not exist yet)."""
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ('item', 'found', 'give', 'take') and isinstance(value, (str, int)):
                    found.add(str(value))
                elif key == 'items' and isinstance(value, list) and value:
                    found.add(str(value[0]))
                elif key in ('gives', 'takes', 'needs') and isinstance(value, list):
                    found.update(str(item) for item in value)
                elif key == 'map_gives' and isinstance(value, dict):
                    found.update(str(item) for item in value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk({key: value for key, value in data.items() if key in ('npcs', 'hooks')})
    return {item for item in found if not item.startswith('engine:')}


def sound_lua(emitter: Emitter, node: dict, stem: str, where: str, prefix: str = '') -> list[str]:
    """A voiced or sounded line (D-38): `sound: <name>` plays the sound by name with the text (`evt.PlaySoundName`);
    `sound_once: <qbit>` plays it only while that qbit is clear, and sets it. `prefix` 'fail_' reads `fail_sound`."""
    name = node.get(f'{prefix}sound')
    if not name:
        return []
    call = f'evt.PlaySoundName({lua_str(str(name))})'
    once = node.get(f'{prefix}sound_once')
    if not once:
        return [call]
    qbit = emitter.model.qbit(stem, once, where)
    return [f'if not IsQBitSet(QBit({qbit})) then SetQBit(QBit({qbit})) {call} end']


def topic_lua(emitter: Emitter, topic: dict) -> list[str]:
    stem = topic['file']['_stem']
    where = f"{topic['file']['_path']} npc {topic['npc']} {topic['label']!r}"
    ask = topic.get('ask')
    if ask is None:
        lines = [f"RegisterGlobalEvent({topic['id']}, {lua_str(topic['label'])}, function()"]
    else:
        # The Yes/No buttons continue this event: step 1 for Yes, 2 for No.
        lines = [f"RegisterGlobalEvent({topic['id']}, {lua_str(topic['label'])}, function(continueStep)",
                 '    if continueStep == nil then',
                 f"        AskChoiceWithAnswerSteps({topic['id']}, 2, NPCText({ask['text_id']}, "
                 f"{lua_str(ask['text'])}), {{{{Answer = \"Yes\", Step = 1}}, {{Answer = \"No\", Step = 2}}}})",
                 '        return',
                 '    end',
                 '    if continueStep ~= 1 then',
                 f"        evt.SetMessage(NPCText({ask['declined_id']}, {lua_str(ask['declined'])}))",
                 '        return',
                 '    end']
    states = topic['states']
    for index, state in enumerate(states):
        text = clean(state.get('text', ''))
        message = f"evt.SetMessage(NPCText({state['text_id']}, {lua_str(text)}))"
        body = sound_lua(emitter, state, stem, where) + [message] + [line.strip() for line in emitter.effects(state.get('do'), stem, where, '')]
        if 'when' in state:
            lines.append(f"    if {emitter.cond(state['when'], stem, where)} then")
            lines.extend('        ' + line for line in body)
            lines.append('        return')
            lines.append('    end')
        else:
            if index != len(states) - 1:
                emitter.model.problems.append(f'{where}: only the last state may have no `when`')
            lines.extend('    ' + line for line in body)
    lines.append('end)')
    if topic['show'] is not None:
        lines.append(f"RegisterCanShowTopic({topic['id']}, function()")
        lines.append(f"    return {emitter.cond(topic['show'], stem, where)}")
        lines.append('end)')
    return lines


def status_seconds(text: str) -> int | None:
    """How long a status line stays, as the studio's statusLine: a text over 30 characters 2 seconds and one more for
    each 15 characters, at most 6; a shorter one the game's default (None: not written)."""
    if len(text) <= 30:
        return None
    return max(2, min(6, 2 + len(text) // 15))


def is_find(hook: dict) -> bool:
    """D-90 1: a hook that hands over an item (`gives:`) or runs at a container holding one (`map_gives:`) is a find,
    and a find answers on the status line unless it says `window: "<why>"` (a note to read)."""
    return bool(hook.get('gives') or hook.get('map_gives')) and not hook.get('window')


def show_status(hook: dict) -> bool:
    return bool(hook.get('status')) or is_find(hook)


def show_lua(hook: dict, text_id: int, text: str) -> str:
    """A hook's line: a message window the player closes (evt.SimpleMessage), or with `status: true` a status line
    held by its length (F13, 2026-11-21: shrines, wells, fountains and the like answer on the status line; D-90:
    finds too, by default)."""
    call = f'NPCText({text_id}, {lua_str(text)})'
    if not show_status(hook):
        return f'evt.SimpleMessage({call})'
    seconds = status_seconds(text)
    return f'evt.StatusText({call}, {seconds})' if seconds else f'evt.StatusText({call})'


def hook_lua(emitter: Emitter, name: str, hook: dict) -> list[str]:
    stem = hook['_file']['_stem']
    where = f"{hook['_file']['_path']} hook {hook['_name']}"
    sets = [emitter.model.qbit(stem, ref, where) for ref in hook.get('sets') or []]
    lines = [f'XeenQuests.hooks[{lua_str(name)}] = {{']
    if hook.get('once'):
        if not sets:
            emitter.model.problems.append(f'{where}: a once hook needs a qbit it sets')
        else:
            lines.append(f'    once = {sets[0]},')
    requires = hook.get('requires')
    needs = [emitter.item(item) for item in hook.get('needs') or []]
    parts = [emitter.cond(requires, stem, where)] if requires is not None else []
    parts += [f'HasItem({item})' for item in needs]
    if parts:
        lines.append(f"    requires = function() return {' and '.join(parts)} end,")
    for key in ('else_text', 'fail_text'):
        if hook.get(f'{key}_id'):
            text = clean(hook[key])
            sound = ' '.join(sound_lua(emitter, hook, stem, where, key.replace('_text', '_')))
            sound = f'{sound} ' if sound else ''
            lines.append(f"    {key.replace('_text', 'Text')} = function() {sound}return NPCText({hook[key + '_id']}, "
                         f'{lua_str(text)}) end,')
    if hook.get('fail_status') or is_find(hook):
        # The fail line on the status line: the map leaves the map after a refusal (`leave`), and a message box
        # opened in the same event is dropped by the map change (q-c25.inner_door, D-57 Q2). A find's refusal too
        # (D-90 1: no window at a find spot; "Firewood, stacked..." before Ector asks).
        lines.append('    failStatus = true,')
    if hook.get('else_status') or is_find(hook):
        # The else line (a once hook already run) on the status line: a plain line, as the source's "Drain".
        lines.append('    elseStatus = true,')
    body = [f'SetQBit(QBit({qbit}))' for qbit in sets if qbit]
    body += [f'AddValue(InventoryItem({emitter.item(item)}), {emitter.item(item)})' for item in hook.get('gives') or []]
    body += [f'RemoveItem({emitter.item(item)})' for item in hook.get('takes') or []]
    body += [line.strip() for line in emitter.effects(hook.get('do'), stem, where, '')]
    body += sound_lua(emitter, hook, stem, where)
    if hook.get('text_id'):
        body.append(show_lua(hook, hook['text_id'], clean(hook['text'])))
    if hook.get('cinematic_event_id'):
        body.append(f"evt.PlayCinematic({lua_str(str(hook['cinematic']['id']))}, {hook['cinematic_event_id']})")
    lines.append('    run = function()')
    lines.extend('        ' + line for line in body)
    states = hook.get('states') or []
    for index, state in enumerate(states):
        state_body = [line.strip() for line in emitter.effects(state.get('do'), stem, where, '')]
        state_body += sound_lua(emitter, state, stem, where)
        state_body.append(show_lua(hook, state['text_id'], clean(state.get('text', ''))))
        if 'when' in state:
            lines.append(f"        if {emitter.cond(state['when'], stem, where)} then")
            lines.extend('            ' + line for line in state_body)
            lines.append('            return')
            lines.append('        end')
        else:
            if index != len(states) - 1:
                emitter.model.problems.append(f'{where}: only the last state may have no `when`')
            lines.extend('        ' + line for line in state_body)
    lines.append('    end,')
    lines.append('}')
    return lines


def hook_is_called(hook: dict) -> bool:
    return bool(hook.get('text') or hook.get('do') or hook.get('gives') or hook.get('takes') or hook.get('states')
                or hook.get('cinematic'))


def cinematic_done_lua(model, hooks: dict) -> list[str]:
    """The done event of each hook that plays a cinematic: a global event that runs the hook named as `done`."""
    lines = []
    topic_ids = {topic['id']: topic for topic in model.topics}
    for name, hook in sorted(hooks.items()):
        event = hook.get('cinematic_event_id')
        if not event:
            continue
        if event in topic_ids:
            model.problems.append(f"{hook['_file']['_path']} hook {hook['_name']}: cinematic event {event} is "
                                  f"also topic {topic_ids[event]['label']!r}'s")
            continue
        done = hook['cinematic_done']
        lines += ['', f'RegisterGlobalEvent({event}, {lua_str(done)}, function()',
                  f'    XeenQuests.hook({lua_str(done)})', 'end)']
    return lines


def hook_has_lua(hook: dict) -> bool:
    """Every hook gets a Lua function (and a `call` in the hook table), even one that does nothing at run time: a map
    may call any hook by name, and a door whose condition went (D-89: an opened dungeon, XD-18's inner door, XD-07's
    cellar) must still return true there, not "Unknown Xeen quest hook" and false."""
    return True


def teacher_gate_lua(model) -> list[str]:
    """A4's teacher offers that open by qbit (gen_towns.teacher_gates: engine teacher topic, qbit name, npc): each
    topic shows only once its qbit is set (the Grandmaster offers of Kalindra's stage 4)."""
    import gen_towns
    lines = []
    for topic_id, qbit_name, npc_id in gen_towns.teacher_gates():
        stem, _, name = str(qbit_name).partition('.')
        if (stem, name) not in model.qbits:
            model.problems.append(f'teacher gate of npc {npc_id} (topic {topic_id}): unknown qbit {qbit_name!r}')
            continue
        lines.append(f'RegisterCanShowTopic({int(topic_id)}, function() return Xeen.isSet({lua_str(qbit_name)}) end)'
                     f'  -- npc {npc_id}')
    return lines


def mirror_lua() -> list[str]:
    """Xeen.Mirrors from A4's town sources (houses of kind mirror and their arrivals; TOWNS_FORMAT.md), keyed by the
    mirror's house id, for xeen_common.lua's mirror helpers."""
    lines = ['Xeen = Xeen or {}', 'Xeen.Mirrors = {']
    if TOWNS_DIR.exists():
        for path in sorted(TOWNS_DIR.glob('*.yml')):
            town = xeenlib.load_yaml(path) or {}
            arrivals = town.get('arrivals') or {}
            for house in town.get('houses') or []:
                if not isinstance(house, dict) or house.get('kind') != 'mirror' or not house.get('mirror'):
                    continue
                mirror = house['mirror']
                if not mirror.get('qbit'):
                    continue
                # A planned town's arrival has no position yet (`at: null`): the mirror can be touched but is no
                # destination until the map lane fills it in. `opens`: the mirror works only once that qbit is set.
                arrival = arrivals.get(mirror.get('arrival')) or {}
                fields = [f"face = {lua_str(mirror['face'])}", f"town = {lua_str(mirror['town'])}",
                          f"qbit = {int(mirror['qbit'])}"]
                if arrival.get('at'):
                    x, y, z = arrival['at']
                    fields.append(f"arrival = {{{int(x)}, {int(y)}, {int(z)}, {int(arrival.get('direction', 0))}, "
                                  f"{lua_str(town['stem'])}}}")
                if house.get('opens'):
                    fields.append(f"opens = {lua_str(house['opens'])}")
                if house.get('closed_text'):
                    fields.append(f"closedText = {lua_str(clean(house['closed_text']))}")
                lines.append(f"    [{house['id']}] = {{{', '.join(fields)}}},")
    lines.append('}')
    return lines


# ---------------------------------------------------------------------------------------------------------------------
# Slots


def assign_slots(model: Model, topics: list[dict]) -> dict[int, list[int]]:
    by_npc: dict[int, list[dict]] = {}
    for topic in topics:
        by_npc.setdefault(topic['npc'], []).append(topic)
    slots_by_npc = {}
    for npc, npc_topics in sorted(by_npc.items()):
        slots = [0] * SLOTS
        pinned = [topic for topic in npc_topics if topic['slot'] is not None]
        free = [topic for topic in npc_topics if topic['slot'] is None]
        for topic in pinned:
            slot = int(topic['slot'])
            if not 0 <= slot < SLOTS or slots[slot]:
                model.problems.append(f"npc {npc}: topic {topic['label']!r} cannot take slot {slot}")
                continue
            slots[slot] = topic['id']
        for topic in free:
            if 0 not in slots:
                model.problems.append(f"npc {npc}: more than {SLOTS} topics ({topic['label']!r} has no slot)")
                break
            slots[slots.index(0)] = topic['id']
        while slots and slots[-1] == 0:
            slots.pop()
        slots_by_npc[npc] = slots
    return slots_by_npc


# ---------------------------------------------------------------------------------------------------------------------
# The module


def build(ctx: xeenlib.BuildContext):
    model = load_model()
    if not model.quests and not model.npc_files:
        ctx.warn('no quest or npc files')
        return
    items = ctx.shared.get('items')
    if items is None:
        ctx.warn('ctx.shared["items"] is missing (gen_items has not run): every quest that names an item is skipped')
        items = {}

    emitter = Emitter(model, items)
    skipped: set[str] = set()
    for data in model.quests:
        if data.get('status') == 'outline':
            skipped.add(data['_stem'])
    for data in model.quests + model.npc_files:
        missing = sorted(key for key in quest_items(data) if key not in items)
        if missing and data['_stem'] not in skipped:
            skipped.add(data['_stem'])
            ctx.warn(f"{data['_path']}: skipped, items not in A2's rows yet: {', '.join(missing)}")
    unknown_npcs = sorted({topic['npc'] for topic in model.topics if topic['npc'] not in model.towns})
    if unknown_npcs:
        ctx.warn(f"npc ids not in A4's town files: {', '.join(map(str, unknown_npcs))}")

    def live(data: dict) -> bool:
        return data['_stem'] not in skipped

    topics = [topic for topic in model.topics if live(topic['file'])]
    hooks = {name: hook for name, hook in model.hooks.items() if live(hook['_file'])}
    live_files = [data for data in model.quests + model.npc_files if live(data)]
    live_paths = {data['_path'] for data in live_files}
    sources = sorted(path.split('source/', 1)[-1] for path in live_paths)

    # Tables ------------------------------------------------------------------------------------------------------
    topic_table = ctx.table('npc_topic.txt', sources=sources, domain='npc_topics', engine='npc_topic.txt')
    text_table = ctx.table('npc_topic_text.txt', sources=sources, domain='npc_topics', engine='npc_topic_text.txt')
    quest_table = ctx.table('english/quests.txt', sources=sources, domain='qbits', engine='english/quests.txt')
    note_table = ctx.table('english/autonote.txt', sources=sources, domain='autonotes', engine='english/autonote.txt')
    award_table = ctx.table('english/awards.txt', sources=sources, domain='awards', engine='english/awards.txt')

    for topic in topics:
        npc = model.towns.get(topic['npc'], {})
        topic_table.add([topic['id'], topic['label'], 0, topic['file'].get('id', topic['file']['_stem']),
                         topic['ask']['text_id'] if topic.get('ask')
                         else topic['states'][0]['text_id'] if topic['states'] else 0,
                         npc.get('name', ''), topic['npc']],
                        origin=f"{topic['file']['_stem']} {topic['label']}")
    for text_id, text, origin in model.texts:
        if origin.split(' ', 1)[0].split('.', 1)[0] in skipped:
            continue
        text_table.add([text_id, xeenlib.quote_text(text), origin, 'Xeen'], origin=origin)

    for quest in model.quests:
        if not live(quest):
            continue
        stem = quest['_stem']
        for name, entry in (quest.get('qbits') or {}).items():
            journal = entry.get('journal')
            if not journal:
                continue
            until = [model.qbit(stem, ref, f"{quest['_path']} qbit {name}") for ref in entry.get('until') or []]
            # `journal_while`: the line shows while these qbits are set (default: its own), e.g. a target's line
            # that shows from the task's start and ends with the target's own bit (M37's Reflectors)
            required = [model.qbit(stem, ref, f"{quest['_path']} qbit {name} journal_while")
                        for ref in entry.get('journal_while') or []] or [entry['id']]
            quest_table.add([entry['id'], xeenlib.quote_text(clean(journal)), f"{quest['id']} {name}", 'Xeen',
                             ','.join(str(value) for value in required if value),
                             ','.join(str(value) for value in until if value), 'A3'],
                            origin=f'{stem}.{name}')
        for name, entry in (quest.get('autonotes') or {}).items():
            note_table.add([entry['id'], xeenlib.quote_text(clean(entry['text'])), entry.get('category', 'Misc'),
                            'Xeen'], origin=f'{stem}.{name}')
        for name, entry in (quest.get('awards') or {}).items():
            award_table.add([entry['id'], xeenlib.quote_text(clean(entry['text'])), entry.get('sort', 2),
                             f"{quest['id']} {name}"], origin=f'{stem}.{name}')

    news_table = ctx.table('npc_news.txt', sources=sources, domain='npc_topics', engine='npc_news.txt')
    for data in model.npc_files:
        if not live(data):
            continue
        for entry in data.get('news') or []:
            news_table.add([entry['id'], xeenlib.quote_text(clean(entry['text'])), entry.get('who', '')],
                           origin=f"{data['_stem']} news {entry['id']}")

    # Books: the readable text of A2's items whose text is A3's (source/npcs/books.yml) ---------------------------
    for data in model.npc_files:
        for key, book in (data.get('books') or {}).items():
            if key not in items:
                ctx.warn(f"{data['_path']}: book {key} skipped, the item is not in A2's rows yet")
                continue
            readables = ctx.table('readable_items.txt', sources=[data['_path'].split('source/', 1)[-1]],
                                  domain='items', contribution='readable_scrolls', engine='english/scroll.txt',
                                  header_rows=1)
            text = '\n'.join(clean(paragraph) for paragraph in book.get('paragraphs') or [book.get('text', '')])
            readables.add([items[key], xeenlib.quote_text(text), '', book.get('title', key)], origin=f'book {key}')

    # Entrance lines (D-90 4): source/entrances.yml -> english/trans.txt, the world's trans.txt rows (5001-5999) -----
    entrances_path = xeenlib.SOURCE / 'entrances.yml'
    if entrances_path.exists():
        lines = ['2D#\tTransition Description\tNote']
        seen = set()
        for row in (xeenlib.load_yaml(entrances_path) or {}).get('entrances') or []:
            number = int(row['id'])
            if not 5001 <= number <= 5999 or number in seen:
                raise QuestError(f'entrances.yml: id {number} twice or outside 5001-5999')
            seen.add(number)
            lines.append(f"{number}\t{xeenlib.quote_text(clean(row['text']))}\t{row.get('dungeon', '')}")
        ctx.text('data_tables/english/trans.txt', '\n'.join(lines) + '\n', sources=['entrances.yml'])

    # Lua ---------------------------------------------------------------------------------------------------------
    lua = ['-- Generated by tools/xeen/gen_quests.py from source/quests and source/npcs; do not edit.',
           '-- Helpers (Xeen.*, XeenQuests.hook) are in xeen_common.lua. Format: devdocs/xeen/formats/QUESTS_FORMAT.md',
           'XeenQuests = XeenQuests or {}', 'XeenQuests.hooks = XeenQuests.hooks or {}', 'XeenQuests.qbits = {']
    # An outline quest's qbits are named too: their numbers are fixed, and staged houses, mirrors and Xeen.Stages read
    # them by name before the quest's topics exist.
    outline = {data['_stem'] for data in model.quests if data.get('status') == 'outline'}
    for (stem, name), qbit in sorted(model.qbits.items(), key=lambda item: item[1]):
        if stem not in skipped or stem in outline:
            lua.append(f'    [{lua_str(stem + "." + name)}] = {qbit},')
    lua.append('}')
    lua.extend(mirror_lua())
    lua.extend(teacher_gate_lua(model))
    for topic in topics:
        lua.append('')
        lua.extend(topic_lua(emitter, topic))
    for name, hook in sorted(hooks.items()):
        if hook_has_lua(hook):
            lua.append('')
            lua.extend(hook_lua(emitter, name, hook))
    lua.extend(cinematic_done_lua(model, hooks))
    ctx.text(LUA_FILE, '\n'.join(lua) + '\n', sources=sources)

    # Hook table --------------------------------------------------------------------------------------------------
    table = {}
    for name, hook in sorted(hooks.items()):
        stem = hook['_file']['_stem']
        where = f"{hook['_file']['_path']} hook {hook['_name']}"
        entry = {'quest': hook['_file'].get('id'), 'map': hook.get('map'), 'where': hook.get('where', '')}
        if hook.get('question'):
            # the question the map asks before it calls the hook (or an exit preset's meaning); the map lane copies it
            entry['question'] = clean(hook['question'])
        for key in ('sets', 'reads'):
            entry[key] = {str(ref): model.qbit(stem, ref, where) for ref in hook.get(key) or []}
        for key in ('gives', 'needs', 'takes'):
            entry[key] = {str(item): emitter.item(item) for item in hook.get(key) or []}
        if hook.get('map_gives'):
            # Items the map's own chest or monster holds (the map lane places them; the hook does not give them).
            entry['map_gives'] = {str(item): {'id': emitter.item(item), 'count': int(count)}
                                  for item, count in hook['map_gives'].items()}
        if hook_has_lua(hook):
            entry['call'] = f'XeenQuests.hook("{name}")'
        for key in ('entrance', 'sealed', 'gate'):
            # D-89: a dungeon's outer door (`entrance`), why it stays sealed, the tag of a condition inside a dungeon
            if hook.get(key):
                entry[key] = hook[key]
        if hook.get('once'):
            entry['once'] = True
        if hook.get('cinematic_event_id'):
            # the map's cinematic (its cinematics.yml id) and the done event the hook passes to evt.PlayCinematic
            entry['cinematic'] = {'id': str(hook['cinematic']['id']), 'done_event': hook['cinematic_event_id'],
                                  'done_hook': hook['cinematic_done']}
        table[name] = entry
    ctx.text(HOOKS_FILE, xeenlib.dump_yaml(table), sources=sources)

    # NPC slots ---------------------------------------------------------------------------------------------------
    slots = assign_slots(model, topics)
    ctx.shared['npc_topics'] = slots
    if 'npc.txt' in ctx.tables:
        ctx.warn("npc.txt was built before gen_quests ran: its topic columns miss ctx.shared['npc_topics'] "
                 '(gen_quests must run before gen_towns)')

    if model.problems:
        raise QuestError(f'{len(model.problems)} problem(s) in the quest files:\n  ' + '\n  '.join(model.problems))
    if emitter.missing_items - {key for data in model.quests + model.npc_files if not live(data)
                                for key in quest_items(data)}:
        raise QuestError(f'unresolved items: {sorted(emitter.missing_items)}')
    ctx.shared['quest_skipped'] = sorted(skipped)


if __name__ == '__main__':
    print('gen_quests.py is a module of tools/xeen/build_world.py; run that (or tools/xeen/quests.py for the audit).')
