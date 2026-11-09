"""One shared wolf skin, native palette-512 ramps and material classes for all three size tiers."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

PROJECT=Path(__file__).resolve().parents[1];OUT=PROJECT/'textures';SRC=PROJECT/'meshy/retexture_v1'
sys.path.insert(0,str(PROJECT.parent/'mm6_gob_claude/scripts'))
import compose_textures_v2 as C
sys.path.insert(0,str(PROJECT.parent/'claude_shared'))
import region_variants as R
from tier_textures import apply
assert json.loads((PROJECT/'work/texture_correspondence.json').read_text())['max_uv_error']<1e-4
data=np.load(PROJECT/'work/uv3d.npz');part,xyz=C.rasterise(data,tol=0)
valid=part>=0
_,(iy,ix)=ndimage.distance_transform_edt(~valid,return_indices=True)
def pad(a):return a[iy,ix]
def save(a,name,size=None,nearest=False):
    image=Image.fromarray(np.clip(a*255+.5,0,255).astype(np.uint8))
    if size:image=image.resize((size,size),Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS)
    image.save(OUT/name,optimize=True)
base=C.load(SRC/'texture_urls_0_base_color.png');normal=C.load(SRC/'texture_urls_0_normal.png')
ao=C.load(OUT/'wolf_ao_2k.png','L');h,s,v=C.hsv(base);x,y,z=xyz.transpose(2,0,1)
head=valid&(y<-.33)
eyes=head&(h>55)&(h<155)&(s>.35)&(v>.25)&(z>.24)
mouth=head&(y<-.425)&(z<.265)&(h<40)&(s>.32)
teeth=head&(y<-.435)&(z<.275)&(v>.58)&(s<.32)
claws=valid&(z<.035)&(v>.5)&(s<.3)
nose=head&(y<-.49)&(z>.24)&(z<.31)&(v<.3)
fur=valid&~(eyes|mouth|teeth|claws|nose)
assert eyes.sum()>30 and fur.sum()>10000,'Material classification did not find wolf eyes and fur'
native=[]
for view in range(5):
    image=np.asarray(Image.open(PROJECT/f'native/m512sa{view}.png'))
    native.append(image[...,:3][image[...,3]>0]/255.)
native=np.concatenate(native);nh,ns,nv=C.hsv(native)
native_fur=native[(ns<.38)&(nv>.10)&(nv<.8)]
native_eye=native[(nh>55)&(nh<155)&(ns>.45)&(nv>.25)]
assert len(native_eye)>5 and len(native_fur)>1000
fur_target=np.median(native_fur,axis=0)*1.45
eye_target=np.median(native_eye,axis=0)*1.2
shade=(base@R.LUMA)/np.median((base@R.LUMA)[fur])
target=np.clip(shade[...,None]*fur_target,0,1)
weight=ndimage.gaussian_filter(pad(fur.astype(float)),.7)
out=base*(1-weight[...,None])+target*weight[...,None]
eye_weight=ndimage.gaussian_filter(pad(eyes.astype(float)),.5)
eye_shade=np.clip(v/max(float(np.median(v[eyes])),.01),.4,1.5)
out=out*(1-eye_weight[...,None])+np.clip(eye_target*eye_shade[...,None],0,1)*eye_weight[...,None]
out*=np.clip(.72+.28*ao,.72,1)[...,None]
out=pad(out);normal=pad(normal)
save(out,'wolf_basecolor.png');save(normal,'wolf_normal_1k.png',1024)
classes=np.full(valid.shape,2,np.uint8);classes[nose]=1;classes[claws]=4;classes[teeth]=5
classes[eyes]=6;classes[mouth]=7;classes[~valid]=0
Image.fromarray(classes).resize((1024,1024),Image.Resampling.NEAREST).save(OUT/'wolf_material_classes.png')
rough=np.full(valid.shape,.84);rough[eyes]=.18;rough[teeth]=.35;rough[claws]=.45;rough[mouth]=.62;rough[nose]=.55
# Keep baked AO in R for the shared material workflow; skin specular is disabled at runtime.
save(pad(np.stack([ao,rough,np.zeros_like(ao)],-1)),'wolf_metal_rough_1k.png',1024)
weights=[weight,eye_weight];R.write_mask(weights,OUT/'wolf_region_mask.png',1024)
variants=['wolf_a','wolf_b','wolf_c'];ramps={k:[] for k in variants};fit={}
for name,w in zip(['fur','eyes'],weights):
    fitted,report=R.fit_ramps(out,{k:out for k in variants},w)
    fit[name]=report
    for k in variants:ramps[k].append(fitted[k])
config={'variants':variants,'materials':[{'base':'Wolf','prefix':'Wolf','mask':'wolf_region_mask.png',
         'regions':['fur','eyes'],'ramps':ramps}],
        'provenance':{'palettes':{'wolf_a':512,'wolf_b':512,'wolf_c':512},
          'native_fur_median':np.median(native_fur,axis=0).tolist(),'albedo_gain':1.45,
          'native_eye_median':np.median(native_eye,axis=0).tolist(),'tier_difference':'Native size only'},'fit':fit}
(OUT/'wolf_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
mask=np.asarray(Image.open(OUT/'wolf_region_mask.png').resize((2048,2048),Image.Resampling.BILINEAR))/255.
preview=apply(out,mask,ramps['wolf_a']);save(preview,'wolf_preview_a.png')
report={'classes':{str(i):int((classes==i).sum()) for i in np.unique(classes)},'fit':fit,
        'fur_target_srgb':fur_target.tolist(),'eye_target_srgb':eye_target.tolist(),
        'texture_dimensions':[2048,1024],'one_shared_set':True}
(PROJECT/'work/texture_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

sys.path.insert(0,str(PROJECT.parents[2]/'tools'))
from normal_map_convention import measure
normal_path=OUT/'wolf_normal_1k.png';pixels=np.array(Image.open(normal_path).convert('RGB'))
correlation=measure(pixels)
if correlation<-.15:
    pixels[...,1]=255-pixels[...,1];Image.fromarray(pixels).save(normal_path,optimize=True)
print('Normal convention',correlation,'->',measure(pixels))
