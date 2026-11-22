#!/usr/bin/env python3
"""DD-21's heart culvert: look at the placed jar (deco:jar, (-832, -4704) on the ledge at -800) from several sides.
ingame_tour.py <tag>  -> work/s13/<tag>.yml, captures in review/s13/<tag>/ (session 13's glass pass)."""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
tag = sys.argv[1]
JX, JY = -832, -4704
# (name, camera x, y, z (feet), pitch degrees)
SHOTS = [('front', -832, -4520, -896, -6), ('front_low', -832, -4540, -896, 2), ('q', -1000, -4560, -896, -8),
         ('side', -640, -4600, -896, -6), ('far', -832, -4350, -800, -10), ('wide', -1100, -4450, -800, -14)]
out = HERE / 'review' / 's13' / tag
lines = [f'output_dir: {out}', 'exit: true', 'steps:', '- expect: gameplay', '- wait: 1.5', '- key: Escape',
         '- wait: 0.5', '- console: render hud off', '- console: actor kill 100000', '- wait: 1.0']
for name, x, y, z, pitch in SHOTS:
    look = math.atan2(JY - y, JX - x)
    lines += [f'- console: tp {x} {y} {z} {look:.4f} {pitch}', '- wait: 1.5', '- console: loc', f'- capture: jar_{name}']
path = HERE / 'work' / 's13' / f'{tag}.yml'
path.write_text('\n'.join(lines) + '\n')
print(path)
