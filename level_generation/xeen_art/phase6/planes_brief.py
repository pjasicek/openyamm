#!/usr/bin/env python3
"""Writes the planes' L1 briefs from planes_design.py and the measures of planes_render.py (A6's planes sub-agent,
2026-11-21): devdocs/xeen/briefs/<key>/L1/{project,plan,atmosphere}.yml and NOTES.md, in the studio's schema as X9's
and P5's L1 (an open-air BLV region, spaces with `at` and `extent`, point positions in each point's notes).

    planes_brief.py p1 [p2 ...]          (run planes_render.py first: it writes planes/<key>/measure.json)
"""
import argparse
import json
from pathlib import Path

import yaml

import planes_design as D
import planes_geom as G

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MEASURES = HERE / 'planes'
CORNERS = yaml.safe_load((HERE / 'corners.yml').read_text())


class Flow(list):
    pass


yaml.add_representer(Flow, lambda dumper, data: dumper.represent_sequence('tag:yaml.org,2002:seq', data,
                                                                         flow_style=True))


def at_text(xy):
    return f'at ({round(xy[0])}, {round(xy[1])})'


def poi_id(pid):
    return {'exit:way_up': 'poi:way_up', 'exit:dais': 'poi:dais'}.get(pid, pid)


HAZARD_HOOK = {'fire': 'vent', 'air': 'storm', 'earth': 'rockfall', 'water': 'wave'}


def corner(d):
    return CORNERS['corners'][d['element']]


def test_qbit(d):
    # P-1: the test's qbit, A3's name m38.<element>_test (quest_hooks.yml m38.test_<element>_passed)
    return f"m38_{d['element']}_test"


# ------------------------------------------------------------------------------------------------ plan.yml
def plan(pl, f):
    d = pl.d
    el, El = d['element'], d['Element']
    qbit = f'm38_{el}'
    spaces = []
    chests_by_space = {}
    for p in d['places']:
        if p['kind'] == 'chest':
            chests_by_space.setdefault(p['space'], []).append(p)
    for s in d['spaces']:
        e = {'id': s['id'], 'name': s['name'], 'kind': 'room', 'at': Flow(list(s['at'])),
             'extent': Flow(list(s['extent'])), 'floor': s['floor'], 'shape': s['shape'], 'relief': 'flat',
             'purpose': s['purpose']}
        if s.get('safe'):
            e['safe'] = True
            e['keep_clear'] = ['spawns']
        pop = []
        for g in d['groups']:
            if g['space'] == s['id']:
                row = D.ROWS[g['row']]
                pop.append({'id': g['id'], 'actor': row['actor'], 'groups': 1,
                            'per_marker': Flow([g['count'], g['count']]), 'levels': Flow([row['level'], row['level']]),
                            'placed': True, 'notes': f"{g['count']} {row['short']} ({row['level']}) as one group, "
                                                     f"{at_text(g['at'])}" + (", the first fight" if g.get('first')
                                                                              else '')})
        if pop:
            e['population'] = pop
        tr = []
        for c in chests_by_space.get(s['id'], []):
            tr.append({'kind': 'chest', 'count': 1, 'tier': 6, 'notes': f"{c['text']} {at_text(c['at'])}"})
        for p in d['places']:
            if p['space'] == s['id'] and p['kind'] == 'device' and 'A find' in p['text']:
                tr.append({'kind': 'floor_item', 'count': 1, 'tier': 6,
                           'notes': f"{p['id'].split(':')[1].replace('_', ' ')}: the find, {at_text(p['at'])}"})
        if tr:
            e['treasure'] = tr
        spaces.append(e)
    if 'low' in d:
        lo = d['low']
        z = {'id': lo['id'], 'name': lo['name'], 'kind': 'zone', 'floor': lo['level'],
             'shape': (f"{lo['shape']}: {f['low_area_m']} M units, {round(100 * f['low_share'])} % of the basin, "
                       f"ringed by {d['rim']['text']}"),
             'relief': 'flat', 'keep_clear': ['spawns'], 'purpose': lo['purpose']}
        swim = [g for g in d['groups'] if g.get('swims')]
        if swim:
            z.pop('keep_clear')
            z['population'] = [{'id': g['id'], 'actor': D.ROWS[g['row']]['actor'], 'groups': 1,
                                'per_marker': Flow([g['count'], g['count']]),
                                'levels': Flow([D.ROWS[g['row']]['level']] * 2), 'placed': True,
                                'notes': f"{g['count']} {D.ROWS[g['row']]['short']} ({D.ROWS[g['row']]['level']}), "
                                         f"swimming, {at_text(g['at'])}"} for g in swim]
        spaces.append(z)
    else:
        spaces.append({'id': 'void:sky', 'name': 'The sky', 'kind': 'void',
                       'purpose': ("Open sky round, over and under the islands (below_horizon: sky); a fall is "
                                   "caught by the wind and lands on the Gale Landing (question 1).")})
    links = []
    for l in d['links']:
        e = {'id': l['id'], 'from': l['a'], 'to': l['b'],
             'kind': d['gate_kind'] if l.get('gate') else l['kind'],
             'width': l['width'], 'rise': f['links'][l['id']]['rise']}
        if l.get('gate'):
            e['condition'] = {'qbit': test_qbit(d)}
            e['opened_by'] = 'set:test'
        words = {'crust': 'a causeway of cooled black crust over the lava, low banks both sides',
                 'glass': "an obsidian bridge over the lava", 'cloudstone': 'a bridge of cloud-stone over the sky',
                 'stair': 'cloud-stone steps over the sky', 'ramp': 'a stone ramp between terraces over the scree',
                 'arch': 'a natural stone arch over the scree', 'rootstair': 'rough steps cut down the bowl\'s bottom',
                 'walk': 'a colonnade walk on the drowned temple\'s wall tops, steps down to the water both sides',
                 'veil': 'a colonnade under a falling sheet of water'}
        e['notes'] = (f"{words[l['style']]}; {f['links'][l['id']]['length']:,} rim to rim"
                      + (f"; {l['notes']}" if l.get('notes') else ''))
        links.append(e)
    crit = d['critical']
    c = corner(d)
    entrances = [
        {'id': 'entrance:d7_fall', 'space': 'room:landing', 'kind': 'arrival', 'neighbour': 'corner:d7',
         'facing': pl.place['entrance:d7_fall']['face'],
         'how': (f"The drop from D7's {c['d7_corner']} corner ({d['corner_sky']} in the source) after the sky's "
                 f"'What do you seek?' is answered '{El}' ({c['d7_hook']}): the party lands standing on "
                 f"{pl.space['room:landing']['name']} (D-58 C2: no falling damage; Xeen.toPlane(\"{el}\"), "
                 f"Xeen.PlaneArrivals.{el})."),
         'notes': f"{at_text(pl.place['entrance:d7_fall']['at'])}, z 0, quiet ground (keep_clear spawns)"},
        {'id': 'entrance:way_up', 'space': 'room:landing', 'kind': 'exit', 'neighbour': 'exit:d7_way_up',
         'how': pl.place['exit:way_up']['text'], 'notes': at_text(pl.place['exit:way_up']['at'])},
        {'id': 'entrance:dais', 'space': 'room:chamber', 'kind': 'exit', 'neighbour': 'exit:d7_dais',
         'condition': {'qbit': qbit}, 'how': pl.place['exit:dais']['text'], 'notes': at_text(pl.place['exit:dais']['at'])},
    ]
    pois = []
    for p in d['places']:
        if not p['id'].startswith(('poi:', 'exit:')):
            continue
        e = {'id': poi_id(p['id']), 'space': p['space'],
             'kind': {'statue': 'statue', 'pedestal': 'pedestal', 'sleeper': 'sleeper', 'chest': 'chest',
                      'device': 'device', 'exit': 'exit', 'dais': 'exit'}[p['kind']], 'behaviour': p['text']}
        st = f['stations'].get(p['id'])
        e['notes'] = at_text(p['at']) + (f", {st['along']:,} along the walk" if st else '')
        if p['id'] == 'poi:statue':
            e['condition'] = {'lua': f'XeenQuests.hook("m38.plaque_{el}")'}
        if p['id'] == 'poi:test':
            e['uses'] = {'times': 1, 'per': 'party', 'reset': 'never'}
            e['condition'] = {'lua': f'XeenQuests.hook("m38.test_{el}")'}
            e['gives'] = {'map_var': 'test_accepted'}
            e['behaviour'] = (p['text'] + f" Offered while the guardians are hidden and {test_qbit(d)} "
                              f"({D.TEST_QBITS[el]}) is clear; declining does nothing (D-58 C3).")
        if p['id'] == 'poi:sleeper':
            e['condition'] = {'lua': f'XeenQuests.hook("m38.sleeper_{el}")'}
            e['gives'] = {'qbit': qbit}
        if p['id'] == 'exit:way_up':
            e['also'] = ['entrance:way_up']
            e['behaviour'] = p['text'] + f" A3's line m38.way_up_{el} is the window's meaning."
        if p['id'] == 'exit:dais':
            e['behaviour'] = p['text'] + f" A3's line m38.dais_{el} is the window's meaning."
        if p['id'] == 'exit:dais':
            e['also'] = ['entrance:dais']
            e['condition'] = {'qbit': qbit}
        pois.append(e)
    others = [s['id'] for s in d['spaces']]
    cam = d['camera']
    hz = d['hazard']
    set_pieces = [
        {'id': 'set:test', 'kind': 'boss', 'spaces': ['room:arena'],
         'rule': (f"D-58 C3 (a): the pedestal's 'Accept the test of {El}?' (A3's m38.test_{el}) shows the "
                  f"three guardians, a hidden group until then, rising from the pit {at_text(d['test_at'])}: "
                  + ', '.join(f"{g['count']} {D.ROWS[g['row']]['short']} ({D.ROWS[g['row']]['level']})"
                              for g in d['test_group'])
                  + f". Each guardian's death event calls Xeen.planeTestCheck(\"{el}\", <the group>); when the three "
                    f"are dead it runs m38.test_{el}_passed, which sets {test_qbit(d)} ({D.TEST_QBITS[el]}, P-1) and "
                    "opens the gate. A party that leaves mid-fight finds the guardians still shown on return; the test "
                    "is not offered again while they live."),
         'enabled_by': {'map_var': 'test_accepted'},
         'population': [{'id': 'pop:guardians', 'actors': [{'actor': D.ROWS[g['row']]['actor'], 'count': g['count']}
                                                           for g in d['test_group']],
                         'placed': True, 'notes': f"hidden until the test is accepted, {at_text(d['test_at'])}"}],
         'gives': {'qbit': test_qbit(d)}},
        {'id': f"set:{hz['kind']}", 'kind': 'trap', 'spaces': sorted({pl.space_of(c) for c in hz['cells']
                                                                     if pl.space_of(c)}),
         'rule': hz['rule'] + f" PressurePlate faces textured `{d['textures']['new'][0][0]}`, each calling A3's "
                              f"planes.{HAZARD_HOOK[el]}. Cells: {'; '.join(at_text(c) for c in hz['cells'])}. None on "
                              f"the critical path (measured {f['hazard_on_critical']} within 384 of the walk; "
                              f"{f['hazard_on_links']} on a link, {f['hazard_in_arena']} in the arena)."},
    ]
    if 'low' in d:
        set_pieces.append({'id': f"set:{d['low']['kind']}", 'kind': 'trap', 'spaces': [d['low']['id']],
                           'rule': (d['low']['rule'] + f" Measured: the farthest {d['low']['kind']} is "
                                    f"{f['bank_max']:,} from a way out (90 % within {f['bank_p90']:,}).")})
    else:
        set_pieces.append({'id': 'set:fall', 'kind': 'scripted', 'spaces': ['void:sky'],
                           'rule': (f"D-58 P2 Q1 (a): a party below z {d['fall']['below']:,} (and the room's safety "
                                    "floor) is moved by Xeen.skyFallTo(\"p2\") (A3's SkyFalls key `p2`) to "
                                    "entrance:d7_fall on the Gale Landing in this map, from Xeen.SkyFallHeight (850) "
                                    "above it, with falling damage (D-6.2: a third of HP at most; Feather Fall none). "
                                    "The smallest unbridged gap between islands is "
                                    f"{f['island_gaps']['min_unbridged_gap']:,}: no jump across.")})
    states = [
        {'id': 'state:test_passed', 'condition': {'qbit': test_qbit(d)},
         'opens': [l['id'] for l in d['links'] if l.get('gate')],
         'effects': [f"P-1: the map's load event reads {test_qbit(d)} ({D.TEST_QBITS[el]}): the gate stays open, the "
                     "guardians stay hidden and the pit stays quiet, through refills and the reset after a map "
                     "rebuild (D-58 C4 (a))."]},
        {'id': 'state:sleeper_awake', 'condition': {'qbit': qbit}, 'shows': ['poi:dais'],
         'effects': [f"The return dais shows (common question C5 (a)); m38.sleeper_{el} answers its first line."]},
    ]
    landmarks = [
        {'id': 'landmark:statue', 'space': 'room:statue', 'what': pl.place['poi:statue']['text'].split(':')[0],
         'seen_from': ['room:landing'] + [s for s in others if s not in ('room:statue', 'room:landing')][:3]},
        {'id': 'landmark:arena', 'space': 'room:arena', 'what': pl.space['room:arena']['shape'],
         'seen_from': [s for s in others if s != 'room:arena']},
        {'id': 'landmark:chamber', 'space': 'room:chamber', 'what': pl.space['room:chamber']['shape'],
         'seen_from': ['room:landing', 'room:statue', 'room:arena']},
        {'id': 'landmark:way_up', 'space': 'room:landing', 'what': pl.place['exit:way_up']['text'].split('.')[0],
         'seen_from': ['room:landing', 'room:statue']},
    ]
    doc = {
        'format': 0, 'level': 'L1', 'pitch': d['pitch'], 'purpose': d['purpose'], 'mood': d['mood'],
        'datum': d['datum'], 'spaces': spaces, 'links': links, 'entrances': entrances,
        'critical_path': crit, 'return_path': ['room:chamber'],
        'goals': [
            {'id': 'goal:test', 'space': 'room:arena', 'kind': 'kill',
             'what': (f"The test of {El}: the {D.ROWS[d['test_group'][0]['row']]['short']} and two "
                      f"{D.ROWS[d['test_group'][1]['row']]['short']}s"), 'story': 'M38',
             'gives': {'qbit': test_qbit(d)}},
            {'id': 'goal:sleeper', 'space': 'room:chamber', 'kind': 'use',
             'what': f"Wake the {El} Sleeper (m38.sleeper_{el}: Chosen One and M37's four reflectors)",
             'story': 'M38', 'gives': {'qbit': qbit}},
        ],
        'points_of_interest': pois, 'landmarks': landmarks,
        'sightlines': [{'id': 'view:arrival', 'from': 'room:landing',
                        'to': ['landmark:statue', 'landmark:arena', 'landmark:chamber'], 'what': cam['what'],
                        'notes': (f"camera {at_text(cam['at'])}, z {f['camera']['z']} (eye), yaw "
                                  f"{cam['yaw_deg']:.0f} degrees, pitch {cam['pitch_deg']:.0f}; the MU-4 concept")}],
        'set_pieces': set_pieces,
        'height_bands': [{'id': 'band:floors', 'range': Flow(f['floors']), 'spaces': others,
                          'notes': 'the arrival 0, rising to the sleeper'}]
        + ([{'id': f"band:{d['low']['kind']}", 'level': d['low']['level'], 'spaces': [d['low']['id']],
             'notes': f"{d['low']['name'].lower()}; {d['rim']['text']}"}] if 'low' in d else
           [{'id': 'band:fall', 'level': d['fall']['below'], 'spaces': ['void:sky'],
             'notes': 'the fall check'}]),
        'states': states,
        'atmosphere': (f"Sky `{d['sky']['preset']}` ({'shipped' if d['sky']['shipped'] else 'new, A6 after approval'}; "
                       f"question 3); "
                       f"daylight {d['daylight']['ambient_rgb']} ambient; view distance x{d['view_distance_scale']}; "
                       f"no weather; music {d['music']}. No Fly (WORLD_DESIGN 3.4). No lighting bake (open air)."),
        'totals': {'placed_monsters': f['placed_hostiles'], 'kill_xp_per_member': f['kill_xp_per_member'],
                   'chests': f['chests'], 'points_of_interest': f['poi_census'],
                   'walkable_area_millions': float(f['walkable_area_m']), 'walk_length': f['walk_length'],
                   'first_fight': f['first_fight']['straight']},
        'notes': (f"MU-3 for the phase 6 review (A6's planes sub-agent, 2026-11-21). Room {d['room'][0]} x "
                  f"{d['room'][1]} cells ({d['room'][0] * 512:,} a side). Written by "
                  "level_generation/xeen_art/phase6/planes_brief.py from planes_design.py; drawings, measure.json "
                  f"and the board in level_generation/xeen_art/phase6/planes/. Source: the Elemental Plane of {El}, "
                  f"MM5 maze {d['source_map']} (dark/{d['source_text']}). Corner contract: "
                  "level_generation/xeen_art/phase6/corners.yml."),
    }
    return doc


# ------------------------------------------------------------------------------------------------ project.yml
def project(pl, f):
    d = pl.d
    c = corner(d)
    el = d['element']
    doc = {
        'format': 0, 'id': d['id'], 'name': d['name'], 'world': 'xeen', 'kind': 'indoor', 'profile': 'region',
        'map_code': d['code'], 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': Flow(list(d['room']))},
        'map_stats': {'id': d['map_stats_id'], 'encounter_chance': 0, 'treasure_level': 6, 'trap_dice': 8,
                      'perception_difficulty': 8, 'refill_days': 672, 'music': d['music'],
                      'environment': d['environment'], 'lock_difficulty': 15},
        'neighbours': [
            {'id': 'corner:d7', 'to': 'xeen_d7.blv', 'kind': 'scripted',
             'notes': (f"D7 The Skyroads (A6, phase 6): its {c['d7_corner']} corner ({c['d7_hook']}) drops the party "
                       f"here, to entrance:d7_fall (corners.yml).")},
            {'id': 'exit:d7_way_up', 'to': 'xeen_d7.blv', 'kind': 'door', 'arrival': c['d7_return'],
             'arrival_hint': f"On D7 by the {c['d7_corner']} corner's rest stop, facing the road.",
             'notes': "The way up at the arrival, an exit preset (D-24), always open (common question C5)."},
            {'id': 'exit:d7_dais', 'to': 'xeen_d7.blv', 'kind': 'door', 'arrival': c['d7_return'],
             'condition': {'qbit': f'm38_{el}'},
             'notes': "The return dais by the sleeper, shown once the sleeper is awake (common question C5)."},
        ],
        'qbits': {f'm38_{el}': D.SLEEPER_QBITS[el], test_qbit(d): D.TEST_QBITS[el]},
        'rules': {'no_fly': True, 'weather': 'none'},
        'notes': (f"{d['code']} {d['name']}, MU-3 plan for the phase 6 review (A6's planes sub-agent, 2026-11-21): an "
                  f"open-air BLV region (devdocs/INDOOR_OPEN_SKY.md; X9's and P5's route), {d['form']}. Spaces are "
                  "plan spaces with `at` (map units, the middle) and `extent`. Drawings and board: "
                  "level_generation/xeen_art/phase6/planes/."),
    }
    if el == 'air':
        doc['rules']['fall_through'] = {'below': d['fall']['below'], 'to': 'entrance:d7_fall',
                                        'landing': Flow(list(pl.place['entrance:d7_fall']['at']))}
    return doc


def atmosphere(pl):
    d = pl.d
    dl = d['daylight']
    return {
        'format': 0,
        'open_sky': {'mode': 'open', 'preset': d['sky']['preset'], 'view': 'outdoor',
                     'view_distance_scale': d['view_distance_scale']},
        'daylight': {'ambient_rgb': Flow(dl['ambient_rgb']), 'sun_rgb': Flow(dl['sun_rgb']),
                     'night_scale_rgb': Flow(dl['night_scale_rgb']), 'sun_gain': dl['sun_gain']},
        'notes': (f"Sky preset `{d['sky']['preset']}` by name (lanes README: a preset, never a texture alias): "
                  f"{d['sky']['why']} Night scale 255: a plane keeps its light at every hour. D-58 Q3."),
    }


# ------------------------------------------------------------------------------------------------ NOTES.md
def q_block(q, n=None):
    lines = [f"{n or q['id']}. **{q['title']}**", '   - Options:']
    lines += [f'     - {o}' for o in q['options']]
    lines += [f"   - Evidence: {q['evidence']}", f"   - Proposed default (drawn): {q['default']}",
              f"   - Depends on it: {q['depends']}"]
    return '\n'.join(lines)


def notes(pl, f):
    d = pl.d
    el, El = d['element'], d['Element']
    c = corner(d)
    first = d['key'] == 'p1'
    st = f['stations']
    L = []
    L.append(f"# {d['code']} {d['name']}: L1 plan (MU-3, MU-4), approved with changes (D-58)\n")
    pair = next(k for k, v in D.PAIRS.items() if d['key'] in v)
    L.append(f"A6's planes sub-agent, 2026-11-21. A plan only: no geometry. Decider D-58 "
             f"(`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`) approved the board "
             f"(`level_generation/xeen_art/phase6/planes/board_{pair}.png`) with changes; the sixteenth session applied "
             "them to the design data and rewrote this folder (\"D-58 applied\" below). Where this plan and D-58 "
             "differ, D-58 wins.\n")
    L.append("`level_generation/xeen_art/phase6/planes_design.py` holds the four planes' design as data (one family: "
             "the same skeleton, one element each). `planes_render.py` draws and measures it (plan SVG and PNG, the "
             "arrival blockout, `measure.json`), `planes_brief.py` writes this folder, `planes_concepts.py` paints "
             "one `codex exec` concept, `board_planes.py` boards the pair; `planes_run.py` runs them (Python under an "
             "8 GB cgroup cap) and `oymap fmt`, `fmt --check` and `validate --assets assets_dev`.\n")
    L.append(f"Validation: `fmt --check` clean, `validate` no issues (see the run log in "
             f"`level_generation/xeen_art/phase6/planes/run_{next(k for k, v in D.PAIRS.items() if d['key'] in v)}.log`).\n")
    L.append(d58_section(pl, f))
    L.append('## The source\n')
    src = d.get('source_summary') or {
        'fire': ("MM5 maze 25, the Elemental Plane of Fire (`dark/aaze0025`, 16 x 16 squares, every square lava; "
                 "decoded from `reference/mm4_5_world_of_xeen/unpacked`, nothing copied):\n\n"
                 "- the run position (9,9) in the middle; the statue and its plaque (8,7) two squares away;\n"
                 "- the test (10,13): 'Accept the test of Fire?'; yes costs 2,500 fire damage and sets a flag;\n"
                 "- the chest (2,4): burns for 250 unless the flag is set; gold and three items;\n"
                 "- the Fire Sleeper (3,12): three answers (not Chosen; 'Awaiting Grunfeld field activation.'; "
                 "awake, the award);\n"
                 "- nine vent squares: one time in three 50 fire damage;\n"
                 "- eight Fire Blowers (the greater fire elemental);\n"
                 "- the exit (13,2): a fall back to Skyroad A1 (map 89) at (3,13)."),
        'air': ("MM5 maze 26, the Elemental Plane of Air (`dark/aaze0026`, 16 x 16, every square cloud; decoded, "
                "nothing copied):\n\n"
                "- the run position (9,9); the statue and its plaque (7,7);\n"
                "- the test (10,2): 'Accept the test of Air?'; yes costs 2,500 electrical damage and sets a flag;\n"
                "- the chest (5,13): 250 electrical unless the flag is set; gold and three items;\n"
                "- the Air Sleeper (12,12), the same three answers;\n"
                "- nine storm squares: one time in three 50 electrical damage;\n"
                "- eight Whirlwinds (the greater air elemental);\n"
                "- the exit (2,2): a fall back to Skyroad F1 (map x109) at (12,13)."),
    }[el]
    L.append(src + '\n')
    L.append('## The form\n')
    L.append(f"**{d['form'].capitalize()}.** {d['form_why']}\n")
    L.append(f"Room {d['room'][0]} x {d['room'][1]} cells ({d['room'][0] * 512:,} a side), north up, x east, y north, "
             f"the middle at (0, 0); floors over the arrival (0).\n")
    L.append('## The walk\n')
    L.append('| Along | Where | What |\n| ---: | --- | --- |')
    L.append(f"| 0 | {pl.space['room:landing']['name']} (0) | Arrival `entrance:d7_fall` "
             f"{at_text(pl.place['entrance:d7_fall']['at'])}, facing {pl.place['entrance:d7_fall']['face']}; the way "
             f"up {at_text(pl.place['exit:way_up']['at'])}. Quiet. |")
    ff_off = pl.along(next(g['at'] for g in d['groups'] if g['id'] == f['first_fight']['group']))[1]
    L.append(f"| {f['first_fight']['along_walk']:,} | | The first fight (`{f['first_fight']['group']}`), "
             f"{f['first_fight']['straight']:,} from the arrival" + (f", {round(ff_off):,} off the walk" if ff_off > 600
                                                                     else '') + ". |")
    L.append(f"| {st['poi:statue']['along']:,} | {pl.space['room:statue']['name']} "
             f"({pl.space['room:statue']['floor']}) | The statue and its plaque (m38.plaque_{el}). |")
    L.append(f"| {st['poi:test']['along']:,} | {pl.space['room:arena']['name']} ({pl.space['room:arena']['floor']}) |"
             f" The pedestal: 'Accept the test of {El}?' (m38.test_{el}); the guardians rise. |")
    L.append(f"| {st['gate:sleeper']['along']:,} | | The sleeper's gate (open on the passed test). |")
    L.append(f"| {st['poi:sleeper']['along']:,} | {pl.space['room:chamber']['name']} "
             f"({pl.space['room:chamber']['floor']}) | The {El} Sleeper (m38.sleeper_{el}); the test's chest. |")
    L.append(f"| {st['exit:dais']['along']:,} | | The return dais (after the sleeper) to D7's {c['d7_return']}. |\n")
    L.append(f"Legs: arrival to the test {f['walk_legs']['arrival_to_test']:,}; the test to the sleeper "
             f"{f['walk_legs']['test_to_sleeper']:,}; the sleeper to the way out {f['walk_legs']['sleeper_to_way_out']:,}"
             f" ({f['walk_length']:,} in all, about {f['walk_seconds']['walking']} s walking).\n")
    L.append('Spaces:\n')
    for s in d['spaces']:
        L.append(f"- **{s['name']}** (`{s['id']}`) {at_text(s['at'])}, {s['extent'][0]:,} x {s['extent'][1]:,}, "
                 f"floor {s['floor']}: {s['shape']}. {s['purpose']}")
    L.append('')
    L.append('Places:\n')
    for p in d['places']:
        L.append(f"- `{p['id']}` {at_text(p['at'])}: {p['text']}")
    L.append('')
    L.append('## Figures (`measure.json`)\n')
    L.append('| Figure | Target | Plan |\n| --- | --- | --- |')
    L.append(f"| Size | MAPS §3: S-M dungeon scale (S 7-20 M units, M 30-90) | room {d['room'][0]} x {d['room'][1]} "
             f"cells; floors span {f['floor_bbox_cells'][0]} x {f['floor_bbox_cells'][1]} cells; "
             f"**{f['walkable_area_m']} M units** walkable |")
    if 'low' in d:
        L.append(f"| {d['low']['name'][4:].capitalize()} | the element's ground | {f['low_area_m']} M units, "
                 f"{round(100 * f['low_share'])} % of the basin; farthest from a way out {f['bank_max']:,} (90 % within "
                 f"{f['bank_p90']:,}) |")
    else:
        L.append(f"| Sky | the element | {round(100 * f['sky_share'])} % of the room; smallest unbridged gap "
                 f"{f['island_gaps']['min_unbridged_gap']:,}; bridges {f['island_gaps']['bridge_spans'][0]:,}-"
                 f"{f['island_gaps']['bridge_spans'][1]:,} (D-6.2: spans up to 4,000) |")
    L.append(f"| Placed hostiles | MAPS §0: 30 a plane | **{f['placed_hostiles']}** ({f['field_hostiles']} in "
             f"{len(d['groups'])} groups of {'-'.join(str(x) for x in f['group_sizes'])}, and the test's 3) |")
    L.append(f"| Levels | 55-70, the guardian 75 | {f['levels'][0]}-{f['levels'][1]}, mean {f['level_mean']} |")
    L.append(f"| Kill XP per member | D-58: {D.D58_KILL_XP[d['key']] / 1000:.2f}k (MAPS 31.0k a plane) | "
             f"**{f['kill_xp_per_member'] / 1000:.2f}k** ({f['kill_xp_vs_target'] * 100:+.1f} % on MAPS); "
             "XP = L(L+10) as D5 |")
    L.append(f"| First fight | 1,500-4,000 from the arrival | **{f['first_fight']['straight']:,}** |")
    L.append(f"| Quiet arrival | no spawns on the landing | {f['landing_hostiles']} on it; nearest group to the way up "
             f"{f['nearest_group_to_way_up']:,} |")
    L.append(f"| Points of interest | C8: 10-12 | **{f['poi_census']}** (D-20 census, merged within 400); spacing "
             f"median {f['poi_spacing']['median']:,} ({f['poi_spacing']['min']:,}-{f['poi_spacing']['max']:,}) |")
    L.append(f"| Chests | C8: 2 (S 0-3) | **{f['chests']}**, treasure 6, and one find |")
    L.append(f"| Hazard cells | the source's nine | {f['hazard_cells']}, {f['hazard_on_critical']} on the critical "
             f"path, {f['hazard_on_links']} on a link, {f['hazard_in_arena']} in the arena |")
    L.append(f"| P-2 no bypass | every lip at least {D.P2_MIN_LIP} | lowest lip **{f['p2']['lip_min']}**; no higher "
             f"floor within {D.DROP_REACH:,}: {'holds' if f['p2']['holds'] else 'FAILS'} (\"D-58 applied\") |")
    L.append(f"| Walk | - | {f['walk_length']:,} (arrival -> test -> sleeper -> way out) |")
    L.append(f"| Textures | Dungeon S cap 30 (4 new) | about {d['textures']['estimate']}, "
             f"{len(d['textures']['new'])} new |\n")
    L.append('Hostiles by row:\n')
    for k, v in f['by_row'].items():
        L.append(f"- {v} x {k}")
    L.append('')
    L.append('## Hazards and never stuck\n')
    L.append(f"- **{d['hazard']['kind'].capitalize()}** ({d['hazard'].get('question', 'question 2')}): "
             f"{d['hazard']['rule']}")
    if el == 'fire':
        L.append(f"- **Lava** (D-58 Q1): walkable and burning; crust banks and ramps everywhere but the Sleeper's "
                 f"Hall and its bridge (P-2); 90 % of the lava within {f['lava_bank_p90']:,} of a bank, the farthest "
                 f"{f['lava_bank_max']:,} (about {round(f['lava_bank_max'] / 384)} s walking; the lava behind the "
                 "Sleeper's Hall, which the spire's rock walls off from the hall).")
        L.append('- **No falls**: the crater wall closes the room.')
    elif 'low' in d:
        L.append(f"- **{d['low']['name'][4:].capitalize()}** (question 1): {d['low']['rule']} The farthest point is "
                 f"{f['bank_max']:,} from a way out.")
    else:
        L.append(f"- **Falls** (question 1): {d['fall']['text']}")
    L.append("- **Never stuck**: the way up at the arrival is always open; Town Portal and Lloyd's Beacon work (no "
             "no_teleport); the test can be left and taken up again; the gate stays open once passed.\n")
    L.append('## Ways in and out (the corner contract)\n')
    L.append(f"- **In:** D7's {c['d7_corner']} corner ({d['corner_sky']}), `{c['d7_hook']}` ('What do you seek?' "
             f"'{El}'), drops the party to `entrance:d7_fall` here (common question C2: no falling damage).")
    L.append(f"- **Out, always:** the way up at the arrival, an exit preset, to D7's `{c['d7_return']}`.")
    L.append(f"- **Out, after the sleeper:** the return dais in the chamber (condition m38.{el}), the same arrival.")
    L.append("- corners.yml's `default_way_out` (the lead, D-58 C5) says this; Town Portal and Lloyd's Beacon work, Fly "
             "is not cast.\n")
    L.append('## Textures (shipped first; L3 confirms)\n')
    for name, fam, area in d['textures']['shipped']:
        L.append(f"- `{name}`: {fam}; {area}.")
    for name, why in d['textures']['new']:
        L.append(f"- new `{name}`: {why}.")
    L.append(f"\nAbout {d['textures']['estimate']} distinct textures: class S (cap 30, at most 4 new; D-58 C1). The "
             "new ones are made at L3 through xtex.py and registered by the lead.\n")
    L.append('## Original lines\n')
    sl = d['source_lines']
    L.append(f"- '{El} Sleeper' and the three sleeper answers ({d['source_text']}:{sl['sleeper']}): "
             f"m38.sleeper_{el}.")
    L.append(f"- 'Plaque' and the Step text ({d['source_text']}:{sl['plaque']}): m38.plaque_{el}.")
    L.append(f"- 'Accept the test of {El}?' ({d['source_text']}:{sl['test']}): m38.test_{el}.")
    L.append(f"- 'Chest' ({d['source_text']}:{sl['chest']}): the test's chest's name.\n")
    L.append('## Hooks placed\n')
    L.append(f"- A3's, by name: `m38.plaque_{el}` (the statue), `m38.test_{el}` (the pedestal; yes shows the "
             f"guardians), `m38.sleeper_{el}` (the couch, every click; sets m38.{el}, qbit {D.SLEEPER_QBITS[el]}).")
    L.append(f"- The test (P-1, C3): each guardian's death event calls `Xeen.planeTestCheck(\"{el}\", <group>)` "
             f"(xeen_common.lua), which runs `m38.test_{el}_passed` once (sets m38.{el}_test, qbit "
             f"{D.TEST_QBITS[el]}); the load event reads the qbit.")
    L.append(f"- The ways out (C5): `m38.way_up_{el}` and `m38.dais_{el}`, the lines the two `exit` presets' windows "
             "mean (nothing to call).")
    L.append(f"- The hazard and the places (`source/npcs/planes.yml`): `planes.{HAZARD_HOOK[el]}` on the nine plates, "
             "the device, the find's note and the gem device by their names there.")
    L.append(f"- In: D7's `{c['d7_hook']}`, then `Xeen.toPlane(\"{el}\")` to `Xeen.PlaneArrivals.{el}` = "
             f"`entrance:d7_fall` here." + (" Falls: `Xeen.skyFallTo(\"p2\")`." if el == 'air' else '') + "\n")
    L.append('## MU-4 concept\n')
    L.append(d.get('concept_notes', 'Not painted yet.') + '\n')
    L.append('## The questions and D-58\'s answers\n')
    if first:
        L.append('Common to all four planes (asked once, here; P2-P4 refer to them):\n')
        for q in D.COMMON_QUESTIONS:
            L.append(q_block(q) + f"\n   - **Decided (D-58):** {D.COMMON_DECISIONS[q['id']]}")
        L.append('')
    else:
        L.append("The common questions C1-C8 are in P1's NOTES (`devdocs/xeen/briefs/p1/L1/NOTES.md`); D-58 took "
                 "the drawn default on each (C6 (b)).\n")
    L.append(f'{d["code"]}\'s own:\n')
    for q in d['questions']:
        L.append(q_block(q) + f"\n   - **Decided (D-58):** {d['decisions'][q['id']]}")
    L.append('')
    L.append('## Requests (for the orchestrator to relay; D-58 state)\n')
    if first:
        for lane, text in D.COMMON_REQUESTS:
            L.append(f"- **{lane}** (all four planes): {text}")
    for lane, text in d['requests']:
        L.append(f"- **{lane}**: {text}")
    L.append('\n## Blocked\n')
    L.append(f"Nothing blocks L1 or L2: A2's map_stats row {d['map_stats_id']} and the element rows (C6) landed "
             "2026-11-21. L4's walks from assets_dev wait on S's sleeper, couch, statue, pedestal and dais (C7; spots built "
               "by name, blocked) and D7's install (its entrance:" + c['d7_return'].split(':')[1] + "). A3's hooks "
               "are written (m38.test_" + el + "_passed, way_up, dais, planes.yml).\n")
    return '\n'.join(L)


def d58_section(pl, f):
    """The "D-58 applied" table: each change, what was done, the figure."""
    d = pl.d
    el, El = d['element'], d['Element']
    c = corner(d)
    p2 = f['p2']
    rows = []
    rows.append(('P-1 the test in a qbit',
                 f"the gate's link, goal:test, set:test and state:test_passed read or give {test_qbit(d)}; the load "
                 "event reads it: gate open, guardians hidden, pit quiet (A3's m38.test_" + el + "_passed sets it)",
                 f"qbit {D.TEST_QBITS[el]}"))
    lips = '; '.join(f"{('the ' + k[5:]) if k.startswith(('zone:', 'room:', 'link:')) else k.replace('_', ' ')} "
                     f"{('lip ' + format(v['lip_min'], ',')) if v['lip_min'] is not None else 'open sky'}"
                     for k, v in p2['approaches'].items())
    hf = p2['higher_floors'][0] if p2['higher_floors'] else None
    rows.append(('P-2 no bypass',
                 f"measured round {pl.space['room:chamber']['name']} and the gate's link beyond the gate: {lips}; the "
                 f"gate between {d['gate_flank']['what']} ({d['gate_flank']['height']} high, "
                 f"{d['gate_flank']['length']} along the rim)"
                 + (f"; the nearest higher floor ({hf['space'][5:]}, {hf['floor']}) is {hf['gap']:,} away" if hf
                    else '') + ", so no drop reaches it",
                 f"lowest lip {p2['lip_min']} (>= {D.P2_MIN_LIP}): {'holds' if p2['holds'] else 'FAILS'}"))
    rows.append(('P-3 / C6 rows',
                 'names by the C6 pattern; ids where they exist (' + ', '.join(
                     f"{v} {k}" for k, v in f['by_row'].items()) + ')',
                 f"{f['placed_hostiles']} hostiles, {f['kill_xp_per_member'] / 1000:.2f}k per member "
                 f"(D-58 {D.D58_KILL_XP[d['key']] / 1000:.2f}k)"))
    rows.append(('C2 arrival', f"lands standing at entrance:d7_fall (Xeen.PlaneArrivals.{el}, A3)",
                 f"{tuple(pl.place['entrance:d7_fall']['at'])}, floor 0"))
    rows.append(('C3 the test', "the guardians a hidden group at the pit, shown by m38.test_" + el + "; their death "
                 "events call Xeen.planeTestCheck", ', '.join(f"{g['count']} x {D.ROWS[g['row']]['short']}"
                                                              for g in d['test_group'])))
    rows.append(('C4 the gate', f"the {d['gate_kind']} to the chamber opens on the qbit", 'one gate'))
    rows.append(('C5 two ways out', f"the way up and the dais, both `exit` presets to D7's {c['d7_return']} "
                 f"(lines m38.way_up_{el}, m38.dais_{el})", 'always open / after the sleeper'))
    rows.append(('C7 S\'s pieces', 'the sleeper, couch, statue, pedestal and dais are S\'s; L4 builds their spots '
                 'by name and marks them blocked', 'no stand-ins'))
    rows.append(('C8 POIs and chests', 'the test\'s chest and one trapped cache at treasure 6, one find, one buff '
                 'device (the gem device stays as drawn: its one-time gem is planes.yml\'s)',
                 f"{f['poi_census']} POIs, {f['chests']} chests"))
    own = {
        'fire':  lambda: [('Q1 lava', 'walkable `lavtyl` that burns; crust banks within 64 of every lava edge and ramps up '
                  'every shelf, none to the hall or its bridge', f"90 % of the lava within {f.get('bank_p90', 0):,} "
                  "of a bank"),
                 ('Q2 vents', 'nine PressurePlate faces `xpfvent` calling planes.vent',
                  f"{f['hazard_cells']}, {f['hazard_on_critical']} on the critical path"),
                 ('Q3 sky', 'the shipped `plane_fire`', 'atmosphere.yml')],
        'air':  lambda: [('Q1 falls', 'below -1,500 Xeen.skyFallTo("p2") (A3\'s SkyFalls key `p2`; the brief\'s proposed '
                 '`p2_self` is not needed) to entrance:d7_fall here from 850 above, falling damage', 'D-54 tests at L4'),
                ('Q2 storm cells', 'nine plates calling planes.storm; two cells moved out of the Eye',
                 f"{f['hazard_on_links']} on bridges, {f['hazard_in_arena']} in the Eye"),
                ('Q3 sky', 'the shipped `plane_air`', 'atmosphere.yml'),
                ('Q4 monsters', 'elementals only', f"{f['kill_xp_per_member'] / 1000:.2f}k")],
        'earth':  lambda: [('Q1 bowl', 'open to `xeen_plane_earth`; drops into the scree are real falls; scree slopes back up '
                   'to every terrace, none to the Anvil or the Hollow', f"scree {d['low']['level']}, Hollow "
                   f"{pl.space['room:chamber']['floor']}"),
                  ('Q2 rockfall', 'nine plates calling planes.rockfall (with evt.CameraShake)',
                   f"{f['hazard_on_critical']} on the critical path"),
                  ('Q3 monsters', 'elementals only', f"{f['kill_xp_per_member'] / 1000:.2f}k")],
        'water':  lambda: [('Q1 water', 'MM9 water volumes; edge volumes with a constant inward `current` 256 (no radial '
                   'current); Water Walk does nothing on a volume (recorded, accepted)', 'nothing critical swum'),
                  ('Q2 diving', 'none anywhere; the wreck\'s hold half flooded and waded', '0 dives'),
                  ('Q3 sky', '`xeen_plane_water` (the lead\'s preset in Xeen\'s sky.yml)', 'atmosphere.yml'),
                  ('Q4 octopods', 'two swimmer groups, homes moved where needed', '; '.join(
                      f"{k[4:]}: " + ', '.join(f"{v:,} from the {s[5:]}" for s, v in h.items())
                      for k, h in f.get('swimmer_homes', {}).items()))],
    }[el]()
    rows += own
    rows.append(('Concept corrections (L3)', '; '.join(d['corrections']), 'L3'))
    rows.append(('ROWS', f"map_stats {d['map_stats_id']}: encounter 0, treasure 6, lock 15, trap 8, perception 8, "
                 f"refill 672, music {d['music']}, {d['environment'].upper()}"
                 + (" (D-58 said QUARRY; the engine has none, so a door would sound like wood: MOUNTAIN, A2's note)"
                    if el == 'earth' else ''), 'project.yml'))
    rows.append(('Textures', ', '.join(f"`{n}`" for n, _ in d['textures']['new']) + ' new (Dungeon S, cap 30)',
                 f"about {d['textures']['estimate']}"))
    L = ['## D-58 applied\n', '| Change | What was done | Figure |', '| --- | --- | --- |']
    L += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    return '\n'.join(L) + '\n'


def dump(doc, path):
    path.write_text(yaml.dump(doc, sort_keys=False, allow_unicode=True, width=118))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('keys', nargs='+')
    args = parser.parse_args()
    for key in args.keys:
        pl = G.Plane(key)
        f = json.loads((MEASURES / key / 'measure.json').read_text())
        brief = ROOT / 'devdocs/xeen/briefs' / key / 'L1'
        brief.mkdir(parents=True, exist_ok=True)
        dump(plan(pl, f), brief / 'plan.yml')
        dump(project(pl, f), brief / 'project.yml')
        dump(atmosphere(pl), brief / 'atmosphere.yml')
        (brief / 'NOTES.md').write_text(notes(pl, f))
        print(key, '->', brief)


if __name__ == '__main__':
    main()
