from pathlib import Path
import sys,json,hashlib,numpy as np,yaml
sys.path.insert(0,str(Path('tools').resolve()));from build_actor_lods import read_glb,accessor_bytes
P=Path('level_generation/creatures/mm8_m556_claude');report={}
def array(d,b,i):
 a=d['accessors'][i];return np.frombuffer(accessor_bytes(d,b,i),dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]).reshape(a['count'],-1)
for name in ['mm8_m556','mm8_m556_sword','mm8_m556_shield']:
 f=P/f'export/{name}.glb';d,b=read_glb(f);mesh=next(n['mesh'] for n in d['nodes'] if 'mesh'in n);m=d['meshes'][mesh];lods=[mesh]+m.get('extras',{}).get('openyamm_lods',[]);counts=[]
 assert len(lods)==4,(name,lods)
 for i in lods:
  counts.append(sum(d['accessors'][x['indices']]['count']//3 for x in d['meshes'][i]['primitives']))
  for x in d['meshes'][i]['primitives']:
   a=x['attributes'];pos=array(d,b,a['POSITION']);assert np.isfinite(pos).all()
   assert array(d,b,x['indices']).max()<len(pos)
   if 'WEIGHTS_0'in a:
    w=array(d,b,a['WEIGHTS_0']);assert np.allclose(w.sum(1),1,atol=1e-4) and (w>=0).all()
 assert all(x>y>0 for x,y in zip(counts,counts[1:])),counts
 assert len(d['extensions']['KHR_materials_variants']['variants'])==3
 assert all('KHR_materials_specular' not in m.get('extensions',{}) for m in d['materials'])
 source=Path('assets_source/worlds/mm8/models')/f.name;runtime=Path('assets_dev/worlds/mm8/models')/f.name
 assert source.read_bytes()==f.read_bytes() and runtime.is_file()
 report[name]=dict(triangles=counts,source_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),cooked_sha256=hashlib.sha256(runtime.read_bytes()).hexdigest(),materials=len(d['materials']),images=len(d['images']))
 if name=='mm8_m556':
  durations={a['name']:max(float(array(d,b,s['input']).max()) for s in a['samplers']) for a in d['animations']};assert durations=={'Fly':.625,'FlyFast':.625,'Attack':1.25,'Hit':.625,'Fidget':.875,'Death':.875,'Dead':1.0};report[name]['clips']=durations;report[name]['bones']=len(d['skins'][0]['joints'])
rows=[r for r in yaml.safe_load(Path('assets_dev/worlds/mm8/models/actors.yml').read_text())['actors'] if r['descriptor'].startswith('Wasp Warrior ')];assert len(rows)==3 and len({r['scale'] for r in rows})==1
report['bindings']=rows
(P/'review/delivery_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v['triangles'] for k,v in report.items() if isinstance(v,dict)},indent=2))
