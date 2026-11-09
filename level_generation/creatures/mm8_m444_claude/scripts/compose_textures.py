"""Shared 1K body/head maps, semantic surface classes and native palette 445/446/447 cloth ramps."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy import ndimage
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared'));import region_variants as R
T=p/'textures';T.mkdir(exist_ok=True);N=1024
PALS={'m444_a':445,'m444_b':446,'m444_c':447}
def load(path,mode='RGB'):
 return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path)
def hsv(rgb):return np.asarray(Image.fromarray(np.uint8(np.clip(rgb,0,1)*255)).convert('HSV'),float)/255
surface={'skin':(.15,.62),'hair':(.08,.87),'leather':(.35,.72),'cloth':(.06,.85),'metal':(.9,.35),'eyes':(.7,.25),'mouth':(.3,.6)}
class_ids={'skin':1,'hair':2,'leather':8,'cloth':8,'metal':9,'eyes':6,'mouth':7}
sets={}
for part,layer in [('body','UVMap'),('head','HeadUV')]:
 M=p/f'meshy/texture_{part}_v1';base=load(M/'texture_urls_0_base_color.png');rough=load(M/'texture_urls_0_roughness.png','L');normal=load(M/'texture_urls_0_normal.png');r=np.load(p/f'work/uvraster_{layer}.npz');piece,pos=r['piece'],r['pos'];cov=piece>=0;H=hsv(base)
 green=cov&(H[...,0]>.18)&(H[...,0]<.55)&(H[...,1]>.22)
 if part=='body':
  colored=cov&(np.isin(piece,[2,12,14])|((piece==1)&green&(pos[...,2]>1.28)))
  masks={'skin':cov&np.isin(piece,[3,4]),'cloth':cov&np.isin(piece,[1,2,12,14]),'metal':cov&(np.isin(piece,[18,32])|((piece==10)&(pos[...,2]<.68)))}
  masks['leather']=cov&~np.any(list(masks.values()),axis=0)
 else:
  colored=green&(piece==0)&(pos[...,2]<1.47)
  hair=(piece==0)&~colored&((pos[...,2]<1.50)&(pos[...,1]<-.055))
  masks={'hair':hair,'cloth':colored,'eyes':cov&np.isin(piece,[19,20]),'mouth':cov&np.isin(piece,[23,24])}
  masks['skin']=cov&~np.any(list(masks.values()),axis=0)
 # One skin albedo retains fine pores and wrinkles without Meshy's broad salmon patches.
 skin=masks['skin'];lum=base@np.array([.2126,.7152,.0722]);weight=ndimage.gaussian_filter(skin.astype(float),12);blur=ndimage.gaussian_filter(lum*skin,12)/np.maximum(weight,1e-6);detail=np.clip(lum/np.maximum(blur,.02),.55,1.4)
 base[skin]=np.array([188,140,107])/255*detail[skin,None]
 idx=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True);pad=lambda a:a[tuple(idx)]
 spec=np.zeros((N,N));rgh=np.zeros((N,N));classes=np.zeros((N,N),np.uint8)
 for i,(kind,mask) in enumerate(masks.items(),1):
  a,b=surface[kind];spec[mask]=a;rgh[mask]=np.clip(b+.25*(rough[mask]-np.median(rough[mask])),.2,1);classes[mask]=class_ids[kind]
 # Keep woven detail subtle; palette remapping otherwise amplifies Meshy's high-frequency cloth noise.
 cloth=masks['cloth'];w=ndimage.gaussian_filter(cloth.astype(float),2)
 smooth=np.stack([ndimage.gaussian_filter(base[...,c]*cloth,2)/np.maximum(w,1e-6) for c in range(3)],-1)
 base[cloth]=smooth[cloth]+.18*(base[cloth]-smooth[cloth])
 vectors=normal*2-1;vectors[cloth,:2]*=.25
 vectors[skin,:2]*=.6
 vectors/=np.maximum(np.linalg.norm(vectors,axis=-1,keepdims=True),1e-6);normal=(vectors+1)*.5
 # Mask gutters are padded before the slight antialias blur, avoiding coloured seam halos.
 mask=ndimage.gaussian_filter(pad(colored.astype(float)),.55)
 sets[part]={'base':base,'normal':normal,'mr':np.stack([pad(spec),pad(rgh),np.zeros_like(spec)],-1),'mask':mask,'classes':classes,'cov':cov,'colored':colored}
# Only the changing native cloth pixels supply the ramp; unchanged skin/leather stay outside it.
cols={k:[] for k in PALS}
for v in range(5):
 ims={k:np.asarray(Image.open(p.parent/f'mm8_m444/native_variants/m444sa{v}_{pal}.png').convert('RGBA'),float)/255 for k,pal in PALS.items()};a=ims['m444_a'];changed=(a[...,3]>.5)&(np.maximum(np.max(np.abs(a[...,:3]-ims['m444_b'][...,:3]),axis=2),np.max(np.abs(a[...,:3]-ims['m444_c'][...,:3]),axis=2))>8/255)
 for k in PALS:cols[k].append(ims[k][...,:3][changed])
cols={k:np.concatenate(v) for k,v in cols.items()};a=cols['m444_a'];keep=(a[:,1]>.15)&(a[:,1]>a[:,0]*1.2)&(a[:,1]>a[:,2]*1.12);order=np.argsort(R.luminance(cols['m444_a'][keep]));lum=np.sort(R.luminance(sets['body']['base'])[sets['body']['colored']]);lo,hi=np.percentile(lum,[2,98]);ramps={}
for k in PALS:
 rgb=R.srgb_to_linear(cols[k][keep])[order];stops=[]
 for i in range(16):
  q=.2+.6*i/15;j=int(q*(len(rgb)-1));w=max(4,len(rgb)//50);stops.append(np.clip(np.median(rgb[max(0,j-w):j+w],axis=0)*1.35,0,1))
 ramps[k]=[{'range':[float(lo),float(hi)],'colors':np.round(stops,6).tolist()}]
# Compact native sword swatches occupy unused body texels and never receive a tier colour.
S={'blade':(184,192,196),'edge':(225,230,232),'gold':(151,119,64),'grip':(60,38,23)};sw={};body=sets['body'];occupied=ndimage.binary_dilation(body['cov'],iterations=9)
for k,rgb in S.items():
 ys,xs=np.where(~occupied);candidates=np.where((xs>12)&(xs<N-12)&(ys>12)&(ys<N-12))[0];assert len(candidates);j=int(candidates[-1]);x,y=int(xs[j]),int(ys[j]);sl=(slice(y-5,y+6),slice(x-5,x+6));body['base'][sl]=np.array(rgb)/255;body['normal'][sl]=(.5,.5,1);body['mr'][sl]=(.9,.35,0) if k!='grip' else (.3,.75,0);body['mask'][sl]=0;occupied[y-14:y+15,x-14:x+15]=True;sw[k]=[(x+.5)/N,1-(y+.5)/N,3/N]
config={'variants':list(PALS),'materials':[]}
for part,data in sets.items():
 prefix='smuggler' if part=='body' else 'smuggler_head';name='Smuggler' if part=='body' else 'SmugglerHead'
 for key,suffix in [('base','basecolor'),('normal','normal'),('mr','metal_rough')]:save(data[key],T/f'{prefix}_{suffix}_1k.png')
 R.write_mask([data['mask']],T/f'{prefix}_region_mask.png',size=N);Image.fromarray(data['classes']).save(T/f'{prefix}_material_classes.png')
 config['materials'].append({'base':name+'_A','prefix':name,'mask':f'{prefix}_region_mask.png','regions':['cloth'],'palettes':PALS,'ramps':ramps})
 print('TEXTURE',part,'covered',int(data['cov'].sum()),'cloth',int(data['colored'].sum()))
(T/'smuggler_ramps.json').write_text(json.dumps(config,indent=2));(T/'smuggler_sword_swatches.json').write_text(json.dumps(sw,indent=2));(T/'material_class_legend.json').write_text(json.dumps({'class_ids':class_ids,'surfaces':surface,'skin_albedo_srgb':[188,140,107],'native_cloth_pixels':int(keep.sum()),'ramp_gain_linear':1.35},indent=2))
