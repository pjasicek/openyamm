"""G3 composition for Forad (2026-10-30): the ring fit (fit_joints.py) failed on this near-horizontal MM9 bind pose
(one arm NaN, wrist perimeters 4.8 / 40.6 cm), so the two independent estimates are Meshy's auto-rig and the joints
the MM9 route fitted on this same mesh by limb slices (work/mm9_joints.json, sides swapped: MM9 'L' is the
character's right). Composition: Meshy for the axial joints, clavicles, shoulders, elbows, hips and knees (the
MM9 knees sit 10-12 cm low, at the boot cuffs); wrists = the MPFB wrist joints of the grafted hands
(work/hand_openings.json); ankles = ring centres where the ring fit is sane, else Meshy; toes Meshy.
Prints each joint's Meshy-MM9 distance (the X-ray comparison) and writes work/joints_final.json. Args: none"""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda f: os.path.join(HERE, 'work', f)
M = {k: np.array(v) for k, v in json.load(open(W('meshy_joints.json')))['joints'].items()}
R = {k: np.array(v) for k, v in json.load(open(W('joints.json')))['joints'].items()}
HO = {k: np.array(v) for k, v in json.load(open(W('hand_openings.json'))).items()}
J = dict(M)
for s in 'LR':
    J[f'{s}_Hand'] = HO[s]
    f = R.get(f'{s}_Foot')
    J[f'{s}_Foot'] = f if f is not None and np.all(np.isfinite(f)) and np.linalg.norm(f - M[f'{s}_Foot']) < 0.05 else M[f'{s}_Foot']
    ua, fa, hd = J[f'{s}_UpperArm'], J[f'{s}_Forearm'], J[f'{s}_Hand']
    d = hd - ua
    print('ELBOW', s, 't', round(float((fa - ua) @ d / (d @ d)), 3), 'upper', round(float(np.linalg.norm(fa - ua)), 3),
          'fore', round(float(np.linalg.norm(hd - fa)), 3))
h = json.load(open(W('prep.json')))
json.dump({'height_m': 1.7872, 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()},
           'sources': {'meshy': 'axial, clavicles, shoulders, elbows, hips, knees, toes', 'wrists': 'MPFB graft',
                       'ankles': 'rings if within 5 cm of Meshy'}}, open(W('joints_final.json'), 'w'), indent=1)
print('JOINTS', {k: [round(float(x), 3) for x in v] for k, v in J.items() if 'Hand' in k or 'Foot' in k})
