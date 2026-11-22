#!/usr/bin/env python3
"""D6 The Forbidden Zone: the L1 brief (MU-3) in Map Studio's schema, written from the data below (A6, phase 5).

    d6_brief.py        -> devdocs/xeen/briefs/d6/L1/{project,plan,sketch,atmosphere}.yml
                          (then `oymap fmt` and `oymap validate ... --assets assets_dev`)

Edit this script, not the YAML. NOTES.md beside the brief is written by hand. Cells [x, y]: x east, y south, 512 units
each; heights in map units above the stars below the rim (0). The border points along y 109 (D1) and x 109 (D5) are
read from D1's installed heightmap and from phase5/edge_d5_d6.json (both read only). Nothing here is read by the game.
"""
import json
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'devdocs/xeen/briefs/d6/L1'

RIM_NORTH_Y = 24          # the north rim (D5's and D4's north rim also y 24)
RIM_WEST_X = 24           # the west rim (D1's west rim also x 24)
BORDER = 109              # D6's south border row (= D1's y 19) and east border column (= D5's x 19)
MOAT_LEVEL = 1550         # Alamar's lava moat
POD_LAKE_LEVEL = 1450     # Corak's lava lake (the moat drains into it)

# ---------------------------------------------------------------------------------------------- the borders


def d1_row():
    """D1's installed border row y 19 (x 0-127), heights in map units."""
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_odm_file
    data = parse_odm_file(ROOT / 'assets_dev/worlds/xeen/maps/xeen_d1.odm')
    return [int(v) for v in np.array(data['payload']['height_map'], int).reshape(128, 128)[19] * 32]


def d5_column():
    """The shared D5/D6 border (A6's lead file, read only): heights by y 0-127."""
    return json.loads((HERE / 'edge_d5_d6.json').read_text())['heights_by_y']


# ---------------------------------------------------------------------------------------------- geometry

RIM_POLY = [[0, 0], [128, 0], [128, RIM_NORTH_Y], [RIM_WEST_X, RIM_NORTH_Y], [RIM_WEST_X, 128], [0, 128]]
# Alamar's moat: a horseshoe of lava round the plateau, open to the south where the approach climbs onto it
MOAT = [[40, 58], [35, 50], [36, 41], [42, 35], [51, 32], [60, 35], [65, 42], [65, 51], [62, 58], [59, 56], [61, 50],
        [60, 43], [56, 38], [51, 36], [45, 38], [40, 43], [39, 50], [43, 56]]
POD_LAKE = [[64, 59], [70, 57], [77, 59], [80, 64], [80, 70], [76, 74], [69, 75], [63, 72], [61, 66]]
NECRO = [[82, 74], [100, 74], [100, 90], [82, 90]]           # Necropolis inside its walls

SPACES_POLY = {
    'zone:rim': RIM_POLY,
    'zone:ash_waste': [[24, 24], [64, 24], [64, 32], [60, 35], [51, 32], [42, 35], [36, 41], [35, 50], [40, 58],
                       [36, 62], [24, 62]],
    'zone:hot_spring': [[27, 27], [34, 27], [34, 34], [27, 34]],
    'zone:alamar_plateau': [[43, 56], [39, 50], [40, 43], [45, 38], [51, 36], [56, 38], [60, 43], [61, 50], [59, 56],
                            [57, 62], [46, 62]],
    'zone:alamar_approach': [[46, 57], [57, 57], [57, 63], [46, 63]],
    'zone:ancient_field': [[64, 24], [109, 24], [109, 56], [100, 58], [90, 58], [80, 56], [70, 53], [65, 51], [65, 42],
                           [60, 35], [64, 32]],
    'zone:pod_lake_shore': [[61, 52], [70, 53], [80, 56], [86, 62], [86, 70], [82, 76], [74, 80], [64, 80], [57, 74],
                            [57, 62]],
    'zone:pod_crust': [[73, 68], [78, 70], [78, 74], [74, 74]],
    'zone:west_waste': [[24, 62], [36, 62], [40, 58], [46, 62], [46, 63], [57, 63], [57, 74], [60, 80], [56, 88],
                        [44, 90], [24, 90]],
    'zone:archer_camp': [[30, 83], [39, 83], [39, 89], [30, 89]],
    'zone:obelisk_knoll': [[27, 59], [33, 59], [33, 65], [27, 65]],
    'zone:south_peaks': [[24, 90], [44, 90], [56, 88], [60, 92], [60, 109], [24, 109]],
    'zone:griffin_pass': [[59, 91], [70, 91], [70, 100], [59, 100]],
    'zone:mountain_road': [[59, 100], [70, 100], [70, 109], [59, 109]],
    'zone:east_peaks': [[70, 91], [76, 88], [82, 92], [100, 92], [109, 90], [109, 109], [70, 109]],
    'zone:ash_fork_flats': [[57, 74], [64, 80], [74, 80], [82, 76], [82, 90], [76, 88], [70, 91], [59, 91], [60, 80]],
    'town:necropolis': NECRO,
    'zone:np_square': [[88, 75], [95, 75], [95, 81], [88, 81]],
    'zone:bone_road': [[86, 62], [100, 58], [109, 56], [109, 70], [100, 74], [82, 74], [86, 70]],
    'zone:climbers_camp': [[97, 67], [103, 67], [103, 72], [97, 72]],
    'zone:pass_east': [[101, 60], [109, 60], [109, 68], [101, 68]],
    'zone:east_ridge': [[100, 74], [109, 70], [109, 90], [100, 92]],
}

# ---------------------------------------------------------------------------------------------- the plan


def S(id_, name, kind, purpose, **kw):
    d = {'id': id_, 'name': name, 'kind': kind}
    d.update({k: v for k, v in kw.items() if k not in ('purpose',)})
    d['purpose'] = purpose
    return d


SPACES = [
    # ---- the arrivals ----
    S('zone:mountain_road', "The long mountain road", 'zone', floor=[1550, 2400],
      where="south, the road from D1 climbing the Forbidden Zone's southern border to Griffin Pass",
      purpose="Where the party comes in from D1: the long mountain road (D1's north road at x 64) climbs a bare valley "
              "between grey-black peaks to Griffin Pass. Nothing lives on the road itself.",
      safe=True, keep_clear=['spawns']),
    S('zone:griffin_pass', "Griffin Pass", 'zone', floor=2450,
      where="the saddle at the top of the mountain road",
      purpose="A saddle of black rock at 2,450 where the Forbidden Zone opens below: ash plains, the glow of the lava, "
              "Castle Alamar's lit walls far north on their plateau. Ambrose's camp under an overhang: a tent, a fire, "
              "a tethered griffin on a rock (A4's 5512; m25.flight from his topic). After m25.done Ambrose and the "
              "griffin are gone (m25.camp_gone); the tent and the cold fire stay (D-49 change 6).",
      safe=True, keep_clear=['spawns']),
    S('zone:pass_east', "The Forbidden Zone's border pass", 'zone', floor=1700,
      where="east, the pass to D5 at y 64",
      purpose="Where the party comes in from D5: a pass at 1,700 through the east ridge; the source's sign \"The "
              "Forbidden Zone\" at its western lip (B2(15,15)). Necropolis's walls in view to the south-west.",
      safe=True, keep_clear=['spawns']),
    # ---- Necropolis ----
    S('town:necropolis', "Necropolis", 'town', floor=1650,
      where="the east, on a terrace under the east ridge: 18 x 16 cells inside its walls, one gate in the north wall",
      purpose="The city of the dead (WORLD_DESIGN 5.2; A4's d6.yml 4751-4762): a walled necropolis the living enter "
              "with a pass (item 12336 from the Head Witch's chest, Q-D22); the gate turns the passless away (A3's "
              "hook, A6's event). Inside every house is open: the Dark guild, the Temple of the Dead, the Grave Market, "
              "the Embalmer, the Warm Barrel, the mirror, six residences of tombs and mausoleums, DD-21's crypt stair. "
              "The map's lines: the Books of the Dead, the barrel \"Food for the dead, keep warm.\", the skull's story.",
      safe=True, keep_clear=['spawns'], density='medium',
      theme="darkside_town kit in its darkest grade: t09 grey ashlar under xlslate for the guild, the temple and the "
            "walls (about 700 high, square towers, battlements, a gatehouse); tombs and mausoleums of MM7 Zokarr's "
            "Tomb stone (twb1, twb2, 7tws2) with iron doors, the crypt doors in two leaves (gkp103a / gkp103b); MU-2 "
            "D6 ground: road_flagstone in the lanes, mud_cracked (grey) in the yards; black dead trees (MM8 dedltree), "
            "bone-white lamps lit all day.",
      buildings=[
          {'id': 'building:np_guild', 'type': 'house', 'service': 'Necropolis Guild', 'count': 1, 'doors': 1,
           'footprint_cells': [[3, 3]],
           'notes': "4751: the Dark guild (hours 21-6). Two storeys of t09 ashlar, one window per storey and bay, its "
                    "door a carved double door as two leaves (double doors)."},
          {'id': 'building:np_temple', 'type': 'house', 'service': 'Temple of the Dead', 'count': 1, 'doors': 1,
           'footprint_cells': [[4, 3]],
           'notes': "4752: resurrection, cheaper Raise Dead (price 0.7). A domed hall at the square's south side, its "
                    "bronze doors in two leaves."},
          {'id': 'building:np_market', 'type': 'house', 'service': 'The Grave Market', 'count': 1, 'doors': 1,
           'footprint_cells': [[3, 2]], 'notes': "4753: the black-market magic shop (hours 21-6)."},
          {'id': 'building:np_embalmer', 'type': 'house', 'service': 'The Embalmer', 'count': 1, 'doors': 1,
           'footprint_cells': [[2, 2]], 'notes': "4754: the alchemist."},
          {'id': 'building:np_tavern', 'type': 'house', 'service': 'The Warm Barrel', 'count': 1, 'doors': 1,
           'footprint_cells': [[3, 3]],
           'notes': "4755: the tavern for the dead (packs to 30, D-29). The barrel by its wall: \"Food for the dead, "
                    "keep warm.\" (one spot with the door)."},
          {'id': 'building:np_houses', 'type': 'house', 'service': 'residence', 'count': 6, 'doors': 1,
           'footprint_cells': [[3, 3], [3, 2], [2, 2], [2, 2], [2, 2], [2, 2]],
           'notes': "4757-4762 in index order: the Necromancers' House (Master Morbius, Q-D23), Count Velkor's Crypt "
                    "(Vampire GM), the Quiet Tomb (Lady Vex, Dagger GM), the Trapsmith's Vault (Old Bones, Disarm Trap "
                    "GM), the Gravedigger's (Digby), the Weeping Mausoleum (the Weeping Lady). Tombs with iron doors, "
                    "one door each."},
      ]),
    S('zone:np_square', "The Square of Mourning", 'zone', part_of='town:necropolis', floor=1650,
      purpose="Flagstones inside the gate: the Mirror of Necropolis (4756, qbit 119011) on a black plinth with the "
              "talking skull beside it (the skull's story of the two necromancers); the Books of the Dead chained to "
              "lecterns at the square's west edge; the guild, the market, the temple and the tavern open onto it. "
              "Town Portal and mirror arrival.",
      safe=True, keep_clear=['spawns']),
    S('zone:bone_road', "The Bone Road", 'zone', floor=[1650, 1800], relief='slope', density='sparse',
      purpose="Ash and bone-white flagstones from the border pass down to Necropolis's gate under the east ridge: "
              "Bone Fork, a pilgrim's cart that turned back at the gate, an empty climbers' camp.", safe=True),
    S('zone:climbers_camp', "The climbers' camp", 'zone', part_of='zone:bone_road', floor=1800,
      purpose="An empty climbers' camp under the east ridge: a tent, ropes and pitons on a line, nobody there "
              "(dressing; no click, no NPC: D-49 change 1, Freeda is X5's 4527).",
      safe=True, keep_clear=['spawns']),
    S('zone:east_ridge', "The east ridge", 'wild', floor=[2000, 3000], relief='uneven', empty=True,
      purpose="The ridge between D6 and D5 south of the pass (the shared border, edge_d5_d6.json): bare black crags "
              "behind Necropolis."),
    # ---- the lava ----
    S('zone:pod_lake_shore', "Corak's lava lake", 'wild', floor=[1450, 1800], relief='uneven', density='sparse',
      purpose="A lava lake in a basin of black crust south-east of Alamar, fed by the Burning Channel from Alamar's "
              "moat. Escape Pod 1 (Corak's, DD-16) stands in it nose-up, half sunk, its hull scorched and glowing; the "
              "hatch faces the south-east shore over a tongue of crust. Lava dwellers (placed elementals) along the "
              "shores. An islet with a genie lamp in the north-west of the lake.",
      population=[{'id': 'pop:lava_dwellers', 'actor': 'Xeen Elemental', 'groups': 4, 'placed': True,
                   'hostile': True,
                   'notes': "E3: 14 placed Lesser Elementals 55 and Elementals 62 (the lava dwellers' stand-in, as "
                            "A7's DD-16) round the lake and along the Burning Channel, each with a home radius on the "
                            "crust; no group within 2,500 of the hatch."}]),
    S('zone:pod_crust', "The crust before the hatch", 'zone', part_of='zone:pod_lake_shore', floor=1460,
      purpose="Before m28.lava_cooled: lava round the hatch, which only the hook's fail line touches (\"A curved metal "
              "wall stands in lava that bubbles like soup.\"). After it the map's state swaps the lava there for black "
              "cooled crust (lavtyl -> a basalt tile set) and the hatch opens (m29.pod_door). DD-16's way out lands "
              "here, 384 before the hatch, facing away.",
      safe=True, keep_clear=['spawns']),
    S('water:pod_lake', "Corak's lava lake", 'water',
      purpose="Lava (lavtyl, D-40: never water). Level 1,450; Escape Pod 1 nose-up in its middle."),
    S('water:alamar_moat', "Alamar's moat", 'water',
      purpose="A horseshoe of lava round Alamar's plateau (level 1,550), open to the south where the approach "
              "climbs on; it spills north over the rim (the Northern Lava Falls), west along the Slag Run to the west "
              "rim, and south-east down the Burning Channel into Corak's lake."),
    S('water:burning_channel', "The Burning Channel", 'water',
      purpose="Lava from Alamar's moat down to Corak's lake (1,550 to 1,450)."),
    S('water:slag_run', "The Slag Run", 'water',
      purpose="Lava from the moat's west side to the west rim, where it falls into the stars (a lava fall)."),
    S('water:north_falls', "The Northern Lava Falls", 'water',
      purpose="Lava from the moat's north side over the north rim into the stars."),
    # ---- Castle Alamar ----
    S('zone:alamar_plateau', "Castle Alamar's plateau", 'wild', floor=[1800, 2300], relief='uneven',
      purpose="A basalt mesa in the lava moat, north-west of the map's middle (the source's A1(10,4)): Castle Alamar, "
              "a fortress of dark teal steel and black stone, square towers, every window lit, energy fields "
              "humming between its pylons (the Ancient kit: xahull on gn_mtl, xaenergy pylons, xafield curtains). "
              "No walkable roof (WORLD_DESIGN 3.4). Robot patrols on the plateau and the approach. After M33 the "
              "castle has destroyed itself: a smoking ruin of buckled plates (xahullbn) and fallen towers, the "
              "sealed stair down to FD-01 in the broken gatehouse.",
      population=[{'id': 'pop:alamar_robots', 'slot': 3, 'groups': 9, 'per_marker': [1, 3], 'levels': [50, 75],
                   'notes': "Encounter area E2: Patrols 50 (Annihilators 62, an Autobot 75 rarely; Dif 1)."}]),
    S('zone:alamar_approach', "The approach", 'zone', part_of='zone:alamar_plateau', floor=[1700, 2000],
      purpose="The ramp of black rock onto the plateau from the south, between the moat's two arms: four energy-"
              "field pylons in pairs, the castle's double gate at its head (m33.castle_door: \"Castle Alamar. Every "
              "window is lit, and every one of them is looking at you. Enter?\"; DD-17 refuses a party without the "
              "Soul Box and moves it back here).", density='sparse'),
    # ---- the north ----
    S('zone:ash_waste', "The volcanic waste", 'wild', floor=[1550, 2100], relief='uneven', density='sparse',
      purpose="Grey ash and black basalt between Alamar's moat and the north and west rims, cracked by old flows: the "
              "Northern Lava Falls over the rim, the Slag Run to the west rim, a basalt pinnacle with a genie lamp, "
              "the hot spring in the north-west corner. Quiet: only the ash falls."),
    S('zone:hot_spring', "The hot spring", 'zone', part_of='zone:ash_waste', floor=1800,
      purpose="A steaming pool in a basalt bowl by the rims' corner: the Fountain of Super Resilience (the source's "
              "A1(2,13) waters), a burned pilgrim's pack beside it.", safe=True, keep_clear=['spawns']),
    S('zone:ancient_field', "The Ancient field", 'wild', floor=[1700, 2600], relief='uneven',
      purpose="Rock heaved up by something buried: plates, spars and pylons of Ancient metal surfacing through the "
              "basalt over the whole north-east (WORLD_DESIGN 4: Ancient metal surfacing in the north-west of the "
              "Darkside). Escape Pod 2 (Sheltem's, DD-22) lies landed upright in a shallow crater of its own, its "
              "hatch sealed (phase 6). The Well of Warding by the north-east rim; an Ancient locker; gamma gazers.",
      population=[{'id': 'pop:field_gazers', 'slot': 1, 'groups': 17, 'per_marker': [1, 3], 'levels': [40, 65],
                   'notes': "Encounter area E1: Floating Eyes 40, Terrible Eyes 50, Gamma Gazers 65 (Dif 2)."}]),
    # ---- the south-west ----
    S('zone:west_waste', "The cinder plains", 'wild', floor=[1550, 2100], relief='uneven', density='sparse',
      purpose="Cinder flats and low basalt ridges west and south of Alamar (the source's A2, barren highlands): the "
              "obelisk on its knoll over the Slag Run's fall, the barbarian archers' camp under the southern peaks, "
              "the Alamar road from Ash Fork."),
    S('zone:obelisk_knoll', "Obelisk Knoll", 'zone', part_of='zone:west_waste', floor=2050,
      purpose="A basalt knoll by the west rim, the Slag Run falling into the stars below it: the obelisk.",
      safe=True, keep_clear=['spawns']),
    S('zone:archer_camp', "The archers' camp", 'zone', part_of='zone:west_waste', floor=1950,
      purpose="A barbarian war-camp of hide tents behind a stake fence on a shelf under the peaks (the source's A2 "
              "barbarian archer camp): placed archers, their strongbox; burnable as the source's camps (A3).",
      population=[{'id': 'pop:archers', 'actor': 'Xeen Barbarian', 'groups': 1, 'placed': True, 'hostile': True,
                   'notes': "E6: 12 placed: Barbarian Archers 44 x9 and Archer Chiefs 50 x3 (new tiers asked of A2)."}]),
    S('zone:south_peaks', "The Forbidden Zone's southern border", 'wild', floor=[1300, 3400], relief='uneven',
      purpose="Grey-black peaks west of Griffin Pass along the south (the source's A2 border): griffins' crags, the "
              "Forbidden Zone mines: DD-10C's north adit and two boarded mine mouths, a dead prospector.",
      population=[{'id': 'pop:west_griffins', 'slot': 2, 'groups': 8, 'per_marker': [1, 3], 'levels': [30, 48],
                   'notes': "Encounter area E4a: Griffins 48 and Rocs 38 (Dif 5)."}]),
    S('zone:east_peaks', "The southern peaks east", 'wild', floor=[1300, 3200], relief='uneven',
      purpose="The same peaks east of the pass to the D5 ridge: the broken travel pyramid in a high valley, a "
              "griffin's nest, a genie lamp on a crag, the Sardaj cliff over D1's spring.",
      population=[{'id': 'pop:east_griffins', 'slot': 2, 'groups': 8, 'per_marker': [1, 3], 'levels': [30, 48],
                   'notes': "Encounter area E4b: Griffins 48 and Rocs 38 (Dif 5); the first fight from D1."}]),
    S('zone:ash_fork_flats', "Ash Fork", 'zone', floor=[1650, 1900], relief='slope', density='sparse',
      purpose="Ash flats at the foot of the pass where the mountain road forks: north-west to Alamar, east past "
              "Corak's lake to Necropolis. Quiet.", safe=True),
    S('zone:rim', "The world rim", 'wild', floor=0,
      purpose="North and west the land ends in a cliff; below, the stars (water at 0 stands for them). Lava falls "
              "pour over it in two places.", empty=True),
    S('water:rim_sea', "Below the rim", 'water', purpose="The stars below the world's edge (water at 0)."),
    # ---- junctions and edges ----
    S('junction:ash_fork', "Ash Fork", 'junction', signpost=True,
      purpose="North-west: Castle Alamar. East: Necropolis and the border pass. South: Griffin Pass and Castleview."),
    S('junction:bone_fork', "Bone Fork", 'junction',
      purpose="South: Necropolis's gate. East: the border pass (D5). West: Corak's lake and Ash Fork."),
    S('edge:south_end', "South edge", 'road', part_of='zone:mountain_road', purpose="Where the road leaves for D1."),
    S('edge:east_end', "East edge", 'road', part_of='zone:pass_east', purpose="Where the pass leaves for D5."),
]

LINKS = [
    {'id': 'link:mountain_road', 'from': 'edge:south_end', 'to': 'junction:ash_fork', 'kind': 'road', 'rise': 200,
     'purpose': "travel: D1; the long mountain road up to Griffin Pass (2,450) and down to the ash"},
    {'id': 'link:alamar_road', 'from': 'junction:ash_fork', 'to': 'zone:alamar_approach', 'kind': 'road', 'rise': 150,
     'purpose': "north-west over the cinder plains to the approach"},
    {'id': 'link:necropolis_road', 'from': 'junction:ash_fork', 'to': 'junction:bone_fork', 'kind': 'road',
     'purpose': "east past Corak's lake"},
    {'id': 'link:pass_road', 'from': 'edge:east_end', 'to': 'junction:bone_fork', 'kind': 'road', 'rise': -50,
     'purpose': "travel: D5; down from the border pass"},
    {'id': 'link:gate_lane', 'from': 'junction:bone_fork', 'to': 'zone:np_square', 'kind': 'road',
     'purpose': "through Necropolis's gate (the pass)"},
    {'id': 'link:hatch_path', 'from': 'link:necropolis_road', 'to': 'zone:pod_crust', 'kind': 'path',
     'purpose': "down the black shore to the crust before the hatch"},
    {'id': 'link:adit_track', 'from': 'junction:ash_fork', 'to': 'entrance:dd10c_adit', 'kind': 'path', 'rise': 500,
     'purpose': "west under the peaks past the archers' camp to the mines"},
    {'id': 'link:obelisk_path', 'from': 'link:alamar_road', 'to': 'zone:obelisk_knoll', 'kind': 'path', 'rise': 300},
    {'id': 'link:spring_track', 'from': 'link:alamar_road', 'to': 'zone:hot_spring', 'kind': 'path', 'rise': 200,
     'purpose': "west of the moat along the Slag Run and north to the hot spring"},
    {'id': 'link:field_track', 'from': 'link:necropolis_road', 'to': 'entrance:dd22_hatch', 'kind': 'path',
     'rise': 400, 'purpose': "north up the Burning Channel's east bank into the Ancient field"},
    {'id': 'link:rim_track', 'from': 'entrance:dd22_hatch', 'to': 'poi:warding_well', 'kind': 'path',
     'purpose': "east through the field to the well by the rim"},
]

ENTRANCES = [
    {'id': 'entrance:south_road', 'space': 'zone:mountain_road', 'kind': 'both', 'neighbour': 'edge:south',
     'facing': 'n', 'how': "The long mountain road from Castleview (D1) at x 64, climbing toward Griffin Pass."},
    {'id': 'entrance:east_pass', 'space': 'zone:pass_east', 'kind': 'both', 'neighbour': 'edge:east', 'facing': 'w',
     'how': "The Forbidden Zone's border pass from D5 at y 64 (edge_d5_d6.json: 1,700 over y 62-66)."},
    {'id': 'entrance:necropolis_gate', 'space': 'zone:np_square', 'kind': 'arrival', 'neighbour': 'mirror:darkside',
     'how': "Inside the gate by the mirror (A4's necropolis_gate): Town Portal and the mirror (4756, qbit 119011)."},
    {'id': 'entrance:np_gate', 'space': 'zone:bone_road', 'kind': 'both', 'facing': 's',
     'condition': {'item': 'necropolis_pass'},
     'how': "Necropolis's gate in the north wall, two iron-bound leaves under a gatehouse of skulls: with the pass "
            "they open; without it a line turns the living away (A3's hook, A6's event; from inside always open)."},
    {'id': 'entrance:dd17_gate', 'space': 'zone:alamar_approach', 'kind': 'both', 'neighbour': 'door:dd17',
     'facing': 's',
     'how': "Castle Alamar's double gate (two leaves of teal steel): m33.castle_door's question; DD-17's arrival "
            "hook refuses a party without the Soul Box and moves it back here. After M33 the gate is rubble."},
    {'id': 'entrance:fd01_stair', 'space': 'zone:alamar_approach', 'kind': 'both', 'neighbour': 'door:fd01',
     'facing': 's', 'condition': {'qbit': 'alamar_destroyed'},
     'how': "After M33 only: the stair down in the broken gatehouse's floor, sealed with Sheltem's mark "
            "(m39.depths_door: the Cube of Power opens it). One spot with the gate."},
    {'id': 'entrance:dd16_hatch', 'space': 'zone:pod_crust', 'kind': 'both', 'neighbour': 'door:dd16', 'facing': 'n',
     'condition': {'qbit': 'lava_cooled'},
     'how': "Escape Pod 1's hatch midship on the crust (m29.pod_door): shut and too hot until m28.lava_cooled; then "
            "\"The hatch slides aside with a sigh, as if it had been waiting.\""},
    {'id': 'entrance:dd22_hatch', 'space': 'zone:ancient_field', 'kind': 'both', 'neighbour': 'door:dd22',
     'facing': 's',
     'how': "Escape Pod 2's hatch (Sheltem's pod): sealed with a line until phase 6 (DD-22, Act VI)."},
    {'id': 'entrance:xd17_pyramid', 'space': 'zone:alamar_approach', 'kind': 'both', 'neighbour': 'scripted:pyramid',
     'facing': 'n',
     'how': "Beside the travel pyramid on the Alamar road outside the moat (D-50 Q9): XD-17's pyramid lands here; "
            "this pyramid's click (Xeen.travelPyramid(\"alamar_gate\")) goes to XD-17 once m30.done."},
    {'id': 'entrance:dd21_stair', 'space': 'town:necropolis', 'kind': 'both', 'neighbour': 'door:dd21', 'facing': 'n',
     'how': "A crypt stair behind iron grilles in Necropolis's south-east corner (two leaves): down to the Necropolis "
            "Sewer (DD-21, Sandro)."},
    {'id': 'entrance:dd10c_adit', 'space': 'zone:south_peaks', 'kind': 'both', 'neighbour': 'door:dd10c',
     'facing': 'n',
     'how': "The Gemstone Mines' north adit in the peaks' north face: a timbered mouth; DD-10C lands at its start "
            "(0, 192, 0) facing north; its exit returns here, facing away (A6 measures it at L3)."},
]

GOALS = [
    {'id': 'goal:alamar', 'space': 'zone:alamar_approach', 'kind': 'reach',
     'what': "Enter Castle Alamar with Corak in the Soul Box and end Sheltem (M33).", 'story': 'M33'},
    {'id': 'goal:corak', 'space': 'zone:pod_crust', 'kind': 'use',
     'what': "Open Corak's pod once the Pharaoh has cooled the lava, wake him (M29), bring him the Soul Box (M32).",
     'story': 'M29'},
    {'id': 'goal:blackfang', 'space': 'zone:griffin_pass', 'kind': 'use',
     'what': "Answer Ambrose (Dimitri), have his bridle enchanted in Sandcaster, fly to Blackfang's walls (M25).",
     'story': 'M25'},
    {'id': 'goal:sandro', 'space': 'town:necropolis', 'kind': 'reach',
     'what': "Enter Necropolis with the pass; Master Morbius, Sandro's heart in DD-21 (Q-D23).", 'story': 'Q-D23'},
    {'id': 'goal:diamonds', 'space': 'zone:south_peaks', 'kind': 'reach',
     'what': "Dig the north pocket's diamond veins (DD-10C, Q-D7).", 'story': 'Q-D7'},
    {'id': 'goal:roland', 'space': 'zone:alamar_approach', 'kind': 'reach',
     'what': "After M33: open the stair in Alamar's ruin with the Cube (M39, FD-01, phase 6).", 'story': 'M39'},
    {'id': 'goal:obelisk', 'space': 'zone:obelisk_knoll', 'kind': 'use',
     'what': "Read the sixth Darkside word (obelisks.d6).", 'story': 'obelisks'},
]


def P(id_, space, kind, behaviour, **kw):
    d = {'id': id_, 'space': space, 'kind': kind}
    d.update(kw)
    d['behaviour'] = behaviour
    return d


POIS = [
    P('poi:obelisk', 'zone:obelisk_knoll', 'obelisk',
      "obelisks.d6: the sixth of six words, PYRAMID (autonote dark_6, 115055).", rule='native:obelisk',
      notes="On Obelisk Knoll by the west rim (A3's autonote: \"Obelisk in the Forbidden Zone\"), the Slag Run's lava "
            "fall below, Alamar's plateau in view."),
    P('poi:fountain_resilience', 'zone:hot_spring', 'fountain',
      "The Fountain of Super Resilience (the source's +2,500 HP waters, A1(2,13)): +100 hit points until rest, once a "
      "day (rescaled as D4's Fountain of Great Resilience).", uses={'times': 1, 'per': 'character', 'reset': 'daily'}),
    P('poi:warding_well', 'zone:ancient_field', 'well',
      "The Well of Warding (the source's +100 all resistances, B1(14,13)): +20 Fire, Air, Water and Earth resistance "
      "until rest, once a day (rescaled, as D1's prayer shrine).",
      uses={'times': 1, 'per': 'character', 'reset': 'daily'}),
    P('poi:books', 'zone:np_square', 'device',
      "The Books of the Dead (the source's aging books): three black books chained to lecterns; each, once per "
      "character, +3,000 experience and +8 years of age (the source's +999,999 xp and +25-100 years rescaled). The "
      "map's permanent-effect device.", uses={'times': 1, 'per': 'character', 'reset': 'never'}),
    P('poi:skull', 'zone:np_square', 'story_device',
      "A skull on the mirror's plinth tells the story of the two necromancers (the source's long tale, A3's text) "
      "when clicked. One spot with the mirror."),
    P('poi:barrel', 'town:necropolis', 'device',
      "A barrel by the Warm Barrel's wall, beside (never before) its door: \"Food for the dead, keep warm.\" (the "
      "source's line). One spot with the tavern's door."),
    P('poi:mirror', 'zone:np_square', 'story_device',
      "The Mirror of Necropolis (4756): the Darkside mirror network (Kalindra's stage 4, A3's helper)."),
    P('poi:genie_pinnacle', 'zone:ash_waste', 'device', reached_by='off_road',
      behaviour="A genie's lamp on a basalt pinnacle between the moat and the north rim: a wish choice; greed is "
                "punished (the source's three B2 genies, moved)."),
    P('poi:genie_islet', 'water:pod_lake', 'device', reached_by='water',
      behaviour="A second lamp glinting on a black islet in Corak's lake: only by flight or lava walking past the lava "
                "dwellers (the lake's lure)."),
    P('poi:genie_crag', 'zone:east_peaks', 'device', reached_by='off_road',
      behaviour="A third lamp on a crag above the broken pyramid, among the griffins' perches."),
    P('poi:archers_chest', 'zone:archer_camp', 'chest',
      "The archers' strongbox in the chief's tent: their raiding loot (a chest); the camp's burn hook on the same "
      "spot (d6.archers_camp: \"You have discovered a barbarian camp. Destroy?\", D-49 change 5)."),
    P('poi:griffin_nest', 'zone:east_peaks', 'chest',
      "A griffin's nest on a crag east of the pass, a dead courier's satchel among the bones (a chest)."),
    P('poi:prospector', 'zone:south_peaks', 'chest',
      "A prospector dead at the boarded mine mouths, his pack of tools and stones (a chest)."),
    P('poi:ancient_locker', 'zone:ancient_field', 'chest',
      "An Ancient locker surfacing through the rock, its seal long dead (a chest; the Ancient kit's panel)."),
    P('poi:pilgrim_cart', 'zone:bone_road', 'chest',
      "A pilgrim's coffin-cart abandoned on the Bone Road: turned back at the gate without a pass (a chest)."),
    P('poi:spring_pilgrim', 'zone:hot_spring', 'chest',
      "A burned pilgrim's pack by the hot spring, who came for the waters across the waste (a chest)."),
    P('poi:fork_signpost', 'junction:ash_fork', 'signpost',
      "Ash Fork's signpost: \"North-west: Castle Alamar. East: Necropolis. South: Griffin Pass, Castleview.\""),
    P('poi:zone_sign', 'zone:pass_east', 'signpost',
      "The source's sign at the border pass: \"The Forbidden Zone.\" (B2(15,15)) verbatim, with A3's warning line "
      "under it (d6.zone_sign, D-49 change 9)."),
    P('poi:ambrose', 'zone:griffin_pass', 'npc',
      "Ambrose (5512), the Queen's Knight, by his tethered griffin: M24-M25 (\"Who sent you?\"), m25.flight from "
      "his topic. Not a point of interest (D-23 (1))."),
    P('poi:climbers_camp', 'zone:climbers_camp', 'dressing',
      "An empty climbers' camp: a tent, ropes and pitons drying on a line (D-49 change 1: no Freeda, no click)."),
    P('poi:travel_pyramid', 'zone:alamar_approach', 'device',
      "A small Ancient travel pyramid beside the Alamar road outside the moat's mouth (D-50 Q9): "
      "Xeen.travelPyramid(\"alamar_gate\") on click (to XD-17 Shangri-La once m30.done, else \"The moons are not "
      "aligned.\"); its arrival is entrance:xd17_pyramid, no spawn marker within 2,000."),
    P('poi:mine_mouths', 'zone:south_peaks', 'dressing', count=2,
      behaviour="Two boarded mine mouths of the Forbidden Zone mines beside DD-10C's adit (the source's other mines; "
                "dressing, no click)."),
]

LANDMARKS = [
    {'id': 'landmark:alamar', 'space': 'zone:alamar_plateau',
     'what': "Castle Alamar on its basalt mesa in the lava moat: dark teal steel and black stone, square towers, every "
             "window lit, cyan energy fields between its pylons; after M33 a smoking ruin",
     'seen_from': ['zone:griffin_pass', 'zone:ash_fork_flats', 'zone:pod_lake_shore', 'zone:west_waste',
                   'zone:ancient_field', 'zone:ash_waste']},
    {'id': 'landmark:corak_pod', 'space': 'zone:pod_lake_shore',
     'what': "Escape Pod 1 nose-up in the glowing lava lake, its scorched hull lit red from below",
     'seen_from': ['zone:griffin_pass', 'zone:ash_fork_flats', 'zone:bone_road', 'zone:alamar_approach']},
    {'id': 'landmark:sheltem_pod', 'space': 'zone:ancient_field',
     'what': "Escape Pod 2 upright in its crater among the Ancient plates, cold and sealed",
     'seen_from': ['zone:ancient_field', 'zone:alamar_approach']},
    {'id': 'landmark:necropolis', 'space': 'town:necropolis',
     'what': "Necropolis's walls and mausoleum domes under the east ridge, bone-white lamps lit all day",
     'seen_from': ['zone:pass_east', 'zone:bone_road', 'zone:pod_lake_shore', 'zone:east_peaks']},
    {'id': 'landmark:north_falls', 'space': 'zone:ash_waste',
     'what': "Alamar's moat spilling over the north rim: the Northern Lava Falls into the stars",
     'seen_from': ['zone:ash_waste', 'zone:alamar_plateau', 'zone:ancient_field']},
    {'id': 'landmark:west_falls', 'space': 'zone:west_waste',
     'what': "The Slag Run pouring over the west rim below Obelisk Knoll",
     'seen_from': ['zone:obelisk_knoll', 'zone:west_waste', 'zone:ash_waste']},
    {'id': 'landmark:ridge_tower', 'space': 'zone:east_ridge',
     'what': "A roofless watchtower of the dead on the east ridge above Necropolis, looking into D5 (no click)",
     'seen_from': ['town:necropolis', 'zone:bone_road', 'zone:pass_east']},
    {'id': 'landmark:cinder_cone', 'space': 'zone:west_waste',
     'what': "A cinder cone with a smoking vent beside the Alamar road, the cinder plains' one height (no click)",
     'seen_from': ['zone:ash_fork_flats', 'zone:west_waste', 'zone:alamar_approach']},
    {'id': 'landmark:broken_pyramid', 'space': 'zone:east_peaks',
     'what': "A broken travel pyramid in a high valley, its capstone fallen (the source's B2 pyramid; the hoard is "
             "D5's); no click",
     'seen_from': ['zone:east_peaks', 'zone:griffin_pass']},
]

SIGHTLINES = [
    {'id': 'view:arrival', 'from': 'zone:griffin_pass', 'to': ['landmark:alamar', 'landmark:corak_pod',
                                                               'landmark:north_falls'],
     'what': "Arrival from D1: the long mountain road tops Griffin Pass and the Forbidden Zone opens below: ash plains "
             "falling north, the red glow of Corak's lake right of centre with the pod standing in it, Castle Alamar "
             "far north on its mesa ringed by lava, the Ancient field's metal glinting to the right, the lava falls "
             "smoking at the rim, ash in the air; Ambrose's camp and griffin at the left."},
    {'id': 'view:signature', 'from': 'zone:bone_road', 'to': ['landmark:corak_pod', 'landmark:alamar'],
     'what': "The signature view from the Necropolis road on the lake's south-east shore: Corak's pod nose-up in the "
             "glowing lava lake, its hatch on the crust nearest, and beyond it across the moat Castle Alamar's lit "
             "walls and cyan energy fields, under the amber day band with ash in the air (WORLD_DESIGN 4: the crashed "
             "pods' lava glow)."},
]

SET_PIECES = [
    {'id': 'set:alamar', 'kind': 'scripted', 'spaces': ['zone:alamar_plateau', 'zone:alamar_approach'],
     'rule': "Castle Alamar's outside has two states: whole (every window lit, the energy fields up, the gate's "
             "m33.castle_door) until m33.done; then a ruin (model groups swapped: buckled plates, fallen towers, "
             "smoke, the fields dark), the gate rubble with the stair to FD-01 in its floor (m39.depths_door), the "
             "robots hidden on load after m33.done (m33.robots_gone, D-49 change 7; no refill rule).",
     'states': ['whole', 'ruin']},
    {'id': 'set:pod_lava', 'kind': 'scripted', 'spaces': ['zone:pod_crust'],
     'rule': "The lava round Corak's hatch: hot until m28.lava_cooled (111564), the hatch's fail line; then the lava "
             "there is black crust (a basalt face swapped in, the lava's damage off), the hatch opens (m29.pod_door).",
     'states': ['hot', 'cooled']},
    {'id': 'set:sheltem_pod', 'kind': 'scripted', 'spaces': ['zone:ancient_field'],
     'rule': "Sheltem's pod sealed with a line (\"The hatch is fused shut, and something inside is listening.\", A3) "
             "until DD-22 exists (phase 6).", 'states': ['sealed', 'open']},
]

STATES = [
    {'id': 'state:gate_shut', 'condition': {'not': {'item': 'necropolis_pass'}},
     'locks': ['building:np_guild', 'building:np_temple', 'building:np_market', 'building:np_embalmer',
               'building:np_tavern', 'building:np_houses'],
     'atmosphere': "Necropolis's gate shut to the passless: the dead on the walls watch the road.",
     'notes': "The houses are open from inside; only the gate checks the pass (A4's d6.yml). Town Portal and the "
              "mirror land inside the gate."},
    {'id': 'state:alamar_ruin', 'condition': {'qbit': 'alamar_destroyed'},
     'effects': ["Castle Alamar a smoking ruin; the energy fields dark; the stair to FD-01 in the gatehouse.",
                 "Darkside's sun whole again (Xeen.DarksideSkies reads m33.done)."]},
    {'id': 'state:lava_cooled', 'condition': {'qbit': 'lava_cooled'},
     'effects': ["The lava round Corak's hatch black and cool; the hatch opens."]},
]

HEIGHT_BANDS = [
    {'id': 'band:rim_sea', 'range': [0, 0], 'spaces': ['zone:rim', 'water:rim_sea']},
    {'id': 'band:lava', 'range': [1450, 1900], 'spaces': ['zone:pod_lake_shore', 'water:pod_lake',
                                                          'water:alamar_moat', 'zone:ash_fork_flats'],
     'notes': "Corak's lake 1,450; the moat 1,550; the flats 1,650-1,900."},
    {'id': 'band:waste', 'range': [1550, 2300], 'spaces': ['zone:ash_waste', 'zone:west_waste'],
     'partly': ['zone:bone_road']},
    {'id': 'band:plateau', 'range': [1800, 2400], 'spaces': ['zone:alamar_plateau']},
    {'id': 'band:field', 'range': [1700, 2900], 'spaces': ['zone:ancient_field']},
    {'id': 'band:town', 'range': [1600, 1950], 'spaces': ['town:necropolis', 'zone:bone_road']},
    {'id': 'band:peaks', 'range': [800, 3900], 'spaces': ['zone:south_peaks', 'zone:east_peaks',
                                                          'zone:griffin_pass', 'zone:mountain_road'],
     'notes': "D1's border row (1,100-1,700) at y 109, the peaks to 3,800 at y 96-104, Griffin Pass 2,450; D1's Sardaj pool 832 at x 80-87."},
    {'id': 'band:ridge', 'range': [1700, 3300], 'spaces': ['zone:east_ridge', 'zone:pass_east'],
     'notes': "The shared D5 border (edge_d5_d6.json)."},
]

PLAN = {
    'format': 0,
    'level': 'L1',
    'pitch': "Darkside's north-west corner, where the world ends north and west. A volcanic waste of grey ash and "
             "black basalt, cracked by lava, with the metal of something Ancient surfacing through the rock. In its "
             "middle Castle Alamar stands on a mesa in a moat of lava, every window lit, energy fields humming between "
             "its pylons; its lava spills over the rims into the stars and down a burning channel into a lake where "
             "Corak's escape pod stands nose-up, glowing. Sheltem's pod lies cold in the Ancient field to the north. "
             "East under the ridge, the walled Necropolis keeps its dead and its gate; south, the long mountain road "
             "from Castleview tops Griffin Pass, where Ambrose waits with a griffin. Ash falls.",
    'purpose': "Act V's trap and endgame map (party 48-51): Ambrose's flight to Blackfang (M25), Corak's pod (M29, "
               "M32), Castle Alamar and Sheltem (M33, DD-17), Necropolis and Sandro (Q-D23, DD-21; the pass from "
               "Q-D22), the north diamonds (Q-D7, DD-10C), the sixth obelisk; in phase 6 Sheltem's pod (DD-22) and the "
               "Alamar Depths under the ruin (M39, FD-01).",
    'mood': "Ash drifting through the amber light, the red underglow of lava on low cloud; the hiss and crack of "
            "crust; Alamar's hum and its lit windows watching; silence and bone-white lamps in Necropolis; wind on "
            "the pass.",
    'datum': 'water:rim_sea',
    'spaces': SPACES,
    'links': LINKS,
    'entrances': ENTRANCES,
    'critical_path': ['edge:south_end', 'zone:griffin_pass', 'junction:ash_fork', 'zone:pod_crust',
                      'zone:alamar_approach'],
    'goals': GOALS,
    'points_of_interest': POIS,
    'landmarks': LANDMARKS,
    'sightlines': SIGHTLINES,
    'set_pieces': SET_PIECES,
    'height_bands': HEIGHT_BANDS,
    'states': STATES,
    'landform': {
        'relief': "The southern border's peaks (2,800-3,800) along y 94-104 with Griffin Pass (2,450) at x 64, falling "
                  "south to D1's border row (1,100-1,700) and north to the ash flats (1,650-1,900); Corak's lava lake "
                  "(1,450) south-east of the middle; Alamar's mesa (to 2,300) in its lava moat (1,550) north-west of "
                  "it; the volcanic waste (1,550-2,100) to the north and west rims; the Ancient field (1,700-2,600) "
                  "rising north-east to the D5 ridge (to 3,300); Necropolis on a terrace (1,650) under the east "
                  "ridge; the border pass to D5 at 1,700. Inside the playable box the land spans about 1,100-3,800 "
                  "(D1's spring pool 832 at the border).",
        'height_range': [1100, 3800],
        'water': "No water: lava only (lavtyl, D-40): Corak's lake (about 230 cells), Alamar's moat (about 190), the "
                 "Burning Channel, the Slag Run and the Northern Lava Falls (about 40 cells).",
        'water_share': 0.07,
        'caps': [{'kind': 'ash', 'share': 0.35, 'where': "the waste, the cinder plains and the flats"},
                 {'kind': 'bare rock', 'share': 0.25, 'where': "the peaks, the east ridge, the mesa, the rim cliffs"},
                 {'kind': 'lava crust', 'share': 0.08, 'where': "round the lava"}],
        'rim': {'notes': "The world rim along the whole north (y 24) and west (x 24): a cliff of 1,500-2,000 down to "
                         "the stars; lava falls over the north rim at x 44 and the west rim at y 51. South (D1) and "
                         "east (D5) the land runs to the map edge; the roads run out to it."},
    },
    'atmosphere': "Sky xeendark1 (xeen_darkside_day; A3's Lua sets xeendark3 for Act V until M33, then xeendark1); "
                  "ash fall on 40 % of days (atmosphere.yml `ash`, A1's word, D-40 (9) 'also D6'); music 11 (A2). The hiss "
                  "and crack of lava near the lake and the moat; Alamar's low hum; wind on the pass; silence in "
                  "Necropolis.",
    'sketch': {'file': 'sketch.yml', 'grid': 512},
    'totals': {'hostiles_at_load': 110, 'encounter_areas': 6, 'spawn_markers': 42, 'outdoor_chests': 6,
               'points_of_interest': 28, 'dungeon_entrances': 6},
    'notes': "MU-3 for the phase 5 review (A6, 2026-11-20). Source geography: Darkside A1 (Castle Alamar, the waste "
             "and lava, the +2,500 HP waters), A2 (the southern border, the mines, the archer camp), B1 (Griffin Pass, "
             "Sheltem's pod, the +100 resistances well), B2 (Necropolis's gate, Corak's pod in lava, the "
             "genies, the broken pyramid, the Forbidden Zone sign) (MM5_DARKSIDE_CONTENT 4), moved where the edges "
             "and the hooks need: Griffin Pass to the top of D1's mountain road (A3/A4's 'south edge'). Written by "
             "level_generation/xeen_art/phase5/d6_brief.py; board level_generation/xeen_art/phase5/d6/board_d6.png. "
             "totals.points_of_interest is the render's census (measure.json).",
}

# ---------------------------------------------------------------------------------------------- project

PROJECT = {
    'format': 0,
    'id': 'xeen_d6',
    'name': 'The Forbidden Zone',
    'world': 'xeen',
    'kind': 'outdoor',
    'profile': 'odm',
    'map_code': 'D6',
    'units': {'plan_grid': 512},
    'extent': {'terrain_cells': 128},
    'map_stats': {
        'id': 9113,
        'encounter_chance': 10,
        'treasure_level': 5,
        'trap_dice': 8,
        'perception_difficulty': 8,
        'refill_days': 672,
        'music': 11,
        'environment': 'mountains',
        'lock_difficulty': 15,
        'slots': [
            {'monster': 'Xeen Eye', 'tier': 2, 'per_marker': [1, 3], 'weight': 40},
            {'monster': 'Xeen Roc', 'tier': 5, 'per_marker': [1, 3], 'weight': 38},
            {'monster': 'Xeen Robot', 'tier': 1, 'per_marker': [1, 3], 'weight': 22},
        ],
    },
    'neighbours': [
        {'id': 'edge:south', 'to': 'xeen_d1.odm', 'kind': 'edge', 'side': 'south', 'days': 5, 'arrival_side': 'north',
         'approach': "The long mountain road from D1's north edge at x 64, up to Griffin Pass.",
         'notes': "D1 Castleview Vale (installed): its mountain road's valley runs out to its y 0 at x 64 (rim [59, "
                  "70] level, the road 1,550 at (64, 19)), sealed with a sign until D6 exists. D1's arrival from D6 is "
                  "its north road's end; D6's south arrival is entrance:south_road (64, 105) facing north. D6's y 109 "
                  "row repeats D1's installed y 19 row cell for cell (edge_d1.json). A2 writes the travel row."},
        {'id': 'edge:east', 'to': 'xeen_d5.odm', 'kind': 'edge', 'side': 'east', 'days': 5, 'arrival_side': 'west',
         'listed_only': True,
         'approach': "The Forbidden Zone's border pass from D5's west edge at y 64.",
         'notes': "D5 Desert of Doom (A6, phase 5, planned beside this): the shared border edge_d5_d6.json (A6's "
                  "lead), the pass at y 64 at 1,700 over y 62-66; D6's x 109 column carries its heights (edge_d5.json). "
                  "D5's arrival from D6 at about (23, 64) facing east; D6's at entrance:east_pass (105, 64) facing west."},
        {'id': 'mirror:darkside', 'to': 'mirror', 'kind': 'mirror',
         'notes': "The Mirror of Necropolis (house 4756, a thing on the square): the Darkside network (Kalindra's stage "
                  "4, A3's mirror helper), qbit 119011, arrival necropolis_gate."},
        {'id': 'door:dd17', 'to': 'xeen_dd17.blv', 'kind': 'door',
         'arrival_hint': "DD-17's entrance hall (L1); its arrival hook (m33.arrival) refuses a party without the Soul "
                         "Box and moves it back outside the gate.",
         'notes': "DD-17 Castle Alamar (A8, phase 5): the double gate on the approach (two leaves). Until m33.done; "
                  "after it the gate is rubble (set:alamar). Sealed with a line until DD-17 exists."},
        {'id': 'door:fd01', 'to': 'xeen_fd01.blv', 'kind': 'door', 'listed_only': True,
         'condition': {'qbit': 'alamar_destroyed'},
         'arrival_hint': "The foot of the stair, FD-01's first hall (the statue's boast).",
         'notes': "FD-01 Alamar Depths (phase 6, M39): the stair in the ruin's gatehouse, m39.depths_door (the Cube of "
                  "Power). Shown only in the ruin state; sealed until FD-01 exists."},
        {'id': 'door:dd16', 'to': 'xeen_dd16.blv', 'kind': 'door', 'condition': {'qbit': 'lava_cooled'},
         'arrival': 'entrance:d6_hatch',
         'arrival_hint': "entrance:d6_hatch: DD-16's airlock about 192 inside the hatch, facing into the pod (D-47).",
         'notes': "DD-16 Corak's Pod (A7, phase 5; D-47 approved): m29.pod_door names arrival: entrance:d6_hatch. "
                  "DD-16's way out lands on the crust about 384 before the hatch, facing away from it (south-east, "
                  "toward the shore): (74, 70.75) facing s at L1; A6 measures it on the crust at L3."},
        {'id': 'door:dd22', 'to': 'xeen_dd22.blv', 'kind': 'door', 'listed_only': True,
         'arrival_hint': "Inside Sheltem's pod's hatch.",
         'notes': "DD-22 Sheltem's Pod (phase 6, optional lore): sealed with a line until then (set:sheltem_pod)."},
        {'id': 'door:dd21', 'to': 'xeen_dd21.blv', 'kind': 'door',
         'arrival_hint': "At the foot of the crypt stair in the Necropolis Sewer.",
         'notes': "DD-21 Necropolis Sewer (phase 5, Q-D23): the crypt stair in Necropolis's south-east corner, inside "
                  "the walls (the pass already shown). Two grille leaves."},
        {'id': 'door:dd10c', 'to': 'xeen_dd10c.blv', 'kind': 'door',
         'arrival_hint': "DD-10C's start (0, 192, 0), facing north (A8's L3 project).",
         'notes': "DD-10C Gemstone Mines, north pocket (A8, built in scratch; installed in phase 5, D-27): the north "
                  "adit; DD-10C's exit:d6_adit returns outside the adit facing away from it (A6 measures the point at "
                  "L3; D6_ARRIVAL in A8's gen.py)."},
        {'id': 'scripted:pyramid', 'to': 'xeen_xd17.blv', 'kind': 'scripted', 'listed_only': True,
         'notes': "D-50 Q9: the travel pyramid outside Alamar's gate, Xeen.travelPyramid(\"alamar_gate\") to XD-17 "
                  "Shangri-La (PyramidArrivals.shangrila, A3); XD-17's pyramid lands here at entrance:xd17_pyramid."},
        {'id': 'scripted:griffin', 'to': 'xeen_dd14.blv', 'kind': 'scripted', 'listed_only': True,
         'notes': "M25: Ambrose's flight (A3's m25.flight from his topic at Griffin Pass) moves the party to DD-14's "
                  "landing, entrance:d6_griffin (A8). D-42: afterwards he waits on the walls and flies both ways from "
                  "D4's gate; no return to D6 by griffin."},
    ],
    'qbits': {
        'lava_cooled': 111564,        # m28.lava_cooled (A3)
        'm25_done': 111503,           # m25.done
        'alamar_inside': 111660,      # m33.inside
        'alamar_destroyed': 111662,   # m33.done
        'obelisk_dark_6': 115055,     # obelisks.d6
        'mirror_necropolis': 119011,
    },
    'items': {'necropolis_pass': 12336},
    'rules': {'weather': 'ash', 'respawn': 'entrance:necropolis_gate',
              'town_portal_anchor': 'entrance:necropolis_gate',
              'rim': {'cliff_x': RIM_WEST_X, 'cliff_y': RIM_NORTH_Y, 'fall': 'death', 'sides': ['north', 'west']}},
    'notes': "D6 The Forbidden Zone, MU-3 plan for the phase 5 review (A6, 2026-11-20). No geometry until a decider has "
             "approved the board. Plan: plan.yml; to-scale layout: sketch.yml; air: atmosphere.yml; NOTES.md; "
             "drawings and board: level_generation/xeen_art/phase5/d6/. Sky xeendark1, ash fall. Written by "
             "level_generation/xeen_art/phase5/d6_brief.py.",
}

ATMOSPHERE = {
    'format': 0,
    'sky': 'xeendark1',
    'weather': {},
    'ash': 40,
    'notes': "Darkside's amber day (xeendark1; A3's Lua sets the sun's stage on load: xeendark3 in Act V until M33). "
             "Ash fall on 40 % of days (D-40 (9): A1's `ash` word, 'also D6'). No rain or snow.",
}

# ---------------------------------------------------------------------------------------------- sketch

# key heights: [x, y, h, note]
POINTS_H = [
    # the south: D1's border row at y 109 (added below from the installed map), the peaks, the pass
    [64, 106, 1800, "the D1 arrival, climbing"], [64, 102, 2150, None], [63, 99, 2350, None],
    [64, 96, 2450, "Griffin Pass: the Forbidden Zone opens below"], [61, 95, 2500, "Ambrose's camp"],
    [65, 92, 2250, None], [66, 88, 1900, None], [66, 85, 1780, "Ash Fork"],
    [56, 98, 3100, None], [50, 100, 3650, "the western peaks"], [46, 97, 2700, "DD-10C's north adit"],
    [40, 100, 3500, None], [33, 101, 3400, None], [28, 98, 2800, None], [38, 96, 2650, "the boarded mines"],
    [52, 95, 2800, None], [44, 93, 2400, None], [27, 104, 2600, None], [52, 104, 2700, None], [40, 105, 2500, None],
    [72, 98, 3200, None], [78, 101, 3800, "the eastern peaks"], [84, 98, 2700, "the broken pyramid's valley"],
    [88, 101, 3500, "the genie crag"], [94, 99, 3400, None], [100, 101, 3000, None], [76, 94, 2600, "the griffin nest"],
    [84, 105, 2300, "the Sardaj cliff over D1's spring"], [72, 105, 2500, None], [96, 105, 2600, None],
    [104, 96, 2900, None], [92, 94, 2300, None],
    # Ash Fork, the flats and Corak's lake
    [60, 82, 1800, None], [72, 82, 1750, None], [80, 79, 1750, None], [83, 72, 1600, "the signature camera"], [78, 86, 1800, None],
    [77, 72, 1480, "the crust before the hatch"], [72, 67, 1450, "Escape Pod 1 (nose-up)"],
    [66, 63, 1520, "the genie islet"], [84, 66, 1800, None], [83, 58, 1900, None], [60, 76, 1700, None],
    [58, 70, 1750, None], [62, 55, 1700, None],
    # Alamar
    [51, 46, 2300, "Castle Alamar"], [46, 43, 2200, None], [56, 43, 2200, None], [47, 51, 2150, None],
    [55, 51, 2150, None], [51, 55, 2050, "the gate"], [51, 59, 1900, "the approach"], [51, 63, 1800, None],
    [44, 54, 1950, None], [58, 54, 1950, None],
    # the volcanic waste
    [30, 30, 1800, "the hot spring"], [36, 40, 2200, "the genie pinnacle"], [44, 28, 1650, "the north falls' lip"],
    [30, 46, 1750, None], [33, 55, 1800, None], [56, 28, 1800, None], [28, 38, 1700, None], [40, 30, 1700, None],
    # the cinder plains
    [30, 62, 2050, "Obelisk Knoll"], [26, 51, 1600, "the Slag Run's fall"], [40, 66, 1750, None],
    [34, 86, 1950, "the archers' camp"], [28, 76, 1850, None], [42, 78, 1800, None], [48, 72, 1750, None],
    [50, 84, 1900, None], [36, 72, 1800, None], [49, 80, 2250, "the cinder cone"],
    # the Ancient field
    [78, 38, 2000, "Sheltem's pod's crater"], [70, 30, 2000, None], [86, 30, 2300, None], [96, 28, 2600, None],
    [101, 31, 2700, "the Well of Warding"], [88, 44, 2100, "the Ancient locker"], [96, 42, 2400, None],
    [72, 46, 1850, None], [80, 50, 1900, None], [92, 52, 2100, None], [100, 50, 2400, None], [104, 40, 2800, None],
    # Necropolis, the Bone Road, the pass
    [91, 82, 1650, "Necropolis's square"], [85, 86, 1650, None], [97, 86, 1660, None], [91, 72, 1700, "Bone Fork"],
    [86, 69, 1720, "the pilgrim's cart"], [100, 69, 1800, "the climbers' camp"], [105, 64, 1700, "the D5 arrival"],
    [98, 65, 1720, None], [102, 78, 2200, None], [102, 88, 2400, None], [104, 81, 2500, "the ridge watchtower"], [94, 60, 1900, None],
]

BANDS = [
    ('band:rim_sea', 'zone:rim', RIM_POLY),
    ('band:waste', 'zone:ash_waste', SPACES_POLY['zone:ash_waste']),
    ('band:plateau', 'zone:alamar_plateau', SPACES_POLY['zone:alamar_plateau']),
    ('band:field', 'zone:ancient_field', SPACES_POLY['zone:ancient_field']),
    ('band:lava', 'zone:pod_lake_shore', SPACES_POLY['zone:pod_lake_shore']),
    ('band:waste', 'zone:west_waste', SPACES_POLY['zone:west_waste']),
    ('band:peaks', 'zone:south_peaks', SPACES_POLY['zone:south_peaks']),
    ('band:peaks', 'zone:east_peaks', SPACES_POLY['zone:east_peaks']),
    ('band:peaks', 'zone:griffin_pass', SPACES_POLY['zone:griffin_pass']),
    ('band:peaks', 'zone:mountain_road', SPACES_POLY['zone:mountain_road']),
    ('band:lava', 'zone:ash_fork_flats', SPACES_POLY['zone:ash_fork_flats']),
    ('band:town', 'town:necropolis', NECRO),
    ('band:town', 'zone:bone_road', SPACES_POLY['zone:bone_road']),
    ('band:ridge', 'zone:east_ridge', SPACES_POLY['zone:east_ridge']),
    ('band:ridge', 'zone:pass_east', SPACES_POLY['zone:pass_east']),
]

ROADS = [
    {'link': 'link:mountain_road', 'line': [[64, 109], [64, 104], [63.5, 100], [64, 96.5], [65, 92.5], [66, 88.5],
                                            [66, 85]], 'width': 'road', 'surface': 'road_pebbles'},
    {'link': 'link:alamar_road', 'line': [[66, 85], [62, 81], [58.5, 76.5], [56, 71], [54, 66.5], [52, 62],
                                          [51.5, 57]], 'width': 'road', 'surface': 'road_flagstone'},
    {'link': 'link:necropolis_road', 'line': [[66, 85], [71, 82.5], [76, 80], [80.5, 78], [84, 74.5], [87.5, 71.5],
                                              [91, 71]], 'width': 'road', 'surface': 'road_pebbles'},
    {'link': 'link:pass_road', 'line': [[109, 64], [104, 64], [99, 65.5], [95, 68], [91, 71]], 'width': 'road',
     'surface': 'road_pebbles'},
    {'link': 'link:gate_lane', 'line': [[91, 71], [91, 74], [91, 78]], 'width': 'road', 'surface': 'road_flagstone'},
    {'link': 'link:hatch_path', 'line': [[79, 78.5], [78, 75], [76.5, 72]], 'width': 'lane', 'surface': 'gravel'},
    {'link': 'link:adit_track', 'line': [[66, 85], [60, 87], [54, 89], [48, 91], [44, 92], [42, 90], [37, 89],
                                         [40, 92.5], [44, 94.5], [46.5, 96.5]], 'width': 'lane', 'surface': 'gravel'},
    {'link': 'link:obelisk_path', 'line': [[54, 66.5], [47, 65.5], [40, 64.5], [34, 63], [30.5, 62.5]],
     'width': 'lane', 'surface': 'gravel'},
    {'link': 'link:spring_track', 'line': [[40, 64.5], [35, 60], [32, 54.5], [31, 48], [30, 41], [30, 35],
                                           [30.5, 31]], 'width': 'lane', 'surface': 'gravel'},
    {'link': 'link:field_track', 'line': [[80.5, 78], [83, 70], [84.5, 63], [82, 56], [79, 49], [78, 42],
                                          [78, 39.5]], 'width': 'lane', 'surface': 'gravel'},
    {'link': 'link:rim_track', 'line': [[78, 39.5], [82, 36], [88, 33], [94, 31.5], [100, 31]], 'width': 'lane',
     'surface': 'gravel'},
]

# plots: (building, index, at, facing)
PLOTS = [
    ('building:np_guild', None, [84, 76], 'e'),
    ('building:np_market', None, [96, 76], 'w'),
    ('building:np_embalmer', None, [96, 80], 'w'),
    ('building:np_tavern', None, [84, 80], 'e'),
    ('building:np_temple', None, [89, 82], 'n'),
    ('building:np_houses', 1, [94, 83], 'w'),        # the Necromancers' House
    ('building:np_houses', 2, [90, 87], 'n'),        # Count Velkor's Crypt
    ('building:np_houses', 3, [84, 87], 'n'),        # the Quiet Tomb
    ('building:np_houses', 4, [87, 87], 'n'),        # the Trapsmith's Vault
    ('building:np_houses', 5, [94, 87], 'n'),        # the Gravedigger's
    ('building:np_houses', 6, [84, 84], 'e'),        # the Weeping Mausoleum
]

PTS = [
    ('entrance:south_road', [64, 105], 'n'), ('entrance:east_pass', [105, 64], 'w'),
    ('entrance:necropolis_gate', [91, 77], 's'), ('entrance:np_gate', [91, 74], 'n'),
    ('entrance:dd17_gate', [51, 55], 's'), ('entrance:fd01_stair', [51, 55], 's'),
    ('entrance:dd16_hatch', [74, 70], 'n'), ('entrance:dd22_hatch', [78, 40], 's'),
    ('entrance:dd21_stair', [98, 88], 'n'), ('entrance:dd10c_adit', [46, 97], 'n'),
    ('junction:ash_fork', [66, 85], None), ('junction:bone_fork', [91, 71], None),
    ('poi:obelisk', [30, 62], None), ('poi:fountain_resilience', [30, 30], None),
    ('poi:warding_well', [101, 31], None), ('poi:books', [89, 79], None), ('poi:skull', [92, 78], None),
    ('poi:mirror', [92, 78], None), ('poi:barrel', [87, 81], None),
    ('poi:genie_pinnacle', [36, 40], None), ('poi:genie_islet', [66, 63], None), ('poi:genie_crag', [88, 101], None),
    ('poi:archers_chest', [35, 86], None), ('poi:griffin_nest', [76, 94], None), ('poi:prospector', [40, 96], None),
    ('poi:ancient_locker', [88, 44], None), ('poi:pilgrim_cart', [86, 69], None), ('poi:spring_pilgrim', [32, 32], None),
    ('poi:fork_signpost', [66.5, 85.5], None), ('poi:zone_sign', [102, 64.5], None),
    ('poi:ambrose', [61, 95], None), ('poi:climbers_camp', [100, 69], None),
    ('poi:travel_pyramid', [56, 62], None), ('entrance:xd17_pyramid', [54, 62], 'n'),
    ('poi:mine_mouths', [38, 96], None), ('poi:mine_mouths', [54, 97], None),
    ('landmark:alamar', [51, 46], None), ('landmark:corak_pod', [72, 67], None),
    ('landmark:sheltem_pod', [78, 38], None), ('landmark:necropolis', [91, 82], None),
    ('landmark:north_falls', [44, 24], None), ('landmark:west_falls', [24, 51], None),
    ('landmark:broken_pyramid', [84, 98], None), ('landmark:cinder_cone', [49, 80], None),
    ('landmark:ridge_tower', [104, 81], None),
]

ENC = {   # encounter areas: id, markers, slot, polygon, notes
    'pop:field_gazers': (17, 1, [[64, 26], [104, 26], [106, 40], [104, 55], [94, 57], [84, 55], [72, 52], [66, 47],
                                 [66, 36]],
                         "E1: Floating Eyes 40, Terrible Eyes 50, Gamma Gazers 65 (Dif 2) over the Ancient field and "
                         "Sheltem's crater; the first fight from D5 at the field's south-east corner."),
    'pop:alamar_robots': (9, 3, [[42, 37], [60, 37], [62, 46], [60, 56], [58, 64], [46, 64], [42, 56], [39, 47]],
                          "E2: Patrols 50 (Annihilators 62, Autobots 75 rare; Dif 1) on the plateau and the approach; "
                          "off after M33 (set:alamar)."),
    'pop:west_griffins': (8, 2, [[26, 92], [44, 92], [55, 91], [56, 99], [57, 107], [26, 107]],
                          "E4a: Griffins 48, Rocs 38, a Vulture Roc 30 now and then (Dif 5) on the western peaks round "
                          "the mines."),
    'pop:east_griffins': (8, 2, [[70, 93], [80, 93], [100, 95], [106, 96], [106, 107], [70, 107]],
                          "E4b: the same on the eastern peaks; the first fight from D1 (the pass is clear)."),
}

AREAS = [
    *[{'id': aid, 'count': c, 'slot': s, 'polygon': poly, 'notes': n} for aid, (c, s, poly, n) in ENC.items()],
    {'id': 'pop:lava_dwellers', 'count': 14, 'slot': 3, 'kind': 'encounter',
     'polygon': [[60, 55], [70, 53], [79, 57], [82, 63], [79, 66], [71, 68], [70, 76], [64, 75], [60, 68]],
     'notes': "E3: 14 placed elementals (the lava dwellers' stand-in) on the lake's crust and the Burning Channel; see "
              "actors."},
    {'id': 'pop:archers', 'count': 12, 'slot': 3, 'kind': 'encounter',
     'polygon': [[30, 83], [39, 83], [39, 89], [30, 89]],
     'notes': "E6: the archers' camp, 12 placed (new tiers asked of A2)."},
    {'id': 'zone:mountain_road', 'kind': 'keep_clear', 'polygon': [[59, 92], [69, 92], [69, 109], [59, 109]],
     'notes': "The D1 arrival and Ambrose's camp at Griffin Pass."},
    {'id': 'zone:pass_east', 'kind': 'keep_clear', 'polygon': [[96, 59], [109, 59], [109, 73], [96, 73]],
     'notes': "The D5 arrival and the climbers' camp."},
    {'id': 'town:necropolis', 'kind': 'keep_clear', 'polygon': [[77, 69], [105, 69], [105, 95], [77, 95]],
     'notes': "Necropolis and its buffer (2,500 round the doors)."},
    {'id': 'zone:hot_spring', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:hot_spring']},
    {'id': 'zone:obelisk_knoll', 'kind': 'keep_clear', 'polygon': SPACES_POLY['zone:obelisk_knoll']},
    {'id': 'zone:pod_crust', 'kind': 'keep_clear', 'polygon': [[73, 68], [80, 70], [81, 77], [74, 76]],
     'notes': "The hatch's crust and DD-16's way out."},
    {'id': 'zone:ash_fork_flats', 'kind': 'keep_clear', 'polygon': [[60, 80], [72, 80], [72, 90], [60, 90]],
     'notes': "Ash Fork: quiet."},
    {'id': 'zone:south_peaks', 'kind': 'keep_clear', 'polygon': [[42, 93], [50, 93], [50, 101], [42, 101]],
     'notes': "D-49 change 3: no spawn marker within 2,000 of DD-10C's return point outside the adit."},
    {'id': 'zone:alamar_approach', 'kind': 'keep_clear', 'polygon': [[50, 58], [58, 58], [58, 66], [50, 66]],
     'notes': "D-50 Q9: no spawn marker within 2,000 of the travel pyramid's arrival."},
]

ACTORS = [
    {'monster': '11620', 'at': [63, 58], 'count': 3, 'spread': 2, 'group': 1, 'hostile': True,
     'notes': "Lesser Elementals 55 at the Burning Channel's mouth (the lava dwellers' stand-in, A7's DD-16 choice): "
              "home radius on the crust, never on the roads."},
    {'monster': '11620', 'at': [63, 70], 'count': 3, 'spread': 2, 'group': 2, 'hostile': True,
     'notes': "Lesser Elementals 55 on the lake's west shore, by the Alamar road's view."},
    {'monster': '11621', 'at': [64, 72], 'count': 1, 'spread': 0, 'group': 2, 'hostile': True,
     'notes': "An Elemental 62 with them."},
    {'monster': '11620', 'at': [76, 58], 'count': 3, 'spread': 2, 'group': 3, 'hostile': True,
     'notes': "Lesser Elementals 55 on the lake's north shore."},
    {'monster': '11621', 'at': [80, 64], 'count': 1, 'spread': 0, 'group': 3, 'hostile': True},
    {'monster': '11620', 'at': [67, 61], 'count': 2, 'spread': 1, 'group': 4, 'hostile': True,
     'notes': "Two round the genie islet (the lure)."},
    {'monster': '11621', 'at': [65, 72], 'count': 1, 'spread': 0, 'group': 4, 'hostile': True,
     'notes': "An Elemental 62 on the south-west shore: its home and radius stay 2,500 clear of DD-16's way out "
              "(D-49 change 4)."},
    {'monster': '11104', 'at': [34, 86], 'count': 9, 'spread': 2, 'group': 5, 'hostile': True,
     'notes': "Barbarian Archers 44 (A2's 11104, faction xeen_barbarians_archers; D-49 Q3)."},
    {'monster': '11105', 'at': [35, 85], 'count': 3, 'spread': 1, 'group': 5, 'hostile': True,
     'notes': "Archer Chiefs 50 (A2's 11105)."},
    {'monster': 'Peasant', 'npc': 5512, 'at': [61, 95], 'count': 1, 'spread': 0, 'group': 6, 'hostile': False,
     'notes': "Ambrose (talking actor 5512) at his camp by the griffin (M25); hidden on load after m25.done "
              "(m25.camp_gone, D-49 change 6)."},
    {'monster': '11913', 'at': [62, 96], 'count': 1, 'spread': 0, 'group': 6, 'hostile': False,
     'notes': "The Tethered Griffin (A2's 11913: peaceful, placed-only, immobile, not counted); hidden with Ambrose."},
]

VIEWS = [
    {'id': 'view:arrival', 'at': [64, 96], 'height': 180, 'look': [62, 52],
     'purpose': "MU-4 arrival view: from Griffin Pass at the top of the mountain road, looking north over the "
                "Forbidden Zone: the road falling to Ash Fork, the ash flats, Corak's lava lake glowing right of "
                "centre with the pod in it, Castle Alamar far north on its mesa ringed by lava, the Ancient field's "
                "metal at the right, the Northern Lava Falls smoking at the rim, ash in the air (Ambrose's camp is "
                "beside the camera, out of frame)."},
    {'id': 'view:signature', 'at': [82, 72], 'height': 180, 'look': [61, 58],
     'purpose': "MU-4 signature view (about 60 degrees): from the lake's east shore by the Necropolis road, looking "
                "north-west: Corak's escape pod nose-up in the glowing lava lake left of centre, "
                "its hatch on the crust nearest, and beyond the lake and the moat Castle Alamar's lit walls and energy "
                "fields on their mesa right of centre, under the amber day band with ash falling."},
]


def border_points():
    """Height points along the two shared borders: D1's row at y 109 (every 3 cells, and every cell at the road
    and the Sardaj pool) and the D5 column at x 109 (every 3 cells, and every cell over the pass)."""
    row, col = d1_row(), d5_column()
    out = []
    xs = sorted(set(list(range(25, 109, 3)) + list(range(60, 69)) + list(range(80, 89))))
    for x in xs:
        if x < 107:
            out.append([x, BORDER, row[x], "D1's installed y 19 row" if x == 64 else None])
    ys = sorted(set(list(range(25, 106, 3)) + list(range(60, 69)) + [106, 107, 108, 109]))
    for y in ys:
        note = "edge_d5_d6.json (the pass)" if y == 64 else None
        if y == BORDER:
            note = "the corner: edge_d5_d6.json = D1's installed (109, 19) (D-49 Q6)"
        out.append([BORDER, y, col[y], note])
    return out


SKETCH = {
    'format': 0,
    'grid': 512,
    'map_cells': 128,
    'notes': "D6 The Forbidden Zone, MU-3 to-scale plan (A6, 2026-11-20), for the phase 5 review: composition, scale "
             "and density only. Cells [x, y], x east, y south. Heights above the stars below the rims (0): Corak's "
             "lava lake 1,450, Alamar's moat 1,550 and its mesa to 2,300, the waste 1,550-2,100, the Ancient field to "
             "2,700, Necropolis 1,650, the border pass 1,700, the southern peaks to 3,400 with Griffin Pass 2,450; "
             "D1's border row at y 109 and the D5 file's column at x 109. Lava is lavtyl (D-40), never water. Written "
             "by level_generation/xeen_art/phase5/d6_brief.py. The later L3 adds plots' detail, ground, scatter and "
             "structures (Alamar and its ruin, the pods, the walls).",
    'frame': {
        'playable': [19, 19, 90, 90],
        'edges': [
            {'side': 'south', 'span': [59, 70], 'neighbour': 'edge:south',
             'notes': "The mountain road runs out to y 127 at x 64 (D1's north edge, its rim [59, 70] level)."},
            {'side': 'east', 'span': [60, 68], 'neighbour': 'edge:east',
             'notes': "The pass road runs out to x 127 at y 64 (edge_d5_d6.json: 1,700 over y 62-66)."},
        ],
        'rim': [
            {'side': 'north', 'form': 'level', 'height': 0, 'meet': 1,
             'notes': "The world rim: the land ends in a cliff at y 24; below, water at 0 stands for the stars. The "
                      "Northern Lava Falls pour over it at x 44."},
            {'side': 'west', 'form': 'level', 'height': 0, 'meet': 1,
             'notes': "The world rim: the cliff at x 24 (D1's west rim continues); the Slag Run falls over it at y "
                      "51."},
            {'side': 'south', 'span': [0, 24], 'form': 'level', 'height': 0, 'meet': 1,
             'notes': "D1's west rim."},
            {'side': 'south', 'span': [24, 59], 'form': 'ridge', 'height': [1200, 1600], 'floor': 1100, 'crest': 10,
             'roughness': 80,
             'notes': "D6's picture of D1: the vale's north end, 1,100-1,600 (D1's own north strip pictures D6's "
                      "peaks)."},
            {'side': 'south', 'span': [59, 70], 'form': 'level', 'height': 1550, 'meet': 6,
             'notes': "D1's mountain road valley (D1's rim [59, 70]; the road 1,550 at (64, 19))."},
            {'side': 'south', 'span': [70, 80], 'form': 'ridge', 'height': [1300, 1550], 'floor': 1200, 'crest': 8,
             'roughness': 80, 'notes': "D1's north vale."},
            {'side': 'south', 'span': [80, 88], 'form': 'level', 'height': 832, 'meet': 3,
             'notes': "D1's Sardaj spring pool (832) under the cliff: D6's border row drops to it."},
            {'side': 'south', 'span': [88, 100], 'form': 'ridge', 'height': [1100, 1500], 'floor': 1050,
             'crest': 8, 'roughness': 80, 'notes': "D1's north-east vale."},
            {'side': 'south', 'span': [100, 128], 'form': 'ridge', 'height': [1800, 2200], 'floor': 1600,
             'crest': 8, 'roughness': 100, 'notes': "D1's Gemstone foothills (and D2's corner)."},
            {'side': 'east', 'span': [0, 24], 'form': 'level', 'height': 0, 'meet': 1,
             'notes': "The north rim's east end (D5's north rim also y 24)."},
            {'side': 'east', 'span': [24, 58], 'form': 'ridge', 'height': [2600, 3300], 'floor': 2200, 'crest': 10,
             'roughness': 120, 'notes': "D5's north-west highlands (the shared ridge, edge_d5_d6.json)."},
            {'side': 'east', 'span': [58, 70], 'form': 'level', 'height': 1700, 'meet': 6,
             'notes': "The Forbidden Zone's border pass, open to D5 (edge_d5_d6.json)."},
            {'side': 'east', 'span': [70, 128], 'form': 'ridge', 'height': [2500, 3000], 'floor': 2100, 'crest': 10,
             'roughness': 120, 'notes': "D5's western ridge south of the pass."},
        ],
        'edge': {'height': 1700, 'north': 0, 'west': 0},
    },
    'heights': {
        'bands': [{'band': b, 'space': s, 'polygon': poly} for b, s, poly in BANDS],
        'points': None,      # filled in main(): POINTS_H + the border points
        'cliffs': [
            {'line': [[128, RIM_NORTH_Y], [RIM_WEST_X, RIM_NORTH_Y], [RIM_WEST_X, 128]], 'drop': 1600, 'down': 'right',
             'notes': "The world rim, north then west (drawn east to west and north to south, the low side outward); "
                      "the lava falls over it at (44, 24) and (24, 51)."},
            {'line': [[79, 107], [84, 105.5], [89, 107]], 'drop': 1300, 'down': 'right',
             'notes': "The Sardaj cliff: the peaks' south face down to D1's spring pool at the border."},
            {'line': [[42, 58], [39, 50], [40, 42], [46, 37], [52, 35], [58, 37], [62, 44], [62, 52], [60, 56]],
             'drop': 500, 'down': 'left',
             'notes': "Alamar's mesa: its cliffs into the moat (drawn round the mesa clockwise, the moat outside)."},
        ],
        'ridges': [
            {'line': [[27, 101], [36, 100], [44, 99], [52, 100], [58, 98]], 'height': 3300, 'width': 2, 'slope': 4,
             'notes': "The southern border's crest west of the pass."},
            {'line': [[70, 98], [78, 100], [88, 101], [98, 100], [106, 98]], 'height': 3400, 'width': 2, 'slope': 4,
             'notes': "The crest east of the pass, on to the D5 ridge."},
        ],
    },
    'water': {
        'bodies': [
            {'id': 'water:rim_sea', 'kind': 'sea', 'level': 0, 'polygon': RIM_POLY,
             'notes': "Below the rim: stands for the stars."},
            {'id': 'water:pod_lake', 'kind': 'lake', 'level': POD_LAKE_LEVEL, 'polygon': POD_LAKE,
             'tile_set': 'lavtyl',
             'notes': "Corak's lava lake (D-40: the lava tile set, never water). The pod and the genie islet are height "
                      "points inside it (an islet in lava is a height point)."},
            {'id': 'water:alamar_moat', 'kind': 'lake', 'level': MOAT_LEVEL, 'polygon': MOAT, 'tile_set': 'lavtyl',
             'notes': "Alamar's moat: a horseshoe of lava round the mesa, open to the south (the approach)."},
        ],
        'rivers': [
            {'id': 'water:burning_channel', 'line': [[63, 53], [64.5, 55.5], [66, 58]], 'width_cells': 2,
             'tile_set': 'lavtyl', 'notes': "Lava from the moat's east arm down into Corak's lake (1,550 to 1,450)."},
            {'id': 'water:slag_run', 'line': [[36, 48], [31, 50], [27, 51], [24, 51]], 'width_cells': 1.5,
             'tile_set': 'lavtyl', 'notes': "Lava from the moat's west arm to the west rim, where it falls."},
            {'id': 'water:north_falls', 'line': [[46, 34], [45, 30], [44, 26], [44, 24]], 'width_cells': 1.5,
             'tile_set': 'lavtyl', 'notes': "Lava from the moat's north arm over the north rim (the Northern Lava "
                                            "Falls)."},
        ],
    },
    'roads': ROADS,
    'districts': [
        {'space': 'town:necropolis', 'polygon': NECRO,
         'plots': [dict({'building': b, 'at': at, 'facing': f, 'door_to': 'zone:np_square'},
                        **({'index': i} if i else {})) for b, i, at, f in PLOTS],
         'notes': "A4's d6.yml: the guild 4751 and the tavern 4755 west of the square, the Grave Market 4753 and the "
                  "Embalmer 4754 east, the Temple of the Dead 4752 south, six tombs and mausoleums 4757-4762 along "
                  "the south lanes; the mirror 4756 on the square with the skull; the Books of the Dead at the "
                  "square's west edge; DD-21's crypt stair in the south-east corner; one gate in the north wall."},
        *[{'space': s, 'polygon': SPACES_POLY[s]} for s in SPACES_POLY if s not in ('town:necropolis', 'zone:rim')],
        {'space': 'zone:rim', 'polygon': RIM_POLY},
    ],
    'points': [dict({'id': pid, 'at': at}, **({'facing': f} if f else {})) for pid, at, f in PTS],
    'areas': AREAS,
    'views': VIEWS,
    'actors': ACTORS,
}

# houses on the south lanes open onto the town, not the square
for d in SKETCH['districts']:
    for plot in d.get('plots', []):
        if plot['building'] == 'building:np_houses':
            plot['door_to'] = 'town:necropolis'


def whole(v):
    return int(v + 0.5) if v >= 0 else -int(-v + 0.5)


def round_geometry():
    """Whole cells everywhere but road lines and plot corners (the studio's rule)."""
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
    pts = POINTS_H + border_points()
    SKETCH['heights']['points'] = [dict({'at': [x, y], 'h': int(h)}, **({'notes': n} if n else {}))
                                   for x, y, h, n in pts]
    round_geometry()
    dump(PROJECT, OUT / 'project.yml')
    dump(PLAN, OUT / 'plan.yml')
    dump(SKETCH, OUT / 'sketch.yml')
    dump(ATMOSPHERE, OUT / 'atmosphere.yml')
    print('written', OUT)


if __name__ == '__main__':
    main()
