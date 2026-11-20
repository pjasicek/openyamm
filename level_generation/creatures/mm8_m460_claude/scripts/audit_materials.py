from pathlib import Path
import sys,json,io,numpy as np
from PIL import Image
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'));from merge_head_material import read_glb,accessor_array
report={}
for name in ['mm8_m460','mm8_m460_staff']:
 d,b=read_glb(p/'export'/f'{name}.glb');m=d['meshes'][0];primitive=m['primitives'][0];a=primitive['attributes'];uv=accessor_array(d,b,a['TEXCOORD_0']);indices=accessor_array(d,b,primitive['indices']).reshape(-1,3);t=uv[indices];u=t[:,1]-t[:,0];v=t[:,2]-t[:,0];area=abs(u[:,0]*v[:,1]-u[:,1]*v[:,0])*.5
 assert np.isfinite(uv).all() and uv.min()>=-1e-5 and uv.max()<=1.00001
 normal=accessor_array(d,b,a['NORMAL']);assert np.max(abs(np.linalg.norm(normal,axis=1)-1))<.001
 images={};maps=[]
 for material in d['materials']:
  assert material['pbrMetallicRoughness']['metallicFactor']==0
  assert material.get('extras',{}).get('openyamm_specular_mask')
  for kind,ref in [('base',material['pbrMetallicRoughness']['baseColorTexture']),('mr',material['pbrMetallicRoughness']['metallicRoughnessTexture']),('normal',material['normalTexture'])]:
   im=d['images'][d['textures'][ref['index']]['source']];v=d['bufferViews'][im['bufferView']];data=b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];img=Image.open(io.BytesIO(data)).convert('RGB');expected=(2080,1024) if name=='mm8_m460' else (128,1024);assert img.size==expected,(name,kind,img.size)
   pixels=np.asarray(img);images[kind]={'dimensions':list(img.size),'range':[[int(pixels[...,i].min()),int(pixels[...,i].max())] for i in range(3)]}
   if kind=='mr':assert pixels[...,2].max()==0 and pixels[...,0].min()<=(0 if name=='mm8_m460' else 102) and pixels[...,0].max()==255
 zero_uv = area < 1e-12
 if name == 'mm8_m460':
  assert not zero_uv.any()
 else:
  assert int(zero_uv.sum()) == 9
  caps = accessor_array(d,b,a['POSITION'])[indices[zero_uv]]
  # Allow the exported cap's measured 0.015 mm fitting/rounding variation.
  assert np.max(np.ptp(caps[:,:,2], axis=1)) < 2e-5
  assert np.max(np.ptp(t[zero_uv], axis=1)) < 2e-7
 report[name]={'lod0_triangles':len(indices),'zero_uv_area_triangles':int((area<1e-12).sum()),'uv_range':[float(uv.min()),float(uv.max())],'images':images,'shadow_chain':m['extras']['openyamm_shadow_lods'] if name=='mm8_m460' else [0]+m['extras']['openyamm_lods']}
report['mm8_m460_staff']['uv_exception'] = 'Nine planar closed endcap triangles intentionally use one UV texel each; uniform paint and flat normal. Position/UV checks verify this exception.'
(p/'work/material_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('MATERIAL_AUDIT',report)
