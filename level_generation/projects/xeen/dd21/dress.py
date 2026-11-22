#!/usr/bin/env python3
"""DD-21 Necropolis Sewer, L4: objects.yml and wiring.yml (written by gen.py L4)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import geo
from pathlib import Path

import yaml

L4 = Path(_REPO_ROOT + '/devdocs/xeen/briefs/dd21/L4')


def heart_stop_lua():
    """Stops sound:heart (AmbientSound<number> from the L4's ids.lock.yml, written by the first build), or None."""
    p = L4 / 'ids.lock.yml'
    d = (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}
    n = (d.get('sounds') or {}).get('sound:heart')
    return None if n is None else f'evt.SetMapVar("AmbientSound{n}", 2)'

ROACH, LICH, MUMMY, SANDRO, RISEN = 11363, 11281, 11273, 11283, 11926
NAME = {ROACH: 'roach', LICH: 'lich', MUMMY: 'mummy'}
GROUP = {ROACH: 2, LICH: 1, MUMMY: 3}
SANDRO_GROUP, RISEN_GROUP, BARREL_GROUP = 5, 30, 20

CANDLE = [235, 175, 115]
TORCH = [240, 160, 90]
SEWERL = [150, 165, 120]
COLD = [150, 160, 180]
GREEN = [90, 235, 110]

ARRIVAL_AT = [0, 0]
RISEN_AT = [288, -3200]          # on the dais beside the bier
JAR_AT = geo.JAR_LEDGE[0]
JAR_TOP = geo.LOW + geo.JAR_LEDGE[2]
DUST_AT = (RISEN_AT[0], RISEN_AT[1], geo.CRYPT + geo.DAIS[2] + 96)


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
def doors():
    return [
        {'id': 'door:crypt', 'opening': 'open:hall_crypt', 'kind': 'hinged', 'leaves': 2,
         'surface': dict(geo.CRYPTDOOR, fit=True),
         'notes': "The crypt's double doors under Sandro's seal: two hinged leaves of 6d14's iron-bound plank door (d2lgdor, a door surface: each leaf shows it once, the right mirrored)."},
        {'id': 'door:grille', 'opening': 'open:crypt_reliquary', 'kind': 'slide_up', 'surface': dict(geo.GRILLE, fit=True),
         'notes': "The reliquary's iron grille: it lifts with Sandro's release (released 113462) and stays up."},
        {'id': 'door:vault', 'opening': 'open:west_vault', 'kind': 'slide_left', 'surface': dict(geo.VAULTDOOR, fit=True),
         'notes': "The old tomb wall's door: Mummy's Secret Treasure (aaze0036:10)."},
        {'id': 'door:cellar', 'opening': 'open:east_cellar', 'kind': 'slide_left', 'surface': dict(geo.IRONDOOR, fit=True),
         'notes': "The dead-food cellar's iron door (sewer.blv's D8dorA)."},
        {'id': 'door:sluice_room', 'opening': 'open:culvert_sluice', 'kind': 'slide_left',
         'surface': dict(geo.IRONDOOR, fit=True), 'notes': "The sluice room's iron door off the west culvert."},
        {'id': 'door:sluice_gate', 'opening': 'open:outfall_heart', 'kind': 'slide_up',
         'surface': dict(geo.GRILLE, fit=True),
         'notes': "The culvert gate: iron bars over the steps down to the heart culvert; the sluice wheel upstream lifts it, one way (D-43)."},
    ]


def switches():
    return [{'id': 'switch:wheel', 'room': R('sluice'), 'kind': 'lever', 'at': [-2240, -1920], 'reach': 48,
             'notes': "The sluice wheel's handle on the sluice room's north wall."}]


CHEST_LOOK = {'kind': '7gt002'}


def chests():
    return [dict(c, **CHEST_LOOK) for c in [
        {'id': 'chest:reliquary', 'room': R('reliquary'), 'at': [1152, -3040], 'treasure_level': 5,
         'random_items': 3, 'gold': 3000, 'notes': "Sandro's treasure 'in this room' (A3's hook), behind the grille."},
        {'id': 'chest:mummy', 'room': R('mummy_vault'), 'at': [-4224, -1408], 'facing': 'e', 'treasure_level': 5,
         'random_items': 3, 'gold': 2000, 'notes': "Mummy's Secret Treasure (aaze0036:10)."},
        {'id': 'chest:box', 'room': R('east_culvert'), 'at': [64, -2520], 'treasure_level': 5,
         'random_items': 2, 'gold': 1200, 'trap_level': 5,
         'notes': "The source's trapped Box (aaze0036:2) in the east culvert's side niche."},
    ]]


L_, M_ = LICH, MUMMY
PLACED = {
    'crypt_hall': [(LICH, [-192, -1152]), (LICH, [192, -1664])],
    'main_west': [(ROACH, [-2432, -1500]), (ROACH, [-2944, -1560]), (ROACH, [-3328, -1500])],
    'main_east': [(ROACH, [256, -1500]), (ROACH, [960, -1450])],
    'east_culvert': [(ROACH, [288, -2176]), (ROACH, [0, -2848])],
    'mummy_vault': [(MUMMY, [-4096, -1600]), (MUMMY, [-3904, -1216])],
    'heart_culvert': [(LICH, [-1152, -4064]), (ROACH, [-1536, -4032])],
}
BARREL_ROACHES = [[1792, -1280], [1792, -1536]]


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at in lst:
            n[row] = n.get(row, 0) + 1
            out.append({'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                        'facing': 90, 'group': GROUP[row]})
    for i, at in enumerate(BARREL_ROACHES, 1):
        out.append({'id': f'monster:barrel_roach_{i}', 'room': R('dead_food'), 'monster': ROACH, 'at': at,
                    'facing': 180, 'group': BARREL_GROUP, 'hidden': True,
                    'notes': "One of the two Cinder Roaches in the Dead Food barrel (D-62 Q43): placed hidden (counted at load), shown once by the first pry (dead_food_pried 117723); never shown again by a load (D-18: the map state keeps them)."})
    out.append({'id': 'monster:sandro', 'room': R('sandro_crypt'), 'monster': SANDRO, 'at': [0, -2816], 'facing': 90,
                'group': SANDRO_GROUP,
                'notes': "Sandro the Lich (11283, 65): fought once. His fall (evt:sandro_fell) sets sandro_fell 117727, calls q-d23.sandro, shows the risen Sandro and hides this body."})
    out.append({'id': 'monster:sandro_risen', 'room': R('sandro_crypt'), 'monster': RISEN, 'at': RISEN_AT,
                'floor_height': geo.CRYPT + geo.DAIS[2], 'facing': 90, 'hostile': False, 'group': RISEN_GROUP,
                'immobile': True, 'hidden': True,
                'notes': "The risen Sandro (A2's row 11926, D-62 Q41): peaceful, immobile, not counted, Sandro's look; placed hidden by the bier, shown by his fall and on every load while sandro_fell is set and released clear; takes no damage (evt:risen_figure)."})
    return out


# (key, decoration, room, at, floor height or None, title or None)
CELLAR_BARRELS = [('cellar_n1', [1856, -1088]), ('cellar_n2', [1984, -1088]), ('cellar_s1', [1856, -1728]),
                  ('cellar_s2', [1984, -1728]), ('cellar_e1', [2112, -1344])]
PRY_BARREL = ('dead_food', [2112, -1472])
CHANNEL_BARRELS = [('landing_1', [-1600, -1856]), ('landing_2', [-1504, -1856])]
PROPS = [
    ('jar', 'xeen_heartjar', 'heart_culvert', JAR_AT, JAR_TOP),   # S's jar (row 4047), session 17
    ('statuette', '7dec54', 'reliquary', geo.STATUETTE_PLINTH[0], geo.CRYPT + geo.STATUETTE_PLINTH[2]),
    ('crypt_skulls_w', 'sklplrev', 'sandro_crypt', [-704, -3392], None),
    ('crypt_skulls_e', 'sklplrev', 'sandro_crypt', [704, -3392], None),
    ('crypt_candle_w', 'dec02', 'sandro_crypt', [-544, -3104], None),
    ('crypt_candle_e', 'dec02', 'sandro_crypt', [544, -3104], None),
    ('hall_candle_1', 'cndlab0', 'crypt_hall', [416, -832], 64),
    ('hall_candle_2', 'cndlab0', 'crypt_hall', [416, -1472], 64),
    ('hall_candle_3', 'cndlab0', 'crypt_hall', [-416, -896], 64),
    ('vault_bones', 'dec29', 'mummy_vault', [-4224, -1728], None),
    ('vault_skeleton', 'dec05', 'mummy_vault', [-3776, -1728], None),
    ('cistern_bones', '7dec18', 'heart_culvert', [-1728, -3712], None),
    ('culvert_bones', 'dec29', 'west_culvert', [-2016, -2752], None),
]
# (room, wall, along, decoration)
SCONCES = [
    ('stair_foot', 'w', 0.75, 'scon100'), ('stair_foot', 'e', 0.25, 'scon100'),
    ('crypt_hall', 'n', 0.2, 'scon100'), ('crypt_hall', 'n', 0.8, 'scon100'),
    ('sandro_crypt', 'n', 0.15, 'scon100'), ('sandro_crypt', 'n', 0.85, 'scon100'),
    ('sandro_crypt', 'w', 0.5, 'scon100'),
    ('landing', 's', 0.3, 'torch02'),
    ('main_west', 's', 0.55, 'torch02'), ('main_east', 's', 0.6, 'torch02'),
    ('sluice', 'e', 0.5, 'torch02'), ('dead_food', 'n', 0.8, 'torch02'), ('outfall', 's', 0.2, 'torch02'),
    ('mummy_vault', 'n', 0.5, 'torch02'),
]


def decorations():
    out = []
    for key, at in CELLAR_BARRELS + [PRY_BARREL] + CHANNEL_BARRELS:
        room = 'landing' if key.startswith('landing') else 'dead_food'
        out.append({'id': f'deco:barrel_{key}', 'room': R(room), 'decoration': 'bigbarel', 'at': at,
                    'notes': "The Dead Food barrel (evt:dead_food)." if key == 'dead_food'
                    else "A signed barrel: 'Food for the dead, keep warm.' (evt:barrel_" + key + ")."})
    for key, dec, room, at, fh in PROPS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at}
        if fh is not None:
            d['floor_height'] = fh
        if key == 'statuette':
            d['facing'] = 180
        if key == 'jar':
            d['notes'] = "The jar of green glass with Sandro's heart (S's xeen_heartjar, MM7's vase in glowing green glass; the ledge's click: evt:jar)."
        if key == 'statuette':
            d['notes'] = "Sandro's statuette on its plinth, turned to the grille (MM7's small statue 7dec54 standing in; dressing, D-62 Q45)."
        out.append(d)
    for i, (room, wall, along, dec) in enumerate(SCONCES):
        d = {'id': f'deco:sconce_{i}', 'room': R(room), 'decoration': dec, 'wall': wall, 'along': along,
             'height': 192}
        out.append(d)
    return out


THEME_COL = {'theme:crypt': CANDLE, 'theme:channel': SEWERL, 'theme:culvert': SEWERL, 'theme:room': TORCH,
             'theme:tomb': COLD, 'theme:cistern': COLD}
OPEN_AT = {'stair_foot': ([0, 64], 320), 'landing': ([-1344, -1600], 320), 'heart_culvert': ([-1344, -4288], 320)}
DIM = {'heart_culvert': 0.6, 'reliquary': 0.7}


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
        if room in OPEN_AT:
            at, hh = OPEN_AT[room]
            add(room, at, int(1000 * DIM.get(room, 1)), col, height=hh)
            continue
        if room == 'west_culvert':
            add(room, [-2848, -2304], 800, col)
            add(room, [-2304, -2848], 800, col)
            continue
        if room == 'east_culvert':
            add(room, [288, -2304], 800, col)
            add(room, [-128, -2848], 800, col)
            continue
        r = int(min(1600, max(700, 0.6 * max(w, h))) * DIM.get(room, 1))
        if max(w, h) > 1600:
            ax = 0 if w >= h else 1
            for f in (0.25, 0.75):
                p = list(c)
                lo = c[ax] - (w if ax == 0 else h) / 2
                p[ax] = int(lo + f * (w if ax == 0 else h))
                add(room, p, int(r * 0.8), col)
        else:
            add(room, c, r, col)
    add('heart_culvert', [JAR_AT[0], JAR_AT[1]], 700, GREEN, height=geo.JAR_LEDGE[2] + 48,
        notes="The jar's green glow over the cistern.")
    add('sandro_crypt', [0, -3104], 700, [230, 140, 90], height=192, notes="The candles by the dais.")
    return L


def sounds():
    return [
        {'id': 'sound:sewer_landing', 'room': R('landing'), 'at': [-1152, -1408], 'sound': 'xeen_amb_sewer',
         'radius': 2600, 'inner_radius': 900, 'volume': 0.4, 'pan': False,
         'notes': "The sewer's bed over the landing and both arms (D-48: not panned)."},
        {'id': 'sound:sewer_outfall', 'room': R('outfall'), 'at': [-1120, -2944], 'sound': 'xeen_amb_sewer',
         'radius': 2400, 'inner_radius': 800, 'volume': 0.35, 'pan': False,
         'notes': "The bed over the outfall and the culverts (not panned)."},
        {'id': 'sound:basin', 'room': R('outfall'), 'at': [-1120, -2944], 'sound': 'water lapping loop',
         'radius': 1200, 'inner_radius': 300, 'volume': 0.35, 'notes': "The culverts pouring into the basin."},
        {'id': 'sound:cistern', 'room': R('heart_culvert'), 'at': [-1440, -4512], 'sound': 'water lapping loop',
         'radius': 1600, 'inner_radius': 400, 'volume': 0.4, 'notes': "The black cistern."},
        {'id': 'sound:crypt_drip', 'room': R('crypt_hall'), 'at': [0, -1152], 'sound': 'drip03', 'radius': 1600,
         'inner_radius': 400, 'volume': 0.3, 'wait': [4, 10], 'notes': "Drips in the Hall of Biers."},
        {'id': 'sound:heart', 'room': R('heart_culvert'), 'at': list(JAR_AT), 'height': geo.JAR_LEDGE[2] + 48,
         'sound': 'xeen_heartbeat_loop', 'radius': 900, 'inner_radius': 250, 'volume': 0.6,
         'notes': "Sandro's heart beating in the jar (AU's xeen_heartbeat_loop): off once heart_found (113461) is set (evt:jar, evt:heart_quiet)."},
    ]


def exits():
    return [
        {'id': 'exit:wing_left', 'room': R('stair_foot'), 'at': [-80, 1216], 'floor_height': geo.STAIR_TOP,
         'size': [160, 320], 'surface': geo.S_('7solid01', 128, 256, fit=True), 'to': 'exit:d6_stair',
         'notes': "The crypt door's left wing seen from inside (gkp103a, as D6's grille pair): up to the Necropolis."},
        {'id': 'exit:wing_right', 'room': R('stair_foot'), 'at': [80, 1216], 'floor_height': geo.STAIR_TOP,
         'size': [160, 320], 'surface': geo.S_('7solid01', 128, 256, fit=True), 'to': 'exit:d6_stair',
         'notes': "The crypt door's right wing seen from inside (gkp103b): the same way out."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('stair_foot'), 'at': ARRIVAL_AT, 'facing': 's',
                  'notes': "The crypt stair's foot, facing south into the Hall of Biers."},
        'arrivals': [
            {'entrance': 'entrance:d6_stair', 'room': R('stair_foot'), 'at': ARRIVAL_AT, 'facing': 's',
             'notes': "From D6's crypt door in the Necropolis (door:dd21, A6)."},
        ],
        'doors': doors(), 'switches': switches(), 'chests': chests(), 'monsters': monsters(),
        'decorations': decorations(), 'lights': lights(), 'sounds': sounds(), 'exits': exits(),
        'notes': "DD-21's contents, written by output/studio_cal/dd21/tools/dress.py: 6 doors (the crypt's double door as a hinged pair, the reliquary grille, the vault's door, two iron doors, the sluice gate), the sluice wheel, 3 chests, 16 placed monsters (10 Cinder Roaches, two of them hidden in the Dead Food barrel; 3 Greater Liches; 2 Ghost Mummies; Sandro) and, not counted, the risen Sandro (11926, hidden until his fall); two exit faces for the grille pair's wings.",
    }


# ------------------------------------------------------------------------------------------------- wiring
TALK_LUA = "\n".join([
    'if continueStep == 1 then',
    '    if not IsQBitSet(QBit(113463)) and XeenQuests.can("q-d23.ritual") then',
    '        AskChoiceWithAnswerSteps(eventId, 4, "Ask Sandro for his ritual first?", '
    '{{Answer = "Yes", Step = 3}, {Answer = "No", Step = 4}})',
    '        return',
    '    end',
    '    continueStep = 4',
    'end',
    'if continueStep == 3 then',
    '    XeenQuests.hook("q-d23.ritual")',
    '    continueStep = 4',
    'end',
    'if continueStep == 4 then',
    '    if XeenQuests.hook("q-d23.release") then',
    f'        evt.SpawnWorldEffect("mm9:smoke", {DUST_AT[0]}, {DUST_AT[1]}, {DUST_AT[2]}, 1.0)',
    f'        evt.SetMonGroupBit({RISEN_GROUP}, MonsterBits.Invisible, 1)',
    '    end',
    '    return',
    'end',
    'if continueStep ~= nil then',
    '    return',
    'end',
    'if IsQBitSet(QBit(113462)) or not IsQBitSet(QBit(117727)) then',
    '    return',
    'end',
    'XeenQuests.hook("q-d23.sandro")',
    'if HasItem(12353) then',
    '    AskChoiceWithAnswerSteps(eventId, 2, "Give Sandro his heart?", '
    '{{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})',
    'end',
])
BIER_LUA = "\n".join([
    'if continueStep == nil and IsQBitSet(QBit(113462)) then',
    '    evt.StatusText("Sandro\'s bier, empty. Grave dust lies over it.")',
    '    return',
    'end',
    'if continueStep == nil and not IsQBitSet(QBit(117727)) then',
    '    evt.StatusText("Sandro\'s bier.")',
    '    return',
    'end',
    TALK_LUA,
])

ARRIVE_TEXT = "Sandro's crypts under the Necropolis. Below them runs the sewer, where his heart is said to lie."
DRAINS = [
    # (key, panel, find qbit or None, effects of the find)
    ('drain_1', 'panel:drain_1', 'drain_1', [{'gold': 900}], "Wedged in the drain's bars, a purse. (+900 gold)"),
    ('drain_2', 'panel:drain_2', None, None, None),
    ('drain_3', 'panel:drain_3', 'drain_2', [{'give_item': {'level': 5, 'kind': 40}}],
     "Something glints in the muck behind the bars: a ring."),
    ('drain_4', 'panel:drain_4', None, None, None),
    ('drain_5', 'panel:drain_5', 'drain_3', [{'gold': 1200}], "Caught in the drain's bars, a dead man's purse. (+1200 gold)"),
    ('drain_6', 'panel:drain_6', None, None, None),
]


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'dd21_arrived_once'}},
              'effects': [{'qbit': 'dd21_arrived_once'}, {'text': ARRIVE_TEXT}],
              'notes': "The first arrival (dd21_arrived_once 117720): a status line naming the errand (map-local, for A3); the stair's foot is quiet (D-11.3)."})
    for side in ('left', 'right'):
        E.append({'id': f'evt:exit_{side}', 'preset': 'exit', 'source': f'exit:wing_{side}',
                  'title': 'Climb up to the Necropolis',
                  'notes': "The grille pair at the stair's top: the game's leave window (D-24), to D6's entrance:dd21_stair (17408, -11776, 1664) facing 512. A3's q-d23.stair_exit: 'Climb up to the Necropolis?' is its meaning."})
    E.append({'id': 'evt:door_crypt', 'preset': 'door', 'source': 'door:crypt', 'title': 'Double doors'})
    E.append({'id': 'evt:door_vault', 'preset': 'door', 'source': 'door:vault', 'title': "Mummy's Secret Treasure",
              'notes': "The old tomb wall's stone door (aaze0036:10)."})
    E.append({'id': 'evt:door_cellar', 'preset': 'door', 'source': 'door:cellar', 'title': 'Door'})
    E.append({'id': 'evt:door_sluice_room', 'preset': 'door', 'source': 'door:sluice_room', 'title': 'Door'})
    # Sandro
    E.append({'id': 'evt:first_entry', 'preset': 'script', 'trigger': 'step', 'source': R('sandro_crypt'),
              'condition': {'not': {'qbit': 'sandro_met'}},
              'effects': [{'lua': 'XeenQuests.hook("q-d23.first_entry")'}],
              'notes': "The first step into the crypt (A3's q-d23.first_entry, once, sandro_met 117722): 'Sandro the Lich rises from his bier. \"And now my hunger for the living compels me to attack you.\"' (aaze0035:25, :26)."})
    E.append({'id': 'evt:sandro_fell', 'preset': 'script', 'trigger': 'timer', 'every': 1,
              'condition': {'kills': {'monster': 'monster:sandro'}, 'not': {'qbit': 'sandro_fell'}},
              'effects': [{'qbit': 'sandro_fell'}, {'lua': 'XeenQuests.hook("q-d23.sandro")'},
                          {'show_actors': RISEN_GROUP}, {'hide_actors': SANDRO_GROUP},
                          {'lua': 'evt.SetMm9ActorCanReceiveDamage(ActorIndex("monster:sandro_risen"), false)'}],
              'notes': "goal:sandro (D-62 Q41): his fall sets sandro_fell 117727, calls q-d23.sandro (its first text and beaten, or its heart text when the party already has the heart), shows the risen Sandro by the bier and hides the fallen body."})
    E.append({'id': 'evt:risen_show', 'preset': 'script', 'trigger': 'load',
              'condition': {'qbit': 'sandro_fell', 'not': {'qbit': 'released'}},
              'effects': [{'show_actors': RISEN_GROUP}, {'hide_actors': SANDRO_GROUP}],
              'notes': "Every load: the risen Sandro stands by his bier while sandro_fell is set and released clear; the fallen (or refilled) hostile body stays hidden."})
    E.append({'id': 'evt:risen_gone', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'released'},
              'effects': [{'hide_actors': RISEN_GROUP}, {'hide_actors': SANDRO_GROUP}],
              'notes': "Every load after the release: Sandro is gone, both bodies hidden."})
    E.append({'id': 'evt:risen_figure', 'preset': 'script', 'trigger': 'load',
              'lua': 'evt.SetMm9ActorCanReceiveDamage(ActorIndex("monster:sandro_risen"), false)',
              'notes': "The risen Sandro cannot be hurt (DD-15's Pharaoh, D-51's word), on every load."})
    E.append({'id': 'evt:dais', 'preset': 'script', 'trigger': 'step', 'source': 'platform:dais', 'lua': TALK_LUA,
              'notes': "The dais's step: from sandro_fell while released is clear, the risen Sandro speaks (q-d23.sandro: its beaten text, or its heart text); with the heart 'Give Sandro his heart?', then (when someone can learn it) 'Ask Sandro for his ritual first?' (q-d23.ritual), then q-d23.release: the grave-dust puff (mm9:smoke) and Sandro hidden; the grille opens (evt:grille_opens). No to the first prompt: he waits."})
    E.append({'id': 'evt:bier', 'preset': 'script', 'source': 'platform:bier', 'title': "Sandro's bier", 'lua': BIER_LUA,
              'notes': "The bier's click: before his fall 'Sandro's bier.'; after the release an empty bier; between, the same talk as the dais."})
    E.append({'id': 'evt:grille', 'preset': 'script', 'source': 'door:grille', 'title': 'Grille',
              'condition': {'not': {'qbit': 'released'}}, 'effects': [{'lua': 'XeenQuests.hook("q-d23.grille")'}],
              'locked_text': "The grille stands open.",
              'notes': "A3's q-d23.grille before the release: 'Don't even THINK about taking my statuette!' (aaze0035:29) and 'The grille is locked.'"})
    E.append({'id': 'evt:grille_opens', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'released', 'not': {'map_var': 'grille_open'}}, 'opens': ['door:grille'],
              'effects': [{'set': {'var': {'map_var': 'grille_open'}, 'value': 1}}],
              'notes': "goal:release: the reliquary grille lifts once released 113462 is set (at the release, and again after a refill)."})
    # the heart
    stop = heart_stop_lua()
    E.append({'id': 'evt:jar', 'preset': 'script', 'source': 'platform:jar_ledge', 'title': 'Jar of green glass',
              'effects': [{'lua': 'XeenQuests.hook("q-d23.heart")'}] +
                         ([{'lua': f'if IsQBitSet(QBit(113461)) then {stop} end'}] if stop else []),
              'notes': "goal:heart: A3's q-d23.heart (once: Sandro's Heart 12353, heart_found 113461; then 'An empty jar.'); the heartbeat stops once heart_found is set."})
    if stop:
        E.append({'id': 'evt:heart_quiet', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'heart_found'},
                  'lua': stop, 'notes': "Every load once heart_found 113461 is set: the jar's heartbeat stays off."})
    # the sluice
    E.append({'id': 'evt:wheel', 'preset': 'switch', 'source': 'switch:wheel', 'title': 'Sluice wheel',
              'condition': {'not': {'qbit': 'sluice_open'}}, 'opens': ['door:sluice_gate'],
              'effects': [{'lua': 'evt.PlaySoundName("xeen_winch")'}, {'lua': 'XeenQuests.hook("q-d23.sluice_wheel")'},
                          {'set': {'var': {'map_var': 'gate_up'}, 'value': 1}}],
              'else_effects': [{'lua': 'XeenQuests.hook("q-d23.sluice_wheel")'}],
              'notes': "key:sluice (D-62 Q44, D-43): A3's q-d23.sluice_wheel (sluice_open 117721, once) and the culvert gate lifts for good; a second turn: its else line."})
    E.append({'id': 'evt:gate', 'preset': 'script', 'source': 'door:sluice_gate', 'title': 'Culvert gate',
              'condition': {'not': {'qbit': 'sluice_open'}}, 'effects': [{'lua': 'XeenQuests.hook("q-d23.culvert_gate")'}],
              'else_effects': [{'text': "The culvert gate stands open."}],
              'notes': "The culvert gate: A3's q-d23.culvert_gate while shut (the wheel is upstream)."})
    E.append({'id': 'evt:gate_up', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'sluice_open', 'not': {'map_var': 'gate_up'}}, 'opens': ['door:sluice_gate'],
              'effects': [{'set': {'var': {'map_var': 'gate_up'}, 'value': 1}}],
              'notes': "After a refill the gate lifts again (sluice_open stays set)."})
    # the Dead Food
    E.append({'id': 'evt:dead_food', 'preset': 'script', 'source': 'deco:barrel_dead_food', 'title': 'Dead Food',
              'effects': [{'lua': 'XeenQuests.hook("q-d23.dead_food")'}],
              'notes': "A3's q-d23.dead_food (D-62 Q43): Might 30 for the clicking member, else its fail line (aaze0036:7); the first pry sets dead_food_pried 117723 (evt:barrel_roaches then shows the two hidden roaches once); each pry feeds every member present who has not eaten (+2 Endurance, player bit 11378)."})
    E.append({'id': 'evt:barrel_roaches', 'preset': 'script', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'dead_food_pried', 'not': {'map_var': 'roaches_out'}},
              'effects': [{'show_actors': BARREL_GROUP}, {'set': {'var': {'map_var': 'roaches_out'}, 'value': 1}}],
              'notes': "The two roaches come out of the Dead Food barrel once it is first pried (dead_food_pried 117723), shown once (map variable roaches_out; no load event shows them, D-18: the map state keeps them)."})
    for key, at in CELLAR_BARRELS + CHANNEL_BARRELS:
        E.append({'id': f'evt:barrel_{key}', 'preset': 'script', 'source': f'deco:barrel_{key}', 'title': 'Barrel',
                  'effects': [{'lua': 'XeenQuests.hook("q-d23.barrel_sign")'}],
                  'notes': "A3's q-d23.barrel_sign: 'A sign on the barrel says: Food for the dead, keep warm.' (aaze0036:4-5)."})
    # the drains
    for key, panel, qb, eff, text in DRAINS:
        if qb:
            E.append({'id': f'evt:{key}', 'preset': 'script', 'source': panel, 'title': 'Sewer Drain',
                      'condition': {'not': {'qbit': qb}}, 'else_effects': [{'text': 'Nothing here.'}],
                      'effects': [{'qbit': qb}] + eff + [{'text': text}],
                      'notes': f"A drain with a find once (map qbit {qb}), then 'Nothing here.' (aaze0036:3, :1)."})
        else:
            E.append({'id': f'evt:{key}', 'preset': 'text', 'source': panel, 'title': 'Sewer Drain', 'window': False,
                      'text': 'Nothing here.', 'notes': "'Sewer Drain' / 'Nothing here.' (aaze0036:3, :1)."})
    E.append({'id': 'evt:alcove', 'preset': 'text', 'source': 'panel:alcove', 'title': 'Alcove', 'window': False,
              'text': 'Nothing here.', 'notes': "The source's alcove (aaze0036:0)."})
    E.append({'id': 'evt:seal', 'preset': 'text', 'source': 'panel:seal', 'title': "Sandro's seal", 'window': False,
              'text': "A heart pierced by a bone, carved in the dark stone over the doors.",
              'notes': "xdsandro over the crypt's doors."})
    for c in ('reliquary', 'mummy'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    E.append({'id': 'evt:chest_box', 'preset': 'chest', 'source': 'chest:box', 'title': 'Box',
              'notes': "The source's trapped Box (aaze0036:2)."})
    return E


def wiring():
    return {'format': 0, 'variables': ['grille_open', 'gate_up', 'roaches_out'], 'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-21's events, written by output/studio_cal/dd21/tools/dress.py."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
