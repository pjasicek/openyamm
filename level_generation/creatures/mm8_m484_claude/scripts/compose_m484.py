"""Native mail palettes and restrained class-based materials on the retained body/head maps."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as RV
T=P/'textures';T.mkdir(exist_ok=True);N=1024

def save(a,p):Image.fromarray(np.uint8(np.clip(a*255+.5,0,255))).save(p)
def load(p,mode='RGB',size=(N,N)):return np.asarray(Image.open(p).convert(mode).resize(size,Image.Resampling.LANCZOS),float)/255
def hsv(a):return np.asarray(Image.fromarray(np.uint8(np.clip(a*255,0,255))).convert('HSV'),float)/255
def pad(a,m):
 _,ix=ndimage.distance_transform_edt(~m,return_indices=True);return a[tuple(ix)]
def srgb(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)

# One missing mane face uses its own unused atlas tile, sampled from the nearest returned fur surface.
pmap=np.load(P/'work/body_missing_face_lookup.npz');pix,lookup,tiles=pmap['pixels'],pmap['uv'],pmap['tiles'];out=P/'work/body_uv_patched';out.mkdir(exist_ok=True)
for label in ['base_color','normal','roughness','metallic']:
 a=np.asarray(Image.open(P/f'meshy/body_retexture_v2/texture_urls_0_{label}.png').convert('RGB'),float);assert a.shape[:2]==(2048,2048)
 coords=np.array([(1-lookup[:,1])*2048-.5,lookup[:,0]*2048-.5]);values=np.stack([ndimage.map_coordinates(a[...,i],coords,order=1,mode='nearest') for i in range(3)],-1)
 if label=='normal':values[:]=[128,128,255]
 for x,y,size in tiles:
  ids=(pix[:,0]>=x)&(pix[:,0]<x+size)&(pix[:,1]>=y)&(pix[:,1]<y+size);tile=np.zeros((size,size,3));cov=np.zeros((size,size),bool);px=pix[ids,0]-x;py=pix[ids,1]-y;tile[py,px]=values[ids];cov[py,px]=True;a[y:y+size,x:x+size]=pad(tile,cov)
 Image.fromarray(np.uint8(np.clip(a+.5,0,255))).save(out/f'texture_urls_0_{label}.png')

sets={}
for kind,folder,layer in [('body','body_uv_patched','UVMap'),('head','head_uv_repacked','HeadUV')]:
 r=np.load(P/f'work/uvraster_{layer}.npz');piece,pos=r['piece'],r['pos'];cov=piece>=0;base=load(P/f'work/{folder}/texture_urls_0_base_color.png');normal=load(P/f'work/{folder}/texture_urls_0_normal.png');rough=load(P/f'work/{folder}/texture_urls_0_roughness.png','L');h=hsv(base);cls=np.zeros((N,N),np.uint8);cls[cov]=2;cls[np.isin(piece,[0,1])]=1
 metal=np.isin(piece,[2,4,8,22,25,36,40]);cls[np.isin(piece,[3,7,9,10,11])]=8;cls[metal]=9;cls[np.isin(piece,[5,6])]=6
 if kind=='body':
  cls[(piece==1)&(pos[...,2]<.20)]=4
  bracer=(piece==0)&(abs(pos[...,0])>.42)&(pos[...,2]<1.13)&(h[...,1]<.3)&(h[...,2]>.2);cls[bracer]=9
  mail=((piece==100)|(np.isin(piece,[0,1])&(pos[...,2]>.89)&(pos[...,2]<1.0)&(abs(pos[...,0])<.34)&(h[...,0]>.08)&(h[...,0]<.18)))&(h[...,2]>.08);cls[piece==100]=8;cls[mail]=9
 else:
  horn=(piece==0)&(abs(pos[...,0])>.085)&(pos[...,2]>1.72);cls[horn]=4
  ring=piece==8;lum=RV.luminance(base);base[ring]=np.array([.76,.78,.80])*np.clip(lum[ring,None]/max(np.median(lum[ring]),1e-5),.65,1.2)
 sets[kind]={'base':base,'normal':normal,'rough':rough,'classes':cls,'coverage':cov,'piece':piece,'pos':pos,'hsv':h,'mail':mail if kind=='body' else np.zeros_like(cov)}
# Match only the reddish hide across the actual shared head/neck seam.
seams=json.loads((P/'work/head_seam_uv.json').read_text());samples={k:[] for k in sets}
for row in seams:
 for kind in sets:
  u,v=row[kind];samples[kind].append(sets[kind]['base'][int(np.clip((1-v)*N,0,N-1)),int(np.clip(u*N,0,N-1))])
a,b=np.array(samples['body']),np.array(samples['head']);valid=(a[:,0]>a[:,2]*1.2)&(b[:,0]>b[:,2]*1.2)&(a.mean(1)>.08)&(b.mean(1)>.08);assert valid.sum()>2
ratio=np.median(RV.srgb_to_linear(a[valid]),axis=0)/np.maximum(np.median(RV.srgb_to_linear(b[valid]),axis=0),1e-5);gain=np.clip(ratio,.7,1.4);h=sets['head'];warm=np.isin(h['classes'],[1,2])&(h['hsv'][...,1]>.15);h['base'][warm]=srgb(RV.srgb_to_linear(h['base'][warm])*gain)
(P/'review/head_seam.json').write_text(json.dumps({'samples':int(valid.sum()),'measured_rgb_gain':ratio.tolist(),'applied_rgb_gain':gain.tolist()},indent=2))
lookup={1:(.25,.8),2:(0,.9),4:(1,.45),6:(1,.15),8:(.3,.75),9:(1,.38),10:(.3,.7)}
for kind,v in sets.items():
 cls,cov=v['classes'],v['coverage'];ao=load(P/f'work/ao_{"UVMap" if kind=="body" else "HeadUV"}.png','L');spec=np.zeros((N,N));rr=np.full((N,N),.8)
 for c,(s,r) in lookup.items():spec[cls==c]=s;rr[cls==c]=r
 rr=np.clip(rr+.20*(v['rough']-ndimage.gaussian_filter(v['rough'],4)),.1,1);base=srgb(RV.srgb_to_linear(v['base'])*(.85+.15*ao[...,None]));v['base']=base;prefix='m484' if kind=='body' else 'm484_head'
 for label,im in [('basecolor',base),('normal',v['normal']),('metal_rough',np.stack([spec*ao,rr,np.zeros_like(rr)],-1))]:save(pad(im,cov),T/f'{prefix}_{label}_1k.png')
 Image.fromarray(cls).save(T/f'{prefix}_material_classes.png')

PALS={'m484_a':485,'m484_b':486,'m484_c':487};native={k:[] for k in PALS}
for v in range(5):
 idx=np.asarray(Image.open(P.parents[2]/f'assets_dev/engine/sprites/m484Sa{v}.bmp'));mask=(idx>=43)&(idx<=80)
 for k,n in PALS.items():
  pal=np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm8/textures/Pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255;native[k].append(pal[idx[mask]])
base=sets['body']['base'];cov=sets['body']['coverage'];mail=sets['body']['mail'];assert mail.sum()>1000
lum=RV.luminance(base[mail]);lo,hi=np.percentile(lum,[2,98]);assert hi>lo;ramps={}
for k in PALS:
 a=np.concatenate(native[k]);a=a[RV.luminance(a)>.008];a=a[np.argsort(RV.luminance(a))];cols=[]
 for t in np.linspace(lo,hi,16):
  q=np.searchsorted(np.sort(lum),t)/len(lum);cols.append(RV.srgb_to_linear(np.clip(a[min(len(a)-1,int(q*(len(a)-1)))]*1.3,0,1)).tolist())
 ramps[k]=[{'range':[float(lo),float(hi)],'colors':cols}]
RV.write_mask([ndimage.gaussian_filter(pad(mail.astype(float),cov),.5)],T/'m484_region_mask.png',size=N)
Image.new('RGBA',(N,N),(0,0,0,0)).save(T/'m484_head_empty_mask.png')
config={'variants':list(PALS),'materials':[{'base':'M484_A','prefix':'M484','mask':'m484_region_mask.png','regions':['mail'],'palettes':PALS,'ramps':ramps},{'base':'M484Head_A','prefix':'M484Head','mask':'m484_head_empty_mask.png','regions':['mail'],'ramps':ramps}]}
# The axe's two broad faces intentionally share the same symmetric ornament.
im=np.asarray(Image.open(P/'references_hd/axe_reference.png').convert('RGBA'),float)/255;rgb=pad(im[...,:3],im[...,3]>.9);rgb=np.asarray(Image.fromarray(np.uint8(np.clip(rgb*255,0,255))).resize((512,1024),Image.Resampling.LANCZOS),float)/255;h=hsv(rgb);y,x=np.mgrid[:1024,:512];shaft=(abs(x/512-.5)<.04)&(y/1024>.27)&(y/1024<.92);cls=np.full((1024,512),9,np.uint8);cls[shaft]=10;cls[shaft&(h[...,2]<.23)]=8
for y0 in [426,548,768,972,1325,1390]:cls[shaft&(abs(y/1024-y0/1536)<.009)]=9
spec=np.where(cls==9,1,.3);rr=np.where(cls==9,.38,np.where(cls==8,.75,.7));flat=np.stack([np.full_like(rr,.5),np.full_like(rr,.5),np.ones_like(rr)],-1)
for label,a in [('basecolor',rgb),('normal',flat),('metal_rough',np.stack([spec,rr,np.zeros_like(rr)],-1))]:save(a,T/f'm484_axe_{label}.png')
Image.fromarray(cls).save(T/'m484_axe_material_classes.png');Image.new('RGBA',(512,1024),(0,0,0,0)).save(T/'axe_empty_mask.png');config['materials'].append({'base':'Axe_A','prefix':'Axe','mask':'axe_empty_mask.png','regions':[],'ramps':{k:[] for k in PALS}});(T/'m484_ramps.json').write_text(json.dumps(config,indent=1)+'\n')
sys.path.insert(0,str(P.parents[2]/'tools'));import normal_map_convention as C
report={}
for p in T.glob('*normal*.png'):
 a=np.array(Image.open(p).convert('RGB'));c=C.measure(a);report[p.name]={'correlation':c,'flipped':c<=-.15}
 if c<=-.15:a[...,1]=255-a[...,1];Image.fromarray(a).save(p)
(P/'review/normal_convention.json').write_text(json.dumps(report,indent=2));print('COMPOSE',{'mail_pixels':int(mail.sum()),'head_gain':gain.tolist(),'normals':report})
