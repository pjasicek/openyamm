#!/usr/bin/env python3
"""XD-17 Shangri-La: the L1 brief (MU-3 plan) for the phase 5 review (A5, 2026-11-20).

    gen_l1.py [--with-census]     writes devdocs/xeen/briefs/xd17/L1/{project,plan,atmosphere}.yml

Then `oymap fmt` and `oymap validate --assets assets_dev` (run.sh does all of it, the drawings and the board). Later
passes edit this script and places.py, not the YAML. An open-air BLV (`kind: indoor`, `profile: region`, X8's route):
one room open to the sky, the valley floor as ground, the cliffs and the buildings standing in it. Map units, x east,
y north; the datum is the well in the court's middle.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import sys
from pathlib import Path

import yaml

import places as P

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'devdocs/xeen/briefs/xd17/L1'
FIG = pathlib.Path(_REPO_ROOT, 'output/studio_cal/xd17') / 'mockups/figures.json'

X7_CLEFT_POINT = '(4096, 8192, 2496) facing west (1024)'

PROJECT = {
    'format': 0,
    'id': 'xeen_xd17',
    'name': 'Shangri-La',
    'world': 'xeen',
    'kind': 'indoor',
    'profile': 'region',
    'map_code': 'XD-17',
    'units': {'plan_grid': P.GRID},
    'extent': {'footprint_cells': [46, 38], 'climbs': 'ne'},
    'map_stats': {
        'id': 9120,
        'continent': 6,
        'encounter_chance': 0,
        'treasure_level': 0,   # maps.yml's "-": D-50 gives XD-17 no chests; row 9120 writes 0
        'trap_dice': 0,
        'perception_difficulty': 0,
        'refill_days': 672,
        'music': 51,
        'environment': 'plains',
        'lock_difficulty': 0,
    },
    'neighbours': [
        {'id': 'exit:xd16_way', 'to': 'xeen_xd16.blv', 'kind': 'door', 'arrival': 'entrance:xd17_way',
         'arrival_hint': "In XD-16's cool passage about 256 inside its far end, facing back down toward the last cave.",
         'notes': "XD-16 Volcano Cave (A7, D-47 Q4): the cool passage's end calls A3's q-c26.way (true with "
                  "q-c26.done) and moves the party here, to entrance:xd16_way in the cave mouth; this map's way back "
                  "is the back of the mouth's throat, an exit preset (D-24: the game's leave window; its meaning in "
                  "the ledger is the source's \"Leave Shangri-La?\", aaze0049:32), to XD-16's entrance:xd17_way "
                  "(4864, -18176, -1280) facing north (D-50)."},
        {'id': 'exit:x7_cleft', 'to': 'xeen_x7.odm', 'kind': 'door', 'arrival': 'entrance:xd17_cleft',
         'arrival_hint': f"On X7 before the cleft at [72, 48], {X7_CLEFT_POINT}, away from the rock.",
         'notes': "X7 Mount Firestone (A5, installed; D-40 question 3): the back passage's far end, the inside of the "
                  "rockfall, an exit preset (D-24). Its first use calls A3's xd17.cleft_opened (sets cleft_open "
                  "116140, once, a status line) before it moves the party to X7's entrance:xd17_cleft; after that "
                  "X7's door:xd17 leads back in to entrance:x7_cleft. Always open from this side (D-50)."},
        {'id': 'pyramid:alamar', 'to': 'xeen_d6.odm', 'kind': 'pyramid', 'listed_only': True,
         'condition': {'qbit': 'm30_done'},
         'notes': "The second pair of travel pyramids (WORLD_DESIGN 3.3; ROADMAP 5.6): Xeen.travelPyramid(\"shangrila\")"
                  " (xeen_common.lua: opens on m30.done, to alamar_gate); before it the source's \"The moons are not "
                  "aligned. You are unable to pass.\" (aaze0049:25). The far end: D6 outside Castle Alamar's gate (D-50 Q9: "
                  "A6 adds a working pyramid there with entrance:xd17_pyramid; D6 is not built). This map's arrival "
                  "from it is entrance:d6_pyramid, (0, 3200, 256) facing south (1536)."},
    ],
    'qbits': {'cleft_open': 116140, 'qc26_done': 112522, 'm30_done': 111600},
    'rules': {'weather': 'none'},
    'notes': "XD-17 Shangri-La, MU-3 plan for the phase 5 review (A5, 2026-11-20): an open-air BLV (devdocs/"
             "INDOOR_OPEN_SKY.md; X8's studio route, profile region): a green valley ringed by black cliffs in "
             "Mount Firestone's flank, reached through the Volcano Cave (Q-C26). A hidden town of five services and "
             "ten residences (D-5.1; A4's towns/xd17.yml), no monsters, music 51. Drawings and board: "
             "output/studio_cal/xd17/mockups/board_xd17.png.",
}


def building_rows(zone):
    rows = []
    for b in P.BUILDINGS:
        if zone_of(b['at']) != zone:
            continue
        ids = ', '.join(f"{d[0]} (house {d[1]}, indoor id {d[2]}, door at {list(d[3])} facing {d[4]})"
                        for d in b['doors'])
        rows.append({'id': b['id'], 'type': 'house', 'service': b['service'], 'count': 1, 'doors': len(b['doors']),
                     'footprint_cells': footprint(b),
                     'notes': f"{b['name']}: {b['look']}. Floor {b['floor']}, {b['height']} high. A4: {ids}."})
    return rows


def footprint(b):
    """[front, depth] in cells: the front is the side with the (first) door."""
    w, d = b['size']
    if b['doors'][0][4] in ('e', 'w'):
        w, d = d, w
    return [round(w / P.GRID * 2) / 2, round(d / P.GRID * 2) / 2]


def zone_of(pt):
    best, bd = None, 1e9
    for zid, (_, c, ext, _, _) in P.ZONES.items():
        inside = abs(pt[0] - c[0]) <= ext[0] / 2 and abs(pt[1] - c[1]) <= ext[1] / 2
        d = P.dist(pt, c) - (1e6 if inside else 0)
        if d < bd:
            best, bd = zid, d
    return best


def spaces():
    vid, vname, vat, vext = P.VALLEY
    out = [{
        'id': vid, 'name': vname, 'kind': 'room', 'at': list(vat), 'extent': list(vext),
        'shape': 'an uneven oval basin under black cliffs 2,300-3,300 high, longer east-west',
        'floor': {'level': 0, 'range': [-64, 384]},
        'clear_height': 9000,
        'purpose': "The hidden valley: a lawn and lanes on nearly flat ground (terraces of 256 and 384 under the west "
                   "and north cliffs), cool air, no monsters. Open to the sky; its walls and roof are sky faces beyond "
                   "the crest.",
        'theme': 'green valley floor (grass, flagstone lanes, packed earth by the doors), black basalt cliffs',
        'safe': True,
        'population': [
            {'id': 'pop:lacey', 'actor': 'Lacey (monster 11915 Xeen Lacey, NPC 4719)',
             'role': 'a white unicorn by the well', 'groups': 1,
             'notes': f"D-50 Q2: a placed peaceful actor on MM8's unicorn (Unicorn A), not counted; at "
                      f"{list(P.LACEY)}, wandering within 512 of her spot by the well. Her topic: 'The moons will "
                      "align ...' (aaze0049:18), through A1's NPC-on-a-placed-monster word (D-47)."},
            {'id': 'pop:stumpy', 'actor': 'Stumpy (monster 11916 Xeen Stumpy, NPC 4718)',
             'role': 'a talking tree in the orchard', 'groups': 1,
             'notes': f"D-50 Q2: a placed peaceful actor on MM7's treant, move stand, not counted (Leafpoint's "
                      f"pattern, D-36 (5)); at {list(P.STUMPY)}. Topic: the Druid of Summer (aaze0049:6), through "
                      "A1's NPC-on-a-placed-monster word (D-47)."},
        ],
    }]
    for zid, (name, c, ext, floor, purpose) in P.ZONES.items():
        row = {'id': zid, 'name': name, 'kind': 'zone', 'part_of': vid, 'at': list(c), 'extent': list(ext),
               'floor': floor, 'purpose': purpose}
        b = building_rows(zid)
        if b:
            row['buildings'] = b
        out.append(row)
    out += [
        {'id': 'room:cave_mouth', 'name': "The cave mouth", 'kind': 'corridor', 'at': [P.MOUTH[0], P.MOUTH[1] - 384],
         'extent': [512, 768], 'floor': [-128, -64], 'clear_height': 448,
         'purpose': "The end of XD-16's cool passage: a low black throat in the south cliff, 768 deep, rising into "
                    "the light. entrance:xd16_way stands just outside it; its back is the way out to XD-16.",
         'safe': True},
        {'id': 'room:back_passage', 'name': 'The back passage', 'kind': 'corridor',
         'at': [-6656, 3584], 'extent': [2048, P.PASSAGE_WIDTH], 'floor': [0, 128],
         'shape': 'a slot of rock open to the sky, 384 wide, walls 1,500 high, bending once',
         'purpose': "D-40 (3): the valley's back way to X7's cleft. Its far end is the inside of the rockfall: the "
                    "first exit shifts the stones (xd17.cleft_opened) and the cleft is two-way after.",
         'safe': True},
        {'id': 'void:rim', 'name': 'The cliffs and the sky', 'kind': 'void',
         'purpose': "Black basalt cliffs 2,300 (south) to 3,300 (north-east) above the floor, a jagged crest, the "
                    "room's sky faces beyond it. Over the north-east rim, Mount Firestone's summit as a backdrop "
                    "(question 3).",
         'backdrop': True},
    ]
    return out


def plan(poi_count=None):
    doors = P.doors()
    pois = [
        {'id': 'poi:well', 'space': 'zone:court', 'kind': 'well',
         'behaviour': "The source's well, A3's hook xd17.well (D-50 Q1): once per character (player bit) "
                      "20,000 experience and the award Found Shangri-La, with aaze0049:27's 'Congratulations, You "
                      "found Shangri-La!'; after that 'The water is cool and refreshing.' (aaze0049:4).",
         'uses': {'times': 1, 'per': 'character', 'reset': 'never'}},
        {'id': 'poi:pyramid', 'space': 'zone:north_terrace', 'kind': 'pyramid', 'neighbour': 'pyramid:alamar',
         'behaviour': "The travel pyramid: A3's hook xd17.pyramid, which calls Xeen.travelPyramid(\"shangrila\") "
                      "after m30.done; before it \"The moons are not aligned. You are unable to pass.\" (aaze0049:25). "
                      "Its portal face on the south side. D6's far end is not built (D-50 Q9).",
         'condition': {'qbit': 'm30_done'}},
        {'id': 'poi:crystal', 'space': 'room:valley', 'kind': 'curiosity',
         'behaviour': "The hidden crystal in the wall (Benedict's joke, aaze0049:14): a thumb-sized crystal set in "
                      "the cliff by the cave mouth, at eye height, facing the valley. Clicked: A3's line "
                      "(xd17.crystal, D-50 Q5)."},
    ]
    for aid, house, sid, pt, face, b in doors:
        pois.append({'id': 'poi:' + sid.split(':')[1], 'space': zone_of(pt), 'kind': 'house_door',
                     'behaviour': f"{b['name']} (house {house}): A4's {aid}; indoor door id {sid}. At {list(pt)}, "
                                  f"facing {face}, floor {b['floor']}."})
    p = {
        'format': 0,
        'level': 'L1',
        'pitch': "Beyond the last cave, cool air, and the smell of grass. A green valley in the black flank of Mount "
                 "Firestone, ringed by cliffs, with a well that makes you better at everything and people who know "
                 "the answers. The town is small and very pleased with itself.",
        'purpose': "Act V's hidden town (Q-C26, party 48-52): five services from the source (D-5.1), the world's "
                   "late Grandmasters in the Public Library, An Education and the hint people's houses, the +1 level "
                   "well, the second travel pyramid (to Castle Alamar after M30), and a back way out to X7 that "
                   "stays open once found.",
        'mood': "Cool and bright after the Volcano Cave: high sun, green lawns, white plaster, water falling; the "
                "black rim and Firestone's smoke over it as a reminder of where you are.",
        'datum': 'zone:court',
        'spaces': spaces(),
        'links': [
            {'id': 'link:mouth', 'from': 'room:cave_mouth', 'to': 'zone:first_street', 'kind': 'path', 'width': 384,
             'rise': 128, 'purpose': 'Out of the throat into the light.'},
            {'id': 'link:first_street', 'from': 'zone:first_street', 'to': 'zone:court', 'kind': 'path',
             'width': 384},
            {'id': 'link:west_lane', 'from': 'zone:court', 'to': 'zone:west_terrace', 'kind': 'stairs', 'width': 384,
             'rise': 256, 'notes': "Broad steps up to the library's colonnade; a second flight to the temple (384)."},
            {'id': 'link:pyramid_steps', 'from': 'zone:court', 'to': 'zone:north_terrace', 'kind': 'stairs',
             'width': 640, 'rise': 256},
            {'id': 'link:north_west', 'from': 'zone:court', 'to': 'zone:north_west', 'kind': 'path', 'width': 256},
            {'id': 'link:passage', 'from': 'zone:north_west', 'to': 'room:back_passage', 'kind': 'path',
             'width': P.PASSAGE_WIDTH, 'rise': 128},
            {'id': 'link:pool', 'from': 'zone:court', 'to': 'zone:east_shore', 'kind': 'path', 'width': 256},
            {'id': 'link:guild', 'from': 'zone:east_shore', 'to': 'zone:north_terrace', 'kind': 'path', 'width': 256,
             'rise': 256},
            {'id': 'link:east_lane', 'from': 'zone:court', 'to': 'zone:orchard', 'kind': 'path', 'width': 256},
            {'id': 'link:tavern_lane', 'from': 'zone:first_street', 'to': 'zone:west_terrace', 'kind': 'path',
             'width': 256, 'notes': "Past Benedict's and Martok's doors to the library steps."},
        ],
        'loops': [
            {'id': 'loop:west', 'spaces': ['zone:first_street', 'zone:west_terrace', 'zone:court'],
             'notes': 'Up the first street, west to the library, back down to the court.'},
            {'id': 'loop:east', 'spaces': ['zone:court', 'zone:east_shore', 'zone:north_terrace'],
             'notes': "Round the pool and the guild to the pyramid terrace."},
        ],
        'entrances': [
            {'id': 'entrance:xd16_way', 'space': 'zone:first_street', 'kind': 'arrival', 'neighbour': 'exit:xd16_way',
             'facing': 'n',
             'how': f"From XD-16's cool passage (A7's q-c26.way): {list(P.XD16_ARRIVAL)}, floor -64, 512 out of the "
                    "cave mouth, facing north into the valley. The arrival view (MU-4)."},
            {'id': 'entrance:mouth_back', 'space': 'room:cave_mouth', 'kind': 'exit', 'neighbour': 'exit:xd16_way',
             'how': f"The back of the throat at {list(P.MOUTH_EXIT)}: an exit preset (D-24; the window's meaning "
                    "\"Leave Shangri-La?\", aaze0049:32), to XD-16's entrance:xd17_way."},
            {'id': 'entrance:x7_cleft', 'space': 'room:back_passage', 'kind': 'arrival', 'neighbour': 'exit:x7_cleft',
             'facing': 'e',
             'how': f"From X7's cleft once cleft_open is set (X7's door:xd17, A3's xd17.cleft): "
                    f"{list(P.X7CLEFT_ARRIVAL)}, 384 inside the stones, facing east down the passage to the valley."},
            {'id': 'entrance:cleft_back', 'space': 'room:back_passage', 'kind': 'exit', 'neighbour': 'exit:x7_cleft',
             'how': f"The inside of the rockfall at {list(P.PASSAGE_EXIT)}, an exit preset (D-24): its first use "
                    f"calls A3's xd17.cleft_opened ('You shift the last stones from the inside. The cleft is open "
                    f"both ways now.'), then X7's entrance:xd17_cleft {X7_CLEFT_POINT}."},
            {'id': 'entrance:d6_pyramid', 'space': 'zone:north_terrace', 'kind': 'both', 'neighbour': 'pyramid:alamar',
             'facing': 's',
             'how': f"The pyramid's portal face; arriving from the far pyramid at {list(P.PYRAMID['arrival'])}, "
                    "floor 256, facing south over the court (Xeen.PyramidArrivals.shangrila, A3)."},
        ],
        'critical_path': ['room:cave_mouth', 'zone:first_street', 'zone:court'],
        'goals': [
            {'id': 'goal:well', 'space': 'zone:court', 'kind': 'use',
             'what': 'Drink from the well (once per character).'},
        ],
        'points_of_interest': pois,
        'landmarks': [
            {'id': 'landmark:pyramid', 'space': 'zone:north_terrace',
             'what': 'The small stone pyramid on its terrace against the north cliff',
             'seen_from': ['zone:first_street', 'zone:court', 'zone:west_terrace']},
            {'id': 'landmark:guild_dome', 'space': 'zone:east_shore',
             'what': "The Light guild's white tower and gilded dome, the tallest roof (1,536)",
             'seen_from': ['zone:first_street', 'zone:court', 'zone:west_terrace', 'zone:orchard']},
            {'id': 'landmark:falls', 'space': 'zone:east_shore',
             'what': 'The white fall on the east cliff into the cold pool (no event, not a POI: D-50 change 6)',
             'seen_from': ['zone:first_street', 'zone:court', 'zone:west_terrace']},
            {'id': 'landmark:summit', 'space': 'void:rim',
             'what': "Mount Firestone's black summit over the north-east rim, 5,600 above the floor (D-50 Q3; "
                     "smoke only once A6/S have an effect)",
             'seen_from': ['zone:first_street', 'zone:court', 'zone:west_terrace']},
        ],
        'sightlines': [
            {'id': 'view:signature', 'from': 'zone:west_terrace',
             'to': ['zone:court', 'landmark:falls', 'landmark:guild_dome', 'landmark:summit'],
             'what': P.CAMERAS['signature']['what'] +
             f" Camera {list(P.CAMERAS['signature']['at'])}, eye {P.CAMERAS['signature']['z']}, "
             f"looking {P.CAMERAS['signature']['yaw']} degrees (east 0, north 90)."},
            {'id': 'view:arrival', 'from': 'zone:first_street',
             'to': ['landmark:pyramid', 'landmark:guild_dome', 'landmark:falls', 'landmark:summit'],
             'what': P.CAMERAS['arrival']['what'] +
             f" Camera {list(P.CAMERAS['arrival']['at'])}, eye {P.CAMERAS['arrival']['z']}, "
             f"looking {P.CAMERAS['arrival']['yaw']} degrees."},
        ],
        'height_bands': [
            {'id': 'band:floor', 'range': [-128, 64],
             'spaces': ['zone:court', 'zone:first_street', 'zone:orchard', 'zone:east_shore', 'room:cave_mouth'],
             'notes': 'the valley floor; the pool at -32'},
            {'id': 'band:terraces', 'range': [256, 384], 'spaces': ['zone:west_terrace', 'zone:north_terrace'],
             'partly': ['zone:north_west']},
            {'id': 'band:crest', 'range': [2304, 3328], 'spaces': ['void:rim'],
             'notes': 'the cliff crest: south 2,300, west and north 2,600-2,900, north-east 3,300'},
            {'id': 'band:summit', 'level': 6400, 'spaces': ['void:rim'],
             'notes': "Firestone's summit, a backdrop about 12,000 from the court"},
        ],
        'states': [
            {'id': 'state:cleft_shut', 'condition': {'not': {'qbit': 'cleft_open'}},
             'atmosphere': "The back passage ends in fallen rock; daylight between the stones.",
             'notes': 'D-40 (3): the first exit that way opens it (xd17.cleft_opened); from then on X7 leads back in.'},
        ],
        'atmosphere': "Open sky, Cloudside's fair preset (D-50 Q6), no theme, no ash, no weather, no ash inside the rim. Music 51. "
                      "Sounds: the fall and the stream (AU), birds by day, the forge's hammer by the first street, "
                      "the tavern's murmur.",
        'totals': {
            'placed_monsters': 0,
            'spawn_points': 0,
            'chests': 0,
            'doors': len(doors),
            'buildings': len(P.BUILDINGS),
            'services': 5,
            'residences': 10,
            'points_of_interest': poi_count if poi_count is not None else len(pois),
        },
        'notes': "MU-3 for the phase 5 review (A5, 2026-11-20). Footprint about 46 x 38 cells (23,500 x 19,500 with "
                 "the backdrop), the valley floor about 12,900 x 10,400. Source: xeen maze0049 (a green court of "
                 "5 x 9 tiles in a ring of houses; the well in its middle, the way in at the south, the pyramid at "
                 "the north end). Board: output/studio_cal/xd17/mockups/board_xd17.png. Doors by A4's ids "
                 "(towns/xd17.yml; the residences renamed by D-50 change 5). D-50 applied 2026-11-21.",
    }
    return p


ATMOSPHERE = {
    'format': 0,
    'open_sky': {'mode': 'open', 'preset': 'fair', 'view': 'outdoor', 'view_distance_scale': 1.25},
    'notes': "Cloudside's shipped fair preset by name (lanes README: a preset, never a texture alias), seen as an "
             "outdoor map; view distance 1.25 so Firestone's summit (about 15,000-16,000 from the cameras) is not cut "
             "off (question 3). No weather and no ash inside the rim (X7 has ash on ~40 % of days; the valley is "
             "the exception, the source's utopia). Daylight, ground and grass at L3 (X8's daylight block; the "
             "`ground` layers grass, flagstone, packed earth, basalt slope).",
}


class Dumper(yaml.SafeDumper):
    pass


def _list(dumper, data):
    flat = all(not isinstance(v, (list, dict)) for v in data)
    pairs = all(isinstance(v, list) and all(not isinstance(w, (list, dict)) for w in v) for v in data) and data
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=bool(flat or pairs))


Dumper.add_representer(list, _list)
Dumper.add_representer(tuple, lambda d, t: _list(d, list(t)))


def write(name, data):
    (OUT / name).write_text(yaml.dump(data, Dumper=Dumper, sort_keys=False, width=118, allow_unicode=True))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    count = None
    if '--with-census' in sys.argv and FIG.exists():
        count = json.loads(FIG.read_text()).get('poi_count')
    write('project.yml', PROJECT)
    write('plan.yml', plan(count))
    write('atmosphere.yml', ATMOSPHERE)
    print('written', OUT)


if __name__ == '__main__':
    main()
