"""Shared 1K albedo/normal/specular-roughness sets and native palette ramps, no baked tier copies."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as nd
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024
sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as R
SURFACE={'skin':(.3,.6),'cloth':(.12,.84),'leather':(.4,.62),'steel':(.85,.32),'gold':(.9,.34),'hair':(.15,.75),'other':(.3,.6)}
def load(p,mode='RGB',size=(N,N)):
 im=Image.open(p).convert(mode)
 if size and im.size!=size:im=im.resize(size,Image.Resampling.LANCZOS)
 return np.asarray(im,dtype=float)/255
def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p)
def hsv(a):return np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255
sets={}
for part,layer,material in [('body','UVMap','Pirate_A'),('head','HeadUV','PirateHead_A')]:
 src=P/'meshy'/f'{part}_retexture_v1';r=np.load(P/'work'/f'uvraster_{layer}.npz');pc,pos=r['piece'],r['pos'];cov=pc>=0
 base=load(src/'texture_urls_0_base_color.png');normal=load(src/'texture_urls_0_normal.png');rough=load(src/'texture_urls_0_roughness.png','L')
 h=hsv(base);green=(h[:,:,0]>.16)&(h[:,:,0]<.46)&(h[:,:,1]>.25)
 region=(np.isin(pc,[4,11,12,19])|((pc==2)&green&(pos[:,:,2]>.98)))&cov
 skin=(pc==3)|((pc==1)&(h[:,:,0]>.025)&(h[:,:,0]<.13)&(h[:,:,2]>.28)&(h[:,:,1]>.16)&(h[:,:,1]<.77))
 cls={'skin':skin,'cloth':np.isin(pc,[0,2,4,9,10,11,12,19]),'leather':np.isin(pc,[5,6,24]),'steel':pc==7,'gold':np.isin(pc,[17,18,20,21,22,23]),'hair':(pc==1)&~skin}
 cls['other']=cov&~np.any(list(cls.values()),axis=0)
 graded=base.copy()
 # Remove broad baked highlights from skin, retaining small facial/hand detail and darker beard/strap pixels.
 m=cls['skin'];lum=base@np.array([.2126,.7152,.0722]);w=nd.gaussian_filter(m.astype(float),12)
 smooth=nd.gaussian_filter(lum*m,12)/np.maximum(w,1e-6)
 detail=np.clip(lum/np.maximum(smooth,.02),.70,1.22)
 target=np.array([169,121,84])/255
 graded[m]=target*detail[m,None]
 for mask,tgt in [(np.isin(pc,[0,9,10]),[188,185,178]),((pc==2)&~region,[102,102,108])]:
  if mask.any():graded[mask]=base[mask]*np.array(tgt)/255/np.maximum(np.median(base[mask],axis=0),.01)
 # Stray green paint below the actual waist sash belongs to the grey trousers.
 stray=(pc==2)&green&~region
 graded[stray]=(graded[stray]@np.array([.2126,.7152,.0722]))[:,None]*np.array([1,1,1.06])
 # Match green cloth brightness across body, head and weapon before sharing one lookup ramp.
 if region.any():graded[region]*=(.19/np.median(R.luminance(graded)[region]))**(1/2.2)
 idx=nd.distance_transform_edt(~cov,return_distances=False,return_indices=True)
 graded=graded[tuple(idx)];normal=normal[tuple(idx)]
 spec=np.zeros(pc.shape);rgh=np.zeros(pc.shape)
 for k,m in cls.items():
  if not m.any():continue
  a,b=SURFACE[k];spec[m]=a;rgh[m]=np.clip(b+.25*(rough[m]-np.median(rough[m])),.2,1)
 orm=np.stack([spec[tuple(idx)],rgh[tuple(idx)],np.zeros(pc.shape)],-1)
 mask=region.astype(float)[tuple(idx)]
 # A one-texel soft edge blends the textured belt's colour boundaries, with islands padded before filtering.
 mask=nd.gaussian_filter(mask,.55)
 save(graded,T/f'{part}_basecolor.png');save(normal,T/f'{part}_normal.png');save(orm,T/f'{part}_orm.png')
 R.write_mask([mask],T/f'{part}_region_mask.png',N)
 sets[part]={'base':graded,'mask':mask,'material':material,'region':region}
 print(part,{k:int(v.sum()) for k,v in cls.items()},'recolour',int(region.sum()))
prop=load(T/'props/cutlass_basecolor.png',size=None);pm=load(T/'props/cutlass_region_mask.png','RGBA',None)[:,:,0]
prop[pm>.5]*=(.19/np.median(R.luminance(prop)[pm>.5]))**(1/2.2)
save(prop,T/'props/cutlass_basecolor.png')
sets['props/cutlass']={'base':prop,'mask':pm,'material':'PirateCutlass_A','region':pm>.9}
pals={k:np.frombuffer(Path(f'assets_dev/worlds/mm8/textures/pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,n in [('pirate_a',413),('pirate_b',414),('pirate_c',415)]}
counts=np.zeros(256,int)
for f in (P/'native').glob('m412Sa*.bmp'):counts+=np.bincount(np.asarray(Image.open(f)).ravel(),minlength=256)
a=pals['pirate_a'];valid=(a[:,1]>a[:,0]*1.25)&(a[:,1]>a[:,2]*1.3)&(a[:,1]>.12)&(counts>0)
indices=np.repeat(np.where(valid)[0],counts[valid]);indices=indices[np.argsort(R.luminance(a[indices]))]
lum=np.sort(np.concatenate([R.luminance(v['base'])[v['region']] for v in sets.values()]));lo,hi=np.percentile(lum,[2,98])
ramps={}
for key,pal in pals.items():
 colors=[];lin=R.srgb_to_linear(pal[indices])
 for t in np.linspace(lo,hi,16):
  q=np.clip(np.searchsorted(lum,t)/len(lum),.02,.98);c=int(q*(len(lin)-1));w=max(4,len(lin)//40)
  colors.append(np.clip(np.median(lin[max(0,c-w):c+w],0)*1.35,0,1).round(6).tolist())
 ramps[key]=[{'range':[float(lo),float(hi)],'colors':colors}]
cfg={'variants':list(pals),'materials':[]}
for part,v in sets.items():
 cfg['materials'].append({'base':v['material'],'prefix':v['material'][:-2],'mask':f'{part}_region_mask.png','regions':['bandanna_sash_grip'],'ramps':ramps})
 assert v['mask'].max()>.99
(T/'pirate_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
(T/'texture_report.json').write_text(json.dumps({'native_colour_pixels':len(indices),'ramp_gain_linear':1.35,'shared_ramp_range':[lo,hi],'skin_target_srgb':[169,121,84],'roughness_contract':'R specular mask; G roughness; B zero metallic'},indent=2)+'\n')
