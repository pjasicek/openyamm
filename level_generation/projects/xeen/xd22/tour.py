"""Writes output/studio_cal/xd22/<name>.yml: tour.py <name> (the hatch and the crane screen opened by console for the
shots after them). PICK=a,b limits the shots."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys, math, os, yaml
name = sys.argv[1]
P = math.pi
H = ['render hud off']
ALL = [
    ('porch_in', [0, -256, 0], -P / 2, 0.0, H),
    ('porch_out', [0, -850, 0], P / 2, 0.05, None),
    ('porch_bell_broom', [-150, -760, 0], 0.9, -0.15, None),
    ('kitchen', [-1250, -700, 0], 0.5, 0.05, None),
    ('kitchen_ladder', [-1000, -384, 0], 0.0, 0.45, None),
    ('shrine_altar', [0, -1300, 0], -P / 2, -0.12, None),
    ('shrine_east', [-900, -1650, 0], 0.15, 0.0, None),
    ('stair_e_foot', [1120, -1300, 0], P / 2, 0.2, None),
    ('hatch_open', [0, -1480, 0], -P / 2, -0.7, ['event 18']),
    ('cellar', [300, -1750, -448], -2.2, 0.0, None),
    ('cellar_up', [0, -1720, -448], P / 2, 0.8, None),
    ('dorm', [700, -1500, 512], P / 2, 0.0, None),
    ('dorm_paper', [900, -448, 512], P, 0.0, None),
    ('dojo', [-250, -1500, 512], P / 2 + 0.3, 0.0, None),
    ('dojo_paper', [-200, -448, 512], 0.0, 0.0, None),
    ('stair_w_foot', [-896, -400, 512], -P / 2, 0.25, None),
    ('screens_arrive', [-560, -1520, 1024], P / 2 - 0.3, 0.0, None),
    ('screens_band', [-560, -1240, 1024], 0.0, 0.0, None),
    ('screens_cells', [-300, -1000, 1024], P / 2, 0.05, None),
    ('crane', [672, -1580, 1024], P / 2, 0.05, None),
    ('crane_broken', [672, -1580, 1024], P / 2, 0.1, ['destructible 1 destroy']),
    ('armoury', [-650, -760, 1536], 0.0, 0.0, None),
    ('armoury_well', [360, -650, 1536], -P / 2, -0.4, None),
    ('gallery_west', [-1020, -700, 1536], -P / 2, 0.0, None),
    ('gallery_south', [-1000, -1568, 1536], 0.0, 0.0, None),
    ('gallery_sky', [0, -1540, 1536], -P / 2, 0.15, None),
    ('rope_top', [860, -1568, 1536], 0.0, -0.5, None),
    ('top_stair', [-1000, -1184, 1536], 0.0, 0.3, None),
    ('master', [-650, -1250, 2048], 0.35, 0.05, None),
    ('master_dais', [300, -1250, 2048], P / 2, 0.1, None),
    ('rope_foot', [600, -1530, 1024], 0.0, 0.1, None),
]
PICK = os.environ.get('PICK')
shots = [x for x in ALL if not PICK or x[0] in PICK.split(',')]
doc = {'output_dir': f'{_REPO_ROOT}/output/studio_cal/xd22/{name}', 'exit': True,
       'settle_seconds': 1.5, 'shots': []}
for i, (n, pos, yaw, pitch, cmds) in enumerate(shots):
    s = {'name': n, 'position': pos, 'yaw': round(yaw, 4), 'pitch': pitch}
    c = list(cmds or [])
    if i == 0 and 'render hud off' not in c:
        c = ['render hud off'] + c
    if c:
        s['commands'] = c
    doc['shots'].append(s)
open(f'{_REPO_ROOT}/output/studio_cal/xd22/{name}.yml', 'w').write(yaml.safe_dump(doc, sort_keys=False))
print(len(doc['shots']), 'shots')
