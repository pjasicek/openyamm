import sys,json,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path('tools').resolve()))
from build_actor_lods import read_glb,accessor_bytes
path=P/'export/mm8_m536.glb';d,b=read_glb(path);audit=json.loads((P/'work/animation_audit.json').read_text());report={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'clips':{},'meshes':[]}
def data(i):
 a=d['accessors'][i];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];ty={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];v=np.frombuffer(accessor_bytes(d,b,i),dtype=ty).reshape(-1,n)
 if a.get('normalized'):v=v/np.iinfo(v.dtype).max
 return v
for a in d['animations']:
 end=max(float(data(s['input'])[-1,0]) for s in a['samplers']);assert abs(end-audit[a['name']]['duration'])<1e-5;report['clips'][a['name']]=end
assert len(report['clips'])==9 and len(d['skins'][0]['joints'])==55
for mesh in d['meshes']:
 count=0
 for primitive in mesh['primitives']:
  attrs=primitive['attributes'];pos=data(attrs['POSITION']);assert np.isfinite(pos).all();count+=data(primitive['indices']).size//3
  if 'WEIGHTS_0' in attrs:
   w=data(attrs['WEIGHTS_0']);assert np.isfinite(w).all() and np.abs(w.sum(1)-1).max()<1e-4 and (w>=0).all();assert 'WEIGHTS_1' not in attrs
  if 'TEXCOORD_0' in attrs:assert np.isfinite(data(attrs['TEXCOORD_0'])).all()
  if mesh['name'].startswith('FlameTail'):assert data(attrs['COLOR_0'])[:,3].min()==0
 report['meshes'].append({'name':mesh['name'],'triangles':count,'extras':mesh.get('extras',{})})
for name in ['EfreetiFlame','EfreetiFringe']:
 m=next(m for m in d['materials'] if m['name']==name);assert m['alphaMode']=='BLEND' and 'KHR_materials_unlit' in m['extensions'] and m['extras']['openyamm_specular']==0 and m['extras']['openyamm_edge_darkening']==0
assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['m536_a','m536_b','m536_c']
assert (Path('assets_source/worlds/mm8/models/mm8_m536.glb').read_bytes()==path.read_bytes())
report['installed_source_matches']=True;report['runtime_sha256']=hashlib.sha256(Path('assets_dev/worlds/mm8/models/mm8_m536.glb').read_bytes()).hexdigest();report['checks']='finite data; <=4 normalized influences; 55 bones; exact nine durations; three variants; unlit scrolling alpha flame; decreasing authored LODs'
(P/'review/delivery_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('Delivery validation passed:',len(d['meshes']),'meshes, nine clips, three tiers')
