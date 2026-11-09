"""Shared 1K body/head textures, material classes and native trouser-only tier ramps."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
p=Path(__file__).resolve().parents[1];T=p/'textures';T.mkdir(exist_ok=True)
sys.path.insert(0,str(p.parent/'claude_shared'));import region_variants as R
N=1024
FUR=np.array([132,105,78])/255
SPEC={1:.15,2:.28,3:.08,4:.25,5:.3,6:.65}
ROUGH={1:.90,2:.70,3:.95,4:.80,5:.60,6:.30}
def load(path,mode='RGB'):
 return np.array(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path)
def pad(a,cov):
 _,idx=ndimage.distance_transform_edt(~cov,return_indices=True);out=a[tuple(idx)];out[cov]=a[cov];return out
def srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def fur_grade(img,mask):
 lum=R.luminance(img);den=ndimage.gaussian_filter(mask.astype(float),6)
 avg=ndimage.gaussian_filter(lum*mask,6)/np.maximum(den,1e-5)
 fine=np.clip(lum/np.maximum(avg,1e-5),.55,1.45)
 out=img.copy();target=srgb(R.srgb_to_linear(FUR)[None,:]*fine[mask,None]);out[mask]=.15*img[mask]+.85*target;return out
report={};body_lum=None
for layer,job,prefix in [('UVMap','body_retexture_v1','ratman'),('HeadUV','head_retexture_v1','ratman_head')]:
 raw=p/'meshy'/job;base=load(raw/'texture_urls_0_base_color.png');normal=load(raw/'texture_urls_0_normal.png');rough=load(raw/'texture_urls_0_roughness.png','L')
 r=np.load(p/'work'/('uvraster_'+layer+'.npz'));piece,gar,pos,bone=r['piece'],r['garment'],r['pos'],r['bone'];cov=piece>=0
 hsv=np.asarray(Image.fromarray(np.uint8(base*255)).convert('HSV'),float)/255;h,s,v=hsv[...,0]*360,hsv[...,1],hsv[...,2]
 cls=np.ones((N,N),np.uint8);cls[~cov]=0
 tail=np.zeros_like(cov)
 for i,name in enumerate(r['bone_names']):
  if str(name).startswith('Tail'):tail|=bone==i
 if layer=='UVMap':
  pants=cov&(piece==0)&~tail&(pos[...,2]>.30)&(pos[...,2]<1.08)&(np.abs(pos[...,0])<.35)&(h>55)&(h<165)&(s>.18)&(v>.08)
  pants=ndimage.binary_closing(pants,iterations=1)&cov&(piece==0)&~tail&(pos[...,2]>.30)&(pos[...,2]<1.08)
  cls[cov&(piece==1)]=3;cls[pants]=3;cls[cov&(piece==3)]=4
  cls[cov&(piece==0)&~tail&(pos[...,2]>.15)&(pos[...,2]<.40)]=4
  hands=cov&(piece==0)&(np.abs(pos[...,0])>.36)&(pos[...,2]<1.15)
  cls[hands]=2
  # Painted light claw tips retain their ivory and detail.
  cls[cov&(piece==0)&((hands)|(pos[...,2]<.16))&(v>.65)&(s<.3)]=5
 else:
  cls[cov&(piece==201)]=5
  # Pink inner ears, nose, dark eyes and ivory small teeth retain source paint.
  cls[cov&(piece!=201)&(h<20)&(s>.2)&(pos[...,2]>1.60)]=2
  cls[cov&(v<.20)&(pos[...,1]<-.25)]=6
  cls[cov&(s<.22)&(v>.63)&(pos[...,2]<1.52)]=5
 fur=cov&(cls==1)&(s>.12)&(v>.14)&(h>15)&(h<65)
 out=fur_grade(base,fur)
 if layer=='HeadUV':
  teeth=cov&(piece==201);L=R.luminance(base);detail=np.clip(L/np.median(L[teeth]),.5,1.25)
  out[teeth]=np.clip(np.array([.85,.79,.64])*detail[teeth,None],0,1)
 ao=load(p/'work'/('ao_'+layer+'.png'),'L');out[cov]*=(.65+.35*np.maximum(ao[cov],.45))[:,None]
 spec=np.zeros((N,N));rgh=np.ones((N,N))*.9
 for c in SPEC:
  m=cov&(cls==c)
  if m.any():spec[m]=SPEC[c];rgh[m]=np.clip(ROUGH[c]+(rough[m]-np.median(rough[m]))*.25,.15,1)
 save(pad(out,cov),T/(prefix+'_basecolor_1k.png'));save(pad(normal,cov),T/(prefix+'_normal_1k.png'))
 save(np.stack([pad(spec,cov),pad(rgh,cov),np.zeros_like(spec)],-1),T/(prefix+'_metal_rough_1k.png'))
 Image.fromarray(cls).save(T/(prefix+'_material_classes.png'));save(ao,T/(prefix+'_ao_1k.png'))
 report[layer]={'covered':int(cov.sum()),'classes':{str(c):int((cov&(cls==c)).sum()) for c in SPEC},'fur_regraded':int(fur.sum())}
 if layer=='UVMap':
  mask=ndimage.gaussian_filter(pad(pants.astype(float),cov),.6);mask[cov&~pants]=0
  R.write_mask([mask],T/'ratman_region_mask.png',N);body_lum=R.luminance(out[pants]);assert len(body_lum)>1000
  report['pants_texels']=int(pants.sum())
# Palette ramps are measured from identical native pixels that change across 449/450/451.
variants={'ratman_a':449,'ratman_b':450,'ratman_c':451};native={k:[] for k in variants}
for frame in ('m448sa0','m448sa1','m448sa2','m448wa0','m448wc0','m448aa0','m448ad0'):
 ims={k:np.asarray(Image.open(p.parent/'mm8_m448/native_variants'/f'{frame}_{pal}.png').convert('RGBA'),float)/255 for k,pal in variants.items()}
 diff=np.maximum(np.abs(ims['ratman_a']-ims['ratman_b']).max(-1),np.abs(ims['ratman_a']-ims['ratman_c']).max(-1))>.02
 cov=ims['ratman_a'][...,3]>.5
 for k in variants:native[k].append(ims[k][diff&cov,:3])
lo,hi=np.percentile(body_lum,[2,98]);sorted_lum=np.sort(body_lum);ramps={}
for k in variants:
 colors=np.concatenate(native[k]);lum=R.luminance(colors);colors=colors[lum>.015];colors=colors[np.argsort(R.luminance(colors))];assert len(colors)>100
 q=np.searchsorted(sorted_lum,np.linspace(lo,hi,16))/len(sorted_lum)
 rgb=colors[np.minimum((q*(len(colors)-1)).astype(int),len(colors)-1)]
 ramps[k]=[{'range':[float(lo),float(hi)],'colors':R.srgb_to_linear(np.clip(rgb*1.18,0,1)).round(6).tolist()}]
(T/'ratman_ramps.json').write_text(json.dumps({'variants':list(variants),'materials':[{'base':'Ratman_A','prefix':'Ratman','mask':'ratman_region_mask.png','regions':['trousers'],'palettes':variants,'ramps':ramps}]},indent=2))
# Sword colour comes from its authored orthographic reference; pad only the transparent background.
im=Image.open(p/'references_props/sword_front.png').convert('RGBA').crop((330,0,690,1536));a=np.array(im);cov=a[...,3]>128
rgb=pad(a[...,:3]/255,cov);im=Image.fromarray(np.uint8(rgb*255+.5)).resize((256,1024),Image.Resampling.LANCZOS);im.save(T/'ratman_sword_basecolor.png')
y=np.arange(1024)[:,None];leather=(y>780)&(y<961);spec=np.broadcast_to(np.where(leather,.25,.8),(1024,256));rough=np.where(spec<.5,.8,.43);metal=np.where(spec<.5,0,.8)
save(np.stack([spec,rough,metal],-1),T/'ratman_sword_metal_rough.png');Image.new('RGB',(256,1024),(128,128,255)).save(T/'ratman_sword_normal.png')
report['class_legend']={'1':'fur','2':'bare skin','3':'cloth','4':'leather/wraps','5':'teeth/claws','6':'eyes/nose'}
(T/'texture_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
