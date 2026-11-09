"""Orient inward closed parts, including matching shadow geometry; preserve positions, UVs and weights."""
import json,sys
from collections import Counter
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path[:0]=[str(R/'tools'),str(R/'level_generation/decorations/mm8_3d/animated/scripts')]
from check_winding import array,components,check
from build_actor_lods import read_glb,write_glb,append_accessor
src,dst=map(Path,sys.argv[1:]);d,b=read_glb(src);b=bytearray(b);report=[]
for mi,mesh in enumerate(d['meshes']):
 positions=[];normals=[];triangles=[];owners=[];offset=0
 for pi,p in enumerate(mesh['primitives']):
  if d['materials'][p['material']].get('doubleSided'):continue
  co=array(d,b,p['attributes']['POSITION']);ns=array(d,b,p['attributes']['NORMAL']);t=array(d,b,p['indices']).reshape(-1,3)
  positions.extend(co);normals.extend(ns);triangles.extend(t+offset);owners.extend((pi,i) for i in range(len(t)));offset+=len(co)
 if not triangles:continue
 co=np.array(positions,dtype=float);ns=np.array(normals);tris=np.array(triangles);keys=[tuple(np.round(v,5)) for v in co]
 changes={}; normal_changes={}
 for part in components(tris,keys):
  t=tris[part];edges=Counter(tuple(sorted((keys[a],keys[c]))) for a,c in np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]))
  volume=np.einsum('ij,ij->i',co[t[:,0]],np.cross(co[t[:,1]],co[t[:,2]])).sum()/6
  if not all(n==2 for n in edges.values()) or volume>=0:continue
  geometric=np.cross(co[t[:,1]]-co[t[:,0]],co[t[:,2]]-co[t[:,0]])
  alignment=float(np.einsum('ij,ij->i',geometric,ns[t].mean(1)).sum())
  for ti in part:
   pi,local=owners[ti];changes.setdefault(pi,[]).append(local)
   if alignment>0:
    p=mesh['primitives'][pi];local_tri=array(d,b,p['indices']).reshape(-1,3)[local]
    normal_changes.setdefault(pi,set()).update(int(v) for v in local_tri)
  report.append({'mesh_index':mi,'mesh':mesh['name'],'triangles':len(part),'old_volume':float(volume),'normal_alignment_before':alignment})
 for pi,rows in changes.items():
  p=mesh['primitives'][pi];a=d['accessors'][p['indices']];t=array(d,b,p['indices']).reshape(-1,3);t[rows]=t[rows][:,[0,2,1]]
  p['indices']=append_accessor(d,b,a,t.tobytes())
  if pi in normal_changes:
   ai=p['attributes']['NORMAL'];normals=array(d,b,ai);normals[list(normal_changes[pi])]*=-1
   p['attributes']['NORMAL']=append_accessor(d,b,d['accessors'][ai],normals.tobytes())
write_glb(dst,d,b);assert check(dst)==0
(P/'review/sentinel_winding_repair.json').write_text(json.dumps(report,indent=2)+'\n');print('REPAIRED',report)
