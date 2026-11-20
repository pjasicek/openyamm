"""Check the portable Phoenix's role, tier, skin, effect and LOD contracts."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,accessor_bytes
D,B=read_glb(P/'export/mm8_m572.glb')
def array(i):
 a=D['accessors'][i];dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];return np.frombuffer(accessor_bytes(D,B,i),dtype).reshape(-1,n)
clips={a['name']:a for a in D['animations']};assert set(clips)=={'Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'}
assert len(D['skins'][0]['joints'])==35
for mesh in D['meshes']:
 for p in mesh['primitives']:
  assert 'JOINTS_1' not in p['attributes']
  w=array(p['attributes']['WEIGHTS_0']);assert np.allclose(w.sum(1),1,atol=1e-4)
  assert array(p['attributes']['JOINTS_0']).max()<35
  for i in p['attributes'].values():assert np.isfinite(array(i)).all()
report={'sha256':hashlib.sha256((P/'export/mm8_m572.glb').read_bytes()).hexdigest(),'bones':35,'triangles':{},'clips':{}}
for name in ('Body','PhoenixFlames'):
 node=next(n for n in D['nodes'] if n.get('name')==name);mesh=D['meshes'][node['mesh']];levels=[node['mesh']]+mesh['extras']['openyamm_lods'];counts=[sum(D['accessors'][p['indices']]['count']//3 for p in D['meshes'][i]['primitives']) for i in levels];assert all(a>b for a,b in zip(counts,counts[1:]));report['triangles'][name]=counts
 if name=='Body':assert len(mesh['extras']['openyamm_shadow_lods'])==4
for name,a in clips.items():
 dur=max(float(array(s['input']).max()) for s in a['samplers']);report['clips'][name]=dur
 if name in ('Standing','Walking','Running','Fidget','Dead'):
  for c in a['channels']:
   v=array(a['samplers'][c['sampler']]['output']);assert np.max(np.abs(v[0]-v[-1]))<1e-5,(name,c['target'])
 if name in ('Death','Dead'):
  for c in a['channels']:
   if not D['nodes'][c['target']['node']].get('name','').startswith('Fire_') or c['target']['path']!='scale':continue
   values=array(a['samplers'][c['sampler']]['output']);assert (values[-1]<.00002).all()
for m in D['materials']:
 if m['name'] in ('Phoenix_A','Phoenix_B','Phoenix_C'):assert m['extras']['openyamm_specular_mask']
 else:
  assert m['alphaMode']=='BLEND' and m.get('doubleSided',False) and 'KHR_materials_unlit' in m['extensions'];assert m['extras']['openyamm_uv_scroll']==[0,0]
assert len(D['extensions']['KHR_materials_variants']['variants'])==3
(P/'work/export_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
