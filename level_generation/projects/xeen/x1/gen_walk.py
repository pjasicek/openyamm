#!/usr/bin/env python3
"""Writes X1's playtest.yml (the walk) from the built map: door positions from build.json, ground heights from the
map's export, event numbers from ids.lock.yml. Run after a build: gen_walk.py <project> <build folder>."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import math
import os
import subprocess
import sys
import yaml

P, B = sys.argv[1], sys.argv[2]
M = 'xeen_x1.odm'
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run(['openyamm-studio/build-xeen/oymap', 'export', os.path.join(B, M), '--out', exp_path], check=True,
               stdout=subprocess.DEVNULL)
_m = json.load(open(exp_path))['map']
terrain = _m['terrain']
bmin = {b['name']: b['min'] for b in _m['bmodels']}
hm = terrain['height_map']
ids = yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))
ev = {}
for k, v in ids.items():
    if isinstance(v, dict):
        ev.update(v)

def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))

# The world's edge_spans points (the orchestrator's 22:38 X7 rows; A5 13th session): a crossing asserts the span's
# own arrival point, within 128 across and -96/+160 in height.
_SPANS = yaml.safe_load(open(_REPO_ROOT + '/assets_dev/worlds/xeen/data_tables/edge_spans.yml'))


def span_point(src, dst):
    for row in _SPANS['edge_spans']:
        if row['map'] == src and row['to_map'] == dst and 'at' in row:
            return row['at']
    raise SystemExit('edge_spans has no point for %s -> %s' % (src, dst))


def assert_span(src, dst):
    x, y, z = span_point(src, dst)
    return {'assert': {'party_position': {'x': x, 'y': y, 'radius': 128, 'z_min': z - 96, 'z_max': z + 160}}}


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

doors = {b['id']: b for b in build['buildings']}
YAW = {'n': -math.pi / 2, 's': math.pi / 2, 'e': math.pi, 'w': 0.0}   # facing the door from outside it
steps = []
def add(s):
    steps.append(s)

def walk(X, Y, note=None, timeout=120, radius=160):
    if note:
        steps.append({'note': note})
    add({'walk_to': {'x': X, 'y': Y, 'z': ground(X, Y), 'z_tolerance': 600, 'radius': radius,
                     'timeout_seconds': timeout, 'clear_hostiles': 3000}})

def face(X, Y, yaw, pitch=0.0, z=None):
    add({'set_pose': {'map': M, 'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'yaw': round(yaw, 4),
                      'pitch': pitch}})
    add({'advance_runtime': {'seconds': 0.5}})

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import town as T
import dress as DR
import gen as G
# The world (A5 step 2): doors open A4's houses (the build's own row per door), items are A2's; a dungeon whose map
# is not installed in assets_dev/worlds/xeen/maps yet is passed by (its steps wait for its lane's install).
WORLD = G.IN_WORLD
WAREHOUSE_KEY, CRYSTAL_KEY = G.ITEMS['warehouse_key'], G.ITEMS['crystal_key']
INSTALLED = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../../assets_dev/worlds/xeen/maps')
WAITING = []

def installed(target):
    if not WORLD or os.path.exists(os.path.join(INSTALLED, target)):
        return True
    WAITING.append(target)
    return False
WAYS = DR.COBBLE + T.LANES

def cell(X, Y):
    return (X / 512.0 + 64, 64 - Y / 512.0)

def house(bid, house_id=None, walk_first=True, via=(), stairs=None):
    b = doors[bid]
    if house_id is None or WORLD:
        house_id = b['house']
        assert not WORLD or 4001 <= house_id <= 4050, (bid, house_id)
    dx, dy, _ = b['door']
    nx, ny = b['normal']
    sx, sy = round(dx + nx * 300), round(dy + ny * 300)
    if walk_first:
        for v in via:
            walk(*W(*v), timeout=90)
        # by the street: the nearest point of a road or lane to the place before the door, then the door
        d, q = T.nearest_on(WAYS, cell(sx, sy))
        if d > 0.3:
            walk(*W(*q), '%s (%s): along the street to its path' % (b['title'], bid), timeout=90)
        walk(sx, sy, '%s (%s): walk to its door and open it' % (b['title'], bid))
    z = None
    if stairs:
        # pass four: the door stands at the top of a flight (foot y0 at z0, top y1 at z1): the party on the steps
        (y0, z0), (y1, z1) = stairs
        yc = cell(sx, sy)[1]
        z = round(max(ground(sx, sy), z0 + (z1 - z0) * min(1.0, max(0.0, (y0 - yc) / (y0 - y1)))))
    face(sx, sy, math.atan2(-ny, -nx), z=z)
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    if WORLD and house_id >= 4018:
        # a Xeen residence with one resident opens straight into that person's talk
        add({'assert': {'dialog': {'active': True}}})
    else:
        # F1 (merge point 40): a house whose proprietor is its only resident opens straight on his talk
        add({'assert': {'dialog': {'active': True}}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})

FACE_Y = {(44, 31.4): 31.713, (62, 28.6): 28.912, (82, 30.4): 30.713}   # pass three: the click faces kept in place

def doorway_stand(cell):
    # the doorways look south (turn 0) unless turned; the party stands half a cell in front of the click face
    return W(cell[0], FACE_Y.get(tuple(cell), cell[1]) + 0.55)

def window():
    """F16 (A5 s29): the standard entrance window (its trans.txt line or "Do you wish to enter"), OK."""
    add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})

def enter(cell, target, note, stand=None, yaw=math.pi / 2, thing=None):
    if not installed(target):
        steps.append({'note': '%s: waits until %s is installed in the world' % (note, target)})
        return
    X, Y = stand or doorway_stand(cell)
    walk(X, Y, note, timeout=180)
    face(X, Y, yaw, z=max(ground(X, Y), bmin[thing][2]) if thing else None)
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    window()
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': target}})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})
    steps.append({'note': 'Back on X1 where the party stood (by load_map; XD-05 is walked out by its own exit)'})
    face(X, Y, yaw + math.pi)

def message_click(X, Y, yaw, note):
    steps.append({'note': note})
    face(X, Y, yaw)
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'play_lua': {'source': "local s = status(); local w = close(); wait(0.3); "
                                "if s == '' and not w then error('no text shown') end"}})   # F13 (A5 s29): status line or window

s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'assert': {'party_position': {'x': s['x'], 'y': s['y'], 'radius': 96}}})
steps.append({'note': "Mayor Gunther's errand in a window on arrival (a one-shot timer, 2 s)."})
add({'advance_runtime': {'seconds': 3.0}})
add({'assert': {'dialog': {'active': True}}})
add({'press_action': {'action': 'cancel_dialog'}})
# The town: the core's shops along the bent main street, the square, the south bank's guilds and Joe's yard
res = [k for k, v in doors.items() if v.get('house') == (4020 if WORLD else 1101)][0]
house('building:temple', 311, via=[(54, 44.2), (56.8, 44.1), (57, 45.8)])
house('building:bank', 286)
house('building:tavern', 240)
house('building:magic_shop', 85)
house('building:town_hall', 203, via=[(51.5, 43.2)], stairs=((43.0, 640), (41.3, T.UPPER_H)))
house('building:armour_shop', 47, via=[(47.5, 43)])
house('building:weapon_shop', 9, via=[(46.5, 44)])
house('building:alchemist', 117, via=[(47, 43.6)])
# The Adventurer's Inn (MM7's Tatalia inn, 1607): its door runs its event; the roster opens no house dialog in a
# headless run, so the walk checks the event only (the picture tour shows the roster screen).
_b = doors['building:inn']
_sx, _sy = round(_b['door'][0] + _b['normal'][0] * 300), round(_b['door'][1] + _b['normal'][1] * 300)
if WORLD:
    # A4's inn (4007) opens the Adventurer's Inn roster; a scenario closes it with escape (A1, merge point 13)
    walk(*W(44, 44), "The Adventurer's Inn (4007): its door opens the roster, escape closes it", timeout=60)
    walk(_sx, _sy)
    face(_sx, _sy, math.atan2(-_b['normal'][1], -_b['normal'][0]))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5, 'present_dialogs': True}})
    add({'assert': {'dialog': {'adventurers_inn': True}}})
    add({'press_action': {'action': 'escape'}})
    add({'advance_runtime': {'seconds': 0.3}})
    add({'assert': {'dialog': {'adventurers_inn': False}}})
else:
    walk(*W(44, 44), "The Adventurer's Inn: its door's event", timeout=60)
    walk(_sx, _sy)
    face(_sx, _sy, math.atan2(-_b['normal'][1], -_b['normal'][0]))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
house(res, 1101, via=[(44.5, 43.6), (44.5, 41.2)])
walk(*W(46.5, 44), 'Out of the west gate to the training hall', timeout=60)
walk(*W(41.5, 44), timeout=60)
walk(*W(39.0, 44), timeout=60)
house('building:training', 1571)
walk(*W(39.0, 44), 'Back in through the west gate, along the main street and out of the south gate', timeout=60)
walk(*W(41.5, 44), timeout=60)
walk(*W(46.5, 44), timeout=60)
walk(*W(47.5, 43), timeout=60)
walk(*W(51, 43), timeout=60)
walk(*W(52, 44), timeout=60)
walk(*W(52, 47.5))
walk(*W(52.5, 51.5), 'Over Vertigo Bridge')
walk(*W(52, 55))
house('building:guild_water', 140)
house('building:guild_earth', 146)
walk(*W(52, 55), timeout=60)
house('building:guild_air', 135)
house('building:guild_fire', 129)
# Joe's yard: the rain barrel (a decoration: run by its event, a headless run does not draw sprites to click)
walk(*W(52, 55), "Along the guild lane to Joe's yard: the key under the rain barrel", timeout=90)
walk(*W(59, 55), timeout=60)
walk(*W(59.2, 57.6), timeout=60)
walk(*W(60.2, 60.4))
walk(*W(61.3, 60.3))
# D-93 (A3 s40 for A5): a click on the rain barrel puts the key onto the cursor (quest hook m2.rain_barrel)
add({'play_lua': {'source': 'close(); click(%d); wait(0.5); if held() ~= %d then error("the rain barrel put no key on the '
                            'cursor") end; stow(); if not has_item(%d) then error("no warehouse key from the rain barrel") end'
                            % (ev['evt:thing:rain_barrel'], WAREHOUSE_KEY, WAREHOUSE_KEY)}})
# The culvert grate: barred until XD-01 lifts it from inside
# D-95: the grate is at the foot of a ditch cut into the bank (its end face at row 55, x 61.5): down the ramp from the
# lane north of the warehouse, the arch to the north
walk(*W(59.2, 57.6), timeout=60)
walk(*W(59.3, 56.2), timeout=60)       # west of the warehouse's door marks (7dec21 blocks the corner)
walk(*W(61.5, 56.2), timeout=60)
gx, gy = W(61.5, 55.3)
walk(gx, gy, 'The culvert grate at the foot of its ditch: barred from inside')
face(gx, gy, math.pi / 2, pitch=-0.2)
add({'press_interact': {'expect': {'kind': 'event_target'}}})
add({'advance_runtime': {'seconds': 0.5}})
add({'assert': {'map': M}})
walk(*W(61.5, 56.2), timeout=60)
walk(*W(59.3, 56.2), timeout=60)
walk(*W(59.2, 57.6), timeout=60)
# XD-01: the warehouse door (turned 90: it looks west; the party stands west of it, looking east)
enter((61.08, 58.3), 'xeen_xd01.blv', "XD-01 Joe's Warehouse: in by its loading doors", stand=W(60.45, 58.3), yaw=0.0, thing='thing:warehouse_door')
walk(*W(59.2, 57.6), 'Back along the guild lane, over the bridge, through the square and out of the east gate', timeout=60)
walk(*W(59, 55), timeout=60)
walk(*W(52, 55), timeout=60)
walk(*W(52.5, 51.5), timeout=60)
walk(*W(52, 47.5), timeout=60)
walk(*W(52, 44), timeout=60)
walk(*W(57, 44), timeout=60)
walk(*W(57, 46), timeout=60)
walk(*W(62.5, 46.5), timeout=60)
house('building:stables', 461)
walk(*W(62.5, 46.5), 'Back in by the east gate to the north street', timeout=60)
walk(*W(57, 46), timeout=60)
walk(*W(57, 44), timeout=60)
walk(*W(52, 44), timeout=60)
walk(*W(51, 43), timeout=60)
walk(*W(51, 40), timeout=60)
walk(*W(52, 39), timeout=60)
# North: out of the north gate, up the north road to the hill fork
walk(*W(52.5, 38), 'Out of the north gate, up the north road into the hills', timeout=60)
walk(*W(52, 35), timeout=90)
walk(*W(54, 33), timeout=90)
walk(*W(59, 33), timeout=90)
walk(*W(59, 32.5), timeout=90)
enter((44, 31.4), 'xeen_xd02.blv', 'XD-02 Red Dwarf Mines: along the mine lane to the timbered portal', thing='thing:mine_portal')
# The shaft head: barred until the Clan King's lever is thrown in XD-03; then a way down
sx, sy = doorway_stand((62, 28.6))
walk(sx, sy, "XD-03's escape shaft head: barred from below", timeout=180)
message_click(sx, sy, math.pi / 2, 'The hatch says where it opens from')
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 110031, 'value': True}})
enter((62, 28.6), 'xeen_xd03.blv', 'With the shaft opened from below (qbit 110031), the hatch leads down to the Deep Mine', thing='thing:shaft_head')
# XD-05: a round trip by the dungeon's own exit (its exit:x1 lands on entrance:xd05_mouth (9216, 16384, 1376), 512
# before the mouth, facing south; A7 2026-11-21)
def round_trip(cell, target, note, thing, exit_event, arrival, away):
    if not installed(target):
        steps.append({'note': '%s: waits until %s is installed in the world' % (note, target)})
        return
    X, Y = doorway_stand(cell)
    walk(X, Y, note, timeout=180)
    face(X, Y, math.pi / 2, z=max(ground(X, Y), bmin[thing][2]))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    window()
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': target}})
    steps.append({'note': 'Out again by the dungeon exit: back on X1 in front of the door, facing away from it'})
    add({'execute_event': {'id': exit_event}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.0, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    ax, ay = arrival
    add({'assert': {'party_position': {'x': ax, 'y': ay, 'radius': 128, 'z_min': ground(ax, ay) - 80,
                                       'z_max': ground(ax, ay) + 80}}})
    steps.append({'note': 'Off from the door on foot'})
    add({'walk_to': {'x': away[0], 'y': away[1], 'z': ground(*away), 'z_tolerance': 600, 'radius': 160,
                     'timeout_seconds': 30, 'clear_hostiles': 3000, 'close_dialogs': True}})

XD05_LOCK = yaml.safe_load(open('devdocs/xeen/briefs/xd05/L4/ids.lock.yml'))
round_trip((82, 30.4), 'xeen_xd05.blv', 'XD-05 Orc Caves: along the orc lane to the skull-hung mouth, in and out again',
           'thing:orc_cave_mouth', XD05_LOCK['events']['evt:exit_x1'], (9216, 16384), (9216, 15872))
# South: back through town, down the south road to Toad Meadow
walk(*W(66, 31), 'Back down to the hill fork and the north gate', timeout=120)
walk(*W(59, 33), timeout=120)
walk(*W(54, 33), timeout=120)
walk(*W(52, 35), timeout=120)
walk(*W(52.5, 38), timeout=120)
walk(*W(52, 39), timeout=60)
walk(*W(51, 40), timeout=60)
walk(*W(51, 43), timeout=60)
walk(*W(52, 44), timeout=60)
walk(*W(52, 47.5), timeout=60)
walk(*W(52.5, 51.5), timeout=60)
walk(*W(52, 58), 'Down the south road to the south fork', timeout=90)
walk(*W(54, 60), timeout=60)
walk(*W(54, 64), timeout=90)
walk(*W(57, 67), timeout=90)
walk(*W(57, 70), timeout=90)
walk(*W(60, 73), timeout=90)
walk(*W(62, 73), timeout=60)
walk(*W(63.5, 74.5), timeout=60)
walk(*W(72, 74.5), 'Along the toad lane to the hamlet', timeout=120)
# pass five: the tower's door looks north, toward the hamlet (was south, round the back); the party stands half a
# cell north of its click face and looks south
TOWER_STAND = W(88, 81.8)
walk(*W(80, 76.5), 'The tower path from the hamlet', timeout=120)
walk(*W(86, 79), timeout=90)
walk(*TOWER_STAND, 'The Witch Tower: sealed with crystal; Old Valia holds its key', timeout=120)
message_click(*TOWER_STAND, -math.pi / 2, 'The tower door names Valia')
add({'assert': {'map': M}})
walk(*W(86, 79), 'Back north to the hamlet', timeout=60)
walk(*W(80, 76.5), timeout=90)
b = doors['building:valia_cottage']
vx, vy = b['door'][0], b['door'][1] - 300
walk(vx, vy, "Old Valia's cottage: her errand and the Crystal Key", timeout=180)
if WORLD:
    # her house (A4's 4040); the key comes with her first topic (A3's m4: "Falista")
    steps.append({'note': "Valia's house: her Falista topic gives the Crystal Key"})
    face(vx, vy, math.pi / 2)
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'action_id': 40201, 'match_label': 'Quest'}})
    add({'advance_runtime': {'seconds': 0.3}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})
else:
    message_click(vx, vy, math.pi / 2, 'Valia gives the Crystal Key')
# D-89 (A5 s29): the Witch Tower is open; Valia gives no Crystal Key any more (12031 retired)
walk(*W(80, 76.5), 'Back to the tower with the key', timeout=60)
walk(*W(86, 79), timeout=90)
enter((88, 82.4), 'xeen_xd04.blv', 'XD-04 Witch Tower: the Crystal Key opens it', stand=TOWER_STAND, yaw=-math.pi / 2,
      thing='thing:witch_tower_door')
house('building:myra_hut', 1125)
# West: the west road's travel prompt (X3; Erathia as the stand-in), declined
walk(*W(72, 74.5), 'Back to town and out along the west road', timeout=120)
walk(*W(63.5, 74.5), timeout=90)
walk(*W(60, 73), timeout=90)
walk(*W(57, 70), timeout=90)
walk(*W(57, 67), timeout=90)
walk(*W(54, 64), timeout=90)
walk(*W(54, 60), timeout=90)
walk(*W(52, 58), timeout=60)
walk(*W(52.5, 51.5), timeout=60)
walk(*W(52, 47.5), timeout=60)
walk(*W(52, 44), timeout=60)
walk(*W(51, 43), timeout=60)
walk(*W(47.5, 43), timeout=60)
walk(*W(46.5, 44), timeout=60)
walk(*W(41.5, 44), timeout=90)
walk(*W(38.5, 44), timeout=90)
walk(*W(38.5, 46), timeout=90)
walk(*W(21, 46), timeout=120)
steps.append({'note': "The Water Reflector (M37, A3's hook): the prompt, Yes, and before M36 the hook's fail text"})
add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev['evt:thing:water_reflector']}})
add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})   # one prompt with Yes/No buttons (D-65 B1, D-66)
add({'assert': {'dialog': {'active': True, 'text_contains': 'below the rim. Reflector. Activate?'}}})
add({'answer_input': {'text': 'Yes'}})
add({'advance_runtime': {'seconds': 0.5}})
add({'assert': {'dialog': {'active': True}}})
add({'press_action': {'action': 'cancel_dialog'}})
add({'play_lua': {'source': 'if qbit(111743) then error("the reflector set its bit before M36") end'}})
add({'advance_runtime': {'seconds': 0.3}})
if installed('xeen_x2.odm'):
  add({'walk_to': {'x': W(18, 46)[0], 'y': W(18, 46)[1], 'z': ground(*W(18, 46)), 'z_tolerance': 600, 'radius': 128,
                 'timeout_seconds': 60, 'expect': 'dialog'}})
  add({'assert': {'dialog': {'active': True}}})
  add({'press_action': {'action': 'cancel_dialog'}})
  add({'assert': {'map': M}})
else:
  steps.append({'note': "The west road's travel prompt waits until xeen_x2.odm is installed in the world"})

# The north edge to X7 (D-40 change 6; A5 tenth session): over to X7's entrance:south_road and back over X7's south
# edge to X1's entrance:north_road (69, 21), as D3's D2 leg
if installed('xeen_x7.odm'):
  steps.append({'note': "The north road to the edge: X7 Mount Firestone and back"})
  face(*W(69, 22), math.pi / 2)
  add({'walk_to': {'x': W(69, 17.5)[0], 'y': W(69, 17.5)[1], 'z': ground(*W(69, 18)), 'z_tolerance': 900,
                   'radius': 128, 'timeout_seconds': 60, 'clear_hostiles': 3000, 'expect': 'dialog'}})
  add({'assert': {'dialog': {'active': True}}})
  add({'select_topic': {'match_label': 'OK'}})
  add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
  add({'assert': {'map': 'xeen_x7.odm'}})
  add(assert_span('xeen_x1.odm', 'xeen_x7.odm'))
  steps.append({'note': "On X7's south road; back south over X7's south edge to X1's north road"})
  add({'walk_to': {'x': 2560, 'y': -23552, 'z': 1856, 'z_tolerance': 3000, 'radius': 128, 'timeout_seconds': 60,
                   'clear_hostiles': 3000, 'expect': 'dialog'}})
  add({'assert': {'dialog': {'active': True}}})
  add({'select_topic': {'match_label': 'OK'}})
  add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
  add({'assert': {'map': M}})
  add(assert_span('xeen_x7.odm', 'xeen_x1.odm'))

doc = {'id': 'xeen.x1.walk', 'title': 'X1 Vertigo Meadows: the town and every dungeon entrance',
       'world': 'xeen' if WORLD else 'mm7',
       'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/x1/tools/gen_walk.py from the built map. A new game in Vertigo square:\n'
            '# the errand window, the town\'s houses, the rain barrel\'s key, the culvert grate (barred), XD-01 by\n'
            '# the warehouse doors, the north road to XD-02, the shaft head (barred, then open) to XD-03, XD-05 (in and out by its exit),\n'
            '# Toad Meadow (the tower barred, Valia\'s key, XD-04), and the west road\'s travel prompt.\n')
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'waiting on', sorted(set(WAITING)) or 'nothing')
