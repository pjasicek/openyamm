"""Bake exact engine tier ramp math into review-only GLBs, retaining packaged normals and ORM."""
import sys,copy,io,json
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];W=P/'work/round2';sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
from merge_head_material import image_of,compact
lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
entries=[]
for label,path in [('baseline',P/'review/triangle_reduction/baseline/export/mm6_lch.glb'),('final',P/'export/mm6_lch.glb'),('accepted_far',P/'review/triangle_reduction/baseline/export/mm6_lch.glb')]:
 original,binary=read_glb(path)
 for tier in range(1 if label=='accepted_far'else 3):
  mat=original['materials'][tier];texid=mat['pbrMetallicRoughness']['baseColorTexture']['index'];base=np.asarray(image_of(original,binary,texid)[0].convert('RGB'),np.float32)/255
  mask=np.asarray(image_of(original,binary,mat['extras']['openyamm_region_mask']['index'])[0].convert('RGBA'),np.float32)/255
  color=lin(base);lum=color@np.array([.2126,.7152,.0722])
  for channel,reg in enumerate(mat['extras']['openyamm_region_ramps']):
   colors=np.array(reg['colors']);lo,hi=reg['range'];x=np.clip((lum-lo)/(hi-lo),0,1)*(len(colors)-1);i=np.minimum(x.astype(int),len(colors)-2);f=(x-i)[:,:,None]
   ramp=colors[i]*(1-f)+colors[i+1]*f;color=color*(1-mask[:,:,channel,None])+ramp*mask[:,:,channel,None]
  im=Image.fromarray(np.clip(srgb(color)*255+.5,0,255).astype('uint8'));buf=io.BytesIO();im.save(buf,format='PNG');png=buf.getvalue()
  for level in ([2,3]if label=='accepted_far'else range(4)):
   doc=copy.deepcopy(original);data=bytearray(binary);node=next(n for n in doc['nodes']if n.get('name')=='Lich');mi=node['mesh']
   if label!='baseline'and level:mi=doc['meshes'][mi]['extras']['openyamm_lods'][level-1]
   doc['meshes']=[copy.deepcopy(doc['meshes'][mi])];doc['meshes'][0].pop('extras',None);node['mesh']=0
   index=doc['textures'][texid]['source'];data.extend(b'\0'*(-len(data)%4));doc['bufferViews'].append({'buffer':0,'byteOffset':len(data),'byteLength':len(png)});data.extend(png);doc['images'][index]['bufferView']=len(doc['bufferViews'])-1
   for primitive in doc['meshes'][0]['primitives']:primitive.pop('extensions',None);primitive['material']=tier
   doc,b=compact(doc,data);file=W/f'render_{label}_{tier}_lod{level}.glb';write_glb(file,doc,b)
   entries.append({'label':label,'tier':tier,'level':level,'file':str(file.relative_to(P))})
(P/'review/triangle_rebake/render_inputs.json').write_text(json.dumps(entries,indent=2)+'\n');print('PREPARED',len(entries),'paired material imports')
