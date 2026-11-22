#!/usr/bin/env python3
"""D4 Lakeside and Blackfang: the L1 brief (MU-3) in Map Studio's schema, written from the data below (A6, phase 4).

    d4_brief.py        -> devdocs/xeen/briefs/d4/L1/{project,plan,sketch}.yml (then `oymap fmt` and `oymap validate`)

Edit this script, not the YAML. NOTES.md beside the brief is written by hand. Cells [x, y]: x east, y south, 512 units
each; heights in map units above the stars below the rim (0). Nothing here is read by the game.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'devdocs/xeen/briefs/d4/L1'

LAKE_LEVEL = 1056
RIM_NORTH_Y = 24          # the north rim's cliff (the world's edge), as D2/D3's south rim at y 104-106
RIM_EAST_X = 104          # the east rim's cliff, continuing D3's at x 104

# ---------------------------------------------------------------------------------------------- geometry

LAKE = [[57, 57], [61, 55], [66, 55], [71, 56], [76, 57], [79, 59], [84, 60], [90, 60], [95, 59], [98, 61],
        [100, 64], [100, 69], [98, 72], [95, 73], [93, 76], [95, 78], [94, 80], [90, 81], [85, 82], [80, 81],
        [76, 81], [72, 82], [68, 82], [64, 81], [60, 79], [56, 76], [54, 71], [54, 65], [55, 60]]
ISLE = [[67, 66], [70, 64], [74, 64], [77, 66], [78, 69], [76, 72], [73, 74], [70, 73], [67, 71]]
RIM_POLY = [[0, 0], [128, 0], [128, 128], [RIM_EAST_X, 128], [RIM_EAST_X, RIM_NORTH_Y], [0, RIM_NORTH_Y]]

SPACES_POLY = {
    'zone:rim': RIM_POLY,
    'zone:magic_mountain': [[19, 24], [44, 24], [54, 28], [56, 40], [54, 48], [46, 54], [36, 56], [26, 57], [19, 58]],
    'zone:wizard_camp': [[24, 47], [32, 47], [32, 53], [24, 53]],
    'zone:woodcutters_clearing': [[45, 49], [50, 49], [50, 54], [45, 54]],
    'zone:snow_uplands': [[44, 24], [96, 24], [96, 38], [92, 38], [84, 38], [78, 42], [77, 50], [70, 53], [62, 52],
                          [58, 50], [56, 40], [54, 28]],
    'zone:rim_corner': [[96, 24], [104, 24], [104, 58], [98, 60], [96, 44], [96, 38]],
    'zone:blackfang_crag': [[78, 42], [84, 38], [92, 38], [96, 44], [98, 60], [95, 59], [90, 60], [84, 60], [79, 59],
                            [77, 50]],
    'zone:north_shore': [[56, 50], [62, 52], [70, 53], [77, 50], [79, 59], [76, 57], [71, 56], [66, 55], [61, 55],
                         [57, 57], [55, 56]],
    'zone:west_shore': [[46, 54], [54, 48], [56, 50], [55, 56], [55, 60], [54, 65], [54, 71], [56, 76], [60, 79],
                        [60, 82], [56, 84], [50, 80], [46, 70]],
    'zone:forest_of_peril': [[19, 58], [26, 57], [36, 56], [46, 54], [46, 70], [50, 80], [56, 84], [58, 88],
                             [56, 94], [44, 94], [32, 92], [19, 92]],
    'zone:leafpoint_grove': [[39, 58], [45, 58], [45, 64], [39, 64]],
    'zone:ector_clearing': [[31, 69], [37, 69], [37, 74], [31, 74]],
    'zone:west_edge': [[19, 75], [28, 75], [28, 85], [19, 85]],
    'zone:desert_heath': [[19, 92], [32, 92], [44, 94], [56, 94], [60, 97], [62, 102], [80, 100], [84, 101],
                          [84, 109], [19, 109]],
    'zone:lakeside_brow': [[84, 97], [92, 97], [92, 109], [84, 109]],
    'town:lakeside': [[60, 82], [85, 82], [86, 97], [60, 97]],
    'zone:lakeside_square': [[68, 87], [78, 87], [78, 93], [68, 93]],
    'zone:lakeside_waterfront': [[60, 82], [85, 82], [85, 84], [60, 84]],
    'zone:east_shore': [[85, 82], [90, 81], [94, 80], [95, 78], [93, 76], [95, 73], [98, 72], [100, 69], [104, 69],
                        [104, 84], [92, 86], [86, 90], [85, 86]],
    'zone:mirabeth_point': [[92, 73], [97, 73], [97, 78], [92, 78]],
    'zone:rimward_crags': [[92, 86], [104, 84], [104, 109], [92, 109]],
    'zone:falls_lip': [[99, 62], [104, 62], [104, 72], [99, 72]],
    'zone:isle': ISLE,
}

# ---------------------------------------------------------------------------------------------- the plan

def S(id_, name, kind, purpose, **kw):
    d = {'id': id_, 'name': name, 'kind': kind}
    d.update({k: v for k, v in kw.items() if k not in ('purpose',)})
    d['purpose'] = purpose
    return d


SPACES = [
    # ---- the arrivals ----
    S('zone:lakeside_brow', "Lakeside Brow", 'zone', floor=[1750, 2300], where="south, where the road from D3 tops the last rise",
      purpose="Where the party comes in from D3: the road climbs to a brow of heath (2,300) and the lake country opens below: "
              "Lakeside's slate roofs on the shore, the lake beyond with the Isle of Lost Souls, Castle Blackfang on "
              "its crag across the water, Magic Mountain far to the west.",
      safe=True, keep_clear=['spawns']),
    S('zone:west_edge', "The forest road's end", 'zone', floor=1500,
      where="west, the forest road's last stretch from the D5 border",
      purpose="Where the party comes in from D5: the road leaves the desert edge and enters the Forest of Peril; "
              "Magic Mountain's snowy head north over the trees.",
      safe=True, keep_clear=['spawns']),
    # ---- Lakeside ----
    S('town:lakeside', "Lakeside", 'town', floor=1120,
      where="the lake's south shore, a low town of 15 doors round a square and a waterfront",
      purpose="The coven town (WORLD_DESIGN 5.2; A4's d4.yml 4651-4666): before Q-D22 only the guild (the coven's "
              "riddle door into DD-20), the ferry to the Isle (D-12.1, from day one) and Old Gill's shack work; "
              "after it the tavern, smithy, temple, mirror and the houses open. Naomi in the stocks on the square.",
      safe=True, keep_clear=['spawns'], density='medium',
      theme="darkside_town kit (MU-5 board): grey boulder-stone t06 houses under mossy slate for the waterfront and "
            "the poor, t09 ashlar under xlslate for the guild and the temple; the guild's carved double door as two "
            "leaves (t09a03a / t09a03b); grey plank jetty (7trimda, 7trimd, btrima2); MU-2 D4 ground: road pebbles "
            "in town, sand ripples on the beach.",
      buildings=[
          {'id': 'building:lk_guild', 'type': 'house', 'service': 'Lakeside Guild', 'count': 1, 'doors': 1,
           'footprint_cells': [[4, 4]],
           'notes': "4651: the coven's front (water guild). Two storeys of t09 ashlar, a window once per storey "
                    "(texture fit), the carved double door as two leaves with mirrored wing pictures (double doors). "
                    "Its door asks the riddle (q-d22.guild_door); right: the guild and its back stair to DD-20; "
                    "wrong: the trapdoor into DD-20's sewer half."},
          {'id': 'building:lk_tavern', 'type': 'house', 'service': "The Cozy Lil' Tavern", 'count': 1, 'doors': 1,
           'footprint_cells': [[3, 3]],
           'notes': "4652: before q-d22.done its door is a stair to a dust-sheeted shell: \"These stairs once led to "
                    "a tavern, but it was destroyed long ago.\" (dark/aaze0033:1)."},
          {'id': 'building:lk_smithy', 'type': 'house', 'service': 'Lakeside Smithy', 'count': 1, 'doors': 1,
           'footprint_cells': [[3, 3]], 'notes': "4653: the same before liberation (aaze0033:2)."},
          {'id': 'building:lk_temple', 'type': 'house', 'service': 'Temple of Still Waters', 'count': 1, 'doors': 1,
           'footprint_cells': [[4, 3]], 'notes': "4654: doors nailed shut, a broom painted on them, until q-d22.done."},
          {'id': 'building:lk_yachts', 'type': 'house', 'service': 'Lakeside Yachts', 'count': 1, 'doors': 1,
           'footprint_cells': [[3, 2]],
           'notes': "4655: Captain Ferris Gull's ferry to the Isle (route 420, daily, from day one: D-12.1) and "
                    "Lucio's celestial boat to Olympus (route 426, wed and sat, m30.done: D-5.3) from its jetty."},
          {'id': 'building:lk_houses', 'type': 'house', 'service': 'residence', 'count': 10, 'doors': 1,
           'footprint_cells': [[2, 2], [3, 2], [2, 2], [3, 2], [2, 2], [2, 2], [2, 2], [2, 2], [2, 2], [3, 2]],
           'notes': "4657-4666 in index order: Old Gill's Shack (open), The Tannery, Tidewater House, The Gray Manor "
                    "(Sir Malvern), Netmender's House, The Hollow House, Reedcutter's Cottage, The Eel House, Widow "
                    "Marsh's, The Boathouse (Skiff's: the beached boat by it is his)."},
      ]),
    S('zone:lakeside_square', "Lakeside's square", 'zone', part_of='town:lakeside', floor=1120,
      purpose="Flagstones between the guild (west), the smithy (east), the tavern and the temple (south): the Mirror "
              "of Lakeside (4656) and Naomi in the stocks beside it, watching the guild's door.",
      safe=True, keep_clear=['spawns']),
    S('zone:lakeside_waterfront', "The waterfront", 'zone', part_of='town:lakeside', floor=1090,
      purpose="A shingle beach and a lane along the houses' fronts; the ferry jetty of grey planks into the lake; "
              "Skiff's beached boat with its sign \"This boat under repair.\" east of the Boathouse; the sewer "
              "shaft's grate (DD-20) by the jetty's foot.",
      safe=True, keep_clear=['spawns']),
    # ---- the lake ----
    S('water:octopod_lake', "Octopod Lake", 'water',
      purpose="The great lake: shallows and reeds by the shores, dark deep water in the two basins west and east of "
              "the Isle. Octopods live in the deep water only (the lake is the trap); two skerries with a lure each. "
              "It drains east over the rim at the Octopod Falls.",
      population=[{'id': 'pop:octopods', 'actor': 'Xeen Octopod', 'groups': 2, 'placed': True, 'hostile': True,
                   'notes': "E6 west basin: two Octopods 50, alone, in the deep water only."},
                  {'id': 'pop:octopods_east', 'actor': 'Xeen Octopod', 'groups': 3, 'placed': True, 'hostile': True,
                   'notes': "E6 east basin: an Octopod 50 and two Great Octopods 60, round the East Skerry's lamp."}]),
    S('zone:isle', "The Isle of Lost Souls", 'zone', floor=[1100, 1400], relief='uneven',
      purpose="A rocky isle of dead trees and old graves 5 cells off Lakeside's jetty: a jetty and a sign \"Isle of "
              "Lost Souls\" (aaze0022:5) at its south shore, the ferry's landing; up a short path, a ruined round "
              "tower over DD-12's door (two leaves; lost_souls_key, M20).",
      safe=True, keep_clear=['spawns']),
    S('water:outflow', "The Octopod Falls", 'water',
      purpose="The lake's outflow: a short race east from the lake to the rim, where it falls into the stars."),
    S('zone:falls_lip', "The falls' lip", 'zone', part_of='zone:rim_corner', floor=[1056, 1300],
      purpose="Rocks either side of the race where the lake water goes over the rim, a fisherman's chest caught in "
              "them; the bright face's glow above the rim to the north-east (sky).", density='sparse'),
    # ---- the north ----
    S('zone:blackfang_crag', "Castle Blackfang's crag", 'wild', floor=[1100, 3100], relief='uneven',
      purpose="A crag of black rock rising from the lake's north shore, its south face a cliff into the water; on its "
              "top Castle Blackfang (DD-14) in a storm of bats. The towers kit's Darkside stone (hkm3 slate-blue "
              "under a skull frieze, hkm2 black rubble), xtslate cones; one window per storey on each tower. The gate "
              "at the crag's west foot on the north shore never opens (m25.blackfang_gate): the griffin is the only "
              "way in.", empty=True),
    S('zone:north_shore', "The north shore", 'zone', floor=[1080, 1300], relief='slope',
      purpose="A shingle strip and reedy meadow under the uplands from the Snow River's mouth east to Blackfang's "
              "gate: the track, the gatehouse at the crag's foot.", density='sparse'),
    S('zone:snow_uplands', "The Snow River uplands", 'wild', floor=[1300, 2400], relief='uneven',
      purpose="Snowy heath and stony slopes between Magic Mountain and Blackfang's crag up to the north rim: the Snow "
              "Springs under a snowfield at the rim, the Snow River's rapids down a rocky cut to the lake, the vulture "
              "rocs' pinnacles.",
      population=[{'id': 'pop:snow_rocs', 'slot': 2, 'groups': 12, 'per_marker': [1, 3], 'levels': [30, 48],
                   'notes': "Encounter area E2: Vulture Rocs 30, a Roc 38 or Griffin 48 now and then."}]),
    S('zone:rim_corner', "The rim corner", 'wild', floor=[1300, 2200], relief='uneven',
      purpose="The north-east corner behind Blackfang's crag where the two rims meet: the Fountain of Great "
              "Resilience on a ledge (the source's F1 fountain), the glow of the bright face above the rim (sky).",
      density='sparse'),
    # ---- Magic Mountain ----
    S('zone:magic_mountain', "Magic Mountain", 'wild', floor=[1500, 4100], relief='uneven',
      purpose="A massif of grey crags and snow in the north-west, its north face falling over the rim: the wizards' "
              "camp on a shelf of its south side, the Wizard's Seat (a genie lamp), the gargoyles' perches and their "
              "lair (DD-23) in the eastern crags, Ector's woodpile on its wooded south-east slope.",
      population=[{'id': 'pop:mountain_gargoyles', 'slot': 1, 'groups': 13, 'per_marker': [2, 3], 'levels': [30, 45],
                   'notes': "Encounter area E1: Mountain Gargoyles 30, Sentinels 38, an Overlord 45 (Dif 2)."}]),
    S('zone:wizard_camp', "Xanthus and Slibo's camp", 'zone', part_of='zone:magic_mountain', floor=2300,
      purpose="Two wizards' tents, a fire and a stone basin fed by a spring: the Fountain of Great Magic (Xanthus' "
              "fountain, +SP). Slibo (5317) by the tents (Q-C24's real map, Q-D2).",
      safe=True, keep_clear=['spawns']),
    S('zone:woodcutters_clearing', "The woodcutters' clearing", 'zone', part_of='zone:magic_mountain', floor=1900,
      purpose="Stumps and stacked logs on the mountain's south-east slope: Ector's woodpile (q-d21.woodpile); the "
              "goat path on up to the gargoyles' lair.", safe=True, keep_clear=['spawns']),
    # ---- the Forest of Peril ----
    S('zone:forest_of_peril', "The Forest of Peril", 'wild', floor=[1150, 1700], relief='uneven', density='dense',
      purpose="Old dark firs and gnarled oaks from the mountain's foot to the desert edge, quiet but for the "
              "animal traps (the source's \"Animal trap!\"): Leafpoint's grove, Ector's cabin, the forest road from "
              "D5 to Lakeside."),
    S('zone:leafpoint_grove', "Leafpoint's grove", 'zone', part_of='zone:forest_of_peril', floor=1500,
      purpose="A ring of young trees round the oldest tree in Xeen: Leafpoint (5319), who talks (T2-LEAFPOINT, Arch "
              "Druid after q-c15.done).", safe=True, keep_clear=['spawns']),
    S('zone:ector_clearing', "Ector's clearing", 'zone', part_of='zone:forest_of_peril', floor=1450,
      purpose="A log cabin, a chopping block and a sawpit: Ector the Woodsman (5320), who lost his ring (Q-D21).",
      safe=True, keep_clear=['spawns']),
    S('zone:west_shore', "The west shore", 'wild', floor=[1080, 1500], relief='slope', density='medium',
      purpose="Reed beds and alder carr along the lake's west side, the track north to the Snow River bridge: the "
              "obelisk on Gull Knoll, the coven's cauldron in the reeds.",
      population=[{'id': 'pop:reed_witches', 'actor': 'Xeen Coven', 'groups': 1, 'placed': True, 'hostile': True,
                   'notes': "E4b: 6 placed (Witch 32 x4, Coven Witch 40 x2) at the cauldron in the reeds; gone with "
                            "q-d22.done."}]),
    S('zone:desert_heath', "The desert edge", 'wild', floor=[1400, 2000], relief='uneven', density='sparse',
      purpose="Heather, sand and wind-bent pines along the south, where D3's dunes run on: vulture rocs over the "
              "rocks, the Witches' Circle at the forest's edge, a lost wagon.",
      population=[{'id': 'pop:heath_rocs', 'slot': 2, 'groups': 14, 'per_marker': [1, 3], 'levels': [30, 48],
                   'notes': "Encounter area E5: Vulture Rocs 30 (Rocs 38, Griffins 48 rare)."},
                  {'id': 'pop:circle_witches', 'actor': 'Xeen Coven', 'groups': 1, 'placed': True, 'hostile': True,
                   'notes': "E4a: 8 placed (Witch 32 x5, Coven Witch 40 x2, Coven Mother 50) at the Witches' Circle; "
                            "gone with q-d22.done."}]),
    S('zone:east_shore', "The east shore", 'zone', floor=[1080, 1400], relief='slope', density='sparse',
      purpose="Shingle and turf from Lakeside to the falls: the shore path to Mirabeth Point, the cairn of five "
              "stones (Q-C24) on the way.", safe=True),
    S('zone:mirabeth_point', "Mirabeth Point", 'zone', part_of='zone:east_shore', floor=1150,
      purpose="A low headland with a weathered statue of a mermaid looking west over the water (the Clouds mermaid "
              "Mirabeth, X3); a sign \"Mirabeth Point\" (aaze0022:1).", safe=True, keep_clear=['spawns']),
    S('zone:rimward_crags', "The Rimward crags", 'wild', floor=[1600, 2400], relief='uneven', density='sparse',
      purpose="Broken crags between the road and the east rim (D3's Wrath shoulder running on north): rocs' "
              "perches, the fallen roc-hunter; the first fight from D3.",
      population=[{'id': 'pop:rimward_rocs', 'slot': 2, 'groups': 8, 'per_marker': [1, 3], 'levels': [30, 48],
                   'notes': "Encounter area E3: Vulture Rocs 30."}]),
    S('zone:rim', "The world rim", 'wild', floor=0,
      purpose="North and east the land ends in a cliff; below, the stars (water at 0 stands for them). The bright "
              "face's glow above the north-east rim is the sky's (concept art only; no plan depends on it).",
      empty=True),
    S('water:rim_sea', "Below the rim", 'water', purpose="The stars below the world's edge (water at 0)."),
    S('water:snow_river', "The Snow River", 'water',
      purpose="Rises at the Snow Springs under the snowfield at the north rim, runs down its rapids through a rocky "
              "cut and enters the lake's north-west bay (D-23: it rises and falls inside the map)."),
    S('water:snow_springs', "The Snow Springs", 'water', part_of='zone:snow_uplands',
      purpose="A small black tarn under the snowfield, the river's source."),
    # ---- junctions and edges ----
    S('junction:well_fork', "Well Fork", 'junction', signpost=True,
      purpose="North-west: Lakeside. East: the shore path to Mirabeth Point. South: the road to Sandcaster (D3)."),
    S('junction:ector_fork', "Ector's Fork", 'junction', signpost=True,
      purpose="East: Lakeside. West: the desert road (D5). North: the forest lane to Ector, Leafpoint and Magic "
              "Mountain."),
    S('junction:snow_bridge', "Snow River bridge", 'junction', signpost=True,
      purpose="A timber bridge over the Snow River's last rapids: south to Lakeside, east to Castle Blackfang, "
              "north up the river to the springs and the uplands."),
    S('edge:south_end', "South edge", 'road', part_of='zone:lakeside_brow', purpose="Where the road leaves for D3."),
    S('edge:west_end', "West edge", 'road', part_of='zone:west_edge', purpose="Where the road leaves for D5."),
]

LINKS = [
    {'id': 'link:sandcaster_road', 'from': 'edge:south_end', 'to': 'junction:well_fork', 'kind': 'road', 'rise': -650,
     'purpose': "travel: D3; over the brow and down to the shore"},
    {'id': 'link:town_road_east', 'from': 'junction:well_fork', 'to': 'zone:lakeside_square', 'kind': 'road',
     'purpose': "into Lakeside past the smithy"},
    {'id': 'link:desert_road', 'from': 'edge:west_end', 'to': 'junction:ector_fork', 'kind': 'road',
     'purpose': "travel: D5, the forest road"},
    {'id': 'link:forest_road', 'from': 'junction:ector_fork', 'to': 'zone:lakeside_square', 'kind': 'road',
     'purpose': "through the Forest of Peril, past the Witches' Circle, into Lakeside by the guild"},
    {'id': 'link:shore_path', 'from': 'junction:well_fork', 'to': 'zone:mirabeth_point', 'kind': 'path',
     'purpose': "past the cairn to the statue"},
    {'id': 'link:west_shore_track', 'from': 'zone:lakeside_waterfront', 'to': 'junction:snow_bridge', 'kind': 'path',
     'purpose': "up the west shore past the cauldron reeds and Gull Knoll"},
    {'id': 'link:north_shore_track', 'from': 'junction:snow_bridge', 'to': 'zone:north_shore', 'kind': 'path',
     'purpose': "east under the uplands to Blackfang's gate"},
    {'id': 'link:snow_track', 'from': 'junction:snow_bridge', 'to': 'zone:rim_corner', 'kind': 'path', 'rise': 1100,
     'purpose': "up the river's west bank past the rapids to the springs, then east along the rim to the fountain"},
    {'id': 'link:forest_lane', 'from': 'junction:ector_fork', 'to': 'zone:leafpoint_grove', 'kind': 'path',
     'purpose': "north past Ector's cabin to Leafpoint"},
    {'id': 'link:camp_lane', 'from': 'link:forest_lane', 'to': 'zone:wizard_camp', 'kind': 'path', 'rise': 800,
     'purpose': "switchbacks up to the wizards' shelf"},
    {'id': 'link:seat_path', 'from': 'zone:wizard_camp', 'to': 'poi:genie_seat', 'kind': 'path', 'rise': 700},
    {'id': 'link:woodpile_lane', 'from': 'zone:leafpoint_grove', 'to': 'zone:woodcutters_clearing', 'kind': 'path',
     'rise': 400},
    {'id': 'link:lair_path', 'from': 'zone:woodcutters_clearing', 'to': 'entrance:dd23_lair', 'kind': 'path',
     'rise': 800, 'notes': "a goat path into the gargoyles' crags"},
]

ENTRANCES = [
    {'id': 'entrance:south_road', 'space': 'zone:lakeside_brow', 'kind': 'both', 'neighbour': 'edge:south',
     'facing': 'n', 'how': "The road from Sandcaster (D3) at x 88, on the brow above the lake."},
    {'id': 'entrance:west_road', 'space': 'zone:west_edge', 'kind': 'both', 'neighbour': 'edge:west', 'facing': 'e',
     'how': "The desert road from D5 at y 80, where the forest begins."},
    {'id': 'entrance:lakeside_square', 'space': 'zone:lakeside_square', 'kind': 'arrival',
     'neighbour': 'mirror:darkside', 'how': "Town Portal and the mirror (4656, qbit 119010; open after q-d22.done)."},
    {'id': 'entrance:lakeside_dock', 'space': 'zone:lakeside_waterfront', 'kind': 'arrival',
     'neighbours': ['boat:isle_return', 'stable:castleview', 'stable:sandcaster'],
     'how': "The jetty's foot (A4's lakeside_dock): the caravans from Castleview and Sandcaster (routes 414, 417), "
            "the ferry back from the Isle."},
    {'id': 'entrance:isle_landing', 'space': 'zone:isle', 'kind': 'arrival', 'neighbour': 'boat:isle',
     'how': "The Isle's jetty (A4's isle_landing): Ferris Gull's ferry, route 420."},
    {'id': 'entrance:dd12_door', 'space': 'zone:isle', 'kind': 'both', 'neighbour': 'door:dd12', 'facing': 's',
     'condition': {'item': 'lost_souls_key'},
     'how': "The ruined tower's door: two iron-bound leaves (double doors), \"Enter the Isle of Lost Souls Dungeon?\" "
            "(aaze0022:0) with the key; without it, locked (A8's DD-12, M20's key)."},
    {'id': 'entrance:dd20_guild', 'space': 'zone:lakeside_square', 'kind': 'both', 'neighbour': 'door:dd20_guild',
     'facing': 'e',
     'how': "The guild's double door (house 4651): q-d22.guild_door asks the riddle; right: the guild, its back "
            "stair down to the coven's hall; wrong: the trapdoor into the sewer half (the map's move)."},
    {'id': 'entrance:dd20_shaft', 'space': 'zone:lakeside_waterfront', 'kind': 'both', 'neighbour': 'door:dd20_sewer',
     'facing': 'n',
     'how': "A grated shaft by the jetty's foot: \"Climb down to the sewer?\" (aaze0033:3), the entrance preset "
            "(D-24); sealed with a line until A8's DD-20 is installed."},
    {'id': 'entrance:dd23_lair', 'space': 'zone:magic_mountain', 'kind': 'both', 'neighbour': 'door:dd23',
     'facing': 's',
     'how': "A cave mouth under the gargoyles' perches: q-d15.lair_door's line on approach, then the map's own "
            "\"Enter?\". An open cave mouth, no door leaves."},
    {'id': 'entrance:blackfang_gate', 'space': 'zone:north_shore', 'kind': 'exit',
     'how': "The great double gate in the gatehouse at the crag's foot, two leaves of black oak and iron: "
            "m25.blackfang_gate, \"There seems to be no way in.\" (aaze0021:3). Never opens."},
]

GOALS = [
    {'id': 'goal:coven', 'space': 'zone:lakeside_square', 'kind': 'use',
     'what': "Answer the guild's riddle (or have Naomi say the word), free the five prisoners and break the coven "
             "in DD-20, or join it (Q-D22).", 'story': 'Q-D22'},
    {'id': 'goal:lost_souls', 'space': 'zone:isle', 'kind': 'reach',
     'what': "Take the ferry to the Isle and open DD-12 with Megan's key (M20, M24).", 'story': 'M20'},
    {'id': 'goal:woodpile', 'space': 'zone:woodcutters_clearing', 'kind': 'take',
     'what': "Find Ector's ring in the woodpile on Magic Mountain (Q-D21).", 'story': 'Q-D21'},
    {'id': 'goal:lair', 'space': 'zone:magic_mountain', 'kind': 'reach',
     'what': "Destroy the gargoyle lair (DD-23) for Caleb (Q-D15).", 'story': 'Q-D15'},
    {'id': 'goal:cairn', 'space': 'zone:east_shore', 'kind': 'use',
     'what': "Dig two paces north of the five-stone cairn with Jethro's real map (Q-C24), or sell the map to Slibo.",
     'story': 'Q-C24'},
    {'id': 'goal:obelisk', 'space': 'zone:west_shore', 'kind': 'use',
     'what': "Read the fourth Darkside word (obelisks.d4).", 'story': 'obelisks'},
]


def P(id_, space, kind, behaviour, **kw):
    d = {'id': id_, 'space': space, 'kind': kind}
    d.update(kw)
    d['behaviour'] = behaviour
    return d


POIS = [
    P('poi:obelisk', 'zone:west_shore', 'obelisk',
      "obelisks.d4: the fourth of six words (autonote dark_4, 115053).", rule='native:obelisk',
      notes="On Gull Knoll at the town's west end above the reeds (A3's autonote: \"Obelisk by Lakeside\"), the lake and the Isle in view."),
    P('poi:fountain_magic', 'zone:wizard_camp', 'fountain',
      "Xanthus' Fountain of Great Magic (aaze0017:4-6): +SP, temporary (the source's +1,000 rescaled), daily.",
      uses={'times': 1, 'per': 'character', 'reset': 'daily'}),
    P('poi:warding_well', 'zone:east_shore', 'well',
      "The Fountain of Magic Resistance (aaze0022:2-4): +5 Mind and Body resistance, permanent, once per character "
      "(D-4's +5 rule; the source's +50 rescaled). The map's permanent device.",
      uses={'times': 1, 'per': 'character', 'reset': 'never'}),
    P('poi:fountain_resilience', 'zone:rim_corner', 'fountain',
      "The Fountain of Great Resilience (aaze0021:0-2): +HP, temporary, daily; on a ledge where the rims meet.",
      uses={'times': 1, 'per': 'character', 'reset': 'daily'}),
    P('poi:woodpile', 'zone:woodcutters_clearing', 'device',
      "q-d21.woodpile: \"Woodpile\" (aaze0017:9); searching it gives Ector's ring once.",
      uses={'times': 1, 'per': 'party', 'reset': 'never'}),
    P('poi:cairn', 'zone:east_shore', 'device',
      "q-c24.cairn: a cairn of five stones; with Jethro's real map the party digs up Slibo's cache two paces north.",
      uses={'times': 1, 'per': 'party', 'reset': 'never'}),
    P('poi:mirabeth', 'zone:mirabeth_point', 'statue',
      "Mirabeth Point: the mermaid's statue and its sign (aaze0022:1). Clicking reads the sign."),
    P('poi:genie_seat', 'zone:magic_mountain', 'device', reached_by='off_road',
      behaviour="A genie's lamp on the Wizard's Seat, a ledge above the camp (genie lamps, Q-D27): a wish choice; "
                "greed is punished."),
    P('poi:genie_skerry', 'water:octopod_lake', 'device', reached_by='water',
      behaviour="A second lamp glinting on the East Skerry in the deep east basin: only by water walking or flight, "
                "past the octopods (the lake's lure)."),
    P('poi:witches_circle', 'zone:desert_heath', 'device',
      "The Witches' Circle: standing stones round a cauldron; three skulls on stakes speak the potion recipes "
      "(aaze0033:12-14) when clicked."),
    P('poi:reed_cauldron', 'zone:west_shore', 'device',
      "The coven's cauldron in the reeds: drink? A random effect (spell points or poison), once a day.",
      uses={'times': 1, 'per': 'character', 'reset': 'daily'}),
    P('poi:beached_boat', 'zone:lakeside_waterfront', 'chest',
      "Skiff's beached boat: \"There is a sign here that reads 'This boat under repair.'\" (aaze0033:18); "
      "\"Search the boat?\" (:21); yes: its locker (a chest) and \"The boat sinks into the water, but not before you "
      "recover its treasures.\" (:22): the boat model hides (D-12.1)."),
    P('poi:roc_nest', 'zone:snow_uplands', 'chest',
      "A vulture roc's nest on a pinnacle, with a lost courier's satchel in the bones (a chest)."),
    P('poi:frozen_pilgrim', 'zone:snow_uplands', 'chest',
      "A pilgrim frozen kneeling by the Snow Springs: his pack (a chest)."),
    P('poi:skerry_strongbox', 'water:octopod_lake', 'chest', reached_by='water',
      behaviour="A drowned smuggler's strongbox wedged on the West Skerry: only by water walking or flight (a lure)."),
    P('poi:roc_hunter', 'zone:rimward_crags', 'chest',
      "A roc-hunter who fell among the crags: his pack and broken crossbow (a chest)."),
    P('poi:heath_wagon', 'zone:desert_heath', 'chest',
      "A Sandcaster wagon that tried the heath track: its strongbox under the sand (a chest)."),
    P('poi:circle_chest', 'zone:desert_heath', 'chest',
      "The coven's offering chest at the foot of the circle's altar stone."),
    P('poi:hunters_hide', 'zone:forest_of_peril', 'chest',
      "An old hunters' hide in the western firs, its owner's trap-line long sprung: a locked trunk (a chest)."),
    P('poi:falls_chest', 'zone:falls_lip', 'chest',
      "A fisherman's sea chest caught in the rocks above the falls, where the lake would have taken it over the rim."),
    P('poi:gibbet', 'zone:desert_heath', 'chest',
      "Gallows Knoll above Lakeside's south road: the coven's gibbet, and in its cage a dead thief's purse (a chest)."),
    P('poi:isle_boat', 'zone:isle', 'device',
      "Ferris Gull's mate waits at the Isle's jetty: \"Back to Lakeside?\" (A4's line): the move to lakeside_dock."),
    P('poi:mirror', 'zone:lakeside_square', 'story_device',
      "The Mirror of Lakeside (4656): before q-d22.done \"The mirror shows a witch's face, which does not move when you "
      "do.\" (A4); after it the Darkside mirror network (and Kalindra's stage 4)."),
    P('poi:naomi', 'zone:lakeside_square', 'npc',
      "Naomi (5318) in the stocks, facing the guild's door: Q-D22's giver; she says the guild's word. Not a point of "
      "interest (D-23 (1))."),
    P('poi:slibo', 'zone:wizard_camp', 'npc', "Slibo (5317), Wizard of Magic Mountain: Q-C24, Q-D2."),
    P('poi:leafpoint', 'zone:leafpoint_grove', 'npc',
      "Leafpoint (5319), the oldest tree in Xeen, talks (T2-LEAFPOINT; aaze0018:5-11). See the open question on how a "
      "tree talks."),
    P('poi:ector', 'zone:ector_clearing', 'npc', "Ector the Woodsman (5320) by his cabin: Q-D21 (aaze0018:12-16)."),
    P('poi:animal_trap', 'zone:forest_of_peril', 'trap', count=2,
      behaviour="\"Animal trap!\" (aaze0017:10, aaze0018:17): a sprung trap on the forest lanes, damage once. Hazards, "
                "not counted as points of interest."),
    P('poi:signposts', 'junction:well_fork', 'signpost', count=3,
      spaces=['junction:well_fork', 'junction:ector_fork', 'junction:snow_bridge'],
      behaviour="Signposts at the forks (the source's \"North / <- Tower\" style, aaze0018:4)."),
]
for p in POIS:
    if 'spaces' in p:
        del p['space']

LANDMARKS = [
    {'id': 'landmark:blackfang', 'space': 'zone:blackfang_crag',
     'what': "Castle Blackfang on its black crag over the lake: dark slate towers with cones, one lit window per "
             "storey, a storm of bats wheeling round the keep",
     'seen_from': ['zone:lakeside_brow', 'town:lakeside', 'zone:isle', 'zone:west_shore', 'zone:snow_uplands',
                   'zone:east_shore']},
    {'id': 'landmark:isle', 'space': 'zone:isle',
     'what': "The Isle of Lost Souls: dead trees, graves and a ruined round tower on a rock in the lake",
     'seen_from': ['town:lakeside', 'zone:lakeside_brow', 'zone:west_shore', 'zone:east_shore']},
    {'id': 'landmark:magic_mountain', 'space': 'zone:magic_mountain',
     'what': "Magic Mountain: grey crags and snow to 4,100, gargoyles on its perches",
     'seen_from': ['zone:west_edge', 'zone:forest_of_peril', 'zone:lakeside_brow', 'zone:west_shore']},
    {'id': 'landmark:octopod_falls', 'space': 'zone:falls_lip',
     'what': "The lake pouring over the east rim into the stars",
     'seen_from': ['zone:east_shore', 'zone:mirabeth_point']},
    {'id': 'landmark:rapids', 'space': 'zone:snow_uplands',
     'what': "The Snow River Rapids: white water down a rocky cut from the snowfield",
     'seen_from': ['zone:north_shore', 'zone:west_shore']},
]

SIGHTLINES = [
    {'id': 'view:arrival', 'from': 'entrance:south_road', 'to': ['town:lakeside', 'landmark:isle',
                                                                 'landmark:blackfang', 'landmark:magic_mountain'],
     'what': "Arrival from D3: the road tops the brow and the lake country opens: Lakeside's roofs below on the "
             "shore, the lake with the Isle, Castle Blackfang on its crag across the water, Magic Mountain west."},
    {'id': 'view:signature', 'from': 'zone:lakeside_waterfront', 'to': ['landmark:isle', 'landmark:blackfang'],
     'what': "The signature view from the ferry jetty's end: the Isle of Lost Souls ahead with its ruined tower, "
             "and beyond the water Castle Blackfang on its black crag in the storm of bats; the rapids and the "
             "snowfield far left; the north-east rim's glow (sky)."},
]

STATES = [
    {'id': 'state:coven_rules', 'condition': {'not': {'qbit': 'coven_broken'}},
     'locks': ['building:lk_tavern', 'building:lk_smithy', 'building:lk_temple', 'building:lk_houses'],
     'atmosphere': "Shutters closed, cauldrons painted on windows, Naomi in the stocks; the witches' two camps "
                   "(14 placed) by the forest road and in the reeds.",
     'notes': "A4's closed texts; Old Gill's Shack (lk_houses#1) and the ferry stay open (D-12.1)."},
    {'id': 'state:coven_broken', 'condition': {'qbit': 'coven_broken'},
     'opens': ['building:lk_tavern', 'building:lk_smithy', 'building:lk_temple', 'building:lk_houses'],
     'effects': ["The witches' two camps are gone (their placed groups hidden at load).", "Naomi leaves the stocks."]},
    {'id': 'state:lucio', 'condition': {'qbit': 'lucio_open'},
     'effects': ["Lucio's celestial boat at the ferry jetty twice a week (route 426, D-5.3)."]},
]

HEIGHT_BANDS = [
    {'id': 'band:rim_sea', 'range': [0, 0], 'spaces': ['zone:rim', 'water:rim_sea']},
    {'id': 'band:shore', 'range': [1056, 1500],
     'spaces': ['town:lakeside', 'zone:north_shore', 'zone:east_shore', 'zone:isle', 'water:octopod_lake'],
     'partly': ['zone:west_shore'],
     'notes': "The lake at 1,056; Lakeside 1,090-1,150; the Isle to 1,400."},
    {'id': 'band:forest', 'range': [1150, 1750], 'spaces': ['zone:forest_of_peril', 'zone:west_edge'],
     'partly': ['zone:west_shore']},
    {'id': 'band:heath', 'range': [1250, 2600], 'spaces': ['zone:desert_heath', 'zone:lakeside_brow'],
     'notes': "D3's desert-edge dunes and the Lakeside road (1,750 at the edge) run on into D4."},
    {'id': 'band:uplands', 'range': [1300, 2600], 'spaces': ['zone:snow_uplands', 'zone:rim_corner',
                                                             'zone:rimward_crags']},
    {'id': 'band:crag', 'range': [1100, 3100], 'spaces': ['zone:blackfang_crag']},
    {'id': 'band:peaks', 'range': [1500, 4100], 'spaces': ['zone:magic_mountain']},
]

PLAN = {
    'format': 0,
    'level': 'L1',
    'pitch': "Darkside's north-east corner, where the world ends on two sides. A great lake fills the middle: Octopod "
             "Lake, dark and deep, with the Isle of Lost Souls and its ruined tower a short row off the shore. On its "
             "south shore lies Lakeside, a low town of grey stone and slate under the coven's rule; north across the "
             "water Castle Blackfang crowns a black crag in a storm of bats, and the Snow River comes down its rapids "
             "from a snowfield at the rim. West, Magic Mountain lifts its crags and snow over the Forest of Peril, "
             "with two wizards camped on its shoulder and gargoyles on its perches. The lake drains east over the "
             "rim into the stars; above the north-east rim stands the glow of the bright face.",
    'purpose': "Act IV's wilderness map (party 35-38): the Isle and DD-12 (M20, M24), the coven and Lakeside's "
               "liberation (Q-D22, DD-20; Warlock if joined), Castle Blackfang's sealed gate (M25: the griffin is the "
               "only way in), the gargoyle lair (Q-D15, DD-23), Ector's ring (Q-D21), Slibo and the real map (Q-C24), "
               "Leafpoint (T2-LEAFPOINT), the fourth Darkside obelisk, Lucio's boat after M30.",
    'mood': "Cold amber light on still dark water; slate roofs and closed shutters; reeds hissing; the far shriek of "
            "bats over Blackfang; snow and wind on the uplands; the falls' roar at the rim.",
    'datum': 'water:rim_sea',
    'spaces': SPACES,
    'links': LINKS,
    'entrances': ENTRANCES,
    'critical_path': ['edge:south_end', 'junction:well_fork', 'zone:lakeside_square', 'zone:lakeside_waterfront',
                      'zone:isle'],
    'goals': GOALS,
    'points_of_interest': POIS,
    'landmarks': LANDMARKS,
    'sightlines': SIGHTLINES,
    'height_bands': HEIGHT_BANDS,
    'states': STATES,
    'landform': {
        'relief': "A desert-edge heath along the south at 1,500-1,900 (D3's dunes and the Lakeside road run on), "
                  "falling north to the lake at 1,056; Lakeside on its south shore at 1,100-1,150; the Forest of "
                  "Peril in the west at 1,200-1,700 under Magic Mountain (to 4,100); the Snow River uplands "
                  "(1,300-2,400) and the snowfield along the north rim; Blackfang's crag (3,100) on the north shore; "
                  "the Rimward crags (to 2,400) between the road and the east rim. Inside the playable box the land "
                  "spans about 1,060-4,100.",
        'height_range': [1056, 4100],
        'water': "Octopod Lake (about 1,100 cells, level 1,056) with the Isle; the Snow River (about 30 cells, rapids); "
                 "the outflow race and falls (4 cells); the Snow Springs tarn.",
        'water_share': 0.16,
        'caps': [{'kind': 'snow', 'share': 0.08, 'where': "the uplands north of y 36 and Magic Mountain's head"},
                 {'kind': 'bare rock', 'share': 0.07, 'where': "Magic Mountain's crags, Blackfang's crag, the rim "
                                                                 "cliffs"},
                 {'kind': 'sand', 'share': 0.06, 'where': "the desert edge and the beaches"}],
        'rim': {'notes': "The world rim along the whole north (y 24) and east (x 104): a cliff of 1,100-4,000 down to "
                         "the stars; the lake falls over the east rim at y 67. South and west the land runs to the "
                         "map edge; the roads run out to it."},
    },
    'atmosphere': "Sky xeendark1 (xeen_darkside_day; A3's Lua switches to xeendark2/3 at M17/M27); occasional mist "
                  "on the lake; light snow possible on the uplands only (no map weather by default); music 41. "
                  "Lapping water, reeds and gulls at the shore; bats' shrieks near Blackfang; wind on the mountain; "
                  "the falls at the rim.",
    'sketch': {'file': 'sketch.yml', 'grid': 512},
    'totals': {'hostiles_at_load': 120, 'encounter_areas': 6, 'spawn_markers': 47, 'outdoor_chests': 10,
               'points_of_interest': 35, 'dungeon_entrances': 4},
    'notes': "MU-3 for the phase 4 review (A6, 2026-11-20). Source geography: Darkside E1 (Magic Mountain, the "
             "wizards' camp, the woodpile), E2 (the Forest of Peril, Leafpoint, Ector), F1 (Snow River Rapids, Castle "
             "Blackfang, the gargoyles, the resilience fountain), F2 (Lakeside's gate, the Isle, Octopod Lake, "
             "Mirabeth Point, the magic resistance fountain) (MM5_DARKSIDE_CONTENT 4; dark/aaze0017, 0018, 0021, "
             "0022, 0033). Written by level_generation/xeen_art/phase4/d4_brief.py; board "
             "level_generation/xeen_art/phase4/d4/board_d4.png. totals.points_of_interest is the render's census "
             "(measure.json).",
}

# ---------------------------------------------------------------------------------------------- project

PROJECT = {
    'format': 0,
    'id': 'xeen_d4',
    'name': 'Lakeside and Blackfang',
    'world': 'xeen',
    'kind': 'outdoor',
    'profile': 'odm',
    'map_code': 'D4',
    'units': {'plan_grid': 512},
    'extent': {'terrain_cells': 128},
    'map_stats': {
        'id': 9111,
        'encounter_chance': 10,
        'treasure_level': 4,
        'trap_dice': 5,
        'perception_difficulty': 5,
        'refill_days': 672,
        'music': 41,
        'environment': 'forest',
        'lock_difficulty': 10,
        'slots': [
            {'monster': 'Xeen Mountain Gargoyle', 'tier': 2, 'per_marker': [2, 3], 'weight': 30},
            {'monster': 'Xeen Roc', 'tier': 1, 'per_marker': [1, 3], 'weight': 55},
            {'monster': 'Xeen Coven', 'tier': 1, 'per_marker': [2, 3], 'weight': 15},
        ],
    },
    'neighbours': [
        {'id': 'edge:south', 'to': 'xeen_d3.odm', 'kind': 'edge', 'side': 'south', 'days': 5, 'arrival_side': 'north',
         'approach': "The Lakeside road from D3's north edge at x 88 (D-28), over the brow and down to the shore.",
         'notes': "D3 Sandcaster (installed). D3's north edge arrives at its (88, 20) facing south; D4's south arrival "
                  "is entrance:south_road (88, 105) facing north. D4's south rim continues D3's north-edge spans and "
                  "heights cell for cell (D-28 (6)). A2 writes the travel row when both are installed."},
        {'id': 'edge:west', 'to': 'xeen_d5.odm', 'kind': 'edge', 'side': 'west', 'days': 5, 'arrival_side': 'east',
         'listed_only': True,
         'approach': "The desert road from D5's east edge at y 80 into the Forest of Peril.",
         'notes': "D5 Desert of Doom (A6, phase 5, not planned): proposed crossing y 80, a level valley at 1,500 "
                  "(the west rim's span 72-88); D5 aligns to it. Sealed by a sign at the road's end until D5 is "
                  "installed."},
        {'id': 'boat:isle', 'to': 'xeen_d4.odm', 'kind': 'boat', 'service': 4655, 'arrival': 'isle_landing',
         'schedule': {'per_week': 7, 'weekdays': ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']},
         'notes': "Lakeside Yachts (4655), Captain Ferris Gull: route 420 to the Isle's landing, daily from day one "
                  "(D-12.1)."},
        {'id': 'boat:isle_return', 'to': 'xeen_d4.odm', 'kind': 'scripted', 'arrival': 'lakeside_dock',
         'notes': "The ferry back: a click at the Isle's jetty moves the party to lakeside_dock (A4's line; a map "
                  "event, no house)."},
        {'id': 'boat:lucio', 'to': 'xeen_d7.blv', 'kind': 'boat', 'service': 4655,
         'schedule': {'per_week': 2, 'weekdays': ['wed', 'sat']}, 'condition': {'qbit': 'lucio_open'},
         'arrival': 'olympus_dock',
         'notes': "D-5.3: Lucio's slot on the ferry jetty, route 426 to Olympus, m30.done."},
        {'id': 'stable:castleview', 'to': 'xeen_d1.odm', 'kind': 'stable', 'listed_only': True,
         'notes': "Kramer's caravans from Castleview (route 414, mon/thu) land at lakeside_dock; Lakeside has no "
                  "caravan house (A4's d4.yml)."},
        {'id': 'stable:sandcaster', 'to': 'xeen_d3.odm', 'kind': 'stable', 'listed_only': True,
         'notes': "Sandcaster Caravans (route 417, sun) land at lakeside_dock."},
        {'id': 'mirror:darkside', 'to': 'mirror', 'kind': 'mirror',
         'notes': "The Mirror of Lakeside (house 4656, a thing on the square): opens with q-d22.done (and Kalindra's "
                  "stage 4, A3's mirror helper), qbit 119010, arrival lakeside_square."},
        {'id': 'door:dd12', 'to': 'xeen_dd12.blv', 'kind': 'door', 'condition': {'item': 'lost_souls_key'},
         'arrival_hint': "Inside the ruined tower's door, the entrance hall (A8's m24.arrival).",
         'notes': "DD-12 Dungeon of Lost Souls (A8): the Isle's only gate (D-12.1). Double-winged door: two leaves "
                  "with mirrored wing pictures."},
        {'id': 'door:dd20_guild', 'to': 'xeen_dd20.blv', 'kind': 'door',
         'arrival_hint': "The coven's hall at the foot of the guild's back stair (right answer); the sewer half "
                         "under the trapdoor (wrong answer). A8 gives both inside points.",
         'notes': "DD-20 Lakeside Coven and Sewer (A8): through the guild (4651), A3's q-d22.guild_door / "
                  "guild_right / guild_wrong. The guild's front is a carved double door: two leaves."},
        {'id': 'door:dd20_sewer', 'to': 'xeen_dd20.blv', 'kind': 'door', 'listed_only': True,
         'arrival_hint': "At the foot of the shaft's ladder in the sewer half.",
         'notes': "The source's \"Climb down to the sewer?\" (aaze0033:3): a second way into DD-20's sewer half, "
                  "open from day one (see the open question)."},
        {'id': 'door:dd23', 'to': 'xeen_dd23.blv', 'kind': 'door',
         'arrival_hint': "Just inside the cave mouth, facing in.",
         'notes': "DD-23 Gargoyle Lair (S, Q-D15): a cave mouth in Magic Mountain's eastern crags under the perches "
                  "(A3's q-d15.lair_door). No door leaves; if A8 or A7 gives it a door, two leaves."},
        {'id': 'scripted:blackfang', 'to': 'xeen_dd14.blv', 'kind': 'scripted', 'listed_only': True,
         'notes': "DD-14 Castle Blackfang (A8): the griffin flight from D6 (A3's m25.flight) lands on its walls; on "
                  "D4 only the sealed gate (m25.blackfang_gate) and the castle's outside."},
    ],
    'qbits': {
        'coven_broken': 113441,       # q-d22.done (A3)
        'coven_joined': 113449,       # q-d22.joined: the coven is peaceful to members
        'riddle_answered': 113442,    # q-d22.riddle_answered
        'woodpile_found': 113421,     # q-d21.found
        'cache_dug': 112484,          # q-c24.cache_dug
        'obelisk_dark_4': 115053,     # obelisks.d4
        'lucio_open': 111600,         # m30.done
        'mirror_lakeside': 119010,
    },
    'items': {'lost_souls_key': 12344, 'real_treasure_map': 12356, 'ectors_ring': 12522},
    'rules': {'weather': 'none', 'respawn': 'entrance:lakeside_square',
              'town_portal_anchor': 'entrance:lakeside_square'},
    'notes': "D4 Lakeside and Blackfang, MU-3 plan for the phase 4 review (A6, 2026-11-20). No geometry until a "
             "decider has approved the board. Plan: plan.yml; to-scale layout: sketch.yml; NOTES.md; drawings and "
             "board: level_generation/xeen_art/phase4/d4/. Sky xeendark1. Written by "
             "level_generation/xeen_art/phase4/d4_brief.py.",
}

# ---------------------------------------------------------------------------------------------- sketch

# key heights: [x, y, h, note]
POINTS_H = [
    # the south: D3's spans continue (heath 1,500-1,900, the road 1,750, the Wrath shoulder 1,900-2,400)
    [88, 108, 1760, "the road at the D3 edge (D3's bed 1,760)"],
    [88, 105, 2050, "the D3 arrival, climbing"], [88, 102, 2300, "Lakeside Brow: the lake country opens below"],
    [87, 99, 1950, None], [86, 97, 1650, None], [86, 95, 1450, "Well Fork"], [84, 92, 1180, None],
    [81, 103, 2150, "the brow's west shoulder"], [94, 102, 2300, None],
    [80, 106, 1750, "D3's border here 1,700-1,760"], [74, 104, 2000, "Gallows Knoll"], [72, 105, 1700, None], [60, 105, 1600, None],
    [46, 105, 1500, "D3's border here 1,350-1,500"], [34, 105, 1400, None],
    [24, 105, 1300, "D3's border here 1,200-1,300 (its crags stand west of x 16)"], [21, 100, 1450, None],
    [52, 99, 1650, "the heath wagon"], [40, 98, 1600, None], [30, 95, 1550, None], [62, 100, 1750, None],
    [98, 92, 2000, None], [100, 99, 2350, "the Rimward crags"], [97, 106, 1950, "D3's border here 1,880-1,980"],
    [101, 106, 1750, None], [101, 88, 1900, None],
    [95, 86, 1500, None],
    # Lakeside and the shores
    [72, 90, 1120, "Lakeside's square"], [64, 89, 1130, None], [80, 89, 1140, None], [72, 95, 1160, None],
    [62, 95, 1200, None], [82, 95, 1220, None], [90, 84, 1150, "the cairn"], [94.5, 75.5, 1150, "Mirabeth Point"],
    [97, 82, 1300, None], [101, 75, 1500, None], [101, 66, 1150, "the falls' race"], [102, 60, 1700, None],
    # the isle
    [72, 68.5, 1400, "the Isle's tower knoll"], [70, 70.5, 1250, None], [74.5, 70, 1250, None],
    [72, 72.5, 1120, "the Isle's jetty"], [68.5, 68, 1180, None], [75.5, 67, 1200, None],
    # skerries
    [61, 70, 1130, "the West Skerry"], [89, 70, 1140, "the East Skerry"],
    # west shore and the forest
    [53, 58, 1350, None], [57, 80.5, 1180, "Gull Knoll: the obelisk"], [52, 66, 1200, None], [53, 68.5, 1100, "the cauldron reeds"],
    [57, 81, 1100, None], [50, 84, 1300, None], [50, 90, 1450, "the Witches' Circle"],
    [24, 80, 1500, "the D5 arrival"], [36, 81, 1450, "Ector's Fork"], [44, 83, 1350, None],
    [34, 71.5, 1450, "Ector's cabin"], [42, 61, 1500, "Leafpoint's grove"], [30, 66, 1650, None],
    [24, 70, 1700, None], [22, 88, 1650, None], [40, 74, 1400, None], [46, 66, 1450, None],
    # Magic Mountain
    [30, 36, 4100, "Magic Mountain"], [38, 31, 3700, None], [24, 30, 3500, None], [45, 36, 3200, None],
    [36, 43, 3000, "the Wizard's Seat (genie)"], [27.5, 50, 2300, "the wizards' camp"], [47.5, 51, 1900,
                                                                                         "the woodpile"],
    [46, 41.5, 2700, "the gargoyle lair (DD-23)"], [50, 45, 2400, None], [52, 34, 2600, None], [40, 50, 2600, None],
    [33, 56, 1800, None], [22, 52, 2400, None], [20, 42, 3000, None],
    # the Snow River uplands
    [61, 30, 2300, "the Snow Springs"], [56, 28, 2500, None], [68, 28, 2400, None], [70, 33, 2200, "the roc nest"],
    [64, 40, 1900, None], [58, 44, 1700, "the rapids"], [66, 46, 1600, None], [74, 44, 1800, None],
    [76, 32, 2100, None], [86, 30, 2000, None], [94, 31, 1900, None], [100, 38, 1800, "the resilience fountain"],
    [59.5, 52, 1150, "the Snow River bridge"], [68, 53.5, 1120, None], [78, 54, 1180, "Blackfang's gate"],
    # Blackfang's crag
    [86, 49, 3100, "Castle Blackfang"], [83, 46, 2800, None], [90, 46, 2900, None], [88, 54, 2700, None],
    [82, 53, 2300, None], [93, 52, 2600, None], [92, 42, 2300, None],
]

BANDS = [
    ('band:rim_sea', 'zone:rim', RIM_POLY),
    ('band:peaks', 'zone:magic_mountain', SPACES_POLY['zone:magic_mountain']),
    ('band:uplands', 'zone:snow_uplands', SPACES_POLY['zone:snow_uplands']),
    ('band:uplands', 'zone:rim_corner', SPACES_POLY['zone:rim_corner']),
    ('band:crag', 'zone:blackfang_crag', SPACES_POLY['zone:blackfang_crag']),
    ('band:shore', 'zone:north_shore', SPACES_POLY['zone:north_shore']),
    ('band:forest', 'zone:forest_of_peril', SPACES_POLY['zone:forest_of_peril']),
    ('band:shore', 'zone:west_shore', SPACES_POLY['zone:west_shore']),
    ('band:heath', 'zone:desert_heath', SPACES_POLY['zone:desert_heath']),
    ('band:heath', 'zone:lakeside_brow', SPACES_POLY['zone:lakeside_brow']),
    ('band:shore', 'town:lakeside', SPACES_POLY['town:lakeside']),
    ('band:shore', 'zone:east_shore', SPACES_POLY['zone:east_shore']),
    ('band:uplands', 'zone:rimward_crags', SPACES_POLY['zone:rimward_crags']),
    ('band:shore', 'zone:isle', ISLE),
]

ROADS = [
    {'link': 'link:sandcaster_road', 'line': [[88, 109], [88, 104], [87.5, 100], [86.5, 96.5], [86, 95]],
     'width': 'road', 'surface': 'road_pebbles'},
    {'link': 'link:town_road_east', 'line': [[86, 95], [85, 92.5], [84, 91.5], [81.5, 91.5], [78, 91]],
     'width': 'road', 'surface': 'road_pebbles'},
    {'link': 'link:desert_road', 'line': [[19, 80], [24, 80], [30, 80], [36, 81]], 'width': 'road',
     'surface': 'soil_stony'},
    {'link': 'link:forest_road', 'line': [[36, 81], [42, 82], [47, 84], [52, 86.5], [56, 88.5], [59.5, 90],
                                          [63, 91.5], [68, 91.5]], 'width': 'road', 'surface': 'soil_stony'},
    {'link': 'link:shore_path', 'line': [[86, 95], [88, 91], [89.5, 87], [90.5, 84.5], [92, 80.5], [93.5, 77.5],
                                         [94.5, 76]], 'width': 'lane', 'surface': 'soil'},
    {'link': 'link:west_shore_track', 'line': [[61, 83], [58, 81], [56, 78.5], [54.5, 75], [53, 70], [52.5, 64],
                                               [53.5, 59], [56, 55], [59.5, 52]], 'width': 'lane', 'surface': 'soil'},
    {'link': 'link:north_shore_track', 'line': [[59.5, 52], [63, 53], [68, 53.5], [73, 54], [77, 54]],
     'width': 'lane', 'surface': 'soil'},
    {'link': 'link:snow_track', 'line': [[59.5, 52], [57.5, 48], [57, 44], [58.5, 39], [60, 34], [61, 31.5],
                                         [66, 30], [72, 30.5], [80, 32], [88, 31.5], [94, 33], [98, 36], [100, 38]],
     'width': 'lane', 'surface': 'soil_stony'},
    {'link': 'link:forest_lane', 'line': [[36, 81], [35, 77], [34.5, 74], [36, 69], [38.5, 65.5], [41, 62.5]],
     'width': 'lane', 'surface': 'soil'},
    {'link': 'link:camp_lane', 'line': [[36, 69], [33, 64], [30.5, 60], [32, 56.5], [29.5, 54], [28, 52.5]],
     'width': 'lane', 'surface': 'soil_stony'},
    {'link': 'link:seat_path', 'line': [[29.5, 48.5], [32, 46.5], [34.5, 44.5], [36, 43.5]], 'width': 'lane',
     'surface': 'soil_stony'},
    {'link': 'link:woodpile_lane', 'line': [[43.5, 60], [45, 56.5], [46.5, 53], [47.5, 51.5]], 'width': 'lane',
     'surface': 'soil'},
    {'link': 'link:lair_path', 'line': [[47.5, 51], [48.5, 48], [47.5, 45], [46.5, 42.5]], 'width': 'lane',
     'surface': 'soil_stony'},
]

# plots: (building, index, at, facing)
PLOTS = [
    ('building:lk_guild', None, [63.5, 87], 'e'),
    ('building:lk_smithy', None, [78.5, 87.5], 'w'),
    ('building:lk_tavern', None, [69, 93.5], 'n'),
    ('building:lk_temple', None, [73.5, 93.5], 'n'),
    ('building:lk_yachts', None, [70.5, 83.5], 'n'),
    ('building:lk_houses', 1, [61, 83.5], 'n'),        # Old Gill's Shack
    ('building:lk_houses', 2, [60, 92], 'e'),          # The Tannery
    ('building:lk_houses', 3, [64, 83.5], 'n'),        # Tidewater House
    ('building:lk_houses', 4, [64.5, 94.5], 'n'),      # The Gray Manor
    ('building:lk_houses', 5, [75, 83.5], 'n'),        # Netmender's House
    ('building:lk_houses', 6, [79, 93.5], 'n'),        # The Hollow House
    ('building:lk_houses', 7, [60.5, 87], 'e'),        # Reedcutter's Cottage
    ('building:lk_houses', 8, [67, 83.5], 'n'),        # The Eel House
    ('building:lk_houses', 9, [82.5, 87.5], 'w'),      # Widow Marsh's
    ('building:lk_houses', 10, [78, 83.5], 'n'),       # The Boathouse
]

PTS = [
    ('entrance:south_road', [88, 105], 'n'), ('entrance:west_road', [23, 80], 'e'),
    ('entrance:lakeside_square', [72, 90], 'n'), ('entrance:lakeside_dock', [72, 82], 's'),
    ('entrance:isle_landing', [72, 73], 'n'),
    ('entrance:dd12_door', [72, 67], 's'), ('entrance:dd20_guild', [67.5, 89], 'e'),
    ('entrance:dd20_shaft', [69, 82.5], 'n'), ('entrance:dd23_lair', [46, 41.5], 's'),
    ('entrance:blackfang_gate', [78.5, 53.5], 'w'),
    ('junction:well_fork', [86, 95], None), ('junction:ector_fork', [36, 81], None),
    ('junction:snow_bridge', [59.5, 52], None),
    ('poi:obelisk', [57, 80.5], None), ('poi:fountain_magic', [28.5, 49], None), ('poi:warding_well', [87.5, 96.5], None),
    ('poi:fountain_resilience', [100, 38], None), ('poi:woodpile', [47.5, 51], None), ('poi:cairn', [90.5, 83.5], None),
    ('poi:mirabeth', [94.5, 75.5], None), ('poi:genie_seat', [36, 43.5], None), ('poi:genie_skerry', [89, 70], None),
    ('poi:witches_circle', [50, 90.5], None), ('poi:reed_cauldron', [53, 68.5], None),
    ('poi:beached_boat', [82, 82], None), ('poi:roc_nest', [70, 33], None), ('poi:frozen_pilgrim', [62.5, 29.5], None),
    ('poi:skerry_strongbox', [61, 70], None), ('poi:roc_hunter', [100, 99], None), ('poi:heath_wagon', [52, 99.5], None),
    ('poi:circle_chest', [50.5, 91], None), ('poi:hunters_hide', [24, 64], None), ('poi:falls_chest', [101, 63], None),
    ('poi:gibbet', [74, 104], None), ('poi:isle_boat', [72.5, 73.5], None),
    ('poi:animal_trap', [38, 67], None), ('poi:animal_trap', [30, 85], None),
    ('poi:signposts', [86.5, 94.5], None), ('poi:signposts', [36.5, 81.5], None), ('poi:signposts', [60, 52.5], None),
    ('poi:naomi', [74.5, 89.5], None), ('poi:slibo', [26.5, 51], None), ('poi:leafpoint', [42, 60.5], None),
    ('poi:ector', [33.5, 72.5], None), ('poi:mirror', [72.5, 88], None),
    ('landmark:blackfang', [86, 48], None), ('landmark:isle', [72, 68.5], None),
    ('landmark:magic_mountain', [30, 36], None), ('landmark:octopod_falls', [104, 67], None),
    ('landmark:rapids', [58, 44], None),
]

AREAS = [
    {'id': 'pop:mountain_gargoyles', 'count': 13, 'slot': 1,
     'polygon': [[21, 26], [38, 25], [52, 28], [56, 38], [54, 46], [44, 47.5], [34, 45], [31, 44], [21, 44]],
     'notes': "E1: Mountain Gargoyles 30, Sentinels 38, an Overlord 45 (Dif 2) on the perches round DD-23; none on "
              "the camp's shelf (x < 32) or in the woodcutters' clearing."},
    {'id': 'pop:snow_rocs', 'count': 12, 'slot': 2,
     'polygon': [[56, 26], [103, 26], [103, 56], [98, 57], [95, 44], [93, 38], [84, 38], [77, 43], [70, 47],
                 [62, 47], [58, 41], [56, 33]],
     'notes': "E2: Vulture Rocs 30 (Rocs 38, Griffins 48 rare) over the uplands, the rapids and the rim corner behind "
              "Blackfang's crag (the resilience fountain is reached past them)."},
    {'id': 'pop:rimward_rocs', 'count': 8, 'slot': 2,
     'polygon': [[93, 86], [103, 82], [103, 108], [93, 108]],
     'notes': "E3: Vulture Rocs 30 on the crags east of the road; the first fight from D3 (2,600 off)."},
    {'id': 'pop:heath_rocs', 'count': 14, 'slot': 2,
     'polygon': [[20, 89], [31, 89], [43, 95.5], [58, 96.5], [60, 108], [20, 108]],
     'notes': "E5: Vulture Rocs over the desert edge; the first fight from D5 (about 4,600 off)."},
    {'id': 'pop:circle_witches', 'count': 8, 'slot': 3, 'kind': 'encounter',
     'polygon': [[45.5, 87], [54.5, 87.5], [55, 94], [45.5, 94]],
     'notes': "E4a: the Witches' Circle, 8 placed (not markers): Witch 32 x5, Coven Witch 40 x2, Coven Mother 50."},
    {'id': 'pop:reed_witches', 'count': 6, 'slot': 3, 'kind': 'encounter',
     'polygon': [[49, 63.5], [56, 63.5], [56.5, 73], [50, 73]],
     'notes': "E4b: the cauldron in the reeds, 6 placed: Witch 32 x4, Coven Witch 40 x2."},
    {'id': 'pop:octopods', 'count': 2, 'slot': 2, 'kind': 'encounter',
     'polygon': [[56, 58], [70, 57], [68, 62], [62, 72], [57, 73]],
     'notes': "E6 (west basin): placed octopods in the deep water only; see actors."},
    {'id': 'pop:octopods_east', 'count': 3, 'slot': 2, 'kind': 'encounter',
     'polygon': [[81, 61], [97, 61], [99, 68], [92, 73], [86, 78], [81, 72]],
     'notes': "E6 (east basin)."},
    {'id': 'zone:lakeside_brow', 'kind': 'keep_clear', 'polygon': [[83, 99], [93, 99], [93, 109], [83, 109]],
     'notes': "The D3 arrival."},
    {'id': 'zone:west_edge', 'kind': 'keep_clear', 'polygon': [[19, 75], [29, 75], [29, 86], [19, 86]],
     'notes': "The D5 arrival."},
    {'id': 'town:lakeside', 'kind': 'keep_clear', 'polygon': [[55, 77], [90, 77], [91, 102], [55, 102]],
     'notes': "Lakeside and its buffer (about 2,500 round the doors)."},
    {'id': 'zone:isle', 'kind': 'keep_clear', 'polygon': ISLE},
    {'id': 'zone:wizard_camp', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:wizard_camp']},
    {'id': 'zone:leafpoint_grove', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:leafpoint_grove']},
    {'id': 'zone:ector_clearing', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:ector_clearing']},
    {'id': 'zone:mirabeth_point', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:mirabeth_point']},
    {'id': 'zone:woodcutters_clearing', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:woodcutters_clearing']},
]

ACTORS = [
    {'monster': '11170', 'at': [50, 90], 'count': 5, 'spread': 2, 'group': 1, 'hostile': True,
     'notes': "The Witches' Circle: Witches 32; hidden at load once q-d22.done."},
    {'monster': '11171', 'at': [51, 91], 'count': 2, 'spread': 1, 'group': 1, 'hostile': True,
     'notes': "Coven Witches 40."},
    {'monster': '11172', 'at': [50.5, 90.5], 'count': 1, 'spread': 0, 'group': 1, 'hostile': True,
     'notes': "A Coven Mother 50 at the cauldron."},
    {'monster': '11170', 'at': [53, 68], 'count': 4, 'spread': 2, 'group': 2, 'hostile': True,
     'notes': "The cauldron in the reeds: Witches 32; hidden at load once q-d22.done."},
    {'monster': '11171', 'at': [53.5, 69.5], 'count': 2, 'spread': 1, 'group': 2, 'hostile': True},
    {'monster': '11470', 'at': [59, 65], 'count': 1, 'spread': 0, 'group': 3, 'hostile': True,
     'notes': "An Octopod 50 in the west basin's deep water (A2/A1: a swimmer, it never leaves the deep)."},
    {'monster': '11470', 'at': [64, 60], 'count': 1, 'spread': 0, 'group': 4, 'hostile': True},
    {'monster': '11471', 'at': [87, 66], 'count': 1, 'spread': 0, 'group': 5, 'hostile': True,
     'notes': "A Great Octopod 60 in the east basin, by the East Skerry's lamp."},
    {'monster': '11470', 'at': [94, 67], 'count': 1, 'spread': 0, 'group': 6, 'hostile': True},
    {'monster': '11471', 'at': [84, 74], 'count': 1, 'spread': 0, 'group': 7, 'hostile': True},
    {'monster': 'Peasant', 'npc': 5318, 'at': [74.5, 89.5], 'count': 1, 'spread': 0, 'group': 8, 'hostile': False,
     'notes': "Naomi (talking actor 5318) in the stocks on the square, facing the guild's door (Q-D22)."},
    {'monster': 'Peasant', 'npc': 5317, 'at': [26.5, 51], 'count': 1, 'spread': 0, 'group': 9, 'hostile': False,
     'notes': "Slibo (5317) by the tents (Q-C24, Q-D2)."},
    {'monster': 'Peasant', 'npc': 5320, 'at': [33.5, 72.5], 'count': 1, 'spread': 0, 'group': 10, 'hostile': False,
     'notes': "Ector (5320) at his chopping block (Q-D21)."},
]

VIEWS = [
    {'id': 'view:arrival', 'at': [88, 102], 'height': 180, 'look': [82, 70],
     'purpose': "MU-4 arrival view: from the brow on the D3 road, looking north: the road down to Lakeside's slate "
                "roofs and jetty on the shore at the left, the lake opening up beyond with the Isle of Lost Souls, "
                "Castle Blackfang on its crag across the water, the falls at the east rim at the right, Magic "
                "Mountain's snow far left over the Forest of Peril."},
    {'id': 'view:signature', 'at': [72, 80], 'height': 180, 'look': [82, 50],
     'purpose': "MU-4 signature view (about 60 degrees): from the ferry jetty's end, looking north-north-east over "
                "the water: the Isle of Lost Souls with its ruined round tower and dead trees ahead-left, and beyond "
                "it Castle Blackfang on its black crag in the storm of bats, its sealed gatehouse at the crag's "
                "foot; the rapids and the snowfield at the far left; the glow above the north-east rim."},
]

SKETCH = {
    'format': 0,
    'grid': 512,
    'map_cells': 128,
    'notes': "D4 Lakeside and Blackfang, MU-3 to-scale plan (A6, 2026-11-20), for the phase 4 review: composition, "
             "scale and density only. Cells [x, y], x east, y south. Heights above the stars below the rim (0): the "
             "lake 1,056, Lakeside 1,100-1,150, the forest 1,200-1,700, the heath 1,500-1,900 (D3's spans), the "
             "uplands to 2,400, Blackfang's crag 3,100, Magic Mountain 4,100. Written by "
             "level_generation/xeen_art/phase4/d4_brief.py. The later L3 adds plots' detail, ground, scatter and "
             "structures.",
    'frame': {
        'playable': [19, 19, 90, 90],
        'edges': [
            {'side': 'south', 'span': [82, 94], 'neighbour': 'edge:south',
             'notes': "The Lakeside road runs out to y 127 at x 88 (D3's north edge, D-28)."},
            {'side': 'west', 'span': [72, 88], 'neighbour': 'edge:west',
             'notes': "The desert road runs out to x 0 at y 80 (proposed for D5)."},
        ],
        'rim': [
            {'side': 'north', 'form': 'level', 'height': 0, 'meet': 1,
             'notes': "The world rim: the land ends in a cliff at y 24; below, water at 0 stands for the stars."},
            {'side': 'east', 'form': 'level', 'height': 0, 'meet': 1,
             'notes': "The world rim: the cliff at x 104 (D3's east rim continues); the lake falls over it at y 67."},
            {'side': 'south', 'span': [0, 24], 'form': 'ridge', 'height': [2600, 3400], 'floor': 2000, 'crest': 10,
             'roughness': 120, 'notes': "D3's north edge [0, 24]: the last Gemstone crags."},
            {'side': 'south', 'span': [24, 82], 'form': 'ridge', 'height': [1500, 2000], 'floor': 1400, 'crest': 10,
             'roughness': 80, 'notes': "D3's north edge [24, 82]: dunes of the desert edge."},
            {'side': 'south', 'span': [82, 94], 'form': 'level', 'height': 1750, 'meet': 6,
             'notes': "D3's north edge [82, 94]: the Lakeside road (D3's bed 1,760 at x 88)."},
            {'side': 'south', 'span': [94, 104], 'form': 'ridge', 'height': [1900, 2400], 'floor': 1700, 'crest': 8,
             'roughness': 100, 'notes': "D3's north edge [94, 104]: the Wrath crest's north shoulder."},
            {'side': 'south', 'span': [104, 128], 'form': 'level', 'height': 0, 'meet': 1,
             'notes': "D3's north edge [104, 128]: the rim."},
            {'side': 'west', 'span': [0, 24], 'form': 'level', 'height': 0, 'meet': 1,
             'notes': "The north rim's west end."},
            {'side': 'west', 'span': [24, 60], 'form': 'ridge', 'height': [2800, 3600], 'floor': 2200, 'crest': 10,
             'roughness': 120, 'notes': "Magic Mountain's west flank, on into D5's highlands."},
            {'side': 'west', 'span': [60, 72], 'form': 'ridge', 'height': [1800, 2300], 'floor': 1500, 'crest': 8,
             'roughness': 80, 'notes': "Forested hills."},
            {'side': 'west', 'span': [72, 88], 'form': 'level', 'height': 1500, 'meet': 6,
             'notes': "The desert road's valley, open to D5."},
            {'side': 'west', 'span': [88, 104], 'form': 'ridge', 'height': [1500, 2000], 'floor': 1400, 'crest': 10,
             'roughness': 80, 'notes': "Dunes of the desert edge (D5's Perishing Sands beyond)."},
            {'side': 'west', 'span': [104, 128], 'form': 'ridge', 'height': [2600, 3400], 'floor': 2000, 'crest': 10,
             'roughness': 120, 'notes': "The last Gemstone crags (D3's north-west corner)."},
        ],
        'edge': {'height': 1500, 'north': 0, 'east': 0},
    },
    'heights': {
        'bands': [{'band': b, 'space': s, 'polygon': poly} for b, s, poly in BANDS],
        'points': [dict({'at': [x, y], 'h': h}, **({'notes': n} if n else {})) for x, y, h, n in POINTS_H],
        'cliffs': [
            {'line': [[0, RIM_NORTH_Y], [RIM_EAST_X, RIM_NORTH_Y], [RIM_EAST_X, 128]], 'drop': 1500, 'down': 'left',
             'notes': "The world rim, north then east (drawn west to east and north to south, the low side outward); "
                      "the lake's outflow falls over it at (104, 67)."},
            {'line': [[79, 59], [84, 60], [90, 60], [95, 59]], 'drop': 1400, 'down': 'right',
             'notes': "Blackfang's crag: its south face straight into the lake."},
            {'line': [[40, 44], [44, 47.5], [48, 47]], 'drop': 500, 'down': 'right',
             'notes': "The crags over the woodcutters' clearing, DD-23's cave in their foot at (46, 41.5)."},
        ],
        'ridges': [
            {'line': [[22, 30], [30, 36], [38, 31], [45, 36]], 'height': 3600, 'width': 2, 'slope': 4,
             'notes': "Magic Mountain's crest."},
            {'line': [[95, 88], [100, 96], [99, 104]], 'height': 2300, 'width': 2, 'slope': 3,
             'notes': "The Rimward crags, D3's Wrath shoulder running on north."},
        ],
    },
    'water': {
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': RIM_POLY,
             'notes': "Below the rim: stands for the stars."},
            {'id': 'water:octopod_lake', 'kind': 'lake', 'level': LAKE_LEVEL, 'polygon': LAKE,
             'notes': "Octopod Lake. The Isle of Lost Souls and the two skerries are height points inside it (an islet "
                      "in water is a height point). Deep water: the west basin (56-70, 58-76) and the east basin "
                      "(80-98, 61-78)."},
            {'id': 'water:snow_springs', 'kind': 'pond', 'level': 2270,
             'polygon': [[60, 28.5], [63, 28.5], [63.5, 30.5], [61.5, 31.5], [60, 30.5]],
             'notes': "The Snow Springs' tarn under the snowfield."},
        ],
        'rivers': [
            {'id': 'water:snow_river', 'line': [[61.5, 31], [62, 34], [61, 38], [59.5, 42], [58.5, 46], [59, 50],
                                                [59.5, 53], [59, 56]], 'width_cells': 1.5,
             'notes': "The Snow River: rapids from the springs (2,270) down a rocky cut to the lake's north-west bay "
                      "(1,056); the timber bridge at (59.5, 52)."},
            {'id': 'water:outflow', 'line': [[99.5, 66.5], [102, 67], [104, 67]], 'width_cells': 2,
             'level': LAKE_LEVEL, 'notes': "The race from the lake to the rim, where it falls into the stars."},
        ],
    },
    'roads': ROADS,
    'districts': [
        {'space': 'town:lakeside', 'polygon': SPACES_POLY['town:lakeside'],
         'plots': [dict({'building': b, 'at': at, 'facing': f, 'door_to': 'zone:lakeside_square'},
                        **({'index': i} if i else {})) for b, i, at, f in PLOTS],
         'notes': "A4's d4.yml: the guild 4651 (west of the square, its double door east), the smithy 4653 (east), "
                  "the tavern 4652 and the temple 4654 (south), Lakeside Yachts 4655 on the waterfront with the "
                  "jetty at x 72, ten houses 4657-4666 along the waterfront and the edges; the mirror 4656 on the "
                  "square with Naomi's stocks."},
        *[{'space': s, 'polygon': SPACES_POLY[s]} for s in SPACES_POLY
          if s not in ('town:lakeside', 'zone:rim')],
        {'space': 'zone:rim', 'polygon': RIM_POLY},
    ],
    'points': [dict({'id': pid, 'at': at}, **({'facing': f} if f else {})) for pid, at, f in PTS],
    'areas': AREAS,
    'views': VIEWS,
    'actors': ACTORS,
}

# waterfront plots open onto the waterfront, not the square
for d in SKETCH['districts']:
    for plot in d.get('plots', []):
        if plot['facing'] == 'n' and plot['at'][1] < 85:
            plot['door_to'] = 'zone:lakeside_waterfront'
        if plot['building'] in ('building:lk_houses',) and plot.get('index') in (2, 4, 6, 7, 9):
            plot['door_to'] = 'town:lakeside'


def whole(v):
    return int(v + 0.5) if v >= 0 else -int(-v + 0.5)


def round_geometry():
    """Whole cells everywhere but road lines and plot corners (the studio's rule); half-cell positions above are
    the drawing's intent, rounded here once."""
    for p in SKETCH['points']:
        p['at'] = [whole(c) for c in p['at']]
    for p in SKETCH['heights']['points']:
        p['at'] = [whole(c) for c in p['at']]
    for v in SKETCH['views']:
        v['at'] = [whole(c) for c in v['at']]
        v['look'] = [whole(c) for c in v['look']]
    for r in SKETCH['water']['rivers']:
        r['line'] = [[whole(c) for c in pt] for pt in r['line']]
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
    round_geometry()
    dump(PROJECT, OUT / 'project.yml')
    dump(PLAN, OUT / 'plan.yml')
    dump(SKETCH, OUT / 'sketch.yml')
    print('written', OUT)


if __name__ == '__main__':
    main()
