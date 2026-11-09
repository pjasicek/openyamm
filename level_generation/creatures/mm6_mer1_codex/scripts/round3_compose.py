"""Compose shared 1K maps and native palette ramps; assert native skin luminance survives grading."""
import sys,json,numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
T=P/'textures/round3';T.mkdir(exist_ok=True);N=1024
NAT=P.parent/'mm6_mer1/native_variants';pals={'mer1_a':252,'mer1_b':253,'mer1_c':770}
def load(p,mode='RGB'):
 return np.asarray(Image.open(p).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,p):Image.fromarray(np.uint8(np.clip(a*255+.5,0,255))).save(p)
def hsv(a):return np.asarray(Image.fromarray(np.uint8(np.clip(a*255,0,255))).convert('HSV'),float)/255
def enc(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
def stats(a):return {'mean':float(a.mean()),'p90':float(np.percentile(a,90)),'p95':float(np.percentile(a,95))}
na=np.asarray(Image.open(NAT/'mer1sta0_252.png').convert('RGB'),float)/255
h=hsv(na);yy,xx=np.indices(na.shape[:2]);face=(xx>=81)&(xx<=107)&(yy>=14)&(yy<=38)&(h[...,0]>.02)&(h[...,0]<.13)&(h[...,1]>.16)&(h[...,1]<.65)&(h[...,2]>.35)
assert face.sum()>100
native=na[face];native_lum=np.sort(R.luminance(native));report={'native_face_pixels':int(face.sum()),'native_skin_linear_luminance':stats(native_lum),'native_box':[81,14,107,38]}
hands=(((xx>=35)&(xx<=46)&(yy>=124)&(yy<=145))|((xx>=145)&(xx<=155)&(yy>=124)&(yy<=145)))&(h[...,0]>.02)&(h[...,0]<.13)&(h[...,1]>.15)&(h[...,1]<.65)&(h[...,2]>.4)
hands_lum=np.sort(R.luminance(na[hands]));report['native_hand_pixels']=int(hands.sum());report['native_hands_linear_luminance']=stats(hands_lum)
cols={k:[]for k in pals}
for view in range(5):
 ims={k:np.asarray(Image.open(NAT/f'mer1sta{view}_{pal}.png').convert('RGBA'),float)/255 for k,pal in pals.items()}
 a=ims['mer1_a'];diff=np.maximum(abs(ims['mer1_b'][...,:3]-a[...,:3]).max(-1),abs(ims['mer1_c'][...,:3]-a[...,:3]).max(-1));mask=(diff>8/255)&(a[...,3]>.5)&(a[...,:3].max(-1)>.06)
 for k in pals:cols[k].append(ims[k][...,:3][mask])
cols={k:np.concatenate(v)for k,v in cols.items()};order=np.argsort(R.luminance(cols['mer1_a']));ramps={k:[]for k in pals}

for prefix,job,N in [('head','head_round3_texture_v2',1024),('hands','hands_round3_texture',512)]:
 src=P/'meshy'/job;base=load(src/'texture_urls_0_base_color.png');normal=load(src/'texture_urls_0_normal.png');normal[...,1]=1-normal[...,1];normal[...,:2]=.5+(normal[...,:2]-.5)*.35;rough=load(src/'texture_urls_0_roughness.png','L');r=np.load(P/'work/round3'/f'uvraster_{prefix}.npz');piece=r['piece'];cov=piece>=0;h=hsv(base)
 skin=cov if prefix=='hands'else cov&(piece==0)&(h[...,0]>.02)&(h[...,0]<.13)&(h[...,1]>.1)&(h[...,1]<.7)&(h[...,2]>.25)
 old=R.luminance(base)[skin];targetNative=hands_lum if prefix=='hands'else native_lum;affected=cov if prefix=='hands'else cov&(piece==0);lin=R.srgb_to_linear(base[affected]);lin*=1.92 if prefix=='hands'else 1.3;lum=lin@np.array([.2126,.7152,.0722]);lin=lin*.82+lum[:,None]*.18;base[affected]=enc(np.clip(lin,0,1))

 # Preserve generated skin creases and nail detail; no flat hand fill.
 spec=np.where(skin,.3,.08);rgh=np.where(skin,.72,.9);mr=np.stack([spec,rgh,np.zeros_like(spec)],-1);ix=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
 for arr,name in [(base,'basecolor'),(normal,'normal'),(mr,'metal_rough')]:save(arr[tuple(ix)],T/f'{prefix}_{name}.png')
 Image.fromarray(np.uint8(cov)*255).save(T/f'{prefix}_uv_coverage.png');Image.fromarray(np.uint8(skin)*255).save(T/f'{prefix}_skin_mask.png');report[prefix]={'pixels':int(skin.sum()),'native':stats(targetNative),'graded':stats(R.luminance(base)[skin]),'resolution':N,'source':job,'padding':'nearest covered texel dilation over all atlas background; hand islands 33+px gap'}
(T/'skin_report.json').write_text(json.dumps(report,indent=2))
