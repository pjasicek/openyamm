#!/usr/bin/env python3
"""In-game check on DD-12 (xeen_dd12.blv): a menu-input tour that spawns the skinned copy at the aviary's eight cages
as the binding would place it (A8's rule: the cage centre on the wall line, z = the panel bottom, facing out of the
wall; scale = binding height 50 / static height 0.5 m, yaw = facing - 90 degrees as yaw_offset), loops `perch` on
each (started out of step), and captures each wall, a close pair one second apart (the bird moves) and an oblique view
(the tray meets the wall). With a scratch root whose indoor_decorations.yml binds DD-12's store_d small barrels to the
cage bird, the last shots show it placed as a real decoration (idle loop, out of step). Writes work/ingame/dd12.yml."""
import math
from pathlib import Path

import yaml

P = Path(__file__).resolve().parents[1]
FLOOR = -2560
Z = FLOOR + 64                                       # the panels' bottom
NORTH, WEST, SOUTH = 3008, -3424, 1600               # the aviary's walls (gen.py B['aviary'])
CAGES = [(x, NORTH, 270) for x in (-3168, -2784, -2400, -2016)] + [(WEST, y, 0) for y in (2624, 2240)] \
    + [(x, SOUTH, 90) for x in (-3168, -2784)]
SCALE = 50 / 0.5
MODEL = 'worlds/xeen/models/xeen_deco_cagebird_anim.glb'


def shot(tag, x, y, z, yaw_deg, pitch):
    return [{'console': 'tp %d %d %d %.4f %d' % (x, y, z, math.radians(yaw_deg), pitch)}, {'wait': 1.2},
            {'capture': tag}]


steps = [{'expect': 'gameplay'}, {'wait': 1.0}, {'console': 'render hud off'}]
for i, (x, y, facing) in enumerate(CAGES):
    steps.append({'console': 'model spawn %s %d %d %d %.1f %.4f' % (MODEL, x, y, Z, SCALE,
                                                                    math.radians(facing) - math.pi / 2)})
for i in range(len(CAGES)):
    steps += [{'console': 'model play %d perch loop' % i}, {'wait': 0.55}]
steps += shot('north_wall', -2600, 2350, FLOOR, 90, 0)
steps += shot('cage2_a', -2784, 2770, FLOOR, 90, -12)
steps += [{'wait': 1.0}, {'capture': 'cage2_b'}]
steps += shot('cage2_oblique', -2560, 2930, FLOOR, 160, -18)
steps += shot('west_wall', -2950, 2432, FLOOR, 180, -5)
steps += shot('south_wall', -2976, 1950, FLOOR, 270, -5)
steps += shot('cage7_close', -3168, 1830, FLOOR, 270, -12)
# the store_d barrels, rebound to the cage bird in the scratch root: placed as decorations (facing 0, on the floor)
steps += shot('placed_a', 1940, 150, 0, 90, -15)
steps += [{'wait': 1.0}, {'capture': 'placed_b'}]
steps += [{'console': 'loc'}, {'wait': 0.5}]
doc = {'output_dir': str(P / 'review' / 'ingame'), 'exit': True, 'steps': steps}
out = P / 'work' / 'ingame' / 'dd12.yml'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(yaml.safe_dump(doc, sort_keys=False, width=200))
print(out)
