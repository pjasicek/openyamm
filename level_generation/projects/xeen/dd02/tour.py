"""Write DD-02's look tour YAML: tour.py <name> (shots below)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys, math, yaml
R = _REPO_ROOT + '/output/studio_cal/dd02/'
N, E, S, W = math.pi / 2, 0.0, -math.pi / 2, math.pi
SHOTS = [
    ('arrival', (-1216, 640, 0), E, 0, []),
    ('entry-to-front-door', (-100, 640, 0), W, 0, []),
    ('entry-mirror-and-gate', (-500, 400, 0), N - 0.3, 0.05, []),
    ('store-door-open', (-448, 300, 0), S, -0.05, ['event 14']),
    ('store', (-448, -250, 0), S + 0.4, -0.05, []),
    ('question-hall', (700, 300, 0), N + 0.2, 0.05, []),
    ('question-door', (912, 560, 0), N, 0.1, []),
    ('question-door-open', (912, 560, 0), N, 0.1, ['event 22']),
    ('stair1-up', (912, 1000, 0), N, 0.25, []),
    ('stair1-landing', (1000, 2432, 480), E, 0, []),
    ('wards', (1700, 1450, 480), N + 0.6, 0, []),
    ('roost-door-open', (2650, 2368, 480), E, 0, ['event 13']),
    ('roost', (3000, 2000, 480), N + 0.6, 0.05, []),
    ('tapestry-gallery', (3392, 1700, 480), S, 0, []),
    ('tapestry-gallery-east', (3300, 1000, 480), E + 0.3, 0, []),
    ('back1-panel-open', (3600, 672, 480), E, 0, ['event 8']),
    ('back-stair-up', (4112, 950, 480), N, 0.25, []),
    ('gallery2', (3392, 2550, 960), S, 0, []),
    ('library-from-gallery', (2700, 1408, 960), W, 0, []),
    ('library-south', (2176, 300, 960), N, 0.05, []),
    ('library-lectern-fire', (1950, 640, 960), W, -0.25, []),
    ('reading-door-open', (2176, 2000, 960), N, 0, ['event 12']),
    ('reading-room', (1700, 2400, 960), E + 0.5, 0, []),
    ('stair2-landing', (1300, 640, 960), W, 0, []),
    ('stair3-up', (912, 1000, 960), N, 0.25, []),
    ('tapestries-from-stair', (1700, 2432, 1440), E - 0.4, 0.05, []),
    ('tapestries-maze', (1700, 3100, 1440), S + 0.3, 0.05, []),
    ('tapestries-arm', (2600, 700, 1440), E, 0, []),
    ('back3-panel-open', (3650, 672, 1440), E, 0, ['event 9']),
    ('crates', (4112, 1100, 1440), W + 0.2, -0.05, []),
    ('loft-door-open', (2650, 2368, 1440), E, 0.1, ['event 11']),
    ('loft', (3000, 2100, 1440), N + 0.5, 0.15, []),
    ('trap-walk-east', (4992, 2400, 1440), S, 0, []),
    ('trap-walk-south', (4900, 224, 1440), W, 0, []),
    ('last-stair-up', (1264, 400, 1440), N, 0.25, []),
    ('top-landing', (1264, 2432, 1920), W, 0, []),
    ('last-door', (560, 2432, 1920), W, 0.05, []),
    ('last-door-open', (400, 2464, 1920), W, 0, ['event 20']),
    ('study-from-door', (-150, 2464, 1920), W + 0.5, 0.05, []),
    ('study-desk-ellinger', (-832, 2750, 1920), N, 0.05, []),
    ('study-west', (-300, 3200, 1920), W, 0.05, []),
    ('boots-door-open', (-1152, 3550, 1920), N, 0, ['event 10']),
    ('boot-closet', (-1152, 4000, 1920), E + 0.5, -0.05, []),
    ('lift-head', (-768, 2350, 1920), S, -0.1, []),
    ('shaft-from-foot', (-768, 1100, 0), N, 0.35, []),
]
name = sys.argv[1]
d = {'output_dir': R + name, 'exit': True, 'settle_seconds': 2.5, 'shots': []}
for i, (n, p, yaw, pitch, cmds) in enumerate(SHOTS):
    d['shots'].append({'name': '%02d-%s' % (i + 1, n), 'position': list(p), 'yaw': yaw, 'pitch': pitch,
                       'commands': ['render hud off'] + cmds})
yaml.safe_dump(d, open(R + name + '.yml', 'w'), sort_keys=False)
print(R + name + '.yml')
