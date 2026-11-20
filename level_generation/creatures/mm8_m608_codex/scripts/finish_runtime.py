"""Restore the authored specular masks after Blender ORM packing and make eye/flash emission unlit."""
import sys,io,json,numpy as np
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
path=P/'export/mm8_m608.glb';d,raw=read_glb(path);b=bytearray(raw);patched=set()
for mat in d['materials']:
 name=mat.get('name','')
 if name in ['Eyes','Flash']:
  mat.setdefault('extensions',{})['KHR_materials_unlit']={};mat.pop('emissiveTexture',None);mat['emissiveFactor']=[0,0,0]
  continue
 mat.get('extensions',{}).pop('KHR_materials_specular',None)
 info=mat.get('pbrMetallicRoughness',{}).get('metallicRoughnessTexture')
 if not info:continue
 source=d['textures'][info['index']]['source']
 if source in patched:continue
 old=d['images'][source];view=d['bufferViews'][old['bufferView']];im=np.array(Image.open(io.BytesIO(b[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])).convert('RGB'))
 # Metallic ownership already follows the padded belt mask; its red channel is specular strength.
 im[:,:,0]=np.where(im[:,:,2]>70,204,31).astype('uint8')
 encoded=io.BytesIO();Image.fromarray(im).save(encoded,format='PNG');payload=encoded.getvalue();b.extend(b'\0'*(-len(b)%4));d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(payload)});b.extend(payload)
 old['bufferView']=len(d['bufferViews'])-1;old['mimeType']='image/png';patched.add(source)
for field in ['extensionsUsed','extensionsRequired']:
 if field in d:d[field]=[v for v in d[field] if v!='KHR_materials_specular']
if 'KHR_materials_unlit' not in d.setdefault('extensionsUsed',[]):d['extensionsUsed'].append('KHR_materials_unlit')
write_glb(path,d,b)
(P/'work/runtime_contract.json').write_text(json.dumps({'specular_mask_images':len(patched),'unlit':['Eyes','Flash'],'alpha':'opaque stone; blended flash only'},indent=2))
print('FINAL_RUNTIME',path,flush=True)
