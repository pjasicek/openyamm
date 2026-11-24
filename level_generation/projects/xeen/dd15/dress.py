#!/usr/bin/env python3
"""DD-15 Great Pyramid, L4: objects.yml and wiring.yml (written by gen.py L4)."""
import geo

TOMB, GUARD, ROYAL, GHOST = 11270, 11271, 11272, 11273
PHARAOH, PHARAOH_NPC, PHARAOH_GROUP = 11919, 5453, 50
NAME = {TOMB: 'tomb', GUARD: 'guard', ROYAL: 'royal', GHOST: 'ghost'}
MUMMY_GROUP = 1
# The four torches: (chapel room, wall, map qbit name, hidden pair's group, atrium brazier)
TORCHES = {
    'ne': ('chapel_ne', 'n', 'torch_ne', 21, 'atrium_ne'),
    'nw': ('chapel_nw', 'n', 'torch_nw', 22, 'atrium_nw'),
    'sw': ('chapel_sw', 's', 'torch_sw', 23, 'atrium_sw'),
    'se': ('chapel_se', 's', 'torch_se', 24, 'atrium_se'),
}
TORCH_QBITS = {'ne': 117561, 'nw': 117562, 'sw': 117563, 'se': 117564}
# The niche pairs (two hidden Tomb Mummies before each chapel's niches, D-61 Q2)
NICHE_PAIRS = {'nw': [[-4416, 4672], [-4416, 4032]], 'ne': [[4416, 4032], [4416, 4672]],
               'sw': [[-3392, -2816], [-3392, -3328]], 'se': [[2496, -3520], [3136, -3520]]}

ARRIVAL_AT = [0, 4736]                    # entrance:d5_door (the brief's point)
SKY_ARRIVAL_AT = [0, 2944]                # entrance:d7_sky, 256 inside the sky door, facing the throne
D7_SKY = (11424, 2560, 1408, 1024)        # D7's entrance:dd15_sky (assets_dev/worlds/xeen/maps/xeen_d7.studio.yml)
HALL_LANDING = [-960, 640]                # where every pad back sets the party down (pad_w, facing the pads)

SAND = [235, 200, 150]
GOLDL = [240, 210, 140]
STEEL = [170, 190, 210]
FIRE = [255, 150, 70]


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
DOUBLE = {
    'chapel_nw': ('open:chapel_nw', [[dict(geo.DRSML, fit=True), dict(geo.DRSMR, fit=True)]],
                  "The north-west chapel's double doors from Reception: two hinged leaves, Horus on each (egydrsml|egydrsmr)."),
    'chapel_ne': ('open:chapel_ne', [[dict(geo.DRSML, fit=True), dict(geo.DRSMR, fit=True)]],
                  "The north-east chapel's double doors from Information (egydrsml|egydrsmr)."),
    'south_atrium': ('open:south_atrium', [[dict(geo.DRSML, fit=True), dict(geo.DRSMR, fit=True)]],
                     "The atrium's south door onto the south gallery (egydrsml|egydrsmr)."),
    'tomb_w': ('open:tomb_w', [[dict(geo.DRSML, fit=True), dict(geo.DRSMR, fit=True)]],
               "The west tomb's double doors from the processional."),
    'tomb_e': ('open:tomb_e', [[dict(geo.DRSML, fit=True), dict(geo.DRSMR, fit=True)]],
               "The east tomb's double doors from the processional."),
    'throne': ('open:throne', [[dict(geo.DRLGL, fit=True), dict(geo.DRLGR, fit=True)]],
               "The throne hall's great doors: the seated Pharaoh (egydrlgl) and his queen (egydrlgr), each leaf 384 square."),
}
SINGLE = [
    # key, opening, surface, title, notes
    ('reception', 'open:entry_reception', geo.DRSMC, 'Reception', "Door sign 'Reception' (aaze0083:1)."),
    ('information', 'open:entry_information', geo.DRSMC, 'Information', "Door sign 'Information' (aaze0083:4)."),
    ('numbers_information', 'open:numbers_information', geo.DRSMC, 'Door', "The number hall's door into Information."),
    ('overseer', 'open:overseer', geo.DRSMC, "Overseer's Office", "Door sign 'Overseer's Office' (aaze0083:2)."),
    ('cloister_registry', 'open:cloister_registry', geo.DRSMC, 'Door', "The cloister's door beside the registry."),
    ('embalmers', 'open:embalmers', geo.DRSMC, 'Door', "The embalmers' room off the stair head."),
    ('apex', 'open:apex', geo.SWDOOR, 'Door', "The far cell's steel door onto the apex stair."),
    ('ante', 'open:ante', geo.DRSMC, 'Door', "The antechamber's door from the apex landing."),
    ('bedchamber', 'open:bedchamber', geo.DRSMC, 'Bedchamber', "The bedchamber's door from the throne hall."),
]


def doors():
    out = []
    pyr = [[dict(geo.PYRDOR, fit=True), dict(geo.PYRDOR, fit=True)]]
    out.append({'id': 'door:green', 'opening': 'open:green', 'kind': 'hinged', 'leaves': 2,
                'surface': geo.S_('7solid01', 128, 256, fit=True), 'back_surface': dict(geo.PYRDOR, fit=True),
                'notes': "The green doors (A6's xdpyrdor: one wing, mirrored on the right leaf): clicked, the exit preset ('Exit the Great Pyramid?', aaze0083:0). They stay shut."})
    out.append({'id': 'door:stair', 'opening': 'open:stair', 'kind': 'hinged', 'leaves': 2,
                'surface': dict(geo.PYRDOR, fit=True), 'back_surface': dict(geo.PYRDOR, fit=True),
                'notes': "The stair door: two leaves of xdpyrdor; 'Access denied!' (aaze0083:12) until the four torches burn (m28.torches, 111561), then open for good."})
    del pyr
    for k, (op, pics, n) in DOUBLE.items():
        out.append({'id': f'door:{k}', 'opening': op, 'kind': 'hinged', 'leaves': 2, 'pictures': [[{k2: v for k2, v in p.items() if k2 != 'fit'} for p in row] for row in pics],
                    'back_pictures': [[{k2: v for k2, v in p.items() if k2 != 'fit'} for p in row] for row in pics], 'notes': n})
    for k, op, s, t, n in SINGLE:
        out.append({'id': f'door:{k}', 'opening': op, 'kind': 'slide_left', 'surface': dict(s, fit=True), 'notes': n})
    out.append({'id': 'door:vault', 'opening': 'open:vault', 'kind': 'slide_left', 'surface': dict(geo.DRSMD, fit=True),
                'notes': "The Overseer's vault door: locked until the eight niches are answered (117573)."})
    out.append({'id': 'door:registry', 'opening': 'open:registry', 'kind': 'slide_up', 'surface': dict(geo.DRSMD, fit=True),
                'notes': "The bronze registry door: its lock asks 'Registry?' (m28.registry_lock: 1701 or NCC-1701); it slides up and stays up (111562)."})
    out.append({'id': 'door:lift_gate', 'opening': 'open:lift_top', 'kind': 'slide_up', 'surface': dict(geo.GRILLE, scale=1.5), 'tile': True,
                'notes': "The gilded cage's gate at the top (L4): shut while the cage is down, opened with its climb."})
    out.append({'id': 'door:secret_sky', 'opening': 'open:bed_sky', 'kind': 'slide_left', 'secret': True,
                'surface': dict(geo.WLC, fit=True), 'back_surface': dict(geo.SWWALL, fit=True),
                'notes': "The secret way from the bedchamber to the sky corridor: the carved button slides it open for good (117575)."})
    return out


def lifts():
    return [{'id': 'lift:cage', 'room': R('shaft'), 'at': [256, -3584], 'size': [384, 384], 'travel': geo.L4 - geo.L1,
             'thickness': 16, 'speed': 480, 'surface': dict(geo.GOLD),
             'notes': "The Pharaoh's gilded cage: a floor 384 square riding the shaft between the grand stair (down, L1) and the antechamber (up, L4). D-61 Q4: it runs only once the party has entered the throne hall (117577)."}]


def switches():
    out = []
    for k, (room, wall, qn, grp, atr) in TORCHES.items():
        out.append({'id': f'switch:torch_{k}', 'room': R(room), 'kind': 'plate', 'wall': wall, 'along': 0.5,
                    'height': 128, 'size': [64, 64], 'off': dict(geo.SWOFF), 'on': geo.SWON['texture'],
                    'notes': f"The {k} torch's lever (egyswbof, lit egyswbon): one way (D-43)."})
    out += [
        {'id': 'switch:call_foot', 'room': R('stair_foot'), 'kind': 'button', 'at': [-128, -4032], 'height': 112,
         'notes': "Call button beside the cage's mouth at the foot of the grand stair."},
        {'id': 'switch:call_top', 'room': R('ante_s'), 'kind': 'button', 'at': [640, -3200], 'height': 112,
         'notes': "Call button beside the cage's gate in the antechamber."},
        {'id': 'switch:ride_up', 'room': R('shaft'), 'kind': 'button', 'at': [512, -3584], 'floor_height': geo.L1,
         'height': 112, 'notes': "Inside the cage at the foot: sends it up."},
        {'id': 'switch:ride_down', 'room': R('shaft'), 'kind': 'button', 'at': [512, -3584], 'floor_height': geo.L1,
         'height': geo.L4 - geo.L1 + 112, 'notes': "Inside the cage at the top, in reach of a rider: sends it down."},
        {'id': 'switch:button', 'room': R('bedchamber'), 'kind': 'button', 'at': [1664, 2048], 'height': 112,
         'notes': "The carved button on the bedchamber's west wall (the source's L4 button)."},
    ]
    return out


def plate(pid, room, at, size=(256, 256), surface=None, notes=None):
    d = {'id': pid, 'room': R(room), 'at': list(at), 'size': list(size)}
    if surface:
        d['surface'] = dict(surface)
    if notes:
        d['notes'] = notes
    return d


def cell_spots(room):
    x0, y0, x1, y1 = geo.bbox(room)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    return cx, cy


# Each cell: where the party lands, its pad back, and (the bird cell) the second bird.
CELLS = {}
for _c in ('cell_a', 'cell_b', 'cell_c', 'cell_d', 'cell_e'):
    _cx, _cy = cell_spots(_c)
    CELLS[_c] = {'arrive': [_cx - 256, _cy + 256], 'back': [_cx + 256, _cy - 256]}
CELLS['cell_e']['back'] = [CELLS['cell_e']['arrive'][0], CELLS['cell_e']['back'][1]]   # away from the stair door
BIRD2_AT = [CELLS['cell_d']['arrive'][0], CELLS['cell_d']['back'][1]]
PAD_TO = {'sun': 'cell_a', 'eye': 'cell_b', 'scarab': 'cell_c', 'bird': 'cell_d'}


def plates():
    out = []
    for name, (room, at, surf) in geo.PADS.items():
        out.append(plate(f'plate:pad_{name}', room, at, surface=surf,
                         notes=f"The {name} pad: to {PAD_TO[name]} (an in-map move)."))
    for c, s in CELLS.items():
        out.append(plate(f'plate:back_{c}', c, s['back'], surface=geo.PAD_BACK, notes="The pad back to the pad hall."))
    out.append(plate('plate:pad_bird2', 'cell_d', BIRD2_AT, surface=dict(geo.FLORB, scale=2),
                     notes="The second bird: on to the far cell."))
    # approach plates before the statues (the source's 'The statue speaks as you approach it')
    out += [plate(f'plate:{k}', room, at, notes=f"Before the {k} statue.") for k, (room, at) in STATUE_PLATES.items()]
    return out


def chests():
    return [
        {'id': 'chest:safe', 'room': R('bedchamber'), 'at': [2880, 1536], 'treasure_level': 5,
         'random_items': 3, 'gold': 3000, 'notes': "The wall safe (D-61 Q7): its three prompts, 20-30-1, then it opens (117574)."},
        {'id': 'chest:strongbox', 'room': R('information'), 'at': [2000, 1192], 'treasure_level': 5,
         'random_items': 2, 'gold': 1500, 'notes': "The visitors' strongbox behind the counter (the source's find at (23, 15))."},
        {'id': 'chest:vault', 'room': R('vault'), 'at': [4224, -4736], 'facing': 'n', 'treasure_level': 5,
         'random_items': 3, 'gold': 2500, 'notes': "The Overseer's vault: the chest and the visitors' fees (optional, D-61 Q3)."},
        {'id': 'chest:tomb_w', 'room': R('tomb_w'), 'at': [-2432, -1696], 'treasure_level': 5,
         'random_items': 3, 'gold': 1200, 'notes': "The west tomb's grave goods."},
        {'id': 'chest:sun', 'room': R('cell_a'), 'at': [-2432, -336], 'treasure_level': 5,
         'random_items': 3, 'gold': 1500, 'notes': "The sun cell's chest."},
    ]


T, G, GH, RM = TOMB, GUARD, GHOST, ROYAL
PLACED = {
    # L1 (30, incl. the eight niche mummies below)
    'reception': [(T, [-3584, 1792]), (T, [-2560, 2816]), (T, [-2304, 1664])],
    'information': [(T, [2304, 1792]), (T, [3712, 1792]), (G, [2560, 2432])],
    'atrium_nw': [(T, [-384, 1792])], 'atrium_ne': [(G, [384, 1792])],
    'atrium_sw': [(G, [-640, -256])], 'atrium_se': [(T, [640, 128])],
    'west_gal_n': [(T, [-2816, 256])], 'west_gal_s': [(T, [-2816, -1536])],
    'chapel_sw': [(G, [-2816, -3072])],
    'south_gal_w': [(T, [-960, -2304]), (G, [-1536, -1920])],
    'south_gal_e': [(G, [960, -2304]), (G, [1536, -2688])],
    'chapel_se': [(G, [2816, -3072])],
    'number_s': [(T, [3072, -1856]), (G, [3072, -1024])],
    'number_n': [(T, [3072, 640]), (G, [3072, -128])],
    # L2 (20)
    'proc_1': [(G, [-896, -768])], 'proc_3': [(G, [-896, 1792])],
    'tomb_w': [(T, [-2688, -1024]), (T, [-2688, 0]), (T, [-2432, 640]), (G, [-2048, -512]), (G, [-2048, 384])],
    'tomb_e': [(T, [384, 0]), (T, [384, 1152]), (T, [1536, -256]), (G, [1408, 1152]), (G, [512, -320])],
    'cloister_s': [(T, [832, 1920]), (G, [832, 2432])],
    'cloister_n': [(T, [832, 3456]), (G, [832, 2944]), (GH, [1536, 2944])],
    'embalmers': [(T, [-3328, -2304]), (T, [-2304, -2304]), (GH, [-3328, -2944])],
    # L3 (12)
    'pad_w': [(T, [-1216, 256])], 'pad_c': [(GH, [-128, 128])], 'pad_e': [(GH, [1600, 512]), (T, [960, 128])],
    'cell_b': [(GH, [2944, -512]), (GH, [2432, -1024])],
    'cell_c': [(G, [2688, 640]), (G, [2432, 384])],
    'cell_d': [(G, [384, -1920]), (G, [128, -2176])],
    'cell_e': [(T, [1792, -1920]), (T, [1792, -2176])],
    # L4 (8)
    'apex_landing': [(RM, [2432, -640]), (RM, [2816, -640])],
    'ante_s': [(RM, [256, -2304]), (RM, [1280, -2304]), (G, [1408, -2816])],
    'ante_n': [(RM, [256, -1216]), (RM, [1280, -1600]), (G, [-384, -1920])],
}


def monsters():
    out = []
    n = {}
    for room, lst in PLACED.items():
        for row, at in lst:
            n[(room, row)] = n.get((room, row), 0) + 1
            out.append({'id': f'monster:{room}_{NAME[row]}_{n[(room, row)]}', 'room': R(room), 'monster': row,
                        'at': at, 'facing': 270, 'group': MUMMY_GROUP})
    for k, pts in NICHE_PAIRS.items():
        room, wall, qn, grp, atr = TORCHES[k]
        for i, at in enumerate(pts, 1):
            out.append({'id': f'monster:niche_{k}_{i}', 'room': R(room), 'monster': TOMB, 'at': at, 'facing': 270,
                        'group': grp, 'hidden': True,
                        'notes': f"A warden in the {k} chapel's niche (D-61 Q2): placed hidden, shown by the {k} torch's lever and on every load once lit; counted in the 70."})
    out.append({'id': 'monster:pharaoh', 'room': R('throne_n'), 'monster': PHARAOH, 'at': [geo.THRONE_AT[0], 1600],
                'floor_height': geo.L4 + 48, 'facing': 270, 'hostile': False, 'group': PHARAOH_GROUP, 'immobile': True,
                'npc': PHARAOH_NPC,
                'notes': "The Dragon Pharaoh (11919, S's P5 figure, D-56/D-61) before his throne on the dais, npc 5453: clicked, A3's topics (M28 The orb, M30, M36). Peaceful, immobile, uncounted; unkillable (evt:figures_load)."})
    return out


# The talking statues (geo.STATUE_PANELS: a figure in a niche on a wall) and the step plate before each.
STATUE_PLATES = {'history': ('reception', [-4048, 1408]), 'torch_statue': ('atrium_se', [640, -1024]),
                 'rule_s': ('number_s', [2304, -1312]), 'rule_n': ('number_n', [2304, 352]),
                 'verse_1': ('proc_1', [-1280, -1120]), 'verse_2': ('proc_2', [-512, 768]),
                 'verse_3': ('proc_3', [-1280, 1760]), 'verse_4': ('proc_3', [-512, 2144])}
PROPS = [
    # (key, decoration, room, at, floor height, hangs)
    ('salts', 'dec97', 'embalmers', [-2688, -2624], geo.L2 + 80, False),
    ('jar_1', 'dec97', 'embalmers', [-3456, -3072], None, False),
    ('jar_2', 'dec97', 'embalmers', [-3456, -2176], None, False),
    ('urn_1', 'dec97', 'tomb_e', [1664, 1408], None, False),
    ('urn_2', 'dec97', 'tomb_e', [1664, -384], None, False),
    ('urn_3', 'dec97', 'tomb_w', [-3584, 1024], None, False),
    ('urn_4', 'dec97', 'tomb_w', [-1792, -1664], None, False),
    ('bones_1', '7dec18', 'cell_e', [1152, -2560], None, False),
    ('bones_2', 'dec29', 'cell_b', [3072, -1152], None, False),
    ('vault_urn', 'dec97', 'vault', [3840, -4736], None, False),
]
SCONCES = [
    ('entry', 'w', 0.3), ('entry', 'e', 0.7), ('reception', 'w', 0.15), ('reception', 'n', 0.3),
    ('information', 'e', 0.85), ('information', 's', 0.2), ('west_gal_n', 'w', 0.5), ('west_gal_s', 'w', 0.5),
    ('south_gal_w', 's', 0.75), ('south_gal_e', 's', 0.5), ('number_s', 'w', 0.3), ('number_n', 'w', 0.7),
    ('overseer', 'n', 0.5), ('stair_foot', 's', 0.5), ('chapel_nw', 's', 0.25), ('chapel_ne', 's', 0.75),
    ('chapel_sw', 'w', 0.1), ('chapel_se', 'e', 0.9),
    ('landing', 's', 0.3), ('proc_1', 'w', 0.8), ('proc_2', 'e', 0.8), ('proc_3', 'w', 0.2), ('registry', 'n', 0.5),
    ('tomb_w', 'w', 0.9), ('tomb_e', 'e', 0.5), ('cloister_n', 'e', 0.5), ('cloister_s', 'e', 0.3),
    ('embalmers', 'w', 0.5), ('registry_stair', 'e', 0.15),
    ('apex_landing', 'e', 0.5), ('ante_s', 'w', 0.5), ('ante_n', 'w', 0.5), ('ante_n', 'e', 0.2),
    ('throne_s', 'w', 0.5), ('throne_s', 'e', 0.5), ('throne_c', 'w', 0.5), ('throne_c', 'e', 0.5),
    ('bedchamber', 'e', 0.75),
]


def decorations():
    out = []
    for key, dec, room, at, fh, hangs in PROPS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at}
        if fh is not None:
            d['floor_height'] = fh
        if hangs:
            d['hangs'] = True
        out.append(d)
    for k, (room, wall, qn, grp, atr) in TORCHES.items():
        out.append({'id': f'deco:torch_{k}', 'room': R(room), 'decoration': 'torch01', 'wall': wall, 'along': 0.5,
                    'height': 288, 'hidden': True, 'notes': f"The {k} torch over its lever: shown when lit."})
        out.append({'id': f'deco:brazier_{k}', 'room': R(atr), 'decoration': 'flamb00', 'at': geo.BRAZIERS[k],
                    'floor_height': geo.L1 + 64, 'hidden': True,
                    'notes': f"The atrium's {k} brazier burning on its stand: shown with the {k} torch."})
    for i, (room, wall, along) in enumerate(SCONCES):
        out.append({'id': f'deco:sconce_{i}', 'room': R(room), 'decoration': 'torch01', 'wall': wall, 'along': along,
                    'height': 224})
    return out


THEME_COL = {'theme:hall': SAND, 'theme:reception': SAND, 'theme:atrium': GOLDL, 'theme:chapel': SAND,
             'theme:gallery': SAND, 'theme:numbers': SAND, 'theme:office': SAND, 'theme:stair': SAND,
             'theme:processional': GOLDL, 'theme:tomb': SAND, 'theme:ancient': STEEL, 'theme:royal': GOLDL}
# Two-storey rooms: their light in the open part, under the head.
OPEN_AT = {'stair_foot': ([-896, -4352], 448), 'registry_stair': ([-2240, 2816], 448),
           'apex_stair': ([2432, -2304], 448), 'shaft': ([256, -3584], 320)}
DIM = {'porch': 0.0, 'cell_a': 0.7, 'cell_b': 0.7, 'cell_c': 0.7, 'cell_d': 0.7, 'cell_e': 0.7}
# Lights off-centre where a pillar or a platform stands in the middle.
AT = {'cloister_s': [832, 2176], 'cloister_n': [832, 3200], 'throne_n': [640, 1408], 'tomb_e': [384, 512],
      'ante_s': [704, -2560], 'ante_n': [704, -1408]}


def lights():
    L = []

    def add(room, at, radius, color, height=None, notes=None, on=True, lid=None):
        d = {'id': lid or f'light:{room}_{sum(1 for x in L if x["room"] == R(room)) + 1}', 'room': R(room), 'at': at,
             'radius': radius, 'color': color}
        if height:
            d['height'] = height
        if not on:
            d['on'] = False
        if notes:
            d['notes'] = notes
        L.append(d)
    for room in geo.ORDER:
        if DIM.get(room, 1) == 0:
            continue
        (w, h), c = geo.extent(room)
        col = THEME_COL[geo.R[room][4]]
        if room in OPEN_AT:
            at, hh = OPEN_AT[room]
            add(room, at, 1100, col, height=hh)
            continue
        if room == 'sky_corridor':
            add(room, [0, 2560], 900, STEEL, height=320)
            continue
        r = int(min(2000, max(700, 0.6 * max(w, h))) * DIM.get(room, 1))
        add(room, AT.get(room, list(c)), r, col, height=384 if geo.R[room][3] - geo.R[room][2] > 512 else 320)
    for k, (room, wall, qn, grp, atr) in TORCHES.items():
        add(atr, list(geo.BRAZIERS[k]), 900, FIRE, height=224, on=False, lid=f'light:brazier_{k}',
            notes=f"The {k} brazier's fire: dark until the {k} torch is lit.")
    add('throne_n', [512, 1664], 600, [150, 255, 170], height=200, notes="The Brew of Pure Power's glow.")
    return L


def sounds():
    return [
        {'id': 'sound:bed_l1_n', 'room': R('entry'), 'at': [0, 3584], 'sound': 'xeen_amb_necropolis', 'radius': 5200,
         'inner_radius': 3000, 'volume': 0.3, 'pan': False, 'notes': "The tomb's bed (MM6's VARN mood), L1's north half: not panned (D-48)."},
        {'id': 'sound:bed_l1_s', 'room': R('south_gal_w'), 'at': [-960, -2304], 'sound': 'xeen_amb_necropolis',
         'radius': 5200, 'inner_radius': 3000, 'volume': 0.3, 'pan': False, 'notes': "L1's south half."},
        {'id': 'sound:bed_l2', 'room': R('proc_2'), 'at': [-896, 256], 'sound': 'xeen_amb_necropolis', 'radius': 4600,
         'inner_radius': 2800, 'volume': 0.3, 'pan': False, 'notes': "The registry level."},
        {'id': 'sound:bed_l3', 'room': R('pad_c'), 'at': [192, 0], 'sound': 'xeen_barrier_loop', 'radius': 3600,
         'inner_radius': 2200, 'volume': 0.2, 'pan': False, 'notes': "The Ancients' hum over the pad maze."},
        {'id': 'sound:bed_l4', 'room': R('throne_c'), 'at': [0, 704], 'sound': 'xeen_amb_necropolis', 'radius': 3600,
         'inner_radius': 2400, 'volume': 0.25, 'pan': False, 'notes': "The apartments."},
        {'id': 'sound:vat', 'room': R('throne_n'), 'at': geo.VAT_AT, 'sound': 'bubbling cauldron01', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.5, 'notes': "The Brew of Pure Power bubbling (a point sound; AU's own later)."},
        {'id': 'sound:sky_wind', 'room': R('sky_corridor'), 'at': [0, 3072], 'sound': 'whistling wind', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.35, 'notes': "Wind at the sky door."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('entry'), 'at': ARRIVAL_AT, 'facing': 's',
                  'notes': "Inside the green doors, about 384 in, facing south into the pyramid."},
        'arrivals': [
            {'entrance': 'entrance:d5_door', 'room': R('entry'), 'at': ARRIVAL_AT, 'facing': 's',
             'notes': "From D5's green door (A6's door:dd15, m28.door): (0, 4736, 0) facing south (1536)."},
            {'entrance': 'entrance:d7_sky', 'room': R('sky_corridor'), 'at': SKY_ARRIVAL_AT, 'facing': 's',
             'notes': "From D7's sky door (door:dd15, after m30.done): 256 inside the sky door, facing the throne."},
        ],
        'doors': doors(), 'lifts': lifts(), 'switches': switches(), 'plates': plates(), 'chests': chests(),
        'monsters': monsters(), 'decorations': decorations(), 'lights': lights(), 'sounds': sounds(),
        'notes': "DD-15's contents, written by output/studio_cal/dd15/tools/dress.py: 21 doors (eight of them hinged pairs), the Pharaoh's lift, four torch levers, five lift and button switches, ten pads, five chests, 70 placed monsters (34 Tomb Mummies, eight of them hidden in the torch chapels' niches; 24 Pyramid Guards, 6 Ghost Mummies, 6 Royal Mummies) and, not counted, the Dragon Pharaoh (npc 5453).",
    }


# ------------------------------------------------------------------------------------------------- wiring
# The verse statues' lines (dark/aaze0084:1-4, map-local; the other statues are A3's hooks).
LINES = {
    'verse_1': "1 - Total the dates is all you do\nThen minus the number thirty-two",
    'verse_2': "2 - Now take the answer, divide by three\nYour mission is the pharoah to free",
    'verse_3': "3 - Then subtract another forty-two\nThis final number can get you through",
    'verse_4': "4 - Type in the passcode you now should know\nTo quickly get from this level below",
}
NICHES = (3, 4, 5, 6, 7, 8, 9, 10)     # the niches' numbers; niche n is A3's Xeen.pyramidNiche(n - 2)


def torch_lua(k):
    bits = ' and '.join(f'IsQBitSet(QBit({b}))' for b in TORCH_QBITS.values())
    return "\n".join([
        'evt.PlaySoundName("xeen_torch_light")',
        f'if {bits} and not IsQBitSet(QBit(111561)) then',
        '    XeenQuests.hook("m28.torches")',
        'end',
    ])


# The wall safe is chest index 0 (the first of objects.yml `chests`).
SAFE_CHEST_INDEX = 0
STATUE_HOOKS = {'welcome': 'm28.welcome_statue', 'history': 'm28.history_statue', 'torch_statue': 'm28.torch_statue',
                'rule_s': 'm28.rule_statue_1', 'rule_n': 'm28.rule_statue_2'}


def events():
    E = []
    # arrival, the exit, the figures
    E.append({'id': 'evt:welcome_first', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'arrived_once'}},
              'effects': [{'qbit': 'arrived_once'}, {'lua': 'XeenQuests.hook("m28.welcome_statue")'}],
              'notes': "The welcome statue greets the party on its first arrival (A3's m28.welcome_statue, dark/aaze0083:6; first arrival 117560); clicked, again."})
    E.append({'id': 'evt:exit_green', 'preset': 'script', 'source': 'door:green', 'title': 'Exit the Great Pyramid',
              'effects': [{'exit': 'exit:d5_door'}],
              'notes': "The green doors: the game's own leave window (D-24; 'Exit the Great Pyramid?', aaze0083:0) to D5's entrance:dd15_door (0, -7168, 1248) facing 512."})
    E.append({'id': 'evt:figures_load', 'preset': 'script', 'trigger': 'load',
              'lua': 'evt.SetMm9ActorCanReceiveDamage(ActorIndex("monster:pharaoh"), false)',
              'notes': "The Dragon Pharaoh cannot be hurt (D-56, D-61; as P5)."})
    # statues
    for key in geo.STATUE_PANELS:
        title = 'Statue'
        hook = STATUE_HOOKS.get(key)
        if hook:
            E.append({'id': f'evt:{key}', 'preset': 'script', 'source': f'panel:statue_{key}', 'title': title,
                      'lua': f'XeenQuests.hook("{hook}")', 'notes': f"A statue: A3's {hook} (clicked)."})
            if key != 'welcome':
                E.append({'id': f'evt:{key}_step', 'preset': 'script', 'trigger': 'step', 'source': f'plate:{key}',
                          'lua': f'XeenQuests.hook("{hook}")',
                          'notes': f"The statue speaks as the party approaches it: A3's {hook}."})
            continue
        E.append({'id': f'evt:{key}', 'preset': 'text', 'source': f'panel:statue_{key}', 'title': title, 'window': True,
                  'text': LINES[key], 'notes': "A verse statue's line (dark/aaze0084:1-4, map-local)."})
        E.append({'id': f'evt:{key}_step', 'preset': 'text', 'trigger': 'step', 'source': f'plate:{key}',
                  'text': LINES[key].replace('\n', ' '), 'seconds': 6,
                  'notes': "The verse statue speaks as the party passes (a status line; clicked, the window)."})
    # the torches
    for k, (room, wall, qn, grp, atr) in TORCHES.items():
        E.append({'id': f'evt:torch_{k}', 'preset': 'switch', 'source': f'switch:torch_{k}', 'title': 'Lever',
                  'condition': {'not': {'qbit': qn}},
                  'effects': [{'qbit': qn}, {'show_actors': grp}, {'show': f'deco:torch_{k}'},
                              {'show': f'deco:brazier_{k}'}, {'lights_on': f'light:brazier_{k}'},
                              {'text': "The torch flares up. In the niches, something stirs!"}],
                  'lua': torch_lua(k), 'locked_text': "The lever is stuck.",
                  'notes': f"The {k} torch (D-61 Q2): one way; lights its torch and the atrium's {k} brazier, shows the chapel's two niche mummies (group {grp}); a second pull 'The lever is stuck.' (aaze0083:39). The last of the four calls m28.torches."})
        E.append({'id': f'evt:torch_{k}_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': qn},
                  'effects': [{'show_actors': grp}, {'show': f'deco:torch_{k}'}, {'show': f'deco:brazier_{k}'},
                              {'lights_on': f'light:brazier_{k}'}],
                  'notes': f"A lit {k} torch stays lit, and its niche pair shown, on every load (D-18)."})
    E.append({'id': 'evt:torch_plaque', 'preset': 'script', 'source': 'panel:torch_plaque', 'title': 'Plaque',
              'lua': 'XeenQuests.hook("m28.torch_plaque")', 'notes': "A3's m28.torch_plaque."})
    E.append({'id': 'evt:door_stair', 'preset': 'door', 'source': 'door:stair', 'title': 'Door',
              'condition': {'lua': 'XeenQuests.can("m28.stair_door")'},
              'else_effects': [{'lua': 'XeenQuests.hook("m28.stair_door")'}],
              'notes': "The stair door: A3's m28.stair_door ('Access denied!', aaze0083:12) until m28.torches (111561)."})
    E.append({'id': 'evt:stair_open', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'torches', 'not': {'map_var': 'stair_open'}}, 'opens': ['door:stair'],
              'effects': [{'set': {'var': {'map_var': 'stair_open'}, 'value': 1}}],
              'notes': "The stair door opens once the four torches burn (also after a refill)."})
    # the number hall (optional)
    for n in NICHES:
        E.append({'id': f'evt:niche_{n}', 'preset': 'script', 'source': f'panel:niche_{n}', 'title': 'Niche',
                  'lua': f'Xeen.pyramidNiche({n - 2}, eventId, continueStep)',
                  'notes': f"Niche {n} (A3's Xeen.pyramidNiche({n - 2}): dark/aaze0083:13-38, 'Correct!' / 'Wrong!'; the eighth calls m28.niches, vault_open 117573)."})
    E.append({'id': 'evt:door_vault', 'preset': 'door', 'source': 'door:vault', 'title': 'Vault',
              'condition': {'qbit': 'vault_open'}, 'locked_text': "The vault door is locked. Eight numbers bolt it.",
              'notes': "The Overseer's vault: opens once the eight niches are answered."})
    E.append({'id': 'evt:vault_open', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'vault_open', 'not': {'map_var': 'vault_door'}}, 'opens': ['door:vault'],
              'effects': [{'set': {'var': {'map_var': 'vault_door'}, 'value': 1}}],
              'notes': "The vault door opens once 117573 is set."})
    E.append({'id': 'evt:note', 'preset': 'script', 'source': 'platform:desk', 'title': 'Note',
              'lua': 'XeenQuests.hook("m28.overseer_note")', 'notes': "The Overseer's note: A3's m28.overseer_note (the niches' answer-giver)."})
    # the registry
    E.append({'id': 'evt:registry', 'preset': 'script', 'source': 'door:registry', 'title': 'Registry door',
              'condition': {'not': {'qbit': 'registry'}},
              'question': {'message': "A bronze door with a lock of numbered keys. Above it, in raised letters: STARFLEET REGISTRY NUMBER NCC.",
                           'ask': "Registry?", 'answers': ['1701', 'NCC-1701', 'NCC1701', 'NCC 1701'],
                           'wrong_text': "Incorrect!"},
              'opens': ['door:registry'], 'effects': [{'lua': 'XeenQuests.hook("m28.registry_lock")'}],
              'else_effects': [{'text': "The registry door stands open."}],
              'notes': "m28.registry_lock (111562): 1701 or NCC-1701 (the source's prompt, aaze0084:5-6); else 'Incorrect!' (aaze0084:7)."})
    E.append({'id': 'evt:registry_open', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'registry', 'not': {'map_var': 'registry_door'}}, 'opens': ['door:registry'],
              'effects': [{'set': {'var': {'map_var': 'registry_door'}, 'value': 1}}],
              'notes': "The registry door stays open once 111562 is set."})
    E.append({'id': 'evt:registry_plaque', 'preset': 'script', 'source': 'panel:registry_plaque', 'title': 'Plaque',
              'lua': 'XeenQuests.hook("m28.registry_plaque")', 'notes': "A3's m28.registry_plaque (xdregplq)."})
    # the embalmers' find
    E.append({'id': 'evt:salts', 'preset': 'script', 'source': 'deco:salts', 'title': 'Jar',
              'condition': {'not': {'map_var': 'salts_found'}}, 'else_effects': [{'text': "Nothing here."}],
              'effects': [{'set': {'var': {'map_var': 'salts_found'}, 'value': 1}}, {'gold': 400},
                          {'text': "A jar of embalming salts, and a purse the embalmers hid under it. (+400 gold)"}],
              'notes': "The embalmers' room's find, once."})
    # the pad maze
    E.append({'id': 'evt:maze', 'preset': 'script', 'trigger': 'step', 'source': 'room:pad_w',
              'sources': ['room:pad_c', 'room:pad_e'], 'condition': {'not': {'qbit': 'maze_seen'}},
              'effects': [{'lua': 'XeenQuests.hook("m28.maze")'}],
              'notes': "m28.maze on the first arrival in the pad hall (117576)."})
    names = {'cell_a': 'sun', 'cell_b': 'eye', 'cell_c': 'scarab', 'cell_d': 'bird'}
    for name, cell in PAD_TO.items():
        x, y = CELLS[cell]['arrive']
        E.append({'id': f'evt:pad_{name}', 'preset': 'teleport', 'trigger': 'step', 'source': f'plate:pad_{name}',
                  'to': [x, y, geo.L3], 'direction': 270, 'lua': 'evt.PlaySoundName("Teleport")',
                  'text': f"The glyph of the {name} flares beneath you, and the hall is gone.",
                  'notes': f"The {name} pad: to the {names[cell]} cell."})
    x, y = CELLS['cell_e']['arrive']
    E.append({'id': 'evt:pad_bird2', 'preset': 'teleport', 'trigger': 'step', 'source': 'plate:pad_bird2',
              'to': [x, y, geo.L3], 'direction': 270, 'lua': 'evt.PlaySoundName("Teleport")',
              'text': "The second bird flares beneath you.", 'notes': "The bird cell's second pad: to the far cell."})
    for c in CELLS:
        E.append({'id': f'evt:back_{c}', 'preset': 'teleport', 'trigger': 'step', 'source': f'plate:back_{c}',
                  'to': [HALL_LANDING[0], HALL_LANDING[1], geo.L3], 'direction': 270,
                  'lua': 'evt.PlaySoundName("Teleport")', 'text': "The pad sets you down in the pad hall.",
                  'notes': "Every cell's pad back to the pad hall (D-61)."})
    E.append({'id': 'evt:pad_map', 'preset': 'script', 'source': 'panel:pad_map', 'title': "The Overseer's map",
              'lua': 'XeenQuests.hook("m28.pad_map")', 'notes': "The eye cell's find: A3's m28.pad_map (the maze's answer-giver)."})
    E.append({'id': 'evt:rack', 'preset': 'script', 'source': 'platform:weapon_rack', 'title': 'Weapon rack',
              'condition': {'not': {'qbit': 'scarab_find'}}, 'else_effects': [{'text': "Nothing here."}],
              'effects': [{'qbit': 'scarab_find'}, {'give_item': {'level': 5, 'kind': 20}},
                          {'text': "Among the guards' rusted spears, one weapon is worth taking."}],
              'notes': "The scarab cell's find (D-61 APPROVAL): one random T5 weapon once (117578), then 'Nothing here.'."})
    # the lift
    for sid, op, line, ok in (
            ('call_foot', 'closes', "A gilded cage. It answers only to the Pharaoh's guests.", "The gilded cage sinks down the shaft to you."),
            ('call_top', 'opens', "A gilded cage. It answers only to the Pharaoh's guests.", "The gilded cage climbs the shaft to you."),
            ('ride_up', 'opens', "A gilded cage. It answers only to the Pharaoh's guests.", "The gilded cage climbs to the Pharaoh's apartments."),
            ('ride_down', 'closes', "A gilded cage. It answers only to the Pharaoh's guests.", "The gilded cage sinks to the grand stair.")):
        E.append({'id': f'evt:{sid}', 'preset': 'switch', 'source': f'switch:{sid}',
                  'title': 'Call the lift' if sid.startswith('call') else ('Lift: up' if sid == 'ride_up' else 'Lift: down'),
                  'condition': {'lua': 'XeenQuests.can("m28.lift")'}, op: ['lift:cage', 'door:lift_gate'],
                  'effects': [{'lua': 'evt.PlaySoundName("xeen_lift", 256, -3584, 1152)'}],
                  'else_effects': [{'lua': 'XeenQuests.hook("m28.lift")'}], 'text': ok,
                  'notes': "The Pharaoh's lift (D-61 Q4): both ways after the first entry into the throne hall (117577); before it the cage's line."})
    E.append({'id': 'evt:throne_reached', 'preset': 'script', 'trigger': 'step', 'source': 'room:throne_s',
              'sources': ['room:throne_c', 'room:throne_n'], 'condition': {'not': {'qbit': 'throne_reached'}},
              'effects': [{'lua': 'XeenQuests.hook("m28.audience")'}],
              'notes': "The first entry into the throne hall (117577): the Pharaoh's lift wakes."})
    # the apartments
    E.append({'id': 'evt:book', 'preset': 'script', 'source': 'platform:book_stand', 'title': 'Book',
              'lua': 'XeenQuests.hook("m28.prime_directive")',
              'notes': "The Prime Directive (A3's m28.prime_directive; D-61 Q8: the source's three directives, a second read aaze0086:31)."})
    E.append({'id': 'evt:brew_reset', 'preset': 'script', 'trigger': 'load',
              'effects': [{'set': {'var': {'map_var': 'brew_warned'}, 'value': 0}}],
              'notes': "Each visit starts with the Pharaoh's warning (D-61 Q6 (b))."})
    E.append({'id': 'evt:brew', 'preset': 'script', 'source': 'platform:vat', 'title': 'Bubbling Vat',
              'condition': {'not': {'map_var': 'brew_warned'}},
              'effects': [{'set': {'var': {'map_var': 'brew_warned'}, 'value': 1}}, {'lua': 'XeenQuests.hook("m28.brew")'}],
              'else_effects': [{'lua': 'evt.PlaySoundName("xeen_fire_ignite")'}, {'lua': 'XeenQuests.hook("m28.brew_drink")'}],
              'notes': "The Brew of Pure Power (D-61 Q6 (b)): the first click in a visit the Pharaoh's warning (aaze0086:0); a second drinks: 50 fire damage to the clicking member, 'He did warn you.'. No reward."})
    E.append({'id': 'evt:throne', 'preset': 'text', 'source': 'platform:throne', 'title': 'Throne', 'window': False,
              'text': "The Pharaoh's throne. He is using it.", 'notes': "The throne."})
    E.append({'id': 'evt:bed', 'preset': 'text', 'source': 'platform:bed', 'title': 'Ornate Bed', 'window': False,
              'text': "Nothing here.", 'notes': "The ornate bed (aaze0086:2-3)."})
    E.append({'id': 'evt:tapestry', 'preset': 'script', 'source': 'panel:tapestry', 'title': 'Tapestry',
              'lua': 'XeenQuests.hook("m28.tapestry")', 'notes': "The tapestry (aaze0086:6): A3's m28.tapestry, the safe's numbers (D-61 Q7)."})
    E.append({'id': 'evt:safe', 'preset': 'script', 'source': 'chest:safe', 'title': 'Wall Safe',
              'lua': f'if Xeen.pharaohSafe(eventId, continueStep) then\n    evt.OpenChest({SAFE_CHEST_INDEX})\nend',
              'notes': "The wall safe (D-61 Q7): 'Enter Combination.  Left?' 20, 'Right?' 30, 'Left?' 1 (aaze0086:20-29); right: the chest (117574); wrong: 'No Luck.' (aaze0086:19)."})
    E.append({'id': 'evt:button', 'preset': 'switch', 'source': 'switch:button', 'title': 'Button',
              'condition': {'not': {'qbit': 'button'}}, 'opens': ['door:secret_sky'], 'sets': {'qbit': 'button'},
              'text': "Click. Beside the button, a panel of the wall slides aside.",
              'locked_text': "The button is pressed in.",
              'notes': "The carved button (aaze0086:4): the secret way to the sky corridor, for good (117575)."})
    E.append({'id': 'evt:secret_open', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'button', 'not': {'map_var': 'secret_door'}}, 'opens': ['door:secret_sky'],
              'effects': [{'set': {'var': {'map_var': 'secret_door'}, 'value': 1}}],
              'notes': "The secret way stays open once 117575 is set."})
    E.append({'id': 'evt:sky_door', 'preset': 'script', 'source': 'panel:sky_door', 'title': 'Sky door',
              'condition': {'lua': 'XeenQuests.hook("d7.sky_door_dd15")'},
              'effects': [{'exit': 'exit:d7_sky'}],
              'notes': "The sky door (D-58, D-61 Q9): before m30.done the hook's 'Access Denied!' (aaze0086:5); after it the standard entrance window (F16, 2026-11-22: OK/Close, no Yes/No): OK out to D7's entrance:dd15_sky (11424, 2560, 1408) facing 1024."})
    # doors and chests
    for k in DOUBLE:
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}',
                  'title': {'throne': 'Great doors', 'south_atrium': "Visitor's Atrium"}.get(k, 'Double doors')})
    for k, op, s, t, n in SINGLE:
        e = {'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}', 'title': t}
        if k == 'ante':
            # D-89 (INWARD, 2026-11-22): the Queen's pyramid key opens the antechamber's door on L4 (and the Pharaoh's
            # lift); L1-L3 are open to clear. The hook shows its own refusal line.
            e['condition'] = {'lua': 'XeenQuests.hook("m28.antechamber_door")'}
            e['notes'] = "D-89: A3's m28.antechamber_door (the Queen's pyramid_key 12348; else its line naming Queen Kalindra)."
        E.append(e)
    for c in ('strongbox', 'vault', 'tomb_w', 'sun'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    return E


def wiring():
    vars_ = ['stair_open', 'vault_door', 'registry_door', 'secret_door', 'salts_found', 'brew_warned']
    return {'format': 0, 'variables': vars_, 'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-15's events, written by output/studio_cal/dd15/tools/dress.py."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
