"""Write DD-10C's look tour YAML: tour.py <name> [filters] (shots below). The shots' `event N` commands use ids.lock.yml
(9 adit door, 10 collapse door, 11 grotto door)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys, math, yaml
R = _REPO_ROOT + '/output/studio_cal/dd10c/shots/'
N, E, S, W = math.pi / 2, 0.0, -math.pi / 2, math.pi
SHOTS = [
    ('arrival', (0, 192, 0), N, 0, []),
    ('adit-mouth-sealed', (0, 700, 0), S, -0.05, []),
    ('adit-door-closed', (0, 640, 0), N, 0, []),
    ('adit-door-open', (0, 640, 0), N, 0, ['event 9']),
    ('lava-from-door', (0, 1150, 0), E + 0.15, -0.05, []),
    ('lava-seam-west', (600, 1450, 0), -0.7, -0.3, []),
    ('lava-seam-east', (2000, 1450, 0), -2.3, -0.3, []),
    ('lava-seam-above', (1300, 1250, 0), S, -0.5, []),
    ('lava-looking-west', (1900, 1400, 0), W, 0, []),
    ('collapse-door-closed', (320, 1450, 0), N, 0, []),
    ('collapse-door-open', (320, 1450, 0), N, 0, ['event 10']),
    ('diamond-from-lava', (1950, 1344, 0), E, 0.05, []),
    ('diamond-south-veins', (3300, 1250, 0), S, 0.05, []),
    ('diamond-east', (3500, 1450, 0), E - 0.2, 0.05, []),
    ('diamond-north-east', (3500, 1500, 0), N - 0.5, 0.05, []),
    ('diamond-false-vein', (2950, 1450, 0), N + 0.8, 0, []),
    ('diamond-vein-close', (2700, 900, 0), S - 0.3, -0.05, []),
    ('diamond-overview', (4150, 700, 0), W + 0.5, 0.1, []),
    ('grotto-door-closed', (4250, 1344, 0), E, 0, []),
    ('grotto-door-open', (4250, 1344, 0), E, 0, ['event 11']),
    ('grotto', (4650, 1344, 0), E, -0.1, []),
    ('grotto-back', (5150, 1300, 0), W, 0, []),
    ('nest-from-diamond', (3072, 2100, 0), N, 0, []),
    ('nest-west', (3200, 2750, 0), W, -0.05, []),
    ('nest-eggs', (2300, 2650, 0), N, -0.2, []),
    ('collapse-from-nest', (1600, 2528, 0), W, 0, []),
    ('collapse-rubble', (850, 2300, 0), W + 0.3, 0.05, []),
    ('collapse-heap', (760, 2560, 0), W + 0.1, -0.05, []),
    ('collapse-to-door', (-300, 2300, 0), -0.4, -0.05, []),
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
