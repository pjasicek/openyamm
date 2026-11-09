"""The neck loft's last row against the torso ring it was stitched to: at rest they coincide, so any distance in a pose is a real crack. Args: <glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
from scipy.spatial import cKDTree
g = Glb(sys.argv[1]); m = Model(g); doc = g.json
mesh = next(x for x in doc['meshes'] if x['name'] == 'Banshee')
nm = [doc['materials'][p['material']]['name'].rsplit('_', 1)[0] for p in mesh['primitives']]
print(nm)
R = m.skinned_positions(m.world({}))
k_n = nm.index('BansheeNeck') if 'BansheeNeck' in nm else nm.index('BansheeHead')
k_t = nm.index('Banshee')
dd, ii = cKDTree(R[k_t][0]).query(R[k_n][0])
pair = np.where(dd < 0.007)[0]
print('pairs', len(pair))
worst = 0
for a in doc['animations']:
    c = a['name']; wc = 0; wt = 0
    for t in np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 8):
        P = m.skinned_positions(m.world(m.sample(c, float(t))))
        e = np.linalg.norm(P[k_n][0][pair] - P[k_t][0][ii[pair]], axis=1).max()
        if e > wc:
            wc, wt = e, round(float(t), 2)
    print(f'{c}:{wc:.3f}@{wt}', end=' ')
    worst = max(worst, wc)
print('\nNECK GAP worst', round(float(worst), 4))
