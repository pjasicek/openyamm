#!/usr/bin/env python3
"""Writes D1's playtest.yml (the walk) from the built map: event numbers from ids.lock.yml, ground heights from the
map's export, house doors from build.json, NPC actors from the scene.
Usage: gen_walk.py <project L4> <build folder>
The walk: a new game on Castleview square (the M14 arrival text); the mirror and Lyle's bench, the Drawkcab sign, the
jail window, the runaway chest; Public Storage's numbered and lettered chests (q-d4); Ellinger's door refused without
Nadia's key; both gates refused outside without a pass; D-30 from the temple without a pass: each inner leaf lets the
party out at its gate's point with m14.let_out's status line, the outer leaves refuse, Justine's pass bought, in by the north gate
(m14.gate: 2,000 XP, entered, the inn's bit), a save and load, both gates open from inside and walked through both
ways; the notice, Joe's sign, the burrow; the pyramid; the Western Tower's front door
(refused, then with the key from outside: q-d6.tower_opened) and the heretics' rope; the grove rope (refused); the
obelisk; Kalindra's gate (out of phase); the melons; the Well of Might; the Sardaj camp (peaceful, then burnt: the
Sardaj hostile); the outfall grate (barred); the gemsmiths' adit; Luna, Joe, Justine and Yog's talk.
Houses are opened when A4's house rows for D1 are in the world (4451+). At the end, each dungeon door that is live:
the hatch into DD-01 and out by its ladder, the outfall (unbarred, 117001) into DD-01 and out, Ellinger's door (with
the key) into DD-02 and out, the gemsmiths' adit into DD-10A and out, Kalindra's stage 1 (the phase sound's map variable) and its restored gate
into DD-03 and out, each landing on D1's return point; last the burrow into DD-04."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import math
import os
import subprocess
import sys
import yaml

P, B = sys.argv[1], sys.argv[2]
ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..')
WORLD = os.path.join(ROOT, 'assets_dev/worlds/xeen')
M = 'xeen_d1.odm'
HOUSES_LIVE = any(l.startswith('4451\t') for l in open(os.path.join(WORLD, 'data_tables/house_data.txt')))
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run([os.path.join(ROOT, 'openyamm-studio/build-xeen/oymap'), 'export', os.path.join(B, M), '--out',
                exp_path], check=True, stdout=subprocess.DEVNULL)
hm = json.load(open(exp_path))['map']['terrain']['height_map']
ev = dict(yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))['events'])
scene = yaml.safe_load(open(os.path.join(B, 'xeen_d1.scene.yml')))
npc_actor = {a['npc_id']: a['actor_index'] for a in scene['initial_state']['actors'] if a.get('npc_id')}
Q = {'world.inn_castleview': 119021, 'm14.started': 111280, 'm14.entered': 111281, 'q-d4.numbers_closed': 113081, 'q-d4.letters_closed': 113082,
     'q-d6.tower_opened': 113125, 'q-d6.rope_climbed': 113121, 'q-d9.melons_south': 113182,
     'q-d12.camp_burned': 113244, 'obelisks.dark_1': 115050, 'q-d1.started': 113020}
ITEM = {'pass': 12330, 'ellinger_key': 12333, 'west_tower_key': 12338, 'melon': 12343}
TOWN_H = 1150
# a dungeon door goes into its map once the BLV is installed (gen.py DUNGEON): walked at the end, as it leaves D1
DD04_LIVE = os.path.exists(os.path.join(WORLD, 'maps/xeen_dd04.blv'))
DD01_LIVE = os.path.exists(os.path.join(WORLD, 'maps/xeen_dd01.blv'))
DD02_LIVE = os.path.exists(os.path.join(WORLD, 'maps/xeen_dd02.blv'))
DD03_LIVE = os.path.exists(os.path.join(WORLD, 'maps/xeen_dd03.blv'))
KAL_SHOWN_VAR = 'kalindra_stage_shown'   # gen.py's named map variable: the Kalindra stage last shown on D1

def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))

def ground(X, Y):
    x = X / 512.0 + 64
    y = 64 - Y / 512.0
    i, j = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - i, y - j
    def h(a, b):
        a = max(0, min(127, a)); b = max(0, min(127, b))
        return hm[b * 128 + a] * 32
    return round(h(i, j) * (1 - fx) * (1 - fy) + h(i + 1, j) * fx * (1 - fy) + h(i, j + 1) * (1 - fx) * fy
                 + h(i + 1, j + 1) * fx * fy)

steps = []
add = steps.append

def face(X, Y, yaw, z=None):
    add({'set_pose': {'map': M, 'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'yaw': round(yaw, 4),
                      'pitch': 0.0}})
    add({'advance_runtime': {'seconds': 0.5}})

def jump(x, y, note, yaw=0.0, z=None):
    add({'note': note + ' (by teleport)'})
    face(*W(x, y), yaw, z=z)

def close():
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})

sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a6/s32')
import hookwin    # s32: D-90 made most hooks status lines; an event whose hooks all say so opens no window


def event(eid, note, dialog=True, check=None, text=None, fails=False):
    add({'note': note})
    add({'execute_event': {'id': ev[eid]}})
    add({'advance_runtime': {'seconds': 0.5}})
    fails = fails or any(w in note.lower() for w in ('refus', 'without', 'no pass', 'not yet', 'sealed', 'before '))
    if dialog and hookwin.status_only(os.path.join(B, 'xeen_d1.lua'), ev[eid], passes=not fails):
        dialog = False
    if dialog:
        a = {'active': True}
        if text:
            a['text_contains'] = text
        add({'assert': {'dialog': a}})
        close()
    if check:
        add({'play_lua': {'source': check}})

def ask(eid, note, answer, dialog_after=True, check=None, question=None):
    add({'note': note})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev[eid]}})
    if question:    # D-72 rule 3: the prompt's own text on screen before the answer (Yes/No buttons)
        add({'assert': {'dialog': {'active': True, 'text_contains': question}}})
    add({'answer_input': {'text': answer}})
    add({'advance_runtime': {'seconds': 0.5}})
    if dialog_after:
        add({'assert': {'dialog': {'active': True}}})
    add({'play_lua': {'source': 'close(); wait(0.3)'}})
    if check:
        add({'play_lua': {'source': check}})

def bit(name, on=True):
    return ('if %sqbit(%d) then error("%s (%d) %s") end'
            % ('not ' if on else '', Q[name], name, Q[name], 'not set' if on else 'set'))

def at(x, y, r=200):
    X, Y = W(x, y)
    add({'assert': {'party_position': {'x': X, 'y': Y, 'radius': r}}})

def talk(npc, note, near):
    jump(*near, note)
    add({'interact_actor': {'actor_index': npc_actor[npc]}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True}}})
    close()

def into_and_out(eid, note, dmap, arrive, out_event, back, pre=None):
    """A D1 door into a dungeon, the dungeon's arrival asserted, out by its exit (the game's leave window, OK) and
    D1's return point asserted."""
    add({'note': note})
    add({'execute_event': {'id': ev[eid]}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})    # F16: the entrance window
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': dmap}})
    add({'advance_runtime': {'seconds': 2, 'present_dialogs': True}})
    add({'play_lua': {'source': 'close()'}})
    add({'assert': {'party_position': {'x': arrive[0], 'y': arrive[1], 'radius': 96, 'z_min': arrive[2] - 16,
                                       'z_max': arrive[2] + 16}}})
    add({'execute_event': {'id': out_event}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': back[0], 'y': back[1], 'radius': 128, 'z_min': back[2] - 60,
                                       'z_max': back[2] + 160}}})


s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'assert': {'party_position': {'x': s['x'], 'y': s['y'], 'radius': 160}}})
add({'note': "M14: the arrival text (a timer, once)"})
add({'advance_runtime': {'seconds': 4}})
add({'assert': {'dialog': {'active': True, 'text_contains': 'You step out of the pyramid'}}})
close()
add({'play_lua': {'source': bit('m14.started')}})
# ---------------------------------------------------------------- the square and the lanes
event('evt:thing:cv_mirror', "The Mirror of Castleview: asleep until Kalindra's stage 4")
event('evt:part:thing:lyle_bench/bench', "Lyle's bench beside the mirror (a status line)", dialog=False)
event('evt:thing:drawkcab_sign', 'The Drawkcab sign (q-d3.drawkcab_sign)', text='Palindrome')
event('evt:part:thing:jail_window/bars', "The jail's back window: Q-D2 not started (q-d2.jail_window's fail text)")
event('evt:thing:runaway_chest', 'The runaway chest scuttles off (m17.runaway_chest)', text='brass feet')
NUM = [3, 7, 1, 9, 5, 2, 8, 4, 6]
add({'note': "Public Storage's numbered chests, shut 1 to 9 in order (q-d4.number_chests)"})
for n in range(1, 10):
    eid = 'evt:part:thing:number_chest_%d/lid' % (NUM.index(n) + 1)
    event(eid, 'Chest %d' % n, dialog=(n == 9))
add({'play_lua': {'source': bit('q-d4.numbers_closed')}})
LET = [5, 2, 8, 0, 6, 3, 7, 1, 4]
add({'note': "The lettered chests, P-I-T-C-H-F-O-R-K (q-d4.letter_chests)"})
def status_has(text):
    return ("wait(0.2); local s = status(); if not string.find(s, %r, 1, true) then error('status: ' .. s) end"
            % text)
# A6 s27: a wrong lid says so and opens the row again; each right lid says it drops shut (the numbered row's lines)
event('evt:part:thing:letter_chest_%d/lid' % (LET.index(1) + 1), 'Letter I first: the wrong order', dialog=False,
      check=status_has('A letter on the lid reads: I. It will not shut. All nine lids spring open again.'))
for n in range(9):
    event('evt:part:thing:letter_chest_%d/lid' % (LET.index(n) + 1), 'Letter %s' % 'PITCHFORK'[n], dialog=(n == 8),
          check=None if n == 8 else status_has('A letter on the lid reads: %s. The lid drops shut.' % 'PITCHFORK'[n]))
    if n == 0:
        event('evt:part:thing:letter_chest_%d/lid' % (LET.index(0) + 1), 'Letter P again: already shut',
              dialog=False, check=status_has('The P chest is shut.'))
add({'play_lua': {'source': bit('q-d4.letters_closed')}})
event('evt:door:thing:ellinger_tower', "Ellinger's Tower (D-89: no lock): the entrance window with row 5029, Close",
      dialog=False)
add({'assert': {'dialog': {'active': True, 'text_contains': 'Not now', 'action_label_present': 'Close'}}})
add({'select_topic': {'match_label': 'Close'}})
add({'advance_runtime': {'seconds': 0.3}})
add({'assert': {'dialog': {'active': False}}})
# ---------------------------------------------------------------- the gates (D-23)
QIN, QOUT = (53.18, 61.45), (51.32, 63.55)

def walk(x, y, note=None, r=160):
    if note:
        add({'note': note})
    X, Y = W(x, y)
    add({'walk_to': {'x': X, 'y': Y, 'z': ground(X, Y), 'z_tolerance': 600, 'radius': r, 'timeout_seconds': 60}})

jump(63, 41.8, 'Outside the north gate, no pass', yaw=-math.pi / 2)
event('evt:thing:north_gate_outer', 'Outside without a pass: m14.gate refuses', text='The gate stays shut')
jump(*QOUT, "Outside the Queen's Gate, no pass", yaw=0.8)
event('evt:thing:queens_gate_outer', "The Queen's Gate refuses too", text='The gate stays shut')
LET_OUT = "The guard unbars the gate and waves you out."   # m14.let_out's status line (A3, evt.StatusText)

def let_out_text():
    add({'play_lua': {'source': 'local t = status() if not string.find(t, "%s", 1, true) then '
                                'error("no let-out line: " .. t) end' % LET_OUT}})
# D-30: a party inside the walls without a pass (death wakes at the temple): the inner leaves let it out (the
# guard's m14.let_out after the move), the outer ones refuse; Justine's pass, in through the north gate (M14: 2,000
# XP, entered and the inn's bit), a save and load, both gates open
jump(69, 60, "At Castleview's temple (castleview_temple), inside the walls, no pass", yaw=math.pi / 2, z=1152)
at(69, 60, 128)
walk(63, 46.4, 'From the temple through the town to the north gate', r=200)
add({'play_lua': {'source': 'status()'}})
event('evt:thing:north_gate_inner', 'The inner north leaf before entry: the party is let out (m14.let_out)',
      dialog=False)
let_out_text()
at(63, 43, 128)
add({'play_lua': {'source': bit('m14.entered', False)}})
event('evt:thing:north_gate_outer', 'Outside again: the outer leaf still asks for a pass', text='The gate stays shut')
jump(*QIN, "Inside the Queen's Gate, no pass", yaw=-2.3)
add({'play_lua': {'source': 'status()'}})
event('evt:thing:queens_gate_inner', "The Queen's Gate's inner leaf before entry: let out at its point",
      dialog=False)
let_out_text()
at(51, 64, 128)
event('evt:thing:queens_gate_outer', "The Queen's Gate's outer leaf refuses", text='The gate stays shut')
add({'note': "A thousand gold for Justine's pass"})
add({'lua_event': {'source': 'AddValue(Gold, 1000)'}})
jump(57, 42.0, 'Justine at her camp outside the north gate', yaw=math.pi / 2)
add({'interact_actor': {'actor_index': npc_actor[4951]}})
add({'advance_runtime': {'seconds': 0.5}})
add({'assert': {'dialog': {'active': True}}})
add({'select_topic': {'match_label': 'Passes'}})
add({'advance_runtime': {'seconds': 0.5}})
close()
add({'play_lua': {'source': 'if not has_item(%d) then error("no pass from Justine") end '
                            'remember("xp0", experience(0))' % ITEM['pass']}})
jump(63, 41.8, 'Outside the north gate with the pass', yaw=-math.pi / 2)
event('evt:thing:north_gate_outer', 'With the pass: m14.gate lets the party in (D-90: the status line)', dialog=False,
      check=(bit('m14.entered') + ' if not qbit(119021) then error("world.inn_castleview (119021) not set") end '
             'local d = experience(0) - recall("xp0") if d < 2000 then error("M14 gate XP " .. d) end '
             'log("M14 gate XP " .. d)'))
walk(63, 46.2, 'In through the open north gate')
add({'note': 'Save and load back: both gates stand open (evt:gates_open)'})
add({'reload': {}})
add({'play_lua': {'source': bit('m14.entered')}})
event('evt:thing:north_gate_inner', 'The inner north leaf after entry: the gate opens, no move', dialog=False)
at(63, 46.2, 200)
walk(63, 42.4, 'Out through the north gate')
walk(63, 46.2, 'And back in')
jump(*QIN, "Inside the Queen's Gate after entry", yaw=-2.3)
event('evt:thing:queens_gate_inner', "The Queen's Gate's inner leaf after entry: open, no move", dialog=False)
walk(*QOUT, "Out through the Queen's Gate")
walk(*QIN, "And back in")
# ---------------------------------------------------------------- outside the north gate
jump(63, 41.5, 'Outside the north gate', yaw=-math.pi / 2)
event('evt:thing:gate_notice', "The Mayor's notice (q-d1.gate_notice: Q-D1 starts)", check=bit('q-d1.started'))
event('evt:thing:joe_sign', "Joe's sign (q-c24.joes_sign)", text='MAPS BY JOE')
if not DD04_LIVE:
    event('evt:thing:dd04_burrow', "The gremlins' burrow (q-d1.court_entrance; DD-04 sealed)", text='THE COURT')
event('evt:part:thing:pyramid/p', 'The travel pyramid without the Sigil: the moons are not aligned',
      text='not aligned')
event('evt:part:thing:rope_bridge_cut_w/post_n', 'The cut rope bridge (q-d1.sabotage)', text='sawn')
event('evt:thing:acid_pond', 'The acid pond bites')
# ---------------------------------------------------------------- the west: the Western Tower, the grove, the gemsmiths
jump(31, 36.2, "Before the Western Tower's front door", yaw=math.pi / 2, z=1600)
event('evt:door:thing:western_tower', 'The front door without the key (q-d6.front_door_outside refuses)',
      text='warded from both sides')
add({'grant_item': {'item_id': ITEM['west_tower_key']}})
event('evt:door:thing:western_tower', 'The front door with the key, from outside: it opens (tower_opened)',
      text='sulky pop', check=bit('q-d6.tower_opened'))
DD05_LIVE = os.path.exists(os.path.join(WORLD, 'maps/xeen_dd05.blv'))
if not DD05_LIVE:
    event('evt:door:thing:western_tower', 'The door again: open (DD-05 sealed, a status line)', dialog=False)
    ask('evt:part:thing:tower_rope/rope', "The heretics' rope: climb (q-d6.tower_rope; DD-05's top sealed)", 'Yes',
        check=bit('q-d6.rope_climbed'), question="near the tower's top. Climb?")
else:
    # DD-05 installed (A8): the front door into entrance:d1_door and out by its exit door (35, open once
    # tower_opened); the rope up to entrance:d1_rope and down by the window (36); each lands at A8's measured points
    into_and_out('evt:door:thing:western_tower', "The Western Tower's front door: into DD-05 (entrance:d1_door) and out",
                 'xeen_dd05.blv', (0, -1536, 0), 35, (-16896, 14848, 1601))
    add({'note': "The heretics' rope (q-d6.tower_rope): climb into DD-05's top floor (entrance:d1_rope) and down again"})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev['evt:part:thing:tower_rope/rope']}})
    add({'assert': {'dialog': {'active': True, 'text_contains': "near the tower's top", 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})     # F16: the entrance window (row 5033), no Yes/No
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd05.blv'}})
    add({'advance_runtime': {'seconds': 2, 'present_dialogs': True}})
    add({'play_lua': {'source': 'close()'}})
    add({'play_lua': {'source': bit('q-d6.rope_climbed')}})
    add({'assert': {'party_position': {'x': 1376, 'y': 1472, 'radius': 96, 'z_min': 1904, 'z_max': 1936}}})
    add({'execute_event': {'id': 36}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': -16896, 'y': 16896, 'radius': 128, 'z_min': 1541, 'z_max': 1761}}})
event('evt:part:thing:grove_rope/rope', "The rope into the sky: m30.grove_rope refuses before m30.done (its fail window)",
      text='takes only the Chosen', fails=True)
if not os.path.exists(os.path.join(WORLD, 'maps/xeen_dd10a.blv')):
    event('evt:thing:dd10a_adit', "The gemsmiths' adit (DD-10 sealed)")
event('evt:thing:west_well', 'The old west well: +10 Personality', dialog=False)
event('evt:thing:edge_stone', 'The Edge Stone', dialog=False)
# ---------------------------------------------------------------- the south-west and the south
event('evt:door:thing:kalindra_gate', 'Castle Kalindra out of phase (m19.ghost_castle)', text='not quite here')
event('evt:thing:obelisk', "The obelisk (obelisks.d1: DIG)", text='DIG', check=bit('obelisks.dark_1'))
event('evt:thing:melon_patch', 'The wild melons (q-d9.melons_south)', text='Monga',
      check=bit('q-d9.melons_south') + ' if not has_item(%d) then error("no melon") end' % ITEM['melon'])
event('evt:thing:might_well', 'The Well of Might: +2 Might', dialog=False)
event('evt:thing:dd01_outfall', 'The outfall grate: barred from inside', text='barred from inside')
# ---------------------------------------------------------------- people and the Sardaj
talk(4956, "Joe at his stall", (66.0, 42.6))
talk(4951, "Justine at her camp", (57.0, 42.0))
talk(4952, "Luna in her grove", (31.4, 62.6))
talk(4953, "Yog in the Sardaj camp (peaceful)", (89.0, 25.2))
add({'assert': {'actor_count': {'monster_id': 11100, 'hostile': True, 'max': 0}}})
ask('evt:thing:sardaj_tent_1', 'The Sardaj tents: destroy (q-d12.camp)', 'Yes', check=bit('q-d12.camp_burned'),
    question='Barbarian camp. Destroy?')
add({'advance_runtime': {'seconds': 1}})
add({'assert': {'actor_count': {'monster_id': 11100, 'hostile': True, 'min': 1}}})
D2_LIVE = os.path.exists(os.path.join(WORLD, 'maps/xeen_d2.odm'))
TRAVEL_LIVE = any(l.startswith('xeen_d1.odm\t') and 'xeen_d2.odm' in l
                  for l in open(os.path.join(WORLD, 'data_tables/outdoor_travels.txt')))
if D2_LIVE and TRAVEL_LIVE:
    jump(106, 60, 'The east road to its end', yaw=0.0)
    add({'note': "Off D1's east edge: the travel prompt (D2, 5 days), accepted; D2's west start (-22016, 2048)"})
    add({'walk_to': {'x': W(111, 60)[0], 'y': W(111, 60)[1], 'z': ground(*W(111, 60)), 'z_tolerance': 600,
                     'radius': 128, 'timeout_seconds': 60, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_d2.odm'}})
    add({'assert': {'party_position': {'x': -22016, 'y': 2048, 'radius': 700}}})
    add({'note': "Back west off D2's west edge: accepted; D1's east start (21504, 2048)"})
    add({'walk_to': {'x': -24576, 'y': 2048, 'z': 992, 'z_tolerance': 900, 'radius': 128, 'timeout_seconds': 60,
                     'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': 21504, 'y': 2048, 'radius': 700}}})
else:
    jump(106, 60, 'The east road to its end', yaw=0.0)
    event('evt:thing:east_road_end', "The road's end: D2 not installed (sealed)")
if HOUSES_LIVE:
    # every house door (A4's rows): a residence of one person opens that person's talk, a shop its house screen,
    # Lucio's Jetty its closed text before m30.done, Brother Reger's door the Drawkcab test (not a member: refused)
    TOWN = yaml.safe_load(open(os.path.join(WORLD, 'source/towns/d1.yml')))
    CLOSED = {h['id']: h['closed_text'] for h in TOWN['houses'] if h.get('opens')}
    ALONE = {h['id']: h['residents'][0] for h in TOWN['houses'] if len(h.get('residents') or []) == 1}
    INN = {h['id'] for h in TOWN['houses'] if h.get('kind') == 'inn'}
    for b in sorted((b for b in build['buildings'] if b.get('house') and b.get('door')), key=lambda b: b['house']):
        if b['house'] in INN:
            # as X1's: the Adventurer's Inn screen holds the world's input headless and has no dialog to close
            add({'note': "The Adventurer's Inn (%d): passed by (its roster screen cannot be closed by a scenario yet)"
                         % b['house']})
            continue
        dx, dy, dz = b['door']
        nx, ny = b['normal']
        sx, sy = round(dx + nx * 300), round(dy + ny * 300)
        add({'note': '%s (house %d, %s): its door' % (b.get('title', ''), b['house'], b['id'])})
        face(sx, sy, math.atan2(-ny, -nx), z=max(ground(sx, sy), dz))
        add({'press_interact': {'expect': {'kind': 'event_target'}}})
        add({'advance_runtime': {'seconds': 0.5}})
        h = b['house']
        if h in CLOSED:
            add({'assert': {'dialog': {'active': True, 'house_dialog': False, 'text_contains': CLOSED[h][:30]}}})
        elif b['id'] == 'building:reger_cell':
            add({'assert': {'dialog': {'active': True, 'text_contains': 'Go visit the monks'}}})
        elif h in ALONE:
            add({'assert': {'dialog': {'active': True, 'source_id': ALONE[h]}}})
        else:
            add({'assert': {'dialog': {'active': True}}})
        close()
if DD01_LIVE:
    jump(66.5 - 0.9, 57.5, 'Beside the iron hatch on the square', yaw=0.0, z=1152)
    into_and_out('evt:thing:dd01_hatch', 'The sewer hatch: down into the Castleview Sewer (DD-01) and up again',
                 'xeen_dd01.blv', (0, -1088, 0), 17, (1024, 3072, 1152))
    add({'setup_shortcut': {'kind': 'set_qbit', 'id': 117001, 'value': True}})
    jump(79.7, 48.0, "Before the outfall grate in the mill gorge", yaw=math.pi, z=832)
    into_and_out('evt:thing:dd01_outfall', 'The outfall grate unbarred (m16.outfall): into DD-01 and out again',
                 'xeen_dd01.blv', (4096, -4864, -512), 18, (8192, 8192, 832))
if DD02_LIVE:
    add({'grant_item': {'item_id': ITEM['ellinger_key']}})
    jump(69.3, 45.9, "Before Ellinger's Tower's door with Nadia's key", yaw=0.0, z=1152)
    into_and_out('evt:door:thing:ellinger_tower', "Ellinger's Tower (m17.tower_door): into DD-02 and out again",
                 'xeen_dd02.blv', (-1216, 640, 0), 17, (2560, 9216, 1152))
if os.path.exists(os.path.join(WORLD, 'maps/xeen_dd10a.blv')):
    jump(45, 24, "Before the gemsmiths' adit in the mine hill", yaw=math.pi / 2, z=1600)
    into_and_out('evt:thing:dd10a_adit', "The gemsmiths' adit: into the Gemstone Mines' west pocket (DD-10A) and out",
                 'xeen_dd10a.blv', (0, 192, 0), 19, (-9728, 20480, 1600))
if DD03_LIVE:
    # Kalindra's stage 1 (m19.stage1, 111381): the phase sound's load event remembers the stage shown (0 until now),
    # the stage events restore stage 1's parts, the restored gate (254) lets the party into DD-03 and out again
    add({'play_lua': {'source': 'if mapvar("%s") ~= 0 then error("stage shown " .. mapvar("%s")) end'
                                % (KAL_SHOWN_VAR, KAL_SHOWN_VAR)}})
    add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111381, 'value': True}})
    add({'note': "Kalindra's stage 1: the load events (phase sound, parts) run again"})
    for e in ['evt:kalindra_phase'] + ['evt:kalindra_%d' % n for n in range(1, 5)]:
        add({'execute_event': {'id': ev[e]}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'play_lua': {'source': 'if mapvar("%s") ~= 1 then error("stage shown not 1: " .. mapvar("%s")) end '
                                'log("kalindra stage shown " .. mapvar("%s"))' % ((KAL_SHOWN_VAR,) * 3)}})
    jump(44.2, 70.0, "Before Castle Kalindra's restored gate (stage 1)", yaw=math.pi, z=1664)
    into_and_out('evt:door:thing:kalindra_gate_restored', "Kalindra's gate (m19.ghost_castle, stage 1): into DD-03 "
                 "(entrance:gate) and out again", 'xeen_dd03.blv', (-1600, 0, 0), 19, (-9728, -3072, 1664))
    add({'play_lua': {'source': 'if mapvar("%s") ~= 1 then error("stage shown not 1 after the return") end'
                                % KAL_SHOWN_VAR}})
if DD04_LIVE:
    # last: the burrow's event shows q-d1.court_entrance's text and moves into DD-04 (the move closes the message)
    jump(68.5, 42.4, "Before the gremlins' burrow under the north wall", yaw=-math.pi / 2)
    add({'note': "The gremlins' burrow (q-d1.court_entrance): into the Gremlin Court (DD-04 installed)"})
    add({'execute_event': {'id': ev['evt:thing:dd04_burrow']}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'THE COURT', 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd04.blv'}})
doc = {'id': 'xeen.d1.walk', 'title': 'D1 Castleview Vale: the town, both gates, the vale',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/d1/tools/gen_walk.py from the built map (A6). Houses opened: %s.\n'
            % ('yes' if HOUSES_LIVE else 'no (A4 rows pending)'))
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'houses', HOUSES_LIVE)
