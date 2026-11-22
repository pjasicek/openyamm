#!/usr/bin/env python3
"""The Xeen quest audit (A3; devdocs/xeen/formats/QUESTS_FORMAT.md section 9).

    python3 tools/xeen/quests.py            the report; exit 1 when it finds an error
    python3 tools/xeen/quests.py --open     also list every open item (hooks not wired, qbits of later acts)

Reads the quest and NPC files (source/quests, source/npcs) through gen_quests.load_model(), A2's items.yml, A4's
town files, the orchestrator's maps.yml, the built maps' projects (devdocs/xeen/briefs/*/L4/: their `qbits:` tables
and every `qbit:` their events test or set) and xeen_common.lua's qbit names. Writes nothing.

Errors: a qbit number twice or out of range, a reference that does not resolve, a built map's qbit no quest file
registers, a qbit nobody writes, an item taken or needed that nothing gives, a riddle without an answer-giver, more
than six topics on an NPC, an NPC id A4 does not have, a hook on a map maps.yml does not know, a main quest that comes
after a later one, an act over its experience budget by more than 15 %, a touch effect (a hook or map event that gives
a party effect: a shrine, well, fountain, statue, brew) shown in a message window instead of on the status line (F13).
Open (listed with --open): hooks on built maps whose project does not name the hook's qbits yet, qbits of quests not
written yet (xeen_common.lua, `until_later`), outline quests, qbits marked `pending:` (a place not built yet).
A4's town files count as writers and readers too: mirror houses (Xeen.useMirror), Town Portal pages, the inn roster.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_quests  # noqa: E402
import xeenlib  # noqa: E402
import yaml  # noqa: E402

BRIEFS = xeenlib.ROOT / 'devdocs' / 'xeen' / 'briefs'
COMMON_LUA = xeenlib.WORLD / 'events' / 'common' / 'xeen_common.lua'
# MAPS 0 and QUESTS rules: quest experience per member per act, and the per-quest cap factor (x 1,000 x level).
ACT_BUDGET = {'I': 16500, 'II': 83000, 'III': 132000, 'IV': 160000, 'V': 209000, 'VI': 210000, 'opt': 70000}
CAP_FACTOR = {'I': 1.5, 'II': 1.5, 'III': 1.0, 'IV': 1.0, 'V': 0.75, 'VI': 0.75, 'opt': 0.75}
QBIT_RANGE = (110000, 119999)
MAIN_ORDER_KEY = re.compile(r'^m(\d+)$')
# F13 (2026-11-21): map events that give a party effect with their own message window, open for their map lanes
# (USER_FEEDBACK_20261121.md, F13 results). Remove a row when its map is rebuilt with the status line.
F13_MAP_SITES_OPEN = {
    ('xeen_xd07', 'evt:well'),
    ('xeen_xd08', 'evt:juice_blue'),
    ('xeen_xd08', 'evt:juice_green'),
    ('xeen_xd08', 'evt:juice_orange'),
    ('xeen_xd08', 'evt:juice_purple'),
    ('xeen_xd08', 'evt:juice_red'),
    ('xeen_xd08', 'evt:juice_white'),
    ('xeen_xd08', 'evt:juice_yellow'),
    # D-90 2 (2026-11-22): experience counts as a party effect; camps burnt with a window (A5 X4, A6 X5)
    ('xeen_x5', 'evt:thing:camp_tent2'),
    ('xeen_x5', 'evt:thing:ogre_tent'),
    ('xeen_x5', 'evt:thing:archer_tent'),
}

# D-89 (DESIGN_GATING_AND_IDENTITY.md 1.2, 1.5; adopted 2026-11-22): the outer doors that stay sealed, each because it
# is the story itself, with the reason. A hook at a dungeon's outer door (`entrance:`) may carry requires/needs only
# when it is listed here and says `sealed: "<reason>"` and a `fail_text` that names where the way in comes from. A new
# seal needs a decider (DECISIONS.md); add it here only with the decision's id.
SEALED = {
    'm2.warehouse_door': 'XD-01: Joe\'s locked warehouse; the key is in the rain barrel by the door, a click puts it on the cursor (D-93)',
    'm5.crusaders_gate': 'XD-07: the Act I to II beat, the Crusader title (the source\'s line)',
    'm13.darzog_door': 'XD-12: the Act IV hinge; the Skeleton Key is loot in XD-11',
    'q-c7.coffin': 'XD-24: the sundial puzzle at the door, answered on the square',
    'm34.gate': 'XD-19: the cupie doll from Slick\'s stand (the source\'s joke)',
    'x9.castle_gone': 'XD-19: the castle is gone after the finale',
    'm39.depths_door': 'FD-01: a finale seal (the Cube of Power)',
    'm40.sphinx_door': 'FD-02: a finale seal (Roland\'s amulet)',
    'm41.tower_door': 'FD-03: a finale seal (the Darkstone key)',
    'q-f1.tower_door': 'FD-04: optional endgame; the key lies under Castle Alamar (FD-01)',
    'm14.gate': 'Castleview (DD-02 inside): M14\'s arrival beat, two routes',
    'm19.ghost_castle': 'DD-03: the out-of-phase castle is the story',
    'q-d6.front_door_outside': 'DD-05: the key is inside at the top; the rope on the north wall is open',
    'm25.gate_flight': 'DD-14: the griffin flight is M25\'s beat',
    'm29.pod_door': 'DD-16: a main-story set piece (the lava the Pharaoh cools)',
    'm33.arrival': 'DD-17: the finale (Corak\'s Soul Box)',
    'm33.arrival_gate': 'DD-17: the finale (Corak\'s Soul Box), m33.arrival\'s seal checked at D6\'s gate (F16)',
    'm33.roof_arrival': 'DD-17: the finale (Corak\'s Soul Box), from D7\'s roof',
    'd6.necropolis_gate': 'Necropolis (DD-21 inside): the pass is loot in the Lakeside Coven (DD-20)',
    'd6.sheltem_hatch': 'DD-22: sealed from inside until its master falls (Act VI)',
    'q-d26.hatch': 'DD-17 and FD-01 from D7\'s roof: the Megadragon\'s key, Act VI',
    'd7.pyramid_door': 'DD-15 from D7: the sky is Act VI\'s map, sealed by the story',
}
# Map events that move into a dungeon while testing a qbit directly (not through a hook), allowed with their reason. A
# bit set by the dungeon itself (a shortcut opened from inside) or by the hook the same event calls needs no row.
SEALED_MAP_EVENTS = {
    ('xeen_x3', 'evt:thing:xd13_stair'): 'XD-13: the party\'s own castle, staged (the deed, m8.deed); the board points',
    ('xeen_x9', 'evt:gate_l'): 'XD-19: the castle is gone after the finale (m35.done)',
    ('xeen_x9', 'evt:gate_r'): 'XD-19: the castle is gone after the finale (m35.done)',
    ('xeen_d7', 'evt:hatch_dd17'): 'DD-17/FD-01: the destination after m33.done; the hatch is q-d26.hatch',
    ('xeen_d4', 'evt:thing:guild_back_stair'): 'DD-20: the back stair after the front door\'s riddle; the sewer shaft is open',
}
# D-89 sites waiting for their map lanes (REQUESTS of A3 session 34): remove a row when its map is rebuilt.
D89_MAP_SITES_OPEN = {
}
# Sealed outer-door hooks that show no refusal line of their own (the check wants one from every other seal).
SEALED_NO_LINE = {
    'm25.gate_flight': 'the gatehouse shows m25.blackfang_gate\'s line first; this hook is the flight itself',
    'x9.castle_gone': 'not a refusal: the castle-gone stage\'s line after the finale',
}
DUNGEON_KEY = re.compile(r'^(XD|DD|FD)-')


class Audit:
    def __init__(self):
        self.model = gen_quests.load_model()
        self.errors: list[str] = list(self.model.problems)
        self.open: list[str] = []
        self.info: list[str] = []
        self.writers: dict[int, list[str]] = {}
        self.readers: dict[int, list[str]] = {}
        self.items_given: dict[str, list[str]] = {}
        self.items_used: dict[str, list[str]] = {}
        self.maps = {entry.get('key') for entry in (xeenlib.load_yaml(xeenlib.SOURCE / 'maps.yml') or {}).get('maps', [])}
        self.items = self._items()
        self.briefs = self._briefs()
        self.player_bit_maps: dict[int, str] = {}   # registered player bit -> its map (check_numbers)

    # -- sources -----------------------------------------------------------------------------------------------------

    def _items(self) -> set[str]:
        path = xeenlib.SOURCE / 'items.yml'
        keys = set()
        if not path.exists():
            return keys

        def walk(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if isinstance(value, dict) and 'id' in value:
                        keys.add(str(key))
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(xeenlib.load_yaml(path))
        return keys

    def _briefs(self) -> dict[str, dict]:
        """Built maps: map key -> {qbits: name -> number, sets: {numbers}, reads: {numbers}}."""
        briefs = {}
        for project_path in sorted(BRIEFS.glob('*/L4/project.yml')):
            project = xeenlib.load_yaml(project_path) or {}
            key = project.get('map_code') or project_path.parts[-3].upper()
            key = self._map_key(str(key), project_path.parts[-3])
            names = {str(name): int(value) for name, value in (project.get('qbits') or {}).items()}
            sets, reads, hooks, player_bits = set(), set(), set(), set()
            for file in project_path.parent.glob('*.yml'):
                if file.name.startswith('playtest') or file.name == 'ids.lock.yml':
                    continue
                self._scan_qbits(xeenlib.load_yaml(file), names, sets, reads, False)
                # Hooks the map calls by name: `XeenQuests.hook("m2.rain_barrel")` in a lua effect, or `hook: <name>`.
                text = file.read_text(encoding='utf-8')
                hooks.update(re.findall(r'XeenQuests\.(?:hook|can)\(\\?"([^"\\]+)\\?"\)', text))
                hooks.update(re.findall(r'\bhook:\s*"?([a-z0-9-]+\.[a-z0-9_]+)', text))
                # Per-character bits: the studio's `player_bit: n` word, or Lua's PlayerBit(n).
                player_bits.update(int(n) for n in re.findall(r'\bplayer_bit:\s*(\d+)|PlayerBit\((\d+)\)', text)
                                   for n in n if n)
            briefs[key] = {'qbits': names, 'sets': sets, 'reads': reads, 'hooks': hooks, 'player_bits': player_bits,
                           'path': project_path.parent}
        return briefs

    def _map_key(self, code: str, folder: str) -> str:
        if code in self.maps:
            return code
        match = re.match(r'^(x|d)d(\d+)$', folder)
        if match:
            return f'{match.group(1).upper()}D-{int(match.group(2)):02d}'
        return folder.upper()

    def _scan_qbits(self, node, names, sets, reads, writing):
        """Every `qbit:` in a project file: under effects/sets a write, under conditions a read; Lua strings too."""
        if isinstance(node, dict):
            for key, value in node.items():
                if key == 'qbit' and isinstance(value, (str, int)):
                    number = names.get(str(value)) if isinstance(value, str) else int(value)
                    if number:
                        (sets if writing else reads).add(number)
                elif key in ('sets', 'effects', 'else_effects', 'give'):
                    self._scan_qbits(value, names, sets, reads, True)
                elif key in ('condition', 'requires', 'when'):
                    self._scan_qbits(value, names, sets, reads, False)
                else:
                    self._scan_qbits(value, names, sets, reads, writing)
        elif isinstance(node, list):
            for value in node:
                self._scan_qbits(value, names, sets, reads, writing)
        elif isinstance(node, str):
            for number in re.findall(r'SetQBit\(QBit\((\d+)\)\)', node):
                sets.add(int(number))
            for number in re.findall(r'IsQBitSet\(QBit\((\d+)\)\)', node):
                reads.add(int(number))

    # -- walking the quest files ----------------------------------------------------------------------------------

    def _note(self, table, key, where):
        table.setdefault(key, []).append(where)

    def _conditions(self, condition, stem, where):
        if not isinstance(condition, dict):
            return
        for key, value in condition.items():
            if key == 'qbit':
                number = self.model.qbit(stem, value, where)
                if number:
                    self._note(self.readers, number, where)
            elif key in ('item', 'found'):
                self._note(self.items_used, str(value), where)
            elif key == 'items':
                self._note(self.items_used, str(value[0]), where)
            elif key == 'not':
                self._conditions(value, stem, where)
            elif key in ('all', 'any'):
                for part in value:
                    self._conditions(part, stem, where)

    def _effects(self, effects, stem, where, xp_sink):
        for effect in effects or []:
            if not isinstance(effect, dict):
                continue
            for key, value in effect.items():
                if key == 'set':
                    number = self.model.qbit(stem, value, where)
                    if number:
                        self._note(self.writers, number, where)
                elif key == 'clear':
                    self.model.qbit(stem, value, where)
                elif key == 'give':
                    self._note(self.items_given, str(value), where)
                elif key == 'take':
                    self._note(self.items_used, str(value), where)
                elif key == 'xp':
                    xp_sink.append(int(value))

    def _sound_once(self, node, stem, where, prefix=''):
        """`sound_once: <qbit>` (a voiced line played once, D-38): the generated Lua reads and sets the qbit."""
        ref = node.get(f'{prefix}sound_once')
        if ref:
            number = self.model.qbit(stem, ref, where)
            if number:
                self._note(self.writers, number, f'{where} {prefix}sound_once')
                self._note(self.readers, number, f'{where} {prefix}sound_once')

    def walk(self):
        self.xp: dict[str, int] = {}
        for data in self.model.quests + self.model.npc_files:
            stem = data['_stem']
            xp: list[int] = []
            for npc_id, entry in (data.get('npcs') or {}).items():
                for topic in gen_quests.topic_list(entry):
                    where = f"{stem} npc {npc_id} {topic.get('label') or topic.get('role')!r} (n {topic.get('n')})"
                    self._conditions(topic.get('show'), stem, where)
                    for state in gen_quests.topic_states(topic):
                        self._conditions(state.get('when'), stem, where)
                        uncounted = topic.get('repeatable') or state.get('repeatable') or state.get('alternative')
                        sink = [] if uncounted else xp
                        self._effects(state.get('do'), stem, where, sink)
                        self._sound_once(state, stem, where)
            for name, hook in (data.get('hooks') or {}).items():
                where = f'{stem}.{name}'
                for ref in hook.get('sets') or []:
                    number = self.model.qbit(stem, ref, where)
                    if number:
                        self._note(self.writers, number, where)
                if hook.get('once') and hook.get('sets'):
                    # a once hook tests its first bit before it runs (XeenQuests.hook)
                    number = self.model.qbit(stem, hook['sets'][0], where)
                    if number:
                        self._note(self.readers, number, f'{where} once')
                for ref in hook.get('reads') or []:
                    number = self.model.qbit(stem, ref, where)
                    if number:
                        self._note(self.readers, number, where)
                for item in hook.get('gives') or []:
                    self._note(self.items_given, str(item), where)
                for item in hook.get('map_gives') or {}:
                    self._note(self.items_given, str(item), f'{where} (the map places it)')
                for item in (hook.get('needs') or []) + (hook.get('takes') or []):
                    self._note(self.items_used, str(item), where)
                self._conditions(hook.get('requires'), stem, where)
                # `alternative: true`: the other route's pay (a party takes one), left out of the act's budget
                self._effects(hook.get('do'), stem, where, [] if hook.get('alternative') else xp)
                for state in hook.get('states') or []:
                    self._conditions(state.get('when'), stem, where)
                    alternative = hook.get('alternative') or state.get('alternative')
                    self._effects(state.get('do'), stem, where, [] if alternative else xp)
                    self._sound_once(state, stem, where)
                for prefix in ('', 'fail_', 'else_'):
                    self._sound_once(hook, stem, where, prefix)
                if hook.get('map') not in self.maps:
                    self.errors.append(f"hook {where}: map {hook.get('map')!r} is not in maps.yml")
            for name, entry in (data.get('qbits') or {}).items():
                where = f'{stem}.{name}'
                if entry.get('journal'):
                    self._note(self.readers, int(entry['id']), f'{where} journal')
                    # a Current Quests line ends when its step is done (A3 s38); a standing line says why it stays
                    if not entry.get('until') and not entry.get('journal_stays'):
                        self.errors.append(f'{where}: journal line with no `until` (it would never leave Current '
                                           'Quests; give its ending bits, or `journal_stays: <why>`)')
                for key in ('until', 'journal_while'):
                    for ref in entry.get(key) or []:
                        number = self.model.qbit(stem, ref, f'{where} {key}')
                        if number:
                            self._note(self.readers, number, f'{where} {key}')
                for ref in entry.get('until_later') or []:
                    key = self.model.qbit_key(stem, ref)
                    if key not in self.model.qbits:
                        self.open.append(f'{where}: until_later {ref} (its quest is not written yet)')
            for ref in data.get('after') or []:
                number = self.model.qbit(stem, ref, f'{stem} after')
                if number:
                    self._note(self.readers, number, f'{stem} after')
            self.xp[stem] = sum(xp)

    # -- checks ------------------------------------------------------------------------------------------------------

    def check_numbers(self):
        seen: dict[int, str] = {}
        for (stem, name), number in sorted(self.model.qbits.items()):
            if not QBIT_RANGE[0] <= number <= QBIT_RANGE[1]:
                self.errors.append(f'{stem}.{name}: qbit {number} outside {QBIT_RANGE}')
            if number in seen:
                self.errors.append(f'{stem}.{name}: qbit {number} is also {seen[number]}')
            seen[number] = f'{stem}.{name}'
        player_bits: dict[int, str] = {}
        for data in self.model.quests + self.model.npc_files:
            for name, entry in (data.get('player_bits') or {}).items():
                number = int(entry['id'])
                if number in player_bits:
                    self.errors.append(f"{data['_stem']}.{name}: player bit {number} is also {player_bits[number]}")
                player_bits[number] = f"{data['_stem']}.{name}"
                self.player_bit_maps[number] = str(entry.get('map') or '')
        for label, table, low, high in (('autonote', self.model.autonotes, 4001, 4999),
                                        ('award', self.model.awards, 401, 499)):
            used: dict[int, str] = {}
            for (stem, name), number in table.items():
                if not low <= number <= high:
                    self.errors.append(f'{stem}.{name}: {label} {number} outside {low}-{high}')
                if number in used:
                    self.errors.append(f'{stem}.{name}: {label} {number} is also {used[number]}')
                used[number] = f'{stem}.{name}'

    def check_built_maps(self):
        registered = {number for number in self.model.qbits.values()}
        for key, brief in sorted(self.briefs.items()):
            if key not in self.maps:
                # A generator that drops `map_code` (DD-11A/B/C lost it to a comment, 2026-11-22) keys the map by its
                # folder, and every per-map check below then compares against the wrong name.
                self.errors.append(f"{key}: {brief['path']}/project.yml has no map_code that maps.yml knows")
            for name, number in sorted(brief['qbits'].items()):
                if number not in registered:
                    self.errors.append(f'{key}: built qbit {name} ({number}) is in no quest file')
            for number in brief['sets']:
                self._note(self.writers, number, f'{key} map event')
            for number in brief['reads']:
                self._note(self.readers, number, f'{key} map condition')
            for number in sorted(brief['player_bits']):
                owner = self.player_bit_maps.get(number)
                if owner is None:
                    self.errors.append(f'{key}: built player bit {number} is in no quest file (`player_bits:`)')
                elif owner != key:
                    self.errors.append(f'{key}: built player bit {number} is registered for {owner}')

    def check_towns(self):
        """A4's world systems: a town's mirror event sets its mirror's qbit (Xeen.useMirror), which Town Portal and
        Xeen.mirrorDestinations read; the Adventurer's Inn roster rows read their qbit."""
        for path in sorted(gen_quests.TOWNS_DIR.glob('*.yml')):
            town = xeenlib.load_yaml(path) or {}
            for house in town.get('houses') or []:
                mirror = house.get('mirror') if isinstance(house, dict) else None
                if isinstance(mirror, dict) and mirror.get('qbit'):
                    where = f"towns/{path.name} mirror {house.get('id')}"
                    self._note(self.writers, int(mirror['qbit']), f'{where} (Xeen.useMirror)')
                    self._note(self.readers, int(mirror['qbit']), f'{where} (Xeen.mirrorDestinations)')
                for field in ('opens', 'after'):
                    ref = house.get(field) if isinstance(house, dict) else None
                    if not ref or '.' not in str(ref):
                        continue
                    key = self.model.qbit_key('', str(ref))
                    where = f"towns/{path.name} house {house.get('id')} {field}"
                    if key in self.model.qbits:
                        self._note(self.readers, self.model.qbits[key], where)
                    elif key[0] in self.model.by_stem:
                        self.errors.append(f'{where}: {ref} is no qbit')
                    else:
                        self.open.append(f'{where}: {ref} (its quest is not written yet)')
            for page in town.get('pages') or []:
                for destination in page.get('destinations') or []:
                    if destination.get('qbit'):
                        self._note(self.readers, int(destination['qbit']), f"towns/{path.name} Town Portal")
            for row in town.get('roster') or []:
                if row.get('qbit'):
                    self._note(self.readers, int(row['qbit']), f"towns/{path.name} roster {row.get('id')}")

    def note_common_lua_writers(self):
        """A function of xeen_common.lua that names a qbit (Xeen.qbit("m33.sundial_nine")) and calls SetQBit writes it."""
        if not COMMON_LUA.exists():
            return
        text = COMMON_LUA.read_text(encoding='utf-8')
        for body in re.split(r'\nfunction ', text)[1:]:
            name = body.split('(', 1)[0]
            if 'SetQBit' not in body:
                continue
            for ref in set(re.findall(r'Xeen\.qbit\("([a-z0-9_.-]+)"\)', body)):
                number = self.model.qbits.get(self.model.qbit_key('', ref))
                if number is not None:
                    self._note(self.writers, number, f'xeen_common.lua {name}')

    def check_writers_readers(self):
        for (stem, name), number in sorted(self.model.qbits.items(), key=lambda item: item[1]):
            quest = self.model.by_stem.get(stem) or next(
                (npc for npc in self.model.npc_files if npc.get('_stem') == stem), {})
            entry = (quest.get('qbits') or {}).get(name) or {}
            outline = quest.get('status') == 'outline' or bool(entry.get('pending'))
            label = f'{stem}.{name} ({number})'
            if number not in self.writers:
                (self.open if outline else self.errors).append(f'{label}: nothing sets it')
            if number not in self.readers:
                (self.open if outline else self.info).append(f'{label}: nothing reads it')

    def pending_givers(self) -> dict:
        """Items a `pending_npcs` topic gives (an NPC A4 has not numbered yet): item key -> 'stem pending name'."""
        givers = {}
        for data in self.model.quests:
            for name, npc in (data.get('pending_npcs') or {}).items():
                for topic in npc.get('topics') or []:
                    for state in [topic] + list(topic.get('states') or []):
                        for effect in state.get('do') or []:
                            if isinstance(effect, dict) and 'give' in effect:
                                givers.setdefault(effect['give'], f"{data['_stem']} {name}")
        return givers

    def check_items(self):
        for item, places in sorted(self.items_used.items()):
            if item.startswith('engine:'):
                continue
            if item not in self.items_given:
                giver = self.pending_givers().get(item)
                if giver:
                    self.open.append(f'item {item}: used ({places[0]}); given only by {giver}, an NPC without an id yet')
                else:
                    self.errors.append(f'item {item}: used ({places[0]}) but nothing gives it')
        for item, places in sorted(self.items_given.items()):
            if item.startswith('engine:'):
                continue
            if item not in self.items_used:
                self.info.append(f'item {item}: given ({places[0]}) but nothing takes or needs it')
        for data in self.model.quests:
            for item, description in (data.get('items') or {}).items():
                if item not in self.items:
                    target = self.open if data.get('status') == 'outline' else self.errors
                    target.append(f"{data['_stem']}: item {item} is not in A2's items.yml ({description})")

    def check_hooks_on_built_maps(self):
        # A hook that a xeen_common.lua helper calls by its full name (Xeen.genieLamp's lamps and wishes) is wired
        # wherever the map calls the helper.
        common = (xeenlib.WORLD / 'events/common/xeen_common.lua').read_text()
        # A cinematic's done hook is called by the generated done event (gen_quests cinematic_done_lua).
        done_hooks = {hook['cinematic_done'] for hook in self.model.hooks.values() if hook.get('cinematic_done')}
        for name, hook in sorted(self.model.hooks.items()):
            brief = self.briefs.get(hook.get('map'))
            if brief is None or f'"{name}"' in common or name in done_hooks:
                continue
            stem = hook['_file']['_stem']
            numbers = [self.model.qbits.get(self.model.qbit_key(stem, ref)) for ref in
                       (hook.get('sets') or []) + (hook.get('reads') or [])]
            known = set(brief['qbits'].values()) | brief['sets'] | brief['reads']
            missing = [number for number in numbers if number and number not in known]
            if name in brief['hooks']:
                continue
            if missing or (not numbers and gen_quests.hook_is_called(hook)):
                self.open.append(f"hook {name} on {hook.get('map')}: not wired in its project yet"
                                 + (f' (qbits {missing})' if missing else ''))

    def check_riddles_npcs(self):
        for data in self.model.quests:
            for riddle in data.get('riddles') or []:
                if not riddle.get('said_by'):
                    self.errors.append(f"{data['_stem']}: riddle {riddle.get('answer')!r} has no answer-giver")
        live_topics = self.model.topics
        problems_before = len(self.model.problems)
        gen_quests.assign_slots(self.model, live_topics)
        self.errors.extend(self.model.problems[problems_before:])
        # `pending_npc_ids: {id: why}`: an id a decision gave, which A4's town files do not list yet (open, not error).
        pending = {}
        for data in self.model.quests + self.model.npc_files:
            for npc, why in (data.get('pending_npc_ids') or {}).items():
                pending[int(npc)] = f"{data['_stem']}: {why}"
        for npc in sorted({topic['npc'] for topic in live_topics}):
            if npc in self.model.towns:
                continue
            if npc in pending:
                self.open.append(f"npc {npc}: not in A4's town files yet ({pending[npc]})")
            else:
                self.errors.append(f"npc {npc}: not in A4's town files")

    def check_main_order(self):
        def order(stem):
            match = MAIN_ORDER_KEY.match(stem)
            return int(match.group(1)) if match else None

        for quest in self.model.quests:
            mine = order(quest['_stem'])
            if mine is None:
                continue
            for ref in quest.get('after') or []:
                other = order(self.model.qbit_key(quest['_stem'], ref)[0])
                if other is not None and other > mine:
                    self.errors.append(f"{quest['_stem']}: comes after {ref}, a later main step")
        mains = sorted(order(quest['_stem']) for quest in self.model.quests if order(quest['_stem']) is not None)
        self.info.append(f'main steps written: {len(mains)} of 42 ({", ".join(f"M{m}" for m in mains)})')

    def check_common_lua(self):
        if not COMMON_LUA.exists():
            return
        text = COMMON_LUA.read_text(encoding='utf-8')
        for ref in sorted(set(re.findall(r'"((?:m|q-[cdf]|t\d-[a-e]|x\d-[a-z]+|mirrors)\d*\.[a-z0-9_]+)"', text))):
            key = self.model.qbit_key('', ref)
            if ref in self.model.hooks:
                continue
            if key not in self.model.qbits:
                target = self.errors if key[0] in self.model.by_stem else self.open
                target.append(f'xeen_common.lua names {ref}: ' + ('no such qbit' if key[0] in self.model.by_stem
                                                                   else 'its quest is not written yet'))

    def check_experience(self):
        acts: dict[str, int] = {}
        for quest in self.model.quests:
            act = str(quest.get('act'))
            xp = self.xp.get(quest['_stem'], 0)
            acts[act] = acts.get(act, 0) + xp
            cap = 1000 * float(quest.get('level') or 0) * CAP_FACTOR.get(act, 1.0)
            if xp > cap:  # promotions too since D-16: none pays more than a side quest of its level
                self.info.append(f"{quest['_stem']}: {xp} xp per member over the per-quest cap {cap:.0f} "
                                 f"(level {quest.get('level')}, act {act}; a promotion inside it counts)")
        self.act_xp = acts
        for act, budget in ACT_BUDGET.items():
            total = acts.get(act, 0)
            if total > budget * 1.15:
                self.errors.append(f'act {act}: {total} xp per member, over its budget {budget} by more than 15 %')

    # -- touch effects (F13) -----------------------------------------------------------------------------------------

    # A party effect: a statistic, resistance, bonus, HP/SP, age, condition or experience of the members (D-90 2: an
    # experience award at a touch site is a party effect too); not gold, items or map variables.
    GRANT_LUA = re.compile(r'\b(?:AddValue|SetValue|Subtract)\((?!MapVar|InventoryItem|Gold\b|v\b|v\d)\w+'
                           r'|evt\.CastSpell|Xeen\.giveEachOnce')

    def check_touch_sites(self):
        """F13 (the user, 2026-11-21): a shrine, well, fountain, statue, brew or other touch effect answers on the
        status line, as MM6-MM8, never with a message window. A hook is at a touch site when its own effects give a party
        effect (`stat:`, a `lua:` AddValue/SetValue of a member's property, Xeen.giveEachOnce) or a map event that gives
        one calls it; such a hook says `status: true`, or `window: <why>` for a long text the player must read (or a
        choice). A map event that gives a party effect and shows its own evt.SimpleMessage is an error too (the map's
        `window: true` or a reading title): unless it asks a question first (the choice is the dialogue)."""
        def own_grant(hook: dict) -> bool:
            for node in [hook] + list(hook.get('states') or []):
                for effect in node.get('do') or []:
                    if isinstance(effect, dict) and ('stat' in effect or 'xp' in effect
                                                     or self.GRANT_LUA.search(str(effect.get('lua', '')))):
                        return True
            return False

        called: dict[str, list[str]] = {}
        maps_dir = xeenlib.WORLD / 'events' / 'maps'
        for path in sorted(maps_dir.glob('xeen_*.lua')):
            for block in re.split(r'\n(?=-- evt:)', path.read_text(encoding='utf-8')):
                head = block.split('\n', 1)[0]
                if not head.startswith('-- evt:') or not self.GRANT_LUA.search(block):
                    continue
                if 'AskQuestion' in block or 'AskChoice' in block:
                    continue
                where = f'{path.stem} {head[3:]}'
                if 'evt.SimpleMessage' in block:
                    line = (f'touch site {where}: gives a party effect and shows a message window (F13: the status '
                            f'line; the map\'s lua says evt.StatusText, or drop its `window: true`)')
                    # The map sites found on 2026-11-21 wait for their map lanes (USER_FEEDBACK_20261121.md F13);
                    # any other is an error.
                    (self.open if (path.stem, head[3:]) in F13_MAP_SITES_OPEN else self.errors).append(line)
                for name in re.findall(r'XeenQuests\.hook\("([^"]+)"\)', block):
                    called.setdefault(name, []).append(where)
        for name, hook in sorted(self.model.hooks.items()):
            if hook.get('status') or hook.get('window'):
                continue
            if not (hook.get('text') or hook.get('states') or hook.get('else_text') or hook.get('fail_text')):
                continue
            if own_grant(hook) or name in called:
                site = ', '.join(called.get(name, [])[:2]) or 'its own effects'
                self.errors.append(f'touch hook {name} ({site}): shows a message window; say `status: true` '
                                   f'(F13) or `window: <why>` for a long reading text')

    # -- monster deaths (D-90 3) --------------------------------------------------------------------------------------

    DEATH_WHERE = re.compile(r"'s death\b|\bdies\b", re.IGNORECASE)

    def check_death_hooks(self):
        """D-90 3: a monster's death answers on the status line (`status: true`); a window only with
        `window: "<why>"` (a cinematic, a voiced line, a long story text that ends an act). A death hook is one a map
        event calls next to evt.CheckMonstersKilled, or whose `where` says it runs at a death."""
        killed: set[str] = set()
        for path in sorted((xeenlib.WORLD / 'events' / 'maps').glob('xeen_*.lua')):
            for block in re.split(r'\n(?=-- evt:)', path.read_text(encoding='utf-8')):
                if 'CheckMonstersKilled' in block:
                    killed.update(re.findall(r'XeenQuests\.hook\("([^"]+)"\)', block))
        for name, hook in sorted(self.model.hooks.items()):
            if not (name in killed or self.DEATH_WHERE.search(str(hook.get('where', '')))):
                continue
            if not (hook.get('text') or hook.get('states')):
                continue
            if hook.get('status') or hook.get('window') or gen_quests.is_find(hook):
                continue
            self.errors.append(f'death hook {name}: shows a message window; say `status: true` (D-90 3) or '
                               f'`window: "<why>"` (a cinematic, a voiced line, a long text that ends an act)')

    # -- dungeon gating (D-89) ---------------------------------------------------------------------------------------

    def _map_stems(self) -> dict[str, str]:
        stems = {}
        for entry in (xeenlib.load_yaml(xeenlib.SOURCE / 'maps.yml') or {}).get('maps', []):
            if entry.get('stem'):
                stems[str(entry['stem']).rsplit('.', 1)[0]] = str(entry.get('key'))
        return stems

    def _bit_maps(self) -> dict[int, set[str]]:
        """qbit -> the maps whose hooks set it, plus the map its registration names (`map:`)."""
        maps: dict[int, set[str]] = {}
        for data in self.model.quests + self.model.npc_files:
            for name, entry in (data.get('qbits') or {}).items():
                if entry.get('map'):
                    maps.setdefault(int(entry['id']), set()).add(str(entry['map']))
        for name, hook in self.model.hooks.items():
            stem = hook['_file']['_stem']
            refs = list(hook.get('sets') or [])
            for node in [hook] + list(hook.get('states') or []):
                refs += [effect['set'] for effect in node.get('do') or [] if isinstance(effect, dict) and 'set' in effect]
            for ref in refs:
                number = self.model.qbits.get(self.model.qbit_key(stem, ref))
                if number:
                    maps.setdefault(number, set()).add(str(hook.get('map')))
        for key, brief in self.briefs.items():
            for number in brief['sets']:
                maps.setdefault(number, set()).add(key)
        return maps

    def _refs(self, condition, out: list):
        if isinstance(condition, dict):
            for key, value in condition.items():
                if key == 'qbit':
                    out.append(str(value))
                elif key == 'not':
                    self._refs(value, out)
                elif key in ('all', 'any'):
                    for part in value:
                        self._refs(part, out)

    def check_gating(self):
        """D-89 (the user's F17): every dungeon can be entered and cleared without a story item, a quest bit or a
        conversation. Errors: an outer-door hook (`entrance:`) with a condition and not on SEALED (with its `sealed:`
        reason and a fail_text that points the way in); a map event that moves into a dungeon while testing a bit, an
        item or a conditional hook that is neither on the sealed lists nor a shortcut the dungeon opens itself; a hook
        a map's entrance event calls that does not say `entrance:`; a condition inside a dungeon without its tag
        (`gate:` beat, puzzle, order, faction, shortcut); a refusal that moves the party."""
        stems = self._map_stems()
        bit_maps = self._bit_maps()
        hooks = self.model.hooks
        for name, hook in sorted(hooks.items()):
            conditional = bool(hook.get('requires') or hook.get('needs'))
            if hook.get('sealed') and name not in SEALED:
                self.errors.append(f'gate {name}: `sealed:` but not on the sealed list (a new seal needs a decider, '
                                   f'D-89; quests.py SEALED)')
            if hook.get('entrance') and hook.get('gate') == 'shortcut':
                # a way the dungeon opens from inside (a culvert, a shaft, a grate): its bits are set in that dungeon
                stem = hook['_file']['_stem']
                refs = []
                self._refs(hook.get('requires'), refs)
                outside = [ref for ref in refs
                           if hook['entrance'] not in bit_maps.get(self.model.qbits.get(self.model.qbit_key(stem, ref)), set())]
                if hook.get('needs') or outside:
                    self.errors.append(f"gate {name}: a shortcut into {hook['entrance']} reads only bits that dungeon "
                                       f"sets ({outside or hook.get('needs')})")
            elif hook.get('entrance'):
                if conditional and name not in SEALED:
                    self.errors.append(f"gate {name}: the outer door of {hook['entrance']} has a condition (D-89: "
                                       f'every dungeon opens; a seal needs a decider)')
                elif conditional and not (hook.get('sealed') and (hook.get('fail_text') or name in SEALED_NO_LINE)):
                    self.errors.append(f'gate {name}: a sealed outer door says `sealed: "<reason>"` and a fail_text '
                                       f'naming where the way in comes from')
            elif conditional and DUNGEON_KEY.match(str(hook.get('map'))) and name not in SEALED:
                if hook.get('gate') not in gen_quests.GATE_TAGS:
                    self.errors.append(f"gate {name} ({hook.get('map')}): a condition inside a dungeon says "
                                       f"`gate:` {'|'.join(sorted(gen_quests.GATE_TAGS))} (D-89 1.5)")
        self.sealed_lines = []
        for path in sorted((xeenlib.WORLD / 'events' / 'maps').glob('xeen_*.lua')):
            for block in re.split(r'\n(?=-- evt:)', path.read_text(encoding='utf-8')):
                head = block.split('\n', 1)[0]
                if not head.startswith('-- evt:'):
                    continue
                site = (path.stem, head[3:])
                where = f'{path.stem} {head[3:]}'
                pending = D89_MAP_SITES_OPEN.get(site)
                # A refusal that moves the party (D-89 4): `if not XeenQuests.hook/can(...) then` ... MoveToMap before
                # the branch ends.
                for match in re.finditer(r'if not \(*XeenQuests\.(?:hook|can)\("[^"]+"\)\)*\s+then\b(.*?)'
                                         r'(?:\breturn\b|\n\s*end\b|\n\s*else)', block, re.S):
                    # a move to another map (a move inside the map lets the party out, as Castleview's inner gates)
                    if re.search(r'MoveToMap\([^)]*"xeen_\w+\.(?:blv|odm)"', match.group(1)):
                        line = f'refusal moves the party: {where} (D-89: a refused door never moves the party)'
                        (self.open if pending else self.errors).append(line + (f' [{pending}]' if pending else ''))
                targets = {stems.get(stem) for stem in re.findall(r'MoveToMap\([^)]*"(xeen_\w+)\.blv"', block)}
                targets = {key for key in targets if key and DUNGEON_KEY.match(key)}
                here = stems.get(path.stem, '')
                if not targets or (DUNGEON_KEY.match(here) and not targets - {here}):
                    continue
                called = re.findall(r'XeenQuests\.(?:hook|can)\("([^"]+)"\)', block)
                latched = set()
                for name in called:
                    hook = hooks.get(name)
                    if hook is None:
                        continue
                    stem = hook['_file']['_stem']
                    latched.update(self.model.qbits.get(self.model.qbit_key(stem, ref)) for ref in hook.get('sets') or [])
                    if not hook.get('entrance') and (hook.get('requires') or hook.get('needs')):
                        self.errors.append(f'gate {name}: called by the entrance {where} (into '
                                           f"{', '.join(sorted(targets))}) with a condition; say `entrance:` (D-89)")
                bits = {int(n) for n in re.findall(r'IsQBitSet\(QBit\((\d+)\)\)', block)}
                bits |= {self.model.qbits.get(self.model.qbit_key('', ref))
                         for ref in re.findall(r'Xeen\.isSet\("([^"]+)"\)', block)} - {None}
                items = re.findall(r'HasItem\((\d+)\)', block)
                for number in sorted(bits):
                    inside = targets | ({here} if DUNGEON_KEY.match(here) else set())
                    if number in latched or bit_maps.get(number, set()) & inside:
                        continue   # the hook this event calls latches it, or a dungeon opens it from inside
                    if site in SEALED_MAP_EVENTS:
                        continue
                    line = f'entrance {where} (into {", ".join(sorted(targets))}) tests qbit {number} directly (D-89)'
                    (self.open if pending else self.errors).append(line + (f' [{pending}]' if pending else ''))
                if items and site not in SEALED_MAP_EVENTS:
                    self.errors.append(f'entrance {where} tests an item directly (HasItem {items}); use a sealed hook')
        for name, reason in sorted(SEALED.items()):
            hook = hooks.get(name)
            if hook is None:
                self.errors.append(f'sealed list: no hook {name}')
                continue
            self.sealed_lines.append(f"{name} ({reason}): {gen_quests.clean(hook.get('fail_text') or '(no line)')}")

    # -- report ------------------------------------------------------------------------------------------------------

    # D-93: a find hidden in a prop (a barrel, a pack, a crate, a sack, a nest...) goes onto the cursor from the prop's
    # click (a hook with `gives:`), as MM6-MM8's evt.GiveItem; only an item lying in the open is a ground item. A
    # sketch's ground item this close to a decoration (grid units, 512 game units each) reads as hidden in it.
    PROP_FIND_DISTANCE = 0.6

    def check_prop_finds(self):
        for path in sorted(BRIEFS.glob('*/L4/sketch.yml')):
            try:
                sketch = yaml.safe_load(path.read_text()) or {}
            except yaml.YAMLError:
                continue
            props = [thing for thing in sketch.get('structures') or []
                     if isinstance(thing, dict) and thing.get('kind') == 'decoration' and thing.get('at')]
            for item in sketch.get('items') or []:
                if not isinstance(item, dict) or not item.get('at') or item.get('in_the_open'):
                    continue
                near = [thing['id'] for thing in props
                        if math.dist(item['at'][:2], thing['at'][:2]) <= self.PROP_FIND_DISTANCE]
                if near:
                    self.errors.append(
                        f"{path.relative_to(xeenlib.ROOT)}: {item.get('id')} lies at {near[0]}: a find in a prop is given "
                        "onto the cursor by the prop's click (a hook with `gives:`, D-93), not placed as a ground item "
                        "(`in_the_open: \"<why>\"` for an item that only lies beside it in plain sight)")

    def run(self, show_open: bool) -> int:
        self.walk()
        self.check_prop_finds()
        self.check_numbers()
        self.check_built_maps()
        self.check_towns()
        self.note_common_lua_writers()
        self.check_writers_readers()
        self.check_items()
        self.check_hooks_on_built_maps()
        self.check_riddles_npcs()
        self.check_main_order()
        self.check_common_lua()
        self.check_experience()
        self.check_touch_sites()
        self.check_death_hooks()
        self.check_gating()

        full = [q['_stem'] for q in self.model.quests if q.get('status') != 'outline']
        outline = [q['_stem'] for q in self.model.quests if q.get('status') == 'outline']
        print(f'Quest files: {len(self.model.quests)} ({len(full)} full, {len(outline)} outline); '
              f'NPC files: {len(self.model.npc_files)}; topics: {len(self.model.topics)}; hooks: {len(self.model.hooks)}; '
              f'qbits: {len(self.model.qbits)}; built maps read: {len(self.briefs)}')
        print('Quest experience per member by act (budget):')
        for act, budget in ACT_BUDGET.items():
            total = self.act_xp.get(act, 0)
            print(f'  {act:>3}: {total:>7} / {budget} ({100 * total / budget:.0f} %)')
        for title, lines in (('ERRORS', self.errors), ('INFO', self.info)):
            if lines:
                print(f'{title} ({len(lines)}):')
                for line in lines:
                    print(f'  {line}')
        if show_open:
            print(f'SEALED outer doors (D-89; {len(self.sealed_lines)}), with their refusal lines:')
            for line in self.sealed_lines:
                print(f'  {line}')
        print(f'OPEN ({len(self.open)})' + (':' if show_open else ' (--open lists them)'))
        if show_open:
            for line in self.open:
                print(f'  {line}')
        return 1 if self.errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--open', action='store_true', help='list the open items too')
    args = parser.parse_args()
    try:
        sys.exit(Audit().run(args.open))
    except xeenlib.BuildError as error:
        xeenlib.fail(str(error))


if __name__ == '__main__':
    main()
