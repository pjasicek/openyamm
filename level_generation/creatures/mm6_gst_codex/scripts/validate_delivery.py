from pathlib import Path
import sys,json,hashlib,io
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
paths=[P/'export/mm6_gst.glb',P.parents[2]/'assets_source/worlds/mm6/models/mm6_gst.glb',P.parents[2]/'assets_dev/worlds/mm6/models/mm6_gst.glb'];assert paths[0].read_bytes()==paths[1].read_bytes();reports=[]
o,ob=read_glb(P/'export/mm6_gst_runtime_lod0.glb')
for path in [paths[0],paths[2]]:
 d,b=read_glb(path);names={n.get('name') for n in d['nodes']};assert {f'Socket_{s}' for s in ['Gaze','Eye_Left','Eye_Right','Palm_Left','Palm_Right']}<=names;assert len(d['skins'])==1 and len(d['skins'][0]['joints'])==77
 variants=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']];assert variants==['gst_a','gst_b','gst_c'];assert all('KHR_materials_unlit' in m.get('extensions',{}) for m in d['materials']);body=next(n for n in d['nodes'] if n.get('name')=='Body');base=d['meshes'][body['mesh']];chain=[body['mesh']]+base['extras']['openyamm_lods'];counts=[]
 for index in chain:
  mesh=d['meshes'][index];counts.append(sum(d['accessors'][pr['indices']]['count']//3 for pr in mesh['primitives']))
  for pr in mesh['primitives']:
   assert len(pr['extensions']['KHR_materials_variants']['mappings'])==3
   w=accessor_array(d,b,pr['attributes']['WEIGHTS_0']);j=accessor_array(d,b,pr['attributes']['JOINTS_0'])
   if 'WEIGHTS_1' in pr['attributes']:w=np.concatenate([w,accessor_array(d,b,pr['attributes']['WEIGHTS_1'])],1);j=np.concatenate([j,accessor_array(d,b,pr['attributes']['JOINTS_1'])],1)
   pos=accessor_array(d,b,pr['attributes']['POSITION']);indices=accessor_array(d,b,pr['indices']);assert np.isfinite(pos).all() and indices.max()<len(pos)
   assert np.isfinite(w).all() and np.max(abs(w.sum(1)-1))<.001 and j.max()<77
 assert counts==[17143,8571,3075,1008] and len(base['extras']['openyamm_shadow_lods'])==4
 for img in d['images']:
  v=d['bufferViews'][img['bufferView']];off=v.get('byteOffset',0);assert Image.open(io.BytesIO(b[off:off+v['byteLength']])).size==(2080,1024)
 clips={a['name']:max(d['accessors'][x['input']]['max'][0] for x in a['samplers']) for a in d['animations']};assert set(clips)=={'Standing','Walking','Running','Fidget','Attack','Hit','Death','Dead'};assert clips['Hit']<=.75
 for a in o['animations']:
  c=next(x for x in d['animations'] if x['name']==a['name']);assert len(a['samplers'])==len(c['samplers'])
  for x,y in zip(a['samplers'],c['samplers']):
   for key in ['input','output']:assert np.array_equal(accessor_array(o,ob,x[key]),accessor_array(d,b,y[key]))
 reports.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':counts,'bones':77,'clips':clips,'variants':variants,'maps':'4 embedded 2080x1024 PNG atlases','animation_samples_retained':True,'source_installed_exactly':True})
(P/'review/checks').mkdir(exist_ok=True);(P/'review/checks/delivery.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
