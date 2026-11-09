"""Bake runtime colour ramps into portable viewer-only copies; geometry and animation stay identical."""
from pathlib import Path
import json,sys,hashlib,io,copy
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,image_of,add_image
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
source=P/'export/mm8_m488.glb';out=P/'review/viewer'
d,b=read_glb(source);models=[]
for vi,tier in enumerate('abc'):
 doc=copy.deepcopy(d);binary=bytearray(b)
 # The viewer needs only LOD0. Select the variant material and bake the same shader ramp.
 node=next(n for n in doc['nodes'] if n.get('name')=='Minotaur');mesh=doc['meshes'][node['mesh']]
 mesh.pop('extras',None)
 for primitive in mesh['primitives']:
  mappings=primitive['extensions']['KHR_materials_variants']['mappings'];mi=next(m['material'] for m in mappings if vi in m['variants']);primitive['material']=mi
  mat=doc['materials'][mi];pbr=mat['pbrMetallicRoughness'];ex=mat['extras']
  base,_=image_of(doc,binary,pbr['baseColorTexture']['index']);mask,_=image_of(doc,binary,ex['openyamm_region_mask']['index'])
  rgb=R.srgb_to_linear(np.asarray(base.convert('RGB'),float)/255);weights=np.asarray(mask.convert('RGBA'),float)/255;lum=rgb@R.LUMA
  # Runtime extras store flat ranges/colours; use the retained compose ramps as the authoritative data.
  reg=json.loads((P/'textures/m488_ramps.json').read_text())['materials'][0]['ramps']['m488_'+tier][0]
  lo,hi=reg['range'];cols=np.array(reg['colors']);x=np.clip((lum-lo)/(hi-lo),0,1)*15;i=np.minimum(x.astype(int),14);f=(x-i)[...,None]
  rgb=rgb*(1-weights[...,0,None])+(cols[i]*(1-f)+cols[i+1]*f)*weights[...,0,None]
  rgb=np.where(rgb<=.0031308,rgb*12.92,1.055*np.maximum(rgb,0)**(1/2.4)-.055)
  im=Image.fromarray(np.uint8(np.clip(rgb*255+.5,0,255)));idx=add_image(doc,binary,im,'ViewerTier_'+tier,None);pbr['baseColorTexture']={'index':idx}
  primitive.pop('extensions',None)
 name=f'mm8_m488_{tier}.glb';write_glb(out/name,doc,binary);sha=hashlib.sha256((out/name).read_bytes()).hexdigest();models.append({'id':'m488_'+tier,'label':'Minotaur peasant '+tier.upper(),'revision':'m488-production-01','url':name+'?v='+sha[:12],'sha256':sha})
f=out/'manifest.json';manifest=json.loads(f.read_text());manifest.update(revision='m488-production-01',models=models,default_model='m488_a',model='mm8_m488_a.glb',model_sha256=models[0]['sha256']);f.write_text(json.dumps(manifest,indent=2)+'\n');print('VIEWER',len(models),'tiers')
