#!/usr/bin/env python3
"""Writes X4's playtest.yml (the walk) from the built map (A5, 2026-11-20; adapted from X2's tools/gen_walk.py).

    gen_walk.py <project L4> <build folder> <asset root>

House doors from build.json, the adit's dark face and ground heights from the map's export, event numbers from
ids.lock.yml, actor indices of A4's NPCs from the built scene. A house door whose house A4 has not written into the
root's house_data.txt yet (X4's town file is still `planned`) is clicked and its event checked, without the house
screen; the walk says so in a note. Dungeons not installed in the root are passed by with a note.

Route: a new game on Asp's square (the build's start); the rule stone, the pedestals (a wrong touch undone, then the
solution: q-c5.pedestals, qbit 112101), Asp's mirror (fogged until q-c5.done), the undercroft stair into XD-25, Adam
and Eve, Asp's services; the south edge west of x 0 into X3 (D-11.6, edge_spans) and back; the Autumn Druid; the
barbarian camp (No, then Yes: x4.barbarian_camp, qbit 116060); Burlock: the mirror, the well, the herald, the six
services, the castle gate into XD-07; the lists' challenge (refused under Might 30); the Olympian Fountain; the eyrie
into XD-26, Carlawna's hut; the renegades' camp; the ogres' camp; XD-02's west adit refused, then with qbit 110020
entered; Falagar's hut; Joe; the south edge to X2 accepted.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import math
import os
import subprocess
import sys

import yaml

P, B, ROOT = sys.argv[1], sys.argv[2], sys.argv[3]
M = 'xeen_x4.odm'
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run(['openyamm-studio/build-xeen/oymap', 'export', os.path.join(B, M), '--out', exp_path], check=True,
               stdout=subprocess.DEVNULL)
_m = json.load(open(exp_path))['map']
hm = _m['terrain']['height_map']
bmodels = {b['name']: b for b in _m['bmodels']}
ids = yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))
ev = dict(ids['events'])
scene = yaml.load(open(os.path.join(B, 'xeen_x4.scene.yml')), Loader=yaml.CSafeLoader)
npc_actor = {a['npc_id']: a['actor_index'] for a in scene['initial_state']['actors'] if a.get('npc_id')}
_hd = os.path.join(ROOT, 'worlds/xeen/data_tables/house_data.txt')
HOUSES = {int(l.split('\t')[0]) for l in open(_hd) if l.split('\t')[0].isdigit()}
HAVE = {k for k in ('xd02', 'xd07', 'xd25', 'xd26')
        if os.path.exists(os.path.join(ROOT, 'worlds/xeen/maps/xeen_%s.blv' % k))}
_ms = open(os.path.join(ROOT, 'worlds/xeen/data_tables/map_stats.txt')).read()
X3_ROW = '\txeen_x3.odm\t' in _ms and os.path.exists(os.path.join(ROOT, 'worlds/xeen/maps/xeen_x3.odm'))
_tr = open(os.path.join(ROOT, 'worlds/xeen/data_tables/outdoor_travels.txt')).read()
TRAVEL_X2 = any(l.startswith('xeen_x4.odm\t') and 'xeen_x2.odm' in l for l in _tr.split('\n'))


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
    walk(sx, sy, '%s (%s, house %d): walk to its door and open it' % (b['title'], bid, hid))
    face(sx, sy, math.atan2(-ny, -nx), z=max(ground(sx, sy), dz))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    if hid not in HOUSES:
        add({'note': 'house %d is not in house_data.txt yet (A4: x4.yml is still planned): the door\'s event ran' % hid})
        close()
    elif closed:
        add({'note': 'shut until q-c5.done: its closed text'})
        add({'assert': {'dialog': {'active': True}}})
        close()
    elif '_houses#' in bid or bid.endswith('_hut'):
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


def window():
    """F16 (A5 s29): the standard entrance window (its trans.txt line or "Do you wish to enter"), OK."""
    add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})


def enter(eid, stem, at, z, note):
    """Through a door into one of A7's dungeons: the arrival map and spot (its start), then back to X4."""
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
# ---------------------------------------------------------------- Asp: the square, the pedestals (D-4, Q-C5)
event('evt:thing:rule_stone', "The rule stone by the undercroft stair: the pedestals' rhyme (q-c5.pedestal_rhyme)")
add({'note': 'A wrong touch: pedestal 2 to red, then back to blue (the else branch keeps its order)'})
add({'play_lua': {'source': 'click(%d); wait(0.5); close()' % ev['evt:thing:pedestal_2']}})
mv('ped_2', 1)
add({'play_lua': {'source': 'click(%d); wait(0.5); close()' % ev['evt:thing:pedestal_2']}})
mv('ped_2', 0)
add({'note': 'The solution: 1, 3, 5, 7 red (the south-west first, alternating): the timer fires q-c5.pedestals'})
add({'play_lua': {'source': '\n'.join('click(%d); wait(0.4); close()' % ev['evt:thing:pedestal_%d' % i]
                                      for i in (1, 3, 5, 7)), 'max_seconds': 10}})
for i in range(1, 9):
    mv('ped_%d' % i, i % 2)
add({'advance_runtime': {'seconds': 2.0}})
add({'assert': {'dialog': {'active': True}}})
add({'press_action': {'action': 'cancel_dialog'}})
add({'play_lua': {'source': 'if not qbit(112101) then error("q-c5.pedestals (112101) not set") end'}})
event('evt:thing:asp_mirror', "Asp's mirror: fogged until q-c5.done")
enter('evt:thing:xd25_stair', 'xeen_xd25.blv', (-2208, 1760), 256,
      "XD-25: down the undercroft stair (open from day one) to the stair's top inside, facing east")
event('evt:thing:asp_well', "Asp's well", dialog=False)
npc(4301, (43.0, 84.6), 'Adam by the well (Q-C5)')
npc(4302, (43.0, 86.4), 'Eve by the well (Q-C5)')
house('building:asp_houses#1')                                  # Sarah Slither, open from day one
house('building:asp_alchemist', closed=True)
house('building:asp_houses#2', closed=True)
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 112102, 'value': True}})
add({'note': 'q-c5.done (112102, the transformer in XD-25): the cursed houses open'})
house('building:asp_alchemist')
house('building:asp_guild_earth')
house('building:asp_guild_body')
house('building:asp_armour')
house('building:asp_houses#2')
event('evt:thing:asp_sign', "Asp's town sign")
house('building:asp_shrine')
house('building:asp_travel_pit')
event('evt:thing:signpost_5', 'The signpost at the Asp road fork (x4.sign_asp)')
# ---------------------------------------------------------------- the Asp road south: X3's edge span (D-11.6)
go(36, 103.5, 'Down the Asp road to the south edge west of x 0: X3 (D-11.6, the world\'s edge_spans)')
event('evt:thing:x3_road_end', 'The sign at the road end', dialog=False)
if X3_ROW:
    add({'walk_to': {'x': W(36, 111)[0], 'y': W(36, 111)[1], 'z': ground(*W(36, 107)), 'z_tolerance': 3000,
                     'radius': 128, 'timeout_seconds': 60, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_x3.odm'}})
    add({'assert': {'party_position': {'x': -7168, 'y': 22016, 'radius': 300}}})
    add({'note': "On X3's north road end; back to X4 (load_map: X3's own way north is the lead's)"})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})
else:
    add({'note': 'X3 has no map_stats row in this root yet: the edge is passed by'})
# ---------------------------------------------------------------- the west: the Autumn Druid, the barbarian camp
go(28, 72, "The Autumn Druid's grove")
npc(4321, (26.6, 71.0), 'The Autumn Druid in her ring (Q-C1, T1-C)')
go(28, 58.5, 'The barbarian camp (x4.barbarian_camp)')
add({'clear_hostiles': {'radius': 3000}})
tent = ev['evt:thing:barbarian_tent_1']
CAMP_ASK = 'You have stumbled upon a Barbarian encampment. Burn?'   # D-72: one Yes/No prompt with buttons
add({'play_lua': {'source': 'click(%d); wait(0.5)' % tent}})
add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
add({'assert': {'dialog': {'active': True, 'text_contains': CAMP_ASK}}})
add({'answer_input': {'text': 'No'}})
add({'advance_runtime': {'seconds': 1}})
add({'play_lua': {'source': 'close()\nif qbit(116060) then error("the camp burnt on No") end'}})
add({'play_lua': {'source': 'click(%d); wait(0.5)' % tent}})
add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
add({'assert': {'dialog': {'active': True, 'text_contains': CAMP_ASK}}})
add({'answer_input': {'text': 'Yes'}})
add({'advance_runtime': {'seconds': 1}})
add({'play_lua': {'source': 'close(); wait(0.3); close()\nif not qbit(116060) then error("barbarian_camp not set") end'}})
event('evt:thing:barbarian_tent_2', 'Burnt: the other tents say so', dialog=False)
# ---------------------------------------------------------------- the desert road west: X6 (A2's edge_spans row)
X6_ROW = 'xeen_x6.odm' in open(os.path.join(ROOT, 'worlds/xeen/data_tables/map_stats.txt'), encoding='latin-1').read()
if X6_ROW:
    go(24, 60, 'The desert road west to the edge: X6 Desert of the Sphinx (7 days)')
    add({'walk_to': {'x': W(16.5, 60)[0], 'y': W(16.5, 60)[1], 'z': ground(*W(20, 60)), 'z_tolerance': 3000,
                     'radius': 128, 'timeout_seconds': 60, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_x6.odm'}})
    add({'assert': {'party_position': {'x': 22016, 'y': 2048, 'radius': 300}}})
    add({'note': "On X6's east road end; back to X4 (X6's walk crosses its east edge itself)"})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})
else:
    add({'note': 'X6 has no map_stats row in this root: the west edge is passed by'})
# ---------------------------------------------------------------- the Firestone road east: X7 (D-40) and back
X7_ROW = 'xeen_x7.odm' in open(os.path.join(ROOT, 'worlds/xeen/data_tables/map_stats.txt'), encoding='latin-1').read()
if X7_ROW:
    go(104, 66, 'The Firestone road east to the edge: X7 Mount Firestone (5 days)')
    add({'walk_to': {'x': W(111.5, 66)[0], 'y': W(111.5, 66)[1], 'z': ground(*W(108, 66)), 'z_tolerance': 3000,
                     'radius': 128, 'timeout_seconds': 60, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_x7.odm'}})
    add(assert_span('xeen_x4.odm', 'xeen_x7.odm'))
    add({'note': "On X7's west road; back west over X7's west edge to X4's entrance:east_road"})
    add({'walk_to': {'x': -23552, 'y': -1024, 'z': 1408, 'z_tolerance': 3000, 'radius': 128, 'timeout_seconds': 60,
                     'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add(assert_span('xeen_x7.odm', 'xeen_x4.odm'))
# ---------------------------------------------------------------- Burlock: the square, the services, the castle gate
go(61, 57.6, "Castle Burlock's village square")
event('evt:thing:burlock_mirror', "Burlock's mirror (Xeen.useMirror 4157)")
event('evt:thing:well_might', 'The Well of Might (+10 Might, temporary)', dialog=False)
event('evt:thing:herald_board', "The herald's board")
for bid in ('building:burlock_temple', 'building:burlock_tavern', 'building:burlock_weapons',
            'building:burlock_armour', 'building:burlock_training', 'building:burlock_stables'):
    house(bid)
walkc(62, 54.0, 'Up the castle lane to the gate', timeout=60)
walk(*W(62, 50.9), timeout=60, z=1750)
enter('evt:thing:castle_gate', 'xeen_xd07.blv', (0, 384), 0,
      "XD-07: through the castle gate into the gatehouse, before the Crusaders' portcullis")
# ---------------------------------------------------------------- the lists, the falls
go(68.0, 72.6, "The jousting lists: the Master of the Lists' challenge")
event('evt:thing:lists_challenge', 'Refused under Might 30')
go(74.6, 49.0, 'The Olympian Fountain on its ledge by the falls')
event('evt:thing:olympian_fountain', '+2 Might, once', dialog=False)
mv('olympian_drunk', 1)
event('evt:thing:olympian_fountain', 'Again: only cold water', dialog=False)
# ---------------------------------------------------------------- north-west: Carlawna, the eyrie (sealed)
go(41.4, 54.6, "Carlawna's hut")
house('building:carlawna_hut')
go(46.0, 43.4, 'The eyrie path')
enter('evt:thing:xd26_eyrie', 'xeen_xd26.blv', (1344, -1000), 0, "XD-26: into the Gargoyle Eyrie's cave mouth")
# ---------------------------------------------------------------- the south: the renegades' camp
go(57.0, 99.5, "The renegade knights' camp")
add({'clear_hostiles': {'radius': 3000}})
event('evt:thing:knight_tent_1', "The renegades' pavilions burn (+1,500)")
mv('knights_camp_burnt', 1)
# ---------------------------------------------------------------- the east: the ogres, XD-02's adit, Falagar, Joe
go(104.0, 89.5, "The ogres' camp in the red hills")
add({'clear_hostiles': {'radius': 3000}})
event('evt:thing:ogre_camp', "The ogres' fire (+1,500)")
mv('ogre_camp_burnt', 1)
ap, an = dark_face('thing:xd02_adit')
astand = (round(ap[0] + an[0] * 300), round(ap[1] + an[1] * 300))
walkc(101.5, 95.5, "XD-02's west adit", timeout=90)
walk(*astand, timeout=60)
face(astand[0], astand[1], math.atan2(-an[1], -an[0]), z=max(ground(*astand), ap[2]))
add({'press_interact': {'expect': {'kind': 'event_target'}}})
add({'advance_runtime': {'seconds': 0.5}})
add({'assert': {'dialog': {'active': True}}})
add({'press_action': {'action': 'cancel_dialog'}})
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 110020, 'value': True}})
add({'note': "With the winch worked inside XD-02 (qbit 110020) the adit is open"})
if 'xd02' in HAVE:
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    window()
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_xd02.blv'}})
    add({'assert': {'party_position': {'x': 2720, 'y': 5184, 'radius': 400}}})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})
else:
    add({'note': 'XD-02 is not installed in this root: not entered'})
go(100.2, 63.6, "Falagar's hut on the lava shoulder")
house('building:falagar_hut')
go(88.0, 89.0, "Joe's wagon")
npc(4320, (88.2, 88.4), 'Joe the Merchant at his wagon')
# ---------------------------------------------------------------- the south edge to X2
go(96, 104, 'The Rivercity road south to the edge east of x 0: the travel prompt (X2), accepted')
if TRAVEL_X2:
    add({'walk_to': {'x': W(96, 111)[0], 'y': W(96, 111)[1], 'z': ground(*W(96, 111)), 'z_tolerance': 600,
                     'radius': 128, 'timeout_seconds': 60, 'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_x2.odm'}})
else:
    add({'note': "X4's travel row is not in this root: the edge is passed by"})

doc = {'id': 'xeen.x4.walk', 'title': 'X4 Burlock Savannah: both towns, the pedestals, the camps and every way out',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/x4/tools/gen_walk.py from the built map (A5, 2026-11-20): Asp\'s square and\n'
            '# the pedestals, Asp\'s services, the edge to X3, the druid, the barbarian camp, Burlock\'s square and\n'
            '# services, the castle gate, the lists, the fountain, Carlawna, the eyrie, the renegades, the ogres,\n'
            '# XD-02\'s adit, Falagar, Joe and the south edge to X2.\n')
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'houses in the root', len(HOUSES & {b.get('house') for b in build['buildings']}),
      'have', sorted(HAVE), 'x3', X3_ROW, 'travel x2', TRAVEL_X2)
