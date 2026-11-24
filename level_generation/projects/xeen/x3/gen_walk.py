#!/usr/bin/env python3
"""A5 (2026-11-20, fifth session): X3's playtest.yml (the walk) from the built map, after X2's gen_walk.py.
Run after a build: gen_walk.py [build folder]   (default output/studio_cal/x3/build_w; writes briefs/x3/L4/playtest.yml)

A new game at Ebenezer's camp: the tent and the shrine; up to Newcastle's gate (mirror, the foundation stair); the
Marsh Well and the obelisk; the foundation stair (refused without the deed, then into XD-13 and back); over the causeway to the Tower of High Magic (refused, then with the Enchanted Key into
XD-11 and back); Nightshadow: every door before the liberation (A4's closed texts; the Moon Guild and the manor open),
the boards and plinths, the coffin's two refusals, the dials turned to 9, 9, 9, night, the coffin open; after
q-c7.done every house with its screen (once A4's x3.yml is no longer `planned` and the generator has written the
houses: HOUSES_LIVE); the mirror and the well; the Lifeforce Spring; the Tomb's door (refused without the Stone of a
Thousand Terrors, then into XD-08 and back); the fen bridge, the west edge to X5; the north edge onto X4's ground (Z 992,
the world's edge_spans table); the east edge to X2. The scripted mist and sky after q-c7.done (evt.SetMist, evt.SetOutdoorSky) have
no scenario assertion: the load event runs on the reloads after q-c7.done, and the tour pictures show it."""
import json
import math
import os
import subprocess
import sys
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..'))
B = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'output/studio_cal/x3/build_w')
P = os.path.join(ROOT, 'devdocs/xeen/briefs/x3/L4')
M = 'xeen_x3.odm'
WT = os.path.join(ROOT, 'assets_dev/worlds/xeen/data_tables')
# the houses exist once the generator writes x3.yml's rows (A4 removes `planned`, A2/A4 run build_world.py)
HOUSES_LIVE = any(l.startswith('4107\t') for l in open(os.path.join(WT, 'house_data.txt'), encoding='latin-1'))
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
HAVE_XD11 = os.path.exists(os.path.join(ROOT, 'assets_dev/worlds/xeen/maps/xeen_xd11.blv'))
ENCHANTED_KEY = 12306
STONE_OF_TERRORS = 12304     # m10.tomb_door
DEED = 111160                # m8.deed
XD08_START = (0, 384)        # A7's XD-08 start inside the tomb door (its NOTES.md)
XD13_START = (0, 320)        # A7's XD-13 start in the keep gate (its NOTES.md)
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run([os.path.join(ROOT, 'openyamm-studio/build-xeen/oymap'), 'export', os.path.join(B, M), '--out',
                exp_path], check=True, stdout=subprocess.DEVNULL)
hm = json.load(open(exp_path))['map']['terrain']['height_map']
ids = yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))
ev = dict(ids['events'])


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
# a residence of one person opens that person's talk at once (MM7's rule), not the house screen (A4's x3.yml)
_town = yaml.safe_load(open(os.path.join(ROOT, 'assets_dev/worlds/xeen/source/towns/x3.yml')))
SINGLE = {h['id'] for h in _town['houses'] if len(h.get('residents') or []) == 1}
steps = []
add = steps.append


def walk(X, Y, note=None, timeout=120, radius=160, z=None):
    if note:
        add({'note': note})
    add({'walk_to': {'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'z_tolerance': 600, 'radius': radius,
                     'timeout_seconds': timeout, 'clear_hostiles': 3000, 'close_dialogs': True}})


def walkc(x, y, note=None, timeout=120, z=None):
    walk(*W(x, y), note=note, timeout=timeout, z=z)


def route(points, note=None, timeout=90, z=None):
    for k, p in enumerate(points):
        walkc(*p, note=note if k == 0 else None, timeout=timeout, z=z)


def face(X, Y, yaw, pitch=0.0, z=None):
    add({'set_pose': {'map': M, 'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'yaw': round(yaw, 4),
                      'pitch': pitch}})
    add({'advance_runtime': {'seconds': 0.5}})


def close():
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})


def door(bid, note, house_screen):
    """Walk to a door and click it: house_screen True asserts the house's screen (its own id), False a message."""
    b = doors[bid]
    dx, dy, dz = b['door']
    nx, ny = b['normal']
    sx, sy = round(dx + nx * 300), round(dy + ny * 300)
    walk(sx, sy, note, timeout=90)
    face(sx, sy, math.atan2(-ny, -nx), z=max(ground(sx, sy), dz))
    if house_screen and not HOUSES_LIVE:
        add({'note': '%s: house %s has no row yet (x3.yml is planned): not clicked' % (b['title'], b['house'])})
        return
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    if house_screen and b['house'] in SINGLE:
        add({'assert': {'dialog': {'active': True}}})
    elif house_screen:
        # F1 (merge point 40): a house whose proprietor is its only resident opens straight on his talk
        add({'assert': {'dialog': {'active': True}}})
    else:
        add({'assert': {'dialog': {'active': True}}})
    close()


def event(eid, note, dialog=True, check=None):
    add({'note': note})
    add({'execute_event': {'id': ev[eid]}})
    add({'advance_runtime': {'seconds': 0.5}})
    if dialog:   # F13 (A5 s29): a touch's text is a status line, a note or a choice's answer a window: either
        add({'play_lua': {'source': "local s = status(); local w = close(); wait(0.3); "
                                    "if s == '' and not w then error('no text shown') end"}})
    if check:
        add({'play_lua': {'source': check}})


def window():
    """F16 (A5 s29): the standard entrance window (its trans.txt line), OK."""
    add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})


def turn_dial(k, times):
    for _ in range(times):
        add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev['evt:thing:sundial_%d' % k]}})
        add({'assert': {'dialog': {'active': True, 'action_label_present': 'Yes'}}})   # D-72 (A5 s30): buttons
        add({'select_topic': {'match_label': 'Yes'}})
        add({'advance_runtime': {'seconds': 0.5}})
        add({'play_lua': {'source': 'close(); wait(0.3)'}})


s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'assert': {'party_position': {'x': s['x'], 'y': s['y'], 'radius': 128}}})
# ---------------------------------------------------------------- Ebenezer's camp
if HOUSES_LIVE:
    event('evt:thing:ebenezer_tent', "Ebenezer's Tent (house 4101)")
door('building:camp_shrine', 'The Camp Shrine (house 4102)', True)
event('evt:thing:rain_barrel', 'The rain barrel: "The barrel is empty." (aaze0012:13)', dialog=False)
# ---------------------------------------------------------------- Newcastle's gate
route([(86, 44), (84, 41.5), (82.5, 39.5), (82.5, 37.8)], 'Up the stair lane to the Newcastle gate')
event('evt:thing:newcastle_mirror', 'The Newcastle mirror (4121): dark until the keep stands (m11.keep)')
route([(83.5, 35.5), (84.5, 34.6)], "Into the ruin's courtyard: the foundation stair")
event('evt:thing:xd13_stair', 'XD-13: the foundation stair without the deed: refused (a board across the stair)')
add({'setup_shortcut': {'kind': 'set_qbit', 'id': DEED, 'value': True}})
add({'note': 'With the deed (m8.deed, 111160) the stair leads into XD-13 Newcastle Keep'})
add({'execute_event': {'id': ev['evt:thing:xd13_stair']}})
window()
add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
add({'assert': {'map': 'xeen_xd13.blv'}})
add({'assert': {'party_position': {'x': XD13_START[0], 'y': XD13_START[1], 'radius': 160}}})
add({'load_map': {'map': M}})
add({'advance_runtime': {'seconds': 0.5}})
add({'note': 'Back on X3 in the ruin (by load_map)'})
face(*W(84.5, 34.6), math.pi / 2)
event('evt:thing:yard_well', "The masons' well", dialog=False)
route([(82.5, 37.8), (82.5, 39.5), (84, 41.5), (86, 44)], 'Back down the stair lane')
# ---------------------------------------------------------------- west: the Marsh Well, the obelisk, the causeway
route([(80, 45.5), (74, 47.5), (68, 49.5), (63, 52)], 'West along the camp road to the causeway fork')
walkc(59.5, 47.5, 'The Marsh Well', timeout=60)
event('evt:thing:marsh_well', 'The Marsh Well: +10 to the four elements (temporary)', dialog=False)
route([(60, 46), (58.5, 40), (59.5, 32)], 'Up the north road to the obelisk')
event('evt:thing:obelisk', 'The obelisk: the third word, "HOARD"')
route([(58.5, 40), (60, 46), (63, 52)], 'Back to the causeway fork')
walkc(64.5, 55.5, 'Out over the causeway to the islet', timeout=60)
walkc(64.5, 58, timeout=60, z=940)
walkc(64.5, 62, timeout=60, z=940)
walkc(64.5, 66.5, timeout=60, z=992)
td = doors['thing:high_magic']['door']
tstand = (td[0], td[1] + 400)
walk(*tstand, "XD-11: the Tower of High Magic's door, facing north up the causeway", timeout=60, z=td[2])
add({'note': 'D-89: the door is open to all (the lock moved in to the study); the entrance window'})
if HAVE_XD11:
    face(tstand[0], tstand[1], -math.pi / 2, z=td[2])
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    window()
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_xd11.blv'}})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'note': 'Back on X3 at the tower door (by load_map)'})
    face(tstand[0], tstand[1], math.pi / 2, z=td[2])
walkc(64.5, 62, 'Back over the causeway', timeout=60, z=940)
walkc(64.5, 58, timeout=60, z=940)
walkc(64.5, 55.5, timeout=60)
# ---------------------------------------------------------------- Nightshadow, while the Count rules
route([(63, 52), (68, 49.5), (74, 47.5), (80, 45.5), (86, 44), (90, 43.5), (94, 42.5)],
      'East along the camp road to the crossroads')
route([(95.5, 48), (97, 54), (98.5, 59), (99.5, 62), (100.5, 66.5), (100.5, 70)], "South down Nightshadow's road")
NS_DOORS = ['building:moon_guild', 'building:gnome_home', 'building:nightshadow_houses#1',
            'building:nightshadow_tavern', 'building:nightshadow_houses#3', 'building:du_monay_manor',
            'building:nightshadow_houses#2', 'building:nightshadow_temple', 'building:treasure_trove',
            'building:nightshadow_alchemist', 'building:nightshadow_houses#8', 'building:nightshadow_houses#9',
            'building:nightshadow_houses#4', 'building:nightshadow_houses#6', 'building:nightshadow_houses#5',
            'building:nightshadow_houses#7']
OPEN_BEFORE = ('building:moon_guild', 'building:du_monay_manor')
for bid in NS_DOORS:
    b = doors[bid]
    if bid == 'building:moon_guild':
        # 4103 keeps night hours (21-6) while the Count rules: clicked after nightfall below
        walk(*[round(v) for v in (b['door'][0] + b['normal'][0] * 300, b['door'][1] + b['normal'][1] * 300)],
             'The Moon Guild (4103): night hours while the Count rules; clicked after dark', timeout=90)
    else:
        door(bid, '%s (%s) while the Count rules' % (b['title'], b['house']), bid in OPEN_BEFORE)
    walkc(100.5, 72.5, timeout=90)
# the square: boards, plinths, the coffin, the dials
walkc(99, 72.5, "Nightshadow's square: the boards, the plinths, the dials and the coffin", timeout=60)
event('evt:thing:rhyme_board', 'The rhyme board (q-c7.rhyme)')
event('evt:thing:count_sign', 'The sign at the dial walk (q-c7.sign_nine)')
event('evt:thing:dial_plinth_1', 'The first dial\'s plinth (q-c7.clue_stitch)')
event('evt:thing:dial_plinth_2', 'The second dial\'s plinth (q-c7.clue_cat)')
event('evt:thing:coffin_plinth', "The coffin's plinth (q-c7.sign_night)")
event('evt:thing:town_well', 'The town well before the liberation: black water (status text)', dialog=False)
event('evt:thing:nightshadow_mirror', "Nightshadow's mirror (4110): dark until q-c7.done")
event('evt:thing:coffin_closed', 'The coffin, first refusal: the dials are not set')
add({'note': 'The dial walk: 3, 6 and 12 turned to 9, 9 and 9 ; q-c7.dials_set (112142)'})
turn_dial(1, 6)
turn_dial(2, 3)
turn_dial(3, 9)
add({'play_lua': {'source': 'if not qbit(112142) then error("dials_set (112142) not set") end'}})
event('evt:thing:coffin_closed', 'The coffin with the dials set, by day (D-89: no night condition): the lid slides '
      'aside (q-c7.coffin)', check='if not qbit(112143) then error("coffin_opened (112143) not set") end')
add({'note': 'Night falls (game time to after 21:00): the Moon Guild by night'})
add({'advance_game_time': {'hours': 14}})
# XD-24 is entered only once the world knows the map (its map_stats row, A2): without the row the game cannot load it
XD24_ROW = 'xeen_xd24.blv' in open(os.path.join(ROOT, 'assets_dev/worlds/xeen/data_tables/map_stats.txt')).read()
if XD24_ROW:
    add({'note': "The open coffin's stair: into XD-24 at the coffin stair (0, 1600; P3 F45), then back"})
    add({'execute_event': {'id': ev['evt:thing:coffin_open']}})
    window()
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_xd24.blv'}})
    add({'assert': {'party_position': {'x': 0, 'y': 1600, 'radius': 160}}})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'note': 'Back on X3 on the square (by load_map)'})
else:
    add({'note': "The open coffin's stair into XD-24: waits for XD-24's map_stats row (A2) before the walk enters it"})
door('building:moon_guild', 'The Moon Guild (4103) by night', True)
walkc(100.5, 72.5, timeout=90)
# ---------------------------------------------------------------- after the liberation
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 112141, 'value': True}})
add({'note': 'Count Draco destroyed (q-c7.done, 112141): the town opens'})
add({'advance_game_time': {'hours': 10}})
add({'note': 'Morning: the shops keep day hours (6-18); the Moon Guild is 4104 by day now'})
# the well cures (subtract): a weak, diseased member drinks and is well after (A3, eighth session)
add({'setup_shortcut': {'kind': 'set_condition', 'member_index': 0, 'condition': 'weak'}})
add({'setup_shortcut': {'kind': 'set_condition', 'member_index': 0, 'condition': 'disease_weak'}})
add({'setup_shortcut': {'kind': 'set_condition', 'member_index': 0, 'condition': 'disease_severe'}})
event('evt:thing:town_well', 'The town well after the liberation: cured and +10 Personality', dialog=False)
for cond, mi in (('weak', 0), ('disease_weak', 0), ('disease_severe', 0)):
    add({'assert': {'condition': {'name': cond, 'present': False, 'member_index': mi}}})
if HOUSES_LIVE:
    for bid in NS_DOORS:
        b = doors[bid]
        door(bid, '%s after the liberation' % b['title'], True)
        walkc(100.5, 72.5, timeout=90)
# ---------------------------------------------------------------- south: the shore and the Lifeforce Spring
route([(100.5, 75), (101, 79), (102.5, 82), (103, 84.5)], 'Down the south street to the shore path')
route([(96, 87.5), (88, 89), (80, 91.5), (75.5, 93)], 'West along the shore path to the Lifeforce Spring',
      timeout=120)
event('evt:thing:lifeforce_spring', 'The Lifeforce Spring: +2 Endurance once per character (player bit 11280)',
      dialog=False)
# ---------------------------------------------------------------- the Gloomwood and the Tomb
route([(73, 93.5), (66, 92), (58, 90.5), (50, 88), (42, 84), (34, 79)], 'West through the Gloomwood to the Tomb fork',
      timeout=150)
walkc(34, 82.3, "XD-08: the Tomb's barrow door", timeout=60)
add({'note': 'D-89: the Tomb is open to all: its door leads into XD-08 (the entrance window)'})
add({'execute_event': {'id': ev['evt:thing:tomb']}})
window()
add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
add({'assert': {'map': 'xeen_xd08.blv'}})
add({'assert': {'party_position': {'x': XD08_START[0], 'y': XD08_START[1], 'radius': 160}}})
add({'load_map': {'map': M}})
add({'advance_runtime': {'seconds': 0.5}})
add({'note': 'Back on X3 at the tomb lane (by load_map)'})
face(*W(34, 81.5), math.pi / 2)
# ---------------------------------------------------------------- north over the fen bridge to the west edge
route([(34, 79), (34.5, 74), (36, 68.5)], 'North on the tomb path to the fen bridge', timeout=120)
walkc(37, 66.5, 'Over the fen bridge', timeout=60, z=None)
walkc(37, 62, timeout=60, z=None)
route([(36, 60.5), (35, 58.5), (28, 59), (22, 59)], 'West along the fen road to the west edge', timeout=120)
add({'walk_to': {'x': W(17, 59)[0], 'y': W(17, 59)[1], 'z': ground(*W(17, 59)), 'z_tolerance': 600, 'radius': 128,
                 'timeout_seconds': 60, 'expect': 'dialog'}})
add({'assert': {'dialog': {'active': True}}})
add({'note': 'Accepted: on to X5 Winterkill Tundra'})
add({'select_topic': {'match_label': 'OK'}})
add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
add({'assert': {'map': 'xeen_x5.odm'}})
add({'load_map': {'map': M}})
add({'advance_runtime': {'seconds': 0.5}})
# ---------------------------------------------------------------- the north edge to X4 (D-11.6, edge_spans)
add({'note': "To the north road by teleport, then up it and off the north edge: the travel prompt, X4's x 36 arrival"})
face(*W(51, 30), math.pi / 2)
route([(51, 22), (50, 21)], timeout=90)
add({'walk_to': {'x': W(50, 17)[0], 'y': W(50, 17)[1], 'z': ground(*W(50, 17)), 'z_tolerance': 3000,
                 'radius': 128, 'timeout_seconds': 60, 'expect': 'dialog'}})
add({'assert': {'dialog': {'active': True}}})
add({'select_topic': {'match_label': 'OK'}})
add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
add({'assert': {'map': 'xeen_x4.odm'}})
add({'assert': {'party_position': {'x': -14336, 'y': -22016, 'radius': 400, 'z_min': 900, 'z_max': 1100}}})
add({'load_map': {'map': M}})
add({'advance_runtime': {'seconds': 0.5}})
# ---------------------------------------------------------------- the east edge to X2
add({'note': 'Back to the east entry by teleport, then the road to the east edge: the travel prompt (X2), accepted'})
face(*W(104, 40.5), 0.0)
walkc(106, 40, timeout=60)
add({'walk_to': {'x': W(111, 40)[0], 'y': W(111, 40)[1], 'z': ground(*W(111, 40)), 'z_tolerance': 600,
                 'radius': 128, 'timeout_seconds': 60, 'expect': 'dialog'}})
add({'assert': {'dialog': {'active': True}}})
add({'select_topic': {'match_label': 'OK'}})
add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
add({'assert': {'map': 'xeen_x2.odm'}})

doc = {'id': 'xeen.x3.walk', 'title': 'X3 Lifeforce Lagoon: the camp, Newcastle, the Tower, Nightshadow and every door',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/x3/tools/gen_walk.py from the built map (see its docstring).\n'
            '# HOUSES_LIVE %s: house screens %s.\n' % (HOUSES_LIVE, 'asserted' if HOUSES_LIVE else
                                                         'skipped until x3.yml\'s houses are generated'))
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'houses live', HOUSES_LIVE)
