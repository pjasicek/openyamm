"""Replace inherited normals only where decimation turned a face beyond them (copy of mm8_m608_codex/scripts/fix_lod_normals.py; usage: fix_lod_normals.py <glb>, in place)."""
from pathlib import Path
import sys,json,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor
path=Path(sys.argv[1]);d,raw=read_glb(path);b=bytearray(raw);report=[]
def values(i):
 a=d['accessors'][i];return np.frombuffer(accessor_bytes(d,b,i),dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]).reshape(a['count'],-1).copy()
for mesh in d['meshes']:
 if '_LOD' not in mesh['name']:continue
 for prim in mesh['primitives']:
  attrs=prim['attributes'];pos=values(attrs['POSITION']);norm=values(attrs['NORMAL']);indices=values(prim['indices']).reshape(-1,3);p=pos[indices];face=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);bad=np.flatnonzero(np.einsum('ij,ij->i',face,norm[indices].mean(axis=1)) < -1e-10)
  if not len(bad):continue
  owners=indices[bad].ravel();old_count=len(pos)
  for key,accessor in list(attrs.items()):
   data=values(accessor);extra=data[owners].copy()
   if key=='NORMAL':extra=np.repeat(face[bad]/np.linalg.norm(face[bad],axis=1)[:,None],3,axis=0)
   if key=='TANGENT':
    n=np.repeat(face[bad]/np.linalg.norm(face[bad],axis=1)[:,None],3,axis=0);t=extra[:,:3];t-=n*np.sum(t*n,axis=1)[:,None];length=np.linalg.norm(t,axis=1);assert np.all(length>1e-6);extra[:,:3]=t/length[:,None]
   a=dict(d['accessors'][accessor]);a['count']+=len(owners);attrs[key]=append_accessor(d,b,a,np.concatenate([data,extra]).astype(data.dtype).tobytes())
  indices[bad]=np.arange(old_count,old_count+len(owners)).reshape(-1,3);a=dict(d['accessors'][prim['indices']]);a['min']=[int(indices.min())];a['max']=[int(indices.max())];prim['indices']=append_accessor(d,b,a,indices.astype({5121:'u1',5123:'<u2',5125:'<u4'}[a['componentType']]).tobytes())
  report.append({'mesh':mesh['name'],'faces':len(bad)})
write_glb(path,d,b);(P/'work/lod_normal_repair.json').write_text(json.dumps(report,indent=2));print(report)
