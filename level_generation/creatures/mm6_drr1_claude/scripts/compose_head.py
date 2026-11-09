"""One padded skin, class-based specular, and measured native green/blue/red region ramps."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=P.parent/'mm6_drr1'
sys.path.insert(0,str(P.parent/'mm6_gob_claude/scripts'))
sys.path.insert(0,str(P.parent/'claude_shared'))
import compose_textures_v2 as C
import region_variants as R
D=np.load(P/'work/head_uv3d.npz');part,xyz=C.rasterise(D,tol=0)
valid=part>=0;inside=ndimage.binary_erosion(valid,iterations=1)
_,ix=ndimage.distance_transform_edt(~inside,return_indices=True)
def pad(a):
    return a[tuple(ix)]
def save(a,name,size=None,nearest=False):
    im=Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5))
    if size:im=im.resize((size,size),Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS)
    im.save(T/name)
src=P/'meshy/head_texture_v1'
base=pad(C.load(src/'texture_urls_0_base_color.png'))

# Coordinate masks correct the service's green patches on horn roots and missing slit pupils.
x,y,z=xyz[...,0],xyz[...,1],xyz[...,2]
horns=np.zeros(valid.shape,bool)
axis=np.array([[.010,-.452,.339],[.016,-.434,.355],[.019,-.422,.370],[.024,-.405,.386],[.025,-.392,.408],[.021,-.379,.433]])
for sign in [1,-1]:
 curve=axis.copy()
 if sign<0:curve[:,0]=-curve[:,0]-.009
 for i,(a,b) in enumerate(zip(curve,curve[1:])):
  d=b-a;t=np.clip(((xyz-a)*d).sum(-1)/(d@d),0,1)
  radius=[.012,.010,.008,.007,.006][i]
  horns|=valid&(np.linalg.norm(xyz-(a+t[...,None]*d),axis=-1)<radius)

crest=valid&(z>.354)&(np.abs(x+.0045)<.010)&(y>-.464)&(y<-.35)
cheek=valid&np.isin(part,[8,9])
noise=.5+.5*np.sin(x*1743+y*1117+np.sin(z*1931))*np.sin(z*2311-y*1307)
base[horns]=np.stack([.77+.13*noise,.82+.12*noise,.86+.11*noise],-1)[horns]
luminance=base@np.array([.2126,.7152,.0722])
base[crest|cheek]=((.60+.35*luminance[...,None])*np.array([.82,.68,.32]))[crest|cheek]
for eye_part in [5,6]:
 eye_mask=valid&(part==eye_part)
 pupil=np.clip((1-((y+.4714)/.0010)**2-((z-.3341)/.0045)**2)*4,0,1)*eye_mask
 base=base*(1-pupil[...,None])+np.array([.014,.021,.009])*pupil[...,None]

h,s,v=C.hsv(base)
eye=valid&np.isin(part,[5,6]);mouth=valid&(part==2);tooth=valid&np.isin(part,[1,3,4])
neutral=valid&(((s<.25)&(v>.42))|((h>170)&(h<290)))&~eye&~mouth
gold=valid&(h>20)&(h<80)&(s>.25)&~eye&~mouth&~tooth&~neutral
hide=valid&~(eye|mouth|tooth|neutral|gold)
classes=np.zeros(valid.shape,np.uint8);classes[valid]=1;classes[gold]=4;classes[neutral]=4
classes[tooth]=5;classes[mouth]=7;classes[eye]=6
save(pad(classes)/255,'wyrm_head_material_classes.png',1024,True)
save(base,'wyrm_head_basecolor.png')
ao=C.load(T/'wyrm_head_ao_2k.png','L');ao=pad(ao)
# Keep scale detail without the generated hard shine; AO supplies local contact shading.
graded=np.clip(base*(1-.45*(1-ndimage.gaussian_filter(ao,2)))[...,None],0,1)
save(graded,'wyrm_head_basecolor_graded.png',1024)
normal=pad(C.load(src/'texture_urls_0_normal.png'));save(normal,'wyrm_head_normal_1k.png',1024)
rough=np.full(valid.shape,.83);rough[gold]=.72;rough[neutral]=.48;rough[tooth]=.42;rough[eye]=.20;rough[mouth]=.65
spec=np.full(valid.shape,.08);spec[gold]=.12;spec[neutral]=.35;spec[tooth]=.45;spec[eye]=.65
save(pad(np.stack([spec,rough,np.zeros_like(rough)],-1)),'wyrm_head_metal_rough_1k.png',1024)
weights=[]
for mask in [hide,gold]:
    im=Image.fromarray(np.uint8(pad(mask)*255)).filter(ImageFilter.GaussianBlur(.6)).resize((1024,1024),Image.Resampling.LANCZOS)
    weights.append(np.asarray(im,dtype=float)/255)
R.write_mask(weights,T/'wyrm_head_region_mask.png')
palettes={'wyrm_a':697,'wyrm_b':696,'wyrm_c':695}
frames=['drr1wka0','drr1wka1','drr1wka2','drr1wka3','drr1wka4']
samples={k:[[],[]] for k in palettes}
for frame in frames:
    a=C.load(N/'native_variants'/f'{frame}_697.png','RGBA');nh,ns,nv=C.hsv(a[...,:3]);alpha=a[...,3]>.5
    masks=[alpha&(nh>78)&(a[...,1]>a[...,0]+.005)&(a[...,1]>a[...,2]+.005),
           alpha&(nh>12)&(nh<78)&(ns>.25)&(nv>.05)]
    for k,pid in palettes.items():
        rgb=C.load(N/'native_variants'/f'{frame}_{pid}.png')[...,:3]
        for i,m in enumerate(masks):samples[k][i].append(rgb[m])
base1=R.load_srgb(T/'wyrm_head_basecolor_graded.png',1024);lum=R.srgb_to_linear(base1)@np.array([.2126,.7152,.0722])
ramps={k:[] for k in palettes};report=[]
for region,w in enumerate(weights):
    core=w>.8;targets={}
    assert core.sum()>100
    for tier in palettes:
        native=np.concatenate(samples[tier][region]);native=R.srgb_to_linear(native)
        nl=native@np.array([.2126,.7152,.0722]);order=np.argsort(nl);middle=native[order[int(len(order)*.15):int(len(order)*.95)]]
        color=middle.mean(0);brightness=float(lum[core].mean());gain=color/max(brightness,1e-5)*1.5
        linear=np.clip(lum[...,None]*gain,0,1)
        target=np.where(linear<=.0031308,12.92*linear,1.055*linear**(1/2.4)-.055)
        targets[tier]=target
    fitted,rep=R.fit_ramps(base1,targets,w)
    for tier in palettes:ramps[tier].append(fitted[tier])
    report.append(rep)
(T/'wyrm_head_ramps.json').write_text(json.dumps({'variants':list(palettes),'palettes':palettes,'report':report,
    'materials':[{'base':'WyrmHead','prefix':'WyrmHead','mask':'wyrm_head_region_mask.png','ramps':ramps}]},indent=2)+'\n')
(P/'checks/head_materials.json').write_text(json.dumps({'regions':['hide','gold'],'classes':{str(i):int((classes==i).sum()) for i in np.unique(classes)},'mask_padding':'nearest interior then 0.6 px feather','mr_red':'openyamm_specular_mask, not AO'},indent=2)+'\n')
print('COMPOSED',report)
