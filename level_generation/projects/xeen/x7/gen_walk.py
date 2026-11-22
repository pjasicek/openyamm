#!/usr/bin/env python3
"""Writes X7's playtest.yml (the walk) from the built map (A5, 2026-11-20; X6's gen_walk.py).

    gen_walk.py <project L4> <build folder> <asset root>

Event numbers from ids.lock.yml, ground heights from the map's export, Sablewing's actor index from the built scene.
Dungeons not installed (or without a named inside arrival) are clicked for their sealed lines.

Route: a new game at the X1 road (the build's start); the dwarves' watch and its pay chest with the note; Sablewing;
the hot spring and the back gate (barred), the orcs' den; the Shrine of Fire twice (once a day), the Well of Speed twice
(once per character); the orc outpost burnt (x7.orc_outpost, outpost_burned) and its chest; the cairn twice; the
miner's cache; the Gap's warning and the obelisk (cloud_7); down the north track over the black bridge to the Dragon
Cave (sealed); the Volcano Cave and an idol; the cleft (A3's xd17.cleft: the rockfall); the lake track over the
causeway to the island and the Ever-Hot Lava Rock (rock_found); the tower path up the crag to the Dragon Tower's gate
(sealed); the firestone path round the shoulder to the hoard and the Fire Reflector (before M36: no bit); the edges to
X1 and X4 and back when the root's edge_spans has X7's rows.
"""
import json
import math
import os
import subprocess
import sys

import yaml

P, B, ROOT = sys.argv[1], sys.argv[2], sys.argv[3]
M = 'xeen_x7.odm'
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run(['openyamm-studio/build-xeen/oymap', 'export', os.path.join(B, M), '--out', exp_path], check=True,
               stdout=subprocess.DEVNULL)
_m = json.load(open(exp_path))['map']
hm = _m['terrain']['height_map']
ids = yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))
ev = dict(ids['events'])
scene = yaml.load(open(os.path.join(B, 'xeen_x7.scene.yml')), Loader=yaml.CSafeLoader)
npc_actor = {a['npc_id']: a['actor_index'] for a in scene['initial_state']['actors'] if a.get('npc_id')}
_sp = open(os.path.join(ROOT, 'worlds/xeen/data_tables/edge_spans.yml')).read()
SPANS = 'map: xeen_x7.odm' in _sp      # explicit arrival points (else the travel rows' default arrivals)
_tr = [l.split('\t') for l in open(os.path.join(ROOT, 'worlds/xeen/data_tables/outdoor_travels.txt'),
                                     encoding='latin-1')]
_x7 = next((c for c in _tr if c and c[0] == M), [])
EDGES = SPANS or ('xeen_x1.odm' in _x7 and 'xeen_x4.odm' in _x7)


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


steps = []
add = steps.append


def walk(X, Y, note=None, timeout=120, radius=160, z=None):
    if note:
        add({'note': note})
    add({'walk_to': {'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'z_tolerance': 600, 'radius': radius,
                     'timeout_seconds': timeout, 'clear_hostiles': 3000, 'close_dialogs': True}})


def walkc(x, y, note=None, timeout=120, z=None):
    walk(*W(x, y), note=note, timeout=timeout, z=z)


def face(X, Y, yaw, pitch=0.0, z=None):
    add({'set_pose': {'map': M, 'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'yaw': round(yaw, 4),
                      'pitch': pitch}})
    add({'advance_runtime': {'seconds': 0.5}})


def go(x, y, note):
    add({'note': note})
    face(*W(x, y), 0.0)
    add({'clear_hostiles': {'radius': 4000}})


def close():
    add({'play_lua': {'source': 'wait(0.3); close(); wait(0.3)'}})


def window(text):
    """F16 (A5 s29): the standard entrance window shows `text` (its trans.txt line, or "Do you wish to enter"); OK."""
    add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
    add({'assert': {'dialog': {'active': True, 'text_contains': text, 'action_label_present': 'OK'}}})
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


def event(eid, note, dialog=True, check=None, answer=None, prompt=None, chest=False):
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
    if chest:   # the chest screen (and any message before it): escape closes it, as X1's inn roster
        close()
        if chest == 'escape':     # a message closed first, the chest screen still open
            add({'press_action': {'action': 'escape'}})
        add({'advance_runtime': {'seconds': 0.5}})
        close()
    elif dialog:   # F13 (A5 s29): a touch's text is a status line, a note or a choice's answer a window: either
        add({'play_lua': {'source': "local s = status(); local w = close(); wait(0.3); "
                                    "if s == '' and not w then error('no text shown') end"}})
    else:
        close()
    if check:
        add({'play_lua': {'source': check}})


def npc(npc_id, at, note):
    walkc(*at, note=note, timeout=90)
    add({'interact_actor': {'actor_index': npc_actor[npc_id]}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True}}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})


def path(points, note, timeout=90):
    add({'note': note})
    for x, y in points:
        walkc(x, y, timeout=timeout)


s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'assert': {'party_position': {'x': s['x'], 'y': s['y'], 'radius': 128}}})
# ---------------------------------------------------------------- the south slopes
path([(68.6, 100), (66.4, 94.4), (64.6, 88.6), (63.6, 84.0)], 'Up the north road to the dwarves\' watch')
walkc(65.6, 82.5, "Through the watch's gate", timeout=60)
walkc(68.4, 84.4, 'To the pay chest by the south wall', timeout=60)
event('evt:thing:pay_chest', "The pay chest: A3's x7.watch_note (\"The dragons came south ...\") and the chest",
      dialog=False, chest='escape')
path([(65.8, 82.5), (63.4, 83.6), (64.6, 88.6), (66.4, 94.0), (70, 92.5), (73.4, 91.0)],
     "Out by the watch's gate and down to the slope fork, along Sablewing's lane")
event('evt:thing:signpost_slope', 'The slope fork\'s signpost names its four roads')
npc(4720, (74.6, 90.4), 'Sablewing at his cave mouth (D-5.2: Dragon Master)')
go(93.0, 85.2, 'The hot spring in the red rock')
event('evt:thing:hot_spring', 'The hot spring: +150 hit points to every member', dialog=False)
event('evt:thing:hot_spring', 'The same day: "You have soaked enough today."', dialog=False)
go(86.6, 100.0, "Before XD-05's back gate")
event('evt:thing:xd05_gate', 'The back gate before the bar is lifted: barred from within')
if 'xeen_xd05.blv' in open(os.path.join(B, 'xeen_x7.lua')).read():
    # XD-05 names entrance:x7_gate (A7): the gate leads in once the bar is lifted inside (110051); back by its exit
    _lua = open(os.path.join(ROOT, 'worlds/xeen/events/maps/xeen_xd05.lua')).read().splitlines()
    _exit = int(_lua[_lua.index('-- evt:exit_x7') + 1].split('(')[1].split(',')[0])
    _sy = yaml.safe_load(open(os.path.join(ROOT, 'worlds/xeen/maps/xeen_xd05.studio.yml')))
    _at = next(a['at'] for a in _sy['arrivals'] if a['name'] == 'entrance:x7_gate')
    add({'note': "The bar lifted from inside (x1-tam.back_gate, 110051): the gate leads into XD-05's entrance:x7_gate"})
    add({'lua_event': {'source': 'SetQBit(QBit(110051))'}})
    add({'execute_event': {'id': ev['evt:thing:xd05_gate']}})
    window('Do you wish to enter')   # F16: no trans row for a shortcut opened from inside
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_xd05.blv'}})
    add({'assert': {'party_position': {'x': _at[0], 'y': _at[1], 'radius': 300, 'z_min': _at[2] - 80,
                                       'z_max': _at[2] + 160}}})
    add({'note': "XD-05's back gate (evt:exit_x7) out to X7 before the log door"})
    add({'execute_event': {'id': _exit}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': 11776, 'y': -18432, 'radius': 300, 'z_min': 1900, 'z_max': 2200}}})
go(83.15, 102.3, "Before the orcs' stash under their den's overhang (D-91)")
add({'note': "The orcs' stash (level 1): the chest opens at once, no \"Pillage?\" (A5 s31); the look on the status bar"})
add({'execute_event': {'id': ev['evt:thing:den_chest']}})
add({'advance_runtime': {'seconds': 0.5}})
add({'play_lua': {'source': "local s = status(); local w = close(); wait(0.3); "
                            "if not w then error('no chest screen') end; "
                            "if not string.find(s, 'orcs have been living under this overhang', 1, true) then "
                            "error('status: ' .. s) end"}})
close()
go(52.4, 99.4, 'The Shrine of Fire on its knoll')
event('evt:thing:shrine_fire', "The Shrine of Fire: +10 Fire resistance and A3's x7.shrine_fire (player bit 11339)")
event('evt:thing:shrine_fire', "The same day: A3's x7.shrine_fire_again (\"You don't think anyone is listening.\")")
go(28.1, 103.4, 'The Well of Speed')
event('evt:thing:well_speed', "The Well of Speed: +2 Speed once, A3's x7.well_speed (player bit 11338)")
event('evt:thing:well_speed', "Again: A3's x7.well_speed_again")
go(33.0, 88.4, 'The orc outpost')
event('evt:thing:outpost_fire', '"You have found an Orc Outpost. Put it to the torch?" (xeen/aaze0018:3) after the '
      'look, Yes/No buttons (D-72): No leaves it standing', dialog=False, answer='No',
      prompt='You have found an Orc Outpost. Put it to the torch?',
      check='if qbit(116160) then error("No burned the outpost") end')
event('evt:thing:outpost_fire', '"You have found an Orc Outpost. Put it to the torch?" (xeen/aaze0018:3): Yes',
      answer='Yes', prompt='You have found an Orc Outpost. Put it to the torch?', check='if not qbit(116160) then error("x7.outpost_burned not set") end')
event('evt:thing:outpost_fire', "Burnt: A3's else text", dialog=True)
event('evt:thing:outpost_chest', "The orcs' loot (level 1)", dialog=False, chest=True)
go(40.1, 66.2, 'The cairn of the unreturned by the Firestone road')
event('evt:thing:cairn', 'The cairn: +10 Luck to every member until tomorrow', dialog=False)
event('evt:thing:cairn', 'The same day: "You have added your stone today."', dialog=False)
go(44.7, 68.6, "The miner's cache before the adit")
event('evt:thing:miner_cache', "The miner's cache (level 3)", dialog=False, chest=True)
# ---------------------------------------------------------------- the Gap
path([(50, 67.6), (56, 67.2), (61.6, 66.2)], 'Up the Firestone road to the Gap')
event('evt:thing:gap_sign', 'The Gap\'s signpost: "North: Mount Firestone. Dragons. Turn back." (D-40 change 4)')
walkc(63.6, 63.8, "The obelisk on the Gap's north lip", timeout=60)
event('evt:thing:obelisk', 'The obelisk (obelisks.x7: SPHINX)', check='if not qbit(115046) then error("cloud_7 not set") end')
# ---------------------------------------------------------------- the north
path([(61.5, 60), (61, 52), (61, 47), (61, 45.4)], 'Down the north track to the lava fork and the black bridge')
event('evt:thing:signpost_fork', 'The lava fork\'s signpost names its four roads')
walkc(61, 40.6, 'Over the black bridge (the deck holds)', timeout=60)
add({'assert': {'party_position': {'x': W(61, 40.6)[0], 'y': W(61, 40.6)[1], 'radius': 400}}})
path([(59.5, 39), (58, 35), (56.4, 31.6)], 'The tax road to the Dragon Cave')
def inside(key, name):
    sy = yaml.safe_load(open(os.path.join(ROOT, 'worlds/xeen/maps/xeen_%s.studio.yml' % key)))
    return next(a['at'] for a in sy['arrivals'] if a['name'] == name)


def exit_event(key, tag):
    lua = open(os.path.join(ROOT, 'worlds/xeen/events/maps/xeen_%s.lua' % key)).read().splitlines()
    return int(lua[lua.index('-- ' + tag) + 1].split('(')[1].split(',')[0])


def back_to_x7(key, tag, home, note, zr=(-120, 240)):
    """The dungeon's way out (an exit preset: the leave window, OK) back to X7's point before its door."""
    add({'note': note})
    add({'execute_event': {'id': exit_event(key, tag)}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': home[0], 'y': home[1], 'radius': 96, 'z_min': home[2] + zr[0],
                                       'z_max': home[2] + zr[1]}}})


X7_ARRIVALS = {a['name']: a['at'] for a in yaml.safe_load(open(os.path.join(ROOT, 'worlds/xeen/maps/xeen_x7.studio.yml')))['arrivals']}
_lua7 = open(os.path.join(B, 'xeen_x7.lua')).read()
if 'xeen_xd18.blv' in _lua7:
    # A7 installed XD-18 (04:33): the mouth leads to entrance:x7_mouth (384, -3072, 0) facing east; back by its evt:exit
    # to X7's entrance:xd18_mouth
    _at18 = inside('xd18', 'entrance:x7_mouth')
    asked('evt:thing:xd18_mouth', 'smells pretty bad',
          '"The Dragon Cave smells pretty bad. Are you sure you wish to enter?" (xeen/aaze0017:0) after the look, Yes/No '
          'buttons (D-72); Yes into XD-18 at entrance:x7_mouth')
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_xd18.blv'}})
    add({'assert': {'party_position': {'x': _at18[0], 'y': _at18[1], 'radius': 200, 'z_min': _at18[2] - 80,
                                       'z_max': _at18[2] + 160}}})
    add({'advance_runtime': {'seconds': 0.5}})
    close()
    back_to_x7('xd18', 'evt:exit', X7_ARRIVALS['entrance:xd18_mouth'],
               "XD-18's way out (evt:exit) back to X7 before the Dragon Cave (entrance:xd18_mouth)")
else:
    event('evt:thing:xd18_mouth', '"The Dragon Cave smells pretty bad. Are you sure you wish to enter?" '
          '(xeen/aaze0017:0): Yes, then sealed until XD-18', answer='Yes', prompt='The Dragon Cave smells pretty bad. Are you sure you wish to enter?')
event('evt:thing:knight_remains', "A knight's strongbox (level 5)", dialog=False, chest=True)
path([(58, 35), (59.5, 39), (61, 40.6), (61, 45.4), (61, 47), (63.4, 46.0)], 'Back over the bridge to the Volcano Cave')
walkc(65.0, 45.0, "Before the Volcano Cave's mouth", timeout=60)
if 'xeen_xd16.blv' in open(os.path.join(B, 'xeen_x7.lua')).read():
    # A7 installed XD-16 (00:28): the mouth leads to entrance:x7_mouth; back by evt:exit_x7 to entrance:xd16_mouth
    _lua16 = open(os.path.join(ROOT, 'worlds/xeen/events/maps/xeen_xd16.lua')).read().splitlines()
    _exit16 = int(_lua16[_lua16.index('-- evt:exit_x7') + 1].split('(')[1].split(',')[0])
    _sy16 = yaml.safe_load(open(os.path.join(ROOT, 'worlds/xeen/maps/xeen_xd16.studio.yml')))
    _at16 = next(a['at'] for a in _sy16['arrivals'] if a['name'] == 'entrance:x7_mouth')
    asked('evt:thing:xd16_mouth', 'breathing heat',
          '"Enter the Volcano Cave?" (xeen/aaze0017:1) after the look, Yes/No buttons (D-72); Yes into XD-16 at '
          'entrance:x7_mouth')
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_xd16.blv'}})
    add({'assert': {'party_position': {'x': _at16[0], 'y': _at16[1], 'radius': 300, 'z_min': _at16[2] - 80,
                                       'z_max': _at16[2] + 160}}})
    add({'note': "XD-16's way out (evt:exit_x7) back to X7 before the mouth, between the idols"})
    add({'execute_event': {'id': _exit16}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': 512, 'y': 9728, 'radius': 200, 'z_min': 2160, 'z_max': 2440}}})
else:
    event('evt:thing:xd16_mouth', '"Enter the Volcano Cave?" (xeen/aaze0017:1): Yes, then sealed until XD-16',
          answer='Yes', prompt='Enter the Volcano Cave?')
event('evt:thing:idol_demon', "The demon idol (lane S's model): A3's x7.idols (Q-C26's hint)")
event('evt:thing:idol_devil', "The devil idol (lane S's model): A3's x7.idols")
path([(64.2, 46.3), (67, 47.8), (70, 48.6), (72.0, 48.0)], 'Along the cleft path to the cleft')
event('evt:thing:xd17_cleft', "The cleft: A3's xd17.cleft before cleft_open (\"Fallen rock chokes the cleft ...\")")
if 'xeen_xd17.blv' in open(os.path.join(B, 'xeen_x7.lua')).read():
    # A5 installed XD-17 (01:36): with cleft_open the cleft leads to entrance:x7_cleft; back by its evt:cleft (the
    # exit preset's window) to X7's entrance:xd17_cleft
    _lua17 = open(os.path.join(ROOT, 'worlds/xeen/events/maps/xeen_xd17.lua')).read().splitlines()
    _exit17 = int(_lua17[_lua17.index('-- evt:cleft') + 1].split('(')[1].split(',')[0])
    _sy17 = yaml.safe_load(open(os.path.join(ROOT, 'worlds/xeen/maps/xeen_xd17.studio.yml')))
    _at17 = next(a['at'] for a in _sy17['arrivals'] if a['name'] == 'entrance:x7_cleft')
    add({'note': 'cleft_open (116140), as after the first exit through XD-17\'s back passage'})
    add({'setup_shortcut': {'kind': 'set_qbit', 'id': 116140, 'value': True}})
    add({'note': "The cleft open: into XD-17 at entrance:x7_cleft"})
    add({'execute_event': {'id': ev['evt:thing:xd17_cleft']}})
    window('smell of grass')   # F16: trans 5017
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_xd17.blv'}})
    add({'assert': {'party_position': {'x': _at17[0], 'y': _at17[1], 'radius': 300, 'z_min': _at17[2] - 80,
                                       'z_max': _at17[2] + 160}}})
    add({'note': "XD-17's rockfall (evt:cleft) back to X7's entrance:xd17_cleft"})
    add({'execute_event': {'id': _exit17}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': 4096, 'y': 8192, 'radius': 200, 'z_min': 2400, 'z_max': 2700}}})
path([(70, 48.6), (67, 47.8), (64.2, 46.3), (63.4, 46.0), (61, 47), (61, 52)], 'Back to the lava fork')
path([(54, 54), (46, 56), (40, 56.5), (35.5, 55), (35.5, 51), (35.5, 47.0)],
     'The lake track and over the causeway to the island')
add({'assert': {'party_position': {'x': W(35.5, 47.0)[0], 'y': W(35.5, 47.0)[1], 'radius': 500}}})
walkc(35.6, 44.6, 'To the Ever-Hot Lava Rock', timeout=60)
# D-90 (A5 s30): round to the rock's north-west side, between the dead guards (their corpses take the click)
walkc(34.72, 43.72, 'Beside the rock, north-west', timeout=60)
# D-90 (A5 s30): the Ever-Hot Lava Rock is a ground item the party picks up
add({'play_lua': {'source': 'if ground_items(12314) ~= 1 then error("the lava rock is not on the ground") end'}})
add({'pick_up': {'item_id': 12314, 'reach': 700}})
add({'play_lua': {'source': 'close(); if held() ~= 0 then stow() end; if not has_item(12314) then '
                            'error("no Ever-Hot Lava Rock") end'}})
path([(35.5, 51), (35.5, 55), (40, 56.5)], 'Back over the causeway')
event('evt:thing:hydra_wallow', "The hydras' wallow (level 5)", dialog=False, chest=True)
path([(30, 57), (22, 52), (19.5, 45), (21, 38), (23, 35.6), (25.2, 34.2), (27.4, 33.4), (29, 32.4)],
     "The tower path round the lake and up the crag")
add({'assert': {'party_position': {'x': W(29, 32.4)[0], 'y': W(29, 32.4)[1], 'radius': 400, 'z_min': 2400}}})
if 'xeen_fd04.blv' in _lua7:
    # A7 installed FD-04 (04:52): the gate asks A3's q-f1.tower_door (the Key to the Dragon Tower, 12376) and leads to
    # entrance:x7_gate (0, -1280, 0) facing north; back by its evt:way_out to X7's entrance:fd04_door, before the leaves
    event('evt:thing:fd04_gate', "The Dragon Tower's gate without the key: A3's q-f1.tower_door fail text")
    add({'assert': {'map': M}})
    add({'grant_item': {'item_id': 12376, 'member_index': 0}})
    add({'advance_runtime': {'seconds': 0.3}})
    add({'note': 'With the Key to the Dragon Tower: the hook passes (its key line), into FD-04 at entrance:x7_gate'})
    add({'execute_event': {'id': ev['evt:thing:fd04_gate']}})
    window('Two black leaves')   # F16: trans 5065
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    _at4 = inside('fd04', 'entrance:x7_gate')
    add({'assert': {'map': 'xeen_fd04.blv'}})
    add({'assert': {'party_position': {'x': _at4[0], 'y': _at4[1], 'radius': 200, 'z_min': _at4[2] - 80,
                                       'z_max': _at4[2] + 160}}})
    add({'advance_runtime': {'seconds': 0.5}})
    close()
    _h4 = X7_ARRIVALS['entrance:fd04_door']
    back_to_x7('fd04', 'evt:way_out', _h4, "FD-04's way out (evt:way_out) back to X7 before the tower's gate "
               '(entrance:fd04_door)')
    add({'note': 'The return clears the leaves: a step south and back to the point, free of the gate'})
    walk(_h4[0], _h4[1] - 384, z=_h4[2], timeout=30, radius=96)
    walk(_h4[0], _h4[1], z=_h4[2], timeout=30, radius=96)
else:
    event('evt:thing:fd04_gate', "The Dragon Tower's gate: sealed until FD-04")
go(73, 51, 'The firestone path from the cleft round the mountain')
path([(78, 53), (84, 54.6), (90, 54), (95, 50.5), (97.6, 45.2)], 'Round the south shoulder to the hoard')
event('evt:thing:dragon_hoard', "A dragon's hoard (level 6)", dialog=False, chest=True)
path([(98.5, 44), (100, 37), (101, 31), (101, 28.2)], 'On to the Fire corner')
event('evt:thing:fire_reflector', '"Reflector. Activate?" Yes: before M36 the hook\'s fail text', answer='Yes',
      prompt='Reflector. Activate?',
      check='if qbit(111741) then error("the Reflector set its bit before M36") end')
# ---------------------------------------------------------------- the reload: the outpost stays burnt
add({'load_map': {'map': M}})
add({'advance_runtime': {'seconds': 1.0}})
go(33.0, 88.4, 'After a reload the outpost stays burnt (evt:outpost_state)')
event('evt:thing:outpost_fire', "A3's else text again (the burn does not repeat)")
# ---------------------------------------------------------------- the edges
if EDGES:
    pr = yaml.safe_load(open(os.path.join(P, 'project.yml')))
    nb = {n['id']: n for n in pr['neighbours']}
    south, west = nb['edge:south']['arrival'], nb['edge:west']['arrival']
    for to_map, out_cell, arrive, back_cell, home, note in (
            ('xeen_x1.odm', (69, 111.5), south, (69, 16.5), (69, 107), 'South edge: to X1 and back'),
            ('xeen_x4.odm', (16.5, 66), west, (111.5, 66.5), (21, 66), 'West edge: to X4 and back')):
        go(home[0], home[1] - 2 if to_map == 'xeen_x1.odm' else home[1], note)
        add({'walk_to': {'x': W(*out_cell)[0], 'y': W(*out_cell)[1], 'z': ground(*W(*home)), 'z_tolerance': 900,
                         'radius': 128, 'timeout_seconds': 90, 'clear_hostiles': 3000, 'expect': 'dialog'}})
        add({'assert': {'dialog': {'active': True}}})
        add({'select_topic': {'match_label': 'OK'}})
        add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
        add({'assert': {'map': to_map}})
        if SPANS:
            add({'assert': {'party_position': {'x': arrive[0], 'y': arrive[1], 'radius': 200}}})
        else:
            add({'note': "the travel row's default arrival on %s (no edge_spans row for X7 yet)" % to_map})
        add({'advance_runtime': {'seconds': 1.0}})
        close()      # the neighbour's own entry window (X1's errand), if any
        add({'walk_to': {'x': W(*back_cell)[0], 'y': W(*back_cell)[1], 'z': arrive[2], 'z_tolerance': 900,
                         'radius': 128, 'timeout_seconds': 90, 'clear_hostiles': 3000, 'expect': 'dialog'}})
        add({'assert': {'dialog': {'active': True}}})
        add({'select_topic': {'match_label': 'OK'}})
        add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
        add({'assert': {'map': M}})
        if SPANS:
            add({'assert': {'party_position': {'x': W(*home)[0], 'y': W(*home)[1], 'radius': 200}}})
else:
    add({'note': "X7's edge rows are not in this root (A1's edge_spans and travel rows once X7 is installed): the "
                 'edges are passed by'})

doc = {'id': 'xeen.x7.walk', 'title': 'X7 Mount Firestone: every device, the hooks, the sealed doors and the north',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/x7/tools/gen_walk.py from the built map (A5, 2026-11-20).\n')
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'edges', EDGES)
