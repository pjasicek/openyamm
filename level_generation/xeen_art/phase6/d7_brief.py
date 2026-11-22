#!/usr/bin/env python3
"""D7 The Skyroads: writes the L1 brief (project.yml, plan.yml, atmosphere.yml) from d7_design.py (A6 sub-agent,
2026-11-21).

    d7_brief.py       devdocs/xeen/briefs/d7/L1/{project,plan,atmosphere}.yml

`totals` come from d7_render.py's d7/measure.json (run d7_render.py first). The shape follows X9's L1 (A5,
briefs/x9/L1): an open-air BLV region, islands as spaces with `at` (the middle, map units) and `extent`; point
positions are in each point's `notes` or `behaviour` ("at (x, y)"), since an L1 plan has no point coordinates. Olympus
follows XD-17's town zones (`part_of`, `buildings`, `house_door` points). NOTES.md is written by hand.
"""
import json
from pathlib import Path

import yaml

import d7_design as D
import d7_geom as G

ROOT = Path(__file__).resolve().parents[3]
BRIEF = ROOT / 'devdocs/xeen/briefs/d7/L1'
MEASURE = Path(__file__).resolve().parent / 'd7' / 'measure.json'


class Flow(list):
    pass


yaml.add_representer(Flow, lambda d, v: d.represent_sequence('tag:yaml.org,2002:seq', v, flow_style=True))


def at_text(p, z=None):
    s = f'at ({round(p[0])}, {round(p[1])})'
    return s + (f', z {z}' if z is not None else '')


def group_notes(g):
    name, level, xp, mode = D.ROWS[g['actor']]
    tail = ', flying' if mode == 'fly' else ', walking: 300 or more inside the rim or the road edge'
    where = '' if g['space'].startswith('room') or g['space'].startswith('zone') else f" on {g['space']}"
    return f"{g['count']} {name}s ({level}) as one group, {at_text(g['at'])}{where}{tail}"


def population():
    out = {}
    for g in D.GROUPS:
        sp = g['space']
        if sp.startswith('link:'):
            # a group on a road belongs to the nearer island of that link for the plan
            l = next(l for l in D.LINKS if l['id'] == sp)
            sp = min((l['a'], l['b']), key=lambda s: G.dist(D.SPACE[s]['at'], g['at']))
        out.setdefault(sp, []).append({'id': g['id'], 'actor': str(g['actor']), 'groups': g['count'], 'placed': True,
                                       'hostile': True, 'notes': group_notes(g)})
    b = D.BOSS
    out.setdefault(b['space'], []).append({
        'id': b['id'], 'actor': str(b['actor']), 'groups': 1, 'placed': True, 'hostile': True,
        'notes': f"the Megadragon (125, Q-D26, optional), {at_text(b['at'])} on Alamar's roof hatch, leash "
                 f"{b['leash']}; flying but leashed to the roost. Its leash circle stands {D.BREATH_MARGIN:,} or more "
                 f"from every other walkable place (D-54's rule, Dragon Breath); not in the 50"})
    for bd in D.BANDITS:
        out.setdefault(bd['space'], []).append({
            'id': bd['id'], 'actor': 'Sky Bandit (A2 row asked, question 3)', 'groups': bd['count'], 'placed': True,
            'hostile': False, 'notes': f"{bd['count']} sky bandits at the toll, {at_text(bd['at'])}: peaceful until a "
                                       f"refusal (their own faction); not counted at load"})
    return out


TREASURE = {
    'room:roost': [{'kind': 'chest', 'count': 1, 'tier': 6, 'notes': "the Megadragon's hoard (Q-D26's artifact)"}],
    'room:stranded_west': [{'kind': 'chest', 'count': 1, 'tier': 6, 'notes': "the stranded traveller's strongbox"}],
    'room:stranded_south': [{'kind': 'chest', 'count': 1, 'tier': 6, 'notes': "the second castaway's strongbox"}],
    'room:skywaymen_camp': [{'kind': 'chest', 'count': 1, 'tier': 6, 'notes': "the skywaymen's strongbox (the tolls)"}],
    'room:broken_launch': [{'kind': 'chest', 'count': 1, 'tier': 6, 'notes': "a lost traveller's pack on the jetty"}],
}
QUIET = ('rest', 'corner', 'post', 'lake', 'town')


def spaces(P):
    pop = population()
    out = []
    for s in D.SPACES:
        kind = {'town': 'town', 'roost': 'room'}.get(s['kind'], 'room')
        e = {'id': s['id'], 'name': s['name'], 'kind': kind, 'extent': Flow(list(s['extent']))}
        if s.get('shape'):
            e['shape'] = s['shape']
        e['at'] = Flow(list(s['at']))
        e['floor'] = s['floor']
        e['purpose'] = s['purpose']
        if s['kind'] in QUIET:
            e['safe'] = True
            e['keep_clear'] = ['spawns']
        if s['kind'] == 'town':
            e['relief'] = 'flat'
            e['theme'] = "white marble (MM7 Celeste's Hwm/Hwp set), gold bands and domes, 7tws1f paving"
        if s['id'] in pop:
            e['population'] = pop[s['id']]
        if s['id'] in TREASURE:
            e['treasure'] = TREASURE[s['id']]
        e['notes'] = f"Source square {s['square']}; region {s['region']}; falls from it land on " \
                     f"{D.fall_zone(*s['at'])['key']} (entrance:d7_fall)."
        out.append(e)
    for z in D.OLYMPUS_ZONES:
        e = {'id': z['id'], 'name': z['name'], 'kind': 'zone', 'part_of': 'zone:olympus',
             'extent': Flow(list(z['extent'])), 'at': Flow(list(z['at'])), 'floor': D.SPACE['zone:olympus']['floor'],
             'purpose': z['purpose'], 'safe': True}
        b = [x for x in D.BUILDINGS if x[6] == z['id']]
        if b:
            e['buildings'] = [{'id': bid, 'type': 'house', 'service': service, 'count': 1, 'doors': 1,
                               'footprint_cells': Flow(list(fp)),
                               'notes': f"A4's house {house}; door {at_text(at)} facing {facing}, floor 1792"
                                        + (f"; {note}" if note else '')}
                              for bid, house, service, at, facing, fp, zone, note in b]
        out.append(e)
    out.append({'id': 'void:cloud_sea', 'name': 'The cloud sea', 'kind': 'void',
                'purpose': "Open sky under the roads (below_horizon: sky); a fall lands on the surface map beneath, "
                           "by the 3 x 2 zones (D6, D5, D4 north; D1, D2, D3 south) at entrance:d7_fall."})
    out.sort(key=lambda e: e['id'])
    return out


def links(P):
    out = []
    for l in D.LINKS:
        kind = {'road': 'road', 'causeway': 'road', 'spur': 'path', 'bridge': 'bridge'}[l['style']]
        rise = D.SPACE[l['b']]['floor'] - D.SPACE[l['a']]['floor']
        note = {'road': 'the Skyroad: cloud with a paved band of cloud-stone flags (7tws1f) down its middle',
                'causeway': 'a causeway of white marble flags on a cloud tongue',
                'spur': 'a narrow cloud road', 'bridge': "a rope bridge (X8's: t66floor deck, rope rails)"}[l['style']]
        e = {'id': l['id'], 'from': l['a'], 'to': l['b'], 'kind': kind, 'width': l['width'], 'rise': rise,
             'notes': f"{note}; {round(G.link_length(l, P)):,} rim to rim" + (f"; {l['notes']}" if l.get('notes') else '')}
        out.append(e)
    out.sort(key=lambda e: e['id'])
    return out


def entrances():
    out = []
    for a in D.ARRIVALS:
        z = D.SPACE[a['space']]['floor']
        kind = 'both' if a['kind'] == 'both' else 'arrival'
        if a['id'] == 'entrance:dd26_stair':
            kind = 'both'
        e = {'id': a['id'], 'space': a['space'], 'kind': kind}
        nb = {'house:lucio': 'boat:lucio', 'mirror': 'mirror:olympus', 'rope:d1': 'rope:d1'}.get(a['neighbour'],
                                                                                              a['neighbour'])
        e['neighbour'] = nb
        e['facing'] = a['facing']
        e['how'] = a['how']
        e['notes'] = f"{at_text(a['at'], z)}, facing {a['facing']} (MoveToMap direction {G.FACING_MM[a['facing']]})."
        out.append(e)
    for f in D.FALLS:
        out.append({'id': f'entrance:fall_{f["key"].lower()}', 'space': 'void:cloud_sea', 'kind': 'exit',
                    'neighbour': f['id'],
                    'how': f"Any fall off the roads over squares {f['squares']} (x {round(f['x'][0])}..{round(f['x'][1])}, "
                           f"y {round(f['y'][0])}..{round(f['y'][1])}): to {f['key']}'s entrance:d7_fall."})
    for c in ('fire', 'air', 'earth', 'water'):
        p = next(x for x in D.POINTS if x['id'] == f'poi:corner_{c}')
        plane = {'fire': 'p1', 'air': 'p2', 'earth': 'p3', 'water': 'p4'}[c]
        out.append({'id': f'entrance:corner_{c}', 'space': p['space'], 'kind': 'exit', 'neighbour': f'plane:{plane}',
                    'how': f"The {c.title()} Corner's tip: the sky asks 'What do you seek?'; '{c.title()}' runs "
                           f"m38.corner_{c} and drops the party onto {plane.upper()}'s entrance:d7_fall "
                           f"(corners.yml). {at_text(p['at'])}."})
    out.sort(key=lambda e: e['id'])
    return out


def pois():
    out = []
    by_kind = {}
    for p in D.POINTS:
        by_kind.setdefault(p['kind'], []).append(p)
    for p in by_kind['corner']:
        out.append({'id': p['id'], 'space': p['space'], 'kind': 'story_device',
                    'behaviour': f"The road ends in nothing: {p['text']}. A step onto the tip asks (text input); the "
                                 f"element's name runs {p['hook']} and drops the party onto its plane; any other "
                                 f"answer m38.corner_wrong. The zone board within 400 (one spot). {at_text(p['at'])}."})
    for kind, label, extra in [('toll', 'toll', "A3 hook asked: pay (the source's 10,000 gold, rescaled by A3) and "
                                                "the bandits wave the party on; refuse and they fight (question 3)."),
                               ('merchant', 'merchant', "A3 hook asked: the riddle (text input), the answer pays "
                                                        "experience once (the source's 250,000, rescaled)."),
                               ('lamp', 'lamp', "Q-D27's helper Xeen.genieLamp (A3 hooks asked: d7_tired, d7_kind, "
                                                "d7_angry)."),
                               ('bottle', 'bottle', 'A readable note (A3 text asked).')]:
        ps = by_kind[kind]
        out.append({'id': f'poi:{label}s', 'spaces': sorted({p['space'] for p in ps}), 'count': len(ps),
                    'kind': {'toll': 'scripted', 'merchant': 'riddle', 'lamp': 'curiosity', 'bottle': 'note'}[kind],
                    'behaviour': extra + ' ' + '; '.join(f"{p['id'].split(':')[1]} {at_text(p['at'])}: {p['text']}"
                                                         for p in ps),
                    'uses': {'times': 1, 'per': 'party', 'reset': 'never'} if kind != 'bottle' else None})
        if out[-1]['uses'] is None:
            del out[-1]['uses']
    sc = by_kind['scarab']
    out.append({'id': 'poi:scarab_market', 'space': 'room:sky_lake', 'count': 4, 'kind': 'shop',
                'behaviour': "Four stalls in a row on the Sky Lake's west shore, 384 apart (one spot by the census): "
                             + '; '.join(f"{p['text']} {at_text(p['at'])}" for p in sc)
                             + ". How they sell is question 5."})
    for p in by_kind['hatch'] + by_kind['door'] + by_kind['rope']:
        e = {'id': p['id'], 'space': p['space'], 'kind': 'door', 'behaviour': f"{p['text']}. {at_text(p['at'])}."}
        out.append(e)
    for p in by_kind['mirror'] + by_kind['vault'] + by_kind['plaque'] + by_kind['sewer']:
        out.append({'id': p['id'], 'space': 'zone:ol_square' if p['kind'] == 'mirror' else 'zone:ol_temple_court'
                    if p['kind'] in ('vault', 'plaque') else 'zone:ol_gods_row',
                    'kind': {'mirror': 'mirror', 'vault': 'door', 'plaque': 'sign', 'sewer': 'door'}[p['kind']],
                    'behaviour': f"{p['text']}" + (f"; {p['hook']}" if p.get('hook') else '') + f". {at_text(p['at'])}."})
    st = by_kind['statue']
    out.append({'id': 'poi:prophecy_statues', 'space': 'zone:ol_square', 'count': 4, 'kind': 'statue',
                'behaviour': "The four prophecy statues at the square's corners, A3's m31.statue_1-4 (the source's "
                             "verses, dark/aaze0037:12-15): " + '; '.join(f"{p['hook']} {at_text(p['at'])}" for p in st)})
    for bid, house, service, at, facing, fp, zone, note in D.BUILDINGS:
        out.append({'id': 'poi:' + bid.split(':')[1], 'space': zone, 'kind': 'house_door',
                    'behaviour': f"{service} (house {house}): A4's {bid}. At [{at[0]}, {at[1]}], facing {facing}, "
                                 f"floor 1792."})
    out.sort(key=lambda e: e['id'])
    return out


def boards():
    return [{'id': p['id'].replace('board:', 'landmark:'), 'space': p['space'],
             'what': f"a board, hover only (not a POI): {p['text']}, {at_text(p['at'])}"} for p in D.POINTS
            if p['kind'] == 'board']


def plan(P, f):
    doc = {
        'format': 0, 'level': 'L1',
        'pitch': "The roads of the gods over the Darkside: a ring of cloud road round the whole sky with a corner at "
                 "each element, floating Rest Stops along it, the sky bandits' tolls, the merchants of the elements "
                 "with their riddles, and genies in lamps. Inside the ring, a road from the Dark Grove's rope crosses "
                 "to Olympus on its marble cloud, past the Great Pyramid's sky door to the Sky Lake and its scarab "
                 "sellers. Off a dead-end road in the north-west the Megadragon sleeps on Castle Alamar's roof.",
        'purpose': "Act V-VI's sky map (party 55-58; reached after M30): M31 (Soul Storage in Olympus, the true-name "
                   "plaque, the prophecy statues), M38 (the four corners to the planes P1-P4), Olympus' services and "
                   "grandmasters, the side content of the Skyroads (Q-D26 the Megadragon, Q-D27's lamps, the riddles, "
                   "the tolls, the scarabs, two castaways' strongboxes), DD-26's door, and the roof ways up from "
                   "eight Darkside dungeons.",
        'mood': "Amber and high: the Darkside's failing sun from above the clouds, the cloud sea below, white marble "
                "and gold in Olympus; deadpan signs along a highway in the sky ('Speeding??', 'Eat at Joe's'); "
                "polite robbers; the danger is played straight.",
        'datum': 'zone:olympus',
        'spaces': spaces(P),
        'regions': [
            {'id': 'region:north', 'name': 'The north road', 'spaces': [s['id'] for s in D.SPACES if s['region'] == 'north'],
             'where': "Sky A1-F1 (over D6, D5, D4)"},
            {'id': 'region:east', 'name': 'The east road', 'spaces': [s['id'] for s in D.SPACES if s['region'] == 'east'],
             'where': 'Sky F1-F4 (over D4, D3)'},
            {'id': 'region:south', 'name': 'The south road', 'spaces': [s['id'] for s in D.SPACES if s['region'] == 'south'],
             'where': 'Sky A4-F4 (over D1, D2, D3)'},
            {'id': 'region:west', 'name': 'The west road and the dragon', 'spaces': [s['id'] for s in D.SPACES
                                                                                     if s['region'] == 'west'],
             'where': 'Sky A1-B4 (over D6, D1)'},
            {'id': 'region:inner', 'name': 'The inner road', 'spaces': [s['id'] for s in D.SPACES if s['region'] == 'inner'],
             'where': 'Sky B3, C2, C3, D2, E3'},
        ],
        'links': links(P),
        'loops': [
            {'id': 'loop:ring', 'spaces': ['room:fire_corner', 'room:griffin_watch', 'room:north_crossing',
                                           'room:north_toll', 'room:east_rest', 'room:air_corner', 'room:mud_wharf',
                                           'room:east_junction', 'room:earth_corner', 'room:south_rest',
                                           'room:steam_post', 'room:south_toll', 'room:skywaymen_camp',
                                           'room:water_corner', 'room:west_toll', 'room:rope_head', 'room:smoke_post',
                                           'room:west_lookout'],
             'notes': f"The Skyroad round the whole sky, {f['ring_length']:,} long through the islands' middles."},
            {'id': 'loop:west', 'spaces': ['room:rope_head', 'room:broken_launch', 'zone:olympus', 'room:north_crossing',
                                           'room:griffin_watch', 'room:fire_corner', 'room:west_lookout', 'room:smoke_post'],
             'notes': 'The rope, the inner road to Olympus, out of its north gate and round by the Fire Corner.'},
            {'id': 'loop:east', 'spaces': ['zone:olympus', 'room:pyramid_cap', 'room:sky_lake', 'room:east_junction',
                                           'room:mud_wharf', 'room:air_corner', 'room:east_rest', 'room:north_toll',
                                           'room:north_crossing'],
             'notes': "Olympus' east gate, the Pyramid's door, the Sky Lake, up the east road and home by the north."},
        ],
        'entrances': entrances(),
        'critical_path': ['zone:olympus', 'room:north_crossing', 'room:griffin_watch', 'room:fire_corner',
                          'room:west_lookout', 'room:smoke_post', 'room:rope_head', 'room:west_toll', 'room:water_corner'],
        'return_path': ['room:water_corner', 'room:west_toll', 'room:rope_head', 'room:broken_launch', 'zone:olympus'],
        'goals': [
            {'id': 'goal:soul_box', 'space': 'zone:ol_temple_court', 'kind': 'take', 'what': 'The Soul Box (12363) in Soul Storage',
             'story': 'M31', 'gives': {'qbit': 'm31_done'}},
            {'id': 'goal:true_name', 'space': 'zone:ol_temple_court', 'kind': 'use',
             'what': "Read the plaque: Alamar's true name is Sheltem", 'story': 'M31', 'gives': {'qbit': 'm31_true_name'}},
            {'id': 'goal:corners', 'space': 'room:fire_corner', 'kind': 'use',
             'what': "Step off the four corners with the element's name (Fire, Air, Earth, Water)", 'story': 'M38'},
            {'id': 'goal:megadragon', 'space': 'room:roost', 'kind': 'kill',
             'what': "The Megadragon, for the hoard and the key to Alamar's roof (optional)", 'story': 'Q-D26'},
        ],
        'points_of_interest': pois(),
        'landmarks': [
            {'id': 'landmark:olympus', 'space': 'zone:olympus',
             'what': "White marble and gold on a raised cloud: the temple's gold dome, the gates' gilded posts",
             'seen_from': ['room:rope_head', 'room:broken_launch', 'room:north_crossing', 'room:pyramid_cap',
                           'room:griffin_watch', 'room:sky_lake']},
            {'id': 'landmark:capstone', 'space': 'room:pyramid_cap',
             'what': "The Great Pyramid's golden capstone floating over its cloud, cloud dragons circling",
             'seen_from': ['zone:olympus', 'room:sky_lake', 'room:rope_head']},
            {'id': 'landmark:roost', 'space': 'room:roost',
             'what': "A black crag on a high cloud with something huge asleep on it",
             'seen_from': ['room:griffin_watch', 'room:smoke_post', 'room:west_lookout', 'zone:olympus']},
            {'id': 'landmark:corner_glows', 'space': 'void:cloud_sea',
             'what': "Under each corner's tip the cloud sea glows its element's colour (red, white wind, grey, blue)",
             'seen_from': ['room:fire_corner', 'room:air_corner', 'room:earth_corner', 'room:water_corner']},
            {'id': 'landmark:rope', 'space': 'room:rope_head', 'what': 'The Dark Grove rope hanging into a hole in the cloud',
             'seen_from': ['room:broken_launch']},
        ] + boards(),
        'sightlines': [
            {'id': 'view:arrival', 'from': 'room:rope_head',
             'to': ['landmark:olympus', 'landmark:capstone'],
             'what': "The arrival: up the Dark Grove rope onto the Skyroad, the 'XEEN Skyroad' board at the inner "
                     "road's start, the road east to the Broken Launch and its golems, Olympus' gold dome far off on "
                     "the left, the capstone ahead, the Sky Lake's clouds on the right.",
             'notes': f"camera {at_text(D.CAMERAS['arrival']['at'], D.CAMERAS['arrival']['z'])} (eye), yaw "
                      f"{D.CAMERAS['arrival']['yaw_deg']} degrees (east-north-east); Olympus 25,600 away"},
            {'id': 'view:olympus', 'from': 'room:pyramid_cap', 'to': ['landmark:olympus', 'landmark:roost'],
             'what': "The signature: from the east causeway at the Pyramid's door, Olympus across the cloud roads, "
                     "raised on its marble cloud, the north causeway and the inner road leaving it, under the "
                     "Skyroads' amber sky.",
             'notes': f"camera {at_text(D.CAMERAS['signature']['at'], D.CAMERAS['signature']['z'])} (eye), yaw "
                      f"{D.CAMERAS['signature']['yaw_deg']} degrees (west); the east gate 6,300 away, the city's "
                      f"middle 11,000"},
        ],
        'set_pieces': [
            {'id': 'set:corners', 'kind': 'scripted', 'spaces': ['room:fire_corner', 'room:air_corner',
                                                                   'room:earth_corner', 'room:water_corner'],
             'rule': "corners.yml: each corner's tip asks 'What do you seek?' (the source's line); the element's name "
                     "runs m38.corner_<element> and the map moves the party to its plane's entrance:d7_fall; another "
                     "answer runs m38.corner_wrong. Each plane's way out returns to entrance:pN_return."},
            {'id': 'set:tolls', 'kind': 'ambush', 'spaces': ['room:north_toll', 'room:mud_wharf', 'room:south_toll',
                                                             'room:west_toll'],
             'rule': "Sky bandits stop the party at four places, each with its own line of the source; pay and pass "
                     "(once), or refuse and the two bandits there fight. Question 3."},
            {'id': 'set:riddles', 'kind': 'puzzle', 'spaces': ['room:smoke_post', 'room:north_crossing',
                                                               'room:steam_post', 'room:mud_wharf'],
             'rule': "The Merchants of the Elements: 'Between Fire and Air I constantly travel...What's my cargo?' "
                     "smoke, dust (Air and Earth), steam (Fire and Water), mud (Water and Earth).",
             'solution': 'smoke, dust, steam, mud'},
            {'id': 'set:megadragon', 'kind': 'boss', 'spaces': ['room:roost'],
             'rule': "Q-D26 (optional): the Megadragon on Alamar's roof hatch. Its road leaves the Smoke Post with a "
                     "'DANGER! Mega Dragon' board; no other road comes within its breath. The hatch reads the "
                     "source's lines until the key from its hoard opens it."},
            {'id': 'set:castaways', 'kind': 'puzzle', 'spaces': ['room:sky_lake', 'room:stranded_west',
                                                                 'room:stranded_south'],
             'rule': "Two bottles at the Sky Lake name the source squares A2 at 12,14 and C3 at 7,0; each is a small "
                     "island with a strongbox, both out of the Megadragon's reach (D-58 D-2).",
             'solution': 'Find the islands off the West Lookout and the Genie\'s Rock.'},
            {'id': 'set:fall', 'kind': 'scripted', 'spaces': ['void:cloud_sea'],
             'rule': "As X8 and X9: a one-second check moves a party below z -1,000 (and the room's floor at -6,000 "
                     "catches the rest) through A3's Xeen.skyFall to the surface map under that part of the sky, "
                     "at its entrance:d7_fall, with falling damage (about a third of a level-55 party's HP, D-6.2)."},
        ],
        'height_bands': [
            {'id': 'band:north', 'level': 1280, 'spaces': [s['id'] for s in D.SPACES if s['region'] == 'north'],
             'notes': 'the north road, the highest stretch of the ring'},
            {'id': 'band:south', 'level': 768, 'spaces': [s['id'] for s in D.SPACES if s['region'] == 'south'],
             'notes': 'the south road'},
            {'id': 'band:sides', 'range': Flow([768, 1280]),
             'spaces': [s['id'] for s in D.SPACES if s['region'] in ('east', 'west')],
             'notes': 'the east and west roads climb from the south road to the north road (1:30 or gentler)'},
            {'id': 'band:inner', 'range': Flow([896, 1792]),
             'spaces': [s['id'] for s in D.SPACES if s['region'] == 'inner'],
             'notes': "Olympus on the highest cloud (1,792); the Sky Lake's bowl the lowest (896)"},
            {'id': 'band:sea', 'level': -2000, 'spaces': ['void:cloud_sea'], 'notes': 'the cloud sea, far below'},
        ],
        'atmosphere': "Sky preset xeen_skyroads (alias xeenroads; Darkside's amber day with below_horizon: sky) in "
                      "the open_sky block (a preset name, never the alias, lanes README); outdoor view at 2x; no "
                      "weather; wind; music 30. No Fly (no BLV casts it). No lighting bake (open air, X8's rule).",
        'totals': {
            'placed_monsters': f['placed_monsters'],
            'kill_xp_per_member': f['kill_xp_per_member'],
            'kill_xp_per_member_with_megadragon': f['kill_xp_per_member_with_megadragon'],
            'points_of_interest': f['points_of_interest'],
            'chests': f['chests'],
            'walkable_area_millions': f['walkable_area_millions'],
            'quiet_share': f['quiet_share'],
            'ring_length': f['ring_length'],
            'longest_road_link': f['road_links']['max'],
        },
        'notes': "MU-3 for the phase 6 review (A6 sub-agent, 2026-11-21). Room 128 x 88 cells (65,536 x 45,056), one "
                 "outdoor map's side long (MAPS: ~1 ODM). Source: MM5's Skyroads, dark mazes 89-112 (Sky A1-F4), texts "
                 "dark/aaze0089-0099, aazex100-112. Drawings and board: level_generation/xeen_art/phase6/d7/; tools "
                 "level_generation/xeen_art/phase6/d7_*.py and board_d7.py; run output/studio_cal/d7/run.sh.",
    }
    return doc


def project():
    return {
        'format': 0, 'id': 'xeen_d7', 'name': 'The Skyroads', 'world': 'xeen', 'kind': 'indoor', 'profile': 'region',
        'map_code': 'D7', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': Flow(list(D.ROOM))},
        'map_stats': {'id': 9114, 'encounter_chance': 0, 'treasure_level': 6, 'trap_dice': 6, 'perception_difficulty': 6,
                      'refill_days': 672, 'music': 30, 'environment': 'plains', 'lock_difficulty': 12,
                      'slots': [{'monster': 'Xeen Elemental Golem', 'tier': 2, 'per_marker': Flow([1, 3]), 'weight': 50},
                                {'monster': 'Xeen Roc', 'tier': 2, 'per_marker': Flow([2, 3]), 'weight': 25},
                                {'monster': 'Xeen Dark Dragon', 'tier': 0, 'per_marker': Flow([1, 3]), 'weight': 25}]},
        'neighbours': neighbours(),
        'qbits': {'m30_done': 111600, 'm31_started': 111620, 'm31_done': 111621, 'm31_true_name': 111622,
                  'm38_fire': 111760, 'm38_air': 111761, 'm38_earth': 111762, 'm38_water': 111763,
                  'mirror_olympus': 119012},
        'items': {'soul_box': 12363},
        'rules': {'no_fly': True, 'weather': 'none', 'town_buffer': G.TOWN_BUFFER,
                  'fall_through': {'below': -1000, 'zones': [
                      {'to': f['id'], 'x': Flow([round(f['x'][0]), round(f['x'][1])]),
                       'y': Flow([round(f['y'][0]), round(f['y'][1])]), 'arrival': 'entrance:d7_fall',
                       'landing': Flow(list(f['landing']))} for f in D.FALLS]}},
        'notes': "D7 The Skyroads, MU-3 plan for the phase 6 review (A6 sub-agent, 2026-11-21): an open-air BLV "
                 "region (devdocs/INDOOR_OPEN_SKY.md; X8 and X9's route) of cloud roads and islands over the whole "
                 "Darkside, with Olympus (A4's d7.yml) on its own cloud. Islands are plan spaces with `at` (map units, "
                 "the middle) and `extent`. The corner contract with P1-P4: level_generation/xeen_art/phase6/corners.yml. "
                 "Drawings and board: level_generation/xeen_art/phase6/d7/.",
    }


def neighbours():
    out = []
    for f in D.FALLS:
        out.append({'id': f['id'], 'to': f['map'], 'kind': 'fall', 'arrival': 'entrance:d7_fall',
                    'notes': f"Falls over squares {f['squares']} land on {f['key']} at {tuple(f['landing'][:2])}, "
                             f"ground {f['landing'][2]}, facing {f['facing']}: {f['near']}; with falling damage "
                             f"(Feather Fall none). {f['owner']} adds entrance:d7_fall there (request)."})
    for n, (plane, el) in enumerate([('p1', 'Fire'), ('p2', 'Air'), ('p3', 'Earth'), ('p4', 'Water')]):
        out.append({'id': f'plane:{plane}', 'to': f'xeen_{plane}.blv', 'kind': 'scripted', 'arrival': 'entrance:d7_fall',
                    'notes': f"corners.yml: the {el} Corner's tip, m38.corner_{el.lower()}; the plane's way out comes "
                             f"back to entrance:{plane}_return."})
    out.append({'id': 'rope:d1', 'to': 'xeen_d1.odm', 'kind': 'scripted', 'arrival': 'entrance:d7_rope',
                'notes': "The Dark Grove rope, both ways after m30.done (D-23): up from D1's rope (m30.grove_rope) to "
                         "entrance:d1_rope; 'Pull up the rope?' (aaze0091:6) / 'Descend to the Darkness Below?' (:5) "
                         "back down to D1's rope foot (-8192, 14336, 1088), facing 768 (A6 names it entrance:d7_rope)."})
    out.append({'id': 'boat:lucio', 'to': 'xeen_d1.odm', 'kind': 'boat', 'listed_only': True,
                'notes': "D-5.3: Lucio's celestial boats sail up only, from Castleview's jetty (D1, 4901), Sandcaster's "
                         "(D3, 4649) and Lakeside's dock (D4, route 426), twice a week after m30.done, to "
                         "entrance:olympus_dock. No boat leaves D7."})
    out.append({'id': 'mirror:olympus', 'to': 'xeen_d1.odm', 'kind': 'mirror', 'listed_only': True,
                'notes': "The Mirror of Olympus (A4's house 4807, qbit 119012): to the discovered Darkside mirrors; "
                         "the others' and Town Portal's arrival here is entrance:olympus_square."})
    for key, stem, owner, name in [('dd02', 'xeen_dd02.blv', 'A8', "Ellinger's Tower's top floor"),
                                   ('dd03', 'xeen_dd03.blv', 'A8', "Castle Kalindra's third floor (stage 4)"),
                                   ('dd05', 'xeen_dd05.blv', 'A8', "the Western Tower's roof"),
                                   ('dd06', 'xeen_dd06.blv', 'A7', "the Southern Tower's roof"),
                                   ('dd07', 'xeen_dd07.blv', 'A7', "the Eastern Tower's roof"),
                                   ('dd08', 'xeen_dd08.blv', 'A8', "the Northern Tower's roof"),
                                   ('dd14', 'xeen_dd14.blv', 'A8', "Castle Blackfang's roost trapdoor")]:
        out.append({'id': f'roof:{key}', 'to': stem, 'kind': 'roof', 'listed_only': True,
                    'notes': f"One way up (WORLD_DESIGN 3.3, D-5.3; question 2): {name} ({owner}) to "
                             f"entrance:{key}_roof. The hatch on D7 reads the source's line and 'Bolted from below.'"})
    out.append({'id': 'door:dd15', 'to': 'xeen_dd15.blv', 'kind': 'door', 'arrival': 'entrance:d7_sky',
                'condition': {'qbit': 'm30_done'},
                'notes': "The Great Pyramid's sky door (the source's D2 'Enter the Pyramid?'), both ways for the Chosen "
                         "Ones; A8 names DD-15's arrival entrance:d7_sky and its way out to entrance:dd15_sky."})
    out.append({'id': 'door:dd17', 'to': 'xeen_dd17.blv', 'kind': 'door', 'arrival': 'entrance:d7_roof',
                'notes': "Castle Alamar's roof hatch under the Megadragon (Q-D26): locked with the source's line until "
                         "the key from the hoard; then both ways (A8's DD-17 adds entrance:d7_roof)."})
    out.append({'id': 'door:dd26', 'to': 'xeen_dd26.blv', 'kind': 'door', 'arrival': 'entrance:d7_stair',
                'notes': "The Olympus Sewer's stair under a marble grate in the gods' row (A8, Q-D28); its way out comes "
                         "back to entrance:dd26_stair."})
    out.sort(key=lambda e: e['id'])
    return out


def atmosphere():
    return {'format': 0,
            'open_sky': {'mode': 'open', 'preset': 'xeen_skyroads', 'view': 'outdoor', 'view_distance_scale': 2},
            'daylight': {'ambient_rgb': Flow([120, 110, 104]), 'sun_rgb': Flow([255, 232, 196]),
                         'night_scale_rgb': Flow([134, 143, 168]), 'sun_gain': 3},
            'notes': "The Skyroads' preset xeen_skyroads (Darkside's amber day, below_horizon: sky; question 9 for the "
                     "failing-sun stages); an outdoor view at 2x so that the far side of the ring (about 56,000 "
                     "across) and Olympus from the rope read; no weather; a warm daylight block after X9's."}


def dump(doc, path):
    path.write_text(yaml.dump(doc, sort_keys=False, allow_unicode=True, width=118))


def main():
    P = G.polys()
    f = json.loads(MEASURE.read_text())
    BRIEF.mkdir(parents=True, exist_ok=True)
    dump(plan(P, f), BRIEF / 'plan.yml')
    dump(project(), BRIEF / 'project.yml')
    dump(atmosphere(), BRIEF / 'atmosphere.yml')
    print('written', BRIEF)


if __name__ == '__main__':
    main()
