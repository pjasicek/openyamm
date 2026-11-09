import sys, numpy as np
sys.path.insert(0,'scripts')
from meshlib import section; from PIL import Image, ImageDraw
D=np.load('work/body1.npz'); P,T=D['co'],D['tri']
from loadglb import *
Hm,Th,_=load('meshy/head_v1/model_urls_glb.glb'); Hm,Th,_,_=weld(Hm,Th); nc,l=comps(len(Hm),Th); sz=np.bincount(l); Th=Th[(l==np.argmax(sz))[Th[:,0]]]
s=.53; a=np.radians(25.8); c,sn=np.cos(a),np.sin(a); Rx=np.array([[1,0,0],[0,c,-sn],[0,sn,c]])
hm=np.array([0,-.07,-.13]); ht=np.array([0,.285,.023])
Q=(Hm-hm)@Rx.T*s+ht
print('tip',((np.array([0,.23,.49])-hm)@Rx.T*s+ht).round(3), 'jaw tip',((np.array([0,-.3,.49])-hm)@Rx.T*s+ht).round(3),'cap back',((np.array([0,.2,-.5])-hm)@Rx.T*s+ht).round(3),((np.array([0,-.3,-.5])-hm)@Rx.T*s+ht).round(3))
np.savez('work/head_tmp.npz',co=Q,tri=Th)
im=Image.new('RGB',(4*520,2*520),(30,30,30)); d=ImageDraw.Draw(im)
n=np.array([0,.25,1.]); n/=np.linalg.norm(n)
for k,z in enumerate([-.22,-.17,-.12,-.07,-.02,.03,.08,.13]):
    ox,oy=(k%4)*520+260,(k//4)*520+260; p0=np.array([0,.35,z])
    u=np.array([1.,0,0]); v=np.cross(n,u)
    for M,TT,col in ((P,T,(255,255,0)),(Q,Th,(0,255,255))):
        for L in section(M,TT,p0,n):
            q=L['pts']-p0
            for pp in q: d.ellipse([ox+pp@u*420-1,oy-pp@v*420-1,ox+pp@u*420+1,oy-pp@v*420+1],fill=col)
    d.text((ox-250,oy-250),f'z={z}',fill=(255,255,255))
im.save('work/necksec.png')
