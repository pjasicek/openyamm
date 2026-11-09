"""Derive HD palette maps from real ACT pigments, restricted to semantic skin/leather UVs."""
import sys,json,colorsys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin');O=R/'full_20261006';sys.path.insert(0,str(R/'blender_rebuild_20260928/authoring'));from check_glb import Glb
base=Image.open(R/'meshy/body_texture_v1/texture_urls_0_base_color.png').convert('RGB');W,H=base.size;g=Glb(O/'work/body_for_texture_v1.glb');masks={name:Image.new('L',(W,H)) for name in ['skin','leather']}
for m in g.json['meshes']:
 for p in m['primitives']:
  role=g.json['materials'][p['material']]['name'];role='skin' if 'skin' in role else 'leather' if 'leather' in role else None
  if role is None:continue
  uv=g.accessor(p['attributes']['TEXCOORD_0']);ids=[i[0] for i in g.accessor(p['indices'])];draw=ImageDraw.Draw(masks[role])
  for i in range(0,len(ids),3):draw.polygon([(u*W,v*H) for u,v in [uv[j] for j in ids[i:i+3]]],fill=255)
# Dilate into chart padding, preserving all neighbouring non-target charts.
masks={k:v.filter(ImageFilter.MaxFilter(5)) for k,v in masks.items()}
native=np.array(Image.open(R/'stage1_20261006/source/frames/gobsta0.png').convert('RGBA'));act={pid:np.frombuffer((R.parents[2]/f'assets_dev/worlds/mm6/textures/pal{pid}.act').read_bytes()[:768],dtype=np.uint8).reshape(256,3) for pid in [745,746,747]}
lookup={tuple(color):i for i,color in enumerate(act[745])};indices=np.zeros(native.shape[:2],dtype=np.uint8)
for color in np.unique(native[native[:,:,3]>0,:3],axis=0):
 key=tuple(color);assert key in lookup,('native color absent from ACT',key)
 indices[np.all(native[:,:,:3]==color,axis=2)]=lookup[key]
palettes={pid:act[pid][indices].astype(np.float32)/255 for pid in act}
regions={'skin':(155,38,201,88),'leather':(145,183,215,225)};medians={}
for role,(x0,y0,x1,y1) in regions.items():
 original=palettes[745][y0:y1,x0:x1];r,gr,b=original.transpose(2,0,1);sel=((np.minimum(r,gr)-b>.04)&(r<gr*1.25)) if role=='skin' else ((r>gr*1.3)&(gr>b*1.15)&(r-gr>.025))
 assert sel.sum()>25,(role,sel.sum())
 medians[role]={pid:np.median(a[y0:y1,x0:x1][sel],axis=0) for pid,a in palettes.items()}
(O/'delivery/textures').mkdir(exist_ok=True,parents=True);rgb=np.array(base,dtype=np.float32)/255;mx=rgb.max(axis=2);mn=rgb.min(axis=2);sat=(mx-mn)/np.maximum(mx,1e-5)
for pid in [746,747]:
 result=rgb.copy()
 for role in ['skin','leather']:
  native=medians[role][pid];h,s,_=colorsys.rgb_to_hsv(*native);target=np.array(colorsys.hsv_to_rgb(h,s,1),dtype=np.float32)
  # Preserve texture shading/pores; move the pigment hue, with local saturation contrast.
  native_base_s=colorsys.rgb_to_hsv(*medians[role][745])[1];new_s=np.clip(sat*s/max(native_base_s,.1),.10,.92)
  pigment=mx[...,None]*(1-new_s[...,None]*(1-target));r,gr,b=rgb.transpose(2,0,1)
  color_gate=((gr>r*.85)&(b<gr*.90)) if role=='skin' else ((r>gr*1.15)&(gr>b*1.10)&(mx<.84))
  mask=(np.array(masks[role],dtype=np.float32)/255)*color_gate
  result=result*(1-mask[...,None])+pigment*mask[...,None]
 Image.fromarray(np.uint8(np.clip(result,0,1)*255+.5)).save(O/f'delivery/textures/goblin_basecolor_{pid}.png')
report={'native_palette_paths':[f'assets_dev/worlds/mm6/textures/pal{p}.act' for p in [745,746,747]],'native_sample_image':'stage1_20261006/source/frames/gobsta0.png; exact ACT745 color-index lookup','pigment_medians':{r:{p:v.tolist() for p,v in vs.items()} for r,vs in medians.items()},'method':'Real native pigment hue/saturation, HD map value and saturation contrast retained; unique semantic UV masks plus pigment gating protect gold, eyes, teeth and neutral iron. Native scale ratios are consumer metadata.'}
(O/'delivery/palette_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True)
