import sys, numpy as np
from pygltflib import GLTF2
g=GLTF2().load(sys.argv[1])
def mat(n):
    M=np.eye(4)
    if n.matrix: return np.array(n.matrix).reshape(4,4).T
    t=n.translation or [0,0,0]; r=n.rotation or [0,0,0,1]; s=n.scale or [1,1,1]
    x,y,z,w=r
    R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    M[:3,:3]=R*np.array(s); M[:3,3]=t; return M
W={}
def walk(i,P):
    W[i]=P@mat(g.nodes[i]); 
    for c in g.nodes[i].children or []: walk(c,W[i])
for r in g.scenes[0].nodes: walk(r,np.eye(4))
for i,n in enumerate(g.nodes):
    print(i,n.name,np.round(W[i][:3,3],3).tolist(), [g.nodes[c].name for c in n.children or []][:4])
print(g.skins[0].skeleton, len(g.skins[0].joints))
sk=g.skins[0]
a=g.accessors[sk.inverseBindMatrices]; bv=g.bufferViews[a.bufferView]
blob=g.binary_blob()
ib=np.frombuffer(blob,'f4',a.count*16,(bv.byteOffset or 0)+(a.byteOffset or 0)).reshape(-1,4,4).transpose(0,2,1)
for k,j in enumerate(sk.joints):
    B=np.linalg.inv(ib[k]); n=g.nodes[j].name
    d=np.linalg.norm(B[:3,3]-W[j][:3,3]); 
    if any(s in n for s in ['Pelvis','Spine','Head','Box0','L Hand','R Hand','Foot','Forearm','Neck','Calf']): print(n,np.round(B[:3,3],3).tolist(),'node d',round(d,3))
