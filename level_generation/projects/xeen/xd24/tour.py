"""Writes output/studio_cal/xd24/<name>.yml: tour.py <name> (by day; the iron door and the Count's stair opened by console
for the last shots)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys, math, os, yaml
name = sys.argv[1]
P = math.pi
H = ['render hud off']
V = ['qbit set 110940', 'event 24']
C = ['qbit set 112141', 'event 11']
ALL = [
    ('foot_south', [0, 950, 0], -P / 2, 0.0, H),
    ('foot_north', [0, 150, 0], P / 2, 0.1, None),
    ('coffin_stair', [0, 1250, 40], P / 2, 0.25, None),
    ('foot_east', [-350, 512, 0], 0.0, 0.0, None),
    ('niches_west', [350, -384, 0], P, -0.05, None),
    ('niche_coffin', [192, -430, 0], -P / 2, -0.45, None),
    ('ossuary_west', [-720, 640, 0], P, 0.0, None),
    ('ossuary_north', [-1280, 150, 0], P / 2, 0.1, None),
    ('chapel_altar', [-2656, -100, 0], P / 2, 0.15, None),
    ('chapel_west', [-2120, 576, 0], P, 0.05, None),
    ('chapel_roof', [-2656, 200, 0], P / 2, 0.9, None),
    ('sexton', [-3540, 704, 0], P, -0.1, None),
    ('chapel_stair', [-2688, -560, 0], -P / 2, -0.3, None),
    ('cataw_south', [-2752, -2180, -640], -P / 2, 0.0, None),
    ('gallery_east', [-2200, -2496, -640], 0.0, 0.05, None),
    ('gallery_north', [-1280, -2830, -640], P / 2, 0.1, None),
    ('gallery_south', [-1600, -2150, -640], -P / 2, 0.1, None),
    ('catae_south', [-576, -3150, -640], -P / 2, 0.0, None),
    ('feast_west', [-1100, -3290, -640], P, -0.1, None),
    ('feast_table', [-1600, -3450, -640], -P / 2, -0.45, None),
    ('vstair_down', [-60, -2496, -640], 0.0, -0.25, None),
    ('iron_door', [700, -2496, -1100], 0.0, 0.05, None),
    ('vault_from_door', [1300, -2496, -1280], 0.0, 0.1, V),
    ('vault_dais', [2048, -3300, -1280], P / 2, 0.1, None),
    ('vault_roof', [2048, -3100, -1280], P / 2, 0.9, None),
    ('vault_ne', [1500, -1900, -1280], -0.3, 0.0, None),
    ('vault_south', [2300, -1900, -1280], -P / 2, 0.05, None),
    ('count_stair_base', [2048, -2000, -1280], P / 2, 0.15, C),
    ('count_stair', [2048, -1300, -1280], P / 2, 0.25, None),
    ('count_stair_turn', [2000, 400, -400], P, 0.1, None),
    ('count_stair_top', [900, 512, -60], P, 0.0, None),
    ('foot_from_count', [300, 512, 0], P, 0.0, None),
]
PICK = os.environ.get('PICK')
shots = [x for x in ALL if not PICK or x[0] in PICK.split(',')]
doc = {'output_dir': f'{_REPO_ROOT}/output/studio_cal/xd24/{name}', 'exit': True,
       'settle_seconds': 1.5, 'shots': []}
for i, (n, pos, yaw, pitch, cmds) in enumerate(shots):
    s = {'name': n, 'position': pos, 'yaw': round(yaw, 4), 'pitch': pitch}
    if cmds or i == 0:
        s['commands'] = (cmds or []) if cmds is not H else H
        if i == 0 and cmds is not H:
            s['commands'] = H + (cmds or [])
    doc['shots'].append(s)
open(f'{_REPO_ROOT}/output/studio_cal/xd24/{name}.yml', 'w').write(yaml.safe_dump(doc, sort_keys=False))
