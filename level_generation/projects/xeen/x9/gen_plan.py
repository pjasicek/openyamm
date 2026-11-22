#!/usr/bin/env python3
"""X9: writes L2, L3 and L4 plan.yml and project.yml from L1's (A5 sub-agent, 2026-11-21), with D-50 applied (L1 was
regenerated from design.py with D-50; L2 records what L2-L4 settle: the gate's word, the castle footprint, the falls,
the hooks by name, Slick)."""
import copy
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design as D  # noqa: E402
import gen  # noqa: E402
import gen_objects as go  # noqa: E402

BRIEF = gen.BRIEF


def load(level, name):
    return yaml.safe_load(open(BRIEF / level / name))


def plan_l2():
    plan = load('L1', 'plan.yml')
    plan['level'] = 'L2'
    for l in plan['links']:
        if l['id'] == 'link:gate':
            l['notes'] = ("Castle Xeen's gate: two leaves 256 x 512 (gnecdr1l west, gnecdr1r east) in the gate wall at "
                          f"y {gen.GATE[1]}, 640 behind the south towers' faces. A3's m34.gate, then the exit preset's "
                          "leave (the game's own window) into XD-19's entrance:x9_gate; sealed until XD-19 is installed "
                          "(L4 NOTES, 'The gate').")
    for e in plan['entrances']:
        if e['id'] == 'entrance:fall':
            e['how'] = ("Any fall off a cloud: under -1,000 (a one-second check) or onto the safety floor, A3's "
                        "Xeen.skyFallTo('x9') to X2's entrance:x9_fall on Darzog's island, with falling damage.")
        if e['id'] == 'entrance:fd04_roof':
            e['neighbour'] = 'door:fd04'
            e['facing'] = 'n'
            e['how'] = ("FD-04's roof stair arrives here; the way back down is the door in the dragon-head rock's south "
                        "face (the exit preset, 'Descend into Dragon Tower?'), to FD-04's entrance:x9_clouds"
                        + ('' if go.FD04 else '; sealed until FD-04 is installed') + '.')
            e['notes'] = (f"at {tuple(int(v) for v in gen.FD04_ARRIVAL)}, z {gen.DRAGON['floor']}, facing north, on the "
                          "cloud about 900 south of the snout (D-57 Q36). (20864, 18304) is the room's centre, inside "
                          "the skull's footprint, not the arrival.")
    x0, y0, x1, y1 = gen.SHELL
    plan['totals'] = {'placed_monsters': 50, 'chests': 4, 'points_of_interest': 29}
    plan['notes'] = (f'L2 (A5 sub-agent, 2026-11-21): L1 with D-50 applied (L1 NOTES, "D-50 applied"). Castle Xeen\'s '
                     f'shell over XD-19\'s measured outside, x {x0:.0f}..{x1:.0f}, y {y0:.0f}..{y1:.0f}; the gate at '
                     f'{tuple(int(v) for v in gen.GATE)}; the aviary at {tuple(gen.SPACE["room:aviary"]["at"])}; the '
                     "east chain retuned (3,752-3,880). Falls to X2's entrance:x9_fall (-15360, 3072). 50 placed in 19 "
                     'groups plus Slick (peaceful, uncounted).')
    return plan


def project(level):
    p = load('L1', 'project.yml')
    p['map_stats']['bolster'] = 'LowerToEqual'
    for n in p['neighbours']:
        if n['id'] == 'door:xd19':
            if go.XD19:
                n['arrival'] = 'entrance:x9_gate'
                n['screen'] = {'text': 5019}   # F16 (A5 s30): the MM6-MM8 entrance window with A3's trans row
            n['notes'] = ("Castle Xeen's gate into XD-19's entrance:x9_gate (A7): the gate's script writes the exit "
                          "preset's MoveToMap" + ('' if go.XD19 else '; sealed until xeen_xd19.blv is installed') +
                          ". XD-19's exit and the scepter's leave come back to entrance:xd19_gate (0, 11264, 768), 1536.")
        if n['id'] == 'roof:fd04':
            n['id'] = 'door:fd04'
            n['kind'] = 'door'
            if go.FD04:
                n.pop('listed_only', None)
                n['arrival'] = 'entrance:x9_clouds'
                n['screen'] = {'text': 5065}   # F16 (A5 s30): the entrance window with A3's trans row
            n['notes'] = ("Q-F1 (Act VI, optional, D-57 Q36): FD-04's roof stair arrives at entrance:fd04_roof; the door "
                          "in the dragon-head rock's south face leads down to FD-04's entrance:x9_clouds"
                          + ('' if go.FD04 else '; sealed until FD-04 is installed') + '.')
        if n['id'] == 'fall:x2':
            n['arrival'] = list(D.FALL_LANDING_X2['at']) + [D.FALL_LANDING_X2['ground']]
            n['direction'] = 0
            n['notes'] = ("Every fall lands on X2's entrance:x9_fall (-15360, 3072), Darzog's island by the tower door, "
                          "ground 768, facing east, with falling damage (A3's Xeen.skyFallTo('x9')).")
    p['qbits'] = {'m4_done': 110047, 'm21_crodo_freed': 110501, 'm34_done': 111685, 'm35_done': go.M35_DONE,
                  'nest_sw': 116220, 'nest_se': 116221, 'nest_a1': 116222, 'nest_a2': 116223, 'nest_a3': 116224,
                  **({'qf1_eye_done': go.HOOKS['q-f1.eye']['sets']['done']} if go.has_hook('q-f1.eye') else {})}
    p['rules']['fall_through'] = {'below': -1000, 'to': 'fall:x2', 'landing': list(D.FALL_LANDING_X2['at']),
                                  'how': 'wiring evt:fall_check (a one-second timer) and evt:fall_floor (the safety '
                                         'floor at -6000)'}
    p['notes'] = (f'Xeen design brief, level {level}: X9 Clouds of Xeen, an open-air BLV of walkable clouds over Lake '
                  'Darzog (devdocs/INDOOR_OPEN_SKY.md), built with the studio (profile region) as X8 Cloudreach: one '
                  'room open to the sky with the clouds, bridges, the unseen way, Slick\'s carnival and Castle Xeen\'s '
                  'shell hanging in it. Act V, party 46-48; map_stats 9107 (A2\'s row; the block here is the '
                  'studio\'s copy), music 21, treasure 5, sky xeencloud. Placed: Rocs 11561, Griffins 11562, Cloud '
                  'Golems 11592 (50 in 19 groups); Slick 11914 (peaceful, uncounted). Hooks: A3\'s m34.* and x9.*.')
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
