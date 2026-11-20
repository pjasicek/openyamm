"""Keep coarse shadow casters inside the surface and preserve the explicit crystal specular mask."""
from pathlib import Path
import sys,io,json,numpy as np
from PIL import Image
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,accessor_bytes
from normal_map_convention import write_glb
path=P/'export/mm8_m548.glb';d,raw=read_glb(path);b=bytearray(raw)
node=next(n for n in d['nodes'] if n.get('name')=='CrystalDragon');mesh=d['meshes'][node['mesh']]
def array(i):return np.frombuffer(accessor_bytes(d,b,i),'<f4').reshape(-1,3).copy()
ref=mesh['primitives'][0];positions=array(ref['attributes']['POSITION']);normals=array(ref['attributes']['NORMAL'])
normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-8);tree=cKDTree(positions);report={}
for level,mi in enumerate(mesh['extras']['openyamm_shadow_lods'][1:],1):
 for prim in d['meshes'][mi]['primitives']:
  index=prim['attributes']['POSITION'];a=d['accessors'][index];v=d['bufferViews'][a['bufferView']];pos=array(index);_,nn=tree.query(pos)
  n=normals[nn];dist=np.sum((pos-positions[nn])*n,axis=1);push=np.clip(dist+[0,.002,.004,.006][level],0,.01);pos-=n*push[:,None]
  offset=v.get('byteOffset',0)+a.get('byteOffset',0);payload=pos.astype('<f4').tobytes();b[offset:offset+len(payload)]=payload
  a['min']=pos.min(0).tolist();a['max']=pos.max(0).tolist();report[level]={'moved_vertices':int((push>0).sum()),'max_push_m':float(push.max())}
views=[bytes(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]) for v in d['bufferViews']]
patched=set()
for mat in d['materials']:
 mat.pop('extensions',None)
 info=mat.get('pbrMetallicRoughness',{}).get('metallicRoughnessTexture')
 if not info:continue
 image=d['images'][d['textures'][info['index']]['source']];idx=image['bufferView']
 if idx in patched:continue
 im=np.array(Image.open(io.BytesIO(views[idx])).convert('RGB'));im[:,:,0]=220
 out=io.BytesIO();Image.fromarray(im).save(out,format='PNG');views[idx]=out.getvalue();image['mimeType']='image/png';patched.add(idx)
for key in ['extensionsUsed','extensionsRequired']:
 if key in d:
  d[key]=[s for s in d[key] if s!='KHR_materials_specular']
path.write_bytes(write_glb(d,views));(P/'work/shadow_correction.json').write_text(json.dumps(report,indent=2))
print('RUNTIME_FINISHED',path,flush=True)
