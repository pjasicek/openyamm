"""MM9 club: axis, stations, in Blender true-handed axes, MM9 rest."""
import numpy as np, sys
from pygltflib import GLTF2
g=GLTF2().load('source/true/trellborg1_true.glb'); b=g.binary_blob()
def acc(i):
    a=g.accessors[i];bv=g.bufferViews[a.bufferView]
    n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a.type]; t={5126:'f4',5123:'u2',5125:'u4'}[a.componentType]
    return np.frombuffer(b,dtype=t,count=a.count*n,offset=(bv.byteOffset or 0)+(a.byteOffset or 0)).reshape(-1,n)
p=g.meshes[2].primitives[0]; P=acc(p.attributes.POSITION); P=np.c_[P[:,0],-P[:,2],P[:,1]]
UV=acc(p.attributes.TEXCOORD_0)
c=P.mean(0); U=np.linalg.svd(P-c)[2]; u=U[0]; 
if u[1]>0:u=-u
print('axis',u.round(3),'c',c.round(3),'U1',U[1].round(3),'U2',U[2].round(3))
t=(P-c)@u; v=P-c-np.outer(t,u); r=np.linalg.norm(v,axis=1)
print('t range',t.min().round(3),t.max().round(3))
for a in np.arange(t.min(),t.max()+.05,.06):
    m=abs(t-a)<.03
    if m.sum():
        q=(P[m]-c); print(round(a,3),int(m.sum()),'r med',np.median(r[m]).round(3),'max',r[m].max().round(3),'u1',(q@U[1]).min().round(3),(q@U[1]).max().round(3),'u2',(q@U[2]).min().round(3),(q@U[2]).max().round(3))
pts=np.array([-.583,-.126,-.308]); print('pivot t',((pts-c)@u).round(3),'r',np.linalg.norm(pts-c-u*((pts-c)@u)).round(3))
from PIL import Image, ImageDraw
idx=acc(p.indices).reshape(-1,3) if False else None
ai=g.accessors[p.indices]; bv=g.bufferViews[ai.bufferView]
T={5123:'u2',5125:'u4'}[ai.componentType]
I=np.frombuffer(b,dtype=T,count=ai.count,offset=(bv.byteOffset or 0)+(ai.byteOffset or 0)).reshape(-1,3)
S=700
for nm,e in (('u1',U[1]),('u2',U[2])):
    im=Image.new('RGB',(1000,500),(30,30,30)); d=ImageDraw.Draw(im)
    X=(t+.95)*S; Y=250-(P-c)@e*S
    for a_,b_,c_ in I:
        d.polygon([(X[a_],Y[a_]),(X[b_],Y[b_]),(X[c_],Y[c_])],outline=(230,200,120))
    im.save(f'work/v/club_{nm}.png')
