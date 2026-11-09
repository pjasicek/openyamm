"""Independent padded PBR sets; native palette indices define shared hide and membrane ramps."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=2048
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
W=np.array([.2126,.7152,.0722]);lin=R.srgb_to_linear
def enc(c):return np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
def load(f,mode='RGB'):return np.array(Image.open(f).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(c,f):Image.fromarray(np.uint8(np.clip(c,0,1)*255+.5)).save(f)
def pad(c,cov):return c[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
D={};report={}
for slot,label in enumerate(['body','head','wings']):
 d=np.load(P/'work'/f'uvraster_{label}.npz');pos=d['pos'];piece=d['piece'];cov=piece>=0;rgb=load(P/'meshy'/f"{label}_retexture_v{2 if label=='head' else 3}/texture_urls_0_base_color.png");h,s,v=np.moveaxis(np.array(Image.fromarray(np.uint8(rgb*255)).convert('HSV'),float)/255,-1,0);x,y,z=np.moveaxis(pos,-1,0)
 hide=cov&(h>.185)&(h<.49)&(s>.16);mem=cov&(h>.115)&(h<.25)&(s>.13)&(~hide) if label=='wings' else np.zeros_like(cov)
 if label=='wings':
  # The pale thumb horns remain unrecoloured; every membrane texel belongs to the wing ramp.
  horn=cov&(v>.64)&(s<.29);hide=cov&(h>.24)&(h<.49)&(s>.16)&(~np.isin(piece,[2,4]));mem=cov&(~hide)&(~horn)
 classes=np.zeros((N,N),np.uint8);classes[cov]=1;classes[mem]=3;classes[cov&(v>.6)&(s<.28)]=4
 if label=='head':
  classes[cov&(h<.055)&(s>.22)&(v<.65)]=7;classes[cov&(v>.72)&(s<.26)&(z<.70)]=5
 ao=ndimage.gaussian_filter(pad(load(T/f'drg1_{label}_ao_1k.png','L'),cov),1.5);rgb=np.clip(rgb*(.80+.20*ao[...,None]),0,1)
 D[label]=dict(rgb=rgb,cov=cov,pos=pos,hide=hide,mem=mem,classes=classes,ao=ao,normal=d['normal'])
# Extend the lower neck's actual scale/plate paint over the graft by angle and arc.
# The headless Meshy upload otherwise paints a second mouth at the open neck boundary.
from scipy.spatial import cKDTree
# The service detailed one membrane face well but left the opposite wing smeared.
# Transfer that same physical leather across corresponding mirrored wing surfaces.
w=D['wings'];wx,wy,wz=np.moveaxis(w['pos'],-1,0);source=w['cov']&(wx>.16)&(w['normal'][...,1]<-.25)
assert int(source.sum())>10000
query=w['pos'][w['cov']].copy();query[:,0]=abs(query[:,0]);tree=cKDTree(w['pos'][source]);_,indices=tree.query(query);w['rgb'][w['cov']]=w['rgb'][source][indices]
wh,ws,wv=np.moveaxis(np.array(Image.fromarray(np.uint8(np.clip(w['rgb'],0,1)*255)).convert('HSV'),float)/255,-1,0)
horn=w['cov']&(wv>.64)&(ws<.29)&(abs(wx)>.55)&(wz>.70);w['hide']=w['cov']&(wh>.24)&(wh<.49)&(ws>.1)&~horn;w['mem']=w['cov']&~w['hide']&~horn
w['classes'][w['cov']]=1;w['classes'][w['mem']]=3;w['classes'][horn]=4
report['wing_shared_detail_source_texels']=int(source.sum())
b=D['body'];x,y,z=np.moveaxis(b['pos'],-1,0);cy=np.interp(z,[.44,.525,.59,.67],[-.31,-.325,-.315,-.315]);angle=np.arctan2(x,y-cy)
source=b['cov']&(z>.44)&(z<.545)&(abs(x)<.065)&(y<-.25)&(y>-.40)
target=b['cov']&(z>.55)&(z<.69)&(abs(x)<.095)&(y<-.23)
features=np.stack([np.sin(angle)*.05,np.cos(angle)*.05,z],-1);tree=cKDTree(features[source]);query=features[target].copy();query[:,2]=.45+(z[target]-.55)*.70;distance,indices=tree.query(query)
assert float(np.percentile(distance,99))<.008
mix=np.clip((z[target]-.55)/.025,0,1);mix=mix*mix*(3-2*mix);b['rgb'][target]=b['rgb'][target]*(1-mix[:,None])+b['rgb'][source][indices]*mix[:,None]
b['neck_transfer']=(target,mix);b['classes'][target]=1
# One coherent gold material across head fins and the body's belly plates.
def hsv(rgb):return np.moveaxis(np.array(Image.fromarray(np.uint8(np.clip(rgb,0,1)*255)).convert('HSV'),float)/255,-1,0)
hh,hs,hv=hsv(D['head']['rgb']);bh,bs,bv=hsv(b['rgb']);gold_head=D['head']['cov']&(hh>.065)&(hh<.18)&(hs>.40);gold_body=b['cov']&(bh>.065)&(bh<.18)&(bs>.30)
gold_gain=np.clip(np.median(lin(D['head']['rgb'])[gold_head],axis=0)/np.maximum(np.median(lin(b['rgb'])[gold_body],axis=0),1e-5),.45,1.8)
weight=ndimage.gaussian_filter(gold_body.astype(float),1);b['rgb']=enc(lin(b['rgb'])*(1+weight[...,None]*(gold_gain-1)))
bh,bs,bv=hsv(b['rgb']);b['hide']=b['cov']&(bh>.185)&(bh<.49)&(bs>.06)
report['neck_transfer_texels']=int(target.sum());report['gold_body_gain']=gold_gain.tolist()
# Match skin brightness across the real head/neck boundary before using the shared ramps.
b=D['body'];h=D['head'];bm=b['hide']&(b['pos'][...,2]>.43);hm=h['hide']&(h['pos'][...,2]<.69);gain=1.
if bm.sum()>30 and hm.sum()>30:
 gain=float(np.clip(np.median(R.luminance(b['rgb'])[bm])/np.median(R.luminance(h['rgb'])[hm]),.6,1.6));weight=ndimage.gaussian_filter(h['hide'].astype(float),1);h['rgb']=enc(lin(h['rgb'])*(1+weight[...,None]*(gain-1)))
report['head_skin_linear_gain']=gain
pals={f'drg1_{k}':np.fromfile(P.parents[2]/f'assets_dev/worlds/mm6/textures/pal{pid}.act',np.uint8)[:768].reshape(256,3)/255 for k,pid in zip('abc',[692,693,694])}
ramps={}
for tier,pal in pals.items():
 ramps[tier]=[]
 for ri,ids in enumerate([np.arange(184,256),np.arange(55,177)]):
  c=lin(pal[ids]);ca=lin(pals['drg1_a'][ids]);ok=(ca@W)>.003;c=c[ok];ca=ca[ok]
  order=np.argsort(c@W);c=c[order];tone=np.mean(c[len(c)//3:len(c)*4//5],axis=0);tonea=np.mean(ca[np.argsort(ca@W)][len(ca)//3:len(ca)*4//5],axis=0)
  chroma=tone/max(float(tone@W),1e-6);gainlum=float((tone@W)/(tonea@W));stops=[]
  for t in np.linspace(0,1,16):stops.append(np.clip(chroma*t*gainlum,0,1).tolist())
  ramps[tier].append({'range':[0.,1.],'colors':stops})
cfg={'variants':list(pals),'palettes':dict(zip(pals,[692,693,694])),'materials':[],'texture_sets':['body','head','wings'],'merge':False}
for label,d in D.items():
 rgb,cov,classes=d['rgb'],d['cov'],d['classes'];save(pad(rgb,cov),T/f'drg1_{label}_basecolor_2k.png');normal=load(P/'meshy'/f"{label}_retexture_v{2 if label=='head' else 3}/texture_urls_0_normal.png");corr=measure(np.uint8(normal*255+.5))
 if corr<0:normal[...,1]=1-normal[...,1]
 if label=='body':
  target,mix=d['neck_transfer'];normal[target]=normal[target]*(1-mix[:,None])+np.array([.5,.5,1])*mix[:,None]
 rough=np.full((N,N),.82);spec=np.full((N,N),.16);rough[classes==3]=.86;rough[classes==4]=.48;rough[classes==5]=.40;spec[classes==4]=.32;spec[classes==5]=.42;spec*=.35+.65*d['ao']
 save(pad(normal,cov),T/f'drg1_{label}_normal_2k.png');save(np.stack([pad(spec,cov),pad(rough,cov),np.zeros_like(rough)],-1),T/f'drg1_{label}_metal_rough_2k.png');Image.fromarray(classes).save(T/f'drg1_{label}_material_classes.png')
 weights=[ndimage.gaussian_filter(pad(d[k].astype(float),cov),.65) for k in ['hide','mem']];R.write_mask(weights,T/f'drg1_{label}_region_mask.png',size=N)
 cfg['materials'].append({'base':'Drake'+label.title()+'_A','prefix':'Drake'+label.title(),'mask':f'drg1_{label}_region_mask.png','regions':['hide','membrane'],'ramps':ramps})
 report[label]={'covered_texels':int(cov.sum()),'hide':int(d['hide'].sum()),'membrane':int(d['mem'].sum()),'normal_source_correlation':corr}
cfg['report']=report;(T/'drg1_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');print('COMPOSE',json.dumps(report))
