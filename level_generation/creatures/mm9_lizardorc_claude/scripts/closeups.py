"""Joint-framed close-up specs; prints name:clip:t:view:body:cam:target for vshots.sh, one per line."""
import sys; sys.path.insert(0,'../claude_shared/floor')
from glb_pose import Glb, Model
import numpy as np
m=Model(Glb('review/viewer/liz_a.glb')); names=[n.get('name') for n in m.glb.json['nodes']]
J={'kneeL':('Bip01 L Calf',(.1,.4,1)),'kneeR':('Bip01 R Calf',(-.1,.4,1)),'groin':('Bip01 Pelvis',(0,-.5,1)),'armL':('Bip01 L UpperArm',(.7,-.7,.5)),'armR':('Bip01 R UpperArm',(-.7,-.7,.5)),'elbowL':('Bip01 L Forearm',(.3,.5,1)),'neck':('Bip01 Neck',(-.8,.3,.8)),'mouth':('Box01',(-.3,-.1,1))}
s=[]
for c,t in (('Death',.7),('Dead',.5),('Hit2',.5),('AttackMelee',.3),('Death2',.6)):
    w=m.world(m.sample(c,float(t)))
    for k,(j,d) in J.items():
        p=w[names.index(j)][:3,3]; d=np.array(d,float); d/=np.linalg.norm(d); cam=p+d*.75
        s.append(f"{k}_{c}:{c}:{t}:quarter:body:{cam[0]:.3f},{cam[1]:.3f},{cam[2]:.3f}:{p[0]:.3f},{p[1]:.3f},{p[2]:.3f}")
print(' '.join(s))
