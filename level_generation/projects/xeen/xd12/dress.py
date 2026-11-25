#!/usr/bin/env python3
"""XD-12 Darzog's Tower, L4: furniture on top of the shell (rooms.yml), objects.yml, wiring.yml, atmosphere.yml."""
import copy

import geo
from geo import *  # noqa: F401,F403
from emit import dump, rooms_doc
import plan as P

# F12d: an open book on each lectern (the picture's own size, fitted over the top; was the bookcase picture 7t1books)
BOOK_TOP = dict(texture='xnpbook', size=[128, 128], fit=True)
FURN = {}      # room id -> list of functions that change the room dict


def furn(rid):
    def deco(fn):
        FURN.setdefault(rid, []).append(fn)
        return fn
    return deco


def plat(r, **kw):
    r.setdefault('platforms', []).append(kw)


def panel(r, wall, **kw):
    idx = COMPASS.get(wall, wall)
    L = geo.edge_len(r['id'], idx)
    if kw.get('at') == 'centre':
        s = (L - kw['length']) / 2
    elif kw.get('from') == 'end':
        s = L - kw['offset'] - kw['length']
    else:
        s = kw.get('offset', 0)
    PANEL_SPANS.setdefault((r['id'], idx), []).append((s, s + kw['length']))
    for w in r.setdefault('walls', []):
        if w['wall'] == wall:
            w.setdefault('panels', []).append(kw)
            return
    r['walls'].append({'wall': wall, 'panels': [kw]})


# --------------------------------------------------------------------------------------------- objects and wiring
OBJ = {'format': 0, 'doors': [], 'lifts': [], 'switches': [], 'chests': [], 'spawns': [], 'monsters': [],
       'lights': [], 'decorations': [], 'exits': [], 'placeholders': [], 'plates': [], 'items': []}
EVENTS = []
VARS = ['works_gate_up', 'darzog_dead_seen', 'disc_down']


def ev(eid, **kw):
    d = {'id': eid}
    d.update(kw)
    EVENTS.append(d)
    return d


def deco(did, room, name, at, **kw):
    d = {'id': did, 'room': room, 'decoration': name, 'at': at}
    d.update(kw)
    OBJ['decorations'].append(d)


def light(lid, room, at, height, radius, color, **kw):
    d = {'id': lid, 'room': room, 'at': at, 'height': height, 'radius': radius, 'color': color}
    d.update(kw)
    OBJ['lights'].append(d)


def torch(tid, room, wall, along, kind='torch02', **kw):
    """Manual wall torches are kept only above the stair halls' galleries; the rest come from the torch pass."""
    if kw.get('height', 0) < 600:
        return
    d = {'id': tid, 'room': room, 'decoration': kind, 'wall': wall, 'along': along}
    d.update(kw)
    OBJ['decorations'].append(d)


PANEL_SPANS = {}
DRESSED = {}
COMPASS = {'s': 0, 'e': 1, 'n': 2, 'w': 3}


SLOT_TIER = {1: 'c', 2: 'a', 3: 'a'}   # the rebase design: Carnage Hand 35, Wizard 36, Floating Eye 40


def spawn(sid, room, at, slot, tier, **kw):
    d = {'id': sid, 'room': room, 'at': at, 'slot': slot, 'tier': SLOT_TIER[slot]}
    d.update(kw)
    OBJ['spawns'].append(d)


def chest(cid, room, at, _title='Chest', **kw):
    d = {'id': cid, 'room': room, 'at': at}
    d.update(kw)
    OBJ['chests'].append(d)
    ev('evt:' + cid.split(':')[1], preset='chest', source=cid, title=_title)


def door(did, opening, **kw):
    d = {'id': did, 'opening': opening}
    d.update(kw)
    OBJ['doors'].append(d)


# A8 26th (F12, door leaves): the plank doors showed Gloaming's plank strip 7trimd across the leaf; now the tower's own
# braced plank door pictures, the wing pair hhm1d | hhm1d2 (twins, handles at the meeting edge) on a hinged pair, each
# picture fitted to its leaf, as the School of Sorcery's doors below.
PLANK_WINGS = [[dict(texture='hhm1d', size=[128, 256]), dict(texture='hhm1d2', size=[128, 256])]]
PLANK_DOOR = dict(kind='hinged', leaves=2, pictures=PLANK_WINGS, back_pictures=PLANK_WINGS)
# merge point 15 (the double-door rule): the School of Sorcery's carved door is two wings, hhm1d left and hhm1d2
# right (handles at the meeting edge), one per leaf of a hinged pair; never one wing tiled across the doorway.
SOS_WINGS = [[dict(texture='hhm1d', size=[128, 256]), dict(texture='hhm1d2', size=[128, 256])]]
SOS_DOOR = dict(kind='hinged', leaves=2, pictures=SOS_WINGS, back_pictures=SOS_WINGS)


# ============================================================================================ GATE FLOOR (0)
@furn('room:gate_hall')
def _(r):
    panel(r, 'e', at='centre', length=128, height=256, surface=PLANKS,
          notes='Behind the tower door\'s exit face: the door\'s own planks, so it lies on one face.')
    for y in (-1280, 1280):
        plat(r, at=[2944, y], size=[96, 384], rise=40, surface=PLANKSA, top_surface=PLANKSA,
             notes='A bench along the east wall.')
    r['ambient'] = 16


OBJ['start'] = {'room': 'room:gate_hall', 'at': [2752, 0], 'facing': 180,
                'notes': "Inside the tower door, facing west through the gate hall's arch toward the Well."}
OBJ['exits'].append({'id': 'exit:tower_door', 'room': 'room:gate_hall', 'wall': 'e', 'size': [128, 256],
                     'surface': S_('7solid01', 128, 256), 'to': 'exit:lake_island',
                     'notes': "The tower door (two plank leaves of Gloaming's 7trimd), out to the island (X2)."})
ev('evt:tower_door', preset='exit', source='exit:tower_door', title="Leave Darzog's Tower",
   text='You pull the tower door open on the wind off the lake.')
torch('deco:torch_gate_n', 'room:gate_hall', 'n', 0.5)
torch('deco:torch_gate_s', 'room:gate_hall', 's', 0.5)
torch('deco:torch_gate_w1', 'room:gate_hall', 'w', 0.12)
torch('deco:torch_gate_w2', 'room:gate_hall', 'w', 0.88)
deco('deco:gate_barrel1', 'room:gate_hall', 'bigbarel', [2944, -1600])
deco('deco:gate_barrel2', 'room:gate_hall', 'smlbarel', [2832, -1616])
deco('deco:gate_bucket', 'room:gate_hall', 'Bucket', [2944, 1660])

# arrival: why the party is here, and that magic fails
# Hooks and dressing, D-7 (2026-11-20): A3's m21.arrival in place of the map's message, on the first arrival only
# (qbit arrived_once 110503: the window would otherwise open on every entry and pause the monsters).
ev('evt:arrive', preset='script', trigger='timer', every=1, once=True, condition={'not': {'qbit': 'arrived_once'}},
   effects=[{'lua': 'XeenQuests.hook("m21.arrival")'}, {'qbit': 'arrived_once'}],
   notes="Say why the party is here, and that magic fails: A3's hook m21.arrival (its window text; a one-shot timer: a "
         "load event's window is not shown), on the first arrival only (arrived_once); set:no_magic.")

# cloisters
for k, al in (('n', 0.5), ('e', 0.25), ('s', 0.5), ('w', 0.75)):
    torch(f'deco:torch_cloister_{k}', f'room:cloister_{k}', {'n': 'n', 'e': 'e', 's': 's', 'w': 'w'}[k], 0.15)
    torch(f'deco:torch_cloister_{k}2', f'room:cloister_{k}', {'n': 'n', 'e': 'e', 's': 's', 'w': 'w'}[k], 0.85)


@furn('room:cloister_e')
def _(r):
    r['ambient'] = 14


# the Well
@furn('room:well')
def _(r):
    plat(r, id='platform:rune_circle', at=[0, 0], size=[768, 768], rise=16, surface=CWB,
         top_surface={'texture': 'td1', 'size': [512, 512], 'scale': 1.5},
         notes="The rune circle at the Well's foot (the School of Sorcery's summoning circle td1), where Darzog's lightning rises.")


# dressing (2026-11-20): against the octagon's slanted faces, 100 in, clear of the lines between the arches and the disc
for i, (x, y) in enumerate([(-632, -632), (632, -632), (632, 632), (-632, 632)]):
    # lights audit (merge point 14): MM6's brazier hangs on chains and the Well has no ceiling to hang it from (4,000
    # up): log fires on the floor instead (dec04, a floor fixture with its own light)
    deco(f'deco:well_brazier_{i}', 'room:well', 'dec04', [x, y], notes='A fire of logs by the rune circle.')
for i, h in enumerate([96, 900, 1700, 2500, 3300]):
    light(f'light:lightning_{i}', 'room:well', [0, 0], h, 1400, [170, 200, 255],
          pulse={'intensity': [0.35, 1.0], 'frequency': 2.5 + 0.4 * i},
          notes="Darzog's lightning: a pulsing column of blue-white light up the Well's axis.")

# Darzog's disc in the Well, its grille on Darzog's floor, its call buttons
OBJ['movers'] = [{'id': 'mover:disc', 'room': 'room:well', 'at': [0, 672], 'size': [384, 384], 'bottom': 2256,
                  'height': 48, 'travel': [0, 0, -2302], 'speed': 384, 'surface': CWB,
                  'top_surface': {'texture': 'td1', 'size': [512, 512], 'scale': 0.75},
                  'notes': "Darzog's disc: a slab of stone 384 square and 48 thick, the summoning circle on its top, riding the Well's north face between Darzog's floor (its start, top at 2304) and the gate floor (its end, top 2 above the floor). A mover rather than a lift so that its sides and underside take their own stone."}]
door('door:disc_grille', 'open:disc_landing', kind='slide_up', fold=True, tile=True, surface=GRATE,
     notes="A black iron grille (the School of Sorcery's grate c1d1) over the disc's landing; open only while the disc is up and Darzog is dead.")
OBJ['switches'].append({'id': 'switch:disc_call_bottom', 'room': 'room:well', 'kind': 'button', 'at': [400, 896],
                        'height': 112, 'notes': "Call button on the Well's north face beside the arch, at the disc's foot."})
OBJ['switches'].append({'id': 'switch:disc_call_top', 'room': 'room:state_n', 'kind': 'button', 'at': [320, 1024],
                        'height': 112, 'notes': "Call button beside the disc's grille on Darzog's floor."})
DISC_LOCK = ("A disc of black stone hangs in the Well behind this grille, the Baron's rune glowing on its rim. It answers "
             "to Darzog alone while he lives.")
# A8 30th (2026-11-22): the disc and its grille are set to explicit, opposite states, never toggled as a pair. With
# Trigger pairs their phase hung on evt:darzog_dead having opened the grille first: a map reset (a rebuilt map resets
# the saved map on entry, quest bits stay) moved them in the wrong phase and shut the grille in front of a rider at
# the top. The map variable disc_down says where the disc is (0 = up, its start: it resets with the doors); disc up
# means the grille open (Darzog dead), disc down the grille shut. evt:disc and evt:disc_call_bottom are two-way (the
# bottom button calls the disc down and, from the disc, rides it up); evt:disc_call_top only brings it up,
# evt:disc_ride_top only sends it down; evt:disc_restore reopens the grille on every load while the disc is up after
# Darzog's death.
DISC_NUM = 32    # mover:disc (ids.lock.yml)
GRILLE_NUM = 13  # door:disc_grille (ids.lock.yml)
DISC_TWO_WAY = (
    "if IsAtLeast(MapVar(disc_down), 1) then\n"
    f"    evt.SetDoorState({DISC_NUM}, DoorAction.Close)\n"
    f"    evt.SetDoorState({GRILLE_NUM}, DoorAction.Open)\n"
    "    SetValue(MapVar(disc_down), 0)\n"
    "else\n"
    f"    evt.SetDoorState({GRILLE_NUM}, DoorAction.Close)\n"
    f"    evt.SetDoorState({DISC_NUM}, DoorAction.Open)\n"
    "    SetValue(MapVar(disc_down), 1)\n"
    "end")
ev('evt:disc', preset='switch', source='mover:disc', title="Darzog's disc", condition={'qbit': 'darzog_slain'},
   effects=[{'lua': DISC_TWO_WAY}], text='The disc hums and glides along the Well.',
   else_effects=[{'message': DISC_LOCK}],
   notes="set:disc: two-way: up (grille open) when it is down, down (grille shut) when it is up; disc_down follows.")
OBJ['switches'].append({'id': 'switch:disc_ride_top', 'room': 'room:well', 'kind': 'button', 'at': [320, 896],
                        'height': 2416, 'floor_height': 0,
                        'notes': "A button on the Well's north face beside the landing, in reach of a rider on the disc at the top."})
ev('evt:disc_ride_top', preset='switch', source='switch:disc_ride_top', title="Darzog's disc",
   condition={'qbit': 'darzog_slain'}, opens=['mover:disc'], closes=['door:disc_grille'],
   effects=[{'lua': 'SetValue(MapVar(disc_down), 1)'}],
   text='The disc hums and glides down the Well.', else_effects=[{'message': DISC_LOCK}],
   notes='set:disc: down only (the disc down, its grille shut).')
ev('evt:disc_call_bottom', preset='switch', source='switch:disc_call_bottom', title="Darzog's disc",
   condition={'qbit': 'darzog_slain'}, effects=[{'lua': DISC_TWO_WAY}],
   text='The disc hums and glides along the Well.',
   notes='set:disc: two-way, as the disc itself: calls it down, or rides it up from the disc.',
   else_effects=[{'message': "You press the stone. Far above, at the top of the Well, a rune flares and dies: whatever "
                             "it calls is bound by its master, up on his own floor."}])
ev('evt:disc_call_top', preset='switch', source='switch:disc_call_top', title='Call the disc',
   condition={'qbit': 'darzog_slain'}, closes=['mover:disc'], opens=['door:disc_grille'],
   effects=[{'lua': 'SetValue(MapVar(disc_down), 0)'}],
   text='The disc rises up the Well to the landing.', else_effects=[{'message': DISC_LOCK}],
   notes='set:disc: up only (the disc up, its grille open).')
DISC_ON_LOAD = (  # 110500 = darzog_slain (m21.darzog_slain)
    "if IsAtLeast(MapVar(disc_down), 1) then\n"
    f"    evt.SetDoorState({GRILLE_NUM}, DoorAction.Close)\n"
    f"    evt.SetDoorState({DISC_NUM}, DoorAction.Open)\n"
    "else\n"
    f"    evt.SetDoorState({DISC_NUM}, DoorAction.Close)\n"
    "    if IsQBitSet(QBit(110500)) then\n"
    f"        evt.SetDoorState({GRILLE_NUM}, DoorAction.Open)\n"
    "    end\n"
    "end")
ev('evt:disc_restore', preset='script', trigger='load', effects=[{'lua': DISC_ON_LOAD}],
   notes="set:disc: on every load the disc and its grille take the places disc_down says (no-ops in a kept state): "
         "a reset map (disc up, grille shut, darzog_slain kept) opens the grille; a save from before disc_down (the "
         "disc down, the variable 0) brings the disc up to its rest.")
ev('evt:disc_grille', preset='script', source='door:disc_grille', title='Black grille',
   condition={'qbit': 'darzog_slain'},
   effects=[{'text': 'The grille opens when the disc is here. Step onto the disc and touch it to ride down.'}],
   else_effects=[{'message': DISC_LOCK}])


# hall of hands: two rows of plinths, statues of hands on some. Dressing (2026-11-20): the south row keeps three
# (the corners against the south wall and the middle), clear of the lines from the cloister arch to the side doors.
PLINTHS = {'00': (-1408, 2048), '02': (0, 2240), '04': (1408, 2048),
           '10': (-1408, 2752), '11': (-704, 2752), '12': (0, 2752), '13': (704, 2752), '14': (1408, 2752)}


@furn('room:hall_of_hands')
def _(r):
    for pid, (x, y) in PLINTHS.items():
        plat(r, id=f'platform:plinth_{pid}', at=[x, y], size=[192, 192], rise=64, surface=CWB, top_surface=CFB1,
             notes='A plinth where a finished carnage hand waits.')
    r['ambient'] = 16


for pid, (x, y) in PLINTHS.items():
    if (int(pid[0]) + int(pid[1])) % 2 == 0:
        deco(f'deco:hand_statue_{pid}', 'room:hall_of_hands', '7dec54', [x, y], floor_height=64,
             notes='A carnage hand not yet woken (statue).')
torch('deco:torch_hands_1', 'room:hall_of_hands', 's', 0.25)
torch('deco:torch_hands_2', 'room:hall_of_hands', 's', 0.75)
torch('deco:torch_hands_3', 'room:hall_of_hands', 'n', 0.5)
spawn('spawn:hands_w', 'room:hall_of_hands', [-1056, 2496], 1, 'b', notes='Carnage hands stepping off their plinths.')
spawn('spawn:hands_e', 'room:hall_of_hands', [1056, 2496], 1, 'b')


@furn('room:guardroom')
def _(r):
    plat(r, at=[2496, 2496], size=[384, 192], rise=72, surface=PLANKS, top_surface=PLANKSA, notes='Guards\' table.')


chest('chest:guardroom', 'room:guardroom', [2944, 2176], kind='7gt002', facing='w', treasure_level=4, random_items=2,
      gold=400)
torch('deco:torch_guard', 'room:guardroom', 'w', 0.5)
spawn('spawn:guardroom', 'room:guardroom', [2304, 2752], 1, 'b')


@furn('room:storeroom')
def _(r):
    for i, (x, y) in enumerate([(2112, -2944), (2368, -2944), (2944, -2368), (2944, -2112)]):
        plat(r, at=[x, y], size=[128, 128], rise=128, surface=PLANKS, top_surface=PLANKSA, notes='A crate.')


chest('chest:storeroom', 'room:storeroom', [2880, -2880], kind='7gt002', facing='n', treasure_level=4,
      random_items=2, gold=250)
# dressing (2026-11-20): the two barrels stood on the line between the doorways; then on the east wall's crates
# F3 feedback fix (2026-11-21): a barrel on a crate stood 34 from its 128 edge (props stand on the floor, 48 or more
# from any edge): now a pair on the floor in the north-east corner, by the crates, clear of both doorways
deco('deco:store_barrel1', 'room:storeroom', 'bigbarel', [2960, -2004])
deco('deco:store_barrel2', 'room:storeroom', 'bigbarel', [2832, -2004])
deco('deco:store_sack1', 'room:storeroom', 'floursac', [2944, -2624])
deco('deco:store_sack2', 'room:storeroom', 'bag01', [2624, -2944])
torch('deco:torch_store', 'room:storeroom', 'n', 0.5)


@furn('room:cistern')
def _(r):
    r.setdefault('levels', []).append(
        {'id': 'level:cistern', 'outline': rect(-1024, -2752, 1024, -2240), 'floor': -160, 'surface': WATER, 'edge': CWB,
         'notes': 'The cistern: water 160 down, walked round.'})


OBJ.setdefault('floors', []).append({'id': 'floor:cistern', 'of': 'level:cistern', 'kind': 'water'})
# F14 (A8 26th): iron rungs up the cistern's north and south edges (as XD-21's race), so a party that drops into the
# water climbs back onto the walk without spells (check_drops: the water was a pocket 160 down).
OBJ.setdefault('ladders', []).extend([
    {'id': 'ladder:cistern_n', 'room': 'room:cistern', 'at': [-512, -2248], 'facing': 'n', 'height': 160,
     'exit': [-512, -2144], 'grab_at_top': True, 'surface': S_('bemv', 32, 256, uneven=True),
     'notes': "F14: iron rungs up the cistern's north edge onto the walk."},
    {'id': 'ladder:cistern_s', 'room': 'room:cistern', 'at': [512, -2744], 'facing': 's', 'height': 160,
     'exit': [512, -2848], 'grab_at_top': True, 'surface': S_('bemv', 32, 256, uneven=True),
     'notes': "F14: iron rungs up the cistern's south edge onto the walk."},
])
torch('deco:torch_cistern_1', 'room:cistern', 'n', 0.2)
torch('deco:torch_cistern_2', 'room:cistern', 'n', 0.8)
deco('deco:cistern_bucket', 'room:cistern', 'Bucket', [-1344, -2944])
spawn('spawn:cistern', 'room:cistern', [0, -2496], 3, 'a', notes='Floating eyes over the cistern.')


@furn('room:cells')
def _(r):
    r['ambient'] = 20


deco('deco:cells_cage1', 'room:cells', 'Bonecage', [-2880, -2880])
deco('deco:cells_cage2', 'room:cells', '7dec06', [-2368, -2880], notes='A hanging cage.')
deco('deco:cells_bones1', 'room:cells', '7dec18', [-2112, -2624])
deco('deco:cells_bones2', 'room:cells', 'dec29', [-2880, -2240])
deco('deco:cells_skeleton', 'room:cells', 'dec05', [-2560, -2944])
torch('deco:torch_cells', 'room:cells', 'e', 0.5)
spawn('spawn:cells', 'room:cells', [-2496, -2368], 1, 'b')


@furn('room:crypt')
def _(r):
    # dressing (2026-11-20): the north row as before; the south row's three (across the line from the stair doorway
    # to the hall of hands, one in front of the doorway) now two, lying along the west wall
    for i, (x, y, w, d) in enumerate([(-2880, 2304, 256, 128), (-2880, 2560, 256, 128), (-2752, 2880, 128, 256),
                                      (-2432, 2880, 128, 256)]):
        plat(r, at=[x, y], size=[w, d], rise=72, surface=CWB1, top_surface=CFB1,
             notes="A coffin on its bier: one of Darzog's failed apprentices.")
    r['ambient'] = 20


chest('chest:crypt', 'room:crypt', [-2176, 2880], facing='n', size=[128, 256, 72], surface=CWB1, top_surface=CFB1,
      treasure_level=4, random_items=2, _title='Sarcophagus')
deco('deco:crypt_skulls', 'room:crypt', 'sklplrev', [-2944, 2768])
deco('deco:crypt_candle', 'room:crypt', 'dec02', [-2496, 2496])
torch('deco:torch_crypt', 'room:crypt', 'e', 0.5)

# west stair hall (0 -> 768)
torch('deco:torch_wstair_1', 'room:west_stair', 'e', 0.25)
torch('deco:torch_wstair_2', 'room:west_stair', 'w', 0.5, floor_height=0)
torch('deco:torch_wstair_3', 'room:west_stair', 'e', 0.75, height=896, floor_height=0)
spawn('spawn:wstair_gallery', 'room:west_stair', [-2112, 384], 1, 'b', floor_height=768,
      notes='Hands on the upper gallery, coming down the stair.')
# A quiet arrival (A8 session 25): the Well's eye group stood in line with the tower door, the gate hall arch and
# the Well arch, and Paralyzed the party within seconds of arriving (A3, segment 37). It moved to the cistern's
# west end, out of sight of the arrival; the Well keeps the eyes that drift in from the floors above.
spawn('spawn:cistern_w', 'room:cistern', [-1152, -2496], 3, 'a',
      notes='Floating eyes over the cistern (west end), out of sight of the arrival.')

# doors of the gate floor
door('door:guardroom', 'open:gate_guardroom', **PLANK_DOOR)
door('door:storeroom', 'open:gate_store', **PLANK_DOOR)
door('door:crypt', 'open:hands_crypt', **PLANK_DOOR)
door('door:cells', 'open:cistern_cells', **PLANK_DOOR)
for d, t in (('door:guardroom', 'Guardroom door'), ('door:storeroom', 'Storeroom door'), ('door:crypt', 'Crypt door'),
             ('door:cells', 'Cell block door')):
    ev('evt:door_' + d.split(':')[1], preset='door', source=d, title=t)

# ============================================================================================ THE WORKS (768)
@furn('room:forge')
def _(r):
    r.setdefault('levels', []).append(
        {'id': 'level:forge_lava', 'outline': rect(-1536, 2752, 1536, 2944), 'floor': 768 - 96, 'surface': LAVA,
         'edge': CWB1, 'notes': 'The lava channel along the north wall, a step down: it burns.'})
    # dressing (2026-11-20): by the lava channel, north of the line between the side doors (they stood on the lines
    # from the walk's arch to the side doors)
    for i, x in enumerate((-1024, -384, 384)):
        plat(r, at=[x, 2656], size=[128, 96], rise=72, surface=CKB, top_surface=CFB1, notes='An anvil block.')
    r['ambient'] = 12


OBJ['floors'].append({'id': 'floor:forge_lava', 'of': 'level:forge_lava', 'kind': 'lava'})
# F14 (fixup 2026-11-22, as the cistern's): iron rungs up the lava channel's south edge at two places, so a party
# that falls in climbs out without spells (check_drops: the channel was a pocket 96 down)
OBJ.setdefault('ladders', []).extend([
    {'id': f'ladder:forge_lava_{sid}', 'room': 'room:forge', 'at': [x, 2760], 'facing': 's', 'height': 96,
     'exit': [x, 2656], 'grab_at_top': True, 'surface': S_('bemv', 32, 256, uneven=True),
     'notes': "F14: iron rungs up the lava channel's south edge onto the forge floor."}
    for sid, x in (('w', -1344), ('e', 1024))])
deco('deco:forge_hand1', 'room:forge', '7dec55', [-1344, 2048], notes='A half-built hand (statue).')
deco('deco:forge_hand2', 'room:forge', '7dec55', [1344, 2048])
# lights audit (merge point 14): MM6's brazier hangs on chains, so it hangs from the forge's ceiling (640 clear), its
# top 2 into it (146 high)
deco('deco:forge_brazier1', 'room:forge', 'brzier00', [-1664, 2048], height=492, hangs=True,
     notes='A brazier hung on its chains from the ceiling.')
deco('deco:forge_brazier2', 'room:forge', 'brzier00', [1664, 2048], height=492, hangs=True,
     notes='A brazier hung on its chains from the ceiling.')
light('light:forge_lava_w', 'room:forge', [-768, 2848], 64, 900, [255, 110, 40], pulse={'intensity': [0.7, 1.0], 'frequency': 0.7})
light('light:forge_lava_e', 'room:forge', [768, 2848], 64, 900, [255, 110, 40], pulse={'intensity': [0.7, 1.0], 'frequency': 0.9, 'phase': 0.5})
spawn('spawn:forge_w', 'room:forge', [-1152, 2496], 1, 'b', notes='Smiths of the hands.')
spawn('spawn:forge_e', 'room:forge', [512, 2496], 1, 'b')


@furn('room:assembly')
def _(r):
    for i, x in enumerate((-1152, -384, 384, 1152)):
        plat(r, at=[x, -2944], size=[512, 96], rise=256, surface=CKB, top_surface=CFB1,
             notes='A rack of iron limbs along the south wall.')
    r['ambient'] = 14


OBJ['switches'].append({'id': 'switch:works_winch', 'room': 'room:assembly', 'kind': 'lever', 'wall': 'w',
                        'along': 0.75, 'base': CKB, 'off': S_('cwb', 128, 256),
                        'notes': "The works gate's winch lever on the assembly hall's west wall."})
door('door:works_gate', 'open:works_estair', kind='slide_up', fold=True, tile=True, surface=GRATE,
     notes="The works gate: an iron portcullis (c1d1) between the east walk and the east stair hall.")
ev('evt:works_winch', preset='switch', source='switch:works_winch', title='Works gate winch', opens=['door:works_gate'],
   sets={'map_var': 'works_gate_up'},
   effects=[{'lua': 'evt.PlaySoundName("xeen_winch", 1856, 640, 960)'}],
   text='Chains rattle: across the works, the gate to the east stair grinds up.',
   notes="AU's winch (ratchet and rope) heard at the works gate (1856, 640, 960), which it raises.")
ev('evt:works_gate', preset='script', source='door:works_gate', title='Works gate',
   condition={'map_var': 'works_gate_up'}, effects=[{'text': 'The works gate stands open.'}],
   else_effects=[{'message': "An iron gate bars the way to the east stair. Its chains run off along the walls toward "
                             "the south: the winch that raises it must be in the assembly hall."}])
torch('deco:torch_assembly_1', 'room:assembly', 'n', 0.25)
torch('deco:torch_assembly_2', 'room:assembly', 'n', 0.75)
spawn('spawn:assembly_w', 'room:assembly', [-1024, -2432], 1, 'b')
spawn('spawn:assembly_e', 'room:assembly', [1024, -2432], 1, 'b')


@furn('room:smelter')
def _(r):
    r.setdefault('levels', []).append(
        {'id': 'level:smelter_pit', 'outline': rect(2240, 2240, 2752, 2752), 'floor': 768 - 128, 'surface': LAVA,
         'edge': CWB1, 'notes': 'The smelting pit: lava a step down.'})


OBJ['floors'].append({'id': 'floor:smelter_pit', 'of': 'level:smelter_pit', 'kind': 'lava'})
# F14 (fixup 2026-11-22): iron rungs up the smelting pit's north edge (check_drops: a pocket 128 down)
OBJ.setdefault('ladders', []).append(
    {'id': 'ladder:smelter_pit', 'room': 'room:smelter', 'at': [2496, 2736], 'facing': 'n', 'height': 128,
     'exit': [2496, 2848], 'grab_at_top': True, 'surface': S_('bemv', 32, 256, uneven=True),
     'notes': "F14: iron rungs up the smelting pit's north edge onto the smelter floor."})
light('light:smelter', 'room:smelter', [2496, 2496], 64, 900, [255, 110, 40], pulse={'intensity': [0.6, 1.0], 'frequency': 0.8})
chest('chest:smelter', 'room:smelter', [2944, 2048], kind='7gt002', treasure_level=4, random_items=2)
spawn('spawn:smelter', 'room:smelter', [2112, 2880], 1, 'b')

# D-7 (2026-11-20): the third heap from (-2880, 2240), 86 from the line window -> south door, into the south-west corner
for i, (x, y) in enumerate([(-2880, 2880), (-2240, 2944), (-2913, 1990), (-2048, 2816)]):
    deco(f'deco:scrap_{i}', 'room:scrap_hall', ['trasheap', '7dec01', '7dec10', 'trasheap'][i], [x, y])
torch('deco:torch_scrap', 'room:scrap_hall', 'e', 0.5)
spawn('spawn:scrap', 'room:scrap_hall', [-2304, 2560], 1, 'b')

deco('deco:parts_barrel', 'room:parts_store', 'bigbarel', [2944, -2944])
deco('deco:parts_barrel2', 'room:parts_store', 'smlbarel', [2816, -2944])
deco('deco:parts_sack', 'room:parts_store', 'floursac', [2048, -2944])
torch('deco:torch_parts', 'room:parts_store', 'w', 0.5)


@furn('room:quarters')
def _(r):
    for i, (x, y) in enumerate([(-2880, -2112), (-2880, -2624), (-2112, -2880), (-2432, -2880)]):
        w, d = ((256, 128) if i < 2 else (128, 256))
        plat(r, at=[x, y], size=[w, d], rise=48, surface=WOOD, top_surface=S_('t2bedsht', 128, 256),
             notes="An apprentice's bed.")
    plat(r, at=[-2304, -2304], size=[256, 192], rise=72, surface=WOOD, top_surface=WOOD, notes='A table.')


# A8 29th (MP42's 7gt002 chest): the foot locker by the SE bed, east wall; was (-2048, -2048), inside the west stair's
# doorway (x -2240..-1984)
chest('chest:quarters', 'room:quarters', [-1984, -2880], kind='7gt002', facing='n', treasure_level=4, random_items=2)
deco('deco:quarters_candle', 'room:quarters', 'cndlab0', [-2304, -2304], floor_height=840)
torch('deco:torch_quarters', 'room:quarters', 'n', 0.5)
spawn('spawn:quarters', 'room:quarters', [-2560, -2496], 2, 'b', notes="Apprentices in their quarters.")

for k in 'nesw':
    torch(f'deco:torch_works_{k}', f'room:works_{k}', k, 0.2)
    torch(f'deco:torch_works_{k}2', f'room:works_{k}', k, 0.8)
spawn('spawn:works_e', 'room:works_e', [1408, -512], 3, 'a')

door('door:smelter', 'open:forge_smelter', **PLANK_DOOR)
door('door:quarters', 'open:assembly_quarters', **PLANK_DOOR)
ev('evt:door_smelter', preset='door', source='door:smelter', title='Smelter door')
ev('evt:door_quarters', preset='door', source='door:quarters', title="Apprentices' door")
torch('deco:torch_estair_1', 'room:east_stair', 'w', 0.5)
torch('deco:torch_estair_2', 'room:east_stair', 'e', 0.25, height=896, floor_height=768)

# ============================================================================================ THE LIBRARY (1536)
CHAND = 'dec27'
for i, (rid, x, y) in enumerate([('room:reading_room', -896, 2496), ('room:reading_room', 896, 2496),
                                  ('room:great_library', -896, -2496), ('room:great_library', 896, -2496)]):
    deco(f'deco:chandelier_{i}', rid, CHAND, [x, y], notes='A chandelier hanging from the ceiling.')
    light(f'light:chandelier_{i}', rid, [x, y], 520, 1000, [255, 220, 170])


@furn('room:reading_room')
def _(r):
    # dressing (2026-11-20): the tables in the north half (they stood on the lines from the walk's arch to the studies'
    # doors), the Book of Speed's lectern off the line between the two studies' doors
    for i, x in enumerate((-768, 0, 768)):
        plat(r, at=[x, 2688], size=[384, 128], rise=72, surface=WOOD, top_surface=WOOD, notes='A reading table.')
    panel(r, 'n', offset=128, length=512, height=512, surface=BOOKS, notes='Bookcase.')
    panel(r, 'n', at='centre', length=768, height=512, surface=BOOKS, notes='Bookcases.')
    plat(r, id='platform:lectern_speed', at=[-1536, 2816], size=[64, 128], rise=104, surface=WOOD,
         top_surface=BOOK_TOP, notes='Lectern: the Book of Speed.')
    r['ambient'] = 18


@furn('room:great_library')
def _(r):
    # dressing (2026-11-20): the north-west case (across the line from the walk's arch to the west study) is two cases
    # against the north wall; the desk (on the line to the east study) moved to the south half
    for x, y, w, d in ((0, -2304, 640, 96), (-1024, -2752, 640, 96), (0, -2752, 640, 96), (-1408, -2048, 96, 256),
                       (-896, -2048, 96, 256)):
        plat(r, at=[x, y], size=[w, d], rise=320, surface=BOOKS, top_surface=WOOD,
             notes='A free-standing bookcase.' if d == 96 else 'A bookcase against the north wall.')
    plat(r, at=[768, -2752], size=[384, 192], rise=80, surface=WOOD, top_surface=WOOD,
         notes="The Chief Librarian's desk.")
    plat(r, id='platform:lectern_accuracy', at=[1600, -2752], size=[64, 128], rise=104, surface=WOOD,
         top_surface=BOOK_TOP, notes='Lectern: the Book of Accuracy.')
    r['ambient'] = 18


chest('chest:librarian', 'room:great_library', [1152, -3008], size=[256, 96, 256],
      surface=S_('7t1cabs', 64, 128), end_surface=dict(WOOD, uneven=True), top_surface=WOOD, treasure_level=4, random_items=1,
      items=['library_key'], _title='Cabinet')
chest('chest:great_library', 'room:great_library', [-1600, -3008], size=[256, 96, 256], surface=BOOKS,
      end_surface=dict(WOOD, uneven=True), top_surface=WOOD, treasure_level=4, random_items=2, _title='Cabinet')
OBJ['monsters'].append({'id': 'monster:librarian', 'room': 'room:great_library', 'monster': 11191, 'at': [1152, -2560],
                        'facing': 90, 'hostile': True, 'group': 21, 'name': 'Chief Librarian',
                        'notes': "The Chief Librarian (the Wizards' B tier, Sorcerer 45, with his own name) guards his cabinet with the library stair's key."})
for i, x in enumerate((-768, 0, 768)):
    deco(f'deco:reading_candle_{i}', 'room:reading_room', 'cndlab0', [x + 128, 2688], floor_height=1608)
spawn('spawn:reading_w', 'room:reading_room', [-1152, 2624], 2, 'b', notes='Apprentices at their books.')
spawn('spawn:reading_e', 'room:reading_room', [1536, 2240], 2, 'b')
spawn('spawn:great_library', 'room:great_library', [-512, -2496], 2, 'b')
spawn('spawn:library_s', 'room:library_s', [0, -1408], 2, 'b')
spawn('spawn:library_n', 'room:library_n', [384, 1408], 3, 'b')
# D-132 (xeen-fb4-dungeon6, 2026-11-25): at (-2496, 0) its shooters saw the party over the flight's edge with a thin
# shot (check_ledge_shots.py); 512 south of it the flight hides them.
spawn('spawn:library_stair', 'room:library_stair', [-2496, -512], 3, 'b')

STUDY = {'room:study_ne': ('personality', 'BasePersonality', 'Personality', [2880, 2880]),
         'room:study_nw': ('intellect', 'BaseIntellect', 'Intellect', [-2880, 2880]),
         'room:study_se': ('might', 'BaseMight', 'Might', [2880, -2880]),
         'room:study_sw': ('endurance', 'BaseEndurance', 'Endurance', [-2880, -2880])}
for rid, (k, sel, name, at) in STUDY.items():
    def _mk(rid=rid, k=k, at=at):
        @furn(rid)
        def _(r):
            plat(r, id=f'platform:lectern_{k}', at=at, size=[96, 96], rise=104, surface=WOOD, top_surface=BOOK_TOP,
                 notes=f'Lectern: the Book of {k.title()}.')
            sx = 2496 if at[0] > 0 else -2496
            sy = 2496 if at[1] > 0 else -2496
            desk, size = [sx, sy + (-384 if sy > 0 else 384)], [256, 128]
            if rid == 'room:study_se':
                # dressing (2026-11-20): against the east wall, off the line between the stair's door and the library's
                desk, size = [2944, -2112], [128, 256]
            plat(r, at=desk, size=size, rise=72, surface=WOOD, top_surface=WOOD,
                 notes='A study desk.')
            r['ambient'] = 18
    _mk()
    deco(f'deco:study_candle_{k}', rid, 'dec02', [at[0] - (192 if at[0] > 0 else -192), at[1]])
    light(f'light:study_{k}', rid, [at[0] - (192 if at[0] > 0 else -192), at[1]], 160, 700, [255, 210, 150])

BOOK_BITS = {'might': 11230, 'endurance': 11231, 'intellect': 11232, 'personality': 11233, 'speed': 11234,
             'accuracy': 11235}
for k, sel, name, rid in P.BOOKS:
    ev(f'evt:book_{k}', preset='script', source=f'platform:lectern_{k}', title=f'Book of {name}',
       condition={'not': {'player_bit': BOOK_BITS[k]}},
       effects=[{'add': {'var': sel, 'value': 5}}, {'player_bit': BOOK_BITS[k]},
                {'text': f"BOOK OF {name.upper()}. One of Darzog's own studies, written for his apprentices; whoever "
                         f"reads it to the end is changed by it. +5 {name} (permanent)."}],  # F13: a status line
       else_effects=[{'text': f'You have already learned what the book of {name.lower()} can teach.'}],
       notes=f'poi:book_{k}: +5 {name}, once per character (player bit {BOOK_BITS[k]}).')
spawn('spawn:study_nw', 'room:study_nw', [-2304, 2240], 3, 'b')
spawn('spawn:study_sw', 'room:study_sw', [-2240, -2304], 2, 'b')

for k in 'nesw':
    torch(f'deco:sconce_library_{k}', f'room:library_{k}', k, 0.5, kind='scon100')
for k, rid in (('n', 'room:library_n'), ('s', 'room:library_s')):
    def _mkb(rid=rid, k=k):
        @furn(rid)
        def _(r):
            panel(r, k, offset=256, length=768, height=448, surface=BOOKS, notes='Bookcases along the walk.')
    _mkb()


@furn('room:library_e')
def _(r):
    panel(r, 'w', id='panel:warning_note', offset=1120, length=64, bottom=128, height=128,
          surface={'texture': 't2bedsht', 'size': [128, 256], 'scale': 0.5},
          notes="An apprentice's note pinned to the wall at the head of the east stair (stand-in: the sheet t2bedsht; a parchment note is to be generated).")


ev('evt:warning_note', preset='script', source='panel:warning_note', title='A note', window=True,
   effects=[{'message': "A note, pinned at the head of the stair in a hurried hand: 'MIND THE CRACKED FLAGS. The Master's "
                        "hatches drop you straight down to the works, and the hands down there are not friendly. Walk "
                        "round them. -- Wil'"}],
   notes='poi:warning_note: names the trapdoors\' tell before the first one.')

door('door:library_stair', 'open:library_lstair', **SOS_DOOR,
     notes="The library stair door (the School of Sorcery's carved door hhm1d2), locked: the library key.")
ev('evt:library_stair', preset='door', source='door:library_stair', title='The library stair door',
   condition={'item': 'library_key'}, action='open', sets={'qbit': 'library_door_opened'},
   text="The library key turns in the carved lock.",
   else_effects=[{'message': "Locked. The keyhole is cut as a sorcerer's sigil. The Chief Librarian keeps the key to "
                             "the upper stair in his cabinet in the great library, south of the Well."}])
door('door:study_nw', 'open:reading_study_nw', **SOS_DOOR)
door('door:study_sw', 'open:great_study_sw', **SOS_DOOR)
ev('evt:door_study_nw', preset='door', source='door:study_nw', title='Study door')
ev('evt:door_study_sw', preset='door', source='door:study_sw', title='Study door')

# trapdoors: a lift in the works room under each, raised flush with the library floor
for i, (tid, up, low, c) in enumerate(P.TRAPDOORS):
    OBJ['lifts'].append({'id': f'lift:{tid}', 'room': low, 'at': list(c), 'size': [256, 256], 'travel': 736,
                         'thickness': 32, 'speed': 900, 'state': 'up', 'surface': CRACK,
                         'notes': f"A trapdoor in {up}'s floor: a hatch of cracked flags (c1t1fl) sagging 32 below the library floor in a broken rim of red rubble (the hole's sides, cfb1), loose stones round it; it drops to {low}."})
    # what lies round the broken rim: the bones of one who did not mind the flags, a skull
    # D-7 (2026-11-20): the reading room's hatch (trap2) lies where the lines between its doors, arch and windows
    # cross, and its skull (7dec20, radius 52) stood 7 from one: it lies 300 south of the hatch's middle, the nearest
    # place clear of every line (the bones, radius 16, are below the audit's size)
    # F3 feedback fix (2026-11-21): the bones lay 26-28 from the hatch's rim and the skull over it (a 760 drop once it
    # falls): every footprint now 48 or more from the hatch; trap4's skull south of it, clear of the study's lines
    skull = {'trap2': (80, -320), 'trap4': (100, -236)}.get(tid, (244, 170))
    for j, (dx, dy, name) in enumerate([(-210, -60, 'dec29'), (-60, 212, 'dec29'), (skull[0], skull[1], '7dec20')]):
        deco(f'deco:{tid}_bones_{j}', up, name, [c[0] + dx, c[1] + dy],
             notes='Bones by the broken flags: someone who did not mind them.')
    ev(f'evt:{tid}', preset='text', trigger='step', source=f'lift:{tid}', closes=[f'lift:{tid}'],
       text='The cracked flags give way under you! You drop through to the works below.',
       notes='set:trapdoors: stepping on the hatch drops it, and the party with it.')
    # the winch below, on the nearest wall
    OBJ['switches'].append({'id': f'switch:winch_{tid}', 'room': low, 'kind': 'lever', 'at': None, 'base': CKB,
                            'off': S_('cwb', 128, 256), 'notes': 'The hatch\'s winch: raises it again.'})
    ev(f'evt:winch_{tid}', preset='switch', source=f'switch:winch_{tid}', title='Hatch winch', toggles=[f'lift:{tid}'],
       text='The winch clatters, and the hatch moves on its chains.')
WINCH_AT = {'trap1': [-1152, 1792], 'trap2': [1792, 2176], 'trap3': [-1792, -1152], 'trap4': [2240, -3072],
            'trap5': [-3072, 2304]}
for s in OBJ['switches']:
    if s['id'].startswith('switch:winch_'):
        s['at'] = WINCH_AT[s['id'].split('winch_')[1]]

# ============================================================================================ DARZOG'S FLOOR (2304)
@furn('room:darzog_hall')
def _(r):
    r.setdefault('levels', []).append(
        {'id': 'level:dais', 'outline': rect(1216, 2176, 1664, 2816), 'floor': 2304 + 64, 'surface': TFB03,
         'edge': CKB, 'notes': "The Baron's dais at the east end."})
    r['ceiling_levels'] = [{'ceiling': 3040, 'outline': rect(-1536, 2176, 1536, 2816), 'edge': CWB,
                            'notes': 'A raised coffer over the length of the hall.'}]
    r['floor_surfaces'] = None
    plat(r, at=[1536, 2496], size=[128, 192], rise=192, surface=CWB1, top_surface=RUG['a'],
         notes="Darzog's chair of red stone on the dais.")
    for i, x in enumerate((-1280, -640, 0, 640)):
        plat(r, id=f'platform:rug_{i}', at=[x, 2496], size=[512, 384], rise=4, surface=RUGF,
             top_surface={'texture': 'tfb1r4i', 'size': [64, 64]},
             notes="A length of the inlaid rug (Castle Gloaming's tfb1r4).")
    panel(r, 'n', offset=192, length=128, height=256, bottom=96, surface=BANNER_A, notes='Banner.')
    panel(r, 's', offset=1856, length=128, height=256, bottom=96, surface=BANNER_B, notes='Banner.')
    panel(r, 'e', at='centre', length=128, height=256, bottom=96, surface=PORT[1], notes="The Baron's portrait.")
    r['ambient'] = 20


# dressing (2026-11-20): the south-east candelabrum stood on the line from the study's door to the bedchamber's; the
# east pair now flanks the dais' north-west corner
for i, (x, y) in enumerate([(-1536, 2176), (-1536, 2816), (1152, 2880), (896, 2816)]):
    deco(f'deco:hall_candelabrum_{i}', 'room:darzog_hall', 'dec02', [x, y])
    light(f'light:hall_candle_{i}', 'room:darzog_hall', [x, y], 200, 800, [255, 200, 150])
light('light:dais', 'room:darzog_hall', [1440, 2496], 400, 900, [180, 200, 255], pulse={'intensity': [0.6, 1.0], 'frequency': 1.5},
      notes='Cold light on the dais.')
OBJ['monsters'].append({'id': 'monster:darzog', 'room': 'room:darzog_hall', 'monster': 11194, 'at': [1344, 2496],
                        'floor_height': 2368, 'facing': 180, 'hostile': True, 'group': 30,
                        'notes': 'Baron Darzog (the boss row 11194: level 55, three times the hit points, his name) on his dais.'})
for i, (x, y) in enumerate([(-1280, 2240), (-1280, 2752), (-384, 2240), (-384, 2752), (512, 2240), (512, 2752)]):
    OBJ['monsters'].append({'id': f'monster:clone_{i + 1}', 'room': 'room:darzog_hall', 'monster': 11195,
                            'at': [x, y], 'facing': 180, 'hostile': True, 'group': 31,
                            'notes': "One of Darzog's six clones: his face, his robes, his lightning."})
ev('evt:darzog_hall_cue', preset='text', trigger='step', source='room:darzog_hall', once=True,
   text="Seven figures in the Baron's robes turn as one. 'Which of us,' they ask together, 'will you kill first?'",
   notes='set:darzog.')
ev('evt:darzog_dead', preset='script', trigger='timer', every=2,
   # (not while the disc is down: only after a map reset with darzog_slain set can it be down while he lives)
   condition={'all': [{'kills': {'monster': 'monster:darzog'}}, {'not': {'map_var': 'disc_down'}}]},
   once=True, opens=['door:disc_grille'],
   # Hooks and dressing, D-7 (2026-11-20): A3's m21.darzog sets darzog_slain and shows the window (after the shake)
   effects=[{'shake': {'strength': 0.5, 'seconds': 2}}, {'lua': 'XeenQuests.hook("m21.darzog")'}],
   notes="goal:darzog: his death opens the disc's grille (the disc is up); A3's hook m21.darzog sets darzog_slain and says so.")


@furn('room:darzog_study')
def _(r):
    plat(r, at=[-2496, 2560], size=[384, 192], rise=80, surface=WOOD, top_surface=WOOD, notes="Darzog's desk.")
    plat(r, id='platform:journal', at=[-2560, 2560], size=[96, 64], rise=16, base=80, surface=BOOKS,
         top_surface=BOOKS, notes="Darzog's journal, open on the desk.")
    panel(r, 'n', at='centre', length=768, height=512, surface=BOOKS, notes='Bookcases.')
    r['ambient'] = 20


ev('evt:journal', preset='script', source='platform:journal', title="Darzog's journal", window=True,
   effects=[{'message': "DARZOG'S JOURNAL, the last page: '... The old fool Crodo sits behind my own portrait in my "
                        "bedchamber, where he may admire me while he rots. Let him send his dreams to Newcastle's "
                        "tinkers; no spell leaves this tower, and no spell enters it but mine. My new master in the "
                        "clouds is pleased. When the King's precious \"brother\" sits the throne, I shall have Crodo's "
                        "place at last.'"}],
   notes="poi:darzog_journal: names the portrait (no spoiler before M21: this is M21).")
chest('chest:darzog_hoard', 'room:darzog_study', [-2880, 2048], kind='7gt002', facing='e', treasure_level=5,
      random_items=3, gold=1500, _title='Chest')
deco('deco:study_candle', 'room:darzog_study', 'dec02', [-2176, 2560])
deco('deco:desk_skull', 'room:darzog_study', '7dec20', [-2400, 2600], floor_height=2384)
deco('deco:desk_candle', 'room:darzog_study', 'cndlab0', [-2660, 2510], floor_height=2384)
deco('deco:desk_goblet', 'room:darzog_study', '7dec48', [-2400, 2500], floor_height=2384)
light('light:darzog_study', 'room:darzog_study', [-2176, 2560], 180, 700, [255, 200, 150])


@furn('room:bedchamber')
def _(r):
    plat(r, at=[2176, 2880], size=[256, 256], rise=56, surface=WOOD, top_surface=S_('t2bedsht', 128, 256),
         notes="Darzog's bed.")
    panel(r, 0, offset=512, length=128, height=256, bottom=64, surface=TAPESTRY,
          notes='Tapestry (on the south wall: the east wall is the window).')
    r['ambient'] = 22


door('door:portrait', 'open:bedchamber_cell', kind='slide_up', secret=True, surface=PORT[2], back_surface=CNB,
     notes="Darzog's portrait over the cell's door: a secret leaf (cnbport-3) that rises once Darzog is dead.")
ev('evt:portrait', preset='door', source='door:portrait', side='room:bedchamber', title="Darzog's portrait",
   condition={'qbit': 'darzog_slain'}, action='open',
   text="With Darzog dead, the portrait is only paint and wood. It slides up into the wall on a cell.",
   else_effects=[{'message': "The Baron in oils, haughty and gaunt. Behind the painted eyes something moves: an old "
                             "man's face, pressed to the other side, then gone. The frame will not shift while "
                             "Darzog's spell holds it."}],
   notes='set:crodo.')
OBJ['monsters'].append({'id': 'monster:crodo', 'room': 'room:crodo_cell', 'monster': 11900, 'at': [2880, 2880],
                        'facing': 225, 'hostile': False, 'group': 40, 'immobile': True,
                        'notes': "Crodo (the world's character row 11900: an old man in robes, friendly), peaceful, in his cell."})
# Relations (lane A8's move, 2026-11-20; merge point 3 the same day): the world's relations.yml makes the three
# families the party's foes at long range and Crodo friendly, and since merge point 3 the studio's hostility check
# reads it, so the map no longer restates those rows. The Eyes are kept from the constructs and the wizards (and
# Crodo) both ways, as before the move with MM7's ids: the world sets no feud between them, and this keeps it so
# whatever hostile.txt says.
CONSTRUCTS, WIZARDS, EYES, CRODO = [11600, 11601, 11602, 11603], list(range(11190, 11197)), [11570, 11571, 11572], [11900]
OBJ['relations'] = [{'of': EYES, 'toward': kind, 'relation': 'friendly', 'both_ways': True}
                    for kind in CONSTRUCTS + WIZARDS + CRODO]
# Hooks and dressing, D-7 (2026-11-20): A3's once-hook m21.crodo sets crodo_freed, gives the 35,000 experience,
# Crodo's words (with the vault's word) and the autonote; on later visits its else text. The map hides Crodo after.
ev('evt:crodo', preset='script', trigger='step', source='room:crodo_cell',
   effects=[{'lua': 'XeenQuests.hook("m21.crodo")'}, {'hide_actors': 40}],
   notes="goal:crodo and M21's reveal: A3's once-hook m21.crodo (crodo_freed, 35,000 experience each, the vault word); "
         "Crodo (group 40) gone home after it.")


@furn('room:crodo_cell')
def _(r):
    plat(r, at=[2752, 2752], size=[96, 96], rise=40, surface=WOOD, top_surface=WOOD, notes='A stool.')


deco('deco:crodo_bowl', 'room:crodo_cell', 'foodbowl', [2944, 2688])
light('light:crodo', 'room:crodo_cell', [2816, 2816], 400, 600, [200, 210, 255])


@furn('room:clone_vats')
def _(r):
    # dressing (2026-11-20): one block of four in the south-east corner (the north-west vat stood on the line between
    # the portrait hall's doorway and the sky stair's)
    for i, (x, y) in enumerate([(2496, -2496), (2816, -2496), (2496, -2816), (2816, -2816)]):
        plat(r, at=[x, y], size=[256, 256], rise=128, surface=CKB,
             top_surface={'texture': 'xwbrew', 'size': [128, 128], 'liquid': 'liquid', 'flow': 'left'},
             notes='A vat of green brew where a clone was grown.')
    r['ambient'] = 16


light('light:vats', 'room:clone_vats', [2656, -2656], 300, 900, [140, 255, 140], pulse={'intensity': [0.5, 1.0], 'frequency': 0.6})
spawn('spawn:clone_vats', 'room:clone_vats', [2496, -2112], 1, 'c', notes='Carnage hands guarding the vats.')


@furn('room:guard_hall')
def _(r):
    for i, x in enumerate((-2752, -2240)):
        plat(r, at=[x, -2976], size=[384, 96], rise=256, surface=CKB, top_surface=CFB1, notes='A weapon rack.')


chest('chest:guard_hall', 'room:guard_hall', [-2048, -2048], kind='7gt002', facing='n', treasure_level=4,
      random_items=2, gold=600)
spawn('spawn:guard_hall', 'room:guard_hall', [-2496, -2368], 1, 'c', notes='Carnage hands, the Baron\'s guard.')
torch('deco:torch_guard_hall', 'room:guard_hall', 'n', 0.5)


@furn('room:portrait_hall')
def _(r):
    for i, off in enumerate((288, 736, 1936, 2352, 2768, 3184)):   # off the state gallery's doorway (1152-1664)
        panel(r, 'n', offset=off, length=128, height=256, bottom=96, surface=PORT[i % 4], notes='A portrait.')
    for i, off in enumerate((512, 1536, 2432)):
        panel(r, 's', offset=off, length=128, height=256, bottom=96, surface=[TAPESTRY, BANNER_A, BANNER_B][i])
    r['ambient'] = 20


torch('deco:torch_portraits_1', 'room:portrait_hall', 'e', 0.5)
torch('deco:torch_portraits_2', 'room:portrait_hall', 'w', 0.5)
spawn('spawn:portrait_hall', 'room:portrait_hall', [-768, -2496], 2, 'b')
spawn('spawn:state_s', 'room:state_s', [0, -1408], 1, 'c')
for k in 'nesw':
    torch(f'deco:torch_state_{k}', f'room:state_{k}', k, 0.2)
    torch(f'deco:torch_state_{k}2', f'room:state_{k}', k, 0.8)
door('door:darzog_hall', 'open:state_hall', **PLANK_DOOR,
     notes="Darzog's doors: a hinged pair of braced plank wings (hhm1d | hhm1d2), 256 by 384 each.")
ev('evt:door_darzog_hall', preset='door', source='door:darzog_hall', title="Darzog's doors")
door('door:bedchamber', 'open:hall_bedchamber', **PLANK_DOOR)
door('door:darzog_study', 'open:hall_study', **PLANK_DOOR)
ev('evt:door_bedchamber', preset='door', source='door:bedchamber', title='Bedchamber door')
ev('evt:door_darzog_study', preset='door', source='door:darzog_study', title='Study door')
torch('deco:torch_lstair', 'room:library_stair', 'e', 0.5)
torch('deco:torch_skystair', 'room:sky_stair', 'w', 0.5)

# ============================================================================================ THE ROOF (3072)
@furn('room:roof_n')
def _(r):
    for i in range(5):
        plat(r, id=None if i < 4 else 'platform:cloud_top', at=[0, 2240 + 128 * i], size=[384, 128], rise=32 * (i + 1),
             surface=CLOUD_SIDE, top_surface=CLOUD_TOP,
             notes='The cloud stair: white steps of cloud climbing toward the sky.' if i == 4 else 'A step of cloud.')
    for p in r['platforms']:
        if 'id' in p and p['id'] is None:
            p.pop('id')


# The cloud's own pale light: the roof's bake leaves the cloud tiles a smoky grey without it (session 7 pictures).
light('light:cloud_stair', 'room:roof_n', [0, 2496], 288, 640, [235, 240, 255])


# A8 session 17 (A3's segment 83 BLOCKER): X9 exists. After m21.crodo (crodo_freed 110501) the top step opens the
# standard entrance window (F16, 2026-11-22: OK moves, Close stays; no Yes/No before it); before, the cloud gives.
ev('evt:cloud_stair', preset='script', trigger='step', source='platform:cloud_top',
   condition={'lua': 'IsQBitSet(QBit(110501))'},
   effects=[{'exit': 'exit:clouds_of_xeen'}],
   else_effects=[{'text': "The cloud gives under your foot like fog. Something holds it shut: Crodo would know what."}],
   notes="set:cloud_stair (m21.cloud_stair reads crodo_freed 110501; the hook has no call): before it the cloud gives "
         "like fog; after it the standard entrance window (F16), OK to X9's entrance:xd12_roof (0, -17920, 320) "
         "facing 512, Close stays.")
ev('evt:roof', preset='text', trigger='step', source='room:roof_n', once=True,
   text='Wind, and the whole of Lake Darzog below. Above the roof a stair of cloud climbs into the sky.')
spawn('spawn:roof_n', 'room:roof_n', [-2048, 2304], 3, 'b')
spawn('spawn:roof_s', 'room:roof_s', [1024, -2304], 3, 'b')

# ============================================================================================ OUTSIDE
TREES = ['7tree01', '6tree03', '6tree07', '6tree09', '7tree16', '6tree17']
n = 0
# D-7 (2026-11-20): the walking lines of each band run from the corner opening (the band's arm end, 3328-3840 out)
# along the keep's wall to its windows, so the trees toward the arm's end stand further out toward the bank's edge
# (3712), each its radius and 64 clear of every line; the three toward the other end stay at 3536.
TREE_OUT = {-2944: 3536, -2176: 3536, -1408: 3536, -640: 3632, 384: 3680, 1024: 3680, 1664: 3712, 2432: 3712}
for k in range(4):
    for t in (-2944, -2176, -1408, -640, 384, 1024, 1664, 2432):
        x, y = t, TREE_OUT[t]
        for _ in range(k):
            x, y = -y, x
        rid = ['room:out_n', 'room:out_w', 'room:out_s', 'room:out_e'][k]
        deco(f'deco:tree_{n:02d}', rid, TREES[n % len(TREES)], [x, y], notes='A tree on the island at the keep\'s foot.')
        n += 1
    for j, t in enumerate((-1792, 1280)):
        x, y = t, (3600, 3712)[j]   # D-7 (2026-11-20): the second rock (106 from a line) to the bank's edge
        for _ in range(k):
            x, y = -y, x
        deco(f'deco:rock_{k}{j}', ['room:out_n', 'room:out_w', 'room:out_s', 'room:out_e'][k], ['6rock01', '6rock05'][j], [x, y])
for k, rid in enumerate(['room:out_n', 'room:out_w', 'room:out_s', 'room:out_e']):
    ev(f'evt:fall_{rid.split("_")[1]}', preset='script', trigger='step', source=rid,
       # Merge point 10 (D-24): `leave` moves at once, so the line goes first (an event's `text` runs after its effects
       # and was lost with the move).
       effects=[{'text': 'You fall from the tower and crash down on the island. Battered, you pick yourselves up by the tower door.'},
                {'leave': 'exit:lake_island'}],
       notes='A fall from the keep (a window or the battlements) lands outside: X2, in front of the tower door.')


# ============================================================================================ PLACED SOUNDS
# Engine sounds (assets_dev/engine/audio). Heard by 3D distance with no occlusion: each sound stands about mid-height
# in its room (the party hears from 160 over its feet), and its inner radius is under 768 (the floors' spacing), so
# the floors above and below hear it only faintly. A wait range on a looping sound plays it once, then waits.
def sound(sid, room, at, name, radius, inner, volume, notes, **kw):
    d = {'id': sid, 'room': room, 'at': at, 'sound': name, 'radius': radius, 'inner_radius': inner, 'volume': volume}
    d.update(kw)
    d['notes'] = notes
    OBJ.setdefault('sounds', []).append(d)


sound('sound:forge_lava', 'room:forge', [0, 2848], 'lava loop', 1500, 640, 0.8, height=256,
      notes="The lava channel along the forge's north wall.")
sound('sound:smelter_pit', 'room:smelter', [2496, 2496], 'lava loop', 1000, 300, 0.5, height=288,
      notes="The smelting pit's lava, quieter than the forge's channel.")
sound('sound:clone_vats', 'room:clone_vats', [2656, -2656], 'bubbling cauldron01', 1000, 350, 0.7, height=160,
      notes='The green brew bubbling in the four clone vats.')
sound('sound:lightning_foot', 'room:well', [0, 0], '7sparks', 1600, 400, 0.8, height=96, wait=[4, 10],
      notes="Darzog's lightning crackling at the rune circle, the Well's foot.")
sound('sound:lightning_high', 'room:well', [0, 0], '7sparks', 1400, 400, 0.7, height=2496, wait=[5, 12],
      notes="Darzog's lightning crackling up the Well, level with Darzog's floor.")
sound('sound:cistern_drip', 'room:cistern', [-768, -2496], 'drip02', 900, 250, 0.5, wait=[3, 9],
      notes='Water dripping into the cistern.')
for rid, at in (('room:roof_n', [-1024, 2176]), ('room:roof_s', [1024, -2176]), ('room:roof_w', [-2176, 0]),
                ('room:roof_e', [1472, 0])):
    sound('sound:wind_' + rid.split('_')[1], rid, at, 'whistling wind', 2000, 800, 0.3, height=256,
          notes='Wind over the roof terrace.')
# The tower's bed (AU's xeen_amb_tower: chimes and sparkle, bright, so quiet): one source on the Well's axis halfway up
# the halls (z about 1500), full within 2560 (the galleries and side rooms of every floor), fading to 5120 (the corner
# rooms, about 4,450 away at most); one source, so nothing stacks.
sound('sound:tower_bed', 'room:well', [0, 0], 'xeen_amb_tower', 5120, 2560, 0.35, height=1472, pan=False,
      notes="The tower's bed: Darzog's magic chiming up the Well, heard faintly through every hall.")

TORCH_KIND = {'theme:gate': 'torch02', 'theme:works': 'torch02', 'theme:darzog': 'torch07', 'theme:library': 'scon100'}
NO_TORCH = {'room:crodo_cell', 'room:sky_stair'}
FLIGHT_WALLS = {('room:west_stair', 3), ('room:library_stair', 3), ('room:east_stair', 1)}


def _blocked(rid, room_dict):
    """Wall stretches that chests and tall blocks against the walls cover (no torch behind a cabinet or a rack)."""
    boxes = []
    for c in OBJ['chests']:
        if c.get('room') != rid:
            continue
        w, dp = (c.get('size') or [96, 64, 64])[:2]
        if c.get('facing') in ('n', 's'):
            w, dp = dp, w
        boxes.append((c['at'][0] - w / 2, c['at'][1] - dp / 2, c['at'][0] + w / 2, c['at'][1] + dp / 2))
    for p in room_dict.get('platforms', []):
        if p.get('rise', 0) >= 128 and 'at' in p and not p.get('base'):
            w, dp = p['size']
            boxes.append((p['at'][0] - w / 2, p['at'][1] - dp / 2, p['at'][0] + w / 2, p['at'][1] + dp / 2))
    out = {}
    o = room_dict['outline']
    for idx in range(len(o)):
        a, b = o[idx], o[(idx + 1) % len(o)]
        k = 0 if a[1] == b[1] else 1
        line = a[1 - k]
        for x0, y0, x1, y1 in boxes:
            lo, hi = (x0, x1) if k == 0 else (y0, y1)
            near = (y0, y1) if k == 0 else (x0, x1)
            if min(abs(near[0] - line), abs(near[1] - line)) > 160:
                continue
            if b[k] > a[k]:
                s, e = lo - a[k], hi - a[k]
            else:
                s, e = a[k] - hi, a[k] - lo
            out.setdefault(idx, []).append((s, e))
    return out


def torch_pass():
    """Wall torches (Castle Gloaming's torch07; candle sconces in the library) on every wall of the tower's rooms at
    about one per 1,280 of wall, clear of doorways, windows and panels; 128 up (the shipped commonest)."""
    n = 0
    for rid in geo.ORDER:
        r = DRESSED.get(rid, geo.ROOMS[rid])
        blocked = _blocked(rid, r)
        kind = TORCH_KIND.get(r['theme'])
        if not kind or rid in NO_TORCH:
            continue
        for idx in range(len(r['outline'])):
            L = geo.edge_len(rid, idx)
            if L < 512 or (rid, idx) in FLIGHT_WALLS:
                continue
            count = max(1, round(L / 1280))
            extra = PANEL_SPANS.get((rid, idx), []) + blocked.get(idx, [])
            for al in geo.free_alongs(rid, idx, count, clear=128, extra=extra):
                d = {'id': f'deco:wall_torch_{n:03d}', 'room': rid, 'decoration': kind, 'wall': idx, 'along': al}
                if r['ceiling'] - r['floor'] > 1000:
                    d['floor_height'] = r['floor']
                OBJ['decorations'].append(d)
                if kind == 'scon100':
                    # the candle sconce has no light of its own: its candles' light, 32 in front of it
                    o = r['outline']
                    a, b = o[idx], o[(idx + 1) % len(o)]
                    px = a[0] + (b[0] - a[0]) * al
                    py = a[1] + (b[1] - a[1]) * al
                    nx, ny = (b[1] - a[1]), -(b[0] - a[0])
                    ln = (nx * nx + ny * ny) ** 0.5
                    px -= nx / ln * 40
                    py -= ny / ln * 40
                    OBJ['lights'].append({'id': f'light:sconce_{n:03d}', 'room': rid, 'at': [round(px), round(py)],
                                          'height': 176, 'radius': 700, 'color': [255, 205, 150],
                                          'notes': 'The candles of the sconce beside it.'})
                n += 1


def write(folder):
    def change(r):
        for fn in FURN.get(r['id'], []):
            fn(r)
        DRESSED[r['id']] = r
        if r.get('floor_surfaces', 1) is None:
            r.pop('floor_surfaces')
    doc = rooms_doc({rid: change for rid in geo.ORDER})
    torch_pass()
    doc['defaults'] = {'theme': 'theme:gate', 'ambient': 16}
    dump(folder / 'rooms.yml', doc)
    objs = copy.deepcopy(OBJ)
    objs.setdefault('movers', OBJ.get('movers', []))
    for k in list(objs):
        if isinstance(objs[k], list) and not objs[k]:
            objs.pop(k)
    objs['notes'] = ("Objects of XD-12 (written by output/studio_cal/xd12/tools/dress.py). Xeen rows: slot 1 Magic "
                     "constructs (every marker tier c, Carnage Hand 35, 11602), slot 2 Wizards (tier a, Wizard 36, "
                     "11190), slot 3 Eyes (tier a, Floating Eye 40, 11570); Baron Darzog 11194 and his six clones "
                     "11195 (boss rows); the Chief Librarian a Sorcerer 11191 with his name; Crodo 11900, peaceful.")
    dump(folder / 'objects.yml', objs)
    dump(folder / 'wiring.yml', {'format': 0, 'variables': VARS, 'events': EVENTS,
                                 'notes': "Wiring of XD-12 (written by output/studio_cal/xd12/tools/dress.py)."})
    dump(folder / 'atmosphere.yml', {
        'format': 0,
        'open_sky': {'mode': 'open', 'preset': 'fair', 'view': 'outdoor', 'view_distance_scale': 1},
        'daylight': {'ambient_rgb': [90, 90, 100], 'sun_rgb': [255, 240, 220]},
        'notes': "The Well, the sky stair, the roof and the island round the keep open to the sky (their sky faces); "
                 "the rest is lit by its own lights."})
