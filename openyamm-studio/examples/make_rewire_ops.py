#!/usr/bin/env python3
"""Writes the operations of the two S2 acceptance rewires (devdocs/map_studio/S2.md), the way an agent does it: read
what the base map's handlers do (`oymap flow`), state it as wiring presets, apply with `oymap edit`.

  goblinwatch_vault   events 19 to 34 (the sixteen lettered keys): switch presets (doors opened and closed, the
                      key's texture, the map variable that marks the use), one teleport, two scripts
  new_sorpigal_wells  the wells and fountains: text presets with conditions and effects, written by hand

Usage: make_rewire_ops.py <oymap> <asset root>   (writes <example>/rewire.ops.json)
"""
import json, re, subprocess, sys
from pathlib import Path

oymap, assets = sys.argv[1], Path(sys.argv[2])
here = Path(__file__).resolve().parent


def flow(map_file):
    out = subprocess.run([oymap, 'flow', map_file, '--world', 'mm6', '--assets', str(assets)],
                         capture_output=True, text=True, check=True).stdout
    return {event['event']: event for event in json.loads(out)}


def lua_of(effect):
    """A recorded effect back as a Lua statement."""
    if match := re.fullmatch(r'door (\d+) (open|close|toggle)', effect):
        action = {'open': 'Open', 'close': 'Close', 'toggle': 'Trigger'}[match[2]]
        return f'evt.SetDoorState({match[1]}, DoorAction.{action})'
    if match := re.fullmatch(r'set map_var (\d+) = (-?\d+)', effect):
        return f'SetValue(MapVar({match[1]}), {match[2]})'
    if match := re.fullmatch(r'SetTexture\((-?\d+), "(\w+)"\)', effect):
        return f'evt.SetTexture({match[1]}, "{match[2]}")'
    raise SystemExit(f'no Lua for the effect {effect!r}')


# --- Goblinwatch's vault -----------------------------------------------------------------------------------------
events = flow('6d01.blv')
ops = []
for number in range(19, 35):
    event = events[number]
    acting = [path for path in event['paths'] if path['effects']]
    name = f"evt:key_{event['title'].lower()}"
    value = {'id': name, 'replaces': f'evt:e{number}', 'title': event['title']}
    assert len(acting) == 1, number
    path = acting[0]
    effects = list(path['effects'])
    teleport = [e for e in effects if e.startswith('teleport to ')]
    if teleport:
        x, y, z = (int(v) for v in re.match(r'teleport to (-?\d+), (-?\d+), (-?\d+)', teleport[0]).groups())
        value.update(preset='teleport', to=[x, y, z], direction=22.5)       # 128 of 2048 units
    elif path['tests'] and all(re.fullmatch(r'(door \d+ (open|close))|(set map_var \d+ = 1)|(SetTexture\(.*\))', e)
                               for e in effects):
        test = path['tests'][0]
        variable = int(re.fullmatch(r'map_var (\d+) >= 1', test['what'])[1])
        assert not test['taken'] and f'set map_var {variable} = 1' in effects
        value.update(preset='switch', condition={'not': {'map_var': variable}}, sets={'map_var': variable},
                     opens=[f"door:d{m[1]}" for e in effects if (m := re.fullmatch(r'door (\d+) open', e))],
                     closes=[f"door:d{m[1]}" for e in effects if (m := re.fullmatch(r'door (\d+) close', e))])
        texture = [re.fullmatch(r'SetTexture\((-?\d+), "(\w+)"\)', e) for e in effects if e.startswith('SetTexture')]
        if texture:
            value['texture'] = {'cog': int(texture[0][1]), 'name': texture[0][2]}
        if not value['opens']:
            del value['opens']
    elif number == 19:
        value.update(preset='script', lua='evt.CastSpell(6, 3, 1, 2496, 4864, 360, 0, 0, 0)',
                     notes='Key A is the trap: a Fireball at the vault door.')
    else:
        value.update(preset='script', lua='\n'.join(lua_of(e) for e in effects),
                     notes='The reset key: every key works again and every vault door returns.')
    ops.append({'op': 'event.add', 'value': value})
(here / 'goblinwatch_vault/rewire.ops.json').write_text(json.dumps(ops, indent=1) + '\n')

# --- New Sorpigal's wells and fountains ---------------------------------------------------------------------------
# Written by hand as presets with conditions and effects (S3): what each handler tests and does is read from
# `oymap flow oute3.odm --event <n>`; tests/run_rewire.sh proves the result equal.
refreshing = 'Refreshing!'
ops = [
    {'op': 'event.add', 'value': {
        'id': 'evt:water_109', 'preset': 'text', 'replaces': 'evt:e109', 'title': 'Well',
        'condition': {'all': [{'not': {'map_var': 71}}, {'gold': {'below': 1}}]},
        'effects': [{'add': {'var': {'map_var': 71}, 'value': 1}}, {'gold': 100}],
        'locked_text': refreshing,
        'notes': 'Pays 100 gold once to a party with none.'}},
    {'op': 'event.add', 'value': {
        'id': 'evt:water_110', 'preset': 'text', 'replaces': 'evt:e110', 'title': 'Well',
        'condition': {'all': [{'not': {'stat': {'name': 'BaseLuck', 'at_least': 15}}}, {'map_var': 72}]},
        'effects': [{'subtract': {'var': {'map_var': 72}, 'value': 1}}, {'add': {'var': 'BaseLuck', 'value': 2}}],
        'text': '+2 Luck permanent', 'locked_text': refreshing,
        'notes': 'Two points of Luck to the unlucky, while the well has charges (map variable 72).'}},
    {'op': 'event.add', 'value': {
        'id': 'evt:water_131', 'preset': 'text', 'replaces': 'evt:e131', 'title': 'Drink from Fountain',
        'condition': {'map_var': 51},
        'effects': [{'subtract': {'var': {'map_var': 51}, 'value': 1}}, {'add': {'var': 'HP', 'value': 5}},
                    {'autonote': 391}],
        'text': '+5 Hit points restored.',
        'else_effects': [{'autonote': 391}], 'locked_text': refreshing}},
    {'op': 'event.add', 'value': {
        'id': 'evt:water_140', 'preset': 'text', 'replaces': 'evt:e140', 'title': 'Drink from Fountain',
        'condition': {'map_var': 52},
        'effects': [{'subtract': {'var': {'map_var': 52}, 'value': 1}}, {'add': {'var': 'SP', 'value': 5}},
                    {'autonote': 392}, {'lua': 'evt.OpenDimensionDoor()'}],
        'text': '+5 Spell points restored.',
        'else_effects': [{'autonote': 392}, {'lua': 'evt.OpenDimensionDoor()'}], 'locked_text': refreshing}},
    {'op': 'event.add', 'value': {
        'id': 'evt:water_150', 'preset': 'text', 'replaces': 'evt:e150', 'title': 'Drink from Fountain',
        'condition': {'not': {'stat': {'name': 'MightBonus', 'at_least': 10}}},
        'effects': [{'set': {'var': 'MightBonus', 'value': 10}}, {'autonote': 393}],
        'text': '+10 Might temporary.',
        'else_effects': [{'autonote': 393}], 'locked_text': refreshing}},
]
(here / 'new_sorpigal_wells/rewire.ops.json').write_text(json.dumps(ops, indent=1) + '\n')
