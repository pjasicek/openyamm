#!/usr/bin/env python3
"""XD-18 Dragon Cave: writes the L4 playtests from the built ids.lock.yml (event and door numbers by name).

  playtest.yml            the critical path: the urn before and after, volume 1, Scaldrith's tax (house 4852), the
                          inner door opened in the same visit (118100), the upper halls, the ledge, the walked stair,
                          the roost, the library (volumes 2-5, the ledger), the King killed: the grate up in the same
                          visit (118101), the hoard; every window closed, a save and load: both still open
  playtest_tax.yml        D-89 without the tax: the inner door opens (118100), the Dragon King's door says "Tax
                          first," and stays shut; nobody moves
  playtest_dragons.yml    D-57's three headless checks: a Fire Dragon stays in the roost; a Frost Dragon against the
                          starwell's sky slot stays in the map; a walking party is stopped by the ledge's lip
  playtest_exit.yml       out through the mouth to X7, the landing measured
  playtest_hostility.yml  the quiet arrival (10 s, no harm), the four rows hostile, after a reload too
Usage: gen_tests.py (after a build has written L4/ids.lock.yml)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path

import yaml

L4 = Path(_REPO_ROOT + '/devdocs/xeen/briefs/xd18/L4')
lock = yaml.safe_load((L4 / 'ids.lock.yml').read_text())
E = lock['events']
D = lock['doors']
# Actor index: the build orders the scene's actors by their objects.yml id (checked in the built scene, 2026-11-21).
_ids = sorted(m['id'] for m in yaml.safe_load((L4 / 'objects.yml').read_text())['monsters'])
IDX = {m: i for i, m in enumerate(_ids)}
ACID, FIRE, FROST, KING = 11641, 11642, 11643, 11645
X7_ARRIVAL = (-4096, 16896)


def head(tid, title, comment, gold=0, immortal=True, level=62):
    lines = [f'# {line}' for line in comment.strip().splitlines()]
    lines += [f'id: {tid}', 'title: ' + yaml.safe_dump(title, default_style='"', width=10000).strip(), 'world: xeen',
              'mode: faithful', 'steps:',
              '  - new_game_flow:', '      start_map: xeen_xd18.blv', '      party:', f'        gold: {gold}',
              '        food: 20', '        members:',
              f'          - {{name: Brokk, class: Knight, level: {level}, skills: [], equipment: {{}}}}',
              f'          - {{name: Hild, class: Cleric, level: {level}, skills: [], equipment: {{}}}}',
              f'          - {{name: Ivar, class: Archer, level: {level}, skills: [], equipment: {{}}}}',
              f'          - {{name: Sefa, class: Sorcerer, level: {level}, skills: [], equipment: {{}}}}',
              '  - assert: {map: xeen_xd18.blv}']
    if immortal:
        lines.append('  - setup_shortcut: {kind: immortal, value: true}')
    return lines


def walk(x, y, z, r=64, clear=1500, t=40, ztol=None, close=True, plan=None):
    zt = f', z_tolerance: {ztol}' if ztol else ''
    cl = f', clear_hostiles: {clear}' if clear else ''
    pl = f', plan: {"true" if plan else "false"}' if plan is not None else ''
    return (f'  - walk_to: {{x: {x}, y: {y}, z: {z}, radius: {r}{zt}{cl}{pl}, timeout_seconds: {t}, '
            f'close_dialogs: {"true" if close else "false"}}}')


def lua(src):
    return '  - play_lua: {source: ' + yaml.safe_dump(src, default_style='"', width=10000).strip() + '}'


def dialog(text):
    return '  - assert: {dialog: {active: true, text_contains: ' + yaml.safe_dump(text, default_style='"').strip() + '}}'


def write(name, lines):
    (L4 / name).write_text('\n'.join(lines) + '\n')


def click_status(event, text):
    """F13: the line goes to the status line."""
    return [lua(f"click({E[event]}); wait(0.7)"),
            "  - play_lua:\n      source: |\n        local s = tostring(status())\n"
            f"        if not string.find(s, [[{text}]], 1, true) then error(\"status line: \" .. s) end",
            lua('close(); wait(0.3)')]


def click_dialog(event, text):
    return [lua(f"click({E[event]}); wait(0.7)"), dialog(text), lua('close(); wait(0.3)')]


# ------------------------------------------------------------------------------------------------ the critical path
P = head('xeen.xd18.l4.walk', 'Dragon Cave (XD-18 L4), the tax paid, the inner door, Dragon Lore and the Dragon King', """
Playtest of the Dragon Cave (XD-18, L4; lane A7, agent:xeen-a7-xd18; written by output/studio_cal/xd18/tools/
gen_tests.py from ids.lock.yml): the critical path (D-57 Q2). A level-62 party (immortal) with 2,000 gold and 20
gems arrives in the mouth (entrance:x7_mouth): the arrival line; the way out's window (cancelled); the urn before the
tax (A3's q-c25.urn); the waiting room's lectern (volume 1); Scaldrith's door (house 4852): 'The tax' (2,000 gold and
20 gems, tax_paid 112500); the urn after it ("The urn is empty and powerless.", aaze0050:1); the inner door opens in
the same visit (118100); the scorched passage, the bone hall, the road onto the ledge, the fire crossing, the stair
head, the walked stair down to the stair foot, the great roost, the ember gallery, the library's east leaves; shelves
2-4, the ledger refused ('Read the Lore first'), shelf 5 by the King's door, the ledger read (taxation 112506); the
King's door, the Dragon King killed: the grate rises in the same visit (118101) and the hoard is entered; every window
closed, a save and load: the inner door and the grate still open.""", gold=2000)
P += [
    '  - assert: {party_position: {x: 384, y: -3072, radius: 96, z_min: -8, z_max: 8}}',
    lua("wait(2); local s = tostring(status()); log('arrive: ' .. s); if not string.find(s, 'Sulphur and old smoke', 1, true) then error('arrival line: ' .. s) end; close()"),
    '  - grant_item: {item_id: 177, count: 20, member_index: 0}',
    lua("if held() ~= 0 then stow() end; log('party: ' .. party())"),
    walk(140, -3072, 0, r=48),
    lua(f"click({E['evt:exit']}); wait(0.5)"),
    dialog('Do you wish to leave'),
    lua('close()'),
    '  - assert: {map: xeen_xd18.blv}',
    walk(1536, -3460, 0, r=48),
] + click_dialog('evt:urn', 'looks hungry') + [
    walk(1920, -2600, 0, r=48),
    lua(f"open_door({E['evt:door_waiting']}, {D['door:waiting']})"),
    walk(1920, -1900, 0, r=48),
] + click_status('evt:volume1', 'Worms') + [
    lua("if not qbit(112501) then error('volume1 112501 not set') end"),
    walk(1920, -2700, 0, r=48),
    walk(1984, -3560, 0, r=48),
    lua(f"click({E['evt:office']}); wait(0.8)"),
    '  - assert: {dialog: {active: true, source_id: 5702}}',
    '  - select_topic: {action_id: 43751, match_label: "Quest"}',
    dialog('Dragon tax!'),
    lua("close(); wait(0.3); close(); wait(0.3); close(); if not qbit(112500) then error('tax_paid 112500 not set') end; if gold() ~= 0 then error('gold after the tax: ' .. gold()) end; log('after the tax: ' .. party())"),
    walk(1536, -3460, 0, r=48),
] + click_dialog('evt:urn', 'empty and powerless') + [
    walk(2560, -3072, 0, r=48),
    lua(f"click({E['evt:inner_door']}); wait(2); close(); if door_state({D['door:inner']}) ~= 'open' then error('the inner door is not open in the same visit: ' .. door_state({D['door:inner']})) end; if not qbit(118100) then error('inner_door_open 118100 not set') end"),
    '  - assert: {map: xeen_xd18.blv}',
    walk(3300, -3072, 0),
    walk(4400, -3072, 0, clear=3000),
    '  - clear_hostiles: {radius: 3500}',
    walk(5568, -2500, 0, clear=3000),
    walk(5568, -2000, 0, r=48, ztol=24, clear=3000),
    walk(7900, -1990, 0, r=48, ztol=24, clear=3000, t=60),
    walk(8560, -1984, 0, r=48, ztol=24, clear=3000),
    walk(9000, -1700, 0, clear=3000),
    walk(9950, -1984, 0, r=48, clear=3000),
    walk(10048, -1800, 0, r=48),
    walk(10048, 900, -1024, r=64, ztol=40, t=60),
    walk(8576, 900, -1024, r=64, ztol=40),
    walk(8576, 0, -1024, r=64, ztol=40),
    '  - clear_hostiles: {radius: 4500}',
    walk(8000, 0, -1024, r=64, ztol=40, clear=4000),
    walk(5400, -384, -1024, r=64, ztol=40, clear=4000, t=60),
    walk(3300, -384, -1024, r=64, ztol=40, clear=3000),
    lua(f"open_door({E['evt:door_library_e']}, {D['door:library_e']})"),
    walk(2600, -384, -1024, r=64, ztol=40, clear=2500),
    '  - clear_hostiles: {radius: 3000}',
    lua("local s = tostring(status()); log('library: ' .. s)"),
    walk(1408, -900, -1024, r=48, ztol=40),
] + click_status('evt:volume2', 'Lizards') + [
    walk(1920, -900, -1024, r=48, ztol=40),
] + click_status('evt:volume3', 'Serpents') + [
    walk(2432, -900, -1024, r=48, ztol=40),
] + click_status('evt:volume4', 'Drakes') + [
    walk(1300, 0, -1024, r=48, ztol=40),
] + click_dialog('evt:taxation', 'Read the Lore first') + [
    lua("if qbit(112506) then error('taxation set before volume 5') end"),
    walk(700, -256, -1024, r=48, ztol=40),
    walk(192, -150, -1024, r=48, ztol=40),
] + click_status('evt:volume5', 'There is only one') + [
    walk(1300, 0, -1024, r=48, ztol=40),
] + click_status('evt:taxation', 'by Scaldrith') + [
    lua("for _, q in ipairs({112501, 112502, 112503, 112504, 112505, 112506}) do if not qbit(q) then error('lore qbit ' .. q .. ' not set') end end"),
    walk(0, -256, -1024, r=48, ztol=40),
    lua(f"open_door({E['evt:door_king']}, {D['door:king']})"),
    walk(-800, -256, -1024, r=64, ztol=40, clear=0),
    f'  - assert: {{actor_visible: {{actor_index: {IDX["monster:king"]}, name: Dragon King, dead: false, report_state: true}}}}',
    lua(f"if door_state({D['door:grate']}) ~= 'closed' then error('the grate before the King: ' .. door_state({D['door:grate']})) end"),
    '  - clear_hostiles: {radius: 4000}',
    lua(f"wait(4); local s = tostring(status()); log('king: ' .. s); if not qbit(118101) then error('king_slain 118101 not set') end; for _ = 1, 20 do if door_state({D['door:grate']}) == 'open' then break end; wait(0.5) end; if door_state({D['door:grate']}) ~= 'open' then error('the grate is not up in the same visit: ' .. door_state({D['door:grate']})) end"),
    walk(-2000, -128, -1024, r=96, ztol=160),
    walk(-3000, -128, -992, r=64, ztol=160),
    walk(-3700, -128, -1024, r=64, ztol=140),
    lua(f"click({E['evt:chest_hoard']}); wait(0.5); close(); close()"),
    walk(-2000, -128, -1024, r=96, ztol=160),
    lua('close(); close()'),
    '  - reload: {}',
    lua(f"wait(2); close(); if door_state({D['door:inner']}) ~= 'open' then error('the inner door after reload: ' .. door_state({D['door:inner']})) end; if door_state({D['door:grate']}) ~= 'open' then error('the grate after reload: ' .. door_state({D['door:grate']})) end"),
]
write('playtest.yml', P)

# ------------------------------------------------------------------------------------------------ the tax refused
T = head('xeen.xd18.l4.tax', "Dragon Cave (XD-18 L4), no tax: the inner door opens, the Dragon King's door refuses", f"""
D-89 (2026-11-22): a level-62 party with no gold or gems clicks the inner door from the tax hall: it opens (A3's
q-c25.inner_door, 118100) and nobody is moved. Put in the King's antechamber, the party clicks the Dragon King's door:
A3's q-c25.king_door says "Tax first," on the status line, the leaves stay shut and the party stays in the map.""")
T += [
    lua('wait(2); close()'),
    walk(2560, -3072, 0, r=48),
    lua(f"click({E['evt:inner_door']}); wait(2); close(); if door_state({D['door:inner']}) ~= 'open' then error('the inner door did not open without the tax: ' .. door_state({D['door:inner']})) end; if not qbit(118100) then error('118100 not set') end"),
    '  - assert: {map: xeen_xd18.blv}',
    '  - set_pose: {map: xeen_xd18.blv, x: 128, y: -256, z: -1024, yaw: 3.1416, pitch: 0.0}',
    '  - advance_runtime: {seconds: 1.0}',
    lua(f"click({E['evt:door_king']}); wait(0.5); local s = tostring(status()); log('refused: ' .. s); if not string.find(s, 'Tax first', 1, true) then error('fail line: ' .. s) end"),
    '  - advance_runtime: {seconds: 2.0, follow_map_move: true}',
    '  - assert: {map: xeen_xd18.blv}',
    lua(f"if door_state({D['door:king']}) ~= 'closed' then error('the King door opened without the tax: ' .. door_state({D['door:king']})) end; if qbit(112500) then error('tax_paid set') end"),
]
write('playtest_tax.yml', T)

# ------------------------------------------------------------------------------------------------ the three dragon checks
ROOST_FIRE = [IDX[f'monster:roost_{i}'] for i in range(1, 5)]
SPAWNED = len(_ids)    # the Frost Dragon the check summons next to the slot
C = head('xeen.xd18.l4.dragons', "Dragon Cave (XD-18 L4), D-57's three checks: the roost, the starwell's slot, the ledge's lip", f"""
D-57 (XD-18 APPROVAL, RELAYS A7) and D-32. (1) The great roost's four Fire Dragons (actors {ROOST_FIRE}) see the
party (immortal) at the stair foot's opening for 60 s: they stay in the roost and its dragon roads; no Fire Dragon is
in the stair foot (those that come press against the roost's east wall at its low opening), more than their own in the pools, the old roost or the fire crossing, or in the library. (2) The
party stands under the starwell's slot of stars (sky: true over the void, X7's preset); a Frost Dragon summoned
pressed into the slot (y 2,620, z -100, 60 off the wall, its feet at the slot's middle) (actor {SPAWNED}) and the starwell's three stay in the map for 40 s: every one is south of the north
wall (y under 2,688), none lost. (3) On the roost ledge the party walks 3 s straight at the 128 lip: it stops at the
lip, still on the ledge at z 0 (192 if it steps over, as FD-03's parapet).""")
C += [
    lua('wait(2); close()'),
    '  # (1) the roost',
    '  - set_pose: {map: xeen_xd18.blv, x: 8576, y: 0, z: -1024, yaw: 3.1416, pitch: 0.0}',
    '  - advance_runtime: {seconds: 1}',
    f'  - assert: {{actor_count: {{monster_id: {FIRE}, near: [6656, -832, 1700], min: 4}}}}',
    '  - advance_runtime: {seconds: 30}',
    lua("log('roost after 30 s: ' .. tostring(status()))"),
    '  - advance_runtime: {seconds: 30}',
] + [f'  - assert: {{actor_visible: {{actor_index: {i}, dead: false, report_state: true}}}}' for i in ROOST_FIRE] + [
    f'  - assert: {{actor_count: {{monster_id: {FIRE}, near: [8600, 0, 300], max: 0}}}}',
    f'  - assert: {{actor_count: {{monster_id: {FIRE}, near: [8576, 800, 280], max: 0}}}}',
    f'  - assert: {{actor_count: {{monster_id: {FIRE}, near: [9600, 900, 250], max: 0}}}}',
    f'  - assert: {{actor_count: {{monster_id: {FIRE}, near: [9472, 1792, 1000], max: 3}}}}',
    f'  - assert: {{actor_count: {{monster_id: {FIRE}, near: [7296, 1408, 850], max: 3}}}}',
    f'  - assert: {{actor_count: {{monster_id: {FIRE}, near: [8960, -1728, 600], max: 2}}}}',
    f'  - assert: {{actor_count: {{monster_id: {FIRE}, near: [1920, -384, 1000], max: 0}}}}',
    f'  - assert: {{actor_count: {{monster_id: {FIRE}, near: [1900, -3000, 900], max: 0}}}}',
] + [f'  - assert: {{actor_visible: {{actor_index: {i}, near: {{x: 5568, y: -800, max_distance: 3200}}}}}}'
     for i in ROOST_FIRE] + [
    '  # west of the roost\'s east wall (x 8,192): a circle centred far west whose edge runs along the wall',
] + [f'  - assert: {{actor_visible: {{actor_index: {i}, near: {{x: -40000, y: -832, max_distance: 48192}}}}}}'
     for i in ROOST_FIRE] + [
    '  # (2) the starwell slot',
    '  - set_pose: {map: xeen_xd18.blv, x: 4736, y: 2500, z: -1024, yaw: 1.5708, pitch: 0.4}',
    '  - advance_runtime: {seconds: 0.5}',
    f'  - spawn_actor: {{monster_id: {FROST}, count: 1, x: 4736, y: 2620, z: -100}}',
    '  - advance_runtime: {seconds: 0.5}',
    f'  - assert: {{actor_visible: {{actor_index: {SPAWNED}, dead: false, report_state: true}}}}',
    '  - advance_runtime: {seconds: 20}',
    f'  - assert: {{actor_visible: {{actor_index: {SPAWNED}, dead: false, report_state: true}}}}',
    '  - advance_runtime: {seconds: 20}',
    f'  - assert: {{actor_visible: {{actor_index: {SPAWNED}, dead: false, report_state: true, near: {{x: 4736, y: -20000, max_distance: 22688}}}}}}',
] + [f'  - assert: {{actor_visible: {{actor_index: {IDX[f"monster:starwell_{i}"]}, dead: false, report_state: true, near: {{x: 4736, y: -20000, max_distance: 22688}}}}}}'
     for i in (1, 2, 3)] + [
    f'  - assert: {{actor_count: {{monster_id: {FROST}, min: 15, max: 15}}}}',
    f'  - assert: {{actor_count: {{monster_id: {FROST}, near: [4736, 1664, 2000], min: 4}}}}',
    '  # (3) the ledge lip',
    '  - clear_hostiles: {radius: 20000}',
    '  - set_pose: {map: xeen_xd18.blv, x: 6656, y: -2080, z: 0, yaw: 1.5708, pitch: 0.0}',
    '  - advance_runtime: {seconds: 0.5}',
    '  - assert: {party_position: {x: 6656, y: -2080, radius: 48, z_min: -8, z_max: 8}}',
    '  - movement_segment:',
    '      input: forward',
    '      seconds: 3',
    '      start: {map: xeen_xd18.blv, x: 6656, y: -2080, z: 0, yaw_degrees: 90, pitch: 0}',
    '      expect_stop: {map: xeen_xd18.blv, x: 6656, y: -1880, z: 0, yaw_degrees: 90, pitch: 0}',
    '      loose_tolerance: true',
    '      tolerance_xy: 120',
    '      tolerance_z: 24',
    '  - advance_runtime: {seconds: 1}',
    lua("log('at the lip: ' .. tostring(status()))"),
    '  - assert: {party_position: {x: 6656, y: -1950, radius: 160, z_min: -8, z_max: 8}}',
]
write('playtest_dragons.yml', C)

# ------------------------------------------------------------------------------------------------ the exit
X = head('xeen.xd18.l4.exit', 'Dragon Cave (XD-18 L4), out through the mouth to X7', f"""
The way out (the exit preset, D-24): from the mouth's daylight to X7's entrance:xd18_mouth {X7_ARRIVAL} facing south
(A5's named arrival); the leave window's OK pressed; the landing measured (status) and still there 6 s later.""")
X += [
    lua('wait(2); close()'),
    walk(140, -3072, 0, r=48),
    f"  - execute_event: {{id: {E['evt:exit']}}}",
    dialog('Do you wish to leave'),
    '  - select_topic: {match_label: "OK"}',
    '  - advance_runtime: {seconds: 1.5, follow_map_move: true}',
    '  - assert: {map: xeen_x7.odm}',
    lua("log('landing: ' .. status())"),
    '  - clear_hostiles: {radius: 6000}',
    '  - advance_runtime: {seconds: 6.0}',
    lua("log('landing after 6 s: ' .. status())"),
    f'  - assert: {{party_position: {{x: {X7_ARRIVAL[0]}, y: {X7_ARRIVAL[1]}, radius: 160, z_min: 2000}}}}',
]
write('playtest_exit.yml', X)

# ------------------------------------------------------------------------------------------------ hostility
H = head('xeen.xd18.l4.hostility', 'Dragon Cave (XD-18 L4): a quiet arrival; the dragons and the King hostile', """
D-11.3: the party (level 62, not immortal) stands 10 s at the arrival in the mouth and nobody is hurt (party() the
same before and after). A2's rows: Acid Dragon 11641 (9), Fire Dragon 11642 (17), Frost Dragon 11643 (14) and the
Dragon King 11645 (1) all hostile at load and after a save and load. No window is open before the reload.""",
         immortal=False)
H += [
    lua("wait(0.5); close(); remember('hp', party()); log('start: ' .. party())"),
    '  - advance_runtime: {seconds: 10}',
    lua("close(); local a = recall('hp'); local b = party(); log('after 10 s: ' .. b); if a ~= b then error('hurt at the arrival: ' .. a .. ' -> ' .. b) end"),
    '  - assert: {party_position: {x: 384, y: -3072, radius: 96, z_min: -8, z_max: 8}}',
    '  - setup_shortcut: {kind: immortal, value: true}',
] + [f'  - assert: {{actor_count: {{monster_id: {m}, hostile: false, max: 0}}}}' for m in (ACID, FIRE, FROST, KING)] + [
    f'  - assert: {{actor_count: {{monster_id: {m}, hostile: true, min: {n}}}}}'
    for m, n in ((ACID, 9), (FIRE, 17), (FROST, 14), (KING, 1))] + [
    '  - reload: {}',
    lua('wait(1); close()'),
] + [f'  - assert: {{actor_count: {{monster_id: {m}, hostile: false, max: 0}}}}' for m in (ACID, FIRE, FROST, KING)] + [
    f'  - assert: {{actor_count: {{monster_id: {m}, hostile: true, min: {n}}}}}'
    for m, n in ((ACID, 9), (FIRE, 17), (FROST, 14), (KING, 1))]
write('playtest_hostility.yml', H)
print('written 5 playtests')
