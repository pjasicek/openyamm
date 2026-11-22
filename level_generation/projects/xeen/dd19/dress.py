#!/usr/bin/env python3
"""DD-19 Wizard Quarter, L4: objects.yml, wiring.yml, atmosphere.yml (written by gen.py L4)."""
import geo

WIZARD, SORCERER, XENOC = 11190, 11191, 11196
ENCHANTRESS, GRAND, MORGANA = 11181, 11182, 11183
HAND, GOLEM = 11602, 11582
NAME = {WIZARD: 'wizard', SORCERER: 'sorcerer', ENCHANTRESS: 'enchantress', GRAND: 'grand', HAND: 'hand',
        GOLEM: 'golem'}
GROUP = {WIZARD: 1, SORCERER: 1, ENCHANTRESS: 2, GRAND: 2, HAND: 3, GOLEM: 4}
XENOC_GROUP, MORGANA_GROUP, AMBUSH_GROUP = 5, 6, 7
BLASTEM_HOSTILE, BLASTEM_BODY = 20, 21
BLASTEM_NPC = 5248

CANDLE = [235, 175, 115]
HALL = [215, 175, 130]
TORCH = [240, 160, 90]
COLD = [150, 165, 200]
DARK = [190, 140, 150]
UNDER = [170, 140, 110]
SKYL = [170, 150, 160]
VIOLET = [170, 110, 240]

D3_GATE = (-10752, 22016, 1728, 512)      # D3's entrance:dd19_gate (assets_dev/worlds/xeen/maps/xeen_d3.studio.yml)


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
DOUBLE = {'court_mirage': ('Mirage Guild', "The Mirage Guild's great-hall doors on the court: two hinged leaves (t07c03c|t07c03d) opening apart."),
          'court_hq': ('Sorceress HQ', "The Sorceress HQ's great-hall doors on the court: two hinged leaves opening apart.")}
SINGLE = [
    # key, opening, surface, title, notes
    ('arcade_common', 'open:arcade_common', geo.HCDOOR, 'Guild Common', "The Guild Common's door in the arcade's back wall."),
    ('common_weights', 'open:common_weights', geo.HCDOOR, 'Weights and Measures', "The tax office's door."),
    ('hall_study', 'open:hall_study', geo.ICEDOOR, "Xenoc's study", "Xenoc's study behind his chair."),
    ('stair_robing', 'open:stair_robing', geo.IRONDOOR, 'Robing room', "The robing room's door off the HQ stair."),
    ('sanctum_wardrobe', 'open:sanctum_wardrobe', geo.IRONDOOR, "Morgana's wardrobe", "Morgana's wardrobe."),
    ('qw_undercroft', 'open:qw_undercroft', geo.IRONDOOR, 'Guild Quarters', "The wizards' quarters onto the undercroft."),
    ('undercroft_qe', 'open:undercroft_qe', geo.IRONDOOR, 'Guild Quarters', "The sorceresses' quarters off the undercroft."),
    ('alembic_back', 'open:alembic_back', geo.IRONDOOR, 'Door', "The alembic cellar onto the HQ's back stair."),
]


def doors():
    out = []
    for k, (title, notes) in DOUBLE.items():
        out.append({'id': f'door:{k}', 'opening': f'open:{k}', 'kind': 'hinged', 'leaves': 2,
                    'pictures': [list(map(dict, r)) for r in geo.LEAVES],
                    'back_pictures': [list(map(dict, r)) for r in geo.LEAVES], 'notes': notes})
    for k, op, s, title, n in SINGLE:
        out.append({'id': f'door:{k}', 'opening': op, 'kind': 'slide_left', 'surface': dict(s, fit=True), 'notes': n})
    out.append({'id': 'door:bridge', 'opening': 'open:hall_bridge', 'kind': 'slide_left',
                'surface': dict(geo.ICEDOOR, fit=True),
                'notes': "The bridge's west door, bolted on Xenoc's side (switch:bolt in the Hall of Mirages)."})
    out.append({'id': 'door:ward', 'opening': 'open:ward', 'kind': 'slide_down', 'fold': True, 'speed': 96,
                'surface': dict(geo.WARD), 'tile': True,
                'notes': "Morgana's door: a ward of light (XD-25's xufield, see-through) fed by two lamps; it sinks when both are out."})
    out.append({'id': 'door:vault', 'opening': 'open:vault', 'kind': 'slide_left', 'surface': dict(geo.IRONDOOR, fit=True),
                'notes': "The guild vault's iron door: the lever in Xenoc's study raises it."})
    out.append({'id': 'door:mirage', 'opening': 'open:mirage_wall', 'kind': 'slide_up', 'thickness': 16, 'speed': 120,
                'surface': dict(geo.ICEWALL), 'back_surface': dict(geo.ICEBAND), 'tile': True,
                'notes': "The mirage: the gallery's blank wall that is not there (made passable at load, never opened)."})
    return out


def switches():
    return [
        {'id': 'switch:bolt', 'room': R('mirage_hall'), 'kind': 'lever', 'at': [-1152, 1600], 'floor_height': geo.UP,
         'reach': 48, 'notes': "The bridge door's bolt, on the Hall of Mirages' east wall beside the door."},
        {'id': 'switch:vault_lever', 'room': R('xenoc_study'), 'kind': 'lever', 'at': [-1408, -320], 'floor_height': geo.UP,
         'reach': 48, 'notes': "The lever under the guild's seal: the vault's iron door far below."},
    ]


def chests():
    return [
        {'id': 'chest:study', 'room': R('xenoc_study'), 'at': [-2176, -640], 'facing': 'e', 'treasure_level': 4,
         'random_items': 2, 'gold': 1200, 'notes': "Xenoc's chest beside his desk."},
        {'id': 'chest:wardrobe', 'room': R('wardrobe'), 'at': [4608, 2432], 'treasure_level': 4,
         'random_items': 2, 'gold': 1000, 'notes': "Morgana's chest among her robes."},
        {'id': 'chest:weights', 'room': R('weights'), 'at': [1920, 2752], 'facing': 'w', 'treasure_level': 4,
         'random_items': 2, 'gold': 1500, 'notes': "The wizards' tax chest."},
        {'id': 'chest:quarters_w', 'room': R('quarters_w'), 'at': [-1024, 2688], 'facing': 'w', 'treasure_level': 4,
         'random_items': 2, 'gold': 800, 'notes': "The wizards' quarters' chest: opening it springs the ambush."},
        {'id': 'chest:quarters_e', 'room': R('quarters_e'), 'at': [2176, 2816], 'facing': 'w', 'treasure_level': 4,
         'random_items': 2, 'gold': 800, 'notes': "The sorceresses' quarters' chest."},
        {'id': 'chest:hoard', 'room': R('vault'), 'at': [0, -768], 'facing': 'n', 'treasure_level': 5,
         'random_items': 3, 'gold': 4000, 'notes': "The guilds' hoard."},
    ]


W, S, E, GS, CH, IG = WIZARD, SORCERER, ENCHANTRESS, GRAND, HAND, GOLEM
PLACED = {
    'mirage_foyer': [(W, [-1920, 640]), (W, [-1536, 1152]), (W, [-1920, 1664]), (W, [-1472, 1856])],
    'illusions': [(W, [-3072, 512]), (W, [-3072, 1280]), (W, [-2816, 768]), (S, [-2688, 1280])],
    'mirror_gallery': [(W, [-2944, 512]), (W, [-2944, 1216]), (W, [-2688, 1408]), (CH, [-2688, 704]), (CH, [-2688, 1088])],
    'bridge': [(CH, [-384, 1856]), (CH, [384, 1856])],
    'scrying': [(E, [1536, 1024]), (E, [1920, 1408]), (E, [1984, 832])],
    'hq_foyer': [(E, [1536, 640]), (E, [1920, 1280]), (E, [1536, 1664]), (CH, [1920, 640]), (CH, [1920, 1792])],
    'robing': [(E, [4096, 768]), (E, [4352, 1152])],
    'weights': [(CH, [1408, 2432]), (CH, [1792, 2432])],
    'alcoves': [(W, [-4608, 1920]), (W, [-4288, 2112])],
    'undercroft': [(CH, [0, 1472]), (CH, [0, 2752]), (S, [0, 2112])],
    'quarters_e': [(CH, [1280, 2176]), (CH, [1920, 2176])],
    'alembic': [(E, [2816, 2176]), (E, [3072, 2560])],
    'vault': [(IG, [-320, -512]), (IG, [320, -512]), (IG, [-320, 0]), (IG, [320, 0])],
}
FLOOR_OF = {'alcoves': geo.UN}
AMBUSH = [[-3200, 2048], [-2560, 2048], [-1920, 2048], [-1408, 2048]]
XENOC_GUARDS = [[-1600, 640], [-1600, 1152]]
MORGANA_GUARDS = [[2944, 3008], [3712, 3008]]
BLASTEM_AT = [512, 3296]


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at in lst:
            n[row] = n.get(row, 0) + 1
            d = {'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                 'facing': 270, 'group': GROUP[row]}
            if room in FLOOR_OF:
                d['floor_height'] = FLOOR_OF[room]
            out.append(d)
    for i, at in enumerate(AMBUSH, 1):
        out.append({'id': f'monster:ambush_{i}', 'room': R('quarters_w'), 'monster': WIZARD, 'at': at, 'facing': 90,
                    'group': AMBUSH_GROUP, 'hidden': True,
                    'notes': "One of the four wizards in the cells (D-18): placed hidden, shown when the quarters' chest is opened (counted at load)."})
    out.append({'id': 'monster:xenoc', 'room': R('mirage_hall'), 'monster': XENOC, 'at': [-1984, 896], 'facing': 90,
                'group': XENOC_GROUP, 'immobile': True,
                'notes': "Xenoc (11196, 60, blink) before his chair, keeping his place (he casts from it): q-d14.xenoc at his death."})
    for i, at in enumerate(XENOC_GUARDS, 1):
        out.append({'id': f'monster:xenoc_sorcerer_{i}', 'room': R('mirage_hall'), 'monster': SORCERER, 'at': at,
                    'facing': 180, 'group': XENOC_GROUP, 'notes': "One of Xenoc's two Sorcerers."})
    out.append({'id': 'monster:morgana', 'room': R('morgana_sanctum'), 'monster': MORGANA, 'at': [3328, 2944],
                'facing': 270, 'group': MORGANA_GROUP, 'immobile': True,
                'notes': "Morgana keeps her place before her dais (she casts from it). Morgana (11183, 60 by D-42, own skin sorc_m, blink) before her dais: q-d14.morgana at her death."})
    for i, at in enumerate(MORGANA_GUARDS, 1):
        out.append({'id': f'monster:morgana_grand_{i}', 'room': R('morgana_sanctum'), 'monster': GRAND, 'at': at,
                    'facing': 270, 'group': MORGANA_GROUP, 'notes': "One of Morgana's two Grand Sorceresses."})
    out.append({'id': 'monster:blastem', 'room': R('common'), 'monster': SORCERER, 'at': BLASTEM_AT, 'facing': 270,
                'group': BLASTEM_BODY, 'hostile': False, 'immobile': True,
                'notes': "Blastem the Wizard's body (not counted): a peaceful Sorcerer stand-in behind his table until A2 gives him a row of his own; his table talks for him (NPC 5248). Hidden once blastem_angered (evt:blastem_swap, evt:blastem_load)."})
    out.append({'id': 'monster:blastem_angry', 'room': R('common'), 'monster': SORCERER, 'at': [BLASTEM_AT[0] + 160, BLASTEM_AT[1]],
                'facing': 270, 'group': BLASTEM_HOSTILE, 'hidden': True,
                'notes': "Blastem taking 'The lesson' (D-42 (5), the Valio pattern): Sorcerer 11191, hostile, shown in his body's place once blastem_angered (113286), on this and every later load."})
    return out


# (key, decoration, room, at, floor height or None)
PROPS = [
    ('hall_chandelier', 'chndlir0', 'mirage_hall', [-1728, 1280], None, True),
    ('sanctum_chandelier', 'chndlir0', 'morgana_sanctum', [3328, 2432], None, True),
    ('common_chandelier', 'chndlir0', 'common', [0, 2816], None, True),
    ('flame_scry', 'flamb00', 'scrying', [1728, 704], geo.UP + 48, False),
    ('hearth_fire', 'flamb00', 'common', [-768, 3392], 48, False),
    # D-89 identity (s29): the Mirage Guild's crystal on its stand in the magic circle; the Sorceress HQ's two
    # braziers and its shelves of skulls (geo.py)
    ('guild_crystal', 'crystl0', 'mirage_foyer', list(geo.CIRCLE_AT), geo.CRYSTAL_TOP, False),
] + [(f'hq_brazier_{i}', 'brzier00', 'hq_foyer', [x, y], None, True) for i, (x, y) in enumerate(geo.HQ_BRAZIERS, 1)] \
  + [(f'hq_skull_{i}_{j}', '7dec20', 'hq_foyer', [x + dx, y], b + 16, False)
     for i, (x, y, b) in enumerate(geo.SKULL_SHELVES, 1) for j, dx in enumerate((-144, 0, 144), 1)]
# (room, wall, along, decoration)
SCONCES = [
    ('court', 'w', 0.15, 'torch01'), ('court', 'e', 0.85, 'torch01'), ('court', 's', 0.3, 'torch01'),
    ('court', 's', 0.7, 'torch01'),
    ('arcade', 'n', 0.25, 'scon100'), ('arcade', 'n', 0.75, 'scon100'),
    ('common', 'w', 0.25, 'scon100'), ('common', 'e', 0.75, 'scon100'), ('weights', 'n', 0.5, 'scon100'),
    ('mirage_foyer', 'w', 0.2, 'scon100'), ('mirage_foyer', 'w', 0.8, 'scon100'), ('illusions', 's', 0.5, 'scon100'),
    ('mirage_stair', 'n', 0.25, 'scon100'), ('mirror_gallery', 'e', 0.2, 'scon100'), ('mirror_gallery', 'e', 0.8, 'scon100'),
    ('mirage_hall', 'w', 0.2, 'scon100'), ('mirage_hall', 'w', 0.8, 'scon100'), ('xenoc_study', 'w', 0.5, 'scon100'),
    ('bridge', 'n', 0.3, 'scon100'), ('bridge', 'n', 0.7, 'scon100'),
    ('scrying', 'w', 0.2, 'scon100'), ('hq_foyer', 'e', 0.45, 'torch05'), ('hq_foyer', 'e', 0.8, 'torch05'),   # D-89: purple flames (torch05)
    ('hq_stair', 's', 0.2, 'scon100'), ('robing', 's', 0.5, 'scon100'),
    ('morgana_sanctum', 'w', 0.5, 'scon100'), ('morgana_sanctum', 'e', 0.5, 'scon100'), ('wardrobe', 'n', 0.5, 'scon100'),
    ('alcoves', 'w', 0.5, 'torch02'), ('quarters_w', 's', 0.3, 'torch02'), ('quarters_w', 's', 0.7, 'torch02'),
    ('undercroft', 'w', 0.3, 'torch02'), ('undercroft', 'e', 0.7, 'torch02'), ('quarters_stair', 'n', 0.5, 'torch02'),
    ('quarters_e', 's', 0.5, 'torch02'), ('alembic', 'n', 0.5, 'torch02'), ('back_stair', 'n', 0.25, 'torch02'),
    ('vault', 'w', 0.5, 'torch02'), ('vault', 'e', 0.5, 'torch02'),
]
LAMP_ROBE_ALONG = round((4864 - 4544) / 1152, 4)


def decorations():
    out = []
    for key, dec, room, at, fh, hangs in PROPS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at}
        if fh is not None:
            d['floor_height'] = fh
        if hangs:
            d['hangs'] = True
        if key.startswith('hq_brazier'):     # MM6's brazier hangs on three chains: its top 2 into the vault
            d['height'] = geo.R['hq_foyer'][3] - 146 + 2
        out.append(d)
    out.append({'id': 'deco:flame_robe', 'room': R('robing'), 'decoration': 'torch02', 'wall': 'n',
                'along': LAMP_ROBE_ALONG, 'height': 288, 'notes': "Ward lamp 2's flame on its bracket."})
    for i, (room, wall, along, dec) in enumerate(SCONCES):
        out.append({'id': f'deco:sconce_{i}', 'room': R(room), 'decoration': dec, 'wall': wall, 'along': along,
                    'height': 192})
    return out


THEME_COL = {'theme:court': SKYL, 'theme:hc': CANDLE, 'theme:bridge': CANDLE, 'theme:bridge_up': CANDLE, 'theme:mirage': COLD,
             'theme:mirage_hall': COLD, 'theme:mirage_stair': COLD, 'theme:hq': DARK, 'theme:hq_stair': DARK,
             'theme:under': UNDER}
# Where a two-storey room's light stands (in its open part, clear of the head and the flight).
OPEN_AT = {'mirage_stair': ([-2752, 2400], 448), 'hq_stair': ([2688, 640], 448), 'alcoves': ([-4480, 2000], 384),
           'quarters_stair': ([-192, 4480], 384), 'back_stair': ([4096, 2560], 384)}


def lights():
    L = []

    def add(room, at, radius, color, height=None, notes=None, lid=None):
        d = {'id': lid or f'light:{room}_{sum(1 for x in L if x["room"] == R(room)) + 1}', 'room': R(room), 'at': at,
             'radius': radius, 'color': color}
        if height:
            d['height'] = height
        if notes:
            d['notes'] = notes
        L.append(d)
    for room in geo.ORDER:
        (w, h), c = geo.extent(room)
        col = THEME_COL[geo.R[room][4]]
        if room in OPEN_AT:
            at, hh = OPEN_AT[room]
            add(room, at, 1100, col, height=hh)
            continue
        r = int(min(2000, max(700, 0.6 * max(w, h))))
        tall = geo.R[room][3] - geo.R[room][2] > 400
        if max(w, h) > 2400:
            ax = 0 if w >= h else 1
            for f in (0.25, 0.75):
                p = list(c)
                lo = c[ax] - (w if ax == 0 else h) / 2
                p[ax] = int(lo + f * (w if ax == 0 else h))
                add(room, p, int(r * 0.75), col, height=320 if tall else None)
        else:
            add(room, c, r, col, height=320 if tall else None)
    add('scrying', [1728, 704], 700, VIOLET, height=160, lid='light:lamp_scry',
        notes="Ward lamp 1's cold violet flame (out when snuffed).")
    add('robing', [4544, 1472], 700, VIOLET, height=288, lid='light:lamp_robe',
        notes="Ward lamp 2's cold violet flame on its bracket (out when snuffed).")
    add('common', [-768, 3328], 600, TORCH, height=96, notes="The hearth's glow.")
    for i, (x, y) in enumerate(geo.HQ_BRAZIERS, 1):     # D-89 identity (s29)
        add('hq_foyer', [x, y], 1200, VIOLET, height=360, lid=f'light:hq_brazier_{i}',
            notes="A brazier burning violet in the Sorceress HQ.")
    add('mirage_foyer', list(geo.CIRCLE_AT), 600, [140, 170, 255], height=geo.CRYSTAL_TOP + 64,
        lid='light:guild_crystal', notes="The guild's crystal glowing in its circle.")
    return L


def sounds():
    return [
        {'id': 'sound:court', 'room': R('court'), 'at': [0, 768], 'sound': 'xeen_amb_sky', 'radius': 2000,
         'inner_radius': 800, 'volume': 0.3, 'pan': False, 'notes': "The open air over the court."},
        {'id': 'sound:court_wind', 'room': R('court'), 'at': [0, 1024], 'sound': 'whistling wind', 'radius': 1600,
         'inner_radius': 500, 'volume': 0.25, 'notes': "Wind over the court."},
        {'id': 'sound:hall', 'room': R('mirage_hall'), 'at': [-1728, 1152], 'sound': 'xeen_amb_tower', 'radius': 1800,
         'inner_radius': 600, 'volume': 0.35, 'pan': False, 'notes': "The Hall of Mirages' draughts."},
        {'id': 'sound:sanctum', 'room': R('morgana_sanctum'), 'at': [3328, 2560], 'sound': 'xeen_amb_tower',
         'radius': 1800, 'inner_radius': 600, 'volume': 0.35, 'pan': False, 'notes': "Morgana's sanctum."},
        {'id': 'sound:undercroft', 'room': R('undercroft'), 'at': [0, 2048], 'sound': 'drip03', 'radius': 2200,
         'inner_radius': 500, 'volume': 0.4, 'wait': [3, 8], 'notes': "Drips under the low vault."},
        {'id': 'sound:quarters_w', 'room': R('quarters_w'), 'at': [-2240, 2240], 'sound': 'drip02', 'radius': 1800,
         'inner_radius': 400, 'volume': 0.35, 'wait': [2, 6], 'notes': "Water dripping in the cells."},
        {'id': 'sound:alembic', 'room': R('alembic'), 'at': [3200, 2304], 'sound': 'drip02', 'radius': 1600,
         'inner_radius': 400, 'volume': 0.35, 'wait': [2, 6], 'notes': "The still dripping."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('court'), 'at': geo.ARRIVAL_AT, 'facing': 'n',
                  'notes': "Inside the guild gate: the court's south side, 384 inside the gate, facing north (the gate at the party's back)."},
        'arrivals': [
            {'entrance': 'entrance:d3_guild_gate', 'room': R('court'), 'at': geo.ARRIVAL_AT, 'facing': 'n',
             'notes': "From D3's guild gate (thing:dd19_gate, q-d14.quarter_gate, A5): MoveToMap(0, 384, 0, 512)."},
        ],
        'exits': [{'id': 'exit:gate', 'room': R('court'), 'at': [geo.GATE_AT, 0], 'size': [256, 256],
                   'surface': geo.S_('7solid01', 256, 256, fit=True), 'to': 'exit:d3_gate',
                   'notes': "The guild gate's inside face (hclgdr once, as outside): the exit preset back to D3's entrance:dd19_gate."}],
        'doors': doors(), 'switches': switches(), 'chests': chests(), 'monsters': monsters(),
        'decorations': decorations(), 'lights': lights(), 'sounds': sounds(),
        'notes': "DD-19's contents, written by output/studio_cal/dd19/tools/dress.py: 14 doors (two great-hall double doors as hinged pairs, eight single doors, the bolted bridge door, the ward of light, the vault's iron door, the mirage), two levers, six chests, 50 placed monsters (16 Wizards, 4 Sorcerers, Xenoc, 10 Enchantresses, 2 Grand Sorceresses, Morgana, 12 Carnage Hands, 4 Iron Golems; four of the wizards hidden in the quarters' ambush) and Blastem (a peaceful body and his hidden hostile swap, not counted).",
    }


# ------------------------------------------------------------------------------------------------- wiring
ARRIVE = ("THE WIZARD QUARTER. Beyond the guild gate, a court of rose-coloured stone under a dimming sky. To the west, "
          "the Mirage Guild, where Xenoc the Wizard holds court; to the east, the Sorceress HQ, Morgana's house. Astra "
          "wants them both defeated. The gate behind you is the way back to Sandcaster.")
MIRROR = "In the mirror, the blank wall behind you has a door in it."
WARD_LINE = "A ward of light seals the door. The ward draws on two lamps, one above and one below."
THINS = "The ward thins, but holds."
GOES = "The ward flickers and goes out."
BEGONE = "Begone, children, lest I blast you to ash and scatter you to the winds."

BRIDGE_LUA = "\n".join([
    'local x = evt.GetPartyPosition()',
    'if x < -1152 then',
    '    evt.StatusText("The door is bolted. The bolt is on the wall beside it.")',
    'elseif IsQBitSet(QBit(113283)) then',
    '    evt.StatusText("The door is bolted from the far side.")',
    'else',
    f'    evt.StatusText("{BEGONE}")',
    'end',
])
WARD_LUA = "\n".join([
    'if IsAtLeast(MapVar(lamp_scry), 1) or IsAtLeast(MapVar(lamp_robe), 1) then',
    f'    evt.StatusText("{THINS}")',
    'else',
    f'    evt.StatusText("{WARD_LINE}")',
    'end',
])


def lamp_lua(other):
    return "\n".join([
        f'if IsAtLeast(MapVar({other}), 1) then',
        f'    evt.StatusText("{GOES}")',
        'else',
        f'    evt.StatusText("{THINS}")',
        'end',
    ])


BLASTEM_LUA = "\n".join([
    'if IsQBitSet(QBit(113286)) then',
    '    evt.StatusText("Blastem\'s chair is empty.")',
    '    return',
    'end',
    f'evt.SpeakNPC({BLASTEM_NPC})',
])
FONT_LUA = "\n".join(['evt.ForPlayer(Players.All)', 'AddValue(SP, 2000)'])


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'dd19_arrived_once'}},
              'effects': [{'message': ARRIVE}, {'qbit': 'dd19_arrived_once'}],
              'notes': "The first arrival's window, once (dd19_arrived_once 117520, A3's)."})
    for k, (title, notes) in DOUBLE.items():
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}', 'title': title})
    for k, op, s, title, n in SINGLE:
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}', 'title': title})
    E.append({'id': 'evt:exit_gate', 'preset': 'exit', 'source': 'exit:gate', 'title': 'Guild gate',
              'notes': "The game's own leave window, out through the guild gate to D3's entrance:dd19_gate (D-24)."})
    # the mirage and the mirror
    E.append({'id': 'evt:mirage_load', 'preset': 'script', 'trigger': 'load', 'effects': [{'passable': 'door:mirage'}],
              'notes': "The mirage wall: the party walks through it (XD-10's and DD-03's illusory wall)."})
    E.append({'id': 'evt:mirror', 'preset': 'text', 'source': 'panel:mirror', 'title': 'Mirror', 'window': True,
              'text': MIRROR, 'notes': "poi:mirror: the answer to the mirage wall (Blastem's humble answer is the other)."})
    # the bridge's bolt
    E.append({'id': 'evt:bolt', 'preset': 'switch', 'source': 'switch:bolt', 'title': 'Bolt',
              'condition': {'not': {'map_var': 'bolt_drawn'}}, 'opens': ['door:bridge'], 'sets': {'map_var': 'bolt_drawn'},
              'effects': [{'text': "You draw the bolt. The bridge door swings open."}],
              'locked_text': "The bolt is drawn.", 'notes': "key:bolt: drawn from Xenoc's side, once."})
    E.append({'id': 'evt:bridge_door', 'preset': 'script', 'source': 'door:bridge', 'title': 'Door',
              'condition': {'not': {'map_var': 'bolt_drawn'}}, 'lua': BRIDGE_LUA,
              'else_effects': [{'text': "The bolt is drawn back."}],
              'notes': "The bridge's west door: while Xenoc lives his voice through it (aaze0031:37, Wrathmont's line given to Xenoc); after his death 'The door is bolted from the far side.'; from the hall the bolt beside it."})
    # the two kills
    E.append({'id': 'evt:xenoc_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
              'condition': {'kills': {'monster': 'monster:xenoc'}}, 'lua': 'XeenQuests.hook("q-d14.xenoc")',
              'notes': "goal:xenoc: q-d14.xenoc at his death (xenoc_slain 113283, once)."})
    E.append({'id': 'evt:morgana_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
              'condition': {'kills': {'monster': 'monster:morgana'}}, 'lua': 'XeenQuests.hook("q-d14.morgana")',
              'notes': "goal:morgana: q-d14.morgana at her death (morgana_slain 113284, once)."})
    # the ward and its two lamps
    for lamp, other, src, deco, where in (('lamp_scry', 'lamp_robe', 'platform:lamp_scry', 'deco:flame_scry', 'above'),
                                          ('lamp_robe', 'lamp_scry', 'panel:lamp_robe', 'deco:flame_robe', 'below')):
        E.append({'id': f'evt:{lamp}', 'preset': 'script', 'source': src, 'title': 'Ward lamp',
                  'condition': {'not': {'map_var': lamp}},
                  'question': {'message': "A ward lamp. Its cold violet flame leans toward Morgana's door.",
                               'ask': "Snuff it (Yes/No)?", 'answers': ['Yes', 'Y']},
                  'effects': [{'set': {'var': {'map_var': lamp}, 'value': 1}}, {'lights_off': f'light:{lamp}'},
                              {'hide': deco}],
                  'lua': lamp_lua(other),
                  'else_effects': [{'text': "The lamp is out."}],
                  'notes': f"Ward lamp {'1' if where == 'above' else '2'} ({where}): snuffed once; with the other out the ward goes out (evt:ward_down)."})
    E.append({'id': 'evt:ward_down', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
              'condition': {'map_var': 'lamp_scry', 'all': [{'map_var': 'lamp_robe'}], 'not': {'map_var': 'ward_down'}},
              'opens': ['door:ward'], 'effects': [{'set': {'var': {'map_var': 'ward_down'}, 'value': 1}}],
              'notes': "key:lamps: both lamps out, the ward sinks (again after a refill keeps the vars)."})
    E.append({'id': 'evt:ward', 'preset': 'script', 'source': 'door:ward', 'title': 'Ward of light',
              'condition': {'not': {'map_var': 'ward_down'}}, 'lua': WARD_LUA,
              'else_effects': [{'text': "The ward is gone."}],
              'notes': "Morgana's door: its click names both lamps (D-42 (6)); one lamp out: 'The ward thins, but holds.'"})
    # the vault
    E.append({'id': 'evt:vault_lever', 'preset': 'switch', 'source': 'switch:vault_lever', 'title': 'Lever',
              'condition': {'not': {'map_var': 'vault_open'}}, 'opens': ['door:vault'], 'sets': {'map_var': 'vault_open'},
              'effects': [{'text': "Far below, iron grinds."}], 'locked_text': "The lever is down.",
              'notes': "key:vault_lever: the lever under the guild's seal raises the vault's iron door, once."})
    E.append({'id': 'evt:vault_door', 'preset': 'script', 'source': 'door:vault', 'title': 'Iron door',
              'condition': {'not': {'map_var': 'vault_open'}},
              'effects': [{'text': "An iron door with no handle on this side. The guild's seal is cut into it."}],
              'else_effects': [{'text': "The iron door stands raised."}], 'notes': "The vault's iron door."})
    # the ambush
    E.append({'id': 'evt:chest_quarters_w', 'preset': 'script', 'source': 'chest:quarters_w', 'title': 'Chest',
              'condition': {'not': {'map_var': 'ambushed'}},
              'effects': [{'set': {'var': {'map_var': 'ambushed'}, 'value': 1}}, {'show_actors': AMBUSH_GROUP},
                          {'message': "Ambush!"}, {'open_chest': 'chest:quarters_w'}],
              'else_effects': [{'open_chest': 'chest:quarters_w'}],
              'notes': "poi:ambush (aaze0031:56): the first opening shows the four hidden wizards (D-18; a map variable, kept after a reload)."})
    # Blastem
    E.append({'id': 'evt:blastem', 'preset': 'script', 'source': 'platform:blastem_table', 'title': 'Blastem the Wizard',
              'lua': BLASTEM_LUA,
              'notes': "Blastem (NPC 5248, A4's row and A3's topics The lesson / Boots licked) talks through his table until A2's row of his own stands there; after the lesson his chair is empty."})
    E.append({'id': 'evt:blastem_swap', 'preset': 'script', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'blastem_angered', 'not': {'map_var': 'blastem_swapped'}},
              'effects': [{'set': {'var': {'map_var': 'blastem_swapped'}, 'value': 1}}, {'hide_actors': BLASTEM_BODY},
                          {'show_actors': BLASTEM_HOSTILE}, {'lua': 'XeenQuests.hook("q-d14.blastem")'}],
              'notes': "q-d14.blastem: once blastem_angered (113286) the talking Blastem gives way to Sorcerer 11191, hostile (Valio's pattern)."})
    E.append({'id': 'evt:blastem_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'blastem_angered'},
              'effects': [{'hide_actors': BLASTEM_BODY}, {'show_actors': BLASTEM_HOSTILE}],
              'notes': "The swap holds on every later load."})
    # devices
    E.append({'id': 'evt:font', 'preset': 'script', 'source': 'platform:font', 'title': 'Font', 'lua': FONT_LUA,
              'effects': [{'text': "+2000 spell points."}],
              'notes': "poi:font (aaze0031:61): every member's spell points refilled, repeatable (D-42 (7))."})
    E.append({'id': 'evt:orange_potion', 'preset': 'script', 'source': 'platform:alcove_orange', 'title': 'Alcove',
              'lua': 'XeenQuests.hook("q-d14.orange_potion")',
              'notes': "The Orange Potion (aaze0031:57-58): A3's hook decides for the clicking member (player bit 11350)."})
    E.append({'id': 'evt:purple_potion', 'preset': 'script', 'source': 'platform:alcove_purple', 'title': 'Alcove',
              'lua': 'XeenQuests.hook("q-d14.purple_potion")',
              'notes': "The Purple Potion (aaze0031:59-60): A3's hook (player bit 11351)."})
    # things to read
    for src, title, text in (
            ('platform:bed_w1', 'Bed', "Nothing here."), ('platform:bed_e1', 'Bed', "Nothing here."),
            ('panel:painted_door', 'A painted door', "A painted door. Only paint on the brick."),
            ('platform:crystal', 'Crystal', "The crystal shows the court below, and a party in it, looking up."),
            ('platform:xenoc_desk', 'Desk', "A treatise on the inferiority of everyone else, in Xenoc's hand. Unfinished."),
            ('platform:xenoc_chair', "Xenoc's chair", "A tall chair on a dais, set where its owner can look down on the hall."),
            ('platform:scales', 'Weights and Measures', "Scales and ledgers: the wizards taxed the quarter by the ounce."),
            ('platform:still', 'Still', "Retorts and a still, cold. The bottles on the shelves are empty."),
            ('panel:triple_window', 'Window', "The triple window looks down on the court.")):
        key = src.split(':')[1]
        E.append({'id': f'evt:read_{key}', 'preset': 'text', 'source': src, 'title': title, 'window': False, 'text': text})
    for c in ('study', 'wardrobe', 'weights', 'quarters_e', 'hoard'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    return E


def wiring():
    vars_ = ['bolt_drawn', 'lamp_scry', 'lamp_robe', 'ward_down', 'vault_open', 'ambushed', 'blastem_swapped']
    return {'format': 0, 'variables': vars_, 'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-19's events, written by output/studio_cal/dd19/tools/dress.py."}


ATMOSPHERE = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_darkside_fading'},
              'notes': "The guild court is open to Darkside's sky (its ceiling a sky face; DD-03's and DD-14's route): the fading preset of Act IV before M27 (D-42)."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
    gen.dump(folder / 'atmosphere.yml', ATMOSPHERE)
