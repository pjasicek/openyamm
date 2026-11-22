"""Write DD-10A's look tour YAML: tour.py <name> (shots below). The shots' `event N` commands use ids.lock.yml."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys, math, yaml
R = _REPO_ROOT + '/output/studio_cal/dd10a/shots/'
N, E, S, W = math.pi / 2, 0.0, -math.pi / 2, math.pi
SHOTS = [
    ('arrival', (0, 192, 0), N, 0, []),
    ('adit-mouth-from-inside', (0, 700, 0), S, -0.05, []),
    ('adit-door-closed', (0, 640, 0), N, 0, []),
    ('adit-door-open', (0, 640, 0), N, 0, ['event 10']),
    ('gallery-north-leg', (0, 1150, 0), N, 0, []),
    ('gallery-bend', (0, 2100, 0), N + 0.6, 0.05, []),
    ('gallery-cart', (500, 2350, 0), E + 0.35, -0.1, []),
    ('gallery-east-to-ruby', (900, 2432, 0), E, 0, []),
    ('ruby-from-gallery', (1800, 2432, 0), E, 0.1, []),
    ('ruby-south-veins', (2500, 2300, 0), S + 0.2, 0, []),
    ('ruby-north-veins', (2600, 2850, 0), N - 0.3, 0.05, []),
    ('ruby-vein-close', (2450, 2050, 0), S, -0.05, []),
    ('ruby-pillar-roof', (2200, 2900, 0), E - 0.4, 0.35, []),
    ('ruby-to-cobweb', (3100, 2560, 0), E, 0, []),
    ('cobweb-from-ruby', (3700, 2560, 0), E, 0.05, []),
    ('cobweb-cocoon', (4400, 2650, 0), E, -0.1, []),
    ('cobweb-west-web', (4300, 2900, 0), N + 0.8, 0.1, []),
    ('cobweb-sump-door', (4288, 2500, 0), S, 0, []),
    ('cobweb-sump-door-open', (4288, 2500, 0), S, 0, ['event 12']),
    ('sump-from-door', (4288, 1850, 0), S, -0.15, []),
    ('sump-pool-chest', (4300, 1700, 0), S - 0.6, -0.15, []),
    ('sump-west-door-open', (4200, 1376, 0), W, 0, ['event 11']),
    ('emerald-from-sump', (3450, 1376, 0), W - 0.3, 0, []),
    ('emerald-south-veins', (2700, 1150, 0), S, 0, []),
    ('emerald-north-veins', (2800, 950, 0), N + 0.3, 0.05, []),
    ('emerald-to-bones', (2400, 1024, 0), W, 0, []),
    ('bones-from-emerald', (1850, 1050, 0), W + 0.3, -0.1, []),
    ('bones-heaps', (1250, 1400, 0), S - 0.8, -0.2, []),
    ('bones-chest', (1320, 1150, 0), S, -0.2, []),
    ('bones-to-gallery', (1024, 1600, 0), N, 0, []),
    ('gallery-from-bones', (1024, 2000, 0), N, 0.05, []),
]
name = sys.argv[1]
d = {'output_dir': R + name, 'exit': True, 'settle_seconds': 2.5, 'shots': []}
for i, (n, p, yaw, pitch, cmds) in enumerate(SHOTS):
    d['shots'].append({'name': '%02d-%s' % (i + 1, n), 'position': list(p), 'yaw': yaw, 'pitch': pitch,
                       'commands': ['render hud off'] + cmds})
yaml.safe_dump(d, open(R + name + '.yml', 'w'), sort_keys=False)
print(R + name + '.yml')
