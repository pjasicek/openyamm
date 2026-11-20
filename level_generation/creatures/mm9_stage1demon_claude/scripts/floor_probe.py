"""Per frame of a clip: lowest point of each foot (vertices weighted mostly to that side's foot/toe bones), the lowest point
overall and its bone. Args: glb clip [fps]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); clip = sys.argv[2]; fps = float(sys.argv[3]) if len(sys.argv) > 3 else 30
doc = m.glb.json; names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
PR = m.primitives
J = np.vstack([p['joints'] for p in PR]); W = np.vstack([p['weights'] for p in PR])
dom = np.array([names[J[i, np.argmax(W[i])]] for i in range(len(J))])
side = {s: np.array([(f'{s} Foot' in d or f'{s} Toe' in d) for d in dom]) for s in 'LR'}
T = m.clip_times(clip)[-1]
for t in np.arange(0, T + 1e-6, 1 / fps):
    P = np.vstack([x[0] for x in m.skinned_positions(m.world(m.sample(clip, float(t))))])
    y = P[:, 1]; k = int(np.argmin(y))
    print(f'{t:5.2f} L {y[side["L"]].min()*100:6.1f} R {y[side["R"]].min()*100:6.1f} lowest {y[k]*100:6.1f} {dom[k]}')
