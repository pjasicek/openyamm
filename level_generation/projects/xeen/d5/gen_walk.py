#!/usr/bin/env python3
"""Writes D5's playtest.yml (the walk) from the built map (A6, thirteenth session; D4's walk adapted): door points from
build.json, ground heights from the map's export, event numbers from ids.lock.yml, NPC actors from the scene.
Usage: gen_walk.py <project L4> <build folder>
The walk: a new game on D5 (the build's start); the People at load; the west: the D6 road's sealed end, the obelisk,
the west boulders (a line, the riddle wrong then right, a crumble), the Last Water, the shrine; the east: the sign and a
boulder, the broken pyramid, the pyramid's door without and with the key (DD-15 sealed), the grate (the bolt, then
into DD-18 at entrance:d5_grate); the highlands: Gurodel's talk, DD-24's doors (into entrance:d5_hold), the tower door
without and with the key (DD-08 sealed), Bosco's door (DD-25 sealed), the fountains, the lair; the D4 edge both ways
when A2's travel rows exist."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import math
import os
import subprocess
import sys
import yaml

P, B = sys.argv[1], sys.argv[2]
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..'))
WORLD = os.path.join(ROOT, 'assets_dev/worlds/xeen')
M = 'xeen_d5.odm'
TRAVEL = [l.split('\t') for l in open(os.path.join(WORLD, 'data_tables/outdoor_travels.txt'))]
TRAVEL_LIVE = any(r[0] == M and 'xeen_d4.odm' in r for r in TRAVEL) and \
    any(r[0] == 'xeen_d4.odm' and M in r for r in TRAVEL)
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run([os.path.join(ROOT, 'openyamm-studio/build-xeen/oymap'), 'export', os.path.join(B, M), '--out',
                exp_path], check=True, stdout=subprocess.DEVNULL)
hm = json.load(open(exp_path))['map']['terrain']['height_map']
ev = dict(yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))['events'])
scene = yaml.load(open(os.path.join(B, 'xeen_d5.scene.yml')), Loader=yaml.CSafeLoader)
actors = scene['initial_state']['actors']
npc_actor = {a['npc_id']: i for i, a in enumerate(actors) if a.get('npc_id')}
doors = {b['id']: b for b in build['buildings']}
arr = {a['name']: a['at'] for a in build['named_arrivals']}


def sidecar(stem):
    f = os.path.join(WORLD, 'maps/%s.studio.yml' % stem)
    return {a.get('name'): a for a in ((yaml.safe_load(open(f)) or {}).get('arrivals') or [])} if os.path.exists(f) \
        else {}


DD18, DD24 = sidecar('xeen_dd18'), sidecar('xeen_dd24')
DD15, DD25, DD08 = sidecar('xeen_dd15'), sidecar('xeen_dd25'), sidecar('xeen_dd08')


def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))


def ground(X, Y):
    x = X / 512.0 + 64
    y = 64 - Y / 512.0
    i, j = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - i, y - j

    def h(a, b):
        return hm[max(0, min(127, b)) * 128 + max(0, min(127, a))] * 32
    return round(h(i, j) * (1 - fx) * (1 - fy) + h(i + 1, j) * fx * (1 - fy) + h(i, j + 1) * (1 - fx) * fy
                 + h(i + 1, j + 1) * fx * fy)


steps = []
add = steps.append


def close():
    add({'play_lua': {'source': 'close(); wait(0.3)'}})


def face(X, Y, yaw, z=None):
    add({'set_pose': {'map': M, 'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'yaw': round(yaw, 4),
                      'pitch': 0.0}})
    add({'advance_runtime': {'seconds': 0.5}})


def jump(x, y, note, yaw=0.0):
    add({'note': note + ' (by teleport)'})
    face(*W(x, y), yaw)


def walkc(x, y, note=None, timeout=120):
    if note:
        add({'note': note})
    X, Y = W(x, y)
    add({'walk_to': {'x': X, 'y': Y, 'z': ground(X, Y), 'z_tolerance': 700, 'radius': 192,
                     'timeout_seconds': timeout, 'clear_hostiles': 3000}})


sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a6/s32')
import hookwin    # s32: D-90 made most hooks status lines; such an event opens no window


def event(eid, note, dialog=True, text=None, check=None):
    add({'note': note})
    add({'execute_event': {'id': ev[eid]}})
    add({'advance_runtime': {'seconds': 0.5}})
    if dialog and hookwin.status_only(os.path.join(B, 'xeen_d5.lua'), ev[eid], passes=not any(
            w in note.lower() for w in ('refus', 'without', 'no pass', 'not yet', 'sealed', 'before '))):
        dialog = False
    if dialog:
        a = {'active': True}
        if text:
            a['text_contains'] = text
        add({'assert': {'dialog': a}})
    close()
    if check:
        add({'play_lua': {'source': check}})


def ask(eid, note, answer, check=None):
    add({'note': note})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev[eid]}})
    add({'answer_input': {'text': answer}})
    add({'advance_runtime': {'seconds': 0.5}})
    close()
    if check:
        add({'play_lua': {'source': check}})


def bit(q, on=True):
    return 'if %sqbit(%d) then error("qbit %d %s") end' % ('not ' if on else '', q, q, 'not set' if on else 'set')


def door(bid, note, expect=None, moves=False):
    b = doors[bid]
    dx, dy, dz = b['door']
    nx, ny = b['normal']
    sx, sy = round(dx + nx * 300), round(dy + ny * 300)
    add({'note': note})
    face(sx, sy, math.atan2(-ny, -nx), z=max(ground(sx, sy), dz))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    if moves:
        return
    if expect is not None:
        add({'assert': {'dialog': expect}})
    close()


def into(blv, name, note):
    a = {'DD18': DD18, 'DD24': DD24, 'DD15': DD15, 'DD25': DD25, 'DD08': DD08}[note][name]['at']
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # s32 (F16): the entrance window
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': blv}})
    add({'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}})
    close()
    add({'assert': {'party_position': {'x': a[0], 'y': a[1], 'radius': 160}}})


s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'assert': {'party_position': {'x': s['x'], 'y': s['y'], 'radius': 200}}})
add({'advance_runtime': {'seconds': 2}})
add({'note': 'At load: the six People (11083-11085) and Gurodel placed, the eyrie griffins'})
add({'assert': {'actor_count': {'monster_id': 11083, 'min': 3}}})
add({'assert': {'actor_count': {'monster_id': 11085, 'min': 2}}})
add({'assert': {'actor_count': {'monster_id': 11562, 'min': 3}}})
# ---------------------------------------------------------------- the west
if any(t['id'] == 'thing:west_road_end' for t in yaml.safe_load(open(os.path.join(P, 'sketch.yml')))['structures']):
    jump(21.4, 63.6, "The pass at the D6 border (D6 sealed)", yaw=math.pi)
    event('evt:thing:west_road_end', "The road's end sign", text='rockfall')
else:
    add({'note': "D6 is installed: the west edge is open (walked once A2's travel rows D5-D6 exist)"})
jump(44.5, 71.0, 'The west road by the obelisk knoll', yaw=0.0)
event('evt:thing:obelisk', 'The obelisk (obelisks.d5)', dialog=False, check=bit(115054))
jump(39.0, 69.0, 'The west boulders by the west road', yaw=math.pi)
event('evt:thing:boulder_1', 'Boulder 1 speaks (q-d24.boulder_1)', text='first')
ask('evt:thing:boulder_7', 'Boulder 7 asks; a wrong answer (q-d24.answer_wrong)', 'stone', check=bit(113480, False))
ask('evt:thing:boulder_7', 'Boulder 7 asks; Paladin (q-d24.answer: 12529, solved)', 'paladin', check=bit(113480))
event('evt:thing:boulder_2', 'After the answer boulder 2 crumbles (crumbled_2) and is hidden', check=bit(113482))
event('evt:thing:boulder_2', 'Clicked again: only sand', text='only sand')
walkc(45.0, 75.6, 'Down the oasis track to the Last Water', timeout=90)
event('evt:thing:last_water', 'The Last Water (d5.last_water: +2 Luck, once per character)', dialog=False)
jump(32.0, 85.4, "The Shrine of Great Power's mesa", yaw=math.pi / 2)
ask('evt:thing:shrine_altar', 'The shrine: "Will the party pray?" Yes (d5.shrine)', 'Yes')
# ---------------------------------------------------------------- the east
jump(EAST := 88.0, 79.0, 'The desert road at the east boulders', yaw=math.pi)
event('evt:thing:boulder_sign', 'The weathered sign (q-d24.sign)', text='paladin')
event('evt:thing:boulder_3', 'Boulder 3 after the answer: crumbles (crumbled_3)', check=bit(113483))
jump(96.4, 75.4, 'The broken travel pyramid by the road', yaw=math.pi / 2)
event('evt:part:thing:broken_pyramid/body', 'The broken pyramid (obelisks.dark_hoard: the portal destroyed)', text='portal')
jump(64.0, 76.0, "The Great Pyramid's north door", yaw=-math.pi / 2)
door('thing:great_pyramid', 'The green door without the key (m28.door)')
add({'grant_item': {'item_id': 12348}})
if 'entrance:d5_door' in DD15:
    add({'note': "With the Key to the Ancient Pyramid: m28.door (111560), the green doors into DD-15 (entrance:d5_door)"})
    door('thing:great_pyramid', 'The green door with the key', None, moves=True)
    add({'play_lua': {'source': bit(111560)}})
    into('xeen_dd15.blv', 'entrance:d5_door', 'DD15')
    add({'note': "Back to D5 (DD-15's way out is A8's; set down at entrance:dd15_door)"})
    add({'load_map': {'map': M}})
    p_ = arr['entrance:dd15_door']
    face(p_[0], p_[1], -math.pi / 2)
else:
    door('thing:great_pyramid', 'With the Key to the Ancient Pyramid: DD-15 sealed until A8 installs it',
         {'active': True, 'text_contains': 'later part'})
jump(101.0, 99.5, "The grate's hollow", yaw=-math.pi / 2)
event('evt:thing:dd18_grate', 'The grate: the bolt drawn (dd18.d5_grate, 116121)', dialog=False)
add({'play_lua': {'source': bit(116121)}})
if 'entrance:d5_grate' in DD18:
    add({'note': 'Through the grate into DD-18 (entrance:d5_grate)'})
    add({'execute_event': {'id': ev['evt:thing:dd18_grate']}})
    into('xeen_dd18.blv', 'entrance:d5_grate', 'DD18')
    add({'note': "Back to D5 (DD-18's exit:d5_grate is A8's; set down at entrance:dd18_grate)"})
    g = arr['entrance:dd18_grate']
    add({'load_map': {'map': M}})
    face(g[0], g[1], math.pi / 2)
# ---------------------------------------------------------------- the highlands
jump(76.0, 52.6, 'Highland Fork (the top of the switchbacks)', yaw=0.0)
walkc(82.0, 49.5, "The hold lane to Gurodel's fire", timeout=120)
add({'note': "Gurodel's talk (5452)"})
add({'interact_actor': {'actor_index': npc_actor[5452]}})
add({'advance_runtime': {'seconds': 0.5}})
add({'assert': {'dialog': {'active': True}}})
close()
if 'entrance:d5_hold' in DD24:
    add({'note': "DD-24's great doors (two leaves): into the Giants' Hall at entrance:d5_hold"})
    add({'execute_event': {'id': ev['evt:thing:giants_hall_doors']}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'play_lua': {'source': 'if dialog_active and dialog_active() then select_label("OK") end'}}) \
        if False else None
    into('xeen_dd24.blv', 'entrance:d5_hold', 'DD24')
    add({'load_map': {'map': M}})
    h = arr['entrance:dd24_hold']
    face(h[0], h[1], -math.pi / 2)
add({'note': 'Back at the hold: no People hostile after the visit'})
add({'assert': {'actor_count': {'monster_id': 11083, 'hostile': True, 'max': 0}}})
jump(69.0, 42.6, 'The Northern Tower', yaw=math.pi / 2)
door('thing:northern_tower', "The tower door without Bosco's key (q-d17.tower_door)")
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 113341, 'value': True}})
if 'entrance:d5_tower' in DD08:
    door('thing:northern_tower', "With the key: into DD-08 (entrance:d5_tower)", None, moves=True)
    into('xeen_dd08.blv', 'entrance:d5_tower', 'DD08')
    add({'load_map': {'map': M}})
    p_ = arr['entrance:dd08_door']
    face(p_[0], p_[1], math.pi / 2)
else:
    door('thing:northern_tower', "With the key: DD-08 sealed until A8 installs it",
         {'active': True, 'text_contains': 'later part'})
jump(63.2, 46.3, "Bosco's terrace", yaw=math.pi)
if 'entrance:d5_bosco' in DD25:
    add({'note': "Bosco's door: into DD-25 (entrance:d5_bosco)"})
    add({'execute_event': {'id': ev['evt:thing:bosco_door']}})
    into('xeen_dd25.blv', 'entrance:d5_bosco', 'DD25')
    add({'note': "Back to D5 (DD-25's way out is A8's; set down at entrance:dd25_door)"})
    add({'load_map': {'map': M}})
    p_ = arr['entrance:dd25_door']
    face(p_[0], p_[1], 0.0)
else:
    event('evt:thing:bosco_door', "Bosco's door: DD-25 sealed until A8 installs it", text='later part')
jump(100.5, 33.5, 'The Fountain of Might under the rim', yaw=math.pi / 2)
event('evt:thing:fountain_might', 'The Fountain of Might (d5.fountain_might)', dialog=False)
jump(48.5, 31.0, "The Fountain of Energy Resistance by the Barrier's west end", yaw=math.pi / 2)
event('evt:thing:fountain_energy', 'The Fountain of Energy Resistance (d5.fountain_energy)', dialog=False)
jump(35.2, 42.6, "The cyclopes' lair", yaw=math.pi / 2)
ask('evt:part:thing:lair_leanto/leanto', '"Destroy?" Yes (d5.lair, 116180)', 'Yes', check=bit(116180))
# ---------------------------------------------------------------- the D4 edge
if TRAVEL_LIVE:
    add({'note': 'Off the east edge to D4 (the travel prompt, OK)'})
    jump(107.0, 80.0, 'The D4 road at the border', yaw=0.0)
    X, Y = W(127.6, 80)
    add({'walk_to': {'x': X, 'y': Y, 'z': ground(X, Y), 'z_tolerance': 900, 'radius': 128, 'timeout_seconds': 150,
                     'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_d4.odm'}})
    add({'note': "Back west off D4's west edge at y 80: the prompt, OK; D5's entrance:d4_road"})
    add({'set_pose': {'map': 'xeen_d4.odm', 'x': W(22, 80)[0], 'y': W(22, 80)[1], 'z': 1504,
                      'yaw': round(math.pi, 4), 'pitch': 0.0}})
    add({'walk_to': {'x': W(0.4, 80)[0], 'y': W(0.4, 80)[1], 'z': 1504, 'z_tolerance': 900, 'radius': 128,
                     'timeout_seconds': 150, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    a = arr['entrance:d4_road']
    add({'assert': {'party_position': {'x': a[0], 'y': a[1], 'radius': 700}}})
steps = [s_ for s_ in steps if s_ is not None]
doc = {'id': 'xeen.d5.walk', 'title': 'D5 Desert of Doom: the west, the east, the highlands', 'world': 'xeen',
       'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/d5/tools/gen_walk.py from the built map (A6). D4 edge walked: %s.\n'
            % ('yes' if TRAVEL_LIVE else 'no (A2 travel rows pending)'))
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'travel', TRAVEL_LIVE, 'dd18', 'entrance:d5_grate' in DD18, 'dd24',
      'entrance:d5_hold' in DD24, 'dd15', 'entrance:d5_door' in DD15, 'dd25', 'entrance:d5_bosco' in DD25,
      'dd08', 'entrance:d5_tower' in DD08)
