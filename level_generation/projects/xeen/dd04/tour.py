"""Write DD-04's look tour YAML: tour.py <name> (shots below)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys, math, yaml
R = _REPO_ROOT + '/output/studio_cal/dd04/'
N, E, S, W = math.pi / 2, 0.0, -math.pi / 2, math.pi
SHOTS = [
    ('arrival', (0, 200, 0), N, 0, []),
    ('tiny-door-from-inside', (0, 560, 0), S, -0.05, []),
    ('burrow-entry', (0, 760, 0), N, 0, []),
    ('burrow-bend', (300, 1400, 0), N, 0, []),
    ('bolt-hole-mouth', (240, 1664, 0), E, -0.1, []),
    ('plunder-from-burrow', (0, 2380, 0), N, 0, []),
    ('plunder-west', (250, 2700, 0), W + 0.35, -0.05, []),
    ('plunder-to-cellar-arch', (-300, 2816, 0), E, 0, []),
    ('cellar-from-arch', (960, 2700, 0), E + 0.4, 0, []),
    ('cellar-arm-to-larder-door', (1408, 3700, 0), N, 0, []),
    ('waiting-door-closed', (0, 3150, 0), N, 0, []),
    ('waiting-door-open', (0, 3150, 0), N, 0, ['event 10']),
    ('waiting-room', (0, 3520, 0), N, 0, []),
    ('waiting-sign', (150, 3776, 0), W, 0.05, []),
    ('court-door-open', (0, 3800, 0), N, 0, ['event 8']),
    ('court-from-door', (0, 4300, 0), N, 0.05, []),
    ('court-throne', (0, 4950, 0), N, 0.18, []),
    ('court-east-side', (700, 4500, 0), N + 0.7, 0.05, []),
    ('court-hatch-closed', (600, 5248, 0), E, 0, []),
    ('court-hatch-open', (600, 5248, 0), E, 0, ['event 16']),
    ('larder-door-open', (1408, 4400, 0), N, 0, ['event 9']),
    ('larder', (1250, 4950, 0), N - 0.3, -0.05, []),
    ('larder-trapdoor-open', (1300, 5344, 0), E, -0.1, ['event 23']),
    ('trapdoor-stair-down', (1700, 5344, 0), E, -0.25, []),
    ('bolt-hole-down', (650, 1664, -30), E, -0.15, []),
    ('barracks-from-bolt', (1650, 1664, -384), E, 0, []),
    ('barracks-north', (2700, 1300, -384), N + 0.6, 0, []),
    ('sap-tunnel', (2560, 2450, -384), N, 0, []),
    ('sap-bend', (2848, 3700, -384), N, 0, []),
    ('sap-stair-from-tunnel', (2800, 5344, -384), W, 0.1, []),
    ('stair-up-to-trapdoor', (2380, 5344, -380), W, 0.2, []),
    ('sap-last-dig', (2720, 6100, -384), N, -0.05, []),
]
name = sys.argv[1]
d = {'output_dir': R + name, 'exit': True, 'settle_seconds': 2.5, 'shots': []}
for i, (n, p, yaw, pitch, cmds) in enumerate(SHOTS):
    d['shots'].append({'name': '%02d-%s' % (i + 1, n), 'position': list(p), 'yaw': yaw, 'pitch': pitch,
                       'commands': ['render hud off'] + cmds})
yaml.safe_dump(d, open(R + name + '.yml', 'w'), sort_keys=False)
print(R + name + '.yml')
