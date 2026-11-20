"""Shared Thug PBR maps and four native palette regions; no textures duplicated per runtime tier."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';T.mkdir(exist_ok=True)
sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as R
import native_shading as NS
N=1024;W=np.array([.2126,.7152,.0722]);GAIN=1.35
paldir=P.parents[2]/'assets_dev/worlds/mm6/textures'
pals={k:np.frombuffer((paldir/f'pal{n}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,n in {'fgt_a':733,'fgt_b':734,'fgt_c':735}.items()}
def load(path,mode='RGB'):
 return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def pad(a,cov):
 ix=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
 return a[tuple(ix)]
def hsv(a):return np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255
body=load(P/'meshy/retexture_v1/texture_urls_0_base_color.png');head=load(P/'meshy/head_retexture_v1/texture_urls_0_base_color.png')
b=np.load(P/'work/uvraster_UVMap.npz');h=np.load(P/'work/uvraster_HeadUV.npz')
piece,pos=b['piece'],b['pos'];hp,hpos=h['piece'],h['pos'];cov=piece>=0;hcov=hp>=0
bh,bs,bv=np.moveaxis(hsv(body),-1,0);hh,hs,hv=np.moveaxis(hsv(head),-1,0)
steel=cov&(bs<.20)&(bv>.22)
cloth=(piece==2)|((piece==0)&(bh>.20)&(bh<.48)&(bs>.25))
copper=np.isin(piece,[11,12])&~steel
leather=cov&~steel&~cloth&~copper
# Painted eyes, eyebrows, sideburns and lips keep their own detail.
skin=(hp==1)&(hh>.015)&(hh<.12)&(hs>.12)&(hs<.66)&(hv>.25)
hair=hcov&~skin
# The thin sideburn shells received projected cheek colour; match the actual hair shell.
sideburn=np.isin(hp,[26,27]);hair_col=np.median(head[hp==3],0)
side_lum=R.luminance(head[sideburn]);detail=np.clip(side_lum/max(float(np.median(side_lum)),1e-5),.6,1.5)**.25
head[sideburn]=hair_col*detail[:,None]
assert cloth.sum()>10000 and leather.sum()>10000 and copper.sum()>500 and skin.sum()>10000
body*= (1-.40*(1-np.maximum(load(P/'work/ao_body.png','L'),.35)))[...,None]
# Retain Meshy's metal detail but temper its white plate highlights.
body[steel]*=.78
# Native face is warmer and darker than Meshy's pale face, without recolouring its hair or eyes.
head[hp==1]*=np.array([1.02,.91,.87])
# Use native standing pixels from all five views; exclude palette background and near-black outlines.
lut={tuple(np.uint8(c*255+.5)):i for i,c in enumerate(pals['fgt_a'])}
idx=[];face_idx=[]
for view in range(5):
 im=np.asarray(Image.open(P.parent/'mm6_fgt/native'/f'fgtfsta{view}.png').convert('RGB'))
 ids=np.array([lut.get(tuple(c),-1) for c in im.reshape(-1,3)]).reshape(im.shape[:2]);idx.extend(ids.ravel())
 face_idx.extend(ids[:70].ravel())
idx=np.array(idx);face_idx=np.array(face_idx)
regions=[('fabric',cloth,np.zeros_like(skin),1,56),('leather',leather,np.zeros_like(skin),89,178),('copper',copper,np.zeros_like(skin),56,89),('skin',np.zeros_like(cloth),skin,178,231)]
ramps={k:[] for k in pals};report={}
for name,bm,hm,loidx,hiidx in regions:
 ids=face_idx if name=='skin' else idx
 ids=ids[(ids>=loidx)&(ids<hiidx)]
 # Copper samples are the orange plate, not the near-black belt/mace pixels in the same palette band.
 threshold=.20 if name=='copper' else .14
 ids=ids[pals['fgt_a'][ids].max(1)>threshold]
 if name=='copper':ids=ids[(pals['fgt_a'][ids,0]>1.45*pals['fgt_a'][ids,1])]
 assert len(ids)>50
 order=np.argsort(R.luminance(pals['fgt_a'][ids]));ids=ids[order]
 lum=np.sort(np.r_[R.luminance(body[bm]),R.luminance(head[hm])]);lo,hi=np.percentile(lum,[2,98]);assert hi>lo
 for key,pal in pals.items():
  # Native hue/brightness, with the generated texture's continuous shading. Rank matching the sprite's
  # baked shadows amplified facial pores and leather grain into dark mottling in the first review.
  native=R.srgb_to_linear(pal[ids]);mid=np.median(native[len(ids)//4:3*len(ids)//4],0)*GAIN
  chroma=mid/max(float(mid@W),1e-6);gain=float(mid@W)/max(float(np.median(lum)),1e-6)
  cols=[np.clip(chroma*(lo+j/15*(hi-lo))*gain,0,1).tolist() for j in range(16)]
  ramps[key].append({'range':[float(lo),float(hi)],'colors':cols})
 report[name]={'native_pixels':len(ids),'body_texels':int(bm.sum()),'head_texels':int(hm.sum()),'range':[float(lo),float(hi)]}
print('REGIONS',report)
# Native contrast only: retain the accepted ramps so faces and other leather parts do not shift.
original=body.copy();native_height=[];native_chest=[];native_steel=[]
for view in (0,4):
 frame=np.asarray(Image.open(P.parent/'mm6_fgt/native_variants'/f'fgtfsta{view}_733.png').convert('RGBA'),float)/255
 ids=np.array([lut.get(tuple(c),-1) for c in np.uint8(frame[...,:3]*255+.5).reshape(-1,3)]).reshape(frame.shape[:2])
 y,x,height=NS._sample_view(frame,'height',0,.5)
 take=(ids[y,x]>=89)&(ids[y,x]<178)&(height>=.59)&(height<=.81)
 native_height.extend(height[take]);native_chest.extend(NS.srgb_luminance(frame[y[take],x[take],:3]))
 alpha=frame[...,3]>.5;rows=np.nonzero(alpha.any(1))[0]
 height=np.broadcast_to(((rows.max()-np.arange(frame.shape[0]))/(rows.max()-rows.min()))[:,None],alpha.shape)
 take=ndimage.binary_erosion(alpha)&(ids>=231)&(ids<255)&(height>.70)&(height<.90)
 native_steel.extend(NS.srgb_luminance(frame[take,:3]))
bins=np.arange(.61,.791,.03)
curve,known=NS._binned(np.asarray(native_height),np.asarray(native_chest),bins,.03)
assert known.all() and len(native_steel)>500
curve=ndimage.gaussian_filter1d(curve,1)
height=NS.texel_coordinate(pos,'height',z_range=(0,1.70012))
torso=leather&(piece==0)&(np.abs(pos[...,0])<.19)&(height>.60)&(height<.80)
# Feather in physical space, across UV seams; keep arms, gloves, scarf, belts and tassets out.
fade=np.minimum.reduce([np.clip((.19-np.abs(pos[...,0]))/.05,0,1),
                        np.clip((height-.60)/.03,0,1),np.clip((.80-height)/.03,0,1)])
fade=fade*fade*(3-2*fade)
relative=np.clip(np.interp(height,bins,curve)/np.median(curve),.70,1.30)
torso_gain=1+.30*fade*(relative-1)
body[torso]*=torso_gain[torso,None]
plate=steel&np.isin(piece,[7,13]);lum=NS.srgb_luminance(body)
model_mid,highlight=np.percentile(lum[plate],[50,90]);native_mid,native_high=np.percentile(native_steel,[50,90])
# Keep the bright metal detail; take only 40% of the native midtone-to-highlight contrast.
exponent=1+.40*(np.clip(np.log(native_mid/native_high)/np.log(model_mid/highlight),1,3)-1)
plate_gain=np.clip(np.minimum(lum[plate]/highlight,1)**(exponent-1),.70,1)
body[plate]*=plate_gain[:,None]
assert np.array_equal(body[~(torso|plate)],original[~(torso|plate)])
assert np.isfinite(body).all() and plate_gain.min()>=.70 and torso_gain.min()>=.90
contrast={'views':['fgtfsta0_733','fgtfsta4_733'],'coordinate':'height, torso only',
 'height_bins':bins.tolist(),'native_torso_luminance':curve.tolist(),'torso_amount':.30,
 'torso_gain_range':[float(torso_gain[torso].min()),float(torso_gain[torso].max())],
 'steel_contrast_amount':.40,'steel_exponent':float(exponent),
 'steel_native_p50_p90':[float(native_mid),float(native_high)],
 'steel_before_p10_p50_p90':np.percentile(NS.srgb_luminance(original[plate]),[10,50,90]).tolist(),
 'steel_after_p10_p50_p90':np.percentile(NS.srgb_luminance(body[plate]),[10,50,90]).tolist(),
 'torso_texels':int(torso.sum()),'steel_texels':int(plate.sum()),'other_occupied_texels_unchanged':True}
(P/'work/native_contrast.json').write_text(json.dumps(contrast,indent=2)+'\n')
print('NATIVE CONTRAST',contrast)

# Matte textile, satin leather, subdued skin and metallic plate glints use the current MR.R specular contract.
surfaces=[(cloth,.08,.88),(leather,.30,.66),(copper,.8,.36),(steel,.8,.38)]
rough=load(P/'meshy/retexture_v1/texture_urls_0_roughness.png','L');normal=load(P/'meshy/retexture_v1/texture_urls_0_normal.png');spec=np.zeros_like(rough);rg=np.zeros_like(rough)
for mask,s,r in surfaces:
 spec[mask]=s;rg[mask]=np.clip(r+.4*(rough[mask]-np.median(rough[mask])),.25,1)
body=pad(body,cov);normal=pad(normal,cov);spec=pad(spec,cov);rg=pad(rg,cov)
masks=np.stack([ndimage.gaussian_filter(pad(bm.astype(float),cov),.7) for _,bm,_,_,_ in regions],-1)
# Small non-recoloured atlas cells for the mace's leather grip, steel shaft/spikes and blackened head.
occ=ndimage.binary_dilation(cov,iterations=8);sw={};swatch=np.zeros_like(cov)
for cls,rgb,s,r in [(1,(72,38,24),.30,.73),(2,(174,174,178),.8,.35),(3,(29,28,27),.45,.53)]:
 found=False
 for y in range(N-12,12,-5):
  for x in range(N-12,12,-5):
   if not occ[y-6:y+6,x-6:x+6].any():found=True;break
  if found:break
 assert found,'No free mace atlas cell'
 sl=(slice(y-6,y+6),slice(x-6,x+6));body[sl]=np.array(rgb)/255;normal[sl]=(.5,.5,1);spec[sl]=s;rg[sl]=r
 occ[y-9:y+9,x-9:x+9]=True;swatch[y-9:y+9,x-9:x+9]=True;sw[str(cls)]=[(x+.5)/N,1-(y+.5)/N,3/N]
masks[swatch]=0
save(body,T/'fgt_basecolor_1k.png');save(normal,T/'fgt_normal_1k.png');save(np.stack([spec,rg,np.zeros_like(rg)],-1),T/'fgt_metal_rough_1k.png')
R.write_mask([masks[...,i] for i in range(4)],T/'fgt_region_mask.png',size=N)
cmap=np.zeros_like(piece,dtype=np.uint8);cmap[cov]=8;cmap[steel|copper]=9;Image.fromarray(cmap).save(T/'fgt_material_classes.png')
hr=load(P/'meshy/head_retexture_v1/texture_urls_0_roughness.png','L');hspec=np.where(skin,.25,.18);hrg=np.where(skin,.72,.75)+.25*(hr-.5)
save(pad(head,hcov),T/'fgt_head_basecolor_1k.png');save(pad(load(P/'meshy/head_retexture_v1/texture_urls_0_normal.png'),hcov),T/'fgt_head_normal_1k.png')
save(np.stack([pad(hspec,hcov),pad(hrg,hcov),np.zeros_like(hr)],-1),T/'fgt_head_metal_rough_1k.png')
R.write_mask([ndimage.gaussian_filter(pad(hm.astype(float),hcov),.7) for _,_,hm,_,_ in regions],T/'fgt_head_region_mask.png',size=N)
hc=np.zeros_like(hp,dtype=np.uint8);hc[hcov]=2;hc[skin]=1
for eye in [(-.022,-.099,1.568),(.024,-.097,1.568)]:
 eye_mask=(hp==1)&(np.linalg.norm((hpos-np.array(eye))/np.array([.012,.010,.008]),axis=-1)<1)&~skin
 hc[eye_mask]=6
Image.fromarray(hc).save(T/'fgt_head_material_classes.png')
cfg={'variants':list(pals),'materials':[{'base':name+'_A','prefix':name,'mask':mask,'regions':[r[0] for r in regions], 'palettes':{'fgt_a':733,'fgt_b':734,'fgt_c':735},'ramps':ramps,'report':report} for name,mask in [('Thug','fgt_region_mask.png'),('ThugHead','fgt_head_region_mask.png')]]}
(T/'fgt_ramps.json').write_text(json.dumps(cfg,indent=2));(T/'fgt_mace_swatches.json').write_text(json.dumps(sw,indent=2))
assert np.all(masks[swatch]==0) and np.isfinite(body).all() and np.isfinite(head).all()
