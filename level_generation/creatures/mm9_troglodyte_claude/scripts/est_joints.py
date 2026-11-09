"""Joint estimates on work/body0.npz by ring centroids (left side). Prints JSON-ish; saved to work/src_joints.json. Frame: glTF, not shifted."""
import sys, json, numpy as np
sys.path.insert(0,'scripts')
from meshlib import *
D=np.load('work/body0.npz'); P,T=D['co'],D['tri']
def ring(p,n):
    p=np.array(p,float); n=np.array(n,float); n/=np.linalg.norm(n)
    L=section(P,T,p,n); l=nearest_loop(L,p); return l['c'],l['per']
for name,p,n in [('sh',(.15,.385,-.0),(.5,-.6,-.6)),('b1',(.2,.3,-.07),(.5,-.6,-.6)),('b2',(.24,.22,-.145),(.5,-.6,-.6)),('el',(.29,.17,-.2),(.3,-.8,0.)),('f1',(.31,.08,-.17),(.04,-.25,.22)),('f2',(.32,0,-.1),(.04,-.25,.22)),('f3',(.335,-.06,-.05),(.04,-.25,.22)),('f4',(.34,-.09,-.03),(.04,-.25,.22)),('f5',(.345,-.11,-.0),(.04,-.25,.22)),
   ('th1',(.14,0,-.15),(.35,-.6,.5)),('th2',(.2,-.1,-.08),(.35,-.6,.5)),('kn',(.235,-.21,-.03),(0,-1,0)),('sh1',(.235,-.3,-.13),(0,-.7,-.6)),('sh2',(.23,-.4,-.2),(0,-.7,-.6)),('an',(.23,-.46,-.24),(0,-1,-.1)),
   ('t0',(0,-.05,-.26),(0,1,0)),('t1',(0,-.2,-.23),(0,1,0)),('t2',(0,-.38,-.19),(0,1,0)),('t3',(0,-.5,-.17),(0,1,0))]:
    c,per=ring(p,n); print(name,np.round(c,3).tolist(),round(per,3))
# foot
m=(P[:,1]<-.5)&(P[:,0]>0); Q=P[m]; print('foot bbox',Q.min(0).round(3),Q.max(0).round(3))
hand=(P[:,1]<-.05)&(P[:,0]>.28); Q=P[hand]
for a in np.arange(-.12,-.40,-.04):
    print(round(a,2),[ (np.round(l['c'],3).tolist(),round(l['per'],3)) for l in section(P,T,np.array([0,a,0]),np.array([0,1.,0])) if l['c'][0]>.27])
