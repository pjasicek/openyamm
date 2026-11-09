import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=2048
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
W=np.array([.2126,.7152,.0722]);lin=R.srgb_to_linear
enc=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
def load(p,mode='RGB'):return np.array(Image.open(p).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(c,p):Image.fromarray(np.uint8(np.clip(c,0,1)*255+.5)).save(p)
def pad(c,cov):return c[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
pals={f'cdr1_{k}':np.fromfile(P.parents[2]/f'assets_dev/worlds/mm6/textures/pal{v}.act',np.uint8)[:768].reshape(256,3)/255 for k,v in zip('abc',[698,699,700])}
phsv=np.array(Image.fromarray(np.uint8(pals['cdr1_a'][None]*255)).convert('HSV'))[0]/255;ph,ps,pv=phsv.T
regions=[(ph<32/360)&(ps>.25)&(pv>.10),(ph>=32/360)&(ph<85/360)&(ps>.25)&(pv>.10)]
cfg={'variants':list(pals),'palettes':dict(zip(pals,[698,699,700])),'materials':[],'texture_sets':['body','head','wings'],'merge':False};report={}
for slot,label in enumerate(['body','head','wings']):
 d=np.load(P/'work'/f'uvraster_{label}.npz');cov=d['piece']>=0;rgb=load(P/'meshy'/f'{label}_texture_v1/texture_urls_0_base_color.png');ao=ndimage.gaussian_filter(load(T/f'cdr1_{label}_ao_1k.png','L'),1.5);rgb*=.80+.20*ao[...,None]
 h,s,v=np.moveaxis(np.array(Image.fromarray(np.uint8(np.clip(rgb,0,1)*255)).convert('HSV'))/255,-1,0)
 gold=cov&(h>32/360)&(h<85/360)&(s>.32);hide=cov&((h<32/360)|(h>.94))&(s>.30)
 masks=[ndimage.gaussian_filter(pad(m.astype(float),cov),.65) for m in [hide,gold]]
 classes=np.zeros((N,N),np.uint8);classes[cov]=3 if label=='wings' else 1;horn=cov&(s<.30)&(v>.5);classes[horn]=4
 if label=='head':classes[cov&(h>.87)&(v<.65)]=7
 normal=load(P/'meshy'/f'{label}_texture_v1/texture_urls_0_normal.png');corr=measure(np.uint8(normal*255+.5))
 if corr<0:normal[...,1]=1-normal[...,1]
 rough=np.full((N,N),.82 if label!='wings' else .88);rough[horn]=.48;spec=np.full((N,N),.14);spec[horn]=.35;spec*=.35+.65*ao
 save(pad(rgb,cov),T/f'cdr1_{label}_basecolor_2k.png');save(pad(normal,cov),T/f'cdr1_{label}_normal_2k.png');save(np.stack([pad(spec,cov),pad(rough,cov),np.zeros_like(spec)],-1),T/f'cdr1_{label}_metal_rough_2k.png');Image.fromarray(classes).save(T/f'cdr1_{label}_material_classes.png');R.write_mask(masks,T/f'cdr1_{label}_region_mask.png',size=N)
 ramps={k:[] for k in pals}
 for reg,mask in zip(regions,masks):
  ix=np.where(reg)[0];basepal=lin(pals['cdr1_a'][ix]);order=np.argsort(basepal@W);chosen=ix[order[len(order)//3:len(order)*4//5]];native_a=lin(pals['cdr1_a'][chosen]).mean(0)
  core=mask>.9
  if core.sum()<100:col=np.array([.4,.22,.07]);range_=[0.,1.]
  else:col=lin(rgb)[core].mean(0);range_=[0.,1.]
  for key,pal in pals.items():
   target=lin(pal[chosen]).mean(0);chroma=target/max(float(target@W),1e-6);gain=1 if key=='cdr1_a' else float((target@W)/max(native_a@W,1e-6));gain=np.clip(gain,.5,2)
   ramps[key].append({'range':range_,'colors':[np.clip(chroma*t*gain,0,1).tolist() for t in np.linspace(0,1,16)]})
 cfg['materials'].append({'base':'Dragon'+label.title()+'_A','prefix':'Dragon'+label.title(),'mask':f'cdr1_{label}_region_mask.png','regions':['hide','belly'],'ramps':ramps});report[label]={'covered_texels':int(cov.sum()),'hide':int(hide.sum()),'gold':int(gold.sum()),'normal_correlation':corr}
cfg['report']=report;(T/'cdr1_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');print('COMPOSE',report)
