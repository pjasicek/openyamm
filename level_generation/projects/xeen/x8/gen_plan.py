#!/usr/bin/env python3
"""X8: writes L2, L3 and L4 plan.yml and project.yml from L1's, with D-6.2 and D-6.4 (lane A6 sub-agent, 2026-11-20).

L2 is L1 revised: the archipelagos closer (the long bridge's spans 3,500-4,000), link:garden_ramp gone, a rope bridge
from the rhyme garden to the observatory isle, the golem heights a dead end by the long ramp, the Witch landing's
harpies 2,000 or more from the stair head, the falls in three zones (D-6.4). L3 and L4 carry the same plan.
"""
import copy
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen  # noqa: E402

BRIEF = gen.BRIEF


def load(level, name):
    return yaml.safe_load(open(BRIEF / level / name))


def plan_l2():
    plan = load('L1', 'plan.yml')
    plan['level'] = 'L2'
    for space in plan['spaces']:
        key = space['id'].split(':', 1)[1]
        if key in gen.ISLANDS:
            (cx, cy), (ex, ey), floor, _ = gen.ISLANDS[key]
            space['at'] = [cx, cy]
            space['extent'] = [ex, ey]
            space['floor'] = floor
    spaces = {s['id']: s for s in plan['spaces']}
    spaces['room:witch_landing']['population'][0]['notes'] = (
        'Three Harpies (14) and a Harpy Hag (18) on the landing\'s north side, 2,000 or more from the stair head '
        '(D-6.2).')
    spaces['room:golem_heights']['shape'] = ('a high, lumpy cloud reached only by the long ramp from the observatory '
                                             'isle: a dead end the party sees from the ramp (D-6.2)')
    spaces['room:half_way']['purpose'] = (
        'Rest in the middle of the long bridge; looking down through the gap to Lake Darzog (X2) far below. A fall '
        'here, or from the inner 2,000 of either span, lands in Lake Darzog (D-6.4).')
    spaces['void:cloud_sea']['purpose'] = (
        'The sky below the islands (the open sky drawn under the horizon). A fall is caught under -1,000: east of '
        'x 3,072 it lands on X1 by the Witch Tower; between x -3,072 and 3,072 (the half-way cloud and the inner '
        '2,000 of each span) in X2\'s Lake Darzog; west of x -3,072 on X3 by the Tower of High Magic (until X3 is '
        'built: Lake Darzog too). D-6.4.')
    links = [l for l in plan['links'] if l['id'] != 'link:garden_ramp']
    for l in links:
        if l['id'] == 'link:long_bridge_east':
            l['purpose'] = 'the long rope bridge, east span (3,883 rim to rim; D-6.2: 3,500-4,000)'
        if l['id'] == 'link:long_bridge_west':
            l['purpose'] = 'the long rope bridge, west span (3,858 rim to rim; D-6.2: 3,500-4,000)'
        if l['id'] == 'link:heights_ramp':
            l['notes'] = 'the long ramp: the only way up to the golem heights (D-6.2), a visible dead end'
    links.append({'id': 'link:garden_obs_bridge', 'from': 'room:rhyme_garden', 'to': 'room:observatory_isle',
                  'kind': 'bridge', 'width': 256, 'rise': 128,
                  'notes': 'rope bridge in place of the garden ramp: keeps the High Magic loop (D-6.2)'})
    plan['links'] = links
    plan['loops'] = [{'id': 'loop:high_magic',
                      'spaces': ['room:stair_landing', 'room:observatory_isle', 'room:rhyme_garden'],
                      'notes': 'Round the High Magic Clouds by the causeway and the two garden bridges (D-6.2).'}]
    for e in plan['entrances']:
        if e['id'] == 'entrance:fall_east':
            e['how'] = 'Any fall east of x 3,072 (the Witch Clouds and the outer part of the east span): X1 by the Witch Tower.'
        if e['id'] == 'entrance:fall_west':
            e['how'] = ('Any fall west of x -3,072: X3 by the Tower of High Magic; until X3 is built, X2\'s Lake '
                        'Darzog (D-6.4).')
    plan['entrances'].append({'id': 'entrance:fall_middle', 'space': 'void:cloud_sea', 'kind': 'exit',
                              'neighbour': 'fall:x2',
                              'how': 'A fall between x -3,072 and 3,072: Lake Darzog on X2, no falling damage.'})
    for p in plan['points_of_interest']:
        if p['id'] == 'poi:harpy_nests':
            p['spaces'] = ['room:nest_spires', 'room:witch_perch']
            p['count'] = 3
            p['behaviour'] = ('"Harpy Nest. Destroy?" (xeen/aaze0025:5); burnt, A3\'s hooks x8-sky.nest_1 to nest_3 '
                              'pay 500 experience each. The queen\'s great nest holds her hoard.')
        if p['id'] == 'poi:explorer_statue':
            p['behaviour'] = 'A3\'s hook x8-sky.explorer_statue: the award Super Explorer and +2 Speed, once.'
        if p['id'] == 'poi:rhyme_statues':
            p['behaviour'] = ('The source\'s rhymes (xeen/aaze0025:1, :2 and :4), read by anyone (the Linguist gate '
                              'is a request to A3).')
    for s in plan['set_pieces']:
        if s['id'] == 'set:fall':
            s['rule'] = ('A fall off any island is caught under -1,000 (a one-second check) and moved by zone '
                         '(D-6.4) through A3\'s Xeen.skyFall: X1 lands 850 over the ground (about a third of each '
                         'member\'s hit points, none with Feather Fall), Lake Darzog at the surface without damage.')
    plan['totals'] = {'placed_monsters': 60, 'chests': 4, 'points_of_interest': 12}
    plan['notes'] = ('L2 (A6 sub-agent, 2026-11-20): L1 approved with changes (D-6.2, D-6.4). The two archipelagos '
                     'moved 1,536 closer (the long bridge\'s spans 3,883 and 3,858 rim to rim); the garden ramp gone '
                     'and a rope bridge from the rhyme garden to the observatory isle; the islands within each '
                     'archipelago drawn closer so no causeway is longer than the long ramp (3,472). Footprint about '
                     '78 by 64 cells. 60 placed: 29 on the Witch Clouds, 29 on the High Magic Clouds, 2 Cloud '
                     'Golems (50, a trap: D-1.2).')
    return plan


def project(level):
    p = load('L1', 'project.yml')
    p['map_stats'].pop('slots', None)
    p['map_stats']['slots'] = [
        {'monster': 'Xeen Harpy', 'tier': 0, 'per_marker': [1, 3], 'weight': 50},
        {'monster': 'Xeen Construct', 'tier': 0, 'per_marker': [1, 2], 'weight': 50},
    ]
    p['map_stats']['bolster'] = 'LowerToEqual'
    for n in p['neighbours']:
        if n['id'] == 'roof:witch_tower':
            n['notes'] = ("One way up: XD-04's cloud stair arrives at the head of the Witch Clouds' stair "
                          "(objects.yml start). There is no way back down but falling.")
        if n['id'] == 'roof:high_magic':
            n['notes'] = ("One way up: XD-11's Stairway to Heaven arrives at the head of the High Magic Clouds' "
                          "stair, by explicit coordinates in XD-11's exit (NOTES.md, Arrivals).")
        if n['id'] == 'fall:x1':
            n['arrival'] = [11264, -7936, 1618]
            n['direction'] = 308
            n['notes'] = ('A fall east of x 3,072 lands on X1 1,100 north-west of the Witch Tower\'s door, 850 over '
                          'the ground (768): about a third of each member\'s hit points, none with Feather Fall.')
        if n['id'] == 'fall:x3':
            n['notes'] = ('A fall west of x -3,072 lands on X3 by the Tower of High Magic. X3 is not built: until '
                          'it is, these falls land in X2\'s Lake Darzog (fall:x2).')
    p['neighbours'].append({
        'id': 'fall:x2', 'to': 'xeen_x2.odm', 'kind': 'fall', 'arrival': [-10240, 8448, 576], 'direction': 45,
        'notes': ("A fall between x -3,072 and 3,072 (the half-way cloud and the inner 2,000 of each span; D-6.4) "
                  "lands in Lake Darzog's north-east lobe on X2 (A5's point), near the shore, without damage.")})
    p['rules']['fall_through'] = {
        'below': -1000, 'east_of_x': {'x': 3072, 'to': 'fall:x1'}, 'west_of_x': {'x': -3072, 'to': 'fall:x3'},
        'between': 'fall:x2',
        'how': 'wiring evt:fall_check (a one-second timer) and evt:fall_floor (the safety floor at -6000)'}
    p['qbits'] = {'explorer': 115020, 'nest_1': 115021, 'nest_2': 115022, 'nest_3': 115023,
                  'm4_done': 110047}
    p['notes'] = (f'Xeen design brief, level {level}: X8 Cloudreach, the open-air BLV of walkable cloud islands '
                  'over Cloudside (devdocs/INDOOR_OPEN_SKY.md), built with the studio (profile region): one '
                  'room open to the sky with the islands, bridges and causeways hanging in it. Act II, party '
                  '18-20; map_stats 9106 (A2\'s row from source/map_rows.yml; the block here is the studio\'s '
                  'copy), music 25, treasure 3, sky xeencloud. Monsters placed: Harpies 11520-11522, Flying '
                  'Feet 11600, Guardians 11601, two Cloud Golems 11592 (a trap, D-1.2). Quest bits 115020-115023 '
                  '(A3\'s X8-SKY), 110047 (M4 done: the Crusaders, the offering statues).')
    return p


def write(level, name, data):
    (BRIEF / level).mkdir(parents=True, exist_ok=True)
    with open(BRIEF / level / name, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


if __name__ == '__main__':
    plan = plan_l2()
    for level in ('L2', 'L3', 'L4'):
        p = copy.deepcopy(plan)
        p['level'] = level if level != 'L4' else 'L3'
        write(level, 'plan.yml', p)
        write(level, 'project.yml', project(level))
    print('written L2-L4 plan.yml and project.yml')
