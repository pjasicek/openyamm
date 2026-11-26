#!/usr/bin/env python3
"""Dungeon campfires (D-104; F74 of devdocs/xeen/reviews/PLAYER_FEEDBACK_20261126.md, the engine agent's survey): an
open fire a party would sit at (a camp's cookfire, a den's fire, a hall's hearth) feeds the party once and gives a
character with Perception a small ring, as the outdoor campfires do (common/wild.py CAMPFIRE_LUA, MM8 Global 285/286
"Camp Fire", MM7's campfire ring). Braziers, forges, a study's grate and XD-04's stoking pots are fixtures: no click.

    python3 level_generation/projects/xeen/common/campfires.py apply <key>    add the missing events to <key>'s L4
    python3 level_generation/projects/xeen/common/campfires.py --check        every map: exit 1 on an error

`apply` adds one `preset: script` event per open fire at the end of L4/wiring.yml's events (source the decoration, `once: true`, the
outdoor campfire's Lua) when the fire has no event yet; regen.py runs it after each listed map's generator, and on
XD-05 (no generator: its L4 is the source) it is run once by hand. `--check`:
- `campfire.unlisted` (error): a fire decoration (FIRE_NAMES) in an indoor L4 that is in neither CAMPFIRES nor FIXTURES;
- `campfire.no_event` (error): a listed campfire whose L4 has no `once` campfire event for it;
- `campfire.not_installed` (error): the installed map Lua carries fewer campfire events than the L4 lists (rebuild and
  install the map).
"""
import json
import os
import sys

import yaml

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.realpath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, HERE)
from wild import CAMPFIRE_LUA, FIRES  # noqa: E402

FIRE_NAMES = set(FIRES) | {'v77dec24', 'fire01'}
# The open fires a party expects to use (the engine agent's survey, f74/fire_survey_blv.py, 2026-11-26).
CAMPFIRES = {
    'xd05': ['deco:cookfire', 'deco:den_fire', 'deco:hollows_fire'],
    'xd07': ['deco:hearth_fire'],
    'xd14': ['deco:hearth_fire'],
    'xd21': ['deco:boss_fire'],
    'xd27': ['deco:chief_fire', 'deco:den_fire', 'deco:quarry_fire', 'deco:yard_fire', 'deco:pit_cookfire',
             'deco:pit_fire'],
    'dd04': ['deco:barracks_fire'],
    'dd05': ['deco:kitchen_fire'],
    'dd09': ['deco:cookfire'],
    'dd13': ['deco:fire_e', 'deco:fire_w'],
    'dd24': ['deco:hearth_fire', 'deco:trench_fire_1', 'deco:trench_fire_2'],
    'dd25': ['deco:hearth_fire'],
}
# Fire decorations that are fixtures, not camp fires (no click wanted).
FIXTURES = {
    'xd03': {d: 'a brazier in the king hall' for d in ('deco:brazier_e1', 'deco:brazier_e2', 'deco:brazier_se',
                                                       'deco:brazier_sw', 'deco:brazier_w1', 'deco:brazier_w2',
                                                       'deco:forge_brazier_e', 'deco:forge_brazier_w')},
    'xd04': dict({'deco:stoking_pot_%d' % i: "a stoking pot under the witches' cauldrons" for i in (1, 2, 3, 4)},
                 **{'deco:vat_bubbling': 'the fire under the bubbling vat'}),
    'xd05': {'deco:hall_fire': 'a brazier in the drum hall', 'deco:hearth_fire': "a brazier beside the cookfire",
             'deco:yard_brazier': 'a brazier in the palisade yard'},
    'xd09': {'deco:forge_fire': "the golem forge's fire"},
    'xd12': {'deco:well_brazier_%d' % i: 'a brazier round the well' for i in range(4)},
    'xd14': {'deco:study_fire': "the study's grate"},
    'dd24': {'deco:brazier_e': "a throne hall brazier", 'deco:brazier_w': "a throne hall brazier"},
    'dd25': {'deco:forge_fire': "the forge bay's fire"},
}
MARK = 'a ring in the ashes'   # a phrase of CAMPFIRE_LUA, counted in the installed Lua


def l4(key):
    return os.path.join(REPO, 'devdocs', 'xeen', 'briefs', key, 'L4')


def title_of(deco):
    name = deco.split(':', 1)[1]
    if 'hearth' in name:
        return 'Hearth'
    if 'cook' in name or 'kitchen' in name:
        return 'Cooking fire'
    return 'Campfire'


def events_by_source(key):
    wiring = yaml.safe_load(open(os.path.join(l4(key), 'wiring.yml'))) or {}
    out = {}
    for e in wiring.get('events') or []:
        if e.get('source'):
            out.setdefault(e['source'], []).append(e)
    return out


def is_campfire_event(e):
    return e.get('preset') == 'script' and e.get('once') and MARK in (e.get('lua') or '')


def apply(key):
    """Add the missing campfire events at the end of the L4's wiring.yml `events` list (as text: the rest of the
    file stays as it is)."""
    path = os.path.join(l4(key), 'wiring.yml')
    lines = open(path).read().rstrip('\n').split('\n')
    start = lines.index('events:')
    end = next((i for i in range(start + 1, len(lines)) if lines[i][:1] not in ('', ' ', '-')), len(lines))
    item = next((ln for ln in lines[start + 1:end] if ln.lstrip().startswith('- ')), '  - ')
    pad = ' ' * (len(item) - len(item.lstrip()))   # the list's own indent (a generator's dump has none, fmt two)
    have = events_by_source(key)
    objects = yaml.safe_load(open(os.path.join(l4(key), 'objects.yml')))
    decos = {d['id'] for d in objects.get('decorations') or []}
    added = []
    for deco in CAMPFIRES.get(key, []):
        if deco not in decos:
            sys.exit('%s: %s is not a decoration of the L4' % (key, deco))
        if have.get(deco):
            if not any(is_campfire_event(e) for e in have[deco]):
                sys.exit('%s: %s has an event of its own; merge the campfire by hand' % (key, deco))
            continue
        added.append('\n'.join(pad + ln for ln in [
            '- id: evt:campfire_%s' % deco.split(':', 1)[1],
            '  preset: script',
            '  source: %s' % deco,
            '  title: %s' % title_of(deco),
            '  once: true',
            '  lua: %s' % json.dumps(CAMPFIRE_LUA),
            '  notes: "D-104: a dungeon campfire feeds the party once and gives a character with Perception a small '
            'ring, as the outdoor campfires (level_generation/projects/xeen/common/campfires.py)."']))
    if added:
        lines[end:end] = added
        with open(path, 'w') as f:
            f.write('\n'.join(lines) + '\n')
    print('%s: %d campfire events added' % (key, len(added)))


def check():
    errors = []
    listed = 0
    for key in sorted(os.listdir(os.path.join(REPO, 'devdocs', 'xeen', 'briefs'))):
        objects_path = os.path.join(l4(key), 'objects.yml')
        if not os.path.exists(objects_path) or not os.path.exists(os.path.join(l4(key), 'wiring.yml')):
            continue
        objects = yaml.safe_load(open(objects_path)) or {}
        fires = [d['id'] for d in objects.get('decorations') or [] if d.get('decoration') in FIRE_NAMES]
        camp = set(CAMPFIRES.get(key, []))
        for deco in fires:
            if deco not in camp and deco not in FIXTURES.get(key, {}):
                errors.append('%s campfire.unlisted: %s is a fire in neither CAMPFIRES nor FIXTURES' % (key, deco))
        if not camp:
            continue
        have = events_by_source(key)
        for deco in sorted(camp):
            listed += 1
            if not any(is_campfire_event(e) for e in have.get(deco, [])):
                errors.append('%s campfire.no_event: %s has no once campfire event (run campfires.py apply %s)'
                              % (key, deco, key))
        lua = os.path.join(REPO, 'assets_dev', 'worlds', 'xeen', 'events', 'maps', 'xeen_%s.lua' % key)
        n = open(lua).read().count(MARK) if os.path.exists(lua) else 0
        if n < len(camp):
            errors.append('%s campfire.not_installed: the installed Lua has %d campfire events, the L4 lists %d'
                          % (key, n, len(camp)))
    for e in errors:
        print(e)
    print('%d campfires listed on %d maps, %d fixtures; %d errors' % (
        listed, len(CAMPFIRES), sum(len(v) for v in FIXTURES.values()), len(errors)))
    return 1 if errors else 0


if __name__ == '__main__':
    if sys.argv[1:] == ['--check']:
        sys.exit(check())
    if len(sys.argv) == 3 and sys.argv[1] == 'apply':
        apply(sys.argv[2])
        sys.exit(0)
    sys.exit(__doc__)
