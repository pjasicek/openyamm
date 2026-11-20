"""Structural assertions on the actual staged runtime GLBs and review variants."""
from pathlib import Path
import struct,json,hashlib,io
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
DT={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
N={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def read(path):
 raw=path.read_bytes();magic,version,total=struct.unpack_from('<III',raw);assert (magic,version,total)==(0x46546c67,2,len(raw))
 n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
 def accessor(i):
  a=doc['accessors'][i];assert 'sparse' not in a;aView=doc['bufferViews'][a['bufferView']];dtype=np.dtype(DT[a['componentType']]);count=N[a['type']]
  offset=aView.get('byteOffset',0)+a.get('byteOffset',0);stride=aView.get('byteStride',count*dtype.itemsize)
  assert offset+(a['count']-1)*stride+count*dtype.itemsize<=len(binary)
  out=np.ndarray((a['count'],count),dtype=dtype,buffer=binary,offset=offset,strides=(stride,dtype.itemsize))
  assert np.isfinite(out).all(),(path,i)
  return out
 for i in range(len(doc.get('accessors',[]))):accessor(i)
 counts=[];weightError=0.;influences=0
 for m in doc['meshes']:
  tris=0
  for pr in m['primitives']:
   attrs=pr['attributes'];pos=accessor(attrs['POSITION']);indices=accessor(pr['indices']).ravel();assert len(indices)%3==0 and indices.max()<len(pos)
   tris+=len(indices)//3
   for semantic,idx in attrs.items():assert len(accessor(idx))==len(pos),(path,semantic)
   ws=[accessor(attrs[n]) for n in ['WEIGHTS_0','WEIGHTS_1'] if n in attrs]
   if ws:
    weights=np.concatenate(ws,axis=1);weightError=max(weightError,float(abs(weights.sum(1)-1).max()));influences=max(influences,int((weights>1e-6).sum(1).max()))
    assert weights.min()>=0 and weightError<.0001 and influences<=8
    skin=doc['skins'][0];assert len(skin['joints'])<=128
    for semantic in ['JOINTS_0','JOINTS_1']:
     if semantic in attrs:assert accessor(attrs[semantic]).max()<len(skin['joints'])
  counts.append(tris)
 imageSizes=[]
 for im in doc.get('images',[]):
  v=doc['bufferViews'][im['bufferView']];offset=v.get('byteOffset',0)
  with Image.open(io.BytesIO(binary[offset:offset+v['byteLength']])) as image:image.load();imageSizes.append(list(image.size))
 return doc,{'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'mesh_triangles':counts,'joints':max([len(s['joints']) for s in doc.get('skins',[])],default=0),'maximum_influences':influences,'weight_sum_max_error':weightError,'image_sizes':imageSizes}
report={}
for name in ['export/mm6_sor1.glb','export/mm6_sor1_staff.glb',*[f'review/viewer/mm6_sor1_{x}.glb' for x in 'abc']]:
 doc,r=read(p/name);report[name]=r
 if name.startswith('export/'):
  extras=doc['meshes'][0]['extras'];lods=[0,*extras['openyamm_lods']];shadow=extras.get('openyamm_shadow_lods',[]);assert len(lods)==4;assert not shadow or len(shadow)==4
  r['colour_lod_triangles']=[r['mesh_triangles'][i] for i in lods];assert all(a>b for a,b in zip(r['colour_lod_triangles'],r['colour_lod_triangles'][1:]))
  assert all(len(doc['meshes'][i]['primitives'])==1 for i in lods+shadow)
 if name=='export/mm6_sor1.glb':
  names={n['name'] for n in doc['nodes']};assert {'B_Staff','Socket_Palm_Left','Socket_Palm_Right','Socket_Staff_Head'}<=names
  r['tiers']=[v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']];assert r['tiers']==['sor1_a','sor1_b','sor1_c']
  r['clips']={a['name']:max(float(readT) for s in a['samplers'] for readT in [doc['accessors'][s['input']]['max'][0]]) for a in doc['animations']}
  assert set(r['clips'])=={'Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget'}
 if name=='export/mm6_sor1_staff.glb':assert not doc.get('animations') and not doc.get('skins')
for name,h in json.loads((p/'source/input_hashes.json').read_text()).items():assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==h,name
report['source_reference_hashes_unchanged']=True
(p/'work/runtime_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
