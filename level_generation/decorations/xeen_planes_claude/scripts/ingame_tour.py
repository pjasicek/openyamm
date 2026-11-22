#!/usr/bin/env python3
"""Menu-input tour per plane (scripts/placements.json): spawn every piece at its spot with the binding's yaw (facing
+ yaw_offset -90 degrees), then for each piece teleport the party in front of it and at a three-quarter angle and
capture. Usage: ingame_tour.py <plane> -> work/ingame/<plane>.yml"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
plane = sys.argv[1]
cfg = json.load(open(HERE / 'placements.json'))[plane]
out = PROJECT / 'review' / 'ingame' / plane
out.mkdir(parents=True, exist_ok=True)
steps = [{'expect': 'gameplay'}, {'wait': 1.0}, {'console': 'render hud off'}, {'console': 'loc'}]
for p in cfg['pieces']:
    yaw = math.radians(p['facing']) - math.pi / 2
    steps.append({'console': 'model spawn worlds/xeen/models/xeen_deco_%s.glb %d %d %d 100 %.4f' % (
        p['model'], p['at'][0], p['at'][1], p['z'], yaw)})
steps.append({'wait': 1.5})
for p in cfg['pieces']:
    for tag, turn in (('front', 0), ('q', 40)):
        a = math.radians(p['facing'] + turn)
        x = p['at'][0] + math.cos(a) * p['view']
        y = p['at'][1] + math.sin(a) * p['view']
        look = math.atan2(p['at'][1] - y, p['at'][0] - x)
        steps.append({'console': 'tp %.0f %.0f %d %.4f %d' % (x, y, p['eye_z'], look, p['pitch'])})
        steps.append({'wait': 1.2})
        steps.append({'console': 'loc'})
        steps.append({'capture': '%s_%s' % (p['model'], tag)})
doc = {'output_dir': str(out), 'exit': True, 'steps': steps}
import yaml  # noqa: E402
(PROJECT / 'work' / 'ingame').mkdir(parents=True, exist_ok=True)
path = PROJECT / 'work' / 'ingame' / f'{plane}.yml'
path.write_text(yaml.safe_dump(doc, sort_keys=False, width=200))
print(path)
