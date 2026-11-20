"""One shared body skin, a small equipment atlas, and native palette ramps for green/violet/crimson accents."""
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
def resize(a,size):return np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).resize((size,size),Image.Resampling.BILINEAR),float)/255
base=np.asarray(Image.open(M/'texture_urls_0_base_color.png').convert('RGB'),float)/255;assert base.shape==(2048,2048,3)
small=resize(base,1024);ao=np.asarray(Image.open(T/'m556_ao.png').convert('L'),float)/255;ao=pad(ao)
wing=pad((abs(pos[...,0])>.085)&(pos[...,2]>.60));head=pad((pos[...,1]<-.13)&(pos[...,2]>.62))
green=(small[...,1]>small[...,0]*1.18)&(small[...,1]>small[...,2]*1.10)&(small[...,1]>.085)&~wing
green=pad(green);eye=green&head;armor=green&~head
claw=pad(((abs(pos[...,0])>.21)&(pos[...,2]<.48)&(pos[...,1]<0))|((abs(pos[...,0])>.20)&(pos[...,2]<.14))|((pos[...,2]<.08)&(pos[...,1]>.30))|((pos[...,1]<-.30)&(pos[...,2]>.78)))
classes=np.ones((1024,1024),np.uint8);classes[wing]=3;classes[claw]=4;classes[eye]=6;classes[armor]=9
Image.fromarray(classes).save(T/'m556_material_classes.png')
shade=.82+.18*ao;shade[wing]*=.64
base=np.clip(base*resize(shade,2048)[...,None],0,1);save(base,'m556_basecolor.png')
rough=np.full(ao.shape,.65);spec=np.full(ao.shape,.48);metal=np.zeros(ao.shape)
rough[wing]=.82;spec[wing]=.25;rough[claw]=.48;spec[claw]=.60;rough[eye]=.22;spec[eye]=.9;rough[armor]=.40;spec[armor]=.72;metal[armor]=.45
save(np.stack([spec*(.65+.35*ao),rough,metal],-1),'m556_metal_rough.png')
normal=np.asarray(Image.open(M/'texture_urls_0_normal.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS),float)/127.5-1;normal/=np.maximum(np.linalg.norm(normal,axis=-1,keepdims=True),1e-6);save(normal*.5+.5,'m556_normal.png')
weight=np.asarray(Image.fromarray(np.uint8(green)*255).filter(ImageFilter.GaussianBlur(.65)),float)/255
R.write_mask([weight],T/'m556_region_mask.png')
# The same source coordinates are sampled in all three palettes; cyan background is excluded by the green test.
native=P.parent/'mm8_packed_outline_collection_20261002/families/mm8_m556/native_variants';pixels={pal:[] for pal in [557,558,559]}
for f in sorted(native.glob('*_557.png')):
 a=np.asarray(Image.open(f).convert('RGB'),float)/255;m=(a[...,1]>a[...,0]*1.18)&(a[...,1]>a[...,2]*1.10)&(a[...,1]>.085)
 for pal in pixels:pixels[pal].append(np.asarray(Image.open(str(f).replace('_557.png',f'_{pal}.png')).convert('RGB'),float)[m]/255)
lum=R.srgb_to_linear(resize(base,1024))@R.LUMA;sample=np.sort(lum[(weight>.9)&covered]);lo,hi=np.percentile(sample,[.5,99.5]);stops=np.linspace(lo,hi,16);quantiles=np.searchsorted(sample,stops)/len(sample)
ramps={};native_report={}
for pal,letter in zip(pixels,'abc'):
 a=np.concatenate(pixels[pal]);a=a[np.argsort(R.srgb_to_linear(a)@R.LUMA)];colors=[]
 for q in quantiles:
  center=int(q*(len(a)-1));radius=max(3,len(a)//250);value=np.median(a[max(0,center-radius):center+radius+1],axis=0);colors.append(R.srgb_to_linear(np.clip(value*1.40,0,1)))
 ramps['wasp_'+letter]=[{'range':[float(lo),float(hi)],'colors':np.clip(colors,0,1).tolist()}];native_report[str(pal)]=dict(pixels=len(a),median_srgb=np.median(a,axis=0).tolist())
# One quadrant per real equipment material class. UVs sit in quadrant centers, so no swatch can bleed at a seam.
ebase=np.zeros((128,128,3),float);emr=np.zeros_like(ebase);emask=np.zeros((128,128),float);eclass=np.zeros((128,128),np.uint8)
for swatch,color,mr,label in [(0,(.48,.52,.57),(.88,.31,.85),9),(1,(.10,.32,.17),(.72,.40,.45),9),(2,(.40,.42,.40),(.70,.55,.45),9),(3,(.075,.052,.029),(.25,.82,0),8)]:
 x=(swatch%2)*64;y=(1-swatch//2)*64;ebase[y:y+64,x:x+64]=color;emr[y:y+64,x:x+64]=mr;eclass[y:y+64,x:x+64]=label
 if swatch==1:emask[y:y+64,x:x+64]=1
save(ebase,'m556_equipment_basecolor.png');save(emr,'m556_equipment_metal_rough.png');save(np.full_like(ebase,[.5,.5,1]),'m556_equipment_normal.png');Image.fromarray(eclass).save(T/'m556_equipment_material_classes.png');R.write_mask([emask],T/'m556_equipment_region_mask.png')
config={'variants':list(ramps),'materials':[{'base':'WaspBody','prefix':'WaspBody','mask':'m556_region_mask.png','regions':['native accents'],'ramps':ramps},{'base':'WaspEquipment','prefix':'WaspEquipment','mask':'m556_equipment_region_mask.png','regions':['native accents'],'ramps':ramps}]}
(T/'m556_ramps.json').write_text(json.dumps(config,indent=2));(P/'review/texture_composition.json').write_text(json.dumps(dict(native_palette_samples=native_report,accent_luminance_range=[float(lo),float(hi)],body_pixels=int(covered.sum()),green_pixels=int((green&covered).sum()),classes={str(k):int(((classes==k)&covered).sum()) for k in np.unique(classes)},material_contract='MR.R specular mask, G roughness, B metallic; baked AO in shared base color; separate 128px equipment atlas'),indent=2))
assert len(sample)>100 and np.isfinite(base).all() and np.isfinite(normal).all()
print('COMPOSED',native_report, 'range',lo,hi)
