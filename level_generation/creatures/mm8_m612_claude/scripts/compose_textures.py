"""Compose the Gog's body/head sets and shared native-palette scale ramps."""
import colorsys,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as RV
import material_classes_to_orm as MC
import tier_textures as TT
sys.path.insert(0,str(R/'tools'));import normal_map_convention as NC
T=P/'textures';T.mkdir(exist_ok=True);N=1024
def load(path,mode='RGB'):
    return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):
    Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def hsv(a):
    h=np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255
    return h[...,0]*360,h[...,1],h[...,2]
def srgb(x):
    return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def pad(img,cov):
    _,(iy,ix)=ndimage.distance_transform_edt(~cov,return_indices=True)
    out=img[iy,ix];out[cov]=img[cov];return out
sets={}
tips=[np.array(v) for side in json.loads((P/'work/finger_joints.json').read_text()).values() for name,v in side.items() if name.endswith('_tip')]
for kind,layer in (('body','UVMap'),('head','HeadUV')):
    job=P/f'meshy/{kind}_texture_v1';raster=np.load(P/f'work/uvraster_{layer}.npz')
    piece,pos=raster['piece'],raster['pos'];cov=piece>=0
    base=load(job/'texture_urls_0_base_color.png');h,s,v=hsv(base)
    cls=np.zeros((N,N),np.uint8);cls[cov]=1
    if kind=='body':
        tip=np.zeros_like(cov)
        for point in tips:tip|=np.linalg.norm(pos-point,axis=-1)<.055
        toes=(pos[...,2]<.09)&(pos[...,1]<.10)
        spikes=((pos[...,2]>1.29)&(np.abs(pos[...,0])>.16))|(pos[...,1]>.19)|(piece!=0)
        keratin=cov&(tip|toes|spikes)&(h<72)&(v>.35)
        cls[keratin]=4
    else:
        teeth=cov&np.isin(piece,range(28,37));eye=cov&np.isin(piece,[26,27])
        for x in (-.03256,.02868):
            eye|=cov&(np.linalg.norm(pos-np.array([x,-.126,1.476]),axis=-1)<.025)&(h<70)&(s>.5)&(v>.4)
        mouth=cov&((piece==25)|((np.abs(pos[...,0])<.055)&(pos[...,1]<-.11)&(pos[...,2]<1.43)&(pos[...,2]>1.33)&(v<.2)))
        horns=(pos[...,2]>1.52)|np.isin(piece,[6,23])
        keratin=cov&horns&(h<72)&(v>.30)&~eye&~teeth
        cls[keratin]=4;cls[mouth]=7;cls[teeth]=5;cls[eye]=6
    # Native horns/claws are weathered pale keratin rather than bright yellow ivory.
    k=(cls==4)|(cls==5);grey=base[k].mean(1,keepdims=True)
    base[k]=(.4*base[k]+.6*grey)*.85
    ao=load(P/f'work/ao_{layer}.png','L');base[cov]*=(.7+.3*np.maximum(ao[cov],.45))[:,None]
    skin=cls==1
    assert skin.sum()>10000,(kind,int(skin.sum()))
    sets[kind]={'base':base,'cov':cov,'skin':skin,'cls':cls,'pos':pos,
                'normal':load(job/'texture_urls_0_normal.png'),'rough':load(job/'texture_urls_0_roughness.png','L')}
b,h=sets['body'],sets['head']
nb=b['skin']&(b['pos'][...,2]>1.33)&(b['pos'][...,2]<1.40)
nh=h['skin']&(h['pos'][...,2]<1.40)
assert nb.sum()>20 and nh.sum()>20
gain=(np.median(RV.luminance(b['base'][nb]))/np.median(RV.luminance(h['base'][nh])))**(1/2.2)
h['base'][h['skin']]=np.clip(h['base'][h['skin']]*gain,0,1)
palettes={f'gog_{tier}':np.frombuffer((R/f'assets_dev/worlds/mm8/textures/PAL{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for tier,n in zip('abc',(613,614,615))}
ph,ps,pv=hsv(palettes['gog_a'][None])
si=np.where((ph[0]>60)&(ph[0]<165)&(ps[0]>.15)&(np.abs(palettes['gog_a']-palettes['gog_c']).sum(1)>.06))[0]
indices=np.concatenate([np.asarray(Image.open(R/f'assets_dev/engine/sprites/m612SA{v}.bmp')).reshape(-1) for v in range(5)])
used=indices[np.isin(indices,si)];assert len(used)>10000
native=np.median(palettes['gog_a'][used],axis=0)
native_h,native_s,_=colorsys.rgb_to_hsv(*native)
colors=np.concatenate([x['base'][x['skin']] for x in sets.values()])
lum=RV.luminance(colors);lo,hi=np.log(np.percentile(lum,[1,99]))
assert hi>lo
tone=lambda x:np.clip((np.log(np.maximum(x,1e-6))-lo)/(hi-lo),0,1)
all_t=tone(lum);median=np.median(colors,axis=0)
mh,ms,mv=colorsys.rgb_to_hsv(*median);shift=native_h-mh;sat_gain=native_s/ms
stops=[]
for i in range(16):
    selected=np.abs(all_t-i/15)<.5/15
    c=np.median(colors[selected],axis=0)
    ch,cs,cv=colorsys.rgb_to_hsv(*c)
    stops.append(colorsys.hsv_to_rgb((ch+shift)%1,min(1,cs*sat_gain),min(1,mv*(max(cv,1e-4)/mv)**1.15)))
src=palettes['gog_a'][si]
maps={k:np.linalg.lstsq(np.c_[src,np.ones(len(src))],p[si],rcond=None)[0] for k,p in palettes.items()}
ramps={k:[{'range':[.01,.30],'colors':[RV.srgb_to_linear(np.clip(np.r_[c,1]@matrix,0,1)).tolist() for c in stops]}] for k,matrix in maps.items()}
report={'native_skin_pixels':int(len(used)),'native_palette_indices':si.tolist(),'head_neck_gain':float(gain),
        'native_median_rgb':native.tolist(),'texture_median_rgb':median.tolist(),'hue_shift_degrees':shift*360,'saturation_gain':sat_gain,'sets':{}}
for kind,x in sets.items():
    base,skin,cov,cls=x['base'],x['skin'],x['cov'],x['cls']
    l=RV.luminance(base[skin]);target=.01+tone(l)*.29
    base[skin]=srgb(np.clip(RV.srgb_to_linear(base[skin])*(target/np.maximum(l,1e-6))[:,None],0,1))
    prefix='gog' if kind=='body' else 'gog_head'
    save(pad(base,cov),T/f'{prefix}_basecolor_1k.png')
    normal=pad(x['normal'],cov)
    corr=NC.measure(np.uint8(np.clip(normal,0,1)*255+.5))
    if corr<=-.15:normal[...,1]=1-normal[...,1]
    save(normal,T/f'{prefix}_normal_1k.png')
    report.setdefault('normal_convention',{})[kind]={'input_correlation':corr,'flipped':bool(corr<=-.15)}
    labels=MC.fill_nearest(cls);rough=MC.roughness_map(labels,pad(x['rough'],cov),1)
    spec=np.zeros_like(rough);metal=np.zeros_like(rough)
    for label in np.unique(labels):
        metal[labels==label]=MC.TABLE[int(label)][0];spec[labels==label]=MC.TABLE[int(label)][3]
    save(np.stack([spec,rough,metal],-1),T/f'{prefix}_metal_rough_1k.png')
    RV.write_mask([ndimage.gaussian_filter(pad(skin.astype(float),cov),.7)],T/f'{prefix}_region_mask.png',size=N)
    Image.fromarray(cls).save(T/f'{prefix}_material_classes.png')
    report['sets'][kind]={'coverage':float(cov.mean()),'class_pixels':{str(int(c)):int((cls==c).sum()) for c in np.unique(cls)}}
config={'variants':list(palettes),'materials':[
    {'base':'Gog_A','prefix':'Gog','mask':'gog_region_mask.png','regions':['scales'],'ramps':ramps},
    {'base':'GogHead_A','prefix':'GogHead','mask':'gog_head_region_mask.png','regions':['scales'],'ramps':ramps}]}
(T/'gog_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
(T/'composition.json').write_text(json.dumps(report,indent=2)+'\n')
for kind,prefix in (('body','gog'),('head','gog_head')):
    base=load(T/f'{prefix}_basecolor_1k.png');mask=load(T/f'{prefix}_region_mask.png','RGBA')
    for variant in palettes:
        save(TT.apply(base,mask,ramps[variant]),T/f'{prefix}_preview_{variant}.png')
print(json.dumps({k:v for k,v in report.items() if k!='native_palette_indices'},indent=2))
