"""Native vest ramps, even skin colour and matte civilian materials; original maps remain untouched."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy import ndimage
p=Path(__file__).resolve().parents[1];T=p/'textures';T.mkdir(exist_ok=True);N=1024
sys.path.insert(0,str(p.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(p.parents[2]/'tools'));import normal_map_convention as NC
PALS={'bedraggled_a':621,'bedraggled_b':622,'bedraggled_c':623}
def load(path,mode='RGB'):return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path)
def encode(a):return np.where(a<=.0031308,12.92*a,1.055*np.maximum(a,0)**(1/2.4)-.055)
pals={k:np.frombuffer((p/f'source/palettes/pal{v}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,v in PALS.items()}
changed=(np.abs(pals['bedraggled_a']-pals['bedraggled_b']).max(1)>.03)|(np.abs(pals['bedraggled_a']-pals['bedraggled_c']).max(1)>.03)
idx=np.concatenate([np.asarray(Image.open(p.parents[2]/f'assets_dev/engine/sprites/m620Sa{v}.bmp')).ravel() for v in range(5)])
idx=idx[(idx!=0)&changed[idx]];assert len(idx)>100
materials=[];report={}
for layer,job,suffix in [('UVMap','body_retexture_v1','')]:
 z=np.load(p/f'work/uvraster_{layer}.npz');region=z['piece'];cov=z['coverage'];pos=z['pos'];raw=p/'meshy'/job
 base=load(raw/'texture_urls_0_base_color.png');normal=load(raw/'texture_urls_0_normal.png');rough=load(raw/'texture_urls_0_roughness.png','L')
 skin=cov&(region==0);vest=cov&(region==2);hair=cov&(region==4);eyes=cov&(region==5);boots=cov&(region==3)
 # The hanging vest frays share a few upper-trouser charts; include their painted cloth, never bare skin.
 hsv=np.asarray(Image.fromarray(np.uint8(np.clip(base,0,1)*255)).convert('HSV'))
 fringe=cov&(region==1)&(pos[:,:,2]>.78)&(hsv[:,:,0]>35)&(hsv[:,:,0]<100)&(hsv[:,:,1]>45)
 fringe=ndimage.binary_dilation(fringe,iterations=2)&cov&(region==1)&(pos[:,:,2]>.78)
 vest|=fringe
 assert not (vest&skin).any()
 nearest=tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))
 # Remove broad baked lighting and coloured blotches while retaining fine wrinkles and skin texture.
 lum=R.luminance(base);blur=ndimage.gaussian_filter(np.where(skin,lum,0),6)/np.maximum(ndimage.gaussian_filter(skin.astype(float),6),1e-6)
 detail=np.clip(lum/np.maximum(blur,1e-5),.55,1.4)
 clean=encode(R.srgb_to_linear(np.array([172,133,107])/255)*(.78+.22*detail[...,None]))
 base[skin]=clean[skin]
 ao=load(p/f'work/ao{suffix}.png','L')
 # The old head's baked neck occlusion no longer belongs on the joined skin.
 neck=np.clip((pos[:,:,2]-1.40)/.04,0,1)*skin*(np.abs(pos[:,:,0]+.011)<.09)
 ao=ao*(1-neck)+neck
 base*=1-.15*(1-np.maximum(ao,.35))[...,None]
 save(base[nearest],T/f'bedraggled{suffix}_basecolor_1k.png')
 corr=NC.measure(np.uint8(normal*255+.5))
 if corr<=-.15:normal[:,:,1]=1-normal[:,:,1]
 strength=.4 if suffix else .65
 normal=(normal-[.5,.5,1])*strength+[.5,.5,1]
 save(normal[nearest],T/f'bedraggled{suffix}_normal_1k.png')
 spec=np.full((N,N),.10);rr=np.full((N,N),.90)
 for mask,sp,ro in [(skin,.14,.82),(hair,.13,.83),(eyes,.55,.34),(boots,.22,.73)]:spec[mask]=sp;rr[mask]=ro
 rr=np.clip(rr+.12*(rough-np.median(rough[cov])),.3,.98)
 save(np.stack([spec,rr,np.zeros_like(rr)],-1)[nearest],T/f'bedraggled{suffix}_metal_rough_1k.png')
 classes=np.zeros((N,N),np.uint8);classes[skin]=1;classes[hair]=2;classes[eyes]=6;classes[boots]=8;classes[cov&np.isin(region,[1,2,6])]=8
 Image.fromarray(classes[nearest]).save(T/f'bedraggled{suffix}_material_classes.png')
 mask=vest.astype(float)[nearest];R.write_mask([mask],T/f'bedraggled{suffix}_region_mask.png',N)
 if not suffix:
  assert vest.sum()>1000
  values=R.luminance(base[vest]);lo,hi=np.percentile(values,[2,98]);srt=np.sort(values);ramps={}
  for key,pal in pals.items():
   colors=pal[idx];colors=colors[R.luminance(colors)>.005];colors=colors[np.argsort(R.luminance(colors))];ramp=[]
   for i in range(16):
    q=np.searchsorted(srt,lo+(hi-lo)*i/15)/len(srt);color=colors[min(len(colors)-1,int(q*(len(colors)-1)))];ramp.append(R.srgb_to_linear(color).tolist())
   ramps[key]=[{'range':[float(lo),float(hi)],'colors':ramp}]
 materials.append({'base':'BedraggledHead_A' if suffix else 'Bedraggled_A','prefix':'BedraggledHead' if suffix else 'Bedraggled','mask':f'bedraggled{suffix}_region_mask.png','regions':['vest'],'palettes':PALS,'ramps':ramps})
 report[layer]={'skin_texels':int(skin.sum()),'vest_texels':int(vest.sum()),'normal_correlation':corr,'flipped_normal_green':bool(corr<=-.15),'coverage':float(cov.mean())}
(T/'bedraggled_ramps.json').write_text(json.dumps({'variants':list(PALS),'materials':materials},indent=2)+'\n')
(T/'texture_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

# The runtime merger requires body maps at least as tall as the detailed head map.
# Keep the established body paint unchanged while storing it at the shared 2K height.
for channel in ('basecolor','normal','metal_rough','region_mask'):
 Image.open(T/f'bedraggled_{channel}_1k.png' if channel!='region_mask' else T/'bedraggled_region_mask.png').resize((2048,2048),Image.Resampling.NEAREST).save(T/f'bedraggled_{channel}_2k.png')
r=json.loads((T/'bedraggled_ramps.json').read_text());r['materials'][0]['mask']='bedraggled_region_mask_2k.png';(T/'bedraggled_ramps.json').write_text(json.dumps(r,indent=2)+'\n')

import runpy
runpy.run_path(str(p/'scripts/compose_head_v2.py'),run_name='__main__')
