"""One shared 1K body/head set with native palette-524 ramps and nonmetal reptile materials."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure

def load(p,mode='RGB'):return np.asarray(Image.open(p).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255

def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p,optimize=True)

def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]

images={label:load(P/'meshy'/f'{label}_retexture_v1/texture_urls_0_base_color.png') for label in ['body','head']};data={label:np.load(P/'work'/f'uvraster_{label}.npz') for label in images}
hd=data['head'];pos=hd['pos'];uv=hd['body_uv'];sample=ndimage.map_coordinates(images['body'],[np.broadcast_to(((1-uv[...,1])*N-.5)[...,None],(N,N,3)),np.broadcast_to((uv[...,0]*N-.5)[...,None],(N,N,3)),np.broadcast_to(np.arange(3),(N,N,3))],order=1,mode='nearest')
# The full-body paint supplies a continuous neck seam; the separate head paint takes over above it.
f=np.clip((pos[...,2]-1.56)/.13,0,1);f=f*f*(3-2*f);f=np.where((hd['piece']==0)&(pos[...,1]>.12),f,1);images['head']=sample*(1-f[...,None])+images['head']*f[...,None]
regions={};classes={};reports={}
for label,img in images.items():
 d=data[label];covered=d['piece']>=0;pos=d['pos'];mx=img.max(-1);mn=img.min(-1);sat=(mx-mn)/np.maximum(mx,1e-6);h=np.asarray(Image.fromarray(np.uint8(img*255)).convert('HSV'),float)[...,0]/255
 tooth=covered&(d['piece']>0) if label=='head' else covered&(abs(pos[...,0])>.65)&(pos[...,2]<.78)&(sat<.27)&(mx>.45)
 mouth=covered&(h<.075)&(sat>.48)&(img[...,0]>img[...,1]*1.65) if label=='head' else np.zeros((N,N),bool)
 eyes=covered&(h>.08)&(h<.18)&(sat>.6)&(mx>.32)&(pos[...,2]>1.78)&(abs(pos[...,0])>.1) if label=='head' else np.zeros((N,N),bool)
 pale=covered&(sat<.30)&(mx>.35)&~tooth&~mouth&~eyes
 brown=covered&~pale&~tooth&~mouth&~eyes
 regions[label]=[brown,pale];cl=np.zeros((N,N),np.uint8);cl[covered]=1;cl[tooth]=5 if label=='head' else 4;cl[eyes]=6;cl[mouth]=7;classes[label]=cl
 ao=ndimage.gaussian_filter(pad(load(T/f'm524_{label}_ao.png','L'),covered),2);img=img*(1-.35*(1-ao))[...,None];images[label]=img
 prefix=P/'meshy'/f'{label}_retexture_v1/texture_urls_0';rough=load(str(prefix)+'_roughness.png','L');normal=load(str(prefix)+'_normal.png');correlation=measure(np.uint8(normal*255+.5));assert correlation<-.15,correlation;normal[...,1]=1-normal[...,1]
 rg=np.clip(.58+.2*(rough-.5),.42,.76);rg[pale]=.66;rg[tooth]=.36;rg[eyes]=.25;rg[mouth]=.48
 save(pad(img,covered),T/f'm524_{label}_basecolor_1k.png');save(pad(normal,covered),T/f'm524_{label}_normal_1k.png');save(np.stack([pad(ao,covered),pad(rg,covered),np.zeros((N,N))],-1),T/f'm524_{label}_metal_rough_1k.png');R.write_mask([ndimage.gaussian_filter(pad(m.astype(float),covered),.6) for m in regions[label]],T/f'm524_{label}_region_mask.png',size=N);Image.fromarray(cl).save(T/f'm524_{label}_material_classes.png');reports[label]={'brown_texels':int(brown.sum()),'pale_texels':int(pale.sum()),'normal_correlation_before_conversion':float(correlation),'ao_min':float(ao[covered].min()),'material_classes':np.unique(cl).tolist()}
 overlay=img*.25;overlay[brown]=[.1,.8,.2];overlay[pale]=[.2,.4,1];overlay[tooth]=[1,.9,.1];overlay[eyes]=[1,.2,.1];save(overlay,P/'review'/f'regions_{label}.png')
pal=np.frombuffer((P.parents[2]/'assets_dev/worlds/mm8/textures/pal524.act').read_bytes()[:768],np.uint8).reshape(256,3)/255
native=np.concatenate([pal[np.array(Image.open(P.parents[2]/f'assets_dev/engine/sprites/m524Sa{v}.bmp')).ravel()] for v in range(5)]);r,g,b=native.T;mx=native.max(1);sat=(mx-native.min(1))/np.maximum(mx,1e-6)
select=[(r>g*1.12)&(g>b*1.1)&(mx>.16)&(mx<.7),(sat<.25)&(mx>.25)&(r>=b)&(r<g*1.3)]
ramps=[]
for channel in range(2):
 colors=native[select[channel]];assert len(colors)>100
 target=R.srgb_to_linear(np.clip(np.median(colors,axis=0)*1.45,0,1));lum=np.concatenate([R.luminance(images[label][regions[label][channel]]) for label in images]);lo,hi=np.percentile(lum,[1,99]);median=float(np.median(lum));ramp={'range':[float(lo),float(hi)],'colors':[np.clip(target*((lo+i/15*(hi-lo))/median),0,1).tolist() for i in range(16)]};ramps.append(ramp);reports[['brown','pale'][channel]]={'native_samples':len(colors),'native_median_srgb':np.median(colors,axis=0).tolist(),'target_srgb':np.clip(np.median(colors,axis=0)*1.45,0,1).tolist(),'range':[float(lo),float(hi)]}
variants=['serpentman_a','serpentman_b','serpentman_c'];cfg={'variants':variants,'palettes':{v:524 for v in variants},'report':reports,'materials':[{'base':name+'_A','prefix':name,'mask':f'm524_{label}_region_mask.png','regions':['brown','pale'],'ramps':{v:ramps for v in variants}} for label,name in [('body','Serpentman'),('head','SerpentmanHead')]]};(T/'m524_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');print(json.dumps(reports))
