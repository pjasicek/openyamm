#!/usr/bin/env python3
"""P5 Clouds of the Ancients: writes the L1 brief (plan.yml, project.yml, atmosphere.yml) from design.py (A5
sub-agent, 2026-11-21). After X9's gen_l1.py.

    gen_l1.py [--with-census]       devdocs/xeen/briefs/p5/L1/{plan,project,atmosphere}.yml

--with-census fills plan.yml's `totals` from render_p5.py's mockups/figures.json. The shape follows X9's L1: an
open-air BLV region, the clouds as spaces with `at` (the middle, map units) and `extent`. Point positions are in each
point's `notes` ("at (x, y)"), since the plan has no point coordinates at L1.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import json
from pathlib import Path

import yaml

import design as D
import geom as G

ROOT = Path(__file__).resolve().parents[4]
BRIEF = ROOT / 'devdocs/xeen/briefs/p5/L1'
MOCK = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p5') / 'mockups'
P = {p['id']: p for p in D.PLACES}


class Flow(list):
    pass


def flow_rep(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


yaml.add_representer(Flow, flow_rep)


def at_text(pid):
    x, y = P[pid]['at']
    return f'at ({round(x)}, {round(y)})'


def spaces(figures):
    out = []
    for s in D.SPACES:
        e = {'id': s['id'], 'name': s['name'], 'kind': 'room', 'at': Flow(list(s['at'])),
             'extent': Flow(list(s['extent'])), 'floor': s['floor']}
        if s.get('shape'):
            e['shape'] = s['shape']
        e['purpose'] = s['purpose']
        e.update({'relief': 'flat', 'safe': True, 'keep_clear': ['spawns']})
        if s['id'] == 'room:shrine':
            e['treasure'] = [{'kind': 'chest', 'count': 1, 'tier': 6,
                              'notes': "the wedding gift in the pavilion, shown with it on m42.done (question 7)"}]
            e['notes'] = ("The middle of the ring: its rim is at least "
                          f"{figures['shrine_sky_gap'][0]:,} of open sky from every road and pad but the last Rest "
                          "Stop, which the causeway joins.")
        if s['id'] == 'room:crown':
            sh = D.STAIR_HOUSE
            e['notes'] = (f"The stair house at {tuple(sh['at'])}: a round black tower top of radius {sh['radius']}, "
                          f"walls {sh['wall']}, a skull frieze {sh['band']}, a slate cone of about {sh['cone']}, as "
                          "X5's Darkstone Tower's crown (A6's thing:darkstone: gtrlwal1, hkm3b, xtslate). Its door "
                          "faces north. The road leaves the pad's north-west at (3584, -2944).")
        out.append(e)
    out.append({'id': 'void:sky', 'name': 'The sky', 'kind': 'void',
                'purpose': "Open sky round and under the clouds (below_horizon: sky); any fall lands on X5."})
    return out


def links(figures):
    out = []
    words = {'road': "the cloud road, 768 wide, a dashed line of cloud-stone flags down its middle",
             'causeway': "a cloud-stone causeway over the sky"}
    for l in D.LINKS:
        e = {'id': l['id'], 'from': l['a'], 'to': l['b'], 'kind': l['kind'], 'width': l['width'],
             'rise': G.SPACE[l['b']]['floor'] - G.SPACE[l['a']]['floor']}
        e['notes'] = (f"{words[l['style']]}; {figures['links'][l['id']]['length']:,} rim to rim"
                      + (f"; {l['notes']}" if l.get('notes') else ''))
        out.append(e)
    return out


def pois(figures):
    boards = [p for p in D.PLACES if p['kind'] == 'board']
    rests = [p for p in D.PLACES if p['kind'] == 'rest']
    st = figures['stations']
    return [
        {'id': 'poi:pharaoh_note', 'space': 'room:crown', 'kind': 'sign',
         'behaviour': ("A3's m42.pharaoh_note: 'A message reads: It's a long road ahead so rest where you can. But "
                       "don't forget to recast your spells. Signed, The Dragon Pharaoh' (aazex129:15)."),
         'notes': f"{at_text('poi:pharaoh_note')}, on a post by the stair house's door (the source's (29,7), two steps "
                  "from the arrival); question 4"},
        {'id': 'poi:boards', 'spaces': sorted({p['space'] for p in boards}), 'kind': 'sign', 'count': len(boards),
         'behaviour': ("Billboards on the road's outer shoulder, each naming one New World Computing game, the "
                       "source's sign texts (aazex129:1-10), clicked or hovered: "
                       + ', '.join(f"'{p['text']}'" for p in boards) + ". In walking order; 'Might and Magic' last, "
                       "beside the causeway's head (the source's (12,17)). Question 8 decides lettered faces."),
         'notes': '; '.join(f"{p['text']} {at_text(p['id'])} facing {p['face']}, {st[p['id']]['along']:,} along"
                            for p in boards)},
        {'id': 'poi:rest_stops', 'spaces': [p['space'] for p in rests], 'kind': 'sign', 'count': len(rests),
         'behaviour': ("Rest Stop huts beside the road: an open-fronted hut with a bench, the sign 'Rest Stop' "
                       "(aazex129:0) over its front. Clicked: the line. The map has no monsters; resting is safe "
                       "anywhere."),
         'notes': '; '.join(f"{p['id'].split(':')[1]} {at_text(p['id'])} facing {p['face']}, "
                            f"{st[p['id']]['along']:,} along" for p in rests)},
        {'id': 'poi:observatory', 'space': 'room:observatory', 'kind': 'door',
         'behaviour': "A3's m42.observatory (status): 'The observatory is closed.' (aazex129:11). The door never opens.",
         'notes': f"{at_text('poi:observatory')}, the door in the round tower's south face, "
                  f"{st['poi:observatory']['along']:,} along"},
        {'id': 'poi:shrine', 'space': 'room:shrine', 'kind': 'shrine',
         'behaviour': ("A3's m42.shrine: with the Cube of Power, Xeen's Scepter and the four sleepers it takes the two, "
                       "sets m42.done, gives 'Made Xeen One World' and 40,000 experience, and starts the ending "
                       "cinematic (set:unification); without, the Pharaoh's refusal (aazex129:12-13); after, 'The "
                       "shrine is quiet. The pavilion is still there; somebody has left cake.'"),
         'uses': {'times': 1, 'per': 'party', 'reset': 'never'},
         'condition': {'lua': 'XeenQuests.hook("m42.shrine")'},
         'notes': f"{at_text('poi:shrine')}: the dais (1,024 x 704, 64 high) faces south, its two stone hands 768 "
                  f"apart; {st['poi:shrine']['along']:,} along"},
        {'id': 'poi:gift_chest', 'space': 'room:shrine', 'kind': 'chest',
         'behaviour': ("The wedding gift: one chest of treasure 6 against the pavilion's back, clear of the couple and "
                       "the walking line, shown with it on m42.done (D-56 Q7)."),
         'condition': {'qbit': 'm42_done'}, 'notes': at_text('poi:gift_chest')},
        {'id': 'poi:disc', 'space': 'room:shrine', 'kind': 'teleport',
         'behaviour': ("A cloud-stone disc beside the pavilion's open south side, shown with state:wedding: a click "
                       "moves the party inside the map to entrance:fd03_roof with A3's line (D-56 change 7, Q10). "
                       "No new travel link."),
         'condition': {'qbit': 'm42_done'}, 'notes': at_text('poi:disc') + ", off the walking line"},
    ]


def plan(figures):
    stations = ['room:crown', 'room:rest_east', 'room:ne_turn', 'room:observatory', 'room:nw_turn', 'room:rest_west',
                'room:sw_turn', 'room:rest_south', 'room:shrine']
    doc = {
        'format': 0,
        'level': 'L1',
        'pitch': ("The cloud above Darkstone Tower, the last place in the world. One road of cloud leaves the tower's "
                  "black crown and goes the long way round: a ring past Rest Stop huts, an observatory that is "
                  "closed and billboards naming New World Computing's games, with the Pharaoh's shrine in sight across "
                  "the sky the whole way, until a causeway turns in to it. There the Dragon Pharaoh waits with his "
                  "two stone hands held up for the Cube and the Scepter; after the ceremony, a wedding pavilion."),
        'purpose': ("Act VI's finale (M42, party 61-65): the walk, the Pharaoh's note, the shrine and the ending "
                    "cinematic (evt.PlayCinematic), Roland and Kalindra's wedding, the completion certificate. "
                    "Reached by FD-03's roof stair after M41's seal; left down the stair house, by falling (to X5) or "
                    "by spell."),
        'mood': ("Bright, quiet and a little solemn; a highway in the sky with rest stops and billboards. The world "
                 "winks one last time; nothing attacks."),
        'datum': 'room:crown',
        'regions': [
            {'id': 'region:ring', 'name': 'The long road',
             'spaces': [s for s in stations if s != 'room:shrine'],
             'where': "the source's spiral road (maze 129 with x181-x183), one ring of 7,168 a side"},
            {'id': 'region:middle', 'name': "The Pharaoh's shrine", 'spaces': ['room:shrine'],
             'where': "the source's middle, (13,15)"},
        ],
        'spaces': spaces(figures),
        'links': links(figures),
        'entrances': [
            {'id': 'entrance:fd03_roof', 'space': 'room:crown', 'kind': 'both', 'neighbour': 'door:fd03',
             'facing': 'n',
             'how': ("Out of the stair house's door at the top of FD-03's roof stair, after M41's seal. The same door "
                     "is the way down: an exit preset, meaning 'Descend into Darkstone Tower?' (aazex129:14), to "
                     "FD-03's entrance:p5_stair."),
             'notes': f"{at_text('entrance:fd03_roof')}, z 0, facing north (MoveToMap direction 512); the door "
                      f"{at_text('exit:stair_house')}."},
            {'id': 'entrance:fall', 'space': 'void:sky', 'kind': 'exit', 'neighbour': 'fall:x5',
             'how': "Any fall off a cloud: to X5, on Darkstone's rock before the tower door (question 3)."},
        ],
        'critical_path': stations,
        'return_path': ['room:shrine', 'room:crown'],
        'goals': [
            {'id': 'goal:unification', 'space': 'room:shrine', 'kind': 'use',
             'what': "The Pharaoh's shrine with the Cube of Power, Xeen's Scepter and the four sleepers awake",
             'story': 'M42', 'gives': {'qbit': 'm42_done'}},
        ],
        'points_of_interest': pois(figures),
        'landmarks': [
            {'id': 'landmark:crown', 'space': 'room:crown',
             'what': "Darkstone's crown: the black stair house with its skull frieze and slate cone, where the road "
                     "starts",
             'seen_from': [s for s in stations if s != 'room:crown']},
            {'id': 'landmark:hands', 'space': 'room:shrine',
             'what': "The shrine's two great stone hands held up open, gold-paved cloud under them",
             'seen_from': [s for s in stations if s != 'room:shrine']},
            {'id': 'landmark:observatory', 'space': 'room:observatory',
             'what': 'A round pale-stone tower with a copper dome and a shut slit',
             'seen_from': ['room:crown', 'room:rest_east', 'room:ne_turn', 'room:nw_turn', 'room:shrine']},
            {'id': 'landmark:pavilion', 'space': 'room:shrine',
             'what': 'The wedding pavilion: white canvas and gold, after m42.done',
             'seen_from': ['room:rest_south', 'room:observatory', 'room:rest_east', 'room:rest_west']},
        ],
        'sightlines': [
            {'id': D.CAMERAS['walk']['id'], 'from': 'room:crown',
             'to': ['landmark:hands', 'landmark:observatory'], 'what': D.CAMERAS['walk']['what'],
             'notes': (f"camera at {tuple(D.CAMERAS['walk']['at'])}, z {figures['cameras']['walk']['z']} (eye), "
                       f"yaw {D.CAMERAS['walk']['yaw_deg']:.0f} degrees (north-north-west); the shrine "
                       f"{figures['cameras']['walk']['to_shrine']:,} away")},
            {'id': D.CAMERAS['shrine']['id'], 'from': 'room:rest_south',
             'to': ['landmark:hands', 'landmark:pavilion', 'landmark:observatory'], 'what': D.CAMERAS['shrine']['what'],
             'notes': (f"camera at {tuple(D.CAMERAS['shrine']['at'])} on the causeway's head, z "
                       f"{figures['cameras']['shrine']['z']} (eye), facing north; the dais "
                       f"{figures['cameras']['shrine']['to_dais']:,} away")},
        ],
        'set_pieces': [
            {'id': 'set:long_road', 'kind': 'vista', 'spaces': stations,
             'rule': (f"The long way round: {figures['walk_length']:,} along the road from the arrival to the dais "
                      f"(about {figures['walk_seconds']['walking']} s walking, {figures['walk_seconds']['running']} s "
                      "running), the shrine in sight across the sky the whole way. The road climbs 448 round the "
                      f"ring. The crown and the last Rest Stop are {figures['crown_to_last_stop']['gap']:,} apart "
                      f"and 448 apart in height: no short cut.")},
            {'id': 'set:unification', 'kind': 'scripted', 'spaces': ['room:shrine'],
             'rule': ("D-56 change 5, in this order: the shrine's click (A3's m42.shrine) takes the Cube and the "
                      "Scepter, sets m42.done, gives the award and the 40,000 experience and starts the cinematic "
                      "`unification` (xeen_p5.cinematics.yml, A5 at L4) through evt.PlayCinematic; skippable, about "
                      "35 s; every gameplay step is an `event` cue, so a skip runs them too: (1) close on the dais, "
                      "an event cue shows the Cube and the Scepter in the hands, the Pharaoh's voiced line from the "
                      "cue only (D-38 xeen_vo_pharaoh_unification: 'Let the two faces of Xeen be one world again.'); "
                      "(2) a rising pull-back over the ring, four far chimes (the sleepers answer); (3) up into the "
                      "sky and a fade to white (A1's fade colour; black if A1 declines, final), during which an event "
                      "cue shows state:wedding; (4) fade in on the pavilion, Roland and Kalindra under it, the "
                      "Pharaoh turning to them with his book; a subtitle; (5) the party's view. When the cinematic "
                      "ends (played or skipped) the done event shows the hook's narrative text once; when that window "
                      "closes, the completion certificate (A4's world.yml `completion`) follows, never during the "
                      "cinematic (A1).")},
            {'id': 'set:fall', 'kind': 'scripted', 'spaces': ['void:sky'],
             'rule': ("As X8 and X9: a one-second check moves a party below z -1,000 (and the room's safety floor "
                      "at -6,000) through A3's Xeen.skyFall to X5, on Darkstone's rock "
                      f"{D.FALL_LANDING_X5['at']}, ground {D.FALL_LANDING_X5['ground']}, facing the tower door "
                      "(question 3).")},
        ],
        'states': [
            {'id': 'state:wedding', 'condition': {'qbit': 'm42_done'},
             'shows': ['thing:pavilion', 'npc:roland', 'npc:kalindra', 'landmark:cake', 'poi:gift_chest',
                       'decor:cube', 'decor:scepter', 'poi:disc'],
             'effects': ["Shown live by the cinematic's event cue at the fade, and on every load after (the wedding "
                         "load event on m42.done).",
                         "The shrine's click gives m42's else_text ('somebody has left cake')."],
             'notes': ("The pavilion is a structure hidden until then; the couple are placed peaceful figures, the Cube "
                       "and the Scepter the installed item models as scaled decorations (D-56 changes 3, 4, 7).")},
        ],
        'height_bands': [
            {'id': 'band:sea', 'level': -2000, 'spaces': ['void:sky'], 'notes': 'the cloud sea, far below'},
            {'id': 'band:ring', 'range': Flow([0, 448]),
             'spaces': [s for s in stations if s != 'room:shrine'],
             'notes': 'the road climbs 64 at each pad round the ring'},
            {'id': 'band:shrine', 'level': 512, 'spaces': ['room:shrine']},
        ],
        'atmosphere': ("Sky xeencloud (xeen_cloud_sea, below_horizon: sky, high sun, X9's daylight block), question 9; "
                       "no weather; wind; music 15 (MM8 Plane Between Planes). No Fly (no BLV casts it). No lighting "
                       "bake (open air)."),
        'notes': ("MU-3 for the phase 6 review (A5 sub-agent, 2026-11-21), D-56 applied (A5, sixteenth session). Room 26 x 26 cells (13,312 a side). "
                  "Board: output/studio_cal/p5/mockups/board_p5.png; tools output/studio_cal/p5/tools/ (run.sh). "
                  "Source: the Clouds of the Ancients, MM5 maze 129 with x181-x183 (dark/aazex129). D-56: the "
                  "Pharaoh, Roland and the wedding Kalindra (a new row keeping npc 5001) are peaceful, placed-only, "
                  "uncounted, NoArena figures, made unkillable by the map's load event "
                  "(SetMm9ActorCanReceiveDamage(false), as D-51 and D-52); Dungeon M with at most 13 new textures; "
                  "falls tested in D-54's shape (change 10)."),
    }
    if figures and figures.get('_census'):
        doc['totals'] = {
            'placed_monsters': 0,
            'chests': 1,
            'points_of_interest': figures['poi_census'],
            'walkable_area_millions': figures['walk_area_m'],
            'walk_length': figures['walk_length'],
            'shrine_sky_gap': figures['shrine_sky_gap'][0],
        }
    return doc


def project():
    return {
        'format': 0,
        'id': 'xeen_p5',
        'name': 'Clouds of the Ancients',
        'world': 'xeen',
        'kind': 'indoor',
        'profile': 'region',
        'map_code': 'P5',
        'units': {'plan_grid': 512},
        'extent': {'footprint_cells': Flow(list(D.ROOM))},
        'map_stats': {
            'id': 9119, 'encounter_chance': 0, 'treasure_level': 6, 'trap_dice': 0, 'perception_difficulty': 0,
            'refill_days': 672, 'music': 15, 'environment': 'plains', 'lock_difficulty': 0,
        },
        'neighbours': [
            {'id': 'door:fd03', 'to': 'xeen_fd03.blv', 'kind': 'door',
             'arrival': 'entrance:p5_stair',
             'arrival_hint': "At the top of FD-03's roof stair, inside the seal, facing down the stair.",
             'notes': ("FD-03 Darkstone Tower (A7, phase 6): its roof stair, open once M41's seal is broken "
                       "(m41.seal_broken 111820), comes up into P5's stair house at entrance:fd03_roof "
                       f"{tuple(D.ARRIVAL)}, z 0, facing north (512). The stair house's door goes back down: an "
                       "exit preset, meaning 'Descend into Darkstone Tower?' (aazex129:14).")},
            {'id': 'fall:x5', 'to': 'xeen_x5.odm', 'kind': 'fall',
             'notes': (f"Every fall lands on X5 at {D.FALL_LANDING_X5['at']}, Darkstone's rock top "
                       f"(ground {D.FALL_LANDING_X5['ground']}) 224 before the tower's north door, facing south "
                       "(1536), with falling damage; X5's entrance:p5_fall (A6), question 3.")},
        ],
        'qbits': {'m41_seal_broken': 111820, 'm42_done': 111840},
        'items': {'cube_of_power': 12365, 'xeens_scepter': 12366},
        'rules': {
            'no_fly': True,
            'weather': 'none',
            'fall_through': {'below': -1000, 'to': 'fall:x5', 'landing': Flow(list(D.FALL_LANDING_X5['at']))},
        },
        'notes': ("P5 Clouds of the Ancients, MU-3 plan for the phase 6 review (A5 sub-agent, 2026-11-21): an "
                  "open-air BLV region (devdocs/INDOOR_OPEN_SKY.md; X9's route) of walkable cloud above Darkstone "
                  "Tower. Clouds are plan spaces with `at` (map units, the middle) and `extent`. Drawings and board: "
                  "output/studio_cal/p5/mockups/."),
    }


def atmosphere():
    return {
        'format': 0,
        'open_sky': {'mode': 'open', 'sky_texture': 'xeencloud', 'view': 'outdoor', 'view_distance_scale': 1.5},
        'daylight': {'ambient_rgb': Flow([110, 112, 125]), 'sun_rgb': Flow([255, 248, 232]),
                     'night_scale_rgb': Flow([134, 143, 168]), 'sun_gain': 3},
        'notes': ("Sky xeencloud (xeen_cloud_sea: below_horizon sky) as every sky map (lanes README), question 9; an "
                  "outdoor view at 1.5 times the view distance so that the far side of the ring (about 10,000 across) "
                  "and the cloud sea read; no weather; X9's daylight block."),
    }


def dump(doc, path):
    path.write_text(yaml.dump(doc, sort_keys=False, allow_unicode=True, width=118))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-census', action='store_true')
    args = parser.parse_args()
    figures = json.loads((MOCK / 'figures.json').read_text())
    figures['_census'] = args.with_census
    BRIEF.mkdir(parents=True, exist_ok=True)
    dump(plan(figures), BRIEF / 'plan.yml')
    dump(project(), BRIEF / 'project.yml')
    dump(atmosphere(), BRIEF / 'atmosphere.yml')


if __name__ == '__main__':
    main()
