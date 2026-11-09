"""Triton: Meshy axial/leg estimates; skin-centred wrists and elbows. Ring leg extrema follow the long fins."""
import json
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent.parent / 'work'
M = json.loads((W/'meshy_joints.json').read_text())['joints']
R = json.loads((W/'joints.json').read_text())['joints']
CL = json.loads((W/'centrelines.json').read_text())
J = {k: np.array(v) for k,v in M.items()}
report = {}
for side in ('L','R'):
    sh = J[f'{side}_UpperArm']
    wr = np.array(R[f'{side}_Hand'])
    d = wr-sh; length = np.linalg.norm(d); d /= length
    cs = np.array(CL[f'{side}_arm']); t = (cs-sh)@d/length
    tm = (J[f'{side}_Forearm']-sh)@d/length
    order = np.argsort(t)
    el = np.array([np.interp(tm,t[order],cs[order,k]) for k in range(3)])
    assert .35 < tm < .65
    J[f'{side}_Forearm'] = el
    J[f'{side}_Hand'] = wr
    report[side] = {'elbow_t':float(tm), 'upper_m':float(np.linalg.norm(el-sh)), 'forearm_m':float(np.linalg.norm(wr-el))}
    print('JOINT COMPOSITION',side,report[side],flush=True)
(W/'joints_final.json').write_text(json.dumps({'height_m':1.7,'joints':{k:v.tolist() for k,v in J.items()},'report':report},indent=2))
