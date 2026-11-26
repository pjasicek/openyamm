#!/usr/bin/env python3
"""XD-12 Darzog's Tower: plan.yml, project.yml and diagram.txt for L1 to L4.
L1: the floors and the vertical spine (one space per floor ring, the Well, the four stair halls, the roof, the set
pieces' rooms). L2: every room and its connections, population and treasure. L3: L2 with the to-scale sketch
(rooms.yml). L4: L3's plan with the build's words (world xeen, the world's rows)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy

import design
import geo
from emit import dump

PITCH = ("Baron Darzog's black tower on the wooded island in Lake Darzog, sealed since Crodo vanished. A square keep of "
         "four floors stands round one great Well open to the sky, where Darzog's lightning crackles from the gate floor "
         "to the clouds; every floor looks into it, and the windows and the battlements look out over the lake. Magic "
         "dies in this tower: the Baron's ward stills every spell but his own, so the party fights with steel. The gate "
         "floor's carnage hands, the forge where the hands are made, the library of his apprentices with its six study "
         "books and its cracked trapdoor floors, and at the top Darzog's own hall, where the Baron waits among six "
         "clones that wear his face. Behind his portrait sits Crodo. The roof opens on the clouds where Lord Xeen hides.")
PURPOSE = ("Story step M21 (QUESTS.md): with the Skeleton Key from the Tower of High Magic (M13) the party enters, kills "
           "Baron Darzog and his clones and frees Crodo, who tells them that 'Prince Roland' is Lord Xeen, that his "
           "hideout is in the clouds above this tower and that only the sword buried under Newcastle can kill him. The "
           "roof's cloud stair then leads up to X9, the Clouds of Xeen. Cloudside's first L set piece: monster levels "
           "30 to 48, Darzog 55; a party of about level 33 that leaves at about 36. The six study books give +5 to a "
           "stat each, once per character (the source's +20, rescaled).")
MOOD = ("Cold, high and quiet: grey keep stone, blue-white lightning up the Well, the red glow of the forge below the "
        "library's candles, the Baron's portraits watching; wind and open sky at the top, the lake far below.")

QBITS = {'darzog_slain': 110500, 'crodo_freed': 110501, 'library_door_opened': 110502}
ITEMS_XEEN = {'skeleton_key': 12100, 'library_key': 12230}

FLOOR_NAME = ['Gate floor', 'The works', 'The library', "Darzog's floor"]

REGIONS = [
    ('region:gate', 'Gate floor (0)', 'theme:gate', ['room:gate_hall', 'room:cloister_n', 'room:cloister_e',
     'room:cloister_s', 'room:cloister_w', 'room:hall_of_hands', 'room:guardroom', 'room:storeroom', 'room:cistern',
     'room:cells', 'room:crypt', 'room:west_stair'],
     "Castle Gloaming's grey keep stone, torches; carnage hands on guard."),
    ('region:works', 'The works (768)', 'theme:works', ['room:works_n', 'room:works_e', 'room:works_s',
     'room:works_w', 'room:forge', 'room:assembly', 'room:smelter', 'room:scrap_hall', 'room:parts_store',
     'room:quarters', 'room:east_stair'],
     "Red rock and lava: the forge where the hands are made."),
    ('region:library', 'The library (1536)', 'theme:library', ['room:library_n', 'room:library_e', 'room:library_s',
     'room:library_w', 'room:reading_room', 'room:great_library', 'room:study_ne', 'room:study_nw', 'room:study_se',
     'room:study_sw', 'room:library_stair'],
     "The School of Sorcery's books and flags; candles; trapdoors."),
    ('region:darzog', "Darzog's floor (2304)", 'theme:darzog', ['room:state_n', 'room:state_e', 'room:state_s',
     'room:state_w', 'room:darzog_hall', 'room:darzog_study', 'room:bedchamber', 'room:crodo_cell', 'room:clone_vats',
     'room:guard_hall', 'room:portrait_hall', 'room:sky_stair'],
     "Gloaming's state rooms: portraits, banners, the inlaid rug."),
    ('region:roof', 'The roof (3072)', 'theme:roof', ['room:roof_n', 'room:roof_s', 'room:roof_w', 'room:roof_e'],
     "Battlements under the open sky."),
    ('region:spine', 'The Well', 'theme:shaft', ['room:well'], "The core, gate floor to sky."),
    ('region:outside', 'The island and the lake', 'theme:outside', ['room:out_n', 'room:out_e', 'room:out_s',
     'room:out_w'], "Seen, not walked."),
]

# ---------------------------------------------------------------------------------------------------- links (L2+)
DOORS = {
    # opening: (kind, motion, condition, notes)
    'open:gate_guardroom': ('door', 'slide', None, 'Plank door.'),
    'open:gate_store': ('door', 'slide', None, 'Plank door.'),
    'open:hands_crypt': ('door', 'slide', None, 'Plank door.'),
    'open:cistern_cells': ('door', 'slide', None, 'Plank door.'),
    'open:works_estair': ('portcullis', 'slide', {'map_var': 'works_gate_up'},
                          "The works gate: a portcullis raised by the winch lever in the assembly hall (set:works_gate)."),
    'open:forge_smelter': ('door', 'slide', None, 'Plank door.'),
    'open:assembly_quarters': ('door', 'slide', None, 'Plank door.'),
    'open:library_lstair': ('door', 'slide', {'item': 'library_key'},
                            "The library stair door: carved, locked; the library key in the Chief Librarian's cabinet (great library) opens it."),
    'open:reading_study_nw': ('door', 'slide', None, 'Carved door.'),
    'open:great_study_sw': ('door', 'slide', None, 'Carved door.'),
    'open:state_hall': ('double_door', 'slide', None, "Darzog's doors: two leaves."),
    'open:hall_bedchamber': ('door', 'slide', None, 'Plank door.'),
    'open:hall_study': ('door', 'slide', None, 'Plank door.'),
    'open:bedchamber_cell': ('secret_door', 'slide', {'qbit': 'darzog_slain'},
                             "Darzog's portrait: the cell's door; Darzog's spell holds it until he dies (set:crodo)."),
    'open:disc_landing': ('door', 'slide', {'qbit': 'darzog_slain'},
                          "A black grille over the Well where the disc lands; open while the disc is up and Darzog is dead."),
}
STAIRS = {'open:wstair_works_w', 'open:wstair_scrap', 'open:wstair_quarters', 'open:estair_library_e',
          'open:estair_study_ne', 'open:estair_study_se', 'open:lstair_state_w', 'open:lstair_study',
          'open:lstair_guard', 'open:skystair_roof_n', 'open:skystair_roof_s', 'open:skystair_roof_e',
          'open:skystair_roof_nw', 'open:skystair_roof_sw'}
TRAPDOORS = geo.TRAPDOORS


def links_l2():
    out = []
    for o in geo.OPENINGS:
        oid = o['id']
        a, b = o['from'], o['to']
        if o.get('in') == 'floor':
            continue          # the trapdoors' holes: links below
        if b.startswith('room:out_') or a.startswith('room:out_'):
            continue          # windows and battlements over the lake: views, not ways
        lid = 'link:' + oid.split(':', 1)[1]
        d = {'id': lid, 'from': a, 'to': b}
        if oid in DOORS:
            kind, motion, cond, notes = DOORS[oid]
            d['kind'] = kind
            d['motion'] = motion
            if cond:
                d['condition'] = cond
            d['notes'] = notes
        elif 'win' in oid or o.get('sill', 0) and o.get('sill', 0) >= 96:
            d['kind'] = 'overlook'
            d['notes'] = 'A railed opening onto the Well: seen through, not walked.'
        elif oid in STAIRS:
            d['kind'] = 'stairs'
            d['rise'] = 768
            d['notes'] = "From the stair hall's hanging gallery at the upper floor."
        elif o.get('width') == 'full':
            d['kind'] = 'open'
            d['width'] = 'full'
        elif oid.startswith('open:arch') or o.get('shape') == 'arch':
            d['kind'] = 'open'
            d['width'] = o['width']
            d['notes'] = 'An arch.'
        else:
            d['kind'] = 'open'
            d['width'] = o['width']
        out.append(d)
    # the stair halls' own flights
    for hall, f in (('room:west_stair', 0), ('room:east_stair', 1), ('room:library_stair', 2), ('room:sky_stair', 3)):
        pass
    for tid, up, low, c in TRAPDOORS:
        out.append({'id': f'link:{tid}', 'from': up, 'to': low, 'kind': 'drop', 'one_way': True, 'rise': -768,
                    'notes': f"A trapdoor of cracked flags at {list(c)}: steps on it and the hatch drops to the works below (set:trapdoors); a winch lever below raises it again."})
    out.append({'id': 'link:disc', 'from': 'room:state_n', 'to': 'room:well', 'kind': 'lift', 'rise': -2304,
                'condition': {'qbit': 'darzog_slain'},
                'notes': "Darzog's disc: a stone disc 384 across on the Well's north face, from the gate floor to Darzog's floor; bound by his rune until he dies (set:disc)."})
    out.append({'id': 'link:fall', 'from': 'room:roof_n', 'to': 'room:out_n', 'kind': 'drop', 'one_way': True,
                'rise': -3072, 'notes': "Over the battlements (or out of a window): the fall lands on the island and leaves for X2."})
    return out


def entrances(level):
    return [
        {'id': 'entrance:tower_door', 'space': 'room:gate_hall', 'kind': 'both', 'neighbour': 'exit:lake_island',
         'facing': 'w', 'how': "Inside the tower door in the middle of the gate hall's east wall, facing west toward the Well; the door needs the Skeleton Key from outside.",
         'condition': {'item': 'skeleton_key'}},
        {'id': 'entrance:cloud_stair', 'space': 'room:roof_n', 'kind': 'exit', 'neighbour': 'exit:clouds_of_xeen',
         'how': "The cloud stair on the roof: white steps of cloud climbing from the north terrace into the sky.",
         'condition': {'qbit': 'crodo_freed'}},
        {'id': 'entrance:fall', 'space': 'room:out_e', 'kind': 'exit', 'neighbour': 'exit:lake_island',
         'how': "Falling from the keep (a window, the battlements): the party lands on the island's shore by Medin's jetty."},
    ]


GOALS = [
    {'id': 'goal:darzog', 'space': 'room:darzog_hall', 'kind': 'kill', 'what': 'Kill Baron Darzog (among his six clones).',
     'story': 'M21', 'gives': {'qbit': 'darzog_slain'}},
    {'id': 'goal:crodo', 'space': 'room:crodo_cell', 'kind': 'set', 'what': "Free Crodo from the cell behind Darzog's portrait.",
     'story': 'M21', 'handed_in_at': 'exit:lake_island', 'gives': {'qbit': 'crodo_freed'}},
]
KEYS = [
    {'id': 'key:skeleton_key', 'grants': {'item': 'skeleton_key'},
     'how': 'another map: the Tower of High Magic (XD-11, M13); the tower door on X2 tests it'},
    {'id': 'key:works_gate', 'grants': {'map_var': 'works_gate_up'}, 'found_in': 'room:assembly',
     'how': 'lever: the works gate winch on the assembly hall west wall'},
    {'id': 'key:library_key', 'grants': {'item': 'library_key'}, 'found_in': 'room:great_library',
     'how': "chest: the Chief Librarian's cabinet in the great library (he stands guard by it)"},
    {'id': 'key:darzog_dead', 'grants': {'qbit': 'darzog_slain'}, 'found_in': 'room:darzog_hall',
     'how': "kill: Darzog's death breaks his bindings (the portrait, the disc)"},
]
BOOKS = [('might', 'BaseMight', 'Might', 'room:study_se'), ('endurance', 'BaseEndurance', 'Endurance', 'room:study_sw'),
         ('intellect', 'BaseIntellect', 'Intellect', 'room:study_nw'),
         ('personality', 'BasePersonality', 'Personality', 'room:study_ne'),
         ('speed', 'BaseSpeed', 'Speed', 'room:reading_room'), ('accuracy', 'BaseAccuracy', 'Accuracy', 'room:great_library')]
POIS = [
    {'id': f'poi:book_{k}', 'space': room, 'kind': 'book',
     'behaviour': f"A study book on a lectern: whoever reads it gains +5 {name} for good, once per character (the source's +20 rescaled to MM6-MM8).",
     'uses': {'times': 1, 'per': 'character', 'reset': 'never'}} for k, sel, name, room in BOOKS
] + [
    {'id': 'poi:warning_note', 'space': 'room:library_e', 'kind': 'note',
     'behaviour': "Pinned at the head of the east stair, an apprentice's note: 'Mind the cracked flags. The Master's hatches drop you to the works, and the hands down there are not friendly. -- Wil'. Names the trapdoors' tell before the first one."},
    {'id': 'poi:darzog_journal', 'space': 'room:darzog_study', 'kind': 'book',
     'behaviour': "Darzog's journal on his desk: '... the old fool Crodo sits behind my own portrait, where he can admire me while he rots. Let him send his dreams; no spell leaves this tower.' Names the cell's door."},
    {'id': 'poi:portrait', 'space': 'room:bedchamber', 'kind': 'secret door',
     'behaviour': "Darzog's portrait. While Darzog lives: 'Behind the painted Baron's eyes something moves: an old man's face, then gone. The frame will not shift while Darzog's spell holds it.' After: it slides aside on the cell."},
    {'id': 'poi:crodo', 'space': 'room:crodo_cell', 'kind': 'npc',
     'behaviour': "Crodo, thin and grey. Clicking him: his story in a message window (M21's reveal: Roland is Lord Xeen, the hideout in the clouds above this tower, the sword under Newcastle); he goes home to Castle Burlock and the cloud stair will bear the party.",
     'gives': {'qbit': 'crodo_freed'}},
    {'id': 'poi:works_winch', 'space': 'room:assembly', 'kind': 'lever',
     'behaviour': 'Raises the works gate between the east walk and the east stair hall.', 'gives': {'map_var': 'works_gate_up'}},
]
SET_PIECES = [
    {'id': 'set:no_magic', 'kind': 'scripted', 'spaces': ['room:gate_hall'],
     'rule': "No spells inside the tower (a map flag): the party's spellbook, quick spells and scrolls are refused everywhere in the map; monsters still cast. The arrival message says so."},
    {'id': 'set:trapdoors', 'kind': 'trap', 'spaces': [t[1] for t in TRAPDOORS],
     'rule': "Five hatches of cracked flags (the School of Sorcery's c1t1fl, in a floor of whole flags) in the library's floors. Stepping on one drops it with the party to the works below (768); a winch lever beside the fallen hatch below raises it again (and whoever stands on it). The note at the east stair names the tell.",
     'inputs': ['step on a hatch'], 'states': ['set', 'dropped', 'raised again']},
    {'id': 'set:books', 'kind': 'puzzle', 'spaces': [b[3] for b in BOOKS],
     'rule': "Six study books on lecterns, one stat each: +5 to the reader's base stat, once per character (player bits)."},
    {'id': 'set:works_gate', 'kind': 'puzzle', 'spaces': ['room:works_e', 'room:assembly'],
     'rule': "The works gate (portcullis) bars the east stair; its winch lever is in the assembly hall. Clicking the gate while down says where the winch is."},
    {'id': 'set:darzog', 'kind': 'boss', 'spaces': ['room:darzog_hall'],
     'rule': "Baron Darzog among six clones that wear his face (one family of casters, his lightning). The real Baron is the one with his name and three times the hit points; when he dies his bindings break (qbit darzog_slain): the portrait yields, the disc unbinds, and a line says so.",
     'gives': {'qbit': 'darzog_slain'}},
    {'id': 'set:crodo', 'kind': 'scripted', 'spaces': ['room:bedchamber', 'room:crodo_cell'],
     'rule': "Darzog's journal names the portrait; the portrait shows an old man's face behind the Baron's eyes and will not move while Darzog lives; after his death it slides aside on Crodo's cell. Crodo tells the party the truth about Roland and goes home; the cloud stair on the roof will bear the party from then on.",
     'enabled_by': {'qbit': 'darzog_slain'}, 'gives': {'qbit': 'crodo_freed'}},
    {'id': 'set:disc', 'kind': 'scripted', 'spaces': ['room:well', 'room:state_n', 'room:cloister_n'],
     'rule': "Darzog's disc rides the Well's north face between the gate floor and Darzog's floor. It rests at the top behind a black grille, bound by Darzog's rune; after his death the grille opens while the disc is up, clicking the disc rides it, and a call button at each end brings it.",
     'enabled_by': {'qbit': 'darzog_slain'}},
    {'id': 'set:cloud_stair', 'kind': 'scripted', 'spaces': ['room:roof_n'],
     'rule': "White steps of cloud climb from the north roof. Before Crodo is freed they will not bear the party ('the cloud gives under your foot like fog'); after, the top step leads to X9."},
]
LANDMARKS = [
    {'id': 'landmark:lightning', 'space': 'room:well',
     'what': "A column of Darzog's lightning (pulsing blue-white lights) up the Well's axis from the rune circle to the sky.",
     'seen_from': ['room:cloister_e', 'room:works_n', 'room:library_n', 'room:state_n', 'room:roof_w']},
    {'id': 'landmark:lake', 'space': 'room:out_e', 'what': "Lake Darzog and the island's shore far below, from every window above the gate floor and from the battlements.",
     'seen_from': ['room:forge', 'room:reading_room', 'room:darzog_hall', 'room:roof_n', 'room:sky_stair']},
]
SIGHTLINES = [
    {'id': 'sightline:well_up', 'from': 'room:cloister_e', 'to': ['room:well', 'landmark:lightning'],
     'what': "Through the arch from the gate: up the Well past three floors of railed windows to the open sky."},
    {'id': 'sightline:well_down', 'from': 'room:roof_w', 'to': ['room:well'],
     'what': "From the roof's parapet, 3,000 down the Well to the rune circle."},
    {'id': 'sightline:lake', 'from': 'room:roof_s', 'to': ['room:out_s'],
     'what': "Over the battlements: the island's grass at the keep's foot, the lake, the sky."},
]


def spaces_l2():
    out = []
    for rid in geo.ORDER:
        meta = copy.deepcopy(design.SPACES[rid])
        d = {'id': rid, 'name': geo.ROOMS[rid]['name'], 'kind': meta.pop('kind', 'room')}
        for k in ('size', 'extent', 'shape', 'where', 'floor', 'clear_height', 'relief', 'features', 'purpose',
                  'population', 'treasure', 'empty', 'secret', 'backdrop', 'keep_clear', 'theme', 'light', 'palette',
                  'furniture'):
            if k in meta:
                v = meta[k]
                if k == 'theme':
                    v = {'gate': "Castle Gloaming (MM7 d03): keep stone cnb, flags tfb03, ceiling blocks t4s1fl",
                         'works': "Castle Gloaming's red rock cwb1, granite cfb1, lava",
                         'library': "School of Sorcery (MM7 7d14): twb2, 7tfb1, tfb2, bookcases 7t1books",
                         'darzog': "Castle Gloaming's state rooms: cnb with portraits cnbport, banners, the rug tfb1r4",
                         'shaft': "Castle Gloaming keep stone with brick courses; open sky",
                         'roof': "Gloaming flags, stone parapets, open sky",
                         'outside': "Island grass 7grastyl, lake 7wtrtyl, open sky"}[v]
                d[k] = v
        if 'relief' not in d:
            d['relief'] = 'flat'
        out.append(d)
    return out


def spaces_l1():
    """L1: the floors as one space each, the spine and the set pieces' rooms."""
    keep = ['room:gate_hall', 'room:well', 'room:west_stair', 'room:east_stair', 'room:library_stair', 'room:sky_stair',
            'room:darzog_hall', 'room:crodo_cell', 'room:great_library']
    full = {s['id']: s for s in spaces_l2()}
    out = [full[k] for k in keep]
    for f, (sid, name, purpose, pop) in enumerate([
        ('room:gate_floor', 'Gate floor', "The double ring of the gate floor round the Well's foot: the cloister (four galleries with arches into the Well), the hall of hands, guardroom, storeroom, cistern, cells and crypt. Carnage hands and eyes.",
         [design.P(design.POP_HANDS_B, 5), design.P(design.POP_EYES_A, 2)]),
        ('room:works', 'The works', "The construct works: four walks round the Well with railed windows, the forge of the hands, the assembly hall with the works gate's winch, smelter, scrap hall, parts store, the apprentices' quarters.",
         [design.P(design.POP_HANDS_B, 7), design.P(design.POP_MAGES_B, 1), design.P(design.POP_EYES_A, 1)]),
        ('room:library', 'The library', "The library: four reading walks, the reading room, the great library (the Chief Librarian and his key), four studies; the six study books; five trapdoors of cracked flags.",
         [design.P(design.POP_MAGES_B, 5), design.P(design.POP_EYES_B, 3)]),
        ('room:darzog_floor', "Darzog's floor", "The state rooms: four galleries (the disc's landing), Darzog's hall, study and bedchamber, the clone vats, the guard hall, the portrait hall.",
         [design.P(design.POP_HANDS_C, 2), design.P(design.POP_MAGES_C, 2)]),
    ]):
        if f == 0:
            pass
        out.append({'id': sid, 'name': name, 'kind': 'room', 'size': 'XL', 'extent': [6144, 6144], 'floor': geo.FL[f],
                    'clear_height': 640, 'relief': 'flat', 'shape': 'Square ring 6,144 across round the Well.',
                    'purpose': purpose, 'population': pop})
    out.append({'id': 'room:roof', 'name': 'The roof', 'kind': 'room', 'size': 'XL', 'extent': [6144, 6144],
                'floor': geo.ROOF, 'clear_height': 1152, 'relief': 'flat',
                'shape': "Battlemented terrace round the Well's rim under the open sky.",
                'purpose': "The vista and the cloud stair to X9.", 'population': [design.P(design.POP_EYES_B, 2)]})
    out.append({'id': 'room:outside', 'name': 'The island and the lake', 'kind': 'room', 'size': 'XL',
                'extent': [8704, 8704], 'floor': 0, 'clear_height': 4224, 'relief': 'flat', 'backdrop': True,
                'empty': True, 'shape': "Band of open air round the keep: grass, then water, then sky.",
                'purpose': "Seen from the windows and the roof; a fall lands here and leaves for X2."})
    return out


def links_l1():
    L = []

    def l(a, b, kind, **kw):
        d = {'id': f'link:{a.split(":")[1]}_{b.split(":")[1]}', 'from': a, 'to': b, 'kind': kind}
        d.update(kw)
        L.append(d)
    l('room:gate_hall', 'room:gate_floor', 'open', width=768, notes='A great arch.')
    l('room:gate_floor', 'room:well', 'open', width=512, notes='Four arches from the cloister into the Well.')
    l('room:gate_floor', 'room:west_stair', 'open')
    l('room:west_stair', 'room:works', 'stairs', rise=768)
    l('room:works', 'room:well', 'overlook', notes='Railed windows onto the Well.')
    l('room:works', 'room:east_stair', 'portcullis', condition={'map_var': 'works_gate_up'}, notes='The works gate.')
    l('room:east_stair', 'room:library', 'stairs', rise=768)
    l('room:library', 'room:great_library', 'open')
    l('room:library', 'room:library_stair', 'door', condition={'item': 'library_key'}, notes='The library stair door.')
    l('room:library', 'room:works', 'drop', one_way=True, rise=-768, notes='Five trapdoors.')
    l('room:library_stair', 'room:darzog_floor', 'stairs', rise=768)
    l('room:darzog_floor', 'room:darzog_hall', 'double_door')
    l('room:darzog_floor', 'room:crodo_cell', 'secret_door', condition={'qbit': 'darzog_slain'},
      notes="Darzog's portrait in his bedchamber.")
    l('room:darzog_floor', 'room:well', 'lift', rise=-2304, condition={'qbit': 'darzog_slain'},
      notes="Darzog's disc down the Well's north face to the gate floor.")
    l('room:darzog_floor', 'room:sky_stair', 'open')
    l('room:sky_stair', 'room:roof', 'stairs', rise=768)
    l('room:roof', 'room:well', 'overlook', notes="The parapet round the Well's rim.")
    l('room:roof', 'room:outside', 'drop', one_way=True, rise=-3072, notes='Over the battlements: to X2.')
    return L


DIAGRAM = r"""ROOF (+3072)  [roof terrace, open sky] -- cloud stair ==> X9 Clouds of Xeen (after Crodo)    battlements: fall ==> X2
                 ^ sky stair (E, open to the sky)            parapet round the Well's rim
DARZOG (+2304) [W gallery]-(state galleries round the WELL)-[E: sky stair]
                 |            |  arch           \ disc landing (grille) -- DISC down the Well to the gate floor (after Darzog)
                 |   [DARZOG'S HALL: Darzog + 6 clones]--[bedchamber: PORTRAIT #]--[CRODO'S CELL]
                 |   [study: journal, hoard $]   [clone vats]  [guard hall $]  [portrait hall]
                 ^ library stair (W), its door locked: the library key
LIBRARY (+1536)[E gallery: the note]-(reading walks)-[W: library stair]    TRAPDOORS v v v v v (to the works)
                 [reading room: Book of Speed]  [great library: Chief Librarian, his cabinet: KEY; Book of Accuracy]
                 [4 studies: Might, Endurance, Intellect, Personality]
                 ^ east stair (E), behind the works gate
WORKS (+768)   [W gallery]-(walks)-[E: works gate (portcullis)]   winch lever in the assembly hall
                 [forge of the hands: lava]  [assembly hall: WINCH]  [smelter $] [scrap] [parts] [quarters $]
                 ^ west stair (W)
GATE (0)       [gate hall] <== TOWER DOOR (Skeleton Key from X2's side) -- arch -- (cloister round the WELL)
                 [hall of hands] [guardroom $] [storeroom $] [cistern] [cells] [crypt $]
THE WELL: one octagonal shaft from the gate floor to the sky; lightning up its axis; every floor looks in.
OUTSIDE: the island's grass and Lake Darzog under the open sky, seen from every window and the battlements.
 $ chest   # secret   stairs alternate W / E / W / E, so every floor is crossed.
"""


def project(level):
    built = level == 'L4'   # the built map: a map of the Xeen world since lane A8's move (2026-11-20)
    p = {
        'format': 0, 'id': 'xeen_xd12', 'name': "Darzog's Tower", 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'XD-12', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [17, 17], 'climbs': 'n'},
        'map_stats': {
            'id': 9140, 'encounter_chance': 10, 'treasure_level': 4, 'trap_dice': 6, 'perception_difficulty': 12,
            'refill_days': 336, 'music': 22 if built else 'tower_high', 'environment': 'stone hall',
            'lock_difficulty': 12,
            'bolster': 'LowerToEqual',
            # the world's slots (A2's source/map_rows.yml XD-12, map_stats row 9140); each marker's tier picks the row
            'slots': ([{'monster': 'Xeen Construct', 'tier': 5, 'per_marker': [2, 3], 'weight': 40},
                       {'monster': 'Xeen Wizard', 'tier': 0, 'per_marker': [2, 3], 'weight': 30},
                       {'monster': 'Xeen Eye', 'tier': 0, 'per_marker': [1, 2], 'weight': 30}] if built else
                      [{'monster': 'Magic constructs', 'tier': 3, 'per_marker': [2, 3], 'weight': 40},
                       {'monster': 'Wizards', 'tier': 3, 'per_marker': [2, 3], 'weight': 30},
                       {'monster': 'Eyes', 'tier': 2, 'per_marker': [2, 3], 'weight': 30}]),
        },
        'neighbours': [
            {'id': 'exit:lake_island', 'to': 'xeen_x2.odm' if built else 'X2', 'kind': 'door',
             'arrival_hint': "On Lake Darzog's wooded island in X2, in front of the tower door on the keep's east side, facing the jetty (east).",
             'condition': {'item': 'skeleton_key'},
             'notes': "X2's door:xd12 (devdocs/xeen/briefs/x2/DOORS.md): the tower door opens from outside only to the Skeleton Key (M13); from inside it always opens. A fall from the keep also lands here."},
        ],
        # arrived_once (2026-11-20, D-7 touch-up): the arrival window on the first arrival only (A3 to register in m21.yml)
        'qbits': dict(QBITS, arrived_once=110503) if built else QBITS,
        'items': ITEMS_XEEN,
        # solo_spells (U-18, 2026-11-26): the ward holds for a party, monsters included (no_monster_spells); a solo
        # run casts (a lone mage has no steel) and so do the monsters, every spell at half damage
        'rules': {'no_spells': True, 'no_monster_spells': True, 'solo_spells': True, 'solo_spell_damage_percent': 50},
    }
    if built:
        p['neighbours'][0].update({'arrival': [-15631, 3014, 768], 'direction': 0})
        # A8 session 17 (A3's segment 83 BLOCKER): X9 is built; the cloud stair's top step leaves for its arrival
        p['neighbours'].append(
            {'id': 'exit:clouds_of_xeen', 'to': 'xeen_x9.blv', 'kind': 'roof', 'one_way': True,
             'arrival': 'entrance:xd12_roof',
             'condition': {'qbit': 'crodo_freed'},
             'arrival_hint': "On the Clouds of Xeen (X9), at the foot of the cloud stair (X9's entrance:xd12_roof, "
                             "(0, -17920, 320) facing 512).",
             'notes': "The cloud stair's top step after m21.crodo: the map's own Yes/No 'Climb the cloud stair into "
                      "the sky?' (D-66's rule for a roof exit into a BLV), Yes leaves at once."})
    else:
        p['neighbours'].append(
            {'id': 'exit:clouds_of_xeen', 'to': 'X9', 'kind': 'roof', 'one_way': True,
             'condition': {'qbit': 'crodo_freed'},
             'arrival_hint': "On the Clouds of Xeen (X9), at the foot of the cloud stair that rises from Darzog's roof.",
             'notes': "X9 is not built: a placeholder exit."})
    p['notes'] = ("Xeen design brief, level %s, for a new map (no original). Story step M21 (devdocs/xeen/QUESTS.md). "
                  "Size L (MAPS.md section 0 and Dungeons): 50-75 sectors, 120-200 M units squared, about 70-80 monsters "
                  "plus the boss; monster levels 30 to 48, Darzog 55; Tres 4 (chests at 4, Darzog's hoard at 5). Ids: "
                  "map_stats 9140, qbits 110500-110599, items 12230-12299 (ACT2_BUILD.md)." % level)
    if built:
        p['notes'] += (" A map of the Xeen world: its map_stats, bolster and slot rows are the world's "
                       "(source/map_rows.yml, A2), the slots here repeat them. Slot 1 Magic constructs (Xeen Construct; "
                       "every marker tier c, Carnage Hand 35, 11602), slot 2 Wizards (Xeen Wizard; tier a, Wizard 36, "
                       "11190), slot 3 Eyes (Xeen Eye; tier a, Floating Eye 40, 11570; one or two a marker). Baron "
                       "Darzog is the boss row 11194, his six clones 11195, the Chief Librarian a Sorcerer (11191) with "
                       "his placed name, Crodo the world's peaceful character row 11900. Items: the Skeleton Key 12100 "
                       "(the tower door from outside), the library key 12230. Quest bits 110500-110502 as M21 names them "
                       "(source/quests/m21.yml). Music 22. exit:lake_island leads to X2 (xeen_x2.odm) at X2's DOORS.md "
                       "arrival. The cloud stair's top step leads to X9 (exit:clouds_of_xeen, X9's entrance:xd12_roof) "
                       "once Crodo is freed, after the map's own Yes/No.")
    return p


def plan(level):
    d = {'format': 0, 'level': 'L3' if level == 'L4' else level, 'pitch': PITCH, 'purpose': PURPOSE, 'mood': MOOD, 'datum': 'arrival'}
    if level == 'L1':
        d['spaces'] = spaces_l1()
        d['regions'] = [{'id': 'region:floors', 'name': 'The four floors and the roof',
                         'spaces': ['room:gate_floor', 'room:works', 'room:library', 'room:darzog_floor', 'room:roof'],
                         'theme': "Keep stone below, red rock in the works, books in the library, state rooms on top"}]
        d['links'] = links_l1()
        d['critical_path'] = ['room:gate_hall', 'room:gate_floor', 'room:west_stair', 'room:works', 'room:east_stair',
                              'room:library', 'room:great_library', 'room:library', 'room:library_stair',
                              'room:darzog_floor', 'room:darzog_hall', 'room:darzog_floor', 'room:crodo_cell']
        d['return_path'] = ['room:crodo_cell', 'room:darzog_floor', 'room:well', 'room:gate_floor', 'room:gate_hall']
    else:
        d['spaces'] = spaces_l2()
        d['regions'] = [{'id': r[0], 'name': r[1], 'spaces': r[3], 'theme': r[4]} for r in REGIONS]
        d['links'] = links_l2()
        d['critical_path'] = ['room:gate_hall', 'room:cloister_e', 'room:cloister_s', 'room:cloister_w',
                              'room:west_stair', 'room:works_w', 'room:works_s', 'room:assembly', 'room:works_s',
                              'room:works_e', 'room:east_stair', 'room:library_e', 'room:library_s',
                              'room:great_library', 'room:library_s', 'room:library_w', 'room:library_stair',
                              'room:state_w', 'room:state_n', 'room:darzog_hall', 'room:bedchamber', 'room:crodo_cell']
        d['return_path'] = ['room:crodo_cell', 'room:bedchamber', 'room:darzog_hall', 'room:state_n', 'room:well',
                            'room:cloister_n', 'room:cloister_e', 'room:gate_hall']
        d['loops'] = [
            {'id': f'loop:ring_{k}', 'spaces': [f'room:{p}_n', f'room:{p}_e', f'room:{p}_s', f'room:{p}_w'],
             'notes': 'The galleries round the Well on this floor are one ring.'}
            for k, p in (('gate', 'cloister'), ('works', 'works'), ('library', 'library'), ('darzog', 'state'))]
        d['loops'].append({'id': 'loop:disc', 'spaces': ['room:well', 'room:cloister_n', 'room:cloister_w',
                                                         'room:west_stair', 'room:works_w', 'room:works_e',
                                                         'room:east_stair', 'room:library_e', 'room:library_w',
                                                         'room:library_stair', 'room:state_w', 'room:state_n'],
                           'closed_until': {'qbit': 'darzog_slain'},
                           'notes': "Up the stairs, down the disc: the whole tower becomes a ring after Darzog."})
    d['entrances'] = entrances(level)
    d['goals'] = GOALS
    d['keys'] = KEYS
    if level != 'L1':
        d['points_of_interest'] = POIS
        d['landmarks'] = LANDMARKS
        d['sightlines'] = SIGHTLINES
    d['set_pieces'] = SET_PIECES
    if level == 'L4':
        # the built map (A8 session 17): X9 exists; the cloud stair's top step leads there once Crodo is freed
        d['set_pieces'] = copy.deepcopy(SET_PIECES)
        for sp in d['set_pieces']:
            if sp['id'] == 'set:cloud_stair':
                sp['rule'] = ("White steps of cloud climb from the north roof. Before Crodo is freed the cloud gives "
                              "like fog; after it the top step asks 'Climb the cloud stair into the sky?', and Yes "
                              "leaves for X9 (the Clouds of Xeen) at once.")
    if level != 'L1':
        d['mechanisms'] = [
            {'kind': 'plank door', 'count': 8, 'notes': "Gloaming's plank leaves 7trimd, folding sideways."},
            {'kind': 'carved door', 'count': 2, 'notes': "The School of Sorcery's hhm1d2 in the library."},
            {'kind': 'double door', 'count': 1, 'notes': "Darzog's hall."},
            {'kind': 'locked door', 'count': 1, 'notes': 'The library stair door (the library key).'},
            {'kind': 'portcullis', 'count': 1, 'notes': 'The works gate, raised by a winch lever in the assembly hall.'},
            {'kind': 'secret door', 'count': 1, 'notes': "Darzog's portrait (cnbport) over Crodo's cell."},
            {'kind': 'grille', 'count': 1, 'notes': "Over the disc's landing on Darzog's floor."},
            {'kind': 'lift', 'count': 1, 'notes': "Darzog's disc: 384 square, travel 2304, rests up; call buttons at each end."},
            {'kind': 'trapdoor (dropping hatch)', 'count': 5, 'notes': 'A lift in the works room under each, raised flush with the library floor; a step drops it; a winch lever below raises it.'},
            {'kind': 'lever', 'count': 6, 'notes': 'The works winch and the five trapdoor winches.'},
            {'kind': 'study book', 'count': 6, 'notes': 'Lecterns (clicked blocks).'},
            {'kind': 'readable', 'count': 2, 'notes': "The warning note; Darzog's journal."},
            {'kind': 'chest', 'count': 8, 'notes': 'Chests at level 4 (guardroom, storeroom, crypt coffin, smelter, quarters, great library bookcase, guard hall; the librarian\'s cabinet holds the key); Darzog\'s hoard at 5.'},
            {'kind': 'exit', 'count': 3, 'notes': 'The tower door (X2), the cloud stair (X9), a fall from the keep (X2).'},
        ]
        d['atmosphere'] = ("Cold and high. Music 22 (Castle Gloaming's) everywhere, environment stone hall. The Well is "
                           "the brightest place: a column of pulsing blue-white light up its axis (five lights from the "
                           "rune circle to the roof), braziers round the circle. The gate floor torchlit (ambient 14-16), "
                           "the works red from the lava (ambient 14), the library candlelit with chandeliers (ambient 16-18), "
                           "Darzog's floor dark state rooms with candelabra (ambient 18-20). The roof and the outside open "
                           "to the sky (atmosphere open_sky, preset fair, daylight). No magic anywhere (set:no_magic).")
    d['height_bands'] = [
        {'id': f'band:floor_{f}', 'level': geo.FL[f],
         'spaces': ([r for r in REGIONS[f][3] if r not in ('room:west_stair', 'room:east_stair', 'room:library_stair',
                                                             'room:sky_stair')] if level != 'L1' else
                    [['room:gate_floor', 'room:gate_hall'], ['room:works'], ['room:library', 'room:great_library'],
                     ['room:darzog_floor', 'room:darzog_hall', 'room:crodo_cell']][f]),
         'partly': [['room:west_stair'], ['room:west_stair', 'room:east_stair'], ['room:east_stair', 'room:library_stair'],
                    ['room:library_stair', 'room:sky_stair']][f]}
        for f in range(4)]
    d['height_bands'].append({'id': 'band:roof', 'level': geo.ROOF,
                              'spaces': ['room:roof'] if level == 'L1' else ['room:roof_n', 'room:roof_s', 'room:roof_w', 'room:roof_e'],
                              'partly': ['room:sky_stair']})
    d['diagram'] = {'file': 'diagram.txt'}
    if level in ('L3', 'L4'):
        d['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    d['totals'] = {'sectors': 55, 'floor_area_millions': 151, 'loops': 5, 'doors': 15, 'monsters_about': 80,
                   'spawn_points': 29, 'fixed_actors': 9, 'chest_events': 9, 'secret_faces': 2, 'height_range': 3392,
                   'critical_path_length': 26000}
    d['notes'] = ("Size L: about 55 sectors (the 4 floors' double rings of 10-12 rooms, the Well, 4 stair halls, the roof's "
                  "4 parts, 4 bands of open air outside the keep, Crodo's cell); floor area inside the L band without the outside "
                  "band (measured at L4: 150.8 M walked, 483.7 M with the band); about 80 monsters (29 spawn points of 2-3, "
                  "8 placed hostiles: Darzog, six clones and the Chief Librarian) in 1.2-1.5 per sector, none in the gate hall, stairs or outside. Floors 768 apart, "
                  "rooms 640 high (128 floors), the Well 4,224 high and open to the sky. Stairs alternate west and east "
                  "as two-storey halls with hanging galleries (rooms stack since S7; floor holes since S8), so every floor "
                  "is crossed; the works gate and the library door make each crossing a task. Chests at Tres 4, Darzog's "
                  "hoard at 5. Measured against MM7 Castle Gloaming (48 sectors, 175 M, height range 4,920) and Castle "
                  "Lambent / Clanker's Laboratory (the same three monster families).")
    return d


L1_KEEP = ['room:gate_hall', 'room:well', 'room:west_stair', 'room:east_stair', 'room:library_stair', 'room:sky_stair',
           'room:darzog_hall', 'room:crodo_cell', 'room:great_library']
L1_FLOOR = {'region:gate': 'room:gate_floor', 'region:works': 'room:works', 'region:library': 'room:library',
            'region:darzog': 'room:darzog_floor', 'region:roof': 'room:roof', 'region:outside': 'room:outside'}


def coarse(rid):
    if rid in L1_KEEP:
        return rid
    for reg in REGIONS:
        if rid in reg[3] and reg[0] in L1_FLOOR:
            return L1_FLOOR[reg[0]]
    return rid


def _remap(o):
    if isinstance(o, dict):
        return {k: _remap(v) for k, v in o.items()}
    if isinstance(o, list):
        out = []
        for x in o:
            y = _remap(x)
            if y not in out or not isinstance(y, str):
                out.append(y)
        return out
    if isinstance(o, str) and o.startswith('room:'):
        return coarse(o)
    return o


def write(level, folder):
    p = plan(level)
    if level == 'L1':
        for k in ('entrances', 'goals', 'keys', 'set_pieces'):
            p[k] = _remap(p[k])
    dump(folder / 'plan.yml', p)
    dump(folder / 'project.yml', project(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import shell  # noqa: F401
    lv = sys.argv[1]
    write(lv, Path(_REPO_ROOT + '/devdocs/xeen/briefs/xd12') / lv)
