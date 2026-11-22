#!/usr/bin/env python3
"""DD-18 Sandcaster Sewer, L4: objects.yml, wiring.yml (written by gen.py L4)."""
import geo
from geo import S_

STALKER, MATRIARCH, ASP, KCOBRA, MWARRIOR, MQUEEN = 11401, 11402, 11490, 11491, 11371, 11372
NAME = {STALKER: 'stalker', MATRIARCH: 'matriarch', ASP: 'asp', KCOBRA: 'killer_cobra', MWARRIOR: 'mantis',
        MQUEEN: 'queen'}

BIT_VITAMIN, BIT_PROTEIN = 11318, 11319

LAMP = [215, 180, 120]
SAND = [205, 175, 125]
TUNNEL = [180, 165, 140]
NESTC = [175, 150, 110]
DAY = [215, 205, 180]


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
DOORS = [
    # id, opening, notes
    ('shaft_drain', 'open:shaft_drain', "A lattice door from the shaft into the main drain."),
    ('shaft_gym', 'open:shaft_gym', "The members' room's door under Barticus' sign."),
    ('warren_cistern', 'open:warren_cistern', "A lattice door from the warren into the great cistern."),
    ('drain_alcoves', 'open:drain_alcoves', "A lattice door from the main drain to the alcoves."),
    ('cobra_cistern', 'open:cobra_cistern', "A lattice door from the cobra drain into the great cistern."),
    ('nest_drowned', 'open:nest_drowned', "An old lattice door between the mantis nest and the drowned vault."),
    ('tunnel_gate', 'open:tunnel_gate', "A lattice door at the long tunnel's end, before the desert gate."),
]


def doors():
    return [{'id': f'door:{k}', 'opening': op, 'kind': 'slide_up', 'surface': dict(geo.DOOR, fit=True), 'notes': n}
            for k, op, n in DOORS]


def chests():
    return [
        {'id': 'chest:cistern', 'room': R('cistern'), 'at': [7616, 448], 'facing': 'w', 'treasure_level': 3,
         'random_items': 2, 'gold': 600, 'notes': "Under the overflow's grated mouth on the cistern's east wall."},
        {'id': 'chest:alcove', 'room': R('niche_2'), 'at': [2240, -2048], 'facing': 'n', 'treasure_level': 3,
         'random_items': 2, 'gold': 400, 'notes': "The one alcove that holds something."},
        {'id': 'chest:nest', 'room': R('mantis_nest'), 'at': [4608, -9088], 'treasure_level': 3,
         'random_items': 3, 'gold': 900, 'notes': "What the ants dragged in."},
        {'id': 'chest:strongbox', 'room': R('drowned'), 'at': [1536, -6272], 'facing': 's', 'treasure_level': 3,
         'random_items': 2, 'gold': 700, 'notes': "An old strongbox in the drowned vault's dry corner."},
        {'id': 'chest:pack', 'room': R('desert_gate'), 'at': [-7936, -6144], 'treasure_level': 3,
         'random_items': 2, 'gold': 500,
         'notes': "A sand-buried prospector's pack at the grate's foot (D-27's find)."},
    ]


PLACED = {
    'main_drain': [(STALKER, [1280, -240]), (STALKER, [1920, 240]), (STALKER, [2560, -240]), (STALKER, [3072, 240])],
    'warren': [(STALKER, [3968, -448]), (STALKER, [4736, -448]), (STALKER, [3968, 448]), (STALKER, [4736, 448]),
               (MATRIARCH, [4352, 0])],
    'breeding_vault': [(STALKER, [4096, 1600]), (STALKER, [4608, 1600]), (MATRIARCH, [4352, 1344])],
    'cistern': [(STALKER, [5632, -1152]), (STALKER, [5632, 1024]), (STALKER, [7424, -1152]), (STALKER, [7424, 1024]),
                (ASP, [6528, -1024]), (ASP, [6528, 768])],
    'alcoves': [(STALKER, [2240, -960]), (STALKER, [3072, -960])],
    'cobra_drain': [(ASP, [3840, -1280]), (ASP, [4224, -1792]), (ASP, [4608, -1280]), (ASP, [4992, -1792]),
                    (ASP, [3840, -1792]), (ASP, [4608, -1792]), (KCOBRA, [4224, -1280]), (KCOBRA, [4992, -1280])],
    'collapse': [(ASP, [5632, -2048]), (ASP, [7424, -2048]), (KCOBRA, [6016, -2688]), (KCOBRA, [7040, -2688]),
                 (MATRIARCH, [5632, -2880]), (MATRIARCH, [7168, -2432])],
    'mantis_gallery': [(MWARRIOR, [4096, -5248]), (MWARRIOR, [4608, -5248]), (MWARRIOR, [5120, -5248]),
                       (MWARRIOR, [4096, -6144]), (MWARRIOR, [4608, -5760]), (MWARRIOR, [5120, -6144])],
    'mantis_nest': [(MWARRIOR, [3968, -7424]), (MWARRIOR, [5248, -7424]), (MQUEEN, [4608, -7936]),
                    (MQUEEN, [4096, -8576]), (MQUEEN, [5120, -8576])],
    'egg_cells': [(MWARRIOR, [6144, -7808]), (MWARRIOR, [6656, -8320]), (MQUEEN, [6400, -8064])],
    'tunnel_east': [(MWARRIOR, [512, -5696]), (MWARRIOR, [1408, -5696])],
}


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at in lst:
            n[row] = n.get(row, 0) + 1
            out.append({'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                        'facing': 270, 'hostile': True, 'group': 1})
    return out


# key: (decoration, room, at, floor height or None, title)
DECOS = [
    ('vitamin_brew', 'dec35', 'gym', [-128, -1712], geo.SHELF_RISE, 'Vitamin Brew'),
    ('protein_brew', 'bucket', 'gym', [128, -1712], geo.SHELF_RISE, 'Protein Brew'),
    ('milestone', '6rock04', 'tunnel_head', [7232, -6208], None, 'Milestone'),
]
PROPS = [
    ('gym_barrel_1', 'bigbarel', 'gym', [704, -1600]),
    ('gym_barrel_2', 'bigbarel', 'gym', [704, -1408]),
    ('warren_heap_1', 'trasheap', 'warren', [3840, 704]),
    ('warren_heap_2', '7dec10', 'breeding_vault', [4672, 1792]),
    ('warren_bones', 'dec29', 'warren', [4928, -640]),
    ('collapse_rock_1', '6rock01', 'collapse', [5440, -2560]),
    ('collapse_rock_2', '6rock03', 'collapse', [7616, -2048]),
    ('collapse_rock_3', '6rock05', 'collapse', [5440, -1856]),
    ('nest_dirt_1', '7dec11', 'mantis_nest', [3712, -8192]),
    ('nest_dirt_2', '7dec11', 'mantis_nest', [5376, -8704]),
    ('nest_bones', 'dec19', 'mantis_nest', [3712, -8576]),
    ('eggs_dirt', '7dec11', 'egg_cells', [6720, -7616]),
    ('eggs_bones', '7dec18', 'egg_cells', [6080, -8512]),
    ('drift_sand_1', '7dec11', 'sand_drift', [-2240, -5376]),
    ('drift_sand_2', '7dec11', 'sand_drift', [-1152, -6016]),
    ('gate_sand', '7dec11', 'desert_gate', [-7936, -5248]),
    ('gallery_rock', '7rock03', 'mantis_gallery', [5312, -5056]),
]
# lights audit (merge point 14): the alcoves' north torch moved from 0.8 (on the main drain's lattice door) to 0.55
TORCHES = [('gym', 'n', 0.2), ('gym', 'n', 0.8), ('gym', 'e', 0.5), ('gym', 'w', 0.85), ('shaft', 'e', 0.25),
           ('main_drain', 's', 0.3), ('main_drain', 'n', 0.75), ('cistern', 'w', 0.25), ('cistern', 'w', 0.8),
           ('cistern', 'e', 0.2), ('alcoves', 'n', 0.55), ('cobra_drain', 'n', 0.5), ('tunnel_head', 'e', 0.5),
           ('tunnel_east', 'n', 0.2), ('tunnel_east', 'n', 0.6), ('sand_drift', 's', 0.5), ('tunnel_west', 'n', 0.3),
           ('tunnel_west', 'n', 0.8), ('drowned', 'w', 0.5)]


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
                    'height': 224})
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
    for room in geo.R:
        (w, h), c = geo.extent(room)
        if room == 'shaft':
            add(room, c, 1000, DAY, height=1100, notes="Daylight down through the street lid's grate.")
            continue
        if room == 'desert_gate':
            add(room, [-7424, -5696], 1200, DAY, height=384, notes="Daylight through the desert grate.")
            continue
        col = SAND if geo.R[room][2] == 0 else TUNNEL
        if room in ('mantis_gallery', 'mantis_nest', 'egg_cells', 'warren', 'breeding_vault'):
            col = NESTC
        if room == 'gym':
            col = LAMP
        r = int(min(2000, max(700, 0.6 * max(w, h))))
        if max(w, h) > 2400:
            ax = 0 if w >= h else 1
            for f in (0.25, 0.75):
                p = list(c)
                lo = c[ax] - (w if ax == 0 else h) / 2
                p[ax] = int(lo + f * (w if ax == 0 else h))
                add(room, p, int(r * 0.7), col)
        else:
            add(room, c, r, col)
    return L


def sounds():
    return [
        {'id': 'sound:main_drain', 'room': R('main_drain'), 'at': [1984, 0], 'sound': 'water lapping loop',
         'radius': 1600, 'inner_radius': 500, 'volume': 0.35, 'notes': "The channel's slow water."},
        {'id': 'sound:cobra_drain', 'room': R('cobra_drain'), 'at': [4352, -1536], 'sound': 'water lapping loop',
         'radius': 1400, 'inner_radius': 400, 'volume': 0.35, 'notes': "The warm drain's water."},
        {'id': 'sound:cistern', 'room': R('cistern'), 'at': [6528, -288], 'sound': 'drip02', 'radius': 1800,
         'inner_radius': 500, 'volume': 0.5, 'wait': [2, 6], 'notes': "Drips into the cistern's pool."},
        {'id': 'sound:collapse', 'room': R('collapse'), 'at': [6528, -2432], 'sound': 'drip03', 'radius': 1300,
         'inner_radius': 400, 'volume': 0.4, 'wait': [3, 7], 'notes': "Water seeping into the broken drain."},
        {'id': 'sound:drowned', 'room': R('drowned'), 'at': [2112, -6912], 'sound': 'drip01', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.5, 'wait': [2, 6], 'notes': "The drowned vault dripping."},
        {'id': 'sound:sand_drift', 'room': R('sand_drift'), 'at': [-1664, -5696], 'sound': 'whistling wind',
         'radius': 1600, 'inner_radius': 400, 'volume': 0.25, 'notes': "The desert's air down the long tunnel."},
        {'id': 'sound:desert_gate', 'room': R('desert_gate'), 'at': [-7680, -5696], 'sound': 'whistling wind',
         'radius': 1400, 'inner_radius': 300, 'volume': 0.45, 'notes': "Sand blowing through the grate."},
        # AU's sewer bed (xeen_amb_sewer, 62800) over the drains and the wet tunnels, not the sand end (session 7).
        {'id': 'sound:bed_drains', 'room': R('alcoves'), 'at': [2304, -896], 'sound': 'xeen_amb_sewer', 'radius': 3200,
         'inner_radius': 1000, 'volume': 0.4, 'pan': False,
         'notes': "The sewer's trickles and drips (bed, west drains)."},
        {'id': 'sound:bed_cistern', 'room': R('cistern'), 'at': [6528, 512], 'sound': 'xeen_amb_sewer',
         'radius': 3200, 'inner_radius': 1000, 'volume': 0.4, 'pan': False,
         'notes': "The sewer's trickles and drips (bed, east)."},
        {'id': 'sound:bed_tunnel', 'room': R('tunnel_east'), 'at': [1664, -5696], 'sound': 'xeen_amb_sewer',
         'radius': 3000, 'inner_radius': 1000, 'volume': 0.35, 'pan': False,
         'notes': "The sewer's trickles and drips (bed, tunnel)."},
        {'id': 'sound:bed_nest', 'room': R('mantis_nest'), 'at': [4608, -7424], 'sound': 'xeen_amb_sewer',
         'radius': 3000, 'inner_radius': 1000, 'volume': 0.35, 'pan': False,
         'notes': "The sewer's trickles and drips (bed, nest)."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('shaft'), 'at': [0, 128], 'facing': 's',
                  'notes': "At the shaft ladder's foot, facing the members' room's door under Barticus' sign (D3's street shaft arrives here)."},
        'doors': doors(), 'chests': chests(), 'monsters': monsters(), 'decorations': decorations(), 'lights': lights(),
        'sounds': sounds(),
        'exits': [
            {'id': 'exit:shaft', 'room': R('shaft'), 'wall': 'north', 'size': [128, 256], 'surface': dict(geo.LADDER),
             'to': 'exit:d3_shaft', 'notes': "The iron ladder up to the street's lid beside Barticus' Gym (D3)."},
        ],
        # F14 (A8 session 26): rungs out of the great cistern's pool (96 deep), so a party that steps in climbs back.
        'ladders': [
            {'id': 'ladder:cistern_pool', 'room': R('cistern'), 'at': [6528, -16], 'facing': 'n', 'height': 96,
             'exit': [6528, 64], 'grab_at_top': True, 'surface': {'texture': 'bemv', 'size': [32, 256], 'uneven': True},
             'notes': "F14: iron rungs up the pool's north edge onto the cistern floor."},
        ],
        'notes': "DD-18's contents, written by output/studio_cal/dd18/tools/dress.py: 7 doors, five chests, 50 placed monsters (16 Sewer Stalkers, 4 Stalker Matriarchs, 10 Guardian Asps, 4 Killer Cobras, 12 Mantis Warriors, 4 Mantis Queens), the members' room's pay box, brews and book, the sealed desert grate.",
    }


# ------------------------------------------------------------------------------------------------- wiring
ARRIVAL = ("THE SANDCASTER SEWER. The ladder from the street ends by a door under Barticus' sign: his members' room, "
           "where the brews are kept. Barticus says the stalkers got in. East, the drains run round the city's old "
           "cistern, and they say there is a passage in the sewer that leads a long ways under the desert.")
PAY_Q = {'message': "It costs 5,000 gold to use the gym. Pay?", 'ask': "Pay (Yes/No)?", 'answers': ['Yes', 'Y'],
         'wrong_text': "Get lost!"}


def brew_lua(bit, var, hook):
    return "\n".join([
        'if not XeenQuests.hook("dd18.members_room") then',
        '    return',
        'end',
        'evt.ForPlayer(Players.Current)',
        f'if IsPlayerBitSet(PlayerBit({bit})) then',
        '    XeenQuests.hook("dd18.brew_again")',
        '    return',
        'end',
        f'AddValue({var}, 2)',
        f'SetPlayerBit(PlayerBit({bit}))',
        f'XeenQuests.hook("{hook}")',
    ])


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'arrived_once'}},
              'effects': [{'message': ARRIVAL}, {'qbit': 'arrived_once'}],
              'notes': "Say what is here (the members' room, the drains, the long tunnel; Barticus' town topic, D-27), on the first arrival only (arrived_once 117280)."})
    for k, op, n in DOORS:
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}', 'title': 'Door'})
    E.append({'id': 'evt:exit_shaft', 'preset': 'exit', 'source': 'exit:shaft', 'title': 'Ladder to the street',
              'notes': "The game's own leave window, up the ladder to D3's street shaft beside Barticus' Gym (D-24)."})
    E.append({'id': 'evt:paybox', 'preset': 'script', 'source': 'panel:paybox', 'title': 'Pay box',
              'condition': {'not': {'qbit': 'gym_paid'}}, 'question': dict(PAY_Q),
              'effects': [{'lua': 'XeenQuests.hook("dd18.pay_box")'}],
              'else_effects': [{'lua': 'XeenQuests.hook("dd18.pay_box")'}],
              'notes': "poi:paybox (D-27): 'It costs 50,000 gold to use the gym. Pay?' / 'Get lost!' (dark/aaze0032:3-4, the price rescaled); Yes runs A3's once-hook dd18.pay_box (5,000 gold, gym_paid 116120, 'Enjoy the facilities.'; short of gold the charity-gym refusal, dark/aaze0032:14); once paid the hook's 'Paid up.'"})
    E.append({'id': 'evt:vitamin_brew', 'preset': 'script', 'source': 'deco:vitamin_brew', 'title': 'Vitamin Brew',
              'lua': brew_lua(BIT_VITAMIN, 'BaseEndurance', 'dd18.vitamin_brew'),
              'notes': "Vitamin Brew (dark/aaze0032:8): members only (dd18.members_room); +2 Endurance once per character (player bit 11318), A3's text; again: dd18.brew_again."})
    E.append({'id': 'evt:protein_brew', 'preset': 'script', 'source': 'deco:protein_brew', 'title': 'Protein Brew',
              'lua': brew_lua(BIT_PROTEIN, 'BaseMight', 'dd18.protein_brew'),
              'notes': "Protein Brew (dark/aaze0032:9): members only; +2 Might once per character (player bit 11319)."})
    E.append({'id': 'evt:book', 'preset': 'script', 'source': 'platform:bench', 'title': 'The Art of Bodybuilding',
              'lua': 'if XeenQuests.hook("dd18.members_room") then XeenQuests.hook("dd18.bodybuilding") end',
              'notes': "The Art of Bodybuilding (dark/aaze0032:6) on the bench: members only; A3's text."})
    for k in ('alcove_1', 'alcove_3'):
        E.append({'id': f'evt:{k}', 'preset': 'text', 'source': f'panel:{k}', 'title': 'Alcove', 'window': False,
                  'text': "Nothing here.", 'notes': "'Alcove' (dark/aaze0032:11)."})
    for k in ('outlet_main', 'outlet_cistern', 'outlet_cobra'):
        E.append({'id': f'evt:{k}', 'preset': 'text', 'source': f'panel:{k}', 'title': 'Sewer Drain', 'window': False,
                  'text': "Water trickles through the grate from the city above.",
                  'notes': "'Sewer Drain' (dark/aaze0032:0)."})
    E.append({'id': 'evt:milestone', 'preset': 'text', 'source': 'deco:milestone', 'title': 'Milestone',
              'window': False, 'text': "Cut in the stone: TO THE DESERT.",
              'notes': "poi:milestone: the long tunnel's start."})
    E.append({'id': 'evt:desert_grate', 'preset': 'script', 'source': 'panel:desert_grate', 'title': 'Grate',
              'lua': 'XeenQuests.hook("dd18.tunnel_grate")',
              'notes': "poi:grate (D-27): bolted on the desert side; A3's dd18.tunnel_grate refuses with \"Sand blows through the bars. The bolt is on the other side.\" until D5's grate sets d5_tunnel (116121). Phase 5: this event becomes the exit preset to exit:d5_grate with condition {qbit: d5_tunnel} (project.yml neighbours, sealed)."})
    for c in ('cistern', 'alcove', 'nest', 'strongbox'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    E.append({'id': 'evt:chest_pack', 'preset': 'chest', 'source': 'chest:pack', 'title': 'Bag',
              'notes': "D-27's find at the grate's foot: a sand-buried prospector's pack (treasure 3)."})
    return E


def wiring():
    return {'format': 0, 'variables': [], 'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-18's events, written by output/studio_cal/dd18/tools/dress.py."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
