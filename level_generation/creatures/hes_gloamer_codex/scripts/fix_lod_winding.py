"""Correct closed components inverted by far-LOD collapse; preserve all vertex positions, weights and UVs."""
import sys,json,importlib.util
from pathlib import Path
from collections import defaultdict
import numpy as np
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor
spec=importlib.util.spec_from_file_location('winding',ROOT/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py');W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)
src,dst=map(Path,sys.argv[1:]);doc,buf=read_glb(src);report=[]
for mesh in doc['meshes']:
 for prim in mesh['primitives']:
  pos=accessor_array(doc,buf,prim['attributes']['POSITION']).astype(float);tri=accessor_array(doc,buf,prim['indices']).reshape(-1,3).copy();norm=accessor_array(doc,buf,prim['attributes']['NORMAL']).copy();keys=[tuple(np.round(v,5)) for v in pos];changed=False
  for ids in W.components(tri,keys):
   t=tri[ids];edges=defaultdict(int)
   for face in t:
    for j in range(3):edges[tuple(sorted((keys[face[j]],keys[face[(j+1)%3]])))]+=1
   a,b,c=pos[t[:,0]],pos[t[:,1]],pos[t[:,2]];volume=np.einsum('ij,ij->i',a,np.cross(b,c)).sum()/6
   if not all(v==2 for v in edges.values()) or volume>=0:continue
   assert 'LOD' in mesh['name'],'LOD0 must never need this correction'
   tri[ids]=t[:,[0,2,1]];changed=True
   # Recompute only this component's vertex normals from its corrected area-weighted faces.
   sums=defaultdict(lambda:np.zeros(3))
   for face in tri[ids]:
    a,b,c=pos[face];n=np.cross(b-a,c-a)
    for vi in face:sums[keys[vi]]+=n
   for vi in np.unique(t):
    n=sums[keys[vi]];length=np.linalg.norm(n)
    if length>1e-15:norm[vi]=n/length
   report.append({'mesh':mesh['name'],'triangles':len(ids),'negative_volume':float(volume)})
  if changed:
   prim['indices']=append_accessor(doc,buf,tri.reshape(-1,1),doc['accessors'][prim['indices']],34963)
   prim['attributes']['NORMAL']=append_accessor(doc,buf,norm,doc['accessors'][prim['attributes']['NORMAL']],34962)
write_glb(dst,doc,buf);assert W.check(dst)==0
(P/'review/lod_winding_corrections.json').write_text(json.dumps(report,indent=2)+'\n');print('CORRECTED',report)
