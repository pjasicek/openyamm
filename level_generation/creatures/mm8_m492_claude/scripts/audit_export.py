"""Validate final dragon geometry, animation, images and material contracts."""
import sys,json,io,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb
from build_actor_lods import accessor_bytes
D,B=read_glb(P/'export/mm8_m492.glb')
source,raw=read_glb(P/'export/mm8_m492_lods.glb')
assert D['nodes']==source['nodes'] and D['skins']==source['skins'] and D['animations']==source['animations']
geometry_hash=lambda doc,data:hashlib.sha256(b''.join(accessor_bytes(doc,data,i) for i in range(len(doc['accessors'])))).hexdigest()
assert geometry_hash(D,B)==geometry_hash(source,raw),'Material finishing changed geometry or animation'
def array(index):
 a=D['accessors'][index];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 return np.frombuffer(accessor_bytes(D,B,index),dtype=dtype).reshape(-1,cols)
node=next(n for n in D['nodes'] if n.get('name')=='Body');base=D['meshes'][node['mesh']];indices=[node['mesh']]+base['extras']['openyamm_lods'];shadows=base['extras']['openyamm_shadow_lods'];assert len(indices)==len(shadows)==4
counts=[]
for index in indices+shadows:
 mesh=D['meshes'][index];count=0
 for p in mesh['primitives']:
  count+=len(array(p['indices']))//3;attrs=p['attributes'];assert 'WEIGHTS_1' not in attrs
  w=array(attrs['WEIGHTS_0']);assert np.isfinite(w).all() and np.max(abs(w.sum(1)-1))<1e-4
  assert np.isfinite(array(attrs['POSITION'])).all()
 counts.append(count)
assert all(.35<a/b<.65 for a,b in zip(counts[1:4],counts[:3])),counts
clips={a['name']:a for a in D['animations']};assert set(clips)==set(['Standing','Walking','Running','Fidget','Attack','Cast','Hit','Death','Dead'])
assert not any(n.get('name')=='MouthFire' and 'mesh' in n for n in D['nodes']), 'User requested no death flame'
assert all('emissiveTexture' not in m and 'occlusionTexture' not in m for m in D['materials'])
fire_windows={}
for name,animation in clips.items():
 active=[]
 for channel in animation['channels']:
  target=channel['target'];n=D['nodes'][target['node']].get('name','')
  if n.startswith('MouthFire') and n[-1:].isdigit() and target['path']=='scale':
   sampler=animation['samplers'][channel['sampler']];assert sampler['interpolation']=='STEP';times=array(sampler['input']).ravel();values=array(sampler['output']);active.extend(times[(values>1e-3).any(1)].tolist())
 if active:
  raise AssertionError(('Unexpected flame controls',name,active))
  fire_windows[name]=[min(active),max(active)]
mat=next(m for m in D['materials'] if m.get('name')=='Dragon_M492')
assert mat['extras']['openyamm_specular_mask'] and mat['extras']['openyamm_specular']==1
sizes={}
for key,info in [('basecolor',mat['pbrMetallicRoughness']['baseColorTexture']),('normal',mat['normalTexture']),('metal_rough',mat['pbrMetallicRoughness']['metallicRoughnessTexture'])]:
 im=D['images'][D['textures'][info['index']]['source']];v=D['bufferViews'][im['bufferView']];a=Image.open(io.BytesIO(B[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]));sizes[key]=list(a.size);assert a.size==(6208,2048)
 if key=='metal_rough':assert np.array_equal(np.array(a)[...,:3],np.array(Image.open(P/'textures/dragon_metal_rough_2k.png'))[...,:3])
report={'body_triangles':counts[:4],'shadow_triangles':counts[4:],'mouth_fire_triangles':0,'clips':list(clips),'fire_windows':fire_windows,'images':sizes,'skin_influences':4,'geometry_animation_sha256':geometry_hash(D,B)}
(P/'work/final_export_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('FINAL_AUDIT',report)
