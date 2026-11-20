import sys,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
O=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');R=O.parent
sys.path.insert(0,str(R/'blender_rebuild_20260928/authoring'));from check_glb import Glb
up=O/'work/body_for_texture_v1.glb';ret=R/'meshy/body_texture_v1/model_urls_glb.glb'
def inspect(path):
 g=Glb(path);vertices=defaultdict(list);triangles=Counter();count=0
 for m in g.json['meshes']:
  for p in m['primitives']:
   v=g.accessor(p['attributes']['POSITION']);uv=g.accessor(p['attributes']['TEXCOORD_0']);keys=[tuple(round(a,6) for a in t) for t in uv]
   for k,xyz in zip(keys,v):vertices[k].append(xyz)
   ids=[t[0] for t in g.accessor(p['indices'])]
   for i in range(0,len(ids),3):
    face=tuple(keys[j] for j in ids[i:i+3]);triangles[min(face[j:]+face[:j] for j in range(3))]+=1;count+=1
 return vertices,triangles,count
s,st,sc=inspect(up);d,dt,dc=inspect(ret);assert s.keys()==d.keys();assert st==dt,('per-corner UV triangles changed',len(st),len(dt));assert sc==dc==13773
keys=sorted(s);x=np.array([s[k][0] for k in keys]);y=np.array([d[k][0] for k in keys]);scales=[];offsets=[]
for axis in range(3):
 scale,offset=np.linalg.lstsq(np.column_stack([x[:,axis],np.ones(len(x))]),y[:,axis],rcond=None)[0];scales.append(float(scale));offsets.append(float(offset))
residual=float(np.abs(y-x*np.array(scales)-np.array(offsets)).max());assert residual<1e-6,(residual,'non-affine geometry change')
report={'static_upload':str(up.relative_to(R)),'static_upload_sha256':hashlib.sha256(up.read_bytes()).hexdigest(),'meshy_return':str(ret.relative_to(R)),'meshy_return_sha256':hashlib.sha256(ret.read_bytes()).hexdigest(),'body_triangles':sc,'unique_uv_keys':len(keys),'per_corner_uv_triangle_multisets_equal':True,'returned_static_transform_gltf_axes':{'scale_xyz':scales,'translation_xyz_m':offsets,'maximum_affine_residual_m':residual},'decision':'Transfer downloaded PNG maps to the retained animated body; do not use Meshy normalized static geometry','uv_padding_fraction':.004,'uv_padding_pixels_at_4096':16.384,'uv_notes':'139 initial overlap pairs exposed 88 folded faces; locally planar repairs followed by 0.004 repacking; final validation has no unintended overlap or degenerate UV triangles','pbr_conventions':{'base_color':'sRGB PNG 4096','normal':'Non-Color tangent OpenGL PNG 4096, strength 0.65','roughness':'Non-Color PNG 2048','metallic':'Non-Color PNG 2048; force zero for skin/leather/teeth/eyes','body_uv_set':'Goblin_Atlas_4K'},'maps':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'meshy/body_texture_v1').glob('texture_urls_*.png')}}
(O/'review/texture_transfer.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
