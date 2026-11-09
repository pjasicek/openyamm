"""Native MM8 palette ramps and per-surface specular/roughness on shared 1K texture sets."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
SURFACE={'skin':(.40,.58),'cloth':(.15,.84),'steel':(.85,.40),'chain':(.62,.64),'gold':(1,.34),'eye':(.8,.22),'under':(.22,.82)}
def load(p,mode='RGB',size=(N,N)):
 im=Image.open(p).convert(mode)
 if size and im.size!=size:im=im.resize(size,Image.Resampling.LANCZOS)
 return np.asarray(im,float)/255
def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p)
def hsv(a):return np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255
sets={};report={}
for part,layer,material in [('body','UVMap','DragonHunter_A'),('head','HeadUV','DragonHunterHead_A')]:
 src=P/'meshy'/f'{part}_retexture_v1';r=np.load(P/'work'/f'uvraster_{layer}.npz');pc,pos=r['piece'],r['pos'];cov=pc>=0
 base=load(src/'texture_urls_0_base_color.png');normal=load(src/'texture_urls_0_normal.png');rough=load(src/'texture_urls_0_roughness.png','L')
 # The return painted two symmetric steel shells brown. Reproject the matching silver shell's albedo and roughness.
 if part=='body':
  for source,target in [((pc==2)&(pos[:,:,0]<-.04),(pc==0)&(pos[:,:,2]<.94)&(pos[:,:,0]>.06)),(pc==9,pc==10)]:
   points=pos[target].copy();points[:,0]*=-1;dist,ix=cKDTree(pos[source]).query(points)
   base[target]=base[source][ix];rough[target]=rough[source][ix]
   report.setdefault('mirrored_surface_mm',[]).append({'p50':float(np.median(dist)*1000),'p99':float(np.percentile(dist,99)*1000)})
 h=hsv(base);gold=np.isin(pc,[12,13,14,19,24,25,26])|((pc==3)&(h[:,:,0]>.05)&(h[:,:,0]<.16)&(h[:,:,1]>.25))
 # Thin painted gold rims stay protected; their width is bounded to the armour's ends.
 rim=np.isin(pc,[9,10])&((pos[:,:,2]<.91)|(pos[:,:,2]>1.065))|np.isin(pc,[15,16,27,28])
 gold|=rim&(h[:,:,0]>.045)&(h[:,:,0]<.16)&(h[:,:,1]>.3)&(h[:,:,2]>.23)
 cloth=(pc==11)|((pc==0)&(pos[:,:,1]<-.075)&(pos[:,:,2]>.94)&(pos[:,:,2]<1.075)&(abs(pos[:,:,0])<np.where(pos[:,:,2]>.92,.15,.10)))
 cls={'skin':pc==1,'eye':np.isin(pc,[29,30]),'cloth':cloth,'gold':gold&~cloth,'chain':np.isin(pc,[6,7]),'under':pc==35}
 cls['steel']=cov&~np.any(list(cls.values()),axis=0)
 graded=base.copy();lum=base@np.array([.2126,.7152,.0722])
 # One steel family across body and helm; retain texture scratches and shading, remove the accidental brown hue.
 steel=cls['steel'];graded[steel]=lum[steel,None]*np.array([.94,1.0,.97])
 skin=cls['skin'];graded[skin]=np.clip(base[skin]*1.16,0,1)
 under=cls['under'];graded[under]=np.clip(lum[under,None]*np.array([.38,.42,.40]),.025,.20)
 # Cloth albedo uses the same range before the shared crest/waist tier ramp is applied.
 if cloth.any():
  L=R.luminance(graded)[cloth];graded[cloth]*=(.09/max(float(np.median(L)),.002))**(1/2.2)
 ao=load(P/'work'/f'ao_{layer}.png','L');graded[cov]*=(.78+.22*np.maximum(ao[cov],.4))[:,None]
 ix=nd.distance_transform_edt(~cov,return_distances=False,return_indices=True)
 spec=np.zeros(pc.shape);rg=np.zeros(pc.shape)
 for key,m in cls.items():
  if not m.any():continue
  a,b=SURFACE[key];spec[m]=a;rg[m]=np.clip(b+.18*(rough[m]-np.median(rough[m])),.2,1)
 masks=[nd.gaussian_filter(m.astype(float)[tuple(ix)],.5) for m in [cloth,steel]]
 graded=graded[tuple(ix)];normal=normal[tuple(ix)]
 save(graded,T/f'{part}_basecolor.png');save(normal,T/f'{part}_normal.png');save(np.stack([spec[tuple(ix)],rg[tuple(ix)],np.zeros(pc.shape)],-1),T/f'{part}_orm.png');R.write_mask(masks,T/f'{part}_region_mask.png',N)
 sets[part]={'base':graded,'masks':masks,'material':material,'core':[cloth,steel]};report[part]={'classes':{k:int(v.sum()) for k,v in cls.items()},'median_steel':float(np.median(R.luminance(graded)[steel]))}
# Native palette rows are weighted by their actual use in the five standing views.
pals={f'dragon_hunter_{s}':np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm8/textures/Pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for s,n in [('a',457),('b',458),('c',459)]}
counts=np.zeros(256,int)
for f in (P.parents[2]/'assets_dev/engine/sprites').glob('m456Sa*.bmp'):counts+=np.bincount(np.asarray(Image.open(f)).ravel(),minlength=256)
a=pals['dragon_hunter_a'];sat=(a.max(1)-a.min(1))/np.maximum(a.max(1),.001);changed=np.any(a!=pals['dragon_hunter_b'],1)|np.any(a!=pals['dragon_hunter_c'],1)
regions=[changed&(sat>.35)&(a[:,1]>a[:,0]*1.15),changed&(sat<=.35)]
ramps={k:[] for k in pals}
for channel,m in enumerate(regions):
 ids=np.repeat(np.where(m)[0],counts[m]);ids=ids[np.argsort(R.luminance(a[ids]))];native_lum=R.luminance(a[ids]);valid=native_lum>.005;ids=ids[valid];native_lum=native_lum[valid]
 lum=np.concatenate([R.luminance(v['base'])[v['core'][channel]] for v in sets.values()]);lo,hi=np.percentile(lum,[1,99]);median=float(np.median(lum));native_mid=float(np.median(native_lum))*1.35
 for key,pal in pals.items():
  colors=[]
  for value in np.linspace(lo,hi,16):
   target=native_mid*(value/max(median,.001))**(.90 if channel==1 else 1)
   q=float(np.clip(np.searchsorted(np.sort(lum),value)/len(lum),.02,.98));i=int(q*(len(ids)-1));window=max(4,len(ids)//30);c=np.median(R.srgb_to_linear(pal[ids[max(0,i-window):i+window+1]]),0);c*=target/max(float(c@R.LUMA),.001)
   colors.append(np.clip(c,0,1).round(6).tolist())
  ramps[key].append({'range':[float(lo),float(hi)],'colors':colors})
 report.setdefault('native_regions',[]).append({'channel':channel,'pixels':len(ids),'native_median_linear':native_mid,'texture_median_linear':median})
cfg={'variants':list(pals),'materials':[{'base':v['material'],'prefix':v['material'][:-2],'mask':f'{part}_region_mask.png','regions':['crest_waist','tinted_steel'],'ramps':ramps} for part,v in sets.items()]}
(T/'dragon_hunter_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
# Shared sword material: the blade keeps its native dark steel while hilt and leather retain their reference colours.
source=np.asarray(Image.open(P/'references_props/sword.png').convert('RGBA'))[25:1507,400:624];valid=source[:,:,3]>128;ix=nd.distance_transform_edt(~valid,return_distances=False,return_indices=True);prop=np.asarray(Image.fromarray(source[:,:,:3][tuple(ix)]).resize((256,1024),Image.Resampling.LANCZOS),float)/255;rows=np.arange(1024)[:,None];blade=rows<((1170-25)/(1507-25)*1024);blade=np.broadcast_to(blade,prop.shape[:2]);L=prop@np.array([.2126,.7152,.0722]);prop[blade]=L[blade,None]*np.array([.65,.70,.67]);save(prop,T/'props/sword_basecolor.png');orm=np.empty(prop.shape);orm[:]=[.95,.38,0];orm[(rows>830).repeat(256,axis=1)]=[.3,.75,0];save(orm,T/'props/sword_orm.png');Image.new('RGB',(256,1024),(128,128,255)).save(T/'props/sword_normal.png')
report['contract']='ORM: R specular class, G roughness, B zero metallic; shared body/head ramps; native gold/skin protected.'
(T/'texture_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
