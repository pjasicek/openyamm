import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, 'level_generation/creatures/claude_shared/floor')
from glb_pose import Glb, Model
m = Model(Glb('level_generation/creatures/mm9_ghoul_claude/source/g1/ghoul1_true.glb'))
names=[n.get('name') for n in m.glb.json['nodes']]
print([a for a in dir(m) if not a.startswith('__')])
w=m.world({})
for i,n in enumerate(names):
    if n and ('Bip' in n or 'Bone' in n) and ('Finger' not in n or n.endswith(('0','1','2')) ):
        print(i,n,np.round(w[i][:3,3],3))
print([a['name'] for a in m.glb.json['animations']])
