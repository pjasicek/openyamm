"""Assert the exported Ratman contract and installed-source identity without changing assets."""
from pathlib import Path
import json,struct,io,hashlib,argparse
import numpy as np
from PIL import Image
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--installed',action='store_true',help='also require matching installed source GLBs')
args=parser.parse_args()
p=Path(__file__).resolve().parents[1];repo=p.parents[2];report={}
def read(path):
 raw=path.read_bytes();magic,version,length=struct.unpack_from('<III',raw);assert (magic,version,length)==(0x46546c67,2,len(raw))
 n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:]
def acc(d,b,index):
 a=d['accessors'][index];v=d['bufferViews'][a['bufferView']];dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',dt.itemsize*width)
 assert offset+(a['count']-1)*stride+dt.itemsize*width<=len(b)
 return np.ndarray((a['count'],width),dtype=dt,buffer=b,offset=offset,strides=(stride,dt.itemsize))
for stem in ('mm8_ratman','mm8_ratman_sword'):
 f=p/'export'/(stem+'.glb');d,b=read(f);body=stem=='mm8_ratman';node=next(n for n in d['nodes'] if 'mesh' in n);base=d['meshes'][node['mesh']]
 lods=[node['mesh']]+base['extras']['openyamm_lods'];counts=[]
 assert len(lods)==4
 for i,m in enumerate(d['meshes']):
  for prim in m['primitives']:
   a=prim['attributes'];positions=acc(d,b,a['POSITION']);assert np.isfinite(positions).all()
   indices=acc(d,b,prim['indices']);assert indices.max()<len(positions)
   if body:
    assert 'WEIGHTS_1' not in a
    w=acc(d,b,a['WEIGHTS_0']);assert w.shape[1]==4 and np.max(np.abs(w.sum(1)-1))<1e-4
    assert acc(d,b,a['JOINTS_0']).max()<len(d['skins'][0]['joints'])
 for i in lods:counts.append(sum(d['accessors'][x['indices']]['count']//3 for x in d['meshes'][i]['primitives']))
 assert all(a>b for a,b in zip(counts,counts[1:]))
 variants=d['extensions']['KHR_materials_variants']['variants'];assert [v['name'] for v in variants]==['ratman_a','ratman_b','ratman_c']
 if body:
  assert counts[0]==14623 and len(d['skins'])==1
  assert {a['name'] for a in d['animations']}=={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'}
  assert all(len(d['meshes'][i]['primitives'])==1 for i in lods)
  for mat in d['materials']:
   assert mat['extras']['openyamm_specular_mask'] and mat['pbrMetallicRoughness']['metallicFactor']==0
  mi=d['materials'][0]['extras']['openyamm_region_mask']['index'];im=d['images'][d['textures'][mi]['source']];v=d['bufferViews'][im['bufferView']];off=v.get('byteOffset',0)
  pixels=np.array(Image.open(io.BytesIO(b[off:off+v['byteLength']])).convert('RGBA'));assert pixels.shape==(1024,2080,4)
  assert not pixels[:,1056:,:].any() and not pixels[...,1:].any();assert pixels[...,0].max()==255
 else:assert not d.get('skins') and counts[0]==136
 sha=hashlib.sha256(f.read_bytes()).hexdigest();installed=repo/'assets_source/worlds/mm8/models'/f.name
 if args.installed:assert installed.exists() and hashlib.sha256(installed.read_bytes()).hexdigest()==sha
 report[stem]={'sha256':sha,'bytes':f.stat().st_size,'triangles':counts,'variants':3,'material_count':len(d['materials']),'image_count':len(d['images'])}
assert report['mm8_ratman']['triangles'][0]+report['mm8_ratman_sword']['triangles'][0]<15000
(p/'review/runtime_contract.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
