#!/usr/bin/env python3
"""Writes D4's playtest.yml (the walk) from the built map (A6, ninth session; D1's and D2's walks adapted): house doors
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
M = 'xeen_d4.odm'
TRAVEL_LIVE = any(l.startswith('xeen_d4.odm\t') and 'xeen_d3.odm' in l
                  for l in open(os.path.join(WORLD, 'data_tables/outdoor_travels.txt')))
TOWN = yaml.safe_load(open(os.path.join(WORLD, 'source/towns/d4.yml')))
CLOSED = {h['id']: h['closed_text'] for h in TOWN['houses'] if h.get('opens') == 'q-d22.done'}
ALONE = {h['id']: h['residents'][0] for h in TOWN['houses'] if len(h.get('residents') or []) == 1}
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run([os.path.join(ROOT, 'openyamm-studio/build-xeen/oymap'), 'export', os.path.join(B, M), '--out',
                exp_path], check=True, stdout=subprocess.DEVNULL)
hm = json.load(open(exp_path))['map']['terrain']['height_map']
ids = yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))
ev = dict(ids['events'])
scene = yaml.load(open(os.path.join(B, 'xeen_d4.scene.yml')), Loader=yaml.CSafeLoader)
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
    if dialog and hookwin.status_only(os.path.join(B, 'xeen_d4.lua'), ev[eid], passes=not any(
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


def ask(eid, note, answer, dialog_after=True, text=None, check=None, question=None):
    add({'note': note})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev[eid]}})
    if question:    # D-72 rule 3: the prompt's own text on screen before the answer (Yes/No buttons)
        add({'assert': {'dialog': {'active': True, 'text_contains': question}}})
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


def door(bid, note, expect, moves=False):
    b = doors[bid]
    dx, dy, dz = b['door']
    nx, ny = b['normal']
    sx, sy = round(dx + nx * 300), round(dy + ny * 300)
    add({'note': note})
    face(sx, sy, math.atan2(-ny, -nx), z=max(ground(sx, sy), dz))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    if moves:     # s32 (F16): the entrance window, OK
        add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
        add({'select_topic': {'match_label': 'OK'}})
        return
    if expect is not None:
        add({'assert': {'dialog': expect}})
    close()


s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'assert': {'party_position': {'x': s['x'], 'y': s['y'], 'radius': 200}}})
add({'advance_runtime': {'seconds': 2}})
add({'note': 'D-36 at load: the coven placed (A2: long), the five octopods in the water'})
add({'assert': {'actor_count': {'monster_id': 11170, 'min': 9}}})
add({'assert': {'actor_count': {'monster_id': 11470, 'min': 3}}})
# ---------------------------------------------------------------- the Isle
add({'note': "The Isle: up from the landing to DD-12's door (two leaves)"})
dx, dy, dz = doors['thing:isle_tower']['door']
walk(dx, dy - 420, timeout=90)
door('thing:isle_tower', "DD-12's door without the Lost Souls key: locked", None)
add({'grant_item': {'item_id': 12344}})
if 'entrance:d4_isle' in DD12:
    # DD-12 live (A8, 2026-11-21): in at entrance:d4_isle, out by its doors (event 35) to D4 (4096, -3072)
    a = DD12['entrance:d4_isle']['at']
    add({'note': "With the key (lost_souls_key): into DD-12 at entrance:d4_isle (%d, %d)" % (a[0], a[1])})
    door('thing:isle_tower', "DD-12's door with the key", None, moves=True)
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd12.blv'}})
    add({'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}})
    add({'play_lua': {'source': 'close()'}})
    add({'assert': {'party_position': {'x': a[0], 'y': a[1], 'radius': 160}}})
    add({'clear_hostiles': {'radius': 3000}})
    add({'note': "DD-12's doors to the Isle (event 35): back at D4 (4096, -3072), entrance:dd12_door"})
    add({'execute_event': {'id': 35}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': 4096, 'y': -3072, 'radius': 200}}})
else:
    door('thing:isle_tower', "With the key (lost_souls_key): DD-12 sealed until A8's DD-12 lists entrance:d4_isle", None)
add({'note': "The Isle Ferry (A4's house 4667, Tern): its house screen"})
add({'execute_event': {'id': ev['evt:thing:isle_ferry']}})
add({'advance_runtime': {'seconds': 0.5}})
add({'assert': {'dialog': {'active': True}}})
close()
# ---------------------------------------------------------------- Lakeside
jump(73.0, 89.5, "Lakeside's square (the mirror's and Town Portal's arrival)", yaw=math.pi / 2)
for b in sorted((b for b in build['buildings'] if b.get('house') and b.get('door')), key=lambda b: b['house']):
    h = b['house']
    if b['id'] == 'building:lk_guild':
        continue
    if h in CLOSED:
        exp = {'active': True, 'house_dialog': False, 'text_contains': CLOSED[h][:30]}
    elif h in ALONE:
        exp = {'active': True}
    else:
        exp = {'active': True}
    door(b['id'], '%s (house %d): its door' % (b.get('title', ''), h), exp)
add({'note': "The guild's door (q-d22.guild_door): the riddle, a wrong answer: 'Begone fools!' and the trapdoor "
             "(DD-20's sewer half sealed: a status line)"})
gb = doors['building:lk_guild']
gx, gy, gz = gb['door']
face(round(gx + gb['normal'][0] * 300), round(gy + gb['normal'][1] * 300), math.pi, z=gz)
if not DD20_LIVE:
    ask('evt:door:building:lk_guild', 'Wrong: "wolf"', 'wolf', text='Begone')
else:
    # DD-20 installed: the wrong answer drops the party through the trapdoor into the sewer half
    # (entrance:d4_trapdoor); up its ladder (34) to the jetty's shaft, then back to the guild's door
    dd20_round('Wrong: "wolf": the trapdoor into DD-20 (entrance:d4_trapdoor), up the ladder to the shaft',
               [{'play_lua': {'source': 'click(%d); wait(0.5)' % ev['evt:door:building:lk_guild']}},
                {'answer_input': {'text': 'wolf'}}],
               'entrance:d4_trapdoor', DD20_EXIT_SHAFT, (3072, -9728))
    face(round(gx + gb['normal'][0] * 300), round(gy + gb['normal'][1] * 300), math.pi, z=gz)
add({'play_lua': {'source': bit(113442, on=False)}})
ask('evt:door:building:lk_guild', 'Right: "witch" (q-d22.guild_right: membership, 113442)', 'witch', text='Correct',
    check=bit(113442))
door('building:lk_guild', 'The guild open now (4651)', {'active': True})
if not DD20_LIVE:
    event('evt:thing:guild_back_stair', "The guild's back stair for members (DD-20's coven hall sealed: a status line)",
          dialog=False)
else:
    dd20_round("The guild's back stair for members: into DD-20's coven hall (entrance:d4_guild) and out by the cellar "
               "door", [{'execute_event': {'id': ev['evt:thing:guild_back_stair']}},
                        {'advance_runtime': {'seconds': 0.5}},
                        {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}},
                        {'select_topic': {'match_label': 'OK'}}], 'entrance:d4_guild',
               DD20_EXIT_GUILD, (-1024, -13312))
event('evt:thing:lk_mirror', 'The Mirror of Lakeside before q-d22.done', dialog=True)
jump(SHX := 69.75, 83.2, 'The grated shaft by the jetty', yaw=-math.pi / 2)
if not DD20_LIVE:
    event('evt:thing:sewer_shaft', 'The grated shaft (DD-20 sealed: a status line, no question)', dialog=False)
else:
    dd20_round('"Climb down to the sewer?" Yes: into DD-20 (entrance:d4_shaft) and up its ladder again',
               [{'play_lua': {'source': 'click(%d); wait(0.5)' % ev['evt:thing:sewer_shaft']}},
                {'assert': {'dialog': {'active': True, 'text_contains': "sewer", 'action_label_present': 'OK'}}},
                {'select_topic': {'match_label': 'OK'}}],      # s32 (F16): the entrance window, row 5055
               'entrance:d4_shaft', DD20_EXIT_SHAFT, (3072, -9728))
event('evt:part:thing:beached_boat/hull', "Skiff's beached boat: 'This boat under repair.'", text='under repair')
talk(5318, 'Naomi in the stocks (Q-D22)', (71.2, 90.1))
# ---------------------------------------------------------------- the D3 road and the brow
jump(78.5, 91.2, 'East out of the square along the town road', yaw=0.0)
walkc(84, 91.5, timeout=90)
walkc(86, 95, 'Well Fork', timeout=90)
event('evt:thing:warding_well', 'The Fountain of Magic Resistance (+5 Mind and Body, once per character)',
      dialog=False)
walkc(86.5, 96.5, 'Up the Sandcaster road', timeout=120)
walkc(87.5, 100, timeout=120)
walkc(88, 102, 'Lakeside Brow', timeout=120)
walkc(88, 105, 'The D3 arrival', timeout=120)
if TRAVEL_LIVE:
    add({'note': 'Off the south edge to D3 (the travel prompt, OK)'})
    add({'walk_to': {'x': W(88, 127.6)[0], 'y': W(88, 127.6)[1], 'z': ground(*W(88, 127.6)), 'z_tolerance': 900,
                     'radius': 128, 'timeout_seconds': 150, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_d3.odm'}})
    add({'note': "Back north off D3's north edge at x 88 (D3's road): the prompt, OK; D4's south start"})
    add({'set_pose': {'map': 'xeen_d3.odm', 'x': 12288, 'y': 20480, 'z': 1760, 'yaw': round(math.pi / 2, 4),
                      'pitch': 0.0}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'walk_to': {'x': 12288, 'y': 32512, 'z': 1760, 'z_tolerance': 900, 'radius': 128, 'timeout_seconds': 150,
                     'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': arr['entrance:south_road'][0], 'y': arr['entrance:south_road'][1],
                                       'radius': 700}}})
else:
    add({'note': "A2's travel row D3-D4 is not written yet: the south edge is not walked"})
# ---------------------------------------------------------------- the north shore and the crag
jump(74.5, 54.0, "The north-shore track before Blackfang's gatehouse", yaw=0.0)
door('thing:blackfang_gatehouse', "The gate never opens (m25.blackfang_gate)",
     {'active': True, 'text_contains': 'Castle Blackfang does not take'})
add({'note': "D-42: after m25.done (111503) the gate asks; Yes: Ambrose's griffin (DD-14 sealed: a status line)"})
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111503, 'value': True}})
ask('evt:door:thing:blackfang_gatehouse', 'The gate after m25.done: "... fly you inside?" (a choice) Fly in', 'Fly in',
    dialog_after=False, question='Would you like my griffin to fly you inside?')
if 'entrance:d4_griffin' in DD14:
    g = DD14['entrance:d4_griffin']['at']
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd14.blv'}})
    add({'note': "Ambrose's griffin set the party on DD-14's walls at entrance:d4_griffin (%d, %d)" % (g[0], g[1])})
    add({'assert': {'party_position': {'x': g[0], 'y': g[1], 'radius': 200}}})
    add({'load_map': {'map': M}})
    add({'note': 'Back on D4 (by load_map)'})
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111503, 'value': False}})
add({'note': "The bat storm (m25.bat_storm): a party flying over the crag top is set down on the north shore"})
cx, cy = W(85.2, 46.2)
face(cx, cy, 0.0, z=3110)
add({'cast_spell': {'member_index': 0, 'spell_id': 21, 'skill': 10, 'mastery': 3}})
add({'assert': {'buff': {'spell_id': 21, 'present': True}}})
add({'movement_segment': {'input': 'none', 'fly_up': True, 'seconds': 1.5, 'actor_collision': False,
                          'actor_ai': False, 'start': {'map': M, 'x': cx, 'y': cy, 'z': 3110, 'yaw_degrees': 90,
                                                       'pitch': 0},
                          'expect_stop': {'map': M, 'x': cx, 'y': cy, 'z': 3600, 'yaw_degrees': 90, 'pitch': 0},
                          'loose_tolerance': True, 'tolerance_xy': 20000, 'tolerance_z': 5000}})
add({'advance_runtime': {'seconds': 3}})
dX, dY = W(75.6, 54.0)
add({'assert': {'party_position': {'x': dX, 'y': dY, 'radius': 300}}})
add({'note': 'Fly ended by the knock-down (evt.RemovePartyBuff, merge point 18)'})
add({'assert': {'buff': {'spell_id': 21, 'present': False}}})
# ---------------------------------------------------------------- the west shore, the forest, the mountain
jump(57.0, 82.6, 'Gull Knoll: the obelisk', yaw=math.pi / 2)
event('evt:thing:obelisk', "The obelisk: A3's obelisks.d4 (dark_4)", dialog=False, check=bit(115053))
talk(5319, 'Leafpoint in his grove (an MM7 Treant, friendly)', (42.0, 62.4))
talk(5320, 'Ector by his cabin (Q-D21)', (35.4, 73.2))
jump(47.0, 52.4, "The woodcutters' clearing: Ector's woodpile (q-d21.woodpile)", yaw=math.pi / 2)
event('evt:part:thing:woodpile/pile', 'The woodpile before Ector asks: firewood', dialog=False)
walkc(47.5, 51.0, 'Up the lair path', timeout=60)
walkc(48.2, 48.0, timeout=90)
walkc(47.6, 45.0, timeout=90)
walkc(46.4, 43.4, "DD-23's ledge", timeout=90)
# D-72: the hook's line, then Yes/No buttons "Enter the cave?"; the window shows the hook's message and the prompt's
# own line under it (A6 s24 probe), so the question is on screen
LAIR_PROMPT = 'Enter the cave?'
if DD23_EXIT is None:
    event('evt:thing:dd23_lair', "DD-23's cave mouth (sealed: a status line, no question)", dialog=False)
else:
    # DD-23 live (A7's BLV lists entrance:d4_mouth): in at its point, out by its mouth to D4's entrance:dd23_lair
    ins = DD23_MOUTH['at']
    add({'note': "DD-23's cave mouth: q-d15.lair_door's line, Enter? Yes: DD-23 at entrance:d4_mouth (%d, %d)"
                 % (ins[0], ins[1])})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev['evt:thing:dd23_lair']}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'very still', 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})     # s32 (F16): the entrance window, row 5058
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd23.blv'}})
    add({'assert': {'party_position': {'x': ins[0], 'y': ins[1], 'radius': 200}}})
    ex = arr['entrance:dd23_lair']
    add({'note': "DD-23's way out (its event %d) to D4's entrance:dd23_lair (%d, %d, %d)"
                 % ((DD23_EXIT,) + tuple(ex))})
    add({'clear_hostiles': {'radius': 3000}})
    add({'execute_event': {'id': DD23_EXIT}})
    add({'assert': {'dialog': {'active': True}}})          # the leave-map prompt (D2's dungeon exits)
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': ex[0], 'y': ex[1], 'radius': 200}}})
talk(5317, "Slibo at the wizards' camp", (27.4, 51.6))
event('evt:thing:magic_fountain', 'The Fountain of Great Magic (+200 SP, daily)', dialog=False)
jump(100.0, 39.6, 'The Fountain of Great Resilience', yaw=math.pi / 2)
event('evt:thing:resilience_fountain', 'The Fountain of Great Resilience (+200 HP, daily)', dialog=False)
jump(91.0, 85.0, 'The cairn on the east shore', yaw=0.0)
event('evt:thing:cairn', 'The cairn without the real map (q-c24.cairn)', dialog=False)
jump(94.0, 77.6, 'Mirabeth Point', yaw=0.6)
event('evt:thing:mirabeth', "Mirabeth's statue", dialog=False)
# A6 s27: the two small lamps pay once; the second rub says the genie has gone (no silent click)
for lamp, pay, gone in (('seat', 5000, 'Its genie has gone back in for good.'),
                        ('skerry', 8000, 'still wet. Its genie has gone.')):
    for k, expect in ((1, pay), (2, 0)):
        add({'note': 'The %s lamp, rub %d' % (lamp, k)})
        add({'play_lua': {'source': "remember('g', gold())"}})
        add({'execute_event': {'id': ev['evt:thing:genie_lamp_%s' % lamp]}})
        add({'advance_runtime': {'seconds': 0.5}})
        add({'play_lua': {'source': "local d = gold() - recall('g') if d ~= %d then error('lamp %s rub %d: ' .. d) end"
                                    % (expect, lamp, k)
                                    + ("" if k == 1 else " local s = status() if not string.find(s, %r, 1, true) "
                                       "then error('second rub: ' .. s) end" % gone)}})
jump(50.5, 93.4, "The Witches' Circle (a skull speaks)", yaw=math.pi / 2)
event('evt:thing:circle_skull_1', 'A skull on a stake', dialog=False)
D5_TRAVEL = any(l.startswith('xeen_d4.odm\t') and 'xeen_d5.odm' in l
                for l in open(os.path.join(WORLD, 'data_tables/outdoor_travels.txt')))
if not os.path.exists(os.path.join(WORLD, 'maps/xeen_d5.odm')):
    jump(21.0, 80.6, "The desert road's west end (D5 sealed)", yaw=math.pi)
    event('evt:thing:west_road_end', "The road's end sign", text='closed')
elif D5_TRAVEL:
    jump(23.0, 80.0, "The desert road at the forest's west edge (D5 live)", yaw=math.pi)
    add({'note': 'Off the west edge to D5 (the travel prompt, OK)'})
    add({'walk_to': {'x': W(-0.4, 80)[0], 'y': W(-0.4, 80)[1], 'z': ground(*W(0, 80)), 'z_tolerance': 900,
                     'radius': 128, 'timeout_seconds': 150, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_d5.odm'}})
    add({'note': "Back east off D5's east edge at y 80 (the desert road): the prompt, OK; D4's west start"})
    add({'set_pose': {'map': 'xeen_d5.odm', 'x': W(105, 80)[0], 'y': W(105, 80)[1], 'z': 1600, 'yaw': 0.0,
                      'pitch': 0.0}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'walk_to': {'x': W(127.6, 80)[0], 'y': W(127.6, 80)[1], 'z': 1550, 'z_tolerance': 900, 'radius': 128,
                     'timeout_seconds': 150, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': arr['entrance:west_road'][0], 'y': arr['entrance:west_road'][1],
                                       'radius': 700}}})
else:
    add({'note': "D5 is live but A2's D4-D5 travel row is not written: the west edge is not walked"})

doc = {'id': 'xeen.d4.walk', 'title': 'D4 Lakeside and Blackfang: the Isle, Lakeside, the brow, the crag, the west',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/d4/tools/gen_walk.py from the built map (A6). South edge walked: %s.\n'
            % ('yes' if TRAVEL_LIVE else 'no (A2 travel row pending)'))
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'travel', TRAVEL_LIVE)
