"""One shared 1K body/1K head set, with padded UV rectangles for each independently rebaked LOD."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
P=Path(__file__).resolve().parents[1];T=P/'textures/round2';sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,append_accessor
from merge_head_material import compact,accessor_array
# Pixel rectangles use a lower-left origin, exactly like glTF UVs. Entire allocated tiles have repeated edge texels.
slots=[(0,0,768,1024,8),(768,512,256,512,16),(768,256,256,256,16),(768,0,256,256,16)]
rects=[];report=[]
for level,(x,y,w,h,g)in enumerate(slots):
 rects.append([x+g,y+g,w-2*g,h-2*g]);assert x+w<=1024 and y+h<=1024
 if level:
  for prefix in ['lch','lch_head']:
   coverage=np.asarray(Image.open(T/f'lod{level}/{prefix}_coverage.png').convert('RGB'))[:,:,0]>250
   assert coverage.mean()>.03,(level,prefix,coverage.mean())
   _,ix=distance_transform_edt(~coverage,return_indices=True)
   for suffix in ['basecolor_1k','normal_1k','metal_rough_1k','region_mask']:
    path=T/f'lod{level}/{prefix}_{suffix}.png';a=np.array(Image.open(path).convert('RGBA'));a[~coverage]=a[ix[0][~coverage],ix[1][~coverage]]
    if suffix=='region_mask':a[:,:,1:]=0
    else:a[:,:,3]=255
    Image.fromarray(a).save(path)
   report.append({'lod':level,'set':prefix,'ray_hit_fraction':float(coverage.mean())})
for prefix in ['lch','lch_head']:
 for suffix in ['basecolor_1k','normal_1k','metal_rough_1k','region_mask']:
  canvas=np.zeros((1024,1024,4),dtype=np.uint8)
  for level,(x,y,w,h,g)in enumerate(slots):
   source=Image.open(T/f'lod{level}/{prefix}_{suffix}.png').convert('RGBA')
   # Resize individual channels: region-mask alpha is intentionally zero and must not premultiply RGB.
   a=np.stack([np.asarray(c.resize((w-2*g,h-2*g),Image.Resampling.LANCZOS))for c in source.split()],axis=-1)
   if suffix=='normal_1k':
    n=a[:,:,:3].astype(float)/127.5-1;n/=np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-8);a[:,:,:3]=np.clip((n+1)*127.5+.5,0,255).astype('uint8')
   tile=np.pad(a,((g,g),(g,g),(0,0)),mode='edge');canvas[1024-y-h:1024-y,x:x+w]=tile
  Image.fromarray(canvas).save(T/f'{prefix}_{suffix}.png')
for level,rect in enumerate(rects):
 doc,data=read_glb(P/f'work/round2/lod{level}_geometry_unpacked.glb');data=bytearray(data)
 node=next(n for n in doc['nodes']if n.get('name')=='Lich');x,y,w,h=rect
 for prim in doc['meshes'][node['mesh']]['primitives']:
  i=prim['attributes']['TEXCOORD_0'];uv=accessor_array(doc,data,i);assert uv.min()>-.001 and uv.max()<1.001
  uv[:,0]=(x+uv[:,0]*w)/1024;uv[:,1]=(1024-y-h+uv[:,1]*h)/1024
  prim['attributes']['TEXCOORD_0']=append_accessor(doc,data,doc['accessors'][i],uv.astype('<f4').tobytes())
 doc,data=compact(doc,data);write_glb(P/f'work/round2/lod{level}_geometry.glb',doc,data)
(P/'review/triangle_rebake/texture_layout.json').write_text(json.dumps({'set_resolution':[1024,1024],'source_bake_resolution':[1024,1024],'rectangles_lower_left':rects,'tile_padding_px':[r[4]for r in slots],'method':'Four independently projected surface bakes in one shared body set and one shared head set; no new tier materials or runtime texture slots. Normal vectors renormalized after resampling.','coverage':report},indent=2)+'\n');print('SHARED_LOD_TEXTURE_LAYOUT',rects)
