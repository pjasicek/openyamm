"""Shared Necromancer PBR maps and native green/blue/red rune and iris ramps."""
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared'));import region_variants as R
T=p/'textures';T.mkdir(exist_ok=True);N=1024
PALS={'necromancer_a':473,'necromancer_b':474,'necromancer_c':475}
def load(path,mode='RGB'):return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),dtype=float)/255
def save(a,path):Image.fromarray(np.clip(a*255+.5,0,255).astype('uint8')).save(path,optimize=True)
def hsv(a):
 q=np.asarray(Image.fromarray(np.clip(a*255,0,255).astype('uint8')).convert('HSV'),dtype=float)/255
 return q[:,:,0]*360,q[:,:,1],q[:,:,2]
def pad(a,cov):
 _,(iy,ix)=ndimage.distance_transform_edt(~cov,return_indices=True);return a[iy,ix]
def encode(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
pals={k:np.frombuffer((p/'source/palettes'/f'pal{v}.act').read_bytes()[:768],dtype='uint8').reshape(256,3)/255 for k,v in PALS.items()}
changed=(np.abs(pals['necromancer_a']-pals['necromancer_b']).max(1)>.03)|(np.abs(pals['necromancer_a']-pals['necromancer_c']).max(1)>.03)
idx=np.concatenate([np.asarray(Image.open(Path('assets_dev/engine/sprites')/f'm472Sa{v}.bmp')).ravel() for v in range(5)])
ph,ps,pv=hsv(pals['necromancer_a'][None,:,:]);green=(ph[0]>65)&(ph[0]<180)&(ps[0]>.25)
idx=idx[(idx!=0)&changed[idx]&green[idx]];assert len(idx)>100,len(idx)
materials=[];report={}
for layer,job,suffix in [('UVMap','body_retexture_v1',''),('HeadUV','head_retexture_v1','_head')]:
 z=np.load(p/f'work/uvraster_{layer}.npz');pc=z['piece'];pos=z['pos'];cov=pc>=0;src=p/'meshy'/job
 base=load(src/'texture_urls_0_base_color.png');normal=load(src/'texture_urls_0_normal.png');rough=load(src/'texture_urls_0_roughness.png','L');h,s,v=hsv(base)
 marks=cov&(h>65)&(h<180)&(s>.30)&(v>.10)&np.isin(pc,[0,10,11])
 metal=cov&(pc==0)&(pos[:,:,2]>1.055)&(pos[:,:,2]<1.415)&(abs(pos[:,:,0])<.185)&(s<.24)&(v>.25)
 skin=cov&np.isin(pc,[2,3,4,8,9]);hair=cov&(pc==1);eye=cov&np.isin(pc,[10,11]);cord=cov&np.isin(pc,[5,6,7])
 g=base.copy()
 # Preserve painted anatomy while bringing head and hand skin to the same cool, undead palette.
 lum=R.luminance(base);blur=ndimage.gaussian_filter(np.where(skin,lum,0.),6)/np.maximum(ndimage.gaussian_filter(skin.astype(float),6),1e-5)
 detail=np.clip(lum/np.maximum(blur,1e-4),.35,1.6)
 g[skin]=.55*base[skin]+.45*encode(R.srgb_to_linear(np.array([153,175,192])/255)*detail[skin,None])
 spec=np.full((N,N),.14);rgh=np.full((N,N),.89);met=np.zeros((N,N))
 for mask,sp,ro in [(skin,.24,.77),(metal,.9,.40),(marks,.20,.82),(hair,.18,.75),(eye,.8,.23),(cord,.28,.72)]:
  spec[mask]=sp
  if mask.any():rgh[mask]=np.clip(ro+.25*(rough[mask]-np.median(rough[mask])),.15,.98)
 met[metal]=.85
 save(pad(g,cov),T/f'necromancer{suffix}_basecolor_1k.png');save(pad(normal,cov),T/f'necromancer{suffix}_normal_1k.png');save(np.stack([pad(spec,cov),pad(rgh,cov),pad(met,cov)],-1),T/f'necromancer{suffix}_metal_rough_1k.png')
 mask=ndimage.gaussian_filter(pad(marks.astype(float),cov),.55);mask[cov&~marks]=0
 R.write_mask([mask],T/f'necromancer{suffix}_region_mask.png',size=N)
 assert marks.sum()>(500 if not suffix else 10),(layer,int(marks.sum()))
 l=R.luminance(g[marks]);lo,hi=np.percentile(l,[2,98]);assert hi>lo;srt=np.sort(l);ramps={}
 for k,pal in pals.items():
  colors=pal[idx];ll=R.luminance(colors);colors=colors[ll>.005];colors=colors[np.argsort(R.luminance(colors))];ramp=[]
  for i in range(16):
   q=np.searchsorted(srt,lo+(hi-lo)*i/15)/len(srt);c=colors[min(len(colors)-1,int(q*(len(colors)-1)))];ramp.append(R.srgb_to_linear(c).tolist())
  ramps[k]=[{'range':[float(lo),float(hi)],'colors':ramp}]
 if suffix:ramps=materials[0]['ramps']
 materials.append({'base':'NecromancerHead_A' if suffix else 'Necromancer_A','prefix':'NecromancerHead' if suffix else 'Necromancer','mask':f'necromancer{suffix}_region_mask.png','regions':['runes_and_iris'],'palettes':PALS,'ramps':ramps})
 report[layer]={'skin_texels':int(skin.sum()),'rune_iris_texels':int(marks.sum()),'metal_texels':int(metal.sum()),'original_skin_median':np.median(base[skin],axis=0).tolist()}
(T/'necromancer_ramps.json').write_text(json.dumps({'variants':list(PALS),'materials':materials},indent=2))
(T/'texture_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
