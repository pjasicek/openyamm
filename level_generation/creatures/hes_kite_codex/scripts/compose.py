"""Rasterise anatomical regions; build one shared PBR set and three colour-ramp variants."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';T.mkdir(exist_ok=True)
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
N=2048;d=np.load(P/'work/surface_v3.npz');v=d['positions'];tri=d['triangles'];uv=d['uv']
pos=np.zeros((N,N,3),np.float32);normal=pos.copy();wing=np.zeros((N,N),bool);cov=wing.copy()
for ids,ut in zip(tri,uv):
    q=ut*N;a,b,c=q;x0,y0=np.maximum(np.floor(q.min(0)).astype(int),0);x1,y1=np.minimum(np.ceil(q.max(0)).astype(int),N-1)
    den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(den)<1e-10 or x1<x0 or y1<y0:continue
    x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
    w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
    w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;w2=1-w0-w1;m=(w0>=0)&(w1>=0)&(w2>=0)
    iy=N-1-y[m].astype(int);ix=x[m].astype(int)
    pos[iy,ix]=w0[m,None]*v[ids[0]]+w1[m,None]*v[ids[1]]+w2[m,None]*v[ids[2]]
    n=np.cross(v[ids[1]]-v[ids[0]],v[ids[2]]-v[ids[0]]);n/=max(np.linalg.norm(n),1e-10)
    normal[iy,ix]=n;cov[iy,ix]=True;wing[iy,ix]=d['domains'][ids[0]]!='Body'
assert cov.sum()>N*N*.2
nearest=tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))
def pad(a):return a[nearest]
def load(path,mode='RGB',size=N):return np.asarray(Image.open(path).convert(mode).resize((size,size),Image.Resampling.LANCZOS),np.float32)/255

def save(a,path,size=None):
    im=Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5));(im.resize((size,size),Image.Resampling.LANCZOS) if size else im).save(path)
src=P/'meshy/body_texture_v3';rgb=load(src/'texture_urls_0_base_color.png');lum=rgb@R.LUMA
# Preserve painted eyes/mouth/ivory tips; undersides have their own pale ramp.
fixed=(pos[:,:,1]<-.73)&((lum<.17)|(lum>.80))
under=~wing&(normal[:,:,2]<-.25)&(pos[:,:,1]<.5)&~fixed
hide=~wing&~under&~fixed
weights=[pad((m&cov).astype(np.float32)) for m in (hide,wing,under)]
ao=load(T/'ashkite_ao_1k.png','L');rgb*=.86+.14*ao[:,:,None]
save(pad(rgb),T/'ashkite_basecolor_2k.png')
nm=load(src/'texture_urls_0_normal.png');corr=measure(np.uint8(nm*255+.5))
if corr<0:nm[:,:,1]=1-nm[:,:,1]
save(pad(nm),T/'ashkite_normal_1k.png',1024)
rough=np.full((N,N),.76);rough[wing]=.64;rough[fixed]=.4
save(np.stack([pad(ao),pad(rough),np.zeros((N,N))],-1),T/'ashkite_metal_rough_1k.png',1024)
R.write_mask(weights,T/'ashkite_region_mask.png',size=1024)
# Authored concept colours, dark/mid/light for hide, rust membrane and pale underside.
colours={
'kite_a':[[[30,31,29],[111,108,96],[185,181,163]],[[39,23,18],[132,76,49],[205,154,109]],[[64,60,47],[176,169,145],[228,219,191]]],
'kite_b':[[[18,19,20],[64,61,58],[132,127,115]],[[30,20,17],[106,60,40],[182,127,84]],[[57,51,39],[158,146,120],[216,201,167]]],
'kite_c':[[[22, 23, 26], [78, 79, 85], [164, 160, 172]], [[31, 22, 19], [108, 66, 44], [182, 133, 94]], [[63, 60, 64], [176, 170, 180], [232, 226, 235]]]}
ramps={k:[] for k in colours};ll=R.luminance(rgb)
for region,w in enumerate(weights):
    lo,hi=np.percentile(ll[cov&(w>.8)],[.5,99.5]);assert hi>lo
    for k in colours:
        cs=R.srgb_to_linear(np.array(colours[k][region])/255)
        arr=np.stack([np.interp(np.linspace(0,1,16),[0,.5,1],cs[:,ch]) for ch in range(3)],-1)
        ramps[k].append({'range':[float(lo),float(hi)],'colors':arr.round(6).tolist()})
(T/'ramps.json').write_text(json.dumps({'variants':list(ramps),'materials':[{'base':'Ashkite','prefix':'Ashkite','mask':'ashkite_region_mask.png','ramps':ramps}]},indent=2)+'\n')
(P/'review/texture_composition.json').write_text(json.dumps({'covered_texels':int(cov.sum()),'normal_correlation_before_flip':float(corr),'regions':['hide','membrane','underside'],'head_density':2.5,'metallic':0},indent=2)+'\n')
# No native fly frames exist for this new family. Compare matching spread top silhouettes;
# comparing a raised-wing front master against a moving flap changes the projected pose area.
im=np.asarray(Image.open(P.parents[2]/'design/kreegan_world/concepts/monsters/fam_ashkites.png').convert('RGB'),float)[520:1010,830:1536]
m=(np.ptp(im,axis=2)>17)|(im.mean(2)>66);lab,n=ndimage.label(m);counts=np.bincount(lab.ravel());counts[0]=0
m=ndimage.binary_fill_holes(lab==counts.argmax());y,x=np.nonzero(m)
ref=float(m.sum()/(np.ptp(x)+1)**2*2.7**2)
Image.fromarray(np.uint8(m)*255).save(P/'review/scale_reference_top_mask.png')
canvas=Image.new('1',(1600,1600));draw=ImageDraw.Draw(canvas);xy=v[:,:2]*400+800
for ids in tri:draw.polygon([tuple(q) for q in xy[ids]],fill=1)
area=np.count_nonzero(np.array(canvas))/400**2;factor=(ref/area)**.5
canvas.save(P/'review/scale_model_top_mask.png')
(P/'review/silhouette_area.json').write_text(json.dumps({'method':'matching spread top silhouettes; no native fly frames exist','reference_crop':[830,520,1536,1010],'reference_area_pixels':int(m.sum()),'reference_width_pixels':int(np.ptp(x)+1),'reference_area_m2_at_2_7m_span':ref,'model_area_m2':area,'area_scale':factor,'resulting_max_span_m':2.7368*factor},indent=2)+'\n')
print('COMPOSE',int(cov.sum()),'AREA_SCALE',factor,'SPAN',2.7368*factor)
