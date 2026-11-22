#!/usr/bin/env python3
"""FD-03 Darkstone Tower: writes the L4 playtests from ids.lock.yml (event and door numbers) and the scene's actor
order. Rerun after gen.py and a build (cycle.sh) whenever an id may have moved.

  playtest.yml            the critical path: the three storeys' gongs (guards shown, slabs up), L1's plaques with
                          the fourth read's summary, the Onyx Golem and the vault, L4's heads (autonote), the seal
                          without and with the Chime, the roof stair to the hatch (No), a reload keeping it all
  playtest_fall.yml       off an unraised top step onto the dais and out (L1), then the gong and the climb; the same at
                          L3 after one twin gong (the riser's half height), then the second gong and the climb
  playtest_exit.yml       the way out to X5 (the leave window's OK), the landing measured
  playtest_roof.yml       the hatch's own Yes/No (D-66): No stays, Yes up to P5's entrance:fd03_roof, measured
  playtest_hostility.yml  a quiet arrival; every golem hostile; no fights among them
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
L4 = R / 'devdocs/xeen/briefs/fd03/L4'
SCENE = R / 'output/studio_cal/fd03/root/worlds/xeen/maps/xeen_fd03.scene.yml'
ids = yaml.safe_load((L4 / 'ids.lock.yml').read_text())
E, D = ids['events'], ids['doors']
scene = yaml.safe_load(SCENE.read_text())
actors = scene['initial_state']['actors']
HIDDEN = [a['actor_index'] for a in actors if a['attributes'] & 0x10000]
ONYX = [a['actor_index'] for a in actors if a['monster_info_id'] == 11584][0]
# The hidden guards in actor order (sorted by monster id): L1 group 21, L2 22, L3 31 (west), 32 (east).
G1, G2, G3W, G3E = HIDDEN[0:2], HIDDEN[2:4], HIDDEN[4:6], HIDDEN[6:8]
assert len(HIDDEN) == 8, HIDDEN


def party(level=61):
    return {'gold': 0, 'food': 20, 'members': [
        {'name': n, 'class': c, 'level': level, 'skills': [], 'equipment': {}}
        for n, c in (('Brokk', 'Knight'), ('Hild', 'Cleric'), ('Ivar', 'Archer'), ('Sefa', 'Sorcerer'))]}


def start():
    return [{'new_game_flow': {'start_map': 'xeen_fd03.blv', 'party': party()}},
            {'assert': {'map': 'xeen_fd03.blv'}}]


def walk(x, y, z, r=64, t=60, clear=1500, ztol=None):
    w = {'x': x, 'y': y, 'z': z, 'radius': r, 'timeout_seconds': t, 'close_dialogs': True}
    if clear:
        w['clear_hostiles'] = clear
    if ztol is not None:
        w['z_tolerance'] = ztol
    return {'walk_to': w}


def lua(src):
    return {'play_lua': {'source': src}}


def vis(idx, hidden):
    return [{'assert': {'actor_visible': {'actor_index': i, 'hidden': hidden}}} for i in idx]


def gong_check(event, qbit, door, guards, seconds=6):
    return [lua(f"click({E[event]}); wait(0.5); local s = tostring(status()); log('{event}: ' .. s); "
                f"if not string.find(s, 'No Sound No Ground', 1, true) then error('no voice: ' .. s) end"),
            lua(f"wait({seconds}); if not qbit({qbit}) then error('{qbit} not set') end; "
                f"if door_state({D[door]}) ~= 'open' then error('{door} not up: ' .. door_state({D[door]})) end"),
            ] + vis(guards, False)


def dialog(text):
    return [{'advance_runtime': {'seconds': 0.5, 'present_dialogs': True}},
            {'assert': {'dialog': {'active': True, 'text_contains': text}}}]


def write(name, doc, header):
    text = header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
    (L4 / name).write_text(text)


# ------------------------------------------------------------------------------------------------ playtest.yml
steps = start() + [
    {'setup_shortcut': {'kind': 'immortal', 'value': True}},
    {'assert': {'party_position': {'x': 0, 'y': 1792, 'radius': 96, 'z_min': -8, 'z_max': 8}}},
    lua("wait(2); local s = tostring(status()); log('arrive: ' .. s); "
        "if not string.find(s, 'Darkstone Tower', 1, true) then error('arrival line: ' .. s) end; close()"),
    # The way out asks (playtest_exit.yml leaves by it); here it is cancelled.
    lua(f"click({E['evt:way_out']}); wait(0.5)"),
    {'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}},
    lua("close()"),
    {'assert': {'map': 'xeen_fd03.blv'}},
    # The guards are hidden before their gongs.
] + vis(HIDDEN, True) + vis([ONYX], False) + [
    # The vault's force is up while the Onyx Golem lives (the walk's clears reach through the floors later on).
    lua(f"click({E['evt:force']}); wait(0.5); local s = tostring(status()); log('force: ' .. s); "
        "if not string.find(s, 'A force repels you', 1, true) then error('force line: ' .. s) end; "
        f"if door_state({D['door:force']}) ~= 'closed' then error('the force is down before the Onyx Golem') end; "
        "if qbit(118124) then error('118124 set at the start') end"),
    # The inner gate, the west arc, L1's four plaques (the fourth adds the columns read down).
    walk(-272, 1620, 0, clear=0),
    lua(f"open_door({E['evt:door_inner_gate']}, {D['door:inner_gate']})"),
    walk(-272, 1320, 0),
    walk(-1264, 0, 0),
]
for i in range(1, 4):
    steps += [lua(f"click({E[f'evt:plaque1_{i}']}); wait(0.5)"),
              {'assert': {'dialog': {'active': True, 'text_contains': 'A plaque reads:'}}}, lua("close(); wait(0.3)")]
steps += [
    lua(f"click({E['evt:plaque1_4']}); wait(0.5); local s = tostring(status()); log('fourth plaque: ' .. s); "
        "if not string.find(s, 'A plaque reads: -LHSURAGGAMC', 1, true) then error('fourth row: ' .. s) end"),
    {'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}},
    {'assert': {'dialog': {'active': True, 'text_contains': 'NEW WORLD THANKS YOU FOR PLAYING MIGHT AND MAGIC'}}},
    lua("close(); wait(0.3)"),
    # The L1 rotunda: the gong.
    walk(-700, 0, 0),
] + gong_check('evt:gong1', 118120, 'mover:slab1', G1) + [
    {'clear_hostiles': {'radius': 3000}},
    lua(f"click({E['evt:gong1']}); wait(0.5); log('second ring: ' .. tostring(status()))"),
    # South: the passage, the stairwell, the flight, the slab, L2's landing.
    walk(0, -700, 0), walk(0, -1250, 0), walk(-336, -1640, 0),
    walk(-920, -1888, 0, ztol=24, clear=0), walk(-50, -1888, 768, ztol=24, t=90),
    walk(272, -1700, 768, ztol=24), walk(272, -1300, 768, ztol=24),
    # L2: the west arc, the rotunda, the gong.
    walk(-760, -1100, 768), walk(-560, -560, 768),
] + gong_check('evt:gong2', 118121, 'mover:slab2', G2) + [
    {'clear_hostiles': {'radius': 3000}},
    walk(0, 700, 768), walk(0, 1250, 768), walk(336, 1640, 768),
    walk(920, 1888, 768, ztol=24, clear=0), walk(50, 1888, 1536, ztol=24, t=90),
    walk(-272, 1700, 1536, ztol=24), walk(-272, 1300, 1536, ztol=24),
    # L3: the twin gongs; one raises the riser only, both the slab.
    walk(-760, 1100, 1536), walk(-560, 560, 1536),
] + gong_check('evt:gong3w', 118122, 'mover:riser3', G3W, seconds=4) + [
    lua(f"if door_state({D['mover:slab3']}) ~= 'closed' then error('slab3 moved after one gong') end"),
] + gong_check('evt:gong3e', 118123, 'mover:slab3', G3E, seconds=8) + [
    {'clear_hostiles': {'radius': 3000}},
    walk(0, -700, 1536), walk(0, -1250, 1536), walk(-336, -1640, 1536),
    walk(-920, -1888, 1536, ztol=24, clear=0), walk(-50, -1888, 2304, ztol=24, t=90),
    walk(272, -1700, 2304, ztol=24), walk(272, -1300, 2304, ztol=24),
    # L4: the west arc, the skull hall's doors, the Onyx Golem and the vault's force.
    walk(-760, -1100, 2304, clear=900), walk(-1250, 0, 2304, clear=900),
    lua(f"open_door({E['evt:door_skull']}, {D['door:skull_pair']})"),
    walk(-700, 0, 2304, clear=0),
    lua(f"click({E['evt:skull']}); wait(0.5); local s = tostring(status()); log('skull: ' .. s); "
        "if not string.find(s, 'The skull is silent', 1, true) then error('skull line: ' .. s) end"),
    {'clear_hostiles': {'radius': 4000}},
    lua(f"wait(4); if not qbit(118124) then error('vault_open 118124 not set by the Onyx Golem') end; "
        f"if door_state({D['door:force']}) ~= 'open' then error('force not down: ' .. door_state({D['door:force']})) end"),
    walk(-560, 560, 2304), walk(-950, 900, 2304),
    lua(f"loot_chest({E['evt:chest_vault']})"),
    # L4's heads: the fourth writes the summary (autonote 4720, A3's m41.plaques_l4).
]
HEAD_ROWS = {1: 'Head 13 speaks: T-MEOE-FENN-TEAO', 2: 'Head 14 speaks: Y"PRNV4--G-DHE-N',
             3: 'Head 15 speaks: PCU"-E-TDEOE--S!'}   # dark/aazex116:3-5 verbatim (D-63 9)
for i in range(1, 4):
    steps += [lua(f"click({E[f'evt:head_{i}']}); wait(0.5)"),
              {'assert': {'dialog': {'active': True, 'text_contains': HEAD_ROWS[i]}}}, lua("close(); wait(0.3)")]
steps += [
    lua(f"click({E['evt:head_4']}); wait(0.5); local s = tostring(status()); log('fourth head: ' .. s); "
        "if not string.find(s, 'Head 16 speaks: EOT-LLOHUOFASYO-', 1, true) then error('fourth head: ' .. s) end"),
    {'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}},
    {'assert': {'dialog': {'active': True, 'text_contains': 'TYPE "COMPUTER"'}}},
    lua("close(); wait(0.3)"),
    # The seal: without the Chime, then with it.
    walk(-560, 560, 2304), walk(0, 700, 2304), walk(0, 1250, 2304),
    lua(f"click({E['evt:seal']}); wait(0.5)"),
    # The refusal stays a window (m41.seal has no fail_status: a door's refusal, not a find; s27).
    {'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}},
    {'assert': {'dialog': {'active': True, 'text_contains': 'An invisible seal prevents passage'}}},
    lua(f"close(); wait(0.3); if door_state({D['door:seal']}) ~= 'closed' then error('seal opened without the Chime') end"),
    {'grant_item': {'item_id': 12373}},
    lua(f"click({E['evt:seal']}); wait(0.5)"),
    lua("local s = tostring(status()); if not string.find(s, 'The seal has been broken', 1, true) then error('status line: ' .. s) end"),
    lua(f"close(); wait(5); if not qbit(111820) then error('seal_broken not set') end; "
        f"if has_item(12373) then error('the Chime was not taken') end; "
        f"if door_state({D['door:seal']}) ~= 'open' then error('seal not open: ' .. door_state({D['door:seal']})) end"),
    # The roof stair to the head and the hatch's Yes/No.
    walk(0, 1620, 2304), walk(-640, 1640, 2304), walk(-650, 1904, 2304, ztol=24, clear=0),
    walk(200, 1904, 3072, ztol=24, t=90),
    # The hatch asks its own Yes/No (D-66); No stays (playtest_roof.yml climbs).
    lua(f"click({E['evt:hatch']}); wait(0.5)")] + [{'advance_runtime': {'seconds': 0.5, 'present_dialogs': True}},
     {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}] + [
    lua('close()'),
    {'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}},
    {'assert': {'map': 'xeen_fd03.blv'}},
    # A save and load with every window closed: the slabs, the force and the seal stay open.
    lua("close(); wait(1); close()"),
    {'reload': {}},
    lua("wait(8); close()\n"
        + ''.join(f"if door_state({D[d]}) ~= 'open' then error('{d} after reload: ' .. door_state({D[d]})) end\n"
                  for d in ('mover:slab1', 'mover:slab2', 'mover:riser3', 'mover:slab3', 'door:force', 'door:seal'))),
]
write('playtest.yml', {'id': 'xeen.fd03.l4.walk', 'title': 'Darkstone Tower (FD-03 L4), the gongs, the plaques, the '
                       'Onyx Golem, the seal and the roof stair', 'world': 'xeen', 'mode': 'faithful', 'steps': steps},
      "# Playtest of Darkstone Tower (FD-03, L4; lane A7, written by output/studio_cal/fd03/tools/gen_tests.py from\n"
      "# ids.lock.yml): the critical path of D-57 (every gong with its guards and slab, the plaques with one storey's\n"
      "# fourth read, the Onyx Golem, the vault opening, the seal with the Chime, the roof stair to the hatch (No),\n"
      "# and a reload that keeps the slabs and the seal). A level-61 party, immortal.\n")

# ------------------------------------------------------------------------------------------------ playtest_fall.yml
steps = start() + [
    {'setup_shortcut': {'kind': 'immortal', 'value': True}},
    lua("wait(2); close()"),
    {'console': {'line': 'tp -336 -1640 0'}},
    {'advance_runtime': {'seconds': 1.0}},
    lua("close(); wait(0.3); close()"),
    # Up the flight to the unraised top step: the plate gives the voice.
    walk(-920, -1888, 0, ztol=24, clear=0), walk(-50, -1888, 768, ztol=24, t=90, clear=0),
    lua("wait(0.5); local s = tostring(status()); log('top step: ' .. s); "
        "if not string.find(s, 'No Sound No Ground', 1, true) then error('no voice at the top step: ' .. s) end"),
    lua(f"if door_state({D['mover:slab1']}) ~= 'closed' then error('slab1 is up') end"),
    # Off the edge: onto the dais 128 high.
    {'walk_to': {'x': 272, 'y': -1888, 'z': 128, 'z_tolerance': 40, 'radius': 64, 'timeout_seconds': 30,
                 'close_dialogs': True}},
    {'advance_runtime': {'seconds': 1.5}},
    lua("log('on the dais: ' .. tostring(status()) .. ' ' .. party())"),
    {'assert': {'party_position': {'x': 272, 'y': -1760, 'radius': 300, 'z_min': 100, 'z_max': 160}}},
    # Off the dais and out of the stairwell.
    walk(-336, -1640, 0, ztol=24, clear=0), walk(0, -1250, 0, clear=0), walk(0, -700, 0, clear=0),
    {'assert': {'party_position': {'x': 0, 'y': -700, 'radius': 96, 'z_min': -8, 'z_max': 8}}},
    # The gong, and the climb.
    walk(-700, 0, 0, clear=1500),
] + gong_check('evt:gong1', 118120, 'mover:slab1', G1) + [
    {'clear_hostiles': {'radius': 3000}},
    walk(0, -1250, 0), walk(-336, -1640, 0),
    walk(-920, -1888, 0, ztol=24, clear=0), walk(-50, -1888, 768, ztol=24, t=90), walk(272, -1700, 768, ztol=24), walk(272, -1300, 768, ztol=24),
    {'assert': {'party_position': {'x': 272, 'y': -1300, 'radius': 96, 'z_min': 760, 'z_max': 776}}},
    # L3 after one twin gong: the riser stands at half height (448 over the floor).
    {'console': {'line': 'tp -560 560 1536'}},
    {'advance_runtime': {'seconds': 1.0}},
    lua("close(); wait(0.3); close()"),
] + gong_check('evt:gong3w', 118122, 'mover:riser3', G3W, seconds=4) + [
    {'clear_hostiles': {'radius': 3000}},
    {'console': {'line': 'tp -336 -1640 1536'}},
    {'advance_runtime': {'seconds': 1.0}},
    lua("close(); wait(0.3); close()"),
    walk(-920, -1888, 1536, ztol=24, clear=0), walk(-50, -1888, 2304, ztol=24, t=90, clear=0),
    {'walk_to': {'x': 272, 'y': -1888, 'z': 1984, 'z_tolerance': 40, 'radius': 64, 'timeout_seconds': 30,
                 'close_dialogs': True}},
    {'advance_runtime': {'seconds': 1.5}},
    lua("log('on the riser: ' .. tostring(status()) .. ' ' .. party())"),
    {'assert': {'party_position': {'x': 272, 'y': -1760, 'radius': 300, 'z_min': 1960, 'z_max': 2000}}},
    walk(-336, -1640, 1536, ztol=24, clear=0), walk(0, -1250, 1536, clear=0),
    {'assert': {'party_position': {'x': 0, 'y': -1250, 'radius': 96, 'z_min': 1528, 'z_max': 1544}}},
    # The second gong: the slab up through the riser, and the climb to L4.
    lua(f"click({E['evt:gong3e']}); wait(9); if door_state({D['mover:slab3']}) ~= 'open' then "
        f"error('slab3 not up: ' .. door_state({D['mover:slab3']})) end"),
    {'clear_hostiles': {'radius': 4000}},
    walk(-336, -1640, 1536), walk(-920, -1888, 1536, ztol=24, clear=0), walk(-50, -1888, 2304, ztol=24, t=90), walk(272, -1700, 2304, ztol=24),
    walk(272, -1300, 2304, ztol=24),
    {'assert': {'party_position': {'x': 272, 'y': -1300, 'radius': 96, 'z_min': 2296, 'z_max': 2312}}},
]
write('playtest_fall.yml', {'id': 'xeen.fd03.l4.fall', 'title': 'Darkstone Tower (FD-03 L4), off an unraised top '
                            'step and out, then the gong and the climb (L1 and L3)', 'world': 'xeen',
                            'mode': 'faithful', 'steps': steps},
      "# Playtest of D-57 Q15 (FD-03, L4; written by output/studio_cal/fd03/tools/gen_tests.py): walk off an\n"
      "# unraised top step onto the dais, walk out of the stairwell, then ring the gong and climb; the same at L3 after\n"
      "# one twin gong (the riser at half height 448), then the second gong and the climb to L4. Never stuck.\n")

# ------------------------------------------------------------------------------------------------ playtest_exit.yml
steps = start() + [
    {'assert': {'party_position': {'x': 0, 'y': 1792, 'radius': 96, 'z_min': -8, 'z_max': 8}}},
    lua("wait(2); close()"),
    {'setup_shortcut': {'kind': 'immortal', 'value': True}},
    lua(f"click({E['evt:way_out']}); wait(0.5)"),
    {'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}},
    {'select_topic': {'match_label': 'OK'}},
    {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
    {'assert': {'map': 'xeen_x5.odm'}},
    lua("log('landing: ' .. status())"),
    {'clear_hostiles': {'radius': 6000}},
    {'advance_runtime': {'seconds': 4.0}},
    lua("log('landing after 4 s: ' .. status())"),
    {'assert': {'party_position': {'x': -4608, 'y': 2560, 'radius': 160, 'z_min': 1440, 'z_max': 1600}}},
]
write('playtest_exit.yml', {'id': 'xeen.fd03.l4.exit', 'title': 'Darkstone Tower (FD-03 L4), out to X5',
                            'world': 'xeen', 'mode': 'faithful', 'steps': steps},
      "# Playtest of Darkstone Tower's way out (FD-03, L4; written by output/studio_cal/fd03/tools/gen_tests.py): the\n"
      "# tower door (the exit preset, aazex113:0) through the leave window (OK) to X5's entrance:fd03_door point\n"
      "# (-4608, 2560, 1504) facing 512 (A6's corrected point); the landing measured (status). X5's door back in is A6's.\n")

# ------------------------------------------------------------------------------------------------ playtest_roof.yml
steps = start() + [
    lua("wait(2); close()"),
    {'setup_shortcut': {'kind': 'immortal', 'value': True}},
    {'setup_shortcut': {'kind': 'set_qbit', 'id': 111820, 'value': True}},
    {'reload': {}},
    lua("wait(8); close()"),
    {'console': {'line': 'tp 224 1904 3072'}},
    {'advance_runtime': {'seconds': 1.0}},
    lua("close(); wait(0.3); close()"),
    {'assert': {'party_position': {'x': 224, 'y': 1904, 'radius': 96, 'z_min': 3064, 'z_max': 3080}}},
    lua(f"click({E['evt:hatch']}); wait(0.5)")] + [{'advance_runtime': {'seconds': 0.5, 'present_dialogs': True}},
     {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}] + [
    lua('close()'),
    {'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}},
    lua("close(); wait(0.5); close()"),
    {'assert': {'map': 'xeen_fd03.blv'}},
    {'assert': {'party_position': {'x': 224, 'y': 1904, 'radius': 96, 'z_min': 3064, 'z_max': 3080}}},
    lua(f"click({E['evt:hatch']}); wait(0.5)")] + [{'advance_runtime': {'seconds': 0.5, 'present_dialogs': True}},
     {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}] + [
    {'select_topic': {'match_label': 'OK'}},
    {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
    {'assert': {'map': 'xeen_p5.blv'}},
    lua("log('landing: ' .. status())"),
    {'clear_hostiles': {'radius': 6000}},
    {'advance_runtime': {'seconds': 4.0}},
    {'assert': {'party_position': {'x': 4608, 'y': -3968, 'radius': 160, 'z_min': -60, 'z_max': 60,
                                   'facing': 512, 'facing_within': 40}}},
]
write('playtest_roof.yml', {'id': 'xeen.fd03.l4.roof', 'title': 'Darkstone Tower (FD-03 L4), the hatch up to P5',
                            'world': 'xeen', 'mode': 'faithful', 'steps': steps},
      "# Playtest of the roof hatch (FD-03, L4; written by output/studio_cal/fd03/tools/gen_tests.py): from the roof\n"
      "# stair's head (entrance:p5_stair, the seal broken) the hatch's own Yes/No (D-66, A3's m41.roof_exit question):\n"
      "# No stays, Yes moves at once to P5's entrance:fd03_roof (4608, -3968, 0) facing north; measured.\n")

# ------------------------------------------------------------------------------------------------ playtest_hostility.yml
steps = start() + [
    {'console': {'line': 'arena trace on'}},
    # Quiet arrival (D-11.3, D-57): nothing comes for the party while it stands at the door.
    {'advance_runtime': {'seconds': 10}},
    lua("close()"),
    {'assert': {'party_position': {'x': 0, 'y': 1792, 'radius': 96, 'z_min': -8, 'z_max': 8}}},
    {'assert': {'ai_trace': {'event': 'target', 'target': 'party', 'max_count': 0, 'report': True}}},
    {'setup_shortcut': {'kind': 'immortal', 'value': True}},
    # The roof stair's head is quiet too (entrance:p5_stair, the first room from P5), with the seal broken and the
    # seal room's Sky Golems alive: nothing comes for the party in 10 s there.
    {'setup_shortcut': {'kind': 'set_qbit', 'id': 111820, 'value': True}},
    {'reload': {}},
    lua("wait(8); close()"),
    lua(f"if door_state({D['door:seal']}) ~= 'open' then error('seal not open with 111820') end"),
    {'console': {'line': 'tp 224 1904 3072'}},
    {'advance_runtime': {'seconds': 1}},
    lua("close()"),
    {'console': {'line': 'arena trace on'}},
    {'advance_runtime': {'seconds': 10}},
    {'assert': {'party_position': {'x': 224, 'y': 1904, 'radius': 96, 'z_min': 3064, 'z_max': 3080}}},
    {'assert': {'ai_trace': {'event': 'target', 'target': 'party', 'max_count': 0, 'report': True}}},
    {'assert': {'actor_count': {'monster_id': 11585, 'hostile': True, 'min': 20}}},
    {'assert': {'actor_count': {'monster_id': 11586, 'hostile': True, 'min': 16}}},
    {'assert': {'actor_count': {'monster_id': 11594, 'hostile': True, 'min': 8}}},
    {'assert': {'actor_count': {'monster_id': 11584, 'hostile': True, 'min': 1, 'max': 1}}},
    {'assert': {'actor_count': {'monster_id': 11585, 'hostile': False, 'max': 0}}},
    {'assert': {'actor_count': {'monster_id': 11586, 'hostile': False, 'max': 0}}},
    {'assert': {'actor_count': {'monster_id': 11594, 'hostile': False, 'max': 0}}},
    {'console': {'line': 'tp -700 0 0'}},
    {'advance_runtime': {'seconds': 1}},
    lua("close()"),
    {'spawn_actor': {'monster_id': 11585, 'x': -500, 'y': -500, 'z': 0}},
    {'spawn_actor': {'monster_id': 11586, 'x': -500, 'y': 500, 'z': 0}},
    {'spawn_actor': {'monster_id': 11594, 'x': -300, 'y': -600, 'z': 0}},
    {'advance_runtime': {'seconds': 12}},
    {'assert': {'ai_trace': {'event': 'target', 'target': 'actor', 'max_count': 0, 'report': True}}},
    {'assert': {'ai_trace': {'actor_index': 'last', 'event': 'target', 'target': 'party', 'min_count': 1}}},
    {'assert': {'actor_count': {'monster_id': 11585, 'hurt': True, 'max': 0}}},
    {'assert': {'actor_count': {'monster_id': 11586, 'hurt': True, 'max': 0}}},
]
write('playtest_hostility.yml', {'id': 'xeen.fd03.l4.hostility', 'title': 'Darkstone Tower (FD-03 L4): a quiet '
                                 'arrival, every golem hostile, no fights among them', 'world': 'xeen',
                                 'mode': 'faithful', 'steps': steps},
      "# Hostility check of Darkstone Tower (FD-03, L4; written by output/studio_cal/fd03/tools/gen_tests.py): the\n"
      "# arrival is quiet (nothing targets the party for 10 s at the door, D-11.3); every onyx golem, Sky Golem and the\n"
      "# Onyx Golem hostile (the hidden guards included); spawned golems go for the party, never for each other.\n")
print('written playtests; hidden', HIDDEN, 'onyx', ONYX)
