"""One palette-452 atlas for all three size tiers; native fur and skin medians, explicit material classes."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_gob_claude/scripts'))
import compose_textures_v2 as C
src=P/'meshy/retexture_v1';out=P/'textures';data=np.load(P/'work/uv3d.npz')
part,xyz=C.rasterise(data,tol=0);valid=part>=0
# Preserve small teeth/whisker islands: pad from their original covered texels, without eroding them away.
_,(iy,ix)=ndimage.distance_transform_edt(~valid,return_indices=True)
def pad(a):return a[iy,ix]
base=C.load(src/'texture_urls_0_base_color.png');normal=C.load(src/'texture_urls_0_normal.png')
assert base.shape==(2048,2048,3) and normal.shape==base.shape
base=pad(base);h,s,v=C.hsv(base);x,y,z=xyz.transpose(2,0,1)
# Skin colour is constrained to anatomical regions so warm fur remains fur.
skin=(y>.172)|((z<.045)&(abs(x)>.025))|((y<-.484)&(z>.18))
ears=(y>-.34)&(y<-.285)&(z>.235)&(abs(x)>.02)
skin|=ears&(s>.19)&(base[...,0]>base[...,1]*1.22)
eye=np.zeros_like(valid)
for center in [(.006,-.414,.211),(-.016,-.412,.212)]:
    eye|=np.sum(((xyz-np.array(center)) / np.array([.0055,.010,.0075]))**2,axis=-1)<1
teeth=(part==2)|(part==3);whisker=part==4
mouth=(y<-.408)&(y>-.476)&(z<.179)&(z>.151)&~teeth&~whisker
claw=(z<.018)&(s<.30)&(v>.37)
classes=np.full(part.shape,2,np.uint8);classes[skin]=1;classes[mouth]=7;classes[claw]=4;classes[teeth]=5;classes[eye]=6;classes[whisker]=11
classes[~valid]=0
lum=base@np.array([.2126,.7152,.0722]);result=base.copy()
for label,color in [(2,np.array([44,37,36])*1.6/255),(1,np.array([160,108,78])*1.25/255)]:
    mask=valid&(classes==label);reference=float(np.median(lum[mask]))
    shade=np.clip(lum/max(reference,1e-4),.32,1.9)
    tint=np.clip(color[None,None,:]*shade[...,None],0,1)
    result[mask]=tint[mask]
result[teeth]=np.array([.80,.74,.56]);result[claw]=np.array([.58,.50,.37])
result[mouth]=np.maximum(result[mouth]*.22,np.array([.025,.012,.014]))
result[eye]=(.019,.012,.008);result[whisker]=(.12,.105,.09)
def save(a,name,size=None):
    im=Image.fromarray(np.clip(pad(a)*255+.5,0,255).astype(np.uint8))
    if size:im=im.resize(size,Image.Resampling.LANCZOS)
    im.save(out/name)
save(result,'rat_basecolor.png');save(normal,'rat_normal.png')
rough=C.load(src/'texture_urls_0_roughness.png','L');rough=pad(rough)
save(np.stack([np.ones_like(rough),rough,np.zeros_like(rough)],-1),'rat_metal_rough.png',(1024,1024))
Image.fromarray(pad(classes)).resize((1024,1024),Image.Resampling.NEAREST).save(out/'rat_material_classes.png')
report={'palette':452,'native_fur_median':[44,37,36],'native_skin_median':[160,108,78],
 'albedo_gain':{'fur':1.6,'skin':1.25},'classes':{str(k):int((valid&(classes==k)).sum()) for k in range(1,12)},
 'shared_across_descriptors':[40,41,42],'basecolor_size':[2048,2048],'normal_size':[2048,2048]}
(out/'composition.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
