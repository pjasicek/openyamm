import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as nd
P=Path(__file__).resolve().parents[1];T=P/'textures';sys.path.insert(0,str(P.parent/'mm6_peasants'));from mep_materials import weights
L=np.array([.2126,.7152,.0722]);lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4);enc=lambda c:np.where(c<=.0031308,12.92*c,1.055*np.maximum(c,0)**(1/2.4)-.055)
def image(path):return np.array(Image.open(path).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS))/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a*255+.5,0,255))).save(path)
job=P/'meshy/head_retexture_round2_uv';data=np.load(P/'work/round2_head_lod0.npz');piece=data['piece'];cloth=data['cloth'];pos=data['pos'];occupied=piece>=0
suv=data['source_uv'];coords=[(1-suv[:,:,1])*1024-.5,suv[:,:,0]*1024-.5]
def sampled(name):
 a=image(job/('texture_urls_0_'+name+'.png'));return np.stack([nd.map_coordinates(a[:,:,c],coords,order=1,mode='nearest') for c in range(3)],-1)
base=sampled('base_color');normal=sampled('normal');normal[:,:,1]=1-normal[:,:,1];normal[piece==0]=[.5,.5,1]
for name,arr in [('basecolor',base),('normal',normal)]:
 old=image(P/f'review/round2/before/textures/lod0/mep_head_{name}.png');cap=np.stack([nd.map_coordinates(old[:,:,c],coords,order=1,mode='nearest') for c in range(3)],-1);arr[piece==4]=cap[piece==4]

ref=np.array(Image.open(P/'references_head/front.png').convert('RGBA'))/255
# Register the HD eyes, nose tip and lips to the corresponding mesh landmarks.
u=np.interp(pos[:,:,0],[-.085,-.060,-.02706,-.004,.0196,.056,.078],[173,218,289,338,386,430,464])
v=np.interp(pos[:,:,2],[1.29,1.43,1.478,1.503,1.527,1.5563,1.57,1.60,1.61],[622,470,410,367,320,247,222,197,180])
beard=(piece==0)&(pos[:,:,1]<0)&(pos[:,:,2]<1.49);factor=np.interp(pos[:,:,2],[1.29,1.43,1.49],[.4,.63,.9]);u=np.where(beard,338+(u-338)*factor,u)
photo=np.stack([nd.map_coordinates(ref[:,:,c],[v,u],order=1,mode='nearest') for c in range(4)],-1)
front=np.clip((.025-pos[:,:,1])/.045,0,1)*(piece==0)*~cloth*(pos[:,:,2]<1.613)*photo[:,:,3]
base=base*(1-front[:,:,None])+photo[:,:,:3]*front[:,:,None]
normal=normal*(1-front[:,:,None]) + np.array([.5,.5,1])*front[:,:,None]
side_ref=np.array(Image.open(P/'references_head/left.png').convert('RGBA'))/255
su=np.interp(pos[:,:,1],[-.11,-.082,-.065,-.040,-.005,.020,.042,.07,.11],[133,159,195,245,308,364,401,447,490])
side_photo=np.stack([nd.map_coordinates(side_ref[:,:,c],[v,su],order=1,mode='nearest') for c in range(4)],-1)
side=np.clip((abs(pos[:,:,0]+.003)-.035)/.022,0,1)*np.clip((pos[:,:,1]+.065)/.065,0,1)*(piece==0)*~cloth*(pos[:,:,2]>1.40)*(pos[:,:,2]<1.613)*side_photo[:,:,3]
side*=~((pos[:,:,2]<1.49)&(pos[:,:,1]<-.025))
base=base*(1-side[:,:,None])+side_photo[:,:,:3]*side[:,:,None];normal=normal*(1-side[:,:,None])+np.array([.5,.5,1])*side[:,:,None]
# The separate globes carry the registered HD irises, without projecting cloth onto them.
for part,cx in [(12,.0196),(13,-.02706)]:
 m=piece==part;ex=386 if part==12 else 289;ey=247
 uu=ex+(pos[:,:,0]-cx)*2100;vv=ey-(pos[:,:,2]-1.5563)*2100
 eye=np.stack([nd.map_coordinates(ref[:,:,c],[vv,uu],order=1,mode='nearest') for c in range(3)],-1)
 base[m]=eye[m];normal[m]=[.5,.5,1]
base[cloth]=np.clip(base[cloth].mean(1,keepdims=True)*1.05,.68,.93);normal[cloth]=[.5,.5,1]
# Saturation separates skin from the soft white hair strands; no geometric rectangular face mask.
mx=base.max(2);mn=base.min(2);sat=(mx-mn)/np.maximum(mx,1e-5);warm=(base[:,:,0]>base[:,:,1]*1.08)&(base[:,:,1]>base[:,:,2]*1.02)
skin=warm&(sat>.19)&(piece==0)&~cloth&(pos[:,:,2]>1.40);mask=np.zeros((*piece.shape,4));mask[:,:,2]=1;mask[piece==4]=[0,1,0,0];mask[skin]=[0,0,0,1];mask[np.isin(piece,[12,13])]=0
classes=np.full(piece.shape,2,np.uint8);classes[skin]=1;classes[piece==4]=8;classes[np.isin(piece,[12,13])]=6
# Native palette histograms drive the same skin mapping on head, neck, hands and legs.
native=np.array(Image.open(P.parent/'mm6_mep/native/mepsta0.png'));rgb=native[:,:,:3];y,x=np.indices(rgb.shape[:2]);sel=(native[:,:,3]>0)&(weights(rgb)[:,:,3]>.65)&(((x>=119)&(x<=145)&(y>=20)&(y<=45))|((x>=172)&(x<=186)&(y>=108)&(y<=147))|((x>=95)&(x<=120)&(y>=216)&(y<=249))|((x>=141)&(x<=160)&(y>=216)&(y<=249)))
repo=P.parents[2];palettes=[np.frombuffer((repo/f'assets_dev/worlds/mm6/textures/pal{804+i}.act').read_bytes()[:768],np.uint8).reshape(256,3) for i in range(3)];indices=np.argmin(((rgb[sel,None].astype(float)-palettes[0][None])**2).sum(2),axis=1)
cfg=json.loads((P/'review/round2/before/textures/mep_ramps.json').read_text());oldskin=cfg['materials'][0]['ramps']['mep_a'][3];newramps={};native_stats={}
for tier,palette in zip('abc',palettes):
 colors=lin(palette[indices]/255);colors=colors[np.argsort(colors@L)];q=(np.arange(len(colors))+.5)/len(colors);ramp=np.column_stack([np.interp(np.linspace(0,1,16),q,colors[:,c]) for c in range(3)])
 newramps['mep_'+tier]={'range':[0.,1.],'colors':ramp.tolist()};native_stats[tier]={'mean':float((colors@L).mean()),'p90':float(np.percentile(colors@L,90))}
for entry in cfg['materials'][:2]:
 for tier in 'abc':entry['ramps']['mep_'+tier][3]=newramps['mep_'+tier]
(T/'mep_ramps.json').write_text(json.dumps(cfg,indent=2))
def rank_grade(a,core):
 lum=lin(a)@L;values=np.sort(lum[core]);rank=np.searchsorted(values,lum,side='left')/len(values);out=lin(a);out[core]=rank[core,None];return np.clip(enc(out),0,1)
base=rank_grade(base,skin);core=(mask[:,:,2]>.5)&occupied;linear=lin(base);linear[core]*=1.16;base=np.clip(enc(linear),0,1)
# Dilate all maps into every UV gutter before feathering the semantic hair edge.
_,near=nd.distance_transform_edt(~occupied,return_indices=True);base=base[near[0],near[1]];mask=mask[near[0],near[1]];normal=normal[near[0],near[1]];classes=classes[near[0],near[1]]
mask=np.stack([nd.gaussian_filter(mask[:,:,c],.6) for c in range(4)],-1);mask/=np.maximum(mask.sum(2,keepdims=True),1)
rough=sampled('roughness')[:,:,0];rough=np.maximum(rough,np.where(classes==6,.3,np.where(classes==1,.82,.9)));orm=np.stack([np.ones_like(rough),rough,np.zeros_like(rough)],-1)[near[0],near[1]]
for name,a in [('basecolor',base),('normal',normal),('orm',orm),('region_mask',mask)]:
 save(a,T/f'mep_head_{name}_round2.png')
 for level in range(4):shutil.copy2(T/f'mep_head_{name}_round2.png',T/f'lod{level}/mep_head_{name}.png')
Image.fromarray(classes).save(T/'mep_head_material_classes_round2.png')
# Reparameterise only exposed body skin; leather and cloth retain their previous appearance.
for level in range(4):
 folder=T/f'lod{level}';backup=P/f'review/round2/before/textures/lod{level}';d=np.load(P/f'work/round1_mep_lod{level}.npz');part=d['piece'];used=part>=0;a=np.array(Image.open(backup/'mep_basecolor.png').convert('RGB'))/255;body_skin=np.isin(part,[2,3,5,6]);a=rank_grade(a,body_skin)
 # Existing leather uses the same channel: map its old luminance to the new native ramp.
 leather=np.isin(part,[10,11]);old=lin(np.array(Image.open(backup/'mep_basecolor.png').convert('RGB'))/255)@L;xx=np.clip((old-oldskin['range'][0])/(oldskin['range'][1]-oldskin['range'][0]),0,1);ys=np.array(oldskin['colors'])@L;desired=np.interp(xx,np.linspace(0,1,16),ys);newys=np.array(newramps['mep_a']['colors'])@L;value=np.interp(desired,newys,np.linspace(0,1,16));a[leather]=enc(value[leather,None])
 sash=part==7;co=d['pos'];weave=.50+.008*np.sin(co[:,:,0]*2600)*np.sin(co[:,:,2]*2800)+.012*np.sin(co[:,:,2]*180);a[sash]=weave[sash,None]
 _,nn=nd.distance_transform_edt(~used,return_indices=True);a=a[nn[0],nn[1]];save(a,folder/'mep_basecolor.png')
 normalbody=np.array(Image.open(backup/'mep_normal.png').convert('RGB'));normalbody[sash]=[128,128,255];normalbody=normalbody[nn[0],nn[1]];Image.fromarray(normalbody).save(folder/'mep_normal.png')
# Match the head's skin input distribution to the body's, then fit native mean and highlight together.
from scipy.optimize import least_squares
body=image(T/'lod0/mep_basecolor.png');bd=np.load(P/'work/round1_mep_lod0.npz');bm=np.array(Image.open(T/'lod0/mep_region_mask.png'))/255;bodycore=np.isin(bd['piece'],[2,3,5,6])&(bm[:,:,3]>.99);bodylum=(lin(body)@L)[bodycore]
head=image(T/'lod0/mep_head_basecolor.png');hm=np.array(Image.open(T/'lod0/mep_head_region_mask.png'))/255;headcore=(hm[:,:,3]>.99)&occupied;hl=lin(head)@L;hs=np.sort(hl[headcore]);quant=np.searchsorted(hs,hl)/len(hs);mapped=np.interp(quant,(np.arange(len(bodylum))+.5)/len(bodylum),np.sort(bodylum));hlinear=lin(head);hlinear[skin]=mapped[skin,None];head=np.clip(enc(hlinear),0,1);head=head[near[0],near[1]]
save(head,T/'mep_head_basecolor_round2.png')
for level in range(4):shutil.copy2(T/'mep_head_basecolor_round2.png',T/f'lod{level}/mep_head_basecolor.png')
measurements={};headlum=(lin(image(T/'lod0/mep_head_basecolor.png'))@L)[headcore]
for tier in 'abc':
 reg=cfg['materials'][0]['ramps']['mep_'+tier][3];colors=np.array(reg['colors']);ys=colors@L;target=native_stats[tier]
 def output(lum,params):return np.interp(lum,np.linspace(0,1,16),np.maximum(ys*params[0]+params[1],.000001))
 def error(params):
  val=output(bodylum,params);return [(val.mean()-target['mean'])/target['mean'],(np.percentile(val,90)-target['p90'])/target['p90']]
 fit=least_squares(error,[1,0],bounds=([.1,-.1],[3,.1]));newy=np.maximum(ys*fit.x[0]+fit.x[1],.000001);colors*=np.divide(newy,ys)[:,None]
 for entry in cfg['materials'][:2]:entry['ramps']['mep_'+tier][3]['colors']=colors.tolist()
 row={}
 for name,lum in [('body',bodylum),('head',headlum)]:
  val=np.interp(lum,np.linspace(0,1,16),colors@L);row[name]={'mean':float(val.mean()),'p90':float(np.percentile(val,90))}
  assert abs(val.mean()/target['mean']-1)<.04 and abs(np.percentile(val,90)/target['p90']-1)<.04,(tier,name,row)
 measurements[tier]=row
(T/'mep_ramps.json').write_text(json.dumps(cfg,indent=2))
report={'native':native_stats,'measured':measurements,'head_skin_pixels':int(skin.sum()),'method':'HD front reference registered to mesh eye/nose/lip landmarks over regenerated Meshy maps; head and exposed body skin quantile-mapped to native palette, same shared ramps','head_set_resolution':[1024,1024]}
(P/'review/round2/skin_calibration.json').write_text(json.dumps(report,indent=2));print('HEAD_TEXTURES',report)

# The shared atlas merger requires equal map heights; preserve the existing lower-LOD body rebakes at 1K.
for level in [2,3]:
 for name in ['basecolor','normal','orm','region_mask']:
  path=T/f'lod{level}/mep_{name}.png';source=(P/f'review/round2/before/textures/lod{level}/mep_{name}.png') if name not in ['basecolor','normal'] else path
  im=Image.open(source);method=Image.Resampling.NEAREST if name=='region_mask' else Image.Resampling.BILINEAR
  im=Image.merge(im.mode,[c.resize((1024,1024),method) for c in im.split()]);im.save(path)
