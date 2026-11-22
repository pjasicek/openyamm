#!/usr/bin/env python3
"""X9 Clouds of Xeen: writes the L1 brief (plan.yml, project.yml) from design.py (A5, 2026-11-20).

    gen_l1.py [--with-census]       devdocs/xeen/briefs/x9/L1/{plan,project}.yml

--with-census fills plan.yml's `totals` from render_x9.py's mockups/figures.json. The shape follows X8 Cloudreach's
L1 (devdocs/xeen/briefs/x8/L1): an open-air BLV region, islands as spaces with `at` (the middle, map units) and
`extent`. Point positions are in each point's `notes` ("at (x, y)"), since the plan has no point coordinates at L1.
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
BRIEF = ROOT / 'devdocs/xeen/briefs/x9/L1'
MOCK = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x9') / 'mockups'


class Flow(list):
    pass


def flow_rep(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


yaml.add_representer(Flow, flow_rep)


def at_text(pt):
    return f'at ({round(pt[0])}, {round(pt[1])})'


def population(polys):
    out = {}
    for g in D.GROUPS:
        name, level, xp = D.ROWS[g['actor']]
        at = G.place_at(g, polys)
        out.setdefault(g['space'], []).append({
            'id': g['id'], 'actor': str(g['actor']), 'groups': g['count'], 'placed': True, 'hostile': True,
            'notes': f"{g['count']} {name}s ({level}) as one group, {at_text(at)}" +
                     (', flying' if g['actor'] != 11592 else ', walking: 300 or more inside the rim')})
    return out


TREASURE = {
    'room:sw_nest': [{'kind': 'chest', 'count': 1, 'tier': 5, 'notes': 'the hollow under the nest: stolen goods'},
                     {'kind': 'decoration', 'count': 1, 'notes': 'the nest of whole branches, bones and trinkets'}],
    'room:se_nest': [{'kind': 'decoration', 'count': 1, 'notes': 'the nest'}],
    'room:nw_isle': [{'kind': 'chest', 'count': 1, 'tier': 5, 'notes': "an old traveller's cache"}],
    'room:east_horn': [{'kind': 'chest', 'count': 1, 'tier': 5, 'notes': "a lost traveller's pack"}],
    'room:aviary': [{'kind': 'chest', 'count': 1, 'tier': 5, 'notes': "the rocs' hoard: shiny things carried up from the land"},
                    {'kind': 'decoration', 'count': 3, 'notes': 'three great nests'}],
}

EXTRA = {
    'room:stair_head': dict(safe=True, keep_clear=['spawns']),
    'room:brink': dict(safe=True, keep_clear=['spawns']),
    'room:landing': dict(safe=True, keep_clear=['spawns']),
    'room:carnival': dict(safe=True, keep_clear=['spawns'], relief='flat'),
    'room:gate_court': dict(safe=True, keep_clear=['spawns'], relief='flat'),
    'room:dragon_clouds': dict(empty=True, secret=True),
}


def spaces(polys):
    pop = population(polys)
    out = []
    for s in D.SPACES:
        e = {'id': s['id'], 'name': s['name'], 'kind': 'zone' if s['kind'] == 'castle' else 'room',
             'at': Flow([s['at'][0], s['at'][1]]), 'extent': Flow(list(s['extent'])), 'floor': s['floor']}
        if s.get('shape'):
            e['shape'] = s['shape']
        e['purpose'] = s['purpose']
        e.update(EXTRA.get(s['id'], {}))
        if s['id'] in pop:
            e['population'] = pop[s['id']]
        if s['id'] in TREASURE:
            e['treasure'] = TREASURE[s['id']]
        if s['kind'] == 'castle':
            h = D.CASTLE_HEIGHTS
            x0, y0 = s['at'][0] - s['extent'][0] / 2, s['at'][1] - s['extent'][1] / 2
            e['notes'] = (f"Not walkable, closed on every side, roof included (D-50 change 5): XD-19's measured footprint "
                          f"x {x0:.0f}..{x0 + s['extent'][0]:.0f}, y {y0:.0f}..{y0 + s['extent'][1]:.0f} (XD-19's frame "
                          f"+ {D.XD19_OFFSET}). The walls stand {h['walls']}, the four corner towers {h['towers']} "
                          f"(radius {h['tower_radius']}), the keep {h['keep']}, over the base {s['floor']}, so that "
                          "XD-19's rooms (up to 3,456 over the gate sill) fit inside. The gate is set "
                          f"{h['gate_recess']} back from the south-corner towers' fronts, two leaves of "
                          f"{h['gate_leaves'][0]} x {h['gate_leaves'][1]} (gnecdr1l/gnecdr1r). Its own cloud runs "
                          "1,024 beyond the walls on every side (the apron the aviary stair leaves from).")
        if s['kind'] == 'sealed':
            e['notes'] = 'Sealed: no link from any other cloud; FD-04 (A7, phase 6) is its only way in. Q-F1 fills it.'
        out.append(e)
    return out


def links(polys):
    out = []
    for l in D.LINKS:
        p, q = G.link_ends(l, polys)
        e = {'id': l['id'], 'from': l['a'], 'to': l['b'], 'kind': l['kind'], 'width': l['width'],
             'rise': G.SPACE[l['b']]['floor'] - G.SPACE[l['a']]['floor']}
        words = {'neck': 'one cloud: a waist', 'bridge': 'rope bridge', 'causeway': 'cloud-stone stair on a cloud tongue',
                 'road': 'the Xeen road, cloud-stone flags on a cloud tongue', 'unseen': 'the unseen way',
                 'gate': 'two leaves'}[l['style']]
        e['notes'] = f"{words}; {round(G.length(p, q)):,} rim to rim" + (f"; {l['notes']}" if l.get('notes') else '')
        if l['id'] == 'link:gate':
            e['condition'] = {'lua': 'XeenQuests.hook("m34.gate")'}
            e['notes'] = ("Castle Xeen's gate: two leaves (the double-door rule), XD-19's door with the exit preset's "
                          "leave (D-50 change 3, D-24): condition A3's m34.gate (the fail text without a doll; with it "
                          "the game's own leave window, meaning 'Enter Castle Xeen?', aaze0027:40). No map question. "
                          "Into XD-19's entrance:x9_gate (A7).")
        out.append(e)
    return out


def pois(polys):
    P = {p['id']: p for p in D.PLACES}
    at = {k: G.place_at(v, polys) for k, v in P.items()}
    out = [
        {'id': 'poi:signs', 'spaces': ['room:stair_head', 'room:brink', 'room:landing', 'room:aviary'], 'kind': 'sign',
         'count': 4,
         'behaviour': ("The source's four signs, clicked: 'Danger! Go back!' (aaze0027:7) on the neck to the brink; "
                       "'Xeen--9N.' (:6) at the unseen way's foot; 'Now entering Xeendom' (:8) at its head; "
                       "'Xeen's Aviary' (:9) at the top of the aviary stair (D-47)."),
         'notes': '; '.join(f"{k.split(':')[1]} {at_text(at[k])}" for k in
                            ('poi:danger_sign', 'poi:nine_north', 'poi:xeendom_sign', 'poi:aviary_sign'))},
        {'id': 'poi:rhyme_statues', 'spaces': ['room:west_wing', 'room:east_wing'], 'kind': 'statue', 'count': 4,
         'behaviour': ("A3's m34.statue_1-4, the source's four rhymes (aaze0027:2-5): the dig permit, Xeen's bane "
                       "under the castle, Lord Xeen above the island tower, only the sword. Readable by anyone until "
                       "the Linguist gate exists (as X8)."),
         'notes': '; '.join(f"statue_{i} {at_text(at[f'poi:statue_{i}'])}" for i in range(1, 5))},
        {'id': 'poi:roc_nests', 'spaces': ['room:sw_nest', 'room:se_nest', 'room:aviary'], 'kind': 'camp', 'count': 5,
         'behaviour': ("'Roc Nest. Destroy?' (aaze0027:0), Yes/No; the nest goes and a hook pays experience (the "
                       "source's 50,000 each, rescaled by A3; X8's harpy nests pay 500)."),
         'uses': {'times': 1, 'per': 'party', 'reset': 'never'},
         'notes': '; '.join(f"{k.split(':')[1]} {at_text(at[k])}" for k in
                            ('poi:nest_sw', 'poi:nest_se', 'poi:nest_a1', 'poi:nest_a2', 'poi:nest_a3'))},
        {'id': 'poi:offering_statues', 'spaces': ['room:west_pillar', 'room:west_spine', 'room:west_shelf',
                                                  'room:nw_isle', 'room:east_ledge', 'room:east_horn'],
         'kind': 'statue', 'count': 6,
         'behaviour': ("'Offering' (aaze0027:33), as X8's: a Crusader (M4 done) is given one item of treasure 5 once; "
                       "anyone else is struck. One on each lone cloud of the two chains (the source has nine)."),
         'uses': {'times': 1, 'per': 'party', 'reset': 'never'}, 'reached_by': 'off_road',
         'notes': '; '.join(f"offering_{i} {at_text(at[f'poi:offering_{i}'])}" for i in range(1, 7))},
        {'id': 'poi:might_game', 'space': 'room:carnival', 'kind': 'game',
         'behaviour': "A3's m34.might_game: a high-striker, the bell on a pole and a hammer (Might 60, 100 gold).",
         'notes': at_text(at['poi:might_game'])},
        {'id': 'poi:speed_game', 'space': 'room:carnival', 'kind': 'game',
         'behaviour': "A3's m34.speed_game: a gremlin's race track (Speed 60, 1,000 gold).",
         'notes': at_text(at['poi:speed_game'])},
        {'id': 'poi:endurance_game', 'space': 'room:carnival', 'kind': 'game',
         'behaviour': "A3's m34.endurance_game: a treadmill (Endurance 60, 5 gems).",
         'notes': at_text(at['poi:endurance_game'])},
        {'id': 'poi:accuracy_game', 'space': 'room:carnival', 'kind': 'game',
         'behaviour': "A3's m34.accuracy_game: the shooting line, a straw bullseye 1,536 west at the plaza's end (Accuracy 60, 10 gems).",
         'notes': at_text(at['poi:accuracy_game'])},
        {'id': 'poi:prize_stand', 'space': 'room:gate_court', 'kind': 'game',
         'behaviour': "A3's m34.prize_stand: four dolls for the Lord Xeen doll (12371), 10,000 experience.",
         'notes': at_text(at['poi:prize_stand'])},
        {'id': 'poi:castle_gate', 'space': 'room:gate_court', 'kind': 'door',
         'behaviour': ("Castle Xeen's gate (XD-19's door): m34.gate. After m35.done the castle is gone and a click or "
                       "step on the spot reads 'The great Castle Xeen recently stood here.' (aaze0027:44)."),
         'condition': {'lua': 'XeenQuests.hook("m34.gate")'}, 'neighbour': 'door:xd19',
         'notes': at_text(at['poi:castle_gate'])},
    ]
    return out


def plan(polys, figures):
    places = {p['id']: G.place_at(p, polys) for p in D.PLACES}
    doc = {
        'format': 0,
        'level': 'L1',
        'pitch': ("Lord Xeen's own clouds over Lake Darzog. A long southern cloud where Darzog's Tower's cloud stair "
                  "comes up, four rhyming statues and two roc nests on it; an open gap that a sign crosses in two "
                  "words ('Xeen--9N.'); and the rising cloud of Xeendom beyond: Slick's carnival on a paved plaza, "
                  "Castle Xeen black and gold at the top of the road, the rocs' aviary on its high cloud to the "
                  "east. Down both sides, lone clouds and rope bridges with offering statues. High above the "
                  "aviary, out of reach, the Dragon Clouds."),
        'purpose': ("Act V's sky map (party 46-48): M34 (Slick's four stat games and the cupie doll that opens Castle "
                    "Xeen's gate) and the way into XD-19 (M35). Reached one way up from XD-12's roof after M21; left "
                    "by falling (to X2) or through the castle. Later Q-F1's Dragon Clouds, a sealed island."),
        'mood': "Bright, airy and vertiginous; a cheerful carnival at an evil lord's gate. The world winks; the rocs do not.",
        'datum': 'room:stair_head',
        'regions': [
            {'id': 'region:south', 'name': 'The stair clouds', 'spaces': ['room:stair_head', 'room:brink',
             'room:west_wing', 'room:sw_nest', 'room:east_wing', 'room:se_nest'],
             'where': "the source's long southern cloud (y 1-9)"},
            {'id': 'region:west', 'name': 'The west chain', 'spaces': ['room:west_pillar', 'room:west_spine',
             'room:west_shelf', 'room:nw_isle'], 'where': "the source's lone clouds down the west side"},
            {'id': 'region:xeendom', 'name': 'Xeendom', 'spaces': ['room:landing', 'room:carnival', 'room:back_lot',
             'room:gate_court', 'zone:castle', 'room:aviary'], 'where': "the source's northern cloud (y 18-31)"},
            {'id': 'region:east', 'name': 'The east chain', 'spaces': ['room:east_pillar', 'room:east_ledge',
             'room:east_horn'], 'where': "the source's (23,10-12) and (28-30,19-21)"},
        ],
        'spaces': spaces(polys) + [{'id': 'void:cloud_sea', 'name': 'The cloud sea', 'kind': 'void',
                                    'purpose': "Open sky under the islands (below_horizon: sky); any fall lands on X2."}],
        'links': links(polys),
        'loops': [
            {'id': 'loop:west_ring', 'spaces': ['room:stair_head', 'room:west_wing', 'room:sw_nest', 'room:west_pillar',
             'room:west_spine', 'room:west_shelf', 'room:nw_isle', 'room:back_lot', 'room:carnival', 'room:landing',
             'room:brink'], 'notes': 'Up the west chain to the carnival, back over the unseen way.'},
            {'id': 'loop:east_ring', 'spaces': ['room:stair_head', 'room:east_wing', 'room:se_nest', 'room:east_pillar',
             'room:east_ledge', 'room:east_horn', 'room:aviary', 'zone:castle', 'room:gate_court', 'room:carnival',
             'room:landing', 'room:brink'], 'notes': "Up the east chain to the aviary, round the castle's apron."},
        ],
        'entrances': [
            {'id': 'entrance:xd12_roof', 'space': 'room:stair_head', 'kind': 'arrival', 'neighbour': 'roof:xd12',
             'facing': 'n', 'how': "The top step of XD-12's cloud stair rising out of the cloud sea (as X8's stair heads).",
             'notes': f"{at_text(places['entrance:xd12_roof'])}, z 320, facing north (MoveToMap direction 512)."},
            {'id': 'entrance:xd19_gate', 'space': 'room:gate_court', 'kind': 'both', 'neighbour': 'door:xd19',
             'facing': 's', 'how': ("Castle Xeen's gate leads into XD-19; XD-19's way out and the scepter "
                                     "cinematic's leave (D-47 Q14) arrive here, 512 south of the leaves."),
             'notes': f"{at_text(places['entrance:xd19_gate'])}, z 768 (the castle cloud's apron), facing south (1536)."},
            {'id': 'entrance:fd04_roof', 'space': 'room:dragon_clouds', 'kind': 'arrival', 'neighbour': 'roof:fd04',
             'facing': 's', 'how': "The Dragon Tower's roof stair (FD-04, phase 6). Sealed until FD-04 and Q-F1 exist.",
             'notes': f"{at_text(G.SPACE['room:dragon_clouds']['at'])}, z 2048."},
            {'id': 'entrance:fall', 'space': 'void:cloud_sea', 'kind': 'exit', 'neighbour': 'fall:x2',
             'how': "Any fall off a cloud: to X2, on Darzog's island by the tower door."},
        ],
        'critical_path': ['room:stair_head', 'room:brink', 'room:landing', 'room:carnival', 'room:gate_court'],
        'return_path': ['room:gate_court', 'room:carnival', 'room:landing', 'room:brink'],
        'goals': [
            {'id': 'goal:dolls', 'space': 'room:carnival', 'kind': 'use', 'what': "Win Slick's four games",
             'story': 'M34'},
            {'id': 'goal:cupie', 'space': 'room:gate_court', 'kind': 'take', 'what': 'The Lord Xeen doll (12371)',
             'story': 'M34', 'gives': {'qbit': 'm34_done'}},
            {'id': 'goal:castle', 'space': 'room:gate_court', 'kind': 'reach', 'what': "Castle Xeen's gate",
             'story': 'M35'},
        ],
        'points_of_interest': pois(polys),
        'landmarks': [
            {'id': 'landmark:castle_xeen', 'space': 'zone:castle',
             'what': 'Castle Xeen: black walls, gold friezes and caps, four round towers and a keep',
             'seen_from': ['room:stair_head', 'room:brink', 'room:landing', 'room:carnival', 'room:nw_isle',
                           'room:east_horn']},
            {'id': 'landmark:carnival', 'space': 'room:carnival', 'what': "Slick's striped awnings and the bell pole",
             'seen_from': ['room:brink', 'room:landing', 'room:back_lot']},
            {'id': 'landmark:aviary', 'space': 'room:aviary', 'what': 'Rock spurs, great nests and circling rocs',
             'seen_from': ['room:brink', 'room:gate_court', 'room:east_horn', 'room:se_nest']},
            {'id': 'landmark:dragon_clouds', 'space': 'room:dragon_clouds',
             'what': "A high lone cloud with a dragon-head rock, out of reach",
             'seen_from': ['room:aviary', 'room:east_horn', 'room:brink']},
        ],
        'sightlines': [
            {'id': 'view:xeendom', 'from': 'room:brink',
             'to': ['landmark:castle_xeen', 'landmark:carnival', 'landmark:aviary', 'landmark:dragon_clouds'],
             'what': ("The signature: from the 'Xeen--9N.' sign over the gap and the faint way, Xeendom rising in "
                      "terraces to Castle Xeen, the carnival on the left, the aviary's rocs on the right."),
             'notes': (f"camera {at_text(figures['signature']['at'])}, z {figures['signature']['z']} (eye), facing "
                       f"north; the gate {figures['signature']['to_gate']:,} away")},
        ],
        'set_pieces': [
            {'id': 'set:unseen_way', 'kind': 'puzzle', 'spaces': ['room:brink', 'room:landing'],
             'rule': ("'Xeen--9N.': a 768-wide way (D-50) nine cells (4,608) due north from the sign over the open gap, "
                      "falling 192. How visible it is is decision 1."),
             'solution': 'Walk straight north from the sign.'},
            {'id': 'set:carnival', 'kind': 'puzzle', 'spaces': ['room:carnival', 'room:gate_court'],
             'rule': ("Slick's four booths (A3's hooks; the clicking member's statistic, retry on a loss), the prize "
                      "stand, then the gate.")},
            {'id': 'set:fall', 'kind': 'scripted', 'spaces': ['void:cloud_sea'],
             'rule': ("As X8: a one-second check moves a party below z -1,000 (and the room's safety floor at -6,000) "
                      "through A3's Xeen.skyFall to X2, Darzog's island by the tower door "
                      f"{D.FALL_LANDING_X2['at']} (cell {list(D.FALL_LANDING_X2['cell'])}), ground 768, with falling damage.")},
            {'id': 'set:castle_gone', 'kind': 'scripted', 'spaces': ['zone:castle', 'room:gate_court'],
             'rule': "On m35.done (111707) the castle's shell is hidden and its gate sealed; its cloud stays (state:castle_gone)."},
        ],
        'states': [
            {'id': 'state:castle_gone', 'condition': {'qbit': 'm35_done'},
             'hides': ["Castle Xeen's shell (walls, towers, keep, gate leaves)"], 'seals': ['link:gate'],
             'effects': ["The gate spot reads 'The great Castle Xeen recently stood here.' (aaze0027:44).",
                         "XD-19's return point stays: the scepter cinematic's leave and a Lloyd's Beacon set inside still land there."],
             'notes': "D-47 Q14 (a). Burlock's after-line: 'Castle Xeen is a cloud again.'"},
        ],
        'height_bands': [
            {'id': 'band:sea', 'level': -2000, 'spaces': ['void:cloud_sea'], 'notes': 'the cloud sea, far below'},
            {'id': 'band:south', 'range': Flow([320, 512]), 'spaces': ['room:stair_head', 'room:brink',
             'room:west_wing', 'room:east_wing', 'room:sw_nest', 'room:se_nest']},
            {'id': 'band:chains', 'range': Flow([384, 704]), 'spaces': ['room:west_pillar', 'room:west_spine',
             'room:west_shelf', 'room:nw_isle', 'room:east_pillar', 'room:east_ledge', 'room:east_horn']},
            {'id': 'band:xeendom', 'range': Flow([256, 1024]), 'spaces': ['room:landing', 'room:carnival',
             'room:back_lot', 'room:gate_court', 'zone:castle', 'room:aviary'],
             'notes': 'rising in terraces from the landing (256) to the castle (768) and the aviary (1,024)'},
            {'id': 'band:dragon', 'level': 2048, 'spaces': ['room:dragon_clouds']},
        ],
        'atmosphere': ("Sky xeencloud (xeen_cloud_sea, below_horizon: sky, high sun, daylight block); no weather; "
                       "wind; music 21. No Fly (no BLV casts it). No lighting bake (open air, X8's rule)."),
        'notes': ("MU-3 for the phase 5 review (A5, 2026-11-20). Room 88 x 84 cells (45,056 x 43,008), about 70 % of "
                  "an outdoor map's side as X8's 76 x 64 is 60 %. Board: output/studio_cal/x9/mockups/board_x9.png; "
                  "tools output/studio_cal/x9/tools/ (run.sh). Source: the Clouds of Xeen, MM4 maze 27 with "
                  "x106-x108 (xeen/aaze0027)."),
    }
    if figures:
        doc['totals'] = {
            'placed_monsters': figures['monsters'],
            'kill_xp_per_member': figures['kill_xp_member'],
            'chests': figures['kinds'].get('chest', 0),
            'points_of_interest': figures['poi_census'],
            'walkable_area_millions': figures['walk_area_m'],
            'quiet_share': figures['quiet_share'],
            'longest_bridge': figures['bridge_range'][1],
        }
    return doc


def project():
    return {
        'format': 0,
        'id': 'xeen_x9',
        'name': 'Clouds of Xeen',
        'world': 'xeen',
        'kind': 'indoor',
        'profile': 'region',
        'map_code': 'X9',
        'units': {'plan_grid': 512},
        'extent': {'footprint_cells': Flow(list(D.ROOM))},
        'map_stats': {
            'id': 9107, 'encounter_chance': 0, 'treasure_level': 5, 'trap_dice': 5, 'perception_difficulty': 5,
            'refill_days': 672, 'music': 21, 'environment': 'plains', 'lock_difficulty': 10,
            'slots': [
                {'monster': 'Xeen Roc', 'tier': 1, 'per_marker': Flow([2, 3]), 'weight': 80},
                {'monster': 'Xeen Elemental Golem', 'tier': 2, 'per_marker': Flow([1, 3]), 'weight': 20},
            ],
        },
        'neighbours': [
            {'id': 'roof:xd12', 'to': 'xeen_xd12.blv', 'kind': 'roof', 'listed_only': True,
             'notes': ("One way up: XD-12's cloud stair (A8's exit:clouds_of_xeen, sealed until X9 exists) arrives at "
                       "entrance:xd12_roof. No way back down but falling or Lloyd's Beacon.")},
            {'id': 'door:xd19', 'to': 'xeen_xd19.blv', 'kind': 'door',
             'notes': ("Castle Xeen's gate into XD-19's entrance:x9_gate (A7); XD-19's exit and the scepter's leave "
                       "come back to entrance:xd19_gate.")},
            {'id': 'roof:fd04', 'to': 'xeen_fd04.blv', 'kind': 'roof', 'listed_only': True,
             'notes': 'Q-F1 (Act VI, optional): the Dragon Tower roof to the Dragon Clouds. Sealed until FD-04 exists.'},
            {'id': 'fall:x2', 'to': 'xeen_x2.odm', 'kind': 'fall',
             'notes': (f"Every fall lands on X2 at {D.FALL_LANDING_X2['at']} (cell {list(D.FALL_LANDING_X2['cell'])}), "
                       "Darzog's island between the tower's east door and the jetty, ground 768, facing east, with "
                       "falling damage (a level-46 party loses little; Feather Fall none).")},
        ],
        'qbits': {'m21_crodo_freed': 110501, 'm34_done': 111685, 'm35_done': 111707},
        'items': {'might_doll': 12367, 'speed_doll': 12368, 'endurance_doll': 12369, 'accuracy_doll': 12370,
                  'lord_xeen_doll': 12371},
        'rules': {
            'no_fly': True,
            'weather': 'none',
            'fall_through': {'below': -1000, 'to': 'fall:x2', 'landing': Flow(list(D.FALL_LANDING_X2['at'])) },
        },
        'notes': ("X9 Clouds of Xeen, MU-3 plan for the phase 5 review (A5, 2026-11-20): an open-air BLV region "
                  "(devdocs/INDOOR_OPEN_SKY.md; X8 Cloudreach's route, briefs/x8/L4/NOTES.md) of walkable clouds "
                  "above X2. Islands are plan spaces with `at` (map units, the middle) and `extent`. The drawing and "
                  "review board: output/studio_cal/x9/mockups/."),
    }


def dump(doc, path):
    path.write_text(yaml.dump(doc, sort_keys=False, allow_unicode=True, width=118))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-census', action='store_true')
    args = parser.parse_args()
    polys = G.outlines()
    figures = json.loads((MOCK / 'figures.json').read_text()) if args.with_census else None
    if figures is None and (MOCK / 'figures.json').exists():
        figures = json.loads((MOCK / 'figures.json').read_text())
        figures_for_totals = None
    else:
        figures_for_totals = figures
    BRIEF.mkdir(parents=True, exist_ok=True)
    doc = plan(polys, figures)
    if figures_for_totals is None:
        doc.pop('totals', None)
    dump(doc, BRIEF / 'plan.yml')
    dump(project(), BRIEF / 'project.yml')


if __name__ == '__main__':
    main()
