"""Retain the accepted far geometry byte-for-byte after the shared texture atlas rebuild."""
import copy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,append_accessor,accessor_bytes
from merge_head_material import compact,accessor_array
old,ob=read_glb(P/'review/triangle_reduction/baseline/export/mm6_lch.glb');doc,b=read_glb(P/'export/mm6_lch.glb');b=bytearray(b)
assert old['nodes']==doc['nodes']
rects=json.loads((P/'review/triangle_rebake/texture_layout.json').read_text())['rectangles_lower_left']
for mi in [2,3,6,7]:
 mesh=copy.deepcopy(old['meshes'][mi])
 for prim in mesh['primitives']:
  for semantic,idx in list(prim['attributes'].items()):
   packed=accessor_bytes(old,ob,idx)
   if semantic=='TEXCOORD_0' and mi in [2,3]:
    uv=accessor_array(old,ob,idx);head=uv[:,0]>.5;x,y,w,h=rects[mi]
    local=(uv[:,0]*2080-head*1056)/1024;uv[:,0]=(x+local*w+head*1056)/2080;uv[:,1]=(1024-y-h+uv[:,1]*h)/1024
    packed=uv.astype('<f4').tobytes()
   prim['attributes'][semantic]=append_accessor(doc,b,old['accessors'][idx],packed)
  idx=prim['indices'];prim['indices']=append_accessor(doc,b,old['accessors'][idx],accessor_bytes(old,ob,idx))
 doc['meshes'][mi]=mesh
 doc['meshes'][mi]['name']=old['meshes'][mi]['name']
doc,b=compact(doc,b);write_glb(P/'export/mm6_lch.glb',doc,b)
print('Accepted LOD2/3 and corresponding shadow positions, normals, weights and indices retained; UVs mapped into shared LOD bake tiles')
