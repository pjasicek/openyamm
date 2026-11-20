import sys
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb
g=Glb('source/g1/ghoul1_true.glb'); j=g.json
m=j['meshes'][0]['primitives'][0]
p=g.accessor(m['attributes']['POSITION']); jn=g.accessor(m['attributes']['JOINTS_0']).astype(int); wt=g.accessor(m['attributes']['WEIGHTS_0'])
sk=j['skins'][0]['joints']; names=[j['nodes'][i].get('name') for i in sk]
hd=names.index('Bip01 Head'); s=((jn==hd)&(wt>0.5)).any(1)
P=np.c_[p[:,0],-p[:,2],p[:,1]]  # blender
H=P[s]
print('head bbox',H.min(0),H.max(0))
f=H[H[:,1]<-0.05]; print('front verts',f.min(0),f.max(0))
print('chin', H[np.argmin(H[:,2])]); 
nt=H[np.argmin(H[:,1])]; print('nose/front tip',nt)
ear=H[np.abs(H[:,0])>0.13]; print('ear',ear.min(0),ear.max(0), 'n',len(ear))
ct=H[np.abs(H[:,0])<0.1]; print('crown',ct[np.argmax(ct[:,2])])
hairb=H[H[:,1]>0.05]; print('back of head verts min z',hairb.min(0),hairb.max(0))
