#!/usr/bin/env python3
"""FD-02 Southern Sphinx: writes the L4 playtests from the built ids.lock.yml (event and door numbers by name).

  playtest.yml            the critical path: runes, the name wrong then right, the door in the same visit, Picard's
                          topic without and with the widget (the Chime, m40.done), Picard unkillable, a reload
  playtest_traps.yml      one unprotected crossing of each run within D-57's cap, nobody dies; the masks: No, Yes,
                          the clue; paid blades stopped, also after a reload
  playtest_crypt.yml      D-57 / D-32: the Dragon Mummies stay in the crypt and the stalls, the party at the arch above
  playtest_exit.yml       out through the leaves to X6, the landing measured
  playtest_hostility.yml  the quiet arrival (10 s, no harm), the three rows hostile, Picard peaceful, after a reload too
Usage: gen_tests.py (after a build has written L4/ids.lock.yml)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path

import yaml

L4 = Path(_REPO_ROOT + '/devdocs/xeen/briefs/fd02/L4')
lock = yaml.safe_load((L4 / 'ids.lock.yml').read_text())
E = lock['events']
D = lock['doors']
HP = {0: 335, 1: 150, 2: 210, 3: 140}   # level-59 Knight, Cleric, Archer, Sorcerer (measured, NOTES)
# Actor index: the build orders the scene's actors by their objects.yml id (checked in the built scene, 2026-11-21).
_ids = sorted(m['id'] for m in yaml.safe_load((L4 / 'objects.yml').read_text())['monsters'])
PICARD = _ids.index('monster:picard')


def head(tid, title, comment, gold=0, immortal=True):
    lines = [f'# {line}' for line in comment.strip().splitlines()]
    lines += [f'id: {tid}', 'title: ' + yaml.safe_dump(title, default_style='"', width=10000).strip(), 'world: xeen', 'mode: faithful', 'steps:',
              '  - new_game_flow:', '      start_map: xeen_fd02.blv', '      party:', f'        gold: {gold}',
              '        food: 20', '        members:',
              '          - {name: Brokk, class: Knight, level: 59, skills: [], equipment: {}}',
              '          - {name: Hild, class: Cleric, level: 59, skills: [], equipment: {}}',
              '          - {name: Ivar, class: Archer, level: 59, skills: [], equipment: {}}',
              '          - {name: Sefa, class: Sorcerer, level: 59, skills: [], equipment: {}}',
              '  - assert: {map: xeen_fd02.blv}']
    if immortal:
        lines.append('  - setup_shortcut: {kind: immortal, value: true}')
    return lines


def walk(x, y, z, r=64, clear=1500, t=40, ztol=None, close=True):
    zt = f', z_tolerance: {ztol}' if ztol else ''
    cl = f', clear_hostiles: {clear}' if clear else ''
    return (f'  - walk_to: {{x: {x}, y: {y}, z: {z}, radius: {r}{zt}{cl}, timeout_seconds: {t}, '
            f'close_dialogs: {"true" if close else "false"}}}')


def lua(src):
    return '  - play_lua: {source: ' + yaml.safe_dump(src, default_style='"', width=10000).strip() + '}'


def dialog(text):
    return '  - assert: {dialog: {active: true, text_contains: ' + yaml.safe_dump(text, default_style='"').strip() + '}}'


def full_hp():
    return [f'  - setup_shortcut: {{kind: set_member_points, member_index: {i}, health: {h}}}' for i, h in HP.items()]


def write(name, lines):
    (L4 / name).write_text('\n'.join(lines) + '\n')


# ------------------------------------------------------------------------------------------------ the critical path
P = head('xeen.fd02.l4.walk', 'Southern Sphinx (FD-02 L4), the runes, the name wrong then right, Picard and the Chime', f"""
Playtest of the Southern Sphinx (FD-02, L4; lane A7, agent:xeen-a7-fd02; written by output/studio_cal/fd02/tools/
gen_tests.py from ids.lock.yml): the critical path (D-57's FD-02 playtest). A level-59 party (immortal) arrives on the
breast's top step (entrance:x6_door): the arrival line, the way out's window (cancelled); the hall, the Swinging Death,
the north Preservation Room (runes P, I, C; the great sarcophagus's Might 60), the canopic chamber, the south room
(A, R, D: the sixth calls m40.runes), back by the Chopping Death; up the stair of the name: the landing asks, a wrong
name ("Wrong."), the door asked again, PICARD ("Correct, come on up!", name_said 111800) and the door open within two
seconds; the Home (m40.stair's line); Picard's topic without the widget, then with it (the Chime, m40.done 111801);
Picard struck: no damage, still peaceful; every window closed and a save and load: the door still open.""")
P += [
    '  - assert: {party_position: {x: -256, y: 0, radius: 96, z_min: -8, z_max: 8}}',
    lua("wait(2); local s = tostring(status()); log('arrive: ' .. s); if not string.find(s, 'Sand on the steps', 1, true) then error('arrival line: ' .. s) end; close()"),
    walk(-112, 0, 0, r=48),
    lua(f"click({E['evt:exit_l']}); wait(0.5)"),
    dialog('Do you wish to leave'),
    lua('close()'),
    '  - assert: {map: xeen_fd02.blv}',
    walk(-840, 0, -256, r=48, ztol=40),
    lua(f"open_door({E['evt:door_body']}, {D['door:body']})"),
    walk(-1200, 0, -256),
    walk(-2600, 0, -256),
    '  - clear_hostiles: {radius: 3000}',
    walk(-3300, 256, -256),
    walk(-4520, 256, -256),
    lua(f"open_door({E['evt:door_swing']}, {D['door:swing']})"),
    walk(-4900, 256, -256),
    '  - clear_hostiles: {radius: 2500}',
]
for c, x, y in (('p', -5216, 540), ('i', -5056, 540), ('c', -4896, 540)):
    P += [walk(x, y, -256, r=40), lua(f"click({E['evt:rune_' + c]}); wait(0.7)"),
          dialog(f'lesson about the letter "{c.upper()}"'), lua('close()')]
P += [
    walk(-5056, 240, -256, r=40),
    lua(f"log('party: ' .. party()); click({E['evt:chest_sarc_n']}); wait(0.7)"),
    dialog('too weak to open the sarcophagus'),
    lua('close()'),
    walk(-5300, 288, -256),
    walk(-5824, 0, -256),
    '  - clear_hostiles: {radius: 2500}',
    walk(-5300, -288, -256),
    walk(-5056, -384, -256),
    '  - clear_hostiles: {radius: 2500}',
]
for c, x, y in (('a', -4896, -540), ('r', -5056, -540)):
    P += [walk(x, y, -256, r=40), lua(f"click({E['evt:rune_' + c]}); wait(0.7)"),
          dialog(f'lesson about the letter "{c.upper()}"'), lua('close()')]
P += [
    walk(-5216, -540, -256, r=40),
    lua(f"click({E['evt:rune_d']}); wait(0.7)"),
    dialog('in the order of the halls'),
    lua("close(); close(); for _, q in ipairs({118110, 118111, 118112, 118113, 118114, 118115}) do if not qbit(q) then error('rune qbit ' .. q .. ' not set') end end"),
    walk(-4800, -256, -256),
    lua(f"open_door({E['evt:door_chop']}, {D['door:chop']})"),
    walk(-4520, -256, -256),
    walk(-3300, -256, -256),
    walk(-1344, 300, -256),
    walk(-1344, 1900, 700, ztol=80, t=60),
    '  - set_pose: {map: xeen_fd02.blv, x: -1344, y: 2140, z: 768, yaw: 1.5708, pitch: 0.0}',
    '  - advance_runtime: {seconds: 1, present_dialogs: true}',
    dialog('What is my name?'),
    '  - answer_input: {text: "Golux"}',
    '  - advance_runtime: {seconds: 1, present_dialogs: true}',
    dialog('Wrong'),
    lua(f"close(); wait(1); if qbit(111800) then error('name_said on a wrong name') end; if door_state({D['door:name']}) ~= 'closed' then error('the door moved on a wrong name') end"),
    walk(-1344, 2400, 768, r=40, ztol=24),
    lua(f"click({E['evt:name_door']}); wait(0.5)"),
    dialog('What is my name?'),
    '  - answer_input: {text: "Picard"}',
    '  - advance_runtime: {seconds: 1, present_dialogs: true}',
    dialog('Correct, come on up!'),
    lua(f"close(); wait(2); if not qbit(111800) then error('name_said 111800 not set') end; if door_state({D['door:name']}) ~= 'open' then error('the door of the name is not open in the same visit: ' .. door_state({D['door:name']})) end"),
    walk(-1344, 2480, 768, r=48, ztol=24),
    '  - set_pose: {map: xeen_fd02.blv, x: -1344, y: 2800, z: 768, yaw: 1.5708, pitch: 0.0}',
    '  - advance_runtime: {seconds: 1, present_dialogs: true}',
    dialog('a room full of books'),
    lua('close()'),
    lua(f"click({E['evt:book_4']}); wait(0.5)"),
    dialog('old cigars'),
    lua('close()'),
    walk(-1420, 3200, 768, r=48, ztol=24),
    f'  - assert: {{actor_visible: {{actor_index: {PICARD}, name: Picard the Aged, hidden: false}}}}',
    f'  - interact_actor: {{actor_index: {PICARD}}}',
    '  - advance_runtime: {seconds: 0.5, present_dialogs: true}',
    '  - assert: {dialog: {active: true}}',
    '  - select_topic: {action_id: 42001, match_label: "Quest"}',
    dialog('widget'),
    lua("close(); close(); wait(0.5); close(); if qbit(111801) then error('m40.done without the widget') end"),
    '  - grant_item: {item_id: 12315, member_index: 0}',
    lua('if held() ~= 0 then stow() end'),
    f'  - interact_actor: {{actor_index: {PICARD}}}',
    '  - advance_runtime: {seconds: 0.5, present_dialogs: true}',
    '  - select_topic: {action_id: 42001, match_label: "Quest"}',
    dialog('Really?'),
    lua("close(); close(); wait(0.5); close(); if not qbit(111801) then error('m40.done 111801 not set') end; if not has_item(12373) then error('no Chime of Opening') end; if has_item(12315) then error('the widget is still here') end"),
    '  # D-51 / D-52: Picard cannot be killed: struck 40 times, no damage, still peaceful.',
    f'  - party_attack: {{actor_index: {PICARD}, member_index: 0, count: 40, kill: true, min_hit_rate: 0.025, report: true}}',
    f'  - assert: {{actor_visible: {{actor_index: {PICARD}, name: Picard the Aged, dead: false, hp: 180, report_state: true}}}}',
    '  - assert: {actor_count: {monster_id: 11922, hostile: false, min: 1}}',
    lua(f"click({E['evt:throne']}); wait(0.5)"),
    dialog('very good chair'),
    lua('close(); close()'),
    '  - reload: {}',
    lua(f"wait(2); close(); if door_state({D['door:name']}) ~= 'open' then error('the door of the name after reload: ' .. door_state({D['door:name']})) end"),
    '  - assert: {actor_count: {monster_id: 11922, hostile: false, min: 1}}',
]
write('playtest.yml', P)

# ------------------------------------------------------------------------------------------------ the traps
SW = [D[f'mover:swing_{i}'] for i in range(1, 5)]
CH = [D[f'mover:chop_{i}'] for i in range(1, 4)]
T = head('xeen.fd02.l4.traps', 'Southern Sphinx (FD-02 L4), the death runs within the cap and the masks', f"""
D-57 APPROVAL and Q9: one unprotected crossing of each run (a level-59 party, not immortal, every member at full HP:
Knight 335, Cleric 150, Archer 210, Sorcerer 140) costs each member at most 25 % of its HP and kills nobody (4 x 8 on
the Swinging Death, 3 x 11 on the Chopping Death: the sorcerer 23 %). The Chopping Death's mask: No ("Begone, then!",
no gold taken). The Swinging Death's mask: Yes (A3's m40.mask_swinging: 2,000 gold, swinging_paid 118116, its line);
the blades go into their slots and a second crossing costs nothing; clicked again, the clue bought (500, "There's
one born every minute."), and again, refused ("Begone, then!"); every window closed, a save and load: the blades still in their slots, a third crossing free.""",
              gold=6000, immortal=False)
T += [
    lua('wait(2); close()'),
    walk(-840, 0, -256, r=48, ztol=40),
    lua(f"open_door({E['evt:door_body']}, {D['door:body']})"),
    walk(-1200, 0, -256),
    walk(-2400, 0, -256),
    '  - clear_hostiles: {radius: 6000}',
    walk(-3250, 256, -256),
] + full_hp() + [
    walk(-4540, 256, -256, clear=0, t=30),
    '  - advance_runtime: {seconds: 0.5}',
    lua("log('after the Swinging Death: ' .. party())"),
] + [f'  - assert: {{member_points: {{member_index: {i}, health_min: {h - h // 4}, health_max: {h - 1}}}}}'
     for i, h in HP.items()] + [
    walk(-3250, 256, -256, clear=0),
    walk(-3250, -256, -256, clear=0),
] + full_hp() + [
    walk(-4540, -256, -256, clear=0, t=30),
    '  - advance_runtime: {seconds: 0.5}',
] + [f'  - assert: {{member_points: {{member_index: {i}, health_min: {h - h // 4}, health_max: {h - 1}}}}}'
     for i, h in HP.items()] + [
    walk(-3500, -256, -256, clear=0),
    walk(-3520, -340, -256, r=40, clear=0),
    lua(f"click({E['evt:mask_chop']}); wait(0.5)"),
    dialog('Chopping Death'),
    '  - answer_input: {text: "No"}',
    '  - advance_runtime: {seconds: 1, present_dialogs: true}',
    dialog('Begone, then!'),
    lua("close(); if gold() ~= 6000 then error('gold taken on No: ' .. gold()) end; if qbit(118117) then error('chopping_paid on No') end"),
    walk(-3500, 256, -256, clear=0),
    walk(-3520, 340, -256, r=40, clear=0),
    lua(f"click({E['evt:mask_swing']}); wait(0.5)"),
    dialog('Swinging Death'),
    '  - answer_input: {text: "Yes"}',
    '  - advance_runtime: {seconds: 1, present_dialogs: true}',
    dialog('blades swing slower'),
    lua(f"close(); close(); if not qbit(118116) then error('swinging_paid 118116 not set') end; if gold() ~= 4000 then error('gold after paying: ' .. gold()) end; wait(3); for _, d in ipairs({{{', '.join(map(str, SW))}}}) do if door_state(d) ~= 'open' then error('blade ' .. d .. ' not in its slot: ' .. door_state(d)) end end"),
] + full_hp() + [
    walk(-4540, 256, -256, clear=0, t=30),
    '  - advance_runtime: {seconds: 0.5}',
] + [f'  - assert: {{member_points: {{member_index: {i}, health_min: {h}, health_max: {h}}}}}' for i, h in HP.items()] + [
    walk(-3520, 340, -256, r=40, clear=0, t=30),
    lua(f"click({E['evt:mask_swing']}); wait(0.5)"),
    dialog('another 500'),
    '  - answer_input: {text: "Yes"}',
    '  - advance_runtime: {seconds: 1, present_dialogs: true}',
    dialog('born every minute'),
    lua("close(); close(); if gold() ~= 3500 then error('gold after the clue: ' .. gold()) end"),
    lua(f"click({E['evt:mask_swing']}); wait(0.5)"),
    dialog('another 500'),
    '  - answer_input: {text: "No"}',
    '  - advance_runtime: {seconds: 1, present_dialogs: true}',
    dialog('Begone, then!'),
    lua("close(); close(); if gold() ~= 3500 then error('gold after No to the clue: ' .. gold()) end"),
    '  - reload: {}',
    lua(f"wait(3); close(); if not qbit(118116) then error('swinging_paid lost') end; for _, d in ipairs({{{', '.join(map(str, SW))}}}) do if door_state(d) ~= 'open' then error('blade ' .. d .. ' after reload: ' .. door_state(d)) end end; for _, d in ipairs({{{', '.join(map(str, CH))}}}) do log('chop ' .. d .. ' ' .. door_state(d)) end"),
] + full_hp() + [
    walk(-3250, 256, -256, clear=0, t=30),
    walk(-4540, 256, -256, clear=0, t=30),
    '  - advance_runtime: {seconds: 0.5}',
] + [f'  - assert: {{member_points: {{member_index: {i}, health_min: {h}, health_max: {h}}}}}' for i, h in HP.items()]
write('playtest_traps.yml', T)

# ------------------------------------------------------------------------------------------------ the crypt dragons
C = head('xeen.fd02.l4.crypt', 'Southern Sphinx (FD-02 L4), the Dragon Mummies stay in the crypt and the stalls (D-57, D-32)', """
D-57 FD-02 APPROVAL and D-32: the Dragon Mummy (11672, 450 high, flies) is kept below by the crypt steps' 288-high arch.
The party (immortal) stands in the canopic chamber at the arch's mouth, in the dragons' sight, for 60 s: all six are
still in the crypt and the stalls, none in the canopic chamber or the Preservation Rooms.""")
C += [
    lua('wait(2); close()'),
    '  - set_pose: {map: xeen_fd02.blv, x: -6000, y: 0, z: -256, yaw: 3.1416, pitch: -0.3}',
    '  - advance_runtime: {seconds: 0.5}',
    '  - clear_hostiles: {radius: 1200}',
    '  - assert: {actor_count: {monster_id: 11672, near: [-7360, 0, 1300], min: 4}}',
    '  - assert: {actor_count: {monster_id: 11672, near: [-9280, 0, 900], min: 2}}',
    '  - advance_runtime: {seconds: 30}',
    lua("log('after 30 s: ' .. tostring(status()))"),
    '  - advance_runtime: {seconds: 30}',
    '  - assert: {actor_count: {monster_id: 11672, near: [-5824, 0, 700], max: 0}}',
    '  - assert: {actor_count: {monster_id: 11672, near: [-5056, 384, 600], max: 0}}',
    '  - assert: {actor_count: {monster_id: 11672, near: [-5056, -384, 600], max: 0}}',
    '  - assert: {actor_count: {monster_id: 11672, near: [-2112, 0, 1300], max: 0}}',
    '  - assert: {actor_count: {monster_id: 11672, near: [-8100, 0, 2000], min: 6}}',
]
write('playtest_crypt.yml', C)

# ------------------------------------------------------------------------------------------------ the exit
X = head('xeen.fd02.l4.exit', 'Southern Sphinx (FD-02 L4), out through the leaves to X6', """
The way out (the exit preset, D-24): through the breast's leaves to X6's named arrival entrance:fd02_door
(-12288, -10240, 1536) facing east (A5 moved it out of the sphinx); the leave window's OK pressed; the landing measured
(status) and still there 6 s later.""")
X += [
    lua('wait(2); close()'),
    walk(-112, 0, 0, r=48),
    f"  - execute_event: {{id: {E['evt:exit_r']}}}",
    dialog('Do you wish to leave'),
    '  - select_topic: {match_label: "OK"}',
    '  - advance_runtime: {seconds: 1.5, follow_map_move: true}',
    '  - assert: {map: xeen_x6.odm}',
    lua("log('landing: ' .. status())"),
    '  - clear_hostiles: {radius: 6000}',
    '  - advance_runtime: {seconds: 6.0}',
    lua("log('landing after 6 s: ' .. status())"),
    '  - assert: {party_position: {x: -12288, y: -10240, radius: 120, z_min: 1400}}',
]
write('playtest_exit.yml', X)

# ------------------------------------------------------------------------------------------------ hostility
H = head('xeen.fd02.l4.hostility', 'Southern Sphinx (FD-02 L4): a quiet arrival; mummies and dragon mummies hostile, Picard peaceful', """
D-11.3: the party stands 10 s on the arrival step, not immortal, and nobody is hurt. A2's rows: Ghost Mummy 11273 (16),
Phase Mummy 11274 (4) and Dragon Mummy 11672 (6) all hostile at load and after a save and load; Picard the Aged 11922
peaceful. No window is open before the reload.""", immortal=False)
H += [
    '  - advance_runtime: {seconds: 10}',
    lua('close()'),
] + [f'  - assert: {{member_points: {{member_index: {i}, health_min: {h}, health_max: {h}}}}}' for i, h in HP.items()] + [
    '  - assert: {party_position: {x: -256, y: 0, radius: 96, z_min: -8, z_max: 8}}',
    '  - setup_shortcut: {kind: immortal, value: true}',
    '  - assert: {actor_count: {monster_id: 11273, hostile: false, max: 0}}',
    '  - assert: {actor_count: {monster_id: 11274, hostile: false, max: 0}}',
    '  - assert: {actor_count: {monster_id: 11672, hostile: false, max: 0}}',
    '  - assert: {actor_count: {monster_id: 11273, hostile: true, min: 16}}',
    '  - assert: {actor_count: {monster_id: 11274, hostile: true, min: 4}}',
    '  - assert: {actor_count: {monster_id: 11672, hostile: true, min: 6}}',
    '  - assert: {actor_count: {monster_id: 11922, hostile: false, min: 1}}',
    '  - reload: {}',
    lua('wait(1); close()'),
    '  - assert: {actor_count: {monster_id: 11273, hostile: false, max: 0}}',
    '  - assert: {actor_count: {monster_id: 11273, hostile: true, min: 16}}',
    '  - assert: {actor_count: {monster_id: 11274, hostile: true, min: 4}}',
    '  - assert: {actor_count: {monster_id: 11672, hostile: true, min: 6}}',
    '  - assert: {actor_count: {monster_id: 11922, hostile: false, min: 1}}',
]
write('playtest_hostility.yml', H)
print('written 5 playtests')
