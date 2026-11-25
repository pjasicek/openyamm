#!/usr/bin/env python3
"""Writes X6's playtest.yml (the walk) from the built map (A5, 2026-11-20; D3's gen_walk.py).

    gen_walk.py <project L4> <build folder> <asset root>

House doors from build.json, event numbers from ids.lock.yml, ground heights from the map's export, actor indices of
A4's NPCs from the built scene. A house door whose house A4 has not written into the root's house_data.txt yet (x6.yml
is still `planned`) is clicked and its event checked without the house screen; the walk says so. Dungeons not
installed are clicked for their sealed lines.

Route: a new game at Sphinx Wells (the build's start): Old Ibb's well, the tavern, the caravans, the two homes; the
oasis fountain twice (once per character); the caravan cairn twice (x6.caravan_cairn, then _again); the obelisk; the
Sphinx's door without and with the Jewelled Amulet (q-c9.door, then sealed), the hoard mound; Arie; the cliff path
walked up to Castle Basenji's gate ("Castle Basenji.  Enter?", sealed); the Waters of Great Power; the Air Reflector
before M36; the Shrine of Energy; Saul and his urn; the Southern Sphinx without Roland's amulet, then with it into FD-02 and
out by both its exits; the Well of Accuracy;
the sun stones twice; the Summer Druid; the coach yard from inside (Gorm's refusal, the coach house, the arena gate),
then from the desert side (x6.warzone_gate opens it, the party walks in, after a reload it stays open); the east edge
to X4 and X4's west edge back, the south edge to X5 and X5's north edge back.
"""
import json
import math
import os
import subprocess
import sys

import yaml

P, B, ROOT = sys.argv[1], sys.argv[2], sys.argv[3]
M = 'xeen_x6.odm'
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run(['openyamm-studio/build-xeen/oymap', 'export', os.path.join(B, M), '--out', exp_path], check=True,
               stdout=subprocess.DEVNULL)
_m = json.load(open(exp_path))['map']
hm = _m['terrain']['height_map']
ids = yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))
ev = dict(ids['events'])
scene = yaml.load(open(os.path.join(B, 'xeen_x6.scene.yml')), Loader=yaml.CSafeLoader)
npc_actor = {a['npc_id']: a['actor_index'] for a in scene['initial_state']['actors'] if a.get('npc_id')}
_hd = os.path.join(ROOT, 'worlds/xeen/data_tables/house_data.txt')
HOUSES = {int(l.split('\t')[0]) for l in open(_hd, encoding='latin-1') if l.split('\t')[0].isdigit()}
_sp = open(os.path.join(ROOT, 'worlds/xeen/data_tables/edge_spans.yml')).read()
EDGES = 'map: xeen_x6.odm' in _sp


def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))


def ground(X, Y):
    x = X / 512.0 + 64
    y = 64 - Y / 512.0
    i, j = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - i, y - j

    def h(a, b):
        a = max(0, min(127, a))
        b = max(0, min(127, b))
        return hm[b * 128 + a] * 32
    return round(h(i, j) * (1 - fx) * (1 - fy) + h(i + 1, j) * fx * (1 - fy) + h(i, j + 1) * (1 - fx) * fy
                 + h(i + 1, j + 1) * fx * fy)


doors = {b['id']: b for b in build['buildings']}
steps = []
add = steps.append


def walk(X, Y, note=None, timeout=120, radius=160, z=None):
    if note:
        add({'note': note})
    add({'walk_to': {'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'z_tolerance': 600, 'radius': radius,
                     'timeout_seconds': timeout, 'clear_hostiles': 3000, 'close_dialogs': True}})


def walkc(x, y, note=None, timeout=120, z=None):
    walk(*W(x, y), note=note, timeout=timeout, z=z)


def face(X, Y, yaw, pitch=0.0, z=None, m=M):
    add({'set_pose': {'map': m, 'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'yaw': round(yaw, 4),
                      'pitch': pitch}})
    add({'advance_runtime': {'seconds': 0.5}})


def go(x, y, note):
    add({'note': note})
    face(*W(x, y), 0.0)
    add({'clear_hostiles': {'radius': 4000}})


def close():
    add({'play_lua': {'source': 'wait(0.3); close(); wait(0.3)'}})


def house(bid):
    b = doors[bid]
    hid = b['house']
    dx, dy, dz = b['door']
    nx, ny = b['normal']
    sx, sy = round(dx + nx * 300), round(dy + ny * 300)
    add({'note': '%s (%s, house %d): before its door, open it' % (b['title'], bid, hid)})
    face(sx, sy, math.atan2(-ny, -nx), z=max(ground(sx, sy), dz))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    if hid not in HOUSES:
        add({'note': "house %d is not in house_data.txt yet (A4: x6.yml is still planned): the door's event ran" % hid})
        close()
    elif '_houses#' in bid:
        add({'note': "a residence of one person opens that person's talk (MM7's rule), not the house screen"})
        add({'assert': {'dialog': {'active': True}}})
        add({'press_action': {'action': 'cancel_dialog'}})
        add({'advance_runtime': {'seconds': 0.3}})
    else:
        # F1 (merge point 40): a house whose proprietor is its only resident opens straight on his talk
        add({'assert': {'dialog': {'active': True}}})
        add({'press_action': {'action': 'cancel_dialog'}})
        add({'advance_runtime': {'seconds': 0.3}})


def window(text=None):
    """F16 (A5 s29): the standard entrance window (its trans.txt line or "Do you wish to enter"), OK."""
    add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
    add({'assert': {'dialog': dict({'active': True, 'action_label_present': 'OK'},
                                   **({'text_contains': text} if text else {}))}})
    add({'select_topic': {'match_label': 'OK'}})


def asked(eid, prompt, note):
    """F16 / D-90 (A5 s29): the entrance window (its trans.txt line) asks, not the map's own Yes/No: Close stays on
    the map, then the window again and OK (the caller checks the move)."""
    add({'note': note + ': Close stays'})
    for label in ('Close', 'OK'):
        add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev[eid]}})
        add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
        add({'assert': {'dialog': {'active': True, 'text_contains': prompt, 'action_label_present': 'OK'}}})
        add({'select_topic': {'match_label': label}})
        if label == 'Close':
            add({'advance_runtime': {'seconds': 0.5}})
            add({'assert': {'map': M}})
            add({'assert': {'dialog': {'active': False}}})


def event(eid, note, dialog=True, check=None, answer=None, prompt=None):
    add({'note': note})
    if answer:
        add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev[eid]}})
        if prompt:   # the prompt's own text on screen (D-65 B1: one prompt, no message before it)
            add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
            add({'assert': {'dialog': {'active': True, 'text_contains': prompt}}})
        add({'answer_input': {'text': answer}})
        add({'advance_runtime': {'seconds': 0.5}})
    else:
        add({'execute_event': {'id': ev[eid]}})
        add({'advance_runtime': {'seconds': 0.5}})
    if dialog:   # F13 (A5 s29): a touch's text is a status line, a note or a choice's answer a window: either
        add({'play_lua': {'source': "local s = status(); local w = close(); wait(0.3); "
                                    "if s == '' and not w then error('no text shown') end"}})
    if check:
        add({'play_lua': {'source': check}})


def npc(npc_id, at, note):
    walkc(*at, note=note, timeout=90)
    add({'interact_actor': {'actor_index': npc_actor[npc_id]}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True}}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})


_ms = open(os.path.join(ROOT, 'worlds/xeen/data_tables/map_stats.txt'), encoding='latin-1').read()


def live(stem):
    """The dungeon is installed in the root and has its map_stats row: the door leads in (places.live)."""
    return os.path.exists(os.path.join(ROOT, 'worlds/xeen/maps', stem)) and ('\t%s\t' % stem) in _ms


def dungeon_event(stem, name):
    """The event number of `-- evt:<name>` in the dungeon's installed Lua (its way out)."""
    lines = open(os.path.join(ROOT, 'worlds/xeen/events/maps', stem.replace('.blv', '.lua'))).read().splitlines()
    i = lines.index('-- %s' % name)
    return int(lines[i + 1].split('(')[1].split(',')[0])


def arrival_of(stem, name):
    sy = yaml.safe_load(open(os.path.join(ROOT, 'worlds/xeen/maps', stem.replace('.blv', '.studio.yml'))))
    return next(a['at'] for a in sy['arrivals'] if a['name'] == name)


def into_and_back(stem, arrival, exit_name, back, note):
    """The door's move (already clicked) lands on the dungeon's named arrival; its way out brings the party back to
    `back` (x, y, z) on X6."""
    at = arrival_of(stem, arrival)
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': stem}})
    add({'assert': {'party_position': {'x': at[0], 'y': at[1], 'radius': 300, 'z_min': at[2] - 80,
                                       'z_max': at[2] + 160}}})
    add({'note': note})
    add({'execute_event': {'id': dungeon_event(stem, exit_name)}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': back[0], 'y': back[1], 'radius': 300, 'z_min': back[2] - 120,
                                       'z_max': back[2] + 200}}})


def cross(to_map, out_cell, start, note, arrive, m=M):
    """Walk over an edge (out_cell beyond the box) and answer the travel dialog; check the arrival."""
    add({'note': note})
    add({'walk_to': {'x': W(*out_cell)[0], 'y': W(*out_cell)[1], 'z': start[2], 'z_tolerance': 900, 'radius': 128,
                     'timeout_seconds': 90, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': to_map}})
    add({'assert': {'party_position': {'x': arrive[0], 'y': arrive[1], 'radius': 600}}})


s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'assert': {'party_position': {'x': s['x'], 'y': s['y'], 'radius': 128}}})
# ---------------------------------------------------------------- Sphinx Wells
event('evt:thing:wells_well', "Old Ibb's well (xeen/aaze0001:4)", dialog=False)
for bid in ('building:x6_tavern', 'building:x6_stables', 'building:x6_houses#1', 'building:x6_houses#2'):
    house(bid)
# ---------------------------------------------------------------- the oasis
go(46.4, 61.8, 'The oasis fountain: +2 Endurance once per character, then its plain line')
event('evt:thing:oasis_fountain', 'The oasis fountain (player bit 11330)', dialog=False)
event('evt:thing:oasis_fountain', 'The oasis fountain again: "It has given you all it will."', dialog=False)
# ---------------------------------------------------------------- the desert road: the cairn, the obelisk, the Sphinx
go(96.0, 58.6, 'The caravan cairn (x6.caravan_cairn, once per character a day)')
event('evt:thing:caravan_cairn', "A stone for luck: A3's x6.caravan_cairn")
event('evt:thing:caravan_cairn', "The same day: A3's x6.caravan_cairn_again")
go(75.8, 52.0, 'The obelisk on its red knoll (obelisks.x6)')
event('evt:thing:obelisk', 'The obelisk (obelisks.x6: THE)', check='if not qbit(115045) then error("cloud_6 not set") end')
walkc(81.0, 61.0, 'Along the road to the Sphinx fork', timeout=90)
walkc(82.0, 52.0, 'Up the Sphinx track', timeout=90)
walkc(82.0, 46.4, 'Into the forecourt, before the paws', timeout=90)
# D-89 (A5 s29): the Sphinx is open to all; no amulet (12317 retired)
if live('xeen_xd15.blv'):
    add({'note': "With the amulet: q-c9.door (sets 112180), its status line on X6 and xeen_sphinx_stir; no move"})
    add({'play_lua': {'source': 'status(); click(%d); wait(0.5); local s = status(); if not string.find(s, '
                                '"slides aside", 1, true) then error("no q-c9.door line: " .. s) end; '
                                'if not qbit(112180) then error("q-c9.entered not set") end'
                                % ev['evt:door:thing:northern_sphinx']}})
    add({'advance_runtime': {'seconds': 1.0}})
    add({'assert': {'map': M}})
    add({'assert': {'dialog': {'active': False}}})
    add({'note': 'The door again, open: into XD-15 at entrance:x6_paws'})
    add({'execute_event': {'id': ev['evt:door:thing:northern_sphinx']}})
    window('paws the size of houses')
    into_and_back('xeen_xd15.blv', 'entrance:x6_paws', 'evt:exit_e', (9216, 9728, 1408),
                  "XD-15's way out (evt:exit_e) back to X6 before the Sphinx's breast")
    add({'play_lua': {'source': 'if not qbit(112180) then error("q-c9.entered not set") end'}})
    add({'note': 'The door again, now open: no second hook run, straight in (the bit 112180)'})
    add({'execute_event': {'id': ev['evt:door:thing:northern_sphinx']}})
    window('paws the size of houses')
    into_and_back('xeen_xd15.blv', 'entrance:x6_paws', 'evt:exit_w', (9216, 9728, 1408),
                  "XD-15's other way out (evt:exit_w) back to X6")
else:
    event('evt:door:thing:northern_sphinx', 'With the amulet: q-c9.door (sets 112180), then sealed until XD-15 is '
          'installed', check='if not qbit(112180) then error("q-c9.entered not set") end')
event('evt:thing:cloud_hoard', 'The mound between the paws (obelisks.cloud_hoard): silent without the seven words '
      '(A3: the hook has no fail text)', dialog=False)
# ---------------------------------------------------------------- Arie, the cliff path, Castle Basenji
npc(4608, (46.4, 45.8), "Arie at her camp below the cliff (Q-C8)")
add({'note': 'Up the cliff path to the castle gate (walked: the path must hold)'})
for x, y in ((48.4, 44.2), (50.5, 42.6), (53.0, 41.1), (50.4, 39.4), (46.8, 38.0), (42.6, 37.2), (39.4, 36.6)):
    walkc(x, y, timeout=90)
add({'assert': {'party_position': {'x': W(39.4, 36.6)[0], 'y': W(39.4, 36.6)[1], 'radius': 400, 'z_min': 2400}}})
walkc(38.0, 34.2, "Before Castle Basenji's gate on the terrace", timeout=60)
if live('xeen_xd14.blv'):
    asked('evt:door:thing:castle_basenji', 'a dog howls',
          '"Castle Basenji. Enter?" (xeen/aaze0001:19) after the look, Yes/No buttons (D-72); Yes into XD-14 at '
          'entrance:x6_gate')
    into_and_back('xeen_xd14.blv', 'entrance:x6_gate', 'evt:exit_left', (-13312, 15104, 2592),
                  "XD-14's gate (evt:exit_left) back to X6 on the terrace before the gatehouse")
else:
    event('evt:door:thing:castle_basenji', '"Castle Basenji.  Enter?" (xeen/aaze0001:19): Yes, then sealed until '
          'XD-14', answer='Yes', prompt='Castle Basenji. Enter?')
go(31.4, 35.0, 'The Waters of Great Power on the heights')
event('evt:thing:waters_power', 'The Waters of Great Power (+200 hit points, once per character a day)',
      dialog=False)
go(27.4, 27.6, 'The Air Reflector on the rock spit where the rims meet')
event('evt:thing:air_reflector', 'The Air Reflector, a click (D-144): before M36 the hook\'s fail text on the status '
      'line', dialog=False,
      check='local s = tostring(status())\n'
            'if not string.find(s, "cold and silent", 1, true) then error("status line: " .. s) end\n'
            'if qbit(111740) then error("the Reflector set its bit before M36") end')
# ---------------------------------------------------------------- the west: the shrine, Saul, the Southern Sphinx
go(29.0, 55.2, 'The Shrine of Energy by the west rim')
# D-144 (F69b, X6 p5): a click, its line on the status line (the source's "Pray?" was a free Yes/No)
event('evt:thing:shrine_energy', 'The Shrine of Energy (xeen/aaze0001:0), a click: +5 Air resistance once',
      dialog=False,
      check='local s = tostring(status())\n'
            'if not string.find(s, "Lightning runs over your skin", 1, true) then error("status line: " .. s) end')
add({'assert': {'dialog': {'active': False}}})
npc(4602, (32.2, 71.0), "Saul at his hermitage (Meditation)")
event('evt:thing:saul_urn', "Saul's urn (x6.saul_urn)")
go(40.6, 84.0, "Before the Southern Sphinx's breast")
event('evt:door:thing:southern_sphinx', "FD-02 without Roland's amulet: m40.sphinx_door refuses")
if live('xeen_fd02.blv'):
    # 18th session: FD-02 installed (A7); the door moves to its entrance:x6_door, its exits back to X6's
    # entrance:fd02_door (FD-02's exits still name the raw point (-12144, -10240, 1536), within the radius)
    back = next(a['at'] for a in build['named_arrivals'] if a['name'] == 'entrance:fd02_door')
    add({'grant_item': {'item_id': 12372, 'member_index': 0}})
    add({'note': "With Roland's amulet: m40.sphinx_door's line, into FD-02 at entrance:x6_door"})
    add({'execute_event': {'id': ev['evt:door:thing:southern_sphinx']}})
    window('stone jaw')
    into_and_back('xeen_fd02.blv', 'entrance:x6_door', 'evt:exit_l', tuple(back),
                  "FD-02's way out (evt:exit_l) back to X6 before the Southern Sphinx's breast")
    add({'note': 'The door again: into FD-02, out by its other way (evt:exit_r)'})
    add({'execute_event': {'id': ev['evt:door:thing:southern_sphinx']}})
    window('stone jaw')
    into_and_back('xeen_fd02.blv', 'entrance:x6_door', 'evt:exit_r', tuple(back),
                  "FD-02's other way out (evt:exit_r) back to X6")
# ---------------------------------------------------------------- the south: the well, the sun stones, the druid
go(52.0, 93.2, 'The Well of Accuracy by the steppe road')
event('evt:thing:well_accuracy', 'The Well of Accuracy (+10 Accuracy until tomorrow)', dialog=False)
event('evt:thing:well_accuracy', 'Again the same day: "You have drunk your fill of this well today."', dialog=False)
go(69.0, 101.4, 'The sun stones on their rise')
event('evt:thing:sun_stones', "The sun stones: +10 Fire resistance and A3's x6.sun_stones")
event('evt:thing:sun_stones', "The same day: A3's x6.sun_stones_again")
npc(4601, (69.0, 91.2), 'The Summer Druid in her grove (Q-C1)')
# ---------------------------------------------------------------- the coach yard (D-8.1)
go(86.4, 96.4, "Inside the coach yard (the warzone_coach arrival), as a coach party")
event('evt:thing:yard_gate_inner_n', "The desert gate from the yard: Gorm's gate_line (x6.warzone_gate_open)")
house('building:warzone_coach')
add({'note': 'The arena gate (XD-20)'})
face(*W(87.9, 95.0), 0.0)
if live('xeen_xd20.blv'):
    # 13th session: A2's row 9121; XD-20's yard door (evt:yard_l) back to X6 before the arena gate
    asked('evt:door:thing:arena_gate', 'crowd roars',
          '"Enter the War Zone?" (xeen/aaze0006:4) after the look, Yes/No buttons (D-72); Yes into XD-20 at '
          'entrance:x6_yard')
    into_and_back('xeen_xd20.blv', 'entrance:x6_yard', 'evt:yard_l', (12288, -15872, 1504),
                  "XD-20's yard door (evt:yard_l) back to X6 before the arena gate")
else:
    event('evt:door:thing:arena_gate', '"Enter the War Zone?" (xeen/aaze0006:4): Yes, then sealed until XD-20',
          answer='Yes', prompt='Enter the War Zone?')
go(80.6, 96.0, 'Outside the yard on the desert side')
event('evt:thing:yard_gate_outer_n', "From the desert side the bar lifts: A3's x6.warzone_gate (116100)",
      check='if not qbit(116100) then error("x6.warzone_gate not set") end')
walkc(85.6, 96.0, 'Through the open gate into the yard', timeout=60)
add({'assert': {'party_position': {'x': W(85.6, 96.0)[0], 'y': W(85.6, 96.0)[1], 'radius': 400}}})
add({'load_map': {'map': M}})
add({'advance_runtime': {'seconds': 1.0}})
go(80.6, 96.0, 'After a reload the gate stays open (evt:yard_gate_state)')
walkc(85.6, 96.0, 'Through the gate without a click', timeout=60)
add({'assert': {'party_position': {'x': W(85.6, 96.0)[0], 'y': W(85.6, 96.0)[1], 'radius': 400}}})
# ---------------------------------------------------------------- the edges
if EDGES:
    import yaml as _y
    pr = _y.safe_load(open(os.path.join(P, 'project.yml')))
    nb = {n['id']: n for n in pr['neighbours']}
    east, south = nb['edge:east']['arrival'], nb['edge:south']['arrival']
    go(104.0, 60.0, 'The desert road east to the edge: X4')
    cross('xeen_x4.odm', (111.5, 60.0), (0, 0, ground(*W(108, 60))), 'East edge: travel to X4 Burlock Savannah',
          east)
    add({'note': "On X4's west road: west over its edge back to X6 (the scratch root's edge_spans row)"})
    add({'walk_to': {'x': W(16.5, 60.0)[0], 'y': W(16.5, 60.0)[1], 'z': east[2], 'z_tolerance': 900, 'radius': 128,
                     'timeout_seconds': 90, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': W(107, 60)[0], 'y': W(107, 60)[1], 'radius': 600}}})
    go(50.0, 104.0, 'The steppe road south to the edge: X5')
    cross('xeen_x5.odm', (50.0, 111.5), (0, 0, ground(*W(50, 108))), 'South edge: travel to X5 Winterkill Tundra',
          south)
    add({'note': "On X5's steppe road: north over its edge back to X6"})
    add({'walk_to': {'x': W(50.0, 16.5)[0], 'y': W(50.0, 16.5)[1], 'z': south[2], 'z_tolerance': 900, 'radius': 128,
                     'timeout_seconds': 90, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': W(50, 107)[0], 'y': W(50, 107)[1], 'radius': 600}}})
else:
    add({'note': "X6's edge rows are not in this root (the orchestrator's edge_spans): the edges are passed by"})

doc = {'id': 'xeen.x6.walk', 'title': 'X6 Desert of the Sphinx: every door, the hooks, the yard gate and both edges',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/x6/tools/gen_walk.py from the built map (A5, 2026-11-20).\n')
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'houses in the root', len(HOUSES & {b.get('house') for b in build['buildings']}),
      'edges', EDGES)
