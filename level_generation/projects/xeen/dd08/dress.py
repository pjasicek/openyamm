#!/usr/bin/env python3
"""DD-08 Northern Tower, L4: objects.yml and wiring.yml (written by gen.py L4)."""
import geo

SLAYER, DEATH, FIGURE = 11150, 11151, 11925
NAME = {SLAYER: 'slayer', DEATH: 'death'}
KNIGHT_GROUP = 1
FIGURE_GROUP = 40          # the four oath figures (hidden until the oath, D-61 Q28)

ARRIVAL_AT = [0, -1152]                     # entrance:d5_tower (the brief's point), facing north
D7_ROOF = (5632, 15104, 1158, 512)          # D7's entrance:dd08_roof (assets_dev/worlds/xeen/maps/xeen_d7.studio.yml)

STONEL = [200, 215, 200]
WARM = [255, 200, 140]
CANDLE = [255, 220, 170]


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
SINGLE = [
    # key, opening, title, notes
    ('lectern', 'open:wgal_lect', 'Door', "The west lectern room's door."),
    ('refectory', 'open:refec_hall', 'Door', "The refectory's door from the Hall of Arms."),
    ('helms', 'open:core_helms', 'Door', "The west armoury's door off the great stair's head."),
    ('mail', 'open:core_mail', 'Door', "The east armoury's door off the great stair's head."),
    ('quartermaster', 'open:mail_qm', 'Door', "The quartermaster's store."),
    ('west_study', 'open:wstair_study', 'Door', "The west study off the west wall stair's head."),
    ('east_study', 'open:estair_study', 'Door', "The east study off the east wall stair's head."),
    ('west_dorm', 'open:chapter_wdorm', 'Door', "The west cells off the chapter hall."),
    ('east_dorm', 'open:thrones_edorm', 'Door', "The east cells off the Hall of Thrones."),
]


def pics(left, right):
    return [[dict(left), dict(right)]]


def doors():
    out = [{'id': 'door:gate', 'opening': 'open:gate', 'kind': 'hinged', 'leaves': 2,
            'pictures': pics(geo.S_('7solid01', 128, 256), geo.S_('7solid01', 128, 256)), 'back_pictures': pics(geo.GATEL, geo.GATER),
            'notes': "The tower's gate (D-49: the Northern Tower's pair hkm1dl|hkm1dr, mirrored inside): clicked, the exit preset ('Exit the Knight's Tower?', aaze0069:0). It stays shut."},
           {'id': 'door:chapter', 'opening': 'open:chapter', 'kind': 'hinged', 'leaves': 2,
            'pictures': pics(geo.CDOORL, geo.CDOORR), 'back_pictures': pics(geo.CDOORL, geo.CDOORR),
            'notes': "The chapter hall's doors: two hinged leaves of 7d33's arched door (chb1dl|chb1dr)."}]
    for k, op, t, n in SINGLE:
        out.append({'id': f'door:{k}', 'opening': op, 'kind': 'slide_left', 'surface': dict(geo.GDOOR, fit=True), 'notes': n})
    out.append({'id': 'door:iron', 'opening': 'open:iron', 'kind': 'slide_up', 'surface': dict(geo.GDOOR, fit=True),
                'notes': "The iron door to the chalice room: opened by the voice's answer (q-d17.voice, 113342) and open on every later load."})
    for side, k in (('w', 'wall_w'), ('e', 'wall_e')):
        out.append({'id': f'door:{k}', 'opening': f'open:{"w" if side == "w" else "e"}study_niche', 'kind': 'slide_left',
                    'secret': True, 'surface': dict(geo.STONE), 'back_surface': dict(geo.STONE),
                    'notes': f"The {'west' if side == 'w' else 'east'} study's sliding wall: the step plate before it opens it with a grind, for good ({117652 if side == 'w' else 117653})."})
    return out


def plates():
    return [
        {'id': 'plate:wall_w', 'room': R('west_study'), 'at': [-2048, 1728], 'size': [192, 192],
         'notes': "Before the west wall (the source's (3, 8)): the wall slides open."},
        {'id': 'plate:wall_e', 'room': R('east_study'), 'at': [2048, 1728], 'size': [192, 192],
         'notes': "Before the east wall (the source's (11, 8)): the wall slides open."},
    ]


def chests():
    return [
        {'id': 'chest:quartermaster', 'room': R('quartermaster'), 'at': [1536, -672], 'treasure_level': 5,
         'random_items': 3, 'gold': 1500, 'notes': "The quartermaster's strongbox in the corner (the source's cabinet)."},
        {'id': 'chest:niche_w', 'room': R('niche_w'), 'at': [-2720, 1728], 'treasure_level': 5,
         'random_items': 3, 'gold': 1200, 'notes': "Behind the west sliding wall."},
        {'id': 'chest:niche_e', 'room': R('niche_e'), 'at': [2720, 1728], 'treasure_level': 5,
         'random_items': 3, 'gold': 1200, 'notes': "Behind the east sliding wall."},
        {'id': 'chest:west_dorm', 'room': R('west_dorm'), 'at': [-2560, 1040], 'treasure_level': 5,
         'random_items': 3, 'gold': 2000, 'notes': "The order's strongbox in the west cells."},
    ]


S, DK = SLAYER, DEATH
PLACED = {
    # L1 (8)
    'hall': [(S, [-1280, -512]), (S, [1024, -512]), (S, [1408, -640])],
    'dormitory0': [(S, [1152, 1472]), (S, [1408, 1536])],
    'refectory': [(S, [2048, -512]), (S, [2304, 320]), (S, [2048, 512])],
    # L2 (12)
    'helms': [(S, [-1408, 256]), (S, [-1088, 640]), (S, [-1408, 896])],
    'north_gallery1': [(S, [-1024, 1600]), (DK, [0, 1600]), (S, [1024, 1600])],
    'mail': [(S, [1088, 256]), (DK, [1408, 640]), (S, [1088, 896])],
    'quartermaster': [(S, [960, -512]), (DK, [1216, -640]), (S, [1408, -448])],
    # L3 (15)
    'drill_w': [(S, [-1408, 0]), (S, [-1024, 512]), (S, [-1408, 896])],
    'drill_s': [(S, [-1280, -704]), (S, [-896, -896]), (S, [-512, -640]),
                (S, [640, -704]), (S, [1024, -896]), (DK, [1408, -640])],
    'drill_e': [(S, [1408, 0]), (DK, [1024, 512]), (S, [1408, 896])],
    'estair': [(S, [1872, 1216]), (DK, [2048, 1216]), (DK, [1872, 1024])],
    # L4 (10)
    'chapter_hall': [(S, [-1856, 256]), (S, [-1152, 512]), (DK, [-1536, 896])],
    'thrones': [(DK, [1536, -0]), (DK, [1536, 960]), (S, [2176, 384])],
    'west_dorm': [(S, [-2560, 256]), (DK, [-2560, 640])],
    'east_dorm': [(S, [2624, 256]), (DK, [2624, 768])],
}
FLOOR_OF = {'estair': geo.L3}       # the east wall stair's three stand on its head (896)


def monsters():
    out = []
    n = {}
    for room, lst in PLACED.items():
        for row, at in lst:
            n[(room, row)] = n.get((room, row), 0) + 1
            d = {'id': f'monster:{room}_{NAME[row]}_{n[(room, row)]}', 'room': R(room), 'monster': row, 'at': at,
                 'facing': 270, 'group': KNIGHT_GROUP}
            if room in FLOOR_OF:
                d['floor_height'] = FLOOR_OF[room]
            out.append(d)
    for k, (wall, off, at) in geo.NICHES.items():
        out.append({'id': f'monster:figure_{k}', 'room': R('chapter_hall'), 'monster': FIGURE, 'at': list(at),
                    'facing': {'w': 0, 's': 90}[wall], 'hostile': False, 'immobile': True, 'hidden': True,
                    'group': FIGURE_GROUP,
                    'notes': "A Voweless Knight (11925, D-61 Q28) in a niche of the chapter hall: placed hidden, shown by the oath (q-d17.oath) and on every later load; peaceful, immobile, not counted."})
    return out


PROPS = [
    # (key, decoration, room, at, floor height)
    ('statue', '7dec55', 'hall', list(geo.STATUE), geo.L1 + 64),
    ('chalice', '7dec46', 'chalice_room', list(geo.STAND), geo.L4 + 112),
    ('qm_barrel_1', 'bigbarel', 'quartermaster', [896, -672], None),
    ('qm_barrel_2', 'bigbarel', 'quartermaster', [992, -672], None),
    ('qm_sack_1', 'floursac', 'quartermaster', [1568, -384], None),
    ('qm_sack_2', 'bag01', 'quartermaster', [880, -384], None),
    ('refectory_cask_1', '7dec21', 'refectory', [2592, 960], None),
    ('refectory_cask_2', '7dec21', 'refectory', [2496, 960], None),
    ('refectory_candle', 'cndlab0', 'refectory', [2368, 832], geo.L1 + 80),
    ('drill_barrel_1', 'bigbarel', 'drill_s', [1568, -1056], None),
    ('drill_barrel_2', 'bigbarel', 'drill_s', [1472, -1056], None),
]
# Wall sconces (scon100, as DD-05): (room, wall, along)
SCONCES = [
    ('gatehouse', 'w', 0.5), ('gatehouse', 'e', 0.5), ('hall', 's', 0.25), ('hall', 's', 0.75), ('hall', 'n', 0.5),
    ('wgal', 'e', 0.75), ('egal', 'w', 0.75), ('lectern_w0', 'n', 0.25), ('dormitory0', 'e', 0.75),
    ('refectory', 'e', 0.3), ('refectory', 'n', 0.5), ('core', 's', 0.25), ('core', 's', 0.75),
    ('helms', 'n', 0.25), ('mail', 'n', 0.75), ('north_gallery1', 's', 0.5), ('quartermaster', 'e', 0.5),
    ('wstair', 'w', 0.25), ('estair', 'e', 0.25),
    ('drill_w', 'w', 0.5), ('drill_e', 'e', 0.5), ('drill_s', 'n', 0.5), ('west_study', 'n', 0.5),
    ('east_study', 'n', 0.5), ('core2', 's', 0.25), ('core2', 's', 0.75),
    ('chapter_hall', 'e', 0.25), ('chapter_hall', 's', 0.5), ('antechamber', 's', 0.5), ('antechamber', 'n', 0.15),
    ('chalice_room', 'e', 0.5), ('chalice_room', 'w', 0.5), ('thrones', 'n', 0.25), ('thrones', 's', 0.25),
    ('east_dorm', 'w', 0.15), ('west_dorm', 'e', 0.85), ('roof_loft', 'e', 0.5),
]
SCONCE_HEIGHT = 240


def decorations():
    out = []
    for key, dec, room, at, fh in PROPS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at}
        if fh is not None:
            d['floor_height'] = fh
        out.append(d)
    # the thrones (D-66 item 7): S's models, the origin at the seat's foot centre, `facing` the way the seat looks
    for key, ((x, y), back) in geo.THRONES.items():
        room = 'dunce' if key == 'dunce' else 'thrones'
        dec = 'xeen_throne_gold' if key == 'euphoria' else 'xeen_throne'
        out.append({'id': f'deco:throne_{key}', 'room': R(room), 'decoration': dec, 'at': [x, y],
                    'floor_height': geo.L4 + (48 if key == 'euphoria' else 0), 'facing': THRONE_FACING[back],
                    'notes': f"{THRONE_TITLE.get(key, 'Emotion Throne')} (clicked: evt:throne_{key})."})
    for i, (room, wall, along) in enumerate(SCONCES):
        out.append({'id': f'deco:sconce_{i}', 'room': R(room), 'decoration': 'scon100', 'wall': wall, 'along': along,
                    'height': SCONCE_HEIGHT + (geo.L1 if False else 0)})
    return out


THEME_COL = {'theme:tower': STONEL, 'theme:stair': STONEL, 'theme:knights': WARM}
# Two-storey rooms: a light below and one over the head.
TWO = {'core': ([0, 320], geo.L1, [0, 960], geo.L2), 'core2': ([0, 320], geo.L3, [0, 960], geo.L4),
       'wstair': ([-1984, -256], geo.L2, [-1984, 1024], geo.L3), 'estair': ([1984, -256], geo.L2, [1984, 1024], geo.L3)}
DIM = {'porch': 0.0, 'niche_w': 0.6, 'niche_e': 0.6, 'dunce': 0.7, 'roof_loft': 0.7}
AT = {'thrones': [1536, 832], 'hall': [384, -512], 'roof_loft': [2560, 1408]}


def lights():
    L = []

    def add(room, at, radius, color, height, fh=None, notes=None, lid=None):
        d = {'id': lid or f'light:{room}_{sum(1 for x in L if x["room"] == R(room)) + 1}', 'room': R(room), 'at': at,
             'radius': radius, 'color': color, 'height': height}
        if fh is not None:
            d['floor_height'] = fh
        if notes:
            d['notes'] = notes
        L.append(d)
    for room in geo.ORDER:
        if DIM.get(room, 1) == 0:
            continue
        (w, h), c = geo.extent(room)
        col = THEME_COL[geo.R[room][4]]
        if room in TWO:
            a, fa, b, fb = TWO[room]
            add(room, a, 1100, col, 320, fh=fa)
            add(room, b, 1100, col, 320, fh=fb)
            continue
        r = int(min(1800, max(700, 0.6 * max(w, h))) * DIM.get(room, 1))
        add(room, AT.get(room, list(c)), r, col, 320 if geo.R[room][3] - geo.R[room][2] <= 384 else 400)
    add('chalice_room', list(geo.STAND), 500, [220, 230, 255], 300, notes="The one lamp over the Chalice.")
    return L


def sounds():
    return [
        {'id': 'sound:tower_bed', 'room': R('core2'), 'at': [0, 320], 'height': 64, 'sound': 'xeen_amb_tower',
         'radius': 4200, 'inner_radius': 2400, 'volume': 0.3, 'pan': False,
         'notes': "The tower of Mok's bed (AUDIO.md xeen_amb_tower, quiet): one source in the core on L3, heard on every floor; a bed, not panned (D-48)."},
        {'id': 'sound:drill_wind', 'room': R('drill_s'), 'at': [0, -1024], 'sound': 'whistling wind', 'radius': 1400,
         'inner_radius': 400, 'volume': 0.3, 'notes': "Wind at the drill yard's slits."},
        {'id': 'sound:loft_wind', 'room': R('roof_loft'), 'at': list(geo.HATCH), 'height': 352, 'sound': 'whistling wind',
         'radius': 1000, 'inner_radius': 300, 'volume': 0.3, 'notes': "Wind round the roof trapdoor."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('gatehouse'), 'at': ARRIVAL_AT, 'facing': 'n',
                  'notes': "Inside the gate, 256 in, facing north into the tower."},
        'arrivals': [
            {'entrance': 'entrance:d5_tower', 'room': R('gatehouse'), 'at': ARRIVAL_AT, 'facing': 'n',
             'notes': "From D5's tower door (A6's door:dd08, q-d17.tower_door): (0, -1152, 0) facing north (512)."},
        ],
        'doors': doors(), 'plates': plates(), 'chests': chests(), 'monsters': monsters(),
        'decorations': decorations(), 'lights': lights(), 'sounds': sounds(),
        'notes': "DD-08's contents, written by output/studio_cal/dd08/tools/dress.py: 14 doors (the gate and the chapter hall's doors as hinged pairs, two sliding walls, the iron door), two step plates, four chests, 45 placed knights (33 Slayer, 12 Death) and, not counted, the four oath figures (11925) hidden in the chapter hall's niches.",
    }


# ------------------------------------------------------------------------------------------------- wiring
BOOK_TITLE = 'Book'
BED_NOTE = "A note under the pillow reads:  In life, to appreciate the highs one must experience the lows."
LESSONS = {
    'lesson_1': "You find a note under the pillow that reads:  Cliff Notes Lesson 1:\nEEEIOIE",
    'lesson_2': "You find a note under the pillow that reads:  Cliff Notes Lesson 2:\nEOAUAAUE",
    'lesson_3': "You find a note under the pillow that reads:  Cliff Notes Lesson 3:\nEEEOEAOUEIEEEOEE",
    'lesson_4': "You find a note under the pillow that reads:  Cliff Notes Lesson 4:\nOEOOEIEOOOAEI",
    'lesson_5': "You find a note under the pillow that reads:  Cliff Notes Lesson 5:\nOOOAIOEIEOU",
    'lesson_6': "You find a note under the pillow that reads:  Cliff Notes Lesson 6:\nAOOAIOEAEOOAE",
    'lesson_7': "You find a note under the pillow that reads:  Cliff Notes Lesson 7:\nIIEEEOEEEOUIE",
}
THRONE_TITLE = {'euphoria': 'Euphoria Throne', 'dunce': 'Throne of the Dunce'}
THRONE_FACING = {'w': 0, 'e': 180, 'n': 270, 's': 90}   # the back's side -> the way the seat looks
FINDS = {
    'shield_find': ('panel:shield_find', 'Shield', 5, "You lift the shield from its hooks."),
    'helm_find': ('panel:helm_find', 'Helm', 6, "You take the helm from its peg."),
    'mail_find': ('panel:mail_find', 'Armor', 4, "You take the black plate from its stand."),
}
VOICE_LUA = "\n".join([
    'if IsQBitSet(QBit(113342)) then',
    '    evt.StatusText("The mask is silent.")',
    '    return',
    'end',
    'if continueStep == 1 then',
    '    XeenQuests.hook("q-d17.voice")',
    '    return',
    'elseif continueStep == 2 then',
    '    XeenQuests.hook("q-d17.voice_wrong")',
    '    return',
    'elseif continueStep ~= nil then',
    '    XeenQuests.hook("q-d17.voice_other")',
    '    return',
    'end',
    'AskQuestionWithAnswerSteps(eventId, 3, "A disembodied voice thunders through your brain, \\"What do you seek?\\"\\nWht d y sk?",',
    '    {{Answer = "Chlc", Step = 1}, {Answer = "aie", Step = 1}, {Answer = "Chalice", Step = 2}})',
])
OATH_LUA = "\n".join([
    'if IsQBitSet(QBit(113344)) then',
    '    if XeenQuests.can("q-d17.oath_again") then',
    '        XeenQuests.hook("q-d17.oath_again")',
    '    else',
    '        XeenQuests.hook("q-d17.oath")',
    '    end',
    '    return',
    'end',
    'if continueStep == 1 then',
    '    if XeenQuests.hook("q-d17.oath") then',
    f'        evt.SetMonGroupBit({FIGURE_GROUP}, MonsterBits.Invisible, 0)',
    '    end',
    '    return',
    'end',
    'if continueStep ~= nil then',
    '    return',
    'end',
    'if not XeenQuests.can("q-d17.oath") then',
    '    XeenQuests.hook("q-d17.oath")',
    '    return',
    'end',
    'AskChoiceWithAnswerSteps(eventId, 3, "Swear the Voweless oath?", {{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})',
])
MIRROR_LUA = "\n".join([
    'if continueStep ~= nil then',
    '    evt.StatusText("The mirror does not respond.")',
    '    return',
    'end',
    'AskQuestionWithAnswerSteps(eventId, 1, "Where to?", {{Answer = "\\1", Step = 1}})',
])


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'arrived_once'}},
              'effects': [{'qbit': 'arrived_once'},
                          {'text': "The Northern Tower of the Voweless Knights. Bosco's Chalice is kept at the top, where a voice asks what you seek."}],
              'notes': "The first arrival (117640): the errand and where to go (the build's arrival check)."})
    E.append({'id': 'evt:exit_gate', 'preset': 'script', 'source': 'door:gate', 'title': "Exit the Knight's Tower",
              'effects': [{'exit': 'exit:d5_door'}],
              'notes': "The gate: the game's own leave window (D-24; 'Exit the Knight's Tower?', aaze0069:0) to D5's entrance:dd08_door (2560, 11776, 3008) facing 1536."})
    E.append({'id': 'evt:statue', 'preset': 'text', 'source': 'platform:statue', 'title': 'Statue', 'window': True,
              'text': "A plaque reads:\n\"In honor of the Grand Order of Voweless Knights\"",
              'notes': "The founder's statue (aaze0069:1-2)."})
    E.append({'id': 'evt:mirror', 'preset': 'script', 'source': 'panel:mirror', 'title': 'Mirror', 'lua': MIRROR_LUA,
              'notes': "The dead mirror (D-37's xkmirror): 'Where to?' then 'The mirror does not respond.' (aaze0069:3, :5)."})
    E.append({'id': 'evt:pulpit', 'preset': 'text', 'source': 'platform:pulpit', 'title': 'Pulpit', 'window': False,
              'text': "The silent reader's pulpit. Nobody reads here: the book is gone.",
              'notes': "The refectory's pulpit (map-local)."})
    # the seven books
    for key in geo.BOOK_ORDER:
        E.append({'id': f'evt:book_{key}', 'preset': 'script', 'source': f'platform:book_{key}', 'title': BOOK_TITLE,
                  'lua': f'if continueStep == 2 then\n    evt.PlaySoundName("closebook")\nend\nXeen.vowelessBook("{key}", eventId, continueStep)',
                  'notes': f"A Voweless book (D-61 Q25): A3's Xeen.vowelessBook(\"{key}\"): the proverb or its vowels runs q-d17.book_{key} (+1 to one statistic for each member new to it, a player bit); a wrong answer q-d17.book_wrong (the slam) and it may be tried again."})
    # beds and notes
    for key in geo.BEDS:
        if key.startswith('lesson'):
            E.append({'id': f'evt:bed_{key}', 'preset': 'text', 'source': f'platform:bed_{key}', 'title': 'Bed', 'window': True,
                      'text': LESSONS[key], 'notes': f"A bed in the cells: the Cliff Notes (aaze0072:{13 + int(key[-1])})."})
        elif key == 'dorm0_2':
            E.append({'id': f'evt:bed_{key}', 'preset': 'text', 'source': f'platform:bed_{key}', 'title': 'Bed', 'window': True,
                      'text': BED_NOTE, 'notes': "The pillow note (aaze0069:15): the thrones' answer-giver."})
        else:
            E.append({'id': f'evt:bed_{key}', 'preset': 'text', 'source': f'platform:bed_{key}', 'title': 'Bed', 'window': False,
                      'text': "Nothing here.", 'notes': "A bed (aaze0069:13-14)."})
    # the three hung finds
    for q, (src, title, kind, line) in FINDS.items():
        E.append({'id': f'evt:{q}', 'preset': 'script', 'source': src, 'title': title,
                  'condition': {'not': {'qbit': q}}, 'else_effects': [{'text': "Nothing here."}],
                  'effects': [{'qbit': q}, {'give_item': {'level': 5, 'kind': kind}}, {'text': line}],
                  'notes': f"A hung piece taken once ({title}, a T5 item of kind {kind}); then 'Nothing here.' (aaze0069:17, aaze0070:8)."})
    # the sliding walls
    for k, door, txt in (('wall_w', 'door:wall_w', 'west'), ('wall_e', 'door:wall_e', 'east')):
        E.append({'id': f'evt:{k}', 'preset': 'script', 'trigger': 'step', 'source': f'plate:{k}',
                  'condition': {'not': {'qbit': k}}, 'opens': [door],
                  'effects': [{'qbit': k}, {'lua': 'evt.PlaySoundName("stone door0301")'},
                              {'text': "With a grinding of stone, the wall before you slides aside."}],
                  'notes': f"The {txt} study's sliding wall (the source's grinding wall): opens as the party walks up, for good."})
        E.append({'id': f'evt:{k}_open', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
                  'condition': {'qbit': k, 'not': {'map_var': f'{k}_open'}}, 'opens': [door],
                  'effects': [{'set': {'var': {'map_var': f'{k}_open'}, 'value': 1}}],
                  'notes': "The wall stays open on later loads (and after a refill)."})
    # the voice and the iron door
    E.append({'id': 'evt:voice', 'preset': 'script', 'source': 'panel:mask', 'title': 'Mask', 'lua': VOICE_LUA,
              'notes': "The voice (D-61 Q27): aaze0072:2 and 'Wht d y sk?': Chlc or aie calls q-d17.voice (113342, the iron door opens); Chalice q-d17.voice_wrong (aaze0072:6); anything else q-d17.voice_other (aaze0072:7). After the answer: 'The mask is silent.'."})
    E.append({'id': 'evt:door_iron', 'preset': 'door', 'source': 'door:iron', 'title': 'Iron door',
              'condition': {'qbit': 'voice_answered'},
              'locked_text': "An iron door with no handle and no lock. Beside it, the mask waits.",
              'notes': "The iron door: shut until the voice is answered."})
    E.append({'id': 'evt:iron_open', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'voice_answered', 'not': {'map_var': 'iron_open'}}, 'opens': ['door:iron'],
              'effects': [{'set': {'var': {'map_var': 'iron_open'}, 'value': 1}}],
              'notes': "The iron door swings open with the voice's answer and stays open on every later load."})
    # the Chalice
    E.append({'id': 'evt:chalice', 'preset': 'script', 'source': 'platform:stand', 'title': 'Chalice',
              'condition': {'not': {'qbit': 'chalice_taken'}},
              'effects': [{'lua': 'XeenQuests.hook("q-d17.chalice")'}, {'hide': 'deco:chalice'}],
              'else_effects': [{'lua': 'XeenQuests.hook("q-d17.chalice")'}],
              'notes': "q-d17.chalice (113345): the Chalice of Protection (12525); 'An empty stand.' after (the hook's else text)."})
    E.append({'id': 'evt:chalice_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'chalice_taken'},
              'effects': [{'hide': 'deco:chalice'}], 'notes': "The stand stays empty once the Chalice is taken."})
    # the oath and the figures
    E.append({'id': 'evt:oath', 'preset': 'script', 'source': 'panel:plaque', 'title': 'Plaque', 'lua': OATH_LUA,
              'notes': "The order's plaque: with the Chalice, 'Swear the Voweless oath?' Yes calls q-d17.oath (113344) and shows the four figures; without it the hook's fail text; after the oath q-d17.oath_again for a newly eligible member, else the hook's else text."})
    E.append({'id': 'evt:figures_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'oath'},
              'effects': [{'show_actors': FIGURE_GROUP}],
              'notes': "The four Voweless Knights stay shown on every load after the oath (D-61 Q28)."})
    # the thrones
    for key in geo.THRONES:
        E.append({'id': f'evt:throne_{key}', 'preset': 'script', 'source': f'deco:throne_{key}',
                  'title': THRONE_TITLE.get(key, 'Emotion Throne'), 'lua': f'Xeen.vowelessThrone("{key}")',
                  'notes': f"A3's Xeen.vowelessThrone(\"{key}\") (D-61 Q26)."})
    # the roof
    E.append({'id': 'evt:roof', 'preset': 'script', 'source': 'platform:roof_hatch', 'title': 'Trapdoor',
              'condition': {'lua': 'XeenQuests.hook("d7.roof_dd08")'},
              'effects': [{'exit': 'exit:d7_roof'}],
              'notes': "The roof trapdoor (D-58): before m30.done the hook's 'The trapdoor is shut fast.'; after it the standard entrance window (F16, 2026-11-22: OK/Close, no Yes/No): OK up to D7's entrance:dd08_roof (5632, 15104, 1158) facing 512."})
    # doors and chests
    E.append({'id': 'evt:door_chapter', 'preset': 'door', 'source': 'door:chapter', 'title': 'Chapter hall'})
    for k, op, t, n in SINGLE:
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}', 'title': t})
    for c in ('quartermaster', 'niche_w', 'niche_e', 'west_dorm'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    return E


def wiring():
    vars_ = ['wall_w_open', 'wall_e_open', 'iron_open']
    return {'format': 0, 'variables': vars_, 'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-08's events, written by output/studio_cal/dd08/tools/dress.py."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
