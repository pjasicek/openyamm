#!/usr/bin/env python3
"""Writes D6 (from D4's gen_walk.py)'s playtest.yml (the walk) from the built map (A6, ninth session; D1's and D2's walks adapted): house doors
from build.json, ground heights from the map's export, event numbers from ids.lock.yml, NPC actors from the scene.
Usage: gen_walk.py <project L4> <build folder>
The walk: a new game on the Isle (the build's start): DD-12's door refused, then with the key (sealed), the Isle Ferry's
house (4667); Lakeside: every house door (closed until Q-D22, the guild's riddle wrong then right, the guild open), the
back stair, the mirror, the shaft's question, Skiff's boat, Naomi; up the Sandcaster road to the brow; the gatehouse's
refusal; the bat storm over the crag top (a flying party set down on the north shore); the obelisk; Leafpoint, Ector,
the woodpile, DD-23's cave, Slibo; the fountains, the cairn, Mirabeth; the west road's end. The south edge is walked
when A2's travel row D3-D4 exists."""
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
M = 'xeen_d6.odm'
TRAVEL_LIVE = any(l.startswith('xeen_d6.odm\t') and 'xeen_d1.odm' in l
                  for l in open(os.path.join(WORLD, 'data_tables/outdoor_travels.txt')))
TOWN = yaml.safe_load(open(os.path.join(WORLD, 'source/towns/d6.yml')))
CLOSED = {}
ALONE = {h['id']: h['residents'][0] for h in TOWN['houses'] if len(h.get('residents') or []) == 1}
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run([os.path.join(ROOT, 'openyamm-studio/build-xeen/oymap'), 'export', os.path.join(B, M), '--out',
                exp_path], check=True, stdout=subprocess.DEVNULL)
hm = json.load(open(exp_path))['map']['terrain']['height_map']
ids = yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))
ev = dict(ids['events'])
scene = yaml.load(open(os.path.join(B, 'xeen_d6.scene.yml')), Loader=yaml.CSafeLoader)
npc_actor = {a['npc_id']: a['actor_index'] for a in scene['initial_state']['actors'] if a.get('npc_id')}
doors = {b['id']: b for b in build['buildings']}
# DD-23 (A7): live when its BLV's sidecar lists entrance:d4_mouth; its way out is the event that moves to D4
_dd23 = os.path.join(WORLD, 'maps/xeen_dd23.studio.yml')
DD23_MOUTH = next((a for a in (yaml.safe_load(open(_dd23)) or {}).get('arrivals') or []
                   if a.get('name') == 'entrance:d4_mouth'), None) if os.path.exists(_dd23) else None
DD23_EXIT = None
if DD23_MOUTH and ev.get('evt:thing:dd23_lair') is not None:
    import re
    _lua = open(os.path.join(WORLD, 'events/maps/xeen_dd23.lua')).read()
    _m = re.search(r'RegisterEvent\((\d+), [^\n]*function\(\)\n\s*evt\.MoveToMap\([^)]*"xeen_d4\.odm"\)', _lua)
    DD23_EXIT = int(_m.group(1)) if _m else None
arr = {a['name']: a['at'] for a in build['named_arrivals']}
# DD-20 (A8): live when its BLV's sidecar lists the three D4 entrances; its exits to D4 are events 33 (the cellar door
# to the guild's back stair) and 34 (the ladder to the jetty's shaft)
_dd20 = os.path.join(WORLD, 'maps/xeen_dd20.studio.yml')
DD20 = {a.get('name'): a for a in ((yaml.safe_load(open(_dd20)) or {}).get('arrivals') or [])} if os.path.exists(_dd20) \
    else {}
DD20_LIVE = all(k in DD20 for k in ('entrance:d4_guild', 'entrance:d4_shaft', 'entrance:d4_trapdoor'))
DD20_EXIT_GUILD, DD20_EXIT_SHAFT = 33, 34
# DD-12 and DD-14 (A8, installed 2026-11-21): their sidecars' arrivals
def _arrivals(stem):
    f = os.path.join(WORLD, 'maps/%s.studio.yml' % stem)
    return {a.get('name'): a for a in ((yaml.safe_load(open(f)) or {}).get('arrivals') or [])} if os.path.exists(f) else {}


DD12, DD14 = _arrivals('xeen_dd12'), _arrivals('xeen_dd14')
DD17, DD21, DD10C = _arrivals('xeen_dd17'), _arrivals('xeen_dd21'), _arrivals('xeen_dd10c')
DD22 = _arrivals('xeen_dd22')
# DD-22's way out to D6 (A8's exit preset on the hatch's inner face): the event that moves to xeen_d6.odm
_dd22_lua = os.path.join(WORLD, 'events/maps/xeen_dd22.lua')
DD22_EXIT = None
if os.path.exists(_dd22_lua):
    import re as _re
    _m = _re.search(r'RegisterEvent\((\d+), "[^"]*", function\(\)\n    evt.MoveToMap\([^)]*"xeen_d6.odm"\)',
                    open(_dd22_lua).read())
    DD22_EXIT = int(_m.group(1)) if _m else None
if DD22_EXIT is None:
    DD22 = {}


def into_back(blv, inside, back, yaw, note):
    """After a door's move: the dungeon's arrival asserted, then set back down at D6's own arrival."""
    a = inside['at']
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': blv}})
    add({'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}})
    add({'play_lua': {'source': 'close()'}})
    add({'assert': {'party_position': {'x': a[0], 'y': a[1], 'radius': 160}}})
    add({'note': note})
    add({'load_map': {'map': M}})
    face(back[0], back[1], yaw)


def dd20_round(note, enter_steps, inside, exit_event, back):
    """Into DD-20 by enter_steps, its arrival asserted, out by exit_event (the leave prompt, OK), D4's point."""
    add({'note': note})
    for st in enter_steps:
        add(st)
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd20.blv'}})
    add({'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}})
    add({'play_lua': {'source': 'close()'}})
    a = DD20[inside]['at']
    add({'assert': {'party_position': {'x': a[0], 'y': a[1], 'radius': 128, 'z_min': a[2] - 32, 'z_max': a[2] + 32}}})
    add({'clear_hostiles': {'radius': 3000}})
    add({'execute_event': {'id': exit_event}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': back[0], 'y': back[1], 'radius': 160}}})


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


def close():
    add({'play_lua': {'source': 'close(); wait(0.3)'}})


def walk(X, Y, note=None, timeout=120, radius=192, z=None):
    if note:
        add({'note': note})
    add({'walk_to': {'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'z_tolerance': 700, 'radius': radius,
                     'timeout_seconds': timeout, 'clear_hostiles': 3000}})


def walkc(x, y, note=None, timeout=120):
    walk(*W(x, y), note=note, timeout=timeout)


def face(X, Y, yaw, z=None):
    add({'set_pose': {'map': M, 'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'yaw': round(yaw, 4),
                      'pitch': 0.0}})
    add({'advance_runtime': {'seconds': 0.5}})


def jump(x, y, note, yaw=0.0):
    add({'note': note + ' (by teleport)'})
    face(*W(x, y), yaw)


sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a6/s32')
import hookwin    # s32: D-90 made most hooks status lines; such an event opens no window


def event(eid, note, dialog=True, text=None, check=None):
    add({'note': note})
    add({'execute_event': {'id': ev[eid]}})
    add({'advance_runtime': {'seconds': 0.5}})
    if dialog and hookwin.status_only(os.path.join(B, 'xeen_d6.lua'), ev[eid], passes=not any(
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


def ask(eid, note, answer, dialog_after=True, text=None, check=None):
    add({'note': note})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev[eid]}})
    add({'answer_input': {'text': answer}})
    add({'advance_runtime': {'seconds': 0.5}})
    if dialog_after:
        a = {'active': True}
        if text:
            a['text_contains'] = text
        add({'assert': {'dialog': a}})
    close()
    if check:
        add({'play_lua': {'source': check}})


def bit(q, on=True):
    return 'if %sqbit(%d) then error("qbit %d %s") end' % ('not ' if on else '', q, q, 'not set' if on else 'set')


def talk(npc, note, near):
    jump(near[0], near[1], note)
    add({'interact_actor': {'actor_index': npc_actor[npc]}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True}}})
    close()


# Opening hours (A4's house rows, 2026-11-21: the Dark Guild and the magic shop open 21:00-6:00): a house shut at the
# walk's hour (morning of the first day) shows the engine's "This place is open from ... to ..." status line.
HOURS = {}
for _line in open(os.path.join(WORLD, 'data_tables/house_data.txt')):
    _f = _line.rstrip('\n').split('\t')
    if _f[0].isdigit() and len(_f) > 21 and _f[-6].lstrip('-').isdigit() and _f[-5].lstrip('-').isdigit():
        HOURS[int(_f[0])] = (int(_f[-6]), int(_f[-5]))


def open_at(house, hour=10):
    start, end = HOURS.get(house, (0, 0))
    if start == end or (start <= 1 and end >= 24):
        return True
    return start <= hour < end if start < end else (hour >= start or hour < end)


def door(bid, note, expect, moves=False):
    b = doors[bid]
    if expect is not None and b.get('house') and not open_at(b['house']):
        note += ' (shut by day: the hours line)'
        expect = 'closed'
    dx, dy, dz = b['door']
    nx, ny = b['normal']
    sx, sy = round(dx + nx * 300), round(dy + ny * 300)
    add({'note': note})
    face(sx, sy, math.atan2(-ny, -nx), z=max(ground(sx, sy), dz))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    if moves:
        add({'advance_runtime': {'seconds': 0.3}})
        add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: the entrance window
        add({'select_topic': {'match_label': 'OK'}})
        return
    if expect == 'closed':
        add({'play_lua': {'source': "local s = status(); if not string.find(s, 'open from', 1, true) then "
                                    "error('no hours line: ' .. s) end"}})
    elif expect is not None:
        add({'assert': {'dialog': expect}})
    close()


# ======================================================================== D6's walk (A6 sub-agent, 2026-11-21)
DD16 = _arrivals('xeen_dd16')
TOWN_H = 1664


def hp(note, lo=None, hi=None):
    a = {'member_index': 0}
    if lo is not None:
        a['health_min'] = lo
    if hi is not None:
        a['health_max'] = hi
    add({'note': note})
    add({'assert': {'member_points': a}})


s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'advance_runtime': {'seconds': 2}})
add({'note': 'At load: the archers, the lava dwellers, the robots placed; Ambrose and the tethered griffin'})
for mid, n in ((11104, 9), (11105, 3), (11620, 11), (11621, 3), (11610, 16), (11611, 2), (11913, 1)):
    add({'assert': {'actor_count': {'monster_id': mid, 'min': n}}})
# ---------------------------------------------------------------- Necropolis
gx, gy = W(91.5, 72.4)
add({'note': "Necropolis's gate from outside without the pass: A3's refusal"})
face(gx, gy, -math.pi / 2)
event('evt:door:thing:np_gate_outer', 'The outer leaves (d6.necropolis_gate)', text='living need a pass')
add({'grant_item': {'item_id': 12336}})
event('evt:door:thing:np_gate_outer', 'With the pass (12336): the leaves open', dialog=False)
walk(*W(91.5, 76.6), note='Through the gate to the mirror (necropolis_gate)', timeout=60)
add({'note': 'From inside the gate is always open (D-49 change 8): reload (the leaves shut again), inner leaf'})
add({'load_map': {'map': M}})
face(*W(91.5, 75.2), math.pi / 2)
event('evt:door:thing:np_gate_inner', 'The inner leaves: open from inside', dialog=False)
for b in sorted((b for b in build['buildings'] if b.get('house') and b.get('door')), key=lambda b: b['house']):
    h = b['house']
    exp = {'active': True}     # F1 (merge point 40): a proprietor who lives there opens on his talk, not the lobby
    door(b['id'], '%s (house %d): its door' % (b.get('title', ''), h), exp)
face(*W(91.5, 77.4), 0.0)
event('evt:thing:np_mirror', 'The Mirror of Necropolis (4756)', dialog=True)
event('evt:thing:np_skull', "The talking skull (d6.skull)", text='necromancers')
for i in (1, 2, 3):
    event('evt:part:thing:np_book_%d/lectern' % i, 'A Book of the Dead (d6.book_dead_%d)' % i, dialog=False)
event('evt:thing:np_barrel', 'The barrel by the Warm Barrel', text='Food for the dead')
if 'entrance:d6_stair' in DD21:
    door('thing:dd21_crypt', "DD-21's crypt stair: into the Necropolis Sewer (entrance:d6_stair)", None, moves=True)
    into_back('xeen_dd21.blv', DD21['entrance:d6_stair'], arr['entrance:dd21_stair'], math.pi / 2,
              "Back to D6 (DD-21's way out is A8's; set down at entrance:dd21_stair)")
else:
    door('thing:dd21_crypt', "DD-21's crypt stair (sealed until DD-21 exists: a status line)", None)
# ---------------------------------------------------------------- the D5 pass, the zone sign
jump(101.4, 65.2, 'The border pass: the zone sign', yaw=0.0)
event('evt:thing:zone_sign', 'The zone sign (d6.zone_sign)', text='Forbidden Zone')
if any(st['id'] == 'thing:east_road_end' for st in yaml.safe_load(open(os.path.join(P, 'sketch.yml')))['structures']):
    event('evt:thing:east_road_end', 'The road east (D5 sealed)', text='closed')
D5_TRAVEL = any(l.startswith('xeen_d6.odm\t') and 'xeen_d5.odm' in l
                for l in open(os.path.join(WORLD, 'data_tables/outdoor_travels.txt')))
if D5_TRAVEL and os.path.exists(os.path.join(WORLD, 'maps/xeen_d5.odm')):
    # Session 14: A3's travel rows D5-D6 (7 days) are in: the pass at y 64 both ways (edge_d5_d6.json).
    add({'note': 'Off the east edge to D5 over the border pass (the travel prompt, OK)'})
    add({'walk_to': {'x': W(127.6, 64)[0], 'y': W(127.6, 64)[1], 'z': ground(*W(127, 64)), 'z_tolerance': 900,
                     'radius': 128, 'timeout_seconds': 150, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_d5.odm'}})
    add({'note': "Back west off D5's west edge at y 64: the prompt, OK; D6's east pass arrival"})
    add({'set_pose': {'map': 'xeen_d5.odm', 'x': W(2.5, 64)[0], 'y': W(2.5, 64)[1], 'z': ground(*W(126, 64)),
                      'yaw': math.pi, 'pitch': 0.0}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'walk_to': {'x': W(-0.4, 64)[0], 'y': W(-0.4, 64)[1], 'z': ground(*W(126, 64)), 'z_tolerance': 900,
                     'radius': 128, 'timeout_seconds': 150, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': arr['entrance:east_pass'][0], 'y': arr['entrance:east_pass'][1],
                                       'radius': 700}}})
else:
    add({'note': "The D5-D6 travel rows are not written: the east edge is not walked"})
# ---------------------------------------------------------------- Corak's pod, the crust
HX, HY = W(73.91, 68.91)
add({'note': "Before lava_cooled the crust is hidden and has no collision (A1): a party set over its place falls into "
             "the lava and burns"})
add({'setup_shortcut': {'kind': 'immortal', 'value': False}})
add({'setup_shortcut': {'kind': 'set_member_points', 'member_index': 0, 'health': 400}})
add({'set_pose': {'map': M, 'x': HX, 'y': HY, 'z': 1700, 'yaw': -0.7854, 'pitch': 0.0}})
add({'advance_runtime': {'seconds': 6}})
add({'assert': {'party_position': {'x': HX, 'y': HY, 'radius': 600, 'z_max': 1460}}})
hp('in the lava: hurt', hi=399)
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
face(*W(74.4, 69.6), -2.356)
door('thing:corak_pod', "Corak's hatch before lava_cooled: A3's fail line", {'active': True, 'text_contains': 'Nobody'})
add({'note': 'lava_cooled (111564): the crust shown on load'})
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111564, 'value': True}})
add({'load_map': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': False}})
add({'setup_shortcut': {'kind': 'set_member_points', 'member_index': 0, 'health': 400}})
add({'set_pose': {'map': M, 'x': HX, 'y': HY, 'z': 1500, 'yaw': -0.7854, 'pitch': 0.0}})
add({'advance_runtime': {'seconds': 6}})
add({'assert': {'party_position': {'x': HX, 'y': HY, 'radius': 200, 'z_min': 1450}}})
hp('on the crust (a BModel floor over lavtyl): no lava damage (A1)', lo=400)
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
door('thing:corak_pod', "Corak's hatch after lava_cooled: into DD-16", None, moves=True)
if 'entrance:d6_hatch' in DD16:
    a = DD16['entrance:d6_hatch']['at']
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd16.blv'}})
    add({'assert': {'party_position': {'x': a[0], 'y': a[1], 'radius': 200}}})
    add({'load_map': {'map': M}})
# ---------------------------------------------------------------- Alamar, the pyramid
face(*W(51.0, 55.2), math.pi / 2)
if 'entrance:d6_gate' in DD17:
    # s32 (F16, D-89): no Yes/No; without the Soul Box m33.arrival's refusal on the status line, no move; with it the
    # entrance window (row 5049), OK, DD-17's gatehall
    b_ = doors['thing:alamar_gatehouse']
    add({'note': "Alamar's gate without the Soul Box: m33.arrival's refusal on the status line, no move"})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % b_['event']}})
    add({'play_lua': {'source': "local s = status(); if not string.find(s, 'nothing I need to fear', 1, true) then "
                                "error('no refusal line: ' .. s) end"}})
    add({'assert': {'map': M}})
    add({'note': "With Corak's Soul Box (12364): the entrance window with row 5049, OK, into DD-17 (entrance:d6_gate)"})
    add({'grant_item': {'item_id': 12364, 'member_index': 0}})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % b_['event']}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'Every window is lit', 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})
    into_back('xeen_dd17.blv', DD17['entrance:d6_gate'], arr['entrance:dd17_gate'], math.pi / 2,
              "Back to D6 (set down at entrance:dd17_gate)")
    add({'play_lua': {'source': 'discard(12364)'}})
else:
    door('thing:alamar_gatehouse', "Alamar's gate (m33.castle_door's line; DD-17 sealed)",
         {'active': True, 'text_contains': 'Every window is lit'})
face(*W(54.6, 62.0), 0.0)
event('evt:part:thing:travel_pyramid/p', 'The travel pyramid before m30.done', text='moons are not aligned')
# ---------------------------------------------------------------- the west, the mines, the camp
jump(30.0, 63.4, 'Obelisk Knoll', yaw=math.pi / 2)
event('evt:thing:obelisk', "The obelisk: obelisks.d6 (dark_6)", dialog=False, check=bit(115055))
jump(46.0, 95.8, "DD-10C's adit", yaw=-math.pi / 2)
if 'entrance:d6_adit' in DD10C:
    add({'note': "'Enter the Mine?' (Yes/No buttons, D-72) Yes: into DD-10C (entrance:d6_adit)"})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev['evt:thing:dd10c_adit']}})
    add({'advance_runtime': {'seconds': 0.3}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: the entrance window
    add({'select_topic': {'match_label': 'OK'}})
    into_back('xeen_dd10c.blv', DD10C['entrance:d6_adit'], arr['entrance:dd10c_adit'], math.pi / 2,
              "Back to D6 (DD-10C's way out is A8's; set down at entrance:dd10c_adit)")
else:
    event('evt:thing:dd10c_adit', 'The adit (DD-10C sealed: a status line, no question)', dialog=False)
jump(36.6, 86.6, "The archers' camp: burn it", yaw=math.pi)
ask('evt:thing:archers_standard', '"Destroy?" Yes (d6.archers_camp, 116200; D-90: the status line)', 'Yes', dialog_after=False, check=bit(116200))
jump(78.0, 40.6, "Sheltem's pod", yaw=math.pi / 2)
door('thing:sheltem_pod', "Sheltem's hatch before m33.done (d6.sheltem_hatch's sealed line)",
     {'active': True, 'text_contains': 'sealed'})
if 'entrance:d6_hatch' in DD22:
    add({'note': "After m33.done (111662): the hatch's status line, into DD-22's airlock (entrance:d6_hatch)"})
    add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111662, 'value': True}})
    door('thing:sheltem_pod', "Sheltem's hatch after m33.done: into DD-22", None, moves=True)
    _a = DD22['entrance:d6_hatch']['at']
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd22.blv'}})
    add({'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}})
    add({'play_lua': {'source': 'close()'}})
    add({'assert': {'party_position': {'x': _a[0], 'y': _a[1], 'radius': 160}}})
    add({'note': "Out by DD-22's hatch (its exit event, 'Exit Escape Pod 2?' OK): D6's entrance:dd22_hatch"})
    add({'execute_event': {'id': DD22_EXIT}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    _b = arr['entrance:dd22_hatch']
    add({'assert': {'party_position': {'x': _b[0], 'y': _b[1], 'radius': 160}}})
    add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111662, 'value': False}})
# ---------------------------------------------------------------- FD-01's stair under the ruin (D-69 change 6)
FD01 = _arrivals('xeen_fd01')
_fd01_lua = os.path.join(WORLD, 'events/maps/xeen_fd01.lua')
FD01_EXIT = None
if os.path.exists(_fd01_lua):
    import re as _re
    _m = _re.search(r'RegisterEvent\((\d+), "[^"]*", function\(\)\n    evt.MoveToMap\([^)]*"xeen_d6.odm"\)',
                    open(_fd01_lua).read())
    FD01_EXIT = int(_m.group(1)) if _m else None
if 'entrance:d6_stair' in FD01 and FD01_EXIT is not None:
    _g = arr['entrance:fd01_stair']
    add({'note': "m33.done (111662): the ruin on load, FD-01's stair in the broken gatehouse's floor"})
    add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111662, 'value': True}})
    add({'load_map': {'map': M}})
    face(_g[0], _g[1], math.pi / 2, z=_g[2])
    add({'note': "Without the Cube: m39.depths_door's fail_text, no move"})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev['evt:thing:fd01_stair']}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'Nothing you carry'}}})
    close()
    add({'assert': {'map': M}})
    add({'note': "With the Cube of Power (12365): the mark goes out, down to FD-01's entrance:d6_stair"})
    add({'grant_item': {'item_id': 12365, 'member_index': 0}})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev['evt:thing:fd01_stair']}})
    add({'advance_runtime': {'seconds': 0.3}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: the entrance window
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_fd01.blv'}})
    add({'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}})
    add({'play_lua': {'source': 'for i = 1, 3 do if not close() then break end wait(0.5) end'}})
    _a = FD01['entrance:d6_stair']['at']
    add({'assert': {'party_position': {'x': _a[0], 'y': _a[1], 'radius': 160}}})
    add({'note': "Out by FD-01's exit preset at the stair's top (event %d, the leave window, OK): D6's "
                 "entrance:fd01_stair" % FD01_EXIT})
    add({'execute_event': {'id': FD01_EXIT}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': _g[0], 'y': _g[1], 'radius': 160}}})
    add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111662, 'value': False}})
    add({'load_map': {'map': M}})
# ---------------------------------------------------------------- Griffin Pass, Ambrose's flight
talk(5512, 'Ambrose at Griffin Pass', (61.6, 95.6))
add({'note': "m25.done (111503): Ambrose's topic 'Fly to Blackfang' calls m25.flight, which moves the party to "
             "DD-14's entrance:d6_griffin (A3)"})
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111503, 'value': True}})
FLIGHT = os.environ.get('D6_WALK_FLIGHT') == '1'
if not FLIGHT:
    add({'note': "SKIPPED (2026-11-21): Ambrose's topics use Xeen.onMap, whose GetCurrentMapName is nil in the topic "
                 "program (merge point 21): no topic is offered. D6_WALK_FLIGHT=1 walks it once A1/A3 fix it."})
    add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111503, 'value': False}})
jump(61.6, 95.6, 'Back to Ambrose', yaw=math.pi)
if not FLIGHT:
    steps.pop()
    steps.pop()
    steps.pop()
_flight = [{'interact_actor': {'actor_index': npc_actor[5512]}}, {'advance_runtime': {'seconds': 0.5}},
           {'select_topic': {'match_label': 'Fly to Blackfang'}},
           {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}}]
_flight += [{'play_lua': {'source': 'close(); wait(0.3)'}}, {'advance_runtime': {'seconds': 1.0, 'follow_map_move': True}},
            {'assert': {'map': 'xeen_dd14.blv'}}, {'assert': {'party_position': {'x': 0, 'y': -1472, 'radius': 250}}},
            {'load_map': {'map': M}}]
if FLIGHT:
    steps.extend(_flight)
    # load_map sets the party at the build's start (DD-10C's adit): back to the pass for the road down
jump(61.6, 95.6, 'Griffin Pass', yaw=math.pi)
# ---------------------------------------------------------------- the D1 edge
walk(*W(64.0, 104.0), note='Down the mountain road to the D1 arrival', timeout=150)
if TRAVEL_LIVE:
    add({'note': 'Off the south edge to D1 (the travel prompt, OK)'})
    add({'walk_to': {'x': W(64, 127.6)[0], 'y': W(64, 127.6)[1], 'z': ground(*W(64, 127.6)), 'z_tolerance': 900,
                     'radius': 128, 'timeout_seconds': 150, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_d1.odm'}})
    add({'note': "Back north from D1's arrival (y 19, its arrival line closed first) up the road off the north edge at "
                 "x 64 (session 14): the prompt, OK; D6's south road arrival"})
    # s16: arriving at D1's y 21 (A2's edge_spans), the travel's message window opens a moment after the arrival
    add({'advance_runtime': {'seconds': 2.0}})
    close()
    add({'walk_to': {'x': W(64, -0.4)[0], 'y': W(64, -0.4)[1], 'z': ground(*W(64, 126)), 'z_tolerance': 900,
                     'radius': 128, 'timeout_seconds': 150, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': arr['entrance:south_road'][0], 'y': arr['entrance:south_road'][1],
                                       'radius': 700}}})
else:
    add({'note': "A2's travel row D6-D1 is not written yet: the south edge is not walked"})

doc = {'id': 'xeen.d6.walk', 'title': 'D6 The Forbidden Zone: Necropolis, the pass, the pod and crust, Alamar, the west, '
       'Griffin Pass', 'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/d6/tools/gen_walk.py from the built map (A6). South edge walked: %s.\n'
            % ('yes, both ways' if TRAVEL_LIVE else 'no (A2 travel row pending)'))
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'travel', TRAVEL_LIVE)
