"""Discard collapsed, inverted tetrahedra in far LODs; never change LOD0 or a larger connected piece."""
from pathlib import Path
from collections import Counter
import importlib.util,sys,json,numpy as np
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor,compact
spec=importlib.util.spec_from_file_location('winding',ROOT/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
path=Path(sys.argv[1]);d,b=read_glb(path);b=bytearray(b);removed=[]
for mesh in d['meshes']:
 positions=[];triangles=[];owners=[];offset=0
 for pi,pr in enumerate(mesh['primitives']):
  mat=d['materials'][pr['material']]
  if mat.get('doubleSided') or mat.get('alphaMode')=='BLEND':continue
  pos=accessor_array(d,b,pr['attributes']['POSITION']).astype(float);ix=accessor_array(d,b,pr['indices']).reshape(-1,3)
  positions.extend(pos);triangles.extend(ix+offset);owners.extend((pi,i) for i in range(len(ix)));offset+=len(pos)
 if not triangles:continue
 pos=np.array(positions);tris=np.array(triangles);keys=[tuple(np.round(v,5)) for v in pos];drop={}
 for part in check.components(tris,keys):
  t=tris[part];edges=Counter(tuple(sorted((keys[face[i]],keys[face[(i+1)%3]]))) for face in t for i in range(3));a,bb,c=pos[t[:,0]],pos[t[:,1]],pos[t[:,2]];volume=float(np.einsum('ij,ij->i',a,np.cross(bb,c)).sum()/6)
  if all(n==2 for n in edges.values()) and volume<0:
   assert len(part)<=4 and any(x in mesh.get('name','') for x in ('LOD2','LOD3')),(path,mesh['name'],len(part),volume)
   for j in part:pi,fi=owners[j];drop.setdefault(pi,set()).add(fi)
   removed.append({'mesh':mesh['name'],'triangles':len(part),'signed_volume_m3':volume})
 for pi,indices in drop.items():
  pr=mesh['primitives'][pi];ix=accessor_array(d,b,pr['indices']).reshape(-1,3);keep=np.array([i not in indices for i in range(len(ix))]);assert keep.any()
  pr['indices']=append_accessor(d,b,ix[keep].astype(np.uint32).ravel(),{'componentType':5125,'type':'SCALAR'},34963)
write_glb(path,*compact(d,b));path.with_suffix('.winding.json').write_text(json.dumps(removed,indent=2)+'\n');print('FAR_WINDING',path,removed,flush=True)
assert check.check(path)==0
