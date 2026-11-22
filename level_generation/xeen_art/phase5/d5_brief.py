#!/usr/bin/env python3
"""D5 Desert of Doom and the Great Pyramid: the L1 brief (MU-3) in Map Studio's schema, written from the data below
(A6, phase 5).

    d5_brief.py        -> devdocs/xeen/briefs/d5/L1/{project,plan,sketch}.yml (then `oymap fmt` and `oymap validate`)

Edit this script, not the YAML. NOTES.md beside the brief is written by hand. Cells [x, y]: x east, y south, 512 units
each; heights in map units above the stars below the rim (0). The border points are read from D4's installed
heightmap (x 19, read only) and the shared D5/D6 border file (phase5/edge_d5_d6.json, not changed here). Nothing here
is read by the game.
"""
import json
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'devdocs/xeen/briefs/d5/L1'
N = 128
RIM_NORTH_Y = 24          # the north rim's cliff (the world's edge), as D4's and D6's
BOX = (19, 109)


def d4_column():
    """D4's installed west border column (x 19), heights by y: D5's east border column x 109 carries them."""
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_odm_file
    data = parse_odm_file(ROOT / 'assets_dev/worlds/xeen/maps/xeen_d4.odm')
    return [int(v) for v in (np.array(data['payload']['height_map'], int).reshape(N, N) * 32)[:, 19]]


def d6_column():
    """The shared D5/D6 border (A6's lead file): D5's west border column x 19."""
    return json.loads((HERE / 'edge_d5_d6.json').read_text())['heights_by_y']


def d2_row():
    """D2's installed north border row (y 19): D5's south border row y 109 roughly continues it (D2 is no crossing)."""
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_odm_file
    data = parse_odm_file(ROOT / 'assets_dev/worlds/xeen/maps/xeen_d2.odm')
    return [int(v) for v in (np.array(data['payload']['height_map'], int).reshape(N, N) * 32)[19]]


# ---------------------------------------------------------------------------------------------- geometry

RIM_POLY = [[0, 0], [128, 0], [128, RIM_NORTH_Y], [0, RIM_NORTH_Y]]
# The Parabolic Barrier: an arc of Ancient frames bowed south from the rim, its vertex before the Northern Tower
BARRIER = [[46, 24], [52, 28.5], [58, 31.5], [64, 33.5], [70, 34.5], [76, 34.5], [82, 33.5], [88, 31.5], [94, 28.5],
           [100, 24]]
PYRAMID = [[58, 80], [70, 80], [70, 92], [58, 92]]        # the Great Pyramid's base, 12 x 12 cells
OASIS = [[42, 77], [45, 76.5], [46.5, 78.5], [45, 80.5], [42.5, 80]]

SPACES_POLY = {
    'zone:rim': RIM_POLY,
    'zone:barrier_lee': BARRIER + [[100, 24], [46, 24]],
    'zone:quivering_forest': [[19, 24], [46, 24], [51, 30], [54, 40], [55, 47], [50, 51], [40, 53], [28, 56],
                              [19, 57]],
    'zone:cyclops_lair': [[32, 37], [38, 37], [38, 42], [32, 42]],
    'zone:highlands': [[46, 24], [109, 24], [109, 58], [100, 58], [92, 57], [80, 56], [66, 54], [60, 50], [55, 47],
                       [54, 40], [51, 30]],
    'zone:giants_hold': [[82, 43], [91, 43], [91, 49], [82, 49]],
    'zone:tower_knoll': [[66, 36], [73, 36], [73, 42], [66, 42]],
    'zone:bosco_terrace': [[58, 44], [64, 44], [64, 49], [58, 49]],
    'zone:escarpment': [[19, 57], [28, 56], [40, 53], [50, 51], [55, 47], [60, 50], [66, 54], [80, 56], [92, 57],
                        [100, 58], [100, 62], [86, 62], [72, 60.5], [56, 59.5], [42, 60], [32, 61], [19, 60]],
    'zone:west_pass': [[19, 60], [32, 61], [34, 68], [19, 68]],
    'zone:desert_of_doom': [[19, 68], [34, 68], [32, 61], [42, 60], [56, 59.5], [56, 72], [52, 78], [54, 96],
                            [52, 101], [19, 101]],
    'zone:oasis': [[40, 75], [48, 75], [48, 82], [40, 82]],
    'zone:shrine_mesa': [[28, 85], [35, 85], [35, 91], [28, 91]],
    'zone:perishing_sands': [[56, 59.5], [72, 60.5], [86, 62], [100, 62], [100, 74], [100, 86], [102, 101],
                             [52, 101], [54, 96], [52, 78], [56, 72]],
    'zone:pyramid_precinct': [[56, 77], [72, 77], [72, 94], [56, 94]],
    'zone:boulder_field': [[82, 79], [88, 79], [88, 84], [82, 84]],
    'zone:boulders_west': [[34, 68], [40, 68], [40, 73], [34, 73]],
    'zone:east_valley': [[100, 62], [109, 62], [109, 101], [102, 101], [100, 86], [100, 74]],
    'zone:south_hills': [[19, 101], [102, 101], [109, 101], [109, 109], [19, 109]],
    'zone:grate_hollow': [[98, 99], [105, 99], [105, 104], [98, 104]],
}

# ---------------------------------------------------------------------------------------------- the plan


def S(id_, name, kind, purpose, **kw):
    d = {'id': id_, 'name': name, 'kind': kind}
    d.update(kw)
    d['purpose'] = purpose
    return d


SPACES = [
    # ---- the arrivals ----
    S('zone:east_valley', "The forest's end", 'zone', floor=[1250, 2100], relief='slope', density='sparse',
      where="east, the level valley out of D4's Forest of Peril and the slopes either side",
      purpose="Where the party comes in from D4: the desert road leaves the last firs of the Forest of Peril along a "
              "level valley at 1,500 and the desert opens west, the Great Pyramid far off over the dunes, the broken "
              "travel pyramid on the slope to the right, the highlands' cliffs along the north.",
      keep_clear=['spawns']),
    S('zone:west_pass', "The Forbidden Zone pass", 'zone', floor=[1500, 1900], relief='slope',
      where="west, the border pass at y 64 (1,700) between the Quivering Forest's flank and the western hills",
      purpose="Where the party comes in from D6: the road tops the pass out of the Forbidden Zone and goes down east "
              "into the Desert of Doom; the forest track turns north up the flank.",
      safe=True, keep_clear=['spawns']),
    # ---- the north ----
    S('zone:highlands', "The northern highlands", 'wild', floor=[2000, 3800], relief='uneven', density='sparse',
      purpose="Cold stony downs and snow in the hollows between the escarpment and the rim: the giants' country. "
              "Gurodel's hold and the great doors of his hall (DD-24), Bosco's Hall (DD-25) in a crag, the Northern "
              "Tower (DD-08) at the Parabolic Barrier's vertex, the Fountain of Might by the rim, an abandoned dwarf "
              "camp. Peaceful People giants at the hold; no wild monsters (the map's quiet quarter until Q-D16's war).",
      population=[{'id': 'pop:people', 'actor': 'Xeen Giant', 'groups': 1, 'placed': True, 'hostile': False,
                   'notes': "Gurodel's People at the hold: 6 placed, peaceful (A2's People rows 11083-11085, "
                            "faction xeen_giants_people, D-47, D-49 Q1); hostile on q-d16.war, q-d16.hall_attacked, "
                            "q-d12.hostile or q-d12.camp_burned. Not counted in the 110 at load."}]),
    S('zone:giants_hold', "Gurodel's hold", 'zone', part_of='zone:highlands', floor=2700,
      purpose="A shelf under a hillside: a ring of standing slabs round a great fire, hides on frames, a heap of "
              "boulders for throwing; Gurodel (5452) at his fire, talking (Q-D16: \"Greetings, little ones.\"). "
              "Behind the fire the hillside rises with the great doors of the Giants' Hall (DD-24), two leaves "
              "384 x 512.",
      safe=True, keep_clear=['spawns']),
    S('zone:bosco_terrace', "Bosco's door", 'zone', part_of='zone:highlands', floor=2650,
      purpose="A paved terrace under a grey crag on the highlands' south-west shoulder: the carved stone double door "
              "of Bosco's Hall (DD-25, the dwarf king's small hall with a smith, a tavern and the Earth guild), two "
              "lanterns, a bench, the dwarves' anvil sign.",
      safe=True, keep_clear=['spawns']),
    S('zone:tower_knoll', "The Northern Tower", 'zone', part_of='zone:highlands', floor=[2900, 3100],
      purpose="A knoll inside the Parabolic Barrier's curve: the Northern Tower of the Voweless Knights (DD-08), "
              "dark coursed stone, three storeys and a flat battlement, its door under the lintel \"Grnd rdr f "
              "Vwlss Knghts\" (q-d17.tower_door, Bosco's key).",
      safe=True, keep_clear=['spawns']),
    S('zone:barrier_lee', "Behind the Barrier", 'void',
      purpose="The strip between the Parabolic Barrier and the rim: bare rock and the drop to the stars. The curtain "
              "cannot be crossed; nothing is placed here (not counted as land).", empty=True),
    S('zone:quivering_forest', "The Quivering Forest", 'wild', floor=[2300, 3300], relief='uneven', density='dense',
      purpose="A highland forest of tall pale aspens whose leaves never stop trembling, on the plateau north-west "
              "of the pass: the cyclopes' lair, the forest track to the Barrier's west end and the Fountain of "
              "Energy Resistance.",
      population=[{'id': 'pop:forest_cyclopes', 'slot': 3, 'groups': 11, 'per_marker': [2, 3], 'levels': [36, 62],
                   'notes': "Encounter area E4: Cyclopes 36 (Giants 50, Elder Giants 62 rare): the source's C1 giant "
                            "lair, wild giants, not Gurodel's People."}]),
    S('zone:cyclops_lair', "The cyclopes' lair", 'zone', part_of='zone:quivering_forest', floor=2700,
      purpose="A trampled clearing of broken aspens, a bone heap and a lean-to of whole trunks: \"You have found a "
              "Giant's lair. Destroy?\" (aaze0009:1-2); the lair's hoard under the trunks."),
    S('zone:escarpment', "The Griffin Cliffs", 'wild', floor=[1450, 2900], relief='uneven', density='sparse',
      purpose="The highlands' south face: red and slate cliffs 600-1,200 high over the desert from the pass to the "
              "valley, broken by the highland road's switchbacks; griffins and rocs on the ledges, the eyrie with a "
              "dead griffin-hunter in the nest.",
      population=[{'id': 'pop:cliff_birds', 'slot': 2, 'groups': 11, 'per_marker': [1, 3], 'levels': [30, 48],
                   'notes': "Encounter area E3: Vulture Rocs 30, Rocs 38, Griffins 48 (Dif 2), and 3 Griffins 48 "
                            "placed at the eyrie."}]),
    # ---- the deserts ----
    S('zone:desert_of_doom', "The Desert of Doom", 'wild', floor=[1250, 2400], relief='uneven', density='sparse',
      purpose="Stony desert of wind-cut mesas and dry wadis between the pass and the dunes, rising to the western "
              "and southern hills: the obelisk by the road, the oasis, the Shrine of Great Power on its mesa, a "
              "dead prospector in a wadi, a genie's lamp in a ruined hill shrine; vulture rocs over the wadis.",
      population=[{'id': 'pop:doom_birds', 'slot': 2, 'groups': 10, 'per_marker': [1, 3], 'levels': [30, 48],
                   'notes': "Encounter area E5: Vulture Rocs over the wadis and the western hills; the first fight "
                            "from D6."}]),
    S('zone:oasis', "The Last Water", 'zone', part_of='zone:desert_of_doom', floor=1330,
      purpose="A spring pool under a few date palms in a hollow south of the road: the Last Water, a stone basin "
              "fed by the spring (d5.last_water: +2 Luck, permanent, once per character; D-49 Q5 as A2 swapped it).",
      safe=True, keep_clear=['spawns']),
    S('zone:shrine_mesa', "The Shrine of Great Power", 'zone', part_of='zone:desert_of_doom', floor=1900,
      purpose="A flat-topped mesa with a ramp cut in its north side: a ring of broken columns round an altar, "
              "\"Shrine of Great Power. Will the party pray?\" (aaze0010:15-17).",
      keep_clear=['spawns']),
    S('zone:perishing_sands', "The Perishing Sands", 'wild', floor=[1000, 1700], relief='uneven', density='open',
      purpose="A sea of high amber dunes east and south of the pyramid, a white salt pan in its lowest trough: "
              "iguanasaurus everywhere off the road; the boulder field by the road, a caravan swallowed by the sand, "
              "a lamp on a dune crest, the tunnel grate in the southern hills' foot.",
      population=[{'id': 'pop:sands_lizards', 'slot': 1, 'groups': 8, 'per_marker': [2, 3], 'levels': [42, 55],
                   'notes': "Encounter area E1: Iguanasaurus 42, Great 50, Ancient 55 (Dif 3); the first fight from "
                            "D4."},
                  {'id': 'pop:pyramid_lizards', 'slot': 1, 'groups': 7, 'per_marker': [2, 3], 'levels': [42, 55],
                   'notes': "Encounter area E2: the same round the pyramid's west and south sides."}]),
    S('zone:pyramid_precinct', "The Great Pyramid", 'zone', part_of='zone:perishing_sands', floor=1250,
      purpose="The Dragon Pharaoh's pyramid (DD-15): 12 x 12 cells at its foot, about 3,600 high, of great sandstone "
              "blocks with a gilded capstone, rising straight out of the dunes. Its door at the foot of the north "
              "face: a sealed door of green stone with the Pharaoh's sign, two leaves (m28.door, the Key to the "
              "Ancient Pyramid). A tomb robbers' camp at its south-east corner.",
      keep_clear=['buildings']),
    S('zone:boulder_field', "The east boulders", 'zone', part_of='zone:perishing_sands', floor=1380,
      purpose="Where the road meets the dunes (D-49 change 1): the weathered sign by the road (q-d24.sign) and four "
              "great Enchanted Boulders (q-d24.boulder_3-6) in a chained ring, each within 400 of the next: one spot.",
      safe=True, keep_clear=['spawns']),
    S('zone:boulders_west', "The west boulders", 'zone', part_of='zone:desert_of_doom', floor=1500,
      purpose="By the west road in the Desert of Doom (D-49 change 1): Enchanted Boulders 1, 2 and 7 (the seventh "
              "asks \"What am I?\") in a chained ring, each within 400 of the next: one spot; at least 2,600 from "
              "the obelisk knoll and the Last Water.",
      safe=True, keep_clear=['spawns']),
    S('zone:south_hills', "The Gemstone spurs", 'wild', floor=[1300, 3600], relief='uneven', density='sparse',
      purpose="Bare hills along the south, the Gemstone Range's last spurs (D2's north border runs on, 2,400-2,900, "
              "a peak of 3,550 at x 80): closed high ground, no crossing to D2. The tunnel grate in their foot.",
      empty=False),
    S('zone:grate_hollow', "The tunnel grate", 'zone', part_of='zone:south_hills', floor=1450,
      purpose="A rock hollow at the hills' foot: an iron grate in a stone arch, bolted on this side, over a long "
              "tunnel north from Sandcaster (DD-18). \"You draw the bolt. The grate swings open on a long tunnel.\"",
      safe=True, keep_clear=['spawns']),
    S('zone:rim', "The world rim", 'wild', floor=0,
      purpose="North the land ends in a cliff; below, the stars (water at 0 stands for them).", empty=True),
    S('water:rim_sea', "Below the rim", 'water', purpose="The stars below the world's edge (water at 0)."),
    S('water:last_water', "The Last Water's pool", 'water', part_of='zone:oasis',
      purpose="A spring pool about 4 x 4 cells at 1,320: it rises and sinks in the hollow (D-23; no river)."),
    # ---- junctions and edges ----
    S('junction:pyramid_fork', "Pyramid Fork", 'junction', signpost=True,
      purpose="East: the forest road (D4). South-west: the Great Pyramid. West: the Forbidden Zone (D6). North: the "
              "giants' highlands."),
    S('junction:scarp_foot', "The cliff road's foot", 'junction',
      purpose="Where the highland road leaves the desert road for its switchbacks up the cliffs."),
    S('junction:highland_fork', "Highland Fork", 'junction', signpost=True,
      purpose="At the top of the switchbacks: east, Gurodel's hold; north, the Northern Tower; west, Bosco's Hall."),
    S('junction:doom_fork', "Doom Fork", 'junction', signpost=True,
      purpose="East: the pyramid and D4. West: the pass to the Forbidden Zone (D6). South: the Last Water."),
    S('edge:east_end', "East edge", 'road', part_of='zone:east_valley', purpose="Where the road leaves for D4."),
    S('edge:west_end', "West edge", 'road', part_of='zone:west_pass', purpose="Where the road leaves for D6."),
]

LINKS = [
    {'id': 'link:desert_road', 'from': 'edge:east_end', 'to': 'junction:pyramid_fork', 'kind': 'road', 'rise': -100,
     'purpose': "travel: D4; the valley out of the Forest of Peril, past the broken pyramid and the boulder field"},
    {'id': 'link:west_road', 'from': 'junction:pyramid_fork', 'to': 'edge:west_end', 'kind': 'road', 'rise': 280,
     'purpose': "travel: D6; across the desert north of the pyramid, past the obelisk and Doom Fork, up the pass"},
    {'id': 'link:pyramid_track', 'from': 'junction:pyramid_fork', 'to': 'entrance:dd15_door', 'kind': 'path',
     'purpose': "over the sand to the pyramid's north door"},
    {'id': 'link:highland_road', 'from': 'junction:scarp_foot', 'to': 'junction:highland_fork', 'kind': 'path',
     'rise': 1050, 'purpose': "switchbacks up the Griffin Cliffs"},
    {'id': 'link:hold_lane', 'from': 'junction:highland_fork', 'to': 'zone:giants_hold', 'kind': 'path', 'rise': 200},
    {'id': 'link:tower_lane', 'from': 'junction:highland_fork', 'to': 'zone:tower_knoll', 'kind': 'path', 'rise': 500},
    {'id': 'link:bosco_lane', 'from': 'junction:highland_fork', 'to': 'zone:bosco_terrace', 'kind': 'path',
     'rise': 150},
    {'id': 'link:might_path', 'from': 'zone:giants_hold', 'to': 'poi:fountain_might', 'kind': 'path', 'rise': 500,
     'purpose': "along the giants' spring up to the rim"},
    {'id': 'link:broken_lane', 'from': 'link:desert_road', 'to': 'poi:capstone', 'kind': 'path', 'rise': 200,
     'purpose': "a short climb to the broken travel pyramid"},
    {'id': 'link:grate_track', 'from': 'link:desert_road', 'to': 'entrance:dd18_grate', 'kind': 'path',
     'purpose': "south over the dunes to the tunnel grate"},
    {'id': 'link:forest_track', 'from': 'link:west_road', 'to': 'zone:cyclops_lair', 'kind': 'path', 'rise': 1050,
     'purpose': "north up the forest's flank into the Quivering Forest"},
    {'id': 'link:barrier_path', 'from': 'zone:cyclops_lair', 'to': 'poi:fountain_energy', 'kind': 'path',
     'rise': 250, 'purpose': "through the aspens to the Barrier's west end"},
    {'id': 'link:oasis_track', 'from': 'junction:doom_fork', 'to': 'zone:oasis', 'kind': 'path', 'rise': -120},
    {'id': 'link:shrine_path', 'from': 'zone:oasis', 'to': 'zone:shrine_mesa', 'kind': 'path', 'rise': 570,
     'purpose': "down a wadi and up the mesa's ramp"},
]

ENTRANCES = [
    {'id': 'entrance:d4_road', 'space': 'zone:east_valley', 'kind': 'both', 'neighbour': 'edge:east', 'facing': 'w',
     'how': "The desert road from D4 at y 80 (D-36), where the Forest of Peril ends; arrival facing west."},
    {'id': 'entrance:d6_pass', 'space': 'zone:west_pass', 'kind': 'both', 'neighbour': 'edge:west', 'facing': 'e',
     'how': "The road from D6 over the Forbidden Zone pass at y 64 (edge_d5_d6.json); arrival facing east."},
    {'id': 'entrance:dd15_door', 'space': 'zone:pyramid_precinct', 'kind': 'both', 'neighbour': 'door:dd15',
     'facing': 'n', 'condition': {'item': 'pyramid_key'},
     'how': "The Great Pyramid's door: two leaves of green stone with the Pharaoh's sign (m28.door); without the "
            "key \"A sealed door of green stone with the Pharaoh's sign on it. The keyhole is the size of a royal "
            "favour.\" The way out returns 512 north of the door, facing north."},
    {'id': 'entrance:dd08_door', 'space': 'zone:tower_knoll', 'kind': 'both', 'neighbour': 'door:dd08',
     'facing': 's', 'condition': {'qbit': 'tower_key'},
     'how': "The Northern Tower's door (q-d17.tower_door, Bosco's key): \"Bosco's key turns. Over the door: "
            "'Grnd rdr f Vwlss Knghts'.\" Two iron-bound leaves."},
    {'id': 'entrance:dd24_doors', 'space': 'zone:giants_hold', 'kind': 'both', 'neighbour': 'door:dd24',
     'facing': 's',
     'how': "The great doors in the hillside behind Gurodel's fire: two leaves 384 x 512 (A7's DD-24). Inside "
            "arrival entrance:d5_hold; the way out returns 512 before the doors, facing south, clear of Gurodel."},
    {'id': 'entrance:dd25_door', 'space': 'zone:bosco_terrace', 'kind': 'both', 'neighbour': 'door:dd25',
     'facing': 'e',
     'how': "Bosco's Hall: a carved stone double door in the crag, two leaves (A8's DD-25, a small town BLV); open "
            "from day one."},
    {'id': 'entrance:dd18_grate', 'space': 'zone:grate_hollow', 'kind': 'both', 'neighbour': 'door:dd18',
     'facing': 'n',
     'how': "The long tunnel's grate (A3's dd18.d5_grate): a plain click \"You draw the bolt. The grate swings open "
            "on a long tunnel.\" sets d5_tunnel (116121); then the exit preset both ways. DD-18's exit:d5_grate "
            "arrives here, outside the grate facing north; D5's way in lands in DD-18 at (-7680, -5696, -640) "
            "facing east."},
]

GOALS = [
    {'id': 'goal:pyramid', 'space': 'zone:pyramid_precinct', 'kind': 'reach',
     'what': "Open the Great Pyramid with the Key to the Ancient Pyramid and climb to the Dragon Pharaoh (M28-M30).",
     'story': 'M28'},
    {'id': 'goal:gurodel', 'space': 'zone:giants_hold', 'kind': 'use',
     'what': "Talk to Gurodel: the People's friendship (two Energy Disks), or war and the bloody throne in DD-24 "
             "(Q-D16).", 'story': 'Q-D16'},
    {'id': 'goal:chalice', 'space': 'zone:tower_knoll', 'kind': 'reach',
     'what': "Take Bosco's key to the Northern Tower and bring back the Chalice of Protection (Q-D17).",
     'story': 'Q-D17'},
    {'id': 'goal:boulders', 'space': 'zone:boulder_field', 'kind': 'use',
     'what': "Hear the seven Enchanted Boulders in their two clusters and answer the seventh: Paladin (Q-D24).",
     'story': 'Q-D24'},
    {'id': 'goal:obelisk', 'space': 'zone:desert_of_doom', 'kind': 'use',
     'what': "Read the fifth Darkside word (obelisks.d5).", 'story': 'obelisks'},
    {'id': 'goal:hoard', 'space': 'zone:east_valley', 'kind': 'take',
     'what': "With all six Darkside words, dig under the broken travel pyramid's capstone (obelisks.dark_hoard).",
     'story': 'obelisks'},
]


def P(id_, space, kind, behaviour, **kw):
    d = {'id': id_, 'space': space, 'kind': kind}
    d.update(kw)
    d['behaviour'] = behaviour
    return d


POIS = [
    P('poi:obelisk', 'zone:desert_of_doom', 'obelisk',
      "obelisks.d5: the fifth of six words, TRAVEL (autonote dark_5, 115054).", rule='native:obelisk',
      notes="On a red rock knoll beside the west road, the pyramid in view to the south-east."),
    P('poi:shrine_great_power', 'zone:shrine_mesa', 'shrine',
      "\"Shrine of Great Power. Will the party pray?\" (aaze0010:15-17): +15 to all seven stats until the next rest "
      "(the source's +15 levels rescaled, as D1's prayer shrine's +3 levels became +10 all stats), once a day.",
      uses={'times': 1, 'per': 'character', 'reset': 'daily'}),
    P('poi:last_water', 'zone:oasis', 'fountain',
      "The Last Water (d5.last_water): +2 Luck, permanent, once per character (D-49 Q5: the least-served "
      "permanent stat by A2's ledger; the map's permanent device).",
      uses={'times': 1, 'per': 'character', 'reset': 'never'}),
    P('poi:fountain_energy', 'zone:quivering_forest', 'fountain',
      "The Fountain of Energy Resistance (aaze0009:3-5, \"Your spine tingles and the hair on the back of your neck "
      "stands on end.\"): +5 Air resistance, permanent, once per character (the source's +50 rescaled by D-4's +5 "
      "rule, as D4's magic resistance well). By the Barrier's west end.",
      uses={'times': 1, 'per': 'character', 'reset': 'never'}),
    P('poi:fountain_might', 'zone:highlands', 'fountain',
      "The Fountain of Might (aaze0013:9-11): +20 Might until the next rest (the source's +100 rescaled), once a day. "
      "A spring under the rim the giants drink from.",
      uses={'times': 1, 'per': 'character', 'reset': 'daily'}),
    P('poi:capstone', 'zone:east_valley', 'device',
      "obelisks.dark_hoard: the broken travel pyramid and its fallen capstone at its foot, within 400 of the "
      "pyramid's click (\"The pyramid portal has been destroyed.\", aaze0013:12): one spot (D-49 change 2); with all "
      "six Darkside words the party digs out the obelisk hoard, once.",
      uses={'times': 1, 'per': 'party', 'reset': 'never'}),
    P('poi:lamp_doom', 'zone:desert_of_doom', 'device', reached_by='off_road',
      behaviour="A genie's lamp in a ruined hill shrine in the western hills (aaze0010:11-14; Q-D27's wish choice, "
                "greed punished)."),
    P('poi:lamp_sands', 'zone:perishing_sands', 'device', reached_by='off_road',
      behaviour="A genie's lamp half buried on a high dune crest in the sand sea (aaze0014:15-18; Q-D27)."),
    P('poi:boulder_sign', 'zone:boulder_field', 'sign',
      "q-d24.sign: \"A weathered sign reads: A dying paladin gave all his magical armor to the enchanted boulders of "
      "the land for safekeeping.\""),
    P('poi:boulders', 'zone:boulder_field', 'device', count=4,
      behaviour="q-d24.boulder_3-6: four great Enchanted Boulders with the sign, a chained ring (each within 400 of "
                "the next: one spot with the sign). After q-d24.solved each crumbles when clicked, gives one random "
                "treasure-level-5 item and is hidden (crumbled_3-6). No chests."),
    P('poi:boulders_west', 'zone:boulders_west', 'device', count=3,
      behaviour="q-d24.boulder_1, 2 and 7: three Enchanted Boulders in a chained ring by the west road (one spot); "
                "the seventh asks \"What am I?\" (q-d24.answer: Paladin, the dead paladin's armour 12529; else "
                "answer_wrong). Boulders 1 and 2 crumble after the answer as the east ones (crumbled_1, 2)."),
    P('poi:giants_lair', 'zone:cyclops_lair', 'device',
      "\"You have found a Giant's lair. Destroy?\" (aaze0009:1-2): tearing it apart gives experience once (the "
      "source's +50,000 rescaled by A3).",
      uses={'times': 1, 'per': 'party', 'reset': 'never'}),
    P('poi:lair_hoard', 'zone:cyclops_lair', 'chest',
      "The cyclopes' hoard under the lean-to's trunks (a chest)."),
    P('poi:eyrie_nest', 'zone:escarpment', 'chest', reached_by='off_road',
      behaviour="The griffins' eyrie on a ledge of the cliffs: in the bones, a dead griffin-hunter's satchel (a chest), "
                "guarded by three griffins."),
    P('poi:caravan_wreck', 'zone:perishing_sands', 'chest',
      "A Sandcaster caravan the sands swallowed: a wagon's ribs and a strongbox at the salt pan's edge (a chest)."),
    P('poi:prospector', 'zone:desert_of_doom', 'chest',
      "A dead prospector in a wadi under an overhang, his pick and his pack (a chest)."),
    P('poi:dwarf_camp', 'zone:highlands', 'chest',
      "An abandoned dwarf prospectors' camp on the east highlands: a cold fire, picks, a sledge and a locked strongbox "
      "(a chest); Bosco's people stopped coming when the giants moved in."),
    P('poi:robbers_camp', 'zone:pyramid_precinct', 'chest',
      "Tomb robbers' camp at the pyramid's south-east corner: a torn tent, ropes up the blocks, a dead robber and "
      "his loot box (a chest)."),
    P('poi:munchies', 'zone:desert_of_doom', 'trap', count=2, spaces=['zone:desert_of_doom', 'zone:perishing_sands'],
      behaviour="\"SOMEONE in the party got the munchies and ate all the food!\" (aaze0010:18, aaze0014:20): a spot "
                "that empties the party's food, once a day. Hazards, not counted as points of interest."),
    P('poi:gurodel', 'zone:giants_hold', 'npc',
      "Gurodel, King of the People (5452), at his fire: Q-D16 (\"Greetings, little ones.\"). Not a point of interest "
      "(D-23 (1))."),
    P('poi:signposts', 'junction:pyramid_fork', 'signpost', count=3,
      spaces=['junction:pyramid_fork', 'junction:highland_fork', 'junction:doom_fork'],
      behaviour="Signposts at the three forks."),
]
for p in POIS:
    if 'spaces' in p:
        del p['space']

SET_PIECES = [
    {'id': 'set:enchanted_boulders', 'kind': 'puzzle', 'spaces': ['zone:boulder_field', 'zone:boulders_west'],
     'rule': "The seven Enchanted Boulders in two clusters (D-49 change 1): the sign and boulders 3-6 by the desert "
             "road, boulders 1, 2 and 7 by the west road; each cluster a chained ring within 400, one spot each in "
             "the census (D-20, D-11.4). Each boulder says one line of the riddle; the seventh asks for the answer.",
     'solution': "Paladin (the sign tells the story outright); the paladin's armour.",
     'gives': {'qbit': 'boulders_solved'}},
]

LANDMARKS = [
    {'id': 'landmark:great_pyramid', 'space': 'zone:pyramid_precinct',
     'what': "The Great Pyramid: a sandstone pyramid about 3,600 high and 6,100 along each side with a gilded "
             "capstone, rising straight out of the amber dunes",
     'seen_from': ['zone:east_valley', 'zone:west_pass', 'zone:perishing_sands', 'zone:desert_of_doom',
                   'zone:escarpment', 'zone:highlands', 'zone:boulder_field']},
    {'id': 'landmark:barrier', 'space': 'zone:highlands',
     'what': "The Parabolic Barrier: a long bowed line of tall Ancient metal frames (gn_mtl, xaenergy) along the north "
             "highlands with a shimmering xafield curtain between them, the rim's drop behind it; a blocking BModel "
             "up to the map's fly ceiling, no event, no click, not a POI (D-49 Q4)",
     'seen_from': ['zone:highlands', 'zone:perishing_sands', 'zone:quivering_forest', 'zone:escarpment']},
    {'id': 'landmark:broken_pyramid', 'space': 'zone:east_valley',
     'what': "The broken travel pyramid: a small Ancient metal pyramid, cracked open, its capstone fallen at its foot",
     'seen_from': ['zone:east_valley', 'zone:boulder_field']},
    {'id': 'landmark:northern_tower', 'space': 'zone:tower_knoll',
     'what': "The Northern Tower of the Voweless Knights on its knoll at the Barrier's vertex",
     'seen_from': ['zone:highlands', 'zone:perishing_sands']},
    {'id': 'landmark:giants_fire', 'space': 'zone:giants_hold',
     'what': "The giants' fire: a column of smoke from the highland shelf, seen from the desert",
     'seen_from': ['zone:perishing_sands', 'zone:east_valley', 'zone:boulder_field']},
]

SIGHTLINES = [
    {'id': 'view:arrival', 'from': 'entrance:d4_road',
     'to': ['landmark:great_pyramid', 'landmark:broken_pyramid', 'landmark:giants_fire', 'landmark:barrier'],
     'what': "Arrival from D4: the last firs of the Forest of Peril thin out along the level valley and the desert "
             "opens west: the road down to the boulder field, the dunes beyond, the Great Pyramid far off, the "
             "broken travel pyramid on the slope to the right and the cliffs of the highlands along the north."},
    {'id': 'view:signature', 'from': 'zone:perishing_sands', 'to': ['landmark:great_pyramid'],
     'what': "The signature view from a dune crest south-east of the pyramid: the Great Pyramid rising from the "
             "dunes under the amber Darkside day band and the pale small sun, the robbers' tent at its foot, the "
             "Griffin Cliffs and the highlands' Barrier faint beyond."},
]

STATES = [
    {'id': 'state:peace', 'condition': {'not': {'any': [{'qbit': 'giants_war'}, {'qbit': 'sardaj_hostile'},
                                                         {'qbit': 'sardaj_camp_burned'}, {'qbit': 'hall_attacked'}]}},
     'atmosphere': "The People at their fire, friendly; the hold and the doors of their hall open.",
     'notes': "A2's relations: the People friendly at load."},
    {'id': 'state:war', 'condition': {'any': [{'qbit': 'giants_war'}, {'qbit': 'sardaj_hostile'},
                                              {'qbit': 'sardaj_camp_burned'}, {'qbit': 'hall_attacked'}]},
     'effects': ["The six People giants at the hold turn hostile (A2's relations); Gurodel's talk closes "
                 "(q-d16.yml); DD-24's giants wait on the stair."]},
    {'id': 'state:tunnel_open', 'condition': {'qbit': 'd5_tunnel'},
     'effects': ["The grate stands open both ways (DD-18's exit:d5_grate)."]},
    {'id': 'state:boulders_solved', 'condition': {'qbit': 'boulders_solved'},
     'effects': ["The seventh boulder is gone (\"Where the boulder stood there is only sand.\"); the six others "
                 "crumble when clicked, leave one treasure-level-5 item each and are hidden (q-d24.crumbled_1-6)."]},
]

HEIGHT_BANDS = [
    {'id': 'band:rim_sea', 'range': [0, 0], 'spaces': ['zone:rim', 'water:rim_sea']},
    {'id': 'band:sands', 'range': [950, 1800], 'spaces': ['zone:perishing_sands', 'zone:pyramid_precinct',
                                                          'zone:boulder_field'],
     'notes': "The salt pan at about 1,000; the dunes to 1,700; the pyramid's plinth 1,250."},
    {'id': 'band:doom', 'range': [1200, 3000], 'spaces': ['zone:desert_of_doom', 'zone:oasis', 'zone:shrine_mesa'],
     'notes': "Stony desert 1,300-1,600 rising west to the hills; the mesa 1,900; the oasis 1,330."},
    {'id': 'band:valley', 'range': [1200, 2400], 'spaces': ['zone:east_valley'],
     'notes': "D4's x 19 column: 2,080 at y 58, the valley 1,504-1,536 at y 76-84, 1,248 at y 100-109."},
    {'id': 'band:pass', 'range': [1450, 2600], 'spaces': ['zone:west_pass'],
     'notes': "The shared border: 1,696 at y 62-66, 2,400 at y 54, 2,150 at y 72."},
    {'id': 'band:scarp', 'range': [1300, 3000], 'spaces': ['zone:escarpment']},
    {'id': 'band:forest', 'range': [2000, 3400], 'spaces': ['zone:quivering_forest', 'zone:cyclops_lair']},
    {'id': 'band:highlands', 'range': [2000, 3900], 'spaces': ['zone:highlands', 'zone:giants_hold',
                                                               'zone:tower_knoll', 'zone:bosco_terrace',
                                                               'zone:barrier_lee']},
    {'id': 'band:hills', 'range': [1200, 3700], 'spaces': ['zone:south_hills', 'zone:grate_hollow'],
     'notes': "D2's north border row (y 19) runs on along y 109: 2,400-2,900, 3,550 at x 79-82; the south-east "
              "corner falls to D4's 1,248."},
]

PLAN = {
    'format': 0,
    'level': 'L1',
    'pitch': "Darkside's top middle, between the Forest of Peril and the Forbidden Zone. A basin of desert under the "
             "amber day: the Perishing Sands in the east and south, a sea of high dunes with a white salt pan, and "
             "rising out of it the Great Pyramid of the Dragon Pharaoh, alone and enormous; the Desert of Doom in "
             "the west, stony mesas and dry wadis, an oasis, a shrine on a mesa. Along the north the Griffin Cliffs "
             "lift the cold highlands of the giants: Gurodel's fire and the doors of his hall, Bosco's dwarf hall in "
             "a crag, the Northern Tower, and before the rim the Parabolic Barrier, a bowed line of Ancient frames "
             "with a shimmering curtain. In the north-west the aspens of the Quivering Forest never stop trembling.",
    'purpose': "Act V's wilderness map (party 42-45): the Great Pyramid and DD-15 (M28-M30), Gurodel's giants and "
               "DD-24 (Q-D16), Bosco's Hall (DD-25) and the Northern Tower (DD-08, Q-D17), the Enchanted Boulders "
               "(Q-D24), the fifth Darkside obelisk and the obelisk hoard under the broken travel pyramid, the far "
               "end of Sandcaster's sewer tunnel (DD-18), two genie lamps (Q-D27); the road from D4 to D6.",
    'mood': "Heat haze under a low amber band and a small pale sun; wind hissing over sand; the pyramid's shadow "
            "long across the dunes; cold wind and woodsmoke on the highlands; the trembling of the aspens; the "
            "Barrier's faint hum.",
    'datum': 'water:rim_sea',
    'spaces': SPACES,
    'links': LINKS,
    'entrances': ENTRANCES,
    'critical_path': ['edge:east_end', 'junction:pyramid_fork', 'zone:pyramid_precinct'],
    'goals': GOALS,
    'points_of_interest': POIS,
    'set_pieces': SET_PIECES,
    'landmarks': LANDMARKS,
    'sightlines': SIGHTLINES,
    'height_bands': HEIGHT_BANDS,
    'states': STATES,
    'landform': {
        'relief': "A desert basin at 1,000-1,700 (the salt pan's 1,000 the lowest) closed by high ground on three "
                  "sides: the Griffin Cliffs (600-1,200 high) lifting the northern highlands to 2,500-3,000 and a "
                  "crest of 3,750 before the rim; the Quivering Forest's plateau (2,300-3,300) in the north-west; the "
                  "western hills along the D6 border (2,100-3,000) with the pass at 1,700 (y 64); the Gemstone spurs "
                  "along the south (D2's 2,400-2,900, 3,550 at x 80). East the level valley at 1,500 opens to D4 "
                  "(y 80). Inside the playable box the land spans about 1,000-3,750.",
        'height_range': [1000, 3750],
        'water': "No river (D-23): the Last Water's spring pool (about 12 cells) at 1,320; dry wadis from the "
                 "western hills and the cliffs end in the salt pan.",
        'water_share': 0.002,
        'caps': [{'kind': 'sand', 'share': 0.42, 'where': "the Perishing Sands and the pyramid's dunes"},
                 {'kind': 'bare rock', 'share': 0.12, 'where': "the Griffin Cliffs, the mesas, the Gemstone spurs"},
                 {'kind': 'snow', 'share': 0.04, 'where': "hollows of the highlands above 3,000"}],
        'rim': {'notes': "The world rim along the whole north (y 24): a cliff of 2,400-3,700 down to the stars. East "
                         "(D4), west (D6) and south (D2) the land runs to the map edge; the two roads run out to "
                         "theirs."},
    },
    'atmosphere': "Sky xeendark1 (xeen_darkside_day; Act V: A3's Lua switches to xeendark2/3, xeen_darkside_fading/"
                  "_failing, by stage); heat shimmer over the sands (no map weather by default); music 6. Wind and "
                  "blown sand on the dunes; the aspens' rustle in the Quivering Forest; the giants' fire crackling; "
                  "the Barrier's hum near its frames.",
    'sketch': {'file': 'sketch.yml', 'grid': 512},
    'totals': {'hostiles_at_load': 110, 'encounter_areas': 5, 'spawn_markers': 47, 'outdoor_chests': 6,
               'points_of_interest': 24, 'dungeon_entrances': 5},
    'notes': "MU-3 for the phase 5 review (A6, 2026-11-20). Source geography: Darkside C1 (the Quivering Forest, "
             "the giant's lair, the energy resistance fountain), C2 (the Desert of Doom, three Enchanted Boulders, "
             "the Shrine of Great Power, a lamp, the munchies), D1 (the Northern Tower, the Parabolic Barrier, "
             "Gurodel, Bosco, the Fountain of Might, the broken pyramid), D2 (the Great Pyramid, the Perishing "
             "Sands, four boulders, a lamp, the sewer's exit) (MM5_DARKSIDE_CONTENT 4; dark/aaze0009, 0010, 0013, "
             "0014). Written by level_generation/xeen_art/phase5/d5_brief.py; board "
             "level_generation/xeen_art/phase5/d5/board_d5.png. totals.points_of_interest is the render's census "
             "(measure.json).",
}

# ---------------------------------------------------------------------------------------------- project

PROJECT = {
    'format': 0,
    'id': 'xeen_d5',
    'name': 'Desert of Doom',
    'world': 'xeen',
    'kind': 'outdoor',
    'profile': 'odm',
    'map_code': 'D5',
    'units': {'plan_grid': 512},
    'extent': {'terrain_cells': 128},
    'map_stats': {
        'id': 9112,
        'encounter_chance': 10,
        'treasure_level': 5,
        'trap_dice': 6,
        'perception_difficulty': 6,
        'refill_days': 672,
        'music': 6,
        'environment': 'desert',
        'lock_difficulty': 12,
        'slots': [
            {'monster': 'Xeen Iguanasaurus', 'tier': 3, 'per_marker': [2, 3], 'weight': 40},
            {'monster': 'Xeen Roc', 'tier': 2, 'per_marker': [1, 3], 'weight': 40},
            {'monster': 'Xeen Giant', 'tier': 1, 'per_marker': [2, 3], 'weight': 20},
        ],
    },
    'neighbours': [
        {'id': 'edge:east', 'to': 'xeen_d4.odm', 'kind': 'edge', 'side': 'east', 'days': 5, 'arrival_side': 'west',
         'approach': "The desert road from D4's west edge at y 80 (D-36): the level valley out of the Forest of Peril.",
         'notes': "D4 Lakeside and Blackfang (installed). D4's west edge arrives at its (23, 80) facing east; D5's east "
                  "arrival is entrance:d4_road (105, 80) facing west. D5's east border column x 109 carries D4's x 19 "
                  "column cell for cell; its east rim repeats D4's west-rim spans word for word (D-36 (7)). A2 writes "
                  "the travel row when both are installed."},
        {'id': 'edge:west', 'to': 'xeen_d6.odm', 'kind': 'edge', 'side': 'west', 'days': 5, 'arrival_side': 'east',
         'listed_only': True,
         'approach': "The Forbidden Zone pass at y 64 (1,700 over y 62-66).",
         'notes': "D6 The Forbidden Zone (A6, phase 5, planned beside this one). The shared border is "
                  "level_generation/xeen_art/phase5/edge_d5_d6.json: D5's x 19 column = D6's x 109 column. D5's "
                  "arrival from D6 is entrance:d6_pass (23, 64) facing east. Sealed by a sign at the road's end "
                  "until D6 is installed."},
        {'id': 'door:dd15', 'to': 'xeen_dd15.blv', 'kind': 'door', 'condition': {'item': 'pyramid_key'},
         'arrival_hint': "Inside the green door, the pyramid's entrance hall on L1, facing south (A8).",
         'notes': "DD-15 Great Pyramid (A8, L): m28.door. Double-winged door: two leaves of green stone, the "
                  "Pharaoh's sign mirrored on the pair."},
        {'id': 'door:dd08', 'to': 'xeen_dd08.blv', 'kind': 'door', 'condition': {'qbit': 'tower_key'},
         'arrival_hint': "The Northern Tower's ground floor, facing north (A8).",
         'notes': "DD-08 Northern Tower (A8): q-d17.tower_door with Bosco's key; two iron-bound leaves."},
        {'id': 'door:dd24', 'to': 'xeen_dd24.blv', 'kind': 'door',
         'arrival_hint': "entrance:d5_hold, about 384 inside the leaves, facing into the hall (A7's DD-24 notes).",
         'notes': "DD-24 Giants' Hall (A7): the great doors behind Gurodel's fire, two leaves 384 x 512, open at "
                  "peace (A7's DECIDE 1a)."},
        {'id': 'door:dd25', 'to': 'xeen_dd25.blv', 'kind': 'door',
         'arrival_hint': "Inside Bosco's door, facing west into the hall (A8).",
         'notes': "DD-25 Bosco's Hall (A8, a small town BLV: smith, tavern, Earth guild; Bosco gives the tower key)."},
        {'id': 'door:dd18', 'to': 'xeen_dd18.blv', 'kind': 'door', 'condition': {'qbit': 'd5_tunnel'},
         'arrival_hint': "DD-18's exit:d5_grate side: (-7680, -5696, -640) facing east, inside the grate (A8).",
         'notes': "DD-18 Sandcaster Sewer (A8, installed): the grate bolted on the desert side (D-27); D5's plain "
                  "click (dd18.d5_grate) draws the bolt, then the exit preset both ways."},
    ],
    'qbits': {
        'pyramid_started': 111560,     # m28.started (A3)
        'tower_key': 113341,           # q-d17.key (A3)
        'giants_friends': 113320,      # q-d16.friends
        'giants_war': 113321,          # q-d16.war
        'sardaj_hostile': 113242,      # q-d12.hostile
        'sardaj_camp_burned': 113244,  # q-d12.camp_burned
        'boulders_solved': 113480,     # q-d24.solved
        'obelisk_dark_5': 115054,      # obelisks.dark_5
        'dark_hoard_found': 115057,    # obelisks.dark_hoard_found
        'd5_tunnel': 116121,           # dd18.d5_grate (A3's world bit)
        'hall_attacked': 113323,       # q-d16.hall_attacked (D5's hold or DD-24)
        'lair_destroyed': 116180,      # d5.lair
        'crumbled_1': 113481, 'crumbled_2': 113482, 'crumbled_3': 113483,     # q-d24.crumbled_1-6
        'crumbled_4': 113484, 'crumbled_5': 113485, 'crumbled_6': 113486,
    },
    'items': {'pyramid_key': 12348, 'paladins_armour': 12529},
    'rules': {'weather': 'none', 'respawn': 'entrance:d4_road', 'town_portal_anchor': 'entrance:d4_road',
              'rim': {'cliff_y': 24, 'fall': 'death', 'sides': ['north']}},
    'notes': "D5 Desert of Doom, MU-3 plan for the phase 5 review (A6, 2026-11-20). No geometry until a decider has "
             "approved the board. Plan: plan.yml; to-scale layout: sketch.yml; NOTES.md; drawings and board: "
             "level_generation/xeen_art/phase5/d5/. Sky xeendark1. Written by "
             "level_generation/xeen_art/phase5/d5_brief.py. Qbit and item numbers checked against A3's quest files "
             "(2026-11-21). D-49 applied (briefs/d5/L1/D49_DECISION.md).",
}

# ---------------------------------------------------------------------------------------------- sketch

# key heights inside the box: [x, y, h, note]
POINTS_H = [
    # the north: the Barrier's crest and the highlands
    [56, 28, 3200, None], [64, 31, 3400, None], [72, 31, 3550, None], [80, 30, 3750, "Gurodel's Crown, the crest"],
    [90, 28, 3500, None], [100, 27, 3350, None],
    [69, 39, 3000, "the Northern Tower's knoll"], [62, 40, 2850, None], [77, 40, 3100, None],
    [86, 40, 3250, "the hillside behind the hold: DD-24's doors in its foot"], [86, 46, 2700, "Gurodel's fire"],
    [94, 42, 2950, None], [102, 31, 3150, "the Fountain of Might"], [102, 40, 2900, None],
    [61, 46, 2650, "Bosco's door"], [66, 44, 2800, None], [76, 53, 2500, "Highland Fork"], [70, 50, 2600, None],
    [84, 52, 2500, None], [92, 52, 2450, None], [102, 50, 2500, "the dwarf camp"],
    # the Quivering Forest
    [28, 30, 3200, None], [38, 28, 3150, None], [47, 29, 2950, "the Fountain of Energy Resistance"],
    [35, 40, 2700, "the cyclopes' lair"], [26, 44, 2850, None], [44, 40, 2850, None], [50, 46, 2600, None],
    [36, 50, 2450, None], [26, 52, 2450, None], [44, 50, 2500, None],
    # the escarpment and its foot
    [50, 54, 2250, "the griffins' eyrie ledge"], [40, 57, 1850, None], [60, 58, 1600, None],
    [74, 61, 1600, "the switchbacks' foot"], [74, 57, 2050, None], [86, 60, 1750, None], [96, 60, 1950, None],
    [30, 59, 2000, None],
    # the west pass and the Desert of Doom
    [23, 64, 1700, "the D6 arrival"], [28, 65, 1620, None], [34, 67, 1520, None], [40, 68, 1450, "Doom Fork"],
    [46, 72, 1450, "the obelisk's knoll"], [44, 79, 1330, "the Last Water"], [36, 72, 1650, None],
    [28, 77, 1550, "the prospector's wadi"], [31, 88, 1900, "the Shrine of Great Power's mesa"],
    [24, 84, 2300, None], [24, 92, 2450, None], [24, 98, 2350, "the ruined hill shrine (lamp)"],
    [38, 95, 1650, None], [46, 88, 1450, None], [50, 82, 1380, None], [52, 96, 1500, None],
    # the Perishing Sands and the pyramid
    [64, 86, 1250, "the Great Pyramid's plinth (its apex about 4,850)"], [64, 79, 1260, "the pyramid's door"],
    [73, 93, 1300, "the robbers' camp"], [82, 98, 1550, "the signature dune crest"], [85, 96, 1500, "the lamp's dune"],
    [90, 92, 1000, "the salt pan"], [95, 91, 1080, "the caravan wreck"], [80, 90, 1300, None],
    [60, 64, 1500, None], [66, 68, 1450, None], [56, 76, 1350, None], [74, 66, 1500, None], [86, 70, 1450, None],
    [58, 97, 1450, None], [68, 98, 1500, None], [74, 87, 1350, None], [85, 83, 1380, "the boulder field"],
    [80, 77, 1420, "Pyramid Fork"], [74, 73, 1450, "the cliff road's foot"], [56, 70, 1420, None],
    # the east valley and the broken pyramid
    [105, 80, 1520, "the D4 arrival"], [100, 79, 1500, None], [95, 72, 1620, "the broken travel pyramid"],
    [102, 72, 1720, None], [104, 66, 1820, None], [102, 90, 1550, None], [100, 96, 1420, None],
    # the south hills and the grate
    [101, 102, 1450, "the tunnel grate"], [30, 104, 2250, None], [46, 104, 2150, None], [62, 104, 2100, None],
    [80, 105, 2900, "the spur under D2's 3,550 peak"], [90, 104, 2050, None],
]


def border_points():
    """Height points one cell inside each border, carrying the border cell's height (east: D4's x 19; west: the
    shared D5/D6 file; south: D2's y 19, falling in the corner to D4's 1,248)."""
    east, west, south = d4_column(), d6_column(), d2_row()
    out = []
    for y in range(26, 109, 4):
        out.append([108, y, east[y], f"D4's x 19 here {east[y]:,}" if y % 12 == 2 else None])
        out.append([20, y, west[y], f"edge_d5_d6 here {west[y]:,}" if y % 12 == 2 else None])
    # D-49 Q6: the last four cells of the shared column blend to D1's installed corner (2,636 ... 2,176)
    for y in (107, 108):
        out.append([20, y, west[y], f"edge_d5_d6 here {west[y]:,} (D-49 Q6, D1's corner)" if y == 108 else None])
    for x in range(24, 104, 6):
        out.append([x, 108, south[x], f"D2's y 19 here {south[x]:,}" if x % 18 == 6 else None])
    out.append([104, 108, 1700, "the south-east corner falls to D4's 1,248"])
    return out


BANDS = [
    ('band:rim_sea', 'zone:rim', RIM_POLY),
    ('band:highlands', 'zone:highlands', SPACES_POLY['zone:highlands']),
    ('band:forest', 'zone:quivering_forest', SPACES_POLY['zone:quivering_forest']),
    ('band:scarp', 'zone:escarpment', SPACES_POLY['zone:escarpment']),
    ('band:pass', 'zone:west_pass', SPACES_POLY['zone:west_pass']),
    ('band:doom', 'zone:desert_of_doom', SPACES_POLY['zone:desert_of_doom']),
    ('band:sands', 'zone:perishing_sands', SPACES_POLY['zone:perishing_sands']),
    ('band:valley', 'zone:east_valley', SPACES_POLY['zone:east_valley']),
    ('band:hills', 'zone:south_hills', SPACES_POLY['zone:south_hills']),
]

ROADS = [
    {'link': 'link:desert_road', 'line': [[109, 80], [105, 80], [100, 79], [94, 78.5], [88, 78.5], [84, 78],
                                          [80, 77]], 'width': 'road', 'surface': 'soil_stony'},
    {'link': 'link:west_road', 'line': [[80, 77], [76.5, 75], [74, 73], [70, 72.5], [64, 72], [58, 71.5], [52, 71],
                                        [47, 70.5], [43, 69.5], [40, 68], [36, 67], [32, 66], [28, 64.5], [24, 64],
                                        [19, 64]], 'width': 'road', 'surface': 'soil_stony'},
    {'link': 'link:pyramid_track', 'line': [[80, 77], [77, 78.5], [72, 79], [68, 79], [65, 79]], 'width': 'lane',
     'surface': 'sand_ripples'},
    {'link': 'link:highland_road', 'line': [[74, 73], [74, 70], [72.5, 67], [75, 64.5], [72.5, 62], [75, 59.5],
                                            [73.5, 57], [75.5, 55], [76, 53]], 'width': 'lane',
     'surface': 'soil_stony'},
    {'link': 'link:hold_lane', 'line': [[76, 53], [79, 51], [82, 49], [85, 47.5], [86, 46.5]], 'width': 'lane',
     'surface': 'soil_stony'},
    {'link': 'link:tower_lane', 'line': [[76, 53], [74.5, 49], [72, 45], [70, 42], [69.5, 40.5]], 'width': 'lane',
     'surface': 'soil_stony'},
    {'link': 'link:bosco_lane', 'line': [[76, 53], [72, 52], [68, 50.5], [64.5, 48], [62, 46.5]], 'width': 'lane',
     'surface': 'soil_stony'},
    {'link': 'link:might_path', 'line': [[87, 46], [91, 43], [95, 39], [99, 35], [101.5, 32]], 'width': 'lane',
     'surface': 'soil_stony'},
    {'link': 'link:broken_lane', 'line': [[96, 79], [95.5, 77], [94.5, 75]], 'width': 'lane',
     'surface': 'soil_stony'},
    {'link': 'link:grate_track', 'line': [[100, 79], [100.5, 84], [100, 90], [100.5, 96], [101, 101]],
     'width': 'lane', 'surface': 'sand_ripples'},
    {'link': 'link:forest_track', 'line': [[30, 65.5], [31, 61], [33, 57], [34.5, 53], [35, 48], [34.5, 44],
                                           [35, 41]], 'width': 'lane', 'surface': 'soil'},
    {'link': 'link:barrier_path', 'line': [[35, 40], [38, 36], [42, 33], [45.5, 30.5], [47, 29.5]], 'width': 'lane',
     'surface': 'soil'},
    {'link': 'link:oasis_track', 'line': [[40, 68], [41.5, 72], [43, 75], [44, 77]], 'width': 'lane',
     'surface': 'soil_stony'},
    {'link': 'link:shrine_path', 'line': [[44, 80], [40.5, 82], [37, 84.5], [34, 86.5], [32, 88]], 'width': 'lane',
     'surface': 'soil_stony'},
]

# D-49 change 1: two chained rings (each boulder within 400 of the next; the L3 places them to the unit, these
# whole cells are the drawing's)
BOULDERS = [[85, 81], [86, 81], [86, 82], [85, 82]]            # 3-6 with the sign, by the desert road
BOULDERS_WEST = [[37, 70], [38, 70], [37, 71]]                 # 1, 2, 7 by the west road

PTS = [
    ('entrance:d4_road', [105, 80], 'w'), ('entrance:d6_pass', [23, 64], 'e'),
    ('entrance:dd15_door', [64, 80], 'n'), ('entrance:dd08_door', [69, 40], 's'),
    ('entrance:dd24_doors', [86, 42], 's'), ('entrance:dd25_door', [61, 46], 'e'),
    ('entrance:dd18_grate', [101, 102], 'n'),
    ('junction:pyramid_fork', [80, 77], None), ('junction:scarp_foot', [74, 73], None),
    ('junction:highland_fork', [76, 53], None), ('junction:doom_fork', [40, 68], None),
    ('poi:obelisk', [46, 72], None), ('poi:shrine_great_power', [31, 88], None),
    ('poi:last_water', [46, 79], None), ('poi:fountain_energy', [47, 29], None),
    ('poi:fountain_might', [102, 31], None), ('poi:capstone', [95, 73], None),
    ('poi:lamp_doom', [24, 98], None), ('poi:lamp_sands', [85, 96], None),
    ('poi:boulder_sign', [85, 80], None),
    *[('poi:boulders', b, None) for b in BOULDERS],
    *[('poi:boulders_west', b, None) for b in BOULDERS_WEST],
    ('poi:giants_lair', [35, 40], None), ('poi:lair_hoard', [35, 40], None),
    ('poi:eyrie_nest', [50, 54], None), ('poi:caravan_wreck', [95, 91], None), ('poi:prospector', [28, 77], None),
    ('poi:dwarf_camp', [102, 50], None), ('poi:robbers_camp', [72, 93], None),
    ('poi:munchies', [38, 95], None), ('poi:munchies', [70, 99], None),
    ('poi:gurodel', [86, 46], None),
    ('poi:signposts', [81, 76], None), ('poi:signposts', [77, 52], None), ('poi:signposts', [41, 67], None),
    ('landmark:great_pyramid', [64, 86], None), ('landmark:barrier', [73, 35], None),
    ('landmark:barrier', [89, 32], None), ('landmark:barrier', [56, 31], None),
    ('landmark:broken_pyramid', [95, 72], None), ('landmark:northern_tower', [69, 38], None),
    ('landmark:giants_fire', [86, 45], None),
]

AREAS = [
    {'id': 'pop:sands_lizards', 'count': 8, 'slot': 1,
     'polygon': [[80, 88], [92, 86], [99, 85], [102, 90], [100, 97], [93, 97], [90, 104], [74, 105], [72, 96]],
     'notes': "E1: Iguanasaurus 42 (Great 50, Ancient 55; Dif 3) in the dunes east of the pyramid and round the salt "
              "pan; the first fight from D4 (about 4,400 off). The grate hollow kept clear."},
    {'id': 'pop:pyramid_lizards', 'count': 7, 'slot': 1,
     'polygon': [[48, 73], [57, 74], [56, 81], [55, 92], [71, 95], [72, 105], [52, 105], [48, 96], [50, 86]],
     'notes': "E2: the same west and south of the pyramid; none on the north door's apron or the track."},
    {'id': 'pop:cliff_birds', 'count': 11, 'slot': 2,
     'polygon': [[36, 51], [50, 49], [56, 49], [62, 53], [70, 55], [80, 56], [92, 57], [100, 57], [108, 56], [108, 64],
                 [98, 64], [92, 62], [80, 61.5], [70, 61], [56, 60.5], [44, 61], [36, 62]],
     'notes': "E3: Vulture Rocs 30, Rocs 38, Griffins 48 (Dif 2) on the Griffin Cliffs, east to the valley's north "
              "slope at the D4 border; 3 Griffins placed at the eyrie (50, 54)."},
    {'id': 'pop:forest_cyclopes', 'count': 11, 'slot': 3,
     'polygon': [[21, 27], [43, 26], [44, 33], [51, 34], [54, 41], [53, 47], [44, 50], [32, 53], [21, 54]],
     'notes': "E4: wild Cyclopes 36 (Giants 50, Elder Giants 62 rare; Dif 1) in the Quivering Forest round their "
              "lair; the Barrier's west end and its fountain outside it."},
    {'id': 'pop:doom_birds', 'count': 10, 'slot': 2,
     'polygon': [[21, 70], [34, 70], [37, 76], [38, 84], [44, 92], [47, 101], [21, 104]],
     'notes': "E5: Vulture Rocs over the wadis, the mesa and the western hills; the first fight from D6 (about 3,300 "
              "off)."},
    {'id': 'zone:east_valley', 'kind': 'keep_clear', 'polygon': [[99, 74], [109, 74], [109, 86], [99, 86]],
     'notes': "The D4 arrival."},
    {'id': 'zone:west_pass', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:west_pass'],
     'notes': "The D6 arrival."},
    {'id': 'zone:giants_hold', 'kind': 'keep_clear', 'polygon': [[80, 40], [93, 40], [93, 51], [80, 51]],
     'notes': "Gurodel's hold and DD-24's doors (peaceful People only)."},
    {'id': 'zone:bosco_terrace', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:bosco_terrace']},
    {'id': 'zone:tower_knoll', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:tower_knoll']},
    {'id': 'zone:oasis', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:oasis']},
    {'id': 'zone:boulder_field', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:boulder_field']},
    {'id': 'zone:boulders_west', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:boulders_west']},
    {'id': 'zone:grate_hollow', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:grate_hollow'],
     'notes': "The DD-18 grate and its arrival."},
]

ACTORS = [
    {'monster': '11562', 'at': [50, 54], 'count': 3, 'spread': 1, 'group': 1, 'hostile': True,
     'notes': "The eyrie: three Griffins 48 on the nest ledge (great_birds C)."},
    {'monster': '11083', 'at': [84, 47], 'count': 3, 'spread': 2, 'group': 3, 'hostile': False,
     'notes': "The People at the hold (D-47, D-49 Q1: A2's rows 11083-11085, faction xeen_giants_people, shared "
              "with DD-24; one blow on either map turns both): Cyclops 38 x3, peaceful until q-d16.war / "
              "hall_attacked / q-d12. Not counted in the 110."},
    {'monster': '11084', 'at': [88, 47], 'count': 2, 'spread': 1, 'group': 3, 'hostile': False,
     'notes': "Giant 50 x2 (People)."},
    {'monster': '11085', 'at': [89, 44], 'count': 1, 'spread': 0, 'group': 3, 'hostile': False,
     'notes': "Elder Giant 58 x1 by the doors (People)."},
    {'monster': '11085', 'npc': 5452, 'at': [86, 46], 'count': 1, 'spread': 0, 'group': 2, 'hostile': False,
     'notes': "Gurodel, King of the People (talking actor 5452) at his fire, facing south (Q-D16), on the People's "
              "Elder Giant row (D-47); not a fighter in the count (his talk closes at war)."},
]

VIEWS = [
    {'id': 'view:arrival', 'at': [105, 80], 'height': 180, 'look': [64, 80],
     'purpose': "MU-4 arrival view (about 76 degrees): from the D4 arrival in the level valley, looking west: the "
                "last firs of the Forest of Peril either side, the road running down to the boulder field, the dunes "
                "opening beyond, the Great Pyramid far off (about 21,000 away), the broken travel pyramid on the "
                "right-hand slope, the Griffin Cliffs and the highlands along the north (right)."},
    {'id': 'view:signature', 'at': [82, 98], 'height': 180, 'look': [64, 85],
     'purpose': "MU-4 signature view (about 60 degrees): from the dune crest south-east of the pyramid, looking "
                "north-west: the Great Pyramid rising from the dunes (about 11,300 away, its apex 15 degrees up), the "
                "robbers' tent at its foot, the pale small sun low in the amber band, the Griffin Cliffs and the "
                "Barrier's line faint beyond."},
]

SKETCH = {
    'format': 0,
    'grid': 512,
    'map_cells': 128,
    'notes': "D5 Desert of Doom, MU-3 to-scale plan (A6, 2026-11-20), for the phase 5 review: composition, scale and "
             "density only. Cells [x, y], x east, y south. Heights above the stars below the rim (0): the salt pan "
             "1,000, the sands 1,100-1,700, the Desert of Doom 1,300-2,000, the cliffs' foot 1,500-1,600, the "
             "highlands 2,500-3,000, the crest 3,750, the Gemstone spurs 2,100-2,900. Border points one cell inside "
             "each border carry the border's heights (D4's x 19 column, edge_d5_d6.json, D2's y 19 row). Written by "
             "level_generation/xeen_art/phase5/d5_brief.py. The later L3 adds plots' detail, ground, scatter and "
             "structures.",
    'frame': {
        'playable': [19, 19, 90, 90],
        'edges': [
            {'side': 'east', 'span': [72, 88], 'neighbour': 'edge:east',
             'notes': "The desert road runs out to x 127 at y 80 (D4's west edge, D-36)."},
            {'side': 'west', 'span': [58, 70], 'neighbour': 'edge:west',
             'notes': "The road runs out to x 0 at y 64 over the pass (edge_d5_d6.json)."},
        ],
        'rim': [
            {'side': 'north', 'form': 'level', 'height': 0, 'meet': 1,
             'notes': "The world rim: the land ends in a cliff at y 24; below, water at 0 stands for the stars."},
            # east: D4's west rim spans word for word (D-36 (7))
            {'side': 'east', 'span': [0, 24], 'form': 'level', 'height': 0, 'meet': 1,
             'notes': "D4's west edge [0, 24]: the north rim."},
            {'side': 'east', 'span': [24, 60], 'form': 'ridge', 'height': [2800, 3600], 'floor': 2200, 'crest': 10,
             'roughness': 120, 'notes': "D4's west edge [24, 60]: Magic Mountain's west flank."},
            {'side': 'east', 'span': [60, 72], 'form': 'ridge', 'height': [1800, 2300], 'floor': 1500, 'crest': 8,
             'roughness': 80, 'notes': "D4's west edge [60, 72]: forested hills."},
            {'side': 'east', 'span': [72, 88], 'form': 'level', 'height': 1500, 'meet': 6,
             'notes': "D4's west edge [72, 88]: the desert road's valley into the Forest of Peril."},
            {'side': 'east', 'span': [88, 104], 'form': 'ridge', 'height': [1500, 2000], 'floor': 1400, 'crest': 10,
             'roughness': 80, 'notes': "D4's west edge [88, 104]: dunes of the desert edge."},
            {'side': 'east', 'span': [104, 128], 'form': 'ridge', 'height': [2600, 3400], 'floor': 2000, 'crest': 10,
             'roughness': 120, 'notes': "D4's west edge [104, 128]: the last Gemstone crags (D3's north-west corner)."},
            # west: the shared D5/D6 border, the same spans and heights as D6's east rim (its L1 of 2026-11-20)
            {'side': 'west', 'span': [0, 24], 'form': 'level', 'height': 0, 'meet': 1,
             'notes': "The D5/D6 border [0, 24]: the north rim."},
            {'side': 'west', 'span': [24, 58], 'form': 'ridge', 'height': [2600, 3300], 'floor': 2200, 'crest': 10,
             'roughness': 120, 'notes': "The D5/D6 border [24, 58]: barren highlands of the Forbidden Zone."},
            {'side': 'west', 'span': [58, 70], 'form': 'level', 'height': 1700, 'meet': 6,
             'notes': "The D5/D6 border [58, 70]: the Forbidden Zone pass (1,700 at y 62-66)."},
            {'side': 'west', 'span': [70, 128], 'form': 'ridge', 'height': [2500, 3000], 'floor': 2100, 'crest': 10,
             'roughness': 120, 'notes': "The D5/D6 border [70, 128]: the Forbidden Zone's south-east hills."},
            # south: D2's north rim words (the Gemstone Range), then D4's corner
            {'side': 'south', 'span': [0, 100], 'form': 'ridge', 'height': [3400, 4400], 'floor': 2600, 'crest': 10,
             'roughness': 140, 'notes': "D2's north rim: the Gemstone Range, slate crags with crystal veins (no "
                                        "crossing)."},
            {'side': 'south', 'span': [100, 128], 'form': 'ridge', 'height': [1500, 2400], 'floor': 1300,
             'crest': 10, 'roughness': 80,
             'notes': "The corner where D2, D3 and D4 meet: dunes of D4's desert edge, D3's crags beyond."},
        ],
        'edge': {'height': 1500, 'north': 0},
    },
    'heights': {
        'bands': [{'band': b, 'space': s, 'polygon': poly} for b, s, poly in BANDS],
        'points': [],       # filled in main(): POINTS_H + border_points()
        'cliffs': [
            {'line': [[0, RIM_NORTH_Y], [128, RIM_NORTH_Y]], 'drop': 2000, 'down': 'left',
             'notes': "The world rim (drawn west to east, the low side outward)."},
            {'line': [[30, 57], [40, 54.5], [50, 52], [56, 49], [62, 53], [70, 55]], 'drop': 700, 'down': 'right',
             'notes': "The Griffin Cliffs' west half (the eyrie's ledge at (50, 54))."},
            {'line': [[78, 56], [86, 57], [94, 57.5]], 'drop': 500, 'down': 'right',
             'notes': "The Griffin Cliffs' east half, lower toward the valley."},
            {'line': [[29, 86], [33, 86], [34, 90], [29, 90], [29, 86]], 'drop': 350, 'down': 'right',
             'notes': "The shrine mesa's sides (its ramp on the north side)."},
        ],
        'ridges': [
            {'line': [[56, 28], [64, 31], [72, 31], [80, 30], [90, 28], [100, 27]], 'height': 3500, 'width': 2,
             'slope': 4, 'notes': "The highlands' crest along the Barrier, Gurodel's Crown 3,750 at (80, 30)."},
            {'line': [[62, 105], [72, 105], [80, 106], [90, 105]], 'height': 2700, 'width': 2, 'slope': 3,
             'notes': "The Gemstone spurs under D2's 3,550 peak."},
            {'line': [[86, 99], [82, 98], [77, 95], [70, 97]], 'height': 1550, 'width': 1, 'slope': 3,
             'notes': "The great dune's crest (the signature camera on it)."},
        ],
    },
    'water': {
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': RIM_POLY,
             'notes': "Below the rim: stands for the stars."},
            {'id': 'water:last_water', 'kind': 'pond', 'level': 1320, 'polygon': OASIS,
             'notes': "The Last Water's spring pool (D-23: no river)."},
        ],
    },
    'roads': ROADS,
    'districts': [{'space': s, 'polygon': SPACES_POLY[s]} for s in SPACES_POLY],
    'points': [dict({'id': pid, 'at': at}, **({'facing': f} if f else {})) for pid, at, f in PTS],
    'areas': AREAS,
    'views': VIEWS,
    'actors': ACTORS,
}


def whole(v):
    return int(v + 0.5) if v >= 0 else -int(-v + 0.5)


def round_geometry():
    """Whole cells everywhere but road lines (the studio's rule); half-cell positions above are the drawing's intent,
    rounded here once."""
    for p in SKETCH['points']:
        p['at'] = [whole(c) for c in p['at']]
    for p in SKETCH['heights']['points']:
        p['at'] = [whole(c) for c in p['at']]
    for v in SKETCH['views']:
        v['at'] = [whole(c) for c in v['at']]
        v['look'] = [whole(c) for c in v['look']]
    for c in SKETCH['heights']['cliffs'] + SKETCH['heights']['ridges']:
        c['line'] = [[whole(v) for v in pt] for pt in c['line']]
    for group in (SKETCH['heights']['bands'], SKETCH['districts'], SKETCH['areas'], SKETCH['water']['bodies']):
        for d in group:
            poly = [[whole(c) for c in pt] for pt in d['polygon']]
            out = []
            for pt in poly:
                if not out or out[-1] != pt:
                    out.append(pt)
            if out[0] == out[-1]:
                out.pop()
            d['polygon'] = out


def dump(data, path):
    class Dumper(yaml.SafeDumper):
        pass

    def str_presenter(dumper, value):
        return dumper.represent_scalar('tag:yaml.org,2002:str', value)
    Dumper.add_representer(str, str_presenter)
    text = yaml.dump(data, Dumper=Dumper, sort_keys=False, default_flow_style=None, width=120, allow_unicode=True)
    path.write_text(text)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    SKETCH['heights']['points'] = [dict({'at': [x, y], 'h': h}, **({'notes': n} if n else {}))
                                   for x, y, h, n in POINTS_H + border_points()]
    round_geometry()
    dump(PROJECT, OUT / 'project.yml')
    dump(PLAN, OUT / 'plan.yml')
    dump(SKETCH, OUT / 'sketch.yml')
    print('written', OUT)


if __name__ == '__main__':
    main()
