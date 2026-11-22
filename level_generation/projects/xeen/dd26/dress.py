#!/usr/bin/env python3
"""DD-26 Olympus Sewer, L4: objects.yml and wiring.yml (written by gen.py L4)."""
import geo

LESSER, WATER = 11625, 11710
NAME = {LESSER: 'lesser', WATER: 'elemental'}
HOUSE = 4815                      # A4's "Pets Unlimited" (source/towns/dd26.yml), residence, Cyrano Jones 5614

MARBLE_L = [215, 220, 235]        # cold daylight through the city's grates
STONE_L = [160, 175, 190]
DEN_L = [240, 190, 130]
GOLD_L = [245, 205, 120]

ARRIVAL_AT = [0, 0]


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
def doors():
    return [
        {'id': 'door:den', 'opening': 'open:conduit_den', 'kind': 'hinged', 'leaves': 2,
         'pictures': [[dict(geo.PLANK_DOOR), dict(geo.PLANK_DOOR2)]],
         'back_pictures': [[dict(geo.PLANK_DOOR), dict(geo.PLANK_DOOR2)]],
         'notes': "The den's plank door, two leaves (d01's hhm1d and its twin hhm1d2): 'Cyrano sells the password.' (aaze0038:12) is its hover."},
        {'id': 'door:spill_grate', 'opening': 'open:west_spill', 'kind': 'slide_up', 'surface': dict(geo.GRATE, fit=True),
         'notes': "The spillway's grate: iron bars that lift."},
        {'id': 'door:outfall_grate', 'opening': 'open:east_outfall', 'kind': 'slide_up',
         'surface': dict(geo.GRATE, fit=True), 'notes': "The outfall's grate: iron bars that lift."},
        {'id': 'door:tribble', 'opening': 'open:tdoor_vault', 'kind': 'hinged', 'leaves': 2, 'thickness': 24,
         'edge_surface': dict(geo.GILT),
         'pictures': [[dict(geo.LEAF_L), dict(geo.LEAF_R)]], 'back_pictures': [[dict(geo.LEAF_L), dict(geo.LEAF_R)]],
         'notes': "The tribble door: two riveted bronze leaves (gcs05a | gcs05b, the right the left's twin) under the marble lintel, opening apart into the vault; the password opens them for good (117805)."},
    ]


CHEST_LOOK = {'kind': '7gt002'}


def chests():
    return [dict(c, **CHEST_LOOK) for c in [
        {'id': 'chest:spill', 'room': R('spill'), 'at': geo.WEIR[0], 'floor_height': geo.WEIR[2], 'treasure_level': 6, 'random_items': 3, 'gold': 4000,
         'notes': "On the weir's dry ledge (T6)."},
        {'id': 'chest:vault', 'room': R('vault'), 'at': geo.VAULT_LEDGE[0], 'floor_height': geo.VAULT_LEDGE[2],
         'treasure_level': 6, 'random_items': 4, 'gold': 6000,
         'notes': "The offerings' chest on the vault's ledge (T6), the map's goal."},
    ]]


# room: [(row, at, group)]
PLACED = {
    'conduit': [(LESSER, [-1150, 320], 1), (LESSER, [-950, 704], 1), (LESSER, [-1400, 704], 1)],
    'west': [(LESSER, [-2080, 704], 2), (LESSER, [-2080, 1408], 2), (LESSER, [-2080, 1664], 2)],
    'spill': [(LESSER, [-2620, 896], 3), (LESSER, [-2600, 1184], 3)],
    'cistern': [(WATER, [-640, 2848], 4), (WATER, [640, 2848], 4), (LESSER, [-2048, 2560], 5),
                (LESSER, [-1920, 2816], 5)],
    'east': [(LESSER, [2080, 704], 6), (LESSER, [2080, 1408], 6), (LESSER, [2080, 1664], 6)],
    'outfall': [(LESSER, [2620, 896], 7), (LESSER, [2600, 1184], 7)],
    'vault': [(WATER, [3712, 2304], 8), (WATER, [3712, 2816], 8), (LESSER, [3968, 2560], 8)],
}


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at, g in lst:
            n[row] = n.get(row, 0) + 1
            out.append({'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                        'facing': 90, 'group': g})
    return out


# MM7's empty hanging cage (7dec05; 7dec06/07 hold a skeleton and a prisoner): each hangs from the den's vault by its
# ring, over the counter and along the west wall.
CAGE_HANG = None    # the build hangs a cage from the vault when it has no height
# (key, decoration, room, at, floor height or None, facing or None)
PROPS = [
    # tribble cages on the counter and by the den's walls
    ('cage_counter_1', '7dec05', 'den', [-480, 1800], CAGE_HANG, None),
    ('cage_counter_2', '7dec05', 'den', [-320, 1800], CAGE_HANG, None),
    ('cage_counter_3', '7dec05', 'den', [400, 1800], CAGE_HANG, None),
    ('cage_west_1', '7dec05', 'den', [-576, 1280], None, None),
    ('cage_west_2', '7dec05', 'den', [-576, 1472], None, None),
    ('den_bowl', 'foodbowl', 'den', [-448, 1056], None, None),
    # the offering vault: cups, coin, a gilt statue, a vase, by the walls
    ('vault_statue', '7dec55', 'vault', [3456, 2976], None, 270),
    ('vault_cup_1', '7dec46', 'vault', [3328, 2128], None, None),
    ('vault_cup_2', '7dec48', 'vault', [3424, 2120], None, None),
    ('vault_cup_3', '7dec46', 'vault', [4096, 2992], None, None),
    ('vault_coin_1', 'bag01', 'vault', [4256, 2144], None, None),
    ('vault_coin_2', 'bag_A', 'vault', [4256, 2976], None, None),
    ('vault_vase', 'dec97', 'vault', [3904, 2992], None, None),
]
# (room, wall, along, decoration)
SCONCES = [
    ('stair', 'e', 0.75, 'scon100'), ('stair', 'w', 0.75, 'scon100'),
    ('conduit', 's', 0.25, 'scon100'), ('conduit', 's', 0.75, 'scon100'),
    ('conduit', 'n', 0.2, 'scon100'), ('conduit', 'n', 0.8, 'scon100'),
    ('den', 'w', 0.85, 'scon100'), ('den', 'e', 0.15, 'scon100'),
    ('west', 'e', 0.75, 'scon100'), ('east', 'w', 0.25, 'scon100'),
    ('spill', 'e', 0.2, 'scon100'), ('outfall', 'w', 0.8, 'scon100'),
    ('cistern', 'n', 0.25, 'scon100'), ('cistern', 'n', 0.75, 'scon100'),
    ('cistern', 's', 0.3, 'scon100'), ('cistern', 's', 0.7, 'scon100'),
    ('tdoor', 'n', 0.5, 'scon100'), ('tdoor', 's', 0.5, 'scon100'),
    ('vault', 'n', 0.6, 'scon200'), ('vault', 's', 0.6, 'scon200'),
]


def decorations():
    out = []
    for key, dec, room, at, fh, facing in PROPS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at}
        if fh is not None:
            d['height'] = fh
        if facing is not None:
            d['facing'] = facing
        if key.startswith('cage'):
            d['notes'] = "A tribble cage hung from the den's vault (MM7's empty cage 7dec05)." 
        if key == 'vault_statue':
            d['notes'] = "The gilt statue by the north wall (MM7's statue 7dec55; the graph's toppled statue stands: no decoration lies on its side)."
        out.append(d)
    for i, (room, wall, along, dec) in enumerate(SCONCES):
        out.append({'id': f'deco:sconce_{i}', 'room': R(room), 'decoration': dec, 'wall': wall, 'along': along,
                    'height': 192})
    return out


THEME_COL = {'theme:marble': MARBLE_L, 'theme:culvert': STONE_L, 'theme:den': DEN_L, 'theme:temple': GOLD_L}


def lights():
    L = []

    def add(room, at, radius, color, height=None, notes=None):
        d = {'id': f'light:{room}_{sum(1 for x in L if x["room"] == R(room)) + 1}', 'room': R(room), 'at': at,
             'radius': radius, 'color': color}
        if height:
            d['height'] = height
        if notes:
            d['notes'] = notes
        L.append(d)
    for room in geo.ORDER:
        (w, h), c = geo.extent(room)
        col = THEME_COL[geo.R[room][4]]
        r = int(min(1600, max(700, 0.6 * max(w, h))))
        if max(w, h) > 1600:
            ax = 0 if w >= h else 1
            n = 3 if max(w, h) > 3000 else 2
            for k in range(n):
                f = (k + 0.5) / n
                p = list(c)
                lo = c[ax] - (w if ax == 0 else h) / 2
                p[ax] = int(lo + f * (w if ax == 0 else h))
                add(room, p, int(r * 0.8), col)
        else:
            add(room, c, r, col)
    add('vault', [4224, 2560], 600, GOLD_L, height=160, notes="The gold's glow round the offerings' chest.")
    return L


def sounds():
    return [
        {'id': 'sound:bed_conduit', 'room': R('conduit'), 'at': [0, 512], 'sound': 'xeen_amb_sewer',
         'radius': 2800, 'inner_radius': 900, 'volume': 0.35, 'pan': False,
         'notes': "The sewer's bed over the conduit, the stair and the culverts' south ends (D-48: not panned)."},
        {'id': 'sound:bed_cistern', 'room': R('cistern'), 'at': [0, 2496], 'sound': 'xeen_amb_sewer',
         'radius': 2800, 'inner_radius': 900, 'volume': 0.35, 'pan': False,
         'notes': "The bed over the cistern and the culverts' north ends (not panned)."},
        {'id': 'sound:conduit_water_w', 'room': R('conduit'), 'at': [-896, 512], 'sound': 'rushing water loop',
         'radius': 1200, 'inner_radius': 300, 'volume': 0.25, 'notes': "The conduit's water, west run."},
        {'id': 'sound:conduit_water_e', 'room': R('conduit'), 'at': [896, 512], 'sound': 'rushing water loop',
         'radius': 1200, 'inner_radius': 300, 'volume': 0.25, 'notes': "The conduit's water, east run."},
        {'id': 'sound:basin', 'room': R('cistern'), 'at': [0, 2496], 'sound': 'water lapping loop',
         'radius': 1600, 'inner_radius': 400, 'volume': 0.35, 'notes': "The cistern's clear water."},
        {'id': 'sound:cistern_drip', 'room': R('cistern'), 'at': [-1024, 2848], 'sound': 'drip03', 'radius': 1400,
         'inner_radius': 300, 'volume': 0.3, 'wait': [4, 10], 'notes': "The cistern's deeper drip from the vault."},
        {'id': 'sound:outfall', 'room': R('outfall'), 'at': [2992, 1088], 'sound': 'waterfall loop1',
         'radius': 1100, 'inner_radius': 250, 'volume': 0.3, 'notes': "The water falling away through the barred mouth."},
        {'id': 'sound:tribbles', 'room': R('den'), 'at': [0, 1700], 'height': 160, 'sound': 'xeen_tribble_purr',
         'radius': 1000, 'inner_radius': 300, 'volume': 0.45, 'notes': "The tribbles purring in the den's cages (AU)."},
    ]


def exits():
    return [
        {'id': 'exit:grate', 'room': R('stair'), 'at': [0, -1216], 'floor_height': geo.STAIR_TOP,
         'size': [160, 320], 'surface': dict(geo.GRATE, fit=True), 'to': 'exit:d7_stair',
         'notes': "The grate at the stair's top, its bars rising into the shaft: up to Olympus (D7's entrance:dd26_stair)."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('stair'), 'at': ARRIVAL_AT, 'facing': 'n',
                  'notes': "The marble stair's foot, facing north into the conduit."},
        'arrivals': [
            {'entrance': 'entrance:d7_stair', 'room': R('stair'), 'at': ARRIVAL_AT, 'facing': 'n',
             'notes': "From D7's marble grate in the gods' row (door:dd26, A6): 'Descend into the sewer?' (aaze0037:1)."},
        ],
        'doors': doors(), 'chests': chests(), 'monsters': monsters(),
        'decorations': decorations(), 'lights': lights(), 'sounds': sounds(), 'exits': exits(),
        'notes': "DD-26's contents, written by output/studio_cal/dd26/tools/dress.py: 4 doors (the den's plank pair, the spillway's and the outfall's grates, the tribble door's bronze pair), 2 chests (T6), 20 placed monsters (Lesser Water Elemental 11625 x16, Water Elemental 11710 x4, one faction); Cyrano's counter door is a wall panel (rooms.yml door:pets_unlimited, house 4815); the grate at the stair's top is the exit face.",
    }


# ------------------------------------------------------------------------------------------------- wiring
DRAINS = [
    # (key, panel, qbit, piece line)
    ('drain_tr', 'panel:drain_1', "You find a piece of a note that reads: TR"),
    ('drain_ib', 'panel:drain_2', "You find a piece of a note that reads: IB"),
    ('drain_bl', 'panel:drain_3', "You find a piece of a note that reads: BL"),
    ('drain_es', 'panel:drain_4', "You find a piece of a note that reads: ES"),
]


TRIBBLE_LUA = "\n".join([
    'if Xeen.tribbleDoor(eventId, continueStep) then',
    '    evt.SetDoorState(%d, DoorAction.Open)' % 5,
    '    evt.SetDoorState(%d, DoorAction.Open)' % 6,
    'end',
])


def hook(name):
    return {'lua': f'XeenQuests.hook("q-d28.{name}")'}


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'dd26_arrived_once'}}, 'effects': [hook('arrival')],
              'notes': "The first arrival: A3's q-d28.arrival (once: arrived_once 117800 and its line). The stair holds no monsters (D-11.3)."})
    E.append({'id': 'evt:exit', 'preset': 'script', 'source': 'exit:grate', 'title': 'Climb up to Olympus',
              'effects': [{'exit': 'exit:d7_stair'}],
              'notes': "The grate at the stair's top (D-67 item 8; F16 2026-11-22: the standard MM6-MM8 entrance window, OK/Close, no Yes/No): OK moves to D7's entrance:dd26_stair (-8704, 8192, 1808) facing 0, Close stays."})
    E.append({'id': 'evt:scroll', 'preset': 'script', 'source': 'panel:scroll', 'title': 'Scroll',
              'effects': [hook('scroll')],
              'notes': "D-65 change 1: hover 'Scroll' (aaze0038:10); A3's q-d28.scroll: 'Search the drains.' (:11)."})
    E.append({'id': 'evt:den_door', 'preset': 'door', 'source': 'door:den', 'title': 'Cyrano sells the password.',
              'notes': "The den's door: its hover is the source's line on it (aaze0038:12; map-local, A3 has no hook for it)."})
    E.append({'id': 'evt:pets_unlimited', 'preset': 'script', 'source': 'door:pets_unlimited',
              'title': 'Pets Unlimited', 'effects': [{'lua': f'evt.EnterHouse({HOUSE})'}],
              'notes': f"A4's house {HOUSE} 'Pets Unlimited' (aaze0038:19; source/towns/dd26.yml door:pets_unlimited): Cyrano Jones (5614), a residence; his topics are A3's (q-d28: Tribbles, Companions)."})
    E.append({'id': 'evt:bed', 'preset': 'script', 'source': 'platform:bed', 'title': 'Bed', 'effects': [hook('bed')],
              'notes': "The bed (aaze0038:16): A3's q-d28.bed (once: one random T6 item, bed 117806; then 'Nothing here.', :17)."})
    for key, panel, line in DRAINS:
        E.append({'id': f'evt:{key}', 'preset': 'script', 'source': panel, 'title': 'Drain', 'effects': [hook(key)],
                  'notes': f"A drain (aaze0038:0): A3's q-d28.{key} (its piece once, map qbit {QB[key]}; the fourth also writes the autonote; then 'Drain' on the status line)."})
    E.append({'id': 'evt:tribble_door', 'preset': 'script', 'source': 'door:tribble', 'side': 'room:tdoor',
              'title': 'Bronze doors', 'lua': TRIBBLE_LUA,
              'notes': "D-65 change 2 (B1): A3's Xeen.tribbleDoor asks the voice (aaze0038:5) as the typed prompt's own text, no message before it; 'tribbles' or 'tribble' in any case runs q-d28.tribble_door (door_open 117805, 'Correct! You may pass.') and the leaves open for good; any other answer q-d28.tribble_wrong ('Wrong! You may not pass!'). Once open it asks nothing (the leaves stay open). Doors 5 and 6 are the pair's leaves (ids.lock.yml)."})
    E.append({'id': 'evt:tribble_back', 'preset': 'switch', 'source': 'door:tribble', 'side': 'room:vault',
              'title': 'Bronze doors', 'opens': ['door:tribble'],
              'notes': "From the vault the bronze pair opens (never shuts the party in)."})
    E.append({'id': 'evt:tribble_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'tribble_door'},
              'opens': ['door:tribble'],
              'notes': "Every load: the bronze pair stands open once the password was given (117805), also after a refill."})
    E.append({'id': 'evt:voice', 'preset': 'text', 'source': 'panel:voice', 'title': 'Grille', 'window': False,
              'text': 'A voice waits behind the grille.',
              'notes': "The grille mouth over the bronze pair (map-local line, for A3)."})
    E.append({'id': 'evt:spill_grate', 'preset': 'door', 'source': 'door:spill_grate', 'title': 'Grate'})
    E.append({'id': 'evt:outfall_grate', 'preset': 'door', 'source': 'door:outfall_grate', 'title': 'Grate'})
    for c in ('spill', 'vault'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    return E


QB = {
    'drain_tr': 117801, 'drain_ib': 117802, 'drain_bl': 117803, 'drain_es': 117804,
}


def wiring():
    return {'format': 0, 'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-26's events, written by output/studio_cal/dd26/tools/dress.py."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
