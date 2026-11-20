"""Resolve supersampled bakes to the unchanged shared texture budget and compose native tiers."""
import io,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parents[1];out=p/'review/round4';src=out/'before/textures';dest=out/'rebaked'
for f in dest.glob('mnk1_*.png'):
 im=Image.open(f);size=2048 if '2k' in f.name else 1024
 # Independent channels preserve the red mask when its unused alpha channel is zero.
 channels=[ch.resize((size,size),Image.Resampling.LANCZOS) for ch in im.convert('RGBA').split()];pixels=np.array(Image.merge('RGBA',channels))
 if 'basecolor' in f.name:
  rgb=np.asarray(im.convert('RGB'),float)/255;rgb=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);rgb=np.stack([np.array(Image.fromarray(rgb[:,:,i].astype('float32')).resize((size,size),Image.Resampling.LANCZOS)) for i in range(3)],-1);rgb=np.where(rgb<=.0031308,rgb*12.92,1.055*np.clip(rgb,0,None)**(1/2.4)-.055);pixels[:,:,:3]=np.clip(rgb*255+.5,0,255).astype('uint8')
 if 'normal' in f.name:
  v=pixels[:,:,:3].astype(float)/127.5-1;v/=np.maximum(np.linalg.norm(v,axis=2,keepdims=True),1e-8);pixels[:,:,:3]=np.clip((v+1)*127.5,0,255).astype('uint8')
 if 'region_mask' in f.name:pixels[:,:,1:]=0
 Image.fromarray(pixels).save(f)
# Extract the normal texture actually used by the accepted runtime (its Meshy input was +Y-down).
sys.path.insert(0,str(p.parents[2]/'tools'));import build_actor_lods as G
d,b=G.read_glb(out/'before/export/mm6_mnk1.glb');im=d['images'][d['textures'][d['materials'][0]['normalTexture']['index']]['source']];v=d['bufferViews'][im['bufferView']];(out/'source_normal.png').write_bytes(b[v['byteOffset']:v['byteOffset']+v['byteLength']])
W=np.array([.2126,.7152,.0722]);lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4);srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.clip(c,0,None)**(1/2.4)-.055)
r=json.loads((src/'mnk1_ramps.json').read_text());entry=r['materials'][0]
for kind,folder in [('source',src),('reduced',dest)]:
 im=Image.open(folder/'mnk1_basecolor_2k.png').convert('RGB');base=lin(np.asarray(im,float)/255);mask=np.stack([np.asarray(ch.resize(im.size,Image.Resampling.BILINEAR),float)/255 for ch in Image.open(folder/'mnk1_region_mask.png').convert('RGBA').split()],-1);lum=base@W
 for tier in 'abc':
  colour=base.copy()
  for c,reg in enumerate(entry['ramps']['mnk1_'+tier]):
   lo,hi=reg['range'];colors=np.array(reg['colors']);t=np.clip((lum-lo)/(hi-lo),0,1)*(len(colors)-1);i=np.minimum(t.astype(int),len(colors)-2);f=(t-i)[...,None];ramp=colors[i]*(1-f)+colors[i+1]*f;colour=colour*(1-mask[...,c:c+1])+ramp*mask[...,c:c+1]
  Image.fromarray(np.clip(srgb(colour)*255+.5,0,255).astype('uint8')).save(out/f'{kind}_{tier}.png')
assert Image.open(dest/'mnk1_basecolor_2k.png').size==(2048,2048)
