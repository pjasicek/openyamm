#!/usr/bin/env python3
"""Writes X5's playtest.yml (the walk) from the built map: house doors from build.json, the dark faces of the ways in
and ground heights from the map's export, event numbers from ids.lock.yml, NPC actors from the scene.
Usage: gen_walk.py <project L4> <build folder>
The walk: a new game on Winterkill square; the gongs, the plaque, the signboard, the machine, the cursed chest, Mayor
Randon; Q-C6's machinery (the Spirit Bones laid set wave1_laid; Randon's reported1 brings the Polter-Fools); the Edge
Watch; the south track to the Winter Druid, Glom's fork, the giants' outpost (Q-C16's hook), the Giants' Stones, the
Waters of Great Magic and the Reflector; the forest track to the Shrine of Cold, the Holy Book (Q-C18), the warren,
XD-10's south mouth, Thickbark; the mere (the fishing hole, the frozen pack, Darkstone's sealed door); the monastery,
the pagoda, the obelisk, the steppe road's end, the barbarian camp; the pass and Freeda; the pocket: Halon, XD-10's
north mouth, the Golem Dungeon's door (refused, then with the Golem Stone), the hot spring, the lagoon road's end.
Houses are opened when A4's house rows for X5 are in the world (4251+); dungeons are entered when installed."""
import json
import math
import re
import os
import subprocess
import sys
import yaml

P, B = sys.argv[1], sys.argv[2]
ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..')
WORLD = os.path.join(ROOT, 'assets_dev/worlds/xeen')
M = 'xeen_x5.odm'
HAVE = {k for k in ('xd09', 'xd10', 'xd22', 'xd23', 'fd03') if os.path.exists(os.path.join(WORLD, 'maps/xeen_%s.blv' % k))}
HOUSES_LIVE = any(l.startswith('4251\t') for l in open(os.path.join(WORLD, 'data_tables/house_data.txt')))
X3_LIVE = os.path.exists(os.path.join(WORLD, 'maps/xeen_x3.odm'))
# the edge travels once A2's generator has written X5's row (outdoor_travels.txt) with X3 on its east (Left) side
TRAVEL_LIVE = any(l.startswith('xeen_x5.odm\t') and 'xeen_x3.odm' in l
                  for l in open(os.path.join(WORLD, 'data_tables/outdoor_travels.txt')))
# X6 (A5, 2026-11-20): the north edge travels once X6 is installed and A2's travel row X5-X6 is written; the arrival
# points are asserted when A2's edge_spans rows for X5/X6 exist (else the side's default arrival: the map only)
X6_LIVE = os.path.exists(os.path.join(WORLD, 'maps/xeen_x6.odm'))
X6_TRAVEL = any(l.startswith('xeen_x5.odm\t') and 'xeen_x6.odm' in l
                for l in open(os.path.join(WORLD, 'data_tables/outdoor_travels.txt')))
_SPANS = open(os.path.join(WORLD, 'data_tables/edge_spans.yml')).read()
X6_SPANS = ('map: xeen_x5.odm, edge: north' in _SPANS) and ('map: xeen_x6.odm, edge: south' in _SPANS)
# A4's cursed-town houses (`opens: q-c6.done`): their closed_text until Winterkill is liberated (112121)
TOWN = yaml.safe_load(open(os.path.join(WORLD, 'source/towns/x5.yml')))
CLOSED = {h['door']: h['closed_text'] for h in TOWN['houses'] if h.get('opens') and not h['door'].startswith('thing:')}
# once open, a residence of one person opens that person's talk (MM7's rule); any other house its house screen
ALONE = {h['door']: h['residents'][0] for h in TOWN['houses'] if len(h.get('residents') or []) == 1}
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run([os.path.join(ROOT, 'openyamm-studio/build-xeen/oymap'), 'export', os.path.join(B, M), '--out',
                exp_path], check=True, stdout=subprocess.DEVNULL)
_m = json.load(open(exp_path))['map']
hm = _m['terrain']['height_map']
bmodels = {b['name']: b for b in _m['bmodels']}
ids = yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))
ev = dict(ids['events'])
scene = yaml.safe_load(open(os.path.join(B, 'xeen_x5.scene.yml')))
npc_actor = {a['npc_id']: a['actor_index'] for a in scene['initial_state']['actors'] if a.get('npc_id')}

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

def dark_face(name, tex='7solid01'):
    b = bmodels[name]
    for f in b['faces']:
        if f['texture'] == tex:
            vs = [b['vertices'][i] for i in f['vertices']]
            n = f['plane_normal']
            return ((sum(v[0] for v in vs) / len(vs), sum(v[1] for v in vs) / len(vs), min(v[2] for v in vs)),
                    (n[0] / 65536.0, n[1] / 65536.0))
    raise SystemExit('no %s face on %s' % (tex, name))

doors = {b['id']: b for b in build['buildings']}
steps = []
add = steps.append

def walk(X, Y, note=None, timeout=120, radius=192, z=None):
    if note:
        add({'note': note})
    add({'walk_to': {'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'z_tolerance': 700, 'radius': radius,
                     'timeout_seconds': timeout, 'clear_hostiles': 3000}})

def walkc(x, y, note=None, timeout=120, z=None):
    walk(*W(x, y), note=note, timeout=timeout, z=z)

def face(X, Y, yaw, z=None):
    add({'set_pose': {'map': M, 'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'yaw': round(yaw, 4),
                      'pitch': 0.0}})
    add({'advance_runtime': {'seconds': 0.5}})

def jump(x, y, note, yaw=0.0):
    add({'note': note + ' (by teleport)'})
    face(*W(x, y), yaw)

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
    if dialog:
        add({'assert': {'dialog': {'active': True}}})
        add({'press_action': {'action': 'cancel_dialog'}})
        add({'advance_runtime': {'seconds': 0.3}})
    if check:
        add({'play_lua': {'source': check}})

def talk(npc, note, near):
    walkc(*near, note=note, timeout=120)
    add({'interact_actor': {'actor_index': npc_actor[npc]}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True}}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})

def house(bid, note=None, closed=False, opened=False):
    b = doors[bid]
    dx, dy, dz = b['door']
    nx, ny = b['normal']
    sx, sy = round(dx + nx * 300), round(dy + ny * 300)
    if not HOUSES_LIVE:
        return
    walk(sx, sy, note or '%s (%s): its door' % (b['title'], bid), timeout=90)
    face(sx, sy, math.atan2(-ny, -nx), z=max(ground(sx, sy), dz))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    if closed:
        add({'assert': {'dialog': {'active': True, 'house_dialog': False, 'text_contains': CLOSED[bid][:40]}}})
    elif opened and bid in ALONE:
        add({'assert': {'dialog': {'active': True, 'source_id': ALONE[bid]}}})
    elif opened:
        add({'assert': {'dialog': {'active': True}}})
    else:
        add({'assert': {'dialog': {'active': True}}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})

# The named arrivals (A6 ninth session): where each door must land inside, from the dungeon's <stem>.studio.yml
ARRIVE = {'thing:xd10_south': ('xeen_xd10', 'entrance:x5_south'), 'thing:xd10_north': ('xeen_xd10', 'entrance:x5_north'),
          'thing:xd09_door': ('xeen_xd09', 'entrance:x5')}


def arrival_point(stem, entrance):
    st = yaml.safe_load(open(os.path.join(WORLD, 'maps/%s.studio.yml' % stem)))
    return next(a['at'] for a in st.get('arrivals', []) if a['name'] == entrance)


def into(name, target, key, note, before=None):
    fp, fn = dark_face(name)
    X, Y = round(fp[0] + fn[0] * 280), round(fp[1] + fn[1] * 280)
    yaw = math.atan2(-fn[1], -fn[0])
    walk(X, Y, note, timeout=120)
    face(X, Y, yaw, z=max(ground(X, Y), fp[2]))
    if before:
        before(X, Y, yaw, fp)
    if key not in HAVE:
        add({'note': '%s is not installed in the world yet: its door is passed by' % target})
        return
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: the entrance window
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': target}})
    if name in ARRIVE and key in HAVE:
        ax, ay, _ = arrival_point(*ARRIVE[name])
        add({'note': 'Arrived at %s %s' % ARRIVE[name]})
        add({'assert': {'party_position': {'x': ax, 'y': ay, 'radius': 200}}})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'note': 'Back on X5 where the party stood (by load_map)'})
    face(X, Y, yaw + math.pi, z=max(ground(X, Y), fp[2]))

s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'assert': {'party_position': {'x': s['x'], 'y': s['y'], 'radius': 160}}})
# ---------------------------------------------------------------- Winterkill
add({'assert': {'actor_count': {'monster_id': 11241, 'hostile': True, 'min': 6}}})
add({'note': "Q-C6: the Spirit Bones haunt the square; the Polter-Fools and the Ghost Riders are hidden"})
event('evt:thing:gong_plaque', "The plaque between the northern gongs (q-c6.north_gongs_verse)")
event('evt:thing:randon_board', 'The signboard by the gongs (q-c6.signboard)')
event('evt:part:thing:acme_machine/lens', 'The Acme Ghost Visualization System (q-c6.acme_sign)')
event('evt:thing:ghost_chest', 'The cursed chest: shut until the town is free (q-c6.ghost_verse)')
event('evt:thing:north_gong_1', 'A northern gong: BONG', dialog=False)
event('evt:thing:strength_well' if 'evt:thing:strength_well' in ev else 'evt:thing:north_gong_2',
      'The old well: frozen until the town is free', dialog=False)
talk(4502, 'Mayor Randon by the gongs: the ghosts (Q-C6)', (36.6, 43.6))
house('building:mindmeld_guild', 'The Mindmeld Guild: open from day one')
for _bid in sorted(CLOSED, key=lambda k: (doors[k]['door'][1], doors[k]['door'][0]), reverse=True):
    house(_bid, '%s (%s): closed until the town is free' % (doors[_bid]['title'], _bid), closed=True)
walkc(37, 41.5, 'Round the square: the Spirit Bones are laid (clear_hostiles)', timeout=90)
walkc(35, 39.5, timeout=60)
walkc(39, 39.5, timeout=60)
walkc(39, 44, timeout=60)
walkc(35, 44, timeout=60)
walkc(43, 41.5, timeout=60)
walkc(40, 41.5, timeout=60)
walkc(37, 44.5, timeout=60)
walkc(37, 47.8, timeout=60)
walkc(37, 41.5, timeout=60)
add({'play_lua': {'source': 'local n = clear_hostiles(4000); log("cleared " .. n)'}})
add({'advance_runtime': {'seconds': 7}})
add({'play_lua': {'source': 'if not qbit(112122) then error("wave1_laid (112122) not set") end'}})
add({'note': 'The southern gong over the laid wave (q-c6.gong sets rung); Randon then reports (reported1, A3)'})
event('evt:thing:south_gong', 'The southern gong (q-c6.gong)')
add({'play_lua': {'source': 'if not qbit(112125) then error("rung (112125) not set") end'}})
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 112126, 'value': True}})
add({'advance_runtime': {'seconds': 5}})
add({'assert': {'actor_count': {'monster_id': 11260, 'hostile': True, 'min': 6}}})
add({'note': 'With reported1 the Polter-Fools are out'})
# ---------------------------------------------------------------- the Edge Watch and the snowfields
walkc(30, 41.5, 'West along the rim walk to the Edge Watch', timeout=90)
walkc(27.6, 41.6, timeout=60)
event('evt:thing:edge_note', "The Edge Watch's old note")
jump(37, 49, 'South out of the town to the south track', yaw=-math.pi / 2)
walkc(37, 50, timeout=60)
walkc(36, 55, timeout=90)
walkc(35.5, 60, timeout=90)
talk(4529, "The Winter Druid in his grove (Q-C1's Winter step)", (31.6, 61.4))
walkc(35.5, 60, timeout=60)
walkc(37, 66, timeout=90)
walkc(40, 72, timeout=90)
walkc(42, 77, "Glom's fork", timeout=90)
house('building:glom_burrow#1', "Glom's burrow")
# ---------------------------------------------------------------- the giants' corner
walkc(40, 82, 'Up the giants\' path', timeout=90)
walkc(39.5, 86, timeout=90)
event('evt:thing:giant_stone', "The Giants' Stones (Might 40)", dialog=False)
walkc(41.5, 90.5, timeout=90)
walkc(43, 92, 'The cyclops outpost', timeout=90)
# A6 s27 (D-72): the source's question on Yes/No buttons; No leaves it standing, Yes burns it (the hook's text)
event('evt:thing:outpost_tent', "The Cyclops' outpost: Burn? No", answer='No', prompt="Cyclops' outpost! Burn?",
      dialog=False, check='if qbit(112321) then error("outpost_burnt (112321) set by No") end')
event('evt:thing:outpost_tent', "Burn the Cyclops' outpost: Yes (q-c16.outpost)", answer='Yes',
      prompt="Cyclops' outpost! Burn?",
      check='if not qbit(112321) then error("outpost_burnt (112321) not set") end')
walkc(46, 98, 'Down to the Reflector\'s ledge', timeout=120)
walkc(46.5, 99.6, timeout=60)
event('evt:thing:waters_great_magic', 'The Waters of Great Magic', dialog=False)
event('evt:thing:earth_reflector', '"Reflector. Activate?" Yes: before M36 the hook\'s fail text', answer='Yes',
      prompt='Reflector. Activate?',
      check='if qbit(111742) then error("the Reflector set its bit before M36") end')
# ---------------------------------------------------------------- the Troll Forest
jump(48, 77, 'The forest track east of the fork', yaw=0.0)
walkc(53, 76.2, 'The Shrine of Cold', timeout=90)
event('evt:part:thing:shrine_cold/s', 'The Shrine of Cold: +5 Water resistance', dialog=False)
walkc(58, 81, timeout=120)
walkc(63, 88, timeout=120)
walkc(65.5, 92.0, timeout=90)
# D-93 (A3 s40 for A6): a click on the torn pack puts the Holy Book onto the cursor (quest hook q-c18.book)
walkc(68.85, 92.75, 'The Holy Book of Elvenkind in a torn pack on the snow (onto the cursor; from the south)', timeout=90)
add({'play_lua': {'source': 'close(); click(%d); wait(0.5); if held() ~= 12524 then error("the torn pack put no book on the '
                            'cursor") end; stow(); if not has_item(12524) then error("no Holy Book from the torn pack") end'
                            % ev['evt:thing:holy_book']}})
if 'xd23' in HAVE:
    # the warren's mouth (event of thing:warren): "You drag the frozen hides aside.", then into XD-23 (D-25)
    fp, fn = dark_face('thing:warren')
    WX, WY = round(fp[0] + fn[0] * 280), round(fp[1] + fn[1] * 280)
    walk(WX, WY, 'The Troll Warren mouth (XD-23 live)', timeout=90)
    face(WX, WY, math.atan2(-fn[1], -fn[0]), z=max(ground(WX, WY), fp[2]))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: the entrance window
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_xd23.blv'}})
    add({'assert': {'party_position': {'x': 0, 'y': -256, 'radius': 200}}})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'note': 'Back on X5 where the party stood (by load_map)'})
else:
    event('evt:thing:warren' if 'evt:thing:warren' in ev else 'evt:hint:thing:warren', 'The Troll Warren: shut (XD-23)')
walkc(63, 88, timeout=90)
walkc(70, 85.5, timeout=120)
walkc(75, 83, timeout=90)
into('thing:xd10_south', 'xeen_xd10.blv', 'xd10', "XD-10's south mouth in the spur's west face")
jump(60, 73.5, 'The Thickbark path along the forest\'s edge', yaw=0.2)
walkc(67, 71.5, timeout=90)
talk(4528, 'Thickbark the Civilized by the frozen river (Q-C15)', (72.4, 70.2))
# ---------------------------------------------------------------- the mere
jump(47, 57, 'On the ice: Old Knut\'s fishing hole', yaw=0.0)
event('evt:thing:fishing_stool', "Old Knut's fishing hole", dialog=False)
walkc(51, 63, 'Across the ice to Darkstone\'s rock', timeout=90, z=800)
walkc(59.8, 65.2, timeout=90, z=800)
event('evt:thing:frozen_pack', 'A pack frozen into the ice (a chest)', dialog=False)
add({'press_action': {'action': 'cancel_dialog'}})
if 'fd03' in HAVE:
    # D-57 (A6 s16): the keyhole refuses without the black key (M41's qbit 111780); with it A3's line and into FD-03
    # at entrance:x5_door (0, 1792); FD-03's exit lands on X5's entrance:fd03_door on the rock top (-4608, 2560, 1504)
    event('evt:door:thing:darkstone', "Darkstone Tower's door without the black key: the keyhole")
    add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111780, 'value': True}})
    add({'note': "With the black key (111780): A3's m41.tower_door line, then into FD-03"})
    add({'execute_event': {'id': ev['evt:door:thing:darkstone']}})
    # the hook's SimpleMessage is closed by the move at once (A3: a StatusText shows on the arriving map, MP17)
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: the entrance window
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_fd03.blv'}})
    add({'assert': {'party_position': {'x': 0, 'y': 1792, 'radius': 200}}})
    add({'note': "FD-03's way out (A7's exit to X5's entrance:fd03_door): the party stands on Darkstone's rock top"})
    _fd03_lua = open(os.path.join(WORLD, 'events/maps/xeen_fd03.lua')).read()
    _way_out = int(re.search(r'-- evt:way_out\nRegisterEvent\((\d+)', _fd03_lua).group(1))
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % _way_out}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'advance_runtime': {'seconds': 2.0}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': -4608, 'y': 2560, 'radius': 200, 'z_min': 1450, 'z_max': 1560}}})
else:
    event('evt:door:thing:darkstone', "Darkstone Tower: sealed (FD-03)")
# D-56 (session 15): P5's fall lands on the rock's top before the door; the way off is the door or the drop
jump(55, 59, "P5's fall point entrance:p5_fall on Darkstone's rock (D-56)", yaw=-math.pi / 2)
walkc(55, 59.6, 'Across the terrace to the tower door', timeout=30, z=1504)
walkc(54, 59, 'Along the terrace', timeout=30, z=1504)
walkc(55, 55.5, "Off the rock's north edge: the drop to the ice", timeout=60, z=800)
# ---------------------------------------------------------------- the north: monastery, pagoda, obelisk, steppe
jump(70.6, 40.4, 'The monastery\'s foot', yaw=math.pi / 2)
walkc(70.6, 39.6, timeout=60)
walkc(70.6, 35.8, 'Up the stair to the cloister', timeout=90, z=1900)
house('building:monastery_training', "Kai Wu's Monastery: training to 40")
house('building:monastery_temple', 'Hall of Stillness')
event('evt:part:thing:bell_frame/frame', 'The monastery bell', dialog=False)
jump(68, 44.5, 'The pagoda path', yaw=-math.pi / 2)
if 'xd22' in HAVE and 'Ninja Pagoda' in open(os.path.join(WORLD, 'data_tables/map_stats.txt')).read():
    add({'note': 'The Ninja Pagoda door into XD-22 (D-25)'})
    add({'execute_event': {'id': ev['evt:door:thing:pagoda']}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: the entrance window
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_xd22.blv'}})
    add({'assert': {'party_position': {'x': 0, 'y': -256, 'radius': 200}}})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})
    jump(68, 44.5, 'Back on the pagoda path', yaw=-math.pi / 2)
else:
    event('evt:door:thing:pagoda', 'The Ninja Pagoda: barred (XD-22)')
jump(58.5, 41.2, 'The obelisk on the promontory', yaw=-math.pi / 2)
event('evt:thing:obelisk', "The obelisk: A3's obelisks.x5 (the word FOR, cloud_5)",
      check='if not qbit(115044) then error("cloud_5 (115044) not set") end')
jump(50, 34, 'The Steppe Cross', yaw=math.pi / 2)
walkc(50, 28, 'North up the steppe road', timeout=120)
walkc(50, 21.5, timeout=120)
if X6_LIVE and X6_TRAVEL:
    event('evt:thing:north_road_end', 'The waymark by the road: "North: the Desert of the Sphinx."')
    add({'note': "Off X5's north edge: the travel prompt (X6, 7 days), accepted; X6's south start (-7168, -22016)"})
    add({'walk_to': {'x': W(50, 16.5)[0], 'y': W(50, 16.5)[1], 'z': ground(*W(50, 19)), 'z_tolerance': 900,
                     'radius': 128, 'timeout_seconds': 60, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_x6.odm'}})
    if X6_SPANS:
        add({'assert': {'party_position': {'x': -7168, 'y': -22016, 'radius': 700}}})
    add({'note': "Back south off X6's south edge on its steppe road: the prompt names Winterkill; accepted, X5's "
                 "north start (-7168, 22528)"})
    add({'walk_to': {'x': W(50, 111.5)[0], 'y': W(50, 111.5)[1], 'z': 1472, 'z_tolerance': 900, 'radius': 128,
                     'timeout_seconds': 60, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    if X6_SPANS:
        add({'assert': {'party_position': {'x': -7168, 'y': 22528, 'radius': 700}}})
elif X6_LIVE:
    add({'note': "X6 is installed but A2's travel row X5-X6 is not written yet: the edge is not walked"})
    event('evt:thing:north_road_end', 'The waymark by the road', dialog=True)
else:
    event('evt:thing:north_road_end', "The road's end: X6 not built (sealed)")
walkc(47, 23, 'West to the barbarian camp', timeout=120)
walkc(44.5, 25.5, timeout=90)
event('evt:thing:camp_tent2', "Burn the barbarians' tents (F13: the status line)", dialog=False)
event('evt:thing:camp_chest', "The chief's chest", dialog=False)
add({'press_action': {'action': 'cancel_dialog'}})
# ---------------------------------------------------------------- the pass and the pocket
jump(73, 40, 'The monastery foot: up the pass descent to the crest', yaw=0.6)
walkc(77, 41.5, timeout=120)
walkc(80, 44, timeout=120)
talk(4527, 'Freeda the Mountaineer at her camp on the crest', (82.0, 45.6))
walkc(83.5, 47.5, 'Down the pass road into the pocket', timeout=120)
walkc(86, 51, timeout=120)
walkc(89, 55, timeout=120)
event('evt:thing:frozen_sledge', "A trader's sledge in a drift", dialog=False)
add({'press_action': {'action': 'cancel_dialog'}})
walkc(93, 58, timeout=120)
walkc(98, 60, 'The lagoon fork', timeout=120)
walkc(99, 56, 'Up the hill track to Halon\'s yard', timeout=90)
walkc(100.5, 52.5, timeout=90)
house('building:halon_workshop', "Halon's Workshop")
event('evt:part:thing:halon_clock/tower', "Halon's water clock: frozen", dialog=False)
walkc(100.5, 48, timeout=90)
walkc(98.5, 46, timeout=90)
into('thing:xd10_north', 'xeen_xd10.blv', 'xd10', "XD-10's north mouth (D-4)")
jump(98, 60, 'Back at the lagoon fork; over the footbridge to the Golem Rocks', yaw=-math.pi / 2)
walkc(97.5, 61, timeout=60)
walkc(97.5, 65, timeout=90, z=None)
walkc(98.5, 67, timeout=60)

def golem_refused(X, Y, yaw, fp):
    add({'note': 'Without the Golem Stone the slab door stays shut (m10.golem_door)'})
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True}}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})
    add({'grant_item': {'item_id': 12305}})
    add({'note': 'With the Golem Stone (12305) the door opens'})
into('thing:xd09_door', 'xeen_xd09.blv', 'xd09', "XD-09's slab door in the Golem Rocks' north face",
     before=golem_refused)
jump(104, 64.8, 'The hot spring south of the river', yaw=-math.pi / 2)
event('evt:thing:hot_spring', 'The hot spring', dialog=False)
# ---------------------------------------------------------------- Winterkill liberated (q-c6.done): every house opens
jump(37, 41.5, 'Back on Winterkill square; the town liberated (q-c6.done, 112121)', yaw=-math.pi / 2)
add({'play_lua': {'source': 'local n = clear_hostiles(6000); log("cleared " .. n)'}})
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 112121, 'value': True}})
add({'advance_runtime': {'seconds': 1}})
for _bid in sorted(CLOSED, key=lambda k: (doors[k]['door'][1], doors[k]['door'][0]), reverse=True):
    house(_bid, '%s (%s): open now' % (doors[_bid]['title'], _bid), opened=True)
jump(106, 59, 'The lagoon road east to its end', yaw=0.0)
if X3_LIVE and not TRAVEL_LIVE:
    add({'note': "X3 is installed but A2's travel row X5-X3 is not written yet: the edge is not walked"})
    walkc(108, 59, timeout=60)
elif X3_LIVE:
    add({'note': "Off X5's east edge: the travel prompt (X3, 7 days), accepted; X3's west start (-22016, 2560, 864)"})
    add({'walk_to': {'x': W(112, 59)[0], 'y': W(112, 59)[1], 'z': ground(*W(112, 59)), 'z_tolerance': 600,
                     'radius': 128, 'timeout_seconds': 60, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_x3.odm'}})
    add({'assert': {'party_position': {'x': -22016, 'y': 2560, 'radius': 700}}})
    add({'note': "Back west off X3's west edge: the prompt names Winterkill; accepted, X5's east start (22016, 3072)"})
    add({'walk_to': {'x': -24576, 'y': 2560, 'z': 864, 'z_tolerance': 900, 'radius': 128, 'timeout_seconds': 60,
                     'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': 22016, 'y': 3072, 'radius': 700}}})
else:
    walkc(108, 59, timeout=60)
    event('evt:thing:east_road_end', "The road's end: X3 not built (sealed)")

doc = {'id': 'xeen.x5.walk', 'title': 'X5 Winterkill Tundra: Winterkill, the tundra, the pass and the pocket',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/x5/tools/gen_walk.py from the built map (A6). Houses opened: %s; '
            'dungeons entered: %s.\n' % ('yes' if HOUSES_LIVE else 'no (A4 rows pending)', sorted(HAVE) or 'none'))
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'houses', HOUSES_LIVE, 'have', sorted(HAVE))
