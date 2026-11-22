#!/usr/bin/env python3
"""Scratch check only (never written to assets_dev): an overlay mount for X6 with the three way-up columns placed on
open ground (X6 is outdoors: a copy of decorations.yml with this project's indoor bindings appended) and the GLBs.
The debug `model spawn` draws a model without its blend state, so effects are checked as placed decorations.
Usage: ingame_overlay.py <mount dir>"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
mount = Path(sys.argv[1]).resolve()
W = REPO / 'assets_dev/worlds/xeen'
CX, CY, Z = 4096, -9216, 1400
PLACE = [('wayup_earth', 4041, (CX, CY, Z), 0), ('wayup_air', 4040, (CX + 1400, CY, Z), 0),
         ('wayup_fire', 4039, (CX - 1400, CY, Z), 270)]
lines = (W / 'maps/xeen_x6.scene.yml').read_text().splitlines(keepends=True)
at = next(i for i, l in enumerate(lines) if l.startswith('spawns:'))
last = max(int(l.split(':')[1]) for l in lines[:at] if l.startswith('  - entity_index:'))
block = []
for k, (name, deco, (x, y, z), facing) in enumerate(PLACE, 1):
    block.append(f"""  - entity_index: {last + k}
    name: {name}
    decoration_list_id: {deco - 1}
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
dst = mount / 'worlds/xeen/maps/xeen_x6.scene.yml'
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(''.join(lines[:at] + block + lines[at:]))
models = mount / 'worlds/xeen/models'
models.mkdir(parents=True, exist_ok=True)
out = (W / 'models/decorations.yml').read_text().rstrip('\n') + '\n' + (HERE / 'integration/indoor_decorations.yml').read_text()
(models / 'decorations.yml').write_text(out)
for p in ('earth', 'air', 'fire'):
    shutil.copy(HERE / f'work/{p}/xeen_deco_wayup_{p}.glb', models / f'xeen_deco_wayup_{p}.glb')
print('WROTE', mount)
