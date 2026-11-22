#!/usr/bin/env python3
"""Menu-input tour for D7: spawn the four sky-barges and the celestial boat at A6's spots (work/placement.json; spawn
scale = binding height / model height in metres = 100, yaw = facing - 90 deg as the binding's yaw_offset) and capture
each from its island at eye height and from 1,500+ away. Writes work/ingame/d7.yml. Usage: python3 tour.py"""
import json
import math
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(HERE))
import placement  # noqa: E402

gen = placement.gen
PL = json.loads((PROJECT / 'work' / 'placement.json').read_text())


def yaw_to(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def far_spot(target, prefer_deg, lo=1600, hi=2600):
    """A walkable point lo..hi from target, as near the preferred bearing as possible."""
    for dev in range(0, 181, 10):
        for sgn in (1, -1):
            for d in range(lo, hi + 1, 200):
                a = math.radians(prefer_deg + sgn * dev)
                p = (target[0] + d * math.cos(a), target[1] + d * math.sin(a))
                z = gen.height_at(p)
                if z is not None:
                    return p, z, d
    raise ValueError(target)


def near_spot(b):
    """On the island: 420 in from the gangplank's end and 260 toward the stern, a three-quarter view."""
    at, f = b['at'], math.radians(b['facing'])
    inward = (-math.sin(f), math.cos(f))                     # port = the island side
    back = (-math.cos(f), -math.sin(f))
    g = b['gangplank_end_on_island']
    for d_in, d_back in ((420, 260), (500, 0), (360, -260), (600, 400)):
        p = (g[0] + inward[0] * d_in + back[0] * d_back, g[1] + inward[1] * d_in + back[1] * d_back)
        z = gen.height_at(p)
        if z is not None:
            return p, z
    raise ValueError(b['cargo'])


def main():
    steps = [{'expect': 'gameplay'}, {'wait': 2.0}, {'console': 'render hud off'}, {'console': 'actor kill 100000'}]
    pieces = [(f"skybarge_{b['element']}", b['at'], b['floor_height'], b['facing']) for b in PL['barges']]
    bt = PL['boat']
    pieces.append(('skyboat', bt['at'], bt['floor_height'], bt['facing']))
    for m, at, z, f in pieces:
        steps.append({'console': 'model spawn worlds/xeen/models/xeen_deco_%s.glb %d %d %d 100.000 %.4f' % (
            m, at[0], at[1], z, math.radians(f) - math.pi / 2)})
    steps.append({'wait': 1.5})
    shots = []
    for b in PL['barges']:
        p, z = near_spot(b)
        shots.append((f"{b['element']}_near", p, z, yaw_to(p, b['at']), -6))
        f = math.radians(b['facing'])
        inward_deg = math.degrees(math.atan2(math.cos(f), -math.sin(f)))
        q, zq, d = far_spot(b['at'], inward_deg - 35)
        shots.append((f"{b['element']}_far", q, zq, yaw_to(q, b['at']), -2))
        print(b['element'], 'far', round(d))
    # the boat: from the jetty's end by its north-east rail, looking back down over the rail; from the jetty further
    # back; and from the road 2,600 north-east across the void (the boat's broadside)
    f = math.radians(bt['jetty_facing'])
    ux, uy = math.cos(f), math.sin(f)
    nx, ny = -uy, ux
    e = bt['jetty_end']
    p = (e[0] - ux * 40 + nx * 230, e[1] - uy * 40 + ny * 230)
    shots.append(('boat_jetty_end', p, gen.height_at(p), yaw_to(p, bt['at']), -18))
    p2 = (e[0] - ux * 1500 + nx * 230, e[1] - uy * 1500 + ny * 230)
    shots.append(('boat_jetty', p2, gen.height_at(p2), yaw_to(p2, bt['at']), -10))
    side = math.degrees(math.atan2(ny, nx))
    q, zq, d = far_spot(bt['at'], side, 2400, 3200)
    shots.append(('boat_far', q, zq, yaw_to(q, bt['at']), 2))
    print('boat far', round(d))
    for tag, p, z, yaw, pitch in shots:
        steps += [{'console': 'tp %d %d %d %.4f %d' % (p[0], p[1], z, yaw % (2 * math.pi), pitch)}, {'wait': 2.0},
                  {'console': 'loc'}, {'capture': tag}]
    doc = {'output_dir': str(PROJECT / 'review' / 'ingame'), 'exit': True, 'steps': steps}
    out = PROJECT / 'work' / 'ingame' / 'd7.yml'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(doc, sort_keys=False, width=200))
    print(out)


if __name__ == '__main__':
    main()
