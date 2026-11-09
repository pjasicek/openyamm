import hashlib,io,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
P=Path('level_generation/creatures/mm6_pman_claude_20261013')
def load(p):
 raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[n+28:]
def acc(d,b,i):
 a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dt=np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);off=v.get('byteOffset',0)+a.get('byteOffset',0)
 return np.ndarray((a['count'],n),dtype=dt,buffer=b,offset=off,strides=(v.get('byteStride',n*dt.itemsize),dt.itemsize)).copy()
def channels(d,b):
 out={}
 for a in d['animations']:
  for c in a['channels']:
   s=a['samplers'][c['sampler']];k=(a['name'],d['nodes'][c['target']['node']]['name'],c['target']['path']);out[k]=(s.get('interpolation','LINEAR'),acc(d,b,s['input']),acc(d,b,s['output']))
 return out
path=P/'export/mm6_pman_v2.glb';d,b=load(path);old,ob=load(P/'work/before_feedback_v1/mm6_pman_v2.glb');ch=channels(d,b);och=channels(old,ob);assert ch.keys()==och.keys()
for k,v in ch.items():
 assert v[0]==och[k][0] and np.array_equal(v[1],och[k][1]) and np.array_equal(v[2],och[k][2]),k
report={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'meshes':[],'clip_durations':{},'texture_sizes':[],'unchanged_animation_channels':len(ch)}
for m in d['meshes']:
 tris=0;inf=0
 for p in m['primitives']:
  tris+=d['accessors'][p['indices']]['count']//3;attrs=p['attributes'];ww=[acc(d,b,i) for k,i in attrs.items() if k.startswith('WEIGHTS_')];w=np.concatenate(ww,axis=1);assert np.max(abs(w.sum(1)-1))<1e-5;inf=max(inf,int((w>1e-6).sum(1).max()));assert inf<=8
 report['meshes'].append({'name':m['name'],'triangles':tris,'primitives':len(m['primitives']),'max_influences':inf})
for a in d['animations']:report['clip_durations'][a['name']]=max(float(acc(d,b,s['input']).max()) for s in a['samplers'])
assert set(report['clip_durations'])=={'Standing','Walking','Hit','Fidget','Death','Dead'}
for im in d['images']:
 v=d['bufferViews'][im['bufferView']];i=Image.open(io.BytesIO(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]));assert i.size==(2080,1024);report['texture_sizes'].append({'name':im.get('name'),'size':i.size,'mode':i.mode})
(P/'checks/final_structure.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
