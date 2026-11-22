# Writes the tour yml: python3 tour.py <out yml> <output dir>
import sys, yaml
H = 'render hud off'
S = [
 ('arrival-gate-hall', [0, -3000, 0], 1.5708, 0.02, []),
 ('tower-door-from-inside', [0, -2300, 0], -1.5708, 0.05, []),
 ('gallery-warden-door-shut', [-1150, -1250, 0], 3.1416, 0.0, []),
 ('gallery-warden-door-open', [-1150, -1250, 0], 3.1416, 0.0, ['event 24'], 3.0),
 ('warden-lodge-cage-1', [-1750, -1300, 0], 3.75, -0.05, []),
 ('cauldron-from-the-west-arch', [-320, -1000, 0], 1.25, 0.22, []),
 ('shaft-up-from-the-cauldron-rim', [520, -620, 0], 2.2, 0.95, []),
 ('alacorn-from-below', [600, 250, 0], 3.6, 0.85, []),
 ('goblin-pens', [800, -1750, 0], -0.45, 0.0, []),
 ('toad-larder', [-760, -1700, 0], 3.9, -0.08, []),
 ('east-stair-turn', [1750, -1312, 0], 0.0, 0.12, []),
 ('balcony-over-the-shaft', [1110, 300, 640], 3.3, -0.9, []),
 ('dormitory-loose-panel-shut', [3000, 420, 640], 0.0, -0.05, []),
 ('dormitory-loose-panel-open', [4250, 420, 640], 0.0, -0.05, ['event 17'], 4.0),
 ('schoolroom-slate-and-mistress', [1750, 1650, 640], 0.0, 0.05, []),
 ('schoolroom-cage-2', [2500, 1900, 640], 0.9, -0.05, []),
 ('schoolroom-doors-shut', [1320, 1312, 640], 0.0, 0.0, []),
 ('schoolroom-doors-open', [1320, 1312, 640], 0.0, 0.0, ['event 23'], 3.0),
 ('talking-skulls', [1750, 640, 640], 0.0, -0.05, []),
 ('west-stair', [1312, 1700, 640], 1.5708, 0.25, []),
 ('vat-hall-three-vats', [-1536, 2150, 1280], 1.5708, -0.05, []),
 ('bookcase-shut', [-2250, 2368, 1280], 3.1416, 0.0, []),
 ('bookcase-open-cage-3', [-2250, 2368, 1280], 3.1416, 0.0, ['event 5'], 5.0),
 ('herb-loft', [150, 1750, 1472], 0.45, 0.0, []),
 ('broken-balcony-gap', [384, 1230, 1280], -1.5708, -0.75, []),
 ('north-stair', [-1450, 1312, 1280], 3.1416, 0.28, []),
 ('rosebud-door-shut', [-3072, 1400, 1920], -1.5708, 0.05, []),
 ('rosebud-door-open', [-3072, 1400, 1920], -1.5708, 0.05,
  ['lua evt.SetDoorState(15, DoorAction.Open); evt.SetDoorState(16, DoorAction.Open)'], 4.0),
 ('sanctum-witch-mark-circle', [-1700, 650, 1920], 3.45, -0.15, ['actor kill 450']),
 ('pier-and-bridge', [-1000, -128, 1920], 0.0, -0.08, []),
 ('bridge-the-alacorn', [-420, -128, 1920], 0.0, -0.15, []),
 ('from-the-landing-down-the-shaft', [20, -140, 1920], 0.2, -1.15, []),
 ('bedchamber-cage-4', [-2700, -650, 1920], 3.1416, -0.05, []),
 ('hoist-room-cage-up', [-2150, -620, 1920], 0.0, -0.05, []),
 ('hoist-brake-pulled', [-2150, -620, 1920], 0.0, -0.05, ['event 6'], 13.0),
 ('hoist-cage-at-the-bottom', [-760, -528, 0], 3.1416, 0.05, []),
 ('ward-shut', [-3700, 448, 1920], 3.1416, 0.0, []),
 ('ward-fallen', [-3700, 448, 1920], 3.1416, 0.0, ['lua evt.SetDoorState(19, DoorAction.Open)'], 4.0),
 ('roof-stair-and-hatch', [-4250, 448, 1920], 3.1416, 0.2, []),
 ('roof-and-cloud-stair', [-5650, 300, 2560], 3.0, 0.05, []),
]
shots = []
for s in S:
    d = {'name': s[0], 'position': s[1], 'yaw': s[2], 'pitch': s[3], 'commands': [H] + s[4]}
    if len(s) > 5:
        d['settle_seconds'] = s[5]
    shots.append(d)
out = {'output_dir': sys.argv[2], 'exit': True, 'settle_seconds': 1.3, 'shots': shots}
open(sys.argv[1], 'w').write(yaml.safe_dump(out, sort_keys=False, default_flow_style=None, width=200))
