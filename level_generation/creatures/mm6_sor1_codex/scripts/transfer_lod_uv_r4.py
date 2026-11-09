"""Carry every lower face into one LOD0 chart, preventing interpolation between unrelated atlas islands."""
from pathlib import Path
import numpy as np,json
from scipy.spatial import cKDTree
from bake_atlas_r4 import nearest
p=Path(__file__).resolve().parents[1];hi=np.load(p/'work/atlas_uv_r4.npz');hv,hf,hu,hp,hc=[hi[k] for k in ['vertices','faces','uv','part','chart']];tri=hv[hf];parts=hp[hf[:,0]]
parttrees={pt:(np.where(parts==pt)[0],cKDTree(tri[parts==pt].mean(1))) for pt in set(parts)}
charts={c:(np.where(hc==c)[0],cKDTree(tri[hc==c].mean(1))) for c in set(hc)}
np.savez_compressed(p/'work/uv_final_lod0_r4.npz',**{k:hi[k] for k in hi.files})
for level in range(1,4):
 d=np.load(p/'work'/f'uv_lod{level}_r4.npz');v,f,part=[d[k] for k in ['vertices','faces','part']];uv=np.empty((len(f),3,2));ch=np.empty(len(f),int)
 for i,face in enumerate(f):
  pt=int(part[face[0]]);ids,tree=parttrees[pt];point=v[face].mean(0);_,near=tree.query(point,k=min(24,len(ids)));candidates=ids[np.atleast_1d(near)];w,dist=nearest(np.broadcast_to(point,(len(candidates),3)),tri[candidates]);source=candidates[dist.argmin()];chart=int(hc[source]);ids,tree=charts[chart]
  _,near=tree.query(v[face],k=min(24,len(ids)));near=np.asarray(near).reshape(3,-1);candidates=ids[near];w,dist=nearest(v[face][:,None,:],tri[candidates]);best=dist.argmin(1);source=candidates[np.arange(3),best];uv[i]=(hu[source]*w[np.arange(3),best,:,None]).sum(1);ch[i]=chart
 assert np.isfinite(uv).all() and uv.min()>=0 and uv.max()<=1
 np.savez_compressed(p/'work'/f'uv_final_lod{level}_r4.npz',uv=uv,faces=f,vertices=v,part=part,chart=ch);print('LOD',level,'UVs transferred',len(f),flush=True)
