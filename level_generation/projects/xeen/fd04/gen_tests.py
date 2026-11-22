#!/usr/bin/env python3
"""FD-04 Dragon Tower and the Dungeon of Death: writes the L4 playtests from ids.lock.yml (event, door and light
numbers) and the built scene's actor order. Rerun after gen.py and a build (cycle.sh) whenever an id may have moved.

  playtest_gongs.yml      the gong reset (D-43): lamps on when rung, the chest silences them ('The gongs fall
                          silent.'), the lever after four, the shutter, the machine broken, a reload keeping it all
  playtest_crossword.yml  Sandro's door without and with his key; the descent refused; a wrong answer, then Winterkill
                          for 45 Down and the other eleven; the descent open and walked; a reload
  playtest_terminal.yml   the main terminal: Goober, SUPER Goober, then 'computer' (any case) pays once
  playtest_alister.yml    Alister unkillable and peaceful; the egg from the nest; his paying talk; hidden the second
                          after the talk closes, in the same visit; a reload keeps him gone
  playtest_shrine.yml     the Shrine of Minor Evil (its experience), then the Ultimate's tell, No, Yes: the throw out
                          to X7 alive, 118148
  playtest_dragons.yml    a dragon on each floor stays on its floor (D-32, D-57 Q29): the party waits at each hall's
                          low opening, every dragon is still in its own hall
  playtest_exit.yml       the gate out to X7 (the leave window's OK), the landing measured
  playtest_roof.yml       the roof hatch up to X9's entrance:fd04_roof, the landing measured
  playtest_hostility.yml  quiet arrivals at the gate and on the roof stair's head; every monster hostile, Alister
                          peaceful; no fights among them
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import subprocess
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
L4 = R / 'devdocs/xeen/briefs/fd04/L4'
SCENE = R / 'output/studio_cal/fd04/root/worlds/xeen/maps/xeen_fd04.scene.yml'
ids = yaml.safe_load((L4 / 'ids.lock.yml').read_text())
E, D, LT = ids['events'], ids['doors'], ids['lights']
DECO = ids['decorations']
EGGS = [DECO[f'deco:egg_{i}'] for i in (1, 2, 3)]
LIZARD = [DECO['deco:lizard']]
scene = yaml.safe_load(SCENE.read_text())
actors = scene['initial_state']['actors']
ALISTER = [a['actor_index'] for a in actors if a['monster_info_id'] == 11923][0]
# The BLV's light index (the scenario's `light` key) of each lock light number.
EXPORT = R / 'output/studio_cal/fd04/export.json'
subprocess.run([str(R / 'openyamm-studio/build-xeen/oymap'), 'export',
                str(R / 'output/studio_cal/fd04/root/worlds/xeen/maps/xeen_fd04.blv'), '--world', 'xeen', '--assets',
                str(R / 'output/studio_cal/fd04/root'), '--out', str(EXPORT)], check=True, capture_output=True)
BLV_LIGHT = {l['id']: i for i, l in enumerate(json.loads(EXPORT.read_text())['map']['lights']) if l.get('id')}
DRAGON_IDS = (11641, 11642, 11643, 11652, 11653)
# The dragon halls: (x0, y0, x1, y1, floor z).
HALLS = {'scorched': (320, -224, 1536, 1536, 0), 'ring': (-960, -1536, 1536, 960, 1280),
         'nest': (-1536, -1536, 704, 960, 2560), 'hatchery': (768, -768, 1536, 960, 2560),
         'high': (-1536, -1536, 256, -192, 3840), 'crown': (-1024, -128, 960, 1536, 3840)}


def hall_of(a):
    p = a['position']
    for k, (x0, y0, x1, y1, z) in HALLS.items():
        if x0 < p['x'] < x1 and y0 < p['y'] < y1 and abs(p['z'] - z) < 64:
            return k
    raise ValueError(a)


DRAGONS = [(a['actor_index'], hall_of(a)) for a in actors if a['monster_info_id'] in DRAGON_IDS]
assert len(DRAGONS) == 26, len(DRAGONS)


def party(level=63):
    return {'gold': 0, 'food': 20, 'members': [
        {'name': n, 'class': c, 'level': level, 'skills': [], 'equipment': {}}
        for n, c in (('Brokk', 'Knight'), ('Hild', 'Cleric'), ('Ivar', 'Archer'), ('Sefa', 'Sorcerer'))]}


def start():
    return [{'new_game_flow': {'start_map': 'xeen_fd04.blv', 'party': party()}},
            {'assert': {'map': 'xeen_fd04.blv'}}]


def walk(x, y, z, r=64, t=60, clear=1500, ztol=None):
    w = {'x': x, 'y': y, 'z': z, 'radius': r, 'timeout_seconds': t, 'close_dialogs': True}
    if clear:
        w['clear_hostiles'] = clear
    if ztol is not None:
        w['z_tolerance'] = ztol
    return {'walk_to': w}


def lua(src):
    return {'play_lua': {'source': src}}


def tp(x, y, z):
    return [{'console': {'line': f'tp {x} {y} {z}'}}, {'advance_runtime': {'seconds': 1.0}}, lua("close(); wait(0.3); close()")]


def dialog(text):
    return [{'advance_runtime': {'seconds': 0.5, 'present_dialogs': True}},
            {'assert': {'dialog': {'active': True, 'text_contains': text}}}]


def status(text):
    # A line the game shows on the status line (D-90: an XP touch writes no window).
    return lua(f"local s = tostring(status()); if not string.find(s, [[{text}]], 1, true) then "
               f"error('status line: ' .. s) end")


def answer(event, text, expect, on_status=False):
    # status() reads the line once (a second read finds it empty): a status-line answer is checked in the logging read.
    check = (f" if not string.find(s, [[{expect}]], 1, true) then error('status line: ' .. s) end" if on_status else '')
    return [lua(f"click({E[event]}); wait(0.5)"), {'answer_input': {'text': text}},
            {'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}}, lua(f"local s = tostring(status()); "
                                                                                 f"log('{event} {text.replace(chr(39), '')}: ' .. s);{check}"),
            ] + ([{'assert': {'dialog': {'active': True, 'text_contains': expect}}}] if expect and not on_status else []) + [
            lua("close(); wait(0.5); close()")]


def light(name, on):
    return {'assert': {'light': {'key': BLV_LIGHT[LT[name]], 'on': on}}}


def write(name, doc, header):
    (L4 / name).write_text(header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120))


def scenario(name, sid, title, steps, header):
    write(name, {'id': sid, 'title': title, 'world': 'xeen', 'mode': 'faithful', 'steps': steps}, header)


IMMORTAL = {'setup_shortcut': {'kind': 'immortal', 'value': True}}

# ------------------------------------------------------------------------------------------------ gongs and machine
steps = start() + [IMMORTAL, lua("wait(2); close()")] + tp(0, 9100, -2560) + [
    {'clear_hostiles': {'radius': 6000}},
    lua(f"if door_state({D['door:shutter']}) ~= 'closed' then error('the shutter does not start shut') end"),
    # Two gongs rung: their lamps light.
    lua(f"click({E['evt:gong_1']}); wait(0.5); log('gong 1: ' .. tostring(status())); click({E['evt:gong_2']}); wait(0.5)"),
    light('light:gong_1', True), light('light:gong_2', True),
    # The lever before four: it won't budge, and the voice.
    lua(f"click({E['evt:lever']}); wait(0.5)"),
] + dialog("The lever won't budge.") + [
    lua(f"close(); wait(0.5); if door_state({D['door:shutter']}) ~= 'closed' then error('shutter moved') end"),
    # The chest before the shutter: the gongs fall silent, their lamps go out.
    lua(f"click({E['evt:chest_gongs']}); wait(0.5); close(); wait(2.5); local s = tostring(status()); "
        "log('chest: ' .. s); if not string.find(s, 'The gongs fall silent', 1, true) then error('no reset line: ' .. s) end"),
    light('light:gong_1', False), light('light:gong_2', False),
    # All four, then the lever: the shutter rises for good.
] + [lua(f"click({E[f'evt:gong_{i}']}); wait(0.5)") for i in range(1, 5)] + [
    light('light:gong_1', True), light('light:gong_2', True), light('light:gong_3', True), light('light:gong_4', True),
    lua(f"click({E['evt:lever']}); wait(7); log('lever: ' .. tostring(status())); if not qbit(118144) then "
        f"error('shutter_up 118144 not set') end; if door_state({D['door:shutter']}) ~= 'open' then "
        f"error('shutter not up: ' .. door_state({D['door:shutter']})) end"),
    # The chest after the shutter: no reset.
    lua(f"click({E['evt:chest_gongs']}); wait(0.5); close(); wait(2.5); local s = tostring(status()); "
        "if string.find(s, 'fall silent', 1, true) then error('reset after the shutter') end"),
    light('light:gong_1', True),
    # Through the shutter, maintenance, the machine: the question breaks it, the cores go dark.
    walk(0, 9800, -2560), walk(0, 10432, -2560), walk(0, 11000, -2560), walk(-300, 11500, -2560),
    {'clear_hostiles': {'radius': 6000}},
    lua(f"click({E['evt:machine']}); wait(0.5)"), {'answer_input': {'text': 'Yes'}},
    {'advance_runtime': {'seconds': 2.0, 'present_dialogs': True}},
    {'assert': {'dialog': {'active': True, 'text_contains': 'Lord Xeen Machine'}}},
    lua("close(); wait(1); close(); if not qbit(118145) then error('machine_broken 118145 not set') end; "
        "if not qbit(114041) then error('Q-F2 done 114041 not set') end"),
    light('light:core_fire', False), light('light:core_air', False),
    lua(f"click({E['evt:term_fire']}); wait(0.5)"),
] + dialog('Fire Core Offline') + [
    lua("close(); wait(1); close()"),
    {'reload': {}},
    lua(f"wait(6); close(); if door_state({D['door:shutter']}) ~= 'open' then error('shutter after reload') end"),
    light('light:gong_1', True), light('light:gong_4', True), light('light:core_water', False),
]
scenario('playtest_gongs.yml', 'xeen.fd04.l4.gongs', 'Dragon Tower (FD-04 L4): the gongs, their lamps and the reset, '
         'the lever and shutter, the Lord Xeen Machine', steps,
         "# The gong hall (D-43, D-57 FD-04; written by output/studio_cal/fd04/tools/gen_tests.py): lamps light as the\n"
         "# gongs are rung; the chest before the shutter silences them (A3's 'The gongs fall silent.', lamps out); four\n"
         "# gongs and the lever raise the shutter (118144); the machine broken (118145); a reload keeps it all.\n")

# ------------------------------------------------------------------------------------------------ crossword
WORDS = [('1a', 'Xeens Sceptre.'), ('5a', 'VAMPIRE.'), ('6a', 'Kalindra\u2019s'), ('13a', 'corak.'), ('21a', 'Castle Alamar'),
         ('24a', 'Necropolis'), ('40a', 'Sandcaster'), ('44d', 'Castleview'), ('47d', 'The Southern Sphinx'),
         ('76d', 'Mirror'), ('77d', 'Xeen')]
steps = start() + [IMMORTAL, lua("wait(2); close()"),
                   walk(0, -720, 0, clear=0),
                   lua(f"click({E['evt:sandro']}); wait(0.5)")] + dialog('answers only to his key') + [
    lua(f"close(); wait(0.5); if door_state({D['door:sandro']}) ~= 'closed' then error('opened without the key') end"),
    {'grant_item': {'item_id': 12354}},
    lua(f"click({E['evt:sandro']}); wait(0.5)")] + dialog('turns in the skull') + [
    lua(f"close(); wait(3); if not qbit(118130) then error('door_open 118130 not set') end; if door_state("
        f"{D['door:sandro']}) ~= 'open' then error('door not open') end; if not has_item(12354) then "
        "error('the key was taken') end"),
    walk(0, -300, 0, clear=0), walk(0, -180, 0, clear=0),
    walk(0, 1060, -1024, ztol=24, t=90, clear=0), walk(0, 1400, -1024, clear=2500),
    {'clear_hostiles': {'radius': 4000}},
    # The descent before the twelve.
    lua(f"click({E['evt:descent']}); wait(0.5)")] + dialog('crossword puzzle is not done yet') + [
    lua("close(); wait(0.5)"),
] + answer('evt:clue_45d', 'Darkstone', 'Wrong!') + [
    lua("if qbit(118139) then error('a wrong answer lit 45 Down') end")
] + answer('evt:clue_45d', 'Winterkill', 'Correct!') + [
    lua("if not qbit(118139) then error('word_45d 118139 not set') end"), light('light:word_45d', True)
] + answer('evt:clue_1a', 'Sceptor', 'Wrong!') + answer('evt:clue_1a', 'Staff.', 'Wrong!') + [
    lua("if qbit(118131) then error('a wrong answer lit 1 Across') end")]
for key, word in WORDS:
    steps += answer(f'evt:clue_{key}', word, 'Correct!')
steps += [
    lua("for b = 118131, 118142 do if not qbit(b) then error('word ' .. b .. ' not set') end end"),
    light('light:word_1a', True), light('light:word_77d', True),
    lua(f"click({E['evt:clue_45d']}); wait(0.5); log('solved plaque: ' .. tostring(status()))"),
    lua(f"click({E['evt:descent']}); wait(0.5)")] + [lua("local s = tostring(status()); if not string.find(s, 'You may pass', 1, true) then error('status line: ' .. s) end")] + [
    lua(f"close(); wait(6); if not qbit(118143) then error('crossword_done 118143 not set') end; if door_state("
        f"{D['door:descent']}) ~= 'open' then error('descent shut: ' .. door_state({D['door:descent']})) end"),
    walk(0, 3000, -1024), walk(0, 3420, -1024, clear=0), walk(0, 4320, -1792, ztol=24, t=90, clear=0),
    walk(0, 4560, -1792, clear=0),
    lua("wait(0.5); local s = tostring(status()); log('welcome: ' .. s); if not string.find(s, 'Welcome', 1, true) "
        "then error('no Welcome sign: ' .. s) end"),
    lua("close(); wait(1); close()"),
    {'reload': {}},
    lua(f"wait(6); close(); if door_state({D['door:sandro']}) ~= 'open' then error('Sandro door after reload') end; "
        f"if door_state({D['door:descent']}) ~= 'open' then error('descent after reload') end"),
    light('light:word_45d', True), light('light:word_6a', True),
]
scenario('playtest_crossword.yml', 'xeen.fd04.l4.crossword', 'Dragon Tower (FD-04 L4): Sandro\'s door and the '
         'crossword', steps,
         "# Sandro's door and the crossword (D-57 Q24, Q25; written by output/studio_cal/fd04/tools/gen_tests.py): the\n"
         "# door refused without item 12354, opened with it (118130, the key kept); the descent refused; 45 Down wrong\n"
         "# (Darkstone, the replaced clue's answer), then Winterkill; 1 Across wrong twice (Sceptor, Staff.); the other\n"
         "# eleven in mixed case and variants (a trailing full stop, Sceptre, no or a curly apostrophe); the\n"
         "# descent pays and opens (118143); down to the Welcome hall; a reload keeps the doors and the lit words.\n")

# ------------------------------------------------------------------------------------------------ terminal
steps = start() + [IMMORTAL, lua("wait(2); close()")] + tp(-1344, 10300, -2560) + [
    {'clear_hostiles': {'radius': 6000}},
    lua("if qbit(118149) then error('code set at the start') end"),
] + answer('evt:terminal', 'Darkstone', 'You are a Goober!') + answer('evt:terminal', 'password',
                                                                       'You are a SUPER Goober!') + [
    lua(f"remember('xp', tostring(experience(0)))"),
] + answer('evt:terminal', 'cOmPuTeR', 'CODE ACCEPTED', on_status=True) + [
    lua("if not qbit(118149) then error('code_entered 118149 not set') end; log('xp before ' .. recall('xp') .. "
        "', after ' .. tostring(experience(0)))"),
    lua(f"click({E['evt:terminal']}); wait(0.5)")] + dialog('Code accepted already') + [lua("close()")]
scenario('playtest_terminal.yml', 'xeen.fd04.l4.terminal', 'Dragon Tower (FD-04 L4): the main terminal', steps,
         "# The main terminal (D-57 Q35; written by output/studio_cal/fd04/tools/gen_tests.py): 'Main Terminal / Enter\n"
         "# Code'; a wrong code gives 'You are a Goober!', a second 'You are a SUPER Goober!'; 'Computer' in any case\n"
         "# pays once (118149, A3's q-f2.terminal); a later click gives the hook's else line.\n")

# ------------------------------------------------------------------------------------------------ Alister
# The name is the NPC row's (F9-R2, merge point 41: an actor with an NPC id shows 'Name, Profession').
steps = start() + [IMMORTAL, lua("wait(2); close()"),
                   {'assert': {'actor_visible': {'actor_index': ALISTER, 'name': 'Alister, Druid', 'hidden': False,
                                                 'report_state': True}}},
                   {'assert': {'actor_count': {'monster_id': 11923, 'hostile': False, 'min': 1}}},
                   walk(-640, -768, 0, clear=0),
                   {'party_attack': {'actor_index': ALISTER, 'member_index': 0, 'count': 20, 'kill': True,
                                     'min_hit_rate': 0.0, 'report': True}},
                   {'assert': {'actor_visible': {'actor_index': ALISTER, 'dead': False, 'report_state': True}}},
                   {'assert': {'actor_count': {'monster_id': 11923, 'hostile': False, 'min': 1}}},
                   {'assert': {'sprite_hidden': LIZARD}},
                   lua("close(); wait(0.5); close()"),
                   {'interact_actor': {'actor_index': ALISTER}},
                   {'advance_runtime': {'seconds': 0.5, 'present_dialogs': True}},
                   {'assert': {'dialog': {'active': True}}},
                   {'select_topic': {'action_id': 45551, 'match_label': 'Quest'}},
                   {'assert': {'dialog': {'active': True, 'text_contains': 'I need a dragon egg'}}},
                   lua("close(); close(); wait(0.5); close(); if not qbit(114020) then error('Q-F1 started not set') "
                       "end; if qbit(118147) then error('alister_gone too early') end"),
                   # The egg from the nest (a click on the bowl's rock; the hook gives it once): three eggs lie
                   # there (S's xeen_dragonegg), the third hidden once it is taken.
                   {'assert': {'sprite_shown': EGGS}},
                   lua(f"click({E['evt:egg']}); wait(0.5)")] + [lua("local s = tostring(status()); if not string.find(s, 'You lift one of the eggs', 1, true) then error('status line: ' .. s) end")] + [
    lua(f"close(); wait(0.5); if not has_item(12375) then error('no Dragon Egg') end; if not qbit(118146) then "
        f"error('egg_taken 118146 not set') end; click({E['evt:egg']}); wait(0.5)"), status('Two eggs are left')] + [
    {'assert': {'sprite_hidden': EGGS[2:], 'sprite_shown': EGGS[:2]}},
    lua("close(); wait(0.5); close()"),
    {'interact_actor': {'actor_index': ALISTER}},
    {'advance_runtime': {'seconds': 0.5, 'present_dialogs': True}},
    {'select_topic': {'action_id': 45551, 'match_label': 'Quest'}},
    {'assert': {'dialog': {'active': True, 'text_contains': 'drink this egg potion'}}},
    {'assert': {'actor_visible': {'actor_index': ALISTER, 'hidden': False}}},
    lua("close(); close(); wait(0.3); close(); wait(2); if not qbit(118147) then error('alister_gone 118147 not set') "
        "end; if has_item(12375) then error('the egg was not taken') end"),
    {'assert': {'actor_visible': {'actor_index': ALISTER, 'hidden': True}}},
    {'assert': {'sprite_shown': LIZARD}},
    lua("close(); wait(1); close()"),
    {'reload': {}},
    lua("wait(4); close()"),
    {'assert': {'actor_visible': {'actor_index': ALISTER, 'hidden': True}}},
    {'assert': {'sprite_hidden': EGGS[2:], 'sprite_shown': EGGS[:2] + LIZARD}},
]
scenario('playtest_alister.yml', 'xeen.fd04.l4.alister', "Dragon Tower (FD-04 L4): Alister, the egg and his vanish",
         steps,
         "# Alister (D-57 Q27; written by output/studio_cal/fd04/tools/gen_tests.py): peaceful and unkillable (struck\n"
         "# twenty times, still alive and peaceful); his first talk starts Q-F1; the nest's egg (q-f1.egg, 118146, once);\n"
         "# his paying talk takes it; the second after the talk closes he is hidden (118147) and the lizard he became\n"
         "# shown (S's xeen_lizard, hidden till then) in the same visit; a reload keeps him gone, the lizard and two eggs.\n")

# ------------------------------------------------------------------------------------------------ shrines
steps = start() + [lua("wait(2); close()")] + tp(1500, 7000, -1792) + [
    IMMORTAL, {'clear_hostiles': {'radius': 8000}},
    # A healthy party (D-57 Q26: never lethal to a healthy party): the fountain first (aazex123:5).
    lua(f"click({E['evt:fountain']}); wait(0.5); local s = tostring(status()); log('fountain: ' .. s); "
        "if not string.find(s, 'Ahh, refreshing', 1, true) then error('fountain line: ' .. s) end"),
    {'assert': {'member_points': {'member_index': 1, 'health_min': 150}}},
    {'setup_shortcut': {'kind': 'immortal', 'value': False}},
    lua(f"click({E['evt:shrine_minor']}); wait(0.5)"), {'answer_input': {'text': 'Yes'}},
    {'advance_runtime': {'seconds': 1.5, 'present_dialogs': True}},
    status('Shrine of Minor Evil cracks'),
    lua("close(); wait(0.5); close(); if not qbit(114043) then error('shrine_minor 114043 not set') end"),
    # The Ultimate: the tell in its question; No leaves it; Yes throws the party out to X7, alive.
    lua(f"click({E['evt:shrine_ultimate']}); wait(0.5)"),
    {'assert': {'dialog': {'active': True, 'text_contains': 'walls seem to lean'}}},
    {'answer_input': {'text': 'No'}},
    {'advance_runtime': {'seconds': 1.0}},
    lua("close(); wait(0.5); if qbit(118148) then error('No broke the Ultimate shrine') end"),
    # Yes: the throw is a `leave` (D-24, D-63 13): out to X7 at once, no leave window, no OK pressed.
    lua(f"click({E['evt:shrine_ultimate']}); wait(0.5)"), {'answer_input': {'text': 'Yes'}},
    {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
    {'assert': {'map': 'xeen_x7.odm'}},
    {'assert': {'dialog': {'active': False}}},
    lua("local s = tostring(status()); log('ultimate: ' .. s .. ' | ' .. party()); if not qbit(118148) then "
        "error('ultimate_broken 118148 not set') end"),
    lua("log('after the shrine: ' .. party()); for i = 0, 3 do local c = tostring(conditions(i)); log('member ' .. i "
        ".. ': ' .. c); if string.find(c, 'Dead', 1, true) or string.find(c, 'Eradicated', 1, true) then "
        "error('the shrine killed member ' .. i) end end"),
    {'assert': {'party_position': {'x': -17920, 'y': 16384, 'radius': 200, 'z_min': 2400, 'z_max': 2800}}},
]
scenario('playtest_shrine.yml', 'xeen.fd04.l4.shrine', "Dragon Tower (FD-04 L4): the Shrines of Minor and Ultimate "
         "Evil", steps,
         "# The shrines (D-57 Q26; written by output/studio_cal/fd04/tools/gen_tests.py): Minor Evil broken by its\n"
         "# question (its experience once); the Ultimate's question carries the tell; No leaves it; Yes: A3's Fire\n"
         "# damage and line, the shake, 118148, and the throw (leave, no window: D-63 13) out to X7's entrance:fd04_door, the\n"
         "# party alive.\n")

# ------------------------------------------------------------------------------------------------ dragons
WAIT_AT = {0: [(1216, -500, 0)], 1: [(-736, 1150, 1280)], 2: [(544, 1150, 2560), (1152, 1150, 2560)],
           3: [(480, -1280, 3840), (1280, 600, 3840)]}
FLOOR_HALLS = {0: ['scorched'], 1: ['ring'], 2: ['nest', 'hatchery'], 3: ['high', 'crown']}
steps = start() + [IMMORTAL, lua("wait(2); close()")]
for fl, points in WAIT_AT.items():
    for (x, y, z) in points:
        steps += tp(x, y, z) + [{'advance_runtime': {'seconds': 30}}, lua("close()")]
    for idx, hall in DRAGONS:
        if hall not in FLOOR_HALLS[fl]:
            continue
        x0, y0, x1, y1, hz = HALLS[hall]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rmax = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / 2
        steps.append({'assert': {'actor_visible': {'actor_index': idx, 'report_state': True, 'dead': False,
                                                   'near': {'x': cx, 'y': cy, 'max_distance': round(rmax),
                                                            'min_z': hz - 16}}}})
# None in the stair's ring (the three ramps run at |x| or |y| 1,600-1,888).
for (x, y) in ((-1744, -800), (-1744, 0), (-1744, 800), (-800, 1744), (0, 1744), (800, 1744), (1744, 800), (1744, 0),
               (1744, -800)):
    for mid in DRAGON_IDS:
        steps.append({'assert': {'actor_count': {'monster_id': mid, 'near': [x, y, 200], 'max': 0}}})
scenario('playtest_dragons.yml', 'xeen.fd04.l4.dragons', "Dragon Tower (FD-04 L4): each floor keeps its dragons",
         steps,
         "# D-32 and D-57 Q29 (written by output/studio_cal/fd04/tools/gen_tests.py): the party (immortal) waits 30 s at\n"
         "# each dragon hall's low opening (256 x 288), floor by floor; then every dragon of that floor is still in its\n"
         "# own hall, on its floor (position within the hall's circle, its feet at least the floor's height), and none of\n"
         "# the 26 stands in the stair's ring.\n")

# ------------------------------------------------------------------------------------------------ exits
steps = start() + [
    {'assert': {'party_position': {'x': 0, 'y': -1280, 'radius': 96, 'z_min': -8, 'z_max': 8}}},
    lua("wait(2); close()"), IMMORTAL,
    lua(f"click({E['evt:way_out']}); wait(0.5)"),
    {'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}},
    {'select_topic': {'match_label': 'OK'}},
    {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
    {'assert': {'map': 'xeen_x7.odm'}},
    lua("log('landing: ' .. party())"),
    {'clear_hostiles': {'radius': 6000}},
    {'advance_runtime': {'seconds': 4.0}},
    lua("log('landing after 4 s: ' .. party())"),
    {'assert': {'party_position': {'x': -17920, 'y': 16384, 'radius': 160, 'z_min': 2500, 'z_max': 2700,
                                   'facing': 1536, 'facing_within': 40}}},
]
scenario('playtest_exit.yml', 'xeen.fd04.l4.exit', 'Dragon Tower (FD-04 L4), out to X7', steps,
         "# The gate out (written by output/studio_cal/fd04/tools/gen_tests.py): the exit preset (aazex117:4) through\n"
         "# the leave window (OK) to X7's named arrival entrance:fd04_door (-17920, 16384, 2592) facing south; measured.\n")
steps = start() + [lua("wait(2); close()"), IMMORTAL] + tp(-1312, 608, 4224) + [
    {'assert': {'party_position': {'x': -1312, 'y': 608, 'radius': 96, 'z_min': 4216, 'z_max': 4232}}},
    lua(f"click({E['evt:hatch']}); wait(0.5)")] + [{'advance_runtime': {'seconds': 0.5, 'present_dialogs': True}},
     {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}] + [
    lua('close()'),
    {'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}},
    lua("close(); wait(0.5); close()"),
    {'assert': {'map': 'xeen_fd04.blv'}},
    {'assert': {'party_position': {'x': -1312, 'y': 608, 'radius': 96, 'z_min': 4216, 'z_max': 4232}}},
    lua(f"click({E['evt:hatch']}); wait(0.5)")] + [{'advance_runtime': {'seconds': 0.5, 'present_dialogs': True}},
     {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}] + [
    {'select_topic': {'match_label': 'OK'}},
    {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
    {'assert': {'map': 'xeen_x9.blv'}},
    lua("log('landing: ' .. party())"),
    {'advance_runtime': {'seconds': 4.0}},
    lua("log('landing after 4 s: ' .. party())"),
    {'assert': {'party_position': {'x': 20352, 'y': 17280, 'radius': 160, 'z_min': 1990, 'z_max': 2110}}},
]
scenario('playtest_roof.yml', 'xeen.fd04.l4.roof', 'Dragon Tower (FD-04 L4), the roof hatch up to X9', steps,
         "# The roof (D-57 Q36; written by output/studio_cal/fd04/tools/gen_tests.py): from the roof stair's head\n"
         "# (entrance:x9_clouds) the hatch's own Yes/No (D-66): No stays, Yes moves at once to X9's entrance:fd04_roof\n"
         "# [20352, 17280, 2048]; measured.\n")

# ------------------------------------------------------------------------------------------------ hostility
COUNTS = {11641: 6, 11642: 8, 11643: 6, 11652: 5, 11653: 1, 11282: 10, 11284: 6, 11285: 8, 11152: 4, 11612: 6}
steps = start() + [
    {'console': {'line': 'arena trace on'}},
    {'advance_runtime': {'seconds': 10}},
    lua("close()"),
    {'assert': {'party_position': {'x': 0, 'y': -1280, 'radius': 96, 'z_min': -8, 'z_max': 8}}},
    {'assert': {'ai_trace': {'event': 'target', 'target': 'party', 'max_count': 0, 'report': True}}},
    IMMORTAL,
] + tp(-1312, 608, 4224) + [
    {'console': {'line': 'arena trace on'}},
    {'advance_runtime': {'seconds': 10}},
    {'assert': {'party_position': {'x': -1312, 'y': 608, 'radius': 96, 'z_min': 4216, 'z_max': 4232}}},
    {'assert': {'ai_trace': {'event': 'target', 'target': 'party', 'max_count': 0, 'report': True}}},
] + [{'assert': {'actor_count': {'monster_id': m, 'hostile': True, 'min': n, 'max': n}}} for m, n in COUNTS.items()] + [
    {'assert': {'actor_count': {'monster_id': 11923, 'hostile': False, 'min': 1, 'max': 1}}},
    {'assert': {'actor_count': {'monster_id': 11923, 'hostile': True, 'max': 0}}},
] + tp(0, 6900, -1792) + [
    {'clear_hostiles': {'radius': 3000}},
    {'console': {'line': 'arena trace on'}},
    {'spawn_actor': {'monster_id': 11282, 'x': -300, 'y': 6800, 'z': -1792}},
    {'spawn_actor': {'monster_id': 11152, 'x': 300, 'y': 6800, 'z': -1792}},
    {'spawn_actor': {'monster_id': 11612, 'x': 0, 'y': 7200, 'z': -1792}},
    {'advance_runtime': {'seconds': 12}},
    {'assert': {'ai_trace': {'event': 'target', 'target': 'actor', 'max_count': 0, 'report': True}}},
    {'assert': {'ai_trace': {'actor_index': 'last', 'event': 'target', 'target': 'party', 'min_count': 1}}},
]
scenario('playtest_hostility.yml', 'xeen.fd04.l4.hostility', 'Dragon Tower (FD-04 L4): quiet arrivals, every monster '
         'hostile, Alister peaceful, no fights among them', steps,
         "# Hostility (written by output/studio_cal/fd04/tools/gen_tests.py): nothing targets the party for 10 s at\n"
         "# entrance:x7_gate (D-11.3, D-57 'quiet gate hall') nor on the roof stair's head (entrance:x9_clouds); the 60\n"
         "# placed monsters hostile, Alister peaceful; a lich, a knight and an Autobot spawned together go for the party,\n"
         "# never for each other.\n")
print('written 9 playtests; Alister', ALISTER, 'dragons', len(DRAGONS))
