# First wiring.yml of the Goblinwatch rebuild: one event per handler of the original (oymap flow 6d01.blv, 6d01.lua).
# Written once; wiring.yml is the source afterwards.
import yaml, sys

ev = []
variables = []


def door(n, src=None, title='Door', notes='', **kw):
    e = {'id': f'evt:d{n}', 'preset': 'door', 'source': src or f'door:d{n}', 'action': 'open'}
    if title:
        e['title'] = title
    e.update(kw)
    e['notes'] = (f'Original event {n}: the door opens and stays open. ' + notes).strip()
    ev.append(e)


for n in list(range(1, 19)):
    door(n)
door(61, 'door:d23', notes='Door record 23.')
ev[-1]['id'] = 'evt:d23'
ev.append({'id': 'evt:d30w', 'preset': 'door', 'source': 'door:d30w', 'action': 'open', 'opens': ['door:d30e'],
           'notes': "Original event 63 (no title), bound to both towers' back walls (faces 1626, 1627): door record 30 rises with both. Clicked here on the west leaf."})
ev.append({'id': 'evt:d30e', 'preset': 'door', 'source': 'door:d30e', 'action': 'open', 'opens': ['door:d30w'],
           'notes': 'Original event 63, the east leaf.'})
ev.append({'id': 'evt:d60', 'preset': 'door', 'source': 'door:d60', 'action': 'open', 'title': 'Door', 'side': 'room:s51',
           'notes': "Original event 60: both leaves (records 45, 46) part, clicked from the corridor's side only; the leaves' faces toward the cave run event 38, which has no handler (nothing happens), as here."})
ev.append({'id': 'evt:dais', 'preset': 'switch', 'source': 'switch:dais', 'title': 'Switch', 'opens': ['mover:towers'],
           'notes': "Original event 62: the button (door record 31) is pushed in and the two towers' walls (door record 32) sink."})

G = {36: 'mover:g36', 38: 'mover:g38', 40: 'mover:g40', 44: 'mover:g44', 47: 'mover:g47', 48: 'mover:g48',
     51: 'mover:g51', 52: 'mover:g52', 55: 'mover:g55', 56: 'mover:g56', 57: 'mover:g57', 58: 'mover:g58',
     59: 'mover:g59', 60: 'mover:g60'}
# letter: (event, var number, records moved away ('close' in the original), records set back ('open'))
PUZ = {'b': (20, 2, [55, 56], [57, 58]), 'c': (21, 3, [57, 58], [55, 56]), 'd': (22, 4, [40, 52, 51], [57, 58]),
       'e': (23, 5, [57, 58], [40, 52, 51]), 'f': (24, 6, [36, 47, 48], [55, 56]), 'g': (25, 7, [59, 60], []),
       'h': (26, 8, [38, 44], [36, 47, 48]), 'i': (27, 9, [36, 47, 48], [38, 44]), 'j': (28, 10, [36, 47, 48], [40, 52, 51]),
       'k': (29, 11, [59, 60], [57, 58]), 'l': (30, 12, [38, 44], [55, 56]), 'n': (32, 13, [40, 51, 52], [36, 47, 48]),
       'o': (33, 14, [57, 58], [59, 60])}
for letter, (n, var, away, back) in PUZ.items():
    v = f'switch_{letter}'
    variables.append(v)
    e = {'id': f'evt:{letter}', 'preset': 'switch', 'source': f'switch:{letter}', 'title': letter.upper(),
         'condition': {'not': {'map_var': v}}, 'sets': {'map_var': v}}
    if away:
        e['opens'] = [G[r] for r in away]
    if back:
        e['closes'] = [G[r] for r in back]
    e['notes'] = (f"Original event {n} ('{letter.upper()}'): once until P resets it (map variable {var} there), the gate bands of door records "
                  f"{away} slide away and {back or 'none'} come back, and the switch's picture turns to T1swDu. Used again before the reset: nothing.")
    ev.append(e)
ev.append({'id': 'evt:a', 'preset': 'switch', 'source': 'switch:a', 'title': 'A',
           'effects': [{'lua': 'evt.CastSpell(6, 3, 1, 2496, 4864, 360, 0, 0, 0)'}],
           'notes': "Original event 19 ('A'): a trap: a fireball (spell 6, mastery 3, level 1) from over the gallery's east end (2496, 4864, 360) at the party; the picture does not change (its `on` is its `off`). The cast is Lua: the `cast` effect's target is a point, the original's is the party (0, 0, 0)."})
ev.append({'id': 'evt:m', 'preset': 'switch', 'source': 'switch:m', 'title': 'M',
           'effects': [{'teleport': {'to': [9000, 1916, -767], 'direction': 22}}],
           'notes': "Original event 31 ('M'): the party is moved to (9000, 1916, -767) in the east cave, facing 128 of 2048 (22 degrees); the picture does not change."})
reset_lua = ['for _, v in ipairs({' + ', '.join(f'MapVar(switch_{l})' for l in PUZ) + '}) do SetValue(v, 0) end',
             '-- the switches\' pictures back to T1swDd: their faces by the cogs ids.lock.yml keeps',
             'for _, cog in ipairs(PLATES) do evt.SetTexture(cog, "t1swdd") end']
ev.append({'id': 'evt:p', 'preset': 'switch', 'source': 'switch:p', 'title': 'P',
           'closes': [G[r] for r in (40, 51, 52, 36, 47, 48, 38, 44, 55, 56, 57, 58, 59, 60)],
           'effects': [{'lua': '\n'.join(reset_lua)}],
           'notes': "Original event 34 ('P'): every switch B to O is set back (its variable to 0, its picture to T1swDd) and every gate band comes back. The pictures by Lua (no word sets a switch's picture back); the cog numbers are filled in after the first build."})
ev.append({'id': 'evt:plates_load', 'preset': 'script', 'trigger': 'load',
           'lua': 'PLATE_LOAD',
           'notes': "Original event 66 (on load): each switch whose variable is set shows T1swDu. As the original: E's picture follows D's variable (the original tests MapVar(4) twice), a slip kept."})

for rec, cid in [(3, 'chest:c3'), (5, 'chest:c5'), (6, 'chest:c6'), (8, 'chest:c8'), (9, 'chest:c9'), (10, 'chest:c10')]:
    ev.append({'id': f'evt:c{rec}', 'preset': 'chest', 'source': cid, 'title': 'Chest', 'notes': f'Original event {40 + rec}: opens chest record {rec}.'})
variables.append('ambush')
ev.append({'id': 'evt:c7', 'preset': 'chest', 'source': 'chest:c7', 'title': 'Chest',
           'effects': [{'lua': 'if not IsAtLeast(MapVar(ambush), 1) then\n  SetValue(MapVar(ambush), 1)\n  evt.SummonObject(2100, 9856, 4992, -1024, 512, 3, false)\n  evt.SummonMonsters(2, 2, 3, 9856, 4992, -1024, 0, 0)\nend'}],
           'notes': "Original event 47: opens chest record 7, and the first time a starburst (object 2100) and three goblins of tier B (slot 2) at (9856, 4992, -1024), the vault's middle. Lua: no word does an effect once inside a chest's event, nor summons an object."})
for rec, panel in [(1, 'panel:chest1'), (2, 'panel:chest2'), (4, 'panel:chest4')]:
    ev.append({'id': f'evt:c{rec}', 'preset': 'script', 'source': panel, 'title': 'Chest', 'effects': [{'open_chest': f'chest:c{rec}'}],
               'notes': f"Original event {40 + rec}: opens chest record {rec}, which has no box: the chest picture ch2frnt on the locker's back wall."})
ev.append({'id': 'evt:exit', 'preset': 'exit', 'source': 'exit:way_out', 'title': 'Exit Door',
           'notes': 'Original event 51: to New Sorpigal (oute3.odm) at (-18400, -14982, 1600), facing 512 of 2048.'})
variables.append('armour_found')
ev.append({'id': 'evt:armour', 'preset': 'script', 'source': 'panel:armour', 'condition': {'not': {'map_var': 'armour_found'}},
           'sets': {'map_var': 'armour_found'}, 'effects': [{'lua': 'evt.GiveItem(4, ItemType.Armor_)'}],
           'notes': "Original event 55 (no title): a spot of the sewer passage's east wall gives a random armour of level 4 once (map variable 26). The give is Lua (no word gives a random item of a level and kind)."})
variables.append('wizard_eye')
ev.append({'id': 'evt:fountain', 'preset': 'script', 'source': 'platform:spout', 'condition': {'not': {'map_var': 'wizard_eye'}},
           'sets': {'map_var': 'wizard_eye'}, 'effects': [{'lua': 'evt.CastSpell(12, 15, 1, 0, 0, 0, 0, 0, 0)'}],
           'notes': "Original event 64 (no title), bound to the fountain's rims, spout and fire: Wizard Eye (spell 12) on the party once until the daily reset. Bound here to the spout alone (an event has one source)."})
ev.append({'id': 'evt:fountain_reset', 'preset': 'script', 'trigger': 'timer', 'every': 2880,
           'effects': [{'set': {'var': {'map_var': 'wizard_eye'}, 'value': 0}}],
           'notes': "Original event 65: daily at midnight the fountain's Wizard Eye is ready again. Here every 2880 half minutes (a day) from entry: no word for a timer at an hour of the day indoors."})

out = {'format': 0, 'variables': variables, 'events': ev}
yaml.safe_dump(out, sys.stdout, sort_keys=False, width=200)
