#!/usr/bin/env python3
"""Writes X2's playtest.yml (the walk) from the built map: house doors from build.json, the doorways' and the cave
mouth's dark faces and ground heights from the map's export, event numbers from ids.lock.yml.
Run after a build: gen_walk.py <project> <build folder> [dungeons...]  (the dungeons the play mount holds are entered;
for the others the walk checks that the door's event runs and goes on)."""
import json
import math
import os
import subprocess
import sys
import yaml

P, B = sys.argv[1], sys.argv[2]
HAVE = set(sys.argv[3:])            # xd21 xd27 xd06 xd12: dungeons the play mount holds
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from gen import IN_WORLD as WORLD, XEEN_ITEMS   # noqa: E402  (the world switch, A5 2026-11-20)
_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../../assets_dev')
if WORLD:
    # the dungeons installed in the world, and the X1-X2 travel row (A2's driver writes it once both maps are in)
    HAVE = {k for k in ('xd21', 'xd27', 'xd06', 'xd12')
            if os.path.exists(os.path.join(_ROOT, 'worlds/xeen/maps/xeen_%s.blv' % k))}
    _tr = os.path.join(_ROOT, 'worlds/xeen/data_tables/outdoor_travels.txt')
    TRAVEL_X1 = os.path.exists(_tr) and any(l.startswith('xeen_x2.odm\t') for l in open(_tr))
else:
    TRAVEL_X1 = True
SKELETON_KEY = XEEN_ITEMS['skeleton_key'] if WORLD else 1461
M = 'xeen_x2.odm'
build = json.load(open(os.path.join(B, 'build.json')))
exp_path = os.path.join(B, 'export.json')
subprocess.run(['openyamm-studio/build-xeen/oymap', 'export', os.path.join(B, M), '--out', exp_path], check=True,
               stdout=subprocess.DEVNULL)
_m = json.load(open(exp_path))['map']
hm = _m['terrain']['height_map']
bmodels = {b['name']: b for b in _m['bmodels']}
ids = yaml.safe_load(open(os.path.join(P, 'ids.lock.yml')))
ev = {}
for k, v in ids.items():
    if isinstance(v, dict):
        ev.update(v)

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

# D-189 (2026-11-26): a built doorway shows its kit's door picture; a cave mouth's way in stays 7solid01
DOOR_FACES = ('7solid01', 'xvdoor', 'xvsdoor', 'xvtdoor')


def dark_face(name, tex=DOOR_FACES):
    b = bmodels[name]
    for f in b['faces']:
        if f['texture'] in tex and f.get('cog_triggered') and abs(f['plane_normal'][2]) < 6554:
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
                     'timeout_seconds': timeout, 'clear_hostiles': 3000}})

def walkc(x, y, note=None, timeout=120, z=None):
    walk(*W(x, y), note=note, timeout=timeout, z=z)

def face(X, Y, yaw, pitch=0.0, z=None):
    add({'set_pose': {'map': M, 'x': X, 'y': Y, 'z': z if z is not None else ground(X, Y), 'yaw': round(yaw, 4),
                      'pitch': pitch}})
    add({'advance_runtime': {'seconds': 0.5}})

def house(bid, house_id=None, via=(), npc=False):
    b = doors[bid]
    if house_id is None or WORLD:
        house_id = b['house']
    dx, dy, dz = b['door']
    nx, ny = b['normal']
    sx, sy = round(dx + nx * 300), round(dy + ny * 300)
    for v in via:
        walkc(*v, timeout=90)
    walk(sx, sy, '%s (%s): walk to its door and open it' % (b['title'], bid))
    face(sx, sy, math.atan2(-ny, -nx), z=max(ground(sx, sy), dz))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    if npc:
        # a residence of one person opens that person's talk at once (MM7's rule), not the house screen
        add({'assert': {'dialog': {'active': True}}})
    else:
        # F1 (merge point 40): a house whose proprietor is its only resident opens straight on his talk
        add({'assert': {'dialog': {'active': True}}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})

def message_door(bid, note):
    """A building door whose event shows a message (the wild huts, a locked dungeon door)."""
    b = doors[bid]
    dx, dy, dz = b['door']
    nx, ny = b['normal']
    sx, sy = round(dx + nx * 300), round(dy + ny * 300)
    walk(sx, sy, note)
    face(sx, sy, math.atan2(-ny, -nx), z=max(ground(sx, sy), dz))
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True}}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})
    return sx, sy

def event(eid, note, dialog=True, check=None):
    add({'note': note})
    add({'execute_event': {'id': ev[eid]}})
    add({'advance_runtime': {'seconds': 0.5}})
    if dialog:   # F13 (A5 s29): a touch's text is a status line, a note or a choice's answer a window: either
        add({'play_lua': {'source': "local s = status(); local w = close(); wait(0.3); "
                                    "if s == '' and not w then error('no text shown') end"}})
    if check:
        add({'play_lua': {'source': check}})

def into(stand, yaw, target, note, z=None, have=True, at=None):
    """Click a way in from where the party stands; with the dungeon in the play mount, check the map and come back."""
    X, Y = stand
    if WORLD and not have:
        add({'note': '%s is not installed in the world yet: the walk waits for it here' % target})
        return
    face(X, Y, yaw, z=z)
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    # F16 (A5 s29): the standard entrance window (its trans.txt line), OK
    add({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
    add({'select_topic': {'match_label': 'OK'}})
    if have:
        add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
        add({'assert': {'map': target}})
        if at:
            add({'assert': {'party_position': {'x': at[0], 'y': at[1], 'radius': 256}}})
        add({'load_map': {'map': M}})
        add({'advance_runtime': {'seconds': 0.5}})
        add({'note': 'Back on X2 where the party stood (by load_map)'})
        face(X, Y, yaw + math.pi, z=z)
    else:
        add({'note': '%s is not in the play mount: the door\'s event ran; not entered' % target})
        add({'advance_runtime': {'seconds': 0.5}})
        add({'load_map': {'map': M}})
        add({'advance_runtime': {'seconds': 0.5}})
        face(X, Y, yaw + math.pi, z=z)

def out_front(face_pos, normal, d):
    return (round(face_pos[0] + normal[0] * d), round(face_pos[1] + normal[1] * d))

s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'assert': {'party_position': {'x': s['x'], 'y': s['y'], 'radius': 128}}})
# ---------------------------------------------------------------- Bridge Square
# 2026-11-16: the compact town (gen.py): the square at the bridge's north head, the shops round it and along the main
# street (y 43.5, jogging a cell north west of x 58 and east of x 73), the guilds and the skill row on the south bank's
# riverside row with their doors on the south street (y 61).
event('evt:thing:mirror', 'The town mirror on Bridge Square: its two tips')
event('evt:thing:town_fountain', 'The fountain: stopped until Barok has his pendant', dialog=False)
event('evt:thing:ad_deep_mine', 'The ads on Bridge Square')
if WORLD:
    event('evt:thing:ad_navigation', "The School of Navigation's sign (x2.ad_navigation)")
    event('evt:thing:ad_mountains', "The sign by Martin's door (x2.ad_mountains)")
# ---------------------------------------------------------------- the north bank's shops
house('building:alchemist', 118, via=[(62.8, 44.4)])
house('building:bank', 287, via=[(62.8, 44.4), (63, 43.5)])
house('building:magic_shop', 86, via=[(60.5, 43.5)])
house('building:training', 1572, via=[(58.4, 43.5), (58, 42.5), (56, 42.5)])
walkc(58, 42.5, 'East along the main street', timeout=60)
walkc(58.4, 43.5, timeout=60)
house('building:tavern', 241, via=[(64, 43.5)])
event('evt:thing:patron_1', "The drunk on the cask outside Bull's Tavern", dialog=False)
house('building:armour_shop', 49, via=[(67.5, 43.5)])
house('building:weapon_shop', 10, via=[(72.6, 43.5), (73, 42.5)])
walkc(73, 42.5, 'Back west to the square and up the north road to the stables', timeout=60)
walkc(72.6, 43.5, timeout=60)
walkc(64, 43.5, timeout=90)
walkc(64, 41.5, timeout=60)
house('building:stables', 462, via=[(64, 39.5)])
walkc(64, 41.5, 'Back down the north road to the square', timeout=60)
walkc(64, 43.5, timeout=60)
walkc(62.6, 44.4, timeout=60)
walkc(62.6, 47.4, timeout=60)
# ---------------------------------------------------------------- over the great bridge
walkc(64, 48, 'Over the great bridge to the South Square', timeout=60)
walkc(64, 49.5, timeout=60, z=1024)
walkc(64, 53, timeout=60, z=1024)
walkc(64, 57.0, timeout=60, z=1024)
walkc(64, 59.5, timeout=60)
house('building:guild_spirit', 153, via=[(63.5, 61), (61, 61)])
house('building:guild_mind', 159, via=[(58, 61)])
house('building:guild_body', 165, via=[(55.5, 61)])
walkc(58, 61, 'Back to the South Square and east along the south street', timeout=60)
walkc(64, 61, timeout=60)
house('building:temple', 312, via=[(64, 62)])
walkc(64.2, 61.2, timeout=60)
walkc(67.5, 61, timeout=60)
house('building:skill_gym', 945, via=[(68.5, 61.1)], npc=True)
house('building:skill_martial', 923, npc=True)
house('building:skill_temps', 929, npc=True)
# ---------------------------------------------------------------- the south quay: the dock and the Robbers' Den
walkc(75, 61.0, 'Past the skill row to the promenade and down the quay steps to the south quay', timeout=60)
walkc(75, 58.2, timeout=60)
walkc(73, 58.2, timeout=60)
walkc(73, 55.6, timeout=60)
b = doors['thing:boat_house']
house('thing:boat_house', 486, via=[(75.5, 55.6)])
fp, fn = dark_face('thing:den_door')
den_stand = out_front(fp, fn, 260)
walkc(75.5, 55.6, "West along the quay toward the bridge's south end", timeout=60)
if WORLD:
    # A5 (2026-11-20, third session): the sorceresses' house (A4's 4098, two residents: the house screen) and Q-C2's
    # strongbox against its east wall: it gives Barok's pendant (12152, D-9.4) and brings out the two hidden apprentices
    # (11184, group 54), hostile; the walk's clear_hostiles deals with them
    house('building:quay_houses#5', via=[(72.2, 55.5)])
    walkc(71.9, 55.6, "Q-C2: the sorceresses' strongbox", timeout=60)
    add({'assert': {'actor_count': {'monster_id': 11184, 'hostile': True, 'min': 2, 'max': 2}}})
    add({'play_lua': {'source': 'click(%d); wait(1.0); take_chest(); wait(0.3); close(); wait(0.5); close(); wait(0.5)\n'
                                'if not (has_item(12152) or held() == 12152) then error("no pendant") end'
                                % ev['evt:thing:sorceress_strongbox'], 'max_seconds': 10}})
    add({'assert': {'actor_count': {'monster_id': 11184, 'hostile': True, 'min': 2,
                                    'near': [3900, 4100, 1200]}}})
    add({'note': 'The apprentices are out (shown by the strongbox); the next walk clears them'})
walkc(70, 55.5, timeout=60)
walkc(67.4, 55.5, timeout=60)
walk(*den_stand, "XD-21: the Robbers' Den's door in the quay wall", timeout=60)
into(den_stand, math.atan2(-fn[1], -fn[0]), 'xeen_xd21.blv', 'In', z=ground(*den_stand), have='xd21' in HAVE,
     at=(-2560, 320))
walkc(67.4, 55.5, 'Back east along the quay and up the steps', timeout=60)
walkc(70, 55.5, timeout=60)
walkc(73, 55.6, timeout=60)
walkc(73, 58.2, timeout=60)
walkc(75, 58.2, timeout=60)
walkc(75, 61.0, timeout=60)
walkc(64, 61, timeout=90)
# ---------------------------------------------------------------- west: the lake shore, Medin, the island
walkc(58, 61, 'West along the south street to the lake path', timeout=60)
walkc(54.5, 61, timeout=60)
walkc(52, 61, timeout=90)
message_door('building:medin_hut', "Medin's hut: the lake beasts (Q-C13)")
walkc(49, 61, timeout=60)
walkc(47.6, 61.0, timeout=60)
walkc(46.2, 60.5, "Out on Medin's jetty", timeout=60, z=672)
event('evt:thing:medin_boat', "Medin's boat: not while the beasts live")
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 110201, 'value': True}})
event('evt:thing:medin_boat', "With the beasts dead (qbit 110201) Medin rows the party to the island", dialog=False)
add({'advance_runtime': {'seconds': 1.0}})
add({'assert': {'map': M}})
tdx, tdy, tdz = doors['thing:darzog_tower']['door']
tstand = (round(tdx + 300), tdy)
walk(*tstand, "Darzog's Tower: the door on the east side", timeout=90)
face(tstand[0], tstand[1], math.pi, z=tdz)
add({'press_interact': {'expect': {'kind': 'event_target'}}})
add({'advance_runtime': {'seconds': 0.5}})
add({'assert': {'dialog': {'active': True}}})
add({'press_action': {'action': 'cancel_dialog'}})
add({'grant_item': {'item_id': SKELETON_KEY}})
add({'play_lua': {'source': 'if not has_item(%d) then error("no Skeleton Key") end' % SKELETON_KEY}})
add({'note': 'With the Skeleton Key the door opens'})
add({'advance_runtime': {'seconds': 0.3}})
into(tstand, math.pi, 'xeen_xd12.blv', 'In', z=tdz, have='xd12' in HAVE, at=(2752, 0))
walkc(38.4, 60.6, 'The island jetty: Medin rows the party back', timeout=90, z=672)
event('evt:thing:island_boat', 'Back to the jetty', dialog=False)
add({'advance_runtime': {'seconds': 1.0}})
walkc(48.5, 61.5, timeout=60)
# ---------------------------------------------------------------- north-west: the west road, the ogres, the edge
walkc(52, 61, 'Back to town, over the bridge and out along the west road', timeout=90)
walkc(54.5, 61, timeout=60)
walkc(64, 61, timeout=60)
walkc(64, 59.5, timeout=60)
walkc(64, 57.0, timeout=60, z=1024)
walkc(64, 49.5, timeout=60, z=1024)
walkc(64, 48, timeout=60)
walkc(62.6, 47.4, timeout=60)
walkc(62.6, 44.4, timeout=60)
walkc(64, 43.5, timeout=60)
walkc(58.4, 43.5, timeout=60)
walkc(58, 42.5, timeout=60)
walkc(51, 42.5, timeout=60)
message_door('building:barok_hut', "Barok's hut by the west road (Q-C2)")
walkc(49, 42.5, timeout=60)
walkc(46, 41, timeout=60)
walkc(37, 41, timeout=90)
walkc(36, 40, timeout=60)
walkc(33.5, 40, "Over the ogres' bridge", timeout=60, z=None)
walkc(31, 40, timeout=60)
walkc(28, 37, 'Up the lair path', timeout=90)
walkc(25, 34, timeout=90)
lp, ln = dark_face('thing:ogre_lair')
lair_stand = out_front(lp, ln, 280)
walk(*lair_stand, 'XD-27: the Ogre Lair', timeout=90)
into(lair_stand, math.atan2(-ln[1], -ln[0]), 'xeen_xd27.blv', 'In', z=max(ground(*lair_stand), lp[2]),
     have='xd27' in HAVE)
walkc(25, 34, timeout=60)
walkc(28, 37, timeout=60)
walkc(31, 40, timeout=60)
if WORLD:
    # A5 (fifth session): X3 installed: the west edge leads to X3's east start (21504, 12288), declined then accepted
    walkc(24, 40, 'West along the road to the west edge: the travel prompt (X3 Lifeforce Lagoon)', timeout=90)
    add({'walk_to': {'x': W(17, 40)[0], 'y': W(17, 40)[1], 'z': ground(*W(17, 40)), 'z_tolerance': 600,
                     'radius': 128, 'timeout_seconds': 60, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_x3.odm'}})
    add({'assert': {'party_position': {'x': 21504, 'y': 12288, 'radius': 700}}})
    add({'note': "Back east along X3's east road to its edge: the prompt names Rivercity; accepted, the party arrives "
                 "on X2's west start"})
    add({'walk_to': {'x': 24576, 'y': 12288, 'z': 1024, 'z_tolerance': 900, 'radius': 128, 'timeout_seconds': 60,
                     'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': W(21, 40)[0], 'y': W(21, 40)[1], 'radius': 700}}})
    # and the north edge: up the north road past the stables to X4's south start (16384, -22016)
    add({'note': 'To the stables by teleport, then up the north road to the north edge: the travel prompt (X4)'})
    face(*W(64, 38), math.pi / 2)
    walkc(64, 36.5, timeout=60)
    walkc(66, 34.5, timeout=60)
    walkc(66, 28, timeout=90)
    walkc(66, 22, timeout=90)
    add({'walk_to': {'x': W(66, 17)[0], 'y': W(66, 17)[1], 'z': ground(*W(66, 17)), 'z_tolerance': 600,
                     'radius': 128, 'timeout_seconds': 60, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_x4.odm'}})
    add({'assert': {'party_position': {'x': 16384, 'y': -22016, 'radius': 900}}})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})
else:
  walkc(24, 40, 'West along the road to the west edge: the travel prompt (X3, Erathia as the stand-in), declined',
        timeout=90)
  add({'walk_to': {'x': W(18, 40)[0], 'y': W(18, 40)[1], 'z': ground(*W(18, 40)), 'z_tolerance': 600, 'radius': 128,
                   'timeout_seconds': 60, 'expect': 'dialog'}})
  add({'assert': {'dialog': {'active': True}}})
  add({'press_action': {'action': 'cancel_dialog'}})
  add({'assert': {'map': M}})
# ---------------------------------------------------------------- south: the woods, Danulf, the Temple of Yak
add({'note': 'Back to the South Square by teleport (the walk has crossed the town twice already)'})
face(*W(64, 61.4), math.pi / 2 * 3)
walkc(64, 62.4, 'Down the south road into the fairy woods', timeout=90)
walkc(63, 63.5, timeout=60)
walkc(63, 67.5, timeout=60)
walkc(62, 67.5, timeout=60)
walkc(62, 72, timeout=60)
walkc(63, 73, timeout=60)
walkc(61, 77, timeout=90)
walkc(58, 80, timeout=90)
if WORLD:
    # Danulf (A4's NPC 4154) by his altar: his talk
    add({'note': "Danulf the Faery King at his ring of stones: his talk (Q-C17)"})
    _scene = yaml.safe_load(open(os.path.join(B, 'xeen_x2.scene.yml')))
    _danulf = [x['actor_index'] for x in _scene['initial_state']['actors'] if x.get('npc_id') == 4154][0]
    walkc(57.6, 81.4, timeout=60)
    add({'interact_actor': {'actor_index': _danulf}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True}}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})
else:
    event('evt:thing:danulf_ring', "Danulf the Faery King's ring of stones: his errand (Q-C17)")
walkc(58, 86, timeout=90)
walkc(61, 90, timeout=90)
walkc(62, 95, timeout=90)
yx, yy, yz = doors['thing:yak_temple']['door']
ystand = (yx, yy + 300)
walk(*ystand, 'XD-06: the Temple of Yak, open without the Yak Stone (D-89)', timeout=90)
into(ystand, -math.pi / 2, 'xeen_xd06.blv', 'In', z=max(ground(*ystand), yz), have='xd06' in HAVE, at=(0, 384))
# ---------------------------------------------------------------- east: the river road to Vertigo
if not TRAVEL_X1:
    steps.append({'note': "The east edge's travel to X1 waits for A2's travel row (both maps installed)"})
_east_start = len(steps)
add({'note': 'Back to the east entry by teleport, then the river road to the east edge: the travel prompt (X1), declined'})
face(*W(84, 45.5), 0.0)
walkc(85, 45.5, timeout=60)
walkc(88, 46, timeout=60)
walkc(104, 46, timeout=180)
add({'walk_to': {'x': W(111, 46)[0], 'y': W(111, 46)[1], 'z': ground(*W(111, 46)), 'z_tolerance': 600,
                 'radius': 128, 'timeout_seconds': 60, 'expect': 'dialog'}})
add({'assert': {'dialog': {'active': True}}})
add({'note': 'Accepted: on to X1 by the river road, arriving at its west start'})
add({'select_topic': {'match_label': 'OK'}})
add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
add({'assert': {'map': 'xeen_x1.odm'}})
add({'assert': {'party_position': {'x': -22016, 'y': 9216, 'radius': 700}}})
add({'note': "Mayor Gunther's errand window opens on a first visit to X1 (its one-shot timer): closed"})
add({'advance_runtime': {'seconds': 3.0}})
add({'assert': {'dialog': {'active': True}}})
add({'press_action': {'action': 'cancel_dialog'}})
add({'advance_runtime': {'seconds': 0.3}})
add({'note': "Back west along X1's west road to its edge: the prompt names Rivercity; accepted, the party arrives on X2's east edge"})
# Hostility pass (2026-11-16): X1's slot monsters no longer fight each other, so the ones at the west road's end
# stand in the party's way: cleared as X1's own walk clears them.
add({'walk_to': {'x': -24576, 'y': 9216, 'z': 640, 'z_tolerance': 900, 'radius': 128, 'timeout_seconds': 60,
                 'clear_hostiles': 3000, 'expect': 'dialog'}})
add({'assert': {'dialog': {'active': True}}})
add({'select_topic': {'match_label': 'OK'}})
add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
add({'assert': {'map': M}})
add({'assert': {'party_position': {'x': W(106, 46)[0], 'y': W(106, 46)[1], 'radius': 700}}})
if not TRAVEL_X1:
    del steps[_east_start:]
# ---------------------------------------------------------------- Nystor's boat ride to Vertigo
_nystor = len(steps)
add({'note': "Captain Nystor's pier: 100 gold for a ride down the river to Vertigo (X1)"})
add({'play_lua': {'source': 'if gold() < 100 then error("the party has under 100 gold for the ride") end'}})
face(*W(80.2, 53.6), 0.0, z=672)
add({'execute_event': {'id': ev['evt:thing:nystor_post']}})
add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
add({'assert': {'map': 'xeen_x1.odm'}})
if WORLD:
    # the dock house (A4's 4063, visited above) sells the rides; the post only quotes Nystor
    del steps[_nystor:]

doc = {'id': 'xeen.x2.walk', 'title': 'X2 Rivercity and Lake Darzog: the town, the bridge and every dungeon door',
       'world': 'xeen' if WORLD else 'mm7', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/x2/tools/gen_walk.py from the built map. A new game on Bridge Square:\n'
            '# the mirror, the fountain and the ads; the shops round the square and along the main street, the tavern,\n'
            '# the stables; over the great bridge to the guilds, the temple and the skill row; the dock and the\n'
            '# Robbers\' Den on the south quay;\n'
            '# Medin and his boat to the island and Darzog\'s door; Barok, the ogres\' bridge and the Ogre Lair; the\n'
            '# west edge; the fairy woods, Danulf and the Temple of Yak; the east edge; Nystor\'s ride to Vertigo.\n')
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps))
