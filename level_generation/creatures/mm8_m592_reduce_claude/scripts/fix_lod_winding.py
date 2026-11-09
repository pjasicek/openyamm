"""Repair any closed shells inverted by LOD collapse or shadow inset."""
import sys,numpy as np
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).parent));from shrink_shadow_lods import read_glb,write_glb,view
repo=Path(__file__).resolve().parents[4];sys.path.insert(0,str(repo/'level_generation/decorations/mm8_3d/animated/scripts'));from check_winding import components
path=Path(sys.argv[1]);doc,binary=read_glb(path);fixed=[]
for mesh in doc['meshes']:
 for prim in mesh['primitives']:
  pos,_=view(doc,binary,prim['attributes']['POSITION']);nrm,_=view(doc,binary,prim['attributes']['NORMAL']);ind,_=view(doc,binary,prim['indices']);tris=ind.reshape(-1,3);keys=[tuple(np.round(q,5)) for q in pos]
  for comp in components(tris,keys):
   tri=tris[comp];edges=Counter(tuple(sorted((keys[t[i]],keys[t[(i+1)%3]]))) for t in tri for i in range(3))
   if not all(n==2 for n in edges.values()):continue
   a,b,c=pos[tri[:,0]],pos[tri[:,1]],pos[tri[:,2]];vol=float(np.einsum('ij,ij->i',a,np.cross(b,c)).sum())/6
   if vol>=0:continue
   assert 'LOD' in mesh['name'],'LOD0 winding must be corrected in the editable master'
   tris[comp]=tri[:,[0,2,1]]
   new=tris[comp];normals=np.zeros_like(nrm)
   cross=np.cross(pos[new[:,1]]-pos[new[:,0]],pos[new[:,2]]-pos[new[:,0]])
   for i in range(3):np.add.at(normals,new[:,i],cross)
   ids=np.unique(new);flip=np.einsum('ij,ij->i',nrm[ids],normals[ids])<0;nrm[ids[flip]]*=-1
   fixed.append({'mesh':mesh['name'],'triangles':len(comp),'old_volume':vol})
write_glb(path,doc,binary);print('LOD winding repairs',fixed)
