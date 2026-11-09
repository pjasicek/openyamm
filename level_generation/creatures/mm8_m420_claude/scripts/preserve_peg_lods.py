"""Keep the 160-triangle peg at every LOD: collapsing its UV seams samples neighbouring coat islands."""
import sys,copy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import accessor_array,append_accessor,read_glb,write_glb
D,B=read_glb(P/'export/mm8_m420_lods_raw.glb');B=bytearray(B);skin=D['skins'][0];joint=skin['joints'].index(next(i for i,n in enumerate(D['nodes']) if n.get('name')=='B_R_Calf'))
def peg(pr):
 pos=accessor_array(D,B,pr['attributes']['POSITION']);ids=accessor_array(D,B,pr['indices']).reshape(-1,3);j=accessor_array(D,B,pr['attributes']['JOINTS_0']);w=accessor_array(D,B,pr['attributes']['WEIGHTS_0']);full=((j==joint)&(w>.999)).any(1);candidate=full[ids].all(1)
 _,mapping=np.unique(np.round(pos*100000).astype(np.int64),axis=0,return_inverse=True);parent=list(range(mapping.max()+1))
 def root(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 for tri in ids[candidate]:
  a,b,c=map(lambda i:root(int(mapping[i])),tri);parent[b]=a;parent[c]=a
 groups={}
 for i in np.flatnonzero(candidate):groups.setdefault(root(int(mapping[ids[i,0]])),[]).append(i)
 selected=[]
 for group in groups.values():
  co=pos[np.unique(ids[group])]
  if co[:,1].min()<.025 and co[:,1].max()>.4:selected+=group
 assert selected,'Peg component missing'
 return ids,np.isin(np.arange(len(ids)),selected)
base=D['meshes'][0];pr=next(p for p in base['primitives'] if D['materials'][p['material']]['name']=='PirateMage_A');ids,mask=peg(pr);assert mask.sum()==160,mask.sum();used,idx=np.unique(ids[mask].ravel(),return_inverse=True);reference={n:accessor_array(D,B,a)[used].copy() for n,a in pr['attributes'].items()};idx=idx.reshape(-1,3)
for mi,mesh in enumerate(D['meshes']):
 if mi==0 or mesh['name']=='PirateMage_Shadow':continue
 pr=next(p for p in mesh['primitives'] if D['materials'][p['material']]['name']=='PirateMage_A');ids,mask=peg(pr);used,remap=np.unique(ids[~mask].ravel(),return_inverse=True);out=np.concatenate([remap.reshape(-1,3),idx+len(used)]).astype(np.uint32).ravel();attributes={}
 for n,a in pr['attributes'].items():
  values=np.concatenate([accessor_array(D,B,a)[used],reference[n]]);attributes[n]=append_accessor(D,B,values,D['accessors'][a],34962)
 pr['attributes']=attributes;pr['indices']=append_accessor(D,B,out,{'componentType':5125,'type':'SCALAR'},34963)
 print('PEG_LOD',mesh['name'],'replaced',int(mask.sum()),'with',len(idx),'triangles')
write_glb(P/'export/mm8_m420_lods_preserved.glb',D,B)
