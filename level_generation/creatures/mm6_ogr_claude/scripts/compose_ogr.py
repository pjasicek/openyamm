"""Ogre body/head textures and spike-only native palette variants, with per-texel material response."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as R
T=P/'textures';T.mkdir(exist_ok=True);N=1024

def load(path,mode='RGB'):
 return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255

def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)

def hsv(a):
 v=np.array(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255
 return v[...,0]*360,v[...,1],v[...,2]

def pad(a,cov):
 _,(y,x)=ndimage.distance_transform_edt(~cov,return_indices=True)
 return a[y,x]

def lin_to_srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)

bjob=P/'meshy/retexture_v1';hjob=P/'meshy/head_retexture_v1'
r=np.load(P/'work/uvraster_UVMap.npz');hr=np.load(P/'work/uvraster_HeadUV.npz')
piece,pos=r['piece'],r['pos'];hp,hpos=hr['piece'],hr['pos'];cov=piece>=0;hcov=hp>=0
base=load(bjob/'texture_urls_0_base_color.png');head=load(hjob/'texture_urls_0_base_color.png')
normal=load(bjob/'texture_urls_0_normal.png');hnormal=load(hjob/'texture_urls_0_normal.png')
h,s,v=hsv(base);hh,hs,hv=hsv(head)
classes=np.zeros((N,N),np.uint8);classes[cov]=11;classes[piece==0]=1
classes[np.isin(piece,[4,5,6,7,14,19,24,25])]=8
classes[np.isin(piece,[2,3,8,9,10,11,18,26,29,30,31,35])]=9
classes[piece==1]=5
spikes=np.isin(piece,[12,13,27,28,32,33,34,36]);classes[spikes]=4
fj=json.loads((P/'work/finger_joints.json').read_text());near=np.zeros_like(cov)
for side in fj.values():
 for n,point in side.items():
  if n.endswith('_tip'):near|=np.linalg.norm(pos-np.array(point),axis=-1)<.035
near|=(pos[...,2]<.055)&(pos[...,1]<-.06)
claws=(piece==0)&near&(h>20)&(h<70)&(v>.5)&(s<.6);classes[claws]=4
hc=np.zeros((N,N),np.uint8);hc[hcov]=1;hc[np.isin(hp,[20,21])]=5
eye=np.zeros_like(hcov)
for c in [(-.042,-.084,1.594),(.027,-.084,1.594)]:
 d=(hpos-np.array(c))/np.array([.019,.025,.013]);eye|=(d*d).sum(-1)<1
hc[eye&hcov]=6
mouth=(hp==0)&(abs(hpos[...,0]+.008)<.045)&(hpos[...,2]>1.50)&(hpos[...,2]<1.545)&(hpos[...,1]<-.065)&(hv<.25)
hc[mouth]=7
neck_b=(classes==1)&(pos[...,2]>1.32)&(pos[...,2]<1.44)&(abs(pos[...,0])<.16)
neck_h=(hc==1)&(hpos[...,2]<1.46)
assert neck_b.sum()>100 and neck_h.sum()>100,(neck_b.sum(),neck_h.sum())
gain=np.median(base[neck_b],axis=0)/np.maximum(np.median(head[neck_h],axis=0),.01)
assert (gain>.4).all() and (gain<1.8).all(),gain
head[hc==1]=np.clip(head[hc==1]*gain,0,1)
print('HEAD_NECK_GAIN',gain.tolist(),'texels',int(neck_b.sum()),int(neck_h.sum()))
# Match the actual shared edge locally; a global neck average left a polygon-shaped colour boundary.
from scipy.spatial import cKDTree
seams=json.loads((P/'work/seam_samples.json').read_text())
centres=np.array([s['pos'] for s in seams]);tree=cKDTree(centres)
def sample_uv(img,values):
 uv=np.array(values);xy=np.clip(np.floor(uv*N).astype(int),0,N-1)
 return img[N-1-xy[:,1],xy[:,0]]
bcol=sample_uv(base,[s['body'] for s in seams]);hcol=sample_uv(head,[s['head'] for s in seams]);deltas=bcol-hcol
hd,hi=tree.query(hpos[hc==1],k=12);weight=1/np.maximum(hd,.008)**2
correction=(deltas[hi]*weight[...,None]).sum(1)/weight.sum(1)[:,None]
u=np.clip(1-hd[:,0]/.07,0,1);fade=u*u*(3-2*u)
head[hc==1]=np.clip(head[hc==1]+correction*fade[:,None],0,1)
for coords,covered,nmap in [(pos,cov,normal),(hpos,hcov,hnormal)]:
 dist,_=tree.query(coords[covered],k=1);u=np.clip(dist/.008,0,1)
 nmap[covered]=nmap[covered]*u[:,None]+np.array([.5,.5,1])*(1-u[:,None])
after=sample_uv(head,[s['head'] for s in seams])
print('NECK_SEAM_MAE',float(abs(bcol-hcol).mean()*255),'->',float(abs(bcol-after).mean()*255))
# MR red is the current runtime's specular mask; class maps remain available for future refinements.
response={0:(0,1,0),1:(0,.82,0),4:(.35,.48,0),5:(.4,.43,0),6:(1,.18,0),7:(.2,.75,0),8:(.08,.88,0),9:(1,.5,.55),11:(.1,.85,0)}
def mr(c):
 out=np.empty((N,N,3))
 for k,t in response.items():out[c==k]=t
 return out
orm=pad(mr(classes),cov);horm=pad(mr(hc),hcov)
base=pad(base,cov);head=pad(head,hcov);normal=pad(normal,cov);hnormal=pad(hnormal,hcov)
# Only native palette-changing spike colours enter the ramp; skin and equipment stay shared.
paldir=P.parents[2]/'assets_dev/worlds/mm6/textures'
pals={f'ogr_{c}':np.frombuffer((paldir/f'pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for c,n in zip('abc',[783,784,785])}
idx=np.where(np.max(abs(pals['ogr_a']-pals['ogr_c']),axis=1)>.01)[0]
order=idx[np.argsort(R.luminance(pals['ogr_a'][idx]))]
L=R.luminance(base);lo,hi=np.percentile(L[spikes],[1,99]);assert hi-lo>.001
ramps={}
for tier,pal in pals.items():
 stops=np.stack([np.interp(np.linspace(0,len(order)-1,16),np.arange(len(order)),pal[order,c]) for c in range(3)],axis=1)
 # A small lightness gain leaves room for the engine's lighting over the native shaded pixels.
 colors=R.srgb_to_linear(np.clip(stops*1.2,0,1))
 ramps[tier]=[{'range':[float(lo),float(hi)],'colors':colors.round(6).tolist()}]
mask=pad(spikes.astype(float),cov)
# The sword samples separate atlas swatches, outside every body island and the variant mask.
occ=ndimage.binary_dilation(cov,iterations=8);sw={};swpix=np.zeros_like(cov)
for name,rgb in {'blade':(154,153,148),'edge':(209,207,192),'gold':(131,107,61),'grip':(57,36,22)}.items():
 found=False
 for y in range(N-12,12,-4):
  for x in range(N-12,12,-4):
   if not occ[y-6:y+6,x-6:x+6].any():found=True;break
  if found:break
 assert found,'no sword atlas space'
 base[y-6:y+6,x-6:x+6]=np.array(rgb)/255;normal[y-6:y+6,x-6:x+6]=(.5,.5,1)
 orm[y-6:y+6,x-6:x+6]=response[8 if name=='grip' else 9]
 occ[y-9:y+9,x-9:x+9]=True;swpix[y-9:y+9,x-9:x+9]=True
 sw[name]=[(x+.5)/N,1-(y+.5)/N,3/N]
mask=ndimage.gaussian_filter(mask,.65);mask[swpix]=0
for prefix,b,n,m,cl in [('ogr',base,normal,orm,classes),('ogr_head',head,hnormal,horm,hc)]:
 save(b,T/f'{prefix}_basecolor_1k.png');save(n,T/f'{prefix}_normal_1k.png');save(m,T/f'{prefix}_metal_rough_1k.png');Image.fromarray(cl).save(T/f'{prefix}_material_classes.png')
R.write_mask([mask],T/'ogr_region_mask.png',size=N)
R.write_mask([np.zeros_like(mask)],T/'ogr_head_region_mask.png',size=N)
cfg={'variants':list(pals),'materials':[{'base':name,'prefix':name.removesuffix('_A'),'mask':maskfile,'regions':['spikes'],'ramps':ramps,'palettes':dict(zip(pals,[783,784,785]))} for name,maskfile in [('Ogre_A','ogr_region_mask.png'),('OgreHead_A','ogr_head_region_mask.png')]]}
(T/'ogr_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');(T/'ogr_sword_swatches.json').write_text(json.dumps(sw,indent=2)+'\n')
report={'head_neck_gain_rgb':gain.tolist(),'palette_indices':order.tolist(),'body_class_texels':{str(k):int((classes==k).sum()) for k in np.unique(classes)},'head_class_texels':{str(k):int((hc==k).sum()) for k in np.unique(hc)},'specular_channel':'MR.R; openyamm_specular_mask'}
assert report['body_class_texels'].get('11',0)==0,report
(T/'composition_report.json').write_text(json.dumps(report,indent=2)+'\n');print('TEXTURES',json.dumps(report))
