"""Native Genie ramps, UV repair reprojection and shared matte-skin/metal PBR maps."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';T.mkdir(exist_ok=True);N=1024;W=np.array([.2126,.7152,.0722])
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
palettes={'djn_a':739,'djn_b':740,'djn_c':741};pals={k:np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm6/textures/pal{v}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,v in palettes.items()}
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
def hsv(a):return np.moveaxis(np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255,-1,0)
def load(label,suffix):
 src=np.asarray(Image.open(P/f'meshy/{label}_retexture_v{2 if label=="head" else 1}/texture_urls_0_{suffix}.png').convert('RGB'),float)/255
 yy,xx=np.mgrid[:N,:N];uv=np.stack([(xx+.5)/N,1-(yy+.5)/N],-1)
 if label=='body':uv[...,0]/=.96
 else:pass
 patches=json.loads((P/'work/vortex_uv_patches.json').read_text()) if label=='body' else []
 for patch in patches:
  q=np.array(patch['target'])*[N,-N]+[0,N];a,b,c=q;lo=np.maximum(0,np.floor(q.min(0)).astype(int));hi=np.minimum(N-1,np.ceil(q.max(0)).astype(int));x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);m=np.column_stack([b-a,c-a])
  if abs(np.linalg.det(m))<1e-10:continue
  w=np.stack([x-a[0],y-a[1]],-1)@np.linalg.inv(m).T;inside=(w[...,0]>=-.01)&(w[...,1]>=-.01)&(w.sum(-1)<=1.01);weights=np.concatenate([1-w.sum(-1,keepdims=True),w],-1);target=uv[lo[1]:hi[1]+1,lo[0]:hi[0]+1];target[inside]=(weights@np.array(patch['source']))[inside]
 coords=np.array([(1-uv[...,1])*src.shape[0]-.5,uv[...,0]*src.shape[1]-.5]);return np.stack([ndimage.map_coordinates(src[...,i],coords,order=1,mode='nearest') for i in range(3)],-1)
body=load('body','base_color');head=load('head','base_color');bd=np.load(P/'work/uvraster_body.npz');hd=np.load(P/'work/uvraster_head.npz');part,pos=bd['piece'],bd['pos'];hp,hpos=hd['piece'],hd['pos'];cov=part>=0;hc=hp>=0;h,s,v=hsv(body);hh,hs,hv=hsv(head)
skin=cov&(h>.48)&(h<.73)&(s>.18);hskin=hc&(hh>.48)&(hh<.73)&(hs>.18)
gold=cov&(h>.07)&(h<.20)&(s>.3)&(v>.28);hgold=hc&(hh>.07)&(hh<.20)&(hs>.3)&(hv>.28)
gems=cov&np.isin(part,[5,10,11])&(h>.23)&(h<.46)&(s>.4)&(v>.17)
beard=cov&(part==2)&(np.abs(pos[...,0])<.055)&(pos[...,1]<-.12)&(pos[...,2]>1.70)&(pos[...,2]<1.80)
body[beard]=np.clip(body[beard].mean(-1),.04,.105)[:,None]*np.array([1.02,1.,.97]);skin&=~beard
expected_skin=cov&(((part==2)&((pos[...,2]>1.19)|(np.abs(pos[...,0])>.4)))|(part==3))&~beard
edge=expected_skin&~skin;nearest=ndimage.distance_transform_edt(~skin,return_distances=False,return_indices=True);body[edge]=body[tuple(nearest[:,edge])];skin|=expected_skin
vortex=cov&np.isin(part,[0,1,4,6,8,12]);body[vortex]*=.73
# Both UV domains share one skin ramp; align their luminance near the neck before palette mapping.
bseam=skin&(pos[...,2]>1.65);hseam=hskin&(hpos[...,2]<1.86)
gain=float(np.clip(np.median(R.luminance(body[bseam]))/np.median(R.luminance(head[hseam])),.65,1.5));a=R.srgb_to_linear(head);a[hskin]*=gain;head=np.where(a<=.0031308,12.92*a,1.055*np.maximum(a,0)**(1/2.4)-.055)
assert skin.sum()>50000 and hskin.sum()>50000 and gold.sum()>5000
lut={tuple(c):i for i,c in enumerate(np.uint8(pals['djn_a']*255+.5))};used=[]
for view in range(5):
 a=np.asarray(Image.open(P.parent/'mm6_djn/native_variants'/f'djnstaa{view}_739.png'));used.extend(lut.get(tuple(c),0) for c in a[a[...,3]>0,:3])
used=np.array(used);idx=np.arange(256);regions=[('skin',skin,hskin,(idx>=104)&(idx<=167)),('gems',gems,np.zeros_like(hskin),(idx>=88)&(idx<=103))];ramps={k:[] for k in pals};report={}
for name,bm,hm,select in regions:
 ids=used[select[used]];assert len(ids)>20;lum=np.r_[R.luminance(body[bm]),R.luminance(head[hm])];lo,hi=np.percentile(lum,[1,99]);assert hi>lo
 for key,pal in pals.items():
  colors=R.srgb_to_linear(pal[ids]);order=np.argsort(colors@W);colors=colors[order];native=np.median(colors[len(colors)//4:3*len(colors)//4],axis=0)*(1.4 if name=='skin' else 1.25);chroma=native/max(float(native@W),1e-8);gain2=float(native@W)/max(float(np.median(lum)),1e-8);ramps[key].append({'range':[float(lo),float(hi)],'colors':[np.clip(chroma*(lo+j/15*(hi-lo))*gain2,0,1).tolist() for j in range(16)]})
 report[name]={'body_texels':int(bm.sum()),'head_texels':int(hm.sum()),'native_samples':len(ids),'range':[float(lo),float(hi)]}
for label,img,covered,metal_mask,masks in [('body',body,cov,gold,[skin,gems]),('head',head,hc,hgold,[hskin,np.zeros_like(hskin)])]:
 rough=load(label,'roughness')[...,0];normal=load(label,'normal');score=measure(np.uint8(normal*255+.5));assert score<-.15,(label,score);normal[...,1]=1-normal[...,1]
 position=pos if label=='body' else hpos;seam=np.clip(1-np.abs(position[...,2]-1.755)/.018,0,1)*(position[...,1]>-.10);normal=normal*(1-seam[...,None])+np.array([.5,.5,1.])*seam[...,None]
 spec=np.full((N,N),.20);rg=np.clip(.8+.2*(rough-.5),.68,.94);metal=np.zeros((N,N));spec[metal_mask]=.8;rg[metal_mask]=np.clip(.40+.2*(rough[metal_mask]-.5),.29,.52);metal[metal_mask]=.55
 if label=='body':spec[gems]=.6;rg[gems]=.26
 else:
  eyes=np.isin(hp,[9,13]);spec[eyes]=.6;rg[eyes]=.25
 save(pad(img,covered),T/f'djn_{label}_basecolor_1k.png');save(pad(normal,covered),T/f'djn_{label}_normal_1k.png');save(np.stack([pad(spec,covered),pad(rg,covered),pad(metal,covered)],-1),T/f'djn_{label}_metal_rough_1k.png');R.write_mask([ndimage.gaussian_filter(pad(m.astype(float),covered),.55) for m in masks],T/f'djn_{label}_region_mask.png',size=N)
 classes=np.zeros((N,N),np.uint8);classes[covered]=1;classes[metal_mask]=9;Image.fromarray(classes).save(T/f'djn_{label}_material_classes.png');overlay=img*.3
 for mask,color in zip(masks,[(.1,.85,.2),(.9,.1,.1)]):overlay[mask]=color
 overlay[metal_mask]=(1,.8,.1);save(overlay,P/'review'/f'djn_{label}_regions.png')
cfg={'variants':list(pals),'palettes':palettes,'report':report,'head_skin_linear_gain':gain,'materials':[{'base':name+'_A','prefix':name,'mask':f'djn_{label}_region_mask.png','regions':[x[0] for x in regions],'ramps':ramps} for label,name in [('body','Genie'),('head','GenieHead')]]};(T/'djn_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');print('COMPOSE',json.dumps(report),'head gain',gain)
