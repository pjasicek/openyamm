"""One padded body/head texture set; native palette ramps affect the green costume only."""
from pathlib import Path
import json,sys,math
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure

def load(path,mode='RGB'):return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
def hsv(a):return np.moveaxis(np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255,-1,0)
body=load(P/'texturing/body_maps/texture_urls_0_base_color.png');head=load(P/'meshy/head_retexture_v1/texture_urls_0_base_color.png');bd=np.load(P/'work/uvraster_body.npz');hd=np.load(P/'work/uvraster_head.npz');part,pos=bd['piece'],bd['pos'];hp,hpos=hd['piece'],hd['pos'];cov=part>=0;hc=hp>=0;h,s,v=hsv(body);hh,hs,hv=hsv(head);x,y,z=np.moveaxis(pos,-1,0)
cloth=cov&(part==0)&(z>1.48)&(z<1.82)&(h>.20)&(h<.49)&(s>.22)
gold=cov&(np.isin(part,[1,2,4,6,7,16,20,21,22,25,26,31])|((h>.08)&(h<.18)&(s>.45)&(z>1.48)&(v>.45)))
hgold=hc&(np.isin(hp,[3,8,9,11,13,15])&((hh>.07)&(hh<.2)&(hs>.42)&(hv>.4)))
hair=cov&~np.isin(part,[0,1,2,4,6,7,16,20,21,22,25,26,31,100,101,102]);hhair=hc&(hpos[...,1]>.07)&~hgold
skin=cov&(part==0)&(z>1.28)&(z<1.68)&(h<.12)&(s>.12)&~gold&~cloth
hskin=hc&(hp==0)&(hpos[...,1]<.04)&(hh<.12)&(hs>.12)&(hv>.30)&~hgold
assert cloth.sum()>1500 and skin.sum()>3000 and hskin.sum()>10000,(cloth.sum(),skin.sum(),hskin.sum())
# Match tan face and exposed torso in linear light; jewelry and hair are excluded.
gain=float(np.clip(np.median(R.luminance(body[skin]))/np.median(R.luminance(head[hskin])),.75,1.3));lin=R.srgb_to_linear(head);lin[hskin]*=gain;head=np.where(lin<=.0031308,12.92*lin,1.055*np.maximum(lin,0)**(1/2.4)-.055)
# The cropped head paint darkened its open neck border. Match that strip to the body and restore the native choker.
neck_body=cov&(part==0)&(z>1.74)&(z<1.815)&(np.abs(x+.025)<.12)&(y<.08)&~gold
neck_color=np.median(body[neck_body],axis=0);hz=hpos[...,2];blend=np.clip((1.94-hz)/.10,0,1)*(hc&(hp==0)&(hpos[...,1]<.12));head=head*(1-blend[...,None])+neck_color*blend[...,None]
choker=cov&(part==0)&(z>1.805)&(z<1.855)&(np.abs(x+.025)<.15)&(y<.13)
hchoker=hc&(hp==0)&(hz>1.805)&(hz<1.855)&(np.abs(hpos[...,0]+.025)<.15)&(hpos[...,1]<.13)
for img,mask,zz in [(body,choker,z),(head,hchoker,hz)]:
    shade=.82+.18*np.cos((zz-1.83)*math.pi/.05);img[mask]=np.array([.83,.62,.22])*shade[mask,None]
gold|=choker;hgold|=hchoker;hhair=hc&~np.isin(hp,[0,3,8,9,11,13,15]);eyes=hc&np.isin(hp,[8,9]);hgold&=~eyes
pals={key:np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm8/textures/pal{pid}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for key,pid in [('naga_a',625),('naga_b',626),('naga_c',627)]}
# Index correspondence is exact in the original sprite palettes; these are the costume's green ramp.
idx=np.arange(256);a=pals['naga_a'];select=(idx>=11)&(idx<=33)&(a[:,1]>a[:,0]*1.12)&(a[:,1]>a[:,2]*1.12)
native=Image.open(P.parent/'mm8_packed_outline_collection_20261002/families/mm8_m624/native_variants/m624sa0_625.png').convert('RGBA');pixels=np.asarray(native);lut={tuple(c):i for i,c in enumerate(np.uint8(a*255+.5))};used=np.array([lut.get(tuple(c),0)for c in pixels[pixels[...,3]>0,:3]]);ids=used[select[used]];assert len(ids)>60
lum=R.luminance(body[cloth]);lo,hi=np.percentile(lum,[1,99]);ramps={};W=np.array([.2126,.7152,.0722]);base=R.srgb_to_linear(pals['naga_a'][ids]);base_mean=np.median(base,axis=0);base_lum=float(base_mean@W)
for key,pal in pals.items():
 colors=R.srgb_to_linear(pal[ids]);mean=np.median(colors,axis=0);tint=mean/max(base_lum,1e-6);ramps[key]=[{'range':[float(lo),float(hi)],'colors':[np.clip(tint*(lo+i/15*(hi-lo)),0,1).tolist()for i in range(16)]}]
report={'cloth_texels':int(cloth.sum()),'native_costume_samples':len(ids),'head_skin_linear_gain':gain,'normal_convention':{}}
for label,img,covered,metal,hairmask,region in [('body',body,cov,gold,hair,cloth),('head',head,hc,hgold,hhair,np.zeros_like(hskin))]:
 prefix=(P/'texturing/body_maps/texture_urls_0')if label=='body'else(P/'meshy/head_retexture_v1/texture_urls_0');rough=load(str(prefix)+'_roughness.png','L');normal=load(str(prefix)+'_normal.png');score=measure(np.uint8(normal*255+.5));assert abs(score)>.15,score
 if score<0:normal[...,1]=1-normal[...,1]
 report['normal_convention'][label]=score
 ao=load(T/f'naga_{label}_ao.png','L');ao=pad(ao,covered);ao=ndimage.gaussian_filter(ao,1.5);img*=np.maximum(.72,1-.45*(1-ao))[...,None]
 classes=np.ones((N,N),np.uint8);classes[~covered]=0;classes[hairmask]=2;classes[region]=8;classes[metal]=9
 # Full-metal gold stays bright enough to reflect, while skin and cloth stay dielectric.
 img[metal]=np.clip(img[metal]*np.array([1.12,1.05,.94]),0,1)
 spec=np.full((N,N),.25);rg=np.clip(.80+.16*(rough-.5),.70,.90);met=np.zeros((N,N));spec[hairmask]=0;rg[hairmask]=.9;spec[region]=.3;rg[region]=.75;spec[metal]=1;rg[metal]=np.clip(.38+.14*(rough[metal]-.5),.30,.45);met[metal]=1
 if label=='head':classes[eyes]=6;spec[eyes]=1;rg[eyes]=.18;met[eyes]=0
 save(pad(img,covered),T/f'naga_{label}_basecolor_1k.png');save(pad(normal,covered),T/f'naga_{label}_normal_1k.png');save(pad(np.stack([spec,rg,met],-1),covered),T/f'naga_{label}_metal_rough_1k.png');R.write_mask([ndimage.gaussian_filter(pad(region.astype(float),covered),.65)],T/f'naga_{label}_region_mask.png',size=N);Image.fromarray(classes).save(T/f'naga_{label}_material_classes.png');overlay=img*.3;overlay[region]=(0,.8,.2);overlay[metal]=(1,.7,0);save(overlay,P/f'review/naga_{label}_regions.png')
cfg={'variants':list(pals),'palettes':{'naga_a':625,'naga_b':626,'naga_c':627},'report':report,'materials':[{'base':name+'_A','prefix':name,'mask':f'naga_{label}_region_mask.png','regions':['costume'],'ramps':ramps}for label,name in [('body','Naga'),('head','NagaHead')]]};(T/'naga_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');print(json.dumps(report));assert np.isfinite(body).all()and np.isfinite(head).all()
