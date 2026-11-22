#!/usr/bin/env python3
"""Menu-input tours: spawn the D-66 seats and statue at their DD-08 / DD-17 spots (binding height -> spawn scale,
yaw = facing - 90 deg as the binding's yaw_offset) and capture. Writes work/ingame/dd08.yml, dd17.yml."""
import math
from pathlib import Path
import yaml
P = Path(__file__).resolve().parents[1]
H = {'throne': (250, 3.279), 'throne_steel': (250, 3.279), 'throne_gold': (250, 3.279), 'statue_teal': (300, 2.574)}
TOURS = {
    'dd08': {'pieces': [('throne', 1088, 0, 1344, 0), ('throne_gold', 1536, 384, 1392, 270), ('throne', 1984, 768, 1344, 180)],
             'shots': [('emotion', 1700, -60, 1344, 180, 4), ('euphoria', 1536, -150, 1344, 90, 6),
                       ('hall', 2250, -80, 1344, 145, 2), ('emotion_q', 1500, 350, 1392, 225, 2)]},
    'dd17': {'pieces': [('throne_steel', -3840, -4000, 1312, 0), ('statue_teal', -1150, -3536, 0, 270)],
             'shots': [('apse', -3420, -4000, 1280, 180, 4), ('apse_q', -3480, -3700, 1280, 220, 4),
                       ('statue', -1300, -4150, 0, 76, 8), ('statue_q', -800, -4000, 0, 128, 8)]},
}
for name, t in TOURS.items():
    steps = [{'expect': 'gameplay'}, {'wait': 1.0}]
    if name == 'dd17':   # the castle refuses a party without the Soul Box (m33.arrival): back in from D6 with it
        steps += [{'wait': 2.0}, {'console': 'item give 12364'}, {'console': 'lua evt.MoveToMap(0, -4736, 0, 512, 0, 0, 0, 0, [[xeen_dd17.blv]])'},
                  {'wait': 4.0}, {'key': 'Escape'}, {'wait': 1.0}]
    steps += [{'console': 'render hud off'}, {'console': 'actor kill 100000'}]
    for m, x, y, z, f in t['pieces']:
        h, mh = H[m]
        steps.append({'console': 'model spawn worlds/xeen/models/xeen_deco_%s.glb %d %d %d %.2f %.4f' % (
            m, x, y, z, h / mh, math.radians(f) - math.pi / 2)})
    steps.append({'wait': 1.5})
    for tag, x, y, z, yaw, pitch in t['shots']:
        steps += [{'console': 'tp %d %d %d %.4f %d' % (x, y, z, math.radians(yaw), pitch)}, {'wait': 1.5},
                  {'console': 'loc'}, {'capture': tag}]
    doc = {'output_dir': str(P / 'review' / 'ingame' / name), 'exit': True, 'steps': steps}
    (P / 'work' / 'ingame' / f'{name}.yml').write_text(yaml.safe_dump(doc, sort_keys=False, width=200))
