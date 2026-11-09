"""G3 composition for the m470 ghoul: Meshy's auto-rig joints (work/meshy_joints.json) everywhere, the wrists from the
skin ring fit (arm_rings.py: within 1 cm of Meshy's). The ring line fits for the elbows came out degenerate (NaN) on
this thin arm and the narrowest ankle ring sat 4.5 cm above Meshy's ankle (up the shin), so Meshy keeps both.
Writes work/joints_final.json. Args: none"""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(HERE, 'work', 'joints_final.json')))
M = json.load(open(os.path.join(HERE, 'work', 'meshy_joints.json')))['joints']
J = {k: list(v) for k, v in M.items()}
for s in 'LR':
    J[f'{s}_Hand'] = R['joints'][f'{s}_Hand']
for a in ('UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot'):
    l, r = np.array(J[f'L_{a}']), np.array(J[f'R_{a}'])
    print('SYM', a, np.round(l, 3).tolist(), np.round(r, 3).tolist(), 'mirror diff cm', round(float(np.linalg.norm(l - r * np.array([-1, 1, 1]))) * 100, 1))
json.dump({'height_m': R['height_m'], 'joints': J}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
