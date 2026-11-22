#!/usr/bin/env python3
"""FD-01 Alamar Depths, L4: objects.yml, wiring.yml, atmosphere.yml (written by gen.py L4)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path

import yaml

import geo

ANNIHILATOR, AUTOBOT = 11611, 11612
NAME = {ANNIHILATOR: 'annihilator', AUTOBOT: 'autobot'}
TEAL_L = [110, 200, 190]
WHITE = [200, 215, 220]
FIELD_L = [90, 150, 255]
SKY_L = [190, 195, 205]

D6 = (-6656, 4608, 2208, 1536)
D7 = (-18688, 8448, 1536, 1024)
ARRIVAL_AT = [0, 0]                      # entrance:d6_stair, facing west
ROOF_AT = [-7744, 7168]                  # entrance:d7_roof at the shaft's foot, facing east to the shaft door
ROOF_NEAR = 640                          # the D7 arrival line fires only with the party this near ROOF_AT

L4 = Path(_REPO_ROOT + '/devdocs/xeen/briefs/fd01/L4')


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
PLAIN = [
    ('gallery', 'open:gallery_door', "The gallery door, west out of the undercroft hall."),
    ('guard', 'open:guard_door', "The guard door at the south gallery's west end."),
    ('shaft', 'open:shaft_door', "The shaft door between the rubble shaft and the north gallery."),
    ('north', 'open:north_door', "The north door at the head of the long gallery."),
    ('works', 'open:works_door', "The assembly hall's works door."),
    ('warden', 'open:warden_door', "The warden's door between the key vault and the warden's room."),
]


def doors():
    out = []
    for k, op, n in PLAIN:
        out.append({'id': f'door:{k}', 'opening': op, 'kind': 'slide_up', 'surface': dict(geo.DOOR, fit=True),
                    'notes': n + " One cross-braced sw leaf (swdoorb once, whole)."})
    for k, op, side in (('slab_west', 'open:west_slab', 'west'), ('slab_east', 'open:east_slab', 'east')):
        out.append({'id': f'door:{k}', 'opening': op, 'kind': 'slide_down', 'surface': dict(geo.BLAST, fit=True),
                    'speed': 128,
                    'notes': f"The {side} slab (D-69 change 1): a shut bulkhead (swdoora once per face, whole) that drops into the floor for good when the {side} lever is pulled (out of sight of the lever hall)."})
    out.append({'id': 'door:grate', 'opening': 'open:grate', 'kind': 'slide_up', 'surface': dict(geo.GRATE, fit=True),
                'notes': "The bolted grate (D-69 change 4): a solid leaf with the lattice picture (swdoorc once per face, whole); it blocks sight and shots; opened for good from the workshop's face."})
    out.append({'id': 'door:skull', 'opening': 'open:skull_door', 'kind': 'slide_up',
                'pictures': [[dict(geo.SKULL_L), dict(geo.SKULL_R)]],
                'back_pictures': [[dict(geo.SKULL_R), dict(geo.SKULL_L)]],
                'notes': "The skull door: two skull-mask panels (swtrpnl | swtrdk, each once at its 1:2) on one leaf; m39.skull_door (the Cube) raises it for good (117845)."})
    out.append({'id': 'door:vault', 'opening': 'open:vault_pair', 'kind': 'slide_left', 'leaves': 2,
                'pictures': [[dict(geo.DOOR)]], 'back_pictures': [[dict(geo.DOOR)]],
                'notes': "The stasis vault's pair (D-69 change 3, D-67 item 3): one swdoorb picture split over two leaves that part in the middle."})
    return out


def lifts():
    return [{'id': 'lift:cage', 'room': R('liftfoot'), 'at': geo.LIFT_AT, 'size': geo.LIFT_SIZE,
             'travel': geo.LIFT_TRAVEL, 'thickness': 16, 'speed': 256, 'state': 'up', 'surface': dict(geo.GIRDER),
             'notes': "The cage: up in the lift head's floor (0) at the start, down to the lift foot (-768) and back; 3 s."}]


COFFIN_C = geo.DAIS_AT
FIELD_X, FIELD_Y, FIELD_H = 176, 160, 224
FIELD_SINK = FIELD_H + 8
DAIS_TOP = geo.LOW + geo.DAIS_RISE
LID_SLIDE = 104


def movers():
    cx, cy = COFFIN_C
    sheet = dict(geo.FIELD)
    return [
        {'id': 'mover:lid', 'room': R('stasis'), 'at': [cx, cy], 'size': geo.COFFIN_SIZE, 'bottom': 0,
         'floor_height': geo.COFFIN_TOP, 'height': 8, 'travel': [0, LID_SLIDE, 0], 'speed': 64,
         'surface': dict(geo.GIRDER), 'top_surface': dict(geo.GIRDER),
         'notes': "The coffin's steel lid: it slides back off the coffin's top when the field drops (m39.roland)."},
        {'id': 'mover:field', 'room': R('stasis'), 'at': [cx, cy + FIELD_Y - 4], 'size': [2 * FIELD_X, 8],
         'bottom': 0, 'floor_height': DAIS_TOP, 'height': FIELD_H, 'travel': [0, 0, -FIELD_SINK], 'speed': 160,
         'surface': sheet, 'top_surface': dict(sheet), 'end_surface': dict(sheet),
         'parts': [
             {'at': [cx, cy - FIELD_Y + 4], 'size': [2 * FIELD_X, 8], 'bottom': 0, 'height': FIELD_H},
             {'at': [cx - FIELD_X + 4, cy], 'size': [8, 2 * FIELD_Y - 16], 'bottom': 0, 'height': FIELD_H},
             {'at': [cx + FIELD_X - 4, cy], 'size': [8, 2 * FIELD_Y - 16], 'bottom': 0, 'height': FIELD_H},
         ],
         'notes': "The stasis field (xafield, translucent, D-51): four sheets round the coffin on the dais; it sinks into the dais when m39.roland runs and stays down with m39.done (111781)."},
    ] + lever_movers()


def lever_movers():
    """D-71 P2 (merge point 30): each lever's arm (32 square, 176 long, a teal banded pipe) standing up from its pivot
    boss with its grip (48 square, a red collared pipe, session 23) on top as a part of the same mover; the pull swings it 180 degrees about the
    pivot, away from the wall and down, in one second, so it hangs thrown with the grip at its foot (on every load
    after: evt:slab_<side>_load)."""
    out = []
    for side in ('west', 'east'):
        a, g = geo.LEVER_ARM, geo.LEVER_GRIP
        at = geo.lever_at(side, a[0], a[1])
        out.append({'id': f'mover:lever_{side}_arm', 'room': R('levers'), 'at': at,
                    'size': geo.lever_size(side, *a), 'bottom': geo.LEVER_PIVOT, 'height': a[3],
                    'turn': {'pivot': [at[0], at[1], geo.LEVER_PIVOT], 'axis': 'y',
                             'degrees': geo.LEVER_SWING[side]},
                    'speed': 180,
                    'parts': [{'at': geo.lever_at(side, g[0], g[1]), 'size': geo.lever_size(side, *g),
                               'height': g[3], 'surface': dict(geo.LEVER_GRIP_S), 'top_surface': dict(geo.LEVER_CAP)}],
                    'surface': dict(geo.LEVER_ARM_S), 'top_surface': dict(geo.LEVER_CAP),
                    'notes': f"The {side} lever (D-71 P2): the arm up from the pivot, the grip on its top (a part); "
                             "thrown, it swings out from the wall and hangs down from the pivot."})
    return out


def switches():
    return [
        {'id': 'switch:lift_head', 'room': R('skull'), 'kind': 'button', 'wall': 'e', 'along': 0.5, 'height': 112,
         'notes': "The cage's button on the lift head's east wall, beside the hole."},
        {'id': 'switch:lift_foot', 'room': R('liftfoot'), 'kind': 'button', 'wall': 'n', 'along': 0.5, 'height': 112,
         'notes': "The cage's button on the lift foot's north wall, beside the cage."},
    ]


def plates():
    return [{'id': 'plate:statue', 'room': R('stairhall'), 'at': [-1024, -256], 'size': [768, 896],
             'notes': "The floor before Alamar's statue: it speaks as the party first comes near (m39.statue)."}]


# F6 feedback fix (2026-11-21): every Xeen chest is the shipped chest (MM8's gt002 for the depths' metal halls),
# its back to the wall it stands against and its front to the room (`facing` is a chest's long axis: the front faces
# 90 degrees anticlockwise of it, s -> east, w -> south).
LOCKER = {'kind': 'gt002'}


def chests():
    return [dict(c, **LOCKER) for c in [
        {'id': 'chest:pyramid', 'room': R('pyramid'), 'at': [-6736, 320], 'facing': 's', 'treasure_level': 6,
         'random_items': 3, 'gold': 5000, 'notes': "Beside the dead pyramid, against the nook's west wall (T6)."},
        {'id': 'chest:assembly', 'room': R('assembly'), 'at': [-5216, 5072], 'facing': 'w', 'treasure_level': 6,
         'random_items': 3, 'gold': 5000, 'notes': "The foreman's locker in the north-east corner (T6)."},
        {'id': 'chest:warden', 'room': R('warden'), 'at': [-1872, 2816], 'facing': 's', 'treasure_level': 6,
         'random_items': 3, 'gold': 5000,
         'notes': "The warden's chest on the west wall (T6): m39.darkstone_key (the Darkstone key on its cushion)."},
        {'id': 'chest:stasis', 'room': R('stasis'), 'at': [96, 4720], 'facing': 'w', 'treasure_level': 6,
         'random_items': 4, 'gold': 6000, 'notes': "By the stasis vault's north wall (T6)."},
    ]]


A, AU = ANNIHILATOR, AUTOBOT
# room: [(row, at, group)]
PLACED = {
    'south': [(A, [-3008, -512], 1), (A, [-3392, -640], 1), (A, [-3392, -384], 1)],
    'west': [(A, [-7168, 384], 2), (A, [-7168, 768], 2), (A, [-7168, 1152], 2)],
    'north2': [(A, [-4224, 7168], 3), (A, [-3712, 7168], 3)],
    'column': [(A, [-2816, 5888], 4), (A, [-2816, 5504], 4)],
    'hub': [(A, [-3072, 3840], 5), (A, [-3200, 4224], 5), (AU, [-2688, 3840], 6), (AU, [-3328, 3584], 6)],
    'workshop': [(A, [-4608, 384], 7), (A, [-4224, 256], 7), (A, [-4992, 256], 7)],
    'wpass': [(A, [-5632, 2048], 8), (A, [-5632, 2432], 8)],
    'assembly': [(A, [-5952, 4160], 9), (A, [-5632, 4352], 9), (A, [-5952, 4544], 9), (AU, [-5504, 3840], 10),
                 (AU, [-6272, 3840], 10)],
    'keyvault': [(A, [-1216, 1280], 11), (A, [-1536, 1536], 11), (A, [-896, 1536], 11)],
    'warden': [(A, [-1216, 2816], 12), (A, [-1536, 3072], 12), (AU, [-1024, 3072], 12)],
    'stasis': [(A, [-320, 4352], 13), (A, [-320, 3456], 13), (A, [512, 4352], 14), (AU, [512, 3456], 14)],
}


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at, g in lst:
            n[row] = n.get(row, 0) + 1
            out.append({'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                        'facing': 180, 'group': g})
    return out


# (key, decoration, room, at, facing)
DECOS = [
    ('statue', 'xeen_statue_teal', 'stairhall', geo.STATUE_AT, 270),
    ('shaft_rock_1', '6rock01', 'shaft', [-8960, 6720], None),
    ('shaft_rock_2', '6rock03', 'shaft', [-8064, 7808], None),
]


def decorations():
    out = []
    for key, dec, room, at, facing in DECOS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at}
        if facing is not None:
            d['facing'] = facing
        if key == 'statue':
            d['notes'] = "Alamar's teal statue (S's xeen_statue_teal, row 4046, DD-17's) by the north wall, facing into the hall: hover 'Statue'."
        else:
            d['notes'] = "Rubble at the shaft's foot, by the wall."
        out.append(d)
    return out


def lights():
    L = []

    def add(room, at, radius, color, height=None, notes=None, lid=None):
        d = {'id': lid or f'light:{room}_{sum(1 for x in L if x["room"] == R(room)) + 1}', 'room': R(room),
             'at': at, 'radius': radius, 'color': color}
        if height is not None:
            d['height'] = height
        if notes:
            d['notes'] = notes
        L.append(d)
    for room in geo.ORDER:
        if room in ('stasis', 'shaft'):
            continue
        (w, h), c = geo.extent(room)
        ch = geo.R[room][3] - geo.R[room][2]
        hh = min(320, ch - 96)
        r = int(min(1400, max(600, 0.5 * max(w, h))))
        if room == 'pyramid':
            add(room, [-6464, 128], 560, TEAL_L, height=hh,
                notes="The nook's light by its mouth, not over the dead pyramid (D-71's tone: its light is out).")
            continue
        if room == 'hub':
            for p in ([-3072, 3456], [-3072, 4224]):
                add(room, p, 1000, TEAL_L, height=hh)
            continue
        if max(w, h) > 2400:
            ax = 0 if w >= h else 1
            n = 3 if max(w, h) > 3200 else 2
            for k in range(n):
                f = (k + 0.5) / n
                p = list(c)
                lo = c[ax] - (w if ax == 0 else h) / 2
                p[ax] = int(lo + f * (w if ax == 0 else h))
                add(room, p, int(r * 0.85), TEAL_L, height=hh)
        else:
            add(room, c, r, TEAL_L, height=hh)
    # the stasis vault: the field's blue over the dais, the machine ring's teal round the walls
    cx, cy = geo.STASIS_C
    add('stasis', [cx, cy], 900, FIELD_L, height=420, lid='light:field',
        notes="The stasis field's blue glow over the dais: it goes out when the field drops.")
    for dx, dy in ((-560, 0), (560, 0), (0, -560), (0, 560)):
        add('stasis', [cx + dx, cy + dy], 700, TEAL_L, height=400, notes="The machine ring's glow.")
    sx, sy = geo.SHAFT_C
    add('shaft', [sx, sy], 1300, SKY_L, height=1400, notes="Grey daylight down the shaft from the open roof.")
    add('shaft', [sx, sy], 700, TEAL_L, height=240)
    return L


def sounds():
    cx, cy = geo.STASIS_C
    return [
        {'id': 'sound:bed_hub', 'room': R('hub'), 'at': [-3072, 3840], 'sound': 'xeen_machine_stamp_loop',
         'radius': 4200, 'inner_radius': 1600, 'volume': 0.14, 'pan': False,
         'notes': "DD-17's machine bed, fainter (D-48: not panned): the Hall of Nine, the galleries' east half, the lever hall."},
        {'id': 'sound:bed_workshop', 'room': R('workshop'), 'at': [-4288, 384], 'sound': 'xeen_machine_stamp_loop',
         'radius': 4200, 'inner_radius': 1600, 'volume': 0.14, 'pan': False,
         'notes': "The bed over the workshop, the south gallery and the west maze."},
        {'id': 'sound:hum_east', 'room': R('warden'), 'at': [-1216, 2304], 'sound': 'humming', 'radius': 2600,
         'inner_radius': 900, 'volume': 0.16, 'pan': False, 'notes': "The east wing's hum (the warden's consoles)."},
        {'id': 'sound:coffin_hum', 'room': R('stasis'), 'at': [cx, cy], 'sound': 'xeen_stasis_hum', 'radius': 1100,
         'inner_radius': 300, 'volume': 0.4,
         'notes': "The stasis coffin's cold glassy hum (AU's xeen_stasis_hum): it stops when the field drops (AmbientSound map variable)."},
        {'id': 'sound:shaft_wind', 'room': R('shaft'), 'at': list(geo.SHAFT_C), 'sound': 'whistling wind',
         'radius': 1400, 'inner_radius': 500, 'volume': 0.3,
         'notes': "Wind down the rubble shaft (the shipped loop)."},
        {'id': 'sound:shaft_grit', 'room': R('shaft'), 'at': list(geo.SHAFT_C), 'sound': 'xeen_shaft_grit',
         'radius': 1200, 'inner_radius': 300, 'volume': 0.45, 'notes': "Sand and pebbles trickling down the shaft (AU)."},
        {'id': 'sound:metal_groan', 'room': R('hub'), 'at': [-3072, 3840], 'sound': 'xeen_metal_groan', 'radius': 4200,
         'inner_radius': 1600, 'volume': 0.35, 'wait': [25, 60],
         'notes': "The buried ship's metal settling now and then over the Hall of Nine (AU)."},
    ]


def exits():
    return [{'id': 'exit:hatch', 'room': R('stair'), 'at': [1472, 0], 'floor_height': geo.STAIR_TOP,
             'size': [256, 256], 'surface': geo.S_('7solid01', 256, 256, fit=True), 'to': 'exit:d6_stair',
             'notes': "The gatehouse hatch's underside at the stair's head: up to D6 (entrance:fd01_stair)."}]


def objects():
    return {
        'format': 0,
        'start': {'room': R('stair'), 'at': ARRIVAL_AT, 'facing': 'w',
                  'notes': "The ruin stair's foot, facing west into the undercroft hall."},
        'arrivals': [
            {'entrance': 'entrance:d6_stair', 'room': R('stair'), 'at': ARRIVAL_AT, 'facing': 'w',
             'notes': "From D6's thing:fd01_stair (A6; m39.depths_door, the Cube)."},
            {'entrance': 'entrance:d7_roof', 'room': R('shaft'), 'at': ROOF_AT, 'facing': 'e',
             'notes': "From D7's roof hatch (A6; q-d26.hatch after m33.done): the shaft's foot, facing east to the shaft door."},
        ],
        'doors': doors(), 'lifts': lifts(), 'movers': movers(), 'switches': switches(), 'plates': plates(),
        'chests': chests(), 'monsters': monsters(), 'decorations': decorations(), 'lights': lights(),
        'sounds': sounds(), 'exits': exits(),
        'notes': "FD-01's contents, written by output/studio_cal/fd01/tools/dress.py: 11 doors (six plain swdoorb leaves, the two lever slabs, the bolted grate, the skull door, the vault pair), the lift, the coffin's lid and the stasis field (movers), 4 chests (T6 lockers), 34 placed robots (Annihilator 11611 x28, Autobot 11612 x6, one faction), Alamar's statue.",
    }


# ------------------------------------------------------------------------------------------------- wiring


def lua_str(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


def stop_sound_lua(sid):
    n = lock_number('sounds', sid)
    return None if n is None else f'evt.SetMapVar("AmbientSound{n}", 2)'


GRIND = 'evt.PlaySoundName("6stone door0101")'
FEWAEE = ("The message on the plaque reads: FEWAEEFFWAEFAWEEWWEFAW\n"
          "Remember: A = Air, E = Earth, F = Fire, W = Water.")
KEY_FOUND = "Inside the box, alone on its rack: a black key with a dragon's eye for a bow. The Key to the Dragon Tower."


def arrival_lua():
    ax, ay = ROOF_AT
    return "\n".join([
        'local x, y, z = evt.GetPartyPosition()',
        f'local dx, dy = x - ({ax}), y - ({ay})',
        f'if dx * dx + dy * dy < {ROOF_NEAR * ROOF_NEAR} then',
        '    XeenQuests.hook("m39.shaft_arrival")',
        'end',
    ])


def coffin_event(eid, source):
    fx = [hook('m39.roland'), {'lua': 'evt.PlaySoundName("xeen_coffin_lid")'}, {'lights_off': 'light:field'}]
    s = stop_sound_lua('sound:coffin_hum')
    if s:
        fx.append({'lua': s})
    return {'id': eid, 'preset': 'switch', 'source': source, 'title': 'Coffin',
            'condition': {'not': {'qbit': 'm39_done'}}, 'opens': ['mover:field', 'mover:lid'], 'effects': fx,
            'else_effects': [hook('m39.roland')],
            'notes': "D-69 change 2: the coffin, its lid and the field all carry the click and 'Coffin' (aaze0052:7); m39.roland (done 111781, the amulet 12372, the award, 40,000) drops the field and slides the lid back; after it the hook's else line ('An empty stasis coffin, still faintly cold.')."}


def events():
    E = []
    # arrivals: a real entry arms the D7 line once (DD-17's in_visit pattern) and the party's place decides
    E.append({'id': 'evt:visit_load', 'preset': 'script', 'trigger': 'load',
              'condition': {'not': {'map_var': 'in_visit'}},
              'effects': [{'set': {'var': {'map_var': 'in_visit'}, 'value': 1}},
                          {'set': {'var': {'map_var': 'visit'}, 'value': 1}}],
              'notes': "A real entry (in_visit clear, as leaving left it) arms evt:arrival once; a game saved inside and loaded finds in_visit set and arms nothing."})
    E.append({'id': 'evt:visit_end', 'preset': 'script', 'trigger': 'leave',
              'effects': [{'set': {'var': {'map_var': 'in_visit'}, 'value': 0}}],
              'notes': "Leaving by any way ends the visit."})
    E.append({'id': 'evt:arrival', 'preset': 'script', 'trigger': 'timer', 'every': 1,
              'condition': {'map_var': 'visit'},
              'effects': [{'set': {'var': {'map_var': 'visit'}, 'value': 0}}],
              'lua': arrival_lua(),
              'notes': f"D-69 change 5: on a real entry at the shaft's foot (within {ROOF_NEAR} of entrance:d7_roof) A3's m39.shaft_arrival (once per game, 117846, its status line, no line before it); a D6 arrival (the stair's foot) says nothing here (the statue speaks)."})
    # the exit to D6
    E.append({'id': 'evt:exit_hatch', 'preset': 'exit', 'source': 'exit:hatch', 'title': 'Exit Alamar Depths',
              'notes': "The gatehouse hatch at the stair's head (D-24): the leave window, out to D6's entrance:fd01_stair (-6656, 4608, 2208) facing 1536."})
    # the way up to D7
    ladder_sources = (['panel:ladder', 'platform:ladder_rail_s', 'platform:ladder_rail_n']
                      + [f'platform:ladder_rung_{k + 1:02d}' for k in range(len(geo.LADDER_RUNGS))])
    for src in ladder_sources:
        name = 'ladder' if src == 'panel:ladder' else src.split(':')[1]
        E.append({'id': f'evt:{name}', 'preset': 'script', 'source': src, 'title': 'Ladder',
                  'condition': {'lua': 'XeenQuests.hook("q-d26.depths_hatch")'},
                  'effects': [{'exit': 'exit:d7_roof'}],
                  'notes': ("D-69 change 5; F16 (2026-11-22): q-d26.depths_hatch first ('Bolted from above.' until roof_unlocked 113521), then the standard entrance window (OK/Close, no Yes/No); OK moves to D7's entrance:fd01_roof (-18688, 8448, 1536) facing 1024, Close stays."
                            if name == 'ladder' else "The same as evt:ladder, clicked on the ladder's rails and rungs (D-71 P1).")})
    # the statue
    E.append({'id': 'evt:statue_near', 'preset': 'script', 'trigger': 'step', 'source': 'plate:statue',
              'condition': {'not': {'qbit': 'statue_spoken'}}, 'effects': [hook('m39.statue')],
              'notes': "D-69 change 8: the boast as the party first comes near (m39.statue, aaze0052:13), once per game (the hook sets 117840; the map's condition guards it too)."})
    E.append({'id': 'evt:statue', 'preset': 'script', 'source': 'deco:statue', 'title': 'Statue',
              'effects': [hook('m39.statue')],
              'notes': "The statue's click calls the same hook: the boast if the plate has not run yet; after it the hook's else line on the status bar, 'The statue says nothing more. Alamar has had his say.' (A3's else_text, D-71 item 5)."})
    # the plaques
    E.append({'id': 'evt:plaque_nine', 'preset': 'script', 'source': 'panel:plaque_nine', 'title': 'Plaque',
              'effects': [hook('m39.plaque_nine')], 'notes': "'Nine is the time.' (aaze0052:12)."})
    E.append({'id': 'evt:plaque_fewaee', 'preset': 'text', 'source': 'panel:plaque_fewaee', 'title': 'Plaque',
              'window': True, 'text': FEWAEE, 'notes': "aaze0052:14 (map-local; lore, the order of DD-17's belts)."})
    # the levers and their slabs
    for side in ('west', 'east'):
        thrown = [f'door:slab_{side}', f'mover:lever_{side}_arm']
        for part in ('arm', 'boss'):
            src = f'platform:lever_{side}_boss' if part == 'boss' else f'mover:lever_{side}_{part}'
            E.append({'id': f'evt:lever_{side}' + ('' if part == 'arm' else f'_{part}'), 'preset': 'switch',
                      'source': src, 'title': 'Lever',
                      'condition': {'not': {'qbit': f'slab_{side}'}}, 'opens': list(thrown),
                      'effects': [hook(f'm39.lever_{side}'), {'lua': GRIND}],
                      'else_effects': [hook(f'm39.lever_{side}')],
                      'notes': (f"D-69 change 1: the first pull grinds (the source's FX 35: the shipped stone grind), throws the lever down (D-71 P2) and calls m39.lever_{side} (the status line naming the direction, 117{841 if side == 'west' else 842}); the slab drops for good; after it the hook's 'The lever won't budge.' (:17)."
                                if part == 'arm' else f"The same as evt:lever_{side}, clicked on the lever's {part}.")})
        E.append({'id': f'evt:slab_{side}_load', 'preset': 'switch', 'trigger': 'load',
                  'condition': {'qbit': f'slab_{side}'}, 'opens': list(thrown),
                  'notes': f"Every load after the {side} lever: its slab stays down and the lever stays thrown."})
        E.append({'id': f'evt:slab_{side}', 'preset': 'text', 'source': f'door:slab_{side}', 'title': 'Bulkhead',
                  'text': "A shut bulkhead. Nothing on this side moves it.",
                  'notes': "The slab before its lever is pulled (map-local line)."})
    # the bolted grate, one way by side
    E.append({'id': 'evt:grate_bolt', 'preset': 'switch', 'source': 'door:grate', 'side': R('workshop'),
              'title': 'Grate', 'condition': {'not': {'qbit': 'grate_bolt'}}, 'opens': ['door:grate'],
              'effects': [hook('m39.grate_bolt')], 'locked_text': "The grate stands open.",
              'notes': "D-69 change 4: the workshop's face: m39.grate_bolt ('You draw the bolt.', 117843) and the leaf rises for good."})
    E.append({'id': 'evt:grate_bolted', 'preset': 'script', 'source': 'door:grate', 'side': R('south'),
              'title': 'Grate', 'condition': {'not': {'qbit': 'grate_bolt'}}, 'effects': [hook('m39.grate_bolted')],
              'locked_text': "The grate stands open.",
              'notes': "The south gallery's face while the bolt is in: m39.grate_bolted ('Bolted from the other side.'); the leaf stays shut."})
    E.append({'id': 'evt:grate_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'grate_bolt'},
              'opens': ['door:grate'], 'notes': "The grate stays open on every load after the bolt."})
    # plain doors
    for k, op, n in PLAIN:
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}', 'title': 'Door'})
    E.append({'id': 'evt:door_vault', 'preset': 'door', 'source': 'door:vault', 'title': 'Stasis vault'})
    # the skull door
    E.append({'id': 'evt:skull_door', 'preset': 'switch', 'source': 'door:skull', 'title': 'Skull door',
              'condition': {'lua': 'XeenQuests.can("m39.skull_door")'}, 'opens': ['door:skull'],
              'sets': {'qbit': 'skull_door_open'}, 'effects': [hook('m39.skull_door')],
              'else_effects': [hook('m39.skull_door')],
              'notes': "m39.skull_door: with the Cube 'Access granted.', the door rises for good (117845); without it the source's 'Access denied! You do not have the proper I.D.' (aaze0052:3) and it stays shut."})
    E.append({'id': 'evt:skull_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'skull_door_open'},
              'opens': ['door:skull'], 'notes': "The skull door stays open on every load after the Cube."})
    # the lift
    for sw, z in (('lift_head', 0), ('lift_foot', geo.LOW)):
        E.append({'id': f'evt:{sw}', 'preset': 'switch', 'source': f'switch:{sw}', 'title': 'Lift',
                  'toggles': ['lift:cage'],
                  'effects': [{'lua': f'evt.PlaySoundName("xeen_lift", {geo.LIFT_AT[0]}, {geo.LIFT_AT[1]}, {z})'}],
                  'notes': "The cage between the lift head (0) and the lift foot (-768)."})
    # the key box
    E.append({'id': 'evt:keybox', 'preset': 'script', 'source': 'platform:keybox', 'title': 'Box',
              'condition': {'not': {'qbit': 'key_box'}},
              'effects': [{'give_item': 12376}, {'qbit': 'key_box'}, {'message': KEY_FOUND}],
              'else_effects': [{'text': 'Nothing here.'}],
              'notes': "The key vault's box (aaze0052:2): the Key to the Dragon Tower 12376 once (key_box 117844; q-f1.tower_key's map_gives, D-57 Q23), then 'Nothing here.' (:16)."})
    # the pyramid
    E.append({'id': 'evt:pyramid', 'preset': 'script', 'source': 'platform:pyramid', 'title': 'Pyramid',
              'effects': [hook('m39.pyramid')],
              'notes': "Q70 (a): 'Its light is out. Its twin stands outside the gate.' (m39.pyramid)."})
    # the coffin
    E.append(coffin_event('evt:coffin', 'platform:coffin'))
    E.append(coffin_event('evt:field', 'mover:field'))
    E.append(coffin_event('evt:lid', 'mover:lid'))
    lf = [{'lights_off': 'light:field'}]
    s = stop_sound_lua('sound:coffin_hum')
    if s:
        lf.append({'lua': s})
    E.append({'id': 'evt:coffin_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'm39_done'},
              'opens': ['mover:field', 'mover:lid'], 'effects': lf,
              'notes': "Every load with m39.done (111781): the field down, the lid open, the hum and the glow off."})
    # the chests
    E.append({'id': 'evt:chest_warden', 'preset': 'chest', 'source': 'chest:warden', 'title': 'Chest',
              'effects': [hook('m39.darkstone_key')],
              'notes': "The warden's chest (T6): m39.darkstone_key (111780, the key on its cushion; then 'An empty velvet cushion.')."})
    for c in ('pyramid', 'assembly', 'stasis'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    return E


def wiring():
    return {'format': 0, 'variables': ['in_visit', 'visit'], 'events': sorted(events(), key=lambda e: e['id']),
            'notes': "FD-01's events, written by output/studio_cal/fd01/tools/dress.py."}


ATMOSPHERE = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_darkside_day'},
              'notes': "The rubble shaft opens to the sky far above (D7's roof): the day preset (the sun is back after M33; never the alias xeendark1)."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
    gen.dump(folder / 'atmosphere.yml', ATMOSPHERE)
