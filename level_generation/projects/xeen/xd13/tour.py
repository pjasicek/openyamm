"""Writes output/studio_cal/xd13/<name>.yml: tour.py <name> (stage 0, then stage 2, then stage 3 by console)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys, math, yaml
name = sys.argv[1]
P = math.pi
H = ['render hud off']
K = ['qbit set 111221', 'event 31']
D = ['qbit set 111441', 'event 30', 'qbit set 111461', 'event 39']
ALL = [
    ('s0_gate_north', [0, 150, 0], P / 2, 0.05, H),
    ('s0_gate_west', [200, 384, 0], P, 0.1, None),
    ('s0_gate_south', [0, 650, 0], -P / 2, 0.05, None),
    ('s0_hall_south', [0, 1000, 0], P / 2, 0.15, None),
    ('s0_hall_roof', [0, 1700, 0], P / 2, 0.8, None),
    ('s0_hall_hole', [-150, 1150, 0], 2.4, -0.45, None),
    ('s0_hall_north', [200, 1500, 0], 1.9, 0.1, None),
    ('s0_hall_east', [-700, 1728, 0], 0.0, 0.05, None),
    ('s0_pantry_w', [-1450, 2900, 0], P, 0.0, None),
    ('s0_pantry_n', [-2048, 2700, 0], P / 2, 0.0, None),
    ('s0_court', [1450, 1000, 0], 0.8, 0.05, None),
    ('s0_court_north', [2176, 1050, 0], P / 2, 0.1, None),
    ('s0_court_east', [1500, 1856, 0], 0.0, 0.05, None),
    ('s0_court_south', [2528, 2400, 0], -P / 2, 0.0, None),
    ('s0_stair_rubble', [2528, 720, 0], -P / 2, -0.25, None),
    ('s0_pit', [-1550, 1400, -640], 0.3, 0.1, None),
    ('s0_pit_up', [-704, 1250, -640], P / 2, 0.9, None),
    ('s0_ramp', [-1900, 1408, -620], P, 0.05, None),
    ('s0_ramp_up', [-2560, 1500, -380], P / 2, 0.2, None),
    ('s2_hall_south', [0, 1000, 0], P / 2, 0.15, K),
    ('s2_hall_roof', [0, 1700, 0], P / 2, 0.8, None),
    ('s2_hall_floor', [-150, 1150, 0], 2.4, -0.45, None),
    ('s2_gate_east', [-200, 384, 0], 0.0, 0.1, None),
    ('s2_gate_west', [200, 384, 0], P, 0.1, None),
    ('s2_court_east', [1500, 1856, 0], 0.0, 0.05, None),
    ('s2_pantry_ramp', [-2560, 3000, 0], -P / 2, 0.0, None),
    ('s3_court_north', [2176, 1050, 0], P / 2, 0.1, D),
    ('s3_court_well', [2300, 1600, 0], -0.8, -0.2, None),
    ('s3_stair', [2528, 700, 0], -P / 2, -0.3, None),
    ('s3_dstair', [2528, -150, -330], -P / 2, -0.2, None),
    ('s3_cellar', [2528, -1250, -640], -P / 2, 0.0, None),
    ('s3_cellar_w', [3150, -1900, -640], P, 0.0, None),
    ('s3_lab', [1550, -1900, -640], P, 0.0, None),
    ('s3_lab_n', [960, -2250, -640], P / 2, 0.05, None),
    ('s3_vaultdoor', [60, -1920, -640], P, 0.05, None),
    ('s3_vault', [-1000, -1920, -640], P, 0.05, None),
    ('s3_vault_rack', [-1216, -2250, -640], P / 2, 0.1, None),
]
import os
PICK = os.environ.get('PICK')
shots = [x for x in ALL if not PICK or x[0] in PICK.split(',') or x[4] in (K, D)]
doc = {'output_dir': f'{_REPO_ROOT}/output/studio_cal/xd13/{name}', 'exit': True,
       'settle_seconds': 1.5, 'shots': []}
for n, pos, yaw, pitch, cmds in shots:
    s = {'name': n, 'position': pos, 'yaw': round(yaw, 4), 'pitch': pitch}
    if cmds:
        s['commands'] = cmds
    doc['shots'].append(s)
open(f'{_REPO_ROOT}/output/studio_cal/xd13/{name}.yml', 'w').write(yaml.safe_dump(doc, sort_keys=False))
