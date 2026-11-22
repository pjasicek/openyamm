"""G3 composition for the sprite: arm_rings.py's joints (Meshy axial joints, ring wrists, ring ankles) with
- the ELBOWS from Meshy's auto-rig moved onto the ring centreline (closest centreline point): the ring line fits put
  the elbow at 37-41 % of shoulder -> wrist (forearm longer than the upper arm), Meshy at about 47-50 %;
- the ANKLE height from Meshy (the narrowest leg ring lies 1-2 cm up the shin), x/y from the ring.
Rewrites work/joints_final.json (keeps the arm_rings version as joints_rings.json). Args: none"""
import json, os, shutil
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda *p: os.path.join(HERE, 'work', *p)
if not os.path.exists(W('joints_rings.json')):
    shutil.copy(W('joints_final.json'), W('joints_rings.json'))
R = json.load(open(W('joints_rings.json')))
M = json.load(open(W('meshy_joints.json')))['joints']
CL = json.load(open(W('centrelines.json')))
J = {k: np.array(v) for k, v in R['joints'].items()}
for s in ('R', 'L'):
    cs = np.array(CL[f'{s}_arm'])
    me = np.array(M[f'{s}_Forearm'])
    # densify the centreline and take the closest point to Meshy's elbow
    seg = np.concatenate([np.linspace(cs[i], cs[i + 1], 8, endpoint=False) for i in range(len(cs) - 1)])
    el = seg[np.argmin(np.linalg.norm(seg - me, axis=1))]
    sh, wr = J[f'{s}_UpperArm'], J[f'{s}_Hand']
    d = wr - sh
    J[f'{s}_Forearm'] = el
    J[f'{s}_Foot'][2] = M[f'{s}_Foot'][2]
    print('ELBOW', s, 't', round(float((el - sh) @ d / (d @ d)), 3), 'upper', round(float(np.linalg.norm(el - sh)), 3),
          'fore', round(float(np.linalg.norm(wr - el)), 3), 'off meshy cm', round(float(np.linalg.norm(el - me)) * 100, 1))
R['joints'] = {k: [round(float(x), 5) for x in v] for k, v in J.items()}
json.dump(R, open(W('joints_final.json'), 'w'), indent=1)
