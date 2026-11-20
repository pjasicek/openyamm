"""Shared atlas, padded armour/trim regions and HD-colour-derived tier ramps; no baked runtime tier skins."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter
from scipy.ndimage import distance_transform_edt
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path[:0]=[str(R/'tools'),str(R/'level_generation/creatures/claude_shared'),str(R/'level_generation/creatures/hes_turrets_claude/scripts')]
from raster import rasterise
from region_variants import fit_ramps,srgb_to_linear,luminance
from normal_map_convention import measure
S=P/'meshy/sentinel_retexture_v1';out=P/'textures'
load=lambda n:np.asarray(Image.open(S/f'texture_urls_0_{n}.png').convert('RGB'),np.float32)/255
base=load('base_color');normal=load('normal');rough=load('roughness');res=len(base)
d=np.load(P/'work/sentinel_tex_tris.npz');tri,pos=rasterise(d['uv'],d['co'],d['n'],res);cover=tri>=0
r,g,b=np.moveaxis(base,-1,0)
purple=(b>g*1.10)&(r>g*1.08)
armor=(~purple)&(b>r*.54)&(g>r*.74)&(r>.25)
trim=(~purple)&(~armor)&(r>b*1.22)&(g>b*1.10)
weights=np.stack([armor,trim],-1).astype(np.float32)
# Extend only from real UV coverage so gaps cannot retain another island's region.
_,near=distance_transform_edt(~cover,return_indices=True)
weights=weights[tuple(near)];base=base[tuple(near)];normal=normal[tuple(near)];rough=rough[tuple(near)]
mask=np.zeros((res,res,4),np.uint8);mask[:,:,:2]=weights*255
# RGBA channels are four independent masks; never premultiply them by the unused alpha.
Image.merge('RGBA',[Image.fromarray(mask[:,:,i]).resize((1024,1024),Image.Resampling.BOX).filter(ImageFilter.GaussianBlur(.5)) for i in range(4)]).save(out/'sentinel_region_mask.png')
# Materials share maps, but armour's metallic factor is zero on ivory/scorched and metal on gilded.
orm=np.stack([np.ones((res,res)),np.maximum(rough[:,:,0],.52),np.clip(weights.sum(-1),0,1)],-1)
correlation=float(measure(np.asarray(Image.open(S/'texture_urls_0_normal.png').convert('RGB'))))
if correlation<=-.15:normal[:,:,1]=1-normal[:,:,1]
for name,a,size in [('basecolor',base,2048),('normal',normal,1024),('orm',orm,1024)]:
 Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).resize((size,size),Image.Resampling.LANCZOS).save(out/f'sentinel_{name}.png')
labels=np.where(weights[:,:,0]>.5,5,np.where(weights[:,:,1]>.5,9,11)).astype(np.uint8);labels[~cover]=0
Image.fromarray(labels).resize((1024,1024),Image.Resampling.NEAREST).save(out/'sentinel_material_classes.png')
# Triangles are assigned by full-face texel coverage, never by a single UV-centre sample.
counts=np.bincount(tri[cover],minlength=len(d['uv']));means=[]
for channel in range(2):
 sums=np.bincount(tri[cover],weights=weights[:,:,channel][cover],minlength=len(d['uv']))
 means.append(sums/np.maximum(counts,1))
faceclass=np.where(means[0]>.45,0,np.where(means[1]>.45,1,2))
# Subpixel triangles inherit the nearest atlas texel at their UV centre.
u=d['uv'].mean(1);x=np.clip((u[:,0]*res).astype(int),0,res-1);y=np.clip(((1-u[:,1])*res).astype(int),0,res-1)
faceclass[counts==0]=np.where(weights[y[counts==0],x[counts==0],0]>.45,0,np.where(weights[y[counts==0],x[counts==0],1]>.45,1,2))
np.save(P/'work/sentinel_face_materials.npy',faceclass)
# A reproduces the returned ivory look. B/C get independent measured HD colour curves.
def palette(subject,region):
 im=np.asarray(Image.open(P/f'references_hd/{subject}/01_front.png').convert('RGBA'),float)/255
 c=im[:,:,:3];r,g,b=np.moveaxis(c,-1,0);m=im[:,:,3]>.95
 if region=='gold':m&=(r>g*1.06)&(g>b*1.35)&(g>.18)
 else:m&=(r>g)&(g>b)&(b>r*.43)&(r>.22)&((r-b)<.38)
 a=c[m];assert len(a)>100
 lum=luminance(a);order=np.argsort(lum);a=a[order]
 return np.array([np.median(a[int(q*len(a)):max(int(q*len(a))+1,int(min(q+.04,.999)*len(a)))],axis=0) for q in np.linspace(.04,.94,16)])
base1=np.asarray(Image.open(out/'sentinel_basecolor.png').resize((1024,1024)),float)/255
mask1=np.asarray(Image.open(out/'sentinel_region_mask.png'),float)/255
ramps={v:[] for v in ['sentinel_a','sentinel_b','sentinel_c']};errors={};palettes={}
for ch in range(2):
 fit,err=fit_ramps(base1,{'sentinel_a':base1},mask1[:,:,ch]);ramps['sentinel_a'].append(fit['sentinel_a']);errors[str(ch)]=err
 for variant,subject,region in [('sentinel_b','heavy_sentinel','bone' if ch==0 else 'gold'),('sentinel_c','crown_sentinel','gold')]:
  pal=palette(subject,region);palettes[f'{variant}_{ch}']=pal.tolist()
  if variant=='sentinel_b' and ch==1:pal*=.72
  ramps[variant].append({'range':fit['sentinel_a']['range'],'colors':np.clip(srgb_to_linear(pal),0,1).round(6).tolist()})
cfg={'variants':list(ramps),'materials':[{'base':mat,'prefix':mat,'mask':'sentinel_region_mask.png','ramps':ramps} for mat in ['Sentinel_Armour','Sentinel_Trim','Sentinel_Resin']]}
(out/'sentinel_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
report={'normal_correlation':correlation,'normal_green_flipped':correlation<=-.15,'face_material_counts':np.bincount(faceclass,minlength=3).tolist(),'regions':['ivory armour','bronze trim'],'unchanged':'violet resin','region_texel_counts':[int(((weights[:,:,i]>.5)&cover).sum()) for i in range(2)],'fit_A':errors,'HD_palette_samples_srgb':palettes,'material_classes':{'5':'ivory armour (gilded on C)','9':'metal trim','11':'violet resin'}}
(out/'sentinel_material_report.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='HD_palette_samples_srgb'})
