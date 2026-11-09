"""Shared body/head/wand maps, measured native cloth ramps and per-texel material response."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
p=Path(__file__).resolve().parents[1];root=p.parents[2]
sys.path.insert(0,str(p.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(root/'tools'));import normal_map_convention as NC
T=p/'textures';T.mkdir(exist_ok=True);N=1024;SKIN=np.array([.54,.36,.23]);normal_reports={}
def load(path,n=N):return np.asarray(Image.open(path).convert('RGB').resize((n,n),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def hsv(a):
 h=np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255
 return h[...,0]*360,h[...,1],h[...,2]
def pad(a,cov):
 _,(y,x)=ndimage.distance_transform_edt(~cov,return_indices=True);return a[y,x]
def srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def skin(img,mask):
 L=R.luminance(img);blur=ndimage.gaussian_filter(np.where(mask,L,0),6)/np.maximum(ndimage.gaussian_filter(mask.astype(float),6),1e-4)
 detail=np.clip((L/np.maximum(blur,1e-4))**1.15,.5,1.5);out=img.copy();out[mask]=srgb(np.clip(R.srgb_to_linear(SKIN)*detail[mask,None],0,1));return out
def normal(path,n=N):
 raw=np.asarray(Image.open(path).convert('RGB')).copy();correlation=NC.measure(raw);flip=correlation<=-.15
 if flip:raw[...,1]=255-raw[...,1]
 normal_reports[str(path.relative_to(p))]={'correlation':correlation,'flipped_green':bool(flip)}
 out=np.asarray(Image.fromarray(raw).resize((n,n),Image.Resampling.LANCZOS),float)/255
 v=out*2-1;v/=np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-6);return v*.5+.5
def head_image(path):
 im=Image.open(path).convert('RGB').resize((N,round(.94*N)),Image.Resampling.LANCZOS)
 out=Image.new('RGB',(N,N),tuple(np.uint8(SKIN*255)));out.paste(im,(0,N-im.height));return np.asarray(out,float)/255
r=np.load(p/'work/uvraster_UVMap.npz');hr=np.load(p/'work/uvraster_HeadUV.npz');piece,pos=r['piece'],r['pos'];hp,hpos=hr['piece'],hr['pos'];cov=piece>=0;hcov=hp>=0
base=load(p/'meshy/body_retexture_v1/texture_urls_0_base_color.png');head=load(p/'texturing/head_base_bake.png')
bn=normal(p/'meshy/body_retexture_v1/texture_urls_0_normal.png');hn=normal(p/'texturing/head_normal_bake.png')
h,s,v=hsv(base);hh,hs,hv=hsv(head)
classes=np.zeros((N,N),np.uint8);classes[cov]=8;classes[np.isin(piece,[0,2,3,4])]=1;classes[np.isin(piece,[5,9,10,*range(13,25)])]=9
joints=json.loads((p/'work/joints_final.json').read_text())['joints']
for side in 'LR':
 a,b=np.array(joints[side+'_Forearm']),np.array(joints[side+'_Hand']);d=b-a;t=((pos-a)*d).sum(-1)/(d*d).sum();dist=np.linalg.norm(pos-(a+t[...,None]*d),axis=-1)
 classes[(piece==0)&(t>.12)&(t<.94)&(dist<.105)]=8
classes[(piece==2)&(pos[...,2]<.42)]=8
classes[(piece==2)&(pos[...,2]>.76)&(v<.26)]=8
green=(h>65)&(h<170)&(s>.18)
cloth=(piece==1)&((pos[...,2]>1.0)|(r['cape']>.5)|(r['loin']>.5)|green)
# Black shorts and the leather belt are outside the native cloth palette change.
cloth&=~((pos[...,2]>.90)&(pos[...,2]<.99)&(~green)&(r['cape']<.5)&(r['loin']<.5))
hc=np.zeros((N,N),np.uint8);hc[hcov]=1
hair=hcov&(hpos[...,2]>1.59);hc[hair]=2
tie=hair&(hh>15)&(hh<70)&(hs>.25)&(hv>.48)&(hpos[...,2]<1.625);hc[tie]=8
tooth=hcov&(hpos[...,1]<-.18)&(hpos[...,2]>1.39)&(hpos[...,2]<1.448)&(hs<.5)&(hv>.42);hc[tooth]=5
mouth=hcov&(abs(hpos[...,0]+.017)<.052)&(hpos[...,1]<-.185)&(hpos[...,2]>1.397)&(hpos[...,2]<1.434)&((hv<.22)|(hh>330)|(hh<17));hc[mouth&~tooth]=7
eye=np.zeros_like(hcov)
for c in [(-.056,-.187,1.488),(.018,-.187,1.489)]:
 d=(hpos-np.array(c))/np.array([.012,.012,.006]);eye|=(d*d).sum(-1)<1
hc[eye&hcov]=6
base=skin(base,classes==1);head=skin(head,hc==1)
for img,path,covered in [(base,p/'work/ao_UVMap.png',cov),(head,p/'work/ao_HeadUV.png',hcov)]:
 ao=load(path)[...,0];img[covered]*=(.75+.25*np.maximum(ao[covered],.4))[:,None]
# Match the shared neckline by its actual per-corner UV coordinates after transfer.
seams=json.loads((p/'work/seam_samples.json').read_text());tree=cKDTree(np.array([x['pos'] for x in seams]))
def sample_uv(img,values):
 xy=np.clip(np.floor(np.array(values)*N).astype(int),0,N-1);return img[N-1-xy[:,1],xy[:,0]]
bcol=sample_uv(pad(base,cov),[x['body'] for x in seams]);hcol=sample_uv(pad(head,hcov),[x['head'] for x in seams]);delta=bcol-hcol
mask=hc==1;dist,idx=tree.query(hpos[mask],k=12);w=1/np.maximum(dist,.008)**2;target=(bcol[idx]*w[...,None]).sum(1)/w.sum(1)[:,None];u=np.clip((.06-dist[:,0])/.04,0,1);u=u*u*(3-2*u);head[mask]=head[mask]*(1-u[:,None])+target*u[:,None]
for coords,covered,nmap in [(pos,cov,bn),(hpos,hcov,hn)]:
 dist,_=tree.query(coords[covered],k=1);u=np.clip(dist/.008,0,1);nmap[covered]=nmap[covered]*u[:,None]+np.array([.5,.5,1])*(1-u[:,None])
after=sample_uv(pad(head,hcov),[x['head'] for x in seams]);seam_mae=float(np.mean(abs(bcol-after))*255)
response={0:(0,1,0),1:(0,.82,0),2:(0,.94,0),3:(0,.85,0),4:(.35,.48,0),5:(.4,.42,0),6:(1,.16,0),7:(.15,.65,0),8:(.04,.86,0),9:(1,.43,0),10:(.06,.85,0),11:(.8,.20,0)}
def mr(c):
 out=np.zeros((*c.shape,3))
 for k,value in response.items():out[c==k]=value
 return out
palroot=root/'assets_dev/worlds/mm8/textures';pals={f'm540_{c}':np.frombuffer((palroot/f'Pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for c,n in zip('abc',[541,542,543])}
pa=pals['m540_a'];changed=np.max(abs(pa-pals['m540_c']),axis=1)>.01
used=set()
for name,row in json.loads((p/'native_inventory.json').read_text())['sources'].items():
 if name.startswith('m540s'):used.update(np.unique(np.asarray(Image.open(root/row['path']))).tolist())
idx=np.array(sorted(i for i in used if changed[i] and pa[i,1]>pa[i,0]*1.15 and pa[i,1]>pa[i,2]*1.08),int);assert len(idx)>20,idx
order=idx[np.argsort(R.luminance(pa[idx]))];L=R.luminance(base);lo,hi=np.percentile(L[cloth],[2,98]);assert hi-lo>.01
ramps={}
for tier,pal in pals.items():
 stops=np.stack([np.interp(np.linspace(0,len(order)-1,16),np.arange(len(order)),pal[order,c]) for c in range(3)],axis=1)
 ramps[tier]=[{'range':[float(lo),float(hi)],'colors':R.srgb_to_linear(np.clip(stops*1.35,0,1)).round(6).tolist()}]
for prefix,img,nmap,cl,covered in [('m540',base,bn,classes,cov),('m540_head',head,hn,hc,hcov)]:
 save(pad(img,covered),T/f'{prefix}_basecolor_1k.png');save(pad(nmap,covered),T/f'{prefix}_normal_1k.png');save(pad(mr(cl),covered),T/f'{prefix}_metal_rough_1k.png');Image.fromarray(cl).save(T/f'{prefix}_material_classes.png')
weight=ndimage.gaussian_filter(pad(cloth.astype(float),cov),.65)
R.write_mask([weight],T/'m540_region_mask.png',size=N);R.write_mask([np.zeros_like(weight)],T/'m540_head_region_mask.png',size=N)
cfg={'variants':list(pals),'materials':[{'base':name,'prefix':name.removesuffix('_A'),'mask':file,'regions':['cloth'],'ramps':ramps,'palettes':dict(zip(pals,[541,542,543]))} for name,file in [('OgreMage_A','m540_region_mask.png'),('OgreMageHead_A','m540_head_region_mask.png')]]}
(T/'m540_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
# The wand keeps its own small atlas and unchanged colours for every tier.
wr=np.load(p/'work/uvraster_Wand.npz');wcov=wr['piece']>=0;wp=wr['pos'];info=json.loads((p/'work/wand_region.json').read_text());wb=load(p/'meshy/wand_v1/texture_urls_0_base_color.png',512);wn=normal(p/'meshy/wand_v1/texture_urls_0_normal.png',512)
wh,ws,wv=hsv(wb);cl=np.zeros(wcov.shape,np.uint8);cl[wcov]=5;cl[wcov&(ws>.35)&(wh>10)&(wh<65)]=10;cl[wcov&(np.linalg.norm(wp-np.array(info['orb_centre']),axis=-1)<info['orb_radius'])]=11
for suffix,img in [('basecolor',wb),('normal',wn),('metal_rough',mr(cl))]:save(pad(img,wcov),T/f'm540_wand_{suffix}_512.png')
Image.fromarray(cl).save(T/'m540_wand_material_classes.png')
report={'skin_srgb':SKIN.tolist(),'native_palette_indices':order.tolist(),'head_neck_seam_mae_8bit':seam_mae,'material_class_counts':{k:{str(i):int((a==i).sum()) for i in np.unique(a)} for k,a in [('body',classes),('head',hc),('wand',cl)]},'normal_maps':normal_reports,'specular_channel':'MR.R; openyamm_specular_mask, metallic zero','wand_class_11':'enchanted glass orb; geometry sphere region'}
assert seam_mae<20,report
assert int(cloth.sum())>50000 and int((hc==6).sum())>10
(T/'composition_report.json').write_text(json.dumps(report,indent=2)+'\n');print('TEXTURE_COMPOSITION',json.dumps(report))
