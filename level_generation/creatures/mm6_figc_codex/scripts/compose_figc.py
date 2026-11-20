"""Compose one body/head set and three native-palette region ramps; no baked runtime tiers."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));import normal_map_convention
N=1024;PALS={'figc_a':212,'figc_b':211,'figc_c':210};LUMA=np.array([.2126,.7152,.0722])
def load(p,mode='RGB'):return np.asarray(Image.open(p).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p)
def hsv(a):return np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255
# Matched native pixels retain exact palette correspondence.
samples={k:[[],[],[]] for k in PALS}
for view in range(5):
 ims={k:np.asarray(Image.open(P.parent/'mm6_figc/native_variants'/f'figcsta{view}_{pal}.png').convert('RGBA'),float)/255 for k,pal in PALS.items()}
 a=ims['figc_a'];h=hsv(a[:,:,:3]);hu=h[:,:,0]*360;sa=h[:,:,1];va=h[:,:,2];valid=(a[:,:,3]>.5)&(va>.10)
 masks=[valid&(sa>.3)&(hu>20)&(hu<65),valid&(sa>.3)&((hu<20)|(hu>330)),valid&(sa<.20)&(va>.18)]
 for k in PALS:
  for i,m in enumerate(masks):samples[k][i].append(ims[k][:,:,:3][m])
samples={k:[np.concatenate(a) for a in v] for k,v in samples.items()}
sets={}
for suffix,job,layer in [('', 'retexture_v1','UVMap'),('_head','head_retexture_v1','HeadUV')]:
 base=load(P/'meshy'/job/'texture_urls_0_base_color.png');norm=load(P/'meshy'/job/'texture_urls_0_normal.png');rough=load(P/'meshy'/job/'texture_urls_0_roughness.png','L')
 if normal_map_convention.measure(np.uint8(norm*255))<-.15:norm[:,:,1]=1-norm[:,:,1]
 rz=np.load(P/'work'/f'uvraster_{layer}.npz');piece,pos=rz['piece'],rz['pos'];cov=piece>=0;hh=hsv(base);hu=hh[:,:,0]*360;sa=hh[:,:,1];va=hh[:,:,2]
 if suffix:
  metal=cov&np.isin(piece,[3,10,11]);red=cov&(piece==0)&(sa>.38)&((hu<18)|(hu>330));ochre=np.zeros_like(cov);skin=cov&~metal&~red
  mail=cov&(piece==0)&(pos[:,:,2]<1.495);red[:]=False;skin=cov&~metal&~mail
 else:
  skin=np.isin(piece,[1,2]);cloth=(piece==0)&(pos[:,:,2]>.60)&(pos[:,:,2]<1.43)&(sa>.35)
  ochre=cloth&(hu>20)&(hu<65);red=(cloth&~ochre)|(cov&np.isin(piece,[7,8])&(sa>.4)&((hu<20)|(hu>330)))
  metal=cov&np.isin(piece,[7,8,9,12,13,14,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39])&~red
  # Right bracer is a separate part; the left is fused to its mail sleeve.
  metal |= (piece==4)&(pos[:,:,2]<1.03)
  metal |= (piece==0)&(pos[:,:,2]<.24)
  mail=cov&~skin&~cloth&~metal&~red&np.isin(piece,[0,4,5]);mail &= pos[:,:,2]>.2
 base[mail]*=.48
 if suffix and mail.any():
  lum=base@LUMA;base[mail]=np.repeat((lum[mail]*.24/max(np.median(lum[mail]),.02))[:,None],3,axis=1)
 if metal.any():base[metal]*=.55/max(np.median(base[metal]@LUMA),.02)
 # Keep body hands and face in the same neutral skin range.
 if skin.any():
  med=np.median(base[skin],0);base[skin]*=np.array([.45,.30,.19])/np.maximum(med,.03)
 spec=np.full((N,N),.25);rgh=np.clip(.65+(rough-.5)*.15,.2,1)
 spec[metal]=.40;rgh[metal]=np.clip(.64+(rough[metal]-.5)*.14,.55,.75);spec[skin]=.35;rgh[skin]=.6;spec[mail]=.6;rgh[mail]=.55
 masks=[ochre.astype(float),red.astype(float),metal.astype(float)]
 # Extend region ids and material response into UV gutters to keep mip edges clean.
 idx=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
 masks=[ndimage.gaussian_filter(m[tuple(idx)],.5) for m in masks];spec=spec[tuple(idx)];rgh=rgh[tuple(idx)]
 sets[suffix]={'base':base,'normal':norm,'spec':spec,'rough':rgh,'mask':masks,'cov':cov,'piece':piece,'pos':pos}
# The same ramps are shared by body and head for the runtime head-atlas merge.
ramps={k:[] for k in PALS};counts={}
for i,label in enumerate(['ochre_cloth','red_cloth','steel']):
 lum=np.concatenate([R.luminance(d['base'])[d['mask'][i]>.9] for d in sets.values()]);lo,hi=np.percentile(lum,[1,99]);hi=max(hi,lo+.001)
 order=np.argsort(R.srgb_to_linear(samples['figc_a'][i])@LUMA)
 for k in PALS:
  native=R.srgb_to_linear(samples[k][i])[order];stops=[];hue=R.srgb_to_linear(np.median(samples[k][i],0));native_luminance=np.sort(native@LUMA)
  for j in range(16):
   q=np.clip(np.searchsorted(np.sort(lum),lo+j/15*(hi-lo))/len(lum),.025,.985);c=int(q*(len(native)-1));w=max(5,len(native)//100)
   shade=float(np.median(native_luminance[max(0,c-w):c+w]))*1.4
   # Review round 1: keep steel dull grey consistently across native tier ramps.
   color=np.clip(hue*shade/max(float(hue@LUMA),.0001),0,1)
   if label=='steel':color=np.array([.98,1,1.015])*(.025+.265*(j/15)**.9)
   stops.append(color.tolist())
  ramps[k].append({'range':[float(lo),float(hi)],'colors':stops})
 counts[label]=len(order)
# Atlas swatches for locally modelled metal, leather and shield decoration.
d=sets[''];occ=ndimage.binary_dilation(d['cov'],iterations=9);sw={}
colors=[(75,40,18),(160,166,174),(215,220,225),(151,103,31),(36,30,26)]
for kind,rgb in enumerate(colors):
 found=False
 for y in range(N-16,16,-12):
  for x in range(N-16,16,-12):
   if not occ[y-8:y+8,x-8:x+8].any():found=True;break
  if found:break
 assert found
 ys,xs=slice(y-7,y+7),slice(x-7,x+7);yy,xx=np.mgrid[-7:7,-7:7];grain=1+.04*np.sin(xx*2.3+yy*1.7)
 d['base'][ys,xs]=np.array(rgb)/255*grain[:,:,None];d['normal'][ys,xs]=[.5,.5,1];d['spec'][ys,xs]=.85 if kind in [1,2,3] else .25;d['rough'][ys,xs]=.36 if kind in [1,2,3] else .75
 for m in d['mask']:m[ys,xs]=0
 # Native shield steel and ochre share the corresponding tier regions.
 if kind in [1,2]:d['mask'][2][ys,xs]=1
 if kind==3:d['mask'][0][ys,xs]=1
 occ[y-12:y+12,x-12:x+12]=True;sw[str(kind)]=[(x+.5)/N,1-(y+.5)/N,4/N]
(T/'figc_prop_swatches.json').write_text(json.dumps(sw,indent=2))
cfg={'variants':list(PALS),'materials':[],'native_palette_samples':counts}
for suffix,d in sets.items():
 prefix='FighterChainHead' if suffix else 'FighterChain'
 save(d['base'],T/f'figc{suffix}_basecolor_1k.png');save(d['normal'],T/f'figc{suffix}_normal_1k.png');save(np.stack([d['spec'],d['rough'],np.zeros((N,N))],-1),T/f'figc{suffix}_metal_rough_1k.png')
 R.write_mask(d['mask'],T/f'figc{suffix}_region_mask.png',size=N)
 cfg['materials'].append({'base':prefix+'_A','prefix':prefix,'mask':f'figc{suffix}_region_mask.png','regions':['ochre_cloth','red_cloth','steel'],'palettes':PALS,'ramps':ramps})
(T/'figc_ramps.json').write_text(json.dumps(cfg,indent=2));print('TEXTURES composed',counts)
