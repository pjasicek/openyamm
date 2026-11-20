import sys; from pathlib import Path
import numpy as np
sys.path.insert(0,'/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/floor')
from glb_pose import Glb, Model
m=Model(Glb(sys.argv[1])); doc=m.glb.json
for a in doc['animations']:
    n=a['name']; ts=m.glb.accessor(a['samplers'][0]['input'])[:,0]
    lows=[]; 
    for t in np.linspace(ts[0],ts[-1],9):
        W=m.world(m.sample(n,float(t))); P=np.asarray(m.skinned_positions(W)[0][0]).reshape(-1,3); lows.append(P[:,1].min())
    print(n,round(ts[-1],2),np.round(lows,3).tolist(), 'max',round(float(P[:,1].max()),3))
