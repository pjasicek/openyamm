"""Write DD-10B's look tour YAML: tour.py <name> (shots below). The shots' `event N` commands use ids.lock.yml."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys, math, yaml
R = _REPO_ROOT + '/output/studio_cal/dd10b/shots/'
N, E, S, W = math.pi / 2, 0.0, -math.pi / 2, math.pi
D = -480
SHOTS = [
    ('arrival', (0, 192, 0), N, 0, []),
    ('adit-mouth-from-inside', (0, 700, 0), S, -0.05, []),
    ('adit-door-closed', (0, 640, 0), N, 0, []),
    ('adit-door-open', (0, 640, 0), N, 0, ['event 5']),
    ('upper-north-leg', (0, 1150, 0), N, 0, []),
    ('upper-bend', (0, 2000, 0), N + 0.6, 0.05, []),
    ('upper-east-leg', (300, 2304, 0), E, 0, []),
    ('side-cut', (1152, 2450, 0), N, -0.1, []),
    ('side-cut-chest-cart', (1000, 2750, 0), N - 0.5, -0.2, []),
    ('ramp-top', (1280, 2200, 0), S, -0.1, []),
    ('ramp-leg1', (1280, 1800, -30), S, -0.1, []),
    ('ramp-leg2', (1200, 1280, -110), W, -0.1, []),
    ('ramp-leg3', (704, 1150, -200), S, -0.1, []),
    ('ramp-leg4', (800, 384, -360), E, -0.1, []),
    ('ramp-door-closed', (1950, 384, -460), E, 0, []),
    ('ramp-door-open', (1950, 384, -460), E, 0, ['event 6']),
    ('flooded-from-door', (2450, 384, D), E, -0.1, []),
    ('flooded-pool', (2700, 200, D), N + 0.3, -0.15, []),
    ('flooded-chest', (2700, 100, D), W - 0.4, -0.2, []),
    ('flooded-to-god', (3300, 256, D), E, 0, []),
    ('god-from-west', (4000, 300, D), E, 0.05, []),
    ('god-face', (4650, 352, D), E, 0.1, []),
    ('god-hall-north', (4500, 100, D), N, 0.05, []),
    ('stair-from-god', (4608, 850, D), N, 0.15, []),
    ('stair-from-top', (4608, 1880, 0), S, -0.25, []),
    ('throne-from-stair', (4608, 2100, 0), N + 0.4, 0.05, []),
    ('throne', (4450, 2432, 0), E, 0.05, []),
    ('throne-hall-west', (4700, 2432, 0), W, 0.05, []),
    ('throne-door-open', (4150, 2432, 0), W, 0, ['event 7']),
    ('sapphire-from-throne', (3650, 2432, 0), W, 0.05, []),
    ('sapphire-south-veins', (2700, 2000, 0), S + 0.2, 0, []),
    ('sapphire-north-veins', (2900, 2800, 0), N - 0.3, 0.05, []),
    ('sapphire-false-vein', (2300, 2600, 0), N + 0.9, 0, []),
    ('sapphire-vein-close', (2450, 1850, 0), S + 0.1, -0.05, []),
    ('sapphire-from-drift', (2000, 2304, 0), E, 0.1, []),
    ('god-crystal-side', (4700, 650, D), E - 0.6, 0.05, []),
    ('flooded-chest-view', (2700, 0, D), W - 0.2, -0.25, []),
    ('stair-steps-up', (4608, 1000, D), N, 0.3, []),
]
name = sys.argv[1]
only = sys.argv[2:]
if only:
    SHOTS = [x for x in SHOTS if any(o in x[0] for o in only)]
d = {'output_dir': R + name, 'exit': True, 'settle_seconds': 2.5, 'shots': []}
for i, (n, p, yaw, pitch, cmds) in enumerate(SHOTS):
    d['shots'].append({'name': '%02d-%s' % (i + 1, n), 'position': list(p), 'yaw': yaw, 'pitch': pitch,
                       'commands': ['render hud off'] + cmds})
yaml.safe_dump(d, open(R + name + '.yml', 'w'), sort_keys=False)
print(R + name + '.yml')
