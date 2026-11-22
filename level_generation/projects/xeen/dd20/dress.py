#!/usr/bin/env python3
"""DD-20 Lakeside Coven and Sewer, L4: objects.yml, wiring.yml (written by gen.py L4)."""
import geo

WITCH, COVEN_WITCH, HEAD_WITCH, STALKER, MATRIARCH = 11170, 11171, 11173, 11401, 11402
NAME = {WITCH: 'witch', COVEN_WITCH: 'coven_witch', STALKER: 'stalker', MATRIARCH: 'matriarch'}
# A2's named peaceful rows (source/monsters.yml `characters`), each its own friendly faction, move: stand.
PRISONER_ROW = {'camilla': 11906, 'aretha': 11907, 'isabella': 11908, 'rhett': 11909}
PRISONER_NAME = {'camilla': 'Camilla the Captured', 'aretha': 'Aretha the Helpless', 'isabella': 'Isabella the Victim',
                 'rhett': 'Rhett the Wimp'}
PRISONER_GROUP = {'camilla': 20, 'aretha': 21, 'isabella': 22, 'rhett': 23}
FREED = {'camilla': 113443, 'aretha': 113444, 'isabella': 113445, 'rhett': 113446}
COVEN_GROUP, HEAD_GROUP, SEWER_GROUP, AMBUSH_GROUP = 1, 5, 2, 6

CANDLE = [235, 175, 115]
COVENL = [220, 165, 120]
CELLL = [150, 165, 150]
SEWERL = [130, 150, 140]
DAY = [205, 215, 225]
LAKE = [150, 190, 215]


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
DOORS = [
    # id, opening, surface, notes
    ('hall_walk', 'open:hall_walk', None, "The Moon seal's double doors from the coven hall to the witches' walk: two hinged leaves, the seal's four quarters (t1d1a-d)."),
    ('walk_ante', 'open:walk_ante', geo.TEMPLEDOOR, "A temple door from the walk into the antechamber."),
    ('ante_head', 'open:ante_head', geo.TEMPLEDOOR, "The Head Witch's door from the antechamber."),
    ('walk_brewery', 'open:walk_brewery', geo.TEMPLEDOOR, "A temple door from the walk into the brewery."),
    ('brewery_head', 'open:brewery_head', geo.TEMPLEDOOR, "Her private door between the brewery and her room."),
    ('hall_dorm', 'open:hall_dorm', geo.TEMPLEDOOR, "A temple door from the hall into the dormitory."),
    ('hall_gaol', 'open:hall_gaol', geo.TEMPLEDOOR, "A temple door from the hall into the gaoler's room."),
    ('dorm_store', 'open:dorm_store', geo.TEMPLEDOOR, "A temple door from the dormitory into the store."),
    ('main_pump', 'open:main_pump', geo.SEWERDOOR, "The skull-ring door from the main drain into the old pump room."),
]


def doors():
    out = []
    for k, op, s, n in DOORS:
        if k == 'hall_walk':
            out.append({'id': f'door:{k}', 'opening': op, 'kind': 'hinged', 'leaves': 2,
                        'pictures': [list(map(dict, r)) for r in geo.SEAL], 'notes': n})
        else:
            out.append({'id': f'door:{k}', 'opening': op, 'kind': 'slide_up', 'surface': dict(s, fit=True), 'notes': n})
    return out


def gate(key):
    return {'id': f'mover:cage_{key}', 'room': R('cells'), 'at': [geo.CAGES[key], geo.CAGE_FRONT_Y], 'size': [368, 8],
            'bottom': 0, 'height': 256, 'travel': [0, 0, -248], 'speed': 160, 'surface': dict(geo.GRILLE),
            'top_surface': dict(geo.IRON, scale=3),
            'notes': f"{PRISONER_NAME[key]}'s cage front: sinks into the floor once q-d22.{key} has freed her or him."}


def movers():
    return [gate(k) for k in geo.CAGES] + [
        {'id': 'mover:hatch', 'room': R('store'), 'at': geo.HATCH_AT, 'size': [256, 256], 'floor_height': 0,
         'bottom': 0, 'height': 8, 'travel': [0, 240, 0], 'speed': 160, 'surface': dict(geo.HATCH),
         'top_surface': dict(geo.HATCH),
         'notes': "The store's floor hatch over the cistern; the bolt beside it slides it aside."}]


def switches():
    return [{'id': 'switch:hatch_bolt', 'room': R('store'), 'kind': 'lever', 'at': [2432, geo.HATCH_AT[1]], 'reach': 48,
             'notes': "The hatch's bolt on the store's east wall beside the hatch."}]


def ladders():
    return [{'id': 'ladder:cistern', 'room': R('cistern'), 'at': [geo.HATCH_AT[0] - 72, geo.HATCH_AT[1]], 'facing': 'w',
             'height': -geo.SEWER, 'exit': [geo.HATCH_AT[0] - 240, geo.HATCH_AT[1]], 'grab_at_top': True,
             'surface': geo.S_('bemv', 32, 256, uneven=True),
             'notes': "A wooden ladder from the cistern up through the store's floor hatch."}]


def items():
    # D-90 (c, 2026-11-22): the Golden Dragon lies in the alcove as a 3D ground item (was a click on the alcove panel
    # that gave it through q-d20.dragon); A3's hook becomes `map_gives`.
    return [{'id': 'item:golden_dragon', 'room': R('niche'), 'item': 'golden_dragon', 'at': [15680, 1856],
             'floor_height': geo.SEWER, 'notes': "The Golden Dragon at the alcove's foot (Q-D20)."}]


def chests():
    return [
        {'id': 'chest:witch', 'room': R('head_witch'), 'at': [-3904, 4352], 'facing': 's', 'treasure_level': 5,
         'random_items': 3, 'gold': 2500, 'items': [12336],
         'notes': "The Head Witch's chest at her bed's foot (the hoard) with the Necropolis pass 12336, an ordinary chest item (F15, 2026-11-21: quest items are looted, MM6-MM8 style); q-d22.witch_chest sets pass_found on its first opening."},
        {'id': 'chest:dorm', 'room': R('dormitory'), 'at': [2944, 128], 'facing': 'w', 'treasure_level': 4,
         'random_items': 2, 'gold': 600, 'notes': "The senior witch's chest by her bed."},
        {'id': 'chest:gaol', 'room': R('gaol'), 'at': [2496, 1792], 'treasure_level': 4,
         'random_items': 2, 'gold': 400, 'notes': "The prisoners' confiscated things."},
        {'id': 'chest:pump', 'room': R('pump_room'), 'at': [5888, -1856], 'treasure_level': 4,
         'random_items': 2, 'gold': 500, 'notes': "Left by whoever last hid here."},
        {'id': 'chest:warren', 'room': R('warren'), 'at': [11776, 1216], 'facing': 'w', 'treasure_level': 4,
         'random_items': 2, 'gold': 700, 'notes': "Half-sunk in the stalkers' midden: things washed down the drains."},
    ]


# (row, at, group, hidden)
PLACED = {
    'coven_hall': [(WITCH, [0, 1408]), (WITCH, [-1152, 1280])],
    'witches_walk': [(WITCH, [-1920, 2368]), (WITCH, [-1152, 2432]), (COVEN_WITCH, [-2560, 2368])],
    'antechamber': [(COVEN_WITCH, [-3072, 3136]), (COVEN_WITCH, [-2688, 3136])],
    'brewery': [(WITCH, [-1024, 3456]), (WITCH, [-256, 3328]), (WITCH, [256, 3584])],
    'dormitory': [(WITCH, [1664, 0]), (WITCH, [2560, 64]), (WITCH, [2112, -320])],
    'gaol': [(WITCH, [1664, 1152]), (WITCH, [2304, 1216])],
    'slop_pit': [(STALKER, [9408, 1408]), (STALKER, [9792, 1152])],
    'cross': [(STALKER, [9024, 0]), (STALKER, [9984, -320]), (STALKER, [9472, 384])],
    'main_drain': [(STALKER, [5120, -576]), (STALKER, [6912, -576]), (STALKER, [7936, -576])],
    'cistern': [(STALKER, [1280, -2304]), (STALKER, [2816, -1408])],
    'warren': [(STALKER, [10880, 1024]), (STALKER, [11520, 1280]), (STALKER, [11648, 640]), (STALKER, [11008, 448]),
               (MATRIARCH, [11392, 896])],
    'east_drain': [(STALKER, [11264, -1024]), (STALKER, [12672, -1024])],
    'outfall': [(STALKER, [12672, 1920]), (STALKER, [13568, 2048]), (STALKER, [14592, 768]), (STALKER, [12544, -128]),
                (MATRIARCH, [13824, -256])],
}
# D-18 (D-42 (7)): five of the cross's eight climb out of the side drains on the first step.
AMBUSH = [(STALKER, [8832, -832]), (STALKER, [10112, -832]), (STALKER, [8832, 448]), (STALKER, [10112, 448]),
          (MATRIARCH, [9472, -832])]
HEAD_ROOM = [(COVEN_WITCH, [-2752, 4224]), (WITCH, [-3456, 4160])]


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at in lst:
            n[row] = n.get(row, 0) + 1
            out.append({'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                        'facing': 270, 'group': COVEN_GROUP if row in (WITCH, COVEN_WITCH) else SEWER_GROUP})
    out.append({'id': 'monster:head_witch', 'room': R('head_witch'), 'monster': HEAD_WITCH, 'at': [-3200, 4608],
                'facing': 270, 'group': HEAD_GROUP,
                'notes': "The Head Witch (coven boss row 11173, 45, her own skin): q-d22.head_witch at her death. Her group of three (group 5)."})
    n = {}
    for row, at in HEAD_ROOM:
        n[row] = n.get(row, 0) + 1
        out.append({'id': f'monster:head_witch_{NAME[row]}_{n[row]}', 'room': R('head_witch'), 'monster': row, 'at': at,
                    'facing': 270, 'group': HEAD_GROUP})
    n = {}
    for row, at in AMBUSH:
        n[row] = n.get(row, 0) + 1
        out.append({'id': f'monster:ambush_{NAME[row]}_{n[row]}', 'room': R('cross'), 'monster': row, 'at': at,
                    'facing': 90, 'group': AMBUSH_GROUP, 'hidden': True,
                    'notes': "The cross's ambush (D-18, D-42 (7)): placed hidden, shown on the first step onto the cross."})
    for key, x in geo.CAGES.items():
        out.append({'id': f'monster:{key}', 'room': R('cells'), 'monster': PRISONER_ROW[key], 'at': [x, geo.CAGE_Y],
                    'facing': 270, 'hostile': False, 'immobile': True, 'group': PRISONER_GROUP[key],
                    'notes': f"{PRISONER_NAME[key]} (row {PRISONER_ROW[key]}, her or his own friendly faction) in the cage; hidden by its freed bit ({FREED[key]}) at once and on load. Not counted."})
    return out


# key: (decoration, room, at, floor height or None, title)
DECOS = [
    ('init_cauldron', 'cauld00', 'coven_hall', geo.INIT_CAULDRON, 24, 'Initiation cauldron'),
    ('sump_bones', '7dec18', 'sump', [3328, 192], None, 'Bones'),
    ('hideout_bones', '7dec18', 'hideout', [9408, -1984], None, 'Bones'),
    ('niche_bones', '7dec18', 'niche', [15232, 1856], None, 'Bones'),
] + [(f'cauldron_{k}', 'cauld00', 'brewery', [x, geo.CAULDRON_Y], 24, 'Cauldron') for k, x in geo.CAULDRONS.items()] \
  + [(f'skull_{k}', '7dec20', 'brewery', [x + 256, 4272], 96, 'Skull') for k, x in geo.CAULDRONS.items()]
PROPS = [
    # (key, decoration, room, at, floor height, hangs)
    ('hall_chandelier', 'chndlir0', 'coven_hall', geo.INIT_CAULDRON, None, True),
    ('brazier_w', 'flamb00', 'coven_hall', [-1088, 1760], None, False),
    ('brazier_e', 'flamb00', 'coven_hall', [-192, 1760], None, False),
    ('witch_candle_1', 'cndlab0', 'head_witch', [-2688, 5120], 96, False),
    ('witch_candle_2', 'cndlab0', 'head_witch', [-2432, 5120], 96, False),
    ('store_barrel_1', 'bigbarel', 'store', [1280, -2176], None, False),
    ('store_barrel_2', 'bigbarel', 'store', [1408, -2176], None, False),
    ('store_keg_1', 'smlbarel', 'store', [1280, -1408], None, False),
    ('store_sack_1', 'floursac', 'store', [1664, -2176], None, False),
    ('store_sack_2', 'floursac', 'store', [1280, -1664], None, False),
    ('store_sack_3', 'bag01', 'store', [1280, -1920], None, False),
    ('slop_heap_1', 'trasheap', 'slop_pit', [9344, 1600], None, False),
    ('slop_heap_2', '7dec01', 'slop_pit', [9920, 960], None, False),
    ('warren_heap', '7dec10', 'warren', [11520, 1408], None, False),
    ('warren_bones', 'dec19', 'warren', [10752, 1344], None, False),
    ('pump_bucket', 'Bucket', 'pump_room', [6592, -1856], None, False),
]
# (room, wall, along, decoration, height)
SCONCES = [('coven_hall', 'w', 0.2, 'scon100'), ('coven_hall', 'e', 0.75, 'scon100'), ('witches_walk', 'n', 0.25, 'scon100'),
           ('witches_walk', 's', 0.45, 'scon100'), ('witches_walk', 's', 0.85, 'scon100'), ('antechamber', 'n', 0.12, 'scon100'),
           ('antechamber', 'n', 0.88, 'scon100'), ('head_witch', 'e', 0.75, 'scon100'), ('head_witch', 's', 0.75, 'scon100'),
           ('brewery', 'e', 0.5, 'scon100'), ('brewery', 's', 0.3, 'scon100'), ('dormitory', 'e', 0.25, 'scon100'),
           ('dormitory', 'n', 0.5, 'scon100'), ('gaol', 'w', 0.8, 'scon100'), ('store', 'n', 0.8, 'scon100'),
           ('guild_landing', 'w', 0.5, 'scon100'),
           ('cells', 's', 0.2, 'torch02'), ('cells', 's', 0.5, 'torch02'), ('cells', 's', 0.8, 'torch02'),
           ('jetty_shaft', 'w', 0.3, 'torch01'), ('pump_room', 'n', 0.25, 'torch01'), ('slop_pit', 'e', 0.5, 'torch01')]


def decorations():
    out = []
    for key, dec, room, at, fh, title in DECOS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at, 'notes': f"{title} (clicked: evt:{key})."}
        if fh is not None:
            d['floor_height'] = fh
        out.append(d)
    for key, dec, room, at, fh, hangs in PROPS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at}
        if fh is not None:
            d['floor_height'] = fh
        if hangs:
            d['hangs'] = True
        out.append(d)
    for i, (room, wall, along, dec) in enumerate(SCONCES):
        out.append({'id': f'deco:sconce_{i}', 'room': R(room), 'decoration': dec, 'wall': wall, 'along': along,
                    'height': 192})
    return out


THEME_COL = {'theme:guild': CANDLE, 'theme:coven': COVENL, 'theme:head': CANDLE, 'theme:store': COVENL,
             'theme:cells': CELLL, 'theme:drain': SEWERL, 'theme:sewer': SEWERL, 'theme:cave': SEWERL,
             'theme:outfall': LAKE}
DIM = {'sump': 0.6, 'cistern': 0.6, 'niche': 0.6}


def lights():
    L = []

    def add(room, at, radius, color, height=None, pulse=None, notes=None):
        d = {'id': f'light:{room}_{sum(1 for x in L if x["room"] == R(room)) + 1}', 'room': R(room), 'at': at,
             'radius': radius, 'color': color}
        if height:
            d['height'] = height
        if pulse:
            d['pulse'] = pulse
        if notes:
            d['notes'] = notes
        L.append(d)
    for room in list(geo.R) + list(geo.P):
        (w, h), c = geo.extent(room)
        col = THEME_COL[geo.R[room][4] if room in geo.R else geo.P[room][5]]
        if room in geo.P:
            pts = geo.P[room][1]
            a, b = pts[0], pts[-1]
            add(room, [(a[0] + b[0]) // 2, (a[1] + b[1]) // 2], 1000, col, height=224)
            continue
        r = int(min(2000, max(700, 0.6 * max(w, h))) * DIM.get(room, 1))
        if max(w, h) > 2400:
            ax = 0 if w >= h else 1
            for f in (0.25, 0.75):
                p = list(c)
                lo = c[ax] - (w if ax == 0 else h) / 2
                p[ax] = int(lo + f * (w if ax == 0 else h))
                add(room, p, int(r * 0.75), col)
        else:
            add(room, c, r, col)
    add('main_drain', [6528, -384], 700, DAY, height=380, notes="Daylight through the street grate.")
    add('cross', [9472, -128], 800, DAY, height=500, notes="Daylight through the street grate.")
    add('hideout', [9600, -1664], 600, DAY, height=330, notes="The hideout's grate.")
    add('jetty_shaft', [14208, -1152], 700, DAY, height=800, notes="Daylight down the jetty shaft.")
    add('outfall', [13568, 2048], 1200, LAKE, height=300, notes="Pale lake light through the bars.")
    add('coven_hall', [-128, -320], 600, [240, 150, 80], height=96, notes="The initiation cauldron's fire.",
        pulse={'intensity': [0.75, 1.0], 'radius': [560, 640], 'frequency': 0.8})
    add('brewery', [-640, 4032], 900, [240, 150, 80], height=96, notes="The brewing fires.",
        pulse={'intensity': [0.75, 1.0], 'radius': [840, 960], 'frequency': 0.7})
    return L


def sounds():
    return [
        {'id': 'sound:hall_cauldron', 'room': R('coven_hall'), 'at': geo.INIT_CAULDRON, 'sound': 'bubbling cauldron01',
         'radius': 1100, 'inner_radius': 200, 'volume': 0.45, 'notes': "The initiation cauldron on the boil."},
        {'id': 'sound:brewery', 'room': R('brewery'), 'at': [-640, 4032], 'sound': 'bubbling cauldron01', 'radius': 1500,
         'inner_radius': 400, 'volume': 0.5, 'notes': "Three cauldrons at work."},
        {'id': 'sound:cells', 'room': R('cells'), 'at': [5952, 1152], 'sound': 'drip02', 'radius': 1800,
         'inner_radius': 400, 'volume': 0.45, 'wait': [2, 6], 'notes': "Water dripping in the cells."},
        {'id': 'sound:main_drain', 'room': R('main_drain'), 'at': [6336, -160], 'sound': 'water lapping loop',
         'radius': 1800, 'inner_radius': 500, 'volume': 0.3, 'notes': "The drain's slow water."},
        {'id': 'sound:cross', 'room': R('cross'), 'at': [9472, -192], 'sound': 'drip03', 'radius': 1500,
         'inner_radius': 300, 'volume': 0.5, 'wait': [2, 7], 'notes': "Drips from the street grate."},
        {'id': 'sound:cistern', 'room': R('cistern'), 'at': [2048, -2304], 'sound': 'drip02', 'radius': 1500,
         'inner_radius': 300, 'volume': 0.5, 'wait': [3, 8], 'notes': "The still cistern dripping."},
        {'id': 'sound:east_drain', 'room': R('east_drain'), 'at': [12032, -1472], 'sound': 'water lapping loop',
         'radius': 1800, 'inner_radius': 500, 'volume': 0.3, 'notes': "The east drain's water."},
        {'id': 'sound:outfall', 'room': R('outfall'), 'at': [13568, 896], 'sound': 'water lapping loop', 'radius': 2200,
         'inner_radius': 700, 'volume': 0.5, 'notes': "The tidal pool and the lake beyond the bars."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('coven_hall'), 'at': [-640, -384], 'facing': 'n',
                  'notes': "At the foot of the Guild's back stair, facing the Moon seal's double doors (D4's cellar hatch arrives here: entrance:d4_guild)."},
        'arrivals': [
            {'entrance': 'entrance:d4_trapdoor', 'room': R('sump'), 'at': [3456, -640], 'facing': 'e',
             'notes': "Under the trapdoor in the sump, facing the main drain (D4's q-d22.guild_wrong drops the party here)."},
            {'entrance': 'entrance:d4_shaft', 'room': R('jetty_shaft'), 'at': [14208, -1152], 'facing': 'w',
             'notes': "At the jetty shaft's ladder foot, facing the east drain (D4's door:dd20_sewer arrives here)."},
        ],
        'doors': doors(), 'movers': movers(), 'switches': switches(), 'ladders': ladders(), 'chests': chests(),
        'items': items(),
        'monsters': monsters(), 'decorations': decorations(), 'lights': lights(), 'sounds': sounds(),
        'exits': [
            {'id': 'exit:guild', 'room': R('guild_landing'), 'wall': 'south', 'size': [160, 320],
             'surface': geo.S_('7solid01', 128, 256, fit=True), 'to': 'exit:d4_guild',
             'notes': "The cellar door at the top of the Guild's back stair, out beside the Guild's west-wall hatch (D4)."},
            {'id': 'exit:shaft', 'room': R('jetty_shaft'), 'wall': 'east', 'size': [128, 256],
             'surface': dict(geo.LADDER), 'to': 'exit:d4_shaft',
             'notes': "The ladder up to D4's grate by the jetty."},
        ],
        'notes': "DD-20's contents, written by output/studio_cal/dd20/tools/dress.py: 9 doors (the Moon seal's double doors a hinged pair), four cage fronts and the store's hatch (movers), the hatch's bolt, one ladder, five chests, 45 placed monsters (13 Witches, 4 Coven Witches, the Head Witch, 24 Sewer Stalkers, 3 Stalker Matriarchs; five of them the cross's hidden ambush), four peaceful prisoners.",
    }


# ------------------------------------------------------------------------------------------------- wiring
ARRIVAL = ("LAKESIDE'S UNDERSIDE. Under the Guild the coven keeps house; half a storey below its hall are the cells, "
           "and under everything the town's sewer runs east to the lake. Naomi said four prisoners wait in the cells, "
           "and that the Head Witch keeps the coven's north-west corner.")
MIRROR = "A bodiless voice murmurs: \"You are the most beautiful one of all.\""
JOURNAL_NICHE = ("You find the last surviving page of this dead man's journal. It reads: ...still haven't a clue where "
                 "that statuette is. The sewer is infested with sewer monsters, and they seem to come out of nowhere. "
                 "Got to watch my back.")
JOURNAL_HIDEOUT = ("You find the last surviving page of this dead man's journal. It reads: ...witches won't find me "
                   "under here. Maybe I can use one of the other exits from the sewer to pop up in the town and be gone "
                   "before anyone can find me. All of this was so sudden. Who would have known that the witches were "
                   "plotting to...")
SKULLS = {
    'personality': ("Unprompted, the skull begins to speak: To make a Potion of Personality, gather together the ground "
                    "horn of a Unicorn, the tanned hide of an Ogre, and the blood of a monkeydog sacrificed 'neath the "
                    "blackness of a new moon. Slowly pour a half part of the blood into a twenty gallon cauldron and mix "
                    "in the horn powder. Heat to a low simmer and let sit for three days. At the stroke of midnight on "
                    "the third night, drop the Ogre hide into the stew and stir rapidly. If the hide dissolves any sooner "
                    "or later than three minutes, the brew is sour and will turn its drinkers to stone. Makes one serving."),
    'endurance': ("Unprompted, the skull begins to speak: To make a potion of endurance, gather together the poisoned "
                  "entrails of a toad kept under a cold stone for thirty-one days, a slice of swamp snake, the eye of a "
                  "newt, the toe of a frog, wool from a bat, tongue of a dog, a lizard's leg, an owlet's wing, and the "
                  "forked tongue of a snake. Throw them all in a cauldron and let sit under the auspices of a full moon. "
                  "Begin boiling just before sunrise. Keep warm until sunrise of the next day. If the mixture turns "
                  "black, the brew is sour and will turn its drinkers to stone. Makes one serving."),
    'speed': ("Unprompted, the skull begins to speak: To make a potion of speed, gather together the claw of a "
              "roadrunner, the wing of a hummingbird, and the paw of a cheetah. Pound the claw to dust and sprinkle into "
              "briskly boiling salt water. Quickly drop in the wing, followed by the paw. Stir 100 times, rapidly. "
              "Remove the cauldron from the fire and pour the liquid through a strainer and into a second cauldron. If "
              "any material remains in the strainer, the brew is sour and will turn its drinkers to stone. Makes one "
              "serving."),
}
NOTHING = "Nothing here."
INIT_Q = {'message': "Initiation cauldron. The brew smells of toad and ambition. Drink?", 'ask': "Drink (Yes/No)?",
          'answers': ['Yes', 'Y', 'yes', 'y']}


def cage_lua(key):
    return "\n".join([
        f'XeenQuests.hook("q-d22.{key}")',
        f'if IsQBitSet(QBit({FREED[key]})) then',
        f'    evt.SetMonGroupBit({PRISONER_GROUP[key]}, MonsterBits.Invisible, 1)',
        'end',
    ])


# On every load (a fresh entry or a saved game): each prisoner whose freed bit is set stays hidden.
PRISONERS_LOAD = "\n".join(
    [f'if IsQBitSet(QBit({FREED[k]})) then evt.SetMonGroupBit({PRISONER_GROUP[k]}, MonsterBits.Invisible, 1) end'
     for k in geo.CAGES])


TRAPDOOR_LUA = "\n".join([
    'local x, y, z = evt.GetPartyPosition()',
    'if x >= 3328 and x <= 3584 and y >= -768 and y <= -512 and z <= -448 then',
    '    evt.StatusText("The trapdoor is shut fast above you.", 4)',
    'end'])


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'arrived_once'}},
              'effects': [{'message': ARRIVAL}, {'qbit': 'arrived_once'}],
              'notes': "Say why the party is here (Q-D22: the prisoners, the Head Witch), on the first arrival by any of the three ways (arrived_once 117400)."})
    for k, op, s, n in DOORS:
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}',
                  'title': 'Double doors' if k == 'hall_walk' else 'Door'})
    E.append({'id': 'evt:exit_guild', 'preset': 'exit', 'source': 'exit:guild', 'title': 'Cellar door',
              'notes': "The game's own leave window, up into the Guild's back yard beside its cellar hatch (D4's entrance:dd20_guild, D-42 (4))."})
    E.append({'id': 'evt:exit_shaft', 'preset': 'exit', 'source': 'exit:shaft', 'title': 'Ladder',
              'notes': "The game's own leave window, up the ladder to D4's grate by the jetty (entrance:dd20_shaft)."})
    E.append({'id': 'evt:trapdoor_reset', 'preset': 'script', 'trigger': 'leave',
              'effects': [{'set': {'var': {'map_var': 'trap_checked'}, 'value': 0}}],
              'notes': "Leaving ends the visit: the next arrival is checked again for a drop through the trapdoor."})
    E.append({'id': 'evt:trapdoor', 'preset': 'script', 'trigger': 'timer', 'every': 1,
              'condition': {'not': {'map_var': 'trap_checked'}},
              'effects': [{'set': {'var': {'map_var': 'trap_checked'}, 'value': 1}}],
              'lua': TRAPDOOR_LUA,
              'notes': "The sump: the trapdoor a wrong answer drops the party through stays shut (one way, D-42 (4)). Said "
                       "once, on the first tick of a visit that began under the trapdoor (entrance:d4_trapdoor), never on a "
                       "later walk through the sump (A3, session 9)."})
    E.append({'id': 'evt:initiation', 'preset': 'script', 'source': 'deco:init_cauldron', 'title': 'Initiation cauldron',
              'question': dict(INIT_Q), 'lua': 'XeenQuests.hook("q-d22.initiation")',
              'notes': "poi:initiation: A3's q-d22.initiation (needs riddle_answered and the Head Witch alive; sets joined 113449, the Warlock promotion; its fail and else texts)."})
    E.append({'id': 'evt:head_witch_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
              'condition': {'kills': {'monster': 'monster:head_witch'}},
              'lua': 'XeenQuests.hook("q-d22.head_witch")',
              'notes': "goal:head_witch: her death runs A3's q-d22.head_witch (head_witch_slain 113447): the coven turns hostile again (A2's relations), Naomi's stocks open on D4."})
    E.append({'id': 'evt:witch_chest', 'preset': 'chest', 'source': 'chest:witch', 'title': 'Chest',
              'condition': {'any': [{'qbit': 'joined'}, {'qbit': 'head_witch_slain'}]},
              'else_effects': [{'lua': 'XeenQuests.hook("q-d22.witch_chest")'}],
              'effects': [{'lua': 'XeenQuests.hook("q-d22.witch_chest")'}],
              'notes': "goal:pass: her chest opens to a member (joined) or over her body, the Necropolis pass among its loot (F15); A3's q-d22.witch_chest sets pass_found 113448 once; shut, its fail line on the status line."})
    E.append({'id': 'evt:mirror', 'preset': 'text', 'source': 'panel:mirror', 'title': 'Mirror', 'window': True,
              'text': MIRROR, 'notes': "poi:mirror (dark/aaze0033:9)."})
    E.append({'id': 'evt:witch_bed', 'preset': 'script', 'source': 'platform:witch_bed', 'title': 'Bed',
              'condition': {'not': {'map_var': 'witch_bed_found'}}, 'else_effects': [{'text': NOTHING}],
              'effects': [{'set': {'var': {'map_var': 'witch_bed_found'}, 'value': 1}}, {'gold': 500},
                          {'text': "Under the pillow: a purse of the coven's dues. (+500 gold)"}],
              'notes': "'Bed' (dark/aaze0033:15): a find once, then 'Nothing here.' (:16)."})
    for k in geo.CAULDRONS:
        E.append({'id': f'evt:cauldron_{k}', 'preset': 'script', 'source': f'deco:cauldron_{k}', 'title': 'Cauldron',
                  'lua': f'XeenQuests.hook("q-d22.cauldron_{k}")',
                  'notes': f"poi:cauldrons (D-42 (6)): A3's q-d22.cauldron_{k} decides for the clicking member (+2, once per character, its player bit); again: 'You have had your fill.'"})
        E.append({'id': f'evt:skull_{k}', 'preset': 'text', 'source': f'deco:skull_{k}', 'title': 'Skull', 'window': True,
                  'text': SKULLS[k], 'notes': "poi:skulls (dark/aaze0033:12-14): the recipe beside its cauldron."})
    for i in (1, 2, 3, 4):
        if i == 3:
            E.append({'id': f'evt:bed_{i}', 'preset': 'script', 'source': f'platform:bed_{i}', 'title': 'Bed',
                      'condition': {'not': {'map_var': 'bed_found'}}, 'else_effects': [{'text': NOTHING}],
                      'effects': [{'set': {'var': {'map_var': 'bed_found'}, 'value': 1}}, {'gold': 150},
                                  {'text': "A few coins in the straw. (+150 gold)"}],
                      'notes': "'Bed' (dark/aaze0033:15): one find among the beds."})
        else:
            E.append({'id': f'evt:bed_{i}', 'preset': 'text', 'source': f'platform:bed_{i}', 'title': 'Bed',
                      'window': False, 'text': NOTHING, 'notes': "'Bed' / 'Nothing here.' (dark/aaze0033:15-16)."})
    E.append({'id': 'evt:shelf', 'preset': 'script', 'source': 'panel:shelf', 'title': 'Shelf',
              'condition': {'not': {'map_var': 'shelf_found'}}, 'else_effects': [{'text': NOTHING}],
              'effects': [{'set': {'var': {'map_var': 'shelf_found'}, 'value': 1}}, {'gold': 200},
                          {'text': "Behind the jars of newt eyes, a pouch of coins. (+200 gold)"}],
              'notes': "'Shelf' (dark/aaze0033:11): a find once."})
    E.append({'id': 'evt:sigil', 'preset': 'text', 'source': 'panel:sigil', 'title': 'Sigil', 'window': False,
              'text': "The coven's sigil, cut deep into the stone.", 'notes': "The coven hall's west wall."})
    for k in geo.CAGES:
        E.append({'id': f'evt:cage_{k}', 'preset': 'script', 'source': f'mover:cage_{k}', 'title': 'Cage',
                  'condition': {'not': {'qbit': f'{k}_freed'}},
                  'else_effects': [{'lua': f'XeenQuests.hook("q-d22.{k}")'}],
                  'lua': cage_lua(k),
                  'notes': f"poi:cages: 'Cage' (dark/aaze0033:22); A3's q-d22.{k} ({PRISONER_NAME[k]}'s line, {FREED[k]}, 500 XP); she or he is hidden at once; then the hook's 'Nothing here.'"})
        E.append({'id': f'evt:cage_{k}_opens', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
                  'condition': {'qbit': f'{k}_freed', 'not': {'map_var': f'cage_{k}_open'}},
                  'opens': [f'mover:cage_{k}'], 'effects': [{'set': {'var': {'map_var': f'cage_{k}_open'}, 'value': 1}}],
                  'notes': "The cage front sinks once its prisoner is freed (and again after a refill)."})
    E.append({'id': 'evt:prisoners_load', 'preset': 'script', 'trigger': 'load', 'lua': PRISONERS_LOAD,
              'notes': "D-42 (3): each prisoner is hidden by her or his freed bit on every load."})
    E.append({'id': 'evt:hatch_bolt', 'preset': 'switch', 'source': 'switch:hatch_bolt', 'title': 'Bolt',
              'condition': {'not': {'map_var': 'hatch_open'}}, 'opens': ['mover:hatch'], 'sets': {'map_var': 'hatch_open'},
              'effects': [{'text': "You draw the bolt. The hatch slides open over a ladder down into the dark."}],
              'locked_text': "The bolt is drawn; the hatch lies open.",
              'notes': "poi:hatch_bolt: the store's floor hatch, bolted from above, opened once from the store."})
    E.append({'id': 'evt:hatch', 'preset': 'switch', 'source': 'mover:hatch', 'title': 'Hatch',
              'condition': {'not': {'map_var': 'hatch_open'}}, 'effects': [{'text': "The hatch is bolted from above."}],
              'locked_text': "The hatch lies open over the ladder.",
              'notes': "From the cistern's ladder: 'The hatch is bolted from above.' until the store's bolt is drawn."})
    E.append({'id': 'evt:ambush', 'preset': 'script', 'trigger': 'step', 'source': 'room:cross',
              'condition': {'not': {'map_var': 'ambush_shown'}},
              'effects': [{'show_actors': AMBUSH_GROUP}, {'set': {'var': {'map_var': 'ambush_shown'}, 'value': 1}},
                          {'text': "Things climb out of the side drains!"}],
              'notes': "poi:ambush (D-18, D-42 (7)): the hidden group 6 shows on the first step onto the cross and stays shown (saved with the map); a refill resets both."})
    E.append({'id': 'evt:sump_bones', 'preset': 'script', 'source': 'deco:sump_bones', 'title': 'Bones',
              'condition': {'not': {'map_var': 'sump_purse'}}, 'else_effects': [{'text': NOTHING}],
              'effects': [{'set': {'var': {'map_var': 'sump_purse'}, 'value': 1}}, {'gold': 250},
                          {'text': "An earlier wrong answer. Its purse is still on it. (+250 gold)"}],
              'notes': "'Bones' (dark/aaze0034:6): a purse once."})
    E.append({'id': 'evt:hideout_bones', 'preset': 'script', 'source': 'deco:hideout_bones', 'title': 'Bones',
              'condition': {'not': {'map_var': 'hideout_pack'}}, 'else_effects': [{'message': JOURNAL_HIDEOUT}],
              'effects': [{'set': {'var': {'map_var': 'hideout_pack'}, 'value': 1}}, {'gold': 400},
                          {'message': JOURNAL_HIDEOUT + " Beside him, his pack. (+400 gold)"}],
              'notes': "poi:journals: the hideout's dead man (dark/aaze0034:8) and his pack (a find once)."})
    E.append({'id': 'evt:niche_bones', 'preset': 'text', 'source': 'deco:niche_bones', 'title': 'Bones', 'window': True,
              'text': JOURNAL_NICHE, 'notes': "poi:journals: two steps short of the alcove (dark/aaze0034:7)."})
    for pid in ('drain_mouth', 'sidedrain_n', 'sidedrain_s'):
        E.append({'id': f'evt:{pid}', 'preset': 'text', 'source': f'panel:{pid}', 'title': 'Sewer Drain',
                  'window': False,
                  'text': ("A drain grate in the wall. Something drips through it from the street." if pid == 'drain_mouth'
                           else "A side drain, grilled. The grille has been pushed out from inside and set back."),
                  'notes': "'Sewer Drain' (dark/aaze0034:2)."})
    E.append({'id': 'evt:lake_bars', 'preset': 'text', 'source': 'panel:lake_bars', 'title': 'Bars', 'window': False,
              'text': "The lake, beyond the bars. Something with too many arms is listening.",
              'notes': "The outfall's barred mouth to the lake."})
    for c in ('dorm', 'gaol', 'pump', 'warren'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    return E


def wiring():
    return {'format': 0,
            'variables': ['hatch_open', 'ambush_shown', 'sump_purse', 'hideout_pack', 'bed_found', 'witch_bed_found',
                          'shelf_found'] + [f'cage_{k}_open' for k in geo.CAGES] + ['trap_checked'],
            'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-20's events, written by output/studio_cal/dd20/tools/dress.py."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
