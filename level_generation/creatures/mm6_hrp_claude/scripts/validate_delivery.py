"""Check the installed Harpy, separate PBR sets, LODs, variants and untouched animation streams."""
from pathlib import Path
import sys,json,hashlib,io
import numpy as np
from PIL import Image
P=Path('level_generation/creatures/mm6_hrp_claude').resolve()
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
paths=[P/'export/mm6_hrp.glb',P.parents[2]/'assets_dev/worlds/mm6/models/mm6_hrp.glb']
assert paths[0].read_bytes()==paths[1].read_bytes()
d,b=read_glb(paths[0]);names={n.get('name') for n in d['nodes']}
assert {f'Socket_{s}' for s in ['Gaze','Eye_Left','Eye_Right','Palm_Left','Palm_Right']}<=names
assert len(d['skins'])==1 and len(d['skins'][0]['joints'])==59
variants=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]
assert variants==['hrp_a','hrp_b','hrp_c']
body=next(n for n in d['nodes'] if n.get('name')=='Body');base=d['meshes'][body['mesh']]
chain=[body['mesh']]+base['extras']['openyamm_lods'];counts=[];primitive_counts=[]
for i in chain:
 m=d['meshes'][i];primitive_counts.append(len(m['primitives']));assert len(m['primitives'])==3
 counts.append(sum(d['accessors'][p['indices']]['count']//3 for p in m['primitives']))
 images=set()
 for pr in m['primitives']:
  material=d['materials'][pr['material']];images.add(d['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']]['source'])
  w=accessor_array(d,b,pr['attributes']['WEIGHTS_0']);j=accessor_array(d,b,pr['attributes']['JOINTS_0'])
  if 'WEIGHTS_1' in pr['attributes']:
   w=np.concatenate([w,accessor_array(d,b,pr['attributes']['WEIGHTS_1'])],axis=1)
   j=np.concatenate([j,accessor_array(d,b,pr['attributes']['JOINTS_1'])],axis=1)
  assert w.shape[1]<=8
  if i==chain[0]:assert (w>1e-5).sum(1).max()<=4
  assert np.isfinite(w).all() and np.max(abs(w.sum(1)-1))<.001 and j.max()<59
 assert len(images)==3
assert len(chain)==4 and all(a>c for a,c in zip(counts,counts[1:]))
assert len(base['extras']['openyamm_shadow_lods'])==4
for img in d['images']:
 v=d['bufferViews'][img['bufferView']];off=v.get('byteOffset',0)
 assert Image.open(io.BytesIO(b[off:off+v['byteLength']])).size==(1024,1024)
clips={a['name']:max(d['accessors'][x['input']]['max'][0] for x in a['samplers']) for a in d['animations']}
expected={'Standing':1.125,'Walking':1.125,'Running':.875,'Fidget':2.25,'Attack':1.75,'Cast':1.625,'Hit':1.125,'Death':1.875,'Dead':1}
assert clips==expected,(clips,expected)
o,ob=read_glb(P/'export/mm6_hrp_runtime_lod0.glb')
for a in o['animations']:
 c=next(x for x in d['animations'] if x['name']==a['name']);assert len(a['samplers'])==len(c['samplers'])
 for x,y in zip(a['samplers'],c['samplers']):
  for key in ['input','output']:assert np.array_equal(accessor_array(o,ob,x[key]),accessor_array(d,b,y[key]))
r={'runtime_sha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),'runtime_bytes':paths[0].stat().st_size,'triangles':counts,'colour_primitives_per_lod':primitive_counts,'bones':59,'clips':clips,'variants':variants,'embedded_images':len(d['images']),'maps':'Three independent 1024x1024 PBR sets plus two region masks','animation_samples_retained':True,'installed_identical':True}
(P/'review/checks/delivery.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
