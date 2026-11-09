"""Check the actual installed package and preserve its delivery receipt."""
from pathlib import Path
import sys,json,hashlib,io
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
paths=[P/'export/mm6_djn.glb',P.parents[2]/'assets_dev/worlds/mm6/models/mm6_djn.glb']
assert paths[0].read_bytes()==paths[1].read_bytes()
d,b=read_glb(paths[0]);names={n.get('name') for n in d['nodes']}
assert {f'Socket_{s}' for s in ['Gaze','Eye_Left','Eye_Right','Palm_Left','Palm_Right']}<=names
assert len(d['skins'])==1 and len(d['skins'][0]['joints'])==60
variants=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]
assert variants==['djn_a','djn_b','djn_c'] and len(d['materials'])>=3
body=next(n for n in d['nodes'] if n.get('name')=='Body');base=d['meshes'][body['mesh']];chain=[body['mesh']]+base['extras']['openyamm_lods'];counts=[]
for i in chain:
 m=d['meshes'][i];assert len(m['primitives'])==1
 pr=m['primitives'][0];counts.append(d['accessors'][pr['indices']]['count']//3)
 assert len(pr['extensions']['KHR_materials_variants']['mappings'])==3
 w=accessor_array(d,b,pr['attributes']['WEIGHTS_0']);j=accessor_array(d,b,pr['attributes']['JOINTS_0'])
 if 'WEIGHTS_1' in pr['attributes']:
  w=np.concatenate([w,accessor_array(d,b,pr['attributes']['WEIGHTS_1'])],axis=1)
  j=np.concatenate([j,accessor_array(d,b,pr['attributes']['JOINTS_1'])],axis=1)
 assert np.isfinite(w).all() and np.max(abs(w.sum(1)-1))<.001 and j.max()<60
assert 12063<=counts[0]<12500 and all(a>b for a,b in zip(counts,counts[1:]))
assert len(base['extras']['openyamm_shadow_lods'])==4
for img in d['images']:
 v=d['bufferViews'][img['bufferView']];off=v.get('byteOffset',0)
 assert Image.open(io.BytesIO(b[off:off+v['byteLength']])).size==(2080,1024)
clips={a['name']:max(d['accessors'][x['input']]['max'][0] for x in a['samplers']) for a in d['animations']}
assert set(clips)=={'Standing','Walking','Running','Fidget','Attack','Cast','Hit','Death','Dead'}
assert clips['Hit']<=.75 and clips['Attack']>.75 and clips['Cast']>.75
# Post-processes must retain every exported animation sample, including sockets.
o,ob=read_glb(P/'export/mm6_djn_runtime_lod0.glb')
for a in o['animations']:
 c=next(x for x in d['animations'] if x['name']==a['name']);assert len(a['samplers'])==len(c['samplers'])
 for x,y in zip(a['samplers'],c['samplers']):
  for key in ['input','output']:assert np.array_equal(accessor_array(o,ob,x[key]),accessor_array(d,b,y[key]))
r={'runtime_sha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),'triangles':counts,'bones':60,'clips':clips,'variants':variants,'maps':'4 embedded 2080x1024 PNG atlases','animation_samples_retained':True,'installed_identical':True}
(P/'review/checks/delivery.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
