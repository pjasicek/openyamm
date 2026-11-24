#!/usr/bin/env python3
"""DD-17 Castle Alamar, L4: objects.yml, wiring.yml, atmosphere.yml (written by gen.py L4)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path

import yaml

import geo

PATROL, ANNIHILATOR, AUTOBOT = 11610, 11611, 11612
FIRE_EL, AIR_EL, WATER_EL, EARTH_EL = 11620, 11624, 11625, 11626
GAZER = 11572
SHELTEM, CORAK = 11924, 11912
NAME = {PATROL: 'patrol', ANNIHILATOR: 'annihilator', AUTOBOT: 'autobot', FIRE_EL: 'fire_el', AIR_EL: 'air_el',
        WATER_EL: 'water_el', EARTH_EL: 'earth_el', GAZER: 'gazer'}
GROUP = {PATROL: 1, ANNIHILATOR: 1, AUTOBOT: 1, GAZER: 2, FIRE_EL: 3, AIR_EL: 4, WATER_EL: 5, EARTH_EL: 6}
SHELTEM_GROUP, CORAK_GROUP = 40, 41
ELEMENTS = ('fire', 'air', 'water', 'earth')
EL_ROW = {'fire': FIRE_EL, 'air': AIR_EL, 'water': WATER_EL, 'earth': EARTH_EL}
DIAL_INDEX = {'fire': 1, 'air': 2, 'earth': 3, 'water': 4}     # Xeen.AlamarSundials' order (A3's helper)
DIAL_BIT = {'fire': 117611, 'air': 117612, 'water': 117613, 'earth': 117614}   # A3's dial_<el>_nine (m33.sundials)
QB = {'fire': 117601, 'air': 117602, 'water': 117603, 'earth': 117604}
EL_COLOR = {'fire': [255, 110, 60], 'air': [225, 235, 255], 'water': [90, 150, 255], 'earth': [110, 220, 110]}
TEAL_L = [120, 210, 200]
WHITE = [210, 225, 230]
RED = [230, 90, 80]

D6 = (-6656, 4608, 2208, 1536)
D7 = (-18688, 8448, 1536, 1024)
ARRIVAL_AT = [0, -3648]
ROOF_AT = [-2176, 1792]

L4 = Path(_REPO_ROOT + '/devdocs/xeen/briefs/dd17/L4')


def R(r):
    return 'room:' + r


def lock_number(kind, oid):
    """A number from the L4's ids.lock.yml (written by the first build), or None before it."""
    p = L4 / 'ids.lock.yml'
    if not p.exists():
        return None
    d = yaml.safe_load(p.read_text()) or {}
    return (d.get(kind) or {}).get(oid)


# ------------------------------------------------------------------------------------------------ objects
PAIRS = {
    'gate_hall': ('open:gate_hall', "The gate's inner leaves: a blast door (swdoora) on each leaf, the right one mirrored, parting in the middle."),
    'hall_stair': ('open:hall_stair', "The stair hall's two leaves from the Hall of Order: a blast door parting in the middle."),
    'ante_command': ('open:ante_command', "Command Central's two leaves (hover 'Command Central', aaze0051:3): a blast door parting in the middle."),
}
SINGLE = [
    ('ww_barracks', 'open:ww_barracks', geo.BRACEDOOR, "The barracks' door."),
    ('ew_store', 'open:ew_store', geo.BRACEDOOR, "The parts store's door."),
    ('ew_watch', 'open:ew_watch', geo.BRACEDOOR, "The moat watch's door."),
    ('ewalk_post', 'open:ewalk_post', geo.BRACEDOOR, "The watchers' post's door."),
    ('deck_bay', 'open:deck_bay', geo.BRACEDOOR, "The robot bay's door."),
    ('deck_screen', 'open:deck_screen', geo.BRACEDOOR, "The screen room's door."),
    ('west_juice', 'open:west_juice', geo.BRACEDOOR, "The Power Juice room's door."),
    ('west_ante', 'open:west_ante', geo.BRACEDOOR, "The antechamber's door."),
    ('west_hatch', 'open:west_hatch', geo.BRACEDOOR, "The hatch room's door."),
]
MAINT = {'fire': 'open:hfire_ret', 'water': 'open:hwater_ret', 'air': 'open:hair_ret', 'earth': 'open:hearth_ret'}
FIELDS = {'water': 'open:sw_dial', 'fire': 'open:nw_dial', 'air': 'open:ne_dial', 'earth': 'open:se_dial'}


TRAP_OFFSET = [96, 0]


def doors():
    out = []
    # D-91 (2026-11-22): each 224-wide leaf of a 448 opening shows the whole blast door, the right one mirrored (never
    # one picture split over the pair, D6's gate fault).
    wings = [[geo.S_('swdoora', 224, 448), geo.S_('swdoora', 224, 448, mirror=True)]]
    for k, (op, n) in PAIRS.items():
        out.append({'id': f'door:{k}', 'opening': op, 'kind': 'slide_left', 'leaves': 2,
                    'pictures': wings, 'back_pictures': wings, 'notes': n})
    out.append({'id': 'door:gate', 'opening': 'open:gate', 'kind': 'hinged', 'leaves': 2,
                'surface': dict(geo.GLYPH, fit=True),
                'notes': "The true-name gate: two hinged leaves of xaglyph (the left leaf's picture, mirrored on the right, completes the glyph ring); it opens on 'Sheltem' (m33.true_name_gate) and stays open."})
    for k, op, s, n in SINGLE:
        out.append({'id': f'door:{k}', 'opening': op, 'kind': 'slide_up', 'surface': dict(s, fit=True), 'notes': n})
    out.append({'id': 'door:sump', 'opening': 'open:sump_stair', 'kind': 'slide_up', 'surface': dict(geo.BRACEDOOR, fit=True),
                'notes': "The sump's door into the stair hall: its lever is on the sump's side."})
    out.append({'id': 'door:vault', 'opening': 'open:ante_vault', 'kind': 'slide_up', 'surface': dict(geo.BLAST, fit=True),
                'notes': "The strongroom's door: the robot bay's vault release raises it (117605)."})
    for el, op in MAINT.items():
        out.append({'id': f'door:maint_{el}', 'opening': op, 'kind': 'slide_left', 'surface': dict(geo.SEALED, fit=True),
                    'notes': f"The {el} Head's maintenance door to the return gallery: bolted on the Head's side (D-61 Q11)."})
    for el, op in FIELDS.items():
        out.append({'id': f'door:field_{el}', 'opening': op, 'kind': 'slide_down', 'fold': True, 'tile': True, 'speed': 256, 'surface': dict(geo.FIELD),
                    'notes': f"The {el} field (xafield, translucent 0.5, D-51) across the sundial alcove: it drops when the {el} Lava Head is shut down (one-way, D-43)."})
    return out


def lifts():
    out = [{'id': 'lift:core', 'room': R('lift_core'), 'at': geo.LIFT_AT, 'size': geo.LIFT_SIZE, 'travel': 640,
            'thickness': 16, 'speed': 320, 'surface': dict(geo.METALFLOOR),
            'notes': "The lift from the core (640) up through the lift head's floor to the deck (1280); it runs once gate_open 111661 is set."}]
    for el, at in geo.SLABS.items():
        out.append({'id': f'lift:slab_{el}', 'room': R('rings'), 'at': at, 'size': [240, 2 * geo.SLAB_Y], 'travel': 640,
                    'thickness': 32, 'speed': 200, 'surface': dict(geo.TEALPLATE),
                    'notes': f"The {el} chasm's bridge slab on the west line: on the chasm floor until the {el} dial reads nine, then level with the rims (640) (D-61 Q13, a two-state slab)."})
    for key, at in geo.TRAPS:
        # the plate's picture whole on its top: t6 sits half a picture off the others' grid (offset, audit
        # textures.feature_cut, 2026-11-22)
        plate = dict(geo.TRAPPLATE, scale=1.5, **({'offset': TRAP_OFFSET} if key == 't6' else {}))
        out.append({'id': f'lift:trap_{key}', 'room': R('rings'), 'at': at, 'size': [geo.TRAP_SIZE, geo.TRAP_SIZE],
                    'travel': 1280, 'thickness': 32, 'speed': 900, 'state': 'up', 'trap': True,
                    'surface': plate,
                    'notes': "A hatched deck plate (xatrapplt): a trapdoor that drops the party 1,280 to the chasm floor (D-61 Q18)."})
    return out


BELTS = {
    # el: (belt room, plate x, plate size, mouth y, mid y, landing y)
    'fire': ('belt_fire', -1920, [480, 192], -2240, 512, 1152),
    'water': ('belt_water', -3392, [608, 192], -2240, -1152, -384),
    'air': ('belt_air', 1920, [480, 192], -2240, 512, 1152),
    'earth': ('belt_earth', 3392, [608, 192], -2240, -1152, -384),
}
STATUE_PLATES = {'statue1': ('hall_order', [-1216, -2944]), 'statue2': ('north_walk', [352, 2368]),
                 'statue3': ('west_hall', [-2304, 832])}


def plates():
    out = []
    for el, (room, x, size, mouth, mid, land) in BELTS.items():
        out.append({'id': f'plate:belt_{el}_mouth', 'room': R(room), 'at': [x, mouth], 'size': size,
                    'notes': f"The {el} belt's mouth: the floor lurches and carries the party to the far end."})
        out.append({'id': f'plate:belt_{el}_back', 'room': R(room), 'at': [x, mid], 'size': size,
                    'notes': f"Near the {el} belt's far end: walking back down the belt carries the party forward again."})
    for k, (room, at) in STATUE_PLATES.items():
        out.append({'id': f'plate:{k}', 'room': R(room), 'at': at, 'size': [256, 192],
                    'notes': "Before a propaganda statue: it speaks as the party approaches."})
    out.append({'id': 'plate:come_to_me', 'room': R('west_hall'), 'at': [-1536, 0], 'size': [192, 384],
                'notes': "Inside the Hall of Vengeance from the deck: 'A voice bellows, \"Come to ME!\"' (aaze0051:2), once (117606)."})
    out.append({'id': 'plate:dais', 'room': R('command'), 'at': [-2272, -3072], 'size': [192, 320],
                'notes': "Before the dais: 'Before the throne. Open the Soul Box?' (D-61 Q16)."})
    return out


def switches():
    return [
        {'id': 'switch:lift_low', 'room': R('lift_core'), 'kind': 'button', 'at': [1792, 0], 'height': 112,
         'notes': "The lift's button on the core's east wall, beside the lift."},
        {'id': 'switch:lift_high', 'room': R('lift_top'), 'kind': 'button', 'at': [1792, 0], 'height': 112,
         'notes': "The lift's button on the lift head's east wall, beside the shaft."},
        {'id': 'switch:sump_lever', 'room': R('sump'), 'kind': 'lever', 'at': [-448, -1984], 'reach': 40,
         'notes': "The sump door's lever, on the sump's north wall."},
        {'id': 'switch:vault_release', 'room': R('robot_bay'), 'kind': 'lever', 'at': [1152, 2240], 'reach': 40,
         'notes': "The vault release on the robot bay's east wall: one-way (D-43), it raises the strongroom's door (117605)."},
    ]


def chests():
    return [
        {'id': 'chest:barracks', 'room': R('barracks'), 'at': [-3616, -3648], 'facing': 'e', 'treasure_level': 5,
         'random_items': 2, 'gold': 2500, 'notes': "Among the charging racks."},
        {'id': 'chest:watch', 'room': R('watch_se'), 'at': [3616, -3648], 'treasure_level': 5,
         'random_items': 2, 'gold': 2500, 'notes': "Under the moat watch's slit."},
        {'id': 'chest:store', 'room': R('store_ne'), 'at': [2112, -3808], 'facing': 'n', 'treasure_level': 5,
         'random_items': 2, 'gold': 2500, 'notes': "Behind the parts store's barrels."},
        {'id': 'chest:post', 'room': R('gazer_post'), 'at': [3744, 0], 'facing': 'w', 'treasure_level': 5,
         'random_items': 2, 'gold': 3000, 'notes': "In the watchers' glazed bay."},
        {'id': 'chest:robot_bay', 'room': R('robot_bay'), 'at': [576, 2720], 'facing': 's', 'treasure_level': 5,
         'random_items': 2, 'gold': 3000, 'notes': "At the robot bay's back wall."},
        {'id': 'chest:screen', 'room': R('gazer_watch'), 'at': [-1120, 2272], 'treasure_level': 5,
         'random_items': 2, 'gold': 3000, 'notes': "Under the screens."},
        {'id': 'chest:hoard', 'room': R('vault'), 'at': [-3360, -1792], 'facing': 'e', 'treasure_level': 6,
         'random_items': 3, 'gold': 8000, 'notes': "Sheltem's hoard in the strongroom (T6)."},
    ]


P, A, AU, G = PATROL, ANNIHILATOR, AUTOBOT, GAZER
PLACED = {
    'hall_order': [(P, [-1152, -2944]), (P, [1152, -2944]), (P, [0, -2880]), (A, [448, -2784])],
    'west_ward': [(P, [-2560, -2944]), (P, [-3200, -2816]), (A, [-2240, -2816])],
    'east_ward': [(P, [2560, -2944]), (P, [3200, -2816]), (A, [2240, -2816])],
    'barracks': [(P, [-3456, -3648]), (P, [-2816, -3648]), (A, [-3136, -3520])],
    'watch_se': [(P, [2944, -3648]), (P, [3456, -3520]), (G, [3200, -3648])],
    'store_ne': [(A, [1920, -3584]), (A, [2304, -3584])],
    'head_fire': [(FIRE_EL, [-2560, 2240]), (FIRE_EL, [-2048, 2240])],
    'head_water': [(WATER_EL, [-3520, 512]), (WATER_EL, [-3264, 512])],
    'head_air': [(AIR_EL, [2048, 2240]), (AIR_EL, [2560, 2240])],
    'head_earth': [(EARTH_EL, [3264, 512]), (EARTH_EL, [3520, 512])],
    'return_w': [(P, [-2624, -1024]), (P, [-2624, 640])],
    'return_e': [(P, [2624, -1024]), (P, [2624, 640])],
    'stair_hall': [(A, [960, -2112]), (A, [-32, -2304]), (AU, [960, -2368])],
    'landing_w': [(P, [-640, -2944])],
    'landing': [(P, [1280, -2944])],
    'bay_sw': [(P, [-1792, -2944]), (P, [-1792, -2048])],
    'west_walk': [(P, [-1792, -768]), (A, [-1920, 384]), (A, [-1792, 896])],
    'bay_nw': [(P, [-1792, 1792]), (P, [-1792, 2368])],
    'north_walk': [(A, [-512, 2336]), (A, [1280, 2336]), (G, [448, 2240])],
    'bay_ne': [(P, [2496, 1792]), (P, [2496, 2368])],
    'east_walk': [(P, [2496, -768]), (P, [2496, 768]), (A, [2496, 0])],
    'gazer_post': [(G, [3584, -256]), (G, [3584, 256]), (A, [3328, 0])],
    'bay_se': [(P, [2496, -2944]), (P, [2496, -2048])],
    'rings': [(AU, [896, -128]), (AU, [896, 128])],
    'deck': [(P, [-640, -768]), (P, [640, -1280]), (A, [-256, 1024]), (A, [768, 768]), (AU, [0, 0])],
    'robot_bay': [(A, [320, 2400]), (A, [832, 2400]), (AU, [576, 2208])],
    'gazer_watch': [(G, [-896, 2400]), (G, [-345, 2351])],   # F45: the east gazer out of sight of D7's landing
    'west_hall': [(A, [-2176, -512]), (A, [-1664, 512]), (AU, [-1920, -128])],
}
SHELTEM_AT, CORAK_AT = [-3616 / 1.3, -3072], [-3584 / 1.3, -3264]   # Sheltem before his throne (s17)


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at in lst:
            n[row] = n.get(row, 0) + 1
            d = {'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                 'facing': 270, 'group': GROUP[row]}
            if room == 'rings':
                d['floor_height'] = geo.RIM
                d['notes'] = "On the gate island (640)."
            out.append(d)
    out.append({'id': 'monster:sheltem', 'room': R('command_apse'), 'monster': SHELTEM, 'at': SHELTEM_AT, 'facing': 0,
                'hostile': False, 'group': SHELTEM_GROUP, 'immobile': True, 'hidden': True,
                'notes': "Sheltem (A2's row 11924, D-61 Q15) before his throne: peaceful, immobile, unkillable (evt:figures_load), not counted; hidden until the cinematic shows him."})
    out.append({'id': 'monster:corak', 'room': R('command_apse'), 'monster': CORAK, 'at': CORAK_AT, 'facing': 180,
                'hostile': False, 'group': CORAK_GROUP, 'immobile': True, 'hidden': True,
                'notes': "Corak (DD-16's row 11912) on the dais: peaceful, immobile, unkillable, not counted; hidden until the cinematic shows him stepping out of the Soul Box."})
    return out


DECOS = [
    # key, decoration, room, at, floor height, title (clicked) or None
    # session 17 (D-66 item 8): S's teal statues (own plinth) for MM6's sta1a, S's steel throne for the girder block
    ('statue1', 'xeen_statue_teal', 'hall_order', [-1216, -2720], geo.L1, 'Statue', 270),
    ('statue2', 'xeen_statue_teal', 'north_walk', [352, 2592], geo.L2, 'Statue', 270),
    ('statue3', 'xeen_statue_teal', 'west_hall', [-2304, 1088], geo.L3, 'Statue', 270),   # off the hatch door's line
    ('true_name_statue', 'xeen_statue_teal', 'rings', [768, -144], geo.RIM, 'Statue', 180),
    ('throne', 'xeen_throne_steel', 'command_apse', [geo.THRONE_AT[0], geo.THRONE_AT[1]], geo.L3 + 32, "Sheltem's throne", 0),
    ('sump_bones', 'dec29', 'sump', [-1088, -2368], None, 'Bones', None),
]
PROPS = [
    # the parts store (a storeroom): barrels and kegs along the walls
    ('store_1', 'bigbarel', 'store_ne', [1760, -3808]), ('store_2', 'bigbarel', 'store_ne', [1888, -3808]),
    ('store_3', 'smlbarel', 'store_ne', [1760, -3680]), ('store_4', 'bigbarel', 'store_ne', [2464, -3808]),
    ('store_5', 'bigbarel', 'store_ne', [2464, -3680]), ('store_6', 'smlbarel', 'store_ne', [2336, -3808]),
    ('store_7', 'smlbarel', 'store_ne', [2464, -3552]), ('store_8', 'bigbarel', 'store_ne', [1760, -3552]),
    # the barracks: a pair of kegs by the wall
    ('barracks_1', 'smlbarel', 'barracks', [-2656, -3808]), ('barracks_2', 'smlbarel', 'barracks', [-2656, -3680]),
    # the sump: bent plates and bones
    ('sump_bones_2', 'dec05', 'sump', [-448, -2368]),
]


def decorations():
    out = []
    for key, dec, room, at, fh, title, facing in DECOS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at}
        if fh is not None:
            d['floor_height'] = fh
        if facing is not None:
            d['facing'] = facing
        if title:
            d['notes'] = f"{title} (clicked: evt:{key})."
        out.append(d)
    for key, dec, room, at in PROPS:
        out.append({'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at})
    return out


THEME_COL = {'theme:works': TEAL_L, 'theme:main': TEAL_L, 'theme:belt': [130, 230, 150], 'theme:head': RED,
             'theme:store': WHITE, 'theme:sump': [150, 170, 160], 'theme:walk': TEAL_L, 'theme:bay': TEAL_L,
             'theme:dial': [150, 230, 170], 'theme:rings': TEAL_L, 'theme:deck': TEAL_L, 'theme:command': RED,
             'theme:hull': WHITE}
HEAD_ROOMS = {'fire': 'head_fire', 'air': 'head_air', 'water': 'head_water', 'earth': 'head_earth'}


def lights():
    L = []

    def add(room, at, radius, color, height=None, notes=None, lid=None, on=None):
        d = {'id': lid or f'light:{room}_{sum(1 for x in L if x["room"] == R(room)) + 1}', 'room': R(room), 'at': at,
             'radius': radius, 'color': color}
        if height is not None:
            d['height'] = height
        if on is not None:
            d['on'] = on
        if notes:
            d['notes'] = notes
        L.append(d)
    for room in geo.ORDER:
        if room in ('rings', 'stair_hall'):
            continue
        (w, h), c = geo.extent(room)
        col = THEME_COL[geo.R[room][4]]
        ch = geo.R[room][3] - geo.R[room][2]
        hh = min(320, ch - 96)
        if room in HEAD_ROOMS.values():
            el = next(e for e, r in HEAD_ROOMS.items() if r == room)
            add(room, c, 900, EL_COLOR[el], height=hh, lid=f'light:head_{el}',
                notes=f"The {el} Head's glow: it goes out when the Head is shut down.")
            add(room, c, 600, [140, 150, 150], height=hh)
            continue
        r = int(min(2000, max(700, 0.6 * max(w, h))))
        if max(w, h) > 2400:
            ax = 0 if w >= h else 1
            for f in (0.25, 0.75):
                p = list(c)
                lo = c[ax] - (w if ax == 0 else h) / 2
                p[ax] = int(lo + f * (w if ax == 0 else h))
                add(room, p, int(r * 0.75), col, height=hh)
        else:
            add(room, c, r, col, height=hh)
    # the stair hall: in its open part, under the head
    add('stair_hall', [256, -2400], 1100, TEAL_L, height=448)
    # the dial hall: each chasm lit in its element's colour (D-61's ring lips), over the rim, and a light over the lip
    for el in ELEMENTS:
        x0, x1 = geo.ch_west(el)
        a, b = geo.CH[el]
        add('rings', [(x0 + x1) // 2, 256 + (a + b) // 2], 900, EL_COLOR[el], height=720,
            notes=f"The {el} chasm's glow (north arm).")
        add('rings', [(x0 + x1) // 2, -256 - (a + b) // 2], 900, EL_COLOR[el], height=720,
            notes=f"The {el} chasm's glow (south arm).")
        add('rings', [(x0 + x1) // 2, 0], 500, EL_COLOR[el], height=200, notes=f"The {el} chasm's floor at the bridge line.")
    add('rings', [-1088, 0], 900, TEAL_L, height=900, notes="Over the lip.")
    add('rings', [896, 0], 800, WHITE, height=900, notes="Over the gate island.")
    return L


HUM_ROOMS = {'fire': 'head_fire', 'air': 'head_air', 'water': 'head_water', 'earth': 'head_earth'}


def sounds():
    out = []
    for el, room in HUM_ROOMS.items():
        (w, h), c = geo.extent(room)
        out.append({'id': f'sound:hum_{el}', 'room': R(room), 'at': c, 'sound': f'xeen_amb_plane_{el}', 'radius': 1100,
                    'inner_radius': 300, 'volume': 0.7 if el == 'earth' else 0.35,
                    'notes': f"The {el} Lava Head's roar: its element's plane bed (AU session 5) as a point sound; it stops when the Head is shut down (AmbientSound map variable)."})
    for el, room in (('fire', 'dial_fire'), ('air', 'dial_air'), ('water', 'dial_water'), ('earth', 'dial_earth')):
        bay = {'fire': 'bay_nw', 'air': 'bay_ne', 'water': 'bay_sw', 'earth': 'bay_se'}[el]
        (w, h), c = geo.extent(bay)
        out.append({'id': f'sound:field_{el}', 'room': R(bay), 'at': c, 'sound': 'xeen_barrier_loop', 'radius': 900,
                    'inner_radius': 200, 'volume': 0.35,
                    'notes': f"The {el} field's crackle; it stops when the field drops."})
    out += [
        {'id': 'sound:bed_works', 'room': R('hall_order'), 'at': [0, -2944], 'sound': 'xeen_machine_stamp_loop',
         'radius': 4200, 'inner_radius': 1800, 'volume': 0.22, 'pan': False,
         'notes': "The works' machine bed over L1 (an engine stand-in for AU's belt rumble), not panned (D-48)."},
        {'id': 'sound:bed_dials', 'room': R('rings'), 'at': [0, 0], 'height': 700, 'sound': 'humming', 'radius': 4200,
         'inner_radius': 2000, 'volume': 0.25, 'pan': False,
         'notes': "The dial hall's and the dial floor's hum, a bed not panned (D-48)."},
        {'id': 'sound:bed_deck', 'room': R('deck'), 'at': [0, 0], 'sound': 'humming', 'radius': 4200,
         'inner_radius': 2000, 'volume': 0.2, 'pan': False, 'notes': "The deck's and Command Central's hum, a bed."},
    ]
    return out


def exits():
    return [{'id': 'exit:gate', 'room': R('gatehall'), 'at': [0, -3904], 'size': [448, 448],
             'surface': geo.S_('7solid01', 256, 256, fit=True), 'to': 'exit:d6_gate',
             'notes': "The gate from inside: out to D6's approach (entrance:dd17_gate)."}]


def objects():
    return {
        'format': 0,
        'start': {'room': R('gatehall'), 'at': ARRIVAL_AT, 'facing': 'n',
                  'notes': "Inside the gate, facing the Hall of Order's leaves."},
        'arrivals': [
            {'entrance': 'entrance:d6_gate', 'room': R('gatehall'), 'at': ARRIVAL_AT, 'facing': 'n',
             'notes': "From D6's door:dd17 (A6, m33.castle_door)."},
            {'entrance': 'entrance:d7_roof', 'room': R('hatch_room'), 'at': ROOF_AT, 'floor_height': geo.L3, 'facing': 'e',
             'notes': "From D7's door:dd17 (A6, q-d26.hatch): at the ladder's foot, facing east."},
        ],
        'doors': doors(), 'lifts': lifts(), 'switches': switches(), 'plates': plates(), 'chests': chests(),
        'monsters': monsters(), 'decorations': decorations(), 'lights': lights(), 'sounds': sounds(),
        'exits': exits(),
        'notes': "DD-17's contents, written by output/studio_cal/dd17/tools/dress.py: 24 doors (three blast-door pairs, the true-name gate's hinged pair, nine single doors, the sump's and the strongroom's doors, four maintenance doors, four field leaves), the lift, four bridge slabs and six trapdoors (lifts), eight belt plates, seven chests, 70 placed monsters (Patrol 30, Annihilator 20, Autobot 6, the eight Head elementals, Gamma Gazer 6) and, not counted, Sheltem and Corak, hidden.",
    }


# ------------------------------------------------------------------------------------------------- wiring
STATUE_TEXT = {
    'statue1': ("The statue speaks as you approach: I am the statue dedicated to honoring Alamar's efforts to protect "
                "Terra from interference from the Ancients. In spite of the Ancients' attempts to separate Alamar from "
                "his rightful guardianship of Terra, Alamar has persevered in his heroic struggle to return to Terra to "
                "protect the planet from harm, both internal and external. Though many years have passed, Alamar's "
                "resolve to return to his sacred duty persists."),
    'statue2': ("The statue speaks as you approach: I am the statue dedicated to honoring Alamar's skillful rulership "
                "of the realms he has controlled. In all kingdoms lucky enough to benefit from Alamar's wise counsel and "
                "firm guidance, crime has decreased and production increased. Further, social deviance has virtually "
                "disappeared while complete obedience, a behavior desirable in lower life forms, has risen dramatically."),
    'statue3': ("The statue speaks as you approach: I am the statue dedicated to honoring Alamar's glorious vengeance "
                "against the Ancients. From his destruction of Ancient science projects to the subversion and theft of "
                "the Xeen structure, Alamar has caused more damage to the Ancients' works and projects than any other "
                "rogue AI the Ancients have ever had the misfortune to create."),
}
TRUE_NAME_TEXT = ("The statue speaks as you approach: I am the statue dedicated to honoring Alamar's true name. It is: "
                  "kdkiendlshj**:and dugli (crackle)I am the statue dedicated to honoring Alamar's true name. It is: "
                  "kdkiendlshj**:and dugli (crackle)...")
HEAD_SPEAKS = {el: f'The Head speaks: "{el.capitalize()} power field operational."' for el in ELEMENTS}
HEAD_ASK = {el: HEAD_SPEAKS[el] + ' Shut the field down?' for el in ELEMENTS}   # D-66: one prompt, its own text
GATE_ASK = "The time is right. What is Alamar's true name?"   # D-66: the source line whole (aaze0050:19)
HEAD_OFF = "The Head goes dark. Somewhere above, a field dies."
BELT_TEXT = "The floor lurches and carries you along."
LIFT_DENIED = "Access to the upper floor is denied!"
YES = 'continueStep == 1'   # D-66: a Yes/No choice (AskChoiceWithAnswerSteps) continues the handler at step 1 on Yes


def lua_str(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def ask_yes_no(prompt, before=()):
    """D-66: the else branch of a Yes/No event (its condition is YES): a continued handler (No) stops; `before` (Lua
    lines that may return: the hook's refusal) runs first; then the question's own text with Yes/No buttons, no
    message before it (D-65 B1), as DD-15's sky door and DD-08's roof ask."""
    return "\n".join(['if continueStep ~= nil then', '    return', 'end', *before,
                      f'AskChoiceWithAnswerSteps(eventId, 3, {lua_str(prompt)}, '
                      '{{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})'])


def slab_lua(el, indent=''):
    n = lock_number('doors', f'lift:slab_{el}')
    if n is None:
        return ''
    return (f'{indent}if IsQBitSet(QBit({DIAL_BIT[el]})) then evt.SetDoorState({n}, DoorAction.Open) '
            f'else evt.SetDoorState({n}, DoorAction.Close) end')


def dial_lua(el):
    i = DIAL_INDEX[el]
    return "\n".join([
        f'if Xeen.alamarSundial("{el}", eventId, continueStep) then',
        slab_lua(el, '    '),
        f'    local reading = Xeen.alamarSundialReading(Xeen.AlamarSundials[{i}])',
        '    if reading == 9 or reading == 10 then',
        '        evt.PlaySoundName("6stone door0101")',
        '    end',
        'end',
    ])


def stop_sound_lua(sid):
    n = lock_number('sounds', sid)
    return None if n is None else f'evt.SetMapVar("AmbientSound{n}", 2)'


def arrival_lua():
    """D-89 (A3 34th, 2026-11-22): no refusal moves the party. The Soul Box check stands before the move, on D6's gate
    (m33.arrival_gate, A6) and D7's hatch (q-d26.hatch); inside, a party with the box gets the arrival line, by the
    roof (above 1000) or the gate, and a party without it (before D6's check lands) gets nothing."""
    return "\n".join([
        'local x, y, z = evt.GetPartyPosition()',
        'local hook = z > 1000 and "m33.roof_arrival" or "m33.arrival"',
        'if XeenQuests.can(hook) then',
        '    XeenQuests.hook(hook)',
        'end',
    ])


def events():
    E = []
    # the arrival (every entry until m33.done): a load event marks the visit, the timer asks m33.arrival once
    E.append({'id': 'evt:visit_load', 'preset': 'script', 'trigger': 'load',
              'condition': {'not': {'map_var': 'in_visit'}},
              'effects': [{'set': {'var': {'map_var': 'in_visit'}, 'value': 1}},
                          {'set': {'var': {'map_var': 'visit'}, 'value': 1}}],
              'notes': "A real entry (in_visit clear, as leaving left it) arms evt:arrival once; a load of a game saved inside the castle finds in_visit set (saved with the map) and arms nothing (A3's segment 77, DD-09's in_visit pattern)."})
    E.append({'id': 'evt:visit_end', 'preset': 'script', 'trigger': 'leave',
              'effects': [{'set': {'var': {'map_var': 'in_visit'}, 'value': 0}}],
              'notes': "Leaving by any way ends the visit, so the next entry greets again."})
    E.append({'id': 'evt:arrival', 'preset': 'script', 'trigger': 'timer', 'every': 1,
              'condition': {'map_var': 'visit', 'not': {'qbit': 'm33_done'}},
              'effects': [{'set': {'var': {'map_var': 'visit'}, 'value': 0}}, {'qbit': 'dd17_arrived_once'}],
              'lua': arrival_lua(),
              'notes': "m33.arrival on every entry until m33.done with the Soul Box (A3): its line (inside 111660); by the roof hatch (the party above 1000) m33.roof_arrival. D-89 (2026-11-22): no refusal moves the party; the box is checked before the move, at D6's gate and D7's hatch."})
    E.append({'id': 'evt:figures_load', 'preset': 'script', 'trigger': 'load',
              'lua': 'evt.SetMm9ActorCanReceiveDamage(ActorIndex("monster:sheltem"), false)\n'
                     'evt.SetMm9ActorCanReceiveDamage(ActorIndex("monster:corak"), false)',
              'notes': "D-61 Q15, P5's way: Sheltem and Corak cannot be hurt, on every load."})
    # doors
    for k in PAIRS:
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}',
                  'title': 'Command Central' if k == 'ante_command' else 'Blast doors'})
    for k, op, s, n in SINGLE:
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}', 'title': 'Door'})
    E.append({'id': 'evt:door_sump', 'preset': 'switch', 'source': 'door:sump', 'title': 'Door',
              'condition': {'map_var': 'sump_open'}, 'toggles': ['door:sump'],
              'locked_text': "A heavy door. It is worked from the other side.",
              'notes': "From the stair hall the sump's door does not open until its lever (on the sump's side) is pulled."})
    E.append({'id': 'evt:sump_lever', 'preset': 'switch', 'source': 'switch:sump_lever', 'title': 'Lever',
              'condition': {'not': {'map_var': 'sump_open'}}, 'opens': ['door:sump'], 'sets': {'map_var': 'sump_open'},
              'effects': [{'text': "The lever drops. The door to the stair hall grinds up."}],
              'locked_text': "The lever is down; the door stands open.",
              'notes': "The sump's way out (D-61 Q18: a fall costs a climb, not progress)."})
    # the belts
    for el, (room, x, size, mouth, mid, land) in BELTS.items():
        for part in ('mouth', 'back'):
            E.append({'id': f'evt:belt_{el}_{part}', 'preset': 'teleport', 'trigger': 'step',
                      'source': f'plate:belt_{el}_{part}', 'to': [x, land, 0], 'direction': 90,
                      'effects': [{'text': BELT_TEXT}, {'lua': 'evt.PlaySoundName("xeen_phase_shift")'}],
                      'notes': f"D-61 Q11: the {el} belt carries the party to its far end, facing north toward the Head (90 degrees); the rumble is an engine stand-in (AU)."})
    # the Heads and the fields
    for el in ELEMENTS:
        room = HEAD_ROOMS[el]
        fx = [{'lua': f'XeenQuests.hook("m33.head_{el}")'},
              {'set_texture': {'of': f'panel:head_{el}', 'to': geo.HEAD_DARK}},
              {'lights_off': f'light:head_{el}'}, {'lua': 'evt.PlaySoundName("xeen_power_up")'}]
        for sid in (f'sound:hum_{el}', f'sound:field_{el}'):
            s = stop_sound_lua(sid)
            if s:
                fx.append({'lua': s})
        E.append({'id': f'evt:head_{el}', 'preset': 'script', 'source': f'panel:head_{el}', 'title': 'Lava Head',
                  'condition': {'lua': YES},
                  'opens': [f'door:field_{el}'], 'effects': fx,
                  'else_effects': [{'lua': ask_yes_no(HEAD_ASK[el], [f'if IsQBitSet(QBit({QB[el]})) then',
                                                                     f'    XeenQuests.hook("m33.head_{el}")',
                                                                     '    return', 'end'])}],
                  'notes': f"D-61 Q12, D-66: one Yes/No prompt '{HEAD_ASK[el]}' (aaze0049:{ {'fire': 7, 'air': 8, 'water': 9, 'earth': 10}[el] } joined with the question); Yes calls A3's m33.head_{el} (head_{el}_off {QB[el]}, 'The Head goes dark. Somewhere above, a field dies.'); the Head goes dark (xalavahdx), its glow and hum stop, the {el} field on L2 drops (one-way, D-43). Afterwards the hook's else line."})
        lf = [{'set_texture': {'of': f'panel:head_{el}', 'to': geo.HEAD_DARK}}, {'lights_off': f'light:head_{el}'}]
        for sid in (f'sound:hum_{el}', f'sound:field_{el}'):
            s = stop_sound_lua(sid)
            if s:
                lf.append({'lua': s})
        E.append({'id': f'evt:head_{el}_load', 'preset': 'switch', 'trigger': 'load',
                  'condition': {'qbit': f'head_{el}_off'}, 'opens': [f'door:field_{el}'], 'effects': lf,
                  'notes': f"On every load after the {el} Head is shut down: its field stays down, the Head dark and quiet."})
        E.append({'id': f'evt:field_{el}', 'preset': 'text', 'source': f'door:field_{el}', 'title': 'Energy field',
                  'text': f"A crackling {el} field bars the alcove.",
                  'notes': "The field before its Head is shut down (it is down after, nothing to click)."})
        # the maintenance door: bolted on the Head's side until the party has been in the Head's room
        E.append({'id': f'evt:in_head_{el}', 'preset': 'script', 'trigger': 'step', 'source': R(room),
                  'condition': {'not': {'map_var': f'bolt_{el}'}},
                  'effects': [{'set': {'var': {'map_var': f'bolt_{el}'}, 'value': 1}}],
                  'notes': f"The party in the {el} Head's room: its maintenance door can now be worked (from the Head's side first)."})
        E.append({'id': f'evt:maint_{el}', 'preset': 'switch', 'source': f'door:maint_{el}', 'title': 'Maintenance door',
                  'condition': {'map_var': f'bolt_{el}'}, 'toggles': [f'door:maint_{el}'],
                  'locked_text': "A maintenance door. It is bolted on the other side.",
                  'notes': "D-61 Q11: one-way until opened from the Head's side, then both ways."})
    # the sundials and the slabs
    E.append({'id': 'evt:dials_load', 'preset': 'script', 'trigger': 'load',
              'lua': "\n".join(['Xeen.alamarSundialsSync()'] + [slab_lua(el) for el in ELEMENTS]),
              'notes': "D-61 map reset: A3's helper rewrites the dial bits 117611-117614 and m33.sundial_nine from the dial variables, then each bridge slab is set from its bit (level while set)."})
    for el in ELEMENTS:
        E.append({'id': f'evt:dial_{el}', 'preset': 'script', 'source': f'platform:dial_{el}',
                  'title': f"{el.capitalize()} Time", 'lua': dial_lua(el),
                  'notes': f"m33.sundials: A3's Xeen.alamarSundial(\"{el}\", ...) asks '{el.capitalize()} Time. The sundial reads N. Turn?', turns it on, says the line at nine and off nine and sets dial_{el}_nine {DIAL_BIT[el]}; when it turned the dial the event sets the {el} slab from that bit (the grind with it)."})
    # the gate, the statues
    E.append({'id': 'evt:gate', 'preset': 'script', 'source': 'door:gate', 'title': 'True-name gate',
              'condition': {'all': [{'not': {'qbit': 'm33_gate_open'}}, {'lua': 'Xeen.alamarSundialsSync()'}]},
              'question': {'ask': GATE_ASK, 'answers': ['Sheltem'],
                           'wrong_effects': [{'lua': 'XeenQuests.hook("m33.true_name_wrong")'}]},
              'opens': ['door:gate'],
              'effects': [{'lua': 'XeenQuests.hook("m33.true_name_gate")'}, {'lua': 'evt.PlaySoundName("xeen_power_up")'}],
              'else_effects': [{'lua': 'if IsQBitSet(QBit(111661)) then evt.StatusText("The gate stands open.") else XeenQuests.hook("m33.true_name_gate") end'}],
              'notes': "The true-name gate (aaze0050:17-21): with all four dials at nine it asks the source line whole, 'The time is right. What is Alamar's true name?' (aaze0050:19, D-66, no message before it); 'Sheltem' calls m33.true_name_gate (gate_open 111661, autonote 4134) and opens the leaves; any other answer m33.true_name_wrong. Before nine the hook's fail text 'The time is not right. Access denied!'."})
    E.append({'id': 'evt:gate_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'm33_gate_open'},
              'opens': ['door:gate'], 'notes': "The gate stays open on every later load."})
    for k in STATUE_TEXT:
        E.append({'id': f'evt:{k}', 'preset': 'text', 'source': f'deco:{k}', 'title': 'Statue', 'window': True,
                  'text': STATUE_TEXT[k], 'notes': "A propaganda statue (aaze0049:2-4), clicked."})
        E.append({'id': f'evt:{k}_near', 'preset': 'script', 'trigger': 'step', 'source': f'plate:{k}',
                  'condition': {'not': {'map_var': f'{k}_heard'}},
                  'effects': [{'set': {'var': {'map_var': f'{k}_heard'}, 'value': 1}}, {'message': STATUE_TEXT[k]}],
                  'notes': "It speaks as the party first approaches (once until the map refills)."})
    E.append({'id': 'evt:true_name_statue', 'preset': 'text', 'source': 'deco:true_name_statue', 'title': 'Statue',
              'window': True, 'text': TRUE_NAME_TEXT, 'notes': "The crackling true-name statue (aaze0049:5, verbatim)."})
    # the lift
    for sw, msg in (('lift_low', "The lift rises toward the deck."), ('lift_high', "The lift sinks to the dial floor.")):
        E.append({'id': f'evt:{sw}', 'preset': 'switch', 'source': f'switch:{sw}', 'title': 'Lift',
                  'condition': {'qbit': 'm33_gate_open'}, 'toggles': ['lift:core'],
                  'effects': [{'text': msg}, {'lua': f'evt.PlaySoundName("xeen_lift", {geo.LIFT_AT[0]}, {geo.LIFT_AT[1]}, 900)'}],
                  'else_effects': [{'text': LIFT_DENIED}],
                  'notes': "The lift runs only once gate_open 111661 is set; before, from either end: 'Access to the upper floor is denied!' (aaze0050:0)."})
    # the deck's trapdoors
    for i, (key, at) in enumerate(geo.TRAPS):
        E.append({'id': f'evt:trap_{key}', 'preset': 'text', 'trigger': 'step', 'source': f'lift:trap_{key}',
                  'title': "A plate seamed like a hatch." if i == 0 else 'Hatched plate',
                  'closes': [f'lift:trap_{key}'], 'text': "The hatched plate drops away under you!",
                  'effects': [{'lua': 'evt.PlaySoundName("xeen_trapdoor")'}],
                  'notes': "D-61 Q18: a trapdoor (lifts trap): the party falls 1,280 to the chasm floor and walks out by the sump. The first one, inside the lift head, has the hover."})
    E.append({'id': 'evt:come_to_me', 'preset': 'script', 'trigger': 'step', 'source': 'plate:come_to_me',
              'condition': {'not': {'qbit': 'come_to_me'}},
              'effects': [{'qbit': 'come_to_me'}, {'message': 'A voice bellows, "Come to ME!"'}],
              'notes': "aaze0051:2, once (117606)."})
    # the vault
    E.append({'id': 'evt:vault_release', 'preset': 'switch', 'source': 'switch:vault_release',
              'title': "Vault release: the strongroom by Command Central",
              'condition': {'lua': YES},
              'opens': ['door:vault'], 'sets': {'qbit': 'vault_open'},
              'effects': [{'text': "Far off, a heavy door grinds up."}],
              'else_effects': [{'lua': ask_yes_no("Vault release. Pull?", [
                  'if IsQBitSet(QBit(117605)) then',
                  '    evt.StatusText("The release is down. The strongroom stands open.")', '    return', 'end'])}],
              'notes': "One-way (D-43): Yes/No (D-66); vault_open 117605 raises the strongroom's door by the antechamber; after it 'The release is down. The strongroom stands open.'"})
    E.append({'id': 'evt:vault_door', 'preset': 'text', 'source': 'door:vault', 'title': 'Strongroom',
              'text': "The strongroom's door is sealed. Its release is somewhere else.",
              'notes': "Before the release (after it the door is up)."})
    E.append({'id': 'evt:vault_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'vault_open'},
              'opens': ['door:vault'], 'notes': "The strongroom stays open on every later load."})
    # the Power Juice (A3's hook pending)
    E.append({'id': 'evt:juice', 'preset': 'script', 'source': 'platform:juice', 'title': 'XEEN Power Juice',
              'lua': 'XeenQuests.hook("m33.power_juice")',
              'notes': "D-61 Q19: A3's m33.power_juice: +2 Might once per character (player bit 11369), decided for the clicking member."})
    # the hatch
    E.append({'id': 'evt:hatch', 'preset': 'script', 'source': 'platform:hatch', 'title': "The roof hatch",
              'condition': {'lua': 'XeenQuests.hook("q-d26.alamar_hatch")'},
              'effects': [{'exit': 'exit:d7_roof'}],
              'notes': "Q-D26 (D-58, D-61 Q14): q-d26.alamar_hatch ('Bolted from above.' until roof_unlocked 113521); then the standard entrance window (F16, 2026-11-22: OK/Close, no Yes/No): OK moves to D7's entrance:dd17_roof (-18688, 8448, 1536) facing 1024."})
    # Command Central
    E.append({'id': 'evt:dais', 'preset': 'script', 'trigger': 'step', 'source': 'plate:dais',
              'condition': {'lua': YES},
              'effects': [{'lua': 'XeenQuests.hook("m33.sheltem")'},
                          {'cinematic': {'id': 'cinematic:self_destruct', 'then': 'evt:after_sheltem'}}],
              'else_effects': [{'lua': ask_yes_no("Before the throne. Open the Soul Box?", [
                  'if not XeenQuests.can("m33.sheltem") then',
                  '    XeenQuests.hook("m33.sheltem")', '    return', 'end'])}],
              'notes': "D-61 Q16: the dais plate asks first (Yes/No, D-66); Yes calls m33.sheltem (takes the Soul Box, gives the Cube of Power, done 111662, the voiced lines), then the self-destruct cinematic (Sheltem and Corak shown), then the leave to D6. Without the gate or the box: the hook's fail line."})
    E.append({'id': 'evt:show_figures', 'preset': 'script', 'trigger': 'call',
              'effects': [{'show_actors': SHELTEM_GROUP}, {'show_actors': CORAK_GROUP}],
              'notes': "The cinematic's cue: Sheltem appears on the throne and Corak on the dais (hidden placed actors shown, D-61 RELAYS)."})
    E.append({'id': 'evt:after_sheltem', 'preset': 'script', 'trigger': 'call', 'effects': [{'leave': 'exit:d6_gate'}],
              'notes': "D-61 Q17: the cinematic's done event: out to D6's entrance:dd17_gate at once ({direct = true}, XD-19's pattern)."})
    E.append({'id': 'evt:throne', 'preset': 'text', 'source': 'deco:throne', 'title': "Sheltem's throne",
              'text': "The throne is empty, and the air says it will not be for long.", 'notes': "The throne."})
    E.append({'id': 'evt:screens', 'preset': 'text', 'source': 'platform:console_screen', 'title': 'Screens',
              'text': "The screens show the Forbidden Zone from a dozen windows: the lava moat, the road, the gate.",
              'notes': "The screen room's screens."})
    E.append({'id': 'evt:command_screens', 'preset': 'text', 'source': 'panel:screens', 'title': 'Command Central',
              'text': "Banks of machines over the throne, every light lit.", 'notes': "The machines over the throne."})
    # finds
    E.append({'id': 'evt:sump_bones', 'preset': 'script', 'source': 'deco:sump_bones', 'title': 'Bones',
              'condition': {'not': {'map_var': 'sump_find'}},
              'effects': [{'set': {'var': {'map_var': 'sump_find'}, 'value': 1}}, {'gold': 1500},
                          {'give_item': {'level': 5, 'kind': 40}},
                          {'text': "The bones of an earlier caller, and what he carried. (+1500 gold)"}],
              'else_effects': [{'text': "Bones, and bent plates."}],
              'notes': "The sump's find (D-61 treasure): once."})
    # the exit and the chests
    E.append({'id': 'evt:exit_gate', 'preset': 'exit', 'source': 'exit:gate', 'title': 'Exit Castle Alamar',
              'notes': "aaze0049:0's meaning (D-24): out to D6 at entrance:dd17_gate."})
    for c in ('barracks', 'watch', 'store', 'post', 'robot_bay', 'screen', 'hoard'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    return E


CINEMATICS = [{
    'id': 'cinematic:self_destruct',
    'shots': [
        {'seconds': 5, 'at': [-1600, -3072, 1560], 'look_at': [-2944, -3072, 1440]},
        {'seconds': 5, 'at': [-2304, -2688, 1500], 'look_at': [-2800, -3200, 1400]},
        {'seconds': 6, 'at': [-1000, -3500, 1700], 'look_at': [-2700, -3072, 1400]},
    ],
    'cues': [
        {'at': 0, 'fade': 'in', 'seconds': 1},
        {'at': 0.5, 'event': 'evt:show_figures'},
        {'at': 0.5, 'subtitle': "Corak steps out of the Soul Box, taller than the room. Before the throne, Sheltem is there as if he had always been.", 'seconds': 4.5},
        {'at': 5, 'subtitle': "They close on each other, and the castle begins to shake itself apart.", 'seconds': 4.5},
        {'at': 5, 'shake': 0.8, 'seconds': 3},
        {'at': 5, 'sound': 'xeen_klaxon'},
        {'at': 9.5, 'sound': 'xeen_castle_groan'},
        {'at': 9.5, 'shake': 1, 'seconds': 4},
        {'at': 10, 'subtitle': "\"The Cube! Take it and run!\"", 'seconds': 4},
        {'at': 11.5, 'sound': 'xeen_klaxon'},
        {'at': 15, 'fade': 'out', 'seconds': 1},
    ],
    'notes': "D-61 Q15/Q17: the self-destruct after m33.sheltem: Sheltem and Corak shown (evt:show_figures), the castle's groan (XD-19's xeen_castle_groan) between AU's two klaxon blasts (5 s, 11.5 s), then the leave to D6 in the done event. Subtitles are map-local lines after A3's m33.sheltem text (Lines for A3).",
}]


def wiring():
    vars_ = ['visit', 'sump_open', 'sump_find'] + [f'bolt_{el}' for el in ELEMENTS] + \
[f'{k}_heard' for k in STATUE_TEXT] + ['in_visit']
    return {'format': 0, 'variables': vars_, 'events': sorted(events(), key=lambda e: e['id']),
            'cinematics': CINEMATICS, 'notes': "DD-17's events, written by output/studio_cal/dd17/tools/dress.py."}


ATMOSPHERE = {'format': 0, 'notes': "DD-17 is enclosed (no open sky)."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', gen.scale_doc(objects()))
    gen.dump(folder / 'wiring.yml', gen.scale_doc(wiring()))
