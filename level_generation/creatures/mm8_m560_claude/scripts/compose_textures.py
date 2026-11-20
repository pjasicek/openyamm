"""Shared wyvern PBR maps, anatomical classes and native palette colour ramps."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';S=P/'meshy/retexture_v2/texture_urls_0'
sys.path[:0]=[str(P.parent/'claude_shared'),str(P.parent/'mm6_gob_claude/scripts')]
import region_variants as R
from material_classes_to_orm import accessor
import compose_textures_v2 as C
# Meshy recentres and doubles this static upload; its UVs and indexed surface must match exactly.
a,ab=R.read_glb(P/'texturing/wyvern_neutral.glb');b,bb=R.read_glb(P/'meshy/retexture_v2/model_urls_glb.glb')
ap=a['meshes'][0]['primitives'][0];bp=b['meshes'][0]['primitives'][0]
x=accessor(a,ab,ap['attributes']['POSITION']);y=accessor(b,bb,bp['attributes']['POSITION'])
centre=(x.max(0)+x.min(0))*.5
from scipy.spatial import cKDTree
u=accessor(a,ab,ap['attributes']['TEXCOORD_0']);v=accessor(b,bb,bp['attributes']['TEXCOORD_0'])
i=accessor(a,ab,ap['indices']).astype(int).ravel();j=accessor(b,bb,bp['indices']).astype(int).ravel()
assert len(i)==len(j)
source=np.c_[(x-centre)*2,u][i];returned=np.c_[y,v][j]
assert cKDTree(source).query(returned)[0].max()<2e-7
assert cKDTree(returned).query(source)[0].max()<2e-7
data=np.load(P/'work/uv3d.npz');part,xyz=C.rasterise(data,tol=0)
valid=part>=0;interior=ndimage.binary_erosion(valid,iterations=1)
_,(iy,ix)=ndimage.distance_transform_edt(~interior,return_indices=True)
def pad(v):
    out=v[iy,ix];out[interior]=v[interior];return out
base=pad(C.load(str(S)+'_base_color.png'));h,s,v=C.hsv(base)
classes=np.ones(part.shape,np.uint8)
classes[np.isin(part,[4,19])]=3
for n in np.unique(data['part']):
    if n in [1,4,19]:continue
    mean=data['xyz'][data['part']==n].mean(axis=(0,1))
    label=6 if n in [12,40] else 7 if n==17 else 5 if mean[1]<-.43 else 4
    classes[part==n]=label
classes[(part==1)&(((xyz[...,2]<.025)&(xyz[...,1]>-.06))|(xyz[...,1]>.465))&(s<.35)&(v>.45)]=4
# Preserve dark pupils while restoring the tiny eye's red iris from the native source.
eye=classes==6;eye_lum=base.mean(-1)
base[eye]=np.clip(np.array([.8,.07,.025])*np.clip(eye_lum[eye,None]/.35,.25,1.4),0,1)
ao=pad(C.load(T/'wyvern_ao.png','L'));ao=ndimage.gaussian_filter(ao,1)
base*= (.65+.35*ao)[...,None]
membrane=(classes==3)&(h<65)&(s>.2)
body=np.isin(classes,[1,3])&~membrane
weights=[pad(ndimage.gaussian_filter(sel.astype(np.float32),.6)) for sel in [membrane&valid,body&valid]]
for w in weights:assert int((w>.9).sum())>1000
R.write_mask(weights,T/'wyvern_region_mask.png')
def save(a,path,size=None,nearest=False):
    im=Image.fromarray(np.clip(a*255+.5,0,255).astype(np.uint8))
    if size:im=im.resize((size,size),Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS)
    im.save(path)
save(pad(base),T/'wyvern_basecolor.png')
save(pad(C.load(str(S)+'_normal.png')),T/'wyvern_normal_1k.png',1024)
rough=pad(C.load(str(S)+'_roughness.png','L'))
save(np.stack([ao,rough,np.zeros_like(rough)],-1),T/'wyvern_orm_1k.png',1024)
Image.fromarray(pad(classes)).resize((1024,1024),Image.Resampling.NEAREST).save(T/'wyvern_material_classes.png')
# Use identical native pixels across tier palettes, so all shading ranks retain their original colour family.
native=P.parent/'mm8_m560/native_variants';sources=json.loads((P.parent/'mm8_m560/sources.json').read_text())['sources']
regions=[];pixels={n:[] for n in [561,562,563]}
for key,item in sources.items():
    if not key.startswith(('m560s','m560w')):continue
    path=native/(key+'_561.png')
    if not path.exists():continue
    rgb=C.load(path);hh,ss,vv=C.hsv(rgb);opaque=np.asarray(Image.open(item['path']))!=0
    wing=opaque&(hh>20)&(hh<65)&(ss>.35)
    skin=opaque&(hh>=65)&(hh<170)&(ss>.18)
    yy,xx=np.nonzero(wing|skin);regions.append(np.where(wing[yy,xx],0,1))
    for pal in pixels:pixels[pal].append(C.load(native/(key+f'_{pal}.png'))[yy,xx])
regions=np.concatenate(regions);pixels={k:np.concatenate(v) for k,v in pixels.items()}
ramps={f'm560_{tier}':[] for tier in 'abc'};lum=R.luminance(base)
for i,w in enumerate(weights):
    values=np.sort(lum[(w>.9)&valid]);lo,hi=np.percentile(values,[.5,99.5]);quant=np.searchsorted(values,np.linspace(lo,hi,16))/len(values)
    sel=regions==i;assert sel.sum()>500
    order=np.argsort(R.luminance(pixels[561][sel]));half=max(2,len(order)//100)
    for tier,pal in zip('abc',[561,562,563]):
        native_rgb=pixels[pal][sel][order];colors=[]
        for q in quant:
            centre=int(q*(len(order)-1));rgb=np.median(native_rgb[max(0,centre-half):centre+half+1],axis=0)
            colors.append(R.srgb_to_linear(np.clip(rgb*1.15,0,1)).tolist())
        ramps['m560_'+tier].append({'range':[float(lo),float(hi)],'colors':colors})
config={'variants':['m560_a','m560_b','m560_c'],'materials':[{'base':'Wyvern_A','prefix':'Wyvern','mask':'wyvern_region_mask.png','regions':['membrane','body'],'palettes':{'m560_a':561,'m560_b':562,'m560_c':563},'ramps':ramps}]}
(T/'wyvern_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
report={'return_geometry':'uniform x2 recenter only; reordered vertices; bidirectional per-corner position/UV error below 2e-7','native_region_pixels':[int((regions==i).sum()) for i in range(2)],'classes':{str(i):int(((classes==i)&valid).sum()) for i in np.unique(classes)},'atlas_coverage':float(valid.mean()),'head_texture':'2.5x UV density on one 2K atlas, small non-humanoid head'}
(P/'review/texture_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
