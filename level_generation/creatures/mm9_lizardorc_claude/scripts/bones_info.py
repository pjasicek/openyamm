import sys, numpy as np, json
from pygltflib import GLTF2
import struct
g=GLTF2().load(sys.argv[1]); blob=g.binary_blob()
def acc(i):
    a=g.accessors[i]; bv=g.bufferViews[a.bufferView]
    n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a.type]
    dt={5123:np.uint16,5121:np.uint8,5126:np.float32,5125:np.uint32}[a.componentType]
    o=(bv.byteOffset or 0)+(a.byteOffset or 0)
    st=bv.byteStride or n*np.dtype(dt).itemsize
    if st==n*np.dtype(dt).itemsize: return np.frombuffer(blob,dt,a.count*n,o).reshape(a.count,n)
    return np.stack([np.frombuffer(blob,dt,n,o+st*k) for k in range(a.count)])
sk=g.skins[0]; names=[g.nodes[j].name for j in sk.joints]
P=g.meshes[0].primitives[0]
pos=acc(P.attributes.POSITION); J=acc(P.attributes.JOINTS_0); W=acc(P.attributes.WEIGHTS_0)
cnt={}
for j,w in zip(J.flat,W.flat):
    if w>0.01: cnt[int(j)]=cnt.get(int(j),0)+1
for j,c in sorted(cnt.items()): print(names[j],c)
print('---rot range per clip for head bones')
idx={n.name:i for i,n in enumerate(g.nodes)}
for bn in ['Box01','Box02','Bone02','Bone03','Bone04','Bone05','Bone07','Bip01 Head','Box03','Bip01 R Finger1','Bip01 R Finger0']:
    i=idx[bn]; out=[]
    for a in g.animations:
        for c in a.channels:
            if c.target.node==i and c.target.path=='rotation':
                q=acc(a.samplers[c.sampler].output)
                d=np.degrees(2*np.arccos(np.clip(np.abs((q*q[0]).sum(1)),0,1))).max() if len(q) else 0
                out.append(f'{a.name}:{d:.0f}')
    print(bn,' '.join(out))
