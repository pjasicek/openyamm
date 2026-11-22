#!/usr/bin/env python3
"""Scratch check only: an overlay copy of X6's scene (work/ingame/mount/worlds/xeen/maps/xeen_x6.scene.yml) with the
two sphinx decorations appended to the entities at their origins (A5's masses stay). Never written to assets_dev.
Usage: ingame_scene.py"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
src = REPO / 'assets_dev/worlds/xeen/maps/xeen_x6.scene.yml'
dst = Path(__file__).resolve().parents[1] / 'work/ingame/mount/worlds/xeen/maps/xeen_x6.scene.yml'
PLACE = [('xeen_sphinx_north', 4009, (9216, 10240, 1408), 180), ('xeen_sphinx_south', 4010, (-12544, -10240, 1536), 270),
         # clean copies on open ground (no A5 masses around them), for reading the models alone
         ('xeen_sphinx_north_copy', 4009, (4096, -9216, 1400), 180),
         ('xeen_sphinx_south_copy', 4010, (1024, -14336, 1402), 270)]
lines = src.read_text().splitlines(keepends=True)
at = next(i for i, l in enumerate(lines) if l.startswith('spawns:'))
last = max(int(l.split(':')[1]) for l in lines[:at] if l.startswith('  - entity_index:'))
block = []
for k, (name, deco, (x, y, z), facing) in enumerate(PLACE, 1):
    block.append(f"""  - entity_index: {last + k}
    name: {name}
    decoration_list_id: {deco}
    ai_attributes: 0
    position:
      x: {x}
      y: {y}
      z: {z}
    facing: {facing}
    event_id_primary: 0
    event_id_secondary: 0
    variable_primary: 0
    variable_secondary: 0
    special_trigger: 0
    initial_decoration_flag: 0
""")
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(''.join(lines[:at] + block + lines[at:]))
print('WROTE', dst)
