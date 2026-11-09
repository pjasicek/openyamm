"""Grade one shared ash hide set and derive runtime region ramps for A/B/C."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'scripts'))
sys.path.insert(0,str(PROJECT.parent/'claude_shared'))
import raster as C
import region_variants as R
from tier_textures import apply
OUT=PROJECT/'textures'
SRC=PROJECT/'meshy/body_texture_v1'
assert json.loads((PROJECT/'work/texture_correspondence.json').read_text())['max_uv_error']<1e-4
data=np.load(PROJECT/'work/uv3d.npz')
part,xyz=C.rasterise(data,tol=0)
valid=part>=0
_,(iy,ix)=ndimage.distance_transform_edt(~valid,return_indices=True)
def pad(a): return a[iy,ix]
def save(a,name,size=None,nearest=False):
    im=Image.fromarray(np.clip(a*255+.5,0,255).astype(np.uint8))
    if size: im=im.resize((size,size),Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS)
    im.save(OUT/name,optimize=True)
base=C.load(SRC/'texture_urls_0_base_color.png')
normal=C.load(SRC/'texture_urls_0_normal.png')
ao=C.load(OUT/'hound_ao.png','L')
h,s,v=C.hsv(base)
x,y,z=xyz.transpose(2,0,1)
head=valid&(y<-1.0)
gum=valid&(part==1)&(np.abs(x)<.035)&(y> -1.12)
teeth=valid&(part==1)&~gum
claws=valid&(part==2)
eyes=valid&(part==3)
mouth=head&(z<.80)&(s>.20)
nose=head&(y<-1.18)&(z>.75)
horn=valid&(y<-.72)&(z>.96)
hide=valid&~(teeth|claws|mouth|nose|horn|eyes|gum)
assert hide.sum()>10000 and teeth.sum()>100,'Material regions missing'
shade=np.clip((base@R.LUMA)/np.median((base@R.LUMA)[hide]),.18,1.9)
# The shared neutral hide preserves detail under the user-selected tier colours.
grey=np.array([.46,.455,.45])
target=np.clip(shade[...,None]*grey,0,1)
w=ndimage.gaussian_filter(pad(hide.astype(float)),.6)
out=base*(1-w[...,None])+target*w[...,None]
# Pigment never emits; only separate throat/maw geometry will glow.
out[mouth]=np.stack([v[mouth]*.15,v[mouth]*.13,v[mouth]*.12],-1)
out[horn]=np.minimum(out[horn].mean(-1,keepdims=True)*.6,.3)
out[teeth|claws]=np.clip(v[teeth|claws,None],.40,.80)*np.array([1.,.97,.91])
out[gum]=np.array([.055,.045,.04])
out[eyes]=np.array([.025,.025,.025])
out[nose]=np.minimum(out[nose].mean(-1,keepdims=True),.12)
out*=np.clip(.8+.2*ao,.8,1)[...,None]
out=pad(out)
normal=pad(normal)
save(out,'hound_basecolor.png')
save(normal,'hound_normal.png',1024)
rough=np.full(valid.shape,.78)
rough[horn]=.53
rough[teeth|claws]=.37
rough[mouth]=.5
rough[nose]=.55
save(pad(np.stack([ao,rough,np.zeros_like(ao)],-1)),'hound_metal_rough.png',1024)
classes=np.full(valid.shape,1,np.uint8)
classes[teeth|claws]=2
classes[horn]=3
classes[mouth]=4
classes[nose]=5
classes[~valid]=0
Image.fromarray(classes).save(OUT/'hound_material_classes.png')
R.write_mask([w],OUT/'hound_region_mask.png',1024)
variants=['hound_a','hound_b','hound_c']
colours={'hound_a':grey,'hound_b':np.array([.68,.52,.16]),'hound_c':np.array([.62,.18,.14])}
targets={k:np.clip(out*(colour/grey),0,1) for k,colour in colours.items()}
ramps,fit=R.fit_ramps(out,targets,w)
config={'variants':variants,'materials':[{'base':'HoundHide','prefix':'HoundHide',
        'mask':'hound_region_mask.png','regions':['hide'],'ramps':{k:[ramps[k]] for k in variants}}],
        'provenance':'User colour revision 2026-10-26: A grey / B yellow ochre / C red; one shared set',
        'fit':fit}
(OUT/'hound_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
mask=np.stack([np.asarray(b.resize((2048,2048),Image.Resampling.BILINEAR))/255. for b in Image.open(OUT/'hound_region_mask.png').split()],-1)
for k in variants: save(apply(out,mask,[ramps[k]]),f'{k}_review.png')
report={'one_shared_runtime_set':True,'dimensions':[2048,2048],'regions':{
    'hide':int(hide.sum()),'teeth':int(teeth.sum()),'horn':int(horn.sum())},'fit':fit}
(PROJECT/'work/texture_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
sys.path.insert(0,str(PROJECT.parents[2]/'tools'))
from normal_map_convention import measure
npix=np.asarray(Image.open(OUT/'hound_normal.png')).copy()
before=measure(npix)
if before<-.15:
    npix[...,1]=255-npix[...,1]
    Image.fromarray(npix).save(OUT/'hound_normal.png')
print('Normal convention',before,'->',measure(npix))
