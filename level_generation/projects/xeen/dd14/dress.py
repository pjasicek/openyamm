#!/usr/bin/env python3
"""DD-14 Castle Blackfang, L4: objects.yml, wiring.yml, atmosphere.yml (written by gen.py L4)."""
import geo

VAMPIRE, LORD, ROYAL, COUNT = 11291, 11292, 11295, 11294
SENTINEL, OVERLORD, OCTOPOD = 11551, 11552, 11473   # 11473: A2's indoor Octopod D, no swimmer AI (D-52)
NAME = {VAMPIRE: 'vampire', LORD: 'lord', ROYAL: 'royal', SENTINEL: 'sentinel', OVERLORD: 'overlord',
        OCTOPOD: 'octopod'}
GROUP = {VAMPIRE: 1, LORD: 1, SENTINEL: 2, OVERLORD: 2, OCTOPOD: 3}
COUNT_GROUP = 5
GRIFFIN_HIDDEN = True
GRIFFIN, GRIFFIN_GROUP = 11913, 30   # A2's Tethered Griffin (D6's figure): placed only, peaceful
AMBROSE, QUEEN, QUEEN_GROUP = 11917, 11918, 31   # A2's peaceful placed-only rows (D-52); Ambrose in the griffin's group
IMMOBILE_OCTOPODS = True
# The sleepers (D-18): each its own group, shown when its coffin is opened.
SLEEPERS = {'dorm_w1': (VAMPIRE, 11), 'dorm_w3': (VAMPIRE, 12), 'dorm_e2': (VAMPIRE, 13),
            'crypt_dutchess': (LORD, 14), 'crypt_lady': (LORD, 15)}

CANDLE = [235, 175, 115]
HALL = [215, 175, 130]
TORCH = [240, 160, 90]
COLD = [150, 160, 180]
NIGHT = [120, 125, 160]
DUNGEON = [170, 140, 110]
WATERL = [110, 140, 150]

QUEEN_NPC, AMBROSE_NPC = 5001, 5512
D4_SETDOWN = (6144, 5120, 1216, 1024)     # D4's entrance:dd14_griffin (assets_dev/worlds/xeen/maps/xeen_d4.studio.yml)
ARRIVAL_AT = [0, -1472]
# The cistern's octopods (D-52 (5)): west bank two, south and north banks one each, the far (east) ledge one.
OCTO_AT = [[1776, 1152], [1776, 2560], [2176, 752], [2176, 2960], [2576, 1600]]
AMBROSE_AT, QUEEN_AT = [96, -1840], [-880, -192]


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
DOUBLE = ['gallery_chapel', 'yard_stairhall', 'yard_great', 'stairhall_throne']
SINGLE = [
    # key, opening, surface, notes
    ('north_keep', 'open:north_keep', geo.IRONDOOR, "The keep's iron-bound door from the north walk into the bat roost."),
    ('countess_dorm', 'open:countess_dorm', geo.IRONDOOR, "An iron-bound door between the Countess's rooms and the sleeping hall (was the slab twb1a, F12, A8 session 26)."),
    ('cellar_kitchen', 'open:cellar_kitchen', geo.IRONDOOR, "The cellar's iron-bound door from the kitchen (was the slab twb1a)."),
    ('throne_crypt', 'open:throne_crypt', geo.IRONDOOR, "The crypt's iron door behind the dais."),
    ('dstair_question', 'open:dstair_question', geo.IRONDOOR, "The question room's iron door at the stair's foot."),
]
DOUBLE_NOTES = {
    'gallery_chapel': "The black chapel's double doors from the long gallery: two hinged oak leaves (chb1dl|chb1dr).",
    'yard_stairhall': "The keep door from the courtyard into the grand stair hall: two hinged oak leaves.",
    'yard_great': "The great hall's double doors on the courtyard: two hinged oak leaves.",
    'stairhall_throne': "The Count's hall's double doors from the grand stair hall: two hinged oak leaves.",
}


def doors():
    out = []
    for k in DOUBLE:
        out.append({'id': f'door:{k}', 'opening': f'open:{k}', 'kind': 'hinged', 'leaves': 2,
                    'pictures': [list(map(dict, r)) for r in geo.OAK],
                    'back_pictures': [list(map(dict, r)) for r in geo.OAK], 'notes': DOUBLE_NOTES[k]})
    for k, op, s, n in SINGLE:
        out.append({'id': f'door:{k}', 'opening': op, 'kind': 'slide_left', 'surface': dict(s, fit=True), 'notes': n})
    out.append({'id': 'door:bar', 'opening': 'open:throne_dstair', 'kind': 'slide_up', 'surface': dict(geo.IRONDOOR, fit=True),
                'notes': "The dungeon stair's bar: a plain black iron leaf (D-42 (6)); it lifts at the Count's death (m27.blackfang) and stays up (blackfang_slain)."})
    out.append({'id': 'door:yard_gate', 'opening': 'open:yard_gate', 'kind': 'slide_up', 'surface': dict(geo.GRILLE, fit=True),
                'notes': "The yard gate at the courtyard stair's head: iron bars; its bar on the stair's side (switch:yard_bar)."})
    out.append({'id': 'door:study_panel', 'opening': 'open:keep_study', 'kind': 'slide_left',
                'surface': dict(geo.HALLWALL, fit=True), 'back_surface': dict(geo.BROWN, fit=True),
                'notes': "The panel in the keep's upper hall's north wall: the gong in the north-west tower slides it open (aaze0045:6-7)."})
    return out


def movers():
    return [{'id': 'mover:hatch', 'room': R('cellar'), 'at': geo.HATCH_AT, 'size': [256, 256], 'floor_height': 0,
             'bottom': 0, 'height': 8, 'travel': [0, 240, 0], 'speed': 160, 'surface': dict(geo.HATCH),
             'top_surface': dict(geo.HATCH),
             'notes': "The cellar's trapdoor over the ladder shaft; the bolt below slides it aside."}]


def switches():
    return [
        {'id': 'switch:hatch_bolt', 'room': R('shaft'), 'kind': 'lever', 'at': [-1408, -640], 'reach': 48,
         'notes': "The trapdoor's bolt, on the shaft's east wall by the ladder."},
        {'id': 'switch:yard_bar', 'room': R('courtyard'), 'kind': 'lever', 'at': [-736, -1024], 'floor_height': geo.L1,
         'reach': 48, 'notes': "The yard gate's bar, on the courtyard stair's head beside the gate."},
    ]


def ladders():
    hx, hy = geo.HATCH_AT
    return [{'id': 'ladder:shaft', 'room': R('shaft'), 'at': [hx - 72, hy], 'facing': 'w', 'height': -geo.DUN,
             'exit': [hx - 240, hy], 'grab_at_top': True, 'surface': geo.S_('bemv', 32, 256, uneven=True),
             'notes': "The ladder up the shaft through the cellar's trapdoor (Zarkon's Kloikus fell off it)."}]


def plates():
    return [{'id': f'plate:fire_{i}', 'room': R('east_walk'), 'at': [2048, y], 'size': [384, 256],
             'surface': dict(geo.FLAGS), 'notes': "A pressure plate in a darker slab: fire from the merlons."}
            for i, y in enumerate((-768, -256, 256, 768), 1)] + [
        {'id': 'plate:stair_force', 'room': R('throne'), 'at': [-1152, 2752], 'size': [192, 192],
         'surface': dict(geo.DARKFLAGS), 'notes': "The step before the bar: the force like wind (m27.dungeon_stair)."}]


def chests():
    return [
        {'id': 'chest:roost', 'room': R('keep_top'), 'at': [1088, 2752], 'facing': 'w', 'treasure_level': 4,
         'random_items': 2, 'gold': 900, 'notes': "A strongbox under the droppings."},
        {'id': 'chest:study', 'room': R('study'), 'at': [-512, 3168], 'facing': 'w', 'treasure_level': 4,
         'random_items': 2, 'gold': 1200, 'notes': "The Count's strongbox."},
        {'id': 'chest:hoard', 'room': R('crypt'), 'at': [-448, 4224], 'facing': 'n', 'treasure_level': 5,
         'random_items': 3, 'gold': 4000, 'notes': "The castle's hoard, at the foot of the Count's own coffin."},
        {'id': 'chest:question', 'room': R('question'), 'at': [-2304, 2240], 'facing': 'e', 'treasure_level': 4,
         'random_items': 2, 'gold': 700, 'notes': "The gaolers' strongbox."},
        {'id': 'chest:cistern', 'room': R('cistern'), 'at': [2880, 1856], 'treasure_level': 4,
         'random_items': 2, 'gold': 800, 'notes': "On the far ledge, past the pool."},
    ]


V, VL, GS, GO, RV = VAMPIRE, LORD, SENTINEL, OVERLORD, ROYAL
PLACED = {
    'sw_tower': [(V, [-1600, -1344]), (V, [-2240, -1344])],
    'west_walk': [(GS, [-1920, -640]), (GS, [-1920, 0]), (GS, [-1920, 640])],
    'nw_tower': [(V, [-2176, 1664]), (V, [-1664, 1920])],
    'north_walk': [(GS, [-768, 1408]), (GS, [768, 1408]), (GO, [0, 1408])],
    'keep_top': [(V, [-640, 2368]), (V, [640, 2368])],
    'ne_tower': [(V, [1664, 1664]), (V, [1792, 1408])],
    'east_walk': [(GS, [1600, -512]), (GS, [1600, 512]), (GO, [1600, 0])],
    'south_gallery': [(V, [-1024, -1664]), (V, [-640, -1664]), (V, [-320, -1664])],
    'chapel2': [(V, [320, -1472]), (V, [960, -1472]), (VL, [448, -1792]), (VL, [832, -1792])],
    'library': [(V, [1920, 0]), (V, [1920, 1664])],
    'keep_hall2': [(V, [-1920, 1792]), (V, [-1152, 1792]), (V, [-640, 2048]), (VL, [-1536, 2048])],
    'countess': [(VL, [-1920, 448]), (VL, [-1664, 704])],
    'coffin_dorm': [(V, [-2048, -768]), (V, [-2048, -256])],
    'cellar': [(V, [-2176, -640]), (V, [-1920, -896])],
    'kitchen': [(V, [-2048, 384]), (V, [-1664, 640])],
    'courtyard': [(GS, list(p)) for p in geo.PLINTHS],
    'stair_hall3': [(V, [192, 1536]), (V, [1088, 1536])],
    'great_hall': [(V, [-1920, 1408]), (V, [-1152, 2176]), (V, [-704, 2048]), (VL, [-1600, 2240])],
    'dstair': [(V, [-2112, 3584]), (V, [-2112, 3200])],
    'cells': [(V, [-1920, 128]), (V, [-1920, 896])],
    'undercroft': [(V, [-960, 1344]), (V, [256, 2000]), (V, [768, 2624]), (VL, [-320, 2624]), (VL, [256, 1344])],
    # each just inside the pool's edge (POOL x 1664-2688, y 640-3072), in melee reach of the bank or the far ledge
    'cistern': [(OCTOPOD, OCTO_AT[0]), (OCTOPOD, OCTO_AT[1]), (OCTOPOD, OCTO_AT[2]), (OCTOPOD, OCTO_AT[3]),
                (OCTOPOD, OCTO_AT[4])],
}
THRONE_GROUP = [(COUNT, [-704, 3264]), (RV, [-512, 3008]), (RV, [-512, 3520]), (RV, [-384, 3264])]
SLEEPER_AT = {k: list(c) for k, room, c, ax in geo.COFFINS if k in SLEEPERS}   # on the coffin: rises from it


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at in lst:
            n[row] = n.get(row, 0) + 1
            d = {'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                 'facing': 270, 'group': GROUP[row]}
            if row == OCTOPOD:
                d['immobile'] = IMMOBILE_OCTOPODS
                d['notes'] = "Octopod D (A2's indoor row, D-52 (5)): stationary in the cistern's water by its edge, where a blow from the bank or the ledge reaches it."
            out.append(d)
    out.append({'id': 'monster:count', 'room': R('throne'), 'monster': COUNT, 'at': THRONE_GROUP[0][1], 'facing': 0,
                'group': COUNT_GROUP,
                'notes': "Count Blackfang (11294, 70, blink): m27.blackfang at his death lifts the dungeon stair's bar."})
    for i, (row, at) in enumerate(THRONE_GROUP[1:], 1):
        out.append({'id': f'monster:royal_{i}', 'room': R('throne'), 'monster': row, 'at': at, 'facing': 180,
                    'group': COUNT_GROUP, 'notes': "One of the Count's three guards (Royal Vampire 11295, 58, D-42 (2))."})
    out.append({'id': 'monster:griffin', 'room': R('landing'), 'monster': GRIFFIN, 'at': [320, -1856], 'facing': 90,
                'group': GRIFFIN_GROUP, 'immobile': True, 'hidden': GRIFFIN_HIDDEN,
                'notes': "Ambrose's griffin (A2's Tethered Griffin 11913, D6's figure, friendly, immobile, not counted) on its perch; shown from m25.done (evt:griffin_load)."})
    out.append({'id': 'monster:ambrose', 'room': R('landing'), 'monster': AMBROSE, 'at': AMBROSE_AT, 'facing': 90,
                'hostile': False, 'group': GRIFFIN_GROUP, 'immobile': True, 'hidden': GRIFFIN_HIDDEN, 'npc': AMBROSE_NPC,
                'notes': "Ambrose (A2's row 11917, D-52 (6)) beside his griffin by the perch, NPC 5512: clicked, he talks; his topic Fly us out (A3, from m25.done) runs m27.fly_out. In the griffin's group, shown from m25.done (evt:griffin_load) and never hidden after; takes no damage (evt:figures_load)."})
    out.append({'id': 'monster:queen', 'room': R('queen_cell'), 'monster': QUEEN, 'at': QUEEN_AT, 'facing': 180,
                'hostile': False, 'group': QUEEN_GROUP, 'immobile': True, 'npc': QUEEN_NPC,
                'notes': "Queen Kalindra (A2's row 11918, D-52 (6)) by the bench in her cell, facing the cell's open grille door (west; she faced the wall until session 23), NPC 5001: clicked, A3's topic The crown. Hidden on load once done 111542 is set (evt:queen_load); takes no damage (evt:figures_load)."})
    for key, (row, grp) in SLEEPERS.items():
        room = 'coffin_dorm' if key.startswith('dorm') else 'crypt'
        out.append({'id': f'monster:sleeper_{key}', 'room': R(room), 'monster': row, 'at': SLEEPER_AT[key],
                    'facing': 90, 'group': grp, 'hidden': True,
                    'notes': f"A sleeper (D-18): placed hidden, shown when coffin {key} is opened (counted at load); still rises after the Count's death (D-42 (5))."})
    return out


# (key, decoration, room, at, floor height or None, title)
DECOS = [
    ('landing_bones', '7dec18', 'landing', [-256, -2048], None, 'Bones'),
    ('tower_bones', '7dec18', 'sw_tower', [-2432, -1344], None, 'Bones'),
    ('zarkon_bones', '7dec18', 'shaft', [-2176, -896], None, 'Bones'),
    ('rat_bones', 'dec29', 'shaft', [-2240, -512], None, 'Bones'),
    ('cask_find', '7dec21', 'cellar', [-2304, -896], None, 'Cask'),
]
# (key, decoration, room, at, floor height or None, hangs)
PROPS = [
    ('keep2_chandelier_w', 'chndlir0', 'keep_hall2', [-1792, 1792], None, True),
    ('keep2_chandelier_e', 'chndlir0', 'keep_hall2', [-768, 1792], None, True),
    ('great_chandelier_w', 'chndlir0', 'great_hall', [-1792, 1792], None, True),
    ('great_chandelier_e', 'chndlir0', 'great_hall', [-768, 1792], None, True),
    ('throne_chandelier', 'chndlir0', 'throne', [0, 3200], None, True),
    ('throne_candle_s', 'dec02', 'throne', [-1088, 3008], None, False),
    ('throne_candle_n', 'dec02', 'throne', [-1088, 3520], None, False),
    ('altar_candle_w', 'dec02', 'chapel2', [288, -2016], None, False),
    ('altar_candle_e', 'dec02', 'chapel2', [992, -2016], None, False),
    ('crypt_brazier_sw', 'flamb00', 'crypt', [-1216, 4032], None, False),
    ('crypt_brazier_se', 'flamb00', 'crypt', [-64, 4032], None, False),
    ('crypt_brazier_nw', 'flamb00', 'crypt', [-1216, 4928], None, False),
    ('crypt_brazier_ne', 'flamb00', 'crypt', [-64, 4928], None, False),
    # the great hall's long table: goblets and plates
    ('goblet_1', '7dec46', 'great_hall', [-2048, 1728], 80, False),
    ('goblet_2', '7dec48', 'great_hall', [-1792, 1856], 80, False),
    ('goblet_3', '7dec46', 'great_hall', [-1536, 1728], 80, False),
    ('goblet_4', '7dec48', 'great_hall', [-1280, 1856], 80, False),
    ('plates_1', 'dec39', 'great_hall', [-1920, 1792], 80, False),
    ('plates_2', 'dec39', 'great_hall', [-1408, 1792], 80, False),
    # the cask cellar (a storeroom): casks and barrels along the walls
    ('cask_1', '7dec21', 'cellar', [-2304, -640], None, False),
    ('cask_2', '7dec21', 'cellar', [-2304, -512], None, False),
    ('cask_3', '7dec21', 'cellar', [-2176, -512], None, False),
    ('barrel_1', 'bigbarel', 'cellar', [-1536, -960], None, False),
    ('barrel_2', 'bigbarel', 'cellar', [-1664, -960], None, False),
    ('barrel_3', 'bigbarel', 'cellar', [-2048, -960], None, False),
    ('barrel_4', 'bigbarel', 'cellar', [-2176, -960], None, False),
    ('keg_1', 'smlbarel', 'cellar', [-2304, -768], None, False),
    # the kitchen: barrels in pairs by the walls, bowls on the table
    ('kitchen_barrel_1', 'bigbarel', 'kitchen', [-2368, -192], None, False),
    ('kitchen_barrel_2', 'bigbarel', 'kitchen', [-2240, -192], None, False),
    ('kitchen_barrel_3', 'bigbarel', 'kitchen', [-2368, 960], None, False),
    ('kitchen_barrel_4', 'bigbarel', 'kitchen', [-2240, 960], None, False),
    ('kitchen_bowl', 'foodbowl', 'kitchen', [-1920, 704], 80, False),
    # the question room's instruments, the shaft's dead
    ('question_skulls', 'sklplrev', 'question', [-1536, 1536], None, False),
    ('cell_bones_1', 'dec29', 'cells', [-2304, 512], None, False),
    ('cell_bones_2', 'dec05', 'cells', [-2304, -128], None, False),
    ('undercroft_bones', 'dec29', 'undercroft', [-1088, 3136], None, False),
]
# (room, wall, along, decoration)
SCONCES = [
    # the walks: torches on the towers' walls at each end
    ('west_walk', 's', 0.2, 'torch01'), ('west_walk', 'n', 0.8, 'torch01'),
    ('east_walk', 's', 0.8, 'torch01'), ('east_walk', 'n', 0.2, 'torch01'),
    ('north_walk', 'w', 0.15, 'torch01'), ('north_walk', 'e', 0.85, 'torch01'),
    ('landing', 'w', 0.25, 'torch01'), ('landing', 'e', 0.75, 'torch01'),
    # the towers and the roost
    ('nw_tower', 'w', 0.5, 'torch02'), ('ne_tower', 'n', 0.3, 'torch02'), ('keep_top', 'e', 0.5, 'torch02'),
    ('keep_top', 'w', 0.5, 'torch02'),
    # L2
    ('south_gallery', 's', 0.25, 'scon100'), ('south_gallery', 's', 0.75, 'scon100'), ('south_gallery', 'n', 0.5, 'scon100'),
    ('chapel2', 'n', 0.3, 'scon100'), ('chapel2', 'n', 0.7, 'scon100'),
    ('library', 'w', 0.15, 'scon100'), ('library', 'w', 0.5, 'scon100'), ('library', 'e', 0.85, 'scon100'),
    ('keep_hall2', 's', 0.15, 'scon100'), ('keep_hall2', 'n', 0.85, 'scon100'),
    ('study', 'w', 0.5, 'scon100'), ('countess', 'w', 0.3, 'scon100'), ('countess', 'e', 0.7, 'scon100'),
    ('coffin_dorm', 'n', 0.5, 'torch02'), ('coffin_dorm', 's', 0.3, 'torch02'),
    # L3
    ('kitchen', 'n', 0.5, 'torch02'), ('cellar', 'e', 0.5, 'torch02'), ('great_hall', 'n', 0.15, 'scon100'),
    ('great_hall', 's', 0.15, 'scon100'), ('throne', 'n', 0.6, 'scon100'), ('throne', 's', 0.85, 'scon100'),
    ('stair_hall3', 'e', 0.25, 'scon100'), ('stair_hall3', 'w', 0.25, 'scon100'), ('back_stair', 's', 0.3, 'torch02'),
    ('courtyard', 'n', 0.5, 'torch01'), ('courtyard', 'e', 0.5, 'torch01'), ('courtyard', 'w', 0.85, 'torch01'),
    # the dungeon
    ('dstair', 'w', 0.6, 'torch02'), ('question', 'e', 0.4, 'torch02'), ('cells', 'e', 0.9, 'torch02'),
    ('cells', 'e', 0.32, 'torch02'), ('shaft', 'w', 0.5, 'torch02'),
    ('undercroft', 'w', 0.4, 'torch02'), ('undercroft', 'e', 0.8, 'torch02'), ('undercroft', 'n', 0.5, 'torch02'),
    ('cistern', 'w', 0.15, 'torch02'), ('cistern', 'w', 0.85, 'torch02'),
]


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


THEME_COL = {'theme:walk': NIGHT, 'theme:yard': NIGHT, 'theme:tower': TORCH, 'theme:hall': HALL, 'theme:gallery': HALL,
             'theme:chapel': CANDLE, 'theme:library': CANDLE, 'theme:service': TORCH, 'theme:crypt': COLD,
             'theme:dungeon': DUNGEON, 'theme:cistern': WATERL}
# Where a two-storey room's light stands (in its open part, under the head's height).
OPEN_AT = {'sw_tower': ([-2240, -1984], 448), 'se_tower': ([2240, -1984], 448), 'stair_hall3': ([224, 1600], 448),
           'back_stair': ([-3584, 448], 448), 'dstair': ([-2112, 3456], 384)}
DIM = {'shaft': 0.6, 'queen_cell': 0.0}


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
        if DIM.get(room, 1) == 0:
            continue
        (w, h), c = geo.extent(room)
        col = THEME_COL[geo.R[room][4]]
        if room in OPEN_AT:
            at, hh = OPEN_AT[room]
            add(room, at, 1100, col, height=hh)
            continue
        r = int(min(2000, max(700, 0.6 * max(w, h))) * DIM.get(room, 1))
        if max(w, h) > 2400:
            ax = 0 if w >= h else 1
            for f in (0.25, 0.75):
                p = list(c)
                lo = c[ax] - (w if ax == 0 else h) / 2
                p[ax] = int(lo + f * (w if ax == 0 else h))
                add(room, p, int(r * 0.75), col, height=320 if geo.R[room][3] - geo.R[room][2] > 400 else None)
        else:
            add(room, c, r, col, height=320 if geo.R[room][3] - geo.R[room][2] > 400 else None)
    add('throne', [-960, 3264], 700, [230, 120, 90], height=256, notes="The candelabra by the throne.")
    add('crypt', [-640, 4480], 900, [235, 150, 90], height=96, notes="The braziers' glow.")
    add('cells', [-1536, 0], 500, TORCH, height=224, notes="The torch outside the Queen's cell (none inside it).")
    return L


def sounds():
    return [
        {'id': 'sound:wind_landing', 'room': R('landing'), 'at': [0, -1664], 'sound': 'whistling wind', 'radius': 2000,
         'inner_radius': 700, 'volume': 0.45, 'notes': "Wind over the battlements."},
        {'id': 'sound:gust_landing', 'room': R('landing'), 'at': [0, -1920], 'sound': 'xeen_sky_gust', 'radius': 2400,
         'inner_radius': 900, 'volume': 0.35, 'wait': [6, 14], 'notes': "Gusts off the lake."},
        {'id': 'sound:wind_west', 'room': R('west_walk'), 'at': [-1920, 0], 'sound': 'whistling wind', 'radius': 1600,
         'inner_radius': 500, 'volume': 0.35, 'notes': "Wind on the west walk."},
        {'id': 'sound:wind_north', 'room': R('north_walk'), 'at': [0, 1408], 'sound': 'whistling wind', 'radius': 1800,
         'inner_radius': 500, 'volume': 0.35, 'notes': "Wind on the north walk."},
        {'id': 'sound:wind_east', 'room': R('east_walk'), 'at': [1920, 0], 'sound': 'whistling wind', 'radius': 1600,
         'inner_radius': 500, 'volume': 0.35, 'notes': "Wind on the east walk."},
        {'id': 'sound:yard_wind', 'room': R('courtyard'), 'at': [0, 0], 'sound': 'xeen_amb_sky', 'radius': 2000,
         'inner_radius': 800, 'volume': 0.3, 'pan': False, 'notes': "The open air over the courtyard: a bed, not panned (D-48)."},
        {'id': 'sound:roost', 'room': R('keep_top'), 'at': [0, 2368], 'sound': 'xeen_amb_tower', 'radius': 1800,
         'inner_radius': 600, 'volume': 0.4, 'pan': False, 'notes': "The roost's draughts and rustling: a bed, not panned (D-48)."},
        {'id': 'sound:cells', 'room': R('cells'), 'at': [-1920, 512], 'sound': 'drip02', 'radius': 1800,
         'inner_radius': 400, 'volume': 0.45, 'wait': [2, 6], 'notes': "Water dripping in the cells."},
        {'id': 'sound:undercroft', 'room': R('undercroft'), 'at': [-128, 1856], 'sound': 'drip03', 'radius': 2000,
         'inner_radius': 500, 'volume': 0.4, 'wait': [3, 8], 'notes': "Drips under the low vault."},
        {'id': 'sound:cistern', 'room': R('cistern'), 'at': [2176, 1856], 'sound': 'water lapping loop', 'radius': 2000,
         'inner_radius': 700, 'volume': 0.4, 'notes': "The black water stirring."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('landing'), 'at': ARRIVAL_AT, 'facing': 'n',
                  'notes': "Where Ambrose's griffin sets the party down: the middle of the landing, facing north over the inner parapet (the courtyard below, the keep beyond)."},
        'arrivals': [
            {'entrance': 'entrance:d4_griffin', 'room': R('landing'), 'at': ARRIVAL_AT, 'facing': 'n',
             'notes': "From D4's gate (m25.gate_flight, A6), D-42 Q1."},
            {'entrance': 'entrance:d6_griffin', 'room': R('landing'), 'at': ARRIVAL_AT, 'facing': 'n',
             'notes': "From D6's Griffin Pass (m25.flight; D6 is phase 5): the same spot (D-42)."},
        ],
        'doors': doors(), 'movers': movers(), 'switches': switches(), 'ladders': ladders(), 'plates': plates(),
        'chests': chests(), 'monsters': monsters(), 'decorations': decorations(), 'lights': lights(),
        'sounds': sounds(),
        'notes': "DD-14's contents, written by output/studio_cal/dd14/tools/dress.py: 12 doors (four double doors as hinged oak pairs, the bar, the yard gate, the study's panel), the cellar's trapdoor (a mover) and its bolt, the yard gate's bar, one ladder, four fire plates, five chests, 70 placed monsters (39 Vampires, 10 Vampire Lords, 3 Royal Vampires, Count Blackfang, 10 Gargoyle Sentinels, 2 Gargoyle Overlords, 5 Octopods D; five of them sleepers in coffins, placed hidden), and, not counted, Ambrose's griffin, Ambrose (npc 5512) and Queen Kalindra (npc 5001), peaceful and unhurt (D-52).",
    }


# ------------------------------------------------------------------------------------------------- wiring
NOTES_LANDING = ("You find a page of notes in the bones: Coffins contain treasure and vampires. Floor traps are "
                 "regularly spaced. Remember to get Sorcerer to Jump us over them. The Count's magic keeps us from "
                 "descending. Be sure to kill him when we get a chance.")
DIARY_TOWER = ("You find a diary in the bones: ...entering the black castle today. The Queen is captive somewhere "
               "within its walls, and we must remain inside the castle 'til nightfall or she would surely die once we "
               "brought her into the light. ...")
DIARY_ZARKON = ("You find a diary in the bones: 1/9/753: Kloikus Thunbeard the Round came to a bad end today. He was "
                "struggling up a ladder in his ridiculous armor when one of those vampires grabbed for his ankles "
                "through a hole in the wall. He fell a good forty feet.")
DIARY_RATS = ("You find a diary in the bones, but it has mostly been devoured by rats. None of what remains is "
              "legible.")
EMPTY = "The coffin is empty."
LINEAGE = ("The Blackfang Lineage, in a dry hand: four names are copied out large on the last page, with a line for "
           "each coffin in the family crypt: Dutchess Blackfang, Countess Blackfang, Count Blackfang, Lady Blackfang.")
LEDGER = ("The Count's ledger. The last entry reads: 'Received from Lord Xeen's man: one queen, crowned. Crown kept by "
          "her people. No matter.'")
CRYPT_NAMES = {'crypt_dutchess': 'Dutchess Blackfang', 'crypt_countess': 'Countess Blackfang',
               'crypt_count': 'Count Blackfang', 'crypt_lady': 'Lady Blackfang'}
# Coffin contents: key: (find gold or 0, find text or None)
FINDS = {
    'dorm_w1': (300, "Under the sleeper, a purse."), 'dorm_w2': (250, "A purse of old coins under the shroud."),
    'dorm_w3': (300, "Under the sleeper, a purse."), 'dorm_e1': (200, "A few coins pressed into the dead wood."),
    'dorm_e2': (350, "Under the sleeper, a purse."), 'dorm_e3': (250, "A purse of old coins under the shroud."),
    'ne_1': (400, "A purse of coins and a dried rose."), 'crypt_dutchess': (500, "Grave goods: a purse of old coins."),
    'crypt_lady': (500, "Grave goods: a purse of old coins."),
}
RISE = "The lid flies back and a vampire rises from the coffin!"


def coffin_events():
    E = []
    for key, room, c, ax in geo.COFFINS:
        title = CRYPT_NAMES.get(key, 'Coffin')
        src = f'platform:coffin_{key}'
        var = f'coffin_{key}'
        if key in SLEEPERS:
            grp = SLEEPERS[key][1]
            gold, text = FINDS[key]
            E.append({'id': f'evt:coffin_{key}', 'preset': 'script', 'source': src, 'title': title,
                      'condition': {'not': {'map_var': var}}, 'else_effects': [{'text': EMPTY}],
                      'effects': [{'set': {'var': {'map_var': var}, 'value': 1}}, {'show_actors': grp},
                                  {'lua': 'evt.PlaySoundName("xeen_coffin_lid")'}, {'gold': gold},
                                  {'message': f"{RISE} {text} (+{gold} gold)"}],
                      'notes': f"A sleeper's coffin (D-18): the first opening shows group {grp} (counted at load) and gives its find; then 'The coffin is empty.' (aaze0047:2). Still rises after the Count's death (D-42 (5))."})
        elif key in FINDS:
            gold, text = FINDS[key]
            E.append({'id': f'evt:coffin_{key}', 'preset': 'script', 'source': src, 'title': title,
                      'condition': {'not': {'map_var': var}}, 'else_effects': [{'text': EMPTY}],
                      'effects': [{'set': {'var': {'map_var': var}, 'value': 1}}, {'gold': gold},
                                  {'text': f"{text} (+{gold} gold)"}],
                      'notes': "A coffin with a find (once), then 'The coffin is empty.' (aaze0047:2)."})
        elif key == 'se_loot':
            E.append({'id': f'evt:coffin_{key}', 'preset': 'script', 'source': src, 'title': title,
                      'condition': {'not': {'map_var': var}}, 'else_effects': [{'text': EMPTY}],
                      'effects': [{'set': {'var': {'map_var': var}, 'value': 1}}, {'gold': 1500},
                                  {'give_item': {'level': 4, 'kind': 40}},
                                  {'message': "Loot hidden in a coffin: a heap of gold and a ring. (+1500 gold)"}],
                      'notes': "The south-east tower's coffin of loot (a find: gold and a ring), once."})
        elif key == 'crypt_count':
            E.append({'id': f'evt:coffin_{key}', 'preset': 'text', 'source': src, 'title': title, 'window': False,
                      'text': "Count Blackfang's own coffin, lined with black silk. His strongbox stands at its foot.",
                      'notes': "The Count's coffin (aaze0047:8); the hoard is chest:hoard at its foot."})
        else:
            E.append({'id': f'evt:coffin_{key}', 'preset': 'text', 'source': src, 'title': title, 'window': False,
                      'text': EMPTY, 'notes': "'Coffin' / 'The coffin is empty.' (aaze0046:0, aaze0047:1-2)."})
    return E


PERCH_LUA = "\n".join([
    'if continueStep == 1 then',
    '    XeenQuests.hook("m27.fly_out")',
    '    return',
    'end',
    'if continueStep ~= nil then',
    '    return',
    'end',
    'if not XeenQuests.can("m27.fly_out") then',
    '    evt.StatusText("A griffin\'s perch, empty.")',
    '    return',
    'end',
    'AskChoiceWithAnswerSteps(eventId, 3, "Are you ready to leave this awful place, friends?", '
    '{{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})',
])
BENCH_LUA = "\n".join([
    'if IsQBitSet(QBit(111542)) then',
    '    evt.StatusText("The cell is empty. The Queen has gone home.")',
    '    return',
    'end',
    'evt.StatusText("A stone bench.")',
])
COUNT_DEAD_LUA = "\n".join([
    'XeenQuests.hook("m27.blackfang")',
    'evt.PlaySoundName("xeen_coffin_lid")',
])
BAR_LUA = "\n".join([
    'if IsQBitSet(QBit(111540)) then',
    '    evt.StatusText("The bar is lifted; the stair lies open.")',
    '    return',
    'end',
    'XeenQuests.hook("m27.dungeon_stair")',
])


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'dd14_arrived_once'}},
              'effects': [{'lua': 'XeenQuests.hook("m27.landing")'}, {'qbit': 'dd14_arrived_once'}],
              'notes': "m27.landing: the first arrival's text (A3's, a window: 'Castle Blackfang's battlements ... The way down is through the Count.'), once (dd14_arrived_once 117480)."})
    for k in DOUBLE:
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}', 'title': 'Double doors'})
    for k, op, s, n in SINGLE:
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}', 'title': 'Door'})
    E.append({'id': 'evt:ambrose', 'preset': 'script', 'source': 'platform:perch', 'title': "Griffin's perch",
              'lua': PERCH_LUA,
              'notes': "The griffin's perch (D-42 Q1, D-52 (6)): from m25.done 'Are you ready to leave this awful place, friends?' (aaze0045:1): Yes calls m27.fly_out, whose own move sets the party down on D4 at entrance:dd14_griffin (6144, 5120, 1216) facing west; No: nothing. Before m25.done the perch is empty. Ambrose himself (monster:ambrose, npc 5512) talks when clicked."})
    E.append({'id': 'evt:figures_load', 'preset': 'script', 'trigger': 'load',
              'lua': 'evt.SetMm9ActorCanReceiveDamage(ActorIndex("monster:ambrose"), false)\n'
                     'evt.SetMm9ActorCanReceiveDamage(ActorIndex("monster:queen"), false)',
              'notes': "D-52 (6), D-51's word: Ambrose and Queen Kalindra cannot be hurt; every hit on them is zeroed, on every load."})
    E.append({'id': 'evt:griffin_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'm25_done'},
              'effects': [{'show_actors': GRIFFIN_GROUP}], 'else_effects': [{'hide_actors': GRIFFIN_GROUP}] if GRIFFIN_HIDDEN else [{'show_actors': GRIFFIN_GROUP}],
              'notes': "Ambrose's griffin stands on its perch from m25.done (111503) on, on every load (D-42 Q1)."})
    E.append({'id': 'evt:landing_bones', 'preset': 'text', 'source': 'deco:landing_bones', 'title': 'Bones',
              'window': True, 'text': NOTES_LANDING,
              'notes': "poi:notes (dark/aaze0045:5): the traps' and the stair's answer-giver."})
    E.append({'id': 'evt:tower_bones', 'preset': 'script', 'source': 'deco:tower_bones', 'title': 'Bones',
              'condition': {'not': {'map_var': 'tower_purse'}}, 'else_effects': [{'message': DIARY_TOWER}],
              'effects': [{'set': {'var': {'map_var': 'tower_purse'}, 'value': 1}}, {'gold': 300},
                          {'message': DIARY_TOWER + " Beside it, a purse. (+300 gold)"}],
              'notes': "poi:diary (dark/aaze0045:4) and a purse once (a find)."})
    E.append({'id': 'evt:zarkon_bones', 'preset': 'text', 'source': 'deco:zarkon_bones', 'title': 'Bones',
              'window': True, 'text': DIARY_ZARKON, 'notes': "poi:shaft_bones (dark/aaze0047:4)."})
    E.append({'id': 'evt:rat_bones', 'preset': 'text', 'source': 'deco:rat_bones', 'title': 'Bones', 'window': True,
              'text': DIARY_RATS, 'notes': "poi:shaft_bones (dark/aaze0047:5)."})
    E.append({'id': 'evt:gong', 'preset': 'script', 'source': 'panel:gong', 'title': 'Gong',
              'condition': {'not': {'map_var': 'study_open'}},
              'effects': [{'lua': 'evt.PlaySoundName("xeen_gong")'}, {'set': {'var': {'map_var': 'study_open'}, 'value': 1}},
                          {'text': "You hear a rumbling in the distance."}],
              'opens': ['door:study_panel'],
              'else_effects': [{'lua': 'evt.PlaySoundName("xeen_gong")'}, {'text': "You hear a rumbling in the distance."}],
              'notes': "poi:gong (dark/aaze0045:6-7): the first stroke slides open the study's panel on L2 (study_open), for good."})
    E.append({'id': 'evt:study_panel', 'preset': 'script', 'source': 'door:study_panel', 'title': 'Panel',
              'condition': {'not': {'map_var': 'study_open'}},
              'effects': [{'text': "The panel is set fast in the wall. Somewhere above, something must move it."}],
              'else_effects': [{'text': "The panel stands open."}],
              'notes': "The study's panel: shut until the gong."})
    E.append({'id': 'evt:roof_trapdoor', 'preset': 'text', 'source': 'platform:roof_trapdoor', 'title': 'Trapdoor',
              'window': False, 'text': "A trapdoor in the roof, bolted from above. Wind howls over it.",
              'notes': "poi:roof_trapdoor (D-42 (7)): drawn now, bolted; the D7 lane decides in phase 6."})
    E.append({'id': 'evt:lineage', 'preset': 'text', 'source': 'platform:lectern', 'title': 'The Blackfang Lineage',
              'window': True, 'text': LINEAGE, 'notes': "The library's find: the crypt's four names."})
    E.append({'id': 'evt:ledger', 'preset': 'text', 'source': 'platform:desk', 'title': 'Ledger', 'window': True,
              'text': LEDGER, 'notes': "The study's ledger (the graph's line)."})
    E.append({'id': 'evt:jewel_box', 'preset': 'script', 'source': 'platform:dressing_table', 'title': 'Jewel box',
              'condition': {'not': {'map_var': 'jewels_found'}}, 'else_effects': [{'text': "The jewel box is empty."}],
              'effects': [{'set': {'var': {'map_var': 'jewels_found'}, 'value': 1}}, {'gold': 800},
                          {'text': "The Countess's jewel box: rings and a jet brooch. No mirror anywhere. (+800 gold)"}],
              'notes': "The Countess's rooms' find, once."})
    E.append({'id': 'evt:portraits', 'preset': 'text', 'source': 'panel:portraits', 'title': 'Portraits',
              'window': False,
              'text': "Four centuries of Blackfangs. In every portrait the mirror behind the sitter shows an empty chair.",
              'notes': "The long gallery's find."})
    E.append({'id': 'evt:altar', 'preset': 'text', 'source': 'platform:altar', 'title': 'Altar', 'window': False,
              'text': "The altar cloth is embroidered with a black bat. The altar faces the wrong way.",
              'notes': "The black chapel's altar."})
    E.append({'id': 'evt:cask_find', 'preset': 'script', 'source': 'deco:cask_find', 'title': 'Cask',
              'condition': {'not': {'map_var': 'wine_found'}}, 'else_effects': [{'text': "Wine. The cask is nearly dry."}],
              'effects': [{'set': {'var': {'map_var': 'wine_found'}, 'value': 1}}, {'gold': 150},
                          {'text': "Wine. Real wine. Somebody here still drinks it. A purse is tucked behind the cask. (+150 gold)"}],
              'notes': "The cask cellar's find (the graph's line), once."})
    E.append({'id': 'evt:throne_seat', 'preset': 'text', 'source': 'platform:throne', 'title': 'Throne',
              'window': False, 'text': "A throne of black stone. The seat is cold.", 'notes': "The Count's throne."})
    E.append({'id': 'evt:crest_throne', 'preset': 'text', 'source': 'panel:crest_throne', 'title': "Blackfang's arms",
              'window': False, 'text': "A black bat with one red fang on slate grey: the arms of Blackfang.",
              'notes': "xbfcrest over the throne."})
    E.append({'id': 'evt:crest_great', 'preset': 'text', 'source': 'panel:crest_great', 'title': "Blackfang's arms",
              'window': False, 'text': "A black bat with one red fang on slate grey: the arms of Blackfang.",
              'notes': "xbfcrest on the great hall's end wall."})
    E.append({'id': 'evt:table', 'preset': 'text', 'source': 'platform:long_table', 'title': 'Long table',
              'window': False, 'text': "Goblets laid for a feast. They have never held wine.",
              'notes': "The great hall's long table."})
    # the Count, the bar, the dungeon stair
    E.append({'id': 'evt:count_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
              'condition': {'kills': {'monster': 'monster:count'}}, 'lua': COUNT_DEAD_LUA,
              'notes': "goal:count: his death runs A3's m27.blackfang (blackfang_slain 111540, once: 'every coffin lid in the castle slams shut at once ...'); the lids' sound."})
    E.append({'id': 'evt:bar_lifts', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'blackfang_slain', 'not': {'map_var': 'bar_open'}},
              'opens': ['door:bar'], 'effects': [{'set': {'var': {'map_var': 'bar_open'}, 'value': 1}}],
              'notes': "The bar lifts once blackfang_slain is set (at his death, and again after a refill)."})
    E.append({'id': 'evt:bar', 'preset': 'script', 'source': 'door:bar', 'title': 'Black iron bar', 'lua': BAR_LUA,
              'notes': "m27.dungeon_stair: until the Count is dead its fail text, the source's refusal (aaze0047:0, D-42 (6)); then a status line."})
    E.append({'id': 'evt:stair_force', 'preset': 'script', 'trigger': 'step', 'source': 'plate:stair_force',
              'condition': {'not': {'qbit': 'blackfang_slain'}}, 'lua': 'XeenQuests.hook("m27.dungeon_stair")',
              'notes': "The step before the bar (m27.dungeon_stair's where): the force like wind, until the Count is dead."})
    # the Queen
    E.append({'id': 'evt:queen_cell', 'preset': 'script', 'trigger': 'step', 'source': R('queen_cell'),
              'condition': {'not': {'qbit': 'queen_seen'}}, 'lua': 'XeenQuests.hook("m27.queen_cell")',
              'notes': "m27.queen_cell on the cell's entry (D-52, A3): its first text once (queen_seen 111544), while the Queen is there (the hook's own not-done)."})
    E.append({'id': 'evt:queen', 'preset': 'script', 'source': 'platform:queen_bench', 'title': 'Bench',
              'lua': BENCH_LUA,
              'notes': "The Queen's bench: after done 'The cell is empty. The Queen has gone home.' Queen Kalindra herself (monster:queen, npc 5001) talks when clicked: A3's The crown (queen_found, then done and m27.ambrose_return, the flight to D1)."})
    E.append({'id': 'evt:queen_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'done'},
              'effects': [{'hide_actors': QUEEN_GROUP}],
              'notes': "Queen Kalindra is home once done 111542 is set (M27): her body is hidden on every load after."})
    # the yard gate and the trapdoor
    E.append({'id': 'evt:yard_bar', 'preset': 'switch', 'source': 'switch:yard_bar', 'title': 'Bar',
              'condition': {'not': {'map_var': 'yard_gate_open'}}, 'opens': ['door:yard_gate'],
              'sets': {'map_var': 'yard_gate_open'},
              'effects': [{'text': "You lift the bar. The gate swings up onto the landing."}],
              'locked_text': "The bar is lifted; the gate stands open.",
              'notes': "poi:yard_bar: the yard gate's bar on the courtyard stair's side, lifted once."})
    E.append({'id': 'evt:yard_gate', 'preset': 'switch', 'source': 'door:yard_gate', 'title': 'Gate',
              'condition': {'not': {'map_var': 'yard_gate_open'}},
              'effects': [{'text': "The gate is barred on the courtyard side."}],
              'locked_text': "The gate stands open.",
              'notes': "The yard gate: barred from the stair's side until its bar is lifted."})
    E.append({'id': 'evt:hatch_bolt', 'preset': 'switch', 'source': 'switch:hatch_bolt', 'title': 'Bolt',
              'condition': {'not': {'map_var': 'hatch_open'}}, 'opens': ['mover:hatch'], 'sets': {'map_var': 'hatch_open'},
              'effects': [{'text': "You draw the bolt. The trapdoor at the ladder's top falls open."}],
              'locked_text': "The bolt is drawn; the trapdoor lies open.",
              'notes': "poi:hatch_bolt: the trapdoor's bolt, drawn from the shaft, once."})
    E.append({'id': 'evt:hatch', 'preset': 'switch', 'source': 'mover:hatch', 'title': 'Trapdoor',
              'condition': {'not': {'map_var': 'hatch_open'}},
              'effects': [{'text': "A trapdoor in the floor, bolted from below."}],
              'locked_text': "The trapdoor lies open over a ladder.",
              'notes': "From the cellar: 'A trapdoor in the floor, bolted from below.' until the bolt is drawn."})
    # the trapped walk
    for i, y in enumerate((-768, -256, 256, 768), 1):
        E.append({'id': f'evt:fire_{i}', 'preset': 'script', 'source': f'plate:fire_{i}', 'trigger': 'step',
                  'effects': [{'cast': {'spell': 2, 'from': [2400, y, geo.L1 + 160], 'to': [2048, y, geo.L1 + 40],
                                        'mastery': 'expert', 'level': 8}},
                              {'text': "Fire leaps from a slit in the merlons!"}],
                  'notes': "poi:fire_plates: fire from the merlons' slits (the notes on the landing: 'Floor traps are regularly spaced')."})
    E.extend(coffin_events())
    for c in ('roost', 'study', 'hoard', 'question', 'cistern'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    return E


def wiring():
    vars_ = ['bar_open', 'study_open', 'yard_gate_open', 'hatch_open', 'tower_purse', 'jewels_found', 'wine_found'] + \
        [f'coffin_{k}' for k, room, c, ax in geo.COFFINS if k in SLEEPERS or k in FINDS or k == 'se_loot']
    return {'format': 0, 'variables': vars_, 'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-14's events, written by output/studio_cal/dd14/tools/dress.py."}


ATMOSPHERE = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_darkside_fading'},
              'notes': "The courtyard and the wall walks are open to Darkside's sky (their ceilings' sky faces; DD-03's route): the fading preset of Act IV before M27 (D-42)."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
    gen.dump(folder / 'atmosphere.yml', ATMOSPHERE)
