"""Shared 1K PBR sets, geometry-based material classes and native palette ramps for m628 A/B/C."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as RV
sys.path.insert(0,str(R/'tools'));import normal_map_convention
T=P/'textures';T.mkdir(exist_ok=True);N=1024
def load(path,mode='RGB'):
    return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray((np.clip(a,0,1)*255+.5).astype(np.uint8)).save(path)
def pad(a,cov):
    _,(iy,ix)=ndimage.distance_transform_edt(~cov,return_indices=True);out=a[iy,ix];out[cov]=a[cov];return out
def hsv(a):
    h=np.asarray(Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)).convert('HSV'),float)/255
    return h[...,0]*360,h[...,1],h[...,2]
def reserve_strip(a,fill):
    out=np.empty_like(a);out[:]=fill
    # Sample exactly the UV affine transform, rather than rounding the 20.48-pixel boundary.
    x=(np.arange(N)+.5-N*.02)/.98-.5;y=np.arange(N)
    yy,xx=np.meshgrid(y,x,indexing='ij')
    if a.ndim==2:r=ndimage.map_coordinates(a,[yy,xx],order=1,mode='nearest')
    else:r=np.stack([ndimage.map_coordinates(a[...,i],[yy,xx],order=1,mode='nearest')for i in range(a.shape[2])],-1)
    valid=(np.arange(N)+.5)/N>=.02;out[:,valid]=r[:,valid];return out
report={};cloth=None;basebody=None
for kind in ['body','head','bow']:
    job=P/f'meshy/{kind}_retexture_v1';base=load(job/'texture_urls_0_base_color.png');normal=load(job/'texture_urls_0_normal.png')
    rough=load(job/'texture_urls_0_roughness.png','L');metal=load(job/'texture_urls_0_metallic.png','L')
    if kind=='head':
        repairs=json.loads((P/'work/head_uv_repairs.json').read_text())
        for a in [base,normal,rough,metal]:
            original=a.copy()
            for patch in repairs['patches']:
                x,y,w,h=patch['source'];dx,dy=patch['destination'];a[dy:dy+h,dx:dx+w]=original[y:y+h,x:x+w]
    if kind=='body':
        base=reserve_strip(base,np.array([.72,.66,.51]));normal=reserve_strip(normal,np.array([.5,.5,1]));rough=reserve_strip(rough,.8);metal=reserve_strip(metal,0)
    raster=np.load(P/f'work/uvraster_{kind}.npz');piece=raster['piece'];pos=raster['pos'];cov=piece>=0
    hue,sat,val=hsv(base);cls=np.zeros((N,N),np.uint8);cls[cov]=5
    if kind=='body':
        cls[cov&np.isin(piece,[0,1,3,5,6,9,16,23,24,37,39,4001,4002])]=8
        brass=cov&((piece==37)|((cls==8)&(metal>.5)&(hue>25)&(hue<62)&(sat>.35)&(val>.3)))
        cls[brass]=9
        strings=cov&np.isin(piece,[4001,4002]);base[strings]=[.065,.055,.041];normal[strings]=[.5,.5,1]
        cloth=cov&(piece==0)&(pos[...,2]<1.02)&(hue>65)&(hue<170)&(sat>.14)&(val>.08)
        cloth=ndimage.binary_fill_holes(cloth)&cov&(piece==0)&(pos[...,2]<1.02)
        assert cloth.sum()>1500,int(cloth.sum())
    elif kind=='head':cls[cov&(piece<2000)]=8
    else:
        cls[cov]=raster['material_class'][cov]
        stave=cov&(piece==4000);cls[stave]=10
        brass=stave&(metal>.35)&(hue>20)&(hue<70)&(sat>.2);cls[brass]=9
        # The bow's black grip is visible in the painted reference and returned albedo.
        cls[stave&(val<.23)]=8
        feather=cov&(cls==11);lum=RV.luminance(base)
        detail=np.clip(lum/np.maximum(ndimage.gaussian_filter(lum,6),.01),.65,1.3)
        base[feather]=np.array([.76,.73,.61])*detail[feather,None]
        tips=cov&(cls==9)&(piece!=4000);base[tips]=np.array([.30,.31,.30])*detail[tips,None]
    ao=load(P/f'work/ao_{kind}.png','L');graded=base.copy();graded[cov]*=(.65+.35*np.maximum(ao[cov],.35))[:,None]
    # Bone stays warm ivory, with the generated pores, cracks and cavity shading retained.
    bone=cov&(cls==5);graded[bone]*=np.array([.96,.97,.97])
    spec=np.zeros((N,N));rgh=np.full((N,N),.8)
    for value,s,r in [(5,.35,.72),(8,.18,.86),(9,.85,.40),(10,.25,.74),(11,.12,.92)]:
        m=cov&(cls==value);spec[m]=s
        if m.any():rgh[m]=np.clip(r+(rough[m]-np.median(rough[m]))*.25,.25,.98)
    normal=pad(normal,cov);correlation=normal_map_convention.measure((np.clip(normal,0,1)*255+.5).astype(np.uint8))
    if correlation<=-.15:normal[...,1]=1-normal[...,1]
    save(pad(graded,cov),T/f'm628_{kind}_basecolor.png');save(normal,T/f'm628_{kind}_normal.png')
    save(np.stack([pad(spec,cov),pad(rgh,cov),np.zeros((N,N))],-1),T/f'm628_{kind}_orm.png')
    Image.fromarray(cls).save(T/f'm628_{kind}_material_classes.png')
    report[kind]={'classes':{str(i):int((cls==i).sum())for i in np.unique(cls)},'coverage':float(cov.mean()),'AO':'work/ao_'+kind+'.png',
        'source_normal_correlation':correlation,'normal_green_flipped':correlation<=-.15}
    if kind=='body':basebody=graded;bodycov=cov;cloth=pad(cloth.astype(float),cov);RV.write_mask([ndimage.gaussian_filter(cloth,.55)],T/'m628_region_mask.png',size=N)
# Palette indices 192..255 are the native recolour domain. Weight their frequencies by real native frame pixels.
palettes={k:np.frombuffer((R/f'assets_dev/worlds/mm8/textures/Pal{p}.act').read_bytes()[:768],dtype=np.uint8).reshape(256,3)/255
    for k,p in [('m628_a',629),('m628_b',630),('m628_c',631)]}
samples=[]
for frame in ['sa0','sa1','sa2','sa3','sa4','aa0','ac0','ae0','wa0','wd0']:
    ix=np.asarray(Image.open(R/f'assets_dev/engine/sprites/m628{frame}.bmp'));samples.extend(ix[(ix>=192)&(ix>0)].tolist())
indices=np.array(samples);assert len(indices)>1000
mask=(cloth>.8)&bodycov;L=RV.luminance(basebody);lo,hi=np.percentile(L[mask],[2,98]);ordered=np.sort(L[mask]);ramps={}
for key,pal in palettes.items():
    colors=pal[indices];nativeL=RV.luminance(colors);colors=colors[nativeL>.015];colors=colors[np.argsort(RV.luminance(colors))]
    colors=RV.srgb_to_linear(np.clip(colors*1.25,0,1));stops=[]
    for l in np.linspace(lo,hi,16):
        q=np.searchsorted(ordered,l)/len(ordered);stops.append(colors[min(len(colors)-1,int(q*(len(colors)-1)))].tolist())
    ramps[key]=[{'range':[float(lo),float(hi)],'colors':stops}]
cfg={'variants':list(palettes),'materials':[{'base':'SkeletonArcherBody_A','prefix':'SkeletonArcherBody',
    'mask':'m628_region_mask.png','regions':['breeches'],'palettes':{'m628_a':629,'m628_b':630,'m628_c':631},'ramps':ramps}]}
(T/'m628_ramps.json').write_text(json.dumps(cfg,indent=2));report['native_ramps']={'sample_pixels':len(indices),'palette_indices':[192,255],'gain':1.25,'region_texels':int(mask.sum())}
(P/'work/texture_compose.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
