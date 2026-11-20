"""Shared nonmetal PBR skin and native ACT-derived shell ramps; head and paddles stay unchanged."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageFilter
from scipy.ndimage import distance_transform_edt
P=Path(__file__).resolve().parents[1];T=P/'textures';M=P/'meshy/body_texture_v1';sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as R
u=np.load(P/'work/uv_raster.npz');covered=u['covered'];pos=u['pos'];nearest=distance_transform_edt(~covered,return_distances=False,return_indices=True)
def pad(a):return a[tuple(nearest)]
def save(a,name):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(T/name)
def resize(a,n):return np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).resize((n,n),Image.Resampling.BILINEAR),float)/255
base=np.asarray(Image.open(M/'texture_urls_0_base_color.png').convert('RGB'),float)/255;assert base.shape==(2048,2048,3)
small=resize(base,1024);ao=pad(np.asarray(Image.open(T/'m580_ao.png').convert('L'),float)/255)
head=pad(pos[...,1]<-.50);shell=pad((pos[...,1]>-.26)&(pos[...,1]<.45)&(abs(pos[...,0])<.31)&(pos[...,2]>.225));flipper=pad(abs(pos[...,0])>.305)
green=pad(shell&(small[...,1]>small[...,0]*1.06)&(small[...,1]>small[...,2]*1.15)&(small[...,1]>.05))
eye=head&(small[...,0]>.3)&(small[...,1]>.22)&(small[...,2]<small[...,1]*.5)
horn=pad((head&(pos[...,2]>.29))|(shell&(pos[...,2]>.40)))
classes=np.ones((1024,1024),np.uint8);classes[shell]=11;classes[flipper]=3;classes[horn]=4;classes[eye]=6;classes[~covered]=0;Image.fromarray(classes).save(T/'m580_material_classes.png')
base=np.clip(base*resize(.88+.12*ao,2048)[...,None],0,1);save(base,'m580_basecolor.png')
rough=np.full(ao.shape,.80);rough[shell]=.66;rough[flipper]=.85;rough[horn]=.48;rough[eye]=.20
save(np.stack([ao,rough,np.zeros_like(ao)],-1),'m580_metal_rough.png')
normal=np.asarray(Image.open(M/'texture_urls_0_normal.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS),float)/127.5-1;normal/=np.maximum(np.linalg.norm(normal,axis=-1,keepdims=True),1e-6);save(normal*.5+.5,'m580_normal.png')
weight=np.asarray(Image.fromarray(np.uint8(green)*255).filter(ImageFilter.GaussianBlur(.65)),float)/255;R.write_mask([weight],T/'m580_region_mask.png')
native=P.parent/'mm7_mm8_packed_outline/session_mm8_06/mm8_m580/redo_2x';pals={n:np.frombuffer((native/f'palettes/pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for n in [581,582,583]}
a=pals[581];changed=np.maximum(abs(a-pals[582]),abs(a-pals[583])).max(1)>8/255;selected=changed&(a[:,1]>a[:,0]*1.1)&(a[:,1]>a[:,2]*1.2);selected[0]=False
counts=np.zeros(256)
for frame in (native/'sources.json',):
 sources=json.loads(frame.read_text())['sources']
 for name,rec in sources.items():
  if rec.get('referenced'):counts+=np.bincount(np.asarray(Image.open(rec['path'])).ravel(),minlength=256)
ids=np.flatnonzero(selected&(counts>0));w=np.sqrt(counts[ids]/counts[ids].max());A=R.srgb_to_linear(a[ids]);lin=R.srgb_to_linear(resize(base,1024));lum=lin@R.LUMA;pixels=lin[(weight>.9)&covered];pixels=pixels[np.argsort(pixels@R.LUMA)];lo,hi=np.percentile(pixels@R.LUMA,[.5,99.5]);stops=np.linspace(lo,hi,16)
base_colors=np.array([np.median(pixels[max(0,int(np.searchsorted(pixels@R.LUMA,y))-30):min(len(pixels),int(np.searchsorted(pixels@R.LUMA,y))+31)],axis=0) for y in stops])
ramps={'turtle_a':[]};report={}
for pal,letter in [(582,'b'),(583,'c')]:
 B=R.srgb_to_linear(pals[pal][ids]);matrix=np.linalg.lstsq(A*w[:,None],B*w[:,None],rcond=None)[0];colors=np.clip(base_colors@matrix,0,1)
 ramps['turtle_'+letter]=[{'range':[float(lo),float(hi)],'colors':colors.tolist()}];report[str(pal)]={'paired_palette_entries':len(ids),'linear_rgb_fit_rmse':float(np.sqrt(np.mean((A@matrix-B)**2))),'transform':matrix.tolist()}
config={'variants':list(ramps),'materials':[{'base':'TurtleBody','prefix':'TurtleBody','mask':'m580_region_mask.png','regions':['native shell green'],'ramps':ramps}]}
(T/'m580_ramps.json').write_text(json.dumps(config,indent=2)+'\n');(P/'review/texture_composition.json').write_text(json.dumps({'native_palette_fit':report,'green_texels':int((green&covered).sum()),'base_tier_exact_bypass':True,'classes':{str(k):int(((classes==k)&covered).sum()) for k in np.unique(classes)},'material_contract':'Nonmetal skin; MR.R baked AO, G roughness, B zero. Runtime skin specular disabled per approved shared texture guide. Class11 is keratin shell.'},indent=2)+'\n')
assert len(pixels)>100 and np.isfinite(base).all() and np.isfinite(normal).all() and all(v['linear_rgb_fit_rmse']<.06 for v in report.values()),report
print('TEXTURES',json.dumps(report),flush=True)
