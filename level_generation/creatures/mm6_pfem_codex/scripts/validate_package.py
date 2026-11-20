"""Quick delivered-package checks; no Blender or service calls."""
import json,struct,hashlib,io
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parents[1];f=p/'export/mm6_pfem.glb'
raw=f.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);b=raw[28+n:]
def arr(i):
 a=d['accessors'][i];v=d['bufferViews'][a['bufferView']]
 typ={5121:np.uint8,5123:np.uint16,5125:np.uint32,5126:np.float32}[a['componentType']]
 size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 return np.ndarray((a['count'],size),dtype=typ,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(typ).itemsize*size),np.dtype(typ).itemsize))
durations={a['name']:max(float(arr(s['input']).max()) for s in a['samplers']) for a in d['animations']}
expected={'Standing':2.,'Walking':.8,'Hit':.5,'Death':71/30,'Dead':1.,'Fidget':3.}
assert durations.keys()==expected.keys()
assert all(abs(durations[k]-v)<1e-5 for k,v in expected.items())
assert len(d['skins'])==1 and len(d['skins'][0]['joints'])==128
assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['pfem_a','pfem_b','pfem_c']
counts=[]
for mesh in d['meshes'][:4]:
 assert len(mesh['primitives'])==1
 prim=mesh['primitives'][0];counts.append(d['accessors'][prim['indices']]['count']//3)
 w=arr(prim['attributes']['WEIGHTS_0']);assert w.shape[1]==4 and np.max(abs(w.sum(axis=1)-1))<1e-5
 assert 'WEIGHTS_1' not in prim['attributes']
assert counts==[9123,4560,1640,539],counts
for m in d['materials']:
 assert m['extras']['openyamm_specular_mask']
 idx=m['pbrMetallicRoughness']['metallicRoughnessTexture']['index']
 im=d['images'][d['textures'][idx]['source']];v=d['bufferViews'][im['bufferView']];off=v.get('byteOffset',0)
 pixels=np.array(Image.open(io.BytesIO(b[off:off+v['byteLength']])))
 assert pixels.shape[:2]==(1024,2080) and pixels[:,:,2].max()==0 and len(np.unique(pixels[:,:,0]))>1
root=p.parents[2];source=root/'assets_source/worlds/mm6/models/mm6_pfem.glb'
assert source.read_bytes()==raw
report={'sha256':hashlib.sha256(raw).hexdigest(),'triangles':counts,'joints':128,'max_influences':4,'clips':durations,'palette_variants':['pfem_a','pfem_b','pfem_c'],'one_primitive_per_visible_lod':True,'atlas_size':[2080,1024],'source_matches_export':True}
(p/'export/validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
