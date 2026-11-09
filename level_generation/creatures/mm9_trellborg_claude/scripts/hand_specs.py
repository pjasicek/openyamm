"""Hand cameras riding the hand joint. Args: <glb> <tier>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
m = Model(Glb(Path(sys.argv[1]))); nm = [n.get('name') for n in m.glb.json['nodes']]; w0 = m.world({})
for c, t in (('Running', .15), ('Walking', .25), ('AttackMelee', .3)):
    w = m.world(m.sample(c, t))
    for S, sg in (('R', 1), ('L', -1)):
        i = nm.index(f'Bip01 {S} Hand'); f = nm.index(f'Bip01 {S} Forearm'); R = w[i][:3, :3] @ np.linalg.inv(w0[i][:3, :3]); Rf = w[f][:3, :3] @ np.linalg.inv(w0[f][:3, :3]); p = w[i][:3, 3]
        for v, o in (('s', (-0.1 * sg, 0.25, 1)), ('b', (-1 * sg, 0.2, -0.25))):
            o = np.array(o, float); o = Rf @ (o / np.linalg.norm(o) * 0.95)
            print(f'{c}{S}{v}:{c}:{t}:front:body:' + ','.join(f'{x:.3f}' for x in p + o) + ':' + ','.join(f'{x:.3f}' for x in p))
