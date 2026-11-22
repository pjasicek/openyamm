#!/usr/bin/env python3
"""Scratch check only (never written to assets_dev): an overlay mount for X6 with the P5 shrine decorations placed on
open ground as A5's generator places them (hands at +-384 facing 270 = south, the Cube and the Scepter at the hands'
own spots, the cake and a bench beside), the outdoor bindings (X6 is outdoors: a copy of decorations.yml with this
project's indoor bindings appended) and the Pharaoh's actor binding (the xeen_pharaoh_claude overlay).
Usage: ingame_overlay.py <mount dir>"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
mount = Path(sys.argv[1]).resolve()
W = REPO / 'assets_dev/worlds/xeen'
CX, CY, Z = 4096, -9216, 1400
PLACE = [('p5_hand_w', 4017, (CX - 384, CY, Z), 270), ('p5_hand_e', 4018, (CX + 384, CY, Z), 270),
         ('p5_cube', 4019, (CX - 384, CY, Z), 0), ('p5_scepter', 4020, (CX + 384, CY, Z), 0),
         ('p5_cake', 4021, (CX + 1100, CY + 300, Z), 0), ('p5_bench', 4022, (CX - 1100, CY - 200, Z), 270)]
src = W / 'maps/xeen_x6.scene.yml'
lines = src.read_text().splitlines(keepends=True)
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
ind = (W / 'models/indoor_decorations.yml').read_text()
mine = ind[ind.index('  # P5 shrine (lane S, xeen-s7-p5'):]
out = (W / 'models/decorations.yml').read_text().rstrip('\n') + '\n' + mine
(mount / 'worlds/xeen/models').mkdir(parents=True, exist_ok=True)
(mount / 'worlds/xeen/models/decorations.yml').write_text(out)
act = (W / 'models/actors.yml').read_text()
mine = (REPO / 'level_generation/creatures/xeen_pharaoh_claude/integration/actors.yml').read_text()
block = mine[mine.index('- descriptor: Xeen Dragon Pharaoh'):]
i = act.index('- descriptor: Xeen Dragon Pharaoh')
j = act.find('\n- descriptor:', i + 10)
act = act[:i] + block + (act[j + 1:] if j >= 0 else '')
(mount / 'worlds/xeen/models/actors.yml').write_text(act)
print('WROTE', mount)
