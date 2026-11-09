"""Native four-region troll tiers, restrained PBR and shared body/head detail."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];repo=P.parents[2];sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
T=P/'textures';T.mkdir(exist_ok=True);N=1024
load=lambda p,mode='RGB',n=N:np.asarray(Image.open(p).convert(mode).resize((n,n),Image.Resampling.LANCZOS),float)/255
save=lambda a,p:Image.fromarray(np.round(np.clip(a,0,1)*255).astype('uint8')).save(p)
def pad(a,c):
 _,ix=ndimage.distance_transform_edt(~c,return_indices=True);out=a[tuple(ix)];out[c]=a[c];return out
def softnormal(a,strength):
 v=a*2-1;v[...,:2]*=strength;v/=np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-5);return v*.5+.5
def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
def linear_to_srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
palettes=[np.frombuffer((repo/f'assets_dev/worlds/mm8/textures/PAL{i}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for i in (481,482,483)]
# Corresponding native indices, sampled from the belly, wrap, crest and mottled back.
regions=[('m480SA0.bmp',(110,110,139,149),range(40,132),1.55),('m480SA0.bmp',(111,157,141,181),range(170,195),1.25),('m480SA0.bmp',(110,51,143,78),range(139,156),1.5),('m480SA4.bmp',(109,93,147,135),range(211,240),1.3)]
native=[]
for file,box,indices,gain in regions:
 a=np.asarray(Image.open(repo/'assets_dev/engine/sprites'/file));x0,y0,x1,y1=box;a=a[y0:y1,x0:x1].ravel();a=a[np.isin(a,list(indices))];assert len(a)>100
 native.append((a[np.argsort(R.luminance(palettes[0][a]))],gain))
variants=['m480_a','m480_b','m480_c'];materials=[];report={}
for layer,part,material in [('UVMap','','TrollPeasant'),('HeadUV','_head','TrollPeasantHead')]:
 m=P/f'meshy/{"head" if part else "body"}_retexture_v1';b=load(m/'texture_urls_0_base_color.png');r=np.load(P/f'work/uvraster_{layer}.npz');g=r['piece'];pos=r['pos'];cov=g>=0
 hsv=np.asarray(Image.fromarray(np.round(np.clip(b,0,1)*255).astype('uint8')).convert('HSV'),float)/255;h,s,v=np.moveaxis(hsv,-1,0)
 cloth=np.isin(g,[1,2,16,17,65]);eyes=np.isin(g,[7,8]);mouth=np.isin(g,[4,5,10]);crest=cov&(g!=0)&~cloth&~eyes&~mouth
 claw=(g==0)&(s<.26)&(v>.6)&(pos[...,2]<1.1)
 ear=(g==0)&(np.abs(pos[...,0])>.075)&(pos[...,2]>1.32)&((h<.035)|(h>.94))&(s>.35)
 back=(g==0)*smooth((pos[...,1]-.015)/.075)*smooth((pos[...,2]-.78)/.15)*smooth((b[...,2]/np.maximum(b[...,0],.01)-.55)/.28)
 skin=((g==0)&~claw&~ear).astype(float)*(1-back)
 masks=[skin,cloth.astype(float),crest.astype(float),back]
 b*= (.82+.18*np.maximum(load(P/f'work/ao_{layer}.png','L'),.4))[...,None]
 spec=np.full((N,N),.25);rough=np.full((N,N),.83);classes=np.ones((N,N),np.uint8)
 for mask,cl,sp,ro in [(cloth,8,.12,.91),(crest,8,.20,.80),(claw,1,.35,.58),(eyes,6,.7,.23),(mouth,1,.35,.55)]:spec[mask]=sp;rough[mask]=ro;classes[mask]=cl
 prefix='m480'+part;save(pad(b,cov),T/f'{prefix}_basecolor_1k.png');save(pad(softnormal(load(m/'texture_urls_0_normal.png'),.3),cov),T/f'{prefix}_normal_1k.png');save(np.stack([pad(spec,cov),pad(rough,cov),np.zeros_like(spec)],-1),T/f'{prefix}_metal_rough_1k.png');classes[~cov]=0;Image.fromarray(classes).save(T/f'{prefix}_material_classes.png')
 masks=[ndimage.gaussian_filter(pad(w,cov),.45) for w in masks];total=np.maximum(sum(masks),1);masks=[w/total for w in masks];R.write_mask(masks,T/f'{prefix}_region_mask.png',size=N)
 ramps={variant:[] for variant in variants};lum=R.luminance(b)
 for j,(samples,gain) in enumerate(native):
  core=cov&(masks[j]>.65)
  lo,hi=0.,1.
  for variant,pal in zip(variants,palettes):
   # Native sprites include baked shadows; transfer their corresponding hues without reapplying that contrast.
   selected=samples[int(len(samples)*.15):max(int(len(samples)*.95),1)]
   reference=R.srgb_to_linear(palettes[0][selected]).mean(0);target=R.srgb_to_linear(pal[selected]).mean(0)
   tone=target/max(float(reference@R.LUMA),1e-5)
   colors=[np.clip(stop*tone*[1.,1.,.7,.85][j],0,1).tolist() for stop in np.linspace(lo,hi,16)]
   ramps[variant].append({'range':[float(lo),float(hi)],'colors':colors})
 for variant in variants:
  base=R.srgb_to_linear(b);out=base*(1-sum(masks))[...,None]
  for w,ramp in zip(masks,ramps[variant]):
   lo,hi=ramp['range'];t=np.clip((lum-lo)/(hi-lo),0,1)*15;i=np.minimum(t.astype(int),14);f=t-i;c=np.asarray(ramp['colors']);out+=w[...,None]*(c[i]*(1-f[...,None])+c[i+1]*f[...,None])
  save(pad(linear_to_srgb(out),cov),T/f'{prefix}_{variant[-1]}_preview.png')
 materials.append({'base':material+'_A','prefix':material,'mask':f'{prefix}_region_mask.png','ramps':ramps});report[layer]={'coverage':int(cov.sum()),'region_core_texels':[int((cov&(w>.65)).sum()) for w in masks],'eyes':int(eyes.sum())}
(T/'m480_ramps.json').write_text(json.dumps({'variants':variants,'materials':materials},indent=2))
m=P/'meshy/club_v1';b=load(m/'texture_urls_0_base_color.png',n=512);normal=load(m/'texture_urls_0_normal.png',n=512);meat=(b[...,0]>b[...,1]*1.4)&(b[...,0]>b[...,2]*1.4)
save(b,T/'m480_club_basecolor.png');save(softnormal(normal,.45),T/'m480_club_normal.png');save(np.stack([np.where(meat,.38,.25),np.where(meat,.57,.73),np.zeros_like(meat)],-1),T/'m480_club_metal_rough.png')
(P/'review/texture_regions.json').write_text(json.dumps(report,indent=2));print(report)
assert report['UVMap']['region_core_texels'][0]>10000 and report['UVMap']['region_core_texels'][1]>1000 and report['HeadUV']['region_core_texels'][2]>1000
