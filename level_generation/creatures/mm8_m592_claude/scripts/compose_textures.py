"""Shared Guardian maps, anatomical material classes and independently measured native mane ramps."""
from pathlib import Path
import sys,json,hashlib,numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(ROOT/'tools'));import normal_map_convention as NC
T=P/'textures';T.mkdir(exist_ok=True);N=1024;normal_reports={}
def load(path):return np.asarray(Image.open(path).convert('RGB').resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def pad(a,cov):
 _,(y,x)=ndimage.distance_transform_edt(~cov,return_indices=True);return a[y,x]
def hsv(a):
 v=np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255;return v[...,0]*360,v[...,1],v[...,2]
def normal(path):
 raw=np.asarray(Image.open(path).convert('RGB')).copy();corr=NC.measure(raw);flip=corr<=-.15
 if flip:raw[...,1]=255-raw[...,1]
 normal_reports[str(path.relative_to(P))]={'correlation':float(corr),'green_flipped':bool(flip)};v=np.asarray(Image.fromarray(raw).resize((N,N),Image.Resampling.LANCZOS),float)/127.5-1;v/=np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-8);return v
sets={}
for kind,layer in [('body','UVMap'),('head','HeadUV')]:
 r=np.load(P/f'work/uvraster_{layer}.npz');pos=r['pos'];piece=r['piece'];covered=piece>=0;base=load(P/f'meshy/{kind}_retexture_v1/texture_urls_0_base_color.png');h,s,v=hsv(base);cl=np.zeros((N,N),np.uint8);cl[covered]=1
 domain=(pos[...,2]>.90)&((pos[...,1]>-.28)|(pos[...,2]>1.38)) if kind=='body' else ((pos[...,2]>1.38)|(pos[...,1]>-.40)|(pos[...,2]<1.105))
 warm=(h>8)&(h<75)&(s>.28);hair=covered&((domain&warm)|(piece>2));cl[hair]=2
 eye=covered&np.isin(piece,[1,2]);cl[eye]=6
 if kind=='body':
  bn=r['bone_names'];bindex=r['bone'];claw=covered&np.isin(bindex,[i for i,n in enumerate(bn) if 'Finger' in n]);cl[claw]=4
  toe=covered&(abs(pos[...,0])<.42)&(pos[...,2]<.085)&(pos[...,1]<.26)&(v>.43);cl[toe]=4
 else:
  mouthbox=covered&(piece==0)&(abs(pos[...,0])<.16)&(pos[...,1]<-.43)&(pos[...,2]>1.065)&(pos[...,2]<1.31)
  hair[mouthbox]=False;cl[mouthbox]=1
  tooth=mouthbox&(h>10)&(h<75)&(s<.80)&(v>.45);cl[tooth]=5
  mouth=mouthbox&((h<18)|(h>335)|(v<.23));cl[mouth&~tooth]=7
 n=normal(P/f'meshy/{kind}_retexture_v1/texture_urls_0_normal.png')
 if kind=='body':
  geo=load(P/'work/geometry_normal_UVMap.png')*2-1;bad=(geo[...,2]<.1)|(np.linalg.norm(geo,axis=-1)<.5);geo[bad]=[0,0,1];geo/=np.maximum(np.linalg.norm(geo,axis=-1,keepdims=True),1e-8);t=geo+np.array([0,0,1]);u=n*np.array([-1,-1,1]);n=t*((t*u).sum(-1)/np.maximum(t[...,2],1e-6))[...,None]-u;n/=np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-8);normal_reports['geometry_bake_bad_covered_fraction']=float((bad&covered).sum()/covered.sum())
 ao=load(P/f'work/ao_{layer}.png')[...,0];base[covered]*=(.85+.15*np.clip(ao[covered],.3,1))[:,None];weight=hair.astype(float)
 # Teeth, mouth and eyes never enter the mane recolour, including feathered mask borders.
 weight[np.isin(cl,[4,5,6,7])]=0;weight=ndimage.gaussian_filter(pad(weight,covered),.65);weight[covered&np.isin(cl,[4,5,6,7])]=0
 if kind=='head':weight[mouthbox]=0
 sets[kind]={'base':base,'normal':n*.5+.5,'class':cl,'coverage':covered,'mask':weight,'pos':pos}
# Match skin brightness at the shared neck boundary; preserve pigment and separate material classes.
seams=json.loads((P/'work/seam_samples.json').read_text())
def sample(img,uv):
 xy=np.clip(np.floor(np.array(uv)*N).astype(int),0,N-1);return img[N-1-xy[:,1],xy[:,0]]
b=sets['body'];hset=sets['head'];bc=sample(pad(b['base'],b['coverage']),[r['body'] for r in seams]);hc=sample(pad(hset['base'],hset['coverage']),[r['head'] for r in seams]);bcl=sample(b['class'],[r['body'] for r in seams]);hcl=sample(hset['class'],[r['head'] for r in seams]);skin=(bcl==1)&(hcl==1);gain=float(np.clip(np.median(R.luminance(bc[skin])/np.maximum(R.luminance(hc[skin]),.02)),.65,1.5)) if skin.sum()>8 else 1
lin=R.srgb_to_linear(hset['base']);m=hset['class']==1;lin[m]*=gain;hset['base'][m]=np.where(lin[m]<=.0031308,lin[m]*12.92,1.055*np.maximum(lin[m],0)**(1/2.4)-.055)
response={0:(0,1,0),1:(0,.84,0),2:(0,.94,0),3:(0,.85,0),4:(.35,.48,0),5:(.4,.42,0),6:(1,.16,0),7:(.15,.65,0)}
for kind,row in sets.items():
 prefix='m592'+('_head' if kind=='head' else '');cl=row['class'];covered=row['coverage'];mr=np.zeros((N,N,3))
 for c,value in response.items():mr[cl==c]=value
 for name,img in [('basecolor',row['base']),('normal',row['normal']),('metal_rough',mr)]:save(pad(img,covered),T/f'{prefix}_{name}_1k.png')
 Image.fromarray(cl).save(T/f'{prefix}_material_classes.png');R.write_mask([row['mask']],T/f'{prefix}_region_mask.png',size=N)
pals={f'm592_{c}':np.frombuffer((ROOT/f'assets_dev/worlds/mm8/textures/pal{pid}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for c,pid in zip('abc',[593,594,595])};a,bp,cp=pals.values();ah,ass,av=hsv(a[None,:,:]);changed=np.max(abs(a-cp),axis=1)>.01;ids=np.flatnonzero(changed&(ah[0]>14)&(ah[0]<75)&(ass[0]>.28)&(bp[:,1]>bp[:,0]*1.25)&(bp[:,1]>bp[:,2]*1.10)&(cp[:,0]>cp[:,1]*1.4));assert len(ids)>30,ids
lum=np.concatenate([R.luminance(r['base'])[r['mask']>.9] for r in sets.values()]);lo,hi=np.percentile(lum,[2,98]);assert hi-lo>.02;ramps={}
for tier,pal in pals.items():
 colors=pal[ids];colors=colors[np.argsort(R.luminance(colors))];stops=np.stack([np.interp(np.linspace(0,len(colors)-1,16),np.arange(len(colors)),colors[:,i]) for i in range(3)],axis=1);ramps[tier]=[{'range':[float(lo),float(hi)],'colors':R.srgb_to_linear(np.clip(stops*1.35,0,1)).round(6).tolist()}]
cfg={'variants':list(pals),'materials':[{'base':name,'prefix':name.removesuffix('_A'),'mask':file,'regions':['mane'],'ramps':ramps,'palettes':dict(zip(pals,[593,594,595]))} for name,file in [('PlaneGuardian_A','m592_region_mask.png'),('PlaneGuardianHead_A','m592_head_region_mask.png')]]};(T/'m592_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
report={'native_palette_indices':ids.tolist(),'ramps':'Each native palette independently luminance-sorted; albedo boost 1.35','head_skin_linear_luminance_gain':gain,'seam_skin_samples':int(skin.sum()),'normal_maps':normal_reports,'material_class_counts':{k:{str(i):int((r['class']==i).sum()) for i in np.unique(r['class'])} for k,r in sets.items()},'specular':'MR.R mask; G roughness, B zero metallic','geometry_normal':'Retained 16.5k smooth geometry baked onto the reduced body; RNM combined with Meshy painted detail'};assert min(int((r['class']==2).sum()) for r in sets.values())>1000;assert int((sets['head']['class']==6).sum())>10;(T/'composition_report.json').write_text(json.dumps(report,indent=2)+'\n');print('TEXTURE_COMPOSITION',json.dumps(report),flush=True)
