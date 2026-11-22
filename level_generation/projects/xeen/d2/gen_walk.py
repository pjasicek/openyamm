#!/usr/bin/env python3
"""Writes D2's playtest.yml (adapted from X5's gen_walk.py) (the walk) from the built map: house doors from build.json, the dark faces of the ways in
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
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import math
import os
import subprocess
import sys
import yaml

P, B = sys.argv[1], sys.argv[2]
ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..')
WORLD = os.path.join(ROOT, 'assets_dev/worlds/xeen')
M = 'xeen_d2.odm'
_STATS = open(os.path.join(WORLD, 'data_tables/map_stats.txt')).read()
# as gen.py: a door opens when its BLV is installed and A2's map_stats row names it
HAVE = {k for k in ('dd06', 'dd09', 'dd10b', 'dd11a', 'dd11b', 'dd11c', 'dd13')
        if os.path.exists(os.path.join(WORLD, 'maps/xeen_%s.blv' % k)) and '\txeen_%s.blv\t' % k in _STATS}
HOUSES_LIVE = any(l.startswith('4551\t') for l in open(os.path.join(WORLD, 'data_tables/house_data.txt')))
D1_LIVE = os.path.exists(os.path.join(WORLD, 'maps/xeen_d1.odm'))
D3_LIVE = os.path.exists(os.path.join(WORLD, 'maps/xeen_d3.odm'))
D3_TRAVEL = any(l.startswith('xeen_d2.odm\t') and 'xeen_d3.odm' in l
                for l in open(os.path.join(WORLD, 'data_tables/outdoor_travels.txt')))
def exit_of(key, near=None):
    """A dungeon's way back out onto D2: (its event number, the arrival x, y, z on D2), from its installed Lua; with
    `near` (x, y) the exit landing nearest it (DD-13 has one per gate)."""
    path = os.path.join(WORLD, 'events/maps/xeen_%s.lua' % key)
    if not os.path.exists(path):
        return None
    prev = None
    found = []
    for l_ in open(path):
        if l_.startswith('RegisterEvent('):
            prev = int(l_.split('(')[1].split(',')[0])
        if 'MoveToMap' in l_ and 'xeen_d2.odm' in l_:
            a = [int(v) for v in l_.split('(')[1].split(',')[:3]]
            found.append((prev, a[0], a[1], a[2]))
    if not found:
        return None
    if near is None:
        return found[0]
    return min(found, key=lambda e: math.hypot(e[1] - near[0], e[2] - near[1]))

# DD-06's front door (its own event) back out onto D2's entrance:dd06_door (15872, -7680)
DD06_EXIT = (exit_of('dd06') or (None,))[0]
# the west edge travels once A2's generator has written D2's row (outdoor_travels.txt) with D1 on it
TRAVEL_LIVE = any(l.startswith('xeen_d2.odm\t') and 'xeen_d1.odm' in l
                  for l in open(os.path.join(WORLD, 'data_tables/outdoor_travels.txt')))
TOWN = yaml.safe_load(open(os.path.join(WORLD, 'source/towns/d2.yml')))
CLOSED = {}
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
scene = yaml.load(open(os.path.join(B, 'xeen_d2.scene.yml')), Loader=yaml.CSafeLoader)
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
SKETCH = yaml.load(open(os.path.join(P, 'sketch.yml')), Loader=yaml.CSafeLoader)
VILLAGE_FLOOR = 980
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

sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a6/s32')
import hookwin    # s32: D-90 made most hooks status lines; such an event opens no window


def event(eid, note, dialog=True, check=None):
    add({'note': note})
    add({'execute_event': {'id': ev[eid]}})
    add({'advance_runtime': {'seconds': 0.5}})
    if dialog and hookwin.status_only(os.path.join(B, 'xeen_d2.lua'), ev[eid], passes=not any(
            w in note.lower() for w in ('refus', 'without', 'no pass', 'not yet', 'sealed', 'before '))):
        dialog = False
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

def out_again(key, note, near=None):
    """In a dungeon of D2: its exit event (the leave window, OK) back onto D2 at its return point."""
    ex = exit_of(key, near)
    add({'note': note + ' (its event %s), back on D2 at (%d, %d, %d)' % ex})
    add({'clear_hostiles': {'radius': 3000}})
    add({'execute_event': {'id': ex[0]}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': ex[1], 'y': ex[2], 'radius': 200, 'z_min': ex[3] - 40,
                                       'z_max': ex[3] + 120}}})

def dive(key, eid, inside, note, out_note, near):
    """A live way in run by its event (the hook, if any, passes), the dungeon at `inside`, then out again."""
    add({'note': note})
    add({'execute_event': {'id': ev[eid]}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: entrance window
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_%s.blv' % key}})
    add({'assert': {'party_position': {'x': inside[0], 'y': inside[1], 'radius': 200}}})
    out_again(key, out_note, near)

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
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: entrance window
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': target}})
    add({'load_map': {'map': M}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'note': 'Back on X5 where the party stood (by load_map)'})
    face(X, Y, yaw + math.pi, z=max(ground(X, Y), fp[2]))

s = build['start']
add({'new_game_flow': {'start_map': M}})
add({'assert': {'map': M}})
add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
add({'assert': {'party_position': {'x': s['x'], 'y': s['y'], 'radius': 160}}})
add({'advance_runtime': {'seconds': 2}})
add({'note': "D-23 at load: the pass ogres hostile (A2's relations), Graalg's three and the village sprites peaceful"})
add({'assert': {'actor_count': {'monster_id': 11066, 'hostile': True, 'min': 10}}})
add({'assert': {'actor_count': {'monster_id': 11064, 'hostile': False, 'min': 1}}})
add({'assert': {'actor_count': {'monster_id': 11537, 'hostile': False, 'min': 5}}})
# ---------------------------------------------------------------- the forest's edge to the village
walkc(32, 60, 'East along the Castleview road to Forest Fork', timeout=150)
walkc(35, 64, 'The forest track', timeout=90)
walkc(38, 67, timeout=90)
walkc(42, 70, 'Bark Glade', timeout=90)
for _bid in ('building:nibbler_hollow',):
    house(_bid, "Nibbler's Hollow (4556)", opened=True)
add({'note': "The great tree's door: refused without the bark key (q-d9.bark_door)"})
gx, gy, gz = doors['thing:great_tree']['door']
gnx, gny = doors['thing:great_tree']['normal']
walk(round(gx + gnx * 300), round(gy + gny * 300), timeout=90)
face(round(gx + gnx * 300), round(gy + gny * 300), math.atan2(-gny, -gnx), z=max(ground(gx, gy), gz))
add({'press_interact': {'expect': {'kind': 'event_target'}}})
add({'advance_runtime': {'seconds': 0.5}})
add({'assert': {'dialog': {'active': True, 'text_contains': 'A door in the trunk of the great tree'}}})
add({'press_action': {'action': 'cancel_dialog'}})
add({'advance_runtime': {'seconds': 0.3}})
add({'grant_item': {'item_id': 12342}})
add({'note': 'With the bark key the door asks to enter (and is sealed until DD-09 is installed)'})
if 'dd09' in HAVE:
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: entrance window
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd09.blv'}})
    add({'assert': {'party_position': {'x': 0, 'y': -1920, 'radius': 200}}})
    out_again('dd09', "DD-09's trunk door")
else:
    add({'press_interact': {'expect': {'kind': 'event_target'}}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True}}})
    add({'press_action': {'action': 'cancel_dialog'}})
    add({'advance_runtime': {'seconds': 0.3}})
walkc(39, 72, 'The village lane', timeout=90)
walkc(36, 75, timeout=90)
walkc(33.5, 79, timeout=90)
walkc(31.5, 83, timeout=90)
walkc(29.5, 88, 'The village green', timeout=90)
for _bid in ('building:sprite_potions', 'building:sprite_guild_light', 'building:sharla_tree',
             'building:sprite_houses#1', 'building:sprite_houses#2'):
    house(_bid, opened=True)
if not HOUSES_LIVE:
    add({'note': "A4's house rows 4551-4556 are not in house_data.txt yet: the village's doors are not opened"})
# Sharla's stair to her deck and the chest (q-d10.treehouse fail_text while the sprites live)
st = [s_ for s_ in SKETCH['structures'] if s_['id'] == 'thing:sharla_stair'][0]
# A6's review: the stair is an open walkway winding round the trunk ([x, y, z] points: foot, arc with a landing,
# the stub onto the deck); the walk lines up on its foot, then walks every point
line = st['line']
# the stair's head (its stub in onto the deck) is a walkway of its own, without piers
line = line + [s_ for s_ in SKETCH['structures'] if s_['id'] == 'thing:sharla_stair_head'][0]['line'][1:]
(fx, fy, fz), (nx_, ny_, _nz) = line[0], line[1]
dl = math.hypot(nx_ - fx, ny_ - fy)
bx, by = (fx - nx_) / dl, (fy - ny_) / dl
walkc(fx + bx * 1.2, fy + by * 1.2, "Sharla's stair (the only way up, D-23)", timeout=90)
_X, _Y = W(fx + bx * 0.5, fy + by * 0.5)
add({'walk_to': {'x': _X, 'y': _Y, 'z': fz, 'z_tolerance': 200, 'radius': 48, 'timeout_seconds': 30}})
face(_X, _Y, math.atan2(-(ny_ - fy), nx_ - fx), z=fz)
for (px_, py_, pz_) in line[1:]:
    X_, Y_ = W(px_, py_)
    add({'walk_to': {'x': X_, 'y': Y_, 'z': pz_, 'z_tolerance': 140, 'radius': 96, 'timeout_seconds': 40}})
tx, ty, tz = line[-1]
add({'assert': {'party_position': {'x': W(tx, ty)[0], 'y': W(tx, ty)[1], 'radius': 400, 'z_min': tz - 66}}})
event('evt:thing:treehouse_chest', "The chest on Sharla's deck: a sprite sits on it (q-d10.treehouse)",
      dialog=False, check=None)   # s32: q-d10.treehouse refuses on the status line (failStatus)
# ---------------------------------------------------------------- the robbery: the village sprites turn and die
add({'note': "q-d10.robbery (113203): the village's sprites turn hostile; all dead sets sprites_slain (113208)"})
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 113203, 'value': True}})
add({'advance_runtime': {'seconds': 4}})
add({'assert': {'actor_count': {'monster_id': 11537, 'hostile': True, 'min': 3}}})
add({'play_lua': {'source': 'local n = clear_hostiles(6000); log("cleared " .. n)'}})
add({'advance_runtime': {'seconds': 7}})
add({'play_lua': {'source': 'if not qbit(113208) then error("sprites_slain (113208) not set") end'}})
event('evt:thing:treehouse_chest', 'The treehouse chest now: two Energy Disks (q-d10.treehouse)',
      dialog=False, check='if not has_item(12334) then error("no Energy Disk") end')   # s32: a status-line find (D-90)
# ---------------------------------------------------------------- the forest: the holes, the fruit, the brink
for key in ('dd11a', 'dd11b', 'dd11c'):
    p = [q for q in SKETCH['points'] if q['id'] == 'entrance:%s_hole' % key][0]['at']
    jump(p[0], p[1], 'Troll hole %s (q-d13.troll_holes)' % key[-1].upper(), yaw=0.0)
    add({'note': 'D-25 (a): the return spot of DD-11%s is clear ground' % key[-1].upper()})
    if key in HAVE:
        add({'note': "'Troll Hole. Descend?' then DD-11%s at A7's inside point, facing east" % key[-1].upper()})
        add({'execute_event': {'id': ev['evt:thing:%s_hole' % key]}})
        add({'advance_runtime': {'seconds': 0.5}})
        add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: entrance window
        add({'select_topic': {'match_label': 'OK'}})
        add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
        add({'assert': {'map': 'xeen_%s.blv' % key}})
        ins = {'dd11a': (96, -32), 'dd11b': (96, -32), 'dd11c': (128, -64)}[key]
        add({'assert': {'party_position': {'x': ins[0], 'y': ins[1], 'radius': 200}}})
        out_again(key, "DD-11%s's sod hatch" % key[-1].upper())
    else:
        event('evt:thing:%s_hole' % key, "'Troll Hole. Descend?' then the sealed line")
jump(57.5, 88.5, 'The Forbidden Fruit clearing', yaw=-math.pi / 2)
event('evt:thing:fruit_coconut', 'The coconut of confusion', dialog=False)
event('evt:thing:fruit_sign', 'The label on the basket')
walkc(59, 93, 'Down the brink path', timeout=120)
walkc(60, 97, timeout=120)
walkc(61, 101, timeout=120)
event('evt:thing:brink_bench', "The sprites' lookout over Sprite Falls")
jump(16, 89.5, 'The fairy ring', yaw=math.pi / 2)
event('evt:thing:fairy_ring', 'The fairy ring heals', dialog=False)
# ---------------------------------------------------------------- the foothills and the pass
jump(36, 53, 'The obelisk on its knoll', yaw=math.pi / 2)
event('evt:thing:obelisk', "The obelisk: A3's obelisks.d2 (BENEATH, dark_2)",
      check='if not qbit(115051) then error("dark_2 (115051) not set") end')
jump(34, 32, "The east adit's foot", yaw=math.pi / 2)
if 'dd10b' in HAVE:
    dive('dd10b', 'evt:thing:dd10b_adit', (0, 192), "The adit into DD-10B at A8's point (0, 192), facing north",
         "DD-10B's boarded mouth", (-15360, 16384))
else:
    event('evt:thing:dd10b_adit', 'The Gemstone Mines (DD-10B): sealed until installed')
jump(48, 29.5, 'The crystal seam', yaw=math.pi / 2)
event('evt:thing:crystal_seam', 'The crystal seam (Might 30)', dialog=False)
jump(61, 43, 'The caravan road below the west fort', yaw=0.3)
event('evt:thing:kramer_wagon', "Kramer's strongbox", dialog=False)
add({'press_action': {'action': 'cancel_dialog'}})
jump(72, 37, "The west fort's gate (DD-13)", yaw=math.pi / 2)
if 'dd13' in HAVE:
    dive('dd13', 'evt:thing:dd13_west', (0, -64), "The west fort's gate into DD-13's start (0, -64), facing north",
         "DD-13's west gateway", (4096, 13824))
else:
    event('evt:thing:dd13_west', "The west fort's gate: sealed until DD-13 is installed")
jump(77.5, 37.5, "Graalg's parley fire", yaw=0.6)
talk(5108, 'Graalg at the parley fire (Q-D11): peaceful, he talks', (78.4, 37.0))
jump(87, 41, "The east fort's gate (DD-13)", yaw=-math.pi / 2)
if 'dd13' in HAVE:
    dive('dd13', 'evt:thing:dd13_east', (7552, 32), "The east fort's gate into DD-13 at A7's point (7552, 32), south",
         "DD-13's east gateway", (11776, 11776))
else:
    event('evt:thing:dd13_east', "The east fort's gate: sealed")
# ---------------------------------------------------------------- the Southern Woods
jump(95, 78.5, "The Southern Tower's door (q-d19.tower_door)", yaw=-math.pi / 2)
event('evt:door:thing:southern_tower', "Refused without Thaddeus's key: 'NO THIEVES'")
add({'grant_item': {'item_id': 12339}})
if 'dd06' in HAVE:
    add({'note': "With the key: into DD-06 at A7's inside point (640, 1700, 0) facing south"})
    add({'execute_event': {'id': ev['evt:door:thing:southern_tower']}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})   # F16: entrance window
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_dd06.blv'}})
    add({'assert': {'party_position': {'x': 640, 'y': 1700, 'radius': 200}}})
    add({'note': "DD-06's front door (its event %s) back out onto D2's entrance:dd06_door (15872, -7680)" % DD06_EXIT})
    add({'execute_event': {'id': DD06_EXIT}})
    add({'assert': {'dialog': {'active': True, 'text_contains': 'Do you wish to leave'}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': 15872, 'y': -7680, 'radius': 200}}})
else:
    event('evt:door:thing:southern_tower', 'With the key: the tower (or its sealed line)')
jump(104, 91, 'The Shrine of the Elements', yaw=-math.pi / 2)
event('evt:thing:shrine_altar', 'The Shrine of the Elements: +5 to four resistances', dialog=False)
jump(100, 31.5, "The genie's ledge", yaw=math.pi / 2)
event('evt:thing:genie_lamp', "The genie's lamp", dialog=False)
# A6 s27: the second rub says the genie has gone (no silent click)
event('evt:thing:genie_lamp', "The genie's lamp again: cold", dialog=False,
      check="wait(0.2); local s = status(); if not string.find(s, 'Its genie has gone back in for good.', 1, true) "
            "then error('second rub: ' .. s) end")
jump(106, 41.5, 'The milestone on the Sandcaster road', yaw=math.pi / 2)
event('evt:thing:milestone', 'The milestone')
# ---------------------------------------------------------------- the war: a burned fort turns every ogre (D-12.3)
add({'note': 'q-d11.west_burned (113224) and hostile (113222), as DD-13 sets them: the west fort a ruin on load'})
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 113224, 'value': True}})
add({'setup_shortcut': {'kind': 'set_qbit', 'id': 113222, 'value': True}})
add({'load_map': {'map': M}})
add({'advance_runtime': {'seconds': 2}})
add({'assert': {'actor_count': {'monster_id': 11064, 'hostile': True, 'min': 1}}})
add({'assert': {'actor_count': {'monster_id': 11066, 'hostile': True, 'min': 10}}})
# ---------------------------------------------------------------- the edges
if not D1_LIVE:
    jump(4, 61, 'The road west: D1 not installed (sealed)', yaw=math.pi)
    event('evt:thing:west_road_end', "The road's end: D1 not built (sealed)")
elif not TRAVEL_LIVE:
    add({'note': "D1 is installed but A2's travel row D2-D1 is not written yet: the edge is not walked"})
else:
    jump(6, 60, 'West off the edge to D1', yaw=math.pi)
    add({'walk_to': {'x': W(1, 60)[0], 'y': W(1, 60)[1], 'z': ground(*W(1, 60)), 'z_tolerance': 600,
                     'radius': 128, 'timeout_seconds': 60, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_d1.odm'}})
if not D3_LIVE:
    jump(124, 44, 'The road east: D3 not installed (sealed)', yaw=0.0)
    event('evt:thing:east_road_end', "The road's end: D3 not built (sealed)")
elif not D3_TRAVEL:
    add({'note': "D3 is installed but A2's travel row D2-D3 is not written yet: the edge is not walked"})
else:
    jump(122, 44, 'East along the caravan road off the edge to D3', yaw=0.0)
    add({'note': "Off D2's east edge: the travel prompt (D3, 5 days), accepted; D3's west start (-22528, 10240, 1312)"})
    add({'walk_to': {'x': W(127.5, 44)[0], 'y': W(127.5, 44)[1], 'z': ground(*W(127, 44)), 'z_tolerance': 600,
                     'radius': 128, 'timeout_seconds': 60, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': 'xeen_d3.odm'}})
    add({'assert': {'party_position': {'x': -22528, 'y': 10240, 'radius': 700}}})
    add({'note': "Back west off D3's west edge (by teleport near it on D3's flat road at 1312): the prompt, accepted; "
                 "D2's east start (21504, 10240, 1312)"})
    add({'set_pose': {'map': 'xeen_d3.odm', 'x': -30208, 'y': 10240, 'z': 1312, 'yaw': round(math.pi, 4),
                      'pitch': 0.0}})
    add({'advance_runtime': {'seconds': 0.5}})
    add({'walk_to': {'x': -32512, 'y': 10240, 'z': 1312, 'z_tolerance': 900, 'radius': 128, 'timeout_seconds': 90,
                     'clear_hostiles': 3000, 'expect': 'dialog'}})
    add({'assert': {'dialog': {'active': True}}})
    add({'select_topic': {'match_label': 'OK'}})
    add({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    add({'assert': {'map': M}})
    add({'assert': {'party_position': {'x': 21504, 'y': 10240, 'radius': 700}}})

doc = {'id': 'xeen.d2.walk', 'title': 'D2 Sprite Forest and Ogre Pass: the village, the forest, the pass, the woods',
       'world': 'xeen', 'mode': 'faithful', 'steps': steps}
with open(os.path.join(P, 'playtest.yml'), 'w') as f:
    f.write('# Written by output/studio_cal/d2/tools/gen_walk.py from the built map (A6). Houses opened: %s; '
            'dungeons entered: %s.\n' % ('yes' if HOUSES_LIVE else 'no (A4 rows pending)', sorted(HAVE) or 'none'))
    yaml.safe_dump(doc, f, sort_keys=False, width=120)
print('steps', len(steps), 'houses', HOUSES_LIVE, 'have', sorted(HAVE), 'travel', TRAVEL_LIVE)
