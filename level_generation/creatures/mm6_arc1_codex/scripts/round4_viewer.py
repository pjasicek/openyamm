"""Make the review viewer from the final runtime GLBs, including their repacked maps."""
import sys,copy,runpy
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor,image_of,add_image,TEXTURE_SLOTS,compact,slot
lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.clip(c,0,None)**(1/2.4)-.055)
for tier in range(3):
 d,b=read_glb(P/'export/mm6_arc1.glb')
 mat=d['materials'][tier];base=np.array(image_of(d,b,mat['pbrMetallicRoughness']['baseColorTexture']['index'])[0].convert('RGBA'),np.float32)/255
 mask=np.array(image_of(d,b,mat['extras']['openyamm_region_mask']['index'])[0].convert('RGBA'),np.float32)/255
 out=lin(base[:,:,:3]);lum=out@np.array([.2126,.7152,.0722])
 for c,reg in enumerate(mat['extras']['openyamm_region_ramps']):
  lo,hi=reg['range'];colors=np.array(reg['colors']);x=np.clip((lum-lo)/(hi-lo),0,1)*(len(colors)-1);i=np.minimum(x.astype(int),len(colors)-2);f=(x-i)[...,None]
  out=out*(1-mask[...,c:c+1])+(colors[i]*(1-f)+colors[i+1]*f)*mask[...,c:c+1]
 pixels=np.concatenate((np.clip(srgb(out),0,1),base[:,:,3:4]),2)
 tex=add_image(d,b,Image.fromarray((pixels*255+.5).astype(np.uint8)),f'ReviewTier{tier}',None)
 mat['pbrMetallicRoughness']['baseColorTexture']['index']=tex
 for mesh in d['meshes']:
  for prim in mesh['primitives']:
   prim['material']=tier;prim.pop('extensions',None)
 for name in ['Bow','Arrow']:
  pd,pb=read_glb(P/f'export/mm6_arc1_{name.lower()}.glb');tm={}
  for ti in range(len(pd['textures'])):
   im,n=image_of(pd,pb,ti);tm[ti]=add_image(d,b,im,n,None)
  pm=copy.deepcopy(pd['materials'][0])
  for path in TEXTURE_SLOTS:
   s=slot(pm,path)
   if s is not None:s['index']=tm[s['index']]
  mi=len(d['materials']);d['materials'].append(pm)
  prim=copy.deepcopy(pd['meshes'][0]['primitives'][0]);prim['material']=mi;prim.pop('extensions',None)
  for key,ai in prim['attributes'].items():prim['attributes'][key]=append_accessor(d,b,accessor_array(pd,pb,ai),pd['accessors'][ai],34962)
  ai=prim['indices'];prim['indices']=append_accessor(d,b,accessor_array(pd,pb,ai),pd['accessors'][ai],34963)
  meshid=len(d['meshes']);d['meshes'].append({'name':name+'Attachment','primitives':[prim]})
  ni=len(d['nodes']);d['nodes'].append({'name':name+'Attachment','mesh':meshid})
  joint=next(n for n in d['nodes']if n.get('name')==name);joint.setdefault('children',[]).append(ni)
 d,b=compact(d,b);write_glb(P/f'review/viewer/mm6_arc1_{chr(97+tier)}.glb',d,b)
 print('FINAL RUNTIME VIEWER',tier,flush=True)
runpy.run_path(str(P/'scripts/viewer_manifest.py'),run_name='__main__')
