#!/usr/bin/env python3
"""D7: writes L2, L3 and L4 plan.yml and project.yml from L1's (A6 sub-agent, sixteenth session, 2026-11-21), after
X9's and P5's gen_plan.py. L1 is regenerated from d7_design.py with D-58 applied (output/studio_cal/d7/run.sh); L2
records what L2-L4 settle: the falls through A3's Xeen.skyFallD7 and its SkyFalls table, the hoard's two items, the
bandits, the doors to dungeons sealed until their maps are live."""
import copy
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen  # noqa: E402
import gen_objects as go  # noqa: E402

D = gen.D
BRIEF = gen.BRIEF
MEASURE = gen.ROOT / 'level_generation/xeen_art/phase6/d7/measure.json'
COMMON = gen.WORLD / 'events/common/xeen_common.lua'
ZONE_MAP = {'fall:d6': 'd7_ab12', 'fall:d5': 'd7_cd12', 'fall:d4': 'd7_ef12', 'fall:d1': 'd7_ab34',
            'fall:d2': 'd7_cd34', 'fall:d3': 'd7_ef34'}


def sky_falls():
    """A3's Xeen.SkyFalls d7_* rows: key -> (x, y, ground z, yaw, map)."""
    out = {}
    for m in re.finditer(r'(d7_\w+) = \{(-?\d+), (-?\d+), (-?\d+), (-?\d+), "([\w.]+)"\}', COMMON.read_text()):
        out[m.group(1)] = tuple(int(v) for v in m.groups()[1:5]) + (m.group(6),)
    return out


FALLS = sky_falls()


def load(level, name):
    return yaml.safe_load(open(BRIEF / level / name))


def plan_l2():
    plan = load('L1', 'plan.yml')
    f = json.loads(MEASURE.read_text())
    plan['level'] = 'L2'
    st = f['road_stretches']
    plan['totals'] = {'placed_monsters': f['placed_monsters'], 'chests': f['chests'],
                      'points_of_interest': f['points_of_interest']}
    plan['notes'] = (
        "L2 (A6 sub-agent, sixteenth session, 2026-11-21): L1 with D-58 applied (L1 NOTES, 'D-58 applied'). Longest "
        f"empty stretch: ring {st['ring']['longest_empty']:,}, inner road {st['inner']['longest_empty']:,}, north "
        f"causeway {st['north_causeway']['longest_empty']:,}; POI nearest-neighbour max {f['poi_nn_max']:,} (D-1 "
        f"<= 8,192). The Megadragon's leash circle {f['megadragon_clear']:,} from every walkable place but its road "
        f"(D-2, >= 5,888). Falls through A3's Xeen.skyFallD7 (six zones, Q10). 50 placed in 19 groups, the Megadragon "
        "and eight peaceful Sky Bandits uncounted.")
    for e in plan['entrances']:
        if e['id'].startswith('entrance:fall') or e.get('kind') == 'fall':
            e['how'] = ("Any fall off the roads: under -1,000 (a one-second check) or onto the safety floor, A3's "
                        "Xeen.skyFallD7() picks the surface map by the party's x, y and lands at its entrance:d7_fall "
                        "with falling damage.")
    if not any(e['id'] == 'entrance:fd01_roof' for e in plan['entrances']):
        # D-69 Q67 (b): FD-01's way up lands at the hatch's point (DD-17's), under its own name
        k = next(i for i, e in enumerate(plan['entrances']) if e['id'] == 'entrance:dd17_roof')
        plan['entrances'].insert(k + 1, {
            'id': 'entrance:fd01_roof', 'space': 'room:roost', 'kind': 'both', 'neighbour': 'door:fd01',
            'facing': 'w', 'how': "FD-01 Alamar Depths' rubble shaft (A8, D-69 Q67): up the ladder after M33 once "
                                  "Q-D26's roof is unlocked; down by Alamar's roof hatch.",
            'notes': "at (-18688, 8448), z 1536, facing w (MoveToMap direction 1024)."})
    return plan


def project(level):
    p = load('L1', 'project.yml')
    p['map_stats']['bolster'] = 'LowerToEqual'
    p['new'] = False          # a sky road reached by the rope, the boats and the mirrors: the boards and A3's lines say it
    p['qbits']['qd26_slain'] = 113520
    p['qbits']['m33_done'] = 111662
    p['qbits']['qd26_roof_unlocked'] = 113521
    p['items'] = {'soul_box': 12363, 'wyrmfang': go.WYRMFANG, 'alamar_roof_key': go.ROOF_KEY}
    for n in p['neighbours']:
        nid = n['id']
        if nid in ZONE_MAP and ZONE_MAP[nid] in FALLS:
            x, y, z, yaw, m = FALLS[ZONE_MAP[nid]]
            n['to'] = m
            n['notes'] = (f"Falls over this zone go through A3's Xeen.skyFallD7 to SkyFalls.{ZONE_MAP[nid]}: {m} at "
                          f"({x}, {y}), ground {z}, yaw {yaw}, entrance:d7_fall, with falling damage.")
        if nid == 'rope:d1':
            x, y, z, yaw = go.D1_ROPE
            n['notes'] = (f"The Dark Grove rope, both ways after m30.done (D-23): 'Descend to the Darkness Below?' "
                          f"(aaze0091:5) down to D1's entrance:d7_rope ({x}, {y}, {z}, yaw {yaw}); up by D1's "
                          "m30.grove_rope to entrance:d1_rope.")
        if nid in ('door:dd15', 'door:dd17', 'door:dd26', 'door:fd01'):
            live = go.LIVE[nid.split(':')[1]]
            n['notes'] = n.get('notes', '') + ('' if live else ' Sealed with a line until the dungeon is installed and '
                                                               'names the arrival.')
    if not any(n['id'] == 'door:fd01' for n in p['neighbours']):
        p['neighbours'].append({'id': 'door:fd01', 'to': 'xeen_fd01.blv', 'kind': 'door', 'arrival': 'entrance:d7_roof',
                                'notes': ("D-61 Q14: after m33.done Alamar's roof hatch leads into FD-01 Alamar Depths' "
                                          "entrance:d7_roof (a shaft through the rubble), both ways; sealed (A3's "
                                          "'Castle Alamar is gone.') until FD-01 is installed and names the arrival.")})
    zones = []
    for z in p['rules']['fall_through']['zones']:
        k = ZONE_MAP[z['to']]
        if k in FALLS:
            x, y, gz, yaw, m = FALLS[k]
            z['landing'] = [x, y, gz]
            z['key'] = k
        zones.append(z)
    p['rules']['fall_through']['zones'] = zones
    p['rules']['fall_through']['how'] = ("wiring evt:fall_check (a one-second timer) and evt:fall_floor (the safety "
                                         "floor at -6000) call A3's Xeen.skyFallD7()")
    p['notes'] = (f"Xeen design brief, level {level}: D7 The Skyroads, an open-air BLV (devdocs/INDOOR_OPEN_SKY.md) of "
                  "cloud roads and islands over the whole Darkside, built with the studio (profile region) on X9's and "
                  "P5's route: one room open to the sky with the ring road, its islands, the four element corners, the "
                  "inner road through Olympus, the roost and the Sky Lake hanging in it. Act VI, party 50-75; "
                  "map_stats 9114 (A2's row), music 30, treasure 6, sky xeen_skyroads. Placed: Griffins 11562, Sky "
                  "Golems 11594, Cloud Dragons 11650, Cloud Golems 11592 (50 in 19 groups); the Megadragon 11654 and "
                  "eight Sky Bandits 11116 (peaceful), uncounted. Hooks: A3's m31.*, m38.*; D-58's new hooks as they "
                  "land (L4 NOTES).")
    return p


def write(level, name, data):
    (BRIEF / level).mkdir(parents=True, exist_ok=True)
    with open(BRIEF / level / name, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


if __name__ == '__main__':
    plan = plan_l2()
    for level in ('L2', 'L3', 'L4'):
        pl = copy.deepcopy(plan)
        pl['level'] = level if level != 'L4' else 'L3'
        write(level, 'plan.yml', pl)
        write(level, 'project.yml', project(level))
    print('written L2-L4 plan.yml and project.yml; falls', sorted(FALLS))
