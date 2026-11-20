"""Check unchanged motion, finite portable/runtime buffers, selected textures and the new UV allocation."""
import json,sys,hashlib,io
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];W=P/'work/parts_v5';sys.path.insert(0,str(Path('tools').resolve()))
from build_actor_lods import read_glb,accessor_bytes
old,ob=read_glb(W/'mm6_gar_lods.glb');new,nb=read_glb(P/'export/mm6_gar_lod0.glb')
def channels(d,b):
 out={}
 for a in d['animations']:
  values={}
  for c in a['channels']:
   s=a['samplers'][c['sampler']];key=(d['nodes'][c['target']['node']]['name'],c['target']['path'])
   values[key]=tuple(np.frombuffer(accessor_bytes(d,b,s[x]),'<f4') for x in ['input','output'])
  out[a['name']]=values
 return out
a=channels(old,ob);b=channels(new,nb);motion={};assert a.keys()==b.keys()
for clip in a:
 assert a[clip].keys()==b[clip].keys()
 delta=0
 for key in a[clip]:
  for x,y in zip(a[clip][key],b[clip][key]):
   assert x.shape==y.shape,(clip,key,x.shape,y.shape);delta=max(delta,float(np.abs(x-y).max()));assert np.allclose(x,y,rtol=0,atol=1e-5),(clip,key,delta)
 motion[clip]={'channels':len(a[clip]),'maximum_sample_difference':delta}
report={'animations':motion,'textures':{},'meshes':{}}
runtime=P/'export/mm6_gar.glb';installed=Path('assets_dev/worlds/mm6/models/mm6_gar.glb');assert runtime.read_bytes()==installed.read_bytes()
d,b=read_glb(runtime)
for i,accessor in enumerate(d['accessors']):
 if accessor['componentType']==5126:assert np.isfinite(np.frombuffer(accessor_bytes(d,b,i),'<f4')).all(),i
for m in d['materials']:
 p=m['pbrMetallicRoughness']
 for entry in [p['baseColorTexture'],p['metallicRoughnessTexture'],m['normalTexture']]:
  image=d['images'][d['textures'][entry['index']]['source']];v=d['bufferViews'][image['bufferView']];off=v.get('byteOffset',0);im=Image.open(io.BytesIO(b[off:off+v['byteLength']]))
  assert im.size==(1024,1024),(m['name'],im.size)
 report['textures'][m['name']]='1024x1024'
for name in ['Gargoyle','Rubble']:
 node=next(n for n in d['nodes'] if n.get('name')==name);mesh=d['meshes'][node['mesh']]
 ids=[node['mesh']]+mesh['extras']['openyamm_lods'];counts=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives']) for i in ids]
 assert all(x>y for x,y in zip(counts,counts[1:]));report['meshes'][name]=counts
assert sum(new['accessors'][p['indices']]['count']//3 for p in new['meshes'][0]['primitives'])==7247
report['authored_triangles']=7247
assert 7247<=report['meshes']['Gargoyle'][0]<7300
report['sha256']=hashlib.sha256(runtime.read_bytes()).hexdigest()
for part in ['body','wings']:
 z=np.load(W/(part+'_uv3d.npz'));uv=z['uv'];du=uv[:,1:]-uv[:,:1];dx=z['xyz'][:,1:]-z['xyz'][:,:1];area=np.linalg.norm(np.cross(dx[:,0],dx[:,1]),axis=1)*.5
 length=np.linalg.norm(dx[:,0],axis=1);x=(dx[:,0]*dx[:,1]).sum(1)/np.maximum(length,1e-12);y=np.sqrt(np.maximum((dx[:,1]**2).sum(1)-x*x,1e-20));valid=area>1e-10
 basis=np.zeros((len(x),2,2));basis[:,0,0]=length;basis[:,1,0]=x;basis[:,1,1]=y
 sv=np.linalg.svd(np.linalg.solve(basis[valid],du[valid]),compute_uv=False);stretch=sv[:,0]/np.maximum(sv[:,1],1e-10)
 assert np.percentile(stretch,95)<1.6
 report.setdefault('uv',{})[part]={'stretch_p95':float(np.percentile(stretch,95)),'area_fraction':float(abs(du[:,0,0]*du[:,1,1]-du[:,0,1]*du[:,1,0]).sum()/2)}
(W/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
