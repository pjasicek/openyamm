import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=2048
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
W=np.array([.2126,.7152,.0722]);lin=R.srgb_to_linear
def load(p,mode='RGB'):return np.array(Image.open(p).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(c,p):Image.fromarray(np.uint8(np.clip(c,0,1)*255+.5)).save(p)
def pad(c,cov):return c[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
pals={f'drag_{k}':np.fromfile(P.parents[2]/f'assets_dev/worlds/mm6/textures/pal{v}.act',np.uint8)[:768].reshape(256,3)/255 for k,v in zip('abc',[689,690,691])}
phsv=np.array(Image.fromarray(np.uint8(pals['drag_a'][None]*255)).convert('HSV'))[0]/255;ph,ps,pv=phsv.T
regions=[(ph>.20)&(ph<.65)&(ps>.12)&(pv>.06)&(pv<.8),(ph<.17)&(ps>.35)&(pv>.1)&(pv<.9)]
# Shared ramps across body and head keep the neck seam chromatically continuous.
ramps={k:[] for k in pals}
for reg in regions:
 ix=np.where(reg)[0];assert len(ix)>3;order=np.argsort(lin(pals['drag_a'][ix])@W);chosen=ix[order[len(order)//3:len(order)*4//5]];native_a=lin(pals['drag_a'][chosen]).mean(0)
 for key,pal in pals.items():
  target=lin(pal[chosen]).mean(0);chroma=target/max(float(target@W),1e-6);gain=1 if key=='drag_a' else float((target@W)/max(native_a@W,1e-6));gain=np.clip(gain,.6,1.7)
  ramps[key].append({'range':[0.,1.],'colors':[np.clip(chroma*t*gain,0,1).tolist() for t in np.linspace(0,1,16)]})
cfg={'variants':list(pals),'palettes':dict(zip(pals,[689,690,691])),'materials':[],'texture_sets':['body','head'],'merge':False};report={}
for slot,label in enumerate(['body','head']):
 d=np.load(P/'work'/f'uvraster_{label}.npz');cov=d['piece']>=0;rgb=load(P/'meshy'/f'{label}_texture_v2/texture_urls_0_base_color.png');ao=ndimage.gaussian_filter(load(T/f'drag_{label}_ao_1k.png','L'),1.5);rgb*=.80+.20*ao[...,None]
 h,s,v=np.moveaxis(np.array(Image.fromarray(np.uint8(np.clip(rgb,0,1)*255)).convert('HSV'))/255,-1,0);pos=d['pos'];parts=d['piece']
 bonepart=np.isin(parts,[4,5,6,7,8,9,10,11,12,13,14,15,17,20,38]);teeth=np.isin(parts,[16,18,19,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37]);ivory=(bonepart|teeth|((s<.26)&(v>.52)))&cov
 horn=cov&(parts==0)&(abs(pos[...,0])>.025)&(pos[...,2]>.855)&(pos[...,1]<-.325) if label=='head' else np.zeros_like(cov)
 ivory|=horn
 belly=cov&(h<.17)&(s>.38)&(~ivory);hide=cov&(~belly)&(~ivory)
 mouth=cov&(parts==3)
 eyes=np.zeros_like(cov)
 if label=='head':eyes=cov&(abs(pos[...,0])>.008)&(pos[...,1]<-.36)&(pos[...,1]>-.413)&(pos[...,2]>.78)&(pos[...,2]<.846)&(h<.17)&(s>.45)
 hide&=~eyes;belly|=eyes
 if label=='head':mouth|=cov&((h>.87)|((h<.06)&(s>.30)&(v<.5)))
 hide&=~mouth;belly&=~(mouth&~eyes)
 # Clean ivory keeps subtle source luminance variation, preventing skin-colour flecks on separate spikes/teeth.
 lum=rgb@W;iv=ivory&(bonepart|teeth|horn);rgb[iv]=np.clip((.76+.20*lum[iv,None])*np.array([1.,.98,.87]),0,1)
 masks=[ndimage.gaussian_filter(pad(m.astype(float),cov),.65) for m in [hide,belly]]
 classes=np.zeros((N,N),np.uint8);classes[cov]=1;classes[ivory]=4;classes[teeth]=5;classes[mouth]=7;classes[cov&np.isin(parts,[1,2])]=3;classes[eyes]=6
 normal=load(P/'meshy'/f'{label}_texture_v2/texture_urls_0_normal.png');corr=measure(np.uint8(normal*255+.5))
 if corr<0:normal[...,1]=1-normal[...,1]
 rough=np.full((N,N),.84);rough[ivory]=.47;rough[mouth]=.60;spec=np.full((N,N),.13);spec[ivory]=.35;spec*=.35+.65*ao
 save(pad(rgb,cov),T/f'drag_{label}_basecolor_2k.png');save(pad(normal,cov),T/f'drag_{label}_normal_2k.png');save(np.stack([pad(spec,cov),pad(rough,cov),np.zeros_like(spec)],-1),T/f'drag_{label}_metal_rough_2k.png');Image.fromarray(classes).save(T/f'drag_{label}_material_classes.png');R.write_mask(masks,T/f'drag_{label}_region_mask.png',size=N)
 cfg['materials'].append({'base':'Lizard'+label.title()+'_A','prefix':'Lizard'+label.title(),'mask':f'drag_{label}_region_mask.png','regions':['hide','belly_and_fins'],'ramps':ramps});report[label]={'covered_texels':int(cov.sum()),'hide':int(hide.sum()),'belly':int(belly.sum()),'normal_correlation':corr}
cfg['report']=report;(T/'drag_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');print('COMPOSE',report)
