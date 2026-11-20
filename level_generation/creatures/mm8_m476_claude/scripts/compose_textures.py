"""Shared troll maps; native palette ramps affect only the green cloth edging."""
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared'));import region_variants as R
T=p/'textures';T.mkdir(exist_ok=True);N=1024
PALS={'troll_a':477,'troll_b':478,'troll_c':479};SKIN=np.array([154,142,67])/255

def load(path,mode='RGB'):
 return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),dtype=float)/255

def save(a,path):Image.fromarray(np.clip(a*255+.5,0,255).astype('uint8')).save(path,optimize=True)
def hsv(a):
 q=np.asarray(Image.fromarray(np.clip(a*255,0,255).astype('uint8')).convert('HSV'),dtype=float)/255
 return q[:,:,0]*360,q[:,:,1],q[:,:,2]
def pad(a,cov):
 _,(iy,ix)=ndimage.distance_transform_edt(~cov,return_indices=True);return a[iy,ix]
def encode(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
def skin_grade(base,skin):
 lum=R.luminance(base);blur=ndimage.gaussian_filter(np.where(skin,lum,0.),6)/np.maximum(ndimage.gaussian_filter(skin.astype(float),6),1e-5)
 detail=np.clip(lum/np.maximum(blur,1e-4),.5,1.5);out=base.copy();paint=encode(R.srgb_to_linear(SKIN)*detail[skin,None]);out[skin]=.12*base[skin]+.88*paint;return out
materials=[];report={};ramps=None
for layer,job,suffix in [('UVMap','body_retexture_v1',''),('HeadUV','head_retexture_v1','_head')]:
 z=np.load(p/f'work/uvraster_{layer}.npz');pc=z['piece'];pos=z['pos'];cov=pc>=0
 src=p/'meshy'/job;base=load(src/'texture_urls_0_base_color.png');normal=load(src/'texture_urls_0_normal.png');rough=load(src/'texture_urls_0_roughness.png','L');h,s,v=hsv(base)
 trim=cov&(h>80)&(h<170)&(s>.35)
 if not suffix:
  metal=cov&(((pc==1)&(pos[:,:,2]<.40))|(np.isin(pc,[2,3])&(s<.25)&(pos[:,:,2]>1.05)))
  skin=cov&np.isin(pc,[0,2,3])&(h>35)&(h<85)&(s>.2)&(v>.18)&~metal
  hair=np.zeros_like(cov);eye=np.zeros_like(cov);bone=np.zeros_like(cov)
 else:
  metal=np.zeros_like(cov);skin=cov&(pc==0)&(h>15)&(h<95)&(s>.18)&(v>.15)
  hair=cov&(pc>=20);eye=cov&np.isin(pc,[5,6]);bone=cov&(pc>=7)&(pc<=19)
 g=skin_grade(base,skin)
 # Native iron is dark grey; retain the returned relief without white boot plates.
 g[metal]*=.62
 if hair.any():g[hair]*=np.array([33,28,24])/255/np.maximum(np.median(base[hair],axis=0),.02)
 g=np.clip(g,0,1);spec=np.full((N,N),.25);rgh=np.full((N,N),.80)
 for mask,sp,ro in [(skin,.28,.68),(metal,.65,.52),(trim,.18,.88),(hair,.12,.85),(eye,.8,.23),(bone,.4,.63)]:
  spec[mask]=sp;rgh[mask]=np.clip(ro+.35*(rough[mask]-np.median(rough[mask])) if mask.any() else ro,.15,.98)
 save(pad(g,cov),T/f'troll{suffix}_basecolor_1k.png');save(pad(normal,cov),T/f'troll{suffix}_normal_1k.png');save(np.stack([pad(spec,cov),pad(rgh,cov),np.zeros((N,N))],-1),T/f'troll{suffix}_metal_rough_1k.png')
 mask=ndimage.gaussian_filter(pad(trim.astype(float),cov),.65);mask[cov&~trim]=0
 R.write_mask([mask],T/f'troll{suffix}_region_mask.png',size=N)
 report[layer]={'skin_texels':int(skin.sum()),'trim_texels':int(trim.sum()),'metal_texels':int(metal.sum()),'original_skin_median':np.median(base[skin],axis=0).tolist()}
 if not suffix:
  assert trim.sum()>1000,'Missing native tier trim'
  lum=R.luminance(g[trim]);lo,hi=np.percentile(lum,[2,98]);srt=np.sort(lum)
  pals={k:np.frombuffer(Path(f'assets_dev/worlds/mm8/textures/Pal{v}.act').read_bytes()[:768],dtype='uint8').reshape(256,3)/255 for k,v in PALS.items()}
  changed=(np.abs(pals['troll_a']-pals['troll_b']).max(1)>.03)|(np.abs(pals['troll_a']-pals['troll_c']).max(1)>.03)
  idx=np.concatenate([np.asarray(Image.open(Path('assets_dev/engine/sprites')/f'm476Sa{v}.bmp')).ravel() for v in range(5)])
  ph,ps,pv=hsv(pals['troll_a'][None,:,:]);green=(ph[0]>80)&(ph[0]<170)&(ps[0]>.35)
  idx=idx[(idx!=0)&changed[idx]&green[idx]];assert len(idx)>500;ramps={} 
  for k,pal in pals.items():
   colors=pal[idx];ll=R.luminance(colors);colors=colors[ll>.025];colors=colors[np.argsort(R.luminance(colors))];ramp=[]
   for i in range(16):
    q=np.searchsorted(srt,lo+(hi-lo)*i/15)/len(srt);c=colors[min(len(colors)-1,int(q*(len(colors)-1)))];ramp.append(R.srgb_to_linear(np.clip(c*1.25,0,1)).tolist())
   ramps[k]=[{'range':[float(lo),float(hi)],'colors':ramp}]
 materials.append({'base':'TrollHead_A' if suffix else 'Troll_A','prefix':'TrollHead' if suffix else 'Troll','mask':f'troll{suffix}_region_mask.png','regions':['trim'],'palettes':PALS,'ramps':ramps})
# The club has one unchanged texture set for every tier.
src=p/'meshy/club_geometry_v1';base=load(src/'texture_urls_0_base_color.png');h,s,v=hsv(base);skull=(s<.3)&(v>.30)
save(base,T/'troll_club_basecolor_1k.png');save(load(src/'texture_urls_0_normal.png'),T/'troll_club_normal_1k.png')
save(np.stack([np.where(skull,.40,.25),np.where(skull,.65,.78),np.zeros((N,N))],-1),T/'troll_club_metal_rough_1k.png')
R.write_mask([np.zeros((N,N))],T/'troll_club_region_mask.png',size=N)
materials.append({'base':'Club_A','prefix':'Club','mask':'troll_club_region_mask.png','regions':['trim'],'ramps':ramps})
(T/'troll_ramps.json').write_text(json.dumps({'variants':list(PALS),'materials':materials},indent=2))
(T/'texture_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
