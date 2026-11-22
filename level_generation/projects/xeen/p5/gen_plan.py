#!/usr/bin/env python3
"""P5: writes L2, L3 and L4 plan.yml and project.yml from L1's (A5 sub-agent `agent:a5-p5`, 2026-11-21), after X9's
gen_plan.py. L1 already carries D-56; L2 records what L2-L4 settle: the stair house's door and its FD-03 switch, the
falls to X5's entrance:p5_fall as A6 placed it, A3's hooks by name, the figures and the wedding state."""
import copy
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen  # noqa: E402
import gen_objects as go  # noqa: E402

BRIEF = gen.BRIEF
# X5's entrance:p5_fall as A6 placed it (A3's Xeen.SkyFalls.p5): 256 north of D-56's (-4608, 2304)
FALL_X5 = (-4608, 2560, 1504, 1536)


def load(level, name):
    return yaml.safe_load(open(BRIEF / level / name))


def plan_l2():
    plan = load('L1', 'plan.yml')
    plan['level'] = 'L2'
    for e in plan['entrances']:
        if e['id'] == 'entrance:fall':
            e['how'] = ("Any fall off a cloud: under -1,000 (a one-second check) or onto the safety floor, A3's "
                        f"Xeen.skyFallTo('p5') to X5's entrance:p5_fall ({FALL_X5[0]}, {FALL_X5[1]}, {FALL_X5[2]}) on "
                        "Darkstone's rock, facing the tower door, with falling damage.")
        if e['id'] == 'entrance:fd03_roof':
            e['how'] = ("Out of the stair house's door at the top of FD-03's roof stair, after M41's seal. The same "
                        "door is the way down: the `exit` word (the game's leave window), meaning 'Descend into "
                        "Darkstone Tower?' (aazex129:14), to FD-03's entrance:p5_stair"
                        + ('.' if go.FD03 else '; sealed until FD-03 is installed (L4 NOTES, switches).'))
    plan['notes'] = (plan['notes'] + ' L2-L4 (A5 sub-agent agent:a5-p5, 2026-11-21): built by output/studio_cal/p5/'
                     'tools/gen*.py; falls to A6\'s entrance:p5_fall (-4608, 2560); A3\'s m42.* hooks by name; the '
                     'figures 11919-11921; the gift on a sunk stand raised with state:wedding.')
    return plan


def project(level):
    p = load('L1', 'project.yml')
    for n in p['neighbours']:
        if n['id'] == 'door:fd03':
            if not go.FD03:
                n.pop('arrival', None)
                n.pop('arrival_hint', None)
            else:
                n['screen'] = {'text': 5064}   # F16 (A5 s30): the MM6-MM8 entrance window with A3's trans row
            n['notes'] = ("FD-03 Darkstone Tower (A7): the stair house's door, the `exit` word through the game's "
                          "leave window into FD-03's entrance:p5_stair" +
                          ('' if go.FD03 else '; sealed until xeen_fd03.blv is installed and names it') +
                          ". FD-03's roof stair comes up at entrance:fd03_roof (4608, -3968, 0), facing 512.")
        if n['id'] == 'fall:x5':
            n['arrival'] = list(FALL_X5[:3])
            n['direction'] = FALL_X5[3]
            n['notes'] = ("Every fall lands on X5's entrance:p5_fall (-4608, 2560), Darkstone's rock top (A6), facing "
                          "the tower door (south), with falling damage (A3's Xeen.skyFallTo('p5')).")
    p['new'] = False     # the finale: the Pharaoh's note by the door is the arrival's word
    p['qbits'] = {'m41_seal_broken': 111820, 'm42_done': go.M42_DONE}
    p['rules']['fall_through'] = {'below': -1000, 'to': 'fall:x5', 'landing': list(FALL_X5[:2]),
                                  'how': 'wiring evt:fall_check (a one-second timer) and evt:fall_floor (the safety '
                                         'floor at -6000)'}
    p['notes'] = (f'Xeen design brief, level {level}: P5 Clouds of the Ancients, an open-air BLV (devdocs/'
                  'INDOOR_OPEN_SKY.md) built with the studio (profile region) as X9: one room open to the sky with '
                  'the ring of cloud road, its pads, boards, Rest Stop huts, the observatory, the stair house and the '
                  "Pharaoh's shrine hanging in it. Act VI's finale (M42); map_stats 9119 (A2's row; the block here is "
                  'the studio\'s copy), music 15, treasure 6, sky xeencloud. Figures 11919-11921 (peaceful, placed, '
                  "uncounted); hooks: A3's m42.*; the ending cinematic `unification` (wiring cinematics).")
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
