# Pass two's poses (the user's eight places and every thing changed): python3 tour2.py <out yml> <output dir>
import math, sys, yaml
H = 'render hud off'
D = math.radians
S = [
 # The user's four new poses, as he gave them (yaw radians, pitch degrees).
 ('u1-torch-in-the-air', [-1433.98, -185.02, 1920], 0.257, D(21.5), []),
 ('u2-door-tiling', [-3827.96, 453.52, 1920], 3.130, D(-3.5), []),
 ('u3-hoist-cage-and-call', [-817.43, -480.14, 0], 4.102, D(-9.7), []),
 ('u4-ward-from-the-sanctum', [-3700, 448, 1920], 3.1416, 0.0, []),
 # His first four.
 ('braziers-by-the-cauldron', [700, -700, 0], 2.36, 0.25, []),
 ('braziers-up-close', [-150, -950, 0], 1.2, 0.35, []),
 ('vat-hall-fires', [-1536, 2150, 1280], 1.5708, -0.05, []),
 ('slate', [2650, 1728, 640], 0.0, 0.0, []),
 ('schoolroom-cage-2', [2752, 1900, 640], 1.5708, -0.08, []),
 ('rosebud-door', [-3072, 1400, 1920], -1.5708, 0.05, []),
 # The other cages and clues.
 ('lodge-cage-1', [-2400, -1800, 0], 3.1416, -0.08, []),
 ('hidden-cage-3', [-2300, 2368, 1280], 3.1416, -0.05, ['event 5'], 5.0),
 ('bedchamber-cage-4', [-3500, -560, 1920], 3.1416, -0.08, []),
 ('recipe-card', [544, 1800, 1472], 1.5708, 0.0, []),
 ('cauldron-from-the-west-arch', [-320, -1000, 0], 1.25, 0.22, []),
 ('shaft-up-from-the-cauldron-rim', [520, -620, 0], 2.2, 0.95, []),
 ('roof-and-cloud-stair', [-5650, 300, 2560], 3.0, 0.05, []),
 ('roof-up', [-6000, 800, 2560], 3.6, 0.6, []),
 ('bedchamber-door', [-2200, -150, 1920], 4.4, 0.0, []),
 ('gallery-warden-door', [-1150, -1250, 0], 3.1416, 0.0, []),
]
shots = []
for s in S:
    d = {'name': s[0], 'position': s[1], 'yaw': s[2], 'pitch': round(s[3], 4), 'commands': [H] + s[4]}
    if len(s) > 5:
        d['settle_seconds'] = s[5]
    shots.append(d)
out = {'output_dir': sys.argv[2], 'exit': True, 'settle_seconds': 1.5, 'shots': shots}
open(sys.argv[1], 'w').write(yaml.safe_dump(out, sort_keys=False, default_flow_style=None, width=200))
