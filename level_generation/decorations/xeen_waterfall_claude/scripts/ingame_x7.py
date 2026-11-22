#!/usr/bin/env python3
"""Scratch check only (never written to assets_dev): X7's lava cove with two of A5's three lava falls swapped for
the water fall, as a static decoration, so its additive layers draw as the engine draws decorations (a `model spawn`
instance draws additive layers as plain blended). The cove's south wall is the nearest installed stand-in for
XD-17's east cliff: black basalt, a drop to a flat surface (the stars plane at 0).
- the west fall (x 3328): its lip 1,760 up the wall (a notch below the crest), its foot on the plane at 0;
- the middle fall (x 4864): at the crest (2,304), as A5 placed the lava fall.
Writes work/ingame/mount/worlds/xeen/maps/xeen_x7.scene.yml, the overlay's decorations.yml (assets_dev's plus a
scratch binding of the build in work/, or the installed model with `installed`) and work/ingame/tour_x7.yml.
Usage: ingame_x7.py <out_dir> [installed]"""
import math
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.dont_write_bytecode = True     # never write into A5's folder
sys.path.insert(0, str(REPO / 'output/studio_cal/x7/tools'))
import land as LD  # noqa: E402

OUT = Path(sys.argv[1]).resolve()
INSTALLED = 'installed' in sys.argv[2:]
MOUNT = HERE / 'work/ingame/mount'
SWAP = {'1525': 1760, '1526': None}       # entity index -> new z (None keeps A5's)

scene = (REPO / 'assets_dev/worlds/xeen/maps/xeen_x7.scene.yml').read_text().splitlines(keepends=True)
out, current = [], None
for line in scene:
    if line.startswith('  - entity_index: '):
        current = line.split(':')[1].strip()
    if current in SWAP:
        if line.startswith('    name: xeen_lavafall'):
            line = '    name: xeen_waterfall\n'
        elif line.startswith('    decoration_list_id: 4003'):
            line = '    decoration_list_id: 4015\n'
        elif line.startswith('      z: ') and SWAP[current] is not None:
            line = f'      z: {SWAP[current]}\n'
    out.append(line)
target = MOUNT / 'worlds/xeen/maps/xeen_x7.scene.yml'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(''.join(out))

if INSTALLED:
    (MOUNT / 'worlds/xeen/models/decorations.yml').unlink(missing_ok=True)
else:
    report = yaml.safe_load((HERE / 'work/waterfall/report.json').read_text())
    decos = (REPO / 'assets_dev/worlds/xeen/models/decorations.yml').read_text()
    decos += ('  # scratch test binding (work/ingame only)\n  - name: xeen_waterfall\n'
              '    model: worlds/xeen/models/xeen_wf_test.glb\n'
              f"    height: {report['height_units']:.2f}\n    yaw: facing\n")
    (MOUNT / 'worlds/xeen/models').mkdir(parents=True, exist_ok=True)
    (MOUNT / 'worlds/xeen/models/decorations.yml').write_text(decos)


def W(x, y):
    return [round((x - 64) * 512), round((64 - y) * 512)]


SHOTS = [  # name, eye cell, look-at cell, extra height, pitch, time
    ('cove_falls', (66.4, 27.0), (73.5, 28.6), 250, -0.3, '15:00'),
    ('signature', (67, 25), (75.5, 32), 0, -0.22, '17:30'),
    ('west_near', (68.6, 27.2), (70.5, 28.6), 120, -0.35, '13:00'),
    ('west_foot', (68.6, 27.2), (70.5, 28.0), 120, -0.75, '13:00'),
    ('west_far', (64.0, 23.0), (71.0, 28.4), 300, -0.18, '11:00'),
    ('night', (66.4, 27.0), (73.5, 28.6), 250, -0.3, '23:00'),
]
shots = []
for name, eye, look, up, pitch, t in SHOTS:
    x, y = W(*eye)
    z = round(max(LD.raw_height(*eye), 0) + 200 + up)
    yaw = math.atan2(-(look[1] - eye[1]), look[0] - eye[0])
    shots.append({'name': name, 'position': [x, y, z], 'yaw': round(yaw, 4), 'pitch': pitch, 'time': t,
                  'commands': ['render hud off', 'sky weather 0', 'weather clear']})
doc = {'output_dir': str(OUT), 'exit': True, 'settle_seconds': 2.5, 'shots': shots}
(HERE / 'work/ingame/tour_x7.yml').write_text(yaml.safe_dump(doc, sort_keys=False, width=120))
print('wrote', target, len(shots), 'shots')
