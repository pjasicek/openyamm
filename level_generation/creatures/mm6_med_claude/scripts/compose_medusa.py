"""Native palette ramps and shared PBR maps for the Medusa family."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024;W=np.array([.2126,.7152,.0722])
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
paldir=P.parents[2]/'assets_dev/worlds/mm6/textures';palettes={'med_a':769,'med_b':250,'med_c':251};pals={k:np.frombuffer((paldir/f'pal{v}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,v in palettes.items()}
def load(path,mode='RGB'):return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
def hsv(a):return np.moveaxis(np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255,-1,0)
body=load(P/'meshy/body_retexture_v2/texture_urls_0_base_color.png');head=load(P/'meshy/head_retexture_v1/texture_urls_0_base_color.png');bd=np.load(P/'work/uvraster_body.npz');hd=np.load(P/'work/uvraster_head.npz');part,pos=bd['piece'],bd['pos'];hp,hpos=hd['piece'],hd['pos'];cov=part>=0;hc=hp>=0;h,s,v=hsv(body);hh,hs,hv=hsv(head);x,y,z=np.moveaxis(pos,-1,0)
gold=cov&(h>.105)&(h<.19)&(s>.4)&(v>.44)
armor=cov&(part==0)&(z>1.31+.7*np.abs(x))&(z<1.74)&(h<.145)&~gold
belly=cov&(part==0)&(z<1.35)&(s<.27)&~gold
skin=cov&(h>.135)&(h<.41)&(s>.08)&~gold&~armor&~belly
# The lowest collar lip was projected as skin; it is a continuation of the gold neck rings.
hgold=hc&(hh>.095)&(hh<.19)&(hs>.4)&(hv>.4);collar=(hp==106)&(hpos[...,2]<1.814);hgold|=np.isin(hp,[121,123])|collar
ref=head[hgold&~collar];gold_rgb=np.median(ref,axis=0);detail=R.luminance(head[collar]);detail=(detail/max(float(np.median(detail)),1e-6))**.25;head[collar]=gold_rgb*detail[:,None]
tongues=np.isin(hp,[100,110,114,119,127,129,130,131,132]);eyes=np.isin(hp,[101,104]);snake_eyes=hc&~np.isin(hp,[106,121,123])&(hs>.48)&(hh>.075)&(hh<.16)&(hv>.35)
hskin=hc&(hh>.13)&(hh<.41)&~hgold&~tongues&~eyes&~snake_eyes
# A collar separates the sets; match the green skin distributions, never the gold collar to the body.
gain=float(np.clip(np.median(R.luminance(body[skin]))/np.median(R.luminance(head[hskin])),.7,1.3));linear=R.srgb_to_linear(head);linear[hskin]*=gain;head=np.where(linear<=.0031308,12.92*linear,1.055*np.maximum(linear,0)**(1/2.4)-.055)
assert armor.sum()>2000 and belly.sum()>5000 and skin.sum()>10000 and hskin.sum()>50000
# Palette indices from retained original native pixels. Source BMP inventory paths are archived.
lut={tuple(c):i for i,c in enumerate(np.uint8(pals['med_b']*255+.5))};used=[];front=[]
for view in range(5):
 a=np.asarray(Image.open(P.parent/'mm6_med/native_variants'/f'medstaa{view}_250.png'));idx=np.array([lut.get(tuple(c),0) for c in a[a[...,3]>0,:3]]);used.extend(idx)
 if view==0:front.extend(idx)
used=np.array(used);front=np.array(front);idx=np.arange(256);r,g,b=pals['med_b'].T
select=[(idx>=180)&(b>r+.025)&(b>g+.025),(idx>=180)&(idx<=237)&(np.ptp(pals['med_b'],axis=1)<.01),(g>r*1.1)&(g>b*1.1)&(pals['med_b'].max(1)>.1)]
regions=[('armor',armor,np.zeros_like(hskin)),('belly',belly,np.zeros_like(hskin)),('skin',skin,hskin)];ramps={k:[] for k in pals};report={}
for ch,(name,bm,hm) in enumerate(regions):
 ids=(front if name=='belly' else used);ids=ids[select[ch][ids]];assert len(ids)>100;lum=np.r_[R.luminance(body[bm]),R.luminance(head[hm])];lo,hi=np.percentile(lum,[1,99]);assert hi>lo
 for key,pal in pals.items():
  colors=R.srgb_to_linear(pal[ids]);order=np.argsort(colors@W);colors=colors[order];middle=colors[len(colors)//4:3*len(colors)//4];native=np.median(middle,axis=0)*(1.55 if name=='skin' else 1.35);chroma=native/max(float(native@W),1e-8);k=float(native@W)/max(float(np.median(lum)),1e-8);ramp={'range':[float(lo),float(hi)],'colors':[np.clip(chroma*(lo+j/15*(hi-lo))*k,0,1).tolist() for j in range(16)]};ramps[key].append(ramp)
 report[name]={'body_texels':int(bm.sum()),'head_texels':int(hm.sum()),'native_samples':len(ids),'range':[float(lo),float(hi)]}
for label,img,covered,metal_mask,region_masks in [('body',body,cov,gold,[armor,belly,skin]),('head',head,hc,hgold,[np.zeros_like(hskin),np.zeros_like(hskin),hskin])]:
 job='body_retexture_v2' if label=='body' else 'head_retexture_v1';prefix=P/'meshy'/job/'texture_urls_0';rough=load(str(prefix)+'_roughness.png','L');normal=load(str(prefix)+'_normal.png');spec=np.full((N,N),.28);rg=np.clip(.64+.25*(rough-.5),.4,.85);metal=np.zeros((N,N));spec[metal_mask]=.8;rg[metal_mask]=np.clip(.34+.25*(rough[metal_mask]-.5),.25,.5);metal[metal_mask]=.55
 if label=='body':spec[armor]=.35;rg[armor]=np.clip(.57+.2*(rough[armor]-.5),.4,.75);metal[armor]=.12
 else:spec[eyes|snake_eyes]=.65;rg[eyes|snake_eyes]=.24;spec[tongues]=.35;rg[tongues]=.5
 assert measure(np.uint8(normal*255+.5))<-.15,'Review changed normal-map convention';normal[...,1]=1-normal[...,1]
 save(pad(img,covered),T/f'med_{label}_basecolor_1k.png');save(pad(normal,covered),T/f'med_{label}_normal_1k.png');save(np.stack([pad(spec,covered),pad(rg,covered),pad(metal,covered)],-1),T/f'med_{label}_metal_rough_1k.png');masks=[ndimage.gaussian_filter(pad(m.astype(float),covered),.65) for m in region_masks];R.write_mask(masks,T/f'med_{label}_region_mask.png',size=N);classes=np.zeros((N,N),np.uint8);classes[covered]=1;classes[metal_mask]=9
 if label=='body':classes[armor]=8
 else:classes[eyes|snake_eyes]=6;classes[tongues]=7
 Image.fromarray(classes).save(T/f'med_{label}_material_classes.png')
 overlay=img*.25
 for mask,color in zip(region_masks,[(1,.18,.10),(.15,.4,1),(.1,.85,.2)]):overlay[mask]=color
 overlay[metal_mask]=(1,.8,.1);save(overlay,P/'review'/f'med_{label}_regions.png')
cfg={'variants':list(pals),'palettes':palettes,'report':report,'head_skin_linear_gain':gain,'materials':[{'base':name+'_A','prefix':name,'mask':f'med_{label}_region_mask.png','regions':[x[0] for x in regions],'ramps':ramps} for label,name in [('body','Medusa'),('head','MedusaHead')]]};(T/'med_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');print('COMPOSE',json.dumps(report),'head gain',gain)
assert np.isfinite(body).all() and np.isfinite(head).all()
