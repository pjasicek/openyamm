import sys, numpy as np
from pygltflib import GLTF2
g=GLTF2().load(sys.argv[1]); blob=g.binary_blob()
def acc(i):
    a=g.accessors[i]; bv=g.bufferViews[a.bufferView]
    n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a.type]; ct={5126:'f4',5123:'u2',5125:'u4',5121:'u1'}[a.componentType]
    return np.frombuffer(blob,ct,a.count*n,(bv.byteOffset or 0)+(a.byteOffset or 0)).reshape(a.count,n)
p=g.meshes[0].primitives[0]; P=acc(p.attributes.POSITION); J=acc(p.attributes.JOINTS_0); W=acc(p.attributes.WEIGHTS_0)
names=[g.nodes[j].name for j in g.skins[0].joints]
dom=J[np.arange(len(J)),W.argmax(1)]
for i,n in enumerate(names):
    m=dom==i
    if m.sum(): print(n,m.sum(),np.round(P[m].min(0),3).tolist(),np.round(P[m].max(0),3).tolist())
print('multi-weight verts',(W>0.01).sum(1).max(), ((W>0.01).sum(1)>1).sum())
