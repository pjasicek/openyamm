#!/usr/bin/env python3
"""DD-25 Bosco's Hall, L4: objects.yml, wiring.yml (written by gen.py L4)."""
import geo

GUARD = 11054                      # A2's Bosco's Guard (faction xeen_bosco_hall, peaceful, placed only, not counted)
# MM7's Peasant Dwarf rows (engine monster_data 313-330, townsfolk by name; S binds their bodies for Xeen, D-62 Q34)
DWARF_F_A, DWARF_F_B, DWARF_M_A, DWARF_M_B = 313, 316, 322, 325
Q_ARRIVED, Q_CHALICE = 117680, 113343
HOUSE = {'alehall': 4702, 'forge': 4701, 'mailwright': 4705, 'tinker': 4706, 'kings_hall': 4704, 'guild_earth': 4703}
TITLE = {'alehall': "The Alehall", 'forge': "Bosco's Forge", 'mailwright': "The Mailwright's Burrow",
         'tinker': "The Tinker's Burrow", 'kings_hall': "The King's Hall", 'guild_earth': "The Deep Guild of Earth"}

WARM = [240, 190, 130]
TORCH = [240, 160, 90]
FIRE = [250, 140, 60]
ROCKL = [200, 170, 140]
CRYSTAL = [170, 200, 230]


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
def doors():
    wings = [[dict(geo.LEAF_L), dict(geo.LEAF_R)]]
    return [{'id': 'door:throne_leaves', 'opening': 'open:steps_throne', 'kind': 'hinged', 'leaves': 2,
             'pictures': [list(map(dict, r)) for r in wings], 'back_pictures': [list(map(dict, r)) for r in wings],
             'notes': "The throne hall's two carved leaves (hdr1dl, hdr1dr), opening apart into the hall."}]


def monsters():
    out = []
    for i, (room, at, facing) in enumerate([('gate_passage', [2176, 384], 180), ('gate_passage', [2176, -384], 180),
                                            ('throne_hall', [-2176, 416], 180), ('throne_hall', [-2176, -416], 180)]):
        out.append({'id': f'monster:guard_{i + 1}', 'room': R(room), 'monster': GUARD, 'at': at, 'facing': facing,
                    'hostile': False, 'immobile': True, 'group': 10,
                    'notes': "Bosco's Guard (A2's 11054, faction xeen_bosco_hall), at his post off the walking lines; uncounted."})
    folk = [('townsfolk_1', 'great_hall', DWARF_M_A, [-1088, 560], 270, "by the north bench"),
            ('townsfolk_2', 'great_hall', DWARF_F_A, [608, -576], 135, "by the well"),
            ('townsfolk_3', 'smiths_gallery', DWARF_M_B, [-400, 1232], 0, "at the gallery's west end by the anvil"),
            ('townsfolk_4', 'burrow_lane', DWARF_F_B, [-112, -1264], 180, "at the lane's east end")]
    for key, room, row, at, facing, where in folk:
        out.append({'id': f'monster:{key}', 'room': R(room), 'monster': row, 'at': at, 'facing': facing,
                    'hostile': False, 'immobile': True, 'group': 11,
                    'notes': f"A townsfolk dwarf (MM7 Peasant Dwarf row {row}), {where}; uncounted."})
    return out


# key: (decoration, room, at, floor height or None, extra)
DECOS = [
    ('chalice', '7dec48', 'throne_hall', [-2560, 560], geo.THRONE + 72,
     {'hidden': True, 'notes': "The Chalice of Protection on the tasting table: hidden, shown by evt:chalice while q-d17.done (113343)."}),
    ('cup_1', '7dec46', 'throne_hall', [-2752, 576], geo.THRONE + 72, {}),
    ('cup_2', 'dec39', 'throne_hall', [-2656, 544], geo.THRONE + 72, {}),
    ('cup_3', '7dec46', 'throne_hall', [-2464, 576], geo.THRONE + 72, {}),
    ('cup_4', 'dec39', 'throne_hall', [-2368, 544], geo.THRONE + 72, {}),
    ('brazier_n', 'flamb00', 'throne_hall', [-2944, 448], None, {'notes': "A brazier on the floor by the dais."}),
    ('brazier_s', 'flamb00', 'throne_hall', [-2944, -448], None, {'notes': "A brazier on the floor by the dais."}),
    ('hearth_fire', '7dec02', 'great_hall', [-256, 0], 48, {'notes': "The round hearth's fire."}),
    ('chandelier_w', 'chndlir0', 'great_hall', [-832, 0], None, {'hangs': True}),
    ('chandelier_e', 'chndlir0', 'great_hall', [320, 0], None, {'hangs': True}),
    ('forge_fire', 'ckfyr00', 'forge_bay', [640, 1696], None, {'notes': "The Forge's hearth in its bay."}),
    ('ale_barrel_1', 'bigbarel', 'gate_hall', [1504, -448], None, {'notes': "Ale barrels beside the Alehall's front, never before its door."}),
    ('ale_barrel_2', 'bigbarel', 'gate_hall', [1600, -448], None, {}),
    ('guild_lamp_1', 'dec02', 'guild_hall', [-3648, -1696], None, {'notes': "A guild lamp standing on the floor."}),
    ('guild_lamp_2', 'dec02', 'guild_hall', [-3648, -864], None, {}),
    ('vein_1', 'crclstr', 'guild_hall', [-3200, -848], None, {'notes': "The crystal vein by the north wall."}),
    ('vein_2', 'crys5', 'guild_hall', [-3008, -840], None, {}),
    ('vein_3', 'crys6', 'guild_hall', [-3392, -840], None, {}),
]
# (room, wall, along)
SCONCES = [('gate_passage', 'n', 0.5), ('gate_passage', 's', 0.5),
           ('gate_hall', 'e', 0.75), ('gate_hall', 'n', 0.85),
           ('great_hall', 'n', 0.75), ('great_hall', 's', 0.1), ('great_hall', 'e', 0.15), ('great_hall', 'w', 0.15),
           ('smiths_gallery', 's', 0.6), ('smiths_gallery', 'n', 0.948),
           ('burrow_lane', 'n', 0.85),
           ('throne_hall', 'n', 0.1), ('throne_hall', 's', 0.9),
           ('guild_hall', 'e', 0.15)]


def decorations():
    out = []
    for key, dec, room, at, fh, extra in DECOS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at}
        if fh is not None:
            d['floor_height'] = fh
        d.update(extra)
        out.append(d)
    for i, (room, wall, along) in enumerate(SCONCES):
        out.append({'id': f'deco:sconce_{i + 1}', 'room': R(room), 'decoration': 'scon100', 'wall': wall,
                    'along': along, 'height': 224})
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
    col = {'theme:hall': WARM, 'theme:throne': WARM, 'theme:rock': ROCKL}
    for room in geo.ORDER:
        (w, h), c = geo.extent(room)
        theme = geo.R[room][4] if room in geo.R else geo.P[room][5]
        if room == 'forge_bay':
            continue
        if room in geo.P:
            add(room, c, 1000, col[theme], height=192)
            continue
        r = int(min(1800, max(800, 0.6 * max(w, h))))
        if max(w, h) > 1900:
            ax = 0 if w >= h else 1
            for f in (0.25, 0.75):
                p = list(c)
                lo = c[ax] - (w if ax == 0 else h) / 2
                p[ax] = int(lo + f * (w if ax == 0 else h))
                add(room, p, int(r * 0.8), col[theme], height=320)
        else:
            add(room, c, r, col[theme], height=min(320, (geo.R[room][3] - geo.R[room][2]) * 3 // 4))
    for room, wall, along in SCONCES:
        x0, y0, x1, y1 = geo.R[room][1]
        a, b, n = {'s': ((x0, y0), (x1, y0), (0, 1)), 'e': ((x1, y0), (x1, y1), (-1, 0)),
                   'n': ((x1, y1), (x0, y1), (0, -1)), 'w': ((x0, y1), (x0, y0), (1, 0))}[wall]
        at = [round(a[0] + along * (b[0] - a[0]) + 48 * n[0]), round(a[1] + along * (b[1] - a[1]) + 48 * n[1])]
        add(room, at, 450, TORCH, height=240, notes="The sconce's flame.")
    add('great_hall', [-256, 0], 900, FIRE, height=160, notes="The hearth's glow.",
        pulse={'intensity': [0.75, 1.0], 'radius': [840, 940], 'frequency': 0.8})
    add('forge_bay', [640, 1680], 700, FIRE, height=128, notes="The forge's glow inside its bay.",
        pulse={'intensity': [0.7, 1.0], 'radius': [640, 720], 'frequency': 1.1})
    add('smiths_gallery', [640, 1280], 520, FIRE, height=96, notes="The forge's glow on the anvils at the bay's mouth (D-89).",
        pulse={'intensity': [0.7, 1.0], 'radius': [480, 540], 'frequency': 1.1})
    add('throne_hall', [-2944, 0], 900, TORCH, height=128, notes="The braziers' glow by the dais.",
        pulse={'intensity': [0.8, 1.0], 'radius': [860, 920], 'frequency': 0.6})
    add('guild_hall', [-3200, -896], 500, CRYSTAL, height=96, notes="The crystal vein's cold light.")
    return L


def sounds():
    return [
        {'id': 'sound:bed_hall', 'room': R('great_hall'), 'at': [-256, 0], 'sound': 'xeen_amb_mine', 'radius': 3600,
         'inner_radius': 1800, 'volume': 0.25, 'pan': False,
         'notes': "The hall's bed: stone, distant knocks and drips (xeen_amb_mine, quiet), centred (D-48)."},
        {'id': 'sound:bed_throne', 'room': R('throne_hall'), 'at': [-2816, 0], 'sound': 'xeen_amb_mine', 'radius': 1800,
         'inner_radius': 900, 'volume': 0.2, 'pan': False, 'notes': "The bed in the throne hall (quiet)."},
        {'id': 'sound:bed_guild', 'room': R('guild_hall'), 'at': [-3200, -1280], 'sound': 'xeen_amb_mine',
         'radius': 1600, 'inner_radius': 800, 'volume': 0.3, 'pan': False, 'notes': "The Deep Guild's bed."},
        {'id': 'sound:anvil', 'room': R('forge_bay'), 'at': [640, 1680], 'sound': 'xeen_forge_hall_loop',
         'radius': 2400, 'inner_radius': 500, 'volume': 0.35,
         'notes': "The forge bay's smiths at their anvils (AU's xeen_forge_hall_loop)."},
        {'id': 'sound:forge_fire', 'room': R('forge_bay'), 'at': [640, 1696], 'sound': 'campfire', 'radius': 900,
         'inner_radius': 200, 'volume': 0.4, 'notes': "The forge's fire."},
        {'id': 'sound:hearth', 'room': R('great_hall'), 'at': [-256, 0], 'sound': 'campfire', 'radius': 1000,
         'inner_radius': 300, 'volume': 0.35, 'notes': "The great hall's hearth."},
        {'id': 'sound:alehall', 'room': R('gate_hall'), 'at': [1184, -448], 'sound': 'xeen_amb_tavern', 'radius': 900,
         'inner_radius': 250, 'volume': 0.3, 'notes': "The Alehall's murmur at its door."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('gate_passage'), 'at': [2048, 0], 'facing': 'w',
                  'notes': "entrance:d5_bosco: in the gate passage 256 inside the gate's leaves, facing west into the hall (D5's door:dd25 arrives here)."},
        'doors': doors(), 'monsters': monsters(), 'decorations': decorations(), 'lights': lights(), 'sounds': sounds(),
        'exits': [
            {'id': 'exit:gate_left', 'room': R('gate_passage'), 'at': [2304, 96], 'size': [192, 320],
             'surface': geo.S_('7solid01', 128, 256, fit=True), 'to': 'exit:d5_gate',
             'notes': "The gate's left leaf (seen from inside; t09a03a, D5's leaf picture): out to Bosco's terrace (D5)."},
            {'id': 'exit:gate_right', 'room': R('gate_passage'), 'at': [2304, -96], 'size': [192, 320],
             'surface': geo.S_('7solid01', 128, 256, fit=True), 'to': 'exit:d5_gate',
             'notes': "The gate's right leaf (t09a03b, the right-hand picture of the same pair)."},
        ],
        'notes': "DD-25's contents, written by output/studio_cal/dd25/tools/dress.py: the throne hall's hinged pair, the gate's two leaves (the exit), six house doors (rooms.yml wall panels), eight peaceful dwarves (four Bosco's Guards 11054, four MM7 Peasant Dwarves), no counted monsters, no chests.",
    }


# ------------------------------------------------------------------------------------------------- wiring
ARRIVAL = "The hall rings with hammers. A dwarf at the gate looks you over, then your boots, and waves you in."
THRONE = "The King's throne, empty. He takes his meals in his chambers, where the cups can be watched."
WELL = "Cold and clean. The King had it tasted this morning."


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'arrived_once'}},
              'effects': [{'lua': 'XeenQuests.hook("dd25.arrival")'}, {'qbit': 'arrived_once'}],
              'notes': "The first arrival only: A3's once-hook dd25.arrival (its line, sets arrived_once 117680; D-62)."})
    for key, house in HOUSE.items():
        E.append({'id': f'evt:{key}', 'preset': 'script', 'source': f'door:{key}', 'title': TITLE[key],
                  'effects': [{'lua': f'evt.EnterHouse({house})'}],
                  'notes': f"A4's house {house} (source/towns/dd25.yml door:{key})."})
    E.append({'id': 'evt:throne_leaves', 'preset': 'door', 'source': 'door:throne_leaves', 'title': 'Door',
              'notes': "The throne hall's two leaves: open to all (D-62 Q38: no change after the oath)."})
    for side in ('left', 'right'):
        E.append({'id': f'evt:exit_gate_{side}', 'preset': 'exit', 'source': f'exit:gate_{side}', 'title': "Bosco's gate",
                  'notes': "The game's own leave window (D-24), to D5's entrance:dd25_door on the terrace."})
    E.append({'id': 'evt:throne', 'preset': 'script', 'source': 'platform:throne', 'title': "Bosco's throne",
              'lua': 'XeenQuests.hook("dd25.throne")',
              'notes': "D-62 Q33: the hover \"Bosco's throne\" and A3's hook dd25.throne (its line in a window)."})
    E.append({'id': 'evt:throne_back', 'preset': 'script', 'source': 'platform:throne_back', 'title': "Bosco's throne",
              'lua': 'XeenQuests.hook("dd25.throne")', 'notes': "The throne's back answers as its seat."})
    E.append({'id': 'evt:well', 'preset': 'script', 'source': 'platform:well', 'title': 'Well',
              'lua': 'XeenQuests.hook("dd25.well")',
              'notes': "D-62 Q39: a plain well, no boon; A3's hook dd25.well (its line)."})
    E.append({'id': 'evt:chalice', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'chalice_done'},
              'effects': [{'show': 'deco:chalice'}],
              'notes': "D-62 Q37: the Chalice stands on the tasting table from q-d17.done (113343), shown on every load."})
    return E


def wiring():
    return {'format': 0, 'variables': [],
            'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-25's events, written by output/studio_cal/dd25/tools/dress.py."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
