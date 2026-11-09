"""where.py <glb> clip t joint...: world position of joints, viewer frame"""
import sys; sys.path.insert(0,'../claude_shared/floor')
from glb_pose import Glb, Model
import numpy as np
m=Model(Glb(sys.argv[1])); names=[n.get('name') for n in m.glb.json['nodes']]
w=m.world(m.sample(sys.argv[2],float(sys.argv[3])))
for j in sys.argv[4:]:
    print(j, np.round(w[names.index(j)][:3,3],3).tolist())
