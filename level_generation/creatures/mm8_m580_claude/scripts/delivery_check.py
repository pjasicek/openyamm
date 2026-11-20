from pathlib import Path
import sys,json,hashlib,numpy as np,yaml
sys.path.insert(0,str(Path('tools').resolve()));from build_actor_lods import read_glb,accessor_bytes
P=Path('level_generation/creatures/mm8_m580_claude')
def array(d,b,i):
 a=d['accessors'][i];return np.frombuffer(accessor_bytes(d,b,i),dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]).reshape(a['count'],-1)
f=P/'export/mm8_m580.glb';d,b=read_glb(f);node=next(n for n in d['nodes'] if n.get('name')=='Turtle');mi=node['mesh'];m=d['meshes'][mi];lods=[mi]+m['extras']['openyamm_lods'];counts=[]
assert len(lods)==4 and len(m['extras']['openyamm_shadow_lods'])==4
for i in lods+m['extras']['openyamm_shadow_lods']:
 if i in lods:counts.append(sum(d['accessors'][x['indices']]['count']//3 for x in d['meshes'][i]['primitives']))
 for x in d['meshes'][i]['primitives']:
  a=x['attributes'];pos=array(d,b,a['POSITION']);assert np.isfinite(pos).all();assert array(d,b,x['indices']).max()<len(pos)
  w=array(d,b,a['WEIGHTS_0']);assert np.allclose(w.sum(1),1,atol=1e-4) and (w>=0).all() and w.shape[1]==4
  n=array(d,b,a['NORMAL']);assert np.isfinite(n).all() and np.allclose(np.linalg.norm(n,axis=1),1,atol=.001)
assert all(x>y>0 for x,y in zip(counts,counts[1:])),counts
assert len(d['extensions']['KHR_materials_variants']['variants'])==3
for mat in d['materials']:
 assert mat['extras']['openyamm_specular']==0 and mat['pbrMetallicRoughness']['metallicFactor']==0
 assert 'openyamm_region_ramps' not in mat.get('extras',{}) or len(mat['extras']['openyamm_region_ramps'])==1
source=Path('assets_source/worlds/mm8/models')/f.name;runtime=Path('assets_dev/worlds/mm8/models')/f.name
assert source.read_bytes()==f.read_bytes() and runtime.is_file()
durations={a['name']:max(float(array(d,b,s['input']).max()) for s in a['samplers']) for a in d['animations']};expected={'SwimIdle':1,'Swim':1,'Bite':1.1,'Hit':.75,'Fidget':.5,'Death':.875,'Dead':1}
assert durations.keys()==expected.keys() and all(abs(durations[n]-v)<1e-6 for n,v in expected.items())
rows=[r for r in yaml.safe_load(Path('assets_dev/worlds/mm8/models/actors.yml').read_text())['actors'] if r['descriptor'].startswith('Dragon Turtle ')];assert len(rows)==3 and len({r['scale'] for r in rows})==1
report=dict(triangles=counts,source_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),cooked_sha256=hashlib.sha256(runtime.read_bytes()).hexdigest(),materials=len(d['materials']),images=len(d['images']),clips=durations,bones=len(d['skins'][0]['joints']),bindings=rows)
(P/'review/delivery_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='bindings'},indent=2))
