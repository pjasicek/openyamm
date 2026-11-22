#!/usr/bin/env python3
"""Write a menu-input tour (tools/RUN_GAME.md) that spawns one sleeper at its plane's spot with the debug console
(`model spawn`, scale 100, yaw = facing - 90 deg: the binding's yaw_offset) and captures it from the party's eye:
front, three-quarter, head end, face close-up and far. Usage: make_tour.py <element> <out.yml>"""
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
# L1 spots (planes_design.py poi:sleeper), the facing (direction the couch's front looks) and the floor under it
SPOTS = {'fire': ('p1', -4352, 4864, 315, 384), 'air': ('p2', 4864, 3840, 225, 768),
         'earth': ('p3', -2048, -5504, 90, -768), 'water': ('p4', -4480, -4608, 45, 232)}
element, out = sys.argv[1], Path(sys.argv[2])
plane, x, y, facing, z = SPOTS[element]
f = math.radians(facing)
front = (math.cos(f), math.sin(f))
head = (math.cos(f - math.pi / 2), math.sin(f - math.pi / 2))     # the head lies at facing - 90 deg


def at(d_front, d_head):
    return x + front[0] * d_front + head[0] * d_head, y + front[1] * d_front + head[1] * d_head


def look(px, py, tx, ty):
    return math.atan2(ty - py, tx - px)


shots = []
for name, df, dh, pitch, tgt_h in (('front', 460, 0, -14, 0), ('q', 380, -330, -14, 0), ('head', 0, 520, -12, 0),
                                   ('face', 150, 330, -10, 176), ('far', 1150, 0, -6, 0)):
    px, py = at(df, dh)
    tx, ty = at(0, tgt_h)
    shots.append((name, px, py, look(px, py, tx, ty), pitch))
lines = [f'output_dir: {PROJECT / "review" / "ingame"}', 'exit: true', 'steps:', '- expect: gameplay', '- wait: 1.0',
         '- console: render hud off',
         f'- console: model spawn worlds/xeen/models/xeen_deco_sleeper_{element}.glb {x} {y} {z} 100 '
         f'{math.radians(facing - 90):.4f}', '- wait: 1.5']
for name, px, py, yaw, pitch in shots:
    lines += [f'- console: tp {px:.0f} {py:.0f} {z + 40} {yaw:.4f} {pitch}', '- wait: 1.2', '- console: loc',
              f'- capture: {element}_{name}']
lines += ['- console: model list']
out.write_text('\n'.join(lines) + '\n')
print(out, plane)
