"""Validate the split creature, palette tiers, animation roles and attachment LODs."""
from pathlib import Path
import argparse,json,struct,hashlib,io
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parents[1];repo=p.parents[2];parser=argparse.ArgumentParser();parser.add_argument('--installed',action='store_true');args=parser.parse_args();report={}
def read(f):
 raw=f.read_bytes();magic,version,length=struct.unpack_from('<III',raw);assert (magic,version,length)==(0x46546c67,2,len(raw));n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:]
def acc(d,b,i):
 a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',dt.itemsize*w);assert off+(a['count']-1)*stride+dt.itemsize*w<=len(b);return np.ndarray((a['count'],w),dtype=dt,buffer=b,offset=off,strides=(stride,dt.itemsize))
for suffix in ['', '_club']:
 f=p/f'export/mm8_m480{suffix}.glb';d,b=read(f);body=not suffix;node=next(n for n in d['nodes'] if 'mesh' in n);base=d['meshes'][node['mesh']];lods=[node['mesh']]+base['extras']['openyamm_lods'];assert len(lods)==4;counts=[]
 for m in d['meshes']:
  for pr in m['primitives']:
   a=pr['attributes'];pos=acc(d,b,a['POSITION']);assert np.isfinite(pos).all();assert acc(d,b,pr['indices']).max()<len(pos)
   if body:
    assert 'WEIGHTS_1' not in a;w=acc(d,b,a['WEIGHTS_0']);assert np.max(np.abs(w.sum(1)-1))<1e-4;assert acc(d,b,a['JOINTS_0']).max()<len(d['skins'][0]['joints'])
 for mi in lods:counts.append(sum(d['accessors'][pr['indices']]['count']//3 for pr in d['meshes'][mi]['primitives']))
 assert all(a>=b>0 for a,b in zip(counts,counts[1:])),counts
 assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['m480_a','m480_b','m480_c']
 if body:
  assert counts[0]==9744 and len(d['skins'])==1
  assert {a['name'] for a in d['animations']}=={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'}
  assert all(len(d['meshes'][i]['primitives'])==1 for i in lods)
  assert all(m['extras']['openyamm_specular_mask'] and m['pbrMetallicRoughness']['metallicFactor']==0 for m in d['materials'])
  byname={n['name']:i for i,n in enumerate(d['nodes'])};assert all(n in byname for n in ['B_Head','B_Neck','Club'])
 else:assert not d.get('skins')
 sha=hashlib.sha256(f.read_bytes()).hexdigest()
 if args.installed:assert hashlib.sha256((repo/'assets_source/worlds/mm8/models'/f.name).read_bytes()).hexdigest()==sha
 report[f.stem]={'sha256':sha,'bytes':f.stat().st_size,'triangles':counts,'variants':3,'materials':len(d['materials'])}
assert sum(v['triangles'][0] for v in report.values())<=15000
(p/'review/runtime_contract.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
