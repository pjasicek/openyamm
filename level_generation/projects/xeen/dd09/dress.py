#!/usr/bin/env python3
"""DD-09 Temple of Bark, L4: objects.yml, wiring.yml (written by gen.py L4)."""
import geo

ELITE, SHAMAN, CAPTAIN, SHAALTH, SNOG, ARACH, HUNTER, BARKMAN = 11040, 11041, 11042, 11043, 11044, 11330, 11331, 11633
# The talking prisoners' bodies: A2's rows (source/monsters.yml `characters`), each its own friendly faction (session 6;
# they stood on the engine peasants 358, 361, 349, 376 before).
NATHAN_BODY, SKY_BODY, ALICIA_BODY, SHEEWANA_BODY = 11902, 11903, 11904, 11905
NAME = {ELITE: 'elite', SHAMAN: 'shaman', CAPTAIN: 'captain', ARACH: 'arachnoid', HUNTER: 'hunter'}
SHAALTH_GROUP, BARKMAN_GROUP, PRISONER_GROUP, SHEEWANA_GROUP = 5, 30, 20, 21

Q_ARRIVED, Q_FREED = 117120, 117121
Q_SHAALTH, Q_CAGE, Q_SHEEWANA, Q_DISCIPLES = 113204, 113205, 113206, 113216
Q_ROOT_W, Q_ROOT_E = 113210, 113211
BIT_RED, BIT_BLUE, BIT_BARREL = 11315, 11316, 11317
NPC = {'nathan': 5111, 'sky': 5112, 'snog': 5113, 'alicia': 5114, 'sheewana': 5107}
ENERGY_DISK = 12334

AMBER = [205, 160, 100]
ORC = [215, 150, 90]
GREENL = [160, 195, 165]
ROOTS = [150, 125, 95]
DAY = [200, 220, 160]


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
DOORS = [
    # id, opening, surface, notes
    ('hall_barracks', 'open:hall_barracks', geo.DOOR, "A plank door from the hall into the orc barracks."),
    ('guard_chapel', 'open:guard_chapel', geo.DOOR, "A plank door from the guardroom into the Chapel of Sap."),
    ('roots_vats', 'open:roots_vats', geo.DOOR, "A plank door from the root cellar into the sap store."),
    ('ring_shaalth', 'open:ring_shaalth', geo.DOOR, "A plank door from the ring landing into Shaalth's hall."),
    ('shaalth_shaman', 'open:shaalth_shaman', geo.DOOR, "A plank door from Shaalth's hall into the tea room."),
    ('shaman_asc', 'open:shaman_asc', geo.DOOR, "A plank door from the tea room into the Chapel of Ascension."),
    ('vault', 'open:asc_vault', geo.VAULTDOOR, "The Disciples' arched door under ivy: 'Disciples of Bark ONLY!'"),
    ('treasure_crown', 'open:treasure_crown', geo.DOOR, "A plank door from the treasure room into the crown."),
]


# The vault's arched door is a hinged pair (the double-door rule; the audit's doors.half_wing): ceb1dl the left wing,
# ceb1dr the right, the same from the vault's side.
VAULT_WINGS = [[dict(geo.VAULTDOOR), dict(geo.VAULTDOOR_R)]]


def doors():
    out = []
    for k, op, s, n in DOORS:
        if k == 'vault':
            out.append({'id': f'door:{k}', 'opening': op, 'kind': 'hinged', 'leaves': 2,
                        'pictures': [list(map(dict, r)) for r in VAULT_WINGS],
                        'back_pictures': [list(map(dict, r)) for r in VAULT_WINGS],
                        'notes': n + " A hinged pair (ceb1dl, ceb1dr)."})
        else:
            out.append({'id': f'door:{k}', 'opening': op, 'kind': 'slide_up', 'surface': dict(s, fit=True), 'notes': n})
    return out


def gate(gid, room, at, size, notes):
    return {'id': gid, 'room': R(room), 'at': at, 'size': size, 'bottom': 0, 'height': 256, 'travel': [0, 0, -248],
            'speed': 160, 'surface': dict(geo.GRILLE), 'top_surface': dict(geo.IRON, scale=3), 'notes': notes}


PRISONER_GATES = {
    'nathan': gate('mover:gate_nathan', 'pens', [-6908, geo.PEN_CAGES['nathan']], [8, 368], "Nathan's cage gate (the pen lever): sinks into the floor."),
    'sky': gate('mover:gate_sky', 'pens', [-6908, geo.PEN_CAGES['sky']], [8, 368], "Sky's cage gate (the pen lever)."),
    'snog': gate('mover:gate_snog', 'cells', [geo.CELL_CAGES['snog'], 2692], [368, 8], "Snog's cell gate (the pen lever)."),
    'alicia': gate('mover:gate_alicia', 'cells', [geo.CELL_CAGES['alicia'], 2692], [368, 8], "Alicia's cell gate (the pen lever)."),
}


def movers():
    return list(PRISONER_GATES.values()) + [
        gate('mover:cage_sheewana', 'shaalth', [8512, 1156], [368, 8],
             "Sheewana's cage gate: sinks once q-d10.cage has run (Shaalth's key).")]


def switches():
    return [
        {'id': 'switch:pen_lever', 'room': R('pens'), 'kind': 'lever', 'at': [-6400, -2560], 'reach': 48,
         'notes': "The pen lever on the south wall: opens and shuts the four prisoners' cages."},
        {'id': 'switch:asc_lever', 'room': R('ascension'), 'kind': 'lever', 'at': [11392, -1152], 'reach': 48,
         'notes': "The Disciples' lever on the chapel's south wall."},
    ]


def chests():
    return [
        {'id': 'chest:sap', 'room': R('sap_vats'), 'at': [-3776, -1472], 'treasure_level': 3,
         'random_items': 2, 'gold': 600, 'notes': "The orcs' takings from the sap trade."},
        {'id': 'chest:shaalth', 'room': R('shaalth'), 'at': [7744, -1216], 'treasure_level': 4,
         'random_items': 3, 'gold': 1500, 'notes': "Shaalth's hoard by his dais."},
        {'id': 'chest:vault', 'room': R('vault'), 'at': [12960, 0], 'facing': 'w', 'treasure_level': 3,
         'random_items': 3, 'gold': 800, 'notes': "The Disciples' vault."},
        {'id': 'chest:treasure', 'room': R('treasure'), 'at': [10880, -5824], 'facing': 'n', 'treasure_level': 3,
         'random_items': 2, 'gold': 700, 'notes': "The temple's offerings."},
        {'id': 'chest:barkman', 'room': R('barkman'), 'at': [8704, -5952], 'facing': 'n', 'treasure_level': 4,
         'random_items': 3, 'gold': 2000, 'notes': "Barkman's chest, bound shut by his life force until he dies."},
    ]


PLACED = {
    'barracks': [(ELITE, [1792, -768]), (ELITE, [2304, -768]), (ELITE, [2816, -768]), (ELITE, [1792, 256]),
                 (ELITE, [2816, 256]), (ELITE, [2304, -128]), (CAPTAIN, [3008, -384])],
    'guardroom': [(ELITE, [1792, 1280]), (ELITE, [2816, 1280]), (ELITE, [1792, 2560]), (ELITE, [2816, 2560])],
    'chapel': [(SHAMAN, [0, 2048]), (SHAMAN, [640, 1792])],
    'root_hall': [(ARACH, [-5120, 512]), (ARACH, [-4032, -128]), (ARACH, [-4736, -896]), (ARACH, [-4608, 640])],
    'pens': [(ELITE, [-6144, -1088]), (ELITE, [-6144, -1792]), (ELITE, [-5888, -2304])],
    'sap_vats': [(ELITE, [-5120, -2112]), (ELITE, [-4672, -1600]), (ELITE, [-4672, -2560])],
    'shaalth': [(CAPTAIN, [6912, -768]), (CAPTAIN, [6912, 256]), (CAPTAIN, [7552, 0]), (SHAMAN, [6144, 0]),
                (SHAMAN, [7424, 768])],
    'cells': [(CAPTAIN, [6528, 2112])],
    'shaman': [(SHAMAN, [9216, -448]), (SHAMAN, [9984, -448]), (SHAMAN, [9216, 448]), (SHAMAN, [9984, 384])],
    'treasure': [(SHAMAN, [10112, -5632]), (SHAMAN, [10624, -5248])],
    'limb_walk': [(ARACH, [6016, -4096]), (ARACH, [6912, -4096]), (ARACH, [7680, -4096]), (ARACH, [8704, -4096]),
                  (HUNTER, [7296, -3968]), (HUNTER, [9088, -4224])],
    'fruit': [(ARACH, [9984, -4352]), (ARACH, [10752, -3776]), (HUNTER, [10368, -4096]), (HUNTER, [10752, -4416])],
    'crown': [(HUNTER, [12416, -3328]), (HUNTER, [12416, -4864]), (HUNTER, [11648, -4096]), (HUNTER, [13184, -4096])],
}

PEOPLE = [
    # key, room, body, at, facing, notes
    ('nathan', 'pens', NATHAN_BODY, [-7104, geo.PEN_CAGES['nathan']], 0, "Nathan the Prisoner (row 11902, NPC 5111), in his pen."),
    ('sky', 'pens', SKY_BODY, [-7104, geo.PEN_CAGES['sky']], 0, "Sky the Prisoner (row 11903, NPC 5112), in his pen."),
    ('snog', 'cells', SNOG, [geo.CELL_CAGES['snog'], 2880], 270, "Snog the Orc (row 11044, NPC 5113: his own friendly faction), in his cell."),
    ('alicia', 'cells', ALICIA_BODY, [geo.CELL_CAGES['alicia'], 2880], 270, "Alicia the Just (row 11904, NPC 5114), in her cell."),
]


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at in lst:
            n[row] = n.get(row, 0) + 1
            out.append({'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                        'facing': 270, 'hostile': True, 'group': 1})
    out.append({'id': 'monster:shaalth', 'room': R('shaalth'), 'monster': SHAALTH, 'at': [8064, -928], 'facing': 180,
                'hostile': True, 'group': SHAALTH_GROUP,
                'notes': "Shaalth the Orc King (boss row 11043, 30) on his dais: q-d10.shaalth at his death."})
    out.append({'id': 'monster:barkman', 'room': R('barkman'), 'monster': BARKMAN, 'at': [8192, -5440], 'facing': 90,
                'hostile': True, 'group': BARKMAN_GROUP, 'hidden': True,
                'notes': "Barkman (11633, 60), placed hidden: shown the first time a limb alcove takes a gem (D-27; map variable barkman_shown). Optional; his XP counts in Act IV (D-1.2)."})
    for key, room, body, at, facing, notes in PEOPLE:
        out.append({'id': f'monster:{key}', 'room': R(room), 'monster': body, 'at': at, 'facing': facing,
                    'hostile': False, 'immobile': True, 'group': PRISONER_GROUP,
                    'notes': notes + " Peaceful; talked to through the cage gate; hidden on the next entry (not a reload) once freed."})
    out.append({'id': 'monster:sheewana', 'room': R('shaalth'), 'monster': SHEEWANA_BODY, 'at': [8512, 1344],
                'facing': 270, 'hostile': False, 'immobile': True, 'group': SHEEWANA_GROUP,
                'notes': "Princess Sheewana (row 11905, her own friendly faction; NPC 5107) in her cage; hidden once she has gone home (sheewana_freed)."})
    return out


# key: (decoration, room, at, floor height or None, title)
DECOS = [
    ('red_flask', 'dec35', 'chapel', [-384, 2864], 96, 'Red flask'),
    ('blue_flask', 'dec35', 'chapel', [768, 2864], 96, 'Blue flask'),
    ('kettle', 'cauld00', 'shaman', [9600, 576], None, 'Kettle'),
    ('black_barrel', 'bigbarel', 'sap_vats', [-4512, -2688], None, 'Black barrel'),
]
PROPS = [
    ('barrel_1', 'bigbarel', 'sap_vats', [-3776, -2496]),
    ('barrel_2', 'bigbarel', 'sap_vats', [-3776, -2656]),
    ('bedroll_1', 'bag01', 'barracks', [1600, -960]),
    ('bedroll_2', 'bag01', 'barracks', [2112, -992]),
    ('bedroll_3', 'bag01', 'barracks', [3136, 448]),
    ('bedroll_4', 'bag01', 'barracks', [1600, 448]),
    ('cookfire', 'ckfyr00', 'barracks', [3008, -896]),
    ('guard_sack_1', 'floursac', 'guardroom', [3136, 2752]),
    ('guard_sack_2', 'floursac', 'guardroom', [2944, 2752]),
    ('pen_bones', 'dec29', 'pens', [-5888, -896]),
    ('roots_mush_1', 'mushrm02', 'root_hall', [-5312, -896]),
    ('roots_mush_2', 'mushrm03', 'root_hall', [-3776, 832]),
    ('fruit_sack_1', 'floursac', 'fruit', [9920, -3712]),
    ('fruit_sack_2', 'floursac', 'fruit', [10880, -3648]),
    ('fruit_sack_3', 'bag01', 'fruit', [9856, -4480]),
    ('skull_pole', 'sklplrev', 'shaalth', [7424, -1152]),
    ('treasure_sack', 'bag01', 'treasure', [9792, -5824]),
]
# lights audit (merge point 14): the treasure room's torch moved from 0.5 (in the doorway from Barkman's room) to 0.2
TORCHES = [('barracks', 'w', 0.8), ('barracks', 'e', 0.3), ('guardroom', 'n', 0.5), ('guardroom', 's', 0.25),
           ('pens', 'e', 0.75), ('sap_vats', 'w', 0.6), ('shaalth', 'w', 0.2), ('shaalth', 's', 0.3), ('shaalth', 'n', 0.25),
           ('cells', 's', 0.75), ('shaman', 's', 0.5), ('treasure', 'w', 0.2)]
PATH_LIGHT_HEIGHT = {'ring_stair': 256}


def decorations():
    out = []
    for key, dec, room, at, fh, title in DECOS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at, 'notes': f"{title} (clicked: evt:{key})."}
        if fh is not None:
            d['floor_height'] = fh
        out.append(d)
    for key, dec, room, at in PROPS:
        out.append({'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at})
    for i, (room, wall, along) in enumerate(TORCHES):
        out.append({'id': f'deco:torch_{i}', 'room': R(room), 'decoration': 'torch02', 'wall': wall, 'along': along,
                    'height': 192})
    return out


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
    theme_col = {'theme:trunk': AMBER, 'theme:limb': AMBER, 'theme:branch': DAY, 'theme:barracks': ORC, 'theme:orc': ORC,
                 'theme:chapel': GREENL, 'theme:sanctuary': GREENL, 'theme:roots': ROOTS, 'theme:pens': ROOTS,
                 'theme:sap': ROOTS, 'theme:crown': DAY}
    for room in list(geo.R) + list(geo.P):
        (w, h), c = geo.extent(room)
        col = theme_col[geo.R[room][4] if room in geo.R else geo.P[room][5]]
        if room in geo.P:
            pts = geo.P[room][1]
            for a, b in zip(pts, pts[1:]):
                if abs(b[0] - a[0]) + abs(b[1] - a[1]) >= 1024:
                    # lights audit (merge point 14): the ring stair's ceiling stays level while its floor climbs, so
                    # the default height put its upper light 249 into the rock: an explicit height over the floor
                    add(room, [(a[0] + b[0]) // 2, (a[1] + b[1]) // 2], 1100, col,
                        height=PATH_LIGHT_HEIGHT.get(room))
            continue
        r = int(min(2000, max(700, 0.6 * max(w, h))))
        if max(w, h) > 2400:
            ax = 0 if w >= h else 1
            for f in (0.25, 0.75):
                p = list(c)
                lo = c[ax] - (w if ax == 0 else h) / 2
                p[ax] = int(lo + f * (w if ax == 0 else h))
                add(room, p, int(r * 0.75), col)
        else:
            add(room, c, r, col)
    add('crown', [12416, -4096], 1600, DAY, height=900, notes="Daylight through the leaves.")
    add('ascension', [11840, -704], 500, [150, 200, 230], height=96, notes="The Crystal Water's glow.",
        pulse={'intensity': [0.8, 1.0], 'radius': [460, 520], 'frequency': 0.3})
    add('barracks', [3008, -896], 700, [230, 140, 70], height=64, notes="The orcs' cookfire.",
        pulse={'intensity': [0.7, 1.0], 'radius': [640, 720], 'frequency': 0.9})
    return L


def sounds():
    return [
        {'id': 'sound:crown', 'room': R('crown'), 'at': [12416, -4096], 'sound': 'whistling wind', 'radius': 2200,
         'inner_radius': 800, 'volume': 0.35, 'notes': "Wind in the leaves of the crown."},
        {'id': 'sound:limbs', 'room': R('limb_walk'), 'at': [7520, -4096], 'sound': 'whistling wind', 'radius': 2000,
         'inner_radius': 600, 'volume': 0.25, 'notes': "The limbs creak in the wind."},
        {'id': 'sound:roots', 'room': R('root_hall'), 'at': [-4544, 0], 'sound': 'drip02', 'radius': 1500,
         'inner_radius': 400, 'volume': 0.5, 'wait': [2, 6], 'notes': "Water dripping through the roots."},
        {'id': 'sound:pens', 'room': R('pens'), 'at': [-6400, -1600], 'sound': 'drip03', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.5, 'wait': [3, 8], 'notes': "The pens dripping."},
        {'id': 'sound:sap', 'room': R('sap_vats'), 'at': [-4096, -2112], 'sound': 'bubbling cauldron01', 'radius': 1300,
         'inner_radius': 300, 'volume': 0.4, 'notes': "The sap vats working."},
        {'id': 'sound:kettle', 'room': R('shaman'), 'at': [9600, 576], 'sound': 'bubbling cauldron01', 'radius': 1000,
         'inner_radius': 200, 'volume': 0.5, 'notes': "The shaman's kettle on the boil."},
        {'id': 'sound:cookfire', 'room': R('barracks'), 'at': [3008, -896], 'sound': 'campfire', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.5, 'notes': "The orcs' cookfire."},
        {'id': 'sound:ascension', 'room': R('ascension'), 'at': [11392, -704], 'sound': 'water lapping loop',
         'radius': 1100, 'inner_radius': 300, 'volume': 0.3, 'notes': "The two basins."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('trunk_door'), 'at': [0, -1920], 'facing': 'n',
                  'notes': "At the foot of the temple's first stair, inside the trunk's round door, facing the Hall of the Trunk (D2's door:dd09 arrives here)."},
        'doors': doors(), 'movers': movers(), 'switches': switches(), 'chests': chests(),
        'monsters': monsters(), 'decorations': decorations(), 'lights': lights(), 'sounds': sounds(),
        'exits': [
            {'id': 'exit:trunk_door', 'room': R('trunk_door'), 'wall': 'south', 'size': [256, 352],
             'surface': geo.S_('7solid01', 128, 256, fit=True), 'to': 'exit:d2_trunk',
             'notes': "The great tree's round door, out to the bark glade (D2)."},
        ],
        'notes': "DD-09's contents, written by output/studio_cal/dd09/tools/dress.py: 8 doors, five cage gates (movers), two levers, five chests, 50 placed monsters (16 Orc Elites, 10 Orc Shamans, 5 Orc Captains, Shaalth, 10 Arachnoids, 8 Arachnoid Hunters), Barkman hidden, four peaceful prisoners and Princess Sheewana.",
    }


# ------------------------------------------------------------------------------------------------- wiring
ARRIVAL = ("THE TEMPLE OF BARK. The round door shuts behind you on the bark glade. Inside the great tree the air is "
           "warm and smells of sap and orc. Shaalth's orcs hold the old temple, and somewhere in it Princess "
           "Sheewana, the sprites' sister. This door is the way back out.")
STAGNANT = "The water is stagnant."
FOUNTAIN_TEXT = "The water is cool, clear and refreshing."
BARREL_TEXT = ("The barrel is filled with a strange black sludge. A note on the inside of the lid reads, \"Danger: "
               "Unpredictable Effects.\" Drink?")
BARREL_DONE = "Your statistics have improved, but you have suffered a little magical aging."
LEDGER = ("Ledger. Purchased Item, Cost. 6/6/787: 5 tons manure, 500. 8/10/787: 40 vials, 400. 9/10/787: 12 barrels, "
          "245. 10/1/787: 55 magic skulls, 12,000. 1/5/788: 100 iron spikes, 1,000. 1/7/788: 3 bottles ink, 6. "
          "1/7/788: 10000 pgs paper, 8000. 2/8/788: 84 shovels, 450.")
HISTORY = ("History of Bark. Ages past, before the time when men walked the Earth, there was Bark. From Bark did all "
           "good things come; Bark's roots drew water from the Earth, Bark's leaves drew sustenance from the sun, "
           "Bark's branches held the sky above the ground, lest the sky fall and crush the world beneath it.")
BOOK_SAP = ("Book of Sap. The Sap of Bark runs with power. Store the Sap with care, and add the Holy Bark of Yak on the "
            "spring equinox to the Sap to make it potent. The Sap will make Holy Potions that improve the health and "
            "character of the drinker. The Holy Potions must be reserved for the disciples of Bark, for Bark requires "
            "Her Clerics to be strong of limb and mind.")
CEREMONIES = ("Morning Ceremonies. Take ye then the Bark of the Tree, and sprinkle it with ash. The ash symbolizes the "
              "Yak, the Bark the Moo. March ye the congregation in a circle about the Tree, directing the half of them "
              "to chant \"Yak\" and the other half \"Moo\". ... The Morning Ceremonies are complete. Break for "
              "breakfast, then repeat before lunch.")
DIARY = ("The book seems to be a lengthy diary of Barkman's life. Only a small portion still survives: 4/8/400: "
         "SQUEEZED branch feeders today. 9/7/413: SQUEEZED branch feeders today. 8/2/476: SQUEEZED branch feeders "
         "today. 3/6/655: SQUEEZED branch feeders today.")
BOUND = "The life force of the BARKMAN binds the lid of the chest shut, making it impossible to open."
RUMBLE = "You hear a rumbling in the distance."
CAGE_LOCKED = "Locked. A lever somewhere in the temple works these cages."
CAGE_EMPTY = "The cage is empty."
LIMB_FED = "The limb alcove is fed. Something in the trunk is still awake."
RIGHT_LEVER = "The lever clicks home. In the Crystal Water's basin the scum parts and the water runs clear."


def flask_lua(bit, var, stat):
    return "\n".join([
        f'if IsPlayerBitSet(PlayerBit({bit})) then',
        '    evt.StatusText("The flask is empty for you.")',
        '    return',
        'end',
        'evt.ForPlayer(Players.Current)',
        f'AddValue({var}, 2)',
        f'SetPlayerBit(PlayerBit({bit}))',
        f'evt.StatusText("+2 {stat} (permanent).")',
    ])


def choice(question, yes_lines, pre_lines=(), ask='"Yes/No?"'):
    """A Lua body that asks a typed Yes/No question (the studio's own compiled question form: the right answer comes
    back as continueStep 2) and runs yes_lines on Yes."""
    lines = ['if continueStep == 2 then'] + ['    ' + x for x in yes_lines] + ['    return', 'end',
                                                                                'if continueStep ~= nil then', '    return', 'end']
    lines += list(pre_lines)
    if question:
        lines.append(f'evt.SetMessage({question})')
    lines.append(f'evt.AskQuestion(eventId, 1, 0, 2, {ask}, {{"Yes", "Y", "yes", "y"}})')
    return "\n".join(lines)


FEED_Q = {'message': "Feed me! Give gem?", 'ask': "Give gem (Yes/No)?", 'answers': ['Yes', 'Y']}


def limb_lua(var):
    return "\n".join([
        'if Xeen.payGems(1) then',
        f'    SetValue(MapVar({var}), 1)',
        '    SetValue(MapVar(barkman_woken), 1)',
        '    XeenQuests.hook("q-d10.limb_alcoves")',
        'else',
        '    evt.StatusText("You have no gem. The limb creaks, unfed.")',
        'end'])


def dial_lua(var):
    return choice('"Dial reads " .. n .. ". Turn?"', [
        f'if IsAtLeast(MapVar({var}), 3) then SetValue(MapVar({var}), 0) else AddValue(MapVar({var}), 1) end',
        'SetValue(MapVar(lever_pulled), 0)',
        'local m = 1',
        f'for v = 1, 3 do if IsAtLeast(MapVar({var}), v) then m = v + 1 end end',
        'evt.StatusText("The dial grinds round. It reads " .. m .. ".")'], pre_lines=[
        'local n = 1',
        f'for v = 1, 3 do if IsAtLeast(MapVar({var}), v) then n = v + 1 end end'], ask='"Turn (Yes/No)?"')


def is_exactly(var, v):
    return f'(IsAtLeast(MapVar({var}), {v}) and not IsAtLeast(MapVar({var}), {v + 1}))'


ASC_LEVER = "\n".join([
    f'if {is_exactly("dial_west", 0)} and {is_exactly("dial_north", 1)} and {is_exactly("dial_east", 2)} then',
    '    SetValue(MapVar(lever_pulled), 1)',
    f'    evt.SimpleMessage("{RIGHT_LEVER}")',
    'else',
    '    SetValue(MapVar(lever_pulled), 0)',
    '    evt.StatusText("Nothing happens.")',
    'end',
])

CRYSTAL = "\n".join([
    f'if IsQBitSet(QBit({Q_DISCIPLES})) then',
    '    XeenQuests.hook("q-d10.crystal_water")',
    '    return',
    'end',
    'if not IsAtLeast(MapVar(lever_pulled), 1) then',
    f'    evt.StatusText("{STAGNANT}")',
    '    return',
    'end',
    'XeenQuests.hook("q-d10.crystal_water")',
])

# The Dark Water (D-27): poisons the drinker and takes about a tenth of the drinker's hit points, never the last of them.
DARK = "\n".join([
    'XeenQuests.hook("q-d10.dark_water")',
    'evt.ForPlayer(Players.Current)',
    'local now, step = 0, 4096',
    'while step >= 1 do',
    '    if IsAtLeast(CurrentHealth, now + step) then now = now + step end',
    '    step = math.floor(step / 2)',
    'end',
    'SetValue(PoisonedGreen, 1)',
    'local hurt = math.floor(now / 10)',
    'if hurt > 0 and now - hurt >= 1 then SubtractValue(CurrentHealth, hurt) end',
])

KETTLE = choice('', ['XeenQuests.hook("q-d10.kettle_drunk")', 'evt.ForPlayer(Players.Current)',
                     'SetValue(PoisonedGreen, 1)'], pre_lines=['XeenQuests.hook("q-d10.kettle")'], ask='"Drink (Yes/No)?"')

BARREL = "\n".join([
    'evt.ForPlayer(Players.Current)',
    'for _, stat in ipairs({BaseMight, BaseIntellect, BasePersonality, BaseEndurance, BaseSpeed, BaseAccuracy, BaseLuck}) do',
    '    AddValue(stat, 1)',
    'end',
    'AddValue(Age, 1)',
    f'SetPlayerBit(PlayerBit({BIT_BARREL}))',
    f'evt.SimpleMessage("{BARREL_DONE}")'])
BARREL_Q = {'message': BARREL_TEXT, 'ask': "Drink (Yes/No)?", 'answers': ['Yes', 'Y']}

CAGE = "\n".join([
    f'if IsQBitSet(QBit({Q_SHEEWANA})) then',
    '    XeenQuests.hook("q-d10.cage")',
    '    return',
    'end',
    f'if IsQBitSet(QBit({Q_CAGE})) then',
    f'    evt.SpeakNPC({NPC["sheewana"]})',
    '    return',
    'end',
    'XeenQuests.hook("q-d10.cage")',
])


def prisoner_lua(key):
    return "\n".join([
        'if IsAtLeast(MapVar(prisoners_gone), 1) then',
        f'    evt.StatusText("{CAGE_EMPTY}")',
        '    return',
        'end',
        'if not IsAtLeast(MapVar(pens_open), 1) then',
        f'    evt.StatusText("{CAGE_LOCKED}")',
        '    return',
        'end',
        f'evt.SpeakNPC({NPC[key]})',
    ])


# The load event of a visit: a fresh entry (in_visit clear, as leaving left it) hides the freed prisoners; a reload of a
# game saved inside the map finds in_visit set and changes nothing.
PRISONERS_GONE = "\n".join([
    f'if IsQBitSet(QBit({Q_FREED})) and not IsAtLeast(MapVar(in_visit), 1) then',
    f'    evt.SetMonGroupBit({PRISONER_GROUP}, MonsterBits.Invisible, 1)',
    '    SetValue(MapVar(prisoners_gone), 1)',
    'end',
    'SetValue(MapVar(in_visit), 1)',
])

PEN_LEVER = "\n".join([
    'if IsAtLeast(MapVar(pens_open), 1) then',
    '    SetValue(MapVar(pens_open), 0)',
    'else',
    '    SetValue(MapVar(pens_open), 1)',
    f'    SetQBit(QBit({Q_FREED}))',
    'end',
    f'evt.StatusText("{RUMBLE}")',
])

# D-37 (3): once per character on A3's player bits (q-d10.yml player_bits fountain_*); the map qbits 117122-117125 are
# retired.
FOUNTAIN_BITS = {'fire': 11306, 'air': 11307, 'water': 11308, 'body': 11309}
FOUNTAIN_FULL = FOUNTAIN_TEXT + " You have had your fill."
FOUNTAINS = {'fire': ('FireResistance', 'Fire'), 'air': ('AirResistance', 'Air'), 'water': ('WaterResistance', 'Water'),
             'body': ('BodyResistance', 'Body')}


def fountain_lua(key):
    var, word = FOUNTAINS[key]
    return "\n".join([
        f'if IsPlayerBitSet(PlayerBit({FOUNTAIN_BITS[key]})) then',
        '    ' + status_line(FOUNTAIN_FULL),
        '    return',
        'end',
        'evt.ForPlayer(Players.Current)',
        f'AddValue({var}, 5)',
        f'SetPlayerBit(PlayerBit({FOUNTAIN_BITS[key]}))',
        status_line(f'{FOUNTAIN_TEXT} +5 {word} resistance (permanent).'),
    ])


def status_line(t):
    """F13: a touch effect's text is a status line, evt.StatusText(text[, seconds]), never a window."""
    if len(t) > 30:
        return f'evt.StatusText("{t}", {max(2, min(6, 2 + len(t) // 15))})'
    return f'evt.StatusText("{t}")'


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'arrived_once'}},
              'effects': [{'message': ARRIVAL}, {'qbit': 'arrived_once'}],
              'notes': "Say why the party is here (Q-D10: Sheewana), on the first arrival only (arrived_once 117120)."})
    for k, op, s, n in DOORS:
        e = {'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}', 'title': 'Door'}
        if k == 'vault':
            e.update({'title': "Disciples' door", 'condition': {'qbit': 'disciples'},
                      'locked_text': "Disciples of Bark ONLY!",
                      'notes': "'Disciples of Bark ONLY!' (dark/aaze0076:0): opens to a party that has drunk the Crystal Water (disciples 113216)."})
        E.append(e)
    E.append({'id': 'evt:exit_trunk', 'preset': 'exit', 'source': 'exit:trunk_door', 'title': 'Trunk door',
              'notes': "The game's own leave window, to D2's bark glade outside the great tree's door (D-24)."})
    E.append({'id': 'evt:voice', 'preset': 'script', 'trigger': 'step', 'source': 'room:first_hall',
              'condition': {'not': {'map_var': 'voice_heard'}},
              'effects': [{'set': {'var': {'map_var': 'voice_heard'}, 'value': 1}}, {'lua': 'XeenQuests.hook("q-d10.voice")'}],
              'notes': "poi:voice: A3's q-d10.voice on coming into the hall, once per visit (voice_heard, cleared on leaving)."})
    E.append({'id': 'evt:voice_reset', 'preset': 'script', 'trigger': 'leave',
              'effects': [{'set': {'var': {'map_var': 'voice_heard'}, 'value': 0}}],
              'notes': "The voice speaks again on the next visit."})
    E.append({'id': 'evt:root_west', 'preset': 'script', 'source': 'panel:root_west', 'title': 'Root alcove',
              'condition': {'not': {'qbit': 'root_west'}}, 'else_effects': [{'lua': 'XeenQuests.hook("q-d10.root_west")'}],
              'question': dict(FEED_Q), 'effects': [{'lua': f'if XeenQuests.hook("q-d10.root_west") then AddValue(InventoryItem({ENERGY_DISK}), {ENERGY_DISK}) end'}],
              'notes': "poi:root_alcoves: 'Feed me! Give gem?' (dark/aaze0077:14); A3's once-hook q-d10.root_west takes the gem, the map gives the Energy Disk (map_gives)."})
    E.append({'id': 'evt:root_east', 'preset': 'script', 'source': 'panel:root_east', 'title': 'Root alcove',
              'condition': {'not': {'qbit': 'root_east'}}, 'else_effects': [{'lua': 'XeenQuests.hook("q-d10.root_east")'}],
              'question': dict(FEED_Q), 'effects': [{'lua': f'if XeenQuests.hook("q-d10.root_east") then AddValue(InventoryItem({ENERGY_DISK}), {ENERGY_DISK}) end'}],
              'notes': "poi:root_alcoves: as the west (q-d10.root_east)."})
    for i in (1, 2, 3):
        E.append({'id': f'evt:limb_{i}', 'preset': 'script', 'source': f'panel:limb_{i}', 'title': 'Limb alcove',
                  'condition': {'not': {'map_var': f'limb_{i}_fed'}}, 'else_effects': [{'text': LIMB_FED}],
                  'question': dict(FEED_Q), 'lua': limb_lua(f'limb_{i}_fed'),
                  'notes': "poi:limb_alcoves: one gem each (the map takes it), A3's q-d10.limb_alcoves for the words; the first gem wakes Barkman (barkman_woken)."})
    E.append({'id': 'evt:barkman_wakes', 'preset': 'script', 'trigger': 'timer', 'every': 1,
              'condition': {'map_var': 'barkman_woken', 'not': {'map_var': 'barkman_shown'}},
              'effects': [{'show_actors': BARKMAN_GROUP}, {'set': {'var': {'map_var': 'barkman_shown'}, 'value': 1}}],
              'notes': "D-27: Barkman (group 30) shows the first time a limb alcove takes a gem and stays shown (his state is saved with the map); a refill resets him hidden with the variables."})
    E.append({'id': 'evt:diary', 'preset': 'script', 'source': 'platform:diary', 'title': "Barkman's diary",
              'effects': [{'message': DIARY}], 'notes': "poi:diary (dark/aaze0077:19)."})
    E.append({'id': 'evt:chest_barkman', 'preset': 'chest', 'source': 'chest:barkman', 'title': 'Chest',
              'condition': {'kills': {'monster': 'monster:barkman'}}, 'locked_text': BOUND,
              'notes': "Barkman's chest (hoard 4): his life force binds it shut until he is dead (dark/aaze0077:21)."})
    E.append({'id': 'evt:shaalth_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2,
              'condition': {'kills': {'monster': 'monster:shaalth'}}, 'once': True,
              'lua': 'XeenQuests.hook("q-d10.shaalth")',
              'notes': "goal:shaalth: Shaalth's death runs A3's q-d10.shaalth (shaalth_slain 113204)."})
    E.append({'id': 'evt:cage', 'preset': 'script', 'source': 'mover:cage_sheewana', 'title': 'Cage', 'lua': CAGE,
              'notes': "goal:sheewana: A3's q-d10.cage (needs shaalth_slain; its fail and else texts); once open, Princess Sheewana talks (NPC 5107, topic Home). Words needed: an indoor monster with an npc id."})
    E.append({'id': 'evt:cage_opens', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'cage_opened', 'not': {'map_var': 'cage_moved'}}, 'opens': ['mover:cage_sheewana'],
              'effects': [{'set': {'var': {'map_var': 'cage_moved'}, 'value': 1}}],
              'notes': "The cage's gate lifts once q-d10.cage has set cage_opened (113205)."})
    E.append({'id': 'evt:sheewana_gone', 'preset': 'script', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'sheewana_freed', 'not': {'map_var': 'sheewana_hidden'}},
              'effects': [{'hide_actors': SHEEWANA_GROUP}, {'set': {'var': {'map_var': 'sheewana_hidden'}, 'value': 1}}],
              'notes': "Sheewana goes home once her topic has freed her (sheewana_freed 113206): her body is hidden."})
    E.append({'id': 'evt:pen_lever', 'preset': 'switch', 'source': 'switch:pen_lever', 'title': 'Lever',
              'toggles': [g['id'] for g in PRISONER_GATES.values()], 'effects': [{'lua': PEN_LEVER}],
              'notes': "poi:pen_lever (D-27): two states, the four cages open and shut together; 'You hear a rumbling in the distance.' (dark/aaze0073:15). The first opening sets prisoners_freed (117121)."})
    for key in PRISONER_GATES:
        E.append({'id': f'evt:prisoner_{key}', 'preset': 'script', 'source': PRISONER_GATES[key]['id'],
                  'title': {'nathan': 'Nathan the Prisoner', 'sky': 'Sky the Prisoner', 'snog': 'Snog the Orc',
                            'alicia': 'Alicia the Just'}[key],
                  'lua': prisoner_lua(key),
                  'notes': f"poi:prisoners: NPC {NPC[key]} talks through the opened cage (A3's topic: thanks, 500 XP once). Words needed: an indoor monster with an npc id."})
    E.append({'id': 'evt:prisoners_gone', 'preset': 'script', 'trigger': 'load', 'lua': PRISONERS_GONE,
              'notes': "D-27: once the cages have been opened, the prisoners are gone on the next entry. A load inside a visit (a saved game) finds in_visit set (saved with the map) and leaves them; leaving clears it (evt:visit_end), so only a fresh entry hides them."})
    E.append({'id': 'evt:visit_end', 'preset': 'script', 'trigger': 'leave',
              'effects': [{'set': {'var': {'map_var': 'in_visit'}, 'value': 0}}],
              'notes': "Leaving ends the visit: the next load is a fresh entry (evt:prisoners_gone)."})
    E.append({'id': 'evt:red_flask', 'preset': 'script', 'source': 'deco:red_flask', 'title': 'Red flask',
              'lua': flask_lua(BIT_RED, 'BaseMight', 'Might'),
              'notes': "poi:flasks: Red Potion (dark/aaze0073:8-9, '+5 Might (permanent).' rescaled to +2), once per character (player bit 11315)."})
    E.append({'id': 'evt:blue_flask', 'preset': 'script', 'source': 'deco:blue_flask', 'title': 'Blue flask',
              'lua': flask_lua(BIT_BLUE, 'BasePersonality', 'Personality'),
              'notes': "poi:flasks: Blue Potion (dark/aaze0073:10-11, rescaled to +2), once per character (player bit 11316)."})
    for key, title, text in (('history', 'History of Bark', HISTORY), ('sap', 'Book of Sap', BOOK_SAP),
                             ('ceremonies', 'Morning Ceremonies', CEREMONIES)):
        E.append({'id': f'evt:book_{key}', 'preset': 'script', 'source': f'panel:book_{key}', 'title': title,
                  'effects': [{'message': text}], 'notes': "poi:books (dark/aaze0073:24-30)."})
    E.append({'id': 'evt:black_barrel', 'preset': 'script', 'source': 'deco:black_barrel', 'title': 'Black barrel',
              'condition': {'not': {'player_bit': BIT_BARREL}},
              'else_effects': [{'text': "The black sludge has done all it will do to you."}],
              'question': dict(BARREL_Q), 'lua': BARREL,
              'notes': "poi:black_barrel (D-27; dark/aaze0074:4-9): once per character (player bit 11317): +1 to all seven stats and one year of age (the event age variable; an AgingImmunity item, the Jewel of Ages, protects, D-2.4)."})
    E.append({'id': 'evt:danger', 'preset': 'text', 'source': 'panel:danger', 'title': 'Sign', 'window': False,
              'text': "Danger: Unpredictable Effects.", 'notes': "The black barrel's sign (dark/aaze0074:7)."})
    E.append({'id': 'evt:ledger', 'preset': 'script', 'source': 'platform:ledger', 'title': 'Ledger',
              'effects': [{'message': LEDGER}], 'notes': "poi:ledger (dark/aaze0073:19-20)."})
    E.append({'id': 'evt:kettle', 'preset': 'script', 'source': 'deco:kettle', 'title': 'Kettle', 'lua': KETTLE,
              'notes': "poi:kettle (D-27): A3's q-d10.kettle (the source's invitation, dark/aaze0075:17), then 'Drink?'; Yes: q-d10.kettle_drunk and the drinker is poisoned; repeatable."})
    E.append({'id': 'evt:cabinet', 'preset': 'text', 'source': 'panel:cabinet', 'title': 'Cabinet', 'window': False,
              'text': "Nothing here.", 'notes': "dark/aaze0075:1."})
    for side in ('west', 'north', 'east'):
        E.append({'id': f'evt:dial_{side}', 'preset': 'script', 'source': f'panel:dial_{side}', 'title': 'Dial',
                  'lua': dial_lua(f'dial_{side}'),
                  'notes': "poi:dials (D-27): 'Dial reads N. Turn?' (dark/aaze0076:10-13); a map variable 0-3 shows 1-4; turning a dial undoes the lever."})
    E.append({'id': 'evt:asc_lever', 'preset': 'switch', 'source': 'switch:asc_lever', 'title': 'Lever',
              'effects': [{'lua': ASC_LEVER}],
              'notes': "poi:asc_lever: with the dials at west 1, north 2, east 3 the Crystal Water clears (lever_pulled); otherwise 'Nothing happens.' (D-27)."})
    E.append({'id': 'evt:crystal_water', 'preset': 'script', 'source': 'platform:crystal_water', 'title': 'Crystal Water',
              'lua': CRYSTAL,
              'notes': "poi:crystal_water: before the lever 'The water is stagnant.' (dark/aaze0076:9); after it A3's once-hook q-d10.crystal_water (disciples 113216, award 418 for every member); then its else text. The vault's door reads disciples."})
    E.append({'id': 'evt:dark_water', 'preset': 'script', 'source': 'platform:dark_water', 'title': 'Dark Water',
              'lua': DARK,
              'notes': "poi:dark_water (D-27): A3's q-d10.dark_water; the drinker is poisoned and loses about a tenth of the hit points, never the last 10."})
    E.append({'id': 'evt:book_ascension', 'preset': 'script', 'source': 'platform:lectern', 'title': 'Book of Ascension',
              'lua': 'XeenQuests.hook("q-d10.book_of_ascension")',
              'notes': "poi:book_ascension: A3's text (dark/aaze0076:2, naming the Crystal Water, D-27)."})
    for key in FOUNTAINS:
        E.append({'id': f'evt:fountain_{key}', 'preset': 'script', 'source': f'platform:fountain_{key}', 'title': 'Fountain',
                  'lua': fountain_lua(key),
                  'notes': f"poi:fountains (D-37): +5 to the clicking member, once per character (player bit {FOUNTAIN_BITS[key]}); 'The water is cool, clear and refreshing.' (dark/aaze0077:2), then '... You have had your fill.'"})
    for c in ('sap', 'shaalth', 'vault', 'treasure'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    return E


def wiring():
    return {'format': 0,
            'variables': ['voice_heard', 'limb_1_fed', 'limb_2_fed', 'limb_3_fed', 'barkman_woken', 'barkman_shown',
                          'cage_moved', 'sheewana_hidden', 'pens_open', 'prisoners_gone', 'dial_west', 'dial_north',
                          'dial_east', 'lever_pulled', 'in_visit'],
            'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-09's events, written by output/studio_cal/dd09/tools/dress.py."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
