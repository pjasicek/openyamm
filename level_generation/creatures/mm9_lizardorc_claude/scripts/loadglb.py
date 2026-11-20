"""Plain mesh read of a Meshy GLB (positions in Blender frame x,-z,y), tri list, components."""
import numpy as np, sys
from pygltflib import GLTF2
def load(path):
    g=GLTF2().load(path); blob=g.binary_blob()
    def acc(i):
        a=g.accessors[i]; bv=g.bufferViews[a.bufferView]
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a.type]; ct={5126:'f4',5123:'u2',5125:'u4',5121:'u1'}[a.componentType]
        return np.frombuffer(blob,ct,a.count*n,(bv.byteOffset or 0)+(a.byteOffset or 0)).reshape(a.count,n).copy()
    p=g.meshes[0].primitives[0]
    P=acc(p.attributes.POSITION).astype(float); T=acc(p.indices).reshape(-1,3).astype(int)
    UV=acc(p.attributes.TEXCOORD_0) if p.attributes.TEXCOORD_0 is not None else None
    return P,T,UV
def weld(P,T,eps=1e-5):
    k=np.round(P/eps).astype(np.int64); _,idx,inv=np.unique(k,axis=0,return_index=True,return_inverse=True); inv=inv.ravel()
    return P[idx],inv[T],idx,inv
def comps(n,T):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    e=np.vstack([T[:,[0,1]],T[:,[1,2]]]); G=coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(n,n))
    return connected_components(G,directed=False)
