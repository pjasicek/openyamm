"""Hand against sleeve, every clip at 24 fps: nearest distance from each hand's vertices to the same side's sleeve and cuff (they overlap at the wrist, so 0 up to vertex spacing), and how far the wrist joint is from the sleeve's end ring. Args: glb"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
hand = np.array([n.startswith('Finger') or n.startswith('Zhand') or n.startswith('Zfing') for n in names])
worst = {}
for pi, pr in enumerate(m.primitives):
    dom = pr['joints'][np.arange(len(pr['joints'])), pr['weights'].argmax(1)]
    if not hand[dom].any():
        continue
    hv = hand[dom]; sv = ~hv
    for c in [a['name'] for a in doc['animations'] if a['name'] not in ('Dead',)]:
        for t in np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 24):
            P = m.skinned_positions(m.world(m.sample(c, float(t))))[pi][0]
            d = cKDTree(P[sv]).query(P[hv])[0].min()
            k = (pi, c)
            if d > worst.get(k, (0, 0))[0]:
                worst[k] = (float(d), float(t))
for k, v in worst.items():
    print(k, 'closest hand-to-sleeve distance, worst frame %.1f mm at %.2f s' % (v[0] * 1000, v[1]))
