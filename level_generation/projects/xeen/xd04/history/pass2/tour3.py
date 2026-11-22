# Close looks after the fixes: python3 tour3.py <out yml> <output dir>
import math, sys, yaml
H = 'render hud off'
D = math.radians
O = lambda n: f'lua evt.SetDoorState({n}, DoorAction.Open)'
S = [
 ('cage-2-close', [2752, 1960, 640], 1.5708, -0.12, []),
 ('cage-2-hoisted', [2752, 1960, 640], 1.5708, 0.1, [O(27)], 4.5),
 ('cage-1-close', [-2560, -1850, 0], 3.1416, -0.1, []),
 ('cage-1-hoisted', [-2560, -1850, 0], 3.1416, 0.1, [O(26)], 4.0),
 ('cage-4-close', [-3600, -560, 1920], 2.9, -0.1, []),
 ('cage-3-close', [-2600, 2420, 1280], 3.1416, -0.1, ['event 5'], 5.0),
 ('lodge-table-ring', [-1760, -1480, 0], 3.46, -0.4, []),
 ('brazier-chain-at-beam', [-150, -830, 0], 1.5708, 0.75, []),
 ('braziers-wide', [0, -950, 0], 1.5708, 0.3, []),
 ('slate-angle', [2900, 1450, 640], 0.35, 0.0, []),
 ('slate-straight', [2950, 1728, 640], 0.0, 0.05, ['actor kill 7']),
 ('ward-close', [-3850, 448, 1920], 3.1416, 0.05, []),
 ('ward-from-the-stair', [-4300, 448, 1950], 0.0, -0.05, []),
 ('rosebud-opening', [-3072, 1400, 1920], -1.5708, 0.05, [O(15), O(16)], 1.2),
 ('rosebud-open', [-3072, 1400, 1920], -1.5708, 0.05, [], 4.0),
 ('bedchamber-door', [-3344, 150, 1920], -1.5708, 0.0, []),
 ('warden-door', [-1150, -1312, 0], 3.1416, 0.0, []),
 ('schoolroom-doors', [1320, 1312, 640], 0.0, 0.0, []),
 ('hoist-gate-and-call', [-817.43, -480.14, 0], 4.102, D(-9.7), []),
 ('roof-sky', [-5650, 300, 2560], 3.0, 0.15, []),
 ('roof-cloud-stair', [-6500, 448, 2560], 3.1416, 0.1, []),
 ('vat-hall-cauldron', [-1536, 2350, 1280], 1.5708, -0.1, []),
 ('pier-torches', [-1200, -128, 1920], 0.0, 0.1, []),
 ('cauldron-iron-and-brew', [500, -500, 0], 2.36, -0.3, []),
]
shots = []
for s in S:
    d = {'name': s[0], 'position': s[1], 'yaw': s[2], 'pitch': round(s[3], 4), 'commands': [H] + s[4]}
    if len(s) > 5:
        d['settle_seconds'] = s[5]
    shots.append(d)
open(sys.argv[1], 'w').write(yaml.safe_dump({'output_dir': sys.argv[2], 'exit': True, 'settle_seconds': 1.5, 'shots': shots}, sort_keys=False, default_flow_style=None, width=200))
