import sys; sys.path.insert(0,'scripts')
import numpy as np, mm9_joints
from pygltflib import GLTF2
g=GLTF2().load('source/true/lizardorc_true.glb'); blob=g.binary_blob()
def acc(i):
    a=g.accessors[i]; bv=g.bufferViews[a.bufferView]
    n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a.type]; ct={5126:'f4',5123:'u2',5125:'u4',5121:'u1'}[a.componentType]
    return np.frombuffer(blob,ct,a.count*n,(bv.byteOffset or 0)+(a.byteOffset or 0)).reshape(a.count,n).copy()
m=g.meshes[1].primitives[0]; P=acc(m.attributes.POSITION); T=acc(m.indices).reshape(-1,3); UV=acc(m.attributes.TEXCOORD_0)
J=acc(m.attributes.JOINTS_0); W=acc(m.attributes.WEIGHTS_0); sk=g.skins[0]
print('joint', {g.nodes[sk.joints[int(j)]].name for j in np.unique(J[W>0])})
Wm,par,_=mm9_joints.rest()
print('R hand', Wm['Bip01 R Hand'][:3,3], 'Bone07', Wm['Bone07'][:3,3])
L=(np.linalg.inv(Wm['Bip01 R Hand'])@np.c_[P,np.ones(len(P))].T).T[:,:3]
print('local bbox', L.min(0).round(3), L.max(0).round(3))
C,S,V=None,None,None
u,s,vt=np.linalg.svd(P-P.mean(0)); print('pca', s.round(2), vt.round(3))
ax=vt[0]; a=(P-P.mean(0))@ax
o=np.argsort(a)
for k in np.linspace(0,1,20):
    lo=a.min()+(a.max()-a.min())*k; m_=np.abs(a-lo)<.04
    if m_.any(): print(round(float(lo),3), m_.sum(), P[m_].mean(0).round(3), np.ptp(P[m_],0).round(3))
np.savez('work/cutlass.npz',P=P,T=T,UV=UV)
