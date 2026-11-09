"""Retain the fine surface lighting on each reduced body/head/wing primitive."""
import sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path('tools').resolve()))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor
path=P/'export/mm6_gar_lods.glb';d,payload=read_glb(path);b=bytearray(payload)
def arr(i):
 a=d['accessors'][i];return np.frombuffer(accessor_bytes(d,payload,i),dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]).reshape(a['count'],-1)
node=next(n for n in d['nodes'] if n.get('name')=='Gargoyle');base=d['meshes'][node['mesh']];sources={}
for prim in base['primitives']:
 p=arr(prim['attributes']['POSITION']);n=arr(prim['attributes']['NORMAL']);f=arr(prim['indices']).reshape(-1,3)
 sources[prim['material']]=(BVHTree.FromPolygons(p,f,all_triangles=True),p,n,f)
for mi in base['extras']['openyamm_lods']:
 for prim in d['meshes'][mi]['primitives']:
  tree,p,n,f=sources[prim['material']];out=[]
  for position in arr(prim['attributes']['POSITION']):
   hit,_,fi,_=tree.find_nearest(Vector(position));ids=f[fi];normal=barycentric_transform(hit,*[Vector(v) for v in p[ids]],*[Vector(v) for v in n[ids]])
   assert normal.length>.1;out.append(normal.normalized())
  values=np.array(out,dtype='<f4');assert np.isfinite(values).all()
  old=prim['attributes']['NORMAL'];prim['attributes']['NORMAL']=append_accessor(d,b,d['accessors'][old],values.tobytes())
write_glb(path,d,b);print('LOD_NORMALS_PRESERVED',base['extras']['openyamm_lods'])
