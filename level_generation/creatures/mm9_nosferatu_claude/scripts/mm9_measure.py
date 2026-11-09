"""MM9 head and arm measures in bone-local frames (Sphere05b only)."""
import sys, numpy as np
sys.path.insert(0,'level_generation/creatures/claude_shared/floor')
from glb_pose import Glb, Model
m=Model(Glb('level_generation/creatures/mm9_nosferatu_claude/source/n1/n1.glb'))
d=m.glb.json; nn=[n.get('name') for n in d['nodes']]
print(len(m.primitives), [k for k in m.primitives[0].keys()])
w0=m.world({})
jn=[nn[j] for j in m.joints]
for pi,pr in enumerate(m.primitives):
    if len(pr['positions'])!=1710: continue
    pos=np.asarray(pr['positions'],float); J=pr['joints'];W=pr['weights']
    # world bind positions
    head=jn.index('Bip01 Head')
    mask=(J[:,0]==head)&(W[:,0]>0.5)
    P=pos[mask]
    print('head verts',mask.sum(),'world bb',P.min(0).round(3),P.max(0).round(3))
    Wh=w0[nn.index('Bip01 Head')]
    print('Head world R\n',Wh[:3,:3].round(3),'\nt',Wh[:3,3].round(3))
    # principal symmetry: pair ear tips
    x=P-P.mean(0)
    # ear tips: extreme distance from centroid
    r=np.linalg.norm(x,axis=1); o=np.argsort(-r)[:6]; print('far',P[o].round(3))
    # nose/chin: max z (gltf forward +Z)
    i=np.argmax(P[:,2]);print('front',P[i].round(3)); print('lowest',P[np.argmin(P[:,1])].round(3));print('top',P[np.argmax(P[:,1])].round(3))
    np.save('level_generation/creatures/mm9_nosferatu_claude/work/mm9_head_pts.npy',P)
