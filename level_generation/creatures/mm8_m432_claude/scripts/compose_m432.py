"""Shared body/head maps, per-class specular, and two native palette regions (sleeves and medallions)."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
T=P/'textures';T.mkdir(exist_ok=True);N=1024
PALS={'m432_a':433,'m432_b':434,'m432_c':435}
def load(path,mode='RGB',size=(N,N)):
 im=Image.open(path).convert(mode);return np.asarray(im.resize(size,Image.Resampling.LANCZOS),float)/255

def save(a,path):Image.fromarray(np.uint8(np.clip(a*255+.5,0,255))).save(path)
def hsv(a):return np.asarray(Image.fromarray(np.uint8(np.clip(a*255,0,255))).convert('HSV'),float)/255

def pad(a,m):
 _,ix=ndimage.distance_transform_edt(~m,return_indices=True);return a[tuple(ix)]
def srgb(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
def grade_skin(img,m):
 lum=R.luminance(img);blur=ndimage.gaussian_filter(np.where(m,lum,0),6)/np.maximum(ndimage.gaussian_filter(m.astype(float),6),1e-5)
 detail=np.clip(lum/np.maximum(blur,1e-5),.55,1.5);col=np.array([133,82,65])/255
 out=img.copy();out[m]=.15*img[m]+.85*srgb(R.srgb_to_linear(col)[None,:]*detail[m,None]);return out
# Palette samples use identical pixels from the original five stored views. The native palette uses indices 88–131 for green cloth and 207–211 for the front disk.
native={r:{k:[] for k in PALS} for r in ['sleeves','medallions']}
for v in range(5):
 ims={k:np.asarray(Image.open(P.parent/f'mm8_m432/native_variants/m432sa{v}_{pal}.png').convert('RGBA'),float)/255 for k,pal in PALS.items()}
 a=ims['m432_a'];indices=np.asarray(Image.open(P.parents[2]/f'assets_dev/engine/sprites/m432Sa{v}.bmp'))
 regions={'sleeves':(indices>=88)&(indices<=131),'medallions':(indices>=207)&(indices<=211)}
 for r,m in regions.items():
  for k in PALS:native[r][k].append(ims[k][m,:3])
for r in native:
 for k in PALS:
  x=np.concatenate(native[r][k]);x=x[R.luminance(x)>.012];assert len(x)>30,(r,k,len(x));native[r][k]=x[np.argsort(R.luminance(x))]
def solid_albedo(img,mask,color):
 lum=R.luminance(img);blur=ndimage.gaussian_filter(np.where(mask,lum,0),5)/np.maximum(ndimage.gaussian_filter(mask.astype(float),5),1e-5)
 detail=np.clip(lum/np.maximum(blur,1e-5),.7,1.2)
 out=img.copy();out[mask]=srgb(R.srgb_to_linear(np.array(color)/255)[None,:]*detail[mask,None]);return out

def ramps(lum,region):
 lo,hi=np.percentile(lum,[2,98]);assert hi>lo
 out={}
 for k in PALS:
  x=native[region][k];cols=[]
  for t in np.linspace(lo,hi,16):
   q=np.searchsorted(np.sort(lum),t)/len(lum);col=x[min(len(x)-1,int(q*(len(x)-1)))];cols.append(R.srgb_to_linear(np.clip(col*1.3,0,1)).tolist())
  out[k]={'range':[float(lo),float(hi)],'colors':cols}
 return out
m=P/'meshy/body_retexture_v1';base=load(m/'texture_urls_0_base_color.png');normal=load(m/'texture_urls_0_normal.png');rough=load(m/'texture_urls_0_roughness.png','L')
r=np.load(P/'work/uvraster_UVMap.npz');gar,pos=r['garment'],r['pos'];cov=gar>=0;h=hsv(base);green=cov&(h[...,0]>.17)&(h[...,0]<.58)&(h[...,1]>.15)&(h[...,2]>.07)
disk=green&(pos[...,1]<-.02)&(abs(pos[...,0])<.15)&(pos[...,2]>1.18)&(pos[...,2]<1.61);cloth=green&~disk
assert cloth.sum()>1000 and disk.sum()>100,(cloth.sum(),disk.sum())
# Hair projected onto the underlying collar is texture spill, not armour pigment.
collar=cov&np.isin(r['piece'],[0,7,8])&(pos[...,2]>1.5)&(abs(pos[...,0])<.17)&(h[...,1]<.2)
base=solid_albedo(base,collar,[48,51,54])
cls=np.zeros((N,N),np.uint8);cls[cov]=9;cls[(gar==0)&(pos[...,2]<1.03)]=8;cls[gar==4]=8;cls[cloth]=8;cls[disk]=11
spec=np.full((N,N),.75);rr=np.full((N,N),.5)
spec[cls==8]=.25;rr[cls==8]=.75;spec[disk]=.55;rr[disk]=.42;spec[gar==6]=1;rr[gar==6]=.3
hair_fragments=np.isin(r['piece'],[45,46,47]);cls[hair_fragments]=2;spec[hair_fragments]=.18;rr[hair_fragments]=.7
rr=np.clip(rr+.25*(rough-ndimage.gaussian_filter(rough,6)),.1,1)
for label,img in [('basecolor',base),('normal',normal),('metal_rough',np.stack([spec,rr,np.zeros_like(rr)],-1))]:save(pad(img,cov),T/f'm432_{label}_1k.png')
Image.fromarray(cls).save(T/'m432_material_classes.png')
R.write_mask([ndimage.gaussian_filter(pad(x.astype(float),cov),.5) for x in [cloth,disk]],T/'m432_region_mask.png',size=N)
rp=[ramps(R.luminance(base[x]),key) for x,key in [(cloth,'sleeves'),(disk,'medallions')]]
config={'variants':list(PALS),'materials':[{'base':'M432_A','prefix':'M432','mask':'m432_region_mask.png','regions':['sleeves','medallions'],'palettes':PALS,'ramps':{k:[r[k] for r in rp] for k in PALS}}]}
# The head has one skin albedo with fine detail preserved; silver hair and eyes retain their own pixels.
m=P/'work/head_uv_repacked';base=load(m/'texture_urls_0_base_color.png');normal=load(m/'texture_urls_0_normal.png');r=np.load(P/'work/uvraster_HeadUV.npz');gar,piece=r['garment'],r['piece'];cov=gar>=0;h=hsv(base)
ear=(abs(r['pos'][...,0])>.065)&(r['pos'][...,2]>1.65)
skin=cov&(piece==1)&(((h[...,1]>.15)&((h[...,0]<.14)|(h[...,0]>.9)))|ear);eye=np.isin(piece,[9,10]);base=grade_skin(base,skin);base=solid_albedo(base,cov&np.isin(piece,[2,11]),[205,210,215])
cls=np.zeros((N,N),np.uint8);cls[cov]=2;cls[skin]=1;cls[eye]=6
spec=np.full((N,N),.18);rr=np.full((N,N),.7);spec[skin]=.4;rr[skin]=.65;spec[eye]=.9;rr[eye]=.22
for label,img in [('basecolor',base),('normal',normal),('metal_rough',np.stack([spec,rr,np.zeros_like(rr)],-1))]:save(pad(img,cov),T/f'm432_head_{label}_1k.png')
Image.fromarray(cls).save(T/'m432_head_material_classes.png')
# Sword: both broad faces intentionally share the symmetric reference. Extend opaque colour into UV padding.
im=Image.open(P/'references_props/sword.png').convert('RGBA').crop((399,20,625,1516));a=np.asarray(im,float)/255;cov=a[...,3]>.9;rgb=pad(a[...,:3],cov)
size=(256,1024);rgb=np.asarray(Image.fromarray(np.uint8(rgb*255)).resize(size,Image.Resampling.LANCZOS),float)/255
h=hsv(rgb);gold=(h[...,0]>.05)&(h[...,0]<.18)&(h[...,1]>.25);rr=np.where(gold,.32,.42);spec=np.where(gold,1,.8)
save(rgb,T/'m432_sword_basecolor.png');save(np.stack([np.full_like(rr,.5),np.full_like(rr,.5),np.ones_like(rr)],-1),T/'m432_sword_normal.png');save(np.stack([spec,rr,np.zeros_like(rr)],-1),T/'m432_sword_metal_rough.png')
Image.fromarray(np.full(rr.shape,9,np.uint8)).save(T/'m432_sword_material_classes.png')
# Map every primitive to tier names, even when its pixels do not change.
for name,prefix in [('M432Head_A','M432Head'),('Sword_A','Sword')]:
 mask=f'{prefix.lower()}_empty_mask.png';Image.new('RGBA',(N,N) if prefix=='M432Head' else (256,1024),(0,0,0,0)).save(T/mask)
 config['materials'].append({'base':name,'prefix':prefix,'mask':mask,'regions':[],'ramps':({k:[r[k] for r in rp] for k in PALS} if prefix=='M432Head' else {k:[] for k in PALS})})
(T/'m432_ramps.json').write_text(json.dumps(config,indent=1)+'\n')
print('TEXTURES',{'body_regions':[int(cloth.sum()),int(disk.sum())],'head_skin':int(skin.sum()),'native_regions':{r:{k:len(x) for k,x in pal.items()} for r,pal in native.items()}})

# Store glTF-convention normals in the editable source as well as runtime exports.
sys.path.insert(0,str(P.parents[2]/'tools'));import normal_map_convention as C
normal_report={}
for path in T.glob('*normal*.png'):
 a=np.array(Image.open(path).convert('RGB'));v=C.measure(a);normal_report[path.name]={'correlation':v,'flipped':v<=-.15}
 if v<=-.15:a[...,1]=255-a[...,1];Image.fromarray(a).save(path)
(P/'review/normal_convention.json').write_text(json.dumps(normal_report,indent=1));print('NORMALS',normal_report)
