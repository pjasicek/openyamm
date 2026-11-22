#!/usr/bin/env python3
"""Writes D3's playtest.yml (the walk) from the built map (A5, 2026-11-20, seventh session; X4's gen_walk.py).

    gen_walk.py <project L4> <build folder> <asset root>

House doors from build.json, the adit's dark face and ground heights from the map's export, event numbers from
ids.lock.yml, actor indices of A4's NPCs from the built scene. A house door whose house A4 has not written into the
root's house_data.txt yet (X4's town file is still `planned`) is clicked and its event checked, without the house
screen; the walk says so in a note. Dungeons not installed in the root are passed by with a note.

Route: a new game on Sandcaster's square (the build's start): the mirror, Omid's well, the Vulture Repellant board,
the city's services and homes, the wizard quarter shut (its closed texts) and then open (q-d14.done), the guild gate
(DD-19, sealed), DD-18's shaft (sealed), Lucio's Jetty refused before m30.done and open after; the south gate from
inside, out to the caravan yard and the stables; the gate from outside refused without the pass and opened with it;
the Crossroads' stalls and well; Celia and Derek's cottage before and after q-c22.done; the obelisk; Vespar's ruin
(q-d8.handle); the caravan well; the Wrath Spring; the Eastern Tower's door without and with the key (sealed);
Thaddeus's hut and the Fountain of Youth before and after q-d18.done; the fruit huts; Cornelius; the north edge to D4 and back;
the west edge to D2.
"""
import json
import math
import os
import subprocess
import sys

import yaml

P, B, ROOT = sys.argv[1], sys.argv[2], sys.argv[3]
M = 'xeen_d3.odm'
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run(['openyamm-studio/build-xeen/oymap', 'export', os.path.join(B, M), '--out', exp_path], check=True,
               stdout=subprocess.DEVNULL)
_m = json.load(open(exp_path))['map']
hm = _m['terrain']['height_map']
bmodels = {b['name']: b for b in _m['bmodels']}
ids = yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))
ev = dict(ids['events'])
scene = yaml.load(open(os.path.join(B, 'xeen_d3.scene.yml')), Loader=yaml.CSafeLoader)
npc_actor = {a['npc_id']: a['actor_index'] for a in scene['initial_state']['actors'] if a.get('npc_id')}
_hd = os.path.join(ROOT, 'worlds/xeen/data_tables/house_data.txt')
HOUSES = {int(l.split('\t')[0]) for l in open(_hd) if l.split('\t')[0].isdigit()}
# A4's kinds: a residence of one person opens that person's talk, not the house screen
KIND = {h['id']: h['kind'] for h in yaml.safe_load(open(os.path.join(ROOT, 'worlds/xeen/source/towns/d3.yml')))['houses']}
_tr = open(os.path.join(ROOT, 'worlds/xeen/data_tables/outdoor_travels.txt')).read()
_ms = open(os.path.join(ROOT, 'worlds/xeen/data_tables/map_stats.txt'), encoding='latin-1').read()
HAVE = {k for k in ('dd18', 'dd19', 'dd07') if 'xeen_%s.blv' % k in _ms
        and os.path.exists(os.path.join(ROOT, 'worlds/xeen/maps/xeen_%s.blv' % k))}
_sp = open(os.path.join(ROOT, 'worlds/xeen/data_tables/edge_spans.yml')).read()
TRAVEL_D2 = (any(l.startswith('xeen_d3.odm\t') and 'xeen_d2.odm' in l for l in _tr.split('\n'))
             or 'map: xeen_d3.odm' in _sp)

# D4 (A6): installed with A2's rows D3 north -> D4 'down' and D4 south -> D3 'up'; the arrivals are the sides' starts
TRAVEL_D4 = (os.path.exists(os.path.join(ROOT, 'worlds/xeen/maps/xeen_d4.odm'))
             and any(l.startswith('xeen_d3.odm\txeen_d4.odm\t') for l in _tr.split('\n'))
             and any(l.startswith('xeen_d4.odm\t') and 'xeen_d3.odm' in l for l in _tr.split('\n')))
D3_NORTH_START = next(a['at'] for a in build['arrivals'] if a['entrance'] == 'entrance:north_road')
D4_SOUTH_START = None
if TRAVEL_D4:
    _d4 = yaml.safe_load(open(os.path.join(ROOT, 'worlds/xeen/maps/xeen_d4.studio.yml')))
    D4_SOUTH_START = next(a['at'] for a in _d4['arrivals'] if a['name'] == 'entrance:south_road')


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
    """Teleport (set_pose) to a cell: the walk has its legs in each part, not across the whole savannah."""
    add({'note': note})
    face(*W(x, y), 0.0)


def close():
    add({'play_lua': {'source': 'wait(0.3); close(); wait(0.3)'}})


def house(bid, closed=False):
    b = doors[bid]
    hid = b['house']
    dx, dy, dz = b['door']
    nx, ny = b['normal']
    sx, sy = round(dx + nx * 300), round(dy + ny * 300)
    # set_pose before the door (the streets are walked by the audit's reach; a straight walk_to across the city
    # climbs walls): D3's houses are many and close
    add({'note': '%s (%s, house %d): before its door, open it' % (b['title'], bid, hid)})
    face(sx, sy, math.atan2(-ny, -nx), z=max(ground(sx, sy), dz))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    if hid not in HOUSES:
        add({'note': 'house %d is not in house_data.txt yet (A4: d3.yml is still planned): the door\'s event ran' % hid})
        close()
    elif closed:
        add({'note': 'shut: its closed text'})
        add({'assert': {'dialog': {'active': True}}})
        close()
    elif KIND.get(hid) == 'residence':
        add({'note': 'a residence of one person opens that person\'s talk (MM7\'s rule), not the house screen'})
        add({'assert': {'dialog': {'active': True}}})
        add({'press_action': {'action': 'cancel_dialog'}})
        add({'advance_runtime': {'seconds': 0.3}})
    else:
        # F1 (merge point 40): a house whose proprietor is its only resident opens straight on his talk
        add({'assert': {'dialog': {'active': True}}})
        add({'press_action': {'action': 'cancel_dialog'}})
        add({'advance_runtime': {'seconds': 0.3}})


def event(eid, note, dialog=True, check=None):
    add({'note': note})
    add({'execute_event': {'id': ev[eid]}})
    add({'advance_runtime': {'seconds': 0.5}})
    if dialog:   # F13 (A5 s29): a touch's text is a status line, a note or a choice's answer a window: either
        add({'play_lua': {'source': "local s = status(); local w = close(); wait(0.3); "
                                    "if s == '' and not w then error('no text shown') end"}})
    if check:
        add({'play_lua': {'source': check}})


def window(text=None):
    """F16 (A5 s29): the standard entrance window (its trans.txt line or "Do you wish to enter"), OK."""
    add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
    add({'assert': {'dialog': dict({'active': True, 'action_label_present': 'OK'},
                                   **({'text_contains': text} if text else {}))}})
    add({'select_topic': {'match_label': 'OK'}})


def enter(eid, stem, at, z, note):
    """Through a door into a dungeon: the arrival map and spot, then back to D3 (load_map)."""
    key = stem.split('_')[1].split('.')[0]
    if key not in HAVE:
        add({'note': '%s is not installed in this root: not entered' % stem})
        return
    add({'note': note})
    add({'execute_event': {'id': ev[eid]}})
    window()
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': stem}})
    add({'assert': {'party_position': {'x': at[0], 'y': at[1], 'radius': 300, 'z_min': z - 80, 'z_max': z + 120}}})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})


def fruit(key, stat, cond):
    """A fruit hut (D-28 (4)): once per character (A3's player bit), +2 to the base stat and the condition, its
    line; the same character again: the 'nothing more' line and no second +2."""
    eid = ev['evt:thing:%s_basket' % key]
    add({'note': 'The %s hut: +2 %s (base) and %s, once per character (player bit fruit_%s); the line is status text'
                 % (key, stat, cond, key)})
    add({'lua_event': {'source': 'SetValue(Base%s, 20)' % stat}})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % eid}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'lua_event': {'source': "if not IsAtLeast(Base%s, 22) or IsAtLeast(Base%s, 23) then error('%s is not 22') end; "
                                 "if not IsAtLeast(%s, 1) then error('not %s') end" % (stat, stat, stat, cond, cond)}})
    add({'note': 'The same character again: the nothing-more line, no second +2'})
    add({'play_lua': {'source': 'click(%d); wait(0.5)' % eid}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'lua_event': {'source': "if IsAtLeast(Base%s, 23) then error('the %s worked twice') end" % (stat, key)}})


def mv(name, value):
    add({'assert': {'state_dump_map_var': {'index': ids['map_vars'][name], 'value': value}}})


def npc(npc_id, at, note):
    walkc(*at, note=note, timeout=90)
    add({'interact_actor': {'actor_index': npc_actor[npc_id]}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True}}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})


s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'assert': {'party_position': {'x': s['x'], 'y': s['y'], 'radius': 128}}})
# ---------------------------------------------------------------- Sandcaster: the square
event('evt:thing:sc_mirror', 'The Mirror of Sandcaster (Xeen.useMirror 4612)')
event('evt:thing:omid_well', "Omid's deep well (+5 Intellect, temporary)", dialog=False)
event('evt:thing:repellant_board', 'The Vulture Repellant board (dark/aaze0031:19, :25)')
event('evt:thing:quarter_notice', "The wizards' warning at the quarter stair (dark/aaze0031:29)")
SERVICES = ['building:sc_magic', 'building:sc_alchemist', 'building:sc_temple', 'building:sc_training',
            'building:sc_guild_mind', 'building:sc_guild_spirit', 'building:sc_guild_light', 'building:sc_tavern',
            'building:sc_weapons', 'building:sc_armour']
for bid in SERVICES:
    house(bid)
for i in range(1, 24):
    house('building:sc_houses#%d' % i)
if 'dd18' in HAVE:
    enter('evt:thing:dd18_shaft', 'xeen_dd18.blv', (0, 128), 0,
          "DD-18's street shaft by Barticus' Gym: down to the ladder's foot (entrance:d3_shaft)")
else:
    event('evt:thing:dd18_shaft', "DD-18's street shaft by Barticus' Gym: sealed until DD-18 is installed")
# ---------------------------------------------------------------- Lucio's Jetty (D-5.3, D-28: departs only)
house('building:sc_lucio_jetty', closed=True)
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 111600, 'value': True}})
add({'note': "m30.done (111600): Lucio's Jetty opens"})
house('building:sc_lucio_jetty')
# ---------------------------------------------------------------- the wizard quarter (q-d14.done 113281)
add({'note': 'Up the quarter stair'})
walk(*W(42.5, 29.8), timeout=60)
walk(*W(42.5, 26.4), timeout=60, z=1728)
for bid in ('building:wq_guild_dark', 'building:wq_magic', 'building:wq_houses#1', 'building:wq_houses#2',
            'building:wq_houses#3'):
    house(bid, closed=True)
if 'dd19' in HAVE:
    # D-72: A3's q-d14.quarter_gate line ends on "Enter?" and shows with Yes/No buttons; No stays; Yes enters DD-19
    # at entrance:d3_guild_gate; out by DD-19's gate (evt:exit_gate, the game's leave window) to entrance:dd19_gate
    _lua = open(os.path.join(ROOT, 'worlds/xeen/events/maps/xeen_dd19.lua')).read().splitlines()
    _exit = int(_lua[_lua.index('-- evt:exit_gate') + 1].split('(')[1].split(',')[0])
    _sy = yaml.safe_load(open(os.path.join(ROOT, 'worlds/xeen/maps/xeen_dd19.studio.yml')))
    _at = next(a['at'] for a in _sy['arrivals'] if a['name'] == 'entrance:d3_guild_gate')
    # where DD-19's exit puts the party (its MoveToMap, built from D3's entrance:dd19_gate)
    _i = _lua.index('-- evt:exit_gate')
    _back = [int(v) for v in next(l for l in _lua[_i:] if 'MoveToMap(' in l).split('MoveToMap(')[1].split(',')[:3]]
    add({'note': 'The guild gate: the entrance window with trans 5053 (F16); Close stays, then OK'})
    for label in ('Close', 'OK'):
        add({'play_lua': {'source': 'click(%d); wait(0.5)' % ev['evt:thing:dd19_gate']}})
        add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
        add({'assert': {'dialog': {'active': True, 'text_contains': 'sensitive to insults', 'action_label_present': 'OK'}}})
        add({'select_topic': {'match_label': label}})
        if label == 'Close':
            add({'advance_runtime': {'seconds': 0.5}})
            add({'assert': {'map': M}})
            add({'assert': {'dialog': {'active': False}}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd19.blv'}})
    add({'assert': {'party_position': {'x': _at[0], 'y': _at[1], 'radius': 300, 'z_min': _at[2] - 80,
                                       'z_max': _at[2] + 160}}})
    add({'note': "DD-19's guild gate (evt:exit_gate) back to D3 inside the quarter"})
    add({'execute_event': {'id': _exit}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': _back[0], 'y': _back[1], 'radius': 300, 'z_min': _back[2] - 80,
                                       'z_max': _back[2] + 160}}})
else:
    event('evt:thing:dd19_gate', "The guild gate (q-d14.quarter_gate), then sealed until DD-19 is installed")
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 113281, 'value': True}})
add({'note': 'q-d14.done (113281): the quarter opens'})
for bid in ('building:wq_guild_dark', 'building:wq_magic', 'building:wq_houses#1', 'building:wq_houses#2',
            'building:wq_houses#3'):
    house(bid)
# ---------------------------------------------------------------- the south gate (Q-D8), the caravan yard
go(36.5, 37.5, "Inside the south gate: the inner leaf opens from inside")
event('evt:thing:south_gate_inner_l', 'The gate swings open (no pass needed from inside)', dialog=False)
walk(*W(36.5, 41.5), 'Out through the south gate', timeout=60)
add({'assert': {'party_position': {'x': W(36.5, 41.5)[0], 'y': W(36.5, 41.5)[1], 'radius': 400}}})
house('building:sc_stables')
add({'load_map': {'map': M}})
add({'advance_runtime': {'seconds': 0.5}})
go(36.5, 41.5, 'Back at the south gate from outside after a reload (the gate shut): refused without the pass')
event('evt:thing:south_gate_outer_l', "q-d8.sandcaster_gate without the pass: the guards' line")
add({'grant_item': {'item_id': 12335, 'member_index': 0}})
add({'note': 'With the Sandcaster Pass (12335) the outer leaf opens'})
event('evt:thing:south_gate_outer_l', 'The gate swings open', dialog=False)
walk(*W(36.5, 36.0), 'In through the south gate', timeout=60)
add({'assert': {'party_position': {'x': W(36.5, 36.0)[0], 'y': W(36.5, 36.0)[1], 'radius': 400}}})
go(45.5, 31.5, 'The east gate from inside')
event('evt:thing:east_gate_inner_l', 'The east gate swings open', dialog=False)
walk(*W(49.5, 31.5), 'Out through the east gate', timeout=60)
# ---------------------------------------------------------------- the obelisk, the Crossroads, Celia and Derek
event('evt:thing:obelisk', 'The obelisk (obelisks.d3)')
go(60, 47.5, 'The Crossroads')
event('evt:thing:market_well', "The Crossroads' well", dialog=False)
for i in range(1, 7):
    house('building:xr_stall#%d' % i)
house('building:celia_derek_cottage', closed=True)
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 112442, 'value': True}})
add({'note': 'q-c22.done (112442): the cottage hook moves Celia and Derek in (q-c22.moved 112443)'})
house('building:celia_derek_cottage')
add({'play_lua': {'source': 'if not qbit(112443) then error("q-c22.moved not set") end'}})
add({'note': 'The cottage again (s25): q-c22.moved (112443) set, the door enters house 4647 without the hook'})
house('building:celia_derek_cottage')
# ---------------------------------------------------------------- the forest road: Vespar's ruin, Cornelius, the oak
go(45.0, 46.0, "Vespar's ruin by the caravan road")
event('evt:thing:vespar_rubble', "q-d8.handle: the emerald handle")
add({'play_lua': {'source': 'if not qbit(113161) then error("q-d8.handle_found not set") end'}})
npc(5247, (41.0, 72.6), 'Cornelius the Leprechaun in his glade (Perception)')
go(51.5, 63.6, 'The great oak by its lane')
add({'clear_hostiles': {'radius': 4000}})
event('evt:thing:great_oak', 'The great oak (+5 Personality, temporary)', dialog=False)
fruit('fig', 'Intellect', 'Insane')
# ---------------------------------------------------------------- the desert edge and the Wrath hills
go(63.5, 30.0, 'The caravan well')
add({'clear_hostiles': {'radius': 4000}})
event('evt:thing:caravan_well', 'The caravan well (+5 Endurance)', dialog=False)
go(85.0, 23.2, 'The Wrath Spring on the gorge lip')
add({'clear_hostiles': {'radius': 4000}})
event('evt:thing:wrath_spring', 'The Wrath Spring (+5 Might)', dialog=False)
# ---------------------------------------------------------------- the north edge to D4 and back (tenth session)
if TRAVEL_D4:
    go(88.0, 21.5, "The Lakeside road north to the edge: D4 (A2's row: 'down', 7 days)")
    add({'walk_to': {'x': W(88, 0.5)[0], 'y': W(88, 0.5)[1], 'z': 1760, 'z_tolerance': 900, 'radius': 128,
                     'timeout_seconds': 150, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_d4.odm'}})
    add({'assert': {'party_position': {'x': D4_SOUTH_START[0], 'y': D4_SOUTH_START[1], 'radius': 400}}})
    add({'note': "On D4's south start (entrance:south_road); back south over D4's south edge to D3's north start"})
    add({'walk_to': {'x': D4_SOUTH_START[0], 'y': -32563, 'z': 1632, 'z_tolerance': 900, 'radius': 128,
                     'timeout_seconds': 150, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': D3_NORTH_START[0], 'y': D3_NORTH_START[1], 'radius': 400}}})
else:
    event('evt:thing:north_road_end', "The Lakeside road's end: D4 not built")
go(93.0, 46.5, 'The Eastern Tower on its knoll')
add({'clear_hostiles': {'radius': 4000}})
add({'note': 'D-89: the Eastern Tower is open to all (no key)'})
if 'dd07' in HAVE:
    # A7's DD-07: in at entrance:d3_door, out by its tower door (evt:exit) before D3's tower door
    _lua = open(os.path.join(ROOT, 'worlds/xeen/events/maps/xeen_dd07.lua')).read().splitlines()
    _exit = int(_lua[_lua.index('-- evt:exit') + 1].split('(')[1].split(',')[0])
    _sy = yaml.safe_load(open(os.path.join(ROOT, 'worlds/xeen/maps/xeen_dd07.studio.yml')))
    _at = next(a['at'] for a in _sy['arrivals'] if a['name'] == 'entrance:d3_door')
    add({'note': "q-d18.tower_door (always passes, D-89), into DD-07 at entrance:d3_door"})
    add({'execute_event': {'id': ev['evt:door:thing:eastern_tower']}})
    window('smug')
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd07.blv'}})
    add({'assert': {'party_position': {'x': _at[0], 'y': _at[1], 'radius': 300, 'z_min': _at[2] - 80,
                                       'z_max': _at[2] + 160}}})
    add({'play_lua': {'source': 'if not qbit(113360) then error("q-d18.started not set") end'}})
    add({'note': "DD-07's tower door (evt:exit) back to D3 before the Eastern Tower"})
    add({'execute_event': {'id': _exit}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': 15360, 'y': 9216, 'radius': 300, 'z_min': 1780, 'z_max': 2080}}})
else:
    event('evt:door:thing:eastern_tower', 'With the Eastern Tower key: the hook passes, then sealed until DD-07 is '
          'installed')
# ---------------------------------------------------------------- the river meadows, Venom Pond
go(86.0, 65.5, 'The pear hut on the south bank')
fruit('pear', 'Might', 'Weak')
go(79.0, 74.5, "Thaddeus's yard by Venom Pond")
house('building:thaddeus_hut')
event('evt:thing:fountain_youth', 'The Fountain of Youth before q-d18.done: venom')
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 113364, 'value': True}})
event('evt:thing:fountain_youth', 'After q-d18.done: unnatural aging removed')
# ---------------------------------------------------------------- the west edge to D2
go(21.0, 44.0, 'The caravan road west to the edge: D2')
if TRAVEL_D2:
    add({'walk_to': {'x': W(17, 44)[0], 'y': W(17, 44)[1], 'z': ground(*W(18, 44)), 'z_tolerance': 600,
                     'radius': 128, 'timeout_seconds': 60, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_d2.odm'}})
    add({'assert': {'party_position': {'x': 21504, 'y': 10240, 'radius': 400}}})
    add({'note': "On D2's east road end; back east over D2's east edge to D3's west start (edge_spans)"})
    add({'walk_to': {'x': 23552, 'y': 10240, 'z': 1312, 'z_tolerance': 3000, 'radius': 128, 'timeout_seconds': 60,
                     'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': -22528, 'y': 10240, 'radius': 400}}})
else:
    add({'note': "D3's travel to D2 is not in this root yet (A2): the edge is passed by"})

doc = {'id': 'xeen.d3.walk', 'title': 'D3 Sandcaster and the Aging Forest: every door, the gates, the quarter and the ways out',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/d3/tools/gen_walk.py from the built map (A5, 2026-11-20).\n')
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'houses in the root', len(HOUSES & {b.get('house') for b in build['buildings']}),
      'travel d2', TRAVEL_D2, 'travel d4', TRAVEL_D4, D4_SOUTH_START)
