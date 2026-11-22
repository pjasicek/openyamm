#!/usr/bin/env python3
"""Write the in-game tours (menu_input_tour steps): spawn each device with its binding's yaw (facing - 90 degrees)
at the map lanes' spot, then look at it from several sides.  ingame_tour.py <tag>  -> work/ingame/<tag>_p1.yml, _p2.yml
ingame_tour.py <tag> --placed: P2 only, no spawn (the map places the basket since its session 25), more shots, captures
in review/s13/<tag> (session 13's envelope pass)."""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
tag = sys.argv[1] if len(sys.argv) > 1 else 'a'
placed = '--placed' in sys.argv
# (map, model, x, y, z, facing degrees, shots [(name, bearing from the piece to the camera, degrees from its facing, distance, pitch)])
PIECES = {
    'p1': [('emberfont', -1152, -448, 96, 0, [('front', 0, 340, -12), ('q', -60, 260, -22), ('top', 110, 170, -45),
                                              ('far', 30, 900, -6)]),
           ('firecamp', -3968, -4736, 0, 90, [('front', 0, 330, -22), ('q', -70, 260, -30), ('side', 110, 300, -22),
                                              ('top', 210, 160, -55)])],
    'p2': [('balloonbasket', -3712, 4224, 320, 0, [('front', 0, 380, -10), ('q', -60, 330, -15),
                                                   ('side', 130, 360, -12), ('top', 210, 220, -40)])],
}
if placed:
    PIECES = {'p2': [('balloonbasket', -3712, 4224, 320, 0, [('front', 0, 380, -10), ('q', -60, 330, -15),
                                                             ('side', 130, 360, -12), ('back', 180, 420, -14),
                                                             ('backq', 220, 380, -16), ('top', 210, 220, -40),
                                                             ('far', 150, 900, -8)])]}
for plane, pieces in PIECES.items():
    out = HERE / 'review' / ('s13' if placed else 'ingame') / f'{tag}_{plane}'
    lines = [f'output_dir: {out}', 'exit: true', 'steps:', '- expect: gameplay', '- wait: 1.0',
             '- console: render hud off', '- console: actor kill 100000']
    for name, x, y, z, facing, _ in ([] if placed else pieces):
        yaw = math.radians(facing) - math.pi / 2
        lines.append(f'- console: model spawn worlds/xeen/models/xeen_deco_{name}.glb {x} {y} {z} 100 {yaw:.4f}')
    lines.append('- wait: 1.5')
    for name, x, y, z, facing, shots in pieces:
        for shot, bearing, dist, pitch in shots:
            b = math.radians(facing + bearing)   # bearing relative to the facing (0 = in front)
            cx, cy = x + dist * math.cos(b), y + dist * math.sin(b)
            look = math.atan2(y - cy, x - cx)
            lines += [f'- console: tp {cx:.0f} {cy:.0f} {z} {look:.4f} {pitch}', '- wait: 1.2', '- console: loc',
                      f'- capture: {name}_{shot}']
    (HERE / 'work' / 'ingame' / f'{tag}_{plane}.yml').write_text('\n'.join(lines) + '\n')
    print(HERE / 'work' / 'ingame' / f'{tag}_{plane}.yml')
