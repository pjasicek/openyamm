"""G3 composition for m504: Meshy's auto-rig joints everywhere. The skin ring fits (arm_rings.py) failed on this
body: the left arm's rings merged with the torso (NaN elbow) and the huge fist and forearm have no narrow wrist ring
(R wrist 4.6 cm from Meshy's on a 77 cm perimeter). The X-ray (review/joints_xray_*) checks Meshy's joints inside
the limbs. Writes work/joints_final.json. Args: none"""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(os.path.join(HERE, 'work', 'meshy_joints.json')))['joints']
J = {k: list(v) for k, v in M.items()}
for a in ('UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot'):
    l, r = np.array(J[f'L_{a}']), np.array(J[f'R_{a}'])
    print('SYM', a, np.round(l, 3).tolist(), np.round(r, 3).tolist(), 'mirror diff cm', round(float(np.linalg.norm(l - r * np.array([-1, 1, 1]))) * 100, 1))
json.dump({'height_m': 2.0, 'joints': J}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
