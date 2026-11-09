"""Elbows inside wide bell sleeves: the sleeve's ring centreline sags below the arm and Meshy's estimate sits 5 cm off,
together a 65 deg rest bend and a 14 cm upper arm (arm_rings.py). The A-pose arm in the HD masters is nearly
straight, so each elbow goes on the shoulder -> wrist line at the human upper-arm share UPPER (0.54), moved BACK cm
behind the line (a slight natural bend that fixes the hinge plane). Edits work/joints_final.json in place."""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(HERE, 'work', 'joints_final.json')
d = json.load(open(p)); J = d['joints']
UPPER, BACK = float(os.environ.get('UPPER', '0.54')), float(os.environ.get('BACK', '0.012'))
for s in ('L', 'R'):
    sh, wr = np.array(J[f'{s}_UpperArm']), np.array(J[f'{s}_Hand'])
    el = sh + (wr - sh) * UPPER + np.array([0.0, BACK, 0.0])
    old = np.array(J[f'{s}_Forearm'])
    J[f'{s}_Forearm'] = [round(float(x), 5) for x in el]
    d.setdefault('report', {}).setdefault(s, {})['elbow_fix'] = {'from': old.round(4).tolist(), 'moved_cm': round(float(np.linalg.norm(el - old)) * 100, 1),
                                                               'upper_m': round(float(np.linalg.norm(el - sh)), 3), 'fore_m': round(float(np.linalg.norm(wr - el)), 3)}
    print('ELBOWFIX', s, d['report'][s]['elbow_fix'])
json.dump(d, open(p, 'w'), indent=1)
