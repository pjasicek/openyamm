#!/usr/bin/env python3
"""Tours of S's pieces on P1-P4 (A6, twentieth session): each sleeper (front at eye height, three-quarter from above,
the head close), statue, pedestal, dais (after the console sets the sleeper's qbit and runs evt:dais_load: a tour does not run the map's timers) and way
up, from the installed L4 objects. Writes output/studio_cal/a6/s20/tour_<plane>.yml.

    python3 level_generation/projects/xeen/common/planes/tour_pieces.py
"""
import math
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'output/studio_cal/a6/s20'
EYE = 176
# the floor each piece stands on (S's placement table; daises on the disc top)
FLOORS = {
    'p1': {'sleeper': 384, 'statue': 64, 'pedestal': 256, 'dais': 392, 'way_up': -40},
    'p2': {'sleeper': 768, 'statue': 224, 'pedestal': 256, 'dais': 776, 'way_up': 4},
    'p3': {'sleeper': -768, 'statue': -16, 'pedestal': -384, 'dais': -760, 'way_up': 4},
    'p4': {'sleeper': 232, 'statue': 128, 'pedestal': 128, 'dais': 200, 'bell': 32},
}
HEIGHT = {'sleeper': 206, 'statue': 560, 'pedestal': 110, 'dais': 10, 'way_up': 1400, 'bell': 177}
QBIT = {'p1': 111760, 'p2': 111761, 'p3': 111762, 'p4': 111763}


def look(cam, target):
    dx, dy, dz = target[0] - cam[0], target[1] - cam[1], target[2] - cam[2]
    return round(math.atan2(dy, dx), 4), round(math.atan2(dz, math.hypot(dx, dy)), 4)


def shot(name, piece, floor, dist, side_deg=0.0, rise=EYE, aim=None, commands=None, settle=None):
    x, y = piece['at']
    f = math.radians(piece.get('facing', 0) + side_deg)
    cam = (x + dist * math.cos(f), y + dist * math.sin(f), floor + rise)
    tz = floor + (aim if aim is not None else HEIGHT[piece['id'].split(':')[1]] * 0.5)
    yaw, pitch = look(cam, (x, y, tz))
    s = {'name': name, 'position': [int(round(c)) for c in cam], 'yaw': yaw, 'pitch': pitch,
         'commands': ['render hud off'] + (commands or [])}
    if settle:
        s['settle_seconds'] = settle
    return s


def tour(plane):
    objs = yaml.safe_load(open(ROOT / f'devdocs/xeen/briefs/{plane}/L4/objects.yml'))
    ids = yaml.safe_load(open(ROOT / f'devdocs/xeen/briefs/{plane}/L4/ids.lock.yml'))
    P = {d['id'].split(':')[1]: d for d in objs['decorations']}
    F = FLOORS[plane]
    shots = []
    sl = P['sleeper']
    shots += [shot('sleeper_front', sl, F['sleeper'], 700),
              shot('sleeper_three_quarter_high', sl, F['sleeper'], 650, side_deg=-35, rise=520, aim=120),
              # the head lies at facing - 90: a close look from above the head end
              shot('sleeper_head', sl, F['sleeper'], 330, side_deg=-60, rise=360, aim=150),
              shot('sleeper_far', sl, F['sleeper'], 1500, side_deg=20)]
    st = P['statue']
    shots += [shot('statue_front', st, F['statue'], 900, aim=280),
              shot('statue_three_quarter', st, F['statue'], 900, side_deg=40, aim=280)]
    shots.append(shot('pedestal', P['pedestal'], F['pedestal'], 420, side_deg=25, rise=200, aim=60))
    dais = P['dais']
    shots += [shot('dais_before_wake', dais, F['dais'], 600, side_deg=90, rise=240, aim=0),
              shot('dais_awake', dais, F['dais'], 600, side_deg=90, rise=240, aim=0,
                   commands=[f'qbit set {QBIT[plane]}', f"event {ids['events']['evt:dais_load']}"], settle=3.0),
              shot('dais_and_sleeper', dais, F['dais'], 900, side_deg=150, rise=420, aim=0)]
    if 'way_up' in P:
        w = P['way_up']
        shots += [shot('way_up', w, F['way_up'], 900 if plane == 'p1' else 1100, side_deg=0 if plane == 'p1' else 0,
                       aim=500),
                  shot('way_up_near', w, F['way_up'], 450, side_deg=30, aim=300)]
    if 'bell' in P:
        b = P['bell']
        shots += [shot('bell', b, F['bell'], 600, aim=80), shot('bell_side', b, F['bell'], 600, side_deg=60, aim=80)]
    if plane == 'p4':
        # S's question: the view with the eye under the sea's surface (no diving in play, D-58 Q2)
        shots += [{'name': 'underwater', 'position': [2304, -1600, -400], 'yaw': 1.571, 'pitch': 0.05,
                   'commands': ['render hud off']},
                  {'name': 'sea_surface', 'position': [2304, -1600, 40], 'yaw': 1.571, 'pitch': -0.05,
                   'commands': ['render hud off']}]
    doc = {'output_dir': str(OUT / f'pics/{plane}'), 'settle_seconds': 2.0, 'exit': True, 'shots': shots}
    with open(OUT / f'tour_{plane}.yml', 'w') as f:
        yaml.safe_dump(doc, f, sort_keys=False, width=120)
    return len(shots)


if __name__ == '__main__':
    for p in ('p1', 'p2', 'p3', 'p4'):
        print(p, tour(p), 'shots')
