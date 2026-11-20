from pathlib import Path
import sys,json,hashlib,io
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from merge_head_material import read_glb,accessor_array
source=P/'export/mm6_drg1.glb';installed=P.parents[2]/'assets_dev/worlds/mm6/models/mm6_drg1.glb';authoritative=P.parents[2]/'assets_source/worlds/mm6/models/mm6_drg1.glb';assert source.read_bytes()==authoritative.read_bytes()
d,b=read_glb(source);rd,rb=read_glb(installed);o,ob=read_glb(P/'export/mm6_drg1_runtime_lod0.glb');names={n.get('name') for n in d['nodes']};assert {'Socket_Mouth','Jaw','Tail9','LWing0','RWing0','Remains'}<=names
assert len(d['skins'])==1;nj=len(d['skins'][0]['joints']);assert nj==101,nj
variants=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']];assert variants==['drg1_a','drg1_b','drg1_c']
counts=[];body=next(n for n in d['nodes'] if n.get('name')=='Body');base=d['meshes'][body['mesh']];chain=[body['mesh']]+base['extras']['openyamm_lods'];assert len(base['extras']['openyamm_shadow_lods'])==4
for i in chain:
 m=d['meshes'][i];assert len(m['primitives'])==4;counts.append(sum(d['accessors'][p['indices']]['count']//3 for p in m['primitives']))
 for p in m['primitives']:
  w=accessor_array(d,b,p['attributes']['WEIGHTS_0']);j=accessor_array(d,b,p['attributes']['JOINTS_0'])
  if 'WEIGHTS_1' in p['attributes']:w=np.concatenate([w,accessor_array(d,b,p['attributes']['WEIGHTS_1'])],axis=1);j=np.concatenate([j,accessor_array(d,b,p['attributes']['JOINTS_1'])],axis=1)
  assert np.isfinite(w).all() and np.max(abs(w.sum(1)-1))<.001 and j.max()<nj
assert counts[0]==15292 and all(a>b for a,b in zip(counts,counts[1:])),counts
for img in d['images']:
 v=d['bufferViews'][img['bufferView']];off=v.get('byteOffset',0);assert Image.open(io.BytesIO(b[off:off+v['byteLength']])).size in [(2048,2048),(512,1024)]
fire=next(m for m in d['materials'] if m['name']=='DrakeDeathFlames');assert fire['alphaMode']=='BLEND' and 'KHR_materials_unlit' in fire['extensions'];assert fire.get('emissiveFactor',[0,0,0])==[0,0,0]
fxnode=next(n for n in d['nodes'] if n.get('name')=='DeathFlames');fxtris=sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][fxnode['mesh']]['primitives']);assert fxtris==896
clips={a['name']:max(d['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in d['animations']};assert set(clips)=={'Standing','Walking','Running','Fidget','Attack','Cast','Hit','Death','Dead'};assert clips['Hit']<=.9375
for a in o['animations']:
 for target,binary in [(d,b),(rd,rb)]:
  c=next(x for x in target['animations'] if x['name']==a['name']);assert len(a['samplers'])==len(c['samplers'])
  for x,y in zip(a['samplers'],c['samplers']):
   for key in ['input','output']:assert np.array_equal(accessor_array(o,ob,x[key]),accessor_array(target,binary,y[key]))
rbody=next(n for n in rd['nodes'] if n.get('name')=='Body');rm=rd['meshes'][rbody['mesh']];runtime_counts=[sum(rd['accessors'][p['indices']]['count']//3 for p in rd['meshes'][i]['primitives']) for i in [rbody['mesh']]+rm['extras']['openyamm_lods']]
r={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'runtime_sha256':hashlib.sha256(installed.read_bytes()).hexdigest(),'triangles':counts,'runtime_triangles_including_backface_copies':runtime_counts,'bones':nj,'death_effect_triangles':fxtris,'total_authored_lod0_triangles':counts[0]+fxtris,'clips':clips,'variants':variants,'maps':'3 independent 2K PBR sets + 3 shared region masks; separate animated flame atlas','animation_samples_retained_in_installed_asset':True,'runtime_processing':'tools/install_model.py thin backface separation'}
(P/'review/delivery.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
