"""Three independent PBR sets, native feather palettes, restrained AO and material-class masks."""
from pathlib import Path
import json,sys,runpy
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
W=np.array([.2126,.7152,.0722]);jobs={'body':'torso_retexture_v1','head':'head_retexture_v2','wings':'wings_retexture_v1'}
def load(path,mode='RGB'):return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
encode=lambda x:np.where(x<=.0031308,12.92*x,1.055*np.maximum(x,0)**(1/2.4)-.055)
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
def hsv(a):return np.moveaxis(np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255,-1,0)
D={};report={}
for label,job in jobs.items():
 d=np.load(P/'work'/f'uvraster_{label}.npz');piece,pos=d['piece'],d['pos'];cov=piece>=0;x,y,z=np.moveaxis(pos,-1,0);rgb=load(P/'meshy'/job/'texture_urls_0_base_color.png');h,s,v=hsv(rgb);green=cov&(h>.17)&(h<.46)&(s>.22)
 if label=='wings':
  # Remove isolated green projection spill beyond the native inner-wing coverts.
  spill=green&(abs(x)>.62);brown=cov&(abs(x)>.60)&(abs(x)<.9)&(h>.025)&(h<.16)&(s>.25)
  target=np.median(R.srgb_to_linear(rgb[brown]),axis=0);lin=R.srgb_to_linear(rgb);gain=float((target@W)/np.median(R.luminance(rgb[spill]))) if spill.any() else 1
  lin[spill]=R.luminance(rgb[spill])[:,None]*gain*target/max(float(target@W),1e-8);rgb=encode(lin);green&=~spill;report['outer_wing_spill_texels']=int(spill.sum())
 classes=np.zeros((N,N),np.uint8);classes[cov]=1
 if label=='wings':classes[cov]=2
 elif label=='body':
  feather=cov&(((z>.53)&(z<1.015)&(abs(x)<.31))|green|np.isin(piece,[2,5]));classes[feather]=2;classes[cov&(z<.47)]=4
 else:
  hair=cov&(piece==0)&(v>.32)&(s>.12)&(h<.18);classes[hair]=2;classes[np.isin(piece,[3,6])]=5;classes[np.isin(piece,[4,7])]=6
 D[label]={'rgb':rgb,'cov':cov,'green':green,'classes':classes,'pos':pos,'piece':piece}
b=D['body'];h=D['head'];x,y,z=np.moveaxis(b['pos'],-1,0);bm=b['cov']&(b['piece']==0)&~b['green']&(abs(x)>.27)&(z>.78)&(z<1.25);x,y,z=np.moveaxis(h['pos'],-1,0);hm=h['cov']&(h['piece']==0)&(y<-.09)&(z>1.49)&(z<1.65);assert bm.sum()>1000 and hm.sum()>1000
gain=np.clip(np.median(R.srgb_to_linear(b['rgb'][bm]),axis=0)/np.maximum(np.median(R.srgb_to_linear(h['rgb'][hm]),axis=0),1e-5),.40,1.30);skin=h['classes']==1;linear=R.srgb_to_linear(h['rgb']);skin_weight=ndimage.gaussian_filter(skin.astype(float),3);linear*=1+skin_weight[...,None]*(gain-1);h['rgb']=encode(linear);report['head_skin_linear_gain']=gain.tolist()
# A shared neck tone removes projection seams between the independently generated atlases.
neck_tone=np.median(R.srgb_to_linear(D['body']['rgb'][bm]),axis=0)
for label in ['body','head']:
 d=D[label];x,y,z=np.moveaxis(d['pos'],-1,0)
 smooth=lambda t:np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
 weight=smooth((z-1.25)/.08)*(1-smooth((z-1.49)/.08))*(1-smooth((abs(x+.01)-.14)/.10))*(1-smooth((y-.01)/.09))*d['cov']*(d['piece']==0)
 linear=R.srgb_to_linear(d['rgb']);lum=linear@W;low=ndimage.gaussian_filter(pad(lum,d['cov']),6)
 detail=np.clip(lum/np.maximum(low,1e-5),.65,1.35);target=neck_tone*(1+.20*(detail[...,None]-1))
 d['rgb']=encode(linear*(1-weight[...,None])+target*weight[...,None]);d['neck_weight']=weight;d['neck_target']=target
for label,d in D.items():
 rgb,cov,classes=d['rgb'],d['cov'],d['classes'];save(pad(rgb,cov),T/f'hrp_{label}_basecolor_1k.png')
 sys.argv=['grade_basecolor.py','--ao',str(T/f'hrp_{label}_ao_1k.png'),'--ao-strength','.35','--local','.20','--contrast','1.04','--saturation','1.06','--fine','.70',str(T/f'hrp_{label}_basecolor_1k.png')];runpy.run_path(str(P.parent/'claude_shared/grade_basecolor.py'),run_name='__main__');d['rgb']=load(T/f'hrp_{label}_basecolor_1k_graded.png');d['ramp_rgb']=d['rgb'].copy()
 if 'neck_weight' in d:
  weight=d['neck_weight'][...,None];d['rgb']=encode(R.srgb_to_linear(d['rgb'])*(1-weight)+d['neck_target']*weight);save(pad(d['rgb'],cov),T/f'hrp_{label}_basecolor_1k_graded.png')
 normal=load(P/'meshy'/jobs[label]/'texture_urls_0_normal.png');corr=measure(np.uint8(normal*255+.5));assert corr<-.15 or corr>.15,(label,corr)
 if corr<0:normal[...,1]=1-normal[...,1]
 if 'neck_weight' in d:
  xy=(normal[...,:2]*2-1)*(1-d['neck_weight'][...,None]);normal[...,:2]=(xy+1)/2;normal[...,2]=(np.sqrt(np.maximum(0,1-(xy*xy).sum(-1)))+1)/2
 rough=load(P/'meshy'/jobs[label]/'texture_urls_0_roughness.png','L');spec=np.full((N,N),.24);rg=np.full((N,N),.75)
 for cls,sp,ro in [(2,.18,.83),(4,.35,.52),(5,.45,.40),(6,.8,.20),(7,.35,.48)]:spec[classes==cls]=sp;rg[classes==cls]=ro
 ao=ndimage.gaussian_filter(pad(load(T/f'hrp_{label}_ao_1k.png','L'),cov),2);spec*=.4+.6*ao;rg=np.clip(rg+.1*(rough-.5),.15,.95)
 if 'neck_weight' in d:
  weight=d['neck_weight'];spec=spec*(1-weight)+.24*weight;rg=rg*(1-weight)+.75*weight
 save(pad(normal,cov),T/f'hrp_{label}_normal_1k.png');save(np.stack([pad(spec,cov),pad(rg,cov),np.zeros_like(rg)],-1),T/f'hrp_{label}_metal_rough_1k.png');Image.fromarray(classes).save(T/f'hrp_{label}_material_classes.png');report[label]={'covered_texels':int(cov.sum()),'green_texels':int(d['green'].sum()),'normal_source_correlation':corr}
# Only the native green plumage changes: the brown flight feathers, skin, hair and feet remain shared.
paldir=P.parents[2]/'assets_dev/worlds/mm6/textures';pals={f'hrp_{tier}':np.frombuffer((paldir/f'pal{pal}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for tier,pal in zip('abc',[751,752,753])};ref=pals['hrp_a'];lut={tuple(c):i for i,c in enumerate(np.uint8(ref*255+.5))};used=[]
for view in range(5):
 a=np.asarray(Image.open(P.parent/'mm6_hrp/native_variants'/f'hrpflya{view}_751.png').convert('RGB'));used.extend(lut.get(tuple(c),0) for c in a.reshape(-1,3))
ids=np.array(used);r,g,bl=ref.T;valid=(g>r*1.15)&(g>bl*1.15)&(g>.15);ids=ids[valid[ids]];assert len(ids)>100
cfg={'variants':list(pals),'palettes':dict(zip(pals,[751,752,753])),'materials':[],'report':report,'texture_sets':['body','head','wings'],'merged':False}
for label,name in [('body','HarpyBody'),('wings','HarpyWings')]:
 d=D[label];mask=d['green'];lum=R.luminance(d['ramp_rgb']);lo,hi=np.percentile(lum[mask],[1,99]);assert hi>lo and mask.sum()>1000;ramps={}
 for variant,pal in pals.items():
  colors=R.srgb_to_linear(pal[ids]);colors=colors[np.argsort(colors@W)];native=np.median(colors[len(colors)//4:3*len(colors)//4],axis=0)*1.35;k=float(native@W)/max(float(np.median(lum[mask])),1e-8);chroma=native/max(float(native@W),1e-8)
  ramps[variant]=[{'range':[float(lo),float(hi)],'colors':[np.clip(chroma*(lo+j/15*(hi-lo))*k,0,1).tolist() for j in range(16)]}]
 weight=ndimage.gaussian_filter(pad(mask.astype(float),d['cov']),.55);R.write_mask([weight],T/f'hrp_{label}_region_mask.png',size=N);cfg['materials'].append({'base':name+'_A','prefix':name,'mask':f'hrp_{label}_region_mask.png','regions':['plumage'],'ramps':ramps});overlay=d['rgb']*.3;overlay[mask]=(0.1,.9,.2);save(overlay,P/'review'/f'{label}_regions.png')
(T/'hrp_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');print('COMPOSE',json.dumps(report),flush=True)
